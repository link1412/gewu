"""A washer render developed as the CMA photo was: white balance for the key light (a 5500 K blackbody), the colour
matrix of tools/camera.py, sRGB. The exposure is the one camera setting matched to the photo [F]: the median
luminance over the glaze (pixels brighter than the cloth in both images) equals the photo's. The photo's own
processing is otherwise unknown (its XMP: a linear ACR curve, then Photoshop): no other curve here [A].

    python3 -I objects/ru_washer/develop.py RAW.exr --out OUT.png [--photo ref/ru/photos/cma_1957.40.jpg] [--pair P.png]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import Spectra, blackbody, calibrate, read_raw, srgb_encode  # noqa: E402

Y709 = np.array([0.2126, 0.7152, 0.0722])
GLAZE_MIN = 0.08          # linear luminance: the glaze reads 0.15-0.37 in the photo, the cloth 0.02-0.03 [M]


def srgb_decode(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def develop(raw_path, photo_path, sensor="canon_eos_5d_mkiv", K=5500):
    S = Spectra(sensor)
    cal = calibrate(S, blackbody(K))
    lin = np.maximum((read_raw(raw_path) * cal["gains"]) @ cal["C"].T, 0.0)
    h, w, _ = lin.shape
    ph = Image.open(photo_path).convert("RGB").resize((w, h), Image.LANCZOS)
    ph_lin = srgb_decode(np.asarray(ph, float) / 255.0)
    yr, yp = lin @ Y709, ph_lin @ Y709
    k = 1.0
    for _ in range(3):                                   # the mask depends on the exposure: settle it
        m = (yr * k > GLAZE_MIN) & (yp > GLAZE_MIN)
        k = np.median(yp[m]) / np.median(yr[m])
    lin = lin * k
    stats = {"exposure": float(k), "glaze_pixels": int(m.sum()),
             "median_glaze_rgb_render": np.median(lin[m], 0).round(4).tolist(),
             "median_glaze_rgb_photo": np.median(ph_lin[m], 0).round(4).tolist()}
    return lin, ph_lin, stats


def to8(lin):
    return (np.clip(srgb_encode(np.clip(lin, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--out", required=True)
    ap.add_argument("--photo", default=os.path.join(ROOT, "ref/ru/photos/cma_1957.40.jpg"))
    ap.add_argument("--pair", help="also write the photo above the render")
    ap.add_argument("--factor", help="multiply the developed linear RGB by this (marks.py's .npy)")
    a = ap.parse_args()
    lin, ph_lin, stats = develop(a.raw, a.photo)
    if a.factor:
        lin = lin * np.load(a.factor)
    Image.fromarray(to8(lin)).save(a.out)
    if a.pair:
        Image.fromarray(np.concatenate([to8(ph_lin), to8(lin)], 0)).save(a.pair)
    json.dump(stats, open(os.path.splitext(a.out)[0] + ".json", "w"), indent=1)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
