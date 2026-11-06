"""Shot 33: cinnabar (辰砂) crystals on white dolomite. The tops of the cluster make a rough arc.

    python3 -I v2/stills/s33_chensha.py [preview|mid|final]

Built like the real thing (crystal habit from general knowledge, scales estimated; there is no cinnabar photograph in ref/):
- each crystal is a true closed solid, the exact intersection of half-spaces: a rhombohedron (near-cube faces about the c axis, 52 degrees
  off it), some truncated by a flat basal face, some the penetration twins cinnabar is known for (two rhombohedra on one axis, turned 60
  degrees; here two overlapping solids, not one united solid). Every edge has a hair of a chamfer, which catches the light as a real edge does;
- a real medium: true refraction at n = 2.9 and absorption per channel, so the colour is the light that came through and the path it took,
  with total internal reflection making the dark and blazing facets. Absorption values are estimates (a deep vermilion at a few mm);
- at that index a facet is a mirror reflecting a quarter of what it sees: adamantine lustre. Most facets see black;
- a diffuse lobe under the mirror stands in for what scatters back from the crystal's inside, and a world that only refracted rays see stands
  in for all the light of a room reaching the crystal through its other faces;
- no two faces of a real crystal finish alike: each face has its own roughness, some mirror, some satin, and sharp growth steps run across it
  square to the crystal's c axis, as cinnabar's striations do. Roughness spread and step sizes are estimates;
- inside, a few veils: fracture planes and inclusion clouds, stand-ins as thin patchy sheets in the medium;
- a lens at about f/14, as a macro photograph without stacking would be: one crystal is sharp and the foreground falls away;
- the dolomite: small rhombic grains, each tilted its own way, stained red near the crystals.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.spatial import ConvexHull, HalfspaceIntersection

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, reflect_light_loc, view_dir

W = 4.4
SAG = 0.14
RA = W * (1 / (8 * SAG) + SAG / 2)
EL = 12.0
VIEW = view_dir(-90.0, EL)
EZ = VIEW / np.linalg.norm(VIEW)
EX = np.array([1.0, 0.0, 0.0])
EY = np.cross(EZ, EX)
DIST = 20.0
SEED = 33
TH = np.radians(52.0)


def y_arc(x):
    return -(x**2) / (2 * RA)


def z_rock(lift):
    """The rock's surface towards the camera: gentle under the cluster, then falling towards the lens so that the foreground goes soft."""
    return -0.5 + 0.45 * lift + 0.6 * np.maximum(lift - 0.75, 0.0) ** 1.5


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def rhomb_faces(rng, a, s, phi0, jitter=0.16, cap=None):
    """Half-spaces (n, d) of a rhombohedron about axis a, in the frame's (x, y, z-to-camera) coordinates."""
    u = unit(np.cross(a, [0.31, 0.77, 0.56]))
    v = np.cross(a, u)
    faces = []
    for k in range(3):
        p = phi0 + 2 * np.pi * k / 3
        faces.append((np.cos(TH) * a + np.sin(TH) * (np.cos(p) * u + np.sin(p) * v), s * rng.uniform(1 - jitter, 1 + jitter)))
        p2 = p + np.pi / 3
        faces.append((-np.cos(TH) * a + np.sin(TH) * (np.cos(p2) * u + np.sin(p2) * v), s * rng.uniform(1 - jitter, 1 + jitter)))
    if cap is not None:
        faces.append((a, s * cap))
    return faces


def layout():
    """All crystals as (centre, size, faces)."""
    rng = np.random.default_rng(SEED)
    out = []

    def add(x, y, z, s, cap=None, twin=None):
        a = unit([0.85 * x / RA + rng.normal(0, 0.38), 0.78 + rng.normal(0, 0.1), 0.56 + rng.normal(0, 0.3)])
        phi = rng.uniform(0, 2 * np.pi)
        c = np.array([x, y, z])
        if cap is None and rng.random() < 0.4:
            cap = rng.uniform(0.62, 0.92)
        out.append((c, s, rhomb_faces(rng, a, s, phi, cap=cap), a))
        if (rng.random() < 0.2) if twin is None else twin:
            out.append((c, s, rhomb_faces(rng, a, s * rng.uniform(0.93, 1.03), phi + np.pi / 3, cap=cap), a))

    # the back rank: its tips are the arc
    for x in np.arange(-3.0, 3.05, 0.33):
        x = x + rng.normal(0, 0.05)
        s = rng.uniform(0.11, 0.23)
        add(x, y_arc(x) - s * rng.uniform(1.0, 1.25), -0.52 + rng.normal(0, 0.05), s)
    # the middle rank
    for dy0, step in ((0.14, 0.42), (0.32, 0.5)):
        for x in np.arange(-3.0, 3.05, step):
            x = x + rng.normal(0, 0.08)
            s = rng.uniform(0.15, 0.3)
            add(x, y_arc(x) - s - dy0 * rng.uniform(0.8, 1.2), -0.4 + 0.45 * dy0 + rng.normal(0, 0.04), s)
    # the heroes, in front
    for x, dy, z, s, cap, twin in ((-0.82, 0.6, -0.08, 0.25, None, False), (0.36, 0.52, -0.04, 0.27, None, False), (1.42, 0.54, -0.12, 0.23, None, False), (-1.85, 0.52, -0.14, 0.21, None, False)):
        add(x, y_arc(x) - dy, z, s, cap, twin)
    # small ones scattered over the rock
    for _ in range(210):
        x = rng.uniform(-3.0, 3.0)
        y = y_arc(x) - rng.uniform(0.7, 1.75)
        add(x, y, float(z_rock(y_arc(x) - y)) + 0.012, rng.uniform(0.025, 0.11))
    return out


