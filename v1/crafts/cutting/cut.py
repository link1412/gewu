"""The cut (crafts/cutting/cutting.json): the relief of a knife's cut through the lychee's aril, as a height map on
the cut face for a bump ("texture displacement", mm).

    h = juice-levelled cell bowls, plus the flesh's slump, plus the juice sacs' domes, plus beads of juice, inside
        the aril's ring on the cut plane, 0 elsewhere.

- Cells: a jittered grid of centres d_c apart; e = (d2 - d1)/2 the distance to the cell's wall; the opened lumen
  is a bowl -depth (1 - (1 - e/e_max)^2), 0 at the walls.
- Juice: the film levels the relief finer than its thickness: a Gaussian.
- Slump: the soft flesh relaxes unevenly after the cut: Gaussian-filtered noise of a wavelength and rms.
- Sacs: the groups of juice cells between the aril's membranes swell into the face as low domes (a coarser cell
  pattern, b (1 - (1 - e/e_max)^k)), the membranes creases between them.
- Beads: spherical caps (footprint radius r, contact angle a: height r tan(a/2)) sitting on the face's mean level
  under them, the higher of bead and face.
- The ring: between the aril's outer cut (the envelope's radius at the cut minus pericarp and gap: the layers are
  offset radially in the cut plane, objects/lychee/lychee.py) and its inner cut (the seed's ellipse grown by the
  gap), with the relief tapered to 0 at both edges. The texture's square is the object's [-extent, extent]^2 with
  planar UVs; its border is 0, where the aril's other faces map (lychee.ZERO_UV).
"""
import json
import math
import os

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
BORDER = 0.02                 # of the texture's side kept 0 (ZERO_UV sits in it)


def v(d):
    return d["value"] if isinstance(d, dict) and "value" in d else d


def load(path=os.path.join(HERE, "cutting.json")):
    return json.load(open(path))


