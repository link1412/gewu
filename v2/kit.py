"""Shared tools for the stills: fields in physical units (cm), and shoot() to run the studio and the darkroom."""

import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER = os.environ.get("GEWU_BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender" if sys.platform == "darwin" else "blender")
GPU_API = os.environ.get("GEWU_GPU_API", "METAL" if sys.platform == "darwin" else "OPTIX")  # METAL, OPTIX, CUDA, HIP or ONEAPI
OUT = os.path.join(ROOT, "out", "v2")


# --- noise ------------------------------------------------------------------------------------------------------
def fbm(shape, pxcm, lo, hi, beta=2.0, seed=0):
    """Band-limited fractal noise, wavelengths from lo to hi cm, unit variance."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    fx = np.fft.rfftfreq(nx, 1.0 / pxcm)
    fy = np.fft.fftfreq(ny, 1.0 / pxcm)
    k = np.sqrt(fx[None, :] ** 2 + fy[:, None] ** 2)
    k[0, 0] = 1e-6
    amp = k ** (-beta / 2.0)
    # soft band edges so that no ringing shows at the limits
    amp *= np.exp(-((k * lo) ** 2)) * (1.0 - np.exp(-((k * hi) ** 2)))
    w = rng.standard_normal(shape, dtype=np.float32)
    f = np.fft.irfft2(np.fft.rfft2(w) * amp, s=shape).astype(np.float32)
    return (f - f.mean()) / (f.std() + 1e-9)


def warp(f, dx, dy):
    """Domain warp: dx, dy in pixels."""
    ny, nx = f.shape
    X, Y = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    return cv2.remap(f.astype(np.float32), X + dx.astype(np.float32), Y + dy.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def blur(f, sigma_px):
    return cv2.GaussianBlur(f.astype(np.float32), (0, 0), float(sigma_px), borderType=cv2.BORDER_REFLECT)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def rank(f):
    """Map a field to its percentile in [0, 1], fast (so that thresholds mean area fractions)."""
    lo, hi = np.percentile(f[::4, ::4], [0.1, 99.9])
    t = np.linspace(lo, hi, 1024)
    h, _ = np.histogram(f[::4, ::4], bins=1024, range=(lo, hi))
    c = np.cumsum(h).astype(np.float64)
    c /= c[-1]
    return np.interp(f, t, c).astype(np.float32)


def caps(shape, pxcm, per_cm2, rmin, rmax, seed=0, mask=None, bins=6, slope=-2.0):
    """Union of random spherical caps (height in cm): grape-like crust, blisters, pits."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    out = np.zeros(shape, np.float32)
    edges = np.geomspace(rmin, rmax, bins + 1)
    w = (edges[:-1] * edges[1:]) ** (slope / 2.0 + 1.0)
    w = w / w.sum()
    for i in range(bins):
        r = float(np.sqrt(edges[i] * edges[i + 1]))
        n = int(area * per_cm2 * w[i])
        if n < 1:
            continue
        x = rng.integers(0, nx, n)
        y = rng.integers(0, ny, n)
        if mask is not None:
            keep = rng.random(n) < mask[y, x]
            x, y = x[keep], y[keep]
            if len(x) == 0:
                continue
        seeds = np.ones(shape, np.uint8)
        seeds[y, x] = 0
        d = cv2.distanceTransform(seeds, cv2.DIST_L2, 5) / pxcm
        c = np.sqrt(np.maximum(r * r - d * d, 0.0)).astype(np.float32)
        out = np.maximum(out, c)
    return out


def mix(a, b, t):
    """Blend colors (rows, cols, 3) or scalars by a mask."""
    t = np.asarray(t)
    if np.ndim(a) == 1 or np.ndim(b) == 1 or (np.ndim(a) == 3 or np.ndim(b) == 3):
        t = t[..., None] if t.ndim == 2 else t
    return a * (1.0 - t) + b * t