def solid(faces, eps):
    """Vertices and outward triangles of a convex solid around the origin, every edge and corner chamfered by eps."""
    A = np.array([n for n, _ in faces])
    b = np.array([d for _, d in faces])
    V = HalfspaceIntersection(np.c_[A, -b], np.zeros(3)).intersections
    extra_n, extra_d = [], []
    # a half-space between two faces: where they share an edge it cuts the edge, where they do not it cuts a corner. Both are wanted
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            m = A[i] + A[j]
            nm = np.linalg.norm(m)
            if nm < 0.25:
                continue
            m = m / nm
            extra_n.append(m)
            extra_d.append((V @ m).max() - eps)
    A2 = np.vstack([A, np.array(extra_n)])
    b2 = np.concatenate([b, np.array(extra_d)])
    V2 = HalfspaceIntersection(np.c_[A2, -b2], np.zeros(3)).intersections
    V2 = np.unique(np.round(V2, 7), axis=0)
    hull = ConvexHull(V2)
    F = hull.simplices.copy()
    # outward winding
    e = np.cross(V2[F[:, 1]] - V2[F[:, 0]], V2[F[:, 2]] - V2[F[:, 0]])
    flip = (e * hull.equations[:, :3]).sum(1) < 0
    F[flip] = F[flip][:, ::-1]
    used, inv = np.unique(F, return_inverse=True)
    return V2[used], inv.reshape(F.shape)


