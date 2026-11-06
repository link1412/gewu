"""Shot 30: oiled huanghuali (黄花梨) with its "ghost faces" (鬼脸): rings swirling around knots. The curve of a turned body is the arc.

    python3 -I v2/stills/s30_huali.py [preview|mid|final]

Built like the real thing (scales are estimates from general knowledge, not measured):
- growth rings as level lines of one field: the distance from the pith plus a slow wander, bent around each knot, so that the
  figure closes into eyes the way wood does;
- a thin dark latewood line in each ring, wider honey earlywood between them;
- open pores (棕眼): dark dashes about a millimetre long that follow the grain, drawn by carrying noise along it;
- oil and a long polish: a clear coat over a fine grain relief, so that the sheen breaks a little across the rings.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import Profile, fit_arc, patch, project, reflect_light_loc, turned, view_dir

W = 9.0
RB = 11.5
A_ = np.radians(np.arange(-70, 71, 5.0))
PROF = Profile(np.stack([RB * np.cos(A_), RB * np.sin(A_)], 1).tolist(), sigma=0.2)
VIEW = view_dir(0.0, -28.0)
SEED = 30


def carry(noise, tx, ty, length_px, steps=10):
    """Line-integral convolution: average the noise along the unit field (tx, ty): streaks that follow the grain."""
    ny, nx = noise.shape
    X, Y = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    out = noise.copy()
    px, py = X.copy(), Y.copy()
    qx, qy = X.copy(), Y.copy()
    h = float(length_px) / steps
    w = 1.0
    for _ in range(steps):
        px = px + cv2.remap(tx, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * h
        py = py + cv2.remap(ty, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * h
        qx = qx - cv2.remap(tx, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * h
        qy = qy - cv2.remap(ty, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * h
        out = out + cv2.remap(noise, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) + cv2.remap(noise, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        w += 2.0
    return out / w


FIG = {"ring": 0.135, "wander": 1.0, "wander2": 0.22, "arch": 1.0, "late": 0.72, "jitter": 0.035, "streak": 0.1, "streak_h": 0.00016, "pore": 0.92, "pore_n": 0.9993, "knots": [(0.35, -0.2, 0.44), (-2.9, 0.75, 0.3), (3.3, 0.5, 0.24), (-1.2, -1.75, 0.22), (-4.6, -0.8, 0.26)]}


def rings(U, V, c0, pxcm, fig=FIG):
    """The phase of the rings (one unit per ring) on a coarse grid, for the same figure at every quality."""
    rng = np.random.default_rng(SEED)
    wander = fbm(U.shape, pxcm, 0.5, 7.0, 3.0, SEED + 1)
    wander2 = fbm(U.shape, pxcm, 0.15, 1.5, 2.6, SEED + 2)
    # plain-sawn: cathedral curves from a pith below, running sideways across the frame
    base = (V - c0[1] + fig["arch"] * 0.9 * np.sin((U - c0[0]) * 0.22 + 0.6)) / fig["ring"] + fig["arch"] * 0.14 * (U - c0[0]) ** 2 / fig["ring"] * 0.09
    phase = base + fig["wander"] * wander + fig["wander2"] * wander2
    # the knots: each pulls the rings into closed eyes around it
    for kx, ky, s in fig["knots"]:
        cx, cy = c0[0] + kx + rng.normal(0, 0.05), c0[1] + ky + rng.normal(0, 0.05)
        dx, dy = U - cx, V - cy
        ang = np.arctan2(dy, dx)
        r = np.sqrt((dx * 1.0) ** 2 + (dy * 1.35) ** 2)
        r = r * (1.0 + 0.16 * np.cos(ang * 2 + rng.uniform(0, 6)) + 0.09 * np.cos(ang * 3 + rng.uniform(0, 6)))
        influence = np.exp(-((r / (s * 2.5)) ** 2))
        local = r / (s * 0.22)
        phase = phase * (1.0 - influence) + (local + float(rng.uniform(0, 9))) * influence
    return phase


def build(dens, box, c0, v_line, surf=None, fig=FIG):
    """v_line: where the turned lines go, or None. surf(U, V, h) -> P: the shape to lay this wood on, a turned body by default."""
    u0, u1, v0, v1 = box
    pxcm = 340.0 * dens
    nx, ny = int((u1 - u0) * pxcm), int((v1 - v0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    u = u0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = v0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)

    # the figure on a fixed grid, interpolated: the composition must not change with the quality
    g = 110.0
    gw, gh = int((u1 - u0) * g), int((v1 - v0) * g)
    ug = u0 + (np.arange(gw, dtype=np.float32) + 0.5) / g
    vg = v0 + (np.arange(gh, dtype=np.float32) + 0.5) / g
    Ug, Vg = np.meshgrid(ug, vg)
    pg = rings(Ug, Vg, c0, g, fig).astype(np.float32)
    pg = cv2.GaussianBlur(pg, (0, 0), 0.8)
    phi = cv2.remap(pg, (U - u0) * g - 0.5, (V - v0) * g - 0.5, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # grain direction: along the rings, on the fixed grid
    gy, gx = np.gradient(pg)
    n = np.hypot(gx, gy) + 1e-6
    txg, tyg = (-gy / n).astype(np.float32), (gx / n).astype(np.float32)
    txg, tyg = cv2.GaussianBlur(txg, (0, 0), 2.0), cv2.GaussianBlur(tyg, (0, 0), 2.0)
    n = np.hypot(txg, tyg) + 1e-6
    txg, tyg = txg / n, tyg / n
    tx = cv2.resize(txg, (nx, ny), interpolation=cv2.INTER_LINEAR)
    ty = cv2.resize(tyg, (nx, ny), interpolation=cv2.INTER_LINEAR)

    # --- rings
    jitter = fig["jitter"] * fbm(shape, pxcm, 0.05, 0.4, 2.2, SEED + 3)
    f = np.mod(phi + jitter, 1.0)
    late = sstep(0.62, 0.9, f) * sstep(1.0, 0.94, f)  # the dark line, sharp on the far side
    body = rank(blur(phi * 0.0 + fbm(shape, pxcm, 0.25, 2.5, 2.6, SEED + 4), 1.0))
    # ring-to-ring difference: some years are darker
    ring_id = np.floor(phi + jitter).astype(np.int32)
    tbl = np.random.default_rng(SEED + 5).normal(0, 1, 4096).astype(np.float32)
    year = tbl[np.mod(ring_id, 4096)]

    # --- fibres and pores, carried along the grain
    w = np.random.default_rng(SEED + 6).standard_normal(shape, dtype=np.float32)
    streak = carry(blur(w, max(0.9 * dens, 0.6)), tx, ty, 0.1 * pxcm)
    streak = streak / (streak.std() + 1e-6)
    w2 = (np.random.default_rng(SEED + 7).random(shape, dtype=np.float32) > fig["pore_n"]).astype(np.float32)
    pores = carry(blur(w2, max(1.1 * dens, 0.6)), tx, ty, 0.07 * pxcm, steps=8)
    pores = np.clip(pores / (np.percentile(pores, 99.7) + 1e-6), 0, 1)
    pores = sstep(0.18, 0.7, pores)

    # --- colour: linear; honey, red-brown bands, dark lines
    honey = mix(color([0.66, 0.30, 0.07]), color([0.82, 0.44, 0.12]), body)
    amber = mix(color([0.4, 0.15, 0.03]), color([0.52, 0.21, 0.045]), body)
    t = sstep(-0.9, 1.0, year + 0.35 * fbm(shape, pxcm, 0.1, 0.7, 2.2, SEED + 8))
    col = mix(honey, amber, t)
    col = mix(col, color([0.065, 0.024, 0.009]), late * (fig["late"] + 0.2 * sstep(-1, 1, year)))
    col = col * (1.0 + fig["streak"] * streak[..., None])
    col = mix(col, color([0.03, 0.013, 0.007]), pores * fig["pore"])

    # --- surface: a hair of relief across the rings and in the pores, under the coat
    h = -0.00035 * late + fig["streak_h"] * streak - 0.0011 * pores + 0.0012 * fbm(shape, pxcm, 0.6, 4.0, 3.0, SEED + 9)
    # two turned lines (线脚) cut on the lathe: they make it a thing that was made
    if v_line is not None:
        g1, g2 = np.exp(-(((V - v_line) / 0.028) ** 2)), np.exp(-(((V - v_line - 0.17) / 0.018) ** 2))
        groove = np.maximum(g1, 0.7 * g2)
        h = h - 0.026 * groove
        col = mix(col, col * 0.3, groove[..., None] ** 2 * 0.8)
    rough = 0.3 + 0.08 * sstep(-1, 1, streak) + 0.25 * pores
    P = surf(U, V, h) if surf else turned(PROF, U, V, h)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.45, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s30_huali")
    os.makedirs(d, exist_ok=True)
    uu, vv = np.linspace(-14, 14, 500, dtype=np.float32), np.linspace(0.5, PROF.L - 0.2, 500, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = turned(PROF, Uc, Vc)
    r, z, nr, nz = PROF.at(Vc)
    th = Uc / np.maximum(r, 0.05)
    keep = (np.cos(th) * nr * VIEW[0] + np.sin(th) * nr * VIEW[1] + nz * VIEW[2]) > -0.03
    cam, sag = fit_arc(Pc[keep], VIEW, W, 40.0)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Uc.shape), y.reshape(Uc.shape)
    i = np.nanargmin(((x - 0.47) ** 2 + (y - 0.76) ** 2) + 10 * (~keep))
    c0 = np.array([float(Uc.flat[i]), float(Vc.flat[i])])
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.62) ** 2) + 10 * (~keep))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, 40.0, aperture_mm=6.0, focus_point=focus)
    box = patch(PROF, cam, (-14, 14), (0.5, PROF.L - 0.2))
    print("box", box, "knot centre", c0, flush=True)
    g = np.nanargmin(((x - 0.5) ** 2 + (y - 0.575) ** 2) + 10 * (~keep))
    vg = float(Vc.flat[g])
    P, C, Ro = build(dens, box, c0, vg)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)
    j = np.nanargmin(((x - 0.42) ** 2 + (y - 0.56) ** 2) + 10 * (~keep))
    pw = Pc.reshape(-1, 3)[j]
    nw = np.array([np.cos(th.flat[j]) * nr.flat[j], np.sin(th.flat[j]) * nr.flat[j], nz.flat[j]])
    lw, _ = reflect_light_loc(pw, nw, cam, 50.0)
    lights = [
        {"type": "gradient", "name": "sheen", "loc": lw.tolist(), "target": pw.tolist(), "size": [150, 60], "sigma": [34, 2.6], "L": 1.0, "rgb": [1.0, 0.95, 0.87]},
        {"name": "key", "loc": (focus + np.array([-6, -44, 22])).tolist(), "target": focus.tolist(), "size": [20, 20], "watts": 26000, "rgb": [1.0, 0.92, 0.8], "hide_in_gloss": True},
        {"name": "fill", "loc": (focus + np.array([34, 18, 2])).tolist(), "target": focus.tolist(), "size": [30, 30], "watts": 2800, "rgb": [1.0, 0.95, 0.9], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "wood", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.4, "Coat Weight": 0.9, "Coat Roughness": 0.16, "Subsurface Weight": 0.25, "Subsurface Radius": [1.0, 0.5, 0.2], "Subsurface Scale": 0.05}}],
        "lights": lights,
        "world": [0.001, 0.0008, 0.0006],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s30_huali", scene, q, develop={"exposure": 0.0, "contrast": 1.3, "saturation": 1.03, "black": 0.002, "grain": 1.2, "sharpen": 0.3, "halation": 0.03, "glare": 0.003})


if __name__ == "__main__":
    main()
