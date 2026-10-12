#!/usr/bin/env python3
"""Look 04 with prices and a bundle CTA (9:16, Montserrat, #FEFEFE).

Two calm scenes on one slow push-in:
  1. a thin white arrow draws from each label (piece + price) to the piece
  2. the labels fade out, a soft scrim rises from the bottom and the CTA
     appears line by line
The clip opens from and closes to black, so it loops without a jump.

Usage:
  python3 motion/render_cta.py           # video + cover still into export/
  python3 motion/render_cta.py --stills  # only preview stills
"""

import argparse
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import render
from render import (H, W, Sprite, arrow, blit, ease_in_out_sine, ease_out_cubic, encode,
                    hairline, rgb)

ROOT = render.ROOT
FONTS = render.FONTS

with open(os.path.join(ROOT, "motion", "look-04.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)

BRAND_Y = 236
PIVOT = (W / 2, 820)  # push-in centres on the outfit


def mont(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, f"Montserrat-{weight}.ttf"), size)


def text_pair(text, fnt, tracking, color, shadow=0.42, blur=3.0):
    """Text sprite plus a soft dark shadow sprite that keeps it readable on the wall.

    Origin is the left baseline; `.advance` is the set width.
    """
    ascent, descent = fnt.getmetrics()
    pad = 14
    width = int(math.ceil(fnt.getlength(text) + tracking * max(0, len(text) - 1))) + 2 * pad
    img = Image.new("L", (width, ascent + descent + 2 * pad), 0)
    draw = ImageDraw.Draw(img)
    for i, ch in enumerate(text):
        draw.text((pad + fnt.getlength(text[:i]) + tracking * i, pad + ascent), ch,
                  font=fnt, fill=255, anchor="ls")
    a = np.asarray(img, np.float32)[..., None] / 255.0
    sh = np.asarray(img.filter(ImageFilter.GaussianBlur(blur)), np.float32)[..., None] / 255.0
    sh = np.clip(sh * 1.4, 0, 1) * shadow
    txt = Sprite(np.concatenate([a * color, a], axis=2), -pad, -pad - ascent)
    shd = Sprite(np.concatenate([np.zeros_like(a).repeat(3, axis=2), sh], axis=2), -pad, -pad - ascent + 2)
    txt.advance = shd.advance = width - 2 * pad
    return txt, shd


def put(frame, pair, x, y, alpha):
    txt, shd = pair
    blit(frame, shd, x, y, alpha)
    blit(frame, txt, x, y, alpha)


def fit(weight, size, text, max_w, tracking=0.0):
    while size > 20:
        f = mont(weight, size)
        if f.getlength(text) + tracking * (len(text) - 1) <= max_w:
            return f
        size -= 1
    return mont(weight, 20)


_ys = np.arange(H, dtype=np.float32)
_s = np.clip((_ys - 960) / (H - 960), 0, 1)
SCRIM = (_s * _s * (3 - 2 * _s) * 0.66)[:, None, None]  # smoothstep, darkest at the bottom
VIGNETTE = render.VIGNETTE


class CtaLook:
    def __init__(self):
        self.d = CFG["duration"]
        self.src = Image.open(os.path.join(ROOT, CFG["image"])).convert("RGB")
        self.s0 = max(W / self.src.width, H / self.src.height)
        self.cx = (self.src.width * self.s0 - W) / 2
        self.cy = (self.src.height * self.s0 - H) / 2
        self.white = rgb(CFG["text_color"])

        white = self.white
        self.brand = text_pair(CFG["brand"].upper(), mont("Medium", 19), 6.0, white, 0.3)

        self.items = []
        name_f, price_f = mont("Medium", 20), mont("Light", 36)
        for it in CFG["items"]:
            name = text_pair(it["name"].upper(), name_f, 4.5, white)
            price = text_pair(it["price"], price_f, 0.5, white)
            right, base = it["at"]
            left = right - max(name[0].advance, price[0].advance)
            start = (left - 18, base + 6)
            self.items.append((name, price, right, base, start, it["to"], it["bend"]))

        cta = CFG["cta"]
        l1 = fit("Light", 54, cta["lines"][0], W - 2 * 100, 0.3)
        l2 = fit("Medium", l1.size, cta["lines"][1], W - 2 * 100, 0.3)
        self.lines = [text_pair(cta["lines"][0], l1, 0.3, white, 0.35, 4),
                      text_pair(cta["lines"][1], l2, 0.3, white, 0.35, 4)]
        self.prices = text_pair(cta["prices"], mont("Regular", 25), 1.5, white, 0.35, 3)

    # ---------------------------------------------------------------- camera

    def zoom(self, t):
        return 1.0 + 0.05 * ease_in_out_sine(t / self.d)

    def track(self, p, t):
        z = self.zoom(t)
        return (PIVOT[0] + (p[0] - PIVOT[0]) * z, PIVOT[1] + (p[1] - PIVOT[1]) * z)

    def base(self, t):
        z = self.zoom(t)
        a = 1 / (z * self.s0)
        c = (-PIVOT[0] / z + PIVOT[0] + self.cx) / self.s0
        f = (-PIVOT[1] / z + PIVOT[1] + self.cy) / self.s0
        img = self.src.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, f), Image.BICUBIC)
        return np.asarray(img, dtype=np.float32) / 255.0

    # ---------------------------------------------------------------- frame

    def render(self, t):
        frame = self.base(t)
        frame *= VIGNETTE

        # scene 2: soft scrim rises before the CTA text
        scrim = ease_in_out_sine((t - 6.9) / 1.3)
        if scrim > 0:
            frame *= 1 - scrim * SCRIM

        self.brand_mark(frame, t)
        self.callouts(frame, t)
        self.cta(frame, t)

        # open from / close to black for a clean loop
        black = ease_out_cubic(t / 0.9) * (1 - ease_in_out_sine((t - (self.d - 0.9)) / 0.9))
        frame *= black
        return frame

    def brand_mark(self, frame, t):
        p = ease_out_cubic((t - 0.6) / 1.4)
        txt = self.brand[0]
        put(frame, self.brand, (W - txt.advance) / 2, BRAND_Y + 6 * (1 - p), p * 0.9)

    def callouts(self, frame, t):
        out = 1 - ease_in_out_sine((t - 6.6) / 0.9)
        if out <= 0:
            return
        for i, (name, price, right, base, start, target, bend) in enumerate(self.items):
            t0 = 1.3 + i * 0.9
            p = ease_out_cubic((t - t0) / 1.1)
            rise = 10 * (1 - p)
            put(frame, name, right - name[0].advance, base - 44 + rise, p * out * 0.92)
            q = ease_out_cubic((t - t0 - 0.18) / 1.1)
            put(frame, price, right - price[0].advance, base + 4 + 10 * (1 - q), q * out)
            draw = ease_in_out_sine((t - t0 - 0.45) / 1.3)
            arrow(frame, start, self.track(target, t), bend, draw, 0.95 * out, self.white,
                  width=2.2, head=14)

    def cta(self, frame, t):
        y = 1236
        grow = ease_out_cubic((t - 7.5) / 1.2)
        half = 30 * grow
        if grow > 0:
            hairline(frame, W / 2 - half, y, 2 * half, 2, self.white, 0.85)

        y = 1318
        for i, pair in enumerate(self.lines):
            p = ease_out_cubic((t - 7.8 - i * 0.3) / 1.2)
            put(frame, pair, (W - pair[0].advance) / 2, y + 14 * (1 - p), p)
            y += 68

        p = ease_out_cubic((t - 8.7) / 1.2)
        put(frame, self.prices, (W - self.prices[0].advance) / 2, 1452 + 10 * (1 - p), p * 0.92)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stills", action="store_true", help="only write preview stills")
    args = ap.parse_args()

    clip = CtaLook()
    clip.duration = clip.d
    name = CFG["output"]
    stills = os.path.join(render.EXPORT, "stills")
    os.makedirs(stills, exist_ok=True)
    for label, t in (("cover", 5.5), ("cta", 12.0)):
        render.still(clip, t, os.path.join(stills, f"{name}-{label}.jpg"))
    if not args.stills:
        encode(clip, os.path.join(render.EXPORT, f"{name}.mp4"))


if __name__ == "__main__":
    main()
