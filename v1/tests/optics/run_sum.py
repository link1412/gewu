"""Test a, the runs: do the groups add up to the whole? On the GPU only (same-seed comparisons need one device).

    python3 -I tests/optics/run_sum.py [--spp 64] [--ref-spp 4096] [--remote-tools DIR]

Stages tests/optics/recipes/vase-product_three.json (S3's numbers in docs/optics.md were taken with the rig's first
version: three groups, key, rim, bg) into out/optics/sum/, plus two
variants of its rig written by optics/studio.py:
- scene.all: the same lamps with no group tags (the old one-image path of tools/cycles_scene.py);
- scene.k2: the key lamp's illuminance doubled (its luminance x2), tagged.
Renders (480x270): the grouped scene at seeds 1 and 2; scene.all at seeds 1 and 2; scene.k2 at seed 1; and for
test d (check_denoise.py) scene.all at --ref-spp, seed 7 (ref.exr), and the grouped render's albedo and normal.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
import build as B  # noqa: E402
import rgbscene  # noqa: E402
import studio  # noqa: E402

OUT = os.path.join(ROOT, "out/optics/sum")
NAME = "optics-sum"


def variant(out, recipe, tag, overrides=None, tags=True):
    """Write rig.<tag>.pbrt and scene.<tag>.pbrt (scene.pbrt with that rig) and its Cycles JSON."""
    b = json.load(open(os.path.join(out, "build.json")))
    lo, hi = (B.np.array(x) for x in b["box_mm"])
    rig = studio.load(B.rel(recipe["rig"]))
    cam = studio.Camera(recipe["camera"], lo, hi, b["res"])
    st = studio.Studio(rig, lo, hi, cam, {**recipe.get("rig_overrides", {}), **(overrides or {})})
    st.write(os.path.join(out, f"rig.{tag}.pbrt"), tags=tags)
    text = open(os.path.join(out, "scene.pbrt")).read().replace('Include "rig.pbrt"', f'Include "rig.{tag}.pbrt"')
    open(os.path.join(out, f"scene.{tag}.pbrt"), "w").write(text)
    sc = rgbscene.convert(os.path.join(out, f"scene.{tag}.pbrt"), B.SENSOR, rig["spectrum"]["blackbody_K"])
    json.dump(sc, open(os.path.join(out, f"scene.{tag}.cycles.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--ref-spp", type=int, default=4096)
    ap.add_argument("--remote-tools", default="~/gewu-render/tools-test-optics")
    a = ap.parse_args()
    recipe = json.load(open(os.path.join(HERE, "recipes/vase-product_three.json")))
    groups = B.stage(recipe, OUT, (480, 270), a.spp)
    key = next(l for l in studio.load(B.rel(recipe["rig"]))["lamps"] if l["group"] == "key")
    variant(OUT, recipe, "all", tags=False)
    variant(OUT, recipe, "k2", {"lamps.key.lux": 2 * key["lux"]})
    B.push(OUT, NAME)
    q = lambda js, out, seed, tag: B.queue_cycles(NAME, "gpu", a.remote_tools, f"--spp {a.spp} --seed {seed}",
                                                  out_exr=out, tag=tag, scene_json=js)
    logs = [q("scene.cycles.json", "g1.exr", 1, "-g1"), q("scene.cycles.json", "g2.exr", 2, "-g2"),
            q("scene.all.cycles.json", "all1.exr", 1, "-all1"), q("scene.all.cycles.json", "all2.exr", 2, "-all2"),
            q("scene.k2.cycles.json", "k2.exr", 1, "-k2"),
            B.queue_cycles(NAME, "gpu", a.remote_tools, f"--spp {a.ref_spp} --seed 7", out_exr="ref.exr", tag="-ref",
                           scene_json="scene.all.cycles.json")]
    B.wait(logs)
    files = [f"{s}.exr" for s in ("g1", "g2", "all1", "all2", "k2", "ref")] + [f"{s}.json" for s in ("g1", "all1", "k2", "ref")]
    files += ["g1.albedo.exr", "g1.normal.exr"]
    files += [f"{s}.{g}.exr" for s in ("g1", "g2", "k2") for g in groups]
    B.pull(NAME, files, OUT)


if __name__ == "__main__":
    main()
