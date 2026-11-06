"""Shot 68: does the compositor's refraction agree with Cycles? Black beads under the water in a render (s68_chase.py markers) against their projection. Prints the error per bead, in pixels at the render's width, and at 2560."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import torch

import kit
import s68_comp as C

D = os.path.join(kit.OUT, "s68_chase")
M = np.load(os.path.join(D, "markers.linear.npy"))
h, w = M.shape[:2]
pts = np.array(json.load(open(os.path.join(D, "markers.json"))), np.float32)
view = C.View(w, h)
uu, vv, coc = view.project(torch.from_numpy(pts).to(C.DEV))
g = M.mean(-1)
errs = []
for i, (u, v) in enumerate(zip(uu.tolist(), vv.tolist())):
    r = 22
    x0, x1, y0, y1 = max(int(u) - r, 0), min(int(u) + r, w), max(int(v) - r, 0), min(int(v) + r, h)
    if x1 <= x0 or y1 <= y0:
        print(i, "off frame", u, v)
        continue
    a = g[y0:y1, x0:x1]
    # darkness against the local background (the wall varies slowly)
    d = np.clip(np.median(a) - a, 0, None)
    d[d < 0.5 * d.max()] = 0
    Y, X = np.mgrid[y0:y1, x0:x1]
    cx, cy = (d * (X + 0.5)).sum() / d.sum(), (d * (Y + 0.5)).sum() / d.sum()
    e = np.hypot(cx - u, cy - v)
    errs.append(e)
    print(f"bead {i} {pts[i].tolist()}: projected ({u:.2f}, {v:.2f}) rendered ({cx:.2f}, {cy:.2f}) error {e:.2f} px, {e*2560/w:.2f} px at 2560")
print(f"mean {np.mean(errs):.2f} px, max {np.max(errs):.2f} px at {w} wide; max {np.max(errs)*2560/w:.2f} px at 2560")
