"""What a crack line looks like across: the cross profile of the lines, measured the same way on the photo and on
a render (docs/materials/guan_glaze.md, round 2).

    python3 -I materials/guan_glaze/lines.py photo --out out/materials/guan_glaze/lines_met48503.json
    python3 -I materials/guan_glaze/lines.py image LIN.npy --px-mm 32.23 --out X.json [--blur-px S]

The lines are found by crafts/crackle/network.py (bright-ridge filter, thinning, graph). Along every segment the
cross profiles (linear RGB, along the local normal, -0.5..+0.5 mm, 0.5 px steps, no smoothing) are averaged over
blocks of 0.25 mm, and each block gives:
- contrast: peak of luma / background - 1 (background: median at 0.3-0.5 mm either side; the peak within 0.15 mm);
- FWHM of (luma - background), interpolated at half the peak;
- asymmetry (wR - wL) / (wR + wL) of the two half-widths at half maximum (an inclined stained crack face seen
  through the glaze gives a one-sided band, a symmetric source gives 0);
- a dark core: a dip at the middle deeper than 3% of the background below both shoulders;
- colour: RGB at the peak / RGB of the background;
- orientation of the line (deg, image axes) to look for a dependence on the light's direction.
The mean profile (contrast against r) is written too, both as measured and with each block flipped so that its
wider side is on the right.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "crafts", "crackle"))
import network as nw  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722])


def block_profiles(lin, G, px_mm, half_mm=0.5, block_mm=0.25, step_px=0.5, paths=None):
    """(r_mm, profiles (n, len(r), 3), orientation deg (n,)) of the blocks along all edges of graph G, or along
    `paths` (list of (n, 2) row-col polylines) when given (a render, where the cracks' places are known)."""
    r = np.arange(-half_mm * px_mm, half_mm * px_mm + 1e-9, step_px)
    out, ori = [], []
    H, W = lin.shape[:2]
    for p in (paths if paths is not None else [e["path"] for e in G.edges]):
        p = np.asarray(p, float)
        if paths is not None:          # densify a known polyline to ~1 px
            s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
            t_ = np.arange(0, s_[-1] + 1e-9, 1.0)
            p = np.c_[np.interp(t_, s_, p[:, 0]), np.interp(t_, s_, p[:, 1])]
        if len(p) < 4:
            continue
        ps = np.c_[ndi.gaussian_filter1d(p[:, 0], 2.0, mode="nearest"), ndi.gaussian_filter1d(p[:, 1], 2.0, mode="nearest")]
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ps, axis=0), axis=1))]
        if s[-1] < 2 * block_mm * px_mm:
            continue
        # skip 0.3 mm at each end (junctions)
        t = np.arange(0.3 * px_mm, s[-1] - 0.3 * px_mm, 1.0)
        if len(t) < 4:
            continue
        cy, cx = np.interp(t, s, ps[:, 0]), np.interp(t, s, ps[:, 1])
        ty, tx = np.gradient(cy), np.gradient(cx)
        nrm = np.hypot(ty, tx) + 1e-12
        ty, tx = ty / nrm, tx / nrm
        ny, nx = tx, -ty                                  # normal
        blk = (t - t[0]) // (block_mm * px_mm)
        for b in np.unique(blk):
            ii = np.nonzero(blk == b)[0]
            if len(ii) < 0.6 * block_mm * px_mm:
                continue
            Y = cy[ii, None] + r[None, :] * ny[ii, None]
            X = cx[ii, None] + r[None, :] * nx[ii, None]
            if Y.min() < 0 or X.min() < 0 or Y.max() > H - 1 or X.max() > W - 1:
                continue
            prof = np.stack([ndi.map_coordinates(lin[..., c], [Y.ravel(), X.ravel()], order=1).reshape(Y.shape).mean(0)
                             for c in range(3)], -1)
            out.append(prof)
            ori.append(math.degrees(math.atan2(-np.mean(ty[ii]), np.mean(tx[ii]))) % 180)
    return r / px_mm, np.array(out), np.array(ori)


