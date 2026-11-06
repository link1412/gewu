"""The vessel of shot 6: a Southern Song Guan vase with a globular belly and bowstring ribs
(弦纹瓶 type), and the framing that puts the curve of its belly on the arc of the original shot.

Form: the profile r(z) is measured from the silhouette of the Palace Museum's 官窑青釉弦纹瓶
(photo by Siyuwj, 2016, CC BY-SA 4.0, ref/guan/pm_xianwenping_siyuwj.jpg; reference only, the
photo is not in the film). Lengths come out in units of the belly radius R_b.

Scale: the Palace Museum piece's dimensions were not found. We take the belly diameter of a Guan
vase of the same type, Freer Gallery F1911.338 (Jiaotanxia kiln, 23.2 x 14.1 cm), as ours:
R_b = 70.5 mm. This is a choice, not a measurement of the pictured vase.

Framing: the camera is rolled 90 degrees so the vase's axis is horizontal in the frame; the
belly's side silhouette is the arc at the top of the frame, its apex at the widest point, and
the turntable turns the surface out of the limb and down the frame, as the sphere in the
original turns. The arc's radius is the meridian curvature R_m at the widest point; the
original's arc has R = 1.22 x frame width (spec/shots.json), which fixes the frame width.

    python3 -I shots/06-guan/form.py ref/guan/pm_xianwenping_siyuwj.jpg shots/06-guan/form.json
"""

import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

BELLY_DIAMETER_MM = 141.0   # Freer F1911.338, same type (see above)
ARC_R_OVER_W = 1.22         # spec/shots.json, shot 6
FIT_HALF_WINDOW = 0.25      # fit the meridian circle over |z| <= this * R_b


def silhouette(path, rows=(240, 780), belly_from=500, step_px=4):
    """Left and right edges of the vase, row by row (sub-pixel, at the steepest gradient).
    rows (in 1/1000 of the image height): from below the lip's shadow on the neck to just above
    the foot, where the acrylic mounts begin. The case behind is at luma ~10; the neck's shaded
    side is dim (threshold 25), and below belly_from the display stand shows behind the bright
    belly (threshold 70)."""
    im = np.asarray(Image.open(path).convert("L"), float)
    f = im.shape[0] / 1000.0
    L = ndimage.gaussian_filter(im, 2.0)
    ys, edges = [], []
    for y in range(int(rows[0] * f), int(rows[1] * f), step_px):
        row = L[y]
        threshold = 25.0 if y < belly_from * f else 70.0
        bright = np.nonzero(row > threshold)[0]
        if len(bright) == 0:
            raise SystemExit(f"row {y}: no vase found above luma {threshold}")
        e = []
        for x0, sign in ((bright.min(), 1), (bright.max(), -1)):
            lo = max(int(x0) - 40, 1)
            g = np.gradient(row[lo:int(x0) + 40]) * sign
            k = int(np.argmax(g))
            d = 0.0
            if 0 < k < len(g) - 1:
                d = 0.5 * (g[k - 1] - g[k + 1]) / (g[k - 1] - 2 * g[k] + g[k + 1] + 1e-9)
            e.append(lo + k + d)
        ys.append(y)
        edges.append(e)
    return np.array(ys, float), np.array(edges)


def fit_circle(z, r):
    """Least-squares circle through (z, r): radius, centre, max |residual|."""
    A = np.c_[2 * z, 2 * r, np.ones_like(z)]
    (zc, rc, k), *_ = np.linalg.lstsq(A, z ** 2 + r ** 2, rcond=None)
    R = float(np.sqrt(k + zc ** 2 + rc ** 2))
    res = np.sqrt((z - zc) ** 2 + (r - rc) ** 2) - R
    return R, float(zc), float(rc), float(np.abs(res).max())


def main():
    src, out = sys.argv[1], sys.argv[2]
    ys, e = silhouette(src)
    r = (e[:, 1] - e[:, 0]) / 2
    axis_x = float(np.median((e[:, 1] + e[:, 0]) / 2))
    i0 = int(np.argmax(r))
    rb_px, y_eq = float(r[i0]), float(ys[i0])
    z = (ys - y_eq) / rb_px                       # down the image = towards the foot
    m = np.abs(z) <= FIT_HALF_WINDOW
    R_m, zc, rc, resid = fit_circle(z[m], r[m] / rb_px)
    rb_mm = BELLY_DIAMETER_MM / 2
    frame_w_mm = R_m * rb_mm / ARC_R_OVER_W
    J = {
        "source": "Palace Museum 官窑青釉弦纹瓶, photo Siyuwj 2016-09-11, CC BY-SA 4.0 (reference only)",
        "units": "z and r in belly radii R_b; z = 0 at the widest point, positive towards the foot",
        "axis_x_px": round(axis_x, 1),
        "belly_radius_px": round(rb_px, 1),
        "profile": [[round(float(a), 4), round(float(b), 4)] for a, b in zip(z, r / rb_px)],
        "meridian": {"R_m_over_Rb": round(R_m, 4), "centre_z": round(zc, 4),
                     "fit_half_window": FIT_HALF_WINDOW, "max_resid_over_Rb": round(resid, 4)},
        "scale": {"belly_diameter_mm": BELLY_DIAMETER_MM,
                  "why": "belly diameter of Freer F1911.338, a Guan bowstring vase of the same type; "
                         "the pictured vase's size was not found"},
        "framing": {"arc_R_over_W": ARC_R_OVER_W, "R_m_mm": round(R_m * rb_mm, 2),
                    "frame_width_mm": round(frame_w_mm, 2),
                    "frame_half_span_over_Rb": round(frame_w_mm / 2 / rb_mm, 4),
                    "magnification_full_frame": round(36.0 / frame_w_mm, 3)},
    }
    with open(out, "w") as f:
        json.dump(J, f, indent=1, ensure_ascii=False)
    print(f"widest point at row {y_eq:.0f}, R_b = {rb_px:.0f} px; meridian R_m = {R_m:.3f} R_b "
          f"(fit over |z| <= {FIT_HALF_WINDOW}, max residual {resid * 100:.2f}% R_b)")
    print(f"R_b = {rb_mm} mm -> R_m = {R_m * rb_mm:.1f} mm, frame width {frame_w_mm:.1f} mm "
          f"(+-{frame_w_mm / 2 / rb_mm:.3f} R_b along the axis), {36.0 / frame_w_mm:.2f}x on full frame")


if __name__ == "__main__":
    main()
