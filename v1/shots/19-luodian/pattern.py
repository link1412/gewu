"""Shot 19 round 1: the inlay of a black-lacquer dish with thin, finely cut, coloured mother-of-pearl, a landscape
with figures (docs/shots/19-luodian.md, 纹样). Our own composition in the manner of the Shanghai Museum's
漆螺钿山水人物图圆盘 (Qing, 18th c., 12.6 cm; a figure with an umbrella crossing a bridge); not traced from it.

The design is drawn in the dish's plane in mm, x to the right as the viewer sees it, y away from the viewer (the
picture's "up"), centre of the dish at the origin. The camera looks from -y over the near rim at the far half, so
the picture's upper part (hills, moon, willow crown, pavilion, the bridge with the figure) is what the frame shows.

Pieces are rasterised into an id map at TEXEL_MM; each piece is cut from its own place in the shell, so it has
- its own mean tablet thickness d (its colour; D_RANGE_NM, our choice around Salman 2021's 420 nm, [A]); the
  craftsman picks pieces by colour, so each motif draws d from its own sub-range (COLOURS, our choice, [A]);
- its own tilt of the layers against the polished face: two normal components, RMS TILT_RMS_DEG [A] (S2's
  estimate from polishing gratings, Liu et al. 1999; the shell is cut from a curved valve; no measurement found).
Both are fixed in object space. Seams between abutting pieces are one texel of lacquer; incised details on the
pieces (毛雕) are lacquer lines INCISE_MM wide [A]. Finest strips 0.3 mm [A: the survey found no measurement].

Maps (as shots/19-dianluo/pattern.py, read by the "nacreinlay" material), in object space seen from above:
- inlay (H, W, 3): shell mask, d normalised to the nacre table's axis, 0;
- layers (H, W, 3): the layers' normal in object space, encoded (n + 1) / 2.
Row 0 is y = y0. Object x = -design x (pbrt's LookAt from -y looking +y puts -X on the image's right).
"""

import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TEXEL_MM = 0.025
D_RANGE_NM = (250.0, 550.0)    # piece means; measured abalone tablets 245-550 nm (luodian.md section 3) [查到]
FLAME_D_NM = 30.0               # in-piece thickness swing of the growth bands [A: Tang & Zhang 2015 measured 499 vs 371 nm
                                # between a valve's edge and centre, so tens of nm across a few mm is our guess]
FLAME_TILT_DEG = 5.0            # in-piece swing of the layers' slope [A]
FLAME_PERIOD_MM = (1.8, 3.5)    # the bands' period [A]
FLAME_WARP_MM = (0.25, 0.6)     # the bands' waviness: amplitude, correlation length [A]
TILT_RMS_DEG = 6.8
# the valve is curved and the piece is ground flat, so its layers stay curved under the flat face: the layers' tilt
# changes across a piece by (offset from the piece's centre) / R. R per piece uniform over SHELL_R_MM, bowl or dome at
# random [A: abalone valves are a few cm across; no measurement of the curvature left in a ground piece was found]
SHELL_R_MM = (25.0, 60.0)
INCISE_MM = 0.1         # [A]; round 1 had 0.07 mm, below a pixel and invisible
ROUNDEL_R = 53.4          # the picture's field; the border band outside it
BORDER = (54.0, 56.4)     # two thin rings and a band of lozenges between them
FLOOR_R = 57.2            # flat floor; the cavetto rises from here (scene.py)
# the motifs below are drawn in a frame of their own, then scaled by S and moved up by DY (mm) onto the floor, so
# the picture's upper half lies under the far rim, the part the lens sees
S, DY = 1.08, 14.0

