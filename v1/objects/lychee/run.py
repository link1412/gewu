"""tools/build.py's flow for a lychee recipe, with one step added: the Cycles scene's coefficients of the media
whose absorption is steep inside a camera channel are replaced by albedo-matched ones
(materials/lychee/optics.py channel_media; the pbrt scenes keep the spectra, so --pbrt is the spectral reference).

    python3 -I objects/lychee/run.py RECIPE.json --preview|--check|--remix|--stage-only [build.py's options]

The recipe is build.py's, plus "material_set" (materials/lychee/material.json: leidus, guiwei) and optionally
"focus_stack": {"slice_f_number": N}: the camera's f_number is then only the render's depth of field, and optics.json
(the camera chain's diffraction) gets the slice's N.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "materials/lychee"))
import build as BLD  # noqa: E402
import rgbscene  # noqa: E402
import optics as LO  # noqa: E402


def patch(out, which, K):
    path = os.path.join(out, "scene.cycles.json")
    sc = json.load(open(path))
    sen = rgbscene.Sensor(BLD.SENSOR, K)
    cm = LO.channel_media(which, sen)
    done = {}
    for name, m in sc["media"].items():
        part = name[len("lychee_"):] if name.startswith("lychee_") else None
        if part in cm:
            m.update({k: cm[part][k] for k in ("sigma_a_per_m", "sigma_s_per_m", "g")})
            m["note"] = ("sigma_a per channel albedo-matched (materials/lychee/optics.py channel_media); rgbscene's "
                         f"channel average was {[round(x, 1) for x in cm[part]['averaged_sigma_a_per_m']]} /m")
            done[name] = [round(x, 1) for x in m["sigma_a_per_m"]]
    json.dump(sc, open(path, "w"), indent=1)
    print("albedo-matched sigma_a /m:", done)


def stack(out, recipe):
    """A focus stack: the render's lens stops down for depth (the recipe's f_number), the diffraction is one slice's."""
    fs = recipe.get("focus_stack")
    if not fs:
        return
    path = os.path.join(out, "optics.json")
    o = json.load(open(path))
    o["rendered_f_number"] = o["f_number"]
    o["f_number"] = fs["slice_f_number"]
    o["note"] = "focus stack (the recipe's focus_stack): diffraction at the slice's f-number, depth of field from the render's"
    json.dump(o, open(path, "w"), indent=1)
    print(f"focus stack: rendered at f/{o['rendered_f_number']:g}, diffracted at f/{o['f_number']:g}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recipe")
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--preview", action="store_true")
    m.add_argument("--check", action="store_true")
    m.add_argument("--remix", action="store_true")
    m.add_argument("--stage-only", action="store_true")
    ap.add_argument("--spp", type=int)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--res", help="WxH instead of the preview/check sizes")
    ap.add_argument("--lane", default="cycles", choices=sorted(BLD.LANES))
    ap.add_argument("--remote-tools", default="~/gewu-render/tools")
    ap.add_argument("--pbrt", action="store_true")
    ap.add_argument("--pbrt-spp", type=int)
    ap.add_argument("--no-diffraction", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    recipe = json.load(open(a.recipe))
    name = os.path.splitext(os.path.basename(a.recipe))[0]
    out = a.out or os.path.join(ROOT, "out/recipes", name)
    if a.remix:
        BLD.remix(out, recipe, not a.no_diffraction)
        return
    res = tuple(int(x) for x in a.res.split("x")) if a.res else (960, 540) if a.check else (480, 270)
    render = recipe.get("render", {})
    spp = a.spp or render.get("spp", 128)
    groups = BLD.stage(recipe, out, res, spp)
    K = BLD.studio.load(BLD.rel(recipe["rig"]))["spectrum"]["blackbody_K"]
    patch(out, recipe["material_set"], K)
    stack(out, recipe)
    if a.stage_only:
        return
    BLD.push(out, name)
    seed = a.seed if a.seed is not None else render.get("seed", 0)
    logs = [BLD.queue_cycles(name, a.lane, a.remote_tools, f"--spp {spp} --seed {seed}")]
    if a.pbrt:
        ps = a.pbrt_spp or spp
        logs += [BLD.queue_pbrt(name, f"scene.{g}.pbrt", f"pbrt-{g}", f"--spp {ps} --seed {seed}") for g in groups]
    BLD.wait(logs)
    files = ["x.exr", "x.json", "x.albedo.exr", "x.normal.exr"] + [f"x.{g}.exr" for g in groups]
    if a.pbrt:
        files += [f"pbrt.{g}.exr" for g in groups]
    BLD.pull(name, files, out)
    BLD.remix(out, recipe, not a.no_diffraction)


if __name__ == "__main__":
    main()
