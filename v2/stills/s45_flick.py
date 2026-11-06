"""Shot 45, the breeze: one light, steady air along the barbs, in one direction, and they lie over with it. Used by s45_kongque.py flick; nothing here renders.
A whip of the shaft with a gust and a recoil was made first and turned down (kept at out/v2/s45_kongque_flick_v1_move):
The motion should be one way, gentle, along the fur. So: the shaft does not move at all; the push of the air only ever grows, so a barb has no reason to come back; and it grows in slow swells that run outward from the root, which is what runs along the fur.

Every barb is solved on its own as a planar cantilever of links (angles from its rest shape, cm g s), implicit in bending, explicit in air:
- clamped to the shaft, which stands still;
- bending stiffness tapers to the tip; mass per length likewise;
- quadratic drag on the component of the air's speed across the barb, wider inside the eye where the barbules close the gaps. A barb lying along the air feels nothing: that is the combing;
- air: see load(). Advected noise so that no two barbs are loaded alike. This is a model, air flow is not solved;
- neighbours inside the eye are held together (barbules overlap); past the green they are nearly free.
The mesh hangs from the barbs: each vertex keeps its offset from its parent sample, turned with the barb. Colour stays on the barbule: it was decided at rest. Motion blur is real sub-exposures of the moving mesh, averaged.

ESTIMATED, nothing measured on a specimen: EI 25 dyn cm2 at the root of a 5 cm barb (a 0.12 mm keratin rod at 2.5 GPa), mass 2.5e-4 g/cm, Cd 1.2, drag width, U0, the air's direction and timing, the lift and twist of each barb in the air.
Not simulated: barb against barb contact (they may pass through each other), the bending of the shaft, air flow.
"""

import numpy as np
import scipy.ndimage as ndi

ARG = {"U0": 40.0, "dir": 90.0, "conv": 10.0, "lead": 0.8, "swell": 0.75, "T": 1.0, "wob": 0.03, "tb": 0.05, "scat": 0.1, "rho": 1.2e-3, "Cd": 1.2, "EI": 25.0, "EIp": 3.0, "kf": 0.02, "mu": 2.5e-4, "beta": 0.0035, "d_eye": 0.10, "d_fringe": 0.05, "dt": 1e-3, "spin": 1.2, "N": 14, "lift": 0.1, "barb_twist": 0.6, "zp": -30.0, "seed": 45}


