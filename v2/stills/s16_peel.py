"""The peel of a lychee, shot 16 only. Built from what ref/lychee shows at 100% (leidus_lychee_fruits_and_seed, lychee_04), not from a pattern:

- the plates are not cracked tiles but packed domes, jammed against each other like growing cells: unequal in size, disordered, with defects. A dome's soft top comes from a soft maximum of neighbouring domes, so the valleys are soft by themselves;
- every dome leans: its apex sits off centre towards the blossom end, a point rises there and curls over, and behind it there is often a small crescent-shaped dimple that goes dark;
- ridges run down from the apex; on the skin between them short ochre dashes radiate: cork splits, thicker in the middle, more of them near the top. At the apex they merge into a dry yellow-brown crust, which differs from dome to dome and is missing on some;
- the skin itself is a fine matte granular surface, rose, deeper in the valleys; here and there a thin white scar runs along a valley.
Sizes (dome .15-.45 cm, point up to .12 cm) are estimates from reference photographs of about known fruit size, not measurements. The dash counts and colours are chosen by eye against the same photographs.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.spatial import cKDTree

_N = 128
_C = gaussian_filter(np.random.default_rng(1616).normal(size=(_N, _N, _N)).astype(np.float32), 2.0, mode="wrap")
_C = _C / _C.std()


def n3(p, s, off=0.0):
    """Smooth noise at points p, s cm across. Two lookups at unrelated scales, so that a fine field shows no tile on the fruit."""
    k = 4.0 / s
    a = map_coordinates(_C, [np.mod(p[..., i].ravel() * k + off * (i + 1), _N) for i in range(3)], order=1, mode="grid-wrap")
    q = np.stack([0.8 * p[..., 0] + 0.6 * p[..., 2], p[..., 1], -0.6 * p[..., 0] + 0.8 * p[..., 2]], -1) * (k / 1.47)
    b = map_coordinates(_C, [np.mod(q[..., i].ravel() + 31.0 + off, _N) for i in range(3)], order=1, mode="grid-wrap")
    return (0.72 * (a + b)).reshape(p.shape[:-1]).astype(np.float32)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def pack(R, seed, n=470, r0=0.172):
    """Jam domes on the sphere. Radii lognormal, smaller around the stalk and at the blossom end; pushed apart until they stop. Disorder and defects stay in it. Returns unit sites, radii in cm. Pole is +z here."""
    rng = np.random.default_rng(seed)
    s = rng.normal(size=(n, 3))
    s /= np.linalg.norm(s, axis=1, keepdims=True)
    r = r0 * np.exp(rng.normal(0, 0.22, n))
    r = r * (0.75 + 0.25 * np.exp(-(((s[:, 2]) / 0.55) ** 2)) + 0.12 * rng.normal(0, 1, n) * 0.5)
    r = np.clip(r, 0.085, 0.27)
    for _ in range(60):
        pairs = cKDTree(s).query_pairs(2.2 * r.max() / R, output_type="ndarray")
        d = s[pairs[:, 0]] - s[pairs[:, 1]]
        dist = np.linalg.norm(d, axis=1) + 1e-6
        want = 0.92 * (r[pairs[:, 0]] + r[pairs[:, 1]]) / R
        over = np.maximum(want - dist, 0.0)
        f = (d / dist[:, None]) * (over * 0.5)[:, None]
        np.add.at(s, pairs[:, 0], f)
        np.add.at(s, pairs[:, 1], -f)
        s /= np.linalg.norm(s, axis=1, keepdims=True)
    return s, r


def peel(N0, R, seed, pole):
    """N0: unit directions (ny, nx, 3), world. The sites are built around +z and turned onto `pole`.
    Returns h (height, cm), tang (tangential shift of the points, cm vector), col, rough."""
    rng = np.random.default_rng(seed)
    pole = np.array(pole, float) / np.linalg.norm(pole)
    s, ra = pack(R, seed + 1)
    # sites onto the pole
    z = np.array([0, 0, 1.0])
    v = np.cross(z, pole)
    c = z.dot(pole)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    Rm = np.eye(3) + K + K @ K / (1 + c)
    s = s @ Rm.T
    nB = len(s)
    # each dome leans towards the blossom end, loosely
    t = -pole[None] + (s @ pole)[:, None] * s
    t = t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
    b = np.cross(s, t)
    a = rng.normal(0, 0.75, nB)
    t, b = t * np.cos(a)[:, None] + b * np.sin(a)[:, None], -t * np.sin(a)[:, None] + b * np.cos(a)[:, None]
    off = rng.uniform(0.08, 0.32, nB) * ra  # apex off centre
    apex = s + t * (off / R)[:, None]
    tree = cKDTree(apex)
    sh = N0.shape[:-1]
    flat = N0.reshape(-1, 3).astype(np.float64)
    k = 7
    dist, idx = tree.query(flat, k=k, workers=-1)
    rho = dist * R
    dome_h = 0.32 * ra * np.exp(rng.normal(0, 0.18, nB))
    x = rho / (1.2 * ra[idx])
    h_k = dome_h[idx] * np.maximum(1.0 - x**2.1, 0.0)  # a low cone with its top rounded by the point, not a ball: balls read as raspberry
    # a soft maximum makes soft valleys. Softer for larger domes would be better; one value is enough
    sharp = 1.0 / 0.011
    hm = np.max(h_k, axis=1, keepdims=True)
    H = hm[:, 0] + np.log(np.sum(np.exp(sharp * (h_k - hm)), axis=1)) / sharp
    # who owns the point: nearest by distance over size, so that big domes have rounded edges
    q = rho / ra[idx]
    o = np.argsort(q, axis=1)[:, :2]
    row = np.arange(len(q))
    own = idx[row, o[:, 0]]
    gap = (q[row, o[:, 1]] - q[row, o[:, 0]]) * ra[own]  # about the distance to the valley line, cm
    # local coordinates on the owning dome
    rel = (flat - s[own]) * R
    u = np.sum(rel * t[own], axis=1).astype(np.float32)
    w = np.sum(rel * b[own], axis=1).astype(np.float32)
    rr = ra[own].astype(np.float32)
    up_ = u - off[own].astype(np.float32)  # from the apex
    wo = np.hypot(up_, w) + 1e-5
    th = np.arctan2(w, up_)
    # the point: long along the lean, narrow across
    tip_h = np.where(rng.random(nB) < 0.4, rng.uniform(0.0, 0.01, nB), rng.lognormal(np.log(0.026), 0.62, nB))
    tip_w = rng.uniform(0.16, 0.34, nB) * ra
    tw = tip_w[own].astype(np.float32)
    tip = (tip_h[own].astype(np.float32)) * np.exp(-((np.hypot(up_ * 0.7, w * 1.15) / tw) ** 1.15))
    # the crescent behind it, which reads dark
    cres_d = np.maximum(rng.normal(0.016, 0.016, nB), 0.0)
    cr = np.exp(-(((up_ + 0.42 * rr) / (0.16 * rr)) ** 2 + (w / (0.5 * rr)) ** 2))
    crescent = cres_d[own].astype(np.float32) * cr
    # ridges down from the apex, three to six, each with its own direction, width and length
    nr = 6
    ang = rng.uniform(-np.pi, np.pi, (nB, nr))
    str_ = rng.random((nB, nr))
    count = rng.integers(3, 7, nB)
    str_[np.arange(nr)[None] >= count[:, None]] = 0.0
    ridge = np.zeros(len(th), np.float32)
    wd = 0.014 + 0.022 * rng.random((nB, nr))
    for j in range(nr):
        dth = np.mod(th - ang[own, j].astype(np.float32) + np.pi, 2 * np.pi) - np.pi
        lat = wo * np.sin(dth)
        fwd = np.cos(dth) > 0
        fade = np.exp(-(((wo / rr) / (0.5 + 0.6 * str_[own, j].astype(np.float32))) ** 2))
        ridge = np.maximum(ridge, fwd * str_[own, j].astype(np.float32) * np.exp(-((lat / wd[own, j].astype(np.float32)) ** 2)) * fade)
    P_ = (flat * R).astype(np.float32)  # for the noises
    # the micro surface: fine granular skin, plus a coarser pimpling, smaller in the valleys
    gr1 = n3(P_, 0.012, 1.0)
    gr2 = n3(P_, 0.035, 2.0)
    hump = sstep(0.0, 0.05, gap)
    height = H + tip + 0.009 * ridge - crescent + 0.0016 * gr1 * (0.5 + 0.5 * hump) + 0.0028 * gr2 * hump
    # --- the dashes: cork splits radiating over the dome. Each dome has a table of them by angle
    nb = 72
    dash = np.zeros(len(th), np.float32)
    for lay in range(2):
        pres = rng.random((nB, nb)) < (0.27 if lay == 0 else 0.17)
        r0 = rng.uniform(0.12, 1.1, (nB, nb)) * ra[:, None]
        ll = rng.lognormal(np.log(0.062), 0.55, (nB, nb))
        wd_ = rng.lognormal(np.log(0.015), 0.45, (nB, nb))
        st = rng.beta(2.0, 1.2, (nB, nb))
        ph = rng.uniform(0, 2 * np.pi, nB)
        bend = n3(P_, 0.16, 5.0 + lay) * 0.42  # they are not ruled
        a2 = np.mod(th + bend + ph[own].astype(np.float32), 2 * np.pi) / (2 * np.pi) * nb
        bi = np.floor(a2).astype(np.int32) % nb
        lat = (a2 - np.floor(a2) - 0.5) * (2 * np.pi / nb) * wo
        along = (wo - r0[own, bi].astype(np.float32)) / ll[own, bi].astype(np.float32)
        prof = np.clip(np.sin(np.pi * np.clip(along, 0, 1)), 0, 1) ** 0.7
        d = pres[own, bi] * st[own, bi].astype(np.float32) * prof * np.exp(-((lat / (wd_[own, bi].astype(np.float32) * (0.45 + 0.75 * prof))) ** 2))
        dash = np.maximum(dash, d)
    # some of the domes are much drier than others, in patches across the fruit
    dry_f = n3(P_, 1.6, 8.0)
    dryness = np.clip(0.62 + 0.3 * dry_f + rng.normal(0, 0.22, nB)[own].astype(np.float32), 0.12, 1.2)
    dash = dash * dryness
    # the dry crust at the top of a dome, broken by the skin's grain
    crust_r = rng.lognormal(np.log(0.26), 0.5, nB) * ra * np.clip(rng.normal(0.75, 0.5, nB), 0, 1.3)
    # it splays out in tongues along the splits, so its outline is by angle
    tongue = rng.lognormal(0.0, 0.55, (nB, nb))
    dt = np.hypot(up_, w) / np.maximum(crust_r[own].astype(np.float32) * tongue[own, bi].astype(np.float32), 1e-3)
    crust = sstep(0.0, 0.4, (1.0 - dt) + 0.35 * gr2 + 0.25 * gr1) * sstep(0.1, 0.5, dryness)
    # white scars: thin, along some valleys only, broken
    sc_mask = sstep(1.35, 2.2, n3(P_, 0.55, 12.0))
    scar = np.exp(-((gap / 0.0055) ** 2)) * sc_mask * sstep(0.1, 0.9, n3(P_, 0.08, 16.0)) + sstep(2.15, 2.7, n3(P_, 0.018, 14.0)) * 0.7 * sc_mask
    # colour. Rose skin, deeper in the valleys, a shade paler up the dome
    rose, deep, pale = np.array([0.80, 0.135, 0.115], np.float32), np.array([0.44, 0.045, 0.045], np.float32), np.array([0.90, 0.22, 0.17], np.float32)
    k_val = sstep(0.0, 0.085, gap)
    col = deep + (rose - deep) * k_val[:, None]
    col = col + (pale - col) * (0.5 * sstep(0.35, 1.0, H / np.maximum(dome_h[own].astype(np.float32), 1e-3)))[:, None]
    # plate to plate, a small difference; across the fruit, a long one. A grain of light and dark in the skin
    tone = np.exp(rng.normal(0, 0.075, nB))[own].astype(np.float32)
    col = col * (tone * np.exp(0.13 * gr1 + 0.05 * gr2))[:, None]
    col = col + (np.array([0.92, 0.56, 0.48], np.float32) - col) * (0.55 * sstep(1.5, 2.3, gr1))[:, None]  # the stipple: pale grains in the skin
    col = col * (1.0 - 0.35 * np.clip(crescent / 0.03, 0, 1))[:, None]
    ochre = np.array([0.80, 0.36, 0.055], np.float32) * np.exp(0.3 * n3(P_, 0.05, 15.0))[:, None]
    dark_c = np.array([0.17, 0.055, 0.018], np.float32)
    col = col + (ochre - col) * np.clip(dash * 1.15, 0, 1)[:, None]
    crust_col = ochre + (dark_c - ochre) * np.clip(0.14 + 0.34 * gr2 + 0.2 * gr1, 0, 1)[:, None]
    col = col + (crust_col - col) * (0.92 * crust)[:, None]
    # the very top of the point has dried out
    col = col + (dark_c - col) * (0.55 * sstep(0.55, 0.98, tip / np.maximum(tip_h[own].astype(np.float32), 0.02)))[:, None]
    col = col + (np.array([0.93, 0.72, 0.60], np.float32) - col) * np.clip(0.5 * scar, 0, 0.7)[:, None]
    # a matte skin. Dry crust is rougher, a rubbed crest a little smoother
    rough = 0.44 + 0.04 * gr2 + 0.28 * crust + 0.22 * np.clip(dash, 0, 1) - 0.08 * sstep(0.5, 1.0, H / np.maximum(dome_h[own].astype(np.float32), 1e-3))
    tang = (t[own] * (0.55 * tip.astype(np.float64) * np.clip(tip / np.maximum(tip_h[own], 0.015), 0, 1))[:, None]).astype(np.float32)  # the point curls over towards the blossom end
    return (height.reshape(sh).astype(np.float32), tang.reshape(sh + (3,)), np.clip(col, 0, 1).reshape(sh + (3,)).astype(np.float32), np.clip(rough, 0.2, 0.95).reshape(sh).astype(np.float32))
