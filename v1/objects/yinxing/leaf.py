"""A ginkgo leaf (Ginkgo biloba): the fan-shaped blade with its margin (waves, incisions, the notch), the open
dichotomous veins grown from the petiole, and the petiole. The shape and the veins only: what the tissue is (its
spectra) is the material (materials/yinxing/), and this file never names a colour.

    python3 -I objects/yinxing/leaf.py CONFIG.json [--out DIR] [--preview]

Writes into DIR (default out/yinxing/objects/<name>/):
- blade.ply      the blade, triangulated inside its outline (the z = 0 plane, or the config's cup); u, v = the maps' UVs;
- petiole.ply    the petiole, a closed tube going down from the blade's base;
- veins.exr      c(u, v) in [0, 1]: the vascular bundle's share of the leaf's thickness there (0 lamina, 1 the
                 vein's centre line; the bundle's column is taken as an ellipse in section, so c = sqrt(1 - (2d/w)^2)
                 at distance d from the centre line of a vein w wide), the map the material's familymap reads;
- veins.json     the vein tree (polylines, widths, the downstream ending counts) and the statistics measured on it;
- preview.png    with --preview: the c map in the outline, for a look.

Frame: millimetres; O = the junction of petiole and blade (the middle of the blade's base), +y along the leaf's axis to
the distal margin, +x to the right seen from the adaxial (upper) side, +z out of the adaxial side.

The outline: either traced from a photograph ("outline": {"polygon_mm": ...}, objects/yinxing/trace_ref.py) or
parametric ("outline": {"parametric": ...}: a fan about O with a distal shape, a wavy margin, incisions and a notch).
Either way it is a closed polygon whose base (the segment on y = 0 where the petiole joins) is where the veins enter.
Its parts: the base; the lateral margins, from the base's ends up to the corners (the outline's leftmost and rightmost
points); the distal margin between the corners; and in it the flanks of the notch and of incisions (the margin more
than "flank_depth_mm" below the outline's convex hull), which the veins run along rather than end on.

The veins' growth rule [A, ours; it reproduces what the photographs show: veins entering at the base, spreading to an
even spacing that stays even as the fan widens, a vein along each lateral margin giving off branches inwards, all
ending on the distal margin, open (no vein joins another)]:
- two potentials on the blade, solved on a grid of "field_grid_mm": u (0 on the base, 1 on the distal margin, no flux
  through the lateral margins and the flanks) and psi (0 on the left lateral margin, 1 on the right, no flux through
  the base and the distal margin; each flank held at the value psi first takes at its bottom, so the flow line that
  meets a notch's bottom splits and runs up both its flanks). psi's level lines (the flow lines) run from the base to
  the distal margin, along the lateral margins and the flanks, radiating from a point above the base as in the
  photographs (objects/yinxing/measure_ref.py); u only says which way is forward;
- the veins start as the petiole's two bundles (Carvalho et al. 2017: two bundles in the petiole, one to each half),
  "start_mm" above the base, and advance together, "step_mm" per step, along the flow lines;
- each steers towards the midpoint of its neighbours (they spread to even spacing; "relax_mm" sets how fast), at most
  "steer_max_angle_deg" off the flow line, so a vein follows the flow line where the spacing is even; "wander" adds a
  small random turn per step;
- the outermost two (the marginal veins) keep "edge_offset_mm" inside the lateral margins, turning up to
  "marginal_max_angle_deg" off the flow line to stay there;
- a vein forks when the wider gap to its neighbours exceeds its own threshold (drawn at its birth around
  "split_spacing_mm", sd "split_sd") and the narrower one is over half of it (a margin is no neighbour; so a vein beside
  an open space forks into it once its last sister has drawn away, not at every step), and not before it has run
  "min_fork_mm" since its own birth; the two daughters diverge at "branch_half_angle_deg" each until they have run
  "min_fork_mm", then steer as the others;
- a vein ends where it meets the margin. Widths: w = width_tip_mm * (endings downstream)^width_exponent.
"""
import argparse
import json
import math
import os
import sys

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from scipy import sparse  # noqa: E402
from scipy.ndimage import distance_transform_edt, map_coordinates  # noqa: E402
from scipy.sparse.linalg import spsolve  # noqa: E402
from scipy.spatial import Delaunay, cKDTree  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def load(path):
    c = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    o = c.get("outline", {})
    if "from" in o:                                       # the traced outline in its own file
        o.update(json.load(open(os.path.join(base, o.pop("from"))))["outline"])
    for k in ("veins", "petiole"):                        # a section shared with another config
        if "from_config" in c.get(k, {}):
            c[k] = json.load(open(os.path.join(base, c[k]["from_config"])))[k]
    return c


def need(d, k, where):
    if k not in d:
        raise SystemExit(f"{where}: no \"{k}\" (no default: every number has a source)")
    v = d[k]
    return v["value"] if isinstance(v, dict) and "value" in v else v


