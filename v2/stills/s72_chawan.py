"""Shot 72: tea leaving a chip of pressed Pu'er in a white porcelain tasting bowl, from above, in hard sun. The subject is the fluid: the cloud is the 3D solve m8 (s70_flow), tea seeping from two lumps. Replaces s71_liuli (glass, from the side: "looks fake") and s70_chatang (bowl from low down: "an ashtray of ash water").

    python3 -I v2/stills/s72_chawan.py look TAG k=v,k=v|@file.json [preview|mid|final]     out/v2/s72_chawan/TAG.jpg

The vessel is the bowl of a tea-tasting set (审评碗), white so that the colour of the liquor can be judged. Found: ISO 3103 asks for a white porcelain or glazed bowl of 200 or 380 ml. Not verified: 95 mm across, 56 mm high, 240 ml is my memory of GB/T 23776; the text was not found. The wall's straight flare and small fillet are from memory too.

The solve was made in a smaller bowl (s71_solve.json), and that does not matter: over the saved frames its cloud stays inside |x| < 2.24, |y| < 1.44, z > -2.36 (measured from the VDBs), clear of the wall and the floor of either vessel.

What shows the water, with no stream and no splash:
- the cloud's shadow on the bottom, apart from the cloud by the depth between them;
- the sun gathered by what is left of the waves on the surface, the moving web on the white bottom (caustic(): rays refracted through the surface by forward mapping, painted into the albedo, right in the sun and a small error in the fill; a stand-in for caustics, since shadow rays pass the surface unbent);
- thin bright lines where the meniscus mirrors the room, at the wall and at the chip.
Colour: red : green : blue absorption about 1 : 3.6 : 12, measured from ref/tea_overhead zisha-03 and ceramic-01. They are display values, so the cameras' curves are in them.
Estimates: capillary length 0.257 cm, contact angle 30 degrees, surface tension over density 62 cm3/s2 at about 70 C. The depth of field is a real macro lens's: aperture in mm.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit

NAME = "s72_chawan"
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(kit.OUT, NAME)
SHP = os.path.join(HERE, "s70_shader.py")

LC = 0.257
THETA_C = np.radians(30.0)
N_WATER = 1.33
GRAV = 981.0
SIGMA_RHO = 62.0
SIGMA = [1.0, 3.6, 12.0]

P0 = dict(
    body=[0.9, 0.895, 0.865],  # the porcelain under its glaze
    glaze_rough=0.05,
    R=4.6,  # inside, at the lip
    depth=5.0,  # inside, from the lip to the floor
    foot=2.5,  # where the straight wall would meet the floor
    fillet=0.22,
    z_rim=1.0,  # lip above the still water
    lip=0.16,
    foot_out=2.7,
    E=60.0,  # camera over the horizontal, degrees
    W=7.6,  # frame width, cm
    dist=46.0,
    cx=0.1,  # the frame's centre, in the plane of the water
    cy=-2.2,
    aperture=12.0,
    focus=[-0.3, -0.3, -0.8],
    tea="m8",  # the solved cloud, out/v2/s70_sim/NAME/T.vdb
    tea_t="004.800",
    tea_K=0.4,
    tea_sigma=[1.0, 2.6, 7.0],  # by eye: at the liquor's ratio the dense parts went blood red
    liquor=0.028,  # absorption of the liquor in the red, per cm
    t=0.0,  # s, for what moves on the surface
    ripple=0.012,  # rms slope of what is left of the waves
    ripple_k=[1.6, 11.0],  # their wavenumbers, per cm
    caustic=4.0,  # the most the waves may gather the sun on the bottom; 0 for none
    # the chips, over the sources of the solve (s71_solve.json: x -1.0, y 0.1, half-widths 0.7 and 0.35; x 1.35, y 0, 0.3 and 0.2)
    chips=[
        dict(x=-1.0, y=0.1, ax=0.86, ay=0.5, az=0.17, yaw=7.0, zc=-0.015, seed=3),
        dict(x=1.35, y=0.0, ax=0.42, ay=0.3, az=0.12, yaw=-24.0, zc=-0.01, seed=5),
    ],
    # the sun, towards it
    sun_az=-112.0,  # degrees from +y (into the frame) towards +x
    sun_el=58.0,
    sun_E=3.0,
    sun_rgb=[1.0, 0.94, 0.84],
    fill_W=560.0,
    # the room in reflections
    room_ceil=0.09,
    room_wall=0.04,
    win_L=0.5,
    win_cx=1.0,
    win_cy=1.2,
    win_wx=2.2,
    win_wy=1.7,
    win_tilt=-12.0,
    win_soft=0.3,
    win_rgb=[1.0, 0.98, 0.94],
    arc_L=4.0,
    arc_az0=-15.0,  # degrees from +y
    arc_az=70.0,
    arc_el=[12.0, 24.0],
    top_L=2.5,
    top_el=74.0,
    table=dict(kind="linen", rgb=[0.028, 0.042, 0.075], thread=0.055, rough=0.86, angle=11.0, max_verts=1.6e6),
    gobo=dict(dist=120.0, angle=-18.0, c=[0.0, 0.0], panes=[-9.6, -7.1, -5.2, 9.0], v=[-14.0, 14.0]),
    exposure=0.0,
    spp=None,
    dev={},
)


def zprof(r, o):
    """The inside of the bowl: a flat floor and a straight flaring wall, joined by a small fillet (a soft maximum)."""
    zf = o["z_rim"] - o["depth"]
    cone = o["z_rim"] - (o["R"] - r) * o["depth"] / (o["R"] - o["foot"])
    return zf + o["fillet"] * np.logaddexp(0.0, (cone - zf) / o["fillet"])


def slope(r, o):
    zf = o["z_rim"] - o["depth"]
    cone = o["z_rim"] - (o["R"] - r) * o["depth"] / (o["R"] - o["foot"])
    return o["depth"] / (o["R"] - o["foot"]) / (1.0 + np.exp(-(cone - zf) / o["fillet"]))


def r_of_z(z, o):
    r = np.linspace(0.0, o["R"], 4000)
    return np.interp(z, zprof(r, o), r)


def capacity_ml(o):
    r = np.linspace(0.0, o["R"], 4000)
    return float(np.sum(np.pi * r * r * np.gradient(zprof(r, o), r) * (r[1] - r[0])))


def wob(th):
    """Hand-thrown: not quite round."""
    return 0.012 * np.cos(2 * th + 0.8) + 0.007 * np.cos(3 * th - 1.1) + 0.003 * np.cos(5 * th + 2.0)


def contact(o):
    z = 0.09
    for _ in range(4):
        rc = r_of_z(z, o)
        beta = np.arctan(slope(rc, o))
        z = 2 * LC * np.sin(max(beta - THETA_C, 0.0) / 2)
    return z, r_of_z(z, o)


def meniscus(d, h0):
    h = np.geomspace(h0, 0.0008, 800)
    x = LC * (np.arccosh(2.0 * LC / h) - np.sqrt(np.maximum(4.0 - (h / LC) ** 2, 0.0)))
    x = x - x[0]
    dd = np.maximum(d, 0.0)
    out = np.exp(np.interp(dd, x, np.log(h)))
    return np.where(dd > x[-1], h[-1] * np.exp(-(dd - x[-1]) / LC), out)


def thetas(q):
    n = {"preview": 1200, "mid": 2000, "final": 3600}[q]
    return np.linspace(0.0, 2 * np.pi, n + 1)


def table_z(o):
    return o["z_rim"] - o["depth"] - 0.5


def build_bowl(wet_path, dry_path, o, q):
    th = thetas(q)
    h0, rc = contact(o)
    R = o["R"]
    nr = {"preview": 420, "mid": 760, "final": 1300}[q]
    r_in = np.linspace(0.0, R, nr)
    i = int(np.searchsorted(r_in, rc))
    r_in = np.concatenate([r_in[:i], [rc], r_in[i:]])
    body = np.array(o["body"], np.float32)
    T, Rb = np.meshgrid(th, r_in)
    rr = Rb + wob(T) * kit.sstep(1.0, 3.0, Rb)
    x, y = rr * np.cos(T), rr * np.sin(T)
    Z = zprof(Rb, o)
    col = np.broadcast_to(body, T.shape + (3,)).astype(np.float32)
    if o["caustic"]:
        col = (col * caustic(o, x, y, Z)[..., None]).astype(np.float32)
    P = np.stack([x, y, Z], -1).astype(np.float32)
    rough = np.full(T.shape, o["glaze_rough"], np.float32)
    np.savez(wet_path, P=P[: i + 1], col=col[: i + 1], rough=rough[: i + 1])
    # the lip, round
    t = o["lip"]
    a = np.linspace(-np.pi / 2, np.pi / 2, 26)[1:-1]
    Tl, Al = np.meshgrid(th, a)
    Rl = R + wob(Tl) + t / 2 + t / 2 * np.sin(Al)
    Zl = o["z_rim"] + t / 2 * np.cos(Al)
    # outside, down to the foot and the table
    z_tab = table_z(o)
    s = np.linspace(0.0, 1.0, 60)[1:]
    To, So = np.meshgrid(th, s)
    Ro = R + t + (o["foot_out"] - (R + t)) * So**1.1
    Zo = o["z_rim"] + (z_tab + 0.03 - o["z_rim"]) * So**0.98
    Rr = Ro + wob(To) * (1.0 - So)
    Pd = np.concatenate([P[i:], np.stack([Rl * np.cos(Tl), Rl * np.sin(Tl), Zl], -1).astype(np.float32), np.stack([Rr * np.cos(To), Rr * np.sin(To), Zo], -1).astype(np.float32)])
    Cd = np.concatenate([col[i:], np.broadcast_to(body, Tl.shape + (3,)), np.broadcast_to(body, To.shape + (3,))]).astype(np.float32)
    np.savez(dry_path, P=Pd, col=Cd, rough=np.full(Pd.shape[:2], o["glaze_rough"], np.float32))


def waves(o):
    """What is left of the waves, some time after the water went in: random phases, every mode with its own capillary-gravity frequency, so the pattern moves as water does. In a periodic box: the wall is not modelled, and the waves are faded out towards it (build_water)."""
    N, L = 512, 12.0
    k1 = 2 * np.pi * np.fft.fftfreq(N, L / N)
    KX, KY = np.meshgrid(k1, k1)
    K = np.hypot(KX, KY)
    rng = np.random.default_rng(72)
    band = kit.sstep(o["ripple_k"][0] * 0.7, o["ripple_k"][0], K) * kit.sstep(o["ripple_k"][1] * 1.3, o["ripple_k"][1], K)
    A = band / np.maximum(K, 0.1) ** 1.6 * rng.normal(0.0, 1.0, K.shape) * np.exp(2j * np.pi * rng.random(K.shape))
    om = np.sqrt(GRAV * K + SIGMA_RHO * K**3)
    h = np.real(np.fft.ifft2(A * np.exp(-1j * om * o["t"])))
    gy, gx = np.gradient(h, L / N)
    return (h * o["ripple"] / np.sqrt(np.mean(gx**2 + gy**2))).astype(np.float32), L


def to_sun(o):
    az, el = np.radians(o["sun_az"]), np.radians(o["sun_el"])
    return np.array([np.sin(az) * np.cos(el), np.cos(az) * np.cos(el), np.sin(el)])


def caustic(o, x, y, z):
    """How much the sun on the bottom is gathered and spread by the waves. 1 where the flat surface would give 1, and where the lip shadows the point."""
    h, L = waves(o)
    N = h.shape[0]
    up = 4
    hu = cv2.resize(h, (N * up, N * up), interpolation=cv2.INTER_CUBIC)
    dx = L / (N * up)
    gy, gx = np.gradient(hu, dx)
    c = (np.arange(N * up) + 0.5) * dx - L / 2
    X, Y = np.meshgrid(c, c)
    s = -to_sun(o)

    def land(gx, gy):
        nz = 1.0 / np.sqrt(1 + gx**2 + gy**2)
        nx, ny = -gx * nz, -gy * nz
        cosi = -(s[0] * nx + s[1] * ny + s[2] * nz)
        e = 1.0 / N_WATER
        k = e * cosi - np.sqrt(1 - e**2 * (1 - cosi**2))
        tx, ty, tz = e * s[0] + k * nx, e * s[1] + k * ny, e * s[2] + k * nz
        px, py = X.copy(), Y.copy()
        for _ in range(3):
            d = np.maximum(-zprof(np.hypot(px, py), o), 0.0)
            px, py = X + tx / -tz * d, Y + ty / -tz * d
        return px, py

    M = 512  # 4 x 4 rays per bin: any ratio that is not whole gives a woven moire on the bottom

    def splat(px, py):
        ix = np.clip(((px + L / 2) / L * M).astype(np.int64), 0, M - 1)
        iy = np.clip(((py + L / 2) / L * M).astype(np.int64), 0, M - 1)
        return np.bincount((iy * M + ix).ravel(), minlength=M * M).reshape(M, M).astype(np.float32)

    inside = np.hypot(X, Y) < contact(o)[1]
    px, py = land(gx, gy)
    A = splat(px[inside], py[inside])
    px0, py0 = land(np.zeros_like(gx), np.zeros_like(gy))
    B = splat(px0[inside], py0[inside])
    sig = 1.5  # the sun's own width at this depth, 0.53 degrees over 4 cm is 0.037 cm
    A, B = cv2.GaussianBlur(A, (0, 0), sig), cv2.GaussianBlur(B, (0, 0), sig)
    I = np.where(B > 0.25 * np.median(B[B > 0]), A / np.maximum(B, 1e-6), 1.0).astype(np.float32)
    I = np.clip(I, 0.0, o["caustic"])
    m = lambda u: ((u + L / 2) / L * M - 0.5).astype(np.float32)
    v = cv2.remap(I, m(x), m(y), cv2.INTER_LINEAR)
    # only where the sun gets to, by the ray the renderer's shadow takes
    sn = to_sun(o)
    qx, qy = x + sn[0] / sn[2] * (o["z_rim"] - z), y + sn[1] / sn[2] * (o["z_rim"] - z)
    lit = kit.sstep(0.0, 0.05, o["R"] - np.hypot(qx, qy))
    print(f"[caustic] p1 {np.percentile(I[B > 0], 1):.2f} p50 {np.percentile(I[B > 0], 50):.2f} p99 {np.percentile(I[B > 0], 99):.2f}", flush=True)
    return 1.0 + (v - 1.0) * lit


def pressed_tea(seed, n=1400, size=3.2):
    """The face of a chip of pressed tea: hundreds of flattened, wet leaves laid over one another, painted in order so each lies over the last. Returns height (0 to 1) and colour; size in cm."""
    rng = np.random.default_rng(seed)
    px = n / size
    H = np.zeros((n, n), np.float32)
    C = np.zeros((n, n, 3), np.float32)
    C[...] = (0.02, 0.011, 0.007)
    count = 1100
    for i in range(count):
        L = rng.uniform(0.3, 1.1)
        w = rng.uniform(0.035, 0.1) * (0.5 if rng.random() < 0.3 else 1.0)
        c0 = rng.uniform(0.0, size, 2)
        a = rng.uniform(0.0, np.pi)
        bend = rng.normal(0.0, 0.5)
        s = np.linspace(-0.5, 0.5, 18)
        ang = a + bend * s
        # a leaf: pointed at both ends, wider past the middle, its edge not clean
        cx = c0[0] + L * np.cumsum(np.cos(ang)) / 18
        cy = c0[1] + L * np.cumsum(np.sin(ang)) / 18
        wid = w * np.sin(np.pi * (s + 0.5)) ** 0.7 * (1 + 0.14 * rng.normal(0, 1, 18))
        nx, ny = -np.sin(ang), np.cos(ang)
        poly = np.concatenate([np.stack([cx + nx * wid, cy + ny * wid], -1), np.stack([cx - nx * wid, cy - ny * wid], -1)[::-1]])
        pts = (poly * px).astype(np.int32)
        tone = rng.lognormal(0.0, 0.32)
        if rng.random() < 0.075:  # a golden bud, in a ripened cake
            col = np.array([0.2, 0.105, 0.032]) * tone
        else:
            col = np.array([0.052, 0.024, 0.0125]) * tone
        cv2.fillPoly(C, [pts], tuple(float(v) for v in col), lineType=cv2.LINE_AA)
        cv2.fillPoly(H, [pts], float((i + 1) / count + rng.normal(0.0, 0.05)), lineType=cv2.LINE_AA)
    # each leaf lies in one pressed layer: only the last ones show, so the height is relative to what is near it
    H = H - cv2.GaussianBlur(H, (0, 0), 0.14 * px)
    H = cv2.GaussianBlur(H, (0, 0), 0.0035 * px)
    H = H / max(float(np.percentile(np.abs(H), 99.5)), 1e-6)
    fine = kit.fbm((n, n), px, 0.006, 0.06, 0.8, seed + 100).astype(np.float32)
    return np.clip(H, -1.2, 1.2) + 0.09 * fine, np.clip(C * (1.0 + 0.1 * fine[..., None]), 0.0, 1.0).astype(np.float32), size


def outline(T, seed, smooth=False):
    """A chip broken off a cake: not an ellipse; a few big bites and a torn edge. smooth: the bites only."""
    rng = np.random.default_rng(seed)
    r = np.ones_like(T)
    for m, amp in ((2, 0.1), (3, 0.09), (5, 0.06), (8, 0.035), (13, 0.022), (21, 0.014), (34, 0.009), (55, 0.006)):
        ph = rng.uniform(0, 2 * np.pi)
        if m <= 5 or not smooth:
            r = r + amp * np.cos(m * T + ph)
    return r


def chip_xy(ch, X, Y):
    """Into the chip's own frame: rotated by its yaw and scaled by its half-widths."""
    a = np.radians(ch["yaw"])
    dx, dy = X - ch["x"], Y - ch["y"]
    return (dx * np.cos(a) + dy * np.sin(a)) / ch["ax"], (-dx * np.sin(a) + dy * np.cos(a)) / ch["ay"]


