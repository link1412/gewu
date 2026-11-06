"""Shot 74: a boiled tangyuan that has split at the shoulder, a tongue of black sesame filling running down its side. This version is a still, for the material: it has to look hot and good to eat.

    python3 -I v2/stills/s74_tangyuan.py [preview|mid|final] [TAG] ['{"k": v}']       the skin is a real medium. out/v2/s74_tangyuan/TAG.jpg. The final's default tag is cand; never writes final.*

The appearance target is commercial food imagery (real photographs are no use here); reference only, no pixels of it are used. What it asks for:
- the frame: the ball's whole shoulder against the air, the opening near its outline, so the tongue's thickness shows in profile and its nose stays in the picture. A fluid is read by its outline: a neck and a round nose (an independent review of the earlier version, which had a wide sheet running at the camera, out of frame).
- the skin: smooth, nearly a sphere; the stickiness is in the shading. One real medium, thinning a little towards the surface, with the dark core inside it showing through as a soft shadow, and two lobes of gloss, sharp and wide. A side-rear key gives it a real fall of light. The roughness and a very low ripple in the surface break up the long highlights.
- the torn edge: a thick closed solid of the same gel, swept along the opening's rim and hanging over the filling, which a height field cannot do.
- the filling: a swept surface on the ball, centre line plus width and thickness curves, so it can overhang its foot a little, which a height field cannot. Its shape is DRAWN, not solved: the viscous current's look (thin neck, thick nose, crests across the run) is put in by hand. Dark grey-brown paste of ground seed, not black; fine grains stretched along the run; oil over it, seen as wide soft reflections with a few sharp ones.
- the air: no canvas, no texture. A far warm light out of focus, and the steam, added afterwards (s74_steam.py).

One grid makes the whole ball: an azimuthal projection about the opening, even across the frame and squeezed behind it, its border all on the far pole. So it is watertight, which a medium needs.

Stand-ins and estimates, none measured: size 3.6 cm; every sigma, by eye; n 1.36 of a wet starch gel; skin thickness; all colours; the shape of the opening and of the tongue (drawn); the oil's n, 1.55 by eye (edible fats are about 1.47, general knowledge). Not done: motion.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
from kit import fbm, sstep

NAME = "s74_tangyuan"
HERE = os.path.dirname(os.path.abspath(__file__))
SHP = os.path.join(HERE, "s74_shader.py")
D = os.path.join(kit.OUT, NAME)

P0 = {
    "R": 1.8, "W": 4.2, "E": 14.0, "dist": 22.0, "aperture": 4.0, "apex_y": 0.1, "ball_x": 0.36, "k": 3.0, "s0": 0.85,
    # the opening, as a fraction of the frame: on the shoulder, near the outline
    "open_x": 0.54, "open_y": 0.42, "slit_tilt": 12.0, "slit_L": 0.56, "slit_w": 0.34,
    # the tongue, cm along the run from the opening's centre: half width and thickness at those places
    "run_s": [-0.45, 0.0, 0.14, 0.3, 0.55, 0.85, 1.1, 1.35],
    "run_w": [0.46, 0.46, 0.41, 0.34, 0.3, 0.32, 0.38, 0.42],
    "run_h": [0.14, 0.19, 0.17, 0.115, 0.09, 0.1, 0.125, 0.135],
    "wander": 0.06, "skew": 0.18, "crest": 0.05, "crest_lam": 0.5,
    "th": 0.26, "sigma_s": [17.0, 18.0, 19.5], "clear_k": 0.3, "clear": [0.06, 0.0], "haze": 0.3, "haze_rough": 0.28, "sigma_a": [0.01, 0.05, 0.16], "g": 0.6, "ior": 1.36,
    "rough": 0.055, "rough_var": 0.012, "ripple": 0.0008, "sigma_lip": [12.0, 12.8, 14.0], "fold": 0.2,
    "paste": [0.021, 0.0165, 0.0145], "oil_rough": 0.075, "oil_rough_var": 0.035, "bead_density": 9000.0, "bead_oil": 0.3,
    # lights: irradiance on a surface facing them, so that a change of distance does not change the picture
    "E_key": 7.5, "E_kick": 2.6, "E_front": 1.3, "E_back": 5.0,
    "L_box": 30.0, "L_tongue": 13.0, "L_ridge": 30.0, "L_spark": 22.0, "L_strip": 3.0, "L_rim": 8.0,
    "exposure": 0.12,
}
GRID = {"preview": 1024, "mid": 2048, "final": 3072}
SWEEP = {"preview": (800, 280), "mid": (1600, 460), "final": (2400, 680)}
N0 = 1536  # the opening is made on this grid and resized, so that it does not change with the quality


def grid_dirs(N, c, e1, e2, k, s0):
    """Directions on the ball. Row 0 is at the top, so grid_mesh's faces look outwards."""
    u = np.linspace(-1.0, 1.0, N, dtype=np.float32)
    v = np.linspace(1.0, -1.0, N, dtype=np.float32)
    U, V = np.meshgrid(u, v)
    s = np.maximum(np.abs(U), np.abs(V))
    r = np.maximum(np.hypot(U, V), 1e-6)
    t = sstep(s0, 1.0, s)
    scale = k * (1 - t) + (np.pi / r) * t
    a, b = scale * U, scale * V
    rho = np.maximum(np.hypot(a, b), 1e-6)
    d = np.cos(rho)[..., None] * c + (np.sin(rho) / rho)[..., None] * (a[..., None] * e1 + b[..., None] * e2)
    return d.astype(np.float32), a, b, s


