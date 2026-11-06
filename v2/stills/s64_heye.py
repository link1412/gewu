"""Shot 64: one lotus leaf floating on pond water in the midday sun, seen from nearly straight above (荷叶). The navel at the foot of the frame, the ribs going up from it, and the margin as a great half circle. A single still: no move.

    python3 -I v2/stills/s64_heye.py [plan OUT.png|preview|mid|final] [--tag=cand]
    plan is a hillshade of the leaf in a moment, with no render. S64_DROPS=0 leaves the drops off.

A still, from above, about a half circle so the leaf's shape reads, on water, in daylight. Earlier versions are kept as out/v2/s64_heye/s64_heye_v1.py.txt (35 degrees), s64_heye_v2_low.py.txt (macro) and s64_heye_v3_dark.py.txt (overhead, on near-black water).

Looked at, not measured unless said so: ref/lotus_leaf_water/02 (a leaf in sun on turbid water: the water has its own colour, the rim's shadow is sharp), 06 and 07 (a floating leaf from above), ref/lotus_leaf_drop/09 and 10 (ribs, navel).

Computed or known, not painted:
- the sun is a real light, 0.53 degrees wide (known); its shadows on leaf and water and its glints on the ripple are all traced. The glints come only from facets tilted about 10 degrees, worked out from the sun and camera directions, so flat water has no white patch;
- water: Fresnel at IOR 1.33, about 2% at normal incidence (known), on a rippled surface that is geometry, with the sky mirrored in it. The meniscus decays over water's capillary length, 0.27 cm (known);
- the turbid body below the surface is shaded with a level normal (s64_water_shader.py), because ripple on top does not shade what is under it;
- a clear drop is glass of IOR 1.33 on a Young-Laplace profile; the light it throws on the leaf is traced with photons and blurred.

Estimates and stand-ins:
- the sky is painted (lotuslib.pond_env), its clouds and its colours by eye. Sun against sky comes to 2.4:1 on a level surface (computed from this sky map): a bright day with cloud, softer than a clear one, which from memory runs about 4-6:1;
- the leaf's size (40 cm across), every height and relief amplitude, the ripple's rms slope and spectrum, the meniscus height, the water's reflectance (2-4%, in the range from memory for turbid water) and all the leaf's albedos are picked by eye. The leaf's green is brighter than a measured leaf's (about 10-20% at 550 nm, from memory), as an exposure for the leaf would make it look;
- the pale lip along the margin stands in for a thickness the sheet does not have: painted, 0.04 cm wide;
- the leaf is one sheet, and its underside has the colour of its top;
- a drop casts no real shadow: the shadow ray passes it, and the photon map takes its place;
- shadows lie on the water surface, so they are sharper than in a turbid body and ripple does not bend them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.ndimage import map_coordinates

from kit import OUT, _cam_axes, blur, color, fbm, frame_camera, mix, shoot, sstep
from lotuslib import SHEET, pond_env
from vessel import project, view_dir

PLASTRON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plastron_shader.py")
WATER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s64_water_shader.py")
NAME = "s64_heye"
SEED = 164
R0 = 20.0  # radius of the leaf, cm. An estimate
W = 44.5  # width of the frame at the leaf, cm
EL, AZ, ROLL_ = 80.0, 84.0, 178.0  # some degrees off the vertical, from the side of the rim at the top of the frame: so the lifted margin and its mirror image draw apart and the dark band of the mirror shows outside the leaf, as in ref/lotus_leaf_water/06. The camera is simply held the other way up
DIST = 230.0
APERTURE = 8.0  # about f/8 on a 60 mm lens
NAVEL_SCREEN = (0.5, 0.985)
SUN_EL, SUN_AZ = 62.0, 235.0  # elevation, and azimuth from +x (frame right) towards +y (frame up): high, at the lower left of the frame, the camera leaning the other way. So what lifts on the far side throws its shadow out onto the water, and a water facet has to tilt only about 10 degrees (slope 0.18) to throw the sun into the lens: ripple glints, and flat water has no white patch. Computed from the two directions
KEY = np.array([np.cos(np.radians(SUN_EL)) * np.cos(np.radians(SUN_AZ)), np.cos(np.radians(SUN_EL)) * np.sin(np.radians(SUN_AZ)), np.sin(np.radians(SUN_EL))])
SKY = KEY
SKY_SHARE = 0.8  # the sun's share of the light on the leaf, for what a drop does to it. An estimate: this sky computes to 70%, the render uses 80
SUN_STRENGTH = 5.0  # irradiance facing the sun, in the same units as the sky's radiance
WATER_Z = 0.0
RIP_CALM, RIP_PAW = 0.015, 0.085  # rms slope of the ripple, still water and under a cat's paw. Estimates; the paws carry the glints
MENISCUS = 0.08  # cm, where the margin rests on the water. An estimate
WATER_A, WATER_B = (0.011, 0.017, 0.007), (0.018, 0.022, 0.008)  # pond water, linear. Estimates
PX = 110.0  # maps, px/cm at final
X0, X1, Y0, Y1 = -R0 * 1.25, R0 * 1.25, -R0 * 1.25, R0 * 1.25
# Drops in the dish, where water collects: x, y, crown radius, cm. Placed by eye
BEADS = [(-3.2, 3.4, 1.05), (4.2, 6.2, 0.55), (-7.4, 9.0, 0.3), (1.8, 11.2, 0.2), (8.6, 4.0, 0.42), (6.6, 10.4, 0.13)]

_rng = np.random.default_rng(SEED)
RIBS = np.sort(np.linspace(-np.pi, np.pi, 23, endpoint=False) + _rng.normal(0, 0.05, 23))
RIB_W = _rng.uniform(0.62, 1.0, 23)
RUST = _rng.uniform(0.0, 1.0, 23) ** 2
_RIB_X = np.r_[RIBS[-1] - 2 * np.pi, RIBS, RIBS[0] + 2 * np.pi]
_RIB_I = np.arange(_RIB_X.size, dtype=float)
_ph = _rng.uniform(0, 2 * np.pi, 20)
# a few tears: angle, depth cm, width in degrees
NICKS = ((62.0, 0.5, 0.9), (118.0, 0.2, 0.5), (151.0, 0.6, 1.0), (27.0, 0.15, 0.4))
_low = fbm((256, 256), 256 / 60.0, 7.0, 30.0, 3.0, SEED + 2).astype(np.float32)


def wrap(th):
    return np.mod(th + np.pi, 2 * np.pi) - np.pi


def rim_wave(th):
    """How far the margin is lifted off the water at this angle, cm. Scallops of several sizes, whose crests are rounded and whose troughs are tighter."""
    w = 0.42 * np.sin(3 * th + _ph[0]) + 0.5 * np.sin(5 * th + _ph[1]) + 0.46 * np.sin(8 * th + _ph[2]) + 0.25 * np.sin(13 * th + _ph[3]) + 0.09 * np.sin(21 * th + _ph[4])
    return 0.85 + 1.0 * np.tanh(w * 0.75)  # a floating leaf: much of the margin is on the water, some lifts a centimetre or two


def outline_smooth(th):
    """The margin's radius before any tears, cm: where it is lifted it comes in, as seen from above."""
    r = R0 * (1 + 0.012 * np.sin(2 * th + _ph[5]) + 0.012 * np.sin(4 * th + _ph[6]) + 0.02 * np.sin(7 * th + _ph[7]) + 0.014 * np.sin(11 * th + _ph[8]) + 0.004 * np.sin(19 * th + _ph[9]) + 0.0018 * np.sin(41 * th + _ph[10]) + 0.0008 * np.sin(83 * th + _ph[11]))
    return r - 0.35 * rim_wave(th)


