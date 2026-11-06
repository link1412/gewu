"""Shot 59: Suzhou embroidery as a good hand does it: peonies, leaves, a butterfly on indigo satin stretched in a round frame, seen near. The frame's far edge is the arc, wide and flat across the picture; the flowers come up from the bottom of the frame and are not whole.

    python3 -I v2/stills/s59_silk.py flat                the stitches drawn in 2D, no render: out/v2/s59_suxiu_take_c/flat.jpg
    python3 -I v2/stills/s59_silk.py crop X Y [W]        a small patch at its final size (W cm wide, default 3.0)
    python3 -I v2/stills/s59_silk.py preview|mid|final   final goes to cand.* in out/v2/s59_suxiu_take_c

Each thread is geometry, so the light on it comes from which way it runs: rows of long-and-short stitches (套针, 施针) in each petal, whose threads turn with the petal. At this scale a thread is about a pixel and what is seen is the run of the silk and its sheen.

Colour: a thread takes one of seven dyed shades, and which of two neighbouring shades is drawn thread by thread, so that a petal goes from deep to pale with no boundary, as long-and-short stitch does.
水路: patches do not overlap. A thread stops a hair short of the patch on top of it and the ground shows in a fine line; that is why a petal is flat and clean. Clipped this way the outline of a patch is neat (齐针).

What is what:
- Colours measured (k-means, by eye over which clusters to use, sRGB off a museum photograph, so its lighting and fading are in them) on a piece chosen for its colour: V&A FE.117-1974, panel, China, 1900-1930, satin-weave silk embroidered with coloured silks: indigo satin, shell and cream peonies, sage and straw leaves, a touch of vermilion. The drawing is ours and copies no piece.
- Looked up: splitting silk as fine as a hair (a Chinanews report gives about 60 from one thread, https://www.chinanews.com/sh/2016/06-07/7897265.shtml); no technical standard was found. Silk's section and lustre: https://en.wikipedia.org/wiki/Trilobal
- Estimates, by eye: spacing 0.0048 cm, row height, section, every roughness and lobe weight, the frame's radius, the cord.
- Stand-ins: one tube is one split thread, its filaments are not modelled; two lobes and a translucent part in s59_silk_shader.py stand for what filaments do to light; the satin's weave is a repeating bump; the butterfly and the knots are simplified; the slow folds of the cloth are a sum of sines.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import s59_suxiu as su
from kit import OUT, fbm, frame_camera, shoot, sstep
from vessel import fit_arc, project, view_dir

NAME, RUN = "s59_suxiu", "s59_suxiu_take_c"
HERE = os.path.dirname(os.path.abspath(__file__))
SHADER = os.path.join(HERE, "s59_silk_shader.py")
SEED = 59
W, EL, DIST, APERTURE = 11.0, 62.0, 40.0, 8.0
APEX_Y = 0.485
R = 11.0  # the frame's outer radius, cm: estimate
FOCUS = np.array([-0.5, 9.5, 0.0])
SP = 0.0048
GAP = 0.006  # 水路, cm
WARP, PICK = 0.0045, 0.003
H1, R1 = np.array([-0.9, 8.2]), 2.05
H2, R2 = np.array([3.45, 8.2]), 1.3
INNER = R - 0.48
HEART = 0.2


def lin(c):
    c = np.array(c, np.float32) / 255.0
    return np.where(c < 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


# seven dyes for each: sRGB, deep to pale, read off FE.117-1974 (see the top of this file) and spaced by eye
PAL = {k: lin(v) for k, v in dict(
    shell=[(150, 92, 72), (178, 128, 105), (198, 158, 135), (212, 180, 158), (224, 200, 180), (235, 219, 203), (243, 235, 222)],
    straw=[(150, 118, 68), (180, 150, 95), (201, 177, 109), (215, 190, 130), (226, 202, 149), (236, 220, 180), (243, 235, 210)],
    leaf=[(58, 80, 64), (82, 101, 83), (105, 124, 100), (128, 145, 118), (155, 166, 136), (185, 195, 165), (210, 214, 185)],
    jade=[(50, 82, 78), (72, 104, 96), (96, 126, 114), (122, 148, 132), (150, 170, 150), (180, 194, 172), (208, 214, 192)],
    wing=[(58, 80, 118), (80, 104, 138), (110, 132, 156), (142, 160, 176), (172, 186, 194), (200, 210, 212), (226, 230, 226)],
    body=[(84, 62, 48), (108, 82, 60), (132, 104, 74), (156, 126, 90), (178, 148, 108), (198, 170, 130), (216, 192, 156)],
    vermilion=[(112, 40, 32), (130, 56, 45), (152, 76, 62), (172, 104, 88), (190, 134, 118), (208, 166, 150), (226, 200, 186)],
    gold=[(120, 88, 44), (146, 110, 56), (170, 134, 70), (190, 156, 88), (206, 176, 108), (220, 194, 130), (232, 212, 156)],
).items()}
GROUND = lin((30, 46, 78))


def shade(pal, t, rng):
    """One of seven dyes: which of the two nearest is drawn thread by thread, so that the blend is made of threads."""
    p = PAL[pal]
    n = len(p) - 1
    v = np.clip(t, 0, 1) * n + rng.random(np.shape(t))
    return p[np.clip(np.floor(v).astype(int), 0, n)]


def serrate(e, n, a, seed):
    """The frilled, toothed rim of a peony's petal."""
    r = np.random.default_rng(seed)
    x = e["tab_a"] / e["Th"]
    w = x * n * 0.5 + r.uniform(0, 1) + 0.25 * np.sin(x * r.uniform(5, 9) + r.uniform(0, 6))
    saw = np.abs(np.mod(w, 1.0) - 0.5) * 2.0
    e["tab_e"] = e["tab_e"] * (1.0 - a * (1.0 - saw) ** 1.6)
    return e


