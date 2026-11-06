"""Shot 6 v1 (S8): measure our shot in the cut the way the original was measured, and draw the sheet.

    python3 -I shots/06-guan/v1_check.py [--film out/film/film.mp4] [--out out/shots/06-guan/v1]

Both videos are decoded from the mp4 (ours: film.py's film.mp4, the original's encoder settings), never
from our PNGs:
  - arc, sky luma, object mean RGB: tools/spec_measure.py's own way (ffmpeg's default scale to 480x270,
    fit_arc on the frame, sky = luma above the arc - 8 px and below 5% of the height, object = RGB below
    the arc + 8 px), on the shot's middle frame (103) as the spec does, and on every frame for the sheet.
  - grain: std of Y' - Gaussian(Y', 1.5 px), full 1920x1080, BT.709 decode, every frame 100-105, in two
    crops: "flat" = rows 60-250, cols 100-1800 (the flat top of the sky; the number to quote), and "arc" =
    everything above the original's arc - 40 px and below 5% of the height (the first S8 v1 crop: it reaches
    down to the rim glow, whose gradient leaks into the high-pass and inflates ours, so it understated the
    gap). Our own short measure, the same on both; sub-code values, so near the 8-bit floor
    (sharpness.py measures the original's grain in its flattest tiles; this is not that number).
Writes numbers.json and sheet.png (frames 100, 102, 105 original | ours, numbers under each; a 4x crop).
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import spec_measure as sm  # noqa: E402
from compare import DECODE_VF  # noqa: E402

FIRST, LAST = 100, 105
SHEET = (100, 102, 105)
CROP = (103, 800, 700, 240, 135)          # frame, x, y, w, h (film pixels): a crackle patch below the band
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
Y709 = np.array([0.2126, 0.7152, 0.0722], np.float32)


def frames(path, vf, w, h):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf",
                          f"select=between(n\\,{FIRST}\\,{LAST}),{vf}", "-fps_mode", "passthrough", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    if len(v) != LAST - FIRST + 1:
        raise SystemExit(f"{path}: decoded {len(v)} frames of {FIRST}-{LAST}")
    return v


def spec_numbers(im):
    """spec_measure.main's per-shot numbers for one 480x270 frame."""
    im = im.astype(np.float32)
    p, ax, ay, sag, inl, res = sm.fit_arc(im)
    yy, xx = np.mgrid[0:sm.H, 0:sm.W]
    arc = np.polyval(p, xx)
    lum = im @ Y709
    sky = lum[(yy < arc - 8) & (yy > 0.05 * sm.H)]
    obj = im[yy > arc + 8]
    return {"apex": [round(float(ax), 3), round(float(ay), 3)], "sagitta": round(float(sag), 4),
            "inliers": round(float(inl), 2), "resid_px": round(float(res), 1),
            "sky_luma": round(float(sky.mean()), 1), "object_rgb": [round(float(c), 1) for c in obj.mean(0)]}


