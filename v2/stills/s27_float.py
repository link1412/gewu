"""Shot 27, third version: one sheet of gold leaf (金箔) borne up on rising air, edges curled, slowly undulating. Replaces s27_jinbo.py, whose sheet lay on a mound and read as ore.

    python3 -I v2/stills/s27_float.py gold                      the optical numbers, prints and exits
    python3 -I v2/stills/s27_float.py solve                     solve the sheet's motion, print metrics, no render
    python3 -I v2/stills/s27_float.py look  preview|mid|final [FRAME]     still; final goes to out/v2/s27_jinbo/cand.*
    python3 -I v2/stills/s27_float.py take  preview|mid|final   all frames; final goes to out/v2/s27_jinbo_take_cand/, with take.mp4
    python3 -I v2/stills/s27_float.py deliver [q]               only take.mp4 and the image metrics of a take already there

How it is made:
- SOLVE, coarse (NC x NC): the shape comes from a target with prescribed curvature (an arch over the air, a wave running left to right along the sheet, curled edges), which on its own would stretch.
  A thin-shell energy (edges and diagonals keep their rest length, second differences follow the target's, a weak tether to the target) is minimised with L-BFGS, warm started from the previous frame.
  This is not a fluid solve: the air is prescribed as a shape. It is a sheet that keeps its length while a wave is made to pass through it.
- MEMORY, fine: creases, hammered mottling and crinkle are a height attached to the material (u, v), displaced along the normal of the moving sheet. A crease once made stays and rides the wave.
- Mesh: no thickness; faces beyond the torn edge do not exist.
- Material: gold(). n, k: Johnson & Christy 1972 (looked up). Transmission: Airy formula on those n, k (computed).

The old black streaks above the arc (s27_jinbo): the old grid ran on past the edge with Alpha 0. Not proven to be the cause; the new mesh has no faces there, and the area above the arc is scanned in `deliver`.
Scales: leaf side 9.33 cm is the Nanjing size from memory (searched, not confirmed: an estimate). Thickness 100 nm: sources give about 100 nm machine made, 50 nm hand beaten (looked up, not rigorous). Crease sizes are estimates by eye.
"""

import hashlib
import inspect
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.optimize import minimize
from scipy.spatial import cKDTree

from kit import OUT, blur, fbm, frame_camera, rank, shoot, sstep
from vessel import cam_basis, project, reflect_light_loc

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "s27_jinbo"
SEED = 2711
FRAMES = 12
LEAF = 9.33  # cm, side of the leaf (estimate)
HALF = LEAF / 2
HS = 5.2  # half side of the grid, beyond the leaf's edge
NC = 129  # the coarse sheet
PITCH = np.radians(6.0)  # the far side of the sheet is raised
EL = np.radians(12.0)
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)])
W, DIST, APERTURE = 11.2, 60.0, 2.0
APEX = 0.48  # where the arc is in frame 0; it rises a little over the take
OMEGA = 0.16  # rad per frame of the main wave
RISE = 0.012  # cm per frame
LOOK = {"exposure": 0.2, "contrast": 1.3, "saturation": 1.06, "black": 0.0012, "grain": 1.1, "sharpen": 0.22, "halation": 0.05, "glare": 0.006, "vignette": 0.25}

# Johnson & Christy, Phys. Rev. B 6, 4370 (1972), gold, via refractiveindex.info: wavelength nm, n, k (looked up)
JC = np.array(
    [[397.4, 1.47, 1.952], [413.3, 1.46, 1.958], [430.5, 1.45, 1.948], [450.9, 1.38, 1.914], [471.4, 1.31, 1.849], [495.9, 1.04, 1.833], [520.9, 0.62, 2.081], [548.6, 0.43, 2.455], [582.1, 0.29, 2.863], [616.8, 0.21, 3.272], [659.5, 0.14, 3.697], [704.5, 0.13, 4.103], [756.0, 0.14, 4.542]]
)
RGB_NM = (630.0, 532.0, 465.0)  # the shader's RGB n, k are JC at these wavelengths; gold() compares their F0 with the integral over the spectrum


def nk(lam):
    return np.interp(lam, JC[:, 0], JC[:, 1]), np.interp(lam, JC[:, 0], JC[:, 2])


def cmf(lam):
    """CIE 1931 x, y, z: the multi-lobe Gaussian fit of Wyman, Sloan, Shirley 2013 (an approximation, coefficients from memory of the paper)."""

    def g(x, m, s1, s2):
        s = np.where(x < m, s1, s2)
        return np.exp(-0.5 * ((x - m) / s) ** 2)

    x = 1.056 * g(lam, 599.8, 37.9, 31.0) + 0.362 * g(lam, 442.0, 16.0, 26.7) - 0.065 * g(lam, 501.1, 20.4, 26.2)
    y = 0.821 * g(lam, 568.8, 46.9, 40.5) + 0.286 * g(lam, 530.9, 16.3, 31.1)
    z = 1.217 * g(lam, 437.0, 11.8, 36.0) + 0.681 * g(lam, 459.0, 26.0, 13.8)
    return np.stack([x, y, z], -1)