def build_chip(path, ch, q):
    """Closed: the top face from the middle to the torn edge, and the underside back. The soaked underside and edge are darker."""
    H, C, size = pressed_tea(ch["seed"])
    nr, nt = {"preview": (260, 900), "mid": (420, 1500), "final": (700, 2600)}[q]
    th = np.linspace(0.0, 2 * np.pi, nt + 1)
    rho = np.linspace(0.0, 1.0, nr) ** 0.75
    T, Rh = np.meshgrid(th, rho)
    r = outline(T, ch["seed"]) * Rh
    a = np.radians(ch["yaw"])
    lx, ly = ch["ax"] * r * np.cos(T), ch["ay"] * r * np.sin(T)
    mapx = ((lx + size / 2) / size * (H.shape[1] - 1)).astype(np.float32)
    mapy = ((ly + size / 2) / size * (H.shape[0] - 1)).astype(np.float32)
    hh = cv2.remap(H, mapx, mapy, cv2.INTER_LINEAR)
    cc = cv2.remap(C, mapx, mapy, cv2.INTER_LINEAR)
    dome = np.maximum(1.0 - Rh**5, 0.0) ** 0.5
    ztop = ch["zc"] + ch["az"] * dome + 0.045 * hh * kit.sstep(1.0, 0.86, Rh)
    zbot = ch["zc"] - 1.05 * ch["az"] * dome - 0.03 * hh[::1] * kit.sstep(1.0, 0.86, Rh)
    wx, wy = ch["x"] + lx * np.cos(a) - ly * np.sin(a), ch["y"] + lx * np.sin(a) + ly * np.cos(a)
    P = np.concatenate([np.stack([wx, wy, ztop], -1), np.stack([wx, wy, zbot], -1)[::-1]]).astype(np.float32)
    # wet at the waterline, drying upward: darker and glossier low down
    above = kit.sstep(0.0, 0.11, ztop)
    ct = cc * (0.62 + 0.38 * above)[..., None]
    rt = (0.24 + 0.32 * above) * (1.0 + 0.2 * np.clip(hh, -1, 1))
    Cf = np.concatenate([ct, (cc * 0.6)[::-1]]).astype(np.float32)
    Rf = np.concatenate([rt, np.full(rt.shape, 0.22)[::-1]]).astype(np.float32)
    np.savez(path, P=P, col=Cf, rough=Rf)


