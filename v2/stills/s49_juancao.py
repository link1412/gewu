"""s49, scrolling leaf (卷草) in openwork cloisonne: the old plate's gilt lip, wire and enamel, no flower heads, no medallion, no circles. Black shows between the leaves.

    python3 -I v2/stills/s49_juancao.py flat            2D only, cut to the film's frame: out/v2/s49_falang/juancao_flat.jpg
    python3 -I v2/stills/s49_juancao.py mid|final      mid's tag is juancao_mid, final's is cand; never writes final.*. No motion here yet

S49_PXCM sets the flat grid (default 320 px/cm), S49_SMALL writes a 640 wide copy to that path.
The render has the old plate's material: falang_shader.py, its lights, env, sky, camera and develop, unchanged; enamel leaves are its glass, the black between them its void, truly open. The flat leaves out the old cloud and the render puts it back at the old amount. The stem is the lip's gilt with a half-round section: an estimate, no measurement behind its height.

The drawing is composed in a strip (x along the arc, y = rho, both cm), then bent onto the plate. One stem, a sine-generated curve, swings across the frame one way: curvature runs as a sine along it, so no part is straight, and it thins from each root to the next. Each bend holds one big half-palmette (table in LEAVES): a rib with a slit of black along the stem, lobes radiating from one side of it, the biggest near the root, each tip rolled back. Lobe sizes and angles are jittered per lobe, so that no two are one lobe transformed. fill_gaps() then grows curls and small shoots into whatever black is left.

Tang-style shading (叠晕): each lobe is nested tongues, one enamel to a layer, light at the margin, deep at the core, clean steps, a wire on most first boundaries. Form checked by eye against the Met's Tang textile 39595 (the fleshy lobes and the stepped bands; it is a medallion, not a scroll), reference only; nothing is copied.
The stem is solid gilt, our choice: one unbroken line reads as one stem at a glance, the colours stay in the leaves, and an openwork needs something to carry it. In the flat it is lit by hand (a rounded form, a lamp above, colours set by eye to the lip): a stand-in for the render.
Colours are picked by eye, not measured. Sizes follow the old plate (PROFILE, LOBES, camera), which are themselves estimates.

fields() and paint() are s49_falang.py's, copied here, because that file runs main() on import and must not change. What differs: a shape carries its own three stops, an inner layer can have no wire, the whole plate in frame is openwork, and the glaze keeps its noise.
The flat's lip and room are pixels of the old render out/v2/s49_falang/cand_huahui.jpg (same camera), a stand-in; wire and enamel carry no light at all in the flat.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.interpolate import LinearNDInterpolator

from chanzhi import catmull, uv
from dishkit import Dish
from kit import OUT, caps, color, fbm, mix, rank, shoot, sstep
from vessel import project, reflect_light_loc

NAME = "s49_falang"
SEED = 4949
W, EL, DIST = 9.6, 70.0, 88.0  # the old cand's camera
PROFILE = [(4.0, 0.0), (4.3, 0.18), (5.6, 0.72), (6.7, 1.5), (7.15, 2.0), (7.26, 2.22), (7.22, 2.36), (7.05, 2.36), (6.72, 1.92), (5.8, 1.12), (4.6, 0.62), (2.5, 0.42), (0.0, 0.38)]
LOBES = dict(n=14, a=0.03, b=0.12, p=0.8, rho0=5.8)
RHO_REF = 6.4  # the strip's x is arc length at this rho

# deep to light, sRGB, by eye. Saturated in the middle, kept dark at the deep end so that they stay enamel and not candy
FAMILY = {
    "mag": [(44, 3, 34), (92, 6, 62), (140, 10, 80), (178, 20, 96), (206, 58, 120)],
    "blu": [(4, 6, 66), (8, 24, 142), (14, 62, 226), (30, 104, 255), (92, 158, 255)],
    "cya": [(0, 36, 50), (0, 86, 106), (0, 146, 158), (10, 192, 190), (96, 222, 212)],
}


def tone(fam, t, shift=0.0):
    """A colour along a family, t 0 deep to 1 light. sRGB tuple."""
    r = np.array(FAMILY[fam], float)
    u = np.clip(t + shift, 0, 1) * (len(r) - 1)
    i = min(int(u), len(r) - 2)
    return tuple(r[i] + (r[i + 1] - r[i]) * (u - i))


def srgb(c):
    c = np.array(c, np.float32) / 255.0
    return np.where(c < 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


# --- a stroke: a spine by its curvature, then widths on either side
class Stroke:
    def __init__(self, p, a, L, kappa, wl, wr, rng=None, wander=0.05, n=90):
        """kappa(s), wl(s), wr(s) with s in 0..1: curvature per cm, width to the left and the right of the direction of travel. wander: the hand, as a fraction of the width."""
        self.s = np.linspace(0, 1, n)
        k = kappa(self.s)
        ds = L / (n - 1)
        h = a + np.r_[0.0, np.cumsum(0.5 * (k[1:] + k[:-1]) * ds)]
        step = np.stack([np.cos(h), np.sin(h)], 1) * ds
        self.spine = np.asarray(p, float) + np.r_[np.zeros((1, 2)), np.cumsum(0.5 * (step[1:] + step[:-1]), 0)]
        self.h = h
        self.nrm = np.stack([-np.sin(h), np.cos(h)], 1)  # to the left
        # the inside of a tight bend has no room: narrower than the radius there, or the outline crosses itself
        room = 0.82 / np.maximum(np.abs(k), 1e-3)
        self.wl = np.where(k > 0, np.minimum(wl(self.s), room), wl(self.s))
        self.wr = np.where(k < 0, np.minimum(wr(self.s), room), wr(self.s))
        self.L = L
        self.a = a
        r = rng or np.random.default_rng(0)
        f = r.uniform(5, 11, 3)
        ph = r.uniform(0, 6.28, 6)
        self.bl = 1 + wander * (np.sin(self.s * f[0] + ph[0]) + 0.6 * np.sin(self.s * f[1] * 2 + ph[1]))
        self.br = 1 + wander * (np.sin(self.s * f[2] + ph[2]) + 0.6 * np.sin(self.s * f[0] * 2 + ph[3]))

    def at(self, s):
        i = int(np.clip(s, 0, 1) * (len(self.s) - 1))
        return self.spine[i], self.h[i]

    def outline(self, f=1.0, g=1.0, slide=0.0):
        """Closed polygon. f: width fraction. g: how far along the spine the tongue runs. slide: start this far along, so that inner tongues sit off the base."""
        m = len(self.s)
        idx = np.linspace(slide * (m - 1), g * (m - 1), m)
        sp = np.stack([np.interp(idx, np.arange(m), self.spine[:, j]) for j in (0, 1)], 1)
        nr = np.stack([np.interp(idx, np.arange(m), self.nrm[:, j]) for j in (0, 1)], 1)
        # the same width profile, compressed into the tongue's length, never wider than the full stroke at that point
        prof = np.arange(m)
        wl_ = np.minimum(np.interp(prof, np.arange(m), self.wl), np.interp(idx, np.arange(m), self.wl))
        wr_ = np.minimum(np.interp(prof, np.arange(m), self.wr), np.interp(idx, np.arange(m), self.wr))
        wl_, wr_ = wl_ * f * self.bl, wr_ * f * self.br
        return np.vstack([sp + nr * wl_[:, None], (sp - nr * wr_[:, None])[::-1]])


def belly(W_, peak=0.38, tip=1.0):
    """A comma's width along its spine: quick to swell, long taper to a point."""
    base_ = peak * tip / max(1 - peak, 1e-3)  # s**a * (1-s)**tip peaks at a/(a+tip): match it to `peak`
    norm = peak**base_ * (1 - peak) ** tip
    return lambda s: W_ * np.maximum(s, 1e-4) ** base_ * np.maximum(1 - s, 0) ** tip / norm


