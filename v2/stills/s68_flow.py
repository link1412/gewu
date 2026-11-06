"""Shot 68, the flow: concentrated tea sinking in still hot water. 3D incompressible Boussinesq flow, pseudo-spectral in a free-slip box, with the tea carried by particles.

    python3 v2/stills/s68_flow.py NAME '{json params}'       out/v2/s68_sim/NAME/: params, previews, particle positions at the times in `save`

The mechanism:
- velocity: sine/cosine series for free-slip on all six walls (no periodic images), rotational form, SSP-RK3, 2/3 dealiasing, exact viscosity by integrating factor;
- buoyancy: the tea's density comes from the `dyn` particles deposited on the grid each step. There is no grid scalar, so no numerical diffusion of tea and no spectral ringing;
- render particles are passive, advected in the same field on a spectrally doubled grid every `K` steps (Heun). Diffusion is done at the compositor, from each particle's age, so the picture has no shimmer. D_eff is a choice, far above molecular (see s68_tea);
- no turbulence is added. The symmetry breaks through the drops' lopsided shapes and each other's wakes.

Numbers, estimates from general knowledge unless a comment says otherwise: nu 0.004 cm2/s (about 80 C); g' per unit concentration = 981 * drho/rho.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import torch
import torch.nn.functional as TF

import s68_comp as C
import s68_geom as G

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2")
DEV = C.DEV

SIM = dict(
    dx=0.06, x0=-3.6, x1=3.6, y0=0.6, y1=4.6, z0=-4.6, z1=0.0,
    nu=0.004, D_eff=1.2e-4, g1=0.15, dt=0.03, cfl=0.9, T=10.0, seed=68,
    n_dyn=3_000_000, n_pass=10_000_000, K=3, up=2,
    preview_every=0.5, preview_w=640, K_abs=20.0,
    save=[],
    # x, y, depth of the centre, t0, r, kick (cm/s), share born as a trailing thread, thread duration s, thread radius
    drops=[
        dict(x=0.35, y=3.35, d=0.28, t0=0.0, r=0.26, kick=1.5, tail=0.18, tail_T=3.0, tail_r=0.05),
        dict(x=-0.85, y=3.0, d=0.24, t0=1.2, r=0.22, kick=1.5, tail=0.18, tail_T=3.0, tail_r=0.04),
        dict(x=1.05, y=3.55, d=0.20, t0=2.4, r=0.18, kick=1.5, tail=0.18, tail_T=2.5, tail_r=0.035),
    ],
)


# --- sine and cosine transforms, by one complex FFT of the same length along each axis (Makhoul) -------------------
def _tw(N, dev):
    k = torch.arange(N, device=dev, dtype=torch.float32)
    return torch.polar(torch.ones_like(k), -np.pi * k / (2 * N))


class Tr:
    """dims (z, y, x); kinds per dim: 'c' or 's'. Coefficients on index m = 0..N-1; the sine's m = 0 slot holds its Nyquist mode, which the dealiasing removes."""

    def __init__(self, shape):
        self.shape = shape
        self.tw = [_tw(n, DEV) for n in shape]
        self.perm = []
        self.iperm = []
        for n in shape:
            p = torch.cat([torch.arange(0, n, 2), torch.arange(n - 1 - (n % 2 == 1), 0, -2)]).to(DEV)
            q = torch.empty_like(p)
            q[p] = torch.arange(n, device=DEV)
            self.perm.append(p)
            self.iperm.append(q)
        self.alt = [(1.0 - 2.0 * (torch.arange(n, device=DEV) % 2)).float() for n in shape]

    def _sh(self, d):
        s = [1, 1, 1]
        s[d] = -1
        return s

    def f1(self, x, d, kind):
        n = self.shape[d]
        if kind == "s":
            x = x * self.alt[d].view(self._sh(d))
        v = torch.index_select(x, d, self.perm[d])
        V = torch.fft.fft(v, dim=d)
        X = (V * self.tw[d].view(self._sh(d))).real
        if kind == "s":
            X = torch.roll(torch.flip(X, [d]), 1, d)
        return X

    def i1(self, X, d, kind):
        n = self.shape[d]
        if kind == "s":
            X = torch.flip(torch.roll(X, -1, d), [d])
        # X[N - k] with X[N] = 0
        Xr = torch.roll(torch.flip(X, [d]), 1, d)
        idx = [slice(None)] * 3
        idx[d] = 0
        Xr[tuple(idx)] = 0.0
        V = torch.complex(X, -Xr) * torch.conj(self.tw[d]).view(self._sh(d))
        v = torch.fft.ifft(V, dim=d).real
        x = torch.index_select(v, d, self.iperm[d])
        if kind == "s":
            x = x * self.alt[d].view(self._sh(d))
        return x

    def fwd(self, x, kinds):
        for d, k in enumerate(kinds):
            x = self.f1(x, d, k)
        return x

    def inv(self, X, kinds):
        for d, k in reversed(list(enumerate(kinds))):
            X = self.i1(X, d, k)
        return X


