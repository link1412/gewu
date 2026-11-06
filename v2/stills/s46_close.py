"""Shot 22: a black lacquer dish inlaid in thin mother-of-pearl (薄螺钿), close: a magpie on a plum branch, the dish turning slowly under the lens; its far lip, with a silver edge, is the arc across the whole frame.

    python3 -I v2/stills/s46_luopan.py flat                    the design only, no render: out/v2/s46_luopan/flat.jpg
    python3 -I v2/stills/s46_luopan.py swatch                  the shell with its film thickness running from 100 to 900 nm left to right, lit as in the shot: out/v2/s46_luopan/swatch.jpg
    python3 -I v2/stills/s46_luopan.py [preview|mid|final]

A sea I proposed for this dish was turned down; this drawing was chosen over a palace rendered the same way. What the photographs in ref/luodian teach, mainly the Met's Yuan 梅鹊 dish 40256 (read by eye, scales are estimates):
- a flower is big white pieces of shell, one to a petal, with stamens engraved over them; a bird's wing is separate strips, and it is the bird that carries the colour, in blue and violet;
- the lacquer is left empty, black and deep, with long drying cracks; a ring of red lacquer round the picture, then strips of shell, then a ring of little florets;
- the wall has flower sprays on it whose small pieces flash green and violet;
- most of the pieces are dark and a few flash.
Magpies on plum (喜鹊登梅) is an old motif; this drawing is ours and copies no piece.

Close (the arc crosses the frame, sagitta about .14; the whole dish no longer shows): the picture was redrawn for what the frame holds. One bird and a few flowers placed by hand, and a shallower dish with a narrow wall, or the wall would fill the frame down to the bottom. Read at 100% off the same Met dish: the bird's hood is one big piece in which the colour flows; white shell is cream and glows, its grain running with the piece; lines are lengths of shell; the lacquer has long dry cracks.

The colour is computed in the render, not painted (nacre_shader.py): one thin film per point, the layers of each piece tilted its own way, so the pieces flash in turn as the dish turns. One film stands in for a real stack of layers; the thicknesses and the tilt are picked by eye, the thicknesses off the swatch.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from dishkit import Dish
from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import project, reflect_light_loc

NAME = "s46_luopan"
SEED = 46
HERE = os.path.dirname(os.path.abspath(__file__))
SHADER = os.path.join(HERE, "nacre_shader.py")
# 16 cm of frame on a 24 cm dish: the sagitta follows from it, the elevation is low enough that the picture is still read. The lens is at a macro lens's working distance, so that the near part of the dish grows and falls out of focus as it does in a real close-up.
W, EL, DIST = 16.0, 50.0, 80.0
APERTURE = 15.0  # mm: f/12 or so on this lens
FOCUS_RHO = 9.0  # the bird; the lip is 3 cm further along and the bottom of the frame 3 cm nearer
PXCM = 255.0  # mesh vertices per cm at final
APEX_Y = 0.476
RUN = "s46_luopan_take_c"  # the candidate's own folder on any machine: nothing here touches final.* or *_move_final, and "_take_" makes kit read this shot's move from looks.json
# shallower than the first dish, the wall narrow: at this distance the first one's wall filled the frame
PROFILE = [(7.0, -0.45), (7.6, -0.2), (10.0, 0.25), (11.4, 0.95), (12.0, 1.35), (12.1, 1.52), (11.92, 1.58), (11.35, 1.3), (10.75, 0.75), (10.3, 0.52), (9.6, 0.45), (5.0, 0.45), (0.0, 0.45)]
WELL = 10.0  # the line round the picture, cm
LOBES = dict(n=12, a=0.028, b=0.14, p=0.8, rho0=11.0)  # a foliate rim (葵口)
TURN = 10.0  # degrees the dish turns in the shot; the grid is built for all of it. Twice as close as the 14 degrees of the earlier version, so the same speed on the screen is about 10
WINDOW_RHO = 11.6  # where on the wall the window mirrors
KEY_TRAVEL = 22.0  # cm the key travels with it. At 50 its end of the travel fell into the mirror of the floor and the lacquer went milky

# film thickness in nm by the colour it gives at this camera, on the thin film of the shader (film IOR 2.2), read off the swatch (measured rgb there). The low orders, 170 to 350, are the saturated ones: gold 240, magenta 275, violet 295, blue 310, teal 325, green 345
SILVER, MAGENTA, GREEN, TEAL, VIOLET = 150.0, 272.0, 345.0, 325.0, 295.0
BLUE = 310.0
HOOD = 312.0  # the hood's middle: green at one side of it, violet at the other, it is the piece with room for the colour to run
PALE = ("petal", "bud", "belly", "ring", "center")  # white shell: what is left of the colour is a cast
DEV = {"exposure": 0.55, "contrast": 1.25, "saturation": 1.02, "black": 0.001, "grain": 1.2, "sharpen": 0.3, "halation": 0.012, "glare": 0.002, "vignette": 0.25}


SW_FILM = (150.0, 600.0)


def drift(p):
    """Pieces cut from one shell run on from each other: the colour goes slowly through magenta, green and teal across the picture."""
    x, y = float(p[0]), float(p[1])
    return 316.0 + 34.0 * np.sin(0.62 * x + 0.9 * np.sin(0.42 * y + 1.0) + 0.5) * np.cos(0.33 * y - 0.21 * x) + 10.0 * np.sin(1.4 * y + 0.8 * x)


def bark(rng, p):
    return float(drift(p) + rng.normal(0, 6.0)) if rng.uniform() > 0.1 else float(rng.choice([VIOLET, MAGENTA]))


def bezier(pts, n=200):
    """A smooth curve through control points (Catmull-Rom)."""
    p = np.array(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        t = np.linspace(0, 1, max(n // (len(p) - 3), 4), endpoint=False)[:, None]
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t**2 + (3 * b - a - 3 * c + d) * t**3))
    return np.vstack(out + [p[-2][None]])


def closed(pts, n=60):
    """A closed smooth outline through control points."""
    p = np.array(pts, float)
    return bezier(np.vstack([p[-1], p, p[0], p[1]]), n + 3 * n // len(p))[max(n // len(p), 1) : -max(n // len(p), 1)]


def band(path, w):
    """A strip along a polyline; w is its half-width, one value or one for each point."""
    path = np.array(path, float)
    t = np.gradient(path, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
    n = np.stack([-t[:, 1], t[:, 0]], 1) * np.reshape(w, (-1, 1))
    return np.concatenate([path + n, (path - n)[::-1]], 0)


def arclen(path):
    return np.r_[0.0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]


def line(out, path, w, step, rng, film, kind="line"):
    """A line as an inlayer makes it: lengths of shell, end to end, with a hair's gap. w may taper: (w0, w1)."""
    path = np.array(path, float)
    s = arclen(path)
    w0, w1 = (w, w) if np.isscalar(w) else w
    a = 0.0
    while a < s[-1] - 0.02:
        b = min(a + step * rng.uniform(0.7, 1.3), s[-1])
        u = np.linspace(a, max(b - 0.016, a + 0.01), 8)
        seg = np.stack([np.interp(u, s, path[:, 0]), np.interp(u, s, path[:, 1])], 1)
        wide = (w0 + (w1 - w0) * u / s[-1]) * rng.uniform(0.92, 1.08)
        out.append((band(seg, wide), kind, None, film(rng, seg[3])))
        a = b