def chip_lift(x, y, o):
    """The water climbs the chip, wetting it: a small meniscus round the outline, which is what gives the thin bright line there."""
    z = np.zeros_like(x)
    for ch in o["chips"]:
        u, v = chip_xy(ch, x, y)
        T = np.mod(np.arctan2(v, u), 2 * np.pi)
        e = np.hypot(u, v) / outline(T, ch["seed"], smooth=True)
        d = np.maximum(e - 1.0, 0.0) * 0.5 * (ch["ax"] + ch["ay"])
        z = z + 0.035 * np.exp(-d / (0.5 * LC))
    return z


def build_water(path, o, q):
    """Closed: the surface from the middle out, into the wall by a hair, then back under the glaze."""
    th = thetas(q)
    h0, rc = contact(o)
    nr = {"preview": 700, "mid": 1100, "final": 1800}[q]
    d = np.concatenate([np.linspace(rc, 0.4, nr)[:-1], np.geomspace(0.4, 0.0012, 60), [-0.012]])
    T, Dd = np.meshgrid(th, d)
    r = np.maximum(rc - Dd, 0.0) + wob(T) * kit.sstep(0.0, 1.2, rc - Dd)
    x, y = r * np.cos(T), r * np.sin(T)
    fade = kit.sstep(0.0, 0.6, Dd)
    z = meniscus(Dd, h0)
    if o["ripple"]:
        h, L = waves(o)
        g = lambda u: ((u + L / 2) / L * h.shape[0] - 0.5).astype(np.float32)
        z = z + cv2.remap(h, g(x), g(y), cv2.INTER_CUBIC) * fade
    z = z + chip_lift(x, y, o) * fade
    top = np.stack([x, y, z], -1)
    r2 = np.linspace(rc + 0.012, 0.0, 60)
    T2, R2 = np.meshgrid(th, r2)
    W2 = R2 + wob(T2) * kit.sstep(1.0, 3.0, R2)
    bot = np.stack([W2 * np.cos(T2), W2 * np.sin(T2), zprof(R2, o) - 0.03], -1)
    np.savez(path, P=np.concatenate([top, bot]).astype(np.float32))


