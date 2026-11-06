"""Shot 14: a trotting-horse lantern (走马灯) seen from below, its top rim the arc; the shadows of paper horses gallop round the lit paper.

    python3 -I v2/stills/s54_zoumadeng.py cut                     the ten cut-outs only, no render: out/v2/s54_zoumadeng/cut.jpg
    python3 -I v2/stills/s54_zoumadeng.py [preview|mid|final]     one frame, rendered
    python3 -I v2/stills/s54_zoumadeng.py take [preview|mid|final]   all 30 frames, in out/v2/s54_zoumadeng_take_<q>/ (frames already there are kept)
    python3 -I v2/stills/s54_zoumadeng.py ext [preview|mid|final]    frames 14..29 in out/v2/s54_zoumadeng_take_ext/, so that they can be checked against the take before they go into it

Built like the real thing (no photograph, no model image; all sizes are estimates, a large lantern of about 45 cm):
- a flame on the axis, a ring of paper cut-outs close inside the shade, and a paper shade on a bamboo cage. The shadows on the paper are ray traced from the flame through the
  ring and the cage: the flame's size sets the softness, and it trembles, so the shadows tremble too;
- paper: long fibres and flocs, thin and thick places, a double layer glued over each rib. It scatters forward, so it is brightest on the line from the lens to the flame and
  deepens towards the sides, where the path through it is long;
- the horses are cut as a 皮影 maker would, compared by eye with the puppets in ref/lantern (none of those is a horse, and none is copied): translucent hide, inked bars, a net of diamonds on the
  barrel, fish scales on the neck, a cloud scroll on each joint, a saddle cloth and a tuft of dyed film. Colour comes through them; the shadow is brown, not black;
- the ring leans out at the top, so the heads fall nearer the paper and throw a sharper shadow than the feet; the flame is tall, so shadows blur more across their top and bottom edges;
- behind the lantern, other lanterns up a street at night: real spheres far off, out of focus. That is why the sky is not black.

What is not traditional, and is ours: a real lantern's horses are rigid. Here the ten horses are ten phases of one gallop (a transverse gallop: four beats, then a suspension),
and the ring turns a little more than one horse per film frame (nine horses), so the camera's own strobing makes them run on the spot and creep forward. That is a zoetrope, with the lantern's
optics. A candle could not turn a ring this fast (about 170 rev/min), and a very short shutter is assumed: no motion blur.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, ROOT, _cam_axes, color, fbm, rank, shoot, sstep
from vessel import Profile, fit_arc, project

NAME = "s54_zoumadeng"
FRAMES = 30  # was 15; the first 15 are unchanged (see flame_at)
N = 9  # horses round the ring
SEED = 54
W = 32.0  # frame width at the subject, cm
EL = 30.0  # the camera looks up by this much
DIST = 52.0
RI = 19.0  # radius of the ring of cut-outs
ZF = -3.5  # the flame's height; the top rim is at z = 0
FLAME = 0.45  # its radius
H = 5.2  # a horse's height at the withers on the ring, cm
ZG = -9.5  # the ground line on the ring
DRIFT = np.radians(0.8)  # how far beyond one horse the ring turns in a frame
RIB0, NRIB = np.radians(19.5), 8
FAR_GLOW = 1.1


def rad(z):
    """The shade's radius: a slight barrel, drawn in towards the rim."""
    return 22.6 - 0.01 * (z + 9.0) ** 2


# --- the gallop -------------------------------------------------------------------------------------------------
def catmull(p, n=20, closed=False):
    p = np.array(p, float)
    p = np.vstack([p[-1], p, p[0], p[1]]) if closed else np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    out = []
    for i in range(len(p) - 3):
        a, b, c, d = p[i], p[i + 1], p[i + 2], p[i + 3]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t**2 + (3 * b - a - 3 * c + d) * t**3))
    out = np.vstack(out)
    return out if closed else np.vstack([out, p[-2]])


def ik(a, target, l1, l2, bend):
    """The middle joint of a two-bone chain from a to target. bend = +1 or -1 chooses the side. A reach too long is pulled in."""
    a, target = np.array(a, float), np.array(target, float)
    d = target - a
    L = np.linalg.norm(d)
    L2 = min(max(L, abs(l1 - l2) + 1e-3), (l1 + l2) * 0.999)
    u = d / max(L, 1e-6)
    x = (l1**2 - l2**2 + L2**2) / (2 * L2)
    y = np.sqrt(max(l1**2 - x**2, 0.0))
    return a + u * x + bend * y * np.array([-u[1], u[0]]), a + u * L2


def smooth(t):
    return t * t * (3 - 2 * t)


# The hind leg. The hock can only close forward: the cannon swings towards the front of the gaskin, the point of the hock stays behind, and a horse cannot bend it the other way. The stifle and hock are tied by
# tendons (the reciprocal apparatus) and close together, the hock a little more open, so one angle does for both. On the ground the hoof's path and the pastern's lean fix the rest; in the air the femur and the
# stifle are keyed. From anatomy and from what I know of serial photographs of the gallop, no picture consulted; lengths in H and all these angles are estimates, for a light horse.
HL = dict(femur=0.29, tibia=0.29, cannon=0.27, pastern=0.1)
HOPEN = np.radians(15.0)  # the hock is this much more open than the stifle
HIP = (-0.44, 0.04)  # the hip joint in the body frame. The stifle then hangs below the flank, not inside the barrel
HGAMMA_STANCE = ([0.0, 0.5, 1.0], [-35.0, -62.0, -12.0])  # the pastern's lean from the vertical over the stance, degrees: + = the fetlock ahead of the hoof
# over the swing, t = 0 lift-off, t = 1 touch-down: the femur's lean forward, the stifle's angle, the pastern's lean
HSWING = dict(t=[0.0, 0.15, 0.35, 0.6, 0.82, 1.0], femur=[-17.0, 2.0, 28.0, 47.0, 60.0, 47.0], stifle=[128.0, 110.0, 88.0, 76.0, 95.0, 112.0], gamma=[-12.0, 40.0, 62.0, 45.0, 0.0, -35.0])


def hind_chain(st):
    """The chain hip, stifle, hock, fetlock with the stifle closed to st (radians), the femur along +x. Returns the three joints, in H."""
    S = np.array([HL["femur"], 0.0])
    a = st - np.pi
    K = S + HL["tibia"] * np.array([np.cos(a), np.sin(a)])
    F = K + HL["cannon"] * np.array([np.cos(HOPEN), -np.sin(HOPEN)])
    return S, K, F


