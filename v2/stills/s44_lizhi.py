"""Shot 44: lychee, frame-filling macro. A crimson jewelled crust as the arc, glowing cream flesh in great soft swells below it, veins of glass across them.

    python3 -I v2/stills/s44_lizhi.py [preview|mid|draft|final]

This version rebuilds the shot to the LOOK of a frame picked from another film. That frame is a look reference only: no
pixel of it is used and nothing is traced; the layout of the swells, the veins and every shape here are generated. HERE BEAUTY OUTRANKS BOTANICAL ACCURACY. Knowingly not botany:
- the peel is a rounded lip (radius .032 cm) so that its scales face the camera; a real peel's cut band is flat and its scales are foreshortened;
- the scales are a faceted crumple (linear interpolation on a Delaunay mesh of random peaks and hollows), sharper and smaller than a real fruit's plates;
- the flesh's swells are invented: real aril is not divided into sacs this size. There is no stone in frame and none is modelled;
- no peel or stone behind the flesh: the back light reaches the medium directly, which a whole fruit would not allow.

Stand-ins and estimates: all sizes, sigma and colours are estimates chosen by eye, none is measured. Surface Fresnel uses ior 1.5, not about 1.35. The flesh's surface does not refract
(glaze_shader). The amber in the folds is a tinted sheet under the surface. The bright veins and the film of strands round each swell are EMISSIVE lines on an alpha sheet under the surface: they do not catch light, they fake it (small ridges at the surface above them do catch it).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import Delaunay

from glazekit import close_shell
from kit import OUT, ROOT, blur, color, fbm, frame_camera, rank, shoot, sstep
from vessel import project

NAME = "s44_lizhi"
GLAZE = os.path.join(ROOT, "v2", "stills", "glaze_shader.py")

W = 2.0  # frame width, cm: the fruit is wider than the frame
H = W * 9 / 16
RC = 1.615  # the circle at the lip's centre
RL = 0.032  # the lip's radius
Z0 = -0.04  # the lip's centre above the plane of the cut
THETA = 0.98  # half-angle of the arc that is built
DIST = 9.0
APERTURE = 4.2  # mm: at 9 cm a point .1 cm off the focal plane blurs by about .0047 cm, 6 px of 2560. At 8 mm the swells stood so far off the plane that every strand on them melted
APEX = (0.50, 0.49)
SEED = 44
ZB = -0.16  # the medium's flat back. Thickness then follows the swells: tops are thick and glow, folds are thin and let the dark through, the way real translucency reads

VIEW = np.array([0.0, -1.0, 0.0])
RIGHT = np.array([1.0, 0.0, 0.0])
UP = np.array([0.0, 0.0, 1.0])
n_ = VIEW - 0.09 * RIGHT - 0.07 * UP  # the top of the fruit leans towards the camera, the rest falls away below; one end of the arc is further than the other
NORMAL = n_ / np.linalg.norm(n_)
E1 = RIGHT - RIGHT.dot(NORMAL) * NORMAL
E1 = E1 / np.linalg.norm(E1)
E2 = np.cross(NORMAL, E1)
ROT = np.stack([E1, E2, NORMAL], 1).astype(np.float32)


def world(P):
    return P @ ROT.T


class Tex:
    """A field on the plane of the cut, on a fixed grid, so that composition holds in every quality."""

    def __init__(self, lo, hi, beta, seed, n=2600, half=1.9):
        self.f, self.half = fbm((n, n), n / (2 * half), lo, hi, beta, seed).astype(np.float32), half

    def __call__(self, x, y):
        n, sh = self.f.shape[0], np.shape(x)
        mx = ((x + self.half) / (2 * self.half) * (n - 1)).astype(np.float32).reshape(-1, sh[-1])
        my = ((y + self.half) / (2 * self.half) * (n - 1)).astype(np.float32).reshape(-1, sh[-1])
        return cv2.remap(self.f, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).reshape(sh)


def f2l(fx, fy):
    """Frame fractions to the cut's plane, approximately: the crown is at y = RC + RL at fy = APEX[1]."""
    return (fx - 0.5) * W, RC + RL - (fy - APEX[1]) * H


