"""A pbrt-v4 scene of the Ru washer seen as in the CMA 1957.40 photo (the subset tools/rgbscene.py reads, so it
renders in Cycles too): the solved camera (photo_camera.json), the body and the closed glaze shell (washer.py), a
glaze medium and dielectric and the body's reflectance from a JSON file, a ground plane, and the lights in their own
file, lights.pbrt, Included (a placeholder: replace it with --lights).

    python3 -I objects/ru_washer/scene.py --out out/ru/washer/scene [--res 960x548] [--spp 64]
        [--glaze objects/ru_washer/glaze_placeholder.json] [--lights my_lights.pbrt]
        [--thickness uniform|thin] [--e0 0.5] [--bare-foot-mm 0] [--n-around 360]

    python3 -I tools/rgbscene.py out/ru/washer/scene/scene.pbrt        # the Cycles scene beside it

Frames. washer.py and form.py work in a right-handed object frame (mm, z up, z = 0 the ground). pbrt is
left-handed: the same LookAt shows the mirror image (tools/cycles_scene.py flips Cycles' render to pbrt's for the
same reason). So the scene is the object frame mirrored in x (x -> -x): the washer is round and is written as it is;
the camera and the lights are mirrored, and the image comes out the right way round, as the photo. Write lights in
the object frame and mirror them with pbrt_point() (softbox() does), or write pbrt coordinates directly knowing
that pbrt's +x is the object frame's -x (the photo's left is pbrt's +x side).

Framing: the photo's pinhole, principal point at the centre. pbrt's "fov" is the angle across the shorter image
side; it is set from the photo's height (1942 px), so any resolution with the photo's aspect (3400:1942 = 1.7508;
960x548 is 1.7518, 0.06% wider) frames as the photo does, and another aspect crops or extends it about the centre.

The ground is a plane DROP_MM below z = 0 (the foot ring's flat bottom would otherwise be coplanar with it), x from
-GROUND_HALF_X to +GROUND_HALF_X, y from GROUND_Y[0] (in front) to GROUND_Y[1] (behind; beyond it there is nothing,
black, as the photo's backdrop) [A: the cloth's extent; the photo shows its back edge fading into black about
GROUND_Y[1] behind the washer, read off by eye].
"""
import argparse
import json
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import form as fm  # noqa: E402
import washer as wa  # noqa: E402

GLAZE = os.path.join(HERE, "glaze_placeholder.json")
DROP_MM = 0.005
GROUND_HALF_X, GROUND_Y = 1500.0, (-900.0, 1600.0)


def pbrt_point(P):
    """Object frame (right-handed) -> the scene's frame (mirrored in x)."""
    P = np.array(P, float)
    P[..., 0] *= -1
    return P


def spectrum(entry):
    """A JSON entry {"value": v} or {"lambda_nm_value": [l0, v0, l1, v1, ...]} as a pbrt spectrum array."""
    if "lambda_nm_value" in entry:
        vals = list(entry["lambda_nm_value"])
    else:
        vals = [360, entry["value"], 830, entry["value"]]
    if vals[0] > 360:
        vals = [360, vals[1]] + vals
    if vals[-2] < 830:
        vals = vals + [830, vals[-1]]
    return "[ " + " ".join(f"{x:g}" for x in vals) + " ]"


def softbox(centre, size, scale, K=5500, group=None, aim=(0.0, 0.0, 15.0)):
    """A square diffuse emitter in the object frame (right-handed), facing `aim`, as pbrt lines in the scene's
    (mirrored) frame. Its corners are mirrored and their order reversed, so its front still faces the washer."""
    c = np.asarray(centre, float)
    n = np.asarray(aim, float) - c
    n /= np.linalg.norm(n)
    up = np.array([0, 0, 1.0]) if abs(n[2]) < 0.9 else np.array([0, 1.0, 0])
    vh = np.cross(np.cross(n, up), n)
    vh /= np.linalg.norm(vh)
    uw = np.cross(vh, n)                             # uw x vh = n: pbrt's bilinear patch faces cross(p10-p00, p01-p00)
    cs = [c - size / 2 * uw - size / 2 * vh, c + size / 2 * uw - size / 2 * vh,
          c - size / 2 * uw + size / 2 * vh, c + size / 2 * uw + size / 2 * vh]
    cs = pbrt_point(cs)[[0, 2, 1, 3]]                # the mirror flips the facing; swapping p10 and p01 restores it
    L = ["AttributeBegin"]
    if group:
        L.append(f'  Attribute "light" "string group" "{group}"')
    L += [f'  AreaLightSource "diffuse" "blackbody L" [ {K:g} ] "float scale" [ {scale:g} ]',
          '  Material "diffuse" "rgb reflectance" [ 0 0 0 ]',
          '  Shape "bilinearmesh" "point3 P" [ ' + " ".join(f"{x:.4f}" for q in cs for x in q) + ' ] "integer indices" [ 0 1 2 3 ]',
          "AttributeEnd"]
    return L


