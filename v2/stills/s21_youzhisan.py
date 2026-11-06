"""Shot 21: a whole oil-paper umbrella, open, tipped towards the sun, seen from underneath in a bamboo grove. Its upper rim is the arc.

    python3 -I v2/stills/s21_youzhisan.py [sketch|preview|mid|final]

The old shot was a flat radial picture on black (git history has it). Here everything is geometry and the light is a sun and a sky:
- paper on top, bamboo ribs under it, stretchers from the runner up to the ribs, the silk lacing, the crown and the shaft are separate solids;
- the sun comes from behind through the paper; what falls on it (shadows of bamboo sprays between the sun and the umbrella) is cast, not painted. The paper lets part of the light straight through (softsheet_shader `fw`), so a beam crosses the dome and the ribs throw shadows on the far paper;
- the background is a grove in true lens blur, lit by the same sun, under a sky.
All sizes are estimates from general knowledge (Luzhou type, about 90 cm across, about 48 ribs, set against ref/umbrella), not measured. The sky and the ground are a painted environment (lotuslib.pond_env), for what the holes in the leaves show and for the bounce. Thread colours are chosen, not from a given umbrella.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, frame_camera, shoot, sstep
from lotuslib import pond_env
from s21_lib import smooth1d, strokes
from translib import SOFT, leaves, merge, real_background, save, tubes
from vessel import project, view_dir

NAME = "s21_youzhisan"
R, H = 45.0, 13.5  # radius, rise of the dome (cm); estimates
NRIB = 48
R0 = 0.4
RIB0 = 2.6  # the ribs start here, in the crown
RIB_J = 19.5  # where the stretchers meet the ribs
AXIS_EL, AXIS_AZ = 60.0, 13.0  # the way the umbrella points
W, EL, DIST = 96.0, -19.0, 125.0
APEX = 0.25
APERTURE = 24.0
SUN = np.array([-0.30, 0.25, 0.92])
SUN = SUN / np.linalg.norm(SUN)
SIGMA = color([0.11, 1.62, 2.75])  # absorption per layer of paper with its pigment and oil: a muted, brownish vermilion; thin goes peach, thick goes deep red


def basis():
    a = np.radians(AXIS_EL)
    z = np.radians(AXIS_AZ)
    e3 = np.array([np.sin(z) * np.cos(a), np.cos(z) * np.cos(a), np.sin(a)])
    e1 = np.cross(e3, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e1 = -e1 if e1[0] < 0 else e1
    e2 = np.cross(e3, e1)
    e2 = -e2 if e2[2] < 0 else e2
    return e1, e2, e3


def world(x, y, z):
    e1, e2, e3 = basis()
    return x[..., None] * e1 + y[..., None] * e2 + z[..., None] * e3


def prof(r):
    return H * (1.0 - (np.abs(r) / R) ** 1.75)


def dprof(r):
    return -H * 1.75 * (np.abs(r) / R) ** 0.75 / R


def rib_angles(seed):
    """Hand-split and hand-spaced: uneven, by a few percent."""
    rng = np.random.default_rng(seed)
    return 2 * np.pi * np.arange(NRIB) / NRIB + rng.normal(0, 0.05 * 2 * np.pi / NRIB, NRIB)


def seen(a):
    """Is this angle in the half that faces the frame (top at 90 degrees)?"""
    d = (a - np.pi / 2 + np.pi) % (2 * np.pi) - np.pi
    return np.abs(d) < np.radians(100)


def flat_fields(dens, seed):
    """The paper as one flat sheet, in cm in the plane of the umbrella: mulberry fibre, its clouds, the fine tears at the folds. Sampled later by position, so nothing stretches towards the crown."""
    S = float(np.clip(30.0 * dens, 7, 30))  # px per cm
    n = int(2 * (R + 2) * S)
    rng = np.random.default_rng(seed)
    clouds = fbm((n, n), S, 0.35, 5.0, 2.3, seed + 1)  # formation: the fibre lies in clouds
    fine = fbm((n, n), S, 0.08, 0.5, 1.6, seed + 2)
    patches = fbm((n, n), S, 3.0, 30.0, 2.8, seed + 3)
    # long fibres, each its own curve, some lying together; a little favoured across the mould
    nf = int(60000 * min(dens, 1.0)) + 2000
    lines, vals = [], []
    for _ in range(nf):
        p0 = rng.uniform(0, n, 2)
        L = float(rng.lognormal(0.5, 0.55))  # cm
        a = rng.normal(0.3, 0.9)
        m = 6
        da = np.cumsum(rng.normal(0, 0.28, m))
        pts = [p0]
        for j in range(m):
            pts.append(pts[-1] + L / m * S * np.array([np.cos(a + da[j]), np.sin(a + da[j])]))
        lines.append(np.array(pts))
        vals.append(rng.uniform(0.25, 1.0))
    fib = blur(strokes((n, n), lines, 1, np.array(vals)), 0.55)
    return {"S": S, "n": n, "clouds": clouds, "fine": fine, "patches": patches, "fib": fib}


def sample(F, name, x, y):
    c = (R + 2) * F["S"]
    return cv2.remap(F[name].astype(np.float32), (x * F["S"] + c).astype(np.float32), (y * F["S"] + c).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def water_marks(x, y, seed):
    """Dried rain: a few big irregular stains, each with a slightly darker tide line at its edge. Coarse fields; a tide line is one contour of a smooth blob field."""
    S = 8.0
    n = int(2 * (R + 2) * S)
    f = fbm((n, n), S, 1.2, 14.0, 3.0, seed)
    f = f + 1.3 * fbm((n, n), S, 12.0, 40.0, 3.0, seed + 1)
    c = (R + 2) * S
    v = cv2.remap(f.astype(np.float32), (x * S + c).astype(np.float32), (y * S + c).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return v


def paper(dens, ang, tips, seed=21):
    rng = np.random.default_rng(seed + 1)
    F = flat_fields(dens, seed)
    pan = 2 * np.pi * R / NRIB
    n_d, n_c = max(int(pan * 30 * dens), 20), 10
    # columns: dense in what the frame sees, sparse behind. Vertices fall on every rib
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

    # the rim: a slack cut from tip to tip, slightly hollow; fibrous at the smallest scale, with a few small nicks
    tip = (1 - t) * tips[i % NRIB] + t * tips[(i + 1) % NRIB] - 0.55  # the rib tips stand out past the paper
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

    # fold down the middle of each panel, not ruled: it wanders by a millimetre or so, and its depth differs panel to panel
    wob = np.stack([smooth1d(NRIB * 8, 3.0, rng)], 0)[0]
    Ru = Rr / R
    tc = 0.5 + np.interp(((I + Ru) * 8) % (NRIB * 8), np.arange(NRIB * 8), wob) * 0.006 + rng.normal(0, 0.012, NRIB)[I % NRIB]
    pw = np.maximum(pan * Ru, 0.3)  # panel width here, cm
    d_c = np.abs(T - tc) * pw  # distance from the fold, cm
    deep = rng.uniform(0.2, 0.5, NRIB)[I % NRIB]
    fold = np.exp(-d_c / (0.16 * pw + 0.2))
    d_rib = np.minimum(T, 1 - T) * pw

    z = prof(Rr) - 0.62 * deep * fold * Ru
    z = z + 0.05 * sample(F, "patches", x, y) * (0.3 + 0.7 * Ru) + 0.008 * sample(F, "clouds", x, y)
    z = z - 0.05 * sstep(0.7, 0.1, d_rib)  # drawn down against each rib

    # --- the sheet's thickness in layers, then its colour
    clouds = sample(F, "clouds", x, y)
    fine = sample(F, "fine", x, y)
    fib = sample(F, "fib", x, y)
    patch = sample(F, "patches", x, y)
    # oil runs from the crown to the rim: long streaks along the rib, per panel; in polar fields so they stay radial
    az = (np.arctan2(y, x) % (2 * np.pi)) * R  # cm of arc at the rim
    pxa, pxr = 3.2, 1.0
    oil_tex = fbm((int(R * pxr * 2), int(2 * np.pi * R * pxa)), pxa, 0.5, 9.0, 2.0, seed + 8).astype(np.float32)
    oil = cv2.remap(oil_tex, (az * pxa).astype(np.float32), (Rr * pxr).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
    oil = cv2.GaussianBlur(oil, (0, 0), 1.5)

    # strip over each rib, with a torn edge
    tear = sample(F, "clouds", x * 1.7 + 11, y * 1.7 - 7)
    strip_w = rng.uniform(0.3, 0.55, NRIB + 1)
    wleft, wright = strip_w[I % NRIB], strip_w[(I + 1) % NRIB]
    strip = sstep(0.09, -0.09, np.where(T < 0.5, T * pw - wleft, (1 - T) * pw - wright) + 0.03 * tear)
    # sheet joins: every few ribs two sheets overlap beside a rib, a wider band
    seam_ribs = np.cumsum(rng.integers(2, 6, NRIB)) % NRIB
    seam = np.zeros_like(Rr)
    for sr in np.unique(seam_ribs):
        wd = rng.uniform(0.9, 1.5)
        on = I % NRIB == sr
        seam = np.maximum(seam, on * sstep(0.1, -0.1, T * pw - wd * (0.75 + 0.25 * Ru) + 0.03 * tear))
    hem_w = 0.9 + 0.1 * sample(F, "patches", x * 2.1, y * 2.1) + 0.02 * tear
    hem = sstep(0.12, -0.12, edge[None, :] - Rr - hem_w)
    cap_r = 6.0 + 0.35 * sample(F, "patches", x * 3, y * 3) + 0.14 * tear
    cap = sstep(0.1, -0.1, Rr - cap_r)
    # wear at the fold: fibre broken along it, intermittent
    wear = np.exp(-((d_c / 0.05) ** 2)) * sstep(-0.3, 1.2, sample(F, "patches", x * 4.5, y * 4.5)) * sstep(0.25, 0.7, Ru)
    # dried water
    wm = water_marks(x, y, seed + 40)
    stain = sstep(1.0, 1.25, wm)
    tide = np.exp(-(((wm - 1.0) / 0.045) ** 2)) * sstep(0.2, 0.5, Ru)

    layers = 1.0 + 0.1 * strip + 0.13 * seam + 0.28 * hem + 0.8 * cap
    p = layers * (1.0 + 0.045 * clouds + 0.02 * fine + 0.22 * (fib - fib.mean()) - 0.07 * oil + 0.05 * patch)
    p = p - 0.13 * wear - 0.03 * stain + 0.14 * tide + 0.07 * sstep(R - 8.0, R, Rr)
    p = np.maximum(p, 0.25)
    Tc = np.exp(-p[..., None] * SIGMA)
    dim = np.exp(-0.34 * (p[..., None] - 1.0))  # the paper itself stops light: each layer also dims all colours; oil lets more by
    tr = np.clip(Tc * dim * color([1.0, 0.98, 0.94]), 0, 1)
    col = np.clip(np.power(Tc, 1.15) * color([0.62, 0.6, 0.55]), 0, 1)
    P = world(x, y, z)
    return P.astype(np.float32), col.astype(np.float32), tr.astype(np.float32), edge


def ribs(ang, tips, seed=21):
    """Each rib a split strip of bamboo, flat, wider near the middle, under the paper: skin side down."""
    rng = np.random.default_rng(seed + 20)
    ns, nside = 700, 14
    s = np.linspace(0, 1, ns, dtype=np.float32)
    out = []
    for i in range(NRIB):
        r = RIB0 + (tips[i] - RIB0) * s
        wob = 0.03 * smooth1d(ns, 80, rng) * sstep(0.0, 0.3, s)
        w = rng.uniform(0.21, 0.28) * np.clip(r / 14.0, 0.34, 1.0) * (1.05 - 0.45 * s**3) * (1 + 0.04 * smooth1d(ns, 60, rng))
        ht = rng.uniform(0.09, 0.13) * (1.15 - 0.75 * s) * (1 + 0.15 * sstep(RIB_J - 1.5, RIB_J, r) * sstep(RIB_J + 1.5, RIB_J, r))
        ca, sa = np.cos(ang[i]), np.sin(ang[i])
        x, y = r * ca - wob * sa, r * sa + wob * ca
        z = prof(r) - ht - 0.02
        path = world(x, y, z)
        side = world(np.full(ns, -sa), np.full(ns, ca), np.zeros(ns))
        base = color([0.4, 0.17, 0.06]) * rng.uniform(0.7, 1.15)
        tone = 1 + 0.14 * smooth1d(ns, 30, rng) + 0.05 * smooth1d(ns, 4, rng)
        node = np.zeros(ns, np.float32)
        k = R0 + rng.uniform(4, 14)
        while k < R:
            node += np.exp(-(((r - k) / 0.14) ** 2))
            k += rng.uniform(15, 22)
        cc = base[None] * (tone * (1 - 0.5 * node))[:, None]
        out.append(tubes(path[None], w[None], {"col": cc[None], "tr": cc[None] * color([1.5, 1.0, 0.6])}, nside=nside, side=side[None], ht=ht[None], power=3.2))
    # fine lengthwise lines of the bamboo cannot be in `tubes` by point; give each row of the section its own tone
    m = merge(*out)
    tone = 1 + 0.16 * rng.normal(0, 1, (len(m["V"]) // nside // ns * nside)).reshape(-1, nside)[:, None, :]
    tone = np.repeat(tone, ns, axis=1).reshape(-1, 1)
    m["col"] = m["col"] * np.clip(tone, 0.6, 1.4)
    return m


def stretchers(ang, zr, seed=21):
    """The stretchers: strips from the runner up to each rib."""
    rng = np.random.default_rng(seed + 25)
    ns, nside = 60, 10
    out = []
    for i in range(NRIB):
        ca, sa = np.cos(ang[i]), np.sin(ang[i])
        rt = RIB_J + rng.normal(0, 0.12)
        s = np.linspace(0, 1, ns, dtype=np.float32)
        r = 2.0 + (rt - 2.0) * s
        z = zr + (prof(rt) - 0.5 - zr) * s - 0.25 * np.sin(np.pi * s) * rng.uniform(-0.3, 1)
        w = rng.uniform(0.14, 0.19) * (0.5 + 0.6 * s) * np.ones(ns, np.float32)
        ht = rng.uniform(0.07, 0.1) * np.ones(ns, np.float32)
        path = world(r * ca, r * sa, z)
        side = world(np.full(ns, -sa), np.full(ns, ca), np.zeros(ns))
        cc = color([0.5, 0.25, 0.09]) * rng.uniform(0.7, 1.1) * (1 + 0.1 * smooth1d(ns, 8, rng))[:, None]
        out.append(tubes(path[None], w[None], {"col": cc[None], "tr": cc[None] * color([1.5, 1.0, 0.6])}, nside=nside, side=side[None], ht=ht[None], power=3.0))
    return merge(*out)


def _thread_set(pts, rad, cl):
    """Many threads (n, ns, 3) as one soup."""
    return tubes(pts, rad, {"col": cl, "tr": np.zeros_like(cl)}, nside=5)


def lacing(ang, seed=21):
    """The silk lacing: threads carried from rib to rib, back and forth, in bands. Each thread has its own slack and where it lands on the rib; the ring of wraps round each rib holds them."""
    rng = np.random.default_rng(seed + 30)
    bands = [(RIB_J + 1.8, 0.7, [0.05, 0.11, 0.26], 9), (RIB_J + 3.4, 0.8, [0.66, 0.60, 0.46], 11), (RIB_J + 5.0, 0.6, [0.30, 0.055, 0.04], 9), (RIB_J + 6.1, 0.35, [0.05, 0.14, 0.10], 6)]
    ns = 14
    lines, cols, rads = [], [], []
    for rc, hb, cl, nthr in bands:
        cl = np.array(cl, np.float32)
        for i in range(NRIB):
            a0, a1 = ang[i], ang[(i + 1) % NRIB]
            a1 = a1 + 2 * np.pi if a1 < a0 else a1
            for k in range(nthr):
                sg = 1 if k % 2 == 0 else -1
                base = rc + (k / max(nthr - 1, 1) - 0.5) * 0.22 + rng.normal(0, 0.035)
                r0 = base + sg * hb + rng.normal(0, 0.05)
                r1 = base - sg * hb + rng.normal(0, 0.05)
                t = np.linspace(0, 1, ns, dtype=np.float32)
                r = r0 * (1 - t) + r1 * t
                x = r * ((1 - t) * np.cos(a0) + t * np.cos(a1))
                y = r * ((1 - t) * np.sin(a0) + t * np.sin(a1))
                z = prof(r) - 0.32 - rng.uniform(0, 0.1) - rng.uniform(0.04, 0.2) * 4 * t * (1 - t)
                lines.append(world(x, y, z))
                cols.append(np.broadcast_to(cl * rng.uniform(0.75, 1.2), (ns, 3)))
                rads.append(0.034 * rng.uniform(0.85, 1.2))
    return _thread_set(np.array(lines, np.float32), np.array(rads, np.float32), np.array(cols, np.float32))


def wraps(ang, tips, seed=21):
    """Windings that hold things to the ribs: a sleeve at the tip of each rib, and a tie where each stretcher meets its rib; a rim thread from tip to tip under the hem."""
    rng = np.random.default_rng(seed + 33)
    lines, cols, rads = [], [], []
    ns = 22
    for i in range(NRIB):
        ca, sa = np.cos(ang[i]), np.sin(ang[i])
        for (r0, r1, cl, nw) in ((tips[i] - rng.uniform(1.5, 2.2), tips[i] - 0.45, [0.2, 0.025, 0.02], 26), (RIB_J - 0.55, RIB_J + 0.55, [0.55, 0.5, 0.38], 14)):
            cl = np.array(cl, np.float32)
            for k in range(nw):
                rr = r0 + (r1 - r0) * (k + rng.uniform(-0.25, 0.25)) / nw
                t = np.linspace(0, 2 * np.pi, ns, dtype=np.float32)
                hw = 0.26 * np.clip(rr / 14.0, 0.34, 1.0) * (1.05 - 0.45 * ((rr - RIB0) / (R - RIB0)) ** 3) + 0.03
                ht = 0.11 * (1.15 - 0.75 * rr / R) + 0.02
                off = hw * np.cos(t)
                dz = ht * np.sin(t)
                rs = rr + 0.015 * t
                x, y = rs * ca - off * sa, rs * sa + off * ca
                z = prof(rs) - ht - 0.02 + dz
                lines.append(world(x, y, z))
                cols.append(np.broadcast_to(cl * rng.uniform(0.8, 1.2), (ns, 3)))
                rads.append(0.03 * rng.uniform(0.9, 1.15))
        # rim thread to the next tip, slack under the hem
        a0, a1 = ang[i], ang[(i + 1) % NRIB]
        a1 = a1 + 2 * np.pi if a1 < a0 else a1
        t = np.linspace(0, 1, ns, dtype=np.float32)
        r = (1 - t) * (tips[i] - 0.5) + t * (tips[(i + 1) % NRIB] - 0.5)
        x = r * ((1 - t) * np.cos(a0) + t * np.cos(a1))
        y = r * ((1 - t) * np.sin(a0) + t * np.sin(a1))
        z = prof(r) - 0.07 - 0.1 * 4 * t * (1 - t)
        lines.append(world(x, y, z))
        cols.append(np.broadcast_to(np.array([0.03, 0.025, 0.025], np.float32), (ns, 3)))
        rads.append(0.04)
    return _thread_set(np.array(lines, np.float32), np.array(rads, np.float32), np.array(cols, np.float32))


def revolve(path, rz, col, n=40):
    """A turned part: (r, z) profile about the axis, as a grid."""
    th = np.linspace(0, 2 * np.pi, n, dtype=np.float32)
    r, z = rz[:, 0], rz[:, 1]
    Th, Rr = np.meshgrid(th, r)
    Z = np.repeat(z[:, None], n, 1)
    P = world(Rr * np.cos(Th), Rr * np.sin(Th), Z)
    c = np.broadcast_to(np.array(col, np.float32), P.shape).copy()
    c = c * (1 + 0.1 * fbm(P.shape[:2], 1.0, 2.0, 12.0, 2.0, 5))[..., None]
    np.savez(path, P=P.astype(np.float32), col=np.clip(c, 0, 1).astype(np.float32), tr=np.zeros_like(c, dtype=np.float32))
    return path


def spray(rng, at, up, n_leaf):
    """A bamboo twig with its leaves: the leaves fan out in hands from a thin branch, and hang."""
    axis = up / np.linalg.norm(up)
    L0 = 60 + 50 * rng.random()
    side = np.cross(axis, rng.normal(0, 1, 3))
    side /= np.linalg.norm(side)
    base = at[None] + rng.uniform(-0.5, 0.5, (n_leaf, 1)) * L0 * axis[None] + rng.normal(0, 0.12 * L0, (n_leaf, 1)) * side[None]
    fan = rng.normal(0, 1, (n_leaf, 3))
    fan = fan - axis[None] * np.sum(fan * axis[None], -1, keepdims=True)
    fan = fan / np.linalg.norm(fan, axis=-1, keepdims=True)
    A = fan + np.array([0, 0, -0.55]) + 0.5 * axis[None]
    N = np.cross(A, rng.normal(0, 1, (n_leaf, 3)))
    L, Wd = rng.uniform(9, 17, n_leaf), rng.uniform(1.1, 2.0, n_leaf)
    tone = rng.uniform(0.7, 1.25, (n_leaf, 1))
    col = np.array([[0.05, 0.13, 0.035]]) * tone
    tr = np.array([[0.2, 0.42, 0.06]]) * tone
    return leaves(rng, base, A, N, L, Wd, col, tr, ns=5)


def grove(d, dens, tgt, view):
    """The grove: stems and foliage from a few metres out, where the lens opens them into soft greens and holes of sky. Also the sprays between the sun and the umbrella, that cast the shadows on the paper."""
    rng = np.random.default_rng(2121)
    # stems
    n_st = 46
    paths, rads, cols = [], [], []
    for i in range(n_st):
        y = float(np.exp(rng.uniform(np.log(380), np.log(1500))))
        x = float(rng.uniform(-0.75, 0.75) * y * 1.3)
        t = np.linspace(0, 1, 24, dtype=np.float32)
        lean = rng.normal(0, 0.05, 2) * 1400
        px = x + lean[0] * t**1.5
        py = y + lean[1] * t**1.5
        pz = -200 + 1700 * t
        paths.append(np.stack([px, py, pz], -1))
        rads.append(rng.uniform(2.2, 4.5))
        cols.append(np.array([0.12, 0.19, 0.06], np.float32) * rng.uniform(0.6, 1.3))
    cols_a = np.array(cols, np.float32)
    st = tubes(np.array(paths, np.float32), np.array(rads, np.float32), {"col": cols_a, "tr": 0.2 * cols_a}, nside=10)
    # foliage: clumps
    n_cl = int(300 + 300 * dens)
    n_lf = 34
    fol = []
    for i in range(n_cl):
        y = float(np.exp(rng.uniform(np.log(420), np.log(1700))))
        x = float(rng.uniform(-0.8, 0.8) * (y + 80) * 1.0)
        el = np.radians(rng.uniform(8, 60))
        z = y * np.tan(el)
        c = np.array([x, y, z])
        r = rng.uniform(26, 70)
        at = c + rng.normal(0, r, (n_lf, 3)) * np.array([1, 1, 0.55])
        A = rng.normal(0, 1, (n_lf, 3)) + np.array([0, 0, -0.5])
        N = rng.normal(0, 1, (n_lf, 3))
        tone = rng.uniform(0.75, 1.25, (n_lf, 1)) * rng.uniform(0.75, 1.2)
        fol.append(leaves(rng, at, A, N, rng.uniform(14, 26, n_lf), rng.uniform(2.2, 3.6, n_lf), np.array([[0.05, 0.11, 0.035]]) * tone, np.array([[0.11, 0.21, 0.035]]) * tone, ns=4))
    p0 = save(os.path.join(d, "stems.npz"), st)
    p1 = save(os.path.join(d, "foliage.npz"), merge(*fol))
    # sprays that shade the paper: on the line from points of the paper to the sun
    sp = []
    e1, e2, e3 = basis()
    aims = [(-14.0, 30.0, 58.0, (0.8, 0.1, 0.5), 150), (22.0, 26.0, 80.0, (-0.8, 0.2, -0.3), 170), (-32.0, 8.0, 100.0, (0.6, 0.6, 0.3), 130), (10.0, 4.0, 130.0, (0.2, -0.8, 0.4), 170)]
    for xl, yl, dd, up_, nl in aims:
        pt = xl * e1 + yl * e2 + 7 * e3
        sp.append(spray(rng, pt + SUN * dd, np.array(up_, float), nl))
    p2 = save(os.path.join(d, "sprays.npz"), merge(*sp))
    MAT = {"k": 0.55, "fw": 0.0, "rough": 0.42, "spec": 0.4, "smooth": True}
    return [{"name": "stems", "npz": p0, "shader_py": SOFT, "params": {"k": 0.02, "rough": 0.4, "spec": 0.45}}, {"name": "foliage", "npz": p1, "shader_py": SOFT, "params": MAT}, {"name": "sprays", "npz": p2, "shader_py": SOFT, "params": MAT}]


def main():
    real_background()
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"sketch": 0.3, "preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    ang = rib_angles(21)
    tips = R + np.random.default_rng(23).normal(0, 0.1, NRIB)
    P, col, tr, edge = paper(dens, ang, tips)
    p_paper = os.path.join(d, f"paper.{q}.npz")
    np.savez(p_paper, P=P, col=col, tr=tr)
    zr = -9.5  # the runner, under the crown
    p_ribs = save(os.path.join(d, "ribs.npz"), ribs(ang, tips))
    p_str = save(os.path.join(d, "stretch.npz"), stretchers(ang, zr))
    p_lace = save(os.path.join(d, "lace.npz"), lacing(ang))
    p_wrap = save(os.path.join(d, "wraps.npz"), wraps(ang, tips))
    p_run = revolve(os.path.join(d, "runner.npz"), np.array([[0.0, zr - 5.0], [0.85, zr - 5.0], [1.2, zr - 4.6], [1.5, zr - 3.0], [2.0, zr - 1.2], [2.2, zr - 0.6], [2.2, zr + 1.2], [2.3, zr + 1.6], [1.0, zr + 2.2]]), [0.022, 0.012, 0.01])
    p_crn = revolve(os.path.join(d, "crown.npz"), np.array([[0.0, H - 3.5], [1.9, H - 3.2], [2.4, H - 1.9], [2.4, H - 0.9], [1.3, H - 0.8]]), [0.18, 0.08, 0.035])
    p_sha = revolve(os.path.join(d, "shaft.npz"), np.array([[0.85, -90.0], [0.85, H - 1.0]]), [0.3, 0.2, 0.08], n=24)

    rim = P[-1]
    view = view_dir(-90.0, EL)
    H_f = W * 9 / 16
    e1, e2, e3 = basis()
    tgt = e2 * 6.0 + e3 * 2.0
    for _ in range(5):
        cam = frame_camera(tgt, view, W, DIST)
        _, y, _ = project(cam, rim.reshape(-1, 3))
        tgt = tgt + np.array([0, 0, 1.0]) * (-(float(y.min()) - APEX) * H_f)
    focus = world(np.array(0.0), np.array(R - 3.0), np.array(prof(R - 3.0)))
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, rim.reshape(-1, 3))
    print(f"apex y {y.min():.3f}, x span {x.min():.2f}..{x.max():.2f}", flush=True)
    xh, yh, wh = project(cam, np.array([world(np.array(0.0), np.array(0.0), np.array(zr))]))
    print(f"runner at {xh[0]:.2f},{yh[0]:.2f} depth {wh[0]:.1f}; cam {cam['loc']}; lens {cam['lens_mm']:.1f}", flush=True)

    PAPER = {"k": 0.58, "fw": 0.3, "fw_rough": 0.38, "fw_ior": 1.22, "rough": 0.42, "spec": 0.16}
    WOOD = {"k": 0.4, "rough": 0.36, "spec": 0.42, "smooth": True}
    meshes = [
        {"name": "paper", "npz": p_paper, "shader_py": SOFT, "params": PAPER},
        {"name": "ribs", "npz": p_ribs, "shader_py": SOFT, "params": WOOD},
        {"name": "stretch", "npz": p_str, "shader_py": SOFT, "params": WOOD},
        {"name": "lace", "npz": p_lace, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.38, "spec": 0.5, "sheen": 0.5}},
        {"name": "wraps", "npz": p_wrap, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.4, "spec": 0.5, "sheen": 0.4}},
        {"name": "runner", "npz": p_run, "shader_py": SOFT, "params": WOOD},
        {"name": "crown", "npz": p_crn, "shader_py": SOFT, "params": WOOD},
        {"name": "shaft", "npz": p_sha, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.3, "spec": 0.5}},
    ]
    meshes += grove(d, dens, tgt, view)
    lights = [{"name": "sun", "loc": (tgt + SUN * 900.0).tolist(), "target": tgt.tolist(), "size": [11, 11], "watts": 10800000, "rgb": [1.0, 0.95, 0.86], "hide_in_gloss": True}]
    env = pond_env(os.path.join(d, "env.npy"), SUN, top=(0.5, 0.66, 0.92), low=(0.75, 0.82, 0.8), tree=(0.05, 0.1, 0.04), tree_el=26.0, pond=(0.05, 0.075, 0.035), cloud=0.5, gain=0.8, seed=21, soft=6.0)
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": env, "diffuse": True, "transmission": True},
        "bounces": 16,
        "diffuse_bounces": 10,
        "glossy_bounces": 4,
        "transmission_bounces": 12,
        "spp": {"sketch": 64, "preview": 128, "mid": 192, "final": 448},
    }
    if q == "sketch":
        scene["spp"] = 64
    look = {"exposure": -0.5, "contrast": 1.14, "saturation": 1.06, "black": 0.001, "grain": 0.9, "sharpen": 0.18, "halation": 0.05, "glare": 0.004, "vignette": 0.3}
    shoot(NAME, scene, "preview" if q == "sketch" else q, tag=q, develop=look)


main()
