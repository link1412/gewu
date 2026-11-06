"""The material card of gilt copper (mercury-gilded copper): a knee-like gilt bulb on grey paper, lit by a rig
placed by the crop's reflection map and fitted per light group, shot at the scale of the reference photo (Cleveland
1970.149.1, measured by measure_ref.py). docs/materials/gilt_copper.md; parameters in material.json.

    python3 -I materials/gilt_copper/card.py build --out out/materials/gilt_copper/g1 [--res 960x540] [--spp 256]
                                                 [--tilt 0] [--alpha A] [--seed 1] [--scales ...]
    python3 -I materials/gilt_copper/card.py render out/materials/gilt_copper/g1 [--pbrt]   # queue, wait, pull
    python3 -I materials/gilt_copper/card.py fitlight out/materials/gilt_copper/g1          # fit the lights' scales
    python3 -I materials/gilt_copper/card.py develop out/materials/gilt_copper/g1 [--raw pbrt.exr]
    python3 -I materials/gilt_copper/card.py compare out/materials/gilt_copper/g1           # sheet and numbers
    python3 -I materials/gilt_copper/card.py turns SHEET.png DIR...                         # the turn frames

World: mm, z up, the paper at z = 0, the camera in front (-y) looking slightly down. The frame is 16:9 at the
photo's scale at 1920 px wide. What is the material's (material.json) and what is the card's own choice (the
light, the piece, the camera: the optics and object layers) is kept apart.

Surface structure, all from material.json:
- the gold: pbrt's conductor with eta, k (an opaque layer: 2-10 um, far thicker than gold's ~20 nm skin depth);
- roughness alpha (GGX), and a bump map: burnishing/handling marks (short grooves) and a weak undulation;
- the processes (material.json "processes"; zero on a new piece): abrasion (the gold worn through on the high
  parts, per triangle: copper.ply), oxidation (a cuprite film on that copper, thin-film reflectance).
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
MEASURED = os.path.join(ROOT, "out/materials/gilt_copper/measured_cma1970.149.1.json")
CAM_DIST = 400.0                       # mm, camera to target
CAM_ELEV_DEG = 12.0                    # [A] the photo looks down a little at the statue (the base's ellipse)
TARGET = (0.0, 0.0, 3.0)
# The piece: a knee-like bulb, a sphere cap stretched along x. Its cross-section (y-z) is curved as the reference
# knee's front: there the compared crop (5.9 mm high) runs from the highlight band near the top to the front, so the
# radius is ~6 mm (projected height of a cylinder of radius r from 20 to 85 degrees from the top, seen 12 degrees
# down: ~0.97 r) [D, rough]. A flatter piece shows the crop a far narrower cone of the room (the first cards: a dome
# of radius 14 mm saw only +-35 degrees about the zenith, and its whole top went white).
DOME_R, DOME_H = 6.5, 6.2              # cross-section radius, height (mm) [D] (above)
DOME_SX = 1.6                          # stretch along x: 21 mm long, a knee lying along x [A]
CROP_POLAR_DEG = 50.0                  # the compared crop is centred on the piece this far from its top, on the front,
CROP_X_MM = 4.0                        # and this far to the right: the photo's crop ends where the knee rounds off [D]
F_NUMBER, FOCAL_MM, SENSOR_W = 11.0, 100.0, 36.0
# the lights: elevation, azimuth (0 = toward the camera, + = its right), distance (mm), width, height (mm). Placed by
# the crop's reflection map (refmap.py, on this piece and crop): the photo's band (crop rows 15-55) sees elevation
# ~50-75 behind; rows 50-100 the zenith; rows 120-220 the front-right from elevation ~50 down to ~15; the upright
# highlight (rows 70-115, columns 130-200) elevation ~45, azimuth ~110 [D]
SWEEP_AZ, SWEEP_DIST, SWEEP_W, SWEEP_STEP = 25.0, 900.0, 2000.0, 10.0
RIG = {"key": [66.0, 180.0, 700.0, 400.0, 120.0],
       # the front: a sweep of abutting strips, 10 degrees each from elevation 5 to 85 (one light group each: the
       # fit gives the room's radiance by elevation, a graded light without seams)
       **{f"s{e:02d}": [float(e), SWEEP_AZ, SWEEP_DIST, SWEEP_W, 2 * SWEEP_DIST * math.tan(math.radians(SWEEP_STEP / 2))]
          for e in range(10, 90, 10)},
       "side": [45.0, 110.0, 900.0, 200.0, 500.0]}
GROUPS = tuple(RIG)
# the rig's radiance scales [F]: card.py fitlight on out/materials/gilt_copper/k2 (alpha 0.02, undulation slope 0.02),
# fitted to the photo crop's clipped fraction, luma p5/p50/p95 and 11 x 4 cells of mean luma
RIG_SCALES = [27.81, 0.2409, 0.2733, 0.3244, 0.3783, 0.4632, 0.568, 0.3602, 0.8854, 0.8618]


def load_material():
    return json.load(open(os.path.join(HERE, "material.json")))


def val(m, *path):
    x = m
    for p in path:
        x = x[p]
    return x["value"]


# --- geometry ---------------------------------------------------------------------------------------
def write_ply(path, P, N, F, uv=None):
    P, N, F = np.asarray(P, "<f4"), np.asarray(N, "<f4"), np.asarray(F, "<i4")
    props = "property float x\nproperty float y\nproperty float z\nproperty float nx\nproperty float ny\nproperty float nz\n"
    cols = [P, N]
    if uv is not None:
        props += "property float u\nproperty float v\n"
        cols.append(np.asarray(uv, "<f4"))
    V = np.concatenate(cols, 1).astype("<f4")
    with open(path, "wb") as f:
        f.write((f"ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\n{props}"
                 f"element face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n").encode())
        f.write(V.tobytes())
        rec = np.zeros(len(F), dtype=[("n", "u1"), ("i", "<i4", (3,))])
        rec["n"], rec["i"] = 3, F
        f.write(rec.tobytes())


def sphere_point(theta, phi, r=DOME_R):
    """theta from the top; the sphere's centre at z = DOME_H - DOME_R"""
    s = np.sin(theta)
    n = np.stack([s * np.cos(phi), s * np.sin(phi), np.cos(theta)], -1)
    return n * r + np.array([0, 0, DOME_H - DOME_R]), n