def disc(c, r, n=18):
    th = np.linspace(0, 2 * np.pi, n + 1)[:-1]
    return np.stack([c[0] + r * np.cos(th), c[1] + r * np.sin(th)], 1)


def strap(p, ang, L, w, rng, tip=0.72, power=0.75):
    """A feather or a leaf from p along ang: outline, and its midrib for the graver."""
    t = np.linspace(0, 1, 18)
    half = w * np.sin(np.pi * t**tip) ** power
    bend = rng.normal(0, 0.05) * np.sin(np.pi * t) * L
    x = L * t
    pts = np.concatenate([np.stack([x, half + bend], 1), np.stack([x[::-1], (-half + bend)[::-1]], 1)], 0)
    c, s = np.cos(ang), np.sin(ang)
    rot = lambda q: np.stack([p[0] + c * q[:, 0] - s * q[:, 1], p[1] + s * q[:, 0] + c * q[:, 1]], 1)
    return rot(pts), rot(np.stack([x, bend], 1))


def round_petal(p, ang, L, w, rng):
    """A plum petal: broad, round, a shallow notch at its tip."""
    k = lambda: rng.uniform(0.94, 1.06)
    q = [(0.0, 0.0), (0.22 * L, 0.34 * w * k()), (0.62 * L, 0.54 * w * k()), (0.93 * L, 0.34 * w * k()), (0.98 * L * k(), 0.07 * w), (0.9 * L, -0.02 * w), (0.98 * L * k(), -0.09 * w), (0.92 * L, -0.36 * w * k()), (0.6 * L, -0.53 * w * k()), (0.22 * L, -0.34 * w * k())]
    q = closed(q, 48)
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([p[0] + c * q[:, 0] - s * q[:, 1], p[1] + s * q[:, 0] + c * q[:, 1]], 1)


def uv(a):
    return np.array([np.cos(a), np.sin(a)])


def blossom(out, c, r, rng):
    """An open flower: five pieces of white shell, and stamens engraved across them, each ending in a dot."""
    c = np.array(c, float)
    a0 = rng.uniform(0, 2 * np.pi)
    fl = lambda: float(drift(c + 2.0) + rng.normal(0, 16.0))
    for k in range(5):
        a = a0 + k * 2 * np.pi / 5 + rng.normal(0, 0.05)
        L = r * rng.uniform(0.92, 1.08)
        out.append((round_petal(c + uv(a) * r * 0.05, a, L, r * rng.uniform(0.92, 1.05), rng), "petal", None, fl()))
    eng = []
    for _ in range(int(rng.integers(8, 12))):
        a = rng.uniform(0, 2 * np.pi)
        tip = c + uv(a) * r * rng.uniform(0.28, 0.5)
        eng.append((np.array([c + uv(a) * r * 0.1, tip]), 120))
        eng.append((tip[None], 210))
    out.append((disc(c, r * 0.1, 9), "center", eng, float(rng.choice([TEAL, GREEN]))))


def half_open(out, c, ang, r, rng):
    """A flower seen from the side: three petals fanned from a dark calyx."""
    c = np.array(c, float)
    fl = float(drift(c + 2.0) + rng.normal(0, 16.0))
    for d in (-0.62, 0.62, 0.0):
        out.append((round_petal(c, ang + d, r * rng.uniform(0.9, 1.05), r * rng.uniform(0.8, 0.95), rng), "petal", None, fl + rng.normal(0, 8.0)))
    out.append((disc(c - uv(ang) * r * 0.05, r * 0.2, 8), "line", None, float(VIOLET + rng.normal(0, 10.0))))


def bud(out, c, r, rng):
    c = np.array(c, float)
    th = np.linspace(0, 2 * np.pi, 14)[:-1]
    out.append((np.stack([c[0] + r * np.cos(th) * rng.uniform(0.92, 1.0), c[1] + r * np.sin(th) * rng.uniform(0.92, 1.0)], 1), "bud", None, float(drift(c + 2.0) + rng.normal(0, 16.0))))


