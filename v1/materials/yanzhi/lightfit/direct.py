"""胭脂红 card, S8 r2: one direct render per variant (no mixing of light groups, no interpolation between sweeps),
denoised once, measured as card.py measures (docs/materials/yanzhi.md, round 3).

Round 2's sheet was four renders weighted by group and interpolated between a grey and a white sweep [A], each
undenoised; the judges saw the noise. Here every variant is one Cycles render of the whole rig, its sweep's
reflectance patched into the staged rig (optics/backdrops.json has no 0.5 paper; the patch is this script's, the
value [F] from lightfit/clean.py), optionally the sweep's floor cut short in front of the bowl (beyond it nothing:
a dark studio), then OIDN once (tools/build.py's denoise, with the render's albedo and normal).

    python3 -I materials/yanzhi/lightfit/direct.py queue NAME --object out/materials/yanzhi/card/craft-c050/bowl.pbrt
            [--rig materials/yanzhi/recipes/rig_met_fit2.json] [--rho 0.51] [--floor-cut-mm 300] [--spp 1024]
            [--sheen-floor 0.2,1.5] [--lane gpu]   # stage, push, queue; returns at once
    python3 -I materials/yanzhi/lightfit/direct.py finish NAME [--c 0.5]   # wait, pull, denoise, measure
Out: out/s8/yanzhi/r2/render/NAME/ (x.exr raw, x.dn.exr denoised, card_measure.json from the denoised image).
"""
import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
import build  # noqa: E402
import rgbscene  # noqa: E402

OUT = os.path.join(ROOT, os.environ.get("YZ_RENDER_OUT", "out/s8/yanzhi/r2/render"))   # S8 r3: YZ_RENDER_OUT=out/s8/yanzhi/r3/render
CAMERA = {"focal_mm": 100, "f_number": 11, "azimuth_deg": 0, "elevation_deg": 14, "fill": 0.57, "aim": "centre",
          "why": "as the round-1/2 cards: the photo's view, 14 degrees up (rim ellipse 0.25 [M]), bowl 57% of the frame's height [M]; 100 mm our choice"}
DEVELOP = {"sensor": "canon_eos_5d_mkiv", "iso": 100,
           "expose": {"percentile": 99.0, "of_saturation": 0.75, "why": "our choice"},
           "develop": {"ev": 0.0, "shoulder_from": 0.6, "contrast": 1.0, "pivot": 0.18, "why": "neutral"},
           "sharpen": {"amount": 0.0, "sigma_px": 0.7}, "seed": 1}


def read_ply(path):
    with open(path, "rb") as f:
        head = []
        while True:
            line = f.readline().decode().strip()
            head.append(line)
            if line == "end_header":
                break
        nv = int([l for l in head if l.startswith("element vertex")][0].split()[-1])
        nprop = sum(1 for l in head if l.startswith("property float"))
        V = np.frombuffer(f.read(nv * nprop * 4), "<f4").reshape(nv, nprop).copy()
        rest = f.read()
    return head, V, rest


def cut_floor(out, cut_mm):
    """The sweep's first profile row (the floor's front edge, behind the camera) moved to cut_mm in front of the
    bowl's centre: the floor then ends there (beyond: nothing, black)."""
    p = os.path.join(out, "backdrop.ply")
    head, V, rest = read_ply(p)
    b = json.load(open(os.path.join(out, "build.json")))
    front = np.array(b["camera"].get("front", [0.0, -1.0, 0.0])) if isinstance(b.get("camera"), dict) else np.array([0, -1.0, 0])
    i = np.argsort(V[:, :3] @ front)[::-1][:2]          # the two vertices farthest towards the camera
    d = V[i, :3] @ front
    V[i, :3] -= np.outer(d - cut_mm, front)
    with open(p, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.astype("<f4").tobytes())
        f.write(rest)
    return float(d.min())


