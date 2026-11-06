"""Shot 7: 磁青纸泥金写经. Gold paint on indigo paper: real small regular script, the Heart Sutra in Xuanzang's translation, in a low raking light. No move: one still.

    python3 -I v2/stills/s07_cijing.py flat               # local, seconds: the layout, and a 100% crop lit with a toy shader
    python3 -I v2/stills/s07_cijing.py [preview|mid|final] # All go to cand.*: never final.*

Third version. The second was Liu Hui's circle, ruled in gold: good paper, but gold lines in a figure read as a diagram. Paper fields and the stroke renderer for ruled lines are kept from it.

TEXT. Checked against CBETA T08n0251 (fetched from cbdata.dila.edu.tw, stable/juans?work=T0251&juan=1), punctuation removed. Traditional forms as in Taisho. Layout is checked by writing layout.json.
FONT. cwTeX Q Kai ZH Medium (cwTeX Q 楷體), SIL Open Font License 1.1, Tsong-Min Wu, Tsong-Huey Wu, Edward G.J. Lee, Chen-Pan Liao; a Chinese regular script. File from github.com/l10n-tw/cwtex-q-fonts-TTFs ttf/cwTeXQKaiZH-Medium.ttf,
    upstream github.com/l10n-tw/cwtex-q-fonts. In v2/fonts/, licence beside it. It has every character of the sutra; the script still stops with an error if a character in the layout is missing. Earlier version with Yuji Syuku (Japanese forms) was replaced.
HAND. The font only gives the skeleton. Each character gets its own: size, shear, placement, a slow warp, each separate stroke-group moved a little, weight varying inside the character. A brush load runs through the column,
    falling character by character and re-dipped. Where loaded the paint pools at stroke ends and junctions; where dry it breaks into streaks along the stroke (orientation from the structure tensor of the character).
PAINT. A body with height: bead across the stroke, a rim of pushed-out powder, furrows from the hairs along the stroke; then a surface of small clots, each a flat with its own tilt, with burnished runs. The height goes into the mesh.
SHAPE. The sheet is bent in one direction only, as paper bends: a shallow cylinder with its axis running along the columns, away from the camera. Its far edge is the arc. Roll-set ripples run along the columns (the sheet has been kept rolled).

Measured: nothing of a real manuscript. Text checked as above. Estimates from general knowledge of sutra copying, not measured: column pitch, character size (写经 about 1.5-1.9 cm pitch, 17 to a column, this one tighter), paint height (tens of microns).
Assumption: gold-on-indigo sutra paper is burnished enough to take a broad sheen. Height is exaggerated a little if at all; not calibrated.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize

from kit import OUT, ROOT, _cam_axes, blur, color, fbm, frame_camera, mix, rank, shoot, sstep

NAME = "s07_cijing"
FONT = os.path.join(ROOT, "v2", "fonts", "cwTeXQKaiZH-Medium.ttf")

TITLE = "般若波羅蜜多心經"
BY = "唐三藏法師玄奘譯"
BODY = (
    "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
    "舍利子色不異空空不異色色即是空空即是色受想行識亦復如是"
    "舍利子是諸法空相不生不滅不垢不淨不增不減"
    "是故空中無色無受想行識無眼耳鼻舌身意無色聲香味觸法無眼界乃至無意識界"
    "無無明亦無無明盡乃至無老死亦無老死盡無苦集滅道無智亦無得"
)  # continues 以無所得故菩提薩埵..., out of frame, so not written here

SEED = 7
COL = 1.12  # column pitch, cm (estimate)
ROW = 0.84  # character pitch along the column
EM = 0.72  # character size
PER_COL = 17
RULE_DIM = 0.55  # brightness of the rules against the writing, by eye
TPX = 500.0  # px/cm of the character tiles: fixed, so the characters do not change with quality

R = 19.0  # the bend of the sheet, cm
ELEV = np.radians(31.0)
YAW = np.radians(-5.0)  # the camera is a little off the column direction: flat work is not shot square
W = 11.6  # frame width at the target
DIST = 27.0
APEX_V = 0.455  # far edge of the sheet in the frame, from the top. The caption is at .37 and at most .42 is allowed
APERTURE = 11.0  # mm
X0, X1 = -6.6, 8.6  # the sheet's extent that is meshed, cm
Y1 = 5.0  # far edge
Y0 = -3.0
TOP = Y1 - 1.2  # the top rule; above it is the blank head of the sheet (天头)
X_TITLE = 4.75  # first column; columns go to the left (x falls)
FOCUS = (-0.3, TOP - 2.6)  # paper coordinates of the point in focus


def columns():
    """[(column index, 17 slots of char or None)], right to left."""
    cols = [list(TITLE) + [None] * (PER_COL - len(TITLE)), [None] * 8 + list(BY) + [None]]
    for i in range(0, len(BODY), PER_COL):
        s = BODY[i : i + PER_COL]
        cols.append(list(s) + [None] * (PER_COL - len(s)))
    return cols


def fibres(shape, pxcm, per_cm2, lo, hi, seed):
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 * per_cm2)
    a = rng.uniform(0, np.pi, n)
    length = rng.uniform(lo, hi, n) * pxcm / 5.0
    px, py = rng.uniform(0, nx, n), rng.uniform(0, ny, n)
    pts = [np.stack([px, py], -1)]
    for _ in range(5):
        a = a + rng.normal(0, 0.28, n)
        px, py = px + length * np.cos(a), py + length * np.sin(a)
        pts.append(np.stack([px, py], -1))
    canvas = np.zeros(shape, np.uint8)
    cv2.polylines(canvas, list(np.round(np.stack(pts, 1) * 8).astype(np.int32)), False, 255, 1, cv2.LINE_AA, shift=3)
    return canvas.astype(np.float32) / 255.0


def slow(rng, n, knots, amp):
    """A smooth random curve of n samples."""
    return amp * np.interp(np.linspace(0, 1, n), np.linspace(0, 1, knots), rng.normal(0, 1, knots)) if amp else np.zeros(n)


# --- the rules (乌丝栏 in gold), stroke by stroke with a brush along a bamboo ruler --------------------------------------
def rule_strokes(ncol):
    rng = np.random.default_rng(SEED)
    out = []

    def ruled(p0, p1, hw, load0, run):
        p0, p1 = np.array(p0, float), np.array(p1, float)
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        n_ = np.array([-d[1], d[0]])
        p0 = p0 + n_ * rng.normal(0, 0.012) - d * rng.normal(0.012, 0.03)
        p1 = p1 + n_ * rng.normal(0, 0.012) + d * rng.normal(0.0, 0.03)
        L = np.linalg.norm(p1 - p0)
        m = max(int(L * 110), 24)
        t = np.linspace(0, 1, m)
        bow = slow(rng, m, 5, 0.006)
        pts = p0 + (p1 - p0) * t[:, None] + n_ * (bow + slow(rng, m, max(int(L * 7), 4), 0.003))[:, None]
        # the hair is re-dipped along a long rule, so the load saws
        phase = (t * L / rng.uniform(5.5, 8.0) + rng.random()) % 1.0
        load = load0 * (1.0 - run * phase) + slow(rng, m, max(int(L * 3), 3), 0.05)
        w = hw * (0.82 + 0.34 * np.exp(-t / 0.02) + 0.3 * load + slow(rng, m, max(int(L * 6), 4), 0.09))
        w = w * (1.0 - 0.45 * sstep(0.985, 1.0, t))
        out.append((pts, w, np.clip(load, 0.04, 1.0)))

    bot = TOP - PER_COL * ROW - 0.25
    xr = X_TITLE + COL * 0.5
    for k in range(-2, ncol + 1):
        x = xr - k * COL
        if x < X0 - 0.5 or x > X1 + 0.5:
            continue
        ruled((x, TOP + rng.normal(0.01, 0.02)), (x, bot), 0.0066 * rng.uniform(0.85, 1.15), rng.uniform(0.6, 0.85), 0.55)
    xl = xr - (ncol + 1) * COL
    ruled((xr + 2 * COL, TOP + 0.002), (xl, TOP - 0.004), 0.0115, 0.9, 0.5)
    ruled((xr + 2 * COL, TOP + 0.085), (xl, TOP + 0.08), 0.0055, 0.65, 0.5)
    return out


# --- one character ----------------------------------------------------------------------------------------------------
def _smooth_noise(rng, shape, wave_px):
    n = rng.normal(0, 1, shape).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), wave_px)
    return n / (n.std() + 1e-6)


def character(ch, font, rng, load0, size):
    """The character as paint: thickness Th (about 0..2) and dryness, on a tile of TPX px/cm, centred. It is its own: nothing is shared between two copies of the same character."""
    ts = int(1.3 * EM * TPX)
    big = 2 * ts
    im = Image.new("L", (big, big), 0)
    ImageDraw.Draw(im).text((big / 2, big / 2), ch, fill=255, font=font, anchor="mm")
    m = np.asarray(im, np.uint8)
    if m.max() == 0:
        raise SystemExit(f"blank glyph for {ch}")
    # --- each separate group of strokes was written on its own, so it sits a little off
    nlab, lab, stats, cent = cv2.connectedComponentsWithStats((m > 127).astype(np.uint8), connectivity=8)
    if nlab > 2:
        out = np.zeros_like(m)
        for i in range(1, nlab):
            if stats[i, cv2.CC_STAT_AREA] < 30:
                continue
            piece = cv2.dilate((lab == i).astype(np.uint8), np.ones((3, 3), np.uint8)) * m
            a = rng.normal(0, 1.5)
            s = 1.0 + rng.normal(0, 0.022)
            M = cv2.getRotationMatrix2D((float(cent[i, 0]), float(cent[i, 1])), a, s)
            M[:, 2] += rng.normal(0, 0.011 * EM * TPX * 2, 2)
            out = np.maximum(out, cv2.warpAffine(piece, M, (big, big), flags=cv2.INTER_LINEAR))
        m = out
    # --- the whole character: size, lean, a horizontal that climbs, a slow wander
    M = cv2.getRotationMatrix2D((big / 2, big / 2), rng.normal(0.3, 1.1), 1.0)
    sx, sy = size * (1 + rng.normal(0, 0.022)), size * (1 + rng.normal(0, 0.03))
    shy, shx = rng.normal(-0.018, 0.016), rng.normal(0, 0.016)
    A = M[:, :2] @ np.array([[sx, shx], [shy, sy]])
    M = np.column_stack([A, np.array([big / 2, big / 2]) - A @ np.array([big / 2, big / 2])])
    m = cv2.warpAffine(m, M, (big, big), flags=cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:big, 0:big].astype(np.float32)
    px = EM * TPX * 2
    dx = 0.013 * px * _smooth_noise(rng, (big, big), 0.22 * px) + 0.004 * px * _smooth_noise(rng, (big, big), 0.07 * px)
    dy = 0.013 * px * _smooth_noise(rng, (big, big), 0.22 * px) + 0.004 * px * _smooth_noise(rng, (big, big), 0.07 * px)
    m = cv2.remap(m, xx + dx, yy + dy, cv2.INTER_LINEAR)
    m = cv2.resize(m, (ts, ts), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    # --- signed distance, cm. Weight changes across the character: the hand presses and lifts
    binm = (m > 0.5).astype(np.uint8)
    din = cv2.distanceTransform(binm, cv2.DIST_L2, 5).astype(np.float32)
    dout = cv2.distanceTransform(1 - binm, cv2.DIST_L2, 5).astype(np.float32)
    sd = cv2.GaussianBlur(din - dout + (m - 0.5), (0, 0), 1.0) / TPX
    press = rng.normal(0.0, 0.0022) + 0.0052 * _smooth_noise(rng, (ts, ts), 0.2 * EM * TPX) + 0.0016 * _smooth_noise(rng, (ts, ts), 0.05 * EM * TPX)
    sd = np.maximum(sd + press, np.where(sd > 0, 0.6 * sd, -1.0))  # this font's hairlines are thin: the hand lifts, but a stroke never vanishes
    mask = sd > 0
    if mask.sum() < 40:
        raise SystemExit(f"{ch}: nothing left of the character")
    # --- along the stroke: the structure tensor of the shape
    sm = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 4.0)
    gx, gy = cv2.Sobel(sm, cv2.CV_32F, 1, 0), cv2.Sobel(sm, cv2.CV_32F, 0, 1)
    jxx, jyy, jxy = [cv2.GaussianBlur(q, (0, 0), 12.0) for q in (gx * gx, gy * gy, gx * gy)]
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
    ux, uy = np.cos(ang), np.sin(ang)
    # hair streaks: white noise drawn out along the stroke
    y2, x2 = np.mgrid[0:ts, 0:ts].astype(np.float32)
    n0 = _smooth_noise(rng, (ts, ts), 1.6)
    acc = np.zeros((ts, ts), np.float32)
    for t in range(-34, 35, 4):
        acc += cv2.remap(n0, x2 + t * ux, y2 + t * uy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    inside = acc[mask]
    streak = np.clip(((acc - inside.mean()) / (inside.std() + 1e-6)) * 0.28 + 0.5, 0, 1)
    # --- ends and junctions of the skeleton: paint collects, or the brush leaves dry
    sk = skeletonize(sd > 0.004).astype(np.uint8)
    nb = cv2.filter2D(sk, cv2.CV_16S, np.ones((3, 3), np.int16), borderType=cv2.BORDER_CONSTANT) - sk
    ends = np.argwhere((sk > 0) & (nb == 1))
    junc = np.argwhere((sk > 0) & (nb >= 3))
    pile = np.zeros((ts, ts), np.float32)
    drytail = np.zeros((ts, ts), np.float32)
    sigma_of = lambda p: max(float(sd[p[0], p[1]]), 0.012) * TPX * 1.05
    # dots drawn into an image and blurred per class of radius, instead of one Gaussian each
    for pts, amp_lo, amp_hi, pdry in ((ends, 0.25, 1.0, 0.34), (junc[:: max(1, len(junc) // 8 + 1)], 0.15, 0.45, 0.0)):
        for p in pts:
            s = sigma_of(p)
            r = int(3 * s) + 1
            y0, y1, x0, x1 = max(p[0] - r, 0), min(p[0] + r + 1, ts), max(p[1] - r, 0), min(p[1] + r + 1, ts)
            gy_, gx_ = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            g = np.exp(-((gy_ - p[0]) ** 2 + (gx_ - p[1]) ** 2) / (2 * s * s))
            if rng.random() < pdry:
                drytail[y0:y1, x0:x1] = np.maximum(drytail[y0:y1, x0:x1], g * rng.uniform(0.5, 1.0))
            else:
                pile[y0:y1, x0:x1] += g * rng.uniform(amp_lo, amp_hi)
    # --- the load inside the character: the first strokes (top, left) are wetter
    nx_, ny_ = (x2 - ts / 2) / (EM * TPX), (y2 - ts / 2) / (EM * TPX)
    load = load0 * (1.0 - 0.16 * (nx_ + ny_) + 0.14 * _smooth_noise(rng, (ts, ts), 0.16 * EM * TPX))
    dry = np.clip(sstep(0.56, 0.26, load) + 0.7 * drytail, 0, 1)
    # where it is dry the body only stays on some hairs' tracks
    width = cv2.dilate(np.maximum(sd, 0), np.ones((21, 21), np.uint8))  # half width of the stroke here
    thr = dry * 0.4 * sstep(0.009, 0.024, width)  # never so much that the character cannot be read: a thin stroke stays whole
    cover = sstep(thr - 0.07, thr + 0.07, streak) if thr.max() > 0 else np.ones((ts, ts), np.float32)
    cover = np.where(dry < 0.02, 1.0, cover).astype(np.float32)
    # --- the body
    d = np.maximum(sd, 0)
    bead = np.sqrt(np.clip(1.0 - (1.0 - np.minimum(d / 0.026, 1.0)) ** 2, 0, 1))
    rim = np.exp(-(((d - 0.0065) / 0.0055) ** 2))
    body = bead * (0.52 + 0.62 * np.clip(load, 0, 1)) * (1.0 + 0.32 * (streak - 0.5)) + 0.26 * rim * np.clip(load, 0, 1)
    body = body + 0.85 * bead * pile * np.clip(load + 0.2, 0, 1.1)
    Th = body * cover * mask
    return Th.astype(np.float32), (dry * mask).astype(np.float32)


def characters(pxcm, X0_, X1_, Y0_, Y1_, Th, Dry, want_layout=None):
    """Write every character whose cell is on the grid into Th and Dry. In order of writing: the load of the brush runs on through the column."""
    if not os.path.exists(FONT):
        raise SystemExit(f"missing font {FONT}; see the head of this file for its source and licence")
    font = ImageFont.truetype(FONT, int(EM * TPX * 2))
    from fontTools.ttLib import TTFont

    cmap = TTFont(FONT).getBestCmap()
    rng = np.random.default_rng(SEED + 21)
    ny, nx = Th.shape
    s = pxcm / TPX
    load = 1.0
    layout = []
    for ci, slots in enumerate(columns()):
        x_base = X_TITLE - ci * COL + rng.normal(0, 0.012)
        k = rng.uniform(-0.009, 0.009)  # the column as a whole drifts off the rule, slowly
        wander = slow(rng, PER_COL, 6, 0.022)
        y = TOP - 0.1 + rng.normal(0.0, 0.02)
        for ri, ch in enumerate(slots):
            pitch = ROW * (1 + rng.normal(0, 0.018))
            y -= pitch / 2
            cx, cy = x_base + k * ri + wander[ri] + rng.normal(0, 0.012), y + rng.normal(0, 0.012)
            y -= pitch / 2
            big = 1.0 + rng.normal(0, 0.038)
            lo = load
            # always draw from the random stream, on or off the grid: a crop has the same hand
            tile_rng = np.random.default_rng([SEED, ci, ri])
            if ch is None:
                continue
            load -= rng.uniform(0.045, 0.1)
            if load < rng.uniform(0.3, 0.45):
                load = rng.uniform(0.92, 1.1)
            on = X0_ - 0.6 < cx < X1_ + 0.6 and Y0_ - 0.6 < cy < Y1_ + 0.6
            layout.append({"col": ci, "row": ri, "ch": ch, "x": round(float(cx), 3), "y": round(float(cy), 3), "load": round(float(lo), 3), "meshed": bool(on)})
            if not on:
                continue
            if ord(ch) not in cmap:
                raise SystemExit(f"{ch} is not in {FONT}: the frame reaches a character this font cannot write")
            t, dr = character(ch, font, tile_rng, lo, big)
            if s < 1:
                sig = 0.45 / s
                t, dr = cv2.GaussianBlur(t, (0, 0), sig), cv2.GaussianBlur(dr, (0, 0), sig)
            ts = t.shape[0]
            wpx, hpx = ts * s, ts * s
            gx0, gy0 = (cx - X0_) * pxcm - wpx / 2, (Y1_ - cy) * pxcm - hpx / 2
            ix0, iy0 = int(np.floor(gx0)), int(np.floor(gy0))
            ix1, iy1 = int(np.ceil(gx0 + wpx)) + 1, int(np.ceil(gy0 + hpx)) + 1
            jx0, jy0, jx1, jy1 = max(ix0, 0), max(iy0, 0), min(ix1, nx), min(iy1, ny)
            if jx0 >= jx1 or jy0 >= jy1:
                continue
            M = np.array([[s, 0, gx0 - jx0], [0, s, gy0 - jy0]], np.float32)
            sz = (jx1 - jx0, jy1 - jy0)
            Th[jy0:jy1, jx0:jx1] = np.maximum(Th[jy0:jy1, jx0:jx1], cv2.warpAffine(t, M, sz, flags=cv2.INTER_CUBIC))
            Dry[jy0:jy1, jx0:jx1] = np.maximum(Dry[jy0:jy1, jx0:jx1], cv2.warpAffine(dr, M, sz, flags=cv2.INTER_LINEAR))
    return layout


# --- the sheet ----------------------------------------------------------------------------------------------------------
def build(dens, roi=None):
    pxcm = 300.0 * dens
    x0, x1, y0, y1 = roi or (X0, X1, Y0, Y1)
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M", flush=True)
    x = x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    y = y1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)

    # --- the paper: indigo, burnished; pale fibres take less dye (as the second version)
    flocs = fbm(shape, pxcm, 0.04, 0.5, 2.2, SEED)
    fib = blur(fibres(shape, pxcm, 170, 0.2, 0.9, SEED + 1), max(0.7 * dens, 0.45))
    fib2 = blur(fibres(shape, pxcm, 500, 0.03, 0.14, SEED + 2), max(0.5 * dens, 0.4))
    dye = rank(fbm(shape, pxcm, 0.5, 6.0, 2.6, SEED + 3))
    dye2 = fbm(shape, pxcm, 0.02, 0.15, 1.8, SEED + 4)
    pap = mix(color([0.0035, 0.009, 0.05]), color([0.006, 0.017, 0.08]), dye)
    pap = pap * (1.0 + 0.14 * dye2[..., None] + 1.5 * fib[..., None] + 0.6 * fib2[..., None])
    pap = pap + (fib * 0.012)[..., None] * color([0.4, 0.55, 1.0])
    tooth = (0.7 * rank(flocs) + 0.5 * np.clip(fib + 0.5 * fib2, 0, 1)).astype(np.float32)

    Th = np.zeros(shape, np.float32)
    Dry = np.zeros(shape, np.float32)
    wobble = fbm(shape, pxcm, 0.012, 0.09, 1.6, SEED + 9)
    wob2 = fbm(shape, pxcm, 0.002, 0.012, 1.2, SEED + 10)

    # --- the rules
    cols = columns()
    for pts, w, load in rule_strokes(len(cols)):
        mg = 0.16
        bx0, bx1 = int((pts[:, 0].min() - mg - x0) * pxcm), int((pts[:, 0].max() + mg - x0) * pxcm) + 1
        by0, by1 = int((y1 - pts[:, 1].max() - mg) * pxcm), int((y1 - pts[:, 1].min() + mg) * pxcm) + 1
        bx0, by0 = max(bx0, 0), max(by0, 0)
        bx1, by1 = min(bx1, nx), min(by1, ny)
        if bx0 >= bx1 or by0 >= by1:
            continue
        px = (pts[:, 0] - x0) * pxcm - bx0
        py = (y1 - pts[:, 1]) * pxcm - by0
        canvas = np.zeros((by1 - by0, bx1 - bx0), np.int32)
        ipts = np.round(np.stack([px, py], 1) * 16).astype(np.int32)
        for i in range(len(pts) - 1):
            cv2.line(canvas, tuple(int(v) for v in ipts[i]), tuple(int(v) for v in ipts[i + 1]), int(i + 1), 1, cv2.LINE_8, shift=4)
        if canvas.max() == 0:
            continue
        seed_mask = (canvas == 0).astype(np.uint8)
        d, lab = cv2.distanceTransformWithLabels(seed_mask, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        zeros = seed_mask == 0
        ids = np.zeros(lab.max() + 2, np.int32)
        ids[lab[zeros]] = canvas[zeros] - 1
        near = ids[lab]
        d = d.astype(np.float32) / pxcm
        wn, ln = w[near].astype(np.float32), load[near].astype(np.float32)
        sub = (slice(by0, by1), slice(bx0, bx1))
        edge = wn * (1.0 + (0.14 * wobble[sub] + 0.05 * wob2[sub]) * (0.7 + 0.5 * ln))
        prof = np.sqrt(np.clip(1.0 - (d / np.maximum(edge, 1e-4)) ** 2, 0.0, 1.0))
        dryness = sstep(0.42, 0.1, ln)
        skip = sstep(0.12, 0.4, tooth[sub] + 0.22 * wobble[sub] + 0.9 * ln + 0.08)
        amount = prof * (0.45 + 0.6 * ln) * (1.0 - dryness * (1.0 - skip))
        Th[sub] = Th[sub] + amount
        Dry[sub] = np.maximum(Dry[sub], dryness * (amount > 0.01))

    Rule = sstep(0.0, 0.05, Th)  # the rules are a thinner, duller paint than the writing: they must not outshine it

    # --- the characters
    layout = characters(pxcm, x0, x1, y0, y1, Th, Dry)
    json.dump(layout, open(os.path.join(OUT, NAME, "layout.json"), "w"), ensure_ascii=False, indent=0)

    # --- wet paint levels a little: only a short way, the rim and the furrows stay; it creeps along the paper's tooth
    Th = 0.68 * Th + 0.32 * blur(Th, 0.006 * pxcm)
    cover = sstep(0.09, 0.2, Th + 0.05 * wob2 + 0.03 * wobble)
    tide = blur(Th, 0.014 * pxcm)
    tide_a = sstep(0.05, 0.3, tide) * (1 - cover) * 0.3

    # --- the dried surface: clots, each a small flat with its own tilt, seen only under a raking light
    rs = np.random.default_rng(SEED + 11)
    seeds = np.ones(shape, np.uint8)
    n_seed = int(nx * ny / (pxcm * 0.014) ** 2)
    sx_, sy_ = rs.integers(0, nx, n_seed), rs.integers(0, ny, n_seed)
    seeds[sy_, sx_] = 0
    _, lb = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    sr, sc = np.nonzero(seeds == 0)
    n_lb = len(sr) + 2
    cxs = np.concatenate([[0], x[sc], [0]]).astype(np.float32)
    cys = np.concatenate([[0], y[sr], [0]]).astype(np.float32)
    mag = rs.lognormal(0, 0.7, n_lb).astype(np.float32)
    tx, ty = rs.normal(0, 0.11, n_lb).astype(np.float32) * mag, rs.normal(0, 0.11, n_lb).astype(np.float32) * mag
    lift = rs.normal(0, 0.0007, n_lb).astype(np.float32) * mag
    facets = tx[lb] * (X - cxs[lb]) + ty[lb] * (Y - cys[lb]) + lift[lb]
    del seeds
    clump = fbm(shape, pxcm, 0.012, 0.07, 1.7, SEED + 12)
    burn = rank(fbm(shape, pxcm, 0.25, 1.4, 2.6, SEED + 13))
    burnish = sstep(0.64, 0.82, burn) * (1 - 0.8 * Dry)  # the agate went over some runs
    hue = rank(fbm(shape, pxcm, 0.02, 0.25, 1.9, SEED + 14))
    gold = mix(color([0.82, 0.5, 0.16]), color([0.97, 0.7, 0.3]), hue)
    gold = mix(gold, gold * RULE_DIM, Rule)
    thin = sstep(0.62, 0.12, Th)
    gold = mix(gold, color([0.55, 0.3, 0.09]), thin * 0.7)
    fleck = sstep(0.86, 0.97, rank(fbm(shape, pxcm, 0.006, 0.03, 1.1, SEED + 15))) * (1 - burnish)

    near_line = blur((Th > 0.2).astype(np.float32), 0.04 * pxcm)
    cl = sstep(0.7, 0.95, rank(fbm(shape, pxcm, 0.15, 0.8, 2.2, SEED + 16)))
    stray = (rs.random(shape, dtype=np.float32) < 0.007 * cl * sstep(0.02, 0.2, near_line) * (0.55 / max(dens, 0.1)) ** 2).astype(np.float32)
    stray += (rs.random(shape, dtype=np.float32) < 0.0003 * sstep(0.0, 0.05, near_line) * (0.55 / max(dens, 0.1)) ** 2).astype(np.float32)
    stray = sstep(0.05, 0.3, blur(stray, max(0.9 * dens, 0.6)))

    paint = np.clip(cover + stray * (1 - cover), 0, 1)
    pa = np.clip(paint + tide_a, 0, 1)
    col = mix(pap, mix(gold, color([0.25, 0.12, 0.03]), tide_a / (pa + 1e-3) * (1 - paint)), pa)
    rough = 0.36 + (0.08 + 0.14 * fleck - 0.2 * burnish - 0.08 * sstep(0.5, 1.5, mag[lb]) + 0.16 * Rule) * paint + 0.04 * dye2
    h = 0.0009 * flocs + 0.0014 * fib + 0.0005 * fib2
    relief = cover * 0.0052 * np.minimum(Th, 2.6) + cover * (1 - 0.7 * burnish) * (facets + 0.00055 * clump + 0.0003 * fleck)
    h = h + relief + stray * 0.0012
    metal = np.clip(paint * (0.88 + 0.12 * burnish), 0, 1)

    # --- bend. The ripple comes from fields stretched along the columns, so a low one runs the length of the sheet
    k = max(int(pxcm * 0.25), 1)
    sn = (max(ny // (5 * k), 8), max(nx // k, 8))
    rip = fbm(sn, pxcm / k, 0.9, 4.0, 2.6, SEED + 31)
    rip = blur(cv2.resize(rip, (nx, ny), interpolation=cv2.INTER_CUBIC), k * 0.8)
    cock = fbm((max(ny // k, 8), max(nx // k, 8)), pxcm / k, 0.7, 7.0, 2.6, SEED + 32)
    cock = blur(cv2.resize(cock, (nx, ny), interpolation=cv2.INTER_CUBIC), k * 0.8)
    Z = 0.012 * rip + 0.012 * cock
    # the far edge of the sheet: it wanders and is worn; a straight cut would be a line drawn by a computer
    xs = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm + x0
    r2 = np.random.default_rng(SEED + 33)
    e = np.zeros(nx, np.float32)
    for wv, am in ((3.0, 0.035), (0.8, 0.012), (0.2, 0.005), (0.05, 0.0018)):
        kn = max(int((x1 - x0) / wv), 4)
        e += am * np.interp(np.linspace(0, 1, nx), np.linspace(0, 1, kn), r2.normal(0, 1, kn)).astype(np.float32)
    worn = sstep(0.22, 0.0, (y1 - Y) + 0.02 * wobble)
    Ym = Y + e[None, :] * sstep(y1 - 0.6, y1, Y)
    col = mix(col, col * 1.0 + color([0.012, 0.017, 0.035]), worn * 0.8)
    th = (X + 0.0) / R
    nxv, nzv = np.sin(th), np.cos(th)
    Px = R * nxv + (h + Z) * nxv
    Pz = R * (nzv - 1.0) + (h + Z) * nzv
    P = np.stack([Px, Ym, Pz], -1).astype(np.float32)
    fields = {"h": h, "paint": paint, "metal": metal, "pxcm": pxcm}
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), metal.astype(np.float32), fields, layout


def surface(x, y):
    th = x / R
    return np.array([R * np.sin(th), y, R * (np.cos(th) - 1.0)])


def project(cam, p):
    """Frame coordinates (from the top left, 0..1) of a world point. Assumes no sensor shift."""
    right, up, back = _cam_axes(cam)
    rel = np.array(p, float) - np.array(cam["loc"], float)
    zc = -rel @ back
    f = cam["lens_mm"] / 36.0
    return 0.5 + f * (rel @ right) / zc, 0.5 - f * (rel @ up) / zc * 16.0 / 9.0


def camera():
    """Find the target by iteration, so that the far edge's highest point falls at APEX_V, centred."""
    view = np.array([np.sin(YAW) * np.cos(ELEV), -np.cos(YAW) * np.cos(ELEV), np.sin(ELEV)])
    tgt = surface(FOCUS[0], FOCUS[1])
    xs = np.linspace(X0, X1, 200)
    edge = np.stack([surface(v, Y1) for v in xs])
    for _ in range(6):
        cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=surface(*FOCUS))
        right, up, _b = _cam_axes(cam)
        vs = np.array([project(cam, p) for p in edge])
        i = np.argmin(vs[:, 1])
        tgt = tgt + right * (vs[i, 0] - 0.5) * W + up * (APEX_V - vs[i, 1]) * (W * 9.0 / 16.0)
    cam = frame_camera(tgt, view, W, DIST, aperture_mm=APERTURE, focus_point=surface(*FOCUS))
    return cam


