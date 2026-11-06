"""Cloisonné (景泰蓝) plate from above: a turquoise ground, a scrolling vine of fan-lotus heads round a medallion, in gold wire and a few enamels; the gilt lip of the far side is the arc.

    python3 -I v2/stills/s49_falang.py flat                    the drawing only, no render: out/v2/s49_falang/cand_pattern.jpg
    python3 -I v2/stills/s49_falang.py [preview|mid|final]     The final's tag is cand; never writes final.*
    python3 -I v2/stills/s49_falang.py motion                  all frames, small: s49_falang_cand_move_preview/
    GEWU_MOVE=final python3 -I v2/stills/s49_falang.py final   all frames, 1080p: s49_falang_cand_move_final/ (the shot's own s49_falang_move_final is left alone)

The ornament is in chanzhi.py, its rules read from ref/falang and ref/cloisonne. Reference only, never in the pixels; the drawing is generated and copies no piece.
Scales are estimates from general knowledge and from those photographs, not measured:
- the wire is about 0.4 mm across and stands a hair above the enamel, gilt and rubbed;
- each cell is filled separately: its own level, a very slight dome, a meniscus against the wire, its own hair of tilt, so that a reflection breaks at each wire;
- a few pinholes (砂眼), coarse speckle from the powdered glass, a colour that gathers a little against the wire;
- a petal shades from base to tip through three enamels, on the brief's request: closer to shaded Qing cells than to the Ming pieces whose drawing it follows. Grain and a noisy edge between stops stand in for powders laid side by side.
The rim's 14 shallow lobes (3% of the radius) and the cobalt band are our choice. The polished glassy top is a Principled coat, not a real layer of glass. The enamels are opaque colours picked by eye from the photographs.
The outer band is pierced: gilt wire, air, and glass (plique-a-jour, 空窗珐琅) lit by a lamp behind. A stand-in: the glass is a thin Translucent sheet, no refraction, no real thickness; the wire has no back. A band of this span in plique would be a very fragile thing: our choice, for the light, not a record of any one piece.

The move: the plate turns on its axis, one direction, even, 0.35 degrees a frame, 32 frames. The lights stay; the pattern passes under them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess

import cv2
import numpy as np

import chanzhi
import kit
from chanzhi import spiral, uv
from dishkit import Dish
from kit import OUT, caps, color, fbm, mix, rank, shoot, sstep
from vessel import reflect_light_loc

NAME = "s49_falang"
SEED = 49
W, EL, DIST = 9.6, 70.0, 88.0
PROFILE = [(4.0, 0.0), (4.3, 0.18), (5.6, 0.72), (6.7, 1.5), (7.15, 2.0), (7.26, 2.22), (7.22, 2.36), (7.05, 2.36), (6.72, 1.92), (5.8, 1.12), (4.6, 0.62), (2.5, 0.42), (0.0, 0.38)]
LOBES = dict(n=14, a=0.03, b=0.12, p=0.8, rho0=5.8)
PIERCE = (5.14, 7.32)  # the band that is gilt wire, glass and air
TAKE = "s49_falang_cand"
FRAMES, TURN = 32, 0.2  # degrees a frame


def srgb(r, g, b):
    c = np.array([r, g, b], np.float32) / 255.0
    return np.where(c < 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


# --- from the drawing to fields on a grid
def paint(X, Y, pxcm, rl):
    """Rasterise: returns the wire centre's distance, the shape id per pixel, and the shape table."""
    ny, nx = X.shape
    SS = 2
    x0, y0 = float(X[0, 0]), float(Y[0, 0])
    wobx = fbm((96, 96), 8.0, 1.0, 5.0, 3.0, SEED + 1)
    woby = fbm((96, 96), 8.0, 1.0, 5.0, 3.0, SEED + 2)
    fx = fbm((96, 96), 8.0, 0.3, 1.2, 2.2, SEED + 3)

    def wob(p):
        ix = np.clip(((p[:, 0] + 12) * 4).astype(int), 0, 95)
        iy = np.clip(((p[:, 1] + 12) * 4).astype(int), 0, 95)
        return p + np.stack([0.02 * wobx[iy, ix] + 0.005 * fx[iy, ix], 0.02 * woby[iy, ix] + 0.005 * fx[ix, iy]], 1)

    def to(p, s):
        return np.round((p - [x0, y0]) * pxcm * s * 16 + (s / 2 - 0.5) * 16).astype(np.int32)

    center = np.zeros((ny * SS, nx * SS), np.uint8)
    idx = np.zeros((ny, nx), np.int32)
    meta = [(None, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0)]
    wmap = np.full((ny, nx), 100, np.uint8)  # the pressure of the hand, 100 = 1.0
    rhand = np.random.default_rng(SEED + 40)

    def press(path, p0, p1, stroke):
        """Heavier or lighter along a line: slow swell, one or two places it hung back, each stroke its own weight."""
        q = to(path, 1) >> 4
        n_ = len(q)
        if n_ < 2:
            return
        t_ = np.linspace(0, 1, n_)
        pr = stroke * (p0 + (p1 - p0) * t_) * (1 + 0.1 * np.sin(t_ * rhand.uniform(3, 9) + rhand.uniform(0, 6)))
        for _ in range(rhand.integers(0, 3)):
            pr = pr * (1 + 0.28 * np.exp(-(((t_ - rhand.uniform(0, 1)) / 0.04) ** 2)))
        vals = np.clip(pr * 100, 20, 255).astype(np.uint8)
        for i in range(n_ - 1):
            cv2.line(wmap, tuple(int(c) for c in q[i]), tuple(int(c) for c in q[i + 1]), int(vals[i]), 5)

    for it in chanzhi.design(rl, SEED, PIERCE).items:
        if it[0] == "w":
            q = wob(it[1])
            cv2.polylines(center, [to(q, SS)], False, 255, 1, cv2.LINE_8, shift=4)
            press(q, it[2], it[3], rhand.uniform(0.88, 1.12))
            if rhand.random() < 0.3 and len(q) > 6:  # a bead where the wire was stopped, or soldered to the next
                e = q[0] if rhand.random() < 0.5 else q[-1]
                cv2.circle(center, tuple(int(c) for c in to(e[None], SS)[0]), int(rhand.uniform(0.009, 0.018) * pxcm * SS * 16), 255, -1, cv2.LINE_8, shift=4)
        else:
            _, poly, ramp, o, ang, L, sh, sc, gn = it
            q = wob(poly)
            q2 = to(q, SS)
            cv2.fillPoly(center, [q2], 0, cv2.LINE_8, shift=4)
            cv2.polylines(center, [q2], True, 255, 1, cv2.LINE_8, shift=4)
            press(np.vstack([q, q[:1]]), 1.0, 1.0, rhand.uniform(0.85, 1.15))
            meta.append((ramp, float(o[0]), float(o[1]), float(ang), float(L), sh, sc, gn))
            cv2.fillPoly(idx, [to(q, 1)], len(meta) - 1, cv2.LINE_8, shift=4)
    dist = cv2.distanceTransform(255 - center, cv2.DIST_L2, 5) / (pxcm * SS)
    dist = cv2.resize(dist, (nx, ny), interpolation=cv2.INTER_AREA).astype(np.float32)
    return dist, idx, meta, cv2.GaussianBlur(wmap.astype(np.float32) / 100.0, (0, 0), 1.2)


