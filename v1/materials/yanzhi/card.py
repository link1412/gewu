"""胭脂红's material card: a bowl in the form of the Met's Yongzheng bowl 1971.180.248 (CC0), its outside under the
gold-ruby enamel, its inside and lip the white glaze, under the museum's flat light (optics/rigs/museum_flat.json),
seen as that photograph sees it, and compared with it (docs/materials/yanzhi.md, "card").

    python3 -I materials/yanzhi/card.py object --c 0.2 [--name red]   # meshes + bowl.pbrt in out/materials/yanzhi/card/<name>/
    python3 -I tools/build.py materials/yanzhi/recipes/yanzhi-card-red.json --check   # 960 x 540, Cycles
    python3 -I materials/yanzhi/card.py measure out/recipes/yanzhi-card-red [--c 0.2] [--raw pbrt.exr --tag _pbrt]
                                                       # regions, colour differences, c's next step
    python3 -I materials/yanzhi/card.py sheet out/recipes/yanzhi-card-red [--raw ... --tag ...]   # side by side

The form is a card fixture, not the object layer's bowl [A]: its profile read off the photo's silhouette (the half
width per row at 5.86 px/mm, the rows over 5.69 px/mm, the camera 14 degrees up), at the Met's size (H 9.7 cm, rim
19.1 cm [I]); the wall 2.5 mm, the base 3 mm, the foot ring 3 mm wide [A]; the rim round, though the Met's is
lobed. Layers as tools/coat.py's tile, in the qinghua dish's way (materials/qinghua/dish.py): the glaze's surface
(dielectric, the glaze's index), the body 0.19 mm under it (diffuse), and on the outside, from 1.2 mm under the lip's
top down the wall and the foot ring to the sole, a film 4 um above the body (thindielectric of eta 1, its
transmittance exp(-c kappa) the gold's, enamel.py). The enamel lies on the glaze in the ware and under it here: for
an absorber with no scattering the order of the layers does not change the light, only the top surface's index does
(docs, "one interface": 0.9 Delta E with the glaze's index on top).

Comparing: the photo is the Met's JPEG decoded from sRGB to linear [A: its tone curve unknown, taken as sRGB's];
the render is the raw camera RGB (x.exr) through the camera's white balance and matrix (tools/camera.py calibrate),
no tone curve. Each image is divided channel by channel by its own white, the inside's far wall (a von Kries
balance in linear BT.709), so the exposure and the white balance cancel; the regions are placed by the red's own
outline in each image (rows as fractions of its height, columns as fractions of its half width), so the two framings
need not match. Colour differences are CIEDE2000 in CIELAB over that white.
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
import enamel  # noqa: E402
import stack  # noqa: E402
from camera import LAM, Spectra, blackbody, calibrate, lab, read_raw, rgb709_from_xyz  # noqa: E402
from studio import write_ply  # noqa: E402

OUT = os.path.join(ROOT, "out/materials/yanzhi/card")
PHOTO = os.path.join(ROOT, "ref/yanzhi/research/Met_1971.180.248.jpg")
H_MM, RIM_R = 97.0, 95.5          # [I] the Met's record: H 9.7 cm, rim 19.1 cm
WALL, LIP_R = 2.5, 1.0            # [A]
STEP = 0.5                        # mm along the profile
N_AROUND = 720
GAP = 0.004                       # mm, the film above the body (tools/coat.py's film_gap)
K_LIGHT = 5500.0                  # the rig's blackbody (optics/rigs/museum_flat.json)
SENSOR = "canon_eos_5d_mkiv"


def material():
    return json.load(open(os.path.join(HERE, "material.json")))


def kappa(mat=None):
    """The gold's kappa(LAM) for the material's choices (material.json): tau = c kappa at normal incidence."""
    mat = mat or material()
    g = mat["enamel"]["gold"]
    k, _ = enamel.kappa(LAM, enamel.n_host(LAM, mat), [g["diameter_nm"]["value"]],
                        A=g["size_correction_A"]["value"], source=g["optical_constants"]["value"])
    return k


# --- the form ------------------------------------------------------------------------------------
def _spline(P, step=STEP):
    P = np.asarray(P, float)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    sp = make_interp_spline(s, P, k=3, bc_type="natural")
    t = np.linspace(0, s[-1], max(int(s[-1] / step), 2) + 1)
    return sp(t)


# the outside of the wall, lip to foot, (r, z) mm: the photo's half widths [M, read off at 5.86 / 5.69 px/mm],
# the lip's flare above z 84 and the junction with the foot drawn [A]
OUTER = [(RIM_R, H_MM - LIP_R), (94.6, 92.5), (92.0, 88.5), (88.0, 84.4), (84.8, 80.0), (81.0, 75.6), (78.4, 71.2),
         (77.2, 66.8), (76.0, 62.4), (75.2, 58.0), (74.1, 53.6), (72.9, 49.2), (71.3, 44.8), (69.7, 40.4),
         (67.7, 36.0), (64.8, 31.6), (61.7, 27.2), (57.7, 22.8), (51.5, 18.5), (46.5, 15.6), (43.0, 14.1),
         (41.2, 12.8), (40.4, 11.0)]
FOOT = [(43.0, 14.1), (41.2, 12.8), (40.5, 11.0), (40.3, 7.0), (40.1, 2.5), (39.8, 0.6), (39.3, 0.0)]


def smooth_outer():
    """OUTER down to z 14 (where the foot's curve takes over) through a smoothing spline r(z) (the photo's half widths
    carry a pixel or two of noise), every 1 mm."""
    from scipy.interpolate import UnivariateSpline
    o = np.array(OUTER[:-2])[::-1]                      # z rising
    sp = UnivariateSpline(o[:, 1], o[:, 0], k=3, s=len(o) * 0.25)
    z = np.linspace(o[0, 1], o[-1, 1], int(o[-1, 1] - o[0, 1]) + 1)
    r = sp(z)
    r[-1] = RIM_R
    return np.c_[r, z][::-1]


def profile():
    """The glaze's outer surface, (r, z) mm, one run from the axis on the inside's floor, out and up the inside, over
    the lip, down the outside and the foot ring, across the sole, up the foot's inside, to the axis under the base
    [A, as the module says]. Returns R, Z and the indices of the outside's first point (the lip's outer point) and of
    the sole's outer edge."""
    out = smooth_outer()
    # the inside: the outside's points moved WALL inwards along their normals, down to z 16, then the floor
    t = np.gradient(out, axis=0)
    n = np.c_[-t[:, 1], t[:, 0]]                        # the outward normal of a run going down the outside
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    n = -n if n[len(n) // 2, 0] < 0 else n
    inner = out - WALL * n
    inner = inner[inner[:, 1] > 17.0][::-1]             # bottom to top
    inner[-1] = (RIM_R - 2 * LIP_R, H_MM - LIP_R)       # meets the lip's inner side
    floor = np.c_[np.linspace(0, 28, 57), 12.0 + 0.4 * (np.linspace(0, 28, 57) / 28) ** 2]
    inside = _spline(np.vstack([[floor[-1]], [(33.0, 13.4)], inner]))
    a = np.linspace(np.pi, 0, 13)
    lip = np.c_[RIM_R - LIP_R + LIP_R * np.cos(a), H_MM - LIP_R + LIP_R * np.sin(a)]
    outside = _spline(out)                             # out is already smooth
    foot = _spline(FOOT)
    sole = np.c_[np.linspace(39.3, 36.4, 7), np.zeros(7)]
    finner = _spline([(36.4, 0.0), (35.9, 0.8), (35.5, 4.0), (35.1, 7.6), (34.0, 8.6)])
    rb = np.linspace(34.0, 0, 69)
    base = np.c_[rb, 9.0 + 0.3 * (1 - (rb / 34.0) ** 2)]
    parts = [floor, inside[1:], lip[1:], outside[1:], foot[1:], sole[1:], finner[1:], base[1:]]
    P = np.vstack(parts)
    i_out = len(floor) + len(inside) - 1 + len(lip) - 2          # the lip's outer point
    i_sole = i_out + len(outside) - 1 + len(foot) - 1              # the sole's outer edge
    keep = np.r_[True, np.hypot(*np.diff(P, axis=0).T) > 1e-6]
    idx = np.cumsum(keep) - 1
    P = P[keep]
    return P[:, 0], P[:, 1], int(idx[i_out]), int(idx[i_sole])


def spectrum_text(lam, v):
    return "[ " + " ".join(f"{l:g} {x:.6g}" for l, x in zip(lam, v)) + " ]"


def make_object(a):
    import gen_object as G
    mat = material()
    gl, en = mat["glaze"], mat["enamel"]
    h, eta, alpha = gl["thickness_mm"]["value"], gl["eta"]["value"], gl["ggx_alpha"]["value"]
    rho = mat["body"]["albedo"]["value"]
    R, Z, i_out, i_sole = profile()
    glaze = [(R, Z)]
    body = G.offset(glaze, h)
    Rb, Zb = body[0]
    # the film: the body's outside from 1.2 mm under the lip's top (the white lip) to the sole's edge, GAP outwards
    top = H_MM - en["white_lip_mm"]["value"]
    j0 = i_out + int(np.argmax(Z[i_out:i_sole] <= top))
    fr, fz = Rb[j0:i_sole + 1], Zb[j0:i_sole + 1]
    nf = G.normals2d(fr, fz)
    film = [(fr + GAP * nf[:, 0], fz + GAP * nf[:, 1])]
    d = os.path.join(OUT, a.name)
    os.makedirs(d, exist_ok=True)
    for name, pieces in (("glaze", glaze), ("body", body), ("film", film)):
        P, N, T = G.revolve(pieces, N_AROUND)
        write_ply(os.path.join(d, f"bowl_{name}.ply"), P, N, T)
    lam = np.arange(360, 831, 5)
    T0 = np.exp(-a.c * np.interp(lam, LAM, kappa(mat)))
    film_line = (f'Material "thindielectric" "float eta" [ 1 ] "spectrum transmittance" {spectrum_text(lam, T0)}'
                 if a.c > 0 else None)
    with open(os.path.join(d, "bowl.pbrt"), "w") as f:
        f.write(f"""# 胭脂红 card (materials/yanzhi/card.py): a bowl in Met 1971.180.248's form, {2 * RIM_R:g} x {H_MM:g} mm;
# gold column density c = {a.c:g} g/m^2 (material.json)
AttributeBegin
  Material "dielectric" "float eta" [ {eta} ] "float roughness" [ {alpha} ] "bool remaproughness" false "bool refractivenee" true
  Shape "plymesh" "string filename" [ "bowl_glaze.ply" ]
AttributeEnd
AttributeBegin
  Material "diffuse" "spectrum reflectance" [ 360 {rho} 830 {rho} ]
  Shape "plymesh" "string filename" [ "bowl_body.ply" ]
AttributeEnd
""" + ("" if film_line is None else f"""AttributeBegin
  {film_line}
  Shape "plymesh" "string filename" [ "bowl_film.ply" ]
AttributeEnd
"""))
    if film_line is None:
        os.remove(os.path.join(d, "bowl_film.ply"))
    print(f"-> {d}: glaze {h} mm, eta {eta}, alpha {alpha}, rho {rho}; c {a.c} g/m^2, film z <= {fz[0]:.2f} mm, "
          f"{len(R)} profile points")


# --- images ----------------------------------------------------------------------------------------
_S = Spectra(SENSOR)
_CAL = calibrate(_S, blackbody(K_LIGHT))
_WN = _S.cmf @ _S.d65 / (_S.cmf[1] @ _S.d65)
_XYZ = np.linalg.inv(rgb709_from_xyz(_WN))


def photo_linear():
    v = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float64) / 255
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def render_linear(d, raw_name="x.exr"):
    raw = read_raw(os.path.join(d, raw_name))
    return (raw * _CAL["gains"]) @ _CAL["C"].T


