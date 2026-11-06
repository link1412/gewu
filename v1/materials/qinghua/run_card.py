"""Render the material card (Cycles on the GPU, pbrt on a CPU slot), pull, develop and compare.

    python3 -I materials/qinghua/run_card.py out/materials/qinghua/card_co [--spp-cycles 256] [--spp-pbrt 64] [--no-pbrt]
The directory comes from card.py build.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests/qinghua"))
import qh  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--spp-cycles", type=int, default=256)
    ap.add_argument("--spp-pbrt", type=int, default=64)
    ap.add_argument("--no-pbrt", action="store_true")
    a = ap.parse_args()
    d = os.path.abspath(a.dir)
    name = "card-" + os.path.basename(d)
    files = [f"{d}/{f}" for f in ("scene.pbrt", "scene.cycles.json", "film.npz", "c.pfm", "coat_quad.ply")]
    qh.push(name, files)
    logs = [qh.cycles(name, "scene.cycles.json", "cycles.exr", f"--spp {a.spp_cycles}")]
    if not a.no_pbrt:
        logs.append(qh.pbrt(name, "scene.pbrt", "pbrt", f"--spp {a.spp_pbrt} --outfile pbrt.exr"))
    qh.wait(logs)
    got = ["cycles.exr"] + ([] if a.no_pbrt else ["pbrt.exr"])
    qh.pull(name, got, d)
    card = os.path.join(HERE, "card.py")
    subprocess.run([sys.executable, "-I", card, "develop", d, "--which"] + [g[:-4] for g in got], check=True)
    subprocess.run([sys.executable, "-I", card, "compare", d], check=True)


if __name__ == "__main__":
    main()
