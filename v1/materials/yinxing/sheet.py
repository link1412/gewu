"""The review sheet and the blind pair for the backlit card (S8): photo, this round's render, last round's render.

    python3 -I materials/yinxing/sheet.py NEW.exr OLD.exr OUTDIR [--var VAR.json] [--cmp COMPARE.json] [--fit FIT.json]

- OUTDIR/sheet.png: three columns (照片 / 渲染 本轮 / 渲染 上一轮), the whole leaf and a 1:1 crop of the distal middle
  (16 px/mm, the same pixels: the render is framed on the photo), the key numbers under each column.
- OUTDIR/blind_photo.png, OUTDIR/blind_render.png: the same crop box of the photo and of the new render, pixels only,
  for tools/blind.py.
Both sides displayed the same way: linear relative to the lamp's white, sRGB encoded (compare.display).
"""
import argparse
import importlib.util
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402,F401
_spec = importlib.util.spec_from_file_location("yinxing_compare", os.path.join(HERE, "compare.py"))
CMP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CMP)

CROP = (380, 110, 892, 494)          # x0, y0, x1, y1 px: the distal middle with a stretch of margin, 32 x 24 mm
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"


def render_disp(path):
    card = json.load(open(os.path.join(os.path.dirname(os.path.abspath(path)), "card.json")))
    card.setdefault("sensor", "canon_eos_5d_mkiv")
    lin, _ = CMP.develop(path, card, "lamp")
    return CMP.display(lin)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("old")
    ap.add_argument("outdir")
    ap.add_argument("--var")
    ap.add_argument("--cmp")
    ap.add_argument("--notes", nargs=3, default=["", "", ""], help="one text per column (newlines as |)")
    ap.add_argument("--titles", nargs=3, default=["照片(Fargoh,手机 JPEG)", "渲染 · 本轮(S8 第 1 轮)", "渲染 · 上一轮(S7)"])
    ap.add_argument("--blind", default=None, help="where the blind crops go (default OUTDIR); keep them out of the "
                                                    "judges' folder's parent listing")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    plin, _, _ = CMP.photo_linear("lamp")
    P = CMP.display(plin)
    N = render_disp(a.new)
    O = render_disp(a.old)
    x0, y0, x1, y1 = CROP
    bd = a.blind or a.outdir
    os.makedirs(bd, exist_ok=True)
    Image.fromarray(P[y0:y1, x0:x1]).save(os.path.join(bd, "blind_photo.png"))
    Image.fromarray(N[y0:y1, x0:x1]).save(os.path.join(bd, "blind_render.png"))
    colw = 640
    s = colw / P.shape[1]
    fulls = [Image.fromarray(im).resize((colw, int(im.shape[0] * s)), Image.LANCZOS) for im in (P, N, O)]
    crops = [Image.fromarray(im[y0:y1, x0:x1]).resize((colw, int((y1 - y0) * colw / (x1 - x0))), Image.LANCZOS)
             for im in (P, N, O)]
    titles = a.titles
    f_t = ImageFont.truetype(FONT, 26)
    f_s = ImageFont.truetype(FONT, 17)
    head, gap, foot = 44, 10, 300
    H = head + fulls[0].height + gap + 24 + crops[0].height + gap + foot
    W = 3 * colw + 4 * gap
    sheet = Image.new("RGB", (W, H), (245, 243, 238))
    d = ImageDraw.Draw(sheet)
    for i in range(3):
        x = gap + i * (colw + gap)
        d.text((x, 8), titles[i], font=f_t, fill=(20, 20, 20))
        sheet.paste(fulls[i], (x, head))
        y = head + fulls[i].height + gap
        d.text((x, y), "1:1 局部(远缘中部,32 × 24 mm,16 px/mm;整叶图上的框)", font=f_s, fill=(60, 60, 60))
        sheet.paste(crops[i], (x, y + 24))
        bx = [x + int(v * s) for v in (x0,)] + [head + int(y0 * s)] + [x + int(x1 * s)] + [head + int(y1 * s)]
        d.rectangle([bx[0], bx[1], bx[2], bx[3]], outline=(255, 255, 255), width=2)
        ty = y + 24 + crops[i].height + gap
        for k, line in enumerate(a.notes[i].split("|")):
            d.text((x, ty + k * 22), line, font=f_s, fill=(20, 20, 20))
    sheet.save(os.path.join(a.outdir, "sheet.png"))
    print("->", os.path.join(a.outdir, "sheet.png"))


if __name__ == "__main__":
    main()
