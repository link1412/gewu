"""Shot 68: tea going into water, in a backlit eggshell-thin white cup. The only fluid in the film.

    python3 -I v2/stills/s68_chase.py plate preview|mid|final     the two Cycles plates: out/v2/s68_chase/plate_{R,T}.linear.npy
    python3 -I v2/stills/s68_chase.py markers                     black beads under the water in pass T, to check the compositor's projection against Cycles
    python3 v2/stills/s68_chase.py comp SIM T TAG '{json}'    plates + a solve's saved particles -> out/v2/s68_chase/TAG.{jpg,png,linear.npy,develop.json}
    python3 -I v2/stills/s68_chase.py take SIM '{json}'     plates + a solve's transmission frames -> out/v2/s68_chase_take_cand/

See s68_flow.py for the fluid, s68_comp.py for the light through the tea.
Porcelain numbers, all estimates: 0.5 mm at the lip, about 1.5 mm lower down; sigma_s 80/cm with g 0.6, so about 3 transport lengths through the wall. The window is a choice.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import kit
import s68_geom as G

NAME = "s68_chase"
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(kit.OUT, NAME)

MID = 0.5 * np.pi  # the far side of the cup, the one in the frame


def thetas(dense):
    """Angle grid: fine over the arc in frame, coarse around the rest. The seam is on the near side, out of frame."""
    a = np.radians(42.0)
    n_d = int(2 * a * G.R0 * dense)
    th = np.linspace(-a, a, n_d)
    n_s = 240
    rest = np.linspace(a, 2 * np.pi - a, n_s + 2)[1:-1]
    th = np.concatenate([th, rest, [2 * np.pi - a]])
    return th + MID


def throw(z, th, seed):
    """Throwing marks: rings of the potter's fingers, spiralling slowly up the wall. 1-D noise in height with a slight drift round the cup, in unit variance per band. Returns (fine, broad) at z, th arrays."""
    rng = np.random.default_rng(seed)
    n = 8192
    zz = np.linspace(-6.0, 1.5, n)
    pxcm = (n - 1) / 7.5
    def band(lo, hi, s):
        f = kit.fbm((1, n), pxcm, lo, hi, 2.2, s)[0]
        return f
    fine, broad = band(0.03, 0.14, seed), band(0.14, 0.9, seed + 1)
    zq = z + 0.05 * np.sin(th + 0.7)
    # a ring wanders a little round the cup
    wander = 0.018 * kit.fbm((1, 4096), 4096 / (2 * np.pi), 0.2, 2.5, 2.6, seed + 2)[0]
    zq = zq + np.interp(np.mod(th, 2 * np.pi), np.linspace(0, 2 * np.pi, 4096), wander)
    return np.interp(zq, zz, fine), np.interp(zq, zz, broad)


def out_of_round(th, z):
    """A hand-thrown cup is not round: slow lobes, growing towards the lip."""
    return (0.018 * np.cos(2 * th + 0.8) + 0.011 * np.cos(3 * th - 1.1) + 0.005 * np.cos(5 * th + 2.0)) * (0.6 + 0.4 * kit.sstep(-2.0, G.Z_RIM, z))


ARC = np.linspace(0, 2 * np.pi, 4096)
_arcf = lambda lo, hi, beta, seed: kit.fbm((1, 4096), 4096 / (2 * np.pi), lo, hi, beta, seed)[0]
RIM_H = 0.009 * _arcf(0.5, 3.0, 2.8, 11) + 0.0013 * _arcf(0.05, 0.25, 2.0, 12)  # the rim's height wanders: a little low on one side, shallow dips where the glaze ran
LIP_T = 1.0 + 0.10 * _arcf(0.08, 0.8, 2.2, 13)
zr = lambda t: G.Z_RIM + np.interp(np.mod(t, 2 * np.pi), ARC, RIM_H)
t_lip = lambda t: 0.05 * np.interp(np.mod(t, 2 * np.pi), ARC, LIP_T)


