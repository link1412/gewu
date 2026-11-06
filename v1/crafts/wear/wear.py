"""Wear (磨损) and scratching (划痕): mechanical processes on a surface, with physical parameters (wear.json).
No 'age' knob: a piece's state is its parameters; a new piece has them all at zero (docs/layers.md).

Rubbing (handling, wiping):
- edge rounding: arrises and points are worn round to `edge_radius_mm` (grey opening of the height field with a ball);
- touch: a rubbing body of radius `touch_radius_mm` (a cloth-covered fingertip) pressed from above reaches the
  surface where its envelope (the grey closing with that ball) meets it; `touch_reach_mm` is how far below the
  envelope a compliant cloth still reaches (e-fold). Touch E (0..1) = exp(-(envelope - h) / reach).
  Where touched, the surface is the rubbed surface (GGX `rubbed_alpha`), elsewhere what the other processes left.
Scratching: straight fine V-scratches, Poisson count per cm^2, lognormal length, the roughness inside a scratch
  at least `scratch_alpha`.

    gap(h, step, radius_mm)               -> depth below a pressed ball's envelope
    touch(h, step, P[, gap])              -> E
    round_edges(h, step, P)               -> h
    scratches(shape, step, P, rng)        -> (bump mm <= 0, mask, n)
"""
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "carving"))
import carve  # noqa: E402


def load():
    return json.load(open(os.path.join(HERE, "wear.json")))


def _ball(radius_mm, step):
    n = int(math.ceil(radius_mm / step))
    yy, xx = np.mgrid[-n:n + 1, -n:n + 1] * step
    rr = radius_mm * radius_mm - xx * xx - yy * yy
    fp = rr >= 0
    return fp, np.where(fp, np.sqrt(np.maximum(rr, 0)) - radius_mm, 0.0)


def round_edges(h, step, P):
    r = P["edge_radius_mm"]
    if r <= 0:
        return h
    fp, ball = _ball(r, step)
    return ndi.grey_opening(h, footprint=fp, structure=ball)


def gap(h, step, radius_mm, coarse=4):
    """Depth (mm, >= 0) of the surface below the envelope of a ball of radius_mm pressed from above (grey closing).
    Done on a grid `coarse` times coarser: the ball is mm-sized, the envelope smooth on that scale."""
    hc = ndi.zoom(h, 1 / coarse, order=1)
    fp, ball = _ball(radius_mm, step * coarse)
    env = ndi.grey_closing(hc, footprint=fp, structure=ball)
    env = ndi.zoom(env, (h.shape[0] / hc.shape[0], h.shape[1] / hc.shape[1]), order=1)[:h.shape[0], :h.shape[1]]
    return np.maximum(env - h, 0)


def touch(h, step, P, g=None):
    """Touch E in 0..1 (0 everywhere when the piece was never rubbed: touch_radius_mm = 0)."""
    if P["touch_radius_mm"] <= 0:
        return np.zeros_like(h)
    g = gap(h, step, P["touch_radius_mm"]) if g is None else g
    return np.exp(-g / max(P["touch_reach_mm"], 1e-6))


def scratches(shape, step, P, rng):
    if P["scratch_per_cm2"] <= 0:
        return np.zeros(shape), np.zeros(shape, bool), 0
    b, n = carve.scratches(shape, step, P["scratch_per_cm2"], P["scratch_len_mm"], P["scratch_depth_um"],
                           P["scratch_width_mm"], rng)
    return b, b < -1e-4, n
