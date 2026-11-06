"""Shot 70: tea spreading in a clean white bowl, from low down and lit from behind. Replaces s68_chase (white cup, clear water, tea composited over a plate: read as ink, then as a stained plate; IMAGERY.md).

    python3 -I v2/stills/s70_chatang.py look TAG k=v,k=v|@file.json [preview|mid|final]     out/v2/s70_chatang/TAG.jpg
    python3 -I v2/stills/s70_chatang.py take k=v|@file.json QUALITY FIRST N                 out/v2/s70_chatang_take_QUALITY/; at final also s70_chatang_move_final/

What the picture is made of, all real light in Cycles but for the one stand-in below:
- the bowl, conical as a douli zhan, its far wall facing the lens. Clean and whole: its detail is glaze depth, fine throwing rings that break the edge of a reflection, the wall's thinness;
- a real liquor, a pure absorber, so the colour is the depth: pale gold at the water line, amber towards the well, seen through to the rings on the glaze;
- the tea, a VDB from s70_flow.py, a pure absorber in the same units;
- the far wall upside down in the water: at 18 degrees the surface mirrors about 13%, and the water line is where the thing meets its image;
- a window in the wet glaze. It is in the room that only reflections see.

Stand-in: the light through the wall, through(), is computed per vertex and emitted, not scattered through the body. The swell of the water is two drifting noise fields, not a solved free surface.

Sizes, all estimates: bowl 12 cm across, 4.5 cm deep. Water: capillary length 0.257 cm, contact angle on glaze 30 degrees (estimates, as in s68_geom); on a wall leaning at beta from the horizontal the surface rises at beta - theta, and only about 0.09 cm.
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit

NAME = "s70_chatang"
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(kit.OUT, NAME)
SHP = os.path.join(HERE, "s70_shader.py")

R_RIM = 6.0
BOWL_D = 4.47
BOWL_P = 1.6
LC = 0.257
THETA_C = np.radians(30.0)
N_WATER = 1.33
SIGMA = [1.0, 2.3, 8.0]  # relative absorption, r g b: the ratio read from ref/tea_plume/01 (g/r about 2.1, b/r about 8) and the black tea spectrum in s68_tea (2.7, 8)

P0 = dict(
    z_rim=0.45,  # rim above the still water. From 52 degrees a dry band at 0.38 was a wide flat ring and the bowl read as an ashtray; from low down it is the wall that the water mirrors
    # Why low: straight down the water does not show at all, at 52 degrees it mirrors only 2.4% and the frame holds a wedge under 1.1 cm deep. Fresnel climbs towards grazing (about 6% at 30 degrees, 13% at 20), so the far wall and the lip stand in the water upside down, and the water line is where the thing meets its image
    E=18.0,
    W=8.2,  # the mirror band closes to a point about 4.3 cm off axis (perspective); wider and that tip stands in the frame as a white tongue
    dist=30.0,
    apex_y=0.48,
    aperture=2.5,
    focus_r=5.65,  # radius on the far wall where the focal plane passes: a little under the water, where the tea is. None: the water line
    liquor=0.07,  # absorption of the liquor in the red, per cm
    # A tea drinker's bowl is clean and whole: no chip, no stain, no pinhole. Its detail is what a good bowl does with light: glaze depth, the wall's thinness, the shape of a reflection
    body=[0.93, 0.91, 0.86],  # the porcelain under the glaze
    glaze_sigma=[0.06, 0.045, 0.04],  # absorption of the glaze per unit of nominal thickness: colour is depth, by Beer-Lambert. Estimated by eye, no measured glaze. Nearly white: amber over a bluish glaze came out mustard, and tea people judge a liquor in white porcelain for that reason
    ring_h=0.0003,  # throwing rings left in the surface, cm: glaze levels over them
    ring_depth=0.15,  # and what they do to its depth, as a fraction: the colour keeps what the surface lost
    # light through the wall (see through()), from a soft source behind the bowl
    glow=0.85,
    glow_rgb=[1.0, 0.95, 0.86],  # porcelain passes warm
    glow_x=0.6,  # centre of the pool of light on the wall, cm along the arc from the crown, + is frame right
    glow_w=2.9,
    wall_lip=0.03,  # wall thickness, cm: thin at the lip
    wall_grow=0.25,  # and how much thicker by 2.5 cm in from it
    # marks the potter meant, both off by default: see marks()
    xian=[],  # bowstring lines (xianwen): distance along the wall from the lip, cm
    ribs=0,  # raised lines down the wall (chujin), count round the bowl
    rib_x=-1.6,  # where one of them is, cm along the arc from the crown
    # what the flat water mirrors: a broad, faint, warm sheet with one slanting edge. The eye takes it as a surface because it stays while the tea moves under it. Neutral light lifts the blue over the tea and the filaments go mauve; a small shape reads as a card stuck on; a thin line reads as another ridge
    win_L=0.0,  # off from low down: the far wall's own image does this work
    win_cx=-9.0,  # degrees from the mirror direction: +x right in the frame, +y down
    win_cy=3.0,
    win_wx=8.0,
    win_wy=8.0,
    win_tilt=-35.0,
    win_bar=99.0,  # where a mullion is, degrees from the window's centre
    win_soft=0.05,  # width of the pane's edge, as a fraction of its half width
    win_fade=6.0,  # its far edge fades: the meniscus tilts through all of it, and a hard edge is drawn as rings parallel to the rim
    win_rgb=[1.0, 0.78, 0.42],
    win_shape="rect",  # or "round": centre win_cx, win_cy and radius win_wx
    line_L=0.0,  # off: from low down its edges show as a slab in the water. High over the water, seen only in the steep part of the meniscus: the bright thin water line of ref/tea_plume/05
    line_y0=36.0,
    line_y1=56.0,
    slit_L=0.0,  # a strip light, off by default. y below about 2.2 degrees it is not mirrored at all, at 2.2 a blob, beyond that a closed loop: view angle and meniscus slope together have a minimum there
    slit_y=1.4,
    slit_w=0.3,
    slit_tilt=-3.0,
    slit_x=0.0,
    slit_len=26.0,
    swell=0.0012,  # height of the slow unevenness of the water, cm
    swell_t=0.0,  # time, s: it drifts
    # Both lights from behind and above: the far wall above the water turns away from them and has only what comes through it, so it reads as thin porcelain and not as a white tub, while the well takes them full on and the liquor glows. Lit from the front the same wall was flat grey.
    # The key is smaller, so the tea throws a shadow on the glaze, apart from itself: that gap is what says it hangs in water
    key=[-30.0, 25.0, 35.0],
    key_size=12.0,
    key_W=6000.0,
    key_rgb=[1.0, 0.97, 0.92],
    fill_W=22000.0,
    fill_loc=[0.0, 35.0, 50.0],
    exposure=0.0,
    room_ceil=0.22,  # the room, seen in reflections only. Keep it dark: this low the water mirrors 10% of it, and at 0.5 the whole surface went milky and the tea grey
    room_wall=0.044,
    sheen=14.0,  # bright, far brighter than the wall: at about 5% reflectance on a wall this light, anything less cannot be seen, and it is the sharp edge that says glass
    sheen_bars=0.0,  # 1: window bars. Clean glaze with a bar across its window reads as a smudge
    sheen_az=39.0,  # azimuth from straight behind the camera, degrees: left in the frame, against the heavy tea at lower right
    sheen_el=70.0,
    sheen_waz=8.0,  # half widths
    sheen_wel=18.0,
    sheen_soft=0.9,  # where its edge starts to fall, as a fraction of the half width
    bubbles=0,  # off: the few that show read as specks on a clean bowl
    foam=0,  # off: in a dark room a bubble's skin mirrors black and its edge is a dark claw. bubbles floating on the surface, gathered at the wall by the meniscus
    spp=None,
    dev={},
    tea=None,  # the cloud: name of a solve in out/v2/s70_sim
    tea_t=None,  # its time, as in the file names: "012.000"
    tea_K=2.5,  # absorption of undiluted tea in the red, per cm
)


def zprof(r, o):
    return o["z_rim"] - BOWL_D * (1.0 - np.clip(r / R_RIM, 0.0, 1.0) ** BOWL_P)


def slope(r):
    return BOWL_D * BOWL_P / R_RIM * np.clip(r / R_RIM, 1e-4, 1.0) ** (BOWL_P - 1.0)


def r_of_z(z, o):
    return R_RIM * np.clip(1.0 - (o["z_rim"] - z) / BOWL_D, 0.0, 1.0) ** (1.0 / BOWL_P)


# --- the hand of the potter: slow, shared by everything that follows the wall -------------------
_TH = np.linspace(0, 2 * np.pi, 4096)
_arcf = lambda lo, hi, beta, seed: kit.fbm((1, 4096), 4096 / (2 * np.pi), lo, hi, beta, seed)[0]
_RIM_H = 0.004 * _arcf(0.5, 3.0, 2.8, 701) + 0.0005 * _arcf(0.05, 0.25, 2.0, 702)
_LIP_T = 1.0 + 0.12 * _arcf(0.08, 0.8, 2.2, 703)


def wob(th):
    return 0.012 * np.cos(2 * th + 0.8) + 0.007 * np.cos(3 * th - 1.1) + 0.003 * np.cos(5 * th + 2.0)


def rim_h(th):
    return np.interp(np.mod(th, 2 * np.pi), _TH, _RIM_H)


def thetas(q):
    """Fine over the far wall that the frame sees, coarse round the rest. The seam is on the near side."""
    a = np.radians(52.0)
    n = int(2 * a * R_RIM * {"preview": 70, "mid": 130, "final": 260}[q])
    th = np.linspace(-a, a, n)
    rest = np.linspace(a, 2 * np.pi - a, 202)[1:-1]
    return np.concatenate([th, rest, [2 * np.pi - a]]) + np.pi / 2


def relief(q):
    """Throwing rings and the glaze's slow orange peel, unit variance, on a map in (s along the wall from the rim, x round the wall), both cm. Rings spiral slowly."""
    px = {"preview": 60, "mid": 110, "final": 220}[q]
    ns, nx = int(7.5 * px), int(13.0 * px)
    r1 = kit.fbm((1, ns), px, 0.05, 0.3, 1.6, 705)[0]  # finger and tool width, fine: broad ones read as clouds in the wall
    S, X = np.meshgrid(np.arange(ns) / px, np.arange(nx) / px - 6.5, indexing="ij")
    zq = S + 0.05 * np.sin(X * 0.45 + 0.7) + 0.03 * cv2.resize(kit.fbm((64, 256), 256 / 13.0, 1.0, 8.0, 2.6, 706), (nx, ns), interpolation=cv2.INTER_CUBIC)
    return np.interp(zq, np.arange(ns) / px, r1).astype(np.float32), kit.fbm((ns, nx), px, 0.25, 1.6, 2.6, 707).astype(np.float32), px


