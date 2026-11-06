"""s49: plique-a-jour (空窗珐琅) carp flank, macro. No body, no backing: gilt wire and glass, light from behind.

    python3 -I v2/stills/s49_yulin.py flat            pattern and colour, no render: out/v2/s49_falang/yulin_flat.jpg
    python3 -I v2/stills/s49_yulin.py preview|mid
    python3 -I v2/stills/s49_yulin.py final           out/v2/s49_falang/cand.*

Head to the left, tail to the right, neither in the frame. The back is the arc. Scales overlap as on a fish: each one's round edge towards the tail; a scale nearer the head lies over one nearer the tail. The pattern is generated, nothing is traced. No lateral-line pores: ringed by wire, they read as eyes or rivets.

General knowledge, not measured: enamel in an unbacked cell draws in by surface tension, both faces concave, thin in the middle and thick against the wire; so a cell is light in the middle, deep at the wire, and a small lens.
Estimates (no measured values behind them): glass 0.6 mm at a cell's middle, 0.84 mm at the wire; scale 8-12 mm wide; wire 0.3-0.5 mm; IOR 1.5. Colours are appearance targets: the transmission of 0.5 mm of glass, set by eye.
Real here: closed glass solids, one to a cell, Glass BSDF with homogeneous Volume Absorption (Beer-Lambert), so depth of colour follows thickness; bubbles as real inner surfaces; wire as geometry.
Stand-ins: the window is an emitting panel seen only in reflections; the camera does not see the part of the light behind that runs above the back, by a visibility flag instead of a black flag; a bubble is a sphere of relative IOR 1/1.5 inside the glass, with no volume priority; the light behind is an emitting surface; the sheet's overall curve is our choice.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from kit import OUT, fbm, frame_camera, shoot, sstep

NAME = "s49_falang"
SEED = 4917
W, DIST = 9.0, 60.0
APEX_Y = 0.49
SAG = 0.095  # sagitta of the back over the frame's width. The original's median is .08
NSCALE = 12.0  # scales across the frame
LO, HI = -0.62 * W, 0.62 * W  # the sheet runs past the frame's sides
DEPTH = 4.3  # and past its bottom, measured down from the back
THIN, THICK = 0.03, 0.042  # half thickness at a cell's middle and against the wire, cm: estimates
WIRE = 0.0165  # half width, cm: 0.33 mm across. Estimate
WIRE_H = 0.078  # half height of the wire: stands proud of the glass on both faces
CURVE_X, CURVE_Y = 34.0, 11.0  # the body's radii of curvature, ours
BACK_D = 1.6  # the light stands this far behind the sheet
WIN_SLANT, WIN_C, WIN_HALF = 13.0, (-1.5, -1.0), 0.32  # the window's reflection on the sheet: slant in degrees, middle, half width in cm
HERE = os.path.dirname(os.path.abspath(__file__))

H_FRAME = W * 9.0 / 16.0
Y_APEX = 0.0
R_BACK = ((0.25 + SAG**2) / (2 * SAG)) * W

# Spine to belly, transmission of the thin middle of a cell. The magenta here is bluer than the target #E6007E, since depth pushes it towards red and the target is for what is seen. Neighbouring hues only, magenta to violet to electric blue: all five stages read as a rainbow, a toy (coordinator, on the first version, kept as cand_caihong)
STOPS = [(0.0, (232, 0, 172)), (0.34, (205, 0, 190)), (0.6, (120, 10, 222)), (0.84, (44, 30, 240)), (1.0, (20, 48, 246))]
SPAN = 2.9  # cm from the back at which the last stop is reached


def lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c < 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


_T = np.array([s[0] for s in STOPS])
_C = np.array([lin(s[1]) for s in STOPS])


def ramp(t):
    t = np.clip(t, 0, 1)
    return np.array([np.interp(t, _T, _C[:, k]) for k in range(3)])


def back(x):
    """The height of the back above its apex (never positive)."""
    return np.sqrt(np.maximum(R_BACK**2 - x**2, 1.0)) - R_BACK


def scales(rng):
    """Centres in (x along the body, s down from the back), staggered, with a shear along the body and scales growing towards the belly. Returned in painter's order: tail first, head last, so that a scale nearer the head lies over."""
    dx = W / NSCALE
    out = []
    col = np.arange(int(LO / dx) - 3, int(HI / dx) + 4)
    for k in col:
        s = -0.2 + (0.5 if k % 2 else 0.0) * 0.62
        j = 0
        while s < DEPTH + 0.8:
            size = 0.86 + 0.34 * np.clip(s / 3.4, 0, 1)
            shear = 0.06 * s + 0.012 * s * s  # the rows lean along the body as the flank turns
            x = (k * dx + shear + rng.normal(0, 0.012)) * (1.0 + 0.012 * np.sin(k * 0.7))
            out.append(dict(x=x, s=s + rng.normal(0, 0.012), size=size * rng.uniform(0.97, 1.03), k=int(k), j=j, tilt=0.04 * np.cos(s) + rng.normal(0, 0.025), ph=rng.uniform(0, 6.28, 3)))
            s += 0.62 * size
            j += 1
    out.sort(key=lambda d: -d["x"])
    return out


