"""Shared pieces of the texture tests: images in and out, a pbrt camera model, the render queue.

Scenes are written in mm, Z up, in our pbrt subset; each test's gen_*.py writes one directory under
out/textures/ with scene.pbrt, the maps and (for Cycles) scene.cycles.json from tools/rgbscene.py.
"""
import math
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out/textures")
IMGTOOL = os.path.join(ROOT, "third_party/pbrt-build/imgtool")
REMOTE = "~/gewu-render/scenes"
TOOLS_TEST = "~/gewu-render/tools-test"        # our copy of cycles_scene.py


# --- images ----------------------------------------------------------------------------------
def write_pfm(path, a):
    """a: (H, W) or (H, W, 3) float, row 0 the TOP row of the image (as a picture); PFM stores bottom first."""
    a = np.asarray(a, "<f4")
    if a.ndim == 2:
        a = a[..., None]
    with open(path, "wb") as f:
        f.write(b"PF\n" if a.shape[2] == 3 else b"Pf\n")
        f.write(f"{a.shape[1]} {a.shape[0]}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(a[::-1]).tobytes())


def read_pfm(path):
    with open(path, "rb") as f:
        kind = f.readline().strip()
        w, h = map(int, f.readline().split())
        scale = float(f.readline())
        nc = 3 if kind == b"PF" else 1
        a = np.frombuffer(f.read(), "<f4" if scale < 0 else ">f4").reshape(h, w, nc)
    return np.ascontiguousarray(a[::-1]).astype(np.float64)       # row 0 the top


def read_image(path):
    """Any image imgtool reads (EXR from pbrt or Cycles), as (H, W, 3) float64, row 0 the top."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.pfm")
        subprocess.run([IMGTOOL, "convert", "--outfile", p, path], check=True, capture_output=True)
        a = read_pfm(p)
    return a if a.shape[2] == 3 else np.repeat(a, 3, 2)


def write_exr(path, a):
    """A float map as EXR through imgtool (it writes half floats; read the file back for exact values)."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.pfm")
        write_pfm(p, np.repeat(np.asarray(a)[..., None], 3, 2) if np.ndim(a) == 2 else a)
        subprocess.run([IMGTOOL, "convert", "--outfile", path, p], check=True, capture_output=True)


# --- scene text ------------------------------------------------------------------------------
def header(eye, target, fov, res, spp, up=(0, 0, 1), maxdepth=8, filename="pbrt.exr"):
    return (f"LookAt {eye[0]} {eye[1]} {eye[2]}  {target[0]} {target[1]} {target[2]}  {up[0]} {up[1]} {up[2]}\n"
            f'Camera "perspective" "float fov" [ {fov} ]\n'
            f'Sampler "zsobol" "integer pixelsamples" [ {spp} ]\n'
            f'Integrator "volpath" "integer maxdepth" [ {maxdepth} ]\n'
            f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
            f'"string filename" [ "{filename}" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] '
            f'"bool rawsensor" true\nWorldBegin\n')


def light_quad(center, normal, size, scale, temp=5500, rect=None):
    """An area light, a square (or a rect (w, h) along (e1, e2)) facing along `normal`, written so that
    cross(p10 - p00, p01 - p00) is the normal."""
    n = np.asarray(normal, float)
    n /= np.linalg.norm(n)
    ref = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.99 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(ref, n)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)                  # cross(e1, e2) = n
    w, h = rect or (size, size)
    c = np.asarray(center, float)
    P = [c - e1 * w / 2 - e2 * h / 2, c + e1 * w / 2 - e2 * h / 2, c - e1 * w / 2 + e2 * h / 2, c + e1 * w / 2 + e2 * h / 2]
    pts = " ".join(f"{x:.6f}" for p in P for x in p)
    return (f'AttributeBegin\n  AreaLightSource "diffuse" "blackbody L" [ {temp} ] "float scale" [ {scale} ]\n'
            f'  Material "diffuse" "rgb reflectance" [ 0 0 0 ]\n'
            f'  Shape "bilinearmesh" "point3 P" [ {pts} ] "integer indices" [ 0 1 2 3 ]\nAttributeEnd\n')


