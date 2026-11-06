"""Measure a ginkgo leaf photograph for the leaf's shape and veins (objects/yinxing/leaf.py's parameters).

    python3 -I objects/yinxing/measure_ref.py PHOTO --kind lamp|scan [--px-per-mm S] [--out JSON] [--sheet PNG]

- the leaf: lamp (backlit on a light: the leaf is where blue is low), scan (on white: where the darkest channel is low);
- O, the point the veins radiate from: the least-squares point closest to the lines through every blade texel along
  its vein direction (the structure tensor's orientation of the vein lines, weighted by its coherence) [M];
- about O: the outline R(phi) (the farthest blade point along each ray), the half-angles of the lateral margins at
  several radii, the notch (the dip of R on the axis), the petiole's width;
- the vein spacing along arcs about O: the peak of the power spectrum of the green channel along the arc, detrended
  over 1 mm (needs a scale: px/mm from the scan's dpi, or assumed), and the count it implies;
- the lengths in px and, with a scale, in mm.
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image
from scipy.ndimage import (binary_fill_holes, binary_opening, gaussian_filter, gaussian_filter1d, label,
                           map_coordinates)


def leaf_mask(im, kind):
    if kind == "lamp":
        m = im[..., 2] < 150
    elif kind == "scan":
        m = im.min(2) < 200
    else:
        raise SystemExit(f"kind {kind}?")
    m = binary_fill_holes(binary_opening(m, iterations=2))
    lab, n = label(m)
    s = np.bincount(lab.ravel())
    s[0] = 0
    return lab == np.argmax(s)


def petiole_axis(m):
    """The petiole: the narrow part below the blade; returns (rows, centres, widths) from the bottom up."""
    ys, xs = np.nonzero(m)
    out = []
    for y in range(ys.max(), ys.min(), -1):
        row = np.nonzero(m[y])[0]
        if len(row) == 0:
            continue
        out.append((y, (row.min() + row.max()) / 2, row.max() - row.min() + 1))
    return np.array(out)


def radiating_centre(g, m, scale_px):
    """Structure tensor of the vein lines; the point minimising sum w (n . (p - x))^2 over blade texels, n the normal
    of the vein direction there."""
    a = gaussian_filter(g, 0.7) - gaussian_filter(g, scale_px)
    gy, gx = np.gradient(a)
    s = 2.0 * scale_px
    Jxx, Jyy, Jxy = gaussian_filter(gx * gx, s), gaussian_filter(gy * gy, s), gaussian_filter(gx * gy, s)
    tr = Jxx + Jyy
    det = Jxx * Jyy - Jxy ** 2
    disc = np.sqrt(np.maximum(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 + disc, tr / 2 - disc
    coh = ((l1 - l2) / np.maximum(l1 + l2, 1e-9)) ** 2
    ang = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)            # the gradient's direction = the vein's normal
    nx, ny = np.cos(ang), np.sin(ang)
    from scipy.ndimage import binary_erosion
    inner = binary_erosion(m, iterations=int(3 * scale_px))
    ys, xs = np.nonzero(inner[::4, ::4])
    ys, xs = ys * 4, xs * 4
    w = coh[ys, xs]
    keep = w > np.percentile(w, 50)
    ys, xs, w = ys[keep], xs[keep], w[keep]
    n = np.stack([nx[ys, xs], ny[ys, xs]], 1)
    A = np.einsum("k,ki,kj->ij", w, n, n)
    b = np.einsum("k,ki,k->i", w, n, (n * np.stack([xs, ys], 1)).sum(1))
    c = np.linalg.solve(A, b)
    res = np.abs((n * (np.stack([xs, ys], 1) - c)).sum(1))
    return c, float(np.median(res)), float(coh[inner].mean())


def polar_outline(m, c, nphi=1441):
    H, W = m.shape
    phis = np.radians(np.linspace(-180, 180, nphi))
    rmax = np.hypot(H, W)
    rs = np.arange(0, rmax, 0.5)
    R = np.full(nphi, np.nan)
    for i, p in enumerate(phis):
        x, y = c[0] + rs * np.sin(p), c[1] - rs * np.cos(p)
        ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
        v = map_coordinates(m.astype(float), [y[ok], x[ok]], order=0) > 0.5
        if v.any():
            R[i] = rs[ok][np.nonzero(v)[0].max()]
    return np.degrees(phis), R


def lateral_angles(m, c, radii_px):
    """Half-angles of the blade at radius r: the angular extent of the blade on the arc, left and right."""
    out = []
    H, W = m.shape
    for r in radii_px:
        th = np.radians(np.linspace(-150, 150, 3001))
        x, y = c[0] + r * np.sin(th), c[1] - r * np.cos(th)
        ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
        v = np.zeros_like(th, bool)
        v[ok] = map_coordinates(m.astype(float), [y[ok], x[ok]], order=0) > 0.5
        if v.any():
            k = np.nonzero(v)[0]
            out.append((r, float(np.degrees(th[k.min()])), float(np.degrees(th[k.max()]))))
    return out


def arc_spacing(g, m, c, r, pxmm):
    n = int(math.pi * r * 2)
    th = np.linspace(-math.pi * 0.75, math.pi * 0.75, n)
    x, y = c[0] + r * np.sin(th), c[1] - r * np.cos(th)
    H, W = m.shape
    ok = (x > 0) & (x < W - 1) & (y > 0) & (y < H - 1)
    inl = np.zeros(n, bool)
    inl[ok] = map_coordinates(m.astype(float), [y[ok], x[ok]], order=0) > 0.5
    idx = np.nonzero(inl)[0]
    if len(idx) < 64:
        return None
    pad = int(0.5 * pxmm)
    seg = np.arange(idx[0] + pad, idx[-1] - pad)
    if len(seg) < 64:
        return None
    v = map_coordinates(g, [y[seg], x[seg]], order=1)
    ds = r * (th[1] - th[0]) / pxmm
    hp = v - gaussian_filter1d(v, 1.0 / ds)
    hp = hp * np.hanning(len(hp))
    P = np.abs(np.fft.rfft(hp)) ** 2
    fr = np.fft.rfftfreq(len(hp), ds)
    sel = (fr > 1.0) & (fr < min(8.0, 0.4 / ds))
    if sel.sum() < 5:
        return None
    Ps = gaussian_filter1d(P[sel], 2)
    k = np.argmax(Ps)
    L = len(hp) * ds
    return {"r_mm": round(r / pxmm, 2), "arc_mm": round(L, 2), "spacing_mm": round(1 / fr[sel][k], 3),
            "count": int(round(L * fr[sel][k]))}


def junction(pet, pw):
    """O, the petiole's top: going up the petiole, the last row before the width passes 1.5 petiole widths."""
    for y, xc, w in pet:
        if w > 1.5 * pw:
            return np.array([xc, y + 1.0])
    raise SystemExit("no junction found")