def bird(out, o, rot, s, flip, rng, tail=3.5):
    """A magpie in pieces, as a shell cutter makes it: long strips for the tail and the wing, a row of small ones for the coverts, the belly one white piece. In its own coordinates: unit about 1 cm, the head towards +x. The bird carries the colour."""
    o = np.array(o, float)
    c, si = np.cos(rot), np.sin(rot)

    def T(q):
        q = np.atleast_2d(np.array(q, float)) * np.array([flip, 1.0]) * s
        return o + np.stack([c * q[:, 0] - si * q[:, 1], si * q[:, 0] + c * q[:, 1]], 1)

    blue = lambda: float(rng.choice([GREEN, TEAL, BLUE, 302.0], p=[0.15, 0.35, 0.35, 0.15]) + rng.normal(0, 5.0))
    # the legs, before all of it
    for x_ in (0.12, -0.2):
        line(out, T([(x_, -0.55), (x_ - 0.02, -1.02)]), 0.022 * s, 0.6, rng, lambda r, p: float(r.normal(VIOLET, 8.0)))
        for toe in (-0.15, 0.03, 0.17):
            line(out, T([(x_ - 0.02, -1.02), (x_ + toe, -1.09)]), 0.016 * s, 0.3, rng, lambda r, p: float(r.normal(VIOLET, 8.0)))
    # the tail
    for ang, L, w in ((204.0, tail, 0.135), (211.0, tail * 0.86, 0.115), (197.0, tail * 0.74, 0.1)):
        # each tail feather is two or three lengths of shell butted end to end, each its own colour
        q, rib = strap(np.array([-0.82, -0.12]), np.radians(ang), L, w, rng, tip=0.92, power=0.38)
        nq = len(q) // 2
        cuts = [0] + sorted(int(c_) for c_ in rng.integers(5, nq - 4, 2)) + [nq - 1]
        hue = blue()
        for a_, b_ in zip(cuts[:-1], cuts[1:]):
            if b_ - a_ >= 2:
                out.append((T(np.vstack([q[a_ : b_ + 1], q[2 * nq - 1 - b_ : 2 * nq - a_]])), "feather", [(T(rib[max(a_, 1) : min(b_, nq - 2) + 1]), 90)], float(hue + rng.normal(0, 9.0))))
    # the belly: one white piece, flecked by the graver
    bl = closed([(1.05, 0.28), (0.98, -0.12), (0.5, -0.55), (-0.25, -0.64), (-0.85, -0.38), (-1.06, -0.12), (-0.4, 0.12), (0.5, 0.3)])
    eng = []
    for _ in range(46):
        x_, y_ = rng.uniform(-0.75, 0.85), rng.uniform(-0.52, 0.1)
        eng.append((T([(x_, y_), (x_ - 0.13, y_ - 0.05), (x_ - 0.26, y_ - 0.07)]), int(rng.uniform(40, 95))))
    out.append((T(bl), "belly", eng, float(drift(o) + rng.normal(0, 12.0))))
    # the back
    out.append((T(closed([(1.0, 0.62), (0.55, 0.58), (-0.1, 0.36), (-0.85, 0.02), (-1.08, -0.1), (-0.55, -0.04), (0.2, 0.08), (0.85, 0.24)])), "feather", None, blue()))
    # the wing: long strips laid side by side, a white bar across them
    for k in range(7):
        q, rib = strap(np.array([0.42 - 0.13 * k, 0.1 - 0.035 * k]), np.radians(190.0 + 3.0 * k), 2.05 - 0.13 * k, 0.125, rng, tip=0.84, power=0.42)
        out.append((T(q), "feather", [(T(rib[1:-1]), 180)], blue()))
    for k in range(5):
        q, _ = strap(np.array([0.3 - 0.2 * k, 0.04 - 0.05 * k]), np.radians(240.0 - 6.0 * k), 0.4 + 0.03 * k, 0.085, rng, tip=0.8, power=0.6)
        out.append((T(q), "petal", None, float(drift(o) + rng.normal(0, 12.0))))
    # the coverts: rows of small scales over the shoulder
    for row, (x0_, y0_, nn) in enumerate(((0.6, 0.32, 5), (0.46, 0.16, 5))):
        for k in range(nn):
            q, rib = strap(np.array([x0_ - 0.19 * k, y0_ - 0.04 * k]), np.radians(200.0 + 8.0 * row), 0.44, 0.1, rng, tip=0.78, power=0.6)
            out.append((T(q), "feather", [(T(rib[2:-3]), 120)], blue()))
    # the hood: head, nape and bib, one big piece of shell, as on the Met's bird, the colour running through it. The eye is a hole down to the lacquer with a line cut round it. The bill is short and stout
    hood = closed([(1.5, 0.68), (1.33, 0.9), (1.02, 0.97), (0.72, 0.82), (0.34, 0.56), (0.0, 0.34), (0.3, 0.12), (0.72, 0.0), (1.08, 0.14), (1.3, 0.34), (1.44, 0.48)])
    # short engraved strokes on the bib, following the feathers
    eng = [(T(disc((1.17, 0.72), 0.075, 14)), 130)]
    for _ in range(22):
        x_, y_ = rng.uniform(0.35, 1.2), rng.uniform(0.12, 0.42)
        eng.append((T([(x_, y_), (x_ - 0.1, y_ - 0.02), (x_ - 0.17, y_ - 0.06)]), 75))
    out.append((T(hood), "hood", eng, HOOD))
    out.append((T(disc((1.17, 0.72), 0.048, 12)), "hole", None, 0.0))
    out.append((T([(1.46, 0.73), (1.84, 0.6), (1.46, 0.49)]), "beak", [(T([(1.5, 0.61), (1.8, 0.6)]), 200)], VIOLET))


def spray(out, rho, th, rng):
    """A flower on the wall: a head of small petals, a scrolling stem each way with leaves and buds. These small pieces are the ones that flash in colour."""
    pos = lambda r_, t_: np.stack([r_ * np.cos(t_), r_ * np.sin(t_)], -1)
    hue = float(rng.choice([GREEN, TEAL, 450.0]))
    for sg in (-1.0, 1.0):
        t = np.linspace(0, 1, 40)
        stem = pos(rho + 0.42 * np.sin(t * 5.2 + rng.uniform(-0.3, 0.3)) * (1.0 - 0.3 * t), th + sg * (0.04 + 0.27 * t))
        line(out, stem, 0.019, 0.42, rng, lambda r, p: float(r.normal(VIOLET, 12.0)))
        for k in range(3, 38, 8):
            a = np.arctan2(*(stem[k + 1] - stem[k])[::-1]) + rng.choice([-1.0, 1.0]) * rng.uniform(0.5, 1.1)
            q, rib = strap(stem[k], a, rng.uniform(0.34, 0.56), rng.uniform(0.085, 0.13), rng)
            out.append((q, "leaf", [(rib[2:-3], 150)], float(rng.choice([GREEN, TEAL, MAGENTA, VIOLET], p=[0.4, 0.3, 0.15, 0.15]) + rng.normal(0, 8.0))))
    c = pos(np.array(rho), np.array(th))
    for ring_, (nn, L, w) in enumerate(((18, 0.56, 0.082), (11, 0.32, 0.07))):
        a0 = rng.uniform(0, 6.28)
        for k in range(nn):
            a = a0 + k * 2 * np.pi / nn
            q, rib = strap(c + uv(a) * (0.14 - 0.06 * ring_), a, L * rng.uniform(0.9, 1.08), w, rng, power=0.6)
            out.append((q, "leaf", [(rib[3:-4], 130)], float(hue + rng.normal(0, 16.0) if rng.uniform() > 0.12 else rng.choice([MAGENTA, VIOLET]))))
    eng = [(np.array([c + uv(a) * 0.17, c - uv(a) * 0.17]), 170) for a in np.linspace(0, np.pi, 5)[:-1]]
    out.append((disc(c, 0.17, 12), "bud", eng, float(GREEN + rng.normal(0, 20.0))))


