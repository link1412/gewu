"""Shot 65: the oil-paper umbrella from above, turning in the hand. A long lens from an upper floor looks down on it in a bamboo grove just after rain; its far rim is the arc, the wet stones far below are the dark above the arc.

    python3 -I v2/stills/s65_zhuansan.py [sketch|preview|mid|final]     one still
    python3 -I v2/stills/s65_zhuansan.py motion [q]                     all frames at 640x360, spp 40: out/v2/s65_zhuansan_move_preview/ with take.mp4 and sheet.jpg (the render of kit's GEWU_MOVE=preview takes every 6th frame, which shows no motion)
    GEWU_MOVE=check|final python3 -I v2/stills/s65_zhuansan.py final    kit's own take; the move comes from MOVE below until it is in v2/looks.json

From above, turning, not a dolly. The umbrella's parts come from s21_youzhisan.py (read with its last line, main(), cut off, so that s21 stays as it is and in the film).

What differs from s21, and why:
- the paper is seen from its outside, in sun. So what carries the picture is the outside of the sheet: a film of tung oil over a diffuse red sheet (s65_shader: a real Fresnel layer, not a reflective paint), and its relief (see paper()), which photographs of the real thing showed to be far deeper than I had assumed: every panel a tent hung upside down, with creases and crumples, and the sheen lying in whole facets broken at the folds;
- the sheet here is laid in separate sheets (seams at a few ribs), each a little different in colour: when it turns, that is what the eye follows, along with dried rain marks;
- it has just rained: drops sit on the oil, and each keeps its spark of sun where the geometry puts it, while the drop itself travels. Their highlights are not painted, they are the sun in a real refracting cap. The turning (5 to 8 rev/min) is far too slow to fling them off;
- light: a low sun from behind and to the left, so that the sheen is on the upper part of the dome and the panels are raked. Bamboo sprays between it and the umbrella throw shadows that stay still while the paper goes round under them.

Background: wet bluestone paving with fallen bamboo leaves, 165 cm below, out of focus (a background with a meaning: the ground under a person holding an umbrella; the rain is why it is dark, and it gives the red something cold to sit on). It is in the shade of the grove: a corridor of leaves between the sun and the part of the ground in frame leaves only a few flecks. Those leaves are out of frame.

Estimates, none measured: all sizes (s21's, Luzhou type, about 90 cm), the height of the umbrella over the ground, the lens (about 129 mm at 3 m), the oil's roughness, the paper's slack and wrinkle depth, the drop sizes and contact angle (taken as about 80-95 degrees for tung oil, from general knowledge, not checked). The sky is painted (lotuslib.pond_env), stands in for the grove's upper storey.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
from kit import OUT, blur, color, fbm, frame_camera, shoot, sstep
from lotuslib import pond_env
from s21_lib import smooth1d
from translib import SOFT, leaves, merge, save
from vessel import project, view_dir

NAME = "s65_zhuansan"
SHADER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s65_shader.py")

# --- the umbrella's parts, from s21 ---------------------------------------------------------------------------------
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s21_youzhisan.py")
_src = open(_p).read()
_src = _src[: _src.rindex("\nmain()")]
U = {"__file__": _p, "__name__": "s21_parts"}
exec(compile(_src, _p, "exec"), U)
R, H, NRIB, R0, RIB0, RIB_J = U["R"], U["H"], U["NRIB"], U["R0"], U["RIB0"], U["RIB_J"]
prof = U["prof"]

AXIS = np.array([0.05, 0.09, 1.0])  # the shaft leans a little away from the camera and to the right, as on a shoulder: more of the dome turns to the lens
AXIS = AXIS / np.linalg.norm(AXIS)
EL = 65.0  # the camera's elevation
W, DIST = 84.0, 300.0
APEX_Y = 0.24
APEX_X = 0.454  # so that the crown, not the arc's top, is near the middle: the shaft leans, so they differ by about 0.05 of the width
APERTURE = 42.0  # mm; about f/3 at this focal length
Z_GROUND = -165.0
SUN = np.array([-0.2, 0.87, 0.42])
SUN = SUN / np.linalg.norm(SUN)
SIGMA = color([0.12, 2.85, 3.2])  # for the red of the photographed umbrellas, (217,42,34) under flat light; s21's was a brownish vermilion, right for seeing through the sheet
TURN = -1.6  # degrees per frame; 7.5 degrees between ribs
FRAMES = 24
MOVE = {"spin": {"pt": [0.0, 0.0, 0.0], "axis": AXIS.tolist(), "deg": TURN * (FRAMES - 1), "meshes": ["paper", "ribs", "stretch", "lace", "wraps", "runner", "crown", "tip", "ring", "shaft", "drops"]}, "frames": FRAMES, "shutter": 0.5}


def basis():
    """e2 points to the far side, which is the top of the frame; e1 to the right. e1 x e2 = e3."""
    e3 = AXIS
    e2 = np.array([0.0, 1.0, 0.0]) - e3 * e3[1]
    e2 = e2 / np.linalg.norm(e2)
    return np.cross(e2, e3), e2, e3


U["basis"] = basis
world = U["world"]


def seen(a):
    """Paper is dense where the frame can see it, over the whole turn."""
    d = (a - np.pi / 2 + np.pi) % (2 * np.pi) - np.pi
    return np.abs(d) < np.radians(125)


def polar_field(seed, pxa=5.0, pxr=0.55, lo=0.3, hi=4.0, beta=2.6):
    """Noise in (radius, arc at the rim) so it runs lengthwise and closes up towards the crown. pxr < pxa stretches it along the radius."""
    return fbm((int(R * pxr * 2), int(2 * np.pi * R * pxa)), pxa, lo, hi, beta, seed).astype(np.float32), pxa, pxr


def polar_sample(F, az, Rr):
    tex, pxa, pxr = F
    return cv2.remap(tex, (az * pxa).astype(np.float32), (Rr * pxr).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)


def paper(dens, ang, tips, seed=21):
    """The sheet, its outside facing up. Rows run from crown to rim and columns round it, so grid_mesh's normal (row x column) points out of the dome, up."""
    rng = np.random.default_rng(seed + 1)
    F = U["flat_fields"](dens, seed)
    sample = U["sample"]
    pan = 2 * np.pi * R / NRIB
    n_d, n_c = max(int(pan * 30 * dens), 20), 12
    us = []
    for i in range(NRIB):
        m = n_d if seen(ang[i]) or seen(ang[(i + 1) % NRIB]) else n_c
        us.append(i + np.arange(m, dtype=np.float64) / m)
    u = np.concatenate(us + [np.array([float(NRIB)])])
    nx = u.size
    ny = max(int((R - R0) * 30 * dens), 90)
    v = np.linspace(0, 1, ny, dtype=np.float64)
    i = np.floor(u).astype(np.int32)
    i[-1] = NRIB - 1
    t = (u - i).astype(np.float32)
    t[-1] = 1.0
    a0, a1 = ang[i % NRIB], ang[(i + 1) % NRIB]
    a1 = np.where(a1 < a0, a1 + 2 * np.pi, a1)

    # the rim: a slack cut from tip to tip; fibrous at the smallest scale, a few small nicks
    tip = (1 - t) * tips[i % NRIB] + t * tips[(i + 1) % NRIB] - 0.55
    scal = rng.uniform(0.1, 0.32, NRIB)[i % NRIB]
    edge = tip + 0.05 - scal * (4 * t * (1 - t)) ** 0.8 + 0.035 * smooth1d(nx, 26, rng) + 0.012 * smooth1d(nx, 3.5, rng)
    for _ in range(40):
        c = int(rng.integers(0, nx))
        hw = rng.uniform(4, 28) * dens
        edge = edge - rng.uniform(0.03, 0.14) * sstep(hw, hw * 0.2, np.abs(np.arange(nx) - c))

    Rr = (R0 + (edge[None, :] - R0) * v[:, None]).astype(np.float32)
    T = t[None, :].repeat(ny, 0)
    I = i[None, :].repeat(ny, 0)
    A0, A1 = a0[None, :], a1[None, :]
    x = Rr * ((1 - T) * np.cos(A0) + T * np.cos(A1))
    y = Rr * ((1 - T) * np.sin(A0) + T * np.sin(A1))
    Ru = Rr / R
    az = (np.arctan2(y, x) % (2 * np.pi)) * R

    # --- the shape, as ref/umbrella_top shows it: not a smooth dome. The sheet is longer than the ribs' spacing, because it has to fold shut; so each panel is a tent hung upside down, ridge on the rib, a sharp valley at its fold, with its depth different panel to panel and the fold off the middle. Beside it, shorter creases that memory of folding left, and small crumples across the grain. The rib-to-valley relief is what makes the radial light and dark
    wob = smooth1d(NRIB * 8, 3.0, rng)
    tc = 0.5 + np.interp(((I + Ru) * 8) % (NRIB * 8), np.arange(NRIB * 8), wob) * 0.012 + rng.normal(0, 0.05, NRIB)[I % NRIB]
    pw = np.maximum(2 * np.pi * Rr / NRIB, 0.3)  # panel width here, cm
    d_c = np.abs(T - tc) * pw
    d_rib = np.minimum(T, 1 - T) * pw
    depth = rng.uniform(0.32, 0.92, NRIB)[I % NRIB]
    tl = np.where(T < tc, T / tc, (1 - T) / (1 - tc))
    vee = tl**1.2
    fold = np.exp(-d_c / (0.05 * pw + 0.05))
    z = prof(Rr) + 0.07 - depth * Ru**1.1 * vee - 0.1 * fold * Ru
    # the creases, each its own: where across the panel, how deep, over which part of the radius, and it wanders
    for k in range(NRIB):
        cols_k = np.nonzero(i % NRIB == k)[0]
        if not seen(ang[k]) and not seen(ang[(k + 1) % NRIB]):
            continue
        for _ in range(int(rng.integers(1, 6))):
            tk = rng.uniform(0.1, 0.9)
            dp = rng.uniform(0.08, 0.38)
            r0 = rng.uniform(3, 36)
            r1 = r0 + rng.uniform(6, 34)
            wander = 0.016 * smooth1d(ny, 120, rng) + 0.004 * smooth1d(ny, 24, rng)
            tt = T[:, cols_k] - tk - wander[:, None]
            win = sstep(r0, r0 + 3, Rr[:, cols_k]) * sstep(r1, r1 - 3, Rr[:, cols_k])
            wd = 0.05 * pw[:, cols_k] + 0.04
            dist_k = np.abs(tt) * pw[:, cols_k]
            # a crease is a valley with a ridge pushed up on each side of it
            z[:, cols_k] += dp * (0.55 * np.exp(-(((dist_k - 1.6 * wd) / (1.3 * wd)) ** 2)) - np.exp(-dist_k / wd)) * win * Ru[:, cols_k] ** 0.7
    lift = sstep(0.0, 0.5, d_rib)  # nothing pushes the paper off a rib: the noise below dies out on it, or ribs would come through
    wr1 = polar_sample(polar_field(seed + 11, pxa=6.0, pxr=0.5, lo=0.22, hi=1.6, beta=2.2), az, Rr)
    wr2 = polar_sample(polar_field(seed + 12, pxa=3.0, pxr=0.5, lo=0.8, hi=8.0, beta=2.6), az, Rr)
    crum = polar_sample(polar_field(seed + 13, pxa=1.0, pxr=6.0, lo=1.2, hi=6.0, beta=2.2), az, Rr)
    crum_on = sstep(0.1, 1.0, polar_sample(polar_field(seed + 14, pxa=1.0, pxr=0.6, lo=4.0, hi=16.0, beta=2.0), az, Rr))
    z = z + lift * (0.012 * wr1 * (0.3 + 0.7 * Ru) + 0.045 * wr2 * Ru + 0.05 * crum * crum_on * (0.3 + 0.7 * Ru))
    z = z + lift * (0.05 * sample(F, "patches", x, y) * (0.3 + 0.7 * Ru) + 0.006 * sample(F, "clouds", x, y))

    # --- the sheet's layers
    clouds = sample(F, "clouds", x, y)
    fine = sample(F, "fine", x, y)
    fib = sample(F, "fib", x, y)
    patch = sample(F, "patches", x, y)
    oil = polar_sample(polar_field(seed + 8, pxa=3.2, pxr=1.0, lo=0.5, hi=9.0, beta=2.0), az, Rr)
    oil = cv2.GaussianBlur(oil, (0, 0), 1.5)
    tear = sample(F, "clouds", x * 1.7 + 11, y * 1.7 - 7)
    strip_w = rng.uniform(0.3, 0.55, NRIB + 1)
    wleft, wright = strip_w[I % NRIB], strip_w[(I + 1) % NRIB]
    strip = sstep(0.09, -0.09, np.where(T < 0.5, T * pw - wleft, (1 - T) * pw - wright) + 0.03 * tear)
    # the sheets: each runs over a few ribs, its edge lapped beside one of them, and each a little different in colour
    laps = np.cumsum(rng.integers(3, 7, NRIB)) % NRIB
    laps = np.unique(laps)
    sheet_of = np.searchsorted(laps, np.arange(NRIB), side="right") % max(len(laps), 1)
    tint = rng.normal(0, 1, (len(laps) + 1, 3))
    seam = np.zeros_like(Rr)
    for sr in laps:
        wd = rng.uniform(0.9, 1.5)
        on = I % NRIB == sr
        seam = np.maximum(seam, on * sstep(0.1, -0.1, T * pw - wd * (0.75 + 0.25 * Ru) + 0.03 * tear))
    hem_w = 0.9 + 0.1 * sample(F, "patches", x * 2.1, y * 2.1) + 0.02 * tear
    hem = sstep(0.12, -0.12, edge[None, :] - Rr - hem_w)
    cap_r = 3.2 + 0.2 * sample(F, "patches", x * 3, y * 3) + 0.14 * tear
    cap = sstep(0.1, -0.1, Rr - cap_r)
    wear = np.exp(-((d_c / 0.05) ** 2)) * sstep(-0.3, 1.2, sample(F, "patches", x * 4.5, y * 4.5)) * sstep(0.25, 0.7, Ru)
    wm = U["water_marks"](x, y, seed + 40)
    stain = sstep(1.0, 1.25, wm)
    tide = np.exp(-(((wm - 1.0) / 0.045) ** 2)) * sstep(0.2, 0.5, Ru)

    layers = 1.0 + 0.1 * strip + 0.13 * seam + 0.28 * hem + 0.2 * cap
    p = layers * (1.0 + 0.03 * clouds + 0.015 * fine + 0.14 * (fib - fib.mean()) - 0.03 * oil + 0.03 * patch)
    p = p - 0.13 * wear - 0.03 * stain + 0.14 * tide + 0.07 * sstep(R - 8.0, R, Rr)
    p = np.maximum(p, 0.25)
    Tc = np.exp(-p[..., None] * SIGMA)
    dim = np.exp(-0.34 * (p[..., None] - 1.0))
    trm = np.clip(Tc * dim * color([1.0, 0.98, 0.94]), 0, 1)
    # the sheet in reflection: a paper's colour is its own pigment seen twice through. Sheets differ; sun fades the crown-side less than the rim
    sh = tint[sheet_of[I % NRIB]]
    alb = np.power(Tc, 1.15) * color([0.8, 0.62, 0.62]) * (1 - 0.45 * fold * Ru)[..., None]  # oil pools in the folds
    alb = alb * (1 + 0.05 * sh[..., 0:1]) * (1 + np.array([0.0, 0.07, 0.03], np.float32) * sh[..., 1:2])
    alb = alb * (1 + 0.1 * sstep(0.5, 1.0, Ru) * (0.5 + 0.5 * np.clip(patch, -1, 1)))[..., None]
    col = np.clip(alb, 0, 1)
    # the oil: thicker in streaks that run down from the crown, thin at the worn folds and where the rain has dried
    film = np.clip(0.85 + 0.08 * oil + 0.05 * patch - 0.5 * wear - 0.12 * stain, 0.15, 1.0)
    rough = np.clip(0.16 + 0.04 * patch - 0.02 * oil + 0.015 * fine + 0.2 * wear + 0.07 * stain, 0.1, 0.6)
    P = world(x, y, z)
    return P.astype(np.float32), {"col": col.astype(np.float32), "tr": trm.astype(np.float32), "film": film.astype(np.float32), "rough": rough.astype(np.float32)}


