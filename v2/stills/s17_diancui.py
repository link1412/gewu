"""Shot 17: diancui (点翠): kingfisher feather set in gilt filigree. The rim of the ornament is the arc.

    python3 -I v2/stills/s17_diancui.py [preview|mid|final]

Built like the real thing (scales are estimates from general knowledge; the barb structure compared with the feather photograph in
ref/peacock/photos, a different bird but the same architecture):
- a gilt plate with a raised wire wall around each small cell, a rope-twisted wire at the rim;
- each cell is one snip of feather glued in, with barbs lying side by side in its own direction, side barbules fishboned off each
  barb. So every cell catches the light differently and the blue runs between turquoise and ultramarine;
- the blue is structural, a coloured reflection, not a pigment: a metal-like surface whose colour is the blue;
- the fine dark line between barbs, a lifted barb here and there, a little loss of feather at the worn corners.
The pattern is ours.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 4.6
R = 8.4  # the rim, cm
RS = 16.0  # the dome of the plate
VIEW = view_dir(-90.0, 40.0)
DIST = 22.0
SEED = 17


def cell_polar(th0, dth, rho0, rho1, lobes=3, inset=0.0):
    """A petal in polar coordinates about the ornament's centre: its foot at rho1 (inner), its scalloped head at rho0 (towards the rim)."""
    t = np.linspace(0, 1, 70)
    half = 0.5 * dth * np.sin(np.pi * (0.05 + 0.95 * t)) ** 0.55 * (1.0 + 0.1 * np.sin(np.pi * t)) * (1.0 - inset)
    th_u = th0 + half
    th_d = th0 - half
    rho = rho1 + (rho0 - rho1) * t
    a = np.concatenate([np.stack([th_u, rho], 1), np.stack([th_d[::-1], rho[::-1]], 1)], 0)
    # scalloped head
    k = np.linspace(-1, 1, len(a))
    a[:, 1] -= 0.0
    return a


def to_xy(a):
    r = R - a[:, 1]
    return np.stack([r * np.sin(a[:, 0]), r * np.cos(a[:, 0])], 1)


def layout():
    """Cells as polygons in cm with their barb direction (radians from +x), in drawing order (later overlaps earlier)."""
    rng = np.random.default_rng(SEED)
    cells = []
    # ring of large petals (innermost, drawn first), then a ring over them, then small ones at the rim
    for rho0, rho1, n_dth, inset in ((1.5, 3.95, 0.3, 0.0), (0.68, 2.0, 0.205, 0.0), (0.24, 0.92, 0.102, 0.0)):
        th = -0.75
        k = 0
        while th < 0.75:
            th_c = th + (0.5 * n_dth if k % 2 else 0.0)
            th_c = th + 0.5 * n_dth
            poly = to_xy(cell_polar(th_c, n_dth * 0.98, rho0, rho1))
            base = np.pi / 2 - th_c  # radial
            cells.append((poly, base + rng.normal(0, 0.45), th_c))
            # inside each petal, a smaller one with its own snip of feather, as the wirework does
            rho_in = rho0 + 0.2 * (rho1 - rho0)
            poly2 = to_xy(cell_polar(th_c, n_dth * 0.56, rho_in, rho1 - 0.02))
            cells.append((poly2, base + rng.normal(0, 0.45), th_c))
            th += n_dth
            k += 1
        # half a step between rings comes from n_dth differing
    return cells


