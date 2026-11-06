"""Shot 63: a strand of southern red agate (南红念珠) let down on black lacquer by two hands out of frame. It hangs as a slack V, and its mirror image in the lacquer as the opposite V, so that the picture is an X closing. The lowest bead meets its own reflection first, and the touching runs outward both ways until the strand lies as the arc.

    python3 -I v2/stills/s63_nanhong.py take [preview|mid|final]      all frames: out/v2/s63_nanhong_take_cand/ (preview, mid: s63_nanhong_take_<q>_cand/) with f###.png, take.mp4 and sheet.jpg
    python3 -I v2/stills/s63_nanhong.py frame N [preview|mid|final]   one frame, with its motion blur



Earlier actions: a jerk along a strand lying on the table; one hand laying it from the right, which fell on itself in a zigzag, with a curtain of beads at the frame's edge and no clean arc; the same two hands as here but through a full simulation (s63_chain.run_zip), which measured a rebound of .37 cm, speeds up to 35 cm/s and beads changing direction, against a target of one direction, slow, even, no rebound and no tremble. Why this one: the arc is whole in every frame, the composition is closed by the mirror, it ends on a clean arc at the film's height, and it moves as a very slow lowering does: in equilibrium at every moment, measured 6 cm/s at most, no rebound.

True geometry, true light paths: no emission anywhere. Every bead and every span of thread is its own rigid object, keyed frame by frame, with real motion blur (s63_shader.rigid_take). Beads are closed solids with a real countersunk hole and a slightly lumpy hand-polished form, in true random-walk subsurface. See s63_chain.run_settle for the motion, s63_shader.stone for the stone.
Light and stone are the 17:15 version chosen (frame012_final): two large soft area lights high up and the room law SKY mirrored by the lacquer.
ESTIMATES, none measured: bead sizes, thread gap, subsurface radius, all colours, lacquer unevenness and scratches, how hands lower a strand (s63_chain.run_settle).
STAND-INS: the pattern's depth is by parallax in the shader, not a true medium. The thread between two beads is straight, a short rigid peanut section; the hole's inside is a short blind cone.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, _cam_axes, _render_local, fbm, frame_camera
import s63_chain as chain

NAME = "s63_nanhong"
SEED = 63
N = 54
FRAMES = 40
FPS = 25.0
SHAPE = {"R": (0.65, 0.75), "gap": (0.1, 0.26), "theta_max": np.radians(60.0), "s0": 14.0}
ZIP = {"apex": 27, "half": 14, "v": 6.0, "a": 5.0, "t_kiss": 0.16, "vz": 4.0, "b": 0.05}
FIRST = ZIP["apex"] - ZIP["half"]  # bead k here is bead FIRST + k of the 54: the same stones as in the chosen picture
CX = 0.0
EL = np.radians(24.0)
W = 16.0
DIST = 70.0
APERTURE = 50.0
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)])
UP = np.array([0.0, np.sin(EL), np.cos(EL)])
RIGHT = np.array([1.0, 0.0, 0.0])
APEX_Y = 0.45
SKY = {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "y0": 0.3, "x0": 0.62, "h": 0.62, "mottle": 0.12}  # the film's room
SHADER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s63_shader.py")
LOOK = {"exposure": 0.0, "contrast": 1.2, "saturation": 1.0, "grain": 1.0, "sharpen": 0.15, "halation": 0.05, "vignette": 0.2}
STONE = {"kind": "stone"}
KEY = {"dir": [-0.5, -0.32, 0.8], "dist": 130.0, "size": [110, 150], "watts": 300000}
BACK = {"dir": [0.3, 0.32, 0.9], "dist": 130.0, "size": [200, 120], "watts": 200000}
PERSIMMON, BROCADE = np.array(os.environ.get("S63_P", "0.56,0.056,0.01").split(","), float), np.array(os.environ.get("S63_B", "0.36,0.026,0.006").split(","), float)


def simulate():
    return chain.run_settle(FPS, FRAMES, ZIP, SHAPE, n=N, seed=SEED, pad=1)


def camera(s):
    """Framed on where the beads end up, so that the arc is right at the end of the take: the highest bead of those lying on the table in the last frame goes to APEX_Y, the middle of the landed curve to the middle of the frame."""
    x = s["x"][-1]
    on = x[:, 2] < s["R"] + 0.03
    H = W * 9.0 / 16.0
    near = on & (np.abs(x[:, 0]) < 8.0)
    u = x[near] @ UP + s["R"][near]
    k = np.nonzero(near)[0][int(np.argmax(u))]
    top = x[k] + UP * s["R"][k]
    tgt = top + UP * (APEX_Y - 0.5) * H
    tgt = tgt + RIGHT * (CX - tgt[0])
    return frame_camera(tgt, VIEW, W, DIST, aperture_mm=APERTURE, focus_point=x[k] + VIEW * s["R"][k])


def noise3(d, freq, seed):
    from scipy.ndimage import map_coordinates

    g = np.random.default_rng(seed).normal(0, 1, (48, 48, 48))
    return map_coordinates(g, (d * freq + 24.0).T, order=1, mode="wrap")


def grid_faces(nv, nu):
    i, j = np.meshgrid(np.arange(nv - 1), np.arange(nu), indexing="ij")
    a = (i * nu + j).reshape(-1)
    b = (i * nu + (j + 1) % nu).reshape(-1)
    c = ((i + 1) * nu + j).reshape(-1)
    e = ((i + 1) * nu + (j + 1) % nu).reshape(-1)
    return np.vstack([np.stack([a, c, b], 1), np.stack([b, c, e], 1)])


def normals(V, F):
    n = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for c in range(3):
        np.add.at(n, F[:, c], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def profile(R, nv):
    """A bead's profile, top pole to bottom pole, as (rho, z) in cm, with a real drilled mouth at each end: a blind bore, a small bevel, then the ball. Returns rho, z and the distance from the mouth's rim along the surface."""
    rh, depth, bev = 0.085, 0.42 * R, 0.05  # bore radius, how deep it is modelled, bevel size [estimates]
    a0 = np.arcsin((rh + bev) / R)
    th = np.linspace(a0, np.pi - a0, nv)
    zc = R * np.cos(a0)
    ball = np.stack([R * np.sin(th), R * np.cos(th)], 1)
    t = np.linspace(0, 1, 7)[:-1]
    bevel = np.stack([rh + bev * t**1.5, (zc - bev * 0.7) + bev * 0.7 * (t * (2 - t))], 1)
    bore = np.stack([np.full(5, rh), np.linspace(zc - depth, zc - bev * 0.7, 6)[:-1]], 1)
    cap = np.array([[1e-3, zc - depth]])
    top = np.vstack([cap, bore, bevel])
    bot = top[::-1] * np.array([1.0, -1.0])
    P = np.vstack([top, ball, bot])
    # distance from the rim: 0 inside the bore
    dtop = np.r_[np.zeros(len(top) - 6), np.linspace(0, bev, 6)]
    d_ball = np.minimum(R * (th - a0), R * (np.pi - a0 - th)) + bev
    return P[:, 0], P[:, 1], np.r_[dtop, d_ball, dtop[::-1]]


class Bead:
    def __init__(self, k, R, res, rng):
        nu, nv = res
        rho, z, rim = profile(R, nv)
        ph = np.linspace(0, 2 * np.pi, nu, endpoint=False)
        V = np.stack([np.outer(rho, np.cos(ph)), np.outer(rho, np.sin(ph)), np.outer(z, np.ones(nu))], -1).reshape(-1, 3)
        F = grid_faces(len(rho), nu)
        d = V / np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)
        # hand polish: not a true sphere. Slow lumps, a slight flattening towards the holes [amplitudes estimated]
        lump = 0.014 * noise3(d, 1.3, 3000 + k) + 0.004 * noise3(d, 3.2, 3100 + k)
        away = np.clip(np.repeat(rim, nu) / 0.25, 0, 1)
        V = V * (1 + lump * away)[:, None] * np.array([1.0, 1.0, rng.uniform(0.95, 0.99)])
        self.V, self.F = V.astype(np.float32), F.astype(np.int32)
        ax = rng.normal(0, 1, 3)
        ax /= np.linalg.norm(ax)
        off = rng.uniform(-40, 40, 3)
        # the band's plane cuts the ball near its middle: a plane near the ball's edge would draw a pale disc, not a band
        off += ax * (np.round(off @ ax * 1.9 / np.pi) * np.pi / 1.9 + rng.uniform(-0.3, 0.3) * R - off @ ax)
        self.lp = (V + off).astype(np.float32)
        self.wear = np.exp(-((np.repeat(rim, nu) / 0.075) ** 2)).astype(np.float32)
        c = PERSIMMON + (BROCADE - PERSIMMON) * rng.beta(1.6, 2.0)
        self.col = np.tile(c, (len(V), 1)).astype(np.float32)
        self.ax = np.tile(ax, (len(V), 1)).astype(np.float32)
        band = rng.uniform(0.2, 0.5) if rng.random() < 0.14 else 0.0
        crack = rng.uniform(0.5, 1.0) if rng.random() < 0.4 else 0.0
        self.par = np.tile([band, rng.uniform(0.75, 1.0), crack], (len(V), 1)).astype(np.float32)


def build_beads(s, q):
    res = {"preview": (180, 90), "mid": (240, 120), "final": (360, 180)}[q]
    cam = camera(s)
    d = s["x"].reshape(-1, 3)
    vis = np.zeros(s["x"].shape[1], bool)
    from vessel import project

    for f in range(s["x"].shape[0]):
        px, py, _ = project(cam, s["x"][f])
        vis |= (px > -0.15) & (px < 1.15) & (py > -0.25) & (py < 1.25)
        px, py, _ = project(cam, s["x"][f] * np.array([1.0, 1.0, -1.0]))  # and in the lacquer
        vis |= (px > -0.15) & (px < 1.15) & (py > -0.25) & (py < 1.25)
    beads = {}
    for k in range(s["x"].shape[1]):
        rk = np.random.default_rng(SEED * 1000 + FIRST + k)
        beads[k] = Bead(FIRST + k, s["R"][k], res if vis[k] else (48, 24), rk)
    print(f"beads {len(beads)}, seen {int(vis.sum())}", flush=True)
    return beads


def silk_span(path, ns=24, nr=10, rad=0.052):
    """A span of the silk along +z from 0 to 1, rigid; the object's scale gives its length. Two plies twisted: the section is a peanut that turns along the length."""
    u = np.linspace(0, 1, ns)
    ph = np.linspace(0, 2 * np.pi, nr, endpoint=False)
    r = rad * (1 + 0.18 * np.cos(2 * ph[None] - 2 * np.pi * u[:, None] * 2.5))
    V = np.stack([r * np.cos(ph)[None], r * np.sin(ph)[None], u[:, None].repeat(nr, 1)], -1).reshape(-1, 3)
    F = grid_faces(ns, nr)[:, [0, 2, 1]]
    np.savez(path, V=V.astype(np.float32), F=F, col=np.tile(np.array([0.045, 0.003, 0.004], np.float32), (len(V), 1)))
    return path


