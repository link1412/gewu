"""缠枝 (scrolling vine) ornament for cloisonne, in flat cm around a centre: reusable by any dish or by a jar's flattened shoulder.

    S = Sheet()
    medallion(S, rng, R)                                the centre, radial
    scroll_band(S, rng, rho, n, Rh, schemes, limit)     a closed vine that swings outside one head and inside the next, a branch closing the circle round each head; leaves and tendrils fill what is left
    S.items                                             painter's order: ("w", polyline) and ("s", polygon, ramp name, origin, axis angle, length)

Written after looking closely at ref/falang/met40766 (foliate dish, early 15th c.), ref/cloisonne/cloisonne_cma_153760 (mandala base, early 1400s), ref/falang/met40756. What those pieces do, read by eye, not measured:
1. Order: a medallion at the centre, then rings; every head looks out from the middle (or the bottom of its panel), so the piece is radial as a whole and hand-drawn in each part.
2. The vine: one thin wire, never broken, that swings in S-curves; each head sits in the belly of a swing and a branch closes the circle round it. The eye reads circles linked together.
3. Heads: not many colours in one head, three at most. Outer petals are many (10-14), short, each with a lobed tip and a small gold curl inside; a much simpler heart of three to five bold shapes in other colours (often unsymmetrical on the Ming pieces).
4. Leaves: a narrow base opening into rounded lobes that hook back (not a notched oak leaf). Near-black green, the tip often running into yellow or red. They are half the size of a head, and they, with the tendrils, make up the density. The turquoise still shows through about half the area.
5. Palette: turquoise ground is the main colour; brick red, mustard yellow, lapis and white; dark green. No pink.
6. Colour in a petal: mostly one enamel on Ming pieces, but enamels do run into each other. The ramps here (three stops from base to tip) go beyond them on the brief's request, nearer to the shaded Qing cells (met40756's clouds).
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

    def __init__(self, extent=9.0, cells=40):
        self.items = []
        self.extent, self.cells = extent, cells
        self.occ = np.zeros((int(2 * extent * cells), int(2 * extent * cells)), np.uint8)

    def _px(self, p):
        return np.round((np.asarray(p) + self.extent) * self.cells).astype(np.int32)

    def shape(self, poly, ramp, o=None, ang=0.0, L=1.0, mark=True):
        self.items.append(("s", poly, ramp, np.asarray(poly.mean(0) if o is None else o, float), float(ang), float(L)))
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

    def wire(self, path, mark=False):
        self.items.append(("w", np.asarray(path)))
        if mark:
            self.mark_line(path)


def head(S, rng, c, R, face, scheme):
    """A fan-lotus (番莲) seen from the front: many outer petals, each with its curl; a tier of a second colour; a heart of few, bold shapes, a little off centre as on the old pieces. `face` is the angle it looks towards; the heart's asymmetry follows it."""
    c = np.asarray(c, float)
    outer, mid, h1, h2, dot = scheme
    n = rng.integers(9, 12)
    a0 = face + rng.uniform(0, 0.3)
    angs = a0 + (np.arange(n) + rng.normal(0, 0.08, n)) * 2 * np.pi / n
    for i in rng.permutation(n):
        a = angs[i]
        L = R * rng.uniform(0.76, 0.88)
        w = R * rng.uniform(0.32, 0.38)
        b = c + 0.2 * R * uv(a)
        S.shape(place(petal_q(LOBED, rng, skew=rng.normal(0, 0.16), jitter=0.04), b, a, L, w), outer, b, a, L)
        # the gold curl inside each petal
        s = rng.choice([-1, 1])
        r_ = w * rng.uniform(0.22, 0.3)
        S.wire(spiral(b + L * 0.6 * uv(a) + s * 0.12 * w * uv(a + np.pi / 2), r_, r_ * 0.18, a + rng.uniform(0, 3), s * rng.uniform(1.2, 1.6), 30))
    m = int(rng.integers(5, 7))
    for i in rng.permutation(m):
        a = a0 + 0.3 + (i + rng.normal(0, 0.08)) * 2 * np.pi / m
        L = R * rng.uniform(0.42, 0.48)
        b = c + 0.1 * R * uv(a)
        S.shape(place(petal_q(HEART, rng, skew=rng.normal(0, 0.14), jitter=0.03), b, a, L, R * 0.27), mid, b, a, L)
    # the heart: a bud that looks where the head looks, one tall petal, two at its sides, white at its foot. Not a whirl: a whirl of three reads as a pansy
    off = c - 0.1 * R * uv(face)
    for k, da, Lr, wr, col_ in ((-1, -0.62, 0.44, 0.16, h1), (1, 0.62, 0.44, 0.16, h1), (0, 0.0, 0.56, 0.17, h2)):
        a = face + da + rng.normal(0, 0.05)
        L = R * Lr * rng.uniform(0.94, 1.06)
        S.shape(place(petal_q(POINT, rng, skew=-k * rng.uniform(0.2, 0.45), jitter=0.025), off, a, L, R * wr), col_, off, a, L)
    S.shape(place(petal_q(ROUNDED, rng, jitter=0.02), off - 0.04 * R * uv(face), face + np.pi, 0.15 * R, 0.13 * R), dot, off, face + np.pi, 0.15 * R)
    S.mark(place(np.stack([np.cos(np.linspace(0, 6.3, 30)), np.sin(np.linspace(0, 6.3, 30))], 1), c, 0.0, 0.95 * R, 0.95 * R))


