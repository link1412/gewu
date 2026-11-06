"""Test a, the scenes: Fresnel reflectance against the angle of incidence, for pbrt's conductor and Cycles' Metallic
BSDF (rgbscene projects eta, k to per-channel values, docs/metals.md).

    python3 -I tests/metals/gen_fresnel.py

A row of eight flat plates of one metal, each tilted so that the camera (3 m away, nearly parallel rays) sees it at
one angle of incidence TH (8 ... 88 degrees) and at the same projected size (12 x 12 mm). Each plate's mirror
direction ends on its own small area light (24 mm, 400 mm away, 5500 K), so a smooth plate shows F(theta) times
the light's radiance; a rough one shows the GGX lobe through that light and its neighbours. A 20 mm light facing
the camera below the row is the white reference (the same radiance). Variants: metal Au / Ag / Cu (pbrt's named
spectra) x alpha 0 / 0.02 / 0.1, and "refl": "spectrum reflectance" (pbrt's eta = 1, k = 2 sqrt(r/(1-r))), alpha 0.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcommon as C  # noqa: E402

RES = (960, 540)
EYE, TARGET, UP = np.array([0.0, 3000.0, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
FOV = 2 * math.degrees(math.atan(90.0 / 3000.0))      # 180 mm high at the plates
TH = [8, 30, 45, 60, 70, 80, 85, 88]
XS = [-140.0 + 40.0 * i for i in range(8)]
PLATE = 12.0                                          # projected size, mm
D_LIGHT, S_LIGHT = 400.0, 24.0
REF_C, REF_S = np.array([0.0, 0.0, -50.0]), 20.0
REFL = "[ 360 0.30 450 0.35 550 0.70 650 0.85 830 0.90 ]"     # a made-up rising reflectance, for the reflectance path
VARIANTS = {f"{m}_a{a:g}": (m, a) for m in ("Au", "Ag", "Cu") for a in (0.0, 0.02, 0.1)}
VARIANTS["refl_a0"] = ("refl", 0.0)


def plate(i):
    """centre, normal, the in-plane axes (x across, t up the slope) and the half lengths."""
    th = math.radians(TH[i])
    n = np.array([0.0, math.cos(th), math.sin(th)])
    t = np.array([0.0, -math.sin(th), math.cos(th)])
    return np.array([XS[i], 0.0, 0.0]), n, np.array([1.0, 0.0, 0.0]), t, PLATE / 2, PLATE / 2 / math.cos(th)


def lights():
    """(centre, normal, e1, e2, half size) of each plate's light: on the mirror ray from the plate's centre."""
    out = []
    for i in range(len(TH)):
        p, n, *_ = plate(i)
        d = (p - EYE) / np.linalg.norm(p - EYE)
        r = d - 2 * (d @ n) * n
        q, ln = p + D_LIGHT * r, -r
        e1 = np.cross([0.0, 0.0, 1.0], ln)
        e1 /= np.linalg.norm(e1)
        out.append((q, ln, e1, np.cross(ln, e1), S_LIGHT / 2))
    return out


def light_text(c, nrm, e1, e2, h):
    P = [c - e1 * h - e2 * h, c + e1 * h - e2 * h, c - e1 * h + e2 * h, c + e1 * h + e2 * h]    # cross(p10-p00, p01-p00) = n
    assert np.cross(P[1] - P[0], P[2] - P[0]) @ nrm > 0
    pts = " ".join(f"{x:.6f}" for p in P for x in p)
    return ('AttributeBegin\n  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 1 ]\n'
            '  Material "diffuse" "rgb reflectance" [ 0 0 0 ]\n'
            f'  Shape "bilinearmesh" "point3 P" [ {pts} ] "integer indices" [ 0 1 2 3 ]\nAttributeEnd\n')


def material_text(metal, alpha):
    if metal == "refl":
        spec = f'"spectrum reflectance" {REFL}'
    else:
        spec = f'"spectrum eta" "metal-{metal}-eta" "spectrum k" "metal-{metal}-k"'
    return f'  Material "conductor" {spec} "float roughness" [ {alpha} ] "bool remaproughness" false\n'


def build(d, spp=128):
    os.makedirs(d, exist_ok=True)
    L = lights()
    for name, (metal, alpha) in VARIANTS.items():
        text = C.header(EYE, TARGET, FOV, RES, spp, UP, filename=f"pbrt_{name}.exr")
        for l in L:
            text += light_text(*l)
        text += light_text(REF_C, np.array([0.0, 1.0, 0.0]), np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), REF_S / 2)
        text += "AttributeBegin\n" + material_text(metal, alpha)
        for i in range(len(TH)):
            c, n, ex, t, hx, ht = plate(i)
            text += C.quad(c - ex * hx - t * ht, c + ex * hx - t * ht, c - ex * hx + t * ht, c + ex * hx + t * ht)
        text += "AttributeEnd\n"
        open(f"{d}/scene_{name}.pbrt", "w").write(text)
        msg = C.rgbscene(f"{d}/scene_{name}.pbrt", f"{d}/scene_{name}.cycles.json")
        print(name, msg.strip().splitlines()[0])


if __name__ == "__main__":
    build(os.path.join(C.OUT, "fresnel"))