class Drawing:
    def __init__(self, seed):
        self.items = []
        self.rng = np.random.default_rng(seed)
        self.marks = []  # (index in items, family): what follows belongs to that leaf

    def mark(self, fam):
        self.marks.append((len(self.items), fam))

    def wire(self, path, p0=1.0, p1=1.0):
        self.items.append(("w", np.asarray(path), float(p0), float(p1)))

    def shape(self, poly, stops, o, ang, L, wired=True):
        r = self.rng
        self.items.append(("s", np.asarray(poly), stops, np.asarray(o, float), float(ang), float(L), float(r.normal(0, 0.05)), float(r.uniform(0.9, 1.1)), float(r.uniform(0.95, 1.05)), bool(wired)))


def stops_for(fam, t, spread=0.13, shift=0.0):
    return (tone(fam, t - spread, shift), tone(fam, t, shift), tone(fam, t + spread, shift))


RENDER_GLAZE = False
LEVELS = {3: (0.86, 0.5, 0.14), 4: (0.9, 0.64, 0.38, 0.12), 5: (0.94, 0.72, 0.5, 0.3, 0.08)}  # one enamel to a layer, so that the steps read: Tang 叠晕, margin light, core deep


def tongues(D, st, fam, rng, layers=4, bright=0.0, wire_inner=0.5):
    """One lobe, nested from the margin in. Each layer one colour with a slight run from base to tip, a clean edge between; the first boundary in usually carries a wire."""
    base = st.spine[0]
    chord = st.spine[-1] - st.spine[0]
    ca = np.arctan2(chord[1], chord[0])
    Lc = max(float(np.hypot(*chord)), 1e-3)
    fs = {3: (1.0, 0.66, 0.36), 4: (1.0, 0.74, 0.5, 0.27), 5: (1.0, 0.8, 0.62, 0.44, 0.25)}[layers]
    gs = {3: (1.0, 0.8, 0.56), 4: (1.0, 0.86, 0.68, 0.46), 5: (1.0, 0.89, 0.75, 0.59, 0.4)}[layers]
    jit = rng.normal(0, 0.02)
    for k in range(layers):
        t = LEVELS[layers][k] + bright + jit
        g = gs[k] * rng.uniform(0.97, 1.03) if k else 1.0
        f = fs[k] * rng.uniform(0.96, 1.04) if k else 1.0
        poly = st.outline(f, min(g, 1.0), slide=0.0 if k == 0 else 0.02 * k)
        wired = k == 0 or (k == 1 and rng.random() < wire_inner)
        # in the render each layer spans more of its family, so that the old clouds and the old run from base to tip have something to move through (with one flat enamel they vanish); and the margins sit lower, because the glass's skin and the lamp behind already lift them
        D.shape(poly, stops_for(fam, 0.9 * t, 0.09) if RENDER_GLAZE else stops_for(fam, t, 0.035), base, ca, Lc, wired)


# --- the stem: a sine-generated curve. Curvature runs as a sine along the length, so every part of it is turning and only the inflection is momentarily straight; there is no straight run and no peak
SWINGS = [(3.9, 0.82), (3.55, 0.92), (3.6, 0.98), (3.45, 0.95), (3.5, 0.58), (3.5, 0.72), (3.5, 0.85), (3.5, 0.85)]  # arc length, half the heading swing in radians. Each its own: by hand
STEM_START = (-9.2, 5.6)
FIRST_SIGN = -1


def bow(x):
    """The band under the lip narrows towards the frame's corners: the stem's middle rises with it."""
    return 0.58 * (np.clip(np.abs(x), 0, 6.0) / 4.5) ** 2


def stem_path():
    """Returns the path (strip cm) and the x of each inflection. Goes one way, left to right."""
    ds = 0.01
    k, nodes = [], []
    sg = FIRST_SIGN
    for ln, om in SWINGS:
        n_ = int(ln / ds)
        t = (np.arange(n_) + 0.5) / n_
        k.append(sg * (np.pi * 2 * om / (2 * ln)) * np.sin(np.pi * t))
        nodes.append(n_)
        sg = -sg
    k = np.concatenate(k)
    h = np.cumsum(k) * ds + FIRST_SIGN * -SWINGS[0][1]
    q = np.stack([np.cumsum(np.cos(h)) * ds, np.cumsum(np.sin(h)) * ds], 1) + STEM_START
    q[:, 1] += bow(q[:, 0])
    # never into the lip: above 6.9 the rise is folded down softly, which also keeps it from standing straight up off the frame
    over = np.maximum(q[:, 1] - 6.9, 0)
    q[:, 1] -= over - 0.25 * (1 - np.exp(-over / 0.25))
    ids = np.cumsum(nodes)[:-1]
    return q[::4], q[ids, 0]