def camera(o):
    e = np.radians(o["E"])
    view = np.array([0.0, -np.cos(e), np.sin(e)])
    target = np.array([o["cx"], o["cy"], 0.0])
    loc = target + view * o["dist"]
    cam = {"loc": loc.tolist(), "target": target.tolist(), "lens_mm": 36.0 * o["dist"] / o["W"], "roll": 0.0}
    if o["aperture"]:
        cam["aperture_mm"] = o["aperture"]
        cam["focus_distance"] = float(np.dot(loc - np.array(o["focus"]), view))
    return cam


def env(path, cam, o):
    """The room, for reflections only: dim, with something bright where the water mirrors it, and what the meniscus swings the reflection to: low on the far wall for the near side of the bowl, the ceiling for the far side. Its mullions and clutter break the bright line along the water's edge into dashes, as in ceramic-01."""
    kit.room_env(path, cam, {"window": 0.0, "strip": 0.0, "ceil": o["room_ceil"], "wall": o["room_wall"], "floor": 0.01})
    E = np.load(path)
    h, w = E.shape[:2]
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    loc, tgt = np.array(cam["loc"], float), np.array(cam["target"], float)
    v = (tgt - loc) / np.linalg.norm(tgt - loc)
    mirror = np.array([v[0], v[1], -v[2]])
    e1 = np.array([1.0, 0.0, 0.0])
    e2 = np.cross(mirror, e1)
    e2 = e2 / np.linalg.norm(e2)
    if e2 @ np.array([0.0, 1.0, 0.0]) < 0:
        e2 = -e2
    dm = d @ mirror.astype(np.float32)
    x = np.degrees(np.arctan2(d @ e1.astype(np.float32), dm))
    y = np.degrees(np.arctan2(d @ e2.astype(np.float32), dm))
    a = np.radians(o["win_tilt"])
    xr, yr = (x - o["win_cx"]) * np.cos(a) - (y - o["win_cy"]) * np.sin(a), (x - o["win_cx"]) * np.sin(a) + (y - o["win_cy"]) * np.cos(a)
    pane = kit.sstep(o["win_wx"], o["win_wx"] * (1 - o["win_soft"]), np.abs(xr)) * kit.sstep(o["win_wy"], o["win_wy"] * (1 - o["win_soft"]), np.abs(yr)) * (dm > 0)
    E = E + (o["win_L"] * pane)[..., None].astype(np.float32) * np.array(o["win_rgb"], np.float32)
    az = np.degrees(np.arctan2(d[..., 0], d[..., 1]))
    el = np.degrees(np.arcsin(np.clip(d[..., 2], -1, 1)))
    band = kit.sstep(o["arc_az"], o["arc_az"] * 0.75, np.abs(az - o["arc_az0"])) * kit.sstep(o["arc_el"][0] - 3, o["arc_el"][0] + 3, el) * kit.sstep(o["arc_el"][1] + 3, o["arc_el"][1] - 3, el)
    azm = np.mod(az - o["arc_az0"] + 7.0, 13.5) - 6.75
    bars = kit.sstep(1.2, 2.2, np.abs(azm))
    lumps = cv2.resize(kit.fbm((256, 512), 512 / 360.0, 6.0, 90.0, 2.0, 725), (w, h), interpolation=cv2.INTER_LINEAR)
    band = band * bars * np.clip(0.75 + 0.5 * lumps, 0.15, 1.5)
    cap = kit.sstep(o["top_el"] - 5, o["top_el"] + 5, el) * np.clip(0.8 + 0.5 * lumps, 0.2, 1.5)
    E = E + (o["arc_L"] * band + o["top_L"] * cap)[..., None].astype(np.float32) * np.array([1.0, 0.97, 0.92], np.float32)
    np.save(path, E.astype(np.float32))


