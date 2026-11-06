"""Shots 1 and 38: an ink painting of a dawn on xuan paper, photographed on a light table. The lamp behind it rises, and the ink is still running.

    python3 -I v2/stills/s38_richu.py look [preview|final]      a contact sheet of key frames
    python3 -I v2/stills/s38_richu.py take [preview|final]      all frames of both shots, as PNG sequences

No Blender: light through a sheet is a soft lamp times the transmittance of each layer, so this is exact and fast.

Rebuild, after the blind review ("the same paper noise at one scale, gradients and cloud noise, no content, dead black"):
- The sky is painted stroke by stroke. Each stroke is a loaded brush: a source along a wandering line, and a front that runs out from it through the paper.
  The front is an arrival time (a shortest path over a speed field), the same model the ink pool always had. It is not a simulation of the fluid: that was worked out
  at tens of minutes a run. Speed has big, middle and small scales and the fibres themselves, so a stroke has lobes, then fingers, then feathers, in that order of importance.
- What a real wet stroke does and this one does: pigment thins out towards the front, and collects in a tide line where the front stopped; carbon lags behind the water.
- So the clouds have shapes, gaps that the light comes through, and hard and soft edges, instead of one noise threshold.
- The ink of the horizon keeps running while we watch. It is the same arrival time read at a later moment, with the Lucas-Washburn sqrt(t).
- Dry ink is not dead black: thick sumi has a faint sheen from the room, and the brush's direction shows in it.
Scales are estimates from general knowledge of the paper; stroke layout is ours.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra

from darkroom import develop, save_png
from kit import OUT, blur, fbm, sstep

W = 9.0  # frame width on the paper (cm)
H = W * 9.0 / 16.0
R_H = 32.0  # radius of the horizon (cm): sagitta about 3.5% of the width
X0, X1 = -0.66 * W, 0.66 * W  # the sheet that is modelled, around the crown of the horizon
Y0, Y1 = -0.72 * H, 1.5 * H

SIGMA_WARM = np.array([0.05, 1.05, 3.0], np.float32)  # a warm glaze (朱磦): stops blue, then green
SIGMA_BLUE = np.array([1.7, 1.12, 0.28], np.float32)  # indigo (花青): stops red
SIGMA_INK = np.array([1.04, 1.0, 0.94], np.float32)  # carbon: nearly neutral, a little warm when thin
SIGMA_ROSE = np.array([0.06, 1.0, 0.42], np.float32)  # rouge (胭脂): stops green, so it turns pink alone and violet over indigo
LAMP = np.array([1.0, 0.76, 0.5], np.float32)
AMBIENT = np.array([0.72, 0.8, 1.0], np.float32)

SUN_R0 = (0.34, 0.27, 0.2)  # cm, per channel
SUN_P = 1.55


def fibres(shape, pxcm, per_cm2, lo, hi, seed):
    """Long curved fibres drawn into a canvas (antialiased), each with its own weight."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 * per_cm2)
    out = np.zeros(shape, np.float32)
    for level in (70, 120, 190):
        canvas = np.zeros(shape, np.uint8)
        m = n // 3
        x0, y0 = rng.uniform(0, nx, m), rng.uniform(0, ny, m)
        a = rng.uniform(0, np.pi, m)
        length = rng.uniform(lo, hi, m) * pxcm / 5.0
        pts = []
        px, py = x0.copy(), y0.copy()
        pts.append(np.stack([px, py], -1))
        for _ in range(5):
            a = a + rng.normal(0, 0.28, m)
            px, py = px + length * np.cos(a), py + length * np.sin(a)
            pts.append(np.stack([px, py], -1))
        lines = np.round(np.stack(pts, 1) * 8).astype(np.int32)
        cv2.polylines(canvas, list(lines), False, level, 1, cv2.LINE_AA, shift=3)
        out = np.maximum(out, canvas.astype(np.float32) / 190.0)
    return out


