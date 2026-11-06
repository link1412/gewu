"""Shot 4: the shoulder of an old zisha teapot, pear-skin clay (梨皮), with the seam of the lid running in from the top.

    python3 -I v2/stills/s04_zisha.py [preview|mid|final]

Built like the real thing (all scales are estimates from general knowledge of the ware, not measured):
- a purple-brown clay matrix full of sand: particles of about 0.1-0.5 mm, most of them dark, some pale, a few black iron specks;
- burnished with a horn tool (明针) so that the particles are cut flat and level with the surface, with pores left between them;
- years of handling: an oily sheen, worn smoothest where the hand goes; fine scratches;
- a lid that fits in a dark seam about 0.15 mm wide, with a slightly knocked edge.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import Profile, fit_arc, grains, patch, project, reflect_light_loc, turned, view_dir, window

W = 6.0
PROF = Profile([(4.0, 0.0), (5.4, 1.0), (6.3, 3.0), (6.15, 5.0), (5.0, 6.8), (3.4, 7.9), (1.8, 8.5), (0.3, 8.72)], sigma=0.55)


def build(dens, box):
    u0, u1, v0, v1 = box
    pxcm = 600.0 * dens
    nx, ny = int((u1 - u0) * pxcm), int((v1 - v0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M")
    u = u0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = v0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)

    # --- sand in clay: three populations
    dd, rd, vd = grains(shape, pxcm, 2600, 0.0035, 0.018, 1, slope=-2.6)  # the dark, same-coloured body sand
    dp, rp, vp = grains(shape, pxcm, 900, 0.0035, 0.0135, 2, slope=-2.6)  # the pale sand: the pear skin
    df, rf, vf = grains(shape, pxcm, 90, 0.004, 0.020, 3, slope=-2.4)  # black iron specks
    # irregular outlines: particles are crushed rock, not beads
    wob = fbm(shape, pxcm, 0.002, 0.012, 1.2, 4)
    dd, dp, df = dd + 0.22 * wob, dp + 0.22 * np.roll(wob, 37, 0), df + 0.25 * np.roll(wob, 71, 1)
    md, mp, mf = sstep(1.0, 0.82, dd), sstep(1.0, 0.8, dp), sstep(1.0, 0.8, df)

    # --- pores and the pits where a particle has dropped out
    dq, rq, vq = grains(shape, pxcm, 520, 0.0018, 0.008, 5, slope=-2.8)
    pore = sstep(1.0, 0.55, dq + 0.25 * np.roll(wob, 11, 1)) * (1 - mp) * (1 - mf)

    # --- the wear of the hand: the surface nearest the palm is polished, the rest keeps its tooth
    wear = rank(fbm(shape, pxcm, 0.6, 5.0, 3.0, 6))
    wear = sstep(0.25, 0.85, wear)
    burn = fbm((max(ny // 2, 8), nx // 30 + 8), pxcm, 0.004, 0.08, 1.4, 7)  # horn strokes run around the shoulder
    burn = cv2.resize(burn, (nx, ny), interpolation=cv2.INTER_CUBIC)

    # --- height (cm): level burnished plane; the matrix sits a hair below the cut tops of the particles
    tooth = 1.0 - 0.75 * wear
    h = 0.0
    h = h + 0.0009 * tooth * sstep(0.0, 1.0, md) + 0.0022 * tooth * mp * (0.4 + 0.6 * rp / 0.013).clip(0, 1) + 0.0012 * tooth * mf
    h = h - 0.0032 * pore * (rq / 0.008).clip(0.4, 1) - 0.0003 * blur(fbm(shape, pxcm, 0.003, 0.02, 1.4, 8), 1.0)
    h = h + 0.00018 * burn * (1 - 0.6 * wear)
    # the hand-made form: slow, tiny undulation
    h = h + 0.006 * fbm(shape, pxcm, 2.5, 8.0, 3.8, 9)
    # a few old scratches, shallow and short
    rng = np.random.default_rng(10)
    sc = np.zeros(shape, np.float32)
    for _ in range(int((u1 - u0) * (v1 - v0) * 0.5)):
        p0 = np.array([rng.uniform(0, nx), rng.uniform(0, ny)])
        a = rng.normal(0.25, 0.6)
        L = rng.uniform(0.08, 0.5) * pxcm
        p1 = p0 + L * np.array([np.cos(a), np.sin(a)])
        cv2.line(sc, tuple((p0 * 8).astype(int)), tuple((p1 * 8).astype(int)), float(rng.uniform(0.3, 1.0)), 1, cv2.LINE_AA, shift=3)
    sc = blur(sc, 0.5)
    h = h - 0.0003 * sc

    # --- the lid: a step and a dark gap, with a little wander
    v_s = PROF.s_of_r(3.15)
    wander = 0.008 * fbm((8, nx), pxcm, 0.4, 3.0, 3.0, 11)[4] + 0.0022 * fbm((8, nx), pxcm, 0.03, 0.2, 2.2, 12)[4]
    dv = V - v_s - wander[None, :]
    edge_n = fbm(shape, pxcm, 0.006, 0.05, 1.6, 13)
    gap_w = 0.0095 + 0.003 * edge_n
    gap = sstep(1.0, 0.45, np.abs(dv) / gap_w)
    h = h - 0.075 * gap
    # lid stands a little proud, shoulder rolls in to meet it
    h = h + 0.012 * sstep(0.0, 0.05, dv) - 0.006 * np.exp(-(np.minimum(np.abs(dv), 0.2) / 0.05) ** 2) * (dv < 0)
    # edges of the gap are rounded by wear, with a few small chips
    chips = sstep(0.984, 0.994, rank(fbm(shape, pxcm, 0.012, 0.06, 1.8, 14))) * sstep(0.05, 0.012, np.abs(dv))
    h = h - 0.012 * blur(chips, 1.0)

    # --- color: linear. A deep purple-brown, a touch redder where it has been handled
    cloud = rank(fbm(shape, pxcm, 0.15, 1.5, 2.8, 15))
    base = mix(color([0.082, 0.027, 0.027]), color([0.118, 0.040, 0.034]), cloud)
    base = mix(base, color([0.125, 0.045, 0.034]), (0.5 * wear)[..., None])
    col = base * (0.86 + 0.28 * vd[..., None]) ** 1
    col = mix(base, col, md)
    # pale sand: from buff to a pinkish grey, each its own
    pale = mix(color([0.50, 0.30, 0.17]), color([0.36, 0.22, 0.17]), vp[..., None]) * (0.65 + 0.5 * vp[..., None])
    pale = pale * (0.86 + 0.14 * fbm(shape, pxcm, 0.002, 0.008, 1.2, 16)[..., None])
    col = mix(col, pale, mp * sstep(0.18, 0.5, vp + 0.2))
    col = mix(col, color([0.012, 0.009, 0.009]), mf)
    col = mix(col, color([0.014, 0.006, 0.005]), pore * 0.85)
    # grime in the seam and pores, the lived-in dark
    grime = sstep(0.08, 0.0, np.abs(dv))
    col = col * (1.0 - 0.45 * grime[..., None])
    col = mix(col, color([0.006, 0.003, 0.003]), gap)

    rough = 0.46 - 0.16 * wear + 0.05 * cloud + 0.05 * rank(burn) - 0.07 * mp + 0.1 * pore + 0.14 * gap
    # tiny glints: quartz and mica in the sand
    glint = (vd > 0.965) * md
    rough = rough * (1 - 0.15 * glint)

    P = turned(PROF, U, V, h)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.06, 1).astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.45, "mid": 0.7, "final": 1.0}[q]

    # coarse body for the framing
    uu = np.linspace(-16, 11, 600, dtype=np.float32)
    vv = np.linspace(2.0, PROF.L, 400, dtype=np.float32)
    Uc, Vc = np.meshgrid(uu, vv)
    Pc = turned(PROF, Uc, Vc)
    view = view_dir(0.0, 22.0)
    ROLL = 38.0
    cam, sag = fit_arc(Pc, view, W, 34.0, roll=ROLL)
    box = patch(PROF, cam, (-16, 11), (2.0, PROF.L - 0.25))
    print("box", box)

    P, C, Ro = build(dens, box)
    d = os.path.join(OUT, "s04_zisha")
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)

    # focus on the seam where it meets the frame's middle; find the seam's point nearest the frame centre
    vs = PROF.s_of_r(3.15)
    us = np.linspace(-9, 9, 800, dtype=np.float32)
    Ps = turned(PROF, us, np.full_like(us, vs))
    x, y, _ = project(cam, Ps)
    i = np.argmin((x - 0.5) ** 2 + (y - 0.62) ** 2)
    print("seam nearest", x[i], y[i])
    cam, sag = fit_arc(Pc, view, W, 34.0, roll=ROLL, aperture_mm=9.0, focus_point=Ps[i])

    # the window: where the shoulder below the arc mirrors towards
    Pm = Ps[i]
    nm = Pm * [1, 1, 0] / np.linalg.norm(Pm[:2])
    r_, z_, nr, nz = PROF.at(np.array([vs - 0.9]))
    th = us[i] / PROF.at(np.array([vs]))[0][0]
    pt = np.array([r_[0] * np.cos(th), r_[0] * np.sin(th), z_[0]])
    nrm = np.array([nr[0] * np.cos(th), nr[0] * np.sin(th), nz[0]])
    lw, rdir = reflect_light_loc(pt, nrm, cam, 42.0)
    print("window at", lw, "dir", rdir)
    lights = window("win", lw, pt, 13, 30, 1, 3, 1.2, 80, rgb=[1.0, 0.78, 0.60])
    lights += [
        {"name": "rake", "loc": (pt + np.array([-30, -22, 22])).tolist(), "target": pt.tolist(), "size": [4, 6], "watts": 17000, "rgb": [1.0, 0.86, 0.68]},
        {"name": "rim", "loc": (pt + np.array([-28, 14, 26])).tolist(), "target": pt.tolist(), "size": [30, 6], "watts": 3000, "rgb": [0.92, 0.95, 1.0]},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "pot", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.24}}],
        "lights": lights,
        "world": [0.0008, 0.0008, 0.001],
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s04_zisha", scene, q, develop={"exposure": 0.0, "contrast": 1.55, "saturation": 1.1, "black": 0.002, "grain": 1.2, "sharpen": 0.3, "halation": 0.03, "glare": 0.002})


main()