# kinds in (z, y, x)
KU, KV, KW = "ccs", "csc", "scc"  # u = sin(x) cos(y) cos(z), v = cos(x) sin(y) cos(z), w = cos(x) cos(y) sin(z)
KOX, KOY, KOZ = "ssc", "scs", "css"  # wx = cos sin sin, wy = sin cos sin, wz = sin sin cos


def sheet_field(d):
    """A spoonful laid on the water and spreading: thickness (cm) of the tea layer under the surface, on a 2-D grid. An irregular patch: its outline and thickness vary slowly, nothing finer than `lo` cm. This is an initial condition, chosen for the picture; the solver then does the rest (the layer is heavier than the water below, so it breaks up by Rayleigh-Taylor)."""
    import kit

    px = 80.0
    x = np.arange(d["cx"] - d["ax"] - 0.5, d["cx"] + d["ax"] + 0.5, 1 / px)
    y = np.arange(d["cy"] - d["ay"] - 0.5, d["cy"] + d["ay"] + 0.5, 1 / px)
    X, Y = np.meshgrid(x, y)
    sd = d.get("seed", 3)
    out = kit.fbm(X.shape, px, 0.5, 3.0, 2.6, sd)
    q = np.hypot((X - d["cx"]) / d["ax"], (Y - d["cy"]) / d["ay"]) + 0.28 * out
    mask = kit.sstep(1.0, 0.72, q)
    f = kit.fbm(X.shape, px, d.get("lo", 0.2), 2.5, 2.4, sd + 1)
    h = d["h"] * mask * np.exp(d.get("hvar", 0.45) * f)
    h *= kit.sstep(0.0, 0.2, G.inner_radius(0.0) - np.hypot(X, Y))  # the wall
    return x, y, h.astype(np.float32), px


def source_volume(d):
    if d.get("sheet"):
        _, _, h, px = sheet_field(d)
        return float(h.sum()) / px**2
    return 4 / 3 * np.pi * d["r"] ** 3


def sheet_particles(d, n, rng):
    x, y, h, px = sheet_field(d)
    p = h.ravel().astype(np.float64)
    c = np.cumsum(p)
    c /= c[-1]
    i = np.searchsorted(c, rng.random(n))
    iy, ix = np.unravel_index(i, h.shape)
    X = x[ix] + (rng.random(n) - 0.5) / px
    Y = y[iy] + (rng.random(n) - 0.5) / px
    Z = -0.004 - h[iy, ix] * rng.random(n)
    # the tea arrives from the pouring point outward, so the older part is further along
    b = d["t0"] + np.hypot(X - d["px"], Y - d["py"]) / d["v"]
    return np.stack([X, Y, Z], -1).astype(np.float32), b.astype(np.float32)


def expand_seeps(drops):
    """A patch where tea seeps out: many small steady seeps of unequal strength, so it leaves many threads, some strong, most faint. Physically the leaf or the small lump of strong tea just under the surface; the source itself is not drawn."""
    out = []
    for d in drops:
        if not d.get("seeps"):
            out.append(d)
            continue
        r = np.random.default_rng(d["seed"])
        w = r.lognormal(0.0, d.get("spread", 0.8), d["seeps"])
        w = w / w.mean()
        for i in range(d["seeps"]):
            x, y = d["x"] + r.normal() * d["sx"], d["y"] + r.normal() * d["sy"]
            q = G.inner_radius(0.0) - 0.08
            if np.hypot(x, y) > q:
                x, y = x * q / np.hypot(x, y), y * q / np.hypot(x, y)
            out.append(dict(x=float(x), y=float(y), d=0.05, r=float(d["r"] * w[i] ** (1 / 3)), kick=0.0, tail=1.0, tail_pow=0.5,
                            t0=float(d["t0"] + r.uniform(0, d.get("t_spread", 3.0))), tail_T=float(d["tail_T"] * r.uniform(0.6, 1.0)),
                            tail_r=float(d["tail_r"] * r.uniform(0.6, 1.4)), conc=d.get("conc", 1.0), age0=d.get("age0", 0.0)))
    return out


