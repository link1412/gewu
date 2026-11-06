"""Shot 24: a white paper-cut (团花) lying on indigo home-woven cloth; its round edge is the arc, its shadow falls on the cloth.

    python3 -I v2/stills/s24_jianzhi.py [flat|sketch|preview|mid|final]     (flat: the cutting plan only, no render)
    python3 -I v2/stills/s24_jianzhi.py wind [check|final]                  (a light wind, solved by s24_wind.py; goes to out/v2/s24_jianzhi_wind_move_{preview,final})

Second version. The blind review of the first: "teeth and leaf windows too repetitive and fully symmetric, background
like a noise bump". So the plan is no longer a formula folded into mirrors. How it is made now:
- cut by hand on one sheet, not folded: every window is its own polygon from a small vocabulary (lens leaf, 锯齿 teeth, 月牙 crescent,
  打孔 punch, 毛毛纹 comb of slits), with its own length, width, bend, tooth pitch and depth. Nothing is copied or mirrored;
- scissors work in snips: curves are short straight runs, and the blade sometimes overruns a corner by a hair (small overcuts);
- the field between the three heads (peony, pomegranate, lotus: three different plants) is filled by placing leaves along a slow
  vine flow on an occupancy grid that keeps a bridge of paper between cuts: bridges vary, as a hand's do;
- the old creases are from keeping it folded, not from cutting: a roof-shaped kink plus a slow tent, at irregular angles;
- the paper is lifted in places and tongues near some windows curl off the cloth (per-window amount, most of them nothing);
- the cloth is real threads: each warp and weft has its own width, dye lot and slubs along its length, in plain weave.
Its motion is a thin plate on this very cut shape in a light wind, solved in s24_wind.py, and only the paper moves.
All scales are estimates from general knowledge of paper-cuts and home-woven cloth, not measured. The design is drawn here for this picture,
not copied from a known piece. No textures from photographs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, frame_camera, mix, rank, shoot, sstep

NAME = "s24_jianzhi"
W = 8.0
ELEV = np.radians(42.0)
R = 13.4  # radius of the paper-cut, cm
APEX = 0.2  # y of the top of the rim on the table
YC = APEX - R
X0, X1, Y0, Y1 = -5.8, 5.8, -5.0, 5.4
SEED = 2407


# --- the hand --------------------------------------------------------------------------------------------------------
def snips(pts, rng, step=0.11, jit=0.0035):
    """A smooth curve as the scissors cut it: runs of straight snips with slightly misplaced ends."""
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    L = d[-1]
    if L < step * 1.5:
        return pts
    s = [0.0]
    while s[-1] < L:
        s.append(s[-1] + step * rng.lognormal(0, 0.45))
    s = np.array(s[:-1] + [L])
    out = np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], 1)
    out[1:-1] += rng.normal(0, jit, (len(out) - 2, 2))
    return out


def lens_leaf(rng, c, ang, L, wd, bend=0.0, teeth=None, asym=0.0, belly=0.5):
    """A leaf or petal window: spine with a bend; half width peaks at `belly` along it; teeth (pitch, depth) on the edges, per side."""
    n = max(int(L / 0.012), 24)
    t = np.linspace(0, 1, n)
    ca, sa = np.cos(ang), np.sin(ang)
    q = (t - 0.5) * L
    p = bend * L * (4 * t * (1 - t) - 0.5)
    tang = np.arctan2(bend * L * 4 * (1 - 2 * t), L * np.ones_like(t))
    prof = (np.sin(np.pi * t ** (np.log(0.5) / np.log(belly)))) ** 0.8
    sides = []
    for sg, k in ((1, 1 + asym), (-1, 1 - asym)):
        h = wd * k * prof
        if teeth is not None and teeth[sg > 0] is not None:
            pitch, depth = teeth[sg > 0]
            # walk along the edge tooth by tooth; none are alike
            pos, vals = [0.0], [0.0]
            s = rng.uniform(0, pitch)
            drift = rng.normal(0, 0.15)
            while s < L:
                pw = pitch * rng.lognormal(0, 0.24)
                dp = depth * rng.lognormal(0, 0.3) * (0.55 + 0.45 * prof[min(int(s / L * n), n - 1)])
                pos += [s + pw * (0.5 + drift * 0.35), s + pw]
                vals += [dp, 0.0]
                s += pw
                drift += rng.normal(0, 0.12)
            tooth = np.interp(q + L / 2, pos, vals)
            h = np.maximum(h - tooth, 0.002)
        qq = q - sg * h * np.sin(tang)
        pp = p + sg * h * np.cos(tang)
        sides.append(np.stack([qq, pp], 1))
    poly = np.r_[sides[0], sides[1][::-1]]
    return np.stack([c[0] + ca * poly[:, 0] - sa * poly[:, 1], c[1] + sa * poly[:, 0] + ca * poly[:, 1]], 1)


def crescent(rng, c, ang, r, thick, span=1.25, skew=0.0):
    """月牙: two arcs meeting in two sharp tips, belly towards ang; thick is its widest."""
    n = 26
    a = np.linspace(-span, span, n)
    outer = np.stack([r * np.cos(a), r * np.sin(a)], 1)
    k = np.sin(span)
    rin = np.hypot(r * k, 0)
    # the inner arc through the same tips, flatter; its centre set by thickness
    sag = r - r * np.cos(span) - thick
    sag = max(sag, 0.0015)
    Ri = (k * r * k * r + sag * sag) / (2 * sag)
    xc = r * np.cos(span) + sag - Ri
    ai = np.arcsin(np.clip(k * r / Ri, -1, 1))
    b = np.linspace(ai, -ai, n)
    inner = np.stack([xc + Ri * np.cos(b), Ri * np.sin(b)], 1)
    poly = np.r_[outer, inner]
    poly[:, 1] += skew * poly[:, 0]
    ca, sa = np.cos(ang), np.sin(ang)
    x = c[0] + ca * (poly[:, 0] - r * np.cos(span)) - sa * poly[:, 1]
    y = c[1] + sa * (poly[:, 0] - r * np.cos(span)) + ca * poly[:, 1]
    return np.stack([x, y], 1)


def punch(rng, c, r):
    """Not a punch tool: a few snips around, so it is a lopsided polygon."""
    m = rng.integers(5, 8)
    a = np.sort(rng.uniform(0, 2 * np.pi, m) + np.linspace(0, 2 * np.pi, m, endpoint=False)) % (2 * np.pi)
    a = np.sort(a)
    rr = r * rng.uniform(0.75, 1.15, m)
    sq = rng.uniform(0.7, 1.0)
    th = rng.uniform(0, np.pi)
    x, y = rr * np.cos(a), rr * np.sin(a) * sq
    return np.stack([c[0] + x * np.cos(th) - y * np.sin(th), c[1] + x * np.sin(th) + y * np.cos(th)], 1)


def slit(rng, c, ang, L, wd, curve=0.0):
    """One tooth of a comb: a long thin spike, wide at its base, slightly curved."""
    t = np.linspace(0, 1, 10)
    q = t * L
    p = curve * L * t * t
    h = wd * (1 - t) ** 0.8
    poly = np.r_[np.stack([q, p + h], 1), np.stack([q, p - h], 1)[::-1]]
    ca, sa = np.cos(ang), np.sin(ang)
    return np.stack([c[0] + ca * poly[:, 0] - sa * poly[:, 1], c[1] + sa * poly[:, 0] + ca * poly[:, 1]], 1)


# --- the design -------------------------------------------------------------------------------------------------------
class Plan:
    """Keeps every cut and an occupancy grid, so that a new cut can be refused if it would not leave a bridge of paper."""

    PX = 90.0  # cells per cm of the occupancy grid

    def __init__(self):
        self.cuts = []
        self.nx, self.ny = int((X1 - X0) * self.PX), int((Y1 - Y0) * self.PX)
        self.occ = np.zeros((self.ny, self.nx), np.uint8)

    def _px(self, poly):
        return np.round(np.stack([(poly[:, 0] - X0) * self.PX, (Y1 - poly[:, 1]) * self.PX], 1) * 8).astype(np.int32)

    def add(self, poly, bridge=0.03, force=False):
        p = self._px(poly)
        lo, hi = p.min(0) >> 3, p.max(0) >> 3
        m = int(np.ceil(bridge * self.PX)) + 1
        if lo[0] - m < 0 or lo[1] - m < 0 or hi[0] + m >= self.nx or hi[1] + m >= self.ny:
            return False
        x0, y0, x1, y1 = lo[0] - m, lo[1] - m, hi[0] + m + 1, hi[1] + m + 1
        tmp = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(tmp, [p - np.array([x0 * 8, y0 * 8])], 1, cv2.LINE_8, shift=3)
        if not force:
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * m + 1, 2 * m + 1))
            if (cv2.dilate(tmp, k) & self.occ[y0:y1, x0:x1]).any():
                return False
        self.occ[y0:y1, x0:x1] |= tmp
        self.cuts.append(poly)
        return True


def rim_xy(a, off=0.0):
    rr = R - off
    return np.stack([rr * np.sin(a), YC + rr * np.cos(a)], -1)


def rim_outline(rng):
    """The outer contour: a hand's arc (slow wander) with shallow scallops of different widths, and on some of them small teeth."""
    amax = 0.62
    # scallops
    a, ws = -amax, []
    while a < amax:
        wd = rng.uniform(0.55, 1.05) / R
        ws.append((a, wd))
        a += wd
    n = 5200
    aa = np.linspace(-amax, amax, n)
    wander = 0.035 * np.interp(aa, np.linspace(-amax, amax, 15), rng.normal(0, 1, 15))
    wander = cv2.GaussianBlur(wander.astype(np.float32)[None], (0, 0), 60.0)[0]
    off = wander.astype(np.float64).copy()
    for a0, wd in ws:
        m = (aa >= a0) & (aa < a0 + wd)
        t = (aa[m] - a0) / wd
        depth = rng.uniform(0.05, 0.1)
        sc = 0.09 - depth * np.sin(np.pi * t) ** 0.7  # all scallops meet at the same notch
        if rng.random() < 0.72:  # this scallop gets teeth, each its own
            s = rng.uniform(0, 0.05)
            pos, vals = [], []
            Lm = wd * R
            pitch0 = rng.uniform(0.085, 0.135)
            while s < Lm:
                pw = pitch0 * rng.lognormal(0, 0.28)
                dp = rng.uniform(0.018, 0.06) * rng.lognormal(0, 0.3)
                pos += [s, s + pw * rng.uniform(0.3, 0.7)]
                vals += [0.0, dp]
                s += pw
            sc = sc + np.interp(t * Lm, pos, vals)
        off[m] += sc
    return aa, off


