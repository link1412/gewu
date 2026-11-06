"""Shot 22: Nanjing brocade (云锦): gold and silk floats, thread by thread, over a bolster whose swell is the arc.

    python3 -I v2/stills/s22_yunjin.py [preview|mid|final]

Built like the real thing (scales are estimates from general knowledge, not measured):
- the pattern is decided on the loom's grid: each crossing of a warp and a weft is one cell of a drawing, so outlines step thread by
  thread;
- flowers are in floats of coloured weft, with each flower a different set of colours (逐花异色) in three tones laid side by side
  (晕色), tied down at intervals by a fine warp; the vines and the leaves are flat gold strips (片金); the ground is a satin of
  indigo warp;
- each thread has a round section, its own small difference in colour, and does not run ruler-straight; the gold is a gilded paper
  strip that takes small creases and has worn through in places to its silk core.
The drawing is ours, in the manner of the peony-scroll brocades. It is not a copy of any textile.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 7.5
RU, RV = 21.0, 13.0
VIEW = view_dir(-90.0, 26.0)
DIST = 34.0
U0, U1, V0, V1 = -5.6, 5.6, -3.6, 6.0
DX, DY = 0.0225, 0.0285  # warp and weft spacing, cm
SEED = 22

GROUND, GOLD, WHITE = 0, 1, 2
PALETTES = {
    "rose": [(0.38, 0.006, 0.035), (0.68, 0.035, 0.09), (0.86, 0.22, 0.26)],
    "azure": [(0.006, 0.035, 0.24), (0.025, 0.14, 0.52), (0.2, 0.46, 0.8)],
    "amber": [(0.56, 0.14, 0.006), (0.8, 0.34, 0.03), (0.9, 0.6, 0.15)],
    "jade": [(0.008, 0.13, 0.06), (0.05, 0.32, 0.13), (0.3, 0.56, 0.28)],
}


def table():
    t = [(0.004, 0.009, 0.05), (1.0, 0.72, 0.29), (0.8, 0.76, 0.66)]
    idx = {}
    for name, tones in PALETTES.items():
        idx[name] = len(t)
        t.extend(tones)
    return np.array(t, np.float32), idx


def petal_outline(cx, cy, ang, L, w, scale=1.0, lobes=3, phase=0.0):
    """A petal: narrow at its foot, wide at the shoulder, its tip scalloped."""
    t = np.linspace(0, 1, 90)
    half = w * scale * np.sin(np.pi * t**0.62) ** 0.72
    tip = 1.0 + 0.055 * np.cos(2 * np.pi * lobes * np.linspace(-0.5, 0.5, 180) + phase)
    left = np.stack([L * scale * t, half], 1)
    right = np.stack([L * scale * t[::-1], -half[::-1]], 1)
    p = np.concatenate([left, right], 0)
    p[:, 0] *= tip
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([cx + c * p[:, 0] - s * p[:, 1], cy + s * p[:, 0] + c * p[:, 1]], 1)


def draw(m, pts, val):
    cv2.fillPoly(m, [np.round((pts - [U0, V0]) / [DX, DY] * 16).astype(np.int32)], int(val), cv2.LINE_8, shift=4)


def ruyi(cx, cy, ang, L, w, scale=1.0):
    """A heart-shaped petal with a turned-over tip: the ruyi head of 宝相花. Symmetric about its axis."""
    t = np.linspace(0.0, 1.0, 120)
    # half outline: foot, belly, a notch at the shoulder, a pointed cusp
    x = L * scale * (t + 0.0 * t)
    half = w * scale * (np.sin(np.pi * t**0.7) ** 0.65 * (1.0 + 0.26 * np.sin(np.pi * np.clip((t - 0.45) / 0.55, 0, 1)) ** 2))
    half = half * (1.0 - 0.28 * np.exp(-(((t - 0.73) / 0.05) ** 2)))
    p = np.concatenate([np.stack([x, half], 1), np.stack([x[::-1], -half[::-1]], 1)], 0)
    c, s_ = np.cos(ang), np.sin(ang)
    return np.stack([cx + c * p[:, 0] - s_ * p[:, 1], cy + s_ * p[:, 0] + c * p[:, 1]], 1)


def flower(m, cx, cy, size, pal, rng):
    """宝相花: a formal, symmetric flower of ruyi petals in three rings, each petal outlined in gold and shaded from a dark edge to a
    pale heart in three tones. Hand-drawn in spirit: each ring turns a little off true."""
    rings = [(8, 1.0, 0.33, 0.0), (8, 0.74, 0.25, 0.5), (8, 0.5, 0.17, 0.0)]
    for n, L, w, off in rings:
        for k in range(n):
            a = 2 * np.pi * (k + off) / n + rng.normal(0, 0.008)
            for sc, val in ((1.05, GOLD), (1.0, pal), (0.82, pal + 1), (0.62, pal + 2), (0.34, WHITE)):
                draw(m, ruyi(cx, cy, a, L * size, w * size, scale=sc), val)
    a = np.linspace(0, 2 * np.pi, 48)
    for r, val in ((0.25, GOLD), (0.21, pal), (0.15, GOLD)):
        draw(m, np.stack([cx + r * size * np.cos(a), cy + r * size * np.sin(a)], 1), val)
    for k in range(16):
        b = 2 * np.pi * k / 16
        rs = 0.018 * size
        draw(m, np.stack([cx + 0.19 * size * np.cos(b) + rs * np.cos(a), cy + 0.19 * size * np.sin(b) + rs * np.sin(a)], 1), GOLD)
    for k in range(8):
        b = 2 * np.pi * (k + 0.5) / 8
        draw(m, ruyi(cx, cy, b, 0.13 * size, 0.04 * size), pal + 2)


def tendril(m, x, y, ang, size, sign, rng):
    """A gold curl: a spiral that tightens to a small head, line a few threads wide."""
    th = np.linspace(0, rng.uniform(4.2, 6.6), 90)
    r = size * np.exp(-th * 0.33)
    a = ang + sign * th
    dx = np.cumsum(r * np.cos(a)) * (th[1] - th[0])
    dy = np.cumsum(r * np.sin(a)) * (th[1] - th[0])
    c = np.stack([x + dx, y + dy], 1)
    ip = np.round((c - [U0, V0]) / [DX, DY] * 16).astype(np.int32)
    cv2.polylines(m, [ip], False, GOLD, 2, cv2.LINE_8, shift=4)
    return c[-1], a[-1]


def leaf(m, x, y, ang, L, val, val2=None):
    p = petal_outline(x, y, ang, L, L * 0.34, lobes=2)
    draw(m, p, val)
    if val2 is not None:
        draw(m, petal_outline(x, y, ang, L, L * 0.34, scale=0.62, lobes=2), val2)


def vine(m, p0, p1, bow, rng, idx):
    """A gold scroll between flowers: a curve with a leaf or a curl every so often."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    t = np.linspace(0, 1, 160)[:, None]
    d = p1 - p0
    n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    c = p0 + d * t + n * (bow * np.sin(np.pi * t))
    ip = np.round((c - [U0, V0]) / [DX, DY] * 16).astype(np.int32)
    cv2.polylines(m, [ip], False, GOLD, 4, cv2.LINE_8, shift=4)
    for k in range(6, 152, 11):
        tang = c[k + 1] - c[k]
        a = np.arctan2(tang[1], tang[0])
        side = 1 if (k // 11) % 2 == 0 else -1
        if (k // 11) % 3 == 2:
            end, ea = tendril(m, c[k, 0], c[k, 1], a + side * 0.5, rng.uniform(0.42, 0.62), side, rng)
            leaf(m, end[0], end[1], ea, rng.uniform(0.18, 0.28), GOLD)
        else:
            leaf(m, c[k, 0], c[k, 1], a + side * rng.uniform(0.55, 0.9), rng.uniform(0.3, 0.46), GOLD)


def pattern(c):
    nx, ny = int((U1 - U0) / DX), int((V1 - V0) / DY)
    m = np.zeros((ny, nx), np.uint8)
    t, idx = table()
    rng = np.random.default_rng(SEED)
    fl = [
        (c[0] - 0.05, c[1] + 0.3, 2.05, "rose"),
        (c[0] - 4.9, c[1] + 2.1, 1.7, "azure"),
        (c[0] + 4.65, c[1] + 1.95, 1.8, "amber"),
        (c[0] + 2.55, c[1] - 3.2, 1.55, "azure"),
        (c[0] - 2.9, c[1] - 3.15, 1.6, "jade"),
        (c[0] + 0.1, c[1] + 4.65, 1.5, "amber"),
    ]
    # gold scrolls first, so that flowers sit over them
    for i, a in enumerate(fl):
        for b in fl[i + 1 :]:
            dd = np.hypot(a[0] - b[0], a[1] - b[1])
            if dd < 6.4:
                vine(m, a[:2], b[:2], rng.choice((-1, 1)) * 0.8, rng, idx)
                vine(m, a[:2], b[:2], rng.choice((-1, 1)) * 1.7, rng, idx)
    # small leaves of colour among the gold
    for _ in range(60):
        x, y = rng.uniform(U0, U1), rng.uniform(V0, V1)
        if min(np.hypot(x - f[0], y - f[1]) - f[2] for f in fl) > 0.08:
            name = rng.choice(["jade", "azure", "rose"])
            leaf(m, x, y, rng.uniform(0, 6.28), rng.uniform(0.32, 0.56), idx[name] + 1, idx[name] + 2)
    for x, y, s, name in fl:
        flower(m, x, y, s, idx[name], rng)
    return m, t


def build(dens, c):
    pxcm = 340.0 * dens
    nx, ny = int((U1 - U0) * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    U, V = np.meshgrid(U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, V0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    M, tab = pattern(c)
    h, col, rough, metal = weave(U, V, M, tab, pxcm, shape)

    # the bolster: a low swell with soft dents in the cloth
    dents = 0.05 * fbm(shape, pxcm, 1.5, 9.0, 3.4, SEED + 9)
    z = -(U**2) / (2 * RU) - (V - 2.2) ** 2 / (2 * RV) + dents + h
    P = np.stack([U, V, z], -1).astype(np.float32)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), metal.astype(np.float32)


def weave(U, V, M, tab, pxcm, shape):
    """The cloth from a loom drawing M: thread height, colour, roughness and metal per vertex. U, V and the drawing share the U0, V0, DX, DY of this module."""
    cols, rows = M.shape[1], M.shape[0]

    # threads wander a little; cloth is not a ruler
    wu = 0.018 * fbm(shape, pxcm, 0.3, 2.0, 2.6, SEED + 1) + 0.0035 * fbm(shape, pxcm, 0.05, 0.3, 2.0, SEED + 2)
    wv = 0.024 * fbm(shape, pxcm, 0.3, 2.0, 2.6, SEED + 3) + 0.0045 * fbm(shape, pxcm, 0.05, 0.3, 2.0, SEED + 4)
    cu, cv = (U - U0 + wu) / DX, (V - V0 + wv) / DY
    i, j = np.floor(cu).astype(np.int32), np.floor(cv).astype(np.int32)
    fu, fv = (cu - i).astype(np.float32), (cv - j).astype(np.float32)
    ii, jj = np.clip(i, 0, cols - 1), np.clip(j, 0, rows - 1)
    kind = M[jj, ii]
    is_ground = kind == GROUND
    is_gold = kind == GOLD

    rng = np.random.default_rng(SEED + 5)
    row_tone = rng.normal(0, 1, rows + 2).astype(np.float32)
    col_tone = rng.normal(0, 1, cols + 2).astype(np.float32)
    # the section of one thread across its width
    across_w = np.sqrt(np.maximum(1.0 - (2 * fv - 1.0) ** 2, 0.0))
    across_u = np.sqrt(np.maximum(1.0 - (2 * fu - 1.0) ** 2, 0.0))

    # silk: a weft float tied by a warp every 5 ends, staggered by row
    tie_silk = ((ii + 3 * jj) % 5 == 0) & ~is_ground & ~is_gold
    # gold: a float tied every 7 ends, in a twill
    tie_gold = ((ii + 2 * jj) % 7 == 0) & is_gold
    # ground: a satin of warp, tied by a weft on every fifth crossing
    tie_ground = ((2 * ii + jj) % 5 == 0) & is_ground

    twist = np.sin(2 * np.pi * (fu * 0.5 + cu * 0.42 + fv * 1.5)) * across_w
    H = 0.0135
    h = np.zeros(shape, np.float32)
    # weft floats (silk, gold)
    weft = (~is_ground) & ~tie_silk & ~tie_gold
    h[weft] = (H * (0.58 + 0.42 * across_w) * (1.0 + 0.05 * row_tone[jj]))[weft]
    silk = weft & ~is_gold
    h[silk] += (0.0006 * twist)[silk]
    # gold strip: flat on top, small creases
    crease = fbm(shape, pxcm, 0.012, 0.09, 1.3, SEED + 6)
    goldp = weft & is_gold
    h[goldp] = (H * (0.72 + 0.28 * np.sqrt(np.maximum(1.0 - np.abs(2 * fv - 1.0) ** 4, 0.0))) + 0.00065 * crease)[goldp]
    # tying warps
    ties = tie_silk | tie_gold
    h[ties] = (H * (0.45 + 0.5 * across_u))[ties]
    # ground satin warp
    warp = is_ground & ~tie_ground
    h[warp] = (0.72 * H * (0.55 + 0.45 * across_u) * (1.0 + 0.04 * col_tone[ii]))[warp]
    h[tie_ground] = (0.55 * H * (0.5 + 0.5 * across_w))[tie_ground]
    # floats dip on their way down at both ends of a cell, a hint of the sett
    h = h - 0.0012 * (1.0 - across_u) * weft

    # colour per thread
    col = tab[kind]
    tone = 1.0 + 0.085 * row_tone[jj]
    tone2 = 1.0 + 0.1 * col_tone[ii]
    col = col * np.where(is_ground, tone2, tone)[..., None]
    col[ties] = np.array([0.5, 0.33, 0.13], np.float32) * (0.75 + 0.25 * across_u[ties, None])
    # silk has a fibre sheen, dark in the gaps between threads
    gap = np.where(is_ground, across_u, across_w)
    col = col * (0.42 + 0.58 * gap**0.6)[..., None]

    # age: dust, wear; gold has rubbed through to its yellow core at the high places
    age = rank(fbm(shape, pxcm, 0.6, 5.0, 2.8, SEED + 7))
    rub = sstep(0.72, 0.94, age) * sstep(0.25, 0.8, rank(fbm(shape, pxcm, 0.02, 0.2, 1.7, SEED + 8)))
    metal = np.zeros(shape, np.float32)
    metal[goldp] = 1.0
    metal = metal * (1.0 - rub * 0.85)
    col = mix(col, col * np.array([0.82, 0.7, 0.42], np.float32), rub[..., None] * is_gold[..., None])
    col = col * (0.88 + 0.12 * (1.0 - age))[..., None]

    rough = np.full(shape, 0.44, np.float32)
    rough[is_gold] = 0.27
    rough[is_ground] = 0.36
    rough = rough + 0.1 * rub
    return h, col, rough, metal


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.55, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s22_yunjin")
    os.makedirs(d, exist_ok=True)
    uu, vv = np.linspace(U0, U1, 500, dtype=np.float32), np.linspace(V0, V1, 500, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = np.stack([Uc, Vc, -(Uc**2) / (2 * RU) - (Vc - 2.2) ** 2 / (2 * RV)], -1)
    nrm = np.stack([Uc / RU, (Vc - 2.2) / RV, np.ones_like(Uc)], -1)
    keep = (nrm @ VIEW) > -0.005
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Uc.shape), y.reshape(Uc.shape)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.7) ** 2) + 10 * (~keep))
    c = (float(Uc.flat[k]), float(Vc.flat[k]))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=5.5, focus_point=focus)
    print("c", c, "focus", focus, flush=True)
    P, C, Ro, Me = build(dens, c)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=Me)
    j = np.nanargmin(((x - 0.5) ** 2 + (y - 0.6) ** 2) + 10 * (~keep))
    lw, _ = reflect_light_loc(Pc.reshape(-1, 3)[j], nrm.reshape(-1, 3)[j], cam, 60.0)
    lights = [
        {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": Pc.reshape(-1, 3)[j].tolist(), "size": [150, 90], "sigma": [46, 9], "L": 0.62, "rgb": [1.0, 0.95, 0.87]},
        {"name": "rake", "loc": (focus + np.array([-36, 26, 22])).tolist(), "target": focus.tolist(), "size": [10, 10], "watts": 26000, "rgb": [1.0, 0.93, 0.82]},
        {"name": "fill", "loc": (focus + np.array([20, -30, 26])).tolist(), "target": focus.tolist(), "size": [46, 46], "watts": 4200, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "brocade", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": 0.45, "Sheen Weight": 0.12}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s22_yunjin", scene, q, develop={"exposure": 0.0, "contrast": 1.28, "saturation": 1.08, "black": 0.0015, "grain": 1.2, "sharpen": 0.3, "halation": 0.04, "glare": 0.003, "vignette": 0.45})


if __name__ == "__main__":
    main()
