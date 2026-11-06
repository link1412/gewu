"""The material card of 青花: a flat coated tile shot like the Met's Kangxi plate 18.61.2 (DP-15944-021.jpg), at the
photo's px/mm, side by side with it (docs/materials/qinghua.md).

    python3 -I materials/qinghua/card.py measure                          # the photo: scale, white, the c map
    python3 -I materials/qinghua/card.py build --out out/materials/qinghua/card [--set kangxi] [--spp 64] [--map photo|craft]
    python3 -I materials/qinghua/card.py develop out/materials/qinghua/card [--which cycles pbrt]
    python3 -I materials/qinghua/card.py compare out/materials/qinghua/card

The pattern: --map photo inverts the photo itself to the cobalt's column density c, pixel by pixel, through the
1-D stack (optics.stack): the tile then carries the photo's own painting, so the card tests the material (the
colours of the levels, the glaze and its walk, the white), not the brush. The inversion uses the local 1-D model,
so whatever the photo's lines lost to the glaze's walk is already in c, and the render walks it again: the render's
thin lines come out lighter than the photo's by about what the walk does (a check of its size, tests/qinghua).
--map craft paints a motif with crafts/painting at the c the photo's levels fit (the craft's card).

World: mm, z up, the glaze's surface at z = 0, the camera above looking down (pbrt's LookAt, up +y: image right is
world -x, so the map is mirrored in x to read like the photo). The frame is 960 x 540 at the photo's px/mm (the
camera chain upsamples it to 1920 x 1080; compare brings it back).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import optics  # noqa: E402
from camera import LAM, Spectra, blackbody, calibrate  # noqa: E402
from coat import coated_tile, write_quad  # noqa: E402

PHOTO = "ref/qinghua/met-18.61.2/DP-15944-021.jpg"
PLATE_W_MM = 165.0             # [I] The Met's record for 18.61.2: H. 3.8 cm, W. 16.5 cm (collection API, object 47583)
CROP = (1560, 1250, 960, 540)  # x, y, w, h in the photo: the central medallion (lady, stand, rock)
OUT_M = os.path.join(ROOT, "out/materials/qinghua/measured_met18612.json")
OUT_C = os.path.join(ROOT, "out/materials/qinghua/photo_c.pfm")
RES = (960, 540)
CAM_H = 600.0                  # mm, camera height (pinhole; a flat tile is all in focus)
LAMP = dict(off_normal_deg=52.0, azimuth_deg=(-90.0, 90.0), distance=1000.0, size=600.0)
C_GRID = np.round(np.arange(0.0, 10.0001, 0.05), 4)
K_LIGHT = 5500.0


def srgb_decode(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def lamp_dirs():
    """Unit vectors to the lamps' centres, our choice after the Palace Museum's flat set-up
    (optics/rigs/museum_flat.json: two 60 cm softboxes at 45 deg either side, 30 deg up; about the camera axis that
    is 52 deg off the plate's normal). Placed above and below the frame (world +-y, image up and down), not left and
    right: symmetric, so the colours do not care. The Met's own set-up is not published [A]."""
    th = np.radians(LAMP["off_normal_deg"])
    return [np.array([np.sin(th) * np.cos(np.radians(a)), np.sin(th) * np.sin(np.radians(a)), np.cos(th)])
            for a in LAMP["azimuth_deg"]]


def material_set(name):
    m = optics.material()["sets"][name]
    return dict(eta=m["glaze"]["eta"]["value"], h=m["glaze"]["thickness_mm"]["value"],
                alpha=m["glaze"]["ggx_alpha"]["value"], rho=optics.body_albedo(m["body"]),
                kappa=optics.pigment_kappa(m["pigment"]),
                sigma_a=m["glaze"]["sigma_a_per_mm"]["value"], bleed_um=m["bleed_um"]["value"])


_S = Spectra("canon_eos_5d_mkiv")
_W = _S.sens * blackbody(K_LIGHT)
_C = calibrate(_S, blackbody(K_LIGHT))["C"]


def colours(ms, kappa, c):
    """The 1-D stack's colour at each c, as linear BT.709 relative to the white (c = 0), under the card's lamps,
    developed like tools/camera.py (white balance on the key light, its matrix C)."""
    rho = np.broadcast_to(ms["rho"], LAM.shape)
    mus = [d[2] for d in lamp_dirs()]
    cam = np.array([_W @ sum(optics.stack(ci * kappa, rho, ms["eta"], mu_in=mu)[0] for mu in mus)
                    for ci in np.concatenate([[0.0], np.atleast_1d(c)])])
    return ((cam / cam[0]) @ _C.T)[1:]           # white balanced, then the matrix; white -> (1, 1, 1)


def white_rgb(rho, eta):
    """The unpainted glaze's colour, linear BT.709, white balanced on the key light (a perfect white -> (1, 1, 1))."""
    rho = np.broadcast_to(rho, LAM.shape)
    cam = _W @ sum(optics.stack(np.zeros(LAM.shape), rho, eta, mu_in=d[2])[0] for d in lamp_dirs())
    return (cam / _W.sum(1)) @ _C.T


def fit_tint(eta, rho0, target):
    """The body tint t, q [F] (optics.body_albedo) that gives the white the photo's r/g and b/g."""
    from scipy.optimize import least_squares
    x = (LAM - 550.0) / 100.0

    def res(p):
        w = white_rgb(rho0 * (1 + p[0] * x + p[1] * x * x), eta)
        return [w[0] / w[1] - target[0] / target[1], w[2] / w[1] - target[2] / target[1]]
    return least_squares(res, [0.0, 0.0]).x


class Locus:
    def __init__(self, ms, kappa, c=C_GRID):
        self.c = np.asarray(c)
        self.rgb = colours(ms, kappa, self.c)

    def invert(self, q, eps=0.004, chunk=20000):
        """c for each colour q (..., 3) (linear BT.709 / white): the nearest point of the locus in log space."""
        lm = np.log(np.maximum(self.rgb, 0) + eps)
        flat = np.log(np.maximum(q, 0) + eps).reshape(-1, 3)
        c, r = np.empty(len(flat)), np.empty(len(flat))
        for k in range(0, len(flat), chunk):
            d = ((flat[k:k + chunk, None, :] - lm) ** 2).sum(-1)
            i = d.argmin(-1)
            c[k:k + chunk], r[k:k + chunk] = self.c[i], np.sqrt(d[np.arange(len(i)), i] / 3)
        return c.reshape(q.shape[:-1]), r.reshape(q.shape[:-1])


# --- measure ----------------------------------------------------------------------------------
def plate_scale(g):
    """px/mm from the plate's widest horizontal span (rows 1200-1800, the rim brighter than 0.62 of full scale)."""
    spans = []
    for y in range(1200, 1800, 10):
        m = np.where(g[y] > 0.62)[0]
        spans.append(m.max() - m.min())
    return max(spans) / PLATE_W_MM, max(spans)


def measure(a):
    im = np.asarray(Image.open(os.path.join(ROOT, PHOTO)).convert("RGB")).astype(np.float64) / 255
    pxmm, span = plate_scale(im.mean(-1))
    x, y, w, h = CROP
    lin = srgb_decode(im[y:y + h, x:x + w])
    # the white: the unpainted glaze, pixels whose blue does not exceed red by much, the brighter half of them
    br = lin[..., 2] / np.maximum(lin[..., 0], 1e-4)
    Y = lin @ np.array([0.2126, 0.7152, 0.0722])
    cand = br < 1.25
    white_mask = cand & (Y > np.percentile(Y[cand], 50))
    white = np.median(lin[white_mask], 0)
    ms = material_set(a.set)
    q = lin / white
    # the photo's levels, binned by the blue channel's ratio to the white (independent of the model)
    bins = [(0.70, 0.88), (0.50, 0.70), (0.30, 0.50), (0.15, 0.30), (0.05, 0.15)]
    lev = []
    for lo, hi in bins:
        m = (q[..., 2] >= lo) & (q[..., 2] < hi)
        lev.append((lo, hi, int(m.sum()), np.median(q[m], 0)))
    Q = np.array([l[3] for l in lev])
    eps = 0.004
    kc = optics.cobalt_kappa()

    def resid(p, companion):
        k = kc + (optics.companion_kappa(p[0], p[1]) if companion else 0.0)
        cs = p[2:] if companion else p
        return (np.log(np.maximum(colours(ms, k, cs), 0) + eps) - np.log(Q + eps)).ravel()

    from scipy.optimize import least_squares
    c0 = [0.3, 0.6, 1.2, 2.5, 5.0]
    f0 = least_squares(lambda p: resid(p, False), c0, bounds=(0, 20))
    f1 = least_squares(lambda p: resid(p, True), [0.5, -0.5] + c0,
                       bounds=([0, -2] + [0] * 5, [10, 2] + [20] * 5))
    r_fit, s_fit = f1.x[:2]

    def resid_iron(p):
        return (np.log(np.maximum(colours(ms, kc + optics.iron_like_kappa(p[0], p[1]), p[2:]), 0) + eps)
                - np.log(Q + eps)).ravel()
    f2 = min((least_squares(resid_iron, x0, bounds=([0, 0] + [0] * 5, [50, 5000] + [50] * 5))
              for x0 in ([0.5, 50.0] + c0, [0.5, 50.0, 0.1, 0.3, 1.0, 2.0, 4.0], [0.5, 12.0, 0.15, 0.4, 1.5, 2.2, 3.5])),
             key=lambda f: f.cost)                  # three starts: the fit has local minima
    fe3_fit, fe2_fit = f2.x[:2]
    k_iron = kc + optics.iron_like_kappa(fe3_fit, fe2_fit)
    fit = {"what": "the photo's five levels (pixels binned by blue / white) against the 1-D stack; c per level free",
           "cobalt_only": {"c": np.round(f0.x, 3).tolist(),
                           "log_rms": float(np.sqrt(np.mean(f0.fun ** 2))),
                           "model": np.round(colours(ms, kc, f0.x), 4).tolist()},
           "with_companion": {"r": round(float(r_fit), 4), "s": round(float(s_fit), 4), "c": np.round(f1.x[2:], 3).tolist(),
                              "log_rms": float(np.sqrt(np.mean(f1.fun ** 2))),
                              "model": np.round(colours(ms, kc + optics.companion_kappa(r_fit, s_fit), f1.x[2:]), 4).tolist()},
           "with_iron_like": {"fe3": round(float(fe3_fit), 4), "fe2": round(float(fe2_fit), 4),
                              "c": np.round(f2.x[2:], 3).tolist(), "log_rms": float(np.sqrt(np.mean(f2.fun ** 2))),
                              "model": np.round(colours(ms, k_iron, f2.x[2:]), 4).tolist(),
                              "lab_model": np.round(lab_of(colours(ms, k_iron, f2.x[2:])), 1).tolist(),
                              "lab_photo": np.round(lab_of(Q), 1).tolist()},
           "body_tint": dict(zip(("t", "q"), np.round(fit_tint(ms["eta"], np.mean(ms["rho"]), white), 4).tolist()),
                             what="the tint that gives the 1-D white the photo's r/g, b/g (optics.body_albedo) [F]"),
           "photo": [{"blue_over_white": [lo, hi], "px": n_, "rgb_over_white": np.round(v, 4).tolist()}
                     for lo, hi, n_, v in lev]}
    os.makedirs(os.path.dirname(OUT_C), exist_ok=True)
    maps = {}
    ground = (q[..., 2] >= 0.88) & (q[..., 2] / np.maximum(q[..., 0], 1e-4) < 1.25)
    for model, kappa, grid in (("co", kc, np.round(np.arange(0.0, 10.0001, 0.01), 4)),
                               ("iron", k_iron, np.linspace(0.0, 2.5 * max(f2.x[2:]), 1001))):
        loc = Locus(ms, kappa, grid)
        c, res = loc.invert(q)
        # the ground's floor: the unpainted glaze's own scatter (photo noise, JPEG, a cast) inverts to small c on one
        # side only (c >= 0), which would paint a faint blue speckle over the whole ground; take its 99th percentile
        # off everywhere [D]
        floor = float(np.percentile(c[ground], 99))
        c = np.maximum(c - floor, 0.0)
        path = OUT_C.replace(".pfm", f"_{model}.pfm")
        img = np.ascontiguousarray(c[:, ::-1], dtype="<f4")          # mirrored in x for pbrt's image (module doc)
        with open(path, "wb") as f:
            f.write(f"Pf\n{w} {h}\n-1.0\n".encode())
            f.write(img[::-1].tobytes())
        lv = {}
        for lo, hi, n_, v in lev:
            m = (q[..., 2] >= lo) & (q[..., 2] < hi)
            lv[f"blue/white {lo}-{hi}"] = {"median_c": round(float(np.median(c[m])), 4),
                                           "log_residual_rms": round(float(np.sqrt(np.mean(res[m] ** 2))), 4)}
        maps[model] = {"file": os.path.relpath(path, ROOT), "c_grid": [float(grid[0]), float(grid[-1]), len(grid)],
                       "companion": None if model == "co" else {"model": "iron_like", "fe3": float(fe3_fit),
                                                                "fe2": float(fe2_fit)},
                       "c_max": float(c.max()), "per_level": lv, "ground_floor_c": floor,
                       "white_px": int((c <= grid[1] / 2).sum())}
    out = {"photo": PHOTO, "crop_xywh": list(CROP),
           "scale": {"px_per_mm": round(pxmm, 3), "plate_span_px": int(span), "plate_w_mm": PLATE_W_MM,
                     "how": "the widest horizontal span of the rim over rows 1200-1800 / the Met's W [M / I]; the plate "
                            "is nearly frontal (vertical span within 1.5%), its tilt ignored"},
           "white_linear": np.round(white, 4).tolist(),
           "white_srgb8": np.round(255 * np.median(im[y:y + h, x:x + w][white_mask], 0)).tolist(),
           "assumes": "the photo is sRGB-encoded and colour-correct (the Met's processing is not published) [A]",
           "set": a.set, "lamps": "lamp_dirs(): 52 deg off the normal, above and below the frame [A]",
           "fit": fit, "maps": maps,
           "residual_note": "log_residual_rms: the RMS over channels of ln((q + 0.004) / (model + 0.004)) at the "
                            "fitted c: how far the photo's colour is from the 1-D model's locus (0.05 ~ 5%)"}
    json.dump(out, open(OUT_M, "w"), indent=1)
    print(json.dumps(out, indent=1))


# --- the craft's motif -----------------------------------------------------------------------
def _blob(rng, cx, cy, rx, ry, rot, n=72, wob=0.18):
    """A closed, smoothly irregular outline (a rock, a cloud, a robe's fold) around (cx, cy)."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = 1 + sum(wob / (k + 1) * rng.normal() * np.cos((k + 2) * t + rng.uniform(0, 2 * np.pi)) for k in range(4))
    x, y = rx * r * np.cos(t), ry * r * np.sin(t)
    c, s_ = np.cos(rot), np.sin(rot)
    return np.stack([cx + c * x - s_ * y, cy + s_ * x + c * y], 1)


def _leaf(cx, cy, length, width, ang, bend=0.15, n=40):
    t = np.linspace(0, 1, n)
    spine = np.stack([t * length, bend * length * np.sin(np.pi * t)], 1)
    half = width / 2 * np.sin(np.pi * t) ** 0.8
    nrm = np.stack([-np.gradient(spine[:, 1]), np.gradient(spine[:, 0])], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    P = np.concatenate([spine + nrm * half[:, None], (spine - nrm * half[:, None])[::-1]])
    c, s_ = np.cos(ang), np.sin(ang)
    R = np.array([[c, -s_], [s_, c]])
    return P @ R.T + [cx, cy], spine @ R.T + [cx, cy]


def craft_canvas(fw, fh, bleed_um, seed, px_per_mm=40.0, scale=1.0):
    """A motif painted with crafts/painting at the card's frame (fw x fh mm, centred): rocks and a robe in 分水 of
    several strengths, outlined (勾线), leaves, drapery strokes, a few fine lines; fired. c in g CoO/m^2 from
    craft.json (line_c, wash_c), times `scale` (the card's fit of the levels)."""
    sys.path.insert(0, os.path.join(ROOT, "crafts/painting"))
    import paint
    p = paint.params()
    rng = np.random.default_rng(seed)
    cv = paint.Canvas((-fw / 2, fw / 2), (-fh / 2, fh / 2), px_per_mm)
    lc, (w0, w1) = p["line_c"] * scale, [v * scale for v in p["wash_c"]]
    lw = p["line_width_mm"]
    # rocks on the right, a robe in the middle, a pale cloud upper left
    shapes = [(_blob(rng, 22, -2, 9, 13, 0.3), w0 * 2.5, w1 * 0.8, (0.2, 1.0)),
              (_blob(rng, 29, -12, 6, 5, 1.0), w1 * 0.6, w1, (0, 1)),
              (_blob(rng, 2, -6, 11, 7, -0.2, wob=0.25), w0 * 1.5, w1 * 0.55, (1, -0.4)),
              (_blob(rng, -20, 11, 8, 4, 0.1, wob=0.12), w0, w0 * 2, (1, 0)),
              (_blob(rng, -6, 13, 5, 3, 0.4), w1 * 0.9, w1 * 1.1, (0, 1))]
    for i, (P, ca, cb, dr) in enumerate(shapes):
        cv.wash(P, ca, cb, direction=dr, seed=seed * 100 + i)
        cv.stroke(np.concatenate([P, P[:1]]), lw * rng.uniform(0.8, 1.2), lc, seed=seed * 100 + 50 + i, wobble=0.15)
    # drapery strokes inside the robe
    for j in range(7):
        x0 = -6 + 2.2 * j + rng.normal(0, 0.3)
        path = np.stack([x0 + np.linspace(0, 1.5, 20) + 0.3 * np.sin(np.linspace(0, 3, 20)),
                         np.linspace(-2, -10, 20)], 1)
        cv.stroke(path, lw * 0.8, lc * 0.9, seed=seed * 100 + 70 + j, wobble=0.2)
    # leaves on the left, washed and outlined, with a midrib
    for j in range(6):
        ang = np.radians(55 + 18 * j + rng.normal(0, 5))
        P, spine = _leaf(-24 + rng.normal(0, 0.5), -14, rng.uniform(9, 14), rng.uniform(2.2, 3.2), ang,
                         bend=rng.uniform(-0.2, 0.2))
        cv.wash(P, w1 * 0.7, w1 * 1.2, direction=(np.cos(ang), np.sin(ang)), seed=seed * 100 + 80 + j)
        cv.stroke(np.concatenate([P, P[:1]]), lw * 0.9, lc, seed=seed * 100 + 90 + j, wobble=0.1)
        cv.stroke(spine[3:-6], lw * 0.6, lc * 0.9, seed=seed * 100 + 95 + j)
    # a fence of fine lines, bottom left
    for j in range(5):
        cv.stroke([(-34 + 2.5 * j, -19), (-34 + 2.5 * j, -9)], lw * 0.7, lc, seed=seed * 100 + 110 + j)
    cv.stroke([(-35, -11), (-23, -11.5)], lw * 0.8, lc, seed=seed * 100 + 120)
    cv.stroke([(-35, -16), (-23, -16.3)], lw * 0.8, lc, seed=seed * 100 + 121)
    return cv.fire(bleed_um)


# --- build ------------------------------------------------------------------------------------
def build(a):
    M = json.load(open(OUT_M))
    pxmm = M["scale"]["px_per_mm"]
    fw, fh = RES[0] / pxmm, RES[1] / pxmm
    d = a.out
    os.makedirs(d, exist_ok=True)
    ms = material_set(a.set)
    if a.h is not None:
        ms["h"] = a.h                     # a test of the glaze's walk, not the material's value
    mp = M["maps"][a.model]
    k = optics.cobalt_kappa()
    if mp["companion"]:
        k = k + optics.iron_like_kappa(mp["companion"]["fe3"], mp["companion"]["fe2"])
    grid = np.linspace(*mp["c_grid"][:2], mp["c_grid"][2])
    np.savez(f"{d}/film.npz", lambda_nm=LAM, c=grid, R=optics.film_family(k, grid))
    write_quad(d)
    if a.map == "photo":
        src = open(os.path.join(ROOT, mp["file"]), "rb").read()
        open(f"{d}/c.pfm", "wb").write(src)
    else:
        cv = craft_canvas(fw, fh, ms["bleed_um"], a.seed, scale=a.c_scale)
        img = np.ascontiguousarray(cv.c[::-1][:, ::-1], dtype="<f4")    # image rows (top first), mirrored in x
        with open(f"{d}/c.pfm", "wb") as f:
            f.write(f"Pf\n{img.shape[1]} {img.shape[0]}\n-1.0\n".encode())
            f.write(img[::-1].tobytes())
        if cv.c.max() > grid[-1]:
            print(f"note: the painted c reaches {cv.c.max():.2f}, the family ends at {grid[-1]:.2f} (clamped)")
    fov = 2 * np.degrees(np.arctan(fh / 2 / CAM_H))
    L = [f"LookAt 0 0 {CAM_H}  0 0 0  0 1 0",
         f'Camera "perspective" "float fov" [ {fov:.6f} ]',
         f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ] "integer seed" [ {a.seed} ]',
         'Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" true',
         f'Film "rgb" "integer xresolution" [ {RES[0]} ] "integer yresolution" [ {RES[1]} ] "string filename" [ "pbrt.exr" ] '
         '"string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true',
         "WorldBegin"]
    for i, u in enumerate(lamp_dirs()):
        c = u * LAMP["distance"]
        n = -u
        ref = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.99 else np.array([0.0, 1.0, 0.0])
        e1 = np.cross(ref, n)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        s = LAMP["size"] / 2
        P = [c - e1 * s - e2 * s, c + e1 * s - e2 * s, c - e1 * s + e2 * s, c + e1 * s + e2 * s]
        L += ["AttributeBegin", f'  AreaLightSource "diffuse" "blackbody L" [ {K_LIGHT:g} ] "float scale" [ 20 ]',
              '  Material "diffuse" "spectrum reflectance" [ 360 0 830 0 ]',
              '  Shape "bilinearmesh" "point3 P" [ ' + " ".join(f"{v:.4f}" for p in P for v in p)
              + ' ] "integer indices" [ 0 1 2 3 ]', "AttributeEnd"]
    # the map spans the frame exactly (u, v over the tile = the frame); the tile is the frame plus a margin, so
    # the map is placed on a tile of the frame's size and the margin is unpainted body under the glaze
    margin = 8.0
    L.append('Texture "co" "spectrum" "familymap" "string family" "film.npz" "string map" "c.pfm" "string wrap" "clamp"')
    tx = ((-fw / 2, fw / 2), (-fh / 2, fh / 2))
    body = body_material(ms["rho"])
    film = 'Material "thindielectric" "float eta" [ 1 ] "texture transmittance" "co"'
    text = coated_tile(*tx, z_base=-ms["h"], thickness=ms["h"], eta=ms["eta"], alpha=ms["alpha"], base=body, film=film)
    # the margin: four coated strips without the film (the glaze continues, so the walk is not cut at the frame)
    for (x0, x1), (y0, y1) in (((-fw / 2 - margin, -fw / 2), (-fh / 2 - margin, fh / 2 + margin)),
                               ((fw / 2, fw / 2 + margin), (-fh / 2 - margin, fh / 2 + margin)),
                               ((-fw / 2, fw / 2), (-fh / 2 - margin, -fh / 2)),
                               ((-fw / 2, fw / 2), (fh / 2, fh / 2 + margin))):
        text += coated_tile((x0, x1), (y0, y1), z_base=-ms["h"], thickness=ms["h"], eta=ms["eta"], alpha=ms["alpha"],
                            base=body)
    if a.tilt:
        # the tile tipped toward the upper lamp (about world x), so its mirror image crosses the frame: the glaze's
        # highlight (26 deg puts the lamp's centre on the mirror direction)
        text = f"AttributeBegin\n  Rotate {-a.tilt} 1 0 0\n" + text + "AttributeEnd\n"
    L.append(text)
    open(f"{d}/scene.pbrt", "w").write("\n".join(L) + "\n")
    json.dump({"f_number": 8.0, "magnification": round(36.0 / (fw * 2), 5), "sensor_width_mm": 36.0,
               "focal_mm": 100.0}, open(f"{d}/optics.json", "w"))
    white = M["white_linear"]
    cam = {"sensor": "canon_eos_5d_mkiv",
           "light": {"blackbody_K": K_LIGHT, "why": "the card's softboxes; weights the diffraction"},
           "white_balance": {"K": K_LIGHT, "why": "on the key light, as a museum photographer sets it on a grey card"},
           "iso": 100,
           "expose": {"percentile": 90, "of_saturation": round(float(white[1]), 4),
                      "why": "the photographer's exposure: the white glaze (the frame's 90th percentile) at the photo's "
                             "white, linear G; a choice of the card"},
           "develop": {"ev": 0.0, "shoulder_from": 0.95, "contrast": 1.0, "pivot": 0.18,
                       "why": "no grade: compared in the photo's own tone"},
           "sharpen": {"amount": 0.0, "sigma_px": 0.7}, "seed": 1}
    json.dump(cam, open(f"{d}/camera.json", "w"), indent=1)
    msj = {k: v for k, v in ms.items() if k not in ("rho", "kappa")}
    msj["rho_450_550_650"] = [round(float(np.interp(l, LAM, np.broadcast_to(ms["rho"], LAM.shape))), 4) for l in (450, 550, 650)]
    json.dump({"set": a.set, "material": msj, "map": a.map, "model": a.model, "tilt_deg": a.tilt, "frame_mm": [fw, fh], "px_per_mm": pxmm, "spp": a.spp},
              open(f"{d}/build.json", "w"), indent=1)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), f"{d}/scene.pbrt", "-o",
                    f"{d}/scene.cycles.json", "--key-K", str(K_LIGHT)], check=True)
    print(f"{d}: frame {fw:.2f} x {fh:.2f} mm at {pxmm} px/mm")


