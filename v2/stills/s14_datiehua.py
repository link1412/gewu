"""Shot 14: 打铁花, from inside the sparks. No people, no ground: only flying iron and the night. 24 frames.

    python3 -I v2/stills/s14_datiehua.py look [preview|mid|final] [frame]     one frame, to out/v2/s14_datiehua/look_<q>.png
    python3 -I v2/stills/s14_datiehua.py take [preview|mid|final] [i0 i1]     frames i0..i1-1 to out/v2/s14_datiehua_take_<q>/ (run a few ranges side by side)

Direction: close to the sparks, no figures, more expressive. Three depths: a few big, soft ones past the lens; the plane of focus with white-hot cores, bursts and forks, cooling
white -> yellow -> orange -> dark red; far ones so fine they are a mist with a little lit smoke. The upper edge of the main sheaf makes the film's arc, and is not a regular dome.

No Blender: a spark is far smaller than a pixel, so it is a line of light in the sensor. A 35 mm f/1.4 lens at 4.8 m gives every sample a circle of confusion from its true depth, and light falls as 1/d^2, so the three depths are one
scene seen through one lens, and not three layers. What photographs of sparks showed, and how it is done:
- Hierarchy, not a cloud: a blow throws clots, a clot tears into droplets with nearly the same path, so streaks come in tufts. Clot mass is heavy-tailed.
- Air drag decides the path: terminal speeds of 1-8 m/s. Droplets go up fast, stop, and rain down; the path is asymmetric and no two blows peak alike, so the arc is not a parabola drawn by hand.
- Size sets brightness, range and how long a droplet stays hot. Line width is brightness against the sensor's clip plus lens flare.
- Temperature falls in flight. The hue is Planck's law through a tungsten-ish balance. Brightness goes as a power of T, gentler than Planck's own (which would lose everything below about 1500 K to the black): a substitute, so that the dull red of a
  cooling droplet stays visible, as it does in a real overexposed frame. Clipping does the rest: hot and bright goes yellow and white by itself.
- Carbon bursts: droplets swell, flare, burst into forks; some forks burst again.
- The air is one field: coherent gusts bend neighbouring sparks together.
- Continuity: one fixed set of particles and one moving shutter of 0.10 s, two and a half frame intervals, soft at both ends: long-exposure trails that cannot flicker. A real camera at 25 fps cannot have a shutter longer than 0.04 s: this is a frame merge, as of a
  high-speed shot stacked in post. Smoke is shaped noise lit by a blur of the sparks, not a simulation.

Estimates, not measurements: all speeds, lives, temperatures, counts, gusts, the lens.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from darkroom import develop, save_png
from kit import OUT, fbm, sstep

G = 9.8
N_FRAMES = 24
FPS = 25.0
SHUTTER = 0.10  # s
F_MM, F_NUMBER = 35.0, 1.4
F_PX = 2560.0 * F_MM / 36.0  # focal length in pixels at 2560
FOCUS = 4.8  # m
APERTURE = F_MM / F_NUMBER / 1000.0  # m
DREF = FOCUS  # brightness is 1/d^2 relative to this distance
LOOK = {"contrast": 1.3, "saturation": 1.0, "black": 0.0012, "grain": 1.3, "sharpen": 0.26, "halation": 0.09, "glare": 0.008, "vignette": 0.14, "ca": 0.0003}
K = 27.0  # exposure, at preview size
WB = np.array([0.92, 1.0, 1.1])
COC = np.array([0.0, 3.0, 7.0, 16.0, 36.0, 80.0, 170.0])  # diameters, px at 2560
DOWN = [1, 1, 2, 4, 4, 8, 8]  # each level is stamped at this fraction of the size and blurred there


def _chroma_lut():
    lam = np.array([610e-9, 550e-9, 465e-9])
    Ts = np.linspace(700.0, 3000.0, 256)
    b = 1.0 / (lam**5 * (np.exp(1.4388e-2 / (lam * Ts[:, None])) - 1.0)) * WB
    return (b / b.max(1, keepdims=True)).astype(np.float32)


LUT = _chroma_lut()


def light(T):
    """Linear RGB of a droplet at temperature T: Planck's hue; a power law for the brightness (see the docstring)."""
    i = np.clip((T - 700.0) / 2300.0 * 255.0, 0, 255).astype(np.int32)
    return LUT[i] * ((np.maximum(T, 700.0) / 2300.0) ** 5.2)[:, None]


