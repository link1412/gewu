"""Steep air films in the glaze slab, the minimal scene for the Guan card's crack lines in Cycles against pbrt
(docs/slab.md, "裂缝"). The slab of tests/slab/variants.py's B_smooth (a closed glaze box, smooth top of index 1.5,
1.2 mm, sigma_s 2.5/mm, sigma_a 0.03/mm, g 0.7, body 0.12, the two soft boxes, the same camera) with a row of parallel
crack planes along y, one every PERIOD_PX pixel columns, from 1 um under the surface to 1 um above the body, as
crafts/crackle/faces.py builds them (leaning `tilt` deg from the normal; thindielectric eta 1/1.5, MediumInterface
glaze glaze), optionally with the card's deposit (a diffuse prism in the plane from just above the surface down to
`dep` mm, as faces.channels). The slab Monte Carlo is one-dimensional: pbrt is the judge here (it matched the slab
reference on every film so far, docs/slab.md).

    python3 -I tests/slab/vfilm.py write                # out/ru/vf/<variant>/ (scene.pbrt, meshes, scene.cycles.json)
    python3 -I tests/slab/vfilm.py queue [v1,v2] > q.sh # the queue
    python3 -I tests/slab/vfilm.py table                # after fetching <variant>/{pbrt,cyc}.exr

The number compared: the frame folded by the films' period (columns mod PERIOD_PX), averaged over rows and the
three channels, over the key light's sensor RGB (as tests/slab/table.py); per phase bin and over the period.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import shell  # noqa: E402
import variants as V  # noqa: E402

OUT = os.path.join(ROOT, "out/ru/vf")
RES = (192, 108)
FOV = 3.199057                       # the short side (y): 16.76 mm at 300 mm
FRAME_H = 2 * 300.0 * math.tan(math.radians(FOV / 2))
PX = FRAME_H / RES[1]                # mm per pixel
PERIOD_PX = 16
BASE = dict(tilt=0.0, dep=None, dep_w=0.012, proud=0.001, inset=0.001, alpha=0.0, d=1.2, films=True, eta=1 / 1.5,
            normals=True, rnee=True, cols=None, half_y=30.0)
VARIANTS = {
    "v0_nofilm": {"films": False},
    "v1_vert": {},
    "v2_t15": {"tilt": 15.0},
    "v3_t15_dep": {"tilt": 15.0, "dep": 0.4},
    # vertical films: the period's mean must equal the slab's without films (an exact check, Cycles alone; see docs)
    "v1_flat": {"normals": False},
    "v1_cols": {"cols": 0.04},
    "v1_short": {"half_y": 10.0},
    "v0_rough": {"films": False, "alpha": 0.0307},
    "v1_rough": {"alpha": 0.0307},
}
SPP = {"pbrt": 256, "cycles": 4096}


def params(name):
    return {**BASE, **VARIANTS[name]}


def films_x():
    """The planes' x at the surface: one per PERIOD_PX columns, on a column's centre, across the frame and 2 mm beyond."""
    w = PX * RES[0]
    k = np.arange(-int(w / 2 / (PERIOD_PX * PX)) - 2, int(w / 2 / (PERIOD_PX * PX)) + 3)
    return (k * PERIOD_PX + 0.5) * PX


def meshes(p):
    """gap and deposit as (P, N, T): per quad / triangle its own vertices, the plane's normal (faces.py's way)."""
    k = math.tan(math.radians(p["tilt"]))
    nrm = np.array([1.0, 0.0, k]) / math.hypot(1.0, k)
    Y = p["half_y"]
    zt, zb = -p["inset"], -(p["d"] - p["inset"])
    gap, dep = ([], [], []), ([], [], [])

    def quad(out, a, b, c, d, n):
        P, N, T = out
        i = len(P)
        P += [a, b, c, d]
        N += [n] * 4
        T += [(i, i + 1, i + 2), (i, i + 2, i + 3)]

    def tri(out, a, b, c):
        P, N, T = out
        n = np.cross(np.subtract(b, a), np.subtract(c, a))
        n = n / np.linalg.norm(n)
        i = len(P)
        P += [a, b, c]
        N += [n.tolist()] * 3
        T.append((i, i + 1, i + 2))

    for x0 in films_x():
        X = lambda z, s=0.0: x0 + (-min(z, 0.0)) * k + s
        top = zt
        if p["dep"]:
            h = p["dep_w"] / 2
            zz = (p["proud"], -p["dep"])
            # a sheared box: section corners (-h, z0) (-h, z1) (h, z1) (h, z0), at y = -Y and y = +Y
            sec = [(-h, zz[0]), (-h, zz[1]), (h, zz[1]), (h, zz[0])]
            pts = [[X(z, s), y, z] for y in (-Y, Y) for s, z in sec]
            Kn = len(sec)
            for s in range(Kn):
                a_, b_ = s, (s + 1) % Kn
                # (the winding does not matter: diffuse is two-sided in both renderers)
                tri(dep, pts[a_], pts[Kn + a_], pts[Kn + b_])
                tri(dep, pts[a_], pts[Kn + b_], pts[b_])
            tri(dep, pts[0], pts[2], pts[1]); tri(dep, pts[0], pts[3], pts[2])                  # y = -Y cap
            tri(dep, pts[Kn], pts[Kn + 1], pts[Kn + 2]); tri(dep, pts[Kn], pts[Kn + 2], pts[Kn + 3])  # y = +Y cap
            top = -p["dep"]
        ys = [-Y, Y] if not p["cols"] else np.linspace(-Y, Y, int(round(2 * Y / p["cols"])) + 1).tolist()
        for ya, yb in zip(ys[:-1], ys[1:]):          # one quad, or columns `cols` mm long (the card's du)
            quad(gap, [X(top), ya, top], [X(top), yb, top], [X(zb), yb, zb], [X(zb), ya, zb], nrm.tolist())
    return gap, dep


def write_ply(path, P, N, T, normals=True):
    P, N, T = np.asarray(P, "<f4"), np.asarray(N, "<f4"), np.asarray(T, "<i4")
    nprop = "property float nx\nproperty float ny\nproperty float nz\n" if normals else ""
    head = (f"ply\nformat binary_little_endian 1.0\nelement vertex {len(P)}\nproperty float x\nproperty float y\n"
            f"property float z\n{nprop}element face {len(T)}\nproperty list uchar int vertex_indices\nend_header\n")
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"], face["i"] = 3, T
    with open(path, "wb") as f:
        f.write(head.encode())
        f.write(np.ascontiguousarray(np.concatenate([P, N], 1) if normals else P).tobytes())
        f.write(face.tobytes())


def scene(p):
    q = lambda P: " ".join(f"{c:.4f}" for v in P for c in v)
    rn = "true" if p["rnee"] else "false"
    s = f"""# steep films in the glaze slab (tests/slab/vfilm.py): {json.dumps(p)}