# --- the outline ------------------------------------------------------------------------------
def smin(a, b, k):
    """A smooth minimum of two distances (rounds the corner where the zero sets meet with a radius ~ k)."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Parametric:
    """A fan about O as a field F(x, y) in mm, positive inside: the distal margin r < R(phi), the lateral margins
    |phi| < phi_e(r), the corners rounded, the notch and the incisions cut out, and cut below at the height where the
    lateral margins are the petiole's width apart (the base)."""

    def __init__(self, b, rng):
        w = "outline.parametric"
        self.R0 = need(b, "radius_mm", w)
        self.Phi = math.radians(need(b, "half_angle_deg", w))
        self.Phi0 = math.radians(need(b, "base_half_angle_deg", w))
        self.flare = need(b, "base_flare_mm", w)
        self.shape = need(b, "distal_shape", w)               # R/R0 = 1 + sum a_k cos(k pi phi / Phi)
        self.corner = need(b, "corner_radius_mm", w)
        n = b["notch"]
        self.notch = (need(n, "depth_mm", "notch"), need(n, "bottom_half_width_mm", "notch"),
                      math.radians(need(n, "flank_angle_deg", "notch")))
        u = b["undulation"]
        rms, (l0, l1) = need(u, "rms_mm", "undulation"), need(u, "wavelength_mm", "undulation")
        arc = 2 * self.Phi * self.R0                          # a random Fourier series along the margin
        kmin, kmax = max(1, int(arc / l1)), max(2, int(arc / l0))
        ks = np.arange(kmin, kmax + 1)
        amp = rng.normal(size=len(ks)) / np.sqrt(ks)          # a red spectrum: long waves stronger
        ph = rng.uniform(0, 2 * np.pi, len(ks))
        t = np.linspace(-1, 1, 2001)
        s = (amp[:, None] * np.cos(np.pi * ks[:, None] * (t[None] + 1) / 2 + ph[:, None])).sum(0)
        s *= rms / max(s.std(), 1e-12)
        self.und_t, self.und = t, s
        inc = b.get("incisions", {"count": 0})
        self.cuts = []
        for _ in range(int(need(inc, "count", "incisions"))):
            d0, d1 = need(inc, "depth_mm", "incisions")
            self.cuts.append((rng.uniform(-0.9, 0.9) * self.Phi, rng.uniform(d0, d1),
                              need(inc, "half_width_mm", "incisions")))
        self.base_y = need(b, "petiole_width_mm", w) / 2 / math.tan(self.Phi0)

    def R(self, phi):
        x = np.clip(phi / self.Phi, -1, 1)
        base = 1 + sum(a * np.cos((k + 1) * np.pi * x) for k, a in enumerate(self.shape))
        return self.R0 * base + np.interp(x, self.und_t, self.und)

    def phi_e(self, r):
        return self.Phi - (self.Phi - self.Phi0) * np.exp(-np.maximum(r, 0) / self.flare)

    def F(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        r = np.hypot(x, y)
        phi = np.arctan2(x, y)
        f = smin(self.R(phi) - r, r * np.sin(np.clip(self.phi_e(r) - np.abs(phi), -np.pi / 2, np.pi / 2)),
                 self.corner)
        depth, hw, gam = self.notch
        if depth > 0:
            yb = self.R(0.0) - depth                         # the notch's bottom on the axis
            above = y > yb
            fn = np.where(above, np.abs(x) - (hw + (y - yb) * np.tan(gam)), np.hypot(x, y - yb) - hw)
            fn = np.where(above, fn * np.cos(gam), fn)      # the flank's distance, not its x offset
            f = smin(f, fn, 0.25 * hw)
        for (pc, d, hw) in self.cuts:
            rm = float(self.R(pc))
            px, py = math.sin(pc), math.cos(pc)
            t = np.clip(x * px + y * py, rm - d, rm + 5)
            width = hw * np.clip((t - (rm - d)) / d, 0, 1)
            f = np.minimum(f, np.hypot(x - t * px, y - t * py) - width)
        return np.minimum(f, y - self.base_y)              # the base: a straight cut

    def polygon(self, step):
        """The zero set as a polygon (counter-clockwise), shifted so the base is on y = 0."""
        phi = np.linspace(-self.Phi, self.Phi, 2001)
        rmax = float(np.max(self.R(phi))) + 1
        g = 0.02
        xs = np.arange(-rmax, rmax, g)
        ys = np.arange(self.base_y - 0.5, rmax, g)
        X, Y = np.meshgrid(xs, ys)
        cs, _ = cv2.findContours((self.F(X, Y) > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=len)[:, 0, :].astype(float)
        P = np.stack([xs[0] + c[:, 0] * g, ys[0] + c[:, 1] * g], 1)
        for _ in range(4):                                   # Newton steps onto F = 0
            e = 1e-3
            f = self.F(P[:, 0], P[:, 1])
            gx = (self.F(P[:, 0] + e, P[:, 1]) - self.F(P[:, 0] - e, P[:, 1])) / (2 * e)
            gy = (self.F(P[:, 0], P[:, 1] + e) - self.F(P[:, 0], P[:, 1] - e)) / (2 * e)
            P = P - (f / np.maximum(gx * gx + gy * gy, 1e-6))[:, None] * np.stack([gx, gy], 1)
        P[:, 1] -= self.base_y
        P[np.abs(P[:, 1]) < 1e-3, 1] = 0.0
        return resample(P, step)


def resample(P, step):
    seg = np.hypot(*np.diff(np.r_[P, P[:1]], axis=0).T)
    s = np.r_[0, np.cumsum(seg)]
    t = np.arange(0, s[-1], step)
    Q = np.r_[P, P[:1]]
    P = np.stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])], 1)
    if np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) < 0:
        P = P[::-1]
    return P