class Gusts:
    def __init__(self, seed):
        r = np.random.default_rng(seed)
        n = 9
        lam = r.uniform(0.9, 7.0, n)
        th = r.uniform(0, 2 * np.pi, n)
        self.kx, self.kz = 2 * np.pi / lam * np.cos(th), 2 * np.pi / lam * np.sin(th)
        self.w = r.uniform(0.7, 3.5, n)
        self.p = r.uniform(0, 2 * np.pi, n)
        self.ax = r.normal(0, 1, n) * lam / 7.0
        self.az = r.normal(0, 1, n) * lam / 7.0

    def __call__(self, x, z, t):
        dx = np.zeros_like(x)
        dz = np.zeros_like(x)
        for i in range(len(self.w)):
            s = np.sin(self.kx[i] * x + self.kz[i] * z + self.w[i] * t + self.p[i])
            dx += self.ax[i] * s
            dz += self.az[i] * s
        return dx, dz


# place of the blows, how many, clots per blow, direction of the throw in x-z from the vertical (rad), its spread, depth spread (rad), speed range, droplets per unit mass, gain
SOURCES = [
    dict(pos=(-4.6, 4.9, -3.5), blows=24, clots=24, ang=0.76, spread=0.085, dsp=0.27, v=(9.4, 14.5), per=15, gain=1.0),  # the main sheaf: over the frame from the lower left, its crown is the arc
    dict(pos=(-3.4, 5.6, -3.7), blows=11, clots=20, ang=0.60, spread=0.14, dsp=0.3, v=(7.6, 12.2), per=13, gain=0.8),  # lower throws: they fill under the crown and break its line
    dict(pos=(5.4, 7.6, -4.0), blows=14, clots=20, ang=-0.62, spread=0.16, dsp=0.3, v=(10.0, 15.0), per=12, gain=1.1),  # further off, from the right, lower
    dict(pos=(-14.0, 22.0, -13.0), blows=26, clots=26, ang=0.5, spread=0.4, dsp=0.5, v=(18.0, 26.0), per=22, gain=9.0),  # far away: a mist
    dict(pos=(6.0, 26.0, -15.0), blows=26, clots=26, ang=-0.35, spread=0.45, dsp=0.5, v=(18.0, 26.0), per=22, gain=11.0),
    dict(pos=(14.0, 17.0, -10.0), blows=18, clots=22, ang=-0.55, spread=0.4, dsp=0.5, v=(16.0, 24.0), per=20, gain=6.0),
]


