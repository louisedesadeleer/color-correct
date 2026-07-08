#!/usr/bin/env python3
"""Consensus grade fingerprint: per-frame stats + median/IQR across all frames.
The grade = what survives across every scene; scene color averages out."""
import glob
import numpy as np
from PIL import Image

rows = []
files = sorted(glob.glob("f_*.jpg"))
for path in files:
    im = Image.open(path).convert("RGB")
    im.thumbnail((960, 960))
    rgb = np.asarray(im, dtype=np.float64).reshape(-1, 3)
    luma = 0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2]
    p1, p50, p99 = np.percentile(luma, [1, 50, 99])
    p10, p90 = np.percentile(luma, [10, 90])
    mx, mn = rgb.max(axis=1), rgb.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0).mean() * 100

    def band(lo, hi):
        m = (luma >= lo) & (luma < hi)
        if m.sum() < 100:
            return (np.nan, np.nan)
        px = rgb[m].mean(axis=0)
        return (px[0] - px[2], px[1] - (px[0] + px[2]) / 2)  # R-B, G offset

    srb, sg = band(0, 64)
    mrb, mg = band(64, 160)
    hrb, hg = band(160, 255)
    rows.append([path.replace("f_", "").replace(".jpg", ""), p1, p50, p99, p90 - p10, sat, srb, sg, mrb, mg, hrb, hg])

hdr = ["frame", "p1", "p50", "p99", "spread", "sat%", "shadRB", "shadG", "midRB", "midG", "hiRB", "hiG"]
print(f"{hdr[0]:<18}" + "".join(f"{h:>8}" for h in hdr[1:]))
for r in rows:
    print(f"{r[0]:<18}" + "".join(f"{v:>8.1f}" for v in r[1:]))

data = np.array([r[1:] for r in rows], dtype=float)
med = np.nanmedian(data, axis=0)
q1 = np.nanpercentile(data, 25, axis=0)
q3 = np.nanpercentile(data, 75, axis=0)
print("-" * 114)
print(f"{'MEDIAN':<18}" + "".join(f"{v:>8.1f}" for v in med))
print(f"{'IQR-low':<18}" + "".join(f"{v:>8.1f}" for v in q1))
print(f"{'IQR-high':<18}" + "".join(f"{v:>8.1f}" for v in q3))