def normals(P, outward):
    du = np.gradient(P, axis=1)
    dv = np.gradient(P, axis=0)
    n = np.cross(du, dv)
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)
    return n * np.sign((n * outward).sum(-1, keepdims=True) + 1e-12)


def r_ball(p, d):
    """The ball's radius in direction d: a very little flattened by its own weight."""
    return p["R"] * (1.0 + 0.008 * (1.0 - 2.0 * d[..., 2] ** 2))


def opening(p, g):
    """The opening's edge distance e, on the fixed grid N0. Its long axis lies across the slope."""
    R, k = p["R"], p["k"]
    d, a, b, s = grid_dirs(N0, g["c"], g["e1"], g["e2"], k, p["s0"])
    pxcm = (N0 - 1) / (k * R * 2.0)
    x, y = a * R, b * R
    gx, gy = -g["e1"][2], -g["e2"][2]  # gravity along the surface at the opening
    tilt = np.radians(p["slit_tilt"])
    upx, upy = -gx / np.hypot(gx, gy), -gy / np.hypot(gx, gy)
    upx, upy = upx * np.cos(tilt) - upy * np.sin(tilt), upx * np.sin(tilt) + upy * np.cos(tilt)
    yr = x * upx + y * upy + 0.035 * fbm((N0, N0), pxcm, 0.25, 1.0, 2.6, 745)
    xr = x * upy - y * upx
    L, ws = p["slit_L"], p["slit_w"]
    w = ws * np.maximum(1.0 - (xr / L) ** 2, 0.0) ** 0.6
    e = np.where(np.abs(xr) < L, np.abs(yr) - w, np.hypot(np.abs(xr) - L, yr))
    return (e + 0.012 * fbm((N0, N0), pxcm, 0.12, 0.45, 2.8, 746)).astype(np.float32), (upx, upy)


def noise1d(n, lam, seed):
    """Periodic noise along a closed curve, n samples, wavelength lam in samples, unit variance."""
    rng = np.random.default_rng(seed)
    f = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * np.exp(-((np.fft.rfftfreq(n, 1.0) * lam) ** 2)), n)
    return ((f - f.mean()) / (f.std() + 1e-9)).astype(np.float32)


