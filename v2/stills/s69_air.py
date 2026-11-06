"""Heat shimmer over the burning heap, on the take's scene-linear frames. NOT IN THE PIPELINE: at the bending estimated below it does not show (mean change 0.05 of 255, an out-of-focus row moving under a pixel), and made strong enough to show it is a warp that nothing in the frame asks for. Kept to try: out/v2/s69_mutan_take_cand/take_shimmer3x.mp4 is this at a gain of 3.

    python3 -I v2/stills/s69_air.py IN OUT [gain]

The picture is displaced by vertically stretched noise carried upward over the glow, as hot air bends what is seen through it. IN holds take.linear_###.npy and develop.json. Writing OUT = s69_mutan_move_final would put it in the film: keep the frames without it.
"""

import os
import shutil
import sys

import cv2
import numpy as np

W, H = 1920, 1080
# Bending, as an estimate (not measured, not looked up): n-1 falls from 2.7e-4 in room air to about 1e-4 at 800 K, so Dn is about 2e-4 across a plume's edge, a few mm wide: up to about 1e-3 rad along some cm of it. That is about 1 px for what lies 10 cm behind the plume (0.01 cm at 111 px/cm), 1-2 px for the back row. RMS_X is at the top of that range; what is in focus lies near the front and gets a quarter of it (see the mask).
RMS_X, RMS_Y = 0.9, 0.3  # px
# Real plumes move about 130-400 px per frame here, which would be a frame-to-frame jitter: carried up slowly instead.
EDDIES = [(7300, 26.0, 74.0, 5.0, 0.8), (7301, 10.0, 30.0, 8.0, 0.45)]  # seed, sigma x, sigma y in px, px/frame upward, weight
GLOW_R = 0.4  # linear R above which a part of the picture heats the air over it


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Shimmer:
    def __init__(self, first, n, gain=1.0):
        """The mask from the first frame: only a fixed place heats the air in 1.4 s."""
        glow = sstep(GLOW_R * 0.5, GLOW_R * 2.0, first[..., 0])
        glow = cv2.GaussianBlur(glow, (0, 0), 70.0)
        # what is above a hot place is seen through its plume: a one-sided kernel, the image's rows run downward so that the weight spreads to smaller y
        L0 = 260
        ker = np.exp(-np.arange(L0, dtype=np.float32) / 110.0)[:, None]
        ker = np.vstack([np.zeros((L0 - 1, 1), np.float32), ker])[::-1] / ker.sum()
        rise = cv2.filter2D(glow, -1, ker, borderType=cv2.BORDER_REPLICATE)
        m = np.clip(rise * 3.5, 0.0, 1.0)
        # what is sharp is near the plane of focus, near the front: little hot air lies before it
        lum = np.log(first[..., 0] + 0.02)
        sharp = cv2.GaussianBlur(np.abs(lum - cv2.GaussianBlur(lum, (0, 0), 3.0)), (0, 0), 25.0)
        m = m * (1.0 - 0.75 * sstep(0.03, 0.09, sharp))
        yy = (np.arange(H, dtype=np.float32) + 0.5) / H
        # none where the frame is plain, least over the front row, which little hot air lies in front of
        self.mask = (m * (sstep(0.3, 0.44, yy) * (0.3 + 0.7 * sstep(1.0, 0.68, yy)))[:, None]).astype(np.float32)
        self.Y, self.X = np.mgrid[0:H, 0:W].astype(np.float32)
        self.fields = []
        for seed, sx, sy, v, wt in EDDIES:
            rng = np.random.default_rng(seed)
            rows = H + int(v * n) + 8
            a = cv2.GaussianBlur(rng.standard_normal((rows, W, 2)).astype(np.float32), (0, 0), sigmaX=sx, sigmaY=sy, borderType=cv2.BORDER_REFLECT)
            a /= a.std(axis=(0, 1))
            self.fields.append((a, v, wt))
        tot = np.sqrt(sum(w * w for _, _, w in self.fields))
        self.scale = gain * np.array([RMS_X, RMS_Y], np.float32) / tot

    def displacement(self, k):
        out = np.zeros((H, W, 2), np.float32)
        for a, v, wt in self.fields:
            s = v * k
            i = int(np.floor(s))
            f = s - i
            out += wt * ((1.0 - f) * a[i : i + H] + f * a[i + 1 : i + 1 + H])
        return (out * self.scale * self.mask[..., None]).astype(np.float32)

    def apply(self, L, k):
        d = self.displacement(k)
        return np.maximum(cv2.remap(L, self.X + d[..., 0], self.Y + d[..., 1], cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE), 0.0)


def main():
    src, out = sys.argv[1], sys.argv[2]
    gain = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    names = sorted(x for x in os.listdir(src) if x.startswith("take.linear_") and x.endswith(".npy"))
    if not names:
        raise SystemExit(f"no frames in {src}")
    os.makedirs(out, exist_ok=True)
    sh = Shimmer(np.load(os.path.join(src, names[0])).astype(np.float32), len(names), gain)
    d = sh.displacement(len(names) // 2)
    print(f"displacement: max {np.hypot(d[..., 0], d[..., 1]).max():.2f} px", flush=True)
    for k, name in enumerate(names):
        L = sh.apply(np.load(os.path.join(src, name)).astype(np.float32), k)
        if not np.isfinite(L).all():
            raise SystemExit(f"frame {k}: not finite")
        tmp = os.path.join(out, name + ".tmp.npy")
        np.save(tmp, L.astype(np.float16))
        os.replace(tmp, os.path.join(out, name))
    shutil.copy(os.path.join(src, "develop.json"), os.path.join(out, "develop.json"))


if __name__ == "__main__":
    main()
