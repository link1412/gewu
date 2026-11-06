"""Test a, the scene: a flat smooth dielectric slab (n 1.5) with a sinusoidal bump map, a small area light, the
camera near the specular angle. Variants: bump (the map), zero (a zero map), plain (no texture), ply (the map, the slab a plymesh with u, v), png (the map as a 16-bit PNG).

    python3 -I tests/textures/gen_bump.py

The map file holds sin(2 pi x / P) over the slab (u = (x + 20) / 40) and the texture's "scale" is the amplitude,
in mm, so both are exercised. The slope amplitude A k = 0.05.
"""
import math
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

RES = (960, 540)
EYE, TARGET, UP, FOV = (0, -212.132, 212.132), (0, 0, 0), (0, 0, 1), 3.86      # 300 mm away, 36 mm across
PERIOD, SLOPE, HALF = 4.0, 0.05, 20.0
AMP = SLOPE * PERIOD / (2 * math.pi)                   # mm
# The light is 1 m away and 60 mm wide (0.06 rad), 30 mm off the mirror image of the eye: the reflected direction
# must be 0 to 0.06 rad off the flat mirror's, so only slopes of one sign (and a part of them) show, asymmetric stripes
LIGHT_C, LIGHT_SIZE = (30.0, 707.107, 707.107), (60.0, 120.0)


LIGHT_N = tuple(-np.array(LIGHT_C))


def build(d, spp=64):
    os.makedirs(d, exist_ok=True)
    W = 4096
    x = -HALF + 2 * HALF * (np.arange(W) + 0.5) / W
    C.write_pfm(f"{d}/sine.pfm", np.tile(np.sin(2 * math.pi * x / PERIOD), (8, 1)))
    # the same map as a 16-bit PNG, 0.5 + 0.5 sin, so with "float scale" 2A and "string encoding" "linear"
    q = np.round(65535 * (0.5 + 0.5 * np.sin(2 * math.pi * x / PERIOD))).astype("<u2")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray16le",
                    "-s", f"{W}x8", "-i", "-", "-frames:v", "1", f"{d}/sine16.png"], input=np.tile(q, (8, 1)).tobytes(), check=True)
    C.write_pfm(f"{d}/zero.pfm", np.zeros((8, W)))
    slab = C.quad((-HALF, -HALF, 0), (HALF, -HALF, 0), (-HALF, HALF, 0), (HALF, HALF, 0))
    # the same slab as a plymesh with "u","v" vertex properties (test a's UV check)
    open(f"{d}/slab.ply", "w").write("ply\nformat ascii 1.0\nelement vertex 4\nproperty float x\nproperty float y\nproperty float z\n"
                                   "property float u\nproperty float v\nelement face 2\nproperty list uchar int vertex_indices\nend_header\n"
                                   f"{-HALF} {-HALF} 0 0 0\n{HALF} {-HALF} 0 1 0\n{HALF} {HALF} 0 1 1\n{-HALF} {HALF} 0 0 1\n3 0 1 2\n3 0 2 3\n")
    for var in ("bump", "zero", "plain", "ply", "png"):
        tex = {"png": f'Texture "h" "float" "imagemap" "string filename" "sine16.png" "string encoding" "linear" "float scale" {2 * AMP} "string wrap" "clamp"\n',
               "ply": f'Texture "h" "float" "imagemap" "string filename" "sine.pfm" "float scale" {AMP} "string wrap" "clamp"\n',
               "bump": f'Texture "h" "float" "imagemap" "string filename" "sine.pfm" "float scale" {AMP} "string wrap" "clamp"\n',
               "zero": 'Texture "h" "float" "imagemap" "string filename" "zero.pfm" "float scale" 1 "string wrap" "clamp"\n',
               "plain": ""}[var]
        disp = '' if var == "plain" else ' "texture displacement" "h"'
        text = (C.header(EYE, TARGET, FOV, RES, spp, UP, filename=f"pbrt_{var}.exr")
                + C.light_quad(LIGHT_C, LIGHT_N, None, 20, rect=LIGHT_SIZE) + tex
                + f'AttributeBegin\n  Material "dielectric" "float eta" 1.5 "bool remaproughness" false{disp}\n' + (slab if var != "ply" else '  Shape "plymesh" "string filename" "slab.ply"\n') + 'AttributeEnd\n')
        open(f"{d}/scene_{var}.pbrt", "w").write(text)
        subprocess.run([sys.executable, "-I", os.path.join(C.ROOT, "tools/rgbscene.py"), f"{d}/scene_{var}.pbrt",
                        "-o", f"{d}/scene_{var}.cycles.json"], check=True)


if __name__ == "__main__":
    build(os.path.join(C.OUT, "bump"))
