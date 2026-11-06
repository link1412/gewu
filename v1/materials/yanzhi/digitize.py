"""Read the measured absorption spectra of a gold-ruby glass out of Takebe, Okamoto & Mori 2021 (J. Ceram. Soc. Jpn.
129(9) 590-593, doi 10.2109/jcersj2.21087; the publisher's PDF, ref/yanzhi/research/sources/Takebe_2021.pdf), Fig. 6: 1 mm thick soda-lime solar-panel glass with 0.014 mass% Au2O3
added (their text), struck at 580/600/620/680 C for 10 days; Hitachi U-4100, nine positions per sample, 400-700 nm
plotted [M]. The figure is a raster image inside the PDF (page 4, 2374 x 1325, an Adobe CMYK JPEG: stored
inverted, 255 = no ink). A pixel's ink is the sum over the four channels of 255 - value. The nine curves of a panel
overlap; per column the inked pixels are taken, and their median, 10th and 90th percentile rows give a central
curve and a spread [D, read off a figure, about 0.33 nm and 0.005 absorbance per pixel].

Axis calibration from the panel's own ticks (inked marks inside the frame): x from the frame's ends (400 and
700 nm) and the five major ticks between (uniform to about 1 px); y from the 0 and 1.0 ticks. Panel (c)'s "2.0" sits 8% closer to
1.0 than 1.0 does to 0 (the other panels are uniform to 1 px); the 0 and 1.0 ticks are used, so the curve's ratios
(what the model is checked on) do not depend on it.

    python3 -I materials/yanzhi/digitize.py ref/yanzhi/research/sources/Takebe_2021.pdf
    -> materials/yanzhi/data/takebe2021_fig6.csv (lambda_nm, then per panel a-d: median, p10, p90 absorbance)
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PANELS = {"a": (0, 0), "b": (0, 1187), "c": (660, 0), "d": (660, 1187)}   # (row, column) offsets of the panels
PEAKS = {"a": "521+-7", "b": "526+-5", "c": "533+-2", "d": "544+-2"}       # the figure's labels, nm


def panel(g, oy, ox):
    sub = g[oy:oy + 665, ox:ox + 1187]
    rows = np.where((sub > 400).sum(1) > 500)[0]
    cols = np.where((sub > 400).sum(0) > 300)[0]
    top, bot, left, right = rows.min(), rows.max(), cols.min(), cols.max()
    tick = (sub[:, left + 3:left + 18] > 400).sum(1) >= 12                 # y ticks: marks inside the left frame
    ty = np.where(tick)[0]
    groups = np.split(ty, np.where(np.diff(ty) > 2)[0] + 1)
    # the 0 tick is the last group (on the bottom frame); the curves also cross the tick zone near 400 nm, so the 1.0
    # tick is the group of tick thickness (3-4 rows) nearest the frame's middle, and must lie within 10% of it
    yt = [float(np.mean(gr)) for gr in groups if len(gr) <= 5]
    y0 = yt[-1]
    mid = 0.5 * (top + bot)
    y1 = min(yt, key=lambda y: abs(y - mid))
    if abs(y1 - mid) > 0.1 * (bot - top):
        raise SystemExit(f"panel at {oy},{ox}: no 1.0 tick near the middle row {mid:.0f}")
    xt = (sub[bot - 18:bot - 3, :] > 400).sum(0) >= 10
    tx = np.where(xt)[0]
    groups = np.split(tx, np.where(np.diff(tx) > 2)[0] + 1)
    found = np.array([float(np.mean(gr)) for gr in groups])
    # the major ticks: the frame's ends are 400 and 700 nm; each of the five between must be found within 3 px
    # (some panels also carry minor ticks, which are ignored)
    xs = np.linspace(left + 0.5, right, 7)
    for i in range(1, 6):
        j = np.argmin(np.abs(found - xs[i]))
        if abs(found[j] - xs[i]) > 3:
            raise SystemExit(f"panel at {oy},{ox}: no x tick near {400 + 50 * i} nm")
        xs[i] = found[j]
    ax = np.polyfit(xs, np.arange(400.0, 701.0, 50.0), 1)
    resid = np.polyval(ax, xs) - np.arange(400.0, 701.0, 50.0)
    lam, med, lo, hi = [], [], [], []
    for x in range(left + 7, right - 6):                                    # off the frame's sides (4-5 px)
        col = sub[top + 4:bot - 20, x]                                     # off the frame and the x ticks
        ys = np.where(col > 150)[0] + top + 4
        L = np.polyval(ax, x)
        ys = ys[ys > 165] if L > 565 else ys[ys > 150] if L < 440 else ys  # the labels "(x)" and "nnn+-n nm"
        if len(ys) == 0:
            continue
        A = (y0 - ys) / (y0 - y1)
        lam.append(L); med.append(np.median(A)); lo.append(np.percentile(A, 10)); hi.append(np.percentile(A, 90))
    return np.array(lam), np.array(med), np.array(lo), np.array(hi), float(np.max(np.abs(resid))), (y0, y1)


def ink(pdf):
    import io
    import pdfplumber
    im = pdfplumber.open(pdf).pages[3].images[0]
    a = np.asarray(Image.open(io.BytesIO(im["stream"].get_data())))
    if a.shape != (1325, 2374, 4):
        raise SystemExit(f"{pdf}: page 4's image is {a.shape}, not the 2374 x 1325 CMYK of Fig. 6")
    return (255 - a.astype(int)).sum(2)


def main():
    g = ink(sys.argv[1])
    grid = np.arange(402.0, 699.0, 1.0)
    cols = [grid]
    head = ["lambda_nm"]
    for k, (oy, ox) in PANELS.items():
        lam, med, lo, hi, xr, (y0, y1) = panel(g, oy, ox)
        for v in (med, lo, hi):
            cols.append(np.interp(grid, lam, v))
        head += [f"{k}_median", f"{k}_p10", f"{k}_p90"]
        i = np.argmax(cols[-3])
        print(f"panel {k} (label {PEAKS[k]} nm): x ticks fit to {xr:.2f} nm; y 0 at row {y0:.1f}, 1.0 at {y1:.1f}; "
              f"peak {grid[i]:.0f} nm, A {cols[-3][i]:.3f}; A(450) {np.interp(450, grid, cols[-3]):.3f}, "
              f"A(600) {np.interp(600, grid, cols[-3]):.3f}, A(650) {np.interp(650, grid, cols[-3]):.3f}, "
              f"A(695) {np.interp(695, grid, cols[-3]):.3f}")
    out = os.path.join(HERE, "data", "takebe2021_fig6.csv")
    np.savetxt(out, np.column_stack(cols), delimiter=",", fmt="%.4f",
               header="Takebe, Okamoto & Mori 2021 Fig. 6, read off the raster figure by materials/yanzhi/digitize.py "
                      "[D]; absorbance (a.u. = decadic, 1 mm), median and 10th/90th percentile of the nine curves\n"
                      + ",".join(head))
    print("wrote", out)


if __name__ == "__main__":
    main()
