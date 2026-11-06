"""Checks of the Ru washer's object layer against the photo.

    python3 -I objects/ru_washer/validate.py [--scene out/ru/washer/scene] [--out out/ru/washer]

1. overlay.png: the photo with the projected MESH's silhouette (the union of the glaze shell's front-facing
   triangles, rasterised at the photo's resolution, its boundary in red), the model's front lip and the crease on
   top of the foot ring (form.py's contours, yellow and magenta), and the measured edge points (measure.py, cyan);
   overlay_crops.png: five regions at 3x.
2. The residuals of the mesh: the distance from each measured outline point to the mesh silhouette's boundary (the
   mesh, not the fitted curves: it checks the profile -> mesh -> camera chain), px in the photo.
3. pbrt's camera: the scene's LookAt and fov (scene.json), projected with pbrt's own conventions (left-handed
   LookAt, fov across the shorter side, raster y down) onto the scene's film and scaled to the photo, against the
   photo's pinhole (form.project) on the mesh's vertices: they must agree (the mirror in scene.py).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import form as fm  # noqa: E402
import shell  # noqa: E402

PHOTO = os.path.join(ROOT, "ref/ru/photos/cma_1957.40.jpg")


def cam_params():
    C = json.load(open(fm.CAMERA))
    p = {k: v["value"] for k, v in C["params"].items()}
    p["f_px"] = C["f_px"]["value"]
    return p


def pbrt_project(P, lookat, fov_deg, res):
    """pbrt-v4's perspective camera: LookAt(eye, target, up) (transform.cpp: right = up x dir, newUp = dir x right),
    the screen window [-aspect, aspect] x [-1, 1] for a wide film (fov across the shorter side), raster y down."""
    eye, target, up = (np.asarray(v, float) for v in lookat)
    d = target - eye
    d /= np.linalg.norm(d)
    right = np.cross(up / np.linalg.norm(up), d)
    right /= np.linalg.norm(right)
    nup = np.cross(d, right)
    q = np.asarray(P, float) - eye
    x, y, z = q @ right, q @ nup, q @ d
    t = math.tan(math.radians(fov_deg) / 2)
    W, H = res
    asp = W / H
    if W >= H:
        sx, sy = x / z / t, y / z / t
        return np.c_[(sx + asp) / (2 * asp) * W, (1 - sy) / 2 * H]
    sx, sy = x / z / t, y / z / t
    return np.c_[(sx + 1) / 2 * W, (1 / asp - sy) / (2 / asp) * H]


def silhouette_mask(P, T, p, size):
    """The union of the front-facing triangles of a closed mesh, projected with the photo's pinhole."""
    C, Rm = fm.camera(p)
    gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    front = np.einsum("ij,ij->i", gn, C - P[T[:, 0]]) > 0
    Q = fm.project(P, p)
    im = Image.new("L", size, 0)
    d = ImageDraw.Draw(im)
    for tri in T[front]:
        d.polygon([tuple(Q[i]) for i in tri], fill=255)
    return np.asarray(im) > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default=os.path.join(ROOT, "out/ru/washer/scene"))
    ap.add_argument("--out", default=os.path.join(ROOT, "out/ru/washer"))
    a = ap.parse_args()
    p = cam_params()
    photo = Image.open(PHOTO).convert("RGB")
    W, H = photo.size
    E = {k: np.asarray(v, float) for k, v in json.load(open(fm.EDGES))["sets"].items()}

    P, T = shell.read_ply(os.path.join(a.scene, "glaze.ply"))
    M = silhouette_mask(P, T, p, (W, H))
    edge = M & ~ndi.binary_erosion(M)
    dist = ndi.distance_transform_edt(~edge)
    res = {}
    for k in ("outline_top", "outline_side", "outline_bottom"):
        q = E[k]
        v = ndi.map_coordinates(dist, [q[:, 1], q[:, 0]], order=1)
        res[k] = {"n": int(len(v)), "median_px": round(float(np.median(v)), 2), "p90_px": round(float(np.percentile(v, 90)), 2),
                  "max_px": round(float(v.max()), 1)}
    # pbrt's camera on the film vs the photo's pinhole, on a sample of the mesh's vertices
    S = json.load(open(os.path.join(a.scene, "scene.json")))
    rw, rh = S["res"]
    sample = P[:: max(1, len(P) // 20000)]
    mirrored = sample.copy()
    mirrored[:, 0] *= -1                       # the scene's frame (scene.py): the washer is round, so the same mesh
    qb = pbrt_project(mirrored, S["lookat_pbrt"], S["fov_deg"], (rw, rh)) * (H / rh)
    qb[:, 0] += (W - rw * H / rh) / 2          # the film's width scaled by the height, centred
    qp = fm.project(sample, p)
    diff = np.hypot(*(qb - qp).T)
    cam_check = {"film": [rw, rh], "max_px_in_photo": round(float(diff.max()), 4),
                 "note": "pbrt's projection of the mirrored scene vs the photo's pinhole on the unmirrored washer"}

    # the overlay
    ov = photo.copy()
    d = ImageDraw.Draw(ov)
    ys, xs = np.nonzero(edge)
    for x, y in zip(xs, ys):
        d.point((int(x), int(y)), fill=(255, 40, 40))
    Mc = fm.model_curves({**fm.params_dict([q[1] for q in fm.FIT_PARAMS]), **load_fitted(), **p})
    for k, col in (("lip_front", (255, 230, 0)), ("foot_top", (255, 0, 255))):
        Q = Mc[k].points()
        Q = Q[(Q[:, 0] > E[k][:, 0].min() - 300) & (Q[:, 0] < E[k][:, 0].max() + 300)]
        for x, y in Q[::2]:
            d.point((float(x), float(y)), fill=col)
    for k, v in E.items():
        for x, y in v[::3]:
            d.point((float(x), float(y)), fill=(0, 220, 255))
    os.makedirs(a.out, exist_ok=True)
    box = (330, 560, 3070, 1740)
    ov.crop(box).save(os.path.join(a.out, "overlay.png"))
    crops = [(380, 740, 640, 1000), (2760, 740, 3020, 1000), (760, 1380, 1020, 1640), (2420, 1380, 2680, 1640),
             (1500, 960, 1760, 1220)]
    tiles = [ov.crop(c).resize((780, 780), Image.NEAREST) for c in crops]
    sheet = Image.new("RGB", (780 * len(tiles), 780))
    for i, t in enumerate(tiles):
        sheet.paste(t, (780 * i, 0))
    sheet.save(os.path.join(a.out, "overlay_crops.png"))
    out = {"mesh_silhouette_vs_photo_outline_px": res, "pbrt_camera_vs_photo_pinhole": cam_check,
           "overlay": os.path.relpath(os.path.join(a.out, "overlay.png"), ROOT),
           "crops": "left rim, right rim, foot left end, foot right end, front lip (3x, nearest)"}
    json.dump(out, open(os.path.join(a.out, "validate.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


def load_fitted():
    F = json.load(open(fm.FORM))
    return {k: v["value"] for k, v in F["fitted"].items()}


if __name__ == "__main__":
    main()