def queue(a):
    recipe = {"about": f"yanzhi S8 r2 direct render {a.name}", "object": {"file": a.object}, "rig": a.rig,
              "camera": CAMERA, "render": {"spp": a.spp, "maxdepth": 48, "refractivenee": True, "denoise": True,
                                           "seed": 0}, "mix": {}, "develop": DEVELOP, "sheet": {"stops": 1}}
    out = os.path.join(OUT, a.name)
    os.makedirs(out, exist_ok=True)
    json.dump(recipe, open(os.path.join(out, "recipe.json"), "w"), indent=1)
    build.stage(recipe, out, tuple(int(x) for x in a.res.split("x")), a.spp)
    note = {"rho": a.rho, "floor_cut_mm": a.floor_cut_mm}
    if a.rho is not None:
        for f in os.listdir(out):
            if f.startswith("rig") and f.endswith(".pbrt"):
                p = os.path.join(out, f)
                s = open(p).read()
                s2, n = re.subn(r'(# backdrop: .*\nAttributeBegin\n  Material "diffuse" "spectrum reflectance" )\[ 360 [0-9.]+ 830 [0-9.]+ \]',
                                lambda m: m.group(1) + f"[ 360 {a.rho:g} 830 {a.rho:g} ]", s)
                if n != 1:
                    raise SystemExit(f"{p}: backdrop line not found")
                open(p, "w").write(s2)
    if a.floor_cut_mm:
        note["floor_front_was_mm"] = cut_floor(out, a.floor_cut_mm)
    if a.sheen_floor:
        # a test of the sweep's sheen (S8 r2): in front of the foot (y < -45 mm, the camera on -Y), a darker diffuse
        # patch 0.02 mm above the sweep under a smooth thin dielectric sheet 0.05 mm above it: a paper whose
        # diffuse albedo is rho but which shines at grazing (Fresnel of eta); the rest of the sweep unchanged
        rho_f, eta_f = (float(x) for x in a.sheen_floor.split(","))
        quad = lambda z: (f'Shape "bilinearmesh" "point3 P" [ -600 -1400 {z} 600 -1400 {z} -600 -45 {z} 600 -45 {z} ] '
                          f'"integer indices" [ 0 1 2 3 ]')
        add = ("# S8 r2 test: a sheen floor in front of the bowl (lightfit/direct.py --sheen-floor)\nAttributeBegin\n"
               f'  Material "diffuse" "spectrum reflectance" [ 360 {rho_f:g} 830 {rho_f:g} ]\n  {quad(0.02)}\nAttributeEnd\n'
               f'AttributeBegin\n  Material "thindielectric" "float eta" [ {eta_f:g} ]\n  {quad(0.05)}\nAttributeEnd\n')
        for f in os.listdir(out):
            if f.startswith("rig") and f.endswith(".pbrt"):
                with open(os.path.join(out, f), "a") as fh:
                    fh.write(add)
        note["sheen_floor"] = {"rho": rho_f, "eta": eta_f}
    if a.coat_sweep:
        # S8 r3: a paper with a rough sheen: the whole sweep's diffuse (--rho) under a rough dielectric sheet 0.05 mm
        # above it (the sweep's mesh moved along its normals), GGX alpha as given [A]: a coated diffuse with the
        # coat's internal reflections, as the bowl's glaze over its body (no medium: an open sheet is right here)
        eta_c, al = (float(x) for x in a.coat_sweep.split(","))
        head, Vb, rest = read_ply(os.path.join(out, "backdrop.ply"))
        Vc = Vb.copy()
        Vc[:, :3] += 0.05 * Vc[:, 3:6]
        with open(os.path.join(out, "backdrop_coat.ply"), "wb") as fh:
            fh.write(("\n".join(head) + "\n").encode())
            fh.write(Vc.astype("<f4").tobytes())
            fh.write(rest)
        add = ("# S8 r3 test: the sweep's rough sheen (lightfit/direct.py --coat-sweep)\nAttributeBegin\n"
               f'  Material "dielectric" "float eta" [ {eta_c:g} ] "float roughness" [ {al:g} ] "bool remaproughness" false\n'
               '  Shape "plymesh" "string filename" [ "backdrop_coat.ply" ]\nAttributeEnd\n')
        for f in os.listdir(out):
            if f.startswith("rig") and f.endswith(".pbrt"):
                with open(os.path.join(out, f), "a") as fh:
                    fh.write(add)
        note["coat_sweep"] = {"eta": eta_c, "alpha": al}
    b = json.load(open(os.path.join(out, "build.json")))
    K = 5500.0
    sc = rgbscene.convert(os.path.join(out, "scene.pbrt"), build.SENSOR, K)
    json.dump(sc, open(os.path.join(out, "scene.cycles.json"), "w"), indent=1)
    rname = os.environ.get("YZ_REMOTE_PREFIX", "yz-r2-") + a.name
    build.push(out, rname)
    log = build.queue_cycles(rname, a.lane, "~/gewu-render/tools", f"--spp {a.spp} --seed 0")
    json.dump({"remote": rname, "log": log, "groups": b["groups"], **note}, open(os.path.join(out, "queued.json"), "w"), indent=1)
    print("queued", rname, log, note)


def finish(a):
    import card
    out = os.path.join(OUT, a.name)
    q = json.load(open(os.path.join(out, "queued.json")))
    build.wait([q["log"]])
    files = ["x.exr", "x.json", "x.albedo.exr", "x.normal.exr"] + [f"x.{g}.exr" for g in q["groups"]]
    build.pull(q["remote"], files, out)
    from camera import read_raw
    raw = read_raw(os.path.join(out, "x.exr"))
    build.write_pfm(os.path.join(out, "x.pfm"), raw)
    build.denoise([(os.path.join(out, "x.pfm"), os.path.join(out, "x.dn.exr"))],
                  os.path.join(out, "x.albedo.exr"), os.path.join(out, "x.normal.exr"))
    ns = argparse.Namespace(dir=out, raw="x.dn.exr", tag="", c=a.c)
    card.measure(ns)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("queue")
    q.add_argument("name")
    q.add_argument("--object", required=True)
    q.add_argument("--rig", default="materials/yanzhi/recipes/rig_met_fit2.json")
    q.add_argument("--rho", type=float, default=0.51)
    q.add_argument("--floor-cut-mm", type=float)
    q.add_argument("--sheen-floor", help="RHO,ETA: a test floor in front of the bowl (darker diffuse under a smooth sheet)")
    q.add_argument("--spp", type=int, default=1024)
    q.add_argument("--res", default="960x540")
    q.add_argument("--coat-sweep", help="ETA,ALPHA: the whole sweep under a rough dielectric sheet (S8 r3)")
    q.add_argument("--lane", default="gpu", choices=sorted(build.LANES))
    f = sub.add_parser("finish")
    f.add_argument("name")
    f.add_argument("--c", type=float)
    a = ap.parse_args()
    {"queue": queue, "finish": finish}[a.cmd](a)


if __name__ == "__main__":
    main()
