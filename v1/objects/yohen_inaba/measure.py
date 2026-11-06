"""Edges of the Inaba tenmoku in the 1937 side view (ref/yohen/images/inaba_commons_1937.jpg, upper plate), for
form.py's fit.

    python3 -I objects/yohen_inaba/measure.py      -> out/yohen/form/edges.json, edges.png

The plate (Takahashi, Taisho meiki kan 6, 1937; Commons, PD-Japan-oldphoto) shows the bowl against a plain light
ground from a little above. Measured, in the photo's pixels (x right, y down), subpixel:
  outline_top     the silhouette above the line joining its leftmost and rightmost points (the far lip)
  outline_side    the silhouette below that line, down to the wall's lowest point on either side
  outline_bottom  the silhouette below that (the foot ring and the underside next to it)
  lip_front       the lower edge of the light band along the near lip (the lip's thin glaze seen from above): the
                  near lip's outer contour
The silhouette is the iso-line of the smoothed grey level halfway between the ground (~238) and the bowl (~75). The
lip band is tracked as a ridge of brightness from a seed column outwards; its lower edge is the steepest fall below
the ridge.
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage.measure import find_contours

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PHOTO = os.path.join(ROOT, "ref/yohen/images/inaba_commons_1937.jpg")
OUT = os.path.join(ROOT, "out/yohen/form")
UPPER_ROWS = 1500          # the upper plate (the side view); the lower one is a top view
LEVEL = 0.5 * (238 + 75)   # halfway between the ground and the bowl (grey levels measured on the plate)
GROUND_LEVEL = 230.0      # the ground is 236-241; brighter than this and joined to the border: ground (the far lip on the right is 200-222)
NEAR = 3.0                # px
LIP_SEED = (700, 518)      # a column where the near lip's band is clear, and the band's row there (by eye)
LIP_X = (330, 1880)        # the band is followed over these columns (beyond: it turns into the silhouette)
LIP_SKIP = (1250, 1700)    # ... except here: a highlight on the far wall inside sits on the band [by eye]


def silhouette(g):
    """The outer silhouette. The iso-line at LEVEL is exact where the bowl is dark, but the lip's light band on the
    far right is nearly as light as the ground and the line leaks through it into the bright interior there. So the
    ground is first found as the near-white region joined to the plate's border (GROUND_LEVEL); points of the iso-line
    within NEAR px of that region's edge are kept, and where there are none (the light lip) the region's edge itself
    is used (it sits ~1 px outside a dark edge, closer on a light one)."""
    bg = g > GROUND_LEVEL
    lab, _ = ndi.label(bg)
    border = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    bg = np.isin(lab, border[border > 0])
    bowl = ndi.binary_fill_holes(~bg)
    lab, n = ndi.label(bowl)
    bowl = lab == (1 + int(np.argmax(ndi.sum(bowl, lab, range(1, n + 1)))))
    E = max(find_contours(ndi.gaussian_filter(bowl.astype(float), 0.7), 0.5), key=len)
    E = np.c_[E[:, 1], E[:, 0]]
    I = np.vstack([np.c_[c[:, 1], c[:, 0]] for c in find_contours(g, LEVEL) if len(c) > 50])
    tE, tI = cKDTree(E), cKDTree(I)
    dI, _ = tE.query(I)
    keep_I = I[dI < NEAR]
    dE, _ = tI.query(E)
    fill_E = E[dE >= NEAR]
    S = np.vstack([keep_I, fill_E])
    # order along the outline (by angle about the bowl's centroid) for the plots
    c = S.mean(0)
    return S[np.argsort(np.arctan2(S[:, 1] - c[1], S[:, 0] - c[0]))], len(fill_E)


def lip_band(g):
    gx = ndi.gaussian_filter(g, 1.5)
    out = []
    for direction in (-1, 1):
        x, y = LIP_SEED
        while LIP_X[0] <= x <= LIP_X[1]:
            col = gx[int(y) - 12:int(y) + 13, x - 2:x + 3].mean(1)
            i = int(np.argmax(col))
            y = int(y) - 12 + i
            if not (LIP_SKIP[0] <= x <= LIP_SKIP[1]):
                prof = gx[y:y + 20, x - 2:x + 3].mean(1)
                d = np.diff(prof)
                j = int(np.argmin(d))
                if 1 <= j < len(d) - 1 and prof[0] - prof[-1] > 20:
                    # subpixel: the parabola through the steepest fall and its neighbours
                    a, b, c = d[j - 1], d[j], d[j + 1]
                    off = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
                    out.append((float(x), y + j + 0.5 + off))
            x += 4 * direction
    out.sort()
    return np.array(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    img = np.asarray(Image.open(PHOTO).convert("L")).astype(float)[:UPPER_ROWS]
    g = ndi.gaussian_filter(img, 1.0)
    S, n_fill = silhouette(g)
    iL, iR = int(np.argmin(S[:, 0])), int(np.argmax(S[:, 0]))
    (xl, yl), (xr, yr) = S[iL], S[iR]
    above = S[:, 1] < yl + (S[:, 0] - xl) * (yr - yl) / (xr - xl)
    # the wall's lowest point on either side: where the outline turns inward sharply onto the underside/foot. Taken
    # as the bottom rows of the side outline: below the row where the silhouette is still wider than the foot band
    # by more than 40 px on both sides
    W = img.shape[1]
    bottom_y = S[:, 1].max()
    rows = np.arange(int(yl), int(bottom_y))
    widths = []
    for y in rows:
        xs = S[np.abs(S[:, 1] - y) < 0.5, 0]
        widths.append(xs.max() - xs.min() if len(xs) else 0)
    widths = np.array(widths)
    # the foot ring: the bottom ~120 px have a nearly constant width; the wall above narrows quickly into it
    foot_w = np.median(widths[-60:-20])
    y_foot = rows[np.nonzero(widths > foot_w + 40)[0][-1]]
    side = ~above & (S[:, 1] <= y_foot)
    bottom = ~above & (S[:, 1] > y_foot)
    lip = lip_band(img)
    sets = {"outline_top": S[above], "outline_side": S[side], "outline_bottom": S[bottom], "lip_front": lip}
    J = {"photo": os.path.relpath(PHOTO, ROOT), "photo_size_px": [W, UPPER_ROWS],
         "level": LEVEL, "ground_level": GROUND_LEVEL, "outline_points_from_ground_edge": int(n_fill), "extremes_px": {"left": [round(xl, 2), round(yl, 2)], "right": [round(xr, 2), round(yr, 2)]},
         "y_wall_bottom_px": int(y_foot), "foot_band_width_px": round(float(foot_w), 1),
         "sets": {k: np.round(v, 3).tolist() for k, v in sets.items()}}
    json.dump(J, open(os.path.join(OUT, "edges.json"), "w"))
    rgb = np.stack([img] * 3, -1).astype(np.uint8)
    col = {"outline_top": (255, 0, 0), "outline_side": (0, 200, 0), "outline_bottom": (0, 120, 255),
           "lip_front": (255, 200, 0)}
    for k, P in sets.items():
        for x, y in P:
            xi, yi = int(round(x)), int(round(y))
            rgb[max(yi - 1, 0):yi + 2, max(xi - 1, 0):xi + 2] = col[k]
    Image.fromarray(rgb).save(os.path.join(OUT, "edges.png"))
    print({k: len(v) for k, v in sets.items()}, "left", (round(xl), round(yl)), "right", (round(xr), round(yr)),
          "wall bottom y", int(y_foot), "foot band", round(float(foot_w)))


if __name__ == "__main__":
    main()
