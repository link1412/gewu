"""胭脂红 card, S8 r3: the cheapest test of a black-point offset in the Met's processing (docs/materials/yanzhi.md,
round 4). Model: photo = (render - b) / (1 - b), per channel, on everything over the inside's white (so the white
stays 1): an offset subtracted before the white is set, as a "levels" black point or a flare subtraction would. Fits b
(common to the three channels, or per channel) on the outer wall's 18 points (fit.FZ x fit.US) and scores log RMS
per channel before and after; the backdrop and floor (bright) barely move under such a b, so they do not constrain it.

    python3 -I materials/yanzhi/lightfit/blackpoint.py out/s8/yanzhi/r3/render/base [more dirs]
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import card  # noqa: E402
import fit  # noqa: E402


def wall(lin):
    box, info = card.regions(lin, "x")
    w = card.median_box(lin, box["white"])
    wl = fit.wall_abs(lin, box, info, lin)
    keys = [(fz, float(u)) for fz in fit.FZ for u in fit.US]
    return np.array([wl[k] for k in keys]) / w, keys


def main(dirs):
    P, keys = wall(card.photo_linear())
    for d in dirs:
        Rr, _ = wall(card.render_linear(d, "x.dn.exr"))
        def score(b):
            x = np.maximum((Rr - b) / (1 - b), 1e-4)
            return np.sqrt(np.mean((np.log(x) - np.log(np.maximum(P, 1e-4))) ** 2, 0))
        s0 = score(np.zeros(3))
        bs = np.linspace(0, 0.04, 81)
        common = min(bs, key=lambda b: score(np.full(3, b))[1:].sum() + score(np.full(3, b))[0])
        per = [min(bs, key=lambda b, c=c: score(np.eye(3)[c] * b)[c]) for c in range(3)]
        print(d)
        print(f"  log RMS R G B, no offset:        {s0.round(3)}")
        print(f"  common b {common:.4f}:             {score(np.full(3, common)).round(3)}")
        print(f"  per channel b {np.round(per, 4)}: {score(np.array(per)).round(3)}")
        # the front column vs the sides, G: photo / render, with and without
        for b in (0.0, common):
            x = (Rr - b) / (1 - b)
            print(f"  b {b:.4f} G photo/render by u (fz 0.3): " + " ".join(f"{P[i, 1] / max(x[i, 1], 1e-5):.2f}" for i in range(9)))


if __name__ == "__main__":
    main(sys.argv[1:])
