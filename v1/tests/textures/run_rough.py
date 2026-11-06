"""Test b, the runs (pbrt on the CPU, Cycles on the GPU) into out/textures/rough/.

    python3 -I tests/textures/run_rough.py [--spp 128]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gen_rough as G  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--spp", type=int, default=128)
a = ap.parse_args()
d = os.path.join(C.OUT, "rough")
G.build(d, a.spp)
C.push("rough", glob.glob(d + "/scene_*") + glob.glob(d + "/*.pfm"))
V = ("step", "uni1", "uni2")
logs = [C.pbrt("rough", f"scene_{v}.pbrt", f"pbrt_{v}") for v in V]
logs += [C.cycles("rough", f"scene_{v}.cycles.json", f"cyc_{v}.exr", f"--spp {a.spp} --seed 1") for v in V]
C.wait(logs)
C.pull("rough", [f"pbrt_{v}.exr" for v in V] + [f"cyc_{v}.exr" for v in V], d)
