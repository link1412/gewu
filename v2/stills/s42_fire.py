"""Shot 42: real moving fire. A 3D buoyant reacting flow solved on the GPU, then ray-marched through the shot's camera over a plate of the door.

    python s42_fire.py sim  NAME '{json params}'     solve, store soot and temperature per step in out/v2/s42_sim/NAME/
    python s42_fire.py look NAME FRAMES... -- '{json}'  render frames for looking
    python s42_fire.py take NAME OUTDIR N -- '{json}'    16-bit f###.png and print-look v###.jpg

Needs torch. See s42_yaohuo.py for the plate.

The mechanism, not the look (values are estimates from general knowledge of flames, none measured from a real kiln):
- velocity: incompressible, spectral projection, MacCormack advection, buoyancy g(1 - 300/T), gas expansion where fuel burns, weak vorticity confinement. No turbulence noise outside the firebox;
- walls: the arch as a solid by volume penalisation (masked and projected twice): small leaks are accepted;
- chemistry: fuel + oxygen, one fast step above ignition; soot forms in hot fuel-rich gas and burns away in oxygen; radiative loss cools soot-laden gas, so tongue tips go red;
- light: radiative transfer through soot: Planck at its temperature, with real opacity, so a thick core hides what is behind it and a thin edge is deep orange; lens blur by depth; 180 degree shutter by averaging steps.
- pushes for the picture, not mechanisms: soot burns out faster above the arch (kh), the soot edge is steepened at render (s0, s1), the temperature seen is capped (Tmax), firelight weights come from 8 stand-in emitters.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import torch
import torch.nn.functional as TF

import s42_geom as G

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2")
DEV = "cuda" if torch.cuda.is_available() and not os.environ.get("S42_CPU") else "cpu"
LOX = (-66.0, -28.0, -48.0)
HIX = (66.0, 58.0, 50.0)

SIM = dict(
    dx=0.4, dt=1 / 1200.0, spin=1.0, frames=27, cap_fps=150.0, cap_shutter=0.5, cap_n=4, seed=42,
    g=981.0, conf=0.0, nu=1.5,
    A=600.0, Tign=380.0, s=2.0, q=4200.0, alpha=0.3,  # burn rate 1/s, ignition K, oxygen used per fuel, K per unit fuel burnt, share of expansion kept
    kf=40.0, ko=400.0, cool0=0.6, cool1=1.0, Tsoot=1150.0, kh=110.0, zh0=2.0, zh1=9.0,  # soot formed and burnt away 1/s; radiative loss 1/s, clear and sooty gas; push above the arch
    Tkiln=800.0, O_in=0.75, relax=2.0, Tfuel=1560.0, Q=6.0,
    bed_x=9.0, bed_y0=-5.0, bed_y1=14.0, bed_z=-36.0, src_rate=70.0, src_scale=17.0, src_tau=0.09, src_thresh=-0.4, kick=30.0, puff=0.25,
)


def grids(dx):
    n = [int(round((HIX[i] - LOX[i]) / dx)) // 2 * 2 for i in range(3)]
    xs = [LOX[i] + (np.arange(n[i]) + 0.5) * (HIX[i] - LOX[i]) / n[i] for i in range(3)]
    return n, xs


def solid_mask(X, Y, Z):
    r = torch.hypot(X, Z - G.ZC)
    arch = (Y >= 0.0) & (Y <= G.THICK) & (r > G.R)
    inner = (Y > G.THICK) & ((Z > G.CEIL) | (Y > G.BACK))
    return arch | inner


class Noise:
    """Smooth vector noise on a coarse grid, cross-fading in time: where and how the firebox makes gas."""

    def __init__(self, shape, cells, tau, dt, ch, seed):
        self.g = torch.Generator(device="cpu").manual_seed(seed)
        self.shape, self.cells, self.ch = shape, cells, ch
        self.n = max(1, int(round(tau / dt)))
        self.i = 0
        self.a, self.b = self.draw(), self.draw()

    def draw(self):
        v = torch.randn((1, self.ch) + tuple(self.cells), generator=self.g).to(DEV)
        return TF.interpolate(v, size=self.shape, mode="trilinear", align_corners=True)[0].half()

    def __call__(self):
        if self.i == self.n:
            self.a, self.b, self.i = self.b, self.draw(), 0
        w = 0.5 - 0.5 * np.cos(np.pi * self.i / self.n)
        self.i += 1
        return (self.a.float() * (1 - w) + self.b.float() * w) / np.sqrt((1 - w) ** 2 + w**2)


def sim(name, over):
    P = {**SIM, **over}
    d = os.path.join(OUT, "s42_sim", name)
    os.makedirs(d, exist_ok=True)
    json.dump(P, open(os.path.join(d, "params.json"), "w"), indent=1)
    torch.manual_seed(P["seed"])
    dx, dt = P["dx"], P["dt"]
    (nx, ny, nz), (xs, ys, zs) = grids(dx)
    print(f"[sim] {nx}x{ny}x{nz} = {nx*ny*nz/1e6:.1f} M cells on {DEV}", flush=True)
    t_ = lambda a: torch.tensor(a, dtype=torch.float32, device=DEV)
    Z, Y, X = torch.meshgrid(t_(zs), t_(ys), t_(xs), indexing="ij")
    shape = (nz, ny, nx)
    solid = solid_mask(X, Y, Z)
    fluid = (~solid).float()
    interior = ((Y > G.THICK) & ~solid).float()
    band = TF.max_pool3d(solid.float()[None, None], int(2 * round(1.2 / dx) + 1), 1, int(round(1.2 / dx)))[0, 0] * fluid
    # the firebox's hot source, low and deep
    # the bed: wood burning on the door's sill, under the arch: one mass of fire, not a filled room
    fb = torch.exp(-((X / P["bed_x"]) ** 2)) * torch.clamp((Y - P["bed_y0"]) / 4.0, 0, 1) * torch.clamp((P["bed_y1"] - Y) / 4.0, 0, 1) * torch.clamp((P["bed_z"] - Z) / 3.0, 0, 1) * fluid
    above = torch.hypot(X, Z - G.ZC) - G.R  # distance outside the arch, all round its curve
    height_kill = torch.exp(-dt * P["kh"] * torch.clamp((above - P["zh0"]) / (P["zh1"] - P["zh0"]), 0, 1) * (Y < G.THICK + 1))
    del above
    # sponges: far air is reset, and takes away the volume the firebox and the flames add
    sp = torch.clamp((Z - 36.0) / 14.0, 0, 1) + torch.clamp((-21.0 - Y) / 7.0, 0, 1) + torch.clamp((-42.0 - Z) / 5.0, 0, 1) * (Y < 0)
    sp = sp.clamp(0, 1) * fluid
    # spectral projection
    kz = torch.fft.fftfreq(nz, d=dx, device=DEV) * 2 * np.pi
    ky = torch.fft.fftfreq(ny, d=dx, device=DEV) * 2 * np.pi
    kx = torch.fft.rfftfreq(nx, d=dx, device=DEV) * 2 * np.pi
    KZ = kz[:, None, None]
    KY = ky[None, :, None]
    KX = kx[None, None, :]
    K2 = KX**2 + KY**2 + KZ**2
    K2[0, 0, 0] = 1.0
    visc = torch.exp(-P["nu"] * K2 * dt)  # hot gas is viscous: about 2-3 cm2/s at 1500 K (from general knowledge); this is what keeps a flame silky

    def project(u, rhs=None, visc_now=1.0):
        ux, uy, uz = (torch.fft.rfftn(u[i], dim=(0, 1, 2)) for i in range(3))
        div = 1j * (KX * ux + KY * uy + KZ * uz)
        if rhs is not None:
            div = div - torch.fft.rfftn(rhs, dim=(0, 1, 2))
            del_ = None
        p = div / K2  # p_hat = -div/k2 with grad -> subtract i k phi, phi = -div/k2... sign handled below
        p[0, 0, 0] = 0
        ux = (ux + 1j * KX * p) * visc_now
        uy = (uy + 1j * KY * p) * visc_now
        uz = (uz + 1j * KZ * p) * visc_now
        return torch.stack([torch.fft.irfftn(a, s=shape, dim=(0, 1, 2)) for a in (ux, uy, uz)])

    # base sampling grid, normalised, order x y z
    L = [(HIX[i] - LOX[i]) * (1 - 1 / n) for i, n in enumerate((nx, ny, nz))]
    base = torch.stack([(X - (xs[0] + xs[-1]) / 2) * 2 / L[0], (Y - (ys[0] + ys[-1]) / 2) * 2 / L[1], (Z - (zs[0] + zs[-1]) / 2) * 2 / L[2]], -1)
    scale = t_([2 / L[0], 2 / L[1], 2 / L[2]])

    def advect(f, u, h):
        g = base + (-h * u.permute(1, 2, 3, 0)) * scale
        return TF.grid_sample(f[None], g[None], mode="bilinear", padding_mode="border", align_corners=True)[0]

    # state: u v w | F O T S
    U = torch.zeros((3,) + shape, device=DEV)
    F = torch.zeros(shape, device=DEV)
    O = (1 - interior * (1 - P["O_in"])) * fluid
    T = 300.0 + (P["Tkiln"] - 300.0) * interior
    S = torch.zeros(shape, device=DEV)
    # noise: where the gas comes, and the kick it comes with. Coarse cells at src_scale cm
    c = tuple(max(int((HIX[2 - i] - LOX[2 - i]) / P["src_scale"]), 2) for i in range(3))
    nsrc = Noise(shape, c, P["src_tau"], dt, 1, P["seed"] + 1)
    nkick = Noise(shape, c, P["src_tau"] * 1.3, dt, 3, P["seed"] + 2)
    # embers: a few thousand flecks that follow the gas, with their own drag
    rng = np.random.default_rng(P["seed"] + 3)
    M = 2500
    ep = t_(np.c_[rng.uniform(-64, 64, M), rng.uniform(G.THICK, G.BACK - 4, M), rng.uniform(-46, 10, M)])
    ev = torch.zeros_like(ep)
    etau = t_(rng.lognormal(np.log(0.05), 0.6, M))
    steps_spin = int(P["spin"] / dt)
    period = 1.0 / P["cap_fps"] / dt
    win = P["cap_shutter"] * period
    cap = {}
    for i in range(P["frames"]):
        for e in range(P["cap_n"]):
            cap[steps_spin + int(round(i * period + e * win / P["cap_n"]))] = (i, e)
    steps = max(cap) + 1
    puff_f = rng.uniform(1.5, 6.0, 5)
    puff_p = rng.uniform(0, 2 * np.pi, 5)
    conf = P["conf"]
    t0 = time.time()
    for it in range(steps):
        tnow = it * dt
        # firebox: new gas
        n = nsrc()[0]
        m = torch.clamp((n - P["src_thresh"]) / 0.5, 0, 1) * fb
        puff = 1.0 + P["puff"] * float(np.mean(np.sin(2 * np.pi * puff_f * tnow + puff_p)) * 2.0)
        add = 1 - torch.exp(-P["src_rate"] * dt * m * max(puff, 0.1))
        F = F + (1 - F) * add
        T = T + (P["Tfuel"] - T) * add  # the gas comes off the burning charge hot; the rest of the kiln's air is cooler
        O = O * (1 - add)
        T = T + (P["Tkiln"] - T).clamp(min=0) * (1 - torch.exp(-P["relax"] * dt * interior))
        U = U + nkick() * (fb * P["kick"] * dt * 9.0)
        # buoyancy
        U[2] = U[2] + dt * P["g"] * (1 - 300.0 / T.clamp(min=300.0)) * fluid
        # vorticity confinement
        if conf:
            r = lambda f, s, a: torch.roll(f, s, a)
            wx = (r(U[2], -1, 1) - r(U[2], 1, 1) - r(U[1], -1, 0) + r(U[1], 1, 0)) / (2 * dx)
            wy = (r(U[0], -1, 0) - r(U[0], 1, 0) - r(U[2], -1, 2) + r(U[2], 1, 2)) / (2 * dx)
            wz = (r(U[1], -1, 2) - r(U[1], 1, 2) - r(U[0], -1, 1) + r(U[0], 1, 1)) / (2 * dx)
            m_ = torch.sqrt(wx**2 + wy**2 + wz**2 + 1e-6)
            gx = r(m_, -1, 2) - r(m_, 1, 2)
            gy = r(m_, -1, 1) - r(m_, 1, 1)
            gz = r(m_, -1, 0) - r(m_, 1, 0)
            gm = torch.sqrt(gx**2 + gy**2 + gz**2 + 1e-6)
            gx, gy, gz = gx / gm, gy / gm, gz / gm
            U[0] = U[0] + dt * conf * dx * (gy * wz - gz * wy) * 9.0
            U[1] = U[1] + dt * conf * dx * (gz * wx - gx * wz) * 9.0
            U[2] = U[2] + dt * conf * dx * (gx * wy - gy * wx) * 9.0
            del wx, wy, wz, m_, gx, gy, gz, gm
        # sponge drag
        U = U * (1 - sp * 0.25)
        # chemistry: one explicit fast step
        ign = torch.clamp((T - P["Tign"]) / 60.0, 0, 1)
        b = torch.minimum(F, O / P["s"]) * (1 - torch.exp(-P["A"] * dt * ign))
        F = F - b
        O = O - P["s"] * b
        T = T + P["q"] * b
        hot = torch.clamp((T - P["Tsoot"]) / 250.0, 0, 1)
        S = S + dt * P["kf"] * F * (1 - S) * hot * (1 - O).clamp(0, 1)
        S = S * torch.exp(-dt * P["ko"] * O * ign)
        # the frame's upper part stays dark: outside the arch soot burns out faster with height. A push for the picture (the captions sit above), not a mechanism
        S = S * height_kill
        T = 300.0 + (T - 300.0) * torch.exp(-dt * (P["cool0"] + P["cool1"] * S))
        # volume: firebox source, heat expansion, sink in the sponges so the total balances
        rhs = fb * P["Q"] * max(puff, 0.1) + P["alpha"] * b / dt * (P["q"] / T.clamp(min=300.0))
        rhs = rhs.clamp(max=120.0) * fluid
        rhs = rhs - sp * (rhs.sum() / sp.sum())
        U = project(U * fluid, rhs, visc) * fluid
        U = project(U, rhs) * fluid
        # advection, MacCormack on everything, limited
        f = torch.stack([U[0], U[1], U[2], F, O, T, S])
        vel = U.clone()
        a = advect(f, vel, dt)
        back = advect(a, vel, -dt)
        cor = a + 0.5 * (f - back)
        lo = -TF.max_pool3d(-a[None], 3, 1, 1)[0]
        hi = TF.max_pool3d(a[None], 3, 1, 1)[0]
        cor = torch.minimum(torch.maximum(cor, lo), hi)
        del lo, hi, back, a, f
        U = cor[:3] * fluid
        F, O, T, S = cor[3], cor[4], cor[5], cor[6]
        del cor
        # solids and far air
        keep = fluid
        F = (F * keep).clamp(0, 1)
        O = (O * keep + (1 - keep)).clamp(0, 1)
        T = (T * keep + 300.0 * (1 - keep)).clamp(300.0, 2100.0)
        S = (S * keep).clamp(0, 1)
        # a thin band at the walls is smoothed each step: the masked boundary otherwise rings into speckle
        fz = torch.stack([F, O, T, S])[None]
        fs = TF.avg_pool3d(fz, 3, 1, 1)
        fz = fz + (fs - fz) * band
        F, O, T, S = fz[0, 0], fz[0, 1], fz[0, 2], fz[0, 3]
        del fz, fs
        rs = sp * 0.3
        F, S = F * (1 - rs), S * (1 - rs)
        O = O + (1 - O) * rs
        T = T + (300.0 - T) * rs
        # embers
        ii = (ep - t_([LOX[0], LOX[1], LOX[2]])) / t_([HIX[0] - LOX[0], HIX[1] - LOX[1], HIX[2] - LOX[2]]) * 2 - 1
        vs = TF.grid_sample(U[None], ii[None, None, None], mode="bilinear", padding_mode="border", align_corners=True)[0, :, 0, 0, :].T
        ev = ev + (vs - ev) * (1 - torch.exp(-dt / etau))[:, None]
        ev[:, 2] = ev[:, 2] - dt * 120.0
        ep = ep + ev * dt
        out = (ep[:, 2] > HIX[2] - 6) | (ep[:, 1] < LOX[1] + 4) | (ep[:, 2] < LOX[2] + 1)
        if out.any():
            k = int(out.sum())
            ep[out] = t_(np.c_[rng.uniform(-64, 64, k), rng.uniform(G.THICK, G.BACK - 4, k), rng.uniform(-46, 10, k)])
            ev[out] = 0
        if it in cap:
            i, e = cap[it]
            np.save(os.path.join(d, f"S{i:03d}_{e}.npy"), S.half().cpu().numpy())
            np.save(os.path.join(d, f"T{i:03d}_{e}.npy"), T.half().cpu().numpy())
            np.save(os.path.join(d, f"E{i:03d}_{e}.npy"), ep.cpu().numpy())
        if it % 25 == 0 or it == steps - 1:
            vmax = float(U.abs().max())
            print(f"[sim] {it}/{steps} t={tnow:.2f} vmax {vmax:.0f} cm/s, S {float(S.mean()):.4f} T {float(T.mean()):.0f} F {float(F.mean()):.4f} O {float(O.mean()):.3f}; {(time.time()-t0)/(it+1):.3f} s/step", flush=True)
    json.dump({"frames": P["frames"], "n": P["cap_n"], "shape": [nz, ny, nx]}, open(os.path.join(d, "meta.json"), "w"))
    print(f"[sim] {time.time()-t0:.0f} s", flush=True)


# --- the camera and the light -----------------------------------------------------------------------------------
LOOK = dict(
    w=1280, kabs=0.5, s0=0.12, s1=0.5, Tmax=1760.0, tc=1.0, Tref=1500.0, K=0.25, aperture=1.3, sstep=1, estep=1,
    p0=3.0, gl=600.0, gl_in=0.1, W_ref=30000.0, flick=0.08, shimmer=2.0, ember=1.5,
    wb=(1.05, 0.9, 0.6), contrast=1.5, saturation=1.0, black=0.0008, grain=1.2, sharpen=0.2, halation=0.1, glare=0.012, vignette=0.2, ca=0.0003,
)
LAM = (610e-9, 550e-9, 465e-9)


def planck(T):
    """Linear RGB of a soot flame at T: relative to green at 1550 K, as the plate. Soot's emissivity goes as 1/lambda."""
    c2 = 1.4388e-2
    out = []
    for lam in LAM:
        a = (550e-9 / lam) ** 6
        out.append(a * torch.exp(c2 / (550e-9 * 1550.0) - c2 / (lam * T)))
    return torch.stack(out)


