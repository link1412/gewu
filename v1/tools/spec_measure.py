"""Measure the Opus 5.5 launch film shot by shot -> spec/shots.json.

Everything our film has to match is read off the original here, not eyeballed:
cut frames, where each shot's arc sits and how curved it is, how bright the sky
above the arc is (decides white or black caption), whether the shot moves, and
how much detail it carries (tools/sharpness.py: cutoff, grain, render width).

    python3 -I tools/spec_measure.py ref/opus55.mp4 spec/shots.json

The video stays in ref/ (not in git; it is Anthropic's film).
"""

import json
import os
import subprocess
import sys

import numpy as np

FPS = 25
W, H = 480, 270  # analysis size; ratios are reported, so the size only sets precision

# Captions, read by eye from the frames (S1). Shot numbers are 1-based.
TEXT = {**{s: "There's" for s in range(15, 20)},
        **{s: "more to" for s in range(20, 25)},
        **{s: "discover" for s in range(25, 38)}}
# Shots whose arc the automatic fit does not find (lines, sketches, the end card);
# their arcs get measured by hand when we match them.
MANUAL_ARC = {7: "blueprint lines win over the arc", 8: "rotating negative sphere, fit unstable mid-shot",
              14: "animated horse legs cross the arc", 26: "crayon bands win over the arc",
              30: "wood grain under the arc", 33: "object sits at the bottom edge",
              35: "pen hatching", 38: "end card, the limb is at the bottom"}


