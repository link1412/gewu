"""Check the gold model (enamel.py) against a measured gold-ruby glass: Takebe, Okamoto & Mori 2021, Fig. 6
(digitize.py -> data/takebe2021_fig6.csv; 1 mm soda-lime glass, 0.014 mass% Au2O3, struck at 580-680 C).

For each panel's median curve, and each gold table and surface-damping constant A, the model
    A_meas(lambda) = a + b kappa(lambda; d)
is fitted by least squares over 402-698 nm: a a flat baseline (the two surfaces' reflection, about 0.036, plus the
glass's own absorption) [A: flat], b the gold's amount, d one sphere diameter (a grid). The host is a soda-lime glass,
n_D 1.52, V_d 59 [A: a typical float glass; the paper gives neither]. Reported: the best d, the rms residual relative
to the peak, the fitted peak against the measured one. No number here is used by the card; it decides which gold
table and which A the material uses (docs/materials/yanzhi.md).

    python3 -I materials/yanzhi/validate.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import enamel  # noqa: E402

SODA_LIME = {"enamel": {"glass": {"n_D": {"value": 1.52}, "abbe_number": {"value": 59.0}}}}
SIZES = [3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0]


def fit(lam, y, k):
    M = np.column_stack([np.ones_like(lam), k])
    c, *_ = np.linalg.lstsq(M, y, rcond=None)
    r = y - M @ c
    return c, float(np.sqrt(np.mean(r * r)))


def main():
    d = np.loadtxt(os.path.join(HERE, "data", "takebe2021_fig6.csv"), delimiter=",", comments="#")
    lam = d[:, 0]
    nh = enamel.n_host(lam, SODA_LIME)
    table = {}
    for src in ("jc", "mcpeak"):
        for A in (0.0, 0.25, 0.5, 1.0):
            table[(src, A)] = {s: enamel.kappa(lam, nh, [s], A=A, source=src)[0] for s in SIZES}
    print("model peak (nm) of kappa in soda-lime glass, by diameter:")
    for (src, A), ks in table.items():
        print(f"  {src:6s} A {A:4.2f}: " + "  ".join(f"{s:g}:{enamel.peak(lam, k):.0f}" for s, k in ks.items()))
    print("\nper panel: measured peak; per (table, A): best d, rms/peak, fitted baseline a, model peak")
    for j, p in enumerate("abcd"):
        y = d[:, 1 + 3 * j]
        pk = enamel.peak(lam, y)
        base = y[lam >= 680].mean()
        print(f"panel {p}: peak {pk:.1f} nm, A(peak) {y.max():.3f}; mean 680-698 nm {base:.3f}; "
              f"(A450-base)/(Apk-base) {(np.interp(450, lam, y) - base) / (y.max() - base):.3f}, "
              f"(A600-base)/(Apk-base) {(np.interp(600, lam, y) - base) / (y.max() - base):.3f}")
        for (src, A), ks in table.items():
            best = min(((fit(lam, y, k), s) for s, k in ks.items()), key=lambda t: t[0][1])
            (c, rms), s = best
            print(f"    {src:6s} A {A:4.2f}: d {s:4g} nm, rms/peak {rms / y.max():.4f}, a {c[0]:+.3f}, "
                  f"model peak {enamel.peak(lam, ks[s]):.1f}")


if __name__ == "__main__":
    main()