def placeholder_lights():
    """PLACEHOLDER lights [A], to be replaced: one large soft box above the washer and in front of it, 5500 K."""
    L = ["# PLACEHOLDER lights (objects/ru_washer/scene.py placeholder_lights) [A]: one 500 mm soft box above and in",
         "# front of the washer, 5500 K. Replace this file (scene.py --lights FILE). pbrt frame = object frame mirrored",
         "# in x (scene.py's docstring)."]
    L += softbox((0.0, -350.0, 450.0), 500.0, 1.0, group="key")
    return "\n".join(L) + "\n"


def photo_lights():
    """The CMA photo's lights as read off it [A] (the shadow falls back-left and is very soft, its core 3-4% of the
    lit ground: one large key soft box front-right and above, a fill under 5%; objects/ru_washer/light.py)."""
    L = ["# the CMA 1957.40 photo's lights [A] (objects/ru_washer/scene.py photo_lights): a 700 mm key soft box",
         "# to the right and a little in front, about 30 deg up (the shadow's length; no reflection of it on the far inner wall, as in the photo), a weak fill front-left. pbrt frame = object frame mirrored in x."]
    L += softbox((560.0, -120.0, 330.0), 700.0, 1.0, group="key")
    L += softbox((-500.0, -400.0, 150.0), 800.0, 0.03, group="fill")
    return "\n".join(L) + "\n"