# colour picks per motif: (d_lo, d_hi) in nm, inside D_RANGE_NM [A, a craftsman's choice]. The key-lit pieces see
# their layers at ~28-30 deg inside the shell (34 deg less the ~4-6 deg lean that sends the key to the lens), where
# the stack's hue runs with d (out/shots/19-luodian/hue_vs_d.txt): ~280 blue, ~340 cyan, ~360 green, ~380
# near-white, ~400 pink, ~440 violet, ~480 blue again (first set for 34 deg, then all shifted down 20 nm); the reference dishes are mostly pink, green, white-grey with
# blue-green water, so most motifs draw from 370-450
COLOURS = {
    "hill": (350, 430), "hill2": (395, 450), "moon": (378, 392), "willow": (346, 374), "leaf": (346, 374),
    "trunk": (398, 426), "rock": (315, 450), "rock2": (365, 430), "moss": (348, 368), "pavilion": (378, 420),
    "roof": (435, 480), "bridge": (388, 420), "rail": (376, 394), "robe": (378, 390), "robe2": (420, 432),
    "umbrella": (404, 424), "skin": (380, 390), "water": (290, 362), "grass": (348, 372), "bird": (378, 394),
    "border": (395, 445), "cloud": (375, 400),
}


class Canvas:
    def __init__(self, x0, x1, y0, y1, texel, rng):
        self.x0, self.y1, self.t = x0, y1, texel
        self.W, self.H = int(round((x1 - x0) / texel)), int(round((y1 - y0) / texel))
        self.img = Image.new("I", (self.W, self.H), 0)
        self.draw = ImageDraw.Draw(self.img)
        self.pieces = [None]
        self.rng = rng
        self.placed = False          # True: coordinates are already on the floor (the border)

    def px(self, P, placed=False):
        P = np.atleast_2d(np.asarray(P, float))
        if not (placed or self.placed):
            P = np.c_[S * P[:, 0], S * P[:, 1] + DY]
        return [((x - self.x0) / self.t, (self.y1 - y) / self.t) for x, y in P]   # image rows: y down

    def new(self, motif):
        lo, hi = COLOURS[motif]
        tilt = self.rng.normal(0, math.radians(TILT_RMS_DEG) / math.sqrt(2), 2)
        self.pieces.append({"motif": motif, "d_nm": float(self.rng.uniform(lo, hi)), "tilt": tilt})
        return len(self.pieces) - 1

    def poly(self, P, motif=None, pid=None):
        pid = self.new(motif) if pid is None else pid
        self.draw.polygon(self.px(P), fill=pid)
        return pid

    def cut(self, P, width=INCISE_MM):
        """An incised line (lacquer) through whatever is there."""
        self.draw.line(self.px(P), fill=0, width=max(1, int(round(width / self.t))), joint="curve")

    def strip(self, P, width, motif, seg=None, taper=True):
        """A strip of shell along the polyline P (mm), width mm, cut into pieces about seg mm long, ends pointed."""
        P = np.asarray(P, float)
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        total = d[-1]
        if total <= 0:
            return
        n = 1 if seg is None else max(1, int(round(total / seg)))
        cuts = np.linspace(0, total, n + 1)
        gap = 0.03
        for i in range(n):
            s = np.linspace(cuts[i] + gap, cuts[i + 1] - gap, max(3, int((cuts[i + 1] - cuts[i]) / 0.1)))
            x, y = np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])
            tx, ty = np.gradient(x), np.gradient(y)
            k = np.hypot(tx, ty) + 1e-12
            nx, ny = -ty / k, tx / k
            u = (s - s[0]) / max(s[-1] - s[0], 1e-9)
            w = np.full_like(s, width / 2)
            if taper:
                if i == 0:
                    w *= np.clip(u * (s[-1] - s[0]) / (2 * width) + 0.25, 0, 1)
                if i == n - 1:
                    w *= np.clip((1 - u) * (s[-1] - s[0]) / (2 * width) + 0.25, 0, 1)
            L = np.c_[x + nx * w, y + ny * w]
            R = np.c_[x - nx * w, y - ny * w][::-1]
            self.poly(np.r_[L, R], motif)

    def mosaic(self, outline, cell, motif, cuts=0, cut_rng=None):
        """A shape filled with irregular pieces about `cell` mm across (Voronoi cells of jittered seeds), each its own
        piece; then `cuts` incised strokes (texture strokes, 皴) inside."""
        tmp = Image.new("1", (self.W, self.H), 0)
        ImageDraw.Draw(tmp).polygon(self.px(outline), fill=1)
        m = np.asarray(tmp, bool)
        if not m.any():
            return
        ys, xs = np.nonzero(m)
        r0, r1, c0, c1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        sub = m[r0:r1, c0:c1]
        step = cell / self.t
        gy, gx = np.mgrid[0:sub.shape[0]:step, 0:sub.shape[1]:step]
        seeds = np.c_[gy.ravel(), gx.ravel()] + self.rng.uniform(-0.45, 0.45, (gy.size, 2)) * step
        seeds = seeds[(seeds[:, 0] >= 0) & (seeds[:, 0] < sub.shape[0]) & (seeds[:, 1] >= 0) & (seeds[:, 1] < sub.shape[1])]
        lab = np.zeros(sub.shape, np.int32)
        lab[seeds[:, 0].astype(int), seeds[:, 1].astype(int)] = np.arange(1, len(seeds) + 1)
        _, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
        lab = lab[iy, ix]
        ids = np.array([0] + [self.new(motif) for _ in range(len(seeds))], np.int32)
        cur = np.asarray(self.img, np.int32).copy()
        region = cur[r0:r1, c0:c1]
        region[sub] = ids[lab[sub]]
        cur[r0:r1, c0:c1] = region
        self.img = Image.fromarray(cur)
        self.draw = ImageDraw.Draw(self.img)
        rng = cut_rng or self.rng
        if cuts:
            O = np.asarray(outline, float)
            lo, hi = O.min(0), O.max(0)
            for _ in range(cuts):
                p = lo + rng.uniform(0.1, 0.9, 2) * (hi - lo)
                if not sub_contains(m, self, p):
                    continue
                ang = rng.uniform(-0.6, 0.6) + math.pi / 2 * rng.choice([0, 1]) * 0.3
                L = rng.uniform(0.8, 2.2)
                bend = rng.uniform(-0.3, 0.3)
                tt = np.linspace(-0.5, 0.5, 6)
                Q = np.c_[p[0] + L * tt * math.cos(ang) - bend * (tt ** 2) * math.sin(ang),
                          p[1] + L * tt * math.sin(ang) + bend * (tt ** 2) * math.cos(ang)]
                self.cut(Q)

    def ids(self):
        return np.array(self.img, np.int32)


