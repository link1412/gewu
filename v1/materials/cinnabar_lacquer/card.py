"""The material card of the cinnabar lacquer: a carved test tile (the Cleveland lotus dish 1918.933, traced, crafts/carving)
on a grey backdrop, lit from the top like the museum's front photograph, shot at the photo's scale
(docs/materials/cinnabar_lacquer.md, 材质卡).

    python3 -I materials/cinnabar_lacquer/card.py measure                       # the photo: px/mm, colours -> out/.../measured_cma.json
    python3 -I materials/cinnabar_lacquer/card.py geom --out G [--state S.json|new] [--alpha-pairs SKIN:RUB ...]  # relief, processes, maps, meshes (~60 s)
    python3 -I materials/cinnabar_lacquer/card.py scene --geom G --out F [--frame overview|detail] [--rot DEG] [--alpha-pair SKIN:RUB] [--S S]
    python3 -I materials/cinnabar_lacquer/card.py develop F [--raw-ref R]      # raw EXR -> PNG (tools/camera.py)
    python3 -I materials/cinnabar_lacquer/card.py compare F [--b F2]            # side by side and numbers against the photo

World: mm, z up from the tile's substrate; the camera above looking down; image x = world +x, image up = +y; the dish's
centre at the origin. Frames: 'overview' is 1920 px of the photo's scale (126 mm) rendered at 960x540 (half the photo's
resolution), 'detail' is 960 px of the photo's scale (63 mm) at 960x540 (the photo's own resolution).

The lacquer surface: the shared 'clear layer over a diffuse body' (docs/coats.md, tools/coat.py) in its curved form:
true geometry, triangle meshes offset along the normal (here along z: the relief is a height field), the dielectric
surface (n 1.52, GGX alpha from a map, refractivenee) over the diffuse body (the familymap of the layers) coat_gap_mm
below. No medium and no film in between: in carved lacquer the pigment is in the binder all the way down, so the
binder's absorption is in the body (Kubelka-Munk, lacquer.py), and the skin above it is only the interface.
coat.py's coated_tile is flat, so the meshes are written here (crafts/carving write_ply_grid).
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "crafts/carving"))
import lacquer  # noqa: E402
import carve  # noqa: E402
import patterns  # noqa: E402
for _c in ("wear", "weathering", "dust", "duanwen"):
    sys.path.insert(0, os.path.join(ROOT, "crafts", _c))
import wear  # noqa: E402
import weathering  # noqa: E402
import dust  # noqa: E402
import duanwen  # noqa: E402
STATE = os.path.join(HERE, "state_cma1918933.json")
PROCESSES = {"wear": wear, "weathering": weathering, "dust": dust, "duanwen": duanwen}


def process_state(path):
    """{process: {param: value}}: each process's 'new' values, overridden by the state file's (None/'new' = new)."""
    S = json.load(open(path)) if path and path != "new" else {}
    out = {}
    for name, mod in PROCESSES.items():
        P = {k: v.get("new") for k, v in mod.load()["parameters"].items()}
        for k, v in S.get(name, {}).items():
            if k not in P:
                raise SystemExit(f"{path}: {name}.{k} is not a parameter of crafts/{name}")
            P[k] = v["value"]
        out[name] = P
    return out


def with_dust(m):
    """The material plus a 'dust' row: grime is not a lacquer, its colour is crafts/dust's."""
    m["body"]["dust"] = {"spectrum": "flat", "value": dust.load()["parameters"]["reflectance"]["value"]}
    return m


def alpha_map(alpha0, skin, E, rubbed, scratch, scratch_alpha):
    """GGX alpha: the material's alpha0; the weathered skin where not touched, the rubbed surface where touched
    (in quadrature with alpha0); inside scratches at least scratch_alpha."""
    a = np.sqrt(alpha0 ** 2 + ((1 - E) * skin) ** 2 + (E * (rubbed or 0)) ** 2)
    return np.where(scratch, np.maximum(a, scratch_alpha or 0), a) if scratch is not None else a

