"""Shot 73: the oil-paper umbrella in a dark room, lit from behind, seen from inside the dome at the v1 camera. Its far rim is the arc. A still.

    python3 -I v2/stills/s73_heisan.py [sketch|preview|mid|final]

An improvement on the old black-background still (out/v2/s21_youzhisan/v1_final.jpg; script at git cfce37d), keeping v1's view. A version with the light low behind sharp lacing (out/v2/s73_heisan/cand_center.jpg) was judged less beautiful than v1. So this one goes back to v1's camera, ribs, lamp, lens and development, and repairs only what the blind review found wrong with v1.

v1's numbers: camera, lens, aperture, roll, dome, 32 ribs, lamp and fill positions, development.
What differs from v1:
- the paper is s21's: fibres laid in the plane, oil, panels and folds each different;
- the rain is old rain, stain by stain (rain() below): v1's rings looked copied;
- rib tips under the paper, each pared and bound on its own, and the threads and windings are s21's build, on v1's rings;
- the wall is very nearly black, not exactly 0.
LEFT OUT, knowingly: the rim thread (it would hang in the air over paper this slack), the stretchers, the shaft and the runner. At this camera the shaft and the runner pass about 12 cm from the lens and would be a dark smear down the middle. With the stretchers in, the render has two dark smudges on the lacing at about x .40 and .60; they go when the stretchers go. Cause not traced. v1 had none of these either.
ESTIMATES, none measured: lamp, fill, absorption, the rain, s21's sizes. Rib width is v1's look, set by eye, not measured on a real umbrella.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, color, fbm, shoot, sstep
from s21_lib import look_at_camera
from translib import SOFT, save
from vessel import project

NAME = "s73_heisan"
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s21_youzhisan.py")
_src = open(_p).read()
U = {"__file__": _p, "__name__": "s21_parts"}
# What made v1's rim and ribs beautiful, on s21's parts. Each change asserts, so that a change in s21 is seen rather than silently lost.
for _a, _b in (
    ("scal = rng.uniform(0.1, 0.32, NRIB)", "scal = rng.uniform(0.35, 0.95, NRIB)"),  # the paper hangs in a deep curve from tip to tip
    ("z = prof(Rr) - 0.62 * deep * fold * Ru", "z = prof(Rr) + 2.4 * deep * (1.0 - np.abs(T - tc) / np.maximum(tc, 1.0 - tc)) ** 1.15 * (0.2 + 0.8 * Ru)"),  # v1's soul: each panel a tent with a ridge down the middle, so that against the black the rim is a row of peaks. The ridge wanders and differs panel to panel (s21's tc, deep)
    ("- 0.55  # the rib tips stand out", "+ 0.02  # the rib tips stand out"),  # hardly at all: the paper is folded over them. Standing tips read as CG caps to a blind reviewer
    ("(1.05 - 0.45 * s**3) * (1 + 0.04 * smooth1d(ns, 60, rng))", "(1.05 - 0.45 * s**3) * (1 + 0.04 * smooth1d(ns, 60, rng)) * (1.0 - rng.uniform(0.35, 0.65) * sstep(rng.uniform(0.93, 0.965), 1.0, s))"),  # each end pared by hand
    ("tips[i] - rng.uniform(1.5, 2.2), tips[i] - 0.45, [0.2, 0.025, 0.02], 26)", "tips[i] - rng.uniform(0.6, 1.5), tips[i] - rng.uniform(0.3, 0.6), [0.2, 0.025, 0.02], 13)"),  # a short binding, each its own
    ("* 0.006 + rng.normal(0, 0.012, NRIB)[I % NRIB]", "* 0.022 + rng.normal(0, 0.03, NRIB)[I % NRIB]"),  # the ridge wanders: a ruled one reads as a hard straight edge between a lit and a dark face
    ("z = z + 0.05 * sample(F, \"patches\", x, y)", "z = z + 0.17 * sstep(0.1, 1.2, d_rib) * sample(F, \"patches\", x, y)"),  # paper that has been opened and closed many times; none of it at the rib, or the paper passes through the rib and hides a length of it
    ("bands = [(RIB_J + 1.8, 0.7, [0.05, 0.11, 0.26], 9), (RIB_J + 3.4, 0.8, [0.66, 0.60, 0.46], 11), (RIB_J + 5.0, 0.6, [0.30, 0.055, 0.04], 9), (RIB_J + 6.1, 0.35, [0.05, 0.14, 0.10], 6)]", "bands = [(RIB_J + a, 0.95, c, 12) for a, c in LACE]"),  # v1's big diamonds
    ("(RIB_J - 0.55, RIB_J + 0.55, [0.55, 0.5, 0.38], 14))", "*[(RIB_J + a - 1.25, RIB_J + a + 1.25, c, 26) for a, c in LACE])"),  # and its windings on each rib where the bands cross it
    ("- 0.07 * oil", "- 0.04 * oil"),  # s21's oil streaks, strong against this light, read as dragged noise
    ("0.05 * 2 * np.pi / NRIB, NRIB)", "0.085 * 2 * np.pi / NRIB, NRIB)"),  # hand-spaced, visibly
    ("wob = 0.03 * smooth1d(ns, 80, rng)", "wob = 0.075 * smooth1d(ns, 80, rng)"),  # split bamboo is not ruled
    ("+ 0.14 * tide", "+ 0.025 * tide"),  # s21's tide lines read as contours on a map; the rain below brings its own
    ("w = rng.uniform(0.21, 0.28)", "w = rng.uniform(0.34, 0.46)"),  # v1's ribs are bolder
    ("hw = 0.26 * np.clip", "hw = 0.44 * np.clip"),  # and the windings go round them
    ("    P = world(x, y, z)\n    return P.astype(np.float32), col", "    tr = RAIN(x, y, tr)\n    P = world(x, y, z)\n    return P.astype(np.float32), col"),
):
    assert _a in _src, _a
    _src = _src.replace(_a, _b)
_src, _n = re.subn(r"\n        # rim thread.*?rads\.append\(0\.04\)", "", _src, flags=re.S)
assert _n == 1
exec(compile(_src[: _src.rindex("\nmain()")], _p, "exec"), U)

# v1's camera and dome
C = np.array([0.0, -12.0, -20.0])
T = np.array([0.0, 40.0, 2.5])
LENS = 20.0
ROLL = 180.0
APERTURE = 26.0
DOME = 15.0
R = 45.0
NRIB = 32
RIB_J = 0.0  # the lacing is placed by LACE; this is 0 so that those are plain radii
LACE = [(22.0, [0.75, 0.73, 0.66]), (24.6, [0.05, 0.16, 0.42]), (27.3, [0.72, 0.5, 0.08]), (30.0, [0.04, 0.3, 0.2])]  # v1's rings and colours; against the light they read dark

# v1's lamp and fill
LAMP_LOC, LAMP_TGT, LAMP_SIZE, LAMP_SPREAD, LAMP_W = [-48.0, 58.0, 62.0], [4.0, 36.0, 0.0], 12.0, 60.0, 32000.0
FILL_LOC, FILL_TGT, FILL_W = [10.0, -30.0, -70.0], [0.0, 25.0, 5.0], 8000.0
SIGMA = color([0.06, 2.9, 5.0])  # absorption per layer of paper with its pigment and oil


def prof(r):
    return DOME * (1.0 - (np.abs(r) / R) ** 2)


def basis():
    """The umbrella stands straight up, as in v1."""
    return np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])


def rain(x, y, tr, seed=2173):
    """Old rain on the paper, seen against the light. Dried water: uneven blots a little clearer than the paper round them, each with a broken, darker tide line where it stopped. They lie in patches, overlap, and more of them lie towards the rim; a few fine trails run outwards; only specks are still wet. A blind reviewer read round rings with a bright focus as bubbles, so there are none. Nothing is copied or mirrored."""
    S = 30.0
    n = int(2 * (R + 2) * S)
    c = (R + 2) * S
    rng = np.random.default_rng(seed)
    patch = fbm((n // 8, n // 8), S / 8, 5.0, 30.0, 2.6, seed)
    patch = (patch - patch.mean()) / patch.std()

    def field(lo, hi, sd):
        f = fbm((n // 2, n // 2), S / 2, lo, hi, 2.2, sd)
        return cv2.resize(np.clip((f - f.mean()) / f.std(), -2.5, 2.5).astype(np.float32), (n, n), interpolation=cv2.INTER_CUBIC)

    warp, grit = field(0.35, 3.5, seed + 1), field(0.12, 1.0, seed + 2)
    M = np.ones((n, n), np.float32)

    def place():
        while True:
            r, a = rng.uniform(13.0, 44.5), np.pi / 2 + rng.uniform(-1.2, 1.2)
            px, py = r * np.cos(a), r * np.sin(a)
            p = np.exp(1.5 * patch[int((py * S + c) / 8), int((px * S + c) / 8)]) * (0.25 + 0.75 * (r / R) ** 2)
            if rng.uniform() < 0.16 * p:
                return px, py

    def polar(px, py, h):
        cx, cy = int(px * S + c), int(py * S + c)
        ys, xs = np.mgrid[cy - h : cy + h + 1, cx - h : cx + h + 1]
        dx, dy = (xs - c) / S - px, (ys - c) / S - py
        rl = max(np.hypot(px, py), 1e-3)
        return ys, xs, (dx * px + dy * py) / rl, (-dx * py + dy * px) / rl  # u: outwards, down the dome

    def stain(px, py, rd, clear, tide):
        ys, xs, u, v = polar(px, py, int(rd * S * 2.6) + 3)
        th = np.arctan2(v, u)
        w = np.ones_like(th)
        for k in range(2, 6):
            w += 0.16 / (k - 0.9) * rng.normal(0, 1) * np.cos(k * th + rng.uniform(0, 2 * np.pi))
        rho = np.hypot(u / rng.uniform(1.0, 1.5), v) / (rd * np.maximum(w, 0.4)) + 0.2 * warp[ys, xs] + 0.05 * grit[ys, xs]
        soft = 0.07 + 0.09 * (grit[ys, xs] + 2.5) / 5.0
        inside = sstep(1.0 + soft, 1.0 - soft, rho)
        line = np.exp(-(((rho - 0.99) / 0.055) ** 2)) * sstep(-0.3, 0.7, warp[ys[::-1, ::-1], xs[::-1, ::-1]] + 0.6 * grit[ys, xs])  # stops and starts
        M[ys, xs] *= (1.0 + clear * inside * (0.65 + 0.14 * grit[ys, xs]) - tide * line).astype(np.float32)

    def speck(px, py, rd):
        ys, xs, u, v = polar(px, py, int(rd * S * 2.0) + 3)
        d = np.hypot(u, v) / rd + 0.25 * grit[ys, xs]
        M[ys, xs] *= (1.0 - rng.uniform(0.15, 0.4) * sstep(1.2, 0.7, d) * sstep(0.1, 0.7, d) + rng.uniform(0.15, 0.6) * sstep(0.55, 0.0, d)).astype(np.float32)

    for _ in range(30):
        px, py = place()
        stain(px, py, float(np.clip(np.exp(rng.normal(np.log(0.75), 0.55)), 0.25, 2.4)), rng.uniform(0.02, 0.11), rng.uniform(0.04, 0.17))
    tl = np.zeros((n, n), np.float32)
    for _ in range(9):
        px, py = place()
        a = np.arctan2(py, px)
        pts = [np.array([px, py])]
        for _ in range(int(rng.integers(5, 16))):
            a += rng.normal(0, 0.05)
            pts.append(pts[-1] + 0.5 * np.array([np.cos(a), np.sin(a)]))
        q = np.array([[(p[0] * S + c) * 16, (p[1] * S + c) * 16] for p in pts], np.int32)
        cv2.polylines(tl, [q], False, float(rng.uniform(0.3, 0.9)), int(rng.integers(1, 3)), cv2.LINE_AA, 4)
    M *= 1.0 - 0.09 * cv2.GaussianBlur(tl, (0, 0), 0.9)
    for _ in range(45):
        px, py = place()
        speck(px, py, float(rng.uniform(0.03, 0.11)))
    v = cv2.remap(M, (x * S + c).astype(np.float32), (y * S + c).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.clip(tr * v[..., None], 0, 1)


U.update(NAME=NAME, R=R, H=DOME, NRIB=NRIB, RIB_J=RIB_J, LACE=LACE, SIGMA=SIGMA, prof=prof, basis=basis, RAIN=rain)
# only the far part of the dome is in frame: the vertices go there
U["seen"] = lambda a: np.abs((a - np.pi / 2 + np.pi) % (2 * np.pi) - np.pi) < np.radians(75)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"sketch": 0.3, "preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    ang = U["rib_angles"](21)
    tips = R + np.random.default_rng(23).normal(0, 0.2, NRIB)
    P, col, tr, edge = U["paper"](dens, ang, tips)
    p_paper = os.path.join(d, f"paper.{q}.npz")
    np.savez(p_paper, P=P, col=col, tr=tr)
    p_ribs = save(os.path.join(d, "ribs.npz"), U["ribs"](ang, tips))
    p_lace = save(os.path.join(d, "lace.npz"), U["lacing"](ang))
    p_wrap = save(os.path.join(d, "wraps.npz"), U["wraps"](ang, tips))

    focus = np.array([0.0, R - 0.5, 0.0])
    cam = look_at_camera(C, T, LENS, focus, aperture_mm=APERTURE, roll=ROLL)
    rim = P[-1].reshape(-1, 3)
    rim = rim[rim[:, 1] > 8.0]
    x, y, _ = project(cam, rim)
    on = (x > 0) & (x < 1)
    print(f"apex y {y[on].min():.3f} at x {x[on][int(np.argmin(y[on]))]:.3f}; rim at frame edges y {y[on][np.argmin(x[on])]:.3f}, {y[on][np.argmax(x[on])]:.3f}", flush=True)

    PAPER = {"k": 0.66, "rough": 0.42, "spec": 0.16}
    WOOD = {"k": 0.45, "rough": 0.36, "spec": 0.42, "smooth": True}
    meshes = [
        {"name": "paper", "npz": p_paper, "shader_py": SOFT, "params": PAPER},
        {"name": "ribs", "npz": p_ribs, "shader_py": SOFT, "params": WOOD},
        {"name": "lace", "npz": p_lace, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.38, "spec": 0.5, "sheen": 0.5}},
        {"name": "wraps", "npz": p_wrap, "shader_py": SOFT, "params": {"k": 0.0, "rough": 0.4, "spec": 0.5, "sheen": 0.4}},
    ]
    lights = [
        {"name": "lamp", "loc": LAMP_LOC, "target": LAMP_TGT, "size": [LAMP_SIZE, LAMP_SIZE], "spread": LAMP_SPREAD, "watts": LAMP_W, "rgb": [1.0, 0.93, 0.82], "hide_in_gloss": True},
        {"name": "fill", "loc": FILL_LOC, "target": FILL_TGT, "size": [90, 60], "watts": FILL_W, "rgb": [1.0, 0.62, 0.42]},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "sky": {"top": [0.0034, 0.0032, 0.0031], "glow": [0.0052, 0.0049, 0.0047], "y0": 0.3, "h": 0.6, "x0": 0.45, "mottle": 0.0},
        "bounces": 16,
        "diffuse_bounces": 10,
        "glossy_bounces": 4,
        "transmission_bounces": 12,
        "spp": {"preview": 128, "mid": 192, "final": 512},
    }
    if q == "sketch":
        scene["spp"] = 64
    look = {"exposure": -0.4, "contrast": 1.42, "saturation": 1.02, "black": 0.0008, "grain": 1.2, "sharpen": 0.25, "halation": 0.025, "glare": 0.002}
    shoot(NAME, scene, "preview" if q == "sketch" else q, tag=q, develop=look)


main()