XYZ2RGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])


def film_T_R(lam, d_nm):
    """Normal incidence on a free film in air. Airy; complex index N = n + ik."""
    n, k = nk(lam)
    N = n + 1j * k
    r = (1 - N) / (1 + N)
    ph = np.exp(1j * 2 * np.pi * N * d_nm / lam)
    den = 1 - r * r * ph**2
    t = (1 - r * r) * ph / den
    rr = r * (1 - ph**2) / den
    return np.abs(t) ** 2, np.abs(rr) ** 2


def spectral_rgb(values, lam):
    """Linear Rec.709 of a spectral reflectance or transmittance under equal-energy white: an approximation, the lights here are only near white."""
    c = cmf(lam)
    xyz = (values[..., None] * c).sum(-2) / c[:, 1].sum()
    return xyz @ XYZ2RGB.T


def trans_table():
    lam = np.arange(400.0, 750.0, 5.0)
    ds = np.arange(30.0, 201.0, 5.0)
    T = np.stack([film_T_R(lam, d)[0] for d in ds])
    return ds, np.clip(spectral_rgb(T, lam), 0, None)


def gold():
    lam = np.arange(400.0, 750.0, 5.0)
    print("n, k at RGB", [tuple(round(float(x), 3) for x in nk(l)) for l in RGB_NM])
    print("F0 of those three n, k", [round(float(((nk(l)[0] - 1) ** 2 + nk(l)[1] ** 2) / ((nk(l)[0] + 1) ** 2 + nk(l)[1] ** 2)), 3) for l in RGB_NM])
    n, k = nk(lam)
    print("F0 integrated over the spectrum, linear Rec.709", np.round(spectral_rgb(((n - 1) ** 2 + k**2) / ((n + 1) ** 2 + k**2), lam), 3))
    for d in (50.0, 80.0, 100.0, 130.0, 160.0):
        T, R = film_T_R(lam, d)
        i = int(np.argmax(T))
        print(f"d {d:.0f} nm: T peak {T[i] * 100:.2f}% at {lam[i]:.0f} nm; T rgb % {np.round(spectral_rgb(T, lam) * 100, 3)}; R rgb {np.round(spectral_rgb(R, lam), 3)}")


# --- the outline: the same at every quality ---------------------------------------------------------------------------
def torn_edge(seed):
    """One side's edge as an inward offset (cm) along that side, 100 samples per cm: slow bays, sharp narrow notches, small tabs."""
    rng = np.random.default_rng(seed)
    n = int(2 * HS * 100)
    xs = np.linspace(-HS, HS, n)

    def low(sig):
        return cv2.GaussianBlur(rng.normal(0, 1, n).astype(np.float32)[None], (0, 0), sig)[0] * np.sqrt(2 * np.sqrt(np.pi) * sig)

    e = 0.17 * low(90.0) + 0.024 * low(6.0)
    for _ in range(16):
        c, w_, d_ = rng.uniform(-HS, HS), rng.lognormal(np.log(0.05), 0.6), rng.lognormal(np.log(0.09), 0.9)
        e = e + d_ * np.exp(-np.abs(xs - c) / w_)
    for _ in range(5):
        c, w_, d_ = rng.uniform(-HS, HS), rng.lognormal(np.log(0.09), 0.4), rng.lognormal(np.log(0.07), 0.4)
        e = e - d_ * np.exp(-(((xs - c) / w_) ** 2))
    return xs, e


def inside(U, V):
    """> 0 is leaf, about cm from the edge."""
    d = []
    for i, (a, b) in enumerate(((U, V), (-U, V), (V, U), (-V, U))):
        xs, e = torn_edge(SEED + 40 + i)
        bow = 1.1 * (b / HALF) ** 2 if i == 2 else 0.0  # the far edge tore in a long bow: this leaf is not a square any more, and the arc of the picture is partly this
        d.append(HALF - a - bow - np.interp(b, xs, e).astype(np.float32))
    d = np.min(d, axis=0)
    # corners torn off: a beaten leaf has no clean corners
    rng = np.random.default_rng(SEED + 44)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        d = np.minimum(d, (2 * HALF - rng.uniform(0.25, 0.9) - sx * U - sy * V) / np.sqrt(2))
    return d


# --- the moving sheet -------------------------------------------------------------------------------------------------
def coarse_grid():
    s = np.linspace(-HS, HS, NC)
    return np.meshgrid(s, s)  # U by column, V by row; row 0 is the near side


def memory_fields():
    """What does not change: the sheet's slow memory of having been handled, and how each edge curls."""
    px = (NC - 1) / (2 * HS)
    mem = fbm((NC, NC), px, 1.0, 6.0, 2.6, SEED + 20)
    mem2 = fbm((NC, NC), px, 1.0, 6.0, 2.6, SEED + 21)
    s = np.linspace(-HS, HS, NC)
    rng = np.random.default_rng(SEED + 22)

    def slow(lo, hi):
        f = cv2.GaussianBlur(rng.normal(0, 1, NC * 3).astype(np.float32)[None], (0, 0), 14.0)[0][NC:2 * NC]
        f = (f - f.min()) / (f.max() - f.min())
        return lo + (hi - lo) * f

    return {"s": s, "mem": mem, "mem2": mem2, "far": slow(-0.08, 0.32), "near": slow(0.1, 1.5), "left": slow(0.35, 1.5), "right": slow(0.25, 1.6)}


