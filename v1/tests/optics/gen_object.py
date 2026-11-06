"""The optics tests' objects, each a pbrt fragment (no camera, no lights) in out/optics/objects/<name>/ for recipes to
Include, with <name>.silhouette.json (its profile of revolution, for framing to an arc: optics/framing.py).

    python3 -I tests/optics/gen_object.py [vase dome_glaze dome_relief plate_marble]     (default: all)

Test objects, not material cards: each is chosen to show what a rig does (a smooth even glaze
shows nothing under raking light, an opaque vase is only a silhouette against a backlight).
- vase: shot 6's vase with shot 6's glaze (below).
- dome_glaze: a low dome (a spherical cap, 200 mm across, 35 mm high: a lid or a shield's shape [A], the shape of the
  reference film's arcs) in shot 6's glaze; for the soft, flat and top-light rigs.
- dome_relief: the same dome, diffuse, with a bump map of a carved-looking relief (raised motifs 0.8 mm high with
  0.4 mm soft edges on a finely grained ground [A], a test pattern, not a craft): for raking light, until the carved
  lacquer test plate (crafts/carving) is ready. Its colour is a placeholder [A].
- plate_marble: a thin disc (240 mm across, 4 mm thick, its edge rounded) standing on its edge, of marble as Jensen
  et al. 2001 measured it (pbrt-v4's medium preset "Marble", media.cpp) as a stand-in for jade [A]; for backlight.

- Form: shots/06-guan/vessel.py's profile (the Palace Museum vase's measured silhouette near the belly, 141 mm
  across; the neck top, lower belly and foot ring are SKETCHES there), revolved, and closed here with a flat lid on
  the neck (a SKETCH: the real mouth is open) and a flat foot.
vase:
- Material: shot 6's glaze model, from shots/06-guan/scene.py's GLAZE (S2: a 1.2 mm dielectric shell, n 1.5 [A],
  roughness from the measured gloss of Guan fenqing, over a medium fitted to Guan fenqing's reflectance, on a
  0.12 grey body). Not a validated material: the Guan glaze card is being made (materials/guan_glaze/). Here it is
  only something glossy and translucent to light.
"""
import json
import math
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "shots/06-guan"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
from vessel import Vessel  # noqa: E402
import scene as S06  # noqa: E402  (shot 6's scene generator: its GLAZE, held(), spectrum())
sys.path.insert(0, os.path.join(ROOT, "tools"))
from studio import write_ply  # noqa: E402
import rgbscene  # noqa: E402

OUTS = os.path.join(ROOT, "out/optics/objects")
GLAZE_MM = 1.2                 # shot 6's fit (out/06/lk_150s)
STEP_MM = 1.0                  # along the profile
N_AROUND = 256
DOME_A, DOME_H = 100.0, 35.0   # the dome's base radius and height, mm [A]
PLATE_R, PLATE_T = 120.0, 4.0  # the marble disc's radius and thickness, mm [A] (2 mm showed the lamp through it)
RELIEF_PX, RELIEF_SEED = 2048, 3
# Jensen, Marschner, Levoy, Hanrahan 2001, "A Practical Model for Subsurface Light Transport", marble: reduced
# scattering and absorption, 1/mm, at their R, G, B [M]; as pbrt-v4 has them (media.cpp, preset "Marble"), which turns
# them into spectra as RGBUnboundedSpectrum in sRGB; used with g = 0, as pbrt's preset is
MARBLE_SIGMA_S = (2.19, 2.62, 3.00)
MARBLE_SIGMA_A = (0.0021, 0.0041, 0.0071)
MARBLE_ETA = 1.5               # [A]: pbrt's default; calcite's two indices are 1.486 and 1.658 [I]


def resample(R, Z, step):
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(R), np.diff(Z)))])
    n = max(2, int(math.ceil(s[-1] / step)) + 1)
    t = np.linspace(0, s[-1], n)
    return np.interp(t, s, R), np.interp(t, s, Z)


def closed_profile(v):
    """Pieces from the axis at the lid, down the side, to the axis under the foot; each piece keeps its own normals
    (the lid's and foot's edges are sharp)."""
    R, Z = v.R, v.Z                                     # lip (top) to foot (bottom), mm
    lid = (np.array([0.0, R[0]]), np.array([Z[0], Z[0]]))
    foot = (np.array([R[-1], 0.0]), np.array([Z[-1], Z[-1]]))
    return [resample(*lid, STEP_MM), resample(R, Z, STEP_MM), resample(*foot, STEP_MM)]


def normals2d(R, Z):
    dR, dZ = np.gradient(R), np.gradient(Z)
    n = np.c_[-dZ, dR]                                  # outward, for a profile run lid -> side -> foot
    return n / np.linalg.norm(n, axis=1, keepdims=True)


