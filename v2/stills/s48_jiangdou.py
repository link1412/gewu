"""Peachbloom (豇豆红), a shallow brush washer from above: it rises from the bottom of the frame, its far lip the arc, the inside clouded pink and red with moss specks.

    python3 -I v2/stills/s48_jiangdou.py [preview|mid|final]

From ref/jiangdouhong/report.md and the crops of Met 66.206.17 (reference only, not in the film):
- red of the copper: broken, mottled, flecked with pale, soft at its boundary; pale pink where the copper is thin;
- moss (绿苔): dark round core with a pale green halo, scattered apart, with fine dark dust between. Spots are colour in the glaze, not relief;
- polished glass over all; a pale thin glaze on the lip (灯草口).
Stand-ins and estimates:
- the glaze is painted, not a real medium: a colour map under a clear spec, softened by Principled subsurface scattering, for the sake of a saturated, luminous colour;
- the washer's size and section are estimates; putting the peachbloom on the inside is the brief's choice for this viewpoint, not a statement about a particular piece;
- the colour map and the speck counts are chosen by eye and are richer than the photographs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from dishkit import Dish
from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import reflect_light_loc

NAME = "s48_jiangdou"
SEED = 48
W, EL, DIST = 20.0, 70.0, 84.0
PROFILE = [(3.8, 0.0), (4.2, 0.25), (5.6, 1.0), (6.6, 2.0), (6.98, 2.72), (7.0, 2.98), (6.82, 3.0), (6.45, 2.4), (5.5, 1.35), (4.3, 0.75), (2.5, 0.5), (0.0, 0.45)]


def stamps(shape, pxcm, x0, y0, xs, ys, rs, wx, wy):
    """Soft discs at continuous positions: the field of 1 - d/r, top-most value, outlines from a warp."""
    ny, nx = shape
    F = np.zeros(shape, np.float32)
    for cx, cy, r in zip(xs, ys, rs):
        cx_, cy_, rp = (cx - x0) * pxcm, (cy - y0) * pxcm, max(r * pxcm, 0.6)
        m = int(rp * 1.8) + 3
        i0, i1, j0, j1 = int(cx_) - m, int(cx_) + m + 1, int(cy_) - m, int(cy_) + m + 1
        if i0 < 0 or j0 < 0 or i1 >= nx or j1 >= ny:
            continue
        Yg, Xg = np.mgrid[j0:j1, i0:i1].astype(np.float32)
        d = np.hypot(Xg + wx[j0:j1, i0:i1] * rp - cx_, Yg + wy[j0:j1, i0:i1] * rp - cy_) / rp
        F[j0:j1, i0:i1] = np.maximum(F[j0:j1, i0:i1], 1 - d)
    return F


# copper field -> colour (linear): cream ground, peach, coral, crimson, the deep bean red
RAMP_X = [0.0, 0.16, 0.34, 0.52, 0.72, 0.9, 1.0]
RAMP = np.array(
    [
        [0.94, 0.68, 0.6],
        [0.93, 0.5, 0.46],
        [0.9, 0.3, 0.3],
        [0.84, 0.16, 0.18],
        [0.74, 0.08, 0.1],
        [0.62, 0.042, 0.06],
        [0.5, 0.028, 0.042],
    ],
    np.float32,
)


def build(dish, X, Y, pxcm):
    shape = X.shape
    ny, nx = shape
    x0, y0 = float(X[0, 0]), float(Y[0, 0])
    rho = np.hypot(X, Y)
    rl = dish.rho_lip
    rng = np.random.default_rng(SEED)

    # the copper: blown on, so rich and broken, thicker in a broad sweep round the wall and running out towards the well and to one side
    big = fbm(shape, pxcm, 1.2, 7.0, 3.4, SEED + 1)
    mid = fbm(shape, pxcm, 0.15, 1.2, 2.6, SEED + 2)
    fine = fbm(shape, pxcm, 0.012, 0.09, 1.9, SEED + 3)
    wall = sstep(1.6, 5.2, rho)
    f = 0.16 + 0.5 * wall + 0.075 * big + 0.012 * mid + 0.012 * fine + 0.05 * (-X / 7.0) + 0.05 * sstep(-2.0, 7.0, Y)
    # the flecks live in the boundary of the red: in the heart of it the colour is clean, in the pale it is clean too
    trans = np.exp(-(((f - 0.36) / 0.13) ** 2))
    f = f + trans * (0.075 * mid + 0.04 * fbm(shape, pxcm, 0.03, 0.2, 2.0, SEED + 12))
    # the thick red lies in the concave foot of the wall; towards the lip the glaze thins and the red pales
    f = f - 0.2 * sstep(rl - 1.0, rl - 0.2, rho)
    wx, wy = fbm(shape, pxcm, 0.01, 0.1, 2.0, SEED + 4), fbm(shape, pxcm, 0.01, 0.1, 2.0, SEED + 5)
    # peach points: fine, dense red dots over the pale, and pale dots in the red, at continuous positions
    area = nx * ny / pxcm**2
    n = int(area * 45)
    pr = stamps(shape, pxcm, x0, y0, X.min() + rng.random(n) * (X.max() - X.min()), Y.min() + rng.random(n) * (Y.max() - Y.min()), np.clip(rng.lognormal(np.log(0.022), 0.5, n), 0.008, 0.08), wx, wy)
    n = int(area * 40)
    pw = stamps(shape, pxcm, x0, y0, X.min() + rng.random(n) * (X.max() - X.min()), Y.min() + rng.random(n) * (Y.max() - Y.min()), np.clip(rng.lognormal(np.log(0.028), 0.55, n), 0.01, 0.11), wx, wy)
    f = f + 0.14 * sstep(0.0, 0.5, pr) * sstep(0.02, 0.3, f) * sstep(0.7, 0.4, f)
    f = f - 0.14 * sstep(0.0, 0.55, pw) * sstep(0.2, 0.42, f) * sstep(0.85, 0.5, f)
    f = np.clip(blur(f, max(0.007 * pxcm, 0.5)), 0, 1)  # the copper diffused while firing: flecks have soft sides
    col = np.stack([np.interp(f.ravel(), RAMP_X, RAMP[:, i]).reshape(shape) for i in range(3)], -1).astype(np.float32)

    # moss: only where the copper is thinning, in loose scatters
    def cluster(n_cl, spread, per, weight):
        xs, ys, tries = [], [], 0
        while len(xs) < n_cl and tries < n_cl * 400:
            tries += 1
            a, t = rng.uniform(0.5, rl - 0.6), rng.uniform(-np.pi, np.pi)
            u, v = a * np.cos(t), a * np.sin(t)
            if rng.random() < weight(u, v, a):
                for _ in range(rng.poisson(per) + 1):
                    xs.append(u + rng.normal(0, spread))
                    ys.append(v + rng.normal(0, spread))
        return np.array(xs), np.array(ys)

    # the moss gathers in a broad drift across the wall to the upper left and right
    def mw(u, v, a):
        return np.clip(0.2 + 0.8 * np.exp(-(((a - 4.7) / 1.3) ** 2)), 0, 1) * (0.45 + 0.55 * float(np.sin(1.6 * np.arctan2(v, u) + 0.9) > -0.1))

    xm, ym = cluster(170, 0.42, 1.2, mw)
    rm = np.clip(rng.lognormal(np.log(0.03), 0.42, len(xm)), 0.014, 0.085)
    wlx, wly = fbm(shape, pxcm, 0.03, 0.15, 2.2, SEED + 6), fbm(shape, pxcm, 0.03, 0.15, 2.2, SEED + 7)
    sp = stamps(shape, pxcm, x0, y0, xm, ym, rm, wlx * 0.05, wly * 0.05)
    keep = rng.random(len(xm)) < 0.8
    # the green does not ring its core: it lies to one side, a smear in the glaze; and many specks are green alone (Met crop)
    off = rm[keep] * 1.1
    hl = stamps(shape, pxcm, x0, y0, xm[keep] + rng.normal(0, 1, keep.sum()) * off, ym[keep] + rng.normal(0, 1, keep.sum()) * off, rm[keep] * rng.uniform(1.2, 2.4, keep.sum()), wlx * 0.3, wly * 0.3)
    xg, yg = cluster(240, 0.5, 1.0, mw)
    gl = stamps(shape, pxcm, x0, y0, xg, yg, np.clip(rng.lognormal(np.log(0.04), 0.5, len(xg)), 0.015, 0.11), wlx * 0.3, wly * 0.3)
    hl = np.maximum(hl, gl * rng.uniform(0.8, 1.0))
    core = sstep(0.0, 0.42, blur(sp, max(0.009 * pxcm, 0.6)))
    halo = sstep(0.0, 0.6, blur(hl, max(0.02 * pxcm, 0.8))) * (1 - core)
    # dust
    xd, yd = cluster(2600, 0.16, 0.7, lambda u, v, a: np.clip(0.1 + 0.8 * np.exp(-(((a - 4.4) / 1.6) ** 2)), 0, 1))
    rd = np.clip(rng.lognormal(np.log(0.0065), 0.4, len(xd)), 0.003, 0.02)
    dust = sstep(0.0, 0.35, stamps(shape, pxcm, x0, y0, xd, yd, rd, wx * 0.2, wy * 0.2))
    green = color([0.1, 0.4, 0.2])
    col = mix(col, col * 0.14 + green * 0.86, halo * 0.8)
    kt = rank(fbm(shape, pxcm, 0.04, 0.25, 2.2, SEED + 8))
    k = mix(color([0.014, 0.036, 0.03]), color([0.05, 0.075, 0.02]), kt)
    col = mix(col, k, core)
    col = mix(col, color([0.1, 0.1, 0.05]), dust * 0.75)

    # the lip: thin glaze over the white body
    edge = 0.02 * fbm(shape, pxcm, 0.4, 2.0, 3.0, SEED + 9)
    lip = sstep(rl - 0.2, rl - 0.06, rho + edge)
    col = mix(col, color([0.92, 0.78, 0.72]), lip)

    # glass, with a very low undulation and very few pits
    h = 0.005 * fbm(shape, pxcm, 1.5, 6.0, 3.4, SEED + 10) + 0.000008 * fbm(shape, pxcm, 0.1, 0.4, 2.0, SEED + 11)
    seeds = np.ones(shape, np.uint8)
    nh = int(area * 1.6)
    seeds[rng.integers(0, ny, nh), rng.integers(0, nx, nh)] = 0
    dp = cv2.distanceTransform(seeds, cv2.DIST_L2, 5) / pxcm
    pit = sstep(0.012, 0.005, dp)
    h = h - 0.003 * pit
    rough = 0.04 + 0.012 * rank(mid) + 0.18 * pit + 0.03 * lip
    return dish.surface(X, Y, h), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.02, 1).astype(np.float32)


def crop(dish, X, Y, extra=0.5):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.38), aperture_mm=30.0, focus_rho=dish.rho_lip - 1.8)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 170.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm))
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    P, C, Ro = build(dish, X, Y, pxcm)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)

    def wall(rh, th):
        return dish.polar(np.array(rh), th), dish.normal(np.array(rh * np.cos(th)), np.array(rh * np.sin(th)))

    pf, nf = wall(dish.rho_lip - 1.6, np.pi / 2)
    sheen, _ = reflect_light_loc(pf, nf, cam, 130.0)
    pw, nw = wall(dish.rho_lip - 3.0, np.pi / 2 + 0.5)
    lw, _ = reflect_light_loc(pw, nw, cam, 120.0)
    A = dish.polar(np.array(dish.rho_lip), np.pi / 2)
    scene = {
        "camera": cam,
        "meshes": [
            {
                "name": "washer",
                "npz": npz,
                "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5, "IOR": 1.52, "Subsurface Weight": 0.65, "Subsurface Radius": [0.09, 0.035, 0.03], "Subsurface Scale": 1.0},
            }
        ],
        "lights": [
            {"type": "gradient", "name": "sheen", "loc": sheen.tolist(), "target": pf.tolist(), "size": [420, 300], "sigma": [130, 60], "L": 0.1, "rgb": [1.0, 0.99, 0.98]},
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": pw.tolist(), "size": [190, 4.0], "sigma": [34, 6], "L": 5.5, "rgb": [1.0, 0.98, 0.95]},
            {"name": "key", "loc": [-14.0, 12.0, 100.0], "target": [0, 2, 1], "size": [70, 70], "watts": 62000, "rgb": [1.0, 0.97, 0.93], "hide_in_gloss": True},
            {"name": "fill", "loc": [14.0, -40.0, 85.0], "target": [0, 3, 1], "size": [60, 60], "watts": 14000, "rgb": [1.0, 0.98, 0.96], "hide_in_gloss": True},
            {"name": "lip", "loc": (A + [0.0, 34.0, 26.0]).tolist(), "target": A.tolist(), "size": [60, 4], "watts": 16000, "rgb": [1.0, 0.96, 0.9]},
        ],
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.0, "contrast": 1.25, "saturation": 1.1, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "glare": 0.004, "vignette": 0.2})


main()
