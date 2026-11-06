"""胭脂红 card, round 2: fit the light's group strengths and the gold's c together (docs/materials/yanzhi.md).

Two renders of the same rig at c0 and c1 (probe.py; light groups). Light adds, so a mix of groups is exact at each c;
between the two c, every measured value (the outer wall's luminance over the white, per row and column; the
backdrop over the white) is interpolated log-linearly in c [A: the wall's luminance is near exponential in c, as
exp(-c kappa) is; checked by the confirming render]. Score: rms of log(model / photo) over the wall's 18 points +
back_weight x rms over the 3 backdrop points.

    python3 -I materials/yanzhi/lightfit/joint.py DIR_c0 DIR_c1 --c 0.5 0.8 --geo PROBE_DIR
"""
import argparse
import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fit  # noqa: E402
from fit import LUM  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("d0")
    ap.add_argument("d1")
    ap.add_argument("--c", type=float, nargs=2, required=True)
    ap.add_argument("--geo", required=True)
    ap.add_argument("--back-weight", type=float, default=0.5)
    ap.add_argument("--fixed", default="main")
    a = ap.parse_args()
    lin, pbox, pinfo, pwl, pbl = fit.photo_features()
    keys = [(fz, float(u)) for fz in fit.FZ for u in fit.US]
    pw = np.log([float(pwl[k] @ LUM) for k in keys])
    pb = np.log(fit.backdrop(lin, pbox, pinfo) @ LUM)
    G0 = fit.probe_data(a.geo)
    geo = (G0["box"], G0["info"], G0["ref"])
    Ds = [fit.probe_data(d, geo) for d in (a.d0, a.d1)]
    gs = Ds[0]["groups"]
    others = [g for g in gs if g != a.fixed]
    grid = [0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    cs = np.linspace(0.3, 1.2, 37)
    t = (cs - a.c[0]) / (a.c[1] - a.c[0])
    rows = []
    for ws in itertools.product(grid, repeat=len(others)):
        parts = [(a.fixed, 1.0)] + [(g, w) for g, w in zip(others, ws) if w]
        vals = []
        for D in Ds:
            wl, bk = fit.evaluate(D, parts)
            vals.append((np.log([float(wl[k] @ LUM) for k in keys]), np.log(bk @ LUM)))
        W = vals[0][0][None] + t[:, None] * (vals[1][0] - vals[0][0])[None]      # c x 18
        B = vals[0][1][None] + t[:, None] * (vals[1][1] - vals[0][1])[None]
        ew = np.sqrt(np.mean((W - pw) ** 2, 1))
        eb = np.sqrt(np.mean((B - pb) ** 2, 1))
        s = ew + a.back_weight * eb
        i = int(np.argmin(s))
        rows.append((float(s[i]), float(ew[i]), float(eb[i]), float(cs[i]), dict(zip(others, ws)),
                     np.exp(W[i]).round(3), np.exp(B[i]).round(2)))
    rows.sort(key=lambda r: r[0])
    print("photo wall:", np.exp(pw).round(3), "backdrop", np.exp(pb).round(2))
    for r in rows[:10]:
        print("score {:.3f} wall {:.3f} back {:.3f} | c {:.3f} | {}".format(*r[:5]))
    r = rows[0]
    print("best wall:", r[5], "backdrop", r[6])
    json.dump({"c": r[3], "weights": {a.fixed: 1.0, **r[4]}, "score": r[0], "wall_rms_log": r[1], "back_rms_log": r[2],
               "top": [[x[0], x[1], x[2], x[3], x[4]] for x in rows[:20]]},
              open(os.path.join(a.d0, "joint.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