def revolve(pieces, N_AROUND=N_AROUND):
    """Triangles of the surface of revolution of the pieces, with a single vertex on the axis at each pole."""
    P, N, T = [], [], []
    ph = 2 * np.pi * np.arange(N_AROUND) / N_AROUND
    c, s = np.cos(ph), np.sin(ph)
    for R, Z in pieces:
        n2 = normals2d(R, Z)
        base = len(P)
        rows = []
        for i, (r, z) in enumerate(zip(R, Z)):
            if r < 1e-9:
                rows.append([len(P)])
                P.append((0.0, 0.0, z))
                N.append((0.0, 0.0, float(np.sign(n2[i, 1]))))
            else:
                rows.append(list(range(len(P), len(P) + N_AROUND)))
                P += list(zip(r * c, r * s, np.full(N_AROUND, z)))
                N += list(zip(n2[i, 0] * c, n2[i, 0] * s, np.full(N_AROUND, n2[i, 1])))
        for a, b in zip(rows[:-1], rows[1:]):
            for k in range(N_AROUND):
                k1 = (k + 1) % N_AROUND
                if len(a) == 1:
                    T.append((a[0], b[k], b[k1]))
                elif len(b) == 1:
                    T.append((a[k], b[0], a[k1]))
                else:
                    T += [(a[k], b[k], b[k1]), (a[k], b[k1], a[k1])]
    P, N, T = np.array(P), np.array(N), np.array(T)
    # wind every triangle so that its geometric normal points out (agrees with the shading normal)
    gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    flip = np.einsum("ij,ij->i", gn, N[T].mean(1)) < 0
    T[flip] = T[flip][:, [0, 2, 1]]
    return P, N, T


def offset(pieces, d):
    """The closed profile moved inwards by d (mitred at the sharp edges), as one smooth piece."""
    R = np.concatenate([p[0] if i == 0 else p[0][1:] for i, p in enumerate(pieces)])
    Z = np.concatenate([p[1] if i == 0 else p[1][1:] for i, p in enumerate(pieces)])
    seg = np.c_[np.diff(R), np.diff(Z)]
    seg /= np.linalg.norm(seg, axis=1, keepdims=True)
    ns = np.c_[-seg[:, 1], seg[:, 0]]                   # outward normal per segment
    nv = np.vstack([ns[:1], ns[:-1] + ns[1:], ns[-1:]])
    nv /= np.linalg.norm(nv, axis=1, keepdims=True)
    cos = np.ones(len(R))
    cos[1:-1] = np.einsum("ij,ij->i", nv[1:-1], ns[1:])  # the mitre: d / cos(half the turn)
    Ri, Zi = R - d * nv[:, 0] / cos, Z - d * nv[:, 1] / cos
    Ri[0], Ri[-1] = 0.0, 0.0
    return [(Ri, Zi)]


def glaze_lines():
    """Shot 6's glaze medium and materials, as shots/06-guan/scene.py writes them (lines 697-716)."""
    G, fit = S06.GLAZE, S06.GLAZE["fits"][GLAZE_MM]
    ss = fit["sigma_s"]
    med = (f'MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" {S06.spectrum(S06.held(fit["sigma_a"]))} '
           f'"spectrum sigma_s" [ 360 {ss} 830 {ss} ] "float g" [ {G["g"]} ] "float scale" [ 1 ]')
    outer = (f'Material "dielectric" "float eta" [ {G["eta"]} ] "float roughness" [ {S06.GLAZE_ROUGHNESS} ] '
             f'"bool remaproughness" false "bool refractivenee" true')
    rb = fit["body_reflectance"]
    body = f'Material "diffuse" "spectrum reflectance" [ 360 {rb} 830 {rb} ]'
    return med, outer, body


def write_silhouette(path, pieces, axis=(0, 0, 1), origin=(0, 0, 0)):
    json.dump({"kind": "revolved", "origin": list(origin), "axis": list(axis),
               "pieces": [[np.round(R, 5).tolist(), np.round(Z, 5).tolist()] for R, Z in pieces],
               "about": "the outer surface's profile of revolution (r, z along the axis), mm, in the object's own "
                        "frame; pieces are smooth, their joins sharp (tests/optics/gen_object.py)"},
              open(path, "w"))


