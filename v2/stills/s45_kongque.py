"""Shot 45: the eye of a peacock's train feather. The tips of its barbs make the arc against black.

    python3 -I v2/stills/s45_kongque.py [layout|preview|mid|final] [--tag=NAME]
    python3 -I v2/stills/s45_kongque.py flick [layout|check|preview|final]    the barbs blown over, solved in s45_flick.py; goes to out/v2/s45_kongque_flick_move_{preview,final}

Built like the real thing, every barb and barbule is geometry with parallax and shadow:
- a rachis from below, ending in the V notch of the heart; barbs leave it on both sides and curve up;
- each barb is a dark ramus with two rows of barbules, slanting forward and arched, so that each row has a bright ridge and a dark furrow;
- past the green the barbs part and clump into fringes with black between them;
- colour lives on the barbules only and changes barb by barb, barbule by barbule: zone edges are stepped, never smooth.

ESTIMATES (eyeballed from ref/peacock2 photographs, nothing measured on a specimen): frame width 10 cm, heart width 1.15 cm, zone
outlines, barb spacing ~0.5 mm, barbule length ~0.5 mm, attachment angles.
DELIBERATE DEPARTURES from the real feather: barbule spacing 72 um, about 1.5x our estimate of the real one, so that 2560 px can resolve
the hatching. The zones are pressed closer together and the fringe is shorter than a real one, so that the eye fits under the arc.
Reworked after blind review ("barbules too fine and broken, sparkles like noise, no hooked structure") against ref/peacock2 at 100%: measured on the 1920 px full-eye photograph (about 350 px/cm by
eye), barbules are about 5 px apart, i.e. 0.014 cm, and read as chevrons. So: closer framing (8.2 cm), barbules at that spacing, tips curving over and interleaving with the next barb's row; far less per-facet scatter and
fewer flashes; muted olive-gold instead of the clown-coloured copper; barbs loosen into hair past the green instead of zipping into spikes; a real aperture.
SUBSTITUTES: structural colour is a coloured rough mirror with a Bragg-like angle shift, see s45_shader.py. Barbules have 5 facets;
a real one has many more nodes. Preview and mid use wider, fewer barbules; only final has the full count.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, ROOT, fbm, frame_camera, shoot

NAME = "s45_kongque"
SEED = 45
MARGIN = 0.0  # how far outside the frame geometry is kept, as a fraction of it: a barb that moves can come in from outside
W = 8.2  # frame width at the subject (cm), estimate
DIST = 30.0
AZ, EL = np.radians(9.0), np.radians(-52.0)
ROLL = 8.0  # the azimuth shears the plane; this levels the arc, and leaves the rachis slightly off the vertical
#  # the camera is low and a little to the right: the top of the feather recedes
APEX = (0.50, 0.47)
EYE_Y = 0.80
Z_APEX = 2.72
APEX_SINK = -0.12  # the crown of the fringe sits above the mean outline: aim the camera at the outline minus this  # crown of the fringe in the plane of the feather, above the centre of the heart

# colour ramp: lam -> colour of the reflection. Hand-made from the photographs, a substitute for a computed spectrum.
RAMP = [
    [395, 0.06, 0.0, 0.48],
    [430, 0.02, 0.03, 1.0],
    [460, 0.0, 0.16, 1.0],
    [485, 0.0, 0.5, 1.0],
    [505, 0.0, 0.78, 0.62],
    [530, 0.05, 0.72, 0.14],
    [555, 0.3, 0.68, 0.03],
    [578, 0.66, 0.54, 0.12],
    [605, 0.70, 0.42, 0.14],
    [635, 0.66, 0.28, 0.13],
    [670, 0.6, 0.15, 0.1],
    [705, 0.55, 0.2, 0.38],
    [745, 0.42, 0.2, 0.6],
]


# --- the shape of the feather in its own plane (x right, z up, cm), centre of the heart at the origin ---------------
def surface(x, z):
    """Depth y (away from the camera is +): the vane is convex across and curls towards the camera at the top; slow ripples."""
    y = 0.03 * x * x - 0.03 * np.maximum(z - 0.3, 0.0) ** 2
    return y + RIP(x, z)


_rip = None
EDGE = None  # slow noise on the zone edges


def RIP(x, z):
    return 0.04 * field(_rip, x, z)


GRID = (-8.0, -12.0, 16.0 / 512)  # x0, z0, cm per cell of the fixed grids


def field(f, x, z):
    i = np.clip(((x - GRID[0]) / GRID[2]).astype(np.float32), 0, f.shape[1] - 1.001)
    j = np.clip(((z - GRID[1]) / GRID[2]).astype(np.float32), 0, f.shape[0] - 1.001)
    return cv2.remap(f, i.reshape(-1, 1), j.reshape(-1, 1), cv2.INTER_LINEAR).reshape(np.shape(x))


GREEN = (0.0, 0.30, 2.0, 1.97)


def ell(x, z, cx, cz, rx, rz):
    return np.sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2)


def heart_q(x, z):
    """< 1 inside the heart: a round shape with a V notch cut up from below, a little off the axis."""
    xx, zz = x, (z - 0.04) / 1.14
    th = np.arctan2(xx, zz)  # 0 up, +-pi down
    r = np.hypot(xx, zz) + 1e-6
    dn = np.abs(np.abs(th) - np.pi)
    R = 0.575 * (1.0 + 0.1 * np.cos(2 * th) * 0.5 + 0.05 * np.sin(th))
    R = R * (1.0 - 0.72 * np.exp(-((dn / 0.40) ** 2)))
    return r / R


def lobes(x, z, d=0.0):
    """Zone edges: lam (index into the ramp) and amp (reflectance) at a point of the plane; d shifts the edges (one barb or one barbule)."""
    qh = heart_q(x, z) + d + 0.03 * field(EDGE[0], x, z)
    rr = ell(x, z, 0.035, -0.14, 0.97, 1.04) + d + 0.02 * field(EDGE[1], x, z)  # blue ring: thin at the top, thick below
    rc = ell(x, z, -0.07, 0.30, 1.50, 1.50) + d + 0.022 * field(EDGE[2], x, z)  # copper
    rg = ell(x, z, *GREEN) + d + 0.03 * field(EDGE[3], x, z)  # green
    lam = np.zeros_like(x, np.float32)
    amp = np.zeros_like(x, np.float32)

    # outside: the fringes
    fringe = rg >= 1.0
    lam[fringe] = 548.0
    amp[fringe] = 0.85

    m = rg < 1.0  # green band
    t = np.clip((rc - 1.05) / (0.62 + 1e-6), 0, 1)
    lam[m] = np.interp(t[m], [0, 0.22, 0.55, 1.0], [518, 545, 566, 540])
    amp[m] = 1.0

    rim = 1.045 + 0.016 * field(EDGE[3], x * 1.6, z * 1.6)  # the rim comes and goes
    m = rc < rim  # pink to violet rim
    lam[m] = 660.0 + 22.0 * field(EDGE[1], x * 1.7, z * 1.7)[m]
    amp[m] = 0.45

    m = rc < 1.0  # copper to gold
    d1, d2 = np.maximum(rr - 1.0, 0.0), np.maximum(1.0 - rc, 0.0) * 1.6
    t = d1 / (d1 + d2 + 1e-5)
    lam[m] = np.interp(t[m], [0, 0.06, 0.2, 0.55, 0.85, 1.0], [538, 562, 575, 590, 606, 628])
    amp[m] = 0.92

    m = rr < 1.0  # the ring: royal blue, cyan, turquoise, a thin line of green
    dh = np.maximum(qh - 1.0, 0.0) * 0.45
    do = np.maximum(1.0 - rr, 0.0)
    t = dh / (dh + do + 1e-5)
    lam[m] = np.interp(t[m], [0, 0.2, 0.55, 0.85, 1.0], [440, 458, 480, 502, 528])
    amp[m] = 1.1

    m = qh < 1.0  # the heart: dark, a few blue-violet glints
    lam[m] = 425.0
    amp[m] = 0.075
    return lam, amp


NFAN = 40  # barbs of the fan over the heart, per side


def attach(rng):
    """Distances below the tip of the rachis where barbs leave it: tight at the tip (the fan over the heart)."""
    a, out = 0.0, []
    while a < 11.0:
        out.append(a)
        sp = 0.015 if len(out) <= NFAN else 0.015 + 0.04 * (1.0 - np.exp(-(a - 0.6) / 0.5))
        a += sp * rng.uniform(0.82, 1.18)
    return np.array(out)


Z_TIP = -0.13  # tip of the rachis, inside the notch
DS = 0.01  # step along a barb (cm)
NS = 1300


def envelope(x, z):
    """1 on the outline of the feather: the arc."""
    zc, b = 0.5, Z_APEX - 0.5
    return np.sqrt((x / 6.6) ** 2 + (np.maximum(z - zc, 0.0) / b) ** 2)


def grow_side(side, seed):
    """All barbs of one side on a common arc-length grid: paths (n, NS, 2) in the plane, and how many samples each one has."""
    rng = np.random.default_rng(seed + (0 if side > 0 else 1))
    a = attach(rng)
    n = a.size
    s = np.arange(NS, dtype=np.float32)[None, :] * DS
    # the angle from the rachis at the base: a fan near the tip, about 50 deg lower down
    fan = 0.5 + 1.4 * np.arange(n)
    phi0 = np.radians(np.minimum(fan, 58.0) - 1.3 * np.maximum(a - 0.6, 0.0))
    # barbs curve up towards the tip of the feather
    bend = 0.42 * np.sin(phi0) ** 1.2
    ls = 1.4 + 0.25 * a
    phi = phi0[:, None] - bend[:, None] * (1.0 - np.exp(-s / ls[:, None]))
    phi = phi + rng.normal(0, np.radians(0.22), (n, 1))
    # slow individual wander
    w = rng.standard_normal((n, NS // 25 + 2)).astype(np.float32)
    w = cv2.resize(cv2.GaussianBlur(w, (0, 0), sigmaX=4.0, sigmaY=0.001), (NS, n), interpolation=cv2.INTER_CUBIC)
    phi = phi + np.radians(1.0) * w * np.minimum(s / 2.0, 1.0)
    x = side * np.cumsum(np.sin(phi) * DS, axis=1) + rachis_x(Z_TIP - a)[:, None]
    z = Z_TIP - a[:, None] + np.cumsum(np.cos(phi) * DS, axis=1)

    # where each barb ends: on the outline, with scatter barb by barb and clump by clump
    cl = np.zeros(n, int)
    k, c = 0, 0
    while k < n:
        m = int(rng.integers(2, 7))
        cl[k : k + m] = c
        k, c = k + m, c + 1
    e = envelope(x, z)
    jit = 1.0 + rng.normal(0, 0.03, n) + rng.normal(0, 0.035, c + 1)[cl] + 0.02 * np.sin(a * 1.7 + rng.uniform(0, 6))
    fly = rng.random(n) < 0.05
    jit[fly] += rng.uniform(0.05, 0.3, fly.sum())
    length = np.argmax(e >= jit[:, None], axis=1)
    length[length == 0] = NS - 1

    # clumps: past the green, barbs zip together into bundles
    centre = np.array([np.where(cl == cl[i])[0].mean() for i in range(n)])
    rg = ell(x, z, *GREEN)
    wt = np.clip((rg - 1.0) / 0.35, 0, 1) ** 1.5
    dxn = np.gradient(x, axis=0)
    dzn = np.gradient(z, axis=0)
    pull = (centre - np.arange(n))[:, None] * 0.34 * wt
    x = x + pull * dxn
    z = z + pull * dzn
    return a, np.stack([x, z], -1).astype(np.float32), length


def rachis_x(z):
    return 0.012 * np.minimum(z, 0.0) ** 2


# --- the camera -----------------------------------------------------------------------------------------------------
def camera(pts_apex, focus):
    H = W * 9 / 16
    view = np.array([np.sin(AZ) * np.cos(EL), -np.cos(AZ) * np.cos(EL), np.sin(EL)])
    target = np.array(pts_apex, float)
    target[2] -= (0.5 - APEX[1]) * H
    for _ in range(6):
        cam = frame_camera(target, view, W, DIST, aperture_mm=APERTURE, focus_point=focus, roll=ROLL)
        u, v = project(cam, np.array([pts_apex]))
        target[2] -= (v[0] - APEX[1]) * H / np.cos(EL)
        target[0] += (u[0] - APEX[0]) * W / np.cos(AZ)
    return frame_camera(target, view, W, DIST, aperture_mm=APERTURE, focus_point=focus, roll=ROLL)


APERTURE = 8.0


def project(cam, P):
    loc, tgt = np.array(cam["loc"]), np.array(cam["target"])
    d = tgt - loc
    d = d / np.linalg.norm(d)
    r = np.cross(d, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    up = np.cross(r, d)
    ro = np.radians(cam.get("roll", 0.0))
    r, up = np.cos(ro) * r + np.sin(ro) * up, -np.sin(ro) * r + np.cos(ro) * up
    q = P - loc
    zc = q @ d
    f = cam["lens_mm"] / 36.0
    u = 0.5 + (q @ r) / zc * f
    v = 0.5 - (q @ up) / zc * f * 16 / 9
    return u, v


def world(x, z, h=0.0):
    """Plane coordinates to world; h is towards the camera."""
    return np.stack([x, surface(x, z) - h, z], -1)


# --- the barbs ------------------------------------------------------------------------------------------------------
def frames(x, z, y):
    """Tangent, side (right-hand in the plane) and normal (towards the camera) along a polyline."""
    P = np.stack([x, y, z], -1)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    # the normal of the surface, not of the world
    e = 0.05
    gx = (surface(x + e, z) - surface(x - e, z)) / (2 * e)
    gz = (surface(x, z + e) - surface(x, z - e)) / (2 * e)
    N = np.stack([gx, -np.ones_like(x), gz], -1)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    S = np.cross(N, T)
    S /= np.linalg.norm(S, axis=1, keepdims=True)
    N = np.cross(T, S)
    if N.size and N[0, 1] > 0:
        N, S = -N, -S
    return P, T, S, N


class Soup:
    def __init__(self, names):
        self.V, self.F, self.A, self.n = [], [], {k: [] for k in names}, 0
        self.bid, self.k = [], []  # which barb, and which of its samples, each vertex hangs from: only the flick asks

    def add(self, V, F, skin=None, **a):
        if skin:
            self.bid.append(np.full(len(V), skin[0], np.int32))
            self.k.append(np.broadcast_to(skin[1], len(V)).astype(np.int32))
        self.V.append(V.astype(np.float32))
        self.F.append((F + self.n).astype(np.int32))
        for k, x in a.items():
            self.A[k].append(x.astype(np.float32))
        self.n += len(V)

    def save(self, path):
        np.savez(path, V=np.concatenate(self.V), F=np.concatenate(self.F), **{k: np.concatenate(v) for k, v in self.A.items()})
        return self.n, sum(len(f) for f in self.F)


BARBULE = 0.0135  # barbule spacing (cm), measured by eye on ref/peacock2/1-eye/01 at 100% (about 5 px at about 350 px/cm)
K = 5  # facets per barbule
TK = np.linspace(0, 1, K + 1, dtype=np.float32)
_rows = np.arange(K, dtype=np.int32)
FACES = np.concatenate([np.stack([2 * _rows, 2 * _rows + 1, 2 * _rows + 3], -1), np.stack([2 * _rows, 2 * _rows + 3, 2 * _rows + 2], -1)]).astype(np.int32)


def barbules(soup, P, T, S, N, sg, ds, reach, cover, xs, zs, u, tipf, rng, cam, dbarb, lam_b, amp_b, lamf, dust, bid=None):
    """One row on one barb. P..N are per-sample along the barb; barbules sit every ds cm, jittered. sg: which side of the barb."""
    ns = P.shape[0]
    pos = np.arange(0.02, ns - 1, ds / DS, dtype=np.float32)
    pos = pos + rng.uniform(-0.3, 0.3, pos.size) * ds / DS
    pos = np.clip(pos, 0, ns - 1.001)
    idx = pos.astype(int)
    keep = rng.random(pos.size) < cover[idx]
    idx = idx[keep]
    m = idx.size
    if m == 0:
        return
    # cull what is out of the frame
    uu, vv = project(cam, P[idx])
    vis = (uu > -0.07 - MARGIN) & (uu < 1.07 + MARGIN) & (vv > -0.07 - MARGIN) & (vv < 1.09 + MARGIN)
    if not vis.any():
        return
    idx = idx[vis]
    m = idx.size

    Ti, Si, Ni, Pi = T[idx], S[idx] * sg, N[idx], P[idx]
    rc = reach[idx] * rng.uniform(0.82, 1.14, m) * tipf[idx]
    al = np.radians(rng.normal(38.0, 2.5, m))
    Lb = rc / np.sin(al)
    # along the barbule, a little curved towards the barb's direction (an occasional stray one, as in the macro photographs)
    stray = rng.random(m) < 0.01
    al2 = al.copy()
    al2[stray] += np.radians(rng.normal(0, 22, stray.sum()))
    Lb[stray] *= 1.3
    t = TK[None, :]
    hook = rng.uniform(0.25, 0.55, (m, 1))  # the tip curves over towards the barb's direction, and overlaps the row of the next barb
    along = Lb[:, None] * (np.cos(al2)[:, None] * t + 0.2 * t * t + hook * t**4)
    lat = Lb[:, None] * np.sin(al2)[:, None] * (t - 0.16 * t * t - 0.22 * t**4)
    # arched: up from the ramus, over and down; this is what makes a ridge of light along each barb
    arch = 0.13 * Lb[:, None] * rng.uniform(0.7, 1.25, (m, 1)) * np.sin(np.pi * t**0.8) - 0.10 * Lb[:, None] * t
    # past the green the barbules stand apart like the teeth of a comb
    apart = np.clip((ell(xs[idx], zs[idx], *GREEN) - 1.0) / 0.2, 0, 1)[:, None]
    wid = (1.0 - 0.62 * apart) * ds * 0.56 * (0.62 + 0.62 * np.sin(np.pi * t**0.7)) * (1.0 - 0.75 * t**4)
    tau = np.radians(rng.normal(11.0, 3.5, (m, 1)))  # shingled: each overlaps the next
    Ux = -Ti * np.sin(al)[:, None] + Si * np.cos(al)[:, None]
    C = Pi[:, None, :] + along[..., None] * Ti[:, None, :] + lat[..., None] * Si[:, None, :] + arch[..., None] * Ni[:, None, :]
    # facet-to-facet jitter: each facet of a real barbule is its own small mirror
    C = C + (rng.normal(0, 0.0003, (m, K + 1)) * (t > 0))[..., None] * Ni[:, None, :]
    Wv = np.cos(tau)[..., None] * Ux[:, None, :] + np.sin(tau)[..., None] * Ni[:, None, :]
    a = C - wid[..., None] * Wv
    b = C + wid[..., None] * Wv
    V = np.stack([a, b], 2).reshape(m, 2 * (K + 1), 3)

    # colour: zone edges stepped barb by barb and barbule by barbule
    xr, zr = xs[idx], zs[idx]
    lam, amp = lobes(xr, zr, dbarb + rng.normal(0, 0.007, m).astype(np.float32))
    lam = lam + lam_b + field(lamf, xr, zr) * 7.0 + rng.normal(0, 1.6, m)
    fr = fringe_colour(xr, zr, rng, lam_b)
    is_fr = ell(xr, zr, *GREEN) + dbarb >= 1.0
    lam[is_fr] = fr[is_fr]
    amp = amp * amp_b * (1.0 + 0.16 * rng.normal(0, 0.45, m)) * (0.62 + 0.38 * field(dust, xr, zr))
    amp[is_fr] *= (0.72 + 0.28 * tipf[idx][is_fr])
    # a heavy tail: a few barbules sit exactly right and flash, most of all in the dark heart
    hot = rng.random(m) < 0.0025
    amp[hot] *= rng.uniform(1.3, 2.0, hot.sum())
    heart = heart_q(xr, zr) < 1.0
    amp[heart] *= np.exp(rng.normal(0, 0.9, heart.sum()))
    # per facet: the root is dark, the colour a bit different on every node
    lamk = lam[:, None] + rng.normal(0, 0.8, (m, K + 1))
    ampk = np.maximum(amp, 0.0)[:, None] * (0.3 + 0.7 * np.minimum(t / 0.16, 1.0)) * rng.uniform(0.93, 1.07, (m, K + 1))
    lamk = np.repeat(lamk, 2, 1).ravel()
    ampk = np.repeat(ampk, 2, 1).ravel()

    nv = 2 * (K + 1)
    off = (np.arange(m, dtype=np.int32) * nv)[:, None, None]
    F = (FACES[None] + off).reshape(-1, 3)
    soup.add(V.reshape(-1, 3), F, skin=None if bid is None else (bid, np.repeat(idx, nv)), lam=lamk, amp=ampk)


def fringe_colour(x, z, rng, lam_b):
    """Green-gold on the top, gold and copper lower down, with barb-to-barb scatter."""
    gold = np.clip((0.9 - z) / 2.6, 0, 1)
    base = 545.0 + 18.0 * np.sin(1.3 * x + 0.8 * z) + gold * 62.0
    # about one barb in nine is more bronze than its neighbours
    return base + 2.0 * lam_b + (30.0 if np.ndim(lam_b) == 0 and lam_b > 6.0 else 0.0)


def ramus(soup, P, T, S, N, w, col, skin=None):
    """A ramus: an arched ribbon, three strands across."""
    n = P.shape[0]
    a = P - S * w[:, None]
    b = P + S * w[:, None]
    c = P + N * w[:, None] * 0.7
    V = np.stack([a, c, b], 1).reshape(-1, 3)
    i = np.arange(n - 1, dtype=np.int32)[:, None, None] * 3
    q = np.array([[[0, 3, 1], [1, 3, 4], [1, 4, 2], [2, 4, 5]]], np.int32)
    F = (q + i).reshape(-1, 3)
    soup.add(V, F, skin=skin, col=np.repeat(col, 3, 0))


def build(q, focus_only=False):
    global _rip, EDGE
    EDGE = [fbm((512, 512), 1 / GRID[2], 0.8, 2.8, 2.4, SEED + 10 + k) for k in range(4)]
    dens = {"preview": 1.5, "mid": 1.2, "final": 1.0, "layout": 2.0}[q]
    ds = BARBULE * dens
    _rip = fbm((512, 512), 1 / GRID[2], 1.2, 4.5, 2.2, SEED + 1)
    lamf = fbm((512, 512), 1 / GRID[2], 0.15, 1.2, 1.6, SEED + 2)
    dust = np.clip(0.55 + 0.5 * fbm((512, 512), 1 / GRID[2], 0.05, 0.8, 1.4, SEED + 3), 0, 1)

    # plane-level camera: apex and focus on the surface
    apex = world(np.array([0.0]), np.array([Z_APEX + APEX_SINK]))[0]
    focus = world(np.array([0.05]), np.array([FOCUS_Z]))[0]
    cam = camera(apex, focus)

    sides = [(+1, *grow_side(+1, SEED)), (-1, *grow_side(-1, SEED))]
    return cam, sides, lamf, dust, ds


FOCUS_Z = 0.35


def mesh(q, rec=None):
    """rec: a list to fill with the barbs, for the flick; the npz then has a neighbour skin.{q}.npz."""
    cam, sides, lamf, dust, ds = build(q)
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    soup = Soup(["lam", "amp"])
    rams = Soup(["col"])
    for side, a, paths, length in sides:
        n = len(a)
        for i in range(n):
            rng = np.random.default_rng(SEED * 1000 + i * 2 + (side > 0))
            L = int(length[i])
            step = 2
            x = paths[i, :L:step, 0]
            z = paths[i, :L:step, 1]
            if x.size < 6:
                continue
            y0 = surface(x, z)
            # the barb's own layer: near the rachis they lie flat, out in the fringe they lift apart
            lay = rng.normal(0, 1.0) * (0.012 + 0.11 * np.clip((ell(x, z, *GREEN) - 0.9) / 0.6, 0, 1))
            y = y0 - lay
            P, T, S, N = frames(x, z, y)
            uu, vv = project(cam, P)
            if not ((uu > -0.1 - MARGIN) & (uu < 1.1 + MARGIN) & (vv > -0.1 - MARGIN) & (vv < 1.12 + MARGIN)).any():
                continue
            bid = None
            if rec is not None:
                bid = len(rec)
                rec.append({"P": P, "T": T, "rg": ell(x, z, *GREEN), "side": side, "i": i})
            # twist of the whole barb, slow along its length: the sheen comes and goes
            nw = max(x.size // 80, 4)
            tw = cv2.resize(rng.normal(0, 1, (1, nw)).astype(np.float32), (x.size, 1), interpolation=cv2.INTER_CUBIC)[0]
            ang = rng.normal(0, 0.14) + 0.2 * tw
            ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
            S2 = ca * S + sa * N
            N2 = ca * N - sa * S

            # spacing to the neighbour, so that barbules close the gaps inside the eye and leave black outside
            j = min(i + 1, n - 1) if i < n - 1 else i - 1
            m = min(L, int(length[j]))
            gap = np.full(x.size, 0.16, np.float32)
            pj = paths[j, : L if L <= length[j] else m]
            dist = np.hypot(paths[i, : pj.shape[0], 0] - pj[:, 0], paths[i, : pj.shape[0], 1] - pj[:, 1])[::step]
            gap[: dist.size] = dist
            gap = cv2.GaussianBlur(gap[None, :], (0, 0), 8.0)[0]
            rg = ell(x, z, *GREEN)
            inner = np.clip((1.05 - rg) / 0.15, 0, 1)
            reach = np.clip(0.60 * gap, 0.03, 0.058) * inner + (1 - inner) * np.clip(0.32 * gap, 0.016, 0.03)
            # barbules thin out at the end of a barb, and short near its base
            sl = np.arange(x.size, dtype=np.float32) * DS * step
            tl = rng.uniform(0.55, 1.5)
            tipf = np.clip((sl[-1] - sl) / tl, 0.09, 1.0) ** 0.8 * np.clip(0.55 + sl / 0.25, 0, 1)
            # bald patches in the outer fringe
            cover = np.ones(x.size, np.float32)
            bald = rng.random() < 0.3
            if bald:
                c0, wd = rng.uniform(0.5, 1.0) * sl[-1], rng.uniform(0.08, 0.28)
                cover *= 1.0 - np.exp(-(((sl - c0) / wd) ** 2)) * (rg > 1.0) * rng.uniform(0.6, 1.0)
            cover = cover * np.clip(1.0 - 1.6 * np.maximum(rg - 1.0, 0.0), 0.38, 1.0)
            cover = cover * np.clip((sl[-1] - sl) / rng.uniform(0.04, 0.2), 0.0, 1.0) ** 2  # the ramus runs on past the last barbules, as a hair

            dbarb = rng.normal(0, 0.021)
            lam_b = rng.normal(0, 3.2)
            amp_b = rng.uniform(0.72, 1.14)
            for sg in (-1.0, 1.0):
                # the two rows of a barb are not the same (row-to-row offsets, on top of what the angle does)
                barbules(soup, P, T, S2, N2, sg, ds, reach, cover, x, z, sl, tipf, rng, cam, dbarb, lam_b + rng.normal(0, 1.6), amp_b * rng.uniform(0.88, 1.08), lamf, dust, bid=bid)

            # ramus: dark in the eye, straw on the fringe
            w = (0.0055 * np.exp(-sl / 3.5) + 0.002) * np.clip((sl[-1] - sl) / 0.4, 0.3, 1)
            outer = np.clip((rg - 0.8) / 0.3, 0, 1)
            col = (1 - outer)[:, None] * np.array([0.022, 0.014, 0.010]) + outer[:, None] * np.array([0.13, 0.09, 0.045])
            ramus(rams, P[::2], T[::2], S2[::2], N2[::2], w[::2], col[::2], skin=None if bid is None else (bid, np.repeat(np.arange(P[::2].shape[0], dtype=np.int32) * 2, 3)))

    # the rachis
    zr = np.linspace(-9.0, Z_TIP + 0.02, 280)
    xr = rachis_x(zr)
    P = np.stack([xr, surface(xr, zr) + 0.012, zr], -1)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Sr = np.stack([T[:, 2], 0 * zr, -T[:, 0]], -1)
    Nr = np.cross(T, Sr)
    Nr = Nr * np.sign(-Nr[:, 1:2])
    wr = 0.006 + 0.05 * np.clip(-(zr - Z_TIP) / 7.0, 0, 1) ** 0.8
    col = np.array([0.11, 0.075, 0.035]) * np.ones_like(P) * (0.25 + 0.75 * np.clip(-(zr - Z_TIP) / 1.2, 0, 1))[:, None]
    ramus(rams, P, T, Sr, Nr, wr, col, skin=None if rec is None else (-1, 0))

    p1, p2 = os.path.join(d, f"barbules.{q}.npz"), os.path.join(d, f"rami.{q}.npz")
    print("barbules verts, tris:", soup.save(p1), "rami:", rams.save(p2), flush=True)
    if rec is not None:
        np.savez(os.path.join(d, f"skin.{q}.npz"), bid=np.concatenate(soup.bid + rams.bid), k=np.concatenate(soup.k + rams.k))
    return cam, p1, p2


def layout(cam, sides, lamf, dust):
    """No render: the paths and zones projected through the camera, a few seconds. For composition."""
    w, h = 1600, 900
    img = np.zeros((h, w, 3), np.uint8)
    lut = np.array(RAMP)
    for side, a, paths, length in sides:
        for i in range(len(a)):
            L = int(length[i])
            x, z = paths[i, :L, 0][::3], paths[i, :L, 1][::3]
            if x.size < 3:
                continue
            u, v = project(cam, world(x, z))
            lam, amp = lobes(x, z)
            fr = ell(x, z, *GREEN) >= 1
            lam[fr] = fringe_colour(x, z, None, 0)[fr]
            rgb = np.stack([np.interp(lam, lut[:, 0], lut[:, c]) for c in (3, 2, 1)], -1) * np.minimum(amp, 1)[:, None] * 255
            pts = np.stack([u * w, v * h], -1).astype(np.int32)
            for k in range(len(pts) - 1):
                cv2.line(img, tuple(int(q) for q in pts[k]), tuple(int(q) for q in pts[k + 1]), tuple(float(c) for c in rgb[k]), 1, cv2.LINE_AA)
    cv2.line(img, (0, int(0.47 * h)), (w, int(0.47 * h)), (90, 90, 90), 1)
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cv2.imwrite(os.path.join(d, "layout.jpg"), img)
    print(os.path.join(d, "layout.jpg"))


FLICK_FRAMES, FLICK_SUB = 36, 4  # frames of the take; sub-exposures of the moving mesh in each (the mesh has no keyframes, so its motion blur is made by averaging them)
FLICK_SHUTTER = 0.5


def flick_times(sub):
    return (np.arange(FLICK_FRAMES)[:, None] + (FLICK_SHUTTER * ((np.arange(sub) + 0.5) / sub - 0.5))[None, :]).ravel() / 25.0


def flick_layout(a=None):
    """No render, seconds: the barbs through the camera, frame by frame. For judging the motion."""
    import subprocess

    import s45_flick as FL

    global MARGIN
    MARGIN = 0.28
    cam, sides, lamf, dust, ds = build("layout")
    rec = []
    for side, _a, paths, length in sides:
        for i in range(len(_a)):
            L = int(length[i])
            x, z = paths[i, :L:2, 0], paths[i, :L:2, 1]
            if x.size < 6:
                continue
            P = np.stack([x, surface(x, z), z], -1)
            uu, vv = project(cam, P)
            if ((uu > -0.1 - MARGIN) & (uu < 1.1 + MARGIN) & (vv > -0.1 - MARGIN) & (vv < 1.12 + MARGIN)).any():
                rec.append({"P": P, "T": None, "rg": ell(x, z, *GREEN), "side": side, "i": i})
    print("barbs in reach:", len(rec), flush=True)
    B = FL.Barbs(rec, a)
    ts = flick_times(1)
    th, X, A, Tw = B.solve(ts)
    lut = np.array(RAMP)
    cols = []
    for r in rec:
        lam, amp = lobes(r["P"][:, 0], r["P"][:, 2])
        fr = r["rg"] >= 1
        lam[fr] = fringe_colour(r["P"][:, 0], r["P"][:, 2], None, 0)[fr]
        cols.append(np.stack([np.interp(lam, lut[:, 0], lut[:, c]) for c in (3, 2, 1)], -1) * np.minimum(amp, 1)[:, None] * 255)
    d = os.path.join(OUT, NAME + "_flick")
    os.makedirs(d, exist_ok=True)
    w, h = 1280, 720
    frames = []
    apex0 = project(cam, np.array([world(np.array([0.0]), np.array([Z_APEX + APEX_SINK]))[0]]))
    print("rest apex at", float(apex0[0][0]), float(apex0[1][0]), flush=True)
    for fr in range(len(ts)):
        Px, Py, Pz, dth = B.pose(th[fr], X[fr], A[fr])
        img = np.zeros((h, w, 3), np.uint8)
        top = 1.0
        for b, r in enumerate(rec):
            m = r["P"].shape[0]
            q3 = np.stack([Px[b, :m], Py[b, :m], Pz[b, :m]], -1)
            ca, sa = np.cos(Tw[fr]), np.sin(Tw[fr])
            q3 = np.stack([X[fr] + (q3[:, 0] - X[fr]) * ca - q3[:, 1] * sa, (q3[:, 0] - X[fr]) * sa + q3[:, 1] * ca, q3[:, 2]], -1)
            u, v = project(cam, q3)
            mid = (u > 0.3) & (u < 0.7)
            if mid.any():
                top = min(top, float(v[mid].min()))
            pts = np.stack([u * w, v * h], -1).astype(np.int32)
            for k in range(0, m - 3, 3):
                cv2.line(img, tuple(int(c) for c in pts[k]), tuple(int(c) for c in pts[k + 3]), tuple(float(c) for c in cols[b][k]), 1, cv2.LINE_AA)
        cv2.line(img, (0, int(0.476 * h)), (w // 40, int(0.476 * h)), (120, 120, 120), 1)
        frames.append(img)
        tips = np.array([np.hypot(Px[b, r["P"].shape[0] - 1] - r["P"][-1, 0] - A[fr] * (r["P"][0, 2] + 30.0), Pz[b, r["P"].shape[0] - 1] - r["P"][-1, 2]) for b, r in enumerate(rec)])
        print(f"{fr:2d} t {ts[fr]:.2f} X {X[fr]:+.2f} twist {np.degrees(Tw[fr]):+.1f} top of the arc {top:.3f}; tip moved p50 {np.median(tips):.2f} p95 {np.percentile(tips, 95):.2f} max {tips.max():.2f} cm; dth max {np.degrees(np.abs(th[fr]).max()):.0f} deg", flush=True)
    # silk: does a tip ever turn back? The share of its path travelled against its own net direction, and how far it goes
    last = np.array([B.m - 1]).ravel()
    idx = np.arange(len(rec))
    tip = np.stack([np.stack(B.pose(th[f], X[f], A[f])[0:3:2], -1)[idx, last] for f in range(len(ts))])
    v = np.diff(tip, axis=0)
    net = tip[-1] - tip[0]
    along = np.sum(v * net[None], axis=-1) / np.maximum(np.linalg.norm(net, axis=-1), 1e-6)
    back = np.sum(np.maximum(-along, 0), axis=0) / np.maximum(np.sum(np.abs(along), axis=0), 1e-6)
    step = np.linalg.norm(v, axis=-1)
    print(f"tips over the take: net p50 {np.median(np.linalg.norm(net, axis=-1)):.2f} p95 {np.percentile(np.linalg.norm(net, axis=-1), 95):.2f} cm; path against net p50 {np.median(back):.3f} p95 {np.percentile(back, 95):.3f}; fastest step p95 {np.percentile(step.max(0), 95):.3f} cm per frame", flush=True)
    picks = np.linspace(0, len(frames) - 1, 12).astype(int)
    rows = [np.hstack([cv2.resize(frames[i], (640, 360), interpolation=cv2.INTER_AREA) for i in picks[k : k + 3]]) for k in range(0, 12, 3)]
    cv2.imwrite(os.path.join(d, "layout.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", "25", "-i", "-", "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-movflags", "+faststart", os.path.join(d, "layout.mp4")], stdin=subprocess.PIPE)
    for f in frames:
        ff.stdin.write(f.tobytes())
    ff.stdin.close()
    ff.wait()
    print(os.path.join(d, "layout.jpg"))


def flick_stack(q, rec, sub, path):
    """Every vertex of both meshes at every sub-exposure, (times, verts, 3) float32. It is big, about 12 bytes per vertex per sub-exposure, and it lives beside the render."""
    import s45_flick as FL

    d = os.path.join(OUT, NAME)
    Vb, Vr = np.load(os.path.join(d, f"barbules.{q}.npz"))["V"], np.load(os.path.join(d, f"rami.{q}.npz"))["V"]
    V = np.concatenate([Vb, Vr])
    sk = np.load(os.path.join(d, f"skin.{q}.npz"))
    B = FL.Barbs(rec)
    ts = flick_times(sub)
    th, X, A, Tw = B.solve(ts)
    st = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=(len(ts), V.shape[0], 3))
    for i in range(len(ts)):
        st[i] = B.skin(V, sk["bid"], sk["k"], th[i], X[i], A[i], Tw[i])
    st.flush()
    print(f"{path}: {st.shape}, {os.path.getsize(path) / 1e9:.2f} GB", flush=True)


def flick_average(d, sub):
    """Average each frame's sub-exposures in place; a half-done run shows as an error, not as a short take."""
    fs = sorted(f for f in os.listdir(d) if f.startswith("take.linear_") and f.endswith(".npy"))
    if len(fs) != FLICK_FRAMES * sub:
        raise SystemExit(f"{d}: {len(fs)} sub-exposures, expected {FLICK_FRAMES * sub}")
    out = os.path.join(d, ".avg")
    os.makedirs(out, exist_ok=True)
    for i in range(FLICK_FRAMES):
        a = sum(np.load(os.path.join(d, f)).astype(np.float32) for f in fs[i * sub : (i + 1) * sub]) / sub
        np.save(os.path.join(out, f"take.linear_{i:03d}.npy"), a.astype(np.float16))
    for f in fs:
        os.remove(os.path.join(d, f))
    for f in sorted(os.listdir(out)):
        os.replace(os.path.join(out, f), os.path.join(d, f))
    os.rmdir(out)