def inner_r(q, t):
    z = zr(t) - q
    base = G.R0 * (1.0 - (q / G.DEPTH) ** G.SHAPE_P) ** (1.0 / G.SHAPE_P)
    f, b = throw(z, t, 21)
    wall = kit.sstep(G.DEPTH, G.DEPTH - 1.0, q)
    flare = 0.018 * np.exp(-q / 0.12)  # the very lip turns a hair outward
    return base + wall * (out_of_round(t, z) + 0.0016 * f + 0.0040 * b) + flare, z


def outer_r(q, t):
    z = zr(t) - q
    base = (G.R0 + 0.05) * (1.0 - (q / (G.DEPTH + 0.15)) ** G.SHAPE_P) ** (1.0 / G.SHAPE_P)
    f, b = throw(z, t + 0.4, 31)
    wall = kit.sstep(G.DEPTH, G.DEPTH - 1.0, q)
    extra = 0.04 * kit.sstep(0.0, 0.6, q) + 0.11 * kit.sstep(0.3, 3.0, q)  # thicker going down: the wall under water dims with depth
    flare = 0.018 * np.exp(-q / 0.12)
    lip = t_lip(t) - 0.05
    # the outside carries the marks: the thickness, and so the light through the wall, varies with them
    return base + extra + flare + lip * np.exp(-q / 0.25) + wall * (out_of_round(t, z) + 0.0008 * f + 0.0045 * b), z


def cup_mesh(path, dense):
    th = thetas(dense)
    nc = len(th)
    # rows: inside from the bottom up, over the lip, outside down
    q_in = np.concatenate([np.linspace(G.DEPTH, 4.2, 30)[:-1], np.linspace(4.2, 0.028, int(4.15 * dense * 0.55))])
    a = np.linspace(-0.5 * np.pi, 0.5 * np.pi, int(0.12 * dense * 4) | 1)  # the lip, a half round
    q_out = np.concatenate([np.linspace(0.028, 4.2, int(4.15 * dense * 0.2)), np.linspace(4.2, G.DEPTH + 0.15, 30)[1:]])
    T, Qi = np.meshgrid(th, q_in)
    Tl, Al = np.meshgrid(th, a)
    To, Qo = np.meshgrid(th, q_out)
    Ri, Zi = inner_r(Qi, T)
    Ro, Zo = outer_r(Qo, To)
    # the lip joins the inside at q0 and the outside at q0
    q0 = 0.028
    r_a, _ = inner_r(np.full_like(Tl, q0), Tl)
    r_b, _ = outer_r(np.full_like(Tl, q0), Tl)
    rc, rr = 0.5 * (r_a + r_b), 0.5 * (r_b - r_a)
    Rl = rc + rr * np.sin(Al)
    Zl = (zr(Tl) - q0) + rr * np.cos(Al)  # a true half round: the thin lip has no flat top
    R = np.concatenate([Ri, Rl[1:-1], Ro])
    Z = np.concatenate([Zi, Zl[1:-1], Zo])
    TT = np.concatenate([T, Tl[1:-1], To])
    P = np.stack([R * np.cos(TT), R * np.sin(TT), Z], -1).astype(np.float32)
    # the glaze: nearly a mirror, a little less where the lip has worn
    rough = 0.035 * np.ones_like(R, dtype=np.float32)
    wear = kit.sstep(0.7, 2.0, np.interp(np.mod(TT, 2 * np.pi), ARC, _arcf(0.03, 0.4, 2.0, 14)))
    rough = rough + (0.28 * wear * np.exp(-np.abs(np.concatenate([np.full_like(Ri, 1.0), np.abs(Al[1:-1]), np.full_like(Ro, 1.0)])) * 1.5)).astype(np.float32)
    np.savez(path, P=P, rough=rough)
    print(f"[cup] {P.shape[0]} x {P.shape[1]} = {P.shape[0]*P.shape[1]/1e6:.1f} M vertices", flush=True)