def peony(out, H, Rd, pal, seed, deep="vermilion"):
    """Rings of petals from the rim in, each ring deeper at its root than the last. Later ones lie on the earlier."""
    rng = np.random.default_rng(seed)
    rings = [(0.98, 13, 21, 0.04, 1.0, 3.2), (0.8, 12, 23, 0.03, 0.97, 2.8), (0.62, 10, 26, 0.02, 0.92, 2.4), (0.44, 8, 30, 0.0, 0.82, 1.8), (0.31, 7, 36, 0.0, 0.62, 1.2)]  # the root of a petal is under the next ring: the whole ramp has to fall in the part that shows
    s = seed * 100
    for k, (lf, n, hw, t0, t1, gm) in enumerate(rings):
        a0 = rng.uniform(0, 360)
        for i in range(n):
            a = a0 + i * 360.0 / n + rng.normal(0, 4.0)
            L = Rd * lf * rng.uniform(0.92, 1.06)
            root = H + 0.1 * Rd * lf * np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
            s += 1
            e = su.petal(root, a, L, hw * rng.uniform(0.9, 1.1), bend=rng.normal(0, 7), seed=s, pal=deep if (k == 4 and i % 2 == 0) else pal, z=0.003, t0=t0, t1=t1, gamma=gm, ruffle=0.7, rh=0.3 if lf > 0.5 else 0.22, pleat=0.003, skew=rng.normal(0, 0.1), under=0.0)
            out.append(serrate(e, rng.uniform(5, 8), 0.07, s))
    out.append(("knots", H, Rd))


def leaf(out, p, a, L, Wd, kappa, seed, pal="leaf"):
    """Two halves and a slim pale midrib. The margin rolls and has small even teeth, a good hand's leaf, not the lobes of a botanical plate."""
    r = np.random.default_rng(seed)
    for sd, f in ((1, 1.0), (-1, 0.88)):
        n, ph, ph2 = r.uniform(6, 9), r.uniform(0, 6), r.uniform(0, 6)

        def wf(u, n=n, ph=ph, ph2=ph2, f=f):
            saw = np.abs(np.mod(u * n + ph, 1.0) - 0.5) * 2.0
            return f * Wd * np.sin(np.pi * u**0.8) ** 0.8 * (1.0 + 0.09 * np.sin(2 * np.pi * 1.6 * u + ph2)) * (1.0 - 0.11 * (1.0 - saw) ** 1.5)

        out.append(su.blade(p, a, L, Wd, kappa, sd, 0.9, seed + (0 if sd > 0 else 500), pal, 0.003, t_mid=0.02, t_edge=0.9, lobes=False, rh=0.2, pleat=0.002, wfun=wf, under=0.0))
    fn = lambda u: 0.016 * (1 - u) ** 0.7 + 0.003
    for sd in (1, -1):
        out.append(su.blade(p, a, L * 0.94, 0.02, kappa, sd, 2.4, seed + 900 + sd, pal, 0.003, t_mid=0.72, t_edge=0.85, lobes=False, rh=0.12, pleat=0.0, wfun=fn, under=0.0))


def stem(out, p, a, L, w0, w1, kappa, seed, pal="leaf"):
    n0 = len(out)
    su.ribbon(out, p, a, L, w0, w1, kappa=kappa, seed=seed, pal=pal, z=0.003, tm=0.15, te=0.7)
    for e in out[n0:]:
        e["rh"], e["z"] = 0.12, 0.003