def source_particles(drops, n_total, rng, shape_seed):
    """Lopsided blobs plus a thread born over time at the entry point. Sorted by birth, so the living ones are a prefix. Their volumes are in proportion to r^3."""
    vols = np.array([source_volume(d) * d.get("conc", 1.0) for d in drops])  # every particle carries the same amount of tea: a weak source has fewer
    counts = (vols / vols.sum() * n_total).astype(np.int64)
    P, B, K, A = [], [], [], []
    shp = np.random.default_rng(shape_seed)  # both populations fill the same lopsided shapes
    for d, n in zip(drops, counts):
        if d.get("sheet"):
            p, b = sheet_particles(d, n, rng)
            P.append(p)
            B.append(b)
            K.append(np.zeros(n, np.float32))
            A.append(np.full(n, d.get("age0", 0.0), np.float32))
            continue
        nt = int(n * d["tail"])
        nb = n - nt
        # shape: the sphere pushed by smooth lobes, each drop its own
        m = shp.normal(size=(6, 3))
        m /= np.linalg.norm(m, axis=1, keepdims=True)
        a = shp.uniform(-0.28, 0.28, 6)
        dirs = rng.normal(size=(nb, 3)).astype(np.float32)
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        lob = (np.exp(2.5 * (dirs @ m.T.astype(np.float32)) - 2.5) @ a.astype(np.float32))
        r = d["r"] * (1 + lob) * rng.random(nb, dtype=np.float32) ** (1 / 3)
        p = dirs * r[:, None] * np.array([1.0, 1.0, 0.85], np.float32) + np.array([d["x"], d["y"], -d["d"]], np.float32)
        p[:, 2] = np.minimum(p[:, 2], -0.004)
        b = np.full(nb, d["t0"], np.float32)
        # the thread
        tt = rng.random(nt, dtype=np.float32)
        tb = d["t0"] + 0.2 + d["tail_T"] * tt ** d.get("tail_pow", 1.0)
        th = rng.random(nt, dtype=np.float32) * 2 * np.pi
        rr = d["tail_r"] * np.sqrt(rng.random(nt, dtype=np.float32))
        pt = np.stack([d["x"] + rr * np.cos(th), d["y"] + rr * np.sin(th), -0.02 - d.get("tail_d", 0.08) * rng.random(nt, dtype=np.float32)], -1)
        P += [p, pt.astype(np.float32)]
        B += [b, tb.astype(np.float32)]
        K += [np.full(nb, d["kick"], np.float32), np.zeros(nt, np.float32)]
        A += [np.full(n, d.get("age0", 0.0), np.float32)]
    P, B, K, A = np.concatenate(P), np.concatenate(B), np.concatenate(K), np.concatenate(A)
    o = np.argsort(B, kind="stable")
    return P[o], B[o], K[o], A[o]


