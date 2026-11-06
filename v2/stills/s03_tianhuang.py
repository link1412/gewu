"""Shot 3: a pebble of tianhuang (田黄), honey-coloured field stone. Rebuild: the old version had nothing in focus and its grain was noise blurred in one direction.

Method: stonelib.py. Each vertex looks through 12 real depth layers along the refracted ray. Fibres (萝卜纹) are thousands of individual streamlines through a
slow flow field, in dense bands and clear windows. Red veins (红筋) are polylines, each a dipping sheet with its depth, which bleed iron along the grain. The river skin (石皮)
stays in the hollows of the pebble and blocks light. Reflections are real (the room in scene["env"]), broken by a very low surface unevenness.

Scales are from general knowledge of the stone and are ESTIMATES (no specimen, no reference photo at time of writing): fibre width 20-60 um, cracks about 30 um, skin about 0.1 mm thick.
Internal light is an approximation of multiple scattering (see stonelib) [stand-in]. Not a volume render.

    python3 -I v2/stills/s03_tianhuang.py [flat|preview|mid|final]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, caps, fbm, frame_camera, rank, shoot, sstep
from stonelib import advect_blur, crack_paths, draw_cracks, draw_strokes, ellipsoid_exit, flow_field, refract, sample, streamlines

NAME = "s03_tianhuang"
ABC = np.array([4.6, 2.6, 3.0], np.float32)  # half-axes, cm
W = 4.2
EL = np.radians(13.0)
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)], np.float32)
DIST = 22.0
IOR = 1.56  # [estimate] fine-grained dickite, about 1.56-1.57
TARGET_Z = 3.04  # measured against apex_y
MU = np.array([0.1, 0.72, 2.0], np.float32)  # absorption on the way in and out, per cm: honey at 1-2 cm [estimate]
LAMPS = [
    (np.array([0.42, 0.62, 0.66], np.float32), np.array([2.5, 2.3, 1.7], np.float32)),  # behind, above, to the right
    (np.array([-0.3, -0.2, -0.93], np.float32), np.array([0.16, 0.08, 0.03], np.float32)),  # a weak fill from the table on the lower left
]
ZS = np.array([0.006, 0.018, 0.04, 0.07, 0.11, 0.17, 0.25, 0.36, 0.52, 0.75, 1.1, 1.6], np.float32)
MU_EFF = np.array([0.42, 0.85, 2.0], np.float32)  # how the light fades on its way in, per cm, scattering losses included: this is what draws the glow near the thin edge [estimate]
THETA0 = np.radians(-28.0)  # the grain's general direction in the chart


def layers_for(q):
    return {"flat": 300.0, "preview": 300.0, "mid": 420.0, "final": 600.0}[q]


def build(q):
    pxcm = layers_for(q)
    dens = {"flat": 0.34, "preview": 0.4, "mid": 0.6, "final": 1.0}[q]
    nc, nr = int(3500 * dens), int(2500 * dens)
    lam = np.linspace(-0.62, 0.62, nc, dtype=np.float32)
    S = np.radians(np.linspace(-26.0, 78.0, nr, dtype=np.float32))
    L_, S_ = np.meshgrid(lam, S)
    Rv = float(ABC[2])
    U, V = L_ * ABC[0], S_ * Rv  # chart, cm
    U0, V0 = float(U.min()) - 0.5, float(V.min()) - 0.5
    Wc, Hc = float(U.max() - U.min()) + 1.0, float(V.max() - V.min()) + 1.0
    nx, ny = int(Wc * pxcm), int(Hc * pxcm)
    shape = (ny, nx)
    mx, my = (U - U0) * pxcm, (V - V0) * pxcm
    mx, my = mx.astype(np.float32), my.astype(np.float32)

    # --- form: a water-worn pebble. Fixed coarse grid, so the outline holds across quality.
    d = np.stack([np.sin(L_), np.cos(L_) * -np.sin(S_), np.cos(L_) * np.cos(S_)], -1).astype(np.float32)
    n0 = d / ABC
    n0 /= np.linalg.norm(n0, axis=-1, keepdims=True)
    cg = (420, 640)
    pcg = 640 / (2 * 0.62 * ABC[0])
    big = fbm(cg, pcg, 2.6, 10.0, 3.8, 2)  # flats and swells
    mid_ = fbm(cg, pcg, 0.35, 1.5, 3.2, 3)  # hollows that a river leaves
    big = cv2.resize(big, (nc, nr), interpolation=cv2.INTER_CUBIC)
    mid_ = cv2.resize(mid_, (nc, nr), interpolation=cv2.INTER_CUBIC)
    sig = nr / 420.0 * 2.0
    big, mid_ = blur(big, sig), blur(mid_, sig)
    hollow = -mid_  # high = low-lying
    h_low = 0.012 * big + 0.003 * mid_
    P = d * ABC + n0 * h_low[..., None]

    Pu, Pv = np.gradient(P, axis=1), np.gradient(P, axis=0)
    n = np.cross(Pv, Pu)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    if (n * d).sum(-1).mean() < 0:
        n = -n
    # view
    target = np.array([0.0, 0.0, TARGET_Z], np.float32)
    loc = target + VIEW * DIST
    v = loc - P
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    cos_i = (n * v).sum(-1)
    # the limb: where the centre column turns away
    col = nc // 2
    limb_row = int(np.argmax(cos_i[:, col] > 0.0))
    limb_V = float(V[limb_row, col])
    print("limb at V", round(limb_V, 3), "row", limb_row, flush=True)

    # --- the grain
    theta = flow_field(shape, pxcm, THETA0, 101)
    band_seed = rank(advect_blur(fbm(shape, pxcm, 0.05, 1.2, 2.8, 102), theta, 0.1, pxcm, 6))
    cloud = rank(fbm(shape, pxcm, 0.5, 5.0, 3.2, 103))
    zones = sstep(0.28, 0.72, 0.55 * band_seed + 0.45 * cloud)  # dense bands and clear windows
    zones = zones**1.4

    # --- red veins: two sets of cracks with their own dip; many start at the skin
    rng = np.random.default_rng(7)
    set_a = crack_paths(shape, pxcm, theta, 201, 14, 2.6, branch=1.6, angle=0.5, starts=[(0.66, (limb_V - V0 + 0.2) / Hc), (0.72, (limb_V - V0 + 0.4) / Hc), (0.38, (limb_V - V0 + 0.3) / Hc)])
    set_b = crack_paths(shape, pxcm, theta + 1.25, 202, 12, 1.6, branch=1.0, angle=0.35)
    dip_a, dip_b = np.array([0.28, 0.55]), np.array([-0.5, 0.22])
    wc = max(1.0, 0.0018 * pxcm)

    # --- the skin: a patch that stays in the hollow; bigger at the upper right, cutting the limb, and a scrap at the lower left
    Yc, Xc = np.mgrid[:ny, :nx].astype(np.float32)
    Uc, Vc = Xc / pxcm + U0, Yc / pxcm + V0
    edge = 0.12 * fbm(shape, pxcm, 0.1, 1.2, 2.6, 301) + 0.02 * fbm(shape, pxcm, 0.012, 0.08, 2.3, 302)
    # the patches are long and lean, stretched across the grain, and a slow field pinches them into a shape no ellipse has
    ang = np.radians(-18.0)
    rx, ry = (Uc - 1.3) * np.cos(ang) + (Vc - (limb_V + 0.16)) * np.sin(ang), -(Uc - 1.3) * np.sin(ang) + (Vc - (limb_V + 0.16)) * np.cos(ang)
    rx2, ry2 = (Uc + 1.78) * np.cos(0.5) + (Vc - (limb_V + 1.5)) * np.sin(0.5), -(Uc + 1.78) * np.sin(0.5) + (Vc - (limb_V + 1.5)) * np.cos(0.5)
    pinch = np.clip(1.0 + 0.5 * fbm(shape, pxcm, 0.4, 2.2, 3.2, 304), 0.4, 2.2)
    blob = np.exp(-(((rx / 1.05) ** 2 + (ry / 0.3) ** 2) * pinch)) + 0.62 * np.exp(-(((rx2 / 0.5) ** 2 + (ry2 / 0.13) ** 2) * pinch))
    skinf = blob + edge * sstep(0.04, 0.3, blob)  # noise only bites near a patch: no stray crumbs across the stone
    skin_tex = sstep(0.36, 0.5, skinf)
    skin_thick = sstep(0.45, 0.85, skinf) * (0.6 + 0.4 * rank(fbm(shape, pxcm, 0.02, 0.3, 2.3, 303)))
    # iron from the skin soaks some way in: a wide orange fringe that follows the grain
    fringe = advect_blur(blur(skin_tex, 0.07 * pxcm), theta, 0.05, pxcm, 4)

    # --- the march
    t, cos_t = refract(n, v, 1.0 / IOR)
    tn = np.maximum(-(t * n).sum(-1), 0.2)
    tt = t + (t * n).sum(-1, keepdims=True) * -n * 1.0  # tangential part
    tt = t + n * tn[..., None]
    # tangent vector to chart: U is along +x mostly, V along the curve; use the metric of the grid
    du = float(U[0, 1] - U[0, 0])
    dv = float(V[1, 0] - V[0, 0])
    a11, a12, a22 = (Pu * Pu).sum(-1), (Pu * Pv).sum(-1), (Pv * Pv).sum(-1)
    b1, b2 = (tt * Pu).sum(-1), (tt * Pv).sum(-1)
    det = np.maximum(a11 * a22 - a12 * a12, 1e-14)
    dj, di = (a22 * b1 - a12 * b2) / det, (a11 * b2 - a12 * b1) / det
    dUdz, dVdz = (dj * du / tn).astype(np.float32), (di * dv / tn).astype(np.float32)
    dUdz, dVdz = np.clip(dUdz, -2.5, 2.5), np.clip(dVdz, -2.5, 2.5)
    del a11, a12, a22, b1, b2, det, dj, di, tt

    # chord to the far side along the ray, to stop at the back of the stone
    T = ellipsoid_exit(P * 0.999, t, ABC)

    rng_f = np.random.default_rng(55)
    acc = np.zeros(P.shape, np.float32)
    trans = np.ones(P.shape, np.float32)
    blot = blur(sstep(0.62, 0.98, rank(fbm(shape, pxcm, 0.12, 0.8, 3.0, 411))), 0.02 * pxcm)
    zs_edges = np.concatenate([[0.0], 0.5 * (ZS[1:] + ZS[:-1]), [2.2]])
    sig_base = 0.2  # background scattering per cm [estimate]
    for k, z in enumerate(ZS):
        z = float(z)
        dz = float(zs_edges[k + 1] - zs_edges[k])
        # the coarser layers need no more pixels than their blur leaves
        sc = 1 if z < 0.2 else 2
        sh = (ny // sc, nx // sc)
        pc = pxcm / sc
        th = cv2.resize(theta, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR) + 0.10 * np.sin(z * 7.0)
        zn = cv2.resize(zones, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR)
        # fibres: sparse and thin near the surface, densest around 1-3 mm, deep ones only as a veil
        per_cm2 = 2000.0 * (0.25 + 0.75 * np.exp(-((np.log(z / 0.17)) ** 2) / 1.2))
        nf = int(per_cm2 * Wc * Hc)
        lens = np.minimum(rng_f.lognormal(np.log(0.075), 0.45, nf), 0.32)
        ds = 0.02
        sl = streamlines(th, pc, nf, 0.32, ds, 1000 + k, wiggle=0.12, cross=0.3, weight=0.04 + 0.96 * zn)
        keep = np.clip((lens / ds).astype(np.int32), 3, sl.shape[1])
        lines = [sl[i, : keep[i]] for i in range(nf)]
        vals = rng_f.beta(2.0, 5.5, nf)
        wids = rng_f.choice([1, 1, 1, 1, 2], nf) if sc == 1 and pxcm >= 400 else np.ones(nf, np.int32)
        fib = draw_strokes(sh, lines, vals, wids)
        sblur = (0.0008 + 0.04 * z) * pc  # forward scattering blurs what lies deep
        fib = blur(fib, max(sblur, 0.0022 * pc))
        fib_gain = 0.085 * (0.8 + 0.02 / (0.1 + z)) / (1 + 0.5 * sblur)
        # veins as dipping sheets: thin at the surface, fading into the stone
        # a crack is a dipping sheet: each layer sees the part of the sheet in its thickness, swept along the dip, so no ghost repeats
        ca = sweep(draw_cracks(sh, set_a, offset=tuple(dip_a * z * pc), width=wc / sc), dip_a * dz * pc)
        cb = sweep(draw_cracks(sh, set_b, offset=tuple(dip_b * z * pc), width=wc / sc), dip_b * dz * pc)
        cr = blur(ca + 0.7 * cb, max(0.0009 * pc + 0.03 * z * pc, 0.4))
        fade = np.exp(-z / 0.22)
        halo = advect_blur(blur(cr, 0.006 * pc), th, 0.012, pc, 3) * 2.0
        halo2 = blur(halo, 0.03 * pc) * 1.6
        stain = (1.7 * cr + 0.22 * halo + 0.09 * halo2) * fade
        fr_ = cv2.resize(fringe, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR)
        stain = stain + 0.42 * fr_ * np.exp(-z / 0.2)
        # iron blotches, soft and unconnected to any vein, as on the Cleveland seal (ref/tianhuang)
        blot_ = cv2.resize(blot, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR)
        stain = stain + 0.09 * blot_ * np.exp(-z / 0.25)

        mapx = (mx + dUdz * z * pxcm) / sc
        mapy = (my + dVdz * z * pxcm) / sc
        rho_f = sample(fib, mapx, mapy) * fib_gain
        rho_c = sample(cr, mapx, mapy) * 0.0
        st = sample(stain, mapx, mapy)
        zn_s = sample(zn, mapx, mapy)
        del fib, cr, stain, halo, halo2, ca, cb, th

        s_along = z / tn
        inside = sstep(0.0, 0.02, T - s_along)
        X = P + t * s_along[..., None]
        E = np.zeros(P.shape, np.float32)
        for dr, I in LAMPS:
            dl = ellipsoid_exit(X, dr, ABC)
            E += I * np.exp(-dl[..., None] * MU_EFF)
        # the base stone scatters more in the dense bands
        base = sig_base * dz * (0.6 + 0.6 * zn_s)
        op = (base + rho_f + rho_c) * inside
        scat = 1.0 - np.exp(-op)
        acc += trans * (scat[..., None] * E * np.array([1.0, 0.9, 0.62], np.float32))
        tau = (dz * inside)[..., None] * MU / np.maximum(tn[..., None], 0.3) + st[..., None] * np.array([0.10, 0.72, 1.9], np.float32) + (0.25 * op)[..., None]
        trans = trans * np.exp(-tau)
        del X, E, op, scat, tau, rho_f, rho_c, st, zn_s

    # what comes all the way through: a little backlight
    glow = acc + trans * np.array([0.16, 0.12, 0.07], np.float32)

    # --- the skin at the surface: blocks what lies below, itself a dim brown crust
    sk = sample(skin_tex, mx, my)
    th_ = sample(skin_thick, mx, my)
    # the limb goes darker: where the ray has little stone to light it
    glow = glow * (0.30 + 0.70 * sstep(0.0, 0.5, T))[..., None]
    glow = glow * np.exp(-(sk * (0.35 + 3.4 * th_))[..., None] * np.array([0.7, 1.0, 1.5], np.float32))

    # --- surface relief: pits by the skin, scratches, the slight peel of a hand polish
    peel = sample(fbm(shape, pxcm, 0.02, 0.32, 2.6, 401), mx, my)
    peel2 = sample(fbm(shape, pxcm, 0.3, 1.5, 3.0, 402), mx, my)
    near = blur(skin_tex, 0.2 * pxcm)
    pits_m = np.clip(0.012 + 1.6 * near * (1 - skin_tex), 0, 1) * 0.5 + 0.5 * skin_tex
    pits = sample(caps(shape, pxcm, 34, 0.0035, 0.03, 403, mask=pits_m, slope=-2.6), mx, my)
    grit = sample(fbm(shape, pxcm, 0.005, 0.06, 1.8, 404), mx, my)
    # scratches: straight little arcs, two handling directions, more on the high points
    nsc = int(55 * Wc * Hc)
    sr = np.random.default_rng(405)
    sa = sr.uniform(0, np.pi, nsc)  # handling leaves hairlines in every direction (ref/tianhuang)
    sx, sy = sr.uniform(0, nx, nsc), sr.uniform(0, ny, nsc)
    sl_ = sr.lognormal(np.log(0.12), 0.8, nsc) * pxcm
    lines = [np.stack([np.linspace(sx[i], sx[i] + np.cos(sa[i]) * sl_[i], 6), np.linspace(sy[i], sy[i] + np.sin(sa[i]) * sl_[i], 6) + np.sin(np.linspace(0, 3, 6)) * sl_[i] * 0.02], -1).astype(np.float32) for i in range(nsc)]
    scr_t = draw_strokes(shape, lines, sr.beta(1.2, 3.0, nsc), np.ones(nsc, np.int32))
    scr = sample(scr_t, mx, my)
    # the surface trace of the veins: where a crack breaks the surface, a hairline
    tr = sample(blur(draw_cracks(shape, set_a, width=wc), 0.7), mx, my)
    h = 0.00007 * peel + 0.0013 * peel2 - 0.55 * pits - 0.0005 * scr - 0.0007 * tr + sk * (0.0012 * (0.5 + 0.5 * grit) + 0.0015 * th_)
    P = P + n * h[..., None]

    # --- pits hold dirt and see no light from inside
    pitm = sstep(0.002, 0.012, pits)
    glow = glow * (1 - 0.82 * pitm)[..., None]

    # --- surface colour and finish
    col = np.array([0.20, 0.105, 0.03], np.float32) * np.ones(P.shape, np.float32)
    skc = np.array([0.042, 0.024, 0.013], np.float32) * (0.7 + 0.6 * rank(sample(fbm(shape, pxcm, 0.01, 0.4, 2.4, 406), mx, my)))[..., None]
    col = col * (1 - sk[..., None]) + skc * sk[..., None]
    col = col * (1 - 0.7 * pitm[..., None])
    rough = 0.12 + 0.03 * rank(peel2) + 0.08 * sstep(0.2, 0.8, scr) + 0.42 * sk + 0.25 * pitm
    print("glow p50", np.median(glow, axis=(0, 1)), flush=True)
    return P.astype(np.float32), col.astype(np.float32), rough.astype(np.float32), glow.astype(np.float32), n, cos_i, limb_row


def sweep(img, vec):
    """Average an image along a short vector (px): line-kernel blur, keeping the sum."""
    L = float(np.hypot(*vec))
    if L < 1.5:
        return img
    n = int(np.ceil(L)) | 1
    k = np.zeros((n, n), np.float32)
    c = n // 2
    cv2.line(k, (int(round(c - vec[0] / 2)), int(round(c - vec[1] / 2))), (int(round(c + vec[0] / 2)), int(round(c + vec[1] / 2))), 1.0, 1, cv2.LINE_AA)
    k /= k.sum()
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT) * min(1.0, 2.0 / L + 0.3)


def flat_look(G, name):
    from darkroom import srgb_encode, tone

    img = srgb_encode(tone(G, 1.3)).astype(np.float32)
    cv2.imwrite(name, (np.clip(img, 0, 1) * 255).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    P, C, Ro, G, n, cos_i, limb = build(q)
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    if q == "flat":
        flat_look(G[limb:], os.path.join(os.environ.get("S03_SCRATCH", d), "s03_flat.jpg"))
        return
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, glow=G)
    print("verts", P.shape[0] * P.shape[1], flush=True)

    target = np.array([0.0, 0.0, TARGET_Z])
    col = P.shape[1] // 2 - int(0.05 * P.shape[1])
    # the plane of focus crosses the polish a little below the limb: the limb and the first threads are sharp, the belly falls away
    row = int(np.argmax(cos_i[:, col] > 0.3))
    focus = P[row, col]
    cam = frame_camera(target, VIEW, W, DIST, aperture_mm=3.6, focus_point=focus)
    # the window's reflection is aimed, not guessed: which way does the polish at this spot mirror, in the camera's frame (kit.room_env's az, el)
    from kit import _cam_axes

    hr = int(np.argmax(cos_i[:, int(P.shape[1] * 0.33)] > 0.36))
    hp = P[hr, int(P.shape[1] * 0.33)]
    hn = n[hr, int(P.shape[1] * 0.33)]
    hv = np.array(cam["loc"]) - hp
    hv = hv / np.linalg.norm(hv)
    hr_ = 2 * hn.dot(hv) * hn - hv
    rt, ut, bk = _cam_axes(cam)
    win_az, win_el = float(np.degrees(np.arctan2(hr_ @ rt, hr_ @ bk))), float(np.degrees(np.arcsin(np.clip(hr_ @ ut, -1, 1))))
    print("window aimed at az, el", round(win_az, 1), round(win_el, 1), flush=True)
    scene = {
        "camera": cam,
        "meshes": [{"name": "stone", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "IOR": IOR, "Emission Color": "glow", "Emission Strength": 1.0}}],
        "lights": [
            {"name": "soft", "loc": [-16, -14, 26], "target": [0, 0, 2.2], "size": [22, 14], "watts": 260, "rgb": [1.0, 0.95, 0.88], "hide_in_gloss": True},
        ],
        # a long window to the left, a warm lamp on the right, low: a room that shows in the wax and breaks on it
        "env": {"window": 2.6, "win_az": win_az, "win_el": win_el, "win_w": 15.0, "win_h": 24.0, "strip": 0.9, "strip_az": 56.0, "ceil": 0.3, "wall": 0.05},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},  # the studio's grey-black (the rule on backgrounds)
        "spp": {"preview": 48, "mid": 96, "final": 256},
    }
    shoot(NAME, scene, q, develop={"exposure": -0.4, "contrast": 1.4, "saturation": 1.0, "black": 0.0, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "vignette": 0.2})


main()
