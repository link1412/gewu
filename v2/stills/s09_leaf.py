"""Shot 9, the leaf itself: tissue and sheet for the moving ginkgo. Used by s09_ginkgo.py; nothing here renders. s09_yinxing.py stays as it was and still makes the old final.

Looked at against ref/yinxing (fresh yellow leaves against the sun; only for looking, nothing of them goes in):
- against the sun the veins are the BRIGHT lines, paler than the blade: the old leaf had them dark, as on a pressed, dried leaf. Seen in Franz van Duns 2021 and DSM4694 2024, at 100%.
- the dark things between veins are resin ducts and smudges, and they come in sectors running along the veins, not evenly.
- most of the margin is clean, with a thin edge that shines. Dead tissue is in patches with fingers that follow the veins; the rest of the rim has none.
- small clear dots near the margin; a few spots drawn out along the veins with a darker core.
The scales (veins 10-14 per cm at the margin, about 0.12 mm wide) are read off those photographs with an assumed leaf size, so: estimates. Spot and duct counts: chosen by eye.
The margin's large shapes use the old leaf's seeds, so the silhouette (and the arc of the shot) stays.
"""

import os

import cv2
import numpy as np

from kit import blur, color, fbm, sstep

W = 5.0  # frame width at the subject (cm)
R = 6.5  # radius of the fan at the crown (cm)
R0 = 3.9  # the mesh starts below the frame
TH = 0.78  # half angle of the mesh (rad)
ROUT = R + 0.35
NOTCH_AT = -0.05
TEAR = float(os.environ.get("S09_TEAR", 0.0))
CURL = float(os.environ.get("S09_CURL", 0.2))  # cm, the rim's curl away from the camera. At 0.34 it turned the sheet edge-on along the right lobe's shoulder, a thin dark arc that read as a crack in motion
NY0, NX0 = 300, 1200


def smooth1d(n, sigma, rng):
    x = rng.standard_normal(n + 8 * int(sigma + 1)).astype(np.float32)
    x = cv2.GaussianBlur(x[None, :], (0, 0), float(sigma), borderType=cv2.BORDER_REFLECT)[0][4 * int(sigma + 1) :][:n]
    return (x - x.mean()) / (x.std() + 1e-9)


def coarse(ny, nx, lo, hi, beta, seed):
    """Large-scale noise on a fixed grid, so that a seed is one composition at every quality."""
    f = fbm((NY0, NX0), NX0 / (2 * TH * R), lo, hi, beta, seed)
    f = cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)
    return blur(f, max(nx / NX0, 1.0))


def margin(seed=5, detail=True):
    """The crown of the leaf, R_m(theta) on a fine angle grid: the old leaf's shape, then a few torn slits along the veins."""
    th_f = np.linspace(-TH, TH, 5000)
    s1 = lambda cm, sd: smooth1d(5000, cm / R / (2 * TH / 5000), np.random.default_rng(sd))
    M = R * np.ones(5000)
    M = M + 0.07 * s1(0.9, seed + 1) + 0.022 * s1(0.3, seed + 2) + 0.009 * s1(0.07, seed + 3) + 0.003 * s1(0.012, seed + 4)
    t = np.abs(th_f - NOTCH_AT) * R
    M = M - 0.8 * np.exp(-((t / 0.05) ** 1.05)) + 0.05 * np.exp(-(((t - 0.6) / 0.7) ** 2))
    rw = np.random.default_rng(seed + 5)
    for _ in range(7):  # small bites and tears
        c, w, d = rw.uniform(-TH, TH), rw.uniform(0.02, 0.12), rw.uniform(0.03, 0.2)
        M = M - d * np.exp(-((np.abs(th_f - c) * R / w) ** 1.6))
    if detail:
        rt = np.random.default_rng(seed + 6)
        for c in (-0.27, 0.2, 0.36):  # tears: hair-thin, short, following the veins. Depth TEAR: 0 since the notch read as cracking open; a tear also grooves the sheet, the curl follows it
            c = c + rt.uniform(-0.02, 0.02)
            w, d = rt.uniform(0.003, 0.006), rt.uniform(0.04, 0.13)
            M = M - TEAR * d * np.exp(-((np.abs(th_f - c) * R / w) ** 1.1))
    return th_f, M


