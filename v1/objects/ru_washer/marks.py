"""Surface marks as an image-space stand-in [A], not rendered: the crackle (until cracks.py renders it; --no-crackle
leaves it out), pinholes, the foot's rust, the lip, the uneven tone. a network on the glaze's surface found from a
position pass (pbrt's gbuffer film in world coordinates, 1 spp, at a multiple of the render's resolution, so the
lines come out antialiased), turned into a factor that multiplies the developed render's linear RGB.

What it imitates (the CMA photo's full-resolution crops, 19.7 px/mm, by eye [M]): a fine network of cells 2-5 mm
across with light edges (the 「白边」), and fewer long primary cracks 10-20 mm apart, darker and faintly tan; each cell
a shade of its own (the layered look); a few pinholes (棕眼) on the outer wall; rust-brown
patches and a pale band on the foot ring, a pale lip, an uneven tone (the MARKS). Here: three 3D Voronoi networks (two fine, one primary) cut by
the surface (the cells come out about isotropic on it, no unwrapping), their edges made wavy by a smooth warp. All
the numbers below are [A]. The physical crack (a thin air film in the glaze that reflects and shades) is TODO.

    python3 -I objects/ru_washer/marks.py GBUF.exr --down 2 --out factor.npy [--preview factor.png]
"""
import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IMGTOOL = os.path.join(ROOT, "third_party/pbrt-build/imgtool")

FINE = dict(spacing=2.4, warp=0.6, warp_scale=3.0, sigma=0.05, gain=+0.30, cell_shade=0.05, seed=1)
FINER = dict(spacing=1.5, warp=0.4, warp_scale=2.0, sigma=0.04, gain=+0.18, seed=4)
PRIMARY = dict(spacing=13.0, warp=2.5, warp_scale=10.0, sigma=0.045, gain=-0.22, halo_sigma=0.12, halo_gain=+0.05,
               tan=(0.75, 0.95, 1.25), seed=2)
PINHOLES = dict(n=7, radius=(0.18, 0.4), gain=-0.6, rim=+0.12, seed=3)
# the photo by eye [M]: rust-brown patches on the foot ring's bottom, a pale band under them, a pale lip,
# the glaze's tone uneven (its thickness) [A: all numbers]
MARKS = dict(foot_z=2.6, rust=(0.40, 0.29, 0.23), rust_cover=0.22, band_z=0.5, band=(1.10, 1.07, 1.0),
             lip_mm=0.35, lip=(1.10, 1.06, 0.97), mottle=0.05, mottle_scale=7.0, dark_edges=0.35,
             dark_gain=-0.16, seed=5)
TABLE_N = 64


def read_channels(path, names):
    with tempfile.TemporaryDirectory() as d:
        pfm = os.path.join(d, "c.pfm")
        subprocess.run([IMGTOOL, "convert", "--channels", ",".join(names), "--outfile", pfm, path], check=True,
                       capture_output=True)
        with open(pfm, "rb") as f:
            f.readline()
            w, h = map(int, f.readline().split())
            scale = float(f.readline())
            a = np.frombuffer(f.read(), "<f4" if scale < 0 else ">f4").reshape(h, w, 3)
    return np.flipud(a).astype(np.float64)


def warp(P, amp, scale, rng):
    out = P.copy()
    for c in range(3):
        acc = np.zeros(len(P))
        for _ in range(3):
            d = rng.normal(size=3)
            d /= np.linalg.norm(d)
            acc += np.sin(P @ d / scale * rng.uniform(0.7, 1.4) + rng.uniform(0, 2 * np.pi))
        out[:, c] += amp * acc / np.sqrt(3)
    return out


