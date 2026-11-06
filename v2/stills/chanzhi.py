"""缠枝 (scrolling vine) ornament for cloisonne, in flat cm around a centre: reusable by any dish or by a jar's flattened shoulder.

    S = Sheet()
    medallion(S, rng, R)                                the centre, radial
    scroll_band(S, rng, rho, n, Rh, schemes, limit)     a closed vine that swings outside one head and inside the next, a branch closing the circle round each head; leaves and tendrils fill what is left
    S.items                                             painter's order: ("w", polyline, pressure at start, at end) and ("s", polygon, ramp name, origin, axis angle, length, shift, scale, gain)

Written after looking closely at ref/falang/met40766 (foliate dish, early 15th c.), ref/cloisonne/cloisonne_cma_153760 (mandala base, early 1400s), ref/falang/met40756. What those pieces do, read by eye, not measured:
1. Order: a medallion at the centre, then rings; every head looks out from the middle (or the bottom of its panel), so the piece is radial as a whole and hand-drawn in each part.
2. The vine: one thin wire, never broken, that swings in S-curves; each head sits in the belly of a swing and a branch closes the circle round it. The eye reads circles linked together.
3. Heads: not many colours in one head, three at most. Outer petals are many (10-14), short, each with a lobed tip and a small gold curl inside; a much simpler heart of three to five bold shapes in other colours (often unsymmetrical on the Ming pieces).
4. Leaves: a narrow base opening into rounded lobes that hook back (not a notched oak leaf). Near-black green, the tip often running into yellow or red. They are half the size of a head, and they, with the tendrils, make up the density. The turquoise still shows through about half the area.
5. Palette: turquoise ground is the main colour; brick red, mustard yellow, lapis and white; dark green. No pink.
6. Colour in a petal: mostly one enamel on Ming pieces, but enamels do run into each other. The ramps here (three stops from base to tip) go beyond them on the brief's request, nearer to the shaded Qing cells (met40756's clouds).
The hand (second round: the curl in each petal, the same in every one, read as a pattern machine): each head has its own count of petals, its own lean, sometimes a three-quarter view, sometimes a profile. Marks inside petals are mixed and many petals have none. A line has pressure: heavier at the start, tapering along a branch, beads where the wire was stopped and soldered. A petal's shading is shifted and rescaled on its own. Branches leave the vine along its tangent, as a stroke would.
Nothing is copied: positions and shapes are generated, each petal perturbed separately. Sizes are ESTIMATES from these photographs.
"""

import numpy as np

# name: stops from base to tip, sRGB. By eye from the photographs above; the shaded ends are ours
RAMPS = {
    "red": [(92, 22, 18), (150, 40, 28), (204, 92, 66)],
    "red2": [(120, 30, 22), (168, 50, 34), (214, 120, 84)],
    "yel": [(176, 96, 18), (222, 164, 46), (244, 216, 126)],
    "yelr": [(214, 150, 40), (232, 176, 58), (190, 66, 34)],
    "cob": [(10, 14, 76), (22, 38, 130), (74, 110, 196)],
    "wht": [(146, 176, 200), (226, 228, 218), (250, 248, 238)],
    "whr": [(236, 234, 222), (246, 240, 228), (206, 120, 96)],
    "grn": [(6, 32, 26), (14, 54, 42), (40, 96, 68)],
    "grny": [(6, 32, 26), (16, 58, 44), (196, 176, 62)],
    "grnr": [(6, 32, 26), (16, 58, 44), (170, 56, 34)],
    "tl": [(8, 62, 66), (12, 92, 90), (56, 150, 136)],
}
# glass: what comes through, so these are the colours of light; deep in the middle of a cell. By eye, no reference measured
RAMPS.update(
    {
        "pl_red": [(150, 12, 10), (214, 34, 18), (250, 110, 50)],
        "pl_yel": [(220, 110, 8), (250, 176, 26), (255, 226, 110)],
        "pl_cob": [(10, 24, 150), (22, 66, 214), (70, 150, 250)],
        "pl_grn": [(6, 84, 44), (14, 136, 70), (110, 196, 80)],
        "pl_tl": [(4, 104, 110), (8, 160, 160), (90, 214, 190)],
        "pl_wht": [(240, 210, 150), (252, 236, 200), (255, 250, 236)],
    }
)
GROUND = ((8, 104, 166), (40, 150, 204))
BAND = ((10, 16, 92), (26, 44, 146))


