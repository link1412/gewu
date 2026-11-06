"""The leaf's late-autumn state as maps, made by a process with parameters (material.json "senescence"), not painted.

    python3 -I materials/yinxing/senescence.py SET OBJDIR OUTDIR [--seed N]   # -> OUTDIR/brown.exr, veinamt.exr, senescence.json

OBJDIR is a leaf built by objects/yinxing/leaf.py (veins.json, veins.exr); the maps share veins.exr's grid and UVs.

- brown.exr: the brown pigment, PROSPECT-D's Cbrown (arbitrary units, as Feret et al. 2017), per texel. The sum of:
  - streaks: Cb0 * max(0, n - theta) (S8 r2; round 1 was log-normal, whose tail made broad smudges and whose
    floor browned the whole blade), n a unit Gaussian random field stretched along the veins (white noise blurred
    across the veins by sigma_across, then along the local vein direction by sigma_along), so part of the blade
    stays clean; a broad isotropic drift of the same form (S8 r2);
  - the margin: A exp(-d / l) (d the distance to the margin) times a log-normal factor of its own field along the
    veins (tongues reaching in along the veins);
  - the margin's A varies along the margin (log-normal, an isotropic field; S8 r2);
  - dark specks (S8 r2): a Thomas cluster process of flat ellipses with a sharp ragged edge, long axis along the
    veins, diameter, elongation and depth log-normal, no halo; diffuse patches: Poisson, shallow Gaussian bumps.
  - the vein column's brown is the lamina's times vein_brown_factor (brown_vein.exr; S8 r2).
  - S8 r3: the specks' density rises toward the margin (inhomogeneous Poisson by thinning), near the margin they are
    bigger, rounder, darker; each speck has its own edge width (log-normal: a few sharp pin-points, most soft), a
    quarter have a faint halo; a thin dark crust along the edge; a fine fibrous mottle between the veins; the
    margin's A is higher where the veins run along the margin (lateral) than where they end on it (distal).
  Pigment concentrations add (Beer), so the three add in Cbrown.
- veinamt.exr: the vein map re-rasterised with each vein's strength g(s) along its own arc length s (two
  Ornstein-Uhlenbeck paths, fast and slow, continued through the forks; S8 r2: round 1's 2-D field made the veins
  wander sideways): width w * g^beta_w, share times g^beta_a, clipped to [0, 1]. It is the mix amount between the
  lamina and the vein column (optics.py).
The vein direction: the doubled-angle tangents of the vein tree (veins.json), smoothed, so it follows the veins.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates, zoom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "objects/yinxing"))
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2  # noqa: E402


def params(m, which):
    S = m.get("senescence")
    if S is None:
        raise SystemExit("material.json has no 'senescence'")
    out = {}
    for k, e in S.items():
        if not isinstance(e, dict) or "value" not in e:
            continue
        v = e["value"]
        if isinstance(v, dict):
            if which not in v:
                raise SystemExit(f"senescence.{k}: no value for the set {which!r}")
            v = v[which]
        if v is None:
            raise SystemExit(f"senescence.{k}: not set for {which!r}")
        out[k] = v
    return out


def read_exr1(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if a is None:
        raise SystemExit(f"cannot read {p}")
    return a[..., 0].astype(np.float32) if a.ndim == 3 else a.astype(np.float32)


def write_exr(path, a):
    a = np.asarray(a, np.float32)
    if not cv2.imwrite(path, np.repeat(a[..., None], 3, 2), [cv2.IMWRITE_EXR_TYPE, cv2.IMWRITE_EXR_TYPE_FLOAT,
                                                              cv2.IMWRITE_EXR_COMPRESSION, cv2.IMWRITE_EXR_COMPRESSION_ZIP]):
        raise SystemExit(f"could not write {path}")


class Frame:
    """veins.exr's grid: row 0 at y max (leaf.Grid)."""

    def __init__(self, box, shape):
        self.x0, self.y0, self.x1, self.y1 = box
        self.H, self.W = shape
        self.t = (self.x1 - self.x0) / self.W

    def ij(self, x, y):
        return (self.y1 - y) / self.t - 0.5, (x - self.x0) / self.t - 0.5