def outline(c, rng, t):
    """A scale's edge, drawn by hand: round on the tail's side, tucked under its neighbours on the head's. t scales it towards its own root, for the inner wire."""
    dx = W / NSCALE
    a = np.linspace(-np.pi, np.pi, 120, endpoint=False)
    ra, rb = 1.1 * dx * c["size"], 0.47 * c["size"]
    wob = 1 + 0.018 * np.sin(2 * a + c["ph"][0]) + 0.012 * np.sin(5 * a + c["ph"][1]) + 0.006 * np.sin(9 * a + c["ph"][2])
    ex = ra * np.cos(a) * wob
    ey = rb * np.sin(a) * wob
    root = -0.3 * ra
    ex, ey = root + (ex - root) * t, ey * t
    ct, st = np.cos(c["tilt"]), np.sin(c["tilt"])
    return np.stack([c["x"] + ex * ct - ey * st, back(c["x"] + ex) - c["s"] + ex * st + ey * ct], 1)


def paint(pxcm):
    """Labels on a grid in (x, y): 0 is nothing (above the back), each cell its own number. Also a table of cells."""
    y_top = 0.12
    y_bot = back(HI) - DEPTH
    nx, ny = int((HI - LO) * pxcm), int((y_top - y_bot) * pxcm)
    xs = LO + (np.arange(nx) + 0.5) / pxcm
    ys = y_bot + (np.arange(ny) + 0.5) / pxcm
    rng = np.random.default_rng(SEED)
    L = np.zeros((ny, nx), np.int32)
    cells = [None]

    def to(p):
        return np.round(np.stack([(p[:, 0] - LO) * pxcm - 0.5, (p[:, 1] - y_bot) * pxcm - 0.5], 1) * 16).astype(np.int32)

    def fill(p, meta):
        cells.append(meta)
        cv2.fillPoly(L, [to(p)], len(cells) - 1, cv2.LINE_8, shift=4)

    S = scales(rng)
    for c in S:
        # one colour for the scale: where it sits, a little off, and now and then a wrong one, as a hand mixes
        t = c["s"] / SPAN + rng.normal(0, 0.1)  # no clean bands: neighbours in a row differ in depth and hue
        wrong = rng.random() < 0.03
        if wrong:
            t = rng.uniform(0, 1)
        col = ramp(t) ** rng.uniform(0.75, 1.75) * rng.uniform(0.9, 1.08)  # a thicker or thinner batch of the same frit
        fill(outline(c, rng, 1.0), dict(col=np.clip(col, 0.004, 1), part="rim"))
        # most scales are two cells: a paler rim and a deeper root, parted by a wire that is not quite parallel to the edge. Radial wires are few
        if rng.random() < 0.4:
            t2 = rng.uniform(0.66, 0.78)
            c2 = dict(c, tilt=c["tilt"] + rng.normal(0, 0.04), ph=c["ph"] + rng.normal(0, 0.5, 3))
            fill(outline(c2, rng, t2), dict(col=np.clip(ramp(t + rng.normal(0.05, 0.03)) ** 1.35 * rng.uniform(0.92, 1.05), 0.002, 1), part="root"))
    # nothing above the back
    X, Y = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
    wob = 0.006 * np.sin(X * 1.7 + 0.4) + 0.004 * np.sin(X * 4.1 + 2.0)
    above = Y > back(X) + wob
    L[above] = 0
    return X, Y, L, cells