def quad(p00, p10, p01, p11):
    pts = " ".join(f"{x:.6f}" for p in (p00, p10, p01, p11) for x in p)
    return f'  Shape "bilinearmesh" "point3 P" [ {pts} ] "integer indices" [ 0 1 2 3 ]\n'


# --- pbrt's camera, for analytic predictions --------------------------------------------------
def pixel_rays(eye, target, up, fov_deg, res, rows=slice(None)):
    """pbrt's perspective camera (LookAt: right = up x dir, newUp = dir x right; fov spans the shorter side).
    Returns the eye and the (H, W, 3) unit directions through pixel centres, row 0 the top."""
    eye, target, up = (np.asarray(v, float) for v in (eye, target, up))
    d = target - eye
    d /= np.linalg.norm(d)
    r = np.cross(up / np.linalg.norm(up), d)
    r /= np.linalg.norm(r)
    nu = np.cross(d, r)
    W, H = res
    asp = W / H
    t = math.tan(math.radians(fov_deg) / 2)
    sx = (np.arange(W) + 0.5) / W * 2 - 1
    sy = 1 - (np.arange(H) + 0.5) / H * 2
    sx, sy = (sx * asp, sy) if asp > 1 else (sx, sy / asp)
    sy = sy[rows]
    D = d + (sx[None, :, None] * t) * r + (sy[:, None, None] * t) * nu
    return eye, D / np.linalg.norm(D, axis=2, keepdims=True)


# --- the render machine --------------------------------------------------------------------------------
def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, check=True, **kw)


def push(name, files):
    """Copy files (paths) into the scene directory textures-NAME."""
    d = f"{REMOTE}/textures-{name}"
    sh(f"ssh link 'mkdir -p {d}'")
    sh("scp -q " + " ".join(files) + f" link:{d}/")
    return d


def cycles(name, scene_json, out, extra="--spp 64", wait=True, py="cycles_scene.py"):
    """Queue a Cycles GPU job (our tools-test copy of the adapter)."""
    d = f"{REMOTE}/textures-{name}"
    log = f"/tmp/gewu-tex-{name}-{os.path.splitext(out)[0]}.log"
    sh(f"ssh link 'rm -f {log}; cd {d} && nohup ~/gewu-render/bin/mini-gpu.sh {log} -b --factory-startup "
       f"--python-exit-code 1 -P {TOOLS_TEST}/{py} -- {scene_json} --out $PWD/{out} {extra} > /dev/null 2>&1 & echo queued'")
    return log


def pbrt(name, scene, out_log, extra=""):
    d = f"{REMOTE}/textures-{name}"
    log = f"/tmp/gewu-tex-{name}-{out_log}.log"
    sh(f"ssh link 'rm -f {log}; cd ~ && nohup ~/gewu-render/bin/mini-pbrt.sh {d} {scene} {log} {extra} > /dev/null 2>&1 & echo queued'")
    return log


def wait(logs):
    """Block until each log's last line is `done <code> ...`; fail if a code is not 0."""
    for log in logs:
        r = subprocess.run(f"ssh link 'while ! tail -1 {log} 2>/dev/null | grep -q \"^done\"; do sleep 5; done; tail -2 {log}'",
                           shell=True, capture_output=True, text=True).stdout.strip().splitlines()
        print(log, "->", r[-1] if r else "?")
        if len(r) == 0 or r[-1].split()[1] != "0":
            raise SystemExit(f"{log} failed:\n" + "\n".join(r))


def pull(name, files, local):
    os.makedirs(local, exist_ok=True)
    d = f"{REMOTE}/textures-{name}"
    for f in files:
        sh(f"scp -q link:{d}/{f} {local}/")
