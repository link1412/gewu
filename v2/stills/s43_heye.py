"""Shot 43: water on a lotus leaf (荷叶水珠). The rim of the leaf is the arc; the beads are real refractive water.

    python3 -I v2/stills/s43_heye.py [preview|mid|final]

Built like the real thing (scales are estimates from general knowledge, not measured):
- a lotus leaf is a shallow funnel of radiating veins that fork towards the rim, with a wavy rim; the top is a velvet of wax
  papillae, which is why it looks matte and silvery and why water stands up on it;
- back light through the green blade, so the veins read as a darker network with a pale line;
- the beads are capillary drops: small ones nearly spheres, large ones flattened by gravity (capillary length 2.7 mm); real
  glass-like water with IOR 1.33 in Cycles, resting on an air film, so each holds the whole world upside down.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 10.0
R = 11.0  # the swell of the leaf near the rim, seen from just above
VIEW = view_dir(-90.0, 16.0)
DIST = 40.0
U0, U1, V0, V1 = -8.5, 8.5, -6.0, 9.0
SEED = 43


def height0(U, V):
    return -(U**2) / (2 * R) - (V - 2.0) ** 2 / (2 * 19.0)


def surface(U, V, h=0.0):
    z = height0(U, V)
    nx, ny = U / R, (V - 2.0) / 19.0
    n = 1.0 / np.sqrt(1.0 + nx**2 + ny**2)
    return np.stack([U + h * nx * n, V + h * ny * n, z + h * n], -1).astype(np.float32)


def veins(shape, pxcm, c):
    """Radiating, forking veins from a far centre: returns the mask of the vein network (0-1)."""
    rng = np.random.default_rng(SEED)
    ny, nx = shape
    canvas = np.zeros(shape, np.float32)
    # the centre of the leaf is far below the frame; veins radiate from it towards the rim, forking twice
    centre = np.array([c[0], c[1] - 16.0])
    for a0 in np.radians(np.arange(-26.0, 27.0, 8.2)):
        a0 = a0 + rng.normal(0, 0.012)
        stack = [(centre + np.array([np.sin(a0), np.cos(a0)]) * 7.0, a0, 0.05, 0)]
        while stack:
            p, a, hw, gen = stack.pop()
            L = float(rng.uniform(6.0, 9.0)) if gen == 0 else float(rng.uniform(3.2, 5.5))
            n = int(L * 12)
            pts = [p]
            for _ in range(n):
                a = a + rng.normal(0, 0.012)
                pts.append(pts[-1] + np.array([np.sin(a), np.cos(a)]) * (L / n))
            pts = np.array(pts)
            ip = np.round(np.stack([(pts[:, 0] - U0) * pxcm, (pts[:, 1] - V0) * pxcm], 1) * 16).astype(np.int32)
            for i in range(0, n, 2):
                t = i / n
                th = max(1, int(round(2 * hw * (1.0 - 0.45 * t) * pxcm)))
                cv2.line(canvas, tuple(int(q) for q in ip[i]), tuple(int(q) for q in ip[min(i + 2, n)]), 1.0, th, cv2.LINE_AA, shift=4)
            if gen < 3:
                d = float(rng.uniform(0.2, 0.3))
                stack.append((pts[-1], a - d, hw * 0.62, gen + 1))
                stack.append((pts[-1], a + d, hw * 0.62, gen + 1))
    return canvas


def bead_list(c):
    """Beads as (u, v, radius in cm). Placed by hand so that the picture has one big jewel and a family around it."""
    rng = np.random.default_rng(SEED + 1)
    big = [(c[0] - 0.55, c[1] + 0.2, 0.46), (c[0] + 1.75, c[1] + 0.95, 0.23), (c[0] - 2.75, c[1] + 1.2, 0.17), (c[0] + 0.72, c[1] - 1.05, 0.13), (c[0] + 3.3, c[1] - 0.15, 0.11)]
    out = list(big)
    for _ in range(90):
        u, v = rng.uniform(U0 + 1, U1 - 1), rng.uniform(c[1] - 5.0, c[1] + 6.5)
        r = float(np.exp(rng.uniform(np.log(0.018), np.log(0.07))))
        if all(np.hypot(u - b[0], v - b[1]) > b[2] + r + 0.05 for b in out):
            out.append((u, v, r))
    return out


def drop_profile(b, angle=np.radians(158.0), lc=0.27):
    """The shape of a resting drop: the Young-Laplace equation integrated from the crown (Bashforth-Adams) down to the contact
    angle of a lotus leaf. b is the radius of curvature at the crown, lc the capillary length of water, in cm."""
    ds = b / 400.0
    x, z, phi = 0.0, 0.0, 0.0
    xs, zs = [0.0], [0.0]
    for _ in range(40000):
        k = 2.0 / b + z / lc**2 - (np.sin(phi) / x if x > 1e-9 else 1.0 / b)
        phi += k * ds
        x += np.cos(phi) * ds
        z += np.sin(phi) * ds
        xs.append(x)
        zs.append(z)
        if phi >= angle:
            break
    return np.array(xs), np.array(zs)


def bead_mesh(beads, dens):
    """Each drop a closed surface of revolution from the profile; the contact patch closes it, on a thin film of air."""
    meshes = []
    for u, v, r in beads:
        xs, zs = drop_profile(r)
        xs, zs = np.r_[xs, np.linspace(xs[-1], 0.0, 24)[1:]], np.r_[zs, np.full(23, zs[-1])]
        L = np.r_[0.0, np.cumsum(np.hypot(np.diff(xs), np.diff(zs)))]
        res = int(np.clip(1300 * r * dens, 48, 420))
        t = np.linspace(0, L[-1], res)
        X, Z = np.interp(t, L, xs).astype(np.float32), np.interp(t, L, zs).astype(np.float32)
        ph = np.linspace(0, 2 * np.pi, res * 2, dtype=np.float32)
        Xg, Ph = np.meshgrid(X, ph, indexing="ij")
        Zg = np.broadcast_to(Z[:, None], Xg.shape)
        z0 = float(height0(np.array(u), np.array(v))) + 0.006 + float(zs[-1])
        P = np.stack([u + Xg * np.cos(Ph), v + Xg * np.sin(Ph), z0 - Zg], -1).astype(np.float32)
        meshes.append(P)
    return meshes


def net(shape, pxcm, seed):
    """The fine reticulate veins between the big ones: cell walls around scattered seeds, about 3 mm across."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    n = int(nx * ny / pxcm**2 / 0.09)
    seeds = np.ones(shape, np.uint8)
    seeds[rng.integers(0, ny, n), rng.integers(0, nx, n)] = 0
    _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    wall = ((lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1))).astype(np.float32)
    return blur(wall, max(0.9 * dens_global, 0.6))