HGRID = np.radians(np.linspace(60.0, 165.0, 211))
HREACH = np.array([np.linalg.norm(hind_chain(h)[2]) for h in HGRID])  # reach grows with the angle


def eased(u, us, vs):
    """Eased keyframes: flat at each key, so the leg never jerks where two segments meet."""
    i = int(np.clip(np.searchsorted(us, u, side="right") - 1, 0, len(us) - 2))
    return vs[i] + (vs[i + 1] - vs[i]) * smooth((u - us[i]) / (us[i + 1] - us[i]))


class Pose:
    """All the landmarks of the horse at phase phi of the stride, in cm, ground at y = 0, its middle at x = 0."""

    STANCE = 0.22
    PHASE = {"hf": 0.0, "hn": 0.12, "ff": 0.32, "fn": 0.48}  # (leg, phase of touch-down): the near side leads

    def __init__(self, phi):
        self.phi = phi
        self.pitch = np.radians(5.5) * np.cos(2 * np.pi * (phi - 0.12))
        self.org = np.array([0.0, (0.74 + 0.04 * np.cos(2 * np.pi * (phi - 0.85))) * H])
        self.nu = np.radians(27.0 + 6.0 * np.cos(2 * np.pi * (phi - 0.85)))
        c, s = np.cos(self.pitch), np.sin(self.pitch)
        self.R = np.array([[c, -s], [s, c]])
        self.legs = {k: self.leg(k) for k in self.PHASE}

    def b(self, x, y):
        """Body frame (units of H, x forward, y up) to cm."""
        return self.org + H * (self.R @ np.array([x, y]))

    def leg(self, k):
        fore = k[0] == "f"
        off = np.array([0.05, 0.025]) * H if k[1] == "f" else np.zeros(2)  # the far side: a little further on and higher
        u = (self.phi - self.PHASE[k]) % 1.0
        xc, Rr = (0.27, 0.36) if fore else (-0.47, 0.39)
        d = self.STANCE
        if u < d:
            t = u / d
            xh = xc + Rr * (1 - 2 * t)
            lift = 0.0
            beta = np.radians(-22 + 58 * t)
            past = np.radians(-52 + 78 * t)
        else:
            t = (u - d) / (1 - d)
            xh = xc + Rr * (-1 + 2 * smooth(t))
            lift = (0.46 if fore else 0.36) * np.sin(np.pi * t**0.8) ** 1.2
            beta = np.radians(36 + 84 * smooth(min(t / 0.45, 1.0)) - 142 * smooth(max((t - 0.45) / 0.55, 0.0)))
            past = np.radians(26 + 30 * np.sin(np.pi * t) - 78 * smooth(max((t - 0.6) / 0.4, 0.0)))
        if not fore:
            return self.hind_leg(u, xh, off)
        tip = np.array([xh * H, lift * H]) + off * 0.6
        # back up the leg from the hoof
        lp, lc = 0.085 * H, 0.2 * H
        fet = tip - lp * np.array([np.sin(-(beta + past)), -np.cos(beta + past)])
        kn = fet - lc * np.array([np.sin(-beta), -np.cos(beta)])
        top = self.b(0.4, -0.04) + off
        mid, kn2 = ik(top, kn, 0.32 * H, 0.3 * H, -1)  # the elbow sits behind
        dk = kn2 - kn  # if the reach was pulled in, carry the rest of the leg with it
        return dict(top=top, mid=mid, knee=kn2, fet=fet + dk, tip=tip + dk, fore=fore)

    def hind_leg(self, u, x, off):
        top = self.b(*HIP) + off
        d = self.STANCE

        def planted(tip, gamma):
            # the hoof is fixed: back up to the fetlock, then close stifle and hock together until the chain just reaches the hip
            v = tip + HL["pastern"] * H * np.array([np.sin(gamma), np.cos(gamma)]) - top
            st = float(np.interp(np.linalg.norm(v) / H, HREACH, HGRID))
            S, K, F = hind_chain(st)
            return S, K, F, np.arctan2(v[1], v[0]) - np.arctan2(F[1], F[0])

        def fk(S, K, F, rot, gamma):
            c, s = np.cos(rot), np.sin(rot)
            M = H * np.array([[c, -s], [s, c]])
            mid, kn, fet = top + M @ S, top + M @ K, top + M @ F
            return dict(top=top, mid=mid, knee=kn, fet=fet, tip=fet - HL["pastern"] * H * np.array([np.sin(gamma), np.cos(gamma)]), fore=False)

        if u < d:
            gamma = np.radians(eased(u / d, *HGAMMA_STANCE))
            return fk(*planted(np.array([x * H, 0.0]) + off * 0.6, gamma), gamma)
        t = (u - d) / (1 - d)
        femur, st, gamma = (np.radians(eased(t, HSWING["t"], HSWING[k])) for k in ("femur", "stifle", "gamma"))
        leg = fk(*hind_chain(st), femur - np.pi / 2, gamma)
        if leg["tip"][1] < 0.0:  # about to land: the ground stops the hoof
            leg = fk(*planted(np.array([leg["tip"][0], 0.0]), gamma), gamma)
        return leg

    def head(self):
        wit = self.b(0.3, 0.27)
        poll = wit + 0.56 * H * np.array([np.cos(self.nu), np.sin(self.nu)])
        eta = self.nu - np.radians(70.0)
        d = np.array([np.cos(eta), np.sin(eta)])
        p = np.array([-d[1], d[0]])
        return lambda a, b: poll + H * (a * d + b * p)


# --- the cut-outs -----------------------------------------------------------------------------------------------
U0, U1, V0, V1 = -1.75 * H, 1.3 * H, -0.08 * H, 1.55 * H

# what each layer lets through. Hide is translucent, the way scraped donkey hide is; the bars are where it is cut thick and inked. Estimates, chosen by eye against ref/lantern
T_FAR = np.array([0.075, 0.04, 0.022], np.float32)
T_HIDE = np.array([0.13, 0.065, 0.032], np.float32)
T_HOLE = np.array([0.56, 0.42, 0.25], np.float32)
T_RED = np.array([0.90, 0.085, 0.03], np.float32)
T_GREEN = np.array([0.055, 0.40, 0.15], np.float32)
T_BAR = np.array([0.018, 0.012, 0.009], np.float32)