# --- the swells: own layout, in frame fractions: (x, y, radius across in frame widths, height cm, squash along the arc)
SWELLS = [
    (0.255, 0.705, 0.185, 0.2, 1.25),
    (0.545, 0.665, 0.17, 0.22, 1.1),
    (0.815, 0.775, 0.155, 0.18, 1.2),
    (0.065, 0.905, 0.15, 0.17, 1.0),
    (0.40, 1.03, 0.21, 0.25, 1.15),
    (0.70, 1.02, 0.165, 0.2, 1.1),
    (0.98, 1.0, 0.15, 0.17, 1.0),
]


class Body:
    def __init__(self):
        self.under = Tex(0.25, 1.1, 3.0, SEED + 1)  # slow: swells are not spheres
        self.fine = Tex(0.012, 0.05, 1.3, SEED + 2)
        self.film_n = Tex(0.02, 0.1, 1.6, SEED + 3)
        self.wtex = fbm((512, 512), 1.0, 2.0, 30.0, 1.3, SEED + 6)
        self.wx = Tex(0.08, 0.35, 2.4, SEED + 4)
        self.wy = Tex(0.08, 0.35, 2.4, SEED + 5)
        self.swell = [(*f2l(a, b), r * W, h, s) for a, b, r, h, s in SWELLS]

    def base(self, X, Y):
        """Height of the pressed-together swells. Returns z, how close to a fold (h1 - h2 in cm, 0 in the fold) and the distance from the rim."""
        xw = X + 0.05 * self.under(X, Y)
        yw = Y + 0.05 * self.under(Y, X)
        hs, ds, ps = [], [], []
        for cx, cy, r, h, sq in self.swell:
            d2 = ((xw - cx) / (r * sq)) ** 2 + ((yw - cy) / r) ** 2
            ds.append(np.sqrt(d2))
            ps.append(np.arctan2((yw - cy) / r, (xw - cx) / (r * sq)))
            # a soft-topped dome with steep sides: a rounded sac, not a Gaussian
            hs.append(h * (np.sqrt(np.maximum(1.0 - np.minimum(d2, 1.0) * 0.96, 0.0)) - 0.2 * np.maximum(d2 - 1.0, 0.0)))
        hs = np.array(hs, np.float32)
        k = 95.0
        z = np.log(np.exp(k * np.clip(hs, -0.6, 0.6)).sum(0)) / k
        part = np.partition(hs, -2, axis=0)
        fold = part[-1] - part[-2]
        rim = np.clip(RC - RL * np.sin(np.radians(55.0)) - np.hypot(X, Y), 0.0, None)
        fall = 1.0 - np.exp(-rim / 0.07)
        zr = Z0 + RL * np.cos(np.radians(55.0)) - 0.006
        z = zr - 0.075 + (z + 0.075) * fall + 0.012 * self.under(X, Y)
        idx = np.argmax(hs, axis=0)[None]
        self.D = np.take_along_axis(np.array(ds, np.float32), idx, 0)[0]  # 0 at the swell's centre, 1 at its edge
        self.PHI = np.take_along_axis(np.array(ps, np.float32), idx, 0)[0] + idx[0] * 1.7
        return z.astype(np.float32), fold.astype(np.float32), rim.astype(np.float32)

    def film(self_, X, Y):
        """Strands of a glassy film wrapped round each swell: long lines along the contour, gathered near its edge. Call right after base() on the same X, Y."""
        D, PHI = self_.D, self_.PHI
        wob = 0.018 * self_.under(X * 2.1, Y * 2.1)
        mx = np.mod(PHI / (2 * np.pi) * 70.0, 512.0).astype(np.float32)
        my = np.mod((D + wob) * 330.0, 512.0).astype(np.float32)
        n = cv2.remap(self_.wtex, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        strand_ = np.clip(1.0 - np.abs(n) / 0.3, 0.0, 1.0) ** 3
        gather = sstep(0.5, 0.93, D) * sstep(-0.9, 0.6, self_.wy(X * 0.5, Y * 0.5))
        return (strand_ * gather).astype(np.float32), gather.astype(np.float32)


def strand(canvas, pts, width, px, x0, y0):
    ip = np.round(np.stack([(pts[:, 0] - x0) * px, (pts[:, 1] - y0) * px], 1) * 16).astype(np.int32)
    n = len(pts)
    for i in range(n - 1):
        t = i / max(n - 1, 1)
        w = width * (1 - 0.7 * t) * px
        cv2.line(canvas, tuple(int(q) for q in ip[i]), tuple(int(q) for q in ip[i + 1]), 1.0, max(1, int(round(w))), cv2.LINE_AA, shift=4)


def veins(body, px, seed, n_arcs=2, branch=0.5, width=0.0014):
    """The glass veins: arcs that hug each swell and fork. Branches curve away and thin out. Returns the canvas and its origin."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = -1.25, 1.25, 0.8, 1.72
    canvas = np.zeros((int((y1 - y0) * px), int((x1 - x0) * px)), np.float32)
    stack = []
    for cx, cy, r, h, sq in body.swell:
        for _ in range(n_arcs):
            a0 = rng.uniform(0, 2 * np.pi)
            span = rng.uniform(0.7, 2.6) * rng.choice([-1, 1])
            rr = rng.uniform(0.55, 1.02)
            n = int(abs(span) * 40)
            aa = a0 + np.linspace(0, span, n)
            wand = np.cumsum(rng.normal(0, 0.006, n))
            pts = np.stack([cx + (r * sq * rr + wand) * np.cos(aa), cy + (r * rr + wand) * np.sin(aa)], 1)
            stack.append((pts, width * rng.uniform(0.5, 1.2), 0))
    while stack:
        pts, w, gen = stack.pop()
        strand(canvas, pts, w, px, x0, y0)
        if gen >= 3:
            continue
        for _ in range(rng.poisson(branch * 2)):
            i = rng.integers(1, len(pts) - 1)
            d = pts[i] - pts[i - 1]
            a = np.arctan2(d[1], d[0]) + rng.choice([-1, 1]) * rng.uniform(0.35, 1.0)
            L = rng.uniform(0.06, 0.3) * 0.75**gen
            n = max(int(L * 120), 4)
            curl = rng.normal(0, 0.05)
            ang = a + np.cumsum(rng.normal(curl, 0.09, n))
            q = pts[i] + np.cumsum(np.stack([np.cos(ang), np.sin(ang)], 1) * (L / n), 0)
            stack.append((q, w * 0.7, gen + 1))
    return canvas, x0, y0, px


def sample(c, X, Y):
    canvas, x0, y0, px = c
    return cv2.remap(canvas, ((X - x0) * px).astype(np.float32), ((Y - y0) * px).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def thin_crease(fold, X, Y, width):
    """A mask of even width along fold = 0: fold / |grad fold| is a distance in cm."""
    gy, gx = np.gradient(fold)
    dy, dx = np.gradient(Y), np.gradient(X)
    ds = np.sqrt(0.5 * (dx[0] ** 2 + dy[0] ** 2 + dx[1] ** 2 + dy[1] ** 2)) + 1e-6
    g = np.sqrt(gx**2 + gy**2) / ds + 1e-3
    return np.exp(-((fold / (g * width)) ** 2)).astype(np.float32)


def build_flesh(dens, body):
    nr, nt = int(1000 * dens), int(3800 * dens)
    rho_in = RC - RL * np.sin(np.radians(55.0))
    rho = np.linspace(rho_in, 0.92, nr, dtype=np.float32)
    th = np.linspace(np.pi / 2 - THETA, np.pi / 2 + THETA, nt, dtype=np.float32)
    Rg, Tg = np.meshgrid(rho, th, indexing="ij")
    X, Y = Rg * np.cos(Tg), Rg * np.sin(Tg)
    z, fold, rim = body.base(X, Y)

    v = veins(body, 900.0, SEED + 10)
    vm = sample(v, X, Y)
    # the main membranes lie in the folds, broken here and there
    breaks = sstep(-0.6, 0.5, body.wx(X * 0.6, Y * 0.6))
    crease = thin_crease(fold, X, Y, 0.0035) * breaks * sstep(0.0, 0.02, rim)
    vein = np.clip(np.maximum(vm, crease), 0, 1)
    vs = blur(vein, max(1.1 * dens, 0.6))
    near = blur(vein, 14 * dens)
    near = np.clip(near / (np.percentile(near, 99) + 1e-6), 0, 1)
    # a film wrinkles round the veins; away from them the surface is calm and takes broad soft reflections
    wr = body.film_n(X + 0.02 * body.wy(X, Y), Y + 0.02 * body.wx(X, Y))
    st, gath = body.film(X, Y)
    h = z + 0.0024 * vs + 0.0016 * near * wr + 0.0009 * wr * gath + 0.0024 * st + 0.00012 * body.fine(X, Y)
    rough = 0.075 + 0.035 * rank(body.fine(X, Y)) - 0.03 * vs
    P = np.stack([X, Y, h], -1).astype(np.float32)
    mb = max(nr // 24, 8)
    rb = np.linspace(rho_in, 0.92, mb, dtype=np.float32)
    Rb, Tb = np.meshgrid(rb, th, indexing="ij")
    bot = np.stack([Rb * np.cos(Tb), Rb * np.sin(Tb), np.full_like(Rb, ZB)], -1).astype(np.float32)
    Pg, at = close_shell(P, bot, {"rough": rough.astype(np.float32)}, {"rough": 0.3}, outward=np.array([0.0, 0.0, 1.0]))
    return world(Pg).astype(np.float32), at["rough"], v


def flesh_sheets(dens, body, v):
    """Under the surface: milky veins right under it, amber in the folds and at the rim, deep membranes with true parallax."""
    nr, nt = int(620 * dens), int(2400 * dens)
    rho_in = RC - RL * np.sin(np.radians(55.0)) - 0.002
    rho = np.linspace(rho_in, 0.92, nr, dtype=np.float32)
    th = np.linspace(np.pi / 2 - THETA, np.pi / 2 + THETA, nt, dtype=np.float32)
    Rg, Tg = np.meshgrid(rho, th, indexing="ij")
    X, Y = Rg * np.cos(Tg), Rg * np.sin(Tg)
    z, fold, rim = body.base(X, Y)
    st, gath = body.film(X, Y)
    D = body.D
    vm = sample(v, X, Y)
    crease = thin_crease(fold, X, Y, 0.0035) * sstep(-0.6, 0.5, body.wx(X * 0.6, Y * 0.6)) * sstep(0.0, 0.02, rim)
    vein = np.clip(np.maximum(vm, crease), 0, 1)
    deep = veins(body, 300.0, SEED + 20, n_arcs=3, branch=0.5, width=0.007)
    dm = blur(sample(deep, X, Y), max(3 * dens, 1))
    out = []
    ivory = color([1.0, 0.95, 0.84])
    # just under the surface: the veins' white, and a glow round them
    halo = blur(vein, 16 * dens)
    halo = np.clip(halo / (np.percentile(halo, 99.5) + 1e-6), 0, 1)
    fd = sstep(0.035, 0.0, fold) * sstep(0.0, 0.03, rim)
    tops = sstep(0.04, 0.16, fold)
    gold = np.exp(-rim / 0.05)
    # a milky sheet would stop the back light and read as a dark crack; these glow by themselves, a stand-in for light carried along a wet membrane
    vv = blur(vein, max(0.7 * dens, 0.5))
    alpha = np.clip(0.7 * vv + 0.08 * halo + 0.85 * st + 0.05 * gath, 0, 1)
    P = np.stack([X, Y, z - 0.002], -1).astype(np.float32)
    out.append(dict(P=world(P).astype(np.float32), a=alpha.astype(np.float32), ec=(np.clip(vv + 0.2 * halo + 0.9 * st + 0.08 * gath, 0, 1)[..., None] * color([2.3, 2.05, 1.65])).astype(np.float32)))
    # amber: thick in the folds and against the rim, over the deep light
    am = np.clip(fd + 0.9 * gold, 0, 1)
    # the middle of a swell runs deeper and warmer than the film round it
    ip = sstep(0.95, 0.15, D) * sstep(0.0, 0.06, rim)
    T = np.stack([(1 - 0.08 * am) * (1 - 0.02 * ip), (1 - 0.36 * am) * (1 - 0.08 * ip), (1 - 0.72 * am) * (1 - 0.18 * ip)], -1)
    P = np.stack([X, Y, z - 0.02], -1).astype(np.float32)
    out.append(dict(P=world(P).astype(np.float32), tint=np.clip(T, 0, 1).astype(np.float32), milk=(0.04 * tops).astype(np.float32), mcol=np.broadcast_to(ivory, X.shape + (3,)).copy()))
    # the deep membranes
    for frac, a in ((0.25, 0.42), (0.55, 0.3)):
        P = np.stack([X, Y, z - frac * (z - ZB)], -1).astype(np.float32)
        out.append(dict(P=world(P).astype(np.float32), tint=np.ones(X.shape + (3,), np.float32), milk=(a * dm).astype(np.float32), mcol=np.broadcast_to(color([1.0, 0.86, 0.66]), X.shape + (3,)).copy()))
    return out


def tin(s, t, spacing, seed, power=1.5):
    """A faceted crumple: random heights on a jittered mesh, linear across each triangle, so faces are planes and both ridges and valleys are sharp, with no groove around any one scale."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = float(s.min()) - spacing, float(s.max()) + spacing, float(t.min()) - spacing, float(t.max()) + spacing
    ny, nx = int((y1 - y0) / (spacing * 0.87)) + 2, int((x1 - x0) / spacing) + 2
    xs, ys = np.meshgrid(x0 + np.arange(nx) * spacing, y0 + np.arange(ny) * spacing * 0.87)
    xs = xs + (np.arange(ny)[:, None] % 2) * spacing / 2
    p = np.stack([xs.ravel(), ys.ravel()], 1) + rng.normal(0, spacing * 0.27, (nx * ny, 2))
    z = rng.random(len(p)) ** power
    return LinearNDInterpolator(Delaunay(p), z, fill_value=0.0)(s.ravel(), t.ravel()).reshape(s.shape).astype(np.float32)


def build_lip(dens, body):
    """The crust: a rounded lip with a crumple on it. Colour: wine in the valleys, crimson on the faces, orange-gold high on the ridges; a gold line where it meets the flesh."""
    na, nt = int(460 * dens), int(4200 * dens)
    al = np.radians(np.linspace(-58.0, 175.0, na, dtype=np.float32))
    th = np.linspace(np.pi / 2 - THETA - 0.02, np.pi / 2 + THETA + 0.02, nt, dtype=np.float32)
    A, T = np.meshgrid(al, th, indexing="ij")
    s, t = (T - np.pi / 2) * RC, A * RL * 1.5  # a little more relief across the lip than its true arc length, or it holds only two rows
    gr = sstep(np.radians(-52.0), np.radians(-28.0), A + 0.3 * body.wx(s, np.full_like(s, 0.3)))
    Tc = tin(s, t, 0.058, SEED + 30, 1.3)
    Tm = tin(s, t, 0.03, SEED + 32, 1.6)
    Tf = tin(s, t, 0.012, SEED + 31, 1.2)
    rel = Tc * (0.55 + 0.45 * Tm)
    h = gr * (0.05 * Tc + 0.02 * Tm + 0.0045 * Tf + 0.0004 * body.fine(s * 1.7, t * 1.7)) + 0.0003 * body.fine(s, t)
    rho = RC + 0.008 * body.under(s, np.zeros_like(s)) + (RL + h) * np.sin(A)
    z = Z0 + (RL + h) * np.cos(A)
    P = np.stack([rho * np.cos(T), rho * np.sin(T), z], -1).astype(np.float32)

    tone = (1 + 0.1 * body.fine(s * 1.3, t * 1.3)) + 0.3 * sstep(-1.0, 1.0, body.wy(s * 2.2, t * 2.2) + 1.2 * (Tm - 0.45))
    crimson = color([0.56, 0.005, 0.02])[None, None] * tone[..., None]
    wine = color([0.05, 0.0015, 0.006])
    gold = color([0.95, 0.3, 0.035])
    v = sstep(0.0, 0.3, rel)[..., None]  # valleys
    col = wine * (1 - v) + crimson * v
    k = (sstep(0.42, 0.85, rel + 0.25 * (Tf - 0.5)))[..., None] * 0.7
    col = col * (1 - k) + gold * k
    line = (1 - gr)[..., None]
    col = col * (1 - line) + color([0.96, 0.46, 0.09]) * line
    rough = 0.38 + 0.2 * Tf - 0.16 * line[..., 0]
    return world(P).astype(np.float32), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.08, 1).astype(np.float32)


