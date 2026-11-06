"""The glaze-slab variants that settle which renderer is right (docs/slab.md): the Guan repro
(out/materials/guan_glaze/lt/t_bulk_grey: a glaze 1.2 mm thick over a body, two soft boxes), one change at a time.
Writes out/ru/lt/<variant>/scene.pbrt with its meshes at 96 x 54, full frame. The glaze is a closed box (tools/shell.py)
200 x 200 mm unless the variant says "sheet" (the open quad of the repro, 36 x 22 mm, which Cycles renders dark): the
frame (30 x 17 mm) sees only the slab, and on a laterally infinite slab under distant lights every pixel is the
same, so the mean over the frame's middle is the number compared (tests/slab/table.py), against tools/slab.py's
Monte Carlo of the same slab.

    python3 -I tests/slab/variants.py write [--spp 1024]      # scenes
    python3 -I tests/slab/variants.py mc [--only A_base,...]  # the Monte Carlo reference for each, JSON
    python3 -I tests/slab/variants.py refs [--only mirror,...] # the references of the Cycles probes (PROBES), JSON
    python3 -I tests/slab/variants.py queue                   # the probes as lines of a GPU queue script

The Monte Carlo has the variant's surface: smooth, or rough with the same GGX alpha as pbrt's rough dielectric
(A_nornee, and Cycles' GGX glass for both A variants). pbrt's RNEE (A_base) treats the transmission as smooth
(docs/rnee.md), so A_base against the Monte Carlo is the error of that approximation.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import shell  # noqa: E402
import slab  # noqa: E402

OUT = os.path.join(ROOT, "out/ru/lt")
L1 = [(-352.6686, 140.5365, 233.3975), (-140.5365, 352.6686, 233.3975), (-179.4635, -32.6686, 406.6025),
      (32.6686, 179.4635, 406.6025)]
L2 = [(445.6125, -34.1294, 239.0913), (239.8142, -377.1266, 239.0913), (160.1858, 137.1266, 460.9087),
      (-45.6125, -205.8706, 460.9087)]
BASE = dict(n=1.5, alpha=0.0307, d=1.2, ss=2.5, sa=0.03, g=0.7, rho=0.12, rnee=True, shell="box", half=100.0,
            film=None, body=True, bottom=None, own_ref=True)
VARIANTS = {
    "A_base": {},
    "A_nornee": {"rnee": False},
    "B_smooth": {"alpha": 0.0},
    "B_smooth_sheet": {"alpha": 0.0, "shell": "sheet", "half": None},
    "C_smooth_g0": {"alpha": 0.0, "g": 0.0},
    "D_smooth_n1": {"alpha": 0.0, "n": 1.0},
    "E_smooth_black": {"alpha": 0.0, "rho": 0.0},
    "F_smooth_noscat": {"alpha": 0.0, "ss": 0.0},
    "G_n1_g0": {"alpha": 0.0, "n": 1.0, "g": 0.0},
    "H_n1_g0_sa0": {"alpha": 0.0, "n": 1.0, "g": 0.0, "sa": 0.0},
    # a horizontal air film (pbrt's thindielectric, eta 1/n) in the glaze: the thin cracks' "dark line" question
    "I_film": {"alpha": 0.0, "film": 0.6},
    "I_film_nornee": {"alpha": 0.0, "film": 0.6, "rnee": False},
    # the glaze box 0.6 mm deep and no body: with the Cycles probe boxmirror=1 its bottom is a mirror (pbrt: glass)
    "J_boxmirror": {"alpha": 0.0, "body": False, "bottom": 0.6, "own_ref": False},
    # the film variant with one more change, for the probes only (own_ref False: their references are in REFS)
    "K_film_noscat": {"alpha": 0.0, "film": 0.6, "ss": 0.0, "own_ref": False},
    "L_film_n1": {"alpha": 0.0, "film": 0.6, "n": 1.0, "own_ref": False},
    "M_film_g0": {"alpha": 0.0, "film": 0.6, "g": 0.0, "own_ref": False},
}
# The Cycles probes (tests/slab/cycles_probe.py, docs/slab.md): (label, variant, GEWU_PROBE, reference, reference at
# 64 vertices). Each changes one thing; the reference is the slab Monte Carlo of what that render should be (REFS;
# "mc:<variant>" is the variant's own, from mc.json), unlimited and with Cycles' 64 bounces (max_vertices 64; None
# where the render has 1024 or the paths are short). Cycles does not count a pass through a transparent closure as
# a bounce, the reference counts every meeting with a film: for a film that transmits, Cycles lies between the two.
_S = (2.5, 0.03, 0.7)
REFS = {
    "film64": dict(layers=[(0.6, *_S), (0.6, *_S)], films={0: 1 / 1.5}, max_vertices=64),
    "mirror": dict(layers=[(0.6, *_S), (0.6, *_S)], films={0: ("R", 1.0)}),
    "mirror64": dict(layers=[(0.6, *_S), (0.6, *_S)], films={0: ("R", 1.0)}, max_vertices=64),
    "half": dict(layers=[(0.6, *_S), (0.6, *_S)], films={0: ("R", 0.5)}),
    "white": dict(layers=[(0.6, *_S)], rho=1.0),
    "white64": dict(layers=[(0.6, *_S)], rho=1.0, max_vertices=64),
    "half64": dict(layers=[(0.6, *_S), (0.6, *_S)], films={0: ("R", 0.5)}, max_vertices=64),
    "mirror12_64": dict(layers=[(1.2, *_S), (0.05, *_S)], films={0: ("R", 1.0)}, max_vertices=64),
    "mirror12": dict(layers=[(1.2, *_S), (0.05, *_S)], films={0: ("R", 1.0)}),
    "half_noscat": dict(layers=[(0.6, 0.0, 0.03, 0.7), (0.6, 0.0, 0.03, 0.7)], films={0: ("R", 0.5)}),
    "mirror_n1": dict(n=1.0, layers=[(0.6, *_S), (0.6, *_S)], films={0: ("R", 1.0)}),
    "mirror_g0": dict(layers=[(0.6, 2.5, 0.03, 0.0), (0.6, 2.5, 0.03, 0.0)], films={0: ("R", 1.0)}),
    "mirror_n1_64": dict(n=1.0, layers=[(0.6, *_S), (0.6, *_S)], films={0: ("R", 1.0)}, max_vertices=64),
    "mirror_g0_64": dict(layers=[(0.6, 2.5, 0.03, 0.0), (0.6, 2.5, 0.03, 0.0)], films={0: ("R", 1.0)},
                         max_vertices=64),
}
PROBES = [
    # before the fix: the Glossy BSDF at Blender's default Color 0.8 (gcol=0.8), in the adapter's thin dielectric
    # and in the probes' mirrors
    ("film (the adapter's thin dielectric), Glossy 0.8", "I_film", "gcol=0.8", "mc:I_film", "film64"),
    ("film, transparent", "I_film", "thin=transparent", "mc:B_smooth", None),
    ("film, mix 0.5, Glossy 0.8", "I_film", "thin=mixhalf,gcol=0.8", "half", "half64"),
    ("mirror film, Glossy 0.8", "I_film", "thin=glossy,gcol=0.8", "mirror", "mirror64"),
    ("  + bounces 1024", "I_film", "thin=glossy,gcol=0.8,maxb=1024", "mirror", None),
    ("  + no light tree", "I_film", "thin=glossy,gcol=0.8,tree=0", "mirror", "mirror64"),
    ("  + distance sampling", "I_film", "thin=glossy,gcol=0.8,vsamp=DISTANCE", "mirror", "mirror64"),
    ("  + biased volume (ray marching)", "I_film", "thin=glossy,gcol=0.8,vbias=1", "mirror", "mirror64"),
    ("  + GGX roughness 0.05", "I_film", "thin=glossy,gcol=0.8,rough=0.05", "mirror", "mirror64"),
    ("  + Beckmann", "I_film", "thin=glossy,gcol=0.8,dist=BECKMANN", "mirror", "mirror64"),
    ("mirror body (1.2 mm), Glossy 0.8", "B_smooth", "body=glossy,gcol=0.8", "mirror12", "mirror12_64"),
    ("mirror bottom of the glaze box, Glossy 0.8", "J_boxmirror", "boxmirror=1,gcol=0.8", "mirror", "mirror64"),
    ("mirror film, Metallic BSDF (white)", "I_film", "thin=metal", "mirror", "mirror64"),
    ("white diffuse film", "I_film", "thin=diffuse", "white", "white64"),
    # after: white
    ("film (the adapter's thin dielectric)", "I_film", "", "mc:I_film", "film64"),
    ("film, mix 0.5", "I_film", "thin=mixhalf", "half", "half64"),
    ("mirror film", "I_film", "thin=glossy", "mirror", "mirror64"),
    ("  + bounces 1024", "I_film", "thin=glossy,maxb=1024", "mirror", None),
    ("mirror body (1.2 mm)", "B_smooth", "body=glossy", "mirror12", "mirror12_64"),
    ("mirror bottom of the glaze box", "J_boxmirror", "boxmirror=1", "mirror", "mirror64"),
    ("film mix 0.5, no scattering", "K_film_noscat", "thin=mixhalf", "half_noscat", None),
    ("mirror film, top n = 1", "L_film_n1", "thin=glossy", "mirror_n1", "mirror_n1_64"),
    ("mirror film, g = 0", "M_film_g0", "thin=glossy", "mirror_g0", "mirror_g0_64"),
]
SHEET = (18.0, 11.0)          # the repro's open tile


def probe_slug(probe):
    """The render's file name for a probe string: probe-<key>-<value>_..., probe-default for none."""
    return "probe-" + ("_".join(kv.replace("=", "-") for kv in probe.split(",")) if probe else "default")


