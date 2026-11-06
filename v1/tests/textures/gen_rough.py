"""Test b, the scene: a glossy dielectric slab (n 1.5, "bool remaproughness" false) whose roughness (alpha) is a
step map: A1 on the left half (x < 0), A2 on the right. Variants: step, uni1 (uniform A1), uni2 (uniform A2).

    python3 -I tests/textures/gen_rough.py
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

RES = (960, 540)
EYE, TARGET, UP, FOV = (0, -212.132, 212.132), (0, 0, 0), (0, 0, 1), 3.86      # as the bump test
HALF = 20.0
A1, A2 = 0.03, 0.10
LIGHT_C, LIGHT_SIZE = (0.0, 707.107, 707.107), (120.0, 120.0)             # 1 m away, 0.12 rad: the mirror image
LIGHT_N = (0, -1, -1)


def build(d, spp=128):
    os.makedirs(d, exist_ok=True)
    W = 1024
    step = np.where((np.arange(W) + 0.5) / W < 0.5, A1, A2)
    C.write_pfm(f"{d}/step.pfm", np.tile(step, (8, 1)))
    slab = C.quad((-HALF, -HALF, 0), (HALF, -HALF, 0), (-HALF, HALF, 0), (HALF, HALF, 0))
    for var, rough in (("step", '"texture roughness" "r"'), ("uni1", f'"float roughness" {A1}'), ("uni2", f'"float roughness" {A2}')):
        tex = 'Texture "r" "float" "imagemap" "string filename" "step.pfm" "string wrap" "clamp"\n' if var == "step" else ""
        text = (C.header(EYE, TARGET, FOV, RES, spp, UP, filename=f"pbrt_{var}.exr")
                + C.light_quad(LIGHT_C, LIGHT_N, None, 20, rect=LIGHT_SIZE) + tex
                + f'AttributeBegin\n  Material "dielectric" "float eta" 1.5 "bool remaproughness" false {rough}\n' + slab + "AttributeEnd\n")
        open(f"{d}/scene_{var}.pbrt", "w").write(text)
        subprocess.run([sys.executable, "-I", os.path.join(C.ROOT, "tools/rgbscene.py"), f"{d}/scene_{var}.pbrt",
                        "-o", f"{d}/scene_{var}.cycles.json"], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    build(os.path.join(C.OUT, "rough"))