def vase():
    out = os.path.join(OUTS, "vase")
    os.makedirs(out, exist_ok=True)
    v = Vessel(os.path.join(ROOT, "shots/06-guan/form.json"))
    pieces = closed_profile(v)
    write_ply(os.path.join(out, "vase_glaze.ply"), *revolve(pieces))
    write_ply(os.path.join(out, "vase_body.ply"), *revolve(offset(pieces, GLAZE_MM)))
    write_silhouette(os.path.join(out, "vase.silhouette.json"), pieces)
    med, outer, body = glaze_lines()
    with open(os.path.join(out, "vase.pbrt"), "w") as f:
        f.write(f"""# the optics tests' object (tests/optics/gen_object.py): shot 6's vase form, revolved and closed (SKETCH lid
# and foot), {v.Rb * 2:.0f} mm across the belly, {v.Z.max() - v.Z.min():.0f} mm tall; shot 6's glaze model copied from
# shots/06-guan/scene.py's GLAZE (S2 fit; not a validated material)
{med}
AttributeBegin
  MediumInterface "glaze" ""
  {outer}
  Shape "plymesh" "string filename" [ "vase_glaze.ply" ]
AttributeEnd
AttributeBegin
  MediumInterface "" "glaze"
  {body}
  Shape "plymesh" "string filename" [ "vase_body.ply" ]
AttributeEnd
""")
    print(f"-> {out}: belly {v.Rb * 2:.0f} mm, height {v.Z.max() - v.Z.min():.1f} mm, glaze {GLAZE_MM} mm")


def dome_pieces():
    """A spherical cap on a flat base: apex -> rim, rim -> axis (the rim is sharp)."""
    Rs = (DOME_A ** 2 + DOME_H ** 2) / (2 * DOME_H)
    th = np.linspace(0, math.asin(DOME_A / Rs), 2000)
    cap = resample(Rs * np.sin(th), DOME_H - Rs * (1 - np.cos(th)), STEP_MM)
    base = resample(np.array([DOME_A, 0.0]), np.array([0.0, 0.0]), STEP_MM)
    return [cap, base], Rs


def dome_glaze():
    out = os.path.join(OUTS, "dome_glaze")
    os.makedirs(out, exist_ok=True)
    pieces, Rs = dome_pieces()
    write_ply(os.path.join(out, "dome_glaze.ply"), *revolve(pieces, 1024))
    write_ply(os.path.join(out, "dome_body.ply"), *revolve(offset(pieces, GLAZE_MM), 1024))
    write_silhouette(os.path.join(out, "dome_glaze.silhouette.json"), pieces)
    med, outer, body = glaze_lines()
    with open(os.path.join(out, "dome_glaze.pbrt"), "w") as f:
        f.write(f"""# the optics tests' glazed dome (tests/optics/gen_object.py): a spherical cap {2 * DOME_A:g} mm across, {DOME_H:g} mm
# high (sphere radius {Rs:.1f} mm) on a flat base [A]; shot 6's glaze model copied from shots/06-guan/scene.py's GLAZE
# (S2 fit; not a validated material), {GLAZE_MM} mm over a grey body
{med}
AttributeBegin
  MediumInterface "glaze" ""
  {outer}
  Shape "plymesh" "string filename" [ "dome_glaze.ply" ]
AttributeEnd
AttributeBegin
  MediumInterface "" "glaze"
  {body}
  Shape "plymesh" "string filename" [ "dome_body.ply" ]
AttributeEnd
""")
    print(f"-> {out}: dome {2 * DOME_A:g} x {DOME_H:g} mm, glaze {GLAZE_MM} mm")


def relief_height(n, size_mm, seed):
    """A carved-looking test relief (mm) [A]: raised motifs where band-limited noise is high, 0.8 mm, with soft
    0.4 mm edges, and a ground grained at 0.25 mm, 0.03 mm rms. Row 0 = the top of the image (v = 1)."""
    px = size_mm / n
    rng = np.random.default_rng(seed)
    blob = gaussian_filter(rng.standard_normal((n, n)), 4.0 / px, mode="wrap")
    motif = gaussian_filter((blob > 0.25 * blob.std()).astype(float), 0.4 / px, mode="wrap")
    grain = gaussian_filter(rng.standard_normal((n, n)), 0.25 / px, mode="wrap")
    grain *= 0.03 / grain.std()
    return 0.8 * motif + grain * (1 - 0.7 * motif)


