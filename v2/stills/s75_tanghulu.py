"""Shot 75: 糖葫芦, a still. SHELVED after the last version: not in cut.json, not in the film. Kept as it stood.
The near hawthorn of a string, its shoulder across the whole frame as the film's arc, in focus from the arc to the foreground, its dried calyx on the face; a clear sheet of sugar growing from a ridge of sugar on the left of the arc; the next fruit out of focus at the right edge; a market's lights.

    python3 -I v2/stills/s75_tanghulu.py look TAG k=v,k=v [preview|mid|final]     out/v2/s75_tanghulu/TAG.jpg

Targets: ref/tanghulu/research_photos/photo_04 (the sugar shards), photo_01 for skin and sugar, photo_09 for the calyx. What makes it a hawthorn and not an apple, found by asking a reader with no context after each change (apple 70 % down to 15 %, hawthorn 25 % up to 55 %; the same reader gives real photos 60-70 %):
- a nearly flat end with a torn star of dried sepals. A wide basin with radial wrinkles is an apple's;
- dense, unequal, pale lenticels at the true scale, about 1.3 % of the fruit's width (read off photo_04). Finer ones read as an apple;
- several fruits in a row on one stick, which also gives the scale. A stick alone did not: toffee apples have sticks.
What makes the sugar hard and not wet: thin, following the skin; small ripples rather than big swells; hairline cracks and crazing. Few bubbles on the fruit: round glints read as water.
Flaws: the fruit is lopsided, knocked, creased; a scab, a healed scratch, insect pits, a bruise; a chip and thin places in the sugar; dust.

The light is the lychee's (git cfce37d), turned to the other side. The softbox is split: one lamp lights the skin and is not seen in gloss, a second, soft-edged, is the highlight and lights nothing. The low lamp must be hidden in transmission as well as in gloss: seen through the sugar it was a white blot.
The sheet is truly clear: it shows what stands behind it, the plate, bent. The plate and the sky must not be confused: kit's sky is seen in transmission unless in_transmission is false, and it blocks the environment.

Mesh notes: a grid's normal is row direction x column direction. Sky meshes share one file per shot (sky.npz), so renders with different skies must not run at once.

ESTIMATES, none measured except where said: all sizes; sugar IOR 1.5 (no measured value found); absorption; all lights; colours read by eye from the photos, then adjusted.
STAND-INS:
- the background is a painted plate seen by the camera and through glass, not lit lights through a lens: Cycles' aperture is a perfect disc, so the rim, the cat's eyes, the onion rings and the lateral colour are painted by rule. Its reflections come from separate spheres far behind;
- two sugars: the sheet and the bridge absorb more than the coat on the fruit (SIGMA_SHEET, SIGMA), so that the sheet is gold and the fruit's colour stays. One sugar would have one value;
- the dark flow is painted into the skin; shadow rays pass the sugar unbent, so it casts no caustics;
- the sheet is a separate solid that runs into the fruit's sugar, not one body with it; the coat's meniscus along their join hides this;
- the depth of field (ap = 1) is that of focus stacking, not of one exposure.

Known faults of the last version, seen at 100 %: a grey, metallic stretch along the sheet's upper edge; the sheet's amber too even; lenticels flat and alike.
Found by switching things off (the `off` and `sheet` options): a pale band under the sheet was neither the sugar's thickness nor any lamp but the room's bright wall, seen through the wedge at the sheet's root. A flag sized from the frame shrinks when the camera moves in, so its size is fixed and the wall is dim.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.spatial import cKDTree

from kit import OUT, _cam_axes, color, frame_camera, room_env, shoot, sstep

NAME = "s75_tanghulu"
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(OUT, NAME)
SHP = os.path.join(HERE, "s75_shader.py")

P0 = dict(off=0, sheet=1, W=2.15, cx=0.57, by=0.14, el=6.0, dist=14.0, ap=1.0, dn=1, zw=0.0, ztx=0.0, ztz=0.0, nrows=0, cells=900000, bl=0.52, bx=-0.4, bz=1.03, back=0.3, wall=26.0, h=0.034, a=1.66, c=1.48, tilt=20.0, roll=3.0, row=1, bub=700, sbub=420, sun=600.0, spp=0)
SIGMA = (0.25, 0.9, 2.6)  # per cm, by eye: nearly clear on the fruit (photo_04)
SIGMA_SHEET = (0.4, 1.7, 5.4)  # per cm, by eye: pale gold where the sheet is thick (th_13); a stand-in, the same sugar should have one value
N_SUGAR = 1.5
DEVELOP = dict(exposure=0.0, contrast=1.35, saturation=1.05, black=0.002, grain=1.2, sharpen=0.25, halation=0.03, glare=0.002, seed=75)  # the lychee's


def waves(d, rng, n, k0, k1):
    """A smooth seamless field: random plane waves over the positions or directions d, about unit variance."""
    k = rng.normal(size=(n, 3))
    k = k / np.linalg.norm(k, axis=1, keepdims=True) * rng.uniform(k0, k1, (n, 1))
    ph = rng.uniform(0, 2 * np.pi, n)
    f = np.zeros(d.shape[:-1], np.float32)
    for i in range(n):
        f += np.sin(d @ k[i].astype(np.float32) + ph[i])
    return f * np.sqrt(2.0 / n)


_T0 = (1 + 5**0.5) / 2
_V0 = np.array([[-1, _T0, 0], [1, _T0, 0], [-1, -_T0, 0], [1, -_T0, 0], [0, -1, _T0], [0, 1, _T0], [0, -1, -_T0], [0, 1, -_T0], [_T0, 0, -1], [_T0, 0, 1], [-_T0, 0, -1], [-_T0, 0, 1]], np.float32)
_F0 = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])


def spheres(C, r):
    """Closed spheres of 80 faces, outward normals, as an unshared triangle soup: (N * 240, 3)."""
    V1 = _V0[_F0]
    m = np.stack([(V1[:, 0] + V1[:, 1]) / 2, (V1[:, 1] + V1[:, 2]) / 2, (V1[:, 2] + V1[:, 0]) / 2], 1)
    t = np.concatenate([np.stack([V1[:, 0], m[:, 0], m[:, 2]], 1), np.stack([V1[:, 1], m[:, 1], m[:, 0]], 1), np.stack([V1[:, 2], m[:, 2], m[:, 1]], 1), np.stack([m[:, 0], m[:, 1], m[:, 2]], 1)])
    t = t / np.linalg.norm(t, axis=-1, keepdims=True)
    return (np.asarray(C, np.float32)[:, None, None] + np.asarray(r, np.float32)[:, None, None, None] * t[None]).reshape(-1, 3).astype(np.float32)


FRAME_W = 5.0
FRAME_CX = 0.5


def at_frame(fx, fy, view):
    """The direction from the fruit's centre to about what the frame shows at (fx, fy), so that a flaw can be placed where it is seen. Approximate: a sphere of 1.6 cm, the arc's top at y = .48."""
    v = np.array(view, float)
    up = np.array([0.0, v[2], -v[1]])
    x, z = (fx - FRAME_CX) * FRAME_W, 1.6 - (fy - 0.48) * FRAME_W * 9 / 16
    y = np.sqrt(max(1.6**2 - x**2 - z**2, 0.05))
    d = x * np.array([1.0, 0.0, 0.0]) + z * up + y * v
    return (d / np.linalg.norm(d)).astype(np.float32)


def fruit(path_skin, path_sugar, seed, rows, o, axis, view):
    rng = np.random.default_rng(seed)
    a_, c_ = o["a"], o["c"]
    e3 = axis
    e1 = np.array([0.0, 1.0, 0.0]) - axis * axis[1]  # the mesh's seam looks away from the camera
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(e3, e1)
    u_ = np.linspace(0.0, 1.0, rows, dtype=np.float32)
    th = 1e-3 + (np.pi - 2e-3) * (0.3 * u_ + 0.7 * u_**8)  # the frame sees only the cap round the calyx: most of the rows go there
    ph = np.linspace(0.0, 2 * np.pi, rows * 3, dtype=np.float32)
    th, ph = np.meshgrid(th, ph, indexing="ij")
    st, ct = np.sin(th), np.cos(th)
    F = np.array([e1, e2, e3], np.float32)
    n = (st * np.cos(ph))[..., None] * F[0] + (st * np.sin(ph))[..., None] * F[1] + ct[..., None] * F[2]
    r = 1.0 / np.sqrt((st / a_) ** 2 + (ct / c_) ** 2)
    r = r * (1 + 0.035 * waves(n, rng, 10, 1.5, 3.0) + 0.012 * waves(n, rng, 16, 4.0, 8.0))
    sep_ph = rng.uniform(0, 6.3)
    rs = np.random.default_rng(93)  # dried sepals joined at the base: a dark, torn star, each lobe its own length and width
    lobe = np.zeros_like(th)
    for ph_j, w_j, l_j in zip(sep_ph + 2 * np.pi * np.arange(5) / 5 + rs.uniform(-0.22, 0.22, 5), rs.uniform(0.16, 0.36, 5), rs.uniform(0.02, 0.08, 5)):
        lobe = np.maximum(lobe, l_j * np.clip(1 - np.abs((ph - ph_j + np.pi) % (2 * np.pi) - np.pi) / w_j, 0, 1) ** 0.8)
    lim = 0.075 + lobe + 0.009 * waves(n, np.random.default_rng(83), 10, 30.0, 70.0) + 0.006 * waves(n, np.random.default_rng(97), 14, 90.0, 220.0)
    sepal = sstep(lim + 0.008, lim - 0.006, th) * sstep(0.045, 0.06, th)
    core = sstep(0.042, 0.026, th * (1 + 0.2 * waves(n, np.random.default_rng(84), 8, 30.0, 70.0)))
    r = r * (1 - 0.018 * np.exp(-((th / 0.3) ** 2)) - 0.05 * np.exp(-((th / 0.1) ** 4)) - 0.12 * np.exp(-(((np.pi - th) / 0.26) ** 2)) + 0.022 * sepal * sstep(0.05, 0.16, th) + 0.008 * sepal + 0.008 * core)
    r_smooth = r * (1 + 0.05 * np.exp(-((th / 0.1) ** 4)) * 0.6 - 0.022 * sepal * sstep(0.05, 0.16, th) - 0.008 * sepal - 0.008 * core)
    fold = sum(rng.uniform(0.4, 1.0) * np.sin(k * ph + rng.uniform(0, 6.3) + 1.2 * waves(n, rng, 4, 2.0, 4.0)) for k in (5, 7, 9, 12, 16))
    r = r * (1 - 0.0006 * fold * np.exp(-((th / 0.34) ** 2)) * (1 - np.exp(-((th / 0.07) ** 2))))
    # flaws, from their own random stream. The fruit grew crooked, was knocked, and creased as it dried
    rf = np.random.default_rng(82)
    near = lambda fx, fy, w: np.exp(-((np.arccos(np.clip(n @ at_frame(fx, fy, view), -1, 1)) / w) ** 2))
    r = r * (1 + 0.03 * waves(n, rf, 5, 1.0, 2.2))
    knock = near(0.78, 0.68, 0.2)
    r = r * (1 - 0.05 * knock - 0.022 * near(0.84, 0.64, 0.16) - 0.018 * near(0.2, 0.6, 0.2))
    crease_field = waves(n, rf, 5, 5.0, 11.0)
    crease = np.exp(-((crease_field / 0.05) ** 2)) * near(0.77, 0.7, 0.17)  # the dent's wrinkles
    crease2_field = waves(n, rf, 5, 6.0, 13.0)
    crease = np.maximum(crease, np.exp(-((crease2_field / 0.04) ** 2)) * near(0.3, 0.72, 0.16))
    crease_d = 0.007 * crease
    r = r - crease_d
    P = n * r[..., None]

    # the dark flow and its hard, lobed edge (photo_04): sugar that ran round the stem scar and set thick
    cdir = at_frame(0.1, 0.74, view)
    f = n @ cdir - 0.42 + 0.22 * waves(n, rng, 7, 2.0, 4.5) + 0.07 * waves(n, rng, 12, 7.0, 16.0) + 0.007 * waves(n, rng, 16, 30.0, 70.0)
    w_ = 0.015 + 0.13 * sstep(0.2, 1.4, waves(n, rng, 5, 2.0, 5.0))
    cap = np.clip((f - 0.34) / w_, 0.0, 1.0)
    cap = cap * cap * (3 - 2 * cap)
    deep = cap * (0.6 + 0.4 * sstep(0.0, 0.32, f - 0.34))
    lip = np.exp(-(((f - 0.35) / 0.05) ** 2)) * sstep(-0.8, 0.6, waves(n, np.random.default_rng(81), 5, 2.0, 5.0)) * sstep(0.1, 0.35, n @ np.array(view, np.float32))  # never on the arc itself

    big = waves(n, rng, 8, 1.2, 2.8)
    mot = waves(n, rng, 40, 12.0, 34.0)
    streak = sum(rng.uniform(0.4, 1.0) * np.sin(k * (ph + 0.25 * big) + rng.uniform(0, 6.3)) for k in (37, 59, 97, 151, 233)) / 2.0
    t = sstep(-1.0, 1.0, big + 0.45 * mot + 0.12 * streak)[..., None]
    col = color([0.28, 0.01, 0.022]) * (1 - t) + color([0.72, 0.075, 0.13]) * t
    ps = 0.42 * sstep(-0.3, 1.7, waves(n, np.random.default_rng(86), 6, 1.6, 3.6) + 0.45 * mot + 0.25 * big)[..., None]
    col = col * (1 - ps) + color([0.84, 0.3, 0.2]) * ps  # peach, where the fruit grew in shade
    rt = np.random.default_rng(94)
    pore = waves(n, rt, 36, 150.0, 420.0)  # the skin's own grain: this is most of what separates a fruit from a painted ball at full size
    flo = sstep(0.7, 1.9, waves(n, rt, 30, 260.0, 620.0))[..., None]
    col = col * np.exp(0.07 * pore)[..., None]
    col = col * (1 - 0.11 * flo) + color([0.92, 0.42, 0.42]) * 0.11 * flo
    fine = bool(o["bub"])  # the near fruit only: the others are far out of focus
    relief = np.zeros_like(th)
    if fine:
        rm = np.random.default_rng(101)
        # the pigment: fine threads running out from the calyx, broken into patches, with the orange ground between them
        warp = 0.03 * waves(n, rm, 6, 6.0, 14.0)
        threads = sum(rm.uniform(0.5, 1.0) * np.sin(k * (ph + warp) + rm.uniform(0, 6.3)) for k in (311, 487, 743, 1103, 1571)) / 2.2
        patch = sstep(-0.7, 1.0, waves(n, rm, 10, 14.0, 40.0))
        tq = sstep(-0.8, 0.8, threads + 0.5 * waves(n, rm, 12, 300.0, 800.0))[..., None] * patch[..., None]
        col = col * (1 - 0.14 * tq) + color([0.86, 0.26, 0.14]) * 0.14 * tq
        col = col * (1 - 0.14 * (patch[..., None] - tq).clip(0, 1))
        # the epidermis: a mosaic of cells, each with its own pigment, about 40 um across at this scale (assumed, a 2.5 cm fruit)
        pc = rm.normal(size=(int(o["cells"]), 3)).astype(np.float32)
        pc = pc / np.linalg.norm(pc, axis=1, keepdims=True)
        vis = th < 1.75
        d2, i2 = cKDTree(pc).query(n[vis], k=2, workers=-1)
        val = rm.normal(0.0, 1.0, len(pc)).astype(np.float32)
        cell, wall = np.zeros_like(th), np.zeros_like(th)
        cell[vis] = val[i2[:, 0]]
        wall[vis] = np.exp(-(((d2[:, 1] - d2[:, 0]) / 0.0009) ** 2))
        col = col * np.exp(0.06 * cell.clip(-2.5, 2.5))[..., None] * (1 - 0.09 * wall)[..., None]
        pcell = sstep(1.5, 2.1, cell)[..., None]
        col = col * (1 - 0.14 * pcell) + color([0.95, 0.5, 0.42]) * 0.14 * pcell  # the few cells with less pigment
        relief = relief + 0.00007 * (cell.clip(-1.5, 1.5) - 0.8 * wall)
        # the wrinkles of a skin that has begun to dry
        wr = waves(n, rm, 16, 90.0, 240.0)
        wrk = np.exp(-((wr / 0.1) ** 2)) * sstep(-0.4, 1.0, waves(n, rm, 8, 8.0, 22.0))
        relief = relief - 0.0005 * wrk
        col = col * (1 - 0.1 * wrk)[..., None]
    dark = color([0.1, 0.0015, 0.006]) * (1 - t) + color([0.24, 0.004, 0.014]) * t
    col = col * (1 - deep[..., None]) + dark * deep[..., None]

    bruise = (near(0.8, 0.6, 0.13) * (1 + 0.5 * waves(n, rf, 8, 8.0, 20.0))).clip(0, 1)[..., None]
    col = col * (1 - 0.65 * bruise) + color([0.2, 0.025, 0.03]) * 0.65 * bruise
    pale = (near(0.36, 0.6, 0.1) * sstep(-0.6, 0.8, waves(n, rf, 10, 12.0, 30.0)))[..., None]
    col = col * (1 - 0.6 * pale) + color([0.8, 0.3, 0.13]) * 0.6 * pale
    cr = crease[..., None]
    col = col * (1 - 0.4 * cr) + color([0.09, 0.008, 0.01]) * 0.4 * cr

    # lenticels: small, separate, evenly spread (darts thrown with a minimum distance); olive, some gold, slightly rough at 100 %
    cand = rng.normal(size=(16000, 3))
    cand = cand / np.linalg.norm(cand, axis=1, keepdims=True)
    tree, keep = cKDTree(cand), np.ones(len(cand), bool)
    for i in range(len(cand)):
        if keep[i]:
            nb_ = tree.query_ball_point(cand[i], 0.034)
            keep[nb_] = False
            keep[i] = True
    dots = cand[keep]
    dots = dots[rng.uniform(0, 1, len(dots)) < 0.62 + 0.38 * sstep(-0.6, 0.9, dots @ e3 + 0.5 * rng.normal(size=len(dots)))]  # patchy
    dots = dots[waves(dots, rng, 5, 2.5, 6.0) > -0.9]
    ND = len(dots)
    dist, ix = cKDTree(dots).query(n.reshape(-1, 3), workers=-1)
    dist, ix = dist.reshape(th.shape), ix.reshape(th.shape)
    size = (0.0036 + 0.0034 * rng.gamma(1.5, 0.7, ND))[ix].clip(0.003, 0.0125)
    grain = waves(n, rng, 28, 120.0, 320.0)
    rl = np.random.default_rng(103)
    rag = waves(n, rl, 16, 700.0, 1800.0) if fine else np.zeros_like(th)
    m = sstep(0.95, 0.62, dist / size * (1 + 0.2 * grain + 0.12 * waves(n, rng, 10, 40.0, 100.0) + 0.14 * rag)) * rng.uniform(0.55, 1.0, ND)[ix]
    m = m * (1 - 0.6 * cap)  # hardly seen under the thick flow (photo_04)
    gold = rng.uniform(0.0, 1.0, ND)[ix][..., None]
    lent = color([0.3, 0.2, 0.08]) * (1 - gold) + color([0.56, 0.46, 0.22]) * gold
    if fine:
        cork = sstep(-0.8, 0.8, waves(n, rl, 24, 500.0, 1500.0))[..., None]  # corky inside: pale flakes on brown, a dark rim, split down the middle in many
        lent = lent * (0.78 + 0.34 * cork)
        lent = lent * (1 - 0.4 * sstep(0.5, 0.9, dist / size))[..., None]
        split = np.exp(-((waves(n, rl, 8, 250.0, 500.0) / 0.1) ** 2)) * (rl.uniform(0.0, 1.0, ND)[ix] > 0.45)
        lent = lent * (1 - 0.45 * split)[..., None]
        relief = relief + 0.0016 * m * (1 + 0.3 * cork[..., 0]) * (1 - 0.4 * split)
    halo = (0.5 * (1 + 0.4 * rag).clip(0, 2) * sstep(1.9, 1.0, dist / size) * (1 - m) * (1 - 0.6 * deep))[..., None]
    col = col * (1 - halo) + color([0.13, 0.05, 0.025]) * halo
    col = col * (1 - m[..., None]) + lent * m[..., None]

    # a corky scab, where the skin split on the tree and healed
    ang = np.arccos(np.clip(n @ at_frame(0.36, 0.84, view), -1, 1))
    edge_ = waves(n, rf, 10, 14.0, 40.0)
    scab = sstep(0.045, 0.026, ang * (1 + 0.3 * waves(n, np.random.default_rng(96), 6, 12.0, 26.0).clip(-1.6, 1.6)) * (1 + 0.12 * edge_.clip(-1.5, 1.5)) * np.array(1.0, np.float32))
    tone = sstep(-1.0, 1.0, waves(n, rf, 24, 120.0, 320.0) + (0.9 * waves(n, np.random.default_rng(104), 20, 500.0, 1400.0) if fine else 0.0))[..., None]
    corky = color([0.07, 0.035, 0.018]) * (1 - tone) + color([0.17, 0.09, 0.04]) * tone
    col = col * (1 - scab[..., None]) + corky * scab[..., None]
    relief = relief + 0.004 * scab * tone[..., 0]
    # a healed scratch: a thin brown line, not quite straight
    a0, a1 = at_frame(0.24, 0.62, view), at_frame(0.35, 0.58, view)
    ax_ = np.cross(a0, a1)
    ax_ = ax_ / np.linalg.norm(ax_)
    off = n @ ax_ + 0.006 * waves(n, rf, 6, 10.0, 26.0)
    mid_ = (a0 + a1) / np.linalg.norm(a0 + a1)
    span = np.arccos(np.clip(n @ mid_, -1, 1))
    half = np.arccos(np.clip(a0 @ mid_, -1, 1))
    scratch = np.exp(-((off / 0.0035) ** 2)) * sstep(half, half * 0.8, span) * (0.45 + 0.55 * sstep(-1.0, 0.6, waves(n, rf, 6, 30.0, 70.0)))
    col = col * (1 - scratch[..., None]) + color([0.2, 0.09, 0.05]) * scratch[..., None]
    # insect pits
    for fx_, fy_, w_p in ((0.4, 0.72, 0.006), (0.6, 0.55, 0.004), (0.68, 0.76, 0.005), (0.32, 0.88, 0.005)):
        ang = np.arccos(np.clip(n @ at_frame(fx_, fy_, view), -1, 1))
        ring = np.exp(-((ang / (w_p * 1.9)) ** 2))[..., None]
        col = col * (1 - 0.4 * ring) + color([0.22, 0.09, 0.04]) * 0.4 * ring
        col = col * (1 - sstep(w_p, w_p * 0.6, ang)[..., None]) + np.array([0.008, 0.005, 0.004], np.float32) * sstep(w_p, w_p * 0.6, ang)[..., None]

    # the dry remnant in the scar, and browner skin round it
    k = np.exp(-((th / 0.2) ** 2))[..., None]
    col = col * (1 - 0.4 * k) + np.array([0.13, 0.04, 0.016], np.float32) * 0.4 * k  # browner skin round the pit
    k = sstep(0.095, 0.06, th * (1 + 0.15 * waves(n, np.random.default_rng(90), 6, 6.0, 16.0)))[..., None]
    fib = sum(np.random.default_rng(98 + k_).uniform(0.4, 1.0) * np.sin(k_ * ph + 9.0 * waves(n, np.random.default_rng(298 + k_), 4, 6.0, 16.0) + np.random.default_rng(198 + k_).uniform(0, 6.3)) for k_ in (41, 67, 109, 173)) / 2.0  # fibres running out along the sepals
    grit = sstep(-1.0, 1.0, 0.7 * waves(n, np.random.default_rng(85), 24, 220.0, 620.0) + 0.7 * fib)[..., None]
    col = col * (1 - k) + (np.array([0.012, 0.007, 0.005], np.float32) * (1 - grit) + np.array([0.07, 0.04, 0.02], np.float32) * grit) * k  # the dark ring in the pit
    if fine:
        relief = relief + 0.003 * (sepal + core) * grit[..., 0]
    k = sepal[..., None]
    col = col * (1 - k) + (np.array([0.016, 0.009, 0.006], np.float32) * (1 - grit) + np.array([0.042, 0.024, 0.013], np.float32) * grit) * k
    k = core[..., None]
    col = col * (1 - k) + (np.array([0.03, 0.017, 0.009], np.float32) * (1 - grit) + np.array([0.14, 0.085, 0.04], np.float32) * grit) * k  # the core: dry, brown
    np.savez(path_skin, P=(n * (r + relief)[..., None]).astype(np.float32), col=col.astype(np.float32))

    # sugar
    r = r + 0.75 * crease_d
    wp = np.exp(-((th / 0.42) ** 2))
    r = r * (1 - wp) + r_smooth * wp  # the sugar's own surface is smooth over the pit
    r = r + 0.0035 * waves(n, rng, 12, 5.0, 12.0) + 0.0012 * waves(n, rng, 24, 16.0, 44.0) + 0.0007 * waves(n, rng, 30, 50.0, 130.0) * sstep(-0.3, 0.9, waves(n, rng, 6, 3.0, 8.0)) + 0.0011 * m + (0.000015 * waves(n, np.random.default_rng(105), 24, 400.0, 1000.0) if fine else 0.0)
    h = o["h"] * (1 + 0.45 * waves(n, rng, 12, 2.0, 5.0)) * (1 + 0.8 * sstep(0.2, -0.9, n[..., 2])) * (1 + 2.2 * np.exp(-((np.minimum(th, np.pi - th) / 0.24) ** 2)))
    h = h + 0.022 * cap + 0.05 * lip * sstep(-0.6, 0.9, waves(n, np.random.default_rng(95), 8, 6.0, 18.0))  # the thicker flow, ending in a raised lip
    az = np.arctan2(n[..., 1], n[..., 0])
    wander = 0.5 * waves(n, rng, 5, 1.5, 3.5)
    run = sum(rng.uniform(0.3, 1.0) / np.sqrt(k) * np.sin(k * (az + wander) + rng.uniform(0, 6.3)) for k in (9, 14, 22, 33, 47, 70))
    h = np.maximum(h * (1 + 0.05 * run * sstep(0.98, 0.72, n[..., 2])), 0.006)
    h = np.maximum(h * (1 - 0.72 * near(0.7, 0.52, 0.1)), 0.006)  # where it ran thin
    h = h + 0.012 * near(0.2, 0.52, 0.34)  # the sugar thickens a little towards the sheet. Much more and the fruit's edge turns into a clear band that shows the light behind it
    for fx_, fy_, w_c in ((0.72, 0.62, 0.26), (0.34, 0.8, 0.24), (0.62, 0.84, 0.22), (0.66, 0.6, 0.18)):  # thin ridges, where a run stopped and set
        g_ = waves(n, rf, 4, 3.0, 7.0)
        h = h + 0.01 * np.exp(-((g_ / 0.022) ** 2)) * near(fx_, fy_, w_c) * sstep(-0.7, 0.3, waves(n, rf, 4, 6.0, 14.0))
    ang = np.arccos(np.clip(n @ at_frame(0.52, 0.92, view), -1, 1))
    chip = sstep(0.055, 0.04, ang * (1 + 0.22 * waves(n, rf, 12, 18.0, 60.0)))  # a chip, with a steep edge and a shelly floor
    h = np.maximum(h - chip * (0.5 * h + 0.004 * waves(n, rf, 10, 40.0, 110.0)), 0.004)
    # crazing, in two patches: brittle things craze, wet things do not
    pts_ = np.random.default_rng(92).normal(size=(9000, 3))
    ck = cKDTree(pts_ / np.linalg.norm(pts_, axis=1, keepdims=True))
    rw_ = np.random.default_rng(106)
    nw_ = n + 0.012 * np.stack([waves(n, rw_, 6, 30.0, 70.0) for _ in range(3)], -1)  # bent, or the edges are straight lines drawn with a ruler
    dd, _ = ck.query(nw_.reshape(-1, 3), k=2, workers=-1)
    gapd = (dd[:, 1] - dd[:, 0]).reshape(th.shape).astype(np.float32)
    h = np.maximum(h - 0.003 * np.exp(-((gapd / 0.0012) ** 2)) * (near(0.78, 0.78, 0.13) + near(0.28, 0.72, 0.1)).clip(0, 1) * sstep(-0.3, 0.5, waves(n, rw_, 6, 20.0, 50.0)), 0.004)
    if fine:  # the sheet and the coat are one pour: the coat rises to meet it in a meniscus, along the line where the sheet's plane cuts the fruit
        ex_, ez_, N_ = sheet_axes()
        P_ = n * r[..., None]
        off_ = (P_ - np.array([o["bx"], o["by"], o["bz"]], np.float32)) @ N_
        along = sstep(-1.28, -1.1, P_[..., 0]) * sstep(-0.08, -0.5, P_[..., 0]) * sstep(0.0, 0.3, n[..., 2])
        h = h + 0.05 * np.exp(-((off_ / 0.07) ** 2)) * along * (1 + 0.3 * waves(n, np.random.default_rng(107), 6, 4.0, 12.0))
    S = n * (r + h)[..., None]
    np.savez(path_sugar, P=S.astype(np.float32))

    # bubbles: true voids, gathered in clusters and where the sugar is thick
    C, R = np.zeros((0, 3), np.float32), np.zeros(0, np.float32)
    nb = int(o["bub"])
    if nb:
        cl = 1 + 3 * sstep(0.6, 1.4, waves(n, rng, 10, 6.0, 14.0))
        w = (cl * sstep(0.0, 0.1, h) * np.maximum(n @ np.array(view, np.float32), 0.0) * sstep(0.2, 0.42, th)).ravel().astype(np.float64)  # evenly over the face: gathered by thickness they became a frost round the scar
        i = rng.choice(w.size, nb, p=w / w.sum())
        C = n.reshape(-1, 3)[i] * (r.ravel()[i] + h.ravel()[i] * rng.uniform(0.3, 0.7, nb))[:, None]
        R = np.minimum(0.0022 * rng.pareto(1.6, nb) + 0.0011, 0.22 * h.ravel()[i])
    return S, C, R


ROW = [(np.array([1.5, 3.3, -0.22], np.float32), 0.95, 175, (-0.5, 0.25, 0.83)), (np.array([4.7, 6.65, 0.42], np.float32), 1.0, 275, (0.3, -0.4, 0.86))]  # the next fruits on the stick, by eye


def bridge(path_wood, path_sugar, rows):
    """The stick between the fruits, and the sugar pooled round it: thick and gold at each fruit, thin between (photo_01). Bamboo 2.4 mm against a 33 mm fruit, by eye."""
    rng = np.random.default_rng(88)
    end = ROW[-1][0]
    L = float(np.linalg.norm(end)) + 2.0
    ax = end / np.linalg.norm(end)
    e1 = np.cross(ax, np.array([0.0, 0.0, 1.0], np.float32))
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    ns, na = max(rows // 2, 300), max(rows // 6, 120)
    Ss, An = np.meshgrid(np.linspace(0.0, L, ns, dtype=np.float32), np.linspace(2 * np.pi, 0.0, na, dtype=np.float32), indexing="ij")
    fibre = sum(rng.uniform(0.3, 1.0) * np.sin(k * An + rng.uniform(0, 6.3) + 0.5 * np.sin(0.8 * Ss + rng.uniform(0, 6.3))) for k in (7, 13, 23, 41, 71)) / 3.0
    u = np.cos(An)[..., None] * e1 + np.sin(An)[..., None] * e2
    C = Ss[..., None] * ax
    t = sstep(-1.2, 1.2, fibre)[..., None]
    col = color([0.42, 0.28, 0.12]) * (1 - t) + color([0.74, 0.58, 0.32]) * t
    np.savez(path_wood, P=(C + (0.12 * (1 + 0.012 * fibre))[..., None] * u).astype(np.float32), col=col.astype(np.float32))
    centres = [0.0] + [float(np.linalg.norm(c)) for c, _, _, _ in ROW]
    wob = waves(np.stack([np.cos(An), np.sin(An), Ss * 0.8], -1), rng, 8, 1.5, 4.0)
    h = np.full(Ss.shape, 0.03, np.float32)
    for c_ in centres:
        d_ = np.maximum(np.abs(Ss - c_) - 1.5, 0.0)  # along the stick, from about the fruit's surface
        h = h + 0.42 * np.exp(-((d_ / 0.2) ** 1.3)) * (1 + 0.25 * wob)
    np.savez(path_sugar, P=(C + (0.12 + h)[..., None] * u).astype(np.float32))


def sheet_axes():
    """The sheet's plane: x along it, leftwards; z up it, leaning back; N away from the camera."""
    ex = np.array([-1.0, -0.02, 0.0], np.float32)
    ex = ex / np.linalg.norm(ex)
    ez = np.array([0.0, 0.25, 1.0], np.float32)
    ez = ez - ex * (ez @ ex)
    ez = ez / np.linalg.norm(ez)
    return ex, ez, np.cross(ex, ez).astype(np.float32)