def report(cam, layout):
    """Where the far edge is, what is in frame: computed from the camera, not looked at."""
    xs = np.linspace(X0, X1, 400)
    vs = np.array([project(cam, surface(v, Y1)) for v in xs])
    inframe = (vs[:, 0] >= 0) & (vs[:, 0] <= 1)
    print(f"arc: apex v {vs[:, 1].min():.3f} at u {vs[np.argmin(vs[:, 1]), 0]:.3f}; at frame edges v {vs[inframe, 1][0]:.3f} {vs[inframe, 1][-1]:.3f}; x range in frame at far edge {xs[inframe][0]:.2f} {xs[inframe][-1]:.2f}")
    # the bottom of the frame on the paper
    right, up, back = _cam_axes(cam)
    loc = np.array(cam["loc"])
    f = cam["lens_mm"] / 36.0
    for u_, v_ in ((0.0, 1.0), (1.0, 1.0)):
        ray = -back + right * (u_ - 0.5) / f + up * (0.5 - v_) * (9.0 / 16.0) / f
        t = -loc[2] / ray[2]
        print("frame corner on z=0:", (loc + ray * t).round(2))
    rows = {}
    for c in layout:
        u, v = project(cam, surface(c["x"], c["y"]))
        if 0 <= u <= 1 and 0 <= v <= 1:
            rows.setdefault(c["col"], []).append(c["ch"])
    for k in sorted(rows):
        print(f"  column {k}: {''.join(rows[k])}")
    print(f"topmost character v: {min(project(cam, surface(c['x'], c['y']))[1] for c in layout):.3f}")