def view(w, h):
    right, up, back = G.axes()
    u = (torch.arange(w, device=DEV, dtype=torch.float32) + 0.5) / w - 0.5
    v = 0.5 - (torch.arange(h, device=DEV, dtype=torch.float32) + 0.5) / h
    V, U = torch.meshgrid(v, u, indexing="ij")
    a = G.W / G.DIST
    b = a * h / w
    d = [-float(back[i]) + float(right[i]) * a * U + float(up[i]) * b * V for i in range(3)]
    return d


def expose(S, T, dirs, dy, ys, lk, w, bins):
    """One instant through the camera: march slices front to back. Returns light per blur level, transmission, and the path integral of (1 - 300/T) for the shimmer."""
    h = dirs[0].shape[0]
    Cx, Cy, Cz = [float(a) for a in G.LOC]
    dn = torch.sqrt(dirs[0] ** 2 + dirs[1] ** 2 + dirs[2] ** 2)
    ds = dy * dn / dirs[1].abs()
    L = [torch.zeros((3, h, w), device=DEV) for _ in bins]
    tau = torch.ones((h, w), device=DEV)
    alive = torch.ones((h, w), device=DEV)
    hot = torch.zeros((h, w), device=DEV)
    fpx = w * G.DIST / G.W
    px = G.W / w  # cm per pixel at the target
    b_ = torch.tensor(bins, device=DEV, dtype=torch.float32)
    sst = lk["sstep"]
    F = torch.stack([S, T], 0)  # (2, nz, ny, nx)
    dx_ = (HIX[0] - LOX[0]) / S.shape[2]
    # each ray is shifted by up to half a cell, so that the grid against the camera's perspective does not print as a weave
    jx = (torch.rand((h, w), device=DEV) - 0.5) * dx_
    jz = (torch.rand((h, w), device=DEV) - 0.5) * dx_
    nz, ny, nx = S.shape
    sx, sz = 2.0 / (HIX[0] - LOX[0]), 2.0 / (HIX[2] - LOX[2])
    for j in range(0, ny, sst):
        y = float(ys[j])
        t = (y - Cy) / dirs[1]
        X = Cx + t * dirs[0]
        Z = Cz + t * dirs[2]
        if 0.0 <= y <= G.THICK:
            r = torch.hypot(X, Z - G.ZC)
            alive = alive * torch.clamp(0.5 - (r - G.R) / px, 0, 1)
        elif y > G.THICK:
            alive = alive * torch.clamp(0.5 - (Z - G.CEIL) / px, 0, 1)
        if y >= G.BACK:
            break
        fs = F[:, :, j, :] if sst == 1 else F[:, :, j : j + sst, :].mean(2)
        g = torch.stack([(X + jx - LOX[0]) * sx - 1, (Z + jz - LOX[2]) * sz - 1], -1)
        v = TF.grid_sample(fs[None], g[None], mode="bilinear", padding_mode="border", align_corners=False)[0]
        s, Tv = v[0].clamp(min=0), v[1].clamp(min=300.0)
        if y < G.THICK:
            hot = hot + (1 - 300.0 / Tv) * ds * sst * alive
        Tv = (lk["Tref"] + (Tv - lk["Tref"]) * lk["tc"]).clamp(min=300.0, max=lk["Tmax"])
        s = torch.clamp((s - lk["s0"]) / (lk["s1"] - lk["s0"]), 0, 1)
        s = s * s * (3 - 2 * s)  # the flame's edge is where soot ends: steep, so a soft field gives a clean edge
        a = torch.exp(-lk["kabs"] * s * ds * sst)
        e = planck(Tv) * (1 - a)
        coc = fpx * lk["aperture"] * abs(1.0 / (y - Cy) - 1.0 / (0.0 - Cy))
        k = int(torch.argmin(torch.abs(b_ - coc)))
        L[k] += e * (tau * alive)
        tau = tau * a
    return L, tau, hot


