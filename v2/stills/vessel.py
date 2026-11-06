"""Helpers for the vessel stills (shots 4, 5, 6, 11, 23, 26, 28, 33): turned profiles, framing on the arc, grains, window lights."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from kit import frame_camera


# --- a turned body ----------------------------------------------------------------------------------------------
class Profile:
    """A smoothed polyline (r, z) resampled by arc length. Traverse it so that the outward normal is (tz, -tr):
    foot to axis for an outside surface."""

    def __init__(self, pts, sigma=0.3, ds=0.001):  # finer than the mesh: at 0.004 the polyline beats against the grid and ripples show in a window's reflected edge
        p = np.array(pts, float)
        seg = np.hypot(*np.diff(p, axis=0).T)
        t = np.r_[0.0, np.cumsum(seg)]
        tt = np.arange(0.0, t[-1], ds)
        r, z = np.interp(tt, t, p[:, 0]), np.interp(tt, t, p[:, 1])
        # smooth, with the ends held by reflection
        k = int(sigma / ds) | 1
        rr = cv2.GaussianBlur(r[None, :], (0, 0), k, borderType=cv2.BORDER_REPLICATE)[0]
        zz = cv2.GaussianBlur(z[None, :], (0, 0), k, borderType=cv2.BORDER_REPLICATE)[0]
        s = np.r_[0.0, np.cumsum(np.hypot(np.diff(rr), np.diff(zz)))]
        self.s, self.r, self.z = s, rr, zz
        self.L = float(s[-1])
        tr, tz = np.gradient(rr, s), np.gradient(zz, s)
        n = np.hypot(tr, tz) + 1e-9
        self.nr, self.nz = tz / n, -tr / n

    def at(self, s):
        f = lambda a: np.interp(s, self.s, a).astype(np.float32)  # noqa: E731
        return f(self.r), f(self.z), f(self.nr), f(self.nz)

    def s_of_r(self, r0, near=None):
        """Arc length where the profile crosses radius r0 (the crossing nearest `near`)."""
        i = np.nonzero(np.diff(np.sign(self.r - r0)))[0]
        if near is None:
            return float(self.s[i[-1]])
        return float(self.s[i[np.argmin(np.abs(self.s[i] - near))]])


def turned(prof, U, V, h=0.0, az=0.0):
    """Surface point for flat coordinates U (cm along the latitude, at V's radius) and V (arc length): isometric along
    both, so that a grain stays round everywhere. h moves along the normal. az: azimuth of U = 0."""
    r, z, nr, nz = prof.at(V)
    th = az + U / np.maximum(r, 0.05)
    th = np.clip(th, az - np.pi, az + np.pi)
    rr = r + h * nr
    return np.stack([rr * np.cos(th), rr * np.sin(th), z + h * nz], -1).astype(np.float32)


# --- camera -----------------------------------------------------------------------------------------------------
def cam_basis(cam):
    loc, tgt = np.array(cam["loc"], float), np.array(cam["target"], float)
    f = tgt - loc
    f /= np.linalg.norm(f)
    right = np.cross(f, [0.0, 0.0, 1.0])
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    a = np.radians(cam.get("roll", 0.0))
    return loc, f, np.cos(a) * right + np.sin(a) * up, -np.sin(a) * right + np.cos(a) * up


def project(cam, P):
    """(x, y) in frame fractions from the top left, and depth along the view."""
    loc, f, right, up = cam_basis(cam)
    d = P - loc
    w = d @ f
    k = cam["lens_mm"] / 36.0
    return 0.5 + k * (d @ right) / w, 0.5 - k * (16.0 / 9.0) * (d @ up) / w, w


def view_dir(az_deg, el_deg):
    """Unit vector from the subject to the camera. az measured from +x towards +y, el above the horizon."""
    a, e = np.radians(az_deg), np.radians(el_deg)
    return np.array([np.cos(a) * np.cos(e), np.sin(a) * np.cos(e), np.sin(e)])


def top_arc(cam, P, bins=64):
    """Upper envelope of points in the frame: returns x, y (frame fractions)."""
    x, y, w = project(cam, P.reshape(-1, 3))
    ok = (w > 0) & (x > -0.3) & (x < 1.3)
    x, y = x[ok], y[ok]
    i = np.clip(((x + 0.3) / 1.6 * bins).astype(int), 0, bins - 1)
    top = np.full(bins, np.inf)
    np.minimum.at(top, i, y)
    xc = (np.arange(bins) + 0.5) / bins * 1.6 - 0.3
    good = np.isfinite(top) & (xc > 0.0) & (xc < 1.0)
    return xc[good], top[good]


def fit_arc(P, view, W, dist, apex=(0.5, 0.48), target0=(0.0, 0.0, 0.0), roll=0.0, aperture_mm=None, focus_point=None, iters=6):
    """A camera on `view` with frame width W at the subject, moved in its own plane so that the apex of the upper
    envelope of P lands on `apex`. Returns the camera and the measured sag (fraction of the frame width)."""
    tgt = np.array(target0, float)
    for _ in range(iters):
        cam = frame_camera(tgt, view, W, dist, roll=roll)
        x, y = top_arc(cam, P)
        if x.size < 6:
            tgt = P.reshape(-1, 3).mean(0)
            continue
        a, b, c = np.polyfit(x, y, 2)
        x0 = -b / (2 * a) if abs(a) > 1e-6 else 0.5
        x0 = float(np.clip(x0, -0.5, 1.5))
        y0 = a * x0**2 + b * x0 + c
        _, _, right, up = cam_basis(cam)
        tgt = tgt + right * (x0 - apex[0]) * W - up * (y0 - apex[1]) * W * 9.0 / 16.0
    cam = frame_camera(tgt, view, W, dist, aperture_mm=aperture_mm, focus_point=focus_point if focus_point is not None else tgt, roll=roll)
    x, y = top_arc(cam, P)
    a, b, c = np.polyfit(x, y, 2)
    sag = abs(a) * 0.25 * (9.0 / 16.0)  # y is a fraction of the height; rise from the centre to the edge, over the width
    print(f"arc: apex x {-b / (2 * a):.3f} y {a * (b / (2 * a)) ** 2 - b * b / (2 * a) + c:.3f}, sag {sag:.3f} of W, range y {y.min():.3f}..{y.max():.3f}")
    return cam, sag


def patch(prof, cam, urange, vrange, margin=0.06, az=0.0, n=500):
    """The bounding box in (u, v) of the part of the turned surface that the camera sees in the frame, plus a margin."""
    u = np.linspace(*urange, n, dtype=np.float32)
    v = np.linspace(*vrange, n, dtype=np.float32)
    U, V = np.meshgrid(u, v)
    P = turned(prof, U, V, az=az)
    x, y, w = project(cam, P.reshape(-1, 3))
    x, y = x.reshape(U.shape), y.reshape(U.shape)
    # facing the camera (in latitude terms), with a little over the horizon so that the silhouette is whole
    r, z, nr, nz = prof.at(V)
    th = az + U / np.maximum(r, 0.05)
    nrm = np.stack([nr * np.cos(th), nr * np.sin(th), nz], -1)
    loc = np.array(cam["loc"], float)
    d = loc - P
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    ok = (x > -margin) & (x < 1 + margin) & (y > -margin) & (y < 1 + margin) & ((nrm * d).sum(-1) > -0.12)
    if not ok.any():
        raise SystemExit("nothing of the surface is in the frame")
    return float(U[ok].min()), float(U[ok].max()), float(V[ok].min()), float(V[ok].max())


def reflect_light_loc(point, normal, cam, distance):
    """Where a light has to be for `point` with `normal` to mirror it into the camera: r = 2(n.v)n - v."""
    p, n = np.array(point, float), np.array(normal, float)
    n = n / np.linalg.norm(n)
    v = np.array(cam["loc"], float) - p
    v /= np.linalg.norm(v)
    r = 2 * n.dot(v) * n - v
    return p + r * distance, r


def window(name, loc, target, w, h, cols, rows, bar, L_watts, rgb=(1.0, 1.0, 1.0), roll_up=(0.0, 0.0, 1.0), **kw):
    """A window made of panes with glazing bars: its reflection in a glaze is what makes the glaze read as glass.
    Panes are area lights; watts is per pane. The lights' aim is along target - loc with Blender's up convention, so the
    bars stay level with the world."""
    loc, target = np.array(loc, float), np.array(target, float)
    f = target - loc
    f /= np.linalg.norm(f)
    x = np.cross(f, roll_up)
    x /= np.linalg.norm(x)
    y = np.cross(x, f)
    pw, ph = (w - bar * (cols - 1)) / cols, (h - bar * (rows - 1)) / rows
    out = []
    for j in range(rows):
        for i in range(cols):
            c = loc + x * ((i + 0.5) * (pw + bar) - w / 2 - bar / 2) + y * ((j + 0.5) * (ph + bar) - h / 2 - bar / 2)
            out.append({"name": f"{name}{i}{j}", "loc": c.tolist(), "target": (c + f).tolist(), "size": [pw, ph], "watts": L_watts, "rgb": list(rgb), **kw})
    return out


# --- particles --------------------------------------------------------------------------------------------------
def grains(shape, pxcm, per_cm2, rmin, rmax, seed=0, bins=5, slope=-2.4, spread=0.3, mask=None):
    """Sand: round-ish particles with a size distribution. Returns d (distance from the particle's centre, in units of its
    radius, per the top-most particle), r (radius, cm) and val (a uniform random number per particle)."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    D = np.full(shape, 9.0, np.float32)
    R = np.zeros(shape, np.float32)
    VAL = np.zeros(shape, np.float32)
    edges = np.geomspace(rmin, rmax, bins + 1)
    w = (edges[:-1] * edges[1:]) ** (slope / 2.0 + 1.0)
    w = w / w.sum()
    for i in range(bins):
        r0 = float(np.sqrt(edges[i] * edges[i + 1]))
        n = int(area * per_cm2 * w[i])
        if n < 1:
            continue
        x, y = rng.integers(0, nx, n), rng.integers(0, ny, n)
        if mask is not None:
            keep = rng.random(n) < mask[y, x]
            x, y = x[keep], y[keep]
            if x.size == 0:
                continue
        seeds = np.ones(shape, np.uint8)
        seeds[y, x] = 0
        dist, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        m = int(lab.max()) + 1
        rr = r0 * rng.lognormal(0.0, spread, m).astype(np.float32)
        vv = rng.random(m, dtype=np.float32)
        ri = rr[lab]
        d = dist / pxcm / ri
        win = d < D
        D[win], R[win], VAL[win] = d[win], ri[win], vv[lab][win]
    return D, R, VAL


def seconds_note(log):
    """GPU seconds from a render's log."""
    return open(log).read().strip().splitlines()[-1].split()[-1]