class Shape:
    """The blade from its polygon: a signed distance F (mm, positive inside) on a fine grid, and the margin's parts."""

    def __init__(self, poly, flank_depth, h=0.025, pad=1.0):
        self.poly = np.asarray(poly, float)
        self.h = h
        self.x0, self.y0 = self.poly.min(0) - pad
        x1, y1 = self.poly.max(0) + pad
        self.W, self.H = int(math.ceil((x1 - self.x0) / h)), int(math.ceil((y1 - self.y0) / h))
        m = np.zeros((self.H, self.W), np.uint8)
        pts = np.round(((self.poly - [self.x0, self.y0]) / h - 0.5) * 16).astype(np.int32)
        cv2.fillPoly(m, [pts], 1, lineType=cv2.LINE_8, shift=4)
        inside = m > 0
        self.Fg = ((distance_transform_edt(inside) - distance_transform_edt(~inside)) * h).astype(np.float32)
        # the margin's parts, per polygon vertex
        P = self.poly
        n = len(P)
        on_base = P[:, 1] <= 1e-6
        if on_base.sum() < 2:
            raise SystemExit("outline: no base on y = 0")
        iL, iR = int(np.argmin(P[:, 0])), int(np.argmax(P[:, 0]))
        b_idx = np.nonzero(on_base)[0]
        ib_right = int(b_idx[np.argmax(P[b_idx, 0])])
        ib_left = int(b_idx[np.argmin(P[b_idx, 0])])
        lab = np.full(n, "", object)
        lab[on_base] = "base"

        def walk(i, j, name):                                # counter-clockwise from i to j
            k = i
            while k != j:
                if lab[k] == "":
                    lab[k] = name
                k = (k + 1) % n
        walk(ib_right, iR, "right")
        walk(iR, iL, "distal")
        walk(iL, ib_left, "left")
        lab[iR] = lab[iL] = "distal"
        # the flanks of the notch and of incisions: distal margin deeper than flank_depth below the convex hull
        from scipy.spatial import ConvexHull
        hv = P[ConvexHull(P).vertices]
        depth = np.full(n, np.inf)
        for a, b in zip(hv, np.roll(hv, -1, 0)):
            d = b - a
            t = np.clip(((P - a) @ d) / max(d @ d, 1e-12), 0, 1)
            depth = np.minimum(depth, np.hypot(*(P - a - t[:, None] * d).T))
        lab[(lab == "distal") & (depth > flank_depth)] = "flank"
        self.depth_below_hull_max = float(depth[lab != "base"].max())
        self.depth = depth
        self.flank_run = -np.ones(n, int)                    # connected runs of flank vertices
        k = 0
        for i in range(n):
            if lab[i] == "flank" and self.flank_run[i] < 0:
                j = i
                while lab[j] == "flank" and self.flank_run[j] < 0:
                    self.flank_run[j] = k
                    j = (j + 1) % n
                j = (i - 1) % n
                while lab[j] == "flank" and self.flank_run[j] < 0:
                    self.flank_run[j] = k
                    j = (j - 1) % n
                k += 1
        self.n_flanks = k
        if (lab == "").any():
            raise SystemExit("outline: could not label the margin (is the base at the bottom?)")
        self.label = lab
        self.tree = cKDTree(P)
        self.corners = (P[iL], P[iR])

    def F(self, x, y):
        x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
        f = map_coordinates(self.Fg, [np.ravel((y - self.y0) / self.h - 0.5), np.ravel((x - self.x0) / self.h - 0.5)],
                            order=1, mode="nearest")
        return f.reshape(x.shape)

    def part(self, x, y):
        i = self.tree.query(np.stack([np.ravel(x), np.ravel(y)], 1))[1]
        return self.label[i], self.flank_run[i]

    def bbox(self, pad=0.5):
        lo, hi = self.poly.min(0) - pad, self.poly.max(0) + pad
        return lo[0], min(lo[1], -pad), hi[0], hi[1]


