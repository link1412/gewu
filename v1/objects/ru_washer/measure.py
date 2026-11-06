"""Edges of the Ru washer in the Cleveland Museum of Art's photo (1957.40, CC0, Gary Kirchenbauer; reference only):
the points the profile and the camera are fitted to (form.py).

    python3 -I objects/ru_washer/measure.py [ref/ru/photos/cma_1957.40.jpg] [out/ru/washer/edges.json]

The photo is a side view at a low elevation on a black backdrop over a grey ground cloth; the washer's lower left
is in its own shadow. Sets of edge points, in the photo's pixels (x right, y down, pixel centres at integers):
- outline_top: the back of the rim against the black backdrop, column by column (dark -> bright, going down);
- outline_side: the left and right outline, row by row, where it is steeper than 45 deg;
- outline_bottom: the lower outline (the lower wall and the foot ring against the ground), column by column,
  where it is flatter than 45 deg;
- lip_front: the front of the lip, where it hides the far inner wall: the glaze there is green (G - R ~ 11) and the
  thin glaze on the lip is not (G - R ~ 0); the edge is the steepest drop of G - R going down;
- foot_top: the front of the foot ring's upper edge, a thin bright line between the dark lower wall and the dark
  outer face of the ring (a local maximum of luma).
Each edge is placed at sub-pixel precision at an extremum of the derivative (parabola through three samples), as
shots/06-guan/form.py does; on the outline, the outermost strong one (outermost_step). The object mask (for the outline) is luma > 52 or a green tint (G - R > 3.5 after a
3 px blur): the backdrop is ~5, the ground ~45 and neutral, the glaze in the washer's own shadow ~30 but green.
The outline is refined on luma + 3 (G - R), for the same reason.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHOTO = os.path.join(ROOT, "ref/ru/photos/cma_1957.40.jpg")
OUT = os.path.join(ROOT, "out/ru/washer/edges.json")


def parabola(g, k):
    """Sub-sample offset of the extremum of g at index k."""
    if 0 < k < len(g) - 1:
        den = g[k - 1] - 2 * g[k] + g[k + 1]
        if abs(den) > 1e-9:
            return float(np.clip(0.5 * (g[k - 1] - g[k + 1]) / den, -0.5, 0.5))
    return 0.0


def refine(profile, i0, sign, half=8):
    """Sub-pixel position of the steepest step of `profile` (sign +1: rising, -1: falling) within +-half of i0."""
    lo, hi = max(int(i0) - half, 1), min(int(i0) + half + 1, len(profile) - 1)
    g = np.gradient(profile[lo - 1:hi + 1])[1:-1] * sign
    k = int(np.argmax(g))
    return lo + k + parabola(g, k), float(g[k])


def mask_of(rgb):
    L = ndi.gaussian_filter(rgb.mean(2), 1.5)
    gs = ndi.gaussian_filter(rgb[..., 1] - rgb[..., 0], 3.0)
    M = ndi.binary_opening((L > 52) | (gs > 3.5), iterations=2)
    lab, n = ndi.label(M)
    k = int(np.argmax(ndi.sum(M, lab, range(1, n + 1)))) + 1
    return ndi.binary_fill_holes(lab == k)


def outermost_step(profile, i0, inward, outward, thresh):
    """The outline along a line running from the object outwards (`profile`, the boundary of the mask at index i0):
    the outermost local maximum of the fall of the signal, -d/dt, above `thresh` within [i0 - inward, i0 + outward].
    The outermost, not the steepest: towards its limb the lower wall darkens and reflects the ground, a soft band
    inside the true edge (measured: S 83 -> 60 over 20 px, then -> 37 at the edge, row 1350 at the right)."""
    lo, hi = max(int(i0) - inward, 1), min(int(i0) + outward, len(profile) - 2)
    g = -np.gradient(profile[lo - 1:hi + 2])[1:-1]
    peaks = [k for k in range(1, len(g) - 1) if g[k] >= g[k - 1] and g[k] >= g[k + 1] and g[k] > thresh]
    if not peaks:
        return None
    k = peaks[-1]
    return lo + k + parabola(g, k), float(g[k])


def outline(M, S, thresh=3.0):
    """Outline points: columns for the top and bottom, rows for the sides; each kept where its own direction is the
    better conditioned one (the outline's slope from its neighbours under 45 deg)."""
    cols = np.nonzero(M.any(0))[0]
    rows = np.nonzero(M.any(1))[0]
    sets = {"top": [], "bot": [], "left": [], "right": []}
    for x in cols:
        c = np.nonzero(M[:, x])[0]
        col = S[:, x]
        r = outermost_step(col[::-1], len(col) - 1 - c.min(), 15, 25, thresh)     # upwards from inside
        if r:
            sets["top"].append((x, len(col) - 1 - r[0], r[1]))
        r = outermost_step(col, c.max(), 15, 25, thresh)                          # downwards
        if r:
            sets["bot"].append((x, r[0], r[1]))
    for y in rows:
        c = np.nonzero(M[y])[0]
        row = S[y]
        r = outermost_step(row[::-1], len(row) - 1 - c.min(), 15, 25, thresh)     # leftwards
        if r:
            sets["left"].append((len(row) - 1 - r[0], y, r[1]))
        r = outermost_step(row, c.max(), 15, 25, thresh)                          # rightwards
        if r:
            sets["right"].append((r[0], y, r[1]))
    top, bot, left, right = (np.array(sets[k], float) for k in ("top", "bot", "left", "right"))

    def slope(P, along):
        return np.abs(np.gradient(ndi.uniform_filter1d(P[:, 1 - along], 9), P[:, along]))

    return (top[slope(top, 0) < 1.0, :2], np.vstack([left[slope(left, 1) < 1.0, :2], right[slope(right, 1) < 1.0, :2]]),
            bot[slope(bot, 0) < 1.0, :2])


def smooth_inliers(x, y, tol, deg=4, iters=4):
    """Points that lie within tol px of a polynomial y(x) fitted to them (robustly, by repeated rejection)."""
    keep = np.ones(len(x), bool)
    for _ in range(iters):
        c = np.polyfit(x[keep], y[keep], deg)
        keep = np.abs(np.polyval(c, x) - y) < tol
    return keep


def lip_front(rgb, top, x_range):
    """The front of the lip: per column, the steepest drop of G - R (going down) in a window below the rim's back."""
    gr = ndi.gaussian_filter(rgb[..., 1] - rgb[..., 0], 1.5)
    tx, ty = top[:, 0], top[:, 1]
    pts = []
    for x in range(int(x_range[0]), int(x_range[1]), 2):
        yt = float(np.interp(x, tx, ty))
        lo, hi = int(yt + 150), int(yt + 520)
        g = -np.gradient(gr[lo:hi, x])
        k = int(np.argmax(g))
        pts.append((x, lo + k + parabola(g, k), g[k]))
    P = np.array(pts, float)
    P = P[P[:, 2] > 0.8]
    k = smooth_inliers(P[:, 0], P[:, 1], 3.0)
    return P[k, :2]


def foot_top(rgb, bot, x_range):
    """The foot ring's upper edge at the front: the brightest thin line 60-140 px above the lower outline."""
    L = ndi.gaussian_filter(rgb.mean(2), 1.0)
    bx, by = bot[:, 0], bot[:, 1]
    pts = []
    for x in range(int(x_range[0]), int(x_range[1]), 2):
        yb = float(np.interp(x, bx, by))
        lo, hi = int(yb - 140), int(yb - 60)
        p = L[lo:hi, x]
        ridge = p - ndi.uniform_filter1d(p, 15)
        k = int(np.argmax(ridge))
        pts.append((x, lo + k + parabola(ridge, k), ridge[k]))
    P = np.array(pts, float)
    P = P[P[:, 2] > 4]
    k = smooth_inliers(P[:, 0], P[:, 1], 2.5)
    return P[k, :2]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else PHOTO
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    rgb = np.asarray(Image.open(src).convert("RGB"), float)
    M = mask_of(rgb)
    # the outline is placed on luma plus the glaze's green tint: the lower wall turns dark towards its limb, as dark
    # as the ground, but stays green, and the ground is neutral
    S = ndi.gaussian_filter(rgb.mean(2) + 3.0 * (rgb[..., 1] - rgb[..., 0]), 1.0)
    top, side, bot = outline(M, S)
    xs = np.nonzero(M.any(0))[0]
    x0, x1 = float(xs.min()), float(xs.max())
    w = x1 - x0
    lip = lip_front(rgb, top, (x0 + 0.12 * w, x1 - 0.12 * w))
    # the foot ring spans the middle of the lower outline; its upper edge is clear over the lit middle of it
    foot = foot_top(rgb, bot, (x0 + 0.30 * w, x1 - 0.22 * w))
    J = {"photo": os.path.relpath(src, ROOT), "size": [rgb.shape[1], rgb.shape[0]],
         "about": "edge points in photo pixels (x right, y down), objects/ru_washer/measure.py",
         "sets": {k: np.round(v, 2).tolist() for k, v in
                  (("outline_top", top), ("outline_side", side), ("outline_bottom", bot),
                   ("lip_front", lip), ("foot_top", foot))}}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(J, open(out, "w"))
    print(f"outline x {x0:.0f}..{x1:.0f}; points: " + ", ".join(f"{k} {len(v)}" for k, v in J["sets"].items()))


if __name__ == "__main__":
    main()
