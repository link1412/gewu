"""断纹: shrinkage cracks in a lacquer layer. A lacquer film keeps shrinking as it oxidises and its substrate (wood)
moves; the film cracks through to a dark ground (Han et al. 2023 [I]: cracking appears with light aging, its width,
length and number set by the formulation). Modelled as straight-ish V cracks (duanwen.json): Poisson count per
100 cm^2, lognormal length, depth, width; on a round piece optionally radial (as on the CMA dish, by eye [M]).
A new piece: none.

    cracks(shape, step, x, y, P, rng) -> (bump mm <= 0, mask, log)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "carving"))
import carve  # noqa: E402


def load():
    return json.load(open(os.path.join(HERE, "duanwen.json")))


def cracks(shape, step, x, y, P, rng):
    bump = np.zeros(shape)
    area = (x[-1] - x[0]) * (y[-1] - y[0]) / 1e4
    n = int(rng.poisson(P["per_100cm2"] * area)) if P["per_100cm2"] > 0 else 0
    log = []
    for _ in range(n):
        c = rng.uniform([x[0], y[0]], [x[-1], y[-1]])
        L = rng.lognormal(math.log(P["len_mm"]), 0.5)
        a = math.atan2(c[1], c[0]) if P["radial"] else rng.uniform(0, math.pi)
        a += rng.normal(0, 0.15)
        k = max(int(L / 0.5), 2)
        t = np.linspace(-0.5, 0.5, k + 1)[:, None] * L
        wig = np.cumsum(rng.normal(0, 0.05, (k + 1, 1)), axis=0)       # a crack wanders a little
        d = np.array([math.cos(a), math.sin(a)]); nrm = np.array([-d[1], d[0]])
        Pl = c + t * d + wig * nrm
        i0 = max(int((Pl[:, 0].min() - x[0] - P["width_mm"]) / step), 0)
        i1 = min(int((Pl[:, 0].max() - x[0] + P["width_mm"]) / step) + 2, shape[1])
        j0 = max(int((Pl[:, 1].min() - y[0] - P["width_mm"]) / step), 0)
        j1 = min(int((Pl[:, 1].max() - y[0] + P["width_mm"]) / step) + 2, shape[0])
        if i1 <= i0 or j1 <= j0:
            continue
        X, Y = np.meshgrid(x[i0:i1], y[j0:j1])
        r = carve.dist_polyline(Pl, X, Y)
        cut = -np.maximum(0, P["depth_mm"] * (1 - r / (P["width_mm"] / 2)))
        bump[j0:j1, i0:i1] = np.minimum(bump[j0:j1, i0:i1], cut)
        log.append([round(float(c[0]), 1), round(float(c[1]), 1), round(float(L), 1)])
    return bump, bump < -1e-4, log
