"""Test a, the numbers: do the groups add up to the whole, and does a mix weight act as a lamp's strength?

    python3 -I tests/optics/check_sum.py          (after run_sum.py)

a1. One render (seed 1): its combined image against the sum of its group passes. Should agree to float rounding.
a2. The same lamps untagged, the old one-image path (all1, seed 1), against the grouped render's sum of groups (seed 1).
    Noise floor: the same untagged scene at seed 2 (all2).
a3. The key's illuminance doubled in the scene (k2, seed 1) against the seed-1 groups mixed with the key at +1 stop.
    The lamp's power changes how Cycles picks lights, so the samples differ: agreement is at the noise level. Noise
    floor: the same mix from the seed-2 groups. Discrimination: the k2 render against the mix with the key at 0.
Numbers in the camera's raw units; "rel" divides by the image's mean.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as C  # noqa: E402

D = os.path.join(ROOT, "out/optics/sum")
GROUPS = json.load(open(os.path.join(D, "build.json")))["groups"]


def rd(name):
    return C.read_raw(os.path.join(D, name))


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)))


def main():
    g1 = {g: rd(f"g1.{g}.exr") for g in GROUPS}
    g2 = {g: rd(f"g2.{g}.exr") for g in GROUPS}
    k2g = {g: rd(f"k2.{g}.exr") for g in GROUPS}
    c1, all1, all2, k2 = rd("g1.exr"), rd("all1.exr"), rd("all2.exr"), rd("k2.exr")
    s1 = sum(g1.values())
    m = float(c1.mean())
    print(f"image mean {m:.4f} (raw), max {c1.max():.2f}; groups' shares of the mean: "
          + ", ".join(f"{g} {g1[g].mean() / s1.mean():.1%}" for g in GROUPS))
    d = c1 - s1
    print(f"a1  combined - sum of groups (one render): max |d| {np.abs(d).max():.3g} ({np.abs(d).max() / m:.2g} of the mean), "
          f"rms {rms(d):.3g}, mean {d.mean():.3g}")
    d2 = all1 - s1
    nf = all1 - all2
    print(f"a2  untagged (old path) - sum of groups, same seed: max |d| {np.abs(d2).max():.3g}, rms {rms(d2):.3g} "
          f"({rms(d2) / m:.2g} rel), mean ratio per channel {np.round(all1.mean((0, 1)) / s1.mean((0, 1)), 6)}; "
          f"pixels differing {np.mean(np.abs(d2) > 0):.1%}")
    print(f"    noise floor, untagged seed 1 - seed 2: rms {rms(nf):.3g} ({rms(nf) / m:.2g} rel)")
    mix1 = g1["key"] + sum(g1.values())                    # the key at +1 stop, the rest at 0
    mix2 = g2["key"] + sum(g2.values())
    e = k2 - mix1
    print(f"a3  key x2 in the scene - mix with key +1 stop: rms {rms(e):.3g} ({rms(e) / k2.mean():.3g} rel), "
          f"mean ratio per channel {np.round(k2.mean((0, 1)) / mix1.mean((0, 1)), 5)}")
    print(f"    noise floor, the same mix seed 1 - seed 2: rms {rms(mix1 - mix2):.3g} ({rms(mix1 - mix2) / k2.mean():.3g} rel)")
    print(f"    the k2 render's own key pass / the seed-1 key pass: mean ratio {np.round(k2g['key'].mean((0, 1)) / g1['key'].mean((0, 1)), 5)}; "
          f"its other passes / seed 1's: " + ", ".join(f"{g} {k2g[g].mean() / g1[g].mean():.5f}" for g in GROUPS if g != "key"))
    w = k2 - c1
    print(f"    discrimination, k2 - the mix with the key at 0 (the plain render): rms {rms(w):.3g} ({rms(w) / k2.mean():.3g} rel), "
          f"mean ratio {np.round(k2.mean((0, 1)) / c1.mean((0, 1)), 4)}")
    for name, b in (("half a stop", 2 ** 0.5), ("a tenth of a stop", 2 ** 0.9)):
        mb = (b - 1) * g1["key"] + s1
        x = k2 - mb
        print(f"    resolution: the mix with the key at {np.log2(b):+.1f} stops instead of +1 ({name} off): rms {rms(x):.3g}, "
              f"mean ratio {np.round(k2.mean() / mb.mean(), 4)}")


if __name__ == "__main__":
    main()
