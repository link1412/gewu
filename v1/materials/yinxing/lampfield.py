"""The lamp behind Fargoh's leaf, measured off the photo: how its brightness varies over the frame, and its white
with the clipped red put back. (S8 round 2.)

    python3 -I materials/yinxing/lampfield.py [--out out/s8/yinxing/r2/lampfield.json]

- The shade is seen around the leaf (blue > 200 of 255 in the JPEG: 47 % of the frame). Its green (sRGB decoded,
  linear) is fitted with a smooth surface, exp of a 2-D polynomial of degree DEG in the frame's coordinates, on the
  shade pixels more than 1.25 mm (20 px) from the leaf (the leaf's glow and the JPEG's ringing stay out) with green
  under 250 (not clipped) [M -> D]. Under the leaf the surface is an extrapolation [A]. The photo cannot tell a lamp
  that is brighter in the middle from a lens that vignettes: both scale the leaf and the shade together, so the
  card puts the whole gradient in the lamp [A].
- The red is clipped (254-255) on 53 % of the shade's pixels, so the median white compare.py takes is too low in red
  and the leaf's red over white too high [M]. It cannot be put back from the shade's unclipped pixels: they are the
  near-neutral bottom right (R/G 1.00, B/G 0.98 there, against the median white's B/G 0.77), the shade's colour is
  not uniform [M]. So it is only reported.
- gain(x, y): the lamp's green over the median of the shade pixels (compare.py's white), on the photo's pixel grid;
  'scales' a coarse grid of it for card.py's lamp patches.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, distance_transform_edt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PHOTO = os.path.join(ROOT, "ref/yinxing/commons/Ginkgo_biloba_yellow_leaf_on_a_lamp.jpg")
DEG = 4
GAP_PX = 20


def srgb_decode(v):
    v = np.asarray(v, float) / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def basis(x, y):
    return np.stack([x ** i * y ** j for i in range(DEG + 1) for j in range(DEG + 1 - i)], -1)


def fit():
    im = np.asarray(Image.open(PHOTO).convert("RGB")).astype(float)
    H, W = im.shape[:2]
    lin = srgb_decode(im)
    bg = im[..., 2] > 200
    leaf = ~bg
    far = distance_transform_edt(~binary_dilation(leaf, iterations=2)) > GAP_PX
    use = bg & far & (im[..., 1] < 250)
    Y, X = np.mgrid[0:H, 0:W]
    xn, yn = (X - W / 2) / (W / 2), (Y - H / 2) / (H / 2)
    A = basis(xn[use], yn[use])
    coef, *_ = np.linalg.lstsq(A, np.log(lin[..., 1][use]), rcond=None)
    G = np.exp(basis(xn, yn) @ coef)
    resid = np.log(lin[..., 1][use]) - np.log(G[use])
    white_med = np.median(lin[bg], 0)                       # compare.photo_linear's white
    gain = G / white_med[1]
    return {"H": H, "W": W, "coef": coef.tolist(), "deg": DEG, "gain": gain, "G": G,
            "fit_pixels": int(use.sum()), "fit_rms_log": float(np.sqrt(np.mean(resid ** 2))),
            "white_median_lin": white_med.tolist(),
            "red_clipped_share_of_shade": float((im[..., 0][bg] >= 254).mean()), "leaf": leaf}


def summary(f, px_per_mm, O_px):
    gain, leaf = f["gain"], f["leaf"]
    return {k: (round(v, 5) if isinstance(v, float) else v) for k, v in {
        "what": "the lamp's green relative to the shade's median (compare.py's white), fitted on the shade around the leaf",
        "fit_pixels": f["fit_pixels"], "fit_rms_log": f["fit_rms_log"], "deg": f["deg"], "coef": f["coef"],
        "gain_shade_p5_p50_p95": [round(float(x), 4) for x in np.percentile(gain[~leaf], [5, 50, 95])],
        "gain_under_leaf_p5_p50_p95": [round(float(x), 4) for x in np.percentile(gain[leaf], [5, 50, 95])],
        "white_median_lin": [round(x, 4) for x in f["white_median_lin"]],
        "red_clipped_share_of_shade": f["red_clipped_share_of_shade"],
        "px_per_mm": px_per_mm, "O_px": O_px, "size_px": [f["W"], f["H"]]}.items()}


def gain_at_mm(f_or_json, x_mm, y_mm):
    """The gain at leaf-plane mm (x right, y up from the petiole's base O) from the fitted polynomial."""
    j = f_or_json
    S, (ox, oy), (W, H) = j["px_per_mm"], j["O_px"], j["size_px"]
    px, py = ox + np.asarray(x_mm) * S, oy - np.asarray(y_mm) * S
    xn, yn = (px - W / 2) / (W / 2), (py - H / 2) / (H / 2)
    xn, yn = np.clip(xn, -1.05, 1.05), np.clip(yn, -1.05, 1.05)      # no extrapolation past the frame
    G = np.exp(basis(xn, yn) @ np.asarray(j["coef"]))
    return G / j["white_median_lin"][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out/s8/yinxing/r2/lampfield.json"))
    a = ap.parse_args()
    o = json.load(open(os.path.join(ROOT, "objects/yinxing/lamp_outline.json")))["outline"]
    f = fit()
    s = summary(f, o["px_per_mm"], o["photo_frame"]["O_px"])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(s, open(a.out, "w"), indent=1)
    g = f["gain"]
    Image.fromarray((np.clip(g / 1.3, 0, 1) * 255).astype(np.uint8)).save(a.out.replace(".json", ".png"))
    print(json.dumps({k: v for k, v in s.items() if k != "coef"}, indent=1))


if __name__ == "__main__":
    main()