def write(a):
    os.makedirs(a.out, exist_ok=True)
    cam = json.load(open(fm.CAMERA))
    G = json.load(open(a.glaze))
    res = [int(v) for v in a.res.lower().split("x")]
    e = wa.uniform(a.e0) if a.thickness == "uniform" else wa.thin_edges(a.e0)
    bm, gm, rec, curves = wa.build(e, a.bare_foot_mm, a.n_around)
    rec["check"] = wa.check(bm, gm, curves)
    if a.deform_seed is not None:                    # this piece's own departure from the turned form
        dv = wa.deviation(a.deform_seed)
        bm = (*wa.deform(bm[0], bm[1], dv), *bm[2:])
        gm = (*wa.deform(gm[0], gm[1], dv), *gm[2:])
        rec["deviation"] = dv.about
    if rec["check"]["body_bad_edges"] or rec["check"]["glaze_bad_edges"]:
        raise SystemExit(f"meshes not watertight: {rec['check']}")
    wa.write_ply(os.path.join(a.out, "body.ply"), *bm)
    wa.write_ply(os.path.join(a.out, "glaze.ply"), *gm)
    rec.pop("profiles")
    json.dump(rec, open(os.path.join(a.out, "mesh.json"), "w"), indent=1)

    # the camera, mirrored into pbrt's frame
    eye = np.array(cam["eye_mm"], float)
    fwd = np.array(cam["forward"], float)
    down = np.array(cam["down"], float)
    target = eye + 100.0 * fwd
    e_, t_, u_ = pbrt_point(eye), pbrt_point(target), pbrt_point(-down)
    f_px = cam["f_px"]["value"]
    W, H = fm.PHOTO_SIZE
    # pbrt's fov spans the shorter side; scale the photo's focal length to this film by the height (or the width)
    if res[1] <= res[0]:
        fov = math.degrees(2 * math.atan(H / 2 / f_px))
    else:
        fov = math.degrees(2 * math.atan(W / 2 / f_px))
    L = [f"# the Ru washer (CMA 1957.40) as photographed: objects/ru_washer/scene.py; camera from photo_camera.json",
         f"# frame: the object frame (right-handed, mm, z up, z = 0 the ground) mirrored in x, see scene.py",
         f"LookAt {e_[0]:.6f} {e_[1]:.6f} {e_[2]:.6f}  {t_[0]:.6f} {t_[1]:.6f} {t_[2]:.6f}  {u_[0]:.6f} {u_[1]:.6f} {u_[2]:.6f}",
         f'Camera "perspective" "float fov" [ {fov:.6f} ]',
         f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]',
         f'Integrator "volpath" "integer maxdepth" [ {G.get("max_depth", 64)} ] "bool refractivenee" true',
         f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
         f'"string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true',
         "WorldBegin",
         'Include "lights.pbrt"',
         f'MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" {spectrum(G["sigma_a_per_mm"])} '
         f'"spectrum sigma_s" {spectrum(G["sigma_s_per_mm"])} "float g" [ {G["g"]["value"]} ] "float scale" [ 1 ]',
         "# the ground cloth: felt.py's textures (--felt), or a plain reflectance from the glaze JSON",
         "AttributeBegin"]
    if a.felt:
        F_ = json.load(open(os.path.join(a.felt, "felt.json")))
        for fn in ("felt_c.pfm", "felt_h.pfm", "felt.npz"):
            shutil.copyfile(os.path.join(a.felt, fn), os.path.join(a.out, fn))
        L += ['  Texture "feltc" "spectrum" "familymap" "string family" "felt.npz" "string map" "felt_c.pfm" '
              '"string wrap" "repeat"',
              '  Texture "felth" "float" "imagemap" "string filename" "felt_h.pfm" "string wrap" "repeat" '
              '"string encoding" "linear"',
              '  Material "diffuse" "texture reflectance" "feltc" "texture displacement" "felth"']
        nu, nv = 2 * GROUND_HALF_X / F_["tile_mm"], (GROUND_Y[1] - GROUND_Y[0]) / F_["tile_mm"]
        uv = f' "point2 uv" [ 0 0 {nu:g} 0 0 {nv:g} {nu:g} {nv:g} ]'
    else:
        L.append(f'  Material "diffuse" "spectrum reflectance" {spectrum(G["ground_reflectance"])}')
        uv = ""
    L += ['  Shape "bilinearmesh" "point3 P" [ ' + " ".join(
             f"{x:g}" for q in ((-GROUND_HALF_X, GROUND_Y[0], -DROP_MM), (GROUND_HALF_X, GROUND_Y[0], -DROP_MM),
                                (-GROUND_HALF_X, GROUND_Y[1], -DROP_MM), (GROUND_HALF_X, GROUND_Y[1], -DROP_MM)) for x in q)
         + ' ] "integer indices" [ 0 1 2 3 ]' + uv,
         "AttributeEnd",
         "# the glaze: a closed shell (outer surface + an inner one inside the body), the medium inside it",
         "AttributeBegin",
         '  MediumInterface "glaze" ""',
         f'  Material "dielectric" "float eta" [ {G["eta"]["value"]} ] "float roughness" [ {G["roughness"]["value"]} ] '
         '"bool remaproughness" false "bool refractivenee" true',
         '  Shape "plymesh" "string filename" [ "glaze.ply" ]',
         "AttributeEnd",
         "# the body: opaque, inside the glaze shell; what leaves it travels in the glaze",
         "AttributeBegin",
         '  MediumInterface "" "glaze"',
         f'  Material "diffuse" "spectrum reflectance" {spectrum(G["body_reflectance"])}',
         '  Shape "plymesh" "string filename" [ "body.ply" ]',
         "AttributeEnd"]
    if a.cracks:                                     # cracks.py's air films, inside the glaze
        for fn in ("gap.ply", "cracks.pbrt"):
            shutil.copyfile(os.path.join(a.cracks, fn), os.path.join(a.out, fn))
        L.append('Include "cracks.pbrt"')
    open(os.path.join(a.out, "scene.pbrt"), "w").write("\n".join(L) + "\n")
    if a.lights == "photo":
        open(os.path.join(a.out, "lights.pbrt"), "w").write(photo_lights())
    elif a.lights:
        shutil.copyfile(a.lights, os.path.join(a.out, "lights.pbrt"))
    else:
        open(os.path.join(a.out, "lights.pbrt"), "w").write(placeholder_lights())
    info = {"camera": os.path.relpath(fm.CAMERA, ROOT), "glaze": os.path.relpath(os.path.abspath(a.glaze), ROOT),
            "lights": a.lights or "placeholder_lights()", "res": res, "spp": a.spp, "fov_deg": fov,
            "lookat_pbrt": [e_.tolist(), t_.tolist(), u_.tolist()], "mesh": rec["check"],
            "thickness": rec["thickness"], "bare_foot_mm": a.bare_foot_mm,
            "cracks": a.cracks, "deviation": rec.get("deviation")}
    json.dump(info, open(os.path.join(a.out, "scene.json"), "w"), indent=1)
    print(json.dumps(info))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out/ru/washer/scene"))
    ap.add_argument("--res", default="960x548")
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--glaze", default=GLAZE)
    ap.add_argument("--lights", help="a pbrt file to Include as the lights, or 'photo' (default: the placeholder soft box)")
    ap.add_argument("--thickness", choices=["uniform", "thin"], default="uniform")
    ap.add_argument("--e0", type=float, default=wa.E_REF)
    ap.add_argument("--bare-foot-mm", type=float, default=0.0)
    ap.add_argument("--n-around", type=int, default=360)
    ap.add_argument("--cracks", help="a cracks.py output directory (gap.ply, cracks.pbrt), made with the same --deform-seed")
    ap.add_argument("--felt", help="a felt.py output directory: the ground's textures")
    ap.add_argument("--deform-seed", type=int, help="this piece's departure from the turned form (washer.deviation)")
    write(ap.parse_args())


if __name__ == "__main__":
    main()