def crown_top(d):
    """The head of the umbrella, from above, as in ref/umbrella_top: a small dome of red-lacquered paper about 4 cm across on a dark bound ring, the bamboo's tip showing at its centre. Sizes read off those photographs, roughly."""
    revolve = U["revolve"]
    dome = np.array([[0.0, H + 2.2], [0.5, H + 2.15], [0.62, H + 2.02], [1.0, H + 1.82], [1.5, H + 1.32], [1.86, H + 0.68], [2.0, H + 0.2], [2.02, H - 0.2], [1.2, H - 0.6]])
    p_dome = revolve(os.path.join(d, "crown.npz"), dome, [0.36, 0.014, 0.011])
    tip = np.array([[0.0, H + 2.42], [0.22, H + 2.38], [0.38, H + 2.26], [0.46, H + 2.1], [0.5, H + 1.9]])
    p_tip = revolve(os.path.join(d, "tip.npz"), tip, [0.42, 0.27, 0.13])
    ring = np.array([[1.9, H + 0.28], [2.12, H + 0.22], [2.24, H + 0.02], [2.3, H - 0.18], [2.28, H - 0.3], [1.6, H - 0.5]])
    p_ring = revolve(os.path.join(d, "ring.npz"), ring, [0.03, 0.008, 0.008])
    return p_dome, p_tip, p_ring