def leaf(S, rng, p, ang, L, side, ramp=None):
    """A leaf (如意叶) on a short curved spine, with a curl in one lobe, and a coloured tip on some."""
    ramp = ramp or rng.choice(["grn", "grny", "grnr", "tl"], p=[0.5, 0.26, 0.1, 0.14])
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
    s = side
    r_ = L * rng.uniform(0.09, 0.13)
    S.wire(spiral(p + 0.32 * L * uv(ang) + s * 0.3 * L * wide * uv(ang + np.pi / 2), r_, r_ * 0.25, ang + rng.uniform(0, 3), s * 1.2, 22))
    if rng.random() < 0.7:
        x = np.linspace(0.05, rng.uniform(0.5, 0.62), 10)
        S.wire(place(np.stack([x, side * 0.05 * np.sin(x * 4)], 1), p, ang, L, L))
    return True


def bud(S, rng, p, ang, s, ramp="red", cup="grn"):
    p = np.asarray(p, float)
    S.shape(place(petal_q(HEART, rng, jitter=0.02), p, ang, s, 0.46 * s), ramp, p, ang, s)
    for k in (-1, 1):
        a = ang + k * rng.uniform(0.55, 0.8)
        S.shape(place(petal_q(POINT, rng, skew=-k * 0.3, jitter=0.02), p, a, s * 0.56, 0.2 * s), cup, p, a, s * 0.56)


def tendril(S, rng, p, a, side, r):
    S.wire(np.vstack([p, spiral(p + r * 1.15 * uv(a + side * np.pi / 2), r, r * 0.18, a - side * np.pi / 2, side * rng.uniform(1.0, 1.5), 30)]), mark=True)


def _breathe(v, rng, amp):
    """The hand: a slow wander along a line, so that no two swings are alike."""
    sl = path_len(v)
    dv = np.gradient(v, axis=0)
    nv = np.stack([-dv[:, 1], dv[:, 0]], 1) / (np.hypot(*dv.T)[:, None] + 1e-9)
    w = amp * (np.sin(sl * 1.7 + rng.uniform(0, 6)) + 0.6 * np.sin(sl * 3.1 + rng.uniform(0, 6)))
    return v + nv * w[:, None]