class Flow:
    def __init__(self, S):
        self.S = S
        dx = S["dx"]
        self.Lx, self.Ly, self.Lz = S["x1"] - S["x0"], S["y1"] - S["y0"], S["z1"] - S["z0"]
        self.n = [int(round(self.Lz / dx)), int(round(self.Ly / dx)), int(round(self.Lx / dx))]  # z, y, x; cell size is nearly dx in all three
        self.lo = torch.tensor([S["x0"], S["y0"], S["z0"]], device=DEV, dtype=torch.float32)
        self.L = torch.tensor([self.Lx, self.Ly, self.Lz], device=DEV, dtype=torch.float32)
        self.cell = self.L / torch.tensor(self.n[::-1], device=DEV, dtype=torch.float32)
        nz, ny, nx = self.n
        self.tr = Tr(tuple(self.n))
        mk = lambda n, L: np.pi / L * torch.arange(n, device=DEV, dtype=torch.float32)
        self.kz = mk(nz, self.Lz).view(-1, 1, 1)
        self.ky = mk(ny, self.Ly).view(1, -1, 1)
        self.kx = mk(nx, self.Lx).view(1, 1, -1)
        K2 = self.kx**2 + self.ky**2 + self.kz**2
        K2[0, 0, 0] = 1.0
        self.K2 = K2
        mask = lambda n: (torch.arange(n, device=DEV) < int(n * 2 / 3)).float()
        self.deal = mask(nz).view(-1, 1, 1) * mask(ny).view(1, -1, 1) * mask(nx).view(1, 1, -1)
        self.U = torch.zeros((3, nz, ny, nx), device=DEV)  # coefficients
        # the top of the resolved band is damped: at this low viscosity the deposit's grid noise otherwise grows into velocity at the grid scale, and particles collect in regular stripes. Velocity scales above about 4 cells are untouched
        km = (2.0 / 3.0) * (self.kx[0, 0, -1] ** 2 + self.ky[0, -1, 0] ** 2 + self.kz[-1, 0, 0] ** 2) ** 0.5
        self.filt = torch.exp(-8.0 * (K2.sqrt() / km) ** 8)
        self.lowF = torch.exp(-0.5 * K2 * (1.5 * self.cell.min()) ** 2)  # the buoyancy is smoothed over 1.5 cells before it acts
        if S["up"] > 1:
            f = S["up"]
            self.tr2 = Tr((nz * f, ny * f, nx * f))

    def project(self, U):
        phi = (self.kx * U[0] + self.ky * U[1] + self.kz * U[2]) / self.K2
        return torch.stack([(U[0] - self.kx * phi) * self.deal, (U[1] - self.ky * phi) * self.deal, (U[2] - self.kz * phi) * self.deal])

    def rhs(self, U, Fz):
        tr = self.tr
        ux, uy, uz = tr.inv(U[0], KU), tr.inv(U[1], KV), tr.inv(U[2], KW)
        ox = tr.inv(self.kz * U[1] - self.ky * U[2], KOX)
        oy = tr.inv(self.kx * U[2] - self.kz * U[0], KOY)
        oz = tr.inv(self.ky * U[0] - self.kx * U[1], KOZ)
        Nx = tr.fwd(uy * oz - uz * oy, KU)
        Ny = tr.fwd(uz * ox - ux * oz, KV)
        Nz = tr.fwd(ux * oy - uy * ox, KW) + Fz
        return self.project(torch.stack([Nx, Ny, Nz]))

    def step(self, Fz, dt):
        vis = torch.exp(-self.S["nu"] * self.K2 * dt * 0.5)
        U = self.U * vis
        a = U + dt * self.rhs(U, Fz)
        b = 0.75 * U + 0.25 * (a + dt * self.rhs(a, Fz))
        U = (U + 2.0 * (b + dt * self.rhs(b, Fz))) / 3.0
        self.U = U * vis * self.filt

    def grid(self):
        tr = self.tr
        return torch.stack([tr.inv(self.U[0], KU), tr.inv(self.U[1], KV), tr.inv(self.U[2], KW)])

    def grid_fine(self):
        """The same field, sampled on a grid f times finer by padding the series: it keeps the velocity's own smoothness, so particles do not gather on the coarse cells as they do with a plain trilinear field."""
        f = self.S["up"]
        if f <= 1:
            return self.grid()
        nz, ny, nx = self.n
        out = []
        for i, k in enumerate((KU, KV, KW)):
            X = torch.zeros((nz * f, ny * f, nx * f), device=DEV)
            X[:nz, :ny, :nx] = self.U[i] * (f**3)
            out.append(self.tr2.inv(X, k))
        return torch.stack(out)

    def deposit(self, P):
        """CIC, in cell units; returns particle counts per cell (z, y, x)."""
        nz, ny, nx = self.n
        q = (P - self.lo) / self.cell - 0.5
        i = q.floor().long()
        f = q - i
        out = torch.zeros(nz * ny * nx, device=DEV)
        for dz in (0, 1):
            for dy in (0, 1):
                for dx in (0, 1):
                    wt = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                    ix = (i[:, 0] + dx).clamp(0, nx - 1)
                    iy = (i[:, 1] + dy).clamp(0, ny - 1)
                    iz = (i[:, 2] + dz).clamp(0, nz - 1)
                    out.index_add_(0, (iz * ny + iy) * nx + ix, wt)
        return out.view(nz, ny, nx)

    def sample(self, G_, P, chunk=8_000_000):
        out = []
        for a in range(0, len(P), chunk):
            p = P[a : a + chunk]
            g = ((p - self.lo) / self.L * 2 - 1)[None, None, None]
            v = TF.grid_sample(G_[None], g, mode="bilinear", padding_mode="border", align_corners=False)[0, :, 0, 0, :].T
            out.append(v)
        return torch.cat(out)

    def keep_in(self, P):
        eps = 1e-3
        P[:, 0].clamp_(self.S["x0"] + eps, self.S["x1"] - eps)
        P[:, 1].clamp_(self.S["y0"] + eps, self.S["y1"] - eps)
        P[:, 2].clamp_(self.S["z0"] + eps, self.S["z1"] - eps)


