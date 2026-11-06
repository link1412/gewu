"""pbrt's thin film (patched: Material "thinfilm", docs/materials/yohen.md) on the flat strip of
tests/yohen/cycles_strip.py: a smooth plane, film thickness linear in x from 0 to DMAX nm, a uniform white
infinite light (rgb L 1 1 1: the sRGB illuminant, D65, so a perfect mirror is (1, 1, 1)), an orthographic camera
at a fixed angle to the normal. Every pixel is R(d, angle) in linear Rec.709; strip_compare.py checks it against
tools/tmm.py.

    python3 -I tests/yohen/pbrt_strip.py DIR --tag b --film 3.0+0.3j --sub 1.6 --dmax 600 --angles 0,30,60
    (then, per angle: pbrt --outfile DIR/strip_b_30.exr DIR/strip_b_30.pbrt)
"""
import argparse
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--tag", required=True)
ap.add_argument("--film", required=True, help="complex index, e.g. 2.5 or 3.0+0.3j")
ap.add_argument("--sub", required=True)
ap.add_argument("--dmax", type=float, required=True)
ap.add_argument("--angles", default="0,30,60")
ap.add_argument("--width", type=int, default=800)
ap.add_argument("--height", type=int, default=20)
ap.add_argument("--spp", type=int, default=256)
a = ap.parse_args()
os.makedirs(a.dir, exist_ok=True)


def cx(s):
    return complex(s.replace("i", "j")) if any(c in s for c in "ij") else complex(float(s), 0)


# the thickness ramp: pixel centres at (i + 0.5) / W hold (i + 0.5) / W, so bilinear lookup is exactly u
W = 4096
ramp = ((np.arange(W) + 0.5) / W).astype("<f4")
with open(os.path.join(a.dir, "ramp.pfm"), "wb") as f:
    f.write(b"Pf\n%d 1\n-1.0\n" % W)
    f.write(ramp.tobytes())


def const(v):
    return f"[ 360 {v:.6f} 830 {v:.6f} ]"


film, sub = cx(a.film), cx(a.sub)
# pbrt's image x runs along world -x here (skill-notes 58: +x is on the left): u = 1 at x = -1, so that image
# column i holds the thickness (i + 0.5) / W * DMAX as in the Cycles strip
for ang in [float(x) for x in a.angles.split(",")]:
    th = np.radians(ang)
    eye = (0.0, -10 * np.sin(th), 10 * np.cos(th))
    hy = a.height / a.width
    scene = f"""LookAt {eye[0]} {eye[1]} {eye[2]}  0 0 0  0 1 0
Camera "orthographic" "float screenwindow" [ -1 1 {-hy} {hy} ]
Sampler "independent" "integer pixelsamples" {a.spp}
Integrator "volpath" "integer maxdepth" 4
Film "rgb" "integer xresolution" {a.width} "integer yresolution" {a.height}
     "string filename" "strip_{a.tag}_{ang:g}.exr"
WorldBegin
LightSource "infinite" "rgb L" [ 1 1 1 ]
Texture "thick" "float" "imagemap" "string filename" "ramp.pfm" "string wrap" "clamp"
        "string filter" "bilinear" "float scale" {a.dmax} "string encoding" "linear"
Material "thinfilm" "spectrum filmeta" {const(film.real)} "spectrum filmk" {const(film.imag)}
         "spectrum eta" {const(sub.real)} "spectrum k" {const(sub.imag)}
         "texture thickness" "thick" "float roughness" 0
Shape "bilinearmesh" "point3 P" [ -1 -4 0  1 -4 0  -1 4 0  1 4 0 ]
      "point2 uv" [ 1 0  0 0  1 1  0 1 ]
"""
    with open(os.path.join(a.dir, f"strip_{a.tag}_{ang:g}.pbrt"), "w") as f:
        f.write(scene)
print("wrote scenes in", a.dir)