def peony(pl, rng, c, Rf):
    """Outer petals, each a broad toothed window; a second ring of narrow ones between; a heart of crescents and stamens."""
    n = rng.integers(8, 10)
    a0 = rng.uniform(0, 6.28)
    angs = a0 + np.cumsum(rng.normal(2 * np.pi / n, 0.09, n))
    for i, a in enumerate(angs):
        Lp = Rf * rng.uniform(0.44, 0.56)
        rc = Rf * rng.uniform(0.66, 0.73)
        pc = np.array(c) + rc * np.array([np.cos(a), np.sin(a)])
        wd = Lp * rng.uniform(0.26, 0.36)
        tl = (rng.uniform(0.06, 0.1), rng.uniform(0.035, 0.07))
        tr = (rng.uniform(0.06, 0.1), rng.uniform(0.035, 0.07)) if rng.random() < 0.85 else None
        pl.add(lens_leaf(rng, pc, a + rng.normal(0, 0.1), Lp, wd, rng.normal(0, 0.1), (tl, tr), rng.normal(0, 0.1), rng.uniform(0.5, 0.68)), 0.022)
    for a in angs + np.pi / n + rng.normal(0, 0.06, n):
        Lp = Rf * rng.uniform(0.2, 0.3)
        pc = np.array(c) + Rf * rng.uniform(0.4, 0.46) * np.array([np.cos(a), np.sin(a)])
        pl.add(lens_leaf(rng, pc, a, Lp, Lp * rng.uniform(0.14, 0.24), rng.normal(0, 0.14), None, rng.normal(0, 0.1), rng.uniform(0.4, 0.65)), 0.018)
    # the heart: crescents turning round, stamens as punches
    m = rng.integers(5, 8)
    for a in rng.uniform(0, 0.4) + np.cumsum(rng.normal(2 * np.pi / m, 0.16, m)):
        pc = np.array(c) + Rf * rng.uniform(0.19, 0.23) * np.array([np.cos(a), np.sin(a)])
        pl.add(crescent(rng, pc, a + rng.normal(0, 0.3), Rf * rng.uniform(0.08, 0.12), Rf * rng.uniform(0.022, 0.045), rng.uniform(1.0, 1.4), rng.normal(0, 0.12)), 0.012)
    for _ in range(12):
        a, r_ = rng.uniform(0, 6.28), Rf * rng.uniform(0.0, 0.12)
        pl.add(punch(rng, np.array(c) + r_ * np.array([np.cos(a), np.sin(a)]), rng.uniform(0.016, 0.034)), 0.016)
    comb(pl, rng, c, Rf * 1.03, Rf * rng.uniform(0.12, 0.19), rng.uniform(0.07, 0.1))


