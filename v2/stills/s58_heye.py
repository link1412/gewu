"""Shot 58: a lotus leaf floating on the pond (荷叶), seen from nearly straight above. The navel sits at the foot of the frame, the ribs go up from it like rays, and the far rim is the arc over dark water.

    python3 -I v2/stills/s58_heye.py [preview|mid|final]

What changed, in order:
- A floating leaf, high saturation, blurred water, no dusk. The first answer was a low camera with soft water behind; kept as out/v2/s58_heye/lowangle_final.jpg.
- More saturated, more nearly overhead, showing the leaf's detail: this version. There is no blur left to hide in, so the leaf has to hold up at 100%.

Built like the real thing, set side by side with ref/lotus_leaf_water/06, 07 and ref/lotus_leaf_drop/03. Scales are estimates from those photographs, not measured:
- a shallow dish 30 cm across with about 23 ribs that fork twice. A rib is about a millimetre wide and only a paler green; a fork opens, or it reads as tram tracks. The navel is about a centimetre. Between the ribs, a coarse network of darker veins and a finer one;
- the blade is too big to stay flat, so it billows between the ribs and buckles along sharp creases that run in from the rim, two of them from tears;
- blotches of colour are drawn out along the ribs (polar_fbm), since a leaf grows outwards; round blotches read as paint;
- water does not wet the leaf. It rests on a film of air, so its underside is a rough water-air boundary (plastron_shader), and rays in the water that meet it past the critical angle are totally reflected. That is where the silver of the drops and of the pool comes from, even from straight above, where a smooth boundary reflects almost nothing. The roughness stands in for the papillae and is picked by eye;
- the drops and the pool are the Young-Laplace profile (contact angle 158 degrees is a figure from general knowledge, not checked). Big drops spread out of round;
- the pond is nearly black, so all you see of it is the sky it mirrors, as in the photographs. It dips where it meets the leaf edge.

Colour: the photographs measure about hue 95-116, saturation .53-.56. This is hue 93-100 and more saturated than they are, on purpose. Saturation in the darkroom has to stay low: it works in linear light and drives the blue channel to 0 at about 1.12, and a green with no blue at all reads as neon. Saturation belongs in the albedo.

Stand-ins:
- the sky is painted (lotuslib.pond_env) and picked for looks, including a bright patch of haze at the mirror direction, which is what the silver and the water show;
- water passes shadow rays and diffuse rays, because a shadow ray cannot refract and a real drop does not put full shadow under itself. So what a drop does to the light on the leaf is painted into the leaf: the caustic on the side away from the sun, the soft shade, the dark contact line. These are painted light, the one place in this shot where there is any;
- the neighbour at top left is this leaf turned and scaled, without the drops.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, _cam_axes, blur, color, fbm, mix, rank, shoot, sstep
from lotuslib import SHEET, pond_env

PLASTRON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plastron_shader.py")
from vessel import fit_arc, project, view_dir

SEED = 58
R0 = 15.0  # radius of the leaf, cm
A = 1.1  # rise of the dish from navel to rim, cm
BILLOW = 0.2
WATER = -0.03  # the level of the pond; the leaf sits on it
W, EL, DIST = 30.0, 70.0, 110.0  # The navel sits at the foot of the frame and the veins go up from it like rays; the far rim is the horizon
APERTURE = 10.0
SUN = np.array([-0.58, 0.6, 0.5])  # low from the left, so that from above every swell has a lit side
SUN = SUN / np.linalg.norm(SUN)

_rng = np.random.default_rng(SEED)
RIBS = np.sort(np.linspace(-np.pi, np.pi, 23, endpoint=False) + _rng.normal(0, 0.07, 23))
RIB_AMP = _rng.uniform(0.15, 1.0, 23)
_RIB_X = np.r_[RIBS[-1] - 2 * np.pi, RIBS, RIBS[0] + 2 * np.pi]
_RIB_I = np.arange(_RIB_X.size, dtype=float)
RUFFLE_N = np.array([4, 7, 11, 17, 27, 43])
RUFFLE_A = np.array([0.3, 0.34, 0.3, 0.2, 0.12, 0.07])
RUFFLE_P = _rng.uniform(0, 2 * np.pi, 6)
TEARS = [(1.02, 0.03, 0.9), (2.42, 0.018, 0.6)]  # angle, width (rad), depth (cm)
POOL = (1.9, 3.2, 3.0)  # x, y, mean radius of the pool. It has run off to one side of the navel, as on a leaf that is not quite level; centred on it, it read as a cut-glass wheel
# (x, y, radius of the crown's curvature), scattered as they fell, each in a pocket
BEADS = [(-5.8, 6.1, 1.0), (7.9, 8.3, 0.62), (-1.7, 10.4, 0.42), (-9.6, 3.0, 0.34), (10.3, 3.4, 0.26), (3.8, 11.3, 0.22), (-3.9, 2.9, 0.17), (-7.9, 9.2, 0.15), (6.2, 2.4, 0.13), (0.9, 8.0, 0.12), (-11.2, 7.0, 0.11), (11.1, 7.2, 0.1), (-2.6, 7.2, 0.09), (4.6, 7.0, 0.085)]
POCKET = 2.4  # how far a pocket reaches, in bead radii, at least 0.8 cm


def wrap(th):
    return np.mod(th + np.pi, 2 * np.pi) - np.pi


def R_of(th):
    r = R0 * (1 + 0.045 * np.sin(2 * th + 1.1) + 0.03 * np.sin(3 * th + 0.4) + 0.012 * np.sin(7 * th + 2.2)) + 0.07 * np.sin(27 * th + 0.8) + 0.04 * np.sin(43 * th + 2.0)
    for a, w, d in TEARS:
        r = r - d * np.exp(-np.abs(wrap(th - a)) / w)
    return r


def height(x, y):
    """The leaf's surface over the flat plan, cm. This is what is modelled; all fine detail goes on top."""
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    rho = np.minimum(r / R_of(th), 1.0)
    z = A * rho**1.75 + 0.1 * np.exp(-((r / 0.42) ** 4)) - 0.03 * np.exp(-((r / 0.11) ** 2))  # the navel: a small raised lens with a dimple
    ph = np.interp(wrap(th), _RIB_X, _RIB_I)
    z = z + BILLOW * rho**1.1 * (np.abs(np.sin(np.pi * ph)) ** 1.5 + 0.18 * sstep(0.45, 0.8, rho) * np.abs(np.sin(2 * np.pi * ph)))
    ra = np.interp(wrap(th), RIBS, RIB_AMP, period=2 * np.pi)
    z = z + 0.012 * ra * sstep(0.05, 0.22, rho) * np.sqrt(np.sin(np.pi * ph) ** 2 + 0.04)  # near the navel too, unevenly, which is part of what crumples the pool's silver
    for i in range(6):
        z = z + RUFFLE_A[i] * rho ** (2.0 + 0.3 * i) * np.sin(RUFFLE_N[i] * th + RUFFLE_P[i] + 0.6 * rho)
    # the blade is too big to stay flat: it buckles along creases that run in from the rim, each one a sharp ridge
    for a_, w_, c_, r0_ in ((1.02, 0.05, 0.5, 0.42), (2.42, 0.04, 0.34, 0.52), (2.03, 0.035, 0.36, 0.5), (0.3, 0.05, 0.3, 0.55)):
        z = z + c_ * sstep(r0_, 0.97, rho) * np.exp(-np.abs(wrap(th - a_)) / w_)
    # one part of the rim has lifted off the water and curled, and catches the sun
    z = z + 1.15 * rho**5 * np.exp(-((wrap(th - 1.66) / 0.42) ** 2)) + 0.8 * rho**6 * np.exp(-((wrap(th - 0.62) / 0.2) ** 2))
    for bx, by, br in BEADS:
        reach = max(POCKET * br, 0.8)
        z = z - 0.05 * reach * np.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * reach**2))
    # the water holds it up: the sheet does not go under, except a hair at the edge
    return WATER + 0.02 + np.logaddexp(0.0, (z - WATER - 0.02) / 0.04) * 0.04


