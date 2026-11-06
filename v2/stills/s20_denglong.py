"""Shot 20: the shoulder of a red silk lantern at night, glowing from inside. The silhouette of the shoulder is the arc.

    python3 -I v2/stills/s20_denglong.py [preview|mid|final]

Built like the real thing (all sizes are estimates, a palace lantern of about 34 cm):
- a bamboo cage: meridian ribs and hoops inside the silk. They are real geometry; what you see of them is their shadow,
  thrown onto the silk by the lamp;
- silk stretched rib to rib, sagging a little between them; it is gathered into pleats at the brass collar;
- a plain weave with uneven threads and slubs; the weave period is exaggerated (about 0.35 mm) to be visible at this scale;
- a forward-scattering silk (s20_shader): bright where you look through it, deep red at the rim.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from kit import OUT, ROOT, blur, color, fbm, frame_camera, shoot, sstep

W = 15.0
A, B = 17.0, 15.0  # semi-axes of the lantern
TILT = np.radians(27.0)  # the axis leans to the left in the picture
NR = 24  # ribs
PC = 0.30  # polar angle of the collar
TH0 = 0.11  # rib phase
H = W * 9 / 16

CT, ST = np.cos(TILT), np.sin(TILT)


def world(x, y, za):
    return np.stack([x * CT - za * ST, y, x * ST + za * CT], -1).astype(np.float32)


NY0, NX0 = 500, 2000
_fields = {}


def field(key, lo, hi, beta, seed):
    """A large-scale noise in (theta, p) on a fixed grid: wavelengths in cm at the shoulder."""
    if key not in _fields:
        _fields[key] = fbm((NY0, NX0), NX0 / (2 * np.pi * 14.0), lo, hi, beta, seed)
    return _fields[key]


def sample(f, TH, P):
    X = ((TH / (2 * np.pi)) % 1.0) * NX0
    Y = np.clip(P / np.pi * 2.0, 0, 0.9999) * NY0
    return blur(cv2.remap(f, X.astype(np.float32), Y.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP), 1.0)


def rib_t(TH):
    """Where we are between two ribs: 0 at a rib, 1 at the next."""
    u = ((TH - TH0) / (2 * np.pi / NR)) % 1.0
    return u


def pleat_field(nx, seed):
    """The gathers at the collar, as a height (1 = full) across theta: uneven widths, sharp crests."""
    rng = np.random.default_rng(seed)
    n = 6000
    s = np.cumsum(rng.gamma(2.2, 1.0, 900))
    s = s / s[-1] * 2 * np.pi
    x = np.linspace(0, 2 * np.pi, n, endpoint=False)
    y = np.zeros(n)
    i = np.searchsorted(s, x).clip(1, s.size - 1)
    t = np.clip((x - s[i - 1]) / (s[i] - s[i - 1]), 0, 1)
    amp = rng.uniform(0.5, 1.0, s.size)
    y = (np.abs(2 * t - 1) ** 1.6 * 2 - 1) * amp[i]
    return x, y


PX, PY = pleat_field(0, 21)


def surface(TH, P):
    """(rho-frame x, y, za) on the silk, with all its large-scale shape."""
    t = rib_t(TH)
    sag = 0.32 * np.sin(P) ** 0.8 * (4 * t * (1 - t)) ** 0.8 * (1 + 0.15 * sample(field("sag", 6, 25, 2.2, 5), TH, P))
    gather = np.exp(-((P - PC) / 0.17)) * (P >= PC)
    pl = np.interp((TH % (2 * np.pi)).ravel(), PX, PY).reshape(TH.shape)
    pl = pl * gather * 0.16
    wr = sample(field("wr", 1.5, 7.0, 2.1, 6), TH, P) * 0.055
    wr2 = sample(field("wr2", 0.6, 2.2, 2.0, 7), TH, P) * 0.015
    d = -sag + pl + wr + wr2
    rho = A * np.sin(P)
    za = B * np.cos(P)
    nr, nz = B * np.sin(P), A * np.cos(P)
    nn = np.hypot(nr, nz)
    rho2 = rho + d * nr / nn
    za2 = za + d * nz / nn
    return rho2 * np.cos(TH), rho2 * np.sin(TH), za2, pl, gather


def silk_attrs(TH, P, pxcm, fine=True, seed=11):
    t = rib_t(TH)
    ny, nx = TH.shape
    x, y, za, pl, gather = surface(TH, P)
    uneven = 1 + 0.05 * sample(field("un", 3, 16, 2.2, 8), TH, P)
    col = np.ones((ny, nx, 3), np.float32) * color([1.0, 0.15, 0.03])
    tau = np.full((ny, nx), 2.0, np.float32) * uneven
    # the pleats are several layers of silk
    tau = tau * (1 + 1.4 * gather * (pl / (0.16 * gather + 1e-5) * 0.5 + 0.5) ** 2)
    k = uneven
    if fine:
        # threads: warp along the meridians, weft along the latitudes, unevenly thick, with slubs
        rho = 14.0
        s = TH * rho
        v = P * 16.0
        per = 0.035
        rng = np.random.default_rng(seed)
        n_warp = int(2 * np.pi * rho / per) + 2
        n_weft = int(np.pi * 16 / per) + 2
        warp_k = 1 + 0.22 * rng.standard_normal(n_warp).clip(-2, 3)
        weft_k = 1 + 0.22 * rng.standard_normal(n_weft).clip(-2, 3)
        i_w = ((s / per) % n_warp)
        i_f = (v / per)
        wk = warp_k[i_w.astype(np.int32) % n_warp]
        fk = weft_k[i_f.astype(np.int32) % n_weft]
        check = np.sin(np.pi * i_w) * np.sin(np.pi * i_f)
        weave = 1 + 0.17 * check
        # thin places let more light through; the thread variation is what reads as cloth
        k = k * weave * (0.5 * wk + 0.5 * fk)
        slub = fbm((max(ny // 18, 4), nx), pxcm, 0.02, 0.6, 1.2, seed + 1)
        slub = cv2.resize(slub, (nx, ny), interpolation=cv2.INTER_LINEAR)
        k = k * (1 + 0.05 * slub)
    col = col * np.clip(k, 0.3, 1.8)[..., None]
    col = np.clip(col, 0, 1).astype(np.float32)
    return x, y, za, {"col": col, "tau": tau.astype(np.float32)}


def apex():
    """The top of the silhouette in the picture plane."""
    p = np.linspace(0, np.pi, 4000)
    x, z = A * np.sin(p), B * np.cos(p)
    X, Z = world(x, 0 * x, z)[:, 0], world(x, 0 * x, z)[:, 2]
    i = int(np.argmax(Z))
    return float(X[i]), float(Z[i])


def main():
    q = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview")
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s20_denglong")
    os.makedirs(d, exist_ok=True)
    ax, az = apex()
    target = np.array([ax + 0.6, 0.0, az - (0.5 - 0.46) * H])

    # --- find the piece of the shell inside the frame; only that gets the dense mesh
    pc, tc = np.linspace(PC, 2.2, 700), np.linspace(-np.pi - 1, np.pi + 1, 2500)
    Tg, Pg = np.meshgrid(tc, pc)
    gx, gy, gz = A * np.sin(Pg) * np.cos(Tg), A * np.sin(Pg) * np.sin(Tg), B * np.cos(Pg)
    pw = world(gx, gy, gz)
    ins = (np.abs(pw[..., 0] - target[0]) < W * 0.56) & (np.abs(pw[..., 2] - target[2]) < H * 0.6) & (pw[..., 1] < 1.5)
    jj = np.nonzero(ins.any(0))[0]
    th_lo, th_hi = tc[jj[0]], tc[jj[-1]]
    p_lo, p_hi = pc[ins.any(1)][0], pc[ins.any(1)][-1]
    print("patch", th_lo, th_hi, p_lo, p_hi)

    pxcm = 2560 * dens / W
    len_th = (th_hi - th_lo) * A * np.sin(0.5 * (p_lo + p_hi))
    len_p = (p_hi - p_lo) * 16
    nx, ny = int(len_th * pxcm), int(len_p * pxcm)
    print("dense mesh", nx, ny, nx * ny / 1e6, "M")
    th = np.linspace(th_lo, th_hi, nx, dtype=np.float32)
    p = np.linspace(p_lo, p_hi, ny, dtype=np.float32)
    TH, Pm = np.meshgrid(th, p)
    x, y, za, attrs = silk_attrs(TH, Pm, pxcm)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=world(x, y, za), mask=np.ones_like(x, np.float32), **attrs)

    # --- the rest of the shell: coarse, with a hole where the dense patch is
    tc2 = np.linspace(0, 2 * np.pi, 1400, dtype=np.float32)
    pc2 = np.linspace(PC, 3.0, 500, dtype=np.float32)
    T2, P2 = np.meshgrid(tc2, pc2)
    x2, y2, z2, a2 = silk_attrs(T2, P2, 8.0, fine=False)
    Tw = ((T2 - th_lo) % (2 * np.pi))
    hole = (Tw < (th_hi - th_lo) - 0.01) & (P2 > p_lo + 0.01) & (P2 < p_hi - 0.01)
    a2["tau"] = np.where(hole, 0.0, a2["tau"]).astype(np.float32)
    np2 = os.path.join(d, f"rest.{q}.npz")
    np.savez(np2, P=world(x2, y2, z2), **a2)

    # --- the bamboo cage, just inside the silk: an inner shell, opaque only on the ribs and hoops
    tc3 = np.linspace(0, 2 * np.pi, 2600, dtype=np.float32)
    pc3 = np.linspace(PC, 3.0, 900, dtype=np.float32)
    T3, P3 = np.meshgrid(tc3, pc3)
    tu = rib_t(T3)
    dist = np.minimum(tu, 1 - tu) * 2 * np.pi / NR * A * np.sin(P3)
    rib = sstep(0.15, 0.11, dist)
    for hp in (0.72, 1.28):
        rib = np.maximum(rib, sstep(0.12, 0.08, np.abs(P3 - hp) * 16))
    # uneven bamboo: darker near nodes
    k3 = 0.985
    x3 = k3 * A * np.sin(P3) * np.cos(T3)
    y3 = k3 * A * np.sin(P3) * np.sin(T3)
    z3 = k3 * B * np.cos(P3)
    np3 = os.path.join(d, f"cage.{q}.npz")
    np.savez(np3, P=world(x3, y3, z3), col=np.broadcast_to(color([0.12, 0.05, 0.02]), rib.shape + (3,)).astype(np.float32).copy(), tau=(rib * 30.0).astype(np.float32))

    # --- the brass collar
    tc4 = np.linspace(0, 2 * np.pi, int(2200 * dens), dtype=np.float32)
    n4 = int(420 * dens)
    s4 = np.linspace(0, 1, n4, dtype=np.float32)
    T4, S4 = np.meshgrid(tc4, s4)
    r_col = A * np.sin(PC) + 0.08
    z_col = B * np.cos(PC)
    # a turned band: roll at the foot, a shallow cove, roll at the lip
    prof_r = r_col + 0.13 * np.exp(-((S4 - 0.08) / 0.08) ** 2) + 0.17 * np.exp(-((S4 - 0.9) / 0.07) ** 2) - 0.05 * np.exp(-((S4 - 0.5) / 0.2) ** 2)
    prof_z = z_col - 0.2 + 0.85 * S4
    x4, y4 = prof_r * np.cos(T4), prof_r * np.sin(T4)
    brush = cv2.resize(fbm((n4, max(int(tc4.size // 20), 4)), 60.0, 0.01, 0.4, 1.3, 42), (T4.shape[1], T4.shape[0]), interpolation=cv2.INTER_LINEAR)
    tarn = cv2.resize(fbm((128, 512), 40.0, 0.1, 1.0, 2.0, 43), (T4.shape[1], T4.shape[0]), interpolation=cv2.INTER_CUBIC)
    a_t = 0.35 * sstep(0.1, 1.5, tarn)
    base = color([0.80, 0.56, 0.25])[None, None] * (1 - 0.18 * a_t[..., None])
    np4 = os.path.join(d, f"collar.{q}.npz")
    np.savez(np4, P=world(x4, y4, prof_z), col=base.astype(np.float32), rough=(0.24 + 0.035 * brush + 0.08 * a_t).clip(0.12, 0.8).astype(np.float32))

    # --- night behind: other lanterns far away
    n = 400
    rng = np.random.default_rng(3)
    em = np.zeros((n, n, 3), np.float32)
    for _ in range(9):
        i, j = rng.integers(0, n, 2)
        cv2.circle(em, (int(j), int(i)), int(rng.integers(2, 4)), (float(rng.uniform(0.3, 1.0)) * 0.9, float(rng.uniform(0.05, 0.18)), 0.012), -1, cv2.LINE_AA)
    xb = np.linspace(-110, 110, n)
    Xb, Zb = np.meshgrid(xb, xb)
    npb = os.path.join(d, "bg.npz")
    np.savez(npb, P=np.stack([Xb, np.full_like(Xb, 420.0), Zb + 30], -1).astype(np.float32), em=em)

    fp = world(*[np.array(v) for v in (A * np.sin(0.6), 0.0, B * np.cos(0.6))])
    view = np.array([0.03, -1.0, -0.02])
    cam = frame_camera(target, view, W, 95.0, aperture_mm=6.5, focus_point=np.array([ax, -1.2, az]))
    silk = {"k_cos": 2.6, "peak": 5.5, "floor": 0.16, "k_deep": 0.55, "through": [1.0, 0.22, 0.09]}
    shader = os.path.join(ROOT, "v2", "stills", "s20_shader.py")
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "silk", "npz": npz, "shader_py": shader, "params": silk},
            {"name": "rest", "npz": np2, "shader_py": shader, "params": silk},
            {"name": "cage", "npz": np3, "shader_py": shader, "params": {"peak": 0.0, "floor": 1.0, "through": [1, 1, 1]}},
            {"name": "collar", "npz": np4, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": 1.0}},
            {"name": "bg", "npz": npb, "material": {"Base Color": [0.0, 0.0, 0.0], "Roughness": 1.0, "Emission Color": "em", "Emission Strength": 1.0}},
        ],
        "lights": [
            {"name": "lamp", "type": "point", "loc": (world(np.array(1.0), np.array(0.0), np.array(4.0)) + np.array([0, -7.0, 0])).tolist(), "radius": 1.6, "watts": 9000, "rgb": [1.0, 0.72, 0.42]},
            {"type": "gradient", "name": "scrim", "loc": [-16, -70, 26], "target": [-9, 0, 13], "size": [60, 40], "sigma": [16, 9], "L": 2.2, "rgb": [1.0, 0.86, 0.66]},
            {"name": "rim", "loc": [30, -24, 42], "target": target.tolist(), "size": [10, 10], "watts": 1200, "rgb": [1.0, 0.82, 0.62]},
        ],
        "world": [0.0006, 0.0004, 0.0005],
        "bounces": 12,
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "transmission_bounces": 10,
        "spp": {"preview": 96, "mid": 160, "final": 384},
    }
    look = {"exposure": -0.45, "contrast": 1.34, "saturation": 1.04, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.12, "glare": 0.004}
    shoot("s20_denglong", scene, q, develop=look)


main()
