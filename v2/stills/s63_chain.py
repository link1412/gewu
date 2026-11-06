"""The strand's dynamics for shot 63 (南红念珠): a real simulation in numpy, no key frames. Units: cm, s, grams. One integer seed sets the whole thing.

An open length of drilled spheres on one elastic thread, lying on a lacquer table:
- thread: pulls only when neighbours part further than its length (one sided, compliant, damped), so a jerk travels at a finite speed;
- bead on bead (neighbours up to 3 apart) and bead on table: one sided contact, restitution, Coulomb friction, solved as impulses on velocity and spin. Spin is never prescribed;
- the hole: outside its clearance, the thread turns the bead towards the thread's direction [a stand-in, not a model of the contact inside the hole];
The hand, out of frame, holds one bead of the right leg and jerks it (run), or lays the strand down along a planned curve (run_lay); nothing else moves the strand.
All coefficients are ESTIMATES; none was measured.
"""

import numpy as np

G = 981.0
RHO = 2.6
DT = 1.0 / 6000.0
CORD_K = 2.5e5  # dyn/cm between neighbours [estimate]
CORD_C = 8.0  # g/s [estimate]
MU_TABLE = 0.4  # stone on lacquer [estimate]
MU_BEAD = 0.2  # stone on stone [estimate]
E_TABLE = 0.35
E_BEAD = 0.55


def qmul(a, b):
    w1, x1, y1, z1 = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    w2, x2, y2, z2 = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], -1)


def qrot(q, v):
    u = q[..., 1:]
    return v + 2.0 * np.cross(u, np.cross(u, v) + q[..., :1] * v)


def qmat(q):
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], -1), np.stack([2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)], -1), np.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1)], -2)


def axis_quat(a_to):
    z = np.array([0.0, 0.0, 1.0])
    q = np.concatenate([(1 + a_to @ z)[..., None], np.cross(z, a_to)], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)


def lay_out(n, seed, Rr, gr, theta_max, s0):
    """The strand as dropped: an arch in the table's plane, y away from the camera, its middle at the apex, both legs running back towards the camera. Heading turns as tanh of arc length; a slow unevenness, as a hand lays it down."""
    r = np.random.default_rng(seed)
    R = r.uniform(Rr[0], Rr[1], n)
    gap = r.uniform(gr[0], gr[1], n - 1)
    L = R[:-1] + R[1:] + gap
    p1, p2 = r.uniform(0, 6, 2)
    def walk(sign, lengths):
        p, out = np.zeros(2), []
        s_, sub = 0.0, 0.02
        for l in lengths:
            left = l
            while left > 0:
                h = min(sub, left)
                th = theta_max * np.tanh(s_ / s0) + 0.07 * np.sin(s_ / 3.1 + p1 * sign) * min(s_ / 6.0, 1.0) + 0.03 * np.sin(s_ / 1.3 + p2 * sign) * min(s_ / 6.0, 1.0)
                p = p + h * np.array([sign * np.cos(th), -np.sin(th)])
                s_ += h
                left -= h
            out.append(p.copy())
        return out
    # the chord is the arc, near enough: the first constraint pass closes the small difference
    mid = n // 2
    right = walk(1.0, L[mid:])
    left = walk(-1.0, L[:mid][::-1])
    xy = np.array(left[::-1] + [np.zeros(2)] + right)
    return np.c_[xy, R], R, L