def huaniao():
    """All the pieces, back to front: (polygon in flat cm, kind, what the graver cuts in it, film thickness). Placed by hand for the frame, which at the middle of the turn holds y from about 6 to the lip (rim mode prints where): the limb from lower left to upper right, the bird on it just right of the middle, a few flowers as company, and the sky at upper left left empty."""
    rng = np.random.default_rng(SEED)
    out = []

    def limb(pts, w0, w1, step=1.0):
        p_ = bezier(np.array(pts, float), 260)
        line(out, p_, (w0, w1), step, rng, bark)
        return p_

    main = limb([(-10.0, 3.0), (-7.2, 4.95), (-4.4, 5.7), (-1.4, 6.4), (1.45, 6.95), (4.0, 7.75), (6.3, 7.45), (9.0, 8.0)], 0.15, 0.04, 0.95)
    up = limb([(-1.4, 6.4), (-2.5, 7.2), (-2.2, 8.1), (-3.0, 9.3)], 0.07, 0.025, 0.7)
    rt = limb([(4.0, 7.75), (4.75, 8.3), (4.55, 9.05), (5.2, 9.5)], 0.06, 0.022, 0.65)
    lo = limb([(-7.2, 4.95), (-7.9, 5.9), (-7.3, 6.8)], 0.06, 0.024, 0.6)
    tw = limb([(6.3, 7.45), (7.1, 6.9), (8.0, 6.85)], 0.04, 0.02, 0.55)
    for p0, p1 in (((-4.4, 5.7), (-5.0, 6.5)), ((-2.3, 7.6), (-1.35, 8.35)), ((3.0, 7.4), (3.75, 6.75)), ((6.3, 7.45), (6.85, 8.35)), ((4.6, 8.75), (5.5, 8.65))):
        p0, p1 = np.array(p0), np.array(p1)
        m_ = (p0 + p1) / 2 + rng.normal(0, 0.06, 2)
        line(out, bezier([p0, m_, p1], 30), (0.03, 0.016), 0.5, rng, bark)

    # flowers, the white shell of the shot. Few and apart: the bird and the colour of the shell are the subject
    for c_, r in (((5.3, 9.0), 0.62), ((-3.05, 8.85), 0.6), ((-5.1, 6.75), 0.56), ((-7.25, 7.05), 0.5)):
        blossom(out, c_, r, rng)
    half_open(out, np.array([6.9, 8.4]), np.radians(62.0), 0.46, rng)
    half_open(out, np.array([-1.3, 8.4]), np.radians(38.0), 0.42, rng)
    for c_, r in (((3.8, 6.68), 0.14), ((8.05, 6.82), 0.13), ((5.55, 8.65), 0.11), ((-2.0, 7.55), 0.1), ((-6.4, 5.45), 0.12)):
        bud(out, c_, r, rng)
    bird(out, np.array([1.0, 8.2]), np.radians(14.0), 1.15, 1.0, rng, tail=3.2)

    # nothing of the picture runs past the line round it
    out.append((np.zeros((3, 2)), "clip", WELL - 0.03, 0.0))

    # the rings: strips of shell, a ring of florets beyond the red. The wall above them is left to the lacquer and the light
    def ring(r_, w, step, film):
        tt = np.linspace(0, 2 * np.pi, int(60 * r_) + 40)
        line(out, np.stack([r_ * np.cos(tt), r_ * np.sin(tt)], 1), w, step, rng, film, kind="ring")

    pale_ring = lambda r, p: float(drift(p) + r.normal(0, 14.0))
    ring(WELL, 0.036, 1.4, pale_ring)
    ring(WELL + 0.56, 0.036, 1.4, pale_ring)
    nn = int(2 * np.pi * (WELL + 0.86) / 0.42)
    for k in range(nn):
        a = 2 * np.pi * k / nn
        c = uv(a) * (WELL + 0.86)
        th = np.linspace(0, 2 * np.pi, 31)[:-1]
        rr = 0.105 * (1.0 + 0.2 * np.cos(5 * th + rng.uniform(0, 6)))
        out.append((np.stack([c[0] + rr * np.cos(th), c[1] + rr * np.sin(th)], 1), "leaf", None, float(rng.choice([GREEN, TEAL, MAGENTA, VIOLET, BLUE]) + rng.normal(0, 6.0))))
    return out


