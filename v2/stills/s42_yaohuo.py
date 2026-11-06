"""Shot 42: the door of a wood-fired kiln (柴窑窑门) at full fire: the static plate of the masonry. The fire itself is v2/stills/s42_fire.py.

    python3 -I v2/stills/s42_yaohuo.py [preview|mid|final] [pass ...]     writes out/v2/s42_yaohuo_plate/<pass>.linear.npy; passes: p0 l0 .. l7

The plate is a light stage: p0 is the masonry lit only by the kiln's own glow; l0..l7 by one soft emitter each, placed where flames burn (s42_geom.LIGHTS).
Each frame of the take adds them up, weighed by the flame's power near each one, so the firelight on the brick really follows the fire. These emitters are a substitute for
lighting from the volume itself. Scales and temperatures are estimates from general knowledge, not measured:
- no saggars show: a dim mottled back wall (their straight seams printed through the flames as boxes);
- one ring of big wedge bricks, each its own width, length and proud or recessed by a little; above it plain courses in stretcher bond; rounded arrises, deep joints;
- firebrick: dense, ochre, thinly sooted right above the crown;
- the inner end of the arch and the kiln behind it glow by themselves, dull red, in the colour of a black body. That is cooler than a kiln at peak, so that flames read against it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import s42_geom as G
from kit import OUT, color, fbm, frame_camera, mix, rank, shoot, sstep

SEED = 42
NAME = "s42_yaohuo_plate"
LIP = 1.1  # radius of the worn lip


def planck(T):
    """Linear RGB of a black body, relative: 1550 K has green 1."""
    lam = np.array([610e-9, 550e-9, 465e-9])
    c2 = 1.4388e-2

    def b(t):
        return 1.0 / (lam**5 * (np.exp(c2 / (lam * t[..., None])) - 1.0))

    return (b(np.asarray(T, np.float64)) / b(np.array(1550.0))[1]).astype(np.float32)


def stretched(shape, pxcm, lo, hi, beta, sq, sth, seed):
    """Noise drawn on a grid squeezed along each axis, so its features run long along the other."""
    ny, nx = shape
    sh = (max(int(ny / sq), 8), max(int(nx / sth), 8))
    f = fbm(sh, pxcm, lo, hi, beta, seed)
    return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)


def masonry(dens):
    """One sheet: from deep inside the arch's underside, round the lip, up the face of the wall. Grid (q along the sheet, theta round the arch)."""
    pxcm = 14.0 * dens
    q_max = G.THICK + 3.0 + 78.0
    TH_MAX = 1.3
    nq, nt = int(q_max * pxcm), int(2 * TH_MAX * 92.0 * pxcm)
    rng = np.random.default_rng(SEED)
    th0 = np.linspace(-TH_MAX, TH_MAX, nt, dtype=np.float32)
    q = np.linspace(0.0, q_max, nq, dtype=np.float32)
    TH, Q = np.meshgrid(th0, q)
    shape = TH.shape
    s1 = G.THICK - LIP
    s2 = s1 + np.pi / 2 * LIP
    phi = np.clip((Q - s1) / (s2 - s1), 0, 1) * np.pi / 2  # 0 on the underside, pi/2 on the face
    # the path of the sheet in (y, rad), without relief
    y = np.where(Q < s1, G.THICK - Q, np.where(Q < s2, LIP - LIP * np.sin(phi), 0.0))
    rad = np.where(Q < s1, G.R, np.where(Q < s2, G.R + LIP - LIP * np.cos(phi), G.R + LIP + (Q - s2)))
    y, rad = y.astype(np.float32), rad.astype(np.float32)
    front = sstep(s1, s2, Q)  # 1 on the face
    X0 = rad * np.sin(TH)
    Z0 = G.ZC + rad * np.cos(TH)
    # hand-laid: nothing is quite where it should be
    wob = fbm(shape, pxcm, 4.0, 22.0, 2.4, SEED + 1)
    wob2 = fbm(shape, pxcm, 0.7, 4.0, 2.2, SEED + 2)
    # the ring: each voussoir its own width
    widths = rng.lognormal(np.log(11.0), 0.06, 60) / G.R
    edges = np.cumsum(widths)
    edges = edges - edges[len(edges) // 2] + 0.018
    TH_w = TH + 0.0022 * wob + 0.0008 * wob2
    ci = np.clip(np.searchsorted(edges, TH_w), 1, len(edges) - 1)
    d_left = (TH_w - edges[ci - 1]) * G.R
    d_right = (edges[ci] - TH_w) * G.R
    nb = len(edges) + 1
    b_len = 25.0 + rng.normal(0, 0.8, nb)  # each brick's length above the lip
    b_recess = rng.normal(0, 0.38, nb)
    b_tone = rng.normal(0, 1, nb)
    b_tilt = rng.normal(0, 0.012, nb)
    b_spall = rng.random(nb)
    along = np.where(Q < s2, 0.0, Q - s2)  # how far up the face of the ring
    ring_end = b_len[ci]
    in_ring = along < ring_end + 0.8 * wob2
    j_ring = np.minimum(np.minimum(d_left, d_right), np.abs(along - ring_end) + 100.0 * (Q < s2))
    # above the ring: courses in stretcher bond, in world coordinates, and not perfectly level
    hc = 10.5
    Zw = Z0 + 0.35 * wob2 + 0.1 * wob
    row = np.floor(Zw / hc).astype(np.int32)
    fz = Zw / hc - row
    shift = rng.uniform(0, 30.0, 256)[row % 256]
    Xw = X0 + 0.25 * wob + shift
    colb = np.floor(Xw / 30.0).astype(np.int32)
    fx = Xw / 30.0 - colb
    j_course = np.minimum(np.minimum(fz, 1 - fz) * hc, np.minimum(fx, 1 - fx) * 30.0)
    idb = (row * 131 + colb * 57) % nb
    jd = np.where(in_ring, j_ring, j_course)
    per = np.where(in_ring, b_tone[ci], b_tone[idb])
    rec = np.where(in_ring, b_recess[ci], b_recess[idb] * 0.7)
    spall_on = np.where(in_ring, b_spall[ci], b_spall[idb])
    # mortar: a recess, with eroded and chipped arrises
    n_mid = fbm(shape, pxcm, 1.0, 6.0, 2.5, SEED + 3)
    n_fine = fbm(shape, pxcm, 0.15, 1.2, 2.0, SEED + 4)
    n_big = fbm(shape, pxcm, 6.0, 40.0, 2.6, SEED + 5)
    jd_e = jd + 0.12 * n_mid + 0.02 * n_fine
    arris = sstep(0.05, 1.3, jd_e - 0.35)  # 0 in the joint, 1 on the brick: a rounded arris over a deep, dark joint
    spall = np.zeros_like(arris)
    under = sstep(s2 + 1.0, s2 - 1.0, Q)
    h = 1.3 * (arris - 1.0) - rec * arris
    # each face a little domed and uneven, from the press and from the fire; hardly any fine grain, firebrick is dense
    h = h + (0.018 * n_mid + 0.005 * n_fine + 0.02 * wob2 + 0.16 * wob + 0.08 * n_big) * (1 - 0.6 * under)
    # the lip is worn back, smoothly, at low frequency only
    wear = sstep(6.0, 0.0, np.abs(Q - s2)) * (0.3 + 0.55 * rank(n_big))
    h = h - wear * 0.7
    # the sheet's free inner end is clean: that edge is what you see against the fire
    h = h * sstep(0.0, 6.0, Q)
    # displace along the sheet's normal: towards the opening on the underside, towards the camera on the face
    ny_ = -np.sin(phi)
    nrad = -np.cos(phi)
    yy = y + ny_ * h
    rr = rad + nrad * h
    # the sheet is a grid: brick tilt shows as a slight lean of the whole face
    P = np.stack([rr * np.sin(TH), yy, G.ZC + rr * np.cos(TH)], -1).astype(np.float32)
    # --- colours
    t_b = rank(n_big + 1.3 * per + 0.25 * n_mid)
    brick = mix(color([0.30, 0.17, 0.09]), color([0.55, 0.34, 0.19]), t_b)
    mortar = color([0.26, 0.2, 0.15])
    # soot: only right above the crown, in plumes, and thin: this wall has to show the firelight
    above = np.maximum(Q - s2, 0.0)
    plume = stretched(shape, pxcm, 3.0, 22.0, 2.6, 5.0, 1.0, SEED + 6)
    soot_a = np.clip(sstep(22.0, 2.0, above + 5.0 * plume) * 0.55, 0, 1) * (0.7 + 0.3 * rank(n_mid))
    col = mix(brick, color([0.03, 0.024, 0.02]), soot_a)
    col = mix(mortar * 0.22, col, arris)
    col = col * (1.0 - 0.55 * under[..., None])
    rough = np.clip(0.8 + 0.08 * n_fine * (1 - under), 0.5, 1.0)
    # --- heat: the inner end of the arch glows, the lip does not
    depth = np.clip(G.THICK - Q, 0, G.THICK) * (Q < s2)
    T = 520.0 + 620.0 * sstep(4.0, G.THICK + 2.0, depth) ** 1.5 + 15.0 * n_mid
    gl = planck(np.maximum(T, 320.0)) * (0.3 + 0.7 * arris[..., None]) * sstep(0.0, 1.0, depth)[..., None]
    return P, np.clip(col, 0, 1).astype(np.float32), rough.astype(np.float32), gl.astype(np.float32)


def stack(cx, cy, r, z0, n, seed, dens):
    """A column of saggars, seen through the fire: each saggar has a rim and a little shadow of a gap."""
    rng = np.random.default_rng(seed)
    pxcm = 3.0 * dens
    a = np.linspace(-np.pi / 2 - 0.1, np.pi / 2 + 0.1, int(np.pi * r * pxcm), dtype=np.float32)
    hh = 19.0
    z = np.linspace(z0, z0 + n * hh, int(n * hh * pxcm), dtype=np.float32)
    A, Z = np.meshgrid(a, z)
    level = (Z - z0) / hh
    i = np.floor(level).astype(np.int32)
    f = level - i
    bulge = 1.0 + 0.012 * np.sin(np.pi * f) + 0.012 * rng.normal(0, 1, n + 2)[np.clip(i, 0, n + 1)]
    rim = sstep(0.93, 0.985, f)
    gap = sstep(0.05, 0.0, f)
    rr = r * bulge + 0.6 * rim - 1.2 * gap
    P = np.stack([cx + rr * np.sin(A), cy - rr * np.cos(A), Z], -1).astype(np.float32)
    hot = fbm(A.shape, pxcm, 4.0, 30.0, 2.6, seed + 1)
    per = rng.normal(0, 1, n + 2).astype(np.float32)[np.clip(i, 0, n + 1)]
    T = 1295.0 + 14.0 * hot + 10.0 * per + 20.0 * rim - 55.0 * gap - 35.0 * np.abs(np.sin(A)) ** 2.5
    return P, planck(T)


def plane_y(y, x0, x1, z0, z1, dens, T0, seed):
    x = np.linspace(x0, x1, int((x1 - x0) * 3 * dens), dtype=np.float32)
    z = np.linspace(z1, z0, int((z1 - z0) * 3 * dens), dtype=np.float32)
    X, Z = np.meshgrid(x, z)
    hot = fbm(X.shape, 3 * dens, 8.0, 70.0, 3.0, seed)
    return np.stack([X, np.full(X.shape, y, np.float32), Z], -1).astype(np.float32), planck(T0 + 45.0 * hot)


def plane_z(z, x0, x1, y0, y1, dens, T0, seed):
    x = np.linspace(x0, x1, int((x1 - x0) * 3 * dens), dtype=np.float32)
    y = np.linspace(y0, y1, int((y1 - y0) * 3 * dens), dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    hot = fbm(X.shape, 3 * dens, 6.0, 30.0, 2.6, seed)
    return np.stack([X, Y, np.full(X.shape, z, np.float32)], -1).astype(np.float32), planck(T0 + 30.0 * hot)


def main():
    a = sys.argv[1:]
    q = a[0] if a else "preview"
    want = a[1:] or ["p0"] + [f"l{i}" for i in range(len(G.LIGHTS))]
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cam = frame_camera(G.TARGET, G.VIEW, G.W, G.DIST, aperture_mm=24.0, focus_point=np.array([0.0, 0.0, 0.0]))
    meshes = []
    P, C, Ro, Gl = masonry(dens)
    p = os.path.join(d, f"wall.{q}.npz")
    np.savez(p, P=P, col=C, rough=Ro, glow=Gl)
    meshes.append(("wall", p, {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5, "Emission Color": "glow"}))
    for nm, (P, E) in (("back", plane_y(G.BACK, -100, 100, -90, 40, dens, 1120.0, SEED + 30)), ("roof", plane_z(G.CEIL, -100, 100, G.THICK - 1.0, G.BACK + 1, dens, 1080.0, SEED + 31))):
        p = os.path.join(d, f"{nm}.{q}.npz")
        np.savez(p, P=P, glow=E)
        meshes.append((nm, p, {"Base Color": [0.0, 0.0, 0.0], "Specular IOR Level": 0.0, "Emission Color": "glow"}))
    dev = {"exposure": 0.0, "contrast": 1.25, "grain": 0, "sharpen": 0.2, "halation": 0.0, "glare": 0.0, "vignette": 0.0, "ca": 0.0}
    for tag in want:
        emit = 1.0 if tag == "p0" else 0.0
        ms = [{"name": n, "npz": f, "material": {**m, "Emission Strength": emit}} for n, f, m in meshes]
        lights = []
        if tag != "p0":
            lights = [{"name": tag, "type": "point", "watts": 1000.0, "radius": 6.0, "loc": list(G.LIGHTS[int(tag[1:])]), "target": [0, 0, 0], "rgb": [1.0, 0.36, 0.08]}]
        scene = {"camera": cam, "meshes": ms, "lights": lights, "world": [0.0, 0.0, 0.0], "diffuse_bounces": 2, "glossy_bounces": 2, "spp": {"preview": 48, "mid": 96, "final": 160}}
        shoot(NAME, scene, q, develop=dev, tag=tag)


main()