def arrival_time(source, speed, band, across=1.0):
    """Shortest travel time from where `source` is true, over an 8-neighbour grid limited to `band`. Unreached cells are inf.
    across: the cost of a vertical step against a horizontal one. The sheet is made along x, so water goes further that way."""
    ny, nx = band.shape
    idx = -np.ones((ny, nx), np.int64)
    idx[band] = np.arange(band.sum())
    n = int(band.sum())
    rows, cols, vals = [], [], []
    diag = float(np.hypot(1.0, across))
    for dy, dx, d in ((0, 1, 1.0), (1, 0, across), (1, 1, diag), (1, -1, diag)):
        ya, yb = (0, ny - dy), (dy, ny)
        if dx >= 0:
            a, b = idx[ya[0] : ya[1], 0 : nx - dx], idx[yb[0] : yb[1], dx:]
            sa, sb = speed[ya[0] : ya[1], 0 : nx - dx], speed[yb[0] : yb[1], dx:]
        else:
            a, b = idx[ya[0] : ya[1], -dx:], idx[yb[0] : yb[1], 0 : nx + dx]
            sa, sb = speed[ya[0] : ya[1], -dx:], speed[yb[0] : yb[1], 0 : nx + dx]
        ok = (a >= 0) & (b >= 0)
        rows.append(a[ok])
        cols.append(b[ok])
        vals.append(d * 2.0 / (sa[ok] + sb[ok]))
    start = idx[band & source]
    rows.append(np.full(start.size, n))
    cols.append(start)
    vals.append(np.full(start.size, 1e-6))
    g = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n + 1, n + 1))
    t = dijkstra(g, directed=False, indices=n)
    out = np.full((ny, nx), np.inf, np.float32)
    out[band] = t[:-1]
    return out


# The sky, stroke by stroke, in the order a painter would lay it. xa, xb: extent (cm); hc: height above the horizon (cm); th: thickness at the belly; reach: how far the water runs (cm);
# ink, blue, warm: pigment load. The lower sky is left open over the middle, where the sun will come through.
STROKES = [
    # the wet underpainting of the upper sky: broad, overlapping, nearly all ink
    dict(xa=-7.5, xb=2.5, hc=6.6, th=1.5, reach=0.8, ink=1.7, blue=0.30),
    dict(xa=-2.0, xb=8.0, hc=5.7, th=1.3, reach=0.7, ink=1.5, blue=0.35),
    dict(xa=-8.0, xb=-0.6, hc=4.7, th=1.1, reach=0.62, ink=1.05, blue=0.45),
    dict(xa=0.6, xb=7.6, hc=4.35, th=0.95, reach=0.6, ink=0.95, blue=0.5),
    # banks of cloud in the middle: indigo, thin ink and rouge
    dict(xa=-7.0, xb=-1.1, hc=3.25, th=0.5, reach=0.46, ink=0.34, blue=0.5, rose=0.42),
    dict(xa=1.2, xb=6.8, hc=2.95, th=0.45, reach=0.42, ink=0.36, blue=0.5, rose=0.46),
    dict(xa=-3.6, xb=2.1, hc=3.75, th=0.42, reach=0.4, ink=0.3, blue=0.5, rose=0.3),
    dict(xa=-6.4, xb=-2.5, hc=2.2, th=0.28, reach=0.3, ink=0.22, blue=0.34, rose=0.62),
    dict(xa=2.4, xb=7.2, hc=1.95, th=0.24, reach=0.28, ink=0.24, blue=0.32, rose=0.66),
    dict(xa=-1.9, xb=0.9, hc=2.5, th=0.14, reach=0.2, ink=0.12, blue=0.28, rose=0.42),
    # long thin strata low down, the ones the sun will edge with light
    dict(xa=-7.0, xb=-1.5, hc=1.25, th=0.13, reach=0.17, ink=0.3, blue=0.12, rose=0.42, warm=0.12),
    dict(xa=1.1, xb=5.6, hc=1.05, th=0.11, reach=0.15, ink=0.38, blue=0.08, rose=0.38, warm=0.18),
    dict(xa=3.6, xb=7.4, hc=0.74, th=0.08, reach=0.12, ink=0.48, blue=0.04, rose=0.26, warm=0.25),
    dict(xa=-5.4, xb=-2.2, hc=0.62, th=0.07, reach=0.1, ink=0.46, blue=0.03, rose=0.24, warm=0.28),
]