def write_pfm(path, a):
    """(H, W) float, row 0 the top (v = 1 - row/H as pbrt and Blender read it); PFM stores the bottom row first."""
    a = np.asarray(a, "<f4")
    with open(path, "wb") as f:
        f.write(b"Pf\n" + f"{a.shape[1]} {a.shape[0]}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(a[::-1]).tobytes())


def ring_mask(X, Y, B):
    """Inside the aril's ring on the cut plane (X, Y in the fruit's frame, mm), from the object's Builder."""
    F = B.F
    P, _ = F.envelope(np.array(B.th0), np.array(0.0))
    r_out = float(np.hypot(P[0], P[1])) - B.t_peri - B.g_pa
    A = B.seed_axes + B.g_as
    ts = math.acos((B.cut_z - B.seed_z) / A[2])
    ea, eb = A[0] * math.sin(ts), A[1] * math.sin(ts)
    outer = np.hypot(X, Y) < r_out
    inner = (X / ea) ** 2 + (Y / eb) ** 2 < 1
    return outer & ~inner, (r_out, ea, eb)


def relief(p, n, px_mm, rng):
    """The juice-levelled cell bowls on an n x n grid of px_mm pixels (mm)."""
    dc = v(p["cell_diameter_mm"])
    side = n * px_mm
    m = int(math.ceil(side / dc)) + 2
    gx, gy = np.meshgrid(np.arange(m), np.arange(m), indexing="ij")
    C = (np.stack([gx, gy], -1).reshape(-1, 2) + rng.uniform(-0.45, 0.45, (m * m, 2))) * dc - dc
    tree = cKDTree(C)
    x = (np.arange(n) + 0.5) * px_mm
    X, Y = np.meshgrid(x, x, indexing="xy")
    d, _ = tree.query(np.stack([X.ravel(), Y.ravel()], -1), k=2)
    e = np.clip((d[:, 1] - d[:, 0]) / 2 / (0.5 * dc), 0, 1).reshape(n, n)
    h = -v(p["cell_depth_mm"]) * (1 - (1 - e) ** 2)
    h = gaussian_filter(h, v(p["juice_level_sigma_mm"]) / px_mm, mode="wrap")
    s = p["slump"]
    w = gaussian_filter(rng.standard_normal((n, n)), v(s["wavelength_mm"]) / 4 / px_mm, mode="wrap")
    return h + w * (v(s["rms_mm"]) / w.std()) + sacs(p, n, px_mm, rng)


def sacs(p, n, px_mm, rng):
    """The juice-cell groups as low domes, the membranes between them as creases (mm), on the same grid."""
    q = p.get("sacs")
    if not q:
        return 0.0
    ds = v(q["size_mm"])
    m = int(math.ceil(n * px_mm / ds)) + 2
    gx, gy = np.meshgrid(np.arange(m), np.arange(m), indexing="ij")
    C = (np.stack([gx, gy], -1).reshape(-1, 2) + rng.uniform(-1, 1, (m * m, 2)) * v(q["jitter"])) * ds - ds
    tree = cKDTree(C)
    x = (np.arange(n) + 0.5) * px_mm
    X, Y = np.meshgrid(x, x, indexing="xy")
    d, i = tree.query(np.stack([X.ravel(), Y.ravel()], -1), k=2)
    dd, _ = tree.query(C, k=2)
    emax = 0.5 * dd[:, 1]
    e = np.clip((d[:, 1] - d[:, 0]) / 2 / emax[i[:, 0]], 0, 1).reshape(n, n)
    return v(q["bulge_mm"]) * (1 - (1 - e) ** v(q["profile_power"]))


def write_cut_texture(path, B, p, seed=0):
    """The cut face's height map for the object's Builder B (its extent, cut, layers); returns a summary."""
    rng = np.random.default_rng([seed, 7])
    n = int(v(p["texture_px"]))
    ext = B.extent
    px = 2 * ext / n
    # pixel centres in the fruit's frame: column -> x, row 0 the top -> v = 1 -> y = +ext (planar UV: (xy + ext) / 2ext)
    c = (np.arange(n) + 0.5) * px - ext
    X, Y = np.meshgrid(c, c[::-1], indexing="xy")
    ring, (r_out, ea, eb) = ring_mask(X, Y, B)
    h = relief(p, n, px, rng)
    # beads
    dens = v(p["droplets"]["per_mm2"])
    area = math.pi * r_out ** 2 - math.pi * ea * eb
    nb = rng.poisson(dens * area)
    rlo, rhi = v(p["droplets"]["radius_mm"])
    ang = math.radians(v(p["droplets"]["contact_angle_deg"]))
    beads = 0
    for _ in range(nb * 20):
        if beads >= nb:
            break
        x0, y0 = rng.uniform(-r_out, r_out, 2)
        r = math.exp(rng.uniform(math.log(rlo), math.log(rhi)))
        if not (math.hypot(x0, y0) < r_out - r and (x0 / ea) ** 2 + (y0 / eb) ** 2 > (1 + r / min(ea, eb)) ** 2):
            continue
        R = r / math.sin(ang)                                  # the cap's sphere
        top = R * (1 - math.cos(ang))
        i0, i1 = max(int((ext - y0 - r) / px) - 1, 0), min(int((ext - y0 + r) / px) + 2, n)      # rows: y down
        j0, j1 = max(int((x0 + ext - r) / px) - 1, 0), min(int((x0 + ext + r) / px) + 2, n)
        q = (X[i0:i1, j0:j1] - x0) ** 2 + (Y[i0:i1, j0:j1] - y0) ** 2
        cap = np.sqrt(np.maximum(R * R - q, 0)) - (R - top)
        win = h[i0:i1, j0:j1]
        win[:] = np.where(q < r * r, np.maximum(win, win.mean() + cap), win)    # on the face's local level
        beads += 1
    # taper to 0 at the ring's edges, 0 outside it
    dist = distance_transform_edt(ring) * px
    h = h * np.clip(dist / v(p["edge_taper_mm"]), 0, 1)
    b = int(math.ceil(BORDER * n))
    h[:b], h[-b:], h[:, :b], h[:, -b:] = 0, 0, 0, 0
    write_pfm(path, h.astype(np.float32))
    return {"file": os.path.basename(path), "px": n, "mm_per_px": px, "extent_mm": ext, "ring_mm": [r_out, ea, eb],
            "beads": beads, "h_min_mm": float(h.min()), "h_max_mm": float(h.max())}