def fields(X, Y, pxcm, rl):
    """Colour and masks, in the flat. Everything that goes to the render is computed here, so that the flat view tells the truth about the wire."""
    shape = X.shape
    dist, idx, meta, wpress = paint(X, Y, pxcm, rl)
    rho = np.hypot(X, Y)
    # wire: thin and thick by hand, a touch finer in the small scroll at the rim. Rubbed thin in places
    wid = 0.72 + 0.56 * rank(fbm(shape, pxcm, 0.3, 1.6, 2.4, SEED + 5))
    hw = (0.0104 + 0.0014 * fbm(shape, pxcm, 0.04, 0.3, 2.0, SEED + 6)) * wid
    pb = sstep(PIERCE[0] - 0.02, PIERCE[0] + 0.02, rho)  # the pierced band; the solid rim closes it on the outside
    hw = hw * wpress * (0.72 + 0.5 * pb)  # a wire that must carry itself is heavier
    wire = sstep(1.0, 0.8, dist / hw)
    edge = np.clip(dist / hw, 0, 1)

    # the cells
    free_ = (wire < 0.5).astype(np.uint8)
    n_cells, lab = cv2.connectedComponents(free_, connectivity=4)
    d_in = cv2.distanceTransform(free_, cv2.DIST_L2, 5).astype(np.float32) / pxcm

    # colour, per shape: three stops from base to tip. Grain in the edge between stops: powders laid side by side, not an airbrush
    powder = rank(fbm(shape, pxcm, 0.012, 0.05, 1.2, SEED + 7))
    grit = rank(fbm(shape, pxcm, 0.006, 0.02, 1.0, SEED + 18))
    cloud = rank(fbm(shape, pxcm, 0.1, 0.9, 2.3, SEED + 8))
    blendn = fbm(shape, pxcm, 0.06, 0.5, 2.0, SEED + 9)
    N = len(meta)
    stops = np.zeros((N, 3, 3), np.float32)
    ox, oy, ax, ay, Ln, sh, sc, gn = (np.zeros(N, np.float32) for _ in range(8))
    glo, ghi = srgb(*chanzhi.GROUND[0]), srgb(*chanzhi.GROUND[1])
    for i, (ramp, o0, o1, ang, L, sh_, sc_, gn_) in enumerate(meta):
        if ramp is not None:
            stops[i] = np.array([srgb(*c) for c in chanzhi.RAMPS[ramp]])
        ox[i], oy[i], ax[i], ay[i], Ln[i], sh[i], sc[i], gn[i] = o0, o1, np.cos(ang), np.sin(ang), max(L, 1e-3), sh_, sc_, gn_
    # along the petal, shifted and rescaled for each petal; an uneven front: the enamel was laid wet with a quill, not airbrushed
    t = ((X - ox[idx]) * ax[idx] + (Y - oy[idx]) * ay[idx]) / Ln[idx] * sc[idx] + sh[idx] + 0.12 * blendn + 0.1 * (powder - 0.5) + 0.04 * (grit - 0.5)
    col = stops[idx, 0]
    col = mix(col, stops[idx, 1], sstep(0.1, 0.48, t))
    col = mix(col, stops[idx, 2], sstep(0.58, 1.02, t))
    isg = idx == 0
    isg0 = isg
    cl = (0.5 + 0.34 * (cloud - 0.5))[..., None]
    col = np.where(isg[..., None], glo * (1 - cl) + ghi * cl, col * (0.82 + 0.36 * cl) * gn[idx][..., None])
    # the turquoise itself moves: a greener and a bluer batch of frit, in slow patches
    hue = rank(fbm(shape, pxcm, 0.3, 2.2, 2.8, SEED + 26))
    isg = isg.astype(np.float32)
    col = col * (1 + (isg * (hue - 0.5))[..., None] * np.array([-0.2, 0.08, -0.05], np.float32))

    # the glass: speckle from the powder at two sizes, each cell fired a little differently, colour gathering against the wire, pale crystals
    lv = np.random.default_rng(SEED + 10).normal(0, 1, n_cells).astype(np.float32)
    level = lv[lab]
    # the ground is coarser than the shaded petals, whose grain at this strength reads as sugar
    amp = (0.42 + 0.58 * isg)[..., None]
    col = col * (1.0 + amp * (0.34 * (powder[..., None] - 0.5) + 0.22 * (grit[..., None] - 0.5) - 0.0))
    col = col * (1.0 + 0.07 * np.clip(level, -2, 2)[..., None])
    # the enamel pulls back from the wire in the firing: a dark seam along it, not the same everywhere
    seam_n = rank(fbm(shape, pxcm, 0.08, 0.5, 2.0, SEED + 11))
    gather = np.exp(-d_in / 0.018) * (0.25 + 0.75 * sstep(0.2, 0.75, seam_n))
    col = col * (1.0 - 0.62 * gather)[..., None]
    fleck = sstep(0.955, 0.992, grit) * sstep(0.3, 0.7, rank(fbm(shape, pxcm, 0.2, 1.2, 2.2, SEED + 12)))
    col = mix(col, np.minimum(col * 1.5 + 0.2, 1.0), 0.6 * fleck)

    # pinholes: few, and only in a few places, against the wire more than elsewhere; the old count was 340 a square cm and read as pepper
    dens = 0.25 + 1.5 * rank(fbm(shape, pxcm, 0.5, 2.6, 2.4, SEED + 13)) + 0.5 * np.exp(-d_in / 0.05)
    pits = caps(shape, pxcm, 7, 0.003, 0.012, SEED + 14, slope=-3.8) * sstep(1.05, 1.5, dens)
    pit = sstep(0.0, 0.0028, pits)
    col = mix(col, color([0.014, 0.011, 0.009]), pit * (1 - wire) * 0.94)

    # gilding, rubbed through to copper on the high spots; a dark line where the wire goes down into the glass
    wear = sstep(0.62, 0.9, rank(fbm(shape, pxcm, 0.03, 0.3, 2.0, SEED + 15)))
    gold = mix(color([0.92, 0.60, 0.22]), color([0.56, 0.30, 0.16]), wear)
    col = mix(col, gold, wire)
    # the rim itself
    wob = 0.02 * fbm(shape, pxcm, 0.5, 2.5, 3.0, SEED + 16)
    rim = sstep(rl - 0.36, rl - 0.33, rho + wob)
    wear2 = sstep(0.55, 0.9, rank(fbm(shape, pxcm, 0.06, 0.5, 2.0, SEED + 17)))
    gilt_c = mix(color([1.0, 0.68, 0.26]), color([0.8, 0.46, 0.2]), 0.4 * wear2)
    col = mix(col, gilt_c, rim)
    void = (isg0 * pb * (1 - wire)).astype(np.float32)
    void = void * (1 - rim)
    void = np.maximum(void, sstep(rl + 0.26, rl + 0.3, rho))  # past the curl of the lip the plate stops: the openwork must not show its own underside. The back of the plate does not exist; nothing in the frame sees it otherwise
    glass = ((~isg0) * pb * (1 - wire) * (1 - rim)).astype(np.float32)
    return dict(void=void, glass=glass, col=col, wire=wire, edge=edge, d_in=d_in, level=level, lab=lab, n=n_cells, pits=pits, pit=pit, rim=rim, cloud=cloud, wear=wear, wear2=wear2)


