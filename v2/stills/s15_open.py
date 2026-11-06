"""Shot 15, the fan opening: the motion of the sticks and the skin that hangs the same paper, gold and sticks from it. Used by s15_zheshan.py open; nothing here renders.


Motion of the sticks, solved, not keyframed (every stick is a body about the pin, radians and seconds, inertia in units of an inner stick):
- two hands' worth of intent: the thumb pushes the leading guard, the wrist takes the rear guard back a little later and more slowly. Each guard follows its target through a compliant spring (a hand is not a servo);
- the inner sticks are not driven. They sit in pin friction until the paper between them and their neighbour goes taut, so the opening travels stick by stick. The paper pulls softly as a pleat flattens and hard when it is flat;
- air drag on each stick's share of paper; a stick stops when nothing pulls it;
- at the end the taut sheet stops the guards dead, and the hand gives and recovers: that is the rebound;
- the far ends of the sticks and the paper lag and overshoot the roots: each stick's tip is its root through a damped oscillator, then limited so that no pleat at the rim opens wider than the paper.

Paper that does not stretch. Faces are flat sectors; a face's chord per cm of radius is fixed by the rest pose, f^2 = (2 sin(d0/2))^2 + a0^2, so at any opening its fold depth is a = sqrt(f^2 - (2 sin(d/2))^2), per cm of radius. Crease heights follow the zigzag, each face dropping exactly a[i]; a slow drift of the sheet's middle is let go (its slope per face is tiny, stretch() measures it). Odd creases have no stick: they sit between their neighbours, in the ratio of the two face widths (the exact point differs by much less than the wander of the crease). No scaling anywhere.
Everything on the paper is addressed in paper coordinates (r, face index), so it cannot slide: colour and transmission are vertex attributes decided at rest; bow and lift turn with their face (see _pose); the wander of a crease scales with the opening.

Near the pin the sticks stack along it, as they do in a closed fan: below the paper, in proportion to how closed each is.

ESTIMATED, nothing measured on a real fan or on film of one: every number in ARG. The motion was judged by eye against what a hand does; no footage of a fan being opened was looked at. Taken as filmed at about twice speed (the sweep on screen takes about half a second, a hand's flick about a quarter): an assumption.
The faces belly back as they sweep: a stand-in for air pressure, a bow of `billow` of a face's width in proportion to its speed and to how much it faces the motion, not a solve; each face has its own factor.
NOT solved: the paper's own dynamics (no real flutter, only that bow and the bending of the whole stick), air flow, contact between pleats (they may touch through each other when nearly shut, at a scale not seen in the frame), and the flat-folded wedge of a fully shut fan: this fan never fully shuts, it starts at about OPEN0 degrees.
"""

import numpy as np
import scipy.ndimage as ndi

ARG = {
    "phi0": (-14.0, 2.0),  # degrees: where the guards start; nearly shut, standing at the top of the frame, so that the rim is under the caption from the first frame
    "t_go": 0.14,  # s: the lead starts
    "w_lead": 310.0,  # deg/s, on screen
    "grow_lead": (0.62, 1.32),  # the hand speeds up through the sweep, from this much of w to this much
    "grow_rear": (0.85, 1.12),
    "billow": 0.075,  # of a face's width, at 310 deg/s: air pushes the faces back as they sweep
    "rise_lead": 0.09,
    "t_rear": 0.19,
    "w_rear": 225.0,
    "rise_rear": 0.1,
    "wind": 1.8,  # degrees: the thumb takes up, the fan gathers, before it goes
    "over": 2.0,  # degrees the hand keeps pushing past the stop, and lets go of
    "over_rear": 4.5,  # the wrist drags behind the sheet, so it has further to mean to go
    "Kh": 1800.0,  # hand spring, per unit inertia of a guard
    "Dh": 60.0,
    "Ig": 3.5,  # inertia of a guard
    "K": 2.6e4,  # the taut paper, in tension
    "C": 60.0,  # its loss
    "Ks": 70.0,  # the soft pull of a pleat as it flattens
    "ps": 5.0,
    "mu": 14.0,  # pin friction, rad/s^2
    "drag": 1.5,  # per (rad/s)^2
    "visc": 3.0,
    "Kc": 6000.0,  # the stack pushes back when two sticks lie on each other
    "gap": 0.12,  # of a stick's share of the opening: the closest two sticks get
    "tip_hz": 11.0,
    "tip_z": 0.32,
    "tip_w": 1.0,
    "stack": 2.2,  # cm along the pin, sticks in a stack
    "dt": 1.0e-4,
    "seed": 15,
    "t_rest": 0.62,
}