def ground(path, q):
    """Bluestone paving, wet: separate slabs in rows, a little tilted each, each its own grey; a sunk joint of dirt and moss; water lying in the low places. Far out of focus, so coarse."""
    n = {"sketch": 800, "preview": 900, "mid": 1200, "final": 1500}[q]
    xs = np.linspace(-280.0, 280.0, n, dtype=np.float32)
    ys = np.linspace(-120.0, 440.0, n, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys)
    S = (n - 1) / 560.0
    rng = np.random.default_rng(6565)
    th = np.radians(17.0)
    U_ = np.cos(th) * X + np.sin(th) * Y
    V_ = -np.sin(th) * X + np.cos(th) * Y
    warp = fbm((n, n), S, 2.0, 40.0, 2.6, 301)
    Vw = V_ + 1.1 * warp
    v_edges = np.cumsum(rng.uniform(26, 44, 40)) - 500
    row = np.searchsorted(v_edges, Vw)
    Uw = U_ + 300.0 * 0 + 1.1 * fbm((n, n), S, 2.0, 40.0, 2.6, 302)
    label = np.zeros((n, n), np.int32)
    d_u = np.zeros((n, n), np.float32)
    for r_ in range(len(v_edges) + 1):
        m = row == r_
        if not m.any():
            continue
        e = np.cumsum(rng.uniform(42, 100, 50)) - 2200 + rng.uniform(0, 60)
        k = np.searchsorted(e, Uw[m])
        label[m] = r_ * 100 + k
        ek = np.r_[-1e4, e, 1e4]
        d_u[m] = np.minimum(Uw[m] - ek[k], ek[k + 1] - Uw[m])
    ve = np.r_[-1e4, v_edges, 1e4]
    d_v = np.minimum(Vw - ve[row], ve[row + 1] - Vw)
    dist = np.minimum(d_u, d_v)
    edge = sstep(0.25, 2.8, dist)
    ids, inv = np.unique(label, return_inverse=True)
    inv = inv.reshape(n, n)
    tone = rng.uniform(0.62, 1.3, len(ids))[inv]
    cool = rng.normal(0, 1, len(ids))[inv]
    tx, ty, h0 = rng.normal(0, 0.006, len(ids))[inv], rng.normal(0, 0.006, len(ids))[inv], rng.normal(0, 0.18, len(ids))[inv]
    large = fbm((n, n), S, 6.0, 70.0, 2.8, 303)
    mid = fbm((n, n), S, 1.0, 9.0, 2.4, 304)
    z = Z_GROUND + edge * (h0 + tx * U_ * 0.03 + ty * V_ * 0.03 + 0.1 * large + 0.03 * mid) - 0.9 * (1 - edge)
    # water lies where the slab is low and in the worn middle of the path
    pool = sstep(0.1, 0.85, -large * 0.8 - h0 * 2.0 + 0.2 * mid)
    wet = np.clip(0.55 + 0.45 * pool + 0.2 * mid, 0, 1)
    base = np.stack([0.062 * (1 - 0.1 * cool), np.full_like(cool, 0.07), 0.074 * (1 + 0.14 * cool)], -1).astype(np.float32) * tone[..., None]
    base = base * (1 + 0.28 * mid + 0.2 * large)[..., None]
    base = base * (1 - 0.5 * wet)[..., None] * 0.6
    soil = color([0.018, 0.015, 0.011])
    moss = color([0.016, 0.024, 0.007]) * (1 + 0.5 * mid)[..., None]
    moss_k = sstep(0.3, 1.4, fbm((n, n), S, 3.0, 30.0, 2.6, 305))[..., None]
    col = base * edge[..., None] + (soil * (1 - moss_k) + moss * moss_k) * (1 - edge)[..., None]
    rough = np.clip(0.42 - 0.34 * pool + 0.05 * mid, 0.05, 0.7) * edge + 0.8 * (1 - edge)
    P = np.stack([X, Y, z], -1).astype(np.float32)
    # rows run +y here and columns +x, whose normal (row x col) is down: reverse the rows
    np.savez(path, P=P[::-1], col=np.clip(col, 0, 1)[::-1].astype(np.float32), rough=rough[::-1].astype(np.float32))
    return dist


