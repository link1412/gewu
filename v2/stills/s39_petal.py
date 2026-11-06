"""One lotus petal for s39_cand.py: a coarse surface that can be posed, and its maps, drawn in the plan of the petal.

Set against ref/lotus_petal (looked at in close-up; numbers below are read off those pictures by eye, or estimated):
- the outline is an ogive: both flanks convex, meeting at about 80-110 degrees, with a tiny dry nib. Not a cone: the old surface was a section of constant angle, so its radius went to zero at the tip and every petal ended in a tent. Here the section has a radius of its own (a spoon), bounded away from zero;
- veins: 25-35 long veins, forking and merging, wandering a little, converging on the tip, the outer ones running out at the margin. Between them ladders of cross-veins, sparse at the base, and near the tip a net of small cells. They are thin, and darker than the tissue because they hold more pigment. The short dashes of the old petal were a noise field, and they are gone;
- tissue: paler between the veins, frosted at the scale of the cells, with glassy pale patches here and there, thicker and whiter to the base;
- a thin deep line along the margin, a blush behind it.
Sizes are estimates (petal 10-13 x 6-8 cm). Nothing is traced from a photograph.
"""

import os

import cv2
import numpy as np
import scipy.ndimage as ndi
from scipy.interpolate import PchipInterpolator
from scipy.spatial import Voronoi

OUTL = PchipInterpolator([0.0, 0.08, 0.2, 0.34, 0.5, 0.64, 0.76, 0.86, 0.93, 0.975, 1.0], [0.3, 0.42, 0.66, 0.87, 1.0, 0.99, 0.89, 0.7, 0.5, 0.28, 0.0])
MARG = 1.34  # the map is this many petal widths across, for leaning and lopsided petals
NIB = 0.09  # cm, length of the dry point; an estimate


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blob(seed, shape, sigma):
    """A smooth field on a fixed coarse grid, unit deviation: the same whatever the resolution it is later opened to."""
    f = ndi.gaussian_filter(np.random.default_rng(seed).normal(size=shape).astype(np.float32), sigma, mode="reflect")
    return f / (f.std() + 1e-6)


def lerp3(a, b, t):
    return np.array(a, np.float32) + (np.array(b, np.float32) - np.array(a, np.float32)) * t[..., None].astype(np.float32)


def op(f, ny, nx):
    return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)


def smooth1(rng, n, sig):
    f = ndi.gaussian_filter1d(rng.normal(size=n), sig, mode="reflect")
    return f / (f.std() + 1e-9)


class Shape:
    """Outline of a petal on a dense fixed s grid, so that mesh and maps agree at any quality."""

    N = 2048

    def __init__(self, sp):
        self.sp = sp
        L, W = sp["L"], sp["W"]
        r = np.random.default_rng(sp["seed"] + 1)
        s = np.linspace(0, 1, self.N)
        nb = np.random.default_rng(sp["seed"] + 31)
        self.nib = NIB * (nb.uniform(0.15, 0.4) if nb.random() < 0.45 else nb.uniform(0.5, 1.0))  # most tips end in hardly any point; no two alike
        e = self.nib / L
        sq = np.clip(s / (1 - e), 0, 1)
        peak = r.uniform(-0.1, 0.1)  # where it is widest
        w = OUTL(np.clip(sq - peak * np.sin(np.pi * sq), 0, 1)) ** sp.get("rp", r.uniform(0.72, 1.18))  # blunt or pointed: no two alike
        asym = sp.get("asym", r.uniform(-0.12, 0.12))  # one flank fuller than the other
        hwn = 0.035 / (0.5 * W) * (1 - sstep(1 - 3.5 * e, 1.0, s))  # the nib
        w = np.sqrt(w * w + hwn * hwn)
        w = ndi.gaussian_filter1d(w, 2.0, mode="nearest")
        w[-1] = 1e-4
        wig = 0.012 * smooth1(r, self.N, 60) + 0.004 * smooth1(r, self.N, 14)
        self.s = s
        self.hw = 0.5 * W * np.maximum(w, 1e-4) * (1 + wig * sstep(0.0, 0.3, 1 - s))
        self.hwmax = float(self.hw.max())
        self.cs = sp.get("lean", 0.0) * s**2 + 0.05 * W * r.uniform(-0.25, 0.25) * sstep(0.5, 1.0, s) * 1.0
        self.cs = self.cs + 0.012 * W * smooth1(r, self.N, 300) * sstep(0.0, 0.3, s) * (1 - sstep(0.7, 1.0, s)) + asym * self.hw

    def at(self, s):
        return np.interp(s, self.s, self.hw), np.interp(s, self.s, self.cs)