def dome_mesh(rings=360, segs=720):
    """the cap, stretched by DOME_SX along x (normals by the inverse transpose). Returns the footprint's half-width
    across (y) as `base`; the planar UV spans the square of half-side base * DOME_SX (the long axis)"""
    t_max = math.acos((DOME_R - DOME_H) / DOME_R)
    th = np.linspace(0, t_max, rings + 1)[1:]
    ph = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    T, Ph = np.meshgrid(th, ph, indexing="ij")
    P, N = sphere_point(T.ravel(), Ph.ravel())
    p0, n0 = sphere_point(np.array([0.0]), np.array([0.0]))
    P, N = np.concatenate([p0, P]), np.concatenate([n0, N])
    P[:, 0] *= DOME_SX
    N[:, 0] /= DOME_SX
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    F = [(0, 1 + j, 1 + (j + 1) % segs) for j in range(segs)]
    for i in range(rings - 1):
        a = 1 + i * segs + np.arange(segs)
        b = 1 + i * segs + (np.arange(segs) + 1) % segs
        c, d = a + segs, b + segs
        F += list(zip(a, c, d)) + list(zip(a, d, b))
    base = math.sqrt(DOME_R ** 2 - (DOME_R - DOME_H) ** 2)
    bu = base * DOME_SX
    uv = np.stack([P[:, 0] / (2 * bu) + 0.5, P[:, 1] / (2 * bu) + 0.5], 1)    # planar, over the footprint
    return P, N, np.array(F), uv, base


def abrasion(P, F, base, mat, rng, px=1024):
    """the process 'abrasion' (material.json): per triangle, wear depth = D_top e^p (e = the centroid's height over
    the dome's) against the local gold thickness, a lognormal field (mean, CV, correlation length) on the footprint.
    Returns a bool per triangle: the copper shows."""
    ab = mat["processes"]["abrasion"]
    D = ab["wear_depth_at_top_um"]["value"]
    if D <= 0:
        return np.zeros(len(F), bool)
    t_mean = mat["gold"]["layer_thickness_um"]["value"]
    cv, corr = ab["gold_thickness_cv"]["value"], ab["gold_thickness_corr_mm"]["value"]
    from scipy.ndimage import gaussian_filter
    base = base * DOME_SX                               # the UV square's half-side
    g = gaussian_filter(rng.normal(size=(px, px)), corr / (2 * base / px))
    g /= g.std()
    sig = math.sqrt(math.log(1 + cv * cv))
    c = P[F].mean(1)
    i = np.clip(((c[:, 1] / (2 * base) + 0.5) * px).astype(int), 0, px - 1)
    j = np.clip(((c[:, 0] / (2 * base) + 0.5) * px).astype(int), 0, px - 1)
    t = t_mean * np.exp(sig * g[i, j] - sig * sig / 2)
    e = np.clip(c[:, 2] / DOME_H, 0, 1)
    return D * e ** ab["exposure_power"]["value"] > t


def abrasion_override(P, F, base, mat, rng, D):
    m = json.loads(json.dumps(mat))
    m["processes"]["abrasion"]["wear_depth_at_top_um"]["value"] = D
    return abrasion(P, F, base, m, rng)


def cuprite_on_copper(mat, d_nm):
    """the process 'oxidation': normal-incidence reflectance of a Cu2O film (d_nm) on copper, by the thin-film
    (Airy) formula with complex indices, on 360-830 nm every 5 nm; returned as pbrt's interleaved spectrum. pbrt's
    conductor takes it as a reflectance (eta 1, k from r): right at normal incidence, approximate off it [D]."""
    from camera import pbrt_array
    ox = mat["processes"]["oxidation"]
    T = np.loadtxt(os.path.join(ROOT, ox["cu2o_n_k"]["value"]), delimiter=",", skiprows=1)
    lam = np.arange(360.0, 831.0, 5.0)
    n1 = np.interp(lam, T[:, 0], T[:, 1]) + 1j * np.interp(lam, T[:, 0], T[:, 2])
    e, k = pbrt_array("Cu_eta"), pbrt_array("Cu_k")
    n2 = np.interp(lam, e[0::2], e[1::2]) + 1j * np.interp(lam, k[0::2], k[1::2])
    r01, r12 = (1 - n1) / (1 + n1), (n1 - n2) / (n1 + n2)
    ph = np.exp(2j * 2 * math.pi * n1 * d_nm / lam)
    R = np.abs((r01 + r12 * ph) / (1 + r01 * r12 * ph)) ** 2
    return np.stack([lam, R], 1).ravel()


