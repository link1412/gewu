"""The A/B test: the CMA photo (CC0) and our render in a random order: each on its own (ab_A.png, ab_B.png), and one
above the other on a vertical 1080x1920 picture with the question (ab_still.png); the answer in ab_key.json. --video
also makes the push-in video (H.264, the same slow push-in on both).

    python3 -I objects/ru_washer/ab.py RENDER.png --out out/ru/final/ab [--photo ref/ru/photos/cma_1957.40.jpg]
        [--seconds 8] [--zoom 1.12] [--seed N]
"""
import argparse
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONT = "/System/Library/Fonts/PingFang.ttc"
W, H, FPS = 1080, 1920, 30
TITLE, SUB = "哪张是真的?", "一张是博物馆实拍，一张是代码渲染"


def frame(imgs, z, font_t, font_s, font_l):
    out = Image.new("RGB", (W, H), (0, 0, 0))
    iw, ih = imgs[0].size
    th = round(W * ih / iw)
    y0s = [380, 380 + th + 70]                     # below Douyin's top bar; its caption covers the bottom
    for k, (im, y0) in enumerate(zip(imgs, y0s)):
        cw, ch = iw / z, ih / z
        box = ((iw - cw) / 2, (ih - ch) / 2, (iw + cw) / 2, (ih + ch) / 2)
        out.paste(im.resize((W, th), Image.LANCZOS, box=box), (0, y0))
    d = ImageDraw.Draw(out)
    d.text((W / 2, 230), TITLE, font=font_t, fill=(240, 240, 240), anchor="mm")
    d.text((W / 2, 305), SUB, font=font_s, fill=(170, 170, 170), anchor="mm")
    for lab, y0 in zip("AB", y0s):
        d.text((36, y0 + 24), lab, font=font_l, fill=(225, 225, 225), anchor="lt")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("--out", required=True)
    ap.add_argument("--photo", default=os.path.join(ROOT, "ref/ru/photos/cma_1957.40.jpg"))
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--zoom", type=float, default=1.12)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--video", action="store_true", help="also the push-in video (the default is the pictures only)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ren = Image.open(a.render).convert("RGB")
    ph = Image.open(a.photo).convert("RGB").resize(ren.size, Image.LANCZOS)
    rng = np.random.default_rng(a.seed)
    photo_first = bool(rng.integers(2))
    imgs = [ph, ren] if photo_first else [ren, ph]
    key = {"A": "photo (CMA 1957.40, CC0)" if photo_first else "render", "B": "render" if photo_first else "photo (CMA 1957.40, CC0)"}
    json.dump(key, open(os.path.join(a.out, "ab_key.json"), "w"), indent=1, ensure_ascii=False)
    for lab, im in zip("AB", imgs):
        im.save(os.path.join(a.out, f"ab_{lab}.png"))
    ft, fs, fl = (ImageFont.truetype(FONT, s) for s in (84, 40, 52))
    if not a.video:
        frame(imgs, 1.0, ft, fs, fl).save(os.path.join(a.out, "ab_still.png"))
        print(f"wrote ab_A.png, ab_B.png, ab_still.png in {a.out}, key {key}")
        return
    n = int(round(a.seconds * FPS))
    mp4 = os.path.join(a.out, "ab.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    for i in range(n):
        z = a.zoom ** (i / (n - 1))                       # a constant rate of push-in
        f = frame(imgs, z, ft, fs, fl)
        if i == 0:
            f.save(os.path.join(a.out, "ab_still.png"))
        ff.stdin.write(f.tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ab: ffmpeg failed")
    print(f"wrote {mp4} ({n} frames), key {key}")


if __name__ == "__main__":
    main()
