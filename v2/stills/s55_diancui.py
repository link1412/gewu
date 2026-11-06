"""Shot 17: diancui (点翠), macro. The rim of a flat gilt plaque is the arc; below it the tips of kingfisher-feather snips in beaded wire. Rebuilt for the arc : the old whole round read as a flower.

    python3 -I v2/stills/s55_diancui.py flat                   the drawing inside the frame, no render: out/v2/s55_diancui/flat.jpg
    python3 -I v2/stills/s55_diancui.py [preview|mid|final]    The final's tag is cand; never writes final.*
    GEWU_MOVE=final python3 -I v2/stills/s55_diancui.py final  all frames, 1080p: s55_diancui_cand_move_final/ (the shot's own s55_diancui_move_final is left alone)
    python3 -I v2/stills/s55_diancui.py take                   develop those frames here into s55_diancui_take_cand/ with take.mp4

Everything is a height field in cm, built like the object:
- each cell is one snip of feather glued on a stamped backing. Barbs are real relief: a ridge (ramus) with slanted barbules either side and a dark furrow between. Some snips keep their rachis, with barbs leaving it at a slant; others
  are cut from one vane, so barbs fan from a quill out of sight. Barbs run edge to edge and are cut by the wire;
- the wire is beaded (milled), one bead at a time along the visible outline of each cell, as on ref/diancui, not a smooth tube; the rim is a two-strand twisted rope, hand-laid, its crowns rubbed flat;
- the ground between cells is granulated, grains soldered on one by one; tarnish sits in what is low and bright metal on what stands up, computed from the height, not sprinkled;
- wear comes off barb by barb: first thinner, inky and violet, as on ref/diancui, then gone down to the backing, more on the tips near the rim, where hands reach.

MEASURED on ref/diancui/diancui_cma_161918_main.tif (5858 px over 28.5 cm, about 205 px/cm): barb spacing 3.0 to 3.5 px over six of eight patches of one leaf, so .015 to .017 cm; ours .0158. One piece, one leaf.
FROM THE LITERATURE, by way of a research report, not read in the originals by us: whole barb 40 to 70 um on diancui pieces (Gu 2021, 谷岸 et al.), ours about 47 um; the blue is in the barb's spongy keratin, not the barbules (Stavenga 2011, Lee 2021);
diffuse peak 471 (deep blue) to 500 nm (cyan) between feathers (Kang 2025), blue shift with angle (Meier 2026: 523 nm at 15 degrees, end point not given). Our lam runs 480 to 506, an index into a ramp by eye, not a spectrum.
ESTIMATES: plaque radius 6.5 cm (the museum piece is 28 cm across, so a large round piece is possible; this drawing copies none), wire and grain sizes, the layout, the colours. No source gives barbule size on soft feather; ours fill the gap between barbs at about 78 um pitch, which is a guess
and probably longer than the real, short ones.
SUBSTITUTE: structural colour, see diancui_shader.py.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

NAME = "s55_diancui"
TAKE = "s55_diancui_cand"
FRAMES = 21  # the old take's count: len 18 + 3
SEED = 55
R = 6.5
W, EL, DIST = 4.2, 50.0, 16.0  # a 120 mm macro at 16 cm
APEX = (0.5, 0.49)
RHO_IN = 0.2  # the rim's rope and band, inward from the edge
RAMP = [[400, 0.05, 0.02, 0.28], [430, 0.035, 0.05, 0.50], [455, 0.012, 0.13, 0.66], [475, 0.006, 0.28, 0.74], [495, 0.008, 0.46, 0.68], [515, 0.02, 0.56, 0.50], [540, 0.09, 0.56, 0.26]]


def pol(s, rr):
    """s: arc length along the rim from the top, rr: radius."""
    return np.stack([rr * np.sin(s / R), rr * np.cos(s / R)], -1)


def petal(rng, s0, d0, d1, w, lean=0.0):
    """A cut snip in its wire: foot d0, tip d1 inward from the rim. No two sides equal, and the scissors wandered. Returns polygon, foot, tip."""
    t = np.linspace(0, 1, 140)
    prof = np.sin(np.pi * t**0.86) ** 0.5  # full, then a blunt tip
    sh = [rng.uniform(0.9, 1.1) * (1 + rng.uniform(-0.03, 0.03) * np.sin(2 * np.pi * (f * t + rng.random()))) for f in (1.3, 2.7)]
    uL = w * sh[0] * prof + lean * t**2 + 0.012 * np.sin(2 * np.pi * (3.3 * t + rng.random())) * prof
    uR = -w * sh[1] * prof + lean * t**2 + 0.012 * np.sin(2 * np.pi * (4.1 * t + rng.random())) * prof
    rr = (R - d0) + (d0 - d1) * t
    q = np.vstack([pol(s0 + uL * (R / rr), rr), pol(s0 + uR[::-1] * (R / rr[::-1]), rr[::-1])])
    return q, pol(np.float64(s0), R - d0), pol(np.float64(s0 + lean), R - d1)


def layout():
    """Back to front: a cell is (polygon, foot, tip, kind, height). Only what the frame sees: three tiers of tips, no whole flower."""
    rng = np.random.default_rng(SEED)
    cells = []
    tiers = (  # like scales: each tier staggered over the feet of the one behind, so that blue fills the frame and the gold is what is left at the rim
        (0.285, 0.016, 1.0, [-3.72, -1.86, 0.03, 1.9, 3.74]),
        (0.62, 0.05, 1.02, [-2.8, -0.92, 0.98, 2.86]),
        (1.12, 0.085, 1.02, [-3.7, -1.84, 0.06, 1.9, 3.76]),
    )
    for d1, h, w, ss in tiers:
        for s0 in ss:
            s1 = s0 + rng.normal(0, 0.06)
            kind = "rachis" if rng.random() < 0.34 else "fan"
            cells.append((*petal(rng, s1, 4.6, d1 + abs(rng.normal(0, 0.025)), w * rng.uniform(0.94, 1.06), rng.normal(0, 0.07)), kind, h + rng.normal(0, 0.004)))
    return cells


def beads():
    """Set in the spandrels: (s, d, r, there). One has gone from its setting."""
    return [(-0.97, 0.4, 0.078, True), (0.95, 0.4, 0.074, False)]


def camera():
    th = np.linspace(0, 2 * np.pi, 2880)
    outline = np.stack([R * np.cos(th), R * np.sin(th), np.zeros_like(th)], 1)
    focus = np.array([0.0, R - 0.5, 0.07])
    cam, sag = fit_arc(outline, view_dir(-90.0, EL), W, DIST, apex=APEX, target0=(0.0, R - 1.0, 0.0), aperture_mm=3.5, focus_point=focus)
    print("sag", round(float(sag), 3), flush=True)
    return cam, focus


def window(cam, margin=0.14):  # the plate rises towards the middle, so the near edge comes up into the frame: a wide margin
    """The patch of the plaque the frame sees."""
    x, y = np.meshgrid(np.linspace(-R, R, 500), np.linspace(R - 6, R + 0.1, 400))
    P = np.stack([x, y, 0 * x], -1).reshape(-1, 3)
    u, v, w = project(cam, P)
    ok = (u > -margin) & (u < 1 + margin) & (v > -margin) & (v < 1 + margin) & (w > 0)
    q = P[ok]
    return float(q[:, 0].min()), float(q[:, 0].max()), float(q[:, 1].min()), min(float(q[:, 1].max()), R + 0.04)


def flat_view():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cam, _ = camera()
    im = np.full((720, 1280, 3), (40, 120, 170), np.uint8)
    u, v = np.meshgrid(np.arange(1280) / 1280.0, np.arange(720) / 720.0)
    rng = np.random.default_rng(1)

    def pr(q):
        a, b, _ = project(cam, np.column_stack([q, np.zeros(len(q))]))
        return np.round(np.column_stack([a * 1280, b * 720]) * 16).astype(np.int32)

    th = np.linspace(0, 2 * np.pi, 7200)
    sky = np.vstack([pr(np.column_stack([R * np.cos(th), R * np.sin(th)]))])
    mask = np.zeros((720, 1280), np.uint8)
    cv2.fillPoly(mask, [sky], 255, cv2.LINE_AA, 4)
    for q, _, _, kind, _ in layout():
        c_ = tuple(int(x) for x in (rng.integers(150, 230), rng.integers(70, 140), rng.integers(0, 30)))
        cv2.fillPoly(im, [pr(q)], c_, cv2.LINE_AA, 4)
        cv2.polylines(im, [pr(q)], True, (60, 170, 235), 2, cv2.LINE_AA, 4)
    im[mask == 0] = 20
    for s, dd, r_, there in beads():
        cc = pr(pol(np.array([s]), np.array([R - dd])).reshape(1, 2))[0] // 16
        cv2.circle(im, tuple(int(x) for x in cc), 8, (40, 40, 200) if there else (0, 0, 0), -1, cv2.LINE_AA)
    cv2.line(im, (0, int(0.37 * 720)), (1279, int(0.37 * 720)), (90, 90, 90), 1)
    p = os.path.join(d, "flat.jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(p)


def outline_beads(lab, n, pxcm, X0, Y0, ring):
    """String beads along what shows of each cell's outline, front to back, so a stretch of wire is strung once. Returns seeds (iy, ix, r) in px and cm."""
    rng = np.random.default_rng(SEED + 40)
    occ = np.zeros(lab.shape, np.uint8)
    out = []
    S = 0.0345  # bead pitch, cm

    def string(pts, closed=True):
        if len(pts) < 8:
            return
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.r_[0.0, np.cumsum(seg)] / pxcm
        pos, i = rng.uniform(0, S), 0
        gauge = 1.0
        while pos < cum[-1]:
            i = int(np.searchsorted(cum, pos))
            i = min(i, len(pts) - 1)
            gauge = 0.92 * gauge + 0.08 * rng.lognormal(0, 0.28)  # the wire was drawn by hand: its gauge wanders
            r_ = 0.0178 * gauge * rng.lognormal(0, 0.05)
            x, y = int(pts[i, 0] + rng.normal(0, 0.0012 * pxcm)), int(pts[i, 1] + rng.normal(0, 0.0012 * pxcm))
            mg = int(0.03 * pxcm)
            if mg <= y < lab.shape[0] - mg and mg <= x < lab.shape[1] - mg and not occ[y, x]:
                out.append((y, x, r_))
                cv2.circle(occ, (x, y), max(1, int(0.75 * r_ * pxcm)), 1, -1)
            pos += S * gauge * rng.uniform(0.92, 1.08) * (2.1 if rng.random() < 0.006 else 1.0)  # now and then the mill skipped

    string(ring, closed=True)
    for i in range(n - 1, 0, -1):
        ys, xs = np.nonzero(lab[::8, ::8] == i)
        if ys.size == 0:
            continue
        y0, y1, x0, x1 = max(ys.min() * 8 - 8, 0), ys.max() * 8 + 16, max(xs.min() * 8 - 8, 0), xs.max() * 8 + 16
        cs, _ = cv2.findContours((lab[y0:y1, x0:x1] == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for c in cs:
            pts = c[:, 0, :].astype(np.float32) + [x0, y0]
            sg = max(0.006 * pxcm, 1.0)  # the contour's stairs, away
            m = int(4 * sg) + 1
            if len(pts) > 2 * m:
                wrap = np.vstack([pts[-m:], pts, pts[:m]])
                pts = cv2.GaussianBlur(wrap, (1, 2 * m + 1), 0, sigmaY=sg)[m:-m]
            string(pts)
    return out


def scratches(shape, pxcm, seed, count):
    """Long hairlines and short nicks: handled metal. A float image, 0..1."""
    rng = np.random.default_rng(seed)
    a = np.zeros(shape, np.float32)
    ny, nx = shape
    for _ in range(count):
        x, y = rng.uniform(0, nx), rng.uniform(0, ny)
        th, L = rng.uniform(0, np.pi), rng.lognormal(np.log(0.12), 0.8) * pxcm
        cv2.line(a, (int(x), int(y)), (int(x + L * np.cos(th)), int(y + L * np.sin(th))), float(rng.uniform(0.3, 1)), 1, cv2.LINE_AA)
    return blur(a, max(0.0012 * pxcm, 0.5))


def build(cam, dens):
    pxcm = 1250.0 * dens
    X0, X1, Y0, Y1 = window(cam)
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M", "window", round(X0, 2), round(X1, 2), round(Y0, 2), round(Y1, 2), flush=True)
    X, Y = np.meshgrid(X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    r0 = np.hypot(X, Y)
    th = np.arctan2(X, Y)
    # raised by hand: not a true circle
    r = r0 * (1.0 + 0.0011 * np.sin(5 * th + 0.8) + 0.0006 * np.sin(11 * th + 2.0) + 0.0003 * np.sin(29 * th + 4.1))
    rho = R - r

    cells = layout()
    lab = np.zeros(shape, np.int32)
    for i, c in enumerate(cells, start=1):
        cv2.fillPoly(lab, [np.round((c[0] - [X0, Y0]) * pxcm * 16).astype(np.int32)], i, cv2.LINE_8, shift=4)
    lab[rho < RHO_IN + 0.05] = 0
    n = len(cells) + 1
    feather = lab > 0
    edges = (lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))
    edges[0], edges[:, 0] = False, False
    dw = cv2.distanceTransform((~edges).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm

    # --- the wire, a bead at a time
    tt = np.linspace(-1.1, 1.1, 8000)
    rr_ring = R - RHO_IN - 0.012
    ring = (np.stack([rr_ring * np.sin(tt), rr_ring * np.cos(tt)], 1) - [X0, Y0]) * pxcm
    ring = ring[(ring[:, 0] > 0) & (ring[:, 0] < nx) & (ring[:, 1] > 0) & (ring[:, 1] < ny)]
    bd = outline_beads(lab, n, pxcm, X0, Y0, ring.astype(np.float32))
    print("beads", len(bd), flush=True)
    seeds = np.ones(shape, np.uint8)
    for y, x, _ in bd:
        seeds[y, x] = 0
    dj, lj = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    rmap = np.full(int(lj.max()) + 1, 0.016, np.float32)
    for y, x, r_ in bd:
        rmap[lj[y, x]] = r_
    dj = dj.astype(np.float32) / pxcm
    rj = rmap[lj]
    bead = np.sqrt(np.maximum(1.0 - (dj / rj) ** 2, 0.0))  # 0..1, a dome
    wire_m = sstep(1.0, 0.86, dj / rj)
    del lj

    # --- the rim: a two-strand rope, then a plain band
    s_rim = th * R
    strand = 0.1  # pitch of one strand, cm
    du = 0.28 * cv2.resize(fbm((1, 4096), 4096 / (2.2 * 2 * np.pi), 0.1, 1.2, 2.2, SEED + 11), (4096, 1), interpolation=cv2.INTER_LINEAR)[0]
    warp_u = np.interp(th, np.linspace(-1.1, 1.1, 4096), du)
    u = s_rim / strand + rho * 1.1 / strand + warp_u
    v = u - np.floor(u)
    seg = np.floor(u).astype(np.int64) % 8192
    rr_ = np.random.default_rng(SEED + 41)
    per_seg = rr_.normal(0, 1, 8192).astype(np.float32)[seg]
    crown = np.sqrt(np.maximum(1.0 - (2 * v - 1.0) ** 2, 0.0))
    env = np.sqrt(np.maximum(1.0 - ((rho - 0.068) / 0.068) ** 2, 0.0))
    rope = env * (0.62 + 0.38 * crown)
    flat = 0.965 + 0.012 * per_seg + 0.012 * fbm(shape, pxcm, 0.08, 0.6, 2.4, SEED + 12)  # the crowns are rubbed flat, some more than others
    rope = np.minimum(rope, flat)
    rope_m = (rho < 0.136).astype(np.float32)
    band_m = ((rho >= 0.136) & (rho < RHO_IN + 0.01)).astype(np.float32)
    band_h = 0.012 * sstep(0.118, 0.14, rho)

    # --- the feather, cell by cell
    rp = np.random.default_rng(SEED + 1)
    foot = np.array([[0, 0]] + [c[1] for c in cells], np.float32)
    tip = np.array([[0, 1]] + [c[2] for c in cells], np.float32)
    ax = tip - foot
    ax /= np.linalg.norm(ax, axis=1, keepdims=True)
    is_rach = np.array([False] + [c[3] == "rachis" for c in cells])[lab]
    ox, oy = X - foot[lab, 0], Y - foot[lab, 1]
    t_ = ox * ax[lab, 0] + oy * ax[lab, 1]
    u_ = -ox * ax[lab, 1] + oy * ax[lab, 0]
    bend = rp.normal(0, 0.05, n).astype(np.float32)
    u_ = u_ - bend[lab] * t_**2 * 0.5  # the rachis curves
    S = 0.0158  # mean barb spacing, cm. Measured on ref/diancui, see above
    # fan: barbs from a quill behind the snip
    sk = rp.uniform(-0.75, 0.75, n).astype(np.float32)  # which way the vane was laid
    ca, sa = np.cos(sk), np.sin(sk)
    Dq = rp.uniform(2.5, 8.0, n).astype(np.float32)
    px_ = ca[lab] * t_ - sa[lab] * u_ + Dq[lab]
    py_ = sa[lab] * t_ + ca[lab] * u_
    ang = np.arctan2(py_, px_)
    a_fan = ang * Dq[lab] + bend[lab] * (np.hypot(px_, py_) - Dq[lab]) ** 2
    along_fan = np.hypot(px_, py_)
    # rachis: barbs leave it at a slant, curving towards the tip
    alpha = np.radians(rp.uniform(36, 48, n)).astype(np.float32)
    au = np.abs(u_)
    a_r = (t_ - au / np.tan(alpha[lab]) - 0.1 * au**2) * np.sin(alpha[lab]) + (u_ > 0) * rp.uniform(0, 1, n).astype(np.float32)[lab]
    a = np.where(is_rach, a_r, a_fan).astype(np.float64)
    along = np.where(is_rach, au / np.sin(alpha[lab]), along_fan)
    del px_, py_, ang, a_fan, along_fan, a_r, ox, oy
    a = a + 0.0034 * fbm(shape, pxcm, 0.2, 1.6, 2.4, SEED + 2) + 0.00028 * fbm(shape, pxcm, 0.03, 0.2, 1.8, SEED + 24) + rp.uniform(0, 40, n)[lab] + 80.0
    NB = 16384
    wid = S * rp.lognormal(0, 0.16, NB)
    wid[rp.random(NB) < 0.03] *= 1.7  # a barb lost in the feather's life, a wider furrow
    cum = np.cumsum(wid)
    bi = np.clip(np.searchsorted(cum, a), 1, NB - 1)
    fa = ((a - cum[bi - 1]) / wid[bi]).astype(np.float32)
    del a
    q = np.abs(2 * fa - 1.0)
    per_barb = rp.normal(0, 1, NB).astype(np.float32)[bi]
    w_b = (S / wid)[bi].astype(np.float32)  # q scaled so a ramus has the same width in a wide bay
    ramus = np.sqrt(np.maximum(1.0 - (q / np.minimum(0.3 * w_b, 0.8)) ** 2, 0.0))  # the blue ridge: reported about 40 um across on old pieces (Gu 2021); ours about 60, so that it reads at this frame
    side = np.sign(2 * fa - 1.0)
    bphase = (along + side * q * S * 0.55) / 0.0078  # barbules slant forward from the ramus, a chevron, each its own
    bk = np.floor(bphase).astype(np.int64)
    bul = 0.5 + 0.5 * np.cos(2 * np.pi * bphase)
    rbul = np.random.default_rng(SEED + 42).random(65536).astype(np.float32)[(bk * 7919 + bi * 104729 + (side > 0) * 31) % 65536]
    bul = bul**1.5 * (0.3 + 0.7 * rbul)
    bul_zone = sstep(0.16, 0.3, q) * sstep(1.0, 0.86, q) * (0.55 + 0.45 * rbul)
    furrow = sstep(0.88, 1.0, q)
    # each barb lives its own life along its length
    rb_ = np.random.default_rng(SEED + 43)
    fq, ph = rb_.uniform(1.0, 5.0, NB).astype(np.float32)[bi], rb_.uniform(0, 6.28, NB).astype(np.float32)[bi]
    node = 0.5 + 0.5 * np.sin(fq * along * 2 * np.pi + ph)
    # wear: first thinner and inky, along the barbs; then gone
    near_rim = sstep(1.3, 0.3, rho)
    w1 = rank(fbm(shape, pxcm, 0.04, 0.45, 2.3, SEED + 3))
    w2 = rank(fbm(shape, pxcm, 0.5, 2.2, 2.6, SEED + 13))
    worn = w1 * 0.55 + w2 * 0.45 + 0.05 * near_rim + 0.022 * per_barb
    ink = sstep(0.84, 0.95, worn) * feather  # the inky violet patches of ref/diancui
    lost = sstep(0.985, 0.995, worn + 0.05 * np.exp(-dw / 0.1)) * feather  # it starts at the wire and at the tips, not in the middle of a snip
    # colour: by snip, along it and by barb
    snip = rp.uniform(0, 1, n).astype(np.float32)[lab]
    drift = rank(fbm(shape, pxcm, 0.5, 2.0, 2.4, SEED + 4))
    lam = 480 + 26 * (0.55 * snip + 0.45 * drift) + 3.6 * per_barb - 30 * ink
    amp = (1.0 + 0.16 * per_barb) * (0.82 + 0.18 * node) * (0.2 + 0.95 * ramus) * (1 - 0.55 * furrow) + 1.15 * bul_zone * bul
    amp = amp * (1 - 0.42 * ink) * sstep(0.0, 0.012, dw)
    # the rachis
    rach = is_rach * np.exp(-((u_ / (0.018 + 0.016 * sstep(3.5, 0.0, t_))) ** 2))
    amp = amp * (1 - 0.72 * rach)
    # height: barbs, cell pillow and tilt
    hf = 0.00105 * ramus + 0.0011 * bul * bul_zone - 0.0005 * furrow + 0.0004 * per_barb + 0.05 * (rach * 0.08)
    layer = np.array([0.0] + [c[4] for c in cells], np.float32)
    area = np.bincount(lab.ravel(), minlength=n).astype(np.float64) + 1
    cxs = (np.bincount(lab.ravel(), X.ravel(), minlength=n) / area).astype(np.float32)
    cys = (np.bincount(lab.ravel(), Y.ravel(), minlength=n) / area).astype(np.float32)
    tx, ty = rp.normal(0, 0.02, n).astype(np.float32), rp.normal(0, 0.02, n).astype(np.float32)
    tilt = np.clip(tx[lab] * (X - cxs[lab]) + ty[lab] * (Y - cys[lab]), -0.02, 0.02) * feather
    pillow = (1.0 - np.exp(-dw / 0.12)) * feather
    lay = blur(layer[lab], 0.007 * pxcm)
    mrough = 0.00022 * fbm(shape, pxcm, 0.03, 0.3, 2.2, SEED + 6)  # slow: high-frequency bumps on metal only make tin foil

    # --- the ground: grains soldered on one by one, some missing, some run together
    rg = np.random.default_rng(SEED + 32)
    sp = 0.046
    vs, us = np.meshgrid(np.arange(Y0, Y1, sp * 0.866), np.arange(X0, X1, sp), indexing="ij")
    us = us + 0.5 * sp * (np.round((vs - Y0) / (sp * 0.866)) % 2)
    gx_, gy_ = (us + rg.normal(0, 0.075 * sp, us.shape)).ravel(), (vs + rg.normal(0, 0.075 * sp, us.shape)).ravel()
    keep = rg.random(gx_.size) > 0.025
    gx_, gy_ = gx_[keep], gy_[keep]
    gr_ = np.clip(rg.lognormal(np.log(0.0232), 0.11, gx_.size), 0.012, 0.034).astype(np.float32)
    ix, iy = ((gx_ - X0) * pxcm).astype(int), ((gy_ - Y0) * pxcm).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    ix, iy, gr_ = ix[ok], iy[ok], gr_[ok]
    seeds = np.ones(shape, np.uint8)
    seeds[iy, ix] = 0
    dg, lg = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    rmg = np.full(int(lg.max()) + 1, 0.02, np.float32)
    rmg[lg[iy, ix]] = gr_
    rg_ = rmg[lg]
    gran = np.sqrt(np.maximum(1.0 - (dg.astype(np.float32) / pxcm / rg_) ** 2, 0.0)) * rg_ * 0.8
    per_grain = rg.random(rmg.size).astype(np.float32)[lg]
    del lg, dg, rg_
    fl = 0.55 * sstep(0.95, 0.985, rank(fbm(shape, pxcm, 0.12, 0.7, 2.2, SEED + 15)))  # too much heat: the grains ran together
    gran = gran * (1 - fl) + fl * (blur(gran, 0.018 * pxcm) * 1.1 + 0.002)
    ground = ((~feather) & (rho >= RHO_IN + 0.02)).astype(np.float32)

    # --- the whole relief
    H_w = 0.0178
    h = (lay + 0.028 * pillow + tilt + hf) * feather * (1 - 0.8 * lost)
    h = h + feather * lost * (lay - 0.002)
    h = h + ground * gran
    h = np.maximum(h, 0.0) + ground * 0.0
    base_m = blur(lay + 0.03 * sstep(0.03, 0.0, dw) * feather, 0.012 * pxcm)
    h = np.where(wire_m > 0, np.maximum(h, base_m + 0.0045 + H_w * bead), h)
    rope_h = np.maximum(0.068 * rope, 0.024 * sstep(0.06, 0.112, rho))  # solder has run into the crevice between the rope and the band
    h = np.where(rope_m > 0, np.maximum(rope_h, band_h), h)
    h = np.where(band_m > 0, np.maximum(band_h, h * 0 + band_h), h)
    metal_area = ((~feather) | (wire_m > 0)).astype(np.float32)
    scr = scratches(shape, pxcm, SEED + 50, int(1700 * (X1 - X0) * (Y1 - Y0)))
    h = h + metal_area * (mrough - 0.0009 * scr)

    # --- coral and the empty setting
    col_c = np.zeros(shape + (3,), np.float32)
    mc = np.zeros(shape, np.float32)
    for s, dd, br, there in beads():
        (bx, by) = pol(np.float64(s), R - dd)
        rb = np.hypot(X - bx, Y - by)
        collar = sstep(br * 1.38, br * 1.22, rb)
        h = np.where(collar > 0, np.maximum(h, 0.016 * collar + 0.012 * np.sqrt(np.maximum(1 - ((rb - br * 1.18) / (br * 0.2)) ** 2, 0))), h)
        metal_area = np.maximum(metal_area, collar)
        wire_m = np.maximum(wire_m, collar)
        if there:
            dome = np.sqrt(np.maximum(1.0 - (rb / br) ** 2, 0.0))
            m = sstep(br, br * 0.97, rb)
            pits = sstep(0.93, 0.985, rank(fbm(shape, pxcm, 0.003, 0.012, 1.0, SEED + 21)))
            h = np.where(m > 0, 0.03 + br * 0.92 * dome - 0.0012 * pits, h)
            mott = rank(fbm(shape, pxcm, 0.02, 0.09, 2.0, SEED + 22))
            c0 = mix(color([0.5, 0.045, 0.03]), color([0.28, 0.022, 0.018]), sstep(0.3, 0.8, mott))
            c0 = mix(c0, color([0.62, 0.3, 0.22]), 0.5 * pits)
            col_c = np.where((m > 0)[..., None], c0, col_c)
            mc = np.maximum(mc, m)
        else:
            m = sstep(br, br * 0.9, rb)
            h = np.where(m > 0, 0.004 - 0.004 * sstep(br * 0.8, 0.0, rb), h)
            col_c = np.where((m > 0)[..., None], color([0.035, 0.03, 0.025]), col_c)
            mc = np.maximum(mc, 0.9 * m)

    # --- old silver-gilt: tarnish lies in what is low, computed from the height; what stands up is rubbed through to bright
    cav = blur(h, 0.024 * pxcm) - h
    tarn_n = rank(fbm(shape, pxcm, 0.03, 0.5, 2.0, SEED + 5))
    gold = mix(color([0.96, 0.66, 0.27]), color([0.91, 0.71, 0.40]), sstep(0.3, 0.75, rank(fbm(shape, pxcm, 0.4, 2.4, 2.4, SEED + 16))))
    t_m = sstep(-0.0012, 0.005, cav) * (0.55 + 0.45 * tarn_n) + 0.3 * sstep(0.55, 0.95, tarn_n) + ground * (0.42 * sstep(0.55, 1.0, per_grain) + 0.3 * sstep(0.003, 0.0, gran))
    old = mix(gold, color([0.13, 0.095, 0.06]), np.clip(t_m, 0, 1))
    old = old * (1 - 0.35 * scr)[..., None]
    # backing: where the feather has gone, the stamped metal and a skin of old paper and glue
    glue = rank(fbm(shape, pxcm, 0.02, 0.12, 1.7, SEED + 13))
    back = mix(color([0.30, 0.235, 0.15]), color([0.5, 0.42, 0.28]), glue)
    # dust in the gutter along the wire
    dust = sstep(0.05, 0.016, dw) * sstep(0.45, 0.85, rank(fbm(shape, pxcm, 0.03, 0.3, 2.0, SEED + 14)))
    speck = sstep(0.992, 0.998, rank(fbm(shape, pxcm, 0.004, 0.014, 0.8, SEED + 23)))
    back = mix(back, color([0.34, 0.36, 0.38]), 0.8 * bul_zone * bul * (1 - lost))  # the barbules' grey on the feather; glue keeps the barbs' stripes where they have gone (MOCA report)
    back = back * (1 - 0.3 * lost * (per_barb > 0))[..., None]
    col = mix(back, old, metal_area)
    col = mix(col, col_c, mc)
    rough = 0.2 + 0.17 * tarn_n + 0.45 * sstep(0.0, 0.006, cav) + 0.22 * scr + ground * 0.2 * per_grain
    rough = rough * metal_area + 0.72 * (1 - metal_area)
    rough = rough * (1 - mc) + 0.26 * mc
    metal = metal_area * (1 - 0.65 * sstep(0.2, 0.9, t_m)) * (1 - mc)
    fm = feather.astype(np.float32) * (1 - lost) * (wire_m <= 0) * (1 - 0.32 * bul_zone * bul)
    fm = fm * (1 - mc)
    # dust and specks over the feather: not blue
    both = np.clip(0.6 * dust + speck, 0, 1)
    col = mix(col, color([0.19, 0.17, 0.14]), both)
    fm = fm * (1 - both)
    rough = rough * (1 - both) + 0.85 * both
    metal = metal * (1 - both)

    # the plate: very slight rise to the middle, slow dents, and off at the edge
    h = h + 0.012 * fbm(shape, pxcm, 0.6, 3.0, 2.8, SEED + 7) * (rho > 0.14)
    z = -(r0**2 - R**2) / (2 * 120.0) + h - sstep(0.0, 0.03, -rho) * 0.2
    alpha = sstep(0.004, 0.0, -rho)
    return (
        np.stack([X, Y, z], -1).astype(np.float32),
        np.clip(col, 0, 1).astype(np.float32),
        np.clip(rough, 0.05, 1).astype(np.float32),
        np.clip(metal, 0, 1).astype(np.float32),
        np.clip(fm, 0, 1).astype(np.float32),
        lam.astype(np.float32),
        np.maximum(amp, 0).astype(np.float32),
        alpha.astype(np.float32),
    )


def make_take():
    d = os.path.join(OUT, f"{TAKE}_move_final")
    o = os.path.join(OUT, f"{NAME}_take_cand")
    os.makedirs(o, exist_ok=True)
    for f in os.listdir(o):
        os.remove(os.path.join(o, f))
    from darkroom import develop as dev

    dv = __import__("json").load(open(os.path.join(d, "develop.json")))
    for i, f in enumerate(sorted(x for x in os.listdir(d) if x.endswith(".npy"))):
        im = dev(np.load(os.path.join(d, f)).astype(np.float32), **{**dv, "seed": 700 + i})
        u8 = (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1]
        cv2.imwrite(os.path.join(o, f"f{i:03d}.png"), u8)
        cv2.imwrite(os.path.join(o, f"f{i:03d}.jpg"), u8, [cv2.IMWRITE_JPEG_QUALITY, 94])
    __import__("json").dump(dv, open(os.path.join(o, "develop.json"), "w"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(o, "f%03d.png"), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", os.path.join(o, "take.mp4")], check=True)
    print(os.path.join(o, "take.mp4"))


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "flat":
        flat_view()
        return
    if q == "take":
        make_take()
        return
    name = NAME
    moving = bool(os.environ.get("GEWU_MOVE"))
    if moving:
        orig = kit.looks
        mv = dict(orig()[NAME]["move"])  # the shot's own move: the light travels, the same way and the same distance
        mv.update(frames=FRAMES, spp=mv.get("spp", 192))
        mv["lights"] = {**mv["lights"], "rake": [7.0, 0.0, 0.0]}  # less rake travel than the looks entry (12.86): at this distance the end of the old sweep veiled the feather
        kit.looks = lambda: {**orig(), TAKE: {"move": mv}}
        name = TAKE
    dens = {"preview": 0.45, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cam, focus = camera()
    P, C, Ro, Me, Fm, Lam, Amp, A = build(cam, dens)
    npz = os.path.join(d, f"mesh.cand.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=Me, fm=Fm, lam=Lam, amp=Amp, alpha=A)
    lw, _ = reflect_light_loc(focus, np.array([0.0, 0.0, 1.0]), cam, 50.0)
    scene = {
        "camera": cam,
        "meshes": [
            {
                "name": "ornament",
                "npz": npz,
                "shader_py": os.path.join(os.path.dirname(os.path.abspath(__file__)), "diancui_shader.py"),
                "params": {"ramp": RAMP, "n": 1.45, "cos0": float(np.sin(np.radians(EL))), "k_shift": 0.6, "rough": 0.46, "k_scatter": 0.62, "k_cuticle": 0.11, "rough_c": 0.34},
            }
        ],
        "lights": [
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": focus.tolist(), "size": [130, 100], "sigma": [40, 20], "L": 0.42, "rgb": [1.0, 0.98, 0.94]},
            {"name": "rake", "loc": (focus + np.array([-22, 20, 14])).tolist(), "target": focus.tolist(), "size": [6, 6], "watts": 5000, "rgb": [1.0, 0.94, 0.84]},
            {"name": "fill", "loc": (focus + np.array([14, -22, 26])).tolist(), "target": focus.tolist(), "size": [30, 30], "watts": 2600, "rgb": [1.0, 0.98, 0.96], "hide_in_gloss": True},
        ],
        "env": {"window": 1.4, "win_az": -30.0, "win_el": 40.0, "win_w": 30.0, "win_h": 34.0, "strip": 0.6, "ceil": 0.3, "wall": 0.05},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": 0.42, "seed": 55},
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 2,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot(name, scene, q, tag="cand" if q == "final" else None, develop={"exposure": 0.0, "contrast": 1.2, "saturation": 1.02, "black": 0.0012, "grain": 1.15, "sharpen": 0.25, "halation": 0.05, "glare": 0.004, "vignette": 0.25})


main()
