"""Shot 6: Jun ware (钧窑), the inside of a bowl close up, over its near side. The far rim is the arc, the glaze runs down from it towards the camera, and the eye goes to one run and the earthworm tracks in it.

    python3 -I v2/stills/s06_junyao.py flat                      the fields only, no render: out/v2/s06_junyao/cand_flat.jpg
    python3 -I v2/stills/s06_junyao.py [preview|mid]             it is a real medium
    python3 -I v2/stills/s06_junyao.py cand                      final size, tag cand; never writes final.*
    GEWU_MOVE=final python3 -I v2/stills/s06_junyao.py final     the turn: s06_junyao_cand_move_final, not the film's folder
    python3 -I v2/stills/s06_junyao.py deliver                   develops those frames into s06_junyao_take_cand (f###.png, f###.jpg, take.mp4)

The structure comes from the firing (s06_flow.py): the glaze ran, so it is thin at the lip and fat lower down; the crack network of the drying layer healed into troughs; the copper stroke was carried.
Colour then follows from thickness: thin glaze shows the iron body (紫口, an old name and an old observation: ref/jun/report.md has the Met's and Cleveland's lips, tan to brown), thick glaze is milky.
- medium: a real one in a closed shell, with sheets in it because a volume cannot read mesh attributes. sigma values are estimates (the report found no measured mu_s, mu_a, g for old Jun). It is thinner than the last version's (optical depth about 1 at 0.9 mm, not 2-3): at 2-3 everything under it went soft, and softness was the fault;
- track: a darker glassier band, less milk (李媛 2013, measured width 1.0-1.6 mm), with pale milk gathered along a wavy edge (that paper's fig. 3), and a shallow trough on the surface from the flow model, an estimate, which is what catches the window;
- copper: pink where thin, magenta to purple when thicker, in pale lace streaked along the flow (ref/jun/img/detail_cma1957_36_purple_edge.png, met_50233_05.jpg): colours read off those by eye;
- no bubbles sown in a highlight: small ones at random depth, a steep size law (Wang 2024: most under 100 um).

Reference only, never in the pixels: ref/jun/img/*.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess

import cv2
import numpy as np

import kit
import yohen
from glazekit import balls, close_shell
from kit import OUT, ROOT, blur, fbm, rank, shoot, sstep
from s06_flow import raster_tracks, simulate, track_paths
from vessel import Profile, fit_arc, reflect_light_loc, turned, view_dir

W = 5.2
DIST = 30.0
EL = 36.0
APEX = (0.5, 0.46)
APERTURE = 10.0  # mm. A wider one softens the window: the bowl images it about 3 cm in front of the wall, so its edge blurs by about aperture x 3 / distance.  The focus is a band of the wall
V_FOCUS = 0.5  # cm down from the lip
V_WIN = 0.5  # where the long window lies


def _wall(r0=5.86, z0=0.0, R=5.9, a0=np.radians(72.0), a1=np.radians(6.0), n=500):
    a = np.linspace(a0, a1, n)
    cx, cz = r0 - R * np.sin(a0), z0 + R * np.cos(a0)
    return list(zip(cx + R * np.sin(a), cz - R * np.cos(a)))


PROF = Profile([(4.9, -3.4), (5.82, -1.2), (6.02, -0.25), (6.06, -0.03), (6.03, 0.055), (5.95, 0.06), (5.88, 0.02)] + _wall(), sigma=0.022)
S_LIP = float(PROF.s[np.argmax(PROF.z)])
AZ = np.pi / 2
LU, V0, V1 = 9.0, -0.32, 4.2
SHADER = os.path.join(ROOT, "v2", "stills", "glaze_shader.py")
SHADER_GLAZE = os.path.join(ROOT, "v2", "stills", "s52_shader.py")  # glaze_shader's Fresnel goes to total reflection from inside past 42 degrees and blocks shadow rays: dark zones on the body (found on s52)
GLAZE = {"kind": "glaze", "ior": 1.5, "g": 0.45, "sigma_s": [7.0, 10.0, 14.0], "sigma_a": [1.4, 0.45, 0.4]}  # all estimates

# the brush, cm. One loaded stroke from the rim, with a turn, comes through the focus band left of centre; and a thinner one to the right
STROKES = [  # +u is to the left in the frame
    ([(-4.6, 0.32), (-3.0, 0.42), (-1.7, 0.42), (-0.8, 0.55), (-0.1, 0.92), (0.55, 1.28), (1.5, 1.55), (2.9, 2.0)], 0.19, 0.92),
    ([(1.6, 0.34), (2.4, 0.42), (3.4, 0.36), (4.6, 0.4)], 0.11, 0.6),
]
CRACK_SEED = 73
# the bowl turns on its axis, one way, evenly: the highlight stays and the glaze passes under it. 13 frames, 0.1 degree each = about 5 px a frame at 2560, slow enough for the film's optical flow. looks.json has no entry for this shot; it should have this when it goes in the film
MOVE = {"spin": {"pt": [0, 0, 0], "axis": [0, 0, 1], "deg": 1.2, "meshes": {"except": ["sky"]}}, "frames": 13, "res": [2560, 1440], "spp": 256, "shutter": 0.5}
DEVELOP = {"exposure": 0.45, "contrast": 1.35, "saturation": 1.08, "black": 0.002, "grain": 1.1, "sharpen": 0.25, "halation": 0.03, "vignette": 0.22}


def S(u, v, h=0.0):
    return turned(PROF, u, v + S_LIP, h, az=AZ)


def slope(v):
    """Sine of the wall's tilt, down along arc length."""
    _, _, nr, _ = PROF.at(np.maximum(v, 0.0) + S_LIP)
    return np.abs(nr)