def direction_field(veins, F, step):
    """Unit vein direction (in image rows/cols: dr, dc) on a grid 'step' texels coarse, from the vein tree."""
    h, w = math.ceil(F.H / step), math.ceil(F.W / step)
    acc = np.zeros((2, h, w))
    for V in veins:
        P = np.asarray(V["pts"], float)
        for a, b in zip(P[:-1], P[1:]):
            L = float(np.hypot(*(b - a)))
            n = max(2, int(L / (F.t * step)) + 1)
            s = np.linspace(0, 1, n)
            x, y = a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1])
            i, j = F.ij(x, y)
            i, j = np.clip((i / step).astype(int), 0, h - 1), np.clip((j / step).astype(int), 0, w - 1)
            dr, dc = -(b[1] - a[1]) / L, (b[0] - a[0]) / L          # rows go down as y goes up
            th = math.atan2(dr, dc)
            np.add.at(acc[0], (i, j), math.cos(2 * th))
            np.add.at(acc[1], (i, j), math.sin(2 * th))
    sm = [gaussian_filter(a, 3.0) for a in acc]
    big = [gaussian_filter(a, 15.0) for a in acc]
    mag = np.hypot(*sm)
    cx = np.where(mag > 1e-3, sm[0], big[0])
    sx = np.where(mag > 1e-3, sm[1], big[1])
    th = 0.5 * np.arctan2(sx, cx)
    return np.sin(th), np.cos(th)


def along_blur(f, dr, dc, sigma_px, h=1.5):
    """Diffuse f along the direction field: each pass averages f with f at +-h along it (variance h^2/2 per pass)."""
    if sigma_px <= 0:
        return f
    K = max(1, int(round(sigma_px ** 2 / (0.5 * h * h))))
    H, W = f.shape
    I, J = np.mgrid[0:H, 0:W].astype(np.float32)
    cp = [I + h * dr, J + h * dc]
    cm = [I - h * dr, J - h * dc]
    for _ in range(K):
        f = 0.5 * f + 0.25 * map_coordinates(f, cp, order=1, mode="nearest") + 0.25 * map_coordinates(f, cm, order=1, mode="nearest")
    return f


def field(rng, shape, inside, dr, dc, across_mm, along_mm, texel):
    f = rng.standard_normal(shape).astype(np.float32)
    f = gaussian_filter(f, across_mm / texel)
    f = along_blur(f, dr, dc, along_mm / texel, h=max(1.0, min(3.0, along_mm / texel / 4)))
    f = f - f[inside].mean()
    return f / f[inside].std()


def sr_full(sr, shape):
    a = zoom(sr, (shape[0] / sr.shape[0], shape[1] / sr.shape[1]), order=1)
    return a[: shape[0], : shape[1]]


sc_full = sr_full


def ou_along(rng, n, ds, ell, x0=None):
    """A unit Ornstein-Uhlenbeck path of n samples ds apart, 1/e correlation length ell (from x0 if given)."""
    rho = math.exp(-ds / ell) if ell > 0 else 0.0
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = rng.standard_normal() if x0 is None else x0
    q = math.sqrt(1 - rho * rho)
    for k in range(1, n):
        x[k] = rho * x[k - 1] + q * e[k]
    return x


def vein_strength(rng, veins, p, ds=0.03):
    """(S8 r2) Each vein's strength along its own length: log g = s_fast * x_fast(s) + s_slow * x_slow(s) - var/2,
    two Ornstein-Uhlenbeck paths in the arc length s, a fork's two daughters starting from their parent's last value
    (no jump at a fork). The fast one is the photo's along-vein wander, the slow one the difference between veins.
    Returns per vein (arc positions, g)."""
    sf, lf = p["vein_sigma_ln"], p["vein_corr_mm"]
    ss, ls = p["vein_slow_sigma_ln"], p["vein_slow_corr_mm"]
    out = []
    ends = []
    for V in veins:
        P = np.asarray(V["pts"], float)
        arc = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        n = max(2, int(arc[-1] / ds) + 2)
        par = V["parent"]
        xf0, xs0 = (ends[par] if par >= 0 else (None, None))
        xf = ou_along(rng, n, ds, lf, xf0)
        xs = ou_along(rng, n, ds, ls, xs0)
        ends.append((xf[-1], xs[-1]))
        lg = sf * xf + ss * xs - 0.5 * (sf * sf + ss * ss)
        out.append((np.arange(n) * ds, np.exp(lg), arc))
    return out