class Mesh:
    """The surface. All displacements are in cm of the plan, so they die out with the width towards the tip."""

    def __init__(self, sp, ny, nx):
        self.sp = sp
        self.shape = Shape(sp)
        t = np.linspace(0, 1, ny)
        self.s = 1 - (1 - t) ** 1.45  # rows close up to the tip
        self.u = np.sin(0.5 * np.pi * np.linspace(-1, 1, nx))
        self.hw, self.cs = self.shape.at(self.s)
        U, S = np.meshgrid(self.u, self.s)
        self.U, self.S, self.A = U, S, np.abs(U)
        self.x = U * self.hw[:, None]
        self.rel = self.hw[:, None] / self.shape.hwmax  # 1 at the widest, 0 at the tip
        sd = sp["seed"]
        # coarse relief: long buckles along the veins, a few broad dimples
        uu = ((U + 1) * 0.5 * 95).astype(np.float32)
        ss = (S * 191).astype(np.float32)
        long_ = cv2.remap(blob(sd + 7, (192, 96), (24, 3.0)), uu, ss, cv2.INTER_CUBIC)
        wide = cv2.remap(blob(sd + 8, (192, 96), (14, 10)), uu, ss, cv2.INTER_CUBIC)
        r = np.random.default_rng(sd + 2)
        ruf_l = np.interp(self.s, np.linspace(0, 1, 512), smooth1(r, 512, 26))
        ruf_r = np.interp(self.s, np.linspace(0, 1, 512), smooth1(r, 512, 26))
        ruf = np.where(U < 0, ruf_l[:, None], ruf_r[:, None])
        rel = self.rel
        # what makes this petal this petal, all drawn per petal: a tip that turns back or hooks in, a bend across, a fold along, margins that roll
        self.reflex = sp.get("reflex", r.normal(0, 11) + (r.choice([-1.0, 1.0]) * r.uniform(18, 38) if r.random() < 0.28 else 0.0))
        self.kink, self.s0 = (r.choice([-1.0, 1.0]) * r.uniform(5, 15), r.uniform(0.35, 0.78)) if r.random() < 0.35 else (0.0, 0.5)
        hm = self.shape.hwmax
        fold = np.zeros_like(U)
        if r.random() < 0.42:
            x0, amp = r.uniform(-0.65, 0.65) * hm, r.choice([-1.0, 1.0]) * r.uniform(0.12, 0.34)
            fold = amp * (np.sqrt(((self.x - x0) / 0.22) ** 2 + 1) - 1) * 0.22 / hm * sstep(0.3, 0.75, S)
        cl, cr = [r.uniform(0.04, 0.3) + (r.uniform(0.3, 0.8) if r.random() < 0.3 else 0.0) for _ in (0, 1)]
        s1l, s1r = r.uniform(0.3, 0.7), r.uniform(0.3, 0.7)
        envl = sstep(s1l - 0.2, s1l, S) * (1 - 0.6 * sstep(0.88, 1.0, S))
        envr = sstep(s1r - 0.2, s1r, S) * (1 - 0.6 * sstep(0.88, 1.0, S))
        ct = np.clip((self.A - 0.66) / 0.34, 0, 1)
        self.roll_h = -(np.where(U < 0, cl * envl, cr * envr)) * ct**2  # rolls inward
        self.roll_x = -np.sign(U) * 0.55 * np.where(U < 0, cl * envl, cr * envr) * ct**3
        rug = r.uniform(0.05, 0.2)
        rollw = sp.get("roll", 0.3) * r.uniform(0.25, 1.2)
        dn = fold + sp.get("bump", 0.2) * 0.42 * long_ * sstep(0.0, 0.25, S) * rel + sp.get("bump", 0.2) * 0.5 * wide * rel
        dn = dn + rollw * self.A**6 * sstep(0.15, 0.6, S) * rel * 0.9 + rug * ruf * self.A**3 * sstep(0.1, 0.5, S) * rel
        dn = dn + 0.05 * np.exp(-((self.x / 0.45) ** 2)) * sstep(0.62, 0.97, S)  # the midrib stands out as a soft keel near the tip
        self.dn0 = dn
        self.uvw = np.stack([(self.x + self.cs[:, None]) / (MARG * sp["W"]) + 0.5, S, 0 * S], -1).astype(np.float32)

    def pose(self, flap=0.0, bend=0.0, twist=0.0, cup=0.0, el=None, er=None, tip=0.0):
        """Degrees, degrees, degrees, a share of the cross curvature, the two margins (cm, arrays along s), and degrees of curl at the tip."""
        sp, s = self.sp, self.s
        a = np.radians(sp["alpha"] + sp["beta"] * (1 - s) ** 1.6 - sp["gamma"] * s**1.8 + flap + bend * s**1.6 + tip * sstep(0.68, 1.0, s) + self.reflex * sstep(0.7, 1.0, s) + self.kink * sstep(self.s0 - 0.04, self.s0 + 0.04, s))
        ds = np.diff(s, prepend=0.0) * sp["L"]
        rho = sp["r0"] + np.cumsum(np.sin(a) * ds)
        z = sp["zb"] + np.cumsum(np.cos(a) * ds)
        phi = np.radians(sp["az"] + sp.get("twist", 0.0) * s)
        psi = np.radians(sp["psi"]) * (1 - cup)
        Rm = self.shape.hwmax / np.sin(psi)
        Rc = np.hypot(self.hw / np.sin(psi), 0.62 * Rm)[:, None]
        x = self.x
        off = Rc - np.sqrt(np.maximum(Rc * Rc - x * x, 1e-6))
        h = self.dn0 - off + self.roll_h
        if el is not None:
            h = h + np.where(self.U < 0, el[:, None], er[:, None]) * self.A**2.5 * self.rel
        xx = x + self.cs[:, None] + self.roll_x
        if twist:
            tt = np.radians(twist) * (s**1.2)[:, None]
            c_, s_ = np.cos(tt), np.sin(tt)
            xx, h = xx * c_ - h * s_, xx * s_ + h * c_
        cp, sp_ = np.cos(phi)[:, None], np.sin(phi)[:, None]
        ca, sa = np.cos(a)[:, None], np.sin(a)[:, None]
        Px = rho[:, None] * cp - xx * sp_ + h * ca * cp
        Py = rho[:, None] * sp_ + xx * cp + h * ca * sp_
        Pz = z[:, None] - h * sa
        return np.stack([Px, Py, Pz], -1).astype(np.float32)


