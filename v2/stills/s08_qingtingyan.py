"""Shot 8: a Warring States eye bead (蜻蜓眼琉璃珠). Rewritten against ref/eyebead (the earlier version read as rolled clay with crossing bands of colour).

What the museum pieces show, and what is done here:
- dark brown-black glass; pale tan rings, many and fine; a compound eye is a pale outer ring round a field of small ringed circles, with an ochre dot or a stack of rings at the middle;
- rings are level sets of ONE warped radius per eye, so they never cross: a drop can be off-centre and wider on one side, but not a spiral;
- a mound is one smooth dome; the rings lie in it, nearly flush (a hair of relief), not as terraces;
- glass depth is real: a separate skin of clear glass stands a little above the pattern (s08_shader.py). Weathering is real geometry and roughness: pits and craters in the mesh, the skin thin or gone where worn, soil packed in low places.
ESTIMATES, none measured: every size, count and colour. The layout is ours, not a copy of any piece. Stand-in: the skin does not refract. No emission and no thin film any more.

    python3 -I v2/stills/s08_qingtingyan.py [preview|mid|final]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc

RB = 1.0
W = 2.72
EL = np.radians(24.0)
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)])
RIGHT = np.cross(VIEW, [0, 0, 1.0])
RIGHT = RIGHT / np.linalg.norm(RIGHT)  # points to image left
UP = np.cross(RIGHT, VIEW)
UP = UP / np.linalg.norm(UP)
DIST = 13.0
SEED = 8

TAN = [0.3, 0.235, 0.155]
DARK = [0.0085, 0.0058, 0.0048]
BROWN = [0.03, 0.015, 0.008]
OCHRE = [0.3, 0.14, 0.045]
SHELL_GAP = 0.016


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def rings(n, tan_w=0.52, core=0.14, jit=0.14, rng=None):
    """A stack, outside in: n pale rings and the dark ones between, each as (colour, outer radius as a fraction). Widths wander a little, as in the pieces."""
    rng = rng or np.random.default_rng(1)
    w = np.exp(rng.normal(0, jit, n))
    w = w / w.sum() * (1 - core)
    out, r = [], 1.0
    for k in range(n):
        out.append(("tan", r))
        out.append(("dark", r - w[k] * tan_w))
        r -= w[k]
    out.append(("dark", core))
    return out


def eye_list(rng):
    """Placed by eye: (x, y on the ball seen from the camera, angular radius, stack, mound height as a fraction of the radius)."""
    small = lambda a: [("tan", 1.0), ("dark", 0.76), ("tan", 0.46), ("ochre" if a else "dark", 0.27)]
    out = []
    # the hero: a stack of fine rings on the mound, its rosette of small circles, one pale outer ring round the whole field
    hx, hy, rh = -0.05, 0.60, 0.25
    out.append(dict(x=hx, y=hy, r=0.52, st=[("tan", 1.0), ("dark", 0.94)], mound=0.0))
    out.append(dict(x=hx, y=hy, r=rh, st=rings(8, rng=rng), mound=0.3))
    for k in range(7):
        a = 2 * np.pi * k / 7 + 0.3
        out.append(dict(x=hx + 0.375 * np.cos(a), y=hy + 0.375 * 0.8 * np.sin(a), r=rng.uniform(0.058, 0.07), st=small(k % 3 == 0), mound=0.1))
    # compound eyes round the ball
    for (cx, cy, r0) in [(-0.86, 0.3, 0.4), (0.82, 0.42, 0.42), (0.0, -0.4, 0.46), (-0.7, -0.62, 0.38), (0.72, -0.5, 0.38)]:
        out.append(dict(x=cx, y=cy, r=r0, st=[("tan", 1.0), ("dark", 0.9)], mound=0.0))
        out.append(dict(x=cx, y=cy, r=0.3 * r0, st=rings(3, core=0.3, rng=rng), mound=0.2))
        for k in range(6):
            a = 2 * np.pi * k / 6 + rng.uniform(0, 1)
            out.append(dict(x=cx + 0.62 * r0 * np.cos(a), y=cy + 0.62 * r0 * np.sin(a), r=0.17 * r0, st=small(k % 2 == 0), mound=0.1))
    # a small stack behind the crown and filling circles in the gaps
    out.append(dict(x=0.02, y=0.96, r=0.15, st=rings(4, rng=rng), mound=0.2))
    for (cx, cy, r0) in [(0.5, 0.82, 0.07), (-0.52, 0.8, 0.075), (0.56, 0.1, 0.06), (-0.5, 0.05, 0.06), (0.3, 0.02, 0.05), (-0.82, 0.68, 0.06), (0.78, 0.84 - 0.2, 0.05)]:
        out.append(dict(x=cx, y=cy, r=r0, st=small(False), mound=0.1))
    return out


def build(dens):
    na, nb = int(2400 * dens), int(3500 * dens)
    a = np.linspace(-0.6, 1.72, na, dtype=np.float32)
    b = np.linspace(-1.5, 1.5, nb, dtype=np.float32)
    B, A = np.meshgrid(b, a)
    shape = A.shape
    pxcm = na / (2.32 * RB)
    right, view, up = RIGHT.astype(np.float32), VIEW.astype(np.float32), UP.astype(np.float32)
    cb, sb, ca, sa = np.cos(B), np.sin(B), np.cos(A), np.sin(A)
    N = sb[..., None] * right + (cb * ca)[..., None] * view + (cb * sa)[..., None] * up

    # the body: brown-black glass with slow clouds and the striae of the gather
    striae = cv2.resize(fbm((shape[0], max(16, shape[1] // 14)), pxcm, 0.012, 0.25, 2.2, SEED + 1), (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
    cloud = rank(fbm(shape, pxcm, 0.1, 1.2, 3.0, SEED + 2) + 0.35 * striae)
    col = mix(color(DARK), color(BROWN), 0.55 * cloud)
    h = np.zeros(shape, np.float32)
    tan = np.zeros(shape, np.float32)
    wob = fbm(shape, pxcm, 0.012, 0.09, 2.2, SEED + 3)
    slowm = rank(fbm(shape, pxcm, 0.06, 0.5, 2.6, SEED + 4))
    rng = np.random.default_rng(SEED + 30)
    pal = {"tan": TAN, "dark": DARK, "ochre": OCHRE}
    for e in eye_list(rng):
        ex, ey, r0 = e["x"], e["y"], e["r"]
        if ex * ex + ey * ey > 1.0:
            continue
        z = np.sqrt(max(1 - ex * ex - ey * ey, 0.02))
        c = unit(z * VIEW - ex * RIGHT + ey * UP).astype(np.float32)
        e1 = unit(np.cross(c, UP)).astype(np.float32)
        e2 = unit(np.cross(c, e1)).astype(np.float32)
        near = (N * c).sum(-1) > np.cos(min(r0 * 1.6, 1.4))
        if not near.any():
            continue
        ii, jj = np.nonzero(near.any(1))[0], np.nonzero(near.any(0))[0]
        sl = (slice(ii[0], ii[-1] + 1), slice(jj[0], jj[-1] + 1))
        n_ = N[sl]
        x, y = (n_ * e1).sum(-1), (n_ * e2).sum(-1)
        psi = np.arccos(np.clip((n_ * c).sum(-1), -1, 1))
        # one warped radius per eye: off-centre more towards the middle, out of round, wider on one side. All rings are level sets of it, so none can cross.
        ox, oy = rng.normal(0, 0.035, 2) * r0
        s0 = np.clip(psi / r0, 0, 1)
        x2, y2 = x - ox * (1 - s0), y - oy * (1 - s0)
        d = np.hypot(x2, y2)
        ph = np.arctan2(y2, x2)
        kk = 1.0
        for m, amp in ((2, 0.022), (3, 0.014), (5, 0.005)):
            kk = kk + rng.uniform(0.5, 1.2) * amp * np.cos(m * ph + rng.uniform(0, 6.3))
        d = d * kk
        pow_ = 1 + 0.2 * np.cos(ph - rng.uniform(0, 6.3))
        rho = r0 * np.clip(d / r0, 1e-4, None) ** pow_ + 0.0007 * wob[sl]
        col_, h_, tan_ = col[sl], h[sl], tan[sl]
        if e["mound"]:
            # one smooth dome: cos^2 profile, a low shoulder beyond the edge
            t = np.clip(psi / (r0 * 1.28), 0, 1)
            h_ += e["mound"] * r0 * np.cos(0.5 * np.pi * t) ** 2
        for name, frac in e["st"]:
            rr = r0 * frac
            soft = rng.uniform(0.0012, 0.0028)
            m_ = sstep(rr + soft, rr - soft, rho)
            base = np.array(pal[name], np.float32) * rng.uniform(0.86, 1.1)
            if name == "tan":
                tone = 0.6 + 0.7 * slowm[sl] + 0.14 * wob[sl]
                col_ = mix(col_, base * tone[..., None], m_)
                tan_ = tan_ * (1 - m_) + m_
                h_ += 0.00035 * m_
            else:
                tan_ = tan_ * (1 - m_)
                col_ = mix(col_, base, m_)
                h_ -= 0.00035 * m_
        col[sl], h[sl], tan[sl] = col_, h_, tan_

    # grit: the pale specks in the body glass of the pieces
    rng = np.random.default_rng(SEED + 31)
    seeds = np.zeros(shape, np.uint8)
    for _ in range(16000):
        c0 = (int(rng.integers(0, shape[1])), int(rng.integers(0, shape[0])))
        rb_ = max(1, int(np.exp(rng.normal(np.log(0.0022), 0.45)) * pxcm))
        cv2.circle(seeds, c0, rb_, 255, -1, cv2.LINE_AA)
    grit = blur(seeds.astype(np.float32) / 255.0, 0.7) * sstep(0.35, 0.8, rank(fbm(shape, pxcm, 0.08, 0.5, 2.6, SEED + 5))) * (1 - tan)
    col = mix(col, color(TAN) * 0.42, grit * 0.75)
    h = h - 0.0006 * grit

    # weathering. Where: patches, on the far sides more; the hero's middle came through almost clean
    patches = rank(fbm(shape, pxcm, 0.2, 1.3, 3.0, SEED + 6))
    hc = unit(np.sqrt(1 - 0.05**2 - 0.6**2) * VIEW + 0.05 * RIGHT + 0.6 * UP).astype(np.float32)
    hdist = np.arccos(np.clip((N * hc).sum(-1), -1, 1))
    wear = sstep(0.52, 0.92, patches) * sstep(0.28, 0.72, hdist + 0.05 * fbm(shape, pxcm, 0.1, 0.5, 2.6, SEED + 7))
    # craters: a union of small circles growing from seeds where it wears, so they have a scalloped edge and a real depth
    r_ = np.random.default_rng(SEED + 33)
    out = np.zeros(shape, np.uint8)
    xs, ys = r_.integers(0, shape[1], 200000), r_.integers(0, shape[0], 200000)
    k = r_.random(200000) < 0.009 * wear[ys, xs] ** 1.5
    for xx, yy, rr in zip(xs[k], ys[k], r_.lognormal(np.log(0.005), 0.55, int(k.sum()))):
        cv2.circle(out, (int(xx), int(yy)), max(1, int(min(rr, 0.022) * pxcm)), 255, -1, cv2.LINE_AA)
    mo = (out > 127).astype(np.uint8)
    dist_in = (cv2.distanceTransform(mo, cv2.DIST_L2, 5) - cv2.distanceTransform(1 - mo, cv2.DIST_L2, 5)).astype(np.float32) / pxcm
    jag = 0.002 * fbm(shape, pxcm, 0.003, 0.02, 1.5, SEED + 34)
    eros = sstep(0.0, 0.002, dist_in + jag)
    h = h - 0.0045 * eros
    # pinholes everywhere, thick in worn patches, thin in the clean ones; the real relief of old glass
    micro_f = fbm(shape, pxcm, 0.003, 0.014, 1.0, SEED + 41)
    pin = sstep(1.3 - 0.6 * wear - 0.25 * tan, 2.0 - 0.6 * wear - 0.25 * tan, micro_f)
    h = h - 0.0009 * pin + 0.00014 * fbm(shape, pxcm, 0.02, 0.1, 2.5, SEED + 42) + 0.0005 * fbm(shape, pxcm, 0.08, 0.4, 2.8, SEED + 43)
    # fine crazing of the opaque rings
    craze = sstep(1.3, 2.0, fbm(shape, pxcm, 0.004, 0.03, 1.4, SEED + 13)) * tan
    h = h - 0.0003 * craze

    # soil, packed where the mesh lies below its neighbours
    low = blur(h, 0.012 * pxcm) - h
    soil = sstep(0.0006, 0.0034, low) * (0.6 + 0.4 * rank(fbm(shape, pxcm, 0.006, 0.05, 1.8, SEED + 14)))
    soilc = color([0.12, 0.078, 0.042]) * (0.7 + 0.6 * rank(fbm(shape, pxcm, 0.01, 0.1, 1.8, SEED + 15)))[..., None]
    col = col * (1 - 0.35 * craze)[..., None]
    col = mix(col, soilc, np.clip(soil, 0, 0.9))
    # worn glass goes a little pale and chalky at the skin
    col = mix(col, col * 0.75 + color([0.05, 0.042, 0.032]), wear * 0.5 * (1 - tan))

    rough = 0.38 + 0.2 * tan + 0.12 * rank(fbm(shape, pxcm, 0.03, 0.4, 2.5, SEED + 18)) + 0.3 * wear + 0.35 * soil + 0.25 * eros
    # a handmade ball is not round
    slow = 0.02 * fbm(shape, pxcm, 0.9, 4.0, 3.4, SEED + 19) + 0.0008 * fbm(shape, pxcm, 0.12, 0.6, 2.8, SEED + 20)
    rad = RB + h + slow
    P = N * rad[..., None]

    # the skin of clear glass above: smoother than what lies under it, thin on the opaque rings, gone in craters and worn places
    nh, nw = max(shape[0] // 2, 8), max(shape[1] // 2, 8)
    rad_s = cv2.resize(blur(np.maximum(rad, blur(rad, 0.01 * pxcm)), 0.006 * pxcm), (nw, nh), interpolation=cv2.INTER_AREA) + SHELL_GAP
    Ns = cv2.resize(N, (nw, nh), interpolation=cv2.INTER_AREA)
    Ns = Ns / np.linalg.norm(Ns, axis=-1, keepdims=True)
    cover = np.clip(1 - 0.55 * blur(tan, 0.004 * pxcm), 0, 1) * (1 - np.clip(blur(eros, 0.003 * pxcm) + 0.8 * wear, 0, 1))
    wave = rank(fbm(shape, pxcm, 0.05, 0.4, 2.6, SEED + 44))
    rough_s = 0.2 + 0.16 * wave + 0.4 * wear + 0.22 * blur(pin, 0.002 * pxcm)
    Ps = (Ns * rad_s[..., None]).astype(np.float32)
    cov_s = cv2.resize(cover, (nw, nh), interpolation=cv2.INTER_AREA)
    rgh_s = cv2.resize(rough_s, (nw, nh), interpolation=cv2.INTER_AREA)
    return P.astype(np.float32), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.04, 1).astype(np.float32), Ps, np.clip(cov_s, 0, 1).astype(np.float32), np.clip(rgh_s, 0.04, 1).astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s08_qingtingyan")
    os.makedirs(d, exist_ok=True)
    ang = np.linspace(0, 2 * np.pi, 800)
    Pc = (np.outer(np.cos(ang), RIGHT) + np.outer(np.sin(ang), UP)) * RB
    # the focus lies on the hero eye; the crown is a little soft behind it, the front falls away
    ex, ey = -0.05, 0.60
    z = np.sqrt(1 - ex * ex - ey * ey)
    focus = unit(z * VIEW - ex * RIGHT + ey * UP) * RB
    cam, sag = fit_arc(Pc, VIEW, W, DIST, apex=(0.5, 0.45), aperture_mm=3.4, focus_point=focus)
    P, C, Ro, Ps, Co, Rs = build(dens)
    npz = os.path.join(d, f"mesh.{q}.npz")
    nps = os.path.join(d, f"skin.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)
    np.savez(nps, P=Ps, cover=Co, rough=Rs)
    print("verts", P.shape[0] * P.shape[1], flush=True)
    # a soft key from the upper left: shows the mounds; the window is what the skin mirrors
    key = (VIEW * 13 + UP * 20 + RIGHT * 24)
    lights = [
        {"name": "key", "loc": key.tolist(), "target": [0, 0, 0], "size": [14, 14], "watts": 12000, "rgb": [1.0, 0.95, 0.87], "hide_in_gloss": True},
        {"name": "rim", "loc": (-VIEW * 22 + UP * 14 - RIGHT * 14).tolist(), "target": [0, 0, 0], "size": [10, 4], "watts": 2500, "rgb": [0.9, 0.95, 1.0]},
    ]
    # the window's reflection is aimed: this spot on the ball, to the upper left of the hero, mirrors it
    from kit import _cam_axes

    hn = unit(np.sqrt(1 - 0.52**2 - 0.72**2) * VIEW + 0.52 * RIGHT + 0.72 * UP)
    hv = unit(np.array(cam["loc"]) - hn * RB)
    hr = 2 * hn.dot(hv) * hn - hv
    rt, ut, bk = _cam_axes(cam)
    win_az, win_el = float(np.degrees(np.arctan2(hr @ rt, hr @ bk))), float(np.degrees(np.arcsin(np.clip(hr @ ut, -1, 1))))
    print("window at", round(win_az, 1), round(win_el, 1), flush=True)
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "bead", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "IOR": 1.5, "Specular IOR Level": 0.3}},
            {"name": "skin", "npz": nps, "shader_py": os.path.join(os.path.dirname(os.path.abspath(__file__)), "s08_shader.py"), "params": {"kind": "shell"}},
        ],
        "lights": lights,
        "env": {"window": 2.0, "win_az": win_az, "win_el": win_el, "win_w": 26.0, "win_h": 38.0, "strip": 0.0, "ceil": 0.18, "wall": 0.035},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "diffuse_bounces": 2,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s08_qingtingyan", scene, q, develop={"exposure": 0.3, "contrast": 1.25, "saturation": 1.0, "grain": 1.1, "sharpen": 0.2, "halation": 0.05, "vignette": 0.25})


main()