def build(dens):
    pxcm = 430.0 * dens
    X0, X1 = -4.4, 4.4
    Y0, Y1 = 3.7, 8.72
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    X, Y = np.meshgrid(X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
    r = np.hypot(X, Y)
    th = np.arctan2(X, Y)

    cells = layout()
    lab = np.zeros(shape, np.int32)
    for i, (poly, _, _) in enumerate(cells, start=1):
        cv2.fillPoly(lab, [np.round((poly - [X0, Y0]) * pxcm * 16).astype(np.int32)], i, cv2.LINE_8, shift=4)
    n = len(cells) + 1

    # the wire: wherever two cells meet, or a cell meets the ground
    edges = (lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))
    dw = cv2.distanceTransform((~edges).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm
    hw = 0.019
    wire = np.sqrt(np.maximum(1.0 - (dw / hw) ** 2, 0.0))
    twist = 0.5 + 0.5 * np.sin(2 * np.pi * (X * 0.9 + Y * 0.5) / 0.028)
    # the rim: a rope wire, then a plain gold band inside it
    rho = R - r
    rope_in = sstep(0.17, 0.155, rho)
    rope = np.sqrt(np.maximum(1.0 - ((rho - 0.08) / 0.078) ** 2, 0.0))
    rope_tw = 0.5 + 0.5 * np.sin(2 * np.pi * (th * R / 0.052 + rho / 0.1))
    band = sstep(0.17, 0.18, rho) * sstep(0.24, 0.23, rho)

    # --- the feather, cell by cell
    rp = np.random.default_rng(SEED + 1)
    phi = np.array([1.2] + [c[1] for c in cells], np.float32)
    hue = rp.uniform(0, 1, n).astype(np.float32)
    bright = rp.normal(0, 1, n).astype(np.float32)
    wob = 0.0035 * fbm(shape, pxcm, 0.15, 1.2, 2.6, SEED + 2)
    a = X * np.cos(phi[lab] + np.pi / 2) + Y * np.sin(phi[lab] + np.pi / 2) + wob
    along = X * np.cos(phi[lab]) + Y * np.sin(phi[lab])
    S = 0.0185  # barb spacing, cm
    bi = np.floor(a / S)
    fa = a / S - bi
    bar = np.sqrt(np.maximum(1.0 - (2 * fa - 1.0) ** 2, 0.0))
    # barbules: fishbone off each barb
    fish = np.abs(2 * fa - 1.0)
    bul = 0.5 + 0.5 * np.sin(2 * np.pi * (along + fish * S * 0.8) / 0.0075)
    tbl = rp.normal(0, 1, 4096).astype(np.float32)
    per_barb = tbl[np.mod(bi.astype(np.int64), 4096)]
    # dead patches where the feather has rubbed off and the gilt shows
    lost = sstep(0.992, 0.997, rank(fbm(shape, pxcm, 0.03, 0.3, 2.0, SEED + 3)))

    t = (0.65 * hue[lab] + 0.35 * rank(fbm(shape, pxcm, 0.2, 1.5, 2.4, SEED + 4)))[..., None]
    blue = color([0.004, 0.07, 0.68]) * (1 - t) + color([0.002, 0.42, 0.78]) * t
    blue = blue * (0.55 + 0.45 * bar[..., None]) * (0.72 + 0.28 * bul[..., None]) * (1.0 + 0.16 * per_barb[..., None]) * (1.0 + 0.22 * bright[lab][..., None])

    gold = mix(color([1.0, 0.7, 0.27]), color([1.0, 0.77, 0.36]), rank(fbm(shape, pxcm, 0.03, 0.4, 2.0, SEED + 5)))
    feather = (lab > 0) & (wire < 0.05)
    g = np.maximum(np.maximum(wire, rope_in.astype(np.float32)), band)
    g = np.maximum(g, lost)
    gg = sstep(0.0, 0.2, g)
    col = mix(blue, gold, gg)
    metal = 0.7 + 0.3 * gg
    rough = (0.3 + 0.1 * sstep(-1, 1, per_barb)) * (1 - gg) + (0.16 + 0.1 * rank(fbm(shape, pxcm, 0.02, 0.3, 1.8, SEED + 6))) * gg

    h = (0.0045 * bar + 0.0007 * bul + 0.0009 * per_barb) * (1 - gg)
    h = h + 0.022 * wire * (0.85 + 0.15 * twist)
    h = h + rope_in * (0.05 * rope * (0.82 + 0.18 * rope_tw)) + band * 0.012
    # slow dents, handled metal
    h = h + 0.008 * fbm(shape, pxcm, 0.5, 3.0, 2.8, SEED + 7)
    z = -(r**2) / (2 * RS)
    edge = sstep(-0.0, 0.08, r - R)
    z = z - edge * 0.6 + h
    P = np.stack([X, Y, z], -1).astype(np.float32)
    alpha = sstep(0.012, 0.0, r - R)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), metal.astype(np.float32), alpha.astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.55, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s17_diancui")
    os.makedirs(d, exist_ok=True)
    xx, yy = np.linspace(-4.4, 4.4, 500, dtype=np.float32), np.linspace(3.7, 8.72, 500, dtype=np.float32)
    Xc, Yc = np.meshgrid(xx, yy)
    rc = np.hypot(Xc, Yc)
    Pc = np.stack([Xc, Yc, -(rc**2) / (2 * RS)], -1)
    keep = rc < R
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Xc.shape), y.reshape(Xc.shape)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.64) ** 2) + 10 * (~keep))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=2.4, focus_point=focus)
    P, C, Ro, Me, A = build(dens)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=Me, alpha=A)
    nrm = np.stack([Xc / RS, Yc / RS, np.ones_like(Xc)], -1)
    j = np.nanargmin(((x - 0.47) ** 2 + (y - 0.68) ** 2) + 10 * (~keep))
    lw, _ = reflect_light_loc(Pc.reshape(-1, 3)[j], nrm.reshape(-1, 3)[j], cam, 50.0)
    lights = [
        {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": Pc.reshape(-1, 3)[j].tolist(), "size": [130, 100], "sigma": [34, 15], "L": 1.35, "rgb": [1.0, 0.98, 0.94]},
        {"name": "rake", "loc": (focus + np.array([-22, 20, 12])).tolist(), "target": focus.tolist(), "size": [5, 5], "watts": 5000, "rgb": [1.0, 0.94, 0.84]},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "ornament", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Alpha": "alpha"}}],
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 2,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s17_diancui", scene, q, develop={"exposure": 0.0, "contrast": 1.28, "saturation": 1.12, "black": 0.0012, "grain": 1.15, "sharpen": 0.3, "halation": 0.05, "glare": 0.004, "vignette": 0.4})


main()
