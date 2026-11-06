"""Shot 59: Suzhou embroidery (苏绣): a round silk fan (团扇) with a peony, a bud and a butterfly, lying flat and tilted to the lens; its slim spotted-bamboo rim is the arc, above it the photographer's dark cloth, out of focus.

    python3 -I v2/stills/s59_suxiu.py flat                       the drawing in 2D, no render: out/v2/s59_suxiu/flat.jpg
    python3 -I v2/stills/s59_suxiu.py stitch x0 x1 y0 y1         real stitches in a window of the fan, shaded with a stand-in lobe model, no render
    python3 -I v2/stills/s59_suxiu.py [preview|mid|final] [lv|lan]   the film uses lan; lv is the bean-green peony (final goes to cand.*), lan the azurite one (cand_lan.*); no colour is the pink original, whose final goes to final.*

Built as the work is built (scales are estimates from general knowledge, compared by eye with ref/suxiu, none of it measured; the drawing is ours and copies no piece):
- each petal, leaf half and wing is its own patch with its own flow, in coordinates where a thread is a straight line. In a petal the threads run from the heart outward (bent polar coordinates about its
  root); in a leaf they run from the midrib out at a slant;
- long-and-short stitch (长短针, 施针): rows of stitches across the flow, each row with its own thread count so that the spacing stays at S as threads converge. Stitch ends are staggered thread by thread,
  and the outline of a patch is made of the ends of its threads, so it is never a clean vector edge;
- colour by stitch, never by pixel: each stitch takes one of 22 dyed shades from its position plus a jitter. All blending comes from interleaved threads of discrete shades, as in real silk shading;
- where a petal passes under another its threads run deeper, as embroiderers do, as well as taking the rendered shadow;
- the height of every vertex is a round thread section with its ends dipping into the cloth, so shimmer comes from geometry: threads across the half vector catch the window and threads along it do not;
- the ground is a plain weave, with slubs, puckered slightly round the embroidery, on a faint waviness. A few loose ends.

Stand-ins and estimates:
- thread spacing 0.022 cm and stitch length 0.3-0.8 cm are estimates. Real split silk can be finer; this is about the finest that still resolves in a 2560 px frame 19 cm wide;
- a thread is a height field, not a true fibre: no undercut and no light through it. The floss's own fibres are not modelled, only a per-stitch roll and tone;
- the ground's emission stands in for light passing through thin silk; a backlit fan would do this, a fan lying flat would do less;
- METAL (0.35 on floss) is a stand-in for the light silk carries inside its fibres, which tints its highlight, and which a plain dielectric lobe lacks;
- THREAD_GLOW, a little emission of a thread's own colour, stands in for light passing along and through floss, which keeps its shadows coloured instead of grey;
- the stitch model's shades (22), the butterfly's finer silk (0.016 cm) and the leaf's (0.019 cm) are choices, not measurements.

Beauty over literal accuracy, deliberately:
- real silk shading is usually more muted and duller in its deep shades. These dyes are lighter and more saturated than any old piece in ref/suxiu, and nothing goes dark;
- the rim is spotted bamboo (湘妃竹), oiled: a usual material for a fan, but the blotches are drawn by us, not measured or copied from a piece;
- the relief (padded petals, rolled lips, a pillow to each petal) is stronger than in most flat Suzhou work, nearer to padded work, because it gives the window something to slide over.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, fbm, frame_camera, shoot, sstep
from vessel import fit_arc, project, view_dir

NAME = "s59_suxiu"
SEED = 59
R = 15.5  # outer edge of the rim, cm: as large as it is so that its arc lies flat across the frame. The drawing did not grow
CY = 8.9 - R  # the rim's centre on y: its crown is at y = 8.9, so the drawing keeps about its place under the crown, a little nearer so that the stamens stay in frame
W, EL, DIST = 19.0, 65.0, 42.0
AX0, AX1, AY0, AY1 = -10.4, 10.4, 2.3, 9.2  # the mesh, cm
S = 0.022  # thread spacing, cm
HTH = 0.0048  # height of a thread's section, cm: unspun floss lies flat, wider than it is high, which also concentrates its reflection
METAL = 0.35
SPEC = 0.5
WSIG = [30, 22]
EMIT = 0.2
THREAD_GLOW = 1.0
LEAN = (-0.2, 0.24)  # the tilt of the half vector
WINDOW_L, RAKE, FILL = 5.0, 2600.0, 10000.0
APERTURE, FOCUS_Y = 12.0, 6.8
SHADES = 22
APEX_FIT = 0.465  # fit_arc fits a parabola to the rim, which can land a little off the crown; checked with tools/arc.py on the render

HEART = np.array([-1.6, 3.9])


# --- palettes: linear RGB, root (0) to tip (1). Nothing dark or muddy ------------------------------------------------------
def _pal(*stops):
    t = np.array([s[0] for s in stops], np.float32)
    c = np.array([s[1] for s in stops], np.float32)
    return t, c


PAL = {
    "coral": _pal((0, (0.80, 0.030, 0.13)), (0.28, (0.93, 0.085, 0.20)), (0.5, (0.97, 0.23, 0.30)), (0.7, (0.99, 0.40, 0.41)), (0.86, (0.995, 0.62, 0.60)), (1, (1.0, 0.86, 0.81))),
    "magenta": _pal((0, (0.62, 0.03, 0.17)), (0.28, (0.80, 0.075, 0.25)), (0.5, (0.90, 0.21, 0.35)), (0.7, (0.95, 0.39, 0.47)), (0.86, (0.97, 0.62, 0.65)), (1, (0.99, 0.86, 0.83))),
    "leaf": _pal((0, (0.05, 0.28, 0.15)), (0.3, (0.12, 0.44, 0.21)), (0.55, (0.28, 0.60, 0.31)), (0.78, (0.52, 0.75, 0.45)), (1, (0.80, 0.90, 0.64))),
    "jade": _pal((0, (0.04, 0.30, 0.27)), (0.3, (0.09, 0.46, 0.37)), (0.55, (0.24, 0.62, 0.48)), (0.78, (0.50, 0.78, 0.63)), (1, (0.80, 0.92, 0.78))),
    "wing": _pal((0, (0.075, 0.035, 0.62)), (0.3, (0.11, 0.10, 0.86)), (0.55, (0.20, 0.26, 0.97)), (0.78, (0.44, 0.54, 0.99)), (1, (0.86, 0.88, 1.0))),
    "gold": _pal((0, (0.86, 0.46, 0.09)), (0.5, (0.99, 0.70, 0.22)), (1, (1.0, 0.90, 0.56))),
    "body": _pal((0, (0.42, 0.20, 0.34)), (1, (0.86, 0.62, 0.52))),
}


def _s(*stops):
    """A ramp given in sRGB 0-255, as a dye is judged by eye."""
    t = np.array([a[0] for a in stops], np.float32)
    c = np.array([a[1] for a in stops], np.float32) / 255.0
    return t, np.where(c < 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


# silk dyes: every value is an estimate by eye, none measured from a piece
COLOURS = {
    "lv": dict(  # 豆绿 peony: deep blue-green root, bean green, nearly moon white with a breath of yellow at the tip. Leaves pressed deep and toward blue so that flower and leaf part. The butterfly stays blue, in dye rather than in screen colour
        coral=_s((0, (26, 76, 70)), (0.28, (58, 112, 94)), (0.5, (116, 152, 108)), (0.7, (160, 186, 134)), (0.86, (204, 216, 172)), (1, (240, 240, 214))),
        magenta=_s((0, (20, 68, 72)), (0.28, (46, 100, 94)), (0.5, (98, 142, 112)), (0.7, (146, 178, 140)), (0.86, (194, 212, 180)), (1, (236, 240, 222))),
        leaf=_s((0, (16, 42, 46)), (0.3, (24, 60, 62)), (0.55, (38, 82, 82)), (0.78, (62, 106, 102)), (1, (104, 142, 130))),
        jade=_s((0, (14, 40, 54)), (0.3, (22, 58, 72)), (0.55, (36, 80, 94)), (0.78, (60, 106, 116)), (1, (104, 144, 146))),
        wing=_s((0, (34, 44, 112)), (0.3, (50, 70, 142)), (0.55, (84, 110, 172)), (0.78, (138, 160, 200)), (1, (214, 222, 232))),
        body=_s((0, (70, 54, 48)), (1, (176, 150, 124))),
    ),
    "lan": dict(  # 石青 peony: deep ultramarine root, azurite, moon white tip. Leaves untouched. The butterfly apricot to ochre gold, or it would run into the flower
        coral=_s((0, (26, 38, 102)), (0.28, (38, 60, 128)), (0.5, (62, 98, 156)), (0.7, (108, 144, 184)), (0.86, (172, 196, 212)), (1, (228, 234, 232))),
        magenta=_s((0, (22, 44, 98)), (0.28, (32, 68, 122)), (0.5, (58, 106, 150)), (0.7, (110, 152, 178)), (0.86, (178, 206, 212)), (1, (230, 238, 232))),
        wing=_s((0, (118, 72, 30)), (0.3, (158, 102, 42)), (0.55, (196, 140, 62)), (0.78, (222, 178, 102)), (1, (242, 216, 162))),
        body=_s((0, (70, 46, 34)), (1, (172, 132, 96))),
    ),
}
COLOUR = None


def use_colour(name):
    global COLOUR
    if name is None:
        return
    if name not in COLOURS:
        raise SystemExit(f"no colour {name}: {list(COLOURS)}")
    COLOUR = name
    PAL.update(COLOURS[name])


def ramp(pal, t, quant=True):
    """The dyed shade for ramp position t. Quantised: there are only so many colours of floss in the box."""
    ts, cs = PAL[pal]
    t = np.clip(t, 0, 1)
    if quant:
        t = np.round(t * (SHADES - 1)) / (SHADES - 1)
    return np.stack([np.interp(t, ts, cs[:, i]) for i in range(3)], -1).astype(np.float32)


# --- a patch: coordinates where threads are straight ----------------------------------------------------------------------
def petal(root, a_deg, L, half_deg, bend=0.0, seed=0, pal="coral", z=0.02, t0=0.1, t1=1.0, gamma=1.0, ruffle=1.0, rh=0.52, fold=None, pleat=0.03, skew=0.0, under=1.0, sp=None):
    """A fan-shaped petal: threads are rays from its root in polar coordinates bent along the length. Its edge is rho_max(theta), ruffled and notched by hand-tuned functions, so the row structure is analytic."""
    rng = np.random.default_rng(1000 + seed)
    Th = np.radians(half_deg)
    x = np.linspace(-1, 1, 721)
    q = np.clip(np.abs(x + skew * (1 - x**2)), 0, 1)
    shape = (1 - q**3.1) ** (1 / 1.55)
    r = np.ones_like(x)
    for f, amp in ((rng.uniform(1.3, 2.2), 0.055), (rng.uniform(2.8, 4.2), 0.05), (rng.uniform(5.5, 8.0), 0.022), (rng.uniform(13, 18), 0.005)):
        r += ruffle * amp * np.sin(np.pi * f * x + rng.uniform(0, 6.28))
    for _ in range(rng.integers(1, 4)):  # clefts between the rounded lobes of the rim: shallow, soft, a small sharp nick at the bottom
        xn, d, wn = rng.uniform(-0.66, 0.66), rng.uniform(0.035, 0.09), rng.uniform(0.05, 0.1)
        r -= ruffle * (d * np.exp(-(((x - xn) / wn) ** 2)) + 0.3 * d * np.exp(-np.abs(x - xn) / 0.012))
    edge = L * shape * np.maximum(r, 0.3)
    fold_t = None
    if fold:  # the lip of the petal rolled over. Its inner line follows the general run of the rim, not its small lobes
        xc, wx, dep = fold
        b = np.exp(-(((x - xc) / wx) ** 4))
        smooth = cv2.GaussianBlur(edge[None].astype(np.float32), (0, 0), 28).ravel().astype(np.float64)
        wig = 1 + 0.12 * np.sin(np.pi * rng.uniform(2.5, 4) * x + rng.uniform(0, 6.28))
        fold_t = smooth - dep * L * b * wig
        fold_t = np.minimum(fold_t, edge - 0.012)
        fold_t[b < 0.04] = 1e9
    # the sides of a petal wave a little
    wave_a, wave_f, wave_p = rng.uniform(0.015, 0.04), rng.uniform(1.0, 2.0), rng.uniform(0, 6.28)
    pl = [(rng.uniform(2.0, 3.4), rng.uniform(0, 6.28), 1.0), (rng.uniform(4.0, 6.5), rng.uniform(0, 6.28), 0.6), (rng.uniform(8.0, 12.0), rng.uniform(0, 6.28), 0.28)]
    e = dict(kind="petal", root=np.array(root, float), a0=np.radians(a_deg), L=L, Th=Th, bend=np.radians(bend), tab_a=x * Th, tab_e=edge, fold_t=fold_t, wave=(wave_a, wave_f, wave_p), pleats=pl, pal=pal, z=z, t0=t0, t1=t1, gamma=gamma, rh=rh, seed=seed, pleat=pleat, tone=rng.normal(0, 1), under=under, scale=None, sp=sp or S)
    return e


def blade(p0, a_deg, L, W_, kappa=0.0, side=1, k=0.9, seed=0, pal="leaf", z=0.012, t_mid=0.15, t_edge=0.95, lobes=True, rh=0.5, pleat=0.012, tip=0.0, wfun=None, under=1.0):
    """One half of a leaf or a ribbon: the midrib is an arc of curvature kappa; a thread is the line a = s - k*|t|. Its edge is found numerically as a table over a."""
    rng = np.random.default_rng(2000 + seed)
    s_ = np.linspace(0, L, 900)
    u = s_ / L
    if wfun is not None:
        w = wfun(u)
    else:
        w = W_ * np.sin(np.pi * u**0.72) ** 0.72
        if lobes:  # the lobes of a peony leaf: shoulders with pointed tips and sinus between
            ph = rng.uniform(0, 6.28)
            w = w * (1 + 0.17 * np.sin(2 * np.pi * rng.uniform(1.4, 2.0) * u + ph) + 0.05 * np.sin(2 * np.pi * rng.uniform(4, 6) * u + ph * 2))
            for _ in range(rng.integers(1, 3)):
                un, d, wn = rng.uniform(0.35, 0.8), rng.uniform(0.14, 0.34), rng.uniform(0.02, 0.05)
                w = w * (1 - d * np.exp(-np.abs(u - un) / wn))
    a_tab = np.linspace(-k * max(W_, 0.02) * 1.3, L, 900)
    # the edge along each thread: walk out from the midrib until it leaves the half
    b = np.linspace(0, max(W_, 0.02) * 1.35, 240)[:, None]
    ss = a_tab[None, :] + k * b
    ww = np.interp(ss, s_, w, left=0, right=0)
    out = b > ww
    first = np.argmax(out, axis=0)
    e_tab = b[first, 0].astype(np.float64)
    e_tab[(ss[-1] < 0) & (first == 0)] = 0
    a0 = np.radians(a_deg)
    e = dict(kind="blade", p0=np.array(p0, float), a0=a0, L=L, W=W_, kappa=kappa, side=side, k=k, tab_a=a_tab, tab_e=e_tab, s_=s_, w=w, pal=pal, z=z, t_mid=t_mid, t_edge=t_edge, rh=rh, seed=seed, pleat=pleat, tone=rng.normal(0, 1), fold_t=None, scale=1.0 / np.sqrt(1 + k * k), phase=rng.uniform(0, 6.28), under=under, sp=0.019)
    return e


def coords(e, X, Y):
    """(rho along the thread, ang across the threads) for points. Threads are lines of constant ang."""
    if e["kind"] == "petal":
        dx, dy = X - e["root"][0], Y - e["root"][1]
        rho = np.hypot(dx, dy)
        a, f, p = e["wave"]
        th = np.arctan2(dy, dx) - e["a0"] - e["bend"] * (rho / e["L"]) ** 1.5 - a * np.sin(2 * np.pi * f * rho / e["L"] + p) * (rho / e["L"])
        th = np.mod(th + np.pi, 2 * np.pi) - np.pi
        return rho, th
    s, t = blade_st(e, X, Y)
    t = t * e["side"]
    a = s - e["k"] * np.abs(t)
    b = np.where(t >= 0, t, -1.0)  # the other half is not this patch
    return b, a


def blade_st(e, X, Y):
    c, s0 = np.cos(e["a0"]), np.sin(e["a0"])
    dx, dy = X - e["p0"][0], Y - e["p0"][1]
    u, v = c * dx + s0 * dy, -s0 * dx + c * dy
    kp = e["kappa"]
    if abs(kp) < 1e-5:
        return u, v
    # centre at (0, 1/kp) in (u, v)
    rc = 1.0 / kp
    ang = np.arctan2(u, rc - v) if kp > 0 else np.arctan2(u, v - rc)
    d = np.hypot(u, v - rc)
    return ang * abs(rc), (abs(rc) - d) * np.sign(kp)


def unmap(e, rho, ang):
    """The inverse of coords: where (rho, ang) lies in the plane."""
    if e["kind"] == "petal":
        a, f, p = e["wave"]
        th = ang + e["a0"] + e["bend"] * (rho / e["L"]) ** 1.5 + a * np.sin(2 * np.pi * f * rho / e["L"] + p) * (rho / e["L"])
        return e["root"][0] + rho * np.cos(th), e["root"][1] + rho * np.sin(th)
    t = rho * e["side"]
    s = ang + e["k"] * rho
    kp = e["kappa"]
    if abs(kp) < 1e-5:
        u, v = s, t
    else:
        rc = 1.0 / kp
        d = abs(rc) - t * np.sign(kp)
        phi = s / abs(rc)
        u = d * np.sin(phi)
        v = rc - d * np.cos(phi) if kp > 0 else rc + d * np.cos(phi)
    c, s0 = np.cos(e["a0"]), np.sin(e["a0"])
    return e["p0"][0] + c * u - s0 * v, e["p0"][1] + s0 * u + c * v


def outline(e):
    a, ed = e["tab_a"], e["tab_e"]
    x, y = unmap(e, ed, a)
    if e["kind"] == "petal":
        return np.concatenate([np.stack([x, y], 1), e["root"][None]], 0)
    k = np.linspace(0, len(a) - 1, 400).astype(int)
    x0, y0 = unmap(e, np.zeros(400), a[k])
    return np.concatenate([np.stack([x[k], y[k]], 1), np.stack([x0, y0], 1)[::-1]], 0)


def t_of(e, rho, ang, eg):
    """Ramp position of a thread at (rho, ang), where eg is the edge along that thread."""
    if e["kind"] == "petal":
        u = np.clip(rho / np.maximum(eg, 1e-3), 0, 1)
        return e["t0"] + (e["t1"] - e["t0"]) * u ** e["gamma"] + 0.035 * e["tone"]
    u = np.clip(rho / np.maximum(np.interp(ang + e["k"] * rho, e["s_"], e["w"], left=0.02, right=0.02), 0.02), 0, 1)
    along = np.clip((ang + e["k"] * rho) / e["L"], 0, 1)
    return e["t_mid"] + (e["t_edge"] - e["t_mid"]) * u**0.9 + 0.18 * (along - 0.4) + 0.03 * e["tone"]


def relief(e, rho, ang, ed):
    """Pillow and pleats in cm: the slow shape of the patch. This is what makes the window slide across it."""
    if e["kind"] == "petal":
        x = ang / e["Th"]
        u = np.clip(rho / e["L"], 0, 1.2)
        p = sum(w * np.sin(np.pi * f * x + ph) for f, ph, w in e["pleats"])
        rel = e["pleat"] * p * u**1.2
        return rel + 0.018 * (1 - np.exp(-np.maximum(ed - rho, 0) / 0.16)), p
    p = np.sin(ang * 5.2 + e["phase"]) + 0.5 * np.sin(ang * 11 + 2 * e["phase"])
    return e["pleat"] * p + 0.014 * (1 - np.exp(-np.maximum(ed - rho, 0) / 0.1)), p


# --- the drawing -----------------------------------------------------------------------------------------------------------
def leaf(out, p0, a, L, Wd, kappa=0.0, seed=0, pal="leaf", z=0.01, under=1.0):
    """A leaf: two halves meeting at a midrib, a slim paler ribbon on top."""
    out.append(blade(p0, a, L, Wd, kappa, 1, 1.0, seed, pal, z, under=under))
    out.append(blade(p0, a, L, Wd * 0.86, kappa, -1, 1.0, seed + 500, pal, z + 0.002, under=under))
    fn = lambda u: 0.032 * (1 - u) ** 0.7 + 0.004
    for sd in (1, -1):
        out.append(blade(p0, a, L * 0.94, 0.04, kappa, sd, 2.4, seed + 900, pal, z + 0.006, t_mid=0.62, t_edge=0.82, lobes=False, rh=0.4, pleat=0.0, wfun=fn, under=0.0))


def ribbon(out, p0, a, L, w0, w1, kappa=0.0, k=1.8, seed=0, pal="leaf", z=0.012, tm=0.4, te=0.8):
    """A stem or an antenna: a slanted satin along an arc."""
    fn = lambda u: w0 + (w1 - w0) * u
    for sd in (1, -1):
        out.append(blade(p0, a, L, max(w0, w1), kappa, sd, k, seed + (0 if sd > 0 else 11), pal, z, t_mid=tm, t_edge=te, lobes=False, rh=0.45, pleat=0.0, wfun=fn, under=0.0))


def butterfly(out, c, beta, s, z=0.018):
    """Head towards beta (degrees). Seen a little from one side, so the far wings are foreshortened. Wings are petals of 'wing' floss, darker at the root."""
    b = beta
    root = np.array(c)
    fore = dict(pal="wing", z=z, t0=0.04, t1=1.02, gamma=1.25, ruffle=0.34, pleat=0.008, under=0.6, sp=0.016)  # a butterfly is worked in finer split silk
    out.append(petal(root + 0.02, b + 142, 1.16 * s, 40, bend=-10, seed=61, rh=0.34, **fore))
    out.append(petal(root - 0.02, b - 128, 0.98 * s, 36, bend=10, seed=62, rh=0.34, **fore))
    out.append(petal(root, b + 66, 1.72 * s, 27, bend=-16, seed=63, rh=0.36, **fore))
    out.append(petal(root, b - 56, 1.26 * s, 25, bend=14, seed=64, rh=0.36, **fore))
    # the abdomen and thorax, head to tail
    r = np.radians(b)
    head = root + 0.32 * s * np.array([np.cos(r), np.sin(r)])
    fn = lambda u: 0.095 * s * np.sin(np.pi * np.clip(u, 0.02, 0.98)) ** 0.6
    for sd in (1, -1):
        out.append(blade(head, b + 180, 1.0 * s, 0.1 * s, 0.0, sd, 0.15, 70 + sd, "body", z + 0.02, t_mid=0.1, t_edge=0.9, lobes=False, rh=0.16, pleat=0.0, wfun=fn, under=0.0))
    ribbon(out, head, b + 26, 1.05 * s, 0.009, 0.006, kappa=0.28, k=2.5, seed=73, pal="body", z=z + 0.012, tm=0.2, te=0.6)
    ribbon(out, head, b - 21, 0.95 * s, 0.009, 0.006, kappa=-0.3, k=2.5, seed=75, pal="body", z=z + 0.012, tm=0.2, te=0.6)


def design():
    """The elements, back to front. The drawing was made by hand, in numbers: bloom turned so its back petals climb to the rim on the upper left, bud on the right, butterfly in the sky of the fan."""
    out = []
    H = HEART

    # --- stems and leaves, behind everything
    ribbon(out, (3.0, 0.2), 58, 3.9, 0.075, 0.05, kappa=-0.12, seed=301, pal="leaf", z=0.006, tm=0.3, te=0.66)
    leaf(out, (-4.7, 3.0), 171, 2.95, 0.86, kappa=0.1, seed=11, z=0.006)
    leaf(out, (-4.9, 2.35), 193, 2.95, 0.82, kappa=-0.12, seed=12, pal="jade", z=0.005)
    leaf(out, (1.5, 3.7), 22, 3.35, 1.0, kappa=0.13, seed=13, pal="jade", z=0.006)
    leaf(out, (1.9, 2.75), 2, 3.7, 0.92, kappa=0.06, seed=14, z=0.007)
    leaf(out, (5.3, 2.95), -5, 2.6, 0.62, kappa=0.2, seed=15, pal="jade", z=0.009)

    # --- layer A: the great petals. Long at the back, where they climb to the rim. Broad, as a peony's are
    z = 0.02
    A = dict(pal="coral", z=z, t0=0.3, t1=0.95, gamma=1.55, rh=0.56, pleat=0.024)
    Am = dict(A, pal="magenta")
    out.append(petal(H, 219, 4.5, 37, bend=8, seed=1, skew=0.12, **A))
    out.append(petal(H, 183, 4.85, 34, bend=-7, seed=2, skew=-0.1, fold=(0.1, 0.5, 0.05), **Am))
    out.append(petal(H, 147, 4.3, 37, bend=9, seed=3, **A))
    out.append(petal(H, 113, 3.85, 34, bend=-8, seed=4, skew=0.14, fold=(-0.2, 0.45, 0.055), **Am))
    out.append(petal(H, 78, 3.95, 36, bend=9, seed=5, **A))
    out.append(petal(H, 43, 4.35, 35, bend=-9, seed=6, skew=-0.12, fold=(0.15, 0.5, 0.05), **A))
    out.append(petal(H, 10, 4.65, 36, bend=8, seed=7, **Am))
    out.append(petal(H, -24, 4.2, 37, bend=-6, seed=8, skew=0.1, **A))

    # --- layer B
    B = dict(pal="magenta", z=z + 0.016, t0=0.2, t1=0.92, gamma=1.5, rh=0.5, pleat=0.022)
    Bc = dict(B, pal="coral")
    out.append(petal(H, 202, 3.75, 32, bend=-9, seed=21, skew=-0.1, **Bc))
    out.append(petal(H, 165, 3.9, 31, bend=8, seed=22, fold=(0.1, 0.5, 0.06), **B))
    out.append(petal(H, 130, 3.45, 32, bend=-10, seed=23, **Bc))
    out.append(petal(H, 95, 3.15, 31, bend=7, seed=24, skew=0.15, fold=(0.0, 0.42, 0.07), **Bc))
    out.append(petal(H, 60, 3.25, 32, bend=-7, seed=25, **B))
    out.append(petal(H, 26, 3.65, 31, bend=9, seed=26, fold=(-0.1, 0.5, 0.06), **Bc))
    out.append(petal(H, -8, 3.55, 32, bend=-8, seed=27, skew=-0.14, **B))

    # --- layer C
    C = dict(pal="coral", z=z + 0.03, t0=0.1, t1=0.88, gamma=1.4, rh=0.44, pleat=0.018)
    Cm = dict(C, pal="magenta")
    out.append(petal(H, 188, 2.85, 31, bend=8, seed=31, **Cm))
    out.append(petal(H, 150, 2.75, 30, bend=-8, seed=32, skew=0.1, fold=(0.1, 0.5, 0.08), **C))
    out.append(petal(H, 112, 2.4, 31, bend=9, seed=33, **Cm))
    out.append(petal(H, 74, 2.35, 30, bend=-7, seed=34, skew=-0.12, fold=(-0.1, 0.5, 0.08), **C))
    out.append(petal(H, 37, 2.6, 31, bend=8, seed=35, **Cm))
    out.append(petal(H, 2, 2.7, 31, bend=-9, seed=36, **C))

    # --- the front petals, falling away towards the lens: rooted in the heart, seen only at the sides of the cup
    G = dict(pal="coral", z=z + 0.04, t0=0.14, t1=1.0, gamma=1.4, rh=0.5, pleat=0.02)
    Gm = dict(G, pal="magenta")
    out.append(petal(H, -30, 3.2, 40, bend=10, seed=54, **G))
    out.append(petal(H, 218, 3.2, 40, bend=-10, seed=55, **Gm))

    # --- layer D: the cup behind the heart
    D = dict(pal="magenta", z=z + 0.05, t0=0.03, t1=0.86, gamma=1.3, rh=0.36, pleat=0.014, ruffle=0.8)
    Dc = dict(D, pal="coral")
    for a, L, hf, bd, sd, fl in ((178, 1.95, 33, 8, 41, None), (138, 1.85, 32, -8, 42, (0.05, 0.5, 0.1)), (97, 1.62, 34, 7, 43, None), (57, 1.68, 33, -7, 44, (-0.1, 0.5, 0.1)), (18, 1.92, 34, 9, 45, None)):
        out.append(petal(H, a, L, hf, bend=bd, seed=sd, fold=fl, **(D if sd % 2 else Dc)))

    # --- the stamens are painted here
    out.append("stamens")

    # --- the front of the cup: seen from outside, tips rising towards the heart, roots out of the frame
    F = dict(pal="coral", z=z + 0.09, t0=0.25, t1=0.98, gamma=1.4, rh=0.42, pleat=0.014, ruffle=0.8)
    Fm = dict(F, pal="magenta")
    b = H + np.array([0.05, -2.35])
    out.append(petal(b + (-1.95, 0.25), 112, 2.15, 44, bend=-8, seed=58, fold=(0.1, 0.55, 0.06), **F))
    out.append(petal(b + (1.95, 0.2), 66, 2.1, 44, bend=8, seed=59, fold=(-0.1, 0.55, 0.06), **Fm))
    out.append(petal(b + (-0.95, 0.0), 100, 1.98, 50, bend=-8, seed=51, fold=(0.0, 0.6, 0.07), **Fm))
    out.append(petal(b + (1.0, -0.02), 80, 1.95, 50, bend=8, seed=52, fold=(0.1, 0.6, 0.07), **F))
    out.append(petal(b + (0.02, -0.1), 90, 1.82, 58, bend=-3, seed=53, fold=(-0.05, 0.55, 0.08), **dict(Fm, z=z + 0.1)))

    # --- the bud, half open, on its stem
    Bd = dict(pal="coral", t0=0.15, t1=0.98, gamma=1.4, rh=0.4, pleat=0.014, ruffle=0.55)
    r0 = np.array((5.08, 3.2))
    out.append(petal(r0, 112, 2.0, 29, bend=-10, seed=81, z=0.02, **Bd))
    out.append(petal(r0, 60, 2.05, 30, bend=11, seed=82, z=0.02, **dict(Bd, pal="magenta")))
    out.append(petal(r0, 88, 2.25, 27, bend=4, seed=83, z=0.024, **dict(Bd, pal="magenta", t0=0.08, t1=0.88)))
    out.append(petal(r0, 124, 1.62, 32, bend=-14, seed=84, z=0.03, **Bd))
    out.append(petal(r0, 50, 1.65, 33, bend=14, seed=85, z=0.03, fold=(0.1, 0.5, 0.09), **Bd))
    out.append(petal(r0, 90, 1.42, 40, bend=-3, seed=86, z=0.04, fold=(-0.05, 0.6, 0.1), **dict(Bd, pal="magenta")))
    for a, L, wd, sd, kp in ((150, 1.05, 0.25, 91, -0.5), (30, 1.05, 0.24, 92, 0.5), (93, 0.72, 0.25, 93, 0.1)):
        out.append(blade(r0 + (0, -0.08), a, L, wd, kp, 1, 0.9, sd, "jade", 0.05, lobes=False, rh=0.3, t_mid=0.2, t_edge=0.86, under=0.0))
        out.append(blade(r0 + (0, -0.08), a, L, wd, kp, -1, 0.9, sd + 1, "jade", 0.05, lobes=False, rh=0.3, t_mid=0.2, t_edge=0.86, under=0.0))

    butterfly(out, (3.95, 6.45), 200, 0.98)
    return out


def stamens():
    """Pale gold knots (打籽) and their filaments in a ring round three small carpels: (filament lines, knots, carpels). The ring is squashed because the bloom is turned towards the lens."""
    rng = np.random.default_rng(SEED + 7)
    fil, knots = [], []
    for k in range(170):
        a = rng.uniform(0, 2 * np.pi)
        r0 = rng.uniform(0.2, 0.34)
        r1 = rng.uniform(0.42, 0.92)
        sq = 0.86 + 0.14 * np.sin(a)
        p0 = HEART + (0.0, -0.08) + r0 * np.array([np.cos(a), np.sin(a) * sq])
        a1 = a + rng.normal(0, 0.14)
        p1 = HEART + (0.0, -0.08) + r1 * np.array([np.cos(a1), np.sin(a1) * sq])
        fil.append((p0, p1, rng.uniform(0.6, 1)))
        knots.append((p1[0], p1[1], rng.uniform(0.034, 0.058), rng.uniform(0, 1)))
    carp = [(HEART[0] + dx, HEART[1] - 0.08 + dy, r_) for dx, dy, r_ in ((-0.09, 0.05, 0.085), (0.08, 0.08, 0.08), (0.11, -0.07, 0.078), (-0.05, -0.1, 0.082), (0.0, 0.0, 0.07))]
    return fil, knots, carp


# --- under-map: which patch lies under which, for the deep threads -------------------------------------------------------
def under_maps(els, pxcm=40.0):
    """For each patch: 1 right beside the edge of something lying on it, falling off inward."""
    nx, ny = int((AX1 - AX0) * pxcm), int((AY1 - AY0) * pxcm)
    polys = []
    for e in els:
        if isinstance(e, str):
            poly = np.stack([HEART[0] + 0.9 * np.cos(np.linspace(0, 6.28, 60)), HEART[1] - 0.08 + 0.85 * np.sin(np.linspace(0, 6.28, 60))], 1)
        else:
            poly = outline(e)
        polys.append(np.round((poly - [AX0, AY0]) * pxcm * 16).astype(np.int32))
    maps = [None] * len(els)
    acc = np.zeros((ny, nx), np.uint8)
    for i in range(len(els) - 1, -1, -1):
        d = cv2.distanceTransform((acc == 0).astype(np.uint8), cv2.DIST_L2, 3).astype(np.float32) / pxcm
        maps[i] = np.exp(-d / 0.5) * 0.62 + np.exp(-d / 0.13) * 0.38
        cv2.fillPoly(acc, [polys[i]], 1, cv2.LINE_8, shift=4)
    return maps, acc, pxcm


def sample_map(m, pxcm, x, y):
    ix = np.clip(((x - AX0) * pxcm).astype(np.int32), 0, m.shape[1] - 1)
    iy = np.clip(((y - AY0) * pxcm).astype(np.int32), 0, m.shape[0] - 1)
    return m[iy, ix]


# --- the flat view ---------------------------------------------------------------------------------------------------------
def camera(aperture=None, focus=None):
    th = np.linspace(0, 2 * np.pi, 1440)
    rim = np.stack([R * np.cos(th), CY + R * np.sin(th), np.full_like(th, 0.14)], 1)
    return fit_arc(rim, view_dir(-90.0, EL), W, DIST, apex=(0.5, APEX_FIT), target0=(0.0, 8.0, 0.0), aperture_mm=aperture, focus_point=focus)


def frame_outline():
    """The frame's edge on the plane of the fan, for the flat view."""
    cam, _ = camera()
    xs, ys = np.meshgrid(np.linspace(-14, 14, 561), np.linspace(-1, 20, 421))
    x, y, _ = project(cam, np.stack([xs, ys, np.zeros_like(xs)], -1).reshape(-1, 3))
    return xs, ys, x.reshape(xs.shape), y.reshape(xs.shape)