def water_mesh(path, dense):
    th = thetas(dense * 0.5)
    # rows from the middle out, so the normals face up; into the wall by 0.02
    d = np.concatenate([np.linspace(G.R0 - 0.01, 2.2, 40)[:-1], np.linspace(2.2, 0.6, 60)[:-1], np.geomspace(0.6, 0.002, int(dense * 0.25)), [-0.002]])
    T, Dd = np.meshgrid(th, d)
    h = G.meniscus(Dd)
    # the wall the water meets, as cup_mesh at that height (the same seed gives the same marks)
    z = h
    wall, _ = inner_r(zr(T) - z, T)  # the very wall of cup_mesh at that height, so water and glaze meet without a gap
    r = np.maximum(wall - Dd, 0.005)
    # the smallest stir in the room: a very low swell, just enough that a reflection is not a printed image
    sw = kit.fbm((256, 256), 256 / 10.0, 0.5, 4.0, 3.0, 41)
    x, y = r * np.cos(T), r * np.sin(T)
    import cv2

    ux, uy = ((x + 5) / 10 * 255).astype(np.float32), ((y + 5) / 10 * 255).astype(np.float32)
    swell = cv2.remap(sw, ux, uy, cv2.INTER_CUBIC)
    P = np.stack([x, y, z + 0.0006 * swell], -1).astype(np.float32)
    np.savez(path, P=P)
    print(f"[water] {P.shape[0]*P.shape[1]/1e6:.1f} M vertices", flush=True)


def sphere_soup(path, pts, r):
    V, F = [], []
    nu, nv = 24, 16
    for c in pts:
        base = len(V)
        for i in range(nv + 1):
            a = np.pi * i / nv
            for j in range(nu):
                b = 2 * np.pi * j / nu
                V.append(np.array(c) + r * np.array([np.sin(a) * np.cos(b), np.sin(a) * np.sin(b), np.cos(a)]))
        for i in range(nv):
            for j in range(nu):
                p, q, s, t = base + i * nu + j, base + i * nu + (j + 1) % nu, base + (i + 1) * nu + (j + 1) % nu, base + (i + 1) * nu + j
                F += [[p, s, q], [p, t, s]]
    np.savez(path, V=np.array(V, np.float32), F=np.array(F, np.int32))


def env(path, cam):
    """The room, in reflections only: dim walls and a tall window, placed where the water mirrors it. The window lands on part of the water with one edge and a mullion in frame; the lens softens them because the reflection is far out of focus. A choice, so the surface reads as water."""
    kit.room_env(path, cam, {"window": 0.0, "strip": 0.5, "strip_az": 70.0, "ceil": 0.14, "wall": 0.025, "floor": 0.01})
    E = np.load(path)
    h, w = E.shape[:2]
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    r, u, b = G.axes(cam)
    v = -b  # the view axis
    mirror = np.array([v[0], v[1], -v[2]])  # the view axis mirrored in the water
    e1 = r
    e2 = np.cross(mirror, r)
    e2 = e2 / np.linalg.norm(e2)
    if e2[2] < 0:
        e2 = -e2
    x = np.degrees(np.arctan2(d @ e1.astype(np.float32), d @ mirror.astype(np.float32)))
    y = np.degrees(np.arctan2(d @ e2.astype(np.float32), d @ mirror.astype(np.float32)))
    front = (d @ mirror.astype(np.float32)) > 0
    # window: in degrees about the mirror direction. +x = frame right; the frame spans about +-6.5 in x
    a = np.radians(-14.0)
    xr, yr = x * np.cos(a) - y * np.sin(a), x * np.sin(a) + y * np.cos(a)
    cx, cy, wx, wy = 8.0, 3.0, 8.0, 28.0
    pane = kit.sstep(1.0, 0.72, np.abs(xr - cx) / wx) * kit.sstep(1.0, 0.85, np.abs(yr - cy) / wy)
    pane = pane * kit.sstep(0.1, 1.2, np.abs(xr - (cx - 1.5)))  # a mullion
    E = E + (pane * front * 3.2)[..., None].astype(np.float32) * np.array([1.0, 0.98, 0.95], np.float32)
    # the same window's lower part: too low for the flat water to mirror, so the curve of the meniscus gathers it into a thin bright arc, parted by the mullions. The second arc of the picture
    low = kit.sstep(9.0, 7.5, np.abs(x)) * kit.sstep(-40.0, -22.0, y) * kit.sstep(4.0, -8.0, y)
    low = low * kit.sstep(0.2, 0.5, np.abs(x + 2.5)) * kit.sstep(0.2, 0.5, np.abs(x - 3.5))
    E = E + (low * front * 2.2)[..., None].astype(np.float32) * np.array([1.0, 0.97, 0.92], np.float32)
    # a long soft bank overhead, for the glaze: the lip's inner curve mirrors it as one fine line. Nothing else in frame faces it
    dz = np.maximum(d[..., 2], 1e-4)
    uu, vv = np.degrees(np.arctan2(d[..., 0], dz)), np.degrees(np.arctan2(d[..., 1], dz))
    bank = kit.sstep(50.0, 40.0, np.abs(uu)) * kit.sstep(10.0, 7.0, np.abs(vv + 12.0)) * (d[..., 2] > 0)
    E = E + (bank * 10.0)[..., None].astype(np.float32) * np.array([1.0, 0.98, 0.95], np.float32)
    np.save(path, E.astype(np.float32))