PHOTO = os.path.join(ROOT, "ref/carved_lacquer/cma/1918.933_print.jpg")
MEASURED = os.path.join(ROOT, "out/materials/cinnabar_lacquer/measured_cma.json")
DISH_MM = 159.0                 # Cleveland 1918.933 'overall 15.9 cm', taken as the diameter [I]
TILE = (110.0, 90.0)            # mm, the test tile; the overview frame (126 x 71 mm) shows backdrop at both sides
TILE_T = 3.0                    # mm, the tile's thickness to the backdrop
CAM_DIST = 800.0                # mm, pinhole
FOCAL_MM, SENSOR_W, F_NUMBER = 100.0, 36.0, 8.0
# layer stack of the lotus dish, from the substrate up: a black layer under the red. Dark lines run along the foot of
# the cuts in the photos [M]; carved red lacquer has dark 'marker' layers exposed at cuts and losses (NGV conservation
# essay, Shaw 2023 [I]). Its thickness [A] sets the lines' width with the cut's angle; the V cuts' feet (0.25-0.3 mm)
# reach into it. (A pale layer under it, read off alt0, was dropped: no source for a yellow ground on this dish.)
STACK = [("black", 0.40), ("red", 10.0)]


# --- the photo -------------------------------------------------------------------------------
def dish_mask(im):
    R, G = im[..., 0].astype(float), im[..., 1].astype(float)
    m = ndi.binary_opening(R - G > 35, iterations=3)
    lab, n = ndi.label(m)
    m = lab == (np.argmax(ndi.sum(m, lab, range(1, n + 1))) + 1)
    return ndi.binary_fill_holes(m)


def lin(im8):
    x = np.asarray(im8, np.float64) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def measure(a):
    im = np.asarray(Image.open(PHOTO).convert("RGB"))
    m = dish_mask(im)
    ys, xs = np.nonzero(m)
    w, h = xs.max() - xs.min(), ys.max() - ys.min()
    px = (w + h) / 2 / DISH_MM
    cx, cy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
    far = ~ndi.binary_dilation(m, iterations=60)
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    side = far & (np.abs(yy - cy) < 35.5 * px)          # the backdrop beside the dish, at the height of the frame
    bg = lin(im[side]).mean(0)
    out = {"photo": os.path.relpath(PHOTO, ROOT), "dish_px": [int(w), int(h)], "px_per_mm": round(px, 4),
           "centre_px": [round(cx, 1), round(cy, 1)],
           "backdrop_linear": [round(float(v), 4) for v in bg],
           "backdrop_srgb8_median": [int(v) for v in np.median(im[side], 0)],
           "note": "px/mm from the dish's bounding box (mean of width and height) over 159 mm [M]; the backdrop beside the dish, rows within +-35.5 mm of the centre"}
    for name, (wmm, hmm) in (("overview", (1920 / px, 1080 / px)), ("detail", (960 / px, 540 / px))):
        crop = photo_crop(im, out, wmm, hmm)
        L = lin(crop).reshape(-1, 3)
        med = np.median(L, 0)
        out[name] = {"frame_mm": [round(wmm, 2), round(hmm, 2)],
                     "median_linear": [round(float(v), 4) for v in med],
                     "median_over_backdrop": [round(float(v), 4) for v in med / bg]}
    os.makedirs(os.path.dirname(MEASURED), exist_ok=True)
    json.dump(out, open(MEASURED, "w"), indent=1)
    print(json.dumps(out, indent=1))


def photo_crop(im, M, wmm, hmm, centre_mm=(0.0, 0.0)):
    px = M["px_per_mm"]
    cx, cy = M["centre_px"]
    cx, cy = cx + centre_mm[0] * px, cy - centre_mm[1] * px
    w, h = int(round(wmm * px)), int(round(hmm * px))
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    return np.asarray(im)[y0:y0 + h, x0:x0 + w]


