"""Compare Cycles' thin-film strips (tests/yohen/cycles_strip.py) with tools/tmm.py.

    python3 -I tests/yohen/strip_compare.py DIR --film 2.5 --sub 1.6 --dmax 600 --tag a --angles 0,30,60

DIR holds strip_<tag>_<angle>.exr. For each angle: the column means of the Cycles strip against the reference's
linear Rec.709 RGB (D65 white) at the same thicknesses; reports the error in reflectance and in CIELAB (D65), and
writes DIR/compare_<tag>.png: per angle, Cycles above, the reference below, at the same exposure.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import tmm  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--film", type=tmm._cx, required=True, help="complex index, e.g. 2.5 or 3.0+0.3j")
ap.add_argument("--sub", type=tmm._cx, required=True)
ap.add_argument("--dmax", type=float, required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--angles", default="0,30,60")
a = ap.parse_args()

S = tmm.spectra()
white = (S.cmf * S.d65).sum(1) / (S.cmf[1] * S.d65).sum()
xyz_from_rgb = np.linalg.inv(camera.rgb709_from_xyz(white))
rows, report = [], []
for ang in [float(x) for x in a.angles.split(",")]:
    cyc = camera.read_raw(os.path.join(a.dir, f"strip_{a.tag}_{ang:g}.exr")).mean(0)     # (W, 3)
    W = cyc.shape[0]
    d = (np.arange(W) + 0.5) / W * a.dmax
    # the edge columns' pixels straddle the plane's edge and see the white world: drop them
    cyc, d = cyc[1:-1], d[1:-1]
    W = len(d)
    cos0 = np.cos(np.radians(ang))
    R = np.array([tmm.reflectance(camera.LAM, [(a.film, x)], a.sub, 1.0, cos0) for x in d])
    ref = tmm.rgb709_of(R)
    lab_c = camera.lab(cyc @ xyz_from_rgb.T, white)
    lab_r = camera.lab(ref @ xyz_from_rgb.T, white)
    dE = np.linalg.norm(lab_c - lab_r, axis=1)
    Yc, Yr = (cyc @ xyz_from_rgb.T)[:, 1], (ref @ xyz_from_rgb.T)[:, 1]
    report.append((ang, np.median(dE), np.percentile(dE, 95), dE.max(), np.abs(Yc / Yr - 1).mean(),
                   d[np.argmax(dE)]))
    rows += [cyc, ref]
g = 1.0 / max(r.max() for r in rows)
img = np.concatenate([np.repeat(camera.srgb_encode(np.clip(r * g, 0, 1))[None], 40, 0) for r in rows])
Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(os.path.join(a.dir, f"compare_{a.tag}.png"))
print(f"film {a.film} on {a.sub}, 0..{a.dmax:g} nm")
print("angle  dE median  dE p95  dE max (at d nm)  |Y/Yref-1| mean")
for ang, med, p95, mx, ry, dm in report:
    print(f"{ang:5.0f}  {med:9.2f}  {p95:6.2f}  {mx:6.2f} ({dm:5.0f})  {ry:8.3f}")
