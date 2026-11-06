"""Shot 39, the candidate: a lotus half open against the sun, in the leaf field, opening a little. s39_hehua.py is left as it was and still gives the old final.

    python3 -I v2/stills/s39_cand.py layout [TS=.47 ...]        the motion through the camera, no render, seconds
    python3 -I v2/stills/s39_cand.py still preview|mid|final    goes to out/v2/s39_hehua_wind/{preview,mid,cand}.*
    python3 -I v2/stills/s39_cand.py take low|check|final       goes to out/v2/s39_hehua_wind_move_{preview,final}
    python3 -I v2/stills/s39_cand.py deliver DIR                frames of a take as out/v2/s39_hehua_take_cand (f###.png, take.mp4)

Geometry and maps: s39_petal.py. Material: s39_shader.py. Motion: s39_wind.py. Composition, sun, leaves and develop are those of s39_hehua.py.
The camera does not move, nor do the leaves: only petals. Motion blur: the mesh has no keyframes, so each frame is SUB sub-exposures over a 180 degree shutter, averaged. Sizes and all motion numbers are estimates, see those files. Below the frame there is no stem or receptacle.
"""

import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
from kit import OUT, frame_camera, shoot
from lotuslib import FAR_MAT, SHEET, pond_env, stalk, water
from vessel import project, view_dir

import s39_petal as PT
import s39_wind as WD

NAME = "s39_hehua"
RUN = NAME + "_wind" + os.environ.get("S39_TAG", "")  # a tag keeps a variant apart
HERE = os.path.dirname(os.path.abspath(__file__))
SHADER = os.path.join(HERE, "s39_shader.py")
W, EL, DIST = 31.0, 4.0, 150.0
APEX = 0.27
APERTURE = 19.0
SUN = np.array([-0.42, 0.62, 0.66])
SUN = SUN / np.linalg.norm(SUN)
MAT = {"rough": 0.62, "spec": 0.18, "sheen": 0.95, "sheen_rough": 0.55, "bump": 0.1}
LOOK = {"exposure": 0.12, "contrast": 1.14, "saturation": 1.08, "black": 0.001, "grain": 0.9, "sharpen": 0.28, "halation": 0.05, "glare": 0.004, "vignette": 0.3}
FRAMES, SUB, SHUTTER = 36, 2, 0.5  # slow, a tip moves a few px a frame, so two sub-exposures make its blur
RES = {"layout": (40, 20), "preview": (130, 64), "mid": (200, 90), "final": (300, 130)}
DENS = {"preview": 0.4, "mid": 0.65, "final": 1.0}
STILL_FRAME = 15.0  # where in the take the still stands


def whorl(az, base, seed, expo, jit=(5.0, 3.0)):
    r = np.random.default_rng(seed)
    out = []
    for i, a in enumerate(az):
        sp = dict(base)
        sp["az"] = a
        sp["seed"] = seed + 100 * i
        sp["alpha"] = base["alpha"] + r.normal(0, jit[0])
        sp["L"] = base["L"] * r.uniform(0.94, 1.05)
        sp["W"] = base["W"] * r.uniform(0.93, 1.06)
        sp["twist"] = r.normal(0, 7.0)
        sp["lean"] = r.normal(0, 0.45)
        # individuals: drawn after the old draws, so that the old flower stays underneath
        q = np.random.default_rng(seed + 50 + i)
        sp["az"] = a + q.normal(0, 5.0)
        sp["alpha"] += q.normal(0, 0.8 * jit[0])
        sp["L"] *= q.uniform(0.88, 1.08)
        sp["W"] *= q.uniform(0.84, 1.12)
        sp["twist"] += q.normal(0, 10.0)
        sp["lean"] += q.normal(0, 0.75)
        sp["P"] = 1.35 * base["P"] * r.uniform(0.88, 1.12)
        sp["expo"] = expo * r.uniform(0.85, 1.15)
        out.append(sp)
    return out