def body_material(rho):
    """pbrt's diffuse body of albedo spectrum rho (on LAM), sampled every 10 nm."""
    lam = np.arange(360, 831, 10)
    v = np.interp(lam, LAM, np.broadcast_to(rho, LAM.shape))
    return 'Material "diffuse" "spectrum reflectance" [ ' + " ".join(f"{l} {x:.4f}" for l, x in zip(lam, v)) + " ]"


# --- develop and compare -------------------------------------------------------------------------
def develop(a):
    for w in a.which:
        raw = os.path.join(a.dir, f"{w}.exr")
        if not os.path.exists(raw):
            print(f"no {raw}")
            continue
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings",
                        os.path.join(a.dir, "camera.json"), "--first", "0", "--out", os.path.join(a.dir, f"dev_{w}"),
                        raw], check=True)


def load_dev(d, w):
    import camera
    img = camera.read_png16(os.path.join(d, f"dev_{w}", "f0000.png"))
    h, wd = img.shape[0] // 2, img.shape[1] // 2
    return img.reshape(h, 2, wd, 2, 3).mean((1, 3))           # 1920 -> 960: back to the photo's px/mm


def compare(a):
    import detail
    M = json.load(open(OUT_M))
    x, y, w, h = CROP
    ph = np.asarray(Image.open(os.path.join(ROOT, PHOTO)).convert("RGB"))[y:y + h, x:x + w].astype(np.float64) / 255
    ims = [("photo", ph)]
    for r in ("pbrt", "cycles"):
        if os.path.exists(os.path.join(a.dir, f"dev_{r}", "f0000.png")):
            ims.append((r, load_dev(a.dir, r)))
    out = os.path.join(a.dir, "cmp")
    os.makedirs(out, exist_ok=True)
    sheet = Image.new("RGB", (w, len(ims) * (h + 4)), (40, 40, 40))
    for i, (_, im) in enumerate(ims):
        sheet.paste(Image.fromarray(np.round(np.clip(im, 0, 1) * 255).astype(np.uint8)), (0, i * (h + 4)))
    sheet.save(os.path.join(out, "sheet.png"))
    # 1:1 side by side of a 400 x 300 detail (the lady's sleeve and hand)
    sx, sy = 380, 160
    sb = Image.new("RGB", (len(ims) * 404, 300), (40, 40, 40))
    for i, (_, im) in enumerate(ims):
        sb.paste(Image.fromarray(np.round(np.clip(im[sy:sy + 300, sx:sx + 400], 0, 1) * 255).astype(np.uint8)), (i * 404, 0))
    sb.save(os.path.join(out, "side_by_side_1to1.png"))
    # the photo's own levels (blue / white bins, as measure) and its white; the same pixels in each render
    q = srgb_decode(ph) / np.asarray(M["white_linear"])
    bins = [(0.88, 9.0), (0.70, 0.88), (0.50, 0.70), (0.30, 0.50), (0.15, 0.30), (0.05, 0.15)]
    masks = [(q[..., 2] >= lo) & (q[..., 2] < hi) for lo, hi in bins]
    white_m = masks[0] & (q[..., 2] / np.maximum(q[..., 0], 1e-4) < 1.25)
    res = {}
    for name, im in ims:
        lin = srgb_decode(np.clip(im, 0, 1))
        wht = np.median(lin[white_m], 0)
        r = {"white_linear": np.round(wht, 4).tolist()}
        for (lo, hi), m in zip(bins[1:], masks[1:]):
            r[f"photo blue/white {lo}-{hi}: rgb/white"] = np.round(np.median(lin[m], 0) / wht, 4).tolist()
        small = np.asarray(Image.fromarray(np.round(np.clip(im, 0, 1) * 255).astype(np.uint8)).resize(
            (detail.W, detail.H), Image.LANCZOS))
        bands, pct = detail.profile(small, np.ones((detail.H, detail.W), bool))
        r["detail_pct (0.7-1.4 ... 11-22 px at 1024)"] = [round(100 * float(b), 2) for b in bands]
        r["luma8_p5_p50_p95"] = [round(float(v)) for v in pct]
        res[name] = r
    res["note"] = ("levels: the photo's pixels binned by its blue / white (measure), the same pixels in each render, "
                   "each divided by its own white (the photo's unpainted glaze). The render's map was inverted from "
                   "the photo through the 1-D model, so where the model can reach the photo's colour the levels agree "
                   "by construction; where they differ, the model cannot make that colour (measure's fit). Detail: "
                   "tools/detail.py's bands on the whole crop")
    json.dump(res, open(os.path.join(out, "numbers.json"), "w"), indent=1)
    print(os.path.join(out, "sheet.png"))
    print(json.dumps(res, indent=1))


