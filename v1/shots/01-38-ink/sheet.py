"""Side-by-side sheet: the original vs ours for shot 1 and moments of shot 38, with the acceptance numbers.

    python3 -I shots/01-38-ink/sheet.py [--frames-dir out/shots/01-38-ink/r1/frames] [--out out/shots/01-38-ink/r1/sheet.png]
    -> sheet.png and numbers.json next to it.

Numbers per frame (measure.py on both, ours upscaled to 1920x1080 like tools/compare.py does):
  horizon y at the centre (/H; for 38 also the track.py value of the original and our camera's projection of the
  ink edge), R/W of the arc, edge 10-90 % (px at 1080), band peak RGB, rim RGB (just above the horizon), blue 6 %
  above, sky luma (top 60 rows), mean linear luma of the frame.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402

FRAMES = [0, 15, 420, 470, 485, 499]
TW, TH = 640, 360


def font(sz):
    for p in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Supplemental/Courier New.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def numbers(im):
    m = M.measure(im)
    L = M.lin(M.luma(im[::4, ::4]))
    out = dict(mean_lin=round(float(L.mean()), 4), sky_luma=round(m["sky_luma"], 1))
    if m.get("resid_px", 99) > 5 or m.get("n_cols", 0) < 60:   # no clean arc in frame (horizon below it): drop the arc numbers
        m = {k: v for k, v in m.items() if k in ("sky_luma",)}
    for k in ("horizon_y_centre", "r_over_w", "edge_10_90_px", "peak_rgb", "rim_rgb", "blue_rgb_6pc_above", "resid_px"):
        if k in m and m[k] is not None:
            v = m[k]
            out[k] = [round(x) for x in v] if isinstance(v, list) else round(v, 3)
    return out


def fmt(n, track_h=None):
    s = []
    if "horizon_y_centre" in n:
        s.append(f"horizon {n['horizon_y_centre']:.3f}H  R/W {n.get('r_over_w', float('nan')):.2f}  "
                 f"edge {n.get('edge_10_90_px', '-')}px")
    elif track_h is not None:
        s.append(f"horizon {track_h:.3f}H (below frame)")
    if "peak_rgb" in n:
        s.append(f"peak {n['peak_rgb']}  rim {n.get('rim_rgb', '-')}")
    if "blue_rgb_6pc_above" in n:
        s.append(f"6% above {n['blue_rgb_6pc_above']}")
    s.append(f"sky {n['sky_luma']}  mean lin {n['mean_lin']}")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-dir", default=os.path.join(M.ROOT, "out/shots/01-38-ink/r1/frames"))
    ap.add_argument("--out", default=os.path.join(M.ROOT, "out/shots/01-38-ink/r1/sheet.png"))
    a = ap.parse_args()
    orig = dict(zip(FRAMES, M.decode_original(FRAMES)))
    track = {int(k): v for k, v in json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/track.json"))).items()}
    poses = {}
    pj = os.path.join(a.frames_dir, "poses.json")
    if os.path.exists(pj):
        poses = {int(k): v for k, v in json.load(open(pj)).items()}
    f_big, f_sm = font(22), font(15)
    rowh = TH + 92
    sheet = Image.new("RGB", (2 * TW + 30, 60 + rowh * len(FRAMES)), (245, 244, 240))
    d = ImageDraw.Draw(sheet)
    d.text((10, 12), "Shots 1 / 38, r1 (preview 960x540, no camera chain): original (left) | ours (right)", fill=(0, 0, 0), font=f_big)
    allnum = {}
    for i, f in enumerate(FRAMES):
        y0 = 60 + i * rowh
        o = orig[f]
        ours = M.read_png(os.path.join(a.frames_dir, f"f{f:04d}.png"))
        no, nu = numbers(o), numbers(ours)
        allnum[f] = dict(original=no, ours=nu, original_track_horizon=round(track[f]["horizon_y"], 4))
        sheet.paste(Image.fromarray(o).resize((TW, TH)), (10, y0))
        sheet.paste(Image.fromarray(ours).resize((TW, TH)), (20 + TW, y0))
        shot = 1 if f < 399 else 38
        d.text((16, y0 + 6), f"shot {shot}  frame {f}", fill=(255, 255, 255), font=f_big)
        for j, (n, x) in enumerate(((no, 10), (nu, 20 + TW))):
            for k, line in enumerate(fmt(n, track[f]["horizon_y"] if j == 0 else None)):
                d.text((x, y0 + TH + 4 + 20 * k), line, fill=(20, 20, 20), font=f_sm)
    sheet.save(a.out)
    with open(os.path.join(os.path.dirname(a.out), "numbers.json"), "w") as fh:
        json.dump(allnum, fh, indent=1)
    print(json.dumps(allnum, indent=0)[:4000])


if __name__ == "__main__":
    main()