def outline(th):
    """The margin's radius, cm. A tear only cuts the edge: fed into the surface's own radius it ran a crease to the navel."""
    r = outline_smooth(th)
    for a, dp, wd in NICKS:
        d = wrap(th - np.radians(a)) / np.radians(wd)
        r = r - dp * np.exp(-(np.abs(d) ** 1.3))
    return r


def height(x, y):
    """The leaf's surface over the plan, cm above the water, before fine relief."""
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    rho = np.minimum(r / outline_smooth(th), 1.3)
    ph = np.interp(wrap(th), _RIB_X, _RIB_I)
    dish = 0.12 + 0.55 * rho**2.0  # the middle of a floating leaf sits on the water
    # the waves belong to the outer part of the blade: run in further they turned the leaf into a folded fan
    wave = (rim_wave(th + 0.05 * np.sin(4 * rho + th)) - 0.75) * sstep(0.3, 1.03, rho) ** 2.0  # one rise out to the margin: a separate drop towards it folded the crest over
    pleat = 0.2 * rho**1.8 * np.sqrt(np.sin(np.pi * ph) ** 2 + 0.05)
    mx = np.clip((x + 30.0) / 60.0 * 255.0, 0, 255)
    my = np.clip((y + 30.0) / 60.0 * 255.0, 0, 255)
    low = map_coordinates(_low, [np.ravel(my), np.ravel(mx)], order=3, mode="nearest").reshape(np.shape(mx))
    z = dish + wave + pleat + 0.42 * rho * low - 0.3 * np.exp(-((r / 1.5) ** 2))
    return 0.09 + 0.5 * (z - 0.09 + np.sqrt((z - 0.09) ** 2 + 0.01))  # never through the water


def polar_fbm(U, V, lo, hi, beta, seed, stretch=2.0, R=8.0):
    """Noise drawn out along the ribs, wavelengths lo to hi cm across them at R from the navel, `stretch` times that along."""
    nt = 4096
    px = nt / (2 * np.pi * R)
    span = R0 * 1.4
    nr = int(px * span / stretch)
    f = fbm((nr, nt), px, lo, hi, beta, seed)
    mx = ((np.arctan2(V, U) + np.pi) / (2 * np.pi) * nt).astype(np.float32)
    my = (np.hypot(U, V) / span * nr).astype(np.float32)
    return cv2.remap(f, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def veins(shape, pxcm):
    """Ribs, and the side veins that leave them. Returns two masks, 0-1, in the plan."""
    rng = np.random.default_rng(SEED + 3)
    rib = np.zeros(shape, np.float32)
    sec = np.zeros(shape, np.float32)

    def to_px(p):
        return np.round(np.stack([(p[:, 0] - X0) * pxcm, (p[:, 1] - Y0) * pxcm], 1) * 16).astype(np.int32)

    def stroke(canvas, pts, w0, w1):
        ip = to_px(pts)
        n = len(pts) - 1
        for i in range(n):
            th = max(1, int(round((w0 + (w1 - w0) * i / n) * pxcm)))
            cv2.line(canvas, tuple(int(q) for q in ip[i]), tuple(int(q) for q in ip[i + 1]), 1.0, th, cv2.LINE_AA, shift=4)

    def side(p, a, length, w, depth):
        n = max(int(length * 6), 5)
        pts = [p]
        ang = a
        for _ in range(n):
            ang += rng.normal(0, 0.09)
            pts.append(pts[-1] + np.array([np.cos(ang), np.sin(ang)]) * (length / n))
        pts = np.array(pts)
        stroke(sec, pts, w, w * 0.45)
        if depth > 0:
            for k in rng.integers(1, n, 2):
                side(pts[k], ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.2), length * rng.uniform(0.35, 0.65), w * 0.65, depth - 1)

    for a0, wk in zip(RIBS, RIB_W):
        stack = [(np.array([np.cos(a0), np.sin(a0)]) * 0.5, float(a0), 0.19 * float(wk), 0)]
        while stack:
            p, a, w, gen = stack.pop()
            L = float(rng.uniform(0.42, 0.68)) * R0 if gen == 0 else float(rng.uniform(0.14, 0.3)) * R0
            bend = float(rng.normal(0, 0.008))
            n = int(L * 5)
            pts = [p]
            for _ in range(n):
                a = a + rng.normal(0, 0.009) + bend
                pts.append(pts[-1] + np.array([np.cos(a), np.sin(a)]) * (L / n))
            pts = np.array(pts)
            stroke(rib, pts, w, w * 0.55)
            dirs = np.diff(pts, axis=0)
            s = 1.5 + rng.exponential(1.0)
            while s < L - 0.1:
                i = min(int(s / L * n), n - 1)
                q = pts[i]
                d = float(np.arctan2(dirs[i, 1], dirs[i, 0]))
                side(q, d + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1), rng.uniform(1.0, 4.0), rng.uniform(0.04, 0.075), 2)
                s += rng.exponential(1.1) + 0.5
            if gen < 2:
                dv = float(rng.uniform(0.14, 0.3))
                stack.append((pts[-1], a - dv * rng.uniform(0.6, 1.3), w * 0.62, gen + 1))
                stack.append((pts[-1], a + dv * rng.uniform(0.6, 1.3), w * 0.62, gen + 1))
    return rib, sec


