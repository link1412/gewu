"""The material card of the Guan glaze: a flat tile of body plus glaze on a grey backdrop, lit by soft boxes,
shot like Met 48503 (docs/materials/guan_glaze.md). Writes a pbrt scene (the subset tools/rgbscene.py also reads),
optics.json and camera.json beside it.

    python3 -I materials/guan_glaze/card.py thickness               # the glaze thickness field (r2/thickness.npz)
    python3 -I materials/guan_glaze/card.py crackle                 # the crack network on it (r2/crackle.json)
    python3 -I materials/guan_glaze/card.py build --out out/materials/guan_glaze/p1 [--state excavated] [--res 960x540] [--spp 64] [--seed 1]
    python3 -I materials/guan_glaze/card.py develop out/materials/guan_glaze/p1      # raw EXR -> developed PNG
    python3 -I materials/guan_glaze/card.py compare out/materials/guan_glaze/p1      # sheet and numbers against the photo

World: mm, z up, the glaze's outer surface at z = 0, the camera above looking down, image x = world +x, image up = +y.
The frame is always 16:9 (the camera chain is 1920x1080 and takes 960x540 as a preview), at the photo's scale
at 1920 px (px/mm from measured_met48503.json).
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
sys.path.insert(0, os.path.join(ROOT, "crafts", "crackle"))
sys.path.insert(0, os.path.join(ROOT, "crafts", "deposition"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import glaze  # noqa: E402
import shell  # noqa: E402
import faces as fc  # noqa: E402
import deposit as dp  # noqa: E402

MEASURED = os.path.join(ROOT, "out/materials/guan_glaze/measured_met48503.json")
STATES = os.path.join(HERE, "states.json")
R2 = os.path.join(ROOT, "out/materials/guan_glaze/r2")
DOMAIN = (36.0, 24.0)          # mm, half sizes of the thickness field and the crack simulation (beyond the tile)
RAW_REF = 0.0361328            # the exposure, fixed (camera.py expose.raw_ref): round 1's p5 metered value, with which the
                               # backdrop (raw 0.104 in G) reads code 194 like the photo's; the same for every render of the card
TILT_DEG = (10.0, 20.0)        # [D] crack planes lean 10-19 deg from the normal: four cracks read off Yang et al. 2012 (OCT, figs. 1b-1d)
TILE = (46.0, 27.0)            # mm, the tile (body + glaze); the frame is 59.6 x 33.5 mm at the photo's scale
BODY_MM = 3.0                  # the sherd's thickness under the glaze, the backdrop lies this far below
CAM_HEIGHT = 300.0             # mm, pinhole (the plane is in focus: a flat tile)
F_NUMBER = 8.0                 # the optics.json value: diffraction only
FOCAL_MM, SENSOR_W = 100.0, 36.0


def spectrum(vals):
    return "[ " + " ".join(f"{x:g}" for x in vals) + " ]"


def held(vals):
    vals = list(vals)
    if vals[0] > 360:
        vals = [360, vals[1]] + vals
    if vals[-2] < 830:
        vals = vals + [830, vals[-1]]
    return vals


def scaled(shape, k):
    v = list(shape)
    return [x if i % 2 == 0 else min(0.95, x * k) for i, x in enumerate(v)]


def tilt(shape, rho, gamma):
    """A reflectance spectrum with the shape of `shape` (the measured stand-in) raised to gamma, scaled to rho at 550 nm:
    gamma 1 = the stand-in's own colour, 0 = grey. Used because the stand-ins are dark (carbon-like, raw sienna 0.03-0.3)
    and the stains of the sherd are not: their colour is the stand-in's hue at the brightness the photo shows."""
    lam, v = np.array(shape[0::2], float), np.array(shape[1::2], float)
    v550 = np.interp(550, lam, v)
    out = np.minimum(0.9, rho * (v / v550) ** gamma)
    return [x for pair in zip(lam, out) for x in pair]


def write_ply(path, P, N, tris, uv=None):
    P = np.asarray(P, np.float32)
    N = np.asarray(N, np.float32)
    cols = [P, N] + ([np.asarray(uv, np.float32)] if uv is not None else [])
    V = np.ascontiguousarray(np.concatenate(cols, 1))
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(P)}",
            "property float x", "property float y", "property float z",
            "property float nx", "property float ny", "property float nz"]
    if uv is not None:
        head += ["property float u", "property float v"]
    head += [f"element face {len(tris)}", "property list uchar int vertex_indices", "end_header"]
    T = np.asarray(tris, np.int32)
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = T
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.astype("<f4").tobytes())
        f.write(face.tobytes())


def write_pfm(path, a):
    """float32 (rows top to bottom) -> PFM (bottom to top)."""
    with open(path, "wb") as f:
        f.write(b"Pf\n%d %d\n-1\n" % (a.shape[1], a.shape[0]))
        f.write(np.flipud(a).astype("<f4").tobytes())


