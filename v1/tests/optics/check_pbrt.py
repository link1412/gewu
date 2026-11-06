"""Test b, the numbers: each light group in Cycles (one grouped render) against the same group in pbrt (that group
alone lit, spectral; the reference).

    python3 -I tests/optics/check_pbrt.py [--recipe vase-product_three]     (after run_pbrt.py)

Regions from the Cycles render's denoising albedo: the backdrop (albedo within 0.02 of the backdrop's own camera-RGB
reflectance, from scene.cycles.json) and the rest, "object" (the object and what it mirrors; also a lamp seen
directly, if one is in the frame: an emitter's albedo carries its emission, so it is never taken for the backdrop). Per group, region and camera channel: the ratio of the mean raw values, Cycles / pbrt,
and its 2-sigma noise from 16 x 16 px blocks (the spread of the blocks' Cycles - pbrt differences / sqrt(their
number), over pbrt's mean: the picture cancels in the difference, the noise of both renders stays). The noise sets
what the test can see: a ratio within 1 +- 2 sigma is agreement at that precision.
Known difference: Cycles renders camera RGB (reflectances projected with the sensor x the rig's blackbody, exact for
one bounce of that light, docs/optics.md), pbrt the spectrum; the rig has one spectrum (v0), so they differ only
after several bounces, in the glaze's medium and between object and backdrop.
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as C  # noqa: E402
import json  # noqa: E402

BLOCK = 16


def block_means(img, m):
    """Means over BLOCK x BLOCK blocks of the pixels in mask m (blocks with at least half their pixels in m)."""
    H, W = m.shape
    h, w = H // BLOCK, W // BLOCK
    mm = m[:h * BLOCK, :w * BLOCK].reshape(h, BLOCK, w, BLOCK).astype(float)
    cnt = mm.sum((1, 3))
    out = []
    for c in range(3):
        v = (img[:h * BLOCK, :w * BLOCK, c] * m[:h * BLOCK, :w * BLOCK]).reshape(h, BLOCK, w, BLOCK).sum((1, 3))
        out.append(v[cnt >= BLOCK * BLOCK / 2] / cnt[cnt >= BLOCK * BLOCK / 2])
    return np.array(out)                      # (3, n blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", default="vase-product_three")
    a = ap.parse_args()
    d = os.path.join(ROOT, f"out/optics/pbrt-{a.recipe}")
    groups = json.load(open(os.path.join(d, "build.json")))["groups"]
    alb = C.read_raw(os.path.join(d, "x.albedo.exr"))
    sc = json.load(open(os.path.join(d, "scene.cycles.json")))
    bd = np.array(next(o["material"]["reflectance"] for o in sc["objects"] if o.get("file") == "backdrop.ply"))
    back = np.abs(alb - bd).max(2) < 0.02
    regions = {"object": ~back, "backdrop": back}
    print(f"{a.recipe}: regions (pixels) " + ", ".join(f"{k} {int(v.sum())}" for k, v in regions.items()))
    print("ratio Cycles / pbrt of the mean raw value, per camera channel, +- 2 sigma of the noise")
    for g in groups:
        cy = C.read_raw(os.path.join(d, f"x.{g}.exr"))
        pb = C.read_raw(os.path.join(d, f"pbrt.{g}.exr"))
        print(f"  {g}: whole frame {np.round(cy.mean((0, 1)) / pb.mean((0, 1)), 4)}")
        for k in ("object", "backdrop"):
            m = regions[k]
            if m.sum() < 4 * BLOCK * BLOCK:
                continue
            bc, bp = block_means(cy, m), block_means(pb, m)
            n = bc.shape[1]
            mc, mp = bc.mean(1), bp.mean(1)
            if not (mp > 0).all():
                print(f"    {k:9s}: pbrt's mean is zero in a channel")
                continue
            r = mc / mp
            sig = (bc - bp).std(1, ddof=1) / np.sqrt(n) / mp      # the spread of the blocks' differences: the
            # picture cancels, the noise of both renders (and any local disagreement) stays
            share = pb[m].sum() / pb.sum()
            print(f"    {k:9s}: {' '.join(f'{x:.4f}+-{2 * s:.4f}' for x, s in zip(r, sig))}  "
                  f"({n} blocks; {share:.0%} of this group's light in the frame)")


if __name__ == "__main__":
    main()
