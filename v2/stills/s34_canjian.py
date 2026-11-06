"""Shot 34: a silk cocoon against the light. The shoulder of the ellipsoid is the arc.

    python3 -I v2/stills/s34_canjian.py [preview|mid|final]

Built like the real thing. What photographs of Bombyx cocoons show (seen at 100%, never in the picture): the shell is pebbled,
soft pillows 1.5-3 mm across with short creases between them; the floss is finer than it looks, single brins that are nearly transparent, most faint, a few catching the light;
hairs are long lazy arcs with now and then a kink, drifting in small companies. Sizes are estimates (a cocoon about 3.5 x 2 cm, a brin about 10 microns, a bave about 20).
- a shell of compacted silk, thick; its relief is a warped, weighted Voronoi diagram (pillow and crease), so that the light and dark inside it come from a rake on a real surface, and not from a noise on the opacity;
- on it, real separate filaments: the worm lays silk in figure-of-eight waves, so each strand is a chain of 8s of its own size
  and direction, its own height above the shell;
- outer floss: a curvature walk over the shell, its own length, lift, width and brightness along the length, some hairs in companies, some with a free end;
- the pupa inside, a dark body that shows as a shadow where the shell is thin.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from scipy.spatial import cKDTree

from kit import OUT, blur, color, fbm, frame_camera, shoot, sstep
from s21_lib import SHEETS, ribbons, up

A, B = 1.78, 1.04  # semi-axes (cm), x and (y, z)
W = 3.75
H = W * 9 / 16
TILT = np.radians(-4.0)
CT, ST = np.cos(TILT), np.sin(TILT)
APEX = 0.51


def surf(u, v, h=0.0):
    """Position on the ellipsoid: u along the long axis (rad, 0 to pi), v around it."""
    # a very slight waist, like most mulberry cocoons
    waist = 1.0 - 0.055 * np.exp(-((np.cos(u) / 0.34) ** 2))
    x = A * np.cos(u)
    rr = B * np.sin(u) ** 0.92 * waist
    return x + 0 * h, rr * np.cos(v), rr * np.sin(v)


def rot(x, y, z):
    return np.stack([x * CT - z * ST, y, x * ST + z * CT], -1)


def normals(p):
    n = p / np.array([A**2, B**2, B**2], np.float32)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)


def project(p, h):
    """Bring points onto the (waisted) ellipsoid along the direction from the axis, then up by h."""
    x = p[..., 0]
    r_ = np.hypot(p[..., 1], p[..., 2]) + 1e-6
    # scale so as to land on the surface
    s = 1.0 / np.sqrt((x / A) ** 2 + (r_ / B) ** 2 + 1e-9)
    q = p * s[..., None]
    c = np.clip(q[..., 0] / A, -1, 1)
    waist = 1.0 - 0.055 * np.exp(-((c / 0.34) ** 2))
    q = q * np.stack([np.ones_like(c), waist, waist], -1)
    return q + normals(q) * h[..., None]


def _relief(nu=900, nv=1200, cell=0.17, seed=34):
    """The pebbling: pillows and creases on the shell, unit height, on a fixed (u, v) grid. A Voronoi diagram weighted per cell (a weighted distance gives cells of unlike size), warped so that its edges wander and it never reads as polygons."""
    r = np.random.default_rng(seed)
    U, V = np.meshgrid(np.linspace(0, np.pi, nu, dtype=np.float32), np.linspace(0, 2 * np.pi, nv, endpoint=False, dtype=np.float32), indexing="ij")
    P = np.stack([A * np.cos(U), B * np.sin(U) * np.cos(V), B * np.sin(U) * np.sin(V)], -1)
    wx, wy, wz = (fbm((nu, nv), nv / (2 * np.pi * B), 0.12, 0.6, 2.4, seed + k) for k in (1, 2, 3))
    W_ = P + 0.075 * np.stack([wx, wy, wz], -1)
    area = 4 * np.pi * (A * B * B) ** (2 / 3)
    n = int(area / cell**2)
    d = r.standard_normal((n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    sites = d * np.array([A, B, B])
    rad = r.lognormal(0.0, 0.3, n)
    dist, idx = cKDTree(sites).query(W_.reshape(-1, 3), k=7, workers=-1)
    w = np.sort(dist / rad[idx] / cell, axis=1)
    F1, F2 = w[:, 0].reshape(nu, nv), w[:, 1].reshape(nu, nv)
    h = (1.0 - np.exp(-((F2 - F1) / 0.3) ** 1.2)) + 0.28 * (1.0 - np.minimum(F1, 1.0) ** 2)
    return ((h - h.mean()) / h.std()).astype(np.float32)


_D1 = _relief()
_D2 = fbm((320, 400), 400 / (2 * np.pi * B), 0.3, 1.0, 2.2, 35)
_D3 = fbm((900, 1200), 1200 / (2 * np.pi * B), 0.015, 0.07, 1.6, 37)


def dimples(p):
    """The relief the spinning pressed into the shell, shared by shell and threads: from the fixed grid, in cm."""
    c = np.clip(p[..., 0] / A, -1, 1)
    u0 = np.arccos(c) / np.pi
    v0 = (np.arctan2(p[..., 2], p[..., 1]) % (2 * np.pi)) / (2 * np.pi)
    # cv2.remap takes fewer than 32768 rows, and there are more filaments than that: look up flattened to a square
    sh = u0.shape
    side = int(np.ceil(np.sqrt(u0.size)))
    pad = side * side - u0.size

    def look(g):
        nu, nv = g.shape
        uf = np.concatenate([(u0 * (nu - 1)).ravel(), np.zeros(pad)]).reshape(side, side).astype(np.float32)
        vf = np.concatenate([(v0 * nv).ravel(), np.zeros(pad)]).reshape(side, side).astype(np.float32)
        return cv2.remap(g, vf, uf, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).ravel()[: u0.size].reshape(sh)

    # heights in cm, estimates: the pillows about 0.1 mm proud of their creases
    return 0.0075 * look(_D1) + 0.005 * look(_D2) + 0.0035 * look(_D3)


def strands(n, ns, seed, lo, hi, loops, hmax, wmin, wmax, base_h=0.0):
    """Figure-of-eight waves on the ellipsoid. Each its own size, heading and height; vectorised over strands."""
    rng = np.random.default_rng(seed)
    # uniform-ish over the surface: rejection on the sphere is good enough
    d = rng.standard_normal((n, 3)).astype(np.float32)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    c = d * np.array([A, B, B], np.float32)
    nr = normals(c)
    # a heading: mostly around, some along
    ref = np.array([1.0, 0.0, 0.0], np.float32)
    e1 = np.cross(nr, ref)
    e1 /= np.linalg.norm(e1, axis=1, keepdims=True) + 1e-6
    e2 = np.cross(nr, e1)
    a = rng.normal(0, 0.9, n).astype(np.float32)
    h1 = np.cos(a)[:, None] * e1 + np.sin(a)[:, None] * e2
    h2 = -np.sin(a)[:, None] * e1 + np.cos(a)[:, None] * e2
    t = np.linspace(0, 1, ns, dtype=np.float32)[None, :]
    A8 = rng.uniform(lo, hi, n).astype(np.float32)[:, None]  # half-length of a figure 8
    B8 = A8 * rng.uniform(0.3, 0.72, n).astype(np.float32)[:, None]
    nl = rng.uniform(loops[0], loops[1], n).astype(np.float32)[:, None]
    ph = rng.uniform(0, 2 * np.pi, n).astype(np.float32)[:, None]
    # the phase speed wobbles, so that no two 8s are the same size
    k1, k2 = rng.uniform(0.08, 0.22, n).astype(np.float32)[:, None], rng.uniform(0, 6.28, n).astype(np.float32)[:, None]
    s = 2 * np.pi * nl * t + ph + 1.2 * k1 * np.sin(5.3 * t * nl + k2) * 6.28 / 6.28
    amp = 1.0 + 0.3 * np.sin(3.1 * t * nl + k2 * 1.7)
    drift = rng.uniform(0.6, 1.4, n).astype(np.float32)[:, None] * A8 * 2.1 * nl * (t - 0.5)
    lx = drift + A8 * amp * np.sin(s)
    ly = B8 * amp * np.sin(2 * s) + 0.4 * B8 * np.sin(0.7 * s + k2)
    p = c[:, None, :] + lx[..., None] * h1[:, None, :] + ly[..., None] * h2[:, None, :]
    # height: at their crossings the threads rest on one another; loose in the bellies of the loops
    hl = base_h + hmax * rng.uniform(0.02, 1.0, n).astype(np.float32)[:, None] ** 2.0 * (0.25 + 0.75 * np.abs(np.sin(s + 0.4))) * (0.75 + 0.25 * np.sin(1.9 * s + k2))
    q = project(p, hl)
    q = q + normals(q) * dimples(q)[..., None]
    # thread radius varies a little, and silk is a pair of brins: wider sometimes
    w = rng.uniform(wmin, wmax, n).astype(np.float32)[:, None] * np.ones((n, ns), np.float32)
    return q, w, rng.uniform(0.75, 1.0, n).astype(np.float32)


def floss(n, ns, seed, lmed, hmed, wmed, company=0.35, pfree=0.3):
    """Loose hairs: a walk of the heading over the shell. Long lazy arcs, the odd kink, each its own length, lift, width and brightness; about a third drift in small companies of near-parallel hairs."""
    r = np.random.default_rng(seed)
    d = r.standard_normal((n, 3)).astype(np.float32)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    head = r.uniform(0, 2 * np.pi, n).astype(np.float32)
    L = np.clip(r.lognormal(np.log(lmed), 0.65, n), 0.08, 2.2).astype(np.float32)
    lift = np.clip(r.lognormal(np.log(hmed), 0.8, n), 0.004, 0.2).astype(np.float32)
    wid = np.clip(r.lognormal(np.log(wmed), 0.32, n), 0.00018, 0.0011).astype(np.float32)
    bri = np.clip(r.lognormal(np.log(0.42), 0.6, n), 0.1, 1.0).astype(np.float32)
    free = r.random(n) < pfree
    # a company: this hair takes the start and the heading of an earlier one, a little off
    join = np.nonzero(r.random(n) < company)[0]
    join = join[join > 0]
    lead = (r.random(join.size) * join).astype(np.int64)
    d[join] = d[lead] + r.normal(0, 0.012, (join.size, 3)).astype(np.float32)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    head[join] = head[lead] + r.normal(0, 0.1, join.size).astype(np.float32)
    L[join] = L[lead] * r.uniform(0.75, 1.25, join.size).astype(np.float32)
    c = d * np.array([A, B, B], np.float32)
    nr = normals(c)
    e1 = np.cross(nr, np.array([1.0, 0.0, 0.0], np.float32))
    e1 /= np.linalg.norm(e1, axis=1, keepdims=True) + 1e-6
    e2 = np.cross(nr, e1)
    t = np.linspace(0, 1, ns, dtype=np.float32)
    # curvature against arc length: slow waves with an amplitude of their own, plus a kink or two
    amp = r.lognormal(np.log(1.1), 0.75, n).astype(np.float32)[:, None] / np.maximum(L, 0.2)[:, None]
    f1, p1, f2, p2 = r.uniform(0.5, 1.8, (n, 1)), r.uniform(0, 6.28, (n, 1)), r.uniform(2.0, 5.0, (n, 1)), r.uniform(0, 6.28, (n, 1))
    kap = amp * (np.sin(2 * np.pi * f1 * t + p1) + 0.45 * np.sin(2 * np.pi * f2 * t + p2))
    kt, kw, ka = r.uniform(0.1, 0.9, (n, 1)), r.uniform(0.012, 0.035, (n, 1)), r.normal(0, 1.5, (n, 1)) * (r.random((n, 1)) < 0.5)
    kap = kap + ka * np.exp(-(((t - kt) / kw) ** 2)) / (kw * 1.77) / 12.0
    ds = L[:, None] / (ns - 1)
    th = head[:, None] + np.cumsum(kap * ds * L[:, None], axis=1)
    lx = np.cumsum(np.cos(th) * ds, axis=1)
    ly = np.cumsum(np.sin(th) * ds, axis=1)
    p = c[:, None, :] + lx[..., None] * e1[:, None, :] + ly[..., None] * e2[:, None, :]
    prof = np.maximum(np.sin(np.pi * t**0.8), 0.0) ** 0.8
    prof = np.where(free[:, None], sstep(0.0, 0.55, t) * (0.7 + 0.3 * t), prof[None, :])
    hl = lift[:, None] * prof * (1.0 + 0.05 * np.sin(2 * np.pi * f1 * t + p1))
    q = project(p.astype(np.float32), hl.astype(np.float32))
    q = q + normals(q) * dimples(q)[..., None] * (1.0 - sstep(0.0, 0.06, hl))[..., None]
    w = wid[:, None] * (1.0 - np.where(free[:, None], 0.5 * sstep(0.7, 1.0, t), 0.0))
    # a brin's sheen comes and goes along it, as it twists
    sheen = np.clip(0.7 + 0.3 * np.sin(2 * np.pi * f2 * 1.3 * t + p2) + 0.2 * np.sin(2 * np.pi * f1 * 5.1 * t + p1), 0.25, 1.15)
    return q.astype(np.float32), w.astype(np.float32), (bri[:, None] * sheen).astype(np.float32)


def _resample(a, ns):
    """Along the second axis, linear."""
    x = np.linspace(0, a.shape[1] - 1, ns)
    i = np.minimum(x.astype(np.int32), a.shape[1] - 2)
    f = (x - i).astype(np.float32)
    f = f[:, None] if a.ndim == 3 else f
    return a[:, i] * (1 - f) + a[:, i + 1] * f


def main():
    q = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview")
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s34_canjian")
    os.makedirs(d, exist_ok=True)

    # --- camera first, the threads face it
    view = np.array([0.04, -1.0, -0.06])
    view = view / np.linalg.norm(view)
    apex_z = B * 0.99
    target = np.array([0.0, 0.0, apex_z - (0.5 - APEX) * H])
    cam = frame_camera(target, view, W, 15.0, aperture_mm=1.7, focus_point=[0.0, 0.0, apex_z - 0.02])
    C = np.array(cam["loc"], np.float32)

    # --- the shell
    nu, nv = int(1600 * dens) + 400, int(1800 * dens) + 400
    u = np.linspace(0.02, np.pi - 0.02, nu, dtype=np.float32)
    v = np.linspace(0, 2 * np.pi, nv, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing="ij")
    x, y, z = surf(U, V)
    grid = (nu, nv)
    px = nv / (2 * np.pi * B)
    dimple = up(_D1, nu, nv)
    fine = cv2.resize(fbm((nu // 2, nv // 2), px / 2, 0.01, 0.08, 1.4, 37), (nv, nu), interpolation=cv2.INTER_LINEAR)
    pp = np.stack([x, y, z], -1)
    nrm = normals(pp)
    pp = pp + nrm * (dimples(pp) - 0.004)[..., None]
    # no cloud of noise: thick on the pillows, thinner in the creases and at the waist, and a little of the fine felt
    waist_ = np.exp(-((np.cos(U) / 0.34) ** 2))
    tau = (0.74 - 0.12 * waist_ + 0.06 * fine + 0.1 * dimple).clip(0.3, 2.0)
    trans = np.broadcast_to(color([0.85, 0.82, 0.76]), (nu, nv, 3)).astype(np.float32)
    scat = np.ones((nu, nv, 3), np.float32) * color([1.0, 0.93, 0.79]) * (0.95 + 0.05 * np.clip(fine, -1, 1))[..., None]
    np1 = os.path.join(d, f"mesh.{q}.npz")
    np.savez(np1, P=rot(pp[..., 0], pp[..., 1], pp[..., 2]).astype(np.float32), tau=tau.astype(np.float32), scat=np.clip(scat, 0, 1).astype(np.float32), trans=trans, mask=np.ones_like(tau, np.float32))

    # --- the pupa: a dark body floating inside
    us, vs = np.meshgrid(np.linspace(0, np.pi, 300, dtype=np.float32), np.linspace(0, 2 * np.pi, 300, dtype=np.float32), indexing="ij")
    ppx, ppy, ppz = 1.12 * np.cos(us) + 0.1, 0.56 * np.sin(us) * np.cos(vs) + 0.08, 0.60 * np.sin(us) * np.sin(vs) - 0.1
    np2 = os.path.join(d, f"pupa.{q}.npz")
    np.savez(np2, P=rot(ppx, ppy, ppz).astype(np.float32))

    # --- the silk
    k = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    q1, w1, b1 = strands(int(36000 * k), 110, 340, 0.05, 0.2, (2.0, 4.0), 0.016, 0.0004, 0.0008)
    q2, w2, b2 = strands(int(6000 * k), 110, 341, 0.1, 0.3, (1.0, 2.6), 0.045, 0.00032, 0.0006, base_h=0.01)
    q3, w3, b3 = floss(int(3200 * k), 150, 342, 0.24, 0.022, 0.0003, pfree=0.55)  # the short felt of hairs that makes a soft edge
    q4, w4, b4 = floss(int(260 * k), 150, 343, 0.8, 0.075, 0.00036, company=0.45, pfree=0.8)  # the few long ones that stand off
    # the 8s are compact silk: the same sheen all along, with a strand-to-strand spread
    Q = np.concatenate([q1, q2, _resample(q3, 110), _resample(q4, 110)])
    Wd = np.concatenate([w1, w2, _resample(w3, 110), _resample(w4, 110)])
    Br = np.concatenate([np.ones((len(q1) + len(q2), 110), np.float32) * np.concatenate([b1, b2])[:, None] * 0.7, _resample(b3, 110), _resample(b4, 110)])
    Q = rot(Q[..., 0], Q[..., 1], Q[..., 2]).astype(np.float32)
    # drop back-facing filaments: nobody sees them except as what the shell already gives
    fr = np.mean(Q[..., 1], axis=1) < 0.25
    Q, Wd, Br = Q[fr], Wd[fr], Br[fr]
    col = np.ones(Q.shape, np.float32) * color([1.0, 0.94, 0.82]) * Br[:, :, None]
    Pr, ar = ribbons(Q, Wd, C, {"col": col})
    np3 = os.path.join(d, f"silk.{q}.npz")
    np.savez(np3, P=Pr, **ar)
    print("filaments", Q.shape, Pr.shape)

    shell = {"kind": "sheet", "k_tau": 1.0, "front": 0.32, "k_gloss": 0.04, "rough": 0.5, "cos_min": 0.25}
    silk = {"kind": "fibre", "strand_k": 3, "front": 0.45, "k_gloss": 0.35, "rough": 0.3, "ior": 1.55}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "shell", "npz": np1, "shader_py": SHEETS, "params": shell},
            {"name": "pupa", "npz": np2, "shader_py": SHEETS, "params": {"kind": "pbr", "map": {"Base Color": [0.06, 0.03, 0.015], "Roughness": 0.6}}},
            {"name": "silk", "npz": np3, "shader_py": SHEETS, "params": silk},
        ],
        "lights": [
            {"name": "sun", "loc": [-3, 22, 6], "target": [0, 0, 0.2], "size": [5, 5], "watts": 30000, "rgb": [1.0, 0.86, 0.68]},
            {"name": "rake", "loc": [-16, -3, 9], "target": [0, 0, 0.4], "size": [4, 6], "watts": 12000, "rgb": [1.0, 0.93, 0.82]},
            {"name": "fill", "loc": [8, -18, -3], "target": [0, 0, 0], "size": [20, 20], "watts": 900, "rgb": [0.95, 0.9, 1.0]},
        ],
        "world": [0.0005, 0.0005, 0.0007],
        "bounces": 10,
        "diffuse_bounces": 4,
        "glossy_bounces": 2,
        "transmission_bounces": 8,
        "spp": {"preview": 96, "mid": 160, "final": 384},
    }
    look = {"exposure": 0.95, "wb": [1.03, 1.0, 0.93], "contrast": 1.3, "saturation": 1.0, "black": 0.002, "grain": 1.2, "sharpen": 0.2, "halation": 0.03, "glare": 0.002}
    shoot("s34_canjian", scene, q, develop=look)


main()