def catmull(pts, n=14, closed=False):
    p = np.asarray(pts, float)
    m = len(p)
    if closed:
        idx = range(m)
        get = lambda i: p[i % m]
    else:
        p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
        m = len(p)
        idx = range(1, m - 2)
        get = lambda i: p[i]
    out = []
    for i in idx:
        p0, p1, p2, p3 = get(i - 1), get(i), get(i + 1), get(i + 2)
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t**3))
    if not closed:
        out.append(p[-2])
    return np.array(out)


def uv(a):
    return np.array([np.cos(a), np.sin(a)])


def place(q, p, ang, sx=1.0, sy=1.0):
    ca, sa = np.cos(ang), np.sin(ang)
    x, y = q[:, 0] * sx, q[:, 1] * sy
    return np.stack([p[0] + ca * x - sa * y, p[1] + sa * x + ca * y], 1)


def spiral(c, r0, r1, a0, turns, n=40):
    t = np.linspace(0, 1, n)
    r = r0 + (r1 - r0) * t**0.8
    a = a0 + 2 * np.pi * turns * t
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], 1)


def path_len(p):
    return np.r_[0.0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]


# unit shapes, base at the origin, tip on +x, half of them drawn: the other side mirrored then perturbed
LOBED = [(0, 0.2), (0.3, 0.56), (0.52, 0.86), (0.72, 1.0), (0.82, 0.66), (0.86, 0.44), (1.04, 0.0)]  # an outer petal, a shoulder, a dent, a point
ROUNDED = [(0, 0.2), (0.3, 0.72), (0.66, 1.0), (0.92, 0.66), (1.0, 0.0)]
HEART = [(0, 0.1), (0.34, 0.86), (0.72, 1.0), (0.98, 0.52), (0.84, 0.0)]
POINT = [(0, 0.26), (0.22, 0.7), (0.5, 1.0), (0.76, 0.66), (1.04, 0.0)]
# a leaf: narrow base, two rounded lobes hooking back and two smaller toward the tip
LEAF = [(0.0, 0.05), (0.12, 0.12), (0.2, 0.36), (0.1, 0.58), (0.22, 0.78), (0.42, 0.74), (0.47, 0.5), (0.53, 0.54), (0.66, 0.66), (0.8, 0.54), (0.78, 0.34), (0.9, 0.22), (1.03, 0.0)]


def petal_q(half, rng, skew=0.0, jitter=0.03):
    """A closed unit outline from one half: the sides differ, the tip leans; never two the same."""
    h = np.array(half, float)
    a = h + rng.normal(0, jitter, h.shape)
    b = h + rng.normal(0, jitter, h.shape)
    side = rng.uniform(0.88, 1.12)
    a[:, 1] *= side
    b[:, 1] *= -1.0 / side
    q = catmull(np.vstack([a, b[-2::-1]]), 8, closed=True)
    q[:, 1] += skew * q[:, 0] ** 2
    return q