def regions(lin, name):
    """Boxes (row, col, half size) in an image of the bowl: the red outside's outline gives its centre column, its top
    (the lip's front) and bottom rows and its half width per row; the white's top (the lip's back) is the first row
    above the red: the steepest rise of the centre column's luminance (backdrop to white lip)."""
    sm = ndi.gaussian_filter(lin, (2, 2, 0))           # the render's noise (no denoiser on x.exr) off the outline
    R, G = sm[..., 0], sm[..., 1]
    red = ndi.binary_opening((R > 2 * G) & (R > 0.004 * np.percentile(R, 99.5)), iterations=2)
    lab_, n = ndi.label(red)
    if n == 0:
        raise SystemExit(f"{name}: no red found")
    red = lab_ == 1 + int(np.argmax(ndi.sum(red, lab_, range(1, n + 1))))
    rows = np.nonzero(red.any(1))[0]
    cols = np.nonzero(red.any(0))[0]
    cx = 0.5 * (cols.min() + cols.max())
    width = cols.max() - cols.min()
    col_band = slice(int(cx - 0.02 * width), int(cx + 0.02 * width) + 1)
    red_top = int(np.nonzero(red[:, col_band].any(1))[0].min())
    red_bot = int(rows.max())
    Y = lin @ np.array([0.2126, 0.7152, 0.0722])
    # the white's top (the far lip): the steepest rise of the centre column's luminance above the red (smoothed 2 px).
    # Until S8 r2 it was the first row brighter than 1.15 x the backdrop beside the bowl (1.3 before round 2); with
    # backdrop lights the backdrop beside the bowl is as bright as the inside's white and that rule found nothing.
    # The two rules agree to 1 px on the photo (320 / 319) and on round 2's render (66 / 65).
    yc = ndi.gaussian_filter(Y, 2)[:, col_band].mean(1)
    gy = np.gradient(yc[:red_top])
    if red_top < 10:
        raise SystemExit(f"{name}: no white above the red")
    top = int(np.argmax(gy[:int(red_top * 0.95)]))
    s = max(2, int(round(0.015 * width)))
    box = {"white": (int(top + 0.3 * (red_top - top)), int(cx), s)}
    for fz in (0.3, 0.55):
        r = int(red_top + fz * (red_bot - red_top))
        c = np.nonzero(red[r])[0]
        hw = 0.5 * (c.max() - c.min())
        cc = 0.5 * (c.max() + c.min())
        for fu, side in ((-0.6, "left"), (0.0, "centre"), (0.6, "right")):
            box[f"{side}_{'upper' if fz < 0.5 else 'lower'}"] = (r, int(round(cc + fu * hw)), s)
    return box, {"red_top": red_top, "red_bot": red_bot, "top": top, "cx": cx, "width": int(width)}