def flower():
    """From the middle out, the same whorls and draws as s39_hehua.flower, so the same flower."""
    A = whorl([-62, 12, 86, 158, 230], dict(L=12.6, W=6.0, alpha=4, beta=26, gamma=30, psi=74, r0=0.8, zb=0.9, P=0.9, g0=0.3, d=0.45, roll=0.12, bump=0.1), 3910, 0.16, (3.0, 2.0))
    B = whorl([-93, -30, 30, 90, 150, 210], dict(L=12.0, W=7.5, alpha=17, beta=24, gamma=24, psi=58, r0=1.5, zb=0.4, P=1.0, g0=0.22, d=0.7, roll=0.2, bump=0.09), 3920, 0.32, (2.5, 2.0))
    C = whorl([-125, -62, -8, 46, 102, 158, 214], dict(L=12.6, W=7.9, alpha=42, beta=22, gamma=28, psi=42, r0=2.2, zb=0.1, P=0.85, g0=0.28, d=0.9, roll=0.3, bump=0.13), 3930, 0.6, (5.0, 3.0))
    D = whorl([-152, -96, -38, 28, 88, 150], dict(L=12.0, W=7.2, alpha=70, beta=16, gamma=38, psi=30, r0=2.8, zb=-0.5, P=0.8, g0=0.3, d=0.9, roll=0.34, bump=0.16), 3940, 0.85, (7.0, 4.0))
    E = whorl([-120, -60, 0, 60, 120, 180], dict(L=10.5, W=6.2, alpha=96, beta=6, gamma=24, psi=26, r0=3.0, zb=-1.2, P=0.85, g0=0.25, d=0.5, roll=0.34, bump=0.2), 3950, 1.0, (7.0, 4.0))
    B[0].update(az=-93.0, alpha=15.0, d=1.0, twist=4.0, lean=0.2, L=12.3, W=7.9)  # the one in focus, that looks at the camera
    return A + B + C + D + E


def field_spec():
    """The leaves of s39_hehua.field, same draws, as numbers."""
    rng = np.random.default_rng(39)
    out = []
    for i in range(70):
        y = float(np.exp(rng.uniform(np.log(70.0), np.log(1500.0))))
        half = 0.55 * W * (DIST + y) / DIST
        x = float(rng.uniform(-half, half))
        z = float(rng.uniform(-42.0, 4.0))
        R = float(rng.uniform(16.0, 30.0))
        tilt, az = float(rng.uniform(0, 26)), float(rng.uniform(0, 360))
        st = None
        if y < 260 and rng.random() < 0.7:
            st = (float(rng.normal(0, 3)), float(rng.normal(0, 3)))
        out.append(dict(i=i, x=x, y=y, z=z, R=R, tilt=tilt, az=az, stalk=st))
    return out


FAR = (("ff", (-37.0, 330.0, -6.0), None), ("fb", (37.0, 300.0, -6.0), 5), ("fc", (27.0, 230.0, 10.0), None))


def camera(meshes, specs):
    H = W * 9 / 16
    view = view_dir(-90.0, EL)
    tgt = np.array([0.0, 0.0, 6.0])
    tops = np.concatenate([m.pose()[-12:].reshape(-1, 3) for m in meshes])
    for _ in range(4):
        cam = frame_camera(tgt, view, W, DIST)
        _, y, _ = project(cam, tops)
        tgt[2] -= (float(y.min()) - APEX) * H
    hero = meshes[5].pose()
    focus = hero[int(0.62 * hero.shape[0]), hero.shape[1] // 2]
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, tops)
    print(f"apex y {y.min():.3f}, x span {x.min():.2f}..{x.max():.2f}", flush=True)
    return cam, tgt


