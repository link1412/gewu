"""Coat test, the renders: gen_coat.py's scene in pbrt (patched, CPU slots) and Cycles (GPU), then check_coat.py.

    python3 -I tests/qinghua/run_coat.py [--spp-pbrt 256] [--spp-cycles 1024] [--deploy]
--deploy first copies tools/cycles_scene.py to the test copy (qh.TOOLS).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_coat  # noqa: E402
import qh  # noqa: E402

SCENES = list(gen_coat.VARIANTS) + ["ref"]
FILES = ([f"{v}.pbrt" for v in SCENES] + [f"{v}.cycles.json" for v in SCENES]
         + ["coat_quad.ply", "film.npz", "red.npz", "film_c.pfm", "base_c.pfm"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spp-pbrt", type=int, default=256)
    ap.add_argument("--spp-cycles", type=int, default=1024)
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--only", nargs="+", default=SCENES, help="render only these scenes")
    a = ap.parse_args()
    d = gen_coat.build(os.path.join(qh.OUT, "coat"), spp=a.spp_pbrt)
    if a.deploy:
        qh.sh(f"scp -q {qh.ROOT}/tools/cycles_scene.py link:{qh.TOOLS}/cycles_scene.py.tmp && "
              f"ssh link 'mv {qh.TOOLS}/cycles_scene.py.tmp {qh.TOOLS}/cycles_scene.py'")
    qh.push("coat", [f"{d}/{f}" for f in FILES])
    logs = [qh.pbrt("coat", f"{v}.pbrt", f"pbrt-{v}") for v in a.only]
    logs += [qh.cycles("coat", f"{v}.cycles.json", f"{v}_cycles.exr", f"--spp {a.spp_cycles}") for v in a.only]
    qh.wait(logs)
    qh.pull("coat", [f"{v}_{r}.exr" for v in a.only for r in ("pbrt", "cycles")], d)
    print("pulled into", d)


if __name__ == "__main__":
    main()