# --- the potentials -----------------------------------------------------------------------------
class Potentials:
    """u and psi on a grid of h mm (cell centres inside the blade), finite volumes, the boundary half a cell out.
    psi is solved twice: first with no flux through the flanks, then with each flank held at the first solution's
    value at its bottom (its deepest point): the flow line that meets a notch's or an incision's bottom splits there
    and runs along both its flanks (a central notch gets 0.5 by symmetry)."""

    def __init__(self, S, h):
        x0, y0, x1, y1 = S.bbox(2 * h)
        self.h, self.x0, self.y0 = h, x0, y0
        W, H = int(math.ceil((x1 - x0) / h)), int(math.ceil((y1 - y0) / h))
        xs = x0 + (np.arange(W) + 0.5) * h
        ys = y0 + (np.arange(H) + 0.5) * h
        X, Y = np.meshgrid(xs, ys)
        ins = S.F(X, Y) > 0
        idx = -np.ones((H, W), np.int64)
        idx[ins] = np.arange(ins.sum())
        n = int(ins.sum())
        I, J = np.nonzero(ins)
        rows, cols, vals = [], [], []
        diag = np.zeros(n)
        bu, bp = np.zeros(n), np.zeros(n)
        du, dp = np.zeros(n), np.zeros(n)                    # Dirichlet weight on the diagonal, per field
        fl_k, fl_run = [], []                                # cells next to a flank, and which flank
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            I2, J2 = I + di, J + dj
            ok = (I2 >= 0) & (I2 < H) & (J2 >= 0) & (J2 < W)
            nb = np.full(n, -1)
            nb[ok] = idx[I2[ok], J2[ok]]
            k = idx[I, J]
            inner = nb >= 0
            rows.append(k[inner]); cols.append(nb[inner]); vals.append(-np.ones(inner.sum()))
            diag[k[inner]] += 1
            out = ~inner
            if out.any():
                mx = (xs[J[out]] + xs[np.clip(J2[out], 0, W - 1)]) / 2 if dj else xs[J[out]]
                my = (ys[I[out]] + ys[np.clip(I2[out], 0, H - 1)]) / 2 if di else ys[I[out]]
                part, run = S.part(mx, my)
                ko = k[out]
                fl_k.append(ko[part == "flank"]); fl_run.append(run[part == "flank"])
                for name, val in (("base", 0.0), ("distal", 1.0)):     # u: Dirichlet, 2 = boundary half a cell out
                    s = part == name
                    du[ko[s]] += 2.0
                    bu[ko[s]] += 2.0 * val
                for name, val in (("left", 0.0), ("right", 1.0)):      # psi: Dirichlet
                    s = part == name
                    dp[ko[s]] += 2.0
                    bp[ko[s]] += 2.0 * val
        A0 = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))
        u = spsolve((A0 + sparse.diags(diag + du)).tocsc(), bu)
        p = spsolve((A0 + sparse.diags(diag + dp)).tocsc(), bp)
        self.flank_psi = []
        if S.n_flanks:
            fl_k, fl_run = np.concatenate(fl_k), np.concatenate(fl_run)
            for r in range(S.n_flanks):
                vs = np.nonzero(S.flank_run == r)[0]
                bottom = S.poly[vs[np.argmax(S.depth[vs])]]
                ki = fl_k[fl_run == r]
                cells = np.stack([xs[J[ki]], ys[I[ki]]], 1)
                val = float(p[ki[np.argmin(np.hypot(*(cells - bottom).T))]])
                self.flank_psi.append(round(val, 4))
                np.add.at(dp, ki, 2.0)
                np.add.at(bp, ki, 2.0 * val)
            p = spsolve((A0 + sparse.diags(diag + dp)).tocsc(), bp)
        # grids, the outside filled with the nearest inside value (gradients near the margin stay sane)
        _, (ni, nj) = distance_transform_edt(~ins, return_indices=True)
        self.u = np.zeros((H, W)); self.u[ins] = u
        self.p = np.zeros((H, W)); self.p[ins] = p
        self.u, self.p = self.u[ni, nj], self.p[ni, nj]
        self.gu = np.gradient(self.u, h)                     # (d/dy, d/dx)
        self.gp = np.gradient(self.p, h)

    def at(self, a, P):
        return map_coordinates(a, [(P[:, 1] - self.y0) / self.h - 0.5, (P[:, 0] - self.x0) / self.h - 0.5],
                               order=1, mode="nearest")

    def fields(self, P):
        u, p = self.at(self.u, P), self.at(self.p, P)
        gu = np.stack([self.at(self.gu[1], P), self.at(self.gu[0], P)], 1)
        gp = np.stack([self.at(self.gp[1], P), self.at(self.gp[0], P)], 1)
        return u, p, gu, gp