def leaf(path, at, R, tilt, azim, seed, n=48):
    """A leaf of the field: a shallow dish with a wavy rim. Unlike lotuslib.far_leaf it has ribs in its relief and colour and a tone of its own, because the nearest leaves are only half lost in the blur."""
    rng = np.random.default_rng(seed)
    rho = np.linspace(0, 1, n, dtype=np.float32)
    th = np.linspace(0, 2 * np.pi, n * 2, dtype=np.float32)
    Th, Rho = np.meshgrid(th, rho)
    nrib = int(rng.integers(19, 24))
    ph = rng.uniform(0, 6.3, 3)
    rim = 1 + 0.07 * np.sin(2 * Th + ph[0]) + 0.035 * np.sin(5 * Th + ph[1])
    x, y = R * Rho * rim * np.cos(Th), R * Rho * rim * np.sin(Th)
    ribs = 0.5 + 0.5 * np.cos(nrib * Th)
    z = 0.17 * R * Rho**1.6 + 0.055 * R * Rho**3 * np.sin(5 * Th + ph[1]) + 0.03 * R * Rho**2 * np.sin(13 * Th + ph[2]) - 0.018 * R * Rho * ribs
    t, a = np.radians(tilt), np.radians(azim)
    ca, sa = np.cos(a), np.sin(a)
    u = ca * x + sa * y
    v = -sa * x + ca * y
    u, z = u * np.cos(t) - z * np.sin(t), u * np.sin(t) + z * np.cos(t)
    x, y = ca * u - sa * v, sa * u + ca * v
    tone = float(np.exp(rng.normal(-0.1, 0.42)))  # some leaves are much deeper than others
    patch = (0.5 + 0.5 * np.sin(3 * Th + ph[2] + 2.5 * Rho)) * 0.5 + 0.5 * (0.5 + 0.5 * np.sin(7 * Th + ph[0]))
    base = PT.lerp3((0.05, 0.14, 0.05), (0.1, 0.24, 0.085), patch) * tone
    col = base * (0.82 + 0.3 * (ribs**6))[..., None]
    col = col + (np.exp(-((Rho / 0.08) ** 2)))[..., None] * np.array([0.17, 0.2, 0.04], np.float32)
    tr = PT.lerp3((0.085, 0.22, 0.025), (0.15, 0.3, 0.04), patch) * tone * (0.72 + 0.5 * (ribs**6))[..., None]
    tr = tr * (1 + 0.3 * (Rho**5))[..., None]
    np.savez(path, P=np.stack([x + at[0], y + at[1], z + at[2]], -1).astype(np.float32), col=np.clip(col, 0, 1).astype(np.float32), tr=np.clip(tr, 0, 1).astype(np.float32))
    return path


def sim_for(specs, leaves, a=None, sub=1, frames=FRAMES):
    lv = np.array([[l["x"], l["y"], l["R"]] for l in leaves])
    fl = np.array([[f[1][0], f[1][1]] for f in FAR])
    return WD.Sim(specs, lv, fl, a)


def film_times(sub, frames=FRAMES):
    return (np.arange(frames)[:, None] + (SHUTTER * ((np.arange(sub) + 0.5) / sub - 0.5))[None, :]).ravel() / 25.0


