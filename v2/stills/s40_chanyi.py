"""Shot 40: a cicada's fore wing close to its base, where the veins are dense, against the leaves in the sun; the ridged leading edge is the arc.

    python3 -I v2/stills/s40_chanyi.py [sketch|preview|mid|cand|final]    cand is final size, written beside the final

Not passed yet: the latest mid (out/v2/s40_chanyi/mid.jpg) still reads as a soap film, with far more rainbow than ref/cicada. The final on disk is the older version.

The old shot was a flat sheet with evenly wide pen-like veins over round painted lights (git history has it). Set against ref/cicada:
- veins are solids, thick near the base and thin at the tip; they fork, are joined by crossveins at uneven heights and end on an ambient vein running inside the margin; a thick costal vein on one side. Veins are generated: the layout follows the pattern of the photographs, it is not the map of any one species;
- every cell of the membrane has its own slight bulge and tilt, so each catches the sky differently, and the highlight breaks at the veins;
- fine hair is short solid strands on the veins; on the membrane it is a share of scatter (`haze`), a stand-in; wear: hazy scuffs, a few scratches, nicks in the margin, specks of dust;
- a hind wing and the other fore wing lie behind it; the sun throws the veins' shadows on them; the background is a tree in true lens blur, under a sky.
Sizes are estimates (a fore wing about 4.4 cm). The body of the insect is out of frame and not built. The sky is painted (lotuslib.pond_env). Thin-film thickness is chosen, not measured.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from scipy.spatial import cKDTree

from kit import OUT, color, fbm, frame_camera, shoot, sstep
from lotuslib import pond_env
from s21_lib import smooth1d, up
from translib import SOFT, leaves, merge, real_background, save, tubes
from vessel import project, view_dir

NAME = "s40_chanyi"
WING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s40_shader.py")
W, AZ, EL, DIST = 1.85, -90.0, 2.0, 16.0
YAW = 13.0
APEX = 0.27
APERTURE = 7.0
SUN = np.array([-0.35, -0.55, 0.76])
SUN = SUN / np.linalg.norm(SUN)


# The veins of one wing near its base, in the wing's plane, cm: x to the right, y up, the apex of the leading edge at the origin. Laid by hand from the pattern of the photographs (ref/cicada 06, 07), not the map of a species.
# name: control points, half-width at the start, half-width at the end. The hand-placed points are only the plan: each gets its own wander and its own thickening below.
NET = [
    ("sub", [(-1.5, -0.2), (-1.0, -0.092), (-0.55, -0.042), (-0.33, -0.022)], 0.019, 0.015),  # runs close under the leading edge, then joins it at the node
    ("r1", [(-1.5, -0.37), (-0.9, -0.262), (-0.42, -0.205), (0.04, -0.16), (0.55, -0.175), (1.4, -0.36)], 0.024, 0.0075),
    ("r2", [(0.04, -0.16), (0.36, -0.285), (0.8, -0.365), (1.4, -0.51)], 0.012, 0.0065),
    ("m1", [(-1.5, -0.66), (-0.85, -0.52), (-0.37, -0.392), (0.0, -0.355), (0.4, -0.44), (0.86, -0.53), (1.4, -0.67)], 0.026, 0.007),
    ("m2", [(0.0, -0.355), (0.28, -0.58), (0.74, -0.73), (1.4, -0.85)], 0.012, 0.0065),
    ("cu1", [(-1.5, -1.0), (-0.85, -0.85), (-0.33, -0.665), (0.12, -0.61), (0.28, -0.58)], 0.022, 0.0085),
    ("cu2", [(-0.33, -0.665), (0.08, -0.875), (0.6, -0.99), (1.4, -1.14)], 0.012, 0.0065),
    ("a1", [(-1.5, -1.32), (-0.7, -1.12), (-0.1, -1.09), (0.6, -1.24)], 0.02, 0.008),
    # crossveins, never quite square to anything
    ("x1", [(-0.37, -0.392), (-0.345, -0.3), (-0.42, -0.205)], 0.0125, 0.0105),
    ("x2", [(-0.33, -0.665), (-0.385, -0.52), (-0.37, -0.392)], 0.0125, 0.011),
    ("x3", [(0.40, -0.44), (0.415, -0.36), (0.36, -0.285)], 0.0085, 0.007),
    ("x4", [(0.62, -0.335), (0.585, -0.26), (0.62, -0.178)], 0.006, 0.0065),
    ("x5", [(0.74, -0.73), (0.815, -0.62), (0.86, -0.53)], 0.0078, 0.0068),
    ("x6", [(0.08, -0.875), (0.145, -0.74), (0.12, -0.61)], 0.0095, 0.008),
    ("x7", [(0.52, -0.965), (0.60, -0.85), (0.56, -0.67)], 0.0062, 0.007),
    ("x8", [(-0.1, -1.09), (-0.03, -0.98), (0.08, -0.875)], 0.009, 0.0085),
]


def catmull(p, n=60):
    p = np.array(p, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    out = []
    for i in range(len(p) - 3):
        a, b, c, d = p[i], p[i + 1], p[i + 2], p[i + 3]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t**2 + (3 * b - a - 3 * c + d) * t**3))
    return np.vstack(out + [p[-2][None]])


def leading(x, seed=0, Rc=1.95, x0=0.03):
    """The leading edge: a long convex arc, not a circle: it flattens a little past the node. y of the wing's outer edge at x."""
    return -((x - x0) ** 2) / (2 * Rc) + 0.012 * np.sin(1.3 * x + seed) + 0.03 * sstep(-0.1, -1.3, x) * (x + 0.1)