def flat_view():
    """The design alone. The render computes the colour: here only roughly how a silver piece reads."""
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    S, pxcm = 2000, 2000 / 26.0
    im = np.full((S, S, 3), 12, np.uint8)
    lam = np.array([620.0, 540.0, 460.0])
    ps = huaniao()
    yy, xx = np.mgrid[0:S, 0:S]
    rho = np.hypot(xx / pxcm - 13, 13 - yy / pxcm)
    for poly, kind, meta, F in ps:
        if kind == "clip":
            im[rho >= meta] = 12
            continue
        if kind == "hole":
            c_ = np.zeros(3)
        else:
            c_ = 0.55 + 0.45 * np.cos(4 * np.pi * 1.9 * F * 0.96 / lam)
        c_ = (0.3 * c_ + 0.7 * c_.mean()) * np.random.default_rng(int(F * 100) % 977 + len(poly)).uniform(0.5, 1.0)
        if kind in PALE:
            c_ = 0.6 * c_ + 0.4
        v = tuple(int(x) for x in (c_[::-1] * 235))
        toi = lambda q: np.round((np.atleast_2d(q) * [1, -1] + 13) * pxcm * 16).astype(np.int32)
        cv2.fillPoly(im, [toi(poly)], v, cv2.LINE_AA, 4)
        if isinstance(meta, list):
            for pts, val in meta:
                if len(pts) == 1:
                    cv2.circle(im, tuple(int(x) for x in toi(pts)[0]), 16, (20, 20, 20), -1, cv2.LINE_AA, 4)
                else:
                    cv2.polylines(im, [toi(pts)], False, (20, 20, 20), 1, cv2.LINE_AA, 4)
    cv2.circle(im, (S // 2, S // 2), int(12.1 * pxcm), (120, 120, 120), 2, cv2.LINE_AA)
    p = os.path.join(d, "flat.jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(p, "pieces", len(ps))


def grid_for_turn(dish, cam, pxcm, deg, n=700):
    """Flat coordinates of all of the dish that comes into the frame while it turns by deg, centred on the middle of the turn."""
    rho = np.linspace(0.0, dish.L, n)
    th = np.linspace(-np.pi, np.pi, 2 * n)
    R_, T_ = np.meshgrid(rho, th)
    fx, fy = R_ * np.cos(T_), R_ * np.sin(T_)
    keep = np.zeros(R_.shape, bool)
    for a in np.radians(np.linspace(-deg / 2, deg / 2, 5)):
        x, y, _ = project(cam, dish.polar(R_, T_ + a).reshape(-1, 3))
        x, y = x.reshape(R_.shape), y.reshape(R_.shape)
        keep |= (x > -0.05) & (x < 1.05) & (y > -0.05) & (y < 1.05)
    x0, x1, y0, y1 = fx[keep].min(), fx[keep].max(), fy[keep].min(), fy[keep].max()
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    print(f"dish grid {nx} x {ny} = {nx * ny / 1e6:.1f} M", flush=True)
    return np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)


def long_cracks(shape, pxcm, x0, y0, seed):
    """Lacquer dries in long cracks that run across the grain of the wood below: mostly one way, wandering, stopping."""
    ny, nx = shape
    rs = np.random.default_rng(seed)
    im = np.zeros(shape, np.uint8)
    for _ in range(170):
        x, y = rs.uniform(-13, 13), rs.uniform(-13, 13)
        a = rs.normal(0.03, 0.05)
        pts = [(x, y)]
        for _ in range(int(rs.integers(6, 42))):
            a = 0.8 * a + rs.normal(0.0, 0.07)
            x, y = x + 0.34 * np.cos(a), y + 0.34 * np.sin(a)
            pts.append((x, y))
        cv2.polylines(im, [np.round((np.array(pts) - [x0, y0]) * pxcm * 16).astype(np.int32)], False, int(rs.uniform(110, 255)), 1, cv2.LINE_AA, 4)
    return im.astype(np.float32) / 255.0


def build(dish, X, Y, pxcm, swatch=False):
    shape = X.shape
    ny, nx = shape
    x0, y0 = float(X[0, 0]) - 0.5 / pxcm, float(Y[0, 0]) - 0.5 / pxcm
    ps = huaniao()
    print("pieces", len(ps), flush=True)
    lab = np.zeros(shape, np.int32)
    rho = np.hypot(X, Y)
    # the hand: the whole drawing is out of true by a millimetre or so, slowly
    wx = cv2.GaussianBlur(np.random.default_rng(SEED + 40).normal(0, 1, (64, 64)).astype(np.float32), (0, 0), 3.0)
    wy = cv2.GaussianBlur(np.random.default_rng(SEED + 41).normal(0, 1, (64, 64)).astype(np.float32), (0, 0), 3.0)
    wx, wy = wx / wx.std(), wy / wy.std()

    def bent(poly):
        i_ = np.clip(((poly[:, 0] + 13) / 26 * 63).astype(int), 0, 63)
        j_ = np.clip(((poly[:, 1] + 13) / 26 * 63).astype(int), 0, 63)
        return poly + 0.05 * np.stack([wx[j_, i_], wy[j_, i_]], 1)

    toi = lambda q: np.round((bent(np.atleast_2d(q)) - [x0, y0]) * pxcm * 16).astype(np.int32)
    for i, (poly, kind, meta, _) in enumerate(ps, start=1):
        if kind == "clip":
            lab[rho >= meta] = 0
            continue
        cv2.fillPoly(lab, [toi(poly)], 0 if kind == "hole" else i, cv2.LINE_8, shift=4)

    # --- engraved afterwards: a line stops where its piece stops
    engrave = np.zeros(shape, np.uint8)
    for i, (poly, kind, meta, _) in enumerate(ps, start=1):
        if isinstance(meta, list):
            for pts, val in meta:
                if len(pts) == 1:
                    cv2.circle(engrave, tuple(int(x) for x in toi(pts)[0]), int(max(0.022 * pxcm, 1.0) * 16), int(val), -1, cv2.LINE_AA, 4)
                else:
                    cv2.polylines(engrave, [toi(pts)], False, int(val), max(int(0.011 * pxcm), 1), cv2.LINE_AA, 4)

    # --- each piece: gap at the edge, chipped corners, its own growth lines, its own film, its own tilt
    mask0 = (lab > 0).astype(np.uint8)
    edges = (lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))
    edge = np.clip(blur(edges.astype(np.float32), max(0.0035 * pxcm, 0.6)) * 2.2, 0, 1)
    chip = fbm(shape, pxcm, 0.05, 0.3, 2.2, SEED + 3)
    dist = cv2.distanceTransform(mask0, cv2.DIST_L2, 3).astype(np.float32) / pxcm
    shell = sstep(0.0, 0.006, dist + 0.0022 * chip - 0.001) * mask0
    n = len(ps) + 1
    rp = np.random.default_rng(SEED + 4)
    # the shell's grain runs along the piece, because that is how a cutter lays out a strip. phi is the direction across the grain
    phi = rp.uniform(0, np.pi, n).astype(np.float32)
    for i, (poly, kind, *_) in enumerate(ps, start=1):
        if kind not in ("clip", "hole") and len(poly) > 3:
            ev, vec = np.linalg.eigh(np.cov((poly - poly.mean(0)).T))
            if ev[1] > 1.6 * ev[0]:
                phi[i] = float(np.arctan2(vec[1, 0], vec[0, 0]) + rp.normal(0, 0.06))
    off = rp.uniform(0, 100, n).astype(np.float32)
    mean = np.r_[0.0, [p[3] for p in ps]].astype(np.float32)
    tone = rp.normal(0, 1, n).astype(np.float32)
    g = X * np.cos(phi[lab]) + Y * np.sin(phi[lab]) + off[lab]
    wob = 0.014 * fbm(shape, pxcm, 0.2, 1.2, 2.6, SEED + 5)  # the grain wanders a little; more than this and the flames curl into worms
    lines = np.sin(2 * np.pi * (g + wob) / 0.05)
    bands = fbm(shape, pxcm, 0.3, 1.8, 2.6, SEED + 6)
    fine = fbm(shape, pxcm, 0.012, 0.06, 1.2, SEED + 7)
    # abalone: the colour runs in narrow flames along the growth of the shell, and breaks from piece to piece. A chip is nearly one colour; only a large piece has room for the colour to run
    flame_noise = np.zeros(8192, np.float32)
    for amp_, sg in ((0.5, 3.0), (0.8, 9.0), (1.0, 26.0)):  # in steps of 0.01 cm
        one = cv2.GaussianBlur(rp.normal(0, 1, (8192, 1)).astype(np.float32), (0, 0), sg).ravel()
        flame_noise += amp_ * one / one.std()
    flame_noise /= flame_noise.std()
    flames = flame_noise[np.mod(((g + 1.5 * wob) / 0.01).astype(np.int64), 8192)]
    size = np.sqrt(np.bincount(lab.ravel(), minlength=n).astype(np.float32)) / pxcm
    # a large piece has room for the colour to run across it in broad patches as well as in flames: the hood especially
    flow = rank(fbm(shape, pxcm, 0.6, 2.4, 2.8, SEED + 33)) - 0.5
    film = mean[lab] + (3.0 + 9.0 * sstep(0.25, 1.0, size))[lab] * flames + (80.0 * sstep(0.5, 1.2, size))[lab] * flow + 3.0 * bands + 1.5 * lines + 0.6 * fine
    is_pale = np.r_[0.0, [float(p[1] in PALE or p[3] < 250.0) for p in ps]].astype(np.float32)[lab]
    # how much of a piece's light is coloured at all
    sat = (0.55 + 0.42 * rp.beta(2.2, 1.6, n))[lab].astype(np.float32) * (1.0 - 0.72 * is_pale)
    sat = sat * np.r_[1.0, [0.6 if p[1] == "line" else 0.82 if p[1] == "feather" else 1.0 for p in ps]].astype(np.float32)[lab]  # the branch: silver with a little colour, so the bird carries it
    # the layers of the shell tilt in a piece. A slow drift, as they are cut from one shell, and each its own
    slow = lambda sd: cv2.resize(cv2.GaussianBlur(np.random.default_rng(sd).normal(0, 1, (64, 64)).astype(np.float32), (0, 0), 5.0), (nx, ny), interpolation=cv2.INTER_CUBIC)
    sx, sy = slow(SEED + 30), slow(SEED + 31)
    tx_ = rp.normal(0, 0.1, n).astype(np.float32)
    ty_ = rp.normal(0, 0.1, n).astype(np.float32)
    tx = (tx_[lab] + 0.05 * sx / (sx.std() + 1e-6)) * shell * (1.0 - 0.25 * is_pale)
    ty = (ty_[lab] + 0.05 * sy / (sy.std() + 1e-6)) * shell * (1.0 - 0.25 * is_pale)
    # a piece is not optically flat: it comes from a curved shell, and its layers fall away a little towards its cut edge. The polished coat above stays flat. This is the soft light across a petal
    dp = cv2.distanceTransform(((lab > 0) & ~edges).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm
    dome = blur(sstep(0.0, 0.4, dp), max(0.03 * pxcm, 1.0))
    gy_, gx_ = np.gradient(dome)
    k_d = 0.026 * pxcm * shell * (0.35 + 0.65 * is_pale)  # about .065 of a slope at most, an estimate by eye against the Met's petals
    tx, ty = tx - k_d * gx_, ty - k_d * gy_
    # the growth of the shell undulates: the highlight on a piece breaks into silky streaks along its grain, and they slide as the dish turns. This, more than the hue, is what reads as shell. .05 by eye against the Met's hood and petals
    k_c = 0.035 * shell
    tx, ty = tx + k_c * flames * np.cos(phi[lab]), ty + k_c * flames * np.sin(phi[lab])
    # the base reflects about as strongly as the film (R about 14%), or the two do not interfere to any depth of colour. White shell is pale all through, and scatters
    body = 0.21 + 0.09 * sstep(-1.6, 1.6, tone[lab]) + 0.05 * sstep(-1.2, 1.2, flames) + 0.02 * sstep(-1, 1, bands)
    dome_p = blur(sstep(0.0, 0.3, cv2.distanceTransform(((lab > 0) & ~edges).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm), max(0.03 * pxcm, 1.0))
    # white shell is not one white: bands of the shell's growth run through each piece, and the pieces differ, so that a flower is cut from several places in a shell
    cloud = sstep(-1.2, 1.2, fbm(shape, pxcm, 0.25, 1.0, 2.6, SEED + 34))
    body = mix(body, (0.5 + 0.12 * sstep(-1.6, 1.6, tone[lab]) + 0.28 * cloud + 0.24 * sstep(-1.2, 1.2, flames) + 0.1 * sstep(-1, 1, bands) + 0.03 * lines) * (0.82 + 0.22 * dome_p), is_pale)
    body = body * np.r_[1.0, [0.5 if p[1] == "ring" else 1.0 for p in ps]].astype(np.float32)[lab]
    is_beak = np.r_[0.0, [float(p[1] == "beak") for p in ps]].astype(np.float32)[lab]
    body = body * (1.0 - 0.8 * is_beak)  # the bill is dark, as on the Met's bird
    sat = sat * (1.0 - 0.8 * is_beak)
    eng = blur(engrave.astype(np.float32) / 255.0, max(0.0025 * pxcm, 0.45))

    # --- lacquer
    wave = fbm(shape, pxcm, 0.6, 4.0, 3.0, SEED + 8)
    black = mix(color([0.0016, 0.0014, 0.0013]), color([0.0065, 0.0042, 0.003]), rank(wave) ** 2)
    # old lacquer goes thin and brown where it was handled, near the lip and in a slow patch or two
    rub = sstep(0.55, 0.9, rank(fbm(shape, pxcm, 0.5, 4.0, 2.6, SEED + 17))) * (0.06 + 0.94 * sstep(dish.rho_lip - 1.1, dish.rho_lip - 0.2, rho))
    black = mix(black, color([0.05, 0.022, 0.012]), 0.34 * rub)
    # the ring of red lacquer round the picture, darkened with age
    worn = 0.014 * fbm(shape, pxcm, 0.2, 0.9, 2.6, SEED + 18)  # a painted ring, worn at its edges, not a ruled one
    red = sstep(WELL + 0.06, WELL + 0.1, rho + worn) * sstep(WELL + 0.5, WELL + 0.46, rho + worn) * (0.72 + 0.28 * sstep(-0.8, 0.8, fbm(shape, pxcm, 0.1, 0.8, 2.8, SEED + 19)))
    black = mix(black, mix(color([0.11, 0.012, 0.008]), color([0.05, 0.008, 0.006]), rank(wave)), red)
    crk_l = fbm(shape, pxcm, 0.06, 0.6, 2.0, SEED + 14)
    crackle = sstep(0.016, 0.0, np.abs(crk_l)) * sstep(0.4, 0.75, rank(fbm(shape, pxcm, 0.6, 4.0, 2.4, SEED + 15)))
    drying = blur(long_cracks(shape, pxcm, x0, y0, SEED + 21), max(0.003 * pxcm, 0.5))
    scr = np.zeros(shape, np.uint8)
    rs = np.random.default_rng(SEED + 9)
    for _ in range(int(2.0 * nx * ny / pxcm**2)):
        p = np.array([rs.uniform(0, nx), rs.uniform(0, ny)])
        a = rs.uniform(0, np.pi)
        q = p + rs.lognormal(np.log(1.2), 0.6) * pxcm * np.array([np.cos(a), np.sin(a)])
        cv2.line(scr, tuple(np.int32(p)), tuple(np.int32(q)), int(rs.uniform(40, 120)), 1, cv2.LINE_AA)
    scratches = scr.astype(np.float32) / 255.0

    # --- a silver edge on the lip, tarnished, worn through in places
    rl = dish.rho_lip
    brass = sstep(rl - 0.12, rl - 0.09, rho) * sstep(rl + 0.24, rl + 0.2, rho)
    brass_col = mix(color([0.82, 0.79, 0.74]), color([0.5, 0.45, 0.4]), sstep(-0.4, 1.4, fbm(shape, pxcm, 0.5, 4.0, 2.4, SEED + 16)))
    crk = fbm(shape, pxcm, 0.03, 0.7, 2.2, SEED + 10)
    cracks = sstep(0.022, 0.0, np.abs(crk)) * sstep(0.5, 0.8, rank(fbm(shape, pxcm, 0.3, 2.0, 2.4, SEED + 11)))

    dark = np.maximum(np.clip(eng * 0.85 + edge * 0.55, 0, 1), cracks * 0.7) * shell
    col = mix(black, np.repeat(body[..., None], 3, -1) * mix(color([1.0, 0.985, 0.96]), color([1.0, 0.89, 0.72]), is_pale), shell)
    col = col + (0.012 * drying * (1.0 - shell))[..., None]  # the lip of a dry crack catches a little light
    col = mix(col, color([0.012, 0.01, 0.01]), dark)
    col = mix(col, brass_col, brass)
    # a white piece scatters light from inside as well as mirroring it: a grey mirror in a dark room read as cut paper
    metal = np.maximum(shell * (0.94 - 0.5 * is_pale) * (1.0 - 0.9 * eng) * (1.0 - 0.75 * is_beak), brass * 0.97)
    rough = 0.09 + 0.05 * sstep(-1, 1, wave) + 0.14 * scratches + 0.2 * crackle + 0.04 * drying
    rough = rough * (1 - shell) + shell * (0.11 + 0.03 * sstep(-1, 1, fine) + 0.18 * eng)
    rough = mix(rough, 0.2 + 0.05 * sstep(-1, 1, chip), brass)
    h = 0.0012 * wave - 0.00018 * scratches - 0.0006 * crackle * (1 - shell) - 0.0012 * drying * (1 - shell)
    # the step at a piece's edge is laid over a few pixels: a one-pixel step is a wall in the normals, and glitters
    h = h + blur(shell, max(0.012 * pxcm, 1.0)) * 0.0005 + shell * (0.00008 * lines + 0.0002 * flames - 0.0006 * eng - 0.0009 * cracks) + brass * 0.02
    coat = (1.0 - brass) * (0.92 - 0.25 * rub)
    crough = 0.05 + 0.05 * rank(wave) + 0.16 * scratches + 0.2 * crackle + 0.1 * rub + 0.03 * drying
    # thrown, carved and warped: lacquer on wood moves
    th_ = np.arctan2(Y, X)
    P_ = dish.surface(X, Y, h)
    k_ = (1.0 + 0.0028 * np.sin(2 * th_ + 0.5) + 0.0014 * np.sin(3 * th_ + 2.4))[..., None]
    P_[..., :2] *= k_
    if swatch:
        # a sheet of shell over the whole grid, thickness running with X: read back through the camera by `swatch`
        film = np.clip(SW_FILM[0] + (SW_FILM[1] - SW_FILM[0]) * (X + 8.0) / 16.0, 50.0, 900.0)
        sat, tx, ty = np.ones(shape, np.float32), np.zeros(shape, np.float32), np.zeros(shape, np.float32)
        shell = np.ones(shape, np.float32)
        col = np.full(shape + (3,), 0.3, np.float32)
        metal = np.full(shape, 0.94, np.float32)
        rough = np.full(shape, 0.16, np.float32)
        P_ = dish.surface(X, Y, 0.0)
    return dict(
        P=P_,
        col=np.clip(col, 0, 1).astype(np.float32),
        rough=np.clip(rough, 0.05, 1).astype(np.float32),
        metal=metal.astype(np.float32),
        spec=(0.42 + 0.08 * shell).astype(np.float32),
        coat=coat.astype(np.float32),
        crough=crough.astype(np.float32),
        film=(film * shell).astype(np.float32),
        sat=(sat * shell).astype(np.float32),
        tx=tx.astype(np.float32),
        ty=ty.astype(np.float32),
    )


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "flat":
        flat_view()
        return
    swatch = q == "swatch"
    q = "preview" if swatch else q
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, RUN)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, lobes=LOBES)
    # the aperture grows with the frame, so that a thing out of focus takes the same share of the picture as it did
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, APEX_Y), aperture_mm=APERTURE, focus_rho=FOCUS_RHO)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = PXCM * dens
    X, Y = grid_for_turn(dish, cam, pxcm, TURN)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, **build(dish, X, Y, pxcm, swatch))
    # the window's image lies on the wall, not on the floor: a grey sheet over the whole picture hid the depth of the lacquer
    far = dish.polar(np.array(WINDOW_RHO), np.pi / 2 + 0.2)
    nf = dish.normal(np.array(WINDOW_RHO * np.cos(np.pi / 2 + 0.2)), np.array(WINDOW_RHO * np.sin(np.pi / 2 + 0.2)))
    lw, _ = reflect_light_loc(far, nf, cam, 170.0)
    # the key stands behind and above, so that the nacre's lobe faces the lens while the lacquer's mirror image of it falls outside the dish
    key_loc = np.array([-92.0, 145.0, 115.0])
    scene = {
        "camera": cam,
        "meshes": [{"name": "dish", "npz": npz, "shader_py": SHADER, "params": {"film_ior": 2.2}}],
        "lights": [
            {"name": "key", "loc": key_loc.tolist(), "target": [0, 4, 0], "size": [100, 100], "watts": 170000, "rgb": [1.0, 0.97, 0.92]},
            {"name": "key2", "loc": [90.0, 120.0, 120.0], "target": [0, 4, 0], "size": [90, 90], "watts": 70000, "rgb": [1.0, 0.98, 0.95]},
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": far.tolist(), "size": [340, 120], "sigma": [120, 16], "L": 1.7, "rgb": [0.88, 0.92, 1.0]},
        ],
        "env": {"window": 2.4, "win_az": -32.0, "win_el": 40.0, "win_w": 30.0, "win_h": 34.0, "strip": 0.9, "ceil": 0.07, "wall": 0.03},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": APEX_Y, "seed": 46},
        "world": [0.0, 0.0, 0.0],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 4,
        "spp": {"preview": 96, "mid": 192, "final": 384},
    }
    tag = "swatch" if swatch else {"final": "cand"}.get(q, q)
    if os.environ.get("GEWU_MOVE"):  # the turn this close: move it into looks.json when this take goes into the film. Full size for final, and only this run sees that
        import kit

        lk = kit.looks()
        mv = {**lk[NAME]["move"], "spin": {**lk[NAME]["move"]["spin"], "deg": TURN}, "lights": {"key": [KEY_TRAVEL, 0.0, 0.0]}}
        if os.environ["GEWU_MOVE"] == "final":
            mv.update(res=[2560, 1440], spp=192)
        lk[NAME]["move"] = mv
        kit.looks = lambda: lk
    shoot(RUN, scene, q, develop=DEV, tag=tag)
    if swatch:
        # the chart: thickness against colour at Y = 8, read back from the render
        im = cv2.imread(os.path.join(OUT, RUN, "swatch.png"))
        H_, W_ = im.shape[:2]
        for F_ in np.arange(SW_FILM[0], SW_FILM[1] + 1, 20.0):
            fx = (F_ - SW_FILM[0]) / (SW_FILM[1] - SW_FILM[0]) * 16.0 - 8.0
            x_, y_, _ = project(cam, dish.surface(np.array([fx]), np.array([8.0])).reshape(-1, 3))
            i_, j_ = int(x_[0] * W_), int(y_[0] * H_)
            if 0 <= j_ < H_ and 0 <= i_ < W_:
                print(f"film {F_:.0f} rgb", im[j_, i_][::-1].tolist())