class Sheet:
    """Painter's list, and a coarse occupancy map so that filler goes only where there is room."""

    def __init__(self, extent=9.0, cells=40, seed=1):
        self.items = []
        self.rng_hand = np.random.default_rng(seed)
        self.extent, self.cells = extent, cells
        self.occ = np.zeros((int(2 * extent * cells), int(2 * extent * cells)), np.uint8)

    def _px(self, p):
        return np.round((np.asarray(p) + self.extent) * self.cells).astype(np.int32)

    def shape(self, poly, ramp, o=None, ang=0.0, L=1.0, mark=True):
        r = self.rng_hand
        # the enameller's hand: this petal's shading starts a little earlier or later, runs shorter or longer, and the batch is a little lighter or darker
        self.items.append(("s", poly, ramp, np.asarray(poly.mean(0) if o is None else o, float), float(ang), float(L), float(r.normal(0, 0.11)), float(r.uniform(0.82, 1.2)), float(r.uniform(0.92, 1.08))))
        if mark:
            self.mark(poly)

    def mark(self, poly):
        import cv2

        cv2.fillPoly(self.occ, [self._px(poly)], 1)

    def mark_line(self, path, r=0.05):
        import cv2

        cv2.polylines(self.occ, [self._px(path)], False, 1, max(1, int(2 * r * self.cells)))

    def overlap(self, poly):
        """The fraction of this polygon that lands on something already there."""
        import cv2

        q = self._px(poly)
        x0, y0 = np.maximum(q.min(0), 0)
        x1, y1 = q.max(0) + 1
        if x1 <= x0 or y1 <= y0:
            return 1.0
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(m, [q - [x0, y0]], 1)
        n = m.sum()
        return float((m & self.occ[y0:y1, x0:x1]).sum()) / max(n, 1)

    def wire(self, path, mark=False, p0=1.0, p1=1.0):
        self.items.append(("w", np.asarray(path), float(p0), float(p1)))
        if mark:
            self.mark_line(path)


def _mark(S, rng, b, a, L, w):
    """What the wire does inside a petal: often nothing, a short vein, a fork, now and then a curl, and each curl its own. On the old pieces these vary a lot from flower to flower."""
    k = rng.choice(["none", "vein", "fork", "curl"], p=[0.34, 0.26, 0.14, 0.26])
    if k == "vein":
        x = np.linspace(rng.uniform(0.15, 0.3), rng.uniform(0.5, 0.8), 10)
        y = rng.normal(0, 0.05) + rng.normal(0, 0.05) * np.sin(x * 5)
        S.wire(place(np.stack([x, y * w / L * np.ones_like(x)], 1), b, a, L, L), p0=0.9, p1=0.55)
    elif k == "fork":
        q = rng.uniform(0.35, 0.5)
        x = np.linspace(0.18, q, 6)
        S.wire(place(np.stack([x, 0 * x], 1), b, a, L, L), p0=0.9, p1=0.7)
        for sg in (-1, 1):
            x2 = np.linspace(q, q + rng.uniform(0.18, 0.32), 6)
            S.wire(place(np.stack([x2, sg * (x2 - q) * rng.uniform(0.5, 1.0) * w / L], 1), b, a, L, L), p0=0.7, p1=0.5)
    elif k == "curl":
        s_ = rng.choice([-1, 1])
        r_ = w * rng.uniform(0.14, 0.34)
        turns = rng.uniform(0.7, 1.7)
        S.wire(spiral(b + L * rng.uniform(0.42, 0.72) * uv(a) + s_ * rng.uniform(0.0, 0.2) * w * uv(a + np.pi / 2), r_, r_ * rng.uniform(0.1, 0.4), a + rng.uniform(0, 6), s_ * turns, 30), p0=0.9, p1=0.55)


