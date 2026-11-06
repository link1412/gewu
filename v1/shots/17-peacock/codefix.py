"""Shot 17: lightfit matches linear region means; shotcheck judges mean 8-bit codes, and on a mottled frame the two
differ by 10+ codes (the original's middle band: code of the linear mean (105, 140, 103), mean code (92, 120, 92)).
One fixed-point step: scale lightfit's target (the original in raw camera RGB, 640x360) per shotcheck region and
channel by (original mean code / our mean code), each linearised, and write it as the spec's target_raw.

    python3 -I shots/17-peacock/codefix.py --dev out/shots/17-peacock/r1/dev1080/f0240.png [--reset]
Writes out/shots/17-peacock/r1/target_raw.pfm and points shots/17-peacock/lightfit.json at it. [F]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import lightfit as L  # noqa: E402
import shotcheck  # noqa: E402

SPEC = os.path.join(HERE, "lightfit.json")
OUTP = os.path.join(ROOT, "out/shots/17-peacock/r1/target_raw.pfm")
ROWS = {"top60": (0, 60), "upper": (60, 360), "middle": (360, 720), "bottom": (720, 1080)}

ap = argparse.ArgumentParser()
ap.add_argument("--dev", required=True)
ap.add_argument("--reset", action="store_true")
a = ap.parse_args()
s = json.load(open(SPEC))
M, cam = L.chain(L.P(s["camera"]))
d = cam["develop"]
W, H = s["res"]
if a.reset or not os.path.exists(OUTP):
    T = L.original_raw(L.P("ref/opus55.mp4"), range(236, 244), W, H, M, cam, "linear")
else:
    T = L.read_image(OUTP)
o = np.mean([shotcheck.orig_frames([f])(f).astype(float) for f in (236, 240, 243)], 0)
u = np.asarray(Image.open(a.dev).convert("RGB"), float)
Minv = np.linalg.inv(M)


def lin(c):          # mean code -> display-linear -> raw, through the inverse of to8 (no shoulder above 0.5 kept: unshoulder)
    x = L.unshoulder(camera.srgb_decode(np.asarray(c) / 255.0), d)
    return x


for k, (r0, r1) in ROWS.items():
    co, cu = o[r0:r1].reshape(-1, 3).mean(0), u[r0:r1].reshape(-1, 3).mean(0)
    f = lin(co) / lin(cu)                      # display-linear per channel
    g = Minv @ np.diag(f) @ M                  # as a raw-space map
    y0, y1 = int(r0 / 1080 * H), int(r1 / 1080 * H)
    T[y0:y1] = T[y0:y1] @ g.T
    print(k, "orig", co.round(1), "ours", cu.round(1), "factor", f.round(3))
L.write_pfm(OUTP, T)
s["frames"] = [{"name": "f00", "target_raw": os.path.relpath(OUTP, ROOT)}]
json.dump(s, open(SPEC, "w"), indent=1)
print("->", OUTP)
