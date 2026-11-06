"""The cobalt's spectrum against measured blue: materials/qinghua's model R(lambda) fitted to Hsieh et al. 2023
Fig. 4 (FORS of mid-Ming Jingdezhen blue decoration, three dishes, materials/qinghua/data/hsieh2023_fig4.csv).

Model: R(lambda) = a + b * S(lambda; c), S the 1-D stack's diffuse reflectance (optics.stack, diffuse light, normal
view; glaze n and body albedo from material.json's kangxi set), a a flat offset (the glaze's specular part and
whatever the probe collects of it), b a scale (the probe's geometry against its white reference), c the cobalt.
Fitted by least squares on the traced points 420-760 nm. Also the band minima (local minima of R) against Hsieh's
Table 2 (glaze: 517-522, 581-586, 655-679 nm) and against the model's own.

    python3 -I tests/qinghua/check_spectrum.py [--plot out/qinghua/spectrum.png]
"""
import argparse
import os
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qh  # noqa: E402

sys.path.insert(0, os.path.join(qh.ROOT, "materials/qinghua"))
import optics  # noqa: E402
from camera import LAM  # noqa: E402

NAMES = ["SC-1269", "SC-14679", "SC-14878"]


def minima(lam, r, lo, hi, smooth=9):
    m = (lam >= lo) & (lam <= hi)
    rs = np.convolve(r, np.ones(smooth) / smooth, mode="same")
    i = np.argmin(np.where(m, rs, np.inf))
    return float(lam[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    a = ap.parse_args()
    d = np.loadtxt(os.path.join(qh.ROOT, "materials/qinghua/data/hsieh2023_fig4.csv"), delimiter=",", skiprows=2)
    lam = d[:, 0]
    k = optics.cobalt_kappa()
    g = optics.material()["sets"]["kangxi"]
    n, rho = g["glaze"]["eta"]["value"], g["body"]["albedo"]["value"]
    fits = []
    for j, name in enumerate(NAMES):
        r, traced = d[:, 1 + j], d[:, 4 + j] > 0
        m = traced & (lam >= 420) & (lam <= 760)

        def model(p):
            S = optics.stack(p[2] * k, np.full(LAM.shape, rho), n)[0]
            return p[0] + p[1] * np.interp(lam, LAM, S)

        best = None
        for c0 in (0.3, 1.0, 3.0):
            f = least_squares(lambda p: (model(p) - r)[m], [0.05, 0.3, c0], bounds=([0, 0, 0], [1, 5, 20]))
            if best is None or f.cost < best.cost:
                best = f
        p = best.x
        res = (model(p) - r)[m]
        S = model(p)
        mins_m = [minima(lam, r, 500, 545), minima(lam, r, 560, 610), minima(lam, r, 630, 700)]
        mins_f = [minima(lam, S, 500, 545), minima(lam, S, 560, 610), minima(lam, S, 630, 700)]
        print(f"{name}: a {p[0]:.3f} b {p[1]:.3f} c {p[2]:.2f} g/m^2; rms residual {np.sqrt(np.mean(res ** 2)):.4f} "
              f"(signal range {np.ptp(r[m]):.3f}); traced {m.sum()} points")
        print(f"   minima measured {mins_m} nm, model {mins_f} nm")
        for lo, hi in ((420, 480), (480, 540), (540, 600), (600, 660), (660, 700), (700, 760)):
            mm = m & (lam >= lo) & (lam < hi)
            if mm.any():
                print(f"   {lo}-{hi} nm: measured {r[mm].mean():.3f} model {S[mm].mean():.3f} "
                      f"(model - measured {S[mm].mean() - r[mm].mean():+.3f})")
        fits.append((name, r, traced, S))
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 5))
        for name, r, traced, S in fits:
            l, = ax.plot(lam[traced], r[traced], ".", ms=2, label=f"{name} (Hsieh 2023 Fig. 4, traced)")
            ax.plot(lam, S, "-", color=l.get_color(), lw=1, label=f"{name} model fit")
        for x in (520, 583, 672):
            ax.axvline(x, color="grey", lw=0.5, ls=":")
        ax.set_xlim(400, 800)
        ax.set_xlabel("wavelength (nm); dotted: Hsieh's mean band minima in glaze")
        ax.set_ylabel("reflectance")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(a.plot, dpi=120)
        print("plot ->", a.plot)


if __name__ == "__main__":
    main()