# --- the bump map: scratches -----------------------------------------------------------------------
def scratches(path, mat, size_mm, rng, px=3072, depth_um=None, slope_override=None, corr_override=None, density=None):
    """height (mm) on the piece's planar UV: straight scratches of Gaussian cross-section (random position, direction,
    length, depth 0.3-1 x the given), and the finish's undulation; written as a PFM (float). The scratches are drawn
    one pixel wide (a deeper one wins where two cross) and blurred to their width"""
    from PIL import ImageDraw
    from scipy.ndimage import gaussian_filter
    s = mat["surface"]["scratches"]
    dens, w_um, d_um = s["per_mm2"]["value"], s["width_um"]["value"], s["depth_um"]["value"]
    if depth_um is not None:
        d_um = depth_um
    if density is not None:
        dens = density
    L0, L1 = s["length_mm"]["value"]
    mm_px = size_mm / px
    n = rng.poisson(dens * size_mm ** 2)
    sig = w_um * 1e-3 / 2.355 / mm_px                     # FWHM -> sigma, in px
    c = rng.uniform(0, px, (n, 2))
    a = rng.uniform(0, math.pi, n)
    L = rng.uniform(L0, L1, n) / mm_px
    dep = rng.uniform(0.3, 1.0, n)
    order = np.argsort(dep)                                # shallow first: a deeper one drawn over it
    canvas = Image.new("F", (px, px), 0.0)
    dr = ImageDraw.Draw(canvas)
    for i in order:
        dx, dy = math.cos(a[i]) * L[i] / 2, math.sin(a[i]) * L[i] / 2
        dr.line([(c[i, 0] - dx, c[i, 1] - dy), (c[i, 0] + dx, c[i, 1] + dy)], fill=float(dep[i]), width=1)
    h = -np.asarray(canvas, np.float32) * (d_um * 1e-3)
    if sig > 0.3:
        h = gaussian_filter(h, sig, mode="wrap") * (math.sqrt(2 * math.pi) * sig)   # a 1 px line's peak back to its depth
    h = h.astype(np.float32)
    # the finish's undulation: a Gaussian random field (correlation length, rms slope), the mottle of the reflection
    un = mat["surface"]["undulation"]
    slope = un["rms_slope"]["value"] if slope_override is None else slope_override
    if slope > 0:
        from scipy.ndimage import gaussian_filter
        corr = un["corr_mm"]["value"] if corr_override is None else corr_override
        g = gaussian_filter(rng.normal(size=(px, px)), corr / mm_px / math.sqrt(2), mode="wrap")
        gy, gx = np.gradient(g, mm_px)
        g *= slope / math.sqrt(np.mean(gx ** 2 + gy ** 2))           # rms of |grad h| = the slope
        h += g.astype(np.float32)
    with open(path, "wb") as f:                          # PFM, bottom row first: row 0 of h is v = 0
        f.write(f"Pf\n{px} {px}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(h).astype("<f4").tobytes())
    return int(n)


# --- the scene -------------------------------------------------------------------------------------
def spectrum(pairs):
    return "[ " + " ".join(f"{x:g}" for x in pairs) + " ]"


def build(a):
    mat = load_material()
    M = json.load(open(MEASURED))
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    res = [int(v) for v in a.res.split("x")]
    px_mm = M["scale"]["px_per_mm"]
    frame_w = 1920 / px_mm
    frame_h = frame_w * res[1] / res[0]
    fov = 2 * math.degrees(math.atan(frame_h / 2 / CAM_DIST))
    el = math.radians(CAM_ELEV_DEG)
    eye = np.array(TARGET) + CAM_DIST * np.array([0, -math.cos(el), math.sin(el)])
    P, N, F, uv, base = dome_mesh()
    exposed = abrasion(P, F, base, mat, rng) if a.wear is None else abrasion_override(P, F, base, mat, rng, a.wear)
    write_ply(os.path.join(a.out, "dome.ply"), P, N, F[~exposed], uv)
    write_ply(os.path.join(a.out, "copper.ply"), P, N, F[exposed] if exposed.any() else F[:1], uv)
    n_scr = scratches(os.path.join(a.out, "h.pfm"), mat, 2 * base * DOME_SX, rng, depth_um=a.scratch_depth,
                      slope_override=a.slope, corr_override=a.corr, density=a.scratch_density)
    gold = mat["gold"]
    alpha = a.alpha if a.alpha is not None else val(mat, "surface", "ggx_alpha")
    L = []
    w = L.append
    w(f"LookAt {eye[0]:.5f} {eye[1]:.5f} {eye[2]:.5f}  {TARGET[0]} {TARGET[1]} {TARGET[2]}  0 0 1")
    w(f'Camera "perspective" "float fov" [ {fov:.6f} ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 16 ]')
    w(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] "string filename" [ "raw.exr" ] '
      '"string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true')
    w("WorldBegin")

    def panel(group, el, az, dist, width, height, scale, K=5500):
        """a soft box (a diffuse rectangle, black behind) in light group `group`: its centre `dist` mm from the target
        at elevation `el`, azimuth `az` (degrees; az 0 = toward the camera, + = the image's right), facing the
        target, its `width` horizontal"""
        e, z = math.radians(el), math.radians(az)
        # pbrt's camera space is left-handed: in its image, the camera's right is world -x
        n = -np.array([-math.sin(z) * math.cos(e), -math.cos(z) * math.cos(e), math.sin(e)])
        centre = np.array(TARGET) - dist * n
        e1 = np.cross([0, 0, 1.0], n)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        hw, hh = width / 2, height / 2
        P = [centre - e1 * hw - e2 * hh, centre + e1 * hw - e2 * hh, centre - e1 * hw + e2 * hh, centre + e1 * hw + e2 * hh]
        w("AttributeBegin")
        w(f'  Attribute "light" "string group" [ "{group}" ]')
        w(f'  AreaLightSource "diffuse" "blackbody L" [ {K} ] "float scale" [ {scale:.6g} ]')
        w('  Material "diffuse" "rgb reflectance" [ 0 0 0 ]')
        w('  Shape "bilinearmesh" "point3 P" [ ' + " ".join(f"{x:.4f}" for p in P for x in p) + ' ] "integer indices" [ 0 1 2 3 ]')
        w("AttributeEnd")
    lt = mat_card_light(a)
    for g in GROUPS:
        panel(g, *lt[g], lt["scale"][g])
    w("AttributeBegin")
    w(f'  Material "diffuse" "spectrum reflectance" [ 360 {lt["paper"]} 830 {lt["paper"]} ]')
    w('  Shape "bilinearmesh" "point3 P" [ -2000 -2000 0 2000 -2000 0 -2000 2000 0 2000 2000 0 ] "integer indices" [ 0 1 2 3 ]')
    # the backdrop: a grey wall behind the piece (the photo's sweep), lit by the same lights
    by = lt["backdrop_y"]
    w(f'  Shape "bilinearmesh" "point3 P" [ -2000 {by} 0 2000 {by} 0 -2000 {by} 2000 2000 {by} 2000 ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    w('Texture "h" "float" "imagemap" "string filename" "h.pfm" "string wrap" "clamp"')
    w("AttributeBegin")
    # the turn: about the sphere's centre, sunk so that the cap's rim stays under the paper
    sink = base * math.sin(math.radians(abs(a.tilt)))
    w(f"  Translate 0 0 {-sink + DOME_H - DOME_R:.5f}")
    w(f"  Rotate {a.tilt} 1 0 0")
    w(f"  Translate 0 0 {DOME_R - DOME_H:.5f}")
    w(f'  Material "conductor" "spectrum eta" "{gold["eta"]["value"]}" "spectrum k" "{gold["k"]["value"]}" '
      f'"float roughness" [ {alpha} ] "bool remaproughness" false "texture displacement" "h"')
    w('  Shape "plymesh" "string filename" [ "dome.ply" ]')
    d_ox = mat["processes"]["oxidation"]["cuprite_nm"]["value"] if a.cuprite is None else a.cuprite
    if exposed.any():
        if d_ox > 0:
            spec = " ".join(f"{x:.5g}" for x in cuprite_on_copper(mat, d_ox))
            w(f'  Material "conductor" "spectrum reflectance" [ {spec} ] "float roughness" [ {alpha} ] "bool remaproughness" false '
              '"texture displacement" "h"')
        else:
            w(f'  Material "conductor" "spectrum eta" "metal-Cu-eta" "spectrum k" "metal-Cu-k" "float roughness" [ {alpha} ] '
              '"bool remaproughness" false "texture displacement" "h"')
        w('  Shape "plymesh" "string filename" [ "copper.ply" ]')
    w("AttributeEnd")
    open(os.path.join(a.out, "scene.pbrt"), "w").write("\n".join(L) + "\n")
    json.dump({"f_number": F_NUMBER, "magnification": round(SENSOR_W / frame_w, 5), "sensor_width_mm": SENSOR_W,
               "focal_mm": FOCAL_MM}, open(os.path.join(a.out, "optics.json"), "w"))
    cam = {"sensor": "canon_eos_5d_mkiv",
           "light": {"blackbody_K": 5500, "why": "the card's soft boxes"},
           "white_balance": {"K": 5500, "why": "on the grey paper, as the photo is (its paper is R = G = B)"},
           "iso": 100,
           "expose": {"percentile": 50, "of_saturation": 0.3, "why": "replaced in develop: the paper in front of the dome is put at the photo's paper level"},
           "develop": {"ev": 0.0, "shoulder_from": 0.9, "contrast": 1.0, "pivot": 0.18, "why": "no grade: compared in the photo's own tone"},
           "sharpen": {"amount": 0.0, "sigma_px": 0.7}, "seed": 1}
    json.dump(cam, open(os.path.join(a.out, "camera.json"), "w"), indent=1)
    info = {"args": vars(a), "fov_deg": fov, "frame_mm": [frame_w, frame_h], "eye": eye.tolist(), "dome_base_radius_mm": base,
            "exposed_triangle_fraction": round(float(exposed.mean()), 5), "cuprite_nm": d_ox, "scratches": n_scr, "alpha": alpha, "light": lt}
    json.dump(info, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), os.path.join(a.out, "scene.pbrt")],
                   check=True, stdout=subprocess.DEVNULL)
    print(json.dumps(info))


