"""Trace a ginkgo leaf photograph's outline into a leaf config's "outline" (objects/yinxing/leaf.py), in millimetres.

    python3 -I objects/yinxing/trace_ref.py PHOTO --kind lamp|scan --px-per-mm S [--out JSON] [--step-mm 0.1]

The blade: the leaf's mask (measure_ref.leaf_mask) above the junction O (measure_ref.junction: going up the
petiole, the first row wider than 1.5 petiole widths), closed by the straight segment across the junction row (the
"base", where the petiole's bundles enter). The frame is leaf.py's: O at (0, 0), +y up the image (the leaf's axis
as the photo shows it, not rotated), +x to the right, mm = px / S. Writes {"outline": {"polygon_mm": [[x, y], ...]
(counter-clockwise), "base_mm": [[x0, 0], [x1, 0]], "petiole_width_mm", "source", "px_per_mm", "photo_frame": the
photo's size and O in px (for the card's framing)}}.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure_ref as M  # noqa: E402

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--kind", required=True)
    ap.add_argument("--px-per-mm", type=float, required=True)
    ap.add_argument("--px-per-mm-source", required=True, help="where the scale comes from (written into the json)")
    ap.add_argument("--step-mm", type=float, default=0.1)
    ap.add_argument("--out")
    a = ap.parse_args()
    im = np.asarray(Image.open(a.photo).convert("RGB")).astype(float)
    m = M.leaf_mask(im, a.kind)
    pet = M.petiole_axis(m)
    pw = float(np.median(pet[:40, 2]))
    Oxy = M.junction(pet, pw)
    jrow = int(round(Oxy[1]))
    blade = m.copy()
    blade[jrow:] = False
    cs, _ = cv2.findContours(blade.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=len)[:, 0, :].astype(float)
    c[:, 1] = np.minimum(c[:, 1] + 0.5, jrow)              # pixel centres; the base row is the cut
    S = a.px_per_mm
    P = np.stack([(c[:, 0] + 0.5 - Oxy[0]) / S, (jrow - c[:, 1]) / S], 1)
    # light smoothing (the mask's staircase), then resample at step_mm
    k = max(1, int(round(0.15 * S)))
    Pc = np.r_[P[-k:], P, P[:k]]
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    Ps = np.stack([np.convolve(Pc[:, i], ker, "valid") for i in range(2)], 1)
    base = Ps[:, 1] < 1.01 / S                           # the bottom pixel row is the cut
    Ps[base, 1] = 0.0
    seg = np.hypot(*np.diff(np.r_[Ps, Ps[:1]], axis=0).T)
    s = np.r_[0, np.cumsum(seg)]
    t = np.arange(0, s[-1], a.step_mm)
    Q = np.r_[Ps, Ps[:1]]
    poly = np.stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])], 1)
    area2 = np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1])
    if area2 < 0:
        poly = poly[::-1]
    on_base = poly[:, 1] < 1e-9
    bx = poly[on_base, 0]
    out = {"outline": {
        "source": f"traced from {os.path.basename(a.photo)} ({a.kind}) by objects/yinxing/trace_ref.py",
        "px_per_mm": S, "px_per_mm_source": a.px_per_mm_source,
        "polygon_mm": np.round(poly, 4).tolist(),
        "base_mm": [[round(float(bx.min()), 4), 0.0], [round(float(bx.max()), 4), 0.0]],
        "petiole_width_mm": round(pw / S, 3),
        "photo_frame": {"size_px": [int(im.shape[1]), int(im.shape[0])], "O_px": [round(float(Oxy[0]), 2), jrow]}}}
    W = poly[:, 0].max() - poly[:, 0].min()
    print(f"O {Oxy} px; petiole {pw:.1f} px = {pw / S:.2f} mm; blade {W:.1f} x {poly[:, 1].max():.1f} mm; "
          f"base {bx.min():.2f}..{bx.max():.2f} mm; {len(poly)} points")
    if a.out:
        json.dump(out, open(a.out, "w"), indent=0)
        print("->", a.out)


if __name__ == "__main__":
    main()