class Sheet:
    """One wing as one heightfield: membrane and veins together, every field per vertex."""

    def __init__(self, seed, dens, frame, x_span=(-1.32, 1.32), y_bot=-1.2, smoke=1.0):
        self.seed, self.frame = seed, frame
        rng = self.rng = np.random.default_rng(seed)
        S = 1250.0 * dens
        self.S = S
        nx, ny = int((x_span[1] - x_span[0]) * S), int((-y_bot + 0.05) * S)
        x = np.linspace(x_span[0], x_span[1], nx, dtype=np.float32)
        v = np.linspace(1.0, 0.0, ny, dtype=np.float32)  # top row first: the mesh's normal (row x column) then faces the camera
        X, V = np.meshgrid(x, v)
        top = leading(X, seed)
        Y = y_bot + (top - y_bot) * V
        self.X, self.Y = X, Y
        self.build_veins()
        self.build_fields(top, smoke)

    def build_veins(self):
        rng = self.rng
        P, W, K = [], [], []
        ends = []
        lines = []
        for name, pts, w0, w1 in NET:
            c = catmull(pts, 80)
            L = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
            n = int(L[-1] / 0.0015) + 2
            t = np.linspace(0, L[-1], n)
            c = np.stack([np.interp(t, L, c[:, i]) for i in (0, 1)], -1)
            # veins are grown, not drawn: they wander, slowly and then quickly, and less at the junctions
            fade = np.clip(t / 0.06, 0, 1) * np.clip((L[-1] - t) / 0.06, 0, 1)
            nrm = np.gradient(c, axis=0)
            nrm = np.stack([-nrm[:, 1], nrm[:, 0]], -1) / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
            amp = rng.uniform(0.004, 0.009)
            c = c + nrm * ((amp * smooth1d(n, 0.11 / 0.0015, rng) + 0.0006 * smooth1d(n, 0.03 / 0.0015, rng)) * fade)[:, None]
            f = t / L[-1]
            # thick from the base to the tip; along that, its own swellings and pinches on two scales; a vein may slim down quite suddenly past a junction
            w = (w0 + (w1 - w0) * f**0.8) * np.exp(0.15 * smooth1d(n, 0.09 / 0.0015, rng) + 0.035 * smooth1d(n, 0.03 / 0.0015, rng))
            P.append(c)
            W.append(w)
            K.append(np.full(n, len(lines)))
            ends += [c[0], c[-1]]
            lines.append((name, c, w))
        P, W = np.vstack(P), np.concatenate(W)
        # every junction flares, as a fork in a living tube does
        de, _ = cKDTree(np.array(ends)).query(P, k=1)
        W = W * (1.0 + 0.55 * np.exp(-((de / 0.032) ** 2)))
        self.vP, self.vW, self.lines = P, W, lines
        self.vK = np.concatenate(K)
        self.vS = np.concatenate([np.arange(len(c)) * 0.0015 for _, c, _ in lines])

    def build_fields(self, top, smoke):
        rng = self.rng
        X, Y = self.X, self.Y
        S = self.S
        sh = X.shape
        pts = np.stack([X.ravel(), Y.ravel()], 1).astype(np.float64)
        d, idx = cKDTree(self.vP).query(pts, k=5, workers=-1)
        e_ = d - self.vW[idx]
        o = np.argmin(e_, axis=1)
        r = np.arange(len(o))
        best = idx[r, o]
        e = e_[r, o].astype(np.float32).reshape(sh)  # below 0 inside a vein
        w = self.vW[best].astype(np.float32).reshape(sh)
        along = self.vS[best].astype(np.float32).reshape(sh)
        # the leading edge is a vein too: thick and with a strip of its own
        de = (top - Y).astype(np.float32)
        lw = 0.033 + 0.015 * sstep(0.6, -1.0, X)
        lw = lw * np.exp(0.06 * up(fbm((32, 256), 40.0, 0.05, 0.8, 2.0, self.seed + 1), *sh))
        e_lead = de - 2 * lw
        lead = e_lead < e
        e = np.where(lead, e_lead, e)
        w = np.where(lead, lw, w)
        along = np.where(lead, X.astype(np.float32) + 1.5, along)
        dv = np.maximum(e, 0.0)
        t = np.clip(-e / np.maximum(w, 1e-4), 0, 1)
        op = sstep(-0.0016, 0.0009, -e)

        # the fields behind everything
        low = up(fbm((64, 128), 40.0, 0.25, 1.6, 2.6, self.seed + 3), *sh)
        mid = up(fbm((256, 512), 180.0, 0.05, 0.3, 2.4, self.seed + 4), *sh)
        P3 = np.stack([X * 37.0, Y * 37.0], -1)
        fine = fbm(sh, S, 0.004, 0.013, 1.0, self.seed + 5)
        fine2 = fbm(sh, S, 0.012, 0.05, 1.5, self.seed + 6)

        # cells: each bulges and tilts on its own, and so catches the sky on its own
        n, lab = cv2.connectedComponents((e > 0.0005).astype(np.uint8), connectivity=4)
        ca = rng.normal(0, 1, (n, 3)).astype(np.float32)
        area = np.bincount(lab.ravel(), minlength=n).astype(np.float64) + 1
        mx = (np.bincount(lab.ravel(), X.ravel(), n) / area).astype(np.float32)
        my = (np.bincount(lab.ravel(), Y.ravel(), n) / area).astype(np.float32)
        pill = sstep(0.0, 0.1, dv)
        z = pill * (0.006 * (0.7 + 0.3 * ca[:, 0])[lab] + 0.012 * ca[:, 1][lab] * (X - mx[lab]) + 0.012 * ca[:, 2][lab] * (Y - my[lab]))
        # across the veins' long cells the membrane is ribbed, like a ladder, near the base and close to the veins (ref/cicada 05, 06). Period about .016 cm, not constant
        rib_ph = along / 0.0165 + 0.7 * low + 0.25 * mid
        rib_mask = sstep(0.42, -0.65, X + 0.25 * mid) * np.exp(-dv / 0.13) * sstep(0.003, 0.02, dv) * np.clip(0.75 + 0.5 * low, 0, 1)
        ribs = np.cos(2 * np.pi * rib_ph) * rib_mask
        z = z + 0.00028 * ribs
        # long soft wrinkles of the membrane, and a crease
        z = z + 0.0016 * pill * mid
        # frost: the microtrichia lie thick in patches, along the upper strip and against the veins. That is what breaks the sun into glitter
        strip = sstep(0.34, 0.1, de) * sstep(-0.1, -0.6, X)
        fr = np.clip(1.05 * strip + 0.55 * np.exp(-dv / 0.07) * sstep(0.2, 1.1, mid + 0.6 * low) + 0.22 * sstep(0.7, 1.7, low), 0, 1)
        fr = fr * sstep(0.1, 0.9, 0.5 + 0.9 * fine2)
        z = z + 0.0013 * fr * fine
        # veins stand up from the sheet, and the sheet dips against them
        z = z - 0.0022 * np.exp(-dv / 0.02)
        hv = 0.62 * w * np.sqrt(np.maximum(1 - (1 - t) ** 2, 0.0))
        z = z + hv * (e < 0)
        z = z + (e < 0) * (0.0005 * mid + 0.00018 * fine2)  # a vein's wall is almost smooth; lumps here read as pebbled leather
        z = z + lead * (e < 0) * 0.0032 * np.cos(2 * np.pi * de / 0.028 + 1.2 * low)  # the leading edge is ridged along its length
        self.z = cv2.GaussianBlur(z.astype(np.float32), (0, 0), 0.9)

        # the smoke: brown in the wall of a cell and clearing to its middle; deeper towards the base; soft tonal bands along the veins
        band = 0.5 + 0.5 * np.cos(2 * np.pi * dv / (0.075 + 0.016 * low)) * np.exp(-dv / 0.26)
        base = sstep(0.75, -1.1, X + 0.2 * low)
        depth = smoke * (0.2 + 0.3 * low * 0.5 + (0.95 + 1.3 * base) * np.exp(-dv / 0.038) + (0.42 + 0.85 * base) * np.exp(-dv / 0.14) + (0.15 + 0.32 * base) * band + 0.22 * base)
        depth = np.maximum(depth + 0.3 * ribs, 0.02)
        tr = np.array([0.93, 0.845, 0.70], np.float32) ** (1.25 * depth[..., None])
        # scuffs and scratches
        sc = np.zeros(sh, np.uint8)
        x0, y0 = float(X.min()), float(Y.min())
        for _ in range(int(16)):
            p0 = np.array([rng.uniform(-1.1, 1.1), rng.uniform(-1.0, -0.1)])
            a = rng.normal(-0.2, 0.9)
            ln = rng.lognormal(np.log(0.14), 0.6)
            q = np.array([p0 + s_ * ln * np.array([np.cos(a + 0.5 * s_), np.sin(a + 0.5 * s_)]) for s_ in np.linspace(0, 1, 12)])
            qq = np.stack([(q[:, 0] - x0) * S, (1 - (q[:, 1] + 1.2) / 1.25) * sh[0]], -1)
            cv2.polylines(sc, [(qq * 8).astype(np.int32)], False, int(rng.uniform(70, 255)), 1, cv2.LINE_AA, shift=3)
        scr = cv2.GaussianBlur(sc.astype(np.float32) / 255.0, (0, 0), 0.7)
        haze = np.clip(0.004 + 0.05 * fr + 0.011 * sstep(0.8, 2.0, low + 0.5 * mid) + 0.1 * scr, 0, 0.5)
        # fine setal sockets: a row of tiny dark points along the strip
        sock = sstep(2.3, 3.1, fine2 + 0.6 * fine) * (0.35 + 0.65 * strip)
        tr = tr * (1.0 - 0.75 * sock)[..., None]
        # the vein: near black. A thick one is a hollow tube: its walls are what you see, the core lets a little amber through, so it reads as a pair of lines
        core = sstep(0.42, 0.95, t) * sstep(0.0085, 0.02, w)
        col = (np.array([0.0045, 0.0034, 0.0028], np.float32) + core[..., None] * np.array([0.05, 0.022, 0.007], np.float32)) * np.exp(0.14 * fine2 + 0.1 * mid)[..., None]
        # a thin line of light yellow where a vein crosses the nodal line, the flexible hinge of the wing; it interrupts the vein
        nod = np.exp(-(((X + 0.335 + 0.2 * (Y + 0.35) + 0.015 * mid) / 0.009) ** 2)) * sstep(0.02, 0.12, de)
        col = col + nod[..., None] * (np.array([0.34, 0.24, 0.1], np.float32) - col)
        op_ = op * (1.0 - 0.3 * core) * (1.0 - 0.45 * nod)
        tr = tr * (1.0 - op)[..., None] + (op * 1.0)[..., None] * (np.array([0.34, 0.14, 0.04], np.float32) * (0.25 + 0.75 * core[..., None]) + 0.25 * nod[..., None] * np.array([1.0, 0.8, 0.4], np.float32))
        tr = tr * (1 + 0.012 * mid[..., None])
        self.tr, self.haze_ = np.clip(tr, 0, 1).astype(np.float32), haze.astype(np.float32)
        self.op, self.col = np.clip(op_, 0, 1).astype(np.float32), np.clip(col, 0, 1).astype(np.float32)
        self.rough = np.clip(0.17 + 0.08 * sstep(0.0, 1.5, low) - 0.08 * fr, 0.06, 0.6).astype(np.float32)
        self.film = (300 + 34 * low).astype(np.float32)

    def save(self, path):
        P = self.frame(self.X, self.Y, self.z)
        np.savez(path, P=P.astype(np.float32), tr=self.tr, haze=self.haze_, film=self.film, op=self.op, col=self.col, rough=self.rough)
        return path, P

    def hairs(self, n, seed):
        """Short bristles along the leading edge and the thick veins; the ones at the edge stand against the light."""
        rng = np.random.default_rng(seed)
        ns = 7
        L, R, C = [], [], []
        pool = []
        xs = rng.uniform(-1.3, 1.3, int(n * 0.5))
        for x in xs:
            y = float(leading(np.float32(x), self.seed))
            pool.append((x, y, 1, 1.4))
        keep = self.vW > 0.009
        pts = self.vP[keep]
        ws = self.vW[keep]
        sel = rng.integers(0, len(pts), n - len(pool))
        for i in sel:
            pool.append((pts[i, 0], pts[i, 1], 0, 1.0))
        for x0, y0, edge, k in pool:
            a = (rng.normal(np.pi * 0.42, 0.42) if edge else rng.uniform(0, 2 * np.pi))
            ln = float(rng.lognormal(np.log(0.022 if edge else 0.012), 0.42))
            t = np.linspace(0, 1, ns, dtype=np.float32)
            curl = rng.normal(0, 0.7)
            x = x0 + ln * t * np.cos(a + curl * t)
            y = y0 + ln * t * np.sin(a + curl * t)
            z = 0.012 * (1 if not edge else 0.5) + ln * rng.uniform(0.15, 0.55) * t * (1 if rng.random() < 0.6 else -1) + 0.0 * t
            L.append(self.frame(x, y, z))
            R.append(float(rng.uniform(0.0005, 0.0011)) * (1 - 0.82 * t))
            C.append(np.array([0.13, 0.085, 0.04], np.float32) * rng.uniform(0.5, 1.7))
        L, R, C = np.array(L, np.float32), np.array(R, np.float32), np.array(C, np.float32)
        return tubes(L, R, {"col": 0.4 * C, "tr": C}, nside=4)

    def dust(self, n, seed):
        rng = np.random.default_rng(seed)
        ns = 6
        L, R, C = [], [], []
        for _ in range(n):
            x0, y0 = rng.uniform(-0.9, 0.9), rng.uniform(-0.75, 0.05)
            a = rng.uniform(0, 6.28)
            ln = float(rng.lognormal(np.log(0.006), 0.6))
            t = np.linspace(0, 1, ns, dtype=np.float32)
            L.append(self.frame(x0 + np.cos(a) * ln * t, y0 + np.sin(a) * ln * t, np.full(ns, -0.002, np.float32) + 0.012))
            R.append(ln * rng.uniform(0.2, 0.55) * np.sin(np.pi * np.linspace(0.08, 0.92, ns)))
            C.append(np.array([0.34, 0.27, 0.18], np.float32) * rng.uniform(0.35, 1.4))
        L, R, C = np.array(L, np.float32), np.array(R, np.float32), np.array(C, np.float32)
        return tubes(L, R, {"col": C, "tr": 0.5 * C}, nside=8)