class Cut:
    """One horse, in a small raster, x from U0 to U1, y from V1 down to V0: a layer each for far legs, hide, carved holes, dyed film and inked bars."""

    def __init__(self, pxcm):
        self.pxcm = pxcm
        self.shape = (int((V1 - V0) * pxcm), int((U1 - U0) * pxcm))
        for k in ("far", "near", "body", "bar", "hole", "red", "green"):
            setattr(self, k, np.zeros(self.shape, np.uint8))

    def q(self, p):
        p = np.asarray(p, float)
        return np.round(np.stack([(p[..., 0] - U0) * self.pxcm, (V1 - p[..., 1]) * self.pxcm], -1) * 16).astype(np.int32)

    def fill(self, poly, canvas, val=255):
        cv2.fillPoly(canvas, [self.q(poly).reshape(-1, 1, 2)], val, cv2.LINE_AA, 4)

    def strip(self, pts, widths, canvas, val=255, caps=True):
        """A tapered strip along pts; widths at even steps along it, cm."""
        c = catmull(pts, 14) if len(pts) > 2 else np.array(pts, float)
        if len(c) == 2:
            c = np.linspace(c[0], c[1], 8)
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        hw = 0.5 * np.interp(s / max(s[-1], 1e-6), np.linspace(0, 1, len(widths)), widths)
        t = np.gradient(c, axis=0)
        t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
        n = np.stack([-t[:, 1], t[:, 0]], 1)
        self.fill(np.vstack([c + n * hw[:, None], (c - n * hw[:, None])[::-1]]), canvas, val)
        if caps:
            for i in (0, -1):
                cv2.circle(canvas, tuple(int(v) for v in self.q(c[i])), int(hw[i] * self.pxcm * 16), val, -1, cv2.LINE_AA, 4)

    def T(self):
        """What the whole figure lets through, colour by colour."""
        f = lambda a: (a.astype(np.float32) / 255.0)[..., None]
        out = np.ones(self.shape + (3,), np.float32)
        for layer, t in ((self.far, T_FAR), (np.maximum(self.body, self.near), T_HIDE), (self.hole, T_HOLE), (self.red, T_RED), (self.green, T_GREEN), (self.bar, T_BAR)):
            a = f(layer)
            out = out * (1 - a) + t[None, None] * a
        return out


def curl(start, L, a0, curve, wave, phase, n=6):
    """A strand trailing in the wind: it leaves at angle a0, bends by curve along its length, and a wave runs from root to tip."""
    pts = [np.array(start, float)]
    for i in range(1, n + 1):
        s = i / n
        ang = a0 + curve * s + wave * s * np.sin(2 * np.pi * (phase - 0.6 * s))
        pts.append(pts[-1] + (L / n) * np.array([np.cos(ang), np.sin(ang)]))
    return pts


def hind(c, pose, leg, canvas, k=1.0, carve=True):
    """A hind leg as one muscle: croup, buttock, thigh and gaskin are a single plate, wide at the top and narrowing without a break to the hock, whose point stands out behind. Drawn in overlapping pieces, because a tightly flexed hock would make one outline cross itself."""
    b, off = pose.b, leg["top"] - pose.b(*HIP)
    S, K, F, Tp = leg["mid"], leg["knee"], leg["fet"], leg["tip"]
    w = H * k
    unit = lambda v: v / max(np.linalg.norm(v), 1e-6)
    rear = lambda t: np.array([t[1], -t[0]])  # the side of a bone that faces back, for a bone running down the leg
    t2, t3, t4 = unit(K - S), unit(F - K), unit(Tp - F)
    r2, r3, r4 = rear(t2), rear(t3), rear(t4)
    L2 = np.linalg.norm(K - S)
    on = lambda s, side: S + s * L2 * t2 + side * w * r2
    C = K - t3 * 0.06 * w + r3 * 0.055 * w  # the point of the hock
    G = on(0.45, 0.115)
    B = b(-0.615, 0.03) + off
    ham = B + 0.5 * (G - B) + 0.03 * w * rear(unit(G - B))  # the back of the thigh, a little full
    # from the point of the hip over the croup to the buttock, down the back of the thigh, along the tendon to the point of the hock, round the front of the hock, up the gaskin, round the stifle, into the flank
    thigh = [b(-0.3, 0.17) + off, b(-0.43, 0.215) + off, b(-0.56, 0.14) + off, B, ham, G, on(0.74, 0.066), C, K + r3 * 0.03 * w + t3 * 0.05 * w, K - r3 * 0.048 * w, on(0.66, -0.036), on(0.28, -0.04), on(0.0, -0.058), b(-0.24, -0.03) + off]
    c.fill(catmull(thigh, 10, closed=True), canvas)
    c.strip([K + t3 * 0.02 * w, K + t3 * 0.14 * w, F], np.array([0.08, 0.06, 0.056]) * w, canvas)
    c.strip([F - t3 * 0.03 * w + r3 * 0.006 * w, F + t4 * 0.02 * w + r3 * 0.006 * w], np.array([0.07, 0.076]) * w, canvas)  # the fetlock, its fullness behind
    c.strip([F, Tp], np.array([0.066, 0.056]) * w, canvas)
    hoof = [Tp - t4 * 0.025 * H, Tp + t4 * 0.045 * H]
    c.strip(hoof, np.array([0.066, 0.1]) * H * k, c.bar, caps=False)
    if carve:
        c.strip([on(0.2, 0.02), on(0.5, 0.012), on(0.84, 0.004)], np.array([0.004, 0.036, 0.004]) * H * k, c.hole)  # a long leaf down the gaskin, as on the forearm
        # long cuts down the thigh, as a carver follows the muscle: one along the back of it from the buttock to the gaskin, one from the point of the hip to the stifle, one between
        hip = leg["top"]
        for p0, p1, wid in ((b(-0.56, 0.0) + off, on(0.34, 0.075), 0.034), (hip + 0.22 * (S - hip) + 0.03 * w * r2, S + 0.12 * (hip - S) + 0.03 * w * r2, 0.03), (0.72 * hip + 0.28 * B + 0.12 * (S - hip), on(0.12, 0.09), 0.03)):
            c.strip([p0, 0.5 * (p0 + p1) + 0.012 * w * rear(unit(p1 - p0)), p1], np.array([0.004, wid, 0.004]) * H * k, c.hole)
        c.strip([K + 0.16 * (F - K), K + 0.84 * (F - K)], np.array([0.003, 0.016, 0.003]) * H * k, c.hole)


