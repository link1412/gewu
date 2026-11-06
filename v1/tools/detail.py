"""How much visible detail a frame carries, scale by scale, inside the object (below the arc).

    python3 -I tools/detail.py profile "orig 6=ref/opus55.mp4:103" "ours=out/06/shot3/dev/f0103.png" \
                                       "vm 36=ref/reference-film.mp4:392"
    python3 -I tools/detail.py sheet out/cmp/detail06.png "orig 6=ref/opus55.mp4:103" "ours=out/06/x/f0103.png" ...

A source is a PNG, or VIDEO:FRAME (frame numbers of that video; the reference film runs one frame
behind the original, so its shot N is the original's frame + 1). Everything is measured at 1024x576,
the reference film's own size, so all sources are compared at the size a viewer sees them.

profile: for octave bands of scale (px at 1024 wide), the RMS of a difference of Gaussians of the luma,
divided by the region's mean luma, in percent; then the region's 8-bit luma at the 5th/50th/95th
percentile. Luma is linear luminance (BT.709 primaries) raised to 1/2.2. The region is everything 4% of
the height below the arc (spec_measure.fit_arc, the fit that measured the original) down to 97%, from 5%
to 95% of the width; --rows a:b (fractions of the height) replaces it when the fit catches another edge.
This is our own yardstick (S3), not a published one: it says "fine detail is 3x weaker than the
reference", not whether the detail is the right kind.

sheet: the sources stacked at 1024x576 with their labels, for looking.
"""

import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_measure as sm  # noqa: E402
from compare import DECODE_VF  # noqa: E402

W, H = 1024, 576
BANDS = [(0.7, 1.4), (1.4, 2.8), (2.8, 5.6), (5.6, 11.2), (11.2, 22.4)]


def load(src):
    """RGB uint8 at 1024x576 from a PNG or VIDEO:FRAME."""
    path, _, n = src.rpartition(":")
    if path and n.isdigit():
        raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf",
                              f"select=eq(n\\,{n}),{DECODE_VF},scale={W}:{H}:flags=lanczos", "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        if len(raw) != W * H * 3:
            sys.exit(f"{src}: no such frame")
        return np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    return np.asarray(Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS))


def region(im, rows):
    yy, xx = np.mgrid[0:H, 0:W]
    m = (xx > 0.05 * W) & (xx < 0.95 * W)
    if rows:
        a, b = (float(v) for v in rows.split(":"))
        return m & (yy >= a * H) & (yy < b * H)
    small = np.asarray(Image.fromarray(im).resize((sm.W, sm.H), Image.BILINEAR), np.float32)
    p, *_ = sm.fit_arc(small)
    arc = np.polyval(p, xx * sm.W / W) * H / sm.H
    return m & (yy > arc + 0.04 * H) & (yy < 0.97 * H)


def profile(im, m):
    x = im.astype(np.float32) / 255
    lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    L = (lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)) ** (1 / 2.2)
    bands = [np.sqrt(np.mean((gaussian_filter(L, a) - gaussian_filter(L, b))[m] ** 2)) / L[m].mean()
             for a, b in BANDS]
    y8 = (im.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32))[m]
    return bands, np.percentile(y8, [5, 50, 95])


def parse(items):
    out = []
    for s in items:
        label, sep, src = s.partition("=")
        out.append((label, src) if sep else (os.path.basename(s), s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["profile", "sheet"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--rows", help="region a:b in fractions of the height, instead of below the arc")
    a = ap.parse_args()
    if a.cmd == "profile":
        print(f"{'':34s}" + "".join(f"{f'{lo:g}-{hi:g}px':>12s}" for lo, hi in BANDS) + "   luma p5/p50/p95")
        for label, src in parse(a.args):
            im = load(src)
            m = region(im, a.rows)
            bands, pct = profile(im, m)
            print(f"{label[:34]:34s}" + "".join(f"{100 * v:12.2f}" for v in bands)
                  + f"   {pct[0]:4.0f} {pct[1]:4.0f} {pct[2]:4.0f}   ({100 * m.mean():.0f}% of frame)")
    else:
        dst, items = a.args[0], parse(a.args[1:])
        sheet = Image.new("RGB", (W, len(items) * (H + 4) - 4), (40, 40, 40))
        d = ImageDraw.Draw(sheet)
        for k, (label, src) in enumerate(items):
            y = k * (H + 4)
            sheet.paste(Image.fromarray(load(src)), (0, y))
            d.rectangle([0, y, 8 + 7 * len(label), y + 16], fill=(0, 0, 0))
            d.text((4, y + 2), label, fill=(255, 255, 0))
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        sheet.save(dst)
        print(dst)


if __name__ == "__main__":
    main()
