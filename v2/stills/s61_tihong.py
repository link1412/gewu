"""Shot 61: tihong (剔红), a Yongle-style carved red lacquer dish with one big peony. Its far lip is the arc.

    python3 -I v2/stills/s61_tihong.py flat                 local only: flat.jpg, flat_frame.jpg, flat_height.jpg in out/v2/s61_tihong/
    python3 -I v2/stills/s61_tihong.py [preview|mid|final]

Compared with ref/carved_lacquer (reference only, no pixel of them is in the film): met/DT2677 (Yuan, Zhang Cheng attr.: rolled petal rims, dense fine radial
veins from the base, knife-cut walls, palmate leaves in separate lancets, dark ground with dust at the foot of each form), cma/1918.933 (soft swelling, cracks across the forms).

Estimates and stand-ins, all of them ours:
- dish diameter 26 cm: an estimate from the range of such dishes; the Met's measured one is 32.4 cm. No Yongle piece is in ref/.
- carved depth of about 8 mm: an estimate. The Met's dish lists H. 0.3 cm, which is evidently not the depth of the carving, so nothing measured backs this.
- the ground: a smooth dark olive-ochre lacquer, chosen by eye towards the Yuan dish in ref/ (dark olive-brown). Yongle yellow grounds are from memory and no photo in ref/ shows one, so it is not used.
- layer pitch 0.12 mm: an estimate, as in s10.
- the design of the flower is ours, not traced from any object.
- the polish is a stand-in: a clear Principled coat, weight and roughness mapped per vertex, in place of measured lacquer. The knife-mark depths (about 0.05-0.15 mm) are estimates.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numba
import numpy as np

from dishkit import Dish
from kit import OUT, camera_path, fbm, mix, rank, shoot, sstep

NAME = "s61_tihong"


RING = 11.45  # flat radius a leaf may reach: the cavetto band starts just outside
W = 13.6
EL = 30.0
DIST = 42.0
PROFILE = [(11.8, -0.5), (12.75, 0.2), (13.02, 0.62), (13.06, 0.74), (12.98, 0.8), (12.86, 0.77), (12.76, 0.66), (12.1, 0.33), (11.6, 0.14), (11.1, 0.045), (10.5, 0.01), (9.6, 0.0), (0.0, 0.0)]
C = np.array([-0.35, 7.1])  # the heart of the flower, flat coordinates
GRID_PXCM = {"measure": 215.0, "flat": 100.0, "preview": 140.0, "mid": 215.0, "final": 215.0}
FOCUS_RHO = 8.6
APERTURE = 5.0  # mm


# --- strokes ------------------------------------------------------------------------------------------------------
@numba.njit(cache=True)
def _stamp(buf, xs, ys, ws, ds, asym):
    """A slanted V cut along a polyline: one bank steep, the other gentle (asym in -1..1, its sign picks the side). Merged by maximum. All in pixels (d is any unit)."""
    ny, nx = buf.shape
    for i in range(xs.size):
        w = ws[i]
        if w < 0.25:
            continue
        j0, j1 = max(i - 1, 0), min(i + 1, xs.size - 1)
        tx, ty = xs[j1] - xs[j0], ys[j1] - ys[j0]
        tl = np.sqrt(tx * tx + ty * ty) + 1e-9
        n_x, n_y = -ty / tl, tx / tl
        reach = w * (1.0 + abs(asym))
        x0, x1 = max(int(xs[i] - reach) - 1, 0), min(int(xs[i] + reach) + 2, nx)
        y0, y1 = max(int(ys[i] - reach) - 1, 0), min(int(ys[i] + reach) + 2, ny)
        for y in range(y0, y1):
            for x in range(x0, x1):
                ax, ay = x + 0.5 - xs[i], y + 0.5 - ys[i]
                r = np.sqrt(ax * ax + ay * ay)
                c = (ax * n_x + ay * n_y) / (r + 1e-9)
                v = ds[i] * (1.0 - r / (w * (1.0 + asym * c)))
                if v > buf[y, x]:
                    buf[y, x] = v


def stroke(buf, pts, hw, dep, pxcm, org, asym=0.45):
    """Polyline pts (cm) with half width hw and depth dep (cm, per point), resampled to under a pixel."""
    pts = np.asarray(pts, np.float64)
    if len(pts) < 2:
        return
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    if s[-1] <= 0:
        return
    t = np.arange(0.0, s[-1], 0.7 / pxcm)
    xs = (np.interp(t, s, pts[:, 0]) - org[0]) * pxcm
    ys = (np.interp(t, s, pts[:, 1]) - org[1]) * pxcm
    _stamp(buf, xs, ys, np.interp(t, s, hw) * pxcm, np.interp(t, s, dep), float(asym))


def wob(rng, n=4, fmax=3.0):
    """A smooth hand-wobble on [0, 1], about unit size."""
    f = rng.uniform(0.4, fmax, n)
    a = rng.normal(0, 1, n) / np.sqrt(n) / (0.5 + f / fmax)
    p = rng.uniform(0, 6.283, n)
    return lambda t: sum(a[i] * np.sin(6.283 * f[i] * np.asarray(t) + p[i]) for i in range(n))


def arc_edge(d, D):
    """A round section (stems, beads)."""
    t = np.clip(d / D, 0.0, 1.0)
    return np.sqrt(1.0 - (1.0 - t) ** 2)


def sdist(m):
    """Signed distance to the outline of a mask, in pixels, with the staircase of the raster smoothed out."""
    a = cv2.distanceTransform(np.pad(m, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    b = cv2.distanceTransform(np.pad(1 - m, 1, constant_values=1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    return cv2.GaussianBlur((a - b).astype(np.float32), (0, 0), 1.1, borderType=cv2.BORDER_REPLICATE)


def dist_in(m, p):
    return np.maximum(sdist(m), 0.0) / p


def cut_edge(d, bevel=0.009):
    """A knife wall: near vertical, the arris eased by about bevel cm (0.1-0.2 mm) and no more."""
    return sstep(0.0, bevel, d)


def field(shape, p, lo, hi, beta, seed, c=8):
    """Slow noise on a coarse isotropic grid, wavelengths in cm."""
    ny, nx = shape
    f = fbm((max(ny // c, 16), max(nx // c, 16)), p / c, lo, hi, beta, seed)
    return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)


# --- the sheet everything is carved on ---------------------------------------------------------------------------
class Sheet:
    def __init__(self, x0, y0, nx, ny, pxcm, fast=False):
        self.fast = fast  # a plan on a coarse grid: outlines only, no knife work
        self.org, self.pxcm, self.shape = (x0, y0), pxcm, (ny, nx)
        self.H = np.zeros((ny, nx), np.float32)  # carved height over the ground, no fine cuts
        self.V = np.zeros((ny, nx), np.float32)  # depth of the fine knife cuts
        self.red = np.zeros((ny, nx), np.float32)  # 1 where red lacquer is left standing
        self.idv = np.zeros((ny, nx), np.float32)  # a value per element: each was carved on its own
        self.undercut = np.zeros((ny, nx), np.float32)

    def roi(self, pts, pad):
        x, y = pts[:, 0], pts[:, 1]
        p = self.pxcm
        x0 = max(int((x.min() - pad - self.org[0]) * p), 0)
        x1 = min(int((x.max() + pad - self.org[0]) * p) + 1, self.shape[1])
        y0 = max(int((y.min() - pad - self.org[1]) * p), 0)
        y1 = min(int((y.max() + pad - self.org[1]) * p) + 1, self.shape[0])
        if x1 - x0 < 4 or y1 - y0 < 4:
            return None
        X, Y = np.meshgrid(self.org[0] + (np.arange(x0, x1) + 0.5) / p, self.org[1] + (np.arange(y0, y1) + 0.5) / p)
        return (y0, y1, x0, x1), X.astype(np.float32), Y.astype(np.float32)

    def mask(self, r, pts):
        (y0, y1, x0, x1) = r
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        q = np.round((pts - np.array(self.org)) * self.pxcm * 16 - np.array([x0, y0]) * 16 - 8).astype(np.int32)
        cv2.fillPoly(m, [q.reshape(-1, 1, 2)], 1, lineType=cv2.LINE_8, shift=4)
        return m

    def place(self, r, m, h, v, idv, groove=0.03, groove_w=0.022, wall=0.07, wall_w=0.035, climb=1.1):
        """Lay one element over what is there. Beside it the carver sinks what lies below: the clean, hidden line of 藏锋清楚."""
        (y0, y1, x0, x1) = r
        k = m > 0
        p = self.pxcm
        dout = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5) / p
        H = self.H[y0:y1, x0:x1]
        # what lies below is cut down to pass under this edge by at least `wall`, and climbs back at `climb`: that is how a carver makes one form lie under another
        sg = max(wall_w * p, 1.0)
        ek = cv2.GaussianBlur((h * m).astype(np.float32), (0, 0), sg, borderType=cv2.BORDER_REPLICATE) / np.maximum(cv2.GaussianBlur(m.astype(np.float32), (0, 0), sg, borderType=cv2.BORDER_REPLICATE), 1e-3)
        band = wall / climb + 1.2 * wall_w
        cap = ek - wall + climb * dout
        H[:] = H - np.maximum(H - cap, 0.0) * sstep(band, band * 0.35, dout)
        H[:] = np.maximum(H - groove * np.exp(-dout / groove_w), 0.0)
        al = np.clip(sdist(m) / 1.4 + 0.5, 0.0, 1.0)  # coverage: the wall does not step along the raster
        H[:] = H * (1.0 - al) + h * al
        self.V[y0:y1, x0:x1][k] = v[k]
        R_ = self.red[y0:y1, x0:x1]
        R_[:] = np.maximum(R_, al)
        self.idv[y0:y1, x0:x1][k] = idv


def drape(sh, r, clearance, floor, sigma=0.3):
    """What an element lies on: the blurred carving below it, plus a clearance, never under floor."""
    (y0, y1, x0, x1) = r
    b = cv2.GaussianBlur(sh.H[y0:y1, x0:x1], (0, 0), sigma * sh.pxcm, borderType=cv2.BORDER_REPLICATE)
    return floor + 0.22 * np.maximum(b + clearance - floor, -0.1)


# --- a petal: one by one, nothing copied ------------------------------------------------------------------------
def petal(sh, B, ang, L, Al, Ar, thick, floor, seed, k=1.0, curl=0.0, nveins=None, notches=None, clearance=0.1, groove=0.05):
    """Fan-shaped petal from base B along angle ang (radians) with length L, half angles Al (+) and Ar (-). k scales its details (1 for a big petal)."""
    rng = np.random.default_rng(seed)
    n = 720
    al = np.linspace(-Ar, Al, n)
    x = np.where(al >= 0, al / Al, al / Ar)  # -1..1 on each side
    pw = rng.uniform(2.1, 3.2)
    sh_x = np.clip(np.abs(x), 0, 1)
    env = (1.0 - sh_x**pw) ** rng.uniform(0.42, 0.62)
    # an obovate outline: its shoulders are off centre and not equal
    env = env * (1.0 + rng.uniform(-0.1, 0.1) * x + rng.uniform(-0.05, 0.08) * np.cos(x * 3.1))
    t = np.linspace(0, 1, n)
    env = env * (1.0 + 0.045 * wob(rng, 5, 3.5)(t))
    # the torn tip: a few deep notches, unevenly spaced, and small ones between them
    if notches is None:
        notches = rng.integers(3, 8)
    cuts = np.sort(rng.uniform(-0.86, 0.86, notches) + rng.normal(0, 0.02, notches))
    cuts = cuts[cuts < 0.95]
    notches = cuts.size
    # keep them from crowding, but do not regularise
    for i in range(1, notches):
        if cuts[i] - cuts[i - 1] < 0.1:
            cuts[i] = cuts[i - 1] + rng.uniform(0.1, 0.24)
    # the edge is cut as convex scallops that meet in a sharp point, the way a knife goes round each lobe
    edges = np.r_[-1.05, cuts, 1.05]
    dcut = np.r_[0.0, rng.uniform(0.025, 0.1, notches), 0.0]
    rough = np.ones(n)
    pleat = np.zeros(n)
    for j, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        z = (x >= a) & (x < b)
        m_, hw_ = (a + b) / 2, (b - a) / 2
        arch = np.sqrt(np.clip(1.0 - ((x[z] - m_) / hw_) ** 2, 0.0, 1.0))
        dd = np.interp(x[z], [a, b], [dcut[j], dcut[j + 1]])
        rough[z] = 1.0 - dd * (1.0 - arch)
        pleat[z] += rng.uniform(0.25, 0.8) * arch  # the blade swells between the folds; the fold itself is a hard crease at the cut
        for _ in range(rng.integers(0, 4)):  # a small second cut on the lobe
            c = rng.uniform(a + 0.1 * (b - a), b - 0.1 * (b - a))
            rough -= rng.uniform(0.008, 0.032) * np.exp(-np.abs(x - c) / rng.uniform(0.008, 0.018))
    rho = L * env * rough
    ca, sa = np.cos(ang), np.sin(ang)
    # the petal leans: the whole outline is sheared as it goes out, so that its axis is not straight
    bend = rng.uniform(-0.1, 0.1)
    a2 = al + bend * (rho / L) ** 2
    px, py = rho * np.cos(a2), rho * np.sin(a2)
    pts = np.stack([B[0] + ca * px - sa * py, B[1] + sa * px + ca * py], 1)
    tip_pt = pts[np.argmin(np.abs(al))]
    r = sh.roi(pts, 0.35)
    if r is None:
        return tip_pt
    box, X, Y = r
    m = sh.mask(box, pts)
    if m.sum() < 8:
        return tip_pt
    p = sh.pxcm
    d = dist_in(m, p)
    dx, dy = X - B[0], Y - B[1]
    lx, ly = ca * dx + sa * dy, -sa * dx + ca * dy
    rr = np.hypot(lx, ly)
    aa = np.arctan2(ly, lx) - bend * np.clip(rr / L, 0, 1) ** 2
    rho_e = np.interp(aa, al, np.maximum(rho, 1e-3)).astype(np.float32)
    q = np.clip(rr / rho_e, 0.0, 1.2)
    xp = np.where(aa >= 0, aa / Al, aa / Ar).astype(np.float32)
    xp = np.clip(xp, -1, 1)
    pl = np.interp(xp, x, pleat).astype(np.float32)
    # the form of the top
    base = drape(sh, box, clearance, floor)
    swell = rng.uniform(0.04, 0.1) * (0.2 + 0.8 * k)
    droop = rng.uniform(0.03, 0.12) * k
    tilt = rng.uniform(-0.2, 0.2) * k
    cross = 1.0 - np.minimum(xp**2, 1.0)
    hump = np.sin(np.pi * np.clip(q * 0.9, 0, 1))
    top = swell * hump * (0.45 + 0.55 * cross) - droop * q**1.6 + tilt * xp * q + rng.uniform(0.045, 0.1) * k * pl * sstep(0.25, 0.85, q)
    ch = rng.uniform(0.0, 0.06) * k
    top = top - ch * np.exp(-np.abs(xp) / rng.uniform(0.06, 0.14)) * sstep(0.1, 0.5, q) * sstep(1.0, 0.7, q)
    # a shallow bowl in most big petals: the middle of the blade sinks, the rim stands, as on the Met's hibiscus
    bowl = rng.uniform(0.0, 0.13) * k * (rng.random() < 0.75)
    top = top - bowl * np.exp(-((xp / 0.62) ** 2)) * np.exp(-(((q - rng.uniform(0.58, 0.74)) / 0.27) ** 2))
    # the edge: a clean wall. A lip is only here and there, narrow, and on few petals; a third swell like a pillow instead
    tip = sstep(0.4, 0.85, q)
    pillow = rng.random() < 0.32 and k > 0.4
    if pillow:
        top = top + (swell * 0.8 + bowl) * hump * cross
    rm = np.interp(xp, x, np.clip(0.75 * wob(rng, 6, 3.2)(t), 0.0, 1.25)).astype(np.float32)  # zero over about half of the edge
    roll_h = (0.0 if pillow else (rng.uniform(0.008, 0.028) + 0.25 * curl)) * (0.4 + 0.6 * k)
    roll = roll_h * rm * np.exp(-np.abs(d - 0.05) / 0.045) * tip
    bev = 0.0075 * (0.6 + 0.4 * k)
    h = base + (thick * cut_edge(d, bev) + np.minimum(d / (bev * 1.3), 1.0) * top) + roll
    h = np.maximum(h, 0.015).astype(np.float32)
    # veins: a system of fine, nearly parallel cuts fanning from the base, 0.15-0.3 mm wide and shallow. As the fan widens new ones start between the old ones.
    # Each still has its own start, end and pressure; a few are heavier, a few fork, a few break off
    v = np.zeros(m.shape, np.float32)
    arc = 0.8 * L * (Al + Ar)
    spacing = rng.uniform(0.062, 0.085) * (0.55 + 0.45 * k)
    nall = int(arc / spacing) if nveins is None else int(nveins)
    if sh.fast:
        nall = 0
    if nall > 0:
        org = (sh.org[0] + box[2] / p, sh.org[1] + box[0] / p)
        xs = (np.arange(nall) + 0.5) / nall * 1.9 - 0.95
        xs = np.clip(xs + 0.07 * wob(rng, 4, 2.2)((xs + 1) / 2) + rng.normal(0, 0.3 * 1.9 / nall, nall), -0.97, 0.97)  # the fan bunches and opens: not equal spacing
        late = nveins is None
        bank = rng.choice([-1.0, 1.0])  # one hand, one tilt of the blade across the petal
        for iv, xi in enumerate(xs):
            if rng.random() < 0.09:
                continue
            sec = late and iv % 2 == 1
            q0 = rng.uniform(0.5, 0.72) if sec else rng.uniform(0.18, 0.42)
            q1 = rng.uniform(0.86, 0.975) if rng.random() > 0.22 else rng.uniform(0.6, 0.86)
            w0 = rng.lognormal(np.log(0.0118), 0.36) * (0.62 + 0.38 * k) * (0.85 if sec else 1.0)
            kind = rng.random()
            if kind < 0.12:
                w0 *= 1.6
            elif kind < 0.3:
                w0 *= 0.62
            ai = xi * (Al if xi >= 0 else Ar)
            f = wob(rng, 3, 1.8)
            qs = np.linspace(q0, q1, 60)
            am = ai + 0.006 * f(qs)
            pxs = qs * np.interp(am, al, rho)
            a_ = am + bend * (pxs / L) ** 2
            ax, ay = pxs * np.cos(a_), pxs * np.sin(a_)
            P = np.stack([B[0] + ca * ax - sa * ay, B[1] + sa * ax + ca * ay], 1)
            u = (qs - q0) / (q1 - q0)
            # the blade goes in hard and lifts out: deep at the start, shallow at the end. Some are cut from the rim inwards
            press = 0.85 + 0.15 * wob(rng, 3, 2.5)(u)
            e = sstep(0.0, rng.uniform(0.025, 0.07), u) * (1.0 - u) ** rng.uniform(0.3, 0.95)
            hw = w0 * np.maximum(e, 0.0) ** 0.55 * press
            dep = hw * rng.lognormal(np.log(0.7), 0.3) * (0.45 + 0.55 * e)
            if rng.random() < 0.38:  # the knife lifted in the tail
                gap = sstep(0, 0.012, np.abs(u - rng.uniform(0.5, 0.88)) - rng.uniform(0.015, 0.06))
                hw, dep = hw * gap, dep * gap
            if rng.random() < 0.12:  # and once early
                gap = sstep(0, 0.01, np.abs(u - rng.uniform(0.2, 0.5)) - rng.uniform(0.008, 0.025))
                hw, dep = hw * gap, dep * gap
            if rng.random() < 0.22:
                hw, dep = hw[::-1], dep[::-1]
            stroke(v, P, hw, dep, p, org, asym=0.62 * bank * (-1.0 if rng.random() < 0.08 else 1.0))
            if rng.random() < 0.06:  # a fork near the end
                i0 = int(rng.uniform(0.5, 0.75) * 60)
                n1 = 60 - i0
                am2 = am[i0:] + np.linspace(0, 1, n1) ** 1.2 * rng.uniform(0.02, 0.05) * rng.choice([-1.0, 1.0])
                p2 = qs[i0:] * np.interp(am2, al, rho)
                a2_ = am2 + bend * (p2 / L) ** 2
                ax2, ay2 = p2 * np.cos(a2_), p2 * np.sin(a2_)
                P2 = np.stack([B[0] + ca * ax2 - sa * ay2, B[1] + sa * ax2 + ca * ay2], 1)
                hw2 = 0.75 * w0 * np.sin(np.pi * (0.1 + 0.9 * np.linspace(0, 1, n1))) ** 0.6
                stroke(v, P2, hw2, hw2 * 0.7, p, org)
        v = v * sstep(0.015, 0.05, d)
    sh.place(box, m, h, v, rng.random(), groove=groove, wall=0.012 + 0.08 * k, wall_w=0.012 + 0.03 * k)
    return tip_pt


# --- a leaf lobe ---------------------------------------------------------------------------------------------------
def lancet(sh, root, ang, L, wd, thick, floor, seed, k=1.0, bend=None, teeth=True, nside=None, mid=True, clearance=0.05, groove=0.035, fold_side=0):
    """One lobe of a leaf: a curved spine, a toothed outline, a midrib, side veins. Height is a low roof that tips one way."""
    rng = np.random.default_rng(seed)
    n = 240
    t = np.linspace(0, 1, n)
    bend = rng.uniform(-0.45, 0.45) if bend is None else bend
    th = ang + bend * t**1.3 + 0.05 * wob(rng, 3, 1.5)(t)
    sx = np.r_[0.0, np.cumsum(np.cos(th[:-1]))] * L / (n - 1)
    sy = np.r_[0.0, np.cumsum(np.sin(th[:-1]))] * L / (n - 1)
    sp = np.stack([root[0] + sx, root[1] + sy], 1)
    nrm = np.stack([-np.sin(th), np.cos(th)], 1)
    peak = rng.uniform(0.28, 0.45)
    prof = np.sin(np.pi * np.clip(t, 0, 1) ** (np.log(0.5) / np.log(peak))) ** rng.uniform(0.62, 0.82)

    def side(sgn):
        w = wd * prof * (1.0 + 0.07 * wob(rng, 3, 2.5)(t))
        if teeth:
            # teeth lean towards the tip: slow rise, sudden drop; none the same
            T = rng.uniform(0.45, 0.85) * (0.45 + 0.55 * k)
            pos, s = rng.uniform(0.12, 0.28), []
            while pos < 0.97:
                s.append(pos)
                pos += rng.uniform(0.09, 0.2) / max(L / 3.0, 0.5)
            for c in s:
                wdt, a = rng.uniform(0.05, 0.13) / max(L / 3.0, 0.5), rng.uniform(0.06, 0.2) * T * wd
                up = (t - (c - wdt)) / wdt
                w = w + a * np.where((up > 0) & (up < 1), np.clip(up, 0, 1) ** 1.6, 0.0) * (1.0 - t * 0.4)
        return sp + nrm * sgn * w[:, None]

    pts = np.concatenate([side(1.0), side(-1.0)[::-1]], 0)
    # a nibble out of the edge in some, as a real leaf has
    r = sh.roi(pts, 0.3)
    if r is None:
        return
    box, X, Y = r
    m = sh.mask(box, pts)
    if m.sum() < 8:
        return
    p = sh.pxcm
    d = dist_in(m, p)
    # distance to the spine, and where along it
    from scipy.spatial import cKDTree

    n_f = max(int(L / 0.003), n)
    t_f = np.linspace(0, 1, n_f)
    sp_f = np.stack([np.interp(t_f, t, sp[:, 0]), np.interp(t_f, t, sp[:, 1])], 1)
    tree = cKDTree(sp_f)
    ys, xs = np.nonzero(m)
    grid_s = np.zeros(m.shape, np.float32)
    grid_o = np.zeros(m.shape, np.float32)
    grid_side = np.zeros(m.shape, np.float32)
    dist, i = tree.query(np.stack([X[ys, xs], Y[ys, xs]], 1), workers=-1)
    grid_s[ys, xs] = t_f[i]
    grid_o[ys, xs] = dist
    i2 = np.clip((t_f[i] * (n - 1)).astype(int), 0, n - 1)
    dv = np.stack([X[ys, xs] - sp_f[i, 0], Y[ys, xs] - sp_f[i, 1]], 1)
    grid_side[ys, xs] = np.sign((dv * nrm[i2]).sum(1))
    # a roof over the spine: one half higher than the other, the tip dropping
    base = drape(sh, box, clearance, floor, 0.2)
    tip_drop = rng.uniform(0.04, 0.16) * k
    tiltv = rng.uniform(0.05, 0.14) * rng.choice([-1, 1]) * k
    o = grid_o / max(wd, 0.05)
    hroof = thick * 0.35 * (np.exp(-((o * 1.25) ** 2))) + tiltv * grid_side * np.minimum(o, 1.2) - tip_drop * grid_s**2
    midrib = rng.uniform(0.012, 0.026) * k * np.exp(-grid_o / (0.02 + 0.012 * k)) * (1.0 - grid_s * 0.7)
    bev = 0.014 * (0.6 + 0.4 * k)
    h = base + thick * 0.5 * cut_edge(d, bev) + np.minimum(d / (bev * 1.3), 1.0) * hroof - (midrib if mid else 0.0)
    if fold_side:
        # the edge of a lobe curled up and over, on one side only and for part of the length
        s0 = rng.uniform(0.3, 0.55)
        zone = np.exp(-(((grid_s - s0) / rng.uniform(0.14, 0.26)) ** 2)) * (grid_side == fold_side)
        h = h + zone * rng.uniform(0.03, 0.07) * np.exp(-d / 0.09)
    h = np.maximum(h, 0.012).astype(np.float32)
    v = np.zeros(m.shape, np.float32)
    org = (sh.org[0] + box[2] / p, sh.org[1] + box[0] / p)
    if mid and not sh.fast:
        hw = (0.009 + 0.004 * k) * (1.0 - t) ** 0.5 * (0.85 + 0.15 * wob(rng, 3, 3)(t))
        stroke(v, sp + 0.002, hw, hw * 0.9, p, org)
    ns = nside if nside is not None else 60
    for sgn in (1.0, -1.0):
        if sh.fast:
            break
        pos = rng.uniform(0.05, 0.14)
        for _ in range(ns):
            if pos > 0.9:
                break
            i0 = int(pos * (n - 1))
            lv = wd * prof[i0] * rng.uniform(0.8, 0.97)
            step = rng.uniform(0.17, 0.3) * (0.5 + 0.5 * k) / max(L, 0.8)
            if lv < 0.05:
                pos += step
                continue
            aout = th[i0] + sgn * rng.uniform(0.5, 0.78)
            cv = rng.uniform(-0.28, -0.05) * sgn
            uu = np.linspace(0, 1, 22)
            aa = aout + cv * uu
            P = sp[i0] + np.stack([np.cumsum(np.cos(aa)), np.cumsum(np.sin(aa))], 1) * lv / 21
            hw2 = rng.lognormal(np.log(0.0085), 0.2) * (0.62 + 0.38 * k) * np.sin(np.pi * (0.04 + 0.96 * uu) ** 0.75) ** 0.55
            stroke(v, P, hw2, hw2 * rng.uniform(0.65, 0.9), p, org)
            if k > 0.35:  # the fine hatching between two side veins
                for _ in range(int(rng.integers(1, 4))):
                    i1 = int(np.clip(pos + rng.uniform(0.2, 0.85) * step, 0, 0.95) * (n - 1))
                    lt = wd * prof[i1] * rng.uniform(0.35, 0.8)
                    if lt < 0.05:
                        continue
                    a0 = th[i1] + sgn * rng.uniform(0.5, 0.78)
                    off = rng.uniform(0.1, 0.5) * lt
                    Pt = sp[i1] + np.outer(np.linspace(off, off + lt * 0.6, 10), r2d(a0))
                    hw3 = rng.uniform(0.0048, 0.0065) * np.sin(np.linspace(0.15, 3.0, 10)) ** 0.6
                    stroke(v, Pt, hw3, hw3 * 0.7, p, org)
            pos += step
    v = v * sstep(0.015, 0.045, d)
    sh.place(box, m, h, v, rng.random(), groove=groove, wall=0.012 + 0.05 * k, wall_w=0.012 + 0.025 * k)


def leaf(sh, root, ang, L, seed, floor=0.14, k=1.0, wd=None):
    """A peony leaf: a petiole and three lobes laid one by one. The side lobes go first, the middle one over them."""
    rng = np.random.default_rng(seed)
    wd = L * rng.uniform(0.17, 0.23) if wd is None else wd
    fork = np.array(root) + np.array([np.cos(ang), np.sin(ang)]) * L * rng.uniform(0.1, 0.2)
    order = [-1, 1] if rng.random() < 0.5 else [1, -1]
    for s in order:
        a = ang + s * rng.uniform(0.52, 0.92)
        Ls = L * rng.uniform(0.55, 0.78)
        while np.hypot(*(fork + r2d(a) * Ls)) > RING and Ls > 0.8:
            Ls *= 0.93
        lancet(sh, fork, a, Ls, wd * rng.uniform(0.72, 0.95), 0.1 * (0.6 + 0.4 * k), floor, seed * 7 + s + 100, k=k, bend=s * rng.uniform(-0.45, 0.1), fold_side=int(rng.choice([0, 0, 1, -1])))
    lancet(sh, root, ang, L, wd, 0.12 * (0.6 + 0.4 * k), floor + 0.02, seed * 7 + 300, k=k, fold_side=int(rng.choice([0, 1, -1])))


def stem(sh, pts, hw0, seed, floor=0.1):
    """A stem as a rounded ridge: a hand-drawn spline of width hw0."""
    rng = np.random.default_rng(seed)
    pts = np.array(pts, float)
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    t = np.linspace(0, s[-1], 400)
    from scipy.interpolate import CubicSpline

    sp = CubicSpline(s, pts)(t)
    dv = np.gradient(sp, axis=0)
    dv /= np.linalg.norm(dv, axis=1, keepdims=True)
    nr = np.stack([-dv[:, 1], dv[:, 0]], 1)
    wv = hw0 * (1.0 + 0.1 * wob(rng, 3, 2)(t / s[-1])) * np.interp(t / s[-1], [0, 1], [1.0, 0.65])
    outline = np.concatenate([sp + nr * wv[:, None], (sp - nr * wv[:, None])[::-1]], 0)
    r = sh.roi(outline, 0.25)
    if r is None:
        return
    box, X, Y = r
    m = sh.mask(box, outline)
    if m.sum() < 8:
        return
    d = dist_in(m, sh.pxcm)
    base = drape(sh, box, 0.03, floor, 0.12)
    h = base + 0.1 * arc_edge(d, hw0)
    sh.place(box, m, h.astype(np.float32), np.zeros(m.shape, np.float32), rng.random(), groove=0.02)


# --- the design: every placement is written out by hand and then jittered -----------------------------------------
def r2d(a):
    return np.array([np.cos(a), np.sin(a)])


def flower_outer_scale(a):
    """The flower is wider than it is deep, to fill the frame's width under the far lip."""
    return 0.86 + 0.44 * np.cos(a) ** 2