def wires(X, Y, L, pxcm):
    """Distance to the nearest wire's centre and that wire's half width there, which swells and thins by hand and beads at joints."""
    edge = np.zeros(L.shape, bool)
    edge[:-1] |= L[:-1] != L[1:]
    edge[1:] |= L[:-1] != L[1:]
    edge[:, :-1] |= L[:, :-1] != L[:, 1:]
    edge[:, 1:] |= L[:, :-1] != L[:, 1:]
    d = cv2.distanceTransform((~edge).astype(np.uint8), cv2.DIST_L2, 5) / pxcm
    d = cv2.GaussianBlur(d, (0, 0), max(0.8, 0.008 * pxcm))  # a raster's edge has corners; a drawn wire has none
    shape = L.shape
    hw = WIRE * (1 + 0.18 * fbm(shape, pxcm, 0.15, 0.7, 2.2, SEED + 1) + 0.02 * fbm(shape, pxcm, 0.05, 0.15, 2.0, SEED + 2))
    # the back is a heavier wire: it carries the sheet
    top = cv2.dilate((L == 0).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    dtop = cv2.distanceTransform((~top).astype(np.uint8), cv2.DIST_L2, 5) / pxcm
    hw = hw * (1 + 0.4 * np.exp(-((dtop / 0.05) ** 2)))
    # solder: where three cells meet, some joints got a bead, and it is never round
    sr = np.random.default_rng(SEED + 3)
    jn = np.zeros(shape, np.float32)
    a, b, c_ = L[:-1, :-1], L[:-1, 1:], L[1:, :-1]
    j = (a != b) & (a != c_) & (b != c_) & (a > 0) & (b > 0) & (c_ > 0)
    ys, xs = np.nonzero(j)
    if len(ys):
        keep = sr.random(len(ys)) < 0.45
        for y, x in zip(ys[keep], xs[keep]):
            r = max(1, int(sr.uniform(0.014, 0.034) * pxcm))
            cv2.ellipse(jn, (int(x), int(y)), (r, max(1, int(r * sr.uniform(0.6, 1.0)))), sr.uniform(0, 180), 0, 360, 1.0, -1)
    jn = cv2.GaussianBlur(jn, (0, 0), max(0.8, 0.008 * pxcm))
    hw = hw * (1 + 1.4 * np.clip(jn, 0, 1))
    return d, hw.astype(np.float32), jn


def flaws(X, Y, L, cells, d, pxcm):
    """A few pinholes and a few cells that drew back from the wire: where the glass is not. Bubbles in the glass, of all sizes, more near wires where they were trapped."""
    r = np.random.default_rng(SEED + 5)
    hole = np.zeros(L.shape, np.uint8)
    cand = np.nonzero((d > 0.07) & (L > 0))
    for i in r.integers(0, len(cand[0]), 3):
        y, x = cand[0][i], cand[1][i]
        rad = max(1, int(r.uniform(0.004, 0.008) * pxcm))
        cv2.circle(hole, (int(x), int(y)), rad, 1, -1)
    # a shrunk edge: a crescent against the wire, in three cells
    rims = [i for i, c in enumerate(cells) if c and c["part"] == "rim"]
    for i in r.choice(rims, 3, replace=False):
        ys, xs = np.nonzero((L == i) & (d < 0.075) & (d > 0.03))
        if len(xs) < 20:
            continue
        k = r.integers(0, len(xs))
        m = np.hypot(xs - xs[k], ys - ys[k]) < r.uniform(0.05, 0.1) * pxcm
        hole[ys[m], xs[m]] = 1
    hole = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), max(0.7, 0.006 * pxcm)) > 0.5
    B = []
    cand2 = np.nonzero((d > 0.03) & (L > 0) & ~hole)
    near = np.exp(-d[cand2] / 0.08)
    p = near / near.sum()
    # log-normal sizes: many fine, a few large
    for i in r.choice(len(cand2[0]), 800, replace=False, p=p):
        B.append((X[cand2[0][i], cand2[1][i]], Y[cand2[0][i], cand2[1][i]], float(np.clip(r.lognormal(np.log(0.0026), 0.45), 0.0012, 0.0065))))
    return hole, np.array(B)