def fourier_fit(phi_deg, R, K, exclude_deg):
    """R(phi) ~ a0 + sum_k (a_k cos k phi + b_k sin k phi), least squares, the notch excluded."""
    ph = np.radians(phi_deg)
    ok = np.isfinite(R) & (np.abs(phi_deg) > exclude_deg)
    A = [np.ones_like(ph)]
    for k in range(1, K + 1):
        A += [np.cos(k * ph), np.sin(k * ph)]
    A = np.stack(A, 1)
    coef, *_ = np.linalg.lstsq(A[ok], R[ok], rcond=None)
    return coef, A @ coef


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--kind", required=True)
    ap.add_argument("--px-per-mm", type=float)
    ap.add_argument("--out")
    ap.add_argument("--fourier-order", type=int, default=10)
    ap.add_argument("--notch-exclude-deg", type=float, default=6.0)
    ap.add_argument("--corner-deg", type=float, default=95.0, help="the lateral corners, about the radiating centre")
    a = ap.parse_args()
    im = np.asarray(Image.open(a.photo).convert("RGB")).astype(float)
    m = leaf_mask(im, a.kind)
    g = im[..., 1]
    pet = petiole_axis(m)
    pw = float(np.median(pet[:20, 2]))
    pxmm = a.px_per_mm
    scale_px = max(2.0, 3 * pw / 2 / 1.0) if pxmm is None else pxmm
    c, res, coh = radiating_centre(g, m, scale_px if pxmm is None else pxmm)
    phi, R = polar_outline(m, c)
    ys, xs = np.nonzero(m)
    blade_rows = [p for p in pet if p[2] > 3 * pw]
    out = {"photo": os.path.basename(a.photo), "kind": a.kind, "px_per_mm": pxmm,
           "size_px": [int(m.shape[1]), int(m.shape[0])],
           "leaf_bbox_px": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
           "petiole_width_px": pw,
           "radiating_centre_px": [round(float(c[0]), 1), round(float(c[1]), 1)],
           "radiating_fit_median_residual_px": round(res, 2), "vein_coherence_mean": round(coh, 3),
           "blade_width_px": int(xs.max() - xs.min()),
           "R_phi_px": {f"{p:.0f}": (round(float(r), 1) if np.isfinite(r) else None)
                        for p, r in zip(phi[::20], R[::20])}}
    Rok = np.where(np.isfinite(R), R, 0)
    inside = (np.abs(phi) < 100)
    out["R_max_px"] = round(float(Rok[inside].max()), 1)
    O = junction(pet, pw)
    out["junction_px"] = [round(float(O[0]), 1), round(float(O[1]), 1)]
    out["centre_above_junction_px"] = round(float(O[1] - c[1]), 1)
    out["centre_right_of_junction_px"] = round(float(c[0] - O[0]), 1)
    notch_ex = a.notch_exclude_deg
    coef, Rf = fourier_fit(phi, R, a.fourier_order, notch_ex)
    res = R - Rf
    dist = np.isfinite(R) & (np.abs(phi) < a.corner_deg) & (np.abs(phi) > notch_ex)
    out["fourier_order"] = a.fourier_order
    out["fourier_px"] = [round(float(v), 2) for v in coef]
    out["undulation_rms_px"] = round(float(np.nanstd(res[dist])), 2)
    ax = np.abs(phi) <= notch_ex
    k = np.nanargmin(np.where(ax, R - Rf, np.inf))
    out["notch"] = {"depth_px": round(float(Rf[k] - R[k]), 1), "at_deg": round(float(phi[k]), 2)}
    # the notch's width at half its depth
    half = ax & (R - Rf < -0.5 * (Rf[k] - R[k]))
    if half.any():
        out["notch"]["width_at_half_depth_deg"] = round(float(phi[half].max() - phi[half].min()), 2)
    # undulation spectrum: arc-length wavelengths of the residual's power peak
    rr = np.where(dist, res, 0.0)
    ds = np.radians(phi[1] - phi[0]) * out["R_max_px"]
    P = np.abs(np.fft.rfft(rr * np.hanning(len(rr)))) ** 2
    fr = np.fft.rfftfreq(len(rr), ds)
    sel = fr > 0
    out["undulation_peak_wavelength_px"] = round(float(1 / fr[sel][np.argmax(P[sel])]), 1)
    axis = np.abs(phi) < 3
    lobes = (np.abs(phi) > 5) & (np.abs(phi) < 40)
    out["R_axis_px"] = round(float(np.min(Rok[axis])), 1)
    out["R_lobes_px"] = round(float(np.median(Rok[lobes])), 1)
    rr = [f * out["R_max_px"] for f in (0.1, 0.2, 0.3, 0.5, 0.7)]
    out["half_angles_deg_at_px"] = [(round(r, 1), round(lo, 1), round(hi, 1)) for r, lo, hi in lateral_angles(m, c, rr)]
    if pxmm:
        out["arcs"] = [s for s in (arc_spacing(g, m, c, r * pxmm, pxmm) for r in (4, 6, 8, 12, 16, 20, 25, 30, 35)) if s]
        out["mm"] = {"centre_above_junction": round(out["centre_above_junction_px"] / pxmm, 2),
                     "fourier": [round(v / pxmm, 3) for v in out["fourier_px"]],
                     "undulation_rms": round(out["undulation_rms_px"] / pxmm, 3),
                     "undulation_peak_wavelength": round(out["undulation_peak_wavelength_px"] / pxmm, 2),
                     "notch_depth": round(out["notch"]["depth_px"] / pxmm, 2),
                     "petiole_width": round(pw / pxmm, 2), "blade_width": round((xs.max() - xs.min()) / pxmm, 1),
                     "R_max": round(out["R_max_px"] / pxmm, 1), "R_axis": round(out["R_axis_px"] / pxmm, 1),
                     "R_lobes": round(out["R_lobes_px"] / pxmm, 1)}
    s = json.dumps(out, indent=1)
    print(s)
    if a.out:
        open(a.out, "w").write(s)


if __name__ == "__main__":
    main()