def small_flower(sh, c, R, seed, floor=0.2):
    """A half-open side flower, tier on tier, with its own veins."""
    rng = np.random.default_rng(seed)
    c = np.array(c, float)
    sd = seed * 10
    for ti, (n, Lk, A, thick, fl, k) in enumerate([(6, 1.0, 0.64, 0.055, 0.0, 0.26), (5, 0.72, 0.76, 0.05, 0.05, 0.22), (4, 0.46, 0.92, 0.04, 0.095, 0.16)]):
        off = rng.uniform(0, 6.28)
        for j in rng.permutation(n):
            sd += 1
            a = off + 6.283 * (j + rng.normal(0, 0.14)) / n
            petal(sh, c + r2d(a) * 0.1 * R, a, R * Lk * rng.uniform(0.88, 1.12), A * rng.uniform(0.85, 1.15), A * rng.uniform(0.85, 1.15), thick, floor + fl, sd, k=k, notches=int(rng.integers(1, 4)), groove=0.018)
    bead(sh, c, 0.06 * R + 0.015, floor + 0.13)


def bud(sh, c, ang, L, seed, floor=0.2):
    """A closed bud: sepals below, petals lapped over one another."""
    rng = np.random.default_rng(seed)
    c = np.array(c, float)
    for s, sg in enumerate((-1.0, 1.0)):
        lancet(sh, c, ang + sg * rng.uniform(0.35, 0.6), L * rng.uniform(0.75, 0.95), L * 0.16, 0.05, floor, seed * 10 + s, k=0.3, bend=sg * rng.uniform(-0.6, -0.1), teeth=False, nside=8)
    for j, (off, Lk, A) in enumerate([(-0.28, 0.86, 0.46), (0.3, 0.9, 0.44), (-0.08, 1.0, 0.5), (0.1, 0.8, 0.36)]):
        petal(sh, c, ang + off + rng.normal(0, 0.04), L * Lk * rng.uniform(0.95, 1.05), A, A * rng.uniform(0.85, 1.15), 0.045, floor + 0.03 + j * 0.025, seed * 10 + 20 + j, k=0.22, notches=int(rng.integers(0, 2)), groove=0.018)