def comb(pl, rng, c, r0, Ls, pitch, a_lo=0.0, a_hi=2 * np.pi):
    """毛毛纹: spikes round a head, pointing outward. Spacing wanders, some spikes are short or missing, the lean drifts slowly."""
    a = a_lo + rng.uniform(0, 0.1)
    lean = rng.normal(0, 0.12)
    while a < a_hi:
        a += pitch * rng.lognormal(0, 0.2) / r0
        lean += rng.normal(0, 0.05)
        lean = np.clip(lean, -0.35, 0.35)
        if rng.random() < 0.05:
            continue
        L = Ls * rng.lognormal(0, 0.32)
        p = np.array(c) + (r0 + rng.normal(0, 0.008)) * np.array([np.cos(a), np.sin(a)])
        pl.add(slit(rng, p, a + lean, L, pitch * rng.uniform(0.2, 0.34), rng.normal(0, 0.1)), 0.009)


def pomegranate(pl, rng, c, Rf):
    """A fruit: split skin (two big curved windows), seeds as uneven punches and small crescents, a crown of three teeth, leaves round it."""
    c = np.array(c)
    tilt = rng.uniform(-0.5, 0.5)
    for sg in (1, -1):
        pc = c + sg * Rf * 0.68 * np.array([np.cos(tilt), np.sin(tilt)])
        pl.add(lens_leaf(rng, pc, tilt + np.pi / 2 + sg * 0.12, Rf * rng.uniform(1.15, 1.35), Rf * rng.uniform(0.1, 0.15), sg * rng.uniform(0.12, 0.2), ((0.08, 0.04), None) if sg > 0 else (None, (0.075, 0.045)), 0.0), 0.02)
    for _ in range(120):
        a, r_ = rng.uniform(0, 6.28), Rf * 0.46 * np.sqrt(rng.random())
        p = c + r_ * np.array([np.cos(a), np.sin(a)])
        if rng.random() < 0.8:
            pl.add(punch(rng, p, rng.uniform(0.03, 0.058)), rng.uniform(0.014, 0.03))
        else:
            pl.add(crescent(rng, p, rng.uniform(0, 6.28), rng.uniform(0.05, 0.08), rng.uniform(0.016, 0.03), 1.1, rng.normal(0, 0.1)), 0.016)
    comb(pl, rng, c, Rf * 1.0, Rf * rng.uniform(0.14, 0.2), rng.uniform(0.075, 0.11))