def to_exr(pfm, exr):
    subprocess.run([os.path.join(ROOT, "third_party/pbrt-build/imgtool"), "convert", "--outfile", exr, pfm], check=True)


def strip_mesh(paths_off, z):
    """paths_off: list of (centre (n,2), half width (n,)) -> vertices, normals(+z), triangles of the strips at height z."""
    PP, TT = [], []
    base = 0
    for c, hw in paths_off:
        t = np.gradient(c, axis=0)
        t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
        nrm = np.c_[-t[:, 1], t[:, 0]] * hw[:, None]
        a, b = c - nrm, c + nrm
        n = len(c)
        PP += [np.c_[a, np.full(n, z)], np.c_[b, np.full(n, z)]]
        i = np.arange(n - 1)
        # triangle winding with normal +z: (a_i, b_i, b_i+1) is counter-clockwise when b is to the left of the direction
        TT.append(np.c_[base + i, base + n + i, base + n + i + 1])
        TT.append(np.c_[base + i, base + n + i + 1, base + i + 1])
        base += 2 * n
    P = np.concatenate(PP)
    return P, np.tile([0.0, 0.0, 1.0], (len(P), 1)), np.concatenate(TT)


def thickness_cmd(a):
    """The glaze thickness field over the simulation domain (mm, 0.25 mm grid), from its own random stream: the
    crack simulation (crafts/crackle) and the card's body read the same field."""
    mat = glaze.load_material()
    step = 0.25
    xs = np.arange(-DOMAIN[0], DOMAIN[0] + 1e-9, step)
    ys = np.arange(-DOMAIN[1], DOMAIN[1] + 1e-9, step)
    e = glaze.thickness(mat, xs, ys, np.random.default_rng([a.seed, 7]))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    np.savez(a.out, x=xs, y=ys, e=e)
    print(a.out, "e min/mean/max", round(float(e.min()), 3), round(float(e.mean()), 3), round(float(e.max()), 3))


def crackle_cmd(a):
    """The crack network of the card: crafts/crackle/crackle.py on the thickness field, with the glaze's crackle
    drivers (material.json) and the toughness spread fitted to the photo's paths (material.json)."""
    mat = glaze.load_material()
    d = mat["crackle_drivers"]
    sets = {"x_range": [-DOMAIN[0], DOMAIN[0]], "y_range": [-DOMAIN[1], DOMAIN[1]],
            "glaze_mm": mat["glaze_volume"]["thickness_mm"]["value"], "e_ref_mm": mat["glaze_volume"]["thickness_mm"]["value"],
            "lag_per_thickness": d["lag_per_thickness"]["value"], "channel_stress": d["channel_stress_ratio"]["value"],
            "poisson": d["poisson"]["value"], "tough_spread": d["tough_spread"]["value"], "tough_corr_mm": d["tough_corr_mm"]["value"],
            "seed": a.seed}
    cmd = [sys.executable, "-I", os.path.join(ROOT, "crafts/crackle/crackle.py"), "--thickness", a.thickness, "--out", a.out,
           "--preview", a.out[:-5] + ".png", "--set"] + [f"{k}={json.dumps(v)}" for k, v in sets.items()]
    subprocess.run(cmd, check=True)


def load_state(name, overrides=None):
    """A set of process parameters (states.json): the crack channel (crack-wall corrosion), the crack deposit, the
    surface stain and the surface's roughness. Nothing else differs between fresh, heirloom and excavated."""
    S = json.load(open(STATES))
    st = json.loads(json.dumps(S["states"][name]))
    for k, v in (overrides or {}).items():
        sec, key = k.split(".", 1) if "." in k else (k, None)
        if key is None:
            st[sec] = v
        else:
            st.setdefault(sec, {})[key] = v
    return st


def thickness_field(path):
    T = np.load(path)
    tx, ty, te = np.asarray(T["x"], float), np.asarray(T["y"], float), np.asarray(T["e"], float)

    def ef(x, y):
        fx = np.interp(np.asarray(x, float), tx, np.arange(len(tx)))
        fy = np.interp(np.asarray(y, float), ty, np.arange(len(ty)))
        return ndi.map_coordinates(te, [fy, fx], order=1, mode="nearest")
    return ef


