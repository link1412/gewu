"""Fit the glaze's scattering coefficient to the measured colour of Guan fenqing glaze.

    python3 -I shots/06-guan/glaze_fit.py [--photons 100000] [--invert] [--glaze-mm 1.2]

Nothing measured gives Guan's scattering coefficient: the literature brackets it at 1.5-15 /mm (bubbles of
Longquan glaze, geometric cross-section; docs/shots/06-guan.md, 釉). We pick the value inside that bracket
whose glaze, over the body, has the measured colour: L*a*b* (51.85, -3.67, 7.46), Guan fenqing, n = 2
(Yu et al. 2021, NF-333 colorimeter; illuminant and geometry not stated: D65 2 deg assumed, and both
specular included (SCI, + F(8 deg)) and excluded (SCE) are reported).

The model, as the renderer sees it: a slab of the glaze (thickness GLAZE_MM, smooth surface of index ETA,
homogeneous medium: sigma_a(lambda) from the Fe2+/Fe3+ bands, grey sigma_s, Henyey-Greenstein g) on a
Lambertian body of albedo A_b, lit diffusely; reflectance by Monte Carlo (implicit capture, Russian roulette).

Inputs and their status:
- sigma_a(lambda): computed in the research notes from Fe2O3 0.91 wt% [M], Fe2+/Fe 0.758 [M], glass density
  2.5 g/cm3 [A], soda-lime-silica band extinctions (Volotinen 2007) [A]; uncertain about 4x in the red.
- ETA 1.50 [A], g 0.7 [A], A_b [A] (body "dark grey to black" [M], no colorimetry): assumptions.

With these sigma_a the best fit gets L* but not the hue (b* about 0 against 7.46): the computed absorption
misses the blue end (no Fe-Ti charge transfer; "below 430 nm unreliable") and is 4x uncertain in the red.
So --invert takes the absorption from a measured reflectance instead: Yu 2021's sherd J2 (fenqing,
digitised from their Fig. 2; its own colour, L*a*b* (52.55, -4.01, 6.04), is within dE 1.6 of the
colorimeter's mean). For each sigma_s it solves sigma_a(lambda) so that the slab reflects J2 (specular
included: a sphere spectrophotometer at 8 deg, assumed), and keeps the sigma_s whose sigma_a in the green
(500-550 nm, where the Fe-band numbers are firmest) agrees with the computed one.
"""

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from camera import LAM, Spectra, lab  # noqa: E402

# sigma_a (natural log, 1/mm), Fe2+/Fe 0.758 (G27g fenqing) [I from M and A]
SIGMA_A = [400, 0.101, 450, 0.028, 500, 0.0125, 550, 0.0165, 600, 0.0527, 650, 0.159, 700, 0.355, 750, 0.615]
TARGET = (51.85, -3.67, 7.46)
ETA = 1.50
G = 0.7
GLAZE_MM = 1.2           # scene.py's uniform glaze; the literature gives 0.5-2 mm [M]
F8 = None                # set in main: Fresnel reflectance at 8 deg (the specular part a d/8 SCI reading adds)


def fresnel(c, eta):
    """Unpolarised reflectance at incidence cosine c (>= 0) into a medium of relative index eta."""
    s2t = (1 - c * c) / (eta * eta)
    tir = s2t >= 1
    ct = np.sqrt(np.maximum(0.0, 1 - s2t))
    rpa = (eta * c - ct) / (eta * c + ct)
    rpe = (c - eta * ct) / (c + eta * ct)
    return np.where(tir, 1.0, 0.5 * (rpa * rpa + rpe * rpe))


def slab(sa, ss, Ab, n, rng):
    """Diffuse reflectance (specular excluded) of the slab under diffuse light."""
    st = sa + ss
    ci = np.sqrt(rng.random(n))                          # cosine-weighted incidence
    w = 1 - fresnel(ci, ETA)
    mu = np.sqrt(1 - (1 - ci * ci) / ETA ** 2)          # refracted, heading down (+z)
    z = np.zeros(n)
    out = 0.0
    alive = np.ones(n, bool)
    while alive.any():
        i = np.flatnonzero(alive)
        s = -np.log(rng.random(len(i))) / st
        zn = z[i] + s * mu[i]
        body = zn >= GLAZE_MM
        top = zn <= 0
        mid = ~(body | top)
        # body: Lambertian, back up
        b = i[body]
        z[b] = GLAZE_MM
        w[b] *= Ab
        mu[b] = -np.sqrt(rng.random(len(b)))
        # top: Fresnel from inside; reflect or leave
        t = i[top]
        z[t] = 0.0
        refl = rng.random(len(t)) < fresnel(np.abs(mu[t]), 1 / ETA)
        mu[t[refl]] = -mu[t[refl]]
        esc = t[~refl]
        out += w[esc].sum()
        alive[esc] = False
        # a collision inside: scatter (Henyey-Greenstein), weight by the albedo
        m = i[mid]
        z[m] = zn[mid]
        w[m] *= ss / st
        u = rng.random(len(m))
        ct = (1 + G * G - ((1 - G * G) / (1 - G + 2 * G * u)) ** 2) / (2 * G)
        st_ = np.sqrt(np.maximum(0, 1 - ct * ct))
        phi = 2 * np.pi * rng.random(len(m))
        mu[m] = mu[m] * ct + np.sqrt(np.maximum(0, 1 - mu[m] ** 2)) * st_ * np.cos(phi)
        # Russian roulette on faint photons
        faint = i[w[i] < 1e-3]
        kill = rng.random(len(faint)) > 0.1
        w[faint[kill]] = 0.0
        alive[faint[kill]] = False
        w[faint[~kill]] /= 0.1
    return out / n


