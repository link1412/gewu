"""Translucent stones as a stack of real depth layers, baked per vertex (石、珠、果组; used by s03, s25).

Not a volume render: for each surface vertex the view ray is refracted into the stone and marched through layers that lie
parallel to the surface, each a flat chart (U, V in cm) with its own full-resolution structure and a scattering blur that
grows with depth. Light inside comes from the analytic path length towards each lamp through the ellipsoid. An approximation
of multiple scattering [stand-in], noise-free, with true parallax and true depth of the structure. Reflections stay real (Cycles).

Everything is drawn stroke by stroke: fibres are streamlines, cracks are polylines; noise only modulates them.
"""

import cv2
import numpy as np

from kit import blur, fbm, rank, sstep


def flow_field(shape, pxcm, theta0, seed, wander=0.55, curl=0.22):
    """Direction field (angle, radians) of the grain: a slow sweep, some bends. Large scale leads."""
    a = theta0 + wander * fbm(shape, pxcm, 1.6, 9.0, 3.6, seed) + curl * fbm(shape, pxcm, 0.35, 1.8, 3.0, seed + 1)
    return a.astype(np.float32)


def streamlines(theta, pxcm, n, length_cm, ds_cm, seed, wiggle=0.25, cross=0.0, weight=None):
    """n streamlines through the field; returns an array (n, m, 2) in pixels. Each fibre has its own heading offset and a wobble."""
    rng = np.random.default_rng(seed)
    ny, nx = theta.shape
    if weight is not None:
        # rejection-sample the seeds by a density map
        xs, ys = [], []
        got = 0
        while got < n:
            x = rng.integers(0, nx, n * 2)
            y = rng.integers(0, ny, n * 2)
            k = rng.random(n * 2) < weight[y, x]
            xs.append(x[k])
            ys.append(y[k])
            got += int(k.sum())
        x = np.concatenate(xs)[:n].astype(np.float32)
        y = np.concatenate(ys)[:n].astype(np.float32)
    else:
        x = rng.uniform(0, nx, n).astype(np.float32)
        y = rng.uniform(0, ny, n).astype(np.float32)
    m = max(3, int(np.max(length_cm) / ds_cm))
    off = rng.normal(0, 1, n).astype(np.float32) * cross
    ph = rng.uniform(0, 6.28, n).astype(np.float32)
    fr = rng.uniform(0.4, 1.6, n).astype(np.float32)
    out = np.zeros((n, m, 2), np.float32)
    step = ds_cm * pxcm
    for i in range(m):
        out[:, i, 0], out[:, i, 1] = x, y
        ix = np.clip(x.astype(np.int32), 0, nx - 1)
        iy = np.clip(y.astype(np.int32), 0, ny - 1)
        a = theta[iy, ix] + off + wiggle * np.sin(ph + fr * i * 0.7)
        x = x + np.cos(a) * step
        y = y + np.sin(a) * step
    return out


def draw_strokes(shape, lines, values, widths, shift=3):
    """Antialiased polylines into a float image, bucketed by (value, width). lines: list of (m, 2) arrays. Adds up where they cross."""
    ny, nx = shape
    img = np.zeros(shape, np.float32)
    values = np.asarray(values)
    widths = np.asarray(widths)
    vb = np.clip((values * 6).astype(np.int32), 0, 6)
    scale = 1 << shift
    for w in np.unique(widths):
        for b in np.unique(vb[widths == w]):
            idx = np.nonzero((widths == w) & (vb == b))[0]
            if len(idx) == 0:
                continue
            c = np.zeros(shape, np.uint8)
            pts = [np.round(lines[i] * scale).astype(np.int32) for i in idx]
            cv2.polylines(c, pts, False, 255, int(w), cv2.LINE_AA, shift)
            img += c.astype(np.float32) / 255.0 * ((b + 0.5) / 6.0)
    return img


