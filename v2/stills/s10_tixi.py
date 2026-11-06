"""Shot 10: tixi (剔犀): a round box of layered lacquer carved in scrolls (屈轮). The far rim of the box is the arc.

    python3 -I v2/stills/s10_tixi.py [preview|mid|final]

Built like the real thing (compared with the Met's Song-Ming pieces in ref/carved_lacquer/met_tixi; scales are estimates):
- the lacquer was laid first, tens of alternating coats, red on top; then a knife cut a V trench along the scrolls;
- therefore the colour is a function of depth. The lines on the walls are not drawn: they are contour lines of the cut through the
  strata, and they follow the scrolls by themselves, tightening where the wall steepens;
- the top stays a worn, satin red; shoulders are rounded by handling; pale dust and old wax sit at the bottom of the V.
The arrangement of the scrolls is ours.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 12.0
R = 12.2
VIEW = view_dir(-90.0, 30.0)
DIST = 46.0
X0, X1, Y0, Y1 = -9.0, 9.0, -0.6, 12.6
SEED = 10
PITCH = 1.02
TRENCH = 0.43  # half width of the cut, cm
DEPTH = 0.38


def top(X, Y):
    """The lid: nearly flat, its edge rolled over by a generous radius."""
    r = np.hypot(X, Y)
    z = -0.006 * r**2
    e = np.clip(r - (R - 1.9), 0.0, 1.9)
    return z - (1.9 - np.sqrt(np.maximum(1.9**2 - e**2, 0.0)))


def spiral(c, r_end, sign, end_dir, r0=0.1):
    """From the eye of the scroll out to its end, where it runs along end_dir."""
    turns = (r_end - r0) / PITCH
    end_ang = np.arctan2(end_dir[1], end_dir[0]) - sign * np.pi / 2
    n = int(turns * 240)
    th = np.linspace(-turns * 2 * np.pi, 0.0, n)
    r = r0 + (r_end - r0) * (1.0 + th / (turns * 2 * np.pi))
    a = end_ang + sign * th
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], 1)


def hermite(p0, t0, p1, t1, n=240):
    s = np.linspace(0, 1, n)[:, None]
    h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
    return h00 * p0 + h10 * t0 + h01 * p1 + h11 * t1


def s_scroll(c0, c1, r0, r1, sign=1.0):
    """Two scrolls turning opposite ways, joined by one S: the classic 屈轮 stroke."""
    c0, c1 = np.array(c0, float), np.array(c1, float)
    u = (c1 - c0) / np.linalg.norm(c1 - c0)
    a = spiral(c0, r0, sign, u)
    b = spiral(c1, r1, -sign, -u)
    d = float(np.linalg.norm(b[-1] - a[-1]))
    mid = hermite(a[-1], u * d * 2.1, b[-1], u * d * 2.1)
    return np.concatenate([a, mid, b[::-1]], 0)


def comma(c, r_end, sign, direction, tail):
    """A small scroll with a tapering tail that dies out, filling a gap."""
    c = np.array(c, float)
    d = np.array([np.cos(direction), np.sin(direction)])
    a = spiral(c, r_end, sign, d)
    n = np.array([-d[1], d[0]]) * sign
    p1 = a[-1] + d * tail - n * tail * 0.35
    mid = hermite(a[-1], d * tail, p1, (d - n * 0.7) * tail)
    return np.concatenate([a, mid], 0)


def curves():
    return [
        (s_scroll((-4.9, 4.7), (-0.75, 7.75), 2.3, 2.3), 1.0),
        (s_scroll((3.75, 4.2), (6.95, 8.2), 2.2, 2.3, -1.0), 1.0),
        (comma((3.05, 9.2), 1.3, 1.0, 0.1, 1.5), 0.9),
        (comma((-4.65, 9.3), 1.2, -1.0, 2.6, 1.6), 0.9),
        (comma((-8.6, 8.1), 1.3, 1.0, -0.8, 1.4), 0.9),
        (comma((-0.15, 2.5), 1.1, -1.0, 0.2, 1.4), 0.9),
        (comma((-9.2, 2.5), 1.7, 1.0, 0.5, 1.6), 0.9),
    ]


def build(dens):
    pxcm = 215.0 * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    X, Y = np.meshgrid(X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)

    # the cuts: a V of constant angle stamped along each centre line. The knife starts small in the eye of a scroll and lifts out
    # at the end of a tail, so width and depth grow and die together
    wall = np.zeros(shape, np.float32)
    rng0 = np.random.default_rng(SEED + 11)
    for pts, tail_frac in curves():
        L = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
        step = 0.018
        keep = np.searchsorted(L, np.arange(0.0, L[-1], step))
        q = pts[np.clip(keep, 0, len(pts) - 1)]
        sa = L[np.clip(keep, 0, len(pts) - 1)] / L[-1]
        grow = sstep(0.0, 0.05, sa)
        die = sstep(1.0, 0.93, sa) if tail_frac < 1.0 else sstep(1.0, 0.95, sa)
        ww = TRENCH * (0.35 + 0.65 * grow) * die * (1.0 + 0.05 * np.sin(sa * rng0.uniform(20, 40) + rng0.uniform(0, 6)))
        for (cx, cy), w in zip(q, ww):
            if w < 0.01:
                continue
            ix, iy = (cx - X0) * pxcm, (cy - Y0) * pxcm
            hp = int(w * pxcm) + 2
            x0, x1 = max(int(ix) - hp, 0), min(int(ix) + hp + 1, nx)
            y0, y1 = max(int(iy) - hp, 0), min(int(iy) + hp + 1, ny)
            if x1 <= x0 or y1 <= y0:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d2 = np.hypot(xx + 0.5 - ix, yy + 0.5 - iy) / pxcm
            cone = np.maximum(w - d2, 0.0).astype(np.float32) / TRENCH
            wall[y0:y1, x0:x1] = np.maximum(wall[y0:y1, x0:x1], cone)
    t = wall
    e = 0.06
    shoulder = sstep(0.0, 0.12, wall)
    depth = DEPTH * wall * (0.25 + 0.75 * shoulder)
    depth = blur(depth, max(0.7 * dens, 0.45))
    # knife marks on the wall: long facets along the cut
    facets = fbm(shape, pxcm, 0.02, 0.2, 1.8, SEED + 2)

    # the strata: tens of coats, laid by hand, not quite level
    rng = np.random.default_rng(SEED)
    thick = 0.0122
    # coats of unequal thickness, not quite level, and a knife that chatters: so the contour lines wander as they do in the real thing
    level = 0.012 * fbm(shape, pxcm, 0.6, 5.0, 2.8, SEED + 3) + 0.0042 * fbm(shape, pxcm, 0.06, 0.6, 2.0, SEED + 12)
    cuts = np.cumsum(rng.lognormal(np.log(thick), 0.42, 90))
    cuts = cuts * (DEPTH * 1.2) / cuts[int(DEPTH * 1.2 / thick)]
    layers = 90
    # each coat: mostly a brown-black, then a red every couple of coats, rarely an ochre
    pal = np.zeros((layers, 3), np.float32)
    for i in range(layers):
        k = rng.random()
        if i % 3 == 1:
            pal[i] = (0.3, 0.032, 0.016)
        elif k < 0.09:
            pal[i] = (0.28, 0.13, 0.035)
        else:
            pal[i] = (0.014 + 0.014 * rng.random(), 0.009 + 0.006 * rng.random(), 0.007 + 0.004 * rng.random())
    pal[:3] = (0.4, 0.036, 0.018)  # the top coats are thick
    idx = np.clip(np.searchsorted(cuts, np.maximum(depth + level * sstep(0.0, 0.02, depth), 0.0)), 0, layers - 1)
    strata = pal[idx]
    strata = cv2.GaussianBlur(strata, (0, 0), max(0.5 * dens, 0.4))

    # the top: satin red, worn; thinner over the shoulders, where the dark coat under it begins to show
    wear = rank(fbm(shape, pxcm, 0.25, 2.5, 2.6, SEED + 4))
    red = mix(color([0.34, 0.028, 0.014]), color([0.4, 0.036, 0.016]), wear)
    col = mix(strata, red, sstep(0.03, 0.0, depth))
    # dust and old wax: pale, in the deep of the V
    dust = sstep(0.7, 1.0, t) * sstep(0.35, 0.7, rank(fbm(shape, pxcm, 0.015, 0.2, 1.4, SEED + 5)))
    col = mix(col, color([0.17, 0.15, 0.12]), dust * 0.75)
    # fine cracks in old lacquer
    cr = fbm(shape, pxcm, 0.04, 0.4, 1.7, SEED + 6)
    hair = sstep(0.022, 0.0, np.abs(cr)) * sstep(0.35, 0.8, rank(fbm(shape, pxcm, 0.5, 3.0, 2.5, SEED + 7))) * sstep(0.03, 0.0, depth)
    col = mix(col, col * 0.4, hair * 0.5)

    rough = 0.22 + 0.08 * wear + 0.22 * sstep(0.0, 0.05, depth) + 0.2 * dust + 0.06 * sstep(-1, 1, facets)
    h = top(X, Y) - depth + 0.0009 * facets * sstep(0.0, 0.1, depth) + 0.0042 * fbm(shape, pxcm, 0.8, 6.0, 3.0, SEED + 8) * sstep(0.08, 0.0, depth) + 0.0002 * fbm(shape, pxcm, 0.012, 0.09, 1.3, SEED + 13) - 0.0006 * hair
    P = np.stack([X, Y, h], -1).astype(np.float32)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s10_tixi")
    os.makedirs(d, exist_ok=True)
    xx, yy = np.linspace(X0, X1, 500, dtype=np.float32), np.linspace(Y0, Y1, 500, dtype=np.float32)
    Xc, Yc = np.meshgrid(xx, yy)
    Pc = np.stack([Xc, Yc, top(Xc, Yc)], -1)
    keep = np.hypot(Xc, Yc) < R - 0.02
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Xc.shape), y.reshape(Xc.shape)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.64) ** 2) + 10 * (~keep))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=6.0, focus_point=focus)
    print("focus", focus, flush=True)
    P, C, Ro = build(dens)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)
    lw, _ = reflect_light_loc(focus + np.array([-1.0, 1.4, 0.0]), np.array([0.0, 0.0, 1.0]), cam, 60.0)
    lights = [
        {"type": "gradient", "name": "sheen", "loc": lw.tolist(), "target": focus.tolist(), "size": [140, 70], "sigma": [38, 7], "L": 0.85, "rgb": [1.0, 0.95, 0.88]},
        {"name": "rake", "loc": (focus + np.array([-44, 20, 20])).tolist(), "target": focus.tolist(), "size": [10, 10], "watts": 42000, "rgb": [1.0, 0.92, 0.8], "hide_in_gloss": True},
        {"name": "fill", "loc": (focus + np.array([26, -32, 34])).tolist(), "target": focus.tolist(), "size": [50, 50], "watts": 6000, "rgb": [1.0, 0.97, 0.94], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "box", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.42}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 2,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s10_tixi", scene, q, develop={"exposure": 0.0, "contrast": 1.3, "saturation": 1.03, "black": 0.0015, "grain": 1.2, "sharpen": 0.3, "halation": 0.04, "glare": 0.002, "vignette": 0.4})


main()
