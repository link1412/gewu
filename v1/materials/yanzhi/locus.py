"""The card's test without the light: does the photograph's red lie on the 1-D stack's colours (docs/materials/yanzhi.md,
"locus")? For each photo region (card_measure.json, linear BT.709 over the inside's white), the gold's column density c
and an irradiance factor E (the region's light over the white's, which the rig sets and the photo does not give) are
fitted to minimise CIEDE2000 between the photo and E x stack(c) / stack(0) (the diffuse part at normal view under
uniform light, white balanced on the rig's 5500 K, through the camera matrix as card.py develops the render). The
residual is what no c and no light level can fix: the material's own error, to first order (the glaze's neutral
sheen and the view angle left out).

    python3 -I materials/yanzhi/locus.py out/materials/yanzhi/card/runs/c0.56/card_measure.json
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import card  # noqa: E402
import enamel  # noqa: E402
import stack  # noqa: E402
from camera import LAM, blackbody  # noqa: E402


def colours(k, mat, cs):
    rho = np.full(LAM.shape, mat["body"]["albedo"]["value"])
    ne, ng = float(enamel.n_host(589.3, mat)), mat["glaze"]["eta"]["value"]
    W = card._S.sens * blackbody(card.K_LIGHT)
    raw = np.array([W @ stack.stack(c * k, rho, ne, ng)[0] for c in np.r_[0.0, cs]])
    return ((raw / raw[0]) @ card._CAL["C"].T)[1:]


def fit(target_lab, k, mat):
    cs = np.linspace(0.02, 1.5, 149)
    rgb = colours(k, mat, cs)
    best = None
    for c, v in zip(cs, rgb):
        for E in np.exp(np.linspace(np.log(0.1), np.log(3.0), 86)):
            d = card.de2000(target_lab, card.lab_of(E * v))
            if best is None or d < best[0]:
                best = (d, c, E)
    d, c, E = best
    v = np.interp(c, cs, rgb[:, 0]), np.interp(c, cs, rgb[:, 1]), np.interp(c, cs, rgb[:, 2])
    return d, c, E, card.lab_of(E * np.array(v))


def main():
    m = json.load(open(sys.argv[1]))
    mat = card.material()
    g = mat["enamel"]["gold"]
    cases = [("material.json", g["optical_constants"]["value"], g["size_correction_A"]["value"], g["diameter_nm"]["value"])]
    cases += [(f"{s} A {A} d {d}", s, A, d) for s, A, d in (("jc", 0.25, 20.0), ("mcpeak", 0.25, 10.0),
                                                             ("mcpeak", 0.25, 30.0), ("mcpeak", 0.25, 40.0))]
    for name, src, A, d in cases:
        k, _ = enamel.kappa(LAM, enamel.n_host(LAM, mat), [d], A=A, source=src)
        print(f"{name}: (peak {enamel.peak(LAM, k):.0f} nm)")
        for reg, rgb in m["photo"]["rgb"].items():
            t = card.lab_of(np.array(rgb))
            dE, c, E, l = fit(t, k, mat)
            ht, hl = (np.degrees(np.arctan2(x[2], x[1])) for x in (t, l))
            print(f"  {reg:13s} photo {t[0]:5.1f} {t[1]:5.1f} {t[2]:5.1f} h {ht:5.1f} | best c {c:.2f} E {E:.2f}: "
                  f"{l[0]:5.1f} {l[1]:5.1f} {l[2]:5.1f} h {hl:5.1f} | dE00 {dE:.2f}")


if __name__ == "__main__":
    main()
