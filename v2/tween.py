"""Frames between rendered frames, for the film's slower clock (SLOW in film.py). Classical optical flow, OpenCV's DIS: no model, nothing learned from pictures.

The takes were rendered for 25 fps. Shown slower, most frames of the film fall between two rendered ones, so each is warped from both neighbours towards its moment and blended.
Where the two warped pictures disagree the flow has failed (a spark that travels further than its own size, something uncovered), and there the nearer rendered frame is used alone: a part held for a frame shows less than a double image.

Tween(load, n).at(pos): load(j) gives rendered frame j as float32 RGB, pos is a float in rendered frames. A pos on a rendered frame returns that frame untouched.
ESTIMATED, set by looking at test shots: FLOW_W, CRISP, BLEND, AGREE.
"""

import cv2
import numpy as np

FLOW_W = 960  # width the flow is measured at: enough for a petal's edge, and baked grain averages away
CRISP = 0.45  # how much is put back, per unit of distance from the nearer rendered frame; fitted to the peacock's barbs
BLEND = (0.3, 0.7)  # where in the gap the hand-over from one rendered frame to the next happens: blending all the way softens every frame that is not near a rendered one, and the softness comes and goes
AGREE = (0.05, 0.14)  # disagreement between the two warped pictures, display brightness 0 to 1: below the first blend, above the second use the nearer frame


def sstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


class Tween:
    def __init__(self, load, n, linear=True):
        self.load, self.n, self.linear = load, n, linear
        self.frames, self.pair = {}, None
        self.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)

    def frame(self, j):
        if j not in self.frames:
            self.frames = {k: v for k, v in self.frames.items() if k >= j - 1}  # the clock only runs forward
            self.frames[j] = self.load(j)
        return self.frames[j]

    def gray(self, img, scale=None):
        """Small display-like brightness as bytes, the same scale for both frames of a pair."""
        h, w = img.shape[:2]
        y = cv2.resize(img, (FLOW_W, round(h * FLOW_W / w)), interpolation=cv2.INTER_AREA) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        y = np.maximum(y, 0.0)
        if self.linear:
            y = y ** (1 / 2.2)
        scale = scale or max(float(np.percentile(y, 99.8)), 1e-3)
        return (np.clip(y / scale, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), scale

    def flows(self, j):
        if self.pair is None or self.pair[0] != j:
            ga, s = self.gray(self.frame(j))
            gb, _ = self.gray(self.frame(j + 1), s)
            self.pair = (j, ga, gb, self.dis.calc(ga, gb, None), self.dis.calc(gb, ga, None))
        return self.pair[1:]

    def at(self, pos):
        pos = min(max(pos, 0.0), self.n - 1.0)
        j = int(pos)
        t = pos - j
        if t < 1e-3 or j + 1 >= self.n:
            return self.frame(j).copy()
        ga, gb, fab, fba = self.flows(j)
        h, w = self.frame(j).shape[:2]
        gh, gw = ga.shape
        gx, gy = np.meshgrid(np.arange(gw, dtype=np.float32), np.arange(gh, dtype=np.float32))
        # where the two warped pictures disagree, measured small
        wa = cv2.remap(ga, gx + t * fba[..., 0], gy + t * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        wb = cv2.remap(gb, gx + (1 - t) * fab[..., 0], gy + (1 - t) * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        bad = sstep(*AGREE, cv2.GaussianBlur(np.abs(wa.astype(np.float32) - wb.astype(np.float32)) / 255.0, (0, 0), 1.5))
        weight = float(sstep(*BLEND, t)) * (1.0 - bad) + (1.0 if t >= 0.5 else 0.0) * bad
        weight = cv2.resize(weight, (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
        # the warps, full size
        k = w / gw
        X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        Fa = cv2.resize(fba, (w, h), interpolation=cv2.INTER_LINEAR) * k
        Fb = cv2.resize(fab, (w, h), interpolation=cv2.INTER_LINEAR) * k
        a = cv2.remap(self.frame(j), X + t * Fa[..., 0], Y + t * Fa[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        b = cv2.remap(self.frame(j + 1), X + (1 - t) * Fb[..., 0], Y + (1 - t) * Fb[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        out = a * (1.0 - weight) + b * weight
        # a warp loses a little of the finest detail, more the further it goes: put back as much as it lost, or the sharpness of a fine picture comes and goes about three times a second
        return np.maximum(out + CRISP * min(t, 1.0 - t) * (out - cv2.GaussianBlur(out, (0, 0), 0.8)), 0.0)
