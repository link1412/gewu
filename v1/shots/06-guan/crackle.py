"""Crackle of a thick glaze, grown crack by crack the way it forms in the kiln and after.

Physics (docs/shots/06-guan.md has the sources):
- The glaze shrinks more than the body on cooling (CTE 6.19e-6 vs 5.70e-6 /K, Li, Deng & Xu,
  MRS Bulletin 2001) and goes into biaxial tension. The tension builds up from zero at a free
  edge (an existing crack) over a length that scales with the glaze thickness e (shear lag).
- Cracks form one at a time (Bohn et al., PRE 71, 046215, 2005): a new one starts where the
  tension first exceeds the local strength, runs perpendicular to the largest principal stress,
  and, because an old crack relaxes only the stress across it, turns to meet the old crack at a
  right angle. Large domains crack in a disordered way (defects, gradients); domains of a few
  thicknesses split deterministically across their long axis.
- A crack starts at a flaw (a bubble) but runs as a channel crack through the glaze thickness,
  which needs only enough elastic energy (Hutchinson & Suo 1992: G = Z s^2 e / E' >= Gamma):
  s_ch = K_Ic / sqrt(Z e), whatever flaw it started from. Against the strength of a flaw of
  depth a, s_f = K_Ic / (Y sqrt(pi a)): s_ch / s_f = Y sqrt(pi a / (Z e)), about 0.45 for
  a = 0.12 mm (bubbles), Z = 2, e = 1.2 mm. So a crack runs on until the stress falls below
  s_ch, and thin glaze (the rim, the ridges) needs more stress and cracks less.
- A crack frees the glaze along its flanks, not ahead of its tips (the stress is concentrated
  there), so a tip that stopped runs on when the load rises further. A crack straight ahead
  raises the stress that drives a tip as the ligament between them shrinks, so tips end on
  cracks: there are next to no free ends, as on real pieces.
- Generation 1 forms while cooling and is stained black when the piece comes out of the kiln;
  generation 2 forms later as the body takes up moisture and expands, and is stained ginger
  ("iron wire and golden thread", Li et al. 2001).

The simulation runs on the conformal map of a surface of revolution (phi, t), dt = ds / r(s),
scaled by r0 so units are mm near the reference radius: X = r0 phi, Y = r0 t. The map keeps
angles, so right-angle junctions stay right angles on the pot; lengths scale by r(s)/r0.

    python3 -I shots/06-guan/crackle.py --out out/06/crackle.json --preview out/06/crackle.png
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Field:
    """A scalar field sampled on the simulation raster (bilinear lookup)."""

    def __init__(self, data, x0, y0, h):
        self.a, self.x0, self.y0, self.h = data, x0, y0, h

    def __call__(self, x, y):
        fx = (np.asarray(x) - self.x0) / self.h
        fy = (np.asarray(y) - self.y0) / self.h
        return ndimage.map_coordinates(self.a, [np.atleast_1d(fy), np.atleast_1d(fx)], order=1, mode="nearest")


def gaussian_field(shape, corr_px, rng):
    """Zero-mean, unit-variance Gaussian random field with correlation length corr_px."""
    f = ndimage.gaussian_filter(rng.standard_normal(shape), corr_px, mode="wrap")
    return (f - f.mean()) / (f.std() + 1e-12)


class SegmentHash:
    """Uniform grid over crack segments, for nearest-crack and intersection queries."""

    def __init__(self, cell):
        self.cell = cell
        self.grid = {}
        self.a = []      # segment start points
        self.b = []      # segment end points
        self.crack = []  # crack id of each segment

    def add(self, p, q, cid):
        i = len(self.a)
        self.a.append(p)
        self.b.append(q)
        self.crack.append(cid)
        lo = np.floor(np.minimum(p, q) / self.cell).astype(int)
        hi = np.floor(np.maximum(p, q) / self.cell).astype(int)
        for gx in range(lo[0], hi[0] + 1):
            for gy in range(lo[1], hi[1] + 1):
                self.grid.setdefault((gx, gy), []).append(i)

    def near(self, p, r):
        lo = np.floor((p - r) / self.cell).astype(int)
        hi = np.floor((p + r) / self.cell).astype(int)
        out = set()
        for gx in range(lo[0], hi[0] + 1):
            for gy in range(lo[1], hi[1] + 1):
                out.update(self.grid.get((gx, gy), ()))
        return list(out)


def seg_intersect(p, q, a, b):
    """Parameter u in [0,1] along p->q where it crosses segment a-b, or None."""
    r, s = q - p, b - a
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-15:
        return None
    w = a - p
    u = (w[0] * s[1] - w[1] * s[0]) / den
    v = (w[0] * r[1] - w[1] * r[0]) / den
    if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0:
        return u
    return None


def closest_on_seg(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-18), 0.0, 1.0)
    c = a + t * ab
    return c, ab / (np.linalg.norm(ab) + 1e-18)


class Crackle:
    def __init__(self, P, thickness, scale, rng):
        """P: parameters (dict). thickness(x, y) -> glaze thickness in mm at conformal (x, y).
        scale(y) -> r(s)/r0, physical mm per conformal mm."""
        self.P, self.rng = P, rng
        self.thickness, self.scale = thickness, scale
        h = P["raster_mm"]
        self.h = h
        self.x0, self.x1 = P["x_range"]
        self.y0, self.y1 = P["y_range"]
        nx = int(round((self.x1 - self.x0) / h)) + 1
        ny = int(round((self.y1 - self.y0) / h)) + 1
        self.shape = (ny, nx)
        yy, xx = np.mgrid[0:ny, 0:nx]
        self.X = self.x0 + xx * h
        self.Y = self.y0 + yy * h
        e = thickness(self.X.ravel(), self.Y.ravel()).reshape(self.shape)
        self.e = e
        # shear-lag length, in conformal mm (physical length / local scale)
        self.ell = P["lag_per_thickness"] * e / scale(self.Y)
        self.ell_f = Field(self.ell, self.x0, self.y0, h)
        self.e_f = Field(e, self.x0, self.y0, h)
        # strength: flaws (smooth random field + point defects such as bubbles), and the energy
        # floor that makes thin glaze harder to crack (G ~ s^2 e)
        corr_px = P["strength_corr_mm"] / h
        flaw = 1.0 + P["strength_spread"] * gaussian_field(self.shape, corr_px, rng)
        nd = rng.poisson(P["defects_per_cm2"] * (self.x1 - self.x0) * (self.y1 - self.y0) / 100.0)
        if nd:
            dx = rng.integers(0, nx, nd)
            dy = rng.integers(0, ny, nd)
            dip = np.zeros(self.shape)
            dip[dy, dx] = rng.uniform(0.2, 1.0, nd)
            dip = ndimage.gaussian_filter(dip, P["defect_radius_mm"] / h) * 2 * math.pi * (P["defect_radius_mm"] / h) ** 2
            flaw = flaw * (1.0 - P["defect_depth"] * np.clip(dip, 0, 1))
        # channel-cracking stress s_ch ~ 1/sqrt(e): what it takes to run; a flaw must also reach it
        channel = P["channel_stress"] * np.sqrt(P["e_ref_mm"] / np.maximum(e, 1e-3))
        self.channel_f = Field(channel, self.x0, self.y0, h)
        self.strength = np.maximum(np.maximum(flaw, 0.05), channel)
        self.strength_f = Field(self.strength, self.x0, self.y0, h)
        # normalised stress tensor M (stress = load * M), kept on the raster so nucleation and
        # propagation see the same field. Each crack multiplies in its relaxation
        # A = I - w (n n^T + nu t t^T), w = exp(-d/ell), symmetrically: M <- M^1/2 A M^1/2.
        # Between two parallel cracks this gives 1 - (1-w1)(1-w2), within a few % of the exact
        # shear-lag strip 1 - (w1+w2)/(1+w1 w2); perpendicular cracks simply add.
        self.cap = 6.0 * float(self.ell.max())
        self.Mxx = np.ones(self.shape)
        self.Mxy = np.zeros(self.shape)
        self.Myy = np.ones(self.shape)
        for edge in P.get("free_edges", ()):   # real free edges (a rim) relax the stress across them
            d = (self.Y - self.y0) if edge == "bottom" else (self.y1 - self.Y)
            w = np.exp(-d / self.ell)
            self.Myy *= 1 - w
            self.Mxx *= 1 - P["poisson"] * w
        self.segs = SegmentHash(P["hash_cell_mm"])
        self.cracks = []
        self.tips = []   # arrested crack tips, which run on when the load rises
        # the border of the simulated patch (outside the frame): cracks stop there, it relaxes nothing
        c = [np.array(v, float) for v in ((self.x0, self.y0), (self.x1, self.y0), (self.x1, self.y1), (self.x0, self.y1))]
        for i in range(4):
            self.segs.add(c[i], c[(i + 1) % 4], -1)

    # --- stress ------------------------------------------------------------------------
    @staticmethod
    def eig(a, b, c):
        """Eigen-decomposition of the symmetric stress [[a, b], [b, c]]: (lam_min, lam_max,
        direction of lam_min). A crack runs along the lam_min direction (it opens against lam_max)."""
        m = 0.5 * (a + c)
        r = np.sqrt(0.25 * (a - c) ** 2 + b ** 2)
        lo, hi = np.clip(m - r, 0.0, None), np.clip(m + r, 0.0, None)
        # eigenvector of the smaller eigenvalue
        vx, vy = b, (m - r) - a
        alt = np.abs(vx) + np.abs(vy) < 1e-9
        vx = np.where(alt, (m - r) - c, vx)
        vy = np.where(alt, b, vy)
        n = np.sqrt(vx ** 2 + vy ** 2) + 1e-18
        return lo, hi, vx / n, vy / n

    def stress_at(self, p):
        f = lambda A: float(Field(A, self.x0, self.y0, self.h)(p[0], p[1])[0])
        lo, hi, vx, vy = self.eig(f(self.Mxx), f(self.Mxy), f(self.Myy))
        return float(lo), float(hi), np.array([float(vx), float(vy)])

    # --- one crack ---------------------------------------------------------------------
    def extend(self, p, d, skip, load):
        """Run a crack tip from p along d at this load until it meets a crack or the border
        (joined) or the stress can no longer drive it. skip: ids of cracks it cannot meet
        (itself, and the crack it continues). Returns (points, joined, direction)."""
        P = self.P
        p = np.array(p, float)
        pts = [p.copy()]
        joined = False
        # In equal biaxial tension a straight crack is neutrally stable (T-stress 0,
        # Cotterell & Rice 1980): it keeps its direction and drifts only as the glaze
        # varies, so where the stress has no axis the path has a slowly varying random
        # curvature (std curv_std, correlated over curv_corr_mm): arcs, not wiggles.
        kappa = P["curv_std"] * self.rng.standard_normal()
        for _ in range(P["max_steps"]):
            ell = float(self.ell_f(p[0], p[1])[0])
            step = P["step_per_lag"] * ell
            lo, hi, v = self.stress_at(p + 0.5 * step * d)   # the tip feels the glaze just ahead
            c = v if np.dot(v, d) >= 0 else -v
            aniso = (hi - lo) / max(hi, 1e-9)
            rho = math.exp(-step / P["curv_corr_mm"])
            kappa = rho * kappa + math.sqrt(1 - rho * rho) * P["curv_std"] * self.rng.standard_normal()
            # steering by the stress where it has an axis, drift where it has none
            k = P["steer"] * aniso
            ang = math.atan2(d[1], d[0])
            target = math.atan2(c[1], c[0])
            dang = (target - ang + math.pi) % (2 * math.pi) - math.pi
            ang += k * dang + (1 - aniso) * kappa * step
            d = np.array([math.cos(ang), math.sin(ang)])
            q = p + step * d
            # stop at the first crack (or border) the step crosses: a T junction
            hit_u, hit = None, None
            for i in self.segs.near((p + q) / 2, step):
                if self.segs.crack[i] in skip:
                    continue
                u = seg_intersect(p, q, self.segs.a[i], self.segs.b[i])
                if u is not None and (hit_u is None or u < hit_u):
                    hit_u, hit = u, i
            if hit is not None:
                pts.append(p + hit_u * (q - p))
                joined = True
                break
            # the tip stops where the stress it feels is below s_ch, unless a crack ahead raises
            # it enough (ahead_factor)
            sc = float(self.channel_f(q[0], q[1])[0])
            if load * hi < sc:
                short = (sc / max(load * hi, 1e-12)) ** 2 - 1   # ahead_factor^2 - 1 must reach this
                reach = min(ell / short, P["ahead_max_lags"] * ell)
                if self.ahead(p, d, reach, skip) is None:
                    break
            pts.append(q)
            p = q
        return pts, joined, d

    def ahead(self, p, d, reach, skip):
        """Distance from p along d to the first crack (not in skip) within reach, or None."""
        r = p + reach * d
        best = None
        for i in self.segs.near((p + r) / 2, 0.5 * reach):
            if self.segs.crack[i] in skip:
                continue
            u = seg_intersect(p, r, self.segs.a[i], self.segs.b[i])
            if u is not None and (best is None or u < best):
                best = u
        return None if best is None else best * reach

    def ahead_factor(self, p, d, ell, skip):
        """How much a crack straight ahead, at distance x, raises the stress that drives the
        tip: sqrt(1 + ell/x). The ligament carries what the crack sheds, over the shear-lag
        length; as it shrinks the stress intensity grows like that of a crack near a free
        edge (Tada, Paris & Irwin), ~ sqrt(ell/x). The interpolating form is ours."""
        x = self.ahead(p, d, self.P["ahead_max_lags"] * ell, skip)
        return 1.0 if x is None else math.sqrt(1 + ell / max(x, 1e-9))

    def restart_load(self, tip):
        """The load at which an arrested tip runs on: the arrest test of extend, solved for the
        load. The glaze ahead of a tip is not relaxed by its own crack (_update_distance)."""
        p, d = tip["p"], tip["d"]
        ell = float(self.ell_f(p[0], p[1])[0])
        step = self.P["step_per_lag"] * ell
        lo, hi, v = self.stress_at(p + 0.5 * step * d)
        q = p + step * d
        f = self.ahead_factor(p, d, ell, (tip["crack"],))
        need = float(self.channel_f(q[0], q[1])[0]) / max(hi * f, 1e-9)
        return max(need, tip.get("min_load", 0.0))

    def _add_tip(self, crack, end, p, d):
        tip = {"crack": crack, "end": end, "p": np.array(p, float), "d": d}
        tip["need"] = self.restart_load(tip)
        self.tips.append(tip)

    def _refresh_tips(self, sl):
        """Recompute the restart load of tips inside a window whose stress has changed."""
        for t in self.tips:
            iy = (t["p"][1] - self.y0) / self.h
            ix = (t["p"][0] - self.x0) / self.h
            if sl[0].start <= iy <= sl[0].stop and sl[1].start <= ix <= sl[1].stop:
                t["need"] = self.restart_load(t)

    def _add(self, crack):
        cid = len(self.cracks)
        self.cracks.append(crack)
        self._relax(crack["pts"], cid)
        return cid

    def _relax(self, pts, cid):
        """Register a new stretch of crack cid and let it relax the glaze around it."""
        for i in range(len(pts) - 1):
            self.segs.add(pts[i], pts[i + 1], cid)
        self._last_window = self._update_distance(pts)
        self._refresh_tips(self._last_window)

    def grow(self, p0, load, gen):
        """A new crack from p0, both ways along the weaker principal direction."""
        P = self.P
        cid = len(self.cracks)
        lo, hi, v = self.stress_at(p0)
        if hi - lo < 0.05 * max(hi, 1e-9):   # nearly isotropic: no preferred direction yet
            a = self.rng.uniform(0, math.pi)
            d0 = np.array([math.cos(a), math.sin(a)])
        else:
            d0 = v
        a = self.extend(p0, d0, (cid,), load)
        b = self.extend(p0, -d0, (cid,), load)
        pts = np.array(a[0][::-1] + b[0][1:])
        if len(pts) < 2 or np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() < P["min_crack_mm"]:
            return None
        self._add({"gen": gen, "load": round(float(load), 5), "pts": pts, "joined": [a[1], b[1]]})
        for end, (side_pts, joined, d) in enumerate((a, b)):
            if not joined:
                self._add_tip(cid, end, side_pts[-1], d)
        return cid

    def resume(self, tip, load, gen):
        """An arrested tip runs on. In its own generation the crack just gets longer; in a later
        one the new stretch opens (and is stained) then, so it is a crack of that generation.
        A run that reaches another crack counts however short it is."""
        parent = self.cracks[tip["crack"]]
        same = parent["gen"] == gen
        cid = tip["crack"] if same else len(self.cracks)
        pts, joined, d = self.extend(tip["p"], tip["d"], (cid, tip["crack"]), load)
        pts = np.array(pts)
        length = np.linalg.norm(np.diff(pts, axis=0), axis=1).sum()
        if joined and length < 1e-6:   # a later crack already passes through the tip
            self.tips.remove(tip)
            parent["joined"][tip["end"]] = True
            return None
        if not joined and length < self.P["min_crack_mm"]:
            tip["min_load"] = load * 1.01   # the first step turned where it cannot go yet
            tip["need"] = self.restart_load(tip)
            return None
        self.tips.remove(tip)
        if same:
            if tip["end"] == 0:
                parent["pts"] = np.vstack([pts[::-1], parent["pts"][1:]])
            else:
                parent["pts"] = np.vstack([parent["pts"], pts[1:]])
            parent["joined"][tip["end"]] = joined
            self._relax(pts, cid)
            end = tip["end"]
        else:
            parent["joined"][tip["end"]] = True
            self._add({"gen": gen, "load": round(float(load), 5), "pts": pts, "joined": [True, joined],
                       "from": tip["crack"]})
            end = 1
        if not joined:
            self._add_tip(cid, end, pts[-1], d)
        return cid

    def _update_distance(self, pts):
        """Add the new crack's relaxation exp(-d/ell) n n^T, in a window around it.
        Along its flanks a crack frees the glaze; straight ahead of an end it does not (ahead
        of a channel-crack tip the stress is concentrated, not relaxed), so beyond an end the
        relaxation is scaled by sin^2 of the angle off the crack's line."""
        pad = self.cap
        lo = np.floor((pts.min(0) - pad - [self.x0, self.y0]) / self.h).astype(int)
        hi = np.ceil((pts.max(0) + pad - [self.x0, self.y0]) / self.h).astype(int)
        lo = np.maximum(lo, 0)
        hi = np.minimum(hi, [self.shape[1] - 1, self.shape[0] - 1])
        win = np.ones((hi[1] - lo[1] + 1, hi[0] - lo[0] + 1), bool)
        tx = np.zeros(win.shape)
        ty = np.zeros(win.shape)
        for i in range(len(pts) - 1):
            seg_d = pts[i + 1] - pts[i]
            L = np.linalg.norm(seg_d)
            if L < 1e-12:
                continue
            n = max(2, int(L / (0.5 * self.h)) + 1)
            seg = np.linspace(pts[i], pts[i + 1], n)
            gx = np.round((seg[:, 0] - self.x0) / self.h).astype(int) - lo[0]
            gy = np.round((seg[:, 1] - self.y0) / self.h).astype(int) - lo[1]
            ok = (gx >= 0) & (gx < win.shape[1]) & (gy >= 0) & (gy < win.shape[0])
            win[gy[ok], gx[ok]] = False
            tx[gy[ok], gx[ok]] = seg_d[0] / L
            ty[gy[ok], gx[ok]] = seg_d[1] / L
        # the two ends, with the outward direction of the crack there
        ox = np.zeros(win.shape)
        oy = np.zeros(win.shape)
        for end, prev in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            o = end - prev
            o = o / (np.linalg.norm(o) + 1e-18)
            gx = int(round((end[0] - self.x0) / self.h)) - lo[0]
            gy = int(round((end[1] - self.y0) / self.h)) - lo[1]
            if 0 <= gx < win.shape[1] and 0 <= gy < win.shape[0]:
                ox[gy, gx], oy[gy, gx] = o
        d, (iy, ix) = ndimage.distance_transform_edt(win, return_indices=True)
        t_x, t_y = tx[iy, ix], ty[iy, ix]
        nx, ny = -t_y, t_x
        jy, jx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
        cos_a = ((jx - ix) * ox[iy, ix] + (jy - iy) * oy[iy, ix]) / np.maximum(d, 1e-9)
        ahead = 1 - np.clip(cos_a, 0, 1) ** 2   # 1 off the ends (o = 0 there), 0 straight ahead
        d = d * self.h
        sl = (slice(lo[1], hi[1] + 1), slice(lo[0], hi[0] + 1))
        w = np.exp(-d / self.ell[sl]) * ahead
        nu = self.P["poisson"]
        # a free edge removes the stress across it, and (Poisson) a fraction nu of the stress
        # along it: next to a crack the glaze is in uniaxial tension (1 - nu) s0
        axx = 1 - w * (nx * nx + nu * t_x * t_x)
        axy = -w * (nx * ny + nu * t_x * t_y)
        ayy = 1 - w * (ny * ny + nu * t_y * t_y)
        mxx, mxy, myy = self.Mxx[sl], self.Mxy[sl], self.Myy[sl]
        # closed-form square root of a 2x2 positive semi-definite matrix
        s = np.sqrt(np.clip(mxx * myy - mxy * mxy, 0, None))
        t = np.sqrt(np.clip(mxx + myy + 2 * s, 1e-30, None))
        rxx, rxy, ryy = (mxx + s) / t, mxy / t, (myy + s) / t
        # M <- R A R with R = M^1/2
        bxx = axx * rxx + axy * rxy
        bxy = axx * rxy + axy * ryy
        byx = axy * rxx + ayy * rxy
        byy = axy * rxy + ayy * ryy
        self.Mxx[sl] = rxx * bxx + rxy * byx
        self.Mxy[sl] = rxx * bxy + rxy * byy
        self.Myy[sl] = rxy * bxy + ryy * byy
        return sl

    # --- the whole history -------------------------------------------------------------
    def run(self, loads):
        """loads: [(load_at_end_of_generation, gen), ...] in increasing order."""
        P = self.P
        margin = int(P["nucleation_margin_mm"] / self.h)
        _, hi, _, _ = self.eig(self.Mxx, self.Mxy, self.Myy)
        ratio = hi / self.strength
        keep = np.zeros(self.shape, bool)
        keep[margin:self.shape[0] - margin, margin:self.shape[1] - margin] = True
        ratio[~keep] = 0
        load = 0.0
        for load_end, gen in loads:
            n_gen = n_run_on = 0
            while True:
                # the next event as the load rises: a new crack, or an arrested tip running on
                k = int(np.argmax(ratio))
                need = 1.0 / max(ratio.flat[k], 1e-12)   # load at which this point cracks
                tip = min(self.tips, key=lambda t: t["need"], default=None)
                need_tip = tip["need"] if tip else math.inf
                if min(need, need_tip) > load_end:
                    break
                if need_tip <= need:
                    load = max(load, need_tip)
                    cid = self.resume(tip, load, gen)
                    n_run_on += cid is not None
                else:
                    load = max(load, need)
                    iy, ix = divmod(k, self.shape[1])
                    p0 = np.array([self.X[iy, ix], self.Y[iy, ix]])
                    cid = self.grow(p0, load, gen)
                    if cid is None:   # starts on a crack, or dies at once: not a place to crack
                        ratio[max(0, iy - 2):iy + 3, max(0, ix - 2):ix + 3] = 0
                        continue
                    n_gen += 1
                if cid is not None:
                    sl = self._last_window
                    _, hi, _, _ = self.eig(self.Mxx[sl], self.Mxy[sl], self.Myy[sl])
                    ratio[sl] = np.where(keep[sl], hi / self.strength[sl], 0)
                if len(self.cracks) % 200 == 0 and cid is not None:
                    print(f"  {len(self.cracks)} cracks (gen {gen}, load {load:.3f})", flush=True)
            print(f"generation {gen}: {n_gen} new cracks, {n_run_on} tips ran on, up to load {load_end}; "
                  f"{len(self.tips)} tips left")
        return self.cracks


