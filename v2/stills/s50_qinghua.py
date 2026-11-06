"""Blue and white (青花), a large early Ming dish seen at a slant: the far lip is the arc, a window lies on the cavetto, and a brushed peony branch sits under real depth of glaze.

    python3 -I v2/stills/s50_qinghua.py flat [pxcm]            the drawing and the body, no render: out/v2/s50_qinghua/flat.jpg
    python3 -I v2/stills/s50_qinghua.py preview|mid|final|draft [--tag=NAME] [--spp=N]
    final goes to cand.* unless --tag says otherwise: the film reads final.*, a new version waits in cand.* until it has been looked at. draft is full size at few samples.

How it is built, from the outside in, because that is how a real one is:
- a glaze shell, closed: transparent + Fresnel gloss at the surface, a little scatter and a faint blue-green absorption in the volume (s50_shader). Its top is level where the body underneath is not, so it pools at the foot of the wall (积釉) and thins over the lip;
- air bubbles in the glaze, real spheres, in swarms, sizes far apart;
- a halo sheet half way up the glaze (cobalt that moved upward in the firing) and the main cobalt sheet just above the body; the two have real parallax. Iron crystals (铁锈斑) sit in the lower one as a dark scatterer. The glaze over them and over heavy cobalt stays level, unlike a real one that sinks a little: any slope there bent the window into white slivers on the dark marks;
- the body, warm, with a few specks of iron, turned on the wheel: its rings are in the body and half smoothed by the glaze;
- the surface: slow hollows that break a reflected window, the throwing rings, orange peel (橘皮), pinholes (棕眼), and a few places where the glaze crawled back from the lip (缩釉) over a body that fired orange (火石红).
- the light on the glaze is a room in reflection only (room() below): a paned window whose image lies on the cavetto, a dim ceiling, a weak veil without an edge over the well (a second window in the well was tried and dropped: its image breaks up and turns the cobalt grey), a dark photographer's side. The white gets its shape from a separate low key light, so the lip throws a real shadow into the dish.

Stand-ins and estimates, none of them measured unless it says so:
- sigma_s, sigma_a, the glaze thickness (0.05-0.09 cm, about twice a real Ming glaze as far as I know, because a sheet at true depth would show under 3 px of parallax at this scale) are estimates. No refraction at the surface (see s50_shader): depths read about 1.5x deeper than they would through n = 1.5;
- the colour targets ARE measured, on ref/bluewhite (reference only, never in the pixels): white sRGB about (216,228,224) on the CMA grape dish, cobalt median (28,43,71), darkest tenth (18,30,49) on the CMA peony bowl. ABS was chosen for that, but what the render gives, measured on cand.jpg, is lighter and bluer than those: white on the rim (196,200,200); all pixels with B-R > 30, pale wash included, median (95,117,149), darkest tenth (57,70,103);
- the brush is a procedural model (hairs, load, wet edge, a wash layer), not a simulated brush; iron spots are clusters of small ellipses where the brush stopped, not a crystal growth; the room is a painted equirect, not a modelled room;
- pinholes, crawl, warp, orange peel and throwing rings are noise fields and hand-set positions at scales chosen by eye.
The drawing is ours, after the general manner of Yongle-Xuande flower sprays (pointed dabs tier on tier, dark at the tip, iron where the brush lifted; long pointed leaves, none like another). ref/bluewhite gave the manner. It copies no piece.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from dishkit import Dish
from glazekit import balls, close_shell
from kit import OUT, ROOT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import view_dir

NAME = "s50_qinghua"
SEED = 50
W, EL, DIST = 15.5, 40.0, 85.0
APEX = (0.5, 0.45)  # the warped lip lands about 0.26 cm above where the unwarped one is fitted, so the crown comes at about .46. The dish is 1.7 frame widths across or more: the far lip is a gentle arc, the rim and its scroll carry the picture, only the top of the flower comes in
# from the outer foot, up over a rounded lip, down the cavetto, over the turn into the well, to the centre. A big dish, 27 cm across; the wide everted rim turns the reflection a second time.
PROFILE = [(8.4, 0.0), (8.75, 0.16), (10.4, 0.5), (12.1, 1.5), (13.0, 2.2), (13.35, 2.62), (13.47, 2.9), (13.42, 3.03), (13.22, 3.04), (12.6, 2.82), (12.0, 2.58), (11.5, 2.26), (11.0, 1.74), (10.5, 1.12), (9.8, 0.72), (6.5, 0.55), (3.0, 0.49), (0.0, 0.47)]
ABS = np.array([2.05, 1.55, 0.82], np.float32)  # per pass through the sheet, see above
SHADER = os.path.join(ROOT, "v2", "stills", "glaze_shader.py")
GLAZE_SHADER = os.path.join(ROOT, "v2", "stills", "s50_shader.py")  # the shell; the sheets and the bubbles stay on glaze_shader
GLAZE = {"kind": "glaze", "ior": 1.52, "g": 0.5, "sigma_s": [1.2, 1.35, 1.4], "sigma_a": [0.62, 0.17, 0.1]}
WELL = 10.15
MS, MY = 1.1, 2.55  # scale and shift of the branch in the well  # rho of the double ring at the well's edge


def catmull(pts, n=16, closed=False):
    p = np.asarray(pts, float)
    if closed:
        m = len(p)
        out = []
        for i in range(m):
            a, b, c, d = p[(i - 1) % m], p[i], p[(i + 1) % m], p[(i + 2) % m]
            t = np.linspace(0, 1, n, endpoint=False)[:, None]
            out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t**3))
        return np.vstack(out)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        t = np.linspace(0, 1, n, endpoint=i == len(p) - 3)[:, None]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t**3))
    return np.vstack(out)


def uv(a):
    return np.array([np.cos(a), np.sin(a)])


class Paper:
    """The raw body being painted: C the strokes, W the washes, I the iron."""

    def __init__(self, X, Y, pxcm, rng):
        self.ny, self.nx = X.shape
        self.x0, self.y0 = float(X[0, 0]), float(Y[0, 0])
        self.pxcm = pxcm
        self.C = np.zeros(X.shape, np.float32)
        self.W = np.zeros(X.shape, np.float32)
        self.I = np.zeros(X.shape, np.float32)
        self.rng = rng

    def fx(self, q, x0=0, y0=0):
        return np.round(((np.asarray(q) - [self.x0, self.y0]) * self.pxcm - [x0, y0]) * 16).astype(np.int32)

    def _box(self, q, m):
        i0 = np.floor((q - [self.x0, self.y0]).min(0) * self.pxcm - m).astype(int)
        i1 = np.ceil((q - [self.x0, self.y0]).max(0) * self.pxcm + m).astype(int)
        return max(i0[0], 0), max(i0[1], 0), min(i1[0], self.nx), min(i1[1], self.ny)

    def stroke(self, pts, hairs=18, edge=0.6, streak=0.5, iron=0.0, pauses=()):
        """pts: (x, y, half width, load). Pigment from a spine, with a tail that breaks up when the load falls."""
        rng = self.rng
        sp = catmull(pts, 18)
        xy, wd, ld = sp[:, :2], np.maximum(sp[:, 2], 0.0015), np.clip(sp[:, 3], 0.0, 1.6)
        d = np.gradient(xy, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1) / (np.hypot(*d.T)[:, None] + 1e-9)
        x0, y0, x1, y1 = self._box(xy, wd.max() * self.pxcm + 6)
        if x1 <= x0 or y1 <= y0:
            return
        sh = (y1 - y0, x1 - x0)
        # the body and its load, a quad at a time
        load = np.zeros(sh, np.float32)
        mask = np.zeros(sh, np.uint8)
        L, Rr = xy + wd[:, None] * nrm, xy - wd[:, None] * nrm
        for i in range(len(xy) - 1):
            q = self.fx(np.array([L[i], L[i + 1], Rr[i + 1], Rr[i]]), x0, y0)
            cv2.fillConvexPoly(load, q, float(0.5 * (ld[i] + ld[i + 1])), cv2.LINE_8, 4)
        poly = self.fx(np.vstack([L, Rr[::-1]]), x0, y0)
        cv2.fillPoly(mask, [poly], 255, cv2.LINE_AA, 4)
        for e_, w_ in ((xy[0], wd[0]), (xy[-1], wd[-1])):  # the brush's round touch
            cv2.circle(mask, tuple(int(v) for v in self.fx(e_, x0, y0)), int(w_ * self.pxcm * 16), 255, -1, cv2.LINE_AA, 4)
        m = mask.astype(np.float32) / 255.0
        load = blur(load, max(0.012 * self.pxcm, 0.5))
        # hairs: lines along the spine, each carrying its own share
        hair = np.zeros(sh, np.float32)
        s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
        hw = max(1, int(round(0.012 * self.pxcm)))
        for _ in range(hairs):
            t0 = rng.uniform(-1, 1)
            wander = np.interp(s, np.linspace(0, s[-1] + 1e-6, 7), rng.normal(0, 0.1, 7))
            q = xy + (np.clip(t0 + wander, -1, 1)[:, None] * wd[:, None]) * nrm
            cv2.polylines(hair, [self.fx(q, x0, y0)], False, float(rng.lognormal(0, 0.45)), hw, cv2.LINE_AA, 4)
        hair = blur(hair, max(0.012 * self.pxcm, 0.5))
        hair = hair / max(float(np.percentile(hair[mask > 128], 70)) if (mask > 128).any() else 1.0, 1e-3)
        # dry: as the load falls the hairs part
        dry = sstep(0.05, 0.75, hair * 0.75 + load - 0.3)
        # the wet edge
        dist = cv2.distanceTransform((mask > 128).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / self.pxcm
        wet = np.exp(-dist / 0.018)
        conc = m * load * (1.0 - streak + streak * np.clip(hair, 0, 1.5)) * dry * (1.0 + edge * wet)
        self.C[y0:y1, x0:x1] += conc
        # iron: where the load runs thick, at random, and where the brush stopped
        n = int(rng.poisson(iron * s[-1]))
        for _ in range(n):
            i = rng.integers(0, len(xy))
            if ld[i] > 0.6:
                self.spots(xy[i] + rng.normal(0, 0.5, 2) * wd[i], rng.lognormal(np.log(0.05), 0.5), rng.poisson(7) + 2)
        for f, k in pauses:
            i = int(f * (len(xy) - 1))
            self.spots(xy[i], max(wd[i] * 0.8, 0.05), k)

    def clear(self, poly, grow=0.03):
        """The painter leaves white for what comes next: what is under a new shape goes, with a hair of white around it."""
        q = np.asarray(poly)
        g = int(grow * self.pxcm) + 2
        x0, y0, x1, y1 = self._box(q, g + 4)
        if x1 <= x0 or y1 <= y0:
            return
        mask = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(mask, [self.fx(q, x0, y0)], 255, cv2.LINE_AA, 4)
        m = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * g + 1, 2 * g + 1))).astype(np.float32) / 255.0
        m = blur(m, max(0.006 * self.pxcm, 0.5))
        for F in (self.C, self.W, self.I):
            F[y0:y1, x0:x1] *= 1.0 - m

    def reserve(self, path, w0, w1):
        """A vein left white: the painter stops his wash short on either side of it. Width from w0 to w1 (half widths, cm), with a tremor."""
        q = np.asarray(path)
        x0, y0, x1, y1 = self._box(q, max(w0, w1) * self.pxcm + 4)
        if x1 <= x0 or y1 <= y0:
            return
        mask = np.zeros((y1 - y0, x1 - x0), np.float32)
        n = len(q)
        pts = self.fx(q, x0, y0)
        for i in range(n - 1):
            t = i / max(n - 2, 1)
            th = max(1, int(round(2 * (w0 + (w1 - w0) * t) * self.pxcm * self.rng.uniform(0.7, 1.25))))
            cv2.line(mask, tuple(int(v) for v in pts[i]), tuple(int(v) for v in pts[i + 1]), 1.0, th, cv2.LINE_AA, 4)
        m = blur(mask, max(0.004 * self.pxcm, 0.4))
        self.C[y0:y1, x0:x1] *= 1.0 - 0.92 * m
        self.W[y0:y1, x0:x1] *= 1.0 - 0.8 * m

    def begin(self, poly, grow=0.012):
        """What is painted until end() stays inside poly: a brush that knows where the edge is, but only roughly."""
        q = np.asarray(poly)
        x0, y0, x1, y1 = self._box(q, 8)
        if x1 <= x0 or y1 <= y0:
            return None
        mask = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(mask, [self.fx(q, x0, y0)], 255, cv2.LINE_AA, 4)
        g = int(grow * self.pxcm) + 1
        m = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * g + 1, 2 * g + 1))).astype(np.float32) / 255.0
        return (x0, y0, x1, y1, self.C[y0:y1, x0:x1].copy(), blur(m, max(0.005 * self.pxcm, 0.5)))

    def end(self, st):
        if st is None:
            return
        x0, y0, x1, y1, old, m = st
        self.C[y0:y1, x0:x1] = old + (self.C[y0:y1, x0:x1] - old) * m

    def spots(self, c, spread, n):
        """Heaped iron: a cluster of small crystals, some run together."""
        rng = self.rng
        for _ in range(int(n * 2.4)):
            p = np.asarray(c) + rng.normal(0, spread, 2)
            r = float(np.clip(rng.lognormal(np.log(0.0125), 0.62), 0.004, 0.042))
            q = self.fx(p)
            axes = (max(int(r * self.pxcm * 16 * rng.uniform(0.7, 1.3)), 8), max(int(r * self.pxcm * 16 * rng.uniform(0.6, 1.1)), 8))
            cv2.ellipse(self.I, tuple(int(v) for v in q), axes, float(rng.uniform(0, 180)), 0, 360, float(rng.uniform(0.6, 1.2)), -1, cv2.LINE_AA, 4)

    def wash(self, poly, o, ang, L, lo, hi, edge=0.3):
        """A wash inside a closed outline, from `hi` (where the brush touched) to `lo` over the length L along the axis."""
        q = np.asarray(poly)
        x0, y0, x1, y1 = self._box(q, 6)
        if x1 <= x0 or y1 <= y0:
            return
        sh = (y1 - y0, x1 - x0)
        mask = np.zeros(sh, np.uint8)
        cv2.fillPoly(mask, [self.fx(q, x0, y0)], 255, cv2.LINE_AA, 4)
        xs = self.x0 + (np.arange(x0, x1, dtype=np.float32) + 0.0) / self.pxcm
        ys = self.y0 + (np.arange(y0, y1, dtype=np.float32) + 0.0) / self.pxcm
        Xs, Ys = np.meshgrid(xs, ys)
        t = np.clip(((Xs - o[0]) * np.cos(ang) + (Ys - o[1]) * np.sin(ang)) / L, 0, 1)
        dist = cv2.distanceTransform((mask > 128).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / self.pxcm
        self.W[y0:y1, x0:x1] += mask.astype(np.float32) / 255.0 * (hi + (lo - hi) * t**0.8) * (1.0 + edge * np.exp(-dist / 0.03))


def press_line(P, pts, w0, w1, load, rng, hairs=8, iron=0.0, pauses=()):
    """A fast line: pts along, thick to thin, the pressure wandering."""
    p = np.asarray(pts, float)
    n = len(p)
    out = []
    for i in range(n):
        f = i / max(n - 1, 1)
        out.append((p[i, 0], p[i, 1], (w0 + (w1 - w0) * f) * rng.uniform(0.72, 1.28), load * rng.uniform(0.85, 1.2) * (1 - 0.2 * f)))
    P.stroke(out, hairs=hairs, edge=0.45, streak=0.45, iron=iron, pauses=pauses)


def curl(P, o, a, size, sign, rng, load=0.85):
    """A tendril, one fast flick that winds in: a brush lifting. Never two alike."""
    n = rng.integers(7, 11)
    turns = rng.uniform(0.9, 1.6)
    t = np.linspace(0, 1, n)
    aa = a + sign * turns * 2 * np.pi * t**1.25
    step = size * (1 - 0.86 * t) * 2 * np.pi * turns / (n - 1) * 0.42
    q = np.asarray(o, float) + np.cumsum(step[:, None] * np.stack([np.cos(aa), np.sin(aa)], 1), 0)
    press_line(P, q, 0.018 * rng.uniform(0.8, 1.2), 0.005, load, rng, hairs=4)
    if rng.random() < 0.5:
        P.spots(q[-1], 0.012, int(rng.integers(1, 3)))


def outline_leaf(base, ang, L, Wd, bend, flick, rng, wavy=0.0):
    """Outline and spine of one long pointed leaf: a curved spine, unequal halves, the tip pulled to one side."""
    s = np.linspace(0, 1, 26)
    u_, n_ = uv(ang), uv(ang + np.pi / 2)
    sp = np.asarray(base, float) + L * s[:, None] * u_ + (bend * L * np.sin(np.pi * s) + flick * L * s**5)[:, None] * n_
    peak = rng.uniform(0.28, 0.5)
    prof = (s / peak) ** 0.75 * np.exp(0.75 * (1 - s / peak)) * (1 - s**2.5) ** 0.9
    prof /= prof.max()
    la, lb = Wd * rng.uniform(0.42, 0.6), Wd * rng.uniform(0.36, 0.56)
    ph = rng.uniform(0, 6.28, 2)
    fq = rng.uniform(9, 15, 2)
    ea = 1 + wavy * np.sin(fq[0] * s + ph[0])
    eb = 1 + wavy * np.sin(fq[1] * s + ph[1])
    d = np.gradient(sp, axis=0)
    nn = np.stack([-d[:, 1], d[:, 0]], 1) / (np.hypot(*d.T)[:, None] + 1e-9)
    A = sp + (la * prof * ea)[:, None] * nn
    B = sp - (lb * prof * eb)[:, None] * nn
    return np.vstack([A, B[::-1][1:-1]]), sp, nn, la * prof, lb * prof


def ming_leaf(P, base, ang, L, Wd, rng, load=1.0, bend=None, flick=None, wavy=None, dark=None):
    """Long strokes along the leaf, each from the stem to the tip, on a wash: dark at one side, a white rib left or a dark rib drawn last, iron along the heavy side and at the tip."""
    bend = rng.uniform(-0.14, 0.14) if bend is None else bend
    flick = rng.uniform(-0.12, 0.12) if flick is None else flick
    wavy = rng.choice([0.0, 0.06, 0.11]) if wavy is None else wavy
    poly, sp, nn, la, lb = outline_leaf(base, ang, L, Wd, bend, flick, rng, wavy)
    P.clear(poly, 0.018)
    P.wash(poly, np.asarray(base), ang, L, 0.3 + 0.2 * rng.random(), 0.6 + 0.2 * rng.random(), edge=0.3)
    st = P.begin(poly, 0.01)
    side = rng.choice([-1, 1])  # the side the loaded brush went down
    nst = int(rng.integers(3, 7))
    for k in range(nst):
        f = (k + rng.uniform(0.2, 0.8)) / nst * 2 - 1
        heavy = 1.0 + 0.5 * side * f
        i0, i1 = int(rng.uniform(0, 3)), int(rng.uniform(15, 25))
        idx = np.linspace(i0, i1, 6).astype(int)
        hw = np.where(f > 0, la, lb)
        q = sp[idx] + (f * hw[idx])[:, None] * nn[idx] * 0.8
        wd_ = Wd * rng.uniform(0.09, 0.16)
        ld = load * heavy * rng.uniform(0.85, 1.25)
        P.stroke([(q[j, 0], q[j, 1], wd_ * (0.5 + 0.7 * np.sin(np.pi * (j + 0.6) / 6.6)), ld * (1.15 - 0.1 * j)) for j in range(6)], hairs=9, edge=0.6, streak=0.55)
    P.end(st)
    if rng.random() < (0.7 if dark is None else 0.0 if dark else 1.0):
        P.reserve(sp[1:22], 0.013, 0.003)
        for f in np.sort(rng.uniform(0.15, 0.75, rng.integers(2, 6))):
            i = int(f * 25)
            s_ = rng.choice([-1, 1])
            e = sp[i] + s_ * nn[i] * (la[i] if s_ > 0 else lb[i]) * rng.uniform(0.45, 0.8) + (sp[min(i + 3, 25)] - sp[i]) * rng.uniform(0.8, 1.6)
            P.reserve(np.linspace(sp[i], e, 5) + rng.normal(0, 0.004, (5, 2)), 0.007, 0.002)
    else:
        P.stroke([(sp[i, 0], sp[i, 1], 0.016 * (1 - i / 26) + 0.003, 1.4) for i in range(0, 24, 4)], hairs=3, edge=0.2, streak=0.2)
    # the brush stopped at the tip and lay along the heavy side: iron gathers there
    edge_ = sp + (side * np.where(side > 0, la, lb))[:, None] * nn * 0.8
    for f in rng.uniform(0.2, 0.9, rng.integers(2, 7)):
        P.spots(edge_[int(f * 25)], 0.03 * rng.uniform(0.6, 1.3), int(rng.integers(1, 5)))
    P.spots(sp[int(rng.uniform(21, 25))], 0.018, int(rng.integers(1, 5)))
    return sp


def lobed_leaf(P, base, ang, L, Wd, rng, load=1.0):
    """A peony leaf: the end lobe long, a shorter one on either side, unequal, sharing a stem."""
    base = np.asarray(base, float)
    for off, fr, wf in sorted(((rng.uniform(0.55, 0.85), rng.uniform(0.5, 0.68), 0.62), (-rng.uniform(0.55, 0.85), rng.uniform(0.5, 0.68), 0.62))):
        ming_leaf(P, base + uv(ang) * L * rng.uniform(0.1, 0.24), ang + off, L * fr, Wd * wf, rng, load * rng.uniform(0.85, 1.05))
    ming_leaf(P, base, ang, L, Wd * 0.8, rng, load)


class Bloom:
    """Places a unit flower on the plate: its axis points where it faces, and it is squashed along that axis: a head seen a little from the side."""

    def __init__(self, c, ang, R, sq):
        self.c, self.ang, self.R, self.sq = np.asarray(c, float), ang, R, sq

    def __call__(self, q):
        q = np.atleast_2d(q) * self.R
        c_, s_ = np.cos(self.ang), np.sin(self.ang)
        x, y = q[:, 0] * self.sq, q[:, 1]
        return np.stack([self.c[0] + c_ * x - s_ * y, self.c[1] + s_ * x + c_ * y], 1)


def dab_petal(P, T, a, r0, r1, wid, load, rng, teeth=None, dark_tip=True, iron=0.55):
    """One petal of a Ming peony: a pointed wedge, cut at its end into one to three teeth, painted by a few dabs from base to tip; the load piles up where the brush lifted."""
    teeth = int(rng.choice([1, 1, 2, 3])) if teeth is None else teeth
    u_, n_ = uv(a + rng.normal(0, 0.035)), uv(a + np.pi / 2)
    L = r1 - r0
    pt = lambda s, t: (r0 * uv(a) + s * L * u_ + t * n_).tolist()  # noqa: E731
    w = wid * rng.uniform(0.82, 1.2)
    sw = rng.uniform(-0.1, 0.1)
    pts = [pt(0, -0.05 * w), pt(0.4, -0.76 * w + sw * w), pt(0.75, -w * rng.uniform(0.86, 1.08))]
    for k in range(teeth):
        f = (k + 0.5) / teeth * 2 - 1
        pts.append(pt(rng.uniform(0.95, 1.1) * (1 - 0.12 * f * f), f * w * 0.72))
        if k < teeth - 1:
            pts.append(pt(rng.uniform(0.76, 0.86), (f + 1.0 / teeth) * w * 0.72))
    pts += [pt(0.75, w * rng.uniform(0.86, 1.08)), pt(0.4, 0.76 * w + sw * w), pt(0, 0.05 * w)]
    poly = T(catmull(pts, 6, closed=True))
    P.clear(poly, 0.02)
    b_ = T(pt(0, 0))[0]
    e_ = T(pt(1, 0))[0]
    dir_ = np.arctan2(*(e_ - b_)[::-1])
    Lp = float(np.hypot(*(e_ - b_)))
    P.wash(poly, b_, dir_, Lp, 0.52 + 0.3 * load * rng.random(), 0.36, edge=0.35)
    st = P.begin(poly, 0.008)
    tips = []
    for k in rng.permutation(int(rng.integers(3, 6))):
        f = (k + rng.uniform(0.2, 0.8)) / 4.5 * 2 - 1
        reach = rng.uniform(0.82, 1.02)
        q0, q1, q2 = pt(rng.uniform(0.1, 0.4), f * w * 0.42), pt(0.68 * reach, f * w * 0.74), pt(reach, f * w * 0.62)
        q = T(np.array([q0, q1, q2]))
        wd_ = float(wid * T.R * rng.uniform(0.2, 0.34))
        ld = load * rng.uniform(0.85, 1.3)
        P.stroke([(q[0, 0], q[0, 1], wd_ * 0.45, ld * 0.55), (q[1, 0], q[1, 1], wd_, ld * 1.05), (q[2, 0], q[2, 1], wd_ * 0.32, ld * (1.45 if dark_tip else 0.9))], hairs=7, edge=0.55, streak=0.5)
        tips.append(q[2])
    P.end(st)
    if rng.random() < 0.6:  # a white vein down the middle, stopped short
        o_ = rng.uniform(-0.3, 0.3) * w
        P.reserve(T(np.array([pt(s_, o_ * (0.6 + s_)) for s_ in np.linspace(0.12, rng.uniform(0.45, 0.72), 6)])) + rng.normal(0, 0.003, (6, 2)), 0.007, 0.002)
    if rng.random() < iron:
        t_ = tips[int(rng.integers(0, len(tips)))]
        P.spots(t_, 0.026 * rng.uniform(0.7, 1.4), int(rng.integers(4, 13)))


def peony(P, c, ang, R, rng, sq=0.86):
    """Tier on tier from the outside in. A thin white stays between the tiers because the painter leaves it. The front tier is long, the back is hidden by what is painted after it; the heart is a white gap with a few short dark jabs, not a target."""
    T = Bloom(c, ang, R, sq)
    a0 = rng.uniform(0, 6.28)
    tiers = ((10, 0.42, 1.0, 0.25, 0.42, 0.5, 3), (13, 0.36, 0.8, 0.17, 0.62, 0.6, None), (14, 0.27, 0.62, 0.125, 0.78, 0.6, None), (11, 0.17, 0.46, 0.1, 0.9, 0.6, 1), (7, 0.09, 0.31, 0.075, 1.0, 0.5, 1))
    for n, r0, r1, wd, load, irn, teeth in tiers:
        order = rng.permutation(n)
        for i in order:
            a = a0 + (i + rng.normal(0, 0.22)) / n * 6.283
            # towards the viewer (the axis) a petal is longer and falls forward; the far ones shorter
            fr = 1.0 + 0.1 * np.cos(a) + rng.normal(0, 0.06)
            if rng.random() < 0.03:
                continue  # a gap: the eye rests here
            dab_petal(P, T, a, r0 * fr, r1 * fr, wd, load * rng.uniform(0.85, 1.12), rng, teeth=teeth, iron=irn)
        a0 += rng.uniform(0.15, 0.5)
    # the heart: white, a crescent of short dark jabs on the far side, seeds of iron
    th_ = np.linspace(0, 6.283, 22, endpoint=False)
    r_ = 0.12 * (1 + 0.14 * np.sin(3 * th_ + rng.uniform(0, 6))) * (1 + 0.1 * rng.normal(0, 1, 22))
    P.clear(T(np.stack([r_ * np.cos(th_), r_ * np.sin(th_)], 1)), 0.012)
    for i in range(int(rng.integers(13, 18))):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0.01, 0.11)
        b = T(r * uv(a))[0]
        e = T((r + rng.uniform(0.03, 0.07)) * uv(a + rng.normal(0, 0.5)))[0]
        P.stroke([(b[0], b[1], 0.012, 0.9), ((b + e)[0] / 2, (b + e)[1] / 2, 0.026, 1.4), (e[0], e[1], 0.007, 1.0)], hairs=4, edge=0.4, streak=0.3)
    P.spots(c, R * 0.12, 16)


def half_open(P, c, ang, R, rng):
    """A flower seen from the side, half open: a cup of pointed petals rising from a calyx."""
    T = Bloom(c, ang, R, 1.0)
    for a, r1, wd, ld in sorted(((rng.uniform(-0.75, -0.5), 0.92, 0.2, 1.1), (rng.uniform(0.5, 0.75), 0.9, 0.2, 1.1), (rng.uniform(-0.32, -0.16), 1.04, 0.2, 0.95), (rng.uniform(0.16, 0.32), 1.0, 0.21, 0.95), (rng.normal(0, 0.05), 0.82, 0.18, 1.3), (rng.uniform(-1.05, -0.9), 0.72, 0.16, 1.2), (rng.uniform(0.9, 1.05), 0.7, 0.16, 1.2)), key=lambda v: -v[1]):
        dab_petal(P, T, a, 0.06, r1, wd, ld, rng)
    for a in (rng.uniform(1.8, 2.3), -rng.uniform(1.8, 2.3)):
        b = T(np.zeros(2))[0]
        ming_leaf(P, b, ang + a * 0.7, R * rng.uniform(0.42, 0.62), R * 0.2, rng, 1.1, wavy=0.0)
    P.spots(T(np.array([0.08, 0.0]))[0], R * 0.1, 10)


def bud(P, c, ang, R, rng):
    T = Bloom(c, ang, R, 1.0)
    for a, r1, wd in ((-0.42, 0.86, 0.3), (0.42, 0.9, 0.3), (0.0, 1.0, 0.3)):
        dab_petal(P, T, a + rng.normal(0, 0.05), 0.02, r1, wd, 1.25, rng, teeth=1)
    for s_ in (-1, 1):
        ming_leaf(P, T(np.zeros(2))[0], ang + s_ * rng.uniform(1.1, 1.5), R * rng.uniform(0.6, 0.85), R * 0.28, rng, 1.1, wavy=0.0)


def turn_ring(P, rho, w, load, rng, a0=None, th0=None, th1=None):
    """A line pulled with the plate turning: the width and the load wander, the circle does not quite close, the rim is not quite centred."""
    a0 = rng.uniform(0, 6.28) if a0 is None else a0
    n = 72
    aa = a0 + np.linspace(0, 6.283 + rng.uniform(0.02, 0.12), n)
    drift = rng.uniform(-0.03, 0.03) * np.linspace(0, 1, n)
    ec, ph = rng.uniform(0.01, 0.03), rng.uniform(0, 6.28)
    wid = np.interp(np.arange(n), np.linspace(0, n, 12), rng.uniform(0.75, 1.3, 12)) * w
    lo_ = np.interp(np.arange(n), np.linspace(0, n, 16), rng.uniform(0.72, 1.2, 16)) * load
    r = rho + drift + ec * np.sin(aa + ph)
    P.stroke(list(zip(r * np.cos(aa), r * np.sin(aa), wid, lo_)), hairs=4, edge=0.25, streak=0.4)


def scroll_band(P, r0, A, rng):
    """卷草 on the rim: one vine, waving, a curled leaf in each bend; each bend drawn on its own, so no two alike. Only the part of the plate that is ever seen."""
    th = -0.5
    sgn = 1.0
    end = np.pi + 0.5
    n = 0
    while th < end:
        step = rng.uniform(0.115, 0.15)
        tt = np.linspace(th, th + step, 7)
        rr = r0 + sgn * A * np.sin(np.pi * (tt - th) / step) * rng.uniform(0.85, 1.1)
        q = np.stack([rr * np.cos(tt), rr * np.sin(tt)], 1)
        press_line(P, q, 0.022, 0.015, 1.0, rng, hairs=4)
        # the leaf curls into the bend from its crown
        mid = q[3]
        rad = uv(0.5 * (tt[3] + tt[3])) * sgn
        tan = uv(tt[3] + np.pi / 2) * rng.choice([-1, 1])
        base = mid
        a = np.arctan2(*(-rad + 0.75 * tan)[::-1])
        for k, (fr, wf, of) in enumerate(((1.0, 1.0, 0.0), (0.72, 0.8, rng.uniform(0.55, 0.85)))):
            if k == 1 and rng.random() < 0.3:
                continue
            L = A * rng.uniform(1.15, 1.6) * fr
            ming_leaf(P, base, a + of * rng.choice([-1, 1]) + rng.normal(0, 0.1), L, A * rng.uniform(0.5, 0.72) * wf, rng, rng.uniform(0.85, 1.1), wavy=0.0, flick=rng.uniform(-0.2, 0.2))
        if rng.random() < 0.3:
            curl(P, q[5], tt[5] + np.pi / 2 * rng.choice([-1, 1]), A * 0.45, rng.choice([-1, 1]), rng)
        th += step
        sgn = -sgn
        n += 1


def paint(X, Y, pxcm, rl):
    """The painter's order: rings on the wheel first, then the rim, the branch, the leaves, the flowers; the wash goes down under the lines of each."""
    Pr = Paper(X, Y, pxcm, np.random.default_rng(SEED))
    rng = Pr.rng
    P = Pr
    turn_ring(P, WELL, 0.022, 1.05, rng)
    turn_ring(P, WELL + 0.2, 0.012, 0.8, rng)
    turn_ring(P, rl - 2.05, 0.018, 1.0, rng)
    turn_ring(P, rl - 1.88, 0.011, 0.75, rng)
    turn_ring(P, rl - 0.32, 0.016, 0.95, rng)
    scroll_band(P, rl - 1.1, 0.5, rng)
    # the branch was drawn in its own coordinates: this is where it sits in the well
    P = Paper(X / MS, (Y - MY) / MS, pxcm * MS, rng)

    FL = np.array([0.9, 3.5])
    F2 = np.array([-4.75, 3.05])
    BD = np.array([5.65, 3.0])
    # the branch: rises from the near side, out of the picture, swings into the flower; a long shoot to each side. One breath each: thick at the fork, thin at the end.
    press_line(P, [(-2.2, -7.2), (-2.75, -5.2), (-2.2, -3.35), (-1.1, -1.85), (0.05, -0.7), (0.7, 1.3)], 0.05, 0.03, 1.1, rng, hairs=12, iron=0.6, pauses=((0.45, 8), (0.72, 6)))
    press_line(P, [(-2.5, -4.2), (-3.9, -3.2), (-5.35, -1.75), (-5.95, -0.2), (-5.6, 1.3), F2 - [0.02, 0.05]], 0.034, 0.015, 1.0, rng, hairs=8, iron=0.5, pauses=((0.05, 6),))
    press_line(P, [(-0.6, -1.25), (1.2, -2.05), (3.3, -1.8), (5.1, -0.75), (6.0, 0.9), BD - [0.0, 0.05]], 0.034, 0.014, 1.0, rng, hairs=8, iron=0.5, pauses=((0.05, 6),))
    press_line(P, [(3.3, -1.8), (4.6, -3.0), (5.95, -3.25), (6.8, -2.6)], 0.018, 0.008, 0.9, rng, hairs=5)
    press_line(P, [(-5.3, -1.85), (-6.5, -1.25), (-7.15, -0.2)], 0.016, 0.007, 0.9, rng, hairs=5)
    # tendrils, where a shoot forks
    for o, a, s, sg in (((6.8, -2.6), 0.6, 0.42, 1), ((-7.15, -0.2), 1.7, 0.36, -1), ((4.5, -1.15), 1.4, 0.4, 1), ((-3.9, -3.2), 2.8, 0.34, -1), ((-5.85, 0.4), 2.4, 0.3, 1), ((1.9, -2.0), -1.0, 0.36, -1)):
        curl(P, o, a, s, sg, rng)

    # leaves: from little to big, and turned every way; a few seen edge on; pairs at a node never level with each other
    for base, ang, L, wd in (
        ((-2.75, -5.2), 2.55, 3.1, 1.15),
        ((-2.4, -3.7), -0.35, 3.3, 1.2),
        ((-1.1, -1.85), 2.2, 2.3, 0.72),
        ((-3.9, -3.2), -2.55, 1.5, 0.5),
        ((-5.35, -1.75), 3.3, 1.2, 0.34),
        ((-5.95, -0.2), -0.6, 2.05, 0.74),
        ((-5.85, 0.75), 2.5, 1.9, 0.56),
        ((1.2, -2.05), -1.25, 2.3, 0.82),
        ((3.3, -1.8), 1.15, 1.65, 0.62),
        ((5.1, -0.75), -0.5, 1.85, 0.56),
        ((5.95, 0.9), 2.05, 2.1, 0.62),
        ((5.98, 1.6), 0.25, 1.45, 0.44),
        ((5.95, -3.25), -1.0, 1.15, 0.36),
        ((-7.15, -0.2), 2.3, 0.85, 0.28),
    ):
        ming_leaf(P, base, ang, L, wd, rng, rng.uniform(0.62, 1.0))
    for base, ang, L, wd in (((-0.3, -0.95), -0.55, 3.1, 1.15), ((0.1, -0.2), 2.75, 2.8, 1.1)):
        lobed_leaf(P, base, ang, L, wd, rng, 0.85)

    half_open(P, F2, 1.42, 2.0, rng)
    bud(P, BD, 1.45, 1.2, rng)
    peony(P, FL, 1.1, 3.2, rng)
    for f in ("C", "W", "I"):
        setattr(Pr, f, getattr(Pr, f) + getattr(P, f))
    return Pr


