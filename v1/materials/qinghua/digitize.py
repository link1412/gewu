"""Read the two spectra the cobalt model rests on out of their papers (ref/qinghua/, not in git).

    python3 -I materials/qinghua/digitize.py thiemsorn ref/qinghua/thiemsorn2007/thiemsorn2007.pdf
    python3 -I materials/qinghua/digitize.py hsieh ref/qinghua/hsieh2023/fig4.png

thiemsorn: Thiemsorn et al. 2007 (J. Solid Mech. Mater. Eng. 1(4) 508-518, doi 10.1299/jmmp.1.508), Fig. 7, the
  solid curve (Lambda_cal = 0.586, their glass Co5): absorbance per path length A/d (decadic, cm^-1) of Co2+ in a
  soda-lime-silica glass, 0.016 mol/L Co [M, their Table 4]. The figure is vector graphics: the curve's own path
  coordinates are read from the PDF (page 9) and mapped through the axis ticks, so this is the plotted curve to
  the PDF's coordinate precision (0.01 pt ~ 0.1 nm, 3e-4 cm^-1), not a hand trace. Check: at 595 nm it reads
  3.091 cm^-1, their Table 4 gives 3.09 for Co5.
  -> materials/qinghua/data/thiemsorn2007_fig7_co5.csv (lambda_nm, A_per_cm)

hsieh: Hsieh, Fischer & Orillaneda 2023 (Heritage Science 11:106, doi 10.1186/s40494-023-00953-0, CC BY 4.0),
  Fig. 4 right: FORS reflectance of the blue decoration of three Santa Cruz dishes (SC-1269 solid, SC-14679
  dashed, SC-14878 dotted), 400-890 nm. A raster figure (the publisher's full-size PNG): the curves are traced
  pixel by pixel (dark pixels on white, and under the translucent blue bars by their red channel), tracked from
  the red end where they are apart, gaps of the dashed and dotted lines interpolated. [D, read off a figure];
  about 1 nm and 0.002 in reflectance per pixel.
  -> materials/qinghua/data/hsieh2023_fig4.csv (lambda_nm, the three curves, then per curve 1 where the column
     was traced and 0 where interpolated: SC-1269 92% traced; the dashed and dotted lines cross between 560 and
     680 nm and are traced there only in part, so a comparison should use the traced columns)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


# --- Thiemsorn 2007, Fig. 7: vector paths --------------------------------------------------------
def pdf_paths(pdf, page):
    """Stroked and filled paths of one page, in page points, with their line widths (Form XObjects followed)."""
    from pypdf import PdfReader
    from pypdf.generic import ContentStream

    def mat(a, b, c, d, e, f):
        return np.array([[a, b, 0], [c, d, 0], [e, f, 1]], float)

    out = []

    def walk(content, resources, reader, ctm):
        stack, path, cur, lw = [], [], [], 1.0
        for operands, op in ContentStream(content, reader).operations:
            op = op.decode() if isinstance(op, bytes) else op
            if op == "q":
                stack.append((ctm.copy(), lw))
            elif op == "Q":
                ctm, lw = stack.pop()
            elif op == "cm":
                ctm = mat(*[float(x) for x in operands]) @ ctm
            elif op == "w":
                lw = float(operands[0])
            elif op == "m":
                if cur:
                    path.append(cur)
                cur = [tuple(float(x) for x in operands)]
            elif op == "l":
                cur.append(tuple(float(x) for x in operands))
            elif op == "c":
                cur.append(tuple(float(x) for x in operands[4:6]))
            elif op in ("v", "y"):
                cur.append(tuple(float(x) for x in operands[2:4]))
            elif op == "re":
                x, y, w, h = [float(v) for v in operands]
                if cur:
                    path.append(cur)
                path.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)])
                cur = []
            elif op in ("S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "n"):
                if cur:
                    path.append(cur)
                if op != "n":
                    for pth in path:
                        P = np.array([[x, y, 1] for x, y in pth]) @ ctm
                        out.append({"op": op, "pts": P[:, :2]})
                path, cur = [], []
            elif op == "Do":
                xo = resources["/XObject"][operands[0]].get_object()
                if xo["/Subtype"] == "/Form":
                    walk(xo, xo.get("/Resources", resources), reader,
                         mat(*[float(x) for x in xo.get("/Matrix", [1, 0, 0, 1, 0, 0])]) @ ctm)

    r = PdfReader(pdf)
    pg = r.pages[page - 1]
    walk(pg.get_contents(), pg["/Resources"], r, np.eye(3))
    return out


def thiemsorn(pdf):
    P = pdf_paths(pdf, 9)
    # Fig. 7's frame and ticks, found on the page: x 300 nm at 409.78 pt ... 1500 nm at 553.18 pt (ticks every
    # 150 nm), y 0 at 605.19 pt ... 4.0 at 764.14 pt (ticks every 0.25). Checked here, not assumed.
    def has_segment(a, b):
        return any(len(p["pts"]) == 2 and np.allclose(p["pts"], [a, b], atol=0.02) for p in P)
    for x in (409.78, 553.18):
        if not has_segment((x, 605.19), (x, 608.43)):
            raise SystemExit(f"{pdf}: Fig. 7's x tick at {x} pt not found; the figure's layout differs")
    for y in (605.19, 764.14):
        if not has_segment((403.78, y), (406.6, y)):
            raise SystemExit(f"{pdf}: Fig. 7's y tick at {y} pt not found")
    # the solid curve: the long paths inside the frame (the dashed curves are many short strokes)
    big = [p["pts"] for p in P if len(p["pts"]) > 300 and p["pts"][:, 0].min() >= 403 and p["pts"][:, 0].max() <= 554]
    a = np.concatenate(big)
    a = a[np.argsort(a[:, 0])]
    lam = 300 + (a[:, 0] - 409.78) * 1200 / (553.18 - 409.78)
    A = (a[:, 1] - 605.19) * 4.0 / (764.14 - 605.19)
    keep = (lam >= 350) & (lam <= 1000) & (A <= 4.0)          # above 4.0 the UV edge runs out of the frame
    lam, A = lam[keep], A[keep]
    lam, i = np.unique(lam.round(3), return_index=True)
    A = A[i]
    a595 = np.interp(595, lam, A)
    print(f"Fig. 7 solid curve: {len(lam)} points, {lam[0]:.1f}-{lam[-1]:.1f} nm, largest gap {np.diff(lam).max():.2f} nm; "
          f"A/d(595) = {a595:.3f} cm^-1 (Table 4, Co5: 3.09)")
    if abs(a595 - 3.09) > 0.02:
        raise SystemExit("the curve does not match Table 4")
    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "thiemsorn2007_fig7_co5.csv")
    with open(out, "w") as f:
        f.write("# Thiemsorn et al. 2007, Fig. 7, solid curve (Lambda_cal 0.586, glass Co5, 0.016 mol/L Co2+): "
                "A/d decadic per cm, read from the PDF's vector paths by materials/qinghua/digitize.py\n"
                "lambda_nm,A_per_cm\n")
        for l, v in zip(lam, A):
            f.write(f"{l:.3f},{v:.5f}\n")
    print(out)


# --- Hsieh 2023, Fig. 4: raster trace ------------------------------------------------------------
X400, PX_PER_NM = 1057.5, 211.0 / 200.0      # ticks: 400 nm at x 1057.5, 600 at 1268, 800 at 1479.5
Y0, PX_PER_UNIT = 730.5, 1302.0              # ticks: 0.0 at y 730.5 ... 0.5 at y 79.5


def ticks_ok(a):
    dark = a.sum(2) < 300
    xt = [c for c in range(1040, 1600) if dark[733:742, c].sum() >= 6]
    yt = [r for r in range(0, 740) if dark[r, 1046:1056].sum() >= 6]
    return ({1057, 1268, 1479} <= set(xt)) and ({79, 209, 339, 469, 600, 730} <= set(yt))


def hsieh(png):
    """The three line styles also differ in colour, which separates them: SC-1269 warm grey (B < R), SC-14679
    slate (B > R), SC-14878 neutral grey. Under the translucent blue bars the colours are lost; there a dark run
    (red channel below the bar's) goes to the curve whose straight interpolation across the bar it lies nearest,
    within 5 px, else that column is interpolated."""
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB")).astype(float)
    if not ticks_ok(a):
        raise SystemExit(f"{png}: the axis ticks are not where this trace expects them")
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    bar = (B - R > 60) & (R > 60)
    dark = np.where(bar, R < 125, a.mean(2) < 185)
    dark[726:, :] = False                                   # the axis
    dark[60:220, 1120:1325] = False                         # the legend box
    dark[590:, 1160:1350] = False                           # the "Co(II) triplet" label
    hue = B - R
    warm, cool = dark & ~bar & (hue < -3), dark & ~bar & (hue > 3)
    near = np.zeros_like(dark)                              # within 3 px (vertically) of a warm or cool pixel:
    for d in range(-3, 4):                                  # anti-aliasing of those lines, not the neutral one
        near |= np.roll(warm | cool, d, axis=0)
    cls = {"SC-1269": warm, "SC-14679": cool, "SC-14878": dark & ~bar & (np.abs(hue) <= 3) & ~near}
    names = list(cls)
    lams = np.arange(402.0, 889.0, 1.0)
    cols = np.round(X400 + (lams - 400) * PX_PER_NM).astype(int)
    barcol = np.array([bar[300:600, c].mean() > 0.5 for c in cols])

    def runs(mask_col):
        rows = np.where(mask_col)[0]
        return [r for r in np.split(rows, np.where(np.diff(rows) > 1)[0] + 1) if len(r)] if len(rows) else []

    tracks = {n: np.full(len(lams), np.nan) for n in names}
    for j, c in enumerate(cols):
        if barcol[j]:
            continue
        for n in names:
            rr = [r for r in runs(cls[n][:, c]) if len(r) <= 60]
            if len(rr) == 1:
                tracks[n][j] = rr[0].mean()
            elif len(rr) > 1:                               # keep the run nearest the previous point
                prev = tracks[n][j - 1] if j and not np.isnan(tracks[n][j - 1]) else None
                if prev is not None:
                    tracks[n][j] = min(rr, key=lambda r: abs(r.mean() - prev)).mean()
    # a dashed or dotted line's dots are short: drop isolated outliers against a running median
    for n in names:
        t = tracks[n]
        ok = ~np.isnan(t)
        idx = np.where(ok)[0]
        bad = [k for k in idx if abs(t[k] - np.median(t[idx[(idx >= k - 15) & (idx <= k + 15)]])) > 6]
        t[bad] = np.nan
    # under the bars
    for j in np.where(barcol)[0]:
        rr = runs(dark[:, cols[j]])
        cand = [r.mean() for r in rr if len(r) <= 40]
        for n in names:
            t = tracks[n]
            ok = ~np.isnan(t)
            left, right = np.where(ok[:j])[0], np.where(ok[j:])[0] + j
            if not len(left) or not len(right):
                continue
            l, r = left[-1], right[0]
            pred = t[l] + (t[r] - t[l]) * (j - l) / (r - l)
            if cand:
                k = int(np.argmin([abs(v - pred) for v in cand]))
                if abs(cand[k] - pred) <= 5:
                    t[j] = cand.pop(k)
    out = [lams]
    for n in names:
        t = tracks[n]
        ok = ~np.isnan(t)
        print(f"{n}: traced {ok.mean():.0%} of the 1 nm columns, the rest interpolated; "
              f"largest gap {np.diff(lams[ok]).max():.0f} nm")
        out.append((Y0 - np.interp(lams, lams[ok], t[ok])) / PX_PER_UNIT)
    for n in names:
        out.append((~np.isnan(tracks[n])).astype(float))
    out = np.stack(out, 1)
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, "hsieh2023_fig4.csv")
    with open(path, "w") as f:
        f.write("# Hsieh, Fischer & Orillaneda 2023, Heritage Science 11:106, Fig. 4 right (CC BY 4.0): FORS reflectance "
                "of the blue decoration, traced from the figure by materials/qinghua/digitize.py [D]\n"
                "lambda_nm," + ",".join(names) + "," + ",".join(f"{n}_traced" for n in names) + "\n")
        for row in out:
            f.write(",".join(f"{v:.4f}" for v in row) + "\n")
    print(path)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("thiemsorn", "hsieh"):
        raise SystemExit(__doc__)
    {"thiemsorn": thiemsorn, "hsieh": hsieh}[sys.argv[1]](sys.argv[2])