def flat_view():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, lobes=LOBES)
    rl = dish.rho_lip
    pxcm = 125.0  # the size it will be at the final's 125 pixels a cm
    xs = (np.arange(int(2 * (rl + 0.3) * pxcm), dtype=np.float32) + 0.5) / pxcm - (rl + 0.3)
    ys = (np.arange(int((rl + 2.4) * pxcm), dtype=np.float32) + 0.5) / pxcm - 2.1
    X, Y = np.meshgrid(xs, ys)
    F = fields(X, Y, pxcm, rl)
    col = F["col"] * (0.94 + 0.06 * F["wire"])[..., None]
    col = col * (1 + 0.25 * F["glass"])[..., None]
    col = col * (1 - F["void"])[..., None] + 0.012 * F["void"][..., None]
    col[np.hypot(X, Y) > rl] = 0.012
    im = np.clip(col, 0, 1) ** (1 / 2.2)
    im = (im[::-1, :, ::-1] * 255).astype(np.uint8)  # +y up
    p = os.path.join(d, "cand_pattern.jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(p, im.shape, "cells", F["n"], "rl", rl, flush=True)


def crop(dish, X, Y, extra=0.5):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def build(dish, X, Y, pxcm):
    shape = X.shape
    rl = dish.rho_lip
    F = fields(X, Y, pxcm, rl)
    wire, edge, d_in, level, lab, pits, rim = F["wire"], F["edge"], F["d_in"], F["level"], F["lab"], F["pits"], F["rim"]
    # each cell: a level, a slight dome, a meniscus up against the wire; a hair of tilt of its own
    n = F["n"]
    inv = lab.ravel()
    rt = np.random.default_rng(SEED + 20)
    tx, ty = rt.normal(0, 0.02, n).astype(np.float32), rt.normal(0, 0.02, n).astype(np.float32)
    area = np.bincount(inv, minlength=n) + 1.0
    cx = (np.bincount(inv, X.ravel(), minlength=n) / area).astype(np.float32)
    cy = (np.bincount(inv, Y.ravel(), minlength=n) / area).astype(np.float32)
    tilt = np.clip(tx[lab] * (X - cx[lab]) + ty[lab] * (Y - cy[lab]), -0.006, 0.006)
    # the thickness you can read: the glass stands in a shallow dish between the wires, higher in the middle of a small cell, with a groove where it pulled back from the wire
    dome = 1.0 - np.exp(-d_in / 0.045)
    groove = np.exp(-d_in / 0.012)
    wave = fbm(shape, pxcm, 0.05, 0.35, 2.4, SEED + 21)  # stoned by hand, not lapped: the polish rides over shallow hollows
    hollow = fbm(shape, pxcm, 0.3, 1.6, 2.8, SEED + 27)
    enamel = -0.0095 - 0.0016 * np.clip(level, -2, 2) + 0.0045 * dome - 0.0032 * groove + tilt + 0.00075 * wave + 0.0022 * hollow - np.minimum(pits, 0.014)
    wire_top = 0.0014 + 0.0040 * np.sqrt(np.maximum(1 - edge**2, 0)) + 0.0005 * fbm(shape, pxcm, 0.02, 0.2, 2.0, SEED + 22)
    h = enamel * (1 - wire) + wire_top * wire
    # the rim: a strip of cast and gilt copper, dented, polished on its crown
    h = h * (1 - rim) + rim * (0.0022 * fbm(shape, pxcm, 0.2, 1.2, 2.6, SEED + 23) + 0.006 * fbm(shape, pxcm, 0.6, 3.0, 2.8, SEED + 28))
    h = h + 0.008 * fbm(shape, pxcm, 1.6, 6.0, 3.4, SEED + 24)  # the beaten copper body under it all
    scratch = rank(fbm(shape, pxcm, 0.003, 0.02, 1.2, SEED + 25))
    pit = F["pit"]
    gilt = np.maximum(wire, rim)
    rough = (0.2 + 0.1 * F["cloud"] + 0.04 * scratch + 0.4 * pit) * (1 - gilt) + (0.2 + 0.1 * scratch + 0.14 * F["wear"]) * wire * (1 - rim) + (0.13 + 0.12 * F["wear2"]) * rim
    metal = 0.94 * gilt
    coat = 0.85 * (1 - gilt) * (1 - pit)
    F["crough"] = 0.075 + 0.075 * rank(hollow) + 0.03 * scratch
    return dish.surface(X, Y, h), np.clip(F["col"], 0, 1).astype(np.float32), np.clip(rough, 0.03, 1).astype(np.float32), metal.astype(np.float32), coat.astype(np.float32), F["crough"].astype(np.float32), F["void"], F["glass"]


def _small_take(name, cfg, lk, move, develop, q):
    """All frames, small, so that the motion can be judged. As s66's."""
    mv = lk["move"]
    path = kit.camera_path(cfg["camera"], cfg.get("lights", []), mv, mv["frames"])
    d = os.path.join(OUT, f"{name}_move_preview")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    cfg.update(res=[640, 360], frames=path, fetch_to=d, shutter=mv.get("shutter", 0.5), spin=mv["spin"], spp=48)
    kit._render_local(cfg, os.path.join(OUT, name), "take")  # small frames
    from darkroom import develop as dev

    for i, f in enumerate(sorted(x for x in os.listdir(d) if x.endswith(".npy"))):
        im = dev(np.load(os.path.join(d, f)).astype(np.float32), **{**develop, "seed": 700 + i})
        cv2.imwrite(os.path.join(d, f"f{i:03d}.png"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(d, "f%03d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(d, "take.mp4")], check=True)
    print(os.path.join(d, "take.mp4"), flush=True)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "flat":
        flat_view()
        return
    orig = kit.looks
    move = {"spin": {"pt": [0, 0, 0], "axis": [0, 0, 1], "deg": -TURN * (FRAMES - 1), "meshes": {"except": ["sky"]}}, "frames": FRAMES, "shutter": 0.5, "spp": 160}
    kit.looks = lambda: {**orig(), TAKE: {"move": move}}
    name = NAME
    if q == "motion":
        kit._take = _small_take
        os.environ["GEWU_MOVE"] = "preview"
        q = "preview"
    if os.environ.get("GEWU_MOVE"):
        name = TAKE  # never the shot's own s49_falang_move_final, which the film reads
    dens = {"preview": 0.5, "mid": 0.7, "final": 0.8 if os.environ.get("GEWU_MOVE") else 1.0}[q]
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, lobes=LOBES)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.49), aperture_mm=16.0, focus_rho=dish.rho_lip - 1.6)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 350.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.22 if os.environ.get("GEWU_MOVE") else 0.05))  # a turn brings new parts of the plate into the corners
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    P, C, Ro, Me, Co, Cr, Vo, Gl = build(dish, X, Y, pxcm)
    if os.environ.get("GEWU_MOVE"):  # the turn is centred on the rest pose, so that a lobe's crown stays over the middle of the frame: the spin runs 0 to -deg, so start at +deg/2
        ca, sa = np.cos(np.radians(TURN * (FRAMES - 1) / 2)), np.sin(np.radians(TURN * (FRAMES - 1) / 2))
        P = np.stack([P[..., 0] * ca - P[..., 1] * sa, P[..., 0] * sa + P[..., 1] * ca, P[..., 2]], -1).astype(np.float32)
    npz = os.path.join(d, f"mesh.{q}{os.environ.get('S49_TAG', '')}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=Me, coat=Co, crough=Cr, void=Vo, glass=Gl)

    def wall(rh, th):
        return dish.polar(np.array(rh), th), dish.normal(np.array(rh * np.cos(th)), np.array(rh * np.sin(th)))

    pf, nf = wall(dish.rho_lip - 1.6, np.pi / 2)
    sheen, _ = reflect_light_loc(pf, nf, cam, 130.0)
    pw, nw = wall(dish.rho_lip - 2.4, np.pi / 2 - 0.55)
    lw, _ = reflect_light_loc(pw, nw, cam, 120.0)
    A = dish.polar(np.array(dish.rho_lip), np.pi / 2)
    scene = {
        "camera": cam,
        "meshes": [
            {
                "name": "plate",
                "npz": npz,
                "shader_py": os.path.join(os.path.dirname(os.path.abspath(__file__)), "falang_shader.py"),
                "params": {"through": 0.12, "skin": 0.1},
            }
        ],
        "lights": [
            {"type": "gradient", "name": "sheen", "loc": sheen.tolist(), "target": pf.tolist(), "size": [420, 300], "sigma": [150, 60], "L": 0.34, "rgb": [1.0, 0.99, 0.97]},
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": pw.tolist(), "size": [150, 90.0], "sigma": [46, 22], "L": 1.5, "rgb": [1.0, 0.98, 0.96]},
            {"name": "key", "loc": [-18.0, 42.0, 90.0], "target": [0, 1, 1], "size": [50, 50], "watts": 30000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
            {"name": "spark", "loc": [-14.0, 30.0, 88.0], "target": [0, 1, 1], "size": [22, 22], "watts": 1500, "rgb": [1.0, 0.97, 0.92], "hide_in_diffuse": True},
            {"name": "fill", "loc": [14.0, -40.0, 85.0], "target": [0, 3, 1], "size": [60, 60], "watts": 7000, "rgb": [0.97, 0.99, 1.0], "hide_in_gloss": True},
            # behind the plate, for the glass: uneven on purpose, stronger on the far side. Nothing else sees it: enamel and gilt face away, and the camera does not see lamps
            {"name": "behind", "loc": [-3.0, 5.0, -16.0], "target": [0.0, 5.0, 0.0], "size": [26, 16], "watts": float(os.environ.get("S49_BACK", 9000)), "rgb": [1.0, 0.93, 0.82], "hide_in_gloss": True},
            {"name": "lip", "loc": (A + [0.0, 34.0, 26.0]).tolist(), "target": A.tolist(), "size": [70, 6], "watts": 22000, "rgb": [1.0, 0.96, 0.9]},
        ],
        "env": {"window": 2.2, "win_az": -30.0, "win_el": 38.0, "win_w": 30.0, "win_h": 34.0, "strip": 0.7, "ceil": 0.32, "wall": 0.06},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": 0.4, "seed": 49},
        "world": [0.0, 0.0, 0.0],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 4,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }
    shoot(name, scene, q, tag=os.environ.get("S49_TAG") or ("cand" if q == "final" else None), develop={"exposure": 0.0, "contrast": 1.26, "saturation": 1.08, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "glare": 0.004, "vignette": 0.2})


main()