def gobo(path, o):
    """The window the sun comes through, as a thing that only casts shadows. Quads on the plane of the water, lifted towards the sun, so a quad falls where it is drawn; dist sets the softness of the edges (the sun is 0.53 degrees across)."""
    g = o["gobo"]
    a = np.radians(g["angle"])
    u, v = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
    c = np.array(g["c"], float)
    far = 300.0
    quads = []

    def rect(u0, u1, v0, v1):
        quads.append([c + u * u0 + v * v0, c + u * u1 + v * v0, c + u * u1 + v * v1, c + u * u0 + v * v1])

    edges = g["panes"]  # in u: open from edges[0] to edges[1], from edges[2] to edges[3], ...
    rect(-far, edges[0], -far, far)
    for i in range(1, len(edges) - 1, 2):
        rect(edges[i], edges[i + 1], -far, far)
    rect(edges[-1], far, -far, far)
    rect(edges[0], edges[-1], g["v"][1], far)
    rect(edges[0], edges[-1], -far, g["v"][0])
    s = to_sun(o)
    V, F = [], []
    for q in quads:
        b = len(V)
        for p_ in q:
            V.append(np.array([p_[0], p_[1], 0.0]) + s * g["dist"])
        F += [[b, b + 1, b + 2], [b, b + 2, b + 3]]
    np.savez(path, V=np.array(V, np.float32), F=np.array(F, np.int32))