dens_global = 1.0


def build(dens, c, beads):
    global dens_global
    dens_global = dens
    pxcm = 200.0 * dens
    nx, ny = int((U1 - U0) * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    u = U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = V0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)
    vein = veins(shape, pxcm, c)
    vs = blur(vein, max(1.2 * dens, 0.6))

    # the velvet: wax papillae, too small to resolve one by one except under a loupe, seen as a soft silver bloom
    pap = fbm(shape, pxcm, 0.008, 0.03, 0.9, SEED + 3)
    cells = fbm(shape, pxcm, 0.05, 0.25, 1.4, SEED + 4)
    quilt = fbm(shape, pxcm, 0.5, 2.2, 3.0, SEED + 5)
    big = fbm(shape, pxcm, 1.0, 6.0, 2.6, SEED + 6)
    # the blade is quilted between the veins
    between = blur(vein, 0.25 * pxcm)
    h = 0.012 * quilt - 0.03 * sstep(0, 0.6, between) * 0.5 + 0.018 * vs + 0.0012 * cells + 0.0006 * pap

    fine = net(shape, pxcm, SEED + 8)
    fine = np.clip(fine / (np.percentile(fine, 99.5) + 1e-6), 0, 1)
    h = h + 0.0022 * fine
    green = mix(color([0.018, 0.1, 0.016]), color([0.04, 0.2, 0.024]), rank(0.7 * big + 0.5 * cells))
    green = mix(green, color([0.09, 0.2, 0.05]), 0.5 * vs)
    col = green * (1.0 + 0.12 * pap[..., None])
    # back light through the blade: it glows, the veins hold it back
    glow = mix(color([0.12, 0.36, 0.022]), color([0.27, 0.56, 0.035]), rank(big + 0.4 * quilt))
    glow = glow * ((1.0 - 0.6 * vs) * (1.0 - 0.3 * fine) * (0.85 + 0.15 * sstep(-1, 1, cells)))[..., None]
    # the bright caustic that each drop throws into its own shadow, away from the sun
    sun = np.array([-30.0, 46.0, 38.0])
    away = -sun[:2] / np.linalg.norm(sun[:2])
    for bu, bv, br in beads:
        if br < 0.05:
            continue
        hb = -drop_profile(br)[1].max()
        reach = abs(hb) * sun[2] ** -1 * np.linalg.norm(sun[:2]) * 0.72
        cu, cv = bu + away[0] * reach, bv + away[1] * reach
        spot = np.exp(-(((U - cu) ** 2 + (V - cv) ** 2) / (2 * (0.2 * br) ** 2)))
        glow = glow + (spot * 26.0)[..., None] * color([1.0, 0.97, 0.75])
    P = surface(U, V, h)
    return P, np.clip(col, 0, 1).astype(np.float32), glow.astype(np.float32), glow[..., 1].astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s43_heye")
    os.makedirs(d, exist_ok=True)
    uu, vv = np.linspace(U0, U1, 500, dtype=np.float32), np.linspace(V0, V1, 500, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = surface(Uc, Vc)
    nrm = np.stack([Uc / R, (Vc - 2.0) / 19.0, np.ones_like(Uc)], -1)
    keep = (nrm @ VIEW) > -0.005
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Uc.shape), y.reshape(Uc.shape)
    bad = 10 * (~keep)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.68) ** 2) + bad)
    c = (float(Uc.flat[k]), float(Vc.flat[k]))
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=9.0, focus_point=focus)
    print("focus", focus, "c", c, flush=True)

    beads = bead_list(c)
    P, C, G, T = build(dens, c, beads)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, glow=G, trans=T)
    meshes = [{"name": "leaf", "npz": npz, "material": {"Base Color": "col", "Roughness": 0.62, "Specular IOR Level": 0.2, "Sheen Weight": 0.45, "Sheen Roughness": 0.5, "Emission Color": "glow", "Emission Strength": 0.26}}]
    for i, Pb in enumerate(bead_mesh(beads, dens)):
        bp = os.path.join(d, f"b{i}.{q}.npz")
        np.savez(bp, P=Pb)
        meshes.append({"name": f"b{i}", "npz": bp, "material": {"Base Color": [1.0, 1.0, 1.0], "Roughness": 0.0, "Transmission Weight": 1.0, "IOR": 1.33, "Specular IOR Level": 0.5}})

    # the sky is what water shows: a big soft window high behind the leaf, mirrored and refracted by every bead
    j = np.nanargmin(((x - 0.5) ** 2 + (y - 0.56) ** 2) + bad)
    pw = Pc.reshape(-1, 3)[j]
    nw = nrm.reshape(-1, 3)[j]
    lw, _ = reflect_light_loc(pw, nw, cam, 60.0)
    lights = [
        {"type": "gradient", "name": "sky", "loc": lw.tolist(), "target": pw.tolist(), "size": [190, 150], "sigma": [64, 26], "L": 0.6, "rgb": [0.92, 0.96, 1.0]},
        {"name": "sun", "loc": (focus + np.array([-30, 46, 38])).tolist(), "target": focus.tolist(), "size": [8, 8], "watts": 30000, "rgb": [1.0, 0.93, 0.8]},
        {"name": "fill", "loc": (focus + np.array([20, -40, 30])).tolist(), "target": focus.tolist(), "size": [50, 50], "watts": 2200, "rgb": [0.9, 0.95, 1.0], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 2,
        "glossy_bounces": 6,
        "transmission_bounces": 12,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }
    shoot("s43_heye", scene, q, develop={"exposure": 0.0, "contrast": 1.34, "saturation": 1.12, "black": 0.0012, "grain": 1.15, "sharpen": 0.28, "halation": 0.05, "glare": 0.004, "vignette": 0.55})


main()
