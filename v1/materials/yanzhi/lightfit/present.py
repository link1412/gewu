"""胭脂红 card, round 2: the review sheet and the judges' blind pair (docs/materials/yanzhi.md).

    python3 -I materials/yanzhi/lightfit/present.py OUTDIR --r1 DIR1[:RAW] --r2 DIR2[:RAW] [--r1-note ..] [--r2-note ..]

Each tile is cut around the bowl by its own outline (card.regions: from 15% of the bowl's height above the far rim
to 10% below the foot, 1.7 bowl heights wide), so every tile is at the same scale (the bowls are the same size);
each image is linear over its own white (the inside's far wall) x 0.85, sRGB-encoded, as card.py's sheet.
Writes OUTDIR/sheet.png (照片 | 渲染 r1 | 渲染 r2, numbers under each, from card_measure*.json in each render's dir)
and OUTDIR/pair/photo.png, OUTDIR/pair/render.png (the photo and r2, same crop, same pixels, no text) for blind.py.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import card  # noqa: E402
from build import font  # noqa: E402

TW = 640


def crop(lin, name):
    box, info = card.regions(lin, name)
    w = card.median_box(lin, box["white"])
    img = np.clip(lin / w * 0.85, 0, 1)
    img = np.where(img <= 0.0031308, 12.92 * img, 1.055 * img ** (1 / 2.4) - 0.055)
    cx, top, bot = info["cx"], info["top"], info["red_bot"]
    hh = bot - top
    x0, x1 = int(round(cx - 0.85 * hh)), int(round(cx + 0.85 * hh))
    y0, y1 = int(round(top - 0.15 * hh)), int(round(bot + 0.10 * hh))
    pad = max(0, -x0, -y0, x1 - img.shape[1], y1 - img.shape[0])
    if pad:
        img = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        x0, x1, y0, y1 = x0 + pad, x1 + pad, y0 + pad, y1 + pad
    im = Image.fromarray((img[y0:y1, x0:x1] * 255 + 0.5).astype(np.uint8))
    return im.resize((TW, int(round(TW * 1.25 / 1.7))), Image.LANCZOS)


def numbers(d, tag):
    p = os.path.join(d, f"card_measure{tag}.json")
    if not os.path.isfile(p):
        return []
    m = json.load(open(p))
    R = {r["region"]: r for r in m["regions"]}
    cen = [R[k]["dE00"] for k in ("centre_upper", "centre_lower")]
    side = [R[k]["dE00"] for k in R if not k.startswith("centre")]
    return m, cen, side


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--r1", required=True)
    ap.add_argument("--r2", required=True)
    ap.add_argument("--r1-note", default="")
    ap.add_argument("--r2-note", default="")
    ap.add_argument("--extra", nargs="*", default=[], help="lines under the sheet")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "pair"), exist_ok=True)
    tiles = [("照片  Met 1971.180.248(CC0,馆方 JPEG)", crop(card.photo_linear(), "photo"), None, "")]
    for lab_, spec, note in (("渲染  第一轮(r1)", a.r1, a.r1_note), ("渲染  这一轮(r2)", a.r2, a.r2_note)):
        d, raw = (spec.split(":") + ["x.exr"])[:2]
        tag = "" if raw == "x.exr" else "_" + os.path.splitext(raw)[0]
        tiles.append((lab_, crop(card.render_linear(d, raw), d), numbers(d, tag), note))
    # the photo's own numbers: from r2's measure (same photo regions)
    m2 = tiles[2][2][0]
    P = {r["region"]: r for r in m2["regions"]}
    ph = tiles[0][1].size[1]
    H = 54 + ph + 230 + 28 * len(a.extra)
    canvas = Image.new("RGB", (3 * (TW + 12) + 12, H), (245, 245, 243))
    dr = ImageDraw.Draw(canvas)
    dr.text((12, 12), "胭脂红材质卡  第二轮:灯拟合到照片之后(左:照片  中:第一轮渲染  右:这一轮渲染;同一比例,各按自己内壁的白归一)",
            fill=(20, 20, 20), font=font(20))
    f = font(17)
    for i, (lab_, im, num, note) in enumerate(tiles):
        x = 12 + i * (TW + 12)
        canvas.paste(im, (x, 54))
        dr.text((x, 54 + ph + 8), lab_, fill=(0, 0, 0), font=font(22))
        y = 54 + ph + 40
        if i == 0:
            lines = [f"正面(中间两区)L*a*b*  {P['centre_upper']['photo_lab'][0]:.1f} {P['centre_upper']['photo_lab'][1]:.1f} "
                     f"{P['centre_upper']['photo_lab'][2]:.1f}",
                     f"侧面(左上)L*a*b*  {P['left_upper']['photo_lab'][0]:.1f} {P['left_upper']['photo_lab'][1]:.1f} "
                     f"{P['left_upper']['photo_lab'][2]:.1f}"]
        else:
            m, cen, side = num
            R = {r["region"]: r for r in m["regions"]}
            lines = [f"金量 c {m['c']} g/m2",
                     f"正面 ΔE00 {cen[0]:.1f} / {cen[1]:.1f}(中间两区)",
                     f"两侧 ΔE00 平均 {np.mean(side):.1f}(四区)",
                     f"六区平均 ΔE00 {m['mean_dE00']:.1f}",
                     f"正面 L*a*b*  {R['centre_upper']['render_lab'][0]:.1f} {R['centre_upper']['render_lab'][1]:.1f} "
                     f"{R['centre_upper']['render_lab'][2]:.1f}"]
        lines += [l for l in note.split("|") if l]
        for l in lines:
            dr.text((x, y), l, fill=(30, 30, 30), font=f)
            y += 24
    y = 54 + ph + 230
    for l in a.extra:
        dr.text((12, y), l, fill=(30, 30, 30), font=f)
        y += 28
    canvas.save(os.path.join(a.out, "sheet.png"))
    tiles[0][1].save(os.path.join(a.out, "pair", "photo.png"))
    tiles[2][1].save(os.path.join(a.out, "pair", "render.png"))
    print("->", os.path.join(a.out, "sheet.png"))


if __name__ == "__main__":
    main()