def blade(path, rows, o, axis):
    """The sheet: a fan seen from the front, one grid folded over its ragged edge, its root hidden in the fruit. Returns the bubbles' centres and radii."""
    rng = np.random.default_rng(76)
    nr, nf = max(rows // 3, 60), rows
    org = np.array([-0.55, 0.02, 0.55], np.float32)
    ex, ez, N = sheet_axes()
    s_ = float(o["bl"])
    new = np.array([o["bx"], o["by"], o["bz"]], np.float32)
    world = lambda X: new + (X - org) * s_

    phi = np.radians(np.linspace(-15.0, 130.0, nf, dtype=np.float32))
    base = np.interp(np.degrees(phi), [-15, 12, 30, 50, 72, 92, 112, 130], [0.25, 0.7, 1.35, 1.75, 1.92, 1.85, 1.25, 0.45]).astype(np.float32)
    lo = sum(rng.uniform(0.5, 1.0) / k**0.7 * np.sin(k * phi + rng.uniform(0, 6.3)) for k in (4, 7, 11, 17))
    hi = 0.4 * sum(rng.uniform(0.5, 1.0) / k**0.7 * np.sin(k * phi + rng.uniform(0, 6.3)) for k in (29, 47, 83, 137, 211))
    spike = sum(rng.uniform(0.015, 0.04) * np.exp(-(((phi - rng.uniform(phi[0], phi[-1])) / rng.uniform(0.005, 0.012)) ** 2)) for _ in range(7))
    Rsoft = base * (1 + 0.13 * lo)
    Rout = Rsoft * (1 + 0.1 * hi) + spike
    Rout = np.maximum(Rout, 0.25).astype(np.float32)

    rho = np.linspace(0.0, 1.0, nr, dtype=np.float32)
    Rh, Ph = np.meshgrid(rho, phi, indexing="ij")
    Rr = Rh * Rout[None, :]
    dirs = np.cos(Ph - 0.38)[..., None] * ex + np.sin(Ph - 0.38)[..., None] * ez  # reaching out along the shoulder, not standing on it
    Q = org + dirs * Rr[..., None]

    # smooth as poured glass, slowly warped: no ridges running outward, which read as a hedgehog
    mid = 0.1 * (Rr / 2.6) ** 2 * np.sin(2 * Ph + 1.0) + 0.009 * waves(Q, rng, 8, 1.5, 4.0) + 0.0028 * waves(Q, rng, 16, 8.0, 22.0)
    rim = (1 - Rh) * Rout[None, :]  # distance in from the true rim
    close = np.sqrt(1 - np.exp(-((rim / np.maximum(0.016 * (1 + 1.1 * waves(Q, rng, 6, 2.0, 7.0)), 0.004)) ** 2)))
    lump = 1 + 0.18 * waves(Q, rng, 8, 1.2, 3.5)
    edge = np.maximum(Rsoft[None, :] - Rr, 0.0)  # distance in from a smooth version of the rim
    wid = 0.07 * (1 + 0.5 * waves(Q, rng, 5, 2.0, 5.0))
    bead = 0.005 * sstep(-0.2, 1.1, waves(Q, rng, 6, 1.0, 3.0)) * (1 + 0.3 * waves(Q, rng, 5, 3.0, 8.0)) * np.exp(-((edge / np.maximum(wid, 0.025)) ** 2))  # the rope of sugar along the rim (th_13)
    rope = np.zeros_like(Rh)
    for _ in range(2):  # ropes inside it, where the syrup ran and set
        at = rng.uniform(0.25, 0.65) + 0.18 * sum(rng.uniform(0.4, 1.0) / k * np.sin(k * Ph + rng.uniform(0, 6.3)) for k in (3, 5, 9, 15))
        along = sstep(0.0, 0.3, Ph - rng.uniform(phi[0], 0.8)) * sstep(0.0, 0.3, rng.uniform(1.0, phi[-1]) - Ph)
        rope += 0.35 * rng.uniform(0.006, 0.012) * along * np.exp(-(((edge - at) / rng.uniform(0.04, 0.07)) ** 2))
    ax_ = np.array(axis, np.float32)
    Qw = world(Q)
    zz = Qw @ ax_
    gap = np.maximum(np.sqrt((np.linalg.norm(Qw - zz[..., None] * ax_, axis=-1) / o["a"]) ** 2 + (zz / o["c"]) ** 2) - 1.0, 0.0) * 1.6 / s_  # roughly cm from the fruit, in the sheet's own units
    th = (0.06 * lump + 0.035 * np.exp(-((gap / 0.7) ** 2)) + bead + rope) * close

    back = Q + N * (mid + th / 2)[..., None]
    front = Q + N * (mid - th / 2)[..., None]
    np.savez(path, P=world(np.concatenate([back, front[::-1][1:]], 0)).astype(np.float32))

    nb = int(o["sbub"])
    if not nb:
        return np.zeros((0, 3), np.float32), np.zeros(0, np.float32)
    cl = 0.15 + 8 * sstep(0.5, 1.3, waves(Q, rng, 10, 3.0, 9.0))
    w = (cl * (rim > 0.03) * (Rr > 0.5) * (1 + 2 * np.exp(-((edge / 0.2) ** 2)))).ravel().astype(np.float64)
    i = rng.choice(w.size, nb, p=w / w.sum())
    t_ = th.ravel()[i]
    C = Q.reshape(-1, 3)[i] + N * ((mid.ravel()[i] + rng.uniform(-0.2, 0.2, nb) * t_)[:, None]).astype(np.float32)
    R = np.minimum(0.0022 * rng.pareto(1.5, nb) + 0.002, 0.34 * t_)
    R[:12] = np.minimum(0.004 + 0.016 * rng.uniform(0, 1, 12) ** 2, 0.36 * t_[:12])  # the few large ones
    seeds = rng.integers(0, nb, 6)  # and tight clusters of minute ones
    g = rng.normal(0.0, 0.05, (6 * 25, 2)).astype(np.float32)
    C3 = np.repeat(C[seeds], 25, axis=0) + g[:, :1] * ex + g[:, 1:] * ez
    R3 = np.minimum(0.0011 + 0.001 * rng.pareto(1.8, 6 * 25), 0.012)
    return world(np.concatenate([C, C3])).astype(np.float32), np.concatenate([R, R3]) * s_


LIGHTS = [  # frame x, y, radius in frame widths, colour, gain: placed by eye, clear of the caption
    (0.03, 0.28, 0.026, "wh", 0.5), (0.075, 0.2, 0.03, "blu", 0.55), (0.11, 0.3, 0.024, "gold", 0.6), (0.15, 0.18, 0.022, "wh", 0.42), (0.02, 0.44, 0.03, "gold", 0.6), (0.2, 0.26, 0.02, "blu", 0.3),
    (0.08, 0.42, 0.018, "gold", 0.5), (0.25, 0.14, 0.018, "gold", 0.25), (0.05, 0.6, 0.024, "wh", 0.4), (0.03, 0.82, 0.05, "or", 0.55), (0.1, 0.92, 0.036, "mag", 0.45), (0.0, 0.66, 0.03, "or", 0.35),
    (0.965, 0.42, 0.034, "gold", 0.35), (0.72, 0.17, 0.026, "gold", 0.16), (0.68, 0.33, 0.03, "or", 0.3),
    (0.13, 0.42, 0.022, "wh", 0.9), (0.23, 0.27, 0.018, "blu", 0.8), (0.27, 0.46, 0.015, "gold", 0.8),  # behind the sheet, to be seen through it
]
PAL = {"gold": (0.78, 0.4, 0.11), "lav": (0.42, 0.42, 0.95), "or": (0.5, 0.13, 0.025), "mag": (0.42, 0.08, 0.3), "wh": (0.8, 0.7, 0.55), "blu": (0.3, 0.42, 0.95)}


def lens_plate(path, cam, o):
    """What the lens makes of the market's lights, painted on a plate close behind the fruit, seen by the camera alone. Cycles' aperture is a perfect disc, so its defocused
    lights come out flat, which reads as render. A STAND-IN for a real lens, painted by rule: a brighter rim, faint onion rings, cat's eyes towards the frame's corners, red and blue
    rims apart, dust. The wash behind them too (the sky mesh stays dark behind the plate)."""
    right, up, back = [np.array(v, float) for v in _cam_axes(cam)]
    loc = np.array(cam["loc"], float)
    d = o["dist"] + 10.0  # behind the last fruit
    W = o["W"] * d / o["dist"]
    nx, ny = 1537, 865
    x, y = np.meshgrid(np.linspace(-0.08, 1.08, nx, dtype=np.float32), np.linspace(-0.08, 1.08, ny, dtype=np.float32))
    a = 9 / 16
    img = np.zeros((ny, nx, 3), np.float32)
    # the air of a night market (photo_04): warm everywhere, a great lavender blur at the upper right, cool dark only in the far corner
    rw = np.random.default_rng(89)
    irr = np.exp(0.45 * waves(np.stack([x * 5, y * 3, 0 * x], -1), rw, 8, 1.0, 3.5))
    img += (irr * np.exp(-(((x - 0.45) / 0.62) ** 2 + ((y - 0.55) / 0.55) ** 2)))[..., None] * np.array([0.085, 0.024, 0.0045], np.float32)
    img += np.exp(-(((x - 0.95) / 0.17) ** 2 + ((y - 0.14) / 0.22) ** 2))[..., None] * np.array([0.075, 0.07, 0.17], np.float32)
    img += np.exp(-(((x - 0.0) / 0.3) ** 2 + ((y - 0.0) / 0.3) ** 2))[..., None] * np.array([0.006, 0.012, 0.035], np.float32)
    img += (0.4 * irr * (np.exp(-(((x - 0.22) / 0.1) ** 2 + ((y - 0.5) / 0.13) ** 2)) + 0.55 * np.exp(-(((x - 0.33) / 0.08) ** 2 + ((y - 0.36) / 0.1) ** 2))))[..., None] * np.array([0.34, 0.14, 0.03], np.float32)  # far lights, wholly out of focus, directly behind the sheet: what the sugar glows with
    img += np.array([0.004, 0.003, 0.005], np.float32)
    rng = np.random.default_rng(79)
    grit = waves(np.stack([x * 16, y * 9, 0 * x], -1), rng, 40, 60.0, 180.0)  # dust and polish marks on a front element
    for fx, fy, rad, name, gain in LIGHTS:
        vx, vy = fx - 0.5, (fy - 0.5) * a
        cc = np.hypot(vx, vy)
        ox, oy = vx / max(cc, 1e-3), vy / max(cc, 1e-3)
        sh = rad * 0.8 * sstep(0.3, 0.62, cc)  # the lens barrel's shadow: a second circle, displaced outwards in the frame, makes the cat's eye
        dx, dy = x - fx, (y - fy) * a
        r_ = np.hypot(dx, dy)
        r2 = np.hypot(dx - ox * sh, dy - oy * sh)
        c = np.array(PAL[name], np.float32) * gain
        for ch, sc in enumerate((1.012, 1.0, 0.988)):  # lateral colour: red a little wider, blue a little narrower
            e = 0.0035
            q = r_ / (rad * sc)
            disc = sstep(1 + e / rad, 1 - e / rad, q) * sstep(rad + e, rad - e, r2)
            side = 1 + 0.16 * (dx * ox + dy * oy) / rad  # brighter towards the frame's edge: spherical aberration, by eye
            body = side * (0.68 + 0.55 * np.exp(-(((1 - q) / 0.05) ** 2))) + 0.05 * np.sin(q * 34.0) * q**2 + 0.05 * sstep(0.45, 0.0, q)
            img[..., ch] += c[ch] * disc * body * (1 + 0.035 * grit)
    fx_ = (x - 0.5) * W
    fy_ = (0.5 - y) * W * a
    P = loc - back * d + right * fx_[..., None] + up * fy_[..., None]
    np.savez(path, P=P.astype(np.float32), col=img.astype(np.float32))


def reflected_lights(path, cam, o):
    """The same lights as true spheres far behind, for what the sugar reflects and shows through. The camera does not see them; it sees the plate."""
    right, up, back = [np.array(v, float) for v in _cam_axes(cam)]
    loc = np.array(cam["loc"], float)
    W, H = o["W"], o["W"] * 9 / 16
    fd = o["dist"]
    C, R, L = [], [], []
    for fx, fy, rad, name, gain in LIGHTS:
        d = 300.0
        C.append(loc - back * d + right * (fx - 0.5) * W * d / fd + up * (0.5 - fy) * H * d / fd)
        R.append(rad * W * d / fd)
        L.append(np.array(PAL[name]) * gain * 7.0)  # what is a soft disc to the lens is a hot lamp in a reflection
    V = spheres(np.array(C), np.array(R))
    col = np.repeat(np.array(L, np.float32), 240, axis=0)
    np.savez(path, V=V, F=np.arange(V.shape[0], dtype=np.int32).reshape(-1, 3), col=col)


def environment(path, cam, o):
    """What clear sugar shows through and reflects: a bright wall round the frame and a black flag just larger than the frame directly behind."""
    half_w = np.degrees(np.arctan(o["W"] / 2 / o["dist"]))
    half_h = np.degrees(np.arctan(o["W"] * 9 / 32 / o["dist"]))
    room_env(path, cam, {"window": 0.0, "ceil": 0.05, "wall": 0.03, "strip": 0.0})
    E = np.load(path)
    h, w = E.shape[:2]
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    r, up, b = [np.array(v, np.float32) for v in _cam_axes(cam)]
    az = np.degrees(np.arctan2(d @ r, -(d @ b)))  # 0 is straight ahead
    el = np.degrees(np.arcsin(np.clip(d @ up, -1, 1)))
    out = np.maximum(np.abs(az) - max(half_w, 11.3) - 1.5, np.abs(el) - max(half_h, 6.4) - 1.5)  # a fixed size: glass bends the view by some degrees whatever the frame, and a flag that shrinks with the frame shows the wall through the sheet's root as a pale band
    wall = sstep(-20.0, -6.0, el) * sstep(o["wall"] + 8.0, o["wall"] - 8.0, np.hypot(az, el)) * sstep(0.0, 2.0, out)
    flag = sstep(2.0, 0.0, out)
    wall = wall * np.exp(0.8 * waves(d, np.random.default_rng(78), 14, 3.0, 14.0))  # no even line of light on any rim
    wall = wall * (0.35 + 0.65 * sstep(-14.0, 8.0, az))  # less on the left, whose reflection lies along the near shoulder
    E = E * (1 - np.maximum(wall, flag))[..., None] + (o["back"] * wall)[..., None] * np.array([1.0, 0.9, 0.76], np.float32) + (0.012 * flag)[..., None]
    # small hot lamps round the stall, cold and warm: the sparkle in the sugar is theirs
    for az0, el0, w0, rgb in ((-58.0, 24.0, 2.5, (3.0, 5.0, 11.0)), (48.0, 34.0, 2.0, (6.0, 7.0, 12.0)), (72.0, 12.0, 3.0, (10.0, 4.0, 1.2)), (-30.0, 48.0, 2.0, (8.0, 8.0, 7.0)), (150.0, 26.0, 3.5, (3.0, 6.0, 12.0)), (-140.0, 18.0, 3.0, (11.0, 5.0, 1.5))):
        E = E + np.exp(-(((az - az0) / w0) ** 2 + ((el - el0) / w0) ** 2))[..., None] * np.array(rgb, np.float32)
    np.save(path, E.astype(np.float32))
    return path


def scene(tag, o, q):
    os.makedirs(D, exist_ok=True)
    global FRAME_W, FRAME_CX
    FRAME_W, FRAME_CX = o["W"], o["cx"]
    rows = int(o["nrows"]) or {"preview": 900, "mid": 1400, "final": 2200}[q]
    el = np.radians(o["el"])
    view = np.array([0.0, -np.cos(el), np.sin(el)])
    up = np.array([0.0, np.sin(el), np.cos(el)])
    t_, r_ = np.radians(o["tilt"]), np.radians(o["roll"])
    # the stick's direction through the fruit; its upper end leans towards the camera, so that the stem scar is on the face and not on the arc
    axis = np.array([np.sin(r_) * np.cos(t_), -np.sin(t_), np.cos(r_) * np.cos(t_)])
    axis = axis / np.linalg.norm(axis)

    sk, su, bp, sp, bk, lp, du, wd, cl = [os.path.join(D, f"{tag}_{n}.npz") for n in ("skin", "sugar", "bub", "sheet", "bokeh", "plate", "dust", "wood", "collar")]
    S, C, R = fruit(sk, su, 75, rows, o, axis, view)
    meshes = [
        {"name": "skin", "npz": sk, "material": {"Base Color": "col", "Roughness": 0.45, "Specular IOR Level": 0.08, "Subsurface Weight": 0.25, "Subsurface Radius": [0.12, 0.02, 0.015], "Subsurface Scale": 1.0}},
        {"name": "sugar", "npz": su, "shader_py": SHP, "params": {"ior": N_SUGAR, "sigma": SIGMA}},
    ]
    if o["row"]:
        for i_, (c2, sc, seed2, ax2) in enumerate(ROW):
            sk2, su2 = os.path.join(D, f"{tag}_skin{i_ + 2}.npz"), os.path.join(D, f"{tag}_sugar{i_ + 2}.npz")
            ax2 = np.array(ax2)
            fruit(sk2, su2, seed2, max(rows // (2 + i_), 450), dict(o, bub=0), ax2 / np.linalg.norm(ax2), view)
            for pth in (sk2, su2):
                z = dict(np.load(pth))
                z["P"] = z["P"] * sc + c2
                np.savez(pth, **z)
            meshes.append({"name": f"skin{i_ + 2}", "npz": sk2, "material": dict(meshes[0]["material"])})
            meshes.append({"name": f"sugar{i_ + 2}", "npz": su2, "shader_py": SHP, "params": {"ior": N_SUGAR, "sigma": SIGMA}})
        bridge(wd, cl, rows)
        meshes.append({"name": "wood", "npz": wd, "material": {"Base Color": "col", "Roughness": 0.55, "Specular IOR Level": 0.3}})
        meshes.append({"name": "bridge", "npz": cl, "shader_py": SHP, "params": {"ior": N_SUGAR, "sigma": SIGMA_SHEET}})
    C2, R2 = blade(sp, rows, o, axis)
    C, R = np.concatenate([C, C2]), np.concatenate([R, R2])
    if o["sheet"]:
      meshes.append({"name": "sheet", "npz": sp, "shader_py": SHP, "params": {"ior": N_SUGAR, "sigma": tuple(x / o["bl"] for x in SIGMA_SHEET)}})
    rd = np.random.default_rng(80)
    pts = S.reshape(-1, 3)
    front = pts[(pts @ view.astype(np.float32)) > 0.3]
    Pd = front[rd.integers(0, len(front), 24)]
    Vd = spheres(Pd, 0.0012 + 0.001 * rd.pareto(2.2, 24).clip(0, 3))
    np.savez(du, V=Vd, F=np.arange(Vd.shape[0], dtype=np.int32).reshape(-1, 3))
    meshes.append({"name": "dust", "npz": du, "smooth": True, "material": {"Base Color": [0.5, 0.46, 0.4], "Roughness": 0.9, "Specular IOR Level": 0.2}})
    if len(R):
        V = spheres(C, R)
        np.savez(bp, V=V, F=np.arange(V.shape[0], dtype=np.int32).reshape(-1, 3))
        meshes.append({"name": "bub", "npz": bp, "smooth": True, "shader_py": SHP, "params": {"ior": 1.0 / N_SUGAR}})

    # where the arc's top is, from the sugar's own surface
    k = np.unravel_index(np.argmax(S @ up.astype(np.float32)), S.shape[:2])
    apex = S[k].astype(float)
    H = o["W"] * 9 / 16
    target = np.array([(0.5 - o["cx"]) * o["W"], 0.0, 0.0]) + up * (apex @ up - 0.02 * H)  # across the frame by the fruit's centre: its highest point jumps about as soon as the shape changes  # the top of the arc at y = .48
    cam = frame_camera(target, view, o["W"], o["dist"], aperture_mm=o["ap"], focus_point=S[0, S.shape[1] // 2].astype(float))  # on the calyx, the subject  # focus a little in front of the arc, so that both the arc and the near face hold

    cam_seen = cam  # a test camera for looking at 100 % without rendering the whole frame: zw is its width, ztx and ztz move it
    if o["zw"]:
        cam_seen = frame_camera(target + np.array([o["ztx"], 0.0, 0.0]) + up * o["ztz"], view, o["zw"], o["dist"], aperture_mm=o["ap"], focus_point=S[0, S.shape[1] // 2].astype(float))
    lens_plate(lp, cam, o)
    reflected_lights(bk, cam, o)
    emit = {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}
    meshes.append({"name": "plate", "npz": lp, "material": emit, "visible": {"diffuse": False, "shadow": False, "glossy": False}})
    meshes.append({"name": "lights", "npz": bk, "smooth": True, "material": emit, "visible": {"camera": False, "diffuse": False, "shadow": False}})
    sky = {"top": [0.001, 0.001, 0.001], "h": 0.5, "mottle": 0.0, "in_transmission": False}

    lights = [
        {"type": "gradient", "name": "sun", "loc": [16, 16, 16], "target": [0, 0, 1.2], "size": [9, 9], "sigma": [1.5, 1.5], "L": o["sun"], "rgb": [1.0, 0.97, 0.95]},
        {"type": "gradient", "name": "scrim", "loc": [-13, -20, 14], "target": [-0.3, -0.4, 1.0], "size": [16, 12], "sigma": [5, 3.5], "L": 5.0, "rgb": [0.97, 0.98, 1.0], "hide_in_gloss": True},
        {"type": "gradient", "name": "rim", "loc": [-15, 17, 7], "target": [0, 0, 1.0], "size": [5, 5], "sigma": [1.5, 1.5], "L": 60.0, "rgb": [1.0, 0.86, 0.68]},
        {"name": "box", "loc": [12, -17, 19], "target": [0, 0, 1.0], "size": [5, 7], "watts": 1500, "rgb": [0.98, 0.98, 1.0], "hide_in_gloss": True},  # its light on the skin
        {"type": "gradient", "name": "box_seen", "loc": [12, -17, 19], "target": [0, 0, 1.0], "size": [5, 7], "sigma": [2.6, 3.6], "L": 14.0, "rgb": [0.98, 0.98, 1.0], "hide_in_diffuse": True},
        {"name": "low", "loc": [-10, -6, -8], "target": [-0.5, -0.8, 0.8], "size": [8, 8], "watts": 1100, "rgb": [1.0, 0.9, 0.9], "hide_in_gloss": True, "hide_in_transmission": True},
    ]
    off = int(o["off"])  # switches, for finding which light does what: a bit for each lamp in order, 64 the small lights, 128 the room
    lights = [l for i_, l in enumerate(lights) if not off >> i_ & 1]
    if off & 64:
        meshes = [m for m in meshes if m["name"] != "lights"]
    e = environment(os.path.join(D, f"{tag}_env.npy"), cam, o)
    spp = int(o["spp"]) or {"preview": 128, "mid": 256, "final": 1024}[q]
    return {
        "camera": cam_seen,
        "meshes": meshes,
        "lights": lights,
        "env": {"npy": e, "diffuse": False, "transmission": not off & 128},
        "sky": sky,
        "bounces": 32,
        "transmission_bounces": 28,
        "glossy_bounces": 12,
        "diffuse_bounces": 3,
        "volume_bounces": 0,
        "clamp_indirect": 30.0,
        "denoise": bool(o["dn"]),
        "spp": {q: spp},
    }


def parse(s):
    o = dict(P0)
    for kv in filter(None, s.split(",")):
        k, v = kv.split("=")
        if k not in P0:
            raise SystemExit(f"unknown parameter {k}")
        o[k] = float(v)
    return o


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "look":
        raise SystemExit(__doc__)
    tag, over = sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""
    q = sys.argv[4] if len(sys.argv) > 4 else "preview"
    o = parse(over)
    shoot(NAME, scene(tag, o, q), q, dict(DEVELOP), tag=tag)