def median_box(lin, b):
    r, c, s = b
    return np.median(lin[r - s:r + s + 1, c - s:c + s + 1].reshape(-1, 3), axis=0)


def lab_of(rgb_over_white):
    return lab(np.asarray(rgb_over_white) @ _XYZ.T, _WN)


def de2000(l1, l2):
    """CIEDE2000 (Sharma, Wu & Dalal 2005), kL = kC = kH = 1."""
    L1, a1, b1 = l1
    L2, a2, b2 = l2
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = 0.5 * (C1 + C2)
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = dh - 360 if dh > 180 else dh + 360 if dh < -180 else dh
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lpm, Cpm = 0.5 * (L1 + L2), 0.5 * (C1p + C2p)
    hs = h1p + h2p
    hpm = hs / 2 if abs(h1p - h2p) <= 180 else (hs + 360) / 2 if hs < 360 else (hs - 360) / 2
    T = (1 - 0.17 * np.cos(np.radians(hpm - 30)) + 0.24 * np.cos(np.radians(2 * hpm))
         + 0.32 * np.cos(np.radians(3 * hpm + 6)) - 0.20 * np.cos(np.radians(4 * hpm - 63)))
    dth = 30 * np.exp(-(((hpm - 275) / 25) ** 2))
    RC = 2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25.0 ** 7))
    SL = 1 + 0.015 * (Lpm - 50) ** 2 / np.sqrt(20 + (Lpm - 50) ** 2)
    SC, SH = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    RT = -np.sin(np.radians(2 * dth)) * RC
    return float(np.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH)))


