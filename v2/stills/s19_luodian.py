"""Shot 19: mother-of-pearl inlay in black lacquer (黑漆嵌螺钿): bamboo on a round tray. The rolled rim of the tray is the arc.

    python3 -I v2/stills/s19_luodian.py look [preview|mid|final]
    python3 -I v2/stills/s19_luodian.py take [preview|mid|final]   12 frames: the light moves slowly and the colours run

Built like the real thing (compared with the pieces in ref/luodian; scales are estimates, the optics a simplification):
- each leaf and stem is its own piece of shell, cut with a blade and let into the lacquer: its growth lines run its own way and its
  colour is its own. So the colours break from piece to piece, with fine dark gaps and chipped corners;
- nacre's colour is interference: reflectance of a film, computed per vertex in three wavelengths from a thickness that varies with
  the growth lines, on a metal-like base; the angle follows the light. This is one film standing in for a real stack of tablets;
- veins are engraved (毛雕) after the inlay: many hairline V cuts with dark lacquer rubbed into them, the blade lifting at each end;
- old shell: white to grey along its streaks, dull where it is worn, with hair cracks and chipped edges;
- the lacquer is deep black, polished, old: a slow wave, hair scratches and a fine crackle, which the window shows.
The drawing is ours, after the bamboo inlays in the reference photographs; it is not a copy of any piece.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 9.0
R = 11.0
VIEW = view_dir(-90.0, 37.0)
DIST = 38.0
X0, X1, Y0, Y1 = -7.2, 7.2, 2.2, 11.6
SEED = 19
FRAMES = 12


def tray(X, Y):
    """A shallow tray with a rolled rim: flat floor, a small lip, the bead."""
    r = np.hypot(X, Y)
    bead = 0.09 * np.exp(-(((r - (R - 0.45)) / 0.34) ** 2))
    fall = -np.maximum(r - (R - 0.25), 0.0) ** 2 * 3.2
    lip = -0.06 * sstep(R - 1.3, R - 0.95, -r + 2 * R - 2 * R + r) * 0.0
    return bead + fall + lip


def leaf_poly(p, ang, L, w, rng):
    t = np.linspace(0, 1, 26)
    half = w * np.sin(np.pi * t**0.72) ** 0.9 * (1.0 + 0.04 * rng.normal(0, 1))
    bend = rng.normal(0, 0.07) * np.sin(np.pi * t) * L
    x = L * t
    upper = np.stack([x, half + bend], 1)
    lower = np.stack([x[::-1], (-half + bend)[::-1]], 1)
    pts = np.concatenate([upper, lower], 0)
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([p[0] + c * pts[:, 0] - s * pts[:, 1], p[1] + s * pts[:, 0] + c * pts[:, 1]], 1), (p, ang, L, bend)


def stem_poly(p0, p1, w0, w1):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-d[1], d[0]])
    return np.array([p0 + n * w0, p1 + n * w1, p1 - n * w1, p0 - n * w0])


def pieces(c):
    """A list of (polygon in cm, kind, extra)."""
    rng = np.random.default_rng(SEED)
    out = []
    # the culm: segments from lower left to upper right, each a separate strip with a gap at each node
    a = np.radians(24.0)
    d = np.array([np.cos(a), np.sin(a)])
    start = np.array([c[0] - 7.6, c[1] - 3.2])
    pos = 0.0
    nodes = []
    while pos < 13.2:
        seg = rng.uniform(2.3, 3.1)
        p0, p1 = start + d * pos, start + d * (pos + seg - 0.04)
        w = 0.17 - 0.006 * pos
        out.append((stem_poly(p0, p1, w * 0.98, w * 0.94), "stem", (p0, p1)))
        nodes.append(p1)
        pos += seg
    # a second culm behind, thinner
    a2 = np.radians(46.0)
    d2 = np.array([np.cos(a2), np.sin(a2)])
    s2 = np.array([c[0] + 0.6, c[1] - 4.6])
    pos = 0.0
    while pos < 8.2:
        seg = rng.uniform(1.8, 2.5)
        p0, p1 = s2 + d2 * pos, s2 + d2 * (pos + seg - 0.04)
        out.append((stem_poly(p0, p1, 0.1, 0.09), "stem", (p0, p1)))
        nodes.append(p1)
        pos += seg
    # sprays of leaves from the nodes; they hang away from the rim and cross each other
    for k, node in enumerate(nodes):
        if node[1] > c[1] + 3.0:
            continue
        # two sprays per node, one to each side: the real pieces are crowded, leaves over leaves
        for side in (-1.0, 1.0):
            tw = node + np.array([side * rng.uniform(0.3, 1.1), rng.uniform(-0.6, 0.2)])
            out.append((stem_poly(node, tw, 0.03, 0.018), "twig", (node, tw)))
            base = np.radians(rng.uniform(-115, -55)) + side * 0.3
            n = int(rng.integers(4, 7))
            for j in range(n):
                ang = base + (j - (n - 1) / 2) * rng.uniform(0.28, 0.46) + rng.normal(0, 0.07)
                L = rng.uniform(1.05, 2.0)
                w = L * rng.uniform(0.1, 0.14)
                poly, meta = leaf_poly(tw, ang, L, w, rng)
                out.append((poly, "leaf", meta))
    return out


def build(dens, c):
    pxcm = 290.0 * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    X, Y = np.meshgrid(X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)

    # two lines of small shell strips following the rim, as trays have
    ps = pieces(c)
    rng = np.random.default_rng(SEED + 2)
    for rr, wid, step in ((R - 1.02, 0.045, 0.62), (R - 1.2, 0.03, 0.34)):
        th = -0.75
        while th < 0.75:
            dth = step / rr * rng.uniform(0.9, 1.1)
            t = np.linspace(th, th + dth * 0.93, 12)
            ou = np.stack([(rr + wid) * np.sin(t), (rr + wid) * np.cos(t)], 1)
            inn = np.stack([(rr - wid) * np.sin(t), (rr - wid) * np.cos(t)], 1)
            ps.append((np.concatenate([ou, inn[::-1]], 0), "strip", None))
            th += dth

    lab = np.zeros(shape, np.int32)
    engrave = np.zeros(shape, np.uint8)
    rng2 = np.random.default_rng(SEED + 20)
    # draw back to front so that the later pieces cut the earlier: one shell over another does not occur, so the later simply wins
    for i, (poly, kind, meta) in enumerate(ps, start=1):
        ip = np.round((poly - [X0, Y0]) * pxcm * 16).astype(np.int32)
        cv2.fillPoly(lab, [ip], i, cv2.LINE_8, shift=4)
    # engraved afterwards, piece by piece: a line stops where its piece stops
    for i, (poly, kind, meta) in enumerate(ps, start=1):
        if kind not in ("leaf", "stem"):
            continue
        q0 = (poly - [X0, Y0]) * pxcm
        x0_, y0_ = max(int(q0[:, 0].min()) - 2, 0), max(int(q0[:, 1].min()) - 2, 0)
        x1_, y1_ = min(int(q0[:, 0].max()) + 3, nx), min(int(q0[:, 1].max()) + 3, ny)
        if x1_ <= x0_ or y1_ <= y0_:
            continue
        one = np.zeros((y1_ - y0_, x1_ - x0_), np.uint8)
        org = np.array([X0 + x0_ / pxcm, Y0 + y0_ / pxcm])
        if kind == "leaf":
            p, ang, L, bend = meta
            ca, sa = np.cos(ang), np.sin(ang)
            t = np.linspace(0.03, 0.97, 26)
            for off in (0.0, 0.16, -0.16, 0.33, -0.33, 0.52, -0.52, 0.72, -0.72):
                w = L * 0.11 * np.sin(np.pi * t**0.72) ** 0.9
                x = L * t
                yy = bend + off * w
                q = np.stack([p[0] + ca * x - sa * yy, p[1] + sa * x + ca * yy], 1)
                # the blade lifts: side veins start late and stop early, and their weight varies
                a0 = 0 if off == 0 else int(rng2.integers(2, 7))
                a1 = 26 if off == 0 else int(rng2.integers(17, 25))
                ie = np.round((q[a0:a1] - org) * pxcm * 16).astype(np.int32)
                cv2.polylines(one, [ie], False, 255 if off == 0 else int(rng2.uniform(70, 170)), max(1, int(round(0.0045 * pxcm))), cv2.LINE_AA, shift=4)
        else:
            p0, p1 = np.array(meta[0]), np.array(meta[1])
            d = (p1 - p0) / np.linalg.norm(p1 - p0)
            n = np.array([-d[1], d[0]])
            for off in (0.06, -0.05):
                q = np.stack([p0 + n * off + d * 0.08, p1 + n * off - d * 0.08], 0)
                ie = np.round((q - org) * pxcm * 16).astype(np.int32)
                cv2.polylines(one, [ie], False, 140, max(1, int(round(0.0045 * pxcm))), cv2.LINE_AA, shift=4)
        roi = engrave[y0_:y1_, x0_:x1_]
        keep_ = lab[y0_:y1_, x0_:x1_] == i
        roi[keep_] = np.maximum(roi[keep_], one[keep_])

    # --- each piece: a mask with a gap at the edge, chipped corners, its own growth lines and its own film
    mask0 = (lab > 0).astype(np.uint8)
    # a fine dark gap where two pieces meet
    edges = (lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))
    edge = blur(edges.astype(np.float32), max(0.9 * dens, 0.6))
    edge = np.clip(edge * 2.2, 0, 1)
    chip = fbm(shape, pxcm, 0.02, 0.22, 1.6, SEED + 3)
    dist = cv2.distanceTransform(mask0, cv2.DIST_L2, 3).astype(np.float32) / pxcm
    shell = sstep(0.0, 0.006, dist + 0.009 * chip - 0.002) * mask0
    n = len(ps) + 1
    rp = np.random.default_rng(SEED + 4)
    phi = rp.uniform(0, np.pi, n).astype(np.float32)
    off = rp.uniform(0, 100, n).astype(np.float32)
    mean = rp.uniform(300, 560, n).astype(np.float32)
    tone = rp.normal(0, 1, n).astype(np.float32)
    g = X * np.cos(phi[lab]) + Y * np.sin(phi[lab]) + off[lab]
    wob = 0.08 * fbm(shape, pxcm, 0.05, 0.8, 2.2, SEED + 5)
    lines = np.sin(2 * np.pi * (g + wob) / 0.034)
    bands = fbm(shape, pxcm, 0.35, 2.4, 2.8, SEED + 6)
    fine = fbm(shape, pxcm, 0.01, 0.06, 1.2, SEED + 7)
    film = mean[lab] + 22.0 * bands + 6.0 * lines + 1.2 * fine
    eng = blur(engrave.astype(np.float32) / 255.0, max(0.6 * dens, 0.45))

    # --- lacquer: black, a slow wave, hair scratches
    wave = fbm(shape, pxcm, 0.6, 4.0, 3.0, SEED + 8)
    black = mix(color([0.0028, 0.0026, 0.0026]), color([0.011, 0.008, 0.0065]), rank(wave) ** 2)
    crk_l = fbm(shape, pxcm, 0.05, 0.5, 2.0, SEED + 14)
    crackle = sstep(0.016, 0.0, np.abs(crk_l)) * sstep(0.35, 0.7, rank(fbm(shape, pxcm, 0.5, 3.0, 2.4, SEED + 15)))
    scr = np.zeros(shape, np.uint8)
    rs = np.random.default_rng(SEED + 9)
    for _ in range(int(240)):
        p = np.array([rs.uniform(0, nx), rs.uniform(0, ny)])
        a = rs.uniform(0, np.pi)
        L = rs.lognormal(np.log(0.9), 0.6) * pxcm
        q = p + L * np.array([np.cos(a), np.sin(a)])
        cv2.line(scr, tuple(np.int32(p)), tuple(np.int32(q)), int(rs.uniform(40, 120)), 1, cv2.LINE_AA)
    scratches = scr.astype(np.float32) / 255.0

    pale = mix(color([0.8, 0.78, 0.74]), color([0.94, 0.9, 0.86]), sstep(-1.5, 1.5, tone[lab] + 0.5 * bands))
    col = mix(black, pale, shell)
    col = mix(col, color([0.02, 0.018, 0.017]), (eng * 0.88 + edge * 0.7 * shell).clip(0, 1) * shell)
    dark = (eng * 0.88 + edge * 0.7 * shell).clip(0, 1) * shell
    metal = shell * (1.0 - 0.9 * eng) * 0.72
    rough = 0.1 + 0.05 * sstep(-1, 1, wave) + 0.14 * scratches + 0.2 * crackle
    rough = rough * (1 - shell) + shell * (0.13 + 0.05 * sstep(-1, 1, fine) + 0.18 * eng)
    # a shell piece sits proud or sunk by a hair, and tilts by a hair: each piece reflects on its own
    tx, ty = rp.normal(0, 0.02, n).astype(np.float32), rp.normal(0, 0.02, n).astype(np.float32)
    area = np.bincount(lab.ravel(), minlength=n).astype(np.float64) + 1
    cxs = (np.bincount(lab.ravel(), X.ravel(), minlength=n) / area).astype(np.float32)
    cys = (np.bincount(lab.ravel(), Y.ravel(), minlength=n) / area).astype(np.float32)
    tilt = np.clip(tx[lab] * (X - cxs[lab]) + ty[lab] * (Y - cys[lab]), -0.0035, 0.0035)
    # old shell has hair cracks running through a piece
    crk = fbm(shape, pxcm, 0.03, 0.7, 2.2, SEED + 10)
    cracks = sstep(0.022, 0.0, np.abs(crk)) * sstep(0.45, 0.75, rank(fbm(shape, pxcm, 0.3, 2.0, 2.4, SEED + 11)))
    h = tray(X, Y) + 0.0012 * wave - 0.00018 * scratches - 0.0006 * crackle * (1 - shell)
    h = h + shell * (0.0007 + 0.00008 * lines + 0.0002 * bands + tilt - 0.0035 * eng - 0.0009 * cracks)
    P = np.stack([X, Y, h], -1).astype(np.float32)
    film_a = (film * shell).astype(np.float32)
    dark = np.maximum(dark, cracks * shell * 0.7)
    # streaks of the shell: a piece is white here and grey there, along its own growth direction, and worn to a dull patch elsewhere
    streak = cv2.resize(fbm((max(ny // 14, 8), nx), pxcm, 0.03, 0.5, 1.6, SEED + 12), (nx, ny), interpolation=cv2.INTER_LINEAR)
    worn = sstep(0.55, 0.9, rank(fbm(shape, pxcm, 0.1, 0.9, 2.2, SEED + 13)))
    sheen = (0.62 + 0.3 * sstep(-1.6, 1.6, tone[lab]) + 0.14 * sstep(-1, 1, 1.4 * bands + 0.8 * streak) + 0.04 * lines) * (1 - 0.24 * worn)
    sheen = sheen.astype(np.float32)
    # most pieces are near white, a few flash with colour (as in the reference pieces)
    sat = (0.06 + 0.42 * rp.beta(1.0, 3.2, n))[lab].astype(np.float32)
    return P, black.astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), metal.astype(np.float32), film_a, shell.astype(np.float32), dark.astype(np.float32), sheen, sat


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "look"
    q = sys.argv[2] if len(sys.argv) > 2 else "preview"
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s19_luodian")
    os.makedirs(d, exist_ok=True)
    xx, yy = np.linspace(X0, X1, 500, dtype=np.float32), np.linspace(Y0, Y1, 500, dtype=np.float32)
    Xc, Yc = np.meshgrid(xx, yy)
    Pc = np.stack([Xc, Yc, tray(Xc, Yc)], -1)
    keep = np.hypot(Xc, Yc) < R + 0.15
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Xc.shape), y.reshape(Xc.shape)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.72) ** 2) + 10 * (~keep))
    c = (float(Xc.flat[k]), float(Yc.flat[k]))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=3.0, focus_point=focus)
    print("c", c, flush=True)
    P, Blk, Ro, Me, Fi, Sh, Dk, Sn, Sa = build(dens, c)
    develop = {"exposure": 0.0, "contrast": 1.28, "saturation": 1.05, "black": 0.001, "grain": 1.2, "sharpen": 0.3, "halation": 0.05, "glare": 0.004, "vignette": 0.4}

    def interference(cos_t):
        """Two-beam thin film per colour: reflectance of nacre in three wavelengths, pastel because a real stack mixes many orders.
        Base colour of a metal-like shell: the reflection takes this colour. Depends on the angle through cos_t."""
        n_shell = 1.62
        lam = np.array([620.0, 540.0, 460.0], np.float32)
        ph = 4.0 * np.pi * n_shell * Fi[..., None] * cos_t / lam
        return 1.0 - Sa[..., None] * (0.5 - 0.5 * np.cos(ph))

    def write_mesh(t):
        # the angle inside the film follows the light as it moves
        v = np.array(cam["loc"], float) - focus
        v /= np.linalg.norm(v)
        l = np.array([-34.0 + 22.0 * t, 30.0, 30.0])
        l /= np.linalg.norm(l)
        hv = (v + l) / np.linalg.norm(v + l)
        sin_i = np.sqrt(max(1.0 - hv[2] ** 2, 0.0))
        cos_t = float(np.sqrt(1.0 - (sin_i / 1.62) ** 2))
        col = mix(Blk, (interference(cos_t) * Sn[..., None]).astype(np.float32), Sh)
        col = mix(col, np.array([0.02, 0.018, 0.017], np.float32), Dk)
        npz = os.path.join(d, f"mesh.{q}.npz")
        np.savez(npz, P=P, col=np.clip(col, 0, 1).astype(np.float32), rough=Ro, metal=Me, spec=(0.035 + 0.46 * Sh).astype(np.float32))
        return npz

    def scene_at(t):
        npz = write_mesh(t)
        j = np.nanargmin(((x - (0.42 + 0.16 * t)) ** 2 + (y - 0.72) ** 2) + 10 * (~keep))
        lw, _ = reflect_light_loc(Pc.reshape(-1, 3)[j], np.array([0.0, 0.0, 1.0]), cam, 60.0)
        return {
            "camera": cam,
            "meshes": [{"name": "tray", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": "spec"}}],
            "lights": [
                {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": Pc.reshape(-1, 3)[j].tolist(), "size": [150, 90], "sigma": [40, 13], "L": 1.5, "rgb": [1.0, 0.97, 0.92]},
                {"name": "key", "loc": (focus + np.array([-34 + 22 * t, 30, 30])).tolist(), "target": focus.tolist(), "size": [14, 14], "watts": 20000, "rgb": [1.0, 0.96, 0.88], "hide_in_gloss": True},
            ],
            "world": [0.0, 0.0, 0.0],
            "diffuse_bounces": 2,
            "glossy_bounces": 3,
            "spp": {"preview": 64, "mid": 128, "final": 256},
        }

    if mode == "look":
        shoot("s19_luodian", scene_at(0.5), q, develop=develop)
        return
    for f in range(FRAMES):
        dv = dict(develop)
        dv["seed"] = 300 + f
        shoot(f"s19_luodian_take_{q}", scene_at(f / (FRAMES - 1)), q, develop=dv, tag=f"f{f:03d}")


main()
