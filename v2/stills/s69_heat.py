"""Shot 69 (charcoal): the temperature is solved, not painted. A surface energy balance on a coarse mesh of every piece, on the GPU.

Two temperatures per surface element. T: the burning char, under a film (ash, or the unburnt black skin). T_f: the film's outer face, which is what the camera sees. Per unit area:
    m dT/dt = q_ox - C (T - T_f) + conduction          the char
    C (T - T_f) = eps (sigma T_f^4 - G) + h (T_f - T_gas)    the film, thin enough to be in balance at every instant
    C = k_ash / thickness
- G: irradiation from what the element sees. K cosine-weighted rays per element are traced once through an occupancy grid; each hit is an element, or the outside (a cold room above, the bed of coals below). G is then the mean radiosity over those K rays, so a matrix-vector product per step.
- Why two temperatures: this is the picture. A face looking at a cold room loses much, the film has a large drop across it, the face is dim and the cracks in it (which show the char itself) are bright: the bright web on a dark red flank. A face looking at other hot faces loses nothing, T_f comes up to T: the cracks stop showing and the face is one smooth glow. Both are in ref/charcoal/charbon.jpg. They come out of the one equation.
- q_ox: char oxidation. Diffusion-limited when hot, kinetically limited when cold, so q = Q * access * (1 - b film) * gust / (1 + exp(E/R (1/T - 1/T_k))). That S-curve is bistable: a patch glows or goes out, and between them is a front, not a soft cloud. That a surface heat balance with a measured reaction rate predicts steady char temperature, and that air speed intensifies the glow and strips ash above about 1.6 m/s, are from a search summary about wood char in a cone calorimeter (univ-lille), not read in full.
- Conduction along the skin: k delta laplacian(T) on the mesh's edges.

ESTIMATES, from general knowledge, not measured: rho 0.3 g/cm3, c 1.2 J/g K, delta 0.05 cm, k_char 1.5e-3 W/cm K, k_ash 5e-4 W/cm K, the black skin 30-430 um, Q, E/R, T_k, h, bed temperature. A search summary gave a two-colour pyrometry average of about 931 C (1204 K) for firebrand surfaces (source not pinned down); T here tops out somewhat below that.
Units: W, cm, K.
"""

import os
import time

import numpy as np
import torch

from s69_crack import DEV

SIGMA = 5.670e-12  # W / cm2 K4


def cosine_dirs(n, K, seed):
    """Stratified cosine-weighted directions about the normals, each element's set turned at random. (N, K, 3)."""
    N = n.shape[0]
    g = torch.Generator(device="cpu").manual_seed(seed)
    side = int(np.ceil(np.sqrt(K)))
    uu, vv = torch.meshgrid(torch.arange(side), torch.arange(side), indexing="ij")
    uu, vv = uu.flatten()[:K].float(), vv.flatten()[:K].float()
    u = ((uu[None] + torch.rand(N, K, generator=g)) / side).to(DEV)
    v = ((vv[None] + torch.rand(N, K, generator=g)) / side).to(DEV)
    v = (v + torch.rand(N, 1, generator=g).to(DEV)) % 1.0
    r = torch.sqrt(u)
    ph = 2.0 * torch.pi * v
    x, y, z = r * torch.cos(ph), r * torch.sin(ph), torch.sqrt((1.0 - u).clamp(min=0.0))
    a = torch.where(n[:, 2:3].abs() < 0.9, torch.tensor([0.0, 0.0, 1.0], device=DEV)[None], torch.tensor([1.0, 0.0, 0.0], device=DEV)[None])
    t = torch.linalg.cross(n, a)
    t = t / (t.norm(dim=1, keepdim=True) + 1e-9)
    b = torch.linalg.cross(n, t)
    return x[..., None] * t[:, None] + y[..., None] * b[:, None] + z[..., None] * n[:, None]