def rot_z_to(d):
    """Quaternion (w, x, y, z) that turns +z onto the unit vector d."""
    return chain.axis_quat(d)


def tracks(s):
    """Per object, per key: location, rotation, stretch along z."""
    x, q, R = s["x"], s["q"], s["R"]
    an = {}
    for k in range(x.shape[1]):
        an[f"bead{k:02d}"] = np.c_[x[:, k], q[:, k], np.ones(len(x))].tolist()
    for k in range(x.shape[1] - 1):
        d = x[:, k + 1] - x[:, k]
        dist = np.linalg.norm(d, axis=1, keepdims=True)
        dn = d / np.maximum(dist, 1e-9)
        a = x[:, k] + dn * R[k] * 0.62
        ln = np.maximum(dist[:, 0] - (R[k] + R[k + 1]) * 0.62, 0.02)
        qq = np.array([rot_z_to(v) for v in dn])
        an[f"silk{k:02d}"] = np.c_[a, qq, ln].tolist()
    return an


def write_meshes(s, beads, dd):
    """Every bead and span once, in its own frame."""
    ents = []
    silk = silk_span(os.path.join(dd, "s63_silk.npz"))
    for k, b in beads.items():
        p = os.path.join(dd, f"s63_bead{k:02d}.npz")
        np.savez(p, V=b.V, F=b.F, lp=b.lp, col=b.col, ax=b.ax, par=b.par, wear=b.wear)
        ents.append({"name": f"bead{k:02d}", "npz": p, "shader_py": SHADER, "params": STONE})
    for k in range(len(beads) - 1):
        ents.append({"name": f"silk{k:02d}", "npz": silk, "shader_py": SHADER, "params": {"kind": "thread"}})
    return ents


