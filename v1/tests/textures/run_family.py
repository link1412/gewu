"""Test c, the runs: Cycles on the GPU, two seeds of the family scene and one of the reference.

    python3 -I tests/textures/run_family.py [--spp 64]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gen_family as G  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--spp", type=int, default=64)
a = ap.parse_args()
d = os.path.join(C.OUT, "family")
G.build(d, a.spp)
C.push("family", glob.glob(d + "/scene_*") + glob.glob(d + "/*.npz") + glob.glob(d + "/ramp_*"))
logs = [C.cycles("family", "scene_fam.cycles.json", "fam1.exr", f"--spp {a.spp} --seed 1"),
        C.cycles("family", "scene_fam.cycles.json", "fam2.exr", f"--spp {a.spp} --seed 2"),
        C.cycles("family", "scene_ref.cycles.json", "ref1.exr", f"--spp {a.spp} --seed 1")]
C.wait(logs)
C.pull("family", ["fam1.exr", "fam2.exr", "ref1.exr"], d)