def scene(pas, q, markers=None):
    cam = G.camera()
    dense = {"preview": 90.0, "mid": 160.0, "final": 420.0}[q]
    os.makedirs(D, exist_ok=True)
    cup = os.path.join(D, f"cup_{q}.npz")
    water = os.path.join(D, f"water_{q}.npz")
    cup_mesh(cup, dense)
    water_mesh(water, dense)
    sky = kit.sky_mesh(os.path.join(D, "sky.npz"), cam, {"top": [0.0058, 0.0058, 0.0060], "glow": [0.0105, 0.0102, 0.0100], "y0": 0.42, "h": 0.6, "x0": 0.42, "mottle": 0.14})
    e = os.path.join(D, "env.npy")
    env(e, cam)
    shp = os.path.join(HERE, "s68_shader.py")
    cup_p = {"kind": "cup", "pass": pas, "sigma_s": [78.0, 80.0, 82.0], "sigma_a": [0.16, 0.30, 0.60], "g": 0.6, "ior": 1.5}
    meshes = [
        {"name": "cup", "npz": cup, "shader_py": shp, "params": cup_p},
        {"name": "water", "npz": water, "shader_py": shp, "params": {"kind": "water", "pass": pas, "ior": G.N_WATER}},
        {"name": "sky", "npz": sky, "material": {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}, "visible": {"camera": pas == "R", "diffuse": False, "shadow": False, "transmission": True}},
    ]
    # a few air bubbles clinging to the wall just under the surface, as in any cup filled a moment ago: small glass-like beads of air (index 1/1.33 relative to the water), seen only through the water. Sizes and places are a choice
    rb = np.random.default_rng(68)
    for r_ in (0.011, 0.018, 0.03):
        n_ = {0.011: 16, 0.018: 8, 0.03: 3}[r_]
        th_ = np.pi / 2 + rb.uniform(-0.62, 0.62, n_)
        z_ = -0.06 - rb.exponential(0.22, n_)
        rw = G.inner_radius(z_) - r_ - 0.002
        bp = os.path.join(D, f"bubbles_{int(r_*1000)}.npz")
        sphere_soup(bp, np.stack([rw * np.cos(th_), rw * np.sin(th_), z_], -1).tolist(), r_)
        meshes.append({"name": f"bubbles{int(r_*1000)}", "npz": bp, "shader_py": shp, "params": {"kind": "water", "pass": pas, "ior": 1.0 / G.N_WATER}})
    if markers:
        p = os.path.join(D, "markers.npz")
        sphere_soup(p, markers["pts"], markers["r"])
        meshes.append({"name": "marker", "npz": p, "shader_py": shp, "params": {"kind": "marker", "pass": pas}})
    cfg = {
        "camera": cam,
        "meshes": meshes,
        "lights": [
            # behind the cup and under the line from the camera over the rim, so the camera cannot see it: high and short, so the wall under water is brightest near the surface and dims with depth
            {"name": "back", "type": "area", "size": [7.0, 1.0], "loc": [0.0, G.R0 + 1.0, -0.45], "target": [0.0, G.R0, -0.35], "watts": 125.0, "rgb": [1.0, 0.87, 0.68], "hide_in_gloss": True, "hide_in_transmission": True},
            # low and deep in colour: the thick lower wall keeps its warmth as it darkens
            {"name": "deep", "type": "area", "size": [8.0, 2.0], "loc": [0.0, G.R0 + 1.2, -2.6], "target": [0.0, G.R0, -2.0], "watts": 28.0, "rgb": [1.0, 0.66, 0.36], "hide_in_gloss": True, "hide_in_transmission": True},
            # a low warm strip right behind the lip: the thin edge glows from behind
            {"name": "lip", "type": "area", "size": [8.0, 0.25], "loc": [0.0, G.R0 + 0.5, G.Z_RIM - 0.75], "target": [0.0, G.R0, G.Z_RIM - 0.12], "watts": 30.0, "rgb": [1.0, 0.72, 0.42], "hide_in_gloss": True, "hide_in_transmission": True},
        ],
        "env": {"npy": e, "diffuse": False, "transmission": True},
        "bounces": 96,
        "volume_bounces": 64,
        "transmission_bounces": 32,
        "glossy_bounces": 12,
        "diffuse_bounces": 2,
        "clamp_indirect": 40.0,
        "res": {"preview": [960, 540], "mid": [1280, 720], "final": [2560, 1440]}[q],
        "spp": {"preview": 48, "mid": 96, "final": 256}[q],
    }
    return cfg


