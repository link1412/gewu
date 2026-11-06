"""Measure the original's shots 1 and 38 (the limb / sunrise): the acceptance numbers.

    python3 -I shots/01-38-ink/measure.py            # -> out/shots/01-38-ink/measure/{orig.json, *.png}
    python3 -I shots/01-38-ink/measure.py --ours DIR # same numbers on our frames (fNNNN.png, global numbering)

Per frame, decoded as viewers see it (BT.709, tv range, same as tools/compare.py):
  - horizon y(x): per column (every 16 px, 64..1856), the row where luma rises through half-way between the
    dark ground below and the band peak above, searched upwards from the bottom; then a circle fit
    (apex, sagitta over the frame width, R/W) and its residual;
  - band: peak luma (Y' code value and linear), its height above the horizon, the hue at the horizon
    (R-B of the 12 rows just above it = "orange"), the colour 3 % of frame height above (= "blue"), the
    10-90 % rise width of the edge at the centre (softness), the sky (rows 0-60) and the ground;
  - title cards: white low-saturation pixels above the horizon: bounding box (shot 38 only).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FW, FH = 1920, 1080
DECODE_VF = "scale=in_color_matrix=bt709:in_range=tv,format=rgb24"
FRAMES = list(range(0, 31)) + list(range(399, 500))   # shot 1 = 0..30, shot 38 = 399..499 (spec frame_out exclusive)
COLS = np.arange(64, 1857, 16)


def decode_original(frames):
    runs, a = [], frames[0]
    for i in range(1, len(frames) + 1):
        if i == len(frames) or frames[i] != frames[i - 1] + 1:
            runs.append((a, frames[i - 1]))
            if i < len(frames):
                a = frames[i]
    sel = "+".join(f"between(n\\,{x}\\,{y})" for x, y in runs)
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", os.path.join(ROOT, "ref/opus55.mp4"),
                          "-vf", f"select='{sel}',{DECODE_VF}", "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)
    assert len(v) == len(frames), (len(v), len(frames))
    return v


def read_png(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf", f"scale={FW}:{FH}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(FH, FW, 3)


def lin(v):
    v = np.asarray(v, float) / 255
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def luma(im):
    im = im.astype(float)
    return 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]


def title_box(im, horizon_top):
    """White, unsaturated pixels above the horizon (the end-card type)."""
    mn = im.min(axis=2).astype(int)
    mx = im.max(axis=2).astype(int)
    m = (mn > 150) & (mx - mn < 40)
    lim = int(max(0, min(FH, horizon_top - 40)))
    m[lim:] = False
    ys, xs = np.nonzero(m)
    if len(ys) < 50:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(len(ys))]


def fit_circle(x, y):
    # algebraic (Kasa) fit: x^2 + y^2 + D x + E y + F = 0
    A = np.c_[x, y, np.ones_like(x)]
    b = -(x ** 2 + y ** 2)
    (D, E, F), *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = -D / 2, -E / 2
    r = np.sqrt(cx ** 2 + cy ** 2 - F)
    res = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r
    return cx, cy, r, res


def measure(im):
    L = luma(im)
    Ls = np.stack([L[:, max(0, c - 4):c + 4].mean(axis=1) for c in COLS], axis=1)   # (FH, ncol)
    # smooth vertically a little (codec noise)
    k = np.ones(5) / 5
    Ls = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, Ls)
    hy = np.full(len(COLS), np.nan)
    peak = np.full(len(COLS), np.nan)
    ground = np.nanmedian(Ls[-40:-5], axis=0)
    for j in range(len(COLS)):
        v = Ls[:, j]
        p = int(np.argmax(v[5:-5])) + 5
        g = np.median(v[-40:-5]) if p < FH - 60 else np.nan
        if not np.isfinite(g) or v[p] - g < 25:
            continue
        half = g + 0.5 * (v[p] - g)
        below = np.nonzero(v[p:] < half)[0]
        if len(below) == 0:
            continue
        r = p + below[0]                     # first row below the peak that is darker than half
        # sub-row interpolation between r-1 (>= half) and r (< half)
        a, bb = v[r - 1], v[r]
        hy[j] = r - 1 + (a - half) / max(a - bb, 1e-6)
        peak[j] = p
    ok = np.isfinite(hy)
    out = {"n_cols": int(ok.sum())}
    out["sky_luma"] = float(L[:60, 200:1720].mean())
    if ok.sum() >= 12:
        x, y = COLS[ok].astype(float), hy[ok]
        cx, cy, r, res = fit_circle(x, y)
        keep = np.abs(res) < 3 * max(np.median(np.abs(res)), 1.0)
        cx, cy, r, res = fit_circle(x[keep], y[keep])
        y_at = lambda xx: cy - np.sqrt(np.maximum(r ** 2 - (xx - cx) ** 2, 0))
        apex_y = cy - r
        y_edges = y_at(np.array([0.0, FW]))
        sag = float(y_edges.max() - apex_y) if cy > 0 else float("nan")
        out.update(apex_x=float(cx / FW), apex_y=float(apex_y / FH), r_over_w=float(r / FW),
                   sagitta_of_width=float((max(y_edges) - apex_y) / FW) if cy > apex_y else None,
                   resid_px=float(np.sqrt(np.mean(res ** 2))), horizon_y_centre=float(y_at(960.0) / FH))
        # band profile at the centre (cols 880..1040)
        c = slice(880, 1040)
        prof = im[:, c].astype(float).mean(axis=1)        # (FH, 3)
        lp = luma(prof[None])[0]
        hc = int(round(y_at(960.0)))
        gnd = lp[min(FH - 6, hc + 40):min(FH - 1, hc + 120)]
        out["ground_luma"] = float(gnd.mean()) if len(gnd) > 5 else None
        out["ground_rgb"] = prof[min(FH - 6, hc + 40):min(FH - 1, hc + 120)].mean(axis=0).round(1).tolist() if len(gnd) > 5 else None
        up = lp[max(0, hc - 400):hc + 1]
        pk = int(np.argmax(up)) + max(0, hc - 400)
        out["peak_luma"] = float(lp[pk])
        out["peak_lin"] = float(lin(lp[pk]))
        out["peak_above_horizon_of_h"] = float((hc - pk) / FH)
        out["peak_rgb"] = prof[pk].round(1).tolist()
        # thin layer right above the horizon: rows hc-14..hc-2
        near = prof[max(0, hc - 14):max(1, hc - 2)].mean(axis=0)
        out["rim_rgb"] = near.round(1).tolist()
        out["rim_r_minus_b"] = float(near[0] - near[2])
        # the most orange row within 60 rows above the horizon
        seg = prof[max(0, hc - 60):hc + 4]
        rb = seg[:, 0] - seg[:, 2]
        out["orange_max_r_minus_b"] = float(rb.max())
        out["orange_row_above_horizon_px"] = int(min(hc + 4, FH) - max(0, hc - 60) - 1 - int(np.argmax(rb)) - 4) if len(rb) else None
        h3 = int(hc - 0.06 * FH)
        out["blue_rgb_6pc_above"] = prof[h3].round(1).tolist() if h3 >= 0 else None
        # band half-max thickness above the horizon (luma over sky + 0.5 (peak - sky))
        sky_c = lp[:40].mean()
        thr = sky_c + 0.5 * (lp[pk] - sky_c)
        j = pk
        while j > 0 and lp[j] > thr:
            j -= 1
        out["band_top_above_horizon_of_h"] = float((hc - j) / FH)
        # edge softness: 10-90 % of the rise from ground to peak, rows below the peak
        g0 = lp[min(FH - 6, hc + 40):min(FH - 1, hc + 120)].mean() if hc + 45 < FH else lp[-5:].mean()
        lo, hi = g0 + 0.1 * (lp[pk] - g0), g0 + 0.9 * (lp[pk] - g0)
        seg = lp[pk:min(FH, hc + 120)]
        i90 = np.nonzero(seg < hi)[0]
        i10 = np.nonzero(seg < lo)[0]
        out["edge_10_90_px"] = float(i10[0] - i90[0]) if len(i10) and len(i90) else None
        out["profile_centre"] = prof[::4].round(1).tolist()
        out["title"] = title_box(im, min(hy[ok]))
    else:
        out["title"] = title_box(im, FH)
        prof = im[:, 880:1040].astype(float).mean(axis=1)
        out["profile_centre"] = prof[::4].round(1).tolist()
        out["peak_luma"] = float(luma(prof[None])[0].max())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default="")
    ap.add_argument("--frames", default="")
    ap.add_argument("--out", default=os.path.join(ROOT, "out/shots/01-38-ink/measure"))
    a = ap.parse_args()
    frames = FRAMES if not a.frames else [int(f) for f in a.frames.split(",")]
    os.makedirs(a.out, exist_ok=True)
    res = {}
    if a.ours:
        for f in frames:
            p = os.path.join(a.ours, f"f{f:04d}.png")
            if os.path.exists(p):
                res[f] = measure(read_png(p))
        name = "ours.json"
    else:
        v = decode_original(frames)
        for f, im in zip(frames, v):
            res[f] = measure(im)
        np.save(os.path.join(a.out, "orig_0_499.npy"), np.stack([v[0], v[-1]]))
        name = "orig.json"
    with open(os.path.join(a.out, name), "w") as fh:
        json.dump(res, fh)
    for f in frames:
        if f not in res:
            continue
        r = res[f]
        print(f, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "profile_centre"})


if __name__ == "__main__":
    sys.exit(main())
