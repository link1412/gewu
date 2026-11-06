"""The ginkgo leaf's material cards: the leaf (objects/yinxing/, built from a config) under the light of two real
photographs, as pbrt scenes with raw sensor RGB (and their Cycles translations).

    python3 -I materials/yinxing/card.py lamp|scan [--spp N] [--set SET]  # -> out/yinxing/card/<rig>_<set>/scene.pbrt (+ .cycles.json)

- lamp (transmission): the leaf lying on a lamp's diffusing shade, seen from the other side, framed and scaled as
  Fargoh's 'Ginkgo biloba yellow leaf on a lamp' (1280 x 959 px, objects/yinxing/lamp_outline.json: O at its
  photo_frame O_px, px_per_mm). The shade: a diffuse emitter just behind the leaf, radiance uniform, warm (blackbody
  3000 K [A: a household lamp; the photo's white balance hides it]), its own diffuse reflectance 0.8 [A: white
  plastic or paper], so the light the leaf reflects back is partly returned; 0.8 mm behind the blade (the petiole's
  depth holds the blade off the shade [A]). No light on the camera's side [A].
- scan (reflection): the leaf face down on a flatbed's glass, as NobbiP's 400 dpi scans (15.75 px/mm): the camera
  looks along the normal, a broad D65 source at 45 degrees [A: the scanner's LED bar, spectra unknown], nothing
  behind the leaf (the scan's ground is black), a white of reflectance 1 beside the leaf for the white point
  [A: the scanner's calibration strip]. The 960 x 540 frame shows the distal half of the leaf.
The camera looks up from below (z < 0), so the image's right is +x and up is +y as in the photos (the leaf's two faces
are the same in round 1). A long lens (300 mm away) stands in for the photos' lenses [A: the leaves are flat].
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "objects/yinxing"))
import optics as O  # noqa: E402

SENSOR = "canon_eos_5d_mkiv"
DIST = 300.0
WHITE = (-30.4, 43.2, -26.4, 46.8)                       # the scan card's white, mm (top left, off the leaf)


def camera(cx, cy, half_short):
    fov = 2 * math.degrees(math.atan(half_short / DIST))
    return [f"LookAt {cx:.4f} {cy:.4f} {-DIST:.1f}  {cx:.4f} {cy:.4f} 0  0 1 0",
            f'Camera "perspective" "float fov" {fov:.6f}']


def quad(x0, y0, x1, y1, z, down):
    """A bilinear patch at height z; its normal -z if down (facing the camera), else +z."""
    if down:
        pts = [(x0, y0), (x0, y1), (x1, y0), (x1, y1)]
    else:
        pts = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    s = " ".join(f"{x:.3f} {y:.3f} {z:.3f}" for x, y in pts)
    return f'Shape "bilinearmesh" "point3 P" [ {s} ]'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rig", choices=("lamp", "scan"))
    ap.add_argument("--leaf", default=os.path.join(ROOT, "objects/yinxing/lamp.json"))
    ap.add_argument("--set")
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--senescence", action="store_true",
                    help="round 2: the blade as a mix of lamina and vein families on senescence.py's maps (pbrt only)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--lampfield", help="S8 r2: lampfield.json, the lamp's brightness over the frame as measured off the "
                                        "photo; the shade becomes a grid of emitters scaled by it")
    a = ap.parse_args()
    which = a.set or {"lamp": "lamp", "scan": "nobbip"}[a.rig]
    cfg = json.load(open(a.leaf))
    obj = os.path.join(ROOT, "out/yinxing/objects", cfg["name"])
    if not os.path.exists(os.path.join(obj, "veins.exr")):
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "objects/yinxing/leaf.py"), a.leaf], check=True)
    out = os.path.join(ROOT, "out/yinxing/card", f"{a.rig}_{which}{a.tag}")
    os.makedirs(out, exist_ok=True)
    for f in ("blade.ply", "petiole.ply", "veins.exr"):
        shutil.copy(os.path.join(obj, f), os.path.join(out, f))
    if a.senescence:
        import senescence
        sen = senescence.build(which, obj, out)
        O.write_brown_families(out, which)
    fam = O.write_family(out, which)
    m = O.load()
    outline = json.load(open(os.path.join(ROOT, "objects/yinxing/lamp_outline.json")))["outline"]
    L = [f"# materials/yinxing/card.py {a.rig}: set {which}, leaf {cfg['name']}"]
    if a.rig == "lamp":
        W, H = outline["photo_frame"]["size_px"]
        H = 960 if H == 959 else H                           # the photo's 959 rows: one more row, cropped later
        S = outline["px_per_mm"]
        ox, oy = outline["photo_frame"]["O_px"]
        cx, cy = (W / 2 - ox) / S, (oy - H / 2) / S          # the frame's centre in the leaf's mm
        L += camera(cx, cy, H / 2 / S)
        key = 3000
    else:
        W, H = 960, 540
        S = 400 / 25.4
        cx, cy = 0.0, 30.0
        L += camera(cx, cy, H / 2 / S)
        key = 6500
    L += [f'Sampler "zsobol" "integer pixelsamples" {a.spp}',
          'Integrator "volpath" "integer maxdepth" 8',
          f'Film "rgb" "bool rawsensor" true "string sensor" "{SENSOR}" "float iso" 100 '
          f'"integer xresolution" {W} "integer yresolution" {H} "string filename" "card.exr"',
          "WorldBegin"]
    if a.senescence:
        L += O.pbrt_blade_mix(brown_vein="brown_vein.exr" if os.path.exists(os.path.join(out, "brown_vein.exr")) else None)
    else:
        L += O.pbrt_blade(os.path.basename(fam["R"]), os.path.basename(fam["T"]), "veins.exr")
    L += ['Shape "plymesh" "string filename" "blade.ply"',
          "AttributeBegin", O.pbrt_petiole(m, which), 'Shape "plymesh" "string filename" "petiole.ply"', "AttributeEnd"]
    if a.rig == "lamp" and a.lampfield:
        # the shade as cells of 0.5 mm over the frame (wider strips outside it), each emitting blackbody 3000 K scaled by
        # the photo's lamp brightness at its centre (lampfield.py: a smooth fit, extrapolated under the leaf [A])
        import lampfield
        import numpy as np
        lj = json.load(open(a.lampfield))
        hw, hh = W / 2 / S + 4, H / 2 / S + 4
        cell = 0.5            # mm: 2 mm cells showed as tiles on the shade seen directly (S8 r2); at 0.5 mm the
        #                       step between cells is under 0.2 %, below the 8-bit display's step
        xs = np.r_[cx - 200, np.arange(cx - hw, cx + hw + 1e-6, cell), cx + 200]
        ys = np.r_[cy - 200, np.arange(cy - hh, cy + hh + 1e-6, cell), cy + 200]
        L += ['Material "diffuse" "spectrum reflectance" [ 300 0.8 900 0.8 ]']
        for x0_, x1_ in zip(xs[:-1], xs[1:]):
            for y0_, y1_ in zip(ys[:-1], ys[1:]):
                g = float(lampfield.gain_at_mm(lj, 0.5 * (x0_ + x1_), 0.5 * (y0_ + y1_)))
                L += ["AttributeBegin", f'AreaLightSource "diffuse" "blackbody L" {key} "float scale" {g:.5f}',
                      quad(x0_, y0_, x1_, y1_, 0.8, down=True), "AttributeEnd"]
    elif a.rig == "lamp":
        L += ["AttributeBegin",
              'Material "diffuse" "spectrum reflectance" [ 300 0.8 900 0.8 ]',
              f'AreaLightSource "diffuse" "blackbody L" {key} "float scale" 1',
              quad(cx - 200, cy - 200, cx + 200, cy + 200, 0.8, down=True),
              "AttributeEnd"]
    else:
        e = math.radians(45)
        d = 2000.0
        c = (cx, cy - d * math.cos(e), -d * math.sin(e))     # the source's centre, in the y-z plane, below
        L += ["AttributeBegin",
              'Material "diffuse" "spectrum reflectance" [ 300 0 900 0 ]',
              'AreaLightSource "diffuse" "spectrum L" "stdillum-D65" "float scale" 1',
              f"Translate {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}",
              f"Rotate {math.degrees(e) - 90:.3f} 1 0 0",
              quad(-600, -600, 600, 600, 0.0, down=False),
              "AttributeEnd",
              "AttributeBegin",
              'Material "diffuse" "spectrum reflectance" [ 300 1 900 1 ]',
              quad(*WHITE, -0.05, down=True),
              "AttributeEnd"]
    path = os.path.join(out, "scene.pbrt")
    open(path, "w").write("\n".join(L) + "\n")
    json.dump({"rig": a.rig, "set": which, "sensor": SENSOR, "leaf": cfg["name"], "px_per_mm": S, "frame_centre_mm": [cx, cy],
               "key_K": key, "white_patch_mm": WHITE if a.rig == "scan" else None,
               "lamp_field": os.path.relpath(a.lampfield, ROOT) if a.lampfield else None},
              open(os.path.join(out, "card.json"), "w"), indent=1)
    if a.senescence:
        print("(no Cycles translation: rgbscene/cycles_scene have no 'mix' material; pbrt is the reference)")
    else:
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), path, "--key-K", str(key)], check=True)
    print("->", path)


if __name__ == "__main__":
    main()