# --- the veins ----------------------------------------------------------------------------------
def grow_veins(cfg, S, Pot, base, rng):
    v = cfg["veins"]
    w = "veins"
    s_split = need(v, "split_spacing_mm", w)
    sd = need(v, "split_sd", w)
    tb = math.tan(math.radians(need(v, "branch_half_angle_deg", w)))
    ell = need(v, "relax_mm", w)
    edge = need(v, "edge_offset_mm", w)
    wander = need(v, "wander", w)
    step = need(v, "step_mm", w)
    lift = need(v, "start_mm", w)
    min_fork = need(v, "min_fork_mm", w)
    tw = math.tan(math.radians(need(v, "marginal_max_angle_deg", w)))
    ts = math.tan(math.radians(need(v, "steer_max_angle_deg", w)))

    def thr():
        return s_split * max(0.5, 1 + sd * rng.normal())

    (bx0, _), (bx1, _) = base
    veins, act = [], []
    for f in (0.25, 0.75):                                   # the petiole's two bundles
        p = np.array([bx0 + f * (bx1 - bx0), lift])
        veins.append({"parent": -1, "pts": [p.tolist()], "children": [], "born_u": 0.0})
        act.append([p, len(veins) - 1, thr(), 0.0, 0])
    it = 0
    while act and it < 200000:
        it += 1
        P = np.array([a[0] for a in act])
        u, p, gu, gp = Pot.fields(P)
        order = np.argsort(p)
        act = [act[i] for i in order]
        P, u, p, gu, gp = P[order], u[order], p[order], gu[order], gp[order]
        n = len(act)
        ngu = np.maximum(np.linalg.norm(gu, axis=1), 1e-9)
        ngp = np.maximum(np.linalg.norm(gp, axis=1), 1e-9)
        # walls: the lateral margins at the ends; a gap whose midpoint is outside the blade (the notch, a cut)
        mid_out = np.zeros(n + 1, bool)
        mid_out[0] = mid_out[-1] = True
        if n > 1:
            M = (P[:-1] + P[1:]) / 2
            mid_out[1:-1] = S.F(M[:, 0], M[:, 1]) <= 0
        gaps = np.full(n + 1, np.nan)
        if n > 1:
            gaps[1:-1] = np.linalg.norm(P[1:] - P[:-1], axis=1)
        dwl, dwr = p[0] / ngp[0], (1 - p[-1]) / ngp[-1]     # distances to the lateral margins (left, right)
        gl, gr = gaps[:-1].copy(), gaps[1:].copy()
        gl[mid_out[:-1]] = np.nan
        gr[mid_out[1:]] = np.nan
        g2 = np.stack([gl, gr])
        none = np.isnan(g2).all(0)
        gmin = np.where(none, 0.0, np.min(np.where(np.isnan(g2), np.inf, g2), 0))
        gmax = np.where(none, 0.0, np.max(np.where(np.isnan(g2), -np.inf, g2), 0))
        # the lateral offset each vein wants (mm, + towards increasing psi)
        off = np.zeros(n)
        if n > 1:
            pm = (np.r_[np.nan, p[:-1]] + np.r_[p[1:], np.nan]) / 2
            free = ~mid_out[:-1] & ~mid_out[1:]
            off[free] = (pm[free] - p[free]) / ngp[free]
        off[0] = edge - dwl if not mid_out[1] or n == 1 else off[0]
        off[-1] = dwr - edge if not mid_out[-2] or n == 1 else off[-1]
        lim = np.full(n, ts)
        lim[0] = lim[-1] = tw                                # the marginal veins follow the lateral margins
        if n == 1:
            off[0] = 0.0
        ds = np.full(n, step)
        slope = np.clip(off / ell + wander * rng.normal(size=n), -lim, lim)
        side = np.array([a[4] for a in act])                 # a fresh daughter: its side of the fork
        young = (side != 0) & (np.array([a[3] for a in act]) < min_fork)
        slope[young] = side[young] * tb                      # diverges at the dichotomy's half-angle
        lat = gp / ngp[:, None]
        fwd = np.stack([-lat[:, 1], lat[:, 0]], 1)           # along psi's level line, the way u increases
        fwd *= np.where(np.einsum("ij,ij->i", fwd, gu) < 0, -1.0, 1.0)[:, None]
        Pn = P + ds[:, None] * (fwd + slope[:, None] * lat)
        alive = S.F(Pn[:, 0], Pn[:, 1]) > 0
        new = []
        for i, a in enumerate(act):
            V = veins[a[1]]
            if not alive[i]:                                 # met the margin: ends on it
                q, f0 = P[i], float(S.F(*P[i]))
                f1 = float(S.F(*Pn[i]))
                t = f0 / max(f0 - f1, 1e-9)
                V["pts"].append((q + t * (Pn[i] - q)).tolist())
                continue
            V["pts"].append(Pn[i].tolist())
            a[3] += float(np.hypot(*(Pn[i] - P[i])))
            a[0] = Pn[i]
            if gmax[i] > a[2] and gmin[i] > a[2] / 2 and a[3] >= min_fork:   # fork (not within min_fork of its birth)
                for sgn in (-1, 1):
                    veins.append({"parent": a[1], "pts": [Pn[i].tolist()], "children": [], "born_u": float(u[i])})
                    V["children"].append(len(veins) - 1)
                    new.append([Pn[i] + sgn * 1e-4 * lat[i], len(veins) - 1, thr(), 0.0, sgn])
            else:
                new.append(a)
        act = new
    if act:
        raise SystemExit("the veins did not all reach the margin")

    def count(i):
        V = veins[i]
        V["n_end"] = 1 if not V["children"] else sum(count(j) for j in V["children"])
        return V["n_end"]
    for i, V in enumerate(veins):
        if V["parent"] < 0:
            count(i)
    wt, ex = need(v, "width_tip_mm", w), need(v, "width_exponent", w)
    for V in veins:
        V["width_mm"] = wt * V["n_end"] ** ex
    return veins


