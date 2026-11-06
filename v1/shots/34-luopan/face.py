"""Shot 34: the luopan's face as an albedo texture (python3 -I shots/34-luopan/face.py OUT_DIR).

Writes OUT_DIR/face.png (sRGB albedo, N x N over the disc's diameter; outside the disc transparent-free beige) and
OUT_DIR/face_ink.png (ink coverage, for a slight gloss difference). Everything [A], drawn after the common layout of a
三元/三合 luopan: concentric rings with radial dividers, each sector one or two small characters (天干, 地支, 八卦,
二十四山, 数字), tick rings of 360 / 120 / 72 marks, a 天池 at the centre. The characters come from the system's Songti
font, used as a texture only. Red ink on a few rings, as real luopans do.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

N = 4096
FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"
BASE = (234, 226, 216)            # pale 米黄 lacquer, near the paper (the original is near-white) [A]
INK = (28, 22, 18)
RED = (176, 38, 30)
SHAN24 = "壬子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥"
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
GUA = "乾坎艮震巽離坤兌"
NUM = "一二三四五六七八九"
WUXING = "金木水火土"
rng = np.random.default_rng(34)

# rings (outer radius fraction, kind, count, colour); from the rim inward; the frame shows r > ~0.55 [A]
RINGS = [
    (1.000, "rim", 0, INK),
    (0.985, "ticks", 180, INK),       # 180 not 360: the outer band was ~12 codes darker than the original's
    (0.955, "chars", 60, INK),        # 分金 (60, not 120: same reason)
    (0.905, "chars", 72, RED),        # 穿山七十二龍
    (0.860, "plain", 0, INK),
    (0.840, "chars", 60, INK),        # 六十甲子
    (0.785, "chars", 24, INK),        # 二十四山 (big)
    (0.700, "chars", 48, RED),
    (0.650, "chars", 24, INK),
    (0.590, "chars", 64, INK),        # 六十四卦
    (0.540, "chars", 8, RED),
    (0.460, "chars", 24, INK),
    (0.380, "chars", 12, INK),
    (0.300, "chars", 8, INK),
    (0.220, "plain", 0, INK),
    (0.150, "pool", 0, INK),          # 天池
]


def text_for(count, k):
    if count == 24:
        return SHAN24[k % 24]
    if count == 120:
        return GAN[k % 10] + ZHI[k % 12]
    if count == 60:
        return GAN[k % 10] + ZHI[k % 12]
    if count == 72:
        return GAN[(k // 3) % 10] + ZHI[k % 12]
    if count == 8:
        return GUA[k]
    if count == 12:
        return ZHI[k]
    if count == 64:
        return GUA[k % 8] + GUA[(k // 8) % 8]
    if count == 48:
        return NUM[k % 9] + WUXING[k % 5]
    return SHAN24[k % 24]


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    img = Image.new("RGB", (N, N), BASE)
    ink = Image.new("L", (N, N), 0)
    d, di = ImageDraw.Draw(img), ImageDraw.Draw(ink)
    c = N / 2
    R = N / 2 - 2
    lw = max(2, N // 900)

    def circle(r, w, col):
        d.ellipse([c - r, c - r, c + r, c + r], outline=col, width=w)
        di.ellipse([c - r, c - r, c + r, c + r], outline=255, width=w)

    def radial(a, r0, r1, w, col):
        p0 = (c + r0 * math.sin(a), c - r0 * math.cos(a))
        p1 = (c + r1 * math.sin(a), c - r1 * math.cos(a))
        d.line([p0, p1], fill=col, width=w)
        di.line([p0, p1], fill=255, width=w)

    fonts = {}
    for i, (rf, kind, cnt, col) in enumerate(RINGS):
        r_out = rf * R
        r_in = RINGS[i + 1][0] * R if i + 1 < len(RINGS) else 0
        circle(r_out, lw * (3 if kind == "rim" else 1), INK)
        if kind == "ticks":
            for k in range(cnt):
                a = 2 * math.pi * k / cnt
                long_ = k % 5 == 0 if cnt >= 180 else True
                radial(a, r_out - (r_out - r_in) * (1.0 if long_ else 0.55), r_out, lw if long_ else max(1, lw - 1), col)
        elif kind == "chars":
            rot0 = -1.5 * 2 * math.pi / cnt if cnt == 24 else 0.0  # 二十四山: 子 centred on north (top); others start at north
            for k in range(cnt):
                radial(rot0 + 2 * math.pi * k / cnt, r_in, r_out, lw, INK)
            band = r_out - r_in
            for k in range(cnt):
                t = text_for(cnt, k)
                arc = 2 * math.pi * r_out / cnt * (r_in + band / 2) / r_out
                # characters stacked radially (outer first), sized to the band and the sector
                size = int(min(band / (len(t) + 0.4), arc * 0.78))
                if size < 6:
                    continue
                f = fonts.setdefault(size, ImageFont.truetype(FONT, size, index=0))
                tile = Image.new("L", (size + 4, len(t) * size + 4), 0)
                td = ImageDraw.Draw(tile)
                for j, ch in enumerate(t):
                    td.text((2, 2 + j * size), ch, font=f, fill=255)
                a = rot0 + 2 * math.pi * (k + 0.5) / cnt
                tile = tile.rotate(-math.degrees(a), resample=Image.BICUBIC, expand=True)
                rm = r_in + band / 2
                x, y = c + rm * math.sin(a) - tile.width / 2, c - rm * math.cos(a) - tile.height / 2
                colour = Image.new("RGB", tile.size, col)
                img.paste(colour, (int(x), int(y)), tile)
                ink.paste(255, (int(x), int(y)), tile)
        elif kind == "pool":
            circle(r_out * 0.92, lw, INK)
    # lacquer wear: very low-contrast mottling [A]
    a = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:N:8, 0:N:8]
    mott = sum(np.cos((xx * kx + yy * ky) * 2 * np.pi / N * f + ph) for kx, ky, f, ph in
               ((rng.normal(), rng.normal(), rng.uniform(3, 30), rng.uniform(0, 6)) for _ in range(24))) / 24
    mott = np.kron(mott, np.ones((8, 8)))[:N, :N]
    a *= (1 + 0.035 * mott)[..., None]
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(out, "face.png"))
    ink.save(os.path.join(out, "face_ink.png"))
    print("face", N, "->", out)


if __name__ == "__main__":
    main()
