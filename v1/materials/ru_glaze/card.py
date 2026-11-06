"""The Ru glaze's thickness strip: a wedge of glaze, 0.1 mm thick at one end and 1.0 mm at the other, on a flat
body, seen straight down under a soft box, to show what the glaze does with its thickness (thin glaze shows the
body, pooled glaze is greener). The glaze comes from a fit (fit.py --out): its scatterers' sigma_s and g, made one
lobe at material.json's render g* (similarity), the iron's sigma_a, Appen's n, the surface alpha, the body (rho0
and its warmth t); the path limit is material.json's render max_depth.

    python3 -I materials/ru_glaze/card.py --fit out/ru/fit/R2_SCI.json --out out/ru/strip/R2 [--res 960x240]
    python3 -I materials/ru_glaze/card.py view out/ru/strip/R2/raw.exr --out strip.png --card out/ru/strip/R2/card.json
    python3 -I materials/ru_glaze/card.py ref --card out/ru/strip/R2/card.json [--mixture]     # the slab's prediction

Writes scene.pbrt with glaze.ply (a closed wedge: Cycles fills a medium only inside a closed mesh, docs/slab.md)
and the body, for pbrt and, through tools/rgbscene.py, Cycles.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import glaze  # noqa: E402
import shell  # noqa: E402

E0, E1 = 0.1, 1.0             # the wedge's thickness at x = -HX and x = +HX, mm
HX, HY = 30.0, 6.0            # half-size of the wedge, mm
# the soft box, 300 mm square, 45 deg up towards -y at 424 mm, facing the strip (corners p00 p10 p01 p11, mm)
BOX = ((-150, -193.934, 406.066), (150, -193.934, 406.066), (-150, -406.066, 193.934), (150, -406.066, 193.934))


def wedge(hx, hy, e0, e1, z_bottom):
    """A closed hexahedron: the top plane from z = e0 at x = -hx to z = e1 at x = +hx, the bottom at z_bottom.
    shell.box's faces, its top corners lifted; the top's uv spans 0..1."""
    P, N, T, UV = shell.box(hx, hy, 1.0, z_bottom)
    top = P[:, 2] == 1.0
    P[top, 2] = e0 + (e1 - e0) * (P[top, 0] + hx) / (2 * hx)
    # flat normals again, from the faces (the top and the two end faces are no longer what box() wrote)
    for f in range(6):
        i = slice(4 * f, 4 * f + 4)
        a, b, c = P[4 * f], P[4 * f + 1], P[4 * f + 2]
        n = np.cross(b - a, c - a)
        N[i] = n / np.linalg.norm(n)
    return P, N, T, UV


def write_ply(path, P, N, T, uv=None):
    P, N, T = np.asarray(P, "<f4"), np.asarray(N, "<f4"), np.asarray(T, "<i4")
    props = "property float x\nproperty float y\nproperty float z\nproperty float nx\nproperty float ny\nproperty float nz\n"
    cols = [P, N]
    if uv is not None:
        props += "property float u\nproperty float v\n"
        cols.append(np.asarray(uv, "<f4"))
    head = (f"ply\nformat binary_little_endian 1.0\nelement vertex {len(P)}\n{props}element face {len(T)}\n"
            f"property list uchar int vertex_indices\nend_header\n")
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"], face["i"] = 3, T
    with open(path, "wb") as f:
        f.write(head.encode())
        f.write(np.ascontiguousarray(np.concatenate(cols, 1)).tobytes())
        f.write(face.tobytes())


def spectrum_pbrt(lam, v):
    lam = list(lam)
    v = list(v)
    # hold the end values out to pbrt's 360-830 nm
    lam = [360.0] + lam + [830.0]
    v = [v[0]] + v + [v[-1]]
    return "[ " + " ".join(f"{l:g} {x:.6g}" for l, x in zip(lam, v)) + " ]"


def view(raw_path, out_png, rho0, t, sensor="canon_eos_5d_mkiv", K=5500):
    """A noise-free view of a strip render: white-balanced for the soft box (a 5500 K blackbody), the colour matrix
    of tools/camera.py, and the exposure set by the bare body, so that the image's linear values are reflectances
    under that light (the body reads its own Y under D65). Returns L*a*b* (D65) along the wedge, per 0.1 mm of
    thickness, and the body's linear BT.709."""
    from PIL import Image
    from camera import LAM, Spectra, blackbody, calibrate, read_raw, srgb_encode, lab, rgb709_from_xyz
    import fit as F
    S = Spectra(sensor)
    cal = calibrate(S, blackbody(K))
    raw = read_raw(raw_path)
    h, w, _ = raw.shape
    lin = np.maximum((raw * cal["gains"]) @ cal["C"].T, 0.0)
    y_body = (S.cmf[1] * S.d65) @ F.body_rho(LAM, rho0, t) / (S.cmf[1] @ S.d65)
    Y = np.array([0.2126, 0.7152, 0.0722])                 # BT.709's luminance
    # the frame is 64 mm across, the wedge 60 mm x 12 mm in the middle: the body above and below it
    mm = 64.0 / w
    # world coordinates of the pixels: pbrt's LookAt makes the camera's right cross(up, dir) = world -x here, and
    # its up world +y (the soft box is at the bottom of the image)
    ys = -(np.arange(h) - h / 2 + 0.5) * mm
    xs = -(np.arange(w) - w / 2 + 0.5) * mm
    # the bare body beside the thin third of the wedge: the thick end's soft shadow (the box reaches down to 25 deg)
    # would fall up to 2 mm past the wedge's side
    body = lin[np.abs(ys) > HY + 1.0][:, (xs > -HX) & (xs < -HX / 3)].reshape(-1, 3).mean(0)
    k = y_body / (body @ Y)
    lin = lin * k
    Image.fromarray((np.clip(srgb_encode(np.clip(lin, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)).save(out_png)
    # along the wedge: the middle half of its width, in 0.1 mm thickness bins (x maps linearly onto E0..E1)
    band = lin[np.abs(ys) < HY / 2]
    e = E0 + (E1 - E0) * (xs + HX) / (2 * HX)
    white = S.cmf @ S.d65 / (S.cmf[1] @ S.d65)
    xyz = band.mean(0) @ np.linalg.inv(rgb709_from_xyz(white)).T
    L = lab(xyz, white)
    rows = []
    for e0 in np.arange(E0, E1 + 1e-9, 0.1):
        m = (np.abs(xs) < HX - 0.5) & (np.abs(e - e0) < 0.05)
        if m.any():
            rows.append((round(float(e0), 2), *[float(v) for v in L[m].mean(0)]))
    return rows, body * k


def projected_solid_angle(P):
    """The quad's projected solid angle (cosine-weighted, onto the z = 0 plane) from the origin: Lambert's formula
    for a polygon, sum over the edges of the angle each subtends times the cosine of its plane's normal to z."""
    v = [np.asarray(P[i], float) / np.linalg.norm(P[i]) for i in (0, 1, 3, 2)]      # around the boundary
    tot = 0.0
    for i in range(4):
        a, b = v[i], v[(i + 1) % 4]
        c = np.cross(a, b)
        tot += math.atan2(np.linalg.norm(c), a @ b) * c[2] / np.linalg.norm(c)
    return abs(0.5 * tot)


def reference(card, fit, thicknesses, nphot=40000, mixture=False, sensor="canon_eos_5d_mkiv", K=5500):
    """The slab's prediction of the strip (tools/slab.py): per thickness, what the camera looking straight down
    sees of the soft box's light (reciprocity: light in along the view, out towards the box; with the rough
    surface's reflection of the box), as a reflectance (the bare body's view of the box is Omega_proj / pi), through
    the same camera and exposure as view().
    mixture: the exact lobes of the fit's scatterers and no path limit (the physics); otherwise one lobe at
    the card's g* and its max_depth (what the renderers were given)."""
    import fit as F
    import slab
    from camera import LAM, Spectra, blackbody, calibrate, lab, rgb709_from_xyz
    mat = glaze.load()
    s = mat["samples"][fit["sample"]]
    lam = np.array(fit["lam"])
    # one n for all wavelengths, as the scene gives both renderers (Cycles has no dispersion; fit.py keeps it)
    n = np.full(len(lam), glaze.appen_nD(s["composition_wt"]["value"])[0])
    sa = glaze.sigma_a(lam, fit["sample"], mat)
    rho = F.body_rho(lam, card["body_rho0"], card["body_t"])
    kinds = list(fit["sigma_s"])
    ss_k = np.array([fit["sigma_s"][k] for k in kinds])
    g_k = np.array([fit["g"][k] for k in kinds])
    g_star = card["g_star"]
    ss_star = (ss_k * (1 - g_k)).sum(0) / (1 - g_star)
    omega = projected_solid_angle(BOX) / math.pi
    S = Spectra(sensor)
    light = blackbody(K)
    cal = calibrate(S, light)
    white = S.cmf @ S.d65 / (S.cmf[1] @ S.d65)
    Y = np.array([0.2126, 0.7152, 0.0722])

    def camera(R):                                       # a reflectance on lam -> linear BT.709 through the camera
        RL = np.interp(LAM, lam, R)
        return ((S.sens @ (light * RL)) * cal["gains"]) @ cal["C"].T
    k = (S.cmf[1] * S.d65) @ F.body_rho(LAM, card["body_rho0"], card["body_t"]) / (S.cmf[1] @ S.d65) \
        / (camera(rho) @ Y)
    rows = []
    for d in thicknesses:
        R = np.zeros(len(lam))
        for i in range(len(lam)):
            if mixture:
                ss = float(ss_k[:, i].sum())
                layer, lim = (d, ss, 0.0, tuple((float(ss_k[j, i]) / ss, float(g_k[j, i])) for j in range(len(kinds)))), None
            else:
                layer, lim = (d, float(ss_star[i]), 0.0, g_star), card["max_depth"]
            # one seed for all wavelengths: their noise is shared, so the colour (differences between bands) is
            # far less noisy than the lightness
            r = slab.run(float(n[i]), [layer], 1.0, 1.0, nphot=nphot, seed=21, lights=[("box", BOX)],
                         alpha=fit["alpha"], record=True, max_vertices=lim)
            # the light that went in and came out towards the box, and the surface's own reflection of it
            R[i] = (slab.events_apply(r["events"], nphot, [sa[i]], rho[i], light_scale={"box": 1.0})[1][0]
                    + r["lights_specular"]["box"]) / omega
        lin = camera(R) * k
        L = lab(lin @ np.linalg.inv(rgb709_from_xyz(white)).T, white)
        rows.append((d, *[float(v) for v in L]))
    return rows


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "ref":
        rp = argparse.ArgumentParser()
        rp.add_argument("cmd")
        rp.add_argument("--card", required=True)
        rp.add_argument("--d", default="0.1,0.3,0.5,0.7,1.0")
        rp.add_argument("--nphot", type=int, default=40000)
        rp.add_argument("--mixture", action="store_true")
        rp.add_argument("--out")
        r = rp.parse_args()
        card = json.load(open(r.card))
        fit = json.load(open(os.path.join(ROOT, card["fit"])))
        rows = reference(card, fit, [float(v) for v in r.d.split(",")], r.nphot, r.mixture)
        for row in rows:
            print(f"  e {row[0]:.1f} mm: L*a*b* {row[1]:6.2f} {row[2]:6.2f} {row[3]:6.2f}", flush=True)
        if r.out:
            with open(r.out, "w") as f:
                json.dump({"card": r.card, "mixture": r.mixture, "nphot": r.nphot, "rows": rows}, f, indent=1)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "view":
        vp = argparse.ArgumentParser()
        vp.add_argument("cmd")
        vp.add_argument("raw")
        vp.add_argument("--out", required=True)
        vp.add_argument("--card", required=True, help="the strip's card.json (for its body)")
        v = vp.parse_args()
        c = json.load(open(v.card))
        rows, body = view(v.raw, v.out, c["body_rho0"], c["body_t"])
        print("body (linear BT.709, exposure by the body):", " ".join(f"{x:.4f}" for x in body))
        for r in rows:
            print(f"  e {r[0]:.1f} mm: L*a*b* {r[1]:6.2f} {r[2]:6.2f} {r[3]:6.2f}")
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", default="960x240")
    ap.add_argument("--spp", type=int, default=256)
    a = ap.parse_args()
    import fit as F
    fit = json.load(open(a.fit))
    mat = glaze.load()
    s = mat["samples"][fit["sample"]]
    lam = np.array(fit["lam"])
    g_star = mat["render"]["g_star"]["value"]
    depth = mat["render"]["max_depth"]["value"]
    ss = sum(np.array(fit["sigma_s"][k]) * (1 - np.array(fit["g"][k])) for k in fit["sigma_s"]) / (1 - g_star)
    sa = glaze.sigma_a(lam, fit["sample"], mat)
    rho0, t = fit["rho_body"], fit.get("body_t", 0.0)
    rho = F.body_rho(lam, rho0, t)
    nD = glaze.appen_nD(s["composition_wt"]["value"])[0]
    os.makedirs(a.out, exist_ok=True)
    P, N, T, UV = wedge(HX, HY, E0, E1, -0.05)
    if shell.watertight(P, T):
        raise SystemExit("card: the wedge is not closed")
    write_ply(os.path.join(a.out, "glaze.ply"), P, N, T, UV)
    w, h = (int(v) for v in a.res.split("x"))
    # the camera straight down; the frame 64 mm wide over the 60 mm wedge. One soft box (BOX): off the mirror
    # direction, so the frame shows no reflection of it
    dist = 400.0
    fov = 2 * math.degrees(math.atan(min(w, h) / max(w, h) * 32.0 / dist)) if w >= h else 0.0
    scene = f"""# Ru glaze thickness strip (materials/ru_glaze/card.py) from {os.path.relpath(a.fit, ROOT)}
LookAt 0 0 {dist} 0 0 0  0 1 0
Camera "perspective" "float fov" [ {fov:.6f} ]
Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]
Integrator "volpath" "integer maxdepth" [ {depth} ] "bool refractivenee" true
Film "rgb" "integer xresolution" [ {w} ] "integer yresolution" [ {h} ] "string filename" [ "raw.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true
WorldBegin
AttributeBegin
  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 1.0 ]
  Material "diffuse" "rgb reflectance" [ 0 0 0 ]
  Shape "bilinearmesh" "point3 P" [ {" ".join(f"{v:g}" for p in BOX for v in p)} ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" {spectrum_pbrt(lam, sa)} "spectrum sigma_s" {spectrum_pbrt(lam, ss)} "float g" [ {g_star} ] "float scale" [ 1 ]
AttributeBegin
  Material "diffuse" "spectrum reflectance" {spectrum_pbrt(lam, rho)}
  Shape "bilinearmesh" "point3 P" [ -200 -200 0 200 -200 0 -200 200 0 200 200 0 ] "integer indices" [ 0 1 2 3 ]
AttributeEnd
AttributeBegin
  MediumInterface "glaze" ""
  Material "dielectric" "float eta" [ {nD:.5f} ] "float roughness" [ {fit['alpha']} ] "bool remaproughness" false "bool refractivenee" true
  Shape "plymesh" "string filename" [ "glaze.ply" ]
AttributeEnd
"""
    with open(os.path.join(a.out, "scene.pbrt"), "w") as f:
        f.write(scene)
    with open(os.path.join(a.out, "card.json"), "w") as f:
        json.dump({"fit": os.path.relpath(a.fit, ROOT), "wedge_mm": [E0, E1], "half_mm": [HX, HY],
                   "frame_mm": 64.0, "res": [w, h], "g_star": g_star, "max_depth": depth, "body_rho0": rho0,
                   "body_t": t}, f, indent=1)
    print(f"wrote {a.out}/scene.pbrt (glaze n {nD:.4f}, g* {g_star}, maxdepth {depth}, body {rho0} t {t:.3f})")


if __name__ == "__main__":
    main()
