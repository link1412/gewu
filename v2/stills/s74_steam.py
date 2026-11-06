"""Shot 74's steam: added to the scene-linear image behind the ball, before developing. No render, no GPU.

    python3 -I v2/stills/s74_steam.py IN.linear.npy OUT.jpg ['{"k": v}']

Steam from a hot ball in a dark room, lit from behind. A continuous density, not points: each pixel is traced backwards through a slowly changing divergence-free flow (a stream function of band-limited noise at three scales, carried upward), and collects whatever a thin band along the ball's outline (where the shot put it, frame.json) released on its way. A divergence-free flow stretches that into sheets, which is what the eye reads as wisps. Bands of age are blurred by how long they have spread. It adds light, as a thin scattering medium in front of a dark wall does; absorption of what lies behind is neglected, since what lies behind is nearly black.

This is a kinematic stand-in, not a solved plume: there is no buoyancy feedback, the rise is constant, and all the numbers are by eye. The density depends only on (seed, time), so frames of a moving shot stay coherent.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "v2"))

import cv2
import numpy as np

import kit
from darkroom import develop

P0 = {
    "seed": 74, "T": 3.2, "rise": 0.15, "swirl": [0.13, 0.09, 0.05], "life": 3.0, "da": 0.05,
    "gain": 0.7, "rgb": [1.0, 0.92, 0.8], "blur0": 1.2, "blur1": 10.0,
    "cx": [0.5, 0.62, 0.32, 0.72], "cw": [0.035, 0.05, 0.04, 0.03], "band": 0.014, "front": 0.12,
}
DEV = {"exposure": 0.12, "wb": [1.03, 1.0, 0.95], "contrast": 1.3, "saturation": 1.05, "black": 0.002, "grain": 1.0, "sharpen": 0.2, "halation": 0.06, "vignette": 0.2}
GW, GH = 960, 540  # the steam's own grid: it is soft, and sits out of focus


def outline(frame):
    """Per column, the fraction of height where the ball's top is; and a mask of the ball, from where the shot put it (frame.json), not from the picture."""
    x = (np.arange(GW, dtype=np.float32) + 0.5) / GW
    dy = np.sqrt(np.maximum(frame["r"] ** 2 - (x - frame["cx"]) ** 2, 0.0)) * GW / GH
    top = np.where(np.abs(x - frame["cx"]) < frame["r"], frame["cy"] - dy, 1.0).astype(np.float32)
    jj, ii = np.meshgrid(x, (np.arange(GH, dtype=np.float32) + 0.5) / GH)
    m = (np.hypot(jj - frame["cx"], (ii - frame["cy"]) * GH / GW) < frame["r"]).astype(np.uint8)
    return top, m


def steam(top, p, t_end):
    """Density on the steam grid at time t_end. x in frame widths, y in frame widths up from the bottom."""
    n = 1024
    aspect = GH / GW
    grads = []
    for s in (p["seed"] + 1, p["seed"] + 11):
        per = []
        for i, (lo, hi) in enumerate(((160.0, 500.0), (50.0, 150.0), (16.0, 46.0))):
            f = kit.fbm((n, n), 1.0, lo, hi, 3.0, s + i).astype(np.float32)
            gx = np.roll(f, -1, 1) - np.roll(f, 1, 1)
            gy = np.roll(f, -1, 0) - np.roll(f, 1, 0)
            k = 1.0 / (np.sqrt((gx**2 + gy**2).mean()) + 1e-9)  # unit rms speed, so `swirl` is a speed
            per.append((gx * k, gy * k))
        grads.append(per)
    tiles, ups = (0.9, 0.42, 0.16), (0.05, 0.1, 0.16)

    def vel(x, y, t):
        vx, vy = np.zeros_like(x), np.zeros_like(y)
        w = 0.5 + 0.5 * np.cos(t * 0.45)  # one field fades into the other, slowly
        for i, amp in enumerate(p["swirl"]):
            u = ((x / tiles[i]) % 1.0 * n).astype(np.float32)
            v = (((y - ups[i] * t) / tiles[i]) % 1.0 * n).astype(np.float32)
            for per, wt in ((grads[0], w), (grads[1], 1.0 - w)):
                gx, gy = per[i]
                vx += amp * wt * cv2.remap(gy, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
                vy -= amp * wt * cv2.remap(gx, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        return vx, vy

    rng = np.random.default_rng(p["seed"])
    cx, cw = np.array(p["cx"], np.float32), np.array(p["cw"], np.float32)
    cs = rng.uniform(0.0, 6.28, len(cx)).astype(np.float32)
    y_top = (1.0 - top) * aspect
    x_axis = (np.arange(GW, dtype=np.float32) + 0.5) / GW

    def source(x, y, t):
        along = np.zeros_like(x)
        for c, w, ph in zip(cx, cw, cs):
            swell = 0.55 + 0.45 * np.sin(ph + 0.7 * t)
            cc = c + 0.015 * np.sin(ph + 0.4 * t)
            along += swell * np.exp(-(((x - cc) / w) ** 2))
        yt = np.interp(x.ravel(), x_axis, y_top).reshape(x.shape).astype(np.float32)
        return along * np.exp(-(((y - yt - 0.006) / p["band"]) ** 2))

    jj, ii = np.meshgrid(np.arange(GW, dtype=np.float32), np.arange(GH, dtype=np.float32))
    X = (jj + 0.5) / GW
    Y = (GH - ii - 0.5) / GW
    da = p["da"]
    steps = int(p["life"] / da)
    bands = 6
    per_band = max(1, steps // bands)
    D_ = np.zeros((GH, GW), np.float32)
    acc = np.zeros((GH, GW), np.float32)
    for s in range(steps):
        a = (s + 0.5) * da
        t = t_end - a
        acc += source(X, Y, t) * np.exp(-a / (0.55 * p["life"])) * da
        vx, vy = vel(X, Y, t)
        X = X - da * vx
        Y = Y - da * (vy + p["rise"])
        if (s + 1) % per_band == 0 or s == steps - 1:
            frac = (s + 1) / steps
            D_ += cv2.GaussianBlur(acc, (0, 0), p["blur0"] + (p["blur1"] - p["blur0"]) * frac)
            acc[:] = 0.0
    return D_


def add_steam(L, p, frame, t=None):
    H, W = L.shape[:2]
    top, m = outline(frame)
    d = steam(top, p, p["T"] if t is None else t) * p["gain"]
    # behind the ball: the matte, softened by the lens
    behind = 1.0 - cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)
    d = cv2.resize(d * (behind + p["front"] * (1.0 - behind)), (W, H), interpolation=cv2.INTER_CUBIC)
    print(f"[steam] density max {d.max():.3f}", flush=True)
    return L + np.maximum(d, 0.0)[..., None] * np.array(p["rgb"], np.float32)


if __name__ == "__main__":
    p = dict(P0)
    if len(sys.argv) > 3:
        p.update(json.loads(sys.argv[3]))
    L = np.load(sys.argv[1]).astype(np.float32)
    with open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "frame.json")) as f:
        frame = json.load(f)
    im = develop(add_steam(L, p, frame), **DEV)
    cv2.imwrite(sys.argv[2], (np.clip(im, 0, 1) * 255.0 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 95])
    print("wrote", sys.argv[2])
