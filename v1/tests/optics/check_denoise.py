"""Test d: denoise after mixing, or each group before? Against a reference with 64 times the samples.

    python3 -I tests/optics/check_denoise.py          (after run_sum.py and the reference, see below)

Renders (out/optics/sum, product_three on the vase, 480x270, Cycles on the GPU): the grouped render g1 (64 spp,
seed 1) with its denoising albedo and normal, and ref (the same lamps untagged, 4096 spp, seed 7, not denoised).
Three ways to the picture with every group at its scene strength:
  A. sum the groups, no denoising;
  B. sum the groups, then OIDN once (what tools/build.py does);
  C. OIDN each group, then sum.
Each against ref: rms error over the pixels that see no lamp, relative to their mean, per pixel and in 4 x 4 px
blocks (the reference's noise drops 4 times there, a denoiser's smooth errors stay), and the mean ratio. The
reference's own noise is about A's error / 8 (64 times the samples); an error near it is below what this test sees.
OIDN runs in this machine's Blender (tools/cycles_denoise.py), with the render's albedo and normal, HDR, prefilter
"Accurate".
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build as B  # noqa: E402
import camera as C  # noqa: E402

D = os.path.join(ROOT, "out/optics/sum")
GROUPS = json.load(open(os.path.join(D, "build.json")))["groups"]


def main():
    g = {k: C.read_raw(os.path.join(D, f"g1.{k}.exr")) for k in GROUPS}
    ref = C.read_raw(os.path.join(D, "ref.exr"))
    alb = C.read_raw(os.path.join(D, "g1.albedo.exr"))
    m = alb.max(2) <= 1.01                                # no lamp seen, directly or in a sharp reflection
    tmp = os.path.join(D, "denoise_test")
    os.makedirs(tmp, exist_ok=True)
    noisy = {"sum": sum(g.values()), **g}
    pairs = []
    for k, img in noisy.items():
        B.write_pfm(os.path.join(tmp, f"{k}.pfm"), img)
        pairs.append((os.path.join(tmp, f"{k}.pfm"), os.path.join(tmp, f"{k}.dn.exr")))
    B.denoise(pairs, os.path.join(D, "g1.albedo.exr"), os.path.join(D, "g1.normal.exr"))
    dn = {k: C.read_raw(os.path.join(tmp, f"{k}.dn.exr")) for k in noisy}
    ways = {"A  sum, no denoising": noisy["sum"], "B  sum, then denoise (build.py)": dn["sum"],
            "C  denoise each group, then sum": sum(dn[k] for k in GROUPS)}
    mean = float(ref[m].mean())
    print(f"reference: 4096 spp; {m.mean():.1%} of the pixels see no lamp, their mean {mean:.4g} (raw)")
    def blocks(img):                                      # 4 x 4 px means (only blocks that see no lamp)
        H, W = m.shape
        x = img[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4, 3).mean((1, 3))
        return x[m[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).all((1, 3))]
    rb = blocks(ref)
    for name, img in ways.items():
        e = img[m] - ref[m]
        eb = blocks(img) - rb
        print(f"{name}: rms error {np.sqrt(np.mean(e ** 2)) / mean:.4f} of the mean per pixel, "
              f"{np.sqrt(np.mean(eb ** 2)) / mean:.4f} in 4x4 px blocks; mean ratio per channel "
              f"{np.round(img[m].mean(0) / ref[m].mean(0), 4)}")
    na = np.sqrt(np.mean((noisy["sum"][m] - ref[m]) ** 2)) / mean
    nb = np.sqrt(np.mean((blocks(noisy["sum"]) - rb) ** 2)) / mean
    print(f"the reference's own noise: about {na / 8:.4f} of the mean per pixel, {nb / 8:.4f} in blocks (A's / 8)")


if __name__ == "__main__":
    main()
