"""Shot 16: a lychee cut through, frame-filling: a thin crimson crust is the arc, below it glassy white flesh in soft lobes.

    python3 -I v2/stills/s60_lizhi.py [flat|preview|mid|final]


So beauty comes before botany here. All sizes are by eye.
Rebuild, against ref/lychee/commons2/thumb_Litchi_chinensis_Luc_Viatour.jpg (looked at, not used):
- crust: rounded polygonal tubercles of unequal size (Voronoi cells, each a dome with a small tip and an ochre fleck), not a lattice; a smooth pink cut wall on the inside. The inner glow of the crust is a stand-in: an emission of a third of its colour;
- flesh: broad radial pleats meeting in sharp creases, faint juice-sac striae, patches of fine membrane wrinkle. The white hair lines and the shard-like glints are gone: the wet look is now one long soft light bent by the folds;
- flesh: two layers. Below, painted light, not a rendered volume: an emission per vertex, peach under the crust, cream and milk within, with membranes in it, some blurred for those deeper down. Above, a real
  shell of glass (IOR 1.38) with the lobes and wrinkles as its relief: it refracts the paint and reflects the lights, and that is where the wet, glassy look and the small glints come from. Glass over paint
  stands in for a scattering jelly: nothing is absorbed or scattered inside it;
- the small lights are hidden from diffuse rays, so that they only ever make glints;
- the lobes are larger and cleaner than in a real aril.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, view_dir

NAME = "s60_lizhi"
SEED = 60
W, EL, DIST = 2.3, 72.0, 9.0
R = 1.8  # the fruit's outer radius, cm; the crown of the arc is at (0, R)
CRUST = 0.2  # how deep the crust band runs in from the rim, cm
X0, X1, Y0, Y1 = -1.42, 1.42, 0.42, 1.9
G = 150.0  # px/cm of the fixed grid for everything large: the composition must not change with the quality
L = 1000.0  # px/cm of the fixed grid the membranes are drawn on

# pleats of flesh, radial and long: angle on the rim (radians from the crown), radial position, half-length, half-width, height. Placed by eye, unequal.
PLEATS = [(-1.02, 1.05, 0.62, 0.30, 0.13), (-0.66, 1.18, 0.62, 0.27, 0.16), (-0.27, 1.14, 0.70, 0.34, 0.18), (0.14, 1.2, 0.6, 0.24, 0.15), (0.47, 1.1, 0.68, 0.33, 0.18), (0.88, 1.12, 0.58, 0.26, 0.14), (1.2, 0.98, 0.6, 0.28, 0.11), (-0.5, 0.56, 0.42, 0.34, 0.1), (0.2, 0.52, 0.44, 0.38, 0.11), (0.82, 0.5, 0.4, 0.3, 0.09)]
LOBES = [(r * np.sin(a), r * np.cos(a), l, w, H, a) for a, r, l, w, H in PLEATS]
# the same domes seen deeper, smaller and off to the side: only ever seen blurred
DEEP = [(-0.95, 1.1, 0.34, 0.3), (-0.3, 1.32, 0.3, 0.22), (0.38, 1.17, 0.26, 0.2), (0.62, 1.32, 0.34, 0.2), (1.08, 1.0, 0.3, 0.3), (-0.55, 0.92, 0.32, 0.26), (0.18, 0.92, 0.34, 0.28), (-1.0, 0.62, 0.3, 0.28), (0.95, 0.7, 0.28, 0.24)]


def low(shape, lo, hi, b, seed):
    """Noise from the fixed grid, for anything that should stay put between preview and final."""
    f = fbm((int((Y1 - Y0) * G), int((X1 - X0) * G)), G, lo, hi, b, seed).astype(np.float32)
    f = cv2.resize(f, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    # interpolation leaves kinks at the old grid's lines, which a mirror surface shows as a comb
    return cv2.GaussianBlur(f, (0, 0), 1.2 * shape[1] / ((X1 - X0) * G))


def draw(lines, warpx, warpy):
    """Lines given as (points in cm, width in px of the fixed grid, brightness along the line); drawn on the fixed grid, bent by the same warp as the domes."""
    h, w = int((Y1 - Y0) * L), int((X1 - X0) * L)
    canvas = np.zeros((h, w), np.uint8)
    for pts, wd, val in lines:
        p = np.round((pts - [X0, Y0]) * L * 16).astype(np.int32)
        for i in range(len(p) - 1):
            v = int(255 * val[i])
            if v > 4:
                cv2.line(canvas, tuple(int(a) for a in p[i]), tuple(int(a) for a in p[i + 1]), v, max(1, int(round(wd[i]))), cv2.LINE_AA, shift=4)
    m = cv2.GaussianBlur(canvas.astype(np.float32) / 255.0, (0, 0), 0.7)
    mx = (warpx - X0) * L - 0.5
    my = (warpy - Y0) * L - 0.5
    return cv2.remap(m, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def strength(n, rng, gaps=True):
    """Brightness along a line of n points: it swells, thins and fades out."""
    t = np.arange(n, dtype=np.float32) / max(n - 1, 1)
    v = 0.62 + 0.3 * np.sin(t * rng.uniform(5, 12) + rng.uniform(0, 6)) + 0.14 * np.sin(t * rng.uniform(16, 34) + rng.uniform(0, 6))
    if gaps:
        v = v * sstep(0.1, 0.6, 0.5 + 0.5 * np.sin(t * rng.uniform(3, 8) + rng.uniform(0, 6)) + 0.45)
    return np.clip(v * np.minimum(sstep(0, 0.12, t), sstep(1, 0.85, t)), 0, 1)


def arcs(domes, rng, each, fr, wmax):
    out = []
    for dome in domes:
        cx, cy, a, b = dome[:4]
        for _ in range(int(rng.integers(*each))):
            f = rng.uniform(*fr)
            a0 = rng.uniform(-0.6, 3.6)
            t = np.linspace(a0, a0 + rng.uniform(0.8, 2.8), 90)
            wob = 0.018 * np.sin(t * rng.uniform(3, 7) + rng.uniform(0, 6)) + 0.006 * np.sin(t * rng.uniform(13, 29) + rng.uniform(0, 6))
            pts = np.stack([cx + (f * a + wob) * np.cos(t), cy + (f * b + wob) * np.sin(t)], 1)
            val = strength(len(t), rng)
            out.append((pts, 1.0 + rng.uniform(0.3, 1.0) * wmax * val, val * rng.uniform(0.6, 1.0)))
    return out


def threads(rng, count):
    """Fine threads that run in from under the crust and wander down, across the domes."""
    out = []
    for _ in range(count):
        th = rng.uniform(np.pi / 2 - 1.0, np.pi / 2 + 1.0)
        r_ = R - CRUST - rng.uniform(0.0, 0.12)
        p = np.array([r_ * np.cos(th), r_ * np.sin(th)])
        ang = th + np.pi + rng.normal(0, 0.4)
        pts = [p]
        for _ in range(int(rng.integers(16, 70))):
            ang += rng.normal(0, 0.12)
            pts.append(pts[-1] + 0.014 * np.array([np.cos(ang), np.sin(ang)]))
        pts = np.array(pts)
        val = strength(len(pts), rng)
        out.append((pts, 1.0 + rng.uniform(0, 0.4) * val, val * rng.uniform(0.25, 0.65)))
    return out


def radial_streaks(r, th, rng):
    """Juice sacs: faint streaks along the radius."""
    s = rng.standard_normal((90, 1500), dtype=np.float32)
    s = cv2.GaussianBlur(s, (0, 0), sigmaX=1.2, sigmaY=9.0)
    s = s / s.std()
    my = (R - r) / 1.5 * 90.0
    mx = (th - np.pi / 2 + 1.3) / 2.6 * 1500.0
    return cv2.remap(s, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def flesh(X, Y, r, th, pxcm, wander):
    shape = X.shape
    rng = np.random.default_rng(SEED)
    Xw = X + 0.05 * low(shape, 0.6, 1.4, 2.4, SEED + 20)
    Yw = Y + 0.05 * low(shape, 0.6, 1.4, 2.4, SEED + 21)
    k = 0.012
    acc = np.zeros(shape, np.float32)
    best = np.full(shape, -9.0, np.float32)
    second = np.full(shape, -9.0, np.float32)
    lit = np.zeros(shape, np.float32)
    for i, (cx, cy, a, b, H, ang) in enumerate(LOBES):
        # along the radius (long), across it (short); the pleat bends a little as it runs
        rad_x, rad_y = np.sin(ang), np.cos(ang)
        along = (Xw - cx) * rad_x + (Yw - cy) * rad_y
        across = (Xw - cx) * rad_y - (Yw - cy) * rad_x + 0.09 * along**2 * (-1) ** i
        q2 = (along / a) ** 2 + (across / b) ** 2
        z = 1.4 * H * np.exp(-q2 * 1.1)
        acc += np.exp(z / k)
        second = np.where(z > best, best, np.maximum(second, z))
        best = np.maximum(best, z)
        # each lobe is a lens: the light gathers towards its upper shoulder and falls off to the side that goes under its neighbour
        lit = np.maximum(lit, np.exp(-(((along - 0.15 * a) / (0.62 * a)) ** 2 + ((across - (-1) ** i * 0.14 * b) / (0.5 * b)) ** 2)))
    for cx, cy, a, b in DEEP:
        lit = np.maximum(lit, 0.42 * np.exp(-(((Xw - cx) / (0.55 * a)) ** 2 + ((Yw - cy) / (0.55 * b)) ** 2)))
    hl = k * np.log(acc)
    seam = blur(sstep(0.035, 0.0, best - second), 0.018 * pxcm)

    # the light within: a warm dark jelly with the milk gathered in it
    d = R - CRUST - (r + wander)  # how far below the crust
    cloud = sstep(-1, 1, low(shape, 0.3, 1.0, 2.6, SEED + 6))
    milk = color([1.12, 0.95, 0.68])
    cream = color([0.97, 0.74, 0.45])
    jelly = color([0.62, 0.40, 0.23])
    peach = color([0.82, 0.48, 0.36])
    crevice = color([0.34, 0.19, 0.10])
    glow = mix(jelly, cream, sstep(0.22, 0.72, lit * (0.72 + 0.28 * cloud))[..., None])
    glow = mix(glow, milk, sstep(0.5, 1.1, lit * (0.7 + 0.5 * cloud))[..., None] * 0.72)
    glow = mix(glow, crevice, seam[..., None] * 0.8)
    glow = mix(glow, peach, sstep(0.13, 0.01, d)[..., None] * 0.8)

    # the deep layer: domes and lines seen through the jelly, soft
    deep = draw(arcs(DEEP, rng, (2, 4), (0.8, 1.05), 5.0) + threads(rng, 26), Xw, Yw)
    depth1 = blur(deep, 0.008 * pxcm)
    depth2 = blur(deep, 0.028 * pxcm)
    glow = glow * (1.0 + 0.7 * depth1[..., None] + 1.0 * depth2[..., None])
    stk = radial_streaks(r, th, rng)
    glow = glow * (1.0 + 0.012 * stk[..., None])

    # no drawn white lines: the membrane is relief only. Fine wrinkles run along the radius, in patches near the rim and at the creases
    stf = radial_streaks(r, th, np.random.default_rng(SEED + 40))
    patch = sstep(0.1, 0.8, low(shape, 0.3, 1.0, 2.6, SEED + 13) * 0.5 + 0.5) * (0.35 + 0.65 * sstep(0.45, 0.05, d)) + 0.5 * seam
    glow = glow * (1.0 + 0.012 * stf[..., None])
    # slow unevenness only: anything shorter breaks the reflection into white shards
    wr1 = low(shape, 0.25, 0.8, 2.6, SEED + 12)
    h = hl + 0.00018 * blur(stf, 0.002 * pxcm) * np.clip(patch, 0, 1) ** 2 + 0.006 * wr1
    rough = 0.1 + 0.05 * rank(wr1) + 0.05 * np.clip(patch, 0, 1)
    return h, hl, glow, rough


def crust(X, Y, r, th, pxcm):
    """Tubercles: Voronoi cells around the rim, unequal, each a dome with a small tip; the seeds are thrown by hand along the band, not on a lattice."""
    shape = X.shape
    rng = np.random.default_rng(SEED + 2)
    ny, nx = shape
    # seeds in polar coordinates, on rows that wander, spacing from a broad distribution
    seeds = np.ones(shape, np.uint8)
    for row in range(6):
        t = -1.6 + rng.uniform(0, 0.1)
        while t < 1.6:
            rr_ = R - 0.008 - row * 0.05 + rng.normal(0, 0.013)
            x_, y_ = rr_ * np.sin(t), rr_ * np.cos(t)
            ix, iy = int((x_ - X0) * pxcm), int((y_ - Y0) * pxcm)
            if 0 <= ix < nx and 0 <= iy < ny:
                seeds[iy, ix] = 0
            t += np.exp(rng.normal(np.log(0.058), 0.36)) / R
    dist, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    d = dist / pxcm + 0.004 * fbm(shape, pxcm, 0.03, 0.12, 2.0, SEED + 1)
    n = int(lab.max()) + 1
    # cells meet along shared grooves: the pillow is the distance to the cell's own border, so that there are no gaps between bumps
    edge = (lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))
    ed = cv2.distanceTransform((~edge).astype(np.uint8), cv2.DIST_L2, 3).astype(np.float32) / pxcm
    size = rng.uniform(0.026, 0.042, n).astype(np.float32)
    tone = rng.uniform(0.0, 1.0, n).astype(np.float32)
    ochre = (rng.random(n) < 0.3).astype(np.float32) * rng.uniform(0.3, 0.8, n).astype(np.float32)
    s_ = size[lab]
    q = np.clip(d / s_, 0, 1)
    dome = blur(1.0 - np.exp(-ed / 0.016), 0.0055 * pxcm)
    tip = np.exp(-((d / (0.17 * s_)) ** 2))  # the point in the middle of each bump
    pyr = dome + 0.28 * tip + 0.05 * fbm(shape, pxcm, 0.008, 0.05, 2.0, SEED + 6)
    t_ = tone[lab][..., None]
    c = mix(color([0.27, 0.012, 0.028]), color([0.46, 0.035, 0.05]), sstep(0.0, 0.8, t_))
    c = mix(c, color([0.55, 0.12, 0.09]), sstep(0.84, 1.0, t_) * 0.5)
    # the ochre fleck on the crown of some bumps, and the dark groove between them
    fine = sstep(-0.4, 0.8, fbm(shape, pxcm, 0.006, 0.04, 2.0, SEED + 5))
    c = mix(c, color([0.62, 0.24, 0.11]), (ochre[lab] * tip * 0.6 + 0.1 * ochre[lab] * dome * fine)[..., None])
    c = c * (0.93 + 0.14 * fine)[..., None]
    c = mix(c, color([0.13, 0.008, 0.015]), sstep(0.32, 0.0, dome)[..., None] * 0.6)
    return pyr, c


def build(dens):
    pxcm = 1000.0 * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M", flush=True)
    X, Y = np.meshgrid(X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)

    wander = 0.016 * low(shape, 0.2, 0.7, 2.4, SEED + 3) + 0.0006 * fbm(shape, pxcm, 0.015, 0.06, 1.8, SEED + 4)
    hf, hl, glow, rf = flesh(X, Y, r, th, pxcm, wander)
    pyr, cc = crust(X, Y, r, th, pxcm)

    edge = R - CRUST
    band = sstep(edge - 0.005, edge + 0.005, r + wander)  # 0 in the flesh, 1 in the crust
    # a slow swell along the rim, and small teeth on it
    swell = 0.012 * low(shape, 0.3, 0.9, 2.4, SEED + 8)
    rim = R + swell + 0.022 * pyr - 0.012
    alpha = sstep(0.003, -0.0015, r - rim)

    # the crust thins to a gold line and then pink, where it meets the flesh
    t = (r + wander - edge) / CRUST
    gold = sstep(0.11, 0.05, t)[..., None]
    cc = mix(cc, color([0.8, 0.3, 0.27]) * (0.9 + 0.2 * (1 - gold)), gold)
    under = sstep(edge - 0.018, edge + 0.002, r + wander)[..., None]
    glow = mix(glow, color([0.9, 0.5, 0.4]), under * 0.7)

    b3 = band[..., None]
    col = mix(glow * 0.12, cc, b3)
    emit = mix(glow, cc * 0.12, b3)
    roll = -0.09 * sstep(edge + 0.01, R + 0.03, r) ** 2  # the rim rolls away from the lens
    h_crust = 0.05 + 0.03 * sstep(edge - 0.02, edge + 0.04, r) + 0.022 * pyr * (1 - gold[..., 0]) + roll
    rough = mix(0.5, 0.3 + 0.14 * (1 - np.clip(pyr, 0, 1)), band)
    spec = 0.5 - 0.3 * band
    base = -(X**2) / (2 * 4.5) - ((Y - 1.4) ** 2) / (2 * 3.2)
    # the paint lies under the jelly, the crust stands on its own, the glass shell ends just under the crust
    # both rise gently towards the crust: a sudden step in the paint would be a wall, its colours stretched and magnified by the glass
    ramp = sstep(edge - 0.14, edge, r + wander)
    P = np.stack([X, Y, base + (0.25 * hl - 0.04 + 0.09 * ramp) * (1 - band) + (hf * 0.25 + h_crust) * band], -1).astype(np.float32)
    Pt = np.stack([X, Y, base + hf + 0.05 * ramp], -1).astype(np.float32)
    alpha_t = sstep(edge + 0.012, edge - 0.002, r + wander) * alpha
    zc = float(Pt[min(int((R - 0.2 - Y0) * pxcm), ny - 1), nx // 2, 2])
    return P, Pt, np.clip(col, 0, 1).astype(np.float32), emit.astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), np.clip(rf, 0.03, 1).astype(np.float32), alpha.astype(np.float32), alpha_t.astype(np.float32), spec.astype(np.float32), zc


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    if q == "flat":
        _, _, C, E, _, _, A, _, _, _ = build(0.5)
        img = np.clip(E + 0.25 * C, 0, 1) * A[..., None] + (1 - A[..., None]) * 0.002
        cv2.imwrite(os.path.join(d, "flat.jpg"), (255 * img[::-1, :, ::-1] ** 0.4545).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
        return
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    P, Pt, C, E, Ro, Rt, A, At, Sp, zc = build(dens)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, glow=E, rough=Ro, alpha=A, spec=Sp)
    npt = os.path.join(d, f"mesh_t.{q}.npz")
    # rows reversed: the glass must face up, or light enters it as if leaving it, and is totally reflected on every far slope
    np.savez(npt, P=Pt[::-1], rough=Rt[::-1], alpha=At[::-1])
    th = np.linspace(np.pi / 2 - 1.1, np.pi / 2 + 1.1, 720)
    outline = np.stack([R * np.cos(th), R * np.sin(th), np.full_like(th, zc)], 1)
    focus = np.array([0.0, 1.5, zc])
    cam, sag = fit_arc(outline, view_dir(-90.0, EL), W, DIST, apex=(0.5, 0.49), target0=(0.0, 1.2, 0.0), aperture_mm=3.2, focus_point=focus)
    print("sag", round(float(sag), 3), flush=True)
    t0 = [0.0, 1.3, zc]
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "fruit", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": "spec", "Emission Color": "glow", "Emission Strength": 1.0, "Alpha": "alpha"}},
            {"name": "jelly", "npz": npt, "material": {"Base Color": [1.0, 1.0, 1.0], "Roughness": "rough", "Transmission Weight": 1.0, "IOR": 1.38, "Specular IOR Level": 0.5, "Alpha": "alpha"}},
        ],
        "lights": [
            # one long soft light, mirrored in the folds: the wet look. It gives no diffuse light; the flesh's light is its own.
            {"type": "gradient", "name": "sheen", "loc": [0.0, 1.3 + 0.31 * 24, zc + 0.95 * 24], "target": t0, "size": [34, 18], "sigma": [7.0, 1.8], "L": 6.5, "rgb": [1.0, 0.98, 0.95], "hide_in_diffuse": True},
            {"name": "c", "loc": [3.0, 7.0, 9.0], "target": t0, "size": [1.2, 1.2], "watts": 200.0, "rgb": [1.0, 0.98, 0.95], "hide_in_diffuse": True},
            # the crust's own light, from behind and above
            {"name": "key", "loc": [-7.0, 9.0, 9.0], "target": [0.0, 1.7, zc], "size": [2.5, 2.5], "watts": 110.0, "rgb": [1.0, 0.93, 0.9], "hide_in_gloss": True},
            {"name": "kick", "loc": [7.0, 8.0, 8.0], "target": [0.0, 1.7, zc], "size": [1.5, 1.5], "watts": 40.0, "rgb": [1.0, 0.92, 0.88]},
        ],
        "world": [0.0072, 0.0002, 0.0009],  # the deep wine ground chosen
        "bounces": 12,
        "diffuse_bounces": 2,
        "glossy_bounces": 8,
        "transmission_bounces": 8,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.0, "contrast": 1.12, "saturation": 1.08, "black": 0.0012, "grain": 1.0, "sharpen": 0.25, "halation": 0.1, "glare": 0.004, "vignette": 0.2})


main()