# --- analysis: ground, hue after normalising by the ground, edges, grain ----------------------------
M709_XYZ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])


def lab_of(rgb_rel):
    """CIELAB of linear BT.709 colours given relative to a white of (1, 1, 1) (D65)."""
    xyz = np.asarray(rgb_rel) @ M709_XYZ.T
    wn = np.ones(3) @ M709_XYZ.T
    t = xyz / wn
    f = np.where(t > (6 / 29) ** 3, np.cbrt(t), t / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def edge_widths(g, mask_rows=None, lo=0.85, hi=0.35, span=10):
    """10-90% widths (px) of steps in a (H, W) image g (relative to its ground): along rows, where the profile goes
    from above `lo` to below `hi` within `span` px. Returns [(row, x_bright, x_dark, width)], sub-pixel."""
    out = []
    H, W = g.shape
    for y in range(H):
        r = g[y]
        for x in range(span, W - span):
            if r[x] >= 0.6 > r[x + 1]:
                a, b = x - span, x + span + 1
                seg = r[a:b]
                top, bot = seg.max(), seg.min()
                if top < lo or bot > hi:
                    continue
                # the bright side must be on the left, the dark on the right, monotone enough
                il, ir = seg[:span + 1].argmax(), span + 1 + seg[span + 1:].argmin()
                prof = seg[il:ir + 1]
                if len(prof) < 3:
                    continue
                f = (prof - bot) / (top - bot)
                def cross(level):
                    j = np.argmax(f < level)
                    if j == 0:
                        return np.nan
                    return j - 1 + (f[j - 1] - level) / (f[j - 1] - f[j])
                w = cross(0.1) - cross(0.9)
                if np.isfinite(w) and w > 0:
                    out.append((y, a + il, a + ir, w))
    return out


def analyze(a):
    import camera
    M = json.load(open(OUT_M))
    x, y, w, h = CROP
    ph = np.asarray(Image.open(os.path.join(ROOT, PHOTO)).convert("RGB"))[y:y + h, x:x + w].astype(np.float64) / 255
    ims = [("photo", srgb_decode(ph))]
    for d in a.dirs:
        for r in ("pbrt", "cycles"):
            if os.path.exists(os.path.join(d, f"dev_{r}", "f0000.png")):
                ims.append((f"{os.path.basename(d.rstrip('/'))} {r}", srgb_decode(np.clip(load_dev(d, r), 0, 1))))
    q_ph = ims[0][1] / np.asarray(M["white_linear"])
    ground = (q_ph[..., 2] >= 0.88) & (q_ph[..., 2] / np.maximum(q_ph[..., 0], 1e-4) < 1.25)
    ground &= np.abs(q_ph[..., 1] - 1) < 0.08                    # not the specks and stains
    bins = {"light wash (photo B/W 0.5-0.7)": (0.5, 0.7), "mid wash (0.3-0.5)": (0.3, 0.5),
            "full stroke (0.05-0.15)": (0.05, 0.15)}
    res = {"ground_px": int(ground.sum()), "how": "each image divided by the median RGB of its own clean ground "
           "(the photo's unpainted glaze, specks out: von Kries); Lab with that ground as white (D65)"}
    for name, lin in ims:
        g = np.median(lin[ground], 0)
        r = {"ground_linear": np.round(g, 4).tolist(), "ground_r/g, b/g": [round(g[0] / g[1], 4), round(g[2] / g[1], 4)]}
        n = lin / g
        for bn, (lo, hi) in bins.items():
            m = (q_ph[..., 2] >= lo) & (q_ph[..., 2] < hi)
            v = np.median(n[m], 0)
            L, A, B = lab_of(v)
            r[bn] = {"rgb/ground": np.round(v, 4).tolist(), "Lab": [round(L, 1), round(A, 1), round(B, 1)],
                     "hue_deg": round(float(np.degrees(np.arctan2(B, A)) % 360), 1),
                     "chroma": round(float(np.hypot(A, B)), 1)}
        # grain: the ground's pixel-to-pixel std in G (relative), and the same after a 3x3 mean (fine noise)
        G = n[..., 1]
        hp = G - ndi_uniform(G, 5)
        r["ground_grain_pct (G, minus a 5 px mean)"] = round(100 * float(hp[ground].std()), 2)
        res[name] = r
    gp = res["photo"]["ground_linear"]
    for name, _ in ims[1:]:
        gr = res[name]["ground_linear"]
        res[name]["ground_dE_vs_photo"] = round(float(np.linalg.norm(lab_of(np.asarray(gr) / gr[1]) - lab_of(np.asarray(gp) / gp[1]))), 2)
        for bn in bins:
            dh = (res[name][bn]["hue_deg"] - res["photo"][bn]["hue_deg"] + 180) % 360 - 180
            res[name][bn]["hue_minus_photo_deg"] = round(float(dh), 1)
    # edges: on the photo's normalised G, where the photo has a clean white-to-dark step; the same rows and columns
    # in each render (aligned: the map is the photo's own), widths in px at the photo's px/mm
    gph = ims[0][1][..., 1] / np.median(ims[0][1][ground], 0)[1]
    found = edge_widths(gph)
    found += [(-1 - yy, xb, xd, ww) for (yy, xb, xd, ww) in edge_widths(gph[:, ::-1])]       # dark-to-bright steps
    res["edges"] = {"n": len(found), "photo_10_90_px_median": round(float(np.median([e[3] for e in found])), 3)}
    for name, lin in ims[1:]:
        gg = lin[..., 1] / np.median(lin[ground], 0)[1]
        ws = []
        for (yy, xb, xd, ww) in found:
            row = gg[yy] if yy >= 0 else gg[-1 - yy][::-1]
            seg = row[xb:xd + 1]
            if len(seg) < 3:
                continue
            top, bot = row[max(xb - 3, 0):xb + 1].max(), row[xd:xd + 4].min()
            if top - bot < 0.3:
                continue
            f = (seg - bot) / (top - bot)
            j9, j1 = np.argmax(f < 0.9), np.argmax(f < 0.1)
            if j9 == 0 or j1 == 0:
                continue
            c9 = j9 - 1 + (f[j9 - 1] - 0.9) / (f[j9 - 1] - f[j9])
            c1 = j1 - 1 + (f[j1 - 1] - 0.1) / (f[j1 - 1] - f[j1])
            ws.append(c1 - c9)
        res["edges"][name] = {"n": len(ws), "10_90_px_median": round(float(np.median(ws)), 3) if ws else None}
    res["edges"]["px_per_mm"] = M["scale"]["px_per_mm"]
    out = os.path.join(a.dirs[0], "cmp", "analysis.json") if a.dirs else None
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1, ensure_ascii=False))


