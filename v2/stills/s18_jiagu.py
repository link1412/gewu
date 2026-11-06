"""Shot 18: an oracle bone (甲骨): a turtle plastron, its swell the arc, with burn marks, cracks and cut signs.

    python3 -I v2/stills/s18_jiagu.py [preview|mid|final]

Built like the real thing (scales are estimates from general knowledge, not measured):
- the shell surface: a smooth, polished bone with fine pores and the faint sutures between the plates, stained by three thousand
  years of soil, darker in the pits, with chips at the worn places;
- the back side of the divination: bored hollows (钻凿), one oval and one round side by side; heat applied there made the crack
  on the face, a long stem with a side branch: the character 卜 is a picture of it;
- the inscription is cut with a knife: straight strokes in a V groove, a little deeper where the blade entered, with crisp burred
  edges. The signs here are illustrative only: straight-stroke forms in the manner of oracle script, drawn by hand as coordinates,
  not a reading of any real text.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 12.0
RU, RV = 11.5, 24.0
VIEW = view_dir(-90.0 + 6.0, 34.0)
DIST = 44.0
U0, U1, V0, V1 = -9.0, 9.0, -8.0, 7.0
SEED = 18

# Stand-in signs: strokes in a 1 x 1.3 box, each ((x0, y0), (x1, y1)). Illustrative, not a text.
SIGNS = [
    [((0.5, 0.0), (0.5, 1.3)), ((0.5, 0.5), (0.98, 0.26))],  # a stem with a branch (the crack sign)
    [((0.0, 0.2), (1.0, 0.2)), ((0.16, 0.2), (0.16, 1.0)), ((0.84, 0.2), (0.84, 1.0)), ((0.16, 1.0), (0.84, 1.0)), ((0.16, 0.6), (0.84, 0.6))],  # a box with a bar (a sun or a mouth)
    [((0.5, 0.0), (0.1, 0.56)), ((0.5, 0.0), (0.9, 0.56)), ((0.1, 0.56), (0.9, 0.56)), ((0.5, 0.56), (0.5, 1.3)), ((0.1, 1.3), (0.9, 1.3))],  # a roof over a stem
    [((0.15, 0.0), (0.85, 1.3)), ((0.85, 0.0), (0.15, 1.3)), ((0.0, 0.65), (1.0, 0.65))],  # a crossing
    [((0.0, 0.22), (1.0, 0.22)), ((0.5, 0.22), (0.5, 1.3)), ((0.0, 0.8), (1.0, 0.8)), ((0.16, 0.22), (0.16, 0.8)), ((0.84, 0.22), (0.84, 0.8))],  # a tree-like form
    [((0.5, 0.0), (0.5, 1.3)), ((0.1, 0.34), (0.9, 0.34)), ((0.1, 0.34), (0.1, 0.94)), ((0.9, 0.34), (0.9, 0.94)), ((0.1, 0.94), (0.9, 0.94))],  # a stem through a box
    [((0.0, 0.1), (0.46, 0.64)), ((1.0, 0.1), (0.54, 0.64)), ((0.5, 0.6), (0.5, 1.3)), ((0.2, 1.3), (0.8, 1.3))],  # a forked stem
    [((0.14, 0.14), (0.86, 0.14)), ((0.5, 0.14), (0.5, 0.74)), ((0.0, 0.74), (1.0, 0.74)), ((0.3, 0.74), (0.08, 1.3)), ((0.7, 0.74), (0.92, 1.3))],  # a figure
]


def surface(U, V, h=0.0):
    z = -(U**2) / (2 * RU) - (V - 2.0) ** 2 / (2 * RV)
    nx, ny = U / RU, (V - 2.0) / RV
    n = 1.0 / np.sqrt(1.0 + nx**2 + ny**2)
    return np.stack([U + h * nx * n, V + h * ny * n, z + h * n], -1).astype(np.float32)


def carve(strokes, shape, pxcm, rng, depth_map, burr_map, width):
    """Knife strokes: a V groove with a burr; the blade goes in deep and comes out shallow, and the hand wobbles a hair."""
    for p0, p1 in strokes:
        p0, p1 = np.array(p0, float), np.array(p1, float)
        L = np.linalg.norm(p1 - p0)
        n = max(int(L * 40), 6)
        t = np.linspace(0, 1, n)
        d = (p1 - p0) / max(L, 1e-6)
        nrm = np.array([-d[1], d[0]])
        wob = 0.008 * np.cumsum(rng.normal(0, 1, n)) / np.sqrt(n)
        pts = p0 + np.outer(t, p1 - p0) + np.outer(wob, nrm)
        hw = width * (0.32 + 0.68 * np.sin(np.pi * np.clip(t, 0, 1)) ** 0.55) * rng.uniform(0.8, 1.15)
        for i in range(n - 1):
            a = (int(round(pts[i, 0] * pxcm * 16)), int(round(pts[i, 1] * pxcm * 16)))
            b = (int(round(pts[i + 1, 0] * pxcm * 16)), int(round(pts[i + 1, 1] * pxcm * 16)))
            amp = float(0.55 + 0.45 * np.sin(np.pi * t[i]) ** 0.5) * float(1.0 - 0.3 * t[i])
            cv2.line(depth_map, a, b, amp, max(1, int(round(2 * hw[i] * pxcm))), cv2.LINE_AA, shift=4)
    return depth_map


def build(dens, c):
    pxcm = 240.0 * dens
    nx, ny = int((U1 - U0) * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    u = U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = V0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)
    rng = np.random.default_rng(SEED)

    # --- the inscription: columns running down from the top of the picture, in rows of signs
    groove = np.zeros(shape, np.float32)
    S = 0.86  # sign size, cm
    col_x = [c[0] - 3.4, c[0] - 2.25, c[0] + 1.7, c[0] + 2.85]
    order = rng.permutation(len(SIGNS)).tolist()
    used = 0
    for ci, x0 in enumerate(col_x):
        y = c[1] + 2.7 - 0.12 * ci
        for k in range(4 if ci in (0, 3) else 3):
            sign = SIGNS[order[used % len(order)]]
            used += 1
            jit = np.array([rng.normal(0, 0.03), rng.normal(0, 0.03)])
            ang = rng.normal(0, 0.05)
            ca, sa = np.cos(ang), np.sin(ang)
            strokes = []
            for a, b in sign:
                pa = np.array([a[0] - 0.5, 0.65 - a[1]]) * S
                pb = np.array([b[0] - 0.5, 0.65 - b[1]]) * S
                ra = np.array([ca * pa[0] - sa * pa[1], sa * pa[0] + ca * pa[1]]) + np.array([x0, y]) + jit
                rb = np.array([ca * pb[0] - sa * pb[1], sa * pb[0] + ca * pb[1]]) + np.array([x0, y]) + jit
                strokes.append((ra - [U0, V0], rb - [U0, V0]))
            carve(strokes, shape, pxcm, rng, groove, None, 0.013)
            y -= S * 1.5
    # V profile from the distance to the stroke's core
    core = (groove > 0.45).astype(np.uint8)
    dv = cv2.distanceTransform(1 - core, cv2.DIST_L2, 5).astype(np.float32) / pxcm
    amp = cv2.dilate(groove, np.ones((5, 5), np.uint8))
    vee = np.clip(1.0 - dv / 0.016, 0, 1) * amp
    burr = np.exp(-(((dv - 0.021) / 0.008) ** 2)) * blur(amp, 2.0)

    fine = fbm(shape, pxcm, 0.06, 0.5, 2.0, SEED + 2)
    # --- divination: the burn pits and their cracks
    pits = [(c[0] - 0.2, c[1] + 1.15), (c[0] - 0.05, c[1] - 1.45)]
    burn = np.zeros(shape, np.float32)
    crack = np.zeros(shape, np.uint8)
    for bx, by in pits:
        # the heat mark on this face: a small oval scorch where the bore thinned the shell
        r = np.hypot((U - bx) / 0.5, (V - by) / 0.68) * (1.0 + 0.1 * fine)
        burn = np.maximum(burn, sstep(1.55, 0.4, r))
        # the crack: a stem along the shell and a side branch: 卜
        for start, heading, L, hw in (((bx, by + 0.9), -np.pi / 2, 1.75, 0.012), ((bx, by), 0.3, 1.1, 0.009)):
            n = int(L * 70)
            ang = heading
            p = np.array(start, float)
            pts = [p.copy()]
            for _ in range(n):
                ang += rng.normal(0, 0.05)
                p = p + np.array([np.cos(ang), np.sin(ang)]) * (L / n)
                pts.append(p.copy())
            ip = np.round((np.array(pts) - [U0, V0]) * pxcm * 16).astype(np.int32)
            cv2.polylines(crack, [ip], False, 255, max(1, int(round(2 * hw * pxcm))), cv2.LINE_AA, shift=4)
    crk = crack.astype(np.float32) / 255.0

    # --- bone
    pore = fbm(shape, pxcm, 0.01, 0.06, 1.0, SEED + 1)
    slow = fbm(shape, pxcm, 0.6, 7.0, 2.8, SEED + 3)
    stain = rank(0.75 * slow + 0.45 * fine)
    blot = sstep(0.55, 1.0, rank(fbm(shape, pxcm, 0.6, 3.5, 3.0, SEED + 4)))
    # the sutures between plates of the plastron: an irregular seam
    nn = 2200
    us = np.linspace(U0, U1, nn)
    seam_v = c[1] - 3.4 + 0.25 * np.sin(us * 0.8) + 0.05 * np.cumsum(rng.normal(0, 1, nn)) / np.sqrt(nn) * 8
    ip = np.round((np.stack([us, seam_v], 1) - [U0, V0]) * pxcm * 16).astype(np.int32)
    seam = np.zeros(shape, np.uint8)
    cv2.polylines(seam, [ip], False, 255, max(1, int(0.016 * pxcm)), cv2.LINE_AA, shift=4)
    seam = seam.astype(np.float32) / 255.0
    # pits of the old surface: chips and worm-cast
    chips = sstep(0.975, 0.992, rank(fbm(shape, pxcm, 0.02, 0.4, 1.6, SEED + 5)))
    # bone has a long fine grain: noise stretched along the shell
    sh2 = (max(ny // 16, 8), nx)
    long_grain = cv2.resize(fbm(sh2, pxcm, 0.012, 0.2, 1.6, SEED + 6), (nx, ny), interpolation=cv2.INTER_CUBIC)
    long_grain = long_grain / (long_grain.std() + 1e-6)

    ivory = mix(color([0.56, 0.4, 0.2]), color([0.72, 0.58, 0.34]), stain)
    ivory = mix(ivory, color([0.34, 0.19, 0.075]), blot * 0.62)
    ivory = ivory * (1.0 + 0.055 * long_grain[..., None] + 0.025 * pore[..., None])
    col = mix(ivory, color([0.06, 0.03, 0.015]), burn * 0.92)
    col = mix(col, color([0.018, 0.012, 0.008]), crk * 0.95)
    col = mix(col, color([0.16, 0.09, 0.05]), blur(seam, 1.2) * 0.8)
    # soil in the cut: dark earth, plus a trace of red in a few signs (some were filled with cinnabar)
    soil = color([0.045, 0.028, 0.017])
    col = mix(col, soil, vee ** 0.7 * 0.92)
    col = mix(col, col * 0.45, chips * 0.8)

    rough = 0.27 + 0.09 * stain + 0.12 * blot + 0.26 * burn + 0.4 * vee
    h = 0.012 * slow + 0.0005 * fine + 0.00007 * pore - 0.034 * vee + 0.0035 * burr - 0.03 * blur(crk, 1.4) - 0.008 * blur(seam, 1.2) - 0.008 * chips + 0.00028 * long_grain
    P = surface(U, V, h)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s18_jiagu")
    os.makedirs(d, exist_ok=True)
    uu, vv = np.linspace(U0, U1, 500, dtype=np.float32), np.linspace(V0, V1, 500, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = surface(Uc, Vc)
    nrm = np.stack([Uc / RU, (Vc - 2.0) / RV, np.ones_like(Uc)], -1)
    keep = (nrm @ VIEW) > -0.005
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Uc.shape), y.reshape(Uc.shape)
    bad = 10 * (~keep)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.7) ** 2) + bad)
    c = (float(Uc.flat[k]), float(Vc.flat[k]))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=6.0, focus_point=focus)
    print("focus", focus, flush=True)
    P, C, Ro = build(dens, c)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)
    j = np.nanargmin(((x - 0.44) ** 2 + (y - 0.56) ** 2) + bad)
    lw, _ = reflect_light_loc(Pc.reshape(-1, 3)[j], nrm.reshape(-1, 3)[j], cam, 60.0)
    lights = [
        {"name": "rake", "loc": (focus + np.array([-48, 20, 16])).tolist(), "target": focus.tolist(), "size": [9, 9], "watts": 34000, "rgb": [1.0, 0.92, 0.78]},
        {"type": "gradient", "name": "sheen", "loc": lw.tolist(), "target": Pc.reshape(-1, 3)[j].tolist(), "size": [130, 60], "sigma": [30, 6], "L": 0.55, "rgb": [1.0, 0.96, 0.9]},
        {"name": "fill", "loc": (focus + np.array([30, -30, 30])).tolist(), "target": focus.tolist(), "size": [50, 50], "watts": 3000, "rgb": [0.9, 0.95, 1.0], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "bone", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.42, "Subsurface Weight": 0.3, "Subsurface Radius": [1.0, 0.7, 0.45], "Subsurface Scale": 0.05}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 2,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s18_jiagu", scene, q, develop={"exposure": 0.0, "contrast": 1.3, "saturation": 1.03, "black": 0.0015, "grain": 1.2, "sharpen": 0.3, "halation": 0.03, "glare": 0.002, "vignette": 0.4})


main()
