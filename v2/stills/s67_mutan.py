"""Shot 67: burning hardwood charcoal, through a macro lens. Stands in for the kiln fire (charcoal with very little flame, macro).

    python3 -I v2/stills/s67_mutan.py [flat|preview|mid|final] [cand]
    python3 -I v2/stills/s67_mutan.py take [FRAMES] [ONLY]       1280x720, 480 px/cm, into out/v2/s67_mutan_take_cand/ (one render per frame: per-vertex emission cannot be animated through studio_bpy's take)
    python3 -I v2/stills/s67_mutan.py takefinal [FRAMES] [ONLY]  2560x1440, 800 px/cm, into out/v2/s67_mutan_move_final/ as float16 linear frames, as film.py reads them

What is in the frame: part of the sawn end of one split round of charred wood lying nearly flat, about 3.2 cm of it across the frame. The burnt outer edge of the round is the arc, rings run parallel to it.
A wide radial split with a lit floor, narrower checks, a brick work of fine cracks between rays and rings, vessels as open pores, a warm grey crust of ash in plates. A small tongue or two of flame on a ridge, out of focus.
The camera, the charcoal and the lights do not move. at_time(S, t) gives the state at t seconds: the air supply drifts one way and waves of heat go through the cracks, the crust's edge creeps forward, the flame's upper part sways. The still is t = 0.

How it is made:
- Wood anatomy first, in wood space (tau along the ring, rho along the ray), one mesh vertex per pixel of that space: rings of unequal width, ring-porous vessels (a row of large pores in the earlywood, flame-shaped groups of small ones in the latewood), broad and fine rays.
- Cracks follow the anatomy, as charring shrinkage does (looked up, doi 10.1007/s00226-005-0062-5, read only as a search summary: oak charcoal splits along broad rays; tangential shrinkage larger than radial, -26% vs -15% for white oak in a kiln): long radial checks start at the rim and run along rays, ring shakes run between them with T junctions, then fine checks fill the cells.
- The glow is not painted. T is a field (surface temperature from a slow air-supply field, hotter at depth because a cavity loses less radiation and cooler under ash), and colour and brightness come from it through Planck's law integrated over the CIE matching functions (Wyman, Sloan, Shirley 2013 fit, coefficients typed from memory, not checked against the paper) into linear Rec.709. Emissivity is 1 - albedo (Kirchhoff), so white ash at the same temperature is dim, without a rule for it.
- The glow lights the neighbouring surfaces by path tracing. The room gives only a dim sheen on the dark char.
- Flame: see flame_sheet. STAND-IN: an analytic shape and profile, no solver and no integration along the view. Not v2/stills/s42_fire.py.

ESTIMATES, by eye or general knowledge, not measured: T range 800-1230 K (clipped there); the red leak into the blue channel (a stand-in for a real sensor, by eye); the other coals (LUMPS), which are stand-ins with no anatomy, only seen blurred; ring width about 0.17 cm; vessels 0.012-0.03 cm (earlywood), 0.004-0.01 cm (latewood); ray widths 0.015-0.05 cm; crack sizes; ash thickness and albedo; char albedo 0.04.
Second version (the first read as a lava landscape, the flame as a gas ring): much finer cracks, a far smaller glowing area with one small bright centre, darker red, paler ash, pores in rows, graphite sheen, chipped split walls, one faint flame, blurred coals in front and behind.
Third version (ash read as frost, flame residue as a dirty spot): ash as hard plates with thin black cracks and clean edges, about half the cover, warmer; flakes removed; the flame 2-3 times larger and mainly orange.
Fourth version (coordinator: cracks like neon, flame a fang, crust like bark or stone): the glow lies in pieces, not lines: one or two hot places, orange to orange-yellow in depth, falling to dark red and to nothing, most cracks dull or dark, showing through thin powder and pores; exposure GAIN halved and the top T raised to 1300 K for that (1230 K from the fifth version). The flame fainter, lower, without an edge. The crust a fine light powder, its relief smoothed, breaking into grains at the edge.
Fifth version (coordinator: the glow a lit window with ladder lines, ash like snow or plaster, flame a seed, deep splits ruled, changing too fast): the glow is a large soft irregular area following the blocks, dark red to deep orange, brightest deep in the splits and along the lower edge of a block, and fine cracks no longer glow by themselves; ash is a thin grey-white powder, low albedo, fading out slowly so the black shows through, on ridges and block tops, broken at crack edges; flame a low thin sheet; splits irregular in spacing and direction, wider ring shakes make blocks; every rate halved.
Rates of change, ALL ESTIMATES, chosen by eye for a 1.5 s shot, not measured from a fire: see the constants under "time".
Lens, estimated: magnification 36 mm / 32 mm = 1.1:1; aperture 5.5 mm at 16 cm is an object-side half angle of about 0.017 rad, like a 100 mm macro near f/16 (effective about f/32), total depth of field about 1.5 mm (2 N c / m^2, c = 0.03 mm).
Compared with (looked at, not used; sources in ref/charcoal/SOURCES.txt): charbon (crack network, faces), rouge (ash plates, glow under ash), glut_closeup (speckle at ash edge).
"""

import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, rank, shoot, sstep
from vessel import fit_arc, project

NAME = "s67_mutan"
SEED = 6701
HERE = os.path.dirname(os.path.abspath(__file__))

# --- the frame ------------------------------------------------------------------------------------------------------
W = 3.2  # frame width at the subject, cm
EL, AZ = 20.0, 13.0  # camera elevation; yaw, so the band of focus runs across the rings at a slant
DIST = 16.0
APERTURE_MM = 5.5
TILT = np.radians(28.0)  # the face lies back this far from level
APEX = (0.54, 0.49)  # across the whole width, sagitta <= .20 (original median .08), apex x .45-.55, y .46-.52; measure with tools/arc.py
FOCUS_AT = (0.67, 0.78)  # where in the frame the plane of focus touches the face
LUMPS = ((0.1, 1.1, -2.6, (0.62, 0.45, 0.3)), (0.02, 0.9, 1.7, (1.0, 0.8, 0.5)), (0.99, 0.92, 1.5, (1.0, 0.85, 0.5)))  # frame x, y of the centre, cm behind the plane of focus, radii: one in front, low at the left; two behind, carrying the arc out to the sides
FLAMES = (((0.72, 0.535), (0.88, 0.60), 0.1),)  # a sheet: frame x, y of its two ends along a ridge; height, cm

# --- the piece --------------------------------------------------------------------------------------------------------
R = 4.4  # the radius of the round, pith to rim; rings' curvature, cm
R0 = 3.7  # radius at which tau is arc length
RHO0, RHO1 = 2.05, 4.8
TAU0, TAU1 = -2.55, 2.55
G = 120.0  # px/cm of the fixed grid for everything large: the composition must not change with the quality

# Temperature, K. Estimates. See temperature().
T_COLD, T_AIR, T_CAVITY, T_CAVITY_HOT, T_EDGE, T_ASH = 835.0, 255.0, 40.0, 125.0, 25.0, 15.0
ASH_PERCENTILE = 66  # of the score: how much of the face the crust covers
T_MAX = 1230.0  # the bright places reach orange to orange-yellow only because they are hotter, and only there
GAIN = 0.7  # scene radiance of a blackbody at 1150 K. The camera's exposure, nothing else

# --- time. All estimates, by eye. The still is t = 0; a take runs either side of it
DRIFT = np.array([-0.8, 0.6])  # unit vector (tau, rho): the one direction everything goes, up and left in the frame
SPEED = 0.15  # cm/s, the air supply's pattern
ENVELOPE_SHARE = 0.4  # the hot place itself moves at this share of that, or it reads as a spotlight sliding over the wood: the pattern runs through it, pieces lighting and dying
WAVE1 = (0.9, 5.2, 22.0)  # heat waves in the cracks: wavelength cm, period s, half amplitude K. Crest speed 0.17 cm/s
WAVE2 = (0.35, 3.4, 8.0)  # a shorter one on top, so a crack's bright beads slide along it
ASH_CREEP = 0.025  # score/s; the score's slope is about 2 per cm, so the edge moves about 0.012 cm/s
VEIL = 0.0  # powder dusting the glowing area (0.3 until the fifth version)
T_FRONT = 15.0  # K: the char just ahead of the crust's edge is burning
FLAME_TONGUES = ((0.43, 0.05, 0.72, 0.5), (0.5, 0.032, 1.0, 2.1), (0.56, 0.026, 0.55, 3.9))  # where along the ridge line, half width cm, relative height, phase
FLAME_GAIN = 1.9  # scene radiance at the heart of a tongue: far above the coals, so it is a light source. Estimate
FPS = 25.0