def lacquer(npz):
    X, Y = np.meshgrid(np.linspace(-90, 90, 3), np.linspace(-90, 160, 3))
    np.savez(npz, P=np.stack([X, Y, 0 * X], -1).astype(np.float32))


def fresnel(cosi, n=1.5):
    g = np.sqrt(n * n - 1 + cosi * cosi)
    a, b = (g - cosi) / (g + cosi), (cosi * (g + cosi) - 1) / (cosi * (g - cosi) + 1)
    return 0.5 * a * a * (1 + b * b)


def room(cam, path):
    """The room, in world directions. Below: nearly nothing. Above: the film's room law as the table mirrors it into the frame, so the lacquer in the picture has those levels. No window, no band; the room's walls go on smoothly around."""
    from kit import fbm as fb

    h, w = 1024, 2048
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)  # Blender's equirect: u = 0.5 - atan2(y, x) / 2pi
    rt, ut, bk = [np.array(v, float) for v in _cam_axes(cam)]
    v = d * np.array([1.0, 1.0, -1.0])  # the camera ray which the table sends to this direction
    fw = np.maximum(-(v @ bk), 1e-3)
    H = W * 9.0 / 16.0
    x = 0.5 + (v @ rt) / fw * DIST / W
    y = 0.5 - (v @ ut) / fw * DIST / H
    dist = np.hypot((x - SKY["x0"]) * 0.62, y - SKY["y0"]) / SKY["h"]
    t = np.exp(-(np.minimum(dist, 20.0) ** 1.7))[..., None]
    F = fresnel(np.clip(d[..., 2:3], 0.05, 1.0))
    T = np.array(SKY["top"]) * (1 - t) + np.array(SKY["glow"]) * t
    m = fb((h // 4, w // 4), 1.0, 12.0, 300.0, beta=3.0, seed=63).astype(np.float32)
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_CUBIC)
    E = T / F * np.exp(SKY["mottle"] * 0.42 * m)[..., None]
    E = E * (d[..., 2:3] > 0) + 0.02 * (d[..., 2:3] <= 0)
    E = np.minimum(E, 0.2)
    np.save(path, E.astype(np.float32))
    return path


def lamp(name, spec, tgt):
    d = np.array(spec["dir"], float)
    d /= np.linalg.norm(d)
    out = {"name": name, "loc": (tgt + d * spec["dist"]).tolist(), "target": tgt.tolist(), "size": spec["size"], "watts": spec["watts"], "rgb": spec.get("rgb", [1.0, 0.97, 0.93])}
    if spec.get("hide_in_gloss"):
        out["hide_in_gloss"] = True
    return out


def scene_for(cam, ents, npt, env):
    tgt = np.array(cam["target"], float)
    return {
        "camera": dict(cam),
        "meshes": [dict(e) for e in ents] + [{"name": "table", "npz": npt, "shader_py": SHADER, "params": {"kind": "lacquer"}}],
        "lights": [lamp("key", KEY, tgt), lamp("back", BACK, tgt)],
        "env": {"npy": env, "diffuse": True},
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "seed": 1,
    }


def render(cfg, name, frames, res, spp, only=None):
    """All frames of a take through kit. Back come linear frames; develop them here."""
    dd = os.path.join(OUT, name)
    cam = cfg["camera"]
    path = [{"loc": cam["loc"], "target": cam["target"], "roll": 0.0, "lens_mm": cam["lens_mm"], "focus_distance": cam["focus_distance"]} for _ in frames]
    cfg = dict(cfg, res=list(res), spp=spp, frames=path, fetch_to=dd, shutter=0.5, anim=cfg["anim"], anim_pad=1)
    if only is not None:
        cfg["anim_only"] = only
    here = os.path.join(OUT, NAME)
    os.makedirs(here, exist_ok=True)
    os.makedirs(dd, exist_ok=True)
    _render_local(cfg, here, "take")


def develop_all(name, n):
    from darkroom import develop, save_png

    dd = os.path.join(OUT, name)
    for i in range(n):
        L = np.load(os.path.join(dd, f"take.linear_{i:03d}.npy")).astype(np.float32)
        save_png(os.path.join(dd, f"f{i:03d}.png"), develop(L, **{**LOOK, "seed": i + 1}))
    json_path = os.path.join(dd, "develop.json")
    with open(json_path, "w") as f:
        import json

        json.dump(LOOK, f)


def contact(name, n):
    dd = os.path.join(OUT, name)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(dd, "f%03d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(dd, "take.mp4")], check=True)
    ims = [cv2.imread(os.path.join(dd, f"f{f:03d}.png")) for f in range(0, n, 2)]
    rows = [np.hstack([cv2.resize(i, (640, 360), interpolation=cv2.INTER_AREA) for i in ims[r : r + 3]]) for r in range(0, len(ims) - 2, 3)]  # 8 bits: enough for a look
    cv2.imwrite(os.path.join(dd, "sheet.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])


def setup(q, dd):
    s = simulate()
    cam = camera(s)
    print(f"camera at {cam['loc']}, lens {cam['lens_mm']:.0f} mm", flush=True)
    beads = build_beads(s, q)
    os.makedirs(dd, exist_ok=True)
    ents = write_meshes(s, beads, dd)
    npt = os.path.join(dd, "s63_table.npz")
    lacquer(npt)
    env = room(cam, os.path.join(dd, "s63_room.npy"))
    cfg = scene_for(cam, ents, npt, env)
    cfg["anim"] = tracks(s)
    return s, cfg


RES = {"preview": (960, 540), "mid": (1280, 720), "final": (2560, 1440)}
SPP = {"preview": 96, "mid": 160, "final": 320}


def take(q):
    name = f"{NAME}_take_cand" if q == "final" else f"{NAME}_take_{q}_cand"  # not _take_final: nothing goes in the film until it has been seen
    dd = os.path.join(OUT, name)
    s, cfg = setup(q, os.path.join(OUT, NAME, f"m_{q}"))
    if os.path.isdir(dd):
        for f in os.listdir(dd):
            os.remove(os.path.join(dd, f))
    os.makedirs(dd, exist_ok=True)
    render(cfg, name, range(FRAMES), RES[q], SPP[q])
    develop_all(name, FRAMES)
    contact(name, FRAMES)
    print(os.path.join(dd, "take.mp4"))


def frame(i, q, tag=None):
    name = f"{NAME}_frame_{i:03d}_{q}{os.environ.get('S63_TAG', '')}"
    dd = os.path.join(OUT, name)
    s, cfg = setup(q, os.path.join(OUT, NAME, f"m_{q}"))
    os.makedirs(dd, exist_ok=True)
    render(cfg, name, [0], RES[q], SPP[q], only=i)
    from darkroom import develop

    L = np.load(os.path.join(dd, "take.linear_000.npy")).astype(np.float32)
    print(f"linear p50 {np.median(L):.4f} p99 {np.percentile(L, 99):.3f} max {L.max():.1f}", flush=True)
    im = develop(L, **LOOK)
    cv2.imwrite(os.path.join(dd, "f.jpg"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(os.path.join(dd, "f.jpg"))


def main():
    a = sys.argv[1:] or ["frame", "12", "preview"]
    if a[0] == "take":
        take(a[1] if len(a) > 1 else "preview")
    else:
        frame(int(a[1]), a[2] if len(a) > 2 else "preview")


main()
