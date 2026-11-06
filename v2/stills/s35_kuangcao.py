"""Shot 35: one stroke of wild cursive (狂草) on gold-flecked paper (洒金笺); the outer edge of the stroke is the arc.

    python3 -I v2/stills/s35_kuangcao.py [sketch|preview|mid|final]

Built like the real thing (scales are estimates from general knowledge, not measured):
- the brush is a body of hair whose tracks are long and thin: the stroke is written in (s, o), along it and across it;
- ink is laid where a track still carries ink and meets the tooth of the paper: wet at the start, 飞白 as it runs dry;
- ink gathers at the edge of the wet part and creeps a little along the fibres; thin ink shows the paper through it;
This is not a written character: it is one sweep and a trailing hair stroke, with no claim to any calligrapher's hand.

Second version. The blind review of the first: "飞白 very good; the paper is same-scale noise, the gold flecks are all alike, that thin line is too even". Changed:
- the paper's structure comes from how it was made, not one noise: laid lines (帘纹) of the bamboo screen with their own spacing and chain lines, a cloudy pulp formation, visible long and short fibres in clots (height and colour, pale and dark), dark bark specks, a slow cockle.
  The same-scale noise is down to a low height (it still decides where the dry brush touches, which is what the 飞白 needs). A first pass removed too much and the fibres went: they are back, compared with the committed version at the same size;
- the gold: torn leaf, each flake an individual polygon with a jagged edge and a few fold lines; sizes span 0.008-0.7 cm by a power law, thrown in clusters, so there are many crumbs and a few large pieces. Each is a metal plate with its own tilt: some flash, most do not;
- the trailing line (牵丝): a pressure curve (thin when fast, thick at the turn), a body of 3-5 hairs that part and rejoin, broken over the tooth where it runs dry. Flung drops are fewer, stretched along their flight;
- the ink has a body: brush tracks in its relief, slightly raised black, a soft sheen.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, frame_camera, mix, rank, shoot, sstep

W = 9.0
ELEV = np.radians(60.0)
R = 8.3  # radius of the outer edge, cm
APEX = 0.23  # y of the crown of the edge on the paper, cm
X0, X1, Y0, Y1 = -6.0, 6.0, -5.4, 4.8
SEED = 35


def paper_fibres(shape, pxcm, per_cm2, lo, hi, seed):
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


def pulp_fibres(shape, pxcm, classes, seed):
    """Real-looking fibres in the sheet: smooth curling paths, thrown in clots (dense here, sparse there), each with its own strength and width.
    classes: (per cm2, shortest cm, longest cm). Returns one buffer per class."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    clot = rank(fbm(shape, pxcm, 0.25, 2.2, 2.6, seed + 1))
    out = []
    for per, lo, hi in classes:
        n = int(nx * ny / pxcm**2 * per)
        px, py = rng.uniform(0, nx, n), rng.uniform(0, ny, n)
        keep = rng.random(n) < 0.12 + 0.88 * clot[py.astype(int), px.astype(int)] ** 2
        px, py = px[keep], py[keep]
        n = len(px)
        a = rng.uniform(0, np.pi, n)
        step = np.exp(rng.uniform(np.log(lo), np.log(hi), n)) * pxcm / 11.0
        curl = rng.normal(0, 0.1, n)
        pts = [np.stack([px, py], -1)]
        for _ in range(11):
            curl = curl + rng.normal(0, 0.05, n)
            a = a + curl
            px, py = px + step * np.cos(a), py + step * np.sin(a)
            pts.append(np.stack([px, py], -1))
        P = np.round(np.stack(pts, 1) * 8).astype(np.int32)
        buf = np.zeros(shape, np.float32)
        level = rng.choice(4, n, p=[0.35, 0.3, 0.2, 0.15])
        thick = rng.random(n) < 0.14
        for lv, val in enumerate((0.3, 0.5, 0.75, 1.0)):
            for th in (1, 2):
                sel = P[(level == lv) & (thick == (th == 2))]
                if len(sel):
                    c = np.zeros(shape, np.uint8)
                    cv2.polylines(c, list(sel), False, 255, max(1, int(round(th * max(pxcm / 300.0, 0.6)))), cv2.LINE_AA, shift=3)
                    buf = np.maximum(buf, c.astype(np.float32) / 255.0 * val)
        out.append(blur(buf, max(0.55 * pxcm / 300.0, 0.42)))
    return out