def half_thickness(d, hw, hole, shape, pxcm):
    """Both faces concave: thick against the wire, thin in the middle, and each face with its own slow ripple. Where the glass drew back it thins to nothing."""
    dg = np.maximum(d - hw * 0.8, 0)
    h = THIN + (THICK - THIN) * np.exp(-dg / 0.095)
    if hole.any():
        dh = cv2.distanceTransform((~hole).astype(np.uint8), cv2.DIST_L2, 5) / pxcm
        h = h * sstep(0.0, 0.035, dh)
    top = h + 0.00028 * fbm(shape, pxcm, 0.25, 0.9, 2.4, SEED + 7) + 0.000012 * fbm(shape, pxcm, 0.05, 0.14, 2.0, SEED + 8)
    bot = h + 0.00028 * fbm(shape, pxcm, 0.25, 0.9, 2.4, SEED + 9)
    return np.maximum(top, 0.0005).astype(np.float32), np.maximum(bot, 0.0005).astype(np.float32)


def world(X, Y, z):
    """Sheet (x, y up, z towards the camera) to the world: the camera is on -Y, Z is up. The flank curves away from the camera at the sides and up the back."""
    yc = Y + 1.2
    zz = z - X**2 / (2 * CURVE_X) - yc**2 / (2 * CURVE_Y)
    return np.stack([X, -zz, Y], -1).astype(np.float32)


def closed(idx_mask, X, Y, top, bot):
    """A closed solid from a mask on the grid: a top and a bottom sheet and side walls along the mask's edges, wound outward. Returns V, F."""
    m = idx_mask
    q = m[:-1, :-1] & m[:-1, 1:] & m[1:, :-1] & m[1:, 1:]
    ys, xs = np.nonzero(q)
    if not len(ys):
        return None
    used = np.zeros(m.shape, bool)
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
        used[ys + dy, xs + dx] = True
    vy, vx = np.nonzero(used)
    n = len(vy)
    ix = -np.ones(m.shape, np.int64)
    ix[vy, vx] = np.arange(n)
    Vt = world(X[vy, vx], Y[vy, vx], top[vy, vx])
    Vb = world(X[vy, vx], Y[vy, vx], -bot[vy, vx])
    a, b, c, e = ix[ys, xs], ix[ys, xs + 1], ix[ys + 1, xs], ix[ys + 1, xs + 1]
    # the sheet's +z is the world's -Y; (x, y, z) -> (x, -z, y) keeps handedness, so a face wound counter-clockwise in (x, y) faces +z
    Ft = np.concatenate([np.stack([a, b, e], 1), np.stack([a, e, c], 1)])
    Fb = np.concatenate([np.stack([a, e, b], 1), np.stack([a, c, e], 1)]) + n
    # the walls: edges of the quad set
    h = np.zeros((q.shape[0] + 1, q.shape[1]), bool)  # horizontal edges
    v = np.zeros((q.shape[0], q.shape[1] + 1), bool)
    h[:-1] ^= q
    h[1:] ^= q
    v[:, :-1] ^= q
    v[:, 1:] ^= q
    W_ = []
    hy, hx = np.nonzero(h)
    for y, x in zip(hy, hx):
        p0, p1 = ix[y, x], ix[y, x + 1]
        if y < q.shape[0] and q[y, x]:  # the quad is above this edge: outward is -y, so run +x on top ... seen from outside
            W_.append((p0, p0 + n, p1 + n))
            W_.append((p0, p1 + n, p1))
        else:
            W_.append((p1, p1 + n, p0 + n))
            W_.append((p1, p0 + n, p0))
    vy2, vx2 = np.nonzero(v)
    for y, x in zip(vy2, vx2):
        p0, p1 = ix[y, x], ix[y + 1, x]
        if x < q.shape[1] and q[y, x]:  # the quad is to the right: outward is -x
            W_.append((p1, p1 + n, p0 + n))
            W_.append((p1, p0 + n, p0))
        else:
            W_.append((p0, p0 + n, p1 + n))
            W_.append((p0, p1 + n, p1))
    F = np.concatenate([Ft, Fb, np.array(W_, np.int64)]) if W_ else np.concatenate([Ft, Fb])
    return np.concatenate([Vt, Vb]), F.astype(np.int32)