LookAt 0 0 300.0 0 0 0  0 1 0
Camera "perspective" "float fov" [ {FOV} ]
Sampler "zsobol" "integer pixelsamples" [ {SPP['pbrt']} ]
Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" {rn}
Film "rgb" "integer xresolution" [ {RES[0]} ] "integer yresolution" [ {RES[1]} ] "string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true
WorldBegin
AttributeBegin
  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 1.0 ]
  Material "diffuse" "rgb reflectance" [ 0 0 0 ]
  Shape "bilinearmesh" "point3 P" [ {q(V.L1)} ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
AttributeBegin
  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 0.35 ]
  Material "diffuse" "rgb reflectance" [ 0 0 0 ]
  Shape "bilinearmesh" "point3 P" [ {q(V.L2)} ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" [ 360 0.03 830 0.03 ] "spectrum sigma_s" [ 360 2.5 830 2.5 ] "float g" [ 0.7 ] "float scale" [ 1 ]
AttributeBegin
  Material "diffuse" "spectrum reflectance" [ 360 0.58 830 0.58 ]
  Shape "bilinearmesh" "point3 P" [ -200 -200 -3.0 200 -200 -3.0 -200 200 -3.0 200 200 -3.0 ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
AttributeBegin
  MediumInterface "glaze" ""
  Material "dielectric" "float eta" [ 1.5 ] "float roughness" [ {p['alpha']} ] "bool remaproughness" false "bool refractivenee" {rn}
  Shape "plymesh" "string filename" [ "outer.ply" ]
AttributeEnd
AttributeBegin
  MediumInterface "" "glaze"
  Material "diffuse" "spectrum reflectance" [ 360 0.12 830 0.12 ]
  Shape "plymesh" "string filename" [ "body.ply" ]
AttributeEnd
"""
    if p["films"]:
        s += f"""AttributeBegin
  MediumInterface "glaze" "glaze"
  Material "thindielectric" "float eta" [ {p['eta']:.6f} ]
  Shape "plymesh" "string filename" [ "gap.ply" ]
AttributeEnd
"""
    if p["films"] and p["dep"]:
        s += """AttributeBegin
  MediumInterface "glaze" "glaze"
  Material "diffuse" "spectrum reflectance" [ 360 0.24 830 0.24 ]
  Shape "plymesh" "string filename" [ "deposit.ply" ]
AttributeEnd
"""
    return s


def write(only=None):
    for name in VARIANTS:
        if only and name not in only:
            continue
        p = params(name)
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        P, N, T, _ = shell.box(100.0, 100.0, 0.0, -p["d"] - 0.05)
        V.write_ply(os.path.join(d, "outer.ply"), P, N, T)
        V.write_ply(os.path.join(d, "body.ply"), *V.quad(100.0, 100.0, -p["d"]))
        gap, dep = meshes(p)
        if p["films"]:
            write_ply(os.path.join(d, "gap.ply"), *gap, normals=p["normals"])
        if p["films"] and p["dep"]:
            write_ply(os.path.join(d, "deposit.ply"), *dep, normals=p["normals"])
        open(os.path.join(d, "scene.pbrt"), "w").write(scene(p))
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), os.path.join(d, "scene.pbrt")],
                       check=True)
    print(f"pixel {PX * 1000:.1f} um, period {PERIOD_PX} px = {PERIOD_PX * PX:.3f} mm, films at x = {films_x()[:3]}...")


def queue(only=None):
    print("#!/bin/bash\n# steep films (tests/slab/vfilm.py queue): pbrt in the CPU slots, Cycles on the GPU in turn\n"
          "S=$HOME/gewu-render/scenes")
    names = [n for n in VARIANTS if not only or n in only]
    for n in names:
        print(f"rm -f /tmp/gewu-vf-{n}-pbrt.log; nohup ~/gewu-render/bin/mini-pbrt.sh $S/vf-{n} scene.pbrt "
              f"/tmp/gewu-vf-{n}-pbrt.log --outfile $S/vf-{n}/pbrt.exr < /dev/null > /dev/null 2>&1 &")
    for n in names:
        print(f"cd $S/vf-{n}; rm -f /tmp/gewu-vf-{n}-cyc.log; ~/gewu-render/bin/mini-gpu.sh /tmp/gewu-vf-{n}-cyc.log -b "
              f"--factory-startup --python-exit-code 1 -P $HOME/gewu-render/tools/cycles_scene.py -- scene.cycles.json "
              f"--spp {SPP['cycles']} --out $S/vf-{n}/cyc.exr < /dev/null > /dev/null 2>&1")
    print("echo done > /tmp/gewu-vf.done")


def profile(path):
    """Folded by the period: (PERIOD_PX,) mean over rows, columns of that phase and channels, over E1; and each bin's
    standard error from the spread of its columns' means (each column a sum of independent pixels)."""
    from camera import read_raw
    from table import E1
    a = (read_raw(path) / E1).mean(2)
    h, w = a.shape
    w0 = w - w % PERIOD_PX
    cols = a[:, :w0].mean(0).reshape(-1, PERIOD_PX)          # (periods, phase)
    return cols.mean(0), cols.std(0, ddof=1) / np.sqrt(len(cols))


def table():
    rows = {}
    for name in VARIANTS:
        d = os.path.join(OUT, name)
        have = {r: os.path.exists(os.path.join(d, f"{r}.exr")) for r in ("pbrt", "cyc")}
        if not all(have.values()):
            print(f"{name}: missing {[r for r, h in have.items() if not h]}")
            continue
        (p, ps), (c, cs) = profile(os.path.join(d, "pbrt.exr")), profile(os.path.join(d, "cyc.exr"))
        mp, mc = p.mean(), c.mean()
        sp, sc = np.sqrt((ps ** 2).sum()) / len(p), np.sqrt((cs ** 2).sum()) / len(c)
        print(f"{name:12s} period mean: pbrt {mp:.5f}+-{sp:.5f}  Cycles {mc:.5f}+-{sc:.5f}  Cycles/pbrt {mc / mp:.4f} "
              f"(z {(mc - mp) / math.hypot(sp, sc):+.1f})")
        print("   phase     " + " ".join(f"{i:6d}" for i in range(PERIOD_PX)))
        print("   pbrt      " + " ".join(f"{v:6.4f}" for v in p))
        print("   Cycles    " + " ".join(f"{v:6.4f}" for v in c))
        print("   C/p       " + " ".join(f"{v:6.3f}" for v in c / p))
        print("   z         " + " ".join(f"{v:+6.1f}" for v in (c - p) / np.hypot(ps, cs)))
        rows[name] = {"pbrt": p.tolist(), "pbrt_se": ps.tolist(), "cycles": c.tolist(), "cycles_se": cs.tolist(),
                      "params": params(name)}
    with open(os.path.join(OUT, "table.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    {"write": lambda: write(only), "queue": lambda: queue(only), "table": table}[cmd]()