class Sparks:
    """Every generation in one set of arrays: droplets of a clot; forks; forks of forks; the few past the lens."""

    def __init__(self, seed=14):
        r = np.random.default_rng(seed)
        self.gusts = Gusts(seed + 1)
        X = []
        T_END = N_FRAMES / FPS
        for src in SOURCES:
            bt = np.sort(r.uniform(-2.6, T_END + 0.02, src["blows"]))
            for tb in bt:
                power = r.lognormal(0.0, 0.3)
                lean = r.normal(0.0, 0.05)
                vpow = r.uniform(0.9, 1.05)  # no two blows reach the same height: this breaks the arc
                n_clots = int(src["clots"] * power) + 5
                mass = r.pareto(1.25, n_clots) + 0.3
                off = src["ang"] + lean + r.normal(0, src["spread"], n_clots)
                daz = r.normal(0, src["dsp"], n_clots)
                # speeds pile up near the top, or the crown has no edge
                speed = (src["v"][0] + (src["v"][1] - src["v"][0]) * (1 - r.random(n_clots) ** 2.2)) * vpow
                tc = tb + r.exponential(0.03, n_clots)
                for c in range(n_clots):
                    k = int(np.clip(mass[c] * src["per"], 3, 360))
                    v = speed[c] * (1 + r.normal(0, 0.075, k))
                    a = off[c] + r.normal(0, 0.045 + 0.03 / np.sqrt(mass[c]), k)
                    da = daz[c] + r.normal(0, 0.06, k)
                    d = r.lognormal(np.log(0.56 + 0.2 * np.log1p(mass[c])), 0.74, k)
                    hot = 1.0 + 16.0 * float(r.random() < 0.10)  # a clot torn from the hottest of the pour
                    X.append(np.c_[np.full(k, src["pos"][0]) + r.normal(0, 0.14, k), np.full(k, src["pos"][1]) + r.normal(0, 0.14, k), np.full(k, src["pos"][2]) + r.normal(0, 0.14, k), v * np.sin(a) * np.cos(da), v * np.sin(da), v * np.cos(a) * np.cos(da), tc[c] + r.exponential(0.015, k), d, np.full(k, src["gain"]) * hot, np.full(k, hot)])
        P = np.vstack(X)
        n = len(P)
        x0, y0, z0, vx, vy, vz, t0, d, sg, hotf = P.T
        tau = np.clip(0.52 * d**0.7, 0.1, 0.82)
        life = np.clip(1.25 * d**0.85 * r.lognormal(0, 0.26, n), 0.2, 3.4)
        T0 = (r.uniform(1560, 2200, n) + 800.0 * (hotf > 1.5)) * np.clip(d, 0.7, 1.15) ** 0.2 * (1.0 + 0.08 * np.clip(np.log(gain_pre := d**2 + 1e-3) , -1, 1.5))
        gain = d**2 * r.lognormal(0, 0.7, n) * sg
        g0 = dict(x0=x0, y0=y0, z0=z0, vx=vx, vy=vy, vz=vz, t0=t0, tau=tau, life=life, life0=life.copy(), T0=T0, gain=gain, burst=np.full(n, -1.0), ign=r.lognormal(np.log(0.26), 0.6, n))

        def state(g, i, a):
            tau = g["tau"][i]
            e = 1.0 - np.exp(-a / tau)
            dec = np.exp(-a / tau)
            return (g["x0"][i] + g["vx"][i] * tau * e, g["y0"][i] + g["vy"][i] * tau * e, g["z0"][i] + (g["vz"][i] + G * tau) * tau * e - G * tau * a, g["vx"][i] * dec, g["vy"][i] * dec, (g["vz"][i] + G * tau) * dec - G * tau)

        def children(g, i, a, k_lo, k_hi, sp_lo, sp_hi, tau_lo, tau_hi, life_lo, life_hi, gain):
            k = r.integers(k_lo, k_hi, i.size)
            par = np.repeat(np.arange(i.size), k)
            m = par.size
            x, y, z, ux, uy, uz = state(g, i[par], a[par])
            dirn = r.normal(0, 1, (m, 3))
            dirn /= np.linalg.norm(dirn, axis=1, keepdims=True)
            s = np.clip(r.lognormal(np.log(np.sqrt(sp_lo * sp_hi)), 0.5, m), sp_lo * 0.4, sp_hi * 1.6)
            lf = r.lognormal(np.log(np.sqrt(life_lo * life_hi)), 0.4, m)
            return dict(x0=x, y0=y, z0=z, vx=ux + dirn[:, 0] * s, vy=uy + dirn[:, 1] * s, vz=uz + dirn[:, 2] * s, t0=g["t0"][i[par]] + a[par], tau=r.uniform(tau_lo, tau_hi, m), life=lf, life0=lf.copy(), T0=g["T0"][i[par]] + r.uniform(-20, 110, m), gain=np.minimum(g["gain"][i[par]], 18.0) ** 0.5 * gain * r.lognormal(0, 0.55, m), burst=np.full(m, -1.0), ign=np.full(m, 0.006))

        bur = r.random(n) < 0.4
        at = life * r.uniform(0.35, 1.0, n)
        ib = np.nonzero(bur)[0]
        g0["burst"][ib] = at[ib]
        g0["life"] = np.where(bur, at, life)
        g1 = children(g0, ib, at[ib], 5, 28, 3.0, 10.0, 0.07, 0.26, 0.1, 0.42, 0.9)
        m1 = len(g1["t0"])
        bur1 = r.random(m1) < 0.12
        at1 = g1["life"] * r.uniform(0.55, 1.0, m1)
        ib1 = np.nonzero(bur1)[0]
        g1["burst"][ib1] = at1[ib1]
        g1["life"] = np.where(bur1, at1, g1["life"])
        g2 = children(g1, ib1, at1[ib1], 3, 8, 0.9, 3.2, 0.03, 0.1, 0.04, 0.14, 0.45)

        # the few past the lens: 0.45-1.3 m from it, slow, big and soft. About four are in the picture at any moment
        nn = 34
        yn = r.uniform(0.45, 1.3, nn)
        tn = np.sort(r.uniform(-0.7, T_END, nn))
        vn = r.uniform(0.7, 1.7, nn) * yn / 0.8  # slow: near ones must not whip across the frame in one shutter
        side = r.uniform(-1, 1, nn)
        headx = r.normal(0.55, 0.4, nn)
        hx = 0.70 * yn  # half the frame width at this distance
        x_st = side * hx * 1.1 - headx * vn * 0.25
        life_n = r.uniform(0.5, 1.1, nn)
        g9 = dict(x0=x_st, y0=yn, z0=0.5 * yn * r.uniform(-1.0, 1.0, nn), vx=headx * vn, vy=r.normal(0, 0.2, nn), vz=-0.05 * vn, t0=tn, tau=np.full(nn, 0.5), life=life_n, life0=life_n * 1.25, T0=r.uniform(1800, 2300, nn), gain=r.uniform(4.0, 12.0, nn), burst=np.full(nn, -1.0), ign=np.full(nn, 0.03))
        for k in g0:
            setattr(self, k, np.r_[g0[k], g1[k], g2[k], g9[k]])
        N = len(self.t0)
        self.ph1, self.ph2 = r.uniform(0, 2 * np.pi, N), r.uniform(0, 2 * np.pi, N)
        self.f1, self.f2 = r.uniform(30, 90, N), r.uniform(150, 420, N)  # rad/s: a burning droplet spins and sputters, so a 0.1 s streak is beaded, not a blade (rates are estimates)
        self.wob = r.lognormal(np.log(0.012), 0.6, N)
        self.th = r.uniform(0, 2 * np.pi, N)
        self.flick = r.uniform(0.45, 1.1, N) * r.choice([0.6, 1.0, 1.0, 1.5], N)
        self.flare_at = r.uniform(0.2, 0.95, N)
        self.flare = (r.random(N) < 0.18) * r.uniform(0.8, 4.0, N)
        self.jit = r.random(N)
        print(f"[sparks] {n} droplets, {m1} forks, {len(g2['t0'])} forks of forks, {nn} past the lens", flush=True)