def rasterize_strength(F, veins, gs, p, sub=3):
    """The vein map with each vein's strength: width w * g^beta_w (the column's elliptic profile kept), its share of the
    thickness times g^beta_a, clipped to [0, 1]; the max over the veins (as leaf.rasterize_veins)."""
    bw, ba = p["vein_width_exp"], p["vein_amount_exp"]
    H, W, t = F.H, F.W, F.t
    out = np.zeros((H, W), np.float32)
    offs = (np.arange(sub) + 0.5) / sub - 0.5
    for V, (sg, g, arc) in zip(veins, gs):
        P = np.asarray(V["pts"], float)
        hw0 = V["width_mm"] / 2
        gmax = float(g.max())
        for k, (a, b) in enumerate(zip(P[:-1], P[1:])):
            hwm = hw0 * gmax ** bw
            lo = np.minimum(a, b) - hwm - t
            hi = np.maximum(a, b) + hwm + t
            j0 = max(0, int((lo[0] - F.x0) / t)); j1 = min(W, int((hi[0] - F.x0) / t) + 1)
            i0 = max(0, int((F.y1 - hi[1]) / t)); i1 = min(H, int((F.y1 - lo[1]) / t) + 1)
            if j1 <= j0 or i1 <= i0:
                continue
            ys = F.y1 - (np.arange(i0, i1) + 0.5) * t
            xs = F.x0 + (np.arange(j0, j1) + 0.5) * t
            X, Y = np.meshgrid(xs, ys)
            d = b - a
            L2 = max(d @ d, 1e-12)
            acc = np.zeros(X.shape, np.float32)
            for ox in offs:
                for oy in offs:
                    px, py = X + ox * t, Y + oy * t
                    tt = np.clip(((px - a[0]) * d[0] + (py - a[1]) * d[1]) / L2, 0, 1)
                    gg = np.interp(arc[k] + tt * math.sqrt(L2), sg, g)
                    hw = hw0 * gg ** bw
                    dist = np.hypot(px - a[0] - tt * d[0], py - a[1] - tt * d[1])
                    acc += np.sqrt(np.clip(1 - (dist / hw) ** 2, 0, 1)) * gg ** ba
            acc /= sub * sub
            np.maximum(out[i0:i1, j0:j1], np.clip(acc, 0, 1), out=out[i0:i1, j0:j1])
    return out


