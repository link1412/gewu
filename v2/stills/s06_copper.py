"""The purple of Jun ware as what it is, shot 6: copper brushed on the raw glaze, which then melts and runs. Sets up a concentration c(u, v) of copper by simulation and turns it into colour, not noise and not a painted cloud.

- brush: wide loaded strokes in a sweep, with dry parts. Their shape is a design (ref/jun/img/met_52663_05, met_50233_05 are the model, and neither is copied);
- firing: the glaze flows slowly down the wall and copper diffuses in it: semi-Lagrangian advection with a velocity that varies from place to place (thick glaze runs faster), and diffusion. This gives soft fronts, drips, and streaks along the flow;
- colour by concentration, read from those photographs, not from a spectrum: where copper is thin it is magenta, so a pink halo runs along every edge; more copper, purple; thick copper goes slate, and in the thickest patches, olive green with oxidised metal;
- a few hairline cracks that drink the colour, as on the photographs.
All the numbers (speeds, widths, the ramp) are estimates chosen by eye. u along the rim, v down the wall, cm.
"""

import cv2
import numpy as np

from kit import blur, fbm, sstep


def _poly(g, pts, pxcm, x0, v0, width, seed, gain=1.0):
    """A stroke of a loaded brush: one polyline widened to `width` (cm), with its edge torn at a long wavelength and a few dry streaks along it."""
    rng = np.random.default_rng(seed)
    pts = np.array(pts, float)
    tt = np.linspace(0, 1, 400)
    cs = np.stack([np.interp(tt, np.linspace(0, 1, len(pts)), pts[:, i]) for i in (0, 1)], -1).astype(np.float32)
    cs = cv2.GaussianBlur(cs, (0, 0), 16.0, borderType=cv2.BORDER_REPLICATE)
    m = np.zeros(g, np.uint8)
    xy = np.round((cs - [x0, v0]) * pxcm).astype(np.int32)
    cv2.polylines(m, [xy.reshape(-1, 1, 2)], False, 255, 1)
    d = cv2.distanceTransform(255 - m, cv2.DIST_L2, 5) / pxcm
    edge = fbm(g, pxcm, 0.6, 3.0, 2.8, seed + 1)
    k = 1.0 - d / np.maximum(width * (1 + 0.13 * edge), 0.1)
    return np.clip(k * 3.0, 0, 1) * gain


def simulate(LU, V0, V1, strokes, seed=620, pxcm=60.0, steps=70):
    """Returns c on a fixed grid (so that the shape stays the same at every quality), and a streak tracer carried by the same flow."""
    g = (int((V1 - V0) * pxcm), int(LU * pxcm))
    x0 = -LU / 2
    c = np.zeros(g, np.float32)
    for i, (pts, width, gain) in enumerate(strokes):
        c = np.maximum(c, _poly(g, pts, pxcm, x0, V0, width, seed + 3 * i, gain))
    # the brush is not even: fuller and drier, in slow patches
    c = c * np.clip(1.02 + 0.09 * fbm(g, pxcm, 0.5, 2.5, 2.8, seed + 40), 0.7, 1.2)
    X, Y = np.meshgrid(np.arange(g[1], dtype=np.float32), np.arange(g[0], dtype=np.float32))
    thick = fbm(g, pxcm, 0.5, 3.5, 3.0, seed + 41)  # thick glaze runs faster
    wan = fbm(g, pxcm, 0.15, 1.6, 2.8, seed + 42)
    ps = cv2.GaussianBlur(wan, (0, 0), 2.0)
    gy, gx = np.gradient(ps)
    vy = np.clip(0.8 + 0.5 * thick, 0.2, 1.7).astype(np.float32)  # px per step, downhill
    vx = (0.2 * gy * pxcm / 6.0 + 0.06 * thick).astype(np.float32)
    streak = fbm(g, pxcm, 0.03, 0.5, 2.2, seed + 43)
    for _ in range(steps):
        c = cv2.remap(c, X - vx, Y - vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        streak = cv2.remap(streak, X - vx, Y - vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        c = cv2.GaussianBlur(c, (0, 0), 1.35)
    # a run ends in a small swell
    c = np.clip(c * 1.1, 0, 1.2)
    return c.astype(np.float32), (streak / streak.std()).astype(np.float32), wan


def ramp(c):
    """Transmission of the copper sheet by concentration, per channel; the light goes through it twice, so these are square roots of what the eye sees over the milky layer below."""
    knots = np.array([0.0, 0.05, 0.2, 0.42, 0.68, 0.95, 1.3], np.float32)
    tr = np.array([1.0, 1.0, 0.98, 0.86, 0.62, 0.50, 0.46], np.float32)
    tg = np.array([1.0, 0.93, 0.62, 0.48, 0.40, 0.38, 0.36], np.float32)
    tb = np.array([1.0, 0.98, 0.80, 0.70, 0.58, 0.52, 0.47], np.float32)
    return np.stack([np.interp(c, knots, t) for t in (tr, tg, tb)], -1).astype(np.float32)


def cracks(shape, pxcm, LU, V0, V1, seed=640, n=14):
    """Hairlines in the glaze: they fork and stop. They take up colour: drawn as a darkening."""
    rng = np.random.default_rng(seed)
    m = np.zeros(shape, np.uint8)
    SH = 4
    k = pxcm * (1 << SH)
    for _ in range(n):
        p = np.array([rng.uniform(-LU / 2, LU / 2), rng.uniform(V0 + 0.4, V1)])
        a = rng.uniform(0, 6.28)
        L = rng.lognormal(np.log(0.45), 0.6)
        for b in range(int(rng.integers(1, 3))):
            q = p.copy()
            aa = a + (b * rng.normal(1.1, 0.3))
            pts = [q.copy()]
            for _ in range(int(L / 0.015)):
                aa += rng.normal(0, 0.22)
                q = q + 0.015 * np.array([np.cos(aa), np.sin(aa)])
                pts.append(q.copy())
            P = np.round((np.array(pts) - [-LU / 2, V0]) * k).astype(np.int32)
            cv2.polylines(m, [P.reshape(-1, 1, 2)], False, int(rng.uniform(80, 255)), max(1, int(round(rng.uniform(0.004, 0.009) * pxcm))), cv2.LINE_AA, SH)
    return cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), max(0.002 * pxcm, 0.4))