def build(a):
    mat = glaze.load_material()
    M = json.load(open(MEASURED))
    px_mm = M["scale"]["px_per_mm"]
    res = tuple(int(x) for x in a.res.split("x"))
    frame_w = 1920 / px_mm
    frame_h = frame_w * 9 / 16
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    gv = mat["glaze_volume"]
    e0 = gv["thickness_mm"]["value"]
    hx, hy = TILE[0] / 2, TILE[1] / 2
    log = {"px_per_mm_at_1920": round(px_mm, 3), "frame_mm": [round(frame_w, 2), round(frame_h, 2)], "tile_mm": TILE}

    # --- surface relief (speckle) --------------------------------------------------------------
    hmm = a.height_px_mm
    h, counts = glaze.height_map(mat, hx, hy, hmm, rng)
    if a.plain:
        h[:] = 0
    write_pfm(os.path.join(a.out, "h.pfm"), h)
    to_exr(os.path.join(a.out, "h.pfm"), os.path.join(a.out, "h.exr"))
    os.remove(os.path.join(a.out, "h.pfm"))
    log["pits"] = counts
    log["height_rms_um"] = round(float(h.std() * 1000), 2)

    # --- thickness (mottling) and the body mesh --------------------------------------------------
    step = 0.25
    xs = np.arange(-hx, hx + 1e-9, step)
    ys = np.arange(-hy, hy + 1e-9, step)
    ef = thickness_field(a.thickness)            # the field the crack simulation ran on
    X, Y = np.meshgrid(xs, ys)
    e = ef(X, Y)
    log["thickness"] = a.thickness
    log["thickness_mm_min_mean_max"] = [round(float(e.min()), 3), round(float(e.mean()), 3), round(float(e.max()), 3)]
    P = np.c_[X.ravel(), Y.ravel(), -e.ravel()]
    gy, gx = np.gradient(-e, step)
    N = np.c_[-gx.ravel(), -gy.ravel(), np.ones(e.size)]
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    nx_, ny_ = len(xs), len(ys)
    tris = []
    for j in range(ny_ - 1):
        i = np.arange(nx_ - 1)
        a0, b0, c0, d0 = j * nx_ + i, j * nx_ + i + 1, (j + 1) * nx_ + i, (j + 1) * nx_ + i + 1
        tris += [np.c_[a0, b0, d0], np.c_[a0, d0, c0]]
    write_ply(os.path.join(a.out, "body.ply"), P, N, np.concatenate(tris))
    # outer glaze surface: one quad with uv for the height map, closed into a box just below the body (Cycles fills
    # a medium only inside a watertight mesh, docs/slab.md; the box's other faces have a constant uv: no bump there,
    # and no ray reaches the bottom past the opaque body)
    P, N, T, UV = shell.box(hx, hy, 0.0, float(-e.max()) - 0.05)
    write_ply(os.path.join(a.out, "outer.ply"), P, N, T, uv=UV)

    # --- burial stains: patches under the surface, in two strengths ------------------------------
    sx = np.arange(-hx, hx, 0.1) + 0.05
    sy = np.arange(-hy, hy, 0.1) + 0.05
    lv = glaze.stain_levels(mat, sx, sy, rng, fraction=0.0 if a.plain else a.state_params["surface_stain_fraction"])
    stain_files = []
    zst = -mat["stains"]["burial_rust"]["depth_mm"]["value"]
    for level, k in ((1, a.stain_k_faint), (2, a.stain_k_strong)):
        jj, ii = np.nonzero(lv == level)
        if len(ii) == 0:
            continue
        x0, y0 = sx[ii] - 0.05, sy[jj] - 0.05
        PP = np.concatenate([np.c_[x0, y0], np.c_[x0 + 0.1, y0], np.c_[x0 + 0.1, y0 + 0.1], np.c_[x0, y0 + 0.1]])
        PP = np.c_[PP, np.full(len(PP), zst)]
        n = len(ii)
        k4 = np.arange(n)
        TT = np.concatenate([np.c_[k4, k4 + n, k4 + 2 * n], np.c_[k4, k4 + 2 * n, k4 + 3 * n]])
        fn = f"stain{level}.ply"
        write_ply(os.path.join(a.out, fn), PP, np.tile([0, 0, 1.0], (len(PP), 1)), TT)
        stain_files.append((fn, k))
    log["stain_area_fraction"] = round(float((lv > 0).mean()), 4)
    np.savez_compressed(os.path.join(a.out, "stain_mask.npz"), x=sx, y=sy, m=lv > 0)    # compare masks it out

    # --- the cracks (round 2): the network (crafts/crackle), each crack a plane through the glaze, leaning
    # TILT_DEG from the normal, its walls corroded into a channel and filled with deposit as the state says
    # (crafts/crackle/faces.channels, crafts/deposition) ------------------------------------------------------------
    st = a.state_params
    C = json.load(open(a.crackle))
    paths = [] if a.plain else [np.asarray(c["pts"], float) for c in C["cracks"]]
    crng = np.random.default_rng([a.seed, 11])
    tilts = crng.uniform(TILT_DEG[0], TILT_DEG[1], len(paths))
    sides = crng.choice([-1, 1], len(paths))
    ch, dep = st["channel"], st.get("deposit")
    cov = dp.cover(dep["c0"], dep["L_mm"]) if dep else None
    F = fc.channels(paths, ef, tilts, sides, cov, crng, w0_mm=ch["w0_mm"], w_deep_mm=ch.get("w_deep_mm"),
                    ramp_mm=ch.get("ramp_mm", 0.3), w_sigma=ch.get("w_sigma", 0.3), corr_mm=ch.get("corr_mm", 0.3),
                    fill_corr_mm=(dep or {}).get("fill_corr_mm", 0.1), top_mm=(dep or {}).get("top_mm", 0.0),
                    du=a.crack_du, clip=(-hx + 0.05, -hy + 0.05, hx - 0.05, hy - 0.05))
    crack_files = {}
    for kind, (Pk, Nk, Tk) in F.items():
        if len(Tk):
            write_ply(os.path.join(a.out, f"{kind}.ply"), Pk, Nk, Tk)
            crack_files[kind] = f"{kind}.ply"
    log["state"] = a.state
    log["state_params"] = st
    log["crack_triangles"] = {k: int(len(F[k][2])) for k in F}
    log["cracks"] = [{"gen": c["gen"], "pts": np.round(np.asarray(c["pts"]), 4).tolist()} for c in C["cracks"]] if not a.plain else []

    # --- the scene -----------------------------------------------------------------------------
    L = []
    w = L.append
    fov_y = math.degrees(2 * math.atan(frame_h / 2 / CAM_HEIGHT))
    w(f"# material card of the Guan glaze (materials/guan_glaze/card.py), seed {a.seed}")
    w(f"LookAt 0 0 {CAM_HEIGHT} 0 0 0  0 1 0")
    w(f'Camera "perspective" "float fov" [ {fov_y:.6f} ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" true')
    w(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
      f'"string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true')
    w("WorldBegin")
    # lights: a big soft box up and to one side (key) and a weaker one on the other (fill), both well off the
    # camera's mirror direction so the flat glaze shows no glare, only the pits' glints
    def softbox(centre, size, scale, K=5500):
        centre = np.asarray(centre, float)
        n = -centre / np.linalg.norm(centre)
        up = np.array([0, 0, 1.0])
        vh = np.cross(np.cross(n, up), n)
        vh /= np.linalg.norm(vh)
        uw = np.cross(vh, n)
        cs = [centre - size / 2 * uw - size / 2 * vh, centre + size / 2 * uw - size / 2 * vh,
              centre - size / 2 * uw + size / 2 * vh, centre + size / 2 * uw + size / 2 * vh]
        w("AttributeBegin")
        w(f'  AreaLightSource "diffuse" "blackbody L" [ {K} ] "float scale" [ {scale} ]')
        w('  Material "diffuse" "rgb reflectance" [ 0 0 0 ]')
        w('  Shape "bilinearmesh" "point3 P" [ ' + " ".join(f"{x:.4f}" for c in cs for x in c) + ' ] "integer indices" [ 0 1 2 3 ]')
        w("AttributeEnd")
    softbox(a.key_pos, a.key_size, 1.0)
    softbox(a.fill_pos, a.fill_size, a.fill_scale)
    ss = gv["sigma_s_per_mm"]["value"]
    sa = list(gv["sigma_a_per_mm"]["lambda_nm_value"])
    for i in range(0, len(sa), 2):       # a variant of the colour: red side x sigma_red, blue side x sigma_blue (smooth between)
        t = min(1.0, max(0.0, (sa[i] - 500) / 100.0))
        sa[i + 1] *= a.sigma_all * (a.sigma_blue ** (1 - t)) * (a.sigma_red ** t)
    w(f'MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" {spectrum(held(sa))} '
      f'"spectrum sigma_s" [ 360 {ss} 830 {ss} ] "float g" [ {gv["g"]["value"]} ] "float scale" [ 1 ]')
    w(f'Texture "h" "float" "imagemap" "string filename" "h.exr" "float scale" [ 1 ] "string wrap" "clamp"')
    # backdrop
    w("AttributeBegin")
    w('  Material "diffuse" "spectrum reflectance" [ 360 0.58 830 0.58 ]')
    w(f'  Shape "bilinearmesh" "point3 P" [ -200 -200 {-BODY_MM} 200 -200 {-BODY_MM} -200 200 {-BODY_MM} 200 200 {-BODY_MM} ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    alpha = a.state_params.get("surface_ggx_alpha") or mat["surface"]["ggx_alpha"]["value"]
    log["surface_ggx_alpha"] = alpha
    w("AttributeBegin")
    w('  MediumInterface "glaze" ""')
    w(f'  Material "dielectric" "float eta" [ {gv["eta"]["value"]} ] "float roughness" [ {alpha} ] "bool remaproughness" false '
      f'"bool refractivenee" true "texture displacement" "h"')
    w('  Shape "plymesh" "string filename" [ "outer.ply" ]')
    w("AttributeEnd")
    w("AttributeBegin")
    w('  MediumInterface "" "glaze"')
    b = gv["body_reflectance"]["value"]
    w(f'  Material "diffuse" "spectrum reflectance" [ 360 {b} 830 {b} ]')
    w('  Shape "plymesh" "string filename" [ "body.ply" ]')
    w("AttributeEnd")
    shape_rust = mat["stains"]["crack_ochre"]["reflectance_shape"]["lambda_nm_value"]
    for fn, k in stain_files:
        w("AttributeBegin")
        w('  MediumInterface "glaze" "glaze"')
        w(f'  Material "diffuse" "spectrum reflectance" {spectrum(held(tilt(shape_rust, k, a.rust_gamma)))}')
        w(f'  Shape "plymesh" "string filename" [ "{fn}" ]')
        w("AttributeEnd")
    if "gap" in crack_files:          # the open crack: an air film in the glaze
        w("AttributeBegin")
        w('  MediumInterface "glaze" "glaze"')
        w(f'  Material "thindielectric" "float eta" [ {1 / gv["eta"]["value"]:.5f} ]')
        w('  Shape "plymesh" "string filename" [ "gap.ply" ]')
        w("AttributeEnd")
    if "deposit" in crack_files:      # the fill of the channel (opaque, diffuse)
        w("AttributeBegin")
        w('  MediumInterface "glaze" "glaze"')
        w(f'  Material "diffuse" "spectrum reflectance" {spectrum(held(dp.fill_spectrum(dep)))}')
        w('  Shape "plymesh" "string filename" [ "deposit.ply" ]')
        w("AttributeEnd")
    open(os.path.join(a.out, "scene.pbrt"), "w").write("\n".join(L) + "\n")
    json.dump({"f_number": F_NUMBER, "magnification": round(SENSOR_W / frame_w, 5), "sensor_width_mm": SENSOR_W,
               "focal_mm": FOCAL_MM}, open(os.path.join(a.out, "optics.json"), "w"))
    cam = {"sensor": "canon_eos_5d_mkiv",
           "light": {"blackbody_K": 5500, "why": "the card's softboxes (card.py); weights the diffraction"},
           "white_balance": {"K": 5500, "why": "on the grey backdrop under that light, as a museum photographer sets it; the photo's backdrop is neutral (193,194,198)"},
           "iso": 100,
           "expose": {"percentile": 50, "of_saturation": a.exposure, "raw_ref": RAW_REF,
                      "why": "the photographer's exposure: fixed so that the grey backdrop reads like the photo's (code 194 in G). A choice of the card, not a measured number of the glaze"},
           "develop": {"ev": 0.0, "shoulder_from": 0.9, "contrast": 1.0, "pivot": 0.18, "why": "no grade: the card is compared in the photo's own tone"},
           "sharpen": {"amount": 0.0, "sigma_px": 0.7}, "seed": 1}
    json.dump(cam, open(os.path.join(a.out, "camera.json"), "w"), indent=1)
    json.dump(log, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(json.dumps(log))


PHOTO_CROP = (1640, 1540)       # top-left of the photo crop (px) used for the comparison: glaze below the dark band, no edges
CROP_MM = (33.0, 18.56)          # the compared region in both images


def develop(a):
    d = a.dir
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings", os.path.join(d, "camera.json"),
                    "--first", "0", "--out", os.path.join(d, "dev"), os.path.join(d, "raw.exr")], check=True)