def light_weights(S, T, lk, ys, zs, xs):
    """The flame's power near each stand-in emitter: on a coarse grid, cell by cell to the nearest one. Inside the door and in front of the wall only."""
    n = 4
    Tv = (lk["Tref"] + (T.clamp(min=300.0) - lk["Tref"]) * lk["tc"]).clamp(min=300.0)
    E = TF.avg_pool3d((S.clamp(min=0) * planck(Tv)[1])[None, None], n)[0, 0]
    t_ = lambda a: torch.tensor(a, dtype=torch.float32, device=DEV)
    zc, yc, xc = t_(zs[n // 2 :: n][: E.shape[0]]), t_(ys[n // 2 :: n][: E.shape[1]]), t_(xs[n // 2 :: n][: E.shape[2]])
    Zg, Yg, Xg = torch.meshgrid(zc, yc, xc, indexing="ij")
    E = E * (Yg < G.THICK + 8)
    d = torch.stack([(Xg - a) ** 2 + (Yg - b) ** 2 + (Zg - c) ** 2 for a, b, c in G.LIGHTS])
    lab = d.argmin(0)
    return torch.stack([E[lab == i].sum() for i in range(len(G.LIGHTS))]).cpu().numpy() * (n * (xs[1] - xs[0])) ** 3


def embers(ep_list, bins, Lb, w, h, lk):
    """Flecks of ash lofted by the gas: a line of light in the shutter. Hidden when behind masonry. Temperature and brightness per fleck are random, estimates."""
    right, up, back = G.axes()
    C = G.LOC.astype(np.float32)
    a = G.W / G.DIST
    fpx = w / a
    rng = np.random.default_rng(424242)
    M = ep_list[0].shape[0]
    gain = rng.lognormal(0, 0.9, M) * lk["ember"]
    Tf = rng.uniform(1100, 1650, M)
    tint = np.stack([np.exp(1.4388e-2 / (550e-9 * 1550.0) - 1.4388e-2 / (l * Tf)) for l in LAM], -1)
    tint = tint * np.array([(550e-9 / l) ** 6 for l in LAM])
    tint = tint / tint.max(1, keepdims=True)
    vis = rng.random(M) < lk.get("ember_frac", 0.12)
    for q0, q1 in zip(ep_list[:-1], ep_list[1:]):
        for t in np.linspace(0, 1, 6, endpoint=False):
            P = q0 + (q1 - q0) * t
            d = P - C
            dz = -(d @ back)
            u = (d @ right) / dz * fpx + w / 2
            v = -(d @ up) / dz * fpx + h / 2
            r = np.hypot(P[:, 0], P[:, 2] - G.ZC)
            blocked = ((P[:, 1] >= 0) & (P[:, 1] <= G.THICK) & (r > G.R)) | ((P[:, 1] > G.THICK))
            keep = vis & ~blocked & (u >= 1) & (u < w - 2) & (v >= 1) & (v < h - 2)
            if not keep.any():
                continue
            coc = fpx * lk["aperture"] * np.abs(1.0 / dz[keep] - 1.0 / (0.0 - C[1]))
            k = np.abs(np.array(bins)[None] - coc[:, None]).argmin(1)
            for b_i in range(len(bins)):
                m = k == b_i
                if not m.any():
                    continue
                uu, vv = u[keep][m], v[keep][m]
                iu, iv = uu.astype(int), vv.astype(int)
                e = (gain[keep][m][:, None] * tint[keep][m] / 6.0 / max(len(ep_list) - 1, 1) * (w / 1920.0) ** 2).astype(np.float32)
                np.add.at(Lb[b_i], (iv, iu), e)


def blur_bins(Ls, bins, ep, w, h, lk):
    import cv2

    Lb = [L.permute(1, 2, 0).cpu().numpy() for L in Ls]
    if lk["ember"] > 0 and len(ep) > 1:
        embers(ep, bins, Lb, w, h, lk)
    out = None
    for im, c in zip(Lb, bins):
        c = c * w / 1920.0
        if c > 0.8:
            im = cv2.GaussianBlur(im, (0, 0), c / 2.4)
        else:
            im = cv2.GaussianBlur(im, (0, 0), 1.1 * w / 1920.0)
        out = im if out is None else out + im
    return out


class Plate:
    def __init__(self, w, h):
        import cv2

        self.p = {}
        d = os.path.join(OUT, "s42_yaohuo_plate")
        for tag in ["p0"] + [f"l{i}" for i in range(len(G.LIGHTS))]:
            f = os.path.join(d, f"{tag}.linear.npy")
            if not os.path.exists(f):
                raise SystemExit(f"plate pass missing: {f}")
            a = np.load(f).astype(np.float32)
            self.p[tag] = cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA if a.shape[1] > w else cv2.INTER_CUBIC)

    def lit(self, wts, flick, lk):
        out = self.p["p0"] * lk["p0"] * flick
        for i, a in enumerate(wts):
            # the row inside the door lights the underside; it is held back so the arch stays a dark band
            out = out + self.p[f"l{i}"] * (lk["gl"] * float(a) * (1.0 if i < 4 else lk["gl_in"]))
        return out


def soften(a):
    """A 1-2-1 filter on each axis: the grid must not print through the steep emission curve as a weave."""
    x = a[None, None]
    for dim in range(3):
        k = [1, 1, 1]
        k[dim] = 3
        w = torch.tensor([0.25, 0.5, 0.25], device=DEV, dtype=x.dtype).view(1, 1, *k)
        pad = [0, 0, 0]
        pad[dim] = 1
        x = TF.conv3d(x, w, padding=tuple(pad))
    return x[0, 0]


def frame_linear(name, i, lk, w, h, plate, stats=None, ema=None):
    import cv2

    d = os.path.join(OUT, "s42_sim", name)
    m = json.load(open(os.path.join(d, "meta.json")))
    (nx, ny, nz), (xs, ys, zs) = grids(json.load(open(os.path.join(d, "params.json")))["dx"])
    dirs = view(w, h)
    dy = float(ys[1] - ys[0])
    if i >= m["frames"]:
        raise SystemExit(f"frame {i}: the sim has {m['frames']}")
    es = list(range(m["n"]))
    ks = es[:: lk["estep"]]
    bins = [0.0, 2.0, 4.0, 7.0, 10.0, 14.0]
    Ls = [torch.zeros((3, h, w), device=DEV) for _ in bins]
    Tau, Hot = 0.0, 0.0
    W_ = 0.0
    for k in ks:
        S = soften(torch.from_numpy(np.load(os.path.join(d, f"S{i:03d}_{k}.npy"))).to(DEV).float())
        T = soften(torch.from_numpy(np.load(os.path.join(d, f"T{i:03d}_{k}.npy"))).to(DEV).float())
        L, tau, hot = expose(S, T, dirs, dy, ys, lk, w, bins)
        for a, b in zip(Ls, L):
            a += b / len(ks)
        Tau = Tau + tau / len(ks)
        Hot = Hot + hot / len(ks)
        if plate is not None:
            W_ = W_ + light_weights(S, T, lk, ys, zs, xs) / len(ks)
    ep = [np.load(os.path.join(d, f"E{i:03d}_{k}.npy")) for k in es]
    im = blur_bins(Ls, bins, ep, w, h, lk)
    if plate is None:
        return im, W_
    # the plate behind the fire, through the hot air: index of refraction goes as density, so as 1/T. The gain is an estimate, raised by eye above the physical amount
    H = cv2.GaussianBlur(Hot.cpu().numpy(), (0, 0), 3.5 * w / 1920.0)
    gx, gy = cv2.Sobel(H, cv2.CV_32F, 1, 0, ksize=3) / 8.0, cv2.Sobel(H, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    Yp, Xp = np.mgrid[0:h, 0:w].astype(np.float32)
    amt = lk["shimmer"] * w / 1920.0
    if ema is not None:  # firelight on the wall breathes; it must not flash
        ema["w"] = W_ if ema.get("w") is None else 0.72 * ema["w"] + 0.28 * W_
        W_ = ema["w"]
    flick = 1.0 + lk["flick"] * (float(np.sum(W_)) / lk["W_ref"] - 1.0)
    pl = plate.lit(W_ / lk["W_ref"] * np.ones(len(W_)), flick, lk)
    pl = cv2.remap(pl, Xp + amt * gx, Yp + amt * gy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if stats is not None:
        stats.append(W_)
    return im + pl * Tau.cpu().numpy()[..., None], W_


def develop_frame(L, lk, seed):
    from darkroom import develop

    dev = {k: lk[k] for k in ("contrast", "saturation", "black", "grain", "sharpen", "halation", "glare", "vignette", "ca", "wb")}
    return develop((L * lk["K"] + 0.0007).astype(np.float32), seed=seed, **dev)


def look(name, frames, over):
    import cv2

    from darkroom import print_look

    lk = {**LOOK, **over}
    w = lk["w"]
    h = w * 9 // 16
    tag = lk.get("tag", "a")
    d = os.path.join(OUT, "s42_sim", name, "look")
    os.makedirs(d, exist_ok=True)
    plate = Plate(w, h) if lk.get("plate", True) else None
    for i in frames:
        t = time.time()
        L, W_ = frame_linear(name, i, lk, w, h, plate)
        x = print_look(develop_frame(L, lk, 4200 + i))
        p = os.path.join(d, f"{tag}_{i:03d}.jpg")
        cv2.imwrite(p, (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(p, f"p50 {np.median(L):.3f} p99 {np.percentile(L, 99):.3f} max {L.max():.2f} W {np.sum(W_):.1f}; {time.time()-t:.1f} s", flush=True)


def take(name, outdir, n, over):
    from darkroom import save_png
    import cv2

    from darkroom import print_look

    lk = {**LOOK, **over}
    w = lk["w"]
    h = w * 9 // 16
    os.makedirs(outdir, exist_ok=True)
    plate = Plate(w, h)
    t0 = time.time()
    ema = {}
    for i in range(n):
        L, W_ = frame_linear(name, i, lk, w, h, plate, ema=ema)
        x = develop_frame(L, lk, 4200 + i)
        save_png(os.path.join(outdir, f"f{i:03d}.png"), x)
        y = print_look(x)
        cv2.imwrite(os.path.join(outdir, f"v{i:03d}.jpg"), (np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(i, f"max {L.max():.1f} W {np.sum(W_):.1f} {time.time()-t0:.0f} s", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    with torch.no_grad():
        if cmd == "sim":
            sim(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
        else:
            a = sys.argv[3:]
            over = json.loads(a[a.index("--") + 1]) if "--" in a else {}
            pos = a[: a.index("--")] if "--" in a else a
            if cmd == "look":
                look(sys.argv[2], [int(x) for x in pos], over)
            elif cmd == "take":
                take(sys.argv[2], pos[0], int(pos[1]), over)