def veins(r, seed, S=0.078):
    """Dichotomous veins as angle(r); a vein forks when its share of the fan has grown too wide. Each returned with how many forks it has been through."""
    rng = np.random.default_rng(seed)
    rf = np.linspace(r[0], r[-1], 700, dtype=np.float32)
    out = []

    def grow(path, width, rlast, age):
        rb = max(S * rng.uniform(0.8, 1.7) / width, rlast + rng.uniform(0.2, 0.7))
        if rb > r[-1]:
            out.append((path, age))
            return
        ramp = sstep(rb, rb + rng.uniform(0.35, 1.5), rf).astype(np.float32)
        a = rng.uniform(0.36, 0.64)
        for off, w in ((-(1 - a) * width / 2, a * width), (a * width / 2, (1 - a) * width)):
            child = path + ramp * off + 0.0008 * smooth1d(rf.size, 45, rng) * ramp
            grow(child, w, rb, age + sstep(rb, rb + 0.35, rf).astype(np.float32))

    th = -TH - 0.05
    while th < TH + 0.05:
        w = 0.016 * rng.uniform(0.65, 1.35)
        grow(th + w / 2 + 0.0015 * smooth1d(rf.size, 70, rng), w, r[0] - 0.2, np.zeros(rf.size, np.float32))
        th += w
    paths = np.stack([np.interp(r, rf, p) for p, _ in out]).astype(np.float32)
    ages = np.stack([np.interp(r, rf, a) for _, a in out]).astype(np.float32)
    o = np.argsort(paths[:, -1])
    return paths[o], ages[o]


