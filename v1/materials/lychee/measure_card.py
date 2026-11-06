"""The card's render measured as measure_ref.py measures the photograph: mean linear BT.709 in a rectangle on each
piece (white balanced, before the tone curve, so ratios are exact), ratios between pieces, set against the photo's.

    python3 -I materials/lychee/measure_card.py [OUT]      # OUT: out/recipes/card-leidus; -> OUT/card_measure.json, regions.png

The rectangles are on the 1920 x 1080 development (lit faces away from highlights, as on the photo), at 960 x 540
render resolution halved.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as C  # noqa: E402

REGIONS = {                                      # (x0, y0, x1, y1) on the 1920 x 1080 development
    "skin": (420, 430, 760, 640),                 # the whole fruit's face, middle
    "aril": (1280, 300, 1560, 460),               # the peeled aril's lit upper middle
    "seed": (950, 965, 1250, 1040),               # the seed's body below its highlight
}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out/recipes/card-leidus")
    cam, sensor = C.settings_camera(os.path.join(out, "camera.json"))
    S = C.Spectra(sensor["pbrt_sensor"])
    cal = C.calibrate(S, C.balance_spectrum(cam))
    raw = C.to_film_size(C.read_raw(os.path.join(out, "x.exr")))[0]
    lin = (raw * cal["gains"]) @ cal["C"].T
    ref = json.load(open(os.path.join(ROOT, "out/lychee/ref_measure.json")))["colours"]
    m = {k: lin[y0:y1, x0:x1].reshape(-1, 3).mean(0) for k, (x0, y0, x1, y1) in REGIONS.items()}
    res = {}
    for k in ("skin", "aril", "seed"):
        p = np.array(ref[k]["linear_srgb"])
        r = {"render": m[k].round(5).tolist(), "chromaticity": (m[k] / m[k].sum()).round(4).tolist(),
             "photo_chromaticity": (p / p.sum()).round(4).tolist()}
        if k != "aril":
            r["over_aril"] = (m[k] / m["aril"]).round(4).tolist()
            r["photo_over_aril"] = ref[k]["over_aril"]
            r["render_over_photo"] = ((m[k] / m["aril"]) / np.array(ref[k]["over_aril"])).round(3).tolist()
        res[k] = r
        print(k, json.dumps(r))
    json.dump({"regions": REGIONS, "colours": res}, open(os.path.join(out, "card_measure.json"), "w"), indent=1)
    from PIL import Image, ImageDraw
    im = Image.open(os.path.join(out, "dev/base.png")).convert("RGB")
    d = ImageDraw.Draw(im)
    for k, (x0, y0, x1, y1) in REGIONS.items():
        d.rectangle([x0, y0, x1, y1], outline=(0, 255, 255), width=3)
        d.text((x0 + 6, y0 + 6), k, fill=(0, 255, 255))
    im.resize((960, 540)).save(os.path.join(out, "regions.png"))


if __name__ == "__main__":
    main()