def sub_contains(mask, cv, p):
    (c, r), = cv.px(p)
    c, r = int(c), int(r)
    return 0 <= r < mask.shape[0] and 0 <= c < mask.shape[1] and mask[r, c]


def blob(cx, cy, rx, ry, rng, n=28, rough=0.18, flat_bottom=False):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    k = 1 + rough * (rng.uniform(-1, 1, n) + 0.5 * np.sin(3 * a + rng.uniform(0, 6)))
    P = np.c_[cx + rx * k * np.cos(a), cy + ry * k * np.sin(a)]
    if flat_bottom:
        P[:, 1] = np.maximum(P[:, 1], cy - 0.35 * ry)
    return P


def leaf_chain(cv, P0, length, sway, rng, motif="willow", leaf=(0.85, 0.32), step=0.55):
    """A hanging willow strand drawn as a chain of separate leaf pieces (no stem strip: at speed a continuous strip
    read as a vertical glitch, round 1): the strand droops from P0 and curves out by `sway` mm; each leaf a small
    pointed lens leaf[0] x leaf[1] mm, alternately left and right, pointing down and out."""
    tt = np.linspace(0, 1, max(4, int(length / step)))
    path = np.c_[P0[0] + sway * tt ** 1.6, P0[1] - length * tt]
    for k, (x, y) in enumerate(path[1:], 1):
        if np.hypot(x, y) > ROUNDEL_R - 0.8:
            break
        side = 1 if k % 2 else -1
        tx, ty = path[k] - path[k - 1]
        ang = math.atan2(ty, tx) + side * 0.55
        L, Wd = leaf[0] * rng.uniform(0.8, 1.15), leaf[1]
        c = np.array([x, y]) + 0.18 * side * np.array([-ty, tx]) / (math.hypot(tx, ty) + 1e-9)
        u = np.array([math.cos(ang), math.sin(ang)])
        n = np.array([-u[1], u[0]])
        cv.poly([c - u * L / 2, c + n * Wd / 2, c + u * L / 2, c - n * Wd / 2], motif)


