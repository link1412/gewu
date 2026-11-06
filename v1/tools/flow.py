"""Optical flow of a moving shot, the original's and ours, to fit our motion to the original's and check it.

    python3 -I tools/flow.py measure 6                    # the original -> out/flow/06_original.npz
    python3 -I tools/flow.py measure 6 --ours out/film    # ours         -> out/flow/06_ours.npz
    python3 -I tools/flow.py compare 6                    # the two, region by region

Each block (96 px, every 48 px) is tracked between consecutive frames of the shot by phase correlation on
high-passed luma: a 6 px Gaussian is subtracted, so the texture is tracked and not a static edge (a limb's
gradient pins the estimate to zero, S2). The median over the shot's frame pairs is kept. px/frame at 1920
wide, y down. A block is dropped where it is flat (std under 1.5 grey levels after the high-pass) or where
its frame pairs disagree (median absolute deviation over 1 px/frame).
"""

import argparse
import os
import subprocess
import sys

import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.registration import phase_cross_correlation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import DECODE_VF, FH, FW, ROOT, load_spec, read_png  # noqa: E402

BLOCK, STEP = 96, 48
HIGHPASS_PX = 6.0
FLAT_STD, MAX_SPREAD = 1.5, 1.0
STILL_PX = 0.3            # under this a block is taken as still (compare, fits)
LUMA = np.array([0.2126, 0.7152, 0.0722])


def original_frames(path, first, last):
    """Frames first..last (inclusive) of the original, decoded as viewers see them."""
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf",
                          f"select=between(n\\,{first}\\,{last}),{DECODE_VF}", "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)
    if len(F) != last - first + 1:
        raise SystemExit(f"decoded {len(F)} frames, expected {last - first + 1}")
    return F


def block_flow(frames):
    """[(x, y, dx, dy, spread)] of the blocks kept, centres in px."""
    L = [f.astype(float) @ LUMA for f in frames]
    L = [f - gaussian_filter(f, HIGHPASS_PX) for f in L]
    win = np.outer(np.hanning(BLOCK), np.hanning(BLOCK))
    out = []
    for r in range(0, FH - BLOCK + 1, STEP):
        for c in range(0, FW - BLOCK + 1, STEP):
            blk = [f[r:r + BLOCK, c:c + BLOCK] for f in L]
            if np.std(blk[0]) < FLAT_STD:
                continue
            # the shift that registers frame i+1 onto frame i, negated: the motion from i to i+1
            s = -np.array([phase_cross_correlation(blk[i] * win, blk[i + 1] * win, upsample_factor=20)[0]
                           for i in range(len(blk) - 1)])
            dy, dx = np.median(s, axis=0)
            spread = np.median(np.abs(s - [dy, dx]), axis=0).max()
            if spread <= MAX_SPREAD:
                out.append((c + BLOCK / 2, r + BLOCK / 2, dx, dy, spread))
    return np.array(out)


def path_of(shot, which):
    return os.path.join(ROOT, "out", "flow", f"{shot:02d}_{which}.npz")


def cmd_measure(a, sh):
    first, last = sh["frame_in"], sh["frame_out"] - 1
    if a.ours:
        frames = [read_png(os.path.join(a.ours, f"f{f:04d}.png")) for f in range(first, last + 1)]
    else:
        frames = original_frames(a.orig, first, last)
    B = block_flow(frames)
    dst = a.out or path_of(sh["shot"], "ours" if a.ours else "original")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    np.savez(dst, x=B[:, 0], y=B[:, 1], dx=B[:, 2], dy=B[:, 3], spread=B[:, 4], frames=[first, last])
    print(f"shot {sh['shot']} frames {first}-{last}: {len(B)} blocks kept -> {dst}")


def moving(D):
    """Blocks that move: a still block is a static edge (a limb, a highlight), not the surface."""
    return np.hypot(D["dx"], D["dy"]) > STILL_PX


def cmd_compare(a, sh):
    O, U = (np.load(path_of(sh["shot"], w)) for w in ("original", "ours"))
    ys = np.quantile(np.r_[O["y"][moving(O)], U["y"][moving(U)]], [0, 1 / 3, 2 / 3, 1]) + [0, 0, 0, 1]
    print(f"shot {sh['shot']}: mean (dx, dy) px/frame of the moving blocks per region (moving / kept); "
          f"rows by tertiles")
    for r0, r1 in zip(ys[:-1], ys[1:]):
        for c0, c1 in ((0, FW / 3), (FW / 3, 2 * FW / 3), (2 * FW / 3, FW)):
            cell = []
            for D in (O, U):
                k = (D["y"] >= r0) & (D["y"] < r1) & (D["x"] >= c0) & (D["x"] < c1)
                m = k & moving(D)
                cell.append(f"({D['dx'][m].mean():+5.1f},{D['dy'][m].mean():+5.1f}) {m.sum():3d}/{k.sum():3d}" if m.any()
                            else f"{'-':>15s} {m.sum():3d}/{k.sum():3d}")
            print(f"  rows {r0:4.0f}-{r1:4.0f} cols {c0:4.0f}-{c1:4.0f}: original {cell[0]}   ours {cell[1]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["measure", "compare"])
    ap.add_argument("shot", type=int)
    ap.add_argument("--ours", help="our frames (fNNNN.png, global numbering); without it, the original")
    ap.add_argument("--orig", default=os.path.join(ROOT, "ref/opus55.mp4"))
    ap.add_argument("--out")
    a = ap.parse_args()
    sh = next(s for s in load_spec()["shots"] if s["shot"] == a.shot)
    if not sh["motion"]["moves"]:
        raise SystemExit(f"shot {a.shot} does not move (spec)")
    {"measure": cmd_measure, "compare": cmd_compare}[a.cmd](a, sh)


if __name__ == "__main__":
    main()