def colour(R, S):
    """L*a*b* (D65, 2 deg) of a reflectance on LAM."""
    yn = S.cmf[1] @ S.d65
    xyz = S.cmf @ (R * S.d65) / yn
    white = S.cmf @ S.d65 / yn
    return lab(xyz, white)


# Yu 2021 Fig. 2, sherd J2 (Guan fenqing), reflectance digitised by eye (+-0.5 % abs) [D]
J2 = [400, 0.141, 450, 0.174, 500, 0.202, 550, 0.213, 600, 0.209, 650, 0.181, 700, 0.150, 750, 0.124]


def invert(a, S):
    rng = np.random.default_rng(7)
    f8 = float(fresnel(np.array([np.cos(np.radians(8))]), ETA)[0])
    lam = np.array(J2[0::2], float)
    target = np.array(J2[1::2]) - f8                      # the diffuse part
    fe = np.interp(lam, SIGMA_A[0::2], SIGMA_A[1::2])
    sa_grid = np.geomspace(1e-4, 3.0, 18)
    rows = []
    for Ab in (0.05, 0.08, 0.12):
        for ss in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0):
            Rg = np.array([slab(sa, ss, Ab, a.photons, rng) for sa in sa_grid])
            if np.any(np.diff(Rg) > 0.002):
                print(f"  warning: R(sigma_a) not monotonic at A_b {Ab}, sigma_s {ss}: {np.round(Rg, 3)}")
            flags = np.where(target > Rg[0], "bright", np.where(target < Rg[-1], "dark", ""))
            # R falls with sigma_a: interpolate log sigma_a against R (reversed to increasing R)
            sa = np.exp(np.interp(target, Rg[::-1], np.log(sa_grid[::-1])))
            green = (lam >= 500) & (lam <= 550)
            err = float(np.sqrt(np.mean(np.log(sa[green] / fe[green]) ** 2)))
            rows.append((err, Ab, ss, sa, flags))
            print(f"A_b {Ab:.2f} sigma_s {ss:4.1f}/mm: sigma_a {np.round(sa, 4)} /mm; green log-misfit {err:.3f}"
                  + (f" flags {list(flags)}" if any(flags) else ""))
    rows.sort(key=lambda r: r[0])
    err, Ab, ss, sa, flags = rows[0]
    print(f"chosen: A_b {Ab}, sigma_s {ss} /mm, g {G}, eta {ETA}, glaze {GLAZE_MM} mm")
    print("sigma_a (1/mm) for pbrt: [ " + " ".join(f"{l:.0f} {v:.4g}" for l, v in zip(lam, sa)) + " ]")
    print("computed Fe bands, for comparison: " + " ".join(f"{l:.0f}:{v:.4g}" for l, v in zip(lam, fe)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photons", type=int, default=100000)
    ap.add_argument("--invert", action="store_true", help="absorption from J2's measured reflectance")
    ap.add_argument("--glaze-mm", type=float, default=GLAZE_MM, help="glaze thickness (an assumption: 0.5-2 mm)")
    a = ap.parse_args()
    globals()["GLAZE_MM"] = a.glaze_mm
    if a.invert:
        invert(a, Spectra("canon_eos_5d_mkiv"))
        return
    rng = np.random.default_rng(6)
    S = Spectra("canon_eos_5d_mkiv")
    f8 = float(fresnel(np.array([np.cos(np.radians(8))]), ETA)[0])
    lam = np.array(SIGMA_A[0::2], float)
    sa_l = np.array(SIGMA_A[1::2], float)
    # reflectance as a function of sigma_a on a grid, then per wavelength by interpolation
    sa_grid = np.geomspace(0.005, 1.0, 14)
    best = []
    print(f"target L*a*b* {TARGET}; glaze {GLAZE_MM} mm, eta {ETA}, g {G}; F(8 deg) = {f8:.4f}")
    for Ab in (0.05, 0.08, 0.12):
        for ss in (1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0):
            Rg = np.array([slab(sa, ss, Ab, a.photons, rng) for sa in sa_grid])
            R_lam = np.interp(np.log(sa_l), np.log(sa_grid), Rg)
            R = np.interp(LAM, lam, R_lam)            # held flat beyond 400 and 750 nm
            for mode, Rm in (("SCE", R), ("SCI", R + f8)):
                L = colour(Rm, S)
                dE = float(np.linalg.norm(L - TARGET))
                best.append((dE, mode, Ab, ss, L, R_lam))
            print(f"A_b {Ab:.2f} sigma_s {ss:5.1f}/mm: R(550) = {np.interp(550, lam, R_lam):.3f}, "
                  f"SCE L*a*b* {np.round(colour(R, S), 2)}, SCI {np.round(colour(R + f8, S), 2)}")
    best.sort(key=lambda t: t[0])
    print("best fits:")
    for dE, mode, Ab, ss, L, R_lam in best[:6]:
        print(f"  dE {dE:5.2f}  {mode}  A_b {Ab:.2f}  sigma_s {ss:5.1f}/mm  L*a*b* {np.round(L, 2)}  "
              f"R(400..750) {np.round(R_lam, 3)}")


if __name__ == "__main__":
    main()
