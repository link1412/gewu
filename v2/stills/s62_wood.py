"""Huanghuali as a solid: what a straight log of it shows where a surface cuts it. Used by s62_quanyi only.

Why the wood looks as it does (the causes this models; strengths are chosen by eye against ref/huali_*, which are only references):
- growth history: a tree does not lay down even rings. Groups of years form soft bands of gold and red-brown, each with a slow rise and an abrupt end, with widths spread over a decade. So the colour is a 1-D table of radius,
  not noise, and the figure (cathedrals, diagonal stripes on a rail) is the surface cutting those shells;
- interlocked grain: fibres lean left and right from one group of years to the next and ripple along their length. A polished surface shows this as bands that brighten and darken with the angle of view (chatoyance).
  That is where the "layer upon layer of depth" comes from: the light goes under the wax and comes back off translucent fibres, so it is a highlight stretched across the fibre, and it is coloured by the wood. Hence the attribute `fib`, used by s62_shader;
- 棕眼: vessels cut open, short dark dashes along the fibre, more of them in the early wood, in several lengths;
- 鬼脸: a dormant bud. The shells swell round it and close on themselves, with a dark resinous core and a dark mineral streak running off it.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates

N = 192
_rng0 = np.random.default_rng(6201)
_CUBE = gaussian_filter(_rng0.normal(size=(N, N, N)).astype(np.float32), 2.2, mode="wrap")
_CUBE = _CUBE / _CUBE.std()


def n3(a, b, c):
    """Smooth noise: features about one unit of its coordinates across. Tiles every N / 4.4 = 44 units. A surface that stays near a plane would show the tile in the fine fields, so those go through fine() below."""
    k = 4.4
    return map_coordinates(_CUBE, [np.mod(a.ravel() * k, N), np.mod(b.ravel() * k, N), np.mod(c.ravel() * k, N)], order=1, mode="grid-wrap").reshape(a.shape).astype(np.float32)


def fine(al, x1, x2, sa, sx, off):
    """A fine field with no lattice in it: two lookups at incommensurate scales and rotated across the grain, multiplied into one distribution."""
    u = 0.81 * x1 + 0.59 * x2
    v = -0.59 * x1 + 0.81 * x2
    return (n3(al / sa + off, u / sx, v / sx + off) + n3(al / (1.37 * sa), v / (1.61 * sx) + 2.3 * off, u / (1.61 * sx))) * 0.72


def history(seed, length=40.0, res=0.004):
    """The life of the tree, by radius in cm: band level t (0 gold .. 1 red-brown), the fine annual ring, mineral lines, the lean of the fibres."""
    rng = np.random.default_rng(seed)
    n = int(length / res)
    r = np.arange(n) * res
    # groups of years: widths spread over a decade, levels with memory
    w = np.exp(rng.normal(np.log(0.34), 0.75, 600))
    edges = np.cumsum(np.clip(w, 0.07, 1.8))
    edges = edges[edges < length]
    lv = np.zeros(len(edges) + 1)
    s = 0.5
    for i in range(len(lv)):
        s = 0.55 * s + 0.45 * rng.beta(0.75, 0.75)
        lv[i] = s + 0.35 * (rng.beta(0.6, 0.6) - 0.5)
    lv = np.clip(lv, 0.0, 1.0)
    seg = np.searchsorted(edges, r)
    start = np.r_[0.0, edges][seg]
    end = np.r_[edges, length][seg]
    f = (r - start) / np.maximum(end - start, 1e-3)
    prev = lv[np.maximum(seg - 1, 0)]
    # a slow change through most of the group; it stops short
    t = prev + (lv[seg] - prev) * np.clip(f / 0.8, 0.0, 1.0) ** 1.4
    t = gaussian_filter1d(t, 0.012 / res, mode="nearest")
    # the annual rings: thin, uneven, each ending in a thin dark line, faint
    ww = np.exp(rng.normal(np.log(0.075), 0.5, 2500))
    ed2 = np.cumsum(ww)
    ed2 = ed2[ed2 < length]
    s2 = np.searchsorted(ed2, r)
    st2, en2 = np.r_[0.0, ed2][s2], np.r_[ed2, length][s2]
    f2 = (r - st2) / np.maximum(en2 - st2, 1e-3)
    amp = (rng.uniform(0, 1, len(ed2) + 1) ** 1.6)[s2]
    ring = amp * np.clip((f2 - 0.55) / 0.4, 0, 1) ** 2 * np.clip((1.0 - f2) / 0.05, 0, 1)
    # dark mineral lines: rare and strong, a few of them
    m = np.zeros(n)
    x = 0.0
    while x < length:
        x += rng.exponential(1.15)
        wd, st = rng.uniform(0.008, 0.035), rng.beta(1.2, 2.5)
        i0, i1 = int(x / res), int((x + wd) / res) + 1
        m[i0:i1] = np.maximum(m[i0:i1], st)
    m = gaussian_filter1d(m, 1.2, mode="nearest")
    # the lean of the fibres: left and right from group to group (interlocked grain), in radians
    lean = gaussian_filter1d(rng.normal(size=n), 0.25 / res, mode="wrap")
    lean = 0.17 * lean / lean.std()
    return dict(t=t.astype(np.float32), ring=ring.astype(np.float32), mineral=m.astype(np.float32), lean=lean.astype(np.float32), res=res)


def _tab(h, key, rho):
    return np.interp(rho, np.arange(len(h[key])) * h["res"], h[key]).astype(np.float32)


GOLD, AMBER, RED, DARK = (np.array(c, np.float32) for c in ([0.45, 0.165, 0.052], [0.265, 0.072, 0.026], [0.098, 0.024, 0.013], [0.018, 0.006, 0.004]))


def wood(P, o, a, e1, pith, slope=0.05, knots=(), tone=1.0, seed=1, spread=(0.12, 0.98), line=1.0):
    """o: a point on the log's axis, a: its direction, e1: across it, pith: where the pith lies from the axis (e1, e2), cm. slope: how fast the shells lean along the log, which sets how long a cathedral is.
    knots: (x1, al, amp, r): a bud where the surface passes it. spread: lowers the band contrast (t is pulled to its middle) by this share, then scales it.
    Returns col (albedo), rough, fib (the direction of the fibres, world), dent (height, cm: pores and the slow unevenness)."""
    rng = np.random.default_rng(seed)
    off = float(rng.uniform(0, 40))
    a = np.array(a, float)
    a /= np.linalg.norm(a)
    e1 = np.array(e1, float)
    e1 = e1 - e1.dot(a) * a
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(a, e1)
    sh = P.shape[:2]
    d = P.reshape(-1, 3).astype(np.float64) - np.array(o, float)
    al, x1, x2 = (d @ a).reshape(sh).astype(np.float32), (d @ e1).reshape(sh).astype(np.float32), (d @ e2).reshape(sh).astype(np.float32)
    # the shells wander, in three scales with a clear order: slow and long, then shorter, then the ripple
    w1 = 1.25 * n3(al / 30.0 + off, x1 / 8.0, x2 / 8.0) + 0.34 * n3(al / 9.0, x1 / 2.6 + off, x2 / 2.6) + 0.07 * n3(al / 2.4 + off, x1 / 0.8, x2 / 0.8 + off)
    w2 = 1.25 * n3(al / 30.0, x1 / 8.0 + off, x2 / 8.0) + 0.34 * n3(al / 9.0, x1 / 2.6, x2 / 2.6 + off) + 0.07 * n3(al / 2.4, x1 / 0.8 + off, x2 / 0.8)
    X1, X2 = x1 + pith[0] + w1, x2 + pith[1] + w2
    rho = np.hypot(X1, X2) + slope * al + 6.0
    core = np.zeros(sh, np.float32)
    halo = np.zeros(sh, np.float32)
    # the fibres part round a bud as a stream parts round a stone: the fine fields are read in coordinates pushed aside by it, and they wander with the shells
    xs1, xs2 = x1 + 0.8 * w1, x2 + 0.8 * w2
    for ku, kv, amp, r in knots:
        dx, dv = x1 - ku + 0.3 * r * n3(al / r, x1 / r + off, x2 / r), (al - kv + 0.3 * r * n3(al / r + off, x1 / r, x2 / r)) * 0.72
        dk = np.hypot(dx, dv)
        g = np.exp(-((dk / r) ** 2))
        rho = rho + amp * g
        xs1 = xs1 - 0.75 * r * g * dx / np.maximum(dk, 0.08 * r)
        core = np.maximum(core, np.exp(-((dk / (0.2 * r)) ** 2.4)))
        halo = np.maximum(halo, np.exp(-((dk / (0.62 * r)) ** 2)))
    rho = np.maximum(rho, 0.01)
    # ripple along the fibre, which comes and goes: 水波纹
    rip_amp = np.clip(0.5 + 0.8 * n3(al / 18.0, x1 / 3.0 + off, x2 / 3.0), 0, 1) ** 2
    rho_w = rho + 0.05 * rip_amp * np.sin(2 * np.pi * (al / 2.3 + 0.9 * n3(al / 8.0 + off, x1 / 2.0, x2 / 2.0)))
    h = history(seed + 17)
    t = _tab(h, "t", rho_w)
    ring = _tab(h, "ring", rho_w)
    mineral = _tab(h, "mineral", rho_w)
    # a mineral line does not run forever: it fades in and out along the log
    mineral = mineral * np.clip(0.55 + 0.9 * n3(al / 7.0 + off, x1 / 1.5, x2 / 1.5 + off), 0, 1)
    cloud = n3(al / 15.0, x1 / 4.5 + off, x2 / 4.5)  # large clouds of colour across the shells
    silk = fine(al, xs1, xs2, 3.2, 0.11, off)  # bundles of fibres in long lines, then the single fibres
    fibre = fine(al, xs1, xs2, 1.3, 0.024, off + 11.0)
    t = t * spread[1] + spread[0] + 0.13 * cloud + 0.09 * silk + 0.2 * halo
    t = np.clip(t, 0.0, 1.0)
    # gold -> amber -> red-brown
    k1 = np.clip(t / 0.5, 0, 1)[..., None]
    k2 = np.clip((t - 0.5) / 0.5, 0, 1)[..., None]
    col = GOLD + (AMBER - GOLD) * k1
    col = col + (RED - col) * k2
    # the pores: more in the pale wood, in clusters, three kinds of length
    density = np.clip(0.62 - 0.45 * (t - 0.5) + 0.45 * n3(al / 5.0 + off, x1 / 1.2, x2 / 1.2 + off), 0.1, 1.2)
    p1 = fine(al, xs1, xs2, 0.15, 0.0115, off + 3.0)  # short dashes
    p2 = fine(al, xs1, xs2, 0.36, 0.0125, off + 7.0)  # long ones, rarer
    strength = np.clip(0.62 + 0.42 * n3(al / 0.9, xs1 / 0.28 + off, xs2 / 0.28), 0.2, 1.0)  # not every vessel is as full of dark gum
    pore = np.maximum(np.clip((p1 - (1.52 - 0.75 * density)) / 0.5, 0, 1), np.clip((p2 - (1.9 - 0.8 * density)) / 0.5, 0, 1)) * strength
    # the fibres are lines of light and dark in the wood, not a noise on top of it: multiply, so that gold stays gold
    col = col * np.exp(0.17 * fibre + 0.1 * silk)[..., None]
    broken = np.clip(0.6 + 0.55 * fibre, 0, 1)  # a ring line is made of fibres, it is not drawn
    dk = np.clip(line * (0.3 * ring * broken + 0.8 * mineral * broken) + 0.92 * pore + 0.92 * core + 0.28 * halo, 0, 0.97)[..., None]
    col = col + (DARK - col) * dk
    col = col * tone
    rough = 0.42 + 0.03 * cloud + 0.3 * pore + 0.12 * core
    # the fibres: the log's axis leaning on the shells, by group of years, and rippling
    lean = _tab(h, "lean", rho) + 0.05 * rip_amp * np.cos(2 * np.pi * (al / 2.3 + 0.9 * n3(al / 8.0 + off, x1 / 2.0, x2 / 2.0)))
    tilt = 0.5 * _tab(h, "lean", rho + 3.1)  # and in and out of the surface
    rr = np.maximum(np.hypot(X1, X2), 1e-3)
    er = (X1 / rr)[..., None] * e1.astype(np.float32) + (X2 / rr)[..., None] * e2.astype(np.float32)  # radial
    et = np.cross(a.astype(np.float32), er)  # tangential
    fib = a.astype(np.float32)[None, None] + lean[..., None] * et + tilt[..., None] * er
    fib /= np.linalg.norm(fib, axis=-1, keepdims=True)
    dent = -0.007 * pore - 0.012 * core + 0.016 * n3(al / 4.0 + off, x1 / 1.5, x2 / 1.5) + 0.002 * silk
    return np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.12, 0.85).astype(np.float32), fib.astype(np.float32), dent.astype(np.float32)