def leaf(dens, seed=5):
    """P (ny, nx, 3), attributes for the shader, and n: the sheet's rest normal with the fine relief left out, along which the wind moves it."""
    nx, ny = int(5200 * dens), int(1500 * dens)
    r = np.linspace(R0, ROUT, ny, dtype=np.float32)
    th = np.linspace(-TH, TH, nx, dtype=np.float32)
    pxcm = nx / (2 * TH * R)
    shape = (ny, nx)
    Rr = r[:, None]
    rng = np.random.default_rng(seed + 100)

    # --- the margin
    th_f, M = margin(seed)
    R_m = np.interp(th, th_f, M).astype(np.float32)
    aa = max(0.0035, 0.7 / pxcm)
    mask = sstep(R_m[None, :] + aa, R_m[None, :] - aa, Rr)
    dm = R_m[None, :] - Rr  # distance in from the margin (cm)

    # --- the veins: every one with its own strength, thinner after each fork, tapering, wandering in width; a few faint
    paths, ages = veins(r, seed)
    nk = paths.shape[0]
    wk = np.exp(rng.normal(0, 0.28, nk)).astype(np.float32)
    sk = np.clip(rng.beta(2.2, 1.6, nk), 0.12, 1.0).astype(np.float32)
    along = np.stack([smooth1d(ny, 0.5 * pxcm, rng) for _ in range(16)])  # wander along the length, shared out between veins
    which = rng.integers(0, 16, nk)
    dist, gap, width, vstr = [np.zeros(shape, np.float32) for _ in range(4)]
    for i in range(ny):
        c = np.maximum.accumulate(paths[:, i])
        k = np.clip(np.searchsorted(c, th), 1, nk - 1)
        dl, dr = th - c[k - 1], c[k] - th
        left = np.abs(dl) < np.abs(dr)
        near = np.where(left, k - 1, k)
        dist[i] = np.where(left, np.abs(dl), np.abs(dr)) * r[i]
        gap[i] = (dl + dr) * r[i]
        wob = np.exp(0.16 * along[which[near], i])
        width[i] = (0.0078 * (1.0 - 0.34 * (r[i] - R0) / (R - R0))) * 0.86 ** ages[near, i] * wk[near] * wob
        vstr[i] = sk[near] * (0.72 + 0.28 * np.clip(along[(which[near] + 5) % 16, i], -1, 1)) * 0.9 ** ages[near, i]
    x_v = dist / (width + 1e-5)
    core = sstep(1.0, 0.25, x_v)
    vein = core * vstr * sstep(0.0, 0.12, dm + 0.02)  # veins die out just short of the edge
    t_mid = np.clip(dist / (0.5 * gap + 1e-5), 0, 1)

    # --- sectors: slow bands along the veins, where ducts crowd and the blade is darker and greener
    def alongv(lo, hi, beta, sd, k):
        f = fbm((max(ny // k, 4), nx), pxcm, lo, hi, beta, sd)
        return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)

    sector = coarse(ny // 5 + 2, nx, 0.25, 1.1, 1.8, seed + 30)
    sector = cv2.resize(sector, (nx, ny), interpolation=cv2.INTER_CUBIC)
    crowd = sstep(-0.2, 1.5, sector + 0.4 * coarse(ny, nx, 0.6, 2.5, 2.2, seed + 31))

    # --- resin ducts: short dark streaks between veins, crowded in the sectors; some as chains of dashes
    duct = np.zeros(shape, np.float32)
    n_ducts = 5200
    lw = max(1, int(round(0.0028 * pxcm)))
    kept = 0
    for _ in range(n_ducts):
        k = int(rng.integers(0, nk - 1))
        i0 = int(rng.integers(0, ny))
        f = rng.uniform(0.28, 0.72)
        j = int(np.clip(((1 - f) * paths[k, i0] + f * paths[k + 1, i0] + TH) / (2 * TH) * (nx - 1), 0, nx - 1))
        if rng.random() > 0.14 + 0.86 * crowd[i0, j]:
            continue
        L = rng.lognormal(np.log(0.085), 0.65) * pxcm
        i1 = min(ny - 1, i0 + int(L))
        ta0 = (1 - f) * paths[k, i0] + f * paths[k + 1, i0]
        ta1 = (1 - f) * paths[k, i1] + f * paths[k + 1, i1]
        j0 = (ta0 + TH) / (2 * TH) * (nx - 1)
        j1 = (ta1 + TH) / (2 * TH) * (nx - 1)
        cv2.line(duct, (int(j0 * 8), int(i0 * 8)), (int(j1 * 8), int(i1 * 8)), float(rng.uniform(0.2, 0.85)), lw, cv2.LINE_AA, 3)
        kept += 1
    duct = blur(duct, max(0.0018 * pxcm, 0.5))

    # --- mesophyll: long cells along the veins, a finer speckle, and blotches at several sizes with a clear main size
    fibre = alongv(0.005, 0.04, 1.2, seed + 10, 6)
    speck = fbm(shape, pxcm, 0.003, 0.02, 0.6, seed + 16)
    blotch = fbm(shape, pxcm, 0.04, 0.5, 2.2, seed + 11)
    big = coarse(ny, nx, 0.6, 3.5, 2.4, seed + 12)
    scorch = sstep(0.5, 1.8, coarse(ny, nx, 0.9, 2.8, 2.6, seed + 17))

    # --- autumn: where the green is gone and how far the gold has gone. Scat keeps headroom: a vein may pass more than the blade
    K = 0.72
    gold = color([0.98, 0.50, 0.030]) * K
    lemon = color([1.0, 0.64, 0.060]) * K
    deep = color([0.90, 0.33, 0.014]) * K
    green = color([0.60, 0.47, 0.03]) * K
    amber = color([0.74, 0.20, 0.008]) * K
    brown = color([0.105, 0.030, 0.008])
    u = sstep(R0 + 0.6, R - 0.1, Rr)
    a_lemon = np.clip(0.28 + 0.72 * u**1.5 + 0.10 * big + 0.03 * blotch - 0.14 * crowd, 0, 1)
    scat = deep[None, None] * (1 - a_lemon[..., None]) ** 2 + gold[None, None] * 2 * a_lemon[..., None] * (1 - a_lemon[..., None]) + lemon[None, None] * a_lemon[..., None] ** 2
    a_green = np.clip(sstep(1.0, 0.1, a_lemon + 0.05 * blotch) * 0.26 + 0.42 * crowd * sstep(0.85, 0.3, a_lemon), 0, 1) * 0.75
    scat = scat * (1 - a_green[..., None]) + green[None, None] * a_green[..., None]
    scat = scat * (1 - 0.5 * scorch[..., None]) + amber[None, None] * 0.5 * scorch[..., None] * (1 - 0.3 * big[..., None].clip(-1, 1))

    # cells differ, the blade is denser halfway between two veins
    cell_k = np.exp(0.07 * fibre + 0.04 * speck + 0.035 * blotch)
    scat = scat * cell_k[..., None]
    scat = scat * (0.86 + 0.14 * (1 - t_mid[..., None] ** 1.5))
    scat = scat * (1 - 0.16 * crowd[..., None] * color([0.7, 1.0, 1.4]))
    # the vein passes more, and paler, and wakes a little glow around itself
    halo = np.exp(-((dist / np.maximum(3.2 * width, 0.006)) ** 2)) * (1 - core) * vstr
    scat = scat * (1 + 0.14 * halo[..., None])
    scat = scat * (1 + vein[..., None] * color([0.34, 0.60, 1.2])) + vein[..., None] * color([0.01, 0.012, 0.012])
    scat = scat * (1 - 0.5 * duct[..., None] * color([0.72, 0.88, 1.0]))

    # --- clear dots near the margin
    dots = np.zeros(shape, np.float32)
    dr_ = np.random.default_rng(seed + 18)
    for _ in range(220):
        j, d0 = int(dr_.integers(0, nx)), dr_.uniform(0.04, 1.3) ** 1.5
        i = int((R_m[j] - d0 - R0) / (ROUT - R0) * (ny - 1))
        if 0 <= i < ny:
            rad = dr_.uniform(0.003, 0.009) * pxcm
            cv2.circle(dots, (j, i), max(1, int(rad)), float(dr_.uniform(0.3, 1.0)), -1, cv2.LINE_AA)
    dots = blur(dots, max(0.002 * pxcm, 0.5))
    scat = scat * (1 + 0.32 * dots[..., None] * color([0.6, 1.0, 1.8]))

    # --- dead tissue: patches on the rim, fingers along the veins, an amber shoulder; most of the rim has none
    n_d = fbm(shape, pxcm, 0.015, 0.45, 2.0, seed + 13)
    fing = alongv(0.01, 0.13, 1.5, seed + 19, 14)
    n_rim = coarse(ny, nx, 0.45, 2.0, 2.4, seed + 14)[-1]
    n_rim = n_rim + 0.7 * np.exp(-(((th - NOTCH_AT - 0.09) / 0.05) ** 2))  # the crown of the right lobe keeps a scorch: it is the eye's first stop
    rim_w = 0.005 + 0.13 * sstep(0.6, 2.4, n_rim + 0.25 * smooth1d(nx, 0.06 * pxcm, np.random.default_rng(seed + 24)))[None, :]
    field = dm / rim_w - 0.42 * fing - 0.4 * n_d
    dead = sstep(1.15, 0.45, field)
    should = sstep(4.5, 1.0, field) * sstep(0.015, 0.09, rim_w)
    scat = scat * (1 - 0.62 * should[..., None]) + amber[None, None] * 0.62 * should[..., None] * cell_k[..., None]

    # --- spots: a stain that spreads through the tissue, drawn out along the veins and stopped by them, darker at its middle; no outline of its own
    spots = np.zeros(shape, np.float32)
    sp = np.random.default_rng(seed + 15)
    n_sp = 0
    while n_sp < 60:
        j, i = int(sp.integers(0, nx)), int(sp.uniform(0.2, 1.0) * (ny - 1))
        if sp.random() > 0.2 + 0.8 * crowd[i, j]:
            continue
        n_sp += 1
        rad = min(sp.lognormal(np.log(0.006), 0.6), 0.022) * pxcm
        ang = float(np.clip(sp.normal(0, 7), -25, 25))
        cv2.ellipse(spots, (j, i), (max(1, int(rad)), max(1, int(rad * sp.uniform(1.4, 3.0)))), ang, 0, 360, float(sp.uniform(0.6, 1.0)), -1, cv2.LINE_AA)
    # the stain's edge is the noise's edge: threshold a blurred blob plus fine noise, so that no ellipse is left
    stain = blur(spots, max(0.007 * pxcm, 0.8))
    wob = fbm(shape, pxcm, 0.004, 0.035, 1.5, seed + 25)
    stain = stain * (1 + 0.5 * wob) * (1 - 0.35 * core)
    halo_s = np.clip(blur(spots, max(0.03 * pxcm, 1.0)) * 2.2, 0, 1)
    scat = scat * (1 - 0.55 * halo_s[..., None] * (1 - color([0.72, 0.40, 0.22])))
    wet = sstep(0.08, 0.62, stain)
    dead = np.maximum(dead, wet * 0.92)
    d_k = 0.7 + 0.5 * (0.5 + 0.5 * np.clip(fibre, -1, 1)) + 0.25 * np.clip(speck, -1, 1)
    # dying tissue goes through amber to brown: the mix is by a curve, so a stain's edge is lighter and warmer than its middle
    mid_col = amber[None, None] * 0.55 * d_k[..., None]
    t1 = sstep(0.0, 0.55, dead)[..., None]
    t2 = sstep(0.45, 1.0, dead)[..., None]
    scat = (scat * (1 - t1) + mid_col * t1) * (1 - t2) + brown[None, None] * d_k[..., None] * t2

    # --- the edge that shines: thin tissue with little pigment, where it is alive
    edge = sstep(0.022, 0.004, dm) * (1 - dead) * (0.5 + 0.5 * sstep(-1.0, 1.0, coarse(ny, nx, 0.1, 0.6, 1.6, seed + 22)))
    scat = scat * (1 - edge[..., None]) + color([0.98, 0.80, 0.30]) * edge[..., None]
    scat = np.clip(scat, 0, 1).astype(np.float32)

    # --- the sheet
    ripple = coarse(ny, nx, 1.6, 5.0, 2.2, seed + 20)
    wav = coarse(ny, nx, 0.4, 1.2, 2.0, seed + 21)
    pleat = coarse(ny // 6 + 2, nx, 0.45, 1.5, 2.2, seed + 23)
    pleat = cv2.resize(pleat, (nx, ny), interpolation=cv2.INTER_CUBIC)
    amp = 0.03 + 0.25 * sstep(0.1, 1.0, (Rr - R0) / (R - R0))
    # relief: the cuticle swells between the veins, sinks along each vein and duct
    h = blur(0.0075 * (4 * t_mid * (1 - t_mid)) ** 0.7 - 0.0045 * core - 0.0012 * duct + 0.0009 * fibre + 0.0018 * blotch, 0.7 * max(dens, 0.5))
    curl = CURL * sstep(0.55, 0.0, dm) ** 2 * (0.25 + 0.75 * sstep(-1.0, 1.0, wav))
    # the two lobes roll back a little from the notch, seen in the light on its edges
    t_n = (th[None, :] - NOTCH_AT) * Rr
    shoulder = 0.10 * sstep(-0.9, 0.0, Rr - R_m.min()) * np.exp(-((np.abs(t_n) / 0.55) ** 1.5)) * sstep(0.0, 0.25, np.abs(t_n))
    a = th[None, :] + 0.008 * ripple
    x = Rr * np.sin(a)
    z = Rr * np.cos(a)
    y0 = amp * (ripple + 0.2 * wav) + curl + shoulder + 0.05 * sstep(0.1, 1.0, (Rr - R0) / (R - R0)) * pleat + 0.62 * (Rr - R) + 0.024 * x**2
    S = np.stack([x, y0, z], -1).astype(np.float32)  # no relief: the sheet the wind sees
    P = S.copy()
    P[..., 1] -= h
    # the direction of travel: the sheet's normal smoothed over about a centimetre. A sharper one lets a large w spread the ripples apart like a balloon
    sg = max(1.0 * pxcm, 1.0)
    sm = 8
    Ss = np.stack([cv2.resize(blur(cv2.resize(S[..., c], (nx // sm, ny // sm), interpolation=cv2.INTER_AREA), sg / sm), (nx, ny), interpolation=cv2.INTER_CUBIC) for c in range(3)], -1)
    du, dv = np.gradient(Ss, axis=1), np.gradient(Ss, axis=0)
    n = np.cross(du, dv)
    n = n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)
    if n[ny // 2, nx // 2, 1] < 0:
        n = -n
    tau = 3.5 * mask * (1 + 0.3 * core + 1.2 * dead) * (1 - 0.6 * edge)
    attrs = {
        "tau": tau.astype(np.float32),
        "scat": scat,
        "trans": (1 - mask[..., None] + mask[..., None] * np.clip(scat / K, 0, 1) ** 1.5).astype(np.float32),
        "mask": mask.astype(np.float32),
        "glw": (mask * (0.45 + 0.55 * sstep(0.5, 0.0, dm)) * (1 - 0.7 * dead)).astype(np.float32),
    }
    return P, attrs, n.astype(np.float32), {"r": r, "th": th, "R_m": R_m, "dm": dm}


def fan_poly(cx, cz, rad, a0, a1, seed, n=260):
    """A neighbour leaf, as the outline that casts the shadow: a fan with a wavy crown and a notch, in the plane of this one. Returns (n, 2) x, z."""
    rg = np.random.default_rng(seed)
    a = np.linspace(a0, a1, n)
    w = smooth1d(n, 22, rg) * 0.1 + smooth1d(n, 6, rg) * 0.02
    rr = rad * (1 + 0.03 * w / 0.1) * (1 - 0.14 * np.exp(-(((a - 0.5 * (a0 + a1)) / 0.022) ** 2)))
    return np.stack([cx + rr * np.sin(a), cz + rr * np.cos(a)], -1), np.array([cx, cz])
