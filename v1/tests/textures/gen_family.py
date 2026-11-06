"""Test c, the scene: two flat diffuse tiles under two side lights, camera straight above, each tile's reflectance
a family of spectra R(lambda; c) indexed by a horizontal ramp of c (our "familymap" texture, Cycles only).
  tile A: uneven c rows, ramp stored as EXR (half floats), runs beyond both ends of the family (clamping);
  tile B: even c rows (the table goes into the LUT as it is), ramp stored as PFM (float), also beyond both ends.
The family is Beer-Lambert absorption, R = 0.9 exp(-c kappa(lambda)), kappa a band at 600 nm: a stand-in for any
concentration-indexed family (cobalt in glaze, ink in paper), here made up, not a measured material.
Variants: fam (the family), ref (the same tiles with reflectance 0.5 everywhere: the illumination's shape).

    python3 -I tests/textures/gen_family.py
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

RES = (960, 540)
EYE, TARGET, UP, FOV = (0, 0, 100), (0, 0, 0), (0, 1, 0), 15.4
TILES = {"A": dict(x0=-22.0, x1=-2.0, c=[0, 0.1, 0.25, 0.5, 0.8, 1.1, 1.4, 1.7, 2.0], ramp=(-0.3, 2.3), file="ramp_a.exr"),
         "B": dict(x0=2.0, x1=22.0, c=list(np.linspace(0, 1, 11)), ramp=(-0.2, 1.3), file="ramp_b.pfm")}
LAM = np.arange(360.0, 831.0, 5.0)
Y0, Y1 = -8.0, 8.0
W = 1024


def family(c):
    kappa = 1.2 * np.exp(-0.5 * ((LAM - 600.0) / 40.0) ** 2) + 0.15
    return 0.9 * np.exp(-np.outer(c, kappa))


def build(d, spp=64):
    os.makedirs(d, exist_ok=True)
    for k, t in TILES.items():
        np.savez(f"{d}/family_{k.lower()}.npz", lambda_nm=LAM, c=np.array(t["c"], float), R=family(np.array(t["c"], float)))
        u = (np.arange(W) + 0.5) / W
        ramp = np.tile(t["ramp"][0] + (t["ramp"][1] - t["ramp"][0]) * u, (8, 1))
        (C.write_exr if t["file"].endswith(".exr") else C.write_pfm)(f"{d}/{t['file']}", ramp)
    lights = (C.light_quad((-70, 0, 50), (1, 0, -0.7), None, 10, rect=(100, 100))
              + C.light_quad((70, 0, 50), (-1, 0, -0.7), None, 10, rect=(100, 100)))
    for var in ("fam", "ref"):
        text = C.header(EYE, TARGET, FOV, RES, spp, UP, filename=f"{var}.exr") + lights
        for k, t in TILES.items():
            if var == "fam":
                text += (f'Texture "fam{k}" "spectrum" "familymap" "string family" "family_{k.lower()}.npz" '
                         f'"string map" "{t["file"]}" "string wrap" "clamp"\n')
                mat = f'"texture reflectance" "fam{k}"'
            else:
                mat = '"float reflectance" 0.5'
            text += (f'AttributeBegin\n  Material "diffuse" {mat}\n'
                     + C.quad((t["x0"], Y0, 0), (t["x1"], Y0, 0), (t["x0"], Y1, 0), (t["x1"], Y1, 0)) + "AttributeEnd\n")
        open(f"{d}/scene_{var}.pbrt", "w").write(text)
        subprocess.run([sys.executable, "-I", os.path.join(C.ROOT, "tools/rgbscene.py"), f"{d}/scene_{var}.pbrt",
                        "-o", f"{d}/scene_{var}.cycles.json"], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    build(os.path.join(C.OUT, "family"))
