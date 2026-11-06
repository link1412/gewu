"""Painting (画) cobalt under a glaze: brush strokes and washes -> the cobalt's column density c(x, y), g CoO per m^2
of the glaze-body boundary, the map materials/qinghua's film reads (docs/crafts/painting.md).

The craft, as Jingdezhen painters describe it (the laws below are ours, [A], none measured; craft.json):
- 勾线 (outlining): a fine brush draws the lines in concentrated pigment. A stroke lands, presses to its full width,
  and lifts to a point; it carries a load that thins as it goes, so its c falls along the stroke; its edge is
  soft over the bristles' spread. One pass of the brush deposits once: within a stroke, overlap takes the max.
- 分水 (graded washing): a full brush pushes a pool of diluted pigment across the shape the lines enclose; c is
  continuous, graded from where the pool starts to where it ends (not quantized to the workshop's 5, 7 or 9 named
  tones), with a band of extra pigment along the pool's edge where it dries last, and a slow mottle.
- Separate passes add their pigment: c sums across strokes and washes.
- 烧 (firing): the cobalt diffuses into the glaze around it; a Gaussian blur of sigma bleed_um
  (materials/qinghua/material.json).

Coordinates: mm. The grid is x0 + (i + 0.5) * step, y0 + (j + 0.5) * step; arrays are indexed [j, i], row 0 at y0
(the bottom), as crafts/carving. save_map() writes an image (row 0 the top) for pbrt's imagemap and familymap.
"""
import json
import os

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))


def params():
    """craft.json's values by name."""
    j = json.load(open(os.path.join(HERE, "craft.json")))
    return {k: v["value"] for k, v in j["params"].items()}