def params(name):
    return {**BASE, **VARIANTS[name]}


def scene(p, spp):
    q = lambda P: " ".join(f"{c:.4f}" for v in P for c in v)
    rn = "true" if p["rnee"] else "false"
    return f"""# glaze-slab variant (tests/slab/variants.py): {json.dumps(p)}
LookAt 0 0 300.0 0 0 0  0 1 0
Camera "perspective" "float fov" [ 3.199057 ]
Sampler "zsobol" "integer pixelsamples" [ {spp} ]
Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" {rn}
Film "rgb" "integer xresolution" [ 96 ] "integer yresolution" [ 54 ] "string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true
WorldBegin
AttributeBegin
  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 1.0 ]
  Material "diffuse" "rgb reflectance" [ 0 0 0 ]
  Shape "bilinearmesh" "point3 P" [ {q(L1)} ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
AttributeBegin
  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 0.35 ]
  Material "diffuse" "rgb reflectance" [ 0 0 0 ]
  Shape "bilinearmesh" "point3 P" [ {q(L2)} ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" [ 360 {p['sa']} 830 {p['sa']} ] "spectrum sigma_s" [ 360 {p['ss']} 830 {p['ss']} ] "float g" [ {p['g']} ] "float scale" [ 1 ]
AttributeBegin
  Material "diffuse" "spectrum reflectance" [ 360 0.58 830 0.58 ]
  Shape "bilinearmesh" "point3 P" [ -200 -200 -3.0 200 -200 -3.0 -200 200 -3.0 200 200 -3.0 ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
AttributeBegin
  MediumInterface "glaze" ""
  Material "dielectric" "float eta" [ {p['n']} ] "float roughness" [ {p['alpha']} ] "bool remaproughness" false "bool refractivenee" {rn}
  Shape "plymesh" "string filename" [ "outer.ply" ]
AttributeEnd
""" + ("" if not p["body"] else f"""AttributeBegin
  MediumInterface "" "glaze"
  Material "diffuse" "spectrum reflectance" [ 360 {p['rho']} 830 {p['rho']} ]
  Shape "plymesh" "string filename" [ "body.ply" ]
AttributeEnd
""") + ("" if p["film"] is None else f"""AttributeBegin
  MediumInterface "glaze" "glaze"
  Material "thindielectric" "float eta" [ {1 / p['n']:.6f} ]
  Shape "plymesh" "string filename" [ "film.ply" ]
AttributeEnd
""")


