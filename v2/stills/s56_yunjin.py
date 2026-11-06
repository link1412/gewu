"""Shot 19: Nanjing brocade (云锦) laid flat, a roundel of pearls (联珠团窠) woven into an indigo satin; the gold border of the roundel is the arc, and the satin beyond it runs out of focus.

    python3 -I v2/stills/s56_yunjin.py flat                    the loom drawing only, no render: out/v2/s56_yunjin/flat.jpg
    python3 -I v2/stills/s56_yunjin.py [preview|mid|final]

Thread by thread, like s22 (scales estimated, not measured), with its own weave here, from ref/zhuanghua at 100% (reference only, never in the pixels):
- a real brocade's colour lies in long weft floats tied in a twill, so a motif reads as fine diagonal ribs; a tie is the warp showing dark, not a dot of another colour;
- an edge is a saw-tooth, row by row, because each pick stops at its own end; the draft itself wobbles by a thread or two;
- the shading is 晕色: three tones of one dye in bands, with row-by-row interlaced borders;
- dyes are muted, gilt paper is brownish, and nothing is scattered: every leaf sits on a vine.
The cloth lies flat instead of being stretched over a bolster, because a brocade is a flat thing. The roundel, flowers and clouds are ours, in the manner of the pattern books, and copy no textile.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import s22_yunjin as yj
from kit import OUT, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, reflect_light_loc, view_dir

NAME = "s56_yunjin"
SEED = 56
W, EL, DIST = 17.0, 60.0, 48.0
R = 6.75  # the outer edge of the gold border, cm
yj.U0, yj.U1, yj.V0, yj.V1 = -9.6, 9.6, -3.0, 12.5
GROUND, GOLD, WHITE = yj.GROUND, yj.GOLD, yj.WHITE
DX, DY = yj.DX, yj.DY


def disc(m, cx, cy, r, val, n=48):
    a = np.linspace(0, 2 * np.pi, n)
    yj.draw(m, np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1), val)


def cloud(m, cx, cy, s, rng):
    """四合如意云 in gold alone: four ruyi heads round a centre, unequal. Quiet, so that the roundel carries the picture."""
    a0 = rng.normal(0, 0.12)
    for k in range(4):
        yj.draw(m, yj.ruyi(cx, cy, a0 + k * np.pi / 2 + rng.normal(0, 0.05), 0.5 * s * rng.uniform(0.9, 1.1), 0.2 * s * rng.uniform(0.9, 1.1)), GOLD)
    disc(m, cx, cy, 0.085 * s, GROUND)


def flower2(m, cx, cy, size, pal, rng, kind="ruyi"):
    """Three rings of petals, each petal its own length and lean (a draft by hand, not a compass), each shaded in three bands of one dye, in gold outline."""
    rings = {"ruyi": [(8, 1.0, 0.33, 0.0), (8, 0.72, 0.25, 0.5), (6, 0.46, 0.17, 0.0)], "peony": [(9, 1.0, 0.3, 0.0), (7, 0.76, 0.27, 0.4), (5, 0.48, 0.2, 0.15)], "lotus": [(7, 1.0, 0.36, 0.0), (7, 0.7, 0.28, 0.5), (5, 0.42, 0.2, 0.0)]}[kind]
    a0 = rng.uniform(0, 6.28)
    for n, L, w, off in rings:
        for k in rng.permutation(n):
            a = a0 + 2 * np.pi * (k + off) / n + rng.normal(0, 0.035)
            ll, ww = L * size * rng.uniform(0.92, 1.06), w * size * rng.uniform(0.9, 1.1)
            lobes, ph = int(rng.integers(2, 5)), rng.uniform(0, 6)
            for sc, val in ((1.045, GOLD), (1.0, pal), (0.76, pal + 1), (0.5, pal + 2)):
                if kind == "ruyi":
                    yj.draw(m, yj.ruyi(cx, cy, a, ll, ww, scale=sc), val)
                else:
                    yj.draw(m, yj.petal_outline(cx, cy, a, ll, ww, scale=sc, lobes=lobes, phase=ph), val)
    disc(m, cx, cy, 0.2 * size, GOLD)
    disc(m, cx, cy, 0.165 * size, pal + 1)
    for k in range(13):
        b = rng.uniform(0, 6.28)
        r_ = 0.14 * size * np.sqrt(rng.uniform(0.05, 1.0))
        disc(m, cx + r_ * np.cos(b), cy + r_ * np.sin(b), 0.016 * size * rng.uniform(0.8, 1.4), GOLD, 16)


def vine2(m, p0, p1, bow, rng, idx):
    """A gold scroll, and its leaves in colour, in gold edge, of unequal size at unequal gaps; a curl now and then. Nothing floats free of it."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    t = np.linspace(0, 1, 160)[:, None]
    d = p1 - p0
    n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    c = p0 + d * t + n * (bow * np.sin(np.pi * t) + 0.12 * np.sin(np.pi * 3 * t + rng.uniform(0, 6)))
    ip = np.round((c - [yj.U0, yj.V0]) / [DX, DY] * 16).astype(np.int32)
    cv2.polylines(m, [ip], False, GOLD, 3, cv2.LINE_8, shift=4)
    k = int(rng.integers(8, 18))
    side = rng.choice([-1, 1])
    while k < 150:
        tang = c[k + 1] - c[k]
        a = np.arctan2(tang[1], tang[0])
        side = -side if rng.random() < 0.8 else side
        if rng.random() < 0.3:
            end, ea = yj.tendril(m, c[k, 0], c[k, 1], a + side * 0.5, rng.uniform(0.34, 0.56), side, rng)
        else:
            name = rng.choice(["jade", "jade", "azure", "rose", "amber"], p=[0.4, 0.2, 0.18, 0.12, 0.1])
            L = rng.uniform(0.42, 0.82)
            b = a + side * rng.uniform(0.5, 0.95)
            lo = int(rng.integers(2, 4))
            ph = rng.uniform(0, 6)
            for sc, val in ((1.09, GOLD), (1.0, idx[name]), (0.62, idx[name] + 1)):
                yj.draw(m, yj.petal_outline(c[k, 0], c[k, 1], b, L, L * 0.3, scale=sc, lobes=lo, phase=ph), val)
        k += int(rng.integers(9, 26))


