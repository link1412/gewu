"""PROSPECT-D, the leaf as a pile of N absorbing plates: hemispherical reflectance R(lambda) and transmittance T(lambda).

    python3 -I materials/yinxing/prospect.py N CAB CAR [ANTH CBROWN CW CM]     # print R, T at a few wavelengths

The model (written here from the papers, checked against closed forms in tests/yinxing/test_prospect.py):
- Jacquemoud & Baret 1990, 'PROSPECT: a model of leaf optical properties spectra', Remote Sens. Environ. 34:75-91:
  a compact plate (Allen et al. 1969) for the first layer, Stokes' pile of plates (Stokes 1862) for the other N-1,
  N real;
- Feret, Gitelson, Noble & Jacquemoud 2017 (PROSPECT-D, RSE 193:204): the absorption is the sum of the pigments'
  specific absorptions times their contents, k(lambda) = (Cab kab + Car kcar + Anth kanth + Cbrown kbrown + Cw kw +
  Cm km) / N, and the plate's transmissivity for isotropic light is tau = (1 - k) e^-k + k^2 E1(k);
- the interface's transmissivity for light within a cone of half-angle alpha, tav(alpha, n), is Stern's closed form
  (Stern 1964, Appl. Opt. 3:111; Allen 1973, JOSA 63:664). The top surface sees alpha = 40 degrees (the model's
  default: light from a cone, as an integrating sphere's sample port), the inner interfaces isotropic light (90).
The data (n, the k's) are PROSPECT-D's own table, data/prospect_d_full.csv. R includes the top surface's reflection
(1 - tav(40, n), about 4-5 %), which the model treats as part of a hemispherical R; a renderer that adds a separate
specular coat must take it out (top_surface_reflection below).
"""
import os
import sys

import numpy as np
from scipy.special import exp1

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ("n", "k_cab_cm2_per_ug", "k_car_cm2_per_ug", "k_anth_cm2_per_ug", "k_brown_au", "k_w_per_cm", "k_m_cm2_per_g")
PARAMS = ("N", "Cab", "Car", "Anth", "Cbrown", "Cw", "Cm")      # -, ug/cm2, ug/cm2, ug/cm2, au, cm, g/cm2


def table():
    """PROSPECT-D's table on its own 1 nm grid, 400-1000 nm: (lambda, {column: array})."""
    rows = np.array([ln.split(",") for ln in open(os.path.join(HERE, "data", "prospect_d_full.csv")) if ln[0].isdigit()],
                    float)
    return rows[:, 0], {c: rows[:, i + 1] for i, c in enumerate(COLS)}


def tav(alpha_deg, n):
    """Mean transmissivity of a dielectric interface (air -> n) for isotropic light within a cone of half-angle alpha,
    Stern's closed form as Allen 1973 writes it (unpolarised: the mean of s and p). alpha = 90: the whole hemisphere."""
    n = np.asarray(n, float)
    n2 = n * n
    np_, nm = n2 + 1, n2 - 1
    a = (n + 1) ** 2 / 2
    k = -(n2 - 1) ** 2 / 4
    sa = np.sin(np.radians(alpha_deg))
    b1 = np.sqrt((sa * sa - np_ / 2) ** 2 + k) if alpha_deg != 90 else 0.0
    b2 = sa * sa - np_ / 2
    b = b1 - b2
    ts = (k ** 2 / (6 * b ** 3) + k / b - b / 2) - (k ** 2 / (6 * a ** 3) + k / a - a / 2)
    tp1 = -2 * n2 * (b - a) / np_ ** 2
    tp2 = -2 * n2 * np_ * np.log(b / a) / nm ** 2
    tp3 = n2 * (1 / b - 1 / a) / 2
    tp4 = 16 * n2 ** 2 * (n2 ** 2 + 1) * np.log((2 * np_ * b - nm ** 2) / (2 * np_ * a - nm ** 2)) / (np_ ** 3 * nm ** 2)
    tp5 = 16 * n2 ** 3 * (1 / (2 * np_ * b - nm ** 2) - 1 / (2 * np_ * a - nm ** 2)) / np_ ** 3
    return (ts + tp1 + tp2 + tp3 + tp4 + tp5) / (2 * sa ** 2)


