"""The fields that make up the glaze's appearance on a flat tile, from material.json (every number there has a tag).

    height_map(...)  the surface relief of the speckle (pits and opened bubbles), mm
    thickness(...)   the glaze thickness field e(x, y), mm (mottling)
    stain_levels(...) the burial-stain blotches, as integer levels
Nothing here is painted from the photo: sizes and densities are measured numbers in material.json, shapes are generated.
"""
import json
import math
import os

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))


def load_material():
    return json.load(open(os.path.join(HERE, "material.json")))


def gaussian_noise(shape, corr_px, rng):
    f = ndi.gaussian_filter(rng.standard_normal(shape), corr_px, mode="reflect")
    return (f - f.mean()) / (f.std() + 1e-12)


def height_map(mat, half_w, half_h, px_per_mm, rng):
    """Float image (rows from y = +half_h down to -half_h, columns x = -half_w..+half_w), mm. Gaussian pits:
    for each size class, Poisson-distributed positions at the measured density, depth = depth_over_sigma x sigma."""
    sp = mat["surface"]["speckle"]
    nx, ny = int(round(2 * half_w * px_per_mm)), int(round(2 * half_h * px_per_mm))
    h = np.zeros((ny, nx), np.float32)
    area = 4 * half_w * half_h
    k = sp["depth_over_sigma"]["value"]
    counts = {}
    for c in sp["classes"]:
        n = rng.poisson(c["per_mm2"] * area)
        counts[c["sigma_um"]] = int(n)
        sig_mm = c["sigma_um"] * 1e-3
        sig_px = sig_mm * px_per_mm
        # sub-pixel positions: spread each delta over the 4 neighbouring pixels
        x = rng.uniform(0, nx - 1.001, n)
        y = rng.uniform(0, ny - 1.001, n)
        # a size spread inside the class (lognormal, 25%) is not modelled: the classes are the measured bins
        layer = np.zeros((ny, nx), np.float64)
        ix, iy = x.astype(int), y.astype(int)
        fx, fy = x - ix, y - iy
        for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            np.add.at(layer, (iy + dy, ix + dx), w)
        g = ndi.gaussian_filter(layer, sig_px, mode="constant") * (2 * math.pi * sig_px ** 2)   # unit-peak pits
        h -= (k * sig_mm * g).astype(np.float32)
    return h, counts


def thickness(mat, xs, ys, rng):
    """Glaze thickness e(x, y) on a grid, mm: mean + a correlated Gaussian field."""
    gv = mat["glaze_volume"]["thickness_mm"]["value"]
    mo = mat["surface"]["mottling"]
    step = xs[1] - xs[0]
    f = gaussian_noise((len(ys), len(xs)), mo["corr_mm"]["value"] / step, rng)
    return np.maximum(gv + mo["std_mm"]["value"] * f, 0.3 * gv)


def stain_levels(mat, xs, ys, rng, fraction=0.077, corr_mm=0.7, big_mm=4.0):
    """Burial blotches: a smooth random field (a fine and a coarse part, so there are small spots and a few
    patches) thresholded. Level 0 none, 1 faint (area `fraction`), 2 strong (a quarter of that area).
    fraction: the photo's area at R/B > 1.4 x the glaze median (measured_met48503.json, stains)."""
    step = xs[1] - xs[0]
    f = 0.6 * gaussian_noise((len(ys), len(xs)), corr_mm / step, rng) + 0.8 * gaussian_noise((len(ys), len(xs)), big_mm / step, rng)
    f = (f - f.mean()) / f.std()
    t1 = np.quantile(f, 1 - fraction)
    t2 = np.quantile(f, 1 - fraction / 4)
    return (f > t1).astype(int) + (f > t2).astype(int)
