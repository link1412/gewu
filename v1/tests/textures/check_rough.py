"""Test b, the check: each half of the step-roughness render against a render with that uniform roughness
(Cycles against Cycles, pbrt against pbrt) and pbrt against Cycles.

    python3 -I tests/textures/check_rough.py

Column profiles (mean of rows 120-420, the highlight depends on x only), the 3 mm around the step left out.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gen_rough as G  # noqa: E402

D = os.path.join(C.OUT, "rough")
ROWS = slice(120, 420)
PX = 36.0 / G.RES[0]                      # mm per pixel (36 mm across)


def prof(r, v):
    return C.read_image(os.path.join(D, f"{r}_{v}.exr"))[ROWS].mean(2).mean(0)


def band(side):
    x = (np.arange(G.RES[0]) + 0.5 - G.RES[0] / 2) * PX                  # image x; world x is its mirror image
    wx = -x
    return (wx < -3) & (wx > -17) if side == "left" else (wx > 3) & (wx < 17)


def stat(a, b, m, label):
    # only columns where the highlight is on (the lobe's tails are noise): above 10% of the uniform profile's peak
    on = m & (b > 0.1 * b[m].max())
    r = a[on] / b[on]
    print(f"  {label}: {on.sum()} columns; mean ratio {r.mean():.4f}, rms deviation of the ratio {r.std():.4f}; "
          f"sum ratio {a[on].sum() / b[on].sum():.4f}")
    return abs(a[on].sum() / b[on].sum() - 1) < 0.03


def main():
    P = {(r, v): prof(r, v) for r in ("pbrt", "cyc") for v in ("step", "uni1", "uni2")}
    ok = True
    for r, name in (("cyc", "Cycles"), ("pbrt", "pbrt")):
        for side, uni, al in (("left", "uni1", G.A1), ("right", "uni2", G.A2)):
            ok &= stat(P[(r, "step")], P[(r, uni)], band(side), f"{name}: step map vs uniform alpha {al}, {side} half")
    for side, uni in (("left", "uni1"), ("right", "uni2")):
        print("  power of the test:", end="")
        other = "uni2" if uni == "uni1" else "uni1"
        stat(P[("cyc", other)], P[("cyc", uni)], band(side), f"Cycles: the WRONG uniform alpha on the {side} half")
    for v in ("uni1", "uni2", "step"):
        for side in ("left", "right"):
            ok &= stat(P[("pbrt", v)], P[("cyc", v)], band(side), f"pbrt vs Cycles, {v}, {side} half")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 4))
    for (r, v), p in P.items():
        ax.plot(p, label=f"{r} {v}", lw=0.8, ls="-" if r == "cyc" else "--")
    ax.legend(ncol=3)
    fig.savefig(os.path.join(D, "profiles.png"), dpi=80)
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