def dots(cv, centre, radii, n, rng, motif, r_dot=(0.16, 0.26)):
    """Moss dots (苔点) scattered in an ellipse: tiny round pieces, each its own."""
    a = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    for _ in range(n):
        th, rr = rng.uniform(0, 2 * np.pi), math.sqrt(rng.uniform(0, 1))
        x, y = centre[0] + radii[0] * rr * math.cos(th), centre[1] + radii[1] * rr * math.sin(th)
        r = rng.uniform(*r_dot)
        cv.poly(np.c_[x + r * np.cos(a), y + r * 0.8 * np.sin(a)], motif)


def compose(cv):
    rng = cv.rng
    # --- water: fine wavy lines, broken into runs as engraved water lines are (rocks and banks overwrite them)
    for j, y in enumerate(np.arange(-14.0, 21.0, 1.15)):
        x = np.linspace(-46, 46, 600)
        yy = y + 0.3 * np.sin(x / 2.1 + j * 1.3) + 0.15 * np.sin(x / 0.8 + j)
        keep = np.hypot(x, yy) < ROUNDEL_R - 1.0
        for x0 in np.sort(rng.uniform(-46, 46, 9)):
            L = rng.uniform(4.0, 11.0)
            sel = keep & (x >= x0) & (x <= x0 + L)
            if sel.sum() > 4:
                cv.strip(np.c_[x[sel], yy[sel]], rng.choice([0.28, 0.34]), "water", seg=2.6)
    # --- distant hills at the top, layered, cut fine, with texture strokes (皴)
    hills = [(-30, 30.5, 13, 5.5), (-14, 33.0, 10, 5.0), (9, 31.5, 12, 4.0), (34, 29.0, 8, 3.5)]
    for i, (cx, cy, rx, ry) in enumerate(hills):
        a = np.linspace(0, np.pi, 30)
        top = np.c_[cx + rx * np.cos(a), cy + ry * np.sin(a) * (1 + 0.15 * np.sin(5 * a + i))]
        P = np.r_[top, [[cx - rx, cy - 1.2], [cx + rx, cy - 1.2]]]
        cv.mosaic(P, 1.8, "hill" if i % 2 == 0 else "hill2", cuts=26)
    # --- the moon (a few pieces) and cloud scrolls of thin threads
    a = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    cv.mosaic(np.c_[-1.0 + 2.0 * np.cos(a), 33.6 + 2.0 * np.sin(a)], 1.4, "moon")
    for k, (cx, cy) in enumerate(((-4.0, 27.6), (13.0, 27.2))):
        th = np.linspace(0, 1.6 * np.pi, 40)
        r = 0.4 + 0.45 * th / np.pi
        cv.strip(np.c_[cx + r * np.cos(th), cy + 0.7 * r * np.sin(th)], 0.3, "cloud", seg=1.8)
        x = np.linspace(cx - 4.5, cx + 0.2, 30)
        cv.strip(np.c_[x, cy - 0.9 + 0.25 * np.sin(x / 0.9)], 0.3, "cloud", seg=1.6)
    # --- geese: tiny chevrons at the upper right
    for gx, gy in ((6.5, 26.0), (8.6, 25.3), (10.2, 26.4), (12.0, 25.6)):
        cv.strip([[gx - 0.7, gy + 0.3], [gx, gy], [gx + 0.7, gy + 0.3]], 0.3, "bird")
    # --- the pavilion on the right bank
    px, py = 22.0, 17.0
    cv.mosaic([[px - 7.5, py], [px + 7.5, py], [px + 6.8, py - 1.2], [px - 6.8, py - 1.2]], 1.3, "pavilion")  # platform
    cv.mosaic(blob(px, py - 4.2, 9.5, 3.4, rng, flat_bottom=False), 1.6, "rock", cuts=20)               # its rock base
    dots(cv, (px - 6.0, py - 1.6), (3.0, 0.9), 14, rng, "moss")
    for xx in (px - 5.0, px - 1.7, px + 1.7, px + 5.0):                                               # posts
        cv.strip([[xx, py + 0.1], [xx, py + 5.4]], 0.38, "pavilion", taper=False)
    cv.strip([[px - 5.4, py + 1.6], [px + 5.4, py + 1.6]], 0.3, "rail", seg=1.4, taper=False)          # railing
    for xx in np.linspace(px - 5.0, px + 5.0, 7)[:-1] + 0.83:                                          # lattice
        cv.strip([[xx - 0.6, py + 0.3], [xx + 0.6, py + 1.5]], 0.3, "rail", taper=False)
    roof = [[px - 8.8, py + 6.6], [px - 7.2, py + 5.6], [px - 4.0, py + 6.4], [px, py + 9.6], [px + 4.0, py + 6.4],
            [px + 7.2, py + 5.6], [px + 8.8, py + 6.6], [px + 7.6, py + 6.0], [px + 4.6, py + 7.4],
            [px, py + 10.8], [px - 4.6, py + 7.4], [px - 7.6, py + 6.0]]
    cv.mosaic(np.array(roof)[[0, 1, 2, 3, 9, 10, 11]], 1.3, "roof")
    cv.mosaic(np.array(roof)[[3, 4, 5, 6, 7, 8, 9]], 1.3, "roof")
    for xx in np.linspace(px - 6, px + 6, 13):                                                       # tile lines
        cv.cut([[xx, py + 6.0 + 0.1 * abs(xx - px)], [px + 0.55 * (xx - px), py + 9.6 - 0.1 * abs(xx - px)]])
    cv.strip([[px - 0.5, py + 10.6], [px, py + 11.8], [px + 0.5, py + 10.6]], 0.3, "roof")              # finial
    # --- the bridge, arched, of planks, with a railing
    bx0, bx1, by, h = -13.0, 17.0, 14.0, 3.2
    xs = np.linspace(bx0, bx1, 300)
    arch = by + h * np.sin(np.pi * (xs - bx0) / (bx1 - bx0))
    n = 26
    edges = np.linspace(bx0, bx1, n + 1)
    for i in range(n):
        s = (xs >= edges[i] + 0.04) & (xs <= edges[i + 1] - 0.04)
        top = np.c_[xs[s], arch[s]]
        cv.poly(np.r_[top, (top - [0, 1.1])[::-1]], "bridge")
    rail = arch + 2.0
    cv.strip(np.c_[xs, rail], 0.32, "rail", seg=2.0, taper=False)
    cv.strip(np.c_[xs, arch + 1.0], 0.3, "rail", seg=2.0, taper=False)
    for xx in np.linspace(bx0 + 0.8, bx1 - 0.8, 16):
        yy = by + h * math.sin(math.pi * (xx - bx0) / (bx1 - bx0))
        cv.strip([[xx, yy], [xx, yy + 2.0]], 0.3, "rail", taper=False)
    for xx in (bx0 + 3.5, bx1 - 3.5):                                                                 # piers
        yy = by + h * math.sin(math.pi * (xx - bx0) / (bx1 - bx0)) - 1.1
        cv.mosaic([[xx - 0.7, yy], [xx + 0.7, yy], [xx + 1.0, yy - 3.0], [xx - 1.0, yy - 3.0]], 0.9, "bridge")
    # --- the figure with an umbrella, on the bridge's crown, walking right; drawn 1.5x so it reads seen obliquely
    fx = 3.2
    fy = by + h * math.sin(math.pi * (fx - bx0) / (bx1 - bx0))
    Z = 1.5
    f = lambda pts: [[fx + Z * (p[0] - fx), fy + Z * (p[1] - fy)] for p in pts]
    robe = [[fx - 1.3, fy + 0.15], [fx + 1.4, fy + 0.15], [fx + 0.9, fy + 3.4], [fx + 0.55, fy + 4.6],
            [fx - 0.55, fy + 4.6], [fx - 0.9, fy + 3.4]]
    cv.poly(f(robe), "robe")
    cv.poly(f([[fx + 0.4, fy + 4.2], [fx + 1.9, fy + 3.3], [fx + 2.0, fy + 2.7], [fx + 0.6, fy + 3.3]]), "robe2")  # sleeve
    cv.cut(f([[fx - 0.3, fy + 4.3], [fx - 0.6, fy + 0.4]]), 0.1)
    cv.cut(f([[fx + 0.4, fy + 3.6], [fx + 0.7, fy + 0.4]]), 0.1)
    cv.cut(f([[fx - 0.8, fy + 3.3], [fx + 0.9, fy + 3.3]]), 0.1)
    for dx in (-0.55, 0.6):                                                                           # feet
        cv.strip(f([[fx + dx, fy + 0.2], [fx + dx + 0.25, fy - 0.3]]), 0.3, "robe")
    a = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    cv.poly(f(np.c_[fx + 0.1 + 0.62 * np.cos(a), fy + 5.3 + 0.7 * np.sin(a)]), "skin")               # head
    ux, uy = fx + 0.7, fy + 7.4                                                                      # umbrella crown
    cv.strip(f([[fx + 1.9, fy + 3.0], [ux, uy]]), 0.3, "rail", taper=False)                           # handle
    rim = np.array([[ux - 3.6, uy - 1.9], [ux - 1.8, uy - 1.2], [ux, uy - 1.0], [ux + 1.8, uy - 1.2], [ux + 3.6, uy - 1.9]])
    for i in range(4):                                                                                # four panels
        cv.poly(f([[ux, uy + 0.45], rim[i], rim[i + 1]]), "umbrella")
    for r in rim:                                                                                     # ribs incised
        cv.cut(f([[ux, uy + 0.4], r]), 0.1)
    # --- the left bank: rocks cut fine, moss dots, grass
    cv.mosaic(blob(-25, 9.0, 14, 5.5, rng), 1.7, "rock", cuts=40)
    cv.mosaic(blob(-35, 15.5, 6.0, 4.5, rng), 1.1, "rock2", cuts=16)
    cv.mosaic(blob(-12, 6.0, 5.5, 3.0, rng), 1.1, "rock2", cuts=12)
    dots(cv, (-30.0, 14.6), (6.0, 1.0), 22, rng, "moss")
    dots(cv, (-36.0, 20.0), (3.0, 0.8), 10, rng, "moss")
    # --- the willow: trunk, branches, and strands of leaf chains
    trunk = np.array([[-27.0, 12.0], [-26.0, 18.0], [-27.5, 23.0], [-25.5, 28.0], [-22.0, 31.0]])
    for k, wdt in ((0, 2.0), (1, 1.6)):
        T = trunk + [0.4 * k, 0]
        cv.strip(T[k:], wdt - 0.4 * k, "trunk", seg=1.8)
    for i in range(10):
        cv.cut([[-27.3 + 0.15 * i, 13 + 1.7 * i], [-26.2 + 0.15 * i, 13.6 + 1.7 * i]], 0.1)
    branches = [[[-25.5, 28.0], [-19.0, 33.0], [-11.0, 33.5]], [[-26.0, 25.0], [-33.0, 30.0], [-37.0, 30.5]],
                [[-22.0, 31.0], [-17.5, 37.0], [-12.0, 38.5]], [[-26.5, 21.0], [-31.0, 25.5]]]
    for B in branches:
        B = np.array(B)
        cv.strip(B, 0.5, "trunk", seg=1.8)
        for s in np.linspace(0.15, 1.0, 6):
            p0 = B[0] + (B[-1] - B[0]) * s
            leaf_chain(cv, p0, rng.uniform(5.0, 11.0), rng.uniform(-1.5, 1.5), rng)
    for gx in np.linspace(-40, -14, 13):
        gy = 13.0 + 3.0 * math.sin(gx / 4)
        for ang in (-0.5, 0.0, 0.45):
            cv.strip([[gx, gy], [gx + 1.4 * math.sin(ang), gy + 1.6 * math.cos(ang)]], 0.3, "grass")
    # --- right bank rocks, ducks on the water, reeds
    cv.mosaic(blob(33, 10.5, 9.0, 4.2, rng), 1.6, "rock", cuts=22)
    dots(cv, (31.0, 14.2), (5.0, 0.8), 14, rng, "moss")
    for gx in np.linspace(26, 40, 8):
        gy = 14.2 + 0.6 * math.sin(gx)
        for ang in (-0.35, 0.3):
            cv.strip([[gx, gy], [gx + 1.8 * math.sin(ang), gy + 2.2 * math.cos(ang)]], 0.3, "grass")
    for dx, dy in ((15.5, 5.0), (19.0, 4.2)):
        cv.poly(blob(dx, dy, 1.4, 0.6, rng, n=16, rough=0.05), "bird")
        a = np.linspace(0, 2 * np.pi, 12, endpoint=False)
        cv.poly(np.c_[dx + 1.2 + 0.35 * np.cos(a), dy + 0.75 + 0.35 * np.sin(a)], "bird")
    # --- the border: two thin rings and a band of lozenges between them, outside the picture (placed directly)
    cv.placed = True
    # the two rings as short dashes with gaps (round 1's near-continuous shell rings lit up as a neon line)
    for r in BORDER:
        segs = int(2 * np.pi * r / 1.2)
        for i in range(segs):
            a = np.linspace(2 * np.pi * i / segs, 2 * np.pi * (i + 0.55) / segs, 12)
            cv.strip(np.c_[r * np.cos(a), r * np.sin(a)], 0.3, "border", taper=False)
    rm = 0.5 * (BORDER[0] + BORDER[1])
    n = int(2 * np.pi * rm / 1.6)
    for i in range(n):
        th = 2 * np.pi * (i + 0.5) / n
        c, s = math.cos(th), math.sin(th)
        q = [(rm - 0.9, 0), (rm, 0.55), (rm + 0.9, 0), (rm, -0.55)]
        cv.poly([(r_ * c - t_ * s, r_ * s + t_ * c) for r_, t_ in q], "border")
    # clip the picture to its field (between the field and the border's inner ring: lacquer)
    ids = cv.ids()
    W, H = cv.W, cv.H
    xs = cv.x0 + (np.arange(W) + 0.5) * cv.t
    ys = cv.y1 - (np.arange(H) + 0.5) * cv.t
    R = np.hypot(*np.meshgrid(xs, ys))
    border_ids = {i for i, p in enumerate(cv.pieces) if p and p["motif"] == "border"}
    is_border = np.isin(ids, list(border_ids))
    ids[(R > ROUNDEL_R) & ~is_border] = 0
    ids[R > BORDER[1] + 0.3] = 0
    return ids


