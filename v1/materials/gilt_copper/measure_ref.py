"""Measure the reference photo of the gilt-copper card: Cleveland Museum of Art 1970.149.1, seated Buddha, Ming,
16th c., gilt bronze, H 99 mm (CC0; ref/metals/cleveland/SOURCES.txt). Writes
out/materials/gilt_copper/measured_cma1970.149.1.json.

    python3 -I materials/gilt_copper/measure_ref.py [--photo ref/metals/cleveland/1970.149.1_full.tif]

The photo carries an sRGB IEC61966-2.1 profile [M]; it is decoded with the sRGB curve, assumed to be the photo's
only tone curve [A]. Regions (full-resolution pixel boxes, picked by eye on the photo; x0 x1 y0 y1):
- floor: the grey paper in front of the base, the white reference (it is neutral in the file: R = G = B to 1e-5);
- knee_r: inside the right knee (6.5 x 5.9 mm: its top highlight and the front below it), a smooth dome, the closest the statue has to the card's dome;
- knee_l: the left knee with some of the robe's edge (colour only);
- band: the plain front band of the base, a vertical wall about 3.5 mm high.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "out/materials/gilt_copper")
HEIGHT_MM = 99.0                  # Cleveland's catalogue: overall height 9.9 cm
REGIONS = {"floor": (2300, 3700, 5750, 6000), "knee_r": (3640, 3880, 4200, 4420),
           "knee_l": (2100, 2600, 4150, 4560), "band": (2400, 3400, 5360, 5480)}
LUMA = np.array([0.2126, 0.7152, 0.0722])


def srgb_lin(im):
    x = im.astype(np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def crop(a, r):
    x0, x1, y0, y1 = r
    return a[y0:y1, x0:x1]


def object_height_px(im):
    """rows spanned by the statue: the largest connected region of saturated, not-dark pixels"""
    f = im.astype(np.float32) / 255
    mx, mn = f.max(2), f.min(2)
    m = ndi.binary_opening(((mx - mn) / np.maximum(mx, 1e-3) > 0.25) & (mx > 0.08), iterations=3)
    lab, n = ndi.label(m)
    big = lab == (np.argmax(ndi.sum(m, lab, range(1, n + 1))) + 1)
    rows, cols = np.where(big.any(1))[0], np.where(big.any(0))[0]
    return int(rows[-1] - rows[0] + 1), [int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])]


def colour_bands(p):
    """white-balanced linear RGB (relative to the floor) of a region, by luma percentile band"""
    p = p.reshape(-1, 3)
    Y = p @ LUMA
    out = {}
    for lo, hi in ((5, 50), (50, 90), (90, 99)):
        m = (Y >= np.percentile(Y, lo)) & (Y <= np.percentile(Y, hi))
        q = p[m].mean(0)
        out[f"p{lo}_{hi}"] = {"rgb_over_floor": q.round(4).tolist(), "R_over_G": round(float(q[0] / q[1]), 3),
                              "B_over_G": round(float(q[2] / q[1]), 3), "luma_over_floor": round(float(Y[m].mean()), 4)}
    out["luma_over_floor_p5_p50_p95"] = np.percentile(Y, [5, 50, 95]).round(4).tolist()
    return out


def dark_spots(p, px_mm, thresh=0.5):
    """spots darker than `thresh` x the local median luma (a 1 mm median): their density, sizes, area fraction"""
    Y = p @ LUMA
    med = ndi.median_filter(Y, size=int(round(px_mm)) | 1)
    m = ndi.binary_opening(Y < thresh * med)                       # drop single-pixel noise
    lab, n = ndi.label(m)
    area = ndi.sum(m, lab, range(1, n + 1)) / px_mm ** 2           # mm^2
    d = 2 * np.sqrt(area / np.pi)
    A = Y.size / px_mm ** 2
    rgb = (p[m].mean(0) / np.maximum(p[~m].mean(0), 1e-6)).round(3).tolist() if n else None
    return {"threshold_of_local_median": thresh, "count": int(n), "per_mm2": round(n / A, 3),
            "spot_rgb_over_surroundings": rgb, "spot_luma_over_local_median_mean": round(float((Y / med)[m].mean()), 3) if n else None,
            "area_fraction": round(float(m.mean()), 4),
            "diameter_mm_p10_p50_p90": np.percentile(d, [10, 50, 90]).round(3).tolist() if n else None,
            "region_mm2": round(A, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default=os.path.join(ROOT, "ref/metals/cleveland/1970.149.1_full.tif"))
    a = ap.parse_args()
    Image.MAX_IMAGE_PIXELS = None
    im = np.asarray(Image.open(a.photo).convert("RGB"))
    h, bbox = object_height_px(im)
    px_mm = h / HEIGHT_MM
    lin = srgb_lin(im)
    floor = crop(lin, REGIONS["floor"]).reshape(-1, 3).mean(0)
    res = {"photo": os.path.relpath(a.photo, ROOT), "regions_x0_x1_y0_y1": REGIONS,
           "scale": {"object_rows_cols": bbox, "height_px": h, "height_mm": HEIGHT_MM, "px_per_mm": round(px_mm, 2),
                     "tag": "D", "note": "projected height over catalogue height; the camera looks slightly down, so "
                     "the base's depth adds a little: an estimate to a few percent"},
           "floor_linear": floor.round(4).tolist(),
           "floor_srgb8": crop(im, REGIONS["floor"]).reshape(-1, 3).mean(0).round(1).tolist()}
    for k in ("knee_r", "knee_l", "band"):
        p = crop(lin, REGIONS[k]) / floor
        res[k] = {"colour": colour_bands(p), "dark_spots": dark_spots(p, px_mm)}
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "measured_cma1970.149.1.json")
    json.dump(res, open(path, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