def stem_ribbon(D, path, xs):
    """Solid gilt. Thins from each root to the next, like a line drawn with one loaded brush; the thick restart is under the next leaf's root."""
    hi, lo = 0.098, 0.042
    x = path[:, 0]
    nodes = np.r_[x[0] - 1e-3, xs, x[-1] + 1e-3]
    i = np.clip(np.searchsorted(nodes, x) - 1, 0, len(nodes) - 2)
    f = (x - nodes[i]) / (nodes[i + 1] - nodes[i])
    hw = lo + (hi - lo) * (1 - f) ** 1.2
    hw = cv2.GaussianBlur(hw.astype(np.float32)[None], (0, 0), 4.0)[0]
    d = np.gradient(path, axis=0)
    n_ = np.stack([-d[:, 1], d[:, 0]], 1) / (np.hypot(*d.T)[:, None] + 1e-9)
    poly = np.vstack([path + n_ * hw[:, None], (path - n_ * hw[:, None])[::-1]])
    D.shape(poly, None, path[0], 0.0, 1.0, wired=False)


def stem_at(path, x):
    i = int(np.argmin(np.abs(path[:, 0] - x)))
    d = path[min(i + 2, len(path) - 1)] - path[max(i - 2, 0)]
    return path[i], float(np.arctan2(d[1], d[0]))


# --- the leaf
def leaf(D, path, x, fam, turn, L, knots, bfull, bthin, lobes, dev=0.1, bright=0.0, seed=0, at=None, sd=1, plain_rib=False):
    """A full half-palmette. The rib runs along the stem's bend, a slit of black between them, and is flung on past it; the body is wide on one side (sd=+1 the concave side, the bend's interior) and the lobes spread from there, the biggest near the root, each smaller: each leans forward, and its tip rolls back.
    lobes: (s on the rib, angle off the rib, length, width, roll at the tip (positive back towards the root, negative forward), layers). at: root (p, a) instead of a place on the stem."""
    rng = np.random.default_rng(SEED + seed)
    p, a = at if at is not None else stem_at(path, x)
    a = a + turn * dev
    o = turn * sd
    kap = lambda s_: turn * np.interp(s_, np.linspace(0, 1, len(knots)), knots)
    wf = belly(bfull, peak=0.38, tip=0.85)
    wt = belly(bthin, peak=0.46, tip=1.0)
    wl, wr = (wf, wt) if o > 0 else (wt, wf)
    body = Stroke(p, a, L, kap, wl, wr, rng, wander=0.03)
    tongues(D, body, fam, rng, layers=4, bright=bright - 0.04, wire_inner=0.0 if plain_rib else 1.0)  # plain_rib: only its outline, when the lobes already crowd the root with lines
    strokes = []
    for s_, off, ll, ww, roll, lay in lobes:
        q, h = body.at(s_)
        ha = h + o * off
        c0 = rng.uniform(0.2, 0.55)
        kp = lambda t, r=roll, c_=c0: o * (-c_ * (1 - t) ** 1.5 + r * t**4)
        pk = rng.uniform(0.42, 0.54)
        wa = belly(ww, peak=pk, tip=rng.uniform(0.7, 0.95))
        wb = belly(ww * rng.uniform(0.72, 0.92), peak=pk + rng.uniform(-0.04, 0.04), tip=rng.uniform(0.7, 0.95))
        wl_, wr_ = (wb, wa) if o > 0 else (wa, wb)  # the fuller side faces forward
        strokes.append((s_, Stroke(q - 0.03 * uv(ha), ha, ll, kp, wl_, wr_, rng, wander=0.035), lay))
    for s_, st, lay in sorted(strokes, key=lambda z: -z[0]):  # from the tip back: each lobe lies over the base of the next one out, its tip free
        tongues(D, st, fam, rng, layers=lay, bright=bright + rng.normal(0, 0.02), wire_inner=0.75)
    if not plain_rib:
        D.wire(body.spine[: int(len(body.spine) * 0.96)], 1.25, 0.7)  # the midrib
    return body


def tendril(D, p, a, turn, L, k0, k1, p0=0.95, p1=0.5):
    """A wire off a stem: a line whose curve tightens, so it never reads as a circle."""
    st = Stroke(p, a, L, lambda s: turn * (k0 + (k1 - k0) * s**2), lambda s: 0 * s, lambda s: 0 * s, n=70)
    D.wire(st.spine, p0, p1)
    return st


def hook(D, p, a, turn, L, W_, fam, rng, bright=0.0, curl=4.5):
    """A small shoot in enamel: a stroke with a curled tip."""
    st = Stroke(p, a, L, lambda s: turn * (0.3 + curl * s**2.4), belly(W_), belly(W_ * 0.7), rng)
    tongues(D, st, fam, rng, layers=3, bright=bright, wire_inner=0.0)
    return st


# --- what the frame sees, in strip cm. An estimate from the camera's numbers, to aim the filling; the picture itself goes through the real camera
def frame_mask(xx, yy):
    return (np.abs(xx) < 5.05) & (yy > 4.75 + 1.25 * (xx / 4.5) ** 2 - 0.05) & (yy < 7.3)


FILL_PX = 40


def occupancy(items):
    xs = (np.arange(int(20 * FILL_PX)) + 0.5) / FILL_PX - 10
    ys = (np.arange(int(6 * FILL_PX)) + 0.5) / FILL_PX + 3
    occ = np.zeros((len(ys), len(xs)), np.uint8)

    def px(q):
        return np.round((np.asarray(q) - [xs[0], ys[0]]) * FILL_PX).astype(np.int32)

    for it in items:
        if it[0] == "w":
            cv2.polylines(occ, [px(it[1])], False, 1, 3)
        else:
            cv2.fillPoly(occ, [px(it[1])], 1)
    X, Y = np.meshgrid(xs, ys)
    return occ, X, Y, px