def lotus(pl, rng, c, Rf):
    """A lotus seen from the side: pointed petals fanning upward from a base, each with a midrib of paper, unequal."""
    c = np.array(c)
    n = 7
    tilt = rng.uniform(-0.2, 0.2)
    for i, f in enumerate(np.linspace(-1.0, 1.0, n) + rng.normal(0, 0.04, n)):
        a = np.pi / 2 + tilt + f * 1.26
        Lp = Rf * (1.05 - 0.28 * abs(f)) * rng.uniform(0.92, 1.05)
        pc = c + Lp * 0.56 * np.array([np.cos(a), np.sin(a)])
        for sg in (1, -1):  # two halves of a petal with a paper midrib
            pp = pc + sg * Lp * 0.075 * np.array([-np.sin(a), np.cos(a)])
            t = ((rng.uniform(0.07, 0.1), rng.uniform(0.025, 0.05)), None) if sg > 0 else (None, (rng.uniform(0.07, 0.1), rng.uniform(0.025, 0.05)))
            pl.add(lens_leaf(rng, pp, a + sg * rng.uniform(-0.02, 0.05), Lp * rng.uniform(0.74, 0.86), Lp * rng.uniform(0.045, 0.07), sg * rng.uniform(0.0, 0.06), t, 0.0, rng.uniform(0.38, 0.5)), 0.012)
    # the seed pod below the petals
    for _ in range(14):
        p = c + np.array([rng.uniform(-0.3, 0.3) * Rf, rng.uniform(-0.2, 0.03) * Rf])
        pl.add(punch(rng, p, rng.uniform(0.018, 0.034)), 0.02)
    comb(pl, rng, c, Rf * 1.06, Rf * rng.uniform(0.14, 0.2), rng.uniform(0.08, 0.11), np.pi / 2 + tilt - 1.5, np.pi / 2 + tilt + 1.5)


