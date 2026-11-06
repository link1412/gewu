"""The Guan card (materials/guan_glaze/card.py) after its glaze became a closed shell: Cycles on the GPU against
pbrt on the CPU, per channel, over the frame and in 8 x 8 blocks, and for the heirloom state along its filled
cracks (where a dark line showed in Cycles). Run after the renders are fetched into
out/ru/guan_check/r/{pbrt,cyc}-{plain,heirloom}.exr and cyc-heirloom-s7.exr (docs/slab.md)."""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import read_raw  # noqa: E402

OUT = os.path.join(ROOT, "out/ru/guan_check")


def blocks(a, n=8):
    h, w = a.shape[:2]
    a = a[: h - h % n, : w - w % n]
    return a.reshape(n, a.shape[0] // n, n, a.shape[1] // n, -1).mean((1, 3)).reshape(n * n, -1)


def main():
    res = {}
    for v in ("plain", "heirloom"):
        p = read_raw(os.path.join(OUT, "r", f"pbrt-{v}.exr"))
        c = read_raw(os.path.join(OUT, "r", f"cyc-{v}.exr"))
        bp, bc = blocks(p), blocks(c)
        r = bc / bp
        res[v] = {"frame_cyc_over_pbrt": (c.mean((0, 1)) / p.mean((0, 1))).tolist(),
                  "blocks_ratio_mean": r.mean(0).tolist(), "blocks_ratio_sd": r.std(0, ddof=1).tolist(),
                  "blocks_ratio_min": r.min(0).tolist(), "blocks_ratio_max": r.max(0).tolist()}
        print(v, "frame Cycles/pbrt (R G B):", " ".join(f"{x:.4f}" for x in res[v]["frame_cyc_over_pbrt"]),
              "| 8x8 blocks mean", " ".join(f"{x:.4f}" for x in res[v]["blocks_ratio_mean"]),
              "sd", " ".join(f"{x:.4f}" for x in res[v]["blocks_ratio_sd"]))
        if v == "heirloom":
            # the lines: pixels darker than their 9-pixel neighbourhood by > 3% (the filled cracks show as lines in
            # this state), found in a third render with its own seed (Cycles, 8192 spp): a mask taken from either
            # compared image would pick that image's dark noise. The same pixels' Cycles/pbrt, against the rest.
            from scipy.ndimage import uniform_filter
            g = read_raw(os.path.join(OUT, "r", "cyc-heirloom-s7.exr"))[..., 1]
            loc = uniform_filter(g, 9)
            line = g < 0.97 * loc
            rest = g > loc
            for name, m in (("lines", line), ("off-line", rest)):
                q = c[m].mean(0) / p[m].mean(0)
                res[v][f"{name}_cyc_over_pbrt"] = q.tolist()
                res[v][f"{name}_pixels"] = int(m.sum())
                print(f"  {name:8s} ({m.sum():6d} px) Cycles/pbrt", " ".join(f"{x:.4f}" for x in q))
            # line contrast (line / neighbourhood) in each renderer
            for name, im in (("pbrt", p), ("Cycles", c)):
                gg = im[..., 1]
                k = float((gg[line] / uniform_filter(gg, 9)[line]).mean())
                res[v][f"line_contrast_{name}"] = k
                print(f"  line / 9-px neighbourhood, G, {name}: {k:.4f}")
    with open(os.path.join(OUT, "compare.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