def color(rgb):
    return np.array(rgb, np.float32)


# --- camera -----------------------------------------------------------------------------------------------------
def frame_camera(target, view_dir, width_cm, dist_cm, aperture_mm=None, focus_point=None, roll=0.0, shift=(0.0, 0.0)):
    """A camera dist_cm from target looking along -view_dir, with width_cm across the frame at the target."""
    target = np.array(target, float)
    d = np.array(view_dir, float)
    d = d / np.linalg.norm(d)
    loc = target + d * dist_cm
    lens = 36.0 * dist_cm / width_cm
    cam = {"loc": loc.tolist(), "target": target.tolist(), "lens_mm": lens, "roll": roll, "shift": list(shift)}
    if aperture_mm:
        fp = np.array(focus_point if focus_point is not None else target, float)
        cam["aperture_mm"] = aperture_mm
        cam["focus_distance"] = float(np.dot(loc - fp, d))
    return cam


# --- the room, the sky and the move: everything that a real shoot has and a render on black has not -------------------
def _cam_axes(cam):
    loc, tgt = np.array(cam["loc"], float), np.array(cam["target"], float)
    back = loc - tgt
    back /= np.linalg.norm(back)
    up0 = np.array([0.0, 0.0, 1.0]) if abs(back[2]) < 0.99999 else np.array([0.0, 1.0, 0.0])
    # Blender's to_track_quat("-Z", "Y") keeps the camera's Y near world Z
    right = np.cross(up0, back)
    right /= np.linalg.norm(right)
    up = np.cross(back, right)
    roll = np.radians(cam.get("roll", 0.0))
    if roll:
        right, up = right * np.cos(roll) + up * np.sin(roll), -right * np.sin(roll) + up * np.cos(roll)
    return right, up, back


