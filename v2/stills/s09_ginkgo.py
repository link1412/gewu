"""Shot 9, moving: a golden ginkgo leaf against low sun, a breath of wind goes through it. The old still and its script (s09_yinxing.py) stay as they are.

    python3 -I v2/stills/s09_ginkgo.py flat [dens]          the tissue in the shot's framing, no render
    python3 -I v2/stills/s09_ginkgo.py layout             the motion through the camera, no render, seconds: out/v2/s09_yinxing_wind/layout.{jpg,mp4}
    python3 -I v2/stills/s09_ginkgo.py still preview|mid|cand
    python3 -I v2/stills/s09_ginkgo.py take low|final       every frame (low: small, no sub-exposures), developed into out/v2/s09_yinxing_take_{cand}

The leaf is in s09_leaf.py. Only the two lobes beside the notch move, a slow rise and fall in the frame's time, see Skin and swell: no wind or plate is solved, the weight and timing are chosen (rejected: a solved flutter, a slow solved lean, and each lobe moving on its own, which opened the notch like a crack).
The shadows of a neighbour leaf and a twig are real occluders and do not move. The camera does not move. The light through the lobes and the sheen on them change as they tilt, by themselves.
`layout` prints the travel of the lobes' tips and of the margin further out, and the notch's width through the frames.
Motion blur: sub-exposures of the moving mesh, averaged.
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
import s09_leaf as LF
from kit import OUT, ROOT, _cam_axes, color, fbm, frame_camera, shoot

NAME = "s09_yinxing"
FRAMES = int(os.environ.get("S09_FRAMES", 36))
SHUTTER = 0.5
SUB = int(os.environ.get("S09_SUB", 6))
LOOK = {"exposure": -0.15, "contrast": 1.38, "saturation": 1.05, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "glare": 0.002}
SUN = np.array([9.0, 30.0, -7.0])


def times(sub):
    return (np.arange(FRAMES)[:, None] + (SHUTTER * ((np.arange(sub) + 0.5) / sub - 0.5))[None, :]).ravel() / 25.0


def camera(P):
    H = LF.W * 9 / 16
    az, el = np.radians(4.0), np.radians(-11.0)
    view = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])
    # the frame sits so that the arc stays at the old still's height, 0.365
    target = np.array([0.0, 0.0, LF.R - (0.5 - 0.40) * H - float(os.environ.get("S09_LOWER", 0.037))])
    i, j = int(P.shape[0] * (LF.R - 0.45 - LF.R0) / (LF.ROUT - LF.R0)), P.shape[1] // 2
    return frame_camera(target, view, LF.W, 30.0, aperture_mm=float(os.environ.get("S09_AP", 8.0)), focus_point=P[i, j])


def project(cam, V):
    right, up, back = _cam_axes(cam)
    d = V - np.array(cam["loc"], np.float32)
    zc = -(d @ back.astype(np.float32))
    f = cam["lens_mm"] / 36.0
    return 0.5 + f * (d @ right.astype(np.float32)) / zc, 0.5 - (16 / 9) * f * (d @ up.astype(np.float32)) / zc, zc


def smooth5(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * u * (u * (6 * u - 15) + 10)


class Skin:
    """Only the two lobes beside the notch move. The rest of the leaf is stiff and stays exactly where it is.
    One field across the notch, never one per lobe: the notch read as cracking open when each lobe had its own timing and a sideways opening. The mesh is continuous across the notch (the notch is only the mask), so two points facing each other across it move almost alike.
    The weight is 0 at and below the notch's root and up to LOW of the notch's length, so the root stays put, 1 at the crown near the notch, flat across the notch itself, and reaches 0 within LT cm sideways, with continuous slope and curvature.
    The direction is one vector, the sheet's normal around the notch leaned towards the camera by MIX, so nothing slides within the sheet. The more it leans, the less the notch's edges slide past a row of the image and the more the motion is seen as light through the tilting lobes than as travel."""

    LT = 2.1  # how far the motion reaches sideways, cm: chosen

    def __init__(self, P, n, g):
        self.P = P
        Rr, Th = g["r"][:, None], g["th"][None, :]
        tn = (Th - LF.NOTCH_AT) * Rr
        self.jl = int(np.searchsorted(g["th"], LF.NOTCH_AT))
        self.tip = float(g["R_m"][self.jl - 8 : self.jl + 8].min())
        start = self.tip + LOW * (LF.R - self.tip)
        self.w = (smooth5(1 - np.abs(tn) / self.LT) * smooth5((Rr - start) / (LF.R - start))).astype(np.float32)
        nd = n[self.w > 0.5].mean(0)
        nd = nd / np.linalg.norm(nd)
        cam = camera(P)
        i = int(np.searchsorted(g["r"], self.tip))
        to_cam = np.array(cam["loc"], np.float64) - P[i, self.jl]
        to_cam = to_cam / np.linalg.norm(to_cam)
        if nd @ to_cam < 0:
            nd = -nd
        d = (1 - MIX) * nd + MIX * to_cam
        self.d = (d / np.linalg.norm(d)).astype(np.float32)
        self.x = P[..., 0]

    def vertices(self, phi, i):
        s = swell(phi["t"][i] - DRIFT * self.x)
        return self.P + (self.w * s * AMP)[..., None] * self.d


LOW = float(os.environ.get("S09_LOW", 0.6))  # the lower part of the notch that does not move at all, as a fraction of its length: a V rising through a row of the image changes the width on that row
AMP = float(os.environ.get("S09_AMP", 0.047))  # cm, half the travel at weight 1
MIX = float(os.environ.get("S09_MIX", 0.4))  # 0: along the sheet's normal, 1: straight at the camera
DRIFT = float(os.environ.get("S09_DRIFT", 0.05))  # s per cm across the frame: the swell arrives a little later further right, a wavelength of 38 cm against a notch under 0.2 cm wide
PERIOD = (1.9, 3.3)


def swell(t):
    """The slow rise and fall, -1 to 1. The main period is PERIOD[0] s of playback, the floor is 1.5 s; a slower one keeps it from repeating. Chosen, not solved: no wind is simulated."""
    return 0.82 * np.sin(2 * np.pi * t / PERIOD[0] + 0.35) + 0.18 * np.sin(2 * np.pi * t / PERIOD[1] + 2.0)


def phases(ts):
    return {"t": ts}


def notch_edges(at, g, jl, reach=0.5):
    """The notch's two edges in the grid, row by row of the tissue: (i, left column, right column), columns fractional where the mask crosses 0.5. Rows where the walk finds no tissue within reach cm are left out."""
    m = at["mask"]
    out = []
    for i in np.where(m[:, jl] < 0.5)[0]:
        lim = int(reach / (g["r"][i] * (g["th"][1] - g["th"][0])))
        L = np.where(m[i, max(0, jl - lim) : jl] >= 0.5)[0]
        Rg = np.where(m[i, jl : jl + lim] >= 0.5)[0]
        if not len(L) or not len(Rg):
            continue
        a = jl - lim + L[-1] if jl >= lim else L[-1]
        b = jl + Rg[0]
        fa = (m[i, a] - 0.5) / max(m[i, a] - m[i, a + 1], 1e-6)
        fb = (0.5 - m[i, b - 1]) / max(m[i, b] - m[i, b - 1], 1e-6)
        out.append((i, a + fa, b - 1 + fb))
    if len(out) < 8:
        raise SystemExit("the notch was not found in the mask")
    return np.array(out)


