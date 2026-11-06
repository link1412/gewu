"""胭脂红 card, round 2: fit the light on two channels (docs/materials/yanzhi.md, "fitting the light").

On the red wall the gold absorbs almost all the green, so the G channel over the white is the glaze's neutral sheen
(what the surface mirrors: the backdrop, the floor) and R is mostly the light through the enamel (diffuse; it scales
with the gold's c, G nearly not: fit5 c 0.5 -> 0.8 moves R by x0.75, G by x0.97). So
    G profile -> the surround's brightness (the backdrop's reflectance rho);
    R profile -> where the lamps are (and one scale factor s for the diffuse part, i.e. c);
    the inside's reflections -> the main pair's place (fit.py's blobs).
The backdrop's reflectance is interpolated linearly between the grey (0.18) and white (0.90) probes, which differ
only in it [A: one bounce off the backdrop dominates]. Candidates: main pair g1 (from the probe grid) + optional
second pair g2 x w2 + top x wt, rho, and s (fitted in closed form: the mean log ratio of R).

    python3 -I materials/yanzhi/lightfit/rgfit.py GREY_PROBE WHITE_PROBE
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fit  # noqa: E402
from fit import LUM  # noqa: E402


def main():
    dg, dw = sys.argv[1], sys.argv[2]
    lin, pbox, pinfo, pwl, pbl = fit.photo_features()
    keys = [(fz, float(u)) for fz in fit.FZ for u in fit.US]
    pR = np.log([pwl[k][0] for k in keys])
    pG = np.log([pwl[k][1] for k in keys])
    pb = np.log(fit.backdrop(lin, pbox, pinfo) @ LUM)
    pblobs = sorted(pbl[:2], key=lambda b: b[0])
    Dg = fit.probe_data(dg)
    Dw = fit.probe_data(dw, (Dg["box"], Dg["info"], Dg["ref"]))
    gs = Dg["groups"]
    pairs = [g for g in gs if g != "top"]

    def arr(D, g):
        W = D["white"][g]
        return (np.array([D["wall"][g][k] for k in keys]), W, D["back"][g])

    A = {g: (arr(Dg, g), arr(Dw, g)) for g in gs}
    miss = {}
    for g in pairs:
        b = Dg["blobs"][g]
        miss[g] = (float(np.sqrt(np.mean([(p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for p, q in zip(pblobs, b)])))
                   if len(b) == 2 and b[0][0] < 0 < b[1][0] else 1.0)
    rhos = np.linspace(0.18, 0.90, 13)
    rows = []
    for g1 in pairs:
        if miss[g1] > 0.15:
            continue
        for g2 in [None] + pairs:
            if g2 == g1:
                continue
            for w2 in ([0] if g2 is None else [0.25, 0.5, 1.0, 2.0]):
                for wt in (0, 0.5, 1.0, 2.0):
                    parts = [(g1, 1.0)] + ([(g2, w2)] if g2 else []) + ([("top", wt)] if wt else [])
                    for rho in rhos:
                        t = (rho - 0.18) / 0.72
                        wall = sum(w * ((1 - t) * A[g][0][0] + t * A[g][1][0]) for g, w in parts)
                        W = sum(w * ((1 - t) * A[g][0][1] + t * A[g][1][1]) for g, w in parts)
                        bk = sum(w * ((1 - t) * A[g][0][2] + t * A[g][1][2]) for g, w in parts)
                        x = wall / W
                        G = np.log(np.maximum(x[:, 1], 1e-5))
                        diff = np.maximum(x[:, 0] - x[:, 1], 1e-5)          # R minus the sheen
                        pdiff = np.exp(pR) - np.exp(pG)
                        ls = float(np.mean(np.log(pdiff) - np.log(diff)))    # the diffuse scale s (c's job)
                        R = np.log(diff * np.exp(ls) + x[:, 1])
                        eR = float(np.sqrt(np.mean((R - pR) ** 2)))
                        eG = float(np.sqrt(np.mean((G - pG) ** 2)))
                        eb = float(np.sqrt(np.mean((np.log(bk @ LUM / (W @ LUM)) - pb) ** 2)))
                        rows.append((eR + eG + 0.5 * eb + miss[g1], eR, eG, eb, miss[g1], g1, g2, w2, wt,
                                     float(rho), float(np.exp(ls))))
    rows.sort(key=lambda r: r[0])
    for r in rows[:15]:
        print("score {:.3f} = R {:.3f} + G {:.3f} + back/2 {:.3f} + blob {:.3f} | {} + {} x {} + top x {} | rho {:.2f} | "
              "diffuse x {:.2f}".format(*r))
    json.dump([list(r) for r in rows[:50]], open(os.path.join(dg, "rgfit.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