def head(S, rng, c, R, face, scheme):
    """A fan-lotus (番莲) from the front or three-quarters: many outer petals, a tier of a second colour, a bud in the heart that looks where the head looks. Each head its own count, lean and squeeze."""
    c = np.asarray(c, float)
    outer, mid, h1, h2, dot = scheme
    # three-quarter: squeezed along a direction of its own, its tiers slid that way
    turn = rng.uniform(0, 6.28)
    squash = rng.choice([1.0, rng.uniform(0.74, 0.92)], p=[0.45, 0.55])
    du = uv(turn)
    slide = 0.0 if squash == 1.0 else rng.uniform(0.04, 0.12)

    def tf(q):
        rel = q - c
        along = rel @ du
        return c + rel + np.outer(along * (squash - 1.0), du)

    def shp(q, ramp, o, a, L):
        S.shape(tf(q), ramp, tf(np.asarray(o)[None])[0], a, L)

    n = int(rng.integers(8, 14))
    a0 = face + rng.uniform(0, 1.0)
    angs = a0 + (np.arange(n) + rng.normal(0, 0.1, n)) * 2 * np.pi / n
    lean = rng.uniform(0.0, 0.14)  # one side of the head a little longer
    long_a = rng.uniform(0, 6.28)
    tmpl = LOBED if rng.random() < 0.7 else POINT
    wid = rng.uniform(0.3, 0.4) * (10.0 / n) ** 0.6
    n0 = len(S.items)
    for i in rng.permutation(n):
        a = angs[i]
        L = R * rng.uniform(0.74, 0.9) * (1.0 + lean * np.cos(a - long_a))
        w = R * wid * rng.uniform(0.88, 1.12)
        b = c + 0.2 * R * uv(a)
        shp(place(petal_q(tmpl, rng, skew=rng.normal(0, 0.18), jitter=0.045), b, a, L, w), outer, b, a, L)
    for i in rng.permutation(n):
        a = angs[i]
        _m0 = len(S.items)
        b = c + 0.2 * R * uv(a)
        L = R * 0.8
        _mark(S, rng, b, a, L, R * wid)
    tiers = rng.choice([1, 2], p=[0.7, 0.3])
    for t_ in range(tiers):
        m = int(rng.integers(5, 9))
        sc = 1.0 if t_ == 0 else 0.68
        for i in rng.permutation(m):
            a = a0 + 0.3 + t_ + (i + rng.normal(0, 0.1)) * 2 * np.pi / m
            L = R * rng.uniform(0.4, 0.5) * sc
            b = c + (0.1 * R + slide * R * (t_ + 1) * np.cos(a - turn)) * uv(a) + slide * R * (t_ + 1) * du * 0.5
            shp(place(petal_q(HEART if rng.random() < 0.7 else ROUNDED, rng, skew=rng.normal(0, 0.18), jitter=0.035), b, a, L, R * 0.27 * sc), mid if t_ == 0 else outer, b, a, L)
    # the heart: a bud that looks where the head looks, with its own proportions
    off = c - 0.1 * R * uv(face) + slide * R * du
    tall = rng.uniform(0.48, 0.62)
    sp = rng.uniform(0.46, 0.72)
    for k, da, Lr, wr, col_ in ((-1, -sp, tall * 0.8, 0.16, h1), (1, sp, tall * rng.uniform(0.7, 0.86), 0.16, h1), (0, 0.0, tall, 0.17, h2)):
        a = face + da + rng.normal(0, 0.08)
        L = R * Lr
        shp(place(petal_q(POINT, rng, skew=-k * rng.uniform(0.15, 0.5), jitter=0.03), off, a, L, R * wr), col_, off, a, L)
    if rng.random() < 0.75:
        shp(place(petal_q(ROUNDED, rng, jitter=0.03), off - 0.04 * R * uv(face), face + np.pi, 0.15 * R, 0.13 * R), dot, off, face + np.pi, 0.15 * R)
    S.mark(place(np.stack([np.cos(np.linspace(0, 6.3, 30)), np.sin(np.linspace(0, 6.3, 30))], 1), c, 0.0, 0.95 * R, 0.95 * R))


def side_head(S, rng, c, R, face, scheme):
    """A lotus in profile: a fan of petals opening towards `face`, a cup at its foot, a pointed heart. Between fronts, as on the Ming scrolls."""
    c = np.asarray(c, float)
    outer, mid, h1, h2, dot = scheme
    n = int(rng.integers(5, 8))
    spread = np.linspace(-1.5, 1.5, n) + rng.normal(0, 0.07, n)
    for i in np.argsort(-np.abs(spread)):
        a = face + spread[i]
        L = R * (1.05 - 0.2 * abs(spread[i]) + rng.normal(0, 0.05))
        w = R * rng.uniform(0.3, 0.38)
        S.shape(place(petal_q(LOBED, rng, skew=-np.sign(spread[i]) * rng.uniform(0.15, 0.5), jitter=0.04), c, a, L, w), outer, c, a, L)
        if rng.random() < 0.55:
            _mark(S, rng, c, a, L, w)
    for s_ in (-1, 1):
        a = face + s_ * rng.uniform(0.4, 0.62)
        L = R * rng.uniform(0.54, 0.66)
        S.shape(place(petal_q(HEART, rng, skew=-s_ * 0.3, jitter=0.03), c, a, L, R * 0.2), mid, c, a, L)
    L = R * rng.uniform(0.6, 0.72)
    S.shape(place(petal_q(POINT, rng, jitter=0.03), c, face + rng.normal(0, 0.05), L, R * 0.17), h2, c, face, L)
    for s_ in (-1, 1):
        a = face + np.pi + s_ * rng.uniform(1.0, 1.4)
        L = R * rng.uniform(0.28, 0.36)
        S.shape(place(petal_q(ROUNDED, rng, skew=s_ * 0.5, jitter=0.03), c, a, L, R * 0.13), h1, c, a, L)
    S.mark(place(np.stack([np.cos(np.linspace(0, 6.3, 30)), np.sin(np.linspace(0, 6.3, 30))], 1), c + 0.2 * R * uv(face), 0.0, 0.95 * R, 0.95 * R))


