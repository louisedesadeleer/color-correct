#!/usr/bin/env python3
"""Measure the color grade of a frame: tonal ranges, tints, saturation, contrast.

Usage: python3 measure.py frame1.jpg [frame2.jpg ...]

For each frame prints a compact grade fingerprint:
- luma percentiles (p1/p10/p50/p90/p99) -> exposure + contrast + lifted/crushed blacks
- shadow / midtone / highlight mean RGB and cast (R-B, G-mid offsets)
- mean saturation (HSV S) overall + per tonal band
- rough color temperature read (R/B balance in neutrals)
"""
import sys
import numpy as np
from PIL import Image


def band_stats(rgb, luma, lo, hi):
    mask = (luma >= lo) & (luma < hi)
    if mask.sum() < 100:
        return None
    px = rgb[mask]
    mean = px.mean(axis=0)
    return mean


def analyze(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((960, 960))
    rgb = np.asarray(im, dtype=np.float64)
    flat = rgb.reshape(-1, 3)
    luma = 0.2126 * flat[:, 0] + 0.7152 * flat[:, 1] + 0.0722 * flat[:, 2]

    p = np.percentile(luma, [1, 10, 50, 90, 99])

    # saturation via HSV
    mx = flat.max(axis=1)
    mn = flat.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)

    bands = {
        "shadows  (0-64)": band_stats(flat, luma, 0, 64),
        "mids   (64-160)": band_stats(flat, luma, 64, 160),
        "highs (160-255)": band_stats(flat, luma, 160, 255),
    }

    print(f"\n=== {path} ===")
    print(f"luma p1/p10/p50/p90/p99: {p[0]:.0f} / {p[1]:.0f} / {p[2]:.0f} / {p[3]:.0f} / {p[4]:.0f}")
    print(f"  -> black floor {'LIFTED (matte)' if p[0] > 8 else 'deep'} | white ceiling {'pulled down' if p[4] < 245 else 'full'} | spread(p90-p10) {p[3]-p[1]:.0f}")
    print(f"mean saturation: {sat.mean()*100:.1f}%   (p90 sat: {np.percentile(sat,90)*100:.0f}%)")
    for name, mean in bands.items():
        if mean is None:
            print(f"{name}: (too few px)")
            continue
        r, g, b = mean
        avg = mean.mean()
        # cast: positive = warm/red, negative = cool/blue; green offset vs neutral
        cast_rb = r - b
        cast_g = g - (r + b) / 2
        tilt = "warm" if cast_rb > 3 else ("cool" if cast_rb < -3 else "neutral")
        gtilt = "green" if cast_g > 3 else ("magenta" if cast_g < -3 else "")
        print(f"{name}: RGB {r:.0f},{g:.0f},{b:.0f}  cast: {tilt} {gtilt} (R-B {cast_rb:+.1f}, G {cast_g:+.1f})")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        analyze(f)
