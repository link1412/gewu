"""Render shots 1 and 38 (preview): the camera follows the original's measured framing, frame by frame.

    python3 -I shots/01-38-ink/render.py [--maps out/shots/01-38-ink/sim/maps.npz] [--frames 0-30,399-499]
                                          [--res 960] [--out out/shots/01-38-ink/r1/frames]
    -> OUT/fNNNN.png (global frame numbers, sRGB 8-bit, or 16-bit with --bits 16; tools/compare.py scales them to 1920x1080)

The camera of frame 0 is fitted (fit.py -> optics.json). Every other frame applies the original's measured
vertical framing (track.py: frame f row y shows frame-0 row 540 + s (y - 540) + d) as a zoom (f_px / s) and a tilt
(atan(-d / f_px)), smoothed (Savitzky-Golay, 7 frames). Both shots are the same pool and the same light: shot 38 ends where
shot 1 begins (the original does the same, measured: frame 499 = frame 0 at scale 0.98, 8 px). Horizontal drift is
not applied yet. Frames whose pose differs from the last rendered one by < 1 px (at 1080; the original holds still there) are copied, not re-rendered.
"""
import argparse
import copy
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402
import optics as op  # noqa: E402


def write_png16(path, rgb01):
    """16-bit RGB PNG through ffmpeg (PIL cannot write 16-bit RGB)."""
    import subprocess
    H, W = rgb01.shape[:2]
    raw = (np.clip(rgb01, 0, 1) * 65535 + 0.5).astype(">u2").tobytes()
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48be",
                    "-s", f"{W}x{H}", "-i", "-", "-pix_fmt", "rgb48be", path], input=raw, check=True)


def frame_list(spec):
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def smooth_track(track, frames):
    """Savitzky-Golay (7 frames, quadratic) within each contiguous run: removes the registration noise (+-1-2 px)
    without lagging the fast end of 38 (a plain 5-frame mean truncated at the run's end put frame 499 19 px off)."""
    from scipy.signal import savgol_filter
    out = {}
    runs, cur = [], [frames[0]]
    for f in frames[1:]:
        if f == cur[-1] + 1:
            cur.append(f)
        else:
            runs.append(cur)
            cur = [f]
    runs.append(cur)
    for r in runs:
        s = np.array([track[f]["scale"] for f in r])
        d = np.array([track[f]["shift"] for f in r])
        if len(r) >= 7:
            s, d = savgol_filter(s, 7, 2, mode="interp"), savgol_filter(d, 7, 2, mode="interp")
        for f, a, b in zip(r, s, d):
            out[f] = (float(a), float(b))
    return out


def pose_camera(C0, s, d):
    """Frame-0 camera C0 moved to the measured pose (scale s, shift d at 1080): zoom f_px / s, tilt atan(-d / f_px)."""
    C = copy.deepcopy(C0)
    C["f_px"] = C0["f_px"] / s
    C["pitch_deg"] = C0.get("pitch_deg", 0.0) + float(np.degrees(np.arctan(-d / C0["f_px"])))
    return C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", default=os.path.join(M.ROOT, "out/shots/01-38-ink/sim/maps.npz"))
    ap.add_argument("--frames", default="0-30,399-499")
    ap.add_argument("--res", type=int, default=960)
    ap.add_argument("--bits", type=int, default=8, choices=(8, 16))
    ap.add_argument("--out", default=os.path.join(M.ROOT, "out/shots/01-38-ink/r1/frames"))
    a = ap.parse_args()
    P = json.load(open(os.path.join(HERE, "params.json")))
    O = json.load(open(os.path.join(HERE, "optics.json")))
    track = {int(k): v for k, v in json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/track.json"))).items()}
    frames = frame_list(a.frames)
    pose = smooth_track(track, sorted(track))
    sheet = op.Sheet(a.maps, P)
    os.makedirs(a.out, exist_ok=True)
    W, H = a.res, a.res * 9 // 16
    C0 = O["camera"]
    last = None
    log = {}
    for f in frames:
        s, d = pose[f]
        C = pose_camera(C0, s, d)
        path = os.path.join(a.out, f"f{f:04d}.png")
        if last is not None and abs(last[1] - d) < 1.0 and abs(last[0] - s) * 960 < 1.0:
            shutil.copyfile(last[2], path)
            log[f] = dict(scale=s, shift=d, copied_from=os.path.basename(last[2]))
            continue
        img = op.render(sheet, O, C, W, H)
        if a.bits == 16:   # 16-bit RGB PNG (round 2: the film wants rgb48 sources)
            write_png16(path, op.to_display(img))
        else:
            Image.fromarray((op.to_display(img) * 255 + 0.5).astype(np.uint8)).save(path)
        last = (s, d, path)
        log[f] = dict(scale=s, shift=d, f_px=C["f_px"], pitch_deg=C["pitch_deg"])
        print(f, f"s {s:.4f} d {d:.1f}", flush=True)
    with open(os.path.join(a.out, "poses.json"), "w") as fh:
        json.dump(log, fh, indent=0)


if __name__ == "__main__":
    main()
