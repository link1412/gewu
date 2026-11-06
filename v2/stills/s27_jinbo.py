"""Shot 27: a sheet of gold leaf (金箔) lying over a soft mound, its torn far edge the arc, the edge trembling in a breath.

    python3 -I v2/stills/s27_jinbo.py look|take [sketch|preview|mid|final]     (take: 8 frames, the edge moves)

Second version. The blind review of the first: "folded faces are big low-poly blocks, the bokeh is neat round dots, the floating flakes too dramatic". Compared 100% with goldleaf_03, 05, 07 (photographs, reference only): real leaf is not mirror facets,
it is a tissue: pale satin brass with long thin wrinkles in bundles and branches, a fine crinkle everywhere, and a torn, holed edge. So:
- the wrinkles are lines, not a triangulation: a slowly turning flow carries long ridges (roof-shaped, each with its own height, width and taper), branches leave them at an angle, smaller lines fill in; four size classes with a power law. Only a gentle underlying crumple (low Delaunay) stays;
- a fine directional crinkle and a grain are on top, at low height, and the material is satin (roughness about 0.3), so a wrinkle's flash spreads instead of reading as a mirror: this is also what removes the round bokeh dots;
- the edge is torn: multi-scale notches, tabs, pinholes clustered near it; it lifts and curls a little off the mound. It is the only thing that moves: leaf trembles at a breath;
- no flakes hang in the air. This replaces the first version's falling flakes: reported to the lead.
The background is the studio's grey-black. Scales are estimates from general knowledge and from the look of those photos, not measured.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from scipy.interpolate import LinearNDInterpolator

from kit import OUT, blur, color, fbm, frame_camera, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc

NAME = "s27_jinbo"
W = 12.0
EL = np.radians(20.0)
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)])
DIST = 42.0
SEED = 2711
FRAMES = 8
FOCUS = np.array([0.0, 2.6, -0.2])
RU, RV = 13.5, 30.0
U0, U1, V0, V1 = -9.5, 9.5, -9.0, 7.0


def dome(U, V):
    return -(U**2) / (2 * RU) - (V - 0.5) ** 2 / (2 * RV)


def rim_of(U):
    return 4.6 - U**2 / 34.0


def wrinkles(shape, pxcm, seed):
    """Height of a net of fold lines. Each class: (lines per cm2, mean length cm, ridge half width cm, height cm). Long ones first; small ones often start on an existing line."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    field = fbm((96, 96), 96 / 22.0, 1.5, 16.0, 3.4, seed + 1)
    field2 = fbm((96, 96), 96 / 22.0, 0.6, 3.0, 2.2, seed + 2)
    theta_f = (field * 1.3 + 0.28 * field2).astype(np.float32)

    def theta(xp, yp):
        ix = np.clip((xp / nx * 95).astype(int), 0, 95)
        iy = np.clip((yp / ny * 95).astype(int), 0, 95)
        return theta_f[iy, ix]

    out = np.zeros(shape, np.float32)
    anchors = np.empty((0, 3), np.float32)  # points on already drawn lines: x, y, heading
    for per, Lm, wd, hgt in ((0.34, 7.5, 0.05, 0.026), (2.6, 2.4, 0.026, 0.012), (22.0, 0.8, 0.012, 0.0048), (110.0, 0.25, 0.0065, 0.0017)):
        if wd * pxcm < 0.55:  # below a pixel in this quality; skip so previews stay light
            continue
        n = int(area * per)
        px, py = rng.uniform(0, nx, n), rng.uniform(0, ny, n)
        off = np.zeros(n)
        if len(anchors):  # branches: start on a bigger line, leave it at an angle
            br = rng.random(n) < 0.55
            pick = rng.integers(0, len(anchors), n)
            px[br], py[br] = anchors[pick[br], 0], anchors[pick[br], 1]
            off[br] = rng.choice([-1, 1], br.sum()) * rng.uniform(0.5, 1.2, br.sum())
        cross = rng.random(n) < 0.3
        off[cross] += np.pi / 2  # some lines run across the bundle
        L = rng.lognormal(np.log(Lm), 0.6, n) * pxcm
        steps = 14
        pts = np.zeros((n, steps, 2), np.float32)
        pts[:, 0, 0], pts[:, 0, 1] = px, py
        jit = rng.normal(0, 0.25, n)
        for s in range(1, steps):
            a = theta(pts[:, s - 1, 0], pts[:, s - 1, 1]) + off + jit + rng.normal(0, 0.09, n)
            pts[:, s, 0] = pts[:, s - 1, 0] + np.cos(a) * L / (steps - 1)
            pts[:, s, 1] = pts[:, s - 1, 1] + np.sin(a) * L / (steps - 1)
        # labels: every segment with its own height; taper to zero at both ends of a line
        lab = np.zeros(shape, np.int32)
        ampl = rng.lognormal(0, 0.55, n) * rng.choice([1.0, 1.0, 1.0, -0.65], n)
        vals = [0.0]
        P = np.round(pts * 16).astype(np.int32)
        k = 1
        for i in range(n):
            for s in range(steps - 1):
                cv2.line(lab, tuple(int(c) for c in P[i, s]), tuple(int(c) for c in P[i, s + 1]), k, 1, cv2.LINE_8, shift=4)
                tp = np.sin(np.pi * (s + 0.5) / (steps - 1)) ** 0.7
                vals.append(ampl[i] * tp)
                k += 1
        vals = np.array(vals, np.float32)
        mask = (lab == 0).astype(np.uint8)
        d, lb = cv2.distanceTransformWithLabels(mask, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        z = mask == 0
        pick = np.zeros(lb.max() + 2, np.int32)
        pick[lb[z]] = lab[z]
        a_ = vals[pick[lb]]
        out += hgt * a_ * np.exp(-d.astype(np.float32) / pxcm / wd)
        anchors = pts[:: max(1, n // 3000), :: 3].reshape(-1, 2)
        anchors = np.c_[anchors, np.zeros(len(anchors))].astype(np.float32)
    return out


def crumple(shape, pxcm, seed, octaves):
    """Low, slow underlying crumple. Coarse grid, interpolated, then blurred, so that no triangle shows."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    w, h = nx / pxcm, ny / pxcm
    res = 36.0
    gy, gx = int(h * res), int(w * res)
    yy, xx = np.mgrid[0:gy, 0:gx].astype(np.float32)
    xx, yy = (xx + 0.5) / res, (yy + 0.5) / res
    out = np.zeros((gy, gx), np.float32)
    for spacing, slope in octaves:
        n = max(int((w + 2 * spacing) * (h + 2 * spacing) / spacing**2), 8)
        pts = np.stack([rng.uniform(-spacing, w + spacing, n), rng.uniform(-spacing, h + spacing, n)], 1)
        z = rng.normal(0, slope * spacing, n)
        out += LinearNDInterpolator(pts, z, fill_value=0.0)(xx, yy).astype(np.float32)
    out = cv2.GaussianBlur(out, (0, 0), 1.6)
    return cv2.resize(out, (nx, ny), interpolation=cv2.INTER_CUBIC)


def sheet(dens):
    """The material of the leaf: everything but the trembling of the edge."""
    pxcm = 170.0 * dens
    nx, ny = int((U1 - U0) * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    u = U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = V1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm  # rows run -y: normals up
    U, V = np.meshgrid(u, v)

    h = crumple(shape, pxcm, SEED, ((1.5, 0.07), (0.55, 0.075), (0.22, 0.05))) + wrinkles(shape, pxcm, SEED + 10)
    # the fine crinkle, directional: a stretched noise sampled along two near-perpendicular ways, ridged
    tb = fbm((1024, 1024), 1.0, 1.4, 14.0, 1.6, SEED + 3)
    c1 = cv2.remap(tb, np.mod(U * 44 + V * 8 + 300, 1023).astype(np.float32), np.mod(V * 210 - U * 40 + 300, 1023).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    c2 = cv2.remap(tb, np.mod(V * 44 + 70, 1023).astype(np.float32), np.mod(U * 210 + 90, 1023).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    crinkle = np.abs(c1) * 0.0058 + np.abs(c2) * 0.0032
    # where the leaf was pressed or stretched the crinkle changes in strength; large areas are nearly quiet
    strength = 0.35 + 0.9 * rank(fbm(shape, pxcm, 0.5, 3.5, 2.8, SEED + 4))
    grain = fbm(shape, pxcm, 0.004, 0.014, 1.1, SEED + 5)
    h = h + crinkle * strength + 0.00035 * grain

    # the torn far edge: slow bays, sharp notches, small tabs; a tear is a line, so the notches are narrow, and never the same
    rng = np.random.default_rng(SEED + 6)
    n_ = int((U1 - U0) * 400)
    uu = np.linspace(U0, U1, n_)
    edge = 0.14 * cv2.GaussianBlur(rng.normal(0, 1, n_).astype(np.float32)[None], (0, 0), 180.0)[0] * np.sqrt(2 * np.pi * 180 ** 2) ** 0.5
    edge = edge + 0.02 * cv2.GaussianBlur(rng.normal(0, 1, n_).astype(np.float32)[None], (0, 0), 14.0)[0] * 7.0
    slow_rim = rim_of(U) + np.interp(U, uu, edge).astype(np.float32)  # lift and tremble follow this, not the notches: a notch has no shadow behind it
    for _ in range(46):
        c_, w_, d_ = rng.uniform(U0, U1), rng.lognormal(np.log(0.05), 0.7), rng.lognormal(np.log(0.09), 0.8)
        edge = edge - d_ * np.exp(-np.abs(uu - c_) / w_)
    for _ in range(14):  # tabs
        c_, w_, d_ = rng.uniform(U0, U1), rng.lognormal(np.log(0.08), 0.5), rng.lognormal(np.log(0.09), 0.5)
        edge = edge + d_ * np.exp(-(((uu - c_) / w_) ** 2))
    rim = rim_of(U) + np.interp(U, uu, edge).astype(np.float32)
    # the fine torn fringe: wrinkles decide where it tore last
    fine = 0.03 * fbm(shape, pxcm, 0.006, 0.12, 1.5, SEED + 7)
    d_rim = rim + fine - V  # > 0 is inside
    alpha = sstep(-0.006, 0.006, d_rim)
    # pinholes: clusters, more near the edge
    ph = rs_pinholes(shape, pxcm, sstep(2.6, 0.0, d_rim), SEED + 8)
    alpha = alpha * (1.0 - ph)

    # lift and curl near the edge; a few places it stands off the mound
    d_slow = slow_rim - V
    lift = 0.2 * np.exp(-np.maximum(d_slow, 0) / 0.7) * rank(fbm(shape, pxcm, 1.2, 6.0, 3.0, SEED + 9))
    z0 = dome(U, V) + h + lift
    # Past the tear alpha is 0 but the grid goes on. A ray grazing that invisible crinkled surface crosses it more often than Cycles' 16 transparent bounces allow and ends black: a dark thread in the background that trembles with the edge. So the grid drops away steeply behind the tear, where a ray passing over the edge cannot reach it; what can be seen is untouched.
    z0 = z0 - 3.0 * np.maximum(-d_rim - 0.05, 0.0)
    # the tremble of a breath, at each frame z0 + amp * sin(...): phase runs along the edge
    amp = sstep(2.2, 0.05, d_slow) * 0.1 * (0.4 + 0.6 * rank(fbm(shape, pxcm, 0.7, 3.5, 2.6, SEED + 12)))
    phase = (U * 0.85 + 1.4 * fbm(shape, pxcm, 1.0, 5.0, 3.0, SEED + 13)).astype(np.float32)

    # colour: 22-carat, pale and greenish where thin, warmer in doubled folds; barely varying
    tone_ = rank(fbm(shape, pxcm, 0.5, 4.0, 2.6, SEED + 14))
    col = mix(color([0.97, 0.69, 0.27]), color([1.0, 0.71, 0.23]), tone_)
    # roughness: satin; pressed flats a bit smoother; crinkled areas duller (micro relief under a pixel)
    rough = 0.17 + 0.09 * sstep(0.3, 1.0, strength) + 0.03 * grain
    P = np.stack([U, V, z0], -1).astype(np.float32)
    return P, amp.astype(np.float32), phase, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.08, 1).astype(np.float32), alpha.astype(np.float32)


def rs_pinholes(shape, pxcm, near, seed):
    """Small holes in the leaf. Lognormal radius, about 0.01-0.05 cm, clustered."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    clus = sstep(0.72, 0.95, rank(fbm(shape, pxcm, 0.12, 0.8, 2.3, seed + 1)))
    n = int(area * 45)
    xs, ys = rng.integers(0, nx, n), rng.integers(0, ny, n)
    keep = rng.random(n) < (0.08 + 0.92 * near[ys, xs]) * clus[ys, xs]
    xs, ys = xs[keep], ys[keep]
    out = np.zeros(shape, np.uint8)
    for x_, y_ in zip(xs, ys):
        m = rng.integers(4, 8)
        a = np.sort(rng.uniform(0, 6.283, m))
        r = rng.lognormal(np.log(0.02), 0.55) * pxcm * rng.uniform(0.5, 1.0, m)
        p = np.stack([x_ + r * np.cos(a), y_ + r * np.sin(a) * rng.uniform(0.5, 1.0)], 1)
        cv2.fillPoly(out, [np.round(p * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    return blur(out.astype(np.float32) / 255.0, max(0.5, 0.4))


def scene_for(q, t, d, cam, base):
    P0, amp, phase, col, rough, alpha = base
    P = P0.copy()
    # one breath across the take: slow and uneven
    P[..., 2] += amp * np.sin(2.0 * np.pi * (0.55 * t + 0.09) + phase) * (0.5 + 0.5 * np.sin(np.pi * t))
    fp = os.path.join(d, f"sheet.{q}.npz")
    np.savez(fp, P=P, col=col, rough=rough, alpha=alpha)
    pm = FOCUS + np.array([0.0, -1.5, 0.0])
    lw, _ = reflect_light_loc(pm, np.array([0.0, -0.1, 1.0]), cam, 70.0)
    lights = [
        {"type": "gradient", "name": "scrim", "loc": lw.tolist(), "target": pm.tolist(), "size": [150, 100], "sigma": [34, 14], "L": 1.5, "rgb": [1.0, 0.95, 0.88]},
        {"type": "gradient", "name": "room", "loc": (FOCUS + np.array([0.0, 26.0, 62.0])).tolist(), "target": FOCUS.tolist(), "size": [190, 150], "sigma": [62, 34], "L": 0.42, "rgb": [1.0, 0.95, 0.86]},
        {"name": "key", "loc": [-44.0, 26.0, 18.0], "target": [0.0, 0.0, 0.0], "size": [18, 18], "watts": 16000, "rgb": [1.0, 0.92, 0.8]},
    ]
    gray = 0.0065
    return {
        "camera": cam,
        "meshes": [{"name": "sheet", "npz": fp, "material": {"Base Color": "col", "Metallic": 1.0, "Roughness": "rough", "Alpha": "alpha"}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "sky": {"top": [gray, gray, gray], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.55, "seed": 27},
        "env": {"window": 1.0, "ceil": 0.6, "wall": 0.09, "floor": 0.05, "strip": 0.7, "win_az": -30.0},
        "diffuse_bounces": 1,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 220},
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "look"
    q = sys.argv[2] if len(sys.argv) > 2 else "preview"
    dens = {"sketch": 0.35, "preview": 0.55, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    uu, vv = np.linspace(U0, U1, 400, dtype=np.float32), np.linspace(V0, V1, 400, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = np.stack([Uc, Vc, dome(Uc, Vc)], -1)
    keep = Vc < rim_of(Uc)
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=7.5, focus_point=FOCUS)
    develop = {"exposure": 0.4, "contrast": 1.26, "saturation": 1.02, "black": 0.0012, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "glare": 0.005, "vignette": 0.3}
    base = sheet(dens)
    bq = "preview" if q == "sketch" else q
    if mode == "look":
        shoot(NAME, scene_for(q, 0.5, d, cam, base), bq, develop=develop, tag=q)
    else:
        for f in range(FRAMES):
            t = f / (FRAMES - 1)
            dv = dict(develop)
            dv["seed"] = 100 + f
            # the film reads _take_final: a candidate goes to _take_cand and is renamed only after it has passed a look at 100%
            shoot(f"{NAME}_take_{'cand' if q == 'final' else q}", scene_for(q, t, d, cam, base), bq, develop=dv, tag=f"f{f:03d}")
    fp = os.path.join(d, f"sheet.{q}.npz")
    if os.path.exists(fp):
        os.remove(fp)


main()