def flat_view():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    pxcm = 90.0
    nx, ny = int((AX1 - AX0) * pxcm), int((AY1 - AY0 + 0.2) * pxcm)
    y0 = AY0 - 0.2
    X, Y = np.meshgrid(AX0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    im = np.ones((ny, nx, 3), np.float32) * np.array([0.87, 0.80, 0.65], np.float32)
    hh = np.zeros((ny, nx), np.float32)
    els = design()
    maps, _, mp = under_maps(els)
    for i, e in enumerate(els):
        if isinstance(e, str):
            fil, knots, carp = stamens()
            for p0, p1, v in fil:
                a = np.round(np.array([(p0[0] - AX0) * pxcm, (p0[1] - y0) * pxcm])).astype(int)
                b = np.round(np.array([(p1[0] - AX0) * pxcm, (p1[1] - y0) * pxcm])).astype(int)
                cv2.line(im, tuple(int(c) for c in a), tuple(int(c) for c in b), (0.98, 0.82 * v, 0.42), 1, cv2.LINE_AA)
            for x, y, r_, v in knots:
                cv2.circle(im, (int((x - AX0) * pxcm), int((y - y0) * pxcm)), max(2, int(r_ * pxcm)), (1.0, 0.72 + 0.2 * v, 0.2 + 0.3 * v), -1, cv2.LINE_AA)
            for x, y, r_ in carp:
                cv2.circle(im, (int((x - AX0) * pxcm), int((y - y0) * pxcm)), int(r_ * pxcm), (0.55, 0.85, 0.55), -1, cv2.LINE_AA)
            hh[np.hypot(X - HEART[0], Y - HEART[1] + 0.08) < 0.9] = 0.1
            continue
        poly = outline(e)
        x0, x1, y0_, y1 = poly[:, 0].min(), poly[:, 0].max(), poly[:, 1].min(), poly[:, 1].max()
        ix0, ix1 = max(int((x0 - AX0) * pxcm) - 1, 0), min(int((x1 - AX0) * pxcm) + 2, nx)
        iy0, iy1 = max(int((y0_ - y0) * pxcm) - 1, 0), min(int((y1 - y0) * pxcm) + 2, ny)
        if ix0 >= ix1 or iy0 >= iy1:
            continue
        Xs, Ys = X[iy0:iy1, ix0:ix1], Y[iy0:iy1, ix0:ix1]
        rho, ang = coords(e, Xs, Ys)
        ed = np.interp(ang, e["tab_a"], e["tab_e"], left=-1, right=-1)
        m = (rho >= 0) & (rho < ed)
        if not m.any():
            continue
        t = t_of(e, rho, ang, ed)
        rel, pl = relief(e, rho, ang, ed)
        t = t + 0.05 * pl
        if "pal" in e:
            t = t - 0.42 * e["under"] * sample_map(maps[i], mp, Xs, Ys)
        c = ramp(e["pal"], t, quant=False)
        if e["fold_t"] is not None:
            ft = np.interp(ang, e["tab_a"], e["fold_t"])
            lip = rho > ft
            c[lip] = ramp(e["pal"], np.full(lip.sum(), 0.95), quant=False)
            rel = rel + 0.03 * lip
        sub = im[iy0:iy1, ix0:ix1]
        sub[m] = c[m]
        hsub = hh[iy0:iy1, ix0:ix1]
        hsub[m] = e["z"] + rel[m]
    # a plain relief light, only to see the shapes
    gy, gx = np.gradient(cv2.GaussianBlur(hh, (0, 0), 1.2), 1.0 / pxcm)
    lam = np.clip(1.0 + 1.4 * (-0.5 * gx + 0.6 * gy), 0.55, 1.25)[..., None]
    im = np.clip(im * lam, 0, 1) ** (1 / 2.2)
    r = np.hypot(X, Y - CY)
    im[r > R] = 0.0
    rim = (r > R - 0.36) & (r <= R)
    im[rim] = (0.78, 0.55, 0.28)
    u8 = (im[::-1, :, ::-1] * 255).astype(np.uint8)
    xs, ys, fx, fy = frame_outline()
    inside = ((fx > 0) & (fx < 1) & (fy > 0) & (fy < 1)).astype(np.uint8)
    cn, _ = cv2.findContours(inside, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c_ in cn:
        p = c_[:, 0, :].astype(np.float32)
        q = np.stack([(xs[0, 0] + p[:, 0] * (xs[0, 1] - xs[0, 0]) - AX0) * pxcm, ny - (ys[0, 0] + p[:, 1] * (ys[1, 0] - ys[0, 0]) - y0) * pxcm], 1)
        cv2.polylines(u8, [np.round(q).astype(np.int32)], True, (255, 255, 255), 1, cv2.LINE_AA)
    p = os.path.join(d, f"flat_{COLOUR}.jpg" if COLOUR else "flat.jpg")
    cv2.imwrite(p, u8, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(p, u8.shape)


# --- the stitches ----------------------------------------------------------------------------------------------------------
def paint(e, G, umap, mp):
    """Lay the threads of a patch into the grid, row by row, each later row over the last."""
    pxcm, gx0, gy0 = G["pxcm"], G["x0"], G["y0"]
    H_, W_ = G["h"].shape
    poly = outline(e)
    ix0, ix1 = max(int((poly[:, 0].min() - gx0) * pxcm) - 4, 0), min(int((poly[:, 0].max() - gx0) * pxcm) + 5, W_)
    iy0, iy1 = max(int((poly[:, 1].min() - gy0) * pxcm) - 4, 0), min(int((poly[:, 1].max() - gy0) * pxcm) + 5, H_)
    if ix0 >= ix1 or iy0 >= iy1:
        return
    x = gx0 + (np.arange(ix0, ix1, dtype=np.float32) + 0.5) / pxcm
    y = gy0 + (np.arange(iy0, iy1, dtype=np.float32) + 0.5) / pxcm
    Xs, Ys = np.meshgrid(x, y)
    rho, ang = coords(e, Xs, Ys)
    tab_a, tab_e = e["tab_a"], e["tab_e"]
    ed = np.interp(ang, tab_a, tab_e, left=-1, right=-1)
    rg = np.flatnonzero(((rho >= 0) & (rho < ed + 0.06)).ravel())
    if rg.size == 0:
        return
    rho = rho.ravel()[rg].astype(np.float32)
    ang = ang.ravel()[rg].astype(np.float32)
    ed = ed.ravel()[rg].astype(np.float32)
    # threads wander; a row boundary is not a ring
    iyy, ixx = np.divmod(rg, ix1 - ix0)
    iyy, ixx = iyy + iy0, ixx + ix0
    wand = G["wa"][iyy, ixx]
    petal_ = e["kind"] == "petal"
    rmax0 = float(tab_e.max())
    if petal_:
        ang_t = ang + wand * 0.012 / np.maximum(rho, 0.35)
    else:
        ang_t = ang + wand * 0.01
    rr = rho + min(0.09, 0.2 * rmax0) * G["wb"][iyy, ixx]
    n = rg.size
    H0 = np.full(n, -1.0, np.float32)
    C0 = np.zeros((n, 3), np.float32)
    Rg = np.full(n, 0.3, np.float32)
    rng = np.random.default_rng(5000 + e["seed"])
    rmax = float(tab_e.max())
    rh = e["rh"]
    # rows, each its own height: from the root outward; on a blade (leaf) rows go out from the midrib
    bnd = [0.0]
    while bnd[-1] < rmax + 0.4:
        bnd.append(bnd[-1] + 0.72 * rh * rng.uniform(0.82, 1.18))
    bnd = np.array(bnd)
    rel, pl = relief(e, rho, ang, ed)

    def lay(k, lo, hi, lift, tforce=None):
        rs = np.random.default_rng(7000 + e["seed"] * 101 + k)
        cand = np.flatnonzero((rr >= lo - rh) & (rr < hi + rh * 0.9))
        if cand.size == 0:
            return
        mid = 0.5 * (lo + hi)
        sc = max(mid, 0.2) if petal_ else e["scale"]
        SP = e["sp"]
        ca = ang_t[cand] * sc / SP
        ii = np.floor(ca).astype(np.int64)
        i0, i1 = ii.min(), ii.max()
        nt = int(i1 - i0 + 1)
        ar = ii - i0
        f = (ca - ii).astype(np.float32)
        u5_c = rs.random(nt).astype(np.float32)
        u1, u2, u3, u4, u5 = rs.random(nt).astype(np.float32), rs.random(nt).astype(np.float32), rs.random(nt).astype(np.float32), rs.normal(0, 1, nt).astype(np.float32), rs.normal(0, 1, nt).astype(np.float32)
        alt = np.where((np.arange(nt) + i0) % 2 == 0, 1.0, -1.0).astype(np.float32)
        # the start of each stitch comes out between the threads of the row beneath, long and short by turns
        h_ = hi - lo
        start = lo - h_ * (0.3 + 0.3 * alt + 0.3 * (u1 - 0.5))
        end = hi + h_ * (0.5 + 0.2 * (u2 - 0.5))
        if k == 0:  # the first row starts at the root or midrib, wherever the wander puts it
            start = np.full(nt, -9.0, np.float32)
        ac = (np.arange(nt) + i0 + 0.5) * SP / sc
        eg = np.interp(ac, tab_a, tab_e, left=-1, right=-1).astype(np.float32)
        eg_i = eg + 0.012 * (u3 - 0.3)  # a thread's end does not fall exactly on the line: a real edge is a little uneven
        # a stitch that would reach the edge goes all the way to it: the edge is judged in true rho, the row ends in warped rho, or holes open beside the edge
        reach = end >= eg_i - 0.3
        last = np.where(reach, 1e6, end).astype(np.float32)
        # the ramp is read where the stitch lies
        rc = 0.5 * (np.maximum(start, 0) + np.minimum(end, eg_i))
        xc, yc = unmap(e, np.maximum(rc, 0), ac)
        under = sample_map(umap, mp, xc, yc) * e["under"]
        if tforce is None:
            tt = t_of(e, rc, ac, eg)
            # pleats go a little deeper in their valleys; each stitch its own jitter
            if petal_:
                xr = ac / e["Th"]
                p_ = sum(w * np.sin(np.pi * ff * xr + ph) for ff, ph, w in e["pleats"])
                tt = tt + 0.045 * p_ * np.clip(rc / e["L"], 0, 1)
            # the threads of a row are not one colour: they straddle the shades of the rows either side, which is what makes the blend
            step = h_ / np.maximum(eg, 0.5) * (e["t1"] - e["t0"] if petal_ else 0.8)
            step = np.minimum(step, (0.2 if e["sp"] == S else 0.1) if petal_ else 0.1)
            tt = tt - 0.42 * under + 0.016 * u4 + 2.6 * step * (u5_c - 0.5)
        else:
            tt = tforce + 0.03 * u4 - 0.1 * under
        col = ramp(e["pal"], tt)
        # a dye lot: each stitch a very little different, in lightness only
        col = col * (1.0 + 0.014 * u5)[..., None]
        rolled = (rs.normal(0, 1, nt) * 0.16).astype(np.float32)
        zz = (rs.normal(0, 1, nt) * 0.0009).astype(np.float32)
        tw = rs.uniform(0.05, 0.095, nt).astype(np.float32)
        tp = rs.uniform(0, 6.28, nt).astype(np.float32)
        ro = 0.2 + 0.08 * u2
        rrc = rr[cand]
        keep = (rrc >= start[ar]) & (rrc < last[ar]) & (rho[cand] < eg_i[ar] + 0.004)
        if not keep.any():
            return
        c2 = cand[keep]
        ar2, f2, r2 = ar[keep], f[keep], rrc[keep]
        # thread section, narrowing and dropping towards its ends
        dend = np.minimum(np.minimum(r2 - start[ar2], last[ar2] - r2), eg_i[ar2] - rho[c2])
        tap = np.sqrt(np.clip(dend / 0.035, 0, 1)).astype(np.float32)
        cf = 2 * f2 - 1
        sec = np.sqrt(np.maximum(1.0 - cf**2, 0.0))
        twist = 0.1 * np.sin(2 * np.pi * r2 / tw[ar2] + tp[ar2] + 2.2 * cf)
        hk = HTH * sec * (0.35 + 0.65 * tap) * (1 + twist) + rolled[ar2] * SP * 0.5 * cf + zz[ar2] + 0.004 * tap
        H0[c2] = hk + lift
        # a little darker in the crevices, in its own hue, not grey
        sh = (0.72 + 0.28 * sec**0.55) * (0.94 + 0.06 * tap)
        C0[c2] = col[ar2] * sh[..., None]
        Rg[c2] = ro[ar2]

    for k in range(len(bnd) - 1):
        lay(k, bnd[k], bnd[k + 1], 0.0)
    if e.get("fold_t") is not None:
        ft = np.interp(ang, tab_a, e["fold_t"]).astype(np.float32)
        lip = rho > ft
        if lip.any():
            H_keep, C_keep, R_keep = H0.copy(), C0.copy(), Rg.copy()
            H0[:], C0[:] = -1.0, 0.0
            for k in range(3):
                lay(900 + k, rmax * 0.55 + k * rh, rmax * 0.55 + (k + 1) * rh, 0.0, tforce=0.8)
                lay(903 + k, rmax * 0.55 - (k + 1) * rh, rmax * 0.55 - k * rh, 0.0, tforce=0.8)
            H1, C1, R1 = H0, C0, Rg
            H0, C0, Rg = H_keep, C_keep, R_keep
            use = lip & (H1 >= 0)
            # the crease lies on the petal, with deeper threads in its lee
            lee = np.exp(-np.maximum(ft - rho, 0) / 0.09) * (~lip) * (ft < 1e8)
            C0 = C0 * (1 - 0.24 * lee)[..., None]
            H0[use] = H1[use] + 0.018 * (1 - np.exp(-(rho[use] - ft[use]) / 0.05))
            C0[use], Rg[use] = C1[use], R1[use]
    m = H0 > -0.5
    if not m.any():
        return
    yy, xx = iyy[m], ixx[m]
    G["h"][yy, xx] = (e["z"] + rel[m] + H0[m]).astype(np.float32)
    G["col"][yy, xx] = C0[m]
    G["rough"][yy, xx] = Rg[m]
    G["top"][yy, xx] = 1


def paint_stamens(G):
    fil, knots, carp = stamens()
    pxcm, gx0, gy0 = G["pxcm"], G["x0"], G["y0"]
    H_, W_ = G["h"].shape
    Z = 0.072
    x0, x1 = HEART[0] - 1.1, HEART[0] + 1.1
    y0, y1 = HEART[1] - 1.2, HEART[1] + 1.0
    ix0, ix1 = max(int((x0 - gx0) * pxcm), 0), min(int((x1 - gx0) * pxcm), W_)
    iy0, iy1 = max(int((y0 - gy0) * pxcm), 0), min(int((y1 - gy0) * pxcm), H_)
    if ix0 >= ix1 or iy0 >= iy1:
        return
    sh = (iy1 - iy0, ix1 - ix0)
    Xs, Ys = np.meshgrid(gx0 + (np.arange(ix0, ix1, dtype=np.float32) + 0.5) / pxcm, gy0 + (np.arange(iy0, iy1, dtype=np.float32) + 0.5) / pxcm)
    h = G["h"][iy0:iy1, ix0:ix1]
    col = G["col"][iy0:iy1, ix0:ix1]
    for p0, p1, v in fil:
        m = np.zeros(sh, np.uint8)
        q = np.round((np.array([p0, p1]) - [gx0 + ix0 / pxcm, gy0 + iy0 / pxcm]) * pxcm * 16).astype(np.int32)
        cv2.line(m, tuple(int(c) for c in q[0]), tuple(int(c) for c in q[1]), 1, max(3, int(0.024 * pxcm)), cv2.LINE_8, 4)
        k = m > 0
        h[k] = Z + 0.012 * v
        col[k] = ramp("gold", np.array(0.75 + 0.25 * v, np.float32))
    for x, y, r_ in carp:
        d = np.hypot(Xs - x, Ys - y)
        m = d < r_
        h[m] = (Z + 0.03 + 0.1 * np.sqrt(np.maximum(1 - (d / r_) ** 2, 0)))[m]
        tone = 0.5 + 0.5 * np.sin(np.arctan2(Ys - y, Xs - x) * 7 + d * 12)
        col[m] = (ramp("leaf", 0.92 * np.ones(m.sum())) * (0.86 + 0.14 * tone[m])[..., None])
    for x, y, r_, v in knots:
        i, j = int((y - gy0) * pxcm) - iy0, int((x - gx0) * pxcm) - ix0
        rr = int(r_ * pxcm) + 2
        a0, a1, b0, b1 = max(i - rr, 0), min(i + rr, sh[0]), max(j - rr, 0), min(j + rr, sh[1])
        if a0 >= a1 or b0 >= b1:
            continue
        dd = np.hypot(Xs[a0:a1, b0:b1] - x, Ys[a0:a1, b0:b1] - y)
        m = dd < r_
        ang = np.arctan2(Ys[a0:a1, b0:b1] - y, Xs[a0:a1, b0:b1] - x)
        wrap = 0.5 + 0.5 * np.sin(ang * 2 + dd / r_ * 12 + v * 6)  # thread wound round itself: a French knot
        hh = Z + 0.03 + 0.05 * np.sqrt(np.maximum(1 - (dd / r_) ** 2, 0)) + 0.0055 * wrap
        h[a0:a1, b0:b1][m] = hh[m]
        cc = ramp("gold", np.array(0.25 + 0.75 * v, np.float32))
        col[a0:a1, b0:b1][m] = cc * (0.74 + 0.26 * wrap[m])[..., None]
    G["top"][iy0:iy1, ix0:ix1][np.hypot(Xs - HEART[0], Ys - HEART[1] + 0.08) < 0.95] = 1


def ground(G):
    """The silk: a plain weave with slubs; the binding at its edge; the rim."""
    pxcm = G["pxcm"]
    X, Y = G["X"], G["Y"]
    shape = X.shape
    SW = 0.0205  # weave spacing, cm: estimate. Real silk is finer still; finer than this aliases in the frame
    wx = cv2.resize(G["coarse"][0], (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC) * 0.02
    wy = cv2.resize(G["coarse"][1], (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC) * 0.02
    cu, cv_ = (X + wx) / SW, (Y + wy) / SW
    iu, iv = np.floor(cu).astype(np.int32), np.floor(cv_).astype(np.int32)
    fu, fv = (cu - iu).astype(np.float32), (cv_ - iv).astype(np.float32)
    over = np.mod(iu + iv, 2) == 0
    rng = np.random.default_rng(SEED + 20)
    t_u = rng.normal(0, 1, 16384).astype(np.float32)
    t_v = rng.normal(0, 1, 16384).astype(np.float32)
    # silk weft has slubs: runs of a thread a little thicker and brighter
    su, sv = t_u[np.mod(iu, 16384)], t_v[np.mod(iv, 16384)]
    sec_w = np.sqrt(np.maximum(1 - (2 * fu - 1) ** 2, 0))
    sec_f = np.sqrt(np.maximum(1 - (2 * fv - 1) ** 2, 0))
    bump_w = np.sin(np.pi * fv)
    bump_f = np.sin(np.pi * fu)
    hw = np.where(over, sec_w * bump_w, sec_f * bump_f).astype(np.float32)
    sl = np.where(over, su, sv)
    h = 0.0026 * hw * (1 + 0.1 * sl)
    tone = (1 + 0.026 * sl) * (0.9 + 0.1 * hw)
    base = np.array([0.90, 0.84, 0.70], np.float32)
    col = base[None, None] * tone[..., None]
    col = col * (1.0 + 0.012 * cv2.resize(G["coarse"][2], (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC))[..., None]
    G["h"][...] = h
    G["col"][...] = col
    G["rough"][...] = 0.46
    G["emit"] = (col * 1.35).astype(np.float32)


def rim(G):
    """Binding and bamboo. The bamboo is a split round, 0.34 wide; its lacquer is thin enough to show the fibres of the cane."""
    X, Y = G["X"], G["Y"]
    r = np.hypot(X, Y - CY)
    th = np.arctan2(Y - CY, X)
    Rc = R - 0.17
    dr = (r - Rc) / 0.17
    tube = np.abs(dr) < 1
    fibre = cv2.resize(G["coarse"][3], (X.shape[1], X.shape[0]), interpolation=cv2.INTER_CUBIC)
    # spotted bamboo (湘妃竹), oiled: honey cane with brown blotches stretched along the fibres, each darker at its edge and paler inside
    nods = np.sin(th * R / 0.05 + 7 * np.sin(dr * 2.5 + 11 * th)) * 0.5 + 0.5
    hgt = 0.235 * np.sqrt(np.maximum(1 - dr**2, 0)) + 0.00016 * fibre + 0.00004 * nods
    rs_ = np.random.default_rng(SEED + 40)
    uu, vv = th[tube] * R, dr[tube] * 0.17  # only the rim's pixels: there are a dozen million in the grid
    fb = np.tanh(fibre[tube])
    spot = np.zeros_like(uu, np.float32)
    ring = np.zeros_like(uu, np.float32)
    for _ in range(int(rs_.integers(52, 60) * R / 9.0)):  # as many to the cm as on a 9 cm rim
        uc, vc = rs_.uniform(0.0, np.pi) * R, rs_.uniform(-0.16, 0.16)
        a, b = rs_.uniform(0.09, 0.42), rs_.uniform(0.045, 0.11)
        q_ = np.hypot((uu - uc) / a, (vv - vc) / b) + 0.3 * fb
        spot = np.maximum(spot, sstep(1.05, 0.8, q_) * rs_.uniform(0.55, 1.0))
        ring = np.maximum(ring, sstep(1.1, 0.98, q_) * sstep(0.62, 0.92, q_))
    streak = 0.86 + 0.14 * np.sin(vv * 2 * np.pi / 0.023 + 2.0 * fb)
    cane = np.array([0.58, 0.33, 0.12], np.float32)
    col = cane[None] * streak[..., None]
    col = col + (np.array([0.20, 0.085, 0.03], np.float32) - col) * spot[..., None]
    col = col + (np.array([0.055, 0.022, 0.012], np.float32) - col) * (0.8 * ring)[..., None]
    col = col * (1.0 - 0.28 * sstep(0.45, 1.0, np.abs(dr[tube])))[..., None]
    G["h"][tube] = hgt[tube]
    G["col"][tube] = col
    G["rough"][tube] = 0.24
    G["emit"][tube] = 0
    # a band of silk cord between the ground and the bamboo
    Rb = R - 0.46
    db = (r - Rb) / 0.115
    band = np.abs(db) < 1
    u = th * R
    # oblique threads, slightly proud
    cc = (u + (r - Rb) * 1.1) / 0.027
    ic = np.floor(cc)
    fc = (cc - ic).astype(np.float32)
    secb = np.sqrt(np.maximum(1 - (2 * fc - 1) ** 2, 0))
    rs = np.random.default_rng(SEED + 31).normal(0, 1, 8192).astype(np.float32)
    hb = 0.03 * np.sqrt(np.maximum(1 - db**2, 0)) + 0.0065 * secb
    colb = np.array([0.80, 0.66, 0.44], np.float32)[None, None] * (0.72 + 0.28 * secb)[..., None] * (1 + 0.04 * rs[np.mod(ic.astype(np.int64), 8192)])[..., None]
    G["h"][band] = hb[band]
    G["col"][band] = colb[band]
    G["rough"][band] = 0.3
    G["emit"][band] = 0
    return tube | band


def loose_ends(G):
    """A few stray filaments and a loose tail or two lying on the ground."""
    rng = np.random.default_rng(SEED + 41)
    pxcm, gx0, gy0 = G["pxcm"], G["x0"], G["y0"]
    H_, W_ = G["h"].shape
    spots = [(3.0, 3.7, "coral"), (-7.1, 6.0, "coral"), (0.8, 8.15, "magenta"), (6.6, 6.3, "jade"), (2.4, 7.9, "wing"), (7.0, 3.5, "leaf")]
    for x, y, pal in spots:
        a = rng.uniform(0, 6.28)
        L = rng.uniform(0.22, 0.55)
        ts = np.linspace(0, 1, 50)
        ang = a + rng.uniform(-1.8, 1.8) * ts
        cx = x + np.cumsum(np.cos(ang)) * L / 50
        cy = y + np.cumsum(np.sin(ang)) * L / 50
        ix0, ix1 = max(int((cx.min() - gx0) * pxcm) - 3, 0), min(int((cx.max() - gx0) * pxcm) + 4, W_)
        iy0, iy1 = max(int((cy.min() - gy0) * pxcm) - 3, 0), min(int((cy.max() - gy0) * pxcm) + 4, H_)
        if ix0 >= ix1 or iy0 >= iy1:
            continue
        m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
        q = np.round(np.stack([(cx - gx0) * pxcm - ix0, (cy - gy0) * pxcm - iy0], 1) * 16).astype(np.int32)
        cv2.polylines(m, [q], False, 1, max(2, int(0.008 * pxcm)), cv2.LINE_8, 4)
        k = m > 0
        G["h"][iy0:iy1, ix0:ix1][k] += 0.006
        G["col"][iy0:iy1, ix0:ix1][k] = ramp(pal, np.array(0.72, np.float32))
        G["emit"][iy0:iy1, ix0:ix1][k] = 0


def build(dens, win=None):
    pxcm = 320.0 * dens
    x0, x1, y0, y1 = win if win else (AX0, AX1, AY0, AY1)
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M", "px/cm", pxcm, "thread px", round(S * pxcm, 1), flush=True)
    X, Y = np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    # the slow fields are made on a fixed grid, so that a change of quality or window does not move the picture
    cx = 80.0
    cs = (int((AY1 - AY0) * cx), int((AX1 - AX0) * cx))
    cgrid = {k: fbm(cs, cx, lo, hi, b, SEED + i) for i, (k, lo, hi, b) in enumerate((("wa", 0.3, 2.0, 2.6), ("wb", 0.25, 1.2, 2.2), ("gu", 0.5, 3.0, 2.6), ("gv", 0.5, 3.0, 2.6), ("gt", 0.3, 3.0, 2.0), ("wave", 1.0, 7.0, 3.0), ("puck", 0.2, 0.8, 2.0)))}

    def up(f):
        ix = np.linspace((x0 - AX0) * cx, (x1 - AX0) * cx, nx, dtype=np.float32)
        iy = np.linspace((y0 - AY0) * cx, (y1 - AY0) * cx, ny, dtype=np.float32)
        Mx, My = np.meshgrid(ix, iy)
        out = cv2.remap(f, Mx, My, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        return out

    wf = up(cgrid["wa"])
    G = dict(pxcm=pxcm, x0=x0, y0=y0, X=X, Y=Y, h=np.zeros(shape, np.float32), col=np.zeros((*shape, 3), np.float32), rough=np.zeros(shape, np.float32), top=np.zeros(shape, np.uint8), wa=wf, wb=up(cgrid["wb"]))
    # noise on the fine grid only where it is wanted, by fibre along the cane
    fib = fbm(shape, pxcm, 0.012, 0.08, 1.2, SEED + 15)
    G["coarse"] = [up(cgrid["gu"]), up(cgrid["gv"]), up(cgrid["gt"]), fib]
    ground(G)
    els = design()
    umaps, acc, mp = under_maps(els)
    n = 0
    for i, e in enumerate(els):
        if isinstance(e, str):
            paint_stamens(G)
            continue
        paint(e, G, umaps[i], mp)
        n += 1
    loose_ends(G)
    h = G["h"]
    # the silk puckers a little where the work has drawn it up, and lies in slow waves on the frame
    d = cv2.distanceTransform((G["top"] == 0).astype(np.uint8), cv2.DIST_L2, 3).astype(np.float32) / pxcm
    z = h + 0.006 * up(cgrid["wave"]) + 0.0035 * up(cgrid["puck"]) * np.exp(-d / 0.55) * (d > 0)
    r = np.hypot(X, Y - CY)
    band = rim(G)
    z = np.where(band, G["h"], z)
    # the ground dips a very little towards the middle, away from the rim
    z = z - 0.012 * (1 - (r / R) ** 2)
    alpha = sstep(0.008, 0.0, r - R)
    # floss carries a tinted highlight (a stand-in, see the top of this file); the ground and the lacquer do not
    metal = np.where((G["top"] > 0) & ~band, METAL, 0.0).astype(np.float32)
    metal[band] = 0.0
    metal[(r > R - 0.34)] = 0.0
    # thin silk glows in its own colour: a stand-in for the light floss and ground pass along and through themselves
    emit = np.where((G["top"] == 0)[..., None], G["emit"], G["col"] * THREAD_GLOW)
    emit[band] = 0
    print("painted", n, "patches", flush=True)
    return np.stack([X, Y, z], -1).astype(np.float32), np.clip(G["col"], 0, 1), np.clip(G["rough"], 0.05, 1), alpha.astype(np.float32), emit.astype(np.float32), metal


# --- a shaded look at real stitches -------------------------------------------------------------------
def stitch_view(win):
    """Lambert plus two broad lobes on the height field, with no shadows: a stand-in for the render, only to judge the threads. Written at 135 px/cm (what a final shows at 100%) and doubled."""
    d = os.path.join(OUT, NAME)
    P, C, Ro, A, Em, _ = build(1.0, win)
    pxcm = 320.0
    h = P[..., 2]
    gy, gx = np.gradient(h, 1.0 / pxcm)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    v = view_dir(-90.0, EL)
    im = 0
    for azel, wgt in (((110.0, 74.0), 0.55), ((30.0, 18.0), 0.12)):
        l = view_dir(*azel)
        lam = np.clip((n * l).sum(-1), 0, 1)
        hv = (l + v) / np.linalg.norm(l + v)
        spec = np.clip((n * hv).sum(-1), 0, 1) ** 70
        im = im + wgt * (C * lam[..., None] + 0.18 * spec[..., None])
    im = im + 0.25 * C + 0.1 * Em
    im = np.clip(im * 1.25, 0, 1) ** (1 / 2.2)
    im = (im[::-1, :, ::-1] * 255).astype(np.uint8)
    s = cv2.resize(im, None, fx=135 / pxcm, fy=135 / pxcm * np.sin(np.radians(EL)), interpolation=cv2.INTER_AREA)
    tag = "_".join(str(int(w * 10)) for w in win)
    p = os.path.join(d, f"stitch_{tag}.jpg")
    cv2.imwrite(p, s, [cv2.IMWRITE_JPEG_QUALITY, 94])
    print(p, s.shape)


def scene_for(q, npz, cam, focus):
    v = view_dir(-90.0, EL)
    # the window is not at the mirror direction: the half vector leans to the upper left, so threads across that lean flash and threads along it stay in their colour
    lean = np.array(LEAN, float)
    h = np.array([lean[0], lean[1], 1.0])
    h /= np.linalg.norm(h)
    r = 2 * h.dot(v) * h - v
    lw = focus + r * 70.0
    return {
        "camera": cam,
        "meshes": [{"name": "fan", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Alpha": "alpha", "Metallic": "metal", "Specular IOR Level": SPEC, "Sheen Weight": 0.06, "Sheen Roughness": 0.4, "Emission Color": "emit", "Emission Strength": EMIT}}],
        "lights": [
            {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": focus.tolist(), "size": [170, 120], "sigma": WSIG, "L": WINDOW_L, "rgb": [1.0, 0.985, 0.96]},
            {"type": "gradient", "name": "rimlight", "loc": (focus + np.array([62, 6, 34])).tolist(), "target": focus.tolist(), "size": [60, 90], "sigma": [14, 34], "L": 1.6, "rgb": [1.0, 0.97, 0.92], "hide_in_diffuse": True},
            {"name": "rake", "loc": (focus + np.array([-34, 26, 13])).tolist(), "target": focus.tolist(), "size": [9, 9], "watts": RAKE, "rgb": [1.0, 0.95, 0.88]},
            {"name": "fill", "loc": (focus + np.array([8, 8, 42])).tolist(), "target": focus.tolist(), "size": [60, 60], "watts": FILL, "rgb": [1.0, 0.985, 0.97], "hide_in_gloss": True},
        ],
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }


DEV = {"exposure": 0.15, "contrast": 1.14, "saturation": 1.08, "black": 0.0006, "grain": 1.05, "sharpen": 0.26, "halation": 0.05, "glare": 0.003, "vignette": 0.22}


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    use_colour(sys.argv[2] if len(sys.argv) > 2 and q in ("flat", "preview", "mid", "final") else None)
    if q == "flat":
        flat_view()
        return
    if q == "stitch":
        stitch_view(tuple(float(a) for a in sys.argv[2:6]))
        return
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    focus = np.array([-0.6, FOCUS_Y, 0.06])
    cam, sag = camera(APERTURE, focus)
    print("sag", round(float(sag), 3), flush=True)
    if q == "crop":  # one patch at the size a final shows it, so threads can be judged cheaply: crop cx cy
        cx, cy = float(sys.argv[2]), float(sys.argv[3])
        use_colour(sys.argv[4] if len(sys.argv) > 4 else None)
        tag = f"crop_{COLOUR or 'pink'}_{int(cx * 10)}_{int(cy * 10)}"
        Wc = 960 / 135.0
        win = (cx - Wc / 2 - 0.3, cx + Wc / 2 + 0.3, max(cy - 2.6, AY0), min(cy + 2.6, AY1))
        P, C, Ro, A, Em, Me = build(1.0, win)
        npz = os.path.join(d, f"mesh.{tag}.npz")
        np.savez(npz, P=P, col=C, rough=Ro, alpha=A, emit=Em, metal=Me)
        tgt = np.array([cx, cy, 0.05])
        camc = frame_camera(tgt, view_dir(-90.0, EL), Wc, DIST, aperture_mm=APERTURE, focus_point=focus)
        shoot(NAME, scene_for(q, npz, camc, focus), "preview", develop=DEV, tag=tag)
        os.remove(npz)
        return
    dens = {"preview": 0.6, "mid": 0.8, "final": 1.0}[q]
    P, C, Ro, A, Em, Me = build(dens)
    # the coloured candidates have their own names, so they never overwrite the film's final.*
    tag = {"lv": "cand", "lan": "cand_lan"}[COLOUR] if COLOUR and q == "final" else (f"{COLOUR}_{q}" if COLOUR else q)
    npz = os.path.join(d, f"mesh.{tag}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, alpha=A, emit=Em, metal=Me)
    del P, C, Ro, A, Em, Me
    shoot(NAME, scene_for(q, npz, cam, focus), q, develop=DEV, tag=tag)
    os.remove(npz)


if __name__ == "__main__":
    main()