def design():
    """Back to front. The drawing is ours, in numbers."""
    o = []
    # the vine, from below the frame
    stem(o, (-2.7, 6.7), 40, 3.6, 0.035, 0.022, -0.2, 401)
    stem(o, (2.1, 6.9), 70, 2.8, 0.035, 0.024, 0.15, 402)
    stem(o, (-3.0, 7.6), 118, 1.7, 0.028, 0.016, -0.35, 403)
    stem(o, (1.0, 7.4), 25, 3.2, 0.028, 0.018, 0.25, 404)
    # leaves: a lobed leaf, two halves and a midrib
    for i, (p, a, L, Wd, k, pal) in enumerate((
        ((-3.2, 8.2), 150, 1.7, 0.52, 0.22, "leaf"),
        ((-3.05, 8.65), 104, 1.45, 0.46, -0.2, "jade"),
        ((-3.3, 7.65), 196, 1.75, 0.55, -0.15, "jade"),
        ((1.55, 9.0), 62, 1.3, 0.42, 0.2, "leaf"),
        ((1.35, 8.2), 18, 0.95, 0.34, -0.15, "jade"),
        ((1.2, 7.55), -18, 1.15, 0.4, 0.2, "leaf"),
        ((4.7, 8.55), 28, 1.25, 0.42, 0.2, "jade"),
        ((4.75, 7.75), -10, 1.3, 0.45, -0.15, "leaf"),
        ((2.65, 9.25), 110, 0.8, 0.28, 0.2, "jade"),
    )):
        leaf(o, p, a, L, Wd, k, 500 + 10 * i, pal)
    peony(o, H2, R2, "straw", 2, deep="shell")
    peony(o, H1, R1, "shell", 1)
    # a bud: the one spot of vermilion on its own
    r0 = np.array((1.75, 9.55))
    for i, (a, L, hw) in enumerate(((112, 0.62, 30), (70, 0.62, 30), (91, 0.7, 26))):
        o.append(su.petal(r0, a, L, hw, seed=700 + i, pal="vermilion", z=0.003, t0=0.0, t1=0.86, gamma=1.2, ruffle=0.4, rh=0.16, pleat=0.002, under=0.0))
    for i, (a, L, wd) in enumerate(((145, 0.34, 0.1), (35, 0.34, 0.1))):
        leaf(o, r0 + (0, -0.03), a, L, wd, 0.3 if i else -0.3, 720 + 10 * i, "jade")
    # a butterfly on the left, in stone blue
    n0 = len(o)
    su.butterfly(o, (-4.25, 9.35), 205, 0.55, z=0.003)
    for e in o[n0:]:
        e["rh"], e["z"] = 0.12, 0.003
        if e["kind"] == "petal":
            e["t0"], e["t1"], e["gamma"] = 0.05, 1.0, 1.1
    return o


def cloth(x, y):
    """The silk's slow folds, cm. Threads and ground ride on the same."""
    return 0.012 * np.sin(0.7 * x + 0.4 * y + 0.6) + 0.007 * np.sin(1.3 * y - 0.5 * x + 2.0) + 0.003 * np.sin(2.6 * x + 1.9 * y + 1.0)


# --- the plan of what is covered ----------------------------------------------------------------------------------------------
MX0, MY0, MP = -9.0, 5.0, 260.0
MS = (int(8.0 * MP), int(18.0 * MP))


def plan_d(occ):
    return cv2.distanceTransform((occ == 0).astype(np.uint8), cv2.DIST_L2, 3).astype(np.float32) / MP


def sample(m, x, y):
    ix = np.clip(((x - MX0) * MP).astype(np.int32), 0, MS[1] - 1)
    iy = np.clip(((y - MY0) * MP).astype(np.int32), 0, MS[0] - 1)
    return m[iy, ix]


def table(rng, n=128):
    r = rng.normal(0, 1, n)
    t = sum(np.roll(r, k) * np.exp(-0.5 * k * k) for k in range(-3, 4)).astype(np.float32)
    return t / t.std()


def lerp_table(t, c):
    i = np.floor(c).astype(np.int64)
    f = (c - i).astype(np.float32)
    n = len(t)
    return t[np.mod(i, n)] * (1 - f) + t[np.mod(i + 1, n)] * f