class Painting:
    def __init__(self, scale=1.0, seed=3):
        self.pxcm = 2560.0 / W * scale
        self.scale = scale
        pxcm = self.pxcm
        nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
        shape = (ny, nx)
        self.shape = shape
        x = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
        y = Y1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
        X, Y = np.meshgrid(x, y)
        h = np.sqrt(X**2 + (Y + R_H) ** 2) - R_H  # height above the horizon, cm
        self.X, self.h = X, h

        # --- the paper: scales with a clear order. Fibres you can see, a slow cloudy formation, and only a little in between.
        formation = fbm(shape, pxcm, 0.09, 1.4, 2.9, seed)
        flocs = fbm(shape, pxcm, 0.02, 0.09, 1.8, seed + 7)
        long_f = cv2.GaussianBlur(fibres(shape, pxcm, 1100, 0.12, 0.42, seed + 2), (0, 0), max(0.5 * scale, 0.35))
        short_f = cv2.GaussianBlur(fibres(shape, pxcm, 800, 0.03, 0.14, seed + 3), (0, 0), max(0.4 * scale, 0.3))
        wob = 0.012 * fbm(shape, pxcm, 0.5, 4.0, 3.0, seed + 4)
        laid = np.sin(2 * np.pi * (Y + wob) / 0.085)
        chain = np.exp(-(((np.mod(X + 0.03 * fbm(shape, pxcm, 1.0, 6.0, 3.0, seed + 5), 2.4) - 1.2) / 0.018) ** 2))
        tau = 0.42 + 0.03 * formation + 0.004 * flocs + 0.07 * long_f + 0.03 * short_f + 0.006 * laid + 0.022 * chain
        self.T_paper = np.exp(-np.maximum(tau, 0.02)).astype(np.float32)
        self.reflect = (0.5 + 0.5 * (1.0 - self.T_paper)).astype(np.float32)
        settle = (1.0 + 0.012 * fbm(shape, pxcm, 0.006, 0.04, 1.6, seed + 6) + 0.1 * blur(long_f, 1.2 * max(scale, 0.5)) + 0.012 * formation).astype(np.float32)
        self.settle = settle

        # --- the speed of water through this paper, on a coarser grid. The order of the scales is what makes lobes, fingers, feathers.
        k = max(int(round(3 * scale)), 1)
        self.k = k
        sm = (ny // k, nx // k)
        big = fbm(sm, pxcm / k, 0.9, 6.0, 3.2, seed + 40)
        mid = fbm(sm, pxcm / k, 0.12, 0.9, 2.6, seed + 41)
        small = fbm(sm, pxcm / k, 0.02, 0.12, 2.0, seed + 42)
        f_soft = cv2.resize(long_f, sm[::-1], interpolation=cv2.INTER_AREA)
        speed = np.exp(0.9 * big + 0.62 * mid + 0.36 * small + 1.5 * f_soft).astype(np.float64)
        speed /= np.median(speed)
        Xs, hs = cv2.resize(X, sm[::-1], interpolation=cv2.INTER_AREA), cv2.resize(h, sm[::-1], interpolation=cv2.INTER_AREA)

        # --- each stroke
        rng = np.random.default_rng(seed + 50)
        blue = np.zeros(shape, np.float32)
        ink = np.zeros(shape, np.float32)
        warm = np.zeros(shape, np.float32)
        rose = np.zeros(shape, np.float32)
        wander_big = fbm(sm, pxcm / k, 1.5, 9.0, 3.2, seed + 51)
        wander_mid = fbm(sm, pxcm / k, 0.2, 1.5, 2.8, seed + 52)
        for i, st in enumerate(STROKES):
            u = (Xs - st["xa"]) / (st["xb"] - st["xa"])
            belly = np.sin(np.pi * np.clip(u, 0, 1)) ** 0.55
            hc = st["hc"] + (0.34 * wander_big + 0.05 * wander_mid) * (0.35 + 0.65 * st["th"]) * 1.6 + 0.12 * np.sin(2.3 * u + i)
            d = np.abs(hs - hc)
            src = (d < 0.5 * st["th"] * belly) & (u > 0) & (u < 1)
            band = (d < 0.5 * st["th"] + 2.6 * st["reach"]) & (u > -0.25) & (u < 1.25)
            if not src.any():
                continue
            # low thin strata run far along the sheet and little across it, so they lie down instead of standing up like bushes
            T = arrival_time(src, speed, band, across=1.0 + 1.1 * float(np.clip(1.0 - st["hc"] / 3.0, 0.0, 1.0))) / (pxcm / k)
            uu = np.where(np.isfinite(T), T / st["reach"], 9.0).astype(np.float32)
            uu = cv2.GaussianBlur(cv2.resize(uu, (nx, ny), interpolation=cv2.INTER_LINEAR), (0, 0), 0.016 * pxcm)
            # a low stratum is laid with a flat brush and drawn out sideways: its fingers run together along the sheet, and only a little of the fine feather stays
            lay = float(np.clip(1.0 - st["hc"] / 3.2, 0.0, 1.0))
            if lay > 0.0:
                uu = (0.2 + 0.8 * (1.0 - lay)) * uu + (0.8 * lay) * cv2.GaussianBlur(uu, (0, 0), sigmaX=0.3 * pxcm, sigmaY=0.012 * pxcm)
            # a stroke thins towards its front, and a tide line stands where the front stopped; each has its own loading along its length
            load = cv2.resize((1.0 + 0.45 * fbm(sm, pxcm / k, 0.6, 3.0, 2.8, seed + 60 + i)).astype(np.float32), (nx, ny), interpolation=cv2.INTER_LINEAR)
            body = sstep(1.0, 0.0, uu) ** 1.15
            tide_here = sstep(0.05, 0.55, cv2.resize(fbm(sm, pxcm / k, 0.4, 2.0, 2.6, seed + 80 + i).astype(np.float32), (nx, ny), interpolation=cv2.INTER_LINEAR))
            tide = 0.14 * tide_here * np.exp(-(((uu - 0.95) / 0.09) ** 2))
            f = np.maximum(load, 0.15) * (body + tide)
            ink += st.get("ink", 0.0) * f
            blue += st.get("blue", 0.0) * f
            warm += st.get("warm", 0.0) * f
            rose += st.get("rose", 0.0) * f
            print(f"[stroke {i}] {src.sum()} source cells", flush=True)

        # --- the washes under the strokes: a warm glaze low down, a thin indigo above it
        def wander(s, amp):
            return amp * fbm(shape, pxcm, 0.8, 7.0, 3.2, s) + 0.12 * amp * fbm(shape, pxcm, 0.05, 0.5, 2.4, s + 1)

        hw = h + wander(seed + 10, 0.09)
        warm += 1.5 * np.exp(-((np.maximum(hw - 0.06, 0.0) / 0.46) ** 2))
        hb = h + wander(seed + 12, 0.18)
        blue += 0.9 * sstep(0.34, 2.2, hb) ** 1.15
        hk = h + wander(seed + 14, 0.3)
        ink += 1.3 * sstep(2.6, 6.2, hk) ** 1.3
        hr = h + wander(seed + 16, 0.14)
        rose += 0.34 * np.exp(-(((hr - 1.5) / 0.95) ** 2))
        self.wash = ((warm * settle)[..., None] * SIGMA_WARM + (blue * settle)[..., None] * SIGMA_BLUE + (ink * settle)[..., None] * SIGMA_INK + (rose * settle)[..., None] * SIGMA_ROSE).astype(np.float32)

        # --- the ink of the horizon: an arrival time at full resolution, which we read at a later moment each frame
        # fibres lead the feathers; the big and middle scales are kept low, or the bleed stands up in fat tufts that read as bushes on a hill
        fast = np.exp(0.3 * cv2.resize(big, (nx, ny), interpolation=cv2.INTER_CUBIC) + 0.26 * cv2.resize(mid, (nx, ny), interpolation=cv2.INTER_CUBIC) + 0.42 * fbm(shape, pxcm, 0.02, 0.1, 2.0, seed + 43) + 1.5 * long_f + 0.6 * short_f).astype(np.float64)
        fast /= np.median(fast)
        edge0 = h + 0.03 * fbm(shape, pxcm, 1.2, 7.0, 3.1, seed + 32) + 0.008 * fbm(shape, pxcm, 0.1, 1.0, 2.5, seed + 33)
        band = (edge0 > -0.12) & (h < 1.3)
        Ti = arrival_time((edge0 < 0) & band, fast, band) / pxcm
        Ti[edge0 <= -0.12] = 0.0
        # capped well past any front we will read, so the edge of the band is no step for the resampling to ring on
        Ti[~np.isfinite(Ti)] = 0.5
        self.Ti = cv2.GaussianBlur(np.minimum(Ti, 0.5).astype(np.float32), (0, 0), 0.006 * pxcm)
        self.edge0 = edge0.astype(np.float32)
        # the brush's direction in the body of the ink, seen only in its sheen: a brush laid along the horizon
        streak = fbm((ny // 2 + 1, nx // 10 + 1), pxcm / 2, 0.05, 2.5, 2.5, seed + 70)
        self.streak = cv2.resize(streak.astype(np.float32), (nx, ny), interpolation=cv2.INTER_CUBIC)
        # the ink of the land is not one density. It was laid in several passes, and when the lamp is strong the thin passes glow through
        passes = fbm((ny // 3 + 1, nx // 14 + 1), pxcm / 3, 0.12, 3.0, 2.6, seed + 71)
        passes = cv2.resize(passes.astype(np.float32), (nx, ny), interpolation=cv2.INTER_CUBIC)
        self.passes = np.clip(0.5 + 0.42 * passes, 0.0, 1.0)
        print(f"[painting] {nx}x{ny}", flush=True)

    def view(self, f, apex_y, zoom, dx=0.0):
        """Warp a sheet field into the frame: the crown of the horizon at apex_y of the height, zoom > 1 pushes in. dx: the camera's travel across the sheet, cm."""
        s = self.pxcm * zoom
        res_w, res_h = int(2560 * self.scale), int(1440 * self.scale)
        fx = self.pxcm / s
        cx = (0.0 + dx - X0) * self.pxcm
        cy = (Y1 - 0.0) * self.pxcm
        M = np.array([[fx, 0.0, cx - fx * res_w / 2.0], [0.0, fx, cy - fx * apex_y * res_h]], np.float32)
        return cv2.warpAffine(f, M, (res_w, res_h), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)

    def frame(self, apex_y, zoom, front, lamp, dx=0.0):
        """Scene-linear frame. `front`: how far the ink has run, cm; lamp: {sun_y, sun_x, sun, disc, glow, ambient}."""
        res_w, res_h = int(2560 * self.scale), int(1440 * self.scale)
        pxcm = self.pxcm * zoom
        xs = (np.arange(res_w, dtype=np.float32) + 0.5 - res_w / 2.0) / pxcm + dx
        ys = (apex_y * res_h - np.arange(res_h, dtype=np.float32) - 0.5) / pxcm
        X, Y = np.meshgrid(xs, ys)
        h = np.sqrt(X**2 + (Y + R_H) ** 2) - R_H

        v = lambda f: self.view(f, apex_y, zoom, dx)
        Ti = np.maximum(v(self.Ti), 0.0)
        e = v(self.edge0)
        settle = v(self.settle)
        # how the ink stands at this moment: dense behind the front, thinning towards it, a tide at the front, and a grey stain of water beyond it, which carbon lags behind
        u = Ti / front
        core = (4.2 + 3.6 * v(self.passes)) * sstep(0.22, -0.02, e / (front * 2.6)) ** 1.25
        run = 2.2 * sstep(1.0, 0.0, u) ** 1.5 + 0.12 * np.exp(-(((u - 0.9) / 0.2) ** 2))
        stain = 0.2 * sstep(1.75, 1.0, u)
        D = (core + run + stain) * settle
        T_ink = np.exp(-D[..., None] * SIGMA_INK)

        # the lamp behind the paper: a wide low source, and the disc itself once it clears the ink
        sx = lamp.get("sun_x", 0.0)
        d2 = (X - sx) ** 2 + (Y - lamp["sun_y"]) ** 2
        wide = lamp["glow"] * np.exp(-np.maximum(h, 0.0) / 2.3) * np.exp(-(((X - sx) / 8.0) ** 2))
        halo = lamp["sun"] * (2.2**2 / (2.2**2 + d2)) ** 1.2
        disc = lamp["disc"] * np.stack([(1.0 + d2 / r0**2) ** -SUN_P for r0 in SUN_R0], -1)
        L = (wide + halo)[..., None] * LAMP + disc * LAMP

        T_p = v(self.T_paper)[..., None]
        T_w = np.exp(-v(self.wash))
        refl = v(self.reflect)[..., None]
        # the room falls on the front of the sheet. Paper gives it back; thick dry ink gives back a faint sheen that shows the brush
        amb = lamp["ambient"] * AMBIENT * refl * (0.06 + 0.94 * T_ink) * (0.35 + 0.65 * T_w)
        sheen = lamp["ambient"] * 0.34 * np.clip(1.0 - T_ink.mean(-1, keepdims=True) * 3.0, 0.0, 1.0) * (1.0 + 0.5 * v(self.streak)[..., None]) * sstep(-2.6, 0.2, h)[..., None] * AMBIENT
        return L * T_p * T_w * T_ink + amb + sheen


LOOK = {"exposure": 0.0, "contrast": 1.24, "saturation": 1.04, "black": 0.0, "grain": 0.9, "sharpen": 0.18, "halation": 0.12, "glare": 0.016, "vignette": 0.22, "ca": 0.00035}


def ease(a, b, t):
    return a + (b - a) * float(sstep(0.0, 1.0, np.clip(t, 0.0, 1.0)))


def shot1(i):
    """31 frames, 1.24 s: the horizon at the middle of the frame, before the light. The ink runs while we watch; the camera pulls back and drifts."""
    t = i / 30.0
    return {"apex_y": 0.48, "zoom": 1.08 - 0.075 * t, "dx": 0.05 - 0.1 * t, "front": 0.05 * (1.0 + 2.6 * t) ** 0.5, "lamp": {"sun_y": -9.0, "sun": 0.0, "disc": 0.0, "glow": 1.0, "ambient": 0.012}}


N38 = 136


def shot38(i):
    """5.4 s. First only a glow at the foot of the frame under the title; the horizon rises, the clouds come out; the lamp clears the ink and floods the sheet."""
    t = i / (N38 - 1.0)
    rise = ease(1.2, 0.86, t / 0.5) if t < 0.5 else ease(0.86, 0.62, (t - 0.5) / 0.32)
    sun_y = ease(-4.4, -1.1, t / 0.62) if t < 0.62 else ease(-1.1, 1.12, (t - 0.62) / 0.38)
    grow = 0.42 + 1.5 * t**1.5 + 2.6 * float(sstep(0.62, 1.0, t))
    return {
        "apex_y": rise,
        "zoom": 1.0 - 0.05 * t,
        "dx": -0.05 + 0.1 * t,
        "front": 0.06 * (1.0 + 1.6 * t) ** 0.5,
        "lamp": {"sun_y": sun_y, "sun": 0.1 + 2.4 * t**4 + 9.0 * float(sstep(0.72, 1.0, t)) ** 2, "disc": 130.0 * float(sstep(0.6, 0.82, t)), "glow": grow, "ambient": 0.012},
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "look"
    q = sys.argv[2] if len(sys.argv) > 2 else "preview"
    scale = {"preview": 0.375, "final": 0.75}[q]
    pic = Painting(scale)

    def render(spec, seed):
        return develop(pic.frame(spec["apex_y"], spec["zoom"], spec["front"], spec["lamp"], spec.get("dx", 0.0)).astype(np.float32), **{**LOOK, "seed": seed})

    if mode == "look":
        from darkroom import print_look, film_grain

        keys = [(shot1, 15), (shot38, 20), (shot38, 60), (shot38, 85), (shot38, 100), (shot38, 115), (shot38, 125), (shot38, 135)]
        ims = [render(fn(i), i + 1) for fn, i in keys]
        d = os.path.join(OUT, "s38_richu")
        os.makedirs(d, exist_ok=True)
        tile = [film_grain(print_look(cv2.resize(a, (960, 540), interpolation=cv2.INTER_AREA)), seed=i) for i, a in enumerate(ims)]
        sheet = np.vstack([np.hstack(tile[k : k + 2]) for k in (0, 2, 4, 6)])
        cv2.imwrite(os.path.join(d, "look.jpg"), (np.clip(sheet, 0, 1)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
        for tag, a in (("first", ims[0]), ("sun", ims[5]), ("last", ims[-1])):
            cv2.imwrite(os.path.join(d, f"look_{tag}.jpg"), (np.clip(print_look(a), 0, 1)[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(os.path.join(d, "look.jpg"))
        return

    for name, fn, n in (("s01_moyun", shot1, 31), ("s38_richu", shot38, N38)):
        dd = os.path.join(OUT, f"{name}_take_{q}")
        os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd):
            os.remove(os.path.join(dd, f))
        for i in range(n):
            save_png(os.path.join(dd, f"f{i:03d}.png"), render(fn(i), i + 1 + (1000 if n > 31 else 0)))
        json.dump(LOOK, open(os.path.join(dd, "look.json"), "w"))
        json.dump([round(fn(i)["apex_y"], 5) for i in range(n)], open(os.path.join(dd, "apex.json"), "w"))  # the film's end title rides on the horizon
        print(dd, flush=True)


main()