def fill_gaps(D, rng, thresh=0.3, most=14):
    """The black left over gets tendrils: find the largest empty circle in the frame, grow a curl into it from the nearest drawing; the bigger holes get a little leaf on the way. Until nothing is left above thresh."""
    occ, X, Y, px = occupancy(D.items)
    occ = occ.copy()
    occ[Y > 7.3] = 1  # the lip
    placed = []
    rng2 = np.random.default_rng(SEED + 2)
    cen, cfam = [], []
    for i, (i0, fam) in enumerate(D.marks):
        i1 = D.marks[i + 1][0] if i + 1 < len(D.marks) else len(D.items)
        for it in D.items[i0:i1]:
            cen.append(it[1].mean(0))
            cfam.append(fam)
    cen = np.array(cen)
    for _ in range(most):
        dist = cv2.distanceTransform(1 - occ, cv2.DIST_L2, 5) / FILL_PX
        dist = dist * frame_mask(X, Y)
        j, i = np.unravel_index(int(np.argmax(dist)), dist.shape)
        d = float(dist[j, i])
        if d < thresh:
            break
        c = np.array([X[j, i], Y[j, i]])
        oy, ox = np.nonzero(occ & (Y <= 7.3))
        k = int(np.argmin((X[oy, ox] - c[0]) ** 2 + (Y[oy, ox] - c[1]) ** 2))
        p0 = np.array([X[oy[k], ox[k]], Y[oy[k], ox[k]]])
        a0 = float(np.arctan2(*(p0 - c)[::-1]))
        if d > 0.42:  # a little shoot of the nearest leaf's colour, leaving the drawing at a slant and curling round the hole, so that it runs with the black
            near = np.hypot(cen[:, 0] - c[0], cen[:, 1] - c[1])
            fam = cfam[int(np.argmin(near))]
            sg = rng.choice([-1, 1])
            ang = a0 + np.pi + sg * rng.uniform(0.75, 1.15)
            kp_ = lambda t, g=-sg: g * (0.5 + 7.0 * t**3)
            st = Stroke(p0 - 0.04 * uv(ang), ang, 2.3 * d, kp_, belly(0.36 * d), belly(0.24 * d), rng)
            for sc_ in (0.85, 0.7, 0.55, 0.42):  # no shoot reaches the lip: only the one wire holds there
                if st.outline()[:, 1].max() < 7.16:
                    break
                st = Stroke(p0 - 0.04 * uv(ang), ang, 2.3 * d * sc_, kp_, belly(0.36 * d), belly(0.24 * d), rng2)
            n0 = len(D.items)
            tongues(D, st, fam, rng, layers=3, bright=-0.04, wire_inner=0.6)
            new = D.items[n0:]
            del D.items[n0:]
            placed += new
            for it in new:
                cv2.fillPoly(occ, [px(it[1])], 1)
            continue
        sg = rng.choice([-1, 1])
        R = 0.8 * d
        turns = rng.uniform(0.9, 1.7)
        t = np.linspace(0, 1, 44)
        r_ = R * (1 - rng.uniform(0.7, 0.92) * t ** rng.uniform(0.55, 1.1))  # each curl its own tightness
        ang = a0 + sg * 0.9 + sg * 2 * np.pi * turns * t
        sp = c + np.stack([r_ * np.cos(ang), r_ * np.sin(ang)], 1)
        path = np.vstack([catmull([p0, 0.45 * p0 + 0.55 * sp[0], sp[0]], 8)[:-1], sp])
        if rng.random() < 0.5:  # now and then a small fork off the line
            f0 = path[5]
            fa = float(np.arctan2(*(path[6] - path[4])[::-1])) - sg * 0.8
            placed.append(("w", Stroke(f0, fa, 0.5 * R + 0.12, lambda u, g=-sg: g * (1.0 + 16.0 * u**2), lambda u: 0 * u, lambda u: 0 * u, n=30).spine, 0.85, 0.45))
        placed.append(("w", path, 1.1, 0.55))
        cv2.circle(occ, tuple(int(v) for v in px(c)), int((R + 0.05) * FILL_PX), 1, -1)
        cv2.polylines(occ, [px(path[:12])], False, 1, 3)
    D.items[:0] = placed  # under the leaves
    print("gaps filled", len(placed), "largest left", round(d, 3), flush=True)


def design():
    """Painter's list in strip cm. Hand composed: each row below is one leaf."""
    D = Drawing(SEED)
    path, xs = stem_path()
    print("inflections", np.round(xs, 2), flush=True)
    stem_ribbon(D, path, xs)
    LEAVES(D, path, xs)
    fill_gaps(D, np.random.default_rng(SEED + 1))
    return D


def fan(seed, n, s0, s1, off0, off1, Lmax, wr=0.3, peak=0.3, floor=0.42, roll=(8, 11)):
    """Lobes of a palmette, listed root to tip: they radiate, the first leaning back, the last nearly along the rib, so that they spread and their tips stay free. The longest at `peak` along the row, falling away towards the tip faster than towards the root. Every lobe jittered by hand, none the same."""
    r = np.random.default_rng(SEED + 500 + seed)
    out = []
    for i in range(n):
        t = i / (n - 1)
        env = floor + (1 - floor) * (t / peak if t < peak else 1 - ((t - peak) / (1 - peak)) ** 1.5)
        ll = Lmax * env * r.uniform(0.84, 1.12)
        out.append((s0 + (s1 - s0) * t + r.normal(0, 0.008), off0 + (off1 - off0) * t**0.85 + r.normal(0, 0.09), ll, ll * wr * r.uniform(0.82, 1.16), r.uniform(*roll), 5 if ll > 1.25 else 4 if ll > 0.7 else 3))
    return out


def LEAVES(D, path, xs):
    # x on the stem, family, turn, rib length, curvature by knots, body full side, thin side; lobes from fan(seed, count, first and last s, first and last angle, longest, ...)
    # off the left edge
    leaf(D, path, -8.6, "blu", -1, 3.0, [0.3, 0.4, 0.3, 1.4], 0.3, 0.1, fan(1, 5, 0.12, 0.88, 2.2, 0.4, 1.2), seed=1)
    # the left, high in the band under the lip: six lobes
    D.mark("mag")
    leaf(D, path, -5.35, "mag", 1, 2.55, [0.15, 0.3, 0.35, 1.8], 0.3, 0.1, fan(2, 6, 0.12, 0.9, 2.3, 0.3, 1.15, peak=0.35), dev=0.55, seed=2)
    # the largest, under the crest at the middle: seven lobes hanging down, the rib flung on and rolled
    D.mark("cya")
    leaf(D, path, -3.1, "cya", -1, 3.05, [0.75, 0.4, 0.3, 0.5, 2.2], 0.34, 0.11, fan(3, 7, 0.1, 0.92, 2.7, 0.1, 1.5, peak=0.42), dev=0.36, seed=3)
    # in the deep trough right of the middle: six lobes
    D.mark("blu")
    leaf(D, path, -0.1, "blu", 1, 2.75, [0.2, 0.42, 0.55, 0.65, 2.3], 0.34, 0.11, fan(4, 6, 0.12, 0.9, 2.55, 0.15, 1.72, peak=0.42), dev=0.52, seed=4, plain_rib=True)
    # under the right crest, into the frame's corner
    D.mark("mag")
    leaf(D, path, 2.5, "mag", -1, 2.9, [0.55, 0.35, 0.3, 0.45, 1.9], 0.3, 0.1, fan(5, 6, 0.14, 0.88, 2.6, 0.2, 1.3, peak=0.38), dev=0.3, seed=5)
    # past the right edge, so that a turn of the plate brings something
    D.mark("cya")
    leaf(D, path, 5.4, "cya", 1, 3.0, [0.3, 0.4, 0.35, 1.3], 0.3, 0.1, fan(6, 5, 0.12, 0.88, 2.2, 0.4, 1.15), seed=6)


