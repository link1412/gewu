"""The neutral veil test (docs/materials/yanzhi.md, round 2, "why too saturated"): across the photo's red wall, away
from the side sheen, is each pixel E_i x m (one colour, scaled by the light) or E_i x m + k (plus a neutral veil, the
same everywhere: the glaze reflecting a roughly uniform surround, or the lens's flare)? With a veil the dim pixels are
less saturated than the bright ones; without it the chromaticity is flat in Y. k is found as the one that makes p - k
most nearly collinear (smallest second singular value), on the pixels below a luminance cut (the side sheen excluded).

    python3 -I materials/yanzhi/lightfit/veil.py [IMAGE: photo (default) | path to a render dir with x.exr] [--ycut 0.07]
"""
import argparse
import os
import sys

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import card  # noqa: E402

LUM = np.array([0.2126, 0.7152, 0.0722])


def wall_pixels(lin, name):
    box, info = card.regions(lin, name)
    w = card.median_box(lin, box["white"])
    x = lin / w
    sm = ndi.gaussian_filter(lin, (2, 2, 0))
    R, G = sm[..., 0], sm[..., 1]
    red = ndi.binary_erosion((R > 2 * G) & (R > 0.004 * np.percentile(R, 99.5)), iterations=max(2, int(info["width"] / 90)))
    rt, rb = info["red_top"], info["red_bot"]
    red[:rt + int(0.12 * (rb - rt))] = 0          # the lip's flare band
    red[int(rt + 0.8 * (rb - rt)):] = 0           # the foot
    return x[red]


def veil(p, ycut):
    q = p[(p @ LUM) < ycut]
    ks = np.linspace(0, 0.03, 301)
    s2 = []
    for k in ks:
        sv = np.linalg.svd(q - k, compute_uv=False)
        s2.append(sv[1] / sv[0])
    k = ks[int(np.argmin(s2))]
    u = np.linalg.svd(q - k, full_matrices=False)[2][0]
    u = u if u[0] > 0 else -u
    return k, u, min(s2), s2[0], len(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?", default="photo")
    ap.add_argument("--raw", default="x.exr")
    ap.add_argument("--ycut", type=float, default=0.07)
    a = ap.parse_args()
    lin = card.photo_linear() if a.image == "photo" else card.render_linear(a.image, a.raw)
    p = wall_pixels(lin, a.image)
    k, u, s, s0, n = veil(p, a.ycut)
    Y = p @ LUM
    mid = p[(Y > np.quantile(Y, 0.4)) & (Y < np.quantile(Y, 0.6))].mean(0)
    E = float((mid - k) @ u / (u @ u))
    pure = E * u
    for nm, v in (("as seen (median band)", mid), ("veil removed", pure)):
        L = card.lab_of(v)
        print(f"{nm:22s} L*a*b* {L[0]:5.1f} {L[1]:5.1f} {L[2]:5.1f}  C {np.hypot(L[1], L[2]):5.1f} "
              f"h {np.degrees(np.arctan2(L[2], L[1])):5.1f}")
    print(f"{a.image}: {n} px under Y {a.ycut}; veil k {k:.4f} of the white (residual s2/s1 {s:.4f}, {s0:.4f} with k 0)")


if __name__ == "__main__":
    main()
