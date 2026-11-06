"""Shot 15: a whole folding fan, sprinkled with gold, standing open with the light behind it. Its top edge is the arc.

    python3 -I v2/stills/s15_zheshan.py [sketch|preview|mid|final]
    python3 -I v2/stills/s15_zheshan.py open [layout|look|final] [FRAMES]    the fan opens, solved in s15_open.py; goes to out/v2/s15_zheshan_open_move_final

The old shot was a crop of flat stripes with flecks printed on them (git history has it). Set against ref/fan:
- true pleats: each face its own surface, each crease its own slightly wandering line, the opening angles a little uneven; the bamboo sticks are solids behind the paper and show through it as shadow, and are seen bare below it;
- gold flakes are solids laid over the folds: every vertex sits on the paper with its own lift, and each small facet has its own tilt, so flakes catch the light one by one, and block it from behind;
- light from behind and to one side passes through the paper, one family of pleat faces turned towards it, the other away. A shuttered window between the lamp and the fan throws soft bands that walk across the pleats.
Sizes are estimates (a fan about 34 cm long). The room is the photographer's grey-black. Paper colour and flake density are chosen, after ref/fan. The room in reflections is kit.room_env (painted).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, frame_camera, mix, shoot, sstep
from s21_lib import smooth1d, strokes, up
from translib import SOFT, merge, real_background, save, tubes
from vessel import project, view_dir

NAME = "s15_zheshan"
R1, R0 = 34.0, 12.5  # paper from R0 to R1, cm; estimates
OPEN = 152.0  # degrees
NFACE = 30
W, AZ, EL, DIST = 62.0, -68.0, -6.0, 118.0  # the camera stands off to the side and a little low: never square-on
APEX = 0.27
APERTURE = 26.0
KEY = np.array([-0.48, 0.78, 0.38])
KEY = KEY / np.linalg.norm(KEY)
SIG = color([0.025, 0.27, 0.85])  # paper: warm cream when light comes through


def _at(F, fx, fy):
    """Bilinear look-up, any shape of fx, fy."""
    x0 = np.clip(np.floor(fx).astype(np.int32), 0, F.shape[1] - 2)
    y0 = np.clip(np.floor(fy).astype(np.int32), 0, F.shape[0] - 2)
    a, b = fx - x0, fy - y0
    return F[y0, x0] * (1 - a) * (1 - b) + F[y0, x0 + 1] * a * (1 - b) + F[y0 + 1, x0] * (1 - a) * b + F[y0 + 1, x0 + 1] * a * b


class Fan:
    """The surface of the paper: S(r, phi index). Lives in the plane x (across), z (up), y into the picture; the pivot at the origin."""

    def __init__(self, seed=15):
        rng = np.random.default_rng(seed)
        widths = 1 + rng.normal(0, 0.035, NFACE)
        self.c = np.concatenate([[0], np.cumsum(widths)])
        self.c = self.c / self.c[-1] * np.radians(OPEN) - np.radians(OPEN) / 2  # crease angles
        self.amp = rng.uniform(0.82, 1.15, NFACE + 1)  # each crease its own height
        self.w_l = np.stack([smooth1d(40, 6, rng) for _ in range(NFACE + 1)])  # wander along the length
        self.bow = rng.normal(0, 1, NFACE)
        self.tw = rng.normal(0, 1, NFACE)
        self.b_t = np.stack([smooth1d(40, 8, rng) for _ in range(NFACE)])
        self.wav = fbm((256, 1024), 1.0, 12.0, 120.0, 2.6, seed + 3)
        self.wav2 = fbm((256, 1024), 1.0, 8.0, 40.0, 2.0, seed + 4)

    def crease(self, i, r):
        s = np.clip((r - R0) / (R1 - R0), 0, 1) * 39
        j = np.floor(s).astype(np.int32)
        j1 = np.minimum(j + 1, 39)
        t = s - j
        wl = self.w_l[i, j] * (1 - t) + self.w_l[i, j1] * t
        return self.c[i] + wl * 0.0011  # about half a millimetre to a millimetre

    def surf(self, r, f):
        """r in cm, f in face units (0..NFACE)."""
        i = np.clip(np.floor(f).astype(np.int32), 0, NFACE - 1)
        t = f - i
        a0, a1 = self.crease(i, r), self.crease(i + 1, r)
        phi = a0 + (a1 - a0) * t
        hw = np.maximum(r * (a1 - a0), 1e-3)
        A = 0.62 * hw  # fold height: the faces meet at a little over 60 degrees
        sgn = np.where(i % 2 == 0, 1.0, -1.0)
        y = sgn * (A * self.amp[i] * (1 - t) * 0.5 * 2 - A * self.amp[i + 1] * t) * 0.5
        # the face is not flat: it bows between creases, by its own amount
        s = np.clip((r - R0) / (R1 - R0), 0, 1)
        sj = s * 38.999
        j = sj.astype(np.int32)
        bt = self.b_t[i, j] * (1 - (sj - j)) + self.b_t[i, j + 1] * (sj - j)
        bow = 0.03 * hw * self.bow[i] + 0.04 * hw * bt
        y = y + sgn * bow * 4 * t * (1 - t) * 1.6
        # slow waves of the sheet
        fx, fy = (f / NFACE * 1023).astype(np.float32), (s * 255).astype(np.float32)
        y = y + 0.04 * _at(self.wav, fx, fy) * s + 0.016 * _at(self.wav2, fx, fy)
        x, z = r * np.sin(phi), r * np.cos(phi)
        return np.stack([x, y, z], -1), hw, t, i


def rim(fan, f):
    """The top of the paper: cut in a clean curve, slightly uneven, a thin strip of binding along it."""
    rng = np.random.default_rng(151)
    n = 2048
    e = 0.05 * smooth1d(n, 140, rng) + 0.008 * smooth1d(n, 10, rng)
    return R1 + np.interp(f, np.linspace(0, NFACE, n), e)


def paper(fan, dens, seed=15):
    n_f = max(int(150 * dens), 32)
    nx = NFACE * n_f + 1
    ny = max(int((R1 - R0) * 32 * dens), 120)
    f = np.linspace(0, NFACE, nx, dtype=np.float32)
    f[-1] = NFACE - 1e-4
    edge = rim(fan, f)
    v = np.linspace(0, 1, ny, dtype=np.float32)
    Rr = R0 + (edge[None, :] - R0) * v[:, None]
    Fg = np.repeat(f[None, :], ny, 0)
    P, hw, t, I = fan.surf(Rr, Fg)

    # the paper in the flat
    S = np.clip(28 * dens, 8, 28)
    nxp = int(2 * 36 * S)
    x_p = P[..., 0]
    z_p = P[..., 2]
    clouds = fbm((nxp, nxp), S, 0.25, 3.0, 2.1, seed + 11)
    patches = fbm((nxp, nxp), S, 2.5, 22.0, 2.8, seed + 12)
    rng = np.random.default_rng(seed + 13)
    lines, vals = [], []
    for _ in range(int(40000 * dens) + 1500):
        p0 = rng.uniform(0, nxp, 2)
        L = float(rng.lognormal(0.1, 0.5))
        a = rng.uniform(0, np.pi * 2)
        da = np.cumsum(rng.normal(0, 0.3, 5))
        pts = [p0]
        for j in range(5):
            pts.append(pts[-1] + L / 5 * S * np.array([np.cos(a + da[j]), np.sin(a + da[j])]))
        lines.append(np.array(pts))
        vals.append(rng.uniform(0.3, 1.0))
    fib = blur(strokes((nxp, nxp), lines, 1, np.array(vals)), 0.55)

    def sample(F):
        return cv2.remap(F.astype(np.float32), ((x_p + 36) * S).astype(np.float32), ((z_p + 0) * S).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    cl, pa, fb = sample(clouds), sample(patches), sample(fib)
    # worn at the creases: the fibre broken, pale where it opens most, towards the rim
    d_cr = np.minimum(t, 1 - t) * 2 * hw
    wr_field = sample(fbm((nxp // 4, nxp // 4), S / 4, 0.5, 5.0, 2.0, seed + 14)) if False else 0.0
    wear = np.exp(-((d_cr / 0.05) ** 2)) * sstep(0.3, 1.0, Rr / R1)
    crush = np.exp(-((d_cr / 0.18) ** 2))
    bind = sstep(0.05, -0.05, edge[None, :] - Rr - 0.22)

    # a stick lies between the two leaves of every other fold. Inside the paper the light is already scattered, so it shows as a soft thickening, not a shadow: a stand-in for light scattering between the leaves, here written as thickness
    d_st = np.where(I % 2 == 0, t, 1 - t) * 2 * hw
    w_st = 0.27 * (1 - 0.55 * np.clip((Rr - R0) / (R1 - R0), 0, 1))
    st = sstep(w_st + 0.16, w_st - 0.1, d_st) * sstep(31.2, 30.6, Rr)
    p = 1.0 + 0.1 * cl + 0.2 * (fb - fb.mean()) + 0.07 * pa + 0.25 * crush - 0.12 * wear
    T = np.exp(-p[..., None] * SIG)
    # two leaves of paper, pasted; a slightly darker binding strip
    tr = T * 0.86 * (1 - 0.55 * bind)[..., None] * np.exp(-0.5 * st)[..., None] * (color([1.0, 0.9, 0.72]) ** st[..., None])
    col = np.power(T, 0.7) * color([0.86, 0.82, 0.72])
    col = mix(col, color([0.22, 0.11, 0.05]), 0.8 * bind)
    tr = mix(tr, color([0.2, 0.09, 0.03]), 0.65 * bind)
    return P.astype(np.float32), col.astype(np.float32), np.clip(tr, 0, 1).astype(np.float32)


def sticks(fan, seed=15, pose=None):
    """The bamboo sticks: one behind every other crease, thin in the paper, wider below it; two thick guards outside; a pivot.
    pose: (PA, PB, tilt0, stack) of s15_open: the same sticks, same widths and colours, at that opening; their far parts bend with the paper, and near the pin they stack along it."""
    rng = np.random.default_rng(seed + 40)
    ns = 180
    out = []
    for i in range(0, NFACE + 1, 2):
        guard = i in (0, NFACE)
        r = np.linspace(0.5, 33.0 if guard else R0 + 0.8, ns, dtype=np.float32)
        a = fan.c[i]
        s = np.clip((r - R0) / (R1 - R0), 0, 1)
        x, z = r * np.sin(a), r * np.cos(a)
        hw_p = (0.62 * r * (fan.c[1] - fan.c[0]))
        y = (0.5 * hw_p * 0 - 0.04 + (0 if i % 2 else 0)) * np.ones_like(r)
        crease_y = fan.surf(np.maximum(r, R0), np.full(ns, min(i, NFACE - 1e-3), np.float32))[0][:, 1]
        y = crease_y + 0.1 + 0.05 * sstep(R0, R0 - 1, r)
        y = y + (1 - sstep(0.5, R0, r)) * 0.2
        if pose is not None:
            PA, PB, tilt0, stack = pose
            bl = np.clip((r - R0) / (R1 - R0), 0, 1) ** 2
            a = PA["C"][i] * (1 - bl) + PB["C"][i] * bl
            x, z = r * np.sin(a), r * np.cos(a)
            H = PA["H"][i] * (1 - bl) + PB["H"][i] * bl
            # the crease's own height, as on the paper, but held constant below the paper as at rest
            y = H * np.maximum(r, R0) + 0.1 + 0.05 * sstep(R0, R0 - 1, r) + (1 - sstep(0.5, R0, r)) * 0.2 + fan_wave_at(fan, i, r)
            y = y + stack * (i / NFACE - 0.5) * PA["G"][i] * (1 - 0.55 * np.clip((r - R0) / (R1 - R0), 0, 1))
        w = (0.42 if guard else 0.27) * (1 - 0.55 * s) * rng.uniform(0.9, 1.1) * (1 + 0.5 * sstep(4, 0, r))
        ht = (0.17 if guard else 0.055) * np.ones_like(r)
        path = np.stack([x, y, z], -1)
        side = np.stack([np.cos(a) * np.ones_like(r), np.zeros_like(r), -np.sin(a) * np.ones_like(r)], -1).astype(np.float32)
        cc = color([0.44, 0.25, 0.1]) * rng.uniform(0.8, 1.15) * (1 + 0.08 * smooth1d(ns, 12, rng))[:, None]
        out.append(tubes(path[None], w[None], {"col": cc[None], "tr": np.clip(2.0 * cc[None], 0, 1)}, nside=10, side=side[None], ht=ht[None], power=3.0))
    return merge(*out)


def fan_wave_at(fan, i, r):
    """The slow waves of the sheet at crease i, radius r: the sticks ride on them too."""
    s = np.clip((r - R0) / (R1 - R0), 0, 1)
    fx, fy = np.full_like(s, min(i, NFACE - 1e-3) / NFACE * 1023, dtype=np.float32), (s * 255).astype(np.float32)
    return 0.04 * _at(fan.wav, fx, fy) * s + 0.016 * _at(fan.wav2, fx, fy)


def flake(rng, fan, r0, f0, size, faces, curl, rec=None):
    """One flake: a ragged star of triangles lying on the paper, following the folds, each ring lifting a little. rec: a list to fill with its paper coordinates (r, f, lift), for the opening."""
    nth = faces
    rings = 3 if size > 0.2 else 2
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False) + rng.normal(0, 0.1, nth)
    rag = np.exp(rng.normal(0, 0.28, nth))
    ax = rng.uniform(0.6, 1.2)
    ca, sa = np.cos(rng.uniform(0, 3.14)), np.sin(rng.uniform(0, 3.14))
    V = [(0.0, 0.0, 0.0)]
    lift_dir = rng.normal(0, 1, 2)
    lift_dir = lift_dir / np.linalg.norm(lift_dir)
    for k in range(1, rings + 1):
        q = k / rings
        rho = size * q * rag * (0.85 + 0.3 * rng.random(nth))
        dx = rho * np.cos(th) * ax
        dy = rho * np.sin(th) / ax
        dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
        lift = curl * size * np.maximum(dx * lift_dir[0] + dy * lift_dir[1], 0) / max(size, 1e-3) * q + rng.normal(0, 0.012 * size, nth)
        for a, b, c in zip(dx, dy, lift):
            V.append((a, b, c))
    V = np.array(V)
    # a flake stays narrower than a pleat, so it bends over one fold at most and never crumples across several
    fit = 0.8 * r0 * (fan.c[1] - fan.c[0]) / max(float(np.abs(V[:, 0]).max()), 1e-6)
    if fit < 1:
        V[:, :2] *= fit
    # dx across the face, dy along the radius; to face coordinates
    pw = r0 * (fan.c[1] - fan.c[0])
    rr = r0 + V[:, 1]
    ff = np.clip(f0 + V[:, 0] / pw, 0, NFACE - 1e-3)
    P = fan.surf(rr.astype(np.float32), ff.astype(np.float32))[0]
    P = P + np.array([0, -1.0, 0]) * (0.01 + np.abs(V[:, 2]))[:, None]  # towards the camera side
    if rec is not None:
        rec.append((rr.astype(np.float32), ff.astype(np.float32), (0.01 + np.abs(V[:, 2])).astype(np.float32)))
    F = []
    for j in range(nth):
        F.append((0, 1 + j, 1 + (j + 1) % nth))
    for k in range(rings - 1):
        b0, b1 = 1 + k * nth, 1 + (k + 1) * nth
        for j in range(nth):
            a, b = j, (j + 1) % nth
            F.append((b0 + a, b1 + a, b1 + b))
            F.append((b0 + a, b1 + b, b0 + b))
    return P.astype(np.float32), np.array(F, np.int32)


def gold(fan, dens, seed=15, rec=None):
    """Sprinkled by hand: big flakes few, broken ones in drifts, a dust that thickens in places."""
    rng = np.random.default_rng(seed + 60)
    Vs, Fs, cs, rs = [], [], [], []
    base = 0
    # drifts: where the hand was
    drifts = [(rng.uniform(0, NFACE), rng.uniform(R0 + 2, R1 - 1), rng.uniform(2, 6), rng.uniform(2, 7)) for _ in range(14)]
    n_big, n_mid, n_small = 28, 1100, int(7000 * max(dens, 0.4))
    for kind, n in (("big", n_big), ("mid", n_mid), ("small", n_small)):
        for _ in range(n):
            if rng.random() < 0.55:
                d = drifts[rng.integers(0, len(drifts))]
                f0 = float(np.clip(rng.normal(d[0], d[2]), 0.1, NFACE - 0.1))
                r0 = float(np.clip(rng.normal(d[1], d[3]), R0 + 0.5, R1 - 0.6))
            else:
                f0 = float(rng.uniform(0.1, NFACE - 0.1))
                r0 = float(rng.uniform(R0 + 0.5, R1 - 0.6))
            if kind == "big":
                size, faces, curl = float(rng.lognormal(np.log(0.42), 0.3)), 11, float(rng.uniform(0.02, 0.1))
            elif kind == "mid":
                size, faces, curl = float(rng.lognormal(np.log(0.12), 0.42)), 8, float(rng.uniform(0.05, 0.3))
            else:
                size, faces, curl = float(rng.lognormal(np.log(0.035), 0.4)), 5, float(rng.uniform(0.1, 0.5))
            P, F = flake(rng, fan, r0, f0, size, faces, curl, rec)
            Vs.append(P)
            Fs.append(F + base)
            base += len(P)
            c = color([1.0, 0.70, 0.30]) * rng.uniform(0.86, 1.04) * color([1, rng.uniform(0.94, 1.03), rng.uniform(0.9, 1.05)])
            cs.append(np.broadcast_to(c, (len(P), 3)))
            rs.append(np.full(len(P), rng.uniform(0.2, 0.5), np.float32))
    return {"V": np.concatenate(Vs), "F": np.concatenate(Fs), "col": np.concatenate(cs).astype(np.float32), "rough": np.concatenate(rs)}


def shutter(path, tgt, d=120.0):
    """The shutters of a window between the lamp and the fan: dark boards, seen by nothing but the lamp. They throw the soft bands."""
    e1 = np.cross(KEY, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(e1, KEY)
    c = np.array(tgt) + KEY * d
    rng = np.random.default_rng(159)
    V, F = [], []
    b = 0
    for x, wd in ((-20.0, 15.0), (19.0, 6.0), (-52.0, 8.0)):  # placed by eye for this frame
        for a, h in ((x, -120), (x + wd, -120), (x + wd, 120), (x, 120)):
            V.append(c + e1 * a + e2 * h)
        F += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        b += 4
    np.savez(path, V=np.array(V, np.float32), F=np.array(F, np.int32), col=np.full((len(V), 3), 0.02, np.float32))
    return path



OPEN_FRAMES = 24
OPEN_SHUTTER = 0.5  # of a frame, 180 degrees
OPEN_PX = 3.0  # sub-exposures: the rim moves no more than this many pixels of 1920 between two of them, so that a fast frame is a streak, not a row of ghosts
OPEN_SUB_MAX = 40


def open_rig(frames=OPEN_FRAMES, a=None):
    """The motion, independent of mesh density."""
    import s15_open as OP

    fan = Fan()
    pl = OP.Pleats(fan.c, fan.amp)
    d0 = np.diff(fan.c)
    tilt0 = pl(fan.c)["tilt"]
    return fan, pl, tilt0, dict(OP.ARG, **(a or {}))


def open_pose(fan, pl, th, tp, om=None):
    """Two poses, the root's and the tip's."""
    import s15_open as OP

    PA, PB = pl(OP.creases(fan.c, th)), pl(OP.creases(fan.c, tp))
    PA["G"] = OP.closed(PA, None)
    if om is not None:
        k = np.random.default_rng(155).uniform(0.6, 1.4, NFACE)
        PA["air"] = OP.air_load(PB, OP.creases(fan.c, om), k, OP.ARG)
    return PA, PB


def open_camera(fan):
    """The still's camera exactly: found from the still's rim."""
    view = view_dir(AZ, EL)
    H_f = W * 9 / 16
    f = np.linspace(0, NFACE, 4501, dtype=np.float32)
    f[-1] = NFACE - 1e-4
    rim_pts = fan.surf(rim(fan, f), f)[0]
    tgt = np.array([0.0, 0.0, 20.0])
    for _ in range(5):
        cam = frame_camera(tgt, view, W, DIST)
        _, y, _ = project(cam, rim_pts)
        tgt[2] -= (float(y.min()) - APEX) * H_f
    return tgt, view


def open_layout(n=OPEN_FRAMES, a=None):
    """No render, seconds: the faces through the still's camera, flat-shaded by the key, every frame. For judging the motion."""
    import subprocess

    import s15_open as OP

    fan, pl, tilt0, A = open_rig(n, a)
    d = os.path.join(OUT, NAME + "_open")
    os.makedirs(d, exist_ok=True)
    tgt, view = open_camera(fan)
    cam = frame_camera(tgt, view, W, DIST)
    ts = np.arange(n) / 25.0
    th, tp, om = OP.solve(fan.c, ts, A)
    rx, rz, dx, dz = OP.rigid(ts, A)
    rr = np.linspace(R0, R1, 9)
    w, h = 960, 540
    out = []
    print("frame: lead, rear (deg); span; slowest and fastest stick, deg/frame; rim speed px/shutter at 1920; apex y; chord err % max; depth at rim cm")
    for k in range(n):
        PA, PB = open_pose(fan, pl, th[k], tp[k], om[k])
        fg = np.repeat(np.arange(0, NFACE + 1, dtype=np.float32)[None], len(rr), 0) * (1 - 1e-5)
        Rg = np.repeat(rr[:, None], NFACE + 1, 1).astype(np.float32)
        S = OP.Static(fan, Rg, fg, R0, R1, NFACE, _at)
        P = OP.pose_points(S, PA, PB, tilt0, A["stack"])
        P = OP.apply_rigid(P, rx[k], rz[k], dx[k], dz[k])
        x, y, dep = project(cam, P.reshape(-1, 3))
        x, y, dep = x.reshape(P.shape[:2]), y.reshape(P.shape[:2]), dep.reshape(P.shape[:2])
        img = np.full((h, w, 3), 22, np.uint8)
        polys = []
        for i in range(NFACE):
            for q in range(len(rr) - 1):
                V = P[q, i], P[q, i + 1], P[q + 1, i + 1], P[q + 1, i]
                nn = np.cross(V[1] - V[0], V[3] - V[0])
                nn = nn / (np.linalg.norm(nn) + 1e-9)
                light = 0.25 + 0.75 * abs(float(nn @ KEY))
                polys.append((float(dep[q, i : i + 2].mean()), light, np.array([[x[q, i], y[q, i]], [x[q, i + 1], y[q, i + 1]], [x[q + 1, i + 1], y[q + 1, i + 1]], [x[q + 1, i], y[q + 1, i]]])))
        polys.sort(key=lambda p: -p[0])
        for _, lit, pts in polys:
            cv2.fillConvexPoly(img, (pts * [w, h] * 8).astype(np.int32), tuple(int(c * lit) for c in (170, 215, 235)), cv2.LINE_AA, 3)
        for j, a_ in enumerate(th[k]):
            s_ = np.linspace(4, R0 if 0 < j < 15 else 33, 12)
            pts = np.stack([s_ * np.sin(a_), 0 * s_, s_ * np.cos(a_)], -1)
            pts = OP.apply_rigid(pts, rx[k], rz[k], dx[k], dz[k])
            u, v, _ = project(cam, pts)
            cv2.polylines(img, [(np.stack([u, v], -1) * [w, h]).astype(np.int32)], False, (40, 90, 170), 1, cv2.LINE_AA)
        cy = int(min(APEX - 0.045, 0.45) * h)
        cv2.line(img, (w // 2 - 40, cy), (w // 2 + 40, cy), (200, 200, 200), 1)
        cv2.putText(img, str(k), (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1, cv2.LINE_AA)
        out.append(img)
        vel = np.degrees(np.abs(th[min(k + 1, n - 1)] - th[max(k - 1, 0)])) / (2 if 0 < k < n - 1 else 1)
        err = OP.stretch(PA, 1.0, fan.c, pl.a0)
        rs = np.radians(vel.max()) * R1 * OPEN_SHUTTER * 1920 / W
        print(f"{k:2d} {np.degrees(th[k, -1]):+6.1f} {np.degrees(th[k, 0]):+6.1f} span {np.degrees(th[k, -1] - th[k, 0]):5.1f}  v {vel.min():5.1f} {vel.max():5.1f}  rim {rs:5.0f} px  apex {y[-1].min():.3f}  err {100 * np.abs(err).max():.3f}%  depth {np.abs(np.diff(PA['H'])).max() * R1:.2f} cm", flush=True)
    np.save(os.path.join(d, "theta.npy"), th)
    cols = 6
    tile = [cv2.resize(f, (320, 180), interpolation=cv2.INTER_AREA) for f in out]
    while len(tile) % cols:
        tile.append(tile[0] * 0)
    cv2.imwrite(os.path.join(d, "layout.jpg"), np.vstack([np.hstack(tile[i : i + cols]) for i in range(0, len(tile), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    # the sticks over time
    T = np.arange(0, n / 25.0, 1 / 100.0)
    tht = OP.solve(fan.c, T, A)[0]
    pl_ = np.full((420, 960, 3), 255, np.uint8)
    for j in range(tht.shape[1]):
        yy = 210 - np.degrees(tht[:, j]) * 2.6
        xx = T / T[-1] * 940 + 10
        cv2.polylines(pl_, [np.stack([xx, yy], -1).astype(np.int32)], False, (0, 0, 200) if j in (0, tht.shape[1] - 1) else (120, 120, 120), 1, cv2.LINE_AA)
    for k in range(n):
        cv2.line(pl_, (int(k / 25.0 / T[-1] * 940 + 10), 0), (int(k / 25.0 / T[-1] * 940 + 10), 6), (0, 0, 0), 1)
    cv2.imwrite(os.path.join(d, "sticks.png"), pl_)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", "25", "-i", "-", "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-movflags", "+faststart", os.path.join(d, "layout.mp4")], stdin=subprocess.PIPE)
    for f in out:
        ff.stdin.write(f.tobytes())
    ff.stdin.close()
    ff.wait()
    print(d, flush=True)


def open_subs(tp, ts_a, ts_b, rig):
    """Sub-exposures of each frame, from how far the rim moves while the shutter is open."""
    disp = np.abs(ts_b - ts_a).max(axis=1) * R1 * 1920 / W
    return np.clip(np.ceil(disp / OPEN_PX).astype(int), 1, OPEN_SUB_MAX)


def open_stack(path, fan, dens, frames, total_spp, recg, Nv_sticks):
    """Every vertex of paper, sticks and gold at every sub-exposure, (times, verts, 3) float32. Also the sub-exposure counts and the samples of each."""
    import s15_open as OP

    pl = OP.Pleats(fan.c, fan.amp)
    tilt0 = pl(fan.c)["tilt"]
    A = dict(OP.ARG)
    only = os.environ.get("S15_ONLY")  # "9,20": just these frames, to look at the blur and the noise before committing to all of them
    ks = np.array([int(x) for x in only.split(",")]) if only else np.arange(frames)
    ka = (ks - OPEN_SHUTTER / 2) / 25.0
    kb = (ks + OPEN_SHUTTER / 2) / 25.0
    ta = OP.solve(fan.c, ka, A)[1]
    tb = OP.solve(fan.c, kb, A)[1]
    subs = open_subs(None, ta, tb, None) if total_spp > 200 else np.ones(len(ks), int)  # a look at the motion has no sub-exposures
    ts = np.concatenate([(k + OPEN_SHUTTER * ((np.arange(n) + 0.5) / n - 0.5)) / 25.0 for k, n in zip(ks, subs)])
    spp = np.concatenate([np.full(n, max(int(np.ceil(total_spp / n)), 16)) for n in subs])
    th, tp, om = OP.solve(fan.c, ts, A)
    rx, rz, dx, dz = OP.rigid(ts, A)
    # the same grid as paper()
    n_f = max(int(150 * dens), 32)
    nx, ny = NFACE * n_f + 1, max(int((R1 - R0) * 32 * dens), 120)
    f = np.linspace(0, NFACE, nx, dtype=np.float32)
    f[-1] = NFACE - 1e-4
    edge = rim(fan, f)
    v = np.linspace(0, 1, ny, dtype=np.float32)
    Rr = R0 + (edge[None, :] - R0) * v[:, None]
    Fg = np.repeat(f[None, :], ny, 0)
    Sp = OP.Static(fan, Rr.ravel(), Fg.ravel(), R0, R1, NFACE, _at)
    rr = np.concatenate([g[0] for g in recg])
    ff = np.concatenate([g[1] for g in recg])
    lift = np.concatenate([g[2] for g in recg])
    Sg = OP.Static(fan, rr, ff, R0, R1, NFACE, _at, lift)
    Nv = nx * ny + Nv_sticks + len(rr)
    st = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=(len(ts), Nv, 3))
    for i in range(len(ts)):
        PA, PB = open_pose(fan, pl, th[i], tp[i], om[i])
        P = OP.pose_points(Sp, PA, PB, tilt0, A["stack"]).astype(np.float32)
        St = sticks(fan, pose=(PA, PB, tilt0, A["stack"]))["V"]
        G = OP.pose_points(Sg, PA, PB, tilt0, A["stack"]).astype(np.float32)
        st[i] = OP.apply_rigid(np.concatenate([P, St, G]), rx[i], rz[i], dx[i], dz[i])
        if i % 20 == 0:
            print(f"stack {i}/{len(ts)}", flush=True)
    st.flush()
    print(f"{path}: {st.shape}, {os.path.getsize(path) / 1e9:.2f} GB; sub-exposures per frame {subs.tolist()}", flush=True)
    return subs, spp.tolist()


def open_average(d, subs):
    """Average each frame's sub-exposures in place; a half-done run shows as an error, not as a short take."""
    fs = sorted(f for f in os.listdir(d) if f.startswith("take.linear_") and f.endswith(".npy"))
    if len(fs) != int(subs.sum()):
        raise SystemExit(f"{d}: {len(fs)} sub-exposures, expected {subs.sum()}")
    out = os.path.join(d, ".avg")
    os.makedirs(out, exist_ok=True)
    a = 0
    for i, n in enumerate(subs):
        im = sum(np.load(os.path.join(d, f)).astype(np.float32) for f in fs[a : a + n]) / n
        np.save(os.path.join(out, f"take.linear_{i:03d}.npy"), im.astype(np.float16))
        a += n
    for f in fs:
        os.remove(os.path.join(d, f))
    for f in sorted(os.listdir(out)):
        os.replace(os.path.join(out, f), os.path.join(d, f))
    os.rmdir(out)


def main():
    real_background()
    opening = None
    if len(sys.argv) > 2 and sys.argv[1] == "open":
        if sys.argv[2] == "layout":
            open_layout(int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else OPEN_FRAMES, {k: float(v) for k, v in (x.split("=") for x in sys.argv[3:] if "=" in x)})
            return
        opening = sys.argv[2]  # look | final
        if opening not in ("look", "final"):
            raise SystemExit("open: layout | look | final")
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if opening:
        q = "preview" if opening == "look" else "final"
    dens = {"sketch": 0.3, "preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    fan = Fan()
    P, col, tr = paper(fan, dens)
    pp = os.path.join(d, f"paper.{q}.npz")
    np.savez(pp, P=P, col=col, tr=tr)
    ps = save(os.path.join(d, "sticks.npz"), sticks(fan))
    pg = os.path.join(d, f"gold.{q}.npz")
    recg = [] if opening else None
    gd = gold(fan, dens, rec=recg)
    np.savez(pg, **gd)

    view = view_dir(AZ, EL)
    H_f = W * 9 / 16
    tgt = np.array([0.0, 0.0, 20.0])
    rim_pts = P[-1]
    for _ in range(5):
        cam = frame_camera(tgt, view, W, DIST)
        _, y, _ = project(cam, rim_pts)
        tgt[2] -= (float(y.min()) - APEX) * H_f
    i_f = int(P.shape[0] * 0.8)
    focus = P[i_f, int(P.shape[1] * 0.38)]
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, rim_pts)
    print(f"apex y {y.min():.3f} at x {x[np.argmin(y)]:.2f}, x span {x.min():.2f}..{x.max():.2f}; focus {project(cam, focus[None])[:2]}", flush=True)

    meshes = [
        {"name": "paper", "npz": pp, "shader_py": SOFT, "params": {"k": 0.6, "fw": 0.05, "fw_rough": 0.55, "fw_ior": 1.2, "rough": 0.55, "spec": 0.3, "sheen": 0.15}},
        {"name": "sticks", "npz": ps, "shader_py": SOFT, "params": {"k": 0.45, "rough": 0.34, "spec": 0.45, "smooth": True}},
        {"name": "gold", "npz": pg, "material": {"Base Color": "col", "Metallic": 1.0, "Roughness": "rough"}},
        {"name": "shutter", "npz": shutter(os.path.join(d, "shutter.npz"), tgt), "material": {"Base Color": [0.02, 0.02, 0.02], "Roughness": 0.9, "Specular IOR Level": 0.0}, "visible": {"camera": False, "glossy": False, "diffuse": False, "transmission": False}},
    ]
    lights = [
        {"name": "key", "loc": (tgt + KEY * 520.0).tolist(), "target": tgt.tolist(), "size": [36, 36], "watts": 5200000, "rgb": [1.0, 0.9, 0.74], "hide_in_gloss": True},
        {"type": "gradient", "name": "win", "loc": (tgt + np.array([70.0, -120.0, 70.0])).tolist(), "target": tgt.tolist(), "size": [150, 150], "sigma": [46, 46], "L": 0.3, "rgb": [1.0, 0.9, 0.74], "hide_in_diffuse": False},
        # what the gold mirrors: placed where the two families of pleat faces reflect the camera (r = 2(n.v)n - v); no light on the paper's matte
        {"type": "gradient", "name": "gl1", "loc": (tgt + 170 * np.array([0.65, -0.74, 0.18])).tolist(), "target": tgt.tolist(), "size": [190, 190], "sigma": [55, 55], "L": 17.0, "rgb": [1.0, 0.93, 0.8], "hide_in_gloss": False, "hide_in_diffuse": True},
        {"type": "gradient", "name": "gl2", "loc": (tgt + 170 * np.array([-0.98, -0.1, 0.18])).tolist(), "target": tgt.tolist(), "size": [190, 190], "sigma": [50, 50], "L": 12.0, "rgb": [1.0, 0.9, 0.76], "hide_in_gloss": False, "hide_in_diffuse": True},
        # the far pleats mirror the table and floor below the fan (measured r has z -.6 to -.99): a warm floor, or their flakes go black
        {"type": "gradient", "name": "gl3", "loc": (tgt + 170 * np.array([0.1, -0.55, -0.83])).tolist(), "target": tgt.tolist(), "size": [260, 260], "sigma": [80, 80], "L": 7.0, "rgb": [1.0, 0.86, 0.68], "hide_in_gloss": False, "hide_in_diffuse": True},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"window": 5.0, "win_az": 30.0, "win_el": 30.0, "win_w": 60.0, "win_h": 70.0, "strip": 1.0, "strip_az": -70.0, "wall": 0.04, "ceil": 0.14, "floor": 0.03, "seed": 15},
        "sky": {"top": [0.0065, 0.0062, 0.0058], "glow": [0.024, 0.022, 0.0195], "h": 0.75, "y0": 0.42, "x0": 0.28, "mottle": 0.14, "seed": 15},
        "bounces": 12,
        "diffuse_bounces": 8,
        "glossy_bounces": 4,
        "spp": {"sketch": 64, "preview": 128, "mid": 192, "final": 448},
    }
    if q == "sketch":
        scene["spp"] = 64
    look = {"exposure": -0.55, "wb": (1.0, 0.96, 0.86), "contrast": 1.2, "saturation": 1.05, "black": 0.001, "grain": 0.9, "sharpen": 0.2, "halation": 0.04, "glare": 0.004, "vignette": 0.28}
    if opening:
        # a candidate under its own name: _take clears {name}_move_*. A still camera, the same lights as the still, none of them moving: the fan moves
        import kit

        frames = int(sys.argv[3]) if len(sys.argv) > 3 else OPEN_FRAMES
        total = 64 if opening == "look" else int(os.environ.get("S15_SPP", 1024))
        sp = os.path.join(d, f"open.{q}.npy")
        Nst = len(np.load(ps)["V"])
        subs, spp = open_stack(sp, fan, dens, frames, total, recg, Nst)
        scene["deform"] = {"npy": sp, "vertex": ["paper", "sticks", "gold"], "spp": spp}
        scene["denoise"] = True  # as the still is: without it the dark pleats are gritty at 100% even at 1024 samples (seen). Each sub-exposure is denoised, then they are averaged
        mv = {"frames": int(subs.sum()), "shutter": 0, "spp": total}
        if opening == "look":
            mv["res"] = [960, 540]
        kit.looks = lambda: {NAME + "_open": {"move": mv}}
        os.environ["GEWU_MOVE"] = "final"
        out = shoot(NAME + "_open", scene, q, develop=look)
        open_average(out, subs)
        os.remove(sp)
        return
    shoot(NAME, scene, "preview" if q == "sketch" else q, tag=q, develop=look)


main()