# --- geometry --------------------------------------------------------------------------------
def geom(a):
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    tx, ty = TILE[0] / 2, TILE[1] / 2
    rel = carve.Relief(-tx, tx, -ty, ty, a.step, 0.0)
    jit = (lambda bb: carve.facet_jitter(bb, a.facet_cell_mm, a.facet_amp_mm, rng)) if a.facet_amp_mm > 0 else None
    keep = lambda bb: bb[2] > -tx and bb[0] < tx and bb[3] > -ty and bb[1] < ty
    patterns.lotus_dish(rel, keep=keep, jitter=jit)
    m = lacquer.load()
    eta, alpha0, gap = lacquer.interface(m)
    # the processes on the surface, by their parameters (a new piece: all at 'new')
    P = process_state(a.state)
    if a.skin_alpha is not None:
        P["weathering"]["skin_alpha"] = a.skin_alpha
    h = wear.round_edges(rel.h, a.step, P["wear"])
    g = wear.gap(h, a.step, P["wear"]["touch_radius_mm"] or 8.0)   # (8 mm for the dust when nothing rubs [A])
    E = wear.touch(h, a.step, P["wear"], g)
    scr_b, scr_m, nscr = wear.scratches(h.shape, a.step, P["wear"], rng)
    crk_b, crk_m, crk_log = duanwen.cracks(h.shape, a.step, rel.x, rel.y, P["duanwen"], rng)
    grime = dust.mask(h, a.step, crk_m, P["dust"])
    m = with_dust(m)
    def amap(skin, rubbed=None):
        return alpha_map(alpha0, skin, E, P["wear"]["rubbed_alpha"] if rubbed is None else rubbed,
                         scr_m, P["wear"]["scratch_alpha"])
    aged = {"bump": scr_b + crk_b, "grime": grime, "alpha": amap(P["weathering"]["skin_alpha"]),
            "log": {"scratches": nscr, "cracks": crk_log, "touched_fraction": round(float((E > 0.5).mean()), 4),
                    "dust_fraction": round(float(grime.mean()), 4)}}
    k = a.mesh_every
    hc = carve.downsample(h, k)
    xc, yc = carve.downsample(rel.x[None], k)[0], carve.downsample(rel.y[:, None], k)[:, 0]
    if (len(xc) - 1) * k != len(rel.x) - 1 or (len(yc) - 1) * k != len(rel.y) - 1:
        raise SystemExit("the grid size must be 1 + a multiple of mesh_every in both directions")
    # sub-mesh detail -> bump map: what the fine field has beyond the mesh's bilinear surface, plus the scratches and cracks (crafts/wear, duanwen)
    bump = h - carve.bilinear_up(hc, k, h.shape) + aged["bump"]
    # layers exposed (coarse, one texel per vertex); grime (crafts/dust) over them
    idx, names = carve.layer_index(hc, STACK)
    names = ["dust"] + names                       # dust next to the black: a grime/black edge blends through dark
    idx = idx + 1
    grime_c = aged["grime"][::k, ::k][:hc.shape[0], :hc.shape[1]]
    idx = np.where(grime_c, 0.0, idx)
    hs = hc.copy()                                 # the skirt (outer ring of vertices) drops to the backdrop
    hs[0, :] = hs[-1, :] = hs[:, 0] = hs[:, -1] = -TILE_T
    s = a.step
    nxf, nyf = len(rel.x), len(rel.y)
    uv_ext = (rel.x[0] - s / 2, rel.x[0] - s / 2 + nxf * s, rel.y[0] - s / 2, rel.y[0] - s / 2 + nyf * s)
    nv, nt = carve.write_ply_grid(os.path.join(a.out, "coat.ply"), xc, yc, hs, 0.0, uv_ext)
    carve.write_ply_grid(os.path.join(a.out, "body.ply"), xc, yc, hs, -gap, uv_ext)
    carve.write_pfm(os.path.join(a.out, "bump.pfm"), bump)
    carve.write_pfm(os.path.join(a.out, "layers.pfm"), idx)
    carve.write_pfm(os.path.join(a.out, "alpha.pfm"), aged["alpha"])
    for pr in a.alpha_pairs:                       # alpha maps for other (skin, rubbed) alphas, same marks: for the fit
        sk, rb = (float(v) for v in pr.split(":"))
        carve.write_pfm(os.path.join(a.out, f"alpha_{sk:g}_{rb:g}.pfm"), amap(sk, rb))
    order = lacquer.write_family(os.path.join(a.out, "family.npz"), m, names, S=a.S)
    nxc, nyc = len(xc), len(yc)
    coarse = {"uscale": nxf * s / (nxc * k * s), "udelta": (k - 1) * s / 2 / (nxc * k * s),
              "vscale": nyf * s / (nyc * k * s), "vdelta": (k - 1) * s / 2 / (nyc * k * s)}
    frac = {n: round(float((idx == i).mean()), 4) for n, i in order.items()}
    info = {"tile_mm": TILE, "step_mm": s, "mesh_every": k, "grid": [nxf, nyf], "mesh": [nxc, nyc],
            "vertices": nv, "triangles": nt, "uv_extent": uv_ext, "coarse_map_uv": coarse,
            "stack": STACK, "family_order": order, "layer_area_fraction": frac,
            "height_mm": [round(float(h.min()), 3), round(float(h.max()), 3)],
            "bump_rms_um": round(float(bump.std() * 1000), 2), "processes": P, "process_log": aged["log"],
            "alpha0": alpha0, "alpha_pairs": a.alpha_pairs, "eta": eta, "coat_gap_mm": gap, "S_per_mm": a.S,
            "args": {k_: v for k_, v in vars(a).items() if k_ not in ("out", "cmd")}, "motifs": rel.log}
    json.dump(info, open(os.path.join(a.out, "geom.json"), "w"), indent=1)
    print(json.dumps({k_: v for k_, v in info.items() if k_ not in ("motifs",)}))