def placer(O, tilt_deg, yaw_deg, roll_deg=0.0):
    """The wing's plane in the world: x to the right, y up, the normal towards the camera. Tipped back by tilt so that it mirrors the sky; yawed so that one side falls out of focus."""
    t, ya, ro = np.radians(tilt_deg), np.radians(yaw_deg), np.radians(roll_deg)
    ex = np.array([np.cos(ya), np.sin(ya), 0.0])
    nrm = np.array([np.sin(ya) * np.cos(t), -np.cos(ya) * np.cos(t), np.sin(t)])
    ey = np.cross(nrm, ex)
    ex, ey = ex * np.cos(ro) + ey * np.sin(ro), -ex * np.sin(ro) + ey * np.cos(ro)
    if np.dot(np.cross(ex, ey), nrm) < 0:
        ey = -ey

    def f(X, Y, Z):
        return np.array(O, np.float32) + np.asarray(X)[..., None] * ex.astype(np.float32) + np.asarray(Y)[..., None] * ey.astype(np.float32) + np.asarray(Z)[..., None] * nrm.astype(np.float32)

    return f


def tree(d, dens):
    """The tree: leaves from the near branches to the far crown, lit by the same sun; a branch close behind. Only what the blur needs."""
    rng = np.random.default_rng(4040)
    fol = []
    for i in range(int(110 + 110 * dens)):
        y = float(np.exp(rng.uniform(np.log(36), np.log(1100))))
        half = 0.7 * W * (DIST + y) / DIST
        x = float(rng.uniform(-half, half))
        z = float(rng.uniform(-half * 0.65, half * 0.65))
        rc = 0.05 * y + rng.uniform(3, 10)
        n_lf = 20
        at = np.array([x, y, z]) + rng.normal(0, rc, (n_lf, 3))
        A = rng.normal(0, 1, (n_lf, 3)) + np.array([0, 0, -0.3])
        N = rng.normal(0, 1, (n_lf, 3)) + np.array([0, -0.25, 0.6])
        tone = rng.uniform(0.7, 1.25, (n_lf, 1)) * rng.uniform(0.65, 1.2)
        sz = 1.0 + y / 120
        fol.append(leaves(rng, at, A, N, rng.uniform(7, 11, n_lf) * sz, rng.uniform(3.4, 5, n_lf) * sz, np.array([[0.04, 0.09, 0.028]]) * tone, np.array([[0.33, 0.55, 0.09]]) * tone, ns=4, droop=0.12))
    p1 = save(os.path.join(d, "tree.npz"), merge(*fol))
    # a branch behind, in the blur
    ns = 40
    t = np.linspace(0, 1, ns)
    path = np.stack([-12 + 26 * t, 11 + 1.4 * np.sin(2.2 * t), -5.8 + 3.2 * t + 0.25 * np.sin(5 * t)], -1)
    c = color([0.11, 0.08, 0.05])[None, None] * np.ones((1, ns, 1), np.float32)
    p2 = save(os.path.join(d, "branch.npz"), tubes(path[None].astype(np.float32), (0.22 + 0.08 * (1 - t))[None].astype(np.float32), {"col": c, "tr": np.zeros_like(c)}, nside=12))
    return p1, p2