class Strand:
    def __init__(self, n, seed, flick, shape):
        self.r = np.random.default_rng(seed + 1)
        self.n = n
        self.x, self.R, self.L = lay_out(n, seed, shape["R"], shape["gap"], shape["theta_max"], shape["s0"])
        if shape.get("keep"):  # only so much of the strand is needed: the rest of it never comes into frame
            n = self.n = shape["keep"]
            self.x, self.R, self.L = self.x[:n], self.R[:n], self.L[: n - 1]
        self.v = np.zeros((n, 3))
        self.w = np.zeros((n, 3))
        self.m = RHO * 4.0 / 3.0 * np.pi * self.R**3
        self.I = 0.4 * self.m * self.R**2
        t = self.tangent()
        off = t + self.r.normal(0, 0.07, (n, 3))
        off /= np.linalg.norm(off, axis=1, keepdims=True)
        ang = self.r.uniform(0, 2 * np.pi, n)
        self.q = qmul(axis_quat(off), np.stack([np.cos(ang / 2), 0 * ang, 0 * ang, np.sin(ang / 2)], 1))
        self.flick = flick
        self.hand = n - 1 if flick.get("kind") == "lay" else n // 2 + shape["hand_off"]
        self.p0 = None
        self.out = None
        a, b = [], []
        for d in range(1, n) if flick.get("kind") == "lay" else (1, 2, 3):  # a strand being laid can fold onto itself anywhere
            a.append(np.arange(n - d))
            b.append(np.arange(d, n))
        self.pa, self.pb = np.concatenate(a), np.concatenate(b)

    def lay_setup(self):
        """The strand is being laid down along its planned curve (self.plan), as a cable is from a ship: the part on the table lies still and the part in the air runs up to the hand, which comes down as less and less is left to lay. Every bead beyond the touch-down point starts on the line to the hand."""
        f = self.flick
        self.plan = self.x.copy()
        ds = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(self.plan[:, :2], axis=0), axis=1))]
        self.s_i = ds - ds[f["apex"]]
        self.s_end = self.s_i[-1]
        t0 = -f["pre"]
        td = self.s_touch(t0)
        hand = self.lay_hand(t0)
        p_td = np.r_[self.along(td), self.R.mean()]
        for i in range(self.n):
            if self.s_i[i] > td:
                u = (self.s_i[i] - td) / max(self.s_end - td, 1e-6)
                self.x[i] = p_td * (1 - u) + hand * u
                self.x[i, 2] = max(self.x[i, 2], self.R[i])
        self.lay_p0 = hand
        self.p0 = hand

    def s_touch(self, t):
        return self.flick["s0"] + self.flick["v"] * t

    def along(self, s):
        """A point of the planned curve at arc length s from the apex, carried on straight beyond its ends."""
        i = int(np.clip(np.searchsorted(self.s_i, s) - 1, 0, self.n - 2))
        d = self.plan[i + 1, :2] - self.plan[i, :2]
        return self.plan[i, :2] + d * (s - self.s_i[i]) / max(self.s_i[i + 1] - self.s_i[i], 1e-9)

    def lay_hand(self, t):
        f = self.flick
        td = self.s_touch(t)
        left = max(self.s_end - td, 0.0)
        xy = self.along(td + f["lead"] * left)
        # an unsteady hand: slow side-to-side drift, in the table's plane
        i = int(np.clip(np.searchsorted(self.s_i, td + f["lead"] * left) - 1, 0, self.n - 2))
        tan = self.plan[i + 1, :2] - self.plan[i, :2]
        tan = tan / max(np.linalg.norm(tan), 1e-9)
        sway = f["sway"] * np.sin(2 * np.pi * (t / f["sway_T"]) + 0.7) * min(left / 6.0, 1.0)
        return np.array([xy[0] - tan[1] * sway, xy[1] + tan[0] * sway, self.R[-1] + f["high"] * left])

    def tangent(self):
        t = np.gradient(self.x, axis=0)
        return t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)

    def hand_pos(self, t):
        f = self.flick
        if f.get("kind") == "lay":
            return self.lay_hand(t)
        up = smooth(t / f["rise"])
        dn = smooth((t - f["rise"] - f["hold"]) / f["fall"])
        slide = smooth(t / f["pull_rise"])
        side = np.array([-self.out[1], self.out[0], 0.0])
        return self.p0 + self.out * f["pull"] * slide + np.array([0.0, 0.0, f["lift"]]) * (up - dn) + side * f.get("side", 0.0) * (up - dn)

    def step(self, t, driven=True, settle=False):
        dt = DT
        x, w, m, I, R = self.x, self.w, self.m, self.I, self.R
        n = self.n
        vold = self.v + np.array([0, 0, -G]) * dt
        xp = x + vold * dt
        im = 1.0 / m
        if driven:
            im = im.copy()
            im[self.hand] = 0.0
            xp[self.hand] = self.hand_pos(t)
        pa, pb = self.pa, self.pb
        rr = R[pa] + R[pb]
        for _ in range(6):
            d = xp[1:] - xp[:-1]
            dist = np.linalg.norm(d, axis=1)
            over = np.maximum(dist - self.L, 0.0)
            ws = im[:-1] + im[1:]
            lam = (over / (ws + 6.0 / (CORD_K * dt * dt)))[:, None] * d / np.maximum(dist, 1e-9)[:, None]
            xp[:-1] += im[:-1, None] * lam
            xp[1:] -= im[1:, None] * lam
            dd = xp[pb] - xp[pa]
            ds = np.linalg.norm(dd, axis=1)
            hit = ds < rr
            if hit.any():
                pi, pj = pa[hit], pb[hit]
                nn = dd[hit] / np.maximum(ds[hit], 1e-9)[:, None]
                c = ((rr[hit] - ds[hit]) / np.maximum(im[pi] + im[pj], 1e-9))[:, None] * nn
                dx = np.zeros_like(xp)
                np.add.at(dx, pi, -im[pi, None] * c)
                np.add.at(dx, pj, im[pj, None] * c)
                xp += 0.7 * dx
            low = xp[:, 2] < R
            xp[low, 2] = R[low]
        vn = (xp - x) / dt
        # thread damping while stretched
        d = xp[1:] - xp[:-1]
        dist = np.linalg.norm(d, axis=1, keepdims=True)
        un = d / np.maximum(dist, 1e-9)
        rel = ((vn[1:] - vn[:-1]) * un).sum(1, keepdims=True) * (dist > self.L[:, None])
        imp = CORD_C * dt * rel * un
        vn[:-1] += im[:-1, None] * imp
        vn[1:] -= im[1:, None] * imp
        dv, dw = np.zeros_like(vn), np.zeros_like(w)
        # table
        on = (xp[:, 2] <= R + 1e-5) & (im > 0)
        if on.any():
            ii = np.nonzero(on)[0]
            jn = m[ii] * np.maximum(vn[ii, 2] - vold[ii, 2], 0.0)
            bounce = vold[ii, 2] < -4.0
            vn[ii[bounce], 2] = -E_TABLE * vold[ii[bounce], 2]
            jn = np.where(bounce, m[ii] * (vn[ii, 2] - vold[ii, 2]), jn)
            r = np.zeros((len(ii), 3))
            r[:, 2] = -R[ii]
            vc = vn[ii] + np.cross(w[ii], r)
            vc[:, 2] = 0.0
            sp = np.linalg.norm(vc, axis=1)
            js = sp / (1 / m[ii] + R[ii] ** 2 / I[ii])
            j = (np.minimum(js, getattr(self, "mu", MU_TABLE) * jn) / np.maximum(sp, 1e-6))[:, None] * vc
            dv[ii] -= j / m[ii, None]
            dw[ii] += np.cross(r, -j) / I[ii, None]
            dw[ii] -= w[ii] * min(1.0, getattr(self, "roll", 6.0) * dt)  # Zip sets a larger one: a bead held by the thread in its hole hardly rolls [stand-in]
        # bead on bead
        dd = xp[pb] - xp[pa]
        ds = np.linalg.norm(dd, axis=1)
        hit = ds < rr + 1e-4
        if hit.any():
            pi, pj = pa[hit], pb[hit]
            nn = dd[hit] / np.maximum(ds[hit], 1e-9)[:, None]
            ws = np.maximum(im[pi] + im[pj], 1e-9)
            vr0 = ((vold[pj] - vold[pi]) * nn).sum(1)
            vr = ((vn[pj] - vn[pi]) * nn).sum(1)
            jn = np.maximum(vr - vr0, 0.0) / ws
            ring = vr0 < -2.0
            jx = np.where(ring, (-E_BEAD * vr0 - vr) / ws, 0.0)
            np.add.at(vn, pi, -(im[pi] * jx)[:, None] * nn)
            np.add.at(vn, pj, (im[pj] * jx)[:, None] * nn)
            jn = jn + np.maximum(jx, 0.0)
            ri, rj = R[pi, None] * nn, -R[pj, None] * nn
            vc = (vn[pj] + np.cross(w[pj], rj)) - (vn[pi] + np.cross(w[pi], ri))
            vc = vc - (vc * nn).sum(1, keepdims=True) * nn
            sp = np.linalg.norm(vc, axis=1)
            js = sp / (im[pi] + im[pj] + R[pi] ** 2 / I[pi] + R[pj] ** 2 / I[pj])
            jt = (np.minimum(js, MU_BEAD * jn) / np.maximum(sp, 1e-6))[:, None] * vc
            np.add.at(dv, pi, im[pi, None] * jt)
            np.add.at(dv, pj, -im[pj, None] * jt)
            np.add.at(dw, pi, np.cross(ri, jt) / I[pi, None])
            np.add.at(dw, pj, np.cross(rj, -jt) / I[pj, None])
        vn = vn + dv
        w = w + dw
        # the hole
        t_ = self.tangent()
        a = qrot(self.q, np.array([0.0, 0.0, 1.0]))
        sgn = np.sign((a * t_).sum(1))
        sgn[sgn == 0] = 1
        err = np.cross(a, t_ * sgn[:, None])
        s = np.linalg.norm(err, axis=1)
        act = np.maximum(s - np.sin(np.radians(9.0)), 0.0) / np.maximum(s, 1e-9)
        w = w + 16000.0 * (act[:, None] * err) * dt
        wa = (w * a).sum(1, keepdims=True) * a
        w = wa * (1 - 0.4 * dt) + (w - wa) * (1 - 60.0 * (act[:, None] > 0) * dt)
        wn = np.linalg.norm(w, axis=1, keepdims=True)
        dq = np.concatenate([np.cos(0.5 * wn * dt), np.sinc(wn * dt / (2 * np.pi)) * 0.5 * dt * w], 1)
        self.q = qmul(dq, self.q)
        self.q /= np.linalg.norm(self.q, axis=1, keepdims=True)
        if settle:
            vn = vn * 0.99
            w = w * 0.99
        self.x, self.v, self.w = xp, vn, w