def target(t, m):
    """Target shape at frame t: not isometric, the solve makes it so."""
    U, V = coarse_grid()
    ds = m["s"][1] - m["s"][0]
    ph = OMEGA * t
    S = U / HALF
    arch = -(0.62 * (1 + 0.1 * np.sin(0.5 * V + 1.0)) * (1 + 0.55 * sstep(-1.0, HALF, V))) * (S - 0.06) * (1 + 0.1 * S**2)  # more towards the far edge: a cone, still developable
    # the wave, left to right; shorter parts are smaller
    wave = 0.30 * np.sin(2 * np.pi * U / 5.2 - ph + 0.2 * V + 0.5) + 0.12 * np.sin(2 * np.pi * U / 2.6 - 1.5 * ph - 0.16 * V + 2.1) + 0.04 * np.sin(2 * np.pi * U / 1.3 - 2.2 * ph + 0.4 * V + 0.3)
    wave = wave * (1 - 0.65 * sstep(0.5, HALF, V))  # a quiet far edge, so that the arc reads
    th = arch + wave + 0.10 * m["mem"]
    th = th + m["right"][:, None] * sstep(HALF - 1.6, HALF + 0.1, U) ** 2 - m["left"][:, None] * sstep(HALF - 1.6, HALF + 0.1, -U) ** 2
    x = np.cumsum(np.cos(th), 1) * ds
    z = np.cumsum(np.sin(th), 1) * ds
    c = NC // 2
    x = x - x[:, c:c + 1]
    z = z - z[:, c:c + 1]
    # along the sheet towards and away from the camera: a slower wave, and the two edges curling
    far = m["far"][None] * (1 + 0.1 * np.sin(ph - 0.6 * U))
    near = m["near"][None] * (1 + 0.1 * np.sin(ph - 0.6 * U + 1.0))
    ph2 = 0.08 * np.sin(2 * np.pi * (V / 5.6 + U / 11.0) - 0.8 * ph + 1.0) + 0.055 * m["mem2"]
    a_ = ph2 + far * sstep(HALF - 1.2, HALF + 0.1, V) ** 2 - near * sstep(HALF - 1.1, HALF + 0.1, -V) ** 2
    a = np.cumsum(np.cos(a_), 0) * ds
    b = np.cumsum(np.sin(a_), 0) * ds
    a = a - a[c:c + 1]
    b = b - b[c:c + 1]
    X = np.stack([x - b * np.sin(th), a, z + b * np.cos(th)], -1)
    X[..., 2] -= X[..., 2].mean()  # the wave passes; it does not carry the sheet up and down: only the air does (RISE)
    # the whole leaf tilted up at the far side, and carried up by the air
    c_, s_ = np.cos(PITCH), np.sin(PITCH)
    Y = X.copy()
    Y[..., 1] = X[..., 1] * c_ - X[..., 2] * s_
    Y[..., 2] = X[..., 1] * s_ + X[..., 2] * c_ + RISE * t
    return Y


EDGES = [
    ((slice(None), slice(None, -1)), (slice(None), slice(1, None)), 1.0),
    ((slice(None, -1), slice(None)), (slice(1, None), slice(None)), 1.0),
    ((slice(None, -1), slice(None, -1)), (slice(1, None), slice(1, None)), np.sqrt(2.0)),
    ((slice(None, -1), slice(1, None)), (slice(1, None), slice(None, -1)), np.sqrt(2.0)),
]
KS, KB, KT = 1.0, 1.0, 1e-4


def second_diffs(X):
    return X[:-2] - 2 * X[1:-1] + X[2:], X[:, :-2] - 2 * X[:, 1:-1] + X[:, 2:]


def solve_frame(T, X0, h, iters):
    D0, D1 = second_diffs(T)

    def f(x):
        X = x.reshape(NC, NC, 3)
        G = np.zeros_like(X)
        e = 0.0
        for A, B, l in EDGES:
            d = X[A] - X[B]
            L = np.linalg.norm(d, axis=-1, keepdims=True)
            r = L / (l * h) - 1
            e += KS * float((r * r).sum())
            g = 2 * KS * r / (l * h) * d / L
            G[A] += g
            G[B] -= g
        S0, S1 = second_diffs(X)
        S0, S1 = S0 - D0, S1 - D1
        e += KB * float((S0 * S0).sum() + (S1 * S1).sum())
        G[:-2] += 2 * KB * S0
        G[1:-1] -= 4 * KB * S0
        G[2:] += 2 * KB * S0
        G[:, :-2] += 2 * KB * S1
        G[:, 1:-1] -= 4 * KB * S1
        G[:, 2:] += 2 * KB * S1
        dT = X - T
        e += KT * float((dT * dT).sum())
        G += 2 * KT * dT
        return e, G.ravel()

    r = minimize(f, X0.ravel(), jac=True, method="L-BFGS-B", options={"maxiter": iters, "maxcor": 30, "ftol": 1e-14, "gtol": 1e-9})
    return r.x.reshape(NC, NC, 3)