# --- Planck --------------------------------------------------------------------------------------------------------
def _cmf(lam):
    """CIE 1931 2 deg matching functions, multi-lobe fit of Wyman, Sloan and Shirley (JCGT 2013). lam in nm."""

    def g(x, mu, s1, s2):
        s = np.where(x < mu, s1, s2)
        return np.exp(-0.5 * ((x - mu) / s) ** 2)

    x = 1.056 * g(lam, 599.8, 37.9, 31.0) + 0.362 * g(lam, 442.0, 16.0, 26.7) - 0.065 * g(lam, 501.1, 20.4, 26.2)
    y = 0.821 * g(lam, 568.8, 46.9, 40.5) + 0.286 * g(lam, 530.9, 16.3, 31.1)
    z = 1.217 * g(lam, 437.0, 11.8, 36.0) + 0.681 * g(lam, 459.0, 26.0, 13.8)
    return x, y, z


def blackbody_table():
    """Linear Rec.709 radiance of a blackbody on a table of T, scaled so that the luminance at 1150 K is GAIN. Out-of-gamut blue is clipped at 0: such a red has no Rec.709 blue."""
    Ts = np.linspace(700.0, 1400.0, 701)
    lam = np.linspace(380.0, 780.0, 201)
    cx, cy, cz = _cmf(lam)
    c2 = 1.4388e7  # nm K
    M = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    B = lam[None] ** -5 / (np.exp(c2 / (lam[None] * Ts[:, None])) - 1.0)
    XYZ = np.stack([(B * cx).sum(1), (B * cy).sum(1), (B * cz).sum(1)], -1)
    rgb = np.maximum(XYZ @ M.T, 0.0)
    # A camera is not a Rec.709 observer: its green and blue filters pass some deep red, so a photographed ember is salmon, not pure red. ESTIMATE, by eye against ref charbon (median sRGB 65, 17, 14), a stand-in for a real sensor's response.
    rgb = rgb * np.array([1.0, 1.0, 1.0]) + rgb[:, :1] * np.array([0.0, 0.0, 0.016])
    ref = XYZ[np.argmin(np.abs(Ts - 1150.0)), 1]
    return Ts, (rgb / ref * GAIN).astype(np.float32)


def radiance(T):
    Ts, tab = blackbody_table()
    return np.stack([np.interp(T, Ts, tab[:, i]).astype(np.float32) for i in range(3)], -1)


# --- wood space -------------------------------------------------------------------------------------------------------
class Space:
    def __init__(self, D):
        self.D = D
        self.nx = int((TAU1 - TAU0) * D)
        self.ny = int((RHO1 - RHO0) * D)
        self.shape = (self.ny, self.nx)
        self.tau = TAU0 + (np.arange(self.nx, dtype=np.float32) + 0.5) / D
        self.rho = RHO1 - (np.arange(self.ny, dtype=np.float32) + 0.5) / D  # rows run towards the pith: the mesh's normals point up, see SHOTS.md
        self.Tau, self.Rho = np.meshgrid(self.tau, self.rho)

    def px(self, t, r):
        return (np.asarray(t) - TAU0) * self.D - 0.5, (RHO1 - np.asarray(r)) * self.D - 0.5

    def coarse(self, lo, hi, beta, seed):
        """A large field on the fixed grid, so that it is the same in every quality; lo, hi in cm."""
        ny, nx = int((RHO1 - RHO0) * G), int((TAU1 - TAU0) * G)
        f = fbm((ny, nx), G, lo, hi, beta, seed)
        return self.up(f)

    def up(self, f):
        return blur(cv2.resize(f, (self.nx, self.ny), interpolation=cv2.INTER_CUBIC), max(0.6, self.D / G * 0.8))


class Lookup:
    """Fixed 1-D and 2-D lookups in cm, evaluated at points along a crack. Fixed grid: identical in every quality."""

    def __init__(self):
        ny, nx = int((RHO1 - RHO0) * G), int((TAU1 - TAU0) * G)
        self.warp = fbm((ny, nx), G, 0.5, 3.0, 3.0, SEED + 1).astype(np.float32) * 0.07
        self.warp2 = fbm((ny, nx), G, 0.08, 0.5, 2.2, SEED + 2).astype(np.float32) * 0.012
        self.ny, self.nx = ny, nx
        rng = np.random.default_rng(SEED + 3)
        widths = np.clip(rng.lognormal(np.log(0.165), 0.36, 40), 0.06, 0.42)
        self.rings = RHO1 + 0.2 - np.cumsum(widths)  # ring boundaries, outward to inward, cm
        self.rings = self.rings[self.rings > RHO0 - 0.4]
        # broad rays: unequal spacing along tau, each a wandering line of its own
        t, self.rays = TAU0 - 0.2, []
        while t < TAU1 + 0.2:
            t += rng.lognormal(np.log(0.2), 0.5)
            self.rays.append((t, rng.uniform(0.012, 0.03), rng.uniform(RHO0 - 0.2, RHO0 + 1.2) if rng.random() < 0.25 else RHO0 - 0.2, rng.uniform(0, 100.0)))

    def warped(self, tau, rho):
        """Rho of a point as the ring pattern sees it."""
        ix = np.clip(((np.asarray(tau) - TAU0) * G).astype(int), 0, self.nx - 1)
        iy = np.clip(((RHO1 - np.asarray(rho)) * G).astype(int), 0, self.ny - 1)
        return rho + self.warp[iy, ix] + self.warp2[iy, ix]

    def ray_tau(self, i, rho):
        t, _, _, ph = self.rays[i]
        return t + 0.022 * np.sin(rho * 3.1 + ph) + 0.011 * np.sin(rho * 8.7 + ph * 1.7) + 0.005 * np.sin(rho * 21.0 + ph * 2.3)


def ring_phase(sp, lk):
    """f in [0, 1) across each ring, outward; 0 at the abrupt start of the earlywood. Also the distance to the nearest ring boundary."""
    warp = cv2.resize(lk.warp + lk.warp2, (sp.nx, sp.ny), interpolation=cv2.INTER_CUBIC)
    rw = sp.Rho + warp
    b = lk.rings[::-1]  # increasing
    k = np.clip(np.searchsorted(b, rw) - 1, 0, len(b) - 2)
    f = (rw - b[k]) / (b[k + 1] - b[k])
    return np.clip(f, 0, 1).astype(np.float32), k.astype(np.int32), rw.astype(np.float32)


