"""Shot 39: a lotus half open against the sun, in the leaf field. The top of the flower is the arc.

    python3 -I v2/stills/s39_hehua.py [sketch|preview|mid|final]

The old shot was one flat arch of petal on black, with a sugar-like grain and veins like pen strokes (git history has it). Set against ref/lotus_petal:
- a real flower is many whole boat-shaped petals, overlapping; most of what is beautiful is one petal seen through another, so each petal here is a surface of its own and the light really passes through;
- veins are soft and low in contrast, wander, fork, some run out at the margin before the tip; there is no grain at this scale; the colour is a long wash, white at the base, deep at the tip;
- the background is the field itself, real leaves in real blur (a background has to mean something), lit by the same sun.
Sizes are estimates from general knowledge (petal 10-13 x 6-8 cm), not measured. The flower is ours, not traced from a photograph. Below the frame there is no stem or receptacle: the frame hides it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, color, fbm, frame_camera, mix, shoot, sstep
from lotuslib import FAR_MAT, SHEET, far_leaf, pond_env, stalk, water
from s21_lib import smooth1d, up
from vessel import project, view_dir

NAME = "s39_hehua"
W, EL, DIST = 31.0, 4.0, 150.0
APEX = 0.27
APERTURE = 19.0
SUN = np.array([-0.42, 0.62, 0.66])
SUN = SUN / np.linalg.norm(SUN)
OUTL_S = np.array([0.0, 0.06, 0.2, 0.4, 0.6, 0.75, 0.87, 0.95, 0.985, 1.0])
OUTL_W = np.array([0.2, 0.28, 0.58, 0.88, 1.0, 0.99, 0.88, 0.63, 0.34, 0.0])  # a blunt, rounded end with a small point; a sharper one read as a tent
MAT = {"k": 0.46, "rough": 0.42, "spec": 0.32, "sheen": 0.25, "sheen_rough": 0.6}


def veins(s, U, hw, rng):
    """The veins of one petal in its own (u, s) plan. They fan from the base and hold their share of the width; those near the sides run out at the margin. Returns the strength of the nearest vein, its soft shoulder and the pillow of tissue between veins."""
    ny, nx = U.shape
    nk = 38
    u0 = np.sort(np.linspace(-1.06, 1.06, nk) + rng.normal(0, 0.014, nk))
    start = np.where(rng.random(nk) < 0.42, 0.0, rng.uniform(0.04, 0.6, nk))
    end = rng.uniform(0.82, 1.1, nk)
    amp = np.where(start == 0.0, rng.uniform(0.7, 1.0, nk), rng.uniform(0.3, 0.75, nk))
    wid = np.where(start == 0.0, rng.uniform(0.024, 0.04, nk), rng.uniform(0.014, 0.024, nk))
    paths = np.zeros((nk, ny), np.float32)
    for k in range(nk):
        paths[k] = u0[k] * (1 + 0.32 * sstep(0.45, 1.0, s)) + 0.01 * smooth1d(ny, 0.08 * ny, rng) + 0.002 * smooth1d(ny, 0.025 * ny, rng)
    for k in range(nk):  # a late vein leaves its neighbour; that is the fork
        if start[k] > 0:
            j = k - 1 if k > 0 and (k == nk - 1 or rng.random() < 0.5) else k + 1
            paths[k] = mix(paths[j], paths[k], sstep(start[k], start[k] + 0.14, s))
    vein = np.zeros((ny, nx), np.float32)
    side = np.zeros((ny, nx), np.float32)
    pillow = np.zeros((ny, nx), np.float32)
    x = U[0]
    for i in range(ny):
        act = (s[i] >= start) & (s[i] <= end)
        if act.sum() < 2:
            continue
        c = np.maximum.accumulate(paths[act, i])
        j = np.clip(np.searchsorted(c, x), 1, c.size - 1)
        dl, dr = x - c[j - 1], c[j] - x
        left = np.abs(dl) < np.abs(dr)
        near = np.where(left, j - 1, j)
        d = np.abs(np.where(left, dl, dr)) * hw[i]
        wk = wid[act][near] * (0.55 + 0.45 * sstep(0.0, 0.5, 1.0 - s[i]))
        a = amp[act][near]
        vein[i] = a * np.exp(-((d / wk) ** 2))
        side[i] = a * np.exp(-((d / (3.2 * wk)) ** 2))
        pillow[i] = np.clip(d / (0.5 * np.abs(dl + dr) * hw[i] + 1e-4), 0, 1)
    return vein, side, pillow


def petal(sp, dens):
    L, Wd = sp["L"], sp["W"]
    pxcm = 92.0 * dens * sp.get("d", 1.0)
    ny, nx = max(int(L * pxcm), 72), max(int(Wd * pxcm), 56)
    seed = sp["seed"]
    rng = np.random.default_rng(seed)
    s = np.linspace(0, 1, ny, dtype=np.float32)
    u = np.linspace(-1, 1, nx, dtype=np.float32)
    U, S = np.meshgrid(u, s)
    A = np.abs(U)

    dense = np.linspace(0, 1, 2048)
    wt = cv2.GaussianBlur(np.interp(dense, OUTL_S, OUTL_W).astype(np.float32)[None, :], (0, 0), 14.0, borderType=cv2.BORDER_REPLICATE)[0]
    wt[-1] = 0.0
    w = np.interp(s, dense, wt).astype(np.float32)
    w = w * (1 + 0.018 * sstep(0.0, 0.3, 1 - s) * smooth1d(ny, 0.05 * ny, rng) + 0.006 * smooth1d(ny, 0.012 * ny, rng))
    hw = 0.5 * Wd * np.maximum(w, 1e-4)

    vein, side, pillow = veins(s, U, hw, rng)

    # coarse fields come from a fixed small grid, opened; only what must be fine is made fine
    c2 = 256.0 / max(L, Wd)
    f0 = cv2.GaussianBlur(cv2.resize(fbm((48, 256), c2, 2.0, 12.0, 2.4, seed + 7).astype(np.float32), (nx, ny), interpolation=cv2.INTER_CUBIC), (0, 0), 0.02 * ny)  # long: a petal buckles along its veins, not across them
    f1 = up(fbm((256, 256), c2, 0.5, 2.0, 2.0, seed + 8).astype(np.float32), ny, nx)
    wash = up(fbm((256, 256), c2, 1.5, 7.0, 2.2, seed + 6).astype(np.float32), ny, nx)
    streak = cv2.resize(fbm((max(ny // 14, 8), nx), pxcm, 0.06, 0.7, 1.6, seed + 4).astype(np.float32), (nx, ny), interpolation=cv2.INTER_CUBIC)
    crk = cv2.resize(fbm((max(ny // 7, 8), nx), pxcm, 0.03, 0.16, 1.4, seed + 11).astype(np.float32), (nx, ny), interpolation=cv2.INTER_CUBIC)
    tip = sstep(0.74, 0.97, S)

    # --- the sheet: all displacements along its outward normal
    ruf_l = smooth1d(ny, 0.05 * ny, rng)
    ruf_r = smooth1d(ny, 0.05 * ny, rng)
    ruf = np.where(U < 0, ruf_l[:, None], ruf_r[:, None])
    dn = sp.get("bump", 0.2) * f0 * sstep(0.0, 0.25, S) + 0.012 * f1
    dn = dn + 0.012 * sstep(0.0, 1.0, pillow) * (1 - 0.5 * tip) - 0.005 * vein
    dn = dn + 0.012 * crk * tip * (0.4 + 0.6 * A)
    dn = dn + sp.get("roll", 0.3) * A**9 * sstep(0.15, 0.6, S) + 0.11 * ruf * A**4 * sstep(0.1, 0.5, S)
    dn = dn + 0.022 * np.exp(-((U / 0.05) ** 2)) * sstep(0.45, 0.95, S)  # the point draws out into a slight keel

    a = np.radians(sp["alpha"] + sp["beta"] * (1 - s) ** 1.6 - sp["gamma"] * s**1.8)
    ds = L / (ny - 1)
    rho = sp["r0"] + np.cumsum(np.sin(a)) * ds
    z = sp["zb"] + np.cumsum(np.cos(a)) * ds
    phi = np.radians(sp["az"] + sp.get("twist", 0.0) * s)
    psi = np.radians(sp["psi"]) * (0.78 + 0.22 * np.sin(np.pi * s)) * (1 - 0.4 * sstep(0.75, 1.0, s))  # the end flattens out
    Th = U * psi[:, None]
    Rc = hw[:, None] / np.sin(psi)[:, None]
    xc = Rc * np.sin(Th) + sp.get("lean", 0.0) * (S**2)
    off = Rc * (1 - np.cos(Th))
    er = np.stack([np.cos(phi), np.sin(phi), 0 * phi], -1)[:, None, :]
    ep = np.stack([-np.sin(phi), np.cos(phi), 0 * phi], -1)[:, None, :]
    ez = np.array([0.0, 0.0, 1.0], np.float32)
    N = np.stack([np.cos(a) * np.cos(phi), np.cos(a) * np.sin(phi), -np.sin(a)], -1)[:, None, :]
    C = rho[:, None, None] * er + z[:, None, None] * ez
    P = C + xc[..., None] * ep + (dn - off)[..., None] * N

    # --- the colour. Anthocyanin in a white tissue: absorbs green, some blue, almost no red
    g = sstep(sp.get("g0", 0.2) + 0.09 * wash, 0.98, S + 0.04 * wash) ** sp.get("gp", 1.5) + 0.55 * sstep(0.84, 1.0, S)
    edge = np.exp(-(1 - A) / 0.07) * sstep(0.3, 0.8, S)
    pale = sstep(0.8, 1.7, crk) * tip
    p = sp["P"] * (g * (1 + 0.055 * streak + 0.12 * wash) + 0.3 * edge)
    p = (p + sp["P"] * g**0.6 * (0.2 * vein + 0.07 * side)) * (1 - 0.55 * pale)
    p = np.maximum(p, 0.0)
    T = np.exp(-p[..., None] * color([0.035, 1.12, 0.5]))
    T = T * np.exp(-((1 - sstep(0.0, 0.26, S)) ** 2)[..., None] * color([0.06, 0.04, 0.55]))  # the base goes creamy, then a little green
    col = np.clip(T**1.3 * 0.86, 0, 1)
    tr = np.clip(T * 0.92, 0, 1)
    return P.astype(np.float32), col.astype(np.float32), tr.astype(np.float32)


def whorl(az, base, seed, jit=(5.0, 3.0)):
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
        sp["P"] = 1.2 * base["P"] * r.uniform(0.88, 1.12)
        out.append(sp)
    return out


def flower():
    """From the middle out: a closed heart, then petals opening further and further. Each whorl sits outside the last."""
    A = whorl([-62, 12, 86, 158, 230], dict(L=12.6, W=6.0, alpha=4, beta=26, gamma=30, psi=74, r0=0.8, zb=0.9, P=0.9, g0=0.3, d=0.45, roll=0.12, bump=0.1), 3910, (3.0, 2.0))
    B = whorl([-93, -30, 30, 90, 150, 210], dict(L=12.0, W=7.5, alpha=17, beta=24, gamma=24, psi=58, r0=1.5, zb=0.4, P=1.0, g0=0.22, d=0.7, roll=0.2, bump=0.09), 3920, (2.5, 2.0))
    C = whorl([-125, -62, -8, 46, 102, 158, 214], dict(L=12.6, W=7.9, alpha=42, beta=22, gamma=28, psi=42, r0=2.2, zb=0.1, P=0.85, g0=0.28, d=0.9, roll=0.3, bump=0.13), 3930, (5.0, 3.0))
    D = whorl([-152, -96, -38, 28, 88, 150], dict(L=12.0, W=7.2, alpha=70, beta=16, gamma=38, psi=30, r0=2.8, zb=-0.5, P=0.8, g0=0.3, d=0.9, roll=0.34, bump=0.16), 3940, (7.0, 4.0))
    E = whorl([-120, -60, 0, 60, 120, 180], dict(L=10.5, W=6.2, alpha=96, beta=6, gamma=24, psi=26, r0=3.0, zb=-1.2, P=0.85, g0=0.25, d=0.5, roll=0.34, bump=0.2), 3950, (7.0, 4.0))
    B[0].update(az=-93.0, alpha=15.0, d=1.0, twist=4.0, lean=0.2, L=12.3, W=7.9)  # the one in focus, that looks at the camera
    return A + B + C + D + E


def field(d, q):
    """The leaf field, out to the bank. Positions are chosen so that the frame is not empty anywhere; a pair of far flowers among them."""
    rng = np.random.default_rng(39)
    out = []
    for i in range(70):
        y = float(np.exp(rng.uniform(np.log(70.0), np.log(1500.0))))
        half = 0.55 * W * (DIST + y) / DIST
        x = float(rng.uniform(-half, half))
        # the leaves stand on stalks, up to about the height of the flower
        z = float(rng.uniform(-42.0, 4.0))
        R = float(rng.uniform(16.0, 30.0))
        p = os.path.join(d, f"lf{i}.npz")
        far_leaf(p, (x, y, z), R, float(rng.uniform(0, 26)), float(rng.uniform(0, 360)), 3900 + i)
        out.append({"name": f"lf{i}", "npz": p, "shader_py": SHEET, "params": FAR_MAT})
        if y < 260 and rng.random() < 0.7:
            ps = os.path.join(d, f"st{i}.npz")
            stalk(ps, (x, y, z), -90.0, lean=(float(rng.normal(0, 3)), float(rng.normal(0, 3))))
            out.append({"name": f"st{i}", "npz": ps, "shader_py": SHEET, "params": {"k": 0.1, "rough": 0.5, "spec": 0.3}})
    return out


def camera():
    H = W * 9 / 16
    view = view_dir(-90.0, EL)
    t = np.array([0.0, 0.0, 6.0])
    return view, H, t


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"sketch": 0.22, "preview": 0.4, "mid": 0.65, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)

    meshes, tops = [], []
    specs = flower()
    for i, sp in enumerate(specs):
        P, col, tr = petal(sp, dens)
        p = os.path.join(d, f"p{i}.{q}.npz")
        np.savez(p, P=P, col=col, tr=tr)
        meshes.append({"name": f"p{i}", "npz": p, "shader_py": SHEET, "params": MAT})
        tops.append(P[-40:].reshape(-1, 3))
    tops = np.concatenate(tops)
    print(f"{len(specs)} petals, {sum(np.load(m['npz'])['P'].size for m in meshes) / 3e6:.1f} M vertices", flush=True)
    hero = np.load(meshes[5]["npz"])["P"]  # B[0], the petal in focus
    focus = hero[int(0.72 * hero.shape[0]), hero.shape[1] // 2]

    view, H, tgt = camera()
    for _ in range(4):
        cam = frame_camera(tgt, view, W, DIST)
        _, y, _ = project(cam, tops)
        tgt[2] -= (float(y.min()) - APEX) * H
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, tops)
    print(f"apex y {y.min():.3f}, x span {x.min():.2f}..{x.max():.2f}", flush=True)

    meshes += field(d, q)
    # another flower and a bud further into the field: only what the blur needs
    for tag, at, take in (("ff", (-37.0, 330.0, -6.0), specs), ("fb", (37.0, 300.0, -6.0), specs[:5])):
        for i, sp in enumerate(take):
            P_, col_, tr_ = petal({**sp, "d": 0.3, "seed": sp["seed"] + 7}, 0.5)
            p = os.path.join(d, f"{tag}{i}.npz")
            np.savez(p, P=P_ + np.array(at, np.float32), col=col_, tr=tr_)
            meshes.append({"name": f"{tag}{i}", "npz": p, "shader_py": SHEET, "params": MAT})
    meshes.append({"name": "pond", "npz": water(os.path.join(d, "pond.npz"), -90.0), "material": {"Base Color": [0.006, 0.02, 0.018], "Roughness": 0.04, "IOR": 1.33, "Specular IOR Level": 0.5}})
    tg = tgt.tolist()
    lights = [{"name": "sun", "loc": (tgt + SUN * 500.0).tolist(), "target": tg, "size": [34, 34], "watts": 1700000, "rgb": [1.0, 0.95, 0.86], "hide_in_gloss": True}]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": pond_env(os.path.join(d, "env.npy"), SUN, tree_el=8.0, gain=0.58, seed=39), "diffuse": True, "transmission": True},
        "bounces": 14,
        "diffuse_bounces": 10,  # light goes through several petals before it reaches the eye
        "glossy_bounces": 4,
        "spp": {"sketch": 64, "preview": 128, "mid": 192, "final": 448},
    }
    if q == "sketch":
        scene["spp"] = 64
    shoot(NAME, scene, "preview" if q == "sketch" else q, tag=q, develop={"exposure": 0.12, "contrast": 1.14, "saturation": 1.08, "black": 0.001, "grain": 0.9, "sharpen": 0.18, "halation": 0.05, "glare": 0.004, "vignette": 0.3})


main()