def fallen(path, n=520, seed=650):
    """Fallen bamboo leaves: lying flat, more of them along the joints and in drifts; old ones pale ochre, a few still green."""
    rng = np.random.default_rng(seed)
    drift = fbm((256, 256), 256 / 560.0, 20.0, 160.0, 3.0, seed)
    at = []
    while len(at) < n:
        x, y = rng.uniform(-260, 260), rng.uniform(-100, 420)
        ix, iy = int((x + 280) / 560 * 255), int((y + 120) / 560 * 255)
        if rng.random() < 0.15 + 0.6 * np.clip(drift[iy, ix], 0, 1.5):
            at.append((x, y, Z_GROUND + rng.uniform(0.3, 0.9)))
    at = np.array(at)
    a = rng.uniform(0, 2 * np.pi, n)
    A = np.stack([np.cos(a), np.sin(a), rng.normal(0, 0.03, n)], -1)
    N = np.array([0.0, 0.0, 1.0]) + rng.normal(0, 0.12, (n, 3))
    L, Wd = rng.uniform(8, 17, n), rng.uniform(1.0, 2.0, n)
    age = rng.random(n)[:, None]
    tone = rng.uniform(0.7, 1.2, (n, 1))
    col = (color([0.34, 0.2, 0.06]) * (1 - age) ** 1 + color([0.1, 0.13, 0.03]) * age * 0.7) * tone * (1 - 0.35 * rng.random((n, 1)))
    return save(path, leaves(rng, at, A, N, L, Wd, col, col * color([0.7, 0.55, 0.3]), ns=6, droop=-0.012, curl=0.06))