def leaf(S, rng, p, ang, L, side, ramps=("grn", "grny", "grnr", "tl")):
    """A leaf (如意叶) on a short curved spine, with a mark inside on some, and a coloured tip on some."""
    ramp = rng.choice(ramps, p=[0.5, 0.26, 0.1, 0.14][: len(ramps)] if len(ramps) == 4 else None)
    for scale in (1.0, 0.76, 0.56):  # what does not fit is tried smaller
        L_ = L * scale
        q = petal_q(LEAF, rng, skew=side * rng.uniform(0.3, 0.7) / max(rng.uniform(0.46, 0.56), 0.3), jitter=0.018)
        wide = rng.uniform(0.46, 0.56)
        poly = place(q, p, ang, L_, L_ * wide)
        if S.overlap(poly) < 0.16:
            L = L_
            break
    else:
        return False
    S.shape(poly, ramp, p, ang, L)
    if rng.random() < 0.34:
        s = side
        r_ = L * rng.uniform(0.07, 0.15)
        S.wire(spiral(p + rng.uniform(0.25, 0.42) * L * uv(ang) + s * 0.3 * L * wide * uv(ang + np.pi / 2), r_, r_ * 0.25, ang + rng.uniform(0, 6), s * rng.uniform(0.8, 1.5), 22), p0=0.8, p1=0.5)
    if rng.random() < 0.72:
        x = np.linspace(0.05, rng.uniform(0.42, 0.7), 10)
        S.wire(place(np.stack([x, side * 0.05 * np.sin(x * 4)], 1), p, ang, L, L), p0=0.8, p1=0.45)
    return True


def leaf_cup(cup, ramp):
    return "pl_grn" if ramp.startswith("pl_") else cup


def bud(S, rng, p, ang, s, ramp="red", cup="grn"):
    p = np.asarray(p, float)
    S.shape(place(petal_q(HEART, rng, jitter=0.02), p, ang, s, 0.46 * s), ramp, p, ang, s)
    for k in (-1, 1):
        a = ang + k * rng.uniform(0.55, 0.8)
        S.shape(place(petal_q(POINT, rng, skew=-k * 0.3, jitter=0.02), p, a, s * 0.56, 0.2 * s), leaf_cup(cup, ramp), p, a, s * 0.56)


def tendril(S, rng, p, a, side, r):
    S.wire(np.vstack([p, spiral(p + r * 1.15 * uv(a + side * np.pi / 2), r, r * rng.uniform(0.1, 0.3), a - side * np.pi / 2, side * rng.uniform(0.8, 1.7), 30)]), mark=True, p0=0.8, p1=0.4)


def _breathe(v, rng, amp):
    """The hand: a slow wander along a line, so that no two swings are alike."""
    sl = path_len(v)
    dv = np.gradient(v, axis=0)
    nv = np.stack([-dv[:, 1], dv[:, 0]], 1) / (np.hypot(*dv.T)[:, None] + 1e-9)
    w = amp * (np.sin(sl * 1.7 + rng.uniform(0, 6)) + 0.6 * np.sin(sl * 3.1 + rng.uniform(0, 6)))
    return v + nv * w[:, None]