def fields(X, Y, pxcm, rl):
    """Everything drawn on the flat coordinates: the two cobalt sheets, the iron, the body's colour, the thickness of the glaze and the surface."""
    shape = X.shape
    P = paint(X, Y, pxcm, rl)
    rho = np.hypot(X, Y)
    # warp: the slow tremor of the body under the brush, a quick feathering where pigment entered the raw clay
    dx = 0.0055 * fbm(shape, pxcm, 0.3, 1.2, 2.6, SEED + 1) + 0.0052 * fbm(shape, pxcm, 0.012, 0.05, 1.4, SEED + 2)
    dy = 0.0055 * fbm(shape, pxcm, 0.3, 1.2, 2.6, SEED + 3) + 0.0052 * fbm(shape, pxcm, 0.012, 0.05, 1.4, SEED + 4)
    mx, my = np.meshgrid(np.arange(shape[1], dtype=np.float32), np.arange(shape[0], dtype=np.float32))
    mx = mx + dx * pxcm
    my = my + dy * pxcm
    C = np.minimum(cv2.remap(P.C, mx, my, cv2.INTER_LINEAR), 2.2)
    Wa = np.minimum(cv2.remap(P.W, mx, my, cv2.INTER_LINEAR), 2.0)
    I = np.clip(cv2.remap(P.I, mx, my, cv2.INTER_LINEAR), 0, 1.2)
    C_s = blur(C, max(0.007 * pxcm, 0.5))
    rag = fbm(shape, pxcm, 0.008, 0.05, 1.5, SEED + 12)
    I = sstep(0.28, 0.62, blur(I, max(0.006 * pxcm, 0.5)) + 0.16 * rag)
    I_s = blur(I, max(0.0025 * pxcm, 0.4)) * sstep(0.12, 0.5, blur(C + Wa, max(0.008 * pxcm, 0.5)))
    cloud = rank(fbm(shape, pxcm, 0.2, 1.4, 2.6, SEED + 5))
    Wa_s = blur(Wa, max(0.025 * pxcm, 0.5)) * (0.72 + 0.56 * cloud)
    tot = C_s + 0.82 * Wa_s
    grain = rank(fbm(shape, pxcm, 0.006, 0.03, 1.4, SEED + 7))
    mott = rank(fbm(shape, pxcm, 0.03, 0.16, 2.0, SEED + 8))
    conc = tot * (0.72 + 0.26 * grain + 0.3 * mott)
    # a powder under a lens: the edge of a pale mark is stipple; a heavy stroke carries dark grains (ref/bluewhite, the grape dish and the peony jar)
    fine = rank(fbm(shape, pxcm, 0.005, 0.016, 1.0, SEED + 13))
    fine2 = rank(fbm(shape, pxcm, 0.008, 0.03, 1.1, SEED + 14))
    conc = conc * (0.34 + 0.66 * sstep(0.02, 0.62, conc * 1.15 + (fine - 0.5)))
    heavy = blur(np.minimum(C, 1.6), max(0.012 * pxcm, 0.5))
    patch = rank(fbm(shape, pxcm, 0.2, 1.4, 2.2, SEED + 15))
    sand = sstep(0.0, 0.05, fine2 - (1.0 - 0.34 * heavy * (0.25 + 1.3 * patch)))
    # the eye reads the dark of a stroke as blue only if it stays short of black: a sheet of pigment saturates, what piles up on it are grains and iron
    conc = 1.15 * (1.0 - np.exp(-conc / 1.15))
    low = conc + 1.3 * I_s + 0.9 * sand
    Iron = I_s  # what stands proud of the cobalt and dents the glaze; the grains stay under it
    I_s = np.maximum(I_s, 0.4 * sand)
    # cobalt that moved upward in the firing: a pale halo beyond every mark, broken by noise; it goes in the upper sheet, so it has parallax against the mark
    hn = 0.5 + 0.9 * rank(fbm(shape, pxcm, 0.08, 0.5, 2.2, SEED + 6))
    hb = np.minimum(tot, 1.3)
    high = (0.26 * blur(hb, max(0.03 * pxcm, 0.5)) + 0.12 * blur(hb, max(0.09 * pxcm, 0.5))) * hn

    # the body: warm, slow patches, a few iron specks, whiter than the glaze over it. Fired orange where the glaze is thin at the lip (a patch here and there, not a line)
    big = rank(fbm(shape, pxcm, 1.5, 7.0, 3.2, SEED + 9))
    body = mix(color([0.89, 0.895, 0.85]), color([0.915, 0.915, 0.875]), big)
    thin = 0.15 + 0.85 * sstep(0.45, 0.85, rank(fbm(shape, pxcm, 0.5, 3.5, 2.6, SEED + 17)))
    wob = 0.03 * fbm(shape, pxcm, 0.3, 2.2, 2.6, SEED + 10) + 0.012 * fbm(shape, pxcm, 0.02, 0.2, 1.6, SEED + 16)
    lipb = sstep(rl - 0.1, rl + 0.03, rho + wob) * thin
    body = mix(body, color([0.74, 0.56, 0.39]), 0.8 * lipb)
    rng = np.random.default_rng(SEED + 11)
    area = shape[0] * shape[1] / pxcm**2
    seeds = np.ones(shape, np.uint8)
    k = int(area * 0.05)
    seeds[rng.integers(0, shape[0], k), rng.integers(0, shape[1], k)] = 0
    dp = cv2.distanceTransform(seeds, cv2.DIST_L2, 5).astype(np.float32) / pxcm
    rsp = 0.004 + 0.012 * rank(fbm(shape, pxcm, 0.5, 2.0, 1.5, SEED + 24)) ** 3
    body = mix(body, color([0.2, 0.14, 0.1]), 0.8 * sstep(1.25, 0.6, dp / rsp))

    # the glaze's thickness: it runs off the lip and off the rim's crest, it collects at the foot of the wall; slowly uneven
    t0 = 0.052 + 0.02 * np.exp(-(((rho - (WELL + 0.5)) / 1.3) ** 2)) + 0.012 * np.exp(-(((rho - (rl - 2.2)) / 0.5) ** 2))
    t0 = t0 * (1 - 0.72 * sstep(rl - 0.55, rl - 0.05, rho))
    tv = 1 + 0.14 * fbm(shape, pxcm, 1.0, 5.0, 3.0, SEED + 25)  # the body is uneven under a level surface, not the other way about
    # where the glaze crawled back: at the lip only, hand-placed so that they are few, irregular, of different sizes, and fired orange
    cr = np.zeros(shape, np.float32)
    for th_, dr, r_ in ((1.34, -0.02, 0.2), (1.385, -0.12, 0.06), (0.62, -0.05, 0.12), (2.18, 0.0, 0.26), (2.24, -0.2, 0.07), (2.7, -0.08, 0.1), (0.2, -0.04, 0.16), (1.81, -0.04, 0.05)):
        cx, cy = (rl + dr) * np.cos(th_), (rl + dr) * np.sin(th_)
        i, j = int((cy - float(Y[0, 0])) * pxcm), int((cx - float(X[0, 0])) * pxcm)
        if 0 <= i < shape[0] and 0 <= j < shape[1]:
            cv2.ellipse(cr, (j, i), (max(int(r_ * pxcm), 1), max(int(r_ * 0.6 * pxcm), 1)), float(np.degrees(th_) + 90), 0, 360, 1.0, -1, cv2.LINE_AA)
    crawl = sstep(0.42, 0.58, blur(cr, max(0.035 * pxcm, 0.5)) + 0.16 * fbm(shape, pxcm, 0.02, 0.2, 1.8, SEED + 26))
    body = mix(body, color([0.66, 0.42, 0.26]), 0.85 * blur(crawl, max(0.012 * pxcm, 0.5)))
    tnom = t0 * (1 - crawl) + 0.0015 * crawl
    t = t0 * tv * (1 - crawl) + 0.0015 * crawl
    # pinholes: where a bubble broke at the surface and the glaze did not close. A few, in loose groups, more near the rim and the foot of the wall
    pits = np.zeros(shape, np.float32)
    n_p = int(area * 0.12)
    grp = rng.uniform(0, 1, (int(n_p / 8) + 1, 2)) * [shape[1], shape[0]]
    pick = rng.integers(0, len(grp), n_p)
    q_ = grp[pick] + rng.normal(0, 0.8 * pxcm, (n_p, 2))
    for (jx, iy), rp in zip(q_, np.clip(rng.lognormal(np.log(0.011), 0.5, n_p), 0.005, 0.03)):
        if 0 <= int(iy) < shape[0] and 0 <= int(jx) < shape[1]:
            cv2.circle(pits, (int(jx), int(iy)), max(int(rp * pxcm), 1), float(rp), -1, cv2.LINE_AA)
    pits = blur(pits, max(0.004 * pxcm, 0.5))
    return dict(low=low, high=high, I=I_s, Iron=Iron, body=body, t=t, tnom=tnom, crawl=crawl, pits=pits, tot=tot)


