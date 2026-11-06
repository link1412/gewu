"""Shot 69 (charcoal): a piece of charcoal as a real solid. An implicit field in shell coordinates, meshed with surface nets. Needs torch.

Shell coordinates: s along the fibres, t round the girth (arc length at R0), w inward from a smooth base surface. The base is a polar graph round the piece's axis, so world position is closed-form and the field can be evaluated in either direction. Unlike a height field a solid has real walls: a crack's wall is sampled as finely as its top, the vessels are tubes that open as grooves where the surface cuts them and show in the crack walls.

Wood anatomy, ESTIMATES from general knowledge (ring-porous hardwood, e.g. oak): ring width 1.2-2.2 mm; earlywood vessels 120-350 um across, in one or two rows at the start of each ring; latewood vessels 30-90 um in groups; rays as spindles along the fibres. Ring surfaces are cylinders round a pith axis tilted against the piece's axis, so the burnt surface cuts them as long contour loops, as it does on a real flank.
"""

import os
import sys
import time

import cv2
import numpy as np
import torch
import torch.nn.functional as TF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s69_crack import DEV, noise


def sstep(a, b, x):
    t = ((x - a) / (b - a)).clamp(0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def fbm2(h, w, dx, lo, hi, seed, beta=1.0):
    """Sum of bands between wavelengths lo and hi (cm), each octave's amplitude falling as (wavelength)^beta. Unit variance."""
    out = torch.zeros(h, w, device=DEV)
    L, k, a = hi, 0, 1.0
    while L >= lo * 0.999:
        out += a * noise(h, w, L / 2.5 / dx, L / 2.5 / dx, seed + k)
        L, k, a = L / 2.0, k + 1, a * 0.5**beta
    return out / (out.std() + 1e-9)


class Piece:
    """p: R0, L (radius, half length of the barrel), s0, s1, t0, t1 (domain, cm), w_out, w_in (cm above and below the base), T (3x3) rotation, C (3) position of the centre; low: strength of the base surface's lumps."""

    def __init__(self, p, seed):
        self.p, self.seed = p, seed
        self.R0, self.L = p["R0"], p["L"]
        self.Rw = np.array(p.get("rot", np.eye(3)), np.float32)
        self.Cw = np.array(p.get("pos", (0, 0, 0)), np.float32)

    def base_fields(self, dx):
        p = self.p
        W, H = int((p["s1"] - p["s0"]) / dx) + 1, int((p["t1"] - p["t0"]) / dx) + 1
        self.H, self.W, self.dx = H, W, dx
        s = p["s0"] + torch.arange(W, device=DEV, dtype=torch.float32) * dx
        t = p["t0"] + torch.arange(H, device=DEV, dtype=torch.float32) * dx
        self.S = s[None, :].expand(H, W)
        self.T = t[:, None].expand(H, W)
        seed = self.seed
        barrel = torch.sqrt((1.0 - (self.S / self.L) ** 2).clamp(min=0.02))
        # on a fixed grid and interpolated, so that the same piece at another resolution is the same shape
        dL = 0.025
        HL, WL = int((p["t1"] - p["t0"]) / dL) + 1, int((p["s1"] - p["s0"]) / dL) + 1
        lump = 0.6 * fbm2(HL, WL, dL, 0.7, 3.0, seed + 1, 1.6) + 0.12 * fbm2(HL, WL, dL, 0.2, 0.7, seed + 2, 1.2)
        lump = TF.interpolate(lump[None, None], size=(H, W), mode="bicubic", align_corners=True)[0, 0]
        self.rho = self.R0 * barrel + p.get("low", 0.05) * lump  # cm from the axis

    def world(self, s, t, w, rho_at):
        """Vertices. s, t, w 1-D tensors; rho_at: base radius at them."""
        a = t / self.R0
        r = rho_at - w
        P = torch.stack([s, -r * torch.sin(a), r * torch.cos(a)], -1).cpu().numpy().astype(np.float32)
        return P @ self.Rw.T + self.Cw


def sample2(f, s, t, p, dx):
    """Bilinear lookup of a 2-D field at shell points."""
    x = (s - p["s0"]) / dx
    y = (t - p["t0"]) / dx
    H, W = f.shape[-2:]
    gx = 2.0 * (x + 0.5) / W - 1.0
    gy = 2.0 * (y + 0.5) / H - 1.0
    g = torch.stack([gx, gy], -1)[None, None]
    return TF.grid_sample(f[None, None] if f.dim() == 2 else f[None], g, mode="bilinear", align_corners=False, padding_mode="border")[0, ..., 0, :].squeeze(0)


def rings_table(seed, r0=0.0, r1=4.0):
    rng = np.random.default_rng(seed)
    w = np.clip(rng.lognormal(np.log(0.16), 0.3, 60), 0.075, 0.32)
    b = r0 - 0.2 + np.cumsum(w)
    return torch.tensor(b, device=DEV, dtype=torch.float32)


def ring_phase(r, bounds):
    """(fraction across the ring, index). 0 at the abrupt start of the earlywood on the pith side."""
    k = torch.searchsorted(bounds, r).clamp(1, len(bounds) - 1)
    lo, hi = bounds[k - 1], bounds[k]
    return ((r - lo) / (hi - lo)).clamp(0.0, 1.0), k


def vessels_tex(p, bounds, dx_tex, seed):
    """A cross-section (t, r) with every vessel in it: 1 inside a tube. One texture, looked up with wandering coordinates along the fibres."""
    t0, t1 = p["t0"] - 0.1, p["t1"] + 0.1
    r0, r1 = p["R0"] - p["w_in"] - 0.2, p["R0"] + p["w_out"] + 0.2
    W, H = int((t1 - t0) / dx_tex), int((r1 - r0) / dx_tex)
    im = np.zeros((H, W), np.uint8)
    rng = np.random.default_rng(seed)
    b = bounds.cpu().numpy()
    Rt = p["R0"]

    def blob(t, r, rx, ry):
        x, y = (t - t0) / dx_tex, (r - r0) / dx_tex
        m = rng.integers(7, 11)
        a = np.sort(rng.uniform(0, 6.283, m))
        q = rng.uniform(0.82, 1.0, m)
        pts = np.stack([x + rx / dx_tex * q * np.cos(a), y + ry / dx_tex * q * np.sin(a)], 1)
        cv2.fillPoly(im, [np.round(pts * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)

    for i in range(len(b) - 1):
        lo, hi = b[i], b[i + 1]
        if hi < r0 or lo > r1:
            continue
        wid = hi - lo
        # earlywood: big, one or two rows at the start of the ring
        n = int((t1 - t0) * rng.uniform(46, 64))
        for t_ in rng.uniform(t0, t1, n):
            dep = abs(rng.normal(0, 0.09))
            a_ = rng.lognormal(np.log(0.0085), 0.3) * np.clip(1.15 - dep * 2.5, 0.45, 1.1)
            blob(t_, lo + 0.012 + dep * wid, a_, a_ * rng.uniform(0.9, 1.35))
        # latewood: small, in flame-shaped groups
        for t_ in rng.uniform(t0, t1, int((t1 - t0) * rng.uniform(9, 14))):
            r_ = lo + wid * rng.uniform(0.3, 0.42)
            sw = rng.uniform(0.012, 0.04)
            for j in range(rng.integers(5, 15)):
                r_ += rng.uniform(0.005, 0.014)
                if r_ > hi - 0.05 * wid:
                    break
                a_ = rng.lognormal(np.log(0.0028), 0.3)
                blob(t_ + rng.normal(0, sw * (1.0 - 0.5 * (r_ - lo) / wid)), r_, a_, a_)
    im = cv2.GaussianBlur(im.astype(np.float32) / 255.0, (0, 0), 1.0)
    return torch.tensor(im, device=DEV), (t0, t1, r0, r1)


def surface_nets(phi):
    """phi (D, H, W), solid where > 0. Returns (V in index space z, y, x), (F triangles, wound so that normals point out of the solid). Vectorised; memory is the volume plus an int32 volume of cell ids."""
    D, H, W = phi.shape
    inside = phi > 0
    c = inside[:-1, :-1, :-1].to(torch.int8) + inside[1:, :-1, :-1].to(torch.int8) + inside[:-1, 1:, :-1].to(torch.int8) + inside[:-1, :-1, 1:].to(torch.int8) + inside[1:, 1:, :-1].to(torch.int8) + inside[1:, :-1, 1:].to(torch.int8) + inside[:-1, 1:, 1:].to(torch.int8) + inside[1:, 1:, 1:].to(torch.int8)
    mixed = (c > 0) & (c < 8)
    del c
    idx = mixed.nonzero()
    n = idx.shape[0]
    ids = torch.full((D - 1, H - 1, W - 1), -1, dtype=torch.int32, device=DEV)
    ids[idx[:, 0], idx[:, 1], idx[:, 2]] = torch.arange(n, device=DEV, dtype=torch.int32)
    del mixed
    # corners and edges of a cell
    corners = torch.tensor([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]], device=DEV)
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    V = torch.zeros((n, 3), device=DEV, dtype=torch.float32)
    bs = 4_000_000
    for a in range(0, n, bs):
        I = idx[a : a + bs]
        vals = torch.stack([phi[I[:, 0] + c_[0], I[:, 1] + c_[1], I[:, 2] + c_[2]] for c_ in corners], 1)
        s_, w_ = torch.zeros((len(I), 3), device=DEV), torch.zeros(len(I), device=DEV)
        for e0, e1 in edges:
            v0, v1 = vals[:, e0], vals[:, e1]
            cross = (v0 > 0) != (v1 > 0)
            f = (v0 / (v0 - v1 + 1e-12)).clamp(0, 1)
            p = corners[e0].float()[None] + (corners[e1] - corners[e0]).float()[None] * f[:, None]
            s_ += p * cross[:, None]
            w_ += cross
        V[a : a + bs] = I.float() + s_ / w_.clamp(min=1)[:, None]
    # faces: one quad round every grid edge whose ends differ
    Fs = []

    def quads(mask, cell_a, cell_b, cell_c, cell_d, flip):
        q = mask.nonzero()
        if len(q) == 0:
            return
        A, B, C, E = [ids[q[:, 0] + o[0], q[:, 1] + o[1], q[:, 2] + o[2]] for o in (cell_a, cell_b, cell_c, cell_d)]
        ins = flip[q[:, 0], q[:, 1], q[:, 2]]
        t1 = torch.stack([A, B, C], 1)
        t2 = torch.stack([A, C, E], 1)
        t1r = torch.stack([A, C, B], 1)
        t2r = torch.stack([A, E, C], 1)
        Fs.append(torch.where(ins[:, None], t1, t1r))
        Fs.append(torch.where(ins[:, None], t2, t2r))

    # edges along z between (z, y, x) and (z + 1, y, x); y and x interior
    e = (inside[:-1, 1:-1, 1:-1] != inside[1:, 1:-1, 1:-1])
    quads(e, (0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1), inside[:-1, 1:-1, 1:-1])
    e = (inside[1:-1, :-1, 1:-1] != inside[1:-1, 1:, 1:-1])
    quads(e, (0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0), inside[1:-1, :-1, 1:-1])
    e = (inside[1:-1, 1:-1, :-1] != inside[1:-1, 1:-1, 1:])
    quads(e, (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), inside[1:-1, 1:-1, :-1])
    F = torch.cat(Fs, 0)
    F = F[(F >= 0).all(1)]
    return V, F