def stitches(e, inframe, dist, nseg=8, K=3):
    """The threads of a patch, rows across the flow. Returns V, n, tc, col, r, one tube after another, and how many."""
    rng = np.random.default_rng(5000 + e["seed"])
    tab_a, tab_e = e["tab_a"], e["tab_e"]
    rmax = float(tab_e.max())
    rh = e["rh"]
    petal_ = e["kind"] == "petal"
    bnd = [0.0]
    while bnd[-1] < rmax + 0.2:
        bnd.append(bnd[-1] + 0.72 * rh * rng.uniform(0.85, 1.15))
    tilt_t = table(rng, 256)
    Vs, Ns, Tc, Cs, Rs = [], [], [], [], []
    count = 0

    def pos(rho, ang, ed):
        rel, _ = su.relief(e, rho, ang, ed)
        x, y = su.unmap(e, rho, ang)
        return np.stack([x, y, e["z"] + 0.3 * rel + cloth(x, y)], -1)

    for k in range(len(bnd) - 1):
        lo, hi = bnd[k], bnd[k + 1]
        sc = max(0.5 * (lo + hi), 0.12) if petal_ else e["scale"]
        idx = np.arange(int(np.floor(tab_a.min() * sc / SP)), int(np.ceil(tab_a.max() * sc / SP)) + 1)
        nt = len(idx)
        u1, u2, u3, u4 = (rng.random(nt).astype(np.float32) for _ in range(4))
        alt = np.where(idx % 2 == 0, 1.0, -1.0).astype(np.float32)
        h_ = hi - lo
        start = np.maximum(lo - h_ * (0.3 + 0.3 * alt + 0.3 * (u1 - 0.5)), 0.0) if k else np.zeros(nt, np.float32)
        end = hi + h_ * (0.5 + 0.45 * (u2 - 0.5))
        ac = (idx + 0.5 + 0.3 * (u3 - 0.5)) * SP / sc
        eg = np.interp(ac, tab_a, tab_e, left=-1, right=-1).astype(np.float32)
        eg_i = eg + 0.004 * (u4 - 0.5)  # a good hand: the edge is even
        last = np.where(end >= eg_i - 0.3 * h_, eg_i, np.minimum(end, eg_i))
        ok = (eg > 0) & (last - start > 0.006)
        if not ok.any():
            continue
        s_, l_, a_, g_ = start[ok], last[ok], ac[ok], eg[ok]
        # a thread stops short of what lies on it: 水路. Walk along it on the plan, keep its first free run
        m = 16
        q = np.linspace(0, 1, m, dtype=np.float32)[None]
        rs = s_[:, None] + (l_ - s_)[:, None] * q
        xs, ys = su.unmap(e, rs, a_[:, None] * np.ones_like(q))
        free = sample(dist, xs, ys) >= GAP
        first = np.argmax(free, 1)
        anyf = free.any(1)
        after = np.where(np.arange(m)[None] >= first[:, None], ~free, False)
        stop = np.where(after.any(1), np.argmax(after, 1), m)
        ii = np.arange(len(s_))
        s2 = np.where(anyf, rs[ii, first], 0.0)
        l2 = np.where(anyf, rs[ii, np.clip(stop - 1, 0, m - 1)], 0.0)
        keep = anyf & (l2 - s2 > 0.006) & inframe(xs, ys)
        if not keep.any():
            continue
        s2, l2, a_, g_ = s2[keep].astype(np.float32), l2[keep].astype(np.float32), a_[keep], g_[keep]
        ns = len(s2)
        rc = 0.5 * (s2 + l2)
        t = su.t_of(e, rc, a_, g_)
        if petal_:
            xr = a_ / e["Th"]
            t = t + 0.03 * sum(w * np.sin(np.pi * ff * xr + ph) for ff, ph, w in e["pleats"]) * np.clip(rc / e["L"], 0, 1)
        t = t + 0.012 * rng.normal(0, 1, ns)
        col = shade(e["pal"], t, rng) * (1.0 + 0.022 * rng.normal(0, 1, ns))[..., None]
        u = np.linspace(0, 1, nseg + 1, dtype=np.float32)[None]
        rho = s2[:, None] + (l2 - s2)[:, None] * u
        wob = rng.normal(0, 0.16, ns)[:, None] * np.sin(np.pi * u)
        ang = a_[:, None] + wob * SP / (np.maximum(rho, 0.2) if petal_ else 1.0)
        ed = np.interp(ang, tab_a, tab_e)
        P = pos(rho, ang, ed)
        dang = SP / np.maximum(rho, 0.2) if petal_ else SP
        Pb = pos(rho, ang + dang, ed)
        s_abs = (l2 - s2)[:, None] * u
        dend = np.minimum(s_abs, (l2 - s2)[:, None] - s_abs)
        lift = (0.0003 + 0.00022 * (rng.random(ns) > 0.5) + rng.normal(0, 0.00012, ns))[:, None]
        B = Pb - P
        P[..., 2] += lift - 0.002 * sstep(0.02, 0.0, dend)
        T = np.gradient(P, axis=1)
        T /= np.linalg.norm(T, axis=-1, keepdims=True) + 1e-9
        B -= (B * T).sum(-1, keepdims=True) * T
        B /= np.linalg.norm(B, axis=-1, keepdims=True) + 1e-9
        N = np.cross(B, T)
        N *= np.sign(N[..., 2, None] + 1e-9)
        wd = (0.5 * SP * rng.uniform(1.7, 2.3, ns))[:, None]  # wider than the spacing: flat floss covers, and threads fan out toward the rim
        hg = wd * 0.32
        roll = rng.normal(0, 0.1, ns)[:, None]
        cr, sr = np.cos(roll)[..., None], np.sin(roll)[..., None]
        B2, N2 = B * cr + N * sr, N * cr - B * sr
        phi = np.linspace(-0.85, 0.85, K, dtype=np.float32)
        V = P[:, :, None, :] + B2[:, :, None, :] * (wd[..., None] * np.sin(phi))[..., None] + N2[:, :, None, :] * (hg[..., None] * np.cos(phi))[..., None]
        ex, ez = np.sin(phi), np.cos(phi)
        # floss is a bundle: its sheen breaks here and there along the thread
        tilt = lerp_table(tilt_t, rng.uniform(0, 256, (ns, 1)) + rho / 0.05)[:, :, None]
        n = B2[:, :, None, :] * ex[None, None, :, None] + N2[:, :, None, :] * ez[None, None, :, None] + T[:, :, None, :] * (0.03 * tilt)[..., None]
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        tc = np.broadcast_to(B2[:, :, None, :], n.shape)
        c = np.broadcast_to(col[:, None, None, :] * (0.75 + 0.25 * sstep(0.0, 0.03, dend))[:, :, None, None], n.shape)
        Vs.append(V.reshape(-1, 3).astype(np.float32))
        Ns.append(n.reshape(-1, 3).astype(np.float32))
        Tc.append(tc.reshape(-1, 3).astype(np.float32))
        Cs.append(c.reshape(-1, 3).astype(np.float32))
        Rs.append(np.repeat((0.42 + 0.1 * rng.random(ns)).astype(np.float32), (nseg + 1) * K))
        count += ns
    if not Vs:
        return None
    return np.concatenate(Vs), np.concatenate(Ns), np.concatenate(Tc), np.concatenate(Cs), np.concatenate(Rs), count


