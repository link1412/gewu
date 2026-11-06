"""The glaze of shot 6 as it fired: a raw layer that cracked as it dried, a loaded copper stroke on top, and then the melt running down the wall.

Thin film on a wall, on a fixed grid (1 mm = 10 px), so the shapes are the same at every quality:
  h_t + div q = 0,  q = C h^3 (S e_v - gamma grad b - kappa grad h)  (lubrication; S the slope of the wall, b the thrown body's slow undulation)
followed each step by capillary levelling, whose rate goes as h^3 k^4 (Orchard): a crack first loses its sharp edge and heals slowly, into a shallow trough.
It gives, without being asked: thin glaze at the lip (the Jeffreys profile, h ~ sqrt(v)), rivers along the body's undulation, and a fat tongue where the stroke was loaded.
A flow map, source coordinates carried by the same velocity, lets everything fine be made at output size and then be stretched along the flow: copper, cracks, clouds, grain.

What is looked up, in ref/jun/report.md: mean glaze 850-920 um, tracks 1.0-1.6 mm wide, up to 5 cm long, about 8-10 in 5 x 4 cm, running rim to foot and sometimes across
(李媛 2013, samples from Juntai, whose dating is disputed); the track is a darker, glassier band in the glaze, healed from a crack in the drying glaze. That paper's 850 um and 65 um are how
deep the band goes into the glaze, NOT a surface groove; it reports no surface height, so the trough's depth here is an estimate. All the speeds, amplitudes and the loaded stroke are estimates.
"""

import cv2
import numpy as np
from scipy.fft import dctn, idctn
from scipy.ndimage import gaussian_filter1d

from kit import fbm, sstep

PX = 100.0  # px per cm of the simulation