def mat_card_light(a):
    """the card's lights (the optics layer, not material parameters), each (elevation, azimuth, distance, width,
    height) and a radiance scale:
    - key: a long horizontal strip above, a little behind the top: the photo's long thin band near the knee's top;
    - s10 ... s80: the front, a sweep of strips by elevation (overhead down to near the table): the knee's front,
      bright under the band and darker toward the bottom;
    - side: an upright box to the right, a little behind: the photo's second, upright highlight;
    grey paper and a grey wall behind (the photo's sweep). Placed by the reflection map of the crop (refmap.py)
    [D from the photo's highlights]; the radiance scales are fitted to the photo's crop (card.py fitlight) [F]."""
    return {**{g: getattr(a, g) for g in GROUPS}, "scale": dict(zip(GROUPS, a.scales)), "paper": 0.5, "backdrop_y": 600.0}


# --- render -----------------------------------------------------------------------------
def render(a):
    d = os.path.abspath(a.dir)
    name = os.path.basename(d.rstrip("/"))
    rd = f"gewu-render/scenes/gilt_copper-{name}"
    files = [os.path.join(d, f) for f in ("scene.pbrt", "scene.cycles.json", "dome.ply", "copper.ply", "h.pfm")]
    subprocess.run(f"ssh link 'mkdir -p ~/{rd}' && scp -q {' '.join(files)} link:{rd}/", shell=True, check=True)
    logs = []
    if a.pbrt:
        log = f"/tmp/gewu-gilt-{name}-pbrt.log"
        subprocess.run(f"ssh link 'rm -f {log}; cd ~ && nohup ~/gewu-render/bin/mini-pbrt.sh ~/{rd} scene.pbrt {log} "
                       f"--outfile pbrt.exr > /dev/null 2>&1 & echo queued'", shell=True, check=True)
        logs.append((log, "pbrt.exr"))
    log = f"/tmp/gewu-gilt-{name}-cyc.log"
    spp = json.load(open(os.path.join(d, "build.json")))["args"]["spp"]
    subprocess.run(f"ssh link 'rm -f {log}; cd ~/{rd} && nohup ~/gewu-render/bin/mini-cycles.sh {log} -b --factory-startup "
                   f"--python-exit-code 1 -P ~/gewu-render/tools-test-metal/cycles_scene.py -- scene.cycles.json "
                   f"--out $PWD/raw.exr --spp {spp} --seed 1 > /dev/null 2>&1 & echo queued'", shell=True, check=True)
    logs.append((log, "raw.exr"))
    for log, f in logs:
        r = subprocess.run(f"ssh link 'while ! tail -1 {log} 2>/dev/null | grep -q \"^done\"; do sleep 3; done; head -1 {log}; tail -1 {log}'",
                           shell=True, capture_output=True, text=True).stdout.strip()
        print(log, "->", r.replace("\n", " | "))
        if not r.splitlines()[-1].startswith("done 0"):
            raise SystemExit(f"{log} failed")
        fs = [f] + ([f"raw.{g}.exr" for g in GROUPS] if f == "raw.exr" else [])      # the light groups' passes
        subprocess.run("scp -q " + " ".join(f"link:{rd}/{x}" for x in fs) + f" {d}/", shell=True, check=True)


