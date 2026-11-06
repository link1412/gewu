"""Checks of PROSPECT-D as written in materials/yinxing/prospect.py, against closed forms and independent sums.

    python3 -I tests/yinxing/test_prospect.py

1. tav(alpha, n), Stern's closed form, against the Fresnel transmissivity integrated over the cone numerically.
2. No absorption: R + T = 1 for N = 1, 1.5, 2.7, 6.
3. Stokes' pile for integer m against adding m plates one by one (R12 = R1 + T1^2 R2 / (1 - R1 R2), ...).
4. The whole leaf for integer N against the top plate added to N - 1 inner plates by hand.
5. Reciprocity-free sanity: 0 <= R, T and R + T <= 1 for random parameters.
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "materials", "yinxing"))
import prospect as P  # noqa: E402

fails = []


def check(name, ok, detail):
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def fresnel_T(theta, n):
    ct = np.cos(theta)
    st = np.sin(theta) / n
    cti = np.sqrt(np.maximum(1 - st * st, 0))
    rs = (ct - n * cti) / (ct + n * cti)
    rp = (n * ct - cti) / (n * ct + cti)
    return 1 - (rs * rs + rp * rp) / 2


# 1
worst = 0
for n in (1.33, 1.45, 1.5115, 1.7):
    for alpha in (20.0, 40.0, 59.0, 90.0):
        th = np.linspace(0, np.radians(alpha), 200001)
        f = fresnel_T(th, n) * np.sin(2 * th)
        num = np.trapezoid(f, th) / np.sin(np.radians(alpha)) ** 2
        worst = max(worst, abs(num - P.tav(alpha, n)))
check("tav against the integrated Fresnel term", worst < 1e-6, f"worst |diff| {worst:.2e}")

# 2
L, c = P.table()
zero = dict(N=1, Cab=0, Car=0, Anth=0, Cbrown=0, Cw=0, Cm=0)
worst = 0
for N in (1.0, 1.5, 2.7, 6.0):
    _, R, T = P.leaf({**zero, "N": N})
    worst = max(worst, np.abs(R + T - 1).max())
check("lossless leaf: R + T = 1", worst < 1e-9, f"worst {worst:.2e}")

# 3
r = np.array([0.08, 0.2, 0.35]); t = np.array([0.85, 0.6, 0.3])
for m in (1, 2, 5):
    Rs, Ts = P.stokes(r, t, m)
    R1, T1 = r.copy(), t.copy()
    for _ in range(m - 1):
        den = 1 - R1 * r
        R1, T1 = R1 + T1 * T1 * r / den, T1 * t / den
    check(f"Stokes m={m} against adding", np.allclose(Rs, R1, atol=1e-12) and np.allclose(Ts, T1, atol=1e-12),
          f"max |dR| {np.abs(Rs - R1).max():.1e}, |dT| {np.abs(Ts - T1).max():.1e}")

# 4
p = dict(N=3, Cab=5, Car=8, Anth=0.5, Cbrown=0.1, Cw=0.012, Cm=0.008)
_, R, T = P.leaf(p)
k = (p["Cab"] * c["k_cab_cm2_per_ug"] + p["Car"] * c["k_car_cm2_per_ug"] + p["Anth"] * c["k_anth_cm2_per_ug"]
     + p["Cbrown"] * c["k_brown_au"] + p["Cw"] * c["k_w_per_cm"] + p["Cm"] * c["k_m_cm2_per_g"]) / p["N"]
r, t, Ra, Ta = P.one_layer(c["n"], P.plate_tau(k))
# the top plate seen from above is (Ra, Ta) going in; from below (inside) it is (r, t) by its symmetric inner faces
Rin, Tin = r.copy(), t.copy()                  # pile of the other N-1 plates, built by adding
for _ in range(int(p["N"]) - 2):
    den = 1 - Rin * r
    Rin, Tin = Rin + Tin * Tin * r / den, Tin * t / den
den = 1 - Rin * r
Rh, Th = Ra + Ta * Rin * t / den, Ta * Tin / den
check("leaf N=3 against the top plate added to two by hand", np.allclose(R, Rh, atol=1e-12) and np.allclose(T, Th, atol=1e-12),
      f"max |dR| {np.abs(R - Rh).max():.1e}, |dT| {np.abs(T - Th).max():.1e}")

# 5
rng = np.random.default_rng(1)
bad = 0
for _ in range(200):
    q = dict(N=rng.uniform(1, 3.5), Cab=rng.uniform(0, 80), Car=rng.uniform(0, 25), Anth=rng.uniform(0, 5),
             Cbrown=rng.uniform(0, 1.5), Cw=rng.uniform(0.002, 0.04), Cm=rng.uniform(0.002, 0.02))
    _, R, T = P.leaf(q)
    bad += int((R < 0).any() or (T < 0).any() or (R + T > 1 + 1e-12).any())
check("0 <= R, T, R + T <= 1 (200 random leaves)", bad == 0, f"{bad} bad")

print("all ok" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
