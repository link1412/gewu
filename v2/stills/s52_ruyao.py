"""Ru ware (汝窑), a shallow six-lobed washer from above: it rises from the bottom of the frame, the crown of its far lobe the arc, the inside sky-blue with crackle at two scales.

    python3 -I v2/stills/s52_ruyao.py [preview|mid|final]

From ref/ru (reference only, not in the film): the Cleveland dish 1957.40 for the plates and the pale cracks, the NPM narcissus basin for the sky blue, the NPM lotus bowl's close-up (lotus/17009895.jpg) for the net.
- The crackle is a fracture hierarchy: long cracks cut the glaze into plates; each plate then breaks on its own, its cracks stopping where the plate stops, so the junctions on a plate's edge are T's;
  the fine crab's-claw net (蟹爪纹) does the same inside the plates that carry it. Edges are bisector distances, so they stay antialiased at any density. The fracture is modelled as Voronoi cells, not grown
  crack by crack (s29 grows them: its cost would be several times worse over a whole dish); within a cell boundary the junctions are Y's, which real sequential fracture does not make. A stand-in.
- Each plate has its own hair of tilt, so a reflection breaks at the cracks. Estimate of size, chosen by eye.
- The depth of a crack is a stand-in: a pale line with a soft shadow beside it, not a sheet of geometry in a medium (s29). The glaze is a painted colour with Principled subsurface scattering, not a real medium,
  for the sake of a saturated, luminous colour.
- After comparing with lotus/17009895.jpg and narcissus/npm_17009896.jpg: the colour came down from turquoise to a grey sky-green, the surface is satin not glass, the cracks are stained tan, darker than the glaze and soft where they run down into it, in three orders; a glass skin (yohen_shader shell) over the painted glaze, with a real gap, so the cracks lie under the reflection. A stand-in for a real medium (s29 does that, at about ten times the cost over a whole dish).
- Lobes: six, depth a = 5% of the radius, are ours. ref/ru holds one lobed piece, the NPM lotus bowl, with about ten pointed petals; no six-lobed washer is in the folder, so count and depth are not checked against a photograph.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.spatial import cKDTree

from dishkit import Dish
import yohen
from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep

NAME = "s52_ruyao"
SEED = 52
HERE = os.path.dirname(os.path.abspath(__file__))
W, EL, DIST = 20.4, 70.0, 88.0
PROFILE = [(4.0, 0.0), (4.35, 0.2), (5.6, 0.9), (6.6, 1.9), (7.02, 2.62), (7.05, 2.86), (6.88, 2.9), (6.5, 2.35), (5.6, 1.4), (4.5, 0.82), (2.5, 0.6), (0.0, 0.55)]
RHO0 = 4.7  # just outside the well


def voronoi(x, y, cell, seed, ang=0.0, stretch=1.0, extent=12.0):
    """Jittered-grid Voronoi on the points (x, y): the cell id and the distance to its edge (bisector distance, cm)."""
    rng = np.random.default_rng(seed)
    ca, sa = np.cos(ang), np.sin(ang)
    u = (ca * x + sa * y) / stretch
    v = -sa * x + ca * y
    g = np.arange(-extent - 2 * cell, extent + 2 * cell, cell)
    gu, gv = np.meshgrid(g, g)
    pts = np.stack([gu.ravel() + rng.uniform(-0.48, 0.48, gu.size) * cell, gv.ravel() + rng.uniform(-0.48, 0.48, gu.size) * cell], 1)
    tree = cKDTree(pts)
    q = np.stack([u, v], -1)
    d, i = tree.query(q, k=2, workers=-1)
    gap = np.linalg.norm(pts[i[:, 0]] - pts[i[:, 1]], axis=1)
    e = (d[:, 1] ** 2 - d[:, 0] ** 2) / (2.0 * np.maximum(gap, 1e-6))
    return i[:, 0].astype(np.int64), e.astype(np.float32)


def crackle(X, Y, pxcm):
    """Three levels of fracture over the grid. Returns the edge distance per level (cm), the plate's id, its L1 cell's id."""
    shape = X.shape
    # a crack changes its mind: a slow wander and a small quick jag, per level
    # (a stronger warp folds the plane over and draws closed loops in the cracks, which fracture never makes)
    w0x, w0y = fbm(shape, pxcm, 0.8, 3.0, 2.8, SEED + 1), fbm(shape, pxcm, 0.8, 3.0, 2.8, SEED + 2)
    jx, jy = fbm(shape, pxcm, 0.05, 0.25, 2.2, SEED + 3), fbm(shape, pxcm, 0.05, 0.25, 2.2, SEED + 4)
    x0 = (X + 0.12 * w0x + 0.006 * jx).ravel()
    y0 = (Y + 0.12 * w0y + 0.006 * jy).ravel()
    plate, e0 = voronoi(x0, y0, 2.0, SEED + 10)
    # second level: each plate breaks on its own. Four fields, one per plate by its id, turned and stretched differently, so that neighbours do not line up
    NL = 4
    who = (plate * 2654435761 % 1000003) % NL
    cell1 = np.zeros(plate.shape, np.int64)
    e1 = np.zeros(plate.shape, np.float32)
    x1 = (X + 0.05 * w0y + 0.005 * jy).ravel()
    y1 = (Y + 0.05 * w0x + 0.005 * jx).ravel()
    for k in range(NL):
        m = who == k
        if m.any():
            cell1[m], e1[m] = voronoi(x1[m], y1[m], 0.56, SEED + 20 + k, ang=0.4 + k * 0.785, stretch=1.45)
    cell1 = cell1 * NL + who
    # third level: the crab's claws, finer, each L1 cell breaking on its own
    NF = 3
    who2 = (cell1 * 40503 % 65537) % NF
    e2 = np.zeros(plate.shape, np.float32)
    x2 = (X + 0.004 * jx).ravel()
    y2 = (Y + 0.004 * jy).ravel()
    for k in range(NF):
        m = who2 == k
        if m.any():
            _, e2[m] = voronoi(x2[m], y2[m], 0.19, SEED + 30 + k, ang=1.1 + k * 1.05, stretch=1.3)
    return e0.reshape(shape), e1.reshape(shape), e2.reshape(shape), plate.reshape(shape), cell1.reshape(shape)


def build(dish, X, Y, pxcm):
    shape = X.shape
    ny, nx = shape
    rho = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    rl = dish.rho_lip
    e0, e1, e2, plate, cell1 = crackle(X, Y, pxcm)

    # per plate random values
    def per(ids, seed):
        u, inv = np.unique(ids, return_inverse=True)
        return np.random.default_rng(seed).random(len(u), dtype=np.float32)[inv].reshape(ids.shape)

    pv = per(plate, SEED + 40)
    cv = per(cell1, SEED + 41)

    # a line's width wanders along its length, and fine ones break off into nothing
    wob = rank(fbm(shape, pxcm, 0.08, 0.5, 2.2, SEED + 5))
    breakup = rank(fbm(shape, pxcm, 0.12, 0.7, 2.2, SEED + 6))
    px = 1.0 / pxcm
    w0 = 0.006 + 0.007 * wob
    w1 = 0.0028 + 0.003 * wob
    w2 = 0.0016 + 0.0012 * wob
    l0 = sstep(w0 + px, np.maximum(w0 - px, 0.0), e0)
    l1 = sstep(w1 + px, np.maximum(w1 - px, 0.0), e1) * sstep(0.12, 0.42, breakup + 0.25 * cv)
    # the fine net lives on two thirds of the wall and is denser where the glaze pooled
    fine_zone = sstep(0.14, 0.42, 0.65 * cv + 0.5 * rank(fbm(shape, pxcm, 1.0, 4.0, 3.0, SEED + 7)))
    l2 = sstep(w2 + px, np.maximum(w2 - px, 0.0), e2) * fine_zone * sstep(0.1, 0.42, breakup)
    # thin glaze on the lip barely cracks
    calm = sstep(rl - 0.08, rl - 0.4, rho)
    l0, l1, l2 = l0 * calm, l1 * calm, l2 * calm

    # --- the glaze: a grey sky-green, bluer where it pooled, greener and warmer where it thins. Measured by eye from the photos: about sRGB (165, 190, 180). Low contrast: a Ru glaze hardly varies
    big = rank(yohen.fixed(X, Y, 1.4, 7.0, 3.4, SEED + 8))
    midf = rank(yohen.fixed(X, Y, 0.3, 1.5, 2.6, SEED + 9))
    sky = color([0.38, 0.475, 0.465])
    jade = color([0.4, 0.485, 0.435])
    col = mix(sky, jade, sstep(0.2, 0.85, big))
    col = col * (0.98 + 0.04 * midf)[..., None]
    col = col * (0.985 + 0.03 * pv)[..., None]
    pool = np.exp(-(((rho - RHO0) / 0.9) ** 2))
    col = mix(col, color([0.32, 0.43, 0.44]), 0.3 * pool)
    # the opacity of the glaze: fine milky grain, the stipple of the lotus bowl's close-up
    grain = fbm(shape, pxcm, 0.012, 0.05, 1.4, SEED + 15)
    col = col * (1.0 + 0.032 * grain)[..., None]

    # thin at the notches and on the lip: paler, warm, the body close under (出筋), never a white band
    n = dish.lobes["n"]
    c2 = np.cos(n * (th - np.pi / 2) / 2.0) ** 2
    ramp = sstep(RHO0 - 0.6, rl, rho)
    rib = np.exp(-(c2 / (0.012 + 0.09 * (1 - ramp)) ** 1.0)) * ramp
    col = mix(col, color([0.56, 0.62, 0.56]), 0.4 * rib)
    edge = 0.012 * yohen.fixed(X, Y, 0.5, 2.5, 3.0, SEED + 11)
    lip = sstep(rl - 0.25, rl - 0.03, rho + edge)
    col = mix(col, color([0.62, 0.6, 0.52]), 0.8 * lip)

    # --- the cracks: a tan stain. Each order has its own width and strength, and each has a core and a soft side where the stain went down into the glaze; the third order is barely there
    tan = color([0.36, 0.34, 0.22])
    soft0 = blur(l0, max(0.018 * pxcm, 0.8))
    soft1 = blur(l1, max(0.01 * pxcm, 0.6))
    soft2 = blur(l2, max(0.004 * pxcm, 0.5))
    stain = np.clip(1.5 * soft0 + 0.9 * soft1 + 0.35 * soft2, 0, 1) * (0.7 + 0.5 * sstep(0.3, 0.9, pv))
    col = col * (1.0 - 0.2 * stain)[..., None]
    core = np.clip(0.8 * l0 + 0.5 * l1 + 0.2 * l2, 0, 1)
    col = mix(col, tan, 0.55 * core)
    # a crack is a plane in the glaze and a few of them catch the light: a thin bright side on the main cracks only, where the plate's own tilt lets it
    ghost = blur(np.roll(l0, 1, 1), 0.6) * sstep(0.55, 0.85, cv)
    col = mix(col, color([0.75, 0.8, 0.74]), 0.28 * ghost)

    # a few bubbles and iron specks: 寥若晨星
    rng = np.random.default_rng(SEED + 12)
    area = nx * ny / pxcm**2
    for k, rc, r_, a_ in ((int(area * 0.12), color([0.14, 0.09, 0.05]), 0.014, 0.7), (int(area * 0.3), color([0.14, 0.11, 0.07]), 0.007, 0.5), (int(area * 0.08), color([0.72, 0.8, 0.78]), 0.012, 0.6), (int(area * 0.6), color([0.5, 0.6, 0.58]), 0.006, 0.5)):
        seeds = np.ones(shape, np.uint8)
        seeds[rng.integers(0, ny, k), rng.integers(0, nx, k)] = 0
        dp = cv2.distanceTransform(seeds, cv2.DIST_L2, 5) / pxcm
        col = mix(col, rc, sstep(r_, r_ * 0.4, dp) * a_)

    # --- relief: low wave, each plate's own hair of tilt, a groove at each crack mouth
    u_, inv = np.unique(plate, return_inverse=True)
    inv = inv.ravel()
    rt = np.random.default_rng(SEED + 13)
    tx, ty = rt.normal(0, 0.006, len(u_)).astype(np.float32), rt.normal(0, 0.006, len(u_)).astype(np.float32)
    area_p = np.bincount(inv, minlength=len(u_)) + 1.0
    cx = (np.bincount(inv, X.ravel(), minlength=len(u_)) / area_p).astype(np.float32)
    cy = (np.bincount(inv, Y.ravel(), minlength=len(u_)) / area_p).astype(np.float32)
    inv = inv.reshape(shape)
    tilt = np.clip(tx[inv] * (X - cx[inv]) + ty[inv] * (Y - cy[inv]), -0.008, 0.008)
    groove = blur(np.clip(l0 + 0.6 * l1 + 0.3 * l2, 0, 1), max(0.003 * pxcm, 0.5))
    h = 0.0005 * groove * 0 + 0.0 * tilt
    rough = 0.45 + 0.1 * groove
    # --- the skin: slow waves, each plate's own hair of tilt so a reflection steps at the cracks, a groove at each main crack's mouth. Satin: glaze this opaque does not mirror
    gap = 0.003 + 0.03 * sstep(rl - 0.05, rl - 0.8, rho)
    hs = gap + 0.005 * yohen.fixed(X, Y, 1.5, 6.0, 3.4, SEED + 14) + 0.3 * tilt - 0.0012 * blur(np.clip(l0 + 0.5 * l1, 0, 1), max(0.003 * pxcm, 0.5)) + 0.00002 * grain
    rs = 0.17 + 0.03 * midf + 0.08 * groove + 0.08 * lip
    on = sstep(rl + 0.2, rl + 0.05, rho)
    return dish.surface(X, Y, h), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.03, 1).astype(np.float32), dish.surface(X, Y, hs), np.clip(rs, 0.03, 1).astype(np.float32), on.astype(np.float32)


def crop(dish, X, Y, extra=0.5):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, lobes=dict(n=6, a=0.05, b=0.2, p=0.8, rho0=RHO0))
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.415), aperture_mm=20.0, focus_rho=dish.rho_lip - 1.6)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 170.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.07))
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    P, C, Ro, Ps, Rs, On = build(dish, X, Y, pxcm)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, **yohen.front(P=P, col=C, rough=Ro))
    npz_s = os.path.join(d, f"shell.{q}.npz")
    np.savez(npz_s, **yohen.front(P=Ps[::2, ::2], rough=Rs[::2, ::2], on=On[::2, ::2]))
    npz_r = os.path.join(d, f"rest.{q}.npz")
    Pr, Cr = yohen.rest_of_bowl(dish, col=(0.34, 0.45, 0.42), under=0.02)
    np.savez(npz_r, **yohen.front(P=Pr, col=Cr))

    # the room: a large overcast window to the left, its reflection falling away softly across the far wall: this shot's light is calm and even, the opposite of the yohen's lamps
    yohen.use_room()
    r0, _, _ = yohen.reflection_at(dish, cam, 0.34, 0.66)
    env = {"diffuse": True, "base": [0.05, 0.05, 0.052], "panels": [{"dir": r0.tolist(), "w": 26, "h": 18, "L": 2.2, "rgb": [0.98, 0.99, 1.0], "soft": 20, "grad": 0.3}]}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "washer", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.15, "IOR": 1.5, "Subsurface Weight": 0.5, "Subsurface Radius": [0.03, 0.05, 0.06], "Subsurface Scale": 1.0}},
            {"name": "skin", "npz": npz_s, "shader_py": os.path.join(HERE, "yohen_shader.py"), "params": {"kind": "shell", "ior": 1.5}},
            {"name": "rest", "npz": npz_r, "material": {"Base Color": "col", "Roughness": 0.3}},
        ],
        "env": env,
        "table": {"z": 0.0, "kind": "linen", "rgb": [0.12, 0.1, 0.082], "thread": 0.06, "angle": 9, "seed": 52},
        "lights": [
            {"name": "key", "loc": [-50.0, 18.0, 80.0], "target": [0, 1, 1], "size": [34, 34], "watts": 38000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
        ],
        "diffuse_bounces": 3,
        "glossy_bounces": 4,
        "bounces": 10,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.2, "contrast": 1.2, "saturation": 1.0, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "halation": 0.04, "glare": 0.004, "vignette": 0.2})


main()
