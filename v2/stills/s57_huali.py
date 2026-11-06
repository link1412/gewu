"""Shot 30: a turned huanghuali (黄花梨) dish seen from above, its ghost faces (鬼脸) across the well; the far lip is the arc.

    python3 -I v2/stills/s57_huali.py [preview|mid|final]

Replaces s30, which showed the figure on the swell of a round body. The figure is that of s30 (rings as level lines bent round knots, thin dark latewood, open pores carried along the grain;
scales are estimates from general knowledge) drawn larger, on a board. One stand-in: the figure is laid over the wall as it lies on the well, where a real turned dish would cut the rings
differently as the wall rises.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from dishkit import Dish
from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from s30_huali import carry, rings
from vessel import reflect_light_loc

NAME = "s57_huali"
SEED = 57
W, EL, DIST = 30.0, 66.0, 110.0
PROFILE = [(10.2, 0.0), (11.8, 0.42), (13.0, 1.25), (13.42, 1.72), (13.5, 1.86), (13.36, 1.96), (12.7, 1.55), (11.75, 0.98), (10.9, 0.66), (9.8, 0.54), (5.0, 0.5), (0.0, 0.5)]
K = 2.5  # the figure of s30 drawn this much larger: at a dish's scale a knot must still fill a quarter of the frame


def build(dish, X, Y, pxcm):
    shape = X.shape
    ny, nx = shape
    x0, y0 = float(X[0, 0]), float(Y[0, 0])
    x1, y1 = float(X[0, -1]), float(Y[-1, 0])
    c0 = np.array([0.1, 8.0 / K])

    # the figure on a fixed grid, in the coordinates of the wood; the composition must not change with the quality
    g = 110.0
    gw, gh = int((x1 - x0) / K * g), int((y1 - y0) / K * g)
    Ug, Vg = np.meshgrid(x0 / K + (np.arange(gw, dtype=np.float32) + 0.5) / g, y0 / K + (np.arange(gh, dtype=np.float32) + 0.5) / g)
    pg = cv2.GaussianBlur(rings(Ug, Vg, c0, g).astype(np.float32), (0, 0), 0.8)
    phi = cv2.remap(pg, (X / K - x0 / K) * g - 0.5, (Y / K - y0 / K) * g - 0.5, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    gy, gx = np.gradient(pg)
    n = np.hypot(gx, gy) + 1e-6
    txg, tyg = cv2.GaussianBlur((-gy / n).astype(np.float32), (0, 0), 2.0), cv2.GaussianBlur((gx / n).astype(np.float32), (0, 0), 2.0)
    n = np.hypot(txg, tyg) + 1e-6
    tx = cv2.resize(txg / n, (nx, ny), interpolation=cv2.INTER_LINEAR)
    ty = cv2.resize(tyg / n, (nx, ny), interpolation=cv2.INTER_LINEAR)

    # --- rings
    jitter = 0.035 * fbm(shape, pxcm, 0.15, 1.0, 2.2, SEED + 3)
    f = np.mod(phi + jitter, 1.0)
    late = sstep(0.62, 0.9, f) * sstep(1.0, 0.94, f)
    body = rank(fbm(shape, pxcm, 0.5, 5.0, 2.6, SEED + 4))
    ring_id = np.floor(phi + jitter).astype(np.int32)
    year = np.random.default_rng(SEED + 5).normal(0, 1, 4096).astype(np.float32)[np.mod(ring_id, 4096)]

    # --- fibres and pores, carried along the grain
    w = np.random.default_rng(SEED + 6).standard_normal(shape, dtype=np.float32)
    streak = carry(blur(w, 0.8), tx, ty, 0.12 * pxcm)
    streak = streak / (streak.std() + 1e-6)
    w2 = (np.random.default_rng(SEED + 7).random(shape, dtype=np.float32) > 0.9992).astype(np.float32)
    pores = carry(blur(w2, 0.8), tx, ty, 0.1 * pxcm, steps=8)
    pores = sstep(0.18, 0.7, np.clip(pores / (np.percentile(pores, 99.7) + 1e-6), 0, 1))

    # --- colour: honey, red-brown bands, dark lines
    honey = mix(color([0.66, 0.30, 0.07]), color([0.82, 0.44, 0.12]), body)
    amber = mix(color([0.4, 0.15, 0.03]), color([0.52, 0.21, 0.045]), body)
    t = sstep(-0.9, 1.0, year + 0.35 * fbm(shape, pxcm, 0.2, 1.4, 2.2, SEED + 8))
    col = mix(honey, amber, t)
    col = mix(col, color([0.065, 0.024, 0.009]), late * (0.72 + 0.2 * sstep(-1, 1, year)))
    col = col * (1.0 + 0.1 * streak[..., None])
    col = mix(col, color([0.03, 0.013, 0.007]), pores * 0.92)

    # --- surface: a hair of relief under the coat; two lines cut on the lathe where the well ends, and one under the lip
    rho = np.hypot(X, Y)
    rl = dish.rho_lip
    groove = np.exp(-(((rho - 9.55) / 0.035) ** 2)) + 0.7 * np.exp(-(((rho - 9.78) / 0.024) ** 2)) + 0.6 * np.exp(-(((rho - (rl - 0.42)) / 0.022) ** 2))
    h = -0.0004 * late + 0.0002 * streak - 0.0012 * pores + 0.0016 * fbm(shape, pxcm, 1.0, 8.0, 3.0, SEED + 9) - 0.03 * groove
    col = mix(col, col * 0.3, np.clip(groove, 0, 1)[..., None] ** 2 * 0.8)
    rough = 0.3 + 0.08 * sstep(-1, 1, streak) + 0.25 * pores
    return dish.surface(X, Y, h), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.42), aperture_mm=30.0, focus_rho=6.5)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 150.0 * dens
    X, Y = dish.grid(cam, pxcm)
    X, Y = X.astype(np.float32), Y.astype(np.float32)
    P, C, Ro = build(dish, X, Y, pxcm)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)
    # the window falls on the far wall, where the polish shows the turn of the dish; a broad light from the side brings up the figure
    rw = dish.rho_lip - 2.0
    far = dish.polar(np.array(rw), np.pi / 2 + 0.15)
    nf = dish.normal(np.array(rw * np.cos(np.pi / 2 + 0.15)), np.array(rw * np.sin(np.pi / 2 + 0.15)))
    lw, _ = reflect_light_loc(far, nf, cam, 150.0)
    focus = dish.polar(np.array(6.5), np.pi / 2)
    scene = {
        "camera": cam,
        "meshes": [{"name": "wood", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.4, "Coat Weight": 0.9, "Coat Roughness": 0.12, "Subsurface Weight": 0.25, "Subsurface Radius": [1.0, 0.5, 0.2], "Subsurface Scale": 0.05}}],
        "lights": [
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": far.tolist(), "size": [340, 150], "sigma": [100, 18], "L": 3.0, "rgb": [1.0, 0.95, 0.87]},
            {"name": "key", "loc": (focus + np.array([-70, -60, 110])).tolist(), "target": focus.tolist(), "size": [70, 70], "watts": 150000, "rgb": [1.0, 0.92, 0.8], "hide_in_gloss": True},
        ],
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.0, "contrast": 1.3, "saturation": 1.08, "black": 0.002, "grain": 1.2, "sharpen": 0.3, "halation": 0.03, "glare": 0.003, "vignette": 0.3})


main()