def plan():
    rng = np.random.default_rng(SEED)
    pl = Plan()
    heads = [(-0.42, -2.62, 1.55, "peony"), (2.95, -2.36, 1.08, "pom"), (-3.72, -2.3, 1.12, "lotus")]
    for x, y, r_, kind in heads:
        {"peony": peony, "pom": pomegranate, "lotus": lotus}[kind](pl, rng, (x, y), r_)

    # crescents in a row inside the rim: walked by hand, spacing and size drifting; a few are dropped or pushed
    a = -0.6
    dr = 0.0
    while a < 0.6:
        step = rng.uniform(0.56, 0.72) * rng.lognormal(0, 0.09)
        dr = np.clip(dr + rng.normal(0, 0.012), -0.04, 0.04)
        off = 0.42 + dr
        c = rim_xy(a, off)
        rr = rng.uniform(0.23, 0.31)
        if rng.random() > 0.06:
            pl.add(crescent(rng, c, np.pi / 2 - a + rng.normal(0, 0.09), rr, rr * rng.uniform(0.3, 0.46), rng.uniform(1.05, 1.3), rng.normal(0, 0.08)), 0.02)
        a += step / R
    # a slit line held by bridges, then small punches: both broken by hand and neither is a perfect ring
    a = -0.6
    while a < 0.6:
        Ls = rng.uniform(0.55, 1.1)
        c = rim_xy(a + 0.5 * Ls / R, 0.68 + rng.normal(0, 0.008))
        pl.add(lens_leaf(rng, c, -a - 0.5 * Ls / R + rng.normal(0, 0.012), Ls, rng.uniform(0.012, 0.024), rng.normal(0, 0.012), None, 0.0, rng.uniform(0.4, 0.6)), 0.015)
        a += (Ls + rng.uniform(0.06, 0.11)) / R

    # the field: leaves along a slow vine flow around the heads, big first, small last; refused if they would crowd
    def flow(x, y):
        v = np.zeros(2)
        for hx, hy, hr, _ in heads:
            d = np.array([x - hx, y - hy])
            nn = np.linalg.norm(d) + 1e-6
            v += np.array([-d[1], d[0]]) / nn * np.exp(-(nn - hr) / 0.9)
        return np.arctan2(v[1] + 0.2, v[0] + 1e-3)

    for size, tries, bridge in ((0.62, 900, 0.035), (0.4, 1400, 0.03), (0.24, 2600, 0.024)):
        for _ in range(tries):
            x, y = rng.uniform(-5.6, 5.6), rng.uniform(-5.0, 0.2)
            if np.hypot(x, y - YC) > R - 0.82:
                continue
            L = size * rng.lognormal(0, 0.22)
            ang = flow(x, y) + rng.normal(0, 0.28)
            t = (rng.uniform(0.05, 0.085), rng.uniform(0.016, 0.04)) if L > 0.3 else None
            u = rng.random()
            if u < 0.68 or L > 0.45:
                poly = lens_leaf(rng, (x, y), ang, L, L * rng.uniform(0.13, 0.26), rng.normal(0, 0.14), (t, t if rng.random() < 0.5 else None), rng.normal(0, 0.12), rng.uniform(0.35, 0.65))
            else:
                poly = crescent(rng, (x, y), ang, L * rng.uniform(0.45, 0.7), L * rng.uniform(0.12, 0.22), rng.uniform(1.0, 1.35), rng.normal(0, 0.1))
            pl.add(poly, bridge * rng.lognormal(0, 0.25))
    print("cuts", len(pl.cuts), flush=True)
    return pl.cuts, rim_outline(rng), rng


def rasterise(cuts, rim, rng, shape, pxcm):
    """Cut ids on the final grid. Snips are applied here, overcuts too. The rim makes the outer polygon."""
    ny, nx = shape
    ids = np.zeros(shape, np.uint16)
    over = np.zeros(shape, np.uint8)

    def tp(poly):
        return np.round(np.stack([(poly[:, 0] - X0) * pxcm - 0.5, (Y1 - poly[:, 1]) * pxcm - 0.5], 1) * 16).astype(np.int32)

    for i, poly in enumerate(cuts):
        q = np.r_[poly, poly[:1]]
        q = snips(q, rng, step=0.017, jit=0.0012).astype(np.float64)
        cv2.fillPoly(ids, [tp(q)], int(i + 1), cv2.LINE_8, shift=4)
        # overcuts: where a sharp corner was cut, the blade runs on a little
        if rng.random() < 0.5:
            k = rng.integers(0, len(poly))
            d = poly[k] - poly[k - 1]
            d = d / (np.hypot(*d) + 1e-9)
            e = poly[k] + d * rng.uniform(0.012, 0.05)
            cv2.line(over, tuple(tp(poly[k:k + 1])[0]), tuple(tp(e[None])[0]), 1, 1, cv2.LINE_8, shift=4)
    aa, off = rim
    a = np.stack([(R - off) * np.sin(aa), YC + (R - off) * np.cos(aa)], 1)
    a = np.r_[a, [[a[-1, 0], Y0 - 1], [a[0, 0], Y0 - 1]]]
    sheet = np.zeros(shape, np.uint8)
    cv2.fillPoly(sheet, [tp(a)], 1, cv2.LINE_8, shift=4)
    return ids, over, sheet