def scroll_band(S, rng, rho, n, Rh, schemes, lo, hi, leaf_L=0.72, density=1.0, Rl=1.2, leaf_ramps=("grn", "grny", "grnr", "tl"), buds=("red", "red2", "cob", "yelr"), side_every=4):
    """A closed ring of n heads (n even) at radius rho, of radius Rh, between radii lo and hi. The main vine goes round outside one head and inside the next. A branch off it closes the circle round each head and ends in its back. Every `side_every`th head, about, is in profile."""
    assert n % 2 == 0
    th0 = rng.uniform(0, 1)
    heads = []
    for k in range(n):
        a = th0 + 2 * np.pi * k / n + rng.normal(0, 0.016)
        r = rho + rng.normal(0, 0.05)
        heads.append((r * uv(a), Rh * rng.uniform(0.9, 1.08), a))
    pts = []
    for k, (c, R, a) in enumerate(heads):
        s = 1.0 if k % 2 == 0 else -1.0  # outside this head, inside the next
        rl = R * Rl
        for f in (-1.0, -0.5, 0.0, 0.5, 1.0):
            pts.append(c + rl * uv(a + f * 1.42 if s > 0 else a + np.pi - f * 1.42))
    v = catmull(pts, 10, closed=True)
    v = np.vstack([v, v[:1]])
    v = _breathe(v, rng, 0.03)
    S.wire(v, mark=True, p0=1.15, p1=1.15)
    stems = [v]
    for k, (c, R, a) in enumerate(heads):
        s = 1.0 if k % 2 == 0 else -1.0
        # the branch leaves the vine at the crossing before this head and goes round the free side of it, closing in
        a_in = a + (np.pi if s > 0 else 0.0)  # the side of the head away from the main vine
        rot = -s
        arc = []
        b0 = a_in + rot * 1.5
        for t in np.linspace(0, 1, 9):
            rr = R * (1.2 - 0.14 * t)
            arc.append(c + rr * uv(b0 - rot * 3.0 * t))
        arc = np.array(arc)
        dv = np.hypot(*(v - arc[0]).T)
        start = v[np.argmin(dv)]
        # off the vine along its tangent, as one stroke
        iv = int(np.argmin(dv))
        tg = v[min(iv + 3, len(v) - 1)] - v[max(iv - 3, 0)]
        tg = tg / (np.hypot(*tg) + 1e-9)
        if tg @ (arc[0] - start) < 0:
            tg = -tg
        br = catmull(np.vstack([start, start + tg * 0.45 * np.hypot(*(arc[0] - start)), arc, c + R * 0.6 * uv(b0 - rot * 3.6)]), 8)
        S.wire(_breathe(br, rng, 0.016), mark=True, p0=1.05, p1=0.7)
        stems.append(br)
    # heads over the vines
    for k, (c, R, a) in enumerate(heads):
        sch = schemes[rng.integers(0, len(schemes))] if k % 3 == 2 else schemes[k % len(schemes)]  # not a strict round of colours
        if rng.random() < 1.0 / side_every:
            side_head(S, rng, c - 0.2 * R * uv(a), R, a + rng.normal(0, 0.25), sch)
        else:
            head(S, rng, c, R, a, sch)
    # filler, from the larger down: buds on short stalks, then leaves, then tendrils. Only where there is room
    def in_band(p, m=0.0):
        r = np.hypot(*p)
        return lo + m < r < hi - m

    side_shoots = []
    for st in stems:
        ln = path_len(st)
        t = rng.uniform(0.1, 0.4)
        side = rng.choice([-1, 1])
        while t < ln[-1] - 0.1:
            i = min(int(np.searchsorted(ln, t)), len(st) - 2)
            d = st[i + 1] - st[i]
            a = np.arctan2(d[1], d[0])
            side = side if rng.random() < 0.15 else -side
            L = float(np.clip(rng.lognormal(np.log(leaf_L), 0.2), 0.3, 0.86))
            b = a + side * rng.uniform(0.5, 1.0)
            tip = st[i] + L * uv(b)
            if in_band(tip, 0.04) and leaf(S, rng, st[i], b, L, side, leaf_ramps):
                side_shoots.append((st[i], a))
            t += rng.lognormal(np.log(0.34 / density), 0.3)
    # then fill what is open: any free place in the band gets a leaf on a stalk from the nearest stem, and that stalk can carry the next. Tendrils take what is too small for a leaf. Stops when nothing fits
    allp = np.vstack(stems)
    for _ in range(int(9000 * density)):
        rr_ = rng.uniform(lo + 0.1, hi - 0.1)
        ta = rng.uniform(-np.pi, np.pi)
        e = rr_ * uv(ta)
        if S.overlap(place(np.stack([np.cos(np.linspace(0, 6.3, 14)), np.sin(np.linspace(0, 6.3, 14))], 1), e, 0.0, 0.13, 0.13)) > 0.02:
            continue
        dd = np.hypot(*(allp - e).T)
        i = int(np.argmin(dd))
        Ls = float(dd[i])
        if Ls > 1.2 or Ls < 0.12:
            continue
        q0 = allp[i]
        a = np.arctan2(*(e - q0)[::-1])
        nm = np.array([-np.sin(a), np.cos(a)])
        iq = min(i, len(allp) - 2)
        tg = allp[iq + 1] - allp[iq]
        tg = tg / (np.hypot(*tg) + 1e-9)
        if tg @ (e - q0) < 0:
            tg = -tg
        stalk = catmull([q0, q0 + tg * Ls * 0.4, (q0 + e) / 2 + nm * Ls * rng.uniform(-0.15, 0.15), e], 6)  # leaves its stem along the stem, then bends away
        if S.overlap(place(np.array([[0.2, 0.05], [0.95, 0.05], [0.95, -0.05], [0.2, -0.05]]), q0, a, Ls, 1.0)) > 0.25:
            continue
        s_ = rng.choice([-1, 1])
        ok = leaf(S, rng, e, a + s_ * rng.uniform(0.0, 0.5), float(np.clip(rng.lognormal(np.log(leaf_L * 0.72), 0.25), 0.26, 0.72)), s_, leaf_ramps)
        if not ok:
            if rng.random() < 0.4:
                tendril(S, rng, e, a, s_, rng.uniform(0.07, 0.13))
            else:
                continue
        S.wire(stalk, mark=True, p0=0.9, p1=0.6)
        allp = np.vstack([allp, stalk])
        side_shoots.append((e, a))
    for _ in range(int(30 * density) if side_shoots else 0):
        p, a = side_shoots[rng.integers(0, len(side_shoots))]
        s_ = rng.choice([-1, 1])
        e = p + 0.42 * uv(a + s_ * 1.0)
        if in_band(e, 0.1) and S.overlap(place(np.array([[-0.14, -0.14], [0.14, -0.14], [0.14, 0.14], [-0.14, 0.14]]), e, 0)) < 0.1:
            S.wire(catmull([p, (p + e) / 2 + rng.normal(0, 0.03, 2), e], 6), mark=True)
            bud(S, rng, e, a + s_ * 1.0, rng.uniform(0.22, 0.36), rng.choice(buds))
    return heads


