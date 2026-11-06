"""Shot 68: tea particles through the flat water surface, to the screen. Torch; runs on the GPU.

Picture = R + T * exp(-tau(lambda)): R (cup above water, sky, reflection on the water) and T (everything seen through the water) are Cycles plates, the tea is only an absorber (an assumption).
Each particle is refracted exactly through the plane z = 0 (Newton on Snell, same pinhole as Blender's camera) and adds column density to a layer chosen by its age (how far it has diffused) and its depth (how far out of focus).
Transmission is taken per wavelength band, layer by layer, so a thin thread out of focus goes pale as it should.
Limits: the surface is taken flat (the meniscus band near the wall is not warped); the circle of confusion uses the mean of the sagittal and tangential apparent depths.
"""

import numpy as np
import torch

import s68_geom as G

DEV = "cuda" if torch.cuda.is_available() else "cpu"
BINS = np.array([0.0, 2.0, 4.0, 7.0, 11.0, 16.0, 23.0, 32.0, 44.0, 60.0, 80.0])  # blur disc diameter in px at 2560 wide
MARGIN = 0.05


class View:
    def __init__(self, w, h, cam=None):
        cam = cam or G.camera()
        self.w, self.h = w, h
        r, u, b = G.axes(cam)
        t = lambda a: torch.tensor(np.asarray(a), dtype=torch.float64, device=DEV)
        self.C, self.r, self.u, self.b = t(cam["loc"]), t(r), t(u), t(b)
        self.fpx = w * cam["lens_mm"] / 36.0
        self.fd = cam["focus_distance"]
        self.A = cam["aperture_mm"] * 0.1

    def project(self, P):
        """P (n, 3) float32 on the GPU. Returns u, v in pixels (pixel i spans i .. i + 1) and the blur disc's diameter in pixels."""
        C = self.C.float()
        H = C[2]
        dx, dy = P[:, 0] - C[0], P[:, 1] - C[1]
        rho = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-6)
        D = (-P[:, 2]).clamp(min=1e-5)
        n = G.N_WATER
        sa0 = rho / torch.sqrt(rho * rho + H * H)
        tw0 = (sa0 / n) / torch.sqrt(1 - (sa0 / n) ** 2)
        s = (rho - D * tw0).clamp(min=0.0)
        for _ in range(3):
            a = torch.sqrt(s * s + H * H)
            b = torch.sqrt((rho - s) ** 2 + D * D)
            f = s / a - n * (rho - s) / b
            df = H * H / a**3 + n * D * D / b**3
            s = (s - f / df).clamp(min=0.0)
            s = torch.minimum(s, rho)
        k = s / rho
        Sx, Sy = C[0] + dx * k, C[1] + dy * k
        ex, ey, ez = Sx - C[0], Sy - C[1], -H
        r, u, bk = self.r.float(), self.u.float(), self.b.float()
        zc = -(ex * bk[0] + ey * bk[1] + ez * bk[2])
        uu = (ex * r[0] + ey * r[1] + ez * r[2]) / zc * self.fpx + self.w / 2.0
        vv = -(ex * u[0] + ey * u[1] + ez * u[2]) / zc * self.fpx + self.h / 2.0
        a = torch.sqrt(s * s + H * H)
        b = torch.sqrt((rho - s) ** 2 + D * D)
        ca, sw = H / a, (rho - s) / b
        cw2 = (1 - sw * sw).clamp(min=1e-6)
        extra = b / n * 0.5 * (1.0 + ca * ca / cw2)  # apparent depth below the surface along the ray: mean of sagittal and tangential
        coc = self.fpx * self.A * torch.abs(1.0 / (zc + extra) - 1.0 / self.fd)
        return uu, vv, coc


COC = np.array([0.0, 8.0, 18.0, 34.0, 60.0])  # lens blur disc, diameter in px at 2560
SIG = np.array([1.5, 3.5, 7.0, 13.0, 24.0, 44.0, 80.0, 140.0])  # blur of the tea by its own diffusion, sigma in px at 2560