def sprays(sh):
    """Cut sprays (折枝) round the flower: a stem, leaves off it by turns, a bud or a half-open flower. They lie over the filler and under the flower."""
    S = [
        # stem knots, leaves as (point along the stem as a knot-fraction, side, length), the end
        ([(3.6, 8.6), (5.2, 9.3), (6.3, 9.15), (7.15, 8.45)], [(0.25, 1, 1.5), (0.45, -1, 2.0), (0.62, 1, 1.5), (0.8, -1, 1.9)], ("flower", 0.92)),
        ([(4.6, 5.2), (6.9, 5.3), (8.6, 5.9), (9.5, 6.9)], [(0.2, -1, 2.3), (0.4, 1, 1.7), (0.58, -1, 2.2), (0.75, 1, 1.6)], ("bud", 1.1)),
        ([(-3.6, 9.0), (-5.4, 9.3), (-6.7, 8.9), (-7.7, 8.15)], [(0.3, -1, 1.5), (0.5, 1, 1.9), (0.7, -1, 1.5), (0.85, 1, 1.7)], ("bud", 1.05)),
        ([(-4.8, 4.2), (-7.0, 4.3), (-8.8, 5.0), (-9.9, 6.0)], [(0.2, 1, 2.2), (0.42, -1, 2.1), (0.6, 1, 1.9), (0.8, -1, 1.8)], ("flower", 0.95)),
        ([(-3.2, 3.2), (-5.0, 2.2), (-7.0, 1.9), (-8.5, 2.2)], [(0.3, -1, 2.2), (0.5, 1, 1.8), (0.72, -1, 1.9)], ("bud", 1.0)),
        ([(3.0, 3.2), (5.2, 2.3), (7.2, 2.2), (8.8, 2.8)], [(0.3, 1, 1.9), (0.5, -1, 2.1), (0.72, 1, 1.7)], ("bud", 1.0)),
    ]
    from scipy.interpolate import CubicSpline

    for i, (knots, lvs, end) in enumerate(S):
        rng = np.random.default_rng(6400 + i)
        knots = np.array(knots, float)
        ss = np.r_[0.0, np.cumsum(np.hypot(*np.diff(knots, axis=0).T))]
        sp = CubicSpline(ss / ss[-1], knots)
        stem(sh, knots, 0.06 + 0.012 * rng.random(), 6450 + i, floor=0.13)
        for j, (u, sg, L) in enumerate(lvs):
            q, dv = sp(u), sp(u, 1)
            a = np.arctan2(dv[1], dv[0]) + sg * rng.uniform(0.5, 1.0)
            L = L * rng.uniform(0.94, 1.06)
            while np.hypot(*(q + r2d(a) * L)) > RING and L > 0.8:
                L *= 0.93
            leaf(sh, q, a, L, 6500 + i * 10 + j, floor=0.15, k=0.62)
        q, dv = sp(1.0), sp(1.0, 1)
        if end[0] == "flower":
            small_flower(sh, q + dv / np.linalg.norm(dv) * 0.3, end[1], 6600 + i, floor=0.22)
        else:
            bud(sh, q, np.arctan2(dv[1], dv[0]) + rng.normal(0, 0.1), end[1], 6620 + i, floor=0.2)