def rim_check():
    """No render: where the crown of the lip and the two birds land in the frame through the turn."""
    dish = Dish(PROFILE, lobes=LOBES)
    cam, _ = dish.camera(W, EL, DIST, apex=(0.5, APEX_Y), aperture_mm=APERTURE, focus_rho=FOCUS_RHO)
    th = np.linspace(0, 2 * np.pi, 7200)
    rho = np.linspace(dish.rho_lip - 0.2, min(dish.rho_lip + 1.2, dish.L), 12)
    R_, T_ = np.meshgrid(rho, th)
    lip = dish.polar(R_, T_).reshape(-1, 3)
    pts = {"bird": (1.0, 8.2), "head": (2.2, 9.55), "tail end": (-1.7, 5.85), "well": (0.0, WELL)}
    birds = dish.polar(np.array([np.hypot(*q) for q in pts.values()]), np.array([np.arctan2(q[1], q[0]) for q in pts.values()]))
    for deg in (-TURN / 2, -TURN / 4, 0.0, TURN / 4, TURN / 2):
        a = np.radians(deg)
        turn = lambda q: np.stack([q[:, 0] * np.cos(a) - q[:, 1] * np.sin(a), q[:, 0] * np.sin(a) + q[:, 1] * np.cos(a), q[:, 2]], 1)
        x, y, _ = project(cam, turn(lip))
        k = np.argmin(y)
        bx, by, _ = project(cam, turn(birds))
        print(f"turn {deg:+.1f}  crown y {y.min():.4f} at x {x[k]:.3f}  dish x {x.min():.3f}..{x.max():.3f}", {n_: (round(float(bx[i]), 3), round(float(by[i]), 3)) for i, n_ in enumerate(pts)})