def border(m, idx):
    """The gold border of the roundel: a band, a ring of pearls, a blue line between gold ones."""
    disc(m, 0, 0, R, GOLD, 360)
    disc(m, 0, 0, R - 0.2, GROUND, 360)
    n_p = 56
    for k in range(n_p):
        a = 2 * np.pi * (k + 0.5) / n_p
        x, y = (R - 0.42) * np.cos(a), (R - 0.42) * np.sin(a)
        disc(m, x, y, 0.21, GOLD)
        disc(m, x, y, 0.16, WHITE)
        disc(m, x, y, 0.07, idx["azure"] + 1)
    disc(m, 0, 0, R - 0.72, GOLD, 360)
    disc(m, 0, 0, R - 0.82, idx["azure"], 360)
    disc(m, 0, 0, R - 0.92, GOLD, 360)
    disc(m, 0, 0, R - 0.98, GROUND, 360)


def pattern():
    nx, ny = int((yj.U1 - yj.U0) / DX), int((yj.V1 - yj.V0) / DY)
    m = np.zeros((ny, nx), np.uint8)
    tab, idx = yj.table()
    # dyes as they are, not as a screen shows them: muted, and the gilt paper brown
    for name, tones in {"rose": [(0.30, 0.012, 0.04), (0.52, 0.05, 0.075), (0.74, 0.22, 0.2)], "azure": [(0.012, 0.045, 0.2), (0.04, 0.14, 0.4), (0.24, 0.42, 0.62)], "amber": [(0.46, 0.14, 0.012), (0.66, 0.32, 0.04), (0.82, 0.56, 0.18)], "jade": [(0.014, 0.10, 0.06), (0.05, 0.24, 0.13), (0.27, 0.46, 0.28)]}.items():
        tab[idx[name] : idx[name] + 3] = tones
    tab[GROUND] = (0.008, 0.018, 0.09)  # a little lighter than s22: this satin is seen, not buried under gold
    tab[GOLD] = (0.86, 0.60, 0.25)
    tab[WHITE] = (0.72, 0.68, 0.56)
    rng = np.random.default_rng(SEED)

    # --- the satin beyond the roundel: gold clouds in staggered rows, as on the loom's repeat, but this one was drawn by a hand
    for iy, v in enumerate(np.arange(-3.2, 13.2, 1.72)):
        for u in np.arange(-10.4, 10.6, 2.5):
            x, y = u + (1.25 if iy % 2 else 0.0) + rng.normal(0, 0.05), v + rng.normal(0, 0.05)
            if np.hypot(x, y) > R + 0.9:
                cloud(m, x, y, 0.82, rng)
    outer = m.copy()

    # --- the roundel: a gold scroll on the satin; six flowers round one, each its own colours and its own kind (逐花异色)
    NF = 6
    rf = 3.95
    fl = [(0.0, 0.0, 2.45, "rose", "ruyi")]
    pals = ["azure", "amber", "jade", "azure", "amber", "rose"]
    kinds = ["peony", "lotus", "peony", "lotus", "peony", "lotus"]
    for k in range(NF):
        a = np.pi / 2 + 2 * np.pi * k / NF + rng.normal(0, 0.02)
        fl.append((rf * np.cos(a), rf * np.sin(a), 1.42 * rng.uniform(0.95, 1.05), pals[k], kinds[k]))
    for k in range(NF):
        a, b = fl[1 + k], fl[1 + (k + 1) % NF]
        vine2(m, a[:2], b[:2], rng.uniform(0.5, 0.8), rng, idx)
        vine2(m, a[:2], b[:2], -rng.uniform(0.3, 0.55), rng, idx)
        vine2(m, fl[0][:2], a[:2], 0.75 * (-1) ** k, rng, idx)
    for x, y, s_, name, kind in fl:
        flower2(m, x, y, s_, idx[name], rng, kind)

    # anything that strayed past the border goes; the border lies on top
    rr = np.hypot(*np.meshgrid(yj.U0 + (np.arange(nx) + 0.5) * DX, yj.V0 + (np.arange(ny) + 0.5) * DY))
    m[rr > R - 0.98] = GROUND
    keep = rr > R + 0.1
    m[keep] = outer[keep]
    ring = np.zeros_like(m)
    border(ring, idx)
    use = (rr <= R + 0.02) & (rr > R - 0.99)
    m[use] = ring[use]

    # the hand and the loom: the draft wobbles by a thread or two, and each pick stops at its own end. So every edge is a saw-tooth and two tones interlace row by row
    wob = fbm((ny, nx), 1.0, 8.0, 80.0, 2.8, SEED + 40)
    rowa = np.random.default_rng(SEED + 41).normal(0, 0.42, ny)
    rowa = rowa + (np.arange(ny) % 2) * 1.0 - 0.5
    mx, my = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    mx = mx + 1.5 * wob / max(float(np.abs(wob).max()), 1e-3) + rowa[:, None].astype(np.float32)
    my = my + 1.3 * np.roll(wob, 37, 1) / max(float(np.abs(wob).max()), 1e-3)
    m = cv2.remap(m, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE)
    return m, tab


