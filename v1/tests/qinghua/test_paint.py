"""Checks of crafts/painting/paint.py: a straight stroke's width and load, a wash's grading and rim, the firing's
mass and spread, and a sample motif written as a picture (out/qinghua/paint/).

    python3 -I tests/qinghua/test_paint.py
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qh  # noqa: E402

sys.path.insert(0, os.path.join(qh.ROOT, "crafts/painting"))
import paint  # noqa: E402

PX = 50.0                      # px per mm


def check(name, ok, detail):
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    return ok


def main():
    good = True
    # a straight stroke along x at y = 2, 0.4 mm wide, c 3
    cv = paint.Canvas((0, 20), (0, 4), PX)
    cv.stroke([(2, 2), (18, 2)], 0.4, 3.0, edge_mm=0.03)
    col = cv.c[:, np.searchsorted(cv.xs, 10)]
    half = col.max() / 2
    fwhm = (col > half).sum() / PX
    good &= check("stroke width", abs(fwhm - 0.4) < 0.04, f"FWHM {fwhm:.3f} mm for 0.4 (edge 0.03)")
    p = paint.params()
    a, b = (cv.c[:, np.searchsorted(cv.xs, x)].max() for x in (4, 14))
    want = (1 - p["load_drop"] * 12 / 16) / (1 - p["load_drop"] * 2 / 16)      # arc length 2 and 12 mm of 16
    good &= check("load", abs(b / a / want - 1) < 0.01, f"c at x 14 / x 4 = {b / a:.3f} (want {want:.3f})")
    tip = cv.c[:, np.searchsorted(cv.xs, 17.99)].max()
    good &= check("lift", tip < 0.2 * a, f"c at the tip {tip:.3f} vs {a:.3f}")

    # a wash, graded 0.4 -> 1.6 along x over a rectangle
    cv = paint.Canvas((0, 20), (0, 10), PX)
    cv.wash([(2, 2), (18, 2), (18, 8), (2, 8)], 0.4, 1.6, direction=(1, 0), mottle=0.0, rim=0.25, rim_mm=0.3)
    row = cv.c[np.searchsorted(cv.ys, 5)]
    c5, c15 = row[np.searchsorted(cv.xs, 5)], row[np.searchsorted(cv.xs, 15)]
    good &= check("wash grading", abs(c5 - (0.4 + 1.2 * 3 / 16)) < 0.02 and abs(c15 - (0.4 + 1.2 * 13 / 16)) < 0.02,
                  f"c(5) {c5:.3f} c(15) {c15:.3f}")
    rimv = row[np.searchsorted(cv.xs, 2.06)]
    good &= check("rim", rimv > 0.4 * 1.1, f"c 0.06 mm inside the edge {rimv:.3f} vs 0.4 + rim")
    levels = np.unique(np.round(cv.c[cv.c > 0], 4)).size
    good &= check("continuous", levels > 100, f"{levels} distinct levels")

    # firing: mass kept, the step's 10-90 width = 2.563 sigma
    m0 = cv.c.sum()
    cv.fire(60)
    good &= check("fire mass", abs(cv.c.sum() / m0 - 1) < 1e-6, f"sum ratio {cv.c.sum() / m0:.8f}")
    cv = paint.Canvas((0, 4), (0, 1), 200.0)
    cv.c[:, cv.xs > 2] = 1.0
    cv.fire(60)
    r = cv.c[0]
    w = (np.argmax(r > 0.9) - np.argmax(r > 0.1)) / 200.0
    good &= check("fire spread", abs(w - 2.563 * 0.060) < 0.006, f"10-90% {w * 1000:.0f} um for sigma 60 um")

    # a motif: a leaf outlined and washed, a stem, a few strokes; the picture as the film would show it
    cv = paint.Canvas((0, 30), (0, 20), 40.0)
    t = np.linspace(0, np.pi, 60)
    leaf = np.stack([6 + 18 * t / np.pi, 10 + 5 * np.sin(t) ** 1.2], 1)
    leaf = np.concatenate([leaf, np.stack([6 + 18 * t[::-1] / np.pi, 10 - 4 * np.sin(t[::-1]) ** 1.2], 1)])
    cv.wash(leaf, 0.3, 1.4, direction=(1, 0.3), seed=1)
    cv.stroke(leaf[:60], 0.35, 3.0, seed=2, wobble=0.15)
    cv.stroke(leaf[60:], 0.35, 3.0, seed=3, wobble=0.15)
    cv.stroke(np.stack([6 + 18 * t / np.pi, 10 + 0.6 * np.sin(t)], 1)[5:55], 0.25, 2.5, seed=4)
    cv.stroke([(2, 3), (6, 10)], 0.5, 3.0, seed=5)
    cv.fire(40)
    d = os.path.join(qh.OUT, "paint")
    os.makedirs(d, exist_ok=True)
    cv.save_map(f"{d}/leaf_c.pfm")
    sys.path.insert(0, os.path.join(qh.ROOT, "materials/qinghua"))
    import optics
    from camera import Spectra, blackbody
    S = Spectra("canon_eos_5d_mkiv")
    w = S.sens * blackbody(5500.0)
    k = optics.cobalt_kappa()
    cg = np.linspace(0, 6, 61)
    rgb = np.array([(w @ optics.stack(c * k, np.full(k.shape, 0.85), 1.52)[0]) / w.sum(1) for c in cg])
    rgb /= rgb[0]
    img = np.stack([np.interp(np.clip(cv.c, 0, 6), cg, rgb[:, i]) for i in range(3)], -1)[::-1]
    img = np.where(img < 0.0031308, 12.92 * img, 1.055 * np.clip(img, 0, 1) ** (1 / 2.4) - 0.055)
    q = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                    f"{cv.W}x{cv.H}", "-i", "-", f"{d}/leaf_preview.png"], input=q.tobytes(), check=True)
    print(f"motif -> {d}/leaf_c.pfm, {d}/leaf_preview.png (1-D stack, camera RGB / white, no white balance)")
    print("all ok" if good else "SOME CHECKS FAILED")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
