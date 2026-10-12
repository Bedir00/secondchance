#!/usr/bin/env python3
"""Finish the Look 04 reel: quiet motion graphics on top of the filmed clip.

  - the hard cut in the source becomes a short, soft cross-dissolve
  - part 1 (selfie walk): two labels with prices, each with a thin white
    arrow that draws itself to the piece and follows it (optical-flow tracking)
  - part 2 (tripod): labels fade out, a soft scrim rises from the bottom and
    the bundle CTA appears line by line
  - opens from and closes to black, so the Instagram loop has no jump
All type is Montserrat in the CI colour (see motion/look-04-video.json).

Usage:
  python3 motion/render_video.py            # video + stills into export/
  python3 motion/render_video.py --stills   # only stills
  python3 motion/render_video.py --debug    # stills with tracked points marked
"""

import argparse
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image

import render
from render import H, W, arrow, ease_in_out_sine, ease_out_cubic, hairline, rgb
from render_cta import SCRIM, fit, mont, put, text_pair

ROOT = render.ROOT

with open(os.path.join(ROOT, "motion", "look-04-video.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)

FPS = CFG["fps"]
BRAND_Y = 236


# ----------------------------------------------------------------------- source

def decode(path):
    """All frames of the source, scaled to fill 1080×1920 (centre crop)."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    sw, sh = map(int, probe.stdout.strip().split(","))
    scale = max(W / sw, H / sh)
    tw, th = round(sw * scale / 2) * 2, round(sh * scale / 2) * 2
    vf = f"scale={tw}:{th}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.3"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def track(frames, start, stop, region, targets):
    """Follow `targets` (points in frame `start`) through frames start..stop-1.

    Features inside `region` (x0, y0, x1, y1 — around the piece) are tracked with
    pyramidal Lucas-Kanade; a RANSAC similarity transform per frame moves the
    targets along. Done at half resolution, then lightly smoothed.
    """
    k = 0.5
    gray = lambda i: cv2.cvtColor(cv2.resize(frames[i], None, fx=k, fy=k, interpolation=cv2.INTER_AREA),
                                  cv2.COLOR_RGB2GRAY)
    box = np.float32([[region[0], region[1]], [region[2], region[1]],
                      [region[2], region[3]], [region[0], region[3]]]) * k
    pts_t = np.float32(targets) * k
    out = [pts_t.copy()]
    prev = gray(start)
    for i in range(start + 1, stop):
        cur = gray(i)
        mask = np.zeros_like(prev)
        cv2.fillConvexPoly(mask, box.astype(np.int32), 255)
        feats = cv2.goodFeaturesToTrack(prev, 400, 0.01, 6, mask=mask)
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, feats, None, winSize=(31, 31), maxLevel=4)
        ok = st.ravel() == 1
        m, _ = cv2.estimateAffinePartial2D(feats[ok], nxt[ok], method=cv2.RANSAC,
                                           ransacReprojThreshold=2.0)
        if m is None:
            m = np.float32([[1, 0, 0], [0, 1, 0]])
        apply = lambda p: p @ m[:, :2].T + m[:, 2]
        pts_t, box = apply(pts_t), apply(box)
        out.append(pts_t.copy())
        prev = cur
    path = np.array(out) / k  # (frames, targets, 2)
    kernel = np.ones(7) / 7
    padded = np.pad(path, ((3, 3), (0, 0), (0, 0)), mode="edge")
    smooth = np.empty_like(path)
    for j in range(path.shape[1]):
        for c in range(2):
            smooth[:, j, c] = np.convolve(padded[:, j, c], kernel, "valid")
    return smooth


# ------------------------------------------------------------------------- reel

class Reel:
    def __init__(self, frames):
        self.frames = frames
        cut, d = CFG["cut_frame"], CFG["dissolve_frames"]
        self.cut, self.dis = cut, d
        self.n = len(frames) - d
        self.duration = self.n / FPS

        items = CFG["items"]
        # each piece is followed with features from its own region
        self.paths = np.concatenate([track(frames, 0, cut, it["track"], [it["to"]]) for it in items], axis=1)

        white = rgb(CFG["text_color"])
        self.white = white
        self.brand = text_pair(CFG["brand"].upper(), mont("Medium", 19), 6.0, white, 0.3)
        self.items = []
        name_f, price_f = mont("Medium", 20), mont("Light", 36)
        for it in items:
            name = text_pair(it["name"].upper(), name_f, 4.5, white)
            price = text_pair(it["price"], price_f, 0.5, white)
            right, base = it["at"]
            left = right - max(name[0].advance, price[0].advance)
            self.items.append((name, price, right, base, (left - 18, base + 6), it["bend"]))

        cta = CFG["cta"]
        l1 = fit("Light", 54, cta["lines"][0], W - 2 * 100, 0.3)
        l2 = fit("Medium", l1.size, cta["lines"][1], W - 2 * 100, 0.3)
        self.lines = [text_pair(cta["lines"][0], l1, 0.3, white, 0.35, 4),
                      text_pair(cta["lines"][1], l2, 0.3, white, 0.35, 4)]
        self.prices = text_pair(cta["prices"], mont("Regular", 25), 1.5, white, 0.35, 3)

    def footage(self, i):
        """Output frame i: part 1, a soft dissolve over the cut, then part 2."""
        cut, d = self.cut, self.dis
        if i < cut - d:
            return self.frames[i].astype(np.float32) / 255
        if i < cut:
            k = i - (cut - d)
            w = ease_in_out_sine((k + 0.5) / d)
            a = self.frames[i].astype(np.float32)
            b = self.frames[cut + k].astype(np.float32)
            return (a * (1 - w) + b * w) / 255
        return self.frames[i + d].astype(np.float32) / 255

    def render(self, i):
        t = i / FPS
        frame = self.footage(i)
        T = CFG["timing"]

        scrim = ease_in_out_sine((t - T["scrim"]) / 1.0)
        if scrim > 0:
            frame *= 1 - scrim * SCRIM

        p = ease_out_cubic((t - 0.4) / 1.4)
        put(frame, self.brand, (W - self.brand[0].advance) / 2, BRAND_Y + 6 * (1 - p), p * 0.9)

        self.callouts(frame, t, i)
        self.cta(frame, t)

        black = ease_out_cubic(t / 0.5) * (1 - ease_in_out_sine((t - (self.duration - 0.45)) / 0.45))
        frame *= black
        return frame

    def callouts(self, frame, t, i):
        T = CFG["timing"]
        out = 1 - ease_in_out_sine((t - T["labels_out"]) / 0.6)
        if out <= 0 or i >= len(self.paths):
            return
        for j, (name, price, right, base, start, bend) in enumerate(self.items):
            t0 = T["labels_in"] + j * 0.6
            p = ease_out_cubic((t - t0) / 1.0)
            put(frame, name, right - name[0].advance, base - 44 + 10 * (1 - p), p * out * 0.92)
            q = ease_out_cubic((t - t0 - 0.15) / 1.0)
            put(frame, price, right - price[0].advance, base + 4 + 10 * (1 - q), q * out)
            draw = ease_in_out_sine((t - t0 - 0.35) / 1.1)
            arrow(frame, start, self.paths[i, j], bend, draw, 0.95 * out, self.white, width=2.2, head=14)

    def cta(self, frame, t):
        t0 = CFG["timing"]["cta"]
        grow = ease_out_cubic((t - t0) / 1.0)
        if grow > 0:
            hairline(frame, W / 2 - 30 * grow, 1236, 60 * grow, 2, self.white, 0.85)
        y = 1318
        for k, pair in enumerate(self.lines):
            p = ease_out_cubic((t - t0 - 0.25 - k * 0.3) / 1.1)
            put(frame, pair, (W - pair[0].advance) / 2, y + 14 * (1 - p), p)
            y += 68
        p = ease_out_cubic((t - t0 - 1.0) / 1.1)
        put(frame, self.prices, (W - self.prices[0].advance) / 2, 1452 + 10 * (1 - p), p * 0.92)


# ----------------------------------------------------------------------- output

_REEL = None


def _work(i):
    rng = np.random.default_rng(i)
    return render.to_bytes(_REEL.render(i), rng)


def encode(reel, path):
    global _REEL
    _REEL = reel
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.1",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(_work, range(reel.n), chunksize=4)):
            proc.stdin.write(buf)
            if k % FPS == 0:
                print(f"\r  {os.path.basename(path)}  {k / FPS:4.1f}s / {reel.duration:.1f}s", end="", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit(f"ffmpeg failed for {path}")
    print(f"\r  {os.path.basename(path)}  done ({reel.duration:.2f}s, {reel.n} frames)      ")


def save(frame, path):
    Image.fromarray(np.clip(frame * 255 + 0.5, 0, 255).astype(np.uint8)).save(path, quality=92)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stills", action="store_true", help="only write stills")
    ap.add_argument("--debug", action="store_true", help="stills with the tracked points marked")
    args = ap.parse_args()

    src = os.path.join(ROOT, CFG["source"])
    reel = Reel(decode(src))
    name = CFG["output"]
    stills = os.path.join(render.EXPORT, "stills")
    os.makedirs(stills, exist_ok=True)

    if args.debug:
        dbg = os.path.join(ROOT, "motion", "debug")
        os.makedirs(dbg, exist_ok=True)
        for i in range(0, reel.cut, 12):
            img = (reel.footage(i) * 255).astype(np.uint8).copy()
            for p in reel.paths[i]:
                cv2.circle(img, tuple(int(v) for v in p), 12, (255, 0, 0), 3)
            Image.fromarray(img).resize((360, 640)).save(os.path.join(dbg, f"track-{i:03d}.jpg"))
        return

    for label, t in (("prices", 3.0), ("cta", 7.2)):
        save(reel.render(int(t * FPS)), os.path.join(stills, f"{name}-{label}.jpg"))
    if not args.stills:
        encode(reel, os.path.join(render.EXPORT, f"{name}.mp4"))


if __name__ == "__main__":
    main()