def simplify(P, tol=0.002):
    """Douglas-Peucker on a polyline (mm)."""
    P = np.asarray(P, float)
    if len(P) < 3:
        return P
    keep = np.zeros(len(P), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(P) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = P[i], P[j]
        d = b - a
        L = np.hypot(*d)
        seg = P[i + 1:j]
        if len(seg) == 0:
            continue
        dist = np.abs(d[0] * (seg[:, 1] - a[1]) - d[1] * (seg[:, 0] - a[0])) / L if L > 0 else np.hypot(*(seg - a).T)
        k = np.argmax(dist)
        if dist[k] > tol:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return P[keep]


# --- the maps -------------------------------------------------------------------------------------
class Grid:
    """The maps' texels: row 0 is the top (y max), as pbrt's image texture puts t = 1 at the first row."""

    def __init__(self, x0, y0, x1, y1, texel):
        self.t = texel
        self.W = int(math.ceil((x1 - x0) / texel))
        self.H = int(math.ceil((y1 - y0) / texel))
        self.x0, self.y1 = x0, y0 + self.H * texel
        self.x1, self.y0 = x0 + self.W * texel, y0

    def uv(self, P):
        return np.stack([(P[:, 0] - self.x0) / (self.x1 - self.x0), (P[:, 1] - self.y0) / (self.y1 - self.y0)], 1)

    def centres(self, i0, i1, j0, j1):
        ys = self.y1 - (np.arange(i0, i1) + 0.5) * self.t
        xs = self.x0 + (np.arange(j0, j1) + 0.5) * self.t
        return np.meshgrid(xs, ys)


def rasterize_veins(G, veins, sub=1):
    """c = sqrt(1 - (2d/w)^2) (the elliptical column's share of the thickness), the max over the veins. Each texel's
    value is the mean over sub x sub points in it (anti-aliased)."""
    c = np.zeros((G.H, G.W), np.float32)
    offs = (np.arange(sub) + 0.5) / sub - 0.5
    for V in veins:
        P = simplify(V["pts"])
        hw = V["width_mm"] / 2
        for a, b in zip(P[:-1], P[1:]):
            lo = np.minimum(a, b) - hw - G.t
            hi = np.maximum(a, b) + hw + G.t
            j0 = max(0, int((lo[0] - G.x0) / G.t)); j1 = min(G.W, int((hi[0] - G.x0) / G.t) + 1)
            i0 = max(0, int((G.y1 - hi[1]) / G.t)); i1 = min(G.H, int((G.y1 - lo[1]) / G.t) + 1)
            if j1 <= j0 or i1 <= i0:
                continue
            X, Y = G.centres(i0, i1, j0, j1)
            d = b - a
            L2 = max(d @ d, 1e-12)
            acc = np.zeros(X.shape, np.float32)
            for ox in offs:
                for oy in offs:
                    px, py = X + ox * G.t, Y + oy * G.t
                    t = np.clip(((px - a[0]) * d[0] + (py - a[1]) * d[1]) / L2, 0, 1)
                    dist = np.hypot(px - a[0] - t * d[0], py - a[1] - t * d[1])
                    acc += np.sqrt(np.clip(1 - (dist / hw) ** 2, 0, 1))
            acc /= sub * sub
            np.maximum(c[i0:i1, j0:j1], acc, out=c[i0:i1, j0:j1])
    return c


def write_exr(path, a):
    a = np.asarray(a, np.float32)
    ok = cv2.imwrite(path, np.repeat(a[..., None], 3, 2),
                     [cv2.IMWRITE_EXR_TYPE, cv2.IMWRITE_EXR_TYPE_HALF, cv2.IMWRITE_EXR_COMPRESSION,
                      cv2.IMWRITE_EXR_COMPRESSION_ZIP])
    if not ok:
        raise SystemExit(f"could not write {path}")


def write_ply(path, P, N, T, uv=None):
    """Binary PLY with normals and optional u, v (as optics/studio.py writes them)."""
    sys.path.insert(0, os.path.join(ROOT, "optics"))
    import studio
    studio.write_ply(path, np.asarray(P, float), np.asarray(N, float), np.asarray(T, np.int32), uv)


# --- the meshes -----------------------------------------------------------------------------------
def surface_z(cfg, x, y):
    """The blade's shape out of its plane, mm: a cup about the axis (z = cup * (x / half-width)^2) [A: the card's
    leaf lies flat; a leaf on the tree is cupped and twisted, the optics layer's choice per shot]."""
    s = cfg.get("surface", {})
    cup = s.get("cup_mm", 0.0)
    hw = s.get("cup_half_width_mm", 30.0)
    return cup * (np.asarray(x, float) / hw) ** 2


def blade_mesh(cfg, S, G, poly):
    inner = need(cfg["mesh"], "interior_step_mm", "mesh")
    x0, y0, x1, y1 = S.bbox()
    xs = np.arange(x0, x1, inner)
    ys = np.arange(y0, y1, inner * math.sqrt(3) / 2)
    X, Y = np.meshgrid(xs, ys)
    X = X + (np.arange(len(ys))[:, None] % 2) * inner / 2
    Q = np.stack([X.ravel(), Y.ravel()], 1)
    Q = Q[S.F(Q[:, 0], Q[:, 1]) > 0.6 * inner]
    P2 = np.r_[poly, Q]
    tri = Delaunay(P2).simplices
    cen = P2[tri].mean(1)
    tri = tri[S.F(cen[:, 0], cen[:, 1]) > 0]
    a, b, c = P2[tri[:, 0]], P2[tri[:, 1]], P2[tri[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    tri[cr < 0] = tri[cr < 0][:, [0, 2, 1]]                  # counter-clockwise seen from +z
    z = surface_z(cfg, P2[:, 0], P2[:, 1])
    e = 1e-3
    dzx = (surface_z(cfg, P2[:, 0] + e, P2[:, 1]) - surface_z(cfg, P2[:, 0] - e, P2[:, 1])) / (2 * e)
    N = np.stack([-dzx, np.zeros_like(dzx), np.ones_like(dzx)], 1)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return np.c_[P2, z], N, tri, G.uv(P2)


def petiole_mesh(cfg):
    """A closed tube from the blade's base down along -y: an ellipse in section (wider than deep), widening towards
    the twig; the top end overlaps the blade's base."""
    p = cfg["petiole"]
    w = "petiole"
    L = need(p, "length_mm", w)
    d_top, d_base = need(p, "diameter_top_mm", w), need(p, "diameter_base_mm", w)
    flat = need(p, "depth_to_width", w)
    bend = need(p, "bend_mm", w)
    over = need(p, "overlap_mm", w)
    ns, nr = 160, 24
    t = np.linspace(0, 1, ns)                                 # 0 at the blade, 1 at the twig
    yc = over - t * (L + over)
    xc = bend * np.sin(np.pi * t) * t                         # a gentle sideways bow
    d = d_top + (d_base - d_top) * t ** 3
    th = np.linspace(0, 2 * np.pi, nr, endpoint=False)
    zc = surface_z(cfg, xc, 0.0) * 0
    P, N = [], []
    for k in range(ns):
        for a in th:
            ex, ez = d[k] / 2 * math.cos(a), d[k] * flat / 2 * math.sin(a)
            P.append([xc[k] + ex, yc[k], zc[k] + ez])
            nn = np.array([math.cos(a) / (d[k] / 2), 0, math.sin(a) / (d[k] * flat / 2)])
            N.append(nn / np.linalg.norm(nn))
    T = []
    for k in range(ns - 1):
        for j in range(nr):
            a, b = k * nr + j, k * nr + (j + 1) % nr
            T += [[a, a + nr, b], [b, a + nr, b + nr]]
    for k, sgn in ((0, 1), (ns - 1, -1)):                    # caps
        ci = len(P)
        P.append([xc[k], yc[k], zc[k]]); N.append([0, sgn, 0])
        for j in range(nr):
            a, b = k * nr + j, k * nr + (j + 1) % nr
            T.append([ci, a, b] if sgn > 0 else [ci, b, a])
    P, N, T = np.array(P), np.array(N), np.array(T)
    tn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    if np.mean(np.einsum("ij,ij->i", tn, N[T[:, 0]]) > 0) < 0.5:
        T = T[:, [0, 2, 1]]                                   # outward winding
    return P, N, T


# --- statistics -----------------------------------------------------------------------------------
def margin_stats(veins, S, depths):
    """The veins crossing the curves `d` mm inside the distal margin (the level sets of F, the part above the
    corners): count and spacing along the curve (median, p10, p90), as a photo is measured; and the endings on each
    half (x < 0, x > 0), as Critchfield 1970 counts them."""
    out = []
    ylow = min(S.corners[0][1], S.corners[1][1])
    for d in depths:
        cs, _ = cv2.findContours((S.Fg > d).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs:
            continue
        c = max(cs, key=len)[:, 0, :].astype(float)
        C = np.stack([S.x0 + (c[:, 0] + 0.5) * S.h, S.y0 + (c[:, 1] + 0.5) * S.h], 1)
        C = C[C[:, 1] > ylow]
        C = C[np.argsort(np.arctan2(C[:, 0], C[:, 1] - ylow))]
        s = np.r_[0, np.cumsum(np.hypot(*np.diff(C, axis=0).T))]
        tree = cKDTree(C)
        hits = []
        for V in veins:
            P = simplify(V["pts"])
            f = S.F(P[:, 0], P[:, 1]) - d
            for i in np.nonzero((f[:-1] > 0) & (f[1:] <= 0))[0]:
                q = P[i] + f[i] / (f[i] - f[i + 1]) * (P[i + 1] - P[i])
                if q[1] > ylow:
                    hits.append(s[tree.query(q)[1]])
        hits = np.sort(hits)
        if len(hits) > 2:
            g = np.diff(hits)
            g = g[g < 5]
            out.append({"depth_mm": d, "count": int(len(hits)), "spacing_median_mm": round(float(np.median(g)), 3),
                        "spacing_p10_mm": round(float(np.percentile(g, 10)), 3),
                        "spacing_p90_mm": round(float(np.percentile(g, 90)), 3)})
    ends = np.array([V["pts"][-1][0] for V in veins if not V["children"]])
    return out, {"left": int((ends < 0).sum()), "right": int((ends >= 0).sum())}


def fork_stats(veins):
    """Path length between successive forks along a lineage (mm), and the number of forks from the petiole to each
    ending."""
    d = []
    for V in veins:
        if V["children"] and V["parent"] >= 0:
            d.append(float(np.sum(np.hypot(*np.diff(np.asarray(V["pts"]), axis=0).T))))
    depth = []

    def walk(i, k):
        V = veins[i]
        if not V["children"]:
            depth.append(k)
        for j in V["children"]:
            walk(j, k + 1)
    for i, V in enumerate(veins):
        if V["parent"] < 0:
            walk(i, 0)
    return {"forks": int(sum(1 for V in veins if V["children"])),
            "fork_to_fork_mm_p10_p50_p90": [round(float(np.percentile(d, q)), 2) for q in (10, 50, 90)] if d else None,
            "forks_to_an_ending_min_median_max": [int(min(depth)), int(np.median(depth)), int(max(depth))]}


def build(cfg, out, preview=False):
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(need(cfg, "seed", "config"))
    o = cfg["outline"]
    step = need(cfg["mesh"], "boundary_step_mm", "mesh")
    if "polygon_mm" in o:
        poly = resample(np.asarray(o["polygon_mm"], float), step)
        poly[np.abs(poly[:, 1]) < 1e-9, 1] = 0.0
    else:
        poly = Parametric(o["parametric"], rng).polygon(step)
    S = Shape(poly, need(o, "flank_depth_mm", "outline"))
    bx = poly[poly[:, 1] <= 1e-6, 0]
    base = ((float(bx.min()), 0.0), (float(bx.max()), 0.0))
    Pot = Potentials(S, need(cfg["veins"], "field_grid_mm", "veins"))
    veins = grow_veins(cfg, S, Pot, base, rng)
    x0, y0, x1, y1 = S.bbox()
    G = Grid(x0, y0, x1, y1, need(cfg["mesh"], "texel_mm", "mesh"))
    c = rasterize_veins(G, veins, sub=need(cfg["mesh"], "texel_supersample", "mesh"))
    X, Y = G.centres(0, G.H, 0, G.W)
    inside = S.F(X, Y) > 0
    c[~inside] = 0.0
    write_exr(os.path.join(out, "veins.exr"), c)
    P, N, T, uv = blade_mesh(cfg, S, G, poly)
    write_ply(os.path.join(out, "blade.ply"), P, N, T, uv)
    Pp, Np, Tp = petiole_mesh(cfg)
    write_ply(os.path.join(out, "petiole.ply"), Pp, Np, Tp)
    area = float(inside.sum()) * G.t ** 2
    perim = float(np.sum(np.hypot(*np.diff(np.r_[poly, poly[:1]], axis=0).T)))
    arcs, ends = margin_stats(veins, S, [0.5, 1.0, 2.0, 4.0, 8.0])
    stats = {"blade_area_mm2": round(area, 1), "perimeter_mm": round(perim, 1),
             "LDI_perimeter_over_sqrt_area": round(perim / math.sqrt(area), 3),
             "width_mm": round(float(poly[:, 0].max() - poly[:, 0].min()), 2),
             "length_mm": round(float(poly[:, 1].max()), 2),
             "veins": len(veins), "endings": int(sum(1 for V in veins if not V["children"])),
             "endings_per_half": ends,
             "vein_cover_c_over_half": round(float((c > 0.5).sum()) / max(1, inside.sum()), 4),
             "inside_distal_margin": arcs,
             **fork_stats(veins),
             "texels": [G.W, G.H], "triangles_blade": int(len(T))}
    stats["outline_depth_below_hull_max_mm"] = round(S.depth_below_hull_max, 2)
    stats["flank_psi"] = Pot.flank_psi
    json.dump({"config": cfg.get("name"), "stats": stats,
               "uv_box_mm": [G.x0, G.y0, G.x1, G.y1],
               "veins": [{"parent": V["parent"], "width_mm": round(V["width_mm"], 4), "n_end": V["n_end"],
                          "pts": np.round(simplify(V["pts"]), 4).tolist()} for V in veins]},
              open(os.path.join(out, "veins.json"), "w"))
    if preview:
        im = (np.clip(1 - 0.8 * c, 0, 1) * 255).astype(np.uint8)
        im = np.where(inside, im, 60).astype(np.uint8)
        cv2.imwrite(os.path.join(out, "preview.png"), cv2.resize(im, (G.W // 2, G.H // 2), interpolation=cv2.INTER_AREA))
        # the potentials' level sets and flow lines, for a look
        k = 20
        img = np.zeros(Pot.u.shape + (3,), np.uint8)
        ins = S.F(*np.meshgrid(Pot.x0 + (np.arange(Pot.u.shape[1]) + 0.5) * Pot.h,
                               Pot.y0 + (np.arange(Pot.u.shape[0]) + 0.5) * Pot.h)) > 0
        img[..., 1] = np.where(ins, ((Pot.u * k) % 1 < 0.08) * 255, 40)
        img[..., 2] = np.where(ins, ((Pot.p * 2 * k) % 1 < 0.08) * 255, 40)
        cv2.imwrite(os.path.join(out, "potentials.png"), img[::-1])
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--out")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    cfg = load(a.config)
    out = a.out or os.path.join(ROOT, "out/yinxing/objects", cfg["name"])
    st = build(cfg, out, a.preview)
    print(json.dumps(st, indent=1))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