def ndi_uniform(x, n):
    from scipy import ndimage
    return ndimage.uniform_filter(x, n)


def read_c(path):
    with open(path, "rb") as f:
        f.readline()
        w, h = map(int, f.readline().split())
        f.readline()
        a = np.frombuffer(f.read(), "<f4").reshape(h, w)
    return a[::-1][:, ::-1].astype(np.float64)        # back to the photo's orientation


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("measure")
    q.add_argument("--set", default="kangxi")
    q = sub.add_parser("build")
    q.add_argument("--out", required=True)
    q.add_argument("--set", default="kangxi")
    q.add_argument("--spp", type=int, default=64)
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--map", default="photo", choices=["photo", "craft"])
    q.add_argument("--h", type=float, help="override the glaze's thickness (mm), for the walk test")
    q.add_argument("--tilt", type=float, default=0.0, help="tip the tile by this many degrees toward the upper lamp")
    q.add_argument("--c-scale", type=float, default=1.0, help="--map craft: scale craft.json's c (the fitted levels)")
    q.add_argument("--model", default="co", choices=["co", "iron"],
                   help="the map: co, inverted with cobalt only; iron, with the iron-like companion (measure's fit)")
    q = sub.add_parser("develop")
    q.add_argument("dir")
    q.add_argument("--which", nargs="+", default=["cycles", "pbrt"])
    q = sub.add_parser("compare")
    q.add_argument("dir")
    q = sub.add_parser("analyze")
    q.add_argument("dirs", nargs="*")
    a = ap.parse_args()
    {"measure": measure, "build": build, "develop": develop, "compare": compare, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
