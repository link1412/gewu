"""Checks of the nacre multilayer (shots/19-luodian/nacre.py) against closed forms.

    python3 -I tests/nacre/test_nacre.py

1. One interface: the Fresnel formulas, s and p, several angles.
2. Uniaxial interface (optic axis normal): r_p vanishes at sin^2 = n_e^2 (n_o^2 - 1) / (n_o^2 n_e^2 - 1).
3. One film on a substrate: the Airy sum (r01 + r12 e^{-2i d}) / (1 + r01 r12 e^{-2i d}), oblique, s and p
   (the characteristic matrix's time convention, exp(i(wt - kz)), as in Macleod).
4. A quarter-wave stack (HL)^N at its design wavelength: R = ((n0 - Y) / (n0 + Y))^2, Y = (nH/nL)^{2N} ns.
5. No absorption: R + T = 1 for a random uniaxial stack, oblique, s and p.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "shots", "19-luodian"))
import nacre as N  # noqa: E402

fails = []


def check(name, ok, detail):
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def iso(n):
    return (n, n)


lam = np.array([450.0, 550.0, 650.0])

# 1. Fresnel
n1, n2 = 1.0, 1.68
th = np.radians([0.0, 20.0, 45.0, 70.0, 85.0])
b = n1 * np.sin(th)
ct = np.sqrt(1 - (b / n2) ** 2)
ci = np.cos(th)
rs = (n1 * ci - n2 * ct) / (n1 * ci + n2 * ct)
rp = (n2 * ci - n1 * ct) / (n2 * ci + n1 * ct)
err = max(np.abs(N.fresnel_R(550.0, b, iso(n1), iso(n2), "s") - rs ** 2).max(),
          np.abs(N.fresnel_R(550.0, b, iso(n1), iso(n2), "p") - rp ** 2).max())
check("fresnel", err < 1e-12, f"max |dR| {err:.1e}")

# 2. uniaxial Brewster
no, ne = 1.6825, 1.530
sB = np.sqrt(ne ** 2 * (no ** 2 - 1) / (no ** 2 * ne ** 2 - 1))
Rp = float(N.fresnel_R(550.0, sB, iso(1.0), (no, ne), "p"))
Rp_iso = float(N.fresnel_R(550.0, sB, iso(1.0), iso(no), "p"))
check("uniaxial Brewster", Rp < 1e-20 and Rp_iso > 1e-4,
      f"R_p {Rp:.1e} at {np.degrees(np.arcsin(sB)):.2f} deg (isotropic n_o there: {Rp_iso:.1e})")

# 3. Airy sum, one film
nf, ns, t = 1.45, 1.68, 130.0
for pol in ("s", "p"):
    worst = 0.0
    for thd in (0.0, 30.0, 60.0):
        bb = np.sin(np.radians(thd))
        q0, Y0 = N.qy(iso(1.0), bb, pol)
        q1, Y1 = N.qy(iso(nf), bb, pol)
        q2, Y2 = N.qy(iso(ns), bb, pol)
        r01 = (Y0 - Y1) / (Y0 + Y1)
        r12 = (Y1 - Y2) / (Y1 + Y2)
        e = np.exp(-2j * (2 * np.pi / lam) * q1 * t)
        r = (r01 + r12 * e) / (1 + r01 * r12 * e)
        rr = N.stack_r(lam, bb, iso(1.0), [(iso(nf), t)], iso(ns), pol)
        worst = max(worst, float(np.abs(rr - r).max()))
    check(f"Airy film ({pol})", worst < 1e-12, f"max |dr| {worst:.1e}")

# 4. quarter-wave stack
nH, nL, n0, nsub, Npairs, lam0 = 1.68, 1.45, 1.0, 1.52, 8, 550.0
layers = []
for _ in range(Npairs):
    layers += [(iso(nH), lam0 / (4 * nH)), (iso(nL), lam0 / (4 * nL))]
Y = (nH / nL) ** (2 * Npairs) * nsub
R_th = ((n0 - Y) / (n0 + Y)) ** 2
R = float(np.abs(N.stack_r(lam0, 0.0, iso(n0), layers, iso(nsub), "s")) ** 2)
check("quarter-wave stack", abs(R - R_th) < 1e-12, f"R {R:.10f}, closed form {R_th:.10f}")

# 5. energy, random uniaxial stack
rng = np.random.default_rng(1)
layers = []
for _ in range(60):
    layers += [((no, ne), rng.uniform(300, 500)), (iso(1.45), rng.uniform(15, 40))]
lam_f = np.linspace(400, 700, 301)
worst = 0.0
for pol in ("s", "p"):
    for thd in (0.0, 40.0, 80.0):
        bb = np.sin(np.radians(thd))
        R = np.abs(N.stack_r(lam_f, bb, iso(1.0), layers, iso(1.52), pol)) ** 2
        T = N.stack_T(lam_f, bb, iso(1.0), layers, iso(1.52), pol)
        worst = max(worst, float(np.abs(R + T - 1).max()))
check("R + T = 1", worst < 1e-10, f"max |R + T - 1| {worst:.1e} (120 layers, s and p, 0-80 deg)")

if fails:
    raise SystemExit(f"{len(fails)} failed: {fails}")
print("all ok")