def seams(ids):
    """One texel of lacquer wherever two different pieces touch."""
    out = ids.copy()
    d = np.zeros(ids.shape, bool)
    d[:, 1:] |= (ids[:, 1:] != ids[:, :-1]) & (ids[:, 1:] > 0) & (ids[:, :-1] > 0)
    d[1:, :] |= (ids[1:, :] != ids[:-1, :]) & (ids[1:, :] > 0) & (ids[:-1, :] > 0)
    out[d] = 0
    return out


def maps(extent_design, d_axis, seed):
    """extent_design = (x0, x1, y0, y1) in design mm. Returns (inlay, layers, extent_object, stats, ids, pieces).
    The maps are in OBJECT space: object x = -design x, so their columns are flipped and the extent's x negated."""
    x0, x1, y0, y1 = extent_design
    cv = Canvas(x0, x1, y0, y1, TEXEL_MM, np.random.default_rng(seed))
    ids = seams(compose(cv))
    ids[0, :] = ids[-1, :] = ids[:, 0] = ids[:, -1] = 0          # EXTEND sampling outside: lacquer
    P = cv.pieces
    shell = ids > 0
    d = np.array([0.0] + [p["d_nm"] for p in P[1:]])[ids]
    tilt = np.array([[0.0, 0.0]] + [p["tilt"] for p in P[1:]])[ids]
    # each piece's curvature about its centroid (design mm)
    rng = np.random.default_rng(seed + 1000)
    K = np.r_[0.0, rng.choice([-1.0, 1.0], len(P) - 1) / rng.uniform(*SHELL_R_MM, len(P) - 1)]
    rows, cols = np.indices(ids.shape)
    X = x0 + (cols + 0.5) * TEXEL_MM
    Y = y1 - (rows + 0.5) * TEXEL_MM
    n = np.bincount(ids.ravel(), minlength=len(P)).astype(float)
    cx = np.bincount(ids.ravel(), X.ravel(), minlength=len(P)) / np.maximum(n, 1)
    cy = np.bincount(ids.ravel(), Y.ravel(), minlength=len(P)) / np.maximum(n, 1)
    tilt = tilt + np.stack([(X - cx[ids]) * K[ids], (Y - cy[ids]) * K[ids]], -1)
    # the flame (growth bands) inside each piece, fixed in object space: the nacre's tablet thickness and the layers'
    # slope both vary in bands across the piece (the layers are corrugated along the growth lines). Per piece a band
    # direction u, a period and a phase; a smooth warp makes the bands wavy. d += FLAME_D cos(phi) and the layers'
    # slope along u += FLAME_TILT cos(phi): thicker tablets where the layers lean one way [A, both]. In phase, not in
    # quadrature: a light that picks out one slope then picks out one thickness, so as the light moves the lit bands'
    # hue moves; in quadrature (tried) the two branches of equal slope have opposite d and the piece's hue averages out
    ang = rng.uniform(0, np.pi, len(P))
    per = rng.uniform(*FLAME_PERIOD_MM, len(P))
    ph = rng.uniform(0, 2 * np.pi, len(P))
    warp = ndimage.gaussian_filter(rng.normal(0, 1, ids.shape).astype(np.float32), FLAME_WARP_MM[1] / TEXEL_MM, mode="wrap")
    warp *= FLAME_WARP_MM[0] / (warp.std() + 1e-12)
    ux, uy = np.cos(ang)[ids], np.sin(ang)[ids]
    phi = 2 * np.pi * ((X - cx[ids]) * ux + (Y - cy[ids]) * uy + warp) / per[ids] + ph[ids]
    d = d + np.where(shell, FLAME_D_NM * np.cos(phi), 0.0)
    slope = math.radians(FLAME_TILT_DEG) * np.cos(phi)
    tilt = tilt + np.stack([slope * ux, slope * uy], -1) * shell[..., None]
    del phi, warp, ux, uy
    d = np.clip(d, d_axis[0], d_axis[1])
    dn = np.where(shell, (d - d_axis[0]) / (d_axis[1] - d_axis[0]), 0.0)
    if dn[shell].min() < 0 or dn[shell].max() > 1:
        raise SystemExit("piece colours fall outside the nacre table")
    # the layers' normal in DESIGN space (floor normal +z, tilted), then to object space (x negated)
    Ld = np.stack([np.tan(tilt[..., 0]), np.tan(tilt[..., 1]), np.ones(ids.shape)], -1)
    Ld /= np.linalg.norm(Ld, axis=-1, keepdims=True)
    Lo = Ld * np.array([-1.0, 1.0, 1.0])
    # image rows run y down in design; maps want row 0 = y0 (bottom) and columns along object x (= -design x)
    flip = lambda a: a[::-1, ::-1]
    inlay = flip(np.stack([shell.astype(float), dn, np.zeros_like(dn)], -1))
    layers = flip(0.5 * (Lo + 1))
    ext_obj = (-x1, -x0, y0, y1)
    used = np.unique(ids[ids > 0])
    stats = {"pieces": int(len(used)), "shell_fraction": float(shell.mean()), "texels": [cv.W, cv.H]}
    return inlay.astype(np.float16), layers.astype(np.float16), ext_obj, stats, ids, P


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="preview the design as an image (pieces in random greys)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=19)
    a = ap.parse_args()
    inlay, layers, ext, st, ids, P = maps((-50, 50, 14, 58), (240, 560), a.seed)
    rng = np.random.default_rng(0)
    lut = rng.uniform(0.35, 1.0, len(P))
    lut[0] = 0.04
    d = np.array([0.0] + [p["d_nm"] for p in P[1:]])
    hue = np.clip((d - 300) / 200, 0, 1)
    rgb = np.stack([lut * (0.6 + 0.4 * hue), lut * (0.8 - 0.2 * hue), lut * (1.0 - 0.5 * hue)], -1)[ids]
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((ids.shape[1] // 2, ids.shape[0] // 2),
                                                                       Image.LANCZOS).save(a.out)
    print(st, "->", a.out)
