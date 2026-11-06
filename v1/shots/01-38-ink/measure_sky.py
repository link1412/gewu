"""Round 2 target: the original's sky above the bleed, as one radiance-vs-height curve in frame-0 coordinates.

    python3 -I shots/01-38-ink/measure_sky.py   -> out/shots/01-38-ink/r2/targets.json, sky_curve.png, orig_profiles.npz

Decode: BT.709 matrix, tv range (measure.decode_original, same as tools/compare.py). All code values are that decode.
Per frame 0 and 399-499: the top-60-row sky (mean RGB and luma, r1's definition; title pixels masked when the
card reaches the top 100 rows) and three column-band profiles (columns 200-360, 880-1040, 1560-1720 at 1920, every row;
title rows masked in the band they touch). Each frame's rows are mapped into frame-0 rows with the measured,
Savitzky-Golay-smoothed tilt track (track.py; render.py uses the same poses): y0 = 540 + s (y - 540) + d.
Height above the horizon is (511 - y0) / 1080 at the centre (frame-0 horizon apex 0.4728 H).

Fit / held-out split (round 2): the fit uses frames 0, 420, 470 only. Frames 456 and 485 are held out; so is every
other frame (they are reported in the curve but no fit residual uses them).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402
import render as RD  # noqa: E402

OUT = os.path.join(M.ROOT, "out/shots/01-38-ink/r2")
BANDS = [(200, 360), (880, 1040), (1560, 1720)]
FIT = [0, 420, 470]
HELD = [456, 485]
H0 = 0.4728 * M.FH


def title_mask(im):
    """(rows, cols) of white unsaturated type, dilated 24 px (the cards are plain white, no glow)."""
    mn = im.min(axis=2).astype(int)
    mx = im.max(axis=2).astype(int)
    m = (mn > 150) & (mx - mn < 40)
    from scipy import ndimage
    if m.sum() < 50:
        return np.zeros_like(m)
    return ndimage.binary_dilation(m, iterations=24)


def frame_measure(im):
    tm = title_mask(im)
    imf = im.astype(float)
    top = imf[:60][~tm[:60]]
    sky_rgb = top.mean(axis=0)
    prof, valid = [], []
    for c0, c1 in BANDS:
        blk = imf[:, c0:c1]
        mk = tm[:, c0:c1].any(axis=1)
        prof.append(blk.mean(axis=1))
        valid.append(~mk)
    return dict(sky_rgb=sky_rgb, sky_luma=float(M.luma(sky_rgb[None])[0]), prof=np.stack(prof), valid=np.stack(valid))


def main():
    os.makedirs(OUT, exist_ok=True)
    frames = [0] + list(range(399, 500))
    track = {int(k): v for k, v in json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/track.json"))).items()}
    pose = RD.smooth_track(track, sorted(track))
    res = {}
    profs, valids = {}, {}
    for i0 in range(0, len(frames), 20):
        chunk = frames[i0:i0 + 20]
        for f, im in zip(chunk, M.decode_original(chunk)):
            m = frame_measure(im)
            profs[f], valids[f] = m["prof"], m["valid"]
            s, d = pose[f]
            res[f] = dict(sky_rgb=[round(float(x), 2) for x in m["sky_rgb"]], sky_luma=round(m["sky_luma"], 2),
                          scale=s, shift=d,
                          top_row_in_frame0=round(540 + s * (30 - 540) + d, 1),
                          top_height_H=round((H0 - (540 + s * (30 - 540) + d)) / M.FH, 3))
        print("decoded", chunk[-1], flush=True)
    np.savez_compressed(os.path.join(OUT, "orig_profiles.npz"), frames=np.array(frames),
                        prof=np.stack([profs[f] for f in frames]).astype(np.float32),
                        valid=np.stack([valids[f] for f in frames]))

    # one curve: frame-0 row -> RGB (per band), medians over frames, 8-px bins
    edges = np.arange(-1000, 1081, 8)
    y = np.arange(M.FH, dtype=float)

    def curve(sel):
        acc = [[[] for _ in range(len(edges) - 1)] for _ in BANDS]
        for f in sel:
            s, d = pose[f]
            y0 = 540 + s * (y - 540) + d
            b = np.digitize(y0, edges) - 1
            for k in range(len(BANDS)):
                for bi in np.unique(b[(b >= 0) & (b < len(edges) - 1)]):
                    rows = (b == bi) & valids[f][k]
                    if rows.any():
                        acc[k][bi].append(profs[f][k][rows].mean(axis=0))
        out = np.full((len(BANDS), len(edges) - 1, 3), np.nan)
        n = np.zeros((len(BANDS), len(edges) - 1), int)
        for k in range(len(BANDS)):
            for bi in range(len(edges) - 1):
                if acc[k][bi]:
                    out[k, bi] = np.median(np.array(acc[k][bi]), axis=0)
                    n[k, bi] = len(acc[k][bi])
        return out, n

    allf = [f for f in frames]
    c_all, n_all = curve(allf)
    c_fit, n_fit = curve(FIT)
    mid = (edges[:-1] + edges[1:]) / 2
    # spread across frames at a given frame-0 row: tests "the light does not change" (one curve for all frames)
    spread = []
    for bi in range(len(mid)):
        vals = []
        for f in frames:
            s, d = pose[f]
            y0 = 540 + s * (y - 540) + d
            rows = (y0 >= edges[bi]) & (y0 < edges[bi + 1]) & valids[f][1]
            if rows.any():
                vals.append(M.luma(profs[f][1][rows].mean(axis=0)[None])[0])
        spread.append(float(np.std(vals)) if len(vals) > 3 else None)

    tj = dict(
        _doc=__doc__.strip(),
        decode="bt709 matrix, tv range (scale=in_color_matrix=bt709:in_range=tv), rgb24 codes",
        bands_px_1920=BANDS, fit_frames=FIT, held_out_frames=HELD,
        horizon_row_frame0=H0,
        per_frame={str(f): v for f, v in res.items()},
        curve=dict(frame0_row=mid.tolist(), height_H=((H0 - mid) / M.FH).round(4).tolist(),
                   rgb_all_frames=[[None if np.isnan(v[0]) else [round(float(x), 2) for x in v] for v in c_all[k]] for k in range(3)],
                   n_frames=n_all.tolist(),
                   rgb_fit_frames=[[None if np.isnan(v[0]) else [round(float(x), 2) for x in v] for v in c_fit[k]] for k in range(3)],
                   luma_spread_across_frames_centre=spread),
    )
    with open(os.path.join(OUT, "targets.json"), "w") as fh:
        json.dump(tj, fh, indent=0)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    hH = (H0 - mid) / M.FH
    for k, ls in zip(range(3), ("-", "--", ":")):
        for c, col in enumerate("rgb"):
            ax[0].plot(hH, c_all[k, :, c], col + ls, lw=1.2)
    ax[0].set_xlabel("height above the horizon (frame-0 H); solid centre band, dashed left, dotted right")
    ax[0].set_ylabel("code (bt709 tv)")
    ax[0].set_title("original: one curve from frames 0 + 399-499 (median)")
    ff = [0] + list(range(399, 500))
    ax[1].plot(ff[1:], [res[f]["sky_luma"] for f in ff[1:]], "k-")
    for c, col in enumerate("rgb"):
        ax[1].plot(ff[1:], [res[f]["sky_rgb"][c] for f in ff[1:]], col + "-", lw=0.8)
    ax[1].set_xlabel("frame"); ax[1].set_title("top-60 sky (luma black, RGB)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "sky_curve.png"), dpi=80)
    for f in [0, 399, 420, 440, 456, 460, 470, 480, 485, 490, 495, 499]:
        print(f, res[f])


if __name__ == "__main__":
    main()