def up(f, shape, sigma):
    """A field of the fixed grid brought to this quality, smoothly: cubic alone leaves ripples in a highlight."""
    g = cv2.resize(f.astype(np.float32), (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(g, (0, 0), max(sigma, 0.5))


def fields(dens):
    pxcm = 500.0 * dens
    nx, ny = int(LU * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M")
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - LU / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + V0
    U, V = np.meshgrid(u, v)

    h_, X_, Y_, load_ = simulate(slope, LU, V0, V1, STROKES, [])  # the flow's shape comes from the load; the tracks no longer open the simulated layer, so they leave no trace in the thickness
    k = pxcm / 100.0
    T = np.maximum(up(h_, shape, k), 0.004)
    X0, Y0 = up(X_, shape, k), up(Y_, shape, k)
    # back through the flow, on the raw layer: anything looked up here was laid before the firing and is now stretched along the run
    mx = (X0 + LU / 2) * pxcm - 0.5
    my = (Y0 - V0) * pxcm - 0.5

    def carried(f):
        return cv2.remap(f.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    # --- the tracks, read off the photographs: thin, wandering, broken, feathered. Hairs on Met 50.145.309 keep their red and lose about 12% of green and blue in sRGB; the Cleveland jar's wider streak measures Y 69 beside 89 (both measured, local means on the crops)
    hairs, bands = track_paths(LU, V0, V1, CRACK_SEED)
    edge_n = fbm(shape, pxcm, 0.012, 0.09, 2.2, 607)
    wh = carried(raster_tracks(hairs, LU, V0, V1, pxcm, 0.004))
    wb = carried(raster_tracks(bands, LU, V0, V1, pxcm, 0.03))
    wh = np.clip(wh * (1 + 0.5 * edge_n), 0, 1)
    wb = np.clip(wb * (1 + 0.7 * edge_n), 0, 1)
    wm = np.maximum(wh, 0.8 * wb)

    # --- copper: the load, carried, then a little diffusion. The edge is torn by the same grain that makes the lace
    load = up(load_, shape, k)  # already a function of where the glaze began, through the map below
    g0 = (int((V1 - V0) * 100.0), int(LU * 100.0))
    c = carried(cv2.resize(_c0(g0), (nx, ny), interpolation=cv2.INTER_CUBIC))
    c = 0.55 * blur(c, 0.035 * pxcm) + 0.45 * blur(c, 0.14 * pxcm)  # a core and a wide thin halo: copper diffuses further than the stroke was wide
    fine = rank(carried(fbm(shape, pxcm, 0.006, 0.05, 2.0, 605)))
    mids = rank(carried(fbm(shape, pxcm, 0.03, 0.26, 2.4, 604)))
    bigs = carried(fbm(shape, pxcm, 0.3, 2.0, 2.8, 603))
    tooth_c = rank(carried(fbm(shape, pxcm, 0.012, 0.06, 2.0, 626)))
    c = np.maximum(c * (1 + 0.42 * (mids - 0.5) + 0.2 * (fine - 0.5)) + 0.05 * (mids - 0.5) * sstep(0.0, 0.2, c), 0)
    c = c * sstep(0.012, 0.055, T)  # the copper thins out with the glaze at the lip
    Tcu = ramp(c)
    mask = sstep(0.06, 0.4, c)
    # crimson clots, where the copper reduced (the Cleveland jar's edge; 李媛 2013 fig. 3, JS-30): less green and blue passes there. Fed by the same grain as the lace, out of step with it
    clots = sstep(0.58, 0.86, 0.55 * tooth_c + 0.45 * mids) * mask
    Tcu = Tcu * (1 - clots[..., None] * np.array([0.0, 0.42, 0.34], np.float32))
    # a track is a warm filter, the same on blue and on purple: red stays, green and blue go down. Through this sheet twice: sRGB ratios about .88 on the hairs (Met), .8 on the streaks (Cleveland)
    Tcu = Tcu * (1 - wh[..., None] * np.array([0.06, 0.40, 0.34], np.float32)) * (1 - wb[..., None] * np.array([0.05, 0.26, 0.2], np.float32))
    tint_cu = np.clip(Tcu, 0.01, 1).astype(np.float32)

    # --- milk: thickness decides. Thin: transparent to the body. Thick: white
    opac = 1 - np.exp(-((T / 0.065) ** 1.7))
    cloud = rank(bigs)
    tooth = rank(carried(fbm(shape, pxcm, 0.014, 0.07, 2.0, 606)))  # clots about 0.2-0.4 mm across: 李媛 2013 fig. 3, x20, blue and white in clots, the track free of them
    milk_low = np.clip(opac * (0.76 + 0.2 * cloud), 0, 0.985) * (1 - 0.08 * wh)
    # a fine tooth everywhere, as on JS-29's blue and the Cleveland blue: pale specks in loose streaks. In the copper, a lace
    lace = sstep(0.7, 0.97, 0.75 * fine + 0.25 * mids)
    speck = sstep(0.58, 0.9, 0.7 * tooth + 0.3 * fine)
    milk_up = opac * (0.04 + 0.05 * cloud + 0.13 * speck * (1 - mask) * sstep(0.06, 0.11, T) + 0.34 * lace * mask * sstep(1.05, 0.35, c)) 
    milk_up = np.clip(milk_up, 0, 0.82) * (1 - 0.6 * wm)
    thick = sstep(0.05, 0.17, T)
    a, b = np.array([0.28, 0.62, 0.68], np.float32), np.array([0.58, 0.87, 0.84], np.float32)
    mcol_low = (a + (b - a) * (thick * (0.75 + 0.25 * cloud))[..., None]).astype(np.float32)
    mcol_up = np.broadcast_to(np.array([0.90, 0.95, 0.94], np.float32), shape + (3,))

    # --- surface: the flow's thickness is the shape. On it a low orange peel; a very fine tooth that breaks the highlight (the Cleveland jar's highlight is a scatter of points); pinholes
    peel = up(fbm((g0[0], g0[1]), 100.0, 0.22, 1.0, 3.0, 608), shape, k)
    # no even grain: a middle scale and a fine one, each only in patches, so parts of the glaze are plain glass
    patch = up(rank(fbm((g0[0], g0[1]), 100.0, 0.5, 2.5, 2.8, 628)), shape, k)
    patch2 = up(rank(fbm((g0[0], g0[1]), 100.0, 0.3, 1.4, 2.8, 629)), shape, k)
    peel_m = fbm(shape, pxcm, 0.05, 0.2, 2.6, 630) * sstep(0.45, 0.85, patch)
    tooth_h = fbm(shape, pxcm, 0.008, 0.035, 2.0, 609) * sstep(0.55, 0.95, patch2)
    rng = np.random.default_rng(610)
    drift = rank(bigs)
    n_pin = int(LU * (V1 - V0) * 24)
    px_, py_ = rng.integers(0, nx, n_pin), rng.integers(0, ny, n_pin)
    keep = rng.random(n_pin) < drift[py_, px_] ** 3
    px_, py_ = px_[keep], py_[keep]
    rad = np.clip(rng.pareto(2.6, len(px_)) * 0.002 + 0.001, 0.001, 0.011)
    hp = np.zeros(shape, np.float32)
    for x_, y_, r_ in zip(px_, py_, rad):
        rr = max(int(r_ * pxcm + 2), 2)
        y0_, y1_, x0_, x1_ = max(y_ - rr, 0), min(y_ + rr + 1, ny), max(x_ - rr, 0), min(x_ + rr + 1, nx)
        yy, xx = np.ogrid[y0_ - y_ : y1_ - y_, x0_ - x_ : x1_ - x_]
        hp[y0_:y1_, x0_:x1_] = np.maximum(hp[y0_:y1_, x0_:x1_], sstep(1.0, 0.45, np.sqrt(xx * xx + yy * yy) / max(r_ * pxcm, 0.7)))
    h_fine = 0.00022 * peel + 0.00002 * peel_m + 0.000004 * tooth_h - 0.003 * hp
    rough = 0.036 + 0.014 * rank(fbm(shape, pxcm, 0.3, 2.0, 2.8, 612)) + 0.2 * hp
    return dict(shape=shape, pxcm=pxcm, U=U, V=V, u=u, T=T, c=c, wm=wm, opac=opac, tint_cu=tint_cu, milk_low=milk_low.astype(np.float32), milk_up=milk_up.astype(np.float32), mcol_low=mcol_low, mcol_up=np.array(mcol_up), h_fine=h_fine.astype(np.float32), rough=np.clip(rough, 0.03, 0.6).astype(np.float32))


def _c0(g0):
    from s06_flow import stroke

    c = np.zeros(g0, np.float32)
    for i, (pts, width, gain) in enumerate(STROKES):
        c = np.maximum(c, gain * stroke(g0, pts, width, -LU / 2, V0, 100.0, 620 + 3 * i))
    return c


def ramp(c):
    """Transmission of the copper sheet by concentration, per channel. The light goes through twice, so these are square roots of what the eye sees over the milk."""
    knots = np.array([0.0, 0.05, 0.18, 0.4, 0.7, 1.0, 1.4], np.float32)
    tr = np.array([1.0, 1.0, 0.98, 0.90, 0.72, 0.58, 0.46], np.float32)
    tg = np.array([1.0, 0.86, 0.58, 0.42, 0.33, 0.30, 0.26], np.float32)
    tb = np.array([1.0, 0.97, 0.80, 0.68, 0.62, 0.60, 0.52], np.float32)
    return np.stack([np.interp(c, knots, t) for t in (tr, tg, tb)], -1).astype(np.float32)


def flat(F, d):
    """A quick composite, not a render: to judge the design, and to see that the flow did something."""
    body = np.array([0.20, 0.11, 0.065], np.float32)
    low = body + (F["mcol_low"] - body) * F["milk_low"][..., None]
    c = low * F["tint_cu"] ** 2
    c = c + (F["mcol_up"] - c) * F["milk_up"][..., None]
    gy, gx = np.gradient(F["T"] + F["h_fine"], 1.0 / F["pxcm"])
    shade = np.clip(1.0 + 2.6 * (gy * 0.7 - gx * 0.3), 0.4, 1.8)
    img = np.clip(c * shade[..., None], 0, 1) ** (1 / 2.2)
    # the frame's rough size on the wall, upper part
    px = F["pxcm"]
    y1 = int((2.6 + 0.32) * px)
    img = img[:y1]
    s = 2000.0 / img.shape[1]
    out = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(d, "cand_flat.jpg"), (out[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
    th = F["T"][:y1]
    cv2.imwrite(os.path.join(d, "cand_flat_thick.jpg"), cv2.resize((np.clip(th / 0.25, 0, 1) * 255).astype(np.uint8), None, fx=s, fy=s, interpolation=cv2.INTER_AREA))
    print("flat written; T percentiles", np.percentile(F["T"][int(0.32 * px) :], [1, 25, 50, 75, 99]).round(3))


def bubbles(seed=617):
    rng = np.random.default_rng(seed)
    n = int(LU * (V1 - V0) * 110)
    u = rng.uniform(-LU / 2, LU / 2, n).astype(np.float32)
    v = rng.uniform(0.25, V1, n).astype(np.float32)
    r = np.clip(rng.lognormal(np.log(0.0028), 0.5, n), 0.0012, 0.012).astype(np.float32)
    return u, v, r, rng


def build(F):
    T, U, V, u = F["T"], F["U"], F["V"], F["u"]
    shape, pxcm = F["shape"], F["pxcm"]
    ny, nx = shape
    wob = 0.0012 * up(fbm((int((V1 - V0) * 100), int(LU * 100)), 100.0, 0.6, 3.0, 3.0, 614), shape, pxcm / 100.0)
    # surface tension: the free surface is far smoother than the thickness below it, which is partly the body's own wobble and the flow's memory. Only its long swell and a little of the trough stay; at the full thickness field the slopes were 6 degrees and the window fell into islands
    Tlow = blur(T, 0.3 * pxcm)
    # the free surface's profile down the wall. A sqrt(v) thickness is convex and cancels the bowl's concavity, which turned the surface into a flat mirror and spread the window over the whole wall (seen in a preview); levelled glaze thickens quickly at the lip and then keeps to the wall. An estimate
    Tm = (0.012 + 0.085 * (1 - np.exp(-np.maximum(V, 0.0) / 0.14))).astype(np.float32)
    F["Tm"] = Tm[:, 0]
    Tg = Tm + 0.014 * (Tlow - blur(Tlow, 1.2 * pxcm)) + 0.0 * (T - Tlow) - 0.0003 * blur(F["wm"], 0.02 * pxcm)  # the geometric thickness; T keeps the colour, as the optical path through the milk it had when it flowed
    top = S(U, V, wob + Tg + F["h_fine"])
    m = max(ny // 24, 8)
    vb = np.linspace(V0, V1, m, dtype=np.float32)
    Ub, Vb = np.meshgrid(u, vb)
    rs = lambda f, n=nx, mm=m: cv2.resize(f, (n, mm), interpolation=cv2.INTER_AREA)  # noqa: E731
    bot = S(Ub, Vb, rs(wob) - 0.35 * rs(Tg) - 0.01)
    Pg, at = close_shell(top, bot, {"rough": F["rough"]}, {"rough": 0.3}, outward=np.array([0.0, -0.75, 0.65]))

    sub = lambda f: cv2.resize(f, (nx // 2, ny // 2), interpolation=cv2.INTER_AREA)  # noqa: E731
    Us, Vs, ws, ts, fs = sub(U), sub(V), sub(wob), sub(Tg), sub(F["h_fine"])
    und = sub(up(fbm((int((V1 - V0) * 100), int(LU * 100)), 100.0, 0.3, 1.6, 3.0, 615), shape, pxcm / 100.0))

    def sheet(frac):  # noqa: E306
        f = frac + min(0.06, 0.25 * frac) * und
        return S(Us, Vs, ws + fs + ts * (1 - f))

    white = np.ones(Us.shape + (3,), np.float32)
    layers = {
        "up": (sheet(0.05), white, sub(F["milk_up"]), sub(F["mcol_up"])),
        "cu": (sheet(0.11), sub(F["tint_cu"]), np.zeros(Us.shape, np.float32), white),
        "low": (sheet(0.72), white, sub(F["milk_low"]), sub(F["mcol_low"])),
    }
    # the body: iron-rich, seen only where the glaze has run thin
    bm, nb = max(ny // 3, 32), max(nx // 3, 32)
    ub = np.linspace(-LU / 2, LU / 2, nb, dtype=np.float32)
    vbb = np.linspace(V0, V1, bm, dtype=np.float32)
    Ubb, Vbb = np.meshgrid(ub, vbb)
    Pb = S(Ubb, Vbb, cv2.resize(wob, (nb, bm), interpolation=cv2.INTER_AREA))
    var = 1.0 + 0.2 * fbm((bm, nb), nb / LU, 0.02, 0.3, 2.2, 616)
    Cb = np.stack([0.24 * var, 0.125 * var, 0.07 * var], -1).astype(np.float32)
    # bubbles in the glaze, at random depth, where they fit
    bu, bv, br, rng = bubbles()
    tv = cv2.remap(T, ((bu + LU / 2) * pxcm).astype(np.float32), ((bv - V0) * pxcm).astype(np.float32), cv2.INTER_LINEAR).ravel()
    frac = np.clip(0.12 + 0.55 * (br / 0.01) * rng.random(len(bu)) + 0.2 * rng.random(len(bu)), 0.08, 0.85)
    keep = tv * frac > br + 0.002
    Pc = balls(S(bu[keep], bv[keep], (tv * (1 - frac))[keep]), br[keep], nlon=10, nlat=7)
    return Pg, at["rough"], Pb, Cb, layers, Pc


def deliver():
    from darkroom import develop as dev, save_png

    src = os.path.join(OUT, "s06_junyao_cand_move_final")
    dst = os.path.join(OUT, "s06_junyao_take_cand")
    os.makedirs(dst, exist_ok=True)
    fs = sorted(f for f in os.listdir(src) if f.endswith(".npy"))
    for i, f in enumerate(fs):
        img = dev(np.load(os.path.join(src, f)).astype(np.float32), **{**DEVELOP, "seed": i + 1})
        save_png(os.path.join(dst, f"f{i:03d}.png"), img)
        cv2.imwrite(os.path.join(dst, f"f{i:03d}.jpg"), (img * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-r", "25", "-i", os.path.join(dst, "f%03d.jpg"), "-vf", "format=yuv420p", "-crf", "16", os.path.join(dst, "take.mp4")])
    print(dst, len(fs))


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "deliver":
        return deliver()
    d = os.path.join(OUT, "s06_junyao")
    os.makedirs(d, exist_ok=True)
    kit.looks = lambda: {"s06_junyao_cand": {"move": MOVE}}
    if q == "flat":
        return flat(fields(0.5), d)
    tag = q
    if q == "cand":  # final size, beside the final: the film reads final.*
        q = "final"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    uu, vv = np.linspace(-7, 7, 300, dtype=np.float32), np.linspace(V0, 3, 200, dtype=np.float32)
    Pc = S(*np.meshgrid(uu, vv))
    view = view_dir(-90.0, EL)
    focus = S(np.array([-0.3], np.float32), np.array([V_FOCUS], np.float32), 0.09)[0]
    cam, sag = fit_arc(Pc, view, W, DIST, apex=APEX, target0=(0, 6, 0), aperture_mm=APERTURE, focus_point=focus)

    F = fields(dens)
    Pg, Rg, Pb, Cb, layers, Pbub = build(F)
    fs = {}

    def save(name, **kw):  # noqa: E306
        fs[name] = os.path.join(d, f"mesh.{name}.{q}.npz")
        np.savez(fs[name], **kw)

    save("glaze", P=Pg, rough=Rg)
    save("body", P=Pb, col=Cb)
    save("bubble", P=Pbub)
    meshes = [
        {"name": "glaze", "npz": fs["glaze"], "shader_py": SHADER_GLAZE, "params": GLAZE},
        {"name": "body", "npz": fs["body"], "material": {"Base Color": "col", "Roughness": 0.75, "Specular IOR Level": 0.2}},
        {"name": "bubble", "npz": fs["bubble"], "shader_py": SHADER, "params": {"kind": "bubble"}},
    ]
    for k, (P, tint, milk, mcol) in layers.items():
        save("l" + k, P=P, tint=tint, milk=milk, mcol=mcol)
        meshes.append({"name": "l" + k, "npz": fs["l" + k], "shader_py": SHADER, "params": {"kind": "layer"}})

    # the long window: a real horizontal bank of panes in the room, mirrored in the wall at V_WIN. It follows the rim because the bowl is a surface of revolution
    vv_ = np.array([V_WIN - 0.03, V_WIN, V_WIN + 0.03], np.float32)
    tm = np.interp(vv_, F["V"][:, 0], F["Tm"]).astype(np.float32)
    q_ = S(np.zeros(3, np.float32), vv_, tm)
    pt = q_[1]
    tan = (q_[2] - q_[0]) / np.linalg.norm(q_[2] - q_[0])
    nrm = np.array([0.0, -tan[2], tan[1]])  # in the y-z plane, turned towards the inside of the bowl
    if nrm[1] > 0:
        nrm = -nrm
    lw, rdir = reflect_light_loc(pt, nrm, cam, 60.0)
    print("window dir", rdir, "at", lw)
    yohen.use_room()
    env = {
        "base": [0.03, 0.03, 0.032],
        "panels": [
            {"dir": rdir.tolist(), "w": 62, "h": 0.6, "L": 4.5, "rgb": [1.0, 0.985, 0.96], "soft": 0.5, "soft_w": 5.0, "grad": 0.15},
            # the room's dim rest of the wall above the window, a slow gradient on the glass below the band
            {"dir": (rdir + np.array([0, 0, -0.45])).tolist(), "w": 75, "h": 18, "L": 0.14, "rgb": [0.96, 0.98, 1.0], "soft": 12.0, "soft_w": 20.0},
        ],
    }
    A = S(np.array([0.0], np.float32), np.array([0.0], np.float32))[0]
    lights = [
        # the milk's light: a big soft source high and to the left, not seen in the gloss; it gives the wall its turn from pale to deep
        {"name": "fill", "loc": (A + np.array([-52, -30, 48])).tolist(), "target": (A + np.array([-1.0, 0.0, -1.5])).tolist(), "size": [55, 55], "watts": 42000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
        # a low lamp from behind the far rim's left: rakes the lip
        {"name": "lip", "loc": (A + np.array([-26, 24, 10])).tolist(), "target": A.tolist(), "size": [24, 1.5], "watts": 420, "rgb": [1.0, 0.93, 0.86]},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "env": env,
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "bounces": 64,
        "volume_bounces": 48,
        "transmission_bounces": 64,
        "diffuse_bounces": 6,
        "glossy_bounces": 6,
        "spp": {"preview": 96, "mid": 192, "final": 640},
    }
    shoot("s06_junyao_cand" if os.environ.get("GEWU_MOVE") else "s06_junyao", scene, q, tag=tag, develop=DEVELOP)


main()