def plan_filler(dish):
    """Where the small leaves go, so that the ground shows only in the cracks. Planned on a coarse grid against everything else, then laid at full density under it."""
    p = 40.0
    x0, y0 = -14.5, -1.0
    nx, ny = int(29.0 * p), int(15.6 * p)
    pre = Sheet(x0, y0, nx, ny, p, fast=True)
    carve(pre, [])
    X, Y = np.meshgrid(x0 + (np.arange(nx) + 0.5) / p, y0 + (np.arange(ny) + 0.5) / p)
    rho = np.hypot(X, Y)
    free = ((pre.red == 0) & (rho < RING + 0.05)).astype(np.uint8)
    rng = np.random.default_rng(6700)
    out = []
    for i in range(400):
        dist = cv2.distanceTransform(free, cv2.DIST_L2, 5) / p
        dn = dist + 0.03 * rng.random(dist.shape)
        iy, ix = np.unravel_index(np.argmax(dn), dn.shape)
        gap = dist[iy, ix]
        if gap < 0.13:
            break
        q = np.array([X[iy, ix], Y[iy, ix]])
        # the sweep: out from the flower and round it, with a slow drift and a hand's jitter
        a = np.arctan2(*(q - C)[::-1]) + 0.6 * np.sin(q[0] * 0.7 + q[1] * 0.45) + rng.normal(0, 0.35)
        wd = float(np.clip(gap * rng.uniform(0.85, 1.15), 0.13, 0.6))
        L = float(np.clip(wd * rng.uniform(3.8, 5.2), 0.7, 3.0))
        root = q - r2d(a) * L * 0.42
        while np.hypot(*(root + r2d(a) * L)) > RING + 0.1 and L > 0.5:
            L *= 0.9
        seed = 6800 + i
        lancet(pre, root, a, L, wd, 0.08, 0.06, seed, k=float(np.clip(L / 3.0, 0.3, 0.7)), clearance=0.02, groove=0.02)
        out.append((tuple(root), float(a), L, wd, seed))
        free = ((pre.red == 0) & (rho < RING + 0.05)).astype(np.uint8)
        cv2.circle(free, (int(ix), int(iy)), max(int(gap * 0.5 * p), 1), 0, -1)
    print("filler leaves", len(out), "largest gap left", float(gap), flush=True)
    return out


def carve(sh, filler):
    rng = np.random.default_rng(611)
    for root, a, L, wd, seed in filler:
        lancet(sh, np.array(root), a, L, wd, 0.08, 0.06, seed, k=float(np.clip(L / 3.0, 0.3, 0.7)), clearance=0.02, groove=0.02)
    # --- leaves and stems behind the flower. Polar from the heart: 90 is towards the far lip. (angle of the root, radius of the root, way it points, length)
    leaves = [
        (168, 4.2, 176, 4.6, 11),
        (147, 3.7, 151, 3.9, 12),
        (127, 3.4, 124, 2.5, 13),
        (101, 3.2, 104, 2.2, 14),
        (76, 3.2, 70, 2.2, 15),
        (52, 3.6, 47, 3.3, 16),
        (31, 4.0, 26, 3.9, 17),
        (9, 4.4, 4, 4.5, 18),
        (192, 4.4, 205, 4.4, 19),
        (214, 3.9, 232, 4.0, 20),
        (-16, 4.0, -24, 4.3, 21),
        (-44, 3.5, -54, 3.8, 22),
    ]
    for ar, rr, a, L, s in leaves:
        q = C + r2d(np.radians(ar)) * rr * np.array([1.2, 1.0])
        an = np.radians(a + rng.uniform(-5, 5))
        L = L * rng.uniform(0.96, 1.05)
        # no leaf is cut by the lip: a carver draws it to fit inside the ring
        tip = q + r2d(an) * L
        while np.hypot(*tip) > RING and L > 1.2:
            L *= 0.93
            tip = q + r2d(an) * L
        leaf(sh, q, an, L, 610 + s, floor=0.1)
    sprays(sh)
    # --- the flower, tier on tier. In each tier the order of laying is shuffled, so that the overlaps do not run round like a pinwheel
    tiers = [
        # n, angle offset, length, half angle, base radius, thick, floor, k, curl
        (9, 11.0, 4.7, 0.62, 0.55, 0.16, 0.13, 1.0, 0.0),
        (9, 31.0, 3.85, 0.6, 0.45, 0.15, 0.27, 0.92, 0.012),
        (8, 7.0, 3.0, 0.68, 0.4, 0.12, 0.38, 0.72, 0.02),
        (8, 28.0, 2.15, 0.8, 0.35, 0.11, 0.48, 0.52, 0.03),
        (8, 2.0, 1.45, 0.92, 0.3, 0.09, 0.56, 0.36, 0.035),
    ]
    sid = 6300
    for ti, (n, off, L, A, b0, thick, floor, k, curl) in enumerate(tiers):
        angs = np.radians(off + 360.0 * (np.arange(n) + rng.normal(0, 0.14, n)) / n)
        order = rng.permutation(n)
        for j in order:
            sid += 1
            a = angs[j]
            lk = rng.uniform(0.9, 1.08)
            s = flower_outer_scale(a) if ti < 2 else 1.0 + 0.5 * (flower_outer_scale(a) - 1.0)
            B = C + r2d(a + rng.normal(0, 0.1)) * b0 * rng.uniform(0.7, 1.3)
            petal(sh, B, a + rng.normal(0, 0.05), L * lk * s, A * rng.uniform(0.85, 1.18), A * rng.uniform(0.85, 1.18), thick * rng.uniform(0.85, 1.15), floor + rng.uniform(-0.015, 0.02), sid, k=k, curl=curl * rng.uniform(0.5, 1.5), clearance=0.06, groove=0.03 if ti < 3 else 0.02, notches=None if ti < 3 else int(rng.integers(1, 4)))
    # --- the crumpled ruff right around the stamens: small, tight, cupped
    n = 11
    for j in rng.permutation(n):
        sid += 1
        a = np.radians(360.0 * (j + rng.normal(0, 0.2)) / n + 13)
        petal(sh, C + r2d(a) * 0.32, a, rng.uniform(0.86, 1.14), rng.uniform(0.75, 1.15), rng.uniform(0.75, 1.15), 0.07, 0.62 + rng.uniform(-0.02, 0.02), sid, k=0.22, curl=0.05, nveins=int(rng.uniform(3, 7)), notches=int(rng.integers(0, 3)), clearance=0.05, groove=0.025)
    heart(sh, sid)
    # small petals come up from right behind the boss and break its edge, so the heart is not a clean disc
    for an in rng.permutation([12, 58, 97, 141, 186, 233, 271, 318]):
        sid += 1
        a = np.radians(an + rng.normal(0, 9))
        petal(sh, C + r2d(a) * rng.uniform(0.42, 0.56), a + rng.normal(0, 0.15), rng.uniform(0.5, 0.78), rng.uniform(0.75, 1.0), rng.uniform(0.75, 1.0), 0.05, 0.69 + rng.uniform(-0.01, 0.02), sid, k=0.16, curl=0.02, nveins=int(rng.integers(2, 6)), notches=int(rng.integers(0, 2)), clearance=0.015, groove=0.012)
    return rng


