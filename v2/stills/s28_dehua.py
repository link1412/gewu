"""Shot 28: Dehua white porcelain (德化白瓷, blanc de Chine), the drapery of a Guanyin at the shoulder: the shoulder is the arc, folds fall from it.

    python3 -I v2/stills/s28_dehua.py [preview|mid|final]

Dehua is a translucent, nearly glassy body under a thin glaze of the same colour, so the whole figure is a medium, not a shell over an opaque body:
a closed volume about 1.5 cm deep, strongly scattering, with very slight warm absorption; deep folds warm up because the light in them has
travelled further. All sigma, and the fold sizes, are estimates (no reference photo in ref/ for this ware, none compared).

Folds: modelled in clay, not by noise. A dozen hand-placed sweeps, each a ridge with a crisp crest; they meet in sharp creases at the valleys (a
smooth max of the ridges). One robe edge lies over the folds with a rolled lip and an incised line, so that there is a hard edge to focus on: a whole frame of
soft gradients read as out of focus. Glaze thin and satin, with a few pinholes and iron specks.

Reworked after blind review ("soft bands, as if it had no surface, no detail at all") against ref/dehua at 100%. The real ware is glossy, not satin: crisp small window reflections, broken by a slow waviness of the glaze;
modelled edges with rolled lips, overlapping layers of cloth with a dark crease under each; glaze pooling grey-green-cream in the recesses; applied beads (a strand of 璎珞 and a small flower); a hairline firing crack, pinholes. So now:
- the height field has layers of cloth (a lapel over the sleeve, a second hem), each with a lip and an undercut, on top of the old sweeps;
- a beaded strand and a small applied flower, each bead its own size, the glaze filling in round its foot;
- real gloss (roughness about .05) reflecting the room (env in looks.json, with a bright window);
- three scales of glaze waviness; pooled tint (s28_shader.py) by cavity; a hairline crack made by a random walk.
Sizes of beads, lips and creases are estimates by eye from those photographs, nothing is measured on a piece. The motif is generic, not copied from any piece. Pooled tint is painted by cavity and is not a thick glaze layer.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from glazekit import balls, close_shell
from kit import OUT, ROOT, blur, fbm, frame_camera, rank, shoot, sstep
from vessel import cam_basis, reflect_light_loc, view_dir

RC = 7.2
W = 6.0
DIST = 34.0
EL = 20.0
LU, V0, V1 = 9.0, -0.4, 5.0
SHADER = os.path.join(ROOT, "v2", "stills", "s28_shader.py")
BODY = {"ior": 1.5, "g": 0.3, "sigma_s": [42.0, 42.0, 42.0], "sigma_a": [0.015, 0.035, 0.10]}
VIEW = view_dir(-90.0, EL)
RM = 3.6  # the shoulder's fall: a torus, so the drapery turns to the camera within the frame instead of being foreshortened against the crest
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


# the folds: a family of sweeps falling from the shoulder and fanning a little, each with its own width and height, plus a few
# short pinches and a sash lying across them. (u, v) control points in cm; fixed seed, so the composition is fixed.
def _folds():
    """Cloth falling from the shoulder: long sweeps, nearly parallel, leaning together to the right and curving as they fall, unequal in width and height, some of
    them merging; a few short tucks. (A fan from two gathers with low ridges was tried: it read as smoke; round ridges read as a jelly mould.)"""
    rng = np.random.default_rng(280)
    out = []
    u0 = -6.6
    while u0 < 5.6:
        a, w = rng.uniform(0.15, 0.29), rng.uniform(0.3, 0.52)
        st = rng.uniform(0.75, 1.5)
        lean = 0.22 + 0.05 * u0
        pts = []
        for f in (0.0, 0.2, 0.45, 0.72, 1.0):
            vv = st + (5.2 - st) * f
            pts.append((u0 + lean * (vv - st) + 0.28 * np.sin(1.1 * vv + u0), vv))
        out.append((pts, a, w))
        u0 += rng.uniform(0.5, 1.1)
    for _ in range(8):
        cu, cv_ = rng.uniform(-4.0, 4.0), rng.uniform(1.6, 3.6)
        a = rng.uniform(0.5, 1.1)
        d = np.array([np.cos(a), np.sin(a)])
        pts = [(cu + d[0] * x, cv_ + d[1] * x) for x in (-0.5, -0.15, 0.2, 0.55)]
        out.append((pts, rng.uniform(0.05, 0.1), rng.uniform(0.12, 0.2)))
    return out


FOLDS = _folds()


def catmull(p, n=300):
    p = np.array(p, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    m = len(p) - 3
    for i in range(m):
        t = np.linspace(0, 1, n // m, endpoint=i == m - 1)[:, None]
        a, b, c, d = p[i], p[i + 1], p[i + 2], p[i + 3]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t**2 + (3 * b - a - 3 * c + d) * t**3))
    return np.vstack(out)


def ridges(pxcm_c=80.0):
    """Fold heights on a fixed coarse grid, so that composition is the same in every quality. Soft max of ridges, sharp in the creases."""
    nx, ny = int(LU * pxcm_c), int((V1 - V0) * pxcm_c)
    shape = (ny, nx)
    wvar = fbm(shape, pxcm_c, 0.8, 3.5, 3.2, 281)
    avar = fbm(shape, pxcm_c, 0.8, 3.5, 3.2, 282)
    k = 55.0  # how sharply ridges meet (1/cm)
    acc = np.ones(shape, np.float32)
    U, V = np.meshgrid((np.arange(nx, dtype=np.float32) + 0.5) / pxcm_c - LU / 2, (np.arange(ny, dtype=np.float32) + 0.5) / pxcm_c + V0)
    # Distances are analytic, not a distance transform: nearest-point labels on a coarse grid left rungs and a chevron where each crest began.
    for pts, A, w in FOLDS:
        c = catmull(pts)
        if A > 0.12:  # a sweep is a function of v: it surfaces gradually over a long run, narrow at first, and has no tip
            st, en = c[0, 1], c[-1, 1]
            uc = np.interp(V.ravel(), c[:, 1], c[:, 0]).reshape(shape)
            d = np.abs(U - uc)
            env = sstep(st - 0.2, st + 1.5, V) * sstep(en + 0.4, en - 0.8, V)
            ww = w * (0.45 + 0.55 * env) * (1 + 0.18 * wvar)
        else:  # a tuck: a short straight pinch in its own axes
            e0, e1 = c[0], c[-1]
            L = float(np.hypot(*(e1 - e0)))
            dx, dy = (e1 - e0) / L
            mx, my = (e0 + e1) / 2
            x = (U - mx) * dx + (V - my) * dy
            d = np.abs(-(U - mx) * dy + (V - my) * dx)
            env = sstep(L * 0.75, L * 0.1, np.abs(x))
            ww = w * (0.6 + 0.4 * env) * (1 + 0.18 * wvar)
        rd = np.minimum(d / ww, 1.3)
        # a crisp crest over wide concave flanks, the way cloth folds: not a puffed round
        h = A * (1 + 0.15 * avar) * env * np.maximum(1 - rd, 0.0) ** 1.05
        acc = acc + np.exp(k * h)
    H = np.log(acc) / k
    H = blur(H, 0.6)
    return H.astype(np.float32)


def build(dens):
    pxcm = 390.0 * dens
    nx, ny = int(LU * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M")
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - LU / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + V0
    U, V = np.meshgrid(u, v)

    H = cv2.resize(ridges(), (nx, ny), interpolation=cv2.INTER_CUBIC)
    H = blur(H, max(pxcm / 80.0 * 0.35, 1.0))
    # folds die away at the crest of the shoulder, so that the arc stays clean
    fade = sstep(0.25, 1.0, V)
    H = H * fade

    # --- layers of cloth, each with a rolled lip and an undercut. uE(v): an edge in the plane; layer(): + side is on top
    def layer(sd, a, lip, on):
        """A sheet lying over what is on its - side: a step up of height a, a rolled lip just inside the edge, a dark crease just outside."""
        return on * (a * sstep(-0.012, 0.03, sd) + lip * np.exp(-(((sd - 0.05) / 0.042) ** 2)) - 0.016 * np.exp(-(((sd + 0.018) / 0.016) ** 2)))

    wob1 = cv2.resize(fbm((64, 64), 8.0, 1.5, 6.0, 3.0, 290), (nx, ny), interpolation=cv2.INTER_CUBIC)
    # the lapel: comes over the shoulder from the upper right, falls to the lower left
    uE = 1.55 - 0.86 * V + 0.07 * np.sin(1.4 * V + 0.7) + 0.05 * wob1
    sd_l = (U - uE) / np.hypot(1.0, 0.86)
    wid = 1.02 + 0.09 * np.sin(1.1 * V + 2.0) + 0.05 * wob1
    on = sstep(0.05, 0.75, V)
    # right of the lapel the under-robe is plain: the sweeps die out there
    H = H * (0.26 + 0.74 * sstep(0.3, -0.2, sd_l - wid))
    # the band itself sags a little across, as a fold of cloth does
    t = np.clip(sd_l / wid, 0.0, 1.0)
    H = H * (1.0 - 0.8 * sstep(-0.1, 0.1, sd_l) * sstep(0.2, -0.1, sd_l - wid))
    H = H + on * sstep(-0.02, 0.03, sd_l) * sstep(0.03, -0.02, sd_l - wid) * (0.13 - 0.026 * np.sin(np.pi * t) + 0.018 * wob1)
    H = H + on * (0.015 + 0.007 * wob1) * (np.exp(-(((sd_l - 0.05) / (0.04 + 0.012 * wob1)) ** 2)) + np.exp(-(((sd_l - wid + 0.06) / (0.05 - 0.012 * wob1)) ** 2)))  # the two rolled edges
    H = H - on * (0.018 * np.exp(-(((sd_l + 0.02) / 0.018) ** 2)) + 0.016 * np.exp(-(((sd_l - wid - 0.022) / 0.018) ** 2)))  # creases on both sides
    # an incised line along the lapel, cut by hand: it wanders a little and its depth comes and goes
    d_in = sd_l - 0.17 - 0.012 * np.sin(2.3 * V + 1.0) - 0.008 * wob1
    H = H - on * (0.0055 + 0.002 * wob1) * np.exp(-((d_in / 0.012) ** 2))
    # a second hem over the sleeve at the left
    uH = -3.05 + 0.62 * V + 0.1 * np.sin(1.2 * V) + 0.05 * wob1
    H = H + layer((U - uH) / np.hypot(1.0, 0.62), 0.05, 0.016, sstep(0.3, 1.1, V) * sstep(0.02, -0.25, sd_l))

    # --- applied beads: a strand on the under-robe, a small flower. Each bead its own size; the glaze fills in round its foot
    rng_b = np.random.default_rng(291)
    strand = catmull([(2.95, 0.72), (2.42, 1.2), (1.82, 1.82), (1.5, 2.36), (1.4, 2.95), (1.55, 3.7)], 900)
    seg = np.r_[0.0, np.cumsum(np.hypot(*np.diff(strand, axis=0).T))]
    caps = []
    pos = 0.05
    k = 0
    while pos < seg[-1]:
        r = rng_b.uniform(0.046, 0.066) if k % 9 else 0.086
        pos += r
        caps.append((float(np.interp(pos, seg, strand[:, 0])) + rng_b.normal(0, 0.006), float(np.interp(pos, seg, strand[:, 1])) + rng_b.normal(0, 0.006), r))
        pos += r * rng_b.uniform(0.96, 1.1)
        k += 1
    # the flower: a raised heart and six petals pressed from a sprig mould, not quite regular
    fc = (1.86, 2.62)
    caps.append((fc[0], fc[1], 0.105))
    for i in range(6):
        ang = i * np.pi / 3 + rng_b.normal(0, 0.09) + 0.3
        rp = rng_b.uniform(0.085, 0.11)
        caps.append((fc[0] + (0.15 + rng_b.normal(0, 0.008)) * np.cos(ang), fc[1] + (0.15 + rng_b.normal(0, 0.008)) * np.sin(ang), rp))
    beads = np.zeros(shape, np.float32)
    for cx, cy, r in caps:
        ix0, ix1 = max(int((cx + LU / 2 - 1.4 * r) * pxcm), 0), min(int((cx + LU / 2 + 1.4 * r) * pxcm) + 2, nx)
        iy0, iy1 = max(int((cy - V0 - 1.4 * r) * pxcm), 0), min(int((cy - V0 + 1.4 * r) * pxcm) + 2, ny)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        d2 = (U[iy0:iy1, ix0:ix1] - cx) ** 2 + (V[iy0:iy1, ix0:ix1] - cy) ** 2
        beads[iy0:iy1, ix0:ix1] = np.maximum(beads[iy0:iy1, ix0:ix1], 0.8 * np.sqrt(np.maximum(r * r - d2, 0.0)))
    beads = blur(beads, 0.007 * pxcm)
    H = H + beads

    # --- a hairline firing crack: a random walk with a sudden change of mind, narrow, a little open
    rng_c = np.random.default_rng(292)
    pts = [np.array([-2.1, 2.9])]
    ang = -1.2
    for _ in range(46):
        ang += rng_c.normal(0, 0.12) + (rng_c.random() < 0.08) * rng_c.normal(0, 0.65)
        pts.append(pts[-1] + 0.05 * np.array([np.cos(ang), np.sin(ang)]))
    pts = np.array(pts)
    cr = np.zeros(shape, np.uint8)
    cv2.polylines(cr, [np.c_[(pts[:, 0] + LU / 2) * pxcm, (pts[:, 1] - V0) * pxcm].astype(np.int32)], False, 255, 1, cv2.LINE_AA)
    crack = blur(cr.astype(np.float32) / 255.0, 0.003 * pxcm + 0.4)

    # --- the state of the glaze: slow waves that break the highlights, a fine orange peel, pinholes
    wave = 0.0030 * fbm(shape, pxcm, 0.35, 1.6, 2.6, 283) + 0.00065 * fbm(shape, pxcm, 0.09, 0.33, 2.4, 293)
    wave = wave * (0.75 + 0.25 * rank(fbm(shape, pxcm, 0.6, 3.0, 2.6, 294)))
    h = H + wave + 0.00011 * fbm(shape, pxcm, 0.03, 0.09, 1.6, 295) - 0.0022 * crack
    rng = np.random.default_rng(284)
    npin = int(LU * (V1 - V0) * 5)
    pin = np.ones(shape, np.uint8)
    # pinholes gather where the glaze ran thin and on the undercuts
    py, px = rng.integers(0, ny, npin), rng.integers(0, nx, npin)
    pin[py, px] = 0
    dp = cv2.distanceTransform(pin, cv2.DIST_L2, 5) / pxcm
    rp = 0.003 + 0.007 * rank(fbm(shape, pxcm, 0.1, 0.4, 2, 285))
    hp = sstep(1.0, 0.5, dp / rp)
    h = h - 0.005 * hp
    rough = 0.042 + 0.022 * rank(fbm(shape, pxcm, 0.15, 1.2, 2.6, 286)) + 0.25 * hp + 0.15 * crack

    # glaze runs off the crests and collects in the hollows: a faint grey-green-cream by depth of cavity. Painted (see the docstring)
    cav = np.clip(blur(H, 0.12 * pxcm) - H, 0.0, 0.05) / 0.05
    pool = np.exp(-(cav[..., None] ** 0.8) * np.array([0.16, 0.15, 0.30], np.float32)) * (1.0 - crack[..., None] * np.array([0.1, 0.11, 0.12], np.float32))
    pool = pool.astype(np.float32)

    top = S(U, V, h)
    m = max(ny // 24, 8)
    vb = np.linspace(V0, V1, m, dtype=np.float32)
    Ub, Vb = np.meshgrid(u, vb)
    bot = S(Ub, Vb, np.full_like(Ub, -1.6))
    Pg, at = close_shell(top, bot, {"rough": rough.astype(np.float32), "pool": pool}, {"rough": 0.3, "pool": 1.0}, outward=D(u[nx // 2], v[ny // 2]))  # the local normal: a fold at the test point can tilt away from the camera
    return Pg, at["rough"], at["pool"]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    DRAFT = q == "draft"  # full size at few samples: to judge at 100% before spending a final
    q = "final" if DRAFT else q
    dens = {"preview": 0.42, "mid": 0.65, "final": 1.0}[q]
    Pg, Rg, Pl = build(dens)
    d = os.path.join(OUT, "s28_dehua")
    os.makedirs(d, exist_ok=True)
    fs = os.path.join(d, f"mesh.body.{q}.npz")
    np.savez(fs, P=Pg, rough=Rg, pool=Pl)

    apex = S(np.array([0.0], np.float32), np.array([0.0], np.float32))[0]
    _, _, _, up = cam_basis(frame_camera(apex, VIEW, W, DIST))
    target = apex - up * (0.5 - 0.46) * W * 9.0 / 16.0
    focus = S(np.array([0.2], np.float32), np.array([1.5], np.float32), np.array([0.13], np.float32))[0]
    cam = frame_camera(target, VIEW, W, DIST, aperture_mm=7.0, focus_point=focus)

    A = apex
    pt = S(np.array([-1.0], np.float32), np.array([2.2], np.float32), np.array([0.2], np.float32))[0]
    nrm = D(np.array([-1.0]), np.array([2.2]))[0]
    lw, r = reflect_light_loc(pt, nrm, cam, 50.0)
    lights = [
        # key: raking, from the upper left and a little behind: carves the folds, shadows fall to the lower right
        {"name": "key", "loc": (A + np.array([-40, -30, 28])).tolist(), "target": (A + np.array([0, -2, -1.5])).tolist(), "size": [40, 46], "watts": 30000, "rgb": [1.0, 0.97, 0.93]},
        # fill: very low, so the shadows hold but stay warm
        {"name": "fill", "loc": (A + np.array([20, -50, 22])).tolist(), "target": (A + np.array([0, -2, -1.5])).tolist(), "size": [50, 50], "watts": 7000, "rgb": [1.0, 0.97, 0.92], "hide_in_gloss": True},
        # behind the shoulder: glows through the thin crest
        {"name": "back", "loc": (A + np.array([6, 30, 9])).tolist(), "target": A.tolist(), "size": [26, 7], "watts": 5500, "rgb": [1.0, 0.93, 0.84], "hide_in_gloss": True},
        {"type": "gradient", "name": "sheen", "loc": lw.tolist(), "target": pt.tolist(), "size": [150, 70], "sigma": [30, 9], "L": 0.7, "rgb": [1.0, 0.98, 0.95]},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "body", "npz": fs, "shader_py": SHADER, "params": BODY}],
        "lights": lights,
        "bounces": 128,
        "volume_bounces": 128,
        "transmission_bounces": 64,
        "glossy_bounces": 4,
        "diffuse_bounces": 4,
        "spp": {"preview": 48, "mid": 128, "final": 384},
    }
    scene["spp"] = {"final": 40} if DRAFT else scene.get("spp", {})
    shoot("s28_dehua", scene, q, tag="draft" if DRAFT else None, develop={"exposure": -0.2, "wb": [1.01, 1.0, 0.97], "contrast": 1.28, "saturation": 1.03, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.04, "vignette": 0.25})


main()
