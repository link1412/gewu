"""Shot 38 (and 1): where is the horizon, even when it is below the frame?

Every frame's luma profile (columns 1300-1460, right of the title, title rows masked) is matched to frame 0's profile under
y0 = 540 + s (y - 540) + d (vertical scale s, shift d), least squares over the overlap (>= 120 rows). Frame 0's
horizon (measure.py) is then mapped into each frame. Also: brightness curves (mean linear luma of the frame,
the band peak), orange (max R-B in the column), title-card box.

    python3 -I shots/01-38-ink/track.py [--ours DIR]   -> out/shots/01-38-ink/measure/track[_ours].json + plots
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402

OUT = os.path.join(M.ROOT, "out/shots/01-38-ink/measure")


def centre(im):
    return im[:, 1300:1460].astype(float).mean(axis=1)


def register(l0, lf, mask, prev=None):
    """Global search on the first frame of a shot; afterwards within +-150 px / [0.85, 1.2] of the previous frame
    (fast frames in 38 are motion blurred and a global search can lock onto the wrong band)."""
    y = np.arange(M.FH, dtype=float)
    best = (np.inf, 1.0, 0.0)
    ss = np.exp(np.linspace(np.log(0.6), np.log(1.4), 81)) if prev is None else np.linspace(0.85, 1.2, 36)
    dd = np.arange(-1300, 1301, 4.0) if prev is None else np.arange(prev[1] - 150, prev[1] + 151, 2.0)
    for s in ss:
        for d in dd:
            src = 540 + s * (y - 540) + d
            ok = (src >= 0) & (src <= M.FH - 1) & mask
            if ok.sum() < 120:
                continue
            e = np.mean((np.interp(src[ok], y, l0) - lf[ok]) ** 2)
            if e < best[0]:
                best = (e, s, d)
    e, s0, d0 = best          # refine
    for s in np.linspace(s0 * 0.985, s0 * 1.015, 31):
        for d in np.arange(d0 - 6, d0 + 6.01, 0.5):
            src = 540 + s * (y - 540) + d
            ok = (src >= 0) & (src <= M.FH - 1) & mask
            if ok.sum() < 120:
                continue
            ee = np.mean((np.interp(src[ok], y, l0) - lf[ok]) ** 2)
            if ee < best[0]:
                best = (ee, s, d)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default="")
    a = ap.parse_args()
    frames = M.FRAMES
    if a.ours:
        ims = {f: M.read_png(os.path.join(a.ours, f"f{f:04d}.png")) for f in frames
               if os.path.exists(os.path.join(a.ours, f"f{f:04d}.png"))}
    else:
        v = M.decode_original(frames)
        ims = dict(zip(frames, v))
    ref = M.decode_original([0])[0]                       # always register against the ORIGINAL frame 0
    m0 = M.measure(ref)
    h0 = m0["horizon_y_centre"] * M.FH
    l0 = M.luma(centre(ref)[None])[0]
    res = {}
    kymo = []
    prev = None
    for f in sorted(ims):
        im = ims[f]
        if f - 1 not in ims:
            prev = None
        c = centre(im)
        lf = M.luma(c[None])[0]
        tb = M.title_box(im, M.FH)
        mask = np.ones(M.FH, bool)
        if tb and tb[4] > 200 and tb[3] - tb[1] < 200:
            mask[max(0, tb[1] - 20):tb[3] + 20] = False
        e, s, d = register(l0, lf, mask, prev)
        prev = (s, d)
        hy = 540 + (h0 - 540 - d) / s                    # frame-0 horizon mapped into this frame
        L = M.lin(M.luma(im[::4, ::4]))
        rb = c[:, 0] - c[:, 2]
        res[f] = dict(scale=float(s), shift=float(d), rms=float(np.sqrt(e)), horizon_y=float(hy / M.FH),
                      mean_lin=float(L.mean()), peak_luma=float(lf.max()), peak_row=int(np.argmax(lf)),
                      orange_r_minus_b=float(rb.max()), orange_row=int(np.argmax(rb)),
                      sky_luma=float(lf[:60].mean()), title=tb)
        kymo.append(c)
        print(f, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res[f].items()})
    name = "track_ours" if a.ours else "track"
    with open(os.path.join(OUT, name + ".json"), "w") as fh:
        json.dump(res, fh, indent=0)
    np.save(os.path.join(OUT, name + "_kymo.npy"), np.stack(kymo).astype(np.float32))


if __name__ == "__main__":
    sys.exit(main())
