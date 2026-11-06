"""Test a, the runs: pbrt (CPU slots) and Cycles, into out/metals/fresnel/.

    python3 -I tests/metals/run_fresnel.py [--spp 128] [--only Au_a0,...]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcommon as C  # noqa: E402
import gen_fresnel as G  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--spp", type=int, default=128)
ap.add_argument("--only")
a = ap.parse_args()
d = os.path.join(C.OUT, "fresnel")
G.build(d, a.spp)
V = a.only.split(",") if a.only else list(G.VARIANTS)
C.deploy_adapter()
C.push("fresnel", [f"{d}/scene_{v}.pbrt" for v in V] + [f"{d}/scene_{v}.cycles.json" for v in V])
logs = [C.pbrt("fresnel", f"scene_{v}.pbrt", f"pbrt_{v}") for v in V]
logs += [C.cycles("fresnel", f"scene_{v}.cycles.json", f"cyc_{v}.exr", f"--spp {a.spp} --seed 1") for v in V]
C.wait(logs)
C.pull("fresnel", [f"pbrt_{v}.exr" for v in V] + [f"cyc_{v}.exr" for v in V] + [f"cyc_{v}.json" for v in V], d)