def dome_relief():
    out = os.path.join(OUTS, "dome_relief")
    os.makedirs(out, exist_ok=True)
    pieces, Rs = dome_pieces()
    P, N, T = revolve(pieces, 1024)
    uv = np.c_[P[:, 0] / (2 * DOME_A) + 0.5, P[:, 1] / (2 * DOME_A) + 0.5]      # straight down onto the base
    write_ply(os.path.join(out, "dome_relief.ply"), P, N, T, uv)
    write_silhouette(os.path.join(out, "dome_relief.silhouette.json"), pieces)
    h = relief_height(RELIEF_PX, 2 * DOME_A, RELIEF_SEED).astype("<f4")
    with open(os.path.join(out, "relief.pfm"), "wb") as f:                  # one channel; PFM stores the bottom row first
        f.write(b"Pf\n" + f"{RELIEF_PX} {RELIEF_PX}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(h[::-1]).tobytes())
    with open(os.path.join(out, "dome_relief.pbrt"), "w") as f:
        f.write(f"""# the optics tests' relief dome (tests/optics/gen_object.py): the glazed dome's shape, diffuse, with a bump map
# of a carved-looking test relief (raised motifs 0.8 mm, soft edges, grained ground) [A]; colour a placeholder [A]
Texture "relief" "float" "imagemap" "string filename" [ "relief.pfm" ] "string wrap" [ "clamp" ]
AttributeBegin
  Material "diffuse" "rgb reflectance" [ 0.45 0.25 0.14 ] "texture displacement" "relief"
  Shape "plymesh" "string filename" [ "dome_relief.ply" ]
AttributeEnd
""")
    print(f"-> {out}: relief {RELIEF_PX} px over {2 * DOME_A:g} mm ({2 * DOME_A / RELIEF_PX:.3f} mm/px), "
          f"height {h.min():.2f}..{h.max():.2f} mm")


def unbounded_spectrum(rgb):
    """pbrt's RGBUnboundedSpectrum of an sRGB triple (scale 2 max, the sigmoid of rgb / scale), as pbrt's
    spectrum samples every 5 nm."""
    sen = rgbscene.Sensor("canon_eos_5d_mkiv", 5500.0)      # only its sRGB sigmoid solve is used (D65, CIE)
    m = max(rgb)
    s = 2 * m * sen.sigmoid_spectrum(np.asarray(rgb) / (2 * m))
    lam = np.arange(360, 831, 5)
    v = np.interp(lam, rgbscene.LAM, s)
    return "[ " + " ".join(f"{a:g} {b:.6g}" for a, b in zip(lam, v)) + " ]"


def plate_marble():
    out = os.path.join(OUTS, "plate_marble")
    os.makedirs(out, exist_ok=True)
    rho = PLATE_T / 2
    a = np.linspace(math.pi / 2, -math.pi / 2, 40)
    face = (np.array([0.0, PLATE_R - rho]), np.array([rho, rho]))
    edge = ((PLATE_R - rho) + rho * np.cos(a), rho * np.sin(a))
    back = (np.array([PLATE_R - rho, 0.0]), np.array([-rho, -rho]))
    R = np.concatenate([resample(*face, STEP_MM)[0], edge[0][1:-1], resample(*back, STEP_MM)[0]])
    Z = np.concatenate([resample(*face, STEP_MM)[1], edge[1][1:-1], resample(*back, STEP_MM)[1]])
    pieces = [(R, Z)]                                           # one smooth piece: the edge is a half round
    P, N, T = revolve(pieces, 1024)
    rot = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)  # the disc's axis (local z) -> -Y, towards the camera
    write_ply(os.path.join(out, "plate_marble.ply"), P @ rot.T, N @ rot.T, T)
    write_silhouette(os.path.join(out, "plate_marble.silhouette.json"), pieces, axis=(0, -1, 0))
    with open(os.path.join(out, "plate_marble.pbrt"), "w") as f:
        f.write(f"""# the optics tests' translucent plate (tests/optics/gen_object.py): a disc {2 * PLATE_R:g} mm across, {PLATE_T:g} mm
# thick, edge a half round, standing on its edge facing -Y [A]; marble as Jensen et al. 2001 measured it (pbrt-v4's
# preset "Marble": sigma_s' {MARBLE_SIGMA_S}, sigma_a {MARBLE_SIGMA_A} per mm at R, G, B [M], spectra as pbrt's
# RGBUnboundedSpectrum, g 0), a stand-in for jade [A]; smooth surface, eta {MARBLE_ETA} [A]
MakeNamedMedium "marble" "string type" "homogeneous" "spectrum sigma_a" {unbounded_spectrum(MARBLE_SIGMA_A)}
    "spectrum sigma_s" {unbounded_spectrum(MARBLE_SIGMA_S)} "float g" [ 0 ] "float scale" [ 1 ]
AttributeBegin
  MediumInterface "marble" ""
  Material "dielectric" "float eta" [ {MARBLE_ETA} ] "float roughness" [ 0 ] "bool remaproughness" false
  Shape "plymesh" "string filename" [ "plate_marble.ply" ]
AttributeEnd
""")
    print(f"-> {out}: disc {2 * PLATE_R:g} x {PLATE_T:g} mm, marble")


MAKERS = {"vase": vase, "dome_glaze": dome_glaze, "dome_relief": dome_relief, "plate_marble": plate_marble}


def main():
    names = sys.argv[1:] or list(MAKERS)
    for n in names:
        if n not in MAKERS:
            raise SystemExit(f"{n}: one of {list(MAKERS)}")
        MAKERS[n]()


if __name__ == "__main__":
    main()