# --- develop and compare ---------------------------------------------------------------------------
def paper_box(d):
    """pixels of the paper in front of the dome (below it in the frame), in the 1920 x 1080 film"""
    return (slice(900, 1040), slice(600, 1320))


def develop(a):
    import camera
    d = a.dir
    raw_name = a.raw or "raw.exr"
    cam = json.load(open(os.path.join(d, "camera.json")))
    M = json.load(open(MEASURED))
    raw, _ = camera.to_film_size(camera.read_raw(os.path.join(d, raw_name)))
    S = camera.Spectra("canon_eos_5d_mkiv")
    cal = camera.calibrate(S, camera.blackbody(cam["white_balance"]["K"]))
    paper_G = raw[paper_box(d)][..., 1].mean()
    # linear output of a grey = raw_G * of_saturation / ref / g.min() (camera.develop); put the paper at the photo's level
    target = M["floor_linear"][1]
    of = cam["expose"]["of_saturation"]
    cam["expose"]["raw_ref"] = float(paper_G * of / (cal["gains"].min() * target))
    cam["expose"]["why"] = f"raw_ref puts the paper in front of the dome at the photo's paper (linear {target:.4f})"
    json.dump(cam, open(os.path.join(d, "camera.json"), "w"), indent=1)
    out = os.path.join(d, "dev" if raw_name == "raw.exr" else "dev_" + os.path.splitext(raw_name)[0])
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings", os.path.join(d, "camera.json"),
                    "--first", "0", "--out", out, os.path.join(d, raw_name)], check=True)