def motion():
    """(FRAMES, NC, NC, 3). Cached on the source of what shapes it."""
    key = hashlib.md5("".join(inspect.getsource(g) for g in (target, solve_frame, memory_fields)).encode() + repr((FRAMES, NC, PITCH, OMEGA, RISE, KS, KB, KT, HS)).encode()).hexdigest()[:10]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, f"sheet_motion.{key}.npy")
    if os.path.exists(fp):
        return np.load(fp)
    for f in os.listdir(d):
        if f.startswith("sheet_motion."):
            os.remove(os.path.join(d, f))
    m = memory_fields()
    h = 2 * HS / (NC - 1)
    out = []
    X = target(0.0, m)
    Tp = X
    for i in range(FRAMES):
        T = target(float(i), m)
        X = solve_frame(T, X + (T - Tp), h, 1000 if i == 0 else 300)
        Tp = T
        out.append(X.astype(np.float32))
        print(f"solved frame {i}", flush=True)
    out = np.stack(out)
    np.save(fp, out)
    return out


def tri_areas(X):
    a, b, c, d = X[:-1, :-1], X[1:, :-1], X[1:, 1:], X[:-1, 1:]
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1), 0.5 * np.linalg.norm(np.cross(c - a, d - a), axis=-1)


def sheet_metrics(stack):
    U, V = coarse_grid()
    h = 2 * HS / (NC - 1)
    ins = inside(U.astype(np.float32), V.astype(np.float32)) > 0
    quads = ins[:-1, :-1] & ins[1:, :-1] & ins[1:, 1:] & ins[:-1, 1:]
    i_, j_ = np.nonzero(ins)
    ij = np.stack([i_, j_], 1)
    rest = h * h / 2
    print(f"frame | edge strain pct mean, p99, max | area err pct sum, max tri | closest non-neighbour points, in cells of {h:.3f} cm")
    for f, X in enumerate(stack):
        st = []
        for A, B, l in EDGES:
            mk = ins[A] & ins[B]
            st.append((np.linalg.norm(X[A] - X[B], axis=-1) / (l * h) - 1)[mk])
        st = np.abs(np.concatenate(st)) * 100
        t1, t2 = tri_areas(X)
        at = np.r_[t1[quads], t2[quads]]
        pts = X[ins]
        tr = cKDTree(pts)
        pairs = tr.query_pairs(4 * h, output_type="ndarray")
        far = np.abs(ij[pairs[:, 0]] - ij[pairs[:, 1]]).max(1) > 8  # further than 8 cells apart on the sheet, yet near in space
        cl = np.inf
        if far.any():
            cl = np.linalg.norm(pts[pairs[far, 0]] - pts[pairs[far, 1]], axis=-1).min() / h
        print(f"{f:3d} | {st.mean():.3f} / {np.percentile(st, 99):.3f} / {st.max():.3f} | {(at.sum() / (rest * at.size) - 1) * 100:+.3f}, {np.abs(at / rest - 1).max() * 100:.2f} | {cl:.2f}")
    v = np.diff(stack, axis=0)
    a = np.diff(v, axis=0)
    print("motion: mean |dX| per frame cm", np.round(np.linalg.norm(v[:, ins], axis=-1).mean(1), 4))
    print("smoothness: mean |d2X|, max |d2X| per frame cm", np.round(np.linalg.norm(a[:, ins], axis=-1).mean(1), 5), np.round(np.linalg.norm(a[:, ins], axis=-1).max(1), 4))


