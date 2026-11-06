"""Shot 11: the low dome of a peachbloom (豇豆红) seal box lid, Kangxi: the crest of the dome is the arc.

    python3 -I v2/stills/s11_jiangdou.py [preview|mid|final]

Built from ref/jiangdouhong/report.md and the photos of Met 66.206.17 and CMA 1942.673 (reference only, not in the film):
- diameter 7.1-7.4 cm, height 3.5-3.9 for the whole box (museum records); the lid's dome radius here is an estimate;
- clear glaze, copper layer, clear overglaze over white porcelain (BM PDF579, 'possibly blown on'), so the medium is nearly clear with
  a little scatter: a closed glaze shell with the white body as another mesh, the copper a real sheet at the middle of the shell. Total
  thickness 0.5-0.7 mm is a proxy from Xuande jihong (Lu 2016, report 4.4), not a measurement of this ware; the sigma values are estimates;
- red of the copper: broken, mottled, flecked with pale, soft-edged at its boundary; pale pink where the copper is thin;
- moss (绿苔): dark core with a pale green halo, in clusters, denser towards the lid's edge; fine dark dust between (photo observation:
  report 2.1). All of these are stamped at continuous random positions. Spots are colour in the glaze, not relief;
- polished glass over all, in a painted room (yohen.paint_room, in place of kit.room_env): a soft window and a broad sheen, no hard-edged patch and no white line round the rim. After the blind review.
- moss: the Met box has a loose band of many dark specks; the green is a thin cloud they sit in, not a ring round each one (estimate from met_box_1.jpg).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from glazekit import balls, close_shell
import yohen
from kit import OUT, ROOT, blur, fbm, frame_camera, rank, shoot, sstep
from vessel import reflect_light_loc, view_dir, window
import kit


RC = 5.3  # dome radius, estimate
W = 4.25
DIST = 30.0
EL = 21.0
LU, V0, V1 = 5.8, -0.28, 3.5  # V: arc length from the silhouette towards the camera
SHADER = os.path.join(ROOT, "v2", "stills", "glaze_shader_v1.py")  # the shader as it was when the film's frame was rendered
GLAZE = {"kind": "glaze", "ior": 1.52, "g": 0.5, "sigma_s": [4.0, 3.5, 3.5], "sigma_a": [0.1, 0.16, 0.2]}
VIEW = view_dir(-90.0, EL)
RM = 3.2  # the dome's fall, an estimate: tighter than its plan radius, so the moss zone turns to the camera (a torus; the box's domed lid is not a sphere either)
X_ = np.array([1.0, 0.0, 0.0])
UP_ = np.cross(VIEW, X_) if np.cross(VIEW, X_)[2] > 0 else -np.cross(VIEW, X_)
C0 = -RC * UP_


def D(u, v):
    a = np.asarray(u) / RC
    b = np.asarray(v) / RM
    e = np.sin(a)[..., None] * X_ + np.cos(a)[..., None] * UP_
    return np.cos(b)[..., None] * e + np.sin(b)[..., None] * VIEW


def S(u, v, h=0.0):
    a = np.asarray(u) / RC
    e = np.sin(a)[..., None] * X_ + np.cos(a)[..., None] * UP_
    return (C0 + (RC - RM) * e + D(u, v) * (RM + np.asarray(h))[..., None]).astype(np.float32)


def thickness(v):
    return 0.052 + 0.016 * sstep(0.5, 3.0, v)


def coarse(shape, cm_per, lo, hi, beta, seed):
    g = (int((V1 - V0) / cm_per), int(LU / cm_per))
    f = fbm(g, 1.0 / cm_per, lo, hi, beta, seed)
    f = cv2.resize(f, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return blur(f, max(shape[1] / g[1], 1.0))


def stamps(shape, pxcm, xs, ys, rs, wx, wy):
    """Soft discs at continuous positions; returns the field of 1 - d/r (the top-most value) with irregular outlines from a warp."""
    ny, nx = shape
    F = np.zeros(shape, np.float32)
    for cx, cy, r in zip(xs, ys, rs):
        cx_, cy_, rp = cx * pxcm, cy * pxcm, max(r * pxcm, 0.6)
        m = int(rp * 1.8) + 3
        x0, x1, y0, y1 = int(cx_) - m, int(cx_) + m + 1, int(cy_) - m, int(cy_) + m + 1
        if x0 < 0 or y0 < 0 or x1 >= nx or y1 >= ny:
            continue
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.hypot(X + wx[y0:y1, x0:x1] * rp - cx_, Y + wy[y0:y1, x0:x1] * rp - cy_) / rp
        F[y0:y1, x0:x1] = np.maximum(F[y0:y1, x0:x1], 1 - d)
    return F


def clusters(rng, n_cl, spread, per, w_of):
    """Poisson clusters in (u, v) with their acceptance from w_of(u, v). Returns x, y (cm from the patch's corner)."""
    xs, ys = [], []
    tries = 0
    while len(xs) < n_cl and tries < n_cl * 200:
        tries += 1
        u, v = rng.uniform(-LU / 2, LU / 2), rng.uniform(V0, V1)
        if rng.random() < w_of(u, v):
            k = rng.poisson(per) + 1
            for _ in range(k):
                xs.append(u + rng.normal(0, spread) + LU / 2)
                ys.append(v + rng.normal(0, spread) - V0)
    return np.array(xs), np.array(ys)


def build(dens):
    pxcm = 560.0 * dens
    nx, ny = int(LU * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M")
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - LU / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + V0
    U, V = np.meshgrid(u, v)

    # --- copper amount. Rich bean red on the crown, falling off down the dome, broken by a blown spray's mottling
    big = coarse(shape, 0.015, 0.6, 3.0, 3.2, 111)
    mid = coarse(shape, 0.005, 0.06, 0.4, 2.6, 112)
    fine = fbm(shape, pxcm, 0.008, 0.05, 2.0, 113)
    # one edge, sweeping across the dome, not islands. V = 1 is only 6 percent of the frame below the crest, V = 2 is 25 percent: the red fills the crown, as on the Met box
    edge_v = 1.86 + 0.16 * big + 0.09 * U + 0.1 * np.sin(1.1 * U + 0.6)
    grad = (edge_v - V) / 0.3  # in units of the edge's half width
    field = grad + 0.35 * mid + 0.5 * fine  # the grain of the spray breaks the edge: the photo's flecks, about 0.3-1 mm
    red = sstep(-1.0, 1.0, field)
    # within the strong red, deeper streaks and a fine pale peach-spot break-up
    deep = sstep(1.0, 5.0, grad + 0.5 * mid)  # deeper on the crown
    wx, wy = fbm(shape, pxcm, 0.004, 0.05, 2.0, 114), fbm(shape, pxcm, 0.004, 0.05, 2.0, 115)

    rng = np.random.default_rng(116)
    # the peach points: fine, dense red dots over the pale and pale dots in the red, at continuous positions
    n = int(LU * (V1 - V0) * 340)
    x, y = rng.uniform(0, LU, n), rng.uniform(0, V1 - V0, n)
    r = np.clip(rng.lognormal(np.log(0.012), 0.5, n), 0.004, 0.05)
    pr = stamps(shape, pxcm, x, y, r, wx, wy)
    n = int(LU * (V1 - V0) * 210)
    x, y = rng.uniform(0, LU, n), rng.uniform(0, V1 - V0, n)
    r = np.clip(rng.lognormal(np.log(0.016), 0.55, n), 0.005, 0.07)
    pw = stamps(shape, pxcm, x, y, r, wx, wy)
    red = np.clip(red + 0.6 * sstep(0.0, 0.5, pr) * (0.1 + 0.9 * sstep(-2.0, 0.5, field)) * (1 - red), 0, 1)
    red = red * (1 - 0.7 * sstep(0.0, 0.55, pw) * sstep(4.0, 0.5, field))
    red = blur(red, max(0.006 * pxcm, 0.5))  # the copper diffused while firing: flecks have soft sides

    # --- moss: a loose band. Many dark specks of very different sizes in soft clusters, denser low on the dome, thinning out upwards
    band_v = lambda uu: 2.5 + 0.1 * np.sin(1.3 * uu + 1.0) + 0.05 * uu  # noqa: E731
    mossw = lambda uu, vv: 0.02 * float(vv > 1.9) + float(np.exp(-(((vv - band_v(uu)) / 0.34) ** 2)))  # noqa: E731
    x, y = clusters(rng, 760, 0.07, 1.3, mossw)
    r = np.clip(rng.lognormal(np.log(0.0105), 0.6, len(x)), 0.004, 0.03)
    wlx, wly = fbm(shape, pxcm, 0.05, 0.2, 2.0, 124), fbm(shape, pxcm, 0.05, 0.2, 2.0, 125)
    sp = stamps(shape, pxcm, x, y, r, wlx * 0.14, wly * 0.14)
    core = sstep(0.02, 0.42, blur(sp, max(0.004 * pxcm, 0.5)))  # each sits in the glaze, so its edge is soft
    # the green: a thin cloud where the specks gather, broken by its own noise. No halo round any one speck
    dens_ = blur(core, max(0.09 * pxcm, 1.0))
    dens_ = dens_ / max(float(np.percentile(dens_, 99.5)), 1e-4)
    cl = coarse(shape, 0.008, 0.08, 0.6, 2.6, 127)
    halo = 0.42 * np.clip(sstep(0.12, 0.8, dens_ + 0.32 * cl), 0, 1) * (0.45 + 0.55 * sstep(-0.6, 0.8, fbm(shape, pxcm, 0.02, 0.12, 2.0, 128))) * (1 - core)
    # dust: fine dark specks, thin everywhere, dense in the band
    x2, y2 = clusters(rng, 2600, 0.14, 0.7, lambda uu, vv: 0.02 + float(np.exp(-(((vv - band_v(uu) + 0.25) / 0.55) ** 2))))
    r2 = np.clip(rng.lognormal(np.log(0.0032), 0.45, len(x2)), 0.0014, 0.01)
    dust = sstep(0.0, 0.3, stamps(shape, pxcm, x2, y2, r2, wx * 0.2, wy * 0.2))

    # a green cast in the far low band
    # --- the sheet's filter (seen twice on the way in and out)
    T_red = np.array([0.95, 0.31, 0.25], np.float32)  # seen twice; the photo: coral, about sRGB (190, 75, 60)
    T_deep = np.array([0.78, 0.2, 0.16], np.float32)
    c = np.ones(shape + (3,), np.float32)
    amt = (red * (1 - 0.0 * deep))[..., None]
    c = c ** 1.0 * (1 - amt) + T_red * amt
    dm = (deep * red * 0.8)[..., None]
    c = c * (1 - dm) + T_deep * dm
    # the pale ground is not white but a warm pink cream (residual copper)
    pale = np.array([1.0, 0.93, 0.88], np.float32)
    c = c * pale
    # below the edge the copper thins out over a long way: pink, then cream
    blush = (sstep(-7.0, -0.5, grad) * (1 - red))[..., None]
    c = c * (1 - blush) + c * np.array([1.0, 0.87, 0.8], np.float32) * blush
    # the Met box's low band keeps a broken wash of red among the specks
    low = np.exp(-(((V - band_v(U) - 0.1) / 0.32) ** 2)) * sstep(0.1, 1.2, coarse(shape, 0.01, 0.15, 0.8, 2.6, 129) + 0.4 * fine)
    amt_low = (0.32 * low * sstep(2.2, 2.6, V) * (1 - red))[..., None]
    c = c * (1 - amt_low) + c * T_red * amt_low
    g = np.array([0.6, 0.76, 0.42], np.float32)  # olive, not apple
    c = c * (1 - halo[..., None] * 0.75) + (c * g) * (halo[..., None] * 0.75)
    # dark, but each its own: blue-grey to olive
    kt = rank(fbm(shape, pxcm, 0.03, 0.2, 2.2, 126))[..., None]
    k = np.array([0.05, 0.08, 0.1], np.float32) * (1 - kt) + np.array([0.075, 0.085, 0.045], np.float32) * kt
    c = c * (1 - core[..., None]) + k * core[..., None]
    c = c * (1 - dust[..., None] * 0.85) + np.array([0.2, 0.22, 0.09], np.float32) * (dust[..., None] * 0.85)
    tint = np.clip(c, 0.01, 1).astype(np.float32)

    # a little of the copper's light comes from large particles scattering red: the '粉' in 粉润
    milk = np.clip(0.02 + 0.05 * red, 0, 0.5) * (1 - core)
    mcol = np.stack([0.80 * np.ones_like(red), 0.35 + 0.42 * (1 - red), 0.30 + 0.40 * (1 - red)], -1).astype(np.float32)

    # --- the surface: glass with a very low undulation, very few pits
    h = 0.0032 * coarse(shape, 0.012, 0.6, 2.5, 3.0, 117) + 0.000022 * fbm(shape, pxcm, 0.03, 0.15, 2.3, 118)
    nh = int(LU * (V1 - V0) * 2.5)
    pin = np.ones(shape, np.uint8)
    pin[rng.integers(0, ny, nh), rng.integers(0, nx, nh)] = 0
    dp = cv2.distanceTransform(pin, cv2.DIST_L2, 5) / pxcm
    hp = sstep(0.009, 0.004, dp)
    h = h - 0.003 * hp
    rough = 0.045 + 0.012 * rank(coarse(shape, 0.01, 0.2, 1.0, 2.4, 119)) + 0.15 * hp

    t = thickness(V) * (1 + 0.12 * coarse(shape, 0.02, 0.5, 2.5, 3.0, 120))
    top = S(U, V, h)
    m = max(ny // 24, 8)
    vb = np.linspace(V0, V1, m, dtype=np.float32)
    Ub, Vb = np.meshgrid(u, vb)
    bot = S(Ub, Vb, -thickness(Vb) * 1.3 - 0.01)
    Pg, at = close_shell(top, bot, {"rough": rough.astype(np.float32)}, {"rough": 0.3}, outward=VIEW)

    # the sheet
    fr = 0.46 + 0.05 * coarse(shape, 0.02, 0.3, 1.5, 3.0, 121)
    Ps = S(U, V, -t * fr)

    bm, nb = max(ny // 4, 32), max(nx // 4, 32)
    ub, vbb = np.linspace(-LU / 2, LU / 2, nb, dtype=np.float32), np.linspace(V0, V1, bm, dtype=np.float32)
    Ubb, Vbb = np.meshgrid(ub, vbb)
    Pb = S(Ubb, Vbb, -cv2.resize(t, (nb, bm), interpolation=cv2.INTER_AREA))
    var = 1.0 + 0.025 * fbm((bm, nb), nb / LU, 0.1, 0.6, 2.4, 122)
    Cb = np.stack([0.96 * var, 0.9 * var, 0.85 * var], -1).astype(np.float32)
    return Pg, at["rough"], Ps, tint, milk.astype(np.float32), mcol, Pb, Cb


def bubbles(seed=123):
    rng = np.random.default_rng(seed)
    n = int(LU * (V1 - V0) * 90)
    u, v = rng.uniform(-LU / 2, LU / 2, n).astype(np.float32), rng.uniform(V0 + 0.1, V1, n).astype(np.float32)
    r = np.clip(rng.lognormal(np.log(0.0028), 0.5, n), 0.0012, 0.012).astype(np.float32)
    d = (r + 0.002 + rng.random(n) * 0.75 * thickness(v)).astype(np.float32)
    return balls(S(u, v, -d), r, nlon=10, nlat=7)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    DRAFT = q == "draft"  # full size at few samples: to judge at 100% before spending a final
    q = "final" if DRAFT else q
    dens = {"preview": 0.42, "mid": 0.65, "final": 1.0}[q]
    apex = S(np.array([0.0], np.float32), np.array([0.0], np.float32))[0]
    from vessel import cam_basis

    _f = frame_camera(apex, VIEW, W, DIST)
    _, _, _, up = cam_basis(_f)
    target = apex - up * (0.5 - 0.46) * W * 9.0 / 16.0
    focus = S(np.array([0.0], np.float32), np.array([1.4], np.float32))[0]
    cam = frame_camera(target, VIEW, W, DIST, aperture_mm=1.5, focus_point=focus)

    Pg, Rg, Ps, tint, milk, mcol, Pb, Cb = build(dens)
    d = os.path.join(OUT, "s11_jiangdou")
    os.makedirs(d, exist_ok=True)
    fs = {k: os.path.join(d, f"mesh.{k}.{q}.npz") for k in ("glaze", "body", "cu", "bubble")}
    np.savez(fs["glaze"], P=Pg, rough=Rg)
    np.savez(fs["body"], P=Pb, col=Cb)
    np.savez(fs["cu"], P=Ps, tint=tint, milk=milk, mcol=mcol)
    np.savez(fs["bubble"], P=bubbles())

    # as in the Met photo: a crisp pale window lying over the middle of the dome, and a thin line of light along the crest
    vs = 0.3
    ps = S(np.array([0.0], np.float32), np.array([vs], np.float32))[0]
    ls, _ = reflect_light_loc(ps, D(np.array([0.0]), np.array([vs]))[0], cam, 50.0)
    vw = 1.75
    pt = S(np.array([0.5], np.float32), np.array([vw], np.float32))[0]
    nrm = D(np.array([0.5]), np.array([vw]))[0]
    lw, rdir = reflect_light_loc(pt, nrm, cam, 50.0)
    print("window at", lw, "dir", rdir)
    lights = [
        {"name": "fill", "loc": (pt + np.array([-20, -46, 52])).tolist(), "target": (pt + np.array([0, -1.2, -0.3])).tolist(), "size": [60, 60], "watts": 16000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
        {"name": "over", "loc": (pt + np.array([-10, 10, 75])).tolist(), "target": (pt + np.array([0, -0.5, -0.5])).tolist(), "size": [50, 50], "watts": 7000, "rgb": [1.0, 0.985, 0.96], "hide_in_gloss": True},
    ]
    sdir = ls - ps
    sdir = sdir / np.linalg.norm(sdir)
    yohen.use_room()
    env = {"base": [0.02, 0.02, 0.022], "panels": [
        {"dir": rdir.tolist(), "w": 13, "h": 5, "L": 0.75, "rgb": [1.0, 0.985, 0.96], "soft": 2.0, "soft_w": 6, "grad": 0.5},
        {"dir": sdir.tolist(), "w": 46, "h": 7, "L": 0.3, "rgb": [0.98, 0.985, 1.0], "soft": 6, "soft_w": 22},
    ]}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "glaze", "npz": fs["glaze"], "shader_py": SHADER, "params": GLAZE},
            {"name": "body", "npz": fs["body"], "material": {"Base Color": "col", "Roughness": 0.5, "Specular IOR Level": 0.3}},
            {"name": "cu", "npz": fs["cu"], "shader_py": SHADER, "params": {"kind": "layer"}},
            {"name": "bubble", "npz": fs["bubble"], "shader_py": SHADER, "params": {"kind": "bubble"}},
        ],
        "lights": lights,
        "env": env,
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.0165, 0.016], "h": 0.62, "mottle": 0.12},
        "bounces": 48,
        "volume_bounces": 48,
        "transmission_bounces": 48,
        "diffuse_bounces": 8,
        "glossy_bounces": 8,
        "spp": {"preview": 48, "mid": 128, "final": 512},
    }
    scene["spp"] = {"final": 40} if DRAFT else scene.get("spp", {})
    shoot("s11_jiangdou", scene, q, tag="draft" if DRAFT else None, develop={"exposure": 0.6, "contrast": 1.3, "saturation": 1.04, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "vignette": 0.25})


main()
