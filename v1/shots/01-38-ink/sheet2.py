"""Round 2 sheet: r1's layout (frames 0, 15, 420, 470, 485, 499; original | ours; numbers under each) plus a strip of
frames 399-480 every 9 frames (original above ours), and the sky / band-profile numbers.

    python3 -I shots/01-38-ink/sheet2.py [--frames-dir out/shots/01-38-ink/r2/frames] [--r1 out/shots/01-38-ink/r1/frames]
    -> out/shots/01-38-ink/r2/{sheet.png, strip.png, numbers.json}

Numbers: r1's (sheet.numbers) and, per frame, the three column-band profiles' rms against the original at 1080 rows
(ours upscaled the way compare.py does; title rows masked; frame 0 only down to 0.3 H below the horizon, as the fit)
plus the top-60 sky RGB. Decode of the original: bt709 tv range.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fit2 as F2  # noqa: E402
import measure as M  # noqa: E402
import sheet as S  # noqa: E402

R2 = os.path.join(M.ROOT, "out/shots/01-38-ink/r2")
STRIP = list(range(399, 481, 9))


def band_rms(im, f, prof):
    if f not in prof:
        return None
    ours = np.stack([im[:, a0:a1].astype(float).mean(axis=1) for a0, a1 in F2.BANDS])
    po, v = prof[f]
    m = v.copy()
    if f == 0:
        m &= F2.frame0_rows(M.FH)
    e = (ours - po)[m]
    return round(float(np.sqrt(np.mean(e ** 2))), 2)


def _centre_luma(im, o):
    """Centre band (880-1040) luma per row, the original's title pixels masked (the checker's metric)."""
    tm = __import__("measure_sky").title_mask(o)
    b = np.where(tm[:, 880:1040, None], np.nan, im[:, 880:1040].astype(float))
    return M.luma(np.nanmean(b, axis=1))


def glow_rms(im, o):
    """The bottom third (rows 720-1080) of the centre band, luma rms against the original: the glow (r2 checker)."""
    e = (_centre_luma(im, o) - _centre_luma(o, o))[720:1080]
    return round(float(np.sqrt(np.nanmean(e ** 2))), 2)


def centre_rows(im):
    return [round(float(v), 1) for v in M.luma(im[:, 880:1040].astype(float).mean(axis=1))[::90]]


def sky_rgb(im):
    tm = __import__("measure_sky").title_mask(im)
    top = im[:60].astype(float)[~tm[:60]]
    return [round(float(x), 1) for x in top.mean(axis=0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-dir", default=os.path.join(R2, "frames"))
    ap.add_argument("--r1", default=os.path.join(M.ROOT, "out/shots/01-38-ink/r1/frames"))
    ap.add_argument("--prev", default=None, help="round 2's first pass (r2a) frames, reported alongside")
    ap.add_argument("--title", default="r2 sky fix")
    a = ap.parse_args()
    d = np.load(os.path.join(R2, "orig_profiles.npz"))
    prof = {int(f): (d["prof"][i].astype(float), d["valid"][i]) for i, f in enumerate(d["frames"])}
    frames = S.FRAMES
    allf = sorted(set(frames + STRIP + F2.HELD))
    orig = dict(zip(allf, M.decode_original(allf)))
    track = {int(k): v for k, v in json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/track.json"))).items()}
    f_big, f_sm = S.font(22), S.font(15)
    TW, TH = S.TW, S.TH
    rowh = TH + 112
    sheet = Image.new("RGB", (2 * TW + 30, 60 + rowh * len(frames)), (245, 244, 240))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 12), f"Shots 1 / 38, {a.title} (preview 960x540, no camera chain): original (left) | ours (right)",
            fill=(0, 0, 0), font=f_big)
    allnum = {}
    for f in allf:
        o = orig[f]
        ours = M.read_png(os.path.join(a.frames_dir, f"f{f:04d}.png"))
        r1 = M.read_png(os.path.join(a.r1, f"f{f:04d}.png"))
        no, nu, n1 = S.numbers(o), S.numbers(ours), S.numbers(r1)
        nu["band_rms"], n1["band_rms"] = band_rms(ours, f, prof), band_rms(r1, f, prof)
        no["sky_rgb"], nu["sky_rgb"], n1["sky_rgb"] = sky_rgb(o), sky_rgb(ours), sky_rgb(r1)
        for n, im in ((no, o), (nu, ours), (n1, r1)):
            n["glow_rms_centre_720_1080"] = None if n is no else glow_rms(im, o)
            n["centre_luma_every_90_rows"] = centre_rows(im)
        allnum[f] = dict(original=no, ours_r2=nu, ours_r1=n1, original_track_horizon=round(track[f]["horizon_y"], 4),
                         role="fit" if f in F2.FIT else ("held-out" if f in F2.HELD else "not fitted"))
        if a.prev:
            pv = M.read_png(os.path.join(a.prev, f"f{f:04d}.png"))
            npv = S.numbers(pv)
            npv["band_rms"], npv["sky_rgb"] = band_rms(pv, f, prof), sky_rgb(pv)
            npv["glow_rms_centre_720_1080"] = glow_rms(pv, o)
            allnum[f]["ours_r2a"] = npv
        if f in frames:
            i = frames.index(f)
            y0 = 60 + i * rowh
            sheet.paste(Image.fromarray(o).resize((TW, TH)), (10, y0))
            sheet.paste(Image.fromarray(ours).resize((TW, TH)), (20 + TW, y0))
            shot = 1 if f < 399 else 38
            dr.text((16, y0 + 6), f"shot {shot}  frame {f}  ({allnum[f]['role']})", fill=(255, 255, 255), font=f_big)
            for j, (n, x) in enumerate(((no, 10), (nu, 20 + TW))):
                lines = S.fmt(n, track[f]["horizon_y"] if j == 0 else None)
                lines.append(f"sky RGB {n['sky_rgb']}" + (f"  band rms {n['band_rms']} (r1 {n1['band_rms']})" if j and n['band_rms'] is not None else ""))
                for k, line in enumerate(lines):
                    dr.text((x, y0 + TH + 4 + 20 * k), line, fill=(20, 20, 20), font=f_sm)
    sheet.save(os.path.join(R2, "sheet.png"))

    sw, sh = 320, 180
    strip = Image.new("RGB", (10 + len(STRIP) * (sw + 6), 50 + 2 * (sh + 6) + 70), (245, 244, 240))
    ds = ImageDraw.Draw(strip)
    ds.text((10, 10), f"Shot 38 frames 399-480 every 9: original (top) | ours {a.title.split()[0]} (bottom); numbers: sky luma o/ours, band rms ours (r1); glow rms ours",
            fill=(0, 0, 0), font=f_sm)
    for i, f in enumerate(STRIP):
        x = 10 + i * (sw + 6)
        strip.paste(Image.fromarray(orig[f]).resize((sw, sh)), (x, 40))
        strip.paste(Image.fromarray(M.read_png(os.path.join(a.frames_dir, f"f{f:04d}.png"))).resize((sw, sh)), (x, 46 + sh))
        n = allnum[f]
        ds.text((x, 52 + 2 * sh), f"{f}: sky {n['original']['sky_luma']}/{n['ours_r2']['sky_luma']}", fill=(0, 0, 0), font=f_sm)
        ds.text((x, 70 + 2 * sh), f"band rms {n['ours_r2']['band_rms']} (r1 {n['ours_r1']['band_rms']})", fill=(0, 0, 0), font=f_sm)
        ds.text((x, 88 + 2 * sh), f"glow rms {n['ours_r2']['glow_rms_centre_720_1080']} (r1 {n['ours_r1']['glow_rms_centre_720_1080']})", fill=(0, 0, 0), font=f_sm)
    strip.save(os.path.join(R2, "strip.png"))
    with open(os.path.join(R2, "numbers.json"), "w") as fh:
        json.dump({str(k): v for k, v in allnum.items()}, fh, indent=1)
    for f in allf:
        n = allnum[f]
        print(f, n["role"], "sky o/r1/r2", n["original"]["sky_luma"], n["ours_r1"]["sky_luma"], n["ours_r2"]["sky_luma"],
              "rgb", n["original"]["sky_rgb"], n["ours_r2"]["sky_rgb"], "band rms r1/r2", n["ours_r1"]["band_rms"],
              n["ours_r2"]["band_rms"])


if __name__ == "__main__":
    main()