def scene(q, o, sub, tag):
    cam = camera(o)
    os.makedirs(sub, exist_ok=True)
    wet, dry, water, tab, e, gp = [os.path.join(sub, f"{tag}_{n}") for n in ("wet.npz", "dry.npz", "water.npz", "tab.npz", "env.npy", "gobo.npz")]
    build_bowl(wet, dry, o, q)
    build_water(water, o, q)
    kit.table_mesh(tab, cam, {**o["table"], "z": table_z(o)})
    env(e, cam, o)
    print(f"[bowl] {capacity_ml(o):.0f} ml to the brim", flush=True)
    gl = {"Base Color": "col", "Roughness": 0.42, "Specular IOR Level": 0.5, "Coat Weight": 1.0, "Coat Roughness": "rough"}
    meshes = [
        {"name": "wet", "npz": wet, "material": {**gl, "Coat IOR": 1.5 / N_WATER}},
        {"name": "dry", "npz": dry, "material": {**gl, "Coat IOR": 1.5}},
        {"name": "water", "npz": water, "shader_py": SHP, "params": {"kind": "water", "ior": N_WATER, "liquor": o["liquor"], "sigma": SIGMA}},
        {"name": "table", "npz": tab, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.3}},
    ]
    for i, ch in enumerate(o["chips"]):
        cp = os.path.join(sub, f"{tag}_chip{i}.npz")
        build_chip(cp, ch, q)
        meshes.append({"name": f"chip{i}", "npz": cp, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5}})
    if o["gobo"]:
        gobo(gp, o)
        meshes.append({"name": "gobo", "npz": gp, "material": {"Base Color": [0.0, 0.0, 0.0], "Roughness": 1.0, "Specular IOR Level": 0.0}, "visible": {"camera": False, "diffuse": False, "glossy": False, "transmission": False, "shadow": True}})
    vols = []
    if o["tea"]:
        vdb = os.path.join(kit.OUT, "s70_sim", o["tea"], o["tea_t"] + ".vdb")
        if not os.path.exists(vdb):
            raise SystemExit(f"no solve frame: {vdb}")
        vols.append({"name": "tea", "vdb": vdb, "shader_py": SHP, "params": {"kind": "tea", "sigma": o["tea_sigma"], "K": o["tea_K"]}})
    return {
        "camera": cam,
        "meshes": meshes,
        "volumes": vols,
        "lights": [
            {"type": "sun", "name": "sun", "strength": o["sun_E"], "angle": 0.53, "rgb": o["sun_rgb"], "loc": (to_sun(o) * 1000).tolist(), "target": [0.0, 0.0, 0.0]},
            {"name": "fill", "type": "area", "size": [120.0, 120.0], "loc": [10.0, -30.0, 90.0], "target": [0.0, 0.0, 0.0], "watts": o["fill_W"] * 10, "rgb": [0.82, 0.9, 1.0], "hide_in_gloss": True},
        ],
        "env": {"npy": e, "diffuse": False, "transmission": True, "no_diffuse_paths": True},
        "bounces": 24,
        "transmission_bounces": 16,
        "glossy_bounces": 8,
        "diffuse_bounces": 6,
        "volume_bounces": 0,
        "clamp_indirect": 30.0,
        "denoise": o.get("denoise", True),
        "res": {"preview": [960, 540], "mid": [1280, 720], "final": [1920, 1080]}[q],
        "spp": o["spp"] or {"preview": 64, "mid": 128, "final": 256}[q],
    }


