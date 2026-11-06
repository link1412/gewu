"""胭脂红 card, round 2: score mixes of the clean renders (clean.py's four) by card.py's six-region CIEDE2000 against
the photo, over the rear and top strengths, the sweep's reflectance (interpolated, [A]) and c (0.45 or 0.56, real
renders, no interpolation). The light fit by luminance (clean.py) and this colour score are reported side by side.

    python3 -I materials/yanzhi/lightfit/colourgrid.py
"""
import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "tools"))
import card  # noqa: E402
import clean  # noqa: E402
from camera import read_raw  # noqa: E402
import fit  # noqa: E402


def regions_lab(lin):
    box, info = card.regions(lin, "mix")
    w = card.median_box(lin, box["white"])
    return {k: card.lab_of(card.median_box(lin, b) / w) for k, b in box.items() if k != "white"}


def main():
    P = regions_lab(card.photo_linear())
    raws = {k: {g: read_raw(os.path.join(clean.D, n, f"x.{g}.exr")) for g in ("main", "rear", "top")}
            for k, n in clean.RUNS.items()}
    rows = []
    for wr, wt, rho, c in itertools.product([0, 1, 3], [0, 1], [0.18, 0.3, 0.45, 0.6, 0.9], [0.45, 0.56]):
        t = (rho - 0.18) / 0.72
        w = {"main": 1.0, "rear": wr, "top": wt}
        img = sum(w[g] * ((1 - t) * raws[("grey", c)][g] + t * raws[("white", c)][g]) for g in w)
        try:
            L = regions_lab(fit.develop(img))
        except SystemExit as e:             # card.regions' outline rule fails on a sweep as bright as the white
            print("skip", wr, wt, rho, c, e)
            continue
        d = {k: card.de2000(P[k], L[k]) for k in P}
        cen = np.mean([d["centre_upper"], d["centre_lower"]])
        rows.append((float(np.mean(list(d.values()))), float(cen), wr, wt, rho, c,
                     float(np.mean([L[k][1] - P[k][1] for k in P]))))
        print("mean dE00 {:.2f} centre {:.2f} | rear {} top {} rho {} c {} | a* render - photo {:+.1f}".format(*rows[-1]),
              flush=True)
    rows.sort()
    print("best:")
    for r in rows[:6]:
        print("  mean dE00 {:.2f} centre {:.2f} | rear {} top {} rho {} c {} | da* {:+.1f}".format(*r))
    json.dump(rows, open(os.path.join(clean.D, "colourgrid.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