def crystals_mesh():
    rng = np.random.default_rng(SEED + 1)
    Vs, axes, frs, fss = [], [], [], []
    picks = []
    frame = np.stack([EX, EY, EZ], 1)  # frame coordinates to world
    for c, s, faces, a in layout():
        V, F = solid(faces, float(np.clip(0.016 * s, 0.0008, 0.006)) * rng.uniform(0.6, 1.5))
        A = np.array([n for n, _ in faces])
        # each true face its own finish; most are bright, some satin, a few dull
        kind = rng.random(len(A))
        fr_face = np.where(kind < 0.6, rng.uniform(0.003, 0.012, len(A)), np.where(kind < 0.88, rng.uniform(0.02, 0.05, len(A)), rng.uniform(0.06, 0.14, len(A))))
        fs_face = rng.uniform(0.0, 1.0, len(A)) ** 3
        tri = V[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        dots = n @ A.T
        which = dots.argmax(1)
        on_face = dots.max(1) > 0.9995
        fr = np.where(on_face, fr_face[which], 0.05)  # an edge is slightly worn
        fs = np.where(on_face, fs_face[which], 0.0)
        # triangles do not share vertices, so that each can carry its face's values
        Vs.append((frame @ (tri.reshape(-1, 3) + c).T).T)
        axes.append(np.tile(frame @ a, (tri.shape[0] * 3, 1)))
        frs.append(np.repeat(fr, 3))
        fss.append(np.repeat(fs, 3))
        for nn, d in faces:
            if nn[2] > 0.45 and abs(c[0]) < 1.9 and s > 0.15:
                picks.append((s * nn[2], frame @ (c + nn * d), frame @ nn, c[0]))
    print("crystals", len(Vs), "tris", sum(len(v) for v in Vs) // 3, flush=True)
    V = np.concatenate(Vs).astype(np.float32)
    F = np.arange(len(V), dtype=np.int32).reshape(-1, 3)
    return V, F, np.concatenate(axes).astype(np.float32), np.concatenate(frs).astype(np.float32), np.concatenate(fss).astype(np.float32), picks


def veils_mesh():
    """Thin irregular sheets inside the larger crystals. They stay within 0.75 s of the centre, and every face is at least 0.84 s away."""
    rng = np.random.default_rng(SEED + 7)
    frame = np.stack([EX, EY, EZ], 1)
    Vs, Fs = [], []
    base = 0
    for c, s, _, _ in layout():
        if s < 0.1:
            continue
        for _ in range(rng.integers(1, 4)):
            nrm = unit(rng.normal(0, 1, 3))
            u = unit(np.cross(nrm, rng.normal(0, 1, 3)))
            v = np.cross(nrm, u)
            th = np.linspace(0, 2 * np.pi, 18, endpoint=False)
            r = s * 0.5 * rng.uniform(0.45, 1.0, 18)
            o = c + unit(rng.normal(0, 1, 3)) * s * 0.25
            ring = o + (r * np.cos(th))[:, None] * u + (r * np.sin(th))[:, None] * v
            ring += nrm * rng.normal(0, 0.03 * s, 18)[:, None]
            P = np.vstack([o, ring])
            Vs.append((frame @ P.T).T)
            Fs.append(np.stack([np.full(18, base), base + 1 + np.arange(18), base + 1 + (np.arange(18) + 1) % 18], 1))
            base += 19
    return np.concatenate(Vs).astype(np.float32), np.concatenate(Fs).astype(np.int32)


def rock(dens):
    pxcm = 700.0 * dens
    X0, X1 = -2.9, 2.9
    Y0, Y1 = -1.9, 0.34
    nx, ny = int((X1 - X0) * pxcm), int((Y1 - Y0) * pxcm)
    shape = (ny, nx)
    xs = X0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    ys = Y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(xs, ys)
    arc = y_arc(X)
    lift = arc - Y
    edge = 0.26 + 0.06 * fbm(shape, pxcm, 0.1, 0.8, 2.5, SEED + 3)
    here = lift > edge
    rng2 = np.random.default_rng(SEED + 2)
    n_seed = int((X1 - X0) * (Y1 - Y0) / 0.03**2)
    seeds = np.ones(shape, np.uint8)
    seeds[rng2.integers(0, ny, n_seed), rng2.integers(0, nx, n_seed)] = 0
    _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    lab = lab.astype(np.int64)
    # DIST_LABEL_PIXEL numbers the zero pixels in scan order, from 1
    zy, zx = np.nonzero(seeds == 0)
    n_lab = zy.size + 1
    cx = np.concatenate([[0.0], xs[zx]]).astype(np.float32)
    cy = np.concatenate([[0.0], ys[zy]]).astype(np.float32)
    tx = rng2.normal(0, 0.12, n_lab).astype(np.float32)
    ty = rng2.normal(0, 0.12, n_lab).astype(np.float32)
    off = rng2.normal(0, 0.003, n_lab).astype(np.float32)
    val = rng2.uniform(0, 1, n_lab).astype(np.float32)
    grain = blur(tx[lab] * (X - cx[lab]) + ty[lab] * (Y - cy[lab]) + off[lab], max(0.003 * pxcm, 0.5))  # grains meet without a gap: a hard step between them drew cracks in dried mud
    Zb = z_rock(lift) + 0.05 * fbm(shape, pxcm, 0.15, 1.2, 2.8, SEED + 4) + grain + 0.002 * fbm(shape, pxcm, 0.005, 0.03, 1.6, SEED + 5)
    # a red stain around each crystal's foot
    st = np.zeros(shape, np.uint8)
    for c, s, *_ in layout():
        cv2.circle(st, (int((c[0] - X0) * pxcm), int((c[1] - Y0) * pxcm)), max(int(s * pxcm), 1), 255, -1)
    stain = blur(st.astype(np.float32) / 255.0, 0.05 * pxcm)
    ivory = mix(color([0.62, 0.6, 0.53]), color([0.9, 0.88, 0.8]), val[lab])
    vein = rank(fbm(shape, pxcm, 0.03, 0.6, 2.4, SEED + 6))
    ivory = mix(ivory, color([0.34, 0.3, 0.24]), sstep(0.8, 0.97, vein) * 0.3)
    col = mix(ivory, color([0.32, 0.035, 0.02]), np.clip(stain * 0.42, 0, 0.42))
    rough = 0.28 + 0.34 * val[lab]
    P = X[..., None] * EX.astype(np.float32) + Y[..., None] * EY.astype(np.float32) + Zb[..., None] * EZ.astype(np.float32)
    return P.astype(np.float32), np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.02, 1).astype(np.float32), here.astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.55, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, "s33_chensha")
    os.makedirs(d, exist_ok=True)
    xa = np.linspace(-2.75, 2.75, 300)
    Pc = np.concatenate([xa[..., None] * EX + (y_arc(xa) - dy)[..., None] * EY + (-0.5 * EZ) for dy in (0.0, 0.5, 1.0, 1.6)], 0)
    focus = np.array(0.42 * EX + (y_arc(0.42) - 0.3) * EY + 0.2 * EZ)
    cam, sag = fit_arc(Pc, VIEW, W, DIST, aperture_mm=6.0, focus_point=focus)
    V, F, Ax, Fr, Fs, picks = crystals_mesh()
    npc = os.path.join(d, "mesh.crystals.npz")
    np.savez(npc, V=V, F=F, axis=Ax, fr=Fr, fs=Fs)
    Vv, Fv = veils_mesh()
    npv = os.path.join(d, "mesh.veils.npz")
    np.savez(npv, V=Vv, F=Fv)
    P, C, Ro, A = rock(dens)
    npr = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npr, P=P, col=C, rough=Ro, alpha=A)
    # windows: on a few large facets spread across the frame; everything else sees black or the sky
    picks.sort(key=lambda t: -t[0])
    top = sorted(picks[14:46], key=lambda t: t[3])  # not the largest faces: a window on a big face reads as a sheet of metal
    lights = []
    for i, k in enumerate((1, 12, 22)):
        _, p, n, _ = top[k]
        loc, _ = reflect_light_loc(p, n, cam, 30.0)
        lights.append({"type": "gradient", "name": f"win{i}", "loc": loc.tolist(), "target": p.tolist(), "size": [6, 6], "sigma": [0.5, 0.5], "L": 1.5, "rgb": [1.0, 0.98, 0.95]})
    lights.append({"name": "key", "loc": (EZ * 18 + EY * 22 - EX * 14).tolist(), "target": (-EY * 0.7).tolist(), "size": [10, 10], "watts": 3000, "rgb": [1.0, 0.95, 0.88], "hide_in_gloss": True})
    lights.append({"type": "gradient", "name": "sky", "loc": (EZ * 10 + EY * 34).tolist(), "target": [0, 0, 0], "size": [70, 70], "sigma": [24, 24], "L": 0.09, "rgb": [1.0, 0.98, 0.96]})
    # a soft box to the right, clear of the key (a gradient light is a real panel and casts a shadow): the faces turned its way carry a slow gradient, not a white sheet
    lights.append({"type": "gradient", "name": "sheen", "loc": (EZ * 20 + EY * 6 + EX * 16).tolist(), "target": [0, 0, 0], "size": [18, 18], "sigma": [5, 5], "L": 0.14, "rgb": [1.0, 0.97, 0.93]})
    # the light that goes through: a large soft source behind and above, out of frame. Refraction at 2.9 sends the rays all over, so some facets find it
    lights.append({"type": "gradient", "name": "back", "loc": (-EZ * 16 + EY * 14).tolist(), "target": [0, 0, 0], "size": [60, 20], "sigma": [20, 8], "L": 12.0, "rgb": [1.0, 0.95, 0.9], "hide_in_gloss": True, "hide_in_diffuse": True})
    lights.append({"type": "gradient", "name": "under", "loc": (EZ * 6 - EY * 16).tolist(), "target": [0, 0, 0], "size": [50, 16], "sigma": [16, 6], "L": 3.0, "rgb": [1.0, 0.95, 0.9], "hide_in_gloss": True, "hide_in_diffuse": True})
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "crystals", "npz": npc, "shader_py": os.path.join(os.path.dirname(os.path.abspath(__file__)), "gem_shader.py"), "params": {"ior": 2.9, "sigma_a": [0.32, 9.0, 12.0], "wave": 0.0012, "terrace": 0.00008, "body_mix": 0.22, "body": [0.72, 0.012, 0.008]}},
            {"name": "veils", "npz": npv, "shader_py": os.path.join(os.path.dirname(os.path.abspath(__file__)), "gem_shader.py"), "params": {"veil": 0.75, "veil_scale": 22.0, "tint": [0.95, 0.42, 0.34]}},
            {"name": "rock", "npz": npr, "material": {"Base Color": "col", "Roughness": "rough", "Alpha": "alpha"}},
        ],
        "lights": lights,
        "world": [3.0, 3.0, 2.9],
        "world_refraction_only": True,
        "bounces": 44,
        "transmission_bounces": 32,
        "glossy_bounces": 32,
        "diffuse_bounces": 2,
        "clamp_indirect": 12.0,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }
    shoot("s33_chensha", scene, q, develop={"exposure": 0.25, "contrast": 1.25, "saturation": 1.06, "black": 0.0012, "grain": 1.15, "sharpen": 0.3, "halation": 0.05, "glare": 0.004, "vignette": 0.3})


main()
