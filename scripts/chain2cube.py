#!/usr/bin/env python3
"""Convert an ffmpeg filter chain into a .cube 3D LUT.

Method: apply the chain to a HALD identity CLUT image, then dump the
result as a .cube (works for any purely per-pixel chain: eq, curves,
colorbalance, colortemperature, vibrance, hue...).

Usage: python3 chain2cube.py "<ffmpeg-chain>" out.cube ["Title"]
"""
import subprocess
import sys
import tempfile
import os
import numpy as np
from PIL import Image

LEVEL = 6  # HALD level 6 -> 216x216 image -> 36^3 LUT
SIZE = LEVEL * LEVEL  # 64


def main():
    chain, out = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(out).replace(".cube", "")
    with tempfile.TemporaryDirectory() as td:
        ident = f"{td}/hald.png"
        graded = f"{td}/hald_out.png"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", f"haldclutsrc={LEVEL}", "-frames:v", "1", ident],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", ident, "-vf", chain, "-frames:v", "1", graded],
            check=True, capture_output=True,
        )
        px = np.asarray(Image.open(graded).convert("RGB"), dtype=np.float64).reshape(-1, 3) / 255.0

    assert px.shape[0] == SIZE ** 3, f"expected {SIZE**3} px, got {px.shape[0]}"
    with open(out, "w") as f:
        f.write(f'TITLE "{title}"\nLUT_3D_SIZE {SIZE}\n')
        # HALD scan order == .cube order (R fastest, then G, then B)
        for r, g, b in px:
            f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
    print(f"{out} ({SIZE}^3)")


if __name__ == "__main__":
    main()