def scroll_band(S, rng, rho, n, Rh, schemes, lo, hi, leaf_L=0.72, density=1.0):
    """A closed ring of n heads (n even) at radius rho, of radius Rh, between radii lo and hi. The main vine goes round outside one head and inside the next. A branch off it closes the circle round each head and ends in its back."""
    assert n % 2 == 0
    th0 = rng.uniform(0, 1)
    heads = []
    for k in range(n):
        a = th0 + 2 * np.pi * k / n + rng.normal(0, 0.012)
        r = rho + rng.normal(0, 0.05)
        heads.append((r * uv(a), Rh * rng.uniform(0.94, 1.06), a))
    Rl = 1.2
    pts = []
    for k, (c, R, a) in enumerate(heads):
        s = 1.0 if k % 2 == 0 else -1.0  # outside this head, inside the next
        rl = R * Rl
        for f in (-1.0, -0.5, 0.0, 0.5, 1.0):
            pts.append(c + rl * uv(a + f * 1.42 if s > 0 else a + np.pi - f * 1.42))
    v = catmull(pts, 10, closed=True)
    v = np.vstack([v, v[:1]])
    v = _breathe(v, rng, 0.022)
    S.wire(v, mark=True)
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
        br = catmull(np.vstack([start, arc, c + R * 0.6 * uv(b0 - rot * 3.6)]), 8)
        S.wire(_breathe(br, rng, 0.012), mark=True)
        stems.append(br)
    # heads over the vines
    for k, (c, R, a) in enumerate(heads):
        head(S, rng, c, R, a, schemes[k % len(schemes)])
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
            if in_band(tip, 0.04) and leaf(S, rng, st[i], b, L, side):
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
        stalk = catmull([q0, (q0 + e) / 2 + nm * Ls * rng.uniform(-0.2, 0.2), e], 6)
        if S.overlap(place(np.array([[0.2, 0.05], [0.95, 0.05], [0.95, -0.05], [0.2, -0.05]]), q0, a, Ls, 1.0)) > 0.25:
            continue
        s_ = rng.choice([-1, 1])
        ok = leaf(S, rng, e, a + s_ * rng.uniform(0.0, 0.5), float(np.clip(rng.lognormal(np.log(leaf_L * 0.72), 0.25), 0.26, 0.72)), s_)
        if not ok:
            if rng.random() < 0.4:
                tendril(S, rng, e, a, s_, rng.uniform(0.07, 0.13))
            else:
                continue
        S.wire(stalk, mark=True)
        allp = np.vstack([allp, stalk])
        side_shoots.append((e, a))
    for _ in range(int(30 * density) if side_shoots else 0):
        p, a = side_shoots[rng.integers(0, len(side_shoots))]
        s_ = rng.choice([-1, 1])
        e = p + 0.42 * uv(a + s_ * 1.0)
        if in_band(e, 0.1) and S.overlap(place(np.array([[-0.14, -0.14], [0.14, -0.14], [0.14, 0.14], [-0.14, 0.14]]), e, 0)) < 0.1:
            S.wire(catmull([p, (p + e) / 2 + rng.normal(0, 0.03, 2), e], 6), mark=True)
            bud(S, rng, e, a + s_ * 1.0, rng.uniform(0.26, 0.34), rng.choice(["red", "red2", "cob", "yelr"]))
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
]


def design(rl, seed=49, band_w=0.86):
    """The whole dish to radius rl: medallion, two scroll bands separated by a double wire ring. Returns a Sheet."""
    rng = np.random.default_rng(seed)
    S = Sheet()
    rm = 0.235 * rl  # medallion
    lim = rl - band_w
    ring = 0.56 * rl
    medallion(S, rng, rm)
    # the double wire between the two bands
    th = np.linspace(-np.pi, np.pi, 1200)
    for r in (ring - 0.05, ring + 0.05):
        S.wire(np.stack([(r + 0.008 * np.sin(th * 3 + r)) * np.cos(th), (r + 0.008 * np.sin(th * 3 + r)) * np.sin(th)], 1), mark=True)
    # inner band
    scroll_band(S, rng, 0.5 * (rm + ring) + 0.05, 8, 0.75, SCHEMES, rm + 0.02, ring - 0.09)
    scroll_band(S, rng, 0.5 * (ring + lim), 12, 0.98, SCHEMES[1:] + SCHEMES[:1], ring + 0.09, lim - 0.06)
    return S