def knots(H, Rd, rng):
    """打籽: the heart filled edge to edge with knots, each a thread wound on itself and pulled down. Laid evenly as a good hand lays them; pale at the middle, ochre and a few vermilion outward."""
    out = []
    rh = HEART * Rd
    N = int(rh * rh / 0.0172**2)
    for i in range(N):
        v = np.sqrt((i + 0.5) / N)
        a = i * 2.39996 + rng.normal(0, 0.03)
        c = H + rh * v * np.array([np.cos(a), np.sin(a)]) + rng.normal(0, 0.002, 2)
        r_ = rng.uniform(0.0115, 0.0145)
        tt = np.linspace(0, 3.4 * np.pi, 22) + rng.uniform(0, 6)
        rad = r_ * (1.0 - 0.45 * np.linspace(0, 1, 22))
        p = np.stack([c[0] + rad * np.cos(tt), c[1] + rad * np.sin(tt), 0.005 + 0.012 * np.sin(np.linspace(0.3, 2.8, 22))], 1)
        p[:, 2] += cloth(c[0], c[1])
        t = np.clip(0.95 - 0.75 * v + rng.normal(0, 0.1), 0, 1)
        pal = "vermilion" if (v > 0.72 and rng.random() < 0.3) else "gold"
        out.append((p, PAL[pal][int(t * 6)] * rng.uniform(0.94, 1.06)))
    return out


def tube_set(paths, wd):
    """Round tubes along 3D paths of equal length, for the knots."""
    K = 4
    Vs, Ns, Tc, Cs = [], [], [], []
    for p, c in paths:
        T = np.gradient(p, axis=0)
        T /= np.linalg.norm(T, axis=-1, keepdims=True)
        B = np.cross(np.array([0.0, 0.0, 1.0]), T)
        B /= np.linalg.norm(B, axis=-1, keepdims=True) + 1e-9
        N = np.cross(T, B)
        phi = np.linspace(-1.6, 1.6, K)
        v = p[:, None] + wd * (B[:, None] * np.sin(phi)[None, :, None] + N[:, None] * np.cos(phi)[None, :, None])
        n = B[:, None] * np.sin(phi)[None, :, None] + N[:, None] * np.cos(phi)[None, :, None]
        Vs.append(v.reshape(-1, 3))
        Ns.append(n.reshape(-1, 3))
        Tc.append(np.repeat(B, K, 0))
        Cs.append(np.tile(c, (v.shape[0] * K, 1)))
    return [np.concatenate(a).astype(np.float32) for a in (Vs, Ns, Tc, Cs)], len(paths[0][0]), K