def run_lay(fps_real, frames, flick, shape, n=54, seed=63, pad=1):
    """Lay the strand down. Frames at t = (i - pad) / fps_real for i in 0 .. frames + 2 pad - 1, so that the first and last frame of the take have neighbours for the motion blur."""
    s = Strand(n, seed, flick, shape)
    s.lay_setup()
    s.v[:] = 0
    s.w[:] = 0
    plan = s.plan.copy()
    xs, qs = [], []
    t = -flick["pre"]
    every = 1.0 / fps_real
    next_t = -pad * every
    while len(xs) < frames + 2 * pad:
        if t >= next_t - 1e-9:
            xs.append(s.x.copy())
            qs.append(s.q.copy())
            next_t += every
        s.step(t)
        t += DT
    return {"x": np.array(xs), "q": np.array(qs), "R": s.R, "L": s.L, "seed": seed, "plan": plan, "s_i": s.s_i}


def run(fps_real, frames, flick, shape, n=54, seed=63, lead=0.012, settle=0.08):
    """Settle, then the jerk at t = 0. The first frame is at t = -lead."""
    s = Strand(n, seed, flick, shape)
    for _ in range(int(settle / DT)):
        s.step(-1.0, driven=False, settle=True)
    s.v[:] = 0
    s.w[:] = 0
    s.p0 = s.x[s.hand].copy()
    o = s.x[s.hand] - s.x[s.hand - 2]
    o[2] = 0.0
    s.out = o / np.linalg.norm(o)
    xs, qs = [], []
    every = 1.0 / fps_real / DT
    nextf = 0.0
    for step in range(int((frames / fps_real + lead) / DT) + 2):
        if step >= nextf:
            xs.append(s.x.copy())
            qs.append(s.q.copy())
            nextf += every
        s.step(-lead + step * DT)
    return {"x": np.array(xs), "q": np.array(qs), "R": s.R, "L": s.L, "seed": seed}


