"""The Inaba yohen tenmoku's spots, read off the 1955 top view (ref/yohen/images/inaba_commons_1955_full.jpg).

    python3 -I objects/yohen_inaba/spots.py [--out out/yohen/spots]

The photo is a printed plate (Hayashiya, Chinese Ceramics, 1955; Commons, PD-Japan): its colours were laid on in
print and are not a measurement; what is used is where things are. Classes, per pixel:
  0 ground   the black glaze (with the hare's-fur streaks)
  1 halo     the bluish haze outside the clusters
  2 cluster  inside a cluster, between the cores (the pale ring round each core and the outer rim)
  3 core     a spot's core (brown)
  4 masked   the photo's highlights (bright crescents) and the unglazed outside of the bowl
Features (CIELAB of the plate as sRGB, D65; smoothed). Clusters: everything enclosed by the light band (each core's
pale ring and the cluster's outer rim are lighter, in L* against the surroundings, than anything else). Cores:
brown inside a cluster, i.e. min(a*, b*) high (cores are red and yellow; the ground is reddish only, the ring
yellow only), split by a watershed on the distance transform. Absolute lightness fails (cores are lighter than the
ground but darker than their rings) and so does warmth a* + b* (the print's warm cast lies over the ground too).
Halo: the feathered fringe just outside a cluster, lighter than its surroundings. Highlights: large, very bright
patches. Thresholds are set by eye on this plate [A] and written with the result.

The bowl's mouth is the circle fitted to the edge of the dark disc (robust, so the cast shadow at lower left does
not pull it); positions are given in the photo's pixels and as (r / R_mouth, theta) about that centre, theta from
the photo's +x towards +y (image down). Mapping onto the bowl's inner surface needs the form (not yet: the photo
is not orthographic; the profile and the camera come with the form).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.optimize import least_squares
from skimage.measure import label as sk_label, regionprops
from skimage.morphology import reconstruction
from skimage.segmentation import watershed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402

PHOTO = os.path.join(ROOT, "ref/yohen/images/inaba_commons_1955_full.jpg")

# thresholds [A: by eye on this plate]
BOWL_L = 45.0          # L* below this is the bowl (the backdrop is ~60)
CLUSTER_LR = 4.0       # the light band round the cores: L* this far above its surroundings (sigma 25)
CORE_BROWN = 3.0       # min(a*, b*) (sigma 2) above this: brown (cores ~4-6; ground's b* ~0, the ring's a* ~0)
CLUSTER_CLOSE = 3      # closing of the light band before filling (bridges its small gaps)
GROUND_MIN_PX = 6000   # a dark patch at least this big is open ground, not a core (the largest cores ~3000 px)
BASIN_DEPTH = 3.0      # (b): L* this far below the grey-level hole filling
BASIN_SOLIDITY = 0.85  # (b): area / convex hull area
BASIN_OWN_EDGE = 0.7   # (b): share of a piece's edge that is the basin's edge rather than a cut
BASIN_BIG_PX = 1000    # (b): basins larger than this must be brownish (mean min(a*, b*) > CORE_BROWN / 3)
CORE_MAX_PX = 5000     # (b): larger basins are open ground
RING_LR = 2.5          # (b): the band: L* this far above its surroundings ...
RING_COVER = 0.7       # ... in this share of the 16 sectors round the basin
CORE_SOLIDITY = 0.8    # every final core: area / convex hull area
CORE_RMAX = 0.96       # no cores on the lip (r / R_mouth): blobs there are the lip's own shading
CORE_MIN_PX = 12       # smaller blobs are noise
PEAK_SIZE = 15         # watershed seeds: local maxima of the distance transform in this window
HALO_REACH = 15        # px outside a cluster
HALO_LR = 1.0          # halo: L* still this far above its surroundings
HIGHLIGHT_L = 45.0     # inside the mouth: brighter than this ...
HIGHLIGHT_MIN_PX = 300  # ... over this many pixels: the photo's highlight


DISC2 = np.hypot(*np.mgrid[-2:3, -2:3]) <= 2.0


def lab_of(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    return camera.lab(lin @ M.T, np.array([0.9505, 1.0, 1.089])), a


def fit_mouth(L):
    dark = ndi.binary_fill_holes(ndi.binary_opening(L < BOWL_L, iterations=3))
    lab, n = ndi.label(dark)
    big = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    edge = big & ~ndi.binary_erosion(big)
    y, x = np.nonzero(edge)
    c0 = np.array([x.mean(), y.mean(), np.sqrt(big.sum() / np.pi)])
    res = least_squares(lambda p: np.hypot(x - p[0], y - p[1]) - p[2], c0, loss="soft_l1", f_scale=3.0)
    r = np.abs(np.hypot(x - res.x[0], y - res.x[1]) - res.x[2])
    return res.x, float(np.median(r)), float(np.mean(r < 3))


def segment(lab, mouth):
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    H, W = L.shape
    yy, xx = np.mgrid[:H, :W]
    rr = np.hypot(xx - mouth[0], yy - mouth[1]) / mouth[2]
    inside = rr < 0.985
    g = ndi.gaussian_filter
    Lr = g(L, 1.5) - g(L, 25.0)            # lightness against the surroundings (the print's falloff removed)
    brown = np.minimum(g(A, 2.0), g(B, 2.0))  # cores are red AND yellow; ground is red only, the ring yellow only
    # the photo's highlights: large, very bright, colourless patches
    hl = inside & (g(L, 2.0) > HIGHLIGHT_L)
    lab_hl, n = ndi.label(hl)
    sizes = ndi.sum(hl, lab_hl, range(1, n + 1))
    highlight = np.isin(lab_hl, 1 + np.nonzero(sizes >= HIGHLIGHT_MIN_PX)[0])
    highlight = ndi.binary_dilation(highlight, iterations=4)
    # a cluster: everything enclosed by the light band (pale rings and the outer rim)
    light = inside & ~highlight & (Lr > CLUSTER_LR)
    light = ndi.binary_closing(light, iterations=CLUSTER_CLOSE)
    # what the band encloses: the dark patches not joined to the large open ground once hairline gaps in the band
    # are cut (an opening of the dark side); fill_holes alone leaks through those gaps
    dark = ~light & inside
    dark_cut = ndi.binary_opening(dark, structure=DISC2)
    comp, n = ndi.label(dark_cut)
    sizes = ndi.sum(dark_cut, comp, range(1, n + 1))
    open_ground = np.isin(comp, 1 + np.nonzero(sizes >= GROUND_MIN_PX)[0])
    open_ground = ndi.binary_dilation(open_ground, structure=DISC2) & dark
    cluster = inside & ~highlight & ~open_ground
    # cores, two ways (their union):
    # (a) brown inside a cluster (the band is not brown: its a* or b* is ~0). Dark, unbrown cores (near the well)
    # come from (b); taking 'dark inside a cluster' here also took slivers of ground between faint bands
    core_a = cluster & (brown > CORE_BROWN)
    # (b) a basin of L* ringed by a light band on most sides, wherever the band is too faint to enclose a cluster:
    # depth below the grey-level hole filling; kept if compact and the band (max of L* in 1-7 px, per 22.5 deg
    # sector) is there in most sectors. The hare's-fur streaks are basins too, but long and unringed.
    Lr1 = g(L, 1.0) - g(L, 25.0)
    seed = Lr1.copy()
    seed[1:-1, 1:-1] = Lr1.max()
    depth = reconstruction(seed, Lr1, method="erosion") - Lr1
    basin = ndi.binary_opening(g(depth, 1.0) > BASIN_DEPTH, structure=DISC2) & inside & ~highlight
    # cut basins at their necks (a core whose band is open on one side leaks into the ground beyond)
    bd = ndi.gaussian_filter(ndi.distance_transform_edt(basin), 1.5)
    bmk, _ = ndi.label((bd == ndi.maximum_filter(bd, size=PEAK_SIZE)) & (bd >= 3.0))
    lb = watershed(-bd, bmk, mask=basin)
    rest, _ = ndi.label(basin & (lb == 0))   # basins too thin for a seed keep their own label
    lb[rest > 0] = rest[rest > 0] + lb.max()
    keep = np.zeros(lb.max() + 1, bool)
    for r in regionprops(lb):
        if not (CORE_MIN_PX <= r.area <= CORE_MAX_PX) or r.solidity < BASIN_SOLIDITY:
            continue
        y0, x0, y1, x1 = r.bbox
        ys, xs = slice(max(y0 - 10, 0), min(y1 + 10, H)), slice(max(x0 - 10, 0), min(x1 + 10, W))
        m = lb[ys, xs] == r.label
        # most of its edge must be the basin's own edge, not a watershed cut (chunks of open ground are all cuts)
        edge = m & ~ndi.binary_erosion(m)
        own = (edge & ndi.binary_dilation(~basin[ys, xs])).sum() / max(edge.sum(), 1)
        if own < BASIN_OWN_EDGE:
            continue
        ann = ndi.binary_dilation(m, iterations=7) & ~m
        yy, xx = np.nonzero(ann)
        sec = ((np.arctan2(yy - (r.centroid[0] - ys.start), xx - (r.centroid[1] - xs.start)) + np.pi)
               / (2 * np.pi) * 16).astype(int) % 16
        v = Lr1[ys, xs][ann]
        top = np.array([v[sec == k].max() if (sec == k).any() else -np.inf for k in range(16)])
        # a large basin must be brown: the dark unbrown cores are all small (near the well); the one large dark
        # basin that passed the ring test was ground between streaks on the steep wall
        if r.area > BASIN_BIG_PX and brown[ys, xs][m].mean() < CORE_BROWN / 3:
            continue
        keep[r.label] = (top > RING_LR).mean() >= RING_COVER
    core = (core_a | keep[lb]) & (rr < CORE_RMAX)
    core = ndi.binary_opening(core, structure=DISC2)
    core = ndi.binary_fill_holes(ndi.binary_closing(core, structure=DISC2))
    cluster |= core
    # split touching cores: watershed of the distance transform from its maxima
    dist = ndi.gaussian_filter(ndi.distance_transform_edt(core), 1.5)
    peaks = (dist == ndi.maximum_filter(dist, size=PEAK_SIZE)) & (dist >= 2.0)
    markers, _ = ndi.label(peaks)
    ws = watershed(-dist, markers, mask=core)
    rest, _ = ndi.label(core & (ws == 0))
    ws[rest > 0] = rest[rest > 0] + ws.max()
    # every core is a compact blob of moderate size (drops slivers of ground caught between faint bands)
    ok = np.zeros(ws.max() + 1, bool)
    for r in regionprops(ws):
        ok[r.label] = CORE_MIN_PX <= r.area <= CORE_MAX_PX and r.solidity >= CORE_SOLIDITY
    ws[~ok[ws]] = 0
    core = ws > 0
    # halo: the feathered fringe just outside a cluster, still lighter than the ground around it
    halo = (inside & ~cluster & ~highlight & ndi.binary_dilation(cluster, iterations=HALO_REACH)
            & (g(Lr, 2.0) > HALO_LR))
    halo = ndi.binary_opening(halo, iterations=1)
    cls = np.zeros((H, W), np.uint8)
    cls[halo] = 1
    cls[cluster] = 2
    cls[core] = 3
    cls[highlight | ~inside] = 4
    return cls, ws, rr


def spots_table(ws, mouth, cls):
    out = []
    for i, sl in enumerate(ndi.find_objects(ws), start=1):
        if sl is None:
            continue
        m = ws[sl] == i
        area = int(m.sum())
        if area < CORE_MIN_PX:
            continue
        y, x = np.nonzero(m)
        cx, cy = float(x.mean() + sl[1].start), float(y.mean() + sl[0].start)
        r = float(np.hypot(cx - mouth[0], cy - mouth[1]) / mouth[2])
        th = float(np.degrees(np.arctan2(cy - mouth[1], cx - mouth[0])))
        out.append({"x": round(cx, 1), "y": round(cy, 1), "area_px": area,
                    "r_eq_px": round(float(np.sqrt(area / np.pi)), 2), "r_mouth": round(r, 4),
                    "theta_deg": round(th, 2)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out/yohen/spots"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lab, rgb = lab_of(PHOTO)
    mouth, med, frac = fit_mouth(lab[..., 0])
    cls, ws, rr = segment(lab, mouth)
    spots = spots_table(ws, mouth, cls)
    inside = cls != 4
    share = {n: float((cls == k).sum() / inside.sum()) for k, n in enumerate(["ground", "halo", "cluster", "core"])}
    px_per_mm = mouth[2] / 61.0   # mouth 12.2 cm [M: NPM 2018 p.23 table 1]; the plate is not orthographic, so
    # this scale holds at the mouth only
    res = {"photo": os.path.relpath(PHOTO, ROOT), "mouth_px": [round(v, 2) for v in mouth],
           "mouth_fit_median_px": round(med, 2), "mouth_fit_within_3px": round(frac, 3),
           "px_per_mm_at_mouth": round(px_per_mm, 3),
           "thresholds": {k: globals()[k] for k in ("BOWL_L", "CLUSTER_LR", "CORE_BROWN", "CLUSTER_CLOSE", "GROUND_MIN_PX", "BASIN_DEPTH", "BASIN_SOLIDITY",
                                                     "CORE_MAX_PX", "BASIN_BIG_PX", "BASIN_OWN_EDGE", "RING_LR", "RING_COVER", "CORE_SOLIDITY", "CORE_RMAX", "CORE_MIN_PX", "PEAK_SIZE",
                                                     "HALO_REACH", "HALO_LR", "HIGHLIGHT_L", "HIGHLIGHT_MIN_PX")},
           "area_share_of_unmasked": {k: round(v, 4) for k, v in share.items()},
           "n_cores": len(spots), "cores": spots}
    with open(os.path.join(a.out, "spots.json"), "w") as f:
        json.dump(res, f, indent=1)
    pal = np.array([[20, 20, 20], [60, 110, 230], [120, 220, 160], [200, 120, 60], [128, 128, 128]], np.uint8)
    Image.fromarray(pal[cls]).save(os.path.join(a.out, "classes.png"))
    over = (rgb * 255).astype(np.uint8).copy()
    edge = ws > 0
    edge = edge & ~ndi.binary_erosion(edge)
    over[edge] = [255, 60, 60]
    yy, xx = np.mgrid[:cls.shape[0], :cls.shape[1]]
    ring = np.abs(np.hypot(xx - mouth[0], yy - mouth[1]) - mouth[2]) < 1.5
    over[ring] = [255, 255, 0]
    Image.fromarray(over).save(os.path.join(a.out, "overlay.png"))
    print(f"mouth centre ({mouth[0]:.1f}, {mouth[1]:.1f}) R {mouth[2]:.1f} px; edge residual median {med:.2f} px, "
          f"{frac * 100:.0f}% within 3 px")
    print(f"cores: {len(spots)};  area shares: " + ", ".join(f"{k} {v * 100:.1f}%" for k, v in share.items()))


if __name__ == "__main__":
    main()
