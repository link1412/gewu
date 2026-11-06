"""Deposition (沉积): material carried into the cracks and onto the surface, with its parameters in deposition.json.

- crack deposit: iron corrosion products with quartz and clay in the cracks (Wu et al. 2025), as the chance that a
  cell of a crack face is filled, cover(depth) = c0 erfc(depth / L) (diffusion down the crack from the mouth), and
  the deposit's reflectance spectrum, an intimate (Hapke) mixture of a measured iron oxide spectrum and a white
  matrix;
- burial stain blotches on the surface: materials/guan_glaze/glaze.stain_levels (excavated pieces only).

    deposit_spectrum(f)  -> pbrt's interleaved [lambda, value, ...] list
    cover(c0, L)         -> function depth_mm -> chance
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    return json.load(open(os.path.join(HERE, "deposition.json")))


def _w(r):
    g = (1 - r) / (1 + r)
    return 1 - g * g


def _r(w):
    g = np.sqrt(np.clip(1 - w, 0, 1))
    return (1 - g) / (1 + g)


def deposit_spectrum(f, A=None, matrix=None, mineral=None):
    """Reflectance of the deposit with iron oxide share f (0..1) in the matrix (deposition.json, 'spectrum'); matrix:
    the matrix's own reflectance (flat), default deposition.json's; mineral: 'goethite', or the default
    lepidocrocite ('iron_oxide')."""
    A = A or load()
    sp = A["crack_deposit"]["spectrum"]
    v = np.array(sp["goethite" if mineral == "goethite" else "iron_oxide"]["lambda_nm_value"], float)
    lam, r_fe = v[0::2], v[1::2]
    r_m = np.full_like(r_fe, sp["matrix_white"]["value"] if matrix is None else matrix)
    r = _r(f * _w(r_fe) + (1 - f) * _w(r_m))
    return [float(x) for pair in zip(lam, np.round(r, 5)) for x in pair]


def fill_spectrum(dep, A=None):
    """The fill's reflectance for a state's deposit: its own fitted spectrum ('reflectance_nm', interleaved), or the
    Hapke mixture of an iron oxide (share f, 'mineral') in a flat matrix ('matrix')."""
    if dep.get("reflectance_nm"):
        return [float(x) for x in dep["reflectance_nm"]]
    return deposit_spectrum(dep["f"], A, matrix=dep.get("matrix"), mineral=dep.get("mineral"))


def cover(c0, L):
    if c0 <= 0:
        return None
    return lambda depth: c0 * math.erfc(depth / L)