def faces(n_tubes, nseg, K, base):
    a = (np.arange(nseg)[:, None] * K + np.arange(K - 1)[None, :]).ravel()
    q = np.stack([a, a + K, a + K + 1, a, a + K + 1, a + 1], 1).reshape(-1, 3)
    off = base + (np.arange(n_tubes) * (nseg + 1) * K)[:, None, None]
    return (q[None] + off).reshape(-1, 3).astype(np.int32)


def camera(aperture=APERTURE):
    th = np.linspace(0, 2 * np.pi, 2880)
    rim = np.stack([R * np.cos(th), R * np.sin(th), np.full_like(th, 0.12)], 1)
    return fit_arc(rim, view_dir(-90.0, EL), W, DIST, apex=(0.5, APEX_Y), target0=(0.0, 8.0, 0.0), aperture_mm=aperture, focus_point=FOCUS)


def build(cam, cull=0.05, nseg=8, K=3):
    els = design()
    # back to front is the order of the drawing; lay from the front, so that each patch knows what is on it
    occ = np.zeros(MS, np.uint8)
    Vs, Ns, Tc, Cs, Rs, Fs = [], [], [], [], [], []
    base = made = 0
    rng = np.random.default_rng(SEED)

    def inframe(xs, ys):
        x, y, _ = project(cam, np.stack([xs, ys, np.zeros_like(xs)], -1).reshape(-1, 3))
        x, y = x.reshape(xs.shape), y.reshape(xs.shape)
        return ((x > -cull) & (x < 1 + cull) & (y > -cull) & (y < 1 + cull)).any(1)

    for e in els[::-1]:
        if isinstance(e, tuple):
            H, Rd = e[1], e[2]
            (v, n, t, c), m, K_ = tube_set(knots(H, Rd, rng), 0.0052)
            nth = len(v) // (m * K_)
            Fs.append(faces(nth, m - 1, K_, base))
            Vs.append(v), Ns.append(n), Tc.append(t), Cs.append(c), Rs.append(np.full(len(v), 0.45, np.float32))
            base += len(v)
            cv2.circle(occ, tuple(int(a) for a in ((H - [MX0, MY0]) * MP)), int(HEART * Rd * MP), 1, -1)
            continue
        d = plan_d(occ) if occ.any() else np.full(MS, 99.0, np.float32)
        r = stitches(e, inframe, d, nseg, K)
        if r is not None:
            v, n, t, c, ro, cnt = r
            Fs.append(faces(cnt, nseg, K, base))
            Vs.append(v), Ns.append(n), Tc.append(t), Cs.append(c), Rs.append(ro)
            base += len(v)
            made += cnt
        poly = np.round((su.outline(e) - [MX0, MY0]) * MP * 16).astype(np.int32)
        cv2.fillPoly(occ, [poly], 1, cv2.LINE_8, shift=4)
    print(f"threads {made}, vertices {base / 1e6:.2f} M, triangles {sum(len(f) for f in Fs) / 1e6:.2f} M", flush=True)
    return dict(V=np.concatenate(Vs), F=np.concatenate(Fs), n=np.concatenate(Ns), tc=np.concatenate(Tc), col=np.concatenate(Cs), r=np.concatenate(Rs)), occ