def bend(p):
    """Strip (x, rho) to the plate's flat coordinates."""
    th = p[:, 0] / RHO_REF
    return np.stack([p[:, 1] * np.sin(th), p[:, 1] * np.cos(th)], 1)


# --- from the drawing to fields on a grid. As s49_falang.py's paint(), with own stops and wire-less layers
def paint(X, Y, pxcm, items):
    ny, nx = X.shape
    SS = 2
    x0, y0 = float(X[0, 0]), float(Y[0, 0])
    wobx = fbm((96, 96), 8.0, 1.0, 5.0, 3.0, SEED + 1)
    woby = fbm((96, 96), 8.0, 1.0, 5.0, 3.0, SEED + 2)
    fx = fbm((96, 96), 8.0, 0.3, 1.2, 2.2, SEED + 3)

    def wob(p):
        ix = np.clip(((p[:, 0] + 12) * 4).astype(int), 0, 95)
        iy = np.clip(((p[:, 1] + 12) * 4).astype(int), 0, 95)
        return p + np.stack([0.02 * wobx[iy, ix] + 0.005 * fx[iy, ix], 0.02 * woby[iy, ix] + 0.005 * fx[ix, iy]], 1)

    def to(p, s):
        return np.round((p - [x0, y0]) * pxcm * s * 16 + (s / 2 - 0.5) * 16).astype(np.int32)

    center = np.zeros((ny * SS, nx * SS), np.uint8)
    idx = np.zeros((ny, nx), np.int32)
    meta = [(None, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0)]
    gfull = np.zeros((ny, nx), np.uint8)  # the stem whole, leaves or no leaves: for its form
    wmap = np.full((ny, nx), 100, np.uint8)
    rhand = np.random.default_rng(SEED + 40)

    def press(path, p0, p1, stroke):
        q = to(path, 1) >> 4
        n_ = len(q)
        if n_ < 2:
            return
        t_ = np.linspace(0, 1, n_)
        pr = stroke * (p0 + (p1 - p0) * t_) * (1 + 0.1 * np.sin(t_ * rhand.uniform(3, 9) + rhand.uniform(0, 6)))
        for _ in range(rhand.integers(0, 3)):
            pr = pr * (1 + 0.28 * np.exp(-(((t_ - rhand.uniform(0, 1)) / 0.04) ** 2)))
        vals = np.clip(pr * 100, 20, 255).astype(np.uint8)
        for i in range(n_ - 1):
            cv2.line(wmap, tuple(int(c) for c in q[i]), tuple(int(c) for c in q[i + 1]), int(vals[i]), 5)

    for it in items:
        if it[0] == "w":
            q = wob(bend(it[1]))
            cv2.polylines(center, [to(q, SS)], False, 255, 1, cv2.LINE_8, shift=4)
            press(q, it[2], it[3], rhand.uniform(0.88, 1.12))
        else:
            _, poly, stops, o, ang, L, sh, sc, gn, wired = it
            q = wob(bend(poly))
            q2 = to(q, SS)
            cv2.fillPoly(center, [q2], 0, cv2.LINE_8, shift=4)
            if stops is None:
                cv2.fillPoly(gfull, [to(q, 1)], 1, cv2.LINE_8, shift=4)
            if wired:
                cv2.polylines(center, [q2], True, 255, 1, cv2.LINE_8, shift=4)
                press(np.vstack([q, q[:1]]), 1.0, 1.0, rhand.uniform(0.85, 1.15))
            # the shading axis, bent with the drawing
            a_ = bend(np.vstack([o, o + 0.1 * np.array([np.cos(ang), np.sin(ang)])]))
            meta.append((stops, float(a_[0, 0]), float(a_[0, 1]), float(np.arctan2(*(a_[1] - a_[0])[::-1])), float(L), sh, sc, gn))
            cv2.fillPoly(idx, [to(q, 1)], len(meta) - 1, cv2.LINE_8, shift=4)
    dist = cv2.distanceTransform(255 - center, cv2.DIST_L2, 5) / (pxcm * SS)
    dist = cv2.resize(dist, (nx, ny), interpolation=cv2.INTER_AREA).astype(np.float32)
    return dist, idx, meta, cv2.GaussianBlur(wmap.astype(np.float32) / 100.0, (0, 0), 1.2), gfull


def stem_form(gfull, pxcm):
    """A half-round section over the whole stem, leaves or no leaves: its height in cm, as tall as it is half wide."""
    g_ = (gfull > 0).astype(np.uint8)
    dg = cv2.distanceTransform(g_, cv2.DIST_L2, 5).astype(np.float32) / pxcm
    rw = int(0.12 * pxcm) | 1
    hwl = cv2.GaussianBlur(cv2.dilate(dg, np.ones((rw, rw), np.uint8)), (0, 0), 0.03 * pxcm)
    u = np.clip(dg / np.maximum(hwl, 1e-3), 0, 1)
    return cv2.GaussianBlur(np.sqrt(np.maximum(1 - (1 - u) ** 2, 0.0)) * hwl, (0, 0), 0.006 * pxcm)