def vein_paths(sp, sh, ny):
    """Long veins in cm of the plan, row by row of an ny-row raster: (k, ny), and where each is alive."""
    r = np.random.default_rng(sp["seed"] + 3)
    s = np.linspace(0, 1, ny)
    hw, cs = sh.at(s)
    nk = int(np.clip(round(sp["W"] * 6.4), 24, 54)) + 10
    du = 2.3 / nk
    u0 = np.linspace(-1.15, 1.15, nk) + r.normal(0, 0.24 * du, nk)
    u0 = np.sort(u0)
    start = np.where(r.random(nk) < 0.74, 0.0, r.uniform(0.05, 0.55, nk))
    end = np.where(r.random(nk) < 0.8, r.uniform(0.985, 1.0, nk), r.uniform(0.72, 0.97, nk))
    amp = np.where(start == 0.0, r.uniform(0.66, 1.0, nk), r.uniform(0.42, 0.72, nk))
    amp = amp * (1 + 0.12 * smooth1(r, nk, 1.0))
    wid = np.where(start == 0.0, r.uniform(0.0075, 0.012, nk), r.uniform(0.006, 0.009, nk))
    W = np.zeros((nk, ny))
    N = 2048
    for k in range(nk):
        w = 0.22 * du * np.interp(s, np.linspace(0, 1, N), smooth1(r, N, 420))
        W[k] = u0[k] * (1 + 0.16 * np.abs(u0[k]) * sstep(0.35, 1.0, s)) + w * (1 - sstep(0.75, 1.0, s) * 0.8) * sstep(0.0, 0.2, s)
    W = np.sort(W, axis=0)  # veins do not cross; where they would, they touch and part: the look of a merge
    W = ndi.gaussian_filter1d(W, 0.012 * ny, axis=1, mode="nearest")  # the swap at such a meeting must not leave a kink; a vein runs straight and long
    for k in range(nk):
        if start[k] > 0:
            j = k - 1 if k > 0 and (k == nk - 1 or r.random() < 0.5) else k + 1
            W[k] = W[j] + (W[k] - W[j]) * sstep(start[k], start[k] + 0.16, s)
        if end[k] < 0.98:
            j = k - 1 if k > 0 and (k == nk - 1 or r.random() < 0.5) else k + 1
            W[k] = W[k] + (W[j] - W[k]) * sstep(end[k] - 0.14, end[k], s)
    # the small wobble of the margin must not pass into every vein
    X = W * ndi.gaussian_filter1d(hw, 0.025 * ny, mode="nearest") * (1 - 0) + ndi.gaussian_filter1d(cs, 0.025 * ny, mode="nearest")
    return s, W, X, start, end, amp, wid