def weave2(U, V, M, tab, pxcm, shape):
    """s22's weave changed after ref/zhuanghua: long weft floats tied in a twill that shows as ribs; a tie is the warp, dark, in the colour of the ground, no dots of another hue."""
    U0, V0 = yj.U0, yj.V0
    cols, rows = M.shape[1], M.shape[0]
    wu = 0.018 * fbm(shape, pxcm, 0.3, 2.0, 2.6, SEED + 1) + 0.0035 * fbm(shape, pxcm, 0.05, 0.3, 2.0, SEED + 2)
    wv = 0.024 * fbm(shape, pxcm, 0.3, 2.0, 2.6, SEED + 3) + 0.0045 * fbm(shape, pxcm, 0.05, 0.3, 2.0, SEED + 4)
    cu, cv_ = (U - U0 + wu) / DX, (V - V0 + wv) / DY
    i, j = np.floor(cu).astype(np.int32), np.floor(cv_).astype(np.int32)
    fu, fv = (cu - i).astype(np.float32), (cv_ - j).astype(np.float32)
    ii, jj = np.clip(i, 0, cols - 1), np.clip(j, 0, rows - 1)
    kind = M[jj, ii]
    is_ground, is_gold = kind == GROUND, kind == GOLD
    is_silk = ~is_ground & ~is_gold
    rng = np.random.default_rng(SEED + 5)
    row_tone = rng.normal(0, 1, rows + 2).astype(np.float32)
    col_tone = rng.normal(0, 1, cols + 2).astype(np.float32)
    across_w = np.sqrt(np.maximum(1.0 - (2 * fv - 1.0) ** 2, 0.0))
    across_u = np.sqrt(np.maximum(1.0 - (2 * fu - 1.0) ** 2, 0.0))
    SIL, GLD = 8, 11
    ps = np.mod(ii + 3 * jj, SIL)
    pg = np.mod(ii + 4 * jj, GLD)
    tie_silk = (ps == 0) & is_silk
    tie_gold = (pg == 0) & is_gold
    tie_ground = (np.mod(2 * ii + jj, 5) == 0) & is_ground
    # how far along its float a point is, 0..1: a float rises from one tie and sinks into the next
    along = np.where(is_gold, (pg + fu) / GLD, (ps + fu) / SIL)
    bow = np.sin(np.pi * np.clip(along, 0, 1)) ** 0.5
    H = 0.0135
    h = np.zeros(shape, np.float32)
    weft = ~is_ground & ~tie_silk & ~tie_gold
    h[weft] = (H * (0.58 + 0.42 * across_w) * (0.82 + 0.18 * bow) * (1.0 + 0.06 * row_tone[jj]))[weft]
    fib = fbm(shape, pxcm, 0.01, 0.06, 1.3, SEED + 6)
    silk = weft & ~is_gold
    h[silk] += (0.0006 * fib)[silk]
    goldp = weft & is_gold
    h[goldp] = (H * (0.72 + 0.28 * np.sqrt(np.maximum(1.0 - np.abs(2 * fv - 1.0) ** 4, 0.0))) * (0.86 + 0.14 * bow) + 0.0007 * fib)[goldp]
    ties = tie_silk | tie_gold
    h[ties] = (H * (0.4 + 0.4 * across_u))[ties]
    warp = is_ground & ~tie_ground
    h[warp] = (0.72 * H * (0.55 + 0.45 * across_u) * (1.0 + 0.04 * col_tone[ii]))[warp]
    h[tie_ground] = (0.55 * H * (0.5 + 0.5 * across_w))[tie_ground]

    col = tab[kind]
    # one pick is a little darker than the next, a dye lot changes across the width, and it faded where the cloth lay in the light
    slub = 1.0 + 0.1 * fbm(shape, pxcm, 0.05, 0.5, 1.8, SEED + 9)
    tone = (1.0 + 0.1 * row_tone[jj]) * slub
    tone2 = 1.0 + 0.1 * col_tone[ii]
    col = col * np.where(is_ground, tone2, tone)[..., None]
    col = np.where(ties[..., None], col * 0.42 + tab[GROUND] * 0.5, col)
    gap = np.where(is_ground, across_u, across_w)
    col = col * (0.58 + 0.42 * gap**0.6)[..., None]
    age = rank(fbm(shape, pxcm, 0.6, 5.0, 2.8, SEED + 7))
    rub = sstep(0.68, 0.92, age) * sstep(0.25, 0.8, rank(fbm(shape, pxcm, 0.02, 0.2, 1.7, SEED + 8)))
    metal = np.zeros(shape, np.float32)
    metal[goldp] = 0.92
    metal = metal * (1.0 - rub * 0.8)
    col = mix(col, col * np.array([0.72, 0.58, 0.36], np.float32), rub[..., None] * is_gold[..., None])
    fade = rank(fbm(shape, pxcm, 1.2, 8.0, 3.0, SEED + 10))
    col = col * (0.82 + 0.26 * fade)[..., None]
    rough = np.full(shape, 0.46, np.float32)
    rough[is_gold] = 0.31
    rough[is_ground] = 0.36
    return h, col, rough + 0.12 * rub, metal


