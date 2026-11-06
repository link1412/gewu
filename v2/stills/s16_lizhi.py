"""Shot 16: a small bunch of lychees on the tree, close enough to read the peel. The top of the near fruit is the arc.

    python3 -I v2/stills/s16_lizhi.py [sketch|preview|mid|cand|final]    cand is final size, written beside the final

The old shot was one patch of peel with plates as regular as dragon scales, on black; then Voronoi plates, whose blind review said: scales too regular, spikes the same shape, skin one frequency of noise, drops like transparent balls stuck on. Now, set against ref/lychee at 100% (s16_peel.py):
- the peel is jammed low domes of unequal size with soft valleys from a soft maximum, disorder and defects; a small point curls over on most, off centre; ochre cork flakes on the flanks, a dry crust at the apex, differing from dome to dome; fine pale-grained rose skin; broken white scars;
- water lies pooled: each pool is a liquid level over the peel and exists only where it is above it, so it sits in the valleys and the domes break its outline; one drop hangs at the lowest point. The sun is visible in gloss, since a drop without the sun in it is a glass ball;
- real stalks, real leaves (lit from behind). The background is the tree itself in true lens blur under a sky, lit by the same sun.
Sizes are estimates from general knowledge (fruit about 3.6 cm, leaflets 8-12 cm), not measured; counts and colours of the peel are chosen by eye. The sky is a painted environment (lotuslib.pond_env); the far foliage is simple narrow leaves, only as much as the blur needs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from kit import OUT, color, fbm, frame_camera, mix, shoot, sstep
from lotuslib import pond_env
from s16_peel import peel
from s21_lib import smooth1d, up
from translib import SOFT, leaves, merge, real_background, save, tubes
from vessel import project, view_dir

NAME = "s16_lizhi"
W, EL, DIST = 11.0, 3.0, 30.0
APEX = 0.30
APERTURE = 10.0
SUN = np.array([-0.62, -0.12, 0.72])
SUN = SUN / np.linalg.norm(SUN)
# fruit: centre, radius, stalk direction, seed, density
FRUIT = [
    ((0.0, 0.0, 0.0), 1.82, (0.12, 0.1, 1.0), 1601, 1.0),
    ((4.7, 3.4, 0.9), 1.72, (-0.28, 0.1, 1.0), 1602, 0.38),
    ((-5.2, 3.8, -0.2), 1.76, (0.34, -0.1, 1.0), 1603, 0.34),
    ((1.9, 3.6, -3.5), 1.75, (-0.1, 0.1, 1.0), 1605, 0.3),
]


def slow(N, seed, n=7, f=2.3):
    """A long, smooth field on the sphere with no poles."""
    rng = np.random.default_rng(seed)
    v = rng.normal(0, 1, (n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    ph = rng.uniform(0, 6.3, n)
    amp = rng.uniform(0.5, 1, n)
    out = sum(a * np.sin(f * (N @ d.astype(np.float32)) + p) for d, p, a in zip(v, ph, amp))
    return (out / np.sqrt(np.sum(amp**2) / 2)).astype(np.float32)


def fruit(c, R, pole, seed, dens, q):
    """One fruit. Grid in stalk coordinates; dense towards the camera, sparse at the back. The peel is s16_peel."""
    pole = np.array(pole, float)
    pole /= np.linalg.norm(pole)
    e1 = np.cross(pole, [0, 1.0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(pole, e1)  # towards -y or +y
    if e2[1] > 0:
        e1, e2 = -e1, -e2  # phi = 90 degrees faces the camera
    pxcm = 330.0 * dens
    ny = max(int(np.pi * R * pxcm), 120)
    nf = max(int(1.15 * np.pi * R * pxcm * 1.2), 120)
    nb = max(nf // 8, 40)
    th = np.linspace(0.002, np.pi - 0.002, ny, dtype=np.float32)
    ph = np.concatenate([np.linspace(np.radians(-30), np.radians(210), nf, endpoint=False), np.linspace(np.radians(210), np.radians(330), nb + 1)]).astype(np.float32)
    Ph, Th = np.meshgrid(ph, th)
    N0 = np.sin(Th)[..., None] * (np.cos(Ph)[..., None] * e1.astype(np.float32) + np.sin(Ph)[..., None] * e2.astype(np.float32)) + np.cos(Th)[..., None] * pole.astype(np.float32)
    h, tang, col, rough = peel(N0, R, seed, pole)

    # the shape of the whole fruit: not a ball. An egg a little fuller at the shoulders, a dimple at the stalk, the blunt tip, a shallow suture down one side
    s = slow(N0, seed + 5, 6, 1.6)
    seam = np.exp(-((np.sin(0.5 * (Ph - np.radians(52))) / 0.05) ** 2))
    shape = 1 + 0.028 * s - 0.13 * np.exp(-((Th / 0.26) ** 2)) + 0.07 * np.exp(-(((np.pi - Th) / 0.42) ** 2)) + 0.05 * np.sin(Th) ** 2 * np.cos(Th) + 0.05 * np.cos(Th) - 0.02 * seam
    r = R * shape + h * (1 - 0.8 * np.exp(-((Th / 0.2) ** 2)))
    P = np.array(c, np.float32) + r[..., None] * N0 + tang

    # a long wash over the fruit: the sun has reddened some of it and a shoulder has stayed paler and yellower
    lo = slow(N0, seed + 6, 7, 2.0)
    lo2 = slow(N0, seed + 7, 7, 4.2)
    yellow = np.clip(0.16 + 0.3 * lo + 0.08 * lo2 + 0.4 * np.exp(-((Th / 0.5) ** 2)), 0, 1)
    wash = 1 - yellow[..., None] * (1 - color([1.0, 1.55, 1.25]))
    col = col * np.exp(0.07 * lo2)[..., None] * wash
    return P.astype(np.float32), np.clip(col, 0, 1).astype(np.float32), rough.astype(np.float32), N0, r


def leaf(path, at, axis, normal, L, Wd, seed, dens=1.0, dark=1.0):
    """A leaflet: a pointed oval, a raised pale midrib, side veins that run out towards the margin, a wavy edge, gloss on top. Lit from behind it shows its veins."""
    rng = np.random.default_rng(seed)
    ny, nx = max(int(L * 42 * dens), 60), max(int(Wd * 42 * dens), 28)
    s = np.linspace(0, 1, ny, dtype=np.float32)
    u = np.linspace(-1, 1, nx, dtype=np.float32)
    U, S = np.meshgrid(u, s)
    hw = 0.5 * Wd * np.maximum(np.sin(np.pi * s**0.78), 0.0) ** 0.85 * (1 + 0.04 * smooth1d(ny, ny * 0.07, rng))
    X = U * hw[:, None]
    A = np.array(axis, float)
    A /= np.linalg.norm(A)
    N = np.array(normal, float)
    N = N - A * N.dot(A)
    N /= np.linalg.norm(N)
    T = np.cross(A, N)
    # veins: curved lines leaving the midrib every so often
    nv = 11
    v0 = np.sort(rng.uniform(0.04, 0.92, nv))
    dist = np.full(U.shape, 9.0, np.float32)
    for sign in (-1, 1):
        for v in v0:
            sv = v + 0.20 * np.abs(U) ** 0.75 + 0.006 * sign
            dist = np.where(U * sign > 0, np.minimum(dist, np.abs(S - sv) * L), dist)
    vein = np.exp(-((dist / 0.035) ** 2)) * (1 - 0.6 * np.abs(U))
    mid = np.exp(-((X / (0.035 + 0.05 * (1 - S))) ** 2))
    pil = np.clip(dist / 0.35, 0, 1) ** 0.6
    wave = 0.18 * np.sin(S * L * 0.9 + rng.uniform(0, 6)) * np.abs(U) ** 2 * Wd / 2.5
    fold = 0.28 * np.abs(X) ** 1.2
    droop = -0.05 * L * S**2 - 0.03 * L * S**4
    H_ = fold + wave + 0.018 * pil + droop - 0.03 * mid + 0.04 * up(fbm((64, 64), 5.0, 0.8, 5.0, 2.4, seed + 1), ny, nx)
    P = np.array(at, np.float32) + (S * L)[..., None] * A.astype(np.float32) + X[..., None] * T.astype(np.float32) + H_[..., None] * N.astype(np.float32)
    tone = rng.uniform(0.8, 1.15) * dark
    wash = up(fbm((64, 64), 5.0, 1.5, 8.0, 2.4, seed + 2), ny, nx)
    col = color([0.028, 0.075, 0.022]) * tone * (1 + 0.12 * wash)[..., None]
    col = mix(col, color([0.3, 0.32, 0.1]), np.clip(mid * 0.9 + vein * 0.2, 0, 1))
    tr = color([0.14, 0.27, 0.035]) * tone * (1 + 0.15 * wash)[..., None]
    tr = mix(tr, color([0.42, 0.45, 0.1]), np.clip(mid + 0.55 * vein, 0, 1))
    np.savez(path, P=P.astype(np.float32), col=np.clip(col, 0, 1).astype(np.float32), tr=np.clip(tr, 0, 1).astype(np.float32))
    return path


def stalks(fr):
    """The twig and the stalks: woody, tan, knobbled; the stalk swells into a small collar at the fruit. Every stalk runs up to the one twig."""
    rng = np.random.default_rng(161)
    ns = 90
    paths, rad, cols = [], [], []
    trunk = np.array([[1.5, 2.6, 20.0], [1.2, 2.5, 14.0], [1.0, 2.3, 10.0], [0.95, 2.3, 8.0], [0.9, 2.2, 6.3]])
    for fi, (c, R, pole, seed, _) in enumerate(FRUIT):
        p = np.array(pole, float)
        p /= np.linalg.norm(p)
        top = np.array(c) + p * R * 0.9
        join = np.array([0.9, 2.2, 6.5]) + rng.normal(0, 0.3, 3)
        ctrl = np.stack([top - p * 0.1, top + p * 0.55, top + p * 1.2 + (join - top) * 0.15, (top + join) * 0.5 + rng.normal(0, 0.1, 3), join])
        t = np.linspace(0, 1, ns)
        x = np.stack([np.interp(t, np.linspace(0, 1, 5), ctrl[:, k]) for k in range(3)], -1)
        for _ in range(3):
            x[1:-1] = 0.25 * x[:-2] + 0.5 * x[1:-1] + 0.25 * x[2:]
        x = x + np.stack([0.006 * smooth1d(ns, 6, rng) for _ in range(3)], -1)
        r = 0.05 + 0.05 * np.exp(-t / 0.05) + 0.03 * t + 0.006 * smooth1d(ns, 3, rng) + sum(rng.uniform(0.012, 0.03) * np.exp(-(((t - c0) / 0.012) ** 2)) for c0 in rng.uniform(0.1, 0.95, 5))
        paths.append(x)
        rad.append(r)
        cc = color([0.2, 0.095, 0.045])[None] * (1 + 0.16 * smooth1d(ns, 2.5, rng))[:, None]
        cols.append(cc)
    a = tubes(np.array(paths, np.float32), np.array(rad, np.float32), {"col": np.array(cols, np.float32), "tr": np.zeros_like(np.array(cols, np.float32))}, nside=14)
    t = np.linspace(0, 1, ns)
    x = np.stack([np.interp(t, np.linspace(0, 1, 5), trunk[:, k]) for k in range(3)], -1)
    r = 0.16 + 0.1 * (1 - t) + 0.01 * smooth1d(ns, 3, rng)
    cc = color([0.25, 0.14, 0.07])[None] * (1 + 0.2 * smooth1d(ns, 2.5, rng))[:, None]
    b = tubes(x[None].astype(np.float32), r[None].astype(np.float32), {"col": cc[None].astype(np.float32), "tr": np.zeros((1, ns, 3), np.float32)}, nside=14)
    return merge(a, b)


def drop_caps(P, N0, r, c, n, seed, zone, Rf):
    """Rain on the peel. Water does not sit on it as beads on glass: the skin is rough and has valleys, so a drop lies down among the domes, filling the valleys and leaving the highest points standing through it.
    Its contact line therefore follows the plates by itself. So: a cap of liquid level over the fruit's surface, and the mesh kept only where that level is above the peel."""
    rng = np.random.default_rng(seed)
    ny, nx = P.shape[:2]
    Vs, Fs = [], []
    base = 0
    cc = np.array(c, np.float32)
    # dome-top level: the slow shape, without the plates
    for k in range(n):
        for _ in range(80):
            i, j = int(rng.uniform(0.3, 0.92) * ny), int(rng.uniform(zone[0], zone[1]) * nx)
            if N0[i, j, 1] < -0.25:
                break
        a = float(np.clip(rng.lognormal(np.log(0.115), 0.55), 0.05, 0.34))
        n0 = N0[i, j].astype(np.float64)
        dth, dph = np.pi / ny, np.radians(240) / (nx * 0.889)
        hi = int(1.6 * a / Rf / dth)
        hj = int(1.6 * a / Rf / max(dph, 1e-4) / max(np.sqrt(1 - n0.dot(N0[0, 0]) ** 2), 0.25))
        i0, i1, j0, j1 = max(i - hi, 0), min(i + hi, ny - 1), max(j - hj, 0), min(j + hj, nx - 1)
        N_ = N0[i0:i1, j0:j1]
        rr = r[i0:i1, j0:j1]
        # local coordinates round the centre. It runs a little downhill and is not round
        e1 = np.cross(n0, [0.0, 0.0, 1.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n0, e1)
        u = (N_ @ e1.astype(np.float32)) * Rf
        v = (N_ @ e2.astype(np.float32)) * Rf
        v = v * (1.0 / rng.uniform(1.05, 1.5))
        ang = np.arctan2(v, u)
        wob = 1 + 0.1 * np.sin(2 * ang + rng.uniform(0, 6)) + 0.06 * np.sin(3 * ang + rng.uniform(0, 6))
        d = np.hypot(u, v) / (a * wob)
        fall = np.maximum(1 - d * d, 0.0)
        ref = float(np.percentile(rr[d < 1.0], 62)) if np.any(d < 1.0) else float(r[i, j])
        lift = a * rng.uniform(0.3, 0.46)
        rw = ref + lift * fall ** 0.62 - 0.4 * a * (1 - fall) * (d >= 1.0) - 0.002
        rw = np.where(d < 1.0, rw, 0.0)
        wet = rw > rr
        if wet.sum() < 12:
            continue
        V = cc + (rw[..., None] * N_)
        h_, w_ = wet.shape
        idx = np.arange(h_ * w_).reshape(h_, w_)
        q = wet[:-1, :-1] & wet[1:, :-1] & wet[1:, 1:] & wet[:-1, 1:]
        ia, ib, ic, id_ = idx[:-1, :-1][q], idx[1:, :-1][q], idx[1:, 1:][q], idx[:-1, 1:][q]
        f = np.concatenate([np.stack([ia, ib, ic], -1), np.stack([ia, ic, id_], -1)])
        used, inv = np.unique(f, return_inverse=True)
        Vs.append(V.reshape(-1, 3)[used])
        Fs.append(inv.reshape(f.shape) + base)
        base += len(used)
    return np.concatenate(Vs).astype(np.float32), np.concatenate(Fs).astype(np.int32)


def hanging_drops(points, seed):
    """Drops hanging from the fruit and the stalks: a closed pear shape."""
    rng = np.random.default_rng(seed)
    Vs, Fs = [], []
    base = 0
    res = 44
    for p, rd in points:
        th = np.linspace(0, np.pi, res // 2, dtype=np.float32)
        ph = np.linspace(0, 2 * np.pi, res, dtype=np.float32)
        Ph, Th = np.meshgrid(ph, th)
        rr = rd * (1 + 0.22 * np.cos(Th) * (np.cos(Th) > 0) * -0.0 + 0.0)
        z = -rd * np.cos(Th) * (1 + 0.28 * (np.cos(Th) < 0) * np.abs(np.cos(Th)) ** 2)
        xy = rr * np.sin(Th) * (1 - 0.2 * (np.cos(Th) < 0) * np.abs(np.cos(Th)) ** 3)
        V = np.array(p) + np.stack([xy * np.cos(Ph), xy * np.sin(Ph), z], -1)
        idx = np.arange(res * (res // 2)).reshape(res // 2, res) + base
        f = np.concatenate([np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:]], -1).reshape(-1, 3), np.stack([idx[:-1, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 3)])
        Vs.append(V.reshape(-1, 3))
        Fs.append(f)
        base += res * (res // 2)
    return np.concatenate(Vs).astype(np.float32), np.concatenate(Fs).astype(np.int32)


def tree(d, dens):
    """The tree behind: leaves from 40 cm out to the far crown, opened by the lens into soft greens and holes of sky."""
    rng = np.random.default_rng(1616)
    fol = []
    for i in range(int(150 + 150 * dens)):
        y = float(np.exp(rng.uniform(np.log(38), np.log(900))))
        half = 0.55 * W * (DIST + y) / DIST * 1.4
        x = float(rng.uniform(-half, half))
        z = float(rng.uniform(-half * 0.8, half * 0.8))
        rc = 0.06 * y + rng.uniform(4, 14)
        n_lf = 26
        at = np.array([x, y, z]) + rng.normal(0, rc, (n_lf, 3))
        A = rng.normal(0, 1, (n_lf, 3)) + np.array([0, 0, -0.3])
        N = rng.normal(0, 1, (n_lf, 3)) + np.array([0, -0.2, 0.7])
        tone = rng.uniform(0.7, 1.25, (n_lf, 1)) * rng.uniform(0.7, 1.2)
        fol.append(leaves(rng, at, A, N, rng.uniform(8, 12, n_lf) * 1.4, rng.uniform(2.2, 3, n_lf) * 1.4, np.array([[0.035, 0.08, 0.025]]) * tone, np.array([[0.13, 0.25, 0.035]]) * tone, ns=4, droop=0.12))
    return save(os.path.join(d, "tree.npz"), merge(*fol))


def main():
    real_background()
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    tag = q
    if q == "cand":  # final size, beside the final: the film reads final.*, and this has to pass a side-by-side first
        q = "final"
    dens = {"sketch": 0.28, "preview": 0.45, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    FR = {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.3, "Subsurface Weight": 0.25, "Subsurface Radius": [0.5, 0.12, 0.08], "Subsurface Scale": 0.06, "Coat Weight": 0.12, "Coat Roughness": 0.3}
    meshes = []
    hero = None
    for i, (c, R, pole, seed, de) in enumerate(FRUIT):
        P, col, rough, N0, r = fruit(c, R, pole, seed, de * dens, q)
        p = os.path.join(d, f"fruit{i}.{q}.npz")
        np.savez(p, P=P, col=col, rough=rough)
        meshes.append({"name": f"fruit{i}", "npz": p, "material": FR})
        if i == 0:
            hero = (P, N0, r)
    P0, N0, r0 = hero
    print(f"hero {P0.shape}", flush=True)

    meshes.append({"name": "stalks", "npz": save(os.path.join(d, "stalks.npz"), stalks(FRUIT)), "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.55, "spec": 0.35, "smooth": True}})
    # leaflets of this branch; the ones near the fruit are real sheets. Positions chosen for the frame.
    LEAF = {"k": 0.4, "rough": 0.26, "spec": 0.55}
    leaves_ = [
        ((5.9, 1.1, 9.0), (0.5, 0.06, -1.0), (-0.3, -0.9, 0.2), 10.5, 2.7, 2),
        ((1.4, 2.4, 9.0), (2.4, 0.5, -1.3), (-0.3, -0.5, 0.8), 12.5, 3.2, 3),
        ((0.6, 3.2, 9.5), (-2.4, 0.6, -0.9), (0.2, -0.6, 0.8), 11.5, 3.0, 4),
        ((-2.0, 7.0, 7.5), (-1.2, 1.0, -2.0), (0.6, -0.7, 0.3), 13.0, 3.3, 5),
        ((6.0, 9.0, 6.5), (1.0, 0.2, -2.2), (-0.7, -0.6, 0.3), 13.0, 3.1, 6),
        ((-8.0, 9.0, 4.0), (-0.3, 0.5, -2.2), (0.8, -0.5, 0.2), 12.0, 3.0, 7),
        ((-10.5, -5.0, -3.5), (2.0, 0.1, -0.5), (0.1, -0.8, 0.6), 10.0, 2.8, 8),  # a blurred one in front, low left
    ]
    for i, (at, ax, nm, L, Wd, sd) in enumerate(leaves_):
        p = leaf(os.path.join(d, f"leaf{i}.{q}.npz"), at, ax, nm, L, Wd, 1660 + sd, 1.0 if i in (0, 1, 2) else 0.5)
        meshes.append({"name": f"leaf{i}", "npz": p, "shader_py": SOFT, "params": LEAF})
    meshes.append({"name": "tree", "npz": tree(d, dens), "shader_py": SOFT, "params": {"k": 0.45, "rough": 0.3, "spec": 0.5, "smooth": True}})

    # water: a light rain has just stopped
    dc, df = drop_caps(P0, N0, r0, FRUIT[0][0], 15, 77, (0.15, 0.62), FRUIT[0][1])
    # one drop gathers on the lowest point it can reach
    low = P0.reshape(-1, 3)
    low = low[np.argmin(low[:, 2] + 3.0 * np.maximum(low[:, 1] + 0.6, 0))]
    hv, hf = hanging_drops([((low[0], low[1], low[2] - 0.085), 0.115)], 78)
    p = os.path.join(d, "water.npz")
    np.savez(p, V=np.concatenate([dc, hv]), F=np.concatenate([df, hf + len(dc)]), one=np.ones(len(dc) + len(hv), np.float32))
    meshes.append({"name": "water", "npz": p, "shader_py": SOFT.replace("softsheet_shader", "water_shader"), "params": {}})

    view = view_dir(-90.0, EL)
    H_f = W * 9 / 16
    tops = P0[:40].reshape(-1, 3)
    tgt = np.array([0.5, 0.0, 0.8])
    tops = P0[20:int(P0.shape[0] * 0.35)].reshape(-1, 3)
    for _ in range(5):
        cam = frame_camera(tgt, view, W, DIST)
        _, y, _ = project(cam, tops)
        tgt[2] -= (float(y.min()) - APEX) * H_f
    # focus on the plates near the silhouette at the upper left of the front
    fi, fj = int(P0.shape[0] * 0.30), int(P0.shape[1] * 0.41)
    focus = P0[fi, fj]
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, tops)
    print(f"apex y {y.min():.3f} at x {x[np.argmin(y)]:.2f}; focus at {project(cam, focus[None])[:2]}", flush=True)
    lights = [{"name": "sun", "loc": (tgt + SUN * 700.0).tolist(), "target": tgt.tolist(), "size": [8, 8], "watts": 3600000, "rgb": [1.0, 0.95, 0.86]}]  # visible in gloss: a drop without the sun in it is a glass ball
    env = pond_env(os.path.join(d, "env.npy"), SUN, top=(0.5, 0.68, 0.95), low=(0.8, 0.86, 0.85), tree=(0.05, 0.1, 0.04), tree_el=16.0, pond=(0.06, 0.09, 0.045), cloud=0.6, gain=1.0, seed=16, soft=4.0)
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": env, "diffuse": True, "transmission": True},
        "bounces": 16,
        "diffuse_bounces": 6,
        "glossy_bounces": 8,
        "transmission_bounces": 12,
        "spp": {"sketch": 64, "preview": 128, "mid": 192, "final": 448},
    }
    if q == "sketch":
        scene["spp"] = 64
    look = {"exposure": 0.2, "contrast": 1.2, "saturation": 1.0, "black": 0.001, "grain": 0.9, "sharpen": 0.18, "halation": 0.05, "glare": 0.004, "vignette": 0.3}
    shoot(NAME, scene, "preview" if q == "sketch" else q, tag=tag, develop=look)


main()