def deliver():
    """The take's linear frames, developed into out/v2/s46_luopan_take_cand: f###.png, f###.jpg, take.mp4, the form the dev page reads."""
    import json
    import subprocess

    from darkroom import develop as dev, save_png

    src = os.path.join(OUT, RUN + "_move_final")
    dst = os.path.join(OUT, NAME + "_take_cand")
    os.makedirs(dst, exist_ok=True)
    fs = sorted(f for f in os.listdir(src) if f.startswith("take.linear_") and f.endswith(".npy"))
    for i, f in enumerate(fs):
        img = dev(np.load(os.path.join(src, f)).astype(np.float32), **{**DEV, "seed": i + 1})
        save_png(os.path.join(dst, f"f{i:03d}.png"), img)
        cv2.imwrite(os.path.join(dst, f"f{i:03d}.jpg"), (img * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
    json.dump(DEV, open(os.path.join(dst, "develop.json"), "w"))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-r", "25", "-i", os.path.join(dst, "f%03d.jpg"), "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-movflags", "+faststart", os.path.join(dst, "take.mp4")])
    print(dst, len(fs))


if __name__ == "__main__":
    if sys.argv[1:] == ["rim"]:
        rim_check()
    elif sys.argv[1:] == ["deliver"]:
        deliver()
    else:
        main()