def pores(sp, lk, f, k, seed):
    """Vessels as a mask, polygons one by one, none alike. Earlywood: big, packed in one or two rows. Latewood: small, in flame-shaped groups between the rays."""
    rng = np.random.default_rng(seed)
    out = np.zeros(sp.shape, np.uint8)
    b = lk.rings
    D = sp.D

    def poly(t, r, rx, ry):
        m = rng.integers(5, 9)
        a = np.sort(rng.uniform(0, 6.283, m))
        q = rng.uniform(0.72, 1.0, m)
        x, y = sp.px(t + rx * q * np.cos(a), r + ry * q * np.sin(a))
        cv2.fillPoly(out, [np.round(np.stack([x, y], 1) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)

    for i in range(len(b) - 1):
        hi, lo = b[i], b[i + 1]  # outer and inner boundary of this ring
        wid = hi - lo
        # earlywood at the inner side of the ring
        n = int((TAU1 - TAU0) * rng.uniform(80, 110))
        ts = rng.uniform(TAU0, TAU1, n)
        depth = np.abs(rng.normal(0, 0.035, n)) + 0.01
        rs = lo + depth * wid * 1.5 + 0.012
        rs = rs - (lk.warped(ts, rs) - rs)
        rad = rng.lognormal(np.log(0.0056), 0.28, n) * np.clip(1.15 - depth * 2.2, 0.4, 1.1)
        for t_, r_, a_ in zip(ts, rs, rad):
            poly(t_, r_, a_, a_ * rng.uniform(0.85, 1.25))
        # latewood: groups running along the ray direction, dying out towards the ring's outer edge
        ng = int((TAU1 - TAU0) * rng.uniform(9, 14))
        for t0 in rng.uniform(TAU0, TAU1, ng):
            r_ = lo + wid * rng.uniform(0.32, 0.45)
            sw = rng.uniform(0.015, 0.05)
            for j in range(rng.integers(5, 15)):
                r_ += rng.uniform(0.006, 0.016)
                if r_ > hi - wid * 0.05:
                    break
                t_ = t0 + rng.normal(0, sw * (1.0 - 0.5 * (r_ - lo) / wid))
                a_ = rng.lognormal(np.log(0.0035), 0.3)
                rr = r_ - (lk.warped(np.array([t_]), np.array([r_]))[0] - r_)
                if a_ * D >= 0.45:
                    poly(t_, rr, a_, a_)
    return blur(out.astype(np.float32) / 255.0, max(0.45, 0.0012 * D))


class Cracks:
    """Polylines in cm, each with width and depth along it; the class rasters them. Everything in cm, so the network is the same in every quality."""

    def __init__(self, sp):
        self.sp = sp
        self.occ = np.zeros((int((RHO1 - RHO0) * 200), int((TAU1 - TAU0) * 200)), np.uint8)  # occupancy at a fixed 200 px/cm: where a new crack must stop
        self.lines = []

    def hit(self, t, r):
        ix, iy = int((t - TAU0) * 200), int((RHO1 - r) * 200)
        if ix < 0 or iy < 0 or iy >= self.occ.shape[0] or ix >= self.occ.shape[1]:
            return True
        return bool(self.occ[iy, ix])

    def commit(self, pts, wid, dep):
        """pts (n, 2) in cm; wid, dep per point. Cracks in the same class are rastered together."""
        pts = np.asarray(pts, np.float32)
        q = np.stack([(pts[:, 0] - TAU0) * 200, (RHO1 - pts[:, 1]) * 200], 1)
        cv2.polylines(self.occ, [np.round(q * 16).astype(np.int32)], False, 1, max(1, int(np.max(wid) * 200)), cv2.LINE_8, shift=4)
        self.lines.append((pts, np.asarray(wid, np.float32), np.asarray(dep, np.float32)))

    def raster(self):
        """Depth, distance from the nearest crack in cm, and the half width of that crack. Lines are drawn into labels, then a distance transform: per pixel the distance and which segment."""
        sp = self.sp
        lab = np.zeros(sp.shape, np.int32)
        wid, dep = [0.0], [0.0]
        k = 1
        for pts, w, d in sorted(self.lines, key=lambda L: L[1].max()):  # widest last: it wins where they touch
            x, y = sp.px(pts[:, 0], pts[:, 1])
            P = np.round(np.stack([x, y], 1) * 16).astype(np.int32)
            for s in range(len(P) - 1):
                cv2.line(lab, tuple(int(c) for c in P[s]), tuple(int(c) for c in P[s + 1]), k, 1, cv2.LINE_8, shift=4)
                wid.append(float(0.5 * (w[s] + w[s + 1])))
                dep.append(float(0.5 * (d[s] + d[s + 1])))
                k += 1
        mask = (lab == 0).astype(np.uint8)
        dist, lb = cv2.distanceTransformWithLabels(mask, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        z = mask == 0
        pick = np.zeros(lb.max() + 2, np.int32)
        pick[lb[z]] = lab[z]
        which = pick[lb]
        return dist.astype(np.float32) / sp.D, np.array(wid, np.float32)[which], np.array(dep, np.float32)[which]


def build_cracks(sp, lk):
    """Order is the order of breaking: long radial checks, then ring shakes between them, then fine checks in the cells. A later crack stops where it meets an earlier one: T junctions."""
    rng = np.random.default_rng(SEED + 5)
    c = Cracks(sp)
    rays = lk.rays
    ray_at = np.array([r[0] for r in rays])

    def radial(i, r0, length, w0, d0, sign=-1.0, jog=0.06, stop=True, taper=1.0, lean=0.0, wander=0.0):
        """Along ray i from rho = r0, inward. Now and then it jumps sideways to the next ray along a ring: zig-zag."""
        step = 0.006
        n = int(length / step)
        rs, ts = [r0], [float(lk.ray_tau(i, np.array(r0)))]
        off, cur = 0.0, i
        ph = rng.uniform([3.0, 0.0, 9.0, 0.0], [7.0, 6.28, 16.0, 6.28])
        for s in range(1, n):
            r_ = rs[-1] + sign * step
            u_ = s / max(n, 1)
            off = lean * u_ + wander * (np.sin(u_ * ph[0] + ph[1]) + 0.5 * np.sin(u_ * ph[2] + ph[3]))  # a deep split does not keep to one ray
            t_ = float(lk.ray_tau(cur, np.array(r_))) + off
            if rng.random() < jog * step * 6:
                nxt = int(np.clip(cur + rng.choice([-1, 1]), 0, len(rays) - 1))
                t2 = float(lk.ray_tau(nxt, np.array(r_)))
                if abs(t2 - ts[-1]) < 0.3:
                    for u in np.linspace(0, 1, 8)[1:]:
                        ts.append(ts[-1] * (1 - u) + t2 * u)
                        rs.append(rs[-1] + sign * 0.0015)
                    cur = nxt
                    continue
            if stop and s > 6 and c.hit(t_, r_):
                break
            ts.append(t_)
            rs.append(r_)
        pts = np.stack([ts, rs], 1)
        u = np.linspace(0, 1, len(pts))
        pts[:, 0] += fine_jitter(rng, len(pts), 0.0022)
        w = w0 * (1 - u) ** taper + 0.0015
        d = d0 * (1 - u) ** (taper * 0.8) + 0.008
        c.commit(pts, w, d)
        return pts

    def along_ring(t0, r0, length, w0, d0, sign):
        """Along the ring through (t0, r0), until it meets a crack. Stays at constant warped rho."""
        step = 0.006
        target = float(lk.warped(np.array([t0]), np.array([r0]))[0])
        ts, rs = [t0], [r0]
        for s in range(int(length / step)):
            t_ = ts[-1] + sign * step
            r_ = rs[-1] + 0.25 * (target - float(lk.warped(np.array([t_]), np.array([rs[-1]]))[0])) + rng.normal(0, 0.0009)
            if s > 5 and c.hit(t_, r_):
                ts.append(t_)
                rs.append(r_)
                break
            ts.append(t_)
            rs.append(r_)
        if len(ts) < 6:
            return None
        pts = np.stack([ts, rs], 1)
        u = np.linspace(0, 1, len(pts))
        w = w0 * np.sin(np.pi * np.clip(0.12 + 0.88 * u, 0, 1)) ** 0.6 + 0.001
        d = d0 * (0.3 + 0.7 * np.sin(np.pi * u) ** 0.5)
        c.commit(pts, w, d)
        return pts

    # The two splits that make the picture: placed, not random. tau where they leave the rim, half width there and depth.
    def nearest(t):
        return int(np.argmin(np.abs(ray_at - t)))

    main = [(-0.72, 0.05, 0.6, 2.4, 0.5, 0.05), (0.52, 0.026, 0.3, 1.5, -0.35, 0.06)]
    majors = []
    for t, w, d, L, lean, wd in main:
        majors.append(radial(nearest(t), R + 0.25, L, w, d, stop=False, jog=0.0, taper=0.8, lean=lean, wander=wd))
    # other long checks from the rim, some shallow, some deep; gaps very unequal, each with its own slant and wander. Placed by hand so no two gaps match
    for t, L, w, lean in ((-2.1, 0.5, 0.01, 0.25), (-1.72, 1.1, 0.014, -0.3), (-1.45, 0.35, 0.007, 0.1), (-0.18, 0.75, 0.012, 0.32), (0.08, 0.3, 0.006, -0.1), (1.18, 0.95, 0.013, 0.42), (1.36, 0.4, 0.008, -0.2), (2.05, 0.8, 0.012, -0.28)):
        majors.append(radial(nearest(t), R + 0.2 - rng.uniform(0, 0.4), L, w, w * rng.uniform(5, 9), lean=lean, wander=0.05, jog=0.15))
    # interior radial checks, not reaching the rim
    for _ in range(20):
        t, r = rng.uniform(TAU0, TAU1), rng.uniform(RHO0, R - 0.3)
        w = rng.lognormal(np.log(0.0065), 0.45)
        majors.append(radial(nearest(t), r, rng.lognormal(np.log(0.5), 0.5), w, w * 8.0))
    # ring shakes: leave a radial check on a ring boundary, run until they meet another check
    bnds = lk.rings
    for pts in list(majors):
        for _ in range(max(2, int(len(pts) * 0.012 * rng.uniform(1.2, 3.0)))):
            j = rng.integers(0, len(pts))
            rw = float(lk.warped(pts[j:j + 1, 0], pts[j:j + 1, 1])[0])
            near = bnds[np.argmin(np.abs(bnds - rw))]
            if abs(near - rw) > 0.05:
                continue
            w = rng.lognormal(np.log(0.0085), 0.5)  # wide enough to cut the face into blocks
            along_ring(float(pts[j, 0]), float(pts[j, 1] - (rw - near)), rng.lognormal(np.log(0.55), 0.5), w, w * rng.uniform(5, 10), rng.choice([-1.0, 1.0]))
    # fine checks: the brick work. Short radial ones between rings, short tangential ones between rays; clustered, large areas have few
    density = fbm((256, 256), 256 / 6.0, 0.25, 2.0, 2.6, SEED + 7)

    def dens(t, r):
        ix, iy = int(np.clip((t - TAU0) / (TAU1 - TAU0) * 255, 0, 255)), int(np.clip((RHO1 - r) / (RHO1 - RHO0) * 255, 0, 255))
        return density[iy, ix]

    area = (TAU1 - TAU0) * (RHO1 - RHO0)
    for _ in range(int(area * 380)):
        t, r = rng.uniform(TAU0, TAU1), rng.uniform(RHO0, RHO1)
        if rng.random() > 0.2 + 0.5 * (dens(t, r) + 1.2):
            continue
        if c.hit(t, r):
            continue
        w = rng.lognormal(np.log(0.0021), 0.42)
        if rng.random() < 0.55:
            radial(nearest(t), r, rng.lognormal(np.log(0.14), 0.55), w, w * rng.uniform(6, 11), sign=rng.choice([-1.0, 1.0]), jog=0.1)
        else:
            rw = float(lk.warped(np.array([t]), np.array([r]))[0])
            near = bnds[np.argmin(np.abs(bnds - rw))]
            if abs(near - rw) < 0.04:
                r = r - (rw - near)
            along_ring(t, r, rng.lognormal(np.log(0.12), 0.55), w, w * rng.uniform(6, 11), rng.choice([-1.0, 1.0]))
    return c


def crust_lines(sp, seed, spacing, keep):
    """Distance in cm to the nearest crack of a mud-crack net in the crust: boundaries of jittered cells, bent, and only a share `keep` of them there, so that small cracks stop part way. Fixed grid: the same in every quality."""
    g = 500.0
    ny, nx = int((RHO1 - RHO0) * g), int((TAU1 - TAU0) * g)
    rng = np.random.default_rng(seed)
    n = int((TAU1 - TAU0) * (RHO1 - RHO0) / spacing**2)
    m = np.ones((ny, nx), np.uint8)
    m[rng.integers(0, ny, n), rng.integers(0, nx, n)] = 0
    _, lb = cv2.distanceTransformWithLabels(m, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_CCOMP)
    edge = (lb != np.roll(lb, 1, 0)) | (lb != np.roll(lb, 1, 1))
    edge[0], edge[:, 0] = False, False
    edge = cv2.dilate(edge.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0  # a 1 px line does not survive the bending below: it came out as a row of dots
    if keep < 1.0:
        k_ = cv2.resize(fbm((ny // 4, nx // 4), g / 4, 0.03, 0.3, 2.2, seed + 1), (nx, ny), interpolation=cv2.INTER_LINEAR)
        edge &= k_ < np.quantile(k_[::9, ::9], keep)
    dx = cv2.resize(fbm((ny // 4, nx // 4), g / 4, 0.02, spacing, 2.4, seed + 2), (nx, ny), interpolation=cv2.INTER_LINEAR) * spacing * 0.22 * g
    dy = cv2.resize(fbm((ny // 4, nx // 4), g / 4, 0.02, spacing, 2.4, seed + 3), (nx, ny), interpolation=cv2.INTER_LINEAR) * spacing * 0.22 * g
    Xg, Yg = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    bent = cv2.remap(edge.astype(np.uint8) * 255, Xg + dx, Yg + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    d = cv2.distanceTransform((bent < 128).astype(np.uint8), cv2.DIST_L2, 5) / g
    return cv2.resize(d, (sp.nx, sp.ny), interpolation=cv2.INTER_LINEAR)


def fine_jitter(rng, n, amp):
    """A wandering offset along a line, wavelength about 0.03-0.1 cm when the step is 0.006 cm."""
    x = rng.normal(0, 1, n + 40).astype(np.float32)[None]
    x = cv2.GaussianBlur(x, (0, 0), 3.0)[0][20:20 + n] * 2.8 + 0.45 * rng.normal(0, 1, n)
    return x * amp


def aniso(sp, seed, st, sr, size=1536, lo=1.5, hi=30.0, beta=1.6):
    """Noise stretched along rho (fibres and rays), by looking up a square noise; st, sr are its px per cm along tau and rho."""
    tb = fbm((size, size), 1.0, lo, hi, beta, seed)
    return cv2.remap(tb, np.mod((sp.Tau - TAU0) * st, size - 1).astype(np.float32), np.mod((sp.Rho - RHO0) * sr, size - 1).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def rim_line(sp):
    """The burnt outer edge of the round. Its large shape is fixed in cm."""
    rng = np.random.default_rng(SEED + 9)
    n = 1024
    t = np.linspace(TAU0, TAU1, n)
    e = np.zeros(n)
    for L, a in ((1.6, 0.07), (0.55, 0.035), (0.2, 0.014), (0.07, 0.007)):
        x = rng.normal(0, 1, n * 3).astype(np.float32)[None]
        s = L / (t[1] - t[0]) / 2.5
        y = cv2.GaussianBlur(x, (0, 0), s)[0][n:2 * n]
        e += a * y / (y.std() + 1e-6)
    return t, R + e


def prepare(D):
    """Everything that does not change while it burns."""
    sp = Space(D)
    lk = Lookup()
    f, k, rw = ring_phase(sp, lk)
    print("grid", sp.nx, sp.ny, f"{sp.nx * sp.ny / 1e6:.1f} M", flush=True)

    # rim: everything falls away beyond it, and it is the arc
    tr, er = rim_line(sp)
    rim = np.interp(sp.Tau, tr, er).astype(np.float32)
    drim = rim - sp.Rho  # > 0 inside
    d_out = np.maximum(-drim, 0.0)
    round_r = 0.34
    fall = np.where(d_out < round_r, round_r - np.sqrt(np.maximum(round_r**2 - d_out**2, 0.0)), round_r + (d_out - round_r) * 7.0)
    shoulder = 0.16 * sstep(0.42, 0.0, drim) ** 2  # the edge has burnt back and rounded
    h_big = -fall - shoulder

    # the crust and the char part along ring boundaries and rays: thin lines, here and there broken. These are what make it read as wood, and the arcs echo the rim
    b_ = lk.rings[::-1]
    ring_w = (b_[k + 1] - b_[k]).astype(np.float32)
    d_ring = np.minimum(f, 1.0 - f) * ring_w
    breaks = sstep(-0.9, -0.1, sp.coarse(0.08, 0.45, 2.2, SEED + 30))
    wobble = 1.0 + 0.4 * np.clip(fbm(sp.shape, D, max(2.0 / D, 0.004), 0.03, 1.6, SEED + 31), -1.5, 1.5)
    ring_line = np.exp(-d_ring / np.maximum(0.0052 * wobble, 0.9 / D)) * breaks

    # broad undulation of the sawn and burnt face
    h_big = h_big + 0.05 * sp.coarse(0.45, 2.5, 3.2, SEED + 11) + 0.006 * sp.coarse(0.1, 0.5, 2.4, SEED + 12)

    # rings: earlywood burnt back further than latewood, an abrupt step at the boundary
    early = sstep(0.34, 0.03, f)
    h_ring = -0.016 * early + 0.010 * sstep(0.45, 0.98, f) - 0.02 * ring_line

    # rays: broad ones as lines, recessed; fine ones as a stretched noise, only tau matters
    ray = np.zeros(sp.shape, np.float32)
    for i, (t, wd, r_from, _) in enumerate(lk.rays):
        rs = np.linspace(RHO1, r_from, 200)
        x, y = sp.px(lk.ray_tau(i, rs), rs)
        P = np.round(np.stack([x, y], 1) * 16).astype(np.int32)
        cv2.polylines(ray, [P], False, 1.0, max(1, int(round(wd * D))), cv2.LINE_AA, shift=4)
    ray = blur(ray, max(0.5, 0.003 * D))
    fine_ray = aniso(sp, SEED + 13, 72.0, 5.0, lo=1.5, hi=9.0, beta=1.2)
    h_ray = -0.012 * ray - 0.0024 * np.maximum(fine_ray, -0.6)

    # vessels: open pipes. The floor of a pore is dark or glowing, its walls drop sharply
    pore = pores(sp, lk, f, k, SEED + 14)
    h_pore = -0.035 * pore

    # fibres: a fine grain along the rays, and a fracture roughness
    grain = aniso(sp, SEED + 15, 340.0, 44.0, lo=1.2, hi=12.0, beta=1.3)
    rough_f = fbm(sp.shape, D, max(2.2 / D, 0.003), 0.07, 2.0, SEED + 16)
    h_fine = 0.0005 * grain + 0.0005 * rough_f  # silk: fibres, so the sheen runs along them

    # cracks
    cr = build_cracks(sp, lk)
    print("cracks", len(cr.lines), flush=True)
    dist, wid, dep = cr.raster()
    wob_fine = np.clip(0.5 * rough_f + 0.25 * grain, -1.2, 1.2)
    wob_wide = sp.coarse(0.04, 0.3, 2.2, SEED + 18)
    wide = sstep(0.015, 0.05, wid)  # a wide split has a wandering wall, not a sawn one
    wid_e = np.maximum(wid * (1.0 + (0.45 * wob_fine) * (1 - wide) + (0.22 * wob_wide + 0.06 * wob_fine) * wide), 0.85 / D)
    t_ = np.clip(dist / wid_e, 0.0, 1.0)
    prof = (1.0 - t_) ** 0.55  # steep walls, a narrow floor
    # a split's wall is broken in chips and ledges, in its own plane (along the ray and down into the wood). Looking the noise up in (rho, depth), not (tau, rho), stops it being stretched into a curtain of even vertical bars
    tb_w = fbm((1024, 1024), 1.0, 1.5, 40.0, 1.5, SEED + 37)
    wall = cv2.remap(tb_w, np.mod((sp.Rho - RHO0) * 230.0, 1023).astype(np.float32), np.mod(dep * prof * 230.0 + 300.0, 1023).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    wall_on = sstep(0.03, 0.1, dep) * sstep(0.02, 0.2, prof)
    h_crack = -dep * prof + 0.018 * wall * wall_on
    # the lips round off, and burn back, in proportion to the crack
    lip = -np.minimum(dep, 0.1) * 0.2 * np.exp(-np.maximum(dist - wid_e, 0.0) / np.maximum(1.8 * wid, 0.012))

    # cells between the cracks: each has its own height; they lifted and curled on their own
    mask = (t_ >= 0.72).astype(np.uint8)
    n_cells, cells = cv2.connectedComponents(mask, connectivity=4)
    rng = np.random.default_rng(SEED + 17)
    # a cell's value depends on its own number only by accident; so the look changes with quality a little at the smallest scale
    cv_off = rng.normal(0, 1, n_cells).astype(np.float32)
    cell_r = rng.random(n_cells).astype(np.float32)[cells]  # each broken face its own polish
    area = np.bincount(cells.ravel(), minlength=n_cells).astype(np.float32) / D**2
    amp = np.minimum(0.007, 0.03 * np.sqrt(area))
    h_cell = (cv_off * amp)[cells]
    h_cell[cells == 0] = 0.0
    h_cell = blur(h_cell, max(0.5, 0.002 * D))

    h_char = h_big + h_ring + h_ray + h_pore + h_crack + lip + h_cell

    # --- ash. It lies on what stands proud and on the edges, longest burnt; it breaks in plates along the crack network
    low = blur(h_big + h_cell + lip * 0.5, 0.03 * D)
    proud = low - blur(low, 0.22 * D)
    rim_near = sstep(0.55, 0.05, drim)
    # the deep cracks cut the blocks. Distance from them, and how near the block's lower edge is: rows run downward in the frame
    deep = (dist < wid_e) & (wid >= 0.006)
    dist_deep = cv2.distanceTransform((~deep).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / D
    rows = np.arange(sp.ny, dtype=np.float32)[:, None]
    nxt = np.minimum.accumulate(np.where(deep, rows, 1e6)[::-1], axis=0)[::-1]
    lower = blur(np.exp(-np.maximum(nxt - rows, 0.0) / D / 0.11).astype(np.float32), max(1.0, 0.012 * D))
    patch = sp.coarse(0.12, 1.6, 2.8, SEED + 19)
    patch2 = fbm(sp.shape, D, max(2.0 / D, 0.004), 0.1, 1.9, SEED + 20)
    score = 0.6 * patch + 0.7 * rim_near + proud * 26.0 + 0.5 * sstep(0.0, 0.16, dist_deep) + 0.1 * sstep(0.5, 0.95, f) - 0.2 * ray  # on ridges and on the tops of blocks
    level = float(np.percentile(score[::7, ::7], ASH_PERCENTILE))
    score = score + 0.1 * sp.coarse(0.025, 0.2, 1.9, SEED + 26)  # a clean edge: wanders at 0.03-0.2 cm, no fuzz
    # a hard crust breaks like dried mud: large plates all the way across, smaller cracks that stop part way. Thin and black: the char shows in them
    big = crust_lines(sp, SEED + 27, 0.34, 1.0)
    small = crust_lines(sp, SEED + 28, 0.13, 0.42)
    line_w = 0.0008 + 0.0012 * rank(sp.coarse(0.04, 0.3, 2.0, SEED + 29))  # beyond the 0.003 of the line itself
    crack_big = sstep(line_w, line_w * 0.45, big)
    crack_small = sstep(line_w * 0.62, line_w * 0.28, small)
    # the edge of a plate also stops at the wood's own cracks and rings, and bridges most pores
    ash_mask = (1.0 - 0.6 * crack_big) * (1.0 - 0.3 * crack_small) * sstep(0.0, 0.03, dist_deep) * sstep(0.1, 0.6, t_) * (1.0 - pore * sstep(0.6, 1.5, patch2)) * (1.0 - sstep(0.25, 0.6, ring_line)) * (1.0 - 0.8 * sstep(0.35, 0.8, ray * breaks))
    # no islands: a crust this size does not leave a lone white pebble. Judged once, on the crust as it will be at the end of any take, so nothing pops in
    grown = sstep(level - 0.012 - 1.5 * ASH_CREEP, level + 0.012 - 1.5 * ASH_CREEP, score) * ash_mask
    n_is, lab_is, st_is, _ = cv2.connectedComponentsWithStats((blur(grown, max(1.0, 0.01 * D)) > 0.5).astype(np.uint8), connectivity=8)
    big_is = st_is[:, cv2.CC_STAT_AREA] / D**2 > 0.05
    big_is[0] = False
    ash_mask = ash_mask * big_is[lab_is]
    # distance to the crust's edge, in cm, from the score's level and its slope: continuous in time, where a distance transform of a mask would step
    sm = blur(score, max(1.0, 0.012 * D))
    gy, gx = np.gradient(sm)
    slope = np.maximum(np.sqrt(gx**2 + gy**2) * D, 0.5)
    fade_noise = 0.006 * sp.coarse(0.015, 0.12, 1.8, SEED + 32)
    thick0 = 0.0015 + 0.0015 * rank(sp.coarse(0.05, 0.5, 2.2, SEED + 22))
    h_soft = blur(h_char, max(1.0, 0.014 * D))  # powder fills what it lies on: under it the wood is only a soft undulation, no hard shadows
    # powder breaks up at its edge in very fine grains; the same grains, sparse and thin, dust the glowing part so that the glow shows through
    dust = rank(fbm(sp.shape, D, max(1.6 / D, 0.003), 0.02, 1.2, SEED + 35))
    veil = VEIL * sstep(0.5, 0.92, rank(sp.coarse(0.03, 0.18, 2.0, SEED + 36))) * (0.5 + 0.5 * dust) * np.exp(-(((sp.Rho - (R - 0.6)) / 0.5) ** 2) - ((sp.Tau - 0.2) / 0.9) ** 2)

    # --- what the temperature takes from the wood
    depth = np.maximum(-h_crack, 0.0)
    cavity = 1.0 - np.exp(-((depth / 0.07) ** 1.5))  # only a deep split sees mostly itself; a fine crack stays near the surface's temperature
    near = np.exp(-np.maximum(dist - wid_e, 0.0) / 0.03) * sstep(0.004, 0.012, wid)  # the lips of the deep ones
    pore_T = 30.0 * pore
    wall_T = 12.0 * np.clip(wall, -1.5, 1.5) * cavity  # a wall is not one temperature
    rim_T = 30.0 * sstep(0.35, 0.0, drim)
    # the wood shows in the glow: earlywood is thin-walled and hotter, the step at the ring is abrupt; rays and fibres each their own. The radiance is steep in T, so a few tens of K are plenty
    wood_T = 8.0 * sstep(0.4, 0.04, f) + 5.0 * np.clip(grain, -1.5, 1.5) + 3.0 * np.clip(fine_ray, -1.5, 1.5) + 26.0 * sp.coarse(0.03, 0.2, 1.8, SEED + 38) + 14.0 * np.clip(rough_f, -1.5, 1.5)  # the rings hardly: a burning face is not striped

    albedo_char = 0.038 + 0.02 * rank(grain) + 0.015 * rank(rough_f)
    ash_tone = (0.9 + 0.1 * rank(sp.coarse(0.06, 0.6, 2.2, SEED + 24))) * (0.95 + 0.05 * sstep(0.2, 0.9, f))  # latewood's ash a little paler, so the rings show in it
    mottle = 0.9 + 0.1 * rank(fbm(sp.shape, D, max(2.0 / D, 0.006), 0.05, 1.6, SEED + 34))  # a fine, faint unevenness: a powder
    col_ash = color([0.46, 0.44, 0.41]) * (ash_tone * mottle)[..., None]  # warm grey, estimate
    col_char = np.stack([albedo_char * 1.04, albedo_char, albedo_char * 0.97], -1)

    # silky graphite on fresh fracture; rougher where burnt
    sheen = rank(sp.coarse(0.06, 0.5, 2.0, SEED + 25))
    rough_char = 0.2 + 0.2 * cell_r + 0.12 * sheen + 0.02 * grain

    # --- into the piece's plane
    th = (sp.Tau / R0).astype(np.float32)
    X = sp.Rho * np.sin(th)
    Y = sp.Rho * np.cos(th)
    return dict(sp=sp, D=D, X=X, Y=Y, h_char=h_char, h_fine=h_fine, pore=pore, score=score, level=level, h_soft=h_soft, dust=dust, veil=veil, lower=lower, pore_T=pore_T, ash_mask=ash_mask, slope=slope, fade_noise=fade_noise, thick0=thick0, cavity=cavity, near=near, wall_T=wall_T, rim_T=rim_T, wood_T=wood_T, col_ash=col_ash, col_char=col_char, rough_char=rough_char, drim=drim, depth=depth, air=Air(sp))


def at_time(S, t):
    """The burning piece at t seconds: heights in cm, everything a shader needs."""
    sp, D = S["sp"], S["D"]
    # the crust's edge goes forward: its level sinks, steadily, never back
    level = S["level"] - ASH_CREEP * t
    inside = (S["score"] - level) / S["slope"]  # cm inside the edge; negative ahead of it
    # the powder gets thinner over about 0.14 cm towards its edge, and the black shows through; the last of it is grains
    edge = np.clip((inside + S["fade_noise"]) / 0.1, 0.0, 1.0)
    ash_core = edge * S["ash_mask"]
    hot, w1, w2 = S["air"].at(t)
    grains = sstep(S["dust"] - 0.18, S["dust"] + 0.18, edge * 1.6)
    ash = np.clip(0.82 * ash_core**0.9 * (0.5 + 0.5 * grains) * (1.0 - 0.5 * np.clip(hot, 0.0, 1.0)), 0.0, 1.0)  # thin where it burns underneath
    cover = 1.0 - (1.0 - ash) * (1.0 - S["veil"])
    b = blur(sstep(0.25, 0.8, ash_core), max(0.6, 0.006 * D))
    h = S["h_char"] * (1.0 - b) + S["h_soft"] * b + blur(S["thick0"] * ash_core, max(0.6, 0.004 * D)) + S["h_fine"] * (1.0 - b)

    cav = S["cavity"]
    glow = np.clip(hot, 0.0, 1.0)
    T = T_COLD + T_AIR * glow**0.85 + 70.0 * S["lower"] * glow + S["pore_T"] * glow + glow * S["wood_T"]  # brightest along a block's lower edge
    T = T + cav * (T_CAVITY + T_CAVITY_HOT * glow) + T_EDGE * S["near"] * (0.1 + 0.9 * glow) + S["wall_T"]
    # waves of heat go through; not all at once, see Air
    T = T + (2.0 * WAVE1[2] * (w1 - 0.5) + 2.0 * WAVE2[2] * (w2 - 0.5)) * cav * (0.3 + 0.7 * glow)
    T = T - T_ASH * ash - S["rim_T"]
    # the char just ahead of the powder is what is burning
    T = T + T_FRONT * np.exp(-((inside / 0.018) ** 2)) * (1.0 - 0.8 * ash) * (0.1 + 0.9 * glow) * sstep(0.2, 0.7, S["ash_mask"])
    T = np.clip(T, 800.0, T_MAX).astype(np.float32)

    col = S["col_char"] * (1.0 - cover[..., None]) + S["col_ash"] * cover[..., None]
    emissivity = 1.0 - col.mean(-1)  # Kirchhoff
    emit = radiance(T) * emissivity[..., None]
    rough = S["rough_char"] * (1 - cover) + 1.0 * cover
    spec = 1.0 * (1 - cover) + 0.04 * cover  # graphite reflects more than a common dielectric; the top of this slider is F0 0.08. Powder hardly at all
    return {"sp": sp, "X": S["X"], "Y": S["Y"], "h": h, "col": col, "emit": emit, "rough": np.clip(rough, 0.1, 1), "spec": np.clip(spec, 0, 1), "T": T, "ash": ash, "depth": S["depth"], "drim": S["drim"]}


class Air:
    """The air supply, on the fixed grid. Its noise is carried along DRIFT at SPEED; the patch where it gets in is carried too; the crests of heat run the same way, a little faster, and their phase differs from place to place, so nothing brightens and darkens all at once. Nothing is periodic within a shot, and nothing is random from frame to frame."""

    def __init__(self, sp):
        self.sp = sp
        ny, nx = int((RHO1 - RHO0) * G), int((TAU1 - TAU0) * G)
        self.A = rank(fbm((ny, nx), G, 0.12, 1.2, 2.8, SEED + 40))
        self.C = rank(fbm((ny, nx), G, 0.3, 1.6, 3.0, SEED + 44))  # large soft shapes
        self.warp_t = fbm((ny, nx), G, 0.6, 3.0, 3.0, SEED + 45)
        self.warp_r = fbm((ny, nx), G, 0.6, 3.0, 3.0, SEED + 46)
        self.B = rank(fbm((ny, nx), G, 0.5, 2.5, 3.0, SEED + 41))
        self.phi = fbm((ny, nx), G, 0.5, 3.0, 3.0, SEED + 43)
        self.Xg, self.Yg = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
        self.Tg = TAU0 + (self.Xg + 0.5) / G
        self.Rg = RHO1 - (self.Yg + 0.5) / G

    def _carried(self, tb, dtau, drho):
        return cv2.remap(tb, self.Xg - dtau * G, self.Yg + drho * G, cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)

    def at(self, t):
        dt, dr = (float(v) for v in DRIFT * SPEED * t)
        n = self._carried(self.C, dt, dr)
        n2 = self._carried(self.A, dt, dr)
        along = self.Tg * float(DRIFT[0]) + self.Rg * float(DRIFT[1])

        def wave(p, off):
            return 0.5 + 0.5 * np.sin(2.0 * np.pi * (along / p[0] - t / p[1] + off))

        w1 = wave(WAVE1, 0.35 * self.phi)
        w2 = wave(WAVE2, 0.2 + 0.5 * self.phi)
        eg = ENVELOPE_SHARE
        Tw = self.Tg + 0.2 * self.warp_t  # no ellipses: the area has an irregular outline
        Rw = self.Rg + 0.15 * self.warp_r
        g = np.exp(-(((Rw - (R - 0.62 + eg * dr)) / 0.42) ** 2) - ((Tw - (0.2 + eg * dt)) / 0.75) ** 2)  # the one large area
        g2 = 0.6 * np.exp(-(((Rw - (R - 1.0 + eg * dr)) / 0.3) ** 2) - ((Tw - (-0.75 + eg * dt)) / 0.42) ** 2)  # a second, duller
        spots = 0.1 * sstep(0.88, 1.0, n2) * (0.5 + w1 * 0.8)  # here and there a small patch has caught, dull red at most
        hot = np.clip((g + g2) * (0.5 + 0.5 * sstep(0.12, 0.88, n)) * (0.92 + 0.16 * w1) + spots, 0.0, 1.0)
        up = self.sp.up
        return up(hot.astype(np.float32)), up(w1.astype(np.float32)), up(w2.astype(np.float32))


def to_world(X, Y, Z):
    c, s = np.cos(TILT), np.sin(TILT)
    return np.stack([X, Y * c - Z * s, Y * s + Z * c], -1).astype(np.float32)


def flame_sheet(cam, bases, height, t=0.0, nv=170):
    """One or two small tongues of flame on a ridge, on a card standing on these base points; additive light, so the char shows through, and out of focus it should read as a glow with a source in it. STAND-IN: analytic, chosen by eye, no solver.
    Their feet do not move, their tops sway slowly. Yellow-orange near the root, deep orange at the edge, fading out; a trace of blue at the root; a wide faint halo."""
    from vessel import cam_basis

    _, f, right, up = cam_basis(cam)
    nu = len(bases)
    length = float(np.sum(np.linalg.norm(np.diff(bases, axis=0), axis=1)))
    U = np.linspace(0.0, 1.0, nu, dtype=np.float32)[None]
    Zmax = height * 2.4
    Z = np.linspace(Zmax, -0.012, nv, dtype=np.float32)[:, None]  # rows run downward in the world
    E = np.zeros((nv, nu), np.float32)
    root = np.zeros((nv, nu), np.float32)
    for u0, wd, hh, ph in FLAME_TONGUES:
        H = height * hh * (1.0 + 0.14 * np.sin(2.0 * np.pi * t / 3.4 + ph))
        V = np.clip(Z / H, 0.0, 1.0)
        sway = 0.3 * wd * V**1.5 * np.sin(2.4 * V - 2.0 * np.pi * t / 2.8 + ph)  # cm; the foot stays where it is
        dx = (U - u0) * length - sway
        ax = wd * sstep(-0.15, 0.2, V) * (1.0 - V) ** 0.8 + 1e-4
        E += np.exp(-((dx / ax) ** 2)) * sstep(1.0, 0.12, V) * (Z >= -0.012)
        root += np.exp(-((dx / (wd * 1.1)) ** 2)) * np.exp(-((np.maximum(Z, 0.0) / (0.2 * H)) ** 2))
        E += 0.02 * np.exp(-((dx / (wd * 3.0)) ** 2) - (((Z - 0.3 * H) / (0.75 * H)) ** 2))  # a wide faint halo
    hotness = np.clip(E, 0.0, 1.0)[..., None] ** 1.6
    deep = np.array([1.0, 0.27, 0.035], np.float32)  # estimate
    yellow = np.array([1.0, 0.6, 0.17], np.float32)  # estimate
    colour = deep * (1.0 - hotness) + yellow * hotness
    fc = colour * (FLAME_GAIN * E)[..., None] + np.array([0.1, 0.3, 1.0], np.float32) * (0.1 * FLAME_GAIN * 0.05 * root)[..., None]
    P = bases.astype(np.float32)[None] - f.astype(np.float32)[None, None] * 0.12 + up.astype(np.float32)[None, None] * Z[..., None]
    return P.astype(np.float32), fc.astype(np.float32)


def lump(cam, fx, fy, off, radii, seed, n=640):
    """Another coal, far out of focus, for scale and depth: a rough solid from plane-wave ridges (no seam), dull cracks. Only its shape, its darkness and a few red lines survive the blur, so that is all it has.
    fx, fy: where its centre is in the frame; off: cm along the view from the plane of focus (+ away)."""
    from vessel import cam_basis

    rng = np.random.default_rng(seed)
    loc, f, right, up = cam_basis(cam)
    w = cam["focus_distance"] + off
    k = cam["lens_mm"] / 36.0
    C = loc + f * w + right * ((fx - 0.5) / k * w) + up * ((0.5 - fy) / (k * 16.0 / 9.0) * w)
    th = np.linspace(0, 2 * np.pi, n, dtype=np.float32)
    ph = np.linspace(0, np.pi, n // 2, dtype=np.float32)
    TH, PH = np.meshgrid(th, ph)
    d = np.stack([np.sin(PH) * np.cos(TH), np.sin(PH) * np.sin(TH), np.cos(PH)], -1)
    r = np.ones_like(TH)
    for a_, kk in ((0.16, 1.6), (0.1, 3.0), (0.05, 6.0), (0.025, 12.0)):
        for _ in range(4):
            v = rng.normal(0, 1, 3)
            v = v / np.linalg.norm(v) * kk
            r += a_ * (np.abs(np.sin(d @ v.astype(np.float32) + rng.uniform(0, 6.28))) - 0.6)
    line = np.ones_like(TH)
    for kk in (9.0, 15.0):
        v = rng.normal(0, 1, 3)
        v = v / np.linalg.norm(v) * kk
        line = np.minimum(line, np.abs(np.sin(d @ v.astype(np.float32) + rng.uniform(0, 6.28))))
    T = 800.0 + 170.0 * np.exp(-line / 0.05) * sstep(0.3, 0.75, np.cos(TH * 2.0 + seed) * 0.5 + 0.5)
    P = C.astype(np.float32) + d * r[..., None] * np.array(radii, np.float32)
    grey = 0.03 + 0.03 * sstep(0.45, 0.8, d[..., 2])
    col = np.stack([grey, grey * 0.98, grey * 0.95], -1).astype(np.float32)
    return P.astype(np.float32), col, (radiance(T) * 0.95).astype(np.float32), np.full(TH.shape, 0.6, np.float32), np.full(TH.shape, 0.35, np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "flat"
    take = q in ("take", "takefinal")
    dens = {"flat": 320.0, "preview": 320.0, "mid": 480.0, "final": 800.0, "take": 480.0, "takefinal": 800.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    S = prepare(dens)
    F = at_time(S, 0.0)
    print("grid", S["sp"].nx, S["sp"].ny, flush=True)
    if q == "flat":
        from darkroom import srgb_encode

        s = 2.0 ** -0.3
        e = F["emit"] * s
        gy, gx = np.gradient(blur(F["h"], 0.7))
        lam = np.clip(0.02 + 0.5 * (gx * 0.5 + gy * 0.8) * dens / 320.0 + F["col"].mean(-1) * 0.4, 0, 1)
        im = np.clip(1.0 - np.exp(-(e + lam[..., None] * 0.2)), 0, 1)
        im = srgb_encode(im)
        out = (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1]
        cv2.imwrite(os.path.join(d, "flat.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("T pct", np.percentile(F["T"][::5, ::5], [1, 25, 50, 75, 95, 99.5]), "ash", F["ash"].mean())
        print(out.shape, os.path.join(d, "flat.jpg"))
        return

    Pc = to_world(F["X"], F["Y"], F["h"])
    h_s = F["h"]
    vis = F["drim"] > -0.34
    view = np.array([np.sin(np.radians(AZ)) * np.cos(np.radians(EL)), -np.cos(np.radians(AZ)) * np.cos(np.radians(EL)), np.sin(np.radians(EL))])
    st = max(1, int(dens / 100))
    # focus: a point of the face, a third down from the arc. One band across
    Pv = Pc[::st, ::st][vis[::st, ::st]]
    cam, sag = fit_arc(Pv, view, W, DIST, apex=APEX, target0=Pv.mean(0))

    def at_frame(x, y):
        """The point of the face seen at this place in the frame (the nearest in the frame; the surface in front of it could hide it, so look)."""
        xs, ys, _ = project(cam, Pc[::st, ::st].reshape(-1, 3))
        k_ = np.argmin((xs - x) ** 2 + ((ys - y) * 9 / 16) ** 2)
        return Pc[::st, ::st].reshape(-1, 3)[k_]

    focus = at_frame(*FOCUS_AT)
    cam, sag = fit_arc(Pv, view, W, DIST, apex=APEX, target0=cam["target"], aperture_mm=APERTURE_MM, focus_point=focus)
    fp = os.path.join(d, f"face.{q}.npz")
    np.savez(fp, P=Pc, col=F["col"].astype(np.float32), emit=F["emit"].astype(np.float32), rough=F["rough"].astype(np.float32), spec=F["spec"].astype(np.float32))
    meshes = [{"name": "face", "npz": fp, "shader_py": os.path.join(HERE, "s67_shader.py"), "params": {"kind": "char"}}]

    for k_, (fx, fy, off, radii) in enumerate(LUMPS):
        Pl, cl, el, rl, sl = lump(cam, fx, fy, off, radii, SEED + 60 + k_)
        lf = os.path.join(d, f"lump{k_}.{q}.npz")
        np.savez(lf, P=Pl, col=cl, emit=el, rough=rl, spec=sl)
        meshes.append({"name": f"lump{k_}", "npz": lf, "shader_py": os.path.join(HERE, "s67_shader.py"), "params": {"kind": "char"}})
        xl, yl, _ = project(cam, Pl.reshape(-1, 3))
        print(f"lump {k_}: top y {yl.min():.3f}, x {xl.min():.2f}..{xl.max():.2f}")

    # the flame: a sheet standing on a ridge, base points looked up along a line in the frame and smoothed
    sheets = []
    for (a_, b_, H_) in FLAMES:
        ps = np.array([at_frame(a_[0] + (b_[0] - a_[0]) * u_, a_[1] + (b_[1] - a_[1]) * u_) for u_ in np.linspace(0, 1, 90)], np.float32)
        ps = cv2.GaussianBlur(ps[None], (0, 0), 4.0, borderType=cv2.BORDER_REPLICATE)[0]
        idx = np.linspace(0, len(ps) - 1, 360)
        sheets.append((np.stack([np.interp(idx, np.arange(len(ps)), ps[:, c_]) for c_ in range(3)], 1), H_))

    def flames(tag, t):
        out = []
        for k_, (bases, H_) in enumerate(sheets):
            Pf, fc = flame_sheet(cam, bases, H_, t)
            ffp = os.path.join(d, f"flame{k_}.{tag}.npz")
            np.savez(ffp, P=Pf, fc=fc)
            out.append({"name": f"flame{k_}", "npz": ffp, "shader_py": os.path.join(HERE, "s67_shader.py"), "params": {"kind": "card"}, "visible": {"shadow": False, "diffuse": False, "glossy": False}})
        return out

    if not take:
        meshes += flames(q, 0.0)
    xa, ya, wa = project(cam, Pc[::st, ::st].reshape(-1, 3))
    print("mesh in frame: x", xa.min(), xa.max(), "y", ya.min(), ya.max())

    # the room: a dim sheen on the char from a soft light high behind, in the mirror direction for a level face
    n = np.array([0.0, -np.sin(TILT), np.cos(TILT)])
    pm = focus
    v = np.array(cam["loc"]) - pm
    v /= np.linalg.norm(v)
    r = 2 * n.dot(v) * n - v
    lights = [
        {"type": "gradient", "name": "scrim", "loc": (pm + r * 40.0).tolist(), "target": pm.tolist(), "size": [60, 40], "sigma": [18, 10], "L": 1.5, "rgb": [0.9, 0.95, 1.06], "hide_in_diffuse": True},
        {"type": "gradient", "name": "room", "loc": (pm + np.array([-20.0, -12.0, 40.0])).tolist(), "target": pm.tolist(), "size": [70, 70], "sigma": [26, 26], "L": 2.0, "rgb": [0.92, 0.97, 1.08], "hide_in_gloss": True},
    ]
    gray = 0.0085
    develop = {"exposure": 0.0, "contrast": 1.38, "saturation": 1.0, "black": 0.0012, "grain": 1.0, "sharpen": 0.22, "halation": 0.09, "glare": 0.006, "vignette": 0.22}
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "sky": {"top": [gray, gray, gray * 1.03], "glow": [0.02, 0.0195, 0.0195], "h": 0.6, "mottle": 0.12, "x0": 0.55, "seed": 67},
        "bounces": 12,
        "diffuse_bounces": 4,
        "glossy_bounces": 3,
        "transmission_bounces": 2,
        "clamp_indirect": 40.0,
        "spp": {"preview": 96, "mid": 160, "final": 400},
    }
    if take:
        run_take(S, scene, develop, meshes, flames, q == "takefinal")
        return
    cand = len(sys.argv) > 2 and sys.argv[2] == "cand"
    shoot(NAME, scene, q, develop=develop, tag="cand" if cand else q)
    for k_ in (fp, *[m["npz"] for m in meshes]):
        if os.path.exists(k_) and k_.endswith(".npz"):
            os.remove(k_)


def run_take(S, scene, develop, meshes, flames, final):
    """All frames, as film.py wants them: float16 scene-linear take.linear_###.npy and develop.json, in <name>_move_final (never 8-bit frames: film.py reads a take's png as black). Also ends.jpg and take.mp4. One render per frame, same sampling seed throughout, so only what burns changes."""
    import kit
    from darkroom import develop as dev

    n = int(sys.argv[2]) if len(sys.argv) > 2 else 36
    only = int(sys.argv[3]) if len(sys.argv) > 3 else None
    out = os.path.join(OUT, f"{NAME}_move_final" if final else f"{NAME}_take_cand")
    work = os.path.join(out, "work")
    os.makedirs(work, exist_ok=True)
    if only is None:
        for f in os.listdir(out):
            if os.path.isfile(os.path.join(out, f)):
                os.remove(os.path.join(out, f))
    json.dump(develop, open(os.path.join(out, "develop.json"), "w"))
    mode = "takefinal" if final else "take"
    fp = os.path.join(OUT, NAME, f"face.{mode}.npz")
    lumps = [m for m in meshes if m["name"].startswith("lump")]
    first_last = {}
    for i in range(n) if only is None else [only]:
        tt = time.time()
        t = (i - (n - 1) / 2.0) / FPS
        F = at_time(S, t)
        np.savez(fp, P=to_world(F["X"], F["Y"], F["h"]), col=F["col"].astype(np.float32), emit=F["emit"].astype(np.float32), rough=F["rough"].astype(np.float32), spec=F["spec"].astype(np.float32))
        cfg = json.loads(json.dumps(scene))
        cfg["meshes"] = json.loads(json.dumps([m for m in meshes if m["name"] == "face"] + lumps + flames(mode, t)))
        cfg.update(res=[2560, 1440] if final else [1280, 720], spp=256 if final else 96, seed=1)
        cfg["camera"] = dict(cfg["camera"])
        kit._dress(cfg, NAME, work, develop)
        tag = f"f{i:03d}"
        linear = kit._render_local(cfg, work, tag)
        L = np.load(linear).astype(np.float32)
        np.save(os.path.join(out, f"take.linear_{i:03d}.npy"), L.astype(np.float16))
        os.remove(linear)
        im = dev(L, **{**develop, "seed": 700 + i})
        rgb8 = (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1]
        cv2.imwrite(os.path.join(work, f"{tag}.jpg"), rgb8, [cv2.IMWRITE_JPEG_QUALITY, 96])  # for the mp4 and for looking at, not for the film
        if i in (0, n - 1):
            first_last[i] = rgb8
        print(f"{tag} t {t:+.2f} s, ash {F['ash'].mean():.4f}, T p99.5 {np.percentile(F['T'][::5, ::5], 99.5):.0f}, {time.time() - tt:.0f} s", flush=True)
    if only is None:
        cv2.imwrite(os.path.join(out, "ends.jpg"), np.vstack([first_last[0], first_last[n - 1]]), [cv2.IMWRITE_JPEG_QUALITY, 92])
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(work, "f%03d.jpg"), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(out, "take.mp4")], check=True)
        jd = os.path.join(out, "jpg")
        os.makedirs(jd, exist_ok=True)
        for k in range(n):
            shutil.move(os.path.join(work, f"f{k:03d}.jpg"), os.path.join(jd, f"f{k:03d}.jpg"))
        shutil.rmtree(work)
    for m in [*lumps, {"npz": fp}, *flames(mode, 0.0)]:
        if os.path.exists(m["npz"]):
            os.remove(m["npz"])


if __name__ == "__main__":
    main()