def lin8(im):
    x = im.astype(np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def card_dome_box(d, size_px):
    """the dome's centre in the developed 1920 x 1080 image (the projection of the dome's top-front) and a box
    of size_px (w, h) around it"""
    info = json.load(open(os.path.join(d, "build.json")))
    eye, tgt = np.array(info["eye"]), np.array(TARGET)
    fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    t0 = math.radians(CROP_POLAR_DEG)
    r = DOME_R * math.sqrt(1 - (CROP_X_MM / (DOME_R * DOME_SX)) ** 2)        # the cross-section at x = CROP_X_MM
    p = np.array([CROP_X_MM, -r * math.sin(t0), DOME_H - DOME_R + r * math.cos(t0)])   # on the piece's front
    v = p - eye
    t = math.tan(math.radians(info["fov_deg"]) / 2)
    x = (v @ right) / (v @ fwd) / t * (1080 / 2) + 1920 / 2
    y = -(v @ up) / (v @ fwd) / t * (1080 / 2) + 1080 / 2
    w, h = size_px
    return int(round(y - h / 2)), int(round(x - w / 2))


def photo_crop(M, eff):
    """the photo's compared crop (knee_r), 8-bit sRGB, at the card's effective resolution"""
    Image.MAX_IMAGE_PIXELS = None
    photo = Image.open(os.path.join(ROOT, M["photo"])).convert("RGB")
    x0, x1, y0, y1 = M["regions_x0_x1_y0_y1"]["knee_r"]
    ph = photo.crop((x0, y0, x1, y1))
    w, h = ph.size                                         # photo px at 37 px/mm; the card's 1920 film has the same scale
    if eff > 1:                                            # the card was rendered at 1920/eff: bring the photo to that resolution
        ph = ph.resize((w // eff, h // eff), Image.LANCZOS).resize((w, h), Image.BICUBIC)
    return np.asarray(ph)


def light_stats(im8, floor, cell=(20, 60)):
    """what the lights are fitted on: the clipped fraction, luma (over the paper) p5/p50/p95, and the mean luma of
    cells of the crop (rows x columns): where the bright reflections are"""
    lin = lin8(im8) / floor
    Y = lin @ np.array([0.2126, 0.7152, 0.0722])
    h, w = Y.shape
    cells = Y[:h - h % cell[0], :w - w % cell[1]].reshape(h // cell[0], cell[0], w // cell[1], cell[1]).mean((1, 3))
    return {"clipped_fraction": float((im8.max(2) >= 250).mean()), "p5_p50_p95": np.percentile(Y, [5, 50, 95]), "cells": cells}


def dev_clean(raw, ref, cam, cal):
    """camera.develop without the sensor noise (the light fit's model of the development): raw (film size) -> 8 bit"""
    import camera
    v = np.minimum(raw * (cam["expose"]["of_saturation"] / ref), 1.0)
    g = cal["gains"]
    v = np.minimum(v * g, g.min())
    lin = np.maximum(v @ cal["C"].T, 0.0)
    rgb = camera.srgb_encode(camera.tone(lin * (2.0 ** cam["develop"]["ev"] / g.min()), cam["develop"]))
    return np.round(np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def fitlight(a):
    """fit the light groups' radiance scales to the photo's crop: its clipped fraction and where its light falls
    (light_stats' cells), on the render's per-group passes raw.<group>.exr. Exposure as develop: the paper in front
    at the photo's paper. Writes fit.json; rebuild with --scales to render the fitted rig."""
    import camera
    from scipy.optimize import minimize
    d = a.dir
    M = json.load(open(MEASURED))
    cam = json.load(open(os.path.join(d, "camera.json")))
    S = camera.Spectra("canon_eos_5d_mkiv")
    cal = camera.calibrate(S, camera.blackbody(cam["white_balance"]["K"]))
    built = json.load(open(os.path.join(d, "build.json")))
    s0 = np.array([built["light"]["scale"][g] for g in GROUPS])
    ph = photo_crop(M, a.eff)
    h, w = ph.shape[:2]
    r0, c0 = card_dome_box(d, (w, h))
    paper, crop = [], []
    for g in GROUPS:
        raw, _ = camera.to_film_size(camera.read_raw(os.path.join(d, f"raw.{g}.exr")))
        paper.append(raw[paper_box(d)][..., 1].mean())
        crop.append(raw[r0:r0 + h, c0:c0 + w])
    paper, crop = np.array(paper), np.array(crop)
    floor, target = np.array(M["floor_linear"]), M["floor_linear"][1]
    P = light_stats(ph, floor)

    def card(x):                                           # x: scales relative to the build's
        k = np.exp(x)
        ref = (k @ paper) * cam["expose"]["of_saturation"] / (cal["gains"].min() * target)
        return dev_clean(np.tensordot(k, crop, 1), ref, cam, cal)

    def cost(x):
        C = light_stats(card(x), floor)
        sw = np.array([x[i] for i, g in enumerate(GROUPS) if g.startswith("s")])
        return (np.mean((C["cells"] - P["cells"]) ** 2) + 4 * (C["clipped_fraction"] - P["clipped_fraction"]) ** 2
                + 0.5 * np.mean((C["p5_p50_p95"] - P["p5_p50_p95"]) ** 2)
                + 0.002 * np.sum(np.diff(sw) ** 2))             # the sweep's radiance changes smoothly with elevation
    best = None
    for x0 in ([0.0] * len(GROUPS), [-1.0] * len(GROUPS), [1.0] + [-1.0] * (len(GROUPS) - 1)):
        r = minimize(cost, np.array(x0), method="Powell", options={"xtol": 1e-3, "ftol": 1e-7, "maxiter": 20000})
        if best is None or r.fun < best.fun:
            best = r
    k = np.exp(best.x)
    C = light_stats(card(best.x), floor)
    out = {"scales": dict(zip(GROUPS, (k * s0).round(5).tolist())), "relative_to_build": dict(zip(GROUPS, k.round(5).tolist())),
           "cost": float(best.fun),
           "photo": {"clipped_fraction": round(P["clipped_fraction"], 3), "p5_p50_p95": P["p5_p50_p95"].round(3).tolist(),
                     "cells": P["cells"].round(2).tolist()},
           "card_predicted": {"clipped_fraction": round(C["clipped_fraction"], 3), "p5_p50_p95": C["p5_p50_p95"].round(3).tolist(),
                              "cells": C["cells"].round(2).tolist()},
           "tag": "F: radiance scales of the rig, fitted to the photo's crop; the rig's placement is D/A (card.py RIG)"}
    json.dump(out, open(os.path.join(d, "fit.json"), "w"), indent=1)
    Image.fromarray(np.concatenate([ph, np.full((h, 6, 3), 40, np.uint8), card(best.x)], 1)).resize((2 * (2 * w + 6), 2 * h), Image.NEAREST).save(os.path.join(d, "fit.png"))
    print(json.dumps({k_: v for k_, v in out.items() if k_ not in ("photo", "card_predicted")}))
    print("photo", out["photo"]["clipped_fraction"], out["photo"]["p5_p50_p95"], " card", out["card_predicted"]["clipped_fraction"], out["card_predicted"]["p5_p50_p95"])
    print("cells photo / card:")
    for rp, rc in zip(P["cells"], C["cells"]):
        print("  " + " ".join(f"{x:4.2f}" for x in rp) + "  |  " + " ".join(f"{x:4.2f}" for x in rc))


def compare(a):
    import detail
    d = a.dir
    M = json.load(open(MEASURED))
    px_mm = M["scale"]["px_per_mm"]
    eff = a.eff
    ph = photo_crop(M, eff)
    h, w = ph.shape[:2]
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import camera
    devs = [p for p in sorted(os.listdir(d)) if p.startswith("dev")]
    out = os.path.join(d, "cmp")
    os.makedirs(out, exist_ok=True)
    res = {"photo_region": "knee_r", "eff": eff, "px_per_mm": px_mm}
    crops = {"photo": ph}
    for dv in devs:
        im = np.round(camera.read_png16(os.path.join(d, dv, "f0000.png")) * 255).astype(np.uint8)
        r0, c0 = card_dome_box(d, (w, h))
        crops[dv] = im[r0:r0 + h, c0:c0 + w]
        Image.fromarray(im).save(os.path.join(out, f"{dv}_full.png"))
    floor = np.array(M["floor_linear"])
    for k, im in crops.items():
        lin = lin8(im) / floor
        Y = lin.reshape(-1, 3) @ np.array([0.2126, 0.7152, 0.0722])
        clip = im.reshape(-1, 3).max(1) >= 250                 # a clipped channel: its colour is not the gold's
        q = {"clipped_fraction": round(float(clip.mean()), 3)}
        for lo, hi in ((5, 50), (50, 90)):                     # colour from unclipped pixels, by luma band
            m = (Y >= np.percentile(Y, lo)) & (Y <= np.percentile(Y, hi)) & ~clip
            c = lin.reshape(-1, 3)[m].mean(0)
            q[f"p{lo}_{hi}"] = {"R_over_G": round(float(c[0] / c[1]), 3), "B_over_G": round(float(c[2] / c[1]), 3),
                                "luma_over_floor": round(float(Y[m].mean()), 3)}
        # the highlight's shoulder: unclipped pixels 2-8 px from a clipped one, brighter than the median: a single
        # reflection of the white lights (no gold sees gold there), the test of interreflection against the pipeline
        from scipy.ndimage import binary_dilation
        cl = im.max(2) >= 250
        sh = (binary_dilation(cl, iterations=8) & ~binary_dilation(cl, iterations=2) & (im.max(2) < 240)
              & (Y.reshape(im.shape[:2]) > np.median(Y))).ravel()
        if sh.sum() > 50:
            c = lin.reshape(-1, 3)[sh].mean(0)
            q["shoulder"] = {"R_over_G": round(float(c[0] / c[1]), 3), "B_over_G": round(float(c[2] / c[1]), 3),
                             "pixels": int(sh.sum())}
        msk = np.ones(im.shape[:2], bool)
        bands, _ = detail.profile(im, msk)
        low = np.zeros(im.shape[:2], bool)
        low[im.shape[0] // 2:] = True                          # the lower half: the front, below the top highlight
        bands_low, _ = detail.profile(im, low)
        res[k] = {"colour": q, "luma_over_floor_p5_p50_p95": np.percentile(Y, [5, 50, 95]).round(3).tolist(),
                  "detail_pct": [round(100 * float(b), 2) for b in bands],
                  "detail_pct_lower_half": [round(100 * float(b), 2) for b in bands_low],
                  "detail_bands_mm": [[round(lo / (px_mm / eff), 3), round(hi / (px_mm / eff), 3)] for lo, hi in detail.BANDS]}
    M709 = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])     # linear BT.709 -> XYZ (D65)
    wht = M709 @ np.ones(3)
    for dv in devs:
        for band in ("p5_50", "p50_90"):
            cp, cc = res["photo"]["colour"].get(band), res[dv]["colour"].get(band)
            if not cp or not cc or not np.isfinite(cc["R_over_G"]):
                continue
            # the two colours at the same luma (0.5 of the paper): a chroma/hue difference only
            labs = []
            for c in (cp, cc):
                rgb = np.array([c["R_over_G"], 1.0, c["B_over_G"]])
                rgb *= 0.5 / (rgb @ [0.2126, 0.7152, 0.0722])
                labs.append(camera.lab((M709 @ rgb)[None], wht)[0])
            res[dv]["colour"][band]["dE_ab_vs_photo_same_luma"] = round(float(np.linalg.norm(labs[0] - labs[1])), 2)
    # side by side: the photo crop and each card crop, 2x enlarged
    tiles = [crops["photo"]] + [crops[dv] for dv in devs]
    sheet = Image.new("RGB", (len(tiles) * (w + 6), h), (40, 40, 40))
    for i, t in enumerate(tiles):
        sheet.paste(Image.fromarray(t), (i * (w + 6), 0))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sp = os.path.join(out, "side_by_side.png")
    sheet.save(sp)
    json.dump(res, open(os.path.join(out, "numbers.json"), "w"), indent=1)
    print(sp)
    print(json.dumps(res, indent=1))


def turns(a):
    """the turn frames side by side: the dome's region of each developed frame (dirs in order)"""
    import camera
    tiles = []
    for d in a.dirs:
        im = np.round(camera.read_png16(os.path.join(d, "dev", "f0000.png")) * 255).astype(np.uint8)
        r0, c0 = card_dome_box(d, (1000, 560))
        tiles.append(im[max(r0, 0):r0 + 560, max(c0, 0):c0 + 1000])
    h, w = tiles[0].shape[:2]
    sheet = Image.new("RGB", (w, len(tiles) * (h + 6)), (40, 40, 40))
    for i, t in enumerate(tiles):
        sheet.paste(Image.fromarray(t), (0, i * (h + 6)))
    sheet.save(a.out)
    print(a.out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--res", default="960x540")
    b.add_argument("--spp", type=int, default=256)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--tilt", type=float, default=0.0, help="degrees about x (the turn frames)")
    b.add_argument("--alpha", type=float, help="override material.json's alpha (sweeps)")
    b.add_argument("--scratch-depth", type=float, help="override material.json's scratch depth, um (sweeps)")
    b.add_argument("--slope", type=float, help="override the undulation's rms slope (sweeps)")
    b.add_argument("--wear", type=float, help="override the abrasion's wear depth at the top, um (the demonstration frame)")
    b.add_argument("--cuprite", type=float, help="override the oxidation's cuprite thickness, nm (the demonstration frame)")
    b.add_argument("--scratch-density", type=float, help="override the scratches per mm^2 (sweeps)")
    b.add_argument("--corr", type=float, help="override the undulation's correlation length, mm (sweeps)")
    for g, v in RIG.items():
        b.add_argument(f"--{g}", type=float, nargs=5, default=v, metavar=("EL", "AZ", "DIST", "W", "H"))
    b.add_argument("--scales", type=float, nargs=len(GROUPS), default=RIG_SCALES, metavar=GROUPS,
                   help="radiance scales (fitlight fits them on a render's light groups)")
    r = sub.add_parser("render")
    r.add_argument("dir")
    r.add_argument("--pbrt", action="store_true", help="also pbrt (CPU slot), to pbrt.exr")
    v = sub.add_parser("develop")
    v.add_argument("dir")
    v.add_argument("--raw", help="raw file in dir (default raw.exr; e.g. pbrt.exr)")
    c = sub.add_parser("compare")
    c.add_argument("dir")
    c.add_argument("--eff", type=int, default=2)
    f = sub.add_parser("fitlight")
    f.add_argument("dir")
    f.add_argument("--eff", type=int, default=2)
    t = sub.add_parser("turns")
    t.add_argument("out")
    t.add_argument("dirs", nargs="+")
    a = ap.parse_args()
    {"build": build, "render": render, "develop": develop, "compare": compare, "fitlight": fitlight, "turns": turns}[a.cmd](a)


if __name__ == "__main__":
    main()