def domain_stats(cr, gen_max):
    """Characteristic spacing l = sqrt(A/N), counting the domains enclosed by cracks of
    generation <= gen_max (rasterised, so very small domains are approximate)."""
    wall = np.zeros(cr.shape, bool)
    for c in cr.cracks:
        if c["gen"] > gen_max:
            continue
        pts = c["pts"]
        for i in range(len(pts) - 1):
            n = max(2, int(np.linalg.norm(pts[i + 1] - pts[i]) / (0.5 * cr.h)) + 1)
            seg = np.linspace(pts[i], pts[i + 1], n)
            gx = np.round((seg[:, 0] - cr.x0) / cr.h).astype(int)
            gy = np.round((seg[:, 1] - cr.y0) / cr.h).astype(int)
            ok = (gx >= 0) & (gx < cr.shape[1]) & (gy >= 0) & (gy < cr.shape[0])
            wall[gy[ok], gx[ok]] = True
    lab, n = ndimage.label(~ndimage.binary_dilation(wall))
    sizes = np.bincount(lab.ravel())[1:] * cr.h ** 2
    sizes = sizes[sizes > 4 * cr.h ** 2]
    area = (cr.x1 - cr.x0) * (cr.y1 - cr.y0)
    return {"domains": int(len(sizes)), "l_mm": round(math.sqrt(area / max(len(sizes), 1)), 2),
            "median_area_mm2": round(float(np.median(sizes)), 2) if len(sizes) else None}


