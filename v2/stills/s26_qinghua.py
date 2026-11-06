"""Shot 26: blue and white (青花), early Ming, a jar's shoulder: the shoulder's crest is the arc, one strong spray of brush strokes below it.

    python3 -I v2/stills/s26_qinghua.py [preview|mid|final]

Cobalt goes on the raw body with a brush and the glaze over it, so the blue sits under a thick clear glaze and diffuses upward into it. So:
- a closed glaze shell with a little scatter and a faint blue-green from iron (胎釉白里泛青), the white body another mesh inside it. All sigma are
  estimates (ref/qinghua/research-spectra was not used for numbers);
- cobalt in two real sheets: sharp at the bottom of the glaze, blurred half way up (晕散);
- strokes are a brush model: each is some dozens of hairs following one spine, each hair with its own load, so the streaks run with the stroke
  and the tail breaks up (飞白); pigment pools at the wet edge and where the brush stopped; a stroke is not a filled shape;
- iron-rich Sumali cobalt (苏麻离青) precipitates dark, slightly sunken crystal patches where it lies thick: clusters at continuous positions;
- bubbles are many and small, real spheres; an orange-peel surface.

Motif: no scene, just a lotus-scroll leaf spray in the Yongle-Xuande manner, a few strong strokes. The shape is drawn from general knowledge, not
copied from a piece. Reference only, not in the film: ref/qinghua/met-18.61.2/DP-15944-021.jpg, met-14.40.276/DP-14605-071.jpg.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from glazekit import balls, close_shell
from kit import OUT, ROOT, blur, fbm, frame_camera, rank, shoot, sstep
from vessel import cam_basis, reflect_light_loc, view_dir, window

RC = 11.0  # radius of the arc: the jar's widest circle seen from its axis
RM = 4.5  # radius of the shoulder's fall from that circle: a torus, so the strokes turn towards the camera within the frame instead of being foreshortened
W = 7.6
DIST = 40.0
EL = 26.0
LU, V0, V1 = 10.6, -0.42, 6.2
SHADER = os.path.join(ROOT, "v2", "stills", "glaze_shader.py")
GLAZE = {"kind": "glaze", "ior": 1.52, "g": 0.5, "sigma_s": [4.0, 4.5, 4.5], "sigma_a": [0.42, 0.16, 0.17]}
VIEW = view_dir(-90.0, EL)
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
    return 0.075 + 0.03 * sstep(0.5, 4.0, v)


def coarse(shape, cm_per, lo, hi, beta, seed):
    g = (int((V1 - V0) / cm_per), int(LU / cm_per))
    f = fbm(g, 1.0 / cm_per, lo, hi, beta, seed)
    f = cv2.resize(f, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return blur(f, max(shape[1] / g[1], 1.0))


def spline(pts, n=400):
    """Catmull-Rom through the control points (u, v, width, load)."""
    p = np.array(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    m = len(p) - 3
    for i in range(m):
        t = np.linspace(0, 1, n // m, endpoint=i == m - 1)[:, None]
        a, b, c, d = p[i], p[i + 1], p[i + 2], p[i + 3]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t**2 + (3 * b - a - 3 * c + d) * t**3))
    return np.vstack(out)


def stroke(C, K, pxcm, pts, rng, hairs=46):
    """Add one brush stroke to the concentration field C and to the ever-touched mask K. Width and load vary along the spine."""
    sp = spline(pts)
    xy, wd, ld = sp[:, :2], np.maximum(sp[:, 2], 0.002), sp[:, 3]
    d = np.gradient(xy, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], -1) / (np.hypot(*d.T)[:, None] + 1e-9)
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    SH = 4
    k = pxcm * (1 << SH)
    x0, y0 = int((xy[:, 0].min() + LU / 2 - wd.max()) * pxcm) - 12, int((xy[:, 1].min() - V0 - wd.max()) * pxcm) - 12
    x1, y1 = int((xy[:, 0].max() + LU / 2 + wd.max()) * pxcm) + 12, int((xy[:, 1].max() - V0 + wd.max()) * pxcm) + 12
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, C.shape[1]), min(y1, C.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    acc = np.zeros((y1 - y0, x1 - x0), np.float32)
    hair_w = max(1, int(round(0.016 * pxcm)))
    for _ in range(hairs):
        t0 = rng.uniform(-1, 1)
        # each hair wanders a little across the stroke
        wander = np.interp(s, np.linspace(0, s[-1], 9), rng.normal(0, 0.05, 9))
        off = (t0 + wander).clip(-1, 1)[:, None] * wd[:, None] * nrm
        q = xy + off
        # the hair's load: runs dry towards the tail by its own schedule
        dry = rng.uniform(0.74, 1.15) * s[-1]
        lhair = ld * rng.uniform(0.7, 1.1) * sstep(dry * 1.04, dry * 0.74, s)
        # segments of even load so that cv2 can draw it
        ip = np.round((q - [-LU / 2, V0]) * k - [x0 * (1 << SH), y0 * (1 << SH)] - 0.5 * (1 << SH)).astype(np.int32)
        for a in range(0, len(ip) - 12, 12):
            v = float(np.clip(lhair[a], 0, 1))
            if v < 0.02:
                continue
            tmp = np.zeros((1, 1), np.uint8)  # keep cv2 honest about uint8 use below
            del tmp
            seg = ip[a : a + 13].reshape(-1, 1, 2)
            mask = np.zeros(acc.shape, np.uint8)
            xa, ya = seg[:, 0, 0] >> SH, seg[:, 0, 1] >> SH
            xl, xh = max(xa.min() - hair_w - 2, 0), min(xa.max() + hair_w + 3, acc.shape[1])
            yl, yh = max(ya.min() - hair_w - 2, 0), min(ya.max() + hair_w + 3, acc.shape[0])
            if xh <= xl or yh <= yl:
                continue
            sub = mask[yl:yh, xl:xh]
            cv2.polylines(sub, [seg - np.array([xl << SH, yl << SH], np.int32)], False, 255, hair_w, cv2.LINE_AA, SH)
            acc[yl:yh, xl:xh] += sub.astype(np.float32) / 255.0 * v
    # hairs touch: wash spreads between them
    acc = blur(acc, max(0.024 * pxcm, 0.5)) * (46.0 / hairs)  # a wet wash: hairs merge, only the dry tail keeps streaks
    c = acc / (0.075 * 46 / 2.0)  # about 1 where the brush was evenly loaded
    C[y0:y1, x0:x1] = np.maximum(C[y0:y1, x0:x1], 0.0) + c * 0.9
    K[y0:y1, x0:x1] = np.maximum(K[y0:y1, x0:x1], (c > 0.12).astype(np.float32))


def vein(Vn, pxcm, pts):
    """A fine line of pigment, tapering: a drawn line, not a brush of hairs. Vn takes the darkest of what crosses it."""
    sp = spline(pts, 60)
    SH = 4
    k = pxcm * (1 << SH)
    q = np.round((sp[:, :2] - [-LU / 2, V0]) * k).astype(np.int32)
    tmp = np.zeros(Vn.shape, np.uint8)
    for a in range(len(q) - 1):
        cv2.line(tmp, tuple(int(x) for x in q[a]), tuple(int(x) for x in q[a + 1]), int(np.clip(sp[a, 3], 0, 1) * 255), max(1, int(round(sp[a, 2] * 2 * pxcm))), cv2.LINE_AA, SH)
    Vn[:] = np.maximum(Vn, tmp.astype(np.float32) / 255.0)


def leaf(C, K, Vn, pxcm, base, tip, wide, bend, rng, load=1.0):
    """A leaf as a painter does it: two unequal presses of a loaded brush, then a fine dark midrib and a few side veins drawn wet over the wash, each a
    fast tapering stroke (the 'hair of white' of the first try read as a sticker)."""
    base, tip = np.array(base, float), np.array(tip, float)
    d = tip - base
    L = np.hypot(*d)
    e = d / L
    n = np.array([-e[1], e[0]])
    prof = [(0.0, 0.03, 0.8), (0.1, 0.5, 1.0), (0.32, 1.0, 1.0), (0.58, 0.78, 0.95), (0.82, 0.3, 0.85), (1.0, 0.01, 0.7)]
    for side, sw, sk in ((-1, rng.uniform(0.86, 1.0), rng.uniform(-0.04, 0.04)), (1, rng.uniform(0.62, 0.8), rng.uniform(-0.04, 0.04))):
        ctrl = []
        for f, w, l in prof:
            f2 = np.clip(f + sk * np.sin(np.pi * f), 0, 1)
            arc = bend * np.sin(np.pi * f)
            c = base + d * f2 + n * (arc + side * (w * sw * wide * 0.5 + 0.004))
            ctrl.append([c[0], c[1], w * sw * wide * 0.5, l * load])
        stroke(C, K, pxcm, ctrl, rng)
    # the midrib, a little beyond the tip, thick to thin
    rib = []
    for f, wd, l in ((0.0, 0.016, 1.0), (0.3, 0.012, 1.0), (0.65, 0.008, 0.85), (0.95, 0.002, 0.45)):
        c = base + d * f + n * (bend * np.sin(np.pi * f))
        rib.append([c[0], c[1], wd, l])
    vein(Vn, pxcm, rib)
    for f in (0.22, 0.42, 0.62):
        for side in (-1, 1):
            if rng.random() < 0.25:
                continue
            o = base + d * f + n * (bend * np.sin(np.pi * f))
            le = wide * rng.uniform(0.28, 0.42) * (1.1 - f)
            tp = o + e * le * 0.75 + n * side * le * 0.62
            mid = (o + tp) / 2 + e * le * 0.05
            vein(Vn, pxcm, [[o[0], o[1], 0.009, 0.75], [mid[0], mid[1], 0.006, 0.6], [tp[0], tp[1], 0.002, 0.3]])


def build(dens):
    pxcm = 350.0 * dens
    nx, ny = int(LU * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M")
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - LU / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + V0
    U, V = np.meshgrid(u, v)

    rng = np.random.default_rng(261)  # the same draws whatever the quality, so the composition holds
    C, K, Vn = np.zeros(shape, np.float32), np.zeros(shape, np.float32), np.zeros(shape, np.float32)

    # --- one small strong spray with white around it: a stem and five leaves, set below the crest so that the arc stays clean
    stroke(C, K, pxcm, [[-4.6, 4.6, 0.022, 1.0], [-3.0, 3.75, 0.036, 1.0], [-1.6, 3.0, 0.05, 1.0], [-0.1, 2.4, 0.044, 1.0], [1.4, 2.1, 0.036, 0.95], [2.6, 2.05, 0.026, 0.85], [3.2, 2.35, 0.016, 0.7]], rng, hairs=16)
    LEAVES = [((-1.9, 3.1), (-1.15, 1.72), 0.62, -0.2, 1.0), ((-0.9, 2.65), (1.35, 3.95), 1.02, 0.3, 1.0), ((0.4, 2.3), (1.35, 1.5), 0.4, 0.1, 0.85), ((-3.0, 3.72), (-3.65, 2.65), 0.5, 0.18, 0.95), ((1.9, 2.1), (3.4, 3.05), 0.68, -0.2, 0.9)]
    for b_, t_, w_, c_, l_ in LEAVES:
        leaf(C, K, Vn, pxcm, b_, t_, w_, c_, rng, load=l_)
    # hooked tendril, one fast stroke
    stroke(C, K, pxcm, [[3.2, 2.35, 0.016, 0.8], [3.05, 2.72, 0.018, 0.75], [2.68, 2.74, 0.016, 0.7], [2.62, 2.46, 0.012, 0.55], [2.84, 2.4, 0.007, 0.35]], rng, hairs=8)

    # the painted double line round the shoulder, one turn of the wheel: a loaded brush held still, its load varying
    uu_ = np.linspace(-LU / 2 - 0.1, LU / 2 + 0.1, 15)
    for vb_, wb_ in ((1.32, 0.012), (1.5, 0.007)):
        stroke(C, K, pxcm, [[x_, vb_ + rng.normal(0, 0.004), wb_ * rng.uniform(0.85, 1.15), rng.uniform(0.8, 1.15)] for x_ in uu_], rng, hairs=8)

    # wet edge: pigment is carried outward as the wash dries (a coffee ring); and it pools where a stroke ends
    Kb = blur(K, max(0.06 * pxcm, 0.5))  # wide enough to melt the hairs' tips: narrower left a sawtooth along every edge
    wob = fbm(shape, pxcm, 0.14, 0.8, 2.6, 262)  # the brush edge wanders slowly: shorter wavelengths read as a nibbled edge
    Km = sstep(0.41, 0.59, Kb + 0.1 * wob)
    C = blur(C, max(0.004 * pxcm, 0.4))
    edge = np.clip(Km - sstep(0.4, 0.95, blur(Km, max(0.03 * pxcm, 0.5))), 0, 1)
    tone = 0.9 + 0.22 * coarse(shape, 0.02, 0.3, 1.5, 2.8, 263) + 0.09 * fbm(shape, pxcm, 0.01, 0.07, 2.0, 264)
    conc = Km * (0.56 + 0.34 * np.clip(C, 0, 1.4)) * tone + 0.4 * edge + 0.85 * blur(Vn, max(0.002 * pxcm, 0.4)) * Km  # 分水: a nearly flat wash, darker at its drying edge

    # --- Sumali precipitates: dark crystalline clusters on thick pigment, at continuous positions
    ncl = int(420)
    xs, ys, rs = [], [], []
    for _ in range(ncl):
        cx, cy = rng.uniform(0, LU), rng.uniform(0, V1 - V0)
        i, j = int(cy * pxcm), int(cx * pxcm)
        if i >= ny or j >= nx:
            continue
        if rng.random() < float(np.clip(conc[i, j] - 0.62, 0, 1)) ** 2 * 3.0:
            for _ in range(rng.poisson(9) + 1):
                xs.append(cx + rng.normal(0, 0.07))
                ys.append(cy + rng.normal(0, 0.05))
                rs.append(np.clip(rng.lognormal(np.log(0.011), 0.55), 0.0035, 0.05))
    # and where the brush stopped: dots at the leaf tips and bases, as Xuande strokes have
    for b_, t_, w_, c_, l_ in LEAVES:
        for pt_, nn in ((b_, 10), (t_, 7)):
            cx, cy = pt_[0] + LU / 2, pt_[1] - V0
            for _ in range(nn):
                xs.append(cx + rng.normal(0, 0.035))
                ys.append(cy + rng.normal(0, 0.03))
                rs.append(np.clip(rng.lognormal(np.log(0.011), 0.5), 0.0035, 0.04))
    print("iron specks", len(xs))
    wx, wy = fbm(shape, pxcm, 0.003, 0.03, 1.6, 265), fbm(shape, pxcm, 0.003, 0.03, 1.6, 266)
    F = np.zeros(shape, np.float32)
    for cx, cy, r in zip(xs, ys, rs):
        cx_, cy_, rp = cx * pxcm, cy * pxcm, max(r * pxcm, 0.7)
        m = int(rp * 2.0) + 3
        x0, x1, y0, y1 = int(cx_) - m, int(cx_) + m + 1, int(cy_) - m, int(cy_) + m + 1
        if x0 < 0 or y0 < 0 or x1 >= nx or y1 >= ny:
            continue
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.hypot(X + wx[y0:y1, x0:x1] * rp * 0.8 - cx_, Y + wy[y0:y1, x0:x1] * rp * 0.8 - cy_) / rp
        F[y0:y1, x0:x1] = np.maximum(F[y0:y1, x0:x1], 1 - d)
    iron = sstep(0.0, 0.4, F)
    conc = conc + 0.45 * sstep(0.0, 1.0, blur(iron, max(0.012 * pxcm, 0.5)))  # cobalt gathers round the iron

    def filt(c):
        return np.stack([np.exp(-c * 2.4), np.exp(-c * 1.62), np.exp(-c * 0.78)], -1).astype(np.float32)

    # cobalt in the sheets: mostly at the bottom; a blurred part diffused half way up
    low = filt(conc * 0.88)
    high = filt(blur(conc, max(0.03 * pxcm, 0.5)) * 0.3)
    # iron: nearly black brown, a matt scatterer sitting in the glaze
    milk = iron * 0.8
    mcol = np.broadcast_to(np.array([0.07, 0.055, 0.05], np.float32), shape + (3,))
    low = low * (1 - iron[..., None] * 0.9) + np.array([0.08, 0.06, 0.06], np.float32) * (iron[..., None] * 0.9)

    # --- surface: orange peel; sunken at the iron (锡光), not over the whole
    h = 0.00012 * coarse(shape, 0.005, 0.12, 0.42, 2.2, 267) + 0.0012 * coarse(shape, 0.01, 0.8, 3.0, 3.0, 268)
    h = h - 0.0014 * blur(iron, max(0.01 * pxcm, 0.5))
    rough = 0.06 + 0.01 * rank(fbm(shape, pxcm, 0.1, 0.6, 2.4, 269)) + 0.12 * blur(iron, max(0.004 * pxcm, 0.5))

    t = thickness(V)
    top = S(U, V, h)
    m = max(ny // 24, 8)
    vb = np.linspace(V0, V1, m, dtype=np.float32)
    Ub, Vb = np.meshgrid(u, vb)
    bot = S(Ub, Vb, -thickness(Vb) * 1.25 - 0.01)
    Pg, at = close_shell(top, bot, {"rough": rough.astype(np.float32)}, {"rough": 0.3}, outward=VIEW)

    Ps_low = S(U, V, -t * 0.93)
    sub = lambda f: cv2.resize(f, (nx // 2, ny // 2), interpolation=cv2.INTER_AREA)  # noqa: E731
    Ps_high = S(sub(U), sub(V), -sub(t) * 0.5)

    bm, nb = max(ny // 4, 32), max(nx // 4, 32)
    ub, vbb = np.linspace(-LU / 2, LU / 2, nb, dtype=np.float32), np.linspace(V0, V1, bm, dtype=np.float32)
    Ubb, Vbb = np.meshgrid(ub, vbb)
    Pb = S(Ubb, Vbb, -cv2.resize(t, (nb, bm), interpolation=cv2.INTER_AREA))
    var = 1.0 + 0.02 * fbm((bm, nb), nb / LU, 0.1, 1.0, 2.4, 270)
    Cb = np.stack([0.88 * var, 0.88 * var, 0.84 * var], -1).astype(np.float32)
    meshes = {
        "low": dict(P=Ps_low, tint=low.astype(np.float32), milk=milk.astype(np.float32), mcol=np.asarray(mcol)),
        "high": dict(P=Ps_high, tint=sub(high), milk=np.zeros(Ps_high.shape[:2], np.float32), mcol=np.ones(Ps_high.shape, np.float32)),
    }
    return Pg, at["rough"], Pb, Cb, meshes




def bubbles(seed=271):
    rng = np.random.default_rng(seed)
    n = int(LU * (V1 - V0) * 120)
    # bubbles gather. Half in loose swarms, half thinly everywhere, sizes far apart
    nc = max(n // 40, 1)
    cu, cv = rng.uniform(-LU / 2, LU / 2, nc), rng.uniform(V0 + 0.1, V1, nc)
    pick = rng.integers(0, nc, n // 2)
    u = np.concatenate([rng.uniform(-LU / 2, LU / 2, n - n // 2), cu[pick] + rng.normal(0, 0.18, n // 2)]).astype(np.float32)
    v = np.clip(np.concatenate([rng.uniform(V0 + 0.1, V1, n - n // 2), cv[pick] + rng.normal(0, 0.18, n // 2)]), V0 + 0.05, V1).astype(np.float32)
    r = np.clip(rng.lognormal(np.log(0.0026), 0.85, n), 0.001, 0.016).astype(np.float32)
    d = (r + 0.002 + rng.random(n) * 0.8 * thickness(v)).astype(np.float32)
    return balls(S(u, v, -d), r, nlon=10, nlat=7)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    DRAFT = q == "draft"  # full size at few samples: to judge at 100% before spending a final
    q = "final" if DRAFT else q
    dens = {"preview": 0.55, "mid": 0.8, "final": 1.0}[q]
    apex = S(np.array([0.0], np.float32), np.array([0.0], np.float32))[0]
    _, _, _, up = cam_basis(frame_camera(apex, VIEW, W, DIST))
    target = apex - up * (0.5 - 0.46) * W * 9.0 / 16.0  # apex above the centre: at .46 from the top
    focus = S(np.array([0.0], np.float32), np.array([1.6], np.float32))[0]
    cam = frame_camera(target, VIEW, W, DIST, aperture_mm=2.5, focus_point=focus)

    Pg, Rg, Pb, Cb, ms = build(dens)
    d = os.path.join(OUT, "s26_qinghua")
    os.makedirs(d, exist_ok=True)
    fs = {}
    def save(name, **kw):  # noqa: E306
        fs[name] = os.path.join(d, f"mesh.{name}.{q}.npz")
        np.savez(fs[name], **kw)

    save("glaze", P=Pg, rough=Rg)
    save("body", P=Pb, col=Cb)
    save("bubble", P=bubbles())
    meshes = [
        {"name": "glaze", "npz": fs["glaze"], "shader_py": SHADER, "params": GLAZE},
        {"name": "body", "npz": fs["body"], "material": {"Base Color": "col", "Roughness": 0.5, "Specular IOR Level": 0.3}},
        {"name": "bubble", "npz": fs["bubble"], "shader_py": SHADER, "params": {"kind": "bubble"}},
    ]
    for k, kw in ms.items():
        save(k, **kw)
        meshes.append({"name": k, "npz": fs[k], "shader_py": SHADER, "params": {"kind": "layer"}})

    # a long soft strip reflected along the arc (the rim reads as a line of light), and a small window lower on the left, for glaze
    vs = 0.55
    ps = S(np.array([0.0], np.float32), np.array([vs], np.float32))[0]
    ls, _ = reflect_light_loc(ps, D(np.array([0.0]), np.array([vs]))[0], cam, 60.0)
    vw = 3.1
    pt = S(np.array([3.05], np.float32), np.array([vw], np.float32))[0]
    nrm = D(np.array([3.05]), np.array([vw]))[0]
    lw, rdir = reflect_light_loc(pt, nrm, cam, 55.0)
    print("window at", lw, "strip at", ls)
    lights = window("win", lw, pt, 11, 8, 2, 2, 0.5, 340, rgb=[1.0, 0.985, 0.96])
    lights += [
        {"type": "gradient", "name": "strip", "loc": ls.tolist(), "target": ps.tolist(), "size": [170, 34], "sigma": [20, 2.2], "L": 1.15, "rgb": [1.0, 0.985, 0.96]},
        {"name": "fill", "loc": (pt + np.array([-16, -48, 54])).tolist(), "target": (pt + np.array([1.5, -1.5, -0.5])).tolist(), "size": [60, 60], "watts": 30000, "rgb": [1.0, 0.985, 0.96], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "bounces": 48,
        "volume_bounces": 48,
        "transmission_bounces": 48,
        "diffuse_bounces": 8,
        "glossy_bounces": 8,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }
    scene["spp"] = {"final": 40} if DRAFT else scene.get("spp", {})
    shoot("s26_qinghua", scene, q, tag="draft" if DRAFT else None, develop={"exposure": 0.72, "contrast": 1.4, "saturation": 1.0, "black": 0.002, "grain": 1.2, "sharpen": 0.28, "halation": 0.03, "vignette": 0.28})


main()
