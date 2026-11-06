"""胭脂红 card, S8 r3: the render through the photo's camera and delivery (camera layer, not image editing).

The judges read the render's lack of sensor grain and its denoised smoothness. The photo went through a camera
sensor and the Met's JPEG; the render gets the same two steps, from data:
  1. sensor noise: the camera chain's model (tools/camera.py develop: Poisson shot noise + Gaussian read noise on
     the photosites behind a pixel, R/G/B split as Bayer), with the Canon EOS 5D Mark IV's measured full well and
     read noise (tools/sensors/) [I]. The Met's camera is not known [A: this one]. Photosites per pixel: the photo is
     2000 px wide [M]; a full-frame 6720-photosite row over 2000 px is 11.3 per pixel [A: no crop], scaled by the
     render's pixel size against the photo's (the bowl's height in pixels). Exposure: the frame's 99th percentile at
     0.75 of saturation (tools/camera.py's material-card default, our choice).
  2. the delivery: 8-bit sRGB, JPEG at the photo's own settings: quantisation tables all 1 (quality 100) and 4:2:0
     chroma (PIL reads both off the Met's file) [M]; the file's ICC profile is sRGB [M].
Out: x.cam.pfm beside the input, in the render's raw space (the development's matrix inverted), so card.py and
present2 read it as any raw.

    python3 -I materials/yanzhi/lightfit/camchain.py DIR [--raw x.dn.exr] [--seed 1]
"""
import argparse
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import card  # noqa: E402
from build import write_pfm  # noqa: E402
from camera import read_raw, srgb_encode, srgb_decode  # noqa: E402

PHOTO_W = 2000                # px [M]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--raw", default="x.dn.exr")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    sensor = json.load(open(os.path.join(ROOT, "tools/sensors/canon_eos_5d_mkiv.json")))
    raw = np.maximum(read_raw(os.path.join(a.dir, a.raw)), 0)
    g, C = card._CAL["gains"], card._CAL["C"]
    # pixel scale: the bowl's height in pixels, photo against render
    _, pi = card.regions(card.photo_linear(), "photo")
    _, ri = card.regions((raw * g) @ C.T, "render")
    k = (pi["red_bot"] - pi["top"]) / (ri["red_bot"] - ri["top"])
    sites = (sensor["photosites"][0] / PHOTO_W) ** 2 * k ** 2
    sat = sensor["saturation_e_at_base_iso"]
    rn = sensor["read_noise_e"]["100"]["e"]
    ref = np.percentile(raw.max(2), 99.0)
    e = np.minimum(raw * (0.75 * sat / ref), sat)
    n = np.array([0.25, 0.5, 0.25]) * sites
    rng = np.random.default_rng(a.seed)
    tot = rng.poisson(e * n) + rng.normal(0.0, rn * np.sqrt(n), e.shape)
    v = tot / n / sat                                    # in units of saturation, as tools/camera.py develop
    v = np.minimum(v * g, g.min())                       # white balance; clipped highlights go white (not magenta)
    lin = np.maximum(v @ C.T, 0.0)
    # to 8-bit sRGB, the white (the inside's far wall) where the photo has it
    box, _ = card.regions(lin, "render")
    pl = card.photo_linear()
    pb, _ = card.regions(pl, "photo")
    s = card.median_box(pl, pb["white"]).mean() / card.median_box(lin, box["white"]).mean()
    v = np.clip(srgb_encode(np.clip(lin * s, 0, 1)), 0, 1)
    buf = io.BytesIO()
    Image.fromarray((v * 255 + 0.5).astype(np.uint8)).save(buf, "JPEG", quality=100, subsampling=2)
    back = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("RGB")).astype(float) / 255
    lin2 = srgb_decode(back) / s
    raw2 = (lin2 @ np.linalg.inv(C.T)) / g
    write_pfm(os.path.join(a.dir, "x.cam.pfm"), raw2)
    info = {"photosites_per_px": float(sites), "photo_over_render_px": float(k), "exposure_ref_raw": float(ref),
            "jpeg": "quality 100, 4:2:0 (the photo's tables all 1) [M]"}
    json.dump(info, open(os.path.join(a.dir, "camchain.json"), "w"), indent=1)
    print(info)


if __name__ == "__main__":
    main()