def polar_grid(nrho, nth):
    """Rows: from the navel to the rim. Columns: all the way round, starting behind the camera, dense on the far side where the frame is."""
    t = np.linspace(-np.pi / 2, 1.5 * np.pi, 8192)
    dens = 0.7 + 0.3 * sstep(2.5, 1.9, np.abs(t - np.pi / 2))  # the whole leaf is in the frame now; thin on the near side shows as stripes
    c = np.cumsum(dens)
    c = (c - c[0]) / (c[-1] - c[0])
    th = np.interp(np.linspace(0, 1, nth), c, t).astype(np.float32)
    rho = np.linspace(0.0, 1.0, nrho, dtype=np.float32)
    Th, Rho = np.meshgrid(th, rho)
    Rr = Rho * R_of(Th).astype(np.float32)
    return Rr * np.cos(Th), Rr * np.sin(Th), Th, Rho


def veins(shape, pxcm, X0, Y0):
    """The ribs, forking on the way out; the mask of the network (0-1), in the flat plan."""
    rng = np.random.default_rng(SEED + 3)
    canvas = np.zeros(shape, np.float32)
    for a0 in RIBS:
        stack = [(np.array([np.cos(a0), np.sin(a0)]) * 0.35, float(a0), float(rng.uniform(0.05, 0.085)), 0)]
        while stack:
            p, a, hw, gen = stack.pop()
            L = float(rng.uniform(0.46, 0.66)) * R0 if gen == 0 else float(rng.uniform(0.16, 0.26)) * R0
            bend = float(rng.normal(0, 0.018))  # none of them runs dead straight
            n = int(L * 10)
            pts = [p]
            for _ in range(n):
                a = a + rng.normal(0, 0.009) + bend / 10.0
                pts.append(pts[-1] + np.array([np.cos(a), np.sin(a)]) * (L / n))
            pts = np.array(pts)
            ip = np.round(np.stack([(pts[:, 0] - X0) * pxcm, (pts[:, 1] - Y0) * pxcm], 1) * 16).astype(np.int32)
            for i in range(n):
                th = max(1, int(round(2 * hw * (1.0 - 0.72 * i / n) * pxcm)))
                cv2.line(canvas, tuple(int(q) for q in ip[i]), tuple(int(q) for q in ip[i + 1]), 1.0, th, cv2.LINE_AA, shift=4)
            if gen < 2:
                d = float(rng.uniform(0.2, 0.34))  # a real fork opens; a narrow one reads as tram tracks
                stack.append((pts[-1], a - d * float(rng.uniform(0.5, 1.2)), hw * 0.62, gen + 1))
                stack.append((pts[-1], a + d * float(rng.uniform(0.5, 1.2)), hw * 0.62, gen + 1))
    return canvas


