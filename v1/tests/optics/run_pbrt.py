"""Test b, the runs: each light group in Cycles against the same group in pbrt (spectral, the reference).

    python3 -I tests/optics/run_pbrt.py [--recipe vase-product_three] [--cycles-spp 1024] [--pbrt-spp 256]

Stages the recipe into out/optics/pbrt-<recipe>/ (tools/build.py), renders the grouped scene once in Cycles on the
GPU (x.<group>.exr) and each scene.<group>.pbrt (only that group lit, the same geometry) with pbrt on the CPU
slots, all at 480x270, and pulls them back.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", default="vase-product_three")
    ap.add_argument("--cycles-spp", type=int, default=1024)
    ap.add_argument("--pbrt-spp", type=int, default=256)
    ap.add_argument("--remote-tools", default="~/gewu-render/tools-test-optics")
    ap.add_argument("--rnee", action="store_true", help="keep pbrt's refracted light connections (they abort here, S3)")
    a = ap.parse_args()
    recipe = json.load(open(os.path.join(HERE, f"recipes/{a.recipe}.json")))
    if not a.rnee:
        # our patched pbrt's refracted light connections (docs/rnee.md) abort on this scene (S3: "Check failed:
        # si->tHit < 1.001 * tMax with si->tHit = NaN" in SampleLdRefracted, pixel (199, 136) sample 19; the scene is
        # kept in out/optics/rnee-crash/). Without them pbrt is still unbiased, only noisier inside the glaze; Cycles
        # never had them.
        recipe["render"]["refractivenee"] = False
    out = os.path.join(ROOT, f"out/optics/pbrt-{a.recipe}")
    name = f"optics-pbrt-{a.recipe}"
    groups = B.stage(recipe, out, (480, 270), a.pbrt_spp)
    B.push(out, name)
    logs = [B.queue_cycles(name, "gpu", a.remote_tools, f"--spp {a.cycles_spp} --seed 1", tag="-cycles")]
    logs += [B.queue_pbrt(name, f"scene.{g}.pbrt", f"pbrt-{g}") for g in groups]
    B.wait(logs)
    B.pull(name, ["x.exr", "x.json", "x.albedo.exr", "x.normal.exr"] + [f"x.{g}.exr" for g in groups]
           + [f"pbrt.{g}.exr" for g in groups], out)


if __name__ == "__main__":
    main()