def medallion(S, rng, R):
    """The centre: 12 panels with an inset and a heart-shaped motif at the base; 12 framed red hearts; a whirl of petals. Each panel drawn separately. The structure is that of the old medallions (see top of file); the drawing is ours."""
    n = 12
    a0 = rng.uniform(0, 0.5)
    # 1. the panels, each bounded by its own wires; the inset in a second enamel
    for i in range(n):
        a = a0 + (i + rng.normal(0, 0.012)) * 2 * np.pi / n
        L = R * rng.uniform(0.63, 0.66)
        b = 0.38 * R * uv(a)
        S.shape(place(petal_q(LOBED, rng, jitter=0.012), b, a, L, R * 0.30), "red", b, a, L)
    for i in range(n):
        a = a0 + (i + rng.normal(0, 0.012)) * 2 * np.pi / n
        L = R * 0.46
        b = 0.42 * R * uv(a)
        S.shape(place(petal_q(HEART, rng, jitter=0.014), b, a, L, R * 0.19), "yel", b, a, L)
        c_ = 0.53 * R * uv(a + rng.normal(0, 0.012))
        S.shape(place(petal_q(HEART, rng, jitter=0.02), c_, a, R * 0.2, R * 0.095), "cob", c_, a, R * 0.2)
        S.wire(spiral(c_ + R * 0.1 * uv(a), R * 0.026, R * 0.006, a, 1.1, 18))
    # 2. the framed hearts
    a1 = a0 + np.pi / n
    for i in range(n):
        a = a1 + (i + rng.normal(0, 0.012)) * 2 * np.pi / n
        b = 0.2 * R * uv(a)
        S.shape(place(petal_q(ROUNDED, rng, jitter=0.012), b, a, R * 0.23, R * 0.135), "grn", b, a, R * 0.23)
        S.shape(place(petal_q(HEART, rng, jitter=0.014), b + 0.03 * R * uv(a), a, R * 0.16, R * 0.086), "red2", b, a, R * 0.16)
    # 3. the whirl
    for i in range(8):
        a = a0 + i * 2 * np.pi / 8 + rng.normal(0, 0.02)
        b = 0.015 * R * uv(a)
        S.shape(place(petal_q(ROUNDED, rng, skew=0.8, jitter=0.012), b, a, R * 0.2, R * 0.075), "cob" if i % 4 else "wht", b, a, R * 0.2)
    S.shape(place(petal_q(ROUNDED, rng, jitter=0.01), np.zeros(2), a0, R * 0.04, R * 0.04), "yel", np.zeros(2), a0, R * 0.05)
    S.mark(place(np.stack([np.cos(np.linspace(0, 6.3, 60)), np.sin(np.linspace(0, 6.3, 60))], 1), np.zeros(2), 0.0, R * 1.04, R * 1.04))


