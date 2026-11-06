"""Shot 69 (charcoal): the cracks, grown instead of drawn. Variational phase-field fracture of a shrinking skin, on the GPU.

    python3 -I s69_crack.py test [dx] ['{"fine":{...}}']     writes out/v2/s69_mutan/crack_test.jpg
    (imported by s69_mutan.py)

The mechanism. A char skin shrinks on a core that shrinks less. It is a film on an elastic foundation: stress builds over a shear-lag length L = sqrt(E / k), a crack relieves it over that length, and the next crack can only form further away or turns to meet the first one. T junctions, spacing and generations are not put in by hand.
Fracture: gradient damage, the AT1 functional (Pham, Amor, Marigo, Maurini 2011; for shrinkage and thermal shock, Sicsic, Marigo, Maurini 2014 and Bourdin et al., PRL 2014; all known from memory, not re-read):
    E = int g(d) psi+(eps(u) - eps0) + psi- + k/2 |u|^2 + (3 Gc / 8) (d / l + l grad d . A grad d),  g = (1 - d)^2,  d only grows
A first attempt with a brittle spring lattice gave diffuse damage locked to the grid and was dropped.
Orthotropy: across the fibres wood shrinks about 4 times as much as along them (a search summary of a fir pyrolysis experiment, Combustion Institute: parallel is 1/4 of perpendicular), it is stiffer along them (typical wood 10-20:1, general knowledge) and splits easily between them. The structure tensor A makes a crack across the fibres cost more than one between them.
Two generations: Baroudi et al. 2017 (arXiv 1604.01249) report a quasi-periodic primary macro pattern, mainly across the fibres, from a thick layer; finer cracks later. A coarse run (thick layer: long L) comes first and is frozen into the fine run (thin skin: short L).
The AT1 profile is d(x) = (1 - |x| / 2l)^2 within 2l of the crack, so 2l (1 - sqrt d) is a smooth distance to its centre line, without stair steps. The crack's width comes from the actual jump of u across it.

ESTIMATES, not measured: every number in PRESETS, by looking at the result against ref/charcoal (charbon, rouge).
Axes: s along the fibres (columns), t across them round the girth (rows). In cm.
"""

import json
import os
import sys
import time

import cv2
import numpy as np
import torch
from scipy.ndimage import distance_transform_edt
import torch.nn.functional as TF

# GEWU_TORCH_DEV=cpu: no GPU slot needed (tools/README.md), and works on a machine without one
DEV = os.environ.get("GEWU_TORCH_DEV") or ("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2")