def smooth(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def load(tau, a):
    """The air's push at time tau of its front, in units of U0 squared. Never falls: a soft start over `lead` seconds, then a steady climb, so a barb keeps leaning at an even speed; on it a swell of period T that speeds and slows the climb but cannot reverse it (swell < 1)."""
    s = np.maximum(tau + a["lead"], 0.0)
    ramp = np.where(s < a["lead"], s * s / (2 * a["lead"]), s - a["lead"] / 2)
    w = 2 * np.pi / a["T"]
    return ramp + a["swell"] * (1 - np.cos(w * s)) / w


def shaft(ts, a):
    """The shaft stands still. Kept as the solver's interface: sideways, its turn, its twist."""
    z = np.zeros_like(np.asarray(ts, np.float64))
    return z, z, z


class Air:
    def __init__(self, a):
        r = np.random.default_rng(a["seed"] + 5)
        self.cell = 0.125
        self.tiles = []
        for sig, wt in ((2.2, 1.0), (0.9, 0.2)):  # large only: a fine, fast wobble is what looks like shaking
            t = ndi.gaussian_filter(r.normal(0, 1, (256, 256)).astype(np.float32), sig / self.cell, mode="wrap")
            self.tiles.append((t / t.std(), wt))
        self.size = 256 * self.cell
        self.a = a

    def noise(self, x, z, t):
        out = 0.0
        for (tile, wt), v in zip(self.tiles, (1.0, 0.8)):
            u = (x % self.size) / self.cell
            w = ((z - v * self.a["conv"] * t) % self.size) / self.cell
            i, j = u.astype(np.int32), w.astype(np.int32)
            fu, fw = u - i, w - j
            i1, j1 = (i + 1) % 256, (j + 1) % 256
            i, j = i % 256, j % 256
            out = out + wt * ((tile[j, i] * (1 - fu) + tile[j, i1] * fu) * (1 - fw) + (tile[j1, i] * (1 - fu) + tile[j1, i1] * fu) * fw)
        return out


class Barbs:
    """rec: the barbs in order, each {"P": (m, 3) rest samples x, y, z, "T": (m, 3) or None, "rg": (m,), "side", "i"}."""

    def __init__(self, rec, a=None):
        self.a = dict(ARG, **(a or {}))
        a, N = self.a, self.a["N"]
        nb = len(rec)
        M = max(r["P"].shape[0] for r in rec)
        self.nb, self.N, self.M = nb, N, M
        self.m = np.array([r["P"].shape[0] for r in rec])
        self.P0 = np.zeros((nb, M, 3), np.float32)
        self.T0 = np.zeros((nb, M, 3), np.float32)
        self.rg = np.zeros((nb, M), np.float32)
        self.i0, self.w0 = np.zeros((nb, M), np.int32), np.zeros((nb, M), np.float32)
        self.phi0, self.ds = np.zeros((nb, N)), np.zeros((nb, 1))
        self.width = np.zeros((nb, N))
        self.side = np.array([r["side"] for r in rec])
        for b, r in enumerate(rec):
            m = r["P"].shape[0]
            self.P0[b, :m] = r["P"]
            self.P0[b, m:] = r["P"][-1]
            if r.get("T") is not None:
                self.T0[b, :m] = r["T"]
            self.rg[b, :m] = r["rg"]
            arc = np.r_[0.0, np.cumsum(np.hypot(*np.diff(r["P"][:, [0, 2]], axis=0).T))]
            ds = arc[-1] / N
            self.ds[b] = ds
            at = ds * np.arange(N + 1)
            xn, zn = np.interp(at, arc, r["P"][:, 0]), np.interp(at, arc, r["P"][:, 2])
            self.phi0[b] = np.arctan2(np.diff(xn), np.diff(zn))
            u = np.clip(arc / ds - 0.5, 0, N - 1.001)
            self.i0[b, :m], self.w0[b, :m] = u.astype(np.int32), u - u.astype(np.int32)
            rgn = np.interp(0.5 * (at[1:] + at[:-1]), arc, r["rg"])
            self.width[b] = a["d_eye"] + (a["d_fringe"] - a["d_eye"]) * smooth((rgn - 0.92) / 0.3)
        self.seg = np.diff(self.P0[..., [0, 2]], axis=1)  # (nb, M-1, 2)
        self.x0, self.z0 = self.P0[:, 0, 0].astype(np.float64), self.P0[:, 0, 2].astype(np.float64)
        r = np.random.default_rng(a["seed"])
        self.lsign = r.normal(0, 1, nb).astype(np.float32)
        self.tw = (r.normal(0, a["barb_twist"], nb)).astype(np.float32)
        self.fringe = np.clip((self.rg - 0.9) / 0.5, 0, 1)
        self.zc = float(self.P0[..., 2].mean())

    def solve(self, times):
        """th[len(times)] (nb, N) float32, plus the shaft at those times."""
        a, nb, N = self.a, self.nb, self.N
        dt = a["dt"]
        arc = self.ds * N
        r = np.random.default_rng(a["seed"] + 1)
        s = (np.arange(N) + 0.5) / N
        L = arc[:, 0]
        # stiffness and mass, with barb to barb scatter that is smooth across the rachis, so clumps go together
        scat = ndi.gaussian_filter1d(r.normal(0, 1, nb), 4.0)
        scat = scat / scat.std()
        EI0 = a["EI"] * (L / 5.0) ** a["EIp"] * np.exp(a["scat"] * scat)  # a long barb is a thick barb
        EI = EI0[:, None] * (1 - 0.68 * s[None, :]) ** 3
        mu = a["mu"] * (1 - 0.55 * s[None, :]) * np.ones((nb, N))
        dk = ndi.gaussian_filter1d(r.normal(0, 1, nb), 4.0)
        drag_k = np.exp(a["scat"] * dk / dk.std())[:, None]  # neighbours alike, so that they go as one sheet of fur and do not cross
        E = EI / self.ds  # joints: 0 is the clamp, i between links i-1 and i
        m = mu * self.ds
        # M_ik = ds^2 sum_{j >= max(i, k)} m_j
        tail = np.cumsum(m[:, ::-1], axis=1)[:, ::-1]
        ii = np.minimum.outer(np.arange(N), np.arange(N))
        jj = np.maximum.outer(np.arange(N), np.arange(N))
        MM = tail[:, jj] * (self.ds[:, None] ** 2)
        K = np.zeros((nb, N, N))
        idx = np.arange(N)
        K[:, idx, idx] = E + np.c_[E[:, 1:], np.zeros(nb)]
        K[:, idx[1:], idx[:-1]] = -E[:, 1:]
        K[:, idx[:-1], idx[1:]] = -E[:, 1:]
        Ainv = np.linalg.inv(MM + dt * a["beta"] * K + dt * dt * K)
        del ii
        # neighbours: along the rachis on each side; the two sides meet at the top of the fan
        prev, nxt = np.arange(nb) - 1, np.arange(nb) + 1
        first = np.r_[True, self.side[1:] != self.side[:-1]]
        last = np.r_[self.side[1:] != self.side[:-1], True]
        starts = np.where(first)[0]
        prev[starts] = starts[::-1] if len(starts) == 2 else starts
        nxt[last] = np.where(last)[0]
        ringn = np.zeros((nb, N))
        for b in range(nb):
            ringn[b] = np.interp((np.arange(N) + 0.5) * self.ds[b, 0], np.arange(self.m[b]) * (arc[b, 0] / max(self.m[b] - 1, 1)), self.rg[b, : self.m[b]])
        kappa = 0.3 * (1 - smooth((ringn - 0.8) / 0.28)) + a["kf"]

        ts = np.arange(-a["spin"], float(times[-1]) + 2 * dt, dt)
        Xs, As, Ts = shaft(ts, a)
        Vs = np.gradient(Xs, dt)
        Acc = np.gradient(Vs, dt)
        air = Air(a)
        th, om = np.zeros((nb, N)), np.zeros((nb, N))
        out = np.zeros((len(times), nb, N), np.float32)
        nxt_t = 0
        for it, t in enumerate(ts):
            phi = self.phi0 + th
            st, ct = np.sin(phi), np.cos(phi)
            rootx = self.x0[:, None] + As[it] * (self.z0[:, None] - a["zp"])
            px = rootx + np.cumsum(st * self.ds, axis=1)
            pz = self.z0[:, None] + np.cumsum(ct * self.ds, axis=1)
            vnx, vnz = ct * self.ds * om, -st * self.ds * om
            vx = Vs[it] + np.cumsum(vnx, axis=1)
            vz = np.cumsum(vnz, axis=1)
            q = air.noise(px, pz, t)
            G = np.sqrt(load(t - (pz - self.zc) / a["conv"] + a["wob"] * q, a))  # the front comes up the feather from the root
            Ux = a["U0"] * G * np.sin(np.radians(a["dir"])) * (1 + a["tb"] * q)
            Uz = a["U0"] * G * np.cos(np.radians(a["dir"])) * (1 + a["tb"] * q)
            rx, rz = vx - Ux, vz - Uz
            vn = rx * ct - rz * st
            Fn = -0.5 * a["rho"] * a["Cd"] * self.width * drag_k * self.ds * np.abs(vn) * vn
            Fx = Fn * ct - m * Acc[it]
            Fz = -Fn * st
            Cx = np.cumsum(Fx[:, ::-1], axis=1)[:, ::-1]
            Cz = np.cumsum(Fz[:, ::-1], axis=1)[:, ::-1]
            Q = self.ds * (ct * Cx - st * Cz)
            d = th[:, 1:] - th[:, :-1]
            tq = E[:, 1:] * d
            Kth = np.zeros_like(th)
            Kth[:, :-1] -= tq
            Kth[:, 1:] += tq
            Kth[:, 0] += E[:, 0] * (th[:, 0] - As[it] * 0.0)  # the shaft's turn is tiny: the clamp stays at rest
            rhs = (MM @ om[..., None])[..., 0] + dt * (Q - Kth)
            om = (Ainv @ rhs[..., None])[..., 0]
            th = th + dt * om
            th = th + kappa * (0.5 * (th[prev] + th[nxt]) - th)
            om = om + kappa * (0.5 * (om[prev] + om[nxt]) - om)
            if not np.isfinite(th).all():
                raise SystemExit(f"flick: the solve blew up at t = {t:.3f}")
            while nxt_t < len(times) and t + dt / 2 >= times[nxt_t]:
                out[nxt_t] = th
                nxt_t += 1
        X, A, T = shaft(np.asarray(times), a)
        return out, X.astype(np.float32), A.astype(np.float32), T.astype(np.float32)

    def pose(self, th, X, A):
        """Rest and new position of every sample, and the turn of each sample: (nb, M) arrays."""
        b = np.arange(self.nb)[:, None]
        dth = th[b, self.i0] * (1 - self.w0) + th[b, self.i0 + 1] * self.w0
        c, s = np.cos(dth[:, :-1]), np.sin(dth[:, :-1])
        sx, sz = self.seg[..., 0] * c + self.seg[..., 1] * s, self.seg[..., 1] * c - self.seg[..., 0] * s
        rootx = (self.x0 + A * (self.z0 - self.a["zp"]))[:, None]
        Px = np.concatenate([rootx, rootx + np.cumsum(sx, axis=1)], axis=1).astype(np.float32)
        Pz = np.concatenate([self.z0[:, None], self.z0[:, None] + np.cumsum(sz, axis=1)], axis=1).astype(np.float32)
        away = np.hypot(Px - rootx - (self.P0[..., 0] - self.x0[:, None]), Pz - self.P0[..., 2])
        Py = self.P0[..., 1] - self.a["lift"] * self.lsign[:, None] * away * (0.25 + 0.75 * self.fringe)
        return Px, Py, Pz, dth.astype(np.float32)

    def skin(self, V, bid, k, th, X, A, tw):
        """The vertices of a mesh for one time. bid -1 is the shaft: it moves whole."""
        Px, Py, Pz, dth = self.pose(th, X, A)
        out = V.copy()
        on = bid >= 0
        b, kk = bid[on], k[on]
        off = V[on] - self.P0[b, kk]
        # each barb rolls a little about itself as it bends, and the sheen goes with it
        T = self.T0[b, kk]
        rl = (self.tw[b] * dth[b, kk])[:, None]
        cr, sr = np.cos(rl), np.sin(rl)
        off = off * cr + np.cross(T, off) * sr + T * np.sum(T * off, axis=1, keepdims=True) * (1 - cr)
        c, s = np.cos(dth[b, kk]), np.sin(dth[b, kk])
        ox, oz = off[:, 0] * c + off[:, 2] * s, off[:, 2] * c - off[:, 0] * s
        out[on, 0] = Px[b, kk] + ox
        out[on, 1] = Py[b, kk] + off[:, 1]
        out[on, 2] = Pz[b, kk] + oz
        sh = ~on
        out[sh, 0] = V[sh, 0] + A * (V[sh, 2] - self.a["zp"])
        # the whole feather twists about the shaft
        ct, st = np.cos(tw), np.sin(tw)
        x = out[:, 0] - X
        y = out[:, 1].copy()
        out[:, 0] = X + x * ct - y * st
        out[:, 1] = x * st + y * ct
        return out