def layout(a):
    """The petals through the camera, shaded by the sun, as a filmstrip and an mp4."""
    specs = flower()
    leaves = field_spec()
    ny, nx = RES["layout"]
    meshes = [PT.Mesh(sp, ny, nx) for sp in specs]
    cam, _ = camera(meshes, specs)
    ts = film_times(1)
    sim = sim_for(specs, leaves, a).run(ts)
    w, h = 960, 540
    d = os.path.join(OUT, RUN)
    os.makedirs(d, exist_ok=True)
    frames, tips = [], []
    for k in range(len(ts)):
        img = np.zeros((h, w, 3), np.uint8)
        img[:] = (40, 72, 34)
        for i, l in enumerate(leaves):  # the leaves as ellipses: just to see them breathe
            cx = l["x"] + sim.leaf["sway"][i, k]
            p = project(cam, np.array([[cx, l["y"], l["z"] + 0.3 * sim.leaf["tx"][i, k]]]))
            sc = DIST / (DIST + l["y"]) * W
            rr = l["R"] / W * w * DIST / (DIST + l["y"])
            tilt = abs(l["tilt"] - 8 + sim.leaf["tx"][i, k]) / 40 + 0.08
            cv2.ellipse(img, (int(p[0][0] * w), int(p[1][0] * h)), (int(rr), int(rr * tilt)), 0, 0, 360, (70 + i % 30, 110 + i % 40, 60), -1, cv2.LINE_AA)
        quads, depth, shade = [], [], []
        tp = []
        for i, m in enumerate(meshes):
            P = sim.head_move(m.pose(**sim.petal_args(i, k, m.s)), k)
            tp.append(P[-1, nx // 2])
            x, y, _ = project(cam, P)
            n = np.cross(P[1:, :-1] - P[:-1, :-1], P[:-1, 1:] - P[:-1, :-1])
            n = n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)
            lit = np.abs(n @ SUN)
            q = np.stack([np.stack([x[:-1, :-1], y[:-1, :-1]], -1), np.stack([x[:-1, 1:], y[:-1, 1:]], -1), np.stack([x[1:, 1:], y[1:, 1:]], -1), np.stack([x[1:, :-1], y[1:, :-1]], -1)], 2)
            quads.append(q.reshape(-1, 4, 2))
            depth.append(P[:-1, :-1, 1].ravel())
            g = m.S[:-1, :-1]
            shade.append(np.stack([0.75 + 0.2 * (1 - g), 0.8 - 0.55 * g, 0.85 - 0.25 * g], -1).reshape(-1, 3) * (0.45 + 0.55 * lit.ravel()[:, None]))
        Q, D, C = np.concatenate(quads), np.concatenate(depth), np.concatenate(shade)
        for j in np.argsort(-D):
            pts = (Q[j] * [w, h] * 16).astype(np.int32)
            cv2.fillConvexPoly(img, pts, tuple(float(c) for c in (C[j][::-1] * 255)), cv2.LINE_AA, 4)
        tips.append(np.array(tp))
        frames.append(img)
    tips = np.array(tips)
    pxcm = 2560 / W
    print("frame head_x neck_deg U | tip move from frame 0, px at 2560: whorl A B C D E (max) | fastest px/frame")
    idx = [0, 5, 11, 18, 24, 30]
    for k in range(0, len(ts), 3):
        mv = np.linalg.norm(tips[k] - tips[0], axis=-1) * pxcm
        print(f"{k:3d} x {sim.head['x'][k]:+.2f} cm n {sim.head['n'][k]:+.2f} U {sim.head['U'][k]:.2f} | " + " ".join(f"{mv[idx[j] : idx[j + 1]].max():5.0f}" for j in range(5)))
    v = np.linalg.norm(np.diff(tips, axis=0), axis=-1) * pxcm
    print(f"fastest tip {v.max():.1f} px/frame at 2560, p50 {np.median(v):.1f}; flap range {sim.pet['flap'].min():.2f}..{sim.pet['flap'].max():.2f}; bend {sim.pet['bend'].min():.1f}..{sim.pet['bend'].max():.1f}; twist {sim.pet['twist'].min():.1f}..{sim.pet['twist'].max():.1f}")
    # the test: how much of the path of each tip goes against its net displacement
    dts = np.diff(tips, axis=0)
    net = tips[-1] - tips[0]
    net = net / (np.linalg.norm(net, axis=-1, keepdims=True) + 1e-9)
    along = (dts * net[None]).sum(-1)
    frac = np.maximum(-along, 0).sum(0) / (np.linalg.norm(dts, axis=-1).sum(0) + 1e-9)
    print("apex y over the take:", " ".join(f"{project(cam, tips[k])[1].min():.3f}" for k in range(0, len(ts), 7)))
    print(f"against the net displacement, share of each tip's path: p50 {np.percentile(frac, 50) * 100:.2f} %, p95 {np.percentile(frac, 95) * 100:.2f} %, max {frac.max() * 100:.2f} %; net move of tips {np.linalg.norm(tips[-1] - tips[0], axis=-1).min() * pxcm:.0f}..{np.linalg.norm(tips[-1] - tips[0], axis=-1).max() * pxcm:.0f} px")
    picks = np.linspace(0, len(frames) - 1, 12).astype(int)
    rows = [np.hstack([cv2.resize(frames[i], (640, 360), interpolation=cv2.INTER_AREA) for i in picks[j : j + 3]]) for j in range(0, 12, 3)]
    cv2.imwrite(os.path.join(d, "layout.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(os.path.join(d, "layout.jpg"))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", "25", "-i", "-", "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-movflags", "+faststart", os.path.join(d, "layout.mp4")], stdin=subprocess.PIPE)
    for f in frames:
        ff.stdin.write(f.tobytes())
    ff.stdin.close()
    ff.wait()


def leaf_pose(V, rest, sim, i, k, at):
    """A leaf: sway of its stalk, tilt about its centre, a wave round the rim."""
    x, y, z = V[..., 0] - at[0], V[..., 1] - at[1], V[..., 2] - at[2]
    tx, ty = np.radians(sim.leaf["tx"][i, k]), np.radians(sim.leaf["ty"][i, k])
    rho2, th = rest
    dz = -tx * x + ty * y + sim.leaf["wave"][i, k] * rho2 * np.sin(2 * th + sim.leaf["ph"][i])
    return np.stack([V[..., 0] + sim.leaf["sway"][i, k] + tx * z, V[..., 1] - ty * z, V[..., 2] + dz], -1).astype(np.float32)


def build(q, sim=None, still_k=None):
    """Writes every mesh and map at the pose of sample still_k (rest if None). Returns the mesh list and how to pose every moving vertex."""
    d = os.path.join(OUT, RUN, "still" if still_k is not None else "take")  # a still and a take can be made side by side
    os.makedirs(d, exist_ok=True)
    specs = flower()
    leaves = field_spec()
    ny, nx = RES[q]
    meshes = [PT.Mesh(sp, ny, nx) for sp in specs]
    cam, tgt = camera(meshes, specs)
    t0 = time.time()
    out, posers = [], []

    def pose_of(i, k):
        return sim.head_move(meshes[i].pose(**sim.petal_args(i, k, meshes[i].s)), k) if k is not None else meshes[i].pose()

    for i, sp in enumerate(specs):
        col, tr, aux, _ = PT.maps(sp, meshes[i].shape, DENS[q])
        ps = {}
        for key, im in (("col", col), ("tr", tr), ("aux", aux)):
            ps[key] = PT.write16(os.path.join(d, f"p{i}.{q}.{key}.png"), im)
        p = os.path.join(d, f"p{i}.{q}.npz")
        np.savez(p, P=pose_of(i, still_k), uvw=meshes[i].uvw)
        out.append({"name": f"p{i}", "npz": p, "shader_py": SHADER, "params": {**MAT, **ps}, "send_params": ["col", "tr", "aux"]})
        posers.append((f"p{i}", lambda k, i=i: pose_of(i, k)))
    print(f"{len(specs)} petals, maps in {time.time() - t0:.0f} s, {sum(m.u.size * m.s.size for m in meshes) / 1e6:.2f} M vertices", flush=True)

    for l in leaves:
        i = l["i"]
        p = os.path.join(d, f"lf{i}.npz")
        leaf(p, (l["x"], l["y"], l["z"]), l["R"], l["tilt"], l["az"], 3900 + i, n=64 if l["y"] < 320 else 32)
        at = np.array([l["x"], l["y"], l["z"]])
        z = dict(np.load(p))
        V = z["P"]
        rho2 = ((V[..., 0] - at[0]) ** 2 + (V[..., 1] - at[1]) ** 2) / l["R"] ** 2
        th = np.arctan2(V[..., 1] - at[1], V[..., 0] - at[0])
        rest = (rho2, th)
        if still_k is not None:
            z["P"] = leaf_pose(V, rest, sim, i, still_k, at)
            np.savez(p, **z)
        out.append({"name": f"lf{i}", "npz": p, "shader_py": SHEET, "params": FAR_MAT})
        if l["stalk"] is not None:
            ps = os.path.join(d, f"st{i}.npz")
            stalk(ps, (l["x"], l["y"], l["z"]), -90.0, lean=l["stalk"])
            zs = dict(np.load(ps))
            Vs = zs["P"]
            T = (Vs[..., 2] + 90.0) / (l["z"] + 90.0)

            def st_pose(k, Vs=Vs, T=T, i=i):
                o = Vs.copy()
                o[..., 0] += sim.leaf["sway"][i, k] * T**2
                return o

            if still_k is not None:
                zs["P"] = st_pose(still_k)
                np.savez(ps, **zs)
            out.append({"name": f"st{i}", "npz": ps, "shader_py": SHEET, "params": {"k": 0.1, "rough": 0.5, "spec": 0.3}})

    # another flower and a bud further into the field, in the blur
    for fi, (tag, at, take) in enumerate(FAR):
        for i, sp in enumerate(specs[:take] if take else specs):
            sp2 = {**sp, "seed": sp["seed"] + 7}
            m = PT.Mesh(sp2, 36, 20)
            col_, tr_ = PT.far_attrs(m, sp2)
            V = m.pose() + np.array(at, np.float32)

            def fp(k, V=V, fi=fi):
                o = V.copy()
                o[..., 0] += sim.far["sway"][fi, k]
                return o

            p = os.path.join(d, f"{tag}{i}.npz")
            np.savez(p, P=fp(still_k) if still_k is not None else V, col=col_, tr=tr_)
            out.append({"name": f"{tag}{i}", "npz": p, "shader_py": SHEET, "params": {"k": 0.46, "rough": 0.42, "spec": 0.32, "sheen": 0.25, "sheen_rough": 0.6}})
    out.append({"name": "pond", "npz": water(os.path.join(d, "pond.npz"), -90.0), "material": {"Base Color": [0.006, 0.02, 0.018], "Roughness": 0.04, "IOR": 1.33, "Specular IOR Level": 0.5}})
    return out, posers, cam, tgt


def scene_of(meshes, cam, tgt, q):
    d = os.path.join(OUT, RUN)
    tg = tgt.tolist()
    lights = [{"name": "sun", "loc": (tgt + SUN * 500.0).tolist(), "target": tg, "size": [60, 60], "watts": 1700000, "rgb": [1.0, 0.93, 0.8], "hide_in_gloss": True}]
    return {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": pond_env(os.path.join(d, "env.npy"), SUN, top=(0.64, 0.7, 0.8), low=(0.95, 0.92, 0.86), tree_el=8.0, gain=0.58, seed=39), "diffuse": True, "transmission": True},
        "bounces": 14,
        "diffuse_bounces": 10,
        "glossy_bounces": 4,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }


def still(q, a):
    ts = np.array([STILL_FRAME / 25.0])
    sim = sim_for(flower(), field_spec(), a).run(ts)
    meshes, _, cam, tgt = build(q, sim, 0)
    scene = scene_of(meshes, cam, tgt, q)
    tag = "cand" if q == "final" else q
    if os.environ.get("S39_NODENOISE"):
        scene["denoise"] = False
    shoot(RUN, scene, q, tag=tag, develop=LOOK)
    if q == "final":
        import shutil

        for ext in ("jpg", "png", "linear.npy", "develop.json"):
            shutil.copyfile(os.path.join(OUT, RUN, f"cand.{ext}"), os.path.join(OUT, NAME, f"cand.{ext}"))


def take(mode, a, frames=None, res=None, spp=None):
    """low: all frames at 960x540, one exposure each, for judging the motion. final: all frames, full size, SUB exposures each."""
    sub = SUB if mode == "final" else 1
    ts = film_times(sub)
    sim = sim_for(flower(), field_spec(), a).run(ts)
    q = "final" if mode == "final" else os.environ.get("S39_Q", "preview")
    meshes, posers, cam, tgt = build(q, sim, None)
    scene = scene_of(meshes, cam, tgt, q)
    names = [n for n, _ in posers]
    total = sum(f(0).size // 3 for _, f in posers)
    sp = os.path.join(OUT, RUN, f"wind.{q}.npy")
    st = np.lib.format.open_memmap(sp, mode="w+", dtype=np.float32, shape=(len(ts), total, 3))
    t0 = time.time()
    for k in range(len(ts)):
        st[k] = np.concatenate([f(k).reshape(-1, 3) for _, f in posers])
    st.flush()
    print(f"{sp}: {st.shape}, {os.path.getsize(sp) / 1e9:.2f} GB, {time.time() - t0:.0f} s", flush=True)
    scene["deform"] = {"npy": sp, "vertex": names}
    scene["denoise"] = True  # undenoised at these samples the blur of the field is blotchy (seen on a mid)
    mv = {"frames": len(ts), "shutter": 0, "spp": spp or (int(os.environ.get("S39_SPP", 160)) if mode == "final" else 64), "res": list(res or ((2560, 1440) if mode == "final" else (960, 540)))}
    if mode == "low":
        mv["spp"] = int(os.environ.get("S39_SPP", 48))
    # studio_bpy skips a frame whose file exists: what a killed take left here would be taken for this take (it was: frames 0-17 of a final came from an older motion)
    here = os.path.join(OUT, RUN)
    for f in os.listdir(here):
        if f.startswith("take.linear_"):
            os.remove(os.path.join(here, f))
    kit.looks = lambda: {RUN: {"move": mv}}
    os.environ["GEWU_MOVE"] = "final" if mode == "low" else mode
    out = shoot(RUN, scene, q, develop=LOOK)
    os.environ.pop("GEWU_MOVE")
    if mode == "final":
        average(out, sub)
        os.remove(sp)
    return out


def average(d, sub):
    fs = sorted(f for f in os.listdir(d) if f.startswith("take.linear_") and f.endswith(".npy"))
    if len(fs) != FRAMES * sub:
        raise SystemExit(f"{d}: {len(fs)} sub-exposures, expected {FRAMES * sub}")
    o = os.path.join(d, ".avg")
    os.makedirs(o, exist_ok=True)
    for i in range(FRAMES):
        v = sum(np.load(os.path.join(d, f)).astype(np.float32) for f in fs[i * sub : (i + 1) * sub]) / sub
        np.save(os.path.join(o, f"take.linear_{i:03d}.npy"), v.astype(np.float16))
    for f in fs:
        os.remove(os.path.join(d, f))
    for f in sorted(os.listdir(o)):
        os.replace(os.path.join(o, f), os.path.join(d, f))
    os.rmdir(o)


def deliver(src, dst=None, fps=25):
    """Develop a take into f###.png, f###.jpg and take.mp4, the form film.find and the dev page read."""
    from darkroom import develop as dev, save_png

    dst = dst or os.path.join(OUT, NAME + "_take_cand")
    os.makedirs(dst, exist_ok=True)
    fs = sorted(f for f in os.listdir(src) if f.startswith("take.linear_") and f.endswith(".npy"))
    for i, f in enumerate(fs):
        img = dev(np.load(os.path.join(src, f)).astype(np.float32), **{**LOOK, "seed": i + 1})
        save_png(os.path.join(dst, f"f{i:03d}.png"), img)
        cv2.imwrite(os.path.join(dst, f"f{i:03d}.jpg"), (img * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
    import json

    json.dump(LOOK, open(os.path.join(dst, "develop.json"), "w"))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-r", str(fps), "-i", os.path.join(dst, "f%03d.jpg"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-movflags", "+faststart", os.path.join(dst, "take.mp4")])
    print(dst, len(fs))


def main():
    args = [x for x in sys.argv[1:] if "=" not in x]
    a = {k: float(v) for k, v in (x.split("=") for x in sys.argv[1:] if "=" in x)}
    what = args[0] if args else "layout"
    if what == "layout":
        layout(a)
    elif what == "still":
        still(args[1] if len(args) > 1 else "preview", a)
    elif what == "take":
        out = take(args[1] if len(args) > 1 else "low", a)
        if os.environ.get("S39_DELIVER"):
            deliver(out, os.path.join(OUT, os.environ["S39_DELIVER"]))
    elif what == "deliver":
        deliver(args[1], args[2] if len(args) > 2 else None)
    else:
        raise SystemExit("layout | still Q | take MODE | deliver DIR")


if __name__ == "__main__":
    main()