def signed_volume(V, F):
    a, b, c = V[F[:, 0]].astype(np.float64), V[F[:, 1]].astype(np.float64), V[F[:, 2]].astype(np.float64)
    return float((a * np.cross(b, c)).sum() / 6.0)


def wire_mesh(X, Y, d, hw, jn, pxcm):
    """The wire, a closed oval section round the mid-plane: top and bottom sheets meeting at the wire's edge. Vertices on the edge are slid onto the true outline, or the grid would show as stairs against the glass."""
    gy, gx = np.gradient(cv2.GaussianBlur(d, (0, 0), 0.8), 1.0 / pxcm)
    gn = np.hypot(gx, gy) + 1e-6
    ins = d < hw
    band = cv2.dilate(ins.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    # the slid position: outside vertices of the band move back onto d = hw
    move = np.where(band & ~ins, d - hw, 0.0)
    move = np.minimum(move, 2.2 / pxcm)
    X2 = X - (move * gx / gn).astype(np.float32)
    Y2 = Y - (move * gy / gn).astype(np.float32)
    rel = np.clip(d / np.maximum(hw, 1e-5), 0, 1)
    z = WIRE_H * np.sqrt(1 - rel**2) * (1 + 0.09 * fbm(d.shape, pxcm, 0.06, 0.3, 2.0, SEED + 11)) * (1 + 0.5 * np.clip(jn, 0, 1))
    z = z.astype(np.float32)
    z[~ins] = 0.00002
    return closed(band, X2, Y2, z, z)


def bubble_mesh(B, X0, Y0, top):
    """Small spheres at the glass's mid-plane or a little off it. Icosphere of 2 subdivisions; enough at this size."""
    t = (1 + 5**0.5) / 2
    v = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    f = np.array([(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)])
    for _ in range(2):
        vv = list(v)
        mid = {}

        def m(a, b):
            k = (min(a, b), max(a, b))
            if k not in mid:
                p = v[a] + v[b]
                vv.append(p / np.linalg.norm(p))
                mid[k] = len(vv) - 1
            return mid[k]

        nf = []
        for a, b, c in f:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        v, f = np.array(vv), np.array(nf)
    r = np.random.default_rng(SEED + 12)
    V, F, off = [], [], 0
    for x, y, rad in B:
        z = r.uniform(-0.012, 0.012)
        p = world(np.array([x]), np.array([y]), np.array([z]))[0]
        V.append(p + v * rad)
        F.append(f + off)
        off += len(v)
    return np.concatenate(V).astype(np.float32), np.concatenate(F).astype(np.int32)


def light_plane(cam_loc, res=500):
    """The light behind: a soft surface, bright and dim in slow patches, across and along. Two parts of the same field: `A` stops short of the back as the camera sees it, so that nothing of it gets above the arc, and is what a pinhole shows; `B` runs on above the back, seen only through glass, since a concave cell bends its rays well past the back (a flag would cut them, and the top scales go black). B is a stand-in for a real light's extent: its visibility is set, no flag exists. Returns (A, E_A), (B, E_B)."""
    depth = BACK_D
    scale = (DIST + depth) / DIST
    cz = float(cam_loc[2])
    r = np.random.default_rng(SEED + 14)
    blobs = [(r.uniform(-7, 7), r.uniform(-4, 0), r.uniform(2.5, 5), r.uniform(1.5, 3), r.uniform(0.3, 0.8)) for _ in range(4)]
    small = [(r.uniform(-7, 7), r.uniform(-5, 1.5), r.uniform(0.4, 1.0), r.uniform(0.3, 0.8), r.uniform(-0.7, 0.8)) for _ in range(120)]

    def field(U, y):
        E = 0.0
        for cx, cy, rx, ry, am in blobs:
            E = E + am * np.exp(-(((U - cx) / rx) ** 2) - ((y - cy) / ry) ** 2)
        E = 0.4 + E / 1.3
        for cx, cy, rx, ry, am in small:  # what a cell's lens picks up: the shading differs cell by cell
            E = E * (1 + am * np.exp(-(((U - cx) / rx) ** 2) - ((y - cy) / ry) ** 2))
        return np.maximum(E, 0.08) * (0.62 + 0.38 * sstep(0.3, -2.2, y))

    def sheet(y0, y1, off):
        u = np.linspace(LO * 1.3, HI * 1.3, res)
        v = np.linspace(0.0, 1.0, res // 2)
        U, Vv = np.meshgrid(u, v)
        y = y0(U) + (y1(U) - y0(U)) * Vv
        Xp = cam_loc[0] + (U - cam_loc[0]) * scale
        Zp = cz + (y - cz) * scale
        return np.stack([Xp, np.full_like(Xp, depth + off), Zp], -1).astype(np.float32), field(U, y).astype(np.float32)

    A = sheet(lambda U: np.full_like(U, -DEPTH - 2.0), lambda U: back(U) - 0.1, 0.02)
    B = sheet(lambda U: np.full_like(U, -DEPTH - 2.0), lambda U: np.full_like(U, 6.0), 0.0)
    return A, B


def window_panel(n=240):
    """A big soft window for the glass's skin. It is laid out in the sheet's own terms: where on the sheet a point of it is mirrored, by the sheet's overall curve. So it can be aimed: a slanted band over part of the scales. Each cell's hollow bends it further, so inside a band it breaks up cell by cell, and that is what shows the surface. Seen only in reflections. The scale factors are worked out for a mirror at this distance (a paraxial estimate), then checked in the picture."""
    Dw = 70.0
    ax = 1 + Dw * (2 / CURVE_X + 1 / DIST)
    ay = 1 + Dw * (2 / CURVE_Y + 1 / DIST)
    az = Dw * 2 * 1.2 / CURVE_Y
    u = np.linspace(-5.2, 5.2, n)
    v = np.linspace(-1.5, 1.5, n // 2)
    U, V = np.meshgrid(u, v)
    a = np.radians(WIN_SLANT)
    sx = WIN_C[0] + U * np.cos(a) - V * np.sin(a)
    sy = WIN_C[1] + U * np.sin(a) + V * np.cos(a)
    P = np.stack([ax * sx, np.full_like(sx, -Dw), ay * sy + az], -1).astype(np.float32)
    E = np.exp(-((V / WIN_HALF) ** 4)) * sstep(-3.2, -1.7, U) * sstep(3.2, 1.7, U)
    E = E * (1 - 0.42 * np.exp(-(((U - 0.9) / 0.09) ** 2)))  # one glazing bar, soft
    return P, E.astype(np.float32)


def flat(d_out):
    pxcm = 213.0
    X, Y, L, cells = paint(pxcm)
    d, hw, jn = wires(X, Y, L, pxcm)
    hole, B = flaws(X, Y, L, cells, d, pxcm)
    h, _ = half_thickness(d, hw, hole, L.shape, pxcm)
    table = np.zeros((len(cells), 3))
    for i, c in enumerate(cells):
        if c:
            table[i] = c["col"]
    # Beer-Lambert by thickness: what the glass will roughly do, under an even light
    sig = -np.log(np.clip(table, 0.003, 1)) / (2 * THIN)
    im = np.exp(-sig[L] * (2 * h)[..., None])
    im = im * (0.55 + 0.45 * sstep(-3.4, -0.6, Y))[..., None]
    wm = d < hw
    im[wm] = lin((205, 165, 90))
    im[L == 0] = 0.008
    im[(L > 0) & hole & ~wm] = 1.0
    # to the frame
    x0, x1 = -W / 2, W / 2
    y1 = Y_APEX + (APEX_Y) * H_FRAME
    y0 = y1 - H_FRAME
    i0, i1 = np.searchsorted(X[0], [x0, x1])
    j0, j1 = np.searchsorted(Y[:, 0], [y0, y1])
    pad = max(0, int((y1 - Y[-1, 0]) * pxcm))
    crop = im[j0:j1, i0:i1]
    if pad:
        crop = np.vstack([crop, np.full((pad,) + crop.shape[1:], 0.008)])
    out = (np.clip(crop, 0, 1) ** (1 / 2.2) * 255)[::-1, :, ::-1].astype(np.uint8)
    p = os.path.join(d_out, "yulin_flat.jpg")
    cv2.imwrite(p, out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(p, out.shape, "cells", len(cells) - 1, "bubbles", len(B), flush=True)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "flat"
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    if q == "flat":
        flat(d)
        return
    pxcm = {"preview": 150.0, "mid": 220.0, "final": 420.0}[q]
    X, Y, L, cells = paint(pxcm)
    d_, hw, jn = wires(X, Y, L, pxcm)
    hole, B = flaws(X, Y, L, cells, d_, pxcm)
    top, bot = half_thickness(d_, hw, hole, L.shape, pxcm)
    target = np.array([0.0, 0.0, (0.5 - APEX_Y) * H_FRAME])
    cam = frame_camera(target, (0, -1, 0), W, DIST, aperture_mm=9.0, focus_point=np.array([0.0, 0.1, -0.9]))
    tag = {"preview": "p", "mid": "m", "final": "f"}[q]
    meshes = []
    shader = os.path.join(HERE, "plique_shader.py")
    n_faces = 0
    # the cells that show in the frame or just past it; the others would only cost
    ids = np.unique(L[L > 0])
    gtmp = os.path.join(d, f"yulin_{tag}")
    os.makedirs(gtmp, exist_ok=True)
    for f in os.listdir(gtmp):
        os.remove(os.path.join(gtmp, f))
    slices = cv2.connectedComponentsWithStats  # noqa: F841
    for i in ids:
        ys, xs = np.nonzero(L == i)
        if len(xs) < 8:
            continue
        j0, j1, i0, i1 = max(ys.min() - 1, 0), ys.max() + 2, max(xs.min() - 1, 0), xs.max() + 2
        m = (L[j0:j1, i0:i1] == i) & ~hole[j0:j1, i0:i1]
        r = closed(m, X[j0:j1, i0:i1], Y[j0:j1, i0:i1], top[j0:j1, i0:i1], bot[j0:j1, i0:i1])
        if r is None:
            continue
        V, F = r
        vol = signed_volume(V, F)
        assert vol > 0, f"cell {i}: wound inward, volume {vol}"
        sig = -np.log(np.clip(cells[i]["col"], 0.003, 1)) / (2 * THIN)
        p = os.path.join(gtmp, f"c{i:04d}.npz")
        np.savez(p, V=V, F=F)
        n_faces += len(F)
        meshes.append({"name": f"c{i:04d}", "npz": p, "shader_py": shader, "params": {"kind": "glass", "sigma": sig.tolist(), "rough": 0.008}})
    print("cells", len(meshes), "faces", round(n_faces / 1e6, 2), "M", flush=True)
    Vw, Fw = wire_mesh(X, Y, d_, hw, jn, pxcm)
    assert signed_volume(Vw, Fw) > 0, "wire wound inward"
    p = os.path.join(gtmp, "wire.npz")
    np.savez(p, V=Vw, F=Fw)
    meshes.append({"name": "wire", "npz": p, "shader_py": shader, "params": {"kind": "wire"}})
    print("wire faces", round(len(Fw) / 1e6, 2), "M", flush=True)
    Vb, Fb = bubble_mesh(B, X, Y, top)
    p = os.path.join(gtmp, "bubbles.npz")
    np.savez(p, V=Vb, F=Fb)
    meshes.append({"name": "bubbles", "npz": p, "shader_py": shader, "params": {"kind": "bubble"}})
    (Pa, Ea), (Pb, Eb) = light_plane(cam["loc"])
    back_L = float(os.environ.get("S49_BACK", 1.5))
    for nm, Pl, El, vis in (("behind_a", Pa, Ea, {"diffuse": False, "glossy": False, "shadow": False, "transmission": False}), ("behind_b", Pb, Eb, {"camera": False, "diffuse": False, "glossy": False, "shadow": False})):
        p = os.path.join(gtmp, f"{nm}.npz")
        np.savez(p, P=Pl, E=El)
        meshes.append({"name": nm, "npz": p, "shader_py": shader, "params": {"kind": "behind", "L": back_L, "rgb": [0.98, 0.98, 1.0]}, "visible": vis})
    Pw, Ew = window_panel()
    p = os.path.join(gtmp, "window.npz")
    np.savez(p, P=Pw, E=Ew)
    meshes.append({"name": "window", "npz": p, "shader_py": shader, "params": {"kind": "behind", "L": float(os.environ.get("S49_WIN", 2.8)), "rgb": [1.0, 0.99, 0.97]}, "visible": {"camera": False, "diffuse": False, "shadow": False, "transmission": False}})
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": [
            # weak and soft, from the camera's side: a gradient panel, so that its reflection in the glass has no edge
            {"type": "gradient", "name": "front", "loc": [-22.0, -60.0, 34.0], "target": [0.0, 0.0, -1.0], "size": [90, 60], "sigma": [26, 16], "L": float(os.environ.get("S49_FRONT", 0.2)), "rgb": [1.0, 0.98, 0.95]},
            # far round to the sides: only the wire's rounded flanks can mirror these, the glass's normals do not tilt that far. Broken highlights along the gilt, with no effect on the glass
            {"name": "gilt_l", "loc": [-70.0, -34.0, 42.0], "target": [0.0, 0.0, -1.0], "size": [16, 16], "watts": float(os.environ.get("S49_GILT", 5000)), "rgb": [1.0, 0.97, 0.92], "hide_in_diffuse": True},
            {"name": "gilt_r", "loc": [64.0, -30.0, -34.0], "target": [0.0, 0.0, -1.0], "size": [14, 14], "watts": float(os.environ.get("S49_GILT", 5000)) * 0.6, "rgb": [1.0, 0.97, 0.92], "hide_in_diffuse": True},
        ],
        "env": {"window": 1.5, "win_az": -30.0, "win_el": 30.0, "win_w": 40.0, "win_h": 34.0, "strip": 0.5, "ceil": 0.9, "wall": 0.12},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "in_transmission": False},
        "world": [0.0, 0.0, 0.0],
        "bounces": 32,
        "diffuse_bounces": 2,
        "glossy_bounces": 8,
        "transmission_bounces": 28,
        "volume_bounces": 2,
        "spp": {"preview": 64, "mid": 128, "final": 384},
    }
    shoot(NAME, scene, q, tag=os.environ.get("S49_TAG") or ("cand" if q == "final" else f"yulin_{q}"), develop={"exposure": 0.0, "contrast": 1.2, "saturation": 1.05, "black": 0.001, "grain": 1.0, "sharpen": 0.2, "halation": 0.08, "glare": 0.006, "vignette": 0.12})


main()