def sample_map(M, px, s, x):
    return cv2.remap(M, (x + 6.5).astype(np.float32) * px, s.astype(np.float32) * px, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def contact(o):
    """Height and radius where the water meets the wall (radius before the wobble)."""
    z = 0.09
    for _ in range(4):
        rc = r_of_z(z, o)
        beta = np.arctan(slope(rc))
        z = 2 * LC * np.sin(max(beta - THETA_C, 0.0) / 2)
    return z, r_of_z(z, o)


def meniscus(d, h0):
    h = np.geomspace(h0, 0.0008, 800)
    x = LC * (np.arccosh(2.0 * LC / h) - np.sqrt(np.maximum(4.0 - (h / LC) ** 2, 0.0)))
    x = x - x[0]
    dd = np.maximum(d, 0.0)
    out = np.exp(np.interp(dd, x, np.log(h)))
    return np.where(dd > x[-1], h[-1] * np.exp(-(dd - x[-1]) / LC), out)


def marks(T, s, Rb, o):
    """What the potter cut on purpose, both on Song qingbai bowls (from memory, not looked up for this): `groove`, 1 in a bowstring line turned on the wheel; `rib`, 1 on a raised line running down the wall. Glaze pools in the first and thins over the second."""
    groove = np.zeros_like(Rb, dtype=np.float32)
    for s0 in o["xian"]:
        groove = np.maximum(groove, np.exp(-(((s - s0) / 0.014) ** 2)))
    rib = np.zeros_like(Rb, dtype=np.float32)
    for k in range(int(o["ribs"])):
        a = np.pi / 2 + o["rib_x"] / R_RIM + k * 2 * np.pi / o["ribs"]
        dist = (np.mod(T - a + np.pi, 2 * np.pi) - np.pi) * Rb
        rib = np.maximum(rib, np.exp(-((dist / 0.032) ** 2)))
    rib = rib * kit.sstep(0.04, 0.3, s) * kit.sstep(1.2, 2.4, Rb)
    return groove.astype(np.float32), rib.astype(np.float32)


def through(o, x, wall, tg):
    """Light through a thin wall, held up to a window: the reason a potter can check a wall's thickness by eye. A stand-in, not a scattering solve: a thin sheet lit from behind, passing exp(-thickness / length) with red going furthest (lengths estimated), once through the glaze. 1 at the lip, about half by 5 cm from the axis, so it dies out as the wall thickens under the water. Radiance."""
    g = np.array(o["glaze_sigma"], np.float32)
    ell = np.array([0.085, 0.07, 0.055], np.float32)
    pool = np.exp(-0.5 * ((x - o["glow_x"]) / o["glow_w"]) ** 2)
    return (o["glow"] * np.array(o["glow_rgb"], np.float32) * pool[..., None] * np.exp(-np.maximum(wall - o["wall_lip"], 0.0)[..., None] / ell) * np.exp(-g * 0.6 * tg[..., None])).astype(np.float32)


def build_bowl(wet_path, dry_path, o, q):
    th = thetas(q)
    h0, rc = contact(o)
    dens = {"preview": 70, "mid": 130, "final": 260}[q]
    Mr, Mp, px = relief(q)
    r_in = np.concatenate([np.linspace(0.02, 1.8, 24)[:-1], np.linspace(1.8, R_RIM, int(4.2 * dens))])
    # split at the contact line
    i = int(np.searchsorted(r_in, rc))
    r_in = np.concatenate([r_in[:i], [rc], r_in[i:]])
    T, Rb = np.meshgrid(th, r_in)
    Z = zprof(Rb, o)
    b = slope(Rb)
    nr, nz = -b / np.sqrt(1 + b * b), 1.0 / np.sqrt(1 + b * b)
    s = (R_RIM - Rb) * np.sqrt(1 + slope(0.5 * (Rb + R_RIM)) ** 2)  # along the wall from the rim, near enough
    x = (np.mod(T - np.pi / 2 + np.pi, 2 * np.pi) - np.pi) * R_RIM
    fade = kit.sstep(0.6, 2.0, Rb) * kit.sstep(0.0, 0.12, s) * kit.sstep(6.2, 5.6, np.abs(x))  # the lip keeps its true round; the middle of the bowl has no marks
    rings = sample_map(Mr, px, s, x) * fade
    groove, rib = marks(T, s, Rb, o)
    h = o["ring_h"] * rings + 0.0005 * sample_map(Mp, px, s, x) * fade - 0.003 * groove + 0.009 * rib
    w = wob(T) * kit.sstep(1.0, 3.0, Rb)
    R = Rb + w + h * nr
    Zz = Z + h * nz + rim_h(T) * kit.sstep(3.0, R_RIM, Rb)
    P = np.stack([R * np.cos(T), R * np.sin(T), Zz], -1).astype(np.float32)
    # glaze depth, in units of its nominal thickness: thin as it runs off the lip, thicker down the wall, pooled towards the well, deeper in a ring's groove and a cut line, thin over a rib
    tg = (0.3 + 0.7 * kit.sstep(0.0, 0.3, s)) * (1.0 + 0.9 * kit.sstep(5.8, 2.5, Rb)) * (1.0 - o["ring_depth"] * rings) + 0.9 * groove - 0.6 * rib
    tg = np.maximum(tg, 0.12).astype(np.float32)
    bodyc = np.array(o["body"], np.float32)
    sig = np.array(o["glaze_sigma"], np.float32)
    col = (bodyc * np.exp(-sig * tg[..., None])).astype(np.float32)
    rough = np.full(T.shape, 0.045, np.float32)
    # the wall: a thin lip thickening towards the foot, as the outside below is cut
    wall = o["wall_lip"] + o["wall_grow"] * np.clip((R_RIM - Rb) / 2.5, 0.0, 1.0) ** 0.8 + 0.003 * rings - 0.008 * groove + 0.014 * rib
    glow = through(o, x, wall, tg)
    np.savez(wet_path, P=P[: i + 1], col=col[: i + 1], rough=rough[: i + 1], glow=glow[: i + 1])
    # the dry part, the lip and the outside
    a = np.linspace(-np.pi / 2, np.pi / 2, 20)[1:-1]
    Tl, Al = np.meshgrid(th, a)
    t_lip = 0.045 * np.interp(np.mod(Tl, 2 * np.pi), _TH, _LIP_T)
    r_a = R_RIM + wob(Tl)
    Rl = r_a + t_lip / 2 + t_lip / 2 * np.sin(Al)
    Zl = o["z_rim"] + rim_h(Tl) + t_lip / 2 * np.cos(Al)
    r_o = np.linspace(R_RIM, 1.4, 60)
    To, Ro = np.meshgrid(th, r_o)
    t = 0.045 + 0.20 * kit.sstep(R_RIM, 3.5, Ro)
    Zo = zprof(Ro, o) - t * 1.1 + rim_h(To) * kit.sstep(3.0, R_RIM, Ro)
    Ro_ = Ro + wob(To) * kit.sstep(1.0, 3.0, Ro) + 0.045 * kit.sstep(3.0, R_RIM, Ro)
    Zo = Zo + 1.1 * 0.045 * kit.sstep(R_RIM - 0.4, R_RIM, Ro)
    xl = (np.mod(Tl - np.pi / 2 + np.pi, 2 * np.pi) - np.pi) * R_RIM
    tl = np.full(Tl.shape, 0.3, np.float32)  # the glaze is at its thinnest going over the lip, and the body nearly shows
    cl = (bodyc * np.exp(-sig * tl[..., None])).astype(np.float32)
    co = (bodyc * np.exp(-sig))[None, None] * np.ones(To.shape + (1,), np.float32)
    Pd = np.concatenate([P[i:], np.stack([Rl * np.cos(Tl), Rl * np.sin(Tl), Zl], -1).astype(np.float32), np.stack([Ro_ * np.cos(To), Ro_ * np.sin(To), Zo], -1).astype(np.float32)])
    Cd = np.concatenate([col[i:], cl, co]).astype(np.float32)
    Rd = np.concatenate([rough[i:], np.full(Tl.shape, 0.05, np.float32), np.full(To.shape, 0.06, np.float32)])
    Gd = np.concatenate([glow[i:], through(o, xl, np.full(Tl.shape, o["wall_lip"], np.float32), tl), np.zeros(To.shape + (3,), np.float32)])
    np.savez(dry_path, P=Pd, col=Cd, rough=Rd, glow=Gd)
    print(f"[bowl] wet {P[: i + 1].shape[:2]}, dry {Pd.shape[:2]}; contact z {h0:.3f}, r {rc:.3f}", flush=True)


def build_water(path, o, q):
    """Closed: the surface from the middle out, into the wall by a hair, then back under the glaze, where no ray reaches. A medium needs a closed mesh (SHOTS.md)."""
    th = thetas(q)
    h0, rc = contact(o)
    k = {"preview": 1.0, "mid": 0.5, "final": 0.25}[q]
    d = np.concatenate([np.linspace(rc - 0.02, 1.2, 50)[:-1], np.linspace(1.2, 0.25, int(40 / k))[:-1], np.geomspace(0.25, 0.0012, int(70 / k)), [-0.012]])
    T, Dd = np.meshgrid(th, d)
    rcw = rc + wob(T) * kit.sstep(1.0, 3.0, rc)
    r = np.maximum(rcw - Dd, 0.005)
    h = meniscus(Dd, h0)
    x, y = r * np.cos(T), r * np.sin(T)
    # a stand-in for the slow surface left by the pour: two fields drifting across each other, not a solved free surface
    t = o["swell_t"]
    swell = 0.0
    for sd, vx, vy in ((708, 0.22, 0.08), (709, -0.14, 0.17)):
        sw = kit.fbm((512, 512), 512 / 14.0, 0.7, 6.0, 3.0, sd)
        swell = swell + 0.7 * cv2.remap(sw, np.mod((x - vx * t + 7) / 14 * 511, 511).astype(np.float32), np.mod((y - vy * t + 7) / 14 * 511, 511).astype(np.float32), cv2.INTER_CUBIC)
    z = h + o["swell"] * swell * kit.sstep(0.0, 0.3, Dd)
    top = np.stack([x, y, z], -1)
    # back under the glaze
    r2 = np.linspace(rc + 0.012, 0.02, 40)
    T2, R2 = np.meshgrid(th, r2)
    bot = np.stack([(R2 + wob(T2) * kit.sstep(1.0, 3.0, R2)) * np.cos(T2), (R2 + wob(T2) * kit.sstep(1.0, 3.0, R2)) * np.sin(T2), zprof(R2, o) - 0.02], -1)
    np.savez(path, P=np.concatenate([top, bot]).astype(np.float32))
    print(f"[water] {top.shape[0] + bot.shape[0]} x {top.shape[1]}", flush=True)


def bubbles(path, o):
    """Air coming out of just-poured hot water, caught on the glaze under the water line: tight clumps along the line, a few strays lower down. Sizes lognormal. V, F soup as in s68_chase."""
    rng = np.random.default_rng(71)
    n = int(o["bubbles"])
    h0, rc = contact(o)
    clumps = rng.uniform(np.pi / 2 - 0.85, np.pi / 2 + 0.85, 26)
    weight = rng.lognormal(0, 0.8, 26)
    c = rng.choice(26, n, p=weight / weight.sum())
    th = clumps[c] + rng.normal(0, 0.035, n)
    d = 0.015 + rng.exponential(0.055, n)
    stray = rng.random(n) < 0.05
    th[stray] = rng.uniform(np.pi / 2 - 0.85, np.pi / 2 + 0.85, stray.sum())
    d[stray] = rng.uniform(0.1, 1.3, stray.sum())
    rad = np.clip(rng.lognormal(np.log(0.010), 0.45, n), 0.004, 0.03)
    rad[stray] = np.minimum(rad[stray], 0.012)
    r_w = rc - d + wob(th) * kit.sstep(1.0, 3.0, rc - d)
    z = zprof(rc - d, o)
    b = slope(rc - d)
    nr, nz = -b / np.sqrt(1 + b * b), 1.0 / np.sqrt(1 + b * b)
    R = r_w + nr * rad * 0.9
    Z = np.minimum(z + nz * rad * 0.9, -rad * 1.05)
    nu, nv = 18, 12
    a = np.pi * np.arange(nv + 1) / nv
    t = 2 * np.pi * np.arange(nu) / nu
    A, T = np.meshgrid(a, t, indexing="ij")
    U = np.stack([np.sin(A) * np.cos(T), np.sin(A) * np.sin(T), np.cos(A)], -1).reshape(-1, 3)
    m = (nv + 1) * nu
    i, j = np.meshgrid(np.arange(nv), np.arange(nu), indexing="ij")
    p0, q0, s0, t0 = i * nu + j, i * nu + (j + 1) % nu, (i + 1) * nu + (j + 1) % nu, (i + 1) * nu + j
    F0 = np.concatenate([np.stack([p0, s0, q0], -1).reshape(-1, 3), np.stack([p0, t0, s0], -1).reshape(-1, 3)])
    C = np.stack([R * np.cos(th), R * np.sin(th), Z], -1)
    V = (C[:, None] + rad[:, None, None] * U[None]).reshape(-1, 3)
    F = (F0[None] + (np.arange(n) * m)[:, None, None]).reshape(-1, 3)
    np.savez(path, V=V.astype(np.float32), F=F.astype(np.int32))
    print(f"[bubbles] {n}", flush=True)


def foam(path, o):
    """Bubbles afloat: domes of thin film standing on the water, clumped at the wall (a meniscus draws them in, the Cheerios effect). Only the cap above the water is modelled; the shallow dimple below it is left out."""
    rng = np.random.default_rng(72)
    n = int(o["foam"])
    h0, rc = contact(o)
    k = 9
    clumps = rng.uniform(np.pi / 2 - 0.8, np.pi / 2 + 0.8, k)
    weight = rng.lognormal(0, 0.9, k)
    c = rng.choice(k, n, p=weight / weight.sum())
    th = clumps[c] + rng.normal(0, 0.05, n)
    rad = np.clip(rng.lognormal(np.log(0.015), 0.45, n), 0.006, 0.045)
    d = rad + 0.02 + rng.exponential(0.10, n)
    r = rc - d + wob(th) * kit.sstep(1.0, 3.0, rc)
    z0 = meniscus(d, h0)
    nu, nv = 24, 10
    a = np.radians(82.0) * np.arange(nv + 1) / nv
    t = 2 * np.pi * np.arange(nu) / nu
    A, T = np.meshgrid(a, t, indexing="ij")
    U = np.stack([np.sin(A) * np.cos(T), np.sin(A) * np.sin(T), 0.8 * np.cos(A)], -1).reshape(-1, 3)
    m = (nv + 1) * nu
    i, j = np.meshgrid(np.arange(nv), np.arange(nu), indexing="ij")
    p0, q0, s0, t0 = i * nu + j, i * nu + (j + 1) % nu, (i + 1) * nu + (j + 1) % nu, (i + 1) * nu + j
    F0 = np.concatenate([np.stack([p0, s0, q0], -1).reshape(-1, 3), np.stack([p0, t0, s0], -1).reshape(-1, 3)])
    C = np.stack([r * np.cos(th), r * np.sin(th), z0], -1)
    V = (C[:, None] + rad[:, None, None] * U[None]).reshape(-1, 3)
    F = (F0[None] + (np.arange(n) * m)[:, None, None]).reshape(-1, 3)
    np.savez(path, V=V.astype(np.float32), F=F.astype(np.int32))
    print(f"[foam] {n}", flush=True)


def slit_mesh(path, cam, o):
    """A long thin emitter far off along the mirror direction, a grid so that its brightness can fall away towards the ends. Emission per vertex, in `col`."""
    loc, tgt = np.array(cam["loc"], float), np.array(cam["target"], float)
    v = (tgt - loc) / np.linalg.norm(tgt - loc)
    mirror = np.array([v[0], v[1], -v[2]])
    e1 = np.array([1.0, 0.0, 0.0])
    e2 = np.cross(mirror, e1)
    e2 = e2 / np.linalg.norm(e2)
    if e2[2] < 0:
        e2 = -e2
    a = np.radians(o["slit_tilt"])
    ax, ay = np.cos(a) * e1 + np.sin(a) * e2, -np.sin(a) * e1 + np.cos(a) * e2
    D = 300.0
    t = np.linspace(-1.0, 1.0, 81)
    q = np.linspace(-1.0, 1.0, 9)
    T, Q = np.meshgrid(t, q)
    c = tgt + D * (mirror + np.tan(np.radians(o["slit_y"])) * e2 + np.tan(np.radians(o["slit_x"])) * e1)
    P = c + (D * np.tan(np.radians(o["slit_len"])) * T)[..., None] * ax + (D * np.tan(np.radians(o["slit_w"] / 2)) * Q)[..., None] * ay
    fall = np.exp(-0.5 * (T / 0.7) ** 2) * kit.sstep(1.0, 0.5, np.abs(Q))
    col = (o["slit_L"] * fall)[..., None] * np.array([1.0, 0.98, 0.94])
    np.savez(path, P=P.astype(np.float32), col=col.astype(np.float32))


def camera(o):
    e = np.radians(o["E"])
    view = np.array([0.0, -np.cos(e), np.sin(e)])
    up = np.array([0.0, np.sin(e), np.cos(e)])
    H = o["W"] * 9.0 / 16.0
    A = np.array([0.0, R_RIM + 0.05, o["z_rim"]])
    target = A - up * (0.5 - o["apex_y"]) * H
    loc = target + view * o["dist"]
    cam = {"loc": loc.tolist(), "target": target.tolist(), "lens_mm": 36.0 * o["dist"] / o["W"], "roll": 0.0}
    if o["aperture"]:
        r = contact(o)[1] if o["focus_r"] is None else o["focus_r"]
        fp = np.array([0.0, r, zprof(r, o)])
        cam["aperture_mm"] = o["aperture"]
        cam["focus_distance"] = float(np.dot(loc - fp, view))
    return cam


def env(path, cam, o):
    """The room: dim walls and ceiling, and a tall window behind the bowl, placed where the water mirrors it. The aperture blurs its reflection by about its own width at the focal plane, so it arrives as a soft wash of light with a darker bar, not as a picture of a window."""
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
    if e2[2] < 0:
        e2 = -e2
    x = np.degrees(np.arctan2(d @ e1.astype(np.float32), d @ mirror.astype(np.float32)))
    y = np.degrees(np.arctan2(d @ e2.astype(np.float32), d @ mirror.astype(np.float32)))
    front = (d @ mirror.astype(np.float32)) > 0
    a = np.radians(o["win_tilt"])
    xr, yr = x * np.cos(a) - y * np.sin(a), x * np.sin(a) + y * np.cos(a)
    # the source in the flat water. Warm: a neutral veil lifts the blue over the tea and the filaments go mauve. Its far edge fades over win_fade degrees: on the meniscus the surface tilts through the whole of it, and a hard edge is drawn as rings parallel to the rim
    if o["win_shape"] == "round":
        pane = kit.sstep(1.0, 1.0 - o["win_soft"], np.hypot(x - o["win_cx"], y - o["win_cy"]) / o["win_wx"])
    else:
        pane = kit.sstep(1.0, 1.0 - o["win_soft"], np.abs(xr - o["win_cx"]) / o["win_wx"])
        pane = pane * kit.sstep(o["win_cy"] - o["win_wy"], o["win_cy"] - o["win_wy"] * (1 - o["win_soft"]), yr) * np.exp(-0.5 * (np.maximum(yr - (o["win_cy"] + o["win_wy"]), 0.0) / o["win_fade"]) ** 2)
        pane = pane * kit.sstep(0.06, 0.2, np.abs(xr - (o["win_cx"] + o["win_bar"])))
    E = E + (pane * front * o["win_L"])[..., None].astype(np.float32) * np.array(o["win_rgb"], np.float32)
    # high up over the water, seen only in the steep part of the meniscus: the bright thin water line of ref/tea_plume/05
    if o["line_L"]:
        strip = kit.sstep(o["line_y0"], o["line_y0"] + 4.0, y) * kit.sstep(o["line_y1"], o["line_y1"] - 8.0, y) * kit.sstep(90.0, 40.0, np.abs(x))
        E = E + (strip * front * o["line_L"])[..., None].astype(np.float32) * np.array([1.0, 0.99, 0.97], np.float32)
    # a window that only the wall can mirror (the wall looks up and back, towards the room behind the camera; the flat water looks away, towards the room behind the bowl): what makes the glaze read as glass, as the window on the cavetto does in s50. Its edges are broken by the orange peel and the throwing rings
    if o["sheen"]:
        az = np.degrees(np.arctan2(d[..., 0], -d[..., 1]))
        el = np.degrees(np.arcsin(np.clip(d[..., 2], -1, 1)))
        pn = kit.sstep(o["sheen_waz"], o["sheen_waz"] * o["sheen_soft"], np.abs(az - o["sheen_az"])) * kit.sstep(o["sheen_wel"], o["sheen_wel"] * o["sheen_soft"], np.abs(el - o["sheen_el"]))
        if o["sheen_bars"]:
            pn = pn * kit.sstep(0.4, 1.0, np.abs(az - (o["sheen_az"] + o["sheen_waz"] * 0.28))) * kit.sstep(0.4, 1.0, np.abs(el - (o["sheen_el"] + 2.0)))
        E = E + (o["sheen"] * pn)[..., None].astype(np.float32) * np.array([0.98, 1.0, 1.0], np.float32)
    np.save(path, E.astype(np.float32))


def scene(q, o, sub, tag, base=None):
    """Files carry the tag: looks run side by side, and a shared env.npy once made two different windows come out as one. With `base`, a frame of a take: all but the water and the tea is built once, under that name."""
    cam = camera(o)
    os.makedirs(sub, exist_ok=True)
    b = base or tag
    wet, dry = [os.path.join(sub, f"{b}_{n}.npz") for n in ("wet", "dry")]
    water = os.path.join(sub, f"{tag}_water.npz")
    if not (base and os.path.exists(dry)):
        build_bowl(wet, dry, o, q)
    build_water(water, o, q)
    sky = os.path.join(sub, f"{b}_sky.npz")
    if not (base and os.path.exists(sky)):
        sky = kit.sky_mesh(sky, cam, {"top": [0.0065, 0.0065, 0.0066], "glow": [0.016, 0.0155, 0.015], "y0": 0.3, "h": 0.6, "x0": 0.55, "mottle": 0.12})
    e = os.path.join(sub, f"{b}_env.npy")
    if not (base and os.path.exists(e)):
        env(e, cam, o)
    gl = {"Base Color": "col", "Roughness": 0.42, "Specular IOR Level": 0.5, "Emission Color": "glow", "Emission Strength": 1.0}
    meshes = [
        {"name": "wet", "npz": wet, "material": {**gl, "Coat Weight": 1.0, "Coat Roughness": "rough", "Coat IOR": 1.5 / N_WATER}},
        {"name": "dry", "npz": dry, "material": {**gl, "Coat Weight": 1.0, "Coat Roughness": "rough", "Coat IOR": 1.5}},
        {"name": "water", "npz": water, "shader_py": SHP, "params": {"kind": "water", "ior": N_WATER, "liquor": o["liquor"], "sigma": SIGMA}},
        {"name": "sky", "npz": sky, "material": {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}, "visible": {"diffuse": False, "shadow": False}},
    ]
    if o["slit_L"]:
        sp = os.path.join(sub, f"{b}_slit.npz")
        slit_mesh(sp, cam, o)
        meshes.append({"name": "slit", "npz": sp, "material": {"Base Color": [0.0, 0.0, 0.0], "Emission Color": "col", "Emission Strength": 1.0, "Specular IOR Level": 0.0, "Roughness": 1.0}, "visible": {"camera": False, "diffuse": False, "shadow": False}})
    if o["bubbles"]:
        bp = os.path.join(sub, f"{b}_bub.npz")
        if not (base and os.path.exists(bp)):
            bubbles(bp, o)
        meshes.append({"name": "bubbles", "npz": bp, "smooth": True, "shader_py": SHP, "params": {"kind": "water", "ior": 1.0 / N_WATER}})
    if o["foam"]:
        fp = os.path.join(sub, f"{b}_foam.npz")
        if not (base and os.path.exists(fp)):
            foam(fp, o)
        meshes.append({"name": "foam", "npz": fp, "smooth": True, "shader_py": SHP, "params": {"kind": "film", "ior": N_WATER}})
    vols = []
    if o["tea"]:
        sim = os.path.join(kit.OUT, "s70_sim", o["tea"])
        vdb = os.path.join(sim, o["tea_t"] + ".vdb")
        if not os.path.exists(vdb):
            b = os.environ.get("GEWU_BLENDER_ROOT", "blender-5.2.1-linux-x64")
            subprocess.run([os.path.join(b, "5.2/python/bin/python3.13"), os.path.join(HERE, "s70_vdb.py"), sim, o["tea_t"]], env={**os.environ, "LD_LIBRARY_PATH": os.path.join(b, "lib")}, check=True)
        vols.append({"name": "tea", "vdb": vdb, "shader_py": SHP, "params": {"kind": "tea", "sigma": SIGMA, "K": o["tea_K"]}})
    return {
        "camera": cam,
        "meshes": meshes,
        "volumes": vols,
        # the light that makes the glaze white: soft, above and in front, unseen in the water and the glaze so that what they mirror is only the window
        "lights": [
            {"name": "key", "type": "area", "size": [o["key_size"], o["key_size"]], "loc": o["key"], "target": [0.0, 4.5, 0.0], "watts": o["key_W"], "rgb": o["key_rgb"], "hide_in_gloss": True},
            {"name": "fill", "type": "area", "size": [60.0, 60.0], "loc": o["fill_loc"], "target": [0.0, 4.5, 0.0], "watts": o["fill_W"], "rgb": [0.96, 0.98, 1.0], "hide_in_gloss": True},
        ],
        # the room is for reflections only: what lights the glaze and what the water mirrors can then be set apart
        "env": {"npy": e, "diffuse": False, "transmission": True, "no_diffuse_paths": True},
        "bounces": 24,
        "transmission_bounces": 16,
        "glossy_bounces": 8,
        "diffuse_bounces": 6,
        "volume_bounces": 0,
        "clamp_indirect": 30.0,
        "denoise": o.get("denoise", True),
        "res": {"preview": [960, 540], "mid": [1280, 720], "final": [1920, 1080]}[q],
        "spp": o["spp"] or {"preview": 96, "mid": 192, "final": 384}[q],
    }


DEVELOP = dict(exposure=0.0, contrast=1.2, saturation=1.08, black=0.0, grain=1.1, sharpen=0.22, halation=0.04, glare=0.0, vignette=0.14, ca=0.0003, seed=70)


def render(cfg, sub, tag):
    t = time.time()
    p = kit._render_local(cfg, sub, tag)
    print(f"[{tag}] {time.time()-t:.0f} s", flush=True)
    return p


def write(L, tag, dev=None):
    from darkroom import develop, print_look

    x = print_look(develop(L.astype(np.float32), **{**DEVELOP, **(dev or {})}))
    cv2.imwrite(os.path.join(D, tag + ".jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])


def look(tag, over, q):
    o = {**P0, **over}
    os.makedirs(D, exist_ok=True)
    L = np.load(render(scene(q, o, D, tag), D, tag))
    print(tag, "p50", np.median(L, axis=(0, 1)).round(3), "p99", np.percentile(L, 99, axis=(0, 1)).round(3), flush=True)
    write(L, tag, {**o["dev"], "exposure": o["exposure"]})


def take(over, q, first, n, step=1.0 / 24):
    """Frames of a solve saved at first + i * step. out/v2/s70_chatang_take_{q}/{v###.jpg, take.mp4}; at final also s70_chatang_move_final/{take.linear_###.npy, develop.json}, which is what the film reads."""
    from darkroom import develop, print_look

    o = {**P0, **over}
    d = os.path.join(kit.OUT, f"{NAME}_take_{q}")
    os.makedirs(d, exist_ok=True)
    dev = {**DEVELOP, **o["dev"], "exposure": o["exposure"]}
    mv = None
    if q == "final":
        mv = os.path.join(kit.OUT, f"{NAME}_move_final")
        os.makedirs(mv, exist_ok=True)
        json.dump(dev, open(os.path.join(mv, "develop.json"), "w"))
    for i in range(n):
        t = first + i * step
        tag = f"f{i:03d}"
        t0 = time.time()
        L = np.load(render(scene(q, {**o, "tea_t": f"{t:07.3f}", "swell_t": i * step}, d, tag, base="take"), d, tag))
        if mv:
            np.save(os.path.join(mv, f"take.linear_{i:03d}.npy"), L.astype(np.float32))
        x = print_look(develop(L.astype(np.float32), **{**dev, "seed": 7000 + i}))
        cv2.imwrite(os.path.join(d, f"v{i:03d}.jpg"), (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        os.remove(os.path.join(d, f"{tag}.linear.npy"))
        print(f"[{tag}] t={t:.3f}, {time.time()-t0:.0f} s", flush=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(d, "v%03d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", os.path.join(d, "take.mp4")], check=True)


def args(s):
    """k=v,k=v with JSON values, or @file.json: passes through shells without quotes."""
    if not s or s == "-":
        return {}
    if s.startswith("@"):
        return json.load(open(s[1:]))
    return {k: json.loads(v) for k, v in (kv.split("=", 1) for kv in s.split(","))}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "look":
        look(sys.argv[2], args(sys.argv[3]) if len(sys.argv) > 3 else {}, sys.argv[4] if len(sys.argv) > 4 else "preview")
    elif cmd == "take":  # take k=v,.. QUALITY FIRST N
        take(args(sys.argv[2]), sys.argv[3], float(sys.argv[4]), int(sys.argv[5]))
    else:
        raise SystemExit(__doc__)