def net(shape, pxcm, seed, sigma, cell):
    """The finest network: walls around scattered seeds, `cell` cm^2 each."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 / cell)
    seeds = np.ones(shape, np.uint8)
    seeds[rng.integers(0, ny, n), rng.integers(0, nx, n)] = 0
    _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    wall = ((lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))).astype(np.float32)
    f = blur(wall, sigma)
    return np.clip(f / (np.percentile(f, 99.5) + 1e-6), 0, 1)


def drop_profile(b, angle=np.radians(140.0), lc=0.27):
    """The shape of a resting drop: Young-Laplace integrated from the crown (Bashforth-Adams) to the contact angle. b: radius of curvature at the crown, lc: capillary length of water, cm."""
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


def bead_rim(i, r):
    lob = float(np.clip((r - 0.2) / 0.5, 0.0, 1.0))
    rl = np.random.default_rng(SEED + 40 + i).uniform(0, 2 * np.pi, 3)
    return lambda ph: 1.0 + lob * (0.06 * np.sin(2 * ph + rl[0]) + 0.03 * np.sin(3 * ph + rl[1]))


def photons(xs, zs, rimf, n, seed, res, light, blur_cm):
    """Trace the sun forward through a drop. xs, zs: its profile from the crown; rimf(ph): how far its outline is drawn out at angle ph. Returns E, the light landing on the plane of the contact relative to the open sun (1 = unaffected), and the half-size of the map, cm."""
    rng = np.random.default_rng(seed)
    H = float(zs[-1])
    h_prof = (H - zs)[::-1]
    x_prof = xs[::-1]
    table_h = np.linspace(0.0, H, 2048)
    table_r = np.interp(table_h, h_prof, x_prof)
    table_d = np.gradient(table_r, table_h)
    rmax = float(np.max(xs)) * float(np.max(rimf(np.linspace(0, 2 * np.pi, 256))))
    drift = light[:2] / light[2]  # horizontal travel of a ray, per unit fallen, towards the light
    half = rmax * 1.2 + H * float(np.linalg.norm(drift)) * 1.3 + 0.02
    # uniform on the horizontal plane at the top of the drop: then the open sun lands uniformly at the bottom
    # stratified: uniform random points left a grain on the whole square, which read as felt and showed the square itself
    ns = int(np.sqrt(n))
    n = ns * ns
    gx_, gy_ = np.meshgrid((np.arange(ns) + 0.5) / ns, (np.arange(ns) + 0.5) / ns)
    ox = (gx_.ravel() + rng.uniform(-0.5, 0.5, n) / ns) * 2 * half - half
    oy = (gy_.ravel() + rng.uniform(-0.5, 0.5, n) / ns) * 2 * half - half
    o = np.stack([ox + drift[0] * H, oy + drift[1] * H, np.full(n, H + 1e-4)], 1)
    d = -light
    w = np.ones(n)
    land = o[:, :2] - drift * o[:, 2][:, None]  # where they land if nothing is in the way
    land0 = land.copy()

    def rad(p):
        ph = np.arctan2(p[:, 1], p[:, 0])
        rho = rimf(ph)
        return np.hypot(p[:, 0], p[:, 1]) / rho, np.interp(np.clip(p[:, 2], 0, H), table_h, table_r), ph, rho

    def normal(p):
        _, _, ph, rho = rad(p)
        r = np.maximum(np.hypot(p[:, 0], p[:, 1]), 1e-6)
        rhat = p[:, :2] / r[:, None]
        that = np.stack([-rhat[:, 1], rhat[:, 0]], 1)
        e = 1e-3
        drho = (rimf(ph + e) - rimf(ph - e)) / (2 * e)
        dR = np.interp(np.clip(p[:, 2], 0, H), table_h, table_d)
        N = np.column_stack([rhat / rho[:, None] - that * (drho / rho**2)[:, None], -np.clip(dR, -200, 200)])
        return N / np.linalg.norm(N, axis=1, keepdims=True)

    # which rays meet the drop at all
    K = 56
    near = np.flatnonzero(np.hypot(*(o[:, :2] - drift * 0.5 * H).T) < rmax + H)
    idx = near
    t_hit = np.full(n, -1.0)
    dt = H / (-d[2]) / K
    live = idx
    for k in range(1, K + 1):
        if live.size == 0:
            break
        p = o[live] + d * (k * dt)
        rn, Rp, _, _ = rad(p)
        hit = (rn < Rp) & (p[:, 2] > 0)
        t_hit[live[hit]] = k * dt
        live = live[~hit]
    idx = np.flatnonzero(t_hit > 0)
    if idx.size:
        a, b = t_hit[idx] - dt, t_hit[idx]
        for _ in range(6):
            m = 0.5 * (a + b)
            rn, Rp, _, _ = rad(o[idx] + d * m[:, None])
            ins = rn < Rp
            b = np.where(ins, m, b)
            a = np.where(ins, a, m)
        p = o[idx] + d * b[:, None]
        N = normal(p)
        c1 = np.clip(-(N @ d), 0, 1)
        w[idx] = np.maximum(1.0 - (0.02 + 0.98 * (1 - c1) ** 5), 0.6)  # what reflects off the rim lands nearby, not nowhere: at 0 it drew a thin dark ring round each shadow
        eta = 1 / 1.33
        t = eta * d + (eta * c1 - np.sqrt(np.maximum(1 - eta**2 * (1 - c1**2), 0)))[:, None] * N
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        # inside: go down to the plane unless the wall comes first
        K2 = 40
        q = p.copy()
        s = (p[:, 2] / np.maximum(-t[:, 2], 1e-3)) / K2
        out_at = np.full(idx.size, -1, np.int32)
        for k in range(1, K2 + 1):
            pk = p + t * (s * k)[:, None]
            rn, Rp, _, _ = rad(pk)
            ex = (rn > Rp + 1e-4) & (out_at < 0)
            out_at[ex] = k
        inside = out_at < 0
        q[inside] = p[inside] + t[inside] * (p[inside, 2] / np.maximum(-t[inside, 2], 1e-3))[:, None]
        land[idx[inside]] = q[inside, :2]
        w[idx[inside]] *= 0.8  # through the film of air
        ii = np.flatnonzero(~inside)
        if ii.size:
            pe = p[ii] + t[ii] * (s[ii] * out_at[ii])[:, None]
            Ne = normal(pe)
            ci = np.clip(np.sum(t[ii] * Ne, axis=1), 0, 1)
            k_ = 1 - 1.33**2 * (1 - ci**2)
            ok = (k_ > 0) & (t[ii, 2] < 0)
            to = 1.33 * t[ii] + (np.sqrt(np.maximum(k_, 0)) - 1.33 * ci)[:, None] * Ne
            land_ok = pe[:, :2] + to[:, :2] * (pe[:, 2] / np.maximum(-to[:, 2], 1e-3))[:, None]
            # ii counts within idx: this indexed the rays of the whole square until now, so the rays that leave through the side wall landed wrongly
            bad = idx[ii[~ok | (to[:, 2] >= 0)]]
            good = (ok) & (to[:, 2] < 0)
            land[idx[ii[good]]] = land_ok[good]
            w[bad] = 0.5  # as at the rim
            land[bad] = land0[bad]
    cells = int(2 * half * res)
    # only what the drop changes: light moved away from where it would have landed and to where it does. Outside its shadow and its caustic this is exactly 1, with no noise at all
    hit = t_hit > 0
    rng_ = [[-half, half], [-half, half]]
    gain_, _, _ = np.histogram2d(land[hit, 1], land[hit, 0], bins=cells, range=rng_, weights=w[hit])
    lost_, _, _ = np.histogram2d(land0[hit, 1], land0[hit, 0], bins=cells, range=rng_)
    rho_h = n / (2 * half) ** 2
    E = 1.0 + (gain_ - lost_) / (rho_h * (2 * half / cells) ** 2)
    E = cv2.GaussianBlur(E.astype(np.float32), (0, 0), max(blur_cm * res, 0.8))  # the size of the source
    return E, half


def chip_outline(x, y, a_, b_, ang, rs):
    """A bit of dirt: an irregular polygon. x, y and the half-sizes in cm, ang in degrees. Returns its corners."""
    n = int(rs.integers(5, 10))
    t = np.sort(rs.uniform(0, 2 * np.pi, n))
    k = rs.uniform(0.55, 1.0, n)
    c_, s_ = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    ex, ey = a_ * k * np.cos(t), b_ * k * np.sin(t)
    return np.stack([x + c_ * ex - s_ * ey, y + s_ * ex + c_ * ey], 1)


# what a drop has gathered: straw, tan, umber, near-black, a little grey-white. Chosen by eye against the photograph
PALETTE = ((0.5, 0.47, 0.36), (0.36, 0.25, 0.13), (0.2, 0.125, 0.065), (0.06, 0.035, 0.02), (0.78, 0.78, 0.72))
PAL_P = (0.25, 0.38, 0.22, 0.1, 0.05)


def under_maps(dr, dens, i):
    """The underside of a drop, in a square around it: the dirt in it, where it touches the leaf, its roughness and its relief. Returns a function of the place."""
    cr = float(dr["xs"][-1]) * 1.1
    n = int(np.clip(2 * cr * 1100.0 * dens, 48, 2600))
    px = n / (2 * cr)
    rs = np.random.default_rng(SEED + 500 + i)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x_, y_ = (xx + 0.5) / px - cr, (yy + 0.5) / px - cr
    dist = np.hypot(x_, y_) / (cr / 1.1)
    # a low dust everywhere, in clouds, broken into grains
    cl = fbm((n, n), px, cr * 0.2, cr * 1.4, 2.4, SEED + 600 + i)
    tone = sstep(-0.8, 0.8, fbm((n, n), px, 0.01, 0.1, 1.5, SEED + 700 + i))[..., None]
    col = mix(color([0.3, 0.2, 0.1]), color([0.56, 0.53, 0.41]), tone).astype(np.float32).copy()
    cov = (0.75 * sstep(1.0, 1.5, fbm((n, n), px, 0.005, 0.022, 0.5, SEED + 800 + i) + 0.55 * cl)).astype(np.float32).copy()

    def put(pts, rgb, val):
        ip = np.round((pts + cr) * px * 16).astype(np.int32)
        cv2.fillPoly(col, [ip], rgb, cv2.LINE_8, shift=4)
        cv2.fillPoly(cov, [ip], float(val), cv2.LINE_8, shift=4)

    if dr["r"] >= 0.05:
        cr0 = cr / 1.1
        area = np.pi * cr0**2
        lo, hi = 0.0015, 0.011 if dr["r"] > 0.25 else 0.008  # magnified by the drop: bigger flakes read as confetti from this close
        def bit(x, y):
            s_ = lo * (1.0 - rs.uniform() * (1.0 - (lo / hi) ** 1.3)) ** (-1.0 / 1.3)  # many small ones, few big
            put(chip_outline(x, y, s_, s_ * rs.uniform(0.4, 1.0), rs.uniform(0, 180), rs), PALETTE[int(rs.choice(5, p=PAL_P))], rs.uniform(0.55, 0.95))
        for _ in range(int(area * 2200)):  # scattered
            t_, a_ = rs.uniform(0, 2 * np.pi), cr0 * np.sqrt(rs.uniform())
            bit(a_ * np.cos(t_), a_ * np.sin(t_))
        for _ in range(max(int(area * 12), 3)):  # clumps
            t_, a_ = rs.uniform(0, 2 * np.pi), cr0 * np.sqrt(rs.uniform())
            cx, cy = a_ * np.cos(t_), a_ * np.sin(t_)
            sp = rs.uniform(0.02, 0.1)
            for _ in range(int(rs.uniform(30, 160))):
                bit(cx + rs.normal(0, sp), cy + rs.normal(0, sp))
        for _ in range(int(cr0 * 2 * np.pi * 420)):  # the band a drop pushes ahead of it, on its near side
            t_ = -np.pi / 2 + rs.normal(0, 0.9)
            a_ = cr0 * rs.uniform(0.72, 1.0)
            bit(a_ * np.cos(t_), a_ * np.sin(t_))
        for _ in range(int(rs.integers(1, 4))):  # a hair
            pts = [rs.uniform(-0.7 * cr0, 0.7 * cr0, 2)]
            a0, kk = rs.uniform(0, 2 * np.pi), rs.normal(0, 3.0 / cr0)
            ln = cr0 * rs.uniform(0.25, 0.7)
            for _ in range(40):
                a0 += kk * ln / 40
                pts.append(pts[-1] + np.array([np.cos(a0), np.sin(a0)]) * ln / 40)
            ip = np.round((np.array(pts) + cr) * px * 16).astype(np.int32)
            th_ = max(1, int(round(0.0025 * px)))
            cv2.polylines(col, [ip], False, PALETTE[3], th_, cv2.LINE_8, shift=4)
            cv2.polylines(cov, [ip], False, 0.95, th_, cv2.LINE_8, shift=4)
    if i == 0:
        # a length of rust-stained rib seen in the biggest drop: a soft stain, then broken bits along it. Beads along a line read as a worm
        t_ = np.linspace(-1, 1, 240)
        rd_ = np.array([dr["x"], dr["y"]]) / np.hypot(dr["x"], dr["y"])  # along the rib it sits on
        fx, fy = rd_[0] * 0.55 * t_ - rd_[1] * 0.03 * np.sin(4 * t_), rd_[1] * 0.55 * t_ + rd_[0] * 0.03 * np.sin(4 * t_)
        st = np.zeros((n, n), np.float32)
        ip = np.round((np.stack([fx, fy], 1) + cr) * px * 16).astype(np.int32)
        for k in range(len(t_) - 1):
            cv2.line(st, tuple(int(v) for v in ip[k]), tuple(int(v) for v in ip[k + 1]), 1.0, max(1, int((0.02 + 0.05 * sstep(-1, 0.7, t_[k])) * px)), cv2.LINE_8, shift=4)
        st = blur(st, 0.03 * px)
        st = st * (0.75 + 0.35 * sstep(-1, 1, fbm((n, n), px, 0.01, 0.08, 1.4, SEED + 900)))
        col[...] = mix(col, color([0.24, 0.13, 0.06]), np.clip(st, 0, 1)[..., None])
        cov[...] = np.maximum(cov, np.clip(0.6 * st, 0, 0.6))
        ang_ = float(np.degrees(np.arctan2(rd_[1], rd_[0])))
        for k in rs.integers(0, 240, 3200):  # small and many: at 500 and larger they were cut-paper flakes in the magnified drop
            w_ = 0.012 + 0.032 * sstep(-1, 0.7, t_[k])
            s_ = rs.uniform(0.05, 0.16) * w_
            put(chip_outline(fx[k] + rs.normal(0, w_), fy[k] + rs.normal(0, w_), s_ * rs.uniform(1.2, 2.6), s_, ang_ + rs.normal(0, 18), rs), PALETTE[int(rs.choice(4, p=(0.08, 0.34, 0.36, 0.22)))], rs.uniform(0.6, 1.0))
    col = blur(col, 0.8)
    cov = np.clip(blur(cov, 0.8), 0, 1)

    # where the water has gone down onto the leaf. Big smooth shapes with a crisp frayed edge, none at the very rim
    if dr["r"] >= 0.05:
        fr = fbm((n, n), px, cr * 0.1, cr * 1.3, 2.3, SEED + 1000 + i) + 0.22 * fbm((n, n), px, 0.006, 0.05, 1.3, SEED + 1100 + i)
        thr = float(np.quantile(fr, 1.0 - rs.uniform(0.32, 0.5)))
        # crisp along part of its edge only: all crisp, the silver broke into white flakes
        crisp = sstep(-0.1, 0.7, fbm((n, n), px, cr * 0.3, cr * 1.5, 2.4, SEED + 1400 + i))
        edge = (0.03 if dr["r"] >= 0.3 else 0.2) + 0.28 * (1.0 - crisp)  # crisp on a small drop came out as a row of white pebbles
        island = 0.92 * np.clip((fr - thr + edge) / (2.0 * edge), 0.0, 1.0) * sstep(0.95, 0.74, dist)
    else:
        island = np.zeros((n, n), np.float32)
    # the papillae touch the water everywhere, too fine to see: a part of every ray goes on to the leaf. This is what makes the silver a pale cream and not a mirror
    wet = np.maximum(island, (0.3 + 0.16 * sstep(-0.9, 0.9, fbm((n, n), px, cr * 0.08, cr * 0.8, 2.2, SEED + 1500 + i))) * sstep(1.02, 0.8, dist))
    # a drop is a ball lens and shows the world upside down: the sky low on its near side, the leaf in its own shadow high on its far side. A ray entering high lands on the far side of the underside, so that is where it goes dark
    # the leaf under there is seen in the shade of the drop, and the mesh does not cast (see thru): a painted stand-in, picked against the photograph
    nearer = sstep(0.1, 0.85, -y_ / (cr / 1.1))
    far = sstep(0.05, 0.8, y_ / (cr / 1.1) + 0.32 * fbm((n, n), px, cr * 0.15, cr * 0.9, 2.2, SEED + 1600 + i)) * sstep(0.35, 0.9, dist)  # broken: straight, it is a water level
    wet = wet * (1.0 - 0.8 * nearer)
    if dr["r"] < 0.25:  # seen from above a small drop must be clear with the leaf in it: with the silver of the old close-up it was a white button
        wet = np.maximum(wet, 0.8)
        cov = cov * 0.35
    # the boundary itself is dimpled, at all the scales the surface of the leaf has: that breaks the line where total reflection starts into patches
    rel = fbm((n, n), px, 0.05, 0.5, 2.5, SEED + 1200 + i)
    gy, gx = np.gradient(rel, 1.0 / px)
    # scaled to a slope, but never more than a fraction of the drop: on a tiny drop the noise is nearly flat, and scaling it up threw spikes across the frame
    rel = rel - float(rel.mean())
    rel = rel * min(0.2 / float(np.sqrt(np.mean(gx**2 + gy**2)) + 1e-9), 0.12 * cr / (float(np.abs(rel).max()) + 1e-9)) * sstep(1.0, 0.86, dist)
    # rougher in a small drop: its line where total reflection starts is otherwise a flat water level across it
    small = float(sstep(0.5, 0.2, dr["r"]))
    rg = 0.16 + 0.14 * small + 0.16 * sstep(-0.6, 1.2, fbm((n, n), px, 0.05, 0.4, 2.2, SEED + 1300 + i))
    # a wet patch is not clean: a thin grey film of fine dust lies over the leaf there, which is why the green seen in a drop is so pale
    col = mix(col, color([0.62, 0.66, 0.56]), (wet * (1.0 - cov))[..., None])
    cov = np.maximum(cov * (1.0 - 0.3 * wet), 0.26 * wet)
    fk = 0.8 if dr["r"] >= 0.4 else 0.45  # in a small drop the dark, at full strength beside the silver, was a black-and-white mosaic
    col = mix(col, color([0.035, 0.06, 0.035]), far[..., None])
    cov = np.maximum(cov, fk * far)

    def at(x, y):
        mx = ((x - dr["x"] + cr) * px - 0.5).astype(np.float32)
        my = ((y - dr["y"] + cr) * px - 0.5).astype(np.float32)
        rd = lambda f: cv2.remap(f.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return rd(col), rd(cov), rd(wet), rd(rg), rd(rel)

    return at


def all_beads():
    """Small drops gather in the dish and along the ribs. Many tiny, few larger; none near the margin's steep parts."""
    rng = np.random.default_rng(SEED + 1)
    out = list(BEADS)
    for _ in range(4000):
        if len(out) >= len(BEADS) + 14:
            break
        a, rr = rng.uniform(-0.1, np.pi + 0.1), R0 * 0.72 * rng.uniform(0.02, 1.0) ** 0.75
        x, y = rr * np.cos(a), rr * np.sin(a)
        r = float(np.exp(rng.uniform(np.log(0.035), np.log(0.11))))
        if all(np.hypot(x - b[0], y - b[1]) > b[2] * 1.3 + r + 0.05 for b in out):
            out.append((float(x), float(y), r))
    return out