def grain(v, arc):
    """Per frame: {"flat": [...], "arc": [...]} (see the module docstring)."""
    yy, xx = np.mgrid[0:1080, 0:1920]
    a = np.polyval(arc, xx / 4.0) * 4.0
    masks = {"flat": (yy >= 60) & (yy < 250) & (xx >= 100) & (xx < 1800),
             "arc": (yy < a - 40) & (yy > 0.05 * 1080)}
    out = {k: [] for k in masks}
    for f in v:
        y = f.astype(np.float32) @ Y709
        hp = y - ndimage.gaussian_filter(y, 1.5)
        for k, m in masks.items():
            out[k].append(round(float(hp[m].std()), 3))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", default=os.path.join(ROOT, "out/film/film.mp4"))
    ap.add_argument("--orig", default=os.path.join(ROOT, "ref/opus55.mp4"))
    ap.add_argument("--out", default=os.path.join(ROOT, "out/shots/06-guan/v1"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sp = next(s for s in json.load(open(os.path.join(ROOT, "spec/shots.json")))["shots"] if s["shot"] == 6)
    N = {}
    small, full = {}, {}
    for who, path in (("original", a.orig), ("ours", a.film)):
        small[who] = frames(path, f"scale={sm.W}:{sm.H}", sm.W, sm.H)
        full[who] = frames(path, DECODE_VF, 1920, 1080)
        N[who] = {f"f{FIRST + i:04d}": spec_numbers(im) for i, im in enumerate(small[who])}
    p_orig = sm.fit_arc(small["original"][103 - FIRST].astype(np.float32))[0]
    for who in N:
        N[who]["grain_sky_f100_105"] = grain(full[who], p_orig)
    t = sp["arc"]
    o = N["ours"]["f0103"]
    N["spec"] = {"apex": [t["apex_x"], t["apex_y"]], "sagitta": t["sagitta_of_width"], "sky_luma": sp["sky_luma"],
                 "object_rgb": sp["object_rgb"]}
    N["accept"] = {
        "arc": bool(abs(o["apex"][1] - t["apex_y"]) < 0.01 and abs(o["apex"][0] - t["apex_x"]) < 0.02
                    and abs(o["sagitta"] / t["sagitta_of_width"] - 1) < 0.1),
        "sky": bool(abs(o["sky_luma"] - sp["sky_luma"]) <= 2),
        "object": bool(all(abs(int(c) - s) <= 6 for c, s in zip(o["object_rgb"], sp["object_rgb"]))),
        "note": "spec object_rgb is int() of the mean (truncated); ours is compared the same way"}
    with open(os.path.join(a.out, "numbers.json"), "w") as f:
        json.dump(N, f, indent=1)
    print(json.dumps({k: N[k] for k in ("spec", "accept")}, indent=1))
    print("ours f0103", o, "\noriginal f0103", N["original"]["f0103"])
    print("grain", N["original"]["grain_sky_f100_105"], N["ours"]["grain_sky_f100_105"])

    # the sheet: 3 rows of original | ours at half size, numbers under each; then the 4x crop
    font = ImageFont.truetype(FONT, 22)
    W2, H2, TXT = 960, 540, 64
    fr, cx, cy, cw, ch = CROP
    crop_h = ch * 4
    sheet = Image.new("RGB", (2 * W2 + 10, len(SHEET) * (H2 + TXT) + crop_h + 50), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for r, fno in enumerate(SHEET):
        for c, who in enumerate(("original", "ours")):
            im = Image.fromarray(full[who][fno - FIRST]).resize((W2, H2), Image.LANCZOS)
            x0, y0 = c * (W2 + 10), r * (H2 + TXT)
            sheet.paste(im, (x0, y0))
            n = N[who][f"f{fno:04d}"]
            d.text((x0 + 8, y0 + H2 + 6), f"{who} f{fno}  apex ({n['apex'][0]:.3f},{n['apex'][1]:.3f})  "
                   f"sagitta {100 * n['sagitta']:.2f}%", fill=(230, 230, 230), font=font)
            d.text((x0 + 8, y0 + H2 + 34), f"sky {n['sky_luma']:.1f}   object ({n['object_rgb'][0]:.0f},"
                   f"{n['object_rgb'][1]:.0f},{n['object_rgb'][2]:.0f})   sky grain {N[who]['grain_sky_f100_105']['flat'][fno - FIRST]:.3f}",
                   fill=(230, 230, 230), font=font)
    y0 = len(SHEET) * (H2 + TXT)
    for c, who in enumerate(("original", "ours")):
        im = Image.fromarray(full[who][fr - FIRST][cy:cy + ch, cx:cx + cw]).resize((cw * 4, ch * 4), Image.NEAREST)
        sheet.paste(im, (c * (W2 + 10), y0))
        d.text((c * (W2 + 10) + 8, y0 + crop_h + 10), f"{who} f{fr} x{cx}-{cx + cw} y{cy}-{cy + ch}, 4x nearest",
               fill=(230, 230, 230), font=font)
    sheet.save(os.path.join(a.out, "sheet.png"))
    print("->", os.path.join(a.out, "sheet.png"))


if __name__ == "__main__":
    main()