def noise(h, w, sy, sx, seed):
    """Gaussian noise blurred by (sy, sx) grid steps, unit variance. By FFT: large sigmas cost nothing. Periodic; the domain has a margin."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    n = torch.randn(h, w, generator=g).to(DEV)
    fy = torch.fft.fftfreq(h, device=DEV)[:, None]
    fx = torch.fft.rfftfreq(w, device=DEV)[None, :]
    H = torch.exp(-2.0 * (torch.pi**2) * ((fy * sy) ** 2 + (fx * sx) ** 2))
    out = torch.fft.irfft2(torch.fft.rfft2(n) * H, s=(h, w))
    return out / (out.std() + 1e-9)


def edge_s(a):
    return 0.5 * (a[:, 1:] + a[:, :-1])


def edge_t(a):
    return 0.5 * (a[1:, :] + a[:-1, :])


def corner(a):
    return 0.25 * (a[1:, 1:] + a[1:, :-1] + a[:-1, 1:] + a[:-1, :-1])


class Skin:
    def __init__(self, H, W, dx, p, seed, gc_map=None, shrink_map=None, frozen=None):
        self.H, self.W, self.dx, self.p = H, W, dx, p
        self.l = p["l"]
        self.ux = torch.zeros(H, W, device=DEV)
        self.uy = torch.zeros(H, W, device=DEV)
        self.vx = torch.zeros(H, W, device=DEV)
        self.vy = torch.zeros(H, W, device=DEV)
        self.d = torch.zeros(H, W, device=DEV)
        self.frozen = frozen
        if frozen is not None:
            self.d = frozen.clone()
        self.sh = shrink_map if shrink_map is not None else torch.ones(H, W, device=DEV)
        # the toughness: large patches, and a grain along the fibres
        f = 1.0 + p.get("gc_patch", 0.12) * noise(H, W, p.get("patch", 0.2) / dx, p.get("patch", 0.2) / dx, seed + 1).clamp(-2.5, 2.5)
        f = f * (1.0 + p.get("gc_fibre", 0.12) * noise(H, W, p.get("fibre_w", 0.012) / dx, p.get("fibre_len", 0.4) / dx, seed + 2).clamp(-2.5, 2.5))
        if gc_map is not None:
            f = f * gc_map
        # Gc so that a uniform film across the fibres reaches its strength at strain ec_t: sigma_c^2 = 3 E Gc / (8 l)
        self.gc = p["ec_t"] ** 2 * 8.0 * self.l * p["E_t"] / 3.0 * f.clamp(0.3, 3.0) ** 2
        self.ve_x = None

    def strains(self, tau):
        p, dx = self.p, self.dx
        ux, uy = self.ux, self.uy
        es = (ux[:, 1:] - ux[:, :-1]) / dx + p["e_s"] * tau * edge_s(self.sh)  # the rest length has shrunk, so a fixed film is in tension
        et = (uy[1:, :] - uy[:-1, :]) / dx + p["e_t"] * tau * edge_t(self.sh)
        duxy = 0.5 * ((ux[1:, 1:] + ux[1:, :-1] - ux[:-1, 1:] - ux[:-1, :-1]) + (uy[1:, 1:] + uy[:-1, 1:] - uy[1:, :-1] - uy[:-1, :-1])) / dx
        exy = 0.5 * duxy
        return es, et, exy

    def degrade(self):
        eta = 1e-4
        g = (1.0 - self.d) ** 2 + eta
        return edge_s(g), edge_t(g), corner(g)

    def force(self, tau, gs, gt, gc):
        p, dx = self.p, self.dx
        es, et, exy = self.strains(tau)
        ss = p["E_s"] * (torch.where(es > 0, gs, torch.ones_like(gs)) * es)  # a closed crack carries compression
        st = p["E_t"] * (torch.where(et > 0, gt, torch.ones_like(gt)) * et)
        sxy = 2.0 * p["G"] * gc * exy
        fx = -p["k"] * self.ux * dx
        fy = -p["k"] * self.uy * dx
        fx = fx.clone()
        fy = fy.clone()
        fx[:, :-1] += ss
        fx[:, 1:] -= ss
        fy[:-1, :] += st
        fy[1:, :] -= st
        # shear on the four corners of each cell
        q = sxy * 0.5
        fx[:-1, :-1] += q
        fx[:-1, 1:] += q
        fx[1:, :-1] -= q
        fx[1:, 1:] -= q
        fy[:-1, :-1] += q
        fy[1:, :-1] += q
        fy[:-1, 1:] -= q
        fy[1:, 1:] -= q
        return fx, fy

    def solve_u(self, tau, n):
        p, dx = self.p, self.dx
        gs, gt, gc = self.degrade()
        ax = 0.85 / (2.0 * p["E_s"] / dx + 2.0 * p["G"] / dx + p["k"] * dx)
        ay = 0.85 / (2.0 * p["E_t"] / dx + 2.0 * p["G"] / dx + p["k"] * dx)
        b = p.get("momentum", 0.93)
        for _ in range(n):
            fx, fy = self.force(tau, gs, gt, gc)
            self.vx = b * self.vx + ax * fx
            self.vy = b * self.vy + ay * fy
            self.ux = self.ux + self.vx
            self.uy = self.uy + self.vy

    def psi(self, tau):
        p = self.p
        es, et, exy = self.strains(tau)
        Ps = 0.5 * p["E_s"] * es.clamp(min=0.0) ** 2
        Pt = 0.5 * p["E_t"] * et.clamp(min=0.0) ** 2
        Pc = 2.0 * p["G"] * exy * exy
        out = torch.zeros(self.H, self.W, device=DEV)
        out[:, :-1] += 0.5 * Ps
        out[:, 1:] += 0.5 * Ps
        out[:-1, :] += 0.5 * Pt
        out[1:, :] += 0.5 * Pt
        out[:-1, :-1] += 0.25 * Pc
        out[:-1, 1:] += 0.25 * Pc
        out[1:, :-1] += 0.25 * Pc
        out[1:, 1:] += 0.25 * Pc
        return out

    def solve_d(self, tau, n, floor):
        p, dx, l = self.p, self.dx, self.l
        P = self.psi(tau)
        As, At = p["A_s"], p.get("A_t", 1.0)
        c = 0.75 * self.gc * l / (dx * dx)  # (3 Gc / 4) l / dx^2
        src = 3.0 * self.gc / (8.0 * l)
        den = 2.0 * P + c * (2.0 * As + 2.0 * At)
        d = self.d
        for it in range(n):
            pad = TF.pad(d[None, None], (1, 1, 1, 1), mode="replicate")[0, 0]
            nb = As * (pad[1:-1, :-2] + pad[1:-1, 2:]) + At * (pad[:-2, 1:-1] + pad[2:, 1:-1])
            new = (2.0 * P - src + c * nb) / den
            d = torch.max(0.25 * d + 0.75 * new, floor).clamp(max=1.0)
        self.d = d

    def run(self, log=print):
        p = self.p
        t0 = time.time()
        t_start = p.get("tau0", 0.2)
        for step in range(p["steps"]):
            tau = t_start + (1.0 - t_start) * (step + 1) / p["steps"]
            floor = self.d.clone()
            for k in range(p.get("stag", 3)):
                self.solve_u(tau, p["iters_u"])
                self.solve_d(tau, p["iters_d"], floor)
            if step % max(1, p["steps"] // 6) == 0 or step == p["steps"] - 1:
                log(f"  step {step + 1}/{p['steps']}, tau {tau:.2f}: cracked share {float((self.d > 0.5).float().mean()):.4f}; {time.time() - t0:.1f} s")
        self.solve_u(1.0, p["iters_u"] * 4)
        return self.d

    def opening(self):
        """How far the crack at each point has opened, cm: the jump of u across it, measured 3 l either side along the gradient of d."""
        dx, l = self.dx, self.l
        d = self.d[None, None]
        gy = (d[..., 2:, 1:-1] - d[..., :-2, 1:-1])[0, 0] / 2.0
        gx = (d[..., 1:-1, 2:] - d[..., 1:-1, :-2])[0, 0] / 2.0
        gy, gx = TF.pad(gy[None, None], (1, 1, 1, 1), mode="replicate")[0, 0], TF.pad(gx[None, None], (1, 1, 1, 1), mode="replicate")[0, 0]
        bl = TF.avg_pool2d(d, 5, 1, 2)[0, 0]
        gyb = TF.pad(((bl[2:, 1:-1] - bl[:-2, 1:-1]) / 2.0)[None, None], (1, 1, 1, 1), mode="replicate")[0, 0]
        gxb = TF.pad(((bl[1:-1, 2:] - bl[1:-1, :-2]) / 2.0)[None, None], (1, 1, 1, 1), mode="replicate")[0, 0]
        m = torch.sqrt(gxb * gxb + gyb * gyb) + 1e-6
        nx, ny = gxb / m, gyb / m
        # the ridge's normal is ill defined on the ridge: use the magnitude of the difference of u over a fixed box, whichever way it runs
        r = int(round(3.0 * l / dx))
        pool = lambda a: TF.max_pool2d(a[None, None], 2 * r + 1, 1, r)[0, 0]
        spanx = pool(self.ux) + pool(-self.ux)
        spany = pool(self.uy) + pool(-self.uy)
        return torch.sqrt(spanx * spanx + spany * spany)


def thin(mask):
    """Zhang-Suen thinning, on the GPU: a band to its 8-connected centre line."""
    k = torch.zeros(mask.shape, device=DEV, dtype=torch.bool)
    m = TF.pad(mask.float()[None, None], (1, 1, 1, 1))[0, 0] > 0.5
    for it in range(400):
        changed = False
        for step in (0, 1):
            a = m.to(torch.int8)
            p2, p3, p4, p5 = a[:-2, 1:-1], a[:-2, 2:], a[1:-1, 2:], a[2:, 2:]
            p6, p7, p8, p9 = a[2:, 1:-1], a[2:, :-2], a[1:-1, :-2], a[:-2, :-2]
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            ns = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            A = sum(((ns[i] == 0) & (ns[i + 1] == 1)).to(torch.int8) for i in range(8))
            if step == 0:
                c1, c2 = p2 * p4 * p6, p4 * p6 * p8
            else:
                c1, c2 = p2 * p4 * p8, p2 * p6 * p8
            rm = m[1:-1, 1:-1] & (B >= 2) & (B <= 6) & (A == 1) & (c1 == 0) & (c2 == 0)
            if rm.any():
                m[1:-1, 1:-1] &= ~rm
                changed = True
        if not changed:
            break
    return m[1:-1, 1:-1]


def centre_dist(d, opening, dx, thr=0.5):
    """The damage band of a phase field is wider than the crack, and wider still where it was overdriven. The crack is its centre line: returns (distance to it in cm, the opening at the nearest point on it, the line)."""
    sk = thin(d > thr)
    dist, ind = distance_transform_edt(~sk.cpu().numpy(), return_indices=True)
    op = opening.cpu().numpy()[ind[0], ind[1]]
    dist = cv2.GaussianBlur(dist.astype(np.float32), (0, 0), 0.5) * dx
    return torch.as_tensor(dist, device=DEV), torch.as_tensor(op.astype(np.float32), device=DEV), sk


# L = sqrt(E / k) in cm. A crack's width is about shrink x spacing.
PRESETS = {
    # the thick layer. Across-grain primaries spaced about a centimetre, then long splits between them
    "macro": dict(dx=0.01, l=0.025, E_s=4.0, E_t=1.0, G=0.25, k=1.2, e_s=0.05, e_t=0.07, ec_t=0.03, A_s=1.0, gc_patch=0.18, patch=0.5, gc_fibre=0.1, fibre_w=0.05, fibre_len=1.0, tau0=0.25, steps=50, stag=3, iters_u=90, iters_d=25),
    # the thin skin. L across 0.35 mm, along 0.9 mm
    "fine": dict(dx=0.0025, l=0.005, E_s=6.0, E_t=1.0, G=0.2, k=250.0, e_s=0.016, e_t=0.042, ec_t=0.03, A_s=9.0, gc_patch=0.14, patch=0.25, gc_fibre=0.12, fibre_w=0.01, fibre_len=0.5, tau0=0.5, steps=40, stag=3, iters_u=80, iters_d=25),
}


def grow(Ws, Hs, seed=6901, log=print, presets=PRESETS, gc_map=None):
    """A domain Ws x Hs cm. Returns dict on the fine grid: dist_f, open_f, the fine network with the macro cracks in it; dist_m, open_m, the macro cracks; d_f, d_m, the damage. Maps' (0, 0) is s = 0, t = 0 of the domain."""
    t0 = time.time()
    pm, pf = presets["macro"], presets["fine"]
    Hm, Wm = int(Hs / pm["dx"]) + 1, int(Ws / pm["dx"]) + 1
    log(f"macro {Wm} x {Hm}")
    sm = 1.0 + 0.25 * noise(Hm, Wm, 0.8 / pm["dx"], 0.8 / pm["dx"], seed + 10).clamp(-2.5, 2.5)
    M = Skin(Hm, Wm, pm["dx"], pm, seed, shrink_map=sm)
    M.run(log)
    Om = M.opening()
    Hf, Wf = int(Hs / pf["dx"]) + 1, int(Ws / pf["dx"]) + 1
    up = lambda a, mode="bicubic": TF.interpolate(a[None, None], size=(Hf, Wf), mode=mode, align_corners=True)[0, 0]
    dm = up(M.d).clamp(0.0, 1.0)
    om = up(Om, "bilinear")
    log(f"macro done {time.time() - t0:.1f} s; opening at cracks p50 {float(torch.median(Om[M.d > 0.7])) if (M.d > 0.7).any() else 0:.4f} cm")
    # the frozen crack as the fine skin sees it: its own narrow profile round the macro crack's centre line
    dist_m, open_m, _ = centre_dist(dm, om, pf["dx"])
    frozen = (1.0 - (dist_m / (2.0 * pf["l"])).clamp(0.0, 1.0)) ** 2
    log(f"fine {Wf} x {Hf} ({Wf * Hf / 1e6:.2f} M)")
    sf = 1.0 + 0.2 * noise(Hf, Wf, 0.25 / pf["dx"], 0.4 / pf["dx"], seed + 11).clamp(-2.5, 2.5)
    F = Skin(Hf, Wf, pf["dx"], pf, seed + 100, shrink_map=sf, frozen=frozen, gc_map=gc_map)
    F.run(log)
    Of = F.opening()
    dist_f, open_f, _ = centre_dist(F.d, Of, pf["dx"])
    log(f"fine done {time.time() - t0:.1f} s; opening p50 {float(torch.median(Of[F.d > 0.7])) if (F.d > 0.7).any() else 0:.4f} cm; {time.time() - t0:.1f} s")
    return dict(d_f=F.d.cpu().numpy(), dist_f=dist_f.cpu().numpy(), open_f=open_f.cpu().numpy(), d_m=dm.cpu().numpy(), dist_m=dist_m.cpu().numpy(), open_m=open_m.cpu().numpy(), dx=pf["dx"], l_f=pf["l"], l_m=pm["l"])