class Zip(Strand):
    """Two hands out of frame hold a length of the strand by its ends and lower it. The lowest bead meets its reflection first, and the touching runs outward both ways, each span between the touching point and its hand a slack catenary under some tension, so the beads land in single file on the planned curve instead of falling on each other. Nothing is keyed but the hands.
    flick: apex (the bead that touches first), half (beads kept each side), v (cm/s of the touching point, [left, right]), t_kiss, lead, high (the hand's place: lead x what is left to lay along the curve, high x it above the table), pre (s before t = 0), air (1/s of damping while it hangs, a hand steadying the strand before the take; off after t = 0), wob [cm, s]: a small unsteadiness of the hands."""

    def __init__(self, n, seed, flick, shape):
        super().__init__(n, seed, dict(flick, kind="lay"), {k: v for k, v in shape.items() if k != "keep"})
        a, h = flick["apex"], flick["half"]
        keep = np.arange(a - h, a + h + 1)
        self.x, self.R, self.m, self.I = self.x[keep], self.R[keep], self.m[keep], self.I[keep]
        self.v, self.w, self.q = self.v[keep], self.w[keep], self.q[keep]
        self.L = self.L[keep[:-1]]
        self.n = n = len(keep)
        self.ia = h
        self.hand = np.array([0, n - 1])
        ii, jj = np.triu_indices(n, 1)
        self.pa, self.pb = ii, jj
        self.plan = self.x.copy()
        ds = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(self.plan[:, :2], axis=0), axis=1))]
        self.s_i = ds - ds[h]
        self.flick = flick
        self.roll = flick.get("roll", 6.0)
        self.mu = flick.get("mu", MU_TABLE)
        # the first hang: a parabola between the hands, sagging to just above the table; the settling is done by the simulation
        t0 = -flick["pre"]
        H = self.hand_pos(t0)
        for side, idx in ((0, np.arange(0, h + 1)), (1, np.arange(h, n))):
            u = np.abs(self.s_i[idx]) / np.abs(self.s_i[self.hand[side]])
            mid = np.r_[self.plan[h, :2], self.R[h] + flick.get("z0", 3.0)]
            self.x[idx] = mid * (1 - u[:, None] ** 2) + H[side] * u[:, None] ** 2

    def front(self, t):
        v = np.array(self.flick["v"])
        return v * (t - self.flick["t_kiss"])

    def along(self, s):
        i = int(np.clip(np.searchsorted(self.s_i, s) - 1, 0, self.n - 2))
        d = self.plan[i + 1, :2] - self.plan[i, :2]
        return self.plan[i, :2] + d * (s - self.s_i[i]) / max(self.s_i[i + 1] - self.s_i[i], 1e-9)

    def hand_pos(self, t):
        f = self.flick
        fr = self.front(t)
        out = []
        for side, sg in ((0, -1.0), (1, 1.0)):
            end = abs(self.s_i[self.hand[side]])
            td = max(fr[side], 0.0)
            left = end - td
            # the free span hangs in a vertical plane, so the hand stays over the tangent of the curve at the touching point
            s = sg * td
            tan = self.along(s + sg * 0.5) - self.along(s - sg * 0.5)
            xy = self.along(s) + tan / max(np.linalg.norm(tan), 1e-9) * f["lead"] * left
            amp, per = f.get("wob", (0.0, 1.0))
            # before the first touch the whole hang comes down at drop x v, from `z0` above the table
            lift = min(max(-fr[side], 0.0) * f.get("drop", 1.0), f.get("z0", 3.0))
            z = self.R[self.hand[side]] + f["high"] * left + lift + amp * np.sin(2 * np.pi * t / per + 1.3 * side)
            out.append(np.r_[xy, z])
        return np.array(out)

    def step(self, t, driven=True, settle=False):
        super().step(t, driven=driven, settle=settle)
        if t < 0.0:
            k = 1.0 - self.flick.get("air", 0.0) * DT
            self.v *= k
            self.w *= k