def main():
    global MARGIN
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    q = args[0] if args else "preview"
    tag = next((a[6:] for a in sys.argv if a.startswith("--tag=")), None)
    if q == "layout":
        cam, sides, lamf, dust, ds = build(q)
        print("barbs per side:", len(sides[0][1]))
        layout(cam, sides, lamf, dust)
        return
    flick = None
    if q == "flick":
        flick = args[1] if len(args) > 1 else "layout"
        if flick == "layout":
            flick_layout({k: float(v) for k, v in (x.split("=") for x in args[2:])})  # flick layout U0=80
            return
        q = "final" if flick == "final" else "mid"
        MARGIN = 0.28
    rec = [] if flick else None
    cam, p1, p2 = mesh(q, rec)
    view = np.array(cam["loc"]) - np.array(cam["target"])
    view /= np.linalg.norm(view)
    n = np.array([0.0, -1.0, 0.0])
    cos0 = float(np.dot(view, n))
    r = 2 * cos0 * n - view  # the mirror direction of the feather's plane
    c = np.array(cam["target"])
    side = np.array([1.0, 0.0, 0.0])
    params = {"ramp": RAMP, "n": 1.6, "cos0": cos0, "rough": 0.29, "k_cuticle": 0.035, "rough_c": 0.3, "k_shift": 0.6}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "barbules", "npz": p1, "shader_py": os.path.join(ROOT, "v2", "stills", "s45_shader.py"), "params": params},
            {"name": "rami", "npz": p2, "material": {"Base Color": "col", "Roughness": 0.45, "Specular IOR Level": 0.18}},
        ],
        "lights": [
            {"type": "gradient", "name": "scrim", "loc": (c + r * 42).tolist(), "target": c.tolist(), "size": [120, 120], "sigma": [22, 16], "L": 6.5, "rgb": [1.0, 0.98, 0.95]},
            {"name": "rake", "loc": (c + r * 22 - side * 38).tolist(), "target": c.tolist(), "size": [8, 8], "watts": 2600, "rgb": [1.0, 0.96, 0.9]},
        ],
        "world": [0.0, 0.0, 0.0],
        "bounces": 6,
        "diffuse_bounces": 2,
        "glossy_bounces": 3,
        "transmission_bounces": 0,
        "denoise": q != "final",
        "spp": {"preview": 48, "mid": 96, "final": int(os.environ.get("S45_SPP", 256))},
    }
    look = {"exposure": 0.12, "contrast": 1.45, "saturation": 1.08, "black": 0.002, "grain": 1.1, "sharpen": 0.25, "halation": 0.02, "glare": 0.002}
    if flick:
        # a candidate under its own name, as s24's wind is: _take clears {name}_move_*. A still camera; only the feather moves
        import kit

        sub = FLICK_SUB if flick == "final" else 1
        sp = os.path.join(OUT, NAME, f"flick.{q}.npy")
        flick_stack(q, rec, sub, sp)
        scene["deform"] = {"npy": sp, "vertex": ["barbules", "rami"]}
        lk = kit.looks().get(NAME, {})
        kit.looks = lambda: {NAME + "_flick": {**{k: v for k, v in lk.items() if k != "move"}, "move": {"frames": FLICK_FRAMES * sub, "shutter": 0, "spp": 64 if sub > 1 else 96}}}
        os.environ["GEWU_MOVE"] = flick
        out = shoot(NAME + "_flick", scene, q, develop=look)
        if flick == "final":
            flick_average(out, sub)
            os.remove(sp)
        return
    shoot(NAME, scene, q, tag=tag or q, develop=look)


if __name__ == "__main__":
    main()