def polar_fbm(U, V, lo, hi, beta, seed, stretch=4.0):
    """Noise drawn out along the ribs, wavelengths lo to hi cm across them and `stretch` times that along. What grows in a leaf grows out from the navel: round blotches read as a painted surface."""
    nt, nr = 2880, int(18.0 * 2880 / (2 * np.pi * R0) / stretch)
    f = fbm((nr, nt), 2880 / (2 * np.pi * R0), lo, hi, beta, seed)
    mx = ((np.arctan2(V, U) + np.pi) / (2 * np.pi) * nt).astype(np.float32)
    my = (np.hypot(U, V) / 18.0 * nr).astype(np.float32)
    return cv2.remap(f, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def net(shape, pxcm, seed, sigma, cell=0.09):
    """The reticulate veins between the ribs: walls around scattered seeds, `cell` cm^2 each."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 / cell)
    seeds = np.ones(shape, np.uint8)
    seeds[rng.integers(0, ny, n), rng.integers(0, nx, n)] = 0
    _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    wall = ((lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))).astype(np.float32)
    f = blur(wall, sigma)
    return np.clip(f / (np.percentile(f, 99.5) + 1e-6), 0, 1)


def drop_profile(b, angle=np.radians(158.0), lc=0.27):
    """The shape of a resting drop: Young-Laplace integrated from the crown (Bashforth-Adams) down to the contact angle of a lotus leaf. b: radius of curvature at the crown, lc: capillary length of water, cm."""
    ds = b / 800.0
    x, z, phi = 0.0, 0.0, 0.0
    xs, zs = [0.0], [0.0]
    for _ in range(80000):
        k = 2.0 / b + z / lc**2 - (np.sin(phi) / x if x > 1e-9 else 1.0 / b)
        phi += k * ds
        x += np.cos(phi) * ds
        z += np.sin(phi) * ds
        xs.append(x)
        zs.append(z)
        if phi >= angle:
            break
    return np.array(xs), np.array(zs)


def all_beads():
    rng = np.random.default_rng(SEED + 1)
    out = list(BEADS)
    pockets = fbm((256, 256), 256 / 32.0, 1.0, 5.0, 2.6, SEED + 9)  # dew gathers in patches
    for _ in range(4000):
        if len(out) >= len(BEADS) + 260:
            break
        x, y = rng.uniform(-14, 14), rng.uniform(-1, 14.5)
        if np.hypot(x, y) > 0.93 * float(R_of(np.arctan2(y, x))):
            continue
        if pockets[int((y + 16) * 8) % 256, int((x + 16) * 8) % 256] < 0.5:
            continue
        r = float(np.exp(rng.uniform(np.log(0.018), np.log(0.1))))
        if np.hypot(x - POOL[0], y - POOL[1]) > 1.25 * POOL[2] + r and all(np.hypot(x - b[0], y - b[1]) > b[2] + r + 0.05 for b in out):
            out.append((x, y, r))
    return out


def pool_rim(ph):
    return 1.0 + 0.13 * np.sin(2 * ph + 2.4) + 0.1 * np.sin(3 * ph + 0.3) + 0.075 * np.sin(5 * ph + 1.0) + 0.035 * np.sin(8 * ph + 4.0) + 0.008 * np.sin(17 * ph + 0.6)


def pool_mesh(dens, surf):
    """The pool: a closed skin of water. The top is level, the Young-Laplace edge of a puddle; the underside lies on the ribs of the leaf with a film of air between, so it is a crumpled mirror from inside. surf(x, y): the leaf's surface including its fine relief."""
    xs, zs = drop_profile(POOL[2] * 1.1)
    contact = float(xs[-1])
    nt = int(260 * dens) + 60
    nb = int(520 * dens) + 60
    nc = int(2600 * dens)
    Lp = np.r_[0.0, np.cumsum(np.hypot(np.diff(xs), np.diff(zs)))]
    # top: crowd the rows towards the edge, where the curvature is
    t = Lp[-1] * (1 - (1 - np.linspace(0, 1, nt)) ** 2.2)
    Xt, Zt = np.interp(t, Lp, xs).astype(np.float32), np.interp(t, Lp, zs).astype(np.float32)
    ph = np.linspace(0, 2 * np.pi, nc, dtype=np.float32)
    rim = pool_rim(ph).astype(np.float32) * POOL[2] / contact
    gap = 0.012
    cx, cy = rim * contact * np.cos(ph) + POOL[0], rim * contact * np.sin(ph) + POOL[1]
    L = surf(cx, cy) + gap
    Lm = float(L.mean())
    H = float(zs[-1])
    Xg = Xt[:, None] * rim[None, :]
    Xtop, Ytop = Xg * np.cos(ph)[None, :] + POOL[0], Xg * np.sin(ph)[None, :] + POOL[1]
    k = np.exp(-0.5 * (np.arange(-40, 41) / 14.0) ** 2)
    Ls = np.convolve(np.r_[L[-40:], L, L[:40]], k / k.sum(), "valid").astype(np.float32)[: L.size]
    Ztop = Lm + (H - Zt[:, None]) + (Ls - Lm)[None, :] * (Zt[:, None] / H) ** 4 + (L - Ls)[None, :] * (Zt[:, None] / H) ** 24
    # underside: from the contact line back to the middle
    fr = np.linspace(1.0, 0.0, nb, dtype=np.float32)[1:]
    Xb = fr[:, None] * contact * rim[None, :]
    Xbot, Ybot = Xb * np.cos(ph)[None, :] + POOL[0], Xb * np.sin(ph)[None, :] + POOL[1]
    Zbot = surf(Xbot, Ybot) + gap
    P = np.stack([np.concatenate([Xtop, Xbot]), np.concatenate([Ytop, Ybot]), np.concatenate([Ztop, Zbot])], -1).astype(np.float32)
    print(f"pool: {H:.2f} cm deep, grid {P.shape[0]} x {P.shape[1]}", flush=True)
    rg = np.zeros(P.shape[:2], np.float32)
    # the underside is rough: see plastron_shader. Unevenly: the film of air holds better in some places, and those are the silver ones
    px, py = np.round((Xbot + 8.0) * 32).astype(np.int32), np.round((Ybot + 8.0) * 32).astype(np.int32)
    patch = fbm((1024, 1024), 32.0, 0.3, 2.2, 2.6, SEED + 50)[np.clip(py, 0, 1023), np.clip(px, 0, 1023)]
    rg[Xtop.shape[0] :] = np.clip(0.42 + 0.14 * patch, 0.2, 0.62)
    return P, rg


def bead_mesh(beads, dens):
    """Each drop a closed surface of revolution; the contact patch closes it, on a thin film of air, at the height of the leaf where it touches. The pool is drawn out of round."""
    meshes = []
    for i, (u, v, r) in enumerate(beads):
        xs, zs = drop_profile(r)
        contact = float(xs[-1])
        xs, zs = np.r_[xs, np.linspace(xs[-1], 0.0, 24)[1:]], np.r_[zs, np.full(23, zs[-1])]
        L = np.r_[0.0, np.cumsum(np.hypot(np.diff(xs), np.diff(zs)))]
        res = int(np.clip(1000 * r * dens, 48, 500))
        t = np.linspace(0, L[-1], res)
        X, Z = np.interp(t, L, xs).astype(np.float32), np.interp(t, L, zs).astype(np.float32)
        ph = np.linspace(0, 2 * np.pi, res * 2, dtype=np.float32)
        Xg, Ph = np.meshgrid(X, ph, indexing="ij")
        Zg = np.broadcast_to(Z[:, None], Xg.shape)
        # a big drop has no reason to be round: it spread where it fell. A small one is held round by its own surface
        lob = float(np.clip((r - 0.12) / 0.5, 0.0, 1.0))
        rl = np.random.default_rng(SEED + 40 + i).uniform(0, 2 * np.pi, 3)
        out = 1.0 + lob * (0.2 * np.sin(2 * Ph + rl[0]) + 0.08 * np.sin(3 * Ph + rl[1]) + 0.025 * np.sin(5 * Ph + rl[2]))
        ring = np.linspace(0, 2 * np.pi, 32)
        base = float(np.max(height(u + contact * np.cos(ring), v + contact * np.sin(ring)))) + 0.006
        P = np.stack([u + Xg * out * np.cos(Ph), v + Xg * out * np.sin(Ph), base + float(zs[-1]) - Zg], -1).astype(np.float32)
        rg = np.where(t > L[-1] - contact * 1.001, 0.5, 0.0)  # the underside is rough: see plastron_shader
        meshes.append((P, np.broadcast_to(rg[:, None], Xg.shape).astype(np.float32)))
    return meshes


def build(dens, beads):
    """The leaf: positions in a polar grid, everything painted in the flat plan and read into it."""
    pxcm = 88.0 * dens
    X0, X1, Y0, Y1 = -17.0, 17.0, -9.0, 17.0
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    u = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)
    rr = np.hypot(U, V)
    rho_f = rr / R_of(np.arctan2(V, U))
    print(f"plan {nx} x {ny}", flush=True)

    vein = veins(shape, pxcm, X0, Y0)
    vs = blur(vein, max(0.012 * pxcm, 0.6))  # soft-sided: a band of paler tissue, not a line
    fine = net(shape, pxcm, SEED + 8, max(0.8 * dens, 0.6))
    netb = net(shape, pxcm, SEED + 18, max(0.03 * pxcm, 0.6), cell=0.55)  # the coarse network that shows at arm's length
    pap = fbm(shape, pxcm, 0.012, 0.05, 0.9, SEED + 3)
    cells = fbm(shape, pxcm, 0.06, 0.3, 1.4, SEED + 4)
    quilt = polar_fbm(U, V, 0.5, 2.4, 3.0, SEED + 5, stretch=3.0)
    big = polar_fbm(U, V, 1.2, 8.0, 2.8, SEED + 6)
    between = blur(vein, 0.22 * pxcm)
    # the veins are sunk a little and the tissue pillows up between them
    wr = polar_fbm(U, V, 0.45, 2.2, 2.8, SEED + 14, stretch=1.5)  # creases along the ribs, which the silver under the pool breaks up on
    near_pool = np.exp(-((np.hypot(U - POOL[0], V - POOL[1]) / (1.25 * POOL[2])) ** 4))
    h = 0.02 * quilt + 0.022 * (1 - sstep(0, 0.5, between)) - 0.012 * vs - 0.005 * netb + 0.0016 * fine + 0.0012 * cells + 0.0012 * pap + (0.002 + 0.016 * near_pool) * wr

    h = h * sstep(0.25, 0.7, rr)  # the navel is smooth
    # the blade: a deep blue-green with long soft mottling, paling at the navel, yellowing at the rim, where it has begun to die
    fade = 1.0 - 0.45 * sstep(0.2, 1.0, rho_f)
    col = mix(color([0.055, 0.25, 0.02]), color([0.125, 0.42, 0.03]), 0.25 + 0.5 * rank(0.9 * big + 0.3 * quilt))
    col = mix(col, color([0.2, 0.5, 0.07]), (0.6 * vs * fade**1.2)[..., None])  # paler green, not yellow; the rib is the same tissue with less in it
    col = col * (1.0 - 0.1 * netb - 0.04 * fine)[..., None] * (1.0 + 0.045 * pap[..., None]) * (1.0 + 0.035 * cells[..., None])  # the velvet: a fine grain of tiny papillae, seen at this scale
    rf = np.random.default_rng(SEED + 19)  # the pale pin-pricks all over a real one
    fleck = np.zeros(shape, np.float32)
    fleck[rf.integers(0, ny, int(nx * ny / pxcm**2 * 0.9)), rf.integers(0, nx, int(nx * ny / pxcm**2 * 0.9))] = 1.0
    fleck = blur(fleck, max(0.012 * pxcm, 0.6))
    col = mix(col, color([0.3, 0.55, 0.15]), np.clip(0.55 * fleck / (fleck.max() + 1e-6), 0, 1)[..., None])
    # the navel is small, about a centimetre, and crisp: a pale lens at the root of the ribs
    th_f = np.arctan2(V, U)
    nav_r = 0.46 * (1 + 0.14 * np.sin(2 * th_f + 0.6) + 0.06 * np.sin(3 * th_f + 1.9))
    col = mix(col, color([0.2, 0.46, 0.07]), (0.5 * np.exp(-((rr / 1.5) ** 2)))[..., None])
    nav = sstep(nav_r * 1.16, nav_r * 0.72, rr)
    col = mix(col, color([0.62, 0.64, 0.2]), nav[..., None])
    col = mix(col, color([0.3, 0.36, 0.08]), (0.7 * np.exp(-((rr / 0.09) ** 2)))[..., None])
    col = mix(col, color([0.17, 0.3, 0.03]), (0.34 * sstep(0.86, 1.0, rho_f + 0.03 * big))[..., None])
    col = mix(col, color([0.17, 0.065, 0.025]), ((0.3 + 0.45 * rank(big)) * sstep(0.988, 0.998, rho_f + 0.004 * quilt))[..., None])  # the thin brown line round the very edge, on and off
    dead = np.zeros(shape, np.float32)
    for a, w_, d in TEARS:
        dead = np.maximum(dead, np.exp(-np.abs(wrap(np.arctan2(V, U) - a)) * 15.0 / (0.6 + 40.0 * w_)) * sstep(0.72, 0.93, rho_f + 0.08 * quilt))
    col = mix(col, color([0.15, 0.085, 0.03]), (0.4 * dead)[..., None])
    # a few marks of a summer outdoors: pin-pricks of brown with a pale ring, and specks of dust
    rs = np.random.default_rng(SEED + 12)
    spot = np.zeros(shape, np.float32)
    ring = np.zeros(shape, np.float32)
    clumps = rs.uniform(0, 1, (5, 2)) * [nx, ny]
    for _ in range(70):
        cx_, cy_ = clumps[rs.integers(0, 5)]  # dirt comes in clumps
        sx, sy = int(cx_ + rs.normal(0, 0.9 * pxcm)), int(cy_ + rs.normal(0, 0.9 * pxcm))
        r0 = float(np.exp(rs.uniform(np.log(0.01), np.log(0.04)))) * pxcm
        cv2.circle(spot, (sx, sy), max(int(r0), 1), 1.0, -1, cv2.LINE_AA)
        cv2.circle(ring, (sx, sy), max(int(2.6 * r0), 1), 1.0, -1, cv2.LINE_AA)
    col = mix(col, color([0.25, 0.32, 0.08]), (0.3 * blur(ring, max(0.02 * pxcm, 0.6)))[..., None])
    col = mix(col, color([0.05, 0.03, 0.015]), (0.85 * blur(spot, 0.6))[..., None])

    # what comes through the sheet
    tr = mix(color([0.2, 0.5, 0.015]), color([0.36, 0.68, 0.025]), rank(big + 0.4 * quilt)[..., None])
    tr = tr * ((1.0 - 0.45 * vs) * (1.0 - 0.2 * fine) * (1.0 - 0.8 * dead) * (1 - 0.8 * blur(spot, 0.6)))[..., None]
    col_clean = col.copy()
    # Stand-ins, painted. Water passes the sun here (a shadow ray cannot refract), so what a drop does to the light on the leaf has to be put back: the sun gathered on the side away from it, a path tracer finds that caustic too rarely; a soft shade beyond that; a tight dark line where the water meets the leaf
    away = -SUN[:2] / np.linalg.norm(SUN[:2])
    under = np.zeros(shape, np.float32)
    shade = np.zeros(shape, np.float32)
    for bu, bv, br in beads:
        contact = float(drop_profile(br)[0][-1]) * (1.0 + 0.25 * float(np.clip((br - 0.12) / 0.5, 0.0, 1.0)))
        pad = contact * 1.9
        i0, i1 = max(int((bv - Y0 - pad) * pxcm) - 2, 0), min(int((bv - Y0 + pad) * pxcm) + 3, ny)
        j0, j1 = max(int((bu - X0 - pad) * pxcm) - 2, 0), min(int((bu - X0 + pad) * pxcm) + 3, nx)
        if i1 <= i0 or j1 <= j0:
            continue
        uu, vv = U[i0:i1, j0:j1] - bu, V[i0:i1, j0:j1] - bv
        d = np.hypot(uu, vv)
        d_off = np.hypot(uu - away[0] * 0.42 * contact, vv - away[1] * 0.42 * contact)
        under[i0:i1, j0:j1] = np.maximum(under[i0:i1, j0:j1], sstep(contact * 0.62, contact * 0.1, d_off) * sstep(contact, contact * 0.8, d))
        d_sh = np.hypot(uu - away[0] * 0.55 * contact, vv - away[1] * 0.55 * contact)
        line = np.exp(-(((d - contact) / max(0.11 * contact, 0.012)) ** 2))
        shade[i0:i1, j0:j1] = np.maximum(shade[i0:i1, j0:j1], np.maximum(0.3 * sstep(contact * 1.25, contact * 0.6, d_sh) * sstep(contact * 0.85, contact * 1.02, d), 0.5 * line))
    col = col * (1.0 - shade)[..., None]
    col = mix(col, color([0.34, 0.68, 0.1]), (0.7 * under)[..., None])

    def surf(x, y):
        mxs, mys = np.atleast_2d((x - X0) * pxcm - 0.5).astype(np.float32), np.atleast_2d((y - Y0) * pxcm - 0.5).astype(np.float32)
        return height(x, y) + cv2.remap(h.astype(np.float32), mxs, mys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).reshape(np.shape(x))

    nrho, nth = int(R0 * pxcm), int(2 * np.pi * R0 * pxcm * 0.85)
    print(f"leaf grid {nrho} x {nth} = {nrho * nth / 1e6:.1f} M", flush=True)
    gx, gy, _, Rho = polar_grid(nrho, nth)
    mx, my = (gx - X0) * pxcm - 0.5, (gy - Y0) * pxcm - 0.5
    rd = lambda f: cv2.remap(f.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    P = np.stack([gx, gy, (height(gx, gy) + rd(h)).astype(np.float32)], -1).astype(np.float32)
    C = np.clip(rd(col), 0, 1)
    return P, C.astype(np.float32), np.clip(rd(col_clean), 0, 1).astype(np.float32), np.clip(rd(tr), 0, 1).astype(np.float32), surf


def pond(path, dens):
    """The water behind and below the leaf: nearly black, so all you see of it is what it reflects, in small ripples."""
    pxcm = 40.0 * dens
    X0, X1, Y0, Y1 = -27.0, 27.0, -12.0, 34.0  # no further than the frame
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    x = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    y = Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)
    # ripples drawn out across the view, as a breath of wind leaves them
    # only slow swells: nothing in this water is small enough to show where the focus falls, so it reads as soft colour right up to the leaf
    swell = cv2.resize(fbm((ny // 4, nx), pxcm, 8.0, 60.0, 3.2, SEED + 30).astype(np.float32), (nx, ny), interpolation=cv2.INTER_CUBIC)
    # the leaf does not wet, so the water dips where it meets the edge: a thin curve that takes the sky, the bright line round a real one. Only where the edge is down on the water
    th = np.arctan2(Y, X)
    rim_z = height(R_of(th) * np.cos(th), R_of(th) * np.sin(th))
    d = np.maximum(np.hypot(X, Y) - R_of(th), 0.0)
    Z = WATER - 0.02 + 0.012 * swell - 0.05 * np.exp(-d / 0.16) * np.exp(-np.maximum(rim_z - WATER - 0.02, 0.0) / 0.08)
    Z = Z - 0.4 * sstep(-0.1, -0.6, np.hypot(X, Y) - R_of(th))  # under the leaf it goes out of the way: near the navel the sheet is at the level of the pond, and the swell came up through its valleys as black slits
    np.savez(path, P=np.stack([X, Y, Z.astype(np.float32)], -1).astype(np.float32))
    return path


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s58_heye")
    os.makedirs(d, exist_ok=True)
    th = np.linspace(0.1, np.pi - 0.1, 2400)
    rim = np.stack([R_of(th) * np.cos(th), R_of(th) * np.sin(th)], -1)
    rim3 = np.stack([rim[:, 0], rim[:, 1], height(rim[:, 0], rim[:, 1])], -1)
    focus = np.array([-1.0, 6.0, float(height(np.array(-1.0), np.array(6.0))) + 0.2])  # the middle of the blade; rim and navel fall just soft
    cam, sag = fit_arc(rim3, view_dir(-90.0, EL), W, DIST, apex=(0.5, 0.1), target0=(0.0, 7.5, 0.5), aperture_mm=APERTURE, focus_point=focus)
    x, y, _ = project(cam, np.array([[0.0, 0.0, 0.0], [BEADS[0][0], BEADS[0][1], 0.5]]))
    print(f"navel at ({x[0]:.2f}, {y[0]:.2f}), first bead at ({x[1]:.2f}, {y[1]:.2f}), sag {sag:.3f}", flush=True)

    beads = all_beads()
    P, C, C0, T, surf = build(dens, beads)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, tr=T)
    meshes = [{"name": "leaf", "npz": npz, "shader_py": SHEET, "params": {"k": 0.24, "rough": 0.58, "spec": 0.11, "sheen": 0.0, "sheen_rough": 0.45}}]
    # Water passes the sun and the sky down to the leaf: a shadow ray cannot refract, so a drop would otherwise lay full shadow under itself. Diffuse rays pass it too, or the sky would be counted twice, once by the shadow ray and once by the bounce
    thru = {"shadow": False, "diffuse": False}
    pp = os.path.join(d, f"pool.{q}.npz")
    Pp, rgp = pool_mesh(dens, surf)
    np.savez(pp, P=Pp, rg=rgp)
    meshes.append({"name": "pool", "npz": pp, "shader_py": PLASTRON, "params": {}, "visible": thru})
    for i, (Pb, rgb_) in enumerate(bead_mesh(beads, dens)):
        bp = os.path.join(d, f"b{i}.{q}.npz")
        np.savez(bp, P=Pb, rg=rgb_)
        meshes.append({"name": f"b{i}", "npz": bp, "shader_py": PLASTRON, "params": {}, "visible": thru})

    # its neighbours, in the frame: this leaf's shape and paint, turned and coarser, so they have real veins in their blur. Placed from where they fall on screen. Straight behind the apex stays clear
    right, up, back = _cam_axes(cam)
    loc = np.array(cam["loc"], float)
    k = 36.0 / cam["lens_mm"]
    for n, (sx, sy, sc, ang) in enumerate(((-0.17, -0.33, 0.95, 2.1),)):
        ray = -back + right * (sx - 0.5) * k + up * (0.5 - sy) * k * 9 / 16
        at = loc + ray * (WATER - loc[2]) / ray[2]
        step = 2
        ca, sa = np.cos(ang), np.sin(ang)
        Q = P[::step, ::step] * sc
        far = os.path.join(d, f"near{n}.{q}.npz")
        np.savez(far, P=np.stack([ca * Q[..., 0] - sa * Q[..., 1] + at[0], sa * Q[..., 0] + ca * Q[..., 1] + at[1], Q[..., 2]], -1).astype(np.float32), col=C0[::step, ::step], tr=T[::step, ::step])
        meshes.append({"name": f"near{n}", "npz": far, "shader_py": SHEET, "params": {"k": 0.24, "rough": 0.58, "spec": 0.11, "sheen": 0.0, "sheen_rough": 0.45}})
    meshes.append({"name": "pond", "npz": pond(os.path.join(d, f"pond.{q}.npz"), dens), "material": {"Base Color": [0.0015, 0.004, 0.0035], "Roughness": 0.03, "IOR": 1.33, "Specular IOR Level": 0.5}})
    tgt = np.array(cam["target"], float)
    lights = [{"name": "sun", "loc": (tgt + SUN * 500.0).tolist(), "target": tgt.tolist(), "size": [60, 60], "watts": 1500000, "rgb": [1.0, 0.95, 0.84], "hide_in_gloss": True, "hide_in_transmission": True}]
    envp = pond_env(os.path.join(d, "sky_env.npy"), SUN, top=(1.3, 1.36, 1.45), tree_el=22.0, gain=0.6, seed=SEED, soft=4.0, gaps=0.08, disc=(3.0, 60.0))
    sky = np.load(envp)
    hh, ww = sky.shape[:2]
    lon, lat = np.meshgrid((np.arange(ww) + 0.5) / ww * 2 * np.pi - np.pi, np.pi / 2 - (np.arange(hh) + 0.5) / hh * np.pi)
    dv = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    glow = np.array([-0.16, 0.26, 0.95])
    ang = np.degrees(np.arccos(np.clip(dv @ (glow / np.linalg.norm(glow)), -1, 1)))
    np.save(envp, (sky + (1.5 * np.exp(-((ang / 11.0) ** 2)))[..., None] * color([1.0, 0.98, 0.94])).astype(np.float32))
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": envp, "diffuse": True, "transmission": True},
        "bounces": 40,  # light rattles inside a drop by total internal reflection; at the default limit it runs out and comes back black, a ring like an eye in each
        "diffuse_bounces": 4,
        "glossy_bounces": 32,
        "transmission_bounces": 32,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }
    shoot("s58_heye", scene, q, develop={"exposure": 0.0, "contrast": 1.18, "saturation": 1.03, "black": 0.001, "grain": 0.9, "sharpen": 0.2, "halation": 0.05, "glare": 0.006, "vignette": 0.34})


main()