def read8(path):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import camera
    return np.round(camera.read_png16(path) * 255).astype(np.uint8)


def crops(a):
    """(photo crop, card crop) as uint8 RGB, same pixel size (the card's px/mm = the photo's at 1920 px).
    --eff 2: the card was rendered at 960x540 (upsampled 2x by the chain); the photo is brought to the same
    effective resolution (down 2x, up 2x) so that the comparison is of the same detail."""
    M = json.load(open(MEASURED))
    px = M["scale"]["px_per_mm"]
    cw, ch = int(round(CROP_MM[0] * px)), int(round(CROP_MM[1] * px))
    ph = Image.open(os.path.join(ROOT, M["photo"])).convert("RGB")
    ph = ph.crop((PHOTO_CROP[0], PHOTO_CROP[1], PHOTO_CROP[0] + cw, PHOTO_CROP[1] + ch))
    if a.eff > 1:
        ph = ph.resize((cw // a.eff, ch // a.eff), Image.LANCZOS).resize((cw, ch), Image.BICUBIC)
    card = read8(os.path.join(a.dir, "dev", "f0000.png"))
    cx, cy = card.shape[1] // 2, card.shape[0] // 2
    card = card[cy - ch // 2:cy - ch // 2 + ch, cx - cw // 2:cx - cw // 2 + cw]
    return np.asarray(ph), card, px


def card_crop_from(img, px):
    ch = int(round(CROP_MM[1] * px)); cw = int(round(CROP_MM[0] * px))
    cx, cy = img.shape[1] // 2, img.shape[0] // 2
    return img[cy - ch // 2:cy - ch // 2 + ch, cx - cw // 2:cx - cw // 2 + cw]


def compare(a):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import detail
    ph, card, px = crops(a)
    out = os.path.join(a.dir, "cmp")
    os.makedirs(out, exist_ok=True)
    h, w = ph.shape[:2]
    # sheet: photo over card, full crops
    sheet = Image.new("RGB", (w, 2 * h + 4), (40, 40, 40))
    sheet.paste(Image.fromarray(ph), (0, 0))
    sheet.paste(Image.fromarray(card), (0, h + 4))
    sp = os.path.join(a.dir, "cmp", "sheet.png")
    sheet.save(sp)
    # a side-by-side at 1:1 of the centre, 640x480 each
    cx, cy = w // 2, h // 2
    sb = Image.new("RGB", (1284, 480), (40, 40, 40))
    sb.paste(Image.fromarray(ph[cy - 240:cy + 240, cx - 320:cx + 320]), (0, 0))
    sb.paste(Image.fromarray(card[cy - 240:cy + 240, cx - 320:cx + 320]), (644, 0))
    sb.save(os.path.join(out, "side_by_side_1to1.png"))
    # numbers
    res = {}
    noise = None
    if a.b:
        # two seeds: the render's noise is measured as (A-B)/sqrt2 per band and taken off the average's band energy
        # (the average carries half of it). Same sensor-noise seed in both, so the difference is the render's.
        cardB = card_crop_from(read8(os.path.join(a.b, "dev", "f0000.png")), px)
        fa, fb = card.astype(np.float32), cardB.astype(np.float32)
        card = np.round((fa + fb) / 2).astype(np.uint8)
        noise = (card_crop_from(read8(os.path.join(a.dir, "dev", "f0000.png")), px), cardB)
    # the card's burial stain (if any) is masked out of the numbers, as the photo's crop has none
    stain = np.zeros(card.shape[:2], bool)
    sm = os.path.join(a.dir, "stain_mask.npz")
    if os.path.exists(sm):
        Z = np.load(sm)
        hh, ww = card.shape[:2]
        rr, cc_ = np.mgrid[0:hh, 0:ww]
        # crop pixel -> world mm (the developed frame is 1920 x 1080 at px; pbrt's image is mirrored in x)
        xw = -((cc_ + 960 - ww // 2) + 0.5 - 960) / px
        yw = -((rr + 540 - hh // 2) + 0.5 - 540) / px
        fx = np.interp(xw, Z["x"], np.arange(len(Z["x"])))
        fy = np.interp(yw, Z["y"], np.arange(len(Z["y"])))
        stain = ndi.map_coordinates(Z["m"].astype(float), [fy, fx], order=0) > 0.5
        stain = ndi.binary_dilation(stain, iterations=int(0.3 * px))
        res["card_stain_masked_fraction"] = round(float(stain.mean()), 4)
    for name, im in (("photo", ph), ("card", card)):
        small = np.asarray(Image.fromarray(im).resize((detail.W, detail.H), Image.LANCZOS))
        m = np.ones((detail.H, detail.W), bool)
        m[:, :int(0.03 * detail.W)] = m[:, -int(0.03 * detail.W):] = False
        if name == "card" and stain.any():
            m &= ~(np.asarray(Image.fromarray(stain.astype(np.uint8) * 255).resize((detail.W, detail.H), Image.NEAREST)) > 127)
        bands, pct = detail.profile(small, m)
        lin = detail_lin(im)
        if name == "card" and noise is not None:
            Lg = lambda img: detail_lin(np.asarray(Image.fromarray(img).resize((detail.W, detail.H), Image.LANCZOS))) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            LA, LB = Lg(noise[0]) ** (1 / 2.2), Lg(noise[1]) ** (1 / 2.2)
            Ln, Lc = (LA - LB) / np.sqrt(2), (LA + LB) / 2
            nb = [float(np.sqrt(np.mean((ndi.gaussian_filter(Ln, lo) - ndi.gaussian_filter(Ln, hi))[m] ** 2)) / Lc[m].mean())
                  for (lo, hi) in detail.BANDS]
            res["noise_one_image_pct"] = [round(100 * v, 2) for v in nb]
            res["noise_note"] = "render noise of ONE image per band; the average has half its variance and it is taken off"
            bands = [float(np.sqrt(max(b ** 2 - 0.5 * n ** 2, 0.0))) for b, n in zip(bands, nb)]
        keep = ~stain if name == "card" else np.ones(im.shape[:2], bool)
        res[name] = {"detail_pct": [round(100 * float(b), 2) for b in bands], "luma8_p5_p50_p95": [round(float(x)) for x in pct],
                     "median_srgb8": [int(x) for x in np.median(im[keep], 0)],
                     "mean_linear": [round(float(x), 4) for x in lin[keep].mean(0)],
                     "median_linear": [round(float(x), 4) for x in np.median(lin[keep], 0)]}
        # large-scale (mottling): relative std of luma after a 3 mm Gaussian (stain pixels set to the median first)
        Y = lin @ np.array([0.2126, 0.7152, 0.0722])
        Y = np.where(keep, Y, np.median(Y[keep]))
        res[name]["mottle_3mm_pct"] = round(100 * float(ndi.gaussian_filter(Y, 3 * px).std() / Y.mean()), 2)
    full = read8(os.path.join(a.dir, "dev", "f0000.png"))
    bk = detail_lin(full[300:780, 5:150]).reshape(-1, 3).mean(0)
    res["backdrop_card_linear"] = [round(float(x), 4) for x in bk]
    res["backdrop_card_srgb8"] = [int(x) for x in full[300:780, 5:150].reshape(-1, 3).mean(0)]
    res["glaze_over_backdrop_linear"] = {"card": [round(float(m / b), 4) for m, b in zip(res["card"]["median_linear"], bk)],
                                         "photo": json.load(open(MEASURED))["glaze_colour"]["ratio_to_backdrop_linear"]}
    json.dump(res, open(os.path.join(out, "numbers.json"), "w"), indent=1)
    print(sp)
    print(json.dumps(res, indent=1))


def lines_cmd(a):
    """The crack lines of a render measured as on the photo: cross profiles (materials/guan_glaze/lines.py) at the
    cracks' known places and where they are found, and the network's statistics (crafts/crackle/network.py), in the
    comparison crop. The render is read raw (no sensor noise), white balanced and brought to linear BT.709 as the
    chain does, the seeds averaged, and blurred by the photo's PSF at this scale (0.75 px at 32.23 px/mm)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import camera
    import lines as ln
    import network as nw
    cam = json.load(open(os.path.join(a.dirs[0], "camera.json")))
    cal = camera.calibrate(camera.Spectra(cam["sensor"]), camera.balance_spectrum(cam))
    lin = np.mean([np.maximum((camera.read_raw(os.path.join(d, "raw.exr")) * cal["gains"]) @ cal["C"].T, 0) for d in a.dirs], 0)
    H, W = lin.shape[:2]
    M = json.load(open(MEASURED))
    px = M["scale"]["px_per_mm"] * W / 1920
    lin = np.stack([ndi.gaussian_filter(lin[..., c], 0.75 * px / M["scale"]["px_per_mm"]) for c in range(3)], -1)
    B = json.load(open(os.path.join(a.dirs[0], "build.json")))
    region = np.zeros((H, W), bool)
    cw, chh = int(round(CROP_MM[0] * px)), int(round(CROP_MM[1] * px))
    region[H // 2 - chh // 2:H // 2 - chh // 2 + chh, W // 2 - cw // 2:W // 2 - cw // 2 + cw] = True
    sm = os.path.join(a.dirs[0], "stain_mask.npz")
    if os.path.exists(sm):                       # the burial stain is masked, as in compare
        Z = np.load(sm)
        rr, cc_ = np.mgrid[0:H, 0:W]
        fx = np.interp(-(cc_ + 0.5 - W / 2) / px, Z["x"], np.arange(len(Z["x"])))
        fy = np.interp(-(rr + 0.5 - H / 2) / px, Z["y"], np.arange(len(Z["y"])))
        st = ndi.binary_dilation(ndi.map_coordinates(Z["m"].astype(float), [fy, fx], order=0) > 0.5, iterations=max(1, int(0.3 * px)))
        region &= ~st
    # world (x, y) mm -> image (row, col): pbrt's image is mirrored in x (measured on the line test tile)
    paths = [np.c_[H / 2 - np.asarray(c["pts"])[:, 1] * px - 0.5, W / 2 - np.asarray(c["pts"])[:, 0] * px - 0.5] for c in B["cracks"]]
    paths = [q for q in paths if region[np.clip(q[:, 0].astype(int), 0, H - 1), np.clip(q[:, 1].astype(int), 0, W - 1)].mean() > 0.5]
    res, G = ln.measure(lin, px, region, paths=paths)
    res["source"] = f"{a.dirs}: raw, mean of {len(a.dirs)} renders, blurred as the photo"
    res["network"] = nw.stats(G, region)
    out = os.path.join(a.dirs[0], "cmp")
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "lines.json"), "w"), indent=1)
    enc = lambda x: (255 * np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.maximum(x, 0.0031308) ** (1 / 2.4) - 0.055)).round().clip(0, 255).astype(np.uint8)
    k = np.array(M["glaze_colour"]["median_linear_rgb"]) / np.median(lin[region], 0)
    nw.overlay(enc(np.clip(lin * k, 0, 1)), G, os.path.join(out, "lines_overlay.png"))
    keys = ["contrast_p10_p50_p90", "fwhm_um_p10_p50_p90_bright", "abs_asymmetry_p25_p50_p75_bright", "dark_core_fraction_of_bright",
            "colour_over_glaze_median_bright", "contrast_median_by_orientation_deg", "mean_profile_fwhm_um", "blocks"]
    print("found:", json.dumps({k_: res.get(k_) for k_ in keys}))
    print("known:", json.dumps({k_: res["known_place"].get(k_) for k_ in keys}))
    print("network:", json.dumps({k_: v for k_, v in res["network"].items() if k_ not in ("source",)}))


def sheet_cmd(a):
    """Renders of the same tile (e.g. the three states) side by side, developed together with one exposure (the
    camera chain's, fixed over all of them), each the full frame at the preview's own size, labelled."""
    from PIL import ImageDraw
    dev = os.path.join(os.path.dirname(os.path.abspath(a.out)), "dev_" + os.path.splitext(os.path.basename(a.out))[0])
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings",
                    os.path.join(a.dirs[0], "camera.json"), "--first", "0", "--out", dev]
                   + [os.path.join(d, "raw.exr") for d in a.dirs], check=True)
    labels = a.labels.split(",") if a.labels else [os.path.basename(d.rstrip("/")) for d in a.dirs]
    tiles = []
    for i, d in enumerate(a.dirs):
        im = Image.fromarray(read8(os.path.join(dev, f"f{i:04d}.png")))
        if a.crop:                                  # a centred crop at 1:1 of the developed frame
            cw, ch_ = (int(x) for x in a.crop.split("x"))
            im = im.crop(((im.width - cw) // 2, (im.height - ch_) // 2, (im.width + cw) // 2, (im.height + ch_) // 2))
        elif a.down > 1:
            im = im.resize((im.width // a.down, im.height // a.down), Image.LANCZOS)
        tiles.append(im)
    w, h = tiles[0].size
    out = Image.new("RGB", (w, (h + 24) * len(tiles)), (30, 30, 30))
    for i, (t, lab) in enumerate(zip(tiles, labels)):
        out.paste(t, (0, i * (h + 24) + 24))
        ImageDraw.Draw(out).text((6, i * (h + 24) + 6), lab, fill=(235, 235, 235))
    out.save(a.out)
    print(a.out)


def detail_lin(im):
    x = im.astype(np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nm in ("develop", "compare"):
        q = sub.add_parser(nm)
        q.add_argument("dir")
        q.add_argument("--b", help="compare: a second render of the same scene (other seed) for the noise correction")
        q.add_argument("--eff", type=int, default=1, help="compare: the card was rendered 1/eff of the 1920 width")
    ln_ = sub.add_parser("lines")
    ln_.add_argument("dirs", nargs="+", help="renders of one scene (seeds), raw.exr in each")
    sh = sub.add_parser("sheet")
    sh.add_argument("dirs", nargs="+")
    sh.add_argument("--out", required=True)
    sh.add_argument("--labels", help="comma separated, one per dir")
    sh.add_argument("--down", type=int, default=2, help="shrink the developed 1920 frames by this")
    sh.add_argument("--crop", help="instead: a centred crop WxH at 1:1 of the developed frame, e.g. 960x540")
    t = sub.add_parser("thickness")
    t.add_argument("--out", default=os.path.join(R2, "thickness.npz"))
    t.add_argument("--seed", type=int, default=6)
    k = sub.add_parser("crackle")
    k.add_argument("--thickness", default=os.path.join(R2, "thickness.npz"))
    k.add_argument("--out", default=os.path.join(R2, "crackle.json"))
    k.add_argument("--seed", type=int, default=6)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--res", default="960x540")
    b.add_argument("--spp", type=int, default=64)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--plain", action="store_true", help="no cracks, stains or relief: the glaze alone (colour sweeps)")
    b.add_argument("--sigma-red", type=float, default=2.2)
    b.add_argument("--sigma-blue", type=float, default=0.45)
    b.add_argument("--sigma-all", type=float, default=1.0)
    b.add_argument("--crackle", default=os.path.join(R2, "crackle.json"))
    b.add_argument("--thickness", default=os.path.join(R2, "thickness.npz"))
    b.add_argument("--state", default="excavated", help="a set of process parameters in states.json")
    b.add_argument("--set", nargs="*", default=[], help="state overrides, section.key=json, e.g. deposit.f=0.05")
    b.add_argument("--crack-du", type=float, default=0.04, help="mm along a crack per column of the channel mesh")
    b.add_argument("--height-px-mm", type=float, default=48.0)
    b.add_argument("--rust-gamma", type=float, default=0.35)
    b.add_argument("--stain-k-faint", type=float, default=0.14)
    b.add_argument("--stain-k-strong", type=float, default=0.18)
    b.add_argument("--exposure", type=float, default=0.185)
    b.add_argument("--key-pos", type=float, nargs=3, default=[-160, 160, 320])
    b.add_argument("--key-size", type=float, default=300)
    b.add_argument("--fill-pos", type=float, nargs=3, default=[200, -120, 350])
    b.add_argument("--fill-size", type=float, default=400)
    b.add_argument("--fill-scale", type=float, default=0.35)
    args = ap.parse_args()
    if args.cmd == "build":
        args.state_params = load_state(args.state, {kv.split("=", 1)[0]: json.loads(kv.split("=", 1)[1]) for kv in args.set})
    {"build": build, "develop": develop, "compare": compare, "thickness": thickness_cmd, "crackle": crackle_cmd,
     "lines": lines_cmd, "sheet": sheet_cmd}[args.cmd](args)


if __name__ == "__main__":
    main()