def voronoi(P, spacing, table):
    """Per point: the distance to the nearest Voronoi face (3D), and the nearest and second-nearest seeds' table
    indices (the face between them is the edge the point is near)."""
    G = P / spacing
    base = np.floor(G).astype(np.int64)
    best = np.full((len(P), 2), np.inf)
    seeds = np.zeros((len(P), 2, 3))
    cell = np.zeros((len(P), 2, 3), np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + np.array([dx, dy, dz])
                idx = np.mod(c, TABLE_N)
                s = c + table[idx[:, 0], idx[:, 1], idx[:, 2]]
                d2 = np.sum((G - s) ** 2, 1)
                first = d2 < best[:, 0]
                second = ~first & (d2 < best[:, 1])
                best[second, 1], seeds[second, 1], cell[second, 1] = d2[second], s[second], c[second]
                best[first, 1], seeds[first, 1], cell[first, 1] = best[first, 0], seeds[first, 0], cell[first, 0]
                best[first, 0], seeds[first, 0], cell[first, 0] = d2[first], s[first], c[first]
    edge = (best[:, 1] - best[:, 0]) / (2 * np.linalg.norm(seeds[:, 1] - seeds[:, 0], axis=1))
    return edge * spacing, np.mod(cell, TABLE_N)


def factor(gbuf, down, crackle=True):
    P = read_channels(gbuf, ["P.X", "P.Y", "P.Z"])
    N = read_channels(gbuf, ["N.X", "N.Y", "N.Z"])
    H, W, _ = P.shape
    r = np.hypot(P[..., 0], P[..., 1])
    on = (P[..., 2] > 0.01) & (r < 90.0)
    F = np.ones((H, W, 3))
    pts, nrm = P[on], N[on]
    f = np.ones((len(pts), 3))
    rng = np.random.default_rng(FINE["seed"])
    table = rng.uniform(0.0, 1.0, (TABLE_N, TABLE_N, TABLE_N, 3))
    shade = rng.uniform(-1.0, 1.0, (TABLE_N, TABLE_N, TABLE_N))
    strength = rng.uniform(0.0, 1.0, (TABLE_N, TABLE_N, TABLE_N))
    rng2 = np.random.default_rng(PRIMARY["seed"])
    table2 = rng2.uniform(0.0, 1.0, (TABLE_N, TABLE_N, TABLE_N, 3))
    table3 = np.random.default_rng(FINER["seed"]).uniform(0.0, 1.0, (TABLE_N, TABLE_N, TABLE_N, 3))
    for i in range(0, len(pts), 200000):
        p = pts[i:i + 200000]
        d1, c1 = voronoi(warp(p, FINE["warp"], FINE["warp_scale"], np.random.default_rng(11)), FINE["spacing"], table)
        w1 = strength[c1[:, 0, 0], c1[:, 0, 1], c1[:, 0, 2]] * strength[c1[:, 1, 0], c1[:, 1, 1], c1[:, 1, 2]]
        line1 = w1 * np.exp(-0.5 * (d1 / FINE["sigma"]) ** 2)
        d3, c3 = voronoi(warp(p, FINER["warp"], FINER["warp_scale"], np.random.default_rng(13)), FINER["spacing"],
                         table3)
        w3 = strength[c3[:, 0, 0], c3[:, 0, 1], c3[:, 0, 2]] * strength[c3[:, 1, 0], c3[:, 1, 1], c3[:, 1, 2]]
        line1 = np.maximum(line1, (FINER["gain"] / FINE["gain"]) * w3 ** 2 * np.exp(-0.5 * (d3 / FINER["sigma"]) ** 2))
        dark = (shade[c1[:, 0, 0], c1[:, 0, 1], c1[:, 0, 2]] * shade[c1[:, 1, 0], c1[:, 1, 1], c1[:, 1, 2]]
                < -(1 - MARKS["dark_edges"]) * 0.5)
        g = 1.0 + FINE["cell_shade"] * shade[c1[:, 0, 0], c1[:, 0, 1], c1[:, 0, 2]] \
            + np.where(dark, MARKS["dark_gain"], FINE["gain"]) * line1
        d2, c2 = voronoi(warp(p, PRIMARY["warp"], PRIMARY["warp_scale"], np.random.default_rng(12)), PRIMARY["spacing"],
                        table2)
        w2 = 0.3 + 0.7 * strength[c2[:, 0, 0], c2[:, 0, 1], c2[:, 0, 2]] * strength[c2[:, 1, 0], c2[:, 1, 1], c2[:, 1, 2]]
        line2 = w2 * np.exp(-0.5 * (d2 / PRIMARY["sigma"]) ** 2)
        halo = np.exp(-0.5 * (d2 / PRIMARY["halo_sigma"]) ** 2)
        if not crackle:
            g, line2, halo = np.ones_like(g), np.zeros_like(line2), np.zeros_like(halo)
        f[i:i + 200000] = g[:, None] * (1.0 + PRIMARY["gain"] * line2[:, None] * np.array(PRIMARY["tan"])) \
            * (1.0 + PRIMARY["halo_gain"] * halo[:, None])
    # pinholes on the outer wall (normals facing out, away from the axis), between the foot and the lip
    rp = np.random.default_rng(PINHOLES["seed"])
    outer = (np.einsum("ij,ij->i", nrm[:, :2], pts[:, :2]) / np.maximum(np.hypot(pts[:, 0], pts[:, 1]), 1e-6) > 0.3) \
        & (pts[:, 2] > 8.0) & (pts[:, 2] < 27.0) & (pts[:, 1] < 0)
    cand = np.flatnonzero(outer)
    if len(cand):
        for j in rp.choice(cand, PINHOLES["n"], replace=False):
            d = np.linalg.norm(pts - pts[j], axis=1)
            rad = rp.uniform(*PINHOLES["radius"])
            f *= (1.0 + PINHOLES["gain"] * np.exp(-0.5 * (d / rad) ** 2)
                  + PINHOLES["rim"] * np.exp(-0.5 * ((d - 1.6 * rad) / (0.4 * rad)) ** 2))[:, None]
    # the foot: rust-brown patches along the bottom of the ring, a pale band at the very bottom
    rm = np.random.default_rng(MARKS["seed"])
    phi = np.arctan2(pts[:, 1], pts[:, 0])
    patch = sum(np.sin(k * phi + rm.uniform(0, 2 * np.pi)) * rm.normal() / k ** 0.6 for k in range(3, 40))
    patch = (patch - np.quantile(patch, 1 - MARKS["rust_cover"])) / patch.std()
    rust = np.clip(patch * 3.0, 0, 1) * np.clip((MARKS["foot_z"] - pts[:, 2]) / 0.8, 0, 1)
    f *= 1 + rust[:, None] * (np.array(MARKS["rust"]) - 1)
    band = np.clip((MARKS["band_z"] - pts[:, 2]) / 0.3, 0, 1) * (1 - rust)
    f *= 1 + band[:, None] * (np.array(MARKS["band"]) - 1)
    # the lip: thin glaze over the warm body, paler
    lip = np.clip(1 - (pts[:, 2].max() - pts[:, 2]) / MARKS["lip_mm"], 0, 1)
    f *= 1 + lip[:, None] * (np.array(MARKS["lip"]) - 1)
    # uneven tone (the glaze's thickness): a smooth field on the surface
    f *= (1 + MARKS["mottle"] * np.tanh(warp(np.zeros_like(pts), 1.0, MARKS["mottle_scale"], rm)[:, 0] * 0
                                        + np.sin(warp(pts, 3.0, MARKS["mottle_scale"], rm) @ rm.normal(size=3)
                                                 / MARKS["mottle_scale"])))[:, None]
    F[on] = f
    # average down to the render's resolution (the edge pixels mix the factor with the ground's 1)
    F = F[:H // down * down, :W // down * down].reshape(H // down, down, W // down, down, 3).mean((1, 3))
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gbuf")
    ap.add_argument("--down", type=int, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview")
    ap.add_argument("--no-crackle", action="store_true", help="the cracks are rendered (cracks.py): leave them out")
    a = ap.parse_args()
    F = factor(a.gbuf, a.down, not a.no_crackle)
    np.save(a.out, F.astype(np.float32))
    if a.preview:
        from PIL import Image
        Image.fromarray((np.clip(F * 0.5, 0, 1) * 255).astype(np.uint8)).save(a.preview)
    print(f"factor {F.shape}: min {F.min():.3f} max {F.max():.3f}")


if __name__ == "__main__":
    main()