def main():
    real_background()
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    tag = q
    if q == "cand":  # final size, beside the final: the film reads final.*, and this has to pass a side-by-side first
        q = "final"
    dens = {"sketch": 0.25, "preview": 0.4, "mid": 0.65, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    fr0 = placer((0.0, 0.0, 0.0), 14.0, YAW)
    hero = Sheet(4001, dens, fr0)
    # the hind wing behind it, out of focus, seen through the fore wing's membrane
    fr1 = placer((0.22, 0.24, -0.46), 17.0, YAW + 7.0, 9.0)
    back = Sheet(4002, dens * 0.42, fr1, smoke=0.8)
    meshes = []
    pa, Pm = hero.save(os.path.join(d, f"mem_hero.{q}.npz"))
    pb_, _ = back.save(os.path.join(d, f"mem_hind.{q}.npz"))
    WP = {"spec": 0.075, "vein_rough": 0.34, "vein_spec": 0.11}
    meshes.append({"name": "mem_hero", "npz": pa, "shader_py": WING, "params": WP})
    meshes.append({"name": "mem_hind", "npz": pb_, "shader_py": WING, "params": WP})
    soup = merge(hero.hairs(int(2600 * dens) + 400, 4101), hero.dust(12, 4102))
    meshes.append({"name": "bristles", "npz": save(os.path.join(d, "bristles.npz"), soup), "shader_py": SOFT, "params": {"k": 0.25, "rough": 0.42, "spec": 0.35, "smooth": True}})

    view = view_dir(AZ, EL)
    H_f = W * 9 / 16
    tgt = np.array([0.0, 0.0, 0.0])
    edge = Pm[0, ::10]
    mid_ = edge[np.abs(hero.X[0, ::10]) < 0.8]
    for _ in range(6):
        cam = frame_camera(tgt, view, W, DIST)
        x, y, _ = project(cam, mid_)
        tgt[2] -= (float(y.min()) - APEX) * H_f
        tgt[0] += (float(x[np.argmin(y)]) - 0.5) * W * 0.5
    focus = fr0(np.float32(-0.08), np.float32(-0.2), np.float32(0.0))
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, mid_)
    print(f"apex y {y.min():.3f} at x {x[np.argmin(y)]:.2f}; focus {project(cam, focus[None])[:2]}", flush=True)

    pt, pb = tree(d, dens)
    meshes.append({"name": "tree", "npz": pt, "shader_py": SOFT, "params": {"k": 0.45, "rough": 0.3, "spec": 0.5, "smooth": True}})
    meshes.append({"name": "branch", "npz": pb, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.5, "spec": 0.35, "smooth": True}})

    lights = [{"name": "sun", "loc": (tgt + SUN * 600.0).tolist(), "target": tgt.tolist(), "size": [8, 8], "watts": 2600000, "rgb": [1.0, 0.95, 0.86]}]  # visible in gloss: this is what the microtrichia break into glitter
    env = pond_env(os.path.join(d, "env.npy"), SUN, top=(0.5, 0.68, 0.95), low=(0.85, 0.9, 0.92), tree=(0.05, 0.1, 0.04), tree_el=12.0, pond=(0.05, 0.08, 0.04), cloud=0.7, gain=1.5, seed=40, soft=4.0)
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": env, "diffuse": True, "transmission": True},
        "bounces": 16,
        "diffuse_bounces": 6,
        "glossy_bounces": 4,
        "transmission_bounces": 12,
        "spp": {"sketch": 64, "preview": 128, "mid": 192, "final": 512},
    }
    if q == "sketch":
        scene["spp"] = 64
    look = {"exposure": 1.6, "contrast": 1.18, "saturation": 1.0, "black": 0.001, "grain": 0.9, "sharpen": 0.2, "halation": 0.05, "glare": 0.004, "vignette": 0.3}
    shoot(NAME, scene, "preview" if q == "sketch" else q, tag=tag, develop=look)


main()