def stack_Y(c, k, mat):
    """The 1-D stack's luminance over the white (c = 0), at normal view under uniform light: for c's next step."""
    rho = np.full(LAM.shape, mat["body"]["albedo"]["value"])
    ne = float(enamel.n_host(589.3, mat))
    ng = mat["glaze"]["eta"]["value"]
    w = _S.cmf[1] * blackbody(K_LIGHT)
    return float(w @ stack.stack(c * k, rho, ne, ng)[0]) / float(w @ stack.stack(0 * k, rho, ne, ng)[0])


def measure(a):
    mat = material()
    imgs = {"photo": photo_linear(), "render": render_linear(a.dir, a.raw)}
    res = {}
    for name, lin in imgs.items():
        box, info = regions(lin, name)
        white = median_box(lin, box["white"])
        res[name] = {"info": info, "boxes": box, "white_linear": white.tolist(),
                     "rgb": {k: (median_box(lin, b) / white).tolist() for k, b in box.items() if k != "white"}}
    rows, dEs, logq = [], [], []
    for k in res["photo"]["rgb"]:
        p, r = np.array(res["photo"]["rgb"][k]), np.array(res["render"]["rgb"][k])
        lp, lr = lab_of(p), lab_of(r)
        hp, hr = (np.degrees(np.arctan2(l[2], l[1])) for l in (lp, lr))
        dE = de2000(lp, lr)
        dEs.append(dE)
        Yp, Yr = (float(v @ np.array([0.2126, 0.7152, 0.0722])) for v in (p, r))
        logq.append(np.log(Yp / Yr))
        rows.append({"region": k, "photo_lab": lp.round(2).tolist(), "render_lab": lr.round(2).tolist(),
                     "photo_hue": round(float(hp), 1), "render_hue": round(float(hr), 1), "dE00": round(dE, 2),
                     "Y_photo_over_render": round(Yp / Yr, 3)})
        print(f"{k:13s} photo L*a*b* {lp[0]:5.1f} {lp[1]:5.1f} {lp[2]:5.1f} h {hp:5.1f} | render {lr[0]:5.1f} "
              f"{lr[1]:5.1f} {lr[2]:5.1f} h {hr:5.1f} | dE00 {dE:5.2f} | Y photo/render {Yp / Yr:.3f}")
    # c is fitted on the centre column only: seen square-on, the glaze reflects least there (the sides carry a sheen
    # of the lamps and the backdrop, whose layout the photo does not give), so the enamel's own colour dominates
    q = float(np.exp(np.mean([lq for lq, r in zip(logq, rows) if r["region"].startswith("centre")])))
    out = {"dir": a.dir, "c": a.c, "regions": rows, "mean_dE00": float(np.mean(dEs)),
           "Y_ratio_centre": q, "Y_ratio_all": float(np.exp(np.mean(logq))), **res}
    if a.c is not None:
        k = kappa(mat)
        y0 = stack_Y(a.c, k, mat)
        from scipy.optimize import brentq
        target = q * y0
        try:
            c1 = brentq(lambda c: stack_Y(c, k, mat) - target, 1e-4, 5.0)
        except ValueError:
            c1 = None
        out["c_next"] = c1
        print(f"mean dE00 {np.mean(dEs):.2f}; luminance photo/render at the centre {q:.3f}; c {a.c} -> next c {c1}")
    json.dump(out, open(os.path.join(a.dir, f"card_measure{a.tag}.json"), "w"), indent=1, default=float)


