"""Measurements off the card's photograph (Ivar Leidus, 'Lychee fruits and seed', Commons, CC BY-SA 4.0; the file is
ref/lychee/leidus_lychee_fruits_and_seed.jpg, not in git), the numbers objects/lychee/leidus.json and the card use.

    python3 -I materials/lychee/measure_ref.py      # -> out/lychee/ref_measure.json, out/lychee/ref_regions.png

- The pieces: the ground is exactly neutral grey (retouched, GIMP in the EXIF), so the objects are every pixel with
  any saturation (max - min > 0.03 of full scale), opened and hole-filled.
- The fruit's limb: the mask's boundary where the left fruit meets the ground; an ellipse fitted (soft-L1), the
  radial residual binned by angle (outermost point per 0.1 degree), the longest run of bins, detrended by a 301-bin
  median; peaks at least 40 bins apart with prominence >= 8 px. Lengths over the fruit's mean diameter (2 sqrt(ab)),
  so no scale is needed.
- Colours: mean linear sRGB (the JPEG's encoding decoded) in rectangles on each piece, lit faces away from
  highlights; ratios between pieces only (the light's level is unknown).
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy import signal
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PHOTO = os.path.join(ROOT, "ref/lychee/leidus_lychee_fruits_and_seed.jpg")
OUT = os.path.join(ROOT, "out/lychee")

# rectangles (x0, y0, x1, y1) at full size, 6000 x 4000, chosen on the 1500 px preview x 4
REGIONS = {
    "skin": (1300, 1400, 2300, 2000),          # the whole fruit's face, middle
    "aril": (3500, 1400, 4300, 1900),          # the peeled aril's lit upper middle
    "seed": (2700, 2750, 3400, 2950),          # the seed's body below its highlight
}


def srgb_to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def limb(mask):
    bd = mask & ~ndi.binary_erosion(mask)
    ys, xs = np.nonzero(bd)
    sel = (xs < 2800) & ((ys < 2450) | (xs < 1500)) & (ys > 820)       # the left fruit against the ground
    x, y = xs[sel].astype(float), ys[sel].astype(float)

    def res(p):
        cx, cy, a, b, t = p
        c, s = np.cos(t), np.sin(t)
        u = ((x - cx) * c + (y - cy) * s) / a
        v = (-(x - cx) * s + (y - cy) * c) / b
        return (np.hypot(u, v) - 1) * np.sqrt(a * b)

    p = least_squares(res, [1700, 1950, 1300, 1100, 0.0], loss="soft_l1", f_scale=20).x
    cx, cy, a, b, t = p
    ang = np.arctan2(y - cy, x - cx)
    r = res(p)
    nb = 3600
    idx = np.clip(((ang + np.pi) / (2 * np.pi) * nb).astype(int), 0, nb - 1)
    rr = np.full(nb, np.nan)
    np.fmax.at(rr, idx, r)
    ok = ~np.isnan(rr)
    runs = [q for q in np.split(np.arange(nb), np.where(np.diff(ok.astype(int)) != 0)[0] + 1) if ok[q[0]]]
    run = max(runs, key=len)
    prof = rr[run]
    D = 2 * np.sqrt(a * b)
    d = prof - ndi.median_filter(prof, size=301, mode="nearest")
    pk, _ = signal.find_peaks(d, distance=40, prominence=8)
    prom = signal.peak_prominences(d, pk)[0]
    s = np.arange(len(prof)) * (2 * np.pi / nb) * D / 2
    return {"ellipse_px": {"centre": [cx, cy], "axes": [2 * a, 2 * b], "tilt_rad": t},
            "aspect": float(max(a, b) / min(a, b)), "mean_diameter_px": float(D),
            "arc_deg": float(len(run) * 360 / nb), "peaks": int(len(pk)),
            "peak_spacing_along_limb_over_D": float(np.median(np.diff(s[pk])) / D),
            "prominence_over_D": {"median": float(np.median(prom) / D), "p25": float(np.percentile(prom, 25) / D),
                                  "p75": float(np.percentile(prom, 75) / D), "max": float(prom.max() / D)},
            "note": "the limb shows tubercles of several rows at once, so its peak spacing is below the plate size; "
                    "the plate size (0.096 D) was counted face-on on a 100 px grid (objects/lychee/leidus.json)"}


def main():
    im = np.asarray(Image.open(PHOTO)).astype(float) / 255
    sat = im.max(2) - im.min(2)
    mask = ndi.binary_fill_holes(ndi.binary_closing(ndi.binary_opening(sat > 0.03, iterations=4), iterations=6))
    lab, n = ndi.label(mask)
    big = np.argmax(ndi.sum(mask, lab, range(1, n + 1))) + 1
    out = {"photo": "ref/lychee/leidus_lychee_fruits_and_seed.jpg", "size": [im.shape[1], im.shape[0]],
           "limb": limb(lab == big)}
    lin = srgb_to_linear(im)
    cols = {}
    for k, (x0, y0, x1, y1) in REGIONS.items():
        m = lin[y0:y1, x0:x1].reshape(-1, 3).mean(0)
        cols[k] = {"linear_srgb": m.round(4).tolist(), "chromaticity": (m / m.sum()).round(4).tolist(),
                   "rect": [x0, y0, x1, y1]}
    for k in ("skin", "seed"):
        cols[k]["over_aril"] = (np.array(cols[k]["linear_srgb"]) / np.array(cols["aril"]["linear_srgb"])).round(4).tolist()
    out["colours"] = cols
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "ref_measure.json"), "w"), indent=1)
    from PIL import ImageDraw
    pv = Image.open(PHOTO).resize((1500, 1000))
    d = ImageDraw.Draw(pv)
    for k, (x0, y0, x1, y1) in REGIONS.items():
        d.rectangle([x0 / 4, y0 / 4, x1 / 4, y1 / 4], outline=(0, 255, 255), width=2)
        d.text((x0 / 4 + 4, y0 / 4 + 4), k, fill=(0, 255, 255))
    pv.save(os.path.join(OUT, "ref_regions.png"))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