def filt(c):
    return np.exp(-c[..., None] * ABS).astype(np.float32)


def flat_view(pxcm):
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE)
    rl = dish.rho_lip
    xs = (np.arange(int(2 * (rl + 0.3) * pxcm), dtype=np.float32) + 0.5) / pxcm - (rl + 0.3)
    ys = (np.arange(int((rl + 8.0) * pxcm), dtype=np.float32) + 0.5) / pxcm - 7.7
    X, Y = np.meshgrid(xs, ys)
    F = fields(X, Y, pxcm, rl)
    col = F["body"] * filt(F["low"]) ** 2 * filt(F["high"]) ** 2 * np.array([0.8, 0.9, 0.92], np.float32)
    col = mix(col, color([0.01, 0.01, 0.02]), 0.8 * sstep(0.3, 0.8, F["I"]))
    col[np.hypot(X, Y) > rl + 0.1] = 0.01
    im = (np.clip(col, 0, 1) ** (1 / 2.2))[::-1, :, ::-1]
    p = os.path.join(d, "flat.jpg")
    cv2.imwrite(p, (im * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(p, im.shape, "rl", rl, flush=True)


def room(path, sp=None):
    """The room as the glaze sees it, in world directions (+y the far side of the dish, the camera on the -y side), an equirectangular float image. Only reflections see it: the white takes its shape from the key light. Painted, a stand-in for a modelled room:
    a tall paned window high on the far left, a smaller one low in front of the camera's mirror line whose image lies flat in the well, a dim ceiling, walls with a slow unevenness, a dark floor."""
    s = {"win": 12.0, "win2": 9.0, "ceil": 0.3, "wall": 0.1, "floor": 0.03, "win_d": (-0.42, 0.42, 0.8), "win_w": 0.1, "win_h": 0.17, "win2_d": (0.07, 0.65, 0.755), "win2_w": 0.017, "win2_h": 0.024, "sheen": 0.0, "sheen_d": (0, 0.7, 0.7), "sheen_s": 0.16, "bar": 0.0, "bar_el": (14.0, 32.0), "bar_az": 72.0}
    s.update(sp or {})
    h, w = 1024, 2048
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)  # Blender's equirect, as in kit.room_env
    un = fbm((h // 4, w // 4), 1.0, 6.0, 200.0, beta=2.6, seed=SEED + 40)
    un = cv2.resize(un, (w, h), interpolation=cv2.INTER_CUBIC)
    E = (s["wall"] * np.exp(0.5 * un))[..., None] * np.array([1.0, 0.985, 0.96], np.float32)
    up = d[..., 2]
    t = sstep(0.35, 0.85, up)[..., None]
    E = E * (1 - t) + (s["ceil"] * np.exp(0.25 * un))[..., None] * np.array([1.0, 0.99, 0.97], np.float32) * t
    t = sstep(-0.05, -0.5, up)[..., None]
    E = E * (1 - t) + s["floor"] * t

    def pane(c, wd, ht, L, rgb, cols, rows, bar=0.035):
        c = np.array(c, float)
        c /= np.linalg.norm(c)
        e1 = np.cross(c, [0.0, 0.0, 1.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(e1, c)
        dc = d @ c.astype(np.float32)
        x = np.where(dc > 0.05, (d @ e1.astype(np.float32)) / np.maximum(dc, 0.05), 9.0) / wd
        y = np.where(dc > 0.05, (d @ e2.astype(np.float32)) / np.maximum(dc, 0.05), 9.0) / ht
        m = sstep(1.0, 0.97, np.abs(x)) * sstep(1.0, 0.98, np.abs(y))
        bx = np.abs(((x + 1.0) * cols / 2.0 + 0.5) % 1.0 - 0.5) / (cols / 2.0)
        by = np.abs(((y + 1.0) * rows / 2.0 + 0.5) % 1.0 - 0.5) / (rows / 2.0)
        m = m * sstep(bar * 0.6, bar * 1.4, bx) * sstep(bar * 0.6 * wd / ht, bar * 1.4 * wd / ht, by)
        grad = 0.7 + 0.4 * y + 0.18 * x  # the sky in the top panes, a building's dull light in the lowest
        return (L * m * grad)[..., None] * np.array(rgb, np.float32)

    E = E + pane(s["win_d"], s["win_w"], s["win_h"], s["win"], [0.94, 0.98, 1.06], 3, 3, bar=0.09)
    if s["win2"]:
        E = E + pane(s["win2_d"], s["win2_w"], s["win2_h"], s["win2"], [0.97, 0.99, 1.03], 2, 3)
    if s["bar"]:  # a long low light behind the dish, seen only by what turns outward: the lip's crest, as one thin unbroken line, and a streak on each side wall
        el_ = np.degrees(np.arcsin(np.clip(up, -1, 1)))
        az_ = np.degrees(np.arctan2(d[..., 0], d[..., 1]))
        m = sstep(s["bar_el"][0] - 2, s["bar_el"][0] + 2, el_) * sstep(s["bar_el"][1] + 2, s["bar_el"][1] - 2, el_) * sstep(s["bar_az"] + 8, s["bar_az"] - 8, np.abs(az_))
        E = E + (s["bar"] * m)[..., None] * np.array([1.0, 0.98, 0.95], np.float32)
    if s["sheen"]:  # a bright overcast sky low in a far window, out of any detail: it lies on the well as a veil, and makes the dark cobalt read as under glass
        c = np.array(s["sheen_d"], np.float32)
        c /= np.linalg.norm(c)
        E = E + (s["sheen"] * np.exp(-0.5 * (np.arccos(np.clip(d @ c, -1, 1)) / s["sheen_s"]) ** 2))[..., None] * np.array([0.96, 0.99, 1.04], np.float32)
    np.save(path, E.astype(np.float32))
    return path


def mirror_to(dish, cam, x, y):
    """The direction in the room whose image in the glaze lies at flat coordinates (x, y)."""
    P = dish.surface(np.array(x, float), np.array(y, float))
    n = dish.normal(np.array(x, float), np.array(y, float))
    v = P - np.array(cam["loc"], np.float32)
    v = v / np.linalg.norm(v)
    return tuple((v - 2 * np.dot(v, n) * n).tolist())


def crop(dish, X, Y, extra=0.7):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def warp(dish, P, X, Y):
    """Thrown by hand and warped in the kiln: no dish is round, and no lip is level."""
    th = np.arctan2(Y, X)
    k = (1.0 + 0.0026 * np.sin(2 * th + 0.7) + 0.0014 * np.sin(3 * th + 2.1) + 0.0006 * np.sin(5 * th + 0.3))[..., None]
    P[..., :2] *= k
    P[..., 2] += (0.05 * np.sin(2 * th + 1.5) + 0.025 * np.sin(3 * th + 0.4) + 0.012 * np.sin(7 * th + 2.0)) * sstep(3.0, dish.rho_lip, np.hypot(X, Y))
    return P


def build(dish, X, Y, pxcm, d, q):
    shape = X.shape
    F = fields(X, Y, pxcm, dish.rho_lip)
    rho = np.hypot(X, Y)
    t = F["t"]
    # the turning rings, in rho: strong in the body, half of them through the glaze
    thr = fbm((32, 4096), 1.0, 60.0, 500.0, 2.4, SEED + 23)[16]  # 0.5 to 4 cm
    rings = np.interp(rho * 120.0, np.arange(4096), thr).astype(np.float32)
    slow = 0.0065 * fbm(shape, pxcm, 2.0, 8.0, 3.4, SEED + 20) + 0.0005 * fbm(shape, pxcm, 0.35, 1.5, 2.4, SEED + 27)
    peel = 0.00009 * fbm(shape, pxcm, 0.1, 0.45, 2.2, SEED + 21)  # slope about .004: at twice this a reflected window shatters into foil over the cobalt
    sink = blur(np.clip(F["tot"], 0, 1.2), max(0.035 * pxcm, 0.5))
    I = F["I"]
        # the surface: fills half way over the body's rings, barely sinks over heavy cobalt (at .00018 the slope bent the window into white slivers on the dark marks), has its pinholes
    top = slow + 0.0006 * rings + F["tnom"] + peel - 0.00003 * sink - F["pits"] * 0.9  # no dent over iron: any dent, however shallow, caught the window and the long light as a white crescent and a grey floor, flakes of foil on a black spot
    rough = 0.04 + 0.018 * rank(fbm(shape, pxcm, 0.3, 2.0, 2.4, SEED + 22)) + 0.02 * sstep(0.3, 0.8, F["Iron"]) + 0.42 * F["crawl"] + 0.05 * sstep(dish.rho_lip - 0.25, dish.rho_lip + 0.1, rho)
    place = lambda x, y, h: warp(dish, dish.surface(x, y, h), x, y)  # noqa: E731
    hb = slow + F["tnom"] - t + 0.0022 * rings - 0.002  # the body: its own rings, below a surface that has mostly levelled them
    Pt = place(X, Y, top)
    ny, nx = shape
    m = max(ny // 4, 16)
    idx = np.round(np.linspace(0, ny - 1, m)).astype(int)
    Pbot = place(X[idx], Y[idx], (hb - 0.035)[idx])
    Pg, at = close_shell(Pt, Pbot, {"rough": np.clip(rough, 0.03, 1).astype(np.float32)}, {"rough": 0.3}, outward=np.array(view_dir(-90.0, EL), np.float32))
    fs = {}

    def save(name, **kw):
        fs[name] = os.path.join(d, f"mesh.{name}.{q}.npz")
        np.savez(fs[name], **kw)

    save("glaze", P=Pg, rough=at["rough"])
    # the main sheet, just above the body; iron in it, a dark scatterer
    tint = filt(F["low"])
    milk = (0.4 * sstep(0.28, 0.75, I)).astype(np.float32)  # with albedo .035 under this key the iron read as grey-brown flakes, paler than the cobalt round it
    save("low", P=place(X, Y, hb + 0.14 * t), tint=tint, milk=milk, mcol=np.broadcast_to(np.array([0.004, 0.004, 0.009], np.float32), shape + (3,)).copy())
    sub = lambda f: cv2.resize(f, (nx // 2, ny // 2), interpolation=cv2.INTER_AREA)  # noqa: E731
    Xs, Ys = sub(X), sub(Y)
    save("high", P=place(Xs, Ys, sub(hb + 0.55 * t)), tint=filt(sub(F["high"])), milk=np.zeros(Xs.shape, np.float32), mcol=np.ones(Xs.shape + (3,), np.float32))
    save("body", P=place(Xs, Ys, sub(hb)), col=sub(F["body"]))
    # bubbles: half in loose swarms, half thinly everywhere, sizes far apart; the area is known from the grid, so the count does not depend on the quality
    rng = np.random.default_rng(SEED + 30)
    x0, x1, y0, y1 = float(X[0, 0]), float(X[0, -1]), float(Y[0, 0]), float(Y[-1, 0])
    n = int((x1 - x0) * (y1 - y0) * 70)
    nc = max(n // 50, 1)
    cx, cy = rng.uniform(x0, x1, nc), rng.uniform(y0, y1, nc)
    pick = rng.integers(0, nc, n // 2)
    bx = np.concatenate([rng.uniform(x0, x1, n - n // 2), cx[pick] + rng.normal(0, 0.28, n // 2)])
    by = np.concatenate([rng.uniform(y0, y1, n - n // 2), cy[pick] + rng.normal(0, 0.28, n // 2)])
    keep = (bx > x0) & (bx < x1) & (by > y0) & (by < y1) & (np.hypot(bx, by) < dish.rho_lip - 0.2)
    bx, by = bx[keep].astype(np.float32), by[keep].astype(np.float32)
    ij = (((by - y0) * pxcm).astype(int).clip(0, ny - 1), ((bx - x0) * pxcm).astype(int).clip(0, nx - 1))
    r = np.clip(rng.lognormal(np.log(0.003), 0.75, bx.size), 0.0012, 0.015).astype(np.float32)
    tb, hbb = t[ij], hb[ij]
    r = np.minimum(r, np.maximum(tb * 0.42, 0.0015))
    hbub = hbb + r + (tb - 2 * r) * rng.random(bx.size).astype(np.float32) ** 0.7
    save("bubble", P=balls(place(bx, by, hbub), r, nlon=8, nlat=6))
    print("bubbles", bx.size, flush=True)
    return fs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    q = args[0] if args else "preview"
    if q == "flat":
        flat_view(float(args[1]) if len(args) > 1 else 60.0)
        return
    draft = q == "draft"
    q = "final" if draft else q
    dens = {"preview": 0.42, "mid": 0.65, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE)
    cam, sag = dish.camera(W, EL, DIST, apex=APEX, aperture_mm=float(opts.get("ap", 5.0)), focus_rho=float(opts.get("focus", 11.6)))
    print("sag", round(float(sag), 3), "lens", round(cam["lens_mm"], 1), flush=True)
    pxcm = 230.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.14))  # the margin is for the dish's turn
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    fs = build(dish, X, Y, pxcm, d, q)
    # --set=a:sheen=0,ev=.6/b:win=20 tries several rooms and lights on one set of meshes, one after the other: the meshes are the slow part. A slash, because the shell would split on a semicolon
    sets = [v.split(":", 1) for v in opts["set"].split("/")] if opts.get("set") else [[opts.get("tag") or ("draft" if draft else "cand" if q == "final" else q), ""]]
    for tag, kv in sets:
        o = {**opts, **dict(x.split("=", 1) for x in kv.split(",") if x)}
        env = room(os.path.join(d, f"room.{tag}.npy"), {
            "win": float(o.get("win", 10.0)),
            "win_w": float(o.get("ww", 0.14)),
            "win_h": float(o.get("wh", 0.42)),
            "bar": float(o.get("bar", 12.0)),
            "win2": float(o.get("win2", 0.0)),
            "win2_w": float(o.get("w2w", 0.013)),
            "win2_h": float(o.get("w2h", 0.019)),
            "win_d": mirror_to(dish, cam, *(uv(np.radians(float(o.get("wa", 72)))) * float(o.get("wr", 12.7)))),
            "win2_d": mirror_to(dish, cam, float(o.get("w2x", 6.6)), float(o.get("w2y", 2.6))),
            "sheen_d": mirror_to(dish, cam, -3.5, 4.0),
            "sheen": float(o.get("sheen", 0.3)),
        })
        ss = float(o.get("ss", 1.0))
        glaze = {**GLAZE, "sigma_s": [v * ss for v in GLAZE["sigma_s"]]}
        scene = {
            "camera": dict(cam),
            "meshes": [
                {"name": "glaze", "npz": fs["glaze"], "shader_py": GLAZE_SHADER, "params": {k: v for k, v in glaze.items() if k != "kind"}},
                {"name": "low", "npz": fs["low"], "shader_py": SHADER, "params": {"kind": "layer"}},
                {"name": "high", "npz": fs["high"], "shader_py": SHADER, "params": {"kind": "layer"}},
                {"name": "body", "npz": fs["body"], "material": {"Base Color": "col", "Roughness": 0.55, "Specular IOR Level": 0.0}},
                {"name": "bubble", "npz": fs["bubble"], "shader_py": SHADER, "params": {"kind": "bubble"}, "visible": {"shadow": False}},
            ],
            "lights": [
                # the key is low on the left, so the white falls away across the dish and the left lip throws a soft shadow; a weak fill from the near side, for the far wall that faces the camera; neither appears in the glaze: the room does that
                {"name": "key", "loc": [-88.0, 28.0, 72.0], "target": [0.0, 4.0, 1.0], "size": [70, 70], "watts": float(o.get("key", 165000)), "rgb": [0.98, 0.99, 1.0], "hide_in_gloss": True},
                {"name": "fill", "loc": [30.0, -70.0, 90.0], "target": [0.0, 9.0, 1.0], "size": [110, 110], "watts": float(o.get("fill", 11000)), "rgb": [0.97, 0.985, 1.0], "hide_in_gloss": True},
            ],
            "env": {"npy": env, "diffuse": False, "transmission": True},
            "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.02, 0.0195, 0.019], "h": 0.62, "mottle": 0.12, "x0": 0.42, "y0": 0.52, "seed": 50},
            "world": [0.0, 0.0, 0.0],
            "bounces": 48,
            "volume_bounces": 32,
            "transmission_bounces": 48,
            "diffuse_bounces": 6,
            "glossy_bounces": 6,
            "spp": {"preview": int(o.get("spp", 96)), "mid": int(o.get("spp", 192)), "final": int(o.get("spp", 48 if draft else 640))},
        }
        shoot(NAME, scene, q, tag=tag, develop={"exposure": float(o.get("ev", 0.72)), "contrast": 1.22, "saturation": 1.0, "black": 0.001, "grain": 1.1, "sharpen": 0.25, "halation": 0.05, "glare": 0.004, "vignette": 0.22})


main()