def twig(rng, at, up, n_leaf):
    """A bamboo twig: leaves fanning from a short stem, so that its shadow reads as bamboo and not as a net."""
    axis = up / np.linalg.norm(up)
    L0 = rng.uniform(14, 26)
    base = at[None] + rng.uniform(-0.5, 0.5, (n_leaf, 1)) * L0 * axis[None]
    fan = rng.normal(0, 1, (n_leaf, 3))
    fan = fan - axis[None] * np.sum(fan * axis[None], -1, keepdims=True)
    fan = fan / np.linalg.norm(fan, axis=-1, keepdims=True)
    A = fan + np.array([0, 0, -0.5]) + 0.5 * axis[None]
    N = np.cross(A, SUN[None])  # the blades face the light more than not, or their shadows are lines
    N = np.cross(N, A) + 0.7 * rng.normal(0, 1, (n_leaf, 3))
    L, Wd = rng.uniform(9, 17, n_leaf), rng.uniform(1.1, 2.0, n_leaf)
    tone = rng.uniform(0.7, 1.25, (n_leaf, 1))
    return leaves(rng, base, A, N, L, Wd, np.array([[0.05, 0.13, 0.035]]) * tone, np.array([[0.2, 0.42, 0.06]]) * tone, ns=7)


def corridor(path, cam, n, seed=652):
    """Leaves between the sun and the part of the ground in frame: the grove's shade. They hang along the sun's line through points on that ground, at a height out of the frame, gathered in clumps with gaps; it is the gaps that make the flecks."""
    rng = np.random.default_rng(seed)
    gaps = fbm((512, 512), 1.0, 8.0, 90.0, 2.8, seed)
    pts = []
    tries = 0
    while len(pts) < n and tries < n * 30:
        tries += 1
        g = np.array([rng.uniform(-170, 170), rng.uniform(0, 300), Z_GROUND])
        hit = (rng.uniform(260, 620)) / SUN[2]
        p = g + SUN * hit
        ix, iy = (int(g[0] * 0.8) + 256) % 512, (int(g[1] * 0.8) + 256) % 512
        if gaps[iy, ix] < -0.15 + rng.normal(0, 0.1):  # gaps in the leaves
            continue
        pts.append(p)
    at = np.array(pts)
    x, y, wd = project(cam, at)
    print(f"corridor: {len(at)} leaves, in frame {int(np.sum((x > -0.05) & (x < 1.05) & (y > -0.05) & (y < 1.05) & (wd > 0)))}", flush=True)
    keep = ~((x > -0.05) & (x < 1.05) & (y > -0.05) & (y < 1.05) & (wd > 0))
    at = at[keep]
    m = len(at)
    A = rng.normal(0, 1, (m, 3)) + np.array([0, 0, -0.5])
    Nn = rng.normal(0, 1, (m, 3))
    tone = rng.uniform(0.7, 1.25, (m, 1))
    return save(path, leaves(rng, at, A, Nn, rng.uniform(14, 28, m), rng.uniform(2.4, 4.2, m), color([0.05, 0.11, 0.035]) * tone, color([0.11, 0.21, 0.035]) * tone, ns=4))