def gap_numbers(P, at, n, g, quiet=False):
    """The notch's width through the frames from the geometry, in px of 1920 x 1080: on fixed rows of the image, and between the same two points of the tissue. And where the root goes."""
    cam = camera(P)
    sk = Skin(P, n, g)
    E = notch_edges(at, g, sk.jl)
    ii = E[:, 0].astype(int)
    root = ii.argmin()
    ts = times(1)
    phi = phases(ts)

    def at_edge(V, col):
        c0 = np.floor(col).astype(int)
        f = (col - c0)[:, None]
        return V[ii, c0] * (1 - f) + V[ii, c0 + 1] * f

    XL, XR, YL, YR = [], [], [], []
    for k in range(len(ts)):
        V = sk.vertices(phi, k)
        for col, X, Y in ((E[:, 1], XL, YL), (E[:, 2], XR, YR)):
            u, v, _ = project(cam, at_edge(V, col))
            X.append(u * 1920)
            Y.append(v * 1080)
    XL, XR, YL, YR = map(np.array, (XL, XR, YL, YR))
    root_y = np.maximum(YL[:, root], YR[:, root])
    y0 = max(YL.min(1).max(), YR.min(1).max())  # highest row every frame has both edges on
    y1 = min(YL.max(1).min(), YR.max(1).min())
    rows = np.arange(np.ceil(y0), np.floor(y1), 2.0)
    W = []
    for k in range(len(ts)):
        a, b = np.argsort(YL[k]), np.argsort(YR[k])
        W.append(np.interp(rows, YR[k][b], XR[k][b]) - np.interp(rows, YL[k][a], XL[k][a]))
    W = np.array(W)
    span = W.max(0) - W.min(0)
    body = rows > rows[0] + 0.25 * (rows[-1] - rows[0])
    mat = XR - XL
    frac = (rows - rows[0]) / max(rows[-1] - rows[0], 1)
    res = {
        "row_span_by_height": {f"{a:.2f}-{b:.2f}": float(span[(frac >= a) & (frac <= b)].max()) for a, b in ((0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 1.0))},  # 0 is the top of the notch
        "width_by_height": {f"{a:.2f}": float(np.interp(a, frac, W.mean(0))) for a in (0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0)},
        "rows": len(rows),
        "row_span_max": float(span.max()),
        "row_span_body": float(span[body].max()),
        "width_rest": [float(W.mean(0).min()), float(W.mean(0).max())],
        "tissue_span_max": float((mat.max(0) - mat.min(0)).max()),
        "root_travel": float(np.hypot(*(np.array([XL[:, root], YL[:, root]]).T - [XL[0, root], YL[0, root]]).T).max()),
        "notch_len_span": float((YL.max(1) - YL.min(1)).max() - (YL.max(1) - YL.min(1)).min()),
        "len": float((YL.max(1) - YL.min(1)).mean()),
    }
    if not quiet:
        print("notch from geometry, px of 1920 x 1080:", json.dumps(res, default=lambda v: round(float(v), 2)))
    return res


