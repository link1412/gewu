"""Shot 19 round 1 review sheet (docs/shots/19-luodian.md).

    python3 -I shots/19-luodian/sheet.py --crop X,Y [--out out/shots/19-luodian/r1/sheet.png]

Rows: frames 255, 260, 266, the original | ours (decoded from out/film/film.mp4), with spec_measure's numbers; then a
3x crop of our shell pieces (at 1080, the window X,Y 1920-px coordinates, 213x120) in frames 255 and 266, next to a
detail of a reference photograph (labelled: not ours); a 1:1 crop of our frame 260 next to a reference photo; then
the TMM validation plot (nacre_check.py).
"""

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import fit  # noqa: E402
import measure  # noqa: E402

FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
REF = ("ref/luodian/img/qingdao_kangxi_03.jpg", (380, 260, 1000, 610),
       "Qingdao Museum, Kangxi black-lacquer dish with thin mother-of-pearl (museum web image), detail")
REF_FULL = ("ref/luodian/img/qingdao_kangxi_03.jpg", (0, 0, 1280, 720))


def label(im, text, xy=(12, 8), size=26):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, size)
    x, y = xy
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            d.text((x + dx, y + dy), text, font=f, fill=(0, 0, 0))
    d.text(xy, text, font=f, fill=(255, 255, 255))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop", required=True, help="X,Y of a 213x120 window at 1920x1080")
    ap.add_argument("--film", default=os.path.join(ROOT, "out/film/film.mp4"))
    ap.add_argument("--tmm", default=os.path.join(ROOT, "out/shots/19-luodian/r1/tmm.png"))
    ap.add_argument("--out", default=os.path.join(ROOT, "out/shots/19-luodian/r1/sheet.png"))
    a = ap.parse_args()
    frames = [255, 260, 266]
    ours = fit.decode_frames(a.film, list(range(255, 267)))
    orig = fit.decode_frames(os.path.join(ROOT, "ref/opus55.mp4"), list(range(255, 267)))
    rows = []
    for f in frames:
        o, u = orig[f - 255], ours[f - 255]
        so, su = measure.stats(o), measure.stats(u)
        L = Image.fromarray(o).resize((960, 540), Image.LANCZOS)
        R = Image.fromarray(u).resize((960, 540), Image.LANCZOS)
        fmt = lambda s: (f"arc ({s['apex_x']:.3f}, {s['apex_y']:.3f}) sag {100 * s['sagitta']:.2f}%  sky {s['sky_luma']:.1f}  "
                         f"obj {' '.join(str(int(round(v))) for v in s['object_rgb'])}")
        label(L, f"original f{f}")
        label(L, fmt(so), (12, 500), 20)
        label(R, f"ours r1 fix f{f}  (黑漆嵌螺钿)")
        label(R, fmt(su), (12, 500), 20)
        row = Image.new("RGB", (1920, 540))
        row.paste(L, (0, 0))
        row.paste(R, (960, 0))
        rows.append(row)
    x, y = (int(v) for v in a.crop.split(","))
    crops = []
    for f in (255, 266):
        c = Image.fromarray(ours[f - 255][y:y + 120, x:x + 213]).resize((639, 360), Image.NEAREST)
        label(c, f"ours f{f}, 3x crop", size=22)
        crops.append(c)
    rp, box, text = REF
    ref = Image.open(os.path.join(ROOT, rp)).convert("RGB").crop(box)
    ref = ref.resize((639, int(639 * ref.height / ref.width)), Image.LANCZOS).crop((0, 0, 639, 360))
    label(ref, "reference photo, not ours", size=22)
    label(ref, "Qingdao Museum Kangxi dish, web image (detail)", (12, 326), 18)
    row = Image.new("RGB", (1920, 360))
    for i, c in enumerate(crops + [ref]):
        row.paste(c, (i * 640, 0))
    rows.append(row)
    # 1:1: the lower middle of our frame 260 at 1080 next to a reference photo at a similar piece size
    c = Image.fromarray(ours[260 - 255][540:1080, 480:1440])
    label(c, "ours f260, 1:1 at 1080 (lower middle)", size=22)
    rp, box = REF_FULL
    r2 = Image.open(os.path.join(ROOT, rp)).convert("RGB").crop(box).resize((960, 540), Image.LANCZOS)
    label(r2, "reference photo, not ours: Qingdao Museum Kangxi dish (web image)", size=20)
    row = Image.new("RGB", (1920, 540))
    row.paste(c, (0, 0))
    row.paste(r2, (960, 0))
    rows.append(row)
    t = Image.open(a.tmm).convert("RGB")
    t = t.resize((1920, int(1920 * t.height / t.width)), Image.LANCZOS)
    rows.append(t)
    H = sum(r.height for r in rows)
    sheet = Image.new("RGB", (1920, H))
    yy = 0
    for r in rows:
        sheet.paste(r, (0, yy))
        yy += r.height
    sheet.save(a.out)
    print(f"-> {a.out} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