# --- scene -----------------------------------------------------------------------------------
def scene(a):
    G = json.load(open(os.path.join(a.geom, "geom.json")))
    M = json.load(open(MEASURED))
    px = M["px_per_mm"]
    os.makedirs(a.out, exist_ok=True)
    gdir = os.path.relpath(os.path.abspath(a.geom), os.path.abspath(a.out))
    res = tuple(int(v) for v in a.res.split("x"))
    wmm = (1920 if a.frame == "overview" else 960) / px
    hmm = wmm * 9 / 16
    fov = math.degrees(2 * math.atan(hmm / 2 / CAM_DIST))
    L = []
    w = L.append
    w(f"# cinnabar lacquer material card (materials/cinnabar_lacquer/card.py), frame {a.frame}, rot {a.rot}")
    w(f"LookAt 0 0 {CAM_DIST} 0 0 0  0 1 0")
    w(f'Camera "perspective" "float fov" [ {fov:.6f} ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 32 ] "bool refractivenee" true')
    w(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
      f'"string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true')
    w("WorldBegin")

    def softbox(direction, dist, size, scale, K=5500):
        n = np.asarray(direction, float)
        n /= np.linalg.norm(n)
        centre = n * dist
        up = np.array([0, 0, 1.0]) if abs(n[2]) < 0.95 else np.array([0, 1.0, 0])
        u = np.cross(up, n)
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        cs = [centre - size / 2 * u - size / 2 * v, centre + size / 2 * u - size / 2 * v,
              centre - size / 2 * u + size / 2 * v, centre + size / 2 * u + size / 2 * v]
        # facing the origin: pbrt's bilinear patch normal is (p10 - p00) x (p01 - p00) = u x v = n; it must point to -n
        cs = [cs[1], cs[0], cs[3], cs[2]]
        w("AttributeBegin")
        w(f'  AreaLightSource "diffuse" "blackbody L" [ {K} ] "float scale" [ {scale} ]')
        w('  Material "diffuse" "rgb reflectance" [ 0 0 0 ]')
        w('  Shape "bilinearmesh" "point3 P" [ ' + " ".join(f"{x:.4f}" for c in cs for x in c) + ' ] "integer indices" [ 0 1 2 3 ]')
        w("AttributeEnd")

    softbox(a.key_dir, a.key_dist, a.key_size, 1.0)
    softbox(a.fill_dir, a.fill_dist, a.fill_size, a.fill_scale)
    w("AttributeBegin")
    w(f'  Material "diffuse" "spectrum reflectance" [ 360 {a.backdrop} 830 {a.backdrop} ]')
    w(f'  Shape "bilinearmesh" "point3 P" [ -400 -400 {-TILE_T} 400 -400 {-TILE_T} -400 400 {-TILE_T} 400 400 {-TILE_T} ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    c = G["coarse_map_uv"]
    cm = f'"float uscale" [ {c["uscale"]:.9g} ] "float udelta" [ {c["udelta"]:.9g} ] "float vscale" [ {c["vscale"]:.9g} ] "float vdelta" [ {c["vdelta"]:.9g} ]'
    w(f'Texture "bump" "float" "imagemap" "string filename" "{gdir}/bump.pfm" "string wrap" "clamp"')
    if a.alpha_pair:
        sk, rb = (float(v) for v in a.alpha_pair.split(":"))
        amap = f"alpha_{sk:g}_{rb:g}.pfm"
    else:
        amap = "alpha.pfm"
    if not os.path.exists(os.path.join(a.geom, amap)):
        raise SystemExit(f"{amap}: not in the geometry (geom --alpha-pairs)")
    w(f'Texture "alpha" "float" "imagemap" "string filename" "{gdir}/{amap}" "string wrap" "clamp"')
    fam = f"{gdir}/family.npz"
    if a.S is not None:                     # a colour variant: this frame's own family, same layers
        lacquer.write_family(os.path.join(a.out, "family.npz"), with_dust(lacquer.load()), list(G["family_order"]), S=a.S)
        fam = "family.npz"
    w(f'Texture "lay" "spectrum" "familymap" "string family" "{fam}" "string map" "{gdir}/layers.pfm" "string wrap" "clamp" {cm}')
    w("AttributeBegin")
    if a.rot:
        w(f"  Translate 0 0 2")
        w(f"  Rotate {a.rot} 0 1 0")
        w(f"  Translate 0 0 -2")
    w("  AttributeBegin")
    w(f'    Material "dielectric" "float eta" [ {G["eta"]} ] "texture roughness" "alpha" "bool remaproughness" false '
      f'"bool refractivenee" true "texture displacement" "bump"')
    w(f'    Shape "plymesh" "string filename" [ "{gdir}/coat.ply" ]')
    w("  AttributeEnd")
    w("  AttributeBegin")
    w('    Material "diffuse" "texture reflectance" "lay" "texture displacement" "bump"')
    w(f'    Shape "plymesh" "string filename" [ "{gdir}/body.ply" ]')
    w("  AttributeEnd")
    w("AttributeEnd")
    open(os.path.join(a.out, "scene.pbrt"), "w").write("\n".join(L) + "\n")
    json.dump({"f_number": F_NUMBER, "magnification": round(SENSOR_W / wmm, 5), "sensor_width_mm": SENSOR_W,
               "focal_mm": FOCAL_MM}, open(os.path.join(a.out, "optics.json"), "w"))
    cam = {"sensor": "canon_eos_5d_mkiv",
           "light": {"blackbody_K": 5500, "why": "the card's soft boxes (card.py)"},
           "white_balance": {"K": 5500, "why": "on the grey backdrop under that light"},
           "iso": 100,
           "expose": ({"raw_ref": a.raw_ref} if a.raw_ref else {"percentile": 50}) | {"of_saturation": 0.5,
                      "why": "the photographer's exposure, the same for every frame of the card: raw_ref is set (card.py "
                             "calibrate) so that the backdrop beside the tile reads like the photo's backdrop. A choice of the card"},
           "develop": {"ev": 0.0, "shoulder_from": 0.9, "contrast": 1.0, "pivot": 0.18, "why": "no grade"},
           "sharpen": {"amount": 0.0, "sigma_px": 0.7}, "seed": 1}
    json.dump(cam, open(os.path.join(a.out, "camera.json"), "w"), indent=1)
    json.dump({"frame": a.frame, "frame_mm": [round(wmm, 3), round(hmm, 3)], "rot_deg": a.rot, "res": res,
               "alpha_pair": a.alpha_pair or "%g:%g" % (G["processes"]["weathering"]["skin_alpha"], G["processes"]["wear"]["rubbed_alpha"]), "S_per_mm": G["S_per_mm"] if a.S is None else a.S, "geom": os.path.abspath(a.geom),
               "args": {k: v for k, v in vars(a).items() if k not in ("cmd",)}},
              open(os.path.join(a.out, "frame.json"), "w"), indent=1)
    print(os.path.join(a.out, "scene.pbrt"))


# --- develop and compare ---------------------------------------------------------------------
def develop(a):
    d = a.dir
    raw = os.path.join(d, a.raw)
    c = json.load(open(os.path.join(d, "camera.json")))
    if a.raw_ref:
        c["expose"]["raw_ref"] = a.raw_ref
    elif "raw_ref" not in c["expose"]:            # freeze the metered exposure, so that 'calibrate' can scale it
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import camera
        c["expose"]["raw_ref"] = float(f"{camera.exposure_ref([raw], c['expose'])[0]:.6g}")
    json.dump(c, open(os.path.join(d, "camera.json"), "w"), indent=1)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings",
                    os.path.join(d, "camera.json"), "--first", "0", "--out", os.path.join(d, "dev"), raw], check=True)