def crack_paths(LU, V0, V1, seed):
    """Drying cracks as polylines with a width at each point: they run down the wall, meander, kink, fork, and stop on one another (T junctions), as a shrinking layer does.
    Returns [(xy (n,2) cm, w (n,) cm)]. Occupancy decides the stops."""
    rng = np.random.default_rng(seed)
    occ_px = 40.0
    occ = np.zeros((int((V1 - V0) * occ_px) + 2, int(LU * occ_px) + 2), np.int32)
    paths = []
    step = 0.022

    def grow(p, a, L, w0, a_home, pid):
        n = max(int(L / step), 4)
        pts, drift = [p.copy()], 0.0
        for i in range(n):
            drift = 0.9 * drift + rng.normal(0, 0.02)
            a = a + drift + 0.03 * (a_home - a)
            if rng.random() < 0.012:  # a crack goes straight and then changes its mind
                a += rng.choice([-1, 1]) * rng.uniform(0.2, 0.55)
            p = p + step * np.array([np.cos(a), np.sin(a)])
            ix, iy = int((p[0] + LU / 2) * occ_px), int((p[1] - V0) * occ_px)
            if not (0 <= ix < occ.shape[1] and 0 <= iy < occ.shape[0]):
                break
            pts.append(p.copy())
            o = occ[iy, ix]
            if o and o != pid and i > 6:
                break  # T junction
            occ[iy, ix] = pid
        t = np.linspace(0, 1, len(pts))
        q = rng.uniform(0, 6.28)
        w = w0 * (0.78 + 0.22 * np.sin(q + t * L * 2.6) + 0.14 * np.sin(2.3 * q + t * L * 7.1)) * sstep(0.0, 0.14, t) ** 0.8 * sstep(1.0, 0.65, t) ** 0.8
        return np.array(pts), np.maximum(w, 0.004)

    pid = 1
    # the long ones, rim to foot: spaced unevenly along the rim
    u = -LU / 2 + rng.uniform(0.1, 0.8)
    mains = []
    while u < LU / 2:
        wide = rng.random() < 0.62
        w0 = rng.uniform(0.05, 0.095) if wide else rng.uniform(0.02, 0.04)
        pts, w = grow(np.array([u, rng.uniform(0.02, 0.28)]), np.pi / 2 + rng.normal(0, 0.28), rng.uniform(1.4, 4.2), w0, np.pi / 2 + rng.normal(0, 0.18), pid)
        paths.append((pts, w))
        mains.append((pts, w, pid))
        pid += 1
        u += rng.uniform(0.45, 1.15)
    # forks and cross-links, narrower, each stopping on the next crack
    for pts, w, _ in list(mains):
        for _ in range(int(rng.integers(1, 4))):
            k = int(rng.integers(len(pts) // 8, max(len(pts) * 7 // 8, len(pts) // 8 + 1)))
            d = pts[min(k + 1, len(pts) - 1)] - pts[k - 1]
            a0 = np.arctan2(d[1], d[0]) + rng.choice([-1, 1]) * rng.uniform(0.7, 1.45)
            paths.append(grow(pts[k].copy(), a0, rng.lognormal(np.log(0.75), 0.6), max(float(w[k]) * rng.uniform(0.35, 0.7), 0.012), a0, pid))
            pid += 1
    return paths


def track_paths(LU, V0, V1, seed):
    """The tracks as they read on the Met's 50.145.309 and the Cleveland jar: hairlines that wander, fade and stop, seldom fork; and a few wider, faint, soft streaks.
    Returns hairs [(xy, w, strength)] and bands the same way. Width and strength are functions of length: strength falls to nothing in places, so one crack reads as several pieces."""
    rng = np.random.default_rng(seed)
    step = 0.012

    def path(p, a, L, a_home):
        n = max(int(L / step), 6)
        pts, drift = [p.copy()], 0.0
        for i in range(n):
            drift = 0.94 * drift + rng.normal(0, 0.016)
            a = a + drift + 0.03 * (a_home - a)
            p = p + step * np.array([np.cos(a), np.sin(a)])
            pts.append(p.copy())
        return np.array(pts)

    def gate(s, L):
        """Strength along the arc length s: slow, with gaps, and ends that fade."""
        q1, q2 = rng.uniform(0, 6.28, 2)
        lam1, lam2 = rng.uniform(0.7, 1.5), rng.uniform(0.22, 0.5)
        g = 0.85 + 0.42 * np.sin(q1 + s / lam1 * 6.28) + 0.16 * np.sin(q2 + s / lam2 * 6.28)
        return np.clip(g, 0, 1) * sstep(0.0, 0.12, s / L) * sstep(1.0, 0.8, s / L)

    hairs, bands = [], []
    u = -LU / 2 + rng.uniform(0.1, 0.5)
    while u < LU / 2:
        L = rng.lognormal(np.log(1.5), 0.5)
        v = rng.uniform(0.05, 1.1)
        a0 = np.pi / 2 + rng.normal(0, 0.55)
        P = path(np.array([u, v]), a0, L, a0)
        s_ = np.arange(len(P)) * step
        q = rng.uniform(0, 6.28)
        w = rng.uniform(0.016, 0.038) * (1 + 0.3 * np.sin(q + s_ * 3.1))
        hairs.append((P, w, gate(s_, L) * rng.uniform(0.5, 1.0)))
        if rng.random() < 0.22:  # a short fork, weak
            k = int(rng.integers(len(P) // 4, 3 * len(P) // 4))
            d = P[k + 1] - P[k - 1]
            a1 = np.arctan2(d[1], d[0]) + rng.choice([-1, 1]) * rng.uniform(0.5, 1.0)
            L1 = rng.uniform(0.2, 0.6)
            Q = path(P[k].copy(), a1, L1, a1)
            s1 = np.arange(len(Q)) * step
            hairs.append((Q, np.full(len(Q), 0.011), 0.6 * gate(s1, L1)))
        u += rng.uniform(0.35, 0.95)
    # the wider streaks of the Cleveland jar, about 1.4 mm by 1 cm (measured off the crop, by its own scale, which is an estimate)
    for _ in range(int((LU * (V1 - V0)) / 4.0)):
        L = rng.uniform(0.6, 1.3)
        a0 = np.pi / 2 + rng.normal(0, 0.3)
        P = path(np.array([rng.uniform(-LU / 2, LU / 2), rng.uniform(0.2, 2.4)]), a0, L, a0)
        s_ = np.arange(len(P)) * step
        bands.append((P, np.full(len(P), rng.uniform(0.07, 0.12)), gate(s_, L) * rng.uniform(0.5, 0.9)))
    return hairs, bands


def raster_tracks(paths, LU, V0, V1, pxcm, feather):
    """Soft mask, strength as the value; feather in cm."""
    g = (int((V1 - V0) * pxcm), int(LU * pxcm))
    m = np.zeros(g, np.uint8)
    SH = 4
    k = pxcm * (1 << SH)
    for pts, w, st in paths:
        P = np.round((pts - [-LU / 2, V0]) * k).astype(np.int32)
        for i in range(0, len(P) - 1):
            if st[i] > 0.02:
                cv2.line(m, tuple(P[i]), tuple(P[i + 1]), int(255 * st[i]), max(1, int(round(float(w[i]) * pxcm))), cv2.LINE_AA, SH)
    return cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), max(pxcm * feather, 0.5))


def raster_cracks(paths, LU, V0, V1, pxcm):
    """Soft mask on a fixed grid; each segment with its own width, in continuous coordinates."""
    g = (int((V1 - V0) * pxcm), int(LU * pxcm))
    m = np.zeros(g, np.uint8)
    SH = 4
    k = pxcm * (1 << SH)
    for pts, w in paths:
        P = np.round((pts - [-LU / 2, V0]) * k).astype(np.int32)
        for i in range(0, len(P) - 1):
            cv2.line(m, tuple(P[i]), tuple(P[i + 1]), 255, max(1, int(round(float(w[i]) * pxcm))), cv2.LINE_AA, SH)
    return cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), max(pxcm * 0.004, 0.5))


