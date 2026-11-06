"""胭脂红 card, S8 r2: the group strengths of rig_met_fit3.json (smaller main pair, a higher pair, any other groups), fitted on one Cycles render with a light group per pair (light adds: the mix is exact), scored as
clean.py scores (the photo's outer wall R and G over the white, 18 points each; backdrop and floor, all as logs).
The sweep is fixed at the reflectance the render has (direct.py's patch). Also prints the chosen mix's reflection
blobs on the inside (fit.blobs), which the photo pins.

    python3 -I materials/yanzhi/lightfit/fit3.py out/s8/yanzhi/r2/render/D-groups-c050
"""
import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import card  # noqa: E402
import clean  # noqa: E402
import fit  # noqa: E402
from fit import LUM  # noqa: E402
from camera import read_raw  # noqa: E402


def main(d):
    q = json.load(open(os.path.join(d, "queued.json")))
    G = {g: read_raw(os.path.join(d, f"x.{g}.exr")) for g in q["groups"]}
    lin, pbox, pinfo, pwl, pbl = fit.photo_features()
    keys = [(fz, float(u)) for fz in fit.FZ for u in fit.US]
    P = {"R": np.log([pwl[k][0] for k in keys]), "G": np.log([pwl[k][1] for k in keys]),
         "back": np.log(fit.backdrop(lin, pbox, pinfo) @ LUM), "floor": np.log(clean.floor(lin, pbox, pinfo) @ LUM)}
    tot = fit.develop(sum(G.values()))
    box, info = card.regions(tot, "all")
    F = {g: clean.features(fit.develop(G[g]), box, info, tot) for g in G}
    grid = [0, 0.125, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6]
    others = [g for g in G if g != "main"]
    rows = []
    for ws_ in itertools.product(grid, repeat=len(others)):
        w = {"main": 1.0, **dict(zip(others, ws_))}
        wall, white, back, fl = [sum(w[g] * F[g][i] for g in w) for i in range(4)]
        x = wall / white
        eR = np.sqrt(np.mean((np.log(x[:, 0]) - P["R"]) ** 2))
        eG = np.sqrt(np.mean((np.log(np.maximum(x[:, 1], 1e-5)) - P["G"]) ** 2))
        eb = np.sqrt(np.mean((np.log(back @ LUM / (white @ LUM)) - P["back"]) ** 2))
        ef = np.sqrt(np.mean((np.log(fl @ LUM / (white @ LUM)) - P["floor"]) ** 2))
        sf = np.exp(np.mean([np.log(x[keys.index((fz, u)), 0] / x[keys.index((fz, 0.0)), 0]) for fz in fit.FZ for u in (-0.6, 0.6)]))
        rows.append((float(eR + eG + 0.5 * eb + 0.5 * ef), float(eR), float(eG), float(eb), float(ef), w, float(sf)))
    rows.sort(key=lambda r: r[0])
    psf = np.exp(np.mean([np.log(pwl[(fz, u)][0] / pwl[(fz, 0.0)][0]) for fz in fit.FZ for u in (-0.6, 0.6)]))
    print(f"photo: R side (u +-0.6) / front {psf:.2f}")
    for r in rows[:10]:
        print("score {:.3f} = R {:.3f} + G {:.3f} + back/2 {:.3f} + floor/2 {:.3f} | {} | R side/front {:.2f}".format(*r))
    best = rows[0]
    w = best[5]
    mixl = fit.develop(sum(w[g] * G[g] for g in w))
    b2, i2 = card.regions(mixl, "mix")
    bl = fit.blobs(mixl, b2, i2, 1.10)
    print("best mix blobs: " + "; ".join("u {:+.2f} v {:.2f} a {:.4f} w {:.2f} h {:.2f}".format(*b) for b in bl[:5]))
    print("photo blobs:    " + "; ".join("u {:+.2f} v {:.2f} a {:.4f} w {:.2f} h {:.2f}".format(*b) for b in pbl[:5]))
    json.dump({"best": {"weights": w, "score": best[0], "rms_log": dict(zip(["R", "G", "backdrop", "floor"], best[1:5])),
                        "R_side_over_front": best[6]}, "photo_R_side_over_front": float(psf),
               "top": [list(r) for r in rows[:20]], "blobs_best": bl[:5], "blobs_photo": pbl[:5]},
              open(os.path.join(d, "fit3.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main(sys.argv[1])