def shadows():
    """A neighbour leaf and a twig between the sun and this leaf, black outlines invisible to the camera. They do not move."""
    d0 = SUN - np.array([0.0, 0.0, 6.0])
    d0 = d0 / np.linalg.norm(d0)
    out, base = LF.fan_poly(4.9, -0.55, 6.6, -1.05, 0.2, 44)
    V = np.vstack([base[None], out])
    F = np.stack([np.zeros(len(out) - 1, int), np.arange(1, len(out)), np.arange(2, len(out) + 1)], -1)
    occ = (np.stack([V[:, 0], np.zeros(len(V)), V[:, 1]], -1) + 5.5 * d0).astype(np.float32)
    t = np.linspace(0, 1, 40)
    cx, cz = -3.15 + 2.7 * t + 0.1 * np.sin(t * 2.2), 7.4 - 3.0 * t
    wd = 0.04 + 0.016 * t
    Vt = np.vstack([np.stack([cx - wd, 0 * t, cz - wd * 0.8], -1), np.stack([cx + wd, 0 * t, cz + wd * 0.8], -1)]) + 3.5 * d0
    Ft = []
    for i in range(39):
        Ft += [[i, i + 1, 40 + i], [i + 1, 41 + i, 40 + i]]
    return (occ, F.astype(np.int32)), (Vt.astype(np.float32), np.array(Ft, np.int32))