def limb(c, leg, canvas, k=1.0, carve=True):
    top, mid, kn, fet, tip = leg["top"], leg["mid"], leg["knee"], leg["fet"], leg["tip"]
    c.strip([top, mid], np.array([0.27, 0.17]) * H * k, canvas)
    c.strip([mid, 0.5 * (mid + kn), kn], np.array([0.165, 0.115, 0.072]) * H * k, canvas)
    d = kn - mid
    d = d / max(np.linalg.norm(d), 1e-6)
    c.strip([kn - 0.04 * H * d, kn + 0.045 * H * d], np.array([0.07, 0.09, 0.06]) * H * k, canvas)  # the knee or hock
    c.strip([kn, fet], np.array([0.058, 0.05]) * H * k, canvas)
    c.strip([fet, tip], np.array([0.07, 0.056]) * H * k, canvas)  # the fetlock and the pastern
    a = tip - fet
    a = a / max(np.linalg.norm(a), 1e-6)
    hoof = [tip - a * 0.025 * H, tip + a * 0.045 * H]
    c.strip(hoof, np.array([0.066, 0.1]) * H * k, c.bar, caps=False)
    if carve:
        # a long leaf cut down the forearm or the gaskin, as a carver follows the muscle
        c.strip([mid + 0.12 * (kn - mid), 0.5 * (mid + kn), mid + 0.82 * (kn - mid)], np.array([0.004, 0.036, 0.004]) * H * k, c.hole)
        c.strip([kn + 0.16 * (fet - kn), kn + 0.84 * (fet - kn)], np.array([0.003, 0.016, 0.003]) * H * k, c.hole)


def lattice(u, v, s):
    """Diamond holes with thin bars between: the net a 皮影 carver cuts into a sleeve."""
    a, b_ = (u + v) / s, (u - v) / s
    fa, fb = a - np.floor(a) - 0.5, b_ - np.floor(b_) - 0.5
    return sstep(0.37, 0.3, np.maximum(np.abs(fa), np.abs(fb)))


def scales(u, v, s):
    """Fish scales: a crescent cut along the free edge of each."""
    row = np.floor(v / (s * 0.62))
    cu = u / s + 0.5 * np.mod(row, 2)
    fu = cu - np.floor(cu) - 0.5
    fv = v / (s * 0.62) - row
    d = np.hypot(fu, fv * 0.62)
    return sstep(0.5, 0.45, d) * sstep(0.27, 0.32, d) * sstep(0.02, 0.1, fv)


def roundel(bx, by, cx, cy, r, n, ph=0.0):
    """A cloud scroll on a joint, the mark a 皮影 carver leaves there: n arms winding out from the middle. Returns the cut, and a mask of where it lies."""
    rr = np.maximum(np.hypot(bx - cx, by - cy) / r, 1e-3)
    a = np.arctan2(by - cy, bx - cx) + ph
    arms = np.cos(n * a + 3.4 * np.log(rr))
    return sstep(0.16, 0.26, rr) * sstep(1.0, 0.86, rr) * sstep(0.1, 0.42, arms), rr < 1.05