DEVELOP = dict(exposure=0.0, contrast=1.1, saturation=1.0, black=0.0, grain=1.1, sharpen=0.2, halation=0.06, glare=0.0, vignette=0.14, ca=0.0003, seed=72)


def render(cfg, sub, tag):
    t = time.time()
    p = kit._render_local(cfg, sub, tag)
    print(f"[{tag}] {time.time()-t:.0f} s", flush=True)
    return p


def look(tag, over, q):
    from darkroom import develop, print_look

    o = {**P0, **over}
    if isinstance(over.get("table"), dict):
        o["table"] = {**P0["table"], **over["table"]}
    os.makedirs(D, exist_ok=True)
    t0 = time.time()
    cfg = scene(q, o, D, tag)
    print(f"[{tag}] built in {time.time()-t0:.0f} s", flush=True)
    L = np.load(render(cfg, D, tag))
    print(tag, "p50", np.median(L, axis=(0, 1)).round(3), "p99", np.percentile(L, 99, axis=(0, 1)).round(3), flush=True)
    x = print_look(develop(L.astype(np.float32), **{**DEVELOP, **o["dev"], "exposure": o["exposure"]}))
    cv2.imwrite(os.path.join(D, tag + ".jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])


def args(s):
    if not s or s == "-":
        return {}
    if s.startswith("@"):
        return json.load(open(s[1:]))
    return {k: json.loads(v) for k, v in (kv.split("=", 1) for kv in s.split(","))}


if __name__ == "__main__":
    if sys.argv[1] == "look":
        look(sys.argv[2], args(sys.argv[3]) if len(sys.argv) > 3 else {}, sys.argv[4] if len(sys.argv) > 4 else "preview")
    else:
        raise SystemExit(__doc__)