def heart(sh, sid):
    """Stamens and carpels: a low boss cut by the knife into flat, tilted, uneven facets, not beads; some run together. A few stamens stand up in the middle."""
    from scipy.spatial import cKDTree

    rng = np.random.default_rng(sid + 77)
    a = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    rad = 0.6 * (1.0 + 0.16 * wob(rng, 6, 5)(a / 6.283))
    pts = C + np.stack([rad * np.cos(a), rad * np.sin(a)], 1)
    r = sh.roi(pts, 0.25)
    if r is None:
        return
    box, X, Y = r
    m = sh.mask(box, pts)
    p = sh.pxcm
    d = dist_in(m, p)
    rr = np.maximum(np.hypot(X - C[0], Y - C[1]), 0.03)
    th = np.arctan2(Y - C[1], X - C[0])
    base = drape(sh, box, 0.02, 0.68, 0.15)
    h = base + 0.018 * cut_edge(d, 0.03) + 0.085 * np.clip(1.0 - (rr / 0.62) ** 2, 0.0, 1.0)
    # the facets: cells of a Voronoi on a stretched polar map, so that each is a little longer radially, and their sizes vary a lot
    S = 1.8

    def embed(rr_, th_):
        return np.stack([S * np.cos(th_), S * np.sin(th_), np.log(rr_)], -1)

    seeds = []
    for _ in range(6000):
        rs, ts = np.sqrt(rng.uniform(0.11**2, 0.72**2)), rng.uniform(0, 6.283)
        e = embed(rs, ts)
        gap = rng.choice([0.09, 0.14, 0.22], p=[0.45, 0.4, 0.15])
        if all(np.linalg.norm(e - q) > gap for q in seeds):
            seeds.append(e)
    seeds = np.array(seeds)
    n = len(seeds)
    tree = cKDTree(seeds)
    dd, idx = tree.query(embed(rr, th).reshape(-1, 3), k=2)
    F1, F2 = dd[:, 0].reshape(rr.shape), dd[:, 1].reshape(rr.shape)
    i1, i2 = idx[:, 0].reshape(rr.shape), idx[:, 1].reshape(rr.shape)
    # some run together: a sparse set of patches take all their cells as one
    group = np.arange(n)
    hubs = seeds[rng.choice(n, size=max(n // 22, 4), replace=False)]
    hd, hi = cKDTree(hubs).query(seeds)
    joined = hd < rng.uniform(0.2, 0.32, n)
    group[joined] = n + hi[joined]
    level = rng.uniform(0.0, 0.05, n + len(hubs))
    tx, ty = rng.normal(0, 0.28, n + len(hubs)), rng.normal(0, 0.28, n + len(hubs))
    g1, g2 = group[i1], group[i2]
    # the wall between two facets: narrow, and of uneven depth
    wall = np.maximum((F2 - F1) * rr * 0.5, 0.0)
    deep = rng.uniform(0.02, 0.05, n)[i1]
    cutv = (1.0 - np.clip(wall / rng.uniform(0.008, 0.012), 0.0, 1.0)) * (g1 != g2)
    h = h + level[g1] + tx[g1] * (X - C[0]) * 0.22 + ty[g1] * (Y - C[1]) * 0.22 - deep * cutv
    # stray nicks, as the blade slips or is drawn twice
    v = np.zeros(m.shape, np.float32)
    org = (sh.org[0] + box[2] / p, sh.org[1] + box[0] / p)
    for _ in range(170):
        t0, r0 = rng.uniform(0, 6.283), rng.uniform(0.14, 0.6)
        ln = rng.lognormal(np.log(0.055), 0.45)
        ang = t0 + rng.normal(0, 0.55)
        ss = np.linspace(0, ln, 8)
        Pn = C + r0 * r2d(t0) + np.stack([ss * np.cos(ang), ss * np.sin(ang)], 1)
        hw = rng.uniform(0.006, 0.014) * np.linspace(1.0, 0.3, 8)
        stroke(v, Pn, hw, hw * rng.uniform(0.7, 1.2), p, org, asym=rng.choice([-0.6, 0.6]))
    # carpels: blunt flat-topped wedges in the very middle
    up = np.zeros(m.shape, np.float32)
    for i in range(4):
        an = 6.283 * (i + rng.normal(0, 0.14)) / 4 + 0.4
        q = C + r2d(an) * rng.uniform(0.05, 0.08)
        ra = rng.uniform(0.045, 0.062)
        cx, cy = X - q[0], Y - q[1]
        e1 = np.hypot(cx * np.cos(an) + cy * np.sin(an), (-cx * np.sin(an) + cy * np.cos(an)) * rng.uniform(1.0, 1.5)) / ra
        up = np.maximum(up, rng.uniform(0.05, 0.08) * np.clip((1.0 - e1) / 0.3, 0.0, 1.0))
    # the stamens that stand: thin stalks rising outward to a flat, nicked anther. Uneven, leaning, not a ring
    for _ in range(11):
        t0 = rng.uniform(0, 6.283)
        r0, ln = rng.uniform(0.07, 0.24), rng.uniform(0.09, 0.19)
        lean = rng.normal(0, 0.3)
        q0 = C + r0 * r2d(t0)
        dirn = r2d(t0 + lean)
        q1 = q0 + ln * dirn
        cx, cy = X - q0[0], Y - q0[1]
        al_ = np.clip((cx * dirn[0] + cy * dirn[1]) / ln, 0.0, 1.0)
        dist = np.hypot(cx - al_ * ln * dirn[0], cy - al_ * ln * dirn[1])
        tall = rng.uniform(0.09, 0.17)
        wd = 0.02 - 0.007 * al_
        up = np.maximum(up, (0.03 + tall * al_**0.7) * np.clip((1.0 - dist / wd) / 0.45, 0.0, 1.0))
        tn = np.array([-dirn[1], dirn[0]])
        ax, ay = X - q1[0], Y - q1[1]
        e2 = np.hypot((ax * tn[0] + ay * tn[1]) / rng.uniform(0.03, 0.048), (ax * dirn[0] + ay * dirn[1]) / rng.uniform(0.016, 0.024))
        up = np.maximum(up, (0.03 + tall + rng.uniform(0.0, 0.02)) * np.clip((1.0 - e2) / 0.32, 0.0, 1.0))
    h = np.maximum(h, base + up)
    sh.place(box, m, h.astype(np.float32), v * sstep(0.02, 0.05, d), rng.random(), groove=0.03)


def band(sh, dish):
    """The cavetto: one continuous scroll of tiny flowers and leaves between two cut lines, dense. A wave of drifting period; a flower sits in every bend, leaves line the stem, every one laid by hand."""
    rng = np.random.default_rng(6155)
    r_in, r_out = RING + 0.32, dish.rho_lip - 0.34
    rm = (r_in + r_out) / 2
    A = (r_out - r_in) * 0.3
    th0, th1 = np.radians(2.0), np.radians(178.0)
    ths = np.arange(th0, th1, 0.0015)
    sl = rm * (ths - th0)
    per = 1.45 + 0.2 * wob(rng, 5, 7)(sl / sl[-1])  # cm, drifting
    phase0 = np.cumsum(2 * np.pi / per) * rm * 0.0015
    ok = sh.roi(np.stack([rm * np.cos(ths), rm * np.sin(ths)], 1), r_out - rm + 0.2)
    if ok is None:
        return
    box, _, _ = ok
    org = (sh.org[0] + box[2] / sh.pxcm, sh.org[1] + box[0] / sh.pxcm)
    if not sh.fast:
        # the two lines that hold the band, cut freehand
        for rl, sd_ in ((r_in - 0.05, 1), (r_out + 0.05, 2)):
            lr = np.random.default_rng(6160 + sd_)
            rr = rl + 0.008 * wob(lr, 6, 40)(sl / sl[-1])
            Q = np.stack([rr * np.cos(ths), rr * np.sin(ths)], 1)
            hw = 0.012 * (0.85 + 0.15 * wob(lr, 6, 30)(sl / sl[-1]))
            stroke(sh.V[box[0] : box[1], box[2] : box[3]], Q, hw, hw * 0.8, sh.pxcm, org)
    sd = 7000
    # two stems wound round each other, half a period apart: a flower in every bend of each, so the band closes up
    for scroll, off0 in enumerate((0.0, np.pi)):
        phase = phase0 + off0
        r_st = rm + A * np.sin(phase) * (0.88 + 0.12 * wob(rng, 4, 11)(sl / sl[-1]))
        P = np.stack([r_st * np.cos(ths), r_st * np.sin(ths)], 1)
        dv = np.gradient(P, axis=0)
        dv /= np.linalg.norm(dv, axis=1, keepdims=True)
        nr = np.stack([-dv[:, 1], dv[:, 0]], 1)
        wv = 0.017 * (1.0 + 0.2 * wob(rng, 6, 25)(sl / sl[-1]))
        outline = np.concatenate([P + nr * wv[:, None], (P - nr * wv[:, None])[::-1]], 0)
        m = sh.mask(box, outline)
        if m.sum() > 8:
            d = dist_in(m, sh.pxcm)
            sh.place(box, m, (0.012 + 0.02 * arc_edge(d, 0.017)).astype(np.float32), np.zeros(m.shape, np.float32), 0.5, groove=0.0, wall=0.0, wall_w=0.01)
        half = np.floor(phase / np.pi).astype(int)
        for hv in range(half.min(), half.max() + 1):
            idx = np.nonzero(half == hv)[0]
            if idx.size < 8:
                continue
            i0, i1 = idx[0], idx[-1]
            ic = (i0 + i1) // 2
            curl = np.sign(np.sin(phase[ic]))  # the flower sits inside the bend
            q = np.array([np.cos(ths[ic]), np.sin(ths[ic])]) * (r_st[ic] - curl * rng.uniform(0.05, 0.11))
            sd += 40
            # leaves crowd both sides of the stem: they lean forward, overlap, and leave only cracks of ground
            for j in range(int(rng.integers(6, 10))):
                i = int(i0 + rng.uniform(0.0, 1.0) * (i1 - i0))
                sg = 1.0 if j % 2 else -1.0
                a = np.arctan2(dv[i, 1], dv[i, 0]) + sg * rng.uniform(0.3, 1.05)
                L = rng.uniform(0.24, 0.44)
                tp = P[i] + r2d(a) * L
                for _ in range(4):
                    if r_in - 0.02 < np.hypot(*tp) < r_out + 0.02:
                        break
                    L *= 0.82
                    tp = P[i] + r2d(a) * L
                lancet(sh, P[i], a, L, L * rng.uniform(0.25, 0.34), 0.016, 0.028, sd + 10 + j, k=0.05, nside=int(rng.integers(2, 5)), bend=rng.uniform(-0.8, 0.8), teeth=rng.random() < 0.3, clearance=0.01, groove=0.005)
            n = int(rng.integers(5, 7))
            off, size = rng.uniform(0, 6.28), rng.uniform(0.15, 0.22)
            for j in rng.permutation(n):
                a = off + 6.283 * (j + rng.normal(0, 0.13)) / n
                petal(sh, q, a, size * rng.uniform(0.88, 1.15), 0.5, 0.5 * rng.uniform(0.85, 1.15), 0.016, 0.046, sd + int(j), k=0.045, nveins=int(rng.integers(1, 4)), notches=int(rng.integers(0, 2)), groove=0.006)
            bead(sh, q, size * 0.17, 0.056)


def bead(sh, q, ra, floor=0.08):
    a = np.linspace(0, 6.283, 40)
    pts = q + np.stack([ra * np.cos(a), ra * np.sin(a)], 1)
    r = sh.roi(pts, 0.1)
    if r is None:
        return
    box, X, Y = r
    m = sh.mask(box, pts)
    if m.sum() < 3:
        return
    dd = np.hypot(X - q[0], Y - q[1])
    b = drape(sh, box, 0.0, floor, 0.05)
    h = b + 0.9 * np.sqrt(np.maximum(ra**2 - dd**2, 0.0))
    sh.place(box, m, h.astype(np.float32), np.zeros(m.shape, np.float32), 0.3, groove=0.004, wall=0.015, wall_w=0.012)


# --- age: where it is, it has a reason ------------------------------------------------------------------------------
def age(sh, Rh, dish):
    """Cracks, chip, scratches. Returns (crack depth, chip depth, scratch depth) in cm."""
    p = sh.pxcm
    ny, nx = sh.shape
    org = sh.org
    cr = np.zeros(sh.shape, np.float32)
    # the coarse carving steers a crack: it runs where the lacquer is thin and turns at the walls
    small = cv2.resize(sh.H, (max(nx // 8, 8), max(ny // 8, 8)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 0.1 * p / 8)
    gy, gx = np.gradient(small)

    def walk(start, ang, length, rng, wander=0.35, steer=0.5):
        pts, q, a = [], np.array(start, float), ang
        step = 0.03
        for _ in range(int(length / step)):
            pts.append(q.copy())
            ix = int(np.clip((q[0] - org[0]) * p / 8, 0, small.shape[1] - 1))
            iy = int(np.clip((q[1] - org[1]) * p / 8, 0, small.shape[0] - 1))
            g = np.array([gx[iy, ix], gy[iy, ix]])
            gn = np.linalg.norm(g)
            if gn > 1e-5:
                # turn along the wall, not up it
                tang = np.arctan2(g[0], -g[1])
                if np.cos(tang - a) < 0:
                    tang += np.pi
                a += steer * np.sin(tang - a) * min(gn * 40, 1.0) * step / 0.03 * 0.25
            a += rng.normal(0, wander) * np.sqrt(step) + (rng.random() < 0.012) * rng.choice([-1, 1]) * rng.uniform(0.35, 0.9)
            q = q + step * r2d(a)
        return np.array(pts)

    def cut(pts, w, rng):
        if len(pts) < 3:
            return
        u = np.linspace(0, 1, len(pts))
        hw = w * np.sin(np.pi * (0.03 + 0.94 * u)) ** 0.35 * (0.75 + 0.25 * wob(rng, 4, 9)(u))
        stroke(cr, pts, hw, hw * 3.0, p, org)

    rng = np.random.default_rng(6177)
    # two age cracks coming in from the lip, where the dish was stressed. Kept far from the heart.
    for th, L, w in [(np.radians(62), 4.3, 0.005), (np.radians(116), 2.2, 0.0042)]:
        q0 = (dish.rho_lip + 0.2) * r2d(th)
        main = walk(q0, th + np.pi, L, rng)
        cut(main, w, rng)
        for _ in range(3):
            i = int(rng.integers(5, max(6, len(main) - 3)))
            a0 = np.arctan2(*(main[i] - main[i - 2])[::-1]) + rng.choice([-1, 1]) * rng.uniform(1.0, 1.7)
            br = walk(main[i], a0, rng.exponential(0.5) + 0.12, rng, 0.5, 0.3)
            cut(br, w * 0.5, rng)
    # a nest of hairlines where a hand holds the dish
    for centre, n in [((3.6, 9.8), 12), ((-3.0, 2.6), 8)]:
        for _ in range(n):
            q0 = np.array(centre) + rng.normal(0, 0.8, 2)
            cut(walk(q0, rng.uniform(0, 6.28), rng.exponential(0.5) + 0.2, rng, 0.45, 0.3), 0.003, rng)
    # the chip in the lip: knocked off, down to the dark under-coats, so the silhouette breaks there
    ch = np.zeros(sh.shape, np.float32)
    chrng = np.random.default_rng(6191)
    th0 = np.radians(71.0)
    for i, (off, wd, dp) in enumerate([(0.0, 0.09, 0.055), (0.085, 0.04, 0.028), (-0.075, 0.03, 0.02)]):
        q = (dish.rho_lip + 0.02) * r2d(th0 + off / dish.R) + chrng.normal(0, 0.008, 2)
        a = np.linspace(0, 6.283, 64, endpoint=False)
        rad = wd * (1.0 + 0.3 * wob(chrng, 7, 9)(a / 6.283)) * np.where(np.cos(a - th0) > 0, 1.0, 0.7)
        pts = q + np.stack([rad * np.cos(a), rad * np.sin(a)], 1)
        ro = sh.roi(pts, 0.05)
        if ro is None:
            continue
        box, X, Y = ro
        m = sh.mask(box, pts)
        d = dist_in(m, p)
        # conchoidal: steep at the edge, stepped inside
        f = dp * (0.6 * sstep(0.0, 0.012, d) + 0.4 * sstep(0.01, wd * 0.7, d))
        ch[box[0] : box[1], box[2] : box[3]] = np.maximum(ch[box[0] : box[1], box[2] : box[3]], f.astype(np.float32))
    # scratches: straight-ish, from handling, on the high ground only
    sc = np.zeros(sh.shape, np.float32)
    s_rng = np.random.default_rng(6201)
    for centre, n in [((-1.2, 8.6), 5), ((2.0, 7.3), 4), ((-4.6, 5.2), 3)]:
        for _ in range(n):
            q0 = np.array(centre) + s_rng.normal(0, 0.7, 2)
            a = np.radians(-28) + s_rng.normal(0, 0.45)
            L = s_rng.exponential(0.8) + 0.3
            t = np.linspace(0, 1, 24)
            pts = q0 + np.outer(t * L, r2d(a)) + np.outer(0.02 * (t - 0.5) ** 2, r2d(a + 1.57))
            hw = s_rng.uniform(0.0028, 0.0052) * np.sin(np.pi * t) ** 0.4
            stroke(sc, pts, hw, hw * 0.7, p, org)
    return cr, ch, sc


# --- from the carving to surface fields ---------------------------------------------------------------------------
def finish(sh, dish, X, Y):
    p = sh.pxcm
    shape = sh.shape
    # the lip is plain: a low, narrow round. One clean step marks where the carved band ends
    rho = np.hypot(X, Y)
    r_lip0 = dish.rho_lip - 0.27
    fade = sstep(r_lip0 + 0.015, r_lip0 - 0.015, rho)
    Hc = sh.H * fade
    red = sh.red * fade
    lip_red = 1.0 - fade
    red = np.maximum(red, lip_red)
    H_total = Hc + 0.04 * lip_red

    s_rng = np.random.default_rng(6240)
    cr, ch, sc = age(sh, H_total, dish)
    # the ground: a smooth lacquer, satin, with nothing on it but a very slow unevenness left by the scraper
    ground_h = 0.005 * field(shape, p, 1.0, 8.0, 3.0, 6101)

    # a hand's wear: not on all that stands high, but where a hand and a cloth reach, and only on the crests
    conv_s = cv2.GaussianBlur(H_total, (0, 0), 0.14 * p)
    conv_l = cv2.GaussianBlur(H_total, (0, 0), 0.45 * p)
    crest = sstep(0.006, 0.05, H_total - conv_s) + 0.6 * sstep(0.01, 0.1, H_total - conv_l)
    hand = rank(field(shape, p, 1.2, 7.0, 3.0, 6103))
    wear = np.clip(crest, 0, 1) * (0.2 + 0.8 * sstep(0.25, 0.8, hand)) * red
    # the deep: the carving's lows hold old wax and dust; dust settles into the ground at the foot of walls
    pit = sstep(0.005, 0.06, conv_s - H_total)
    pit_l = sstep(0.01, 0.1, cv2.GaussianBlur(H_total, (0, 0), 0.09 * p) - H_total)
    grime_tex = rank(fbm(shape, p, 0.012, 0.18, 1.2, 6104))
    low = sstep(0.012, 0.09, conv_l - H_total)  # the wide lows beside a standing form: no cloth reached them; they must not take a pale reflection

    # handling wears the cuts away: on the crests the veins are half gone
    V = sh.V * (1.0 - 0.35 * wear)
    # surface fine: a very low polish wave, hand-sanded: larger on the red tops
    polish = field(shape, p, 0.3, 3.0, 2.5, 6105)
    micro = fbm(shape, p, 0.02, 0.09, 1.2, 6106)
    H = H_total - V + ground_h * (1.0 - red) + red * (0.0017 * polish + 0.00009 * micro) - 0.45 * np.minimum(cr, 0.02) - ch - np.minimum(sc, 0.006)
    # the knife leaves an arris; only a pixel of anti-aliasing here. Handling softens it at a few high places, not everywhere
    H = cv2.GaussianBlur(H, (0, 0), 0.38)
    soft = np.clip(crest, 0, 1) * sstep(0.9, 0.97, hand) * red
    H = H * (1.0 - soft) + cv2.GaussianBlur(H, (0, 0), max(0.018 * p, 1.0)) * soft

    # --- colour. Lacquer is a function of depth: the colour stands where the knife stopped
    gy, gx = np.gradient(H, 1.0 / p)
    slope = np.hypot(gx, gy)
    # strata on steep walls only: faint, uneven, some darker bands
    lr = np.random.default_rng(6107)
    n_l = 120
    bounds = np.cumsum(lr.lognormal(np.log(0.012), 0.5, n_l))
    tone = 1.0 + lr.normal(0, 0.1, n_l)
    tone[lr.random(n_l) < 0.1] *= 0.68
    level = H_total + 0.016 * field(shape, p, 0.2, 1.5, 2.5, 6108) + 0.0022 * fbm(shape, p, 0.04, 0.3, 1.6, 6109)
    idx = np.clip(np.searchsorted(bounds, np.maximum(level, 0)), 0, n_l - 1)
    strata = cv2.GaussianBlur(tone[idx].astype(np.float32), (0, 0), 0.5)
    on_wall = sstep(1.5, 5.0, slope)

    deep_red = color3(0.165, 0.0095, 0.0058)
    mid_red = color3(0.26, 0.021, 0.0105)
    warm_red = color3(0.34, 0.034, 0.0135)
    # each element took the top coats slightly differently; a slow unevenness across the dish
    uneven = field(shape, p, 0.6, 5.0, 2.7, 6110)
    t = np.clip(0.5 + 0.2 * uneven + 0.45 * (sh.idv - 0.5) * 0.45, 0, 1)
    body = mix(deep_red, mid_red, sstep(0.0, 0.75, t))
    # high = warm, handled; low = oxblood
    body = mix(body, warm_red, 0.8 * wear)
    body = mix(body, deep_red * 0.72, 0.6 * np.maximum(pit, 0.8 * low))
    body = body * ((1.0 + (strata - 1.0) * on_wall * 0.85) * (1.0 - 0.34 * on_wall))[..., None]  # a cut wall is rougher and takes less of the top coat
    # old wax and grey dust in the lows and in the foot of the cuts, in clots, not an even wash
    wax = color3(0.06, 0.036, 0.026)
    body = mix(body, wax, 0.5 * np.maximum(0.3 * pit, pit_l) * sstep(0.35, 0.8, grime_tex))  # old dark wax in the foot of a cut, not a grey wash over everything that lies low
    # fine lacquer flecks of a warmer tone, sparse: the cinnabar was ground, not perfect
    flecks = sstep(0.992, 0.999, rank(fbm(shape, p, 0.008, 0.05, 0.5, 6111)))
    body = mix(body, warm_red * 1.25, 0.25 * flecks)

    # the ground: dark olive-ochre, chosen by eye towards the Yuan dish in ref/, so the red stands off it. Dust only as a thin dark line at the very foot of a wall
    g_tone = rank(field(shape, p, 0.8, 7.0, 3.0, 6112))
    gr = mix(color3(0.082, 0.052, 0.022), color3(0.056, 0.036, 0.017), 0.6 * g_tone)
    gr = mix(gr, color3(0.026, 0.018, 0.012), 0.7 * sstep(0.0, 0.6, pit_l))

    a = cv2.GaussianBlur(red, (0, 0), 0.6)
    col = mix(gr, body, a)

    # veins and cracks hold dark wax; a fresh-looking cut wears thin
    dark_v = sstep(0.0, 0.008, V)
    col = col * (1.0 - 0.55 * dark_v * (0.75 + 0.25 * grime_tex))[..., None]
    col = mix(col, color3(0.085, 0.06, 0.045), 0.3 * dark_v * sstep(0.62, 0.9, grime_tex))  # here and there a cut still holds pale wax
    crack_m = sstep(0.0, 0.006, cr)
    col = col * (1.0 - 0.7 * crack_m)[..., None]
    # the chip: red skin over the dark under-coats, a pale ochre coat between them
    chip_dark = color3(0.022, 0.012, 0.009)
    chip_mid = color3(0.2, 0.09, 0.045)
    col = mix(col, chip_mid, sstep(0.0, 0.006, ch))
    col = mix(col, chip_dark, sstep(0.012, 0.024, ch))

    patch = np.clip(field(shape, p, 0.05, 0.4, 2.0, 6114), -1.5, 1.5)
    rough = 0.3 - 0.06 * wear + 0.25 * sstep(0.0, 0.3, pit) + 0.05 * np.clip(polish, -1, 1) + 0.05 * patch
    rough = mix(0.5, rough, a)
    rough = rough + 0.25 * crack_m + 0.2 * sstep(0.0, 0.02, ch) + 0.15 * dark_v + 0.22 * on_wall
    # the polish: a hand-rubbed half gloss that lies on what stands and swells. The lows, the cuts and the cracks never took the rubbing: they stay dull and hold old lacquer
    arris = sstep(0.003, 0.012, H_total - cv2.GaussianBlur(H_total, (0, 0), 0.022 * p)) * a  # the knife's edge: a thread of gloss
    rubbed = rank(field(shape, p, 0.4, 3.0, 2.5, 6115))
    coatw = a * (0.5 + 0.4 * rubbed) * (1.0 - 0.9 * sstep(0.0, 0.25, pit)) * (1.0 - 0.8 * dark_v) * (1.0 - crack_m) * (1.0 - 0.6 * on_wall)
    coatw = np.maximum(coatw, 0.95 * arris * (1.0 - crack_m)) + 0.8 * lip_red * (1.0 - sstep(0.0, 0.006, ch))
    coatw = coatw * (1.0 - 0.85 * low)
    coatw = coatw + 0.2 * (1.0 - a)  # the ground is satin
    coatr = 0.1 + 0.04 * np.clip(patch, -1, 1) + 0.05 * (1.0 - rubbed) + 0.25 * sstep(0.0, 0.25, pit)
    coatr = mix(coatr, 0.06, arris) + 0.25 * (1.0 - a)
    extra = {"coatw": np.clip(coatw, 0, 1).astype(np.float32), "coatr": np.clip(coatr, 0.03, 1).astype(np.float32), "spec": (0.42 * (1.0 - 0.75 * np.maximum(np.maximum(pit, low) * a, 0.0))).astype(np.float32)}
    return H.astype(np.float32), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.08, 1).astype(np.float32), {"wear": wear, "slope": slope, **extra}


def color3(r, g, b):
    return np.array([r, g, b], np.float32)


# --- flat. A cheap shaded look at the design, with the shadow marched over the height field ----
def shaded(H, col, rough, dish, X, Y, p):
    L = np.array([-0.5, 0.62, 0.6])
    L = L / np.linalg.norm(L)
    gy, gx = np.gradient(H, 1.0 / p)
    nd = dish.normal(X, Y)
    n = nd.copy()
    n[..., 0] -= gx
    n[..., 1] -= gy
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    # shadow: march towards the light
    lh = np.hypot(L[0], L[1])
    ux, uy, slope = L[0] / lh, L[1] / lh, L[2] / lh
    ny, nx = H.shape
    Z = H + np.array(dish.surface(X, Y))[..., 2]
    occ = np.zeros(H.shape, np.float32)
    for t in np.geomspace(0.012, 2.4, 34):
        M = np.array([[1, 0, -ux * t * p], [0, 1, -uy * t * p]], np.float32)
        sh = cv2.warpAffine(Z, M, (nx, ny), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        occ = np.maximum(occ, (sh - t * slope - Z - 0.004) / (0.012 + 0.09 * t))
    vis = 1.0 - np.clip(occ, 0, 1)
    ndl = np.clip((n @ L.astype(np.float32)), 0, 1)
    ao = np.exp(-np.clip(cv2.GaussianBlur(Z, (0, 0), 0.25 * p) - Z, 0, 1) * 7.0)
    V = np.array([0.0, -np.cos(np.radians(EL)), np.sin(np.radians(EL))], np.float32)
    H_ = L.astype(np.float32) + V
    H_ /= np.linalg.norm(H_)
    ndh = np.clip(n @ H_, 0, 1)
    spec = (2.0 / np.maximum(rough, 0.1) ** 3) ** 1.0 * 0.5 * ndh ** (2.0 / np.maximum(rough, 0.1) ** 3) * vis
    fill = 0.3 + 0.2 * n[..., 1]
    linear = col * (2.0 * (ndl * vis)[..., None] + (fill * ao)[..., None]) + 0.012 * spec[..., None]
    return linear, n


def tone(x):
    x = np.clip(x, 0, None)
    y = x * (1.0 + x / 6.0) / (1.0 + x * 0.85)
    return np.clip(y, 0, 1) ** (1 / 2.2)


def frame_view(dish, cam, X, Y, H, lit, out_w=1600):
    """The camera's view, painted far to near, for judging composition and foreshortening before any render."""
    from vessel import project

    P = dish.surface(X, Y, H).reshape(-1, 3)
    x, y, w = project(cam, P)
    W_, H_ = out_w, int(out_w * 9 / 16)
    ix, iy = (x * W_).astype(np.int32), (y * H_).astype(np.int32)
    ok = (ix >= 0) & (ix < W_) & (iy >= 0) & (iy < H_) & (w > 0)
    colrs = lit.reshape(-1, 3)[ok]
    order = np.argsort(-w[ok], kind="stable")
    ix, iy, colrs = ix[ok][order], iy[ok][order], colrs[order]
    im = np.zeros((H_, W_, 3), np.float32)
    for k in range(0, len(ix), 1 << 20):  # far to near, batch by batch; a footprint 2 x 3 covers the gaps and steep walls
        a, b = ix[k : k + (1 << 20)], iy[k : k + (1 << 20)]
        c = colrs[k : k + (1 << 20)]
        for dy in (2, 1, 0):
            for dx in (1, 0):
                im[np.minimum(b + dy, H_ - 1), np.minimum(a + dx, W_ - 1)] = c
    return im


def save_jpg(path, rgb):
    cv2.imwrite(path, (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(path, flush=True)


def frame_grid(dish, cam, pxcm, margin=0.09):
    """Flat coordinates of what the frame sees, carving included, with room for a small camera move."""
    from vessel import project

    rho = np.linspace(0.0, dish.rho_lip + 0.5, 700)
    th = np.linspace(-np.pi, np.pi, 1400)
    R_, T_ = np.meshgrid(rho, th)
    fx, fy = R_ * np.cos(T_), R_ * np.sin(T_)
    ok = np.zeros(R_.shape, bool)
    for h in (0.0, 0.9):
        x, y, _ = project(cam, dish.surface(fx, fy, h).reshape(-1, 3))
        x, y = x.reshape(R_.shape), y.reshape(R_.shape)
        ok |= (x > -margin) & (x < 1 + margin) & (y > -margin) & (y < 1 + margin)
    x0, x1, y0, y1 = fx[ok].min(), fx[ok].max(), fy[ok].min(), fy[ok].max()
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    print(f"grid {nx} x {ny} = {nx * ny / 1e6:.1f} M, x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}", flush=True)
    return np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)


def build(q):
    dish = Dish(PROFILE, sigma=0.035)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.48), aperture_mm=APERTURE, focus_rho=FOCUS_RHO, focus_th=np.pi / 2)
    print("sag", sag, flush=True)
    p = float(sys.argv[2]) if q == "flat" and len(sys.argv) > 2 else GRID_PXCM[q]
    if q == "flat":
        X, Y = np.meshgrid(np.arange(-14.5, 14.5, 1.0 / p, dtype=np.float32) + 0.5 / p, np.arange(0.6, 14.6, 1.0 / p, dtype=np.float32) + 0.5 / p)
    else:
        X, Y = frame_grid(dish, cam, p)
    sh = Sheet(float(X[0, 0] - 0.5 / p), float(Y[0, 0] - 0.5 / p), X.shape[1], X.shape[0], p)
    filler = plan_filler(dish)
    band(sh, dish)
    carve(sh, filler)
    return dish, cam, X, Y, sh


def flat():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish, cam, X, Y, sh = build("flat")
    H, col, rough, _ = finish(sh, dish, X, Y)
    p = sh.pxcm
    lit, n = shaded(H, col, rough, dish, X, Y, p)
    img = tone(lit)
    room = tone(np.array([0.012, 0.012, 0.012], np.float32))  # the photographer's room: grey-black
    keep = sstep(dish.rho_lip + 0.3, dish.rho_lip + 0.1, np.hypot(X, Y))[..., None]
    img_flat = img * keep + room * (1.0 - keep)
    # flat coords have +y growing with the row: show it with the far lip up
    im = img_flat[::-1]
    k = 2000.0 / im.shape[1]
    save_jpg(os.path.join(d, "flat.jpg"), cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_AREA))
    hh = (H - np.percentile(H, 0.5)) / (np.percentile(H, 99.9) - np.percentile(H, 0.5))
    hh = np.clip(hh, 0, 1)[::-1]
    save_jpg(os.path.join(d, "flat_height.jpg"), np.repeat(cv2.resize(hh, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)[..., None], 3, 2))
    if len(sys.argv) > 2:
        for i, (cx, cy, wd) in enumerate([(-0.35, 7.1, 3.5), (-3.8, 8.6, 3.5), (5.6, 9.2, 4.0), (0.8, 12.4, 3.0)]):
            a0, b0 = int((cx - wd / 2 - X[0, 0]) * p), int((cy - wd / 3 - Y[0, 0]) * p)
            cr = img[b0 : b0 + int(wd * p * 2 / 3), a0 : a0 + int(wd * p)][::-1]
            save_jpg(os.path.join(d, f"flat_crop{i}.jpg"), cr)
    fv = frame_view(dish, cam, X, Y, H, img)
    fv = np.where(fv.sum(-1, keepdims=True) == 0, room, fv)
    save_jpg(os.path.join(d, "flat_frame.jpg"), fv)
    print("H range", float(H.min()), float(H.max()), flush=True)


def lights(cam, focus):
    """A hard, low lamp from one side and a little behind; the rest stays dark. The room gives the reflections."""
    from vessel import reflect_light_loc

    f = np.array(focus, float) + np.array([0.3, -0.6, 0.3])
    key_dir = np.array([-0.93, -0.12, 0.30])  # from the left and a little nearer: the far lip throws nothing onto the petals
    key_dir /= np.linalg.norm(key_dir)
    loc = f + key_dir * 95.0
    glint, _ = reflect_light_loc(f, np.array([-0.16, 0.22, 1.0]), cam, 70.0)
    strip, _ = reflect_light_loc(f, np.array([0.1, 0.34, 1.0]), cam, 80.0)
    return [
        {"type": "gradient", "name": "glint", "loc": glint.tolist(), "target": f.tolist(), "size": [130, 110], "sigma": [26, 20], "L": 2.0, "rgb": [1.0, 0.86, 0.74], "hide_in_diffuse": True},  # soft edged: a hard-edged lamp drew a straight line across the far petals, where the cavetto starts to tilt them out of its reflection
        {"name": "strip", "loc": strip.tolist(), "target": f.tolist(), "size": [90, 5], "watts": 1800, "rgb": [1.0, 0.88, 0.76], "hide_in_diffuse": True},
        {"name": "key", "loc": loc.tolist(), "target": f.tolist(), "size": [7, 7], "watts": 780, "rgb": [1.0, 0.93, 0.83], "spread": 9.0, "hide_in_gloss": True},
        {"name": "fill", "loc": (f + np.array([38, -30, 36])).tolist(), "target": f.tolist(), "size": [70, 70], "watts": 950, "rgb": [1.0, 0.95, 0.9], "hide_in_gloss": True},
    ]


SKY = {"top": [0.0072, 0.0071, 0.0070], "glow": [0.0189, 0.0187, 0.0185], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": 0.451, "seed": 61}
MOVE = {"truck": [0.01, 0.0], "orbit": [1.0, 0.2], "dolly": 0.025}
DEVELOP = {"exposure": 0.06, "contrast": 1.32, "saturation": 0.97, "black": 0.0012, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "glare": 0.002, "vignette": 0.35}


def measure(dish, cam, X, Y, H):
    """The arc, from the carved mesh: the upper envelope in the frame, and how far the grid edge stays from the frame during the suggested move."""
    from vessel import project, top_arc

    P = dish.surface(X[::4, ::4], Y[::4, ::4], H[::4, ::4])
    x, y = top_arc(cam, P, bins=160)
    a, b, c = np.polyfit(x, y, 2)
    x0 = -b / (2 * a)
    print(f"arc from the mesh: apex x {x0:.3f} y {np.polyval([a, b, c], x0):.3f}, min y in the frame {y.min():.3f}, sag {abs(a) * 0.25 * 9 / 16:.3f} of W", flush=True)
    Xs, Ys = X[::4, ::4], Y[::4, ::4]
    rs = np.hypot(Xs, Ys) < dish.rho_lip  # beyond the lip the grid is the outer wall, behind the dish: it cannot show
    edge = {"near": P[0][rs[0]], "left": P[:, 0][rs[:, 0]], "right": P[:, -1][rs[:, -1]]}
    for i, f in enumerate(camera_path(cam, [], MOVE, 16)):
        if i not in (0, 15):
            continue
        cc = {**cam, **{k: f[k] for k in ("loc", "target", "lens_mm", "roll")}}
        out = {}
        for k, e in edge.items():
            ex, ey, _ = project(cc, e.reshape(-1, 3))
            inside = (ex > 0) & (ex < 1) & (ey > 0) & (ey < 1)
            out[k] = (int(inside.sum()), round(float(ex.min()), 3), round(float(ex.max()), 3), round(float(ey.min()), 3), round(float(ey.max()), 3))
        print("move frame", i, "edge: points in frame, x range, y range", out, flush=True)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "flat"
    if q == "flat":
        flat()
        return
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"mesh.{q}.npz")
    if os.environ.get("S61_REUSE") and os.path.exists(npz):  # lights only: the carving takes minutes, a lit frame seconds
        dish = Dish(PROFILE, sigma=0.035)
        cam, _ = dish.camera(W, EL, DIST, apex=(0.5, 0.48), aperture_mm=APERTURE, focus_rho=FOCUS_RHO, focus_th=np.pi / 2)
    else:
        dish, cam, X, Y, sh = build(q)
        H, col, rough, ex = finish(sh, dish, X, Y)
        measure(dish, cam, X, Y, H)
        if q == "measure":
            return
        P = dish.surface(X, Y, H)
        np.savez(npz, P=P, col=col, rough=rough, coatw=ex["coatw"], coatr=ex["coatr"], spec=ex["spec"])
    focus = dish.polar(np.array(FOCUS_RHO), np.pi / 2)
    scene = {
        "camera": cam,
        "meshes": [{"name": "dish", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": "spec", "Coat Weight": "coatw", "Coat Roughness": "coatr"}}],
        "lights": [l for l in lights(cam, focus) if l["name"] not in os.environ.get("S61_DROP", "").split(",")],
        "world": [0.0, 0.0, 0.0],
        "sky": dict(SKY),
        "env": {"window": 1.6, "win_az": -30.0, "win_el": 28.0, "strip": 0.5},
        "diffuse_bounces": 4,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }
    shoot(NAME, scene, q, develop=dict(DEVELOP))


main()