# --- paper and cloth --------------------------------------------------------------------------------------------------
def fibres(shape, pxcm, per_cm2, lo, hi, seed):
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 * per_cm2)
    a = rng.uniform(0, np.pi, n)
    length = rng.uniform(lo, hi, n) * pxcm / 5.0
    px, py = rng.uniform(0, nx, n), rng.uniform(0, ny, n)
    pts = [np.stack([px, py], -1)]
    for _ in range(5):
        a = a + rng.normal(0, 0.28, n)
        px, py = px + length * np.cos(a), py + length * np.sin(a)
        pts.append(np.stack([px, py], -1))
    canvas = np.zeros(shape, np.uint8)
    cv2.polylines(canvas, list(np.round(np.stack(pts, 1) * 8).astype(np.int32)), False, 255, 1, cv2.LINE_AA, shift=3)
    return canvas.astype(np.float32) / 255.0


CREASES = ((-0.03, 0.0022, 0.03), (0.42, 0.0016, 0.035), (-0.3, 0.0012, 0.03), (0.2, 0.0008, 0.02))  # angle from the vertical through the sheet's centre (radians, irregular), kink, tent height


def build_paper(dens, cut_data):
    pxcm = 320.0 * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("paper grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    x = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    y = Y1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)

    cuts, rim, rng = cut_data
    ids, over, sheet = rasterise(cuts, rim, rng, shape, pxcm)
    hole = ((ids > 0) | (over > 0) | (sheet == 0)).astype(np.uint8)
    dist = cv2.distanceTransform(1 - hole, cv2.DIST_L2, 5).astype(np.float32) / pxcm  # cm into the paper from the nearest cut
    # each window's tongue lifts its own way, most hardly at all; smooth, because paper has no steps
    rc = np.random.default_rng(SEED + 40)
    amt = np.where(rc.random(len(cuts) + 2) < 0.3, rc.lognormal(np.log(0.009), 0.5, len(cuts) + 2), 0.0).astype(np.float32)
    amt[0] = 0.0
    sg = 0.07 * pxcm
    wt = blur((ids > 0).astype(np.float32), sg)
    curl = blur(amt[ids], sg) / (wt + 0.02) * sstep(0.0, 0.06, wt) * np.exp(-dist / 0.14)

    fib_l = blur(fibres(shape, pxcm, 240, 0.2, 0.7, SEED + 1), max(0.7 * dens, 0.45))
    fib_s = blur(fibres(shape, pxcm, 900, 0.03, 0.12, SEED + 2), max(0.5 * dens, 0.4))
    flocs = fbm(shape, pxcm, 0.03, 0.4, 2.2, SEED + 3)
    fine = fbm(shape, pxcm, 0.004, 0.03, 1.5, SEED + 4)

    # the edge: soft by a pixel; fibres stand out a little where the blade dragged
    soft = blur((1 - hole).astype(np.float32), max(0.9 * dens, 0.55))
    wob = 0.09 * fine + 0.1 * fib_l + 0.07 * fib_s
    alpha = sstep(0.42, 0.58, soft + wob * sstep(0.05, 0.0, dist))
    alpha = alpha * (sheet > 0).astype(np.float32) + (sheet == 0) * alpha * 0.0
    print("paper cover", float(alpha.mean()), flush=True)

    # height: slow lift, creases, curl
    u = np.arctan2(X, Y - YC)
    z = 0.016 + 0.03 * sstep(0.42, 0.97, rank(fbm(shape, pxcm, 1.0, 5.0, 3.0, SEED + 6)))
    z = z + 0.014 * sstep(0.5, 0.0, R - np.hypot(X, Y - YC)) * rank(fbm(shape, pxcm, 0.8, 3.0, 2.6, SEED + 7))
    crease_d = np.zeros(shape, np.float32)
    wbl = fbm(shape, pxcm, 0.4, 3.0, 3.0, SEED + 8)
    for ang, kink, tent in CREASES:
        dd = np.hypot(X, Y - YC) * np.sin(u - ang) + 0.012 * wbl  # signed cm from the crease
        # a crease is a kink in slope: the two sides meet at an angle, decays away; broken where the paper was not pressed
        press = 0.5 + 0.5 * sstep(0.2, 0.6, rank(fbm(shape, pxcm, 0.3, 1.6, 2.4, SEED + int(ang * 100) + 50)))
        z = z + tent * np.exp(-np.abs(dd) / 0.7) * press + kink * np.exp(-np.abs(dd) / 0.018) * press
        crease_d = np.maximum(crease_d, np.exp(-np.abs(dd) / 0.012) * press)
    z = z + curl + 0.0006 * flocs + 0.0011 * fib_l + 0.00045 * fib_s
    P = np.stack([X, Y, z], -1).astype(np.float32)

    tone_ = rank(flocs)
    col = mix(color([0.83, 0.815, 0.77]), color([0.895, 0.88, 0.835]), tone_)
    col = col * (1.0 - 0.1 * fib_s[..., None] - 0.05 * fib_l[..., None])
    # handling: greyer along a crease, a faint warm age at the rim
    col = col * (1.0 - 0.1 * crease_d[..., None])
    age = sstep(1.2, 0.0, R - np.hypot(X, Y - YC)) * rank(fbm(shape, pxcm, 0.3, 2.5, 2.6, SEED + 9))
    col = mix(col, col * color([0.96, 0.92, 0.82]), age)
    return P, np.clip(col, 0, 1).astype(np.float32), alpha.astype(np.float32)


def threads(shape, coord, pitch, seed):
    """Variable-width threads along an axis: returns thread index and position across it, -0.5 .. 0.5."""
    rng = np.random.default_rng(seed)
    n = int((coord.max() - coord.min()) / pitch) + 40
    w = pitch * np.clip(rng.lognormal(0, 0.17, n), 0.65, 1.7)
    edges = coord.min() - 10 * pitch + np.r_[0, np.cumsum(w)]
    i = np.clip(np.searchsorted(edges, coord.ravel()) - 1, 0, n - 1).reshape(shape)
    f = (coord - edges[i]) / w[i] - 0.5
    return i, f.astype(np.float32), w


def build_cloth(dens):
    pxcm = 200.0 * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("cloth grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    x = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    y = Y1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)
    a = np.radians(3.2)
    U, V = X * np.cos(a) + Y * np.sin(a), -X * np.sin(a) + Y * np.cos(a)
    # the weave wanders slowly: threads are not on a ruler
    Uw = U + 0.022 * fbm(shape, pxcm, 0.6, 7.0, 3.0, SEED + 20)
    Vw = V + 0.022 * fbm(shape, pxcm, 0.6, 7.0, 3.0, SEED + 21)
    iu, fu, wu = threads(shape, Uw, 0.034, SEED + 22)
    iv, fv, wv = threads(shape, Vw, 0.04, SEED + 23)
    over = (iu + iv) % 2 == 0  # warp on top where even

    # slubs: each thread thickens and thins along its length; a table of noise, one row per thread, long correlation along
    rs = np.random.default_rng(SEED + 24)
    tbl = fbm((1024, 2048), 1.0, 8.0, 180.0, 2.4, SEED + 25)
    tbl2 = fbm((1024, 2048), 1.0, 8.0, 180.0, 2.4, SEED + 26)
    su = tbl[iu % 1024, (((V + 20.0) * 18.0).astype(np.int32)) % 2048]
    sv = tbl2[iv % 1024, (((U + 20.0) * 18.0).astype(np.int32)) % 2048]
    # a few thick slubs in the weft, as handspun has
    slub_w = sstep(1.6, 2.6, sv)
    thick_u, thick_v = 1.0 + 0.2 * su, 1.0 + 0.2 * sv + 0.5 * slub_w
    # height of a thread on top: oval across it, crowned between the crossing threads
    hu = np.sqrt(np.maximum(1 - (2 * fu / np.clip(thick_u, 0.7, 1.5)) ** 2, 0.0)) * np.cos(np.clip(fv, -0.5, 0.5) * np.pi) ** 0.6
    hv = np.sqrt(np.maximum(1 - (2 * fv / np.clip(thick_v, 0.7, 1.9)) ** 2, 0.0)) * np.cos(np.clip(fu, -0.5, 0.5) * np.pi) ** 0.6
    top = np.where(over, hu * thick_u, hv * thick_v).astype(np.float32)
    # hairs and twist on the yarn: stretched noise along the thread on top; twist lines lean
    hairs = fbm((2048, 2048), 1.0, 1.2, 16.0, 1.8, SEED + 27)
    ku = cv2.remap(hairs, np.mod((U * 40.0 + V * 300.0), 2047).astype(np.float32), np.mod(U * 300.0, 2047).astype(np.float32), cv2.INTER_LINEAR)
    kv = cv2.remap(hairs, np.mod((V * 40.0 + U * 300.0) + 500, 2047).astype(np.float32), np.mod(V * 300.0 + 700, 2047).astype(np.float32), cv2.INTER_LINEAR)
    twist = np.where(over, ku, kv)
    wr = fbm(shape, pxcm, 0.8, 9.0, 3.0, SEED + 28)  # it lies in slow soft waves, barely
    z = -0.018 + 0.0065 * top + 0.0007 * twist + 0.006 * wr
    # a thread's dye lot, the fade on the tops where washing rubbed it
    du, dv = rs.normal(0, 1, 1024).astype(np.float32), rs.normal(0, 1, 1024).astype(np.float32)
    shade = np.where(over, du[iu % 1024] + 0.5 * su, dv[iv % 1024] + 0.5 * sv)
    base = mix(color([0.0042, 0.0082, 0.026]), color([0.0085, 0.0155, 0.042]), rank(shade.astype(np.float32)))
    worn = rank(fbm(shape, pxcm, 0.15, 2.0, 2.2, SEED + 29))
    col = base * (0.62 + 0.5 * np.clip(top, 0, 1)[..., None]) * (1.0 + 0.1 * twist[..., None]) * (0.86 + 0.34 * worn[..., None])
    P = np.stack([X, Y, z], -1).astype(np.float32)
    return P, np.clip(col, 0, 1).astype(np.float32)


def flat(cut_data):
    pxcm = 150.0
    shape = (int((Y1 - Y0) * pxcm), int((X1 - X0) * pxcm))
    ids, over, sheet = rasterise(cut_data[0], cut_data[1], cut_data[2], shape, pxcm)
    im = ((ids == 0) & (over == 0) & (sheet > 0)).astype(np.uint8) * 230 + 25
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    y0 = int((Y1 - APEX - 0.2) * pxcm)
    cv2.imwrite(os.path.join(d, "flat.jpg"), im[y0 : y0 + int(4.4 * pxcm)], [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(os.path.join(d, "flat.jpg"))


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    wind = None
    if q == "wind":  # the same picture; the meshes on disk are reused, so the plate and the render have the same paper
        wind = sys.argv[2] if len(sys.argv) > 2 else "check"
        q = "final" if wind == "final" else "mid"
    cut_data = plan()
    if q == "flat":
        flat(cut_data)
        return
    dens = {"sketch": 0.32, "preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"paper.{q}.npz")
    npz2 = os.path.join(d, f"cloth.{q}.npz")
    if not (wind and os.path.exists(npz) and os.path.exists(npz2)):
        Pp, C, A = build_paper(dens, cut_data)
        np.savez(npz, P=Pp, col=C, alpha=A)  # rows run -y, so the normals are up
        Pc, Cc = build_cloth(dens)
        np.savez(npz2, P=Pc, col=Cc)
    view = np.array([0.0, -np.cos(ELEV), np.sin(ELEV)])
    tgt = np.array([0.0, APEX - 0.03 * W * 9.0 / 16.0 / np.sin(ELEV), 0.0])
    focus = np.array([0.0, APEX - 0.95, 0.05])
    cam = frame_camera(tgt, view, W, 34.0, aperture_mm=5.0, focus_point=focus)
    lights = [
        # a window-sized source low on the left and behind: shadows have a penumbra that grows with the lift
        {"name": "window", "loc": [-40, 30, 17], "target": [0, -1, 0], "size": [8, 12], "watts": 62000, "rgb": [1.0, 0.95, 0.88]},
        {"name": "fill", "loc": [24, -30, 34], "target": [0, -1, 0], "size": [44, 44], "watts": 3600, "rgb": [0.9, 0.95, 1.0]},
    ]
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "paper", "npz": npz, "material": {"Base Color": "col", "Alpha": "alpha", "Roughness": 0.82, "Specular IOR Level": 0.3}},
            {"name": "cloth", "npz": npz2, "material": {"Base Color": "col", "Roughness": 0.88, "Specular IOR Level": 0.2, "Sheen Weight": 0.25, "Sheen Roughness": 0.45}},
        ],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 1,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    develop = {"exposure": 0.16, "contrast": 1.28, "saturation": 1.02, "black": 0.0015, "grain": 1.2, "sharpen": 0.25, "halation": 0.04, "glare": 0.003, "vignette": 0.3}
    if wind:
        # a candidate under its own name: _take clears {name}_move_*, and the film reads s24_jianzhi_move_final. A static camera; only the paper moves
        import json

        import kit

        wp = os.path.join(d, "wind.npy")
        if not os.path.exists(wp):
            raise SystemExit(f"missing {wp}: run s24_wind.py first")
        scene["deform"] = {"npy": wp, "extent": json.load(open(wp + ".json"))["extent"], "mesh": "paper"}
        frames = np.load(wp, mmap_mode="r").shape[0]
        lk = kit.looks().get(NAME, {})
        kit.looks = lambda: {NAME + "_wind": {**{k: v for k, v in lk.items() if k != "move"}, "move": {"frames": frames, "shutter": 0, "spp": 192}}}
        os.environ["GEWU_MOVE"] = wind
        shoot(NAME + "_wind", scene, q, develop=develop)
        return
    shoot(NAME, scene, "preview" if q == "sketch" else q, develop=develop, tag="cand" if q == "final" else q)  # the film reads final.*: a candidate goes to cand.* until it has passed a look at 100%


main()