# --- the material: everything that belongs to the leaf, not to the moment ------------------------------------------------
def wrinkles(shape, pxcm, seed, classes=((0.30, 6.5, 0.05, 0.011), (1.3, 2.2, 0.024, 0.0042), (6.0, 0.8, 0.012, 0.0016), (22.0, 0.25, 0.0065, 0.0006))):
    """Fold lines on a slowly turning flow; branches leave bigger lines. Each class: (lines per cm2, mean length cm, ridge half width cm, height cm). From s27_jinbo.py, sparser."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    field = fbm((96, 96), 96 / 22.0, 1.5, 16.0, 3.4, seed + 1)
    field2 = fbm((96, 96), 96 / 22.0, 0.6, 3.0, 2.2, seed + 2)
    theta_f = (field * 1.3 + 0.28 * field2).astype(np.float32)

    def theta(xp, yp):
        ix = np.clip((xp / nx * 95).astype(int), 0, 95)
        iy = np.clip((yp / ny * 95).astype(int), 0, 95)
        return theta_f[iy, ix]

    out = np.zeros(shape, np.float32)
    anchors = np.empty((0, 3), np.float32)
    for per, Lm, wd, hgt in classes:
        if wd * pxcm < 0.55:
            continue
        n = int(area * per)
        px, py = rng.uniform(0, nx, n), rng.uniform(0, ny, n)
        off = np.zeros(n)
        if len(anchors):
            br = rng.random(n) < 0.6
            pick = rng.integers(0, len(anchors), n)
            px[br], py[br] = anchors[pick[br], 0], anchors[pick[br], 1]
            off[br] = rng.choice([-1, 1], br.sum()) * rng.uniform(0.5, 1.2, br.sum())
        cross = rng.random(n) < 0.3
        off[cross] += np.pi / 2
        L = rng.lognormal(np.log(Lm), 0.6, n) * pxcm
        steps = 14
        pts = np.zeros((n, steps, 2), np.float32)
        pts[:, 0, 0], pts[:, 0, 1] = px, py
        jit = rng.normal(0, 0.25, n)
        for s in range(1, steps):
            a = theta(pts[:, s - 1, 0], pts[:, s - 1, 1]) + off + jit + rng.normal(0, 0.09, n)
            pts[:, s, 0] = pts[:, s - 1, 0] + np.cos(a) * L / (steps - 1)
            pts[:, s, 1] = pts[:, s - 1, 1] + np.sin(a) * L / (steps - 1)
        lab = np.zeros(shape, np.int32)
        ampl = rng.lognormal(0, 0.55, n) * rng.choice([1.0, 1.0, 1.0, -0.65], n)
        vals = [0.0]
        P = np.round(pts * 16).astype(np.int32)
        k = 1
        for i in range(n):
            for s in range(steps - 1):
                cv2.line(lab, tuple(int(c) for c in P[i, s]), tuple(int(c) for c in P[i, s + 1]), k, 1, cv2.LINE_8, shift=4)
                vals.append(ampl[i] * np.sin(np.pi * (s + 0.5) / (steps - 1)) ** 0.7)
                k += 1
        vals = np.array(vals, np.float32)
        mask = (lab == 0).astype(np.uint8)
        d, lb = cv2.distanceTransformWithLabels(mask, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        z = mask == 0
        pick = np.zeros(lb.max() + 2, np.int32)
        pick[lb[z]] = lab[z]
        out += hgt * vals[pick[lb]] * np.exp(-d.astype(np.float32) / pxcm / wd)
        anchors = pts[:: max(1, n // 3000), :: 3].reshape(-1, 2)
        anchors = np.c_[anchors, np.zeros(len(anchors))].astype(np.float32)
    return out


def straight_folds(U, V, seed):
    """A few long clean folds from handling: a soft foil folds along a straight line and the line stays."""
    rng = np.random.default_rng(seed)
    out = np.zeros(U.shape, np.float32)
    for _ in range(7):
        a = rng.uniform(0, np.pi)
        cx, cy = rng.uniform(-3.5, 3.5, 2)
        L = rng.uniform(1.5, 4.5)
        wd = rng.lognormal(np.log(0.03), 0.35)
        hgt = rng.choice([-1.0, 1.0]) * rng.lognormal(np.log(0.007), 0.4)
        along = (U - cx) * np.cos(a) + (V - cy) * np.sin(a)
        across = -(U - cx) * np.sin(a) + (V - cy) * np.cos(a) + 0.02 * np.sin(along * 1.7 + cx)
        out += hgt * np.exp(-np.abs(across) / wd) * sstep(1.0, 0.65, np.abs(along) / L)
    return out


def crumple(shape, pxcm, seed, octaves):
    """Low, slow crumple. Coarse grid, interpolated, then blurred, so that no triangle shows."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    w, h = nx / pxcm, ny / pxcm
    res = 36.0
    gy, gx = int(h * res), int(w * res)
    yy, xx = np.mgrid[0:gy, 0:gx].astype(np.float32)
    xx, yy = (xx + 0.5) / res, (yy + 0.5) / res
    out = np.zeros((gy, gx), np.float32)
    for spacing, slope in octaves:
        n = max(int((w + 2 * spacing) * (h + 2 * spacing) / spacing**2), 8)
        pts = np.stack([rng.uniform(-spacing, w + spacing, n), rng.uniform(-spacing, h + spacing, n)], 1)
        out += LinearNDInterpolator(pts, rng.normal(0, slope * spacing, n), fill_value=0.0)(xx, yy).astype(np.float32)
    out = cv2.GaussianBlur(out, (0, 0), 1.6)
    return cv2.resize(out, (nx, ny), interpolation=cv2.INTER_CUBIC)


