"""Shot 16: a lychee against the light; the top of the fruit is the arc. The whole fruit: a first version with a tear on white flesh read as CG, so it was dropped.

    python3 -I v2/stills/s16_lizhi_v1.py [preview|mid|final]

Built like the real thing (sizes are estimates, a fruit of about 3.4 cm):
- the peel: leathery plates of unequal size and shape (a Voronoi of a jittered point set on the sphere, not a grid), each domed, with
  a small hard spine off its centre; shallow secondary cracks inside each plate; deep grooves between plates;
- red varying from plate to plate, yellowish in some grooves, spines dark at the tip; a waxy skin;
- water drops: real refracting caps sitting on the peel.

The arc is more curved than the table says (sag about .19 instead of .08 of the width): at .08 the frame would be 1.2 cm wide and hold
only four plates, which does not read as a lychee.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.spatial import cKDTree

from kit import blur, color, fbm, frame_camera, OUT, rank, shoot, sstep
from s21_lib import SHEETS, smooth1d, up

R = 1.7
AREA = 0.038  # area of a plate, cm2
W = 2.45
H = W * 9 / 16
WINDOW = np.array([0.5, -0.72, 0.49])  # direction of the tear
WINDOW = WINDOW / np.linalg.norm(WINDOW)


def sphere_points(n, seed, jitter):
    rng = np.random.default_rng(seed)
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    a = np.pi * (1 + 5**0.5) * i
    p = np.stack([np.sqrt(1 - z * z) * np.cos(a), np.sqrt(1 - z * z) * np.sin(a), z], 1)
    p = p + rng.normal(0, jitter / np.sqrt(n), p.shape)
    return p / np.linalg.norm(p, axis=1, keepdims=True)


def nearest2(pts, q):
    d, idx = cKDTree(pts).query(q.reshape(-1, 3), k=3, workers=-1)
    return d.reshape(q.shape[:-1] + (3,)), idx.reshape(q.shape[:-1] + (3,))


def main():
    q = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview")
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s16_lizhi_v1")
    os.makedirs(d, exist_ok=True)
    seed = 16
    rng = np.random.default_rng(seed)

    # --- the visible cap of the sphere; pole along x so that no pole falls in the frame
    na, nb = int(2600 * dens), int(3000 * dens)
    lat = np.linspace(-0.95, 0.95, na, dtype=np.float32)
    lon = np.linspace(np.radians(-2.0), np.radians(126.0), nb, dtype=np.float32)  # from -y towards +z and a little past the top
    La, Lo = np.meshgrid(lat, lon, indexing="ij")
    N = np.stack([np.sin(La), -np.cos(La) * np.cos(Lo), np.cos(La) * np.sin(Lo)], -1).astype(np.float32)
    pxcm = nb / (R * (lon[-1] - lon[0]))

    # large noise on a fixed grid, in (lat, lon)
    def field(lo_, hi_, beta, s_):
        return up(fbm((500, 600), 600 / (R * (lon[-1] - lon[0])), lo_, hi_, beta, s_), na, nb)

    # --- plates: cell count from an area of about .055 cm2; each with its own everything
    n_plate = int(4 * np.pi * R * R / AREA)
    pts = sphere_points(n_plate, seed + 1, 0.72)
    # one relaxation step: plates are not points of a pure jitter, but neither are they a lattice
    dd, ii = nearest2(pts, sphere_points(n_plate * 24, seed + 2, 0.5))
    tree = cKDTree(pts)
    s2 = sphere_points(n_plate * 24, seed + 3, 0.5)
    _, near = tree.query(s2)
    acc = np.zeros_like(pts)
    np.add.at(acc, near, s2)
    pts2 = pts * 0.25 + acc * 0.75 / (np.bincount(near, minlength=n_plate)[:, None] + 1e-6)
    pts = pts2 / np.linalg.norm(pts2, axis=1, keepdims=True)

    d3, id3 = nearest2(pts, N)
    c1, c2, c3 = pts[id3[..., 0]], pts[id3[..., 1]], pts[id3[..., 2]]
    w12 = (d3[..., 1] ** 2 - d3[..., 0] ** 2) / (2 * np.linalg.norm(c1 - c2, axis=-1) + 1e-6) * R
    w13 = (d3[..., 2] ** 2 - d3[..., 0] ** 2) / (2 * np.linalg.norm(c1 - c3, axis=-1) + 1e-6) * R
    wall = (np.maximum(w12, 1e-4) ** -3 + np.maximum(w13, 1e-4) ** -3) ** (-1 / 3.0) * 1.1  # rounded corners

    # plate attributes
    h_cell = rng.uniform(0.008, 0.02, n_plate).astype(np.float32)
    spine_len = rng.uniform(0.02, 0.05, n_plate).astype(np.float32)
    spine_off = rng.normal(0, 0.028, (n_plate, 3)).astype(np.float32) / R
    red = rng.uniform(0.7, 1.15, n_plate).astype(np.float32)
    hue = rng.normal(0, 1, n_plate).astype(np.float32)
    idx = id3[..., 0]
    sc = c1 + spine_off[idx]
    sc = sc / np.linalg.norm(sc, axis=-1, keepdims=True)
    ds = np.linalg.norm(N - sc, axis=-1) * R  # distance to the spine, cm
    r_cell = np.sqrt(AREA / np.pi)

    # secondary cracks: a much finer jittered point set, shallow, only within the plate
    pts_f = sphere_points(n_plate * 16, seed + 4, 0.9)
    dF, idF = nearest2(pts_f, N)
    cF1, cF2 = pts_f[idF[..., 0]], pts_f[idF[..., 1]]
    wF = (dF[..., 1] ** 2 - dF[..., 0] ** 2) / (2 * np.linalg.norm(cF1 - cF2, axis=-1) + 1e-6) * R
    crack = np.exp(-((wF / 0.0085) ** 2))
    sub_h = rng.uniform(0.2, 1.0, n_plate * 16).astype(np.float32)[idF[..., 0]]

    groove = np.exp(-((wall / 0.018) ** 1.4))
    dome = np.clip(1 - (ds / (r_cell * 1.2)) ** 2, 0, 1)
    spine = spine_len[idx] * np.exp(-((ds / 0.026) ** 1.1))
    fine = cv2.resize(fbm((na // 2, nb // 2), pxcm / 2, 0.006, 0.05, 1.5, seed + 5), (nb, na), interpolation=cv2.INTER_LINEAR)
    lobes = field(0.8, 3.0, 2.2, seed + 6)
    h = h_cell[idx] * dome + spine - 0.017 * groove - 0.0022 * crack * (0.4 + 0.6 * sstep(0.015, 0.04, wall)) + 0.0011 * sub_h * (1 - crack) + 0.0005 * fine + 0.018 * lobes

    # --- the tear: distance from the window's centre with a jagged edge
    cosw = N @ WINDOW.astype(np.float32)
    ang = np.arccos(np.clip(cosw, -1, 1))
    tear = 0.42 + 0.05 * field(0.08, 0.5, 1.8, seed + 7) + 0.012 * field(0.03, 0.15, 1.7, seed + 8)
    # the tear tends to follow the grooves
    tear = tear + 0.05 * sstep(0.04, 0.0, wall) * 0
    outside = ang - tear
    keep = np.ones_like(outside, np.float32)  # no tear: the torn flesh read as CG in three rounds, so the fruit stays whole
    # the torn edge bends inward and shows the pale inside
    lip = np.zeros_like(outside)
    h = h * (1 - 0.8 * lip) - 0.1 * lip

    # --- colour
    wash = field(0.3, 2.0, 2.1, seed + 9)
    # blush: redder on the upper side, paler towards the shoulder where it grew in shade
    base = color([0.72, 0.105, 0.09])[None, None] * (red[idx] * (1 + 0.1 * wash) * (1 - 0.2 * fine))[..., None]
    pale = color([0.82, 0.36, 0.27])
    yellow = color([0.62, 0.36, 0.09])
    k_pale = sstep(0.0, 1.4, wash + 0.5 * hue[idx])[..., None] * 0.34
    col = base * (1 - k_pale) + pale * k_pale
    # ridges and dome tops slightly bleached, grooves deep; some grooves with yellow-green
    k_groove = groove[..., None]
    k_y = sstep(0.6, 1.8, wash * 0.5 + hue[id3[..., 1]] * 0.8)[..., None]
    col = col * (1 - 0.85 * k_groove) + k_groove * (0.85 * (color([0.1, 0.012, 0.012]) * (1 - k_y) + yellow * 0.6 * k_y))
    # cracks darker
    col = col * (1 - 0.1 * crack[..., None])
    # dry ochre scab around the spines and in flecks over the plate, as on the fruit in ref/lychee
    fleck = sstep(0.62, 0.86, rank(fine + 0.6 * field(0.02, 0.12, 1.8, seed + 21)))
    scab = np.clip(fleck * sstep(r_cell * 1.05, r_cell * 0.25, ds) * (0.5 + 0.5 * sstep(-0.6, 0.8, hue[idx])), 0, 1)[..., None]
    col = col * (1 - 0.8 * scab) + 0.8 * scab * color([0.5, 0.25, 0.06])
    # spine: dark brown tip with a yellowish neck
    tip = np.exp(-((ds / 0.017) ** 2))[..., None]
    neck = np.exp(-((ds / 0.04) ** 2))[..., None] - tip
    col = col * (1 - np.clip(neck, 0, 1) * 0.6) + np.clip(neck, 0, 1) * 0.6 * color([0.55, 0.14, 0.05])
    col = col * (1 - tip) + tip * color([0.035, 0.015, 0.01])
    # inside of the peel
    col = col * (1 - lip[..., None]) + lip[..., None] * color([0.84, 0.66, 0.6])
    rough = np.clip(0.54 + 0.08 * crack + 0.07 * fine + 0.22 * groove + 0.22 * scab[..., 0], 0.18, 0.9)
    rough = rough * (1 - lip) + lip * 0.5
    pos = N * (R + h)[..., None]
    np1 = os.path.join(d, f"mesh.{q}.npz")
    np.savez(np1, P=pos.astype(np.float32), col=np.clip(col, 0, 1).astype(np.float32), rough=rough.astype(np.float32), keep=keep)

    # --- the flesh: just a sphere under the window, with soft lobes and streaks; wet
    ns = int(1400 * dens)
    aw = np.linspace(0, 0.62, ns, dtype=np.float32)
    bw = np.linspace(0, 2 * np.pi, int(1800 * dens), dtype=np.float32)
    Aw, Bw = np.meshgrid(aw, bw, indexing="ij")
    e1 = np.cross(WINDOW, [0, 0, 1.0])
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(WINDOW, e1)
    Nf = (np.cos(Aw)[..., None] * WINDOW + np.sin(Aw)[..., None] * (np.cos(Bw)[..., None] * e1 + np.sin(Bw)[..., None] * e2)).astype(np.float32)
    f1 = up(fbm((400, 500), 500 / 6.0, 0.18, 0.8, 2.2, seed + 10), Aw.shape[0], Aw.shape[1])
    f2 = cv2.resize(fbm((Aw.shape[0] // 2, Aw.shape[1]), 160.0, 0.012, 0.06, 1.5, seed + 11), (Aw.shape[1], Aw.shape[0]), interpolation=cv2.INTER_LINEAR)
    pf = Nf * (R - 0.1 + 0.01 * f1 + 0.0007 * f2)[..., None]
    cf = np.ones(Aw.shape + (3,), np.float32) * color([0.97, 0.965, 0.92]) * (1 + 0.03 * f2)[..., None]
    np2 = os.path.join(d, f"flesh.{q}.npz")
    np.savez(np2, P=pf.astype(np.float32), col=np.clip(cf, 0, 1).astype(np.float32))

    # --- water drops: caps, each with its own size and flattening
    r3 = np.random.default_rng(seed + 12)
    drops = []
    n_a, n_b = 44, 72
    for _ in range(7):
        while True:
            la, lo_ = r3.uniform(-0.6, 0.6), np.radians(r3.uniform(12, 68))
            cn = np.array([np.sin(la), -np.cos(la) * np.cos(lo_), np.cos(la) * np.sin(lo_)])
            break
        rd = r3.uniform(0.02, 0.085)
        e = np.cross(cn, [0.3, 0.2, 0.9])
        e /= np.linalg.norm(e)
        f = np.cross(cn, e)
        t = np.linspace(0, 1, n_a)[:, None]
        p = np.linspace(0, 2 * np.pi, n_b)[None, :]
        rho = rd * t * (1 + 0.06 * np.sin(3 * p + r3.uniform(0, 6)))
        hh = (rd * 0.72) * np.sqrt(np.maximum(1 - t**2, 0))
        P_ = (R + 0.02) * cn[None, None] + rho[..., None] * (np.cos(p)[..., None] * e + np.sin(p)[..., None] * f) + hh[..., None] * cn
        drops.append(P_)
    Pd = np.concatenate(drops, 0).astype(np.float32)
    np3 = os.path.join(d, f"drops.{q}.npz")
    np.savez(np3, P=Pd)

    apex = R + 0.04
    target = np.array([0.0, 0.0, apex - (0.5 - 0.47) * H])
    view = np.array([0.0, -1.0, 0.02])
    cam = frame_camera(target, view, W, 11.0, aperture_mm=1.7, focus_point=[0.0, -0.1, apex - 0.02])
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "peel", "npz": np1, "shader_py": SHEETS, "params": {"kind": "pbr", "cut": True, "map": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.3, "Coat Weight": 0.03, "Coat Roughness": 0.3}}},
            {"name": "drops", "npz": np3, "shader_py": SHEETS, "params": {"kind": "pbr", "strand_k": n_a, "map": {"Base Color": [1.0, 1.0, 1.0], "Roughness": 0.0, "Transmission Weight": 1.0, "IOR": 1.33}}},
        ],
        "lights": [
            {"type": "gradient", "name": "sun", "loc": [-16, 16, 16], "target": [0, 0, 1.2], "size": [9, 9], "sigma": [1.5, 1.5], "L": 900.0, "rgb": [1.0, 0.9, 0.76]},
            {"type": "gradient", "name": "scrim", "loc": [13, -20, 14], "target": [0.3, -0.4, 1.0], "size": [26, 20], "sigma": [8, 5.5], "L": 7.0, "rgb": [0.97, 0.98, 1.0]},
            {"name": "low", "loc": [10, -6, -8], "target": [0.5, -0.8, 0.8], "size": [8, 8], "watts": 1700, "rgb": [1.0, 0.85, 0.75]},
        ],
        "world": [0.0006, 0.0006, 0.0008],
        "bounces": 12,
        "diffuse_bounces": 3,
        "glossy_bounces": 4,
        "transmission_bounces": 8,
        "spp": {"preview": 96, "mid": 192, "final": 448},
    }
    look = {"exposure": 0.0, "contrast": 1.35, "saturation": 1.1, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "glare": 0.002}
    shoot("s16_lizhi_v1", scene, q, develop=look)


main()