def stroke(g, pts, width, x0, v0, pxcm, seed):
    """A brush load: a soft-shouldered band along a polyline, its width torn at a long wavelength. Value 0..1."""
    pts = np.array(pts, float)
    tt = np.linspace(0, 1, 500)
    cs = np.stack([np.interp(tt, np.linspace(0, 1, len(pts)), pts[:, i]) for i in (0, 1)], -1).astype(np.float32)
    cs = gaussian_filter1d(cs, 22.0, axis=0, mode="nearest")  # along the path only. cv2.GaussianBlur on this (n, 2) array also blurs x into y
    m = np.zeros(g, np.uint8)
    xy = np.round((cs - [x0, v0]) * pxcm).astype(np.int32)
    cv2.polylines(m, [xy.reshape(-1, 1, 2)], False, 255, 1)
    d = cv2.distanceTransform(255 - m, cv2.DIST_L2, 5) / pxcm
    e = fbm(g, pxcm, 0.25, 2.2, 2.8, seed)
    return np.clip((1.0 - d / np.maximum(width * (1 + 0.28 * e), 0.05)) * 3.0, 0, 1).astype(np.float32)


def _level(h, dt_A):
    """Capillary levelling, one implicit step, reflecting boundaries, with the mean h^3 (a frozen coefficient: an estimate of the rate is all this needs)."""
    ny, nx = h.shape
    ky = np.pi * np.arange(ny) / (ny / PX)
    kx = np.pi * np.arange(nx) / (nx / PX)
    k2 = kx[None, :] ** 2 + ky[:, None] ** 2
    H = dctn(h, type=2, norm="ortho")
    H *= 1.0 / (1.0 + dt_A * k2 * k2)
    return idctn(H, type=2, norm="ortho").astype(np.float32)