def pinholes(shape, pxcm, near, seed):
    """Small holes. Lognormal radius, about 0.01-0.04 cm, clustered; more near the edge and along folds."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    clus = sstep(0.72, 0.95, rank(fbm(shape, pxcm, 0.12, 0.8, 2.3, seed + 1)))
    n = int(area * 30)
    xs, ys = rng.integers(0, nx, n), rng.integers(0, ny, n)
    keep = rng.random(n) < (0.01 + 0.99 * near[ys, xs]) * clus[ys, xs]
    xs, ys = xs[keep], ys[keep]
    out = np.zeros(shape, np.uint8)
    for x_, y_ in zip(xs, ys):
        m = rng.integers(4, 8)
        a = np.sort(rng.uniform(0, 6.283, m))
        r = rng.lognormal(np.log(0.016), 0.55) * pxcm * rng.uniform(0.5, 1.0, m)
        p = np.stack([x_ + r * np.cos(a), y_ + r * np.sin(a) * rng.uniform(0.5, 1.0)], 1)
        cv2.fillPoly(out, [np.round(p * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    return blur(out.astype(np.float32) / 255.0, 0.5)


def material(dens):
    pxcm = 240.0 * dens
    nx = ny = int(2 * HS * pxcm) + 1
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 2), "M", flush=True)
    s = np.linspace(-HS, HS, nx, dtype=np.float32)
    U, V = np.meshgrid(s, s)

    folds = wrinkles(shape, pxcm, SEED + 10) + straight_folds(U, V, SEED + 11)
    soft = crumple(shape, pxcm, SEED, ((1.5, 0.014), (0.55, 0.012)))
    # the fine crinkle: strong in some places, large areas nearly quiet. Quiet areas are what lets the leaf mirror.
    strength = 0.04 + 0.96 * sstep(0.55, 0.95, rank(fbm(shape, pxcm, 0.6, 4.0, 2.8, SEED + 4)))
    crinkle = wrinkles(shape, pxcm, SEED + 3, ((70.0, 0.55, 0.012, 0.0013), (160.0, 0.2, 0.007, 0.0006))) * strength
    # the beater's hammer: a shallow mottling, slope about one degree, everywhere
    mottle = 0.0004 * fbm(shape, pxcm, 0.06, 0.5, 2.2, SEED + 5)
    h = soft + folds + crinkle + mottle

    d_in = inside(U, V) + 0.016 * fbm(shape, pxcm, 0.008, 0.1, 1.5, SEED + 7)
    crease = np.clip(np.abs(folds) / 0.004, 0, 1)
    alpha = sstep(-0.005, 0.005, d_in)
    ph = pinholes(shape, pxcm, np.maximum(sstep(0.9, 0.0, d_in), 0.08 * crease), SEED + 8)
    alpha = alpha * (1.0 - ph)
    keep = cv2.dilate((alpha > 0.002).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)

    # thickness: beaten unevenly, thinner on the creases. Transmission is exponential in it, so this makes the light through the leaf mottled.
    d_nm = 100.0 * np.exp(0.2 * fbm(shape, pxcm, 0.15, 2.5, 2.4, SEED + 15)) * (1 - 0.12 * crease)
    ds, tr = trans_table()
    trans = np.stack([np.interp(d_nm, ds, tr[:, i]) for i in range(3)], -1).astype(np.float32)

    rough = 0.07 + 0.06 * strength + 0.02 * rank(fbm(shape, pxcm, 0.02, 0.2, 2.0, SEED + 6))
    return {"h": h.astype(np.float32), "alpha": alpha.astype(np.float32), "keep": keep, "trans": trans, "rough": np.clip(rough, 0.05, 1).astype(np.float32), "nx": nx, "pxcm": pxcm}


def pose(M, X):
    """The fine sheet from the solved coarse one: a smooth upsample, then the memory along its normal."""
    nx = M["nx"]
    f = (nx - 1) / (NC - 1)
    ix = np.arange(nx, dtype=np.float32) / f
    mx, my = np.meshgrid(ix, ix)
    X = cv2.GaussianBlur(X.astype(np.float32), (0, 0), 1.0, borderType=cv2.BORDER_REPLICATE)  # the solve leaves a little grid-period noise, and a mirror shows it as a woven screen
    B = cv2.remap(X, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    B = cv2.GaussianBlur(B, (0, 0), max(0.8 * f, 0.5), borderType=cv2.BORDER_REPLICATE)  # a cubic upsample shows as ripples in a mirror
    du = np.gradient(B, axis=1)
    dv = np.gradient(B, axis=0)
    N = np.cross(du, dv)
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-12
    return B + N * M["h"][..., None]


# --- the shoot --------------------------------------------------------------------------------------------------------
def camera(stack):
    U, V = coarse_grid()
    ins = inside(U.astype(np.float32), V.astype(np.float32)) > 0
    pts = stack[0][ins]
    cam = frame_camera(np.zeros(3), VIEW, W, DIST)
    tgt = np.zeros(3)
    _, _, right, up = cam_basis(cam)
    fh = W * 9.0 / 16.0
    for _ in range(4):
        x, y, _w = project(cam, pts)
        i = int(np.argmin(y))
        tgt = tgt + up * (APEX - y[i]) * fh + right * (x[pts[:, 0].argsort()[len(pts) // 2]] - 0.5) * W
        cam = frame_camera(tgt, VIEW, W, DIST)
    x, y, _w = project(cam, pts)
    i = int(np.argmin(y))
    return frame_camera(tgt, VIEW, W, DIST, aperture_mm=APERTURE, focus_point=pts[i]), pts[i]


def silhouette_mask(stack, cam, w=640, h=360):
    """Where the leaf covers the frame in every frame of the take, from the coarse sheet."""
    U, V = coarse_grid()
    ins = inside(U.astype(np.float32), V.astype(np.float32)) > 0
    q = ins[:-1, :-1] & ins[1:, :-1] & ins[1:, 1:] & ins[:-1, 1:]
    out = np.ones((h, w), np.uint8)
    for X in stack:
        x, y, _ = project(cam, X.reshape(-1, 3))
        pp = np.stack([x * w, y * h], -1).reshape(NC, NC, 2)
        poly = np.stack([pp[:-1, :-1][q], pp[1:, :-1][q], pp[1:, 1:][q], pp[:-1, 1:][q]], 1)
        m = np.zeros((h, w), np.uint8)
        cv2.fillPoly(m, list(np.round(poly * 16).astype(np.int32)), 1, cv2.LINE_8, shift=4)
        out &= m
    return out


def panel(stack, cam, fp):
    """A soft light hidden behind the leaf, what a photographer would do to make it glow. A mesh, not a light: it is what the camera sees through the film (Transparent BSDF) and through the pinholes.
    Cut to fit behind the leaf with a margin, since it is out of focus."""
    loc, f, right, up = cam_basis(cam)
    k = cam["lens_mm"] / 36.0
    w = DIST + 11.0
    nu, nv = 193, 109
    yy, xx = np.mgrid[0:nv, 0:nu].astype(np.float32)
    x, y = xx / (nu - 1), yy / (nv - 1)
    P = loc + w * (f + right[None, None] * ((x - 0.5) / k)[..., None] + up[None, None] * ((0.5 - y) / (k * 16.0 / 9.0))[..., None])
    mask = silhouette_mask(stack, cam)
    mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=26).astype(np.float32)
    mask = cv2.GaussianBlur(mask, (0, 0), 16.0)
    m = cv2.resize(mask, (nu, nv), interpolation=cv2.INTER_AREA)
    L = 0.35 * np.exp(-(((x - 0.44) / 0.34) ** 2) - ((y - 0.82) / 0.20) ** 2) * sstep(0.1, 0.7, m)
    col = L[..., None] * np.array([1.0, 0.97, 0.92], np.float32)
    # triangles only where it shines: a whole grid would be an opaque black card in front of the sky
    idx = np.arange(nu * nv).reshape(nv, nu)
    on = L > 0
    q = on[:-1, :-1] | on[1:, :-1] | on[1:, 1:] | on[:-1, 1:]
    a_, b_, c_, d_ = idx[:-1, :-1][q], idx[1:, :-1][q], idx[1:, 1:][q], idx[:-1, 1:][q]
    F = np.r_[np.stack([a_, b_, c_], 1), np.stack([a_, c_, d_], 1)]
    np.savez(fp, V=P.reshape(-1, 3).astype(np.float32), F=F.astype(np.int32), col=col.reshape(-1, 3).astype(np.float32))


def studio_env(d, cam, pt):
    """The room the leaf mirrors, in world directions: a hard-edged softbox, a strip, a dim card, the dark rest. Shapes are written in the space of the normal that mirrors them into the camera (tilt across, tilt along),
    so 'the band flashes where the sheet leans 7 to 24 degrees left' is what is written. Hard edges: a mirror with soft reflections is paper. Warm: tungsten on daylight balance, the choice of a photographer, not a measurement."""
    fp = os.path.join(d, "studio_env.npy")
    h, w = 1024, 2048
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    D = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)  # the mapping measured in kit.room_env
    v = np.array(cam["loc"], float) - pt
    v /= np.linalg.norm(v)
    H = D + v.astype(np.float32)
    H /= np.linalg.norm(H, axis=-1, keepdims=True) + 1e-6
    n0 = np.array([0.0, -np.sin(PITCH), np.cos(PITCH)], np.float32)
    ex = np.array([1.0, 0.0, 0.0], np.float32)
    ey = np.array([0.0, np.cos(PITCH), np.sin(PITCH)], np.float32)
    c = H @ n0
    tx = np.degrees(np.arctan2(H @ ex, c))
    ty = np.degrees(np.arctan2(H @ ey, c))

    def box(x0, x1, y0, y1, soft=0.8):
        return sstep(x0 - soft, x0 + soft, tx) * sstep(x1 + soft, x1 - soft, tx) * sstep(y0 - soft, y0 + soft, ty) * sstep(y1 + soft, y1 - soft, ty)

    warm = np.array([1.0, 0.74, 0.42], np.float32)
    L = 0.02 + 0.02 * sstep(-30.0, 40.0, np.degrees(lat))
    # a big dim ceiling card, so that the arc and the slopes stay gold; darker gaps in it give the contrast
    L = L + (0.17 - 0.1 * box(4.0, 12.0, -60.0, 60.0, 1.5)) * box(-65.0, 65.0, -55.0, 50.0, 4.0)
    L = L + 1.25 * box(-16.0, -4.0, -40.0, 30.0) * (0.72 + 0.28 * sstep(-16.0, -4.0, tx))
    L = L + 0.8 * box(15.0, 18.5, -40.0, 30.0)
    L = L + 0.75 * box(-37.0, -31.0, -40.0, 30.0)
    L = L + 0.5 * box(33.0, 40.0, -40.0, 30.0)
    # the leaf is only ever lit from the front half: behind and below, nothing
    L = L * (c > 0)
    np.save(fp, (L[..., None] * warm).astype(np.float32))
    return fp


def scene_for(q, frame, M, stack, cam, apex_pt):
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    P = pose(M, stack[frame])
    fp = os.path.join(d, f"sheet.{q}.{os.getpid()}.npz")
    np.savez(fp, P=P[::-1], rough=M["rough"][::-1], alpha=M["alpha"][::-1], keep=M["keep"][::-1], trans=M["trans"][::-1])
    fb = os.path.join(d, f"panel.{q}.{os.getpid()}.npz")
    panel(stack, cam, fb)

    env = studio_env(d, cam, apex_pt)
    gray = 0.0065
    return {
        "camera": cam,
        "meshes": [
            {"name": "sheet", "npz": fp, "shader_py": os.path.join(HERE, "s27_shader.py"), "params": {"ior": [float(nk(l)[0]) for l in RGB_NM], "ext": [float(nk(l)[1]) for l in RGB_NM]}},
            {"name": "panel", "npz": fb, "material": {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}, "visible": {"diffuse": False, "shadow": False}},
        ],
        "lights": [],
        "world": [0.0, 0.0, 0.0],
        "sky": {"top": [gray, gray, gray], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.55, "seed": 27},
        "env": {"npy": env},
        "diffuse_bounces": 0,
        "glossy_bounces": 6,
        "transmission_bounces": 8,
        "spp": {"preview": 48, "mid": 96, "final": 256},
    }, (fp, fb)


def scrub(paths):
    for p in paths:
        if os.path.exists(p):
            os.remove(p)


def report_apex(stack, cam):
    U, V = coarse_grid()
    ins = inside(U.astype(np.float32), V.astype(np.float32)) > 0
    ys = [float(project(cam, X[ins])[1].min()) for X in stack]
    print("apex y per frame", np.round(ys, 4), flush=True)


def deliver(q):
    d = os.path.join(OUT, f"{NAME}_take_{'cand' if q == 'final' else q}")
    fs = sorted(f for f in os.listdir(d) if f.startswith("f") and f.endswith(".png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(d, "f%03d.png"), "-vf", "scale=1920:1080,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-movflags", "+faststart", os.path.join(d, "take.mp4")], check=True)
    print(os.path.join(d, "take.mp4"), len(fs))
    # the motion in the picture, and the old streaks: anything darker than the background above the arc
    gray = [cv2.cvtColor(cv2.resize(cv2.imread(os.path.join(d, f)), (640, 360), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY) for f in fs]
    for i in range(len(gray) - 1):
        fl = cv2.calcOpticalFlowFarneback(gray[i], gray[i + 1], None, 0.5, 4, 25, 3, 7, 1.5, 0)
        m = gray[i] > 25
        print(f"flow {i}->{i + 1}, px at 2560: median dx {np.median(fl[..., 0][m]) * 4:+.1f} dy {np.median(fl[..., 1][m]) * 4:+.1f}, p95 |v| {np.percentile(np.hypot(fl[..., 0], fl[..., 1])[m], 95) * 4:.1f}")
    for f, g in zip(fs, gray):
        top = cv2.GaussianBlur(g[:130].astype(np.float32), (0, 0), 1.0)
        bg = cv2.GaussianBlur(g[:130].astype(np.float32), (0, 0), 20.0)
        print(f, "above the arc: min-local", round(float((top - bg).min()), 2), "max-local", round(float((top - bg).max()), 2))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "look"
    if mode == "gold":
        return gold()
    if mode == "deliver":
        return deliver(sys.argv[2] if len(sys.argv) > 2 else "final")
    stack = motion()
    if mode == "solve":
        sheet_metrics(stack)
        cam, ap = camera(stack)
        report_apex(stack, cam)
        return None
    q = sys.argv[2] if len(sys.argv) > 2 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    cam, ap = camera(stack)
    report_apex(stack, cam)
    M = material(dens)
    if mode == "look":
        frame = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        scene, tmp = scene_for(q, frame, M, stack, cam, ap)
        shoot(NAME, scene, q, develop=LOOK, tag="cand" if q == "final" else q)
        scrub(tmp)
    else:
        name = f"{NAME}_take_{'cand' if q == 'final' else q}"
        for f in range(FRAMES):
            scene, tmp = scene_for(q, f, M, stack, cam, ap)
            shoot(name, scene, q, develop={**LOOK, "seed": 100 + f}, tag=f"f{f:03d}")
            scrub(tmp)
        deliver(q)
    return None


main()