def cut_horse(phi, pxcm):
    """One phase of the gallop, cut as a 皮影 horse in its trappings. The drawing is ours and follows no one figure. The hair is the same bunch in every horse; it only moves."""
    c = Cut(pxcm)
    pose = Pose(phi)
    b, at, nu = pose.b, pose.head(), pose.nu
    fixed = np.random.default_rng(SEED + 7)
    nd, nn = np.array([np.cos(nu), np.sin(nu)]), np.array([-np.sin(nu), np.cos(nu)])
    wit = b(0.3, 0.27)
    poll = at(0, 0)
    crest = [poll + 0.01 * H * nn, wit + 0.42 * H * nd + 0.07 * H * nn, wit + 0.2 * H * nd + 0.085 * H * nn, wit + 0.02 * H * nd + 0.03 * H * nn]
    nlow, throat = b(0.64, 0.04), at(-0.02, -0.11)
    hn, fn, hf, ff = pose.legs["hn"], pose.legs["fn"], pose.legs["hf"], pose.legs["ff"]

    hind(c, pose, hf, c.far, 0.92, carve=False)
    limb(c, ff, c.far, 0.92, carve=False)
    body = [poll, *crest[1:], b(0.12, 0.245), b(-0.05, 0.225), b(-0.22, 0.24), b(-0.38, 0.27), b(-0.52, 0.225), b(-0.6, 0.12), b(-0.625, 0.03), b(-0.57, -0.02), b(-0.44, -0.05), b(-0.28, -0.1), b(-0.1, -0.175), b(0.1, -0.23), b(0.26, -0.265), b(0.4, -0.225), b(0.54, -0.125), b(0.635, -0.01), nlow, 0.5 * (nlow + throat) + 0.03 * H * nn, throat, at(0.03, -0.18), at(0.12, -0.18), at(0.22, -0.115), at(0.33, -0.078), at(0.4, -0.085), at(0.445, -0.045), at(0.43, 0.0), at(0.385, 0.04), at(0.24, 0.052), at(0.08, 0.072)]
    c.fill(catmull(body, 10, closed=True), c.body)
    thigh = np.zeros_like(c.near)
    hind(c, pose, hn, thigh)
    c.near = np.maximum(c.near, thigh)
    limb(c, fn, c.near)
    c.strip([b(0.0, -0.2), np.array([b(0.0, -0.2)[0], 0.0])], [0.008 * H, 0.008 * H], c.bar)  # the wire that carries it on the ring

    # coordinates of the raster in the frames of the body and of the neck
    ny, nx = c.shape
    X, Y = np.meshgrid(U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, V1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    dx, dy = X - pose.org[0], Y - pose.org[1]
    R = pose.R
    bx, by = (R[0, 0] * dx + R[1, 0] * dy) / H, (R[0, 1] * dx + R[1, 1] * dy) / H
    ex, ey = X - wit[0], Y - wit[1]
    na, nb = (ex * nd[0] + ey * nd[1]) / H, (ex * nn[0] + ey * nn[1]) / H

    # the carving: inside the figure, a margin from its edge
    inner = cv2.distanceTransform((np.maximum(c.body, c.near) > 127).astype(np.uint8), cv2.DIST_L2, 3) / pxcm / H
    keep = sstep(0.026, 0.04, inner) * np.where(c.near > 127, sstep(-0.24, -0.17, by), 1.0)  # over the thigh and the shoulder too, but not down the leg
    neck = sstep(0.1, 0.14, na) * sstep(0.56, 0.52, na)
    barrel = sstep(0.34, 0.3, bx) * sstep(-0.62, -0.58, bx)
    hole = np.maximum(scales(na, nb, 0.064) * neck, lattice(bx, by, 0.062) * barrel)
    pet0, in0 = roundel(bx, by, HIP[0], HIP[1] + 0.03, 0.095, 3)  # small, on the hip joint: a big round one read as a ball with a leg stuck on it
    pet1, in1 = roundel(bx, by, 0.41, 0.03, 0.135, 3, 0.9)
    hole = hole * (~in0) * (~in1) + pet0 + pet1
    hole = hole * (1 - (thigh > 127) * sstep(0.1, 0.0, by))  # the net stops at the thigh, which is cut only along its muscle (see hind) and so reads as one mass
    bar = np.zeros_like(hole)

    # the saddle cloth: red film in a net, its lower edge scalloped
    scal = -0.09 - 0.022 * np.abs(np.sin(bx * np.pi / 0.085))
    cloth = sstep(-0.215, -0.205, bx) * sstep(0.175, 0.165, bx) * sstep(scal - 0.005, scal + 0.005, by)
    cloth = cloth * (c.body > 127) * (thigh <= 127)  # the thigh lies over the cloth's back corner
    net = lattice(bx, by, 0.046)
    hole = hole * (1 - cloth)
    c.red = np.maximum(c.red, (255 * cloth * net).astype(np.uint8))
    edge = cloth * (1 - sstep(0.012, 0.022, np.minimum(np.minimum(bx + 0.21, 0.17 - bx), by - scal)))
    bar = np.maximum(bar, np.maximum(edge, cloth * (1 - net)))

    c.hole = np.maximum((255 * np.clip(hole, 0, 1) * keep).astype(np.uint8), c.hole)
    inker = cv2.distanceTransform((np.maximum(c.body, c.near) > 127).astype(np.uint8), cv2.DIST_L2, 3) / pxcm / H
    contour = sstep(0.021, 0.014, inker) * (np.maximum(c.body, c.near) > 127)
    n_in = cv2.distanceTransform((c.near > 127).astype(np.uint8), cv2.DIST_L2, 3) / pxcm / H
    # no line over the croup: rump and thigh are one mass, and only the front of the thigh, from the flank down, is drawn across the barrel
    contour = np.maximum(contour, sstep(0.021, 0.014, n_in) * (c.near > 127) * np.where(thigh > 127, sstep(0.05, -0.03, by), 1.0))
    c.bar = np.maximum(c.bar, (255 * np.maximum(bar, contour)).astype(np.uint8))

    # the saddle, and the straps that hold it
    c.fill(catmull([b(-0.15, 0.22), b(-0.2, 0.33), b(-0.09, 0.285), b(0.06, 0.28), b(0.2, 0.345), b(0.16, 0.22)], 8), c.bar)
    c.fill(catmull([b(-0.1, 0.235), b(-0.11, 0.27), b(0.08, 0.265), b(0.11, 0.235)], 8), c.green)
    c.strip([b(0.17, 0.12), b(0.38, 0.1), b(0.6, -0.02)], [0.024 * H] * 2, c.bar)  # the breast strap
    c.strip([b(-0.21, 0.13), b(-0.42, 0.21), b(-0.58, 0.15)], [0.024 * H] * 2, c.bar)  # the crupper
    c.strip([b(0.02, 0.0), b(0.03, -0.2)], [0.03 * H] * 2, c.bar)  # the girth
    for x_, y_ in ((0.3, 0.113), (0.47, 0.06), (-0.33, 0.185), (-0.48, 0.2)):
        cv2.circle(c.bar, tuple(int(v) for v in c.q(b(x_, y_))), int(0.024 * H * pxcm * 16), 255, -1, cv2.LINE_AA, 4)
        cv2.circle(c.red, tuple(int(v) for v in c.q(b(x_, y_))), int(0.012 * H * pxcm * 16), 255, -1, cv2.LINE_AA, 4)

    # the head: ears, forelock, bridle, eye, nostril, mouth
    for a0, b0, a1, b1, w in ((0.0, 0.06, -0.08, 0.2, 0.062), (-0.04, 0.02, -0.15, 0.13, 0.05)):
        c.strip([at(a0, b0), at(0.5 * (a0 + a1), 0.5 * (b0 + b1) + 0.012), at(a1, b1)], np.array([w, w * 0.85, w * 0.1]) * H, c.bar)
    c.strip([poll + 0.02 * H * nd, at(0.07, 0.11), at(0.16, 0.08)], np.array([0.06, 0.035, 0.006]) * H, c.bar)
    c.strip([at(0.02, 0.05), at(0.14, -0.05), at(0.36, -0.07)], [0.016 * H] * 2, c.bar)  # the cheek strap, to the bit
    c.strip([at(0.3, 0.05), at(0.32, -0.075)], [0.016 * H] * 2, c.bar)  # the noseband
    c.strip([at(0.03, -0.14), at(0.13, -0.05), at(0.14, 0.05)], [0.012 * H] * 2, c.bar)
    eye = cv2.ellipse2Poly((0, 0), (100, 62), int(-np.degrees(nu - np.radians(70.0))), 0, 360, 15).astype(float) / 100
    c.fill(eye * 0.04 * H + at(0.125, 0.012), c.bar)
    c.fill(eye * 0.026 * H + at(0.125, 0.012), c.bar, 0)
    c.fill(eye * 0.026 * H + at(0.125, 0.012), c.hole)
    c.strip([at(0.385, 0.012), at(0.405, -0.006), at(0.4, -0.026)], np.array([0.006, 0.024, 0.008]) * H, c.hole)
    c.strip([at(0.34, -0.052), at(0.39, -0.054), at(0.43, -0.05)], np.array([0.006, 0.012, 0.006]) * H, c.bar)
    c.strip([at(0.2, -0.04), at(0.09, -0.1), at(0.02, -0.08)], np.array([0.004, 0.03, 0.004]) * H, c.hole)  # the cheek, cut

    # the mane: locks flung back from the crest, each its own taper
    cc = catmull(crest, 14)
    for j in range(11):
        f = (j + 0.5) / 11 + fixed.normal(0, 0.02)
        p0 = cc[int(np.clip(f, 0, 0.999) * len(cc))]
        L = H * (0.17 + 0.17 * fixed.uniform()) * (0.8 + 0.4 * np.sin(np.pi * f))
        w = H * fixed.uniform(0.04, 0.07)
        c.strip(curl(p0 - 0.012 * H * nn, L, np.radians(164 + fixed.normal(0, 9)) + pose.pitch, np.radians(fixed.normal(-14, 10)), np.radians(16), phi + 0.4 * f + fixed.normal(0, 0.05), 5), np.array([1.0, 0.9, 0.55, 0.05]) * w, c.bar)

    # the tail: a tied dock, then long locks streaming
    root = b(-0.595, 0.15)
    c.strip([b(-0.56, 0.17), root, root + np.array([-0.13, 0.06]) * H], np.array([0.08, 0.075, 0.07]) * H, c.bar)
    for j in range(11):
        f = (j + 0.5) / 11
        w = H * fixed.uniform(0.035, 0.07)
        c.strip(curl(root + np.array([-0.11, 0.05]) * H + fixed.normal(0, 0.012, 2) * H, H * (0.34 + 0.24 * fixed.uniform()), np.radians(158 + 32 * (f - 0.5) + fixed.normal(0, 4)), np.radians(22 + 30 * fixed.uniform()), np.radians(22), phi + fixed.normal(0, 0.06), 6), np.array([1.0, 0.92, 0.6, 0.28, 0.04]) * w, c.bar)

    # a tuft of red film at the chest, streaming back
    knot = b(0.6, -0.02)
    for j in range(9):
        w = H * fixed.uniform(0.014, 0.026)
        c.strip(curl(knot + fixed.normal(0, 0.006, 2) * H, H * fixed.uniform(0.2, 0.34), np.radians(205 + 40 * (j / 8 - 0.5) + fixed.normal(0, 4)), np.radians(fixed.normal(-8, 10)), np.radians(16), phi + fixed.uniform(-0.1, 0.1), 5), np.array([1.0, 0.95, 0.75, 0.2]) * w, c.red)
    c.strip([knot + np.array([0.014, 0.018]) * H, knot - np.array([0.014, 0.018]) * H], np.array([0.04, 0.046]) * H, c.bar)
    return c


# --- the ring ---------------------------------------------------------------------------------------------------
def ring_T(f, pxcm, cache):
    """The ring in flat coordinates (u along it, z up) at frame f: its filter colour T, and the axes. Horses further left are further on in the stride, because the ring's near
    side moves to the right, and it is the horse on the left that arrives where this one was."""
    umax = np.radians(84.0) * RI
    z1, z0 = ZG + V1 + 0.2, ZG - 0.8
    nx, ny = int(2 * umax * pxcm), int((z1 - z0) * pxcm)
    T = np.ones((ny, nx, 3), np.float32)
    S = 2 * np.pi * RI / N
    for i in range(-3, 4):
        k = (f - i) % N
        if k not in cache:
            cache[k] = cut_horse(k / N, pxcm).T()
        u = i * S + (f - 7) * DRIFT * RI + 0.15 * S
        x = (u + U0 + umax) * pxcm
        y = (z1 - (ZG + V1)) * pxcm
        M = np.float32([[1, 0, x], [0, 1, y]])
        T = T * cv2.warpAffine(cache[k], M, (nx, ny), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(1.0, 1.0, 1.0))
    # the ground: one thin strip of hide, a little uneven
    uu = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - umax
    zz = z1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    Uu, Zz = np.meshgrid(uu, zz)
    wander = 0.05 * np.sin(uu * 0.9 + 1.0) + 0.03 * np.sin(uu * 2.3)
    band = sstep(0.05, 0.03, np.abs(Zz - ZG + 0.05 - wander[None, :]))[..., None]
    T = T * (1 - band) + T_BAR[None, None] * band
    th = Uu / RI
    # the ring leans out at the top, as vanes must to catch the rising air: the heads lie closer to the paper and throw a sharper shadow than the feet
    Rz = RI + 0.14 * (Zz - (ZG + 3.0))
    P = np.stack([Rz * np.sin(th), -Rz * np.cos(th), Zz], -1).astype(np.float32)
    return P, T.astype(np.float32)


# --- the shade --------------------------------------------------------------------------------------------------
def paper_fibres(shape, pxcm, per_cm2, lo, hi, seed):
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 * per_cm2)
    a = rng.uniform(0, np.pi, n)
    length = rng.uniform(lo, hi, n) * pxcm / 5.0
    px, py = rng.uniform(0, nx, n), rng.uniform(0, ny, n)
    pts = [np.stack([px, py], -1)]
    for _ in range(5):
        a = a + rng.normal(0, 0.28, n)
        px, py = px + length * np.cos(a), py + length * np.sin(a)
        pts.append(np.stack([px, py], -1))
    canvas = np.zeros(shape, np.uint8)
    cv2.polylines(canvas, list(np.round(np.stack(pts, 1) * 8).astype(np.int32)), False, 255, 1, cv2.LINE_AA, shift=3)
    return canvas.astype(np.float32) / 255.0