def camera_at(t):
    """A hand-held camera, a slow drift, so that the near sparks shift against the far ones. Metres."""
    return 0.012 * np.sin(1.3 * t + 0.4) + 0.01 * t, 0.009 * np.sin(1.9 * t + 1.1)


def stamp(acc, ix, iy, rgb_e, bilinear=True):
    h, w = acc.shape[:2]
    keep = (ix >= 0) & (ix < w - 1) & (iy >= 0) & (iy < h - 1)
    ix, iy = ix[keep], iy[keep]
    rgb_e = rgb_e[keep]
    if ix.size == 0:
        return
    i0, j0 = ix.astype(np.int64), iy.astype(np.int64)
    if bilinear:
        fx, fy = ix - i0, iy - j0
        for dj, wy in ((0, 1.0 - fy), (1, fy)):
            for di, wx in ((0, 1.0 - fx), (1, fx)):
                idx = (j0 + dj) * w + (i0 + di)
                wt = wy * wx
                for c in range(3):
                    acc[..., c] += np.bincount(idx, weights=rgb_e[:, c] * wt, minlength=h * w).reshape(h, w).astype(np.float32)
    else:
        idx = j0 * w + i0
        for c in range(3):
            acc[..., c] += np.bincount(idx, weights=rgb_e[:, c], minlength=h * w).reshape(h, w).astype(np.float32)