def test():
    os.makedirs(os.path.join(OUT, "s69_mutan"), exist_ok=True)
    pr = {k: dict(v) for k, v in PRESETS.items()}
    if len(sys.argv) > 2:
        for k, v in json.loads(sys.argv[2]).items():
            pr[k].update(v)
    R = grow(5.0, 3.0, presets=pr)
    f, m = R["d_f"], R["d_m"]
    print("cracked share fine", (f > 0.5).mean(), "macro", (m > 0.5).mean(), "open_f at crack pct", np.percentile(R["open_f"][f > 0.7], [10, 50, 90]) if (f > 0.7).any() else None)
    mask_f = np.clip((np.minimum(R["open_f"] * 0.5, 0.02) + 0.0008 - R["dist_f"]) / 0.002, 0, 1) * (f > 0.02)
    mask_m = np.clip((np.minimum(R["open_m"] * 0.5, 0.06) - R["dist_m"]) / 0.002, 0, 1) * (m > 0.02)
    print("real share fine", mask_f.mean(), "macro", mask_m.mean())
    im = np.stack([0.85 - mask_f * 0.85 - mask_m, 0.82 - mask_f * 0.82 - mask_m, 0.78 - mask_f * 0.78 - mask_m], -1)
    u8 = (np.clip(im, 0, 1) * 255).astype(np.uint8)
    cv2.imwrite(os.path.join(OUT, "s69_mutan", "crack_test.jpg"), u8, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(u8.shape)


if __name__ == "__main__":
    test()
