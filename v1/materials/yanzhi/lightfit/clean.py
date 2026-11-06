"""胭脂红 card, round 2: the clean fit (docs/materials/yanzhi.md, "fitting the light").

The probe grids (probe.py) put dozens of lamp panels round the bowl at once; in a group's own image the other panels
are dark but still there, and they hide the sweep from the glossy wall, so the grid under-predicts the wall's sheen
(seen when the fitted rig was rendered alone: front G 0.055 against the grid's 0.01; skill-notes). This fit uses
only clean renders of the chosen rig (materials/yanzhi/recipes/rig_met_fit.json): four of them, grey_18 and
white_90 sweeps at c 0.45 and 0.56, each with light groups main / rear / top. Then, exactly: the groups' strengths
(light adds); approximately: the sweep's reflectance rho, linear between grey and white [A: one bounce off the sweep
dominates], and c, log-linear between 0.45 and 0.56 [A]. Scored on the photo's outer wall (R and G channels over the
white, 18 points each), the backdrop (3 points) and the floor just in front of the foot (3 points), all as logs.

    python3 -I materials/yanzhi/lightfit/clean.py [--write OUTDIR]   # --write: the best mix as x.pfm in OUTDIR
"""
import argparse
import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import card  # noqa: E402
import fit  # noqa: E402
from fit import LUM  # noqa: E402
from camera import read_raw  # noqa: E402

D = os.path.join(ROOT, "out/materials/yanzhi/lightfit")
RUNS = {("grey", 0.45): "yanzhi-card-r2-c045-grey", ("white", 0.45): "yanzhi-card-r2-c045",
        ("grey", 0.56): "yanzhi-card-r2-c056-grey", ("white", 0.56): "yanzhi-card-r2-c056"}
FLOOR = (1.06, 1.1, 1.2)


def floor(lin, box, info):
    w = card.median_box(lin, box["white"])
    H, cx = info["red_bot"] - info["top"], int(info["cx"])
    return np.array([card.median_box(lin, (int(info["top"] + f * H), cx, 4)) / w for f in FLOOR])


def features(lin, box, info, ref):
    """absolute (not over the white) wall rgb (18), white rgb, backdrop rgb (3), floor rgb (3)"""
    w = card.median_box(lin, box["white"])
    keys = [(fz, float(u)) for fz in fit.FZ for u in fit.US]
    wl = fit.wall_abs(lin, box, info, ref)
    return (np.array([wl[k] for k in keys]), w, fit.backdrop(lin, box, info) * w, floor(lin, box, info) * w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write")
    a = ap.parse_args()
    lin, pbox, pinfo, pwl, pbl = fit.photo_features()
    keys = [(fz, float(u)) for fz in fit.FZ for u in fit.US]
    P = {"R": np.log([pwl[k][0] for k in keys]), "G": np.log([pwl[k][1] for k in keys]),
         "back": np.log(fit.backdrop(lin, pbox, pinfo) @ LUM), "floor": np.log(floor(lin, pbox, pinfo) @ LUM)}
    raws, F = {}, {}
    ref = None
    for k, name in RUNS.items():
        G = {g: read_raw(os.path.join(D, name, f"x.{g}.exr")) for g in ("main", "rear", "top")}
        raws[k] = G
        tot = fit.develop(sum(G.values()))
        if ref is None:
            box, info = card.regions(tot, name)
            ref = tot
        F[k] = {g: features(fit.develop(G[g]), box, info, ref) for g in G}
    rhos = np.linspace(0.18, 0.9, 25)
    cs = np.linspace(0.3, 0.9, 25)
    rows = []
    for wr, wt in itertools.product([0, 0.25, 0.5, 1, 1.5, 2, 3], [0, 0.25, 0.5, 1, 2, 3]):
        wts = {"main": 1.0, "rear": wr, "top": wt}
        S = {k: [sum(wts[g] * F[k][g][i] for g in wts) for i in range(4)] for k in F}
        for rho in rhos:
            t = (rho - 0.18) / 0.72
            for c in cs:
                u = (c - 0.45) / 0.11
                vals = []
                for i in range(4):
                    gv = [(1 - t) * S[("grey", cc)][i] + t * S[("white", cc)][i] for cc in (0.45, 0.56)]
                    lg = np.log(np.maximum(gv[0], 1e-9)) + u * (np.log(np.maximum(gv[1], 1e-9)) - np.log(np.maximum(gv[0], 1e-9)))
                    vals.append(np.exp(lg))
                wall, white, back, fl = vals
                x = wall / white
                eR = np.sqrt(np.mean((np.log(x[:, 0]) - P["R"]) ** 2))
                eG = np.sqrt(np.mean((np.log(np.maximum(x[:, 1], 1e-5)) - P["G"]) ** 2))
                eb = np.sqrt(np.mean((np.log(back @ LUM / (white @ LUM)) - P["back"]) ** 2))
                ef = np.sqrt(np.mean((np.log(fl @ LUM / (white @ LUM)) - P["floor"]) ** 2))
                rows.append((float(eR + eG + 0.5 * eb + 0.5 * ef), float(eR), float(eG), float(eb), float(ef),
                             wr, wt, float(rho), float(c)))
    rows.sort(key=lambda r: r[0])
    for r in rows[:12]:
        print("score {:.3f} = R {:.3f} + G {:.3f} + back/2 {:.3f} + floor/2 {:.3f} | rear x {} top x {} | rho {:.2f} c {:.3f}".format(*r))
    best = rows[0]
    json.dump({"best": {"rear": best[5], "top": best[6], "rho": best[7], "c": best[8], "score": best[0],
                        "rms_log": {"R": best[1], "G": best[2], "backdrop": best[3], "floor": best[4]}},
               "top": [list(r) for r in rows[:30]]}, open(os.path.join(D, "clean_fit.json"), "w"), indent=1)
    if a.write:
        # the best mix as an image: groups weighted, sweep interpolated, c the nearer render's (no c interpolation of
        # pixels: it is written at the c of a real render, given by --write's dir name)
        os.makedirs(a.write, exist_ok=True)
        wts = {"main": 1.0, "rear": best[5], "top": best[6]}
        t = (best[7] - 0.18) / 0.72
        for cc in (0.45, 0.56):
            img = sum(wts[g] * ((1 - t) * raws[("grey", cc)][g] + t * raws[("white", cc)][g]) for g in wts)
            from build import write_pfm
            write_pfm(os.path.join(a.write, f"mix_c{cc:.2f}.pfm"), img)
        print("->", a.write)


if __name__ == "__main__":
    main()