def splat(cam, V, col, w, h):
    u, v, _ = project(cam, V.reshape(-1, 3))
    iu, iv = (u * w).astype(np.int32), (v * h).astype(np.int32)
    ok = (iu >= 0) & (iu < w) & (iv >= 0) & (iv < h)
    ind = iv[ok] * w + iu[ok]
    n = np.bincount(ind, minlength=w * h).astype(np.float32)
    im = np.stack([np.bincount(ind, weights=col[..., c].reshape(-1)[ok], minlength=w * h) for c in range(3)], -1).astype(np.float32)
    return (im / np.maximum(n, 1)[:, None]).reshape(h, w, 3), n.reshape(h, w) > 0


def to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1]


def flat(dens):
    P, at, n, g = LF.leaf(dens)
    cam = camera(P)
    w, h = (2560, 1440) if dens >= 1.0 else (960, 540)
    L = at["scat"] * at["mask"][..., None] * 2.0
    im, ok = splat(cam, P, L, w, h)
    from darkroom import develop

    d = develop(im, **{**LOOK, "grain": 0})
    p = os.path.join(OUT, NAME, "flat.jpg")
    cv2.imwrite(p, to8(d), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(p)


def layout():
    """No render, seconds: the leaf through the camera with the light of its own tilt, and its numbers."""
    import time

    t0 = time.time()
    P, at, n, g = LF.leaf(0.3)
    cam = camera(P)
    ts = times(1)
    phi = phases(ts)
    sk = Skin(P, n, g)
    w, h = 720, 404
    d = os.path.join(OUT, NAME + "_wind")
    os.makedirs(d, exist_ok=True)
    sun = SUN - np.array([0, 0, 6.0])
    sun = (sun / np.linalg.norm(sun)).astype(np.float32)
    from darkroom import develop

    # points on the margin, by how far they are from the notch along it
    js = np.arange(P.shape[1])
    im_ = np.clip(np.searchsorted(g["r"], g["R_m"] - 0.01), 0, P.shape[0] - 1)
    tn = (g["th"] - LF.NOTCH_AT) * LF.R
    pick = {"L tip": np.argmin(np.abs(tn + 0.12)), "R tip": np.argmin(np.abs(tn - 0.12)), "L crown (1 cm out)": np.argmin(np.abs(tn + 1.0)), "R crown (1 cm out)": np.argmin(np.abs(tn - 1.0)), "L far (2.5 cm out)": np.argmin(np.abs(tn + 2.5)), "R far (2.5 cm out)": np.argmin(np.abs(tn - 2.5))}
    tr = {k: [] for k in pick}
    frames, apex, margin = [], [], []
    every = js[:: max(1, P.shape[1] // 400)]
    for k in range(len(ts)):
        V = sk.vertices(phi, k)
        du, dv = np.gradient(V, axis=1), np.gradient(V, axis=0)
        nn = np.cross(du, dv)
        nn = nn / (np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9)
        L = at["scat"] * at["mask"][..., None] * (0.15 + 2.2 * np.abs(nn @ sun)[..., None])
        im, ok = splat(cam, V, L, w, h)
        frames.append(to8(develop(cv2.medianBlur(im, 3), **{**LOOK, "grain": 0})))
        for name, j in pick.items():
            u, v, _ = project(cam, V[im_[j], j][None])
            tr[name].append((u[0] * 2560, v[0] * 1440))
        u, v, _ = project(cam, V[im_[every], every])
        margin.append(np.stack([u * 2560, v * 1440], -1))
        apex.append(float(v[(u > 0.35) & (u < 0.65)].min()))
    print("px of 2560 x 1440. Travel of each margin point, largest distance between any two frames:")
    for name, c in tr.items():
        c = np.array(c)
        span = np.linalg.norm(c[:, None] - c[None], axis=-1).max()
        print(f"  {name:20s} {span:6.1f} px = {span / 25.6:.2f}% of width; biggest step {np.linalg.norm(np.diff(c, axis=0), axis=1).max():.2f} px; y curve {np.round(c[::5, 1] - c[0, 1], 1).tolist()}")
    M = np.array(margin)
    span = np.linalg.norm(M - M[0], axis=-1).max(0)
    tnm = tn[every]
    print("largest travel by distance from the notch along the margin (cm: px):", {x: round(float(span[np.abs(np.abs(tnm) - x) < 0.1].max()), 1) for x in (0.2, 0.5, 1.0, 1.5, 2.0, 2.2, 3.0, 4.0)})
    gap_numbers(P, at, n, g)
    print("apex_y", round(min(apex), 3), round(max(apex), 3), "still frame apex at rest:", round(float(project(cam, P[im_[every], every])[1][(project(cam, P[im_[every], every])[0] > 0.35) & (project(cam, P[im_[every], every])[0] < 0.65)].min()), 3))
    picks = np.linspace(0, len(frames) - 1, 12).astype(int)
    rows = [np.hstack([cv2.resize(frames[i], (640, 360), interpolation=cv2.INTER_AREA) for i in picks[k : k + 3]]) for k in range(0, 12, 3)]
    cv2.imwrite(os.path.join(d, "layout.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
    mp4(frames, os.path.join(d, "layout.mp4"), bgr=True)
    print(os.path.join(d, "layout.jpg"), "total", round(time.time() - t0, 1))


def mp4(frames, path, bgr=False):
    h, w = frames[0].shape[:2]
    tmp = path + ".tmp.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", "25", "-i", "-", "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for f in frames:
        ff.stdin.write(f.tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed")
    os.replace(tmp, path)


def trees(d, seed=3):
    """The far background: a dim emissive plate, dark canopy with a few gaps, as in the old still. The lens turns it into shapes without edges."""
    rng = np.random.default_rng(seed)
    n = 512
    f = fbm((n, n), n / 140.0, 5, 50, 2.4, seed)
    x = np.linspace(-70, 70, n)
    X, Z = np.meshgrid(x, x)
    base = np.clip(0.012 + 0.012 * (f + 0.4), 0.002, None)
    col = base[..., None] * color([0.48, 0.62, 0.42])
    gaps = np.zeros((n, n), np.float32)
    for _ in range(30):
        i, j = rng.integers(0, n, 2)
        gaps[i, j] = rng.uniform(0.2, 1.0) ** 2.5
    gaps = cv2.GaussianBlur(gaps, (0, 0), 1.0) * 5
    col = col + gaps[..., None] * color([1.0, 0.72, 0.34]) * 0.5
    P = np.stack([X, np.full_like(X, 330.0) + 0.0, Z + 25], -1).astype(np.float32)
    npz = os.path.join(d, "bg.npz")
    np.savez(npz, P=P, em=col.astype(np.float32))
    return npz


def scene_for(P, at, d, q, spp):
    npz = os.path.join(d, f"leaf.{q}.npz")
    np.savez(npz, P=P, **at)
    (occ, Fo), (tw, Ft) = shadows()
    o1, o2 = os.path.join(d, "occ.npz"), os.path.join(d, "twig.npz")
    np.savez(o1, V=occ, F=Fo)
    np.savez(o2, V=tw, F=Ft)
    black = {"Base Color": [0.0, 0.0, 0.0], "Roughness": 1.0, "Specular IOR Level": 0.0}
    hide = {"camera": False, "glossy": False, "diffuse": True, "transmission": False}
    cam = camera(P)
    params = {"k_tau": 1.0, "front": 0.10, "k_gloss": float(os.environ.get("S09_GLOSS", 1.0)), "rough": 0.42, "cos_min": 0.3, "ior": 1.45}
    return {
        "camera": cam,
        "meshes": [
            {"name": "leaf", "npz": npz, "shader_py": os.path.join(ROOT, "v2", "stills", "s09_shader.py"), "params": params},
            {"name": "occ", "npz": o1, "material": black, "visible": hide},
            {"name": "twig", "npz": o2, "material": black, "visible": hide},
            {"name": "bg", "npz": trees(d), "material": {"Base Color": [0.0, 0.0, 0.0], "Roughness": 1.0, "Emission Color": "em", "Emission Strength": 1.0}, "visible": {"diffuse": False, "shadow": False}},
        ],
        "lights": [
            {"name": "sun", "loc": SUN.tolist(), "target": [0, 0, 5.5], "size": [2.0, 2.0], "watts": 18000, "rgb": [1.0, 0.86, 0.66], "hide_in_gloss": True},
            {"name": "fill", "loc": [-6, 42, 16], "target": [0, 0, 6], "size": [46, 46], "watts": 15000, "rgb": [1.0, 0.84, 0.62], "hide_in_gloss": True},
            {"name": "sky", "loc": [-16, -24, 24], "target": [0, 0, 6], "size": [34, 34], "watts": 1000, "rgb": [0.78, 0.88, 1.0], "hide_in_gloss": True},
            {"type": "gradient", "name": "sheen", "loc": [-2.0, -8.0, 42.0], "target": [0, 0, 6], "size": [70, 70], "sigma": [20, 20], "L": float(os.environ.get("S09_SHEEN", 0.5)), "rgb": [0.9, 0.95, 1.0], "hide_in_diffuse": True},
        ],
        "world": [0.0005, 0.0007, 0.001],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "spp": spp,
    }


def still(q):
    tq = {"preview": "preview", "mid": "mid", "cand": "final"}[q]
    dens = {"preview": 0.5, "mid": 0.7, "cand": 1.0}[q]
    d = os.path.join(OUT, NAME)
    P, at, n, g = LF.leaf(dens)
    # the middle of the take
    P2 = Skin(P, n, g).vertices(phases(times(1)), FRAMES // 2)
    scene = scene_for(P2, at, d, q, {"preview": 96, "mid": 160, "final": 384})
    shoot(NAME, scene, tq, tag=q, develop=LOOK)


def develop_take(src, res_w, spp_note=""):
    """Linear frames -> what the film's take reader wants: f###.png, 16-bit, developed, with a jpg each and take.mp4. Atomic: a hidden folder, then the name."""
    from darkroom import develop, save_png

    dest = os.path.join(OUT, NAME + "_take_cand")
    tmp = os.path.join(OUT, f".{NAME}_take_cand.new")
    os.makedirs(tmp, exist_ok=True)
    fs = sorted(f for f in os.listdir(src) if f.startswith("take.linear_") and f.endswith(".npy"))
    frames = []
    for i, f in enumerate(fs):
        L = np.load(os.path.join(src, f)).astype(np.float32)
        im = develop(L, **{**LOOK, "seed": i + 1})
        save_png(os.path.join(tmp, f"f{i:03d}.png"), im)
        u8 = to8(im)
        cv2.imwrite(os.path.join(tmp, f"f{i:03d}.jpg"), u8, [cv2.IMWRITE_JPEG_QUALITY, 93])
        frames.append(cv2.resize(u8, (1920, 1080), interpolation=cv2.INTER_AREA) if u8.shape[1] > 1920 else u8)
    mp4(frames, os.path.join(tmp, "take.mp4"))
    json.dump(LOOK, open(os.path.join(tmp, "develop.json"), "w"))
    if os.path.isdir(dest):
        for f in os.listdir(dest):
            os.remove(os.path.join(dest, f))
        os.rmdir(dest)
    os.replace(tmp, dest)
    print(dest, len(fs), "frames")


def average(d, sub):
    fs = sorted(f for f in os.listdir(d) if f.startswith("take.linear_") and f.endswith(".npy"))
    if len(fs) != FRAMES * sub:
        raise SystemExit(f"{d}: {len(fs)} sub-exposures, expected {FRAMES * sub}")
    if sub == 1:
        return
    out = os.path.join(d, ".avg")
    os.makedirs(out, exist_ok=True)
    for i in range(FRAMES):
        a = sum(np.load(os.path.join(d, f)).astype(np.float32) for f in fs[i * sub : (i + 1) * sub]) / sub
        np.save(os.path.join(out, f"take.linear_{i:03d}.npy"), a.astype(np.float16))
    for f in fs:
        os.remove(os.path.join(d, f))
    for f in sorted(os.listdir(out)):
        os.replace(os.path.join(out, f), os.path.join(d, f))
    os.rmdir(out)


def take(mode):
    """low: a small sharp-shuttered take for judging the motion; final: 2560 x 1440 with sub-exposures."""
    dens = {"low": 0.35, "final": 1.0}[mode]
    sub = {"low": 1, "final": SUB}[mode]
    res = {"low": [1280, 720], "final": [2560, 1440]}[mode]
    spp = {"low": 48, "final": int(os.environ.get("S09_SPP", 64))}[mode]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    P, at, n, g = LF.leaf(dens)
    ts = times(sub)
    phi = phases(ts)
    sk = Skin(P, n, g)
    nv = P.shape[0] * P.shape[1]
    sp = os.path.join(d, f"wind.{mode}.npy")
    st = np.lib.format.open_memmap(sp, mode="w+", dtype=np.float32, shape=(len(ts), nv, 3))
    for i in range(len(ts)):
        st[i] = sk.vertices(phi, i).reshape(-1, 3)
    st.flush()
    del st
    print(f"{sp}: {len(ts)} x {nv} vertices, {os.path.getsize(sp) / 1e9:.2f} GB", flush=True)
    scene = scene_for(P, at, d, f"wind{mode}", {"preview": spp, "mid": spp, "final": spp})
    scene["deform"] = {"npy": sp, "vertex": ["leaf"]}
    if mode == "final":
        scene["denoise"] = bool(int(os.environ.get("S09_DENOISE", 0)))
    name = NAME + ("_wind" if mode == "final" else "_windlo")
    kit.looks = lambda: {name: {"move": {"frames": len(ts), "shutter": 0, "spp": spp, "res": res}}}
    # the renderer resumes by keeping the frames it finds: after a stopped run those are the old motion, spliced in with a jump. Start clean
    stale = os.path.join(OUT, name)  # where the frames wait while rendering; kit empties the _move_final folder itself
    if os.path.isdir(stale):
        for f in os.listdir(stale):
            if f.startswith("take.linear_"):
                os.remove(os.path.join(stale, f))
    os.environ["GEWU_MOVE"] = "final"
    out = shoot(name, scene, "final", develop=LOOK)
    average(out, sub)
    os.remove(sp)
    develop_take(out, res[0])
    if mode == "final":
        # the still is the middle of the take, so the two cannot disagree
        from darkroom import develop, save_png

        L = np.load(os.path.join(out, f"take.linear_{FRAMES // 2:03d}.npy")).astype(np.float32)
        np.save(os.path.join(d, "cand.linear.npy"), L)
        json.dump(LOOK, open(os.path.join(d, "cand.develop.json"), "w"))
        im = develop(L, **LOOK)
        save_png(os.path.join(d, "cand.png"), im)
        cv2.imwrite(os.path.join(d, "cand.jpg"), to8(im), [cv2.IMWRITE_JPEG_QUALITY, 96])


def main():
    args = sys.argv[1:]
    a = args[0] if args else "flat"
    if a == "flat":
        flat(float(args[1]) if len(args) > 1 else 0.5)
    elif a == "layout":
        layout()
    elif a == "still":
        still(args[1])
    elif a == "take":
        take(args[1])
    else:
        raise SystemExit("flat | layout | still preview|mid|cand | take low|final")


if __name__ == "__main__":
    main()