def near_sprays(path, cam):
    """Bamboo sprays on the sun's line through the paper: their shadows on the dome are nearly sharp, and they do not turn with it."""
    rng = np.random.default_rng(653)
    e1, e2, e3 = basis()
    sp = []
    for xl, yl, dd, up_, nl in ((36.0, 10.0, 80.0, (0.5, 0.7, 0.3), 34),):
        sp.append(twig(rng, xl * e1 + yl * e2 + 7 * e3 + SUN * dd, np.array(up_, float), nl))
    m = merge(*sp)
    x, y, wd = project(cam, m["V"])
    print(f"sprays in frame: {int(np.sum((x > 0) & (x < 1) & (y > 0) & (y < 1) & (wd > 0)))} of {len(x)} points", flush=True)
    return save(path, m)


def drop_caps(path, P, q, seed=654):
    """Rain on the oil. Each drop is a real cap on the surface: contact outline not quite round (it is pinned on the fibre), flattened by its own weight when large. Open at the base; the base sits just under the paper. Drops gather along the folds; a few runs have swept lanes clean."""
    rng = np.random.default_rng(seed)
    ny, nx = P.shape[:2]
    n = {"sketch": 1000, "preview": 2000, "mid": 3000, "final": 4000}[q]
    # area-weighted random points of the grid: rows further out hold more; the columns are not uniform (dense where seen), so draw by position
    Ru = (np.arange(ny) + 0.5) / ny
    rows = rng.choice(ny - 4, size=n * 3, p=(Ru[:-4] ** 1.1) / np.sum(Ru[:-4] ** 1.1)) + 2
    cols = rng.integers(2, nx - 3, size=n * 3)
    lanes = fbm((256, 512), 1.0, 2.0, 30.0, 2.6, seed)
    keep = []
    for a, b in zip(rows, cols):
        if rng.random() < 0.5 + 0.45 * lanes[int(a / ny * 255), int(b / nx * 511)]:
            keep.append((a, b))
        if len(keep) >= n:
            break
    keep = np.array(keep)
    a, b = keep[:, 0], keep[:, 1]
    c = P[a, b].astype(np.float64)
    du = P[a + 1, b] - P[a - 1, b]
    dv = P[a, b + 1] - P[a, b - 1]
    nn = np.cross(du, dv).astype(np.float64)
    nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    t1 = du / np.linalg.norm(du, axis=1, keepdims=True).astype(np.float64)
    t2 = np.cross(nn, t1)
    m = len(c)
    rad = np.clip(rng.lognormal(np.log(0.085), 0.55, m), 0.03, 0.42)
    theta = np.radians(rng.uniform(70, 95, m))
    ht = rad * np.tan(theta / 2) * np.clip(1.0 - 0.9 * rad, 0.55, 1.0)  # a cap of this contact angle, flattened with size
    nlat, nlon = 7, 18
    lat = np.linspace(0.0, 1.0, nlat)
    lon = np.linspace(0, 2 * np.pi, nlon, endpoint=False)
    Vs = np.zeros((m, nlat, nlon, 3), np.float32)
    ph = rng.uniform(0, 6.28, (m, 3))
    for i, (cc, nr, a1, a2, r_, h_, p_) in enumerate(zip(c, nn, t1, t2, rad, ht, ph)):
        out = 1 + 0.09 * np.sin(2 * lon + p_[0]) + 0.05 * np.sin(3 * lon + p_[1]) + 0.03 * np.sin(5 * lon + p_[2])
        # s = 0 at the contact line, 1 at the top: radius as a circle's arc through the contact angle
        rr = r_ * np.cos(lat * np.pi / 2) ** 0.85
        zz = h_ * np.sin(lat * np.pi / 2) - 0.012
        Vs[i] = cc[None, None] + (rr[:, None] * out[None] * np.cos(lon)[None])[..., None] * a1[None, None] + (rr[:, None] * out[None] * np.sin(lon)[None])[..., None] * a2[None, None] + zz[:, None, None] * nr[None, None]
    idx = np.arange(m * nlat * nlon).reshape(m, nlat, nlon)
    q1, q2, q3, q4 = idx[:, :-1, :], idx[:, :-1, np.r_[1:nlon, 0]], idx[:, 1:, np.r_[1:nlon, 0]], idx[:, 1:, :]
    F = np.concatenate([np.stack([q1, q2, q3], -1).reshape(-1, 3), np.stack([q1, q3, q4], -1).reshape(-1, 3)])
    np.savez(path, V=Vs.reshape(-1, 3), F=F.astype(np.int32), dummy=np.zeros(Vs.size // 3, np.float32))
    print(f"drops {m}, radius p50 {np.median(rad):.3f} p99 {np.percentile(rad, 99):.3f} cm", flush=True)
    return path


def build(q):
    dens = {"sketch": 0.3, "preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    ang = U["rib_angles"](21)
    tips = R + np.random.default_rng(23).normal(0, 0.1, NRIB)
    P, at = paper(dens, ang, tips)
    p_paper = os.path.join(d, f"paper.{q}.npz")
    np.savez(p_paper, P=P, **at)
    zr = -9.5
    p_ribs = save(os.path.join(d, "ribs.npz"), U["ribs"](ang, tips))
    p_str = save(os.path.join(d, "stretch.npz"), U["stretchers"](ang, zr))
    p_lace = save(os.path.join(d, "lace.npz"), U["lacing"](ang))
    p_wrap = save(os.path.join(d, "wraps.npz"), U["wraps"](ang, tips))
    revolve = U["revolve"]
    p_run = revolve(os.path.join(d, "runner.npz"), np.array([[0.0, zr - 5.0], [0.85, zr - 5.0], [1.2, zr - 4.6], [1.5, zr - 3.0], [2.0, zr - 1.2], [2.2, zr - 0.6], [2.2, zr + 1.2], [2.3, zr + 1.6], [1.0, zr + 2.2]]), [0.022, 0.012, 0.01])
    p_crn, p_tip, p_ring = crown_top(d)
    p_sha = revolve(os.path.join(d, "shaft.npz"), np.array([[0.85, -90.0], [0.85, H - 1.0]]), [0.3, 0.2, 0.08], n=24)
    p_drop = drop_caps(os.path.join(d, f"drops.{q}.npz"), P, q)

    # The frame is fitted to the nominal rim, not to the mesh's last row: its points depend on the density, and the highest of them would move the framing between qualities
    az = np.linspace(-np.pi, np.pi, 2881)
    rim = world(az, np.full_like(az, R), np.full_like(az, prof(R)))
    view = view_dir(-90.0, EL)
    H_f = W * 9 / 16
    tgt = np.array([0.0, 0.0, 0.0])
    right = np.cross(np.array([0, 0, 1.0]), view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    for _ in range(6):
        cam = frame_camera(tgt, view, W, DIST)
        x, y, _ = project(cam, rim.reshape(-1, 3))
        k = int(np.argmin(y))
        tgt = tgt + up * (-(float(y[k]) - APEX_Y) * H_f) * -1 * -1
        tgt = tgt + right * ((float(x[k]) - APEX_X) * W)
    focus = world(np.array(-4.0), np.array(R - 16.0), np.array(prof(R - 16.0)))
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, rim.reshape(-1, 3))
    k = int(np.argmin(y))
    print(f"apex y {y[k]:.3f} at x {x[k]:.3f}; rim leaves the frame at y {np.interp(0.0, np.sort(x[y < 1.5]), y[y < 1.5][np.argsort(x[y < 1.5])]):.3f}", flush=True)
    xh, yh, _ = project(cam, np.array([world(np.array(0.0), np.array(0.0), np.array(H))]))
    print(f"crown at {xh[0]:.3f},{yh[0]:.3f}; lens {cam['lens_mm']:.1f}", flush=True)

    p_g = os.path.join(d, f"ground.{q}.npz")
    ground(p_g, q)
    p_fall = fallen(os.path.join(d, "fallen.npz"))
    p_cor = corridor(os.path.join(d, f"corridor.{q}.npz"), cam, {"sketch": 8000, "preview": 12000, "mid": 16000, "final": 20000}[q])
    p_spr = near_sprays(os.path.join(d, "sprays.npz"), cam)

    PAPER = {"kind": "paper", "k": 0.42, "fw": 0.1, "fw_rough": 0.42, "fw_ior": 1.22, "spec": 0.1, "coat_ior": 1.5, "wr": 0.012}
    WOOD = {"k": 0.4, "rough": 0.36, "spec": 0.42, "smooth": True}
    LEAF = {"k": 0.55, "fw": 0.0, "rough": 0.42, "spec": 0.4, "smooth": True}
    meshes = [
        {"name": "paper", "npz": p_paper, "shader_py": SHADER, "params": PAPER},
        {"name": "ribs", "npz": p_ribs, "shader_py": SOFT, "params": WOOD},
        {"name": "stretch", "npz": p_str, "shader_py": SOFT, "params": WOOD},
        {"name": "lace", "npz": p_lace, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.38, "spec": 0.5, "sheen": 0.5}},
        {"name": "wraps", "npz": p_wrap, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.4, "spec": 0.5, "sheen": 0.4}},
        {"name": "tip", "npz": p_tip, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.35, "spec": 0.5}},
        {"name": "ring", "npz": p_ring, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.4, "spec": 0.5, "sheen": 0.3}},
        {"name": "runner", "npz": p_run, "shader_py": SOFT, "params": WOOD},
        {"name": "crown", "npz": p_crn, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.25, "spec": 0.55}},
        {"name": "shaft", "npz": p_sha, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.3, "spec": 0.5}},
        {"name": "drops", "npz": p_drop, "shader_py": SHADER, "params": {"kind": "water"}, "visible": {"shadow": False, "diffuse": False}},
        {"name": "ground", "npz": p_g, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5}},
        {"name": "fallen", "npz": p_fall, "shader_py": SOFT, "params": {"k": 0.25, "rough": 0.35, "spec": 0.45, "smooth": True}},
        {"name": "corridor", "npz": p_cor, "shader_py": SOFT, "params": LEAF, "visible": {"camera": False}},
        {"name": "sprays", "npz": p_spr, "shader_py": SOFT, "params": LEAF, "visible": {"camera": False}},
    ]
    tgt_l = np.array([0.0, 0.0, 0.0])
    lights = [{"name": "sun", "loc": (tgt_l + SUN * 900.0).tolist(), "target": tgt_l.tolist(), "size": [11, 11], "watts": 10800000, "rgb": [1.0, 0.95, 0.87], "hide_in_gloss": True}]
    env = pond_env(os.path.join(d, "env.npy"), SUN, top=(0.5, 0.66, 0.92), low=(0.75, 0.82, 0.8), tree=(0.05, 0.1, 0.04), tree_el=30.0, pond=(0.05, 0.075, 0.035), cloud=0.6, gain=0.5, seed=65, soft=6.0, gaps=0.2, aureole=(24.0, 5.0))
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": env, "diffuse": True, "transmission": True},
        "bounces": 16,
        "diffuse_bounces": 6,
        "glossy_bounces": 6,
        "transmission_bounces": 12,
        "spp": {"sketch": 64, "preview": 128, "mid": 192, "final": 320},
    }
    return scene