def fields(X, Y, pxcm, rl, clouds=False):
    """Colour and masks in the flat. As s49_falang.py's fields(), wire and glaze the same; the ground is air everywhere. clouds: the old plate's mottling at the old amount (the render), else one even enamel a layer (the flat)."""
    shape = X.shape
    dist, idx, meta, wpress, gfull = paint(X, Y, pxcm, design().items)
    rho = np.hypot(X, Y)
    wid = 0.72 + 0.56 * rank(fbm(shape, pxcm, 0.3, 1.6, 2.4, SEED + 5))
    hw = (0.0104 + 0.0014 * fbm(shape, pxcm, 0.04, 0.3, 2.0, SEED + 6)) * wid
    hw = hw * wpress  # finer than the old band's 1.22: at this scale, with this much drawing inside a lobe, it was heavy
    wire = sstep(1.0, 0.8, dist / hw)
    edge = np.clip(dist / hw, 0, 1)

    free_ = (wire < 0.5).astype(np.uint8)
    n_cells, lab = cv2.connectedComponents(free_, connectivity=4)
    d_in = cv2.distanceTransform(free_, cv2.DIST_L2, 5).astype(np.float32) / pxcm

    powder = rank(fbm(shape, pxcm, 0.012, 0.05, 1.2, SEED + 7))
    cloud = rank(fbm(shape, pxcm, 0.1, 0.9, 2.3, SEED + 8))
    blendn = fbm(shape, pxcm, 0.06, 0.5, 2.0, SEED + 9)
    grit = rank(fbm(shape, pxcm, 0.006, 0.02, 1.0, SEED + 18))
    N = len(meta)
    gilded = np.zeros(N, np.float32)
    stops = np.zeros((N, 3, 3), np.float32)
    ox, oy, ax, ay, Ln, sh, sc, gn = (np.zeros(N, np.float32) for _ in range(8))
    for i, (st, o0, o1, ang, L, sh_, sc_, gn_) in enumerate(meta):
        if st is not None:
            stops[i] = np.array([srgb(c) for c in st])
        elif i:
            gilded[i] = 1.0
        ox[i], oy[i], ax[i], ay[i], Ln[i], sh[i], sc[i], gn[i] = o0, o1, np.cos(ang), np.sin(ang), max(L, 1e-3), sh_, sc_, gn_

    # a tone edge without a wire is not a clean line: powders laid side by side. Displace the lookup a little, but only inside one enamelled area
    isg0 = idx == 0
    dn1 = fbm(shape, pxcm, 0.06, 0.3, 2.2, SEED + 30)
    dn2 = fbm(shape, pxcm, 0.06, 0.3, 2.2, SEED + 31)
    amp = 0.004 * pxcm  # only enough that an edge between two powders is not ruled
    gy, gx = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    idx_d = cv2.remap(idx.astype(np.float32), gx + amp * dn1, gy + amp * dn2, cv2.INTER_NEAREST).astype(np.int32)
    idx_c = np.where((idx_d == 0) | isg0, idx, idx_d)

    t = ((X - ox[idx_c]) * ax[idx_c] + (Y - oy[idx_c]) * ay[idx_c]) / Ln[idx_c] * sc[idx_c] + sh[idx_c] + (0.12 * blendn + 0.1 * (powder - 0.5) + 0.04 * (grit - 0.5) if clouds else 0.03 * (powder - 0.5))
    col = stops[idx_c, 0]
    col = mix(col, stops[idx_c, 1], sstep(0.1, 0.48, t))
    col = mix(col, stops[idx_c, 2], sstep(0.58, 1.02, t))
    cl = (0.5 + 0.34 * (cloud - 0.5))[..., None]
    col = col * (0.82 + 0.36 * cl if clouds else 1.0) * gn[idx_c][..., None]  # the flat has no clouds: there the mottling read as watercolour
    # powders melt a little into each other. Enamel only: the air does not bleed in
    en = (~isg0).astype(np.float32)
    sig = 0.002 * pxcm
    col = np.where(isg0[..., None], col, cv2.GaussianBlur(col * en[..., None], (0, 0), sig) / np.maximum(cv2.GaussianBlur(en, (0, 0), sig), 1e-3)[..., None])

    lv = np.random.default_rng(SEED + 10).normal(0, 1, n_cells).astype(np.float32)
    level = lv[lab]
    col = col * (1.0 + 0.42 * (0.34 * (powder[..., None] - 0.5) + 0.22 * (grit[..., None] - 0.5)))
    col = col * (1.0 + 0.07 * np.clip(level, -2, 2)[..., None])
    seam_n = rank(fbm(shape, pxcm, 0.08, 0.5, 2.0, SEED + 11))
    gather = np.exp(-d_in / 0.018) * (0.25 + 0.75 * sstep(0.2, 0.75, seam_n))
    col = col * (1.0 - 0.62 * gather)[..., None]
    fleck = sstep(0.955, 0.992, grit) * sstep(0.3, 0.7, rank(fbm(shape, pxcm, 0.2, 1.2, 2.2, SEED + 12)))
    col = mix(col, np.minimum(col * 1.5 + 0.2, 1.0), 0.6 * fleck)

    dens = 0.25 + 1.5 * rank(fbm(shape, pxcm, 0.5, 2.6, 2.4, SEED + 13)) + 0.5 * np.exp(-d_in / 0.05)
    pits = caps(shape, pxcm, 7, 0.003, 0.012, SEED + 14, slope=-3.8) * sstep(1.05, 1.5, dens)
    pit = sstep(0.0, 0.0028, pits)
    col = mix(col, color([0.014, 0.011, 0.009]), pit * (1 - wire) * 0.94)

    wear = sstep(0.62, 0.9, rank(fbm(shape, pxcm, 0.03, 0.3, 2.0, SEED + 15)))
    gold = mix(color([0.92, 0.60, 0.22]), color([0.72, 0.44, 0.18]), wear)
    gm = cv2.GaussianBlur(gilded[idx], (0, 0), 0.8)
    wire = np.maximum(wire, gm)
    col = mix(col, gold, wire)
    wob = 0.02 * fbm(shape, pxcm, 0.5, 2.5, 3.0, SEED + 16)
    rim = sstep(rl - 0.36, rl - 0.33, rho + wob)
    wear2 = sstep(0.55, 0.9, rank(fbm(shape, pxcm, 0.06, 0.5, 2.0, SEED + 17)))
    gilt_c = mix(color([1.0, 0.68, 0.26]), color([0.8, 0.46, 0.2]), 0.4 * wear2)
    col = mix(col, gilt_c, np.maximum(rim, gm))  # the stem is the lip's metal, the lip's colour
    void = (isg0 * (1 - wire)).astype(np.float32) * (1 - rim)
    void = np.maximum(void, sstep(rl + 0.26, rl + 0.3, rho))
    glass = ((~isg0) * (1 - wire) * (1 - rim)).astype(np.float32)
    return dict(void=void, glass=glass, col=col, wire=wire, edge=edge, d_in=d_in, level=level, lab=lab, n=n_cells, pits=pits, pit=pit, rim=rim, cloud=cloud, wear=wear, wear2=wear2, gm=gm, gfull=gfull)


