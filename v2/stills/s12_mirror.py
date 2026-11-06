"""Shot 12: the back of a Western Han 'light of the sun' bronze mirror (日光镜), rim and inscription band.

The inscription is the real formula of this mirror type: 見日之光 天下大明. Black-lacquer patina with
malachite, cuprite and soil. Glyph shapes come from a system font (STHeiti) as a stand-in for the Han script.

    python3 -I v2/stills/s12_mirror.py [preview|mid|final]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

from kit import OUT, blur, caps, color, fbm, frame_camera, mix, rank, shoot, sstep, warp

R, W, TAU = 7.0, 4.5, np.radians(30.0)
TEXT = "見日之光天下大明"
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"


def inscription(shape, pxcm, u0, v0, v_top, size, pitch, seed=3):
    """Raised glyph mask on the (u, v) raster, tops toward the rim."""
    ny, nx = shape
    S = 4
    font = ImageFont.truetype(FONT, int(size * pxcm * S))
    img = Image.new("L", (nx, int((v_top + size * 1.3 - v0) * pxcm) + 8), 0)
    rng = np.random.default_rng(seed)
    n = int((nx / pxcm) / pitch) + 2
    start = -(n // 2) * pitch + 0.14
    for i in range(n):
        ch = TEXT[(i + 2) % len(TEXT)]
        g = Image.new("L", (int(size * pxcm * S * 1.25),) * 2, 0)
        ImageDraw.Draw(g).text((int(0.08 * size * pxcm * S), 0), ch, font=font, fill=255)
        g = g.resize((g.width // S, g.height // S), Image.LANCZOS).rotate(float(rng.normal(0, 1.2)), Image.BICUBIC)
        x = int((start + i * pitch - u0 + rng.normal(0, 0.012)) * pxcm)
        y = int((v_top - v0 + rng.normal(0, 0.012)) * pxcm)
        img.paste(255, (x, y), g)
    out = np.zeros(shape, np.float32)
    a = np.asarray(img, np.float32) / 255.0
    h = min(a.shape[0], ny)
    out[:h] = a[:h]
    return out


def build(dens):
    pxcm = 411.0 * dens
    Lu, v0, v1 = 5.5, -0.08, 1.45
    nx, ny = int(Lu * pxcm), int((v1 - v0) * pxcm)
    shape = (ny, nx)
    px = lambda cm: cm * pxcm  # noqa: E731
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - Lu / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + v0
    U, V = np.meshgrid(u, v)

    # --- the casting -------------------------------------------------------------------------------------------
    rim_top = 0.075
    z = np.zeros(shape, np.float32)
    # broad plain rim, slightly convex, with a soft inner shoulder
    conv = 0.012 * (1.0 - ((V - 0.2) / 0.2) ** 2)
    z = np.where(V < 0.40, rim_top + conv, 0.0).astype(np.float32)
    z = blur(z, px(0.028))
    # outer wall
    z = z - (rim_top + 0.34) * sstep(0.035, -0.08, V)

    def ring(vc, width, h):
        return h * np.exp(-(((V - vc) / width) ** 4))

    z += ring(0.44, 0.016, 0.02) + ring(1.05, 0.014, 0.02) + ring(1.235, 0.016, 0.022)

    def comb(va, vb, pitch, seed):
        rng = np.random.default_rng(seed)
        wob = fbm(shape, pxcm, 0.1, 1.2, 2.5, seed) * 0.006
        t = (U + wob) / pitch
        idx = np.floor(t).astype(np.int32)
        idx -= idx.min()
        j1, j2, j3 = rng.random((3, idx.max() + 1))
        tooth = 0.5 + 0.5 * np.cos(2 * np.pi * (t - np.floor(t) - 0.5))
        a = sstep(0.42, 0.72, tooth)
        band = sstep(va - 0.012 + 0.018 * j1[idx], va + 0.004 + 0.018 * j1[idx], V) * sstep(vb + 0.012 - 0.018 * j2[idx], vb - 0.004 - 0.018 * j2[idx], V)
        return 0.024 * a * band * (0.7 + 0.5 * j3[idx])

    z += comb(0.46, 0.555, 0.040, 11) + comb(1.075, 1.20, 0.040, 12)
    z += ring(0.575, 0.011, 0.016)

    # inscription: rounded cast relief, partly lost
    mask = inscription(shape, pxcm, -Lu / 2, v0, 0.615, 0.40, 0.80)
    loss = 0.5 * fbm(shape, pxcm, 0.012, 0.25, 2.2, 21)
    inside = cv2.distanceTransform((mask + 0.18 * loss > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / pxcm
    glyph = np.minimum(inside / 0.012, 1.0) ** 0.7
    z += 0.03 * glyph.astype(np.float32)

    # the mould was not perfect and the pour was not either
    dx = fbm(shape, pxcm, 0.06, 0.9, 2.6, 31) * px(0.006)
    dy = fbm(shape, pxcm, 0.06, 0.9, 2.6, 32) * px(0.006)
    z_cast = warp(z, dx, dy)
    z_cast += 0.009 * fbm(shape, pxcm, 0.25, 3.0, 3.4, 33)

    # --- where the burial attacked -----------------------------------------------------------------------------
    n_lo = fbm(shape, pxcm, 0.25, 3.0, 3.0, 41)
    n_mid = fbm(shape, pxcm, 0.03, 0.35, 2.4, 42)
    n_hi = fbm(shape, pxcm, 0.005, 0.05, 2.0, 43)
    wx = fbm(shape, pxcm, 0.08, 0.8, 2.6, 44) * px(0.05)
    wy = fbm(shape, pxcm, 0.08, 0.8, 2.6, 45) * px(0.05)
    C = warp(0.7 * n_lo + 0.42 * n_mid, wx, wy)
    recess = np.clip((blur(z_cast, px(0.045)) - z_cast) / 0.012, 0.0, 1.0)
    ridge = np.clip((z_cast - blur(z_cast, px(0.06))) / 0.012, 0.0, 1.0)

    n_edge = fbm(shape, pxcm, 0.012, 0.12, 2.0, 46)
    F = rank(C) + 0.14 * recess - 0.30 * ridge + 0.055 * n_edge + 0.03 * n_hi
    crust = sstep(0.755, 0.775, F)
    thin = sstep(0.55, 0.76, F)  # the green stain that runs ahead of the crust
    halo = sstep(0.70, 0.755, F) * (1.0 - crust)  # cuprite shows at the crust's feet

    # grape-like growth, three generations
    grapes = blur(caps(shape, pxcm, 900, 0.008, 0.06, 51, mask=np.clip(crust + 0.08, 0, 1)), px(0.002)) * 0.30
    sand = caps(shape, pxcm, 9000, 0.002, 0.006, 52, mask=np.clip(crust + 0.05, 0, 1)) * 0.3
    n_micro = fbm(shape, pxcm, 0.0, 0.02, 1.6, 53)
    crust_soft = blur(crust, px(0.004))
    h_crust = crust_soft * (0.004 + 0.006 * rank(n_mid) + grapes + sand + 0.0006 * n_micro)

    # pits and pocks on the bare metal
    pits = caps(shape, pxcm, 90, 0.0018, 0.012, 61, mask=np.clip(rank(n_mid) - 0.2, 0, 1), slope=-2.8) * 0.3
    pocks = sstep(0.80, 0.93, rank(warp(fbm(shape, pxcm, 0.02, 0.2, 2.2, 62), wy, wx))) * sstep(0.3, 0.7, thin)
    h_metal = -pits - 0.003 * pocks - 0.0006 * pocks * n_micro

    # handling: fine scratches on whatever stayed metal, a light mottle
    rng = np.random.default_rng(71)
    sc = np.zeros(shape, np.uint8)
    for _ in range(int(nx * ny / pxcm**2 * 45)):
        x, y = rng.integers(0, nx), rng.integers(0, ny)
        a, l = rng.uniform(0, np.pi), rng.uniform(0.05, 0.9) * pxcm
        cv2.line(sc, (int(x), int(y)), (int(x + l * np.cos(a)), int(y + l * np.sin(a))), int(rng.integers(60, 255)), 1, cv2.LINE_AA)
    sc = sc.astype(np.float32) / 255.0
    h_metal = h_metal - 0.0005 * sc

    bare = 1.0 - crust_soft
    H = z_cast + h_crust + bare * h_metal

    # --- color ------------------------------------------------------------------------------------------------
    m1 = rank(fbm(shape, pxcm, 0.06, 1.5, 2.6, 81))
    m2 = rank(fbm(shape, pxcm, 0.012, 0.14, 2.0, 82))

    # black-lacquer patina with silver where the skin has thinned
    metal_col = mix(color([0.060, 0.056, 0.048]), color([0.44, 0.42, 0.36]), sstep(0.60, 1.0, m1)[..., None])
    metal_col = metal_col * (0.9 + 0.2 * m2[..., None])
    rough_m = 0.13 + 0.10 * (1 - m1) + 0.08 * m2 + 0.10 * thin + 0.35 * pocks + 0.10 * sc

    # the stain: dark translucent green over the metal
    stain_col = mix(color([0.012, 0.065, 0.048]), color([0.03, 0.14, 0.095]), m2[..., None])
    cuprite = mix(color([0.14, 0.022, 0.012]), color([0.30, 0.06, 0.025]), m2[..., None])

    # malachite: emerald to pale, with paler tips where it has dried and worn
    tip = np.clip(grapes / 0.03 + 0.5 * m2, 0.0, 1.0)
    depth = cv2.distanceTransform((crust > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / pxcm
    bands = 0.5 + 0.5 * np.sin(depth * 2 * np.pi / 0.022 + 2.2 * fbm(shape, pxcm, 0.02, 0.2, 2.2, 88))
    mal = mix(color([0.008, 0.055, 0.032]), color([0.035, 0.18, 0.105]), (0.45 * m1 + 0.55 * bands)[..., None])
    valley = sstep(0.0, 0.012, grapes + 0.4 * rank(n_mid) * 0.02)
    mal = mal * (0.45 + 0.55 * valley[..., None])
    mal = mix(mal, color([0.20, 0.36, 0.27]), (tip**3.5 * 0.5)[..., None])
    speck = (np.random.default_rng(91).random(shape, dtype=np.float32) ** 3)[..., None]
    mal = mal * (0.72 + 0.7 * speck)

    # azurite in a few pockets, soil in the low places
    az = sstep(0.975, 0.99, rank(fbm(shape, pxcm, 0.02, 0.2, 2.4, 92)))
    azurite = color([0.012, 0.06, 0.17]) * (0.7 + 0.8 * m2[..., None])
    soil_m = sstep(0.55, 0.85, recess + 0.5 * (rank(fbm(shape, pxcm, 0.02, 0.5, 2.4, 93)) - 0.5)) * sstep(0.45, 0.6, F)
    soil = mix(color([0.26, 0.20, 0.13]), color([0.50, 0.42, 0.30]), m2[..., None]) * (0.75 + 0.6 * speck)

    col = metal_col
    metal = np.ones(shape, np.float32)
    rough = rough_m.copy()

    def layer(c, m, r, mk):
        nonlocal col, metal, rough
        col = mix(col, c, mk[..., None])
        metal = metal * (1.0 - mk) + m * mk
        rough = rough * (1.0 - mk) + r * mk

    layer(stain_col, 0.25, 0.36, thin * 0.8)
    layer(cuprite, 0.0, 0.38, halo * 0.9)
    layer(mal, 0.0, 0.72, crust_soft)
    layer(azurite, 0.0, 0.7, crust_soft * az * 0.8)
    layer(soil, 0.0, 0.95, soil_m)

    # --- to 3D ------------------------------------------------------------------------------------------------
    # the edge is not a true circle after two thousand years: chips and lumps of crust
    rng = np.random.default_rng(101)
    e = fbm((8, nx), pxcm, 0.015, 1.2, 2.6, 102)[4]
    chips = 0.016 * e
    lumps = (h_crust * sstep(0.12, 0.0, V)) * 0.7
    r = R + chips - V + lumps
    th = np.pi / 2 - U / R
    P = np.stack([r * np.cos(th), r * np.sin(th), H], -1).astype(np.float32)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.03, 1).astype(np.float32), np.clip(metal, 0, 1).astype(np.float32), rim_top


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.6, "mid": 0.9, "final": 1.5}[q]
    P, C, Ro, M, rim = build(dens)
    d = os.path.join(OUT, "s12_mirror")
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro, metal=M)
    print("verts", P.shape[0] * P.shape[1])

    A = np.array([0.0, R, rim])
    up = np.array([0.0, np.cos(TAU), np.sin(TAU)])
    H_frame = W * 9.0 / 16.0
    # the arc's apex sits at (0.462, 0.58) of the frame
    target = A + up * (0.58 - 0.5) * H_frame + np.array([(0.5 - 0.462) * W, 0, 0])
    view = np.array([0.0, -np.sin(TAU), np.cos(TAU)])
    focus = A - up * 0.42
    cam = frame_camera(target, view, W, 24.0, aperture_mm=3.2, focus_point=focus)

    refl = np.array([0.0, np.sin(TAU), np.cos(TAU)])
    scene = {
        "camera": cam,
        "meshes": [{"name": "mirror", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": 0.5}}],
        "backdrop": {"center": [0, R, -7], "size": 160, "rgb": [0.00025, 0.00025, 0.00025]},
        "lights": [
            {"name": "key", "loc": (A - up * 0.8 + [-12, 8, 9]).tolist(), "target": (A - up * 0.8).tolist(), "size": [2.5, 2.5], "watts": 5000, "rgb": [1.0, 0.95, 0.88]},
            {"name": "sheen", "loc": (A + refl * 34 + [2, 1.5, 0]).tolist(), "target": A.tolist(), "size": [30, 3.5], "watts": 1500, "rgb": [0.95, 0.98, 1.0]},
            {"name": "fill", "loc": (A + [10, -22, 16]).tolist(), "target": A.tolist(), "size": [26, 26], "watts": 280, "rgb": [0.92, 0.96, 1.0]},
            {"name": "kick", "loc": (A + [6, 16, 1.5]).tolist(), "target": A.tolist(), "size": [10, 1.5], "watts": 500, "rgb": [1.0, 0.92, 0.82]},
        ],
    }
    shoot("s12_mirror", scene, q, develop={"exposure": 0.2, "contrast": 1.35, "saturation": 1.08, "black": 0.002, "grain": 1.2, "sharpen": 0.3})


main()