def splat(view, P, age, mass, D_eff, N=None, chunk=16_000_000):
    """Deposit particles in a grid of layers: (sigma bin, lens bin). Each particle's place in the grid moves continuously with its age and depth, shared between neighbours, so nothing pops as it crosses a bin; no random walk is needed, so there is no frame-to-frame shimmer.
    Returns column density (cm of undiluted tea) per layer and the margin."""
    w, h = view.w, view.h
    m = int(MARGIN * w)
    Wd, Hd = w + 2 * m, h + 2 * m
    k = w / 2560.0
    cb = torch.tensor(COC * k, device=DEV, dtype=torch.float32)
    sb = torch.tensor(SIG * k, device=DEV, dtype=torch.float32)
    ns, nc = len(SIG), len(COC)
    if N is None:
        N = torch.zeros((ns * nc, Hd * Wd), device=DEV, dtype=torch.float32)
    flat = N.view(-1)
    px_cm = view.fpx / view.fd
    for i in range(0, len(P), chunk):
        p, ag = P[i : i + chunk], age[i : i + chunk]
        rad = torch.from_numpy(G.inner_radius(p[:, 2].cpu().numpy())).to(DEV).float()
        keep = torch.hypot(p[:, 0], p[:, 1]) < rad  # behind the wall is not seen
        p, ag = p[keep], ag[keep]
        if len(p) == 0:
            continue
        uu, vv, coc = view.project(p)
        x, y = uu + m - 0.5, vv + m - 0.5
        keep = (x >= 0) & (x < Wd - 1) & (y >= 0) & (y < Hd - 1)
        x, y, coc, ag = x[keep], y[keep], coc[keep], ag[keep]
        ix, iy = x.long(), y.long()
        fx, fy = x - ix, y - iy
        sg = torch.sqrt(2.0 * D_eff * ag.clamp(min=0.0)) * px_cm  # px
        cc = coc.clamp(max=float(cb[-1]) - 1e-3)
        ss = sg.clamp(min=float(sb[0]), max=float(sb[-1]) - 1e-3)
        bc = torch.bucketize(cc, cb, right=True) - 1
        bs = torch.bucketize(ss, sb, right=True) - 1
        tc = (cc - cb[bc]) / (cb[bc + 1] - cb[bc])
        ts = (ss - sb[bs]) / (sb[bs + 1] - sb[bs])
        for ds, ws in ((0, 1 - ts), (1, ts)):
            for dc, wc in ((0, 1 - tc), (1, tc)):
                lay = (bs + ds) * nc + bc + dc
                for dx, dy, wx in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
                    flat.index_add_(0, lay * (Hd * Wd) + (iy + dy) * Wd + (ix + dx), wx * ws * wc * (mass * px_cm**2))
    return N.view(ns * nc, Hd, Wd), m


def _freq(H, W):
    Y, X = torch.meshgrid(torch.fft.fftfreq(H, 1 / H, device=DEV), torch.fft.rfftfreq(W, 1 / W, device=DEV) , indexing="ij")
    return Y, X


def transmission(N, m, eps, weights, w):
    """N (layers, H, W). Diffusion moves the tea before it absorbs: Gaussian on the column density. The lens mixes light after: disc on what each layer removes, per band. Layers multiply: pure absorption. Returns (3, h, w) colour multiplier."""
    _, H, W = N.shape
    k = w / 2560.0
    ns, nc = len(SIG), len(COC)
    Yf, Xf = torch.meshgrid(torch.fft.fftfreq(H, device=DEV), torch.fft.rfftfreq(W, device=DEV), indexing="ij")
    w2 = (2 * np.pi) ** 2 * (Xf**2 + Yf**2)
    Trans = torch.ones((len(eps), H, W), device=DEV, dtype=torch.float32)
    Y, X = torch.meshgrid(torch.fft.fftfreq(H, 1 / H, device=DEV), torch.fft.fftfreq(W, 1 / W, device=DEV), indexing="ij")
    rr = torch.hypot(X, Y)
    Ks = []
    for d in COC * k:
        if d < 1.2:
            Ks.append(None)
            continue
        kk = torch.clamp(float(d) / 2.0 + 0.5 - rr, 0, 1)
        Ks.append(torch.fft.rfft2(kk / kk.sum()))
    for b in range(ns * nc):
        n = N[b]
        if float(n.max()) <= 0:
            continue
        s, c = b // nc, b % nc
        n = torch.fft.irfft2(torch.fft.rfft2(n) * torch.exp(-0.5 * w2 * float(SIG[s] * k) ** 2), s=(H, W)).clamp(min=0.0)
        for j, e in enumerate(eps):
            a = 1.0 - torch.exp(-float(e) * n)
            if Ks[c] is not None:
                a = torch.fft.irfft2(torch.fft.rfft2(a) * Ks[c], s=(H, W))
            Trans[j] *= (1.0 - a).clamp(min=0.0)
    wt = torch.tensor(np.asarray(weights), device=DEV, dtype=torch.float32)
    rgb = (Trans.permute(1, 2, 0) @ wt).permute(2, 0, 1).clamp(min=0.0)
    return rgb[:, m:-m, m:-m] if m else rgb