def fit(P):
    crown = world(np.array([[0.0, RC + RL, Z0 + 0.03]], np.float32))[0]
    t = np.array([crown[0], 0.0, crown[2]], float)
    for _ in range(4):
        cam = frame_camera(t, VIEW, W, DIST)
        x, y, _w = project(cam, P)
        m = (x > 0.3) & (x < 0.7)
        apex = float(np.min(y[m]))
        t = t + UP * (APEX[1] - apex) * H
    print("arc: apex y", round(apex, 4))
    return t


def reflect_loc(p, n, cam, dist):
    p, n = np.array(p, float), np.array(n, float)
    n = n / np.linalg.norm(n)
    v = np.array(cam["loc"], float) - p
    v /= np.linalg.norm(v)
    return p + (2 * n.dot(v) * n - v) * dist


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    DRAFT = q == "draft"
    q = "final" if DRAFT else q
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    body = Body()
    Pf, Rf, v = build_flesh(dens, body)
    fp = os.path.join(d, f"mesh.flesh.{q}.npz")
    np.savez(fp, P=Pf, rough=Rf)
    meshes = [{"name": "flesh", "npz": fp, "shader_py": GLAZE, "params": {"kind": "glaze", "ior": 1.5, "g": 0.6, "sigma_s": [6.5, 7.0, 7.6], "sigma_a": [0.07, 0.3, 0.68]}}]
    for i, sh in enumerate(flesh_sheets(dens, body, v)):
        fp = os.path.join(d, f"mesh.sheet{i}.{q}.npz")
        np.savez(fp, **sh)
        if "a" in sh:
            meshes.append({"name": f"sheet{i}", "npz": fp, "material": {"Base Color": [1.0, 0.95, 0.85], "Alpha": "a", "Emission Color": "ec", "Emission Strength": 1.0, "Roughness": 0.3}})
        else:
            meshes.append({"name": f"sheet{i}", "npz": fp, "shader_py": GLAZE, "params": {"kind": "layer"}})
    Pl, Cl, Rl = build_lip(dens, body)
    fp = os.path.join(d, f"mesh.lip.{q}.npz")
    np.savez(fp, P=Pl, col=Cl, rough=Rl)
    meshes.append({"name": "lip", "npz": fp, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5}})

    target = fit(Pl[:: max(Pl.shape[0] // 300, 1), :: max(Pl.shape[1] // 1500, 1)].reshape(-1, 3))
    crown_front = world(np.array([[0.0, RC + RL * 0.75, Z0 + RL * 0.75 + 0.03]], np.float32))[0]  # a little in front of the crown, towards the tops of the swells
    cam = frame_camera(target, VIEW, W, DIST, aperture_mm=APERTURE, focus_point=crown_front)

    # a broad warm window mirrored by the swells' upper-left flanks: soft pools on their tops, none across the whole
    p_d = world(np.array([[-0.45, 1.2, 0.05]], np.float32))[0]
    loc_w = reflect_loc(p_d, NORMAL - 0.18 * E1 + 0.2 * E2, cam, 34.0)
    A = np.array(crown_front)
    lights = [
        # the key: warm, hard and raking across the crust from the upper left, a little in front
        {"name": "key", "loc": (A - RIGHT * 30 + UP * 18 + VIEW * 5).tolist(), "target": A.tolist(), "size": [4, 4], "watts": 20000, "rgb": [1.0, 0.72, 0.44]},
        {"type": "gradient", "name": "pool", "loc": loc_w.tolist(), "target": p_d.tolist(), "size": [26, 18], "sigma": [7, 4], "L": 18.0, "rgb": [1.0, 0.93, 0.8]},
        # behind: the flesh's inner glow
        {"name": "back", "loc": (A - VIEW * 18 - UP * 7).tolist(), "target": (A - UP * 0.6).tolist(), "size": [16, 10], "watts": 6200, "rgb": [1.0, 0.86, 0.66], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.021, 0.0009, 0.0026],  # a very deep warm maroon
        "bounces": 48,
        "volume_bounces": 24,
        "transmission_bounces": 32,
        "glossy_bounces": 4,
        "diffuse_bounces": 3,
        "spp": {"preview": 48, "mid": 128, "final": 320},
    }
    if DRAFT:
        scene["spp"] = {"final": 96}
    look = {"exposure": 0.0, "contrast": 1.3, "saturation": 1.16, "black": 0.0, "grain": 1.1, "sharpen": 0.25, "halation": 0.05, "glare": 0.003, "vignette": 0.3, "wb": [1.03, 1.0, 0.95]}
    shoot(NAME, scene, q, tag="draft" if DRAFT else None, develop=look)


main()