def plate_tau(k):
    """Transmissivity of a plate of absorption k (optical depth at normal incidence) for isotropic light:
    (1 - k) e^-k + k^2 E1(k); 1 at k = 0."""
    k = np.asarray(k, float)
    out = np.ones_like(k)
    j = k > 0
    out[j] = (1 - k[j]) * np.exp(-k[j]) + k[j] ** 2 * exp1(k[j])
    return out


def one_layer(n, tau, alpha=40.0):
    """The compact plate (Allen et al. 1969): (r, t) for isotropic light on its inner faces, (Ra, Ta) for light from
    the cone alpha on its top face."""
    talf = tav(alpha, n)
    ralf = 1 - talf
    t12 = tav(90.0, n)
    r12 = 1 - t12
    t21 = t12 / n ** 2
    r21 = 1 - t21
    den = 1 - r21 ** 2 * tau ** 2
    Ta = talf * tau * t21 / den
    Ra = ralf + r21 * tau * Ta
    t = t12 * tau * t21 / den
    r = r12 + r21 * tau * t
    return r, t, Ra, Ta


def stokes(r, t, m):
    """Reflectance and transmittance of a pile of m (real, >= 0) identical plates (r, t), Stokes 1862 in the form
    PROSPECT uses; the lossless case (r + t = 1) by its limit."""
    r, t = np.broadcast_arrays(np.asarray(r, float), np.asarray(t, float))
    R, T = np.empty_like(r), np.empty_like(r)
    loss = r + t < 1 - 1e-12
    rr, tt = r[loss], t[loss]
    D = np.sqrt((1 + rr + tt) * (1 + rr - tt) * (1 - rr + tt) * (1 - rr - tt))
    a = (1 + rr ** 2 - tt ** 2 + D) / (2 * rr)
    b = (1 - rr ** 2 + tt ** 2 + D) / (2 * tt)
    bm = b ** m
    den = a * a * bm * bm - 1
    R[loss] = a * (bm * bm - 1) / den
    T[loss] = bm * (a * a - 1) / den
    tl = t[~loss]
    T[~loss] = tl / (tl + (1 - tl) * m)
    R[~loss] = 1 - T[~loss]
    return R, T


def leaf(p, lam=None, alpha=40.0):
    """R, T of a leaf with parameters p = {N, Cab, Car, Anth, Cbrown, Cw, Cm} (all required: no defaults) on PROSPECT's
    grid, or interpolated onto `lam` (nm; outside 400-1000 nm it is an error)."""
    missing = [k for k in PARAMS if k not in p]
    if missing:
        raise SystemExit(f"PROSPECT: no value for {missing}")
    L, c = table()
    N = float(p["N"])
    if N < 1:
        raise SystemExit(f"PROSPECT: N = {N} < 1")
    k = (p["Cab"] * c["k_cab_cm2_per_ug"] + p["Car"] * c["k_car_cm2_per_ug"] + p["Anth"] * c["k_anth_cm2_per_ug"]
         + p["Cbrown"] * c["k_brown_au"] + p["Cw"] * c["k_w_per_cm"] + p["Cm"] * c["k_m_cm2_per_g"]) / N
    r, t, Ra, Ta = one_layer(c["n"], plate_tau(k), alpha)
    Rs, Ts = stokes(r, t, N - 1)
    den = 1 - Rs * r
    T = Ta * Ts / den
    R = Ra + Ta * Rs * t / den
    if lam is None:
        return L, R, T
    lam = np.asarray(lam, float)
    if lam.min() < L[0] or lam.max() > L[-1]:
        raise SystemExit(f"PROSPECT covers {L[0]:.0f}-{L[-1]:.0f} nm, asked {lam.min():.0f}-{lam.max():.0f}")
    return lam, np.interp(lam, L, R), np.interp(lam, L, T)


def top_surface_reflection(alpha=40.0):
    """The part of R that is the top interface's own reflection, 1 - tav(alpha, n(lambda)), on PROSPECT's grid."""
    L, c = table()
    return L, 1 - tav(alpha, c["n"])


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    v = [float(x) for x in sys.argv[1:]]
    p = dict(zip(PARAMS, v + [0.0] * (len(PARAMS) - len(v))))
    L, R, T = leaf(p)
    for lam in (450, 500, 550, 600, 650, 680, 750, 850):
        i = int(lam - L[0])
        print(f"{lam} nm  R {R[i]:.4f}  T {T[i]:.4f}  A {1 - R[i] - T[i]:.4f}")


if __name__ == "__main__":
    main()