def trace(P, n, occ, origin, h, K=48, seed=1, batch=40000, log=print):
    """occ: uint8 grid (Z, Y, X) of ints: 0 empty, else solid. Returns hit (N, K) int64: index of the voxel hit (flattened), -1 up and out (room), -2 down and out (bed)."""
    Z, Y, X = occ.shape
    N = P.shape[0]
    hit = torch.full((N, K), -1, dtype=torch.int32, device="cpu")
    orig = torch.tensor(origin, device=DEV, dtype=torch.float32)
    t0 = time.time()
    maxsteps = int(np.sqrt(X * X + Y * Y + Z * Z)) + 2
    for a in range(0, N, batch):
        Pb, nb = P[a : a + batch], n[a : a + batch]
        d = cosine_dirs(nb, K, seed + a).reshape(-1, 3)
        o = (Pb[:, None] + nb[:, None] * (1.6 * h)).expand(-1, K, -1).reshape(-1, 3)
        res = torch.full((d.shape[0],), -1, dtype=torch.int32, device=DEV)
        act = torch.arange(d.shape[0], device=DEV)
        pos = (o - orig) / h
        step = d * 0.7  # in voxels
        for it in range(maxsteps * 2):
            if len(act) == 0:
                break
            q = pos[act] + step[act] * it
            ix, iy, iz = q[:, 0].long(), q[:, 1].long(), q[:, 2].long()
            out = (ix < 0) | (iy < 0) | (iz < 0) | (ix >= X) | (iy >= Y) | (iz >= Z)
            if out.any():
                res[act[out]] = torch.where(d[act[out], 2] < -0.03, -2, -1).to(torch.int32)
            keep = ~out
            act, ix, iy, iz = act[keep], ix[keep], iy[keep], iz[keep]
            s = occ[iz, iy, ix] > 0
            if s.any():
                res[act[s]] = ((iz[s] * Y + iy[s]) * X + ix[s]).to(torch.int32)
            act = act[~s]
        hit[a : a + batch] = res.reshape(-1, K).cpu()
    log(f"traced {N} x {K} rays in {time.time() - t0:.1f} s; up {float((hit == -1).float().mean()):.3f}, down {float((hit == -2).float().mean()):.3f}")
    return hit


