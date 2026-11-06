"""青花's first look: a dish in the form of the Met's Kangxi plate 18.61.2, painted with that plate's own pattern
(inverted from its photograph to the cobalt's column density c), in the Kangxi set and in the modern set
(docs/materials/qinghua.md, "first look").

    python3 -I materials/qinghua/dish.py map               # the photo's whole plate -> c (out/materials/qinghua/dish/)
    python3 -I materials/qinghua/dish.py object --set kangxi|modern     # the dish's meshes and pbrt fragment
    python3 -I tools/build.py materials/qinghua/recipes/dish-kangxi.json --preview

A stand-in: the pattern is borrowed from Met 18.61.2 (CC0), not painted by our craft (crafts/painting).

- Form [A]: a plain Kangxi saucer dish's profile (a flat well, a rounded cavetto, a rounded lip, a foot ring of 0.56
  the width), drawn by us at the Met's size (W 16.5 cm, H 3.8 cm [I]); the photo is taken from above, so it shows no
  profile. The rim's ten lobes are the photo's outline [M]: its radius against angle, as a fraction of its largest,
  applied to the cavetto and rim (the well and the foot stay round).
- Pattern: the photo's linear sRGB over its white, its slow shading taken out (the white glaze's brightness, smoothed
  over 8 mm, divided out), inverted pixel by pixel through the 1-D stack with the iron-like companion fitted on the
  card (card.py measure, the same locus as the card's "iron" map), the ground's floor subtracted; the brown dressed
  lip (the outer 1.8 mm) and everything outside the outline left unpainted. Projected straight down onto the dish
  (the photo's own view), so the map covers the inside up to the lip.
- Both sets carry the same c: the Kangxi set renders it with the companion and the tinted body, the modern set with
  cobalt alone and a white body (material.json).

World (the object's frame): mm, z up, the dish standing on z = 0, its axis on z. The photo's top is +y; the photo is
mirrored in x on the way in (pbrt's left-handed world, make_map), so pbrt and Cycles show the plate the right way round.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import make_interp_spline

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
sys.path.insert(0, os.path.join(ROOT, "tests/optics"))
import card  # noqa: E402
import optics  # noqa: E402
from camera import LAM  # noqa: E402
from studio import write_ply  # noqa: E402

OUT = os.path.join(ROOT, "out/materials/qinghua/dish")
W_MM, H_MM = 165.0, 38.0       # [I] the Met's record for 18.61.2
MAP_HALF = 85.0                # the map covers x, y in [-85, 85] mm
MAP_PX_MM = 6.679              # half the photo's scale
LIP_MM = 1.8                   # the brown dressed lip, left unpainted [M, read off the photo]
SHADE_MM = 8.0                 # the white's shading, smoothed over this
STEP = 0.5                     # mm along the profile
N_AROUND = 720
GAP = 0.004                    # mm, the film above the body (tools/coat.py's film_gap)


# --- the photo ------------------------------------------------------------------------------------
def photo_linear(scale=2):
    im = Image.open(os.path.join(ROOT, card.PHOTO)).convert("RGB")
    im = im.resize((im.size[0] // scale, im.size[1] // scale), Image.LANCZOS)
    return card.srgb_decode(np.asarray(im).astype(np.float64) / 255)


def outline(lin, pxmm, lobes_n=10):
    """The plate in the photo: its centre (px) and its rim's radius (mm) against angle (720 bins, world angle: x
    right, y up). The backdrop brightens toward the bottom of the photo until it is as bright as the glaze, so only the
    upper part of the outline is used [M]: a circle fit gives the centre; the radius, folded over the ten lobes
    (a moulded dish, ten-fold [A]) and taken as the median over the lobes seen, gives one lobe's shape, repeated."""
    g = lin.mean(-1)
    bg = np.median(g[:, :150], axis=1)
    row_lim = int(np.argmax(bg > 0.12)) - 10                         # the backdrop still dark above this row
    dark = ndi.binary_opening(g < 0.12, iterations=2)                # the backdrop (and some deep blue)
    lab, _ = ndi.label(dark)
    back = np.isin(lab, np.unique(lab[0][lab[0] > 0]))               # the dark regions that reach the top edge
    m = ~back[:row_lim]
    # the outline's points: the first plate pixel from the left and from the right in each row, from the top in
    # each column (only these are certain to face the dark backdrop)
    rows = np.nonzero(m.any(1))[0]
    cols = np.nonzero(m.any(0))[0]
    xx = np.r_[[np.argmax(m[y]) for y in rows], [m.shape[1] - 1 - np.argmax(m[y][::-1]) for y in rows], cols]
    yy = np.r_[rows, rows, [np.argmax(m[:, x]) for x in cols]].astype(float)
    xx = xx.astype(float)
    keep = np.ones(len(xx), bool)
    for _ in range(4):                                               # fit, drop the far points, fit again
        A = np.c_[xx[keep], yy[keep], np.ones(keep.sum())]
        D, E, F = np.linalg.lstsq(A, -(xx[keep] ** 2 + yy[keep] ** 2), rcond=None)[0]
        cx, cy, r0 = -D / 2, -E / 2, np.sqrt(D * D / 4 + E * E / 4 - F)
        keep = np.abs(np.hypot(xx - cx, yy - cy) - r0) < 6 * pxmm
    xx, yy = xx[keep], yy[keep]
    th = np.degrees(np.arctan2(-(yy - cy), xx - cx))
    r = np.hypot(xx - cx, yy - cy) / pxmm
    ok = (th > 5) & (th < 175)
    period = 360.0 / lobes_n
    nb = 72
    ph = ((th[ok] % period) / period * nb).astype(int) % nb
    lobe = (th[ok] // period).astype(int)
    tab = np.full((lobes_n, nb), np.nan)
    for L in np.unique(lobe):
        sel = lobe == L
        v = np.full(nb, np.nan)
        np.fmax.at(v, ph[sel], r[ok][sel])
        tab[L] = v
    one = np.nanmedian(tab, 0)
    one = np.interp(np.arange(nb), np.nonzero(~np.isnan(one))[0], one[~np.isnan(one)], period=nb)
    one = ndi.uniform_filter1d(one, 3, mode="wrap")
    thb = (np.arange(720) + 0.5) / 2 - 180.0
    R = np.interp((thb % period) / period * nb - 0.5, np.arange(nb), one, period=nb)
    return (cx, cy), R, {"row_limit": row_lim, "edge_px": int(ok.sum()), "lobes_seen": int(np.isfinite(tab).any(1).sum()),
                         "circle_fit_r_mm": float(r0 / pxmm)}


def make_map(a):
    os.makedirs(OUT, exist_ok=True)
    M = json.load(open(card.OUT_M))
    # pbrt's world is left-handed: seen from above (+z), +x is to the left of +y. So the photo is mirrored left to
    # right here, and the dish then reads like the photo from above (card.py mirrors its map for the same reason)
    lin = photo_linear()[:, ::-1]
    pxmm = M["scale"]["px_per_mm"] / 2
    (cx, cy), R, how = outline(lin, pxmm)
    white = np.array(M["white_linear"])
    q = lin / white
    Y = q @ np.array([0.2126, 0.7152, 0.0722])
    yy, xx = np.mgrid[:lin.shape[0], :lin.shape[1]]
    th = np.arctan2(-(yy - cy), xx - cx)
    rr = np.hypot(xx - cx, yy - cy) / pxmm
    Rth = R[((th + np.pi) / (2 * np.pi) * 720).astype(int) % 720]
    inside = rr < Rth - LIP_MM
    ground = inside & (q[..., 2] >= 0.80) & (q[..., 2] / np.maximum(q[..., 0], 1e-4) < 1.25)
    s = SHADE_MM * pxmm
    num = ndi.gaussian_filter(np.where(ground, Y, 0.0), s)
    den = ndi.gaussian_filter(ground.astype(float), s)
    shade = np.where(den > 0.02, num / np.maximum(den, 1e-9), 1.0)
    shade = np.clip(shade / np.median(shade[ground]), 0.6, 1.4)
    q = q / shade[..., None]
    mp = M["maps"]["iron"]
    kappa = optics.cobalt_kappa() + optics.iron_like_kappa(mp["companion"]["fe3"], mp["companion"]["fe2"])
    loc = card.Locus(card.material_set("kangxi"), kappa, np.linspace(*mp["c_grid"][:2], mp["c_grid"][2]))
    # only the plate's box
    ys, xs = np.nonzero(inside)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    c = np.zeros(Y.shape)
    cb, _ = loc.invert(q[y0:y1, x0:x1], chunk=4000)
    c[y0:y1, x0:x1] = cb
    floor = float(np.percentile(c[ground], 99))
    c = np.where(inside, np.maximum(c - floor, 0.0), 0.0)
    # resample onto the map's square grid (row 0 = y +MAP_HALF), world x right, y up
    n = int(round(2 * MAP_HALF * MAP_PX_MM))
    t = -MAP_HALF + (np.arange(n) + 0.5) / MAP_PX_MM
    X, Yw = np.meshgrid(t, t[::-1])
    px, py = cx + X * pxmm, cy - Yw * pxmm
    cm = ndi.map_coordinates(c, [py, px], order=1, mode="constant", cval=0.0)
    write_pfm(os.path.join(OUT, "c.pfm"), cm)
    Image.fromarray((255 * np.clip(1 - cm / 4, 0, 1)).astype(np.uint8)).save(os.path.join(OUT, "c_preview.png"))
    info = {"photo": card.PHOTO, "scale_px_per_mm": pxmm, "centre_px": [cx, cy],
            "rim_radius_mm": {"max": float(R.max()), "min": float(R.min()), "mean": float(R.mean())}, "outline": how,
            "lobes": "R(theta) / max, 720 bins (rim_radius.npy)", "ground_floor_c": floor,
            "shading": {"smooth_mm": SHADE_MM, "range": [float(shade[inside].min()), float(shade[inside].max())]},
            "locus": "card.py measure's iron map (fe3, fe2) on the Kangxi set", "c_max": float(cm.max()),
            "map": {"half_mm": MAP_HALF, "px_per_mm": MAP_PX_MM, "size": n}}
    np.save(os.path.join(OUT, "rim_radius.npy"), R)
    json.dump(info, open(os.path.join(OUT, "map.json"), "w"), indent=1)
    print(json.dumps(info, indent=1))


def write_pfm(path, img):
    """One channel; img rows top first."""
    img = np.ascontiguousarray(img, dtype="<f4")
    with open(path, "wb") as f:
        f.write(f"Pf\n{img.shape[1]} {img.shape[0]}\n-1.0\n".encode())
        f.write(img[::-1].tobytes())


# --- the form --------------------------------------------------------------------------------------
def _spline(P, step=STEP):
    P = np.asarray(P, float)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    sp = make_interp_spline(s, P, k=3, bc_type="natural")
    t = np.linspace(0, s[-1], max(int(s[-1] / step), 2) + 1)
    return sp(t)


def profile():
    """The glaze's outer surface, (r, z) mm, one run from the axis inside the well, out and up the cavetto, over the
    lip, down the outside, round the foot ring, to the axis under the base [A, our drawing at the Met's size]."""
    rl, zl, rad = W_MM / 2 - 1.0, H_MM - 1.0, 1.0           # the lip: a half round of radius 1 mm on top
    floor = np.c_[np.linspace(0, 30, 61), np.full(61, 9.0)]
    inside = _spline([(30, 9.0), (45, 10.6), (58, 14.6), (68, 20.2), (75, 26.6), (79.2, 32.4), (rl - rad, zl)])
    a = np.linspace(np.pi, 0, 13)
    lip = np.c_[rl + rad * np.cos(a), zl + rad * np.sin(a)]
    outside = _spline([(rl + rad, zl), (80.6, 31.0), (76.2, 24.0), (68.0, 16.4), (58.0, 11.0), (50.5, 8.0),
                       (46.6, 6.4)])
    foot = _spline([(46.6, 6.4), (46.2, 3.0), (46.0, 0.8), (45.4, 0.0)])
    sole = np.c_[np.linspace(45.4, 42.4, 7), np.zeros(7)]
    inner = _spline([(42.4, 0.0), (41.9, 0.8), (41.4, 3.5), (40.4, 5.0)])
    base = np.c_[np.linspace(40.4, 0, 81), 5.0 + 0.5 * (1 - (np.linspace(40.4, 0, 81) / 40.4) ** 2)]
    P = np.vstack([floor, inside[1:], lip[1:], outside[1:], foot[1:], sole[1:], inner[1:], base[1:]])
    keep = np.r_[True, np.hypot(*np.diff(P, axis=0).T) > 1e-6]
    P = P[keep]
    n_inside = len(floor) + len(inside) - 1 + len(lip) // 2      # up to the lip's top
    return P[:, 0], P[:, 1], n_inside


def lobes(P, Rth):
    """Move points radially by the photo's lobes: r (1 + d(theta) b(r)), d = R(theta)/max - 1, b from 0 at r 48 to 1
    at r 80 (the well, the lower cavetto and the foot stay round)."""
    d = Rth / Rth.max() - 1.0
    r = np.hypot(P[:, 0], P[:, 1])
    th = np.arctan2(P[:, 1], P[:, 0])
    f = (th + np.pi) / (2 * np.pi) * 720 - 0.5
    i0 = np.floor(f).astype(int) % 720
    w = f - np.floor(f)
    dd = d[i0] * (1 - w) + d[(i0 + 1) % 720] * w
    b = np.clip((r - 48.0) / 32.0, 0, 1)
    b = b * b * (3 - 2 * b)
    k = 1 + dd * b
    return np.c_[P[:, 0] * k, P[:, 1] * k, P[:, 2]]


def vertex_normals(P, T, N_ref):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for j in range(3):
        np.add.at(N, T[:, j], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    flip = np.einsum("ij,ij->i", N, N_ref) < 0
    N[flip] *= -1
    return N


def make_object(a):
    import gen_object as G
    ms = material_set_full(a.set)
    h = ms["h"]
    R, Z, n_in = profile()
    glaze = [(R, Z)]
    body = G.offset(glaze, h)
    Rb, Zb = body[0]
    # the film: the body's inside, up to the lip's top, moved GAP into the glaze along its normal
    fr, fz = Rb[:n_in], Zb[:n_in]
    nf = G.normals2d(fr, fz)
    film = [(np.r_[0.0, (fr + GAP * nf[:, 0])[1:]], fz + GAP * nf[:, 1])]
    Rth = np.load(os.path.join(OUT, "rim_radius.npy"))
    d = os.path.join(OUT, a.set)
    os.makedirs(d, exist_ok=True)
    for name, pieces in (("glaze", glaze), ("body", body), ("film", film)):
        P, N, T = G.revolve(pieces, N_AROUND)
        P = lobes(P, Rth)
        N = vertex_normals(P, T, N)
        uv = None
        if name == "film":
            uv = np.c_[(P[:, 0] + MAP_HALF) / (2 * MAP_HALF), (P[:, 1] + MAP_HALF) / (2 * MAP_HALF)]
        write_ply(os.path.join(d, f"dish_{name}.ply"), P, N, T, uv)
    grid = np.linspace(*json.load(open(card.OUT_M))["maps"]["iron"]["c_grid"][:2], 1001)
    np.savez(os.path.join(d, "film.npz"), lambda_nm=LAM, c=grid, R=optics.film_family(ms["kappa"], grid))
    open(os.path.join(d, "c.pfm"), "wb").write(open(os.path.join(OUT, "c.pfm"), "rb").read())
    with open(os.path.join(d, "dish.pbrt"), "w") as f:
        f.write(f"""# 青花 first look (materials/qinghua/dish.py): a dish in Met 18.61.2's form, {W_MM:g} x {H_MM:g} mm, its
# pattern borrowed from that plate's photograph (CC0), set "{a.set}" (materials/qinghua/material.json)
Texture "qh_co" "spectrum" "familymap" "string family" "film.npz" "string map" "c.pfm" "string wrap" "clamp"
AttributeBegin
  Material "dielectric" "float eta" [ {ms['eta']} ] "float roughness" [ {ms['alpha']} ] "bool remaproughness" false "bool refractivenee" true
  Shape "plymesh" "string filename" [ "dish_glaze.ply" ]
AttributeEnd
AttributeBegin
  {card.body_material(ms['rho'])}
  Shape "plymesh" "string filename" [ "dish_body.ply" ]
AttributeEnd
AttributeBegin
  Material "thindielectric" "float eta" [ 1 ] "texture transmittance" "qh_co"
  Shape "plymesh" "string filename" [ "dish_film.ply" ]
AttributeEnd
""")
    print(f"-> {d}: glaze {h} mm, eta {ms['eta']}, alpha {ms['alpha']}, rho {np.mean(ms['rho']):.3f}")


def material_set_full(name):
    return card.material_set(name)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("map")
    q = sub.add_parser("object")
    q.add_argument("--set", required=True, choices=["kangxi", "modern"])
    a = ap.parse_args()
    {"map": make_map, "object": make_object}[a.cmd](a)


if __name__ == "__main__":
    main()