def sheet(a):
    """Photo and render side by side, each scaled to the same bowl width and developed the same way: linear over its
    own white, times 0.85 (so the white sits below the clip), sRGB-encoded."""
    m = json.load(open(os.path.join(a.dir, f"card_measure{a.tag}.json")))
    tiles = []
    for name, lin in (("photo", photo_linear()), ("render", render_linear(a.dir, a.raw))):
        info = m[name]["info"]
        w = np.array(m[name]["white_linear"])
        img = np.clip(lin / w * 0.85, 0, 1)
        img = np.where(img <= 0.0031308, 12.92 * img, 1.055 * img ** (1 / 2.4) - 0.055)
        cx, top, bot = info["cx"], info["top"], info["red_bot"]
        hh = bot - top                                  # the bowl's height in the image: the scale of both tiles
        x0, x1 = int(cx - 0.85 * hh), int(cx + 0.85 * hh)
        y0, y1 = int(top - 0.15 * hh), int(bot + 0.1 * hh)
        crop = img[max(0, y0):y1, max(0, x0):x1]
        im = Image.fromarray((crop * 255 + 0.5).astype(np.uint8))
        im = im.resize((800, int(800 * im.size[1] / im.size[0])), Image.LANCZOS)
        tiles.append(im)
    h = max(t.size[1] for t in tiles)
    canvas = Image.new("RGB", (1600, h), (255, 255, 255))
    for i, t in enumerate(tiles):
        canvas.paste(t, (800 * i, 0))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(canvas)
    dr.text((10, 10), "Met 1971.180.248 (CC0), sRGB decoded, over its white", fill=(0, 0, 0))
    dr.text((810, 10), f"render ({a.raw}), c {m['c']} g/m^2, over its white; mean dE00 {m['mean_dE00']:.1f}",
            fill=(0, 0, 0))
    path = os.path.join(a.dir, f"card_sheet{a.tag}.png")
    canvas.save(path)
    print("->", path)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("object")
    o.add_argument("--c", type=float, required=True, help="gold column density, g Au / m^2 (0: no film)")
    o.add_argument("--name", default="red")
    m = sub.add_parser("measure")
    m.add_argument("dir")
    m.add_argument("--c", type=float, default=None)
    s = sub.add_parser("sheet")
    s.add_argument("dir")
    for q in (m, s):
        q.add_argument("--raw", default="x.exr", help="the render's raw file in dir: x.exr (Cycles) or pbrt.exr")
        q.add_argument("--tag", default="", help="suffix of card_measure<tag>.json and card_sheet<tag>.png")
    a = ap.parse_args()
    {"object": make_object, "measure": measure, "sheet": sheet}[a.cmd](a)


if __name__ == "__main__":
    main()