def satin(cam, occ, pxcm):
    xs, ys = np.meshgrid(np.linspace(-10, 10, 401), np.linspace(3, 14, 221))
    x, y, _ = project(cam, np.stack([xs, ys, np.zeros_like(xs)], -1).reshape(-1, 3))
    x, y = x.reshape(xs.shape), y.reshape(xs.shape)
    m = (x > -0.08) & (x < 1.08) & (y > -0.08) & (y < 1.08)
    x0, x1, y0, y1 = xs[m].min(), xs[m].max(), ys[m].min(), min(ys[m].max(), R + 0.2)
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    X, Y = np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    X, Y = X.astype(np.float32), Y.astype(np.float32)
    print(f"satin {nx} x {ny}", flush=True)
    soft = cv2.remap(cv2.GaussianBlur(occ.astype(np.float32), (0, 0), 3.0), (X - MX0) * MP, (Y - MY0) * MP, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    r = np.hypot(X, Y)
    z = cloth(X, Y) - 0.002 * np.clip(soft, 0, 1)
    k = np.minimum(1.0, (R - 0.42) / np.maximum(r, 1e-3))  # the cloth stops under the cord: what lies outside collapses onto that circle
    X, Y = X * k, Y * k
    tone = fbm((ny, nx), pxcm, 0.03, 0.4, 1.6, SEED + 2)
    col = GROUND[None, None] * (1.0 + 0.06 * tone)[..., None]
    return dict(P=np.stack([X, Y, z], -1).astype(np.float32), col=col.astype(np.float32))


def rim(cam, pxcm=240.0):
    """The frame: a slim round of oiled cane, and a cord between it and the cloth, its strands laid on the slant."""
    th0 = np.arctan2(1.0, 0.0)
    half = np.arcsin(min((W * 0.72) / R, 1.0))
    r_ = np.arange(R - 0.48, R + 0.005, 1.0 / pxcm, dtype=np.float32)
    t_ = np.linspace(th0 - half, th0 + half, int(2 * half * R * pxcm), dtype=np.float32)
    Rr, Tt = np.meshgrid(r_, t_)
    u = Tt * R
    dr = (Rr - (R - 0.15)) / 0.15
    cane = np.abs(dr) < 1
    z = np.where(cane, 0.17 * np.sqrt(np.maximum(1 - dr**2, 0.0)), 0.0).astype(np.float32)
    fib = fbm(Rr.shape, pxcm, 0.012, 0.09, 1.3, SEED + 7)
    col = np.tile(lin((132, 92, 54)), (*Rr.shape, 1))
    col = col * (0.82 + 0.18 * np.tanh(fib))[..., None]
    rough = np.full(Rr.shape, 0.26, np.float32)
    # the cord
    db = (Rr - (R - 0.39)) / 0.0901
    band = np.abs(db) < 1
    cc = (u + (Rr - (R - 0.39)) * 1.1) / 0.03
    fc = cc - np.floor(cc)
    sec = np.sqrt(np.maximum(1 - (2 * fc - 1) ** 2, 0.0))
    z = np.where(band, 0.028 * np.sqrt(np.maximum(1 - db**2, 0.0)) + 0.005 * sec, z).astype(np.float32)
    col = np.where(band[..., None], lin((172, 138, 84))[None, None] * (0.62 + 0.38 * sec)[..., None], col)
    rough = np.where(band, 0.34, rough).astype(np.float32)
    P = np.stack([Rr * np.cos(Tt), Rr * np.sin(Tt), z + cloth(Rr * np.cos(Tt), Rr * np.sin(Tt)) * 0.6], -1)
    return dict(P=P.astype(np.float32), col=col.astype(np.float32), rough=rough)


def flat_view():
    d = os.path.join(OUT, RUN)
    os.makedirs(d, exist_ok=True)
    cam, _ = camera()
    Wp = int(16.0 * 150)
    Hp = int(7.0 * 150)
    x0, y0 = -8.0, 5.3
    im = np.tile((GROUND[::-1] ** (1 / 2.2) * 255).astype(np.uint8), (Hp, Wp, 1))
    occ = np.zeros(MS, np.uint8)
    for e in design()[::-1]:
        if isinstance(e, tuple):
            for p, c in knots(e[1], e[2], np.random.default_rng(SEED)):
                q = np.round((p[:, :2] - [x0, y0]) * 150).astype(np.int32)
                q[:, 1] = Hp - q[:, 1]
                cv2.polylines(im, [q], False, tuple(int(255 * v ** (1 / 2.2)) for v in c[::-1]), 1, cv2.LINE_AA)
            cv2.circle(occ, tuple(int(a) for a in ((e[1] - [MX0, MY0]) * MP)), int(HEART * e[2] * MP), 1, -1)
            continue
        r = stitches(e, lambda a, b: np.ones(len(a), bool), plan_d(occ) if occ.any() else np.full(MS, 99.0, np.float32), 4, 3)
        if r is not None:
            v, _, _, c, _, cnt = r
            v = v.reshape(cnt, 5, 3, 3)[:, :, 1, :2]
            c = np.clip(c.reshape(cnt, 5, 3, 3)[:, 2, 1], 0, 1) ** (1 / 2.2)
            q = np.round((v - [x0, y0]) * 150).astype(np.int32)
            q[..., 1] = Hp - q[..., 1]
            ci = (c[:, ::-1] * 255).astype(int)
            for a, b in zip(q, ci):
                cv2.polylines(im, [a], False, (int(b[0]), int(b[1]), int(b[2])), 1, cv2.LINE_8)
        cv2.fillPoly(occ, [np.round((su.outline(e) - [MX0, MY0]) * MP * 16).astype(np.int32)], 1, cv2.LINE_8, shift=4)
    th = np.linspace(0.6, 2.54, 400)
    for rr in (R, INNER):
        q = np.round((np.stack([rr * np.cos(th), rr * np.sin(th)], 1) - [x0, y0]) * 150).astype(np.int32)
        q[:, 1] = Hp - q[:, 1]
        cv2.polylines(im, [q], False, (170, 170, 170), 1, cv2.LINE_AA)
    xs, ys = np.meshgrid(np.linspace(-9, 9, 361), np.linspace(4, 14, 201))
    x, y, _ = project(cam, np.stack([xs, ys, np.zeros_like(xs)], -1).reshape(-1, 3))
    ins = ((x.reshape(xs.shape) > 0) & (x.reshape(xs.shape) < 1) & (y.reshape(xs.shape) > 0) & (y.reshape(xs.shape) < 1)).astype(np.uint8)
    for c_ in cv2.findContours(ins, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]:
        q = c_[:, 0, :].astype(np.float32) * 0.05 + [-9, 4]
        q = np.round((q - [x0, y0]) * 150).astype(np.int32)
        q[:, 1] = Hp - q[:, 1]
        cv2.polylines(im, [q], True, (255, 255, 255), 1, cv2.LINE_AA)
    p = os.path.join(d, "flat.jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(p, im.shape)


def lights(focus):
    """The window is behind and to the left, low: a thread lights up when it runs square to the half vector between it and the lens."""
    d = 60.0
    key = focus + np.array([-0.60, 0.67, 0.44]) * d + [0.0, float(os.environ.get("S59_DY", -8.0)), 0.0]  # S59_DY: to look at the ends of a move as stills
    return [
        {"type": "gradient", "name": "window", "loc": key.tolist(), "target": focus.tolist(), "size": [70, 70], "sigma": [10, 14], "L": 34.0, "rgb": [1.0, 0.97, 0.92]},
        {"name": "fill", "loc": (focus + np.array([14, -14, 40])).tolist(), "target": focus.tolist(), "size": [60, 60], "watts": 700, "rgb": [0.96, 0.98, 1.0], "hide_in_gloss": True},
    ]


DEV = {"exposure": 0.2, "contrast": 1.2, "saturation": 1.0, "black": 0.0008, "grain": 1.05, "sharpen": 0.22, "halation": 0.02, "glare": 0.002, "vignette": 0.2}


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
        q, tag, focus, pg, spec = "preview", f"crop_{int(cx * 10)}_{int(cy * 10)}", p0, 500.0, dict(cull=0.1)
    else:
        cam, sag = camera()
        pg = {"preview": 120.0, "mid": 200.0, "final": 340.0}[q]
        spec = {"preview": dict(nseg=6, K=3), "mid": dict(nseg=8, K=3), "final": dict(nseg=8, K=4)}[q]
    tag = tag or {"final": "cand"}.get(q, q)
    a, occ = build(cam, **spec)
    npz = os.path.join(d, f"silk.{tag}.npz")
    np.savez(npz, **a)
    g = os.path.join(d, f"satin.{tag}.npz")
    np.savez(g, **satin(cam, occ, pg))
    f = os.path.join(d, f"frame.{tag}.npz")
    np.savez(f, **rim(cam))
    import kit

    # this shot's look is its own; looks.json's entry belongs to the old picture
    lk = kit.looks()
    lk[NAME] = {"sky": {"top": [0.0067, 0.0065, 0.0063], "glow": [0.0176, 0.017, 0.0164], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": APEX_Y, "seed": 59}}
    kit.looks = lambda: lk
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "floss", "npz": npz, "shader_py": SHADER, "params": {"kind": "floss", "tint": 0.42, "spec": 0.36, "aniso": 0.88}},
            {"name": "satin", "npz": g, "shader_py": SHADER, "params": {"kind": "ground", "warp": WARP, "pick": PICK}},
            {"name": "frame", "npz": f, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5}},
        ],
        "lights": lights(focus),
        "env": {"window": 1.4, "win_az": -38.0, "win_el": 34.0, "win_w": 30.0, "win_h": 30.0, "strip": 0.5, "ceil": 0.22, "wall": 0.05},
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 96, "mid": 192, "final": 384},
    }
    shoot(RUN, scene, q, develop=DEV, tag=tag)
    for p in (npz, g, f):
        os.remove(p)


if __name__ == "__main__":
    main()