def _smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _polyline(P, step):
    """Resample a polyline at ~step: points (n, 2), arc length s (n,), unit tangents (n, 2)."""
    P = np.asarray(P, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s0 = np.concatenate([[0], np.cumsum(seg)])
    n = max(int(np.ceil(s0[-1] / step)) + 1, 2)
    s = np.linspace(0, s0[-1], n)
    Q = np.stack([np.interp(s, s0, P[:, 0]), np.interp(s, s0, P[:, 1])], 1)
    t = np.gradient(Q, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    return Q, s, t


def _inside(P, X, Y):
    """Even-odd test of points against the closed polygon P (n, 2)."""
    P = np.asarray(P, float)
    A, B = P, np.roll(P, -1, 0)
    x, y = X[..., None], Y[..., None]
    c = ((A[:, 1] > y) != (B[:, 1] > y)) & (
        x < A[:, 0] + (y - A[:, 1]) * (B[:, 0] - A[:, 0]) / np.where(B[:, 1] == A[:, 1], 1e-18, B[:, 1] - A[:, 1]))
    return (c.sum(-1) % 2) == 1


class Canvas:
    def __init__(self, x, y, px_per_mm):
        (self.x0, self.x1), (self.y0, self.y1) = x, y
        self.step = 1.0 / px_per_mm
        self.W = int(round((self.x1 - self.x0) * px_per_mm))
        self.H = int(round((self.y1 - self.y0) * px_per_mm))
        self.xs = self.x0 + (np.arange(self.W) + 0.5) * self.step
        self.ys = self.y0 + (np.arange(self.H) + 0.5) * self.step
        self.c = np.zeros((self.H, self.W))

    # --- 勾线 -------------------------------------------------------------------------------
    def stroke(self, path, width_mm, c, land_mm=None, lift_mm=None, load_drop=None, edge_mm=None, wobble=0.0,
               seed=0):
        """One brush stroke along `path` ((n, 2) mm): full width `width_mm`, c at its start `c` (g/m^2).
        It widens from 40% over `land_mm`, tapers to a point over `lift_mm`, its c falls linearly by `load_drop`
        (a fraction) from start to end, and its edge softens over `edge_mm`; `wobble` (a fraction) varies the width
        slowly (the hand). Defaults from craft.json."""
        p = params()
        land_mm = p["land_mm"] if land_mm is None else land_mm
        lift_mm = p["lift_mm"] if lift_mm is None else lift_mm
        load_drop = p["load_drop"] if load_drop is None else load_drop
        edge_mm = p["edge_mm"] if edge_mm is None else edge_mm
        Q, s, _ = _polyline(path, self.step / 2)
        L = max(s[-1], 1e-9)
        w = width_mm * (0.4 + 0.6 * _smoothstep(s / max(land_mm, 1e-9)))
        w = w * _smoothstep((L - s) / max(lift_mm, 1e-9)) ** 0.5
        if wobble:
            rng = np.random.default_rng(seed)
            k = rng.normal(size=len(s))
            k = ndi.gaussian_filter1d(k, max(1.0, 3.0 / (self.step / 2)), mode="nearest")
            w = w * (1 + wobble * k / max(k.std(), 1e-9))
        cs = c * (1 - load_drop * s / L)
        r = w / 2 + edge_mm
        x0, x1 = Q[:, 0].min() - r.max(), Q[:, 0].max() + r.max()
        y0, y1 = Q[:, 1].min() - r.max(), Q[:, 1].max() + r.max()
        i0, i1 = np.searchsorted(self.xs, [x0, x1])
        j0, j1 = np.searchsorted(self.ys, [y0, y1])
        if i1 <= i0 or j1 <= j0:
            return
        dep = np.zeros((j1 - j0, i1 - i0))
        for k in range(0, len(Q), 64):             # one pass: the max over the brush's positions
            qx, qy, rk = Q[k:k + 64, 0], Q[k:k + 64, 1], r[k:k + 64].max()
            a0, a1 = np.searchsorted(self.xs, [qx.min() - rk, qx.max() + rk])
            b0, b1 = np.searchsorted(self.ys, [qy.min() - rk, qy.max() + rk])
            a0, a1, b0, b1 = max(a0, i0), min(a1, i1), max(b0, j0), min(b1, j1)
            if a1 <= a0 or b1 <= b0:
                continue
            X, Y = np.meshgrid(self.xs[a0:a1], self.ys[b0:b1])
            d = np.sqrt((X[..., None] - qx) ** 2 + (Y[..., None] - qy) ** 2)
            prof = _smoothstep((w[k:k + 64] / 2 + edge_mm / 2 - d) / max(edge_mm, 1e-9))
            sub = dep[b0 - j0:b1 - j0, a0 - i0:a1 - i0]
            np.maximum(sub, (prof * cs[k:k + 64]).max(-1), out=sub)
        self.c[j0:j1, i0:i1] += dep

    # --- 分水 -------------------------------------------------------------------------------
    def wash(self, polygon, c_start, c_end=None, direction=(1.0, 0.0), rim=None, rim_mm=None, mottle=None,
             mottle_mm=None, edge_mm=None, seed=0):
        """A wash over the closed `polygon` ((n, 2) mm): c graded linearly from `c_start` to `c_end` along
        `direction` across the polygon's extent; a rim of extra pigment, `rim` (a fraction) at the edge falling off
        over `rim_mm`; a mottle of relative amplitude `mottle` at scale `mottle_mm`; an edge soft over `edge_mm`.
        Defaults from craft.json."""
        p = params()
        c_end = c_start if c_end is None else c_end
        rim = p["rim"] if rim is None else rim
        rim_mm = p["rim_mm"] if rim_mm is None else rim_mm
        mottle = p["mottle"] if mottle is None else mottle
        mottle_mm = p["mottle_mm"] if mottle_mm is None else mottle_mm
        edge_mm = p["wash_edge_mm"] if edge_mm is None else edge_mm
        P = np.asarray(polygon, float)
        pad = 2 * self.step
        i0, i1 = np.searchsorted(self.xs, [P[:, 0].min() - pad, P[:, 0].max() + pad])
        j0, j1 = np.searchsorted(self.ys, [P[:, 1].min() - pad, P[:, 1].max() + pad])
        if i1 <= i0 or j1 <= j0:
            return
        X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])         # the polygon's box only
        inside = _inside(P, X, Y)
        if not inside.any():
            return
        dist_in = ndi.distance_transform_edt(np.pad(inside, 1)) [1:-1, 1:-1] * self.step   # mm to the edge, inside
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        proj = X * d[0] + Y * d[1]
        pp = P @ d
        t = np.clip((proj - pp.min()) / max(pp.max() - pp.min(), 1e-9), 0, 1)
        c = c_start + (c_end - c_start) * t
        c = c * (1 + rim * np.exp(-dist_in / max(rim_mm, 1e-9)))
        if mottle:
            rng = np.random.default_rng(seed)
            n = ndi.gaussian_filter(rng.normal(size=c.shape), mottle_mm / self.step, mode="wrap")
            c = c * np.clip(1 + mottle * n / max(n.std(), 1e-12), 0, None)
        c = c * _smoothstep(dist_in / max(edge_mm, 1e-9) + 0.5)
        self.c[j0:j1, i0:i1] += np.where(inside, c, 0.0)

    # --- 烧 ---------------------------------------------------------------------------------
    def fire(self, bleed_um):
        """The firing's lateral spread: a Gaussian of sigma bleed_um. Mass is kept (sum c unchanged)."""
        if bleed_um > 0:
            self.c = ndi.gaussian_filter(self.c, bleed_um / 1000.0 / self.step, mode="nearest")
        return self

    # --- out --------------------------------------------------------------------------------
    def save_map(self, path):
        """The map as an image for pbrt (row 0 the top: y1), PFM, one channel, c in g/m^2."""
        img = np.ascontiguousarray(self.c[::-1], dtype="<f4")
        H, W = img.shape
        with open(path, "wb") as f:
            f.write(f"Pf\n{W} {H}\n-1.0\n".encode())
            f.write(img[::-1].tobytes())          # PFM stores the bottom row first
        return path
