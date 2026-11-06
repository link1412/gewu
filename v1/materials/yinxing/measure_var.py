"""The leaf's spatial variation, measured the same way on the backlit photo and on a render of the lamp card.

    python3 -I materials/yinxing/measure_var.py [RENDER.exr ...] [--out JSON] [--maps DIR]

Everything on the green channel, linear (the photo: sRGB decoded, over the lamp's white; a render: compare.develop),
on the blade (the leaf mask 0.5 mm in from the margin), px/mm from card.json / lamp_outline.json (16 px/mm, itself
[D/A]: the photo's vein spacing set to Leigh's 0.69 mm). The photo is a phone JPEG: its tone curve is not undone
beyond the sRGB decoding [A], so contrasts are the phone's.

The image is split into four parts, each with its numbers:
- veins: the white top-hat (the image minus its grey opening by a 5 px disk, 0.31 mm): what is lighter than its
  surroundings and narrower than that. 'lamina' is the opening itself (the blade with the veins taken out).
- margin: the median of log(lamina) against the distance d to the margin (0.25 mm bins to 2 mm, then wider),
  relative to the median over d 8-20 mm;
- spots: log(lamina) minus its 1.5 mm median: connected regions below -0.35 (30 % darker than around them),
  at least 3 px: their number per cm2 (blade d > 1 mm), equivalent diameter, depth (the minimum), elongation (the
  second moments' axis ratio) and the angle of the long axis to the local vein direction;
- streaks and blotches: the rest, log(lamina) minus the margin profile, with the spots filled by their surroundings:
  its standard deviation after removing scales over 6 mm, and its autocorrelation lengths along and across the
  veins (in a window on the leaf's axis where the veins run within 15 degrees of the image's vertical);
- the veins' strength: in the same window, each vein's top-hat profile along its length (a column of the window with
  a vein in it, the max over +-1 px): the coefficient of variation of the top-hat peak along a vein, between veins,
  and the along-vein autocorrelation length.
Lengths are 1/e lengths of the normalised autocorrelation (linear interpolation between pixels).
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.ndimage import (binary_dilation, binary_erosion, binary_fill_holes, binary_opening, distance_transform_edt,
                           gaussian_filter, grey_opening, label, median_filter, find_objects)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import camera  # noqa: E402,F401  (tools/compare first: camera imports it by that name)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("yinxing_compare", os.path.join(HERE, "compare.py"))
CMP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CMP)


SPOT_DLOG = -0.6       # a spot: 45 % darker than the lamina's 1.5 mm median around it (looser thresholds pick up the
                       # phone JPEG's 8 x 8 blocks and the interveinal mottling) [A]
SPOT_MIN_PX = 4
PATCH_DLOG = -0.2     # a diffuse patch: 18 % darker than its 4 mm median, after the dark spots are filled [A] (S8 r2)
PATCH_MIN_MM = 0.4    # at least this equivalent diameter [A]


def trace_veins(top, vdir, win, pxmm, length_mm=12.0):
    """Each vein's top-hat profile along its own path: seeds at the top-hat's peaks along the window's top row, then
    a step of 1 px along the local vein direction (pointing down the image, towards the base), recentred each step on
    the top-hat's max within +-1 px across; stops when it leaves the window."""
    from scipy.signal import find_peaks
    from scipy.ndimage import map_coordinates
    ys, xs = np.nonzero(win)
    y0 = ys.min() + 2
    row = np.where(win[y0], top[y0 - 1:y0 + 2].mean(0), 0)
    pk, _ = find_peaks(row, distance=max(2, int(0.45 * pxmm)), height=np.percentile(row[win[y0]], 60))
    n = int(length_mm * pxmm)
    profs = []
    for x in pk:
        p = np.array([float(x), float(y0)])
        v = []
        for _ in range(n):
            a = vdir[int(round(p[1])), int(round(p[0]))]
            t = np.array([np.cos(a), np.sin(a)])
            if t[1] < 0:
                t = -t
            p = p + t
            nrm = np.array([-t[1], t[0]])
            cand = [p + k * 0.5 * nrm for k in (-2, -1, 0, 1, 2)]
            vals = map_coordinates(top, [[c[1] for c in cand], [c[0] for c in cand]], order=1)
            p = cand[int(np.argmax(vals))]
            iy, ix = int(round(p[1])), int(round(p[0]))
            if not (0 <= iy < win.shape[0] and 0 <= ix < win.shape[1]) or not win[iy, ix]:
                break
            v.append(float(vals.max()))
        if len(v) >= 0.8 * n:
            profs.append(np.array(v[: int(0.8 * n)]))
    return profs


