"""胭脂红 card, S8 r2: the review sheet and the judges' blind pair (docs/materials/yanzhi.md, round 3).

    python3 -I materials/yanzhi/lightfit/present2.py OUTDIR --tile LABEL|DIR[:RAW]|NOTE ... [--extra LINE ...]

The first tile is always the photo; each --tile is a render (its card_measure*.json in DIR gives the numbers; RAW
x.dn.exr by default). Every tile is cut by present.crop (by the bowl's own outline, the same scale for all, each
over its own white x 0.85, sRGB). Writes OUTDIR/sheet.png and OUTDIR/pair/photo.png + OUTDIR/pair/render.png (the
photo and the first --tile, same crop and pixels, no text) for tools/blind.py.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import card  # noqa: E402
import present  # noqa: E402
from build import font  # noqa: E402

TW = present.TW


def measure_of(d, raw):
    tag = {"x.dn.exr": "", "x.exr": ""}.get(raw, "_" + os.path.splitext(raw)[0])
    for t in ([tag] if tag else []) + ["_r2rule", ""]:
        p = os.path.join(d, f"card_measure{t}.json")
        if os.path.isfile(p):
            return json.load(open(p))
    raise SystemExit(f"{d}: no card_measure json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--tile", action="append", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--tw", type=int, default=TW, help="tile width (S8 r3: the blind pair near the photo's own scale)")
    a = ap.parse_args()
    present.TW = a.tw
    os.makedirs(os.path.join(a.out, "pair"), exist_ok=True)
    tiles = [("照片  Met 1971.180.248(CC0,馆方 JPEG)", present.crop(card.photo_linear(), "photo"), None, "")]
    for spec in a.tile:
        lab_, src, note = (spec.split("|") + [""])[:3]
        d, raw = (src.split(":") + ["x.dn.exr"])[:2]
        tiles.append((lab_, present.crop(card.render_linear(d, raw), d), measure_of(d, raw), note))
    m0 = tiles[1][2]
    P = {r["region"]: r for r in m0["regions"]}
    ph = tiles[0][1].size[1]
    n = len(tiles)
    body_h = 300
    H = 54 + ph + body_h + 28 * len(a.extra) + 10
    canvas = Image.new("RGB", (n * (present.TW + 12) + 12, H), (245, 245, 243))
    dr = ImageDraw.Draw(canvas)
    dr.text((12, 12), a.title, fill=(20, 20, 20), font=font(20))
    f = font(17)
    for i, (lab_, im, m, note) in enumerate(tiles):
        x = 12 + i * (present.TW + 12)
        canvas.paste(im, (x, 54))
        dr.text((x, 54 + ph + 8), lab_, fill=(0, 0, 0), font=font(22))
        y = 54 + ph + 40
        if m is None:
            lines = [f"正面(中间两区)L*a*b*  {P['centre_upper']['photo_lab'][0]:.1f} {P['centre_upper']['photo_lab'][1]:.1f} "
                     f"{P['centre_upper']['photo_lab'][2]:.1f}",
                     f"侧面(左上)L*a*b*  {P['left_upper']['photo_lab'][0]:.1f} {P['left_upper']['photo_lab'][1]:.1f} "
                     f"{P['left_upper']['photo_lab'][2]:.1f}"]
        else:
            R = {r["region"]: r for r in m["regions"]}
            side = [R[k]["dE00"] for k in R if not k.startswith("centre")]
            lines = [f"平均金量 c {m['c']} g/m2",
                     f"正面 ΔE00 {R['centre_upper']['dE00']:.1f} / {R['centre_lower']['dE00']:.1f}(中间两区)",
                     f"两侧 ΔE00 平均 {np.mean(side):.1f}(四区)",
                     f"六区平均 ΔE00 {m['mean_dE00']:.2f}",
                     f"正面 L*a*b*  {R['centre_upper']['render_lab'][0]:.1f} {R['centre_upper']['render_lab'][1]:.1f} "
                     f"{R['centre_upper']['render_lab'][2]:.1f}"]
        lines += [l for l in note.split(";") if l]
        for l in lines:
            dr.text((x, y), l, fill=(30, 30, 30), font=f)
            y += 23
    y = 54 + ph + body_h
    for l in a.extra:
        dr.text((12, y), l, fill=(30, 30, 30), font=f)
        y += 28
    canvas.save(os.path.join(a.out, "sheet.png"))
    tiles[0][1].save(os.path.join(a.out, "pair", "photo.png"))
    tiles[1][1].save(os.path.join(a.out, "pair", "render.png"))
    print("->", os.path.join(a.out, "sheet.png"))


if __name__ == "__main__":
    main()