def flat():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    # the middle of the writing at full mesh density
    roi = (-2.6, 2.4, TOP - 5.4, TOP + 0.5)
    P, C, Ro, M, F, layout = build(1.0, roi)
    h, pxcm = F["h"], F["pxcm"]
    gy, gx = np.gradient(h, 1.0 / pxcm)
    n = np.stack([-gx, gy, np.ones_like(h)], -1)  # image rows run -y
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.72, 0.55, 0.42])
    L /= np.linalg.norm(L)
    V = np.array([0.0, -0.3, 0.95])
    V /= np.linalg.norm(V)
    H = (L + V) / np.linalg.norm(L + V)
    diff = np.clip(n @ L, 0, 1)[..., None]
    hh = np.clip(n @ H, 0, 1)
    a = np.maximum(Ro**2, 0.02)
    D = a**2 / (np.pi * ((hh**2) * (a**2 - 1) + 1) ** 2)
    spec = (D * 0.8)[..., None]
    img = C * diff * (1 - M[..., None]) * 3.0 + C * M[..., None] * (spec * 0.9 + 0.06) + 0.03 * spec * (1 - M[..., None])
    img = np.clip(img, 0, 1) ** (1 / 2.2)
    im8 = (img[..., ::-1] * 255).astype(np.uint8)
    cv2.imwrite(os.path.join(d, "flat.jpg"), im8, [cv2.IMWRITE_JPEG_QUALITY, 93])
    # the plain paint map too, for reading the characters
    pm = (np.clip(F["paint"], 0, 1) * 255).astype(np.uint8)
    cv2.imwrite(os.path.join(d, "flat_paint.jpg"), pm, [cv2.IMWRITE_JPEG_QUALITY, 90])
    report(camera(), layout)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    if q == "flat":
        return flat()
    if q == "where":  # what is in frame, computed from the camera; no mesh
        return report(camera(), characters(300.0, 900.0, 901.0, 900.0, 901.0, np.zeros((4, 4), np.float32), np.zeros((4, 4), np.float32)))
    dens = {"sketch": 0.42, "preview": 0.55, "mid": 0.75, "final": 1.0}[q]
    P, C, Ro, M, F, layout = build(dens)
    cam = camera()
    report(cam, layout)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=M)  # rows run -y, so the normals are up
    del F

    # --- light. Key: from the left, low and a little from behind, so slopes that face it flash, slopes away go dark; on the bent sheet it falls off across the frame.
    loc = np.array(cam["loc"])
    # a broad soft sheen: the mirror image of the camera in the sheet at a point left of centre. Gold tops there glow; further along the bend the mirror turns away.
    ps = surface(-2.6, FOCUS[1] + 0.8)
    th = -2.6 / R
    nn = np.array([np.sin(th), 0.0, np.cos(th)])
    v = loc - ps
    v /= np.linalg.norm(v)
    rv = 2 * (v @ nn) * nn - v
    lights = [
        {"type": "gradient", "name": "sheen", "loc": (ps + rv * 60.0).tolist(), "target": ps.tolist(), "size": [90, 90], "sigma": [11, 22], "L": 1.15, "rgb": [1.0, 0.93, 0.82]},
        {"name": "rake", "loc": [-44, 26, 15], "target": [0, 0, 0], "size": [7, 7], "watts": 56000, "rgb": [1.0, 0.89, 0.72]},
        {"name": "fill", "loc": [24, -30, 40], "target": [0, 0, 0], "size": [50, 50], "watts": 1300, "rgb": [0.9, 0.95, 1.0], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "paper", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": 0.42}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"window": 0.5, "strip": 0.25},
        "sky": {"top": [0.0065, 0.0065, 0.0068], "glow": [0.015, 0.015, 0.016], "y0": 0.34, "h": 0.5, "x0": 0.36, "mottle": 0.12},
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.0, "contrast": 1.28, "saturation": 1.0, "black": 0.0015, "grain": 1.2, "sharpen": 0.22, "halation": 0.05, "glare": 0.004, "vignette": 0.3}, tag="cand" if q == "final" else f"cand_{q}")  # never final.*: the film reads that, and the main line swaps it in


main()