def disk(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def efold(ac):
    """The first lag where the normalised autocorrelation drops below 1/e (linear interpolation), in samples."""
    ac = ac / ac[0]
    k = np.nonzero(ac < np.exp(-1))[0]
    if len(k) == 0:
        return float("nan")
    k = k[0]
    return float(k - 1 + (ac[k - 1] - np.exp(-1)) / (ac[k - 1] - ac[k]))


def autocorr_2d(f, w):
    f = np.where(w, f - f[w].mean(), 0.0)
    F = np.fft.rfft2(f, s=(2 * f.shape[0], 2 * f.shape[1]))
    Wf = np.fft.rfft2(w.astype(float), s=(2 * f.shape[0], 2 * f.shape[1]))
    num = np.fft.irfft2(F * np.conj(F))
    den = np.fft.irfft2(Wf * np.conj(Wf))
    return num / np.maximum(den, 1)


def measure(lin, pxmm, maps=None, gain=None):
    g = np.clip(lin[..., 1], 1e-4, None)
    full = CMP.biggest(binary_fill_holes(binary_opening(lin[..., 2] < 0.5, iterations=2)))
    m = binary_erosion(full, iterations=int(0.5 * pxmm))
    d = distance_transform_edt(full) / pxmm
    se = disk(int(round(0.155 * pxmm)))
    gm = np.where(full, g, 0)
    lam = grey_opening(gm, footprint=se)
    top = gm - lam
    L = np.log(np.clip(lam, 1e-4, None))
    out = {"px_per_mm": pxmm}
    # margin profile
    core = m & (d > 8) & (d < 20)
    ref = float(np.median(L[core]))
    edges = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3, 4, 5, 6, 8, 12, 20]
    prof = []
    for a, b in zip(edges[:-1], edges[1:]):
        s = full & (d >= a) & (d < b)
        prof.append([round((a + b) / 2, 3), round(float(np.median(L[s]) - ref), 4)])
    out["margin_profile_dlogG"] = prof
    # spots
    k = int(round(1.5 * pxmm)) | 1
    loc = median_filter(np.where(full, L, ref), size=k)
    r = np.where(m, L - loc, 0)
    spots = (r < SPOT_DLOG) & m & (d > 1.0)
    lab, n = label(spots)
    sizes = np.bincount(lab.ravel())
    keep = np.nonzero(sizes >= SPOT_MIN_PX)[0]
    keep = keep[keep > 0]
    # the vein direction: structure tensor of the top-hat
    a = gaussian_filter(top, 1.0)
    gy, gx = np.gradient(a)
    s = 1.0 * pxmm
    Jxx, Jyy, Jxy = gaussian_filter(gx * gx, s), gaussian_filter(gy * gy, s), gaussian_filter(gx * gy, s)
    normal = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    vdir = normal + np.pi / 2                                    # the veins' direction (image x right, y down)
    rec = []
    sl = find_objects(lab)
    for i in keep:
        ys, xs = np.nonzero(lab[sl[i - 1]] == i)
        ys = ys + sl[i - 1][0].start
        xs = xs + sl[i - 1][1].start
        A = len(ys)
        cov = np.cov(np.stack([xs, ys])) if A > 2 else np.eye(2)
        ev, evec = np.linalg.eigh(cov + 1e-6 * np.eye(2))
        ax = np.arctan2(evec[1, 1], evec[0, 1])
        vd = float(np.median(vdir[ys, xs]))
        ang = abs(((ax - vd) + np.pi / 2) % np.pi - np.pi / 2)
        rec.append((2 * np.sqrt(A / np.pi) / pxmm, float(r[ys, xs].min()), float(np.sqrt(ev[1] / max(ev[0], 1e-6))),
                    np.degrees(ang)))
    rec = np.array(rec) if rec else np.zeros((0, 4))
    area_cm2 = float((m & (d > 1.0)).sum()) / pxmm ** 2 / 100
    q = lambda v: [round(float(x), 3) for x in np.percentile(v, [10, 50, 90])] if len(v) else None
    out["spots"] = {"per_cm2": round(len(rec) / area_cm2, 2), "count": int(len(rec)), "area_cm2": round(area_cm2, 2),
                    "diameter_mm_p10_50_90": q(rec[:, 0]), "depth_dlogG_p10_50_90": q(rec[:, 1]),
                    "elongation_p10_50_90": q(rec[:, 2]),
                    "angle_to_veins_deg_median": round(float(np.median(rec[rec[:, 2] > 1.5, 3])), 1) if (rec[:, 2] > 1.5).any() else None,
                    "share_elongated_over_1.5": round(float((rec[:, 2] > 1.5).mean()), 3) if len(rec) else None,
                    "cover_share": round(float(spots.sum()) / float((m & (d > 1.0)).sum()), 4)}
    # (S8 r2) the dark spots' edges and clustering
    if len(rec):
        gy_, gx_ = np.gradient(L)
        gm_ = np.hypot(gx_, gy_) * pxmm                       # |grad log G| per mm
        edge_w, cen = [], []
        for i in keep:
            sub = lab[sl[i - 1]] == i
            ring = binary_dilation(sub, iterations=1) & ~binary_erosion(sub, iterations=1)
            ys, xs = np.nonzero(ring)
            ys = ys + sl[i - 1][0].start; xs = xs + sl[i - 1][1].start
            ok = (ys < L.shape[0]) & (xs < L.shape[1])
            gmax = np.percentile(gm_[ys[ok], xs[ok]], 75)
            yy, xx = np.nonzero(sub)
            cen.append((yy.mean() + sl[i - 1][0].start, xx.mean() + sl[i - 1][1].start))
            edge_w.append(gmax)
        depth = -rec[:, 1]
        ew = depth / np.maximum(np.array(edge_w), 1e-6)       # depth over the edge's steepest slope: the edge's width, mm
        cen = np.array(cen) / pxmm
        from scipy.spatial import cKDTree
        dd, _ = cKDTree(cen).query(cen, k=2)
        nn = dd[:, 1]
        lam_ = len(rec) / area_cm2 / 100                      # per mm2
        out["spots"]["edge_width_mm_p10_50_90"] = q(ew)
        out["spots"]["clark_evans_R"] = round(float(nn.mean() / (0.5 / np.sqrt(lam_))), 3)
        out["spots"]["nn_mm_p10_50_90"] = q(nn)
        # clumping at a coarser scale: spot counts in 3 mm cells wholly on the blade (d > 1 mm), variance / mean
        cellpx = int(3 * pxmm)
        okm = m & (d > 1.0)
        cnt = []
        cyx = (cen * pxmm).astype(int)
        for y0_ in range(0, okm.shape[0] - cellpx, cellpx):
            for x0_ in range(0, okm.shape[1] - cellpx, cellpx):
                if okm[y0_:y0_ + cellpx, x0_:x0_ + cellpx].all():
                    cnt.append(int(((cyx[:, 0] >= y0_) & (cyx[:, 0] < y0_ + cellpx) & (cyx[:, 1] >= x0_) & (cyx[:, 1] < x0_ + cellpx)).sum()))
        cnt = np.array(cnt)
        out["spots"]["dispersion_3mm_cells"] = round(float(cnt.var() / max(cnt.mean(), 1e-9)), 3)
        out["spots"]["cells"] = int(len(cnt))
        # (S8 r3) density against the distance to the margin (centroids), and the depth spread
        dc = d[np.clip(cyx[:, 0], 0, d.shape[0] - 1), np.clip(cyx[:, 1], 0, d.shape[1] - 1)]
        for nm, a_, b_ in (("d1_3mm", 1.0, 3.0), ("d3_8mm", 3.0, 8.0), ("d8plus", 8.0, 1e9)):
            ar = float((m & (d >= a_) & (d < b_)).sum()) / pxmm ** 2 / 100
            out["spots"].setdefault("per_cm2_by_margin_distance", {})[nm] = round(float(((dc >= a_) & (dc < b_)).sum()) / max(ar, 1e-9), 2)
        out["spots"]["edge_width_over_diameter_p10_50_90"] = q(ew / np.maximum(rec[:, 0], 1e-6))
    # (S8 r2) diffuse patches: shallow, broad darkenings, the dark spots taken out first
    sp_big = binary_dilation(spots, iterations=3)
    Ls = gaussian_filter(np.where(sp_big, loc, L), 0.1 * pxmm)
    k4 = int(round(4 * pxmm)) | 1
    loc4 = median_filter(np.where(full, Ls, ref), size=k4)
    r4 = np.where(m & (d > 1.0), Ls - loc4, 0)
    pt = (r4 < PATCH_DLOG) & m & (d > 1.0) & ~sp_big
    labp, _ = label(pt)
    szp = np.bincount(labp.ravel()); szp[0] = 0
    min_px = int(np.pi * (PATCH_MIN_MM * pxmm / 2) ** 2)
    kp = np.nonzero(szp >= min_px)[0]
    slp = find_objects(labp)
    prec = []
    for i in kp:
        ys, xs = np.nonzero(labp[slp[i - 1]] == i)
        prec.append((2 * np.sqrt(len(ys) / np.pi) / pxmm, float(r4[slp[i - 1]][ys, xs].min())))
    prec = np.array(prec) if prec else np.zeros((0, 2))
    out["patches"] = {"per_cm2": round(len(prec) / area_cm2, 2), "diameter_mm_p10_50_90": q(prec[:, 0]) if len(prec) else None,
                      "depth_dlogG_p10_50_90": q(prec[:, 1]) if len(prec) else None,
                      "cover_share": round(float(np.isin(labp, kp).sum()) / float((m & (d > 1.0)).sum()), 4)}
    # (S8 r2) the margin's browning along the margin: log lamina 0.3-1.2 mm in, per 0.5 mm of the margin
    import cv2 as _cv2
    cs, _ = _cv2.findContours(full.astype(np.uint8), _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_NONE)
    C_ = max(cs, key=len)[:, 0, :].astype(float)
    band = full & (d >= 0.3) & (d <= 1.2)
    Lb = np.where(band, L, 0)
    wsum = gaussian_filter(band.astype(float), 0.4 * pxmm)
    Lbs = gaussian_filter(Lb, 0.4 * pxmm) / np.maximum(wsum, 1e-3)
    # walk the contour, step 0.5 mm, and read the band's mean at the nearest band pixel inward
    sarc = np.r_[0, np.cumsum(np.hypot(*np.diff(C_, axis=0).T))]
    tt = np.arange(0, sarc[-1], 0.5 * pxmm)
    cx_, cy_ = np.interp(tt, sarc, C_[:, 0]), np.interp(tt, sarc, C_[:, 1])
    _, (iy, ix) = distance_transform_edt(~band, return_indices=True)
    vals, ok = [], []
    H_, W_ = L.shape
    ybase = np.nonzero(full.any(1))[0].max()
    for x_, y_ in zip(cx_, cy_):
        yi, xi = int(round(y_)), int(round(x_))
        yi, xi = min(max(yi, 0), H_ - 1), min(max(xi, 0), W_ - 1)
        vals.append(Lbs[iy[yi, xi], ix[yi, xi]] - ref)
        ok.append(y_ < ybase - 12 * pxmm)                     # leave out the petiole's end and the base's narrow wedge
    vals, ok = np.array(vals), np.array(ok)
    v = vals[ok]
    vv = v - v.mean()
    acm = np.correlate(vv, vv, "full")[len(vv) - 1:] / np.arange(len(vv), 0, -1)
    out["margin_along"] = {"samples": int(len(v)), "mean_dlogG": round(float(v.mean()), 3),
                           "std_dlogG": round(float(v.std()), 3), "p10_50_90": q(v),
                           "corr_len_mm": round(efold(acm[: len(vv) // 4]) * 0.5, 2)}
    if gain is not None:
        gl = g / gain
        lamb = np.where(full, grey_opening(np.where(full, gl, 0), footprint=se), 0)
        out["local_white"] = {"blade_median_G": round(float(np.median(gl[m])), 4),
                              "lamina_p90_G": round(float(np.percentile(lamb[m & (d > 2)], 90)), 4),
                              "lamina_median_over_p90": round(float(np.median(lamb[m & (d > 2)]) / np.percentile(lamb[m & (d > 2)], 90)), 4),
                              "blade_median_RGB": [round(float(np.median((lin[..., c] / gain)[m])), 4) for c in range(3)]}
    # streaks / blotches: the rest
    prof_d = np.array([p[0] for p in prof]); prof_v = np.array([p[1] for p in prof])
    marg = np.interp(d, prof_d, prof_v)
    big = binary_dilation(spots, iterations=2)
    rest = np.where(big, loc, L) - ref - marg
    rest = rest - gaussian_filter(np.where(m, rest, 0), 6 * pxmm / 2.355) / np.maximum(gaussian_filter(m.astype(float), 6 * pxmm / 2.355), 1e-3)
    inner = m & (d > 2.0)
    out["rest_std_dlogG"] = round(float(np.std(rest[inner])), 4)
    # (S8 r2) the same with the pixel-scale noise (the JPEG's blocks and grain) smoothed off, and the broad drift
    # (scales over 3 mm, the margin profile removed) that 'rest' leaves out
    out["rest_std_dlogG_smooth_0.15mm"] = round(float(np.std(gaussian_filter(np.where(m, rest, 0), 0.15 * pxmm)[inner])), 4)
    raw_rest = np.where(big, loc, L) - ref - marg
    wgt = gaussian_filter(m.astype(float), 3 * pxmm)
    drift = gaussian_filter(np.where(m, raw_rest, 0), 3 * pxmm) / np.maximum(wgt, 1e-3)
    out["drift_std_dlogG_3mm"] = round(float(np.std(drift[m & (d > 4.0)])), 4)
    # (S8 r3) the fine texture between the spots: log lamina band-passed 0.06-0.3 mm (DoG), the spots (dilated 0.25 mm)
    # and the margin (d < 3 mm) left out; and its anisotropy (std of the along-vein derivative over the across one)
    fine = gaussian_filter(np.where(big, loc, L), 0.06 * pxmm) - gaussian_filter(np.where(big, loc, L), 0.3 * pxmm)
    fm = m & (d > 3.0) & ~binary_dilation(spots, iterations=int(0.25 * pxmm))
    out["fine_bp_std_dlogG"] = round(float(np.std(fine[fm])), 4)
    fy, fx = np.gradient(fine)
    vd_ = vdir
    along_ = fx * np.cos(vd_) + fy * np.sin(vd_)
    across_ = -fx * np.sin(vd_) + fy * np.cos(vd_)
    out["fine_grad_across_over_along"] = round(float(np.std(across_[fm]) / max(np.std(along_[fm]), 1e-9)), 3)
    # (S8 r2) the veins in the browned margin: top-hat over lamina 0.3-1.5 mm in, against 4-12 mm in
    for nm, a_, b_ in (("margin", 0.3, 1.5), ("inner", 4.0, 12.0)):
        z = full & (d >= a_) & (d < b_) & (top > np.percentile(top[full & (d >= a_) & (d < b_)], 90))
        out.setdefault("vein_tophat_over_lamina_p90px", {})[nm] = round(float(np.median(top[z] / np.maximum(lam[z], 1e-4))), 3)
    # the axis window: veins near vertical
    H, W = g.shape
    ys, xs = np.nonzero(full)
    cx = float(np.median(xs[ys < np.percentile(ys, 30)]))
    ang_v = np.degrees(np.abs(((vdir - np.pi / 2) + np.pi / 2) % np.pi - np.pi / 2))
    win = np.zeros_like(m)
    y0, y1 = int(ys.min() + 4 * pxmm), int(ys.min() + 24 * pxmm)
    x0, x1 = int(cx - 6 * pxmm), int(cx + 6 * pxmm)
    win[y0:y1, x0:x1] = True
    win &= inner & (ang_v < 15)
    out["window_px"] = [x0, y0, x1, y1]
    out["window_share_kept"] = round(float(win[y0:y1, x0:x1].mean()), 3)
    ac = autocorr_2d(np.where(win, rest, 0.0)[y0:y1, x0:x1], win[y0:y1, x0:x1])
    out["rest_corr_len_mm"] = {"along": round(efold(ac[:, 0]) / pxmm, 3), "across": round(efold(ac[0, :]) / pxmm, 3)}
    # vein strength along the veins (traced)
    swin = np.zeros_like(m)
    swin[y0:y1, x0:x1] = True
    swin &= inner
    profs = trace_veins(top, vdir, swin, pxmm)
    lamv = np.median(lam[win])
    if profs:
        P = np.array(profs)
        lens = []
        for v in P:
            vv = v - v.mean()
            acv = np.correlate(vv, vv, "full")[len(vv) - 1:] / np.arange(len(vv), 0, -1)
            lens.append(efold(acv[: len(vv) // 2]))
        out["vein_strength"] = {"veins": int(len(P)), "tophat_over_lamina_median": round(float(np.median(P) / lamv), 4),
                                "cv_along_vein": round(float(np.median(P.std(1) / P.mean(1))), 3),
                                "cv_between_veins": round(float(P.mean(1).std() / P.mean(1).mean()), 3),
                                "corr_len_along_mm_median": round(float(np.nanmedian(lens)) / pxmm, 3)}
    # the veins' colour: the top-hat per channel at strong vein pixels over the lamina there
    tops = []
    for ch in range(2):
        c = np.where(full, np.clip(lin[..., ch], 0, None), 0)
        tops.append(c - grey_opening(c, footprint=se))
    strong = inner & (top > np.percentile(top[inner], 95))
    lamR = grey_opening(np.where(full, np.clip(lin[..., 0], 0, None), 0), footprint=se)
    ex = np.array([np.median(tops[0][strong]), np.median(tops[1][strong])])
    ba = np.array([np.median(lamR[strong]), np.median(lam[strong])])
    out["vein_excess"] = {"dR": round(float(ex[0]), 4), "dG": round(float(ex[1]), 4), "lamR": round(float(ba[0]), 4),
                          "lamG": round(float(ba[1]), 4),
                          "excess_G_over_R_rel_lamina_G_over_R": round(float((ex[1] / ex[0]) / (ba[1] / ba[0])), 3)}
    if maps:
        os.makedirs(maps, exist_ok=True)
        from PIL import Image
        def save(name, a, lo, hi):
            Image.fromarray((np.clip((a - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)).save(os.path.join(maps, name))
        save("lamina_logG.png", np.where(full, L - ref, -3), -2, 0.5)
        save("rest.png", np.where(m, rest, 0), -0.6, 0.6)
        save("tophat.png", top / max(lamv, 1e-6), 0, 1.0)
        save("spots.png", spots.astype(float), 0, 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("renders", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--maps")
    ap.add_argument("--gain", help="lampfield.json: also report the blade over the lamp's local white (S8 r2)")
    a = ap.parse_args()
    pxmm = json.load(open(os.path.join(ROOT, "objects/yinxing/lamp_outline.json")))["outline"]["px_per_mm"]
    res = {}
    plin, _, _ = CMP.photo_linear("lamp")
    gain = None
    if a.gain:
        import lampfield
        lj = json.load(open(a.gain))
        Y, X = np.mgrid[0:plin.shape[0], 0:plin.shape[1]]
        ox, oy = lj["O_px"]
        gain = lampfield.gain_at_mm(lj, (X - ox) / lj["px_per_mm"], (oy - Y) / lj["px_per_mm"])
    res["photo"] = measure(plin, pxmm, os.path.join(a.maps, "photo") if a.maps else None, gain)
    for r in a.renders:
        card = json.load(open(os.path.join(os.path.dirname(os.path.abspath(r)), "card.json")))
        card.setdefault("sensor", "canon_eos_5d_mkiv")
        lin, _ = CMP.develop(r, card, "lamp")
        name = os.path.relpath(os.path.abspath(r), ROOT)
        res[name] = measure(lin, card["px_per_mm"], os.path.join(a.maps, name.replace("/", "_")) if a.maps else None,
                            gain if card.get("lamp_field") else (np.ones(lin.shape[:2]) if gain is not None else None))
    s = json.dumps(res, indent=1)
    print(s)
    if a.out:
        open(a.out, "w").write(s)


if __name__ == "__main__":
    main()
