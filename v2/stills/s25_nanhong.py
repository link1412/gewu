"""Shot 25: southern red agate (南红玛瑙), persimmon red: a polished pebble, its crest is the arc. Rebuild with the depth-layer bake of stonelib (as s03), replacing the real medium of the earlier version,
whose bands wiggled like oil on water and whose highlight was one even white line.

From general knowledge of the stone; all scales are ESTIMATES, no specimen or photograph was at hand:
- the colour is fine hematite in chalcedony, and it is not smooth: clouds of dots (朱砂点) 30-120 um, gathered and thinning, at every depth;
- bands (缟): few, in one place, curving round a centre outside the stone; pale and milky, mostly faint, spaced unevenly; each is a sheet at depth, so it shifts with depth and softens;
- a healed crack or two with paler fill; pits and hairlines at the surface.
The highlight is the room (scene env), bent by a slow unevenness. Grazing rim reflection is kept low by a dark ceiling so that no even line runs along the crest.
Internal light is an approximation of multiple scattering (see stonelib) [stand-in].

    python3 -I v2/stills/s25_nanhong.py [preview|mid|final]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, _cam_axes, blur, caps, fbm, frame_camera, rank, shoot, sstep
from stonelib import advect_blur, crack_paths, draw_cracks, draw_strokes, ellipsoid_exit, flow_field, refract, sample

NAME = "s25_nanhong"
ABC = np.array([3.0, 2.0, 1.6], np.float32)
W = 4.05
EL = np.radians(14.0)
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)], np.float32)
DIST = 24.0
IOR = 1.54  # chalcedony
TARGET_Z = 1.59
MU = np.array([0.10, 1.35, 2.9], np.float32)  # per cm, on the way out to the eye [estimate]
MU_EFF = np.array([0.5, 2.1, 4.2], np.float32)  # on the way in, scattering losses included [estimate]
LAMPS = [
    (np.array([-0.5, 0.55, 0.67], np.float32), np.array([0.95, 0.72, 0.5], np.float32)),  # behind, above, to the left
    (np.array([0.75, -0.55, 0.36], np.float32), np.array([0.09, 0.045, 0.025], np.float32)),  # a low fill from the front right
]
ZS = np.array([0.006, 0.018, 0.04, 0.07, 0.11, 0.17, 0.25, 0.36, 0.52, 0.75, 1.1], np.float32)


def band_profile(rng):
    """Layers along a depth coordinate: bands in groups, uneven, of uneven strength."""
    g = np.linspace(-5, 5, 20000)
    w = np.zeros_like(g)
    x = -5.0
    while x < 5:
        if rng.random() < 0.34:
            for _ in range(rng.integers(2, 7)):
                d = rng.lognormal(np.log(0.012), 0.6)
                w[(g >= x) & (g < x + d)] = rng.beta(1.3, 2.6)
                x += d + rng.lognormal(np.log(0.022), 0.7)
        x += rng.lognormal(np.log(0.16), 0.8)
    sg = 0.0035 / (g[1] - g[0])
    xk = np.arange(-int(4 * sg), int(4 * sg) + 1)
    k = np.exp(-0.5 * (xk / sg) ** 2)
    return g, np.convolve(w, k / k.sum(), "same")


def dots(shape, pc, weight, n, med, sigma, seed):
    r = np.random.default_rng(seed)
    out = np.zeros(shape, np.uint8)
    got = 0
    while got < n:
        x = r.integers(0, shape[1], 20000)
        y = r.integers(0, shape[0], 20000)
        k = r.random(20000) < weight[y, x]
        x, y = x[k], y[k]
        rad = r.lognormal(np.log(med * pc * 8), sigma, len(x))
        val = r.integers(70, 255, len(x))
        for xx, yy, rr, vv in zip(x, y, rad, val):
            cv2.circle(out, (int(xx) * 8, int(yy) * 8), max(4, int(rr)), int(vv), -1, cv2.LINE_AA, 3)
        got += len(x)
    return out.astype(np.float32) / 255.0


def build(q):
    pxcm = {"preview": 300.0, "mid": 420.0, "final": 620.0}[q]
    dens = {"preview": 0.4, "mid": 0.6, "final": 1.0}[q]
    nc, nr = int(3300 * dens), int(2200 * dens)
    lam = np.linspace(-0.93, 0.93, nc, dtype=np.float32)
    S = np.radians(np.linspace(-30.0, 72.0, nr, dtype=np.float32))
    L_, S_ = np.meshgrid(lam, S)
    Rv = float(ABC[1])
    U, V = L_ * ABC[0], S_ * Rv
    U0, V0 = float(U.min()) - 0.5, float(V.min()) - 0.5
    Wc, Hc = float(U.max() - U.min()) + 1.0, float(V.max() - V.min()) + 1.0
    nx, ny = int(Wc * pxcm), int(Hc * pxcm)
    shape = (ny, nx)
    mx, my = ((U - U0) * pxcm).astype(np.float32), ((V - V0) * pxcm).astype(np.float32)

    d = np.stack([np.sin(L_), np.cos(L_) * -np.sin(S_), np.cos(L_) * np.cos(S_)], -1).astype(np.float32)
    n0 = d / ABC
    n0 /= np.linalg.norm(n0, axis=-1, keepdims=True)
    big = cv2.resize(fbm((420, 640), 640 / (2 * 0.93 * ABC[0]), 2.2, 8.0, 3.8, 2), (nc, nr), interpolation=cv2.INTER_CUBIC)
    big = blur(big, nr / 420.0 * 2.0)
    P = d * ABC + n0 * (0.012 * big)[..., None]
    Pu, Pv = np.gradient(P, axis=1), np.gradient(P, axis=0)
    n = np.cross(Pv, Pu)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    if (n * d).sum(-1).mean() < 0:
        n = -n
    target = np.array([0.0, 0.0, TARGET_Z], np.float32)
    loc = target + VIEW * DIST
    v = loc - P
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    cos_i = (n * v).sum(-1)

    t, _ = refract(n, v, 1.0 / IOR)
    tn = np.maximum(-(t * n).sum(-1), 0.2)
    tt = t + n * tn[..., None]
    du, dv = float(U[0, 1] - U[0, 0]), float(V[1, 0] - V[0, 0])
    a11, a12, a22 = (Pu * Pu).sum(-1), (Pu * Pv).sum(-1), (Pv * Pv).sum(-1)
    b1, b2 = (tt * Pu).sum(-1), (tt * Pv).sum(-1)
    det = np.maximum(a11 * a22 - a12 * a12, 1e-14)
    dj, di = (a22 * b1 - a12 * b2) / det, (a11 * b2 - a12 * b1) / det
    dUdz = np.clip((dj * du / tn).astype(np.float32), -2.5, 2.5)
    dVdz = np.clip((di * dv / tn).astype(np.float32), -2.5, 2.5)
    del a11, a12, a22, b1, b2, det, dj, di, tt, Pu, Pv
    T = ellipsoid_exit(P * 0.999, t, ABC)

    # --- structure, in the chart
    Yc, Xc = np.mgrid[:ny, :nx].astype(np.float32)
    Uc, Vc = Xc / pxcm + U0, Yc / pxcm + V0
    cloud = rank(fbm(shape, pxcm, 0.4, 3.5, 3.2, 11))  # where the hematite thickens: the persimmon deepens slowly to blood
    gather = rank(fbm(shape, pxcm, 0.12, 1.2, 3.0, 12))  # where the dots gather, unevenly
    mott = rank(fbm(shape, pxcm, 0.03, 0.22, 2.6, 16))
    dot_w = np.clip((gather ** 3.2) * (0.25 + 0.75 * cloud) * (0.25 + 0.75 * mott ** 1.5) + 0.03, 0, 1)
    warp = fbm(shape, pxcm, 1.4, 6.0, 3.4, 13)
    wig = fbm(shape, pxcm, 0.2, 1.0, 2.6, 14)
    grid, prof = band_profile(np.random.default_rng(251))
    # bands occupy one place only: the lower right, fading away; the rest of the stone is quiet
    bmask = sstep(0.1, 0.9, np.exp(-(((Uc - 0.9) / 1.3) ** 2 + ((Vc - 0.95) / 0.62) ** 2)) + 0.22 * fbm(shape, pxcm, 0.3, 1.5, 2.8, 15))
    theta = flow_field(shape, pxcm, np.radians(35.0), 21, wander=0.4, curl=0.15)
    cracks = crack_paths(shape, pxcm, theta, 22, 3, 2.6, branch=0.5, angle=0.3, jag=0.012)

    acc = np.zeros(P.shape, np.float32)
    trans = np.ones(P.shape, np.float32)
    edges = np.concatenate([[0.0], 0.5 * (ZS[1:] + ZS[:-1]), [1.5]])
    for k, z in enumerate(ZS):
        z = float(z)
        dz = float(edges[k + 1] - edges[k])
        sc = 1 if z < 0.2 else 2
        sh = (ny // sc, nx // sc)
        pc = pxcm / sc
        # bands: the same sheets at each depth, so they shift with it
        phi = (np.hypot(Uc - 3.1, Vc - 3.4 + 0.5 * z) + 0.11 * warp + 0.006 * wig + 0.25 * z - 3.0)
        band = np.interp(phi[::sc, ::sc], grid, prof).astype(np.float32) * bmask[::sc, ::sc]
        band = cv2.resize(band, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR)
        sb = (0.0009 + 0.035 * z) * pc
        band = blur(band, max(sb, 0.5))
        dw = cv2.resize(dot_w, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR)
        ndot = int(1500 * Wc * Hc * (0.4 + 0.6 * np.exp(-z / 0.3)))
        dd = dots(sh, pc, dw, ndot, 0.0017 + 0.0012 * min(z, 0.5), 0.6, 1000 + k)
        dd = blur(dd, max(sb, 0.55))
        cr = blur(draw_cracks(sh, cracks, offset=(0.2 * z * pc, 0.3 * z * pc), width=max(1.0, 0.0018 * pc)), max(sb, 0.5)) * np.exp(-z / 0.3)
        mapx, mapy = (mx + dUdz * z * pxcm) / sc, (my + dVdz * z * pxcm) / sc
        b_s = sample(band, mapx, mapy)
        d_s = sample(dd, mapx, mapy)
        c_s = sample(cr, mapx, mapy)
        cl_s = sample(cv2.resize(cloud, (sh[1], sh[0]), interpolation=cv2.INTER_LINEAR), mapx, mapy)
        del band, dd, cr, dw
        s_al = z / tn
        inside = sstep(0.0, 0.02, T - s_al)
        X = P + t * s_al[..., None]
        E = np.zeros(P.shape, np.float32)
        for dr, I in LAMPS:
            E += I * np.exp(-ellipsoid_exit(X, dr, ABC)[..., None] * MU_EFF)
        op = (0.75 * dz * (0.75 + 0.5 * cl_s) + 0.05 * b_s) * inside
        scat = 1.0 - np.exp(-op)
        tint = np.array([1.0, 0.46, 0.25], np.float32)
        milk = b_s[..., None] * np.array([0.0, 0.25, 0.25], np.float32)
        acc += trans * scat[..., None] * E * (tint + milk)
        # hematite: a cloud that deepens the red, and grains that take the green and blue and some of the red
        tau = (dz * inside)[..., None] * MU * (0.8 + 0.55 * cl_s)[..., None] / np.maximum(tn[..., None], 0.3) + d_s[..., None] * np.array([0.5, 0.8, 0.9], np.float32) + (0.25 * op)[..., None] + c_s[..., None] * np.array([0.12, 0.5, 0.7], np.float32)
        trans = trans * np.exp(-tau)
        del X, E, op, scat, tau, b_s, d_s, c_s, cl_s
    glow = acc + trans * np.array([0.1, 0.01, 0.003], np.float32)
    glow = glow * (0.45 + 0.55 * sstep(0.0, 0.4, T))[..., None]

    # --- surface
    peel = sample(fbm(shape, pxcm, 0.3, 1.5, 3.0, 31), mx, my)
    pits = sample(caps(shape, pxcm, 3.0, 0.003, 0.016, 32, mask=sstep(0.5, 0.9, rank(fbm(shape, pxcm, 0.4, 2.0, 3.0, 33))), slope=-2.6), mx, my)
    sr = np.random.default_rng(34)
    nsc = int(14 * Wc * Hc)
    sa, sx, sy = sr.choice([0.3, 1.7, 2.7], nsc) + sr.normal(0, 0.2, nsc), sr.uniform(0, nx, nsc), sr.uniform(0, ny, nsc)
    sl_ = sr.lognormal(np.log(0.16), 0.8, nsc) * pxcm
    lines = [np.stack([np.linspace(sx[i], sx[i] + np.cos(sa[i]) * sl_[i], 5), np.linspace(sy[i], sy[i] + np.sin(sa[i]) * sl_[i], 5)], -1).astype(np.float32) for i in range(nsc)]
    scr = sample(draw_strokes(shape, lines, sr.beta(1.2, 3.0, nsc), np.ones(nsc, np.int32)), mx, my)
    P = P + n * (0.0014 * peel - 0.5 * pits - 0.0003 * scr)[..., None]
    pitm = sstep(0.002, 0.008, pits)
    glow = glow * (1 - 0.8 * pitm)[..., None]
    col = np.array([0.1, 0.012, 0.006], np.float32) * np.ones(P.shape, np.float32) * (1 - 0.6 * pitm)[..., None]
    rough = 0.2 + 0.05 * rank(peel) + 0.08 * sstep(0.2, 0.8, scr) + 0.3 * pitm
    print("glow p50", np.median(glow, axis=(0, 1)), flush=True)
    return P.astype(np.float32), col.astype(np.float32), rough.astype(np.float32), glow.astype(np.float32), n, cos_i


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    P, C, Ro, G, n, cos_i = build(q)
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, glow=G)
    print("verts", P.shape[0] * P.shape[1], flush=True)
    target = np.array([0.0, 0.0, TARGET_Z])
    col = int(P.shape[1] * 0.46)
    focus = P[int(np.argmax(cos_i[:, col] > 0.32)), col]
    cam = frame_camera(target, VIEW, W, DIST, aperture_mm=4.0, focus_point=focus)
    # the window lands on a chosen spot: right of centre, well below the crest
    hc = int(P.shape[1] * 0.64)
    hr = int(np.argmax(cos_i[:, hc] > 0.5))
    hn, hv = n[hr, hc], np.array(cam["loc"]) - P[hr, hc]
    hv = hv / np.linalg.norm(hv)
    r = 2 * hn.dot(hv) * hn - hv
    rt, ut, bk = _cam_axes(cam)
    az, el = float(np.degrees(np.arctan2(r @ rt, r @ bk))), float(np.degrees(np.arcsin(np.clip(r @ ut, -1, 1))))
    scene = {
        "camera": cam,
        "meshes": [{"name": "stone", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "IOR": IOR, "Emission Color": "glow", "Emission Strength": 1.0}}],
        "lights": [],
        "env": {"window": 2.6, "win_az": az, "win_el": el, "win_w": 15.0, "win_h": 22.0, "strip": 0.0, "ceil": 0.05, "wall": 0.02, "floor": 0.01},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "spp": {"preview": 48, "mid": 96, "final": 256},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.0, "contrast": 1.4, "saturation": 1.0, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "vignette": 0.2})


main()
