"""Dust and grime (积灰): settles where wiping does not reach. A wiping cloth's finest fold is a ball of radius
`corner_radius_mm` pressed from above; dust lies where the surface is more than `min_depth_mm` below that ball's
envelope (the concave corners: the foot of walls, the bottom of narrow grooves), and in open cracks (a mask from
crafts/duanwen) when `in_cracks`. Its colour is its own body reflectance (dust.json). A new piece: none.

    mask(h, step, cracks, P) -> bool
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "wear"))
import wear  # noqa: E402


def load():
    return json.load(open(os.path.join(HERE, "dust.json")))


def mask(h, step, cracks, P):
    if not P["on"]:
        return np.zeros(h.shape, bool)
    m = wear.gap(h, step, P["corner_radius_mm"], coarse=2) > P["min_depth_mm"]
    if cracks is not None and P["in_cracks"]:
        m |= cracks
    return m