def maps(sp, sh, dens):
    """(col, tr, aux) float32 images, row 0 at the base."""
    L, Wd = sp["L"], sp["W"]
    pxcm = 92.0 * dens * sp.get("d", 1.0)
    ny, nx = max(int(L * pxcm), 96), max(int(MARG * Wd * pxcm), 72)
    pxy, pxx = ny / L, nx / (MARG * Wd)
    sd = sp["seed"]
    r = np.random.default_rng(sd + 4)
    s, W, X, start, end, amp, wid = vein_paths(sp, sh, ny)
    hw, cs = sh.at(s)
    xs = (np.arange(nx) + 0.5) / nx * MARG * Wd - 0.5 * MARG * Wd
    Xg, Sg = np.meshgrid(xs, s)
    U = (Xg - cs[:, None]) / np.maximum(hw[:, None], 1e-3)
    A = np.minimum(np.abs(U), 1.0)
    edge = (1 - A) * hw[:, None]  # roughly cm from the margin

    # --- veins. Long ones are written as profiles across the row, so they are sub-pixel at any quality
    vein = np.zeros((ny, nx), np.float32)
    halo = np.zeros((ny, nx), np.float32)
    rad = int(np.ceil(0.14 * pxx))
    offs = np.arange(-rad, rad + 1)
    rows = np.arange(ny)
    for k in range(W.shape[0]):
        alive = (s >= start[k]) & (s <= end[k]) & (np.abs(W[k]) < 1.0)
        if alive.sum() < 4:
            continue
        slope = np.gradient(X[k], L / (ny - 1))
        taper = 1 - 0.5 * sstep(0.5, 1.0, s)
        w = wid[k] * taper * np.sqrt(1 + slope**2)
        fade = sstep(start[k], start[k] + 0.08, s) * (1 - sstep(end[k] - 0.05, end[k], s)) if start[k] > 0 else (1 - sstep(end[k] - 0.05, end[k], s))
        # a vein is not one stroke: its pigment and its width come and go along its length
        along = np.interp(s, np.linspace(0, 1, 512), smooth1(r, 512, 22))
        fade = fade * np.clip(0.82 + 0.26 * along, 0.35, 1.25)
        w = w * np.clip(1 + 0.2 * np.interp(s, np.linspace(0, 1, 512), smooth1(r, 512, 34)), 0.6, 1.5)
        cx = (X[k] + 0.5 * MARG * Wd) * pxx - 0.5
        ci = np.round(cx).astype(int)
        for arr, m, a in ((vein, 1.0, 1.0), (halo, 3.4, 1.0)):
            ww = (w * m)[:, None] * pxx
            jj = ci[:, None] + offs
            ok = (jj >= 0) & (jj < nx) & alive[:, None]
            val = (amp[k] * fade)[:, None] * np.exp(-(((jj - cx[:, None]) / np.maximum(ww, 0.7)) ** 2))
            rr = np.broadcast_to(rows[:, None], jj.shape)
            np.maximum.at(arr, (rr[ok], jj[ok]), val[ok].astype(np.float32))

    # ladders and side branches, drawn as thin lines: thinner and fainter than the veins
    fine = np.zeros((ny, nx), np.uint8)  # anti-aliased lines are for 8 bits only
    SH = 4
    F = 1 << SH

    def seg(p, q, a):
        cv2.line(fine, (int(p[0] * F), int(p[1] * F)), (int(q[0] * F), int(q[1] * F)), int(np.clip(a, 0, 1) * 255), 1, cv2.LINE_AA, SH)

    def px(x, sv):
        return ((x + 0.5 * MARG * Wd) * pxx - 0.5, sv * (ny - 1))

    long_alive = np.where(np.abs(W).min(axis=1) < 1.0)[0]
    for k in long_alive[:-1]:
        sv = r.uniform(0.02, 0.12)
        while sv < 0.995:
            gap = (r.lognormal(np.log(1.05 - 0.78 * sstep(0.2, 0.85, sv)), 0.45)) / L
            sv += gap
            sw = sv + r.normal(0, 0.18) / L
            if sv >= 1 or sw >= 1 or sw <= 0:
                break
            i, j = int(sv * (ny - 1)), int(sw * (ny - 1))
            if not (start[k] <= sv <= end[k] and start[k + 1] <= sw <= end[k + 1]):
                continue
            if abs(W[k, i]) >= 1 or abs(W[k + 1, j]) >= 1:
                continue
            xa, xb = X[k, i], X[k + 1, j]
            mid = (0.5 * (xa + xb) + r.normal(0, 0.1) * abs(xb - xa), 0.5 * (sv + sw) + r.normal(0, 0.1) / L)
            ac = r.uniform(0.12, 0.42) * (0.45 + 0.55 * sstep(0.15, 0.7, sv))
            seg(px(xa, sv), px(*mid), ac)
            seg(px(*mid), px(xb, sw), ac)
            if r.random() < 0.3:  # a branch runs on along the vein, and stops, or meets the next rung
                n_ = int(r.uniform(2, 6))
                p = mid
                for _ in range(n_):
                    q = (p[0] + r.normal(0, 0.035) + (p[0] - np.interp(p[1], s, cs)) * 0.012, p[1] + r.uniform(0.2, 0.42) / L)
                    if q[1] >= 1:
                        break
                    seg(px(*p), px(*q), ac * 0.75)
                    p = q
    # the net near the tip: small cells, stretched along the veins, some walls missing
    area = float(np.trapezoid(2 * hw, s * L))
    npts = int(area * 7.5)
    pu = r.uniform(-1.02, 1.02, npts)
    ps = 1 - r.uniform(0, 1, npts) ** 1.35 * 0.72
    hp, cp = sh.at(ps)
    pts = np.stack([pu * hp + cp, ps * L / 1.7], -1)
    vor = Voronoi(pts)
    V = vor.vertices
    breakup = op(blob(sd + 15, (64, 48), (5, 5)), ny, nx)
    for a_, b_ in vor.ridge_vertices:
        if a_ < 0 or b_ < 0:
            continue
        pa, pb = V[a_], V[b_]
        sa, sb = pa[1] * 1.7 / L, pb[1] * 1.7 / L
        if not (0 <= sa <= 1 and 0 <= sb <= 1) or np.hypot(*(pa - pb)) > 1.2:
            continue
        sm = 0.5 * (sa + sb)
        keep = 0.28 + 0.6 * sstep(0.3, 0.9, sm)
        if r.random() > keep:
            continue
        ac = r.uniform(0.08, 0.34) * (0.3 + 0.7 * sstep(0.28, 0.85, sm))
        ln = np.hypot(*(pa - pb))
        mx_ = 0.5 * (pa[0] + pb[0]) + r.normal(0, 0.16) * ln
        my_ = 0.5 * (sa + sb) + r.normal(0, 0.16) * ln / L  # walls of cells are not straight
        seg(px(pa[0], sa), px(mx_, my_), ac)
        seg(px(mx_, my_), px(pb[0], sb), ac)
    fine = cv2.GaussianBlur(fine.astype(np.float32) / 255.0, (0, 0), 0.65) * 1.25 * min(1.0, dens**0.5 + 0.2)
    fine = fine * np.clip(0.8 + 0.28 * breakup, 0.25, 1.3)
    inside = (np.abs(U) <= 1.0).astype(np.float32)

    # --- the tissue. Different things at different scales, not one noise at many
    wash = op(blob(sd + 6, (96, 72), (12, 9)), ny, nx)
    streak = op(blob(sd + 9, (256, 96), (28, 2.2)), ny, nx)
    frost = cv2.GaussianBlur(np.random.default_rng(sd + 20).normal(size=(ny, nx)).astype(np.float32), (0, 0), max(0.6, 0.012 * pxx))
    frost = frost / frost.std()
    frost2 = cv2.GaussianBlur(np.random.default_rng(sd + 21).normal(size=(ny, nx)).astype(np.float32), (0, 0), max(0.8, 0.03 * pxx))
    frost2 = frost2 / frost2.std()
    # fine ribs of the tissue, long and narrow, following the veins only roughly: they break up the flat sheet, seen only close
    def pleat(seed, wid_u, hgt=128):
        """Noise long in s and narrow in u, read at (u, s), so that the pleats run with the veins and close up to the tip. Fixed grid: the same at any quality."""
        f = cv2.GaussianBlur(np.random.default_rng(seed).normal(size=(hgt, 1024)).astype(np.float32), (0, 0), sigmaX=wid_u * 512, sigmaY=2.0)
        f = f / f.std()
        return cv2.remap(f, ((np.clip(U, -1, 1) + 1) * 511.5).astype(np.float32), (Sg * (hgt - 1)).astype(np.float32), cv2.INTER_CUBIC)

    rib = pleat(sd + 22, 0.012)
    pl1 = pleat(sd + 23, 0.03, 96)
    pl2 = pleat(sd + 24, 0.08, 64)
    plz = np.clip(0.55 + 0.5 * op(blob(sd + 25, (64, 48), (7, 5)), ny, nx), 0.1, 1.4)  # some parts of a petal are more pleated than others
    window = sstep(0.9, 1.9, op(blob(sd + 16, (128, 96), (9, 3.0)), ny, nx) + 0.3 * wash)  # glassy pale patches, along the veins

    S = Sg
    g = sstep(sp.get("g0", 0.2) + 0.07 * wash, 0.98, S + 0.035 * wash) ** sp.get("gp", 1.12) + 0.42 * sstep(0.8, 1.0, S)
    rim = np.exp(-edge / 0.05) * (0.25 + 0.75 * sstep(0.12, 0.6, S))
    blush = np.exp(-edge / 0.34) * sstep(0.3, 0.8, S)
    v = vein * (0.5 + 0.5 * sstep(0.05, 0.5, S))
    p = sp["P"] * (g * (1 + 0.1 * streak + 0.12 * wash) * (1 - 0.34 * window) + 0.4 * blush * g**0.5)
    # veins hold pigment even where the tissue has none; that is what draws them in the white part
    p = p + sp["P"] * (0.18 + 0.82 * g**0.55) * (0.4 * v + 0.13 * halo + 0.42 * fine) + sp["P"] * 0.3 * rim
    p = np.maximum(p * (1 + 0.02 * frost + 0.035 * rib), 0.0)
    T = np.exp(-p[..., None] * np.array([0.03, 1.12, 0.56], np.float32))  # warm rose: two layers deepen to red, not to violet
    base = (1 - sstep(0.0, 0.46, S)) ** 1.35
    T = T * np.exp(-base[..., None] * np.array([0.0, 0.1, 0.95], np.float32))  # luminous cream, a warm heart
    deep = (1 - sstep(0.0, 0.11, S)) ** 2
    T = T * np.exp(-deep[..., None] * np.array([0.6, 0.12, 1.0], np.float32))  # then green at the claw
    warm = sstep(0.1, 0.45, S) * (1 - sstep(0.55, 0.9, S))
    nib = sstep(1 - 2.6 * sh.nib / L, 1 - 0.8 * sh.nib / L, S)
    T = T * (1 - nib[..., None] * np.array([0.3, 0.42, 0.46], np.float32))  # the dry point
    # marks, last and few: tiny dry specks, one scuff, a little pollen low down. Placed by how they come: at margins and low on the petal
    mark = np.zeros((ny, nx), np.float32)
    for _ in range(int(r.integers(0, 5))):
        i, j = int(r.uniform(0.15, 0.95) * ny), int(r.uniform(0.2, 0.8) * nx)
        cv2.circle(mark, (j, i), max(1, int(r.uniform(0.012, 0.03) * pxx)), float(r.uniform(0.3, 0.9)), -1, cv2.LINE_AA)
    mark = cv2.GaussianBlur(mark, (0, 0), max(0.6, 0.008 * pxx))
    T = T * (1 - mark[..., None] * np.array([0.55, 0.78, 0.82], np.float32))
    dry = np.exp(-edge / 0.05) * sstep(1.35, 2.2, op(blob(sd + 26, (128, 64), (9, 4)), ny, nx)) * sstep(0.45, 0.8, S)  # the margin dries in places
    T = T * (1 - np.clip(dry, 0, 1)[..., None] * np.array([0.32, 0.55, 0.7], np.float32))
    if r.random() < 0.5:
        pol = np.zeros((ny, nx), np.float32)
        for _ in range(int(r.integers(8, 40))):
            cv2.circle(pol, (int(r.uniform(0.25, 0.75) * nx), int(r.uniform(0.15, 0.45) * ny)), max(1, int(0.012 * pxx)), float(r.uniform(0.3, 1)), -1, cv2.LINE_AA)
        T = T * (1 - cv2.GaussianBlur(pol, (0, 0), 0.7)[..., None] * np.array([0.0, 0.2, 0.75], np.float32))
    scuff = sstep(1.6, 2.5, op(blob(sd + 27, (128, 96), (7, 2.0)), ny, nx))
    col = np.clip(T**1.25 * (0.86 + 0.008 * frost2[..., None]) * np.array([1.0, 0.97, 0.88], np.float32) + 0.05 * scuff[..., None], 0, 1)
    tr = np.clip(T * np.array([1.0, 0.95, 0.86], np.float32) * (1 + (0.012 * frost + 0.012 * frost2)[..., None]), 0, 1)
    tr = tr * (1 - 0.04 * warm[..., None] * np.array([0.0, 0.5, 1.0], np.float32))

    # --- how much goes through: thin to the tip and between veins, thick and white to the base
    thin = sstep(0.05, 0.8, S)
    k = 0.42 + 0.14 * thin - 0.06 * (v + 0.5 * fine) + 0.04 * window
    t = 0.035 + 0.15 * thin**1.2 - 0.05 * np.minimum(v + 0.6 * fine, 1.0) + 0.07 * window * thin
    marg = np.exp(-edge / 0.16)  # the margin thins out and catches the light through
    k = k + 0.12 * marg
    t = t + 0.08 * marg
    # --- relief: tissue pillows between the veins, the veins lie in shallow grooves on the outside
    pil = cv2.GaussianBlur(vein + 0.5 * fine, (0, 0), max(1.0, 0.03 * pxx))
    hgt = -0.035 * pil - 0.012 * cv2.GaussianBlur(halo, (0, 0), max(1.0, 0.05 * pxx)) + 0.0028 * frost2 + 0.0016 * frost + plz * (0.004 * rib + 0.009 * pl1 + 0.016 * pl2)
    aux = np.stack([0.5 + 3.0 * hgt, np.clip(k, 0.02, 0.8), np.clip(t, 0.0, 0.5)], -1)
    # beyond the outline nothing is sampled except by interpolation: carry the margin outward
    return col.astype(np.float32), tr.astype(np.float32), aux.astype(np.float32), inside


def write16(path, im):
    cv2.imwrite(path, (np.clip(im, 0, 1) * 65535 + 0.5).astype(np.uint16)[::-1, :, ::-1])  # an image's v runs up from the bottom row
    return path


def far_attrs(mesh, sp):
    """Colour per vertex for a petal far in the blur: only its gradient counts."""
    S, A = mesh.S, mesh.A
    g = sstep(sp.get("g0", 0.2), 0.98, S) ** 1.4 + 0.4 * sstep(0.8, 1.0, S)
    p = 1.7 * sp["P"] * (g + 0.25)
    T = np.exp(-p[..., None] * np.array([0.035, 1.12, 0.5], np.float32))
    return np.clip(T**1.3 * 0.86, 0, 1).astype(np.float32), np.clip(T * 0.92, 0, 1).astype(np.float32)