def build(dens, drops):
    """The leaf: a polar grid out to its own outline; everything painted in the plan and read into it."""
    pxcm = PX * dens
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    u = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)
    rr = np.hypot(U, V)
    TH = np.arctan2(V, U)
    RH = rr / outline(TH).astype(np.float32)
    print(f"plan {nx} x {ny}", flush=True)

    rib, sec = veins(shape, pxcm)
    away = sstep(0.9, 2.6, rr)  # the ribs melt into the navel; drawn to the centre they make a star
    vs = blur(rib, max(0.03 * pxcm, 0.6)) * away
    ridge = blur(rib, max(0.1 * pxcm, 0.6)) * away
    sec_s = blur(sec, max(0.035 * pxcm, 0.6)) * away
    sec_w = blur(sec, max(0.09 * pxcm, 0.6)) * away
    net_a = net(shape, pxcm, SEED + 41, max(0.05 * pxcm, 0.7), 0.55)
    net_b = net(shape, pxcm, SEED + 42, max(0.02 * pxcm, 0.6), 0.12)
    cells = fbm(shape, pxcm, 0.08, 0.5, 1.6, SEED + 4)
    swell = polar_fbm(U, V, 0.5, 3.0, 2.8, SEED + 5, stretch=1.6)
    h = 0.028 * swell - 0.022 * vs - 0.055 * ridge - 0.012 * sec_s - 0.014 * sec_w - 0.009 * net_a - 0.002 * net_b + 0.0008 * cells

    # the blade. Dark at the margin, paler and yellower towards the middle, in long uneven tongues along the ribs
    m = polar_fbm(U, V, 1.0, 7.0, 2.7, SEED + 6, stretch=3.0)
    m2 = polar_fbm(U, V, 0.4, 2.2, 2.4, SEED + 7, stretch=2.2)
    inner = sstep(0.62, 0.05, RH + 0.14 * m)
    col = mix(color([0.06, 0.17, 0.03]), color([0.085, 0.2, 0.035]), sstep(-1.6, 1.6, m + 0.3 * m2)[..., None])
    col = mix(col, color([0.12, 0.25, 0.045]), (0.75 * inner)[..., None])
    col = mix(col, color([0.24, 0.36, 0.09]), (0.85 * sstep(3.8, 0.9, rr + 0.5 * m2))[..., None])
    # a dull bloom, broad patches: the wax is not even
    col = col * (1.0 + 0.035 * m2[..., None]) * (1.0 - 0.1 * net_a - 0.05 * net_b)[..., None] * (1.0 - 0.3 * sec_s)[..., None] * (1.0 + 0.04 * cells[..., None])
    # ribs: a thin paler line in a darker groove, paler towards the navel
    rootp = np.exp(-((rr / 7.0) ** 2))
    col = mix(col, color([0.05, 0.12, 0.025]), (0.3 * ridge * (1 - rootp))[..., None])
    col = mix(col, color([0.17, 0.29, 0.075]), ((0.3 + 0.45 * rootp) * vs)[..., None])
    # the navel: a small pale yellow disc on a lobed base, pale ring round it
    nav = sstep(0.82, 0.58, rr + 0.07 * np.sin(5 * TH + 0.7))
    felt = fbm(shape, pxcm, 0.2, 0.9, 2.4, SEED + 15)
    col = mix(col, color([0.55, 0.52, 0.17]) * (1.0 + 0.1 * felt[..., None]), (0.95 * nav)[..., None])
    col = mix(col, color([0.3, 0.42, 0.11]), (0.7 * sstep(1.5, 0.8, rr) * (1 - nav))[..., None])
    h = h * (1.0 - 0.9 * nav) + nav * 0.03 * felt + nav * 0.06

    # age. The margin dies first, in stretches, brown and then yellow inward; old spots with a yellow halo; dust and specks
    sect = sstep(0.0, 1.4, polar_fbm(U, V, 3.0, 16.0, 2.8, SEED + 18, stretch=1.2))
    fray = 0.012 * polar_fbm(U, V, 0.2, 1.4, 2.0, SEED + 19, stretch=1.0)
    edge = sstep(0.975, 1.0, RH + fray)
    col = mix(col, color([0.2, 0.25, 0.06]), (0.38 * sstep(0.9, 0.995, RH + 0.8 * fray) * sect)[..., None])
    col = mix(col, color([0.08, 0.065, 0.03]), (0.7 * edge * np.maximum(sect, 0.2))[..., None])
    # the lip: the sheet has no thickness, and a real margin's edge catches the sun as a thin pale line. Painted, a stand-in
    col = mix(col, color([0.44, 0.5, 0.19]), (0.32 * sstep(0.9975, 0.9995, RH))[..., None])
    rs = np.random.default_rng(SEED + 12)
    stain = fbm(shape, pxcm, 0.15, 1.2, 2.0, SEED + 20)
    for bx_, by_, a_, b_ in ((11.8, 7.0, 0.75, 0.4), (4.4, 16.4, 0.9, 0.35)):
        ang_ = np.arctan2(by_, bx_)
        du, dv = (U - bx_) * np.cos(ang_) + (V - by_) * np.sin(ang_), -(U - bx_) * np.sin(ang_) + (V - by_) * np.cos(ang_)
        bl_ = np.exp(-((du / a_) ** 2) - (dv / b_) ** 2) * (1.0 + 0.35 * stain)
        col = mix(col, color([0.13, 0.19, 0.045]), (0.4 * sstep(0.08, 0.6, bl_))[..., None])
        col = mix(col, color([0.06, 0.04, 0.022]), (0.7 * sstep(0.55, 0.95, bl_))[..., None])

    def chips(canvas, n, lo, hi, gather=None):
        for _ in range(n):
            x, y = rs.uniform(X0, X1), rs.uniform(Y0, Y1)
            if gather is not None and not gather(x, y):
                continue
            a_ = float(np.exp(rs.uniform(np.log(lo), np.log(hi))))
            ip = np.round((chip_outline(x, y, a_, a_ * rs.uniform(0.45, 0.95), rs.uniform(0, 180), rs) - np.array([X0, Y0])) * pxcm * 16).astype(np.int32)
            cv2.fillPoly(canvas, [ip], float(rs.uniform(0.5, 1.0)), cv2.LINE_AA, shift=4)

    dark, tan = np.zeros(shape, np.float32), np.zeros(shape, np.float32)
    area = (X1 - X0) * (Y1 - Y0)
    drift = fbm((256, 256), 256 / 60.0, 2.0, 14.0, 2.4, SEED + 13)
    def drifts(x, y):
        return drift[int((y + 30) * 4.26) % 256, int((x + 30) * 4.26) % 256] + rs.normal(0, 0.3) > 0.55
    chips(dark, int(area * 1.0), 0.012, 0.05, drifts)
    chips(tan, int(area * 1.5), 0.01, 0.045, drifts)
    d_s, t_s = blur(dark, 0.6), blur(tan, 0.6)
    col = mix(col, color([0.03, 0.02, 0.012]), np.clip(d_s, 0, 1)[..., None])
    col = mix(col, color([0.24, 0.2, 0.11]), np.clip(t_s * 0.8, 0, 1)[..., None])

    tr = mix(color([0.2, 0.5, 0.05]), color([0.3, 0.6, 0.08]), sstep(-1, 1, m)[..., None]) * (1.0 - 0.3 * vs)[..., None]

    # what the water does to the sky's light on the leaf, traced
    Esky = np.ones(shape, np.float32)
    for k, dr in enumerate(drops):
        if dr["r"] < 0.05:
            continue
        H = float(dr["zs"][-1])
        res = max(90.0, min(500.0, 60.0 / dr["r"]))
        n_ = int(np.clip(4e6 * dr["r"], 2e5, 3e6))
        E = 0.0
        for wgt, az in ((1.0, 0.0),):
            ca, sa = np.cos(np.radians(az)), np.sin(np.radians(az))
            lt = np.array([ca * SKY[0] - sa * SKY[1], sa * SKY[0] + ca * SKY[1], SKY[2]])
            Ei, half = photons(dr["xs"], dr["zs"], dr["rim"], n_ // 2, SEED + 700 + k + int(az), res, lt, 0.01 + 0.22 * H)
            E = E + wgt * Ei
        i0, j0 = int((dr["y"] - half - Y0) * pxcm), int((dr["x"] - half - X0) * pxcm)
        size = int(2 * half * pxcm)
        if size < 2:
            continue
        Er = cv2.resize(E, (size, size), interpolation=cv2.INTER_LINEAR)
        Er = cv2.GaussianBlur(Er, (0, 0), max(1.0, 0.06 * pxcm))  # the map's grain, seen through clear water, frosted the drop
        a0, b0, a1, b1 = max(i0, 0), max(j0, 0), min(i0 + size, ny), min(j0 + size, nx)
        if a1 > a0 and b1 > b0:
            Esky[a0:a1, b0:b1] *= Er[a0 - i0 : a1 - i0, b0 - j0 : b1 - j0].astype(np.float32)
    col = col * ((1.0 - SKY_SHARE) + SKY_SHARE * Esky)[..., None]

    # the grid: polar, out to the outline
    nth = int(2 * np.pi * R0 * pxcm * 0.72)
    nrh = int(R0 * pxcm * 0.9)
    th = np.linspace(np.radians(-90.0), np.radians(270.0), nth)  # all the way round, its seam out of frame below the navel
    rh = np.linspace(0.0, 1.0, nrh) ** 0.9
    Rm = outline(th)
    GX = (rh[:, None] * Rm[None, :] * np.cos(th)[None, :]).astype(np.float32)
    GY = (rh[:, None] * Rm[None, :] * np.sin(th)[None, :]).astype(np.float32)
    print(f"leaf grid {nth} x {nrh} = {nth * nrh / 1e6:.1f} M", flush=True)
    mx, my = (GX - X0) * pxcm - 0.5, (GY - Y0) * pxcm - 0.5
    rd = lambda f: cv2.remap(f.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    P = np.stack([GX, GY, (height(GX, GY) + rd(h)).astype(np.float32)], -1).astype(np.float32)
    return P, np.clip(rd(col), 0, 1).astype(np.float32), np.clip(rd(tr), 0, 1).astype(np.float32)


def bead_mesh(dr, dens, i):
    u, v, r = dr["x"], dr["y"], dr["r"]
    xs, zs = dr["xs"], dr["zs"]
    contact = float(xs[-1])
    xs2, zs2 = np.r_[xs, np.linspace(xs[-1], 0.0, 24)[1:]], np.r_[zs, np.full(23, zs[-1])]
    L = np.r_[0.0, np.cumsum(np.hypot(np.diff(xs2), np.diff(zs2)))]
    res = int(np.clip(1000 * r * dens, 40, 700))
    t = np.linspace(0, L[-1], res)
    X, Z = np.interp(t, L, xs2).astype(np.float32), np.interp(t, L, zs2).astype(np.float32)
    ph = np.linspace(0, 2 * np.pi, res * 2, dtype=np.float32)
    Xg, Ph = np.meshgrid(X, ph, indexing="ij")
    Zg = np.broadcast_to(Z[:, None], Xg.shape)
    out = dr["rim"](Ph)
    Px, Py = u + Xg * out * np.cos(Ph), v + Xg * out * np.sin(Ph)
    H = float(zs[-1])
    # the water follows the leaf where it rests on it and is level at its crown
    hc = float(height(u, v))
    w_ = np.clip(Zg / H, 0, 1) ** 3
    base = hc + w_ * (height(Px, Py) - hc) + 0.03
    P = np.stack([Px, Py, base + H - Zg], -1).astype(np.float32)
    under = (t > L[-1] - contact * 1.001)[:, None]
    dc, dw, wet, rg, rel = under_maps(dr, dens, i)(P[..., 0], P[..., 1])
    rel = np.maximum(rel, -0.008)
    # the underside stays smooth: this is a clear drop, and the small relief of the plastron model frosted it under glass
    rg = np.where(under, rg, 0.0)
    return P, rg.astype(np.float32), dc, np.where(under, dw, 0.0).astype(np.float32), np.where(under, wet, 0.0).astype(np.float32)


def pond(dens):
    """The water: its own dark colour (it is turbid, so sunlight comes back out of it and the leaf's shadow shows), real ripple as geometry, and the meniscus along the margin where it rests on the water."""
    step = 0.02 / max(dens, 0.2)
    x_ = np.arange(-28.0, 28.0, step, dtype=np.float32)
    y_ = np.arange(-4.0, 31.0, step, dtype=np.float32)
    XX, YY = np.meshgrid(x_, y_)
    ny, nx = XX.shape
    # ripple: a wind's spectrum, slope spectrum falling with k, spread about one direction. Normalised by rms slope, in patches, because a breeze moves over a pond in cat's paws
    rng = np.random.default_rng(SEED + 50)
    fx, fy = np.meshgrid(np.fft.rfftfreq(nx, step), np.fft.fftfreq(ny, step))
    k = np.maximum(np.hypot(fx, fy), 1e-6)
    wind = np.radians(45.0)
    spread = np.cos(np.arctan2(fy, fx) - wind) ** 4 + 0.05
    band = sstep(1 / 15.0, 1 / 5.0, k) * sstep(1 / 0.6, 1 / 1.5, k)  # a broad fractal band looked like stucco: real wavelets are few and smooth
    F = (rng.normal(size=k.shape) + 1j * rng.normal(size=k.shape)) * band * spread * k**-2.0
    rip = np.fft.irfft2(F, s=(ny, nx)).astype(np.float32)
    gy, gx = np.gradient(rip, step)
    rip = rip / float(np.sqrt(np.mean(gx**2 + gy**2)))
    paw = sstep(-0.3, 1.2, cv2.resize(fbm((256, 256), 256 / 60.0, 8.0, 40.0, 2.6, SEED + 51), (nx, ny), interpolation=cv2.INTER_LINEAR))
    # the leaf in plan, and how far outside it each point is
    th = np.arctan2(YY, XX)
    inside = (np.hypot(XX, YY) < outline(th)).astype(np.uint8)
    dist = cv2.distanceTransform(1 - inside, cv2.DIST_L2, 5).astype(np.float32) * step
    # calm in the leaf's lee and right against it
    z = rip * (RIP_CALM + (RIP_PAW - RIP_CALM) * paw) * sstep(0.0, 1.2, dist)
    # the meniscus: decays over the capillary length of water, 0.27 cm (a known figure). Height at the leaf estimated. Only where the margin is actually down on the water
    th_s = th.ravel()
    Rm = outline(th_s)
    rim_h = height(Rm * 0.995 * np.cos(th_s), Rm * 0.995 * np.sin(th_s)).reshape(th.shape).astype(np.float32)
    z += MENISCUS * np.exp(-dist / 0.27) * sstep(0.55, 0.14, rim_h)
    # under the leaf nobody sees it; keep it below the sheet
    in_d = cv2.distanceTransform(inside, cv2.DIST_L2, 5).astype(np.float32) * step
    z = np.where(inside > 0, np.minimum(z, 0.05) - 0.5 * sstep(0.0, 3.0, in_d), z)  # fine relief takes the sheet below its floor here and there: at 0.06 the water came through as black holes
    # the water's own colour: dark green-brown, uneven with what is suspended in it. Reflectance estimated, 2-5% is what turbid water gives
    tone = fbm((256, 256), 256 / 60.0, 5.0, 40.0, 2.6, SEED + 52)
    tone = cv2.resize(tone, (nx, ny), interpolation=cv2.INTER_LINEAR)
    fine = cv2.resize(fbm((512, 512), 512 / 60.0, 0.6, 5.0, 2.2, SEED + 53), (nx, ny), interpolation=cv2.INTER_LINEAR)
    col = mix(color(WATER_A), color(WATER_B), sstep(-1.2, 1.2, tone + 0.25 * fine)[..., None])
    print(f"pond grid {nx} x {ny}, rms slope {float(np.sqrt(np.mean(np.square(np.gradient(z, step)))) * np.sqrt(2)):.3f}", flush=True)
    return np.stack([XX, YY, z.astype(np.float32)], -1), col.astype(np.float32)


def aim():
    """The camera, placed so that the navel lands at NAVEL_SCREEN."""
    nav = np.array([0.0, 0.0, float(height(0.0, 0.0))])
    dv = view_dir(AZ, EL)
    fp = nav + np.array([0.0, 9.0, 0.8])
    tgt = nav.copy()
    for _ in range(4):
        cam = frame_camera(tgt, dv, W, DIST, aperture_mm=APERTURE, focus_point=fp, roll=ROLL_)
        x, y, _z = project(cam, nav[None])
        right, up, _b = _cam_axes(cam)
        tgt = tgt + right * (float(x[0]) - NAVEL_SCREEN[0]) * W - up * (float(y[0]) - NAVEL_SCREEN[1]) * W * 9 / 16
    return frame_camera(tgt, dv, W, DIST, aperture_mm=APERTURE, focus_point=fp, roll=ROLL_)


def rim_on_screen(cam):
    th = np.linspace(np.radians(-25.0), np.radians(205.0), 2000)
    Rm = outline(th)
    x_, y_ = Rm * np.cos(th), Rm * np.sin(th)
    return project(cam, np.stack([x_, y_, height(x_ * 0.999, y_ * 0.999)], 1))


def sketch(path, cam):
    """A hillshade of the leaf, top down, without a render."""
    h_, w_ = 540, 960
    right, up, _b = _cam_axes(cam)
    x, y, _ = project(cam, np.array([[0.0, 0.0, 0.0]]))
    px = (np.arange(w_) + 0.5) / w_
    py = (np.arange(h_) + 0.5) / h_
    Sx, Sy = np.meshgrid(px, py)
    XX = (Sx - x[0]) * W
    YY = -(Sy - y[0]) * W * 9 / 16
    th = np.arctan2(YY, XX)
    inside = np.hypot(XX, YY) < outline(th)
    Z = height(XX, YY).astype(np.float32)
    gy, gx = np.gradient(Z, W / w_)
    n = np.stack([-gx, -gy, np.ones_like(Z)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    shade = np.clip(0.25 + 1.0 * (n @ KEY), 0, 1.4)
    im = np.where(inside[..., None], shade[..., None] * np.array([70, 150, 60]), np.array([18, 22, 20]))
    cv2.imwrite(path, np.clip(im, 0, 255).astype(np.uint8)[..., ::-1])


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    cam = aim()
    rx, ry, _ = rim_on_screen(cam)
    vis = (rx > 0) & (rx < 1)
    print(f"rim: apex y {ry[vis].min():.3f} at x {rx[vis][np.argmin(ry[vis])]:.3f}; x range of the rim {rx[ry < 1].min():.3f} to {rx[ry < 1].max():.3f}", flush=True)
    assert rx.min() > -0.2 and rx.max() < 1.2
    if q == "plan":
        sketch(sys.argv[2], cam)
        return
    dens = {"preview": 0.4, "mid": 0.65, "final": 1.0}[q]
    tag = next((a[6:] for a in sys.argv if a.startswith("--tag=")), None)
    mq = tag or q
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)

    drops = []
    for i, (bu, bv, br) in enumerate(all_beads() if os.environ.get("S64_DROPS", "1") != "0" else []):  # no drops: from this far they came out as pale buttons, not water, and the brief is to keep them only if they are true. The code stays for a closer shot
        bx, bz = drop_profile(br)
        drops.append({"x": bu, "y": bv, "r": br, "xs": bx, "zs": bz, "rim": bead_rim(i, br)})

    P, C, T = build(dens, drops)
    npz = os.path.join(d, f"mesh.{mq}.npz")
    np.savez(npz, P=P, col=C, tr=T)
    meshes = [{"name": "leaf", "npz": npz, "shader_py": SHEET, "params": {"k": 0.1, "rough": 0.44, "spec": 0.16, "sheen": 0.0, "sheen_rough": 0.5}}]
    thru = {"shadow": False, "diffuse": False}
    for i, dr in enumerate(drops):
        Pb, rgb_, dcb, dwb, wetb = bead_mesh(dr, dens, i)
        bp = os.path.join(d, f"b{i}.{mq}.npz")
        np.savez(bp, P=Pb, rg=rgb_, dc=dcb, dw=dwb, wet=wetb)
        meshes.append({"name": f"b{i}", "npz": bp, "material": {"Base Color": [1.0, 1.0, 1.0], "Transmission Weight": 1.0, "Roughness": 0.0, "IOR": 1.33}, "visible": thru})
    wp = os.path.join(d, f"pond.{mq}.npz")
    Pw, Cw = pond(dens)
    np.savez(wp, P=Pw, col=Cw)
    meshes.append({"name": "pond", "npz": wp, "shader_py": WATER, "params": {"ior": 1.33, "rough": 0.04}})

    # a bright day through thin cloud, brighter on one side: that is all the light there is
    envp = pond_env(os.path.join(d, f"sky_env.{mq}.npy"), KEY, top=(0.17, 0.27, 0.5), low=(0.6, 0.68, 0.78), tree=(0.05, 0.08, 0.05), tree_el=7.0, cloud=0.75, disc=(2.0, 0.0), aureole=(22.0, 0.8), gain=1.0, seed=SEED, soft=2.0, gaps=0.05)
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": [{"type": "sun", "name": "sun", "strength": SUN_STRENGTH, "angle": 0.53, "rgb": [1.0, 0.97, 0.92], "loc": (KEY * 1000).tolist(), "target": [0, 0, 0]}],
        "world": [0.0, 0.0, 0.0],
        "env": {"npy": envp, "diffuse": True, "transmission": True},
        "bounces": 40,
        "diffuse_bounces": 4,
        "glossy_bounces": 32,
        "transmission_bounces": 32,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }
    shoot(NAME, scene, q, tag=tag, develop={"exposure": 0.0, "contrast": 1.14, "saturation": 1.14, "black": 0.001, "grain": 0.7, "sharpen": 0.25, "halation": 0.03, "glare": 0.004, "vignette": 0.08})


main()