def simulate(prof_slope, LU, V0, V1, strokes, paths, seed=620, T=0.34, C0=100.0, h0=0.098):
    """prof_slope(v): the slope of the wall at arc length v. Returns h (cm), the flow map (u0, v0) in cm, c (the stroke's load through the map, 0..1) on the fixed grid."""
    g = (int((V1 - V0) * PX), int(LU * PX))
    ny, nx = g
    dx = 1.0 / PX
    v = V0 + (np.arange(ny, dtype=np.float32) + 0.5) * dx
    u = -LU / 2 + (np.arange(nx, dtype=np.float32) + 0.5) * dx
    U, V = np.meshgrid(u, v)
    j0 = int(np.ceil(-V0 * PX))  # the lip: the wall starts here, nothing flows in from above

    load = np.zeros(g, np.float32)
    for i, (pts, width, gain) in enumerate(strokes):
        load = np.maximum(load, gain * stroke(g, pts, width, -LU / 2, V0, PX, seed + 3 * i))

    S = prof_slope(v)[:, None].astype(np.float32)
    b = cv2.GaussianBlur(fbm(g, PX, 0.7, 4.0, 3.0, seed + 41).astype(np.float32), (0, 0), 2.0)  # the thrown body, slow, in units of its own: only its slope is used
    bu = np.gradient(b, axis=1) / dx
    bv = np.gradient(b, axis=0) / dx
    gamma = 0.05 / float(np.hypot(bu, bv).std() + 1e-6)  # the undulation tilts the wall by about +-3 degrees: it steers the flow, does not stop it

    cr = raster_cracks(paths, LU, V0, V1, PX)
    h = h0 * (1 + 0.05 * fbm(g, PX, 0.3, 2.0, 2.8, seed + 42)).astype(np.float32) + 0.085 * load
    h = h * (1 - 0.72 * np.clip(cr * 1.3, 0, 1))  # the raw layer has opened along the cracks
    h[:j0] = 0.006
    h = h.astype(np.float32)

    X0 = U.copy()
    Y0 = V.copy()
    GX, GY = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    t = 0.0
    steps = 0
    while t < T:
        hy = np.gradient(h, axis=0) / dx
        hx = np.gradient(h, axis=1) / dx
        hy[: j0 + 2] = 0.0  # the step at the lip is not a pressure gradient
        kappa = 0.12
        mob = C0 * np.minimum(h, 0.2) ** 2  # the mean speed: q / h. Capped: a pool does not run away on this explicit scheme
        vv = mob * (S - gamma * bv - kappa * hy)
        vu = mob * (-gamma * bu - kappa * hx)
        vmax = float(np.abs(vv).max() + np.abs(vu).max()) * 1.6
        dt = min(0.5 * dx / max(vmax, 1e-6), T - t)
        # upwind, conservative
        qv = vv * h
        qu = vu * h
        fv = np.zeros((ny + 1, nx), np.float32)
        up = 0.5 * (vv[:-1] + vv[1:])
        fv[1:-1] = np.where(up > 0, qv[:-1], qv[1:])
        fv[: j0 + 1] = 0.0  # nothing crosses the lip
        fv[-1] = qv[-1]  # and it runs on out of the bottom of the grid
        fu = np.zeros((ny, nx + 1), np.float32)
        up = 0.5 * (vu[:, :-1] + vu[:, 1:])
        fu[:, 1:-1] = np.where(up > 0, qu[:, :-1], qu[:, 1:])
        fu[:, 0] = qu[:, 0]
        fu[:, -1] = qu[:, -1]
        h = h - dt / dx * (np.diff(fv, axis=0) + np.diff(fu, axis=1))
        h = _level(h, dt * 2.2e-4 * 0.15)
        h[:j0] = 0.006
        h = np.maximum(h, 0.004).astype(np.float32)
        # the map, semi-Lagrangian
        mapx = (GX - (vu * dt / dx)).astype(np.float32)
        mapy = (GY - (vv * dt / dx)).astype(np.float32)
        X0 = cv2.remap(X0, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        Y0 = cv2.remap(Y0, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        t += dt
        steps += 1
    print(f"flow: {steps} steps; h {h[j0:].min():.3f}..{h[j0:].max():.3f} cm, median {np.median(h[j0:]):.3f}")
    return h, X0, Y0, load