def preview(cr, path, px_per_mm=8):
    """Black iron-wire and ginger golden-thread lines on the glaze colour, for checking the pattern."""
    from PIL import Image, ImageDraw
    w = int((cr.x1 - cr.x0) * px_per_mm)
    h = int((cr.y1 - cr.y0) * px_per_mm)
    im = Image.new("RGB", (w, h), (168, 182, 170))
    dr = ImageDraw.Draw(im)
    for gen, col, width in ((2, (196, 150, 72), max(1, px_per_mm // 6)), (1, (38, 34, 32), max(1, px_per_mm // 3))):
        for c in cr.cracks:
            if c["gen"] != gen:
                continue
            xy = [((x - cr.x0) * px_per_mm, (cr.y1 - y) * px_per_mm) for x, y in c["pts"]]
            dr.line(xy, fill=col, width=width)
    im.save(path)


DEFAULTS = {
    "x_range": [-60.0, 60.0],      # conformal mm around the pot (crack region; the frame is inside)
    "y_range": [-35.0, 35.0],      # conformal mm along the profile
    "raster_mm": 0.1,
    "hash_cell_mm": 2.0,
    "glaze_mm": 1.2,               # Li et al. 2001: 0.5 to 1-2 mm
    "lag_per_thickness": 5.5,      # shear-lag length / glaze thickness, calibrated on Met 52611 (docs/shots/06-guan.md)
    "step_per_lag": 0.12,
    "steer": 0.55,                 # how fast the tip turns to follow the stress
    "curv_std": 0.017,             # path curvature where the stress has no axis (1/mm)
    "curv_corr_mm": 25.0,          # over which that curvature changes
    "strength_spread": 0.10,
    "strength_corr_mm": 3.0,
    "defects_per_cm2": 3.0,        # bubbles / flaws near the surface that start cracks
    "defect_radius_mm": 0.15,
    "defect_depth": 0.35,
    "poisson": 0.22,               # glass, about 0.2-0.25
    "min_crack_mm": 0.3,
    "ahead_max_lags": 5.0,         # cracks further ahead than this (in shear-lag lengths) do not help a tip
    "channel_stress": 0.45,        # s_ch / s_flaw at e_ref = Y sqrt(pi a / (Z e)), a = 0.12 mm
    "e_ref_mm": 1.2,
    "nucleation_margin_mm": 2.0,
    "max_steps": 4000,
    "loads": [[1.15, 1], [6.0, 2]],# end of cooling (generation 1; with lag_per_thickness, calibrated),
                                   # later moisture expansion (2; not calibrated yet)
    "free_edges": [],
    "seed": 6,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview")
    ap.add_argument("--set", nargs="*", default=[], help="key=json overrides, e.g. glaze_mm=1.5")
    ap.add_argument("--form", help="form.json: simulate on that vase's conformal map (vessel.py) "
                                   "instead of a flat patch")
    a = ap.parse_args()
    P = dict(DEFAULTS)
    for kv in a.set:
        k, v = kv.split("=", 1)
        if k not in P:
            sys.exit(f"unknown parameter {k}")
        P[k] = json.loads(v)
    rng = np.random.default_rng(P["seed"])
    e0 = P["glaze_mm"]
    # thickness: uniform for now; the glaze-flow model will supply e(s) (thin at ridges and rim)
    thickness = lambda x, y: np.full(np.shape(x), e0, float)
    scale = lambda y: np.ones(np.shape(y))
    if a.form:
        from vessel import Vessel
        v = Vessel(a.form)
        scale = lambda y: v.scale(np.asarray(y, float))
    cr = Crackle(P, thickness, scale, rng)
    cr.run([(float(l), int(g)) for l, g in P["loads"]])
    stats = {g: domain_stats(cr, g) for g in sorted({c["gen"] for c in cr.cracks})}
    for g, s in stats.items():
        ends = [j for c in cr.cracks if c["gen"] == g for j in c["joined"]]
        s["free_ends"] = f"{ends.count(False)}/{len(ends)}"
        print(f"gen <= {g}: {s['domains']} domains, l = sqrt(A/N) = {s['l_mm']} mm = {s['l_mm'] / e0:.1f} e; "
              f"gen {g} free ends {s['free_ends']}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"params": P, "stats": stats,
                   "cracks": [{"gen": c["gen"], "load": c["load"], "joined": c["joined"],
                               **({"from": c["from"]} if "from" in c else {}),
                               "pts": np.round(c["pts"], 4).tolist()} for c in cr.cracks]}, f)
    if a.preview:
        preview(cr, a.preview)
    print(f"{len(cr.cracks)} cracks -> {a.out}")


if __name__ == "__main__":
    main()