def read_dev(d):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import camera
    return np.round(camera.read_png16(os.path.join(d, "dev", "f0000.png")) * 255).astype(np.uint8)


def card_at_photo_scale(d, M):
    """The developed card (1920x1080) resampled to the photo's px/mm."""
    F = json.load(open(os.path.join(d, "frame.json")))
    im = read_dev(d)
    w, h = int(round(F["frame_mm"][0] * M["px_per_mm"])), int(round(F["frame_mm"][1] * M["px_per_mm"]))
    return np.asarray(Image.fromarray(im).resize((w, h), Image.LANCZOS)), F


def backdrop_strips(im, F):
    """Mean linear colour of the backdrop strips beside the tile (overview frame only)."""
    wmm = F["frame_mm"][0]
    if wmm / 2 < TILE[0] / 2 + 2:
        return None
    px = im.shape[1] / wmm
    edge = int((wmm / 2 - TILE[0] / 2 - 1.5) * px)
    h = im.shape[0]
    s = np.concatenate([im[h // 4:3 * h // 4, 2:edge].reshape(-1, 3), im[h // 4:3 * h // 4, -edge:-2].reshape(-1, 3)])
    return lin(s).mean(0)


def compare(a):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import detail
    M = json.load(open(MEASURED))
    card, F = card_at_photo_scale(a.dir, M)
    photo = photo_crop(Image.open(PHOTO).convert("RGB"), M, F["frame_mm"][0], F["frame_mm"][1])
    eff = 960 / F["res"][0] * (1920 / 960 if F["frame"] == "overview" else 1)
    if eff > 1.01:            # bring the photo to the card's effective resolution
        hh, ww = photo.shape[:2]
        photo = np.asarray(Image.fromarray(photo).resize((int(ww / eff), int(hh / eff)), Image.LANCZOS)
                           .resize((ww, hh), Image.BICUBIC))
    hh, ww = min(photo.shape[0], card.shape[0]), min(photo.shape[1], card.shape[1])
    photo, card = photo[:hh, :ww], card[:hh, :ww]
    out = os.path.join(a.dir, "cmp")
    os.makedirs(out, exist_ok=True)
    sheet = Image.new("RGB", (ww * 2 + 6, hh), (40, 40, 40))
    sheet.paste(Image.fromarray(photo), (0, 0))
    sheet.paste(Image.fromarray(card), (ww + 6, 0))
    sp = os.path.join(out, "side_by_side.png")
    sheet.save(sp)
    res = {"frame": F["frame"], "rot_deg": F["rot_deg"], "eff": round(eff, 3)}
    # tile region only (the photo's dish vs the card's tile): the central 80% of width, 90% of height of the frame
    yy, xx = np.mgrid[0:hh, 0:ww]
    half_w = min(ww / 2, TILE[0] / 2 * M["px_per_mm"] - 4)
    reg = (np.abs(xx - ww / 2) < 0.9 * half_w) & (np.abs(yy - hh / 2) < 0.45 * hh)
    bands_noise = None
    if a.b:
        cardB, _ = card_at_photo_scale(a.b, M)
        cardB = cardB[:hh, :ww]
        bands_noise = cardB
    for name, im in (("photo", photo), ("card", card)):
        small = np.asarray(Image.fromarray(im).resize((detail.W, detail.H), Image.LANCZOS))
        m = np.asarray(Image.fromarray(reg.astype(np.uint8) * 255).resize((detail.W, detail.H), Image.NEAREST)) > 0
        bands, pct = detail.profile(small, m)
        if name == "card" and bands_noise is not None:
            sb = np.asarray(Image.fromarray(bands_noise).resize((detail.W, detail.H), Image.LANCZOS))
            Lg = lambda x: (lin(x) @ np.array([0.2126, 0.7152, 0.0722])) ** (1 / 2.2)
            LA, LB = Lg(small), Lg(sb)
            Ln, Lc = (LA - LB) / np.sqrt(2), (LA + LB) / 2
            nb = [float(np.sqrt(np.mean((ndi.gaussian_filter(Ln, lo) - ndi.gaussian_filter(Ln, hi))[m] ** 2)) / Lc[m].mean())
                  for lo, hi in detail.BANDS]
            res["noise_one_image_pct"] = [round(100 * v, 2) for v in nb]
            bands = [float(np.sqrt(max(b * b - n * n, 0.0))) for b, n in zip(bands, nb)]   # one image carries all of it
        L = lin(im[reg])
        res[name] = {"detail_pct": [round(100 * float(b), 2) for b in bands],
                     "luma8_p5_p50_p95": [round(float(x)) for x in pct],
                     "median_linear": [round(float(v), 4) for v in np.median(L, 0)],
                     "p95_linear": [round(float(v), 4) for v in np.percentile(L, 95, 0)]}
    bk = backdrop_strips(card, F)
    if bk is not None:
        res["card_backdrop_linear"] = [round(float(v), 4) for v in bk]
        res["photo_backdrop_linear"] = M["backdrop_linear"]
        res["over_backdrop"] = {"card": [round(m_ / b_, 4) for m_, b_ in zip(res["card"]["median_linear"], bk)],
                                "photo": [round(m_ / b_, 4) for m_, b_ in zip(res["photo"]["median_linear"], M["backdrop_linear"])]}
    for nm in ("photo", "card"):
        r, g, b = res[nm]["median_linear"]
        res[nm]["G_over_R"], res[nm]["B_over_R"] = round(g / r, 4), round(b / r, 4)
    json.dump(res, open(os.path.join(out, "numbers.json"), "w"), indent=1)
    print(sp)
    print(json.dumps(res, indent=1))


def calibrate(a):
    """raw_ref so that the overview's backdrop strips read like the photo's backdrop (linear G), from one developed
    overview: the chain is linear below its shoulder, so the new raw_ref = old * (card backdrop / photo backdrop)."""
    M = json.load(open(MEASURED))
    card, F = card_at_photo_scale(a.dir, M)
    bk = backdrop_strips(card, F)
    if bk is None:
        raise SystemExit("calibrate needs the overview frame (backdrop beside the tile)")
    c = json.load(open(os.path.join(a.dir, "camera.json")))
    old = c["expose"]["raw_ref"]
    new = old * bk[1] / M["backdrop_linear"][1]
    print(json.dumps({"card_backdrop_linear": [round(float(v), 4) for v in bk], "photo": M["backdrop_linear"],
                      "raw_ref_old": old, "raw_ref_new": float(f"{new:.6g}")}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("measure")
    g = sub.add_parser("geom")
    g.add_argument("--out", required=True)
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--step", type=float, default=0.04, help="mm, the fine grid (bump map)")
    g.add_argument("--mesh-every", type=int, default=2, help="mesh vertex every N fine samples")
    g.add_argument("--state", default=STATE, help="process parameters of the piece (json), or 'new'")
    g.add_argument("--skin-alpha", type=float, help="override weathering.skin_alpha (the fit)")
    g.add_argument("--alpha-pairs", nargs="*", default=[],
                   help="also write alpha maps for these weathering.skin_alpha:wear.rubbed_alpha pairs (the fit)")
    g.add_argument("--facet-cell-mm", type=float, default=1.5, help="knife strokes: one facet per this many mm [A]")
    g.add_argument("--facet-amp-mm", type=float, default=0.02)
    g.add_argument("--S", type=float, default=None, help="the red's KM scattering, 1/mm (binder absorption over it) [F]; "
                   "material.json's unless given, 0 = no binder absorption")
    s = sub.add_parser("scene")
    s.add_argument("--geom", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--frame", default="overview", choices=["overview", "detail"])
    s.add_argument("--rot", type=float, default=0.0, help="deg about the image's vertical axis")
    s.add_argument("--alpha-pair", help="skin:rubbed: use the geometry's alpha map for this pair (geom --alpha-pairs)")
    s.add_argument("--S", type=float, help="the red's KM scattering (1/mm) for this frame's family; geom's if not given, 0 = none")
    s.add_argument("--res", default="960x540")
    s.add_argument("--spp", type=int, default=128)
    s.add_argument("--raw-ref", type=float, help="the exposure (from 'calibrate'); the median's 50%% of saturation if not given")
    s.add_argument("--backdrop", type=float, default=0.25, help="the grey backdrop's reflectance [A]")
    # the light, read off the photo: highlights on the seeds sit toward the top -> a key above the top edge [M, card.py doc]
    s.add_argument("--key-dir", type=float, nargs=3, default=[-0.18, 0.80, 0.58])
    s.add_argument("--key-dist", type=float, default=900.0)
    s.add_argument("--key-size", type=float, default=350.0)
    # the fill well off the camera's mirror direction (the photo's flat field shows no glare): low, from the bottom
    s.add_argument("--fill-dir", type=float, nargs=3, default=[0.25, -0.75, 0.6])
    s.add_argument("--fill-dist", type=float, default=1200.0)
    s.add_argument("--fill-size", type=float, default=306.0)
    s.add_argument("--fill-scale", type=float, default=0.5)
    for nm in ("develop", "compare", "calibrate"):
        q = sub.add_parser(nm)
        q.add_argument("dir")
        q.add_argument("--b", help="compare: a second render (other seed) to take the render noise off")
        q.add_argument("--raw-ref", type=float)
        q.add_argument("--raw", default="x.exr")
    a = ap.parse_args()
    if a.cmd == "geom" and a.S is None:
        a.S = lacquer.load()["body"]["red"]["scattering_S_per_mm"]["value"]
    {"measure": measure, "geom": geom, "scene": scene, "develop": develop, "compare": compare,
     "calibrate": calibrate}[a.cmd](a)


if __name__ == "__main__":
    main()