def stamp_spots(brown, rng, n, ii, jj, D, E, A, p, prefix, F, sr, sc, st, inside, wob, edge_mm, profile, halo=None):
    """Ellipses (long axis along the veins) added to brown: 'flat' a flat top with a tanh edge edge_mm wide and a
    ragged outline (wob), 'gauss' a Gaussian bump (sigma = the semi-axes / 1.18, so the half-maximum is the ellipse).
    edge_mm may be one value or one per spot (S8 r3). halo (S8 r3): per spot 0 or the halo's Cbrown, a Gaussian
    'halo_scale' times the spot's semi-axes."""
    H, W = brown.shape
    edges = np.broadcast_to(np.asarray(edge_mm, float) / F.t, (n,))
    hs = p.get(prefix + "halo_scale", 2.5)
    for k in range(n):
        edge = float(edges[k])
        i0, j0 = int(ii[k]), int(jj[k])
        if not (0 <= i0 < H and 0 <= j0 < W) or not inside[i0, j0]:
            continue
        a_ = D[k] / 2 * math.sqrt(E[k]) / F.t
        b_ = D[k] / 2 / math.sqrt(E[k]) / F.t
        edge = min(edge, 0.6 * b_ + 0.3)       # (S8 r3) an edge wider than the spot made a flat rectangle the size of
        #                                        the stamp's window (the log-normal edge's tail)
        hk = 0.0 if halo is None else float(halo[k])
        R = int((2.5 * hs if hk > 0 else 2.5) * a_ + 3 * edge) + 2
        r0, r1, c0, c1 = max(0, i0 - R), min(H, i0 + R + 1), max(0, j0 - R), min(W, j0 + R + 1)
        I, J = np.mgrid[r0:r1, c0:c1]
        si, sj = min(i0 // st, sr.shape[0] - 1), min(j0 // st, sr.shape[1] - 1)
        ur, uc = sr[si, sj], sc[si, sj]
        u = (I - ii[k]) * ur + (J - jj[k]) * uc
        v = -(I - ii[k]) * uc + (J - jj[k]) * ur
        rr = np.sqrt((u / a_) ** 2 + (v / b_) ** 2)
        if profile == "flat":
            rr = rr / np.maximum(1 + p[prefix + "rough"] * wob[r0:r1, c0:c1], 0.2)
            prof = 0.5 * (1 - np.tanh((rr - 1) * b_ / max(edge, 0.3)))
        else:
            prof = np.exp(-0.5 * (rr * 1.177) ** 2)
        if hk > 0:
            r0_ = np.sqrt((u / a_) ** 2 + (v / b_) ** 2) / hs
            prof = np.maximum(prof, (hk / max(A[k], 1e-6)) * np.exp(-0.5 * (r0_ * 1.177) ** 2))
        brown[r0:r1, c0:c1] += A[k] * prof


def build(which, objdir, outdir, seed=None, m=None):
    if m is None:
        m = json.load(open(os.path.join(HERE, "material.json")))
    p = params(m, which)
    vj = json.load(open(os.path.join(objdir, "veins.json")))
    c = read_exr1(os.path.join(objdir, "veins.exr"))
    F = Frame(vj["uv_box_mm"], c.shape)
    seed = p["seed"] if seed is None else seed
    rng = np.random.default_rng(seed)
    cfg = json.load(open(os.path.join(ROOT, "objects/yinxing", vj["config"] + ".json")))
    o = cfg["outline"]
    if "from" in o:
        o = json.load(open(os.path.join(ROOT, "objects/yinxing", o["from"])))["outline"]
    if "polygon_mm" not in o:
        raise SystemExit("senescence: only traced outlines (polygon_mm) for now")
    poly = np.asarray(o["polygon_mm"], float)
    i, j = F.ij(poly[:, 0], poly[:, 1])
    inside = np.zeros(c.shape, np.uint8)
    cv2.fillPoly(inside, [np.round(np.stack([j, i], 1) * 8).astype(np.int32)], 1, shift=3)
    inside = inside.astype(bool)
    d = distance_transform_edt(inside) * F.t
    st = 4
    sr, sc = direction_field(vj["veins"], F, st)
    half = 2
    hs = (math.ceil(c.shape[0] / half), math.ceil(c.shape[1] / half))
    up = lambda a, k: zoom(a, (c.shape[0] / a.shape[0], c.shape[1] / a.shape[1]), order=1)[: c.shape[0], : c.shape[1]]
    hr, hc = zoom(sr, (hs[0] / sr.shape[0], hs[1] / sr.shape[1]), order=1), zoom(sc, (hs[0] / sc.shape[0], hs[1] / sc.shape[1]), order=1)
    nrm = np.hypot(hr, hc) + 1e-9
    hr, hc = hr / nrm, hc / nrm
    ins_h = zoom(inside.astype(np.float32), (hs[0] / c.shape[0], hs[1] / c.shape[1]), order=0) > 0.5
    th = F.t * half
    brown = np.zeros(c.shape, np.float32)
    info = {"set": which, "seed": int(seed), "texel_mm": F.t}
    rs = {k: np.random.default_rng([seed, k]) for k in range(9)}   # one stream per part: changing one part's
    #                                                                  parameters leaves the others' draws alone
    # streaks
    if p["streak_Cb0"] > 0:
        n = field(rs[0], hs, ins_h, hr, hc, p["streak_across_mm"], p["streak_along_mm"], th)
        brown += up(p["streak_Cb0"] * np.maximum(n - p["streak_threshold"], 0), half)
    # a broad drift (S8 r2): an isotropic log-normal field drift_mm wide, the leaf's zones browning unevenly
    if p["drift_Cb0"] > 0:
        q = 4
        qs = (math.ceil(c.shape[0] / q), math.ceil(c.shape[1] / q))
        nd = gaussian_filter(rs[7].standard_normal(qs), p["drift_mm"] / (F.t * q))
        nd /= nd.std()
        brown += p["drift_Cb0"] * up(np.maximum(nd - p["drift_threshold"], 0), q)
    # the margin: A exp(-d / l), A itself log-normal along the margin (an isotropic field 'margin_arc_mm' wide), times
    # the tongues along the veins
    q = 4
    qs = (math.ceil(c.shape[0] / q), math.ceil(c.shape[1] / q))
    na = gaussian_filter(rs[2].standard_normal(qs), p["margin_arc_mm"] / (F.t * q))
    na /= na.std()
    if p["margin_A"] > 0:
        n = field(rs[1], hs, ins_h, hr, hc, p["margin_across_mm"], p["margin_along_mm"], th)
        s = p["margin_sigma_ln"]
        tong = up(np.exp(s * n - s * s / 2), half)
        sa = p["margin_arc_sigma_ln"]
        # (S8 r3) where the veins run along the margin (the lateral margins, fed only by the edge vein) it browns
        # more than where they end on it (the distal margin, every vein ending there) [I]: log A + b (w - median),
        # w = 1 - |n . v|, n the margin's normal, v the vein direction (the photo: lateral sectors dlogG -2.7 / -3.4,
        # distal -1.3 [M])
        gy_, gx_ = np.gradient(gaussian_filter(d, 1.0 / F.t))
        nn_ = np.hypot(gy_, gx_) + 1e-9
        vr, vc = sr_full(sr, c.shape), sc_full(sc, c.shape)
        wl = 1 - np.abs((gy_ * vr + gx_ * vc) / nn_)
        band_ = inside & (d < 1.5)
        wls = gaussian_filter(np.where(band_, wl, 0), 1.5 / F.t) / np.maximum(gaussian_filter(band_.astype(float), 1.5 / F.t), 1e-3)
        lat = p["margin_lateral_boost"] * (wls - np.median(wls[band_]))
        Aloc = p["margin_A"] * up(np.exp(sa * na), q) * np.exp(lat)    # margin_A is the median along the margin
        brown += Aloc * np.exp(-d / p["margin_l_mm"]) * tong
    # (S8 r3) the dried rim: a thin dark crust along the very edge, its strength varying along the margin like A
    if p["crust_Cb"] > 0:
        brown += p["crust_Cb"] * up(np.exp(0.5 * p["margin_arc_sigma_ln"] * na), q) * np.exp(-d / p["crust_mm"])
    # (S8 r3) the fine fibrous mottle between the spots: Cb0 * max(0, n), n a field narrower than the vein spacing
    # across and a few tenths of a mm along the veins (on the full grid: it is finer than the half grid's texel)
    if p["fibre_Cb0"] > 0:
        nf = field(rs[8], c.shape, inside, sr_full(sr, c.shape), sc_full(sc, c.shape), p["fibre_across_mm"],
                   p["fibre_along_mm"], F.t)
        brown += p["fibre_Cb0"] * np.maximum(nf, 0)
    area_cm2 = inside.sum() * F.t ** 2 / 100
    # dark necrotic specks: a Thomas cluster process (parents per cm2, a Poisson number of specks round each,
    # Gaussian offsets 'speck_cluster_mm' along the veins and a third of it across), flat with a sharp ragged edge
    wob = gaussian_filter(rs[3].standard_normal(c.shape).astype(np.float32), p["speck_rough_mm"] / F.t)
    wob /= wob.std()
    r_ = rs[4]
    # (S8 r3) more specks near the margin: an inhomogeneous Poisson process of parents, density
    # parents * (1 + K exp(-d / l)), drawn by thinning one of density parents * (1 + K)
    K_, lK = p["speck_margin_boost"], p["speck_margin_l_mm"]
    npar = r_.poisson(p["speck_parents_per_cm2"] * (1 + K_) * area_cm2)
    pi_, pj_ = r_.uniform(0, c.shape[0], npar), r_.uniform(0, c.shape[1], npar)
    dpar = d[np.clip(pi_.astype(int), 0, c.shape[0] - 1), np.clip(pj_.astype(int), 0, c.shape[1] - 1)]
    keep_ = r_.uniform(0, 1, npar) < (1 + K_ * np.exp(-dpar / max(lK, 1e-6))) / (1 + K_)
    pi_, pj_ = pi_[keep_], pj_[keep_]
    npar = len(pi_)
    kids = r_.poisson(p["speck_per_parent"], npar)
    ii, jj = [], []
    for k in range(npar):
        si, sj = min(int(pi_[k]) // st, sr.shape[0] - 1), min(int(pj_[k]) // st, sr.shape[1] - 1)
        ur, uc = sr[si, sj], sc[si, sj]
        a1 = r_.standard_normal(kids[k]) * p["speck_cluster_mm"] / F.t
        a2 = r_.standard_normal(kids[k]) * p["speck_cluster_mm"] / 3 / F.t
        ii += list(pi_[k] + a1 * ur - a2 * uc)
        jj += list(pj_[k] + a1 * uc + a2 * ur)
    nsk = len(ii)
    D = p["speck_diameter_mm"] * np.exp(p["speck_diameter_sigma_ln"] * r_.standard_normal(nsk))
    E = np.maximum(p["speck_elongation"] * np.exp(p["speck_elongation_sigma_ln"] * r_.standard_normal(nsk)), 1.0)
    A = np.clip(p["speck_Cb"] * np.exp(p["speck_Cb_sigma_ln"] * r_.standard_normal(nsk)), *p["speck_Cb_range"])
    ii, jj = np.array(ii), np.array(jj)
    # (S8 r3) near the margin the lesions are bigger, rounder and darker (the photo's lobes, by eye [A])
    dsk = d[np.clip(ii.astype(int), 0, c.shape[0] - 1), np.clip(jj.astype(int), 0, c.shape[1] - 1)]
    wm = np.exp(-dsk / max(p["speck_margin_size_l_mm"], 1e-6))
    D = D * (1 + p["speck_margin_size_boost"] * wm)
    E = 1 + (E - 1) * (1 - wm)
    A = np.clip(A * (1 + p["speck_margin_size_boost"] * wm), *p["speck_Cb_range"])
    # (S8 r3) each speck its own edge width (log-normal): a few sharp pin-points, most soft-edged; some with a halo
    ew = p["speck_edge_mm"] * np.exp(p["speck_edge_sigma_ln"] * r_.standard_normal(nsk))
    halo = np.where(r_.uniform(0, 1, nsk) < p["speck_halo_share"], p["speck_halo_Cb"], 0.0)
    stamp_spots(brown, r_, nsk, ii, jj, D, E, A, p, "speck_", F, sr, sc, st, inside, wob, ew, "flat", halo)
    # diffuse patches: Poisson, Gaussian bumps, shallow
    r_ = rs[5]
    npt = r_.poisson(p["patch_per_cm2"] * area_cm2)
    D = p["patch_diameter_mm"] * np.exp(p["patch_diameter_sigma_ln"] * r_.standard_normal(npt))
    E = np.maximum(p["patch_elongation"] * np.exp(0.3 * r_.standard_normal(npt)), 1.0)
    A = p["patch_Cb"] * np.exp(p["patch_Cb_sigma_ln"] * r_.standard_normal(npt))
    stamp_spots(brown, r_, npt, r_.uniform(0, c.shape[0], npt), r_.uniform(0, c.shape[1], npt), D, E, A, p, "patch_",
                F, sr, sc, st, inside, wob, 0.0, "gauss")
    brown = np.clip(brown, 0, p["Cb_max"]) * inside
    # veins' strength, along each vein (S8 r2: no longer a 2-D field, which made the veins wander sideways)
    if p["vein_sigma_ln"] > 0 or p["vein_slow_sigma_ln"] > 0:
        gs = vein_strength(rs[6], vj["veins"], p)
        amt = rasterize_strength(F, vj["veins"], gs, p, sub=3) * inside
    else:
        amt = c * inside
    os.makedirs(outdir, exist_ok=True)
    write_exr(os.path.join(outdir, "brown.exr"), brown)
    # the vein column browns less than the mesophyll round it (S8 r2: the photo's veins stay light through the brown
    # margin and the specks): its own brown map, the lamina's times vein_brown_factor
    write_exr(os.path.join(outdir, "brown_vein.exr"), brown * p["vein_brown_factor"])
    write_exr(os.path.join(outdir, "veinamt.exr"), amt)
    info.update({"specks": int(nsk), "speck_parents": int(npar), "patches": int(npt),
                 "brown_median_blade": round(float(np.median(brown[inside])), 4),
                 "brown_p90_blade": round(float(np.percentile(brown[inside], 90)), 4),
                 "vein_amt_mean_over_c_mean": round(float(amt[inside].mean() / max(c[inside].mean(), 1e-9)), 4),
                 "params": p})
    json.dump(info, open(os.path.join(outdir, "senescence.json"), "w"), indent=1)
    prev = np.clip(1 - brown / 3, 0, 1) * (0.6 + 0.4 * amt)
    cv2.imwrite(os.path.join(outdir, "senescence_preview.png"),
                cv2.resize((np.where(inside, prev, 0.2) * 255).astype(np.uint8), (c.shape[1] // 3, c.shape[0] // 3), interpolation=cv2.INTER_AREA))
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set")
    ap.add_argument("objdir")
    ap.add_argument("outdir")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    print(json.dumps(build(a.set, a.objdir, a.outdir, a.seed), indent=1))


if __name__ == "__main__":
    main()
