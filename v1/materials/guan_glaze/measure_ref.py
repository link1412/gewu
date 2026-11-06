"""Measure the reference photo of the Guan glaze material card: Met 48503 (a Guan-type sherd, CC0).

    python3 -I materials/guan_glaze/measure_ref.py [--out out/materials/guan_glaze/measured_met48503.json]

Every number written says how it was measured ("method"). The photo is the truth for the card
(docs/materials/guan_glaze.md); what is measured here is parameters of its appearance, [M, from the photo].
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter as gf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHOTO = os.path.join(ROOT, "ref/guan/met48503_0.jpg")
SHERD_MM = (92.0, 48.0)          # Met's "9.2 x 4.8 cm" [M, Met catalogue]


def srgb_to_lin(x):
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def luma(lin):
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def poly_design(shape, order, step):
    h, w = shape
    yy, xx = np.mgrid[0:h:step, 0:w:step]
    return yy, xx


def fit_backdrop(lin, order=3):
    """Smooth surface (2-D polynomial, per channel) fitted robustly to the backdrop: the border band
    first, then everything the previous fit calls backdrop, iterated."""
    h, w = lin.shape[:2]
    s = 8
    small = lin[::s, ::s]
    hh, ww = small.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww]
    u, v = xx / ww * 2 - 1, yy / hh * 2 - 1
    cols = [u ** i * v ** j for i in range(order + 1) for j in range(order + 1 - i)]
    A = np.stack([c.ravel() for c in cols], 1)
    mask = np.zeros((hh, ww), bool)
    b = int(0.06 * hh)
    mask[:b] = mask[-b:] = True
    mask[:, :b] = mask[:, -b:] = True
    L = luma(small)
    for _ in range(8):
        coef = np.linalg.lstsq(A[mask.ravel()], L.ravel()[mask.ravel()], rcond=None)[0]
        fit = (A @ coef).reshape(hh, ww)
        d = np.abs(L - fit) / fit
        mask = d < 0.025
        mask = ndi.binary_opening(mask, iterations=2)
    full = np.zeros((h, w, 3))
    yy, xx = np.mgrid[0:h, 0:w]
    uu, vv = xx / w * 2 - 1, yy / h * 2 - 1
    Af = [uu ** i * vv ** j for i in range(order + 1) for j in range(order + 1 - i)]
    for c in range(3):
        coef = np.linalg.lstsq(A[mask.ravel()], small[..., c].ravel()[mask.ravel()], rcond=None)[0]
        full[..., c] = sum(k * a for k, a in zip(coef, Af))
    return full


def feret(pts):
    """Max Feret diameter and the extent across it, and the angle, from the convex hull."""
    from scipy.spatial import ConvexHull
    hull = pts[ConvexHull(pts).vertices]
    best = None
    for a in np.linspace(0, math.pi, 1800, endpoint=False):
        d = np.array([math.cos(a), math.sin(a)])
        e = hull @ d
        L = e.max() - e.min()
        if best is None or L > best[0]:
            best = (L, a)
    L, a = best
    n = np.array([-math.sin(a), math.cos(a)])
    e = hull @ n
    return L, e.max() - e.min(), a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out/materials/guan_glaze/measured_met48503.json"))
    ap.add_argument("--debug", default=os.path.join(ROOT, "out/materials/guan_glaze/measure_debug"))
    a = ap.parse_args()
    os.makedirs(a.debug, exist_ok=True)
    im = np.asarray(Image.open(PHOTO).convert("RGB"))
    H, W = im.shape[:2]
    lin = srgb_to_lin(im.astype(np.float64))
    R = {"photo": "ref/guan/met48503_0.jpg", "size_px": [W, H]}

    # ---- 1. scale -------------------------------------------------------------------
    bd = fit_backdrop(lin)
    diff = np.abs(luma(lin) - luma(bd)) / luma(bd)
    sm = gf(diff, 3)
    best = None
    out = {}
    chroma = gf(lin[..., 1] / np.maximum(lin[..., 0], 1e-6), 3)
    rel = gf(luma(lin), 3) / luma(bd)
    for thr in (0.65, 0.70, 0.75):
        # sherd: clearly darker than the backdrop (a floating sherd's soft shadow is only a few % darker) or greenish
        m = (rel < thr) | (chroma > 1.12)
        m = ndi.binary_opening(m, iterations=3)
        lab, n = ndi.label(m)
        if n == 0:
            continue
        big = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
        big = ndi.binary_fill_holes(big)
        ys, xs = np.nonzero(big)
        pts = np.c_[xs[::7], ys[::7]].astype(float)
        L, Wd, ang = feret(pts)
        out[thr] = {"length_px": L, "width_px": Wd, "angle_deg": math.degrees(ang), "area_px": int(big.sum()),
                    "px_per_mm_length": L / SHERD_MM[0], "px_per_mm_width": Wd / SHERD_MM[1]}
        if thr == 0.70:
            best = big
    Image.fromarray((best * 255).astype(np.uint8)).resize((W // 4, H // 4)).save(os.path.join(a.debug, "sherd_mask.png"))
    pl = [v["px_per_mm_length"] for v in out.values()]
    pw = [v["px_per_mm_width"] for v in out.values()]
    # Met's 9.2 x 4.8 cm: the length is the sherd's long axis, sharp-ended and the same at every threshold (+-0.1%); the
    # cross extent is the greater width, and gives a scale 3.6% larger, so the catalogue's two numbers disagree by that
    # much (rounding to 1 mm is 0.5-1%; the rest is how Met measured). The length is used, the width is the uncertainty.
    scale = float(np.mean(pl))
    R["scale"] = {"px_per_mm": round(scale, 2), "uncertainty_pct": round(100 * (np.mean(pw) / scale - 1), 1),
                  "px_per_mm_from_width": round(float(np.mean(pw)), 2),
                  "by_threshold": {str(k): {kk: round(vv, 2) for kk, vv in v.items()} for k, v in out.items()},
                  "method": "backdrop = 3rd-order 2-D polynomial per channel fitted robustly (iteratively re-selected "
                            "pixels within 2.5% of the fit); sherd = largest component where smoothed luma/backdrop "
                            "< thr (0.65..0.75) or G/R > 1.12 (the sherd is green, the backdrop and its soft shadow neutral), "
                            "holes filled; max Feret diameter and the extent across it from the convex hull, against Met's "
                            "92 x 48 mm; the scale is the length's (stable to 0.1% over the thresholds); the width's "
                            "scale is 3.6% larger: that is the uncertainty",
                  "tag": "[M, from the photo and Met's size]"}
    pxmm = scale
    # backdrop value and gradient
    R["backdrop"] = {"mean_rgb_8bit": [round(float(x), 1) for x in (255 * (np.mean(bd, axis=(0, 1)) ** (1 / 2.2)))],
                     "luma_ratio_corner_tl_over_br": round(float(luma(bd[:200, :200]).mean() / luma(bd[-200:, -200:]).mean()), 3),
                     "luma_centre_over_edge_mean": round(float(luma(bd[H // 2 - 100:H // 2 + 100, W // 2 - 100:W // 2 + 100]).mean() /
                                                           luma(np.r_[bd[:100].reshape(-1, 3), bd[-100:].reshape(-1, 3)]).mean()), 3)}

    # ---- glaze region: the big sherd mask eroded, minus the dark band and edges ----------
    inner = ndi.binary_erosion(best, iterations=int(0.8 * pxmm))
    Y = luma(lin)
    # the dark brown band (thin glaze over body) and the pale step are found from the smoothed luma
    ys8 = gf(Y, 6 * pxmm / 33)
    band = inner & (ys8 < 0.55 * np.median(Y[inner]))
    lb, nb = ndi.label(band)
    band = lb == (np.argmax(np.bincount(lb.ravel())[1:]) + 1)     # the band itself, not the dark stain blotches
    band = ndi.binary_dilation(band, iterations=int(0.8 * pxmm))
    g = inner & ~band
    # the lower sherd (below the step) only: region used for glaze statistics = rows below the band's lowest point near x
    ys, xs = np.nonzero(band)
    # take the lower-left half-plane under the band's arc: rows greater than the band's row at that column + margin
    colmax = np.full(W, -1)
    for x_, y_ in zip(xs, ys):
        colmax[x_] = max(colmax[x_], y_)
    # band covers x range only partially; use the polynomial of its lowest points
    xc = np.nonzero(colmax >= 0)[0]
    pb = np.polyfit(xc, colmax[xc], 2)
    yy, xx = np.mgrid[0:H, 0:W]
    below = yy > np.polyval(pb, xx) + 1.5 * pxmm
    # left of the band's start also counts as 'below' if row > band start; keep it simple: x within band's x range
    lower = g & below & (xx > xc.min()) & (xx < xc.max())
    # leave out an edge strip near the break (done by erosion) and anything very dark
    R["region_lower_px"] = int(lower.sum())
    R["region_lower_mm2"] = round(float(lower.sum()) / pxmm ** 2, 1)
    dbg = (im * 0.5).astype(np.uint8)
    dbg[lower] = (im[lower] * 0.5 + np.array([0, 100, 0])).astype(np.uint8)
    dbg[band] = [200, 0, 0]
    Image.fromarray(dbg).resize((W // 4, H // 4)).save(os.path.join(a.debug, "regions.png"))

    # ---- 2. colour, mottling ---------------------------------------------------------------
    # crack lines and specks are measured later; the glaze colour is the median of the region (robust to both)
    med = np.median(lin[lower], axis=0)
    R["glaze_colour"] = {"median_linear_rgb": [round(float(x), 5) for x in med],
                         "median_srgb_8bit": [round(float(255 * x ** (1 / 2.2))) for x in med],
                         "mean_srgb_8bit_region": [round(float(x), 1) for x in im[lower].mean(0)],
                         "ratio_to_backdrop_linear": [round(float(m / b), 4) for m, b in zip(med, np.mean(bd, axis=(0, 1)))],
                         "method": "median of linear RGB over the glaze below the dark band (cracks, specks included; "
                                   "the median ignores them); ratio to the fitted backdrop at the same place",
                         "tag": "[M, from the photo]"}
    # mottling: low-passed luma (sigma 1.5 mm) with crack lines and stain blotches excluded
    lp = gf(np.where(lower, Y, np.median(Y[lower])), 1.5 * pxmm)
    # normalised convolution so the mask edge does not leak in
    num = gf(np.where(lower, Y, 0.0), 1.5 * pxmm)
    den = gf(lower.astype(float), 1.5 * pxmm) + 1e-9
    lp = num / den
    mot = lp[lower & (den > 0.8)]
    R["mottling"] = {"sigma_1.5mm_luma_rel_std_pct": round(100 * float(mot.std() / mot.mean()), 2)}
    for s_mm in (0.5, 1.0, 3.0, 6.0):
        n_ = gf(np.where(lower, Y, 0.0), s_mm * pxmm)
        d_ = gf(lower.astype(float), s_mm * pxmm) + 1e-9
        l_ = (n_ / d_)[lower & (d_ > 0.8)]
        R["mottling"][f"luma_rel_std_after_gauss_{s_mm}mm_pct"] = round(100 * float(l_.std() / l_.mean()), 2)
    # correlation length of the low-passed luma (1/e of the autocorrelation), on a patch of the lower region
    ys_, xs_ = np.nonzero(lower)
    cy, cx = int(np.median(ys_)), int(np.median(xs_))
    R["mottling"]["method"] = ("relative std of luma after a Gaussian low-pass (normalised convolution inside the glaze "
                               "region) at the sigma in the key's name; includes the stains and the crack lines' shadow")
    R["mottling"]["tag"] = "[M, from the photo]"

    # ---- 3. speckle ----------------------------------------------------------------------
    # luma, and the local contrast: difference of Gaussians, sigma 0.6 px minus 2.5 px (specks of 1-3 px)
    px = pxmm
    ssm = gf(Y, 0.7)
    dog = ssm - gf(Y, 3.0)
    rel = dog / np.maximum(gf(Y, 3.0), 1e-6)
    # exclude crack lines: ridge mask computed below; first build it
    # ---- 4. crack lines: oriented line filter -----------------------------------------------
    # 16 orientations of a kernel that is a Mexican-hat across the line (sigma_w 2.2 px = 70 um) and a Gaussian
    # along it (sigma_l 8 px = 0.25 mm), on log luma: speckle is isotropic and does not add up, lines do.
    from scipy.signal import fftconvolve
    from skimage.filters import apply_hysteresis_threshold
    from skimage.morphology import skeletonize
    ysx, xsx = np.nonzero(lower)
    y0, y1, x0, x1 = ysx.min() - 24, ysx.max() + 24, xsx.min() - 24, xsx.max() + 24

    def kern(th, sw=2.2, sl=8.0, n=41):
        r = np.arange(n) - n // 2
        yk, xk = np.meshgrid(r, r, indexing="ij")
        u_ = xk * math.cos(th) + yk * math.sin(th)
        v_ = -xk * math.sin(th) + yk * math.cos(th)
        k = (1 - v_ ** 2 / sw ** 2) * np.exp(-v_ ** 2 / (2 * sw ** 2)) * np.exp(-u_ ** 2 / (2 * sl ** 2))
        k -= k.mean()
        return k / np.abs(k).sum()

    logY = np.log(Y[y0:y1, x0:x1])
    ths = np.linspace(0, math.pi, 16, endpoint=False)
    Rs = np.stack([fftconvolve(logY, kern(t), mode="same") for t in ths])
    Acrop = np.abs(Rs).max(0)
    th_crop = ths[np.abs(Rs).argmax(0)]
    Aline = np.zeros((H, W))
    Aline[y0:y1, x0:x1] = Acrop
    th = np.zeros((H, W))
    th[y0:y1, x0:x1] = th_crop
    near_edge = ~ndi.binary_erosion(best, iterations=int(0.6 * pxmm))
    cand = apply_hysteresis_threshold(np.where(lower, Aline, 0.0), 0.050, 0.090)
    skel = skeletonize(cand)
    lab, n = ndi.label(skel, structure=np.ones((3, 3)))
    objs = ndi.find_objects(lab)
    ext = np.array([0.0] + [math.hypot(o[0].stop - o[0].start, o[1].stop - o[1].start) for o in objs])
    skel = np.isin(lab, np.nonzero(ext >= 4.0 * px)[0]) & (lab > 0)    # extent (bounding-box diagonal) >= 4 mm
    lab, n = ndi.label(skel, structure=np.ones((3, 3)))
    Image.fromarray((skel * 255).astype(np.uint8)).save(os.path.join(a.debug, "cracks_skel.png"))
    line_mask = ndi.binary_dilation(skel, iterations=int(0.12 * px) + 2)
    yy, xx = np.mgrid[0:H, 0:W]
    # total length
    # skeleton pixel count ~ length (diagonals sqrt2): use 1.15 factor
    length_mm = skel.sum() * 1.15 / px
    area_mm2 = lower.sum() / px ** 2
    R["cracks"] = {"detected_length_mm": round(float(length_mm), 1), "region_mm2": round(float(area_mm2), 1),
                   "length_density_mm_per_mm2": round(float(length_mm / area_mm2), 4)}
    # cell size: components of the complement of the (dilated) line set; complete cells = not touching the region's border
    walls = ndi.binary_dilation(skel, iterations=int(0.25 * px) + 1)
    free = lower & ~walls
    lab, n = ndi.label(free)
    areas = np.bincount(lab.ravel())[1:] / px ** 2
    # border-touching: touches pixels outside `lower` (after dilating once)
    outside = ~lower
    touch = np.unique(lab[ndi.binary_dilation(outside, iterations=3) & (lab > 0)])
    complete = np.array([i + 1 not in set(touch) for i in range(n)])
    ok = complete & (areas > 1.0)
    A_c = areas[ok]
    R["cracks"]["cell"] = {"complete_cells": int(ok.sum()), "mean_area_mm2": round(float(A_c.mean()), 2) if ok.any() else None,
                           "median_area_mm2": round(float(np.median(A_c)), 2) if ok.any() else None,
                           "l_mm_sqrt_meanA": round(float(math.sqrt(A_c.mean())), 2) if ok.any() else None,
                           "l_mm_from_length_density": round(float(2.0 / (length_mm / area_mm2)), 2),
                           "method": "l = sqrt(A/N) with the complete cells (not touching the region border) of the "
                                     "complement of the ridge skeleton (dilated 0.25 mm), area > 1 mm2; the second figure "
                                     "is 2/(line length per area), the value for a regular network of polygons "
                                     "(l = sqrt(A_cell) = 2 A/P ... for squares)"}
    # lines: per skeleton pixel, the cross profile of luma and colour
    # sample the *signed* contrast: line pixel (smoothed 1 px) vs mean of pixels 6-9 px on both sides along the local normal
    ske_y, ske_x = np.nonzero(skel)
    lin_s = np.stack([gf(lin[..., c], 0.8) for c in range(3)], -1)
    # local direction: from the structure of the skeleton, PCA of neighbours in a 9 px window
    nx_, ny_ = -np.sin(th[ske_y, ske_x]), np.cos(th[ske_y, ske_x])     # line normal, from the filter's best orientation
    prof_r = np.arange(-14, 15)
    prof = np.zeros((len(ske_y), len(prof_r), 3))
    for k, r in enumerate(prof_r):
        sx = np.clip(ske_x + r * nx_, 0, W - 1)
        sy = np.clip(ske_y + r * ny_, 0, H - 1)
        for c in range(3):
            prof[:, k, c] = ndi.map_coordinates(lin_s[..., c], [sy, sx], order=1)
    Yp = prof @ np.array([0.2126, 0.7152, 0.0722])
    bgk = (np.abs(prof_r) >= 8) & (np.abs(prof_r) <= 13)
    bgY = np.median(Yp[:, bgk], 1)
    # line value = extreme within +-3 px; sign: negative (darker) or positive
    cen = np.abs(prof_r) <= 3
    dY = Yp[:, cen] - bgY[:, None]
    arg = np.argmax(np.abs(dY), 1)
    peak = dY[np.arange(len(dY)), arg]
    peak_rel = peak / bgY
    pk_idx = np.nonzero(cen)[0][arg]
    bgC = np.median(prof[:, bgk], 1)
    lineC = prof[np.arange(len(dY)), pk_idx]
    # width: FWHM of |profile - bg| around the peak, parabolic interpolation not needed (1 px steps)
    absd = np.abs(Yp - bgY[:, None])
    wid = np.zeros(len(dY))
    for i in range(len(dY)):
        p = pk_idx[i]
        hm = absd[i, p] / 2
        l_, r_ = p, p
        while l_ > 0 and absd[i, l_] > hm:
            l_ -= 1
        while r_ < len(prof_r) - 1 and absd[i, r_] > hm:
            r_ += 1
        # linear interpolation at half max
        def cross(a_, b_):
            va, vb = absd[i, a_], absd[i, b_]
            return a_ + (hm - va) / (vb - va + 1e-12) * (b_ - a_)
        wid[i] = cross(r_ - 1, r_) - cross(l_ + 1, l_) if l_ < p and r_ > p else 0
    good = (wid > 0.5) & (wid < 12)
    print(f"{good.sum()} / {len(good)} line samples good")
    wmm = wid[good] / px
    # the photo's own blur: the point-spread of the photo is measured on the sherd's outline (edge 10-90 rise) -- see below
    R["cracks"]["profile"] = {
        "samples": int(good.sum()),
        "fwhm_px_median": round(float(np.median(wid[good])), 2),
        "fwhm_um_p10_p50_p90": [round(float(np.percentile(wmm, q) * 1000)) for q in (10, 50, 90)],
        "contrast_signed_rel_to_glaze_p10_p50_p90": [round(float(np.percentile(peak_rel[good], q)), 4) for q in (10, 50, 90)],
        "fraction_darker_than_glaze": round(float((peak_rel[good] < 0).mean()), 3),
        "colour_of_line_over_glaze_linear_rgb_ratio_median": [round(float(x), 3) for x in np.median(lineC[good] / np.maximum(bgC[good], 1e-6), 0)],
        "method": "oriented line filter (see skeleton), cross profiles of the 0.8 px-smoothed linear image along "
                  "the local normal (the filter's best orientation); background = median 8-13 px either side; contrast = "
                  "(extreme of luma within +-3 px - background)/background; width = FWHM of |profile - background| "
                  "(includes the photo's own blur; not removed)"}
    # variation along a line: split the skeleton into connected components, order samples along rows/cols is hard; use the
    # autocorrelation proxy: split each component's samples into runs of 1 mm by skeleton order via distance transform label
    # simple: for each component, sort by angle along principal axis, take 1.0 mm blocks, std of block means
    comp = lab[ske_y, ske_x]
    block_means = []
    wcv = []
    for c_id in np.unique(comp):
        idx = np.nonzero((comp == c_id) & good)[0]
        if len(idx) < 3 * px:
            continue
        pts = np.c_[ske_x[idx], ske_y[idx]].astype(float)
        mu = pts.mean(0)
        u, s_, vt = np.linalg.svd(pts - mu, full_matrices=False)
        t = (pts - mu) @ vt[0]
        order = np.argsort(t)
        blk = (t[order] / px // 1.0).astype(int)
        for b_ in np.unique(blk):
            ii = idx[order][blk == b_]
            if len(ii) >= 0.5 * px:
                block_means.append((c_id, float(np.mean(peak_rel[ii])), float(np.mean(wid[ii]))))
    bm = np.array([[b[1], b[2]] for b in block_means])
    byc = {}
    for c_id, v, w_ in block_means:
        byc.setdefault(c_id, []).append(v)
    within = [np.std(v) for v in byc.values() if len(v) >= 4]
    R["cracks"]["along_line"] = {
        "blocks_1mm": len(bm),
        "block_contrast_p10_p50_p90": [round(float(np.percentile(bm[:, 0], q)), 4) for q in (10, 50, 90)],
        "block_width_px_p10_p50_p90": [round(float(np.percentile(bm[:, 1], q)), 2) for q in (10, 50, 90)],
        "within_line_std_of_1mm_contrast_median": round(float(np.median(within)), 4) if within else None,
        "method": "samples of each skeleton component projected on its principal axis, blocks of 1 mm; "
                  "within-line std = std of the block means along one line (lines with >= 4 blocks)"}
    med_abs = float(np.median(np.abs(bm[:, 0])))
    faint = float((np.abs(bm[:, 0]) < 0.5 * med_abs).mean())
    R["cracks"]["faint_fraction_blocks"] = round(faint, 3)
    R["cracks"]["faint_definition"] = "1 mm blocks whose |contrast| is under half the median block |contrast| = %.4f" % med_abs
    R["cracks"]["tag"] = "[M, from the photo]"

    # ---- speckle (continued): exclude line pixels ---------------------------------------
    sp = lower & ~ndi.binary_dilation(line_mask, iterations=2)
    # blobs by LoG at several sigma, both polarities
    res = {}
    for pol, name in ((1, "bright"), (-1, "dark")):
        cnt = {}
        for sgm in (0.8, 1.2, 1.8, 2.7):
            log = -pol * (gf(Y, sgm) - gf(Y, sgm * 1.6)) / np.maximum(gf(Y, sgm * 1.6), 1e-6)   # >0 where a blob of that polarity
            thr = 0.05
            pk = (log > thr) & (log == ndi.maximum_filter(log, size=int(2 * sgm + 1) + 2)) & sp
            cnt[sgm] = (int(pk.sum()), float(np.median(log[pk])) if pk.any() else 0.0)
        res[name] = cnt
    R["speckle"] = {
        "region_mm2": round(float(sp.sum() / px ** 2), 1),
        "per_mm2_by_sigma_px_and_polarity": {name: {str(s): round(c[0] / (sp.sum() / px ** 2), 2) for s, c in d_.items()} for name, d_ in res.items()},
        "median_peak_dog_contrast_by_sigma": {name: {str(s): round(c[1], 3) for s, c in d_.items()} for name, d_ in res.items()},
        "luma_rel_rms_dog_0.7_3px_pct": round(100 * float(np.sqrt(np.mean(((gf(Y, 0.7) - gf(Y, 3.0)) / gf(Y, 3.0))[sp] ** 2))), 2),
        "luma_rel_rms_dog_0.7_1.4px_pct": round(100 * float(np.sqrt(np.mean(((gf(Y, 0.7) - gf(Y, 1.4)) / gf(Y, 1.4))[sp] ** 2))), 2),
        "method": "blob peaks of -/+ (G(s) - G(1.6 s))/G(1.6 s) of luma, s = 0.8, 1.2, 1.8, 2.7 px, threshold 5% (relative to "
                  "the local mean), non-maximum suppressed, outside the crack lines (dilated); density per mm2; the "
                  "photo's JPEG noise and sharpening are in these numbers",
        "tag": "[M, from the photo]"}
    # one-number skewness: bright or dark specks dominate?
    hp = ((gf(Y, 0.7) - gf(Y, 3.0)) / gf(Y, 3.0))[sp]
    R["speckle"]["skew_of_dog"] = round(float(((hp - hp.mean()) ** 3).mean() / hp.std() ** 3), 2)
    R["speckle"]["dog_rel_p1_p50_p99_pct"] = [round(100 * float(np.percentile(hp, q)), 2) for q in (1, 50, 99)]
    # the photo's own blur: 10-90 rise of the sherd's outline, across the straight left edge
    # ---- 5. stain blotches -------------------------------------------------------------------
    # rusty: red-blue ratio high relative to the glaze median, smooth (sigma 0.5 mm), region = lower + upper glaze (not the band)
    rgbs = np.stack([gf(lin[..., c], 0.4 * px) for c in range(3)], -1)
    rb = rgbs[..., 0] / np.maximum(rgbs[..., 2], 1e-6)
    rb_med = np.median(rb[lower])
    rb_rel = rb / rb_med
    glaze_all = inner & ~band & ~line_mask
    stain = (rb_rel > 1.25) & glaze_all
    stain = ndi.binary_opening(stain, iterations=2)
    lab, n = ndi.label(stain)
    ar = np.bincount(lab.ravel())[1:] / px ** 2
    big = ar > 0.3
    R["stains"] = {
        "threshold": "R/B (0.4 mm smoothed, linear) > 1.25 x the glaze median R/B (= %.3f)" % rb_med,
        "blotches_over_0.3mm2": int(big.sum()),
        "area_fraction_of_glaze": round(float(np.isin(lab, np.nonzero(big)[0] + 1).sum() / glaze_all.sum()), 4),
        "equivalent_diameter_mm_p10_p50_p90": [round(float(np.percentile(2 * np.sqrt(ar[big] / math.pi), q)), 2) for q in (10, 50, 90)] if big.any() else None,
        "colour_median_srgb_8bit": [round(float(255 * x ** (1 / 2.2))) for x in np.median(lin[np.isin(lab, np.nonzero(big)[0] + 1)], 0)] if big.any() else None,
        "colour_ratio_to_glaze_linear": [round(float(x), 3) for x in np.median(lin[np.isin(lab, np.nonzero(big)[0] + 1)], 0) / med] if big.any() else None,
        "mean_rb_rel_inside": round(float(rb_rel[np.isin(lab, np.nonzero(big)[0] + 1)].mean()), 3) if big.any() else None,
        "method": "threshold of the smoothed red/blue ratio, opened 2 px; blotches over 0.3 mm2; area as a fraction of "
                  "the glaze outside the dark band and the crack lines",
        "tag": "[M, from the photo]"}
    R["stains"]["area_fraction_by_ratio_threshold"] = {}
    for tt in (1.15, 1.25, 1.4, 1.6, 2.0):
        st = ndi.binary_opening((rb_rel > tt) & glaze_all, iterations=2)
        R["stains"]["area_fraction_by_ratio_threshold"][str(tt)] = round(float(st.sum() / glaze_all.sum()), 4)
    dbg = (im * 0.6).astype(np.uint8)
    dbg[np.isin(lab, np.nonzero(big)[0] + 1)] = [255, 0, 0]
    dbg[skel] = [255, 255, 0]
    Image.fromarray(dbg).resize((W // 3, H // 3)).save(os.path.join(a.debug, "stains_cracks.png"))

    # ---- 6. the photo's light ----------------------------------------------------------------
    # backdrop: gradient of the fitted surface -> a soft broad source; fall-off in the backdrop's luma
    bl = luma(bd)
    gy_, gx_ = np.gradient(bl[::20, ::20])
    gmx, gmy = float(gx_.mean()), float(gy_.mean())
    R["light"] = {"backdrop_luma_gradient_per_px_x_y_rel": [round(gmx / bl.mean() / 20, 8), round(gmy / bl.mean() / 20, 8)],
                  "backdrop_luma_range_rel": round(float((bl.max() - bl.min()) / bl.mean()), 3)}
    # the highlight: brightest smoothed luma inside the pale step (outside the band, near the band)
    ring = ndi.binary_dilation(band, iterations=int(5 * px)) & inner & ~band
    pale = gf(Y, 2.0)
    pi = np.argmax(np.where(ring, pale, 0))
    hy, hx = divmod(pi, W)
    R["light"]["brightest_step_point_px"] = [int(hx), int(hy)]
    R["light"]["brightest_step_luma_over_glaze_median"] = round(float(pale[hy, hx] / np.median(Y[lower])), 2)
    json.dump(R, open(a.out, "w"), indent=1)
    print(json.dumps({k: R[k] for k in ("scale", "glaze_colour", "mottling")}, indent=1)[:3000])
    print("->", a.out)


if __name__ == "__main__":
    main()