def disc_kernel(r):
    """A lens's out-of-focus disc: flat, a little brighter at the rim, with a soft edge. r in pixels."""
    n = int(np.ceil(r)) + 2
    Y, X = np.mgrid[-n : n + 1, -n : n + 1].astype(np.float32)
    d = np.hypot(X, Y) / r
    k = sstep(1.04, 0.92, d) * (0.84 + 0.26 * d**4)
    return k / k.sum()


def gather(sp, t_end, res_w, res_h, scale):
    acc = [np.zeros((res_h // D, res_w // D, 3), np.float32) for D in DOWN]
    t0, t1 = t_end - SHUTTER, t_end
    alive = np.nonzero((sp.t0 < t1) & (sp.t0 + sp.life > t0))[0]
    f = F_PX * scale
    cx_, cz_ = camera_at(t_end - SHUTTER / 2)

    def pos(sel, a):
        tau = sp.tau[sel][:, None]
        e = 1.0 - np.exp(-a / tau)
        return sp.x0[sel][:, None] + sp.vx[sel][:, None] * tau * e, sp.y0[sel][:, None] + sp.vy[sel][:, None] * tau * e, sp.z0[sel][:, None] + (sp.vz[sel][:, None] + G * tau) * tau * e - G * tau * a

    # how long each streak is on the sensor decides its sampling; cull what is far off the frame
    a0 = np.maximum(t0 - sp.t0[alive], 1e-3)[:, None]
    a1 = np.minimum(t1 - sp.t0[alive], sp.life[alive])[:, None]
    xa, ya, za = pos(alive, a0)
    xb, yb, zb = pos(alive, a1)
    ya, yb = np.maximum(ya, 0.2), np.maximum(yb, 0.2)
    ua, va = xa * f / ya, za * f / ya
    ub, vb = xb * f / yb, zb * f / yb
    length = np.hypot(ub - ua, vb - va)[:, 0]
    mx, my = res_w * 0.75, res_h * 0.75
    inside = ~(((ua[:, 0] < -mx) & (ub[:, 0] < -mx)) | ((ua[:, 0] > mx) & (ub[:, 0] > mx)) | ((va[:, 0] < -my) & (vb[:, 0] < -my)) | ((va[:, 0] > my) & (vb[:, 0] > my))) | (length > res_w)
    alive = alive[inside]
    length = length[inside]
    edges = [0, 6, 14, 30, 70, 160, 360, 800, 1e9]
    ms = [6, 14, 30, 70, 170, 380, 850, 1500]
    for bi in range(len(ms)):
        idx = alive[(length >= edges[bi]) & (length < edges[bi + 1])]
        M = ms[bi]
        chunk = max(1000, int(3e6 / M))
        for s in range(0, idx.size, chunk):
            sel = idx[s : s + chunk]
            u = (np.arange(M)[None, :] + sp.jit[sel][:, None]) / M
            aa = np.maximum(t0 - sp.t0[sel], 1e-3)[:, None]
            ab = np.minimum(t1 - sp.t0[sel], sp.life[sel])[:, None]
            a = aa + (ab - aa) * u
            dt = (ab - aa) / M
            x, y, z = pos(sel, a)
            tt = sp.t0[sel][:, None] + a
            gx, gz = sp.gusts(x, z, tt)
            gr = 0.07 * np.minimum(a, 2.5) ** 1.5 * np.minimum(y / 2.5, 1.0)
            wob = sp.wob[sel][:, None] * np.minimum(a * 4.0, 1.0) * np.sin(sp.ph1[sel][:, None] + sp.f1[sel][:, None] * 0.15 * tt)
            x = x + gx * gr + wob * np.cos(sp.th[sel])[:, None]
            z = z + gz * gr + wob * np.sin(sp.th[sel])[:, None]
            age = np.minimum(a / sp.life0[sel][:, None], 1.0)
            T = sp.T0[sel][:, None] * (1.0 + 0.035 * np.exp(-a / 0.1) - 0.64 * age**0.62)
            fl = np.maximum(1.0 + sp.flick[sel][:, None] * (0.7 * np.sin(sp.ph1[sel][:, None] + sp.f1[sel][:, None] * tt) + 0.5 * np.sin(sp.ph2[sel][:, None] + sp.f2[sel][:, None] * tt)), 0.02)
            flr = sp.flare[sel][:, None] * np.exp(-(((age - sp.flare_at[sel][:, None]) / 0.035) ** 2))
            br = sp.burst[sel][:, None]
            sw = np.where(br > 0, 3.5 * np.exp(-np.maximum(br - a, 0.0) / 0.03), 0.0)
            on = (0.015 + 0.985 * sstep(0.0, 1.0, a / sp.ign[sel][:, None])) * sstep(1.0, 0.86, np.minimum(a / sp.life[sel][:, None], 1.0))
            # the shutter: soft at both ends, so that a blow or a burst comes in and leaves without a pop
            ph = (tt - t0) / SHUTTER
            shut = np.clip(np.minimum(ph, 1.0 - ph) / 0.05, 0.0, 1.0)
            y = np.maximum(y, 0.15)
            E = sp.gain[sel][:, None] * fl * (1.0 + flr + sw) * on * dt * shut * (DREF / y) ** 2
            w = f / y
            ix = res_w / 2.0 + (x - cx_) * w
            iy = res_h / 2.0 - (z - cz_) * w
            coc = F_PX * APERTURE * np.abs(1.0 / y - 1.0 / FOCUS)  # diameter, px at 2560
            lev = np.interp(coc.ravel(), COC, np.arange(len(COC)))
            ok = (E.ravel() > 1e-7) & (ix.ravel() > -40 * scale) & (ix.ravel() < res_w + 40 * scale) & (iy.ravel() > -40 * scale) & (iy.ravel() < res_h + 40 * scale)
            ix_, iy_, E_, T_, lev_ = ix.ravel()[ok], iy.ravel()[ok], E.ravel()[ok], T.ravel()[ok], lev[ok]
            if ix_.size == 0:
                continue
            rgb = light(T_) * E_[:, None]
            l0 = np.minimum(lev_.astype(np.int32), len(COC) - 2)
            fr = (lev_ - l0).astype(np.float64)[:, None]
            for k in range(len(COC)):
                for m_, wt in ((l0 == k, 1.0 - fr), (l0 + 1 == k, fr)):
                    if m_.any():
                        D = DOWN[k]
                        stamp(acc[k], ix_[m_] / D, iy_[m_] / D, rgb[m_] * wt[m_], bilinear=D == 1)
    return acc


def lens(acc, res_w, res_h, scale):
    """Blur each level by its circle of confusion, at its own small size. The whole is then the picture through one lens, with a little flare."""
    out = np.zeros((res_h, res_w, 3), np.float32)
    for k, im in enumerate(acc):
        D = DOWN[k]
        r = COC[k] * scale / 2.0 / D
        if k == 0:
            b = cv2.GaussianBlur(im, (0, 0), 0.72 * max(scale, 0.7))
            b = b + 0.05 * cv2.GaussianBlur(im, (0, 0), 3.2 * scale) + 0.02 * cv2.GaussianBlur(im, (0, 0), 11.0 * scale)
        elif r < 1.3:
            b = cv2.GaussianBlur(im, (0, 0), max(r, 0.6))
        else:
            b = cv2.filter2D(im, -1, disc_kernel(r), borderType=cv2.BORDER_CONSTANT)
        if D > 1:
            b = cv2.resize(b, (res_w, res_h), interpolation=cv2.INTER_LINEAR) / (D * D)  # the same energy over D^2 times the pixels
        out += b
    return out


def _smoke_fields(res_w, res_h):
    w, h = res_w // 4, res_h // 4
    s = 2560.0 / res_w
    return fbm((h * 2, w * 2), 1.0, 6.0 / s, 300.0 / s, 2.9, 77), fbm((h * 2, w * 2), 1.0, 3.0 / s, 110.0 / s, 2.5, 78)


def smoke(L, t, res_w, res_h, fields):
    """Thin smoke far behind, lit by the sparks. Shaped noise, its light a blur of the sparks themselves."""
    a, b = fields
    h, w = a.shape[0] // 2, a.shape[1] // 2

    def slide(f, dx, dy):
        M = np.float32([[1, 0, -w / 2 + dx * w], [0, 1, -h / 2 + dy * h]])
        return cv2.warpAffine(f, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    n = 0.6 * slide(a, 0.015 * t, -0.03 * t) + 0.3 * slide(b, 0.025 * t, -0.05 * t)
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    y = Y / h
    env = sstep(0.1, 0.5, y)
    d = np.clip(0.42 + 0.4 * n, 0.0, None) ** 1.4 * env
    small = cv2.resize(L, (w, h), interpolation=cv2.INTER_AREA)
    light_ = 0.35 * cv2.GaussianBlur(small, (0, 0), 25.0) + 0.65 * cv2.GaussianBlur(small, (0, 0), 90.0)
    out = light_ * d[..., None] * np.array([1.0, 0.66, 0.38], np.float32)
    return cv2.resize(out, (res_w, res_h), interpolation=cv2.INTER_CUBIC)


def render(sp, fields, i, scale):
    res_w, res_h = int(2560 * scale), int(1440 * scale)
    t = (i + 1) / FPS
    acc = gather(sp, t, res_w, res_h, scale)
    L = lens(acc, res_w, res_h, scale)
    L = L + 0.16 * smoke(L, t, res_w, res_h, fields)
    Y = (np.arange(res_h, dtype=np.float32) / res_h)[:, None, None]
    # the night: near-neutral, a touch lighter low down
    sky = np.array([0.0020, 0.0021, 0.0025], np.float32) * (1.0 + 0.7 * sstep(0.3, 1.0, Y))
    return develop((L * K * (scale / 0.5) ** 2 + sky).astype(np.float32), **{**LOOK, "seed": 1400 + i})


def apex(img):
    """Row of the arc: the top edge of the thick of the light, in the middle 70% of the frame; strays above it are ignored by a large blur."""
    g = cv2.GaussianBlur(img.mean(-1).astype(np.float32), (0, 0), img.shape[1] / 110.0)
    g = g[:, int(g.shape[1] * 0.15) : int(g.shape[1] * 0.85)]
    th = 0.22
    rows = np.argmax(g > th, axis=0)
    rows = rows[g.max(0) > th]
    return float(rows.min()) / img.shape[0] if rows.size else -1.0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "look"
    q = sys.argv[2] if len(sys.argv) > 2 else "preview"
    scale = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    sp = Sparks()
    fields = _smoke_fields(int(2560 * scale), int(1440 * scale))
    d = os.path.join(OUT, "s14_datiehua")
    os.makedirs(d, exist_ok=True)
    if mode == "look":
        i = int(sys.argv[3]) if len(sys.argv) > 3 else 12
        im = render(sp, fields, i, scale)
        save_png(os.path.join(d, f"look_{q}.png"), im)
        print(os.path.join(d, f"look_{q}.png"), "apex", apex(im))
        return
    td = os.path.join(OUT, f"s14_datiehua_take_{q}" + os.environ.get("S14_SUFFIX", ""))  # a suffix keeps a new take out of the folder the film reads until it has been checked
    os.makedirs(td, exist_ok=True)
    i0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    i1 = int(sys.argv[4]) if len(sys.argv) > 4 else N_FRAMES
    for i in range(i0, i1):
        p = os.path.join(td, f"f{i:03d}.png")
        if not os.path.exists(p):
            im = render(sp, fields, i, scale)
            save_png(p, im)
            print(p, "apex", round(apex(im), 4), flush=True)
    print(td, flush=True)


main()
