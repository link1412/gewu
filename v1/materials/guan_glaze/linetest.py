"""A small test tile for the crack line's optics (round 2): the card's glaze, light and camera, at the photo's own
scale (32.23 px/mm at 960x540: a 29.8 x 16.8 mm frame), with twelve straight cracks of 6 mm in four orientations,
and one physical candidate per render. The line's cross profile is then measured with lines.py, as on the photo.

    python3 -I materials/guan_glaze/linetest.py build --variant gap_v --out out/materials/guan_glaze/lt/gap_v [--seed 1]
    python3 -I materials/guan_glaze/linetest.py develop DIR          # raw EXR -> linear BT.709 lin.npy (no noise)
    python3 -I materials/guan_glaze/linetest.py variants              # list them

No speckle, no mottling: a plain glaze, so the profile is the crack's alone. The glaze, light and camera are the
card's (card.py); the cracks are crafts/crackle/faces.py, the deposit crafts/deposition/deposit.py.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "crafts", "crackle"))
sys.path.insert(0, os.path.join(ROOT, "crafts", "deposition"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import card  # noqa: E402
import glaze  # noqa: E402
import faces as fc  # noqa: E402
import deposit as dp  # noqa: E402
import shell  # noqa: E402

PX_MM = 32.23
RES = (960, 540)
TILE = (36.0, 22.0)

# tilt: deg from the surface normal (Yang 2012: 10-19 deg read off four cracks, some ~30); deposit: c0, L (mm),
# f (iron oxide share). 'gap' = the open air film only (fresh from the kiln).
VARIANTS = {
    "gap_v": {"tilt": 0, "dep": None},
    "gap_t15": {"tilt": 15, "dep": None},
    "dep_v": {"tilt": 0, "dep": {"c0": 1.0, "L": 0.4, "f": 0.3}},
    "dep_t15": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "f": 0.3}},
    "dep_t30": {"tilt": 30, "dep": {"c0": 1.0, "L": 0.4, "f": 0.3}},
    # chips at the mouth (faces.chips; Yang 2012): share of the length, median width, sigma, both-sides share
    "chip_gap": {"tilt": 15, "dep": None, "chip": {"share": 0.7, "w50_mm": 0.06, "w_sigma": 0.5, "both_share": 0.3}},
    # a channel widened by corrosion and filled with soil from the mouth down (faces.channels; Li 2022): grey fills
    # to calibrate the line's brightness against the fill's reflectance
    "ch_g20": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "grey": 0.2}, "chan": {"w0_mm": 0.063}},
    "ch_g50": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "grey": 0.5}, "chan": {"w0_mm": 0.063}},
    "chw_g50": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "grey": 0.5}, "chan": {"w0_mm": 0.063, "w_deep_mm": 0.2}},
    # the mouth emptied (top_mm), the fill seen through the glaze in a channel widening inside (Li 2022; Wu 2025)
    "deep_a": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "grey": 0.5}, "chan": {"w0_mm": 0.03, "w_deep_mm": 0.2, "top_mm": 0.08}},
    "deep_b": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "grey": 0.5}, "chan": {"w0_mm": 0.03, "w_deep_mm": 0.2, "top_mm": 0.15}},
    "deep_c": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.6, "grey": 0.5}, "chan": {"w0_mm": 0.063, "w_deep_mm": 0.3, "top_mm": 0.08}},
    "chip_dep": {"tilt": 15, "dep": {"c0": 1.0, "L": 0.4, "f": 0.3}, "chip": {"share": 0.7, "w50_mm": 0.06, "w_sigma": 0.5, "both_share": 0.3}},
}


def lines():
    """Twelve 6 mm cracks, centres on a 4 x 3 grid, orientations 0/45/90/135 deg by column, leaning sides alternate."""
    out = []
    for i, ang in enumerate((0, 45, 90, 135)):
        for j in range(3):
            cx, cy = -10.5 + 7.0 * i, -5.0 + 5.0 * j
            t = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
            half = 2.2 if ang in (0, 90) else 2.6
            out.append({"path": np.array([[cx, cy] - half * t, [cx, cy] + half * t]), "side": 1 if (i + j) % 2 == 0 else -1, "ang": ang})
    return out


def build(a):
    v = dict(VARIANTS[a.variant])
    if a.override:
        v.update(json.loads(a.override))
    mat = glaze.load_material()
    gv = mat["glaze_volume"]
    e0 = gv["thickness_mm"]["value"]
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    frame_w = RES[0] / PX_MM
    frame_h = frame_w * RES[1] / RES[0]
    hx, hy = TILE[0] / 2, TILE[1] / 2
    # body (flat at -e0) and the outer surface
    P = np.array([[-hx, -hy, -e0], [hx, -hy, -e0], [hx, hy, -e0], [-hx, hy, -e0]], float)
    card.write_ply(os.path.join(a.out, "body.ply"), P, np.tile([0, 0, 1.0], (4, 1)), [[0, 1, 2], [0, 2, 3]])
    # the glaze: a closed box (top at 0, bottom 0.05 mm under the body), as card.py; an open quad renders dark in
    # Cycles, which fills a medium only inside a watertight mesh (docs/slab.md), and rgbscene.py rejects it
    P, N, T, _ = shell.box(hx, hy, 0.0, -e0 - 0.05)
    card.write_ply(os.path.join(a.out, "outer.ply"), P, N, T)
    L = lines()
    dep = v["dep"]
    cov = dp.cover(dep["c0"], dep["L"]) if dep else None
    thick = lambda x, y: np.full(np.shape(x), e0)
    if v.get("chan"):
        F = fc.channels([l["path"] for l in L], thick, [v["tilt"]] * len(L), [l["side"] for l in L], cov, rng, **v["chan"])
    else:
        F = fc.faces([l["path"] for l in L], thick, [v["tilt"]] * len(L), [l["side"] for l in L], cov, rng)
    if v.get("chip"):
        C = fc.chips([l["path"] for l in L], None, [v["tilt"]] * len(L), [l["side"] for l in L], cov, rng, **v["chip"])
        F = fc.merge(F, C)
    files = {}
    for kind, (Pk, Nk, Tk) in F.items():
        if len(Tk):
            card.write_ply(os.path.join(a.out, f"{kind}.ply"), Pk, Nk, Tk)
            files[kind] = f"{kind}.ply"
    Lw = []
    w = Lw.append
    fov_y = math.degrees(2 * math.atan(frame_h / 2 / card.CAM_HEIGHT))
    w(f"# crack line test tile (materials/guan_glaze/linetest.py), variant {a.variant} {json.dumps(v)}, seed {a.seed}")
    w(f"LookAt 0 0 {card.CAM_HEIGHT} 0 0 0  0 1 0")
    w(f'Camera "perspective" "float fov" [ {fov_y:.6f} ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" true')
    w(f'Film "rgb" "integer xresolution" [ {RES[0]} ] "integer yresolution" [ {RES[1]} ] '
      f'"string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true'
      + (f' "float cropwindow" [ {" ".join(a.crop.split(","))} ]' if a.crop else ""))
    w("WorldBegin")
    for pos, size, scale in (((-160, 160, 320), 300, 1.0), ((200, -120, 350), 400, 0.35)):     # card.py's soft boxes
        c = np.asarray(pos, float)
        n = -c / np.linalg.norm(c)
        vh = np.cross(np.cross(n, [0, 0, 1.0]), n)
        vh /= np.linalg.norm(vh)
        uw = np.cross(vh, n)
        cs = [c - size / 2 * uw - size / 2 * vh, c + size / 2 * uw - size / 2 * vh, c - size / 2 * uw + size / 2 * vh, c + size / 2 * uw + size / 2 * vh]
        w("AttributeBegin")
        w(f'  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ {scale} ]')
        w('  Material "diffuse" "rgb reflectance" [ 0 0 0 ]')
        w('  Shape "bilinearmesh" "point3 P" [ ' + " ".join(f"{x:.4f}" for q in cs for x in q) + ' ] "integer indices" [ 0 1 2 3 ]')
        w("AttributeEnd")
    ss = gv["sigma_s_per_mm"]["value"]
    sa = list(gv["sigma_a_per_mm"]["lambda_nm_value"])
    var = gv["sigma_a_variant_met48503"]
    for i in range(0, len(sa), 2):
        t = min(1.0, max(0.0, (sa[i] - 500) / 100.0))
        sa[i + 1] *= (var["blue_scale"] ** (1 - t)) * (var["red_scale"] ** t)
    w(f'MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" {card.spectrum(card.held(sa))} '
      f'"spectrum sigma_s" [ 360 {ss} 830 {ss} ] "float g" [ {gv["g"]["value"]} ] "float scale" [ 1 ]')
    w("AttributeBegin")
    w('  Material "diffuse" "spectrum reflectance" [ 360 0.58 830 0.58 ]')
    w(f'  Shape "bilinearmesh" "point3 P" [ -200 -200 {-card.BODY_MM} 200 -200 {-card.BODY_MM} -200 200 {-card.BODY_MM} 200 200 {-card.BODY_MM} ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    w("AttributeBegin")
    w('  MediumInterface "glaze" ""')
    w(f'  Material "dielectric" "float eta" [ {gv["eta"]["value"]} ] "float roughness" [ {mat["surface"]["ggx_alpha"]["value"]} ] '
      f'"bool remaproughness" false "bool refractivenee" true')
    w('  Shape "plymesh" "string filename" [ "outer.ply" ]')
    w("AttributeEnd")
    w("AttributeBegin")
    w('  MediumInterface "" "glaze"')
    b = gv["body_reflectance"]["value"]
    w(f'  Material "diffuse" "spectrum reflectance" [ 360 {b} 830 {b} ]')
    w('  Shape "plymesh" "string filename" [ "body.ply" ]')
    w("AttributeEnd")
    if "gap" in files:
        w("AttributeBegin")
        w('  MediumInterface "glaze" "glaze"')
        w(f'  Material "thindielectric" "float eta" [ {1 / gv["eta"]["value"]:.5f} ]')
        w('  Shape "plymesh" "string filename" [ "gap.ply" ]')
        w("AttributeEnd")
    if "deposit" in files:
        w("AttributeBegin")
        w('  MediumInterface "glaze" "glaze"')
        if "grey" in dep:
            w(f'  Material "diffuse" "spectrum reflectance" [ 360 {dep["grey"]} 830 {dep["grey"]} ]')
        else:
            w(f'  Material "diffuse" "spectrum reflectance" {card.spectrum(card.held(dp.fill_spectrum(dep)))}')
        w('  Shape "plymesh" "string filename" [ "deposit.ply" ]')
        w("AttributeEnd")
    open(os.path.join(a.out, "scene.pbrt"), "w").write("\n".join(Lw) + "\n")
    json.dump({"variant": a.variant, "params": v, "seed": a.seed, "px_per_mm": PX_MM,
               "lines": [{"ang": l["ang"], "side": l["side"], "path": l["path"].tolist()} for l in L],
               "triangles": {k: int(len(F[k][2])) for k in F}}, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(a.out, {k: int(len(F[k][2])) for k in F})


def develop(a):
    """Raw camera RGB (EXR, pbrt orientation) -> white balance at 5500 K and the chain's matrix -> linear BT.709,
    no noise, no tone: the profile is a ratio, so the exposure does not matter."""
    import camera
    cam = json.load(open(os.path.join(ROOT, "out/materials/guan_glaze/p5/camera.json")))
    S = camera.Spectra("canon_eos_5d_mkiv")
    cal = camera.calibrate(S, camera.balance_spectrum(cam))
    for d in a.dirs:
        raws = [os.path.join(d, f) for f in sorted(os.listdir(d)) if (f.startswith("cyc") or f == "raw.exr") and f.endswith(".exr") and "." not in f[:-4]]
        for r in raws:
            raw = camera.read_raw(r)
            lin = np.maximum((raw * cal["gains"]) @ cal["C"].T, 0)
            if lin.shape[:2] != (RES[1], RES[0]):
                # a pbrt crop: placed in the frame by the scene's cropwindow (pbrt: pixel bounds ceil(res * crop)),
                # the rest filled with the crop's median; crop.npy marks where the image is
                cw = [float(x) for x in open(os.path.join(d, "scene.pbrt")).read().split('"float cropwindow" [')[1].split("]")[0].split()]
                x0, y0 = math.ceil(RES[0] * cw[0]), math.ceil(RES[1] * cw[2])
                full = np.empty((RES[1], RES[0], 3))
                full[:] = np.median(lin.reshape(-1, 3), 0)
                full[y0:y0 + lin.shape[0], x0:x0 + lin.shape[1]] = lin
                m = np.zeros((RES[1], RES[0]), bool)
                m[y0:y0 + lin.shape[0], x0:x0 + lin.shape[1]] = True
                np.save(os.path.join(d, "crop.npy"), m)
                lin = full
            np.save(r[:-4] + ".lin.npy", lin.astype(np.float32))
            print(r, "->", r[:-4] + ".lin.npy", "mean", lin.mean((0, 1)).round(5))


PHOTO_PSF_PX = 0.75     # [M] the photo's blur: sigma of its smallest specks, p5-p10 (dark 0.75-0.85, bright 0.69-0.80 px)


def measure(a):
    """Average of the two seeds (linear, developed), blurred by the photo's PSF, lines measured as on the photo
    (lines.py); a picture of it at the photo's glaze level beside a photo crop at the same scale."""
    import lines as ln
    from PIL import Image
    from scipy import ndimage as ndi
    M = json.load(open(os.path.join(ROOT, "out/materials/guan_glaze/measured_met48503.json")))
    glaze_lin = np.array(M["glaze_colour"]["median_linear_rgb"])
    rows = {}
    pics = []
    for d in a.dirs:
        L = [np.load(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".lin.npy")]
        lin = np.mean(L, 0).astype(np.float64)
        lin = np.stack([ndi.gaussian_filter(lin[..., c], PHOTO_PSF_PX) for c in range(3)], -1)
        region = np.zeros(lin.shape[:2], bool)
        region[25:-25, 25:-25] = True
        if os.path.exists(os.path.join(d, "crop.npy")):      # a pbrt crop: only inside it, 12 px in from its edges
            region &= ndi.binary_erosion(np.load(os.path.join(d, "crop.npy")), iterations=12)
        B = json.load(open(os.path.join(d, "build.json")))
        paths = [np.c_[RES[1] / 2 - np.asarray(l["path"])[:, 1] * PX_MM - 0.5, RES[0] / 2 - np.asarray(l["path"])[:, 0] * PX_MM - 0.5]
                 for l in B["lines"]]
        paths = [q for q in paths if region[np.clip(q[:, 0].round().astype(int), 0, RES[1] - 1),
                                            np.clip(q[:, 1].round().astype(int), 0, RES[0] - 1)].mean() > 0.7]
        res, G = ln.measure(lin, PX_MM, region, paths=paths)
        res["source"] = f"{d}: mean of {len(L)} seeds, blurred sigma {PHOTO_PSF_PX} px (the photo's PSF)"
        res["glaze_median_linear"] = [round(float(x), 5) for x in np.median(lin[region], 0)]
        json.dump(res, open(os.path.join(d, "lines.json"), "w"), indent=1)
        rows[os.path.basename(d)] = res
        k = glaze_lin / np.median(lin[region], 0)
        pics.append((os.path.basename(d), np.clip(lin * k, 0, 1)))
    # sheet: photo crop (same px/mm) then each variant, 640 x 300 crops
    im = np.asarray(Image.open(os.path.join(ROOT, M["photo"])).convert("RGB"))
    ph = im[1540 + 150:1540 + 150 + 300, 1640 + 300:1640 + 300 + 640]
    enc = lambda x: (255 * np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.maximum(x, 0.0031308) ** (1 / 2.4) - 0.055)).round().clip(0, 255).astype(np.uint8)
    tiles = [("photo Met 48503", ph)] + [(n, enc(p[120:420, 160:800])) for n, p in pics]
    from PIL import ImageDraw
    sheet = Image.new("RGB", (640, 320 * len(tiles)), (30, 30, 30))
    for i, (n, t) in enumerate(tiles):
        sheet.paste(Image.fromarray(t), (0, 320 * i + 20))
        ImageDraw.Draw(sheet).text((4, 320 * i + 4), n, fill=(230, 230, 230))
    sheet.save(a.sheet)
    keys = ["contrast_p10_p50_p90", "fwhm_um_p10_p50_p90_bright", "abs_asymmetry_p25_p50_p75_bright", "dark_core_fraction_of_bright",
            "colour_over_glaze_median_bright", "contrast_median_by_orientation_deg", "mean_profile_fwhm_um", "blocks"]
    for n, r in rows.items():
        print(n, "found:", json.dumps({k: r.get(k) for k in keys}))
        print(n, "known:", json.dumps({k: r["known_place"].get(k) for k in keys}))
    print(a.sheet)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--variant", required=True, choices=sorted(VARIANTS))
    b.add_argument("--override", help="JSON merged into the variant, e.g. '{\"tilt\": 20}'")
    b.add_argument("--out", required=True)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--spp", type=int, default=256)
    b.add_argument("--crop", help="pbrt cropwindow x0,x1,y0,y1 (NDC), e.g. the middle row of lines: 0.07,0.95,0.333,0.667")
    d = sub.add_parser("develop")
    d.add_argument("dirs", nargs="+")
    sub.add_parser("variants")
    m = sub.add_parser("measure")
    m.add_argument("dirs", nargs="+")
    m.add_argument("--sheet", required=True)
    a = ap.parse_args()
    if a.cmd == "build":
        build(a)
    elif a.cmd == "develop":
        develop(a)
    elif a.cmd == "measure":
        measure(a)
    else:
        print(json.dumps(VARIANTS, indent=1))


if __name__ == "__main__":
    main()