# four heads, restrained: each three colours at most
SCHEMES = [
    ("red", "yel", "cob", "wht", "yel"),
    ("yel", "red", "cob", "wht", "red"),
    ("wht", "red2", "cob", "yel", "red"),
    ("cob", "wht", "red", "yel", "wht"),
    ("red2", "wht", "cob", "yel", "yel"),
]
# the same in glass: fewer whites, the light does the rest
GLASS = [
    ("pl_red", "pl_yel", "pl_cob", "pl_wht", "pl_yel"),
    ("pl_cob", "pl_tl", "pl_red", "pl_wht", "pl_yel"),
    ("pl_yel", "pl_red", "pl_cob", "pl_wht", "pl_red"),
    ("pl_red", "pl_wht", "pl_cob", "pl_yel", "pl_yel"),
]


def design(rl, seed=49, pierce=(5.14, 7.18)):
    """The whole dish to radius rl: medallion, a scroll band in opaque enamel, then the pierced band (pierce = its inner and outer radius): gilt wire only, leaves and flowers in glass, air between. Returns a Sheet."""
    rng = np.random.default_rng(seed)
    S = Sheet(seed=seed + 100)
    lo, hi = pierce
    rm = 0.235 * rl
    medallion(S, rng, rm)
    # the two gilt rings that carry the pierced band: heavy
    th = np.linspace(-np.pi, np.pi, 1400)
    for r, pr in ((lo, 2.2), (hi, 2.2)):
        S.wire(np.stack([(r + 0.008 * np.sin(th * 3 + r)) * np.cos(th), (r + 0.008 * np.sin(th * 3 + r)) * np.sin(th)], 1), mark=True, p0=pr, p1=pr)
    scroll_band(S, rng, 0.5 * (rm + lo) + 0.02, 8, 0.95, SCHEMES, rm + 0.02, lo - 0.05, Rl=1.15)
    # the pierced band: the vine touches both rings at each swing, so it all hangs together. Fewer leaves: the air is the point
    Rl = 1.18
    Rp = (hi - lo) / 2.0 / Rl
    scroll_band(S, rng, 0.5 * (lo + hi), 14, Rp * 0.96, GLASS, lo + 0.03, hi - 0.03, Rl=Rl, leaf_L=0.56, density=0.42, leaf_ramps=("pl_grn", "pl_tl", "pl_grn", "pl_yel"), buds=("pl_red", "pl_cob", "pl_yel"), side_every=5)
    return S