LOOK = {"exposure": -0.4, "contrast": 1.16, "saturation": 1.04, "black": 0.001, "grain": 0.9, "sharpen": 0.18, "halation": 0.05, "glare": 0.004, "vignette": 0.25}


def _small_take(name, cfg, lk, move, develop, q):
    """All frames, small, so that the motion can be judged. Everything else as kit._take. The first and last frames of a keyed spin have half the blur: there is no key beyond them."""
    mv = lk["move"]
    path = kit.camera_path(cfg["camera"], cfg.get("lights", []), mv, mv["frames"])
    d = os.path.join(OUT, f"{name}_move_preview")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    cfg.update(res=[640, 360], frames=path, fetch_to=d, shutter=mv.get("shutter", 0.5), spin=mv["spin"], spp=40)
    kit._render_local(cfg, os.path.join(OUT, name), "take")
    from darkroom import develop as dev

    for i, f in enumerate(sorted(x for x in os.listdir(d) if x.endswith(".npy"))):
        im = dev(np.load(os.path.join(d, f)).astype(np.float32), **{**develop, "seed": 700 + i})
        cv2.imwrite(os.path.join(d, f"f{i:03d}.png"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(d, "f%03d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(d, "take.mp4")], check=True)
    ims = [cv2.imread(os.path.join(d, f"f{i:03d}.png")) for i in range(0, mv["frames"], 2)]
    cv2.imwrite(os.path.join(d, "sheet.jpg"), np.vstack([np.hstack(ims[r : r + 3]) for r in range(0, len(ims) - 2, 3)]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(os.path.join(d, "take.mp4"), flush=True)


def main():
    a = sys.argv[1:] or ["preview"]
    orig = kit.looks
    kit.looks = lambda: {**orig(), NAME: {"move": MOVE}}
    if a[0] == "motion":
        q = a[1] if len(a) > 1 else "sketch"
        kit._take = _small_take
        os.environ["GEWU_MOVE"] = "preview"
        shoot(NAME, build(q), "preview", tag="motion", develop=LOOK)
        return
    q = a[0]
    shoot(NAME, build(q), "preview" if q == "sketch" else q, tag=q, develop=LOOK)


main()
