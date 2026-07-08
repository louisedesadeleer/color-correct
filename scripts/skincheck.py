#!/usr/bin/env python3
"""Skin-tone safety gate: compare skin pixels before vs after a grade.

Usage: python3 skincheck.py original.jpg graded.jpg

Detects likely-skin pixels in the ORIGINAL (classic YCbCr chroma box),
then measures how the grade moved those same pixels:
- hue shift (degrees)   — the killer metric; >6 deg reads as wrong skin
- saturation change (%) — oompa-loompa (+) or corpse (-) risk
- luma change           — did the grade darken/brighten faces

Verdict: PASS / SOFTEN (halve the look) / FAIL (rethink the grade).
Exit code 0 = pass, 1 = soften, 2 = fail (script-friendly).
"""
import sys
import numpy as np
from PIL import Image

HUE_SOFTEN, HUE_FAIL = 6.0, 10.0       # degrees (calibrated: approved subtle looks pass)
SAT_SOFTEN, SAT_FAIL = 25.0, 45.0      # relative %
MIN_SKIN_FRACTION = 0.02               # need >2% of frame to judge


def load(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((960, 960))
    return np.asarray(im, dtype=np.float64)


def skin_mask(rgb):
    """Tightened YCbCr skin box + saturation bounds.

    The classic box (Cb 77-127, Cr 133-173) also matches beige walls,
    concrete and blonde hair — measured 41% "skin" on an outdoor talking
    head. Tighter chroma + requiring moderate saturation rejects most
    architecture while keeping real skin."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
    cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    return (
        (cb >= 90) & (cb <= 120) & (cr >= 140) & (cr <= 165)
        & (y > 60) & (y < 235) & (sat > 0.15) & (sat < 0.65)
    )


def hue_sat_luma(px):
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    mx, mn = px.max(axis=1), px.min(axis=1)
    delta = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / delta) % 6,
        np.where(mx == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60.0
    s = np.where(mx > 0, delta / np.maximum(mx, 1e-6), 0)
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # circular mean of hue
    rad = np.deg2rad(h)
    mean_h = np.rad2deg(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())) % 360
    return mean_h, s.mean() * 100, y.mean()


def main():
    orig, graded = load(sys.argv[1]), load(sys.argv[2])
    if orig.shape != graded.shape:
        h = min(orig.shape[0], graded.shape[0]); w = min(orig.shape[1], graded.shape[1])
        orig, graded = orig[:h, :w], graded[:h, :w]

    mask = skin_mask(orig)
    frac = mask.mean()
    if frac < MIN_SKIN_FRACTION:
        print(f"skin: {frac*100:.2f}% of frame — too little to judge (b-roll?). SKIP")
        sys.exit(0)

    h0, s0, y0 = hue_sat_luma(orig[mask])
    h1, s1, y1 = hue_sat_luma(graded[mask])
    dh = (h1 - h0 + 180) % 360 - 180  # signed shortest hue distance
    ds = (s1 - s0) / max(s0, 1e-6) * 100
    dy = y1 - y0

    print(f"skin px: {frac*100:.1f}% of frame")
    print(f"hue:  {h0:.1f} -> {h1:.1f} deg  (shift {dh:+.1f} deg)")
    print(f"sat:  {s0:.1f}% -> {s1:.1f}%  ({ds:+.1f}% relative)")
    print(f"luma: {y0:.0f} -> {y1:.0f}  ({dy:+.0f})")

    if abs(dh) >= HUE_FAIL or abs(ds) >= SAT_FAIL:
        print("VERDICT: FAIL — grade breaks skin; rethink (fix WB first? wrong look?)")
        sys.exit(2)
    if abs(dh) >= HUE_SOFTEN or abs(ds) >= SAT_SOFTEN:
        print("VERDICT: SOFTEN — halve the look strength and re-check")
        sys.exit(1)
    print("VERDICT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