def smooth(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


class Hand:
    """Where the hand means a guard to be, and its speed. Takes up slack backwards; then it speeds up all the way, for a hand has no reason to slow before the stop: it goes until the sheet stops it, then lets go."""

    def __init__(self, start, end, t0, w, rise, wind, over, grow):
        self.start, self.end, self.t0, self.wind, self.over = start, end, t0, np.radians(wind), np.radians(over)
        self.sgn = np.sign(end - start)
        span = abs(end - start) + self.over
        du = 1e-3
        u = np.arange(0, 3.0, du)
        w = np.radians(w)
        self.u = u
        self.v = w * smooth(u / rise) * (grow[0] + (grow[1] - grow[0]) * np.minimum(u / 0.34, 1.0))
        self.d = np.cumsum(self.v) * du - self.wind * (1 - smooth(u / 0.06))
        self.te = t0 + float(u[np.argmax(self.d >= span)])

    def __call__(self, t):
        u = t - self.t0
        if u <= 0:
            return self.start - self.sgn * self.wind * smooth((t - (self.t0 - 0.16)) / 0.14), 0.0
        if t < self.te:
            i = int(u / 1e-3)
            return self.start + self.sgn * self.d[i], self.sgn * self.v[i]
        return self.end + self.sgn * self.over * np.exp(-(t - self.te) / 0.09), 0.0


def solve(c, times, a=None):
    """c: the crease angles at rest (rad, NFACE + 1). times in s. Returns theta (times, nsticks) at the root, tip likewise: rad; and the speed of the tips, rad/s."""
    a = dict(ARG, **(a or {}))
    C0 = np.asarray(c, float)[::2]
    L = np.diff(C0)
    n = len(C0)
    rng = np.random.default_rng(a["seed"])
    start, stop = np.radians(a["phi0"][0]), np.radians(a["phi0"][1])
    sh = L * np.exp(rng.normal(0, 0.35, n - 1))  # shut unevenly: a pack, not a comb
    th = start + np.r_[0, np.cumsum(sh)] / sh.sum() * (stop - start)
    om = np.zeros(n)
    Iv = np.ones(n)
    Iv[0] = Iv[-1] = a["Ig"]
    gap0 = a["gap"] * (stop - start) / (n - 1)
    st = np.array(th)
    sv = np.zeros(n)
    wn = 2 * np.pi * a["tip_hz"]
    dt = a["dt"]
    Tmax = float(np.max(times)) + 0.2
    pre = 0.5  # settle before anything happens, so that the first frame is at rest and the pack has found itself
    steps = int((Tmax + pre) / dt) + 1
    out, tip, spd = np.zeros((len(times), n)), np.zeros((len(times), n)), np.zeros((len(times), n))
    hold = a["Ks"] / (a["Kh"] * a["Ig"])  # what the hand must give so that it comes to rest with the sheet just flat: the rest pose, exactly
    lead = Hand(stop, C0[-1] + hold, a["t_go"], a["w_lead"], a["rise_lead"], a["wind"], a["over"], a["grow_lead"])
    rear = Hand(start, C0[0] - hold, a["t_rear"], a["w_rear"], a["rise_rear"], a["wind"] * 0.6, a["over_rear"], a["grow_rear"])
    order = np.argsort(times)
    nxt = 0
    for s in range(steps):
        t = -pre + s * dt
        dl = th[1:] - th[:-1]
        dv = om[1:] - om[:-1]
        ex = dl - L
        F = a["Ks"] * np.maximum(dl / L, 0) ** a["ps"]
        F = F + np.where(ex > 0, a["K"] * ex + a["C"] * dv, 0.0)
        F = np.maximum(F, 0.0)
        F = F - np.where(dl < gap0, a["Kc"] * (gap0 - dl) - 20.0 * dv, 0.0)
        tau = np.zeros(n)
        tau[:-1] += F
        tau[1:] -= F
        tl, wl = lead(t)
        tr, wr = rear(t)
        tau[-1] += a["Kh"] * Iv[-1] * (tl - th[-1]) + a["Dh"] * Iv[-1] * (wl - om[-1])
        tau[0] += a["Kh"] * Iv[0] * (tr - th[0]) + a["Dh"] * Iv[0] * (wr - om[0])
        acc = tau / Iv - (a["drag"] * np.abs(om) + a["visc"]) * om
        om = om + dt * acc
        # pin friction: it can stop a stick, it cannot reverse it
        fr = a["mu"] * dt
        inner = np.ones(n, bool)
        inner[0] = inner[-1] = False
        om[inner] = np.sign(om[inner]) * np.maximum(np.abs(om[inner]) - fr, 0.0)
        th = th + dt * om
        # sticks do not pass through each other: anything the stack's spring has not held is held here, inner sticks giving way to the guards
        lo = gap0 * 0.3
        for j in range(1, n - 1):
            if th[j] - th[j - 1] < lo:
                th[j] = th[j - 1] + lo
                om[j] = max(om[j], om[j - 1])
        for j in range(n - 2, 0, -1):
            if th[j + 1] - th[j] < lo:
                th[j] = th[j + 1] - lo
                om[j] = min(om[j], om[j + 1])
        sa = wn * wn * (th - st) - 2 * a["tip_z"] * wn * sv
        sv = sv + dt * sa
        st = st + dt * sv
        if not np.isfinite(th).all():
            raise SystemExit(f"open: the solve blew up at t = {t:.3f}")
        while nxt < len(times) and t + dt / 2 >= times[order[nxt]]:
            out[order[nxt]] = th
            tip[order[nxt]] = st
            spd[order[nxt]] = sv
            nxt += 1
    if nxt != len(times):
        raise SystemExit("open: a time was not reached")
    # no pleat opens wider than the paper, at the root or at the rim: the taut spring's give is the solve's, not the paper's. Built outwards from the middle stick
    m = n // 2

    def limit(x, top):
        d = np.clip(np.diff(x, axis=1), 1e-5, L * top)
        y = x.copy()
        y[:, m + 1 :] = x[:, m : m + 1] + np.cumsum(d[:, m:], axis=1)
        y[:, :m] = x[:, m : m + 1] - np.cumsum(d[:, :m][:, ::-1], axis=1)[:, ::-1]
        return y

    out = limit(out, 1.0)
    tp = out + a["tip_w"] * (limit(tip, 1.002) - out)
    # what is left of the solve's error at rest goes, over the last of the settling: the last frame is the still's pose
    if a.get("t_rest") is not None:
        u = smooth((np.asarray(times) - a["t_rest"]) / 0.2)[:, None]
        out = out + (C0 - out) * u
        tp = tp + (C0 - tp) * u
    return out, tp, spd


def creases(c, theta):
    """All crease angles from the stick angles (.., nsticks), each odd crease between its neighbours in the ratio of its two faces."""
    c = np.asarray(c, float)
    d0 = np.diff(c)
    ratio = d0[::2] / (d0[::2] + d0[1::2])
    out = np.zeros(theta.shape[:-1] + (len(c),))
    out[..., ::2] = theta
    out[..., 1::2] = theta[..., :-1] + (theta[..., 1:] - theta[..., :-1]) * ratio
    return out


class Pleats:
    """Crease heights per cm of radius, from the crease angles."""

    def __init__(self, c, amp):
        self.c0 = np.asarray(c, float)
        self.amp = np.asarray(amp, float)
        self.d0 = np.diff(self.c0)
        self.a0 = 0.31 * self.d0 * (self.amp[:-1] + self.amp[1:])
        self.f2 = 4 * np.sin(self.d0 / 2) ** 2 + self.a0**2
        n = len(self.d0)
        B = np.zeros((n, n + 1))
        B[np.arange(n), np.arange(n)] = 1
        B[np.arange(n), np.arange(n) + 1] = 1
        self.Bp = np.linalg.pinv(B)
        self.B = B

    def __call__(self, C):
        d = np.diff(C)
        if (d <= 0).any():
            raise SystemExit(f"open: creases crossed, min {np.degrees(d.min()):.3f} deg")
        a = np.maximum(np.sqrt(np.maximum(self.f2 - 4 * np.sin(d / 2) ** 2, 0.0)), 0.5 * self.a0)  # the floor: a sliver of the tip's overshoot, not a flat sheet
        k = a / self.a0
        kk = np.r_[k[0], 0.5 * (k[1:] + k[:-1]), k[-1]]
        dd = np.r_[self.d0[0], 0.5 * (self.d0[1:] + self.d0[:-1]), self.d0[-1]]
        sg = np.where(np.arange(len(C)) % 2 == 0, 1.0, -1.0)
        ref = sg * 0.31 * self.amp * dd * kk  # where this crease would be if the sheet stayed flat on average
        # the zigzag, face by face: each face drops exactly its depth. Where a deep part meets a shallow one the sheet's middle has to move: it does, as paper does
        Y = np.r_[0.0, np.cumsum(-sg[:-1] * a)]
        m = Y - ref
        m = m - m.mean()
        lo = ndi.gaussian_filter1d(m, 8.0, mode="nearest")
        Y = ref + m - 0.7 * lo  # a slow drift of the middle of the sheet is let go, its slope per face is tiny; measured by stretch()
        ht = sg * Y
        if (ht[:-1] + ht[1:] <= 0).any():
            raise SystemExit("open: a face turned over")
        return {"C": C, "H": Y, "tilt": np.arctan2(a, 2 * np.sin(d / 2)), "rho": np.r_[d[0] / self.d0[0], 0.5 * (d[1:] / self.d0[1:] + d[:-1] / self.d0[:-1]), d[-1] / self.d0[-1]]}


def air_load(P, om_creases, k, a):
    """The bow of each face from the air, as a fraction of its width, signed so that it goes against the motion. om_creases in rad/s."""
    om = 0.5 * (om_creases[:-1] + om_creases[1:])
    return -a["billow"] * k * om / np.radians(310.0) * np.sin(P["tilt"])


def closed(P, c0_d):
    """1 where a crease is packed, 0 where it is open."""
    u = (P["rho"] - 0.25) / 0.45
    return 1 - smooth(u)


def rigid(t, a=None):
    """The hand itself: the fan's plane comes round and upright as it opens, and the pin moves a little. Rotations in rad about x (leaning towards the camera) and about z, pin offset in cm. All end at nothing: the last frame is the still's pose."""
    t = np.asarray(t, float)
    a = dict(ARG, **(a or {}))
    go = a["t_go"]
    s = smooth((t - go + 0.08) / 0.44)
    u = t - (go + 0.36)
    rec = np.where(u > 0, np.exp(-u / 0.13) * np.sin(2 * np.pi * 3.1 * u), 0.0)
    pre = smooth((t - go + 0.2) / 0.16) * (1 - smooth((t - go + 0.02) / 0.1))
    rx = np.radians(7.0 * (1 - s) + 1.1 * rec + 0.6 * pre)
    rz = np.radians(-10.0 * (1 - s) - 0.7 * rec)
    dz = -0.9 * (1 - s) + 0.28 * rec - 0.2 * pre
    dx = -0.5 * (1 - s) + 0.1 * rec
    return rx, rz, dx, dz


def apply_rigid(P, rx, rz, dx, dz):
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    cx, sx = np.cos(rx), np.sin(rx)
    y1, z1 = y * cx - z * sx, y * sx + z * cx
    cz, sz = np.cos(rz), np.sin(rz)
    x1, y2 = x * cz - y1 * sz, x * sz + y1 * cz
    return np.stack([x1 + dx, y2, z1 + dz], -1).astype(np.float32)


class Static:
    """What a set of points on the paper keeps through the whole motion: taken once from (r, f), as Fan.surf would."""

    def __init__(self, fan, r, f, R0, R1, nface, at, lift=None):
        r, f = np.asarray(r, np.float32), np.asarray(f, np.float32)
        self.r = r
        self.f = f
        i = np.clip(np.floor(f).astype(np.int32), 0, nface - 1)
        self.i = i
        self.t = f - i
        self.sgn = np.where(i % 2 == 0, 1.0, -1.0).astype(np.float32)
        s = np.clip((r - R0) / (R1 - R0), 0, 1)
        self.s = s
        wa = lambda k: _wander(fan, k, s)
        self.w0, self.w1 = wa(i), wa(i + 1)
        a0, a1 = fan.c[i] + self.w0 * 0.0011, fan.c[i + 1] + self.w1 * 0.0011
        hw = np.maximum(r * (a1 - a0), 1e-3)
        sj = s * 38.999
        j = sj.astype(np.int32)
        bt = fan.b_t[i, j] * (1 - (sj - j)) + fan.b_t[i, j + 1] * (sj - j)
        self.bow = ((0.03 * hw * fan.bow[i] + 0.04 * hw * bt) * 4 * self.t * (1 - self.t) * 1.6).astype(np.float32)
        fx, fy = (f / nface * 1023).astype(np.float32), (s * 255).astype(np.float32)
        self.wave = (0.04 * at(fan.wav, fx, fy) * s + 0.016 * at(fan.wav2, fx, fy)).astype(np.float32)
        self.lift = None if lift is None else np.asarray(lift, np.float32)
        self.w = (s * s).astype(np.float32)
        self.u = (hw * 4 * self.t * (1 - self.t) * s).astype(np.float32)  # the shape of a face pushed by the air: nothing at its creases, nothing near the sticks' roots


def _wander(fan, k, s):
    sj = s * 39
    j = np.floor(sj).astype(np.int32)
    j1 = np.minimum(j + 1, 39)
    u = sj - j
    return fan.w_l[k, j] * (1 - u) + fan.w_l[k, j1] * u


def pose_points(S, PA, PB, tilt0, stack):
    """The points of S at a pose: PA at the root, PB at the tip, blended along the radius by S.w. The fan's own frame: no rigid motion yet."""
    i, t, w = S.i, S.t, S.w
    def blend(key, k):
        return PA[key][k] * (1 - w) + PB[key][k] * w
    a0 = blend("C", i) + S.w0 * 0.0011 * blend("rho", i)
    a1 = blend("C", i + 1) + S.w1 * 0.0011 * blend("rho", i + 1)
    H0, H1 = blend("H", i), blend("H", i + 1)
    phi = a0 + (a1 - a0) * t
    y = (H0 * (1 - t) + H1 * t) * S.r
    # what stands off a face turns with the face: at rest it is along y
    psi = -S.sgn * (blend("tilt", i) - tilt0[i])
    v = S.sgn * S.bow
    if S.lift is not None:
        v = v - S.lift
    if "air" in PA:
        v = v + S.u * (PA["air"][i] * S.sgn)
    phi = phi - v * np.sin(psi) / np.maximum(S.r, 1.0)
    y = y + v * np.cos(psi) + S.wave
    if stack is not None:
        G = PA["G"]
        g = G[i] * (1 - t) + G[i + 1] * t
        y = y + stack * (S.f / (len(G) - 1) - 0.5) * g * (1 - 0.55 * S.s)
    return np.stack([S.r * np.sin(phi), y, S.r * np.cos(phi)], -1)


def stretch(pose, r, c0, a0):
    """Measured on the crease skeleton: how far each face's true chord at radius r is from its chord at rest, as a fraction. The check that the paper does not stretch."""
    C, H = pose["C"], pose["H"]
    d = np.diff(C)
    ch = np.sqrt(4 * np.sin(d / 2) ** 2 + (H[1:] - H[:-1]) ** 2)
    d0 = np.diff(c0)
    ch0 = np.sqrt(4 * np.sin(d0 / 2) ** 2 + a0**2)
    return ch / ch0 - 1