def write_ply(path, P, N, T):
    P, N, T = np.asarray(P, "<f4"), np.asarray(N, "<f4"), np.asarray(T, "<i4")
    head = (f"ply\nformat binary_little_endian 1.0\nelement vertex {len(P)}\nproperty float x\nproperty float y\n"
            f"property float z\nproperty float nx\nproperty float ny\nproperty float nz\nelement face {len(T)}\n"
            f"property list uchar int vertex_indices\nend_header\n")
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"], face["i"] = 3, T
    with open(path, "wb") as f:
        f.write(head.encode())
        f.write(np.ascontiguousarray(np.concatenate([P, N], 1)).tobytes())
        f.write(face.tobytes())


def quad(hx, hy, z, up=True):
    P = [(-hx, -hy, z), (hx, -hy, z), (hx, hy, z), (-hx, hy, z)]
    return P, [(0, 0, 1 if up else -1)] * 4, [(0, 1, 2), (0, 2, 3)] if up else [(0, 2, 1), (0, 3, 2)]


def main():
    cmd = sys.argv[1]
    spp = int(sys.argv[sys.argv.index("--spp") + 1]) if "--spp" in sys.argv else 1024
    if cmd == "write":
        for name in VARIANTS:
            p = params(name)
            d = os.path.join(OUT, name)
            os.makedirs(d, exist_ok=True)
            hx, hy = (p["half"], p["half"]) if p["shell"] == "box" else SHEET
            if p["shell"] == "box":
                zb = -p["bottom"] if p["bottom"] is not None else -p["d"] - 0.05     # just below the body
                P, N, T, _ = shell.box(hx, hy, 0.0, zb)
            else:
                P, N, T = quad(hx, hy, 0.0)
            write_ply(os.path.join(d, "outer.ply"), P, N, T)
            write_ply(os.path.join(d, "body.ply"), *quad(hx, hy, -p["d"]))
            if p["film"] is not None:                                   # inside the box, clear of its sides
                write_ply(os.path.join(d, "film.ply"), *quad(hx - 1.0, hy - 1.0, -p["film"]))
            with open(os.path.join(d, "scene.pbrt"), "w") as f:
                f.write(scene(p, spp))
        print(f"{len(VARIANTS)} variants in {OUT}")
    elif cmd == "mc":
        path = os.path.join(OUT, "mc.json")
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(VARIANTS)
        res = json.load(open(path)) if os.path.exists(path) and "--only" in sys.argv else {}
        for name in only:
            p = params(name)
            if not p["own_ref"]:
                continue
            if p["film"] is None:
                layers, films = [(p["d"], p["ss"], p["sa"], p["g"])], None
            else:
                layers = [(p["film"], p["ss"], p["sa"], p["g"]), (p["d"] - p["film"], p["ss"], p["sa"], p["g"])]
                films = {0: 1.0 / p["n"]}
            r = slab.run(p["n"], layers, p["rho"], 1.0, nphot=2_000_000, seed=11, lights=[("L1", L1), ("L2", L2)],
                         light_scale={"L1": 1.0, "L2": 0.35}, alpha=p["alpha"], films=films)
            v = r["pixel"]
            res[name] = {"pixel_over_E1": v, "pixel_se": r["pixel_se"], "R_diffuse": r["R_diffuse"],
                         "R_diffuse_se": r["R_diffuse_se"], "alpha_in_mc": p["alpha"]}
            print(f"{name:18s} pixel/E1 {v:.5f} +- {r['pixel_se']:.5f}  (R_diffuse {r['R_diffuse']:.5f} +- {r['R_diffuse_se']:.5f})")
        with open(path, "w") as f:
            json.dump({k: res[k] for k in VARIANTS if k in res}, f, indent=1)
    elif cmd == "refs":
        path = os.path.join(OUT, "mc_probes.json")
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(REFS)
        res = json.load(open(path)) if os.path.exists(path) else {}
        for key in only:
            kw = {**dict(n=1.5, rho=0.12, films=None, max_vertices=None), **REFS[key]}
            r = slab.run(kw["n"], kw["layers"], kw["rho"], 1.0, nphot=2_000_000, seed=13,
                         lights=[("L1", L1), ("L2", L2)], light_scale={"L1": 1.0, "L2": 0.35}, films=kw["films"],
                         max_vertices=kw["max_vertices"])
            res[key] = {"pixel_over_E1": r["pixel"], "pixel_se": r["pixel_se"], "spec": repr(REFS[key])}
            print(f"{key:10s} pixel/E1 {r['pixel']:.5f} +- {r['pixel_se']:.5f}")
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
    elif cmd == "queue":                    # a bash script: one GPU render after another
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
        print("#!/bin/bash\n# Cycles probes (tests/slab/variants.py queue): one after another through mini-gpu.sh\n"
              "run() {\n  D=$HOME/gewu-render/scenes/ru1-$1; cd $D\n"
              "  rm -f /tmp/gewu-ru1-$1-$3.log; GEWU_PROBE=\"$2\" ~/gewu-render/bin/mini-gpu.sh /tmp/gewu-ru1-$1-$3.log -b --factory-startup "
              "--python-exit-code 1 -P $HOME/gewu-render/tools/cycles_probe.py -- scene.cycles.json --spp 16384 "
              "--out $D/$3.exr < /dev/null > /dev/null 2>&1\n}")
        for label, var, probe, *_ in PROBES:
            if only is None or probe_slug(probe) in only:
                print(f'run {var} "{probe}" {probe_slug(probe)}    # {label}')
        print("echo all done > /tmp/gewu-ru1-probes.done")


if __name__ == "__main__":
    main()