def flat_view():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    m, tab = pattern()
    im = (np.clip(tab[m], 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)[::-1]
    im = cv2.resize(im, (im.shape[1] * 2, im.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
    p = os.path.join(d, "flat.jpg")
    cv2.imwrite(p, cv2.resize(im[..., ::-1], (1500, int(1500 * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(p)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "flat":
        flat_view()
        return
    dens = {"preview": 0.55, "mid": 0.75, "final": 1.0}[q]
    pxcm = 300.0 * dens
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    th = np.linspace(0, 2 * np.pi, 1440)
    outline = np.stack([R * np.cos(th), R * np.sin(th), np.zeros_like(th)], 1)
    focus = np.array([0.0, R - 3.4, 0.0])
    cam, sag = fit_arc(outline, view_dir(-90.0, EL), W, DIST, apex=(0.5, 0.34), target0=(0.0, 2.0, 0.0), aperture_mm=15.0, focus_point=focus)
    print("sag", round(float(sag), 3), flush=True)

    U0, U1, V0, V1 = yj.U0, yj.U1, yj.V0, yj.V1
    nx, ny = int((U1 - U0) * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M", flush=True)
    U, V = np.meshgrid(U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, V0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    m, tab = pattern()
    h, col, rough, metal = weave2(U, V, m, tab, pxcm, shape)
    # the cloth lies on a table, not quite flat: slow swells, and one long soft fold across the far side
    swell = 0.05 * fbm(shape, pxcm, 4.0, 14.0, 3.6, SEED + 1)
    fold_axis = 0.94 * (V - 9.0) - 0.34 * U + 0.5 * fbm(shape, pxcm, 3.0, 12.0, 3.2, SEED + 2)
    fold = 0.1 * np.exp(-((fold_axis / 2.4) ** 2))
    z = swell + fold + h
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=np.stack([U, V, z], -1).astype(np.float32), col=np.clip(col, 0, 1).astype(np.float32), rough=np.clip(rough, 0.05, 1).astype(np.float32), metal=metal.astype(np.float32))

    lw, _ = reflect_light_loc(focus, np.array([0.0, 0.0, 1.0]), cam, 70.0)
    scene = {
        "camera": cam,
        "meshes": [{"name": "brocade", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": 0.45, "Sheen Weight": 0.12}}],
        "lights": [
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": focus.tolist(), "size": [190, 120], "sigma": [70, 22], "L": 0.27, "rgb": [1.0, 0.95, 0.87]},
            {"name": "rake", "loc": (focus + np.array([-44, 34, 26])).tolist(), "target": focus.tolist(), "size": [14, 14], "watts": 56000, "rgb": [1.0, 0.93, 0.82]},
            {"name": "fill", "loc": (focus + np.array([26, -34, 40])).tolist(), "target": focus.tolist(), "size": [60, 60], "watts": 9000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
        ],
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.2, "contrast": 1.26, "saturation": 1.1, "black": 0.0015, "grain": 1.2, "sharpen": 0.3, "halation": 0.04, "glare": 0.003, "vignette": 0.42})


main()