def analyse(r_mm, prof, ori):
    if len(prof) == 0:
        return {"blocks": 0, "note": "no line found"}
    Yp = prof @ LUMA
    bgm = (np.abs(r_mm) >= 0.3)
    bg = np.median(Yp[:, bgm], 1)
    bgc = np.median(prof[:, bgm], 1)
    c = Yp / bg[:, None] - 1
    cen = np.abs(r_mm) <= 0.15
    ic = np.nonzero(cen)[0]
    rows = []
    for k in range(len(c)):
        ck = c[k]
        j = ic[np.argmax(np.abs(ck[ic]))]
        pk = ck[j]
        sgn = 1 if pk >= 0 else -1
        a = sgn * ck
        hm = a[j] / 2
        l = j
        while l > 0 and a[l] > hm:
            l -= 1
        rr = j
        while rr < len(a) - 1 and a[rr] > hm:
            rr += 1
        if l == 0 or rr == len(a) - 1 or a[j] <= 0:
            continue
        xl = r_mm[l] + (hm - a[l]) / (a[l + 1] - a[l] + 1e-12) * (r_mm[l + 1] - r_mm[l])
        xr = r_mm[rr - 1] + (hm - a[rr - 1]) / (a[rr] - a[rr - 1] + 1e-12) * (r_mm[rr] - r_mm[rr - 1])
        wl, wr = r_mm[j] - xl, xr - r_mm[j]
        # dark core: a minimum near the middle, under both shoulders by > 0.03 (only for bright lines)
        mid = np.abs(r_mm) <= 0.12
        core = False
        if sgn > 0:
            seg = ck[mid]
            im = np.argmin(seg)
            if 0 < im < len(seg) - 1:
                core = (seg[:im].max() - seg[im] > 0.03) and (seg[im + 1:].max() - seg[im] > 0.03)
        rows.append((pk, xr - xl, (wr - wl) / (wr + wl), core, *(prof[k, j] / bgc[k]), ori[k], k, r_mm[j]))
    if not rows:
        return {"blocks": 0, "note": "no measurable line (no half-maximum crossing)"}
    R = np.array([[x if not isinstance(x, (bool, np.bool_)) else float(x) for x in row] for row in rows])
    pk, fw, asym, core, cr, cg, cb, o = (R[:, i] for i in range(8))
    bright = pk > 0
    pc = lambda a, q=(10, 50, 90): [round(float(np.percentile(a, x)), 4) for x in q] if len(a) else None
    res = {
        "blocks": int(len(R)),
        "contrast_p10_p50_p90": pc(pk),
        "fraction_darker": round(float((pk < 0).mean()), 3),
        "fwhm_um_p10_p50_p90_bright": [round(1000 * v) for v in pc(fw[bright])] if bright.any() else None,
        "abs_asymmetry_p25_p50_p75_bright": pc(np.abs(asym[bright]), (25, 50, 75)),
        "dark_core_fraction_of_bright": round(float(core[bright].mean()), 3) if bright.any() else None,
        "colour_over_glaze_median_bright": [round(float(np.median(x[bright])), 3) for x in (cr, cg, cb)] if bright.any() else None,
        "colour_over_glaze_median_all": [round(float(np.median(x)), 3) for x in (cr, cg, cb)],
        "contrast_median_by_orientation_deg": {f"{a0}-{a0 + 45}": round(float(np.median(pk[(o >= a0) & (o < a0 + 45)])), 4)
                                               if ((o >= a0) & (o < a0 + 45)).sum() > 5 else None for a0 in (0, 45, 90, 135)},
    }
    if not bright.any():
        return res
    # mean profiles (bright blocks), centred on their own peak, as measured and flipped wide side right
    idx = R[:, 8].astype(int)[bright]
    shift = R[:, 9][bright]
    grid = np.arange(-0.4, 0.4001, 0.01)
    m1, m2 = [], []
    for k, s0, asy in zip(idx, shift, asym[bright]):
        f = np.interp(grid + s0, r_mm, c[k])
        m1.append(f)
        m2.append(f if asy >= 0 else f[::-1])
    res["mean_profile_r_mm"] = [round(float(x), 3) for x in grid]
    res["mean_profile_contrast"] = [round(float(x), 4) for x in np.mean(m1, 0)]
    res["mean_profile_contrast_wide_side_right"] = [round(float(x), 4) for x in np.mean(m2, 0)]
    mp = np.mean(m1, 0)
    res["mean_profile_fwhm_um"] = round(1000 * float(np.ptp(grid[mp >= mp.max() / 2])), 1)
    return res


def measure(lin, px_mm, region, lo=0.035, hi=0.07, paths=None):
    """Lines found as on the photo; with `paths` (row-col polylines) also profiled at their known places
    ('known_place')."""
    Y = lin @ LUMA
    sk, A, th = nw.detect(Y, px_mm, region, lo, hi)
    G = nw.Graph(sk, px_mm, region=region)
    r_mm, prof, ori = block_profiles(lin, G, px_mm)
    res = analyse(r_mm, prof, ori)
    res["px_per_mm"] = px_mm
    if paths is not None:
        r_mm, prof, ori = block_profiles(lin, None, px_mm, paths=paths)
        res["known_place"] = analyse(r_mm, prof, ori)
    return res, G


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("photo")
    p.add_argument("--out", required=True)
    p.add_argument("--region", default="all", choices=["lower", "all"])
    p.add_argument("--px-mm", type=float, help="resample the photo to this scale first")
    i = sub.add_parser("image")
    i.add_argument("lin", help=".npy float (H, W, 3) linear RGB, or a PNG (sRGB)")
    i.add_argument("--px-mm", type=float, required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--blur-px", type=float, default=0.0, help="Gaussian blur first (the photo's own PSF)")
    i.add_argument("--border", type=float, default=0.04)
    a = ap.parse_args()
    if a.cmd == "photo":
        im, lin, region, px = nw.photo_region(a.region)
        if a.px_mm:
            from PIL import Image
            f = a.px_mm / px
            im = np.asarray(Image.fromarray(im).resize((int(im.shape[1] * f), int(im.shape[0] * f)), Image.LANCZOS))
            lin = nw.srgb_to_lin(im)
            region = np.asarray(Image.fromarray(region.astype(np.uint8) * 255).resize((im.shape[1], im.shape[0]), Image.NEAREST)) > 127
            px = a.px_mm
        ys, xs = np.nonzero(region)
        sl = (slice(ys.min() - 20, ys.max() + 20), slice(xs.min() - 20, xs.max() + 20))
        res, G = measure(lin[sl], px, region[sl])
        res["source"] = f"Met 48503, region {a.region}"
    else:
        if a.lin.endswith(".npy"):
            lin = np.load(a.lin).astype(np.float64)
        else:
            from PIL import Image
            lin = nw.srgb_to_lin(np.asarray(Image.open(a.lin).convert("RGB")))
        if a.blur_px > 0:
            lin = np.stack([ndi.gaussian_filter(lin[..., c], a.blur_px) for c in range(3)], -1)
        region = np.zeros(lin.shape[:2], bool)
        b = int(a.border * lin.shape[1])
        region[b:-b, b:-b] = True
        res, G = measure(lin, a.px_mm, region)
        res["source"] = a.lin + (f", blurred sigma {a.blur_px} px" if a.blur_px else "")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if not k.startswith("mean_profile_")}, indent=1))
    print("mean profile FWHM um", res["mean_profile_fwhm_um"])


if __name__ == "__main__":
    main()
