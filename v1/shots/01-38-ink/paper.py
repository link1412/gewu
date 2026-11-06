"""Xuan paper as a fibre network: a map of local grammage (fibre mass per area), relative to the mean.

Handmade paper is laid fibre by fibre from a dilute suspension; fibres clump into flocs, which is what a backlit
sheet shows as cloudy "formation". We place fibre segments (straight, random orientation) with a placement
density modulated by a smooth floc field, rasterise them, and blur by the fibre width.

All lengths in mm. Parameters and their labels: params.json "paper".
"""
import numpy as np
from numpy.fft import irfft2, rfft2, rfftfreq, fftfreq


def gaussian_field(shape, dx, corr_mm, rng):
    """Zero-mean, unit-variance Gaussian random field with a Gaussian spectrum of correlation length corr_mm."""
    ny, nx = shape
    kx = rfftfreq(nx, dx)[None, :]
    ky = fftfreq(ny, dx)[:, None]
    amp = np.exp(-(np.pi * corr_mm) ** 2 * (kx ** 2 + ky ** 2))
    f = irfft2(rfft2(rng.standard_normal(shape)) * amp, s=shape)
    return (f - f.mean()) / f.std()


def blur(img, dx, sigma_mm):
    ny, nx = img.shape
    kx = rfftfreq(nx, dx)[None, :]
    ky = fftfreq(ny, dx)[:, None]
    return irfft2(rfft2(img) * np.exp(-2 * (np.pi * sigma_mm) ** 2 * (kx ** 2 + ky ** 2)), s=img.shape)


def grammage(extent, dx, p, seed):
    """extent = (x0, x1, y0, y1) mm. Returns g (ny, nx), mean 1: local fibre mass per area / the sheet's mean."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = extent
    nx, ny = int(round((x1 - x0) / dx)), int(round((y1 - y0) / dx))
    floc = gaussian_field((ny, nx), dx, p["floc_corr_mm"], rng)
    dens = np.exp(p["floc_sigma"] * floc)
    dens /= dens.sum()
    area = (x1 - x0) * (y1 - y0)
    out = np.zeros((ny, nx))
    for fam in p["fibres"]:                      # each furnish: bast (qingtan) and rice straw
        # fibre count from the furnish's share of the basis weight and its coarseness (mass per length)
        mass = p["basis_weight_gsm"] * 1e-6 * area * fam["share"]            # g in this patch (g/m^2 -> g/mm^2)
        L = fam["length_mm"]
        n = int(mass / (fam["coarseness_mg_per_m"] * 1e-6 * L))              # mg/m = 1e-6 g/mm
        acc = np.zeros(nx * ny)
        k = max(2, int(np.ceil(L / dx)))                                     # samples along a mean fibre
        t = (np.arange(k) + 0.5) / k - 0.5
        for c0 in range(0, n, 40000):
            m = min(40000, n - c0)
            cells = rng.choice(nx * ny, size=m, p=dens.ravel())
            cx = x0 + (cells % nx + rng.random(m)) * dx
            cy = y0 + (cells // nx + rng.random(m)) * dx
            ln = L * np.exp(fam["length_logsd"] * rng.standard_normal(m) - fam["length_logsd"] ** 2 / 2)
            th = rng.uniform(0, np.pi, m)
            px = cx[:, None] + np.cos(th)[:, None] * ln[:, None] * t[None, :]
            py = cy[:, None] + np.sin(th)[:, None] * ln[:, None] * t[None, :]
            w = np.repeat((ln / k)[:, None], k, axis=1)                      # fibre length per sample
            ix = np.floor((px - x0) / dx).astype(int)
            iy = np.floor((py - y0) / dx).astype(int)
            ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
            np.add.at(acc, iy[ok] * nx + ix[ok], w[ok] * fam["coarseness_mg_per_m"])   # mass per sample
        out += acc.reshape(ny, nx)
    out = blur(out, dx, p["fibre_width_mm"] / 2)
    return out / out.mean()