def render(cfg, tag):
    t = time.time()
    p = kit._render_local(cfg, D, tag)
    print(f"[{tag}] {time.time()-t:.0f} s", flush=True)
    return p


def plates(q):
    from concurrent.futures import ThreadPoolExecutor

    for pas in ("T", "R"):
        L = np.load(render(scene(pas, q), f"plate_{pas}"))
        print(pas, "p50", np.median(L, axis=(0, 1)), "max", L.max(), flush=True)


def look(tag="plate_look", w=1280):
    """Plates alone, developed: for checking the cup before any tea."""
    import cv2

    from darkroom import develop, print_look

    R, T = np.load(os.path.join(D, "plate_R.linear.npy")), np.load(os.path.join(D, "plate_T.linear.npy"))
    x = print_look(develop((R + T).astype(np.float32), **DEVELOP))
    cv2.imwrite(os.path.join(D, tag + ".jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])


DEVELOP = dict(exposure=0.0, contrast=1.15, saturation=1.2, black=0.0, grain=1.1, sharpen=0.2, halation=0.03, glare=0.0, vignette=0.12, ca=0.0003, seed=68)


def markers():
    """Beads under the water at known places; returns their projection by the compositor and the plate shows where Cycles put them."""
    pts = [[-1.2, 3.4, -0.4], [0.0, 3.0, -0.8], [1.2, 3.5, -0.3], [0.6, 2.8, -1.1], [-0.6, 3.6, -0.15], [1.7, 2.9, -0.6], [-1.6, 2.9, -0.9]]
    c = scene("T", "mid", markers={"pts": pts, "r": 0.03})
    c["camera"] = dict(c["camera"])
    c["camera"].pop("aperture_mm")
    c["spp"] = 32
    L = np.load(render(c, "markers"))
    json.dump(pts, open(os.path.join(D, "markers.json"), "w"))
    print("markers done", L.shape)


def _plates(w, h):
    import cv2

    R, T = [np.load(os.path.join(D, f"plate_{x}.linear.npy")).astype(np.float32) for x in "RT"]
    # the seam at the water's contact with the wall: the first rows where anything is seen through the water are short of light, R having ended and T not begun. Closed along the vertical, only there. A repair in the composite, not physics: the plate's two passes split the antialiasing of that edge
    k = max(3, R.shape[1] // 256) | 1
    L = R + T
    seen = (T.mean(-1) > 0.02).argmax(0)
    closed = cv2.morphologyEx(L, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2 * k + 1)))
    Y = np.arange(R.shape[0])[:, None]
    band = np.abs(Y - seen[None]) <= 2 * k
    R = R + (closed - L) * band[..., None]
    if R.shape[1] != w:
        R = cv2.resize(R, (w, h), interpolation=cv2.INTER_AREA if R.shape[1] > w else cv2.INTER_CUBIC)
        T = cv2.resize(T, (w, h), interpolation=cv2.INTER_AREA if T.shape[1] > w else cv2.INTER_CUBIC)
    return R, T


def comp(sim, t, tag, over):
    """One still from a solve's saved particles."""
    import cv2
    import torch

    import s68_comp as C
    import s68_tea
    from darkroom import develop, print_look, save_png

    S = json.load(open(os.path.join(kit.OUT, "s68_sim", sim, "params.json")))
    P = {"w": 2560, "K_abs": S["K_abs"], "D_eff": S["D_eff"], **over}
    w = P["w"]
    h = w * 9 // 16
    t0 = time.time()
    d = os.path.join(kit.OUT, "s68_sim", sim)
    with torch.no_grad():
        view = C.View(w, h)
        pts = torch.from_numpy(np.load(os.path.join(d, f"pos_{t:06.3f}.npy"))).to(C.DEV)
        age = torch.from_numpy(np.load(os.path.join(d, f"age_{t:06.3f}.npy"))).to(C.DEV)
        N, m = C.splat(view, pts, age, S["mass_px"], P["D_eff"])
        lams, eps = s68_tea.bands()
        Tr = C.transmission(N, m, eps * P["K_abs"], G.band_weights(lams), w).permute(1, 2, 0).cpu().numpy()
    t1 = time.time()
    R, T = _plates(w, h)
    L = R + T * Tr
    dev = {**DEVELOP, **P.get("dev", {})}
    x = develop(L, **dev)
    y = print_look(x)
    np.save(os.path.join(D, tag + ".linear.npy"), L.astype(np.float16))
    json.dump(dev, open(os.path.join(D, tag + ".develop.json"), "w"))
    save_png(os.path.join(D, tag + ".png"), x)
    cv2.imwrite(os.path.join(D, tag + ".jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 96])
    cv2.imwrite(os.path.join(D, tag + "_print.jpg"), (y * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
    print(f"[comp] {len(pts)/1e6:.0f} M particles, tea {t1-t0:.1f} s, all {time.time()-t0:.1f} s; lowest transmission RGB {Tr.min((0,1)).round(3).tolist()}, 0.1th percentile {np.percentile(Tr[::4,::4],0.1,axis=(0,1)).round(3).tolist()}", flush=True)


def take(sim, over):
    """A solve's transmission frames over the plates, with no GPU: out/v2/s68_chase_take_cand/{f###.png, v###.jpg, take.mp4, develop.json}."""
    import glob
    import subprocess

    import cv2

    from darkroom import develop, print_look, save_png

    fs = sorted(glob.glob(os.path.join(kit.OUT, "s68_chase_tr", sim, "t*.npy")))
    if not fs:
        raise SystemExit("no frames")
    o = os.path.join(kit.OUT, "s68_chase_take_cand")
    os.makedirs(o, exist_ok=True)
    for f in glob.glob(o + "/*"):
        os.remove(f)
    a = np.load(fs[0])
    h, w = a.shape[:2]
    R, T = _plates(w, h)
    dev = {**DEVELOP, **over.get("dev", {})}
    json.dump(dev, open(os.path.join(o, "develop.json"), "w"))
    for i, f in enumerate(fs):
        L = R + T * np.load(f).astype(np.float32)
        x = develop(L, **{**dev, "seed": 6800 + i})
        save_png(os.path.join(o, f"f{i:03d}.png"), x)
        y = print_look(x)
        cv2.imwrite(os.path.join(o, f"v{i:03d}.jpg"), (y * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(o, "v%03d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", os.path.join(o, "take.mp4")], check=True)
    print(f"[take] {len(fs)} frames, {w}x{h} -> {o}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "plate":
        plates(sys.argv[2])
        look()
    elif cmd == "markers":
        markers()
    elif cmd == "look":
        look()
    elif cmd == "comp":
        comp(sys.argv[2], float(sys.argv[3]), sys.argv[4], json.loads(sys.argv[5]) if len(sys.argv) > 5 else {})
    elif cmd == "take":
        take(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
    else:
        raise SystemExit(__doc__)
