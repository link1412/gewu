"""Shot 9: a golden ginkgo leaf against low sun, dark trees far behind. The fan's margin is the arc.

    python3 -I v2/stills/s09_yinxing.py [preview|mid|final]

Built like the real thing (scales are estimates from general botany, not measured from a specimen):
- no midrib: veins enter at the base and fork in two, again and again, whenever the gap between them grows too wide
  (about 8-15 veins per cm at the margin, each about 0.2 mm wide);
- between the veins, short dark resin ducts, and mesophyll cells that show as a fine lengthwise mottle;
- a bilobed fan: a notch at the top, shallow crenulations and small wounds in the margin, brown dead tissue along it;
- autumn colour is uneven: lemon towards the margin, deeper gold inside, some green left along veins near the base;
- the soft shadows of a neighbouring leaf and a twig on the sheet are painted into the transmitted colour rather than
  ray traced (a real occluder left a grid artefact in the penumbra after denoising).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from kit import OUT, ROOT, blur, color, fbm, frame_camera, shoot, sstep

W = 5.0  # frame width at the subject (cm)
R = 6.5  # radius of the fan at the crown (cm)
R0 = 3.9  # the mesh starts below the frame
TH = 0.78  # half angle of the mesh (rad)
ROUT = R + 0.35


def smooth1d(n, sigma, rng):
    x = rng.standard_normal(n + 8 * int(sigma + 1)).astype(np.float32)
    x = cv2.GaussianBlur(x[None, :], (0, 0), float(sigma), borderType=cv2.BORDER_REFLECT)[0][4 * int(sigma + 1) :][:n]
    return (x - x.mean()) / (x.std() + 1e-9)


NY0, NX0 = 300, 1200


def coarse(ny, nx, lo, hi, beta, seed):
    """Large-scale noise on a fixed grid, so that a seed is one composition at every quality."""
    f = fbm((NY0, NX0), NX0 / (2 * TH * R), lo, hi, beta, seed)
    f = cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)
    # cubic interpolation has kinks at the coarse grid lines; on a displaced sheet they show as a woven grid in the shading
    return blur(f, max(nx / NX0, 1.0))


def veins(r, seed):
    """Dichotomous veins as angle(r); a vein forks when its share of the fan has grown too wide."""
    rng = np.random.default_rng(seed)
    rf = np.linspace(r[0], r[-1], 700, dtype=np.float32)
    S = 0.095  # the gap (cm) at which a vein forks, roughly
    out = []

    def grow(path, width, rlast, age):
        rb = max(S * rng.uniform(0.85, 1.5) / width, rlast + 0.3)
        if rb > r[-1]:
            out.append((path, age))
            return
        ramp = sstep(rb, rb + rng.uniform(0.45, 1.3), rf).astype(np.float32)
        a = rng.uniform(0.42, 0.58)
        for off, w in ((-(1 - a) * width / 2, a * width), (a * width / 2, (1 - a) * width)):
            child = path + ramp * off + 0.0007 * smooth1d(rf.size, 45, rng) * ramp
            grow(child, w, rb, age + sstep(rb, rb + 0.35, rf).astype(np.float32))

    th = -TH - 0.05
    while th < TH + 0.05:
        w = 0.018 * rng.uniform(0.75, 1.25)
        grow(th + w / 2 + 0.0015 * smooth1d(rf.size, 70, rng), w, r[0] - 0.2, np.zeros(rf.size, np.float32))
        th += w
    paths = np.stack([np.interp(r, rf, p) for p, _ in out]).astype(np.float32)
    ages = np.stack([np.interp(r, rf, a) for _, a in out]).astype(np.float32)
    o = np.argsort(paths[:, -1])
    return paths[o], ages[o]


def leaf(dens, seed=5, notch_at=-0.05, wounds=True):
    nx, ny = int(5200 * dens), int(1500 * dens)
    r = np.linspace(R0, ROUT, ny, dtype=np.float32)
    th = np.linspace(-TH, TH, nx, dtype=np.float32)
    pxcm = nx / (2 * TH * R)
    shape = (ny, nx)
    Rr = r[:, None]
    rng = np.random.default_rng(seed + 100)

    # --- the margin
    th_f = np.linspace(-TH, TH, 5000)
    s1 = lambda cm, sd: smooth1d(5000, cm / R / (2 * TH / 5000), np.random.default_rng(sd))
    M = R * np.ones(5000)
    M = M + 0.07 * s1(0.9, seed + 1) + 0.022 * s1(0.3, seed + 2) + 0.009 * s1(0.07, seed + 3) + 0.003 * s1(0.012, seed + 4)
    # the notch: a narrow, rounded cleft between the two lobes, whose shoulders rise a little
    t = np.abs(th_f - notch_at) * R
    M = M - 0.8 * np.exp(-((t / 0.05) ** 1.05)) + 0.05 * np.exp(-(((t - 0.6) / 0.7) ** 2))
    if wounds:
        rw = np.random.default_rng(seed + 5)
        for _ in range(7):  # small bites and tears
            c, w, d = rw.uniform(-TH, TH), rw.uniform(0.02, 0.12), rw.uniform(0.03, 0.2)
            M = M - d * np.exp(-((np.abs(th_f - c) * R / w) ** 1.6))
    R_m = np.interp(th, th_f, M).astype(np.float32)
    mask = sstep(R_m[None, :] + 0.0035, R_m[None, :] - 0.0035, Rr)
    dm = R_m[None, :] - Rr  # distance in from the margin (cm)

    # --- the veins
    paths, ages = veins(r, seed)
    nk = paths.shape[0]
    wk = rng.uniform(0.75, 1.2, (nk, 1)).astype(np.float32)
    dist, gap, width = [np.zeros(shape, np.float32) for _ in range(3)]
    side = np.zeros(shape, np.int32)
    for i in range(ny):
        c = np.maximum.accumulate(paths[:, i])
        k = np.clip(np.searchsorted(c, th), 1, nk - 1)
        dl, dr = th - c[k - 1], c[k] - th
        left = np.abs(dl) < np.abs(dr)
        near = np.where(left, k - 1, k)
        dist[i] = np.where(left, np.abs(dl), np.abs(dr)) * r[i]
        gap[i] = (dl + dr) * r[i]
        width[i] = (0.0085 * (1.0 - 0.3 * (r[i] - R0) / (R - R0))) * 0.88 ** ages[near, i] * wk[near, 0]
        side[i] = near
    x_v = dist / (width + 1e-5)
    vein = sstep(1.0, 0.45, x_v)
    t_mid = np.clip(dist / (0.5 * gap + 1e-5), 0, 1)

    # --- resin ducts: short dark streaks halfway between veins
    duct = np.zeros(shape, np.float32)
    n_ducts = 2600
    lw = max(1, int(round(0.0035 * pxcm)))
    for _ in range(n_ducts):
        k = int(rng.integers(0, nk - 1))
        L = rng.uniform(0.05, 0.42) * pxcm
        i0 = int(rng.integers(0, ny))
        i1 = min(ny - 1, i0 + int(L * ny / ((ROUT - R0) * pxcm)))
        f = rng.uniform(0.3, 0.7)
        ta0 = (1 - f) * paths[k, i0] + f * paths[k + 1, i0]
        ta1 = (1 - f) * paths[k, i1] + f * paths[k + 1, i1]
        j0 = (ta0 + TH) / (2 * TH) * (nx - 1)
        j1 = (ta1 + TH) / (2 * TH) * (nx - 1)
        cv2.line(duct, (int(j0 * 8), int(i0 * 8)), (int(j1 * 8), int(i1 * 8)), float(rng.uniform(0.35, 1.0)), lw, cv2.LINE_AA, 3)
    duct = blur(duct, 0.5 * max(0.002 * pxcm, 0.5))

    # --- mottle: mesophyll cells, drawn out along the veins
    def along(lo, hi, beta, sd, k):
        f = fbm((max(ny // k, 4), nx), pxcm, lo, hi, beta, sd)
        return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)

    cell = along(0.006, 0.05, 1.3, seed + 10, 5)
    blotch = fbm(shape, pxcm, 0.04, 0.5, 2.2, seed + 11)
    big = coarse(ny, nx, 0.6, 3.5, 2.4, seed + 12)

    # --- autumn: where the green is gone and how far the gold has gone
    gold = color([0.98, 0.50, 0.035])
    lemon = color([1.0, 0.62, 0.075])
    deep = color([0.90, 0.33, 0.018])
    green = color([0.62, 0.46, 0.03])
    brown = color([0.20, 0.070, 0.016])
    u = sstep(R0 + 0.6, R - 0.1, Rr)
    a_lemon = np.clip(0.25 + 0.75 * u**1.5 + 0.10 * big + 0.03 * blotch, 0, 1)
    scat = deep[None, None] * (1 - a_lemon[..., None]) ** 2 + gold[None, None] * 2 * a_lemon[..., None] * (1 - a_lemon[..., None]) + lemon[None, None] * a_lemon[..., None] ** 2
    a_green = np.clip(sstep(1.0, 0.1, a_lemon + 0.05 * blotch) * 0.3 + 0.55 * np.exp(-(((dist) / 0.028) ** 2)) * sstep(0.75, 0.15, a_lemon), 0, 1) * 0.8
    scat = scat * (1 - a_green[..., None]) + green[None, None] * a_green[..., None]

    # the leaf is thicker on the veins and cells differ: everything multiplies the light that gets through
    cell_k = np.exp(0.06 * cell + 0.02 * blotch)
    scat = scat * cell_k[..., None]
    vk = (vein[..., None]) * (1 - color([0.52, 0.56, 0.60]))
    scat = scat * (1 - vk)
    halo = np.exp(-(((dist - width * 1.4) / np.maximum(width, 0.003)) ** 2)) * (1 - vein)
    scat = scat * (1 + 0.10 * halo[..., None])
    scat = scat * (1 - 0.42 * duct[..., None] * color([0.75, 0.9, 1.0]))
    scat = scat * (0.92 + 0.08 * t_mid[..., None] ** 0.5)

    # --- dead tissue along the margin, and a few spots with a halo
    n_d = fbm(shape, pxcm, 0.02, 0.6, 2.2, seed + 13)
    dead = sstep(0.018, 0.0, dm - 0.03 * (n_d + 0.6) - 0.05 * sstep(0.5, 1.8, big))
    n_rim = coarse(ny, nx, 0.25, 1.2, 2.2, seed + 14)
    rim_w = 0.035 + 0.12 * sstep(0.3, 1.6, n_rim)
    dead = np.maximum(dead, sstep(0.25, -0.15, dm / rim_w + 0.28 * n_d))
    spots = np.zeros(shape, np.float32)
    sp_rng = np.random.default_rng(seed + 15)
    for _ in range(15):
        j, i = int(sp_rng.integers(0, nx)), int(sp_rng.uniform(0.25, 1.0) * (ny - 1))
        rad = sp_rng.uniform(0.006, 0.03) * pxcm
        cv2.ellipse(spots, (j, i), (int(rad) + 1, int(rad * sp_rng.uniform(1.0, 1.7)) + 1), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    spots = blur(spots, max(0.006 * pxcm, 0.7))
    halo_s = np.clip(blur(spots, max(0.03 * pxcm, 1.0)) * 1.7 - spots, 0, 1)
    wet = sstep(0.3, 0.62, blur(spots, max(0.008 * pxcm, 1.0)) + 0.34 * (blur(spots, max(0.012 * pxcm, 1.0)) > 0.02) * cell)
    scat = scat * (1 - 0.35 * halo_s[..., None] * (1 - color([0.8, 0.55, 0.3])))
    dead = np.maximum(dead, wet)
    scat = scat * (1 - dead[..., None]) + (brown[None, None] * (0.75 + 0.3 * cell_k[..., None])) * dead[..., None]
    scat = np.clip(scat, 0, 1).astype(np.float32)

    # --- shadows of a neighbour leaf (a big soft fan) and a twig, painted onto the light that arrives from behind
    xx, zz = Rr * np.sin(th[None, :]), Rr * np.cos(th[None, :])
    dd = np.hypot(xx - 2.1, zz - 0.3)
    ang2 = np.arctan2(xx - 2.1, zz - 0.3)
    shade = sstep(4.9, 4.75, dd + 0.05 * big) * sstep(-0.7, -0.45, ang2) * sstep(0.95, 0.65, ang2)
    twig = np.exp(-(((xx + 0.85 * (zz - 5.9) + 1.25) / 0.09) ** 2))
    fade = 1 - 0.40 * blur(shade.astype(np.float32), 0.06 * pxcm)[..., None] * color([0.9, 1.0, 1.15])
    fade = fade * (1 - 0.22 * twig[..., None])
    scat = np.clip(scat * fade, 0, 1).astype(np.float32)

    # --- the sheet
    ripple = coarse(ny, nx, 1.6, 5.0, 2.2, seed + 20)
    wav = coarse(ny, nx, 0.4, 1.2, 2.0, seed + 21)
    amp = 0.03 + 0.32 * sstep(0.1, 1.0, (Rr - R0) / (R - R0))
    # relief: the cuticle swells between the veins, sinks at each vein and at each duct
    h = blur(0.0055 * (4 * t_mid * (1 - t_mid)) ** 0.7 - 0.0045 * vein - 0.0012 * duct + 0.0009 * cell + 0.0018 * blotch, 0.7)
    # the margin curls away
    curl = 0.34 * sstep(0.55, 0.0, dm) ** 2 * (0.25 + 0.75 * sstep(-1.0, 1.0, wav))
    a = th[None, :] + 0.008 * ripple
    x = Rr * np.sin(a)
    z = Rr * np.cos(a)
    y = amp * (ripple + 0.2 * wav) + curl + 0.62 * (Rr - R) - h + 0.024 * x**2
    P = np.stack([x, y, z], -1).astype(np.float32)
    tau = 3.5 * mask * (1 + 0.5 * vein + 1.2 * dead)
    attrs = {
        "tau": tau.astype(np.float32),
        "scat": scat,
        "trans": (1 - mask[..., None] + mask[..., None] * scat**1.5).astype(np.float32),
        "mask": mask.astype(np.float32),
    }
    return P, attrs


def trees(d, seed=3):
    """The far background: a dim emissive plate, dark canopy with a few gaps. The lens turns it into shapes without edges."""
    rng = np.random.default_rng(seed)
    n = 512
    f = fbm((n, n), n / 140.0, 5, 50, 2.4, seed)
    x = np.linspace(-70, 70, n)
    X, Z = np.meshgrid(x, x)
    base = np.clip(0.012 + 0.012 * (f + 0.4), 0.002, None)
    col = base[..., None] * color([0.48, 0.62, 0.42])
    gaps = np.zeros((n, n), np.float32)
    for _ in range(30):
        i, j = rng.integers(0, n, 2)
        gaps[i, j] = rng.uniform(0.2, 1.0) ** 2.5
    gaps = cv2.GaussianBlur(gaps, (0, 0), 1.0) * 5
    col = col + gaps[..., None] * color([1.0, 0.72, 0.34]) * 0.5
    P = np.stack([X, np.full_like(X, 330.0) + 0.0, Z + 25], -1).astype(np.float32)
    npz = os.path.join(d, "bg.npz")
    np.savez(npz, P=P, em=col.astype(np.float32))
    return npz


def main():
    q = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview")
    seed = next((int(a[7:]) for a in sys.argv if a.startswith("--seed=")), 5)
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s09_yinxing")
    os.makedirs(d, exist_ok=True)
    P, attrs = leaf(dens, seed=seed)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, **attrs)

    bg = trees(d)

    H = W * 9 / 16
    az, el = np.radians(4.0), np.radians(-11.0)
    view = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])
    target = np.array([0.0, 0.0, R - (0.5 - 0.40) * H])
    i, j = int(P.shape[0] * (R - 0.45 - R0) / (ROUT - R0)), P.shape[1] // 2
    cam = frame_camera(target, view, W, 30.0, aperture_mm=9.0, focus_point=P[i, j])
    params = {"k_tau": 1.0, "front": 0.10, "k_gloss": 0.0, "rough": 0.34, "cos_min": 0.3, "ior": 1.45}
    shader = os.path.join(ROOT, "v2", "stills", "s37_shader.py")
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "leaf", "npz": npz, "shader_py": shader, "params": params},
            {"name": "bg", "npz": bg, "material": {"Base Color": [0.0, 0.0, 0.0], "Roughness": 1.0, "Emission Color": "em", "Emission Strength": 1.0}},
        ],
        "lights": [
            {"name": "sun", "loc": [9, 30, -7], "target": [0, 0, 5.5], "size": [3.5, 3.5], "watts": 14000, "rgb": [1.0, 0.86, 0.66], "hide_in_gloss": True},
            {"name": "sky", "loc": [-16, -24, 24], "target": [0, 0, 6], "size": [34, 34], "watts": 1000, "rgb": [0.78, 0.88, 1.0], "hide_in_gloss": True},
        ],
        "world": [0.0005, 0.0007, 0.001],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "spp": {"preview": 96, "mid": 160, "final": 384},
    }
    look = {"exposure": -0.15, "contrast": 1.38, "saturation": 1.05, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "glare": 0.002}
    shoot("s09_yinxing", scene, q, tag=f"{q}.s{seed}" if seed != 5 else q, develop=look)


main()
