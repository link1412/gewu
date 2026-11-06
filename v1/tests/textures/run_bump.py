"""Test a, the runs: pbrt (CPU) and Cycles (GPU) on the three bump scenes, results into out/textures/bump/.

    python3 -I tests/textures/run_bump.py [--spp 128]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gen_bump as G  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--spp", type=int, default=128)
a = ap.parse_args()
d = os.path.join(C.OUT, "bump")
G.build(d, a.spp)
C.push("bump", glob.glob(d + "/scene_*") + glob.glob(d + "/*.pfm") + glob.glob(d + "/*.ply") + glob.glob(d + "/*.png"))
logs = [C.pbrt("bump", f"scene_{v}.pbrt", f"pbrt_{v}") for v in ("bump", "zero", "plain", "ply", "png")]
logs += [C.cycles("bump", f"scene_{v}.cycles.json", f"cyc_{v}.exr", f"--spp {a.spp} --seed 1") for v in ("bump", "zero", "plain", "ply", "png")]
C.wait(logs)
C.pull("bump", [f"pbrt_{v}.exr" for v in ("bump", "zero", "plain", "ply", "png")] + [f"cyc_{v}.exr" for v in ("bump", "zero", "plain", "ply", "png")], d)