def torn(rng, pts, rounds, amp):
    """Midpoint displacement of a closed polygon: a torn edge. Amp is relative to the segment length."""
    for _ in range(rounds):
        nxt = np.roll(pts, -1, 0)
        mid = 0.5 * (pts + nxt) + np.stack([pts[:, 1] - nxt[:, 1], nxt[:, 0] - pts[:, 0]], 1) * rng.normal(0, amp, (len(pts), 1))
        out = np.zeros((2 * len(pts), 2))
        out[0::2], out[1::2] = pts, mid
        pts = out
    return pts


def flakes(shape, pxcm):
    """Torn pieces of leaf in physical cm, independent of the grid: returns alpha and height (cm) and a per-pixel 'id'. Sizes follow a power law; thrown in clusters."""
    rng = np.random.default_rng(SEED + 12)
    ny, nx = shape
    alpha = np.zeros(shape, np.uint8)
    hgt = np.zeros(shape, np.float32)
    ids = np.zeros(shape, np.int32)
    # throws: where a pinch of leaf landed
    n_throw = 80
    tx = rng.uniform(X0, X1, n_throw)
    ty = rng.uniform(Y0, Y1, n_throw)
    i = 0
    for k in range(n_throw):
        count = int(rng.lognormal(np.log(10), 0.9))
        spread = rng.lognormal(np.log(0.45), 0.5)
        for j in range(count + 24 // n_throw):
            # power law: p(s) ~ s^-2.2 between 0.008 and 0.7 cm
            u = rng.random()
            a_, b_ = 0.008 ** -1.2, 0.5 ** -1.2
            size = (a_ + u * (b_ - a_)) ** (-1 / 1.2)
            if j == 0 and rng.random() < 0.5:
                size = rng.uniform(0.12, 0.42)
            # the smaller the further it flew
            cx = tx[k] + rng.normal(0, spread * (1.0 + 0.15 / (size + 0.05)) * 0.5)
            cy = ty[k] + rng.normal(0, spread * (1.0 + 0.15 / (size + 0.05)) * 0.5)
            m = rng.integers(3, 7)
            ang = np.sort(rng.uniform(0, 2 * np.pi, m))
            rad = size * rng.uniform(0.3, 1.0, m)
            st = rng.uniform(0.3, 1.0)
            rot = rng.uniform(0, np.pi)
            x, y = rad * np.cos(ang), rad * np.sin(ang) * st
            poly = np.stack([x * np.cos(rot) - y * np.sin(rot), x * np.sin(rot) + y * np.cos(rot)], 1)
            rounds = 2 + int(size > 0.06) + int(size > 0.2)
            poly = torn(rng, poly, rounds, 0.2)
            pp = np.stack([(poly[:, 0] + cx - X0) * pxcm, (Y1 - (poly[:, 1] + cy)) * pxcm], 1)
            lo, hi = np.floor(pp.min(0)).astype(int) - 2, np.ceil(pp.max(0)).astype(int) + 3
            lo, hi = np.maximum(lo, 0), np.minimum(hi, [nx, ny])
            if lo[0] >= hi[0] or lo[1] >= hi[1]:
                continue
            i += 1
            sub_a = alpha[lo[1] : hi[1], lo[0] : hi[0]]
            tmp = np.zeros(sub_a.shape, np.uint8)
            cv2.fillPoly(tmp, [np.round((pp - lo) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
            on = tmp > 127
            yy, xx = np.mgrid[lo[1] : hi[1], lo[0] : hi[0]].astype(np.float32)
            xc, yc = (xx / pxcm + X0 - cx), (Y1 - yy / pxcm - cy)
            # a plate with its own tilt, a few straight folds across it (folds in leaf are straight and sharp)
            slope = 0.014 * rng.lognormal(0, 0.8)
            th = rng.uniform(0, 2 * np.pi)
            h = slope * (np.cos(th) * xc + np.sin(th) * yc) + 0.0006 + slope * size * 0.9
            for _ in range(rng.integers(0, 2 + int(size > 0.1) * 3)):
                f = rng.uniform(0, np.pi)
                dd = np.cos(f) * xc + np.sin(f) * yc - rng.normal(0, size * 0.5)
                h = h + rng.normal(0, 0.016) * np.abs(dd) * 0.4
            sub_a[:] = np.maximum(sub_a, tmp)
            hgt[lo[1] : hi[1], lo[0] : hi[0]][on] = h[on]
            ids[lo[1] : hi[1], lo[0] : hi[0]][on] = i
    print("flakes", i, flush=True)
    return alpha.astype(np.float32) / 255.0, hgt, ids


def laid(shape, Y, X, seed):
    """Screen marks: laid lines across (spacing about 0.09 cm, each its own), chain lines along about every 2.3 cm, faint."""
    rng = np.random.default_rng(seed)
    n = 400
    w = 0.09 * np.clip(rng.lognormal(0, 0.13, n), 0.6, 1.5)
    edges = -22.0 + np.r_[0, np.cumsum(w)]
    # the screen is not square to the picture: 4 degrees off
    a = np.radians(4.0)
    v = Y * np.cos(a) + X * np.sin(a)
    u = -Y * np.sin(a) + X * np.cos(a)
    i = np.clip(np.searchsorted(edges, v.ravel()) - 1, 0, n - 1).reshape(shape)
    f = (v - edges[i]) / w[i]
    bar = np.cos((f - 0.5) * np.pi) ** 2
    strength = rng.uniform(0.5, 1.0, n)[i]
    ch = 2.3 * np.clip(rng.lognormal(0, 0.06, 40), 0.8, 1.2)
    ce = -24.0 + np.r_[0, np.cumsum(ch)]
    j = np.clip(np.searchsorted(ce, u.ravel()) - 1, 0, 39).reshape(shape)
    du = np.minimum(u - ce[j], ce[j + 1] - u)
    chain = np.exp(-(du / 0.02) ** 2)
    return (bar * strength).astype(np.float32), chain.astype(np.float32)


def build(dens):
    pxcm = 300.0 * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    x = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    y = Y1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)

    # --- the paper
    flocs = fbm(shape, pxcm, 0.04, 0.5, 2.2, SEED)
    fib = blur(paper_fibres(shape, pxcm, 190, 0.2, 0.8, SEED + 1), max(0.7 * dens, 0.45))
    fib2 = blur(paper_fibres(shape, pxcm, 700, 0.03, 0.14, SEED + 2), max(0.5 * dens, 0.4))
    tooth = fbm(shape, pxcm, 0.006, 0.05, 1.5, SEED + 3)
    tooth = (tooth + 1.6 * fib + 0.7 * fib2).astype(np.float32)
    wash = rank(fbm(shape, pxcm, 1.5, 12.0, 3.2, SEED + 4))
    bar, chain = laid(shape, Y, X, SEED + 30)
    cloud = fbm(shape, pxcm, 0.12, 1.1, 2.8, SEED + 31)  # formation: clouds of pulp seen in the sheet
    pap = mix(color([0.645, 0.48, 0.262]), color([0.735, 0.57, 0.33]), wash)
    pap = pap * (0.96 + 0.028 * cloud[..., None] + 0.05 * fib[..., None] + 0.03 * fib2[..., None] + 0.018 * flocs[..., None] + 0.016 * bar[..., None] + 0.02 * chain[..., None])
    # the fibres of the sheet, visible: long ones and short ones, in clots, pale and dark, with height so the side light finds them
    f_long, f_mid, f_short = pulp_fibres(shape, pxcm, ((85.0, 0.5, 2.0), (300.0, 0.14, 0.55), (950.0, 0.03, 0.12)), SEED + 50)
    f_dark, = pulp_fibres(shape, pxcm, ((22.0, 0.2, 1.2),), SEED + 60)
    pap = pap * (1.0 + 0.1 * f_long[..., None] + 0.075 * f_mid[..., None] + 0.05 * f_short[..., None] - 0.16 * f_dark[..., None])
    # dark bark specks: rare short bits that the pulp kept
    rb = np.random.default_rng(SEED + 32)
    bark = np.zeros(shape, np.uint8)
    for _ in range(int((X1 - X0) * (Y1 - Y0) * 2.2)):
        xb, yb = rb.uniform(0, nx), rb.uniform(0, ny)
        ab, lb = rb.uniform(0, np.pi), rb.lognormal(np.log(0.05), 0.5) * pxcm
        cb = rb.normal(0, 0.5)
        pts_ = [(xb + lb * t_ * np.cos(ab + cb * t_), yb + lb * t_ * np.sin(ab + cb * t_)) for t_ in np.linspace(0, 1, 5)]
        cv2.polylines(bark, [np.round(np.array(pts_) * 8).astype(np.int32)], False, int(rb.uniform(90, 255)), 1, cv2.LINE_AA, shift=3)
    bark = blur(bark.astype(np.float32) / 255.0, max(0.5 * dens, 0.4))
    pap = pap * (1.0 - 0.55 * bark[..., None] * color([0.8, 1.0, 1.15]))

    # --- the stroke: coordinates along and across it
    yc = APEX - R
    r = np.sqrt(X**2 + (Y - yc) ** 2)
    s = R * np.arctan2(X, Y - yc)  # cm along the outer edge, 0 at the crown, left to right
    hand = 0.035 * fbm((64, 1024), 1024 / 24.0, 0.8, 7.0, 3.0, SEED + 5)[32]  # tremor of the hand, a function of s
    edge_r = R + np.interp(s, np.linspace(-12, 12, 1024), hand)
    # the width as the brush lifts: heavy at the left, thinning into a dry tail on the right
    bs = np.array([-9, -5.2, -3.2, -1.0, 1.0, 2.6, 4.0, 5.2, 7.0])
    bw = np.array([3.6, 3.3, 3.0, 2.55, 2.0, 1.55, 1.05, 0.62, 0.2])
    b = np.interp(s, bs, bw)
    o = (edge_r - r) / b  # 0 at the outer edge, 1 at the inner edge

    # tracks: noise stretched along the stroke; two scales of hair clump, and they wander across slowly
    wander = cv2.resize(fbm((256, 256), 256 / 24.0, 1.0, 9.0, 3.0, SEED + 6), (nx, ny), interpolation=cv2.INTER_CUBIC)
    u = (s + 12.0) * 34.0
    v_cm = (o + 0.0035 * wander) * b
    size = 2048
    clump = fbm((size, size), 1.0, 2.0, 60.0, 2.2, SEED + 7)
    hair = fbm((size, size), 1.0, 1.2, 14.0, 1.6, SEED + 8)
    # rows of the noise are across the stroke: 1 noise pixel across = 0.01 cm, and 1 along = 1/34 cm * stretch
    mapx_c = np.mod(u * 0.34, size - 1).astype(np.float32)
    mapy_c = np.mod(v_cm * 130.0 + 300.0, size - 1).astype(np.float32)
    C = cv2.remap(clump, mapx_c, mapy_c, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    mapx_h = np.mod(u * 0.8, size - 1).astype(np.float32)
    mapy_h = np.mod(v_cm * 260.0 + 900.0, size - 1).astype(np.float32)
    Hr = cv2.remap(hair, mapx_h, mapy_h, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    tracks = 0.62 * C + 0.5 * Hr

    # dryness along the stroke, with the edges a little ahead of the middle
    dry = sstep(-2.8, 5.0, s + 0.5 * cv2.resize(fbm((64, 64), 64 / 24.0, 1.0, 8.0, 2.6, SEED + 9), (nx, ny), interpolation=cv2.INTER_CUBIC))
    edge_near = np.exp(-np.minimum(np.abs(o), np.abs(1 - o)) * b / 0.28)
    thresh = -2.8 + 3.65 * dry**0.9 + 0.3 * dry * edge_near
    grab = tracks + 0.34 * dry * tooth
    deposit = sstep(0.0, 0.26, grab - thresh)

    # the outline of the body of the stroke, rough at a fine scale
    fine = fbm(shape, pxcm, 0.004, 0.05, 1.5, SEED + 10)
    edge_noise = 0.009 * fine + 0.012 * fib
    d_out = (r - edge_r) + edge_noise  # > 0 is outside the outer edge
    d_in = (edge_r - b - r) + edge_noise  # > 0 is inside the inner edge
    body = sstep(0.018, -0.018, d_out) * sstep(0.018, -0.018, d_in)

    # --- ink: density in optical depth
    wet = 1.0 - sstep(0.2, 0.75, dry)
    D = 6.5 * (0.72 + 0.28 * sstep(-1.0, 1.0, C)) * (0.34 + 0.66 * wet) * deposit * body
    # dry hair marks: thinner, and grainy where only the tops of the paper took ink
    D = D + 0.9 * dry * deposit * body * sstep(-0.4, 1.0, tooth)
    # the wet edge: a darker line where ink gathered, and a little creep along the fibres
    side = np.minimum(np.abs(d_out), np.abs(d_in))
    D = D + 1.1 * wet * np.exp(-side / 0.03) * body
    creep = wet * (np.exp(-np.maximum(d_out, 0) / 0.022) * (d_out > -0.02) + np.exp(-np.maximum(d_in, 0) / 0.022) * (d_in > -0.02))
    D = D + 0.65 * creep * sstep(0.1, 0.7, fib + 0.5 * fib2 + 0.1 * fine)
    D = D + 0.12 * wet * (np.exp(-np.maximum(d_out, 0) / 0.09) * (d_out > 0) + np.exp(-np.maximum(d_in, 0) / 0.09) * (d_in > 0))

    # a trailing hair stroke (牵丝): a pressure curve, 3-5 hairs that part and rejoin; it breaks over the tooth where it runs dry
    rt = np.random.default_rng(SEED + 40)
    m = 700
    t = np.linspace(0, 0.6, m)  # it ends where it runs into the wet body
    cxy = np.stack([5.4 - 8.6 * t + 0.5 * np.sin(t * 3.0), -1.0 - 2.0 * t + 1.25 * np.sin(np.pi * t) ** 1.2 - 0.8 * t**2], 1)
    cxy += np.stack([0.03 * np.interp(t, np.linspace(0, 1, 11), rt.normal(0, 1, 11)), 0.03 * np.interp(t, np.linspace(0, 1, 11), rt.normal(0, 1, 11))], 1)
    tang = np.gradient(cxy, axis=0)
    speed = np.hypot(tang[:, 0], tang[:, 1])
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1) / (speed[:, None] + 1e-9)
    curv = np.abs(np.gradient(np.unwrap(np.arctan2(tang[:, 1], tang[:, 0])))) * m
    press = 0.1 + 0.55 * (t / 0.6) ** 1.6 + 0.22 * sstep(0.5, 3.0, cv2.GaussianBlur(curv.astype(np.float32)[None], (0, 0), 16.0)[0]) + 0.12 * np.interp(t, np.linspace(0, 1, 25), rt.random(25))
    tot = np.zeros(shape, np.float32)
    n_hair = 5
    for h_ in range(n_hair):
        canvas = np.zeros(shape, np.uint8)
        # a hair's offset: all together when pressed, apart when light and fast; each hair may lift for a stretch
        off = (h_ - (n_hair - 1) / 2) * 0.012 * (0.2 + 1.8 * (1 - press)) + 0.004 * np.interp(t, np.linspace(0, 1, 16), rt.normal(0, 1, 16))
        lift = np.interp(t, np.linspace(0, 1, 28), rt.random(28)) > 0.12 + 0.45 * (1 - press) ** 2
        wd = (0.0026 + 0.016 * press) * pxcm * (0.8 + 0.4 * np.interp(t, np.linspace(0, 1, 40), rt.random(40)))
        ph = np.stack([cxy[:, 0] + nrm[:, 0] * off, cxy[:, 1] + nrm[:, 1] * off], 1)
        for i in range(m - 1):
            if lift[i]:
                p0 = ((ph[i, 0] - X0) * pxcm, (Y1 - ph[i, 1]) * pxcm)
                p1 = ((ph[i + 1, 0] - X0) * pxcm, (Y1 - ph[i + 1, 1]) * pxcm)
                cv2.line(canvas, (int(p0[0] * 16), int(p0[1] * 16)), (int(p1[0] * 16), int(p1[1] * 16)), 255, max(1, int(round(wd[i]))), cv2.LINE_AA, shift=4)
        tot = np.maximum(tot, canvas.astype(np.float32) / 255.0)
    tot = blur(tot, max(0.6 * dens, 0.45))
    D = D + 2.8 * sstep(0.22, 0.7, tot + 0.08 * fine + 0.1 * (tooth - tooth.mean()))

    # flung drops: fewer, stretched along their flight
    rng = np.random.default_rng(SEED + 11)
    drops = np.zeros(shape, np.uint8)
    for _ in range(26):
        a = rng.uniform(-0.05, 0.7)
        px_ = (R + rng.exponential(0.5)) * np.sin(a) - X0
        py_ = Y1 - (yc + (R + rng.exponential(0.5) - rng.uniform(0, 1.8)) * np.cos(a))
        rr = rng.lognormal(np.log(0.009), 0.7) * pxcm
        cv2.ellipse(drops, (int(px_ * pxcm * 16), int(py_ * pxcm * 16)), (max(1, int(rr * rng.uniform(1.1, 2.6) * 16)), max(1, int(rr * 16))), np.degrees(a) + rng.normal(0, 18), 0, 360, 255, -1, cv2.LINE_AA, shift=4)
    D = D + 2.6 * blur(drops.astype(np.float32) / 255.0, max(0.6 * dens, 0.4))

    # --- leaf
    fl, fh, fid = flakes(shape, pxcm)
    wrinkle = fbm(shape, pxcm, 0.01, 0.06, 1.8, SEED + 13)
    fl_soft = sstep(0.3, 0.7, blur(fl, max(0.5 * dens, 0.4)))
    # the flakes are not one colour: a sheet's tone per piece, redder where thin
    rc = np.random.default_rng(SEED + 14)
    tone_ = rc.random(fid.max() + 2).astype(np.float32)[fid]
    gold = mix(color([0.93, 0.56, 0.15]), color([1.0, 0.72, 0.28]), tone_)
    # ink beads on leaf: a thinner film, broken where the brush was dry
    ink_on_gold = np.exp(-1.2 * D)

    # --- together
    T = np.exp(-D)[..., None]
    ink_col = color([0.0072, 0.0066, 0.0068])
    col = pap * T + ink_col * (1.0 - T)
    col = mix(col, gold * ink_on_gold[..., None] + ink_col * (1.0 - ink_on_gold[..., None]), fl_soft)
    metal = fl_soft * ink_on_gold
    op = 1.0 - np.exp(-1.3 * D)
    rough = 0.82 * (1.0 - op) + (0.38 + 0.1 * sstep(-1.0, 1.0, tooth)) * op
    rough = mix(rough, 0.22 + 0.14 * rank(wrinkle), metal)
    spec = 0.42 * (1.0 - op) + 0.28 * op

    # --- height: paper, a thin body of ink, the leaf a little proud
    h = 0.0004 * cloud + 0.0022 * f_long + 0.0015 * f_mid + 0.0008 * f_short + 0.0008 * f_dark + 0.0006 * flocs + 0.00042 * tooth + 0.0003 * bar + 0.0003 * chain + 0.03 * fbm(shape, pxcm, 1.5, 9.0, 3.2, SEED + 33)
    h = h + (1.0 - np.exp(-0.8 * D)) * (0.0016 * wet + 0.00007 * np.clip(C, -1.5, 1.5) * wet + 0.00005 * np.clip(Hr, -1.5, 1.5) * wet + 0.0004)
    h = h + fl_soft * (fh + 0.00016 * wrinkle) * (0.02 + 0.98 * np.exp(-1.2 * D))  # wet ink pulls a flake flat
    P = np.stack([X, Y, h], -1).astype(np.float32)
    print("ink coverage in frame band", float((D > 1.0).mean()), flush=True)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), np.clip(metal, 0, 1).astype(np.float32), spec.astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"sketch": 0.36, "preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s35_kuangcao")
    os.makedirs(d, exist_ok=True)
    P, C, Ro, M, Sp = build(dens)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=M, spec=Sp)
    view = np.array([0.0, -np.cos(ELEV), np.sin(ELEV)])
    tgt = np.array([0.0, 0.0, 0.0])
    # the crown of the edge is at (x 0.5, y 0.45) of the frame
    tgt[1] = APEX - 0.05 * W * 9.0 / 16.0 / np.sin(ELEV)
    focus = np.array([0.0, APEX - 1.1, 0.0])
    cam = frame_camera(tgt, view, W, 34.0, aperture_mm=7.0, focus_point=focus)
    # the scrim mirrored in the ink: its reflection lies across the wet part of the stroke
    pm = np.array([-2.2, APEX - 1.5, 0.0])
    v = np.array(cam["loc"]) - pm
    v /= np.linalg.norm(v)
    rv = 2 * v[2] * np.array([0, 0, 1.0]) - v
    lights = [
        {"name": "key", "loc": [-44, 26, 15], "target": [0, 0, 0], "size": [12, 12], "watts": 62000, "rgb": [1.0, 0.91, 0.78], "hide_in_gloss": True},
        {"name": "fill", "loc": [20, -30, 40], "target": [0, 0, 0], "size": [50, 50], "watts": 8000, "rgb": [0.92, 0.96, 1.0], "hide_in_gloss": True},
        {"type": "gradient", "name": "sheen", "loc": (pm + rv * 45.0).tolist(), "target": pm.tolist(), "size": [90, 60], "sigma": [26, 12], "L": 1.15, "rgb": [1.0, 0.95, 0.88]},
        {"name": "glint", "loc": [30, 34, 24], "target": [0, 0, 0], "size": [9, 9], "watts": 24000, "rgb": [1.0, 0.92, 0.8]},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "paper", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": "spec"}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"window": 1.4, "strip": 1.0},
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }
    # the film reads final.*: a candidate goes to cand.* and is renamed only after it has passed a look at 100%
    shoot("s35_kuangcao", scene, "preview" if q == "sketch" else q, tag="cand" if q == "final" else q, develop={"exposure": 0.0, "contrast": 1.32, "saturation": 1.04, "black": 0.002, "grain": 1.3, "sharpen": 0.3, "halation": 0.03, "glare": 0.002, "vignette": 0.32})


main()