def decode(path, w, h):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def find_cuts(v):
    """Hard cuts: frames whose colour histogram jumps far more than their neighbours'."""
    def hist(f):
        q = (f // 32).astype(int)
        return np.bincount((q[..., 0] * 64 + q[..., 1] * 8 + q[..., 2]).ravel(), minlength=512) / q[..., 0].size
    hs = np.array([hist(f) for f in v])
    d = np.r_[0, 0.5 * np.abs(np.diff(hs, axis=0)).sum(1)]          # total-variation distance, 0..1
    cuts = [0]
    for i in range(1, len(d)):
        local = np.median(d[max(1, i - 6):i + 7])
        if d[i] > 0.25 and d[i] > 3 * local and i - cuts[-1] > 2:
            cuts.append(i)
    return cuts, d


def fit_arc(im):
    """Robust quadratic through the strongest region boundary in each column (y down)."""
    k = 12
    cs = np.cumsum(np.vstack([np.zeros((1, W, 3)), im]), axis=0)
    ys = np.arange(int(0.30 * H), int(0.88 * H))
    step = np.linalg.norm((cs[ys] - cs[ys - k]) / k - (cs[ys + k] - cs[ys]) / k, axis=2)
    xs = np.arange(8, W - 8, 3)
    ey = ys[np.argmax(step[:, xs], axis=0)].astype(float)
    st = step[:, xs].max(0)
    keep = st > 0.25 * np.median(st) + 1
    x, y = xs[keep].astype(float), ey[keep]
    for _ in range(4):
        p = np.polyfit(x, y, 2)
        r = np.abs(np.polyval(p, x) - y)
        m = r < 3 * (np.median(r) + 0.5)
        x, y = x[m], y[m]
    a, b, c = p
    xv = -b / (2 * a)
    yv = np.polyval(p, xv)
    sag = ((np.polyval(p, 0) + np.polyval(p, W)) / 2 - yv) / W
    resid = float(np.median(np.abs(np.polyval(p, x) - y)))
    return p, xv / W, yv / H, sag, len(x) / len(xs), resid


def phase_shift(a, b, win):
    A = np.fft.fft2((a - a.mean()) * win)
    B = np.fft.fft2((b - b.mean()) * win)
    R = A.conj() * B
    R /= np.abs(R) + 1e-6
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    h, w = a.shape
    return (x - w if x > w // 2 else x), (y - h if y > h // 2 else y)


def motion(g, f0, f1):
    """Global drift (px at W) and zoom between the first and last interior frames, plus what is left."""
    h, w = g.shape[1:]
    win = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    mask = np.ones((h, w), bool)
    mask[int(0.28 * h):int(0.48 * h), int(0.25 * w):int(0.75 * w)] = False   # caption zone
    a, b = g[f0], g[f1]
    dx, dy = phase_shift(a, b, win)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    best_s, best_r = 1.0, np.inf
    for s in np.linspace(0.90, 1.10, 41):
        ys = np.clip(((yy - h / 2) / s + h / 2).astype(int), 0, h - 1)
        xs = np.clip(((xx - w / 2) / s + w / 2).astype(int), 0, w - 1)
        r = np.abs(b[ys, xs] - a)[mask].mean()
        if r < best_r:
            best_s, best_r = s, r
    bs = np.roll(np.roll(b, -dy, 0), -dx, 1)
    resid = float(np.abs(bs - a)[mask].mean())
    per_frame = float(np.mean([np.abs(g[k] - g[k - 1])[mask].mean() for k in range(f0 + 1, f1 + 1)]))
    return dx * W / w, dy * W / w, best_s, resid, per_frame


def main(src, dst):
    v = decode(src, W, H)
    n = len(v)
    cuts, _ = find_cuts(v)
    bounds = cuts + [n]
    gray = decode(src, 320, 180) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    shots = []
    for i in range(len(cuts)):
        f0, f1 = bounds[i], bounds[i + 1]
        s = i + 1
        mid = v[(f0 + f1) // 2]
        p, ax, ay, sag, inl, res = fit_arc(mid)
        yy, xx = np.mgrid[0:H, 0:W]
        arc = np.polyval(p, xx)
        lum = mid @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        sky = lum[(yy < arc - 8) & (yy > 0.05 * H)]
        obj = mid[yy > arc + 8]
        dx, dy, zoom, mres, mpf = motion(gray, f0 + 1, f1 - 1) if f1 - f0 > 3 else (0, 0, 1, 0, 0)
        moves = abs(dx) + abs(dy) >= 3 or abs(zoom - 1) >= 0.01 or mres > 4.0
        shots.append({
            "shot": s, "frame_in": f0, "frame_out": f1, "seconds": round((f1 - f0) / FPS, 2),
            "arc": None if s in MANUAL_ARC else {
                "apex_x": round(float(ax), 3), "apex_y": round(float(ay), 3),
                "sagitta_of_width": round(float(sag), 4),
                "radius_over_width": round(float(1 / (8 * sag)), 2) if sag > 0 else None,
                "fit_inliers": round(float(inl), 2), "fit_resid_px_at_480": round(res, 1)},
            "arc_manual_reason": MANUAL_ARC.get(s),
            "sky_luma": round(float(sky.mean()), 1) if sky.size else None,
            "object_rgb": [int(c) for c in obj.mean(0)] if obj.size else None,
            "motion": {"moves": bool(moves), "drift_px_at_480": [round(float(dx), 1), round(float(dy), 1)],
                       "zoom": round(float(zoom), 3), "residual": round(mres, 1), "mean_abs_diff_per_frame": round(mpf, 2)},
            "caption": TEXT.get(s, "Opus 5.5 / Claude" if s == len(cuts) else ""),
        })
    out = {
        "source": "Claude Opus 5.5 launch film, x.com/claudeai/status/2102435511222890900 (2026-09-22), 1920x1080 h264, 25 fps",
        "frames": n, "fps": FPS,
        "notes": ["arc: y measured downward; apex_x/apex_y are fractions of width/height; "
                  "sagitta = drop from apex to the frame edges, as a fraction of the width",
                  "motion: compares the first and last frame inside the shot; zoom > 1 means the camera pushes in",
                  "caption beats were read by eye; everything else is computed by this script"],
        "shots": shots,
    }
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sharpness  # per-shot detail cutoff, grain, render width (tools/sharpness.py)
    sharpness.add(out, src)
    with open(dst, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{n} frames, {len(cuts)} shots, cuts at frames {cuts[1:]}")
    for sh in shots:
        a = sh["arc"]
        arc = f"apex ({a['apex_x']:.2f},{a['apex_y']:.2f}) sag {100 * a['sagitta_of_width']:4.1f}%" if a else f"manual: {sh['arc_manual_reason']}"
        m = sh["motion"]
        mv = f"moves drift={m['drift_px_at_480']} zoom={m['zoom']}" if m["moves"] else "still"
        print(f"{sh['shot']:>2} {sh['frame_in']:>3}-{sh['frame_out']:<3} {sh['seconds']:>4}s  {arc:<38} sky {sh['sky_luma']!s:>5}  {mv:<36} {sh['caption']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
