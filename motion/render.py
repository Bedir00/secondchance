#!/usr/bin/env python3
"""Render calm, subtle Instagram motion graphics (9:16) from the look photos.

Every frame is composed in numpy and piped straight into ffmpeg:
  - slow push-in on the photo (sub-pixel, no jitter)
  - drifting window light across the wall
  - a few dust motes floating in that light
  - quiet typography: brand mark, look number, name, details

Usage:
  python3 motion/render.py                 # render everything into export/
  python3 motion/render.py --only look-02  # a single video
  python3 motion/render.py --stills        # only poster/preview stills
"""

import argparse
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
EXPORT = os.path.join(ROOT, "export")

with open(os.path.join(ROOT, "motion", "config.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)

W, H, FPS = CFG["width"], CFG["height"], CFG["fps"]

# Typography sits inside the Reels/Stories safe zone (≈250px top, ≈420px bottom).
MARGIN_X = 76
BRAND_Y = 236
BLOCK_Y = 1190
TEXT_MAX_W = 330  # free wall left of the trousers


# --------------------------------------------------------------------------- utils

def rgb(hex_color):
    h = hex_color.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_out_sine(x):
    x = clamp01(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def fade(t, t_in, d_in, t_out, d_out):
    """Opacity that eases in at t_in and back out at t_out."""
    return ease_out_cubic((t - t_in) / d_in) * (1 - ease_in_out_sine((t - t_out) / d_out))


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


# ------------------------------------------------------------------------- sprites

class Sprite:
    """Premultiplied RGBA float image that can be placed at sub-pixel positions."""

    def __init__(self, arr, ox=0.0, oy=0.0):
        self.arr = arr  # (h, w, 4) premultiplied
        self.ox, self.oy = ox, oy  # offset relative to the owning text origin
        self.h, self.w = arr.shape[:2]


def _rasterize(text, fnt, tracking, color):
    ascent, descent = fnt.getmetrics()
    pad = 4
    width = int(math.ceil(fnt.getlength(text) + tracking * max(0, len(text) - 1))) + 2 * pad
    img = Image.new("L", (width, ascent + descent + 2 * pad), 0)
    draw = ImageDraw.Draw(img)
    for i, ch in enumerate(text):
        x = pad + fnt.getlength(text[:i]) + tracking * i
        draw.text((x, pad + ascent), ch, font=fnt, fill=255, anchor="ls")
    a = np.asarray(img, dtype=np.float32)[..., None] / 255.0
    arr = np.concatenate([a * color, a], axis=2)
    return arr, pad, ascent


def text_sprite(text, fnt, tracking=0.0, color=None):
    color = rgb(CFG["colors"]["ink"]) if color is None else color
    arr, pad, ascent = _rasterize(text, fnt, tracking, color)
    s = Sprite(arr, -pad, -pad - ascent)  # origin = left baseline
    s.advance = arr.shape[1] - 2 * pad
    return s


def letter_sprites(text, fnt, tracking=0.0, color=None):
    """One sprite per glyph (kerning kept) for staggered letter reveals."""
    color = rgb(CFG["colors"]["ink"]) if color is None else color
    out = []
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        arr, pad, ascent = _rasterize(ch, fnt, 0, color)
        x = fnt.getlength(text[:i]) + tracking * i
        out.append(Sprite(arr, x - pad, -pad - ascent))
    width = fnt.getlength(text) + tracking * max(0, len(text) - 1)
    return out, width


def fit_font(name, size, text, max_w, tracking=0.0, min_size=40):
    while size > min_size:
        f = font(name, size)
        if f.getlength(text) + tracking * (len(text) - 1) <= max_w:
            return f
        size -= 2
    return font(name, min_size)


def blit(frame, sprite, x, y, alpha):
    """Composite a sprite 'over' the frame at a sub-pixel position."""
    if alpha <= 0.002:
        return
    x += sprite.ox
    y += sprite.oy
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    p = sprite.arr
    h, w = sprite.h, sprite.w
    q = np.zeros((h + 1, w + 1, 4), dtype=np.float32)
    q[:h, :w] += (1 - fx) * (1 - fy) * p
    q[:h, 1:] += fx * (1 - fy) * p
    q[1:, :w] += (1 - fx) * fy * p
    q[1:, 1:] += fx * fy * p
    x0, y0 = max(ix, 0), max(iy, 0)
    x1, y1 = min(ix + w + 1, W), min(iy + h + 1, H)
    if x0 >= x1 or y0 >= y1:
        return
    q = q[y0 - iy:y1 - iy, x0 - ix:x1 - ix] * alpha
    region = frame[y0:y1, x0:x1]
    region *= 1 - q[..., 3:4]
    region += q[..., :3]


def hairline(frame, x, y, length, thickness, color, alpha):
    """Horizontal line with an anti-aliased growing end."""
    if alpha <= 0.002 or length <= 0:
        return
    full = int(length)
    frac = length - full
    a = alpha
    region = frame[int(y):int(y) + thickness]
    seg = region[:, int(x):int(x) + full]
    seg *= 1 - a
    seg += a * color
    if frac > 0 and int(x) + full < W:
        end = region[:, int(x) + full]
        end *= 1 - a * frac
        end += a * frac * color


# ------------------------------------------------------------------ atmosphere

LOW = 4  # light field is computed at 1/4 resolution, it is very smooth anyway
_lx, _ly = np.meshgrid(np.arange(W // LOW, dtype=np.float32) * LOW,
                       np.arange(H // LOW, dtype=np.float32) * LOW)
_ANGLE = math.radians(58)
_U = _lx * math.cos(_ANGLE) + _ly * math.sin(_ANGLE)
_WINDOW = (0.55 + 0.45 * (1 - _lx / W)) * (0.75 + 0.25 * (1 - _ly / H))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.46) / (H / 2)) ** 2
VIGNETTE = (1 - 0.075 * np.clip(_r2, 0, 1.6))[..., None].astype(np.float32)
del yy, xx, _r2


class Atmosphere:
    """Window light drifting across the wall plus a handful of dust motes.

    All motion is periodic over `period`, so a clip can loop seamlessly.
    """

    def __init__(self, seed, period, strength=0.11, motes=34):
        rnd = np.random.default_rng(seed)
        self.period = period
        self.strength = strength
        self.light = rgb(CFG["colors"]["light"])
        span = W * math.cos(_ANGLE) + H * math.sin(_ANGLE)
        self.bands = [
            (span * c, w, s, rnd.uniform(0, 2 * math.pi))
            for c, w, s in ((0.30, 120, 1.0), (0.46, 70, 0.8), (0.62, 150, 0.7), (0.80, 90, 0.5))
        ]
        n = motes
        self.mx = rnd.uniform(0, W, n)
        self.my = rnd.uniform(0, H, n)
        self.ax = rnd.uniform(10, 40, n)
        self.ay = rnd.uniform(25, 90, n)
        self.kx = rnd.integers(1, 3, n)
        self.ky = rnd.integers(1, 3, n)
        self.px = rnd.uniform(0, 2 * math.pi, n)
        self.py = rnd.uniform(0, 2 * math.pi, n)
        self.sig = rnd.uniform(0.7, 2.0, n)
        self.base = rnd.uniform(0.18, 0.45, n)
        self.kt = rnd.integers(1, 4, n)

    def field(self, t):
        ph = 2 * math.pi * t / self.period
        m = np.zeros_like(_U)
        for c, w, s, phase in self.bands:
            c = c + 55 * math.sin(ph + phase)
            m += s * np.exp(-((_U - c) / w) ** 2)
        m *= _WINDOW * (0.85 + 0.15 * math.sin(ph))
        return m

    def apply(self, frame, t, mode="screen"):
        low = self.field(t)
        full = np.asarray(Image.fromarray(low, "F").resize((W, H), Image.BILINEAR))[..., None]
        if mode == "screen":
            frame[:] = 1 - (1 - frame) * (1 - self.strength * full * self.light)
        else:  # soft light pattern on a plain paper card
            frame *= 0.95 + 0.08 * full
        self._motes(frame, t, low)

    def _motes(self, frame, t, low):
        ph = 2 * math.pi * t / self.period
        xs = self.mx + self.ax * np.sin(self.kx * ph + self.px)
        ys = self.my + self.ay * np.sin(self.ky * ph + self.py)
        tw = 0.65 + 0.35 * np.sin(self.kt * ph + self.px * 2)
        for x, y, s, b, k in zip(xs, ys, self.sig, self.base, tw):
            lx = int(np.clip(x / LOW, 0, low.shape[1] - 1))
            ly = int(np.clip(y / LOW, 0, low.shape[0] - 1))
            a = b * k * (0.3 + 0.7 * min(1.0, low[ly, lx]))
            r = int(math.ceil(3 * s))
            x0, x1 = max(int(x) - r, 0), min(int(x) + r + 2, W)
            y0, y1 = max(int(y) - r, 0), min(int(y) + r + 2, H)
            if x0 >= x1 or y0 >= y1:
                continue
            gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            g = np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (2 * s * s))[..., None] * a
            region = frame[y0:y1, x0:x1]
            region[:] = 1 - (1 - region) * (1 - g * self.light)


# -------------------------------------------------------------------- segments

class LookSegment:
    def __init__(self, look, duration, seed, loop=False):
        self.d = duration
        self.loop = loop
        src = Image.open(os.path.join(ROOT, look["image"])).convert("RGB")
        self.src = src
        self.s0 = max(W / src.width, H / src.height)
        self.cx = (src.width * self.s0 - W) / 2
        self.cy = (src.height * self.s0 - H) / 2
        self.atmo = Atmosphere(seed, duration)
        ink = rgb(CFG["colors"]["ink"])
        self.accent = rgb(look["accent"])

        self.brand = text_sprite(CFG["brand"].upper(), font("Inter-Medium.otf", 17), 5.2, ink)
        self.label = text_sprite(f"LOOK {look['id']}", font("Inter-Medium.otf", 18), 5.0, ink)
        name_font = fit_font("CormorantGaramond-LightItalic.ttf", 84, look["name"], TEXT_MAX_W)
        self.letters, _ = letter_sprites(look["name"], name_font, 0.5, ink)
        det_font = font("Inter-Regular.otf", 19)
        self.details = [text_sprite(d, det_font, 1.2, ink) for d in look["details"]]

    def zoom(self, t):
        if self.loop:  # in and back out: identical first/last frame
            return 1 + 0.04 * math.sin(math.pi * t / self.d) ** 2, 0.0
        e = ease_in_out_sine(t / self.d)
        return 1.0 + 0.045 * e, -14 * e

    def base(self, t):
        z, pan_y = self.zoom(t)
        px, py = W / 2, H * 0.44
        a = 1 / (z * self.s0)
        c = ((-px) / z + px + self.cx) / self.s0
        f = ((-py) / z + py - pan_y + self.cy) / self.s0
        img = self.src.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, f), Image.BICUBIC)
        return np.asarray(img, dtype=np.float32) / 255.0

    def render(self, t):
        frame = self.base(t)
        self.atmo.apply(frame, t)
        frame *= VIGNETTE
        self.typography(frame, t)
        return frame

    def typography(self, frame, t):
        out_t, out_d = self.d - 1.6, 1.0

        a = fade(t, 0.5, 1.4, out_t, out_d) * 0.82
        blit(frame, self.brand, MARGIN_X, BRAND_Y + 6 * (1 - ease_out_cubic((t - 0.5) / 1.4)), a)

        block = 1 - ease_in_out_sine((t - out_t) / out_d)
        y = BLOCK_Y
        grow = ease_out_cubic((t - 1.0) / 1.2)
        hairline(frame, MARGIN_X, y, 64 * grow, 2, self.accent, 0.9 * block * (grow > 0))

        y += 44
        p = ease_out_cubic((t - 1.3) / 1.1)
        blit(frame, self.label, MARGIN_X, y + 10 * (1 - p), p * block * 0.72)

        y += 84
        for i, s in enumerate(self.letters):
            p = ease_out_cubic((t - 1.6 - i * 0.065) / 1.2)
            blit(frame, s, MARGIN_X, y + 16 * (1 - p), p * block)

        y += 52
        for i, s in enumerate(self.details):
            p = ease_out_cubic((t - 2.5 - i * 0.22) / 1.1)
            blit(frame, s, MARGIN_X, y + i * 32 + 8 * (1 - p), p * block * 0.78)


class CardSegment:
    """Plain paper card with centred title — used as intro and outro."""

    def __init__(self, card, duration, seed, accent):
        self.d = duration
        self.paper = rgb(CFG["colors"]["paper"])
        self.atmo = Atmosphere(seed, duration * 2, motes=26)
        self.accent = rgb(accent)
        ink = rgb(CFG["colors"]["ink"])
        self.kicker = text_sprite(card["kicker"].upper(), font("Inter-Medium.otf", 19), 6.0, ink)
        title_font = fit_font("CormorantGaramond-LightItalic.ttf", 128, card["title"], W - 2 * 110)
        self.letters, self.title_w = letter_sprites(card["title"], title_font, 0.5, ink)
        self.sub = text_sprite(card["subline"].upper(), font("Inter-Regular.otf", 18), 5.0, ink)

    def render(self, t):
        frame = np.empty((H, W, 3), dtype=np.float32)
        frame[:] = self.paper
        self.atmo.apply(frame, t, mode="paper")
        frame *= VIGNETTE
        out_t, out_d = self.d - 1.0, 0.9
        block = 1 - ease_in_out_sine((t - out_t) / out_d)
        cy = H * 0.45

        p = ease_out_cubic((t - 0.2) / 1.2)
        blit(frame, self.kicker, (W - self.kicker.advance) / 2, cy - 120 + 8 * (1 - p), p * block * 0.7)

        x0 = (W - self.title_w) / 2
        for i, s in enumerate(self.letters):
            p = ease_out_cubic((t - 0.45 - i * 0.05) / 1.3)
            blit(frame, s, x0, cy + 18 * (1 - p), p * block)

        grow = ease_out_cubic((t - 1.1) / 1.3)
        half = 40 * grow
        hairline(frame, W / 2 - half, cy + 56, 2 * half, 2, self.accent, 0.9 * block * (grow > 0))

        p = ease_out_cubic((t - 1.5) / 1.2)
        blit(frame, self.sub, (W - self.sub.advance) / 2, cy + 112 + 8 * (1 - p), p * block * 0.7)
        return frame


class Timeline:
    """Segments in sequence, overlapped by a soft cross-dissolve."""

    def __init__(self, segments, xfade=0.8):
        self.items = []
        t = 0.0
        for i, seg in enumerate(segments):
            self.items.append((t, seg))
            t += seg.d - (xfade if i < len(segments) - 1 else 0)
        self.xfade = xfade
        self.duration = t

    def render(self, t):
        active = [(s, seg) for s, seg in self.items if s <= t < s + seg.d]
        if not active:
            active = [self.items[-1]]
        s, seg = active[-1]
        frame = seg.render(min(t - s, seg.d - 1e-3))
        if len(active) > 1:
            s0, prev = active[0]
            w = ease_in_out_sine((t - s) / self.xfade)
            frame = prev.render(t - s0) * (1 - w) + frame * w
        return frame


# ------------------------------------------------------------------------ output

def to_bytes(frame, rng):
    # Tiny dither keeps the soft gradients free of banding after encoding.
    noise = rng.random((H, W, 1), dtype=np.float32) - 0.5
    out = np.clip(frame * 255 + noise, 0, 255).astype(np.uint8)
    return out.tobytes()


_TIMELINE = None


def _work(i):
    rng = np.random.default_rng(i)
    return to_bytes(_TIMELINE.render(i / FPS), rng)


def encode(timeline, path):
    global _TIMELINE
    _TIMELINE = timeline
    n = int(round(timeline.duration * FPS))
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-shortest",
        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.1",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(_work, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if k % FPS == 0:
                print(f"\r  {os.path.basename(path)}  {k / FPS:5.1f}s / {timeline.duration:.1f}s",
                      end="", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit(f"ffmpeg failed for {path}")
    print(f"\r  {os.path.basename(path)}  done ({timeline.duration:.1f}s, {n} frames)      ")


def still(timeline, t, path):
    frame = timeline.render(t)
    img = np.clip(frame * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path, quality=92)


def build():
    looks = CFG["looks"]
    jobs = {}
    for k, look in enumerate(looks):
        jobs[f"look-{look['id']}"] = Timeline([LookSegment(look, 8.0, 100 + k, loop=True)])
    segs = [CardSegment(CFG["intro"], 3.2, 7, looks[0]["accent"])]
    segs += [LookSegment(look, 7.0, 10 + k) for k, look in enumerate(looks)]
    segs.append(CardSegment(CFG["outro"], 3.6, 9, looks[-1]["accent"]))
    jobs["secondchance-reel"] = Timeline(segs)
    return jobs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="render a single video, e.g. look-01 or secondchance-reel")
    ap.add_argument("--stills", action="store_true", help="only write preview stills")
    args = ap.parse_args()

    jobs = build()
    if args.only:
        if args.only not in jobs:
            sys.exit(f"unknown video '{args.only}', choose from: {', '.join(jobs)}")
        jobs = {args.only: jobs[args.only]}

    stills = os.path.join(EXPORT, "stills")
    os.makedirs(stills, exist_ok=True)
    for name, tl in jobs.items():
        still(tl, 4.2 if name.startswith("look") else 2.0, os.path.join(stills, f"{name}-cover.jpg"))
        if not args.stills:
            encode(tl, os.path.join(EXPORT, f"{name}.mp4"))


if __name__ == "__main__":
    main()