def advect_blur(f, theta, cm_per_pass, pxcm, passes=4):
    """Bleed a field along the grain: repeated averaging along the flow, as a stain wicks along fibres."""
    ny, nx = f.shape
    Y, X = np.mgrid[:ny, :nx].astype(np.float32)
    dx, dy = (np.cos(theta) * cm_per_pass * pxcm).astype(np.float32), (np.sin(theta) * cm_per_pass * pxcm).astype(np.float32)
    for _ in range(passes):
        a = cv2.remap(f, X + dx, Y + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        b = cv2.remap(f, X - dx, Y - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        f = 0.5 * f + 0.25 * (a + b)
    return f


def crack_paths(shape, pxcm, theta, seed, n_main, len_main, branch=0.5, angle=0.5, jag=0.016, starts=None):
    """Hair cracks as polylines: a main crack walks at an angle to the grain, jagged at the small scale; it throws side cracks at acute angles.
    Returns a list of (points, strength along the path, generation)."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    paths = []

    def walk(x, y, a0, L, gen):
        ds = 0.02
        m = max(4, int(L / ds))
        pts = np.zeros((m, 2), np.float32)
        a = a0
        # kinks: a crack runs straight, then turns; not a smooth curve
        for i in range(m):
            pts[i] = x, y
            if rng.random() < 0.05:
                a = a0 + rng.normal(0, 0.45)
            jit = rng.normal(0, 1) * jag * pxcm * 0.5
            x += np.cos(a) * ds * pxcm - np.sin(a) * jit
            y += np.sin(a) * ds * pxcm + np.cos(a) * jit
            a0 += rng.normal(0, 0.012)
            if gen < 2 and rng.random() < 0.02 * branch:
                side = rng.choice([-1, 1])
                walk(x, y, a + side * rng.uniform(0.35, 1.0), L * rng.uniform(0.12, 0.45), gen + 1)
        # strength: pinches and fades, tapering at both ends
        t = np.linspace(0, 1, m)
        s = np.minimum(1.0, 6 * t) * np.minimum(1.0, 3.5 * (1 - t))
        w = np.interp(np.arange(m), np.sort(rng.integers(0, m, max(3, m // 18))), rng.uniform(0.0, 1.0, max(3, m // 18)))
        s = s * sstep(0.12, 0.5, w)
        paths.append((pts, s.astype(np.float32), gen))

    for i in range(n_main):
        if starts is not None and i < len(starts):
            x, y = starts[i][0] * nx, starts[i][1] * ny
        else:
            x, y = rng.uniform(0, nx), rng.uniform(0, ny)
        ix, iy = int(np.clip(x, 0, nx - 1)), int(np.clip(y, 0, ny - 1))
        a0 = theta[iy, ix] + rng.normal(0, angle)
        walk(x, y, a0, rng.uniform(0.5, 1.0) * len_main, 0)
    return paths


def draw_cracks(shape, paths, offset=(0.0, 0.0), width=1.0, gen_fade=(1.0, 0.55, 0.28)):
    """Draw crack polylines with a per-segment strength into a float image; the whole set is shifted by `offset` px (a crack is a dipping sheet)."""
    lines, vals, wids = [], [], []
    ox, oy = offset
    for pts, s, gen in paths:
        n = len(pts)
        k = 0
        while k < n - 1:
            e = min(n, k + 6)
            v = float(s[k:e].mean()) * gen_fade[gen]
            if v > 0.03:
                lines.append(pts[k:e] + np.array([ox, oy], np.float32))
                vals.append(v)
                wids.append(max(1, int(round(width * (0.7 + 1.2 * v) * (1.0 if gen == 0 else 0.7)))))
            k = e - 1
    if not lines:
        return np.zeros(shape, np.float32)
    return draw_strokes(shape, lines, vals, wids)


def surface_frame(P, U, V):
    """Normals from the grid, and for each vertex the inverse metric: world tangent vector -> (dU, dV)."""
    Pu = np.gradient(P, axis=1)
    Pv = np.gradient(P, axis=0)
    n = np.cross(Pu, Pv)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    Uj, Ui = np.gradient(U, axis=1), np.gradient(U, axis=0)
    Vj, Vi = np.gradient(V, axis=1), np.gradient(V, axis=0)
    return n, Pu, Pv, Uj, Ui, Vj, Vi


def refract(n, v, eta):
    """n and v unit, v towards the camera, n outward; returns the inside direction and cos of the inside angle."""
    ci = np.clip((n * v).sum(-1, keepdims=True), 0.02, 1.0)
    k = np.sqrt(np.maximum(1.0 - eta * eta * (1.0 - ci * ci), 0.0))
    t = -eta * v + (eta * ci - k) * n
    t /= np.linalg.norm(t, axis=-1, keepdims=True) + 1e-12
    return t, k


def ellipsoid_exit(X, d, abc):
    """Distance from an inside point X along unit vector(s) d to the ellipsoid (a, b, c). Non-negative."""
    s = X / abc
    dv = d / abc
    A = (dv * dv).sum(-1)
    B = (s * dv).sum(-1)
    C = (s * s).sum(-1) - 1.0
    disc = np.maximum(B * B - A * C, 0.0)
    return np.maximum((-B + np.sqrt(disc)) / A, 0.0)


def sample(tex, mapx, mapy):
    return cv2.remap(tex, mapx.astype(np.float32), mapy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
