"""Shot 13: the top of an old qin (古琴) with its crackle (断纹): snake-belly bands, silk strings and a
mother-of-pearl stud (徽). The swell of the soundboard is the arc.

    python3 -I v2/stills/s13_guqin.py [preview|mid|final]

Built like the real thing (scales are estimates from general knowledge, not measured):
- the lacquer fractured in order: long cracks across the board first (蛇腹断), then shorter ones between them that stop at the
  first in a T, then hairlines: a sequence, not a Voronoi diagram;
- every plate of lacquer is its own rigid piece, tilted a fraction of a degree and curled up at its edges (剑锋), so the
  reflection of the window breaks from plate to plate. This is what makes old lacquer read;
- under the black is ash lacquer (鹿角灰) and a trace of vermilion, seen only in the crack and where the plates wore thin;
- the strings are twisted silk, a real helix of strands; the stud is a shell disc let into the lacquer.
The crack pattern is ours and is not a copy of any instrument.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import fit_arc, project, reflect_light_loc, view_dir

W = 13.0
RU, RV = 21.0, 70.0  # the swell of the board across and along, cm
VIEW = view_dir(-90.0 + 15.0, 13.0)  # from the tail end, a little to one side, low
DIST = 46.0
U0, U1, V0, V1 = -7.0, 12.5, -8.0, 24.0
SEED = 13


def surface(U, V, h=0.0):
    """The board, y running away from the tail. Isometric enough for this small a curvature."""
    z = -(U**2) / (2 * RU) - (V - 6.0) ** 2 / (2 * RV)
    nx, ny = U / RU, (V - 6.0) / RV
    n = 1.0 / np.sqrt(1.0 + nx**2 + ny**2)
    return np.stack([U + h * nx * n, V + h * ny * n, z + h * n], -1).astype(np.float32)


def wander(rng, t, amp, waves):
    """A smooth 1-D wobble: sum of a few sines with random phases."""
    out = np.zeros_like(t)
    for k in waves:
        out = out + rng.normal(0, 1) * np.sin(t * k + rng.uniform(0, 6.3))
    return amp * out / np.sqrt(len(waves))


def crack_lines():
    """All cracks as polylines in cm: (points, half width). Drawn in the order they break."""
    rng = np.random.default_rng(SEED)
    lines = []
    # primary: long and across the board, as the belly scales of a snake; spacing wanders
    vs = [V0]
    while vs[-1] < V1:
        vs.append(vs[-1] + float(rng.lognormal(np.log(0.62), 0.26)))
    uu = np.linspace(U0, U1, 800)
    prim = []
    for v0 in vs:
        tilt = rng.normal(0, 0.05)
        vv = v0 + tilt * uu + wander(rng, uu, 0.13, (0.35, 0.7, 1.3)) + wander(rng, uu, 0.035, (3.1, 5.3, 8.7)) + wander(rng, uu, 0.014, (19.0, 31.0, 47.0))
        prim.append(vv)
        # most of them run the width of the board; some die out
        a, b = 0, len(uu)
        if rng.random() < 0.3:
            a = int(rng.uniform(0, 0.55) * len(uu))
        if rng.random() < 0.3:
            b = int(rng.uniform(0.45, 1.0) * len(uu))
        if b - a > 40:
            lines.append((np.stack([uu[a:b], vv[a:b]], 1), float(rng.uniform(0.005, 0.0105))))
    # secondary: between two primaries, along the board, stopping in a T
    for i in range(len(prim) - 1):
        u = U0 + rng.uniform(0, 1.0)
        while u < U1:
            u += float(rng.lognormal(np.log(0.55), 0.55))
            if u >= U1:
                break
            u1 = u + rng.normal(0, 0.13)
            j0, j1 = np.searchsorted(uu, u), np.searchsorted(uu, u1)
            if not (0 <= j0 < len(uu) and 0 <= j1 < len(uu)):
                continue
            p0, p1 = np.array([u, prim[i][j0]]), np.array([u1, prim[i + 1][j1]])
            n = max(int(np.linalg.norm(p1 - p0) * 90), 8)
            t = np.linspace(0, 1, n)[:, None]
            pts = p0 + (p1 - p0) * t
            env = np.sin(np.pi * t[:, 0])
            pts[:, 0] += env * (wander(rng, t[:, 0], 0.07, (5.0, 9.0)) + wander(rng, t[:, 0], 0.016, (31.0, 53.0)))
            # some stop short: the crack has not arrived yet
            stop = n if rng.random() < 0.72 else int(n * rng.uniform(0.35, 0.8))
            lines.append((pts[:stop], float(rng.uniform(0.0034, 0.007))))
    # tertiary: hairlines (牛毛断), mostly across
    for _ in range(2600):
        c = np.array([rng.uniform(U0, U1), rng.uniform(V0, V1)])
        L = float(rng.lognormal(np.log(0.42), 0.5))
        a = rng.normal(0, 0.4) if rng.random() < 0.8 else rng.uniform(0, np.pi)
        n = max(int(L * 70), 5)
        t = np.linspace(-0.5, 0.5, n)
        pts = np.stack([c[0] + L * t * np.cos(a), c[1] + L * t * np.sin(a)], 1)
        pts[:, 1] += wander(rng, t, 0.018, (9.0, 21.0))
        lines.append((pts, float(rng.uniform(0.0022, 0.004))))
    return lines


def build(dens, stud):
    pxcm = 170.0 * dens
    nx, ny = int((U1 - U0) * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    u = U0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = V0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)

    canvas = np.zeros(shape, np.uint8)
    hair = np.zeros(shape, np.uint8)
    all_lines = crack_lines()
    for pts, hw in all_lines:
        ip = np.round(np.stack([(pts[:, 0] - U0) * pxcm, (pts[:, 1] - V0) * pxcm], 1) * 16).astype(np.int32)
        th = max(1, int(round(2 * hw * pxcm)))
        if hw < 0.0045:
            cv2.polylines(hair, [ip], False, 255, th, cv2.LINE_AA, shift=4)
        else:
            cv2.polylines(canvas, [ip], False, 255, th, cv2.LINE_AA, shift=4)
    crack = canvas.astype(np.float32) / 255.0
    hairl = hair.astype(np.float32) / 255.0

    # distance from a crack, the plates between them, and a rigid tilt per plate
    dist = cv2.distanceTransform((canvas < 90).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm
    n, lab = cv2.connectedComponents((canvas < 90).astype(np.uint8), connectivity=4)
    print("plates", n, flush=True)
    area = np.bincount(lab.ravel(), minlength=n).astype(np.float64) + 1
    cu = (np.bincount(lab.ravel(), U.ravel(), minlength=n) / area).astype(np.float32)
    cv_ = (np.bincount(lab.ravel(), V.ravel(), minlength=n) / area).astype(np.float32)
    rng = np.random.default_rng(SEED + 2)
    tx, ty = rng.normal(0, 0.0022, n).astype(np.float32), rng.normal(0, 0.0022, n).astype(np.float32)
    tz = rng.normal(0, 0.0005, n).astype(np.float32)
    shade = rng.normal(0, 1, n).astype(np.float32)
    plate = tx[lab] * (U - cu[lab]) + ty[lab] * (V - cv_[lab]) + tz[lab]

    # --- height: slow waves of old lacquer, plates, curled edges (剑锋), the grooves themselves
    slow = fbm(shape, pxcm, 0.5, 5.0, 3.0, SEED + 3)
    pits = fbm(shape, pxcm, 0.02, 0.12, 1.4, SEED + 4)
    wear = rank(fbm(shape, pxcm, 0.3, 4.0, 2.8, SEED + 5))
    curl = np.exp(-dist / 0.03)
    h = 0.0045 * slow + plate + 0.0016 * curl - 0.0045 * blur(crack, max(0.8 * dens, 0.5)) - 0.0018 * blur(hairl, 0.5) + 0.00022 * pits

    # --- colour, linear: nearly black, brown where worn thin, ash and a trace of vermilion in the crack
    black = mix(color([0.0065, 0.0052, 0.0048]), color([0.016, 0.0105, 0.0078]), rank(blur(shade[lab], 1.5) + 0.8 * slow))
    thin = sstep(0.68, 0.98, wear) * (0.45 + 0.55 * curl)
    col = mix(black, color([0.06, 0.028, 0.014]), thin * 0.55)
    red = sstep(0.5, 0.85, rank(fbm(shape, pxcm, 0.12, 1.1, 2.3, SEED + 6)))
    under = mix(color([0.17, 0.135, 0.11]), color([0.3, 0.05, 0.022]), red)
    col = mix(col, under, blur(crack, 0.6) * 0.72)
    col = mix(col, under * 0.5, blur(hairl, 0.5) * 0.5)
    # dust in the deep of the cracks
    rough = 0.085 + 0.09 * wear + 0.2 * blur(crack, 0.8) + 0.03 * sstep(-1, 1.5, pits)

    # --- the stud: a shell disc let into the lacquer
    d = np.hypot(U - stud[0], V - stud[1])
    disc = sstep(0.385, 0.375, d)
    if disc.any():
        ang = np.arctan2(V - stud[1], U - stud[0])
        wob = fbm(shape, pxcm, 0.03, 0.5, 2.0, SEED + 7)
        growth = (V - stud[1]) * 5.2 + 0.35 * np.sin(ang * 2 + 0.7) + 0.5 * wob
        tints = [0.5 + 0.5 * np.cos(2 * np.pi * (growth * k + o)) for k, o in ((1.0, 0.0), (1.13, 0.22), (1.3, 0.55))]
        pearl = 0.46 + 0.42 * np.stack(tints, -1)
        col = mix(col, pearl.astype(np.float32), disc)
        rough = rough * (1 - disc) + 0.14 * disc
        h = h * (1 - disc) + disc * (0.0012 * np.cos(growth * 6.28) * 0.3 - 0.002) - 0.016 * np.exp(-(((d - 0.38) / 0.01) ** 2))

    P = surface(U, V, h)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32), disc.astype(np.float32)


def string_mesh(u0, height, radius, dens, seed):
    """Twisted silk: a helix of strands around a core, along the board."""
    rng = np.random.default_rng(seed)
    v = np.linspace(-22.0, 34.0, int(56 * 130 * dens), dtype=np.float32)
    a = np.linspace(0, 2 * np.pi, 56, dtype=np.float32)
    V_, A = np.meshgrid(v, a, indexing="ij")
    strands = 6
    pitch = 0.85  # one turn of the strands, cm
    twist = strands * (A + 2 * np.pi * V_ / pitch)
    wool = 0.05 * fbm(V_.shape, 40.0, 0.05, 0.6, 1.6, seed + 1)
    bump = np.abs(np.cos(twist * 0.5)) ** 0.6
    R = radius * (0.86 + 0.14 * bump + wool)
    u_c = u0 + 0.004 * V_
    # strings under tension are straight: the board swells up towards them, they do not follow it
    base = -(u_c**2) / (2 * RU) + 0.012 * (V_ - 6.0)
    P = np.stack([u_c + R * np.cos(A), V_, base + height + R * np.sin(A)], -1).astype(np.float32)
    silk = 0.5 + 0.5 * np.sin(twist * 4.0 + 4.0 * rng.random())
    col = mix(color([0.5, 0.31, 0.13]), color([0.72, 0.52, 0.27]), (0.35 * silk + 0.65 * bump).astype(np.float32))
    # flagged: the lights do not reach the far part of the strings, which would otherwise cross the black above the board
    lit = sstep(25.0, 14.0, V_).astype(np.float32)
    col = col * lit[..., None]
    return P, np.clip(col, 0, 1).astype(np.float32), lit


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.6, "mid": 0.8, "final": 1.0}[q]
    d = os.path.join(OUT, "s13_guqin")
    os.makedirs(d, exist_ok=True)
    uu, vv = np.linspace(U0, U1, 500, dtype=np.float32), np.linspace(V0, V1, 700, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = surface(Uc, Vc)
    nrm = np.stack([Uc / RU, (Vc - 6.0) / RV, np.ones_like(Uc)], -1)
    keep = (nrm @ VIEW) > -0.005
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST)
    x, y, _ = project(cam, Pc.reshape(-1, 3))
    x, y = x.reshape(Uc.shape), y.reshape(Uc.shape)
    bad = 10 * (~keep)
    k = np.nanargmin(((x - 0.5) ** 2 + (y - 0.63) ** 2) + bad)
    focus = Pc.reshape(-1, 3)[k]
    cam, sag = fit_arc(Pc[keep], VIEW, W, DIST, aperture_mm=7.0, focus_point=focus)
    s = np.nanargmin(((x - 0.71) ** 2 + (y - 0.69) ** 2) + bad)
    stud = (float(Uc.flat[s]), float(Vc.flat[s]))
    print("focus", focus, "stud", stud, flush=True)

    P, C, Ro, disc = build(dens, stud)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=disc * 0.5)
    meshes = [{"name": "board", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": 0.5}}]
    for i, (ux, hgt, r) in enumerate(((focus[0] - 2.3, 0.62, 0.062), (focus[0] - 0.4, 0.58, 0.052), (focus[0] + 1.5, 0.54, 0.044))):
        Ps, Cs, lit = string_mesh(ux, hgt, r, dens, SEED + 20 + i)
        sp = os.path.join(d, f"str{i}.{q}.npz")
        np.savez(sp, P=Ps, col=Cs, spec=0.4 * lit, sheen=0.6 * lit)
        meshes.append({"name": f"str{i}", "npz": sp, "material": {"Base Color": "col", "Roughness": 0.42, "Sheen Weight": "sheen", "Specular IOR Level": "spec"}})

    # a window the board mirrors along the top of the swell: the reflection is what breaks across the plates
    j = np.nanargmin(((x - 0.47) ** 2 + (y - 0.575) ** 2) + bad)
    pw = Pc.reshape(-1, 3)[j]
    nw = nrm.reshape(-1, 3)[j]
    lw, _ = reflect_light_loc(pw, nw, cam, 70.0)
    lights = [
        {"type": "gradient", "name": "window", "loc": lw.tolist(), "target": pw.tolist(), "size": [170, 90], "sigma": [36, 4.5], "L": 1.0, "rgb": [1.0, 0.95, 0.87]},
        {"name": "rake", "loc": (focus + np.array([-44, 22, 9])).tolist(), "target": focus.tolist(), "size": [8, 8], "watts": 15000, "rgb": [1.0, 0.9, 0.74]},
        {"name": "fill", "loc": (focus + np.array([28, -30, 24])).tolist(), "target": focus.tolist(), "size": [30, 30], "watts": 3600, "rgb": [0.95, 0.97, 1.0], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 2,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s13_guqin", scene, q, develop={"exposure": 0.0, "contrast": 1.3, "saturation": 1.05, "black": 0.0012, "grain": 1.2, "sharpen": 0.3, "halation": 0.04, "glare": 0.003, "vignette": 0.4})


main()
