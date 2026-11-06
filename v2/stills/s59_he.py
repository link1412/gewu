"""Shot 59: one spread wing of a crane, Suzhou embroidery on dark satin, seen near. The wing's leading edge is the arc across the frame. No head, neck or legs.

    python3 -I v2/stills/s59_he.py flat                the threads drawn in 2D, no render: out/v2/s59_suxiu_take_e/flat.jpg
    python3 -I v2/stills/s59_he.py crop X Y [W]        a small patch at final scale
    python3 -I v2/stills/s59_he.py preview|mid|final   final goes to cand.* in out/v2/s59_suxiu_take_e

Top to bottom: tiny coverts along the edge, two rows of larger coverts, long flight feathers going to ink and out of the frame. Each row lies on the one below.

The stitch (general knowledge, not measured from a piece): a feather is a unit. A shaft first, a little brighter and thicker. Threads leave it on the slant, the two sides mirrored like a herringbone, so that under one light one side is bright and the other dark: the sheen flips at the shaft. Colour moves root to tip in ranks of long and short stitches (套针) between neighbouring dyes. The rim is open (虚针): thread ends of uneven length lying on the next feather, and where a thread reaches bare satin it goes in at a needle hole. It must read as embroidery, not feather: no barbs or barbules anywhere.

What is what:
- Measured: arc by tools/arc.py; thread width in px follows from the numbers below (0.0085 cm at 269 px/cm is 2.3 px).
- General knowledge, not measured: the stitch above.
- Direction from the coordinator, not measured from any piece: the palette. Each dye below is by eye.
- Estimates, by eye: frame width, feather sizes and fan, stitch lengths, roughness and lobe weights, heights of the rows.
- Stand-ins: one tube is one split thread, its filaments are not modelled (see s59_silk_shader.py); the satin's weave is a repeating bump; the needle holes are dark dimples in the ground; each feather is a tilted plate, not padded by hand.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, fbm, frame_camera, shoot, sstep
from s59_silk import faces, lerp_table, lin, table
from vessel import fit_arc, project, view_dir

NAME, RUN = "s59_suxiu", "s59_suxiu_take_e"
HERE = os.path.dirname(os.path.abspath(__file__))
SHADER = os.path.join(HERE, "s59_silk_shader.py")
SEED = 59
W, EL, DIST, APERTURE = 9.5, 74.0, 36.0, 8.0
APEX_Y = 0.49
RB = 13.1  # the edge's radius, cm: sagitta in widths = (RB - sqrt(RB^2 - (W/2)^2)) * sin(EL) / W
TW = 0.0085  # a thread's width, cm
ACROSS = 0.0048  # spacing square to the threads, cm: floss spreads flat and covers
PSI = 32.0  # threads leave the shaft at this angle
K_ = 1.0 / np.tan(np.radians(PSI))
SWEEP = 14.0  # feathers lean this far toward the wing's outer end
FAN = 11.0  # and fan out by this much at the frame's sides
FOCUS = np.array([0.0, 12.0, 0.0])
WARP, PICK = 0.0045, 0.003
GROUND = lin((26, 44, 70)) * 0.62  # deep stone blue: lighter and colder than the ink feathers, so that they part from it, and whites stand out without glare

# ink to ivory, sRGB, by eye: 墨, 墨灰, 鸽灰, 银灰, 月白, 象牙. Neighbours are close
DYES = lin(((20, 20, 24), (36, 36, 42), (58, 58, 66), (84, 85, 92), (112, 114, 120), (140, 143, 148), (168, 171, 174), (192, 196, 198), (214, 219, 221), (231, 232, 226), (244, 241, 231)))
WARM, COOL = np.array([1.015, 1.0, 0.965], np.float32), np.array([0.975, 1.0, 1.035], np.float32)
ROWS = [  # D: root's depth below the edge, gap along the edge, L, half width, extra sweep, z of the plate; lowest first
    dict(D=0.8, gap=1.2, L=3.5, hw=0.82, sw=0.0, z=0.006),
    dict(D=0.5, gap=1.05, L=1.3, hw=0.58, sw=3.0, z=0.022),
    dict(D=0.15, gap=0.8, L=1.0, hw=0.47, sw=6.0, z=0.038),
    dict(D=0.12, gap=0.3, L=0.46, hw=0.17, sw=30.0, z=0.046),
    dict(D=0.03, gap=0.26, L=0.5, hw=0.18, sw=26.0, z=0.052),
]
TONES = [lambda u: np.interp(u, [0.0, 0.16, 0.3, 0.45, 0.62, 1.0], [0.8, 0.86, 0.72, 0.42, 0.1, 0.02]),
         lambda u: np.interp(u, [0.0, 0.55, 0.85, 1.0], [0.62, 0.8, 0.93, 0.98]),
         lambda u: np.interp(u, [0.0, 0.5, 0.85, 1.0], [0.68, 0.86, 0.97, 1.0]),
         lambda u: np.interp(u, [0.0, 0.5, 1.0], [0.82, 0.94, 1.0]),
         lambda u: np.interp(u, [0.0, 0.5, 1.0], [0.84, 0.95, 1.0])]
MX0, MY0, MP = -7.5, 7.0, 90.0
MS = (int(8.0 * MP), int(15.0 * MP))


def cloth(x, y):
    return 0.008 * np.sin(0.6 * x + 0.3 * y + 0.6) + 0.004 * np.sin(1.2 * y - 0.5 * x + 2.0)


def wfun(u, hw, seed):
    """A rounded feather: narrow at the root, full, then a round tip. A slow unevenness; a hand's, not a template's."""
    base = np.sin(np.pi / 2 * np.clip(u / 0.14, 0, 1)) ** 0.6
    tip = np.sqrt(np.maximum(1 - np.maximum((u - 0.45) / 0.55, 0.0) ** 2.6, 0.0))
    return hw * base * tip * (1 + 0.035 * np.sin(u * 7.0 + seed) + 0.02 * np.sin(u * 17.0 + 2 * seed))


def layout(rng):
    """Each feather: root, direction, size. Laid along arcs under the edge, not on a grid."""
    out = []
    for k, r in enumerate(ROWS):
        n = np.arange(-7.5, 7.5, r["gap"]) + rng.uniform(0, r["gap"])
        for x_ in n:
            s = x_ + rng.normal(0, (0.09 if k < 3 else 0.22) * r["gap"])
            th = np.pi / 2 - s / RB
            rr = RB - r["D"] - rng.normal(0, 0.05 * r["L"])
            root = np.array([rr * np.cos(th), rr * np.sin(th)])
            ang = -90.0 + SWEEP + r["sw"] + FAN * np.clip(s / 4.75, -1.6, 1.6) + rng.normal(0, 3.2 if k < 3 else 6.0)
            scale = rng.uniform(0.88, 1.13)
            out.append(dict(k=k, root=root, a=np.radians(ang), L=r["L"] * scale, hw=r["hw"] * rng.uniform(0.9, 1.1), bow=rng.normal(0, 0.05), z=r["z"], seed=rng.uniform(0, 6.28), tilt=rng.uniform(0.004, 0.008) * (1 if k < 3 else 0.4), warm=rng.uniform(-1, 1)))
    return out


def outline(f):
    u = np.linspace(0, 1, 120)
    w = wfun(u, f["hw"], f["seed"])
    U = np.concatenate([u * f["L"], (u * f["L"])[::-1]])
    V = np.concatenate([w, -w[::-1]])
    return world(f, U, V)


def world(f, U, V):
    d = np.array([np.cos(f["a"]), np.sin(f["a"])])
    n = np.array([-d[1], d[0]])
    V2 = V + f["bow"] * f["L"] * (U / f["L"]) ** 2
    return np.stack([f["root"][0] + d[0] * U + n[0] * V2, f["root"][1] + d[1] * U + n[1] * V2], -1)


def to_map(p):
    return np.round((p - [MX0, MY0]) * MP * 16).astype(np.int32)


def sample(m, x, y):
    ix = np.clip(((x - MX0) * MP).astype(np.int32), 0, MS[1] - 1)
    iy = np.clip(((y - MY0) * MP).astype(np.int32), 0, MS[0] - 1)
    return m[iy, ix]


def shade(t, warm, rng):
    t = np.clip(t + rng.normal(0, 0.012, np.shape(t)), 0, 1)
    i = np.clip(np.floor(t * (len(DYES) - 1) + rng.random(np.shape(t))).astype(int), 0, len(DYES) - 1)
    c = DYES[i] * (1.0 + 0.016 * rng.normal(0, 1, np.shape(t)))[..., None]
    m = np.clip(0.5 + (0.5 * warm + rng.normal(0, 0.18, np.shape(t))) * sstep(0.45, 0.8, t), 0, 1)[..., None]  # warm and cool whites; the inks stay neutral
    return c * (WARM * m + COOL * (1 - m))


def vane(f, side, zm, occ, cull, nseg, rng):
    """One side of a feather: lines of constant a run out from the shaft on the slant; along each, ranks of long and short stitches."""
    L, hw, tone = f["L"], f["hw"], TONES[f["k"]]
    a = np.arange(-K_ * hw * 1.1, L, ACROSS * np.sqrt(1 + K_ * K_))
    b = np.linspace(0, hw * 1.15, 300)[:, None]
    uu = (a[None] + K_ * b) / L
    ins = (uu >= 0) & (uu <= 1) & (b <= wfun(np.clip(uu, 0, 1), hw, f["seed"]))
    ok = ins.any(0)
    a = a[ok]
    ins = ins[:, ok]
    bs = b[np.argmax(ins, 0), 0]
    be = b[len(b) - 1 - np.argmax(ins[::-1], 0), 0]
    nt = len(a)
    alt = np.where(np.arange(nt) % 2 == 0, 1.0, -1.0)
    small = f["k"] >= 3
    rh = 0.04 if small else 0.085
    jit = rng.uniform(-0.03, 0.03, nt) * (0.4 if small else 1.0)
    Ps, Ts, Es = [], [], []
    r = 0
    while True:
        st = bs + r * rh - 0.3 * rh * alt + rng.uniform(-0.3, 0.3, nt) * rh
        ln = rh * np.where(alt > 0, rng.uniform(1.8, 2.5, nt), rng.uniform(1.3, 1.8, nt))
        en = st + ln
        be_j = be + jit
        last = en >= be_j
        en = np.minimum(en, be_j)
        st = np.maximum(st, bs + 0.004)
        keep = (en - st) > 0.012
        if (st > be_j).all():
            break
        r += 1
        if not keep.any():
            continue
        q = np.linspace(0, 1, nseg + 1)[None]
        ai, si, ei = a[keep], st[keep], en[keep]
        lean = rng.normal(0, 0.0035, len(ai))[:, None] * np.sin(np.pi * q)
        bb = si[:, None] + (ei - si)[:, None] * q
        U = ai[:, None] + K_ * bb
        V = side * (bb + 0.006) + lean
        p = world(f, U, V)
        x, y = p[..., 0], p[..., 1]
        if not ((x > cull[0]) & (x < cull[1]) & (y > cull[2]) & (y < cull[3])).any():
            continue
        wv = np.clip(np.abs(V) / hw, 0, 1)
        z = f["z"] + side * f["tilt"] * wv + 0.006 * (1 - wv * wv) + cloth(x, y)
        # the thread's own small arch; a rim thread settles on what is under it, or goes into the satin
        z = z + 0.0008 * sstep(0, 0.2, q) * sstep(1, 0.8, q) + rng.normal(0, 0.0002, len(ai))[:, None]
        lasti = last[keep]
        under = sample(zm, x[:, -1], y[:, -1]) + cloth(x[:, -1], y[:, -1])
        bare = sample(occ, x[:, -1], y[:, -1]) == 0
        target = np.where(bare, cloth(x[:, -1], y[:, -1]) - 0.003, under + 0.0012)
        f_ = sstep(0.62, 1.0, q) * lasti[:, None]
        z = z * (1 - f_) + target[:, None] * f_
        mid = U[:, nseg // 2] / L
        t = tone(np.clip(mid, 0, 1)) + 0.05 * (np.abs(V[:, nseg // 2]) / hw - 0.5)
        Ps.append(np.stack([x, y, z], -1))
        Ts.append(shade(t, f["warm"], rng))
        Es.append(lasti & bare)
    return Ps, Ts, Es


def shaft(f, nseg, rng):
    """A few long stitches end to end down the middle, on top: a little brighter and thicker, thinning to the tip."""
    if f["k"] >= 3:
        return [], []
    Ps, Ts = [], []
    U0 = 0.0
    stop = f["L"] * 0.93
    while U0 < stop:
        ln = rng.uniform(0.32, 0.5)
        q = np.linspace(0, 1, nseg + 1)
        U = (U0 + np.minimum(ln, stop - U0) * q)[None]
        for dv in (-0.0065, 0.0065):
            V = np.full_like(U, dv + rng.normal(0, 0.0012))
            p = world(f, U, V)
            z = f["z"] + 0.0095 + cloth(p[..., 0], p[..., 1])
            Ps.append(np.stack([p[..., 0], p[..., 1], z], -1))
            t = TONES[f["k"]](np.clip(U[:, nseg // 2] / f["L"], 0, 1)) + 0.16
            Ts.append(shade(t, f["warm"], rng))
        U0 += ln * rng.uniform(0.85, 1.0)
    return Ps, Ts


def edge_stitches(nseg, rng):
    """The leading edge itself: short stitches along it, leaning out, each going into the satin: 虚针 with needle holes."""
    s = np.arange(-7.0, 7.0, 0.0045)
    s = s + rng.uniform(-0.002, 0.002, len(s))
    n = len(s)
    v0 = rng.uniform(0.012, 0.17, n)
    ln = rng.uniform(0.09, 0.2, n)
    out = np.radians(rng.uniform(10, 24, n))
    q = np.linspace(0, 1, nseg + 1)[None]
    S = s[:, None] + ln[:, None] * np.cos(out)[:, None] * q
    Dp = v0[:, None] - ln[:, None] * np.sin(out)[:, None] * q
    Dp = np.maximum(Dp, -0.02 + 0.03 * rng.random(n)[:, None] * 0)  # the tips stop at the edge, give or take
    th = np.pi / 2 - S / RB
    r = RB - Dp + 0.012 * np.sin(1.3 * S + 0.4)
    x, y = r * np.cos(th), r * np.sin(th)
    z = cloth(x, y) + ROWS[-1]["z"] + 0.008 * sstep(0.0, 0.1, Dp) * (1 - sstep(0.75, 1.0, q)) - (ROWS[-1]["z"] + 0.003) * sstep(0.55, 1.0, q)
    t = rng.uniform(0.86, 1.0, n)
    return [np.stack([x, y, z], -1)], [shade(t, rng.uniform(-0.2, 0.6), rng)], [np.ones(n, bool)]


def threads(cull=(-6.6, 6.6, 8.9, 13.6), nseg=5):
    """All stitches, lowest row first. P (n, nseg+1, 3), col (n,3), wd (n,), hole (n,)."""
    rng = np.random.default_rng(SEED)
    fs = layout(rng)
    zm = np.zeros(MS, np.float32)
    occ = np.zeros(MS, np.uint8)
    Ps, Cs, Ws, Hs = [], [], [], []
    visible = {k: 0 for k in range(len(ROWS))}
    for f in fs:
        tips = outline(f)
        if not ((tips[:, 0] > cull[0]) & (tips[:, 0] < cull[1]) & (tips[:, 1] > cull[2]) & (tips[:, 1] < cull[3])).any():
            continue
        visible[f["k"]] += 1
        for side in (1, -1):
            P_, C_, E_ = vane(f, side, zm, occ, cull, nseg, rng)
            for a, b, c in zip(P_, C_, E_):
                Ps.append(a), Cs.append(b), Hs.append(c), Ws.append(np.full(len(a), TW))
        P_, C_ = shaft(f, nseg, rng)
        for a, b in zip(P_, C_):
            Ps.append(a), Cs.append(b), Hs.append(np.zeros(len(a), bool)), Ws.append(np.full(len(a), TW * 1.5))
        # what lies here now, for the next feather's rim threads
        lay = np.zeros(MS, np.uint8)
        cv2.fillPoly(lay, [to_map(tips)], 1, cv2.LINE_8, shift=4)
        zm[lay > 0] = f["z"] + 0.006
        occ |= lay
    P_, C_, E_ = edge_stitches(nseg, rng)
    for a, b, c in zip(P_, C_, E_):
        Ps.append(a), Cs.append(b), Hs.append(c), Ws.append(np.full(len(a), TW * 0.9))
    print("feathers in the cull box by row, low to high:", visible, flush=True)
    return dict(P=np.concatenate(Ps).astype(np.float32), col=np.concatenate(Cs).astype(np.float32), wd=np.concatenate(Ws).astype(np.float32), hole=np.concatenate(Hs)), occ


def tubes(th, K=3):
    rng = np.random.default_rng(SEED + 1)
    p, col, w_ = th["P"], th["col"], th["wd"]
    ns, m = p.shape[:2]
    nseg = m - 1
    u = np.linspace(0, 1, m, dtype=np.float32)[None]
    T = np.gradient(p, axis=1)
    T /= np.linalg.norm(T, axis=-1, keepdims=True) + 1e-9
    B = np.cross(np.array([0.0, 0.0, 1.0], np.float32), T)
    B /= np.linalg.norm(B, axis=-1, keepdims=True) + 1e-9
    N = np.cross(T, B)
    wd = (0.5 * w_ * rng.uniform(0.85, 1.15, ns))[:, None] * (0.6 + 0.4 * sstep(0.0, 0.12, u)) * (0.6 + 0.4 * sstep(1.0, 0.85, u))
    hg = 0.26 * wd
    roll = rng.normal(0, 0.1, ns)[:, None]
    cr, sr = np.cos(roll)[..., None], np.sin(roll)[..., None]
    B2, N2 = B * cr + N * sr, N * cr - B * sr
    phi = np.linspace(-0.6, 0.6, K, dtype=np.float32)
    ex, ez = np.sin(phi), np.cos(phi)
    V = p[:, :, None] + B2[:, :, None] * (wd[..., None] * ex)[..., None] + N2[:, :, None] * (hg[..., None] * ez)[..., None]
    tt = table(rng, 256)
    tilt = lerp_table(tt, rng.uniform(0, 256, (ns, 1)) + (p[..., 0] + p[..., 1]) / 0.04)[:, :, None]
    n = B2[:, :, None] * ex[None, None, :, None] + N2[:, :, None] * ez[None, None, :, None] + T[:, :, None] * (0.04 * tilt)[..., None]
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    tc = np.broadcast_to(B2[:, :, None], n.shape)
    c = np.broadcast_to(col[:, None, None] * (0.9 + 0.1 * sstep(0.0, 0.1, u) * sstep(1.0, 0.9, u))[:, :, None, None], n.shape)
    r = np.repeat((0.42 + 0.08 * rng.random(ns)).astype(np.float32), m * K)
    F = faces(ns, nseg, K, 0)
    print(f"stitches {ns}, vertices {V.size / 3 / 1e6:.2f} M, triangles {len(F) / 1e6:.2f} M", flush=True)
    return dict(V=V.reshape(-1, 3).astype(np.float32), F=F, n=n.reshape(-1, 3).astype(np.float32), tc=tc.reshape(-1, 3).astype(np.float32), col=c.reshape(-1, 3).astype(np.float32), r=r)


def camera(aperture=APERTURE):
    th = np.linspace(np.pi / 2 - 0.7, np.pi / 2 + 0.7, 1440)
    arc = np.stack([RB * np.cos(th), RB * np.sin(th), np.full_like(th, 0.03)], 1)
    return fit_arc(arc, view_dir(-90.0, EL), W, DIST, apex=(0.5, APEX_Y), target0=(0.0, 12.0, 0.0), aperture_mm=aperture, focus_point=FOCUS)


def satin(cam, th, occ, pxcm):
    xs, ys = np.meshgrid(np.linspace(-9, 9, 361), np.linspace(7, 17, 201))
    x, y, _ = project(cam, np.stack([xs, ys, np.zeros_like(xs)], -1).reshape(-1, 3))
    x, y = x.reshape(xs.shape), y.reshape(xs.shape)
    m = (x > -0.08) & (x < 1.08) & (y > -0.08) & (y < 1.08)
    x0, x1, y0, y1 = xs[m].min(), xs[m].max(), ys[m].min(), ys[m].max()
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    X, Y = np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    print(f"satin {nx} x {ny}", flush=True)
    z = cloth(X, Y) - 0.002 * (np.hypot(X, Y) < RB - 0.1)
    hole = np.zeros((ny, nx), np.float32)
    ends = th["P"][th["hole"], -1]
    ix = ((ends[:, 0] - x0) * pxcm).astype(int)
    iy = ((ends[:, 1] - y0) * pxcm).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    np.add.at(hole, (iy[ok], ix[ok]), 1.0)
    sg = 0.0026 * pxcm
    hole = np.minimum(cv2.GaussianBlur(hole, (0, 0), sg) * sg * sg * 6.28, 1.0)
    z = z - 0.005 * hole
    tone = fbm((ny, nx), pxcm, 0.03, 0.4, 1.6, SEED + 2)
    col = GROUND[None, None] * ((1.0 + 0.05 * tone) * (1.0 - 0.75 * hole))[..., None]
    return dict(P=np.stack([X, Y, z], -1).astype(np.float32), col=col.astype(np.float32))


def flat_view():
    d = os.path.join(OUT, RUN)
    os.makedirs(d, exist_ok=True)
    Wp, Hp = 1600, 900
    s = Wp / W
    x0, y0 = -W / 2, RB - 0.51 * Hp / s
    im = np.tile((np.clip(GROUND[::-1], 0, 1) ** (1 / 2.2) * 255).astype(np.uint8), (Hp, Wp, 1))
    th, _ = threads()
    q = np.round((th["P"][..., :2] - [x0, y0]) * s).astype(np.int32)
    q[..., 1] = Hp - q[..., 1]
    c = (np.clip(th["col"][:, ::-1], 0, 1) ** (1 / 2.2) * 255).astype(int)
    for a, b in zip(q, c):
        cv2.polylines(im, [a], False, (int(b[0]), int(b[1]), int(b[2])), 1, cv2.LINE_8)
    p = os.path.join(d, "flat.jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(p, im.shape, "stitches", len(th["P"]))


def lights(focus):
    """The window is low and left, a little behind, placed so that the half vector stands square to one side's threads and well off the other's: the sheen flips at each shaft."""
    d = 60.0
    az = np.array([float(v) for v in os.environ.get("S59_L", "-0.76,0.49,0.42").split(",")])  # to try the light as stills
    key = focus + az * d
    return [
        {"type": "gradient", "name": "window", "loc": key.tolist(), "target": focus.tolist(), "size": [70, 70], "sigma": [10, 14], "L": 34.0, "rgb": [1.0, 0.97, 0.92]},
        {"name": "fill", "loc": (focus + np.array([14, -14, 40])).tolist(), "target": focus.tolist(), "size": [60, 60], "watts": 1000, "rgb": [0.96, 0.98, 1.0], "hide_in_gloss": True},
    ]


DEV = {"exposure": 0.68, "contrast": 1.2, "saturation": 1.0, "black": 0.0008, "grain": 1.05, "sharpen": 0.22, "halation": 0.02, "glare": 0.002, "vignette": 0.2}


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "flat":
        flat_view()
        return
    d = os.path.join(OUT, RUN)
    os.makedirs(d, exist_ok=True)
    tag = None
    focus = FOCUS
    if q == "crop":
        cx, cy = float(sys.argv[2]), float(sys.argv[3])
        wc = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
        p0 = np.array([cx, cy, 0.0])
        cam = frame_camera(p0, view_dir(-90.0, EL), wc, DIST, aperture_mm=APERTURE, focus_point=p0)
        cull = (cx - wc * 0.7 - 0.5, cx + wc * 0.7 + 0.5, cy - wc * 0.5 - 0.5, cy + wc * 0.5 + 0.5)
        q, tag, focus, pg, K = "preview", f"crop_{int(cx * 10)}_{int(cy * 10)}", p0, 700.0, 3
    else:
        cam, _ = camera()
        cull = (-6.6, 6.6, 8.9, 13.6)
        pg = {"preview": 160.0, "mid": 240.0, "final": 480.0}[q]
        K = {"preview": 3, "mid": 3, "final": 4}[q]
    tag = tag or {"final": "cand"}.get(q, q)
    th, occ = threads(cull)
    npz = os.path.join(d, f"he.{tag}.npz")
    np.savez(npz, **tubes(th, K))
    g = os.path.join(d, f"satin.{tag}.npz")
    np.savez(g, **satin(cam, th, occ, pg))
    import kit

    # this shot's look is its own; looks.json's entry belongs to the old picture
    lk = kit.looks()
    lk[NAME] = {}
    kit.looks = lambda: lk
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "floss", "npz": npz, "shader_py": SHADER, "params": {"kind": "floss", "tint": 0.26, "spec": 0.3, "aniso": 0.88}},
            {"name": "satin", "npz": g, "shader_py": SHADER, "params": {"kind": "ground", "warp": WARP, "pick": PICK}},
        ],
        "lights": lights(focus),
        "env": {"window": 1.4, "win_az": -38.0, "win_el": 34.0, "win_w": 30.0, "win_h": 30.0, "strip": 0.3, "ceil": 0.14, "wall": 0.04},
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 96, "mid": 192, "final": 384},
    }
    shoot(RUN, scene, q, develop=DEV, tag=tag)
    for p in (npz, g):
        os.remove(p)


if __name__ == "__main__":
    main()