def tea(view, pops, t, S, eps, wt):
    """pops: list of (positions, birth, age offset, mass per particle). Colour multiplier (3, h, w)."""
    N = None
    for P_, B_, A_, mass in pops:
        if len(P_) == 0:
            continue
        N, m = C.splat(view, P_, (t - B_) + A_, mass, S["D_eff"], N)
    if N is None:
        return torch.ones((3, view.h, view.w), device=DEV)
    return C.transmission(N, m, eps, wt, view.w)


def preview(path, Tr_, bg):
    img = bg[:3] * Tr_ + bg[3:]
    x = img.permute(1, 2, 0).cpu().numpy()
    x = np.clip(x, 0, 1) ** (1 / 2.2)
    cv2.imwrite(path, (x * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
    return x


def run(name, over):
    S = {**SIM, **over}
    if DEV == "cuda":
        torch.cuda.set_per_process_memory_fraction(S.get("mem_frac", 0.55))  # 18 GB at most: Blender keeps the rest
    d = os.path.join(OUT, "s68_sim", name)
    os.makedirs(d, exist_ok=True)
    t0 = time.time()
    S["drops"] = expand_seeps(S["drops"])
    Pd, Bd, Kd, Ad = source_particles(S["drops"], S["n_dyn"], np.random.default_rng(S["seed"]), S["seed"] + 7)
    Pp, Bp, Kp, Ap = source_particles(S["drops"], S["n_pass"], np.random.default_rng(S["seed"] + 1), S["seed"] + 7)
    print(f"[init] {S['n_dyn']/1e6:.1f} M + {S['n_pass']/1e6:.1f} M particles, {time.time()-t0:.0f} s", flush=True)
    F = Flow(S)
    nz, ny, nx = F.n
    if S.get("stir"):
        st = S["stir"]  # what is left of the pouring: a slow large-scale drift that bends the threads; a choice, its size set by eye
        g = torch.Generator(device=DEV).manual_seed(st["seed"])
        k = torch.sqrt(F.K2)
        band = torch.exp(-0.5 * (torch.log(k.clamp(min=1e-3) / (2 * np.pi / st["lam"])) / st.get("width", 0.5)) ** 2)
        F.U = F.project(torch.randn((3, nz, ny, nx), device=DEV, generator=g) * band)
        F.U *= st["rms"] / float(F.grid().std())
    print(f"[grid] {nx}x{ny}x{nz} = {nx*ny*nz/1e6:.2f} M cells, cell {[round(float(c),4) for c in F.cell]} cm, device {DEV}", flush=True)
    Pd_, Pp_ = torch.from_numpy(Pd).to(DEV), torch.from_numpy(Pp).to(DEV)
    Bd_, Bp_ = torch.from_numpy(Bd).to(DEV), torch.from_numpy(Bp).to(DEV)
    Ad_, Ap_ = torch.from_numpy(Ad).to(DEV), torch.from_numpy(Ap).to(DEV)
    Kd_ = torch.from_numpy(Kd).to(DEV)
    tot = sum(source_volume(dr) * dr.get("conc", 1.0) for dr in S["drops"])
    cell_v = float(F.cell.prod())
    mass_dyn = tot / S["n_dyn"] / cell_v  # concentration per particle per cell: 1 inside undiluted tea
    m_all = tot / (S["n_dyn"] + S["n_pass"])
    S["mass_px"] = m_all
    json.dump(S, open(os.path.join(d, "params.json"), "w"), indent=1)
    import s68_tea

    lams, eps_ = s68_tea.bands()
    eps = eps_ * S["K_abs"]
    wt = G.band_weights(lams)
    view = C.View(S["preview_w"], S["preview_w"] * 9 // 16)
    bg = preview_bg(view)
    take = S.get("take")
    if take:
        vt = C.View(take["w"], take["w"] * 9 // 16)
        dt_ = os.path.join(OUT, "s68_chase_tr", name)
        os.makedirs(dt_, exist_ok=True)
        ftimes = [take["t0"] + i * take["step"] for i in range(take["n"])]
    else:
        ftimes = []
    pool = ThreadPoolExecutor(2)
    next_prev = 0.0
    saves = sorted(S["save"])
    t, it, alive_d, alive_p = 0.0, 0, 0, 0
    Gp_old, tp_old, refresh = None, 0.0, True
    vid = []
    t0 = time.time()
    rw = np.sqrt(2 * S["D_eff"])
    while t < S["T"] - 1e-9:
        n_d = int(np.searchsorted(Bd, t, side="right"))
        if n_d > alive_d:
            new, kick = Pd_[alive_d:n_d], Kd_[alive_d:n_d]
            if float(kick.max()) > 0:
                k = F.deposit(new[kick > 0]) * mass_dyn * float(kick.max())
                F.U = F.project(F.U + torch.stack([torch.zeros_like(k), torch.zeros_like(k), F.tr.fwd(-k, KW)]))
            alive_d = n_d
        c = F.deposit(Pd_[:alive_d]) * mass_dyn if alive_d else torch.zeros(F.n, device=DEV)
        Fz = F.tr.fwd(-S["g1"] * c, KW) * F.lowF
        U_g = F.grid()
        umax = float(U_g.abs().max())
        dt = min(S["dt"], S["cfl"] * float(F.cell.min()) / max(umax, 1e-3))
        marks = [x for x in ftimes + saves + [next_prev] if x > t + 1e-9]
        if marks and min(marks) - t < dt * 1.5:
            dt = min(marks) - t  # frames land exactly on their times, or the motion would judder
        if refresh:
            Gp_old, tp_old = F.grid_fine(), t
            n_p = int(np.searchsorted(Bp, t, side="right"))
            if n_p > alive_p:
                # those born since the last update start from where they would be by now, or each update's batch shows as a stripe across the thread
                q = Pp_[alive_p:n_p]
                q += (t - Bp_[alive_p:n_p])[:, None] * F.sample(Gp_old, q)
                F.keep_in(q)
            alive_p = n_p
            refresh = False
        F.step(Fz, dt)
        U_new = F.grid()
        if alive_d:
            p = Pd_[:alive_d]
            v0 = F.sample(U_g, p)
            v1 = F.sample(U_new, p + dt * v0)
            p += 0.5 * dt * (v0 + v1) + torch.randn_like(p) * float(rw * np.sqrt(dt))  # the part of the tea that drives the flow diffuses too; only here, where it does not show
            F.keep_in(p)
        t += dt
        it += 1
        due_frame = any(abs(x - t) < 1e-6 for x in ftimes)
        due_save = any(abs(x - t) < 1e-6 for x in saves)
        due_prev = t >= next_prev - 1e-6
        if it % S["K"] == 0 or due_frame or due_save or due_prev or t >= S["T"] - 1e-9:
            Gn = F.grid_fine()
            h = t - tp_old
            for a in range(0, alive_p, 8_000_000):
                q = Pp_[a : min(a + 8_000_000, alive_p)]
                v0 = F.sample(Gp_old, q)
                v1 = F.sample(Gn, q + h * v0)
                q += 0.5 * h * (v0 + v1)
                F.keep_in(q)
            refresh = True
            pops = [(Pd_[:alive_d], Bd_[:alive_d], Ad_[:alive_d], m_all), (Pp_[:alive_p], Bp_[:alive_p], Ap_[:alive_p], m_all)]
            if due_prev:
                Tr_ = tea(view, [(Pd_[:alive_d], Bd_[:alive_d], Ad_[:alive_d], tot / S["n_dyn"])], t, S, eps, wt)
                x = preview(os.path.join(d, f"p{int(round(t*100)):05d}.jpg"), Tr_, bg)
                vid.append((x * 255 + 0.5).astype(np.uint8)[..., ::-1])
                next_prev += S["preview_every"]
            if due_frame:
                i = next(j for j, x in enumerate(ftimes) if abs(x - t) < 1e-6)
                tr = tea(vt, pops, t, S, eps, wt).permute(1, 2, 0).cpu().numpy().astype(np.float16)
                pool.submit(np.save, os.path.join(dt_, f"t{i:03d}.npy"), tr)
                if i % 12 == 0:
                    print(f"[frame {i}] t={t:.3f} {time.time()-t0:.0f} s; min transmission RGB {tr.min((0,1)).astype(float).round(3).tolist()}", flush=True)
            if due_save:
                np.save(os.path.join(d, f"pos_{t:06.3f}.npy"), np.concatenate([Pd_[:alive_d].cpu().numpy(), Pp_[:alive_p].cpu().numpy()]))
                np.save(os.path.join(d, f"age_{t:06.3f}.npy"), np.concatenate([(t - Bd_[:alive_d] + Ad_[:alive_d]).cpu().numpy(), (t - Bp_[:alive_p] + Ap_[:alive_p]).cpu().numpy()]))
                print(f"[save] t={t:.3f}", flush=True)
        if it % 50 == 0:
            mem = torch.cuda.max_memory_reserved() / 2**30 if DEV == "cuda" else 0
            print(f"[{it}] t={t:.2f} dt={dt:.4f} umax {umax:.2f} cm/s, CFL {umax*dt/float(F.cell.min()):.2f}, cmax {float(c.max()):.2f}, {(time.time()-t0)/it:.2f} s/step, alive {alive_d/1e6:.1f}+{alive_p/1e6:.1f} M, reserved peak {mem:.1f} GB", flush=True)
    pool.shutdown(wait=True)
    if vid:
        wr = cv2.VideoWriter(os.path.join(d, "preview_raw.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 8, (vid[0].shape[1], vid[0].shape[0]))
        for v in vid:
            wr.write(v)
        wr.release()
    print(f"[done] {it} steps, {time.time()-t0:.0f} s; {nx}x{ny}x{nz}; reserved peak {torch.cuda.max_memory_reserved()/2**30 if DEV=='cuda' else 0:.1f} GB", flush=True)


def preview_bg(view):
    """(6, h, w): T then R for previews before a plate exists, or the plate shrunk if one does."""
    w, h = view.w, view.h
    d = os.path.join(OUT, "s68_chase")
    T_ = os.path.join(d, "plate_T.linear.npy")
    if os.path.exists(T_):
        T = cv2.resize(np.load(T_).astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
        R = cv2.resize(np.load(os.path.join(d, "plate_R.linear.npy")).astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
    else:
        # a plain card: bright below the still water's line at the wall
        cam = G.camera()
        r, u, b = G.axes(cam)
        ang = np.linspace(-0.6, 0.6, w)
        pts = np.stack([G.R0 * np.sin(ang), G.R0 * np.cos(ang), np.zeros(w)], -1)
        e = pts - np.array(cam["loc"])
        zc = -(e @ b)
        fpx = w * cam["lens_mm"] / 36.0
        uu = (e @ r) / zc * fpx + w / 2
        vv = -(e @ u) / zc * fpx + h / 2
        line = np.interp(np.arange(w) + 0.5, uu, vv)
        Y = np.arange(h)[:, None] + 0.5
        m = (Y > line[None]).astype(np.float32)
        T = np.dstack([m * 0.9, m * 0.85, m * 0.78])
        R = np.zeros_like(T) + 0.004
    x = np.concatenate([T, R], -1).transpose(2, 0, 1)
    return torch.from_numpy(x.astype(np.float32)).to(DEV)


def test():
    """Transforms invert, curl and divergence agree with an analytic mode; energy decays at the viscous rate in a single mode."""
    S = {**SIM, "dx": 0.1, "up": 1}
    F = Flow(S)
    tr = F.tr
    a = torch.randn(tuple(F.n), device=DEV)
    for k in (KU, KV, KW, KOX, KOY, KOZ):
        b = tr.inv(tr.fwd(a, k), k)
        print(k, "roundtrip error", float((a - b).abs().max()))
    nz, ny, nx = F.n
    x = (torch.arange(nx, device=DEV) + 0.5) * float(F.cell[0])
    y = (torch.arange(ny, device=DEV) + 0.5) * float(F.cell[1])
    z = (torch.arange(nz, device=DEV) + 0.5) * float(F.cell[2])
    Z, Y, X = torch.meshgrid(z, y, x, indexing="ij")
    kx, ky, kz = 3 * np.pi / F.Lx, 2 * np.pi / F.Ly, 4 * np.pi / F.Lz
    # a divergence-free mode: u = A sin cos cos, v = B cos sin cos, w = C cos cos sin with kx A + ky B + kz C = 0
    A, B = 1.0, -0.5
    Cc = -(kx * A + ky * B) / kz
    u = A * torch.sin(kx * X) * torch.cos(ky * Y) * torch.cos(kz * Z)
    v = B * torch.cos(kx * X) * torch.sin(ky * Y) * torch.cos(kz * Z)
    w = Cc * torch.cos(kx * X) * torch.cos(ky * Y) * torch.sin(kz * Z)
    U = torch.stack([tr.fwd(u, KU), tr.fwd(v, KV), tr.fwd(w, KW)])
    print("mode: nonzero at", [int(i) for i in (U[0].abs() > 1).nonzero()[0]], "expected (z,y,x)", (4, 2, 3))
    print("projection leaves it:", float((F.project(U) - U * F.deal).abs().max()) / float(U.abs().max()))
    ox = tr.inv(F.kz * U[1] - F.ky * U[2], KOX)
    an = (-ky * Cc + kz * B) * torch.cos(kx * X) * torch.sin(ky * Y) * torch.sin(kz * Z)
    print("curl x error:", float((ox - an).abs().max()) / float(an.abs().max()))
    # a non-solenoidal field loses its gradient part
    g = torch.stack([tr.fwd(a * 0 + torch.sin(kx * X) * torch.cos(ky * Y) * torch.cos(kz * Z), KU), tr.fwd(0 * a, KV), tr.fwd(0 * a, KW)])
    p = F.project(g)
    print("divergence after projection:", float((F.kx * p[0] + F.ky * p[1] + F.kz * p[2]).abs().max()))
    F.U = U.clone()
    e0 = float((F.U**2).sum())
    for _ in range(5):
        F.step(torch.zeros_like(U[0]), 0.02)
    e1 = float((F.U**2).sum())
    k2 = kx**2 + ky**2 + kz**2
    print("decay measured", e1 / e0, "viscous", np.exp(-2 * 0.004 * k2 * 0.1), "(a single mode has a nonlinear term, so close, not equal)")
    q = F.grid()
    print("grid u error:", float((q[0] - u).abs().max()), "after decay, for scale")
    if S["up"] == 1:
        S2 = {**S, "up": 2}
        F2 = Flow(S2)
        F2.U = U.clone()
        fine = F2.grid_fine()
        i = (nz, ny, nx)
        Xf = (torch.arange(nx * 2, device=DEV) + 0.5) * float(F.cell[0]) / 2
        Yf = (torch.arange(ny * 2, device=DEV) + 0.5) * float(F.cell[1]) / 2
        Zf = (torch.arange(nz * 2, device=DEV) + 0.5) * float(F.cell[2]) / 2
        Zg, Yg, Xg = torch.meshgrid(Zf, Yf, Xf, indexing="ij")
        uf = A * torch.sin(kx * Xg) * torch.cos(ky * Yg) * torch.cos(kz * Zg)
        print("fine grid error:", float((fine[0] - uf).abs().max()))


if __name__ == "__main__":
    with torch.no_grad():
        if sys.argv[1] == "test":
            test()
        else:
            run(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
