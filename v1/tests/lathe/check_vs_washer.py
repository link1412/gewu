"""tools/lathe.py against the inlined copy in objects/ru_washer/form.py it was taken from: on the washer's fitted
form and camera, the contours' distances to the washer's edge points must agree exactly (lathe.py adds two fixes,
for runs that meet at both ends and for flat rings; the washer has neither, so they must not change anything).

    python3 -I tests/lathe/check_vs_washer.py      (needs out/ru/washer/{fit,edges}.json: form.py fit, measure.py)
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "objects/ru_washer"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import form as W  # noqa: E402
import lathe  # noqa: E402

fit = json.load(open(os.path.join(ROOT, "out/ru/washer/fit.json")))["x"]
names = [n for n in W.NAMES if n in fit]
p = W.params_dict([fit[n] for n in names], names)
q = dict(p, ref_z=W.REF_Z, cx=W.PHOTO_SIZE[0] / 2, cy=W.PHOTO_SIZE[1] / 2)
V = W.outer_visible(p)
E = {k: np.asarray(v) for k, v in json.load(open(os.path.join(ROOT, "out/ru/washer/edges.json")))["sets"].items()}
ok = True
for part, vm in (("lip", 1.0), ("wall", 0.6), ("foot", 1.0)):
    a = [W.project(L, p) for L in W.contour_points(*V[part], p, vmax=vm)]
    b = [lathe.project(L, q) for L in lathe.contour_points(*V[part], q, vmax=vm)]
    for k, P in E.items():
        d = np.abs(W.Polylines(a).distance(P) - lathe.Polylines(b).distance(P)).max()
        ok &= d == 0
    print(f"{part:5s} polylines {len(a)} / {len(b)}")
print("lathe.py vs ru_washer:", "identical" if ok else "DIFFERENT")
sys.exit(0 if ok else 1)