def run_zip(fps_real, frames, flick, shape, n=54, seed=63, pad=1):
    """Frames at t = (i - pad) / fps_real, so that the first and the last frame of the take have neighbours for the motion blur."""
    s = Zip(n, seed, flick, shape)
    xs, qs = [], []
    t = -flick["pre"]
    every = 1.0 / fps_real
    next_t = -pad * every
    while len(xs) < frames + 2 * pad:
        if t >= next_t - 1e-9:
            xs.append(s.x.copy())
            qs.append(s.q.copy())
            next_t += every
        s.step(t)
        t += DT
    return {"x": np.array(xs), "q": np.array(qs), "R": s.R, "L": s.L, "seed": seed, "plan": s.plan, "s_i": s.s_i, "ia": s.ia}


def run_settle(fps, frames, flick, shape, n=54, seed=63, pad=1):
    """The same strand and the same two hands as Zip, lowered so slowly that it is in equilibrium at every moment: the quasi-static limit, with no integrator, so nothing swings, bounces or slides (one direction, slow, even, no rebound, no tremble).
    What lies on the table lies still on the planned curve. Each free span is a catenary (parameter `a`, cm: tension over weight per length) in the vertical plane of the curve's tangent at the touching point, leaving the table level. A bead at arc distance d past the touching point is at X = a asinh(d/a) along the tangent, Z = a (sqrt(1 + (d/a)^2) - 1) up. The touching point runs at v, so no bead moves faster than v, each only ever goes down and out, and it arrives with no speed left.
    flick: apex, half (as Zip), v (cm/s), a (cm), t_kiss (s), vz (cm/s of the whole strand coming down before the kiss), b (s: how softly the one hands over to the other).
    ESTIMATES: a, v, vz, by eye. STAND-IN: bead turn is only the slope of the thread, and no rolling; the strand's contact with the table has no friction to reckon, nothing on it moves."""
    from scipy.interpolate import CubicSpline

    st = Zip(n, seed, dict(flick, v=[0.0, 0.0], lead=0.5, high=0.5, pre=0.0), shape)
    plan, si, R, q0, h = st.plan, st.s_i, st.R, st.q.copy(), st.ia
    curve = CubicSpline(si, plan[:, :2])
    a, v, tk, vz, b = flick["a"], flick["v"], flick["t_kiss"], flick["vz"], flick["b"]
    xs, qs = [], []
    Z = np.array([0.0, 0.0, 1.0])
    for i in range(frames + 2 * pad):
        t = (i - pad) / fps
        u = np.clip((t - tk) / b, -40.0, 40.0)
        fr = v * b * np.logaddexp(0.0, u)  # 0 before the kiss, v (t - tk) after it
        lift = vz * b * np.logaddexp(0.0, -u)  # the other way round
        x = plan.copy()
        q = q0.copy()
        for k in range(st.n):
            d = abs(si[k]) - fr
            if d > 0.0:
                sg = np.sign(si[k])
                T = curve(sg * fr, 1)
                T = np.r_[sg * T / np.linalg.norm(T), 0.0]  # outward along the curve
                x[k, :2] = curve(sg * fr) + T[:2] * a * np.arcsinh(d / a)
                x[k, 2] = plan[k, 2] + a * (np.sqrt(1.0 + (d / a) ** 2) - 1.0)
                ax = np.cross(T, Z)
                ph = np.arctan(d / a)
                q[k] = qmul(np.r_[np.cos(ph / 2), ax * np.sin(ph / 2)], q0[k])
        x[:, 2] += lift
        xs.append(x)
        qs.append(q)
    return {"x": np.array(xs), "q": np.array(qs), "R": R, "L": st.L, "seed": seed, "plan": plan, "s_i": si, "ia": h}