def room_env(path, cam, spec=None):
    """The room seen in reflections, an equirectangular float image written to `path`. Built in the camera's frame, so 'behind the camera' stays there:
    a dim ceiling, dark walls with a slow unevenness, a tall window behind the camera with mullions, a long warm strip, black cards, the dark shape of camera and
    photographer on the axis. All radiances are in scene units; a glaze at normal incidence shows 4% of them, a rim at grazing nearly all."""
    sp = {"ceil": 0.35, "wall": 0.05, "floor": 0.018, "window": 3.0, "win_az": -38.0, "win_el": 24.0, "win_w": 34.0, "win_h": 50.0, "strip": 1.2, "strip_az": 62.0, "seed": 3, "tint": [1.0, 0.985, 0.96]}
    sp.update(spec or {})
    h, w = 1024, 2048
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])  # row 0 = up
    # Blender's equirect, measured: u = 0.5 - atan2(y, x) / 2pi (+X at the centre of the image, +Y a quarter to the left)
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    r, u, b = [np.array(v, np.float32) for v in _cam_axes(cam)]
    dr, du, db = d @ r, d @ u, d @ b  # right, up, towards the camera's back
    az = np.degrees(np.arctan2(dr, db))  # 0 looking back past the camera, + to the camera's right
    el = np.degrees(np.arcsin(np.clip(du, -1, 1)))
    rng_f = fbm((h // 4, w // 4), 1.0, 6.0, 200.0, beta=2.6, seed=sp["seed"])
    rng_f = cv2.resize(rng_f, (w, h), interpolation=cv2.INTER_CUBIC)
    L = sp["wall"] * np.exp(0.55 * rng_f)
    t = sstep(10.0, 70.0, el)
    L = L * (1 - t) + sp["ceil"] * np.exp(0.3 * rng_f) * t
    t = sstep(-8.0, -45.0, el)
    L = L * (1 - t) + sp["floor"] * t
    tint = np.ones((h, w, 3), np.float32) * np.array(sp["tint"], np.float32)
    E = L[..., None] * tint
    # the window, soft at the edges by lens blur of what is seen in a rough glaze; mullions divide it in 2 x 3 panes
    if sp["window"]:
        x = (az - sp["win_az"]) / (sp["win_w"] / 2)
        y = (el - sp["win_el"]) / (sp["win_h"] / 2)
        panes = sstep(1.0, 0.93, np.abs(x)) * sstep(1.0, 0.95, np.abs(y))
        panes = panes * sstep(0.022, 0.05, np.abs(x)) * sstep(0.018, 0.04, np.abs(y - 0.33)) * sstep(0.018, 0.04, np.abs(y + 0.33))
        grad = 0.75 + 0.35 * y
        E = E + (sp["window"] * panes * grad)[..., None] * np.array([0.92, 0.97, 1.08], np.float32)
    if sp["strip"]:
        x = (az - sp["strip_az"]) / 5.0
        y = (el - 8.0) / 42.0
        E = E + (sp["strip"] * np.exp(-(x**2)) * sstep(1.0, 0.6, np.abs(y)))[..., None] * np.array([1.06, 0.97, 0.86], np.float32)
    # the camera on its stand, the photographer: a dark shape on the axis
    cam_d = np.hypot(az / 13.0, (el + 3.0) / 22.0)
    E = E * (0.15 + 0.85 * sstep(0.75, 1.15, cam_d))[..., None]
    np.save(path, E.astype(np.float32))
    return path


def sky_mesh(path, cam, spec):
    """The sky of the picture: a hand-painted canvas backdrop, far behind everything, out of focus, in the camera's frame. Written as an emissive grid.
    spec: top, glow (linear RGB), y0 (where the glow is centred, 0 = top of frame .. 1 = bottom), h (its half height in frame heights), mottle (0..1), x0 (glow centre across)."""
    D = spec.get("dist", 2400.0)
    right, up, back = _cam_axes(cam)
    loc = np.array(cam["loc"], float)
    wf = 36.0 / cam["lens_mm"] * D  # frame width at the plane, seen from the camera
    hf = wf * 9.0 / 16.0
    nu, nv = 513, 289
    ext = spec.get("extent", 7.0)  # far beyond the frame, because rims reflect it at wide angles
    # a grid dense in the frame, sparse outside
    su = np.sinh(np.linspace(-1, 1, nu) * np.arcsinh(ext * 8.0)) / 8.0
    sv = np.sinh(np.linspace(-1, 1, nv) * np.arcsinh(ext * 8.0)) / 8.0
    fx, fy = np.meshgrid(su, sv)  # fx, fy in frame widths/heights from the frame centre, +fy up
    P = loc - back * D + right[None, None] * (fx * wf)[..., None] + up[None, None] * (fy * hf)[..., None]
    y = 0.5 - fy  # 0 at top of frame
    x = 0.5 + fx
    top = np.array(spec["top"], np.float32)
    glow = np.array(spec.get("glow", spec["top"]), np.float32)
    y0, hh, x0 = spec.get("y0", 0.5), spec.get("h", 0.42), spec.get("x0", 0.5)
    dist = np.hypot((x - x0) * 0.62, y - y0) / hh
    t = np.exp(-(dist**1.7))[..., None]
    col = top * (1 - t) + glow * t
    # painted mottling: the slow clouds of a dabbed canvas, in a fine grid of the frame
    if spec.get("mottle", 0.5):
        m = 1024
        f = fbm((m // 2, m), 1.0, 22.0, 700.0, beta=3.0, seed=spec.get("seed", 5))
        g = fbm((m // 2, m), 1.0, 8.0, 90.0, beta=2.4, seed=spec.get("seed", 5) + 1)
        u_ = np.clip((x / 1.6 + 0.2) * (m - 1), 0, m - 1).astype(np.float32)
        v_ = np.clip((y / 1.6 + 0.2) * (m / 2 - 1), 0, m / 2 - 1).astype(np.float32)
        ff = cv2.remap(0.8 * f + 0.25 * g, u_, v_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        amp = spec["mottle"]
        col = col * np.exp(amp * 0.42 * ff)[..., None]
    np.savez(path, P=P.astype(np.float32), col=col.astype(np.float32))
    return path


def table_mesh(path, cam, spec):
    """A real surface under a dish or a bowl, at height z: the object stands on something, the 'sky' of a picture from above is the table going out of focus.
    spec: z, kind (linen | wood | paper | stone), rgb (albedo), rough, thread (cm, linen), angle (degrees, grain or weave), seed;
    ao {center [x, y], r, w, depth}: the contact shadow a real foot and wall would make, painted into the albedo because the meshes are only the part in frame (a stand-in)."""
    z = float(spec["z"])
    right, up, back = _cam_axes(cam)
    loc = np.array(cam["loc"], float)
    tgt = np.array(cam["target"], float)
    dist = np.linalg.norm(loc - tgt)
    w_ = 36.0 / cam["lens_mm"] * dist
    h_ = w_ * 9.0 / 16.0
    hits = []
    for sx, sy in ((-0.62, -0.62), (0.62, -0.62), (-0.62, 0.62), (0.62, 0.62), (0, 0.62), (0, -0.62)):
        p = tgt + right * sx * w_ + up * sy * h_
        d = p - loc
        if d[2] >= -1e-3:
            raise SystemExit("table_mesh: a frame corner looks above the horizon of the table; use sky instead")
        q = loc + d * (z - loc[2]) / d[2]
        hits.append(q[:2])
    hits = np.array(hits)
    x0, y0 = hits.min(0)
    x1, y1 = hits.max(0)
    area = (x1 - x0) * (y1 - y0)
    pxcm = min(1920.0 / w_, np.sqrt(spec.get("max_verts", 7e6) / area))
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    x = x0 + np.arange(nx, dtype=np.float32) / pxcm
    y = y0 + np.arange(ny, dtype=np.float32) / pxcm
    X, Y = np.meshgrid(x, y)
    sd = spec.get("seed", 11)
    shape = (ny, nx)
    a = np.radians(spec.get("angle", 8.0))
    U, V = X * np.cos(a) + Y * np.sin(a), -X * np.sin(a) + Y * np.cos(a)
    rgb = np.array(spec.get("rgb", [0.1, 0.1, 0.1]), np.float32)
    kind = spec.get("kind", "linen")
    if kind == "linen":
        t = spec.get("thread", 0.07)
        wob = 0.5 * t * fbm(shape, pxcm, 0.4, 5.0, 2.8, sd)
        pu, pv = (U + wob) / t, (V + np.roll(wob, 17, 1)) / t
        iu, iv = np.floor(pu), np.floor(pv)
        over = np.mod(iu + iv, 2.0) < 1.0  # plain weave: which thread is on top
        fu, fv = pu - iu - 0.5, pv - iv - 0.5
        # a slub: each thread has its own thickness and shade along its length
        rng = np.random.default_rng(sd)
        ut = rng.normal(0, 1, 4096).astype(np.float32)
        vt = rng.normal(0, 1, 4096).astype(np.float32)
        su = ut[iu.astype(np.int64) % 4096]
        sv = vt[iv.astype(np.int64) % 4096]
        slub = fbm(shape, pxcm, t * 3, t * 40, 2.2, sd + 1)
        hu = np.sqrt(np.maximum(1 - (2 * fv) ** 2, 0.0)) * np.cos(fu * np.pi)
        hv = np.sqrt(np.maximum(1 - (2 * fu) ** 2, 0.0)) * np.cos(fv * np.pi)
        weave = np.where(over, hv, hu)
        wr = fbm(shape, pxcm, 0.6, 14.0, 3.0, sd + 2)  # the cloth lies in slow wrinkles
        H = t * 0.34 * weave * (1 + 0.2 * slub) + 0.05 * wr
        shade = np.where(over, sv, su)
        col = rgb * (1 + 0.14 * shade + 0.10 * slub + 0.1 * fbm(shape, pxcm, 1.0, 12.0, 2.6, sd + 3))[..., None] * (0.72 + 0.28 * np.clip(weave, 0, 1))[..., None]
        rough = np.full(shape, spec.get("rough", 0.86), np.float32)
    elif kind == "wood":
        wob = 1.6 * fbm(shape, pxcm, 1.5, 22.0, 3.0, sd) + 0.25 * fbm(shape, pxcm, 0.3, 3.0, 2.6, sd + 1)
        rings = (V * 2.3 + 2.2 * wob) + 0.05 * U
        ring = 0.5 + 0.5 * np.sin(rings * 2.0 * np.pi / 3.0)
        fine = fbm((ny // 4 + 1, nx), pxcm, 0.02, 0.5, 1.6, sd + 2)
        fine = cv2.resize(fine, (nx, ny), interpolation=cv2.INTER_LINEAR)
        pores = sstep(1.3, 2.3, fine)
        H = 0.004 * fbm(shape, pxcm, 0.5, 8.0, 3.0, sd + 3) - 0.006 * pores
        col = rgb * (0.72 + 0.36 * ring + 0.12 * fine)[..., None] * (1 - 0.5 * pores)[..., None]
        rough = np.clip(spec.get("rough", 0.34) + 0.08 * fbm(shape, pxcm, 0.6, 9.0, 2.4, sd + 4) + 0.25 * pores, 0.08, 0.9).astype(np.float32)
    elif kind == "paper":
        H = 0.012 * fbm(shape, pxcm, 0.03, 0.8, 2.0, sd) + 0.05 * fbm(shape, pxcm, 1.0, 16.0, 3.0, sd + 1)
        col = rgb * (1 + 0.05 * fbm(shape, pxcm, 0.03, 0.4, 1.8, sd + 2) + 0.06 * fbm(shape, pxcm, 0.8, 10.0, 2.6, sd + 3))[..., None]
        rough = np.full(shape, spec.get("rough", 0.9), np.float32)
    else:  # stone: a honed dark slate
        H = 0.006 * fbm(shape, pxcm, 0.05, 1.5, 2.2, sd) + 0.02 * fbm(shape, pxcm, 1.5, 18.0, 3.0, sd + 1)
        col = rgb * (1 + 0.18 * fbm(shape, pxcm, 0.03, 2.0, 2.0, sd + 2) + 0.2 * fbm(shape, pxcm, 2.0, 24.0, 2.8, sd + 3))[..., None]
        rough = np.clip(spec.get("rough", 0.42) + 0.12 * fbm(shape, pxcm, 0.5, 8.0, 2.4, sd + 4), 0.12, 0.9).astype(np.float32)
    if spec.get("ao"):
        ao = spec["ao"]
        cx, cy = ao.get("center", [0.0, 0.0])
        d_ = np.maximum(np.hypot(X - cx, Y - cy) - ao["r"], 0.0)
        k = 1.0 - ao.get("depth", 0.85) * (0.6 * np.exp(-d_ / (0.22 * ao["w"])) + 0.4 * np.exp(-d_ / ao["w"]))
        col = col * k[..., None]
    P = np.stack([X, Y, z + H], -1).astype(np.float32)
    np.savez(path, P=P, col=np.clip(col, 0.0, 1.0).astype(np.float32), rough=rough)
    print(f"[table] {kind} {nx} x {ny} = {nx * ny / 1e6:.1f} M vertices", flush=True)
    return path


def camera_path(cam, lights, mv, n):
    """A real move: per-frame camera and lights. mv, all optional, s runs -0.5 .. +0.5 over the take:
    dolly: fraction of the camera distance travelled towards the target; truck [x, y]: travel in frame widths; orbit [az, el]: degrees about the pivot;
    pivot: 'focus' (default) or a point; roll: degrees; rack: cm the focus plane moves towards the camera; zoom: fraction of focal length;
    turntable {pt, axis, deg}: the object turns on a table (the camera and the lights turn the other way, which gives the same picture, but only if there is nothing else in it: everything else turns too);
    spin {pt, axis, deg, meshes}: these meshes really turn, each frame, and everything else stays. meshes: a list of names, or {"except": [names]}. See _take and studio_bpy.take;
    lights {name: [dx, dy, dz]}: a light travels this far, in cm."""
    loc0, tgt0 = np.array(cam["loc"], float), np.array(cam["target"], float)
    right, up, back = _cam_axes(cam)
    dist = np.linalg.norm(loc0 - tgt0)
    width = 36.0 / cam["lens_mm"] * dist
    fd = cam.get("focus_distance")
    fp0 = loc0 - back * fd if fd else tgt0
    pivot = np.array(mv["pivot"], float) if isinstance(mv.get("pivot"), list) else fp0

    def rot(v, axis, deg):
        a = np.radians(deg)
        axis = np.array(axis, float) / np.linalg.norm(axis)
        return v * np.cos(a) + np.cross(axis, v) * np.sin(a) + axis * axis.dot(v) * (1 - np.cos(a))

    out = []
    for i in range(n):
        s = (i / max(n - 1, 1) - 0.5) * mv.get("span", 1.0)
        loc, tgt, fp = loc0.copy(), tgt0.copy(), fp0.copy()
        if mv.get("orbit"):
            az, el = mv["orbit"]
            for ang, axis in ((az * s, up), (el * s, right)):
                loc = pivot + rot(loc - pivot, axis, ang)
                tgt = pivot + rot(tgt - pivot, axis, ang)
        if mv.get("truck"):
            d = (right * mv["truck"][0] + up * mv["truck"][1]) * width * s
            loc, tgt = loc + d, tgt + d
        if mv.get("dolly"):
            loc = loc + (tgt - loc) * mv["dolly"] * s
        f = {"loc": loc.tolist(), "target": tgt.tolist(), "roll": cam.get("roll", 0.0) + mv.get("roll", 0.0) * s, "lens_mm": cam["lens_mm"] * (1.0 + mv.get("zoom", 0.0) * s)}
        if mv.get("spin"):
            f["spin_deg"] = mv["spin"]["deg"] * s
        ls = {}
        if mv.get("turntable"):
            tt = mv["turntable"]
            pt = np.array(tt["pt"], float)
            ang = -tt["deg"] * s
            f["loc"] = (pt + rot(loc - pt, tt["axis"], ang)).tolist()
            f["target"] = (pt + rot(tgt - pt, tt["axis"], ang)).tolist()
            fp = pt + rot(fp - pt, tt["axis"], ang)
            for l in lights:
                ls[l["name"]] = {"loc": (pt + rot(np.array(l["loc"], float) - pt, tt["axis"], ang)).tolist(), "target": (pt + rot(np.array(l.get("target", [0, 0, 0]), float) - pt, tt["axis"], ang)).tolist()}
        for name, d in mv.get("lights", {}).items():
            l = next(x for x in lights if x["name"] == name)
            base = ls.get(name, {"loc": l["loc"], "target": l.get("target", [0, 0, 0])})
            ls[name] = {"loc": (np.array(base["loc"], float) + np.array(d, float) * s).tolist(), "target": (np.array(base["target"], float) + np.array(d, float) * s * mv.get("light_target", 0.0)).tolist()}
        if ls:
            f["lights"] = ls
        if fd:
            view = np.array(f["target"], float) - np.array(f["loc"], float)
            view /= np.linalg.norm(view)
            f["focus_distance"] = float(np.dot(fp - np.array(f["loc"], float), view) - mv.get("rack", 0.0) * s)
        out.append(f)
    return out


def looks():
    p = os.path.join(ROOT, "v2", "looks.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def _dress(cfg, name, d, develop):
    """Add what v2/looks.json says for this shot: the painted sky, the room in reflections, the lens. A script can set the same keys itself."""
    lk = looks().get(name.split("_take_")[0], {})
    cam = cfg["camera"]
    if cam.get("aperture_mm") and "blades" not in cam:
        cam["blades"] = lk.get("blades", 9)
    gain = 2.0 ** (develop or {}).get("exposure", 0.0)
    sk = lk.get("sky", cfg.get("sky"))  # looks.json has the last word: it is the film's palette
    cfg.pop("sky", None)
    if sk:
        spec = dict(sk)
        for k in ("top", "glow"):
            if k in spec:
                spec[k] = [c / gain for c in spec[k]]
        p = sky_mesh(os.path.join(d, "sky.npz"), cam, spec)
        cfg["meshes"] = list(cfg.get("meshes", [])) + [
            {"name": "sky", "npz": p, "material": {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}, "visible": {"diffuse": False, "shadow": False, "transmission": sk.get("in_transmission", True)}}
        ]
    tb = lk.get("table", cfg.get("table"))
    if tb:
        p = table_mesh(os.path.join(d, "table.npz"), cam, tb)
        cfg["meshes"] = list(cfg.get("meshes", [])) + [{"name": "table", "npz": p, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": tb.get("spec", 0.35)}}]
    cfg.pop("table", None)
    en = lk.get("env", cfg.get("env"))
    if en is not None and en is not False:
        spec = dict(en) if isinstance(en, dict) else {}
        p = spec.get("npy") or room_env(os.path.join(d, "env.npy"), cam, spec)  # a shot outdoors brings its own sky, in world directions
        cfg["env"] = {"npy": p, "diffuse": spec.get("diffuse", False), "transmission": spec.get("transmission", True)}
    else:
        cfg.pop("env", None)
    return lk


# --- shooting ---------------------------------------------------------------------------------------------------
def _run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(args)[:200]}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout


def _render_local(cfg, d, tag):
    cfg["out"] = os.path.join(d, f"{tag}.linear")
    cfg["gpu_api"] = GPU_API
    jp = os.path.join(d, f"{tag}.scene.json")
    json.dump(cfg, open(jp, "w"), indent=1)
    log = os.path.join(d, f"{tag}.log")
    with open(log, "w") as f:
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "-P", os.path.join(ROOT, "v2", "studio_bpy.py"), "--", jp], stdout=f, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise SystemExit(f"blender failed\n{open(log).read()[-3000:]}")
    if cfg.get("frames"):  # a take: its frames go to where the caller wants them
        to = cfg.get("fetch_to", d)
        os.makedirs(to, exist_ok=True)
        if os.path.abspath(to) != os.path.abspath(d):
            for f in os.listdir(d):
                if f.startswith(f"{tag}.linear_") and f.endswith(".npy"):
                    os.replace(os.path.join(d, f), os.path.join(to, f))
        return to
    return cfg["out"] + ".npy"


def _take(name, cfg, lk, move, develop, q):
    """Render a real move. GEWU_MOVE=check: first and last frame, small, to see that the move shows no edge of a mesh. preview: every 3rd frame, small. final: all frames, 1080p. GEWU_ENDS=1 with final: only the first and last frame, to compare with the film."""
    mv = lk.get("move")
    if not mv:
        raise SystemExit(f"{name}: no move in v2/looks.json")
    cut = json.load(open(os.path.join(ROOT, "v2", "cut.json")))["shots"]
    length = next((s["len"] for s in cut if s["src"] == name), 12)
    n = mv.get("frames", length + 3)
    path = camera_path(cfg["camera"], cfg.get("lights", []), mv, n)
    if cfg.get("deform"):  # a stack of displacements for one mesh, see studio_bpy._deform_setup; check and preview take its frames by their place in the whole take
        for i, f in enumerate(path):
            f["deform_i"] = i
            if cfg["deform"].get("vertex"):
                f["seed"] = i + 1  # sub-exposures to be averaged must not share their noise
            if cfg["deform"].get("spp"):
                f["spp"] = cfg["deform"]["spp"][i]  # a fast frame splits its samples over many sub-exposures, a still one does not
    if move == "check" or os.environ.get("GEWU_ENDS"):
        cfg["only"] = [0, len(path) - 1]  # the whole path stays in the scene: with only the two ends, the shutter would blur across the whole move
    elif move == "preview":
        path = path[:: max(1, n // 4)]
    res = tuple(mv["res"]) if mv.get("res") else {"check": (960, 540), "preview": (640, 360), "final": (1920, 1080)}[move]
    d = os.path.join(OUT, f"{name}_move_{'final' if move == 'final' else 'preview'}")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    cfg.update(res=list(res), frames=path, fetch_to=d, shutter=mv.get("shutter", 0.5), fresh=not os.environ.get("GEWU_MOVE_RESUME"))  # GEWU_MOVE_RESUME=1 keeps the frames of an interrupted run: only when the scene is the same
    if mv.get("spin"):
        cfg["spin"] = mv["spin"]
    if move != "final":
        cfg["spp"] = min(cfg["spp"], 96)
    else:
        cfg["spp"] = mv.get("spp", cfg["spp"])
    t = time.time()
    _render_local(cfg, os.path.join(OUT, name), "take")
    json.dump(develop or {}, open(os.path.join(d, "develop.json"), "w"))
    print(f"[{name}] move {move}: {len(path)} frames in {time.time() - t:.0f} s -> {d}")
    # contact: first, last at 960
    from darkroom import develop as dev

    fs = sorted(x for x in os.listdir(d) if x.endswith(".npy"))
    if not fs:
        raise SystemExit("no frames came back")
    a = dev(np.load(os.path.join(d, fs[0])).astype(np.float32), **(develop or {}))
    b = dev(np.load(os.path.join(d, fs[-1])).astype(np.float32), **(develop or {}))
    im = np.hstack([cv2.resize(a, (960, 540), interpolation=cv2.INTER_AREA), cv2.resize(b, (960, 540), interpolation=cv2.INTER_AREA)])
    cv2.imwrite(os.path.join(d, "ends.jpg"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    return d


def shoot(name, scene, q="preview", develop=None, tag=None):
    """Render scene (dict) and develop it. q: 'preview' 960x540, 'mid' 1280x720, 'final' 2560x1440."""
    from darkroom import develop as dev, save_png

    res = {"preview": (960, 540), "mid": (1280, 720), "final": (2560, 1440)}[q]
    spp = {"preview": 64, "mid": 128, "final": 384}[q]
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    tag = tag or q
    cfg = dict(scene)
    cfg.update(res=list(res), spp=scene.get("spp", {}).get(q, spp) if isinstance(scene.get("spp"), dict) else spp)
    cfg["camera"] = dict(cfg["camera"])
    lk = _dress(cfg, name, d, develop)
    if lk.get("dev"):
        develop = {**(develop or {}), **lk["dev"]}
    move = os.environ.get("GEWU_MOVE")  # preview | check | final: render this shot's move from v2/looks.json instead of a still
    if move:
        return _take(name, cfg, lk, move, develop, q)
    t = time.time()
    linear = _render_local(cfg, d, tag)
    L = np.load(linear)
    print(f"[{name}] render {time.time() - t:.0f} s, {res[0]}x{res[1]} @ {cfg['spp']} spp; linear p50 {np.median(L):.4f} p99 {np.percentile(L, 99):.3f}")
    img = dev(L, **(develop or {}))
    json.dump(develop or {}, open(os.path.join(d, f"{tag}.develop.json"), "w"))  # the film develops the linear image again
    p = os.path.join(d, f"{tag}.png")
    save_png(p, img)
    # an 8-bit copy for looking at
    cv2.imwrite(p[:-4] + ".jpg", (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(f"[{name}] {p[:-4]}.jpg")
    return p
