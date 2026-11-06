"""Coat test, the scene: two coated tiles under one area light, camera straight above (docs/coats.md).
  tile A (y > 0): a white base (flat 0.8), a cobalt film (familymap of transmittances, materials/qinghua kappa)
     painted as three wide bands (c = 0.5, 1.5, 3 g/m^2), lines 0.2, 0.5, 1 and 2 mm wide (c = 3) and a step; a clear
     glaze (eta 1.52, smooth, 0.3 mm, no medium);
  tile B (y < 0): a familymap base (a made-up red pigment family, R = 0.85 exp(-c k(lambda)), k a step below 580 nm)
     ramped along x, under an absorbing coat (a made-up yellowish sigma_a, 0.3 mm, medium "lacquer");
  ref: the same light on a bare diffuse plate of reflectance 0.5 (the illumination, for the analytic comparison);
  thin: the coat scene with a 0.02 mm coat (base, film and surface): the same 1-D stack with almost no lateral walk,
     what a local layered BSDF with full recycling would give; the difference from "coat" is the walk.
The film and the familymap base are ours (pbrt as patched, docs/coats.md); everything else is pbrt-v4's.

    python3 -I tests/qinghua/gen_coat.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qh  # noqa: E402

sys.path.insert(0, os.path.join(qh.ROOT, "materials/qinghua"))
import optics  # noqa: E402
from coat import coat_medium, coated_tile, write_quad  # noqa: E402

RES = (960, 540)
EYE, TARGET, UP = (0, 0, 400), (0, 0, 0), (0, 1, 0)
FOV = 2 * np.degrees(np.arctan(18.0 / 400))         # 36 mm tall at the tile
H = 0.3                                              # coat thickness, mm
VARIANTS = {"coat": H, "thin": 0.02}                 # thin: the same stack with almost no room to walk sideways
ETA = 1.52
LIGHT = dict(center=(300 * np.cos(np.radians(50)), 0.0, 300 * np.sin(np.radians(50))), size=150.0, scale=40.0)
TILE_A = ((-40.0, 40.0), (0.5, 30.0))
TILE_B = ((-40.0, 40.0), (-30.0, -0.5))
MAP_PX_PER_MM = 25.6
BANDS = [(-30, -22, 0.5), (-20, -12, 1.5), (-10, -2, 3.0)]          # x0, x1, c (g CoO / m^2)
LINES = [(4.0, 0.2), (9.0, 0.5), (14.0, 1.0), (20.0, 2.0)]          # centre x, width; c = 3
STEP_X, C_LINE = 26.0, 3.0
PATTERN_Y = (8.0, 17.0)                                              # the painted rows; white below 6.5
C_FILM = np.round(np.arange(0.0, 6.0001, 0.05), 4)
C_BASE = np.linspace(0.0, 1.0, 11)
LAM = np.arange(360.0, 831.0, 2.0)


def red_family(c):
    k = 2.5 / (1 + np.exp((LAM - 580.0) / 15.0)) + 0.05
    return 0.85 * np.exp(-np.outer(c, k))


def lacquer_sigma_a():
    return 0.6 * np.exp(-(LAM - 400.0) / 60.0)          # 1/mm, made up: yellowish


def film_map():
    (x0, x1), (y0, y1) = TILE_A
    W, Hh = int(round((x1 - x0) * MAP_PX_PER_MM)), int(round((y1 - y0) * MAP_PX_PER_MM))
    x = x0 + (np.arange(W) + 0.5) / MAP_PX_PER_MM
    y = y1 - (np.arange(Hh) + 0.5) / MAP_PX_PER_MM               # row 0 the image's top = pbrt's t = 1 = v = 1 = y1
    row = np.zeros(W)
    for a, b, c in BANDS:
        row[(x >= a) & (x < b)] = c
    for xc, w in LINES:
        row[np.abs(x - xc) < w / 2] = C_LINE
    row[x >= STEP_X] = C_LINE
    m = np.zeros((Hh, W))
    on = (y >= PATTERN_Y[0]) & (y <= PATTERN_Y[1])
    m[on] = row
    return m


def base_map():
    (x0, x1), _ = TILE_B
    W = int(round((x1 - x0) * 8))
    u = (np.arange(W) + 0.5) / W
    return np.tile(np.clip((u - 0.1) / 0.8, 0, 1), (8, 1))         # c_base 0 at x < -32, 1 at x > 32


def header(spp, filename, rnee=True):
    t = qh.header(EYE, TARGET, FOV, RES, spp, UP, maxdepth=64, filename=filename)
    if rnee:
        t = t.replace('Integrator "volpath" "integer maxdepth" [ 64 ]',
                      'Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" true')
    return t


def build(d, spp=256):
    os.makedirs(d, exist_ok=True)
    k = optics.cobalt_kappa()
    np.savez(f"{d}/film.npz", lambda_nm=optics.LAM, c=C_FILM, R=optics.film_family(k, C_FILM))
    np.savez(f"{d}/red.npz", lambda_nm=LAM, c=C_BASE, R=red_family(C_BASE))
    write_quad(d)
    qh.write_pfm(f"{d}/film_c.pfm", film_map())
    qh.write_pfm(f"{d}/base_c.pfm", base_map())
    sa = np.stack([LAM, lacquer_sigma_a()], 1).ravel().tolist()
    lights = qh.light_quad(LIGHT["center"], -np.asarray(LIGHT["center"]), LIGHT["size"], LIGHT["scale"])
    def tiles(h):
        return ('Texture "co" "spectrum" "familymap" "string family" "film.npz" "string map" "film_c.pfm" "string wrap" "clamp"\n'
                'Texture "red" "spectrum" "familymap" "string family" "red.npz" "string map" "base_c.pfm" "string wrap" "clamp"\n'
                + coat_medium("lacquer", sa)
                + coated_tile(*TILE_A, z_base=-h, thickness=h, eta=ETA, alpha=0.0,
                              base='Material "diffuse" "spectrum reflectance" [ 360 0.8 830 0.8 ]',
                              film='Material "thindielectric" "float eta" [ 1 ] "texture transmittance" "co"')
                + coated_tile(*TILE_B, z_base=-h, thickness=h, eta=ETA, alpha=0.0, medium="lacquer",
                              base='Material "diffuse" "texture reflectance" "red"'))
    ref = ('AttributeBegin\n  Material "diffuse" "spectrum reflectance" [ 360 0.5 830 0.5 ]\n'
           + qh.quad((-40, -30, 0), (40, -30, 0), (-40, 30, 0), (40, 30, 0)) + "AttributeEnd\n")
    bodies = [(v, tiles(h)) for v, h in VARIANTS.items()] + [("ref", ref)]
    for var, body in bodies:
        open(f"{d}/{var}.pbrt", "w").write(header(spp, f"{var}_pbrt.exr") + lights + body)
        qh.rgbscene(f"{d}/{var}.pbrt", f"{d}/{var}.cycles.json")
    return d


if __name__ == "__main__":
    print(build(os.path.join(qh.OUT, "coat")))