def lip(p, g, e_open, up, r_lookup, N, path):
    """The torn edge: a thick closed solid swept along the opening's rim, rooted in the skin outside it and hanging over the filling, most on the upper side. Thick, and as milky as the skin: only its very rim goes clear. Its inner edge is wavy, as a torn gel's is."""
    R, c, e1, e2, k = p["R"], g["c"], g["e1"], g["e2"], p["k"]
    cnt, _ = cv2.findContours(e_open.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cc = max(cnt, key=len)[:, 0, :].astype(np.float64)
    xy = np.stack([(cc[:, 0] / (N - 1) * 2 - 1) * k * R, (1 - cc[:, 1] / (N - 1) * 2) * k * R], -1)
    seg = np.hypot(*(np.roll(xy, -1, 0) - xy).T)
    L = float(seg.sum())
    nt = int(L / 0.004)
    t = np.concatenate([[0.0], np.cumsum(seg)])
    tq = np.linspace(0, L, nt, endpoint=False)
    xy = np.stack([np.interp(tq, t, np.concatenate([xy[:, i], xy[:1, i]])) for i in (0, 1)], -1)
    fk = np.fft.rfftfreq(nt, L / nt)
    xy = np.stack([np.fft.irfft(np.fft.rfft(xy[:, i]) * np.exp(-((fk * 0.018) ** 2) * 2), nt) for i in (0, 1)], -1)
    tang = np.roll(xy, -1, 0) - np.roll(xy, 1, 0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    area = 0.5 * np.sum(xy[:, 0] * np.roll(xy[:, 1], -1) - np.roll(xy[:, 0], -1) * xy[:, 1])
    inw = np.stack([-tang[:, 1], tang[:, 0]], -1) * (1.0 if area > 0 else -1.0)
    yr = xy[:, 0] * up[0] + xy[:, 1] * up[1]
    upper = sstep(-0.4, 0.6, yr / p["slit_w"])  # 0 on the lower lip, which the filling has pushed flat; 1 on the upper, which hangs
    lam = lambda cm: cm / (L / nt)
    wf = (0.04 + 0.09 * upper) * (1.0 + 0.24 * noise1d(nt, lam(0.34), 761) + 0.08 * noise1d(nt, lam(0.16), 762))
    wf = np.maximum(wf, 0.03)
    lift = 0.012 + 0.03 * upper * (1.0 + 0.3 * noise1d(nt, lam(0.5), 763))
    nq = 34
    q = np.linspace(0.0, 1.0, nq, dtype=np.float32)[None, :]
    I = wf[:, None] * (-0.9 + 1.9 * q)
    Z = -0.012 * (1 - q) ** 2 + lift[:, None] * np.sin(np.pi * 0.7 * q) - 0.012 * upper[:, None] * q**3
    Th = ((0.03 + 0.03 * upper[:, None]) * np.sqrt(np.maximum(1.0 - q**4, 0.0)) + 0.003) * sstep(0.0, 0.45, q)
    x = xy[:, 0, None] + I * inw[:, 0, None]
    y = xy[:, 1, None] + I * inw[:, 1, None]
    rr = r_lookup(x, y)
    a, b = x / R, y / R
    rho = np.maximum(np.hypot(a, b), 1e-6)
    d = np.cos(rho)[..., None] * c + (np.sin(rho) / rho)[..., None] * (a[..., None] * e1 + b[..., None] * e2)
    t_ = d * (rr + Z + Th * 0.5)[..., None]
    b_ = d * (rr + Z - Th * 0.5)[..., None]
    P = np.concatenate([t_, b_[:, ::-1], t_[:, :1]], 1)
    P = np.concatenate([P, P[:1]], 0).astype(np.float32)
    i, j = nt // 2, nq // 2
    if np.dot(np.cross(P[i + 1, j] - P[i, j], P[i, j + 1] - P[i, j]), d[i, j]) < 0:
        P = P[:, ::-1]
    rough = np.full(P.shape[:2], p["rough"], np.float32)
    pool = np.ones(P.shape, np.float32) * np.array([1.0, 0.985, 0.96], np.float32)
    np.savez(path, P=P, rough=rough, pool=pool)
    return path


def curve(xp, s, fp, sm):
    """fp at the knots xp, read at s and smoothed along it (sm in samples)."""
    f = np.interp(s, xp, fp).astype(np.float32)
    pad = int(4 * sm) + 1
    f = np.concatenate([np.full(pad, f[0]), f, np.full(pad, f[-1])]).reshape(-1, 1)
    return cv2.GaussianBlur(f, (1, 0), 0, sigmaY=sm)[pad:-pad, 0]


def seed_texture(p):
    """The paste, flat, in cm along the run and across it: its colour and its relief. Grains stretched along the run, a few flecks of hull. Colour is mostly the paste's; the grains are small and low in contrast."""
    res = 1.0 / 0.0007  # pixels per cm
    s0, s1, l0, l1 = -0.4, 2.0, -0.7, 0.7
    nl, ns = int((l1 - l0) * res), int((s1 - s0) * res)
    rng = np.random.default_rng(753)
    body = np.array(p["paste"], np.float32)
    col = np.broadcast_to(body, (nl, ns, 3)).copy()
    rel = np.zeros((nl, ns), np.float32)
    for _ in range(int((s1 - s0) * (l1 - l0) * p["bead_density"])):
        cx, cy = int(rng.uniform(0, ns)), int(rng.uniform(0, nl))
        hull = rng.uniform() < 0.025
        stretch = rng.uniform(1.2, 2.6)
        ang = float(rng.normal(0.0, 12.0))
        if hull:
            la, lb = rng.uniform(0.006, 0.016), rng.uniform(0.002, 0.004)
            sh = np.array([0.12, 0.085, 0.055]) * float(rng.uniform(0.5, 1.0))
            cv2.ellipse(col, (cx, cy), (max(int(la * res), 1), max(int(lb * res), 1)), ang, 0, 360, sh.tolist(), -1, cv2.LINE_AA)
            continue
        r_ = min(0.003 * (1.0 - rng.uniform(0.0, 0.95)) ** -0.42, 0.008)
        rp = max(int(r_ * res), 1)
        shade = body * float(np.clip(rng.lognormal(-0.25, 0.5), 0.25, 1.9))
        cv2.ellipse(col, (cx, cy), (max(int(rp * stretch), 1), rp), ang, 0, 360, shade.tolist(), -1, cv2.LINE_AA)
        cv2.ellipse(rel, (cx, cy), (max(int(rp * stretch), 1), rp), ang, 0, 360, float(r_ * rng.uniform(0.25, 0.6)), -1, cv2.LINE_AA)
    rel = cv2.GaussianBlur(rel, (0, 0), 1.2)
    col = cv2.GaussianBlur(col, (0, 0), 0.8)
    # the paste is not even: darker clots, and long faint streaks where the run has drawn it out
    pc = res
    clot = cv2.resize(fbm((nl // 4, ns // 8), pc / 4.0, 0.06, 0.3, 2.6, 758), (ns, nl), interpolation=cv2.INTER_CUBIC)
    streak = cv2.resize(fbm((nl // 4, ns // 32), pc / 4.0, 0.02, 0.12, 2.4, 759), (ns, nl), interpolation=cv2.INTER_CUBIC)
    col = col * np.exp(-0.55 * sstep(0.5, 1.7, clot) + 0.14 * streak)[..., None]
    fine = fbm((nl, ns), pc, 0.002, 0.012, 1.4, 754)
    col = col * np.exp(0.14 * fine)[..., None]
    return {"col": col.astype(np.float32), "rel": rel + 0.0002 * fine.astype(np.float32), "s0": s0, "l0": l0, "res": res}


def tongue(p, g, q, path):
    """The filling: a swept surface. u along the run, phi round the section from one foot over the top to the other."""
    R = p["R"]
    c, tg = g["c"], g["t_run"]
    side = np.cross(c, tg)
    nu, nphi = SWEEP[q]
    s_end = p["run_s"][-1]
    s_start = p["run_s"][0]
    u = np.linspace(0.0, 0.9992, nu, dtype=np.float32)
    s = s_end - (s_end - s_start) * (1.0 - u) ** 2  # samples crowd towards the tip, where the section closes as a square root
    fine_n = 8 * nu
    sm = 0.05 * fine_n / (s_end - s_start)
    ds_uni = np.linspace(s_start, s_end, fine_n, dtype=np.float64)
    h_u = curve(p["run_s"], ds_uni, p["run_h"], sm)
    w_u = curve(p["run_s"], ds_uni, p["run_w"], sm)
    # they vary a little, unevenly, and differently on each side
    rng = np.random.default_rng(770)
    wave = lambda lam, ph: np.sin(2 * np.pi * ds_uni / lam + ph)
    wr = w_u * (1.0 + 0.05 * wave(0.71, 0.4) + 0.025 * wave(0.33, 2.0))
    wl = w_u * (1.0 + 0.07 * wave(0.83, 3.1) + 0.03 * wave(0.29, 0.7))
    # a tip: round in plan, and thick right up to it
    nose = float(w_u[-1]) * 1.5
    tip = np.clip((ds_uni - (s_end - nose)) / nose, 0.0, 1.0)
    close = np.sqrt(np.maximum(1.0 - tip**2, 0.0))
    wr, wl = wr * close, wl * close
    h_ = h_u * close**0.7
    to_s = lambda f: np.interp(s, ds_uni, f).astype(np.float32)
    wr, wl, h_ = to_s(wr), to_s(wl), to_s(h_)
    # the centre line: down the slope, wandering across it
    mid = p["wander"] * (np.sin(s / 0.62 + 0.8) + 0.45 * np.sin(s / 0.27 + 2.1)) * sstep(0.1, 0.9, s)
    arc = s / R
    Dir = np.cos(arc)[:, None] * c + np.sin(arc)[:, None] * tg + (mid / R)[:, None] * side
    Dir /= np.linalg.norm(Dir, axis=1, keepdims=True)
    T = np.gradient(Dir, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    B = np.cross(Dir, T)
    # the section
    phi = np.linspace(0.0, np.pi, nphi, dtype=np.float32)
    cs, sn = np.cos(phi)[None, :], np.sin(phi)[None, :]
    zprof = np.maximum(sn, 0.0) ** 0.95
    # a bead's edge: it stands up and leans out over its foot a little
    lean = cs + 0.5 * p["skew"] * np.sin(2.0 * phi)[None, :]
    wid = np.where(lean >= 0.0, wr[:, None], wl[:, None])
    L = lean * wid  # cm across
    # in the opening it starts below the lip
    z_off = -0.17 * sstep(0.5, -0.22, s)[:, None] - 0.008
    # across the run: crests, bowed downstream, travelling; and long faint flow lines. They fade at the foot
    lat = L / np.maximum(wid, 1e-3)
    phase = 2 * np.pi * (s[:, None] - 0.16 * lat**2) / p["crest_lam"]
    crest = np.sin(phase + 0.9) + 0.5 * np.sin(1.73 * phase + 2.2)
    amp = p["crest"] * sstep(0.3, 0.7, s)[:, None] * sstep(0.0, 0.5, zprof)
    lines = cv2.resize(fbm((nu // 3, nu), 1.0, nu / 11.0, nu / 3.0, 3.0, 771), (nphi, nu), interpolation=cv2.INTER_CUBIC) * sstep(0.0, 0.5, zprof) * sstep(0.0, 0.3, s)[:, None]
    H = h_[:, None] * (zprof * (1.0 + amp * crest) + p["fold"] * lines)
    # the paste's grain, projected from above
    tx = seed_texture(p)
    st = s[:, None] * np.ones_like(L) + 0.18 * lat**2 * s[:, None]
    mx = ((st - tx["s0"]) * tx["res"]).astype(np.float32)
    my = ((L - tx["l0"]) * tx["res"]).astype(np.float32)
    rel = cv2.remap(tx["rel"], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    col = cv2.remap(tx["col"], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # world positions: the oil smooths the relief for its own lobe; the paste's normal sees all of it
    d_ = (R * Dir[:, None, :] + L[..., None] * B[:, None, :])
    d_ /= np.linalg.norm(d_, axis=-1, keepdims=True)
    r_ = r_ball(p, d_)
    base = r_ + z_off + H
    P = d_ * (base + p["bead_oil"] * rel)[..., None]
    nb = normals(d_ * (base + 0.5 * rel)[..., None], d_) * 0.5 + 0.5
    # the oil's sharpness varies: wetter in places
    wet = cv2.resize(fbm((nu // 8 + 1, nphi // 4 + 1), 1.0, 6.0, 30.0, 2.6, 772), (nphi, nu), interpolation=cv2.INTER_CUBIC)
    roil = np.clip(p["oil_rough"] + p["oil_rough_var"] * wet, 0.05, 0.32)
    rb = np.clip(0.45 + 0.08 * wet, 0.25, 0.7)
    idx = np.arange(nu * nphi).reshape(nu, nphi)
    a0, a1, a2, a3 = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    # faces outwards
    m, n_ = nu // 2, nphi // 2
    if np.dot(np.cross(P[m + 1, n_] - P[m, n_], P[m, n_ + 1] - P[m, n_]), d_[m, n_]) < 0:
        a1, a3 = a3, a1
    F = np.concatenate([np.stack([a0, a1, a2], -1), np.stack([a0, a2, a3], -1)]).astype(np.int32)
    f = lambda a: a.reshape(-1, a.shape[-1]).astype(np.float32) if a.ndim == 3 else a.ravel().astype(np.float32)
    ones = np.ones((nu * nphi,), np.float32)
    np.savez(path, V=f(P), F=F, col=f(col), rb=f(rb), roil=f(roil), alpha=ones, tint=np.ones((nu * nphi, 3), np.float32), nb=f(nb))
    # its footprint on the ball, for the stain it leaves there
    foot = np.concatenate([d_[:, 0], d_[::-1, -1]])
    g["mid"] = d_[int(nu * 0.62), nphi // 2] * (R + 0.1)
    return foot, nu * nphi


def build(p, N, q):
    os.makedirs(D, exist_ok=True)
    R, k = p["R"], p["k"]
    E = np.radians(p["E"])
    W, H = p["W"], p["W"] * 9.0 / 16.0
    view = np.array([0.0, -np.cos(E), np.sin(E)])  # from the ball to the camera
    top = np.array([0.0, np.sin(E), np.cos(E)])  # the apex of the outline, seen from the camera
    right = np.array([1.0, 0.0, 0.0])
    yo_t = R - (0.5 - p["apex_y"]) * H
    target = yo_t * top + (0.5 - p["ball_x"]) * W * right

    def on_ball(fx, fy):
        """The ball's normal at this fraction of the frame."""
        dx = (fx - p["ball_x"]) * W
        yo = yo_t - (fy - 0.5) * H
        return (dx * right + yo * top + np.sqrt(max(R * R - dx * dx - yo * yo, 0.0)) * view) / R

    c = on_ball(p["open_x"], p["open_y"])
    e1 = right - np.dot(right, c) * c
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(c, e1)
    # down the slope at the opening
    t_run = np.array([0.0, 0.0, -1.0]) + c[2] * c
    t_run /= np.linalg.norm(t_run)
    g = dict(view=view, top=top, right=right, target=target, c=c, e1=e1, e2=e2, t_run=t_run, R=R, on_ball=on_ball)
    with open(os.path.join(D, "frame.json"), "w") as f:
        json.dump({"cx": p["ball_x"], "cy": 0.5 + yo_t / H, "r": R / W}, f)  # for the steam's matte: x and r in frame widths, y in frame heights
    d, a, b, s = grid_dirs(N, c, e1, e2, k, p["s0"])
    pxcm = (N - 1) / (k * R * 2.0)
    win = sstep(1.0, 0.84, s)
    shape = (N, N)

    # --- the ball: smooth and nearly a sphere, with a ripple far too low to read as anything but a wet surface's unevenness
    r0 = r_ball(p, d)
    cm0 = N0 / (2 * k * R)
    lump = cv2.resize(0.004 * fbm((N0, N0), cm0, 1.5, 4.0, 3.4, 741), shape, interpolation=cv2.INTER_CUBIC)
    ripple = cv2.resize(p["ripple"] * fbm((N0, N0), cm0, 0.08, 0.3, 2.8, 742), shape, interpolation=cv2.INTER_CUBIC)
    r_s = r0 + win * (lump + ripple)

    # --- the opening: the skin rolls down into it
    e0, up = opening(p, g)
    # one opening: any other speck the noise made is closed
    n_, lab, st_, _ = cv2.connectedComponentsWithStats((e0 < 0.0).astype(np.uint8))
    e0 = np.where((lab > 0) & (lab != 1 + int(np.argmax(st_[1:, cv2.CC_STAT_AREA]))), 0.02, e0).astype(np.float32)
    e = cv2.GaussianBlur(cv2.resize(e0, shape, interpolation=cv2.INTER_LINEAR), (0, 0), 0.004 * pxcm)
    roll = 0.3 * sstep(0.05, -0.05, e) ** 1.4
    lip_ = 0.014 * np.exp(-(((e - 0.05) / 0.07) ** 2)) + 0.012 * np.exp(-((np.maximum(e, 0.0) / 0.3) ** 2))
    r_skin = r_s + win * (lip_ - roll)

    # --- the core: the skin thins towards the opening; inside the opening it steps back out of the way
    th = p["th"] + cv2.resize(0.06 * fbm((N0, N0), cm0, 0.5, 1.6, 3.0, 749), shape, interpolation=cv2.INTER_CUBIC)
    th = th * (1.0 - 0.5 * np.exp(-((np.maximum(e, 0.0) / 0.3) ** 2)))
    th = np.where(e < 0.0, 0.42, th)
    th = cv2.GaussianBlur(th, (0, 0), 0.02 * pxcm)
    r_core = r_s - th

    # --- the filling
    g["ff"] = os.path.join(D, f"tongue_{q}.npz")
    foot, nv = tongue(p, g, q, g["ff"])

    # --- what the filling leaves on the skin: where it has lain, a thin grey smear; beyond that a little oil, in patches. Both as the tint of the surface
    rho = np.arccos(np.clip(foot @ c, -1, 1))
    k_ = rho / np.maximum(np.sin(rho), 1e-6)
    fx = (foot @ e1) * k_ / k
    fy = (foot @ e2) * k_ / k
    poly = np.stack([(fx + 1) * 0.5 * (N - 1), (1 - fy) * 0.5 * (N - 1)], -1).astype(np.int32)
    mask = np.zeros(shape, np.uint8)
    cv2.fillPoly(mask, [poly], 1)
    mask = mask | (e < 0.0).astype(np.uint8)
    dto = cv2.distanceTransform(1 - mask, cv2.DIST_L2, 5) / pxcm
    patch = sstep(-0.6, 0.9, cv2.resize(fbm((N0, N0), cm0, 0.08, 0.4, 2.8, 752), shape, interpolation=cv2.INTER_CUBIC))
    smear = np.exp(-dto / 0.022) * (0.35 + 0.65 * patch)
    oil = np.exp(-dto / 0.09) * patch * 0.5
    grey = np.array([0.5, 0.45, 0.42], np.float32)
    amber = np.array([0.93, 0.8, 0.58], np.float32)
    pool = np.ones(shape + (3,), np.float32) * np.array([1.0, 0.985, 0.96], np.float32)
    pool = pool * (1.0 - smear[..., None] * (1.0 - grey)) * (1.0 - oil[..., None] * (1.0 - amber))

    # --- meshes
    P = (d * r_skin[..., None]).astype(np.float32)
    # the highlight's sharpness varies slowly, so a long highlight breaks up instead of running like glaze
    rough = np.clip(p["rough"] + p["rough_var"] * cv2.resize(fbm((N0, N0), cm0, 0.3, 1.2, 2.8, 755), shape, interpolation=cv2.INTER_CUBIC), 0.04, 0.2)
    g["fs"] = os.path.join(D, f"skin_{N}.npz")
    np.savez(g["fs"], P=P, rough=rough.astype(np.float32), pool=pool.astype(np.float32))

    st = max(N // 1024, 1)
    g["fc"] = os.path.join(D, f"core_{N}.npz")
    Pc = (d * r_core[..., None])[::st, ::st].astype(np.float32)
    np.savez(g["fc"], P=Pc, col=np.ones(Pc.shape, np.float32) * np.array([0.016, 0.013, 0.011], np.float32))
    r_smooth = cv2.GaussianBlur(r_s + win * lip_, (0, 0), 0.02 * pxcm)

    def r_lookup(xq, yq):
        return cv2.remap(r_smooth, ((xq / (k * R) + 1.0) * 0.5 * (N - 1)).astype(np.float32), ((1.0 - yq / (k * R)) * 0.5 * (N - 1)).astype(np.float32), cv2.INTER_LINEAR)

    g["fl"] = lip(p, g, e < 0.0, up, r_lookup, N, os.path.join(D, f"lip_{N}.npz"))
    print(f"[s74] grid {N}, {1e4 / pxcm:.0f} um a node; tongue {nv / 1e6:.2f} M vertices", flush=True)
    return g


def world(p, g, path):
    """What the reflections see, in world directions. Seen by gloss only (kit: env, diffuse off)."""
    h, w = 1024, 2048
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    E = np.zeros((h, w, 3), np.float32) + np.array([0.05, 0.045, 0.04], np.float32)

    def box(rdir, wx, wy, L, rgb, soft=0.8):
        r = np.array(rdir, np.float32)
        r /= np.linalg.norm(r)
        t1 = np.cross(r, [0.0, 0.0, 1.0])
        t1 /= np.linalg.norm(t1)
        t2 = np.cross(t1, r)
        dr = d @ r
        ax = np.degrees(np.arctan2(d @ t1.astype(np.float32), dr))
        ay = np.degrees(np.arctan2(d @ t2.astype(np.float32), dr))
        return (L * sstep(1.0, soft, np.abs(ax) / wx) * sstep(1.0, soft, np.abs(ay) / wy) * (dr > 0))[..., None] * np.array(rgb, np.float32)

    def mirror(fx, fy):
        n = g["on_ball"](fx, fy)
        return 2 * np.dot(n, g["view"]) * n - g["view"]

    E = E + box(mirror(0.22, 0.26), 15.0, 8.0, p["L_box"], [1.0, 0.95, 0.86], soft=0.55)  # a big window on the ball's lit side
    E = E + box(mirror(0.585, 0.7), 12.0, 18.0, p["L_tongue"], [1.0, 0.95, 0.88], soft=0.2)  # lies wide and grey along the tongue
    E = E + box(mirror(0.56, 0.68), 4.0, 20.0, p["L_ridge"], [1.0, 0.95, 0.88], soft=0.5)  # along the tongue's back
    E = E + box(mirror(0.5, 0.3), 5.0, 4.0, p["L_spark"], [1.0, 0.93, 0.8], soft=0.6)
    E = E + box(mirror(0.2, 0.8), 5.0, 24.0, p["L_strip"], [1.0, 0.9, 0.78], soft=0.5)
    E = E + box(-g["view"] + 0.25 * g["top"], 70.0, 22.0, p["L_rim"], [1.0, 0.88, 0.72], soft=0.4)
    np.save(path, E.astype(np.float32))
    return path


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    tag = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else ("cand" if q == "final" else None)
    p = dict(P0)
    if len(sys.argv) > 3:
        p.update(json.loads(sys.argv[3]))
    g = build(p, GRID[q], q)
    cam = kit.frame_camera(g["target"], g["view"], p["W"], p["dist"], aperture_mm=p["aperture"], focus_point=g["mid"])
    env = world(p, g, os.path.join(D, "env.npy"))

    def lamp(name, offset, irradiance, size, rgb):
        loc = np.array(offset, float)
        return {"name": name, "loc": loc.tolist(), "target": [0.0, 0.0, 0.0], "size": size, "watts": float(irradiance * np.pi * np.dot(loc, loc)), "rgb": rgb, "hide_in_gloss": True}

    skin_base = {"kind": "skin", "sigma_s": p["sigma_s"], "sigma_a": p["sigma_a"], "g": p["g"], "ior": p["ior"], "haze": p["haze"], "haze_rough": p["haze_rough"]}
    skin = {**skin_base, "clear_k": p["clear_k"], "clear_r": [p["R"] - p["clear"][0], p["R"] - p["clear"][1]]}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "skin", "npz": g["fs"], "shader_py": SHP, "params": skin},
            {"name": "lip", "npz": g["fl"], "shader_py": SHP, "params": {**skin_base, "sigma_s": p["sigma_lip"]}},
            {"name": "core", "npz": g["fc"], "shader_py": SHP, "params": {"kind": "core"}},
            {"name": "tongue", "npz": g["ff"], "shader_py": SHP, "smooth": True, "params": {"kind": "filling", "oil_ior": 1.55}},
        ],
        "lights": [
            lamp("key", [-24.0, 12.0, 20.0], p["E_key"], [16, 20], [1.0, 0.86, 0.66]),
            lamp("back", [-2.0, 26.0, 20.0], p["E_back"], [16, 16], [1.0, 0.82, 0.58]),
            lamp("kick", [26.0, 22.0, 4.0], p["E_kick"], [10, 16], [1.0, 0.76, 0.5]),
            lamp("front", [6.0, -30.0, 2.0], p["E_front"], [30, 30], [1.0, 0.8, 0.56]),
        ],
        "env": {"npy": env, "diffuse": False, "transmission": False},
        # no canvas: air, a far warm light out of focus and nothing else. Any structure in it is the steam's.
        "sky": {"top": [0.003, 0.0027, 0.0024], "glow": [0.05, 0.04, 0.031], "h": 0.42, "mottle": 0.0, "y0": 0.34, "x0": 0.82},
        "bounces": 128,
        "volume_bounces": 128,
        "transmission_bounces": 32,
        "glossy_bounces": 6,
        "diffuse_bounces": 4,
        "spp": {"preview": 128, "mid": 512, "final": 1024},
    }
    if "spp" in p:
        scene["spp"][q] = p["spp"]
    dev = {"exposure": p["exposure"], "wb": [1.03, 1.0, 0.95], "contrast": 1.3, "saturation": 1.05, "black": 0.002, "grain": 1.0, "sharpen": 0.2, "halation": 0.06, "vignette": 0.2}
    kit.shoot(NAME, scene, q, tag=tag, develop=dev)


main()
