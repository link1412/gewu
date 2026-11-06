"""Helpers shared by shots 21, 15, 34, 39, 40, 31, 16."""

import os

import cv2
import numpy as np

SHEETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s21_sheets.py")


def ribbons(lines, widths, cam, attrs=None, keep=None):
    """Lines (n, ns, 3), widths (n, ns) half-width in cm -> one strand mesh with 3 rows per line, facing the camera.

    A slight ridge along the centre gives it a round normal. attrs: {name: (n, ns) or (n, ns, 3)}. Returns (P, attrs).
    """
    n, ns = lines.shape[:2]
    t = np.gradient(lines, axis=1)
    v = np.array(cam, np.float32) - lines
    s = np.cross(t, v)
    s = s / (np.linalg.norm(s, axis=-1, keepdims=True) + 1e-9)
    f = v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)
    w = widths[..., None]
    P = np.stack([lines - s * w, lines + f * w * 0.9, lines + s * w], 1).reshape(n * 3, ns, 3)
    out = {}
    for k, a in (attrs or {}).items():
        out[k] = np.repeat(a, 3, axis=0).astype(np.float32)
    if keep is not None:
        out["keep"] = np.repeat(keep, 3, axis=0).astype(np.float32)
    return P.astype(np.float32), out


def strokes(shape, lines, widths=1, values=None, ss=8):
    """Antialiased polylines on a raster: lines is a list of (m, 2) arrays in (x, y) pixels. Keeps the max of the values."""
    img = np.zeros(shape, np.float32)
    values = np.ones(len(lines)) if values is None else values
    widths = np.full(len(lines), widths) if np.isscalar(widths) else widths
    # group by quantised value so that one call draws many
    q = np.round(np.asarray(values) * 12) / 12
    for v in np.unique(q):
        for w in np.unique(widths):
            sel = [(l * 8).astype(np.int32) for l, a, b in zip(lines, q, widths) if a == v and b == w]
            if sel:
                layer = np.zeros(shape, np.float32)
                cv2.polylines(layer, sel, False, float(v), int(w), cv2.LINE_AA, shift=3)
                img = np.maximum(img, layer)
    return img


def smooth1d(n, sigma, rng):
    x = rng.standard_normal(n + 8 * int(sigma + 1)).astype(np.float32)
    x = cv2.GaussianBlur(x[None, :], (0, 0), float(sigma), borderType=cv2.BORDER_REFLECT)[0][4 * int(sigma + 1) :][:n]
    return (x - x.mean()) / (x.std() + 1e-9)


def up(f, ny, nx, sigma=None):
    """Open a field from a fixed grid, then blur by about the zoom, so that highlights do not ripple."""
    g = cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)
    z = max(nx / f.shape[1], ny / f.shape[0]) if sigma is None else sigma
    return cv2.GaussianBlur(g, (0, 0), float(z)) if z > 1.2 else g


def look_at_camera(C, T, lens, focus, aperture_mm=None, roll=0.0):
    C, T, focus = (np.array(a, float) for a in (C, T, focus))
    d = (C - T) / np.linalg.norm(C - T)
    cam = {"loc": C.tolist(), "target": T.tolist(), "lens_mm": float(lens), "roll": float(roll), "shift": [0.0, 0.0]}
    if aperture_mm:
        cam["aperture_mm"] = float(aperture_mm)
        cam["focus_distance"] = float(np.dot(C - focus, d))
    return cam


def sheet_mesh(name, npz, params):
    return {"name": name, "npz": npz, "shader_py": SHEETS, "params": params}


def montage(path, paths, scale=0.5):
    ims = [cv2.imread(p) for p in paths]
    ims = [cv2.resize(i, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) for i in ims]
    cv2.imwrite(path, np.vstack(ims))


def crops(src, dst, boxes, tile=1000):
    """100 % crops, side by side. boxes as (x, y) top-left fractions; tile px wide each."""
    im = cv2.imread(src)
    h, w = im.shape[:2]
    out = []
    for fx, fy in boxes:
        x, y = int(fx * w), int(fy * h)
        out.append(im[y : y + tile, x : x + tile])
    cv2.imwrite(dst, np.hstack(out), [cv2.IMWRITE_JPEG_QUALITY, 92])
