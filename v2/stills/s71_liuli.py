"""Shot 71: tea bleeding into clear water in a glass tea bowl, seen nearly from the side with the liquid lit from behind. Replaces s70_chatang (a white bowl from low down, which read as an ashtray; IMAGERY.md).

    python3 -I v2/stills/s71_liuli.py look TAG k=v,k=v|@file.json [preview|mid|final]     out/v2/s71_liuli/TAG.jpg
    python3 -I v2/stills/s71_liuli.py take k=v,k=v|@file.json QUALITY FIRST N [FPS]       out/v2/s71_liuli_take_QUALITY/   FPS: solve frames per second of solve time, default 48, which played at 24 is half speed

What the picture is made of, all real light in Cycles:
- the bowl, blown glass, whole in the frame, with its thin flared lip;
- water, a closed body that holds the air/water surface and the glass/water wall (s71_shader.py), so the refraction at each interface is right;
- the tea, a VDB from s70_flow.py, a pure absorber in clear water, so it runs from pale gold to deep red by how much of it light crosses;
- a few strips of dark rolled tea floating at the surface, where the cloud starts (made by hand: strip_grid; their shape is from common knowledge, not checked against photographs);
- a lit room behind the bowl with a dark band across it where the frame looks directly: the bowl-shaped water bends every ray it carries out of that band, so the liquid glows and the air around stands in the dark, as a photographer gets with a card hidden behind a glass. Rays near the edges are thrown sideways, so the liquid falls off there and looks round;
- two soft strips further out to the sides, which give the glass its bright edges.

Sizes, estimates: 7.2 cm across, 4.2 cm deep. Water: capillary length 0.257 cm, contact angle on clean glass 20 degrees (estimates).
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit

NAME = "s71_liuli"
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(kit.OUT, NAME)
SHP = os.path.join(HERE, "s71_shader.py")

LC = 0.257
THETA_C = np.radians(20.0)
N_WATER, N_GLASS = 1.33, 1.5
SIGMA = [1.0, 2.3, 8.0]  # relative absorption, r g b: ref/tea_plume/report.md and s70

P0 = dict(
    R=3.6,  # radius at the rim before the flare, cm
    depth=4.2,
    power=2.6,  # the wall: z = rim - depth * (1 - (r / R) ** power)
    z_rim=0.5,  # above the still water
    flare=0.16,
    wall_lip=0.05,  # glass thickness, cm
    wall_foot=0.14,
    E=3.0,  # camera above the water, degrees. As low as this the water line, the surface and the body of the liquid all show, and it is still how one looks at a bowl on a table
    W=9.6,
    dist=34.0,
    apex_y=0.44,
    aperture=5.0,
    focus_y=0.0,
    liquor=0.02,  # absorption of the liquor in the red, per cm. Over the 7 cm across the bowl: a pale, clear gold, the "tea" of the picture; the clouds go deeper from there
    swell=0.0004,
    swell_t=0.0,
    # dark loose tea, rolled, floated just under the surface. By hand, to fall where the plumes start
    strips=[
        dict(x=-1.55, y=0.15, z=0.02, yaw=10.0, pitch=24.0, len=0.95, rad=0.064, seed=11),
        dict(x=-0.62, y=-0.2, z=0.02, yaw=172.0, pitch=30.0, len=0.75, rad=0.058, seed=12, open=0.5),
        dict(x=-1.05, y=0.5, z=0.02, yaw=-40.0, pitch=12.0, len=0.6, rad=0.05, seed=13),
        dict(x=1.15, y=0.0, z=0.02, yaw=-20.0, pitch=34.0, len=0.72, rad=0.056, seed=15, open=0.3),
    ],
    tea=None,
    tea_t=None,
    tea_K=1.1,
    surf_L=1.5,  # the room behind the bowl, see env()
    flag_up=[0.4, 3.6],  # how far above the frame the flag ends, degrees
    room_low=0.25,  # the floor, relative to the wall: rays that come in through the surface from above land there, and at full strength the surface reads as a white plate
    room_az=28.0,  # its width, degrees
    room_el=14.0,  # its falloff upwards from where the body of the liquid looks
    room_az0=-10.0,  # the lamp is left of the bowl's axis
    room_rgb=[1.0, 0.92, 0.76],
    room_rim=[1.0, 0.6, 0.25],
    edge_L=1.5,  # two strips behind and to the sides: the bright lines down the glass's edges
    exposure=0.0,
    spp=None,
    dev={},
)


def profile(o, n=1600):
    """The inner wall from the axis to the lip, evenly along its length."""
    h = np.linspace(0.0, 1.0, 20000) ** 2
    r = o["R"] * h ** (1.0 / o["power"]) + o["flare"] * kit.sstep(0.93, 1.0, h) ** 2  # the flare starts above the water line: a wall that leans this far under water throws the rays out of reach of any light, and a black band runs across the bowl
    z = o["z_rim"] - o["depth"] * (1.0 - h)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(r), np.diff(z)))])
    t = np.linspace(0.0, s[-1], n)
    return np.interp(t, s, r), np.interp(t, s, z), np.interp(t, s, h)


def wob(th):
    """Blown by hand: not quite round, low orders only. cm at the rim."""
    return 0.012 * np.cos(2 * th + 0.8) + 0.007 * np.cos(3 * th - 1.1) + 0.003 * np.cos(5 * th + 2.0)


def contact(o):
    ri, zi, _ = profile(o)
    z = 0.1
    for _ in range(6):
        i = int(np.searchsorted(zi, z))
        beta = np.arctan2(zi[i + 1] - zi[i - 1], ri[i + 1] - ri[i - 1])
        z = 2 * LC * np.sin(max(beta - THETA_C, 0.0) / 2)
    return z, float(np.interp(z, zi, ri))


def meniscus(d, h0):
    h = np.geomspace(h0, 0.0008, 800)
    x = LC * (np.arccosh(2.0 * LC / h) - np.sqrt(np.maximum(4.0 - (h / LC) ** 2, 0.0)))
    x = x - x[0]
    dd = np.maximum(d, 0.0)
    out = np.exp(np.interp(dd, x, np.log(h)))
    return np.where(dd > x[-1], h[-1] * np.exp(-(dd - x[-1]) / LC), out)


def thetas(q):
    # the seam is at the right-hand edge, where the wall is seen at grazing
    return np.linspace(0.0, 2 * np.pi, {"preview": 720, "mid": 1100, "final": 1800}[q])


def build_shell(path, o, q):
    """One sweep: inner wall above the water, up to the lip, round it, and down the outside to the axis. Normals point out of the glass."""
    th = thetas(q)
    ri, zi, hi = profile(o)
    h0, rc = contact(o)
    tr, tz = np.gradient(ri), np.gradient(zi)
    nn = np.hypot(tr, tz)
    tr, tz = tr / nn, tz / nn
    nr, nz = tz, -tr  # out of the bowl
    t = o["wall_lip"] + (o["wall_foot"] - o["wall_lip"]) * kit.sstep(1.0, 0.4, hi)
    ro, zo = ri + t * nr, zi + t * nz
    # inner, from the water line up
    j = int(np.searchsorted(zi, h0))
    inner = np.stack([np.concatenate([[rc], ri[j + 1 :]]), np.concatenate([[h0], zi[j + 1 :]])], -1)
    a = np.linspace(0.0, np.pi, 26)[1:-1]
    cr, cz = 0.5 * (ri[-1] + ro[-1]), 0.5 * (zi[-1] + zo[-1])
    lip = np.stack([cr - 0.5 * t[-1] * nr[-1] * np.cos(a) + 0.5 * t[-1] * tr[-1] * np.sin(a), cz - 0.5 * t[-1] * nz[-1] * np.cos(a) + 0.5 * t[-1] * tz[-1] * np.sin(a)], -1)
    outer = np.stack([ro[::-1], zo[::-1]], -1)
    ring = np.concatenate([inner, lip, outer])
    T, I = np.meshgrid(th, np.arange(len(ring)))
    Rr, Zz = ring[I, 0], ring[I, 1]
    n_in = len(inner) + len(lip)
    # the outside of blown glass is never quite even: slow undulation, seen only by how it moves a reflection
    px = 60.0
    und = kit.fbm((int(9 * px), int(2 * np.pi * o["R"] * px)), px, 0.5, 2.5, 2.6, 7101)
    su = np.clip((np.arange(len(ring)) - n_in) / max(len(ring) - n_in, 1), 0, 1) * (und.shape[0] - 1)
    bump = cv2.remap(und, (T / (2 * np.pi) * (und.shape[1] - 1)).astype(np.float32), su[I].astype(np.float32), cv2.INTER_LINEAR)
    Rr = Rr + 0.0006 * bump * (I >= n_in)
    Rw = Rr * (1.0 + wob(T) / o["R"])
    P = np.stack([Rw * np.cos(T), Rw * np.sin(T), Zz], -1).astype(np.float32)
    np.savez(path, P=P)
    print(f"[shell] {P.shape[:2]}; water line z {h0:.3f}, r {rc:.3f}", flush=True)


def build_water(path, o, q):
    """Closed: the surface from the middle out to the wall, then the wall back down to the axis, IOR per vertex. Rows run so that normals point out of the water. Glass in, water out: at the wall a ray from the glass enters with 1.33 / 1.5."""
    th = thetas(q)
    ri, zi, _ = profile(o)
    h0, rc = contact(o)
    k = {"preview": 1.0, "mid": 0.5, "final": 0.25}[q]
    d = np.concatenate([np.linspace(rc - 0.0005, 1.0, 50)[:-1], np.linspace(1.0, 0.2, int(50 / k))[:-1], np.geomspace(0.2, 0.0012, int(70 / k)), [0.0]])
    T, Dd = np.meshgrid(th, d)
    r = rc - Dd
    w = wob(T) / o["R"]
    x, y = r * (1 + w) * np.cos(T), r * (1 + w) * np.sin(T)
    t = o["swell_t"]
    swell = 0.0
    for sd, vx, vy in ((7108, 0.12, 0.05), (7109, -0.08, 0.1)):
        sw = kit.fbm((512, 512), 512 / 8.0, 0.5, 4.0, 3.0, sd)
        swell = swell + 0.7 * cv2.remap(sw, np.mod((x - vx * t + 4) / 8 * 511, 511).astype(np.float32), np.mod((y - vy * t + 4) / 8 * 511, 511).astype(np.float32), cv2.INTER_CUBIC)
    z = meniscus(Dd, h0) + o["swell"] * swell * kit.sstep(0.0, 0.2, Dd)
    top = np.stack([x, y, z], -1)
    # the wall, from the contact down to the axis. A stand-in for the swell: not a solved free surface
    j = int(np.searchsorted(zi, h0))
    rw, zw = np.concatenate([[rc - 1e-4], ri[: j + 1][::-1]]), np.concatenate([[h0 - 1e-4], zi[: j + 1][::-1]])
    Tw, Iw = np.meshgrid(th, np.arange(len(rw)))
    Rw = rw[Iw] * (1.0 + wob(Tw) / o["R"])
    wall = np.stack([Rw * np.cos(Tw), Rw * np.sin(Tw), zw[Iw]], -1)
    P = np.concatenate([top, wall]).astype(np.float32)
    ior = np.concatenate([np.full(T.shape, N_WATER), np.full(Tw.shape, N_WATER / N_GLASS)]).astype(np.float32)
    np.savez(path, P=P, ior=ior)
    print(f"[water] {P.shape[:2]}", flush=True)


def strip_grid(L, rad, seed, open_=0.0, q="final"):
    """Loose dark tea, a leaf rolled into a strip (tiao suo). A flat ribbon twisted along a nearly straight spine: its silhouette narrows and widens smoothly as it turns, as a dry strip does, and it comes to a point at both ends. `open_` (0 to 1) lets the far end start to unroll. Returns P, col, thru."""
    rng = np.random.default_rng(seed)
    nu, nv = (280, 40) if q == "final" else (140, 24)
    u = np.linspace(0.0, 1.0, nu)
    v = np.linspace(0.0, 1.0, nv)
    U, V = np.meshgrid(u, v, indexing="ij")
    amp = 0.05 * L
    p1, p2 = rng.uniform(0, 6.28, 2)
    k = rng.uniform(0.7, 1.3)
    Sx = L * U
    Sy = amp * np.sin(k * np.pi * U + p1)
    Sz = amp * np.sin(k * np.pi * U + p2)
    taper = np.clip(U / 0.22, 0.0, 1.0) ** 0.7 * np.clip((1.0 - U) / 0.3, 0.0, 1.0) ** 0.8
    along = np.interp(U[:, 0], np.linspace(0, 1, 6), rng.uniform(0.85, 1.15, 6))[:, None]
    th = 2.0 * np.pi * V
    turns = rng.uniform(1.0, 2.0) * rng.choice([-1.0, 1.0])
    phi = rng.uniform(0, 6.28) + 2.0 * np.pi * turns * U * (1.0 - 0.5 * open_ * U)
    op = open_ * kit.sstep(0.4, 1.0, U)
    a_ = rad * taper * along * (1.0 + 1.4 * op)  # across the ribbon
    b_ = rad * taper * along * (0.42 - 0.2 * op)  # through it
    px = nu / L
    wr = kit.fbm((nu, nv), px, 0.012, 0.1, 2.2, seed + 7)  # fine wrinkles, for the highlights only
    wr[:, -1] = wr[:, 0]
    ca, sa = a_ * np.cos(th) * (1.0 + 0.015 * wr), b_ * np.sin(th) * (1.0 + 0.015 * wr)
    P = np.stack([Sx, Sy + ca * np.cos(phi) - sa * np.sin(phi), Sz + ca * np.sin(phi) + sa * np.cos(phi)], -1)
    # dark red-brown when wet; thin parts let some light through
    mott = kit.fbm((nu, nv), px, 0.03, 0.4 * L, 2.4, seed + 11)
    mott[:, -1] = mott[:, 0]
    tone = np.exp(0.4 * mott)
    col = np.array([0.055, 0.026, 0.012]) * tone[..., None]
    thru = np.array([0.95, 0.42, 0.1]) * np.clip(tone * (0.55 + 0.5 * op + 0.35 * kit.sstep(0.6, 0.1, taper)), 0.0, 1.0)[..., None]
    return P, col, thru


def rot(yaw, pitch, roll):
    cy, sy = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    cr, sr = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
    Ry = np.array([[cp, 0.0, sp], [0.0, 1.0, 0.0], [-sp, 0.0, cp]])
    Rx = np.array([[1.0, 0.0, 0.0], [0.0, cr, -sr], [0.0, sr, cr]])
    return Rz @ Ry @ Rx


def build_strips(sub, tag, o, q):
    """The tea, floating: each strip a grid whose top stands `z` above the surface (a little, as soaked tea floats low). An error if one is out at the wall or sunk."""
    out = []
    for si, s in enumerate(o["strips"]):
        P, col, thru = strip_grid(s["len"], s["rad"], s["seed"], s.get("open", 0.0), q)
        # a floating thing moves slowly on the water: a small drift, turning a little, and the surface lifts it
        t = o["swell_t"]
        d = np.random.default_rng(s["seed"] + 500).uniform(-1.0, 1.0, 3)
        W = (P @ rot(s["yaw"] + 1.6 * d[2] * t, s["pitch"], s.get("roll", 0.0)).T) + np.array([s["x"] + 0.03 * d[0] * t, s["y"] + 0.03 * d[1] * t, 0.0])
        W[..., 2] += s["z"] - W[..., 2].max() + 0.004 * np.sin(1.3 * t + s["seed"])
        reach = np.hypot(W[..., 0], W[..., 1]).max()
        if reach > o["R"] - 0.4 or W[..., 2].min() < -0.5 or s["z"] > 0.06:
            raise SystemExit(f"strip {si} is not floating: z {W[..., 2].min():.3f} to {W[..., 2].max():.3f}, reach {reach:.2f}")
        path = os.path.join(sub, f"{tag}_st{si}.npz")
        np.savez(path, P=W.astype(np.float32), col=np.asarray(col, np.float32), thru=np.asarray(thru, np.float32))
        out.append(path)
    return out


def camera(o):
    e = np.radians(o["E"])
    view = np.array([0.0, -np.cos(e), np.sin(e)])
    up = np.array([0.0, np.sin(e), np.cos(e)])
    H = o["W"] * 9.0 / 16.0
    # the arc at apex_y: from above, the far rim; from below the water, the near rim, which then curves upward
    A = np.array([0.0, (1.0 if o["E"] > 0 else -1.0) * (o["R"] + o["flare"]), o["z_rim"]])
    target = A - up * (0.5 - o["apex_y"]) * H
    loc = target + view * o["dist"]
    cam = {"loc": loc.tolist(), "target": target.tolist(), "lens_mm": 36.0 * o["dist"] / o["W"], "roll": 0.0}
    if o["aperture"]:
        fp = np.array([0.0, o["focus_y"], -0.5])
        cam["aperture_mm"] = o["aperture"]
        cam["focus_distance"] = float(np.dot(loc - fp, view))
    return cam


def env(path, cam, o):
    """The room, for reflections only. Directions in the world: +y is behind the bowl, away from the camera."""
    kit.room_env(path, cam, {"window": 0.0, "strip": 0.0, "ceil": 0.012, "wall": 0.006, "floor": 0.004})
    E = np.load(path)
    h, w = E.shape[:2]
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    el = np.degrees(np.arcsin(np.clip(d[..., 2], -1, 1)))
    az_back = np.degrees(np.arctan2(d[..., 0], d[..., 1]))  # 0 straight behind the bowl
    az_cam = np.degrees(np.arctan2(d[..., 0], -d[..., 1]))  # 0 straight behind the camera
    # A lit wall behind the bowl with a black flag on it, just filling the frame, as a photographer would: the air around the bowl is dark, and every ray the water bends off the flag finds the wall. Traced in the plane of the axis, the body of the liquid leaves climbing at 6 to 9 degrees; rays over the water, through glass alone, at 2 or less. Rays near the walls leave far to the side, or mirrored down by the underside of the surface
    half = np.degrees(np.arctan(o["W"] * 9 / 32 / o["dist"]))
    wide = np.degrees(np.arctan(o["W"] / 2 / o["dist"]))
    top, bot = -o["E"] + half, -o["E"] - half
    flag = (1.0 - kit.sstep(top + o["flag_up"][0], top + o["flag_up"][1], el)) * (1.0 - kit.sstep(bot - 0.4, bot - 3.6, el)) * (1.0 - kit.sstep(wide + 1.0, wide + 6.0, np.abs(az_back)))
    fall = np.exp(-0.5 * ((az_back - o["room_az0"]) / o["room_az"]) ** 2) * np.exp(-0.5 * (np.maximum(el - 8.0, 0.0) / o["room_el"]) ** 2)
    glow = (1.0 - flag) * kit.sstep(65.0, 35.0, el) * kit.sstep(-75.0, -50.0, el) * fall * (o["room_low"] + (1.0 - o["room_low"]) * kit.sstep(-6.0, 2.0, el))
    # a warm lamp on a wall: nearly white where it is brightest, amber where it falls away
    tint = np.array(o["room_rim"], np.float32) + (np.array(o["room_rgb"], np.float32) - np.array(o["room_rim"], np.float32)) * (fall**0.8)[..., None].astype(np.float32)
    E = E + (o["surf_L"] * glow)[..., None].astype(np.float32) * tint
    strip = (kit.sstep(10.0, 22.0, np.abs(az_back)) * kit.sstep(42.0, 28.0, np.abs(az_back))) * kit.sstep(-55.0, -40.0, el) * kit.sstep(45.0, 30.0, el)
    E = E + (o["edge_L"] * strip)[..., None].astype(np.float32) * np.array([1.0, 0.92, 0.78], np.float32)
    if o.get("debug_env"):  # which way did each ray go: red up, green behind the bowl, blue towards the camera; brightness by elevation bands
        E = np.stack([(el > 0) * 1.0, (d[..., 1] > 0) * 1.0, (d[..., 1] <= 0) * 1.0], -1) * (0.35 + 0.65 * (np.mod(el, 20.0) > 10.0))[..., None]
    np.save(path, E.astype(np.float32))


def scene(q, o, sub, tag, base=None):
    cam = camera(o)
    os.makedirs(sub, exist_ok=True)
    b = base or tag
    shell, sky, e = [os.path.join(sub, f"{b}_{n}") for n in ("shell.npz", "sky.npz", "env.npy")]
    water = os.path.join(sub, f"{tag}_water.npz")
    if not (base and os.path.exists(shell)):
        build_shell(shell, o, q)
        sky = kit.sky_mesh(sky, cam, {"top": [0.0065, 0.0065, 0.0066], "glow": [0.016, 0.0155, 0.015], "y0": 0.3, "h": 0.6, "x0": 0.55, "mottle": 0.12})
        env(e, cam, o)
    build_water(water, o, q)
    glow = {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}
    meshes = [
        {"name": "shell", "npz": shell, "shader_py": SHP, "params": {"kind": "glass", "ior": N_GLASS}},
        {"name": "water", "npz": water, "shader_py": SHP, "params": {"kind": "water", "liquor": o["liquor"], "sigma": SIGMA}},
        # seen only directly, past the bowl. Rays through the liquid climb by 6 to 9 degrees (traced), into its large sheet, and it turned the top of the liquid into a black band
        {"name": "sky", "npz": sky, "material": glow, "visible": {"diffuse": False, "shadow": False, "transmission": False, "glossy": False}},
    ]
    for i, sp in enumerate(build_strips(sub, b, o, q)):
        meshes.append({"name": f"leaf{i}", "npz": sp, "shader_py": SHP, "params": {"kind": "leaf"}})
    vols = []
    if o["tea"]:
        sim = os.path.join(kit.OUT, "s70_sim", o["tea"])
        vdb = os.path.join(sim, o["tea_t"] + ".vdb")
        if not os.path.exists(vdb):
            raise SystemExit(f"no solve frame: {vdb}")
        vols.append({"name": "tea", "vdb": vdb, "shader_py": SHP, "params": {"kind": "tea", "sigma": SIGMA, "K": o["tea_K"]}})
    return {
        "camera": cam,
        "meshes": meshes,
        "volumes": vols,
        "lights": [],
        "env": {"npy": e, "diffuse": True, "transmission": True},  # diffuse: what lights the leaves from behind
        "bounces": 32,
        "transmission_bounces": 28,
        "glossy_bounces": 12,
        "diffuse_bounces": 2,
        "volume_bounces": 0,
        "clamp_indirect": 30.0,
        "denoise": o.get("denoise", True),
        "res": {"preview": [960, 540], "mid": [1280, 720], "final": [1920, 1080]}[q],
        "spp": o["spp"] or {"preview": 64, "mid": 128, "final": 256}[q],
    }


DEVELOP = dict(exposure=0.0, contrast=1.15, saturation=1.08, black=0.0, grain=1.1, sharpen=0.22, halation=0.05, glare=0.0, vignette=0.1, ca=0.0003, seed=71)


def render(cfg, sub, tag):
    return kit._render_local(cfg, sub, tag)


def look(tag, over, q):
    from darkroom import develop, print_look

    o = {**P0, **over}
    os.makedirs(D, exist_ok=True)
    cfg = scene(q, o, D, tag)
    t = time.time()
    p = render(cfg, D, tag)
    print(f"[{tag}] {time.time()-t:.0f} s", flush=True)
    L = np.load(p)
    print(tag, "p50", np.median(L, axis=(0, 1)).round(3), "p99", np.percentile(L, 99, axis=(0, 1)).round(3), flush=True)
    x = print_look(develop(L.astype(np.float32), **{**DEVELOP, **o["dev"], "exposure": o["exposure"]}))
    cv2.imwrite(os.path.join(D, tag + ".jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])


def take(over, q, first, n, step=1.0 / 48):
    """Frames of a solve saved at first + i * step. out/v2/s71_liuli_take_{q}/{v###.jpg, take.mp4}; at final also s71_liuli_move_final/{take.linear_###.npy, develop.json}, which is what film.py reads."""
    from darkroom import develop, print_look

    o = {**P0, **over}
    d = os.path.join(kit.OUT, f"{NAME}_take_{q}")
    os.makedirs(d, exist_ok=True)
    dev = {**DEVELOP, **o["dev"], "exposure": o["exposure"]}
    mv = None
    if q == "final":
        mv = os.path.join(kit.OUT, f"{NAME}_move_final")
        os.makedirs(mv, exist_ok=True)
        json.dump(dev, open(os.path.join(mv, "develop.json"), "w"))
    for i in range(n):
        t = first + i * step
        tag = f"f{i:03d}"
        t0 = time.time()
        L = np.load(render(scene(q, {**o, "tea_t": f"{t:07.3f}", "swell_t": i * step}, d, tag, base="take"), d, tag))
        if mv:
            np.save(os.path.join(mv, f"take.linear_{i:03d}.npy"), L.astype(np.float32))
        x = print_look(develop(L.astype(np.float32), **{**dev, "seed": 7100 + i}))
        cv2.imwrite(os.path.join(d, f"v{i:03d}.jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        os.remove(os.path.join(d, f"{tag}.linear.npy"))
        print(f"[{tag}] t={t:.3f}, {time.time()-t0:.0f} s", flush=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(d, "v%03d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", os.path.join(d, "take.mp4")], check=True)


def args(s):
    if not s or s == "-":
        return {}
    if s.startswith("@"):
        return json.load(open(s[1:]))
    return {k: json.loads(v) for k, v in (kv.split("=", 1) for kv in s.split(","))}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "look":
        look(sys.argv[2], args(sys.argv[3]) if len(sys.argv) > 3 else {}, sys.argv[4] if len(sys.argv) > 4 else "preview")
    elif cmd == "take":  # take k=v,.. QUALITY FIRST N
        take(args(sys.argv[2]), sys.argv[3], float(sys.argv[4]), int(sys.argv[5]), 1.0 / float(sys.argv[6]) if len(sys.argv) > 6 else 1.0 / 48)
    else:
        raise SystemExit(__doc__)