class Heat:
    def __init__(self, P, n, area, edges, hit_e, access, film, params, log=print):
        """P, n: (N, 3) tensors. hit_e: (N, K) element index or -1 (room), -2 (bed). edges: (M, 2) long. access, film: (N); film in 0..1."""
        self.N = P.shape[0]
        self.P, self.n, self.area = P, n, area
        self.edges = edges
        self.hit = hit_e.to(DEV)
        self.access = access
        self.p = params
        self.T = torch.full((self.N,), params.get("T_start", 1050.0), device=DEV)
        L = (P[edges[:, 0]] - P[edges[:, 1]]).norm(dim=1).clamp(min=1e-4)
        # k delta laplacian: sum over edges of (Tj - Ti) / L^2 is about 2 D laplacian, normalised per element below. Surface nets leave some very short edges: an explicit step is stable only below this limit
        self.cw = (1.0 / (L * L)).clamp(max=0.8 * params["mass"] / (4.0 * params["k_delta"] * 0.008))
        cnt = torch.zeros(self.N, device=DEV)
        cnt.index_add_(0, edges[:, 0], torch.ones(len(edges), device=DEV))
        cnt.index_add_(0, edges[:, 1], torch.ones(len(edges), device=DEV))
        self.cnt = cnt.clamp(min=1.0)
        self.Tg = torch.as_tensor(params["T_gas"], device=DEV, dtype=torch.float32)
        self.set_film(film)
        self.G = torch.zeros(self.N, device=DEV)
        self.Tf = self.T * 0.9
        self.J = self.eps * SIGMA * self.Tf**4

    def set_film(self, film):
        p = self.p
        self.film = film
        self.eps = 1.0 - (p["alb_char"] * (1.0 - film) + p["alb_ash"] * film)
        self.C = p["k_ash"] / (p["film0"] + p["film1"] * film)

    def smooth(self, f, n=2, a=0.5):
        """A few Jacobi passes over the mesh: K rays per element leave noise in G that the eye would read as blotches."""
        e0, e1 = self.edges[:, 0], self.edges[:, 1]
        for _ in range(n):
            acc = torch.zeros(self.N, device=DEV)
            acc.index_add_(0, e0, f[e1])
            acc.index_add_(0, e1, f[e0])
            f = (1.0 - a) * f + a * acc / self.cnt
        return f

    def irradiation(self):
        p = self.p
        mask_room = self.hit == -1
        mask_bed = self.hit == -2
        idx = self.hit.clamp(min=0)
        Jh = self.J[idx]
        Jh = torch.where(mask_room, torch.tensor(SIGMA * p["T_room"] ** 4, device=DEV), Jh)
        Jh = torch.where(mask_bed, torch.tensor(SIGMA * p["T_bed"] ** 4, device=DEV), Jh)
        self.G = self.smooth(Jh.mean(1))
        self.J = self.eps * SIGMA * self.Tf**4 + (1.0 - self.eps) * self.G

    def film_face(self):
        """T_f from the film's balance, by Newton from where it was."""
        p = self.p
        T, Tf = self.T, self.Tf
        for _ in range(3):
            g = self.C * (T - Tf) - self.eps * (SIGMA * Tf**4 - self.G) - p["h"] * (Tf - self.Tg)
            dg = -self.C - 4.0 * self.eps * SIGMA * Tf**3 - p["h"]
            Tf = (Tf - g / dg).clamp(300.0, 1800.0)
        self.Tf = Tf

    def step(self, dt, gust):
        p = self.p
        T = self.T
        self.film_face()
        arr = torch.exp((p["E_R"] * (1.0 / T - 1.0 / p["T_k"])).clamp(max=30.0))
        q = p["Q"] * self.access * (1.0 - p["ash_block"] * self.film) * gust / (1.0 + arr)
        out = self.C * (T - self.Tf)
        # conduction
        dT = T[self.edges[:, 1]] - T[self.edges[:, 0]]
        flow = self.cw * dT
        lap = torch.zeros(self.N, device=DEV)
        lap.index_add_(0, self.edges[:, 0], flow)
        lap.index_add_(0, self.edges[:, 1], -flow)
        cond = p["k_delta"] * lap * (4.0 / self.cnt)
        self.T = (T + dt * (q - out + cond) / p["mass"]).clamp(400.0, 1700.0)
        return float((q - out).abs().mean())

    def relax(self, seconds, dt, gust_fn, every=4, log=print, tag=""):
        t0 = time.time()
        n = int(seconds / dt)
        for i in range(n):
            if i % every == 0:
                self.irradiation()
            r = self.step(dt, gust_fn(i * dt))
            if i % max(1, n // 5) == 0 or i == n - 1:
                st = max(1, self.N // 200000)
                pct = torch.tensor([0.02, 0.25, 0.5, 0.75, 0.98], device=DEV)
                q, qf = torch.quantile(self.T[::st], pct), torch.quantile(self.Tf[::st], pct)
                log(f"  {tag} t {i * dt:6.2f}: T {[int(x) for x in q.cpu().numpy()]}, face {[int(x) for x in qf.cpu().numpy()]}, residual {r:.2f}; {time.time() - t0:.1f} s")


DEFAULT = dict(alb_char=0.05, alb_ash=0.06, T_room=330.0, T_bed=1040.0, Q=5.0, E_R=15000.0, T_k=790.0, ash_block=0.8, h=4e-3, T_gas=800.0, k_delta=1.5e-3 * 0.05, mass=0.3 * 1.2 * 0.05, T_start=1040.0, k_ash=5e-4, film0=0.003, film1=0.04)