# --- the film's frame
def frame_lut(dish, cam, w, h):
    """For each pixel of the frame, where on the flat plate it looks. NaN where it misses. The far side only: past rl + .26 the plate stops, so no folds."""
    rl = dish.rho_lip
    rho = np.r_[np.linspace(3.2, rl - 0.5, 160), np.linspace(rl - 0.49, rl + 0.26, 160)]
    th = np.linspace(np.pi / 2 - 1.15, np.pi / 2 + 1.15, 1600)
    R_, T_ = np.meshgrid(rho, th)
    x, y, _ = project(cam, dish.polar(R_, T_).reshape(-1, 3))
    f = LinearNDInterpolator(np.stack([x * w, y * h], 1), np.stack([(R_ * np.cos(T_)).ravel(), (R_ * np.sin(T_)).ravel()], 1))
    gx, gy = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    uv_ = f(gx, gy)
    return uv_[..., 0].astype(np.float32), uv_[..., 1].astype(np.float32)


def flat_view():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, lobes=LOBES)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.49), aperture_mm=16.0, focus_rho=dish.rho_lip - 1.6)
    print("sag", round(float(sag), 3), "rl", round(dish.rho_lip, 3), flush=True)
    w_, h_ = 2560, 1440
    lx, ly = frame_lut(dish, cam, w_, h_)
    ok = np.isfinite(lx)
    pxcm = float(os.environ.get("S49_PXCM", 320.0))
    rl = dish.rho_lip
    x0, x1, y0, y1 = float(lx[ok].min()) - 0.05, float(lx[ok].max()) + 0.05, float(ly[ok].min()) - 0.05, float(ly[ok].max()) + 0.05
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    X, Y = np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    F = fields(X, Y, pxcm, rl)
    col = F["col"] * (1 - F["wire"][..., None] * (1 - np.array([0.54, 0.48, 0.38], np.float32)))  # gamma alone makes the flat gold pale: set by eye to the wire in the old cand
    col = col * (1 + 0.1 * F["glass"])[..., None]

    # flat only: the stem as polished gilt, with a form and a lamp above, set to the lip's colours by eye. The render will do this for itself
    h_t = stem_form(F["gfull"], pxcm)
    gy, gx = np.gradient(h_t, 1.0 / pxcm)
    nz = 1.0 / np.sqrt(1 + gx * gx + gy * gy)
    nx_, ny_ = -gx * nz, -gy * nz
    lt = np.array([-0.2, 0.62, 0.76])
    hv = (lt + [0, 0, 1]) / np.linalg.norm(lt + [0, 0, 1])
    diff = np.clip(nx_ * lt[0] + ny_ * lt[1] + nz * lt[2], 0, 1)
    spec = np.clip(nx_ * hv[0] + ny_ * hv[1] + nz * hv[2], 0, 1) ** 70
    swell = rank(fbm(X.shape, pxcm, 0.3, 1.5, 2.4, SEED + 50))
    base = np.array([0.46, 0.29, 0.08], np.float32)
    lit = base * (0.22 + 0.95 * diff * (0.75 + 0.5 * swell))[..., None] + np.array([1.0, 0.86, 0.58], np.float32) * (0.85 * spec * (0.5 + 0.7 * swell))[..., None]
    gsh = F["gm"][..., None]
    col = col * (1 - gsh) + lit * gsh
    black = 0.0022  # the air behind, darker than the room's grey above the arc
    col = col * (1 - F["void"])[..., None] + black * F["void"][..., None]

    mx = (np.nan_to_num(lx, nan=-1e3) - x0) * pxcm - 0.5
    my = (np.nan_to_num(ly, nan=-1e3) - y0) * pxcm - 0.5
    fr = cv2.remap(col.astype(np.float32), mx, my, cv2.INTER_AREA if pxcm < 200 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    # the lip and the room are the old cand's own rendered pixels, same camera: the enamel is the only flat thing here. Read only
    old = cv2.imread(os.path.join(d, "cand_huahui.jpg"))
    if old is None or old.shape[:2] != (h_, w_):
        raise SystemExit("s49_juancao: needs out/v2/s49_falang/cand_huahui.jpg at 2560x1440 for the lip")
    # a few of its old leaves reach onto the lip's inner edge: anything there not gold is filled in from the gold around it
    rr0 = np.nan_to_num(np.hypot(lx, ly), nan=99.0)
    bg = old.astype(np.float32)
    notgold = (((bg[..., 1] > bg[..., 2] * 0.95) | (bg[..., 0] > bg[..., 2] * 0.9)) & (bg.max(-1) > 40) & (rr0 < rl - 0.05)).astype(np.uint8)
    sat = (bg[..., 2] - bg[..., 0]) / np.maximum(bg[..., 2], 1.0)  # orange, too saturated for the lip's worn gilt
    notgold = notgold | ((sat > 0.72) & (rr0 < rl - 0.05) & (bg[..., 2] > 60)).astype(np.uint8)
    old = cv2.inpaint(old, cv2.dilate(notgold, np.ones((5, 5), np.uint8)), 5, cv2.INPAINT_TELEA)
    old = (old[..., ::-1].astype(np.float32) / 255.0) ** 2.2
    rr = np.hypot(lx, ly)
    keep = np.nan_to_num(sstep(rl - 0.40, rl - 0.34, rr), nan=1.0)[..., None]
    keep = np.where(ok[..., None], keep, 1.0)
    fr = fr * (1 - keep) + old * keep
    im = np.clip(fr, 0, 1) ** (1 / 2.2)
    im = (im[..., ::-1] * 255 + 0.5).astype(np.uint8)
    p = os.path.join(d, "juancao_flat.jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(p, im.shape, "cells", F["n"], flush=True)
    small = os.environ.get("S49_SMALL")
    if small:
        cv2.imwrite(small, cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 90])


def crop(dish, X, Y, extra=0.5):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def build(dish, X, Y, pxcm):
    """As s49_falang.py's build(): each cell its level, dome, meniscus and tilt, the stoned polish, the beaten body. Added: the stem, a half-round rod with the lip's dents and the lip's finish."""
    shape = X.shape
    rl = dish.rho_lip
    F = fields(X, Y, pxcm, rl, clouds=True)
    wire, edge, d_in, level, lab, pits, rim, gm = F["wire"], F["edge"], F["d_in"], F["level"], F["lab"], F["pits"], F["rim"], F["gm"]
    n = F["n"]
    inv = lab.ravel()
    rt = np.random.default_rng(SEED + 20)
    tx, ty = rt.normal(0, 0.02, n).astype(np.float32), rt.normal(0, 0.02, n).astype(np.float32)
    area = np.bincount(inv, minlength=n) + 1.0
    cx = (np.bincount(inv, X.ravel(), minlength=n) / area).astype(np.float32)
    cy = (np.bincount(inv, Y.ravel(), minlength=n) / area).astype(np.float32)
    tilt = np.clip(tx[lab] * (X - cx[lab]) + ty[lab] * (Y - cy[lab]), -0.006, 0.006)
    dome = 1.0 - np.exp(-d_in / 0.045)
    groove = np.exp(-d_in / 0.012)
    wave = fbm(shape, pxcm, 0.05, 0.35, 2.4, SEED + 21)
    hollow = fbm(shape, pxcm, 0.3, 1.6, 2.8, SEED + 27)
    enamel = -0.0095 - 0.0016 * np.clip(level, -2, 2) + 0.0045 * dome - 0.0032 * groove + tilt + 0.00075 * wave + 0.0022 * hollow - np.minimum(pits, 0.014)
    wire_top = 0.0014 + 0.0040 * np.sqrt(np.maximum(1 - edge**2, 0)) + 0.0005 * fbm(shape, pxcm, 0.02, 0.2, 2.0, SEED + 22)
    h = enamel * (1 - wire) + wire_top * wire
    dents = 0.0022 * fbm(shape, pxcm, 0.2, 1.2, 2.6, SEED + 23) + 0.006 * fbm(shape, pxcm, 0.6, 3.0, 2.8, SEED + 28)
    h = h * (1 - gm) + gm * (0.75 * stem_form(F["gfull"], pxcm) + 0.6 * dents)
    h = h * (1 - rim) + rim * dents
    h = h + 0.008 * fbm(shape, pxcm, 1.6, 6.0, 3.4, SEED + 24)
    scratch = rank(fbm(shape, pxcm, 0.003, 0.02, 1.2, SEED + 25))
    pit = F["pit"]
    solid = np.maximum(rim, gm)  # the lip and the stem: one finish
    gilt = np.maximum(wire, solid)
    rough = (0.2 + 0.1 * F["cloud"] + 0.04 * scratch + 0.4 * pit) * (1 - gilt) + (0.2 + 0.1 * scratch + 0.14 * F["wear"]) * wire * (1 - solid) + (0.13 + 0.12 * F["wear2"]) * solid
    metal = 0.94 * gilt
    coat = 0.85 * (1 - gilt) * (1 - pit)
    crough = 0.075 + 0.075 * rank(hollow) + 0.03 * scratch
    return dish.surface(X, Y, h), np.clip(F["col"], 0, 1).astype(np.float32), np.clip(rough, 0.03, 1).astype(np.float32), metal.astype(np.float32), coat.astype(np.float32), crough.astype(np.float32), F["void"], F["glass"]


def render(q):
    """The old plate's scene, value for value (s49_falang.py main)."""
    global RENDER_GLAZE
    RENDER_GLAZE = True
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, lobes=LOBES)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.49), aperture_mm=16.0, focus_rho=dish.rho_lip - 1.6)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 350.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.05))
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    P, C, Ro, Me, Co, Cr, Vo, Gl = build(dish, X, Y, pxcm)
    npz = os.path.join(d, f"mesh.juancao.{q}.npz")  # the old plate's mesh.*.npz stay
    np.savez(npz, P=P, col=C, rough=Ro, metal=Me, coat=Co, crough=Cr, void=Vo, glass=Gl)

    def wall(rh, th):
        return dish.polar(np.array(rh), th), dish.normal(np.array(rh * np.cos(th)), np.array(rh * np.sin(th)))

    pf, nf = wall(dish.rho_lip - 1.6, np.pi / 2)
    sheen, _ = reflect_light_loc(pf, nf, cam, 130.0)
    pw, nw = wall(dish.rho_lip - 2.4, np.pi / 2 - 0.55)
    lw, _ = reflect_light_loc(pw, nw, cam, 120.0)
    A = dish.polar(np.array(dish.rho_lip), np.pi / 2)
    scene = {
        "camera": cam,
        "meshes": [
            {
                "name": "plate",
                "npz": npz,
                "shader_py": os.path.join(os.path.dirname(os.path.abspath(__file__)), "falang_shader.py"),
                "params": {"through": 0.12, "skin": 0.1},
            }
        ],
        "lights": [
            {"type": "gradient", "name": "sheen", "loc": sheen.tolist(), "target": pf.tolist(), "size": [420, 300], "sigma": [150, 60], "L": 0.34, "rgb": [1.0, 0.99, 0.97]},
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": pw.tolist(), "size": [150, 90.0], "sigma": [46, 22], "L": 1.5, "rgb": [1.0, 0.98, 0.96]},
            {"name": "key", "loc": [-18.0, 42.0, 90.0], "target": [0, 1, 1], "size": [50, 50], "watts": 30000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
            {"name": "spark", "loc": [-14.0, 30.0, 88.0], "target": [0, 1, 1], "size": [22, 22], "watts": 1500, "rgb": [1.0, 0.97, 0.92], "hide_in_diffuse": True},
            {"name": "fill", "loc": [14.0, -40.0, 85.0], "target": [0, 3, 1], "size": [60, 60], "watts": 7000, "rgb": [0.97, 0.99, 1.0], "hide_in_gloss": True},
            {"name": "behind", "loc": [-3.0, 5.0, -16.0], "target": [0.0, 5.0, 0.0], "size": [26, 16], "watts": 9000.0, "rgb": [1.0, 0.93, 0.82], "hide_in_gloss": True},
            {"name": "lip", "loc": (A + [0.0, 34.0, 26.0]).tolist(), "target": A.tolist(), "size": [70, 6], "watts": 22000, "rgb": [1.0, 0.96, 0.9]},
        ],
        "env": {"window": 2.2, "win_az": -30.0, "win_el": 38.0, "win_w": 30.0, "win_h": 34.0, "strip": 0.7, "ceil": 0.32, "wall": 0.06},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": 0.4, "seed": 49},
        "world": [0.0, 0.0, 0.0],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 4,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }
    shoot(NAME, scene, q, tag="cand" if q == "final" else f"juancao_{q}", develop={"exposure": 0.0, "contrast": 1.26, "saturation": 1.08, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "glare": 0.004, "vignette": 0.2})


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else ""
    if q == "flat":
        flat_view()
    elif q in ("preview", "mid", "final"):
        if os.environ.get("GEWU_MOVE"):
            raise SystemExit("s49_juancao: no motion here yet")
        render(q)
    else:
        raise SystemExit("s49_juancao: flat | preview | mid | final")


if __name__ == "__main__":
    main()
