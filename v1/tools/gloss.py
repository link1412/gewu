"""Specular gloss (gloss units, GU) to a microfacet roughness: the GGX (Trowbridge-Reitz) alpha of a smooth
dielectric's surface that a gloss meter would read as the measured value.

    python3 -I tools/gloss.py 46.7 [--n 1.50] [--angle 60]

The meter's geometry is ISO 2813 / ASTM D523: collimated incidence at `angle`, a receptor aperture centred on
the mirror direction, 4.4 x 11.7 degrees at 60 degrees (in the plane of incidence x across it; APERTURE_DEG); gloss is
100 x the flux into it over that of the black-glass standard (n = 1.567, a mirror). The sample's light from
below the surface (its body colour) is left out: a diffuse reflectance of 0.3 puts under 1 GU into that
aperture. Alpha here lumps all the roughness the meter's spot (some mm) averages, waviness included.
"""

import argparse

import numpy as np
from scipy.optimize import brentq

# ISO 2813's receptor aperture, in the plane x across: recalled, not checked against the standard's text [A]
APERTURE_DEG = {60: (4.4, 11.7)}
STANDARD_N = 1.567


def fresnel(cos_i, n):
    s = np.sqrt(np.maximum(0, 1 - (1 - cos_i ** 2) / n ** 2))
    rs = (cos_i - n * s) / (cos_i + n * s)
    rp = (n * cos_i - s) / (n * cos_i + s)
    return 0.5 * (rs ** 2 + rp ** 2)


def ggx_d(cos_h, a):
    return a ** 2 / (np.pi * (cos_h ** 2 * (a ** 2 - 1) + 1) ** 2)


def smith_g1(cos_v, a):
    return 2 / (1 + np.sqrt(1 + a ** 2 * (1 - cos_v ** 2) / cos_v ** 2))


def gloss(a, n, angle_deg, cells=401):
    th = np.radians(angle_deg)
    hin, hacr = (np.radians(x) / 2 for x in APERTURE_DEG[angle_deg])
    wi = np.array([-np.sin(th), 0, np.cos(th)])                 # toward the source
    u, w = np.meshgrid(np.linspace(-hin, hin, cells), np.linspace(-hacr, hacr, cells))
    t = th + u
    wo = np.stack([np.sin(t) * np.cos(w), np.sin(w), np.cos(t) * np.cos(w)], -1)
    h = (wi + wo) / np.linalg.norm(wi + wo, axis=-1)[..., None]
    cos_o = wo[..., 2]
    brdf = (fresnel(h @ wi, n) * ggx_d(h[..., 2], a) * smith_g1(np.cos(th), a) * smith_g1(cos_o, a)
            / (4 * np.cos(th) * cos_o))
    d_omega = (2 * hin / (cells - 1)) * (2 * hacr / (cells - 1)) * np.cos(w)
    reflected = np.sum(brdf * cos_o * d_omega)                  # per unit irradiance
    return 100 * reflected / fresnel(np.cos(th), STANDARD_N)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gu", type=float, help="measured gloss")
    ap.add_argument("--n", type=float, default=1.50, help="the surface's refractive index")
    ap.add_argument("--angle", type=int, default=60, choices=sorted(APERTURE_DEG))
    a = ap.parse_args()
    smooth = 100 * fresnel(np.cos(np.radians(a.angle)), a.n) / fresnel(np.cos(np.radians(a.angle)), STANDARD_N)
    if a.gu >= smooth:
        raise SystemExit(f"{a.gu} GU: a smooth surface of n = {a.n} reads {smooth:.1f} GU at {a.angle} deg")
    alpha = brentq(lambda x: gloss(x, a.n, a.angle) - a.gu, 1e-4, 1.0)
    print(f"{a.gu} GU at {a.angle} deg, n = {a.n} (smooth: {smooth:.1f} GU) -> GGX alpha {alpha:.4f}")


if __name__ == "__main__":
    main()