def rib_dist(th):
    """Distance in angle to the nearest rib of the cage."""
    step = 2 * np.pi / NRIB
    return np.abs(((th - RIB0 + step / 2) % step) - step / 2)


def hg(c, g):
    """Henyey-Greenstein, 1 straight through."""
    return (1 - g) ** 3 / (1 + g * g - 2 * g * c) ** 1.5


def build_shade(q, pxcm, cam, flame, d):
    """The paper, seen from this camera with this flame: colour per vertex. Returns the file."""
    th0 = np.radians(78.0)
    z0, z1 = -21.0, 0.4
    Rm = rad(-8.0)
    nx, ny = int(2 * th0 * Rm * pxcm), int((z1 - z0) * pxcm)
    shape = (ny, nx)
    print("shade", nx, ny, nx * ny / 1e6, "M", flush=True)
    th = np.linspace(-th0, th0, nx, dtype=np.float32)
    z = np.linspace(z1, z0, ny, dtype=np.float32)
    TH, Z = np.meshgrid(th, z)
    # paper taut between the ribs, drawn in a little, and never quite flat
    dist = rib_dist(TH)
    step = 2 * np.pi / NRIB
    sag = 0.16 * (dist / (step / 2)) ** 1.5
    wr = 0.035 * fbm(shape, pxcm, 1.0, 7.0, 2.4, SEED + 20) + 0.012 * fbm(shape, pxcm, 0.3, 1.5, 2.2, SEED + 21)
    r = rad(Z) - sag + wr
    P = np.stack([r * np.sin(TH), -r * np.cos(TH), Z], -1).astype(np.float32)

    # thin and thick: flocs, cloud, long fibres that show as dark threads against the light
    flocs = fbm(shape, pxcm, 0.1, 1.1, 2.1, SEED + 22)
    cloud = rank(fbm(shape, pxcm, 1.5, 11.0, 2.6, SEED + 23))
    fib = cv2.GaussianBlur(paper_fibres(shape, pxcm, 7, 0.5, 2.2, SEED + 24), (0, 0), max(0.5, pxcm / 110.0))
    fib2 = cv2.GaussianBlur(paper_fibres(shape, pxcm, 120, 0.08, 0.32, SEED + 25), (0, 0), max(0.45, pxcm / 150.0))
    thick = 1.0 + 0.1 * flocs + 0.16 * (cloud - 0.5) + 0.16 * fib * (0.45 + 1.1 * cloud) + 0.08 * fib2
    # a second layer glued over each rib, with an uneven edge
    u_cm = dist * rad(Z)
    seam = sstep(0.1, -0.1, u_cm - 0.42 - 0.1 * fbm(shape, pxcm, 0.5, 4.0, 2.4, SEED + 26))
    thick = thick + 0.26 * seam

    # old paper: soot gathered under the rim
    soot = sstep(-6.0, -0.8, Z + 0.7 * fbm(shape, pxcm, 1.0, 8.0, 2.6, SEED + 28))

    # the forward lobe. What comes straight through has scattered least, so it is yellower; what has wandered is deeper
    loc = np.array(cam["loc"], np.float32)
    v = P - loc
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    l = P - np.array(flame, np.float32)
    l /= np.linalg.norm(l, axis=-1, keepdims=True)
    lobe = hg((v * l).sum(-1), 0.68)
    nrm = np.stack([np.sin(TH), -np.cos(TH), np.zeros_like(TH)], -1)
    cos_v = np.maximum(np.abs((v * nrm).sum(-1)), 0.08)
    path = (1.6 - 1.0 * lobe) * cos_v**-0.55

    base = color([1.0, 0.79, 0.53])
    col = base[None, None] ** (thick * path)[..., None]

    # a band painted by hand under the rim, streaky with the brush
    streak = cv2.resize(fbm((ny, max(nx // 30, 8)), pxcm, 0.03, 0.5, 1.8, SEED + 32), (nx, ny), interpolation=cv2.INTER_LINEAR)
    band_z = -1.05 + 0.07 * fbm(shape, pxcm, 0.4, 3.0, 2.4, SEED + 27)
    band = sstep(-0.03, 0.03, Z - band_z + 0.012 * streak)[..., None]
    dye = color([1.0, 0.13, 0.05])[None, None] ** (1.0 + 0.3 * streak + 0.1 * flocs)[..., None]
    col = col * (1 - band) + col * dye * band
    col = col * np.exp(-0.75 * soot * (0.7 + 0.6 * cloud))[..., None]
    col = col * (0.2 + 6.2 * lobe)[..., None]
    p = os.path.join(d, f"shade.{q}.npz")
    np.savez(p, P=P, col=col.astype(np.float32))
    return p


def build_cage(q, d):
    """The ribs just inside the paper; only their shadow shows."""
    th = np.linspace(-np.radians(80), np.radians(80), 2600, dtype=np.float32)
    z = np.linspace(0.3, -21.0, 700, dtype=np.float32)
    TH, Z = np.meshgrid(th, z)
    u = rib_dist(TH) * rad(Z)
    nodes = 0.035 * np.exp(-((((Z + 3.0) % 9.0) - 4.5) / 0.16) ** 2)
    wob = 0.02 * cv2.resize(fbm((700, 16), 32.0, 0.5, 6.0, 2.4, SEED + 33), (TH.shape[1], TH.shape[0]), interpolation=cv2.INTER_CUBIC)
    rib = sstep(0.125, 0.095, u + wob - nodes)
    T = np.ones(TH.shape + (3,), np.float32) * (1 - rib[..., None]) + color([0.02, 0.012, 0.008]) * rib[..., None]
    r = rad(Z) - 0.3
    p = os.path.join(d, f"cage.{q}.npz")
    np.savez(p, P=np.stack([r * np.sin(TH), -r * np.cos(TH), Z], -1).astype(np.float32), T=T.astype(np.float32))
    return p


def build_rim(q, dens, d):
    """A bent bamboo hoop, lacquered: turned about the axis."""
    r0 = rad(0.0)
    prof = Profile([(r0 - 0.15, -0.62), (r0 + 0.5, -0.62), (r0 + 0.62, -0.5), (r0 + 0.62, 0.36), (r0 + 0.5, 0.48), (r0 - 0.15, 0.48)], sigma=0.04, ds=0.002)
    ns, nt = int(420 * dens), int(5200 * dens)
    S = np.linspace(0, prof.L, ns, dtype=np.float32)
    th = np.linspace(-np.radians(86), np.radians(86), nt, dtype=np.float32)
    TH, SS = np.meshgrid(th, S)
    r, z, _, _ = prof.at(SS)
    grain = cv2.resize(fbm((ns, max(nt // 24, 8)), 40.0, 0.01, 0.5, 1.8, SEED + 30), (nt, ns), interpolation=cv2.INTER_LINEAR)
    cloud = cv2.resize(fbm((64, 1024), 30.0, 0.2, 3.0, 2.4, SEED + 31), (nt, ns), interpolation=cv2.INTER_CUBIC)
    c = color([0.1, 0.034, 0.016])[None, None] * (1 + 0.28 * grain + 0.25 * cloud)[..., None]
    rough = (0.27 + 0.05 * grain + 0.05 * cloud).clip(0.08, 0.7).astype(np.float32)
    p = os.path.join(d, f"rim.{q}.npz")
    np.savez(p, P=np.stack([r * np.sin(TH), -r * np.cos(TH), z], -1).astype(np.float32), col=np.clip(c, 0, 1).astype(np.float32), rough=rough)
    return p, np.stack([(r0 + 0.62) * np.sin(th), -(r0 + 0.62) * np.cos(th), np.full_like(th, 0.48)], -1)


def flame_at(f):
    """The flame trembles: where it stands and how strong it is, the same every run."""
    rng = np.random.default_rng(SEED + 40)
    k = np.ones(3) / 3.0
    # the first take had 15 frames: its 17 draws per series come first and in the same order, so those frames stay what they were; the rest follow after
    first = rng.normal(0, 1, (4, 17))
    more = rng.normal(0, 1, (4, FRAMES - 15))
    w, x, y, z = [np.convolve(np.r_[first[i], more[i]], k, "same")[:FRAMES] for i in range(4)]
    return np.array([0.22 * x[f], 0.22 * y[f], ZF + 0.3 * z[f]]), 1.0 + 0.09 * w[f]


def far_lanterns(cam, d):
    """Other lanterns up the street at night, far behind and out of focus. Real spheres, so the discs are the lens's own. The placing is by eye."""
    right, up, back = _cam_axes(cam)
    loc = np.array(cam["loc"], float)
    w = 36.0 / cam["lens_mm"]
    h = w * 9.0 / 16.0
    a, b = np.meshgrid(np.linspace(0, np.pi, 24), np.linspace(0, 2 * np.pi, 48))
    unit = np.stack([np.sin(a) * np.cos(b), np.sin(a) * np.sin(b), np.cos(a)], -1)
    out = []
    for i, (x, y, D, r, tint) in enumerate(((0.07, 0.26, 520, 3.6, 1.0), (0.2, 0.05, 900, 3.2, 0.32), (0.31, 0.2, 760, 2.4, 0.55), (0.66, 0.07, 1000, 3.0, 0.3), (0.83, 0.17, 620, 4.2, 0.85))):
        ray = -back + right * (x - 0.5) * w + up * (0.5 - y) * h
        c = loc + D * ray / np.linalg.norm(ray)
        p = os.path.join(d, f"far{i}.npz")
        np.savez(p, P=(c + r * unit).astype(np.float32))
        e = FAR_GLOW * tint
        out.append({"name": f"far{i}", "npz": p, "material": {"Base Color": [0.0, 0.0, 0.0], "Emission Color": [e, e * 0.2, e * 0.04], "Emission Strength": 1.0, "Roughness": 1.0, "Specular IOR Level": 0.0}, "visible": {"diffuse": False, "shadow": False}})
    return out


def scene_for(f, q, dens, shade, cage, rim, cam, ring_npz, gain, far):
    shader = os.path.join(ROOT, "v2", "stills", "s54_shader.py")
    loc, k = flame_at(f)
    return {
        "camera": dict(cam),
        "meshes": [
            {"name": "shade", "npz": shade, "shader_py": shader, "params": {"kind": "paper", "amb": 0.014 * gain * k}},
            {"name": "cage", "npz": cage, "shader_py": shader, "params": {"kind": "gobo"}},
            {"name": "ring", "npz": ring_npz, "shader_py": shader, "params": {"kind": "gobo"}},
            {"name": "rim", "npz": rim, "material": {"Base Color": "col", "Roughness": "rough"}},
            *[dict(m) for m in far],  # shoot() rewrites a mesh entry to its remote path, so each frame needs its own
        ],
        # a flame is taller than it is wide, so shadows are softer across their top and bottom edges than up their sides: three lights up its height
        "lights": [{"name": f"flame{i}", "type": "point", "loc": (loc + np.array([0.0, 0.0, dz])).tolist(), "radius": rd, "watts": 2000.0 * gain * k * sh, "rgb": [1.0, 0.72, 0.42]} for i, (dz, rd, sh) in enumerate(((-0.55, 0.24, 0.42), (0.0, 0.22, 0.38), (0.6, 0.12, 0.2)))],
        "world": [0.0, 0.0, 0.0],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "transmission_bounces": 4,
        "spp": {"preview": 64, "mid": 128, "final": 256},
    }


def camera_for(rim_top, dens=1.0):
    view = np.array([0.0, -np.cos(np.radians(EL)), -np.sin(np.radians(EL))])
    focus = np.array([0.0, -rad(-5.0), -5.0])
    cam, sag = fit_arc(rim_top, view, W, DIST, apex=(0.5, 0.38), target0=(0.0, -22.0, -6.0), aperture_mm=16.0, focus_point=focus)
    print("sag", round(sag, 3))
    return cam


def cut_sheet(pxcm=60.0):
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cols, tw = 3, 860
    th = int(tw * (V1 - V0) / (U1 - U0))
    out = np.zeros((3 * th, cols * tw, 3), np.uint8)
    for k in range(N):
        im = np.array([235, 190, 120], np.float32)[None, None] * cut_horse(k / N, pxcm).T() ** 0.55  # opened up to see the carving; the render uses T itself
        out[(k // cols) * th : (k // cols + 1) * th, (k % cols) * tw : (k % cols + 1) * tw] = cv2.resize(cv2.GaussianBlur(im, (0, 0), 1.2).astype(np.uint8), (tw, th), interpolation=cv2.INTER_AREA)
    p = os.path.join(d, "cut.jpg")
    cv2.imwrite(p, out[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(p)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if mode == "cut":
        cut_sheet()
        return
    take = mode in ("take", "ext")
    q = (sys.argv[2] if len(sys.argv) > 2 else "preview") if take else mode
    dens = {"preview": 0.45, "mid": 0.6, "final": 1.0}[q]
    gain = 21.0
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    rim, rim_top = build_rim(q, dens, d)
    cam = camera_for(rim_top)
    x, y, _ = project(cam, np.array([[0.0, -rad(-10.6), -10.6], [0.0, -rad(-5.0), -5.0]]))
    print("ground line at y", round(float(y[0]), 3), "centre at", round(float(y[1]), 3), flush=True)
    shade = build_shade(q, 75.0 * dens, cam, [0.0, 0.0, ZF], d)
    cage = build_cage(q, d)
    far = far_lanterns(cam, d)
    cache = {}
    look = {"exposure": 0.78, "contrast": 1.2, "saturation": 1.12, "black": 0.002, "grain": 1.25, "sharpen": 0.2, "halation": 0.14, "glare": 0.004, "vignette": 0.22}
    # S54_TAKE keeps a new take out of the folder the film reads until it has been checked: S54_TAKE=cand writes to s54_zoumadeng_take_cand
    name = (f"{NAME}_take_ext" if mode == "ext" else f"{NAME}_take_{os.environ.get('S54_TAKE', q)}") if take else NAME
    for f in (range(14, FRAMES) if mode == "ext" else range(FRAMES) if take else [7]):
        if take and os.path.exists(os.path.join(OUT, name, f"f{f:03d}.png")):
            continue
        P, T = ring_T(f, 70.0 * max(dens, 0.6), cache)
        ring = os.path.join(d, f"ring.{q}.npz")
        np.savez(ring, P=P, T=T)
        shoot(name, scene_for(f, q, dens, shade, cage, rim, cam, ring, gain, far), q, tag=f"f{f:03d}" if take else None, develop={**look, "seed": 500 + f})


main()
