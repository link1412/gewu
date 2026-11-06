"""Solve scene.ARC_CORR so the visible top edge of region 2 makes the spec's arc, without rendering.

    python3 -I shots/17-peacock/arcfit.py [--seed 17]          # prints the corrections to paste into scene.py

Each region-2 barbule (scene.build: tip inside the corrected circle) is drawn from its base to its tip with its width
on a 1920x1080 mask; the upper edge, column by column, is fitted as the spec fitted the film (optics/framing.py
measure). Newton on (dx, dy, R_scale) against the spec's (apex_x, apex_y, sagitta). The render's edge also has the
barbules' bend and the lens blur, so the result is checked once more with tools/shotcheck.py after the render.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "optics"))
import framing  # noqa: E402
import scene  # noqa: E402

W, H = 1920, 1080


def edge_arc(seed):
    items = scene.build(seed)[0]["R2"]
    s = W / scene.FRAME_W
    L = scene.GEOM["barbule_len"]["R2"]
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    wpx = max(1, int(round(scene.GEOM["barbule_width"] * s)))
    for b, d2, _ in items:
        t = b + d2 * L
        dr.line([(W / 2 + b[0] * s, H / 2 - b[1] * s), (W / 2 + t[0] * s, H / 2 - t[1] * s)], fill=255, width=wpx)
    m = np.asarray(im) > 0
    cols = np.arange(0, W, framing.BIN_PX)
    x, y = [], []
    for c in cols:
        r = np.nonzero(m[:, c:c + framing.BIN_PX].any(1))[0]
        if len(r):
            x.append(c + framing.BIN_PX / 2)
            y.append(r[0])
    return framing.measure(np.array(x, float), np.array(y, float))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=17)
    a = ap.parse_args()
    tgt = np.array([scene.SHOT["arc"][k] for k in ("apex_x", "apex_y", "sagitta_of_width")])
    keys = ("dx", "dy", "R_scale")
    x = np.array([scene.ARC_CORR[k] for k in keys], float)

    def F(x):
        scene.ARC_CORR.update(dict(zip(keys, x)))
        r = edge_arc(a.seed)
        return np.array([r["apex_x"], r["apex_y"], r["sagitta_of_width"]]) - tgt

    for it in range(8):
        f = F(x)
        print(f"iter {it}: corr {np.round(x, 4).tolist()} miss {np.round(f, 4).tolist()}", flush=True)
        if np.abs(f).max() < 0.004:
            break
        J = np.zeros((3, 3))
        for j, h in enumerate((0.01, 0.01, 0.03)):
            dx = np.zeros(3)
            dx[j] = h
            J[:, j] = (F(x + dx) - f) / h
        x = x - np.linalg.lstsq(J, f, rcond=None)[0]
        x[2] = max(x[2], 0.2)
    print("ARC_CORR =", {k: round(float(v), 4) for k, v in zip(keys, x)})


if __name__ == "__main__":
    main()
