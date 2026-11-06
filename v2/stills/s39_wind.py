"""The flower opens a little, for s39_cand.py. Nothing here renders. (The file keeps its name: it began as wind, and that was turned down.)

The petals themselves move, and nothing else does: the camera, the head, the stem and the leaves all stand still. Whatever moves on the screen is a petal.

Each petal turns outward about its base, flattens its cup a little, and its tip curls back a little. Outer whorls start first and inner ones follow. Each petal has its own start and its own size of move, so the flower does not scale like a rigid body. Every quantity is one eased one-way ramp: no way back, no rebound, no tremble. At the end of the take the ramps are still running.

A real lotus opens over hours. This is that motion much sped up, not a time-lapse measured off a plant: every number in ARG is ESTIMATED, set so that a tip travels about 1.5 % of the frame by frame 20 and 2.5 % by frame 36. Not simulated: growth, petal against petal contact (outer whorls lead, so the gaps open and do not close).
"""

import numpy as np

ARG = {
    "t0": -0.55, "dur": 2.6, "stagger": 0.07, "jit": 0.035,
    "flap": 3.4, "bend": 3.1, "tip": 3.3, "cup": 0.07, "twist": 0.5, "edge": 0.05, "gain_j": 0.2,
    "seed": 39,
}


def ease(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


class Sim:
    def __init__(self, specs, leaves, flowers, a=None):
        self.a = dict(ARG, **(a or {}))
        self.specs = specs
        self.nl, self.nf = len(leaves), len(flowers)

    def run(self, film_times):
        a = self.a
        ts = np.asarray(film_times)
        n = len(ts)
        r = np.random.default_rng(a["seed"])
        expo = np.array([s["expo"] for s in self.specs])  # the whorl: 0.16 in the heart to 1 outside
        np_ = len(self.specs)
        order = (1.0 - expo) / 0.84  # 0 outside, 1 in the heart
        start = a["t0"] + a["stagger"] * 5.0 * order + r.uniform(-a["jit"], a["jit"], np_)
        U = ease((ts[None, :] - start[:, None]) / (a["dur"] * r.uniform(0.94, 1.06, np_))[:, None])
        size = (0.72 + 0.28 * expo) * np.exp(r.normal(0, a["gain_j"], np_))

        def part(g, jit=0.2):
            return U * (g * size * np.exp(r.normal(0, jit, np_)))[:, None]

        self.pet = {
            "flap": part(a["flap"]),
            "bend": part(a["bend"]),
            "tip": part(a["tip"]),
            "cup": part(a["cup"]),
            "twist": part(a["twist"] * r.uniform(-1, 1, np_)),
            "edges": [U * (a["edge"] * 0.5**m * size)[:, None] * r.uniform(0.6, 1.2, (np_, 1)) for m in range(2)],
        }
        self.U = U
        zero = np.zeros(n)
        self.head = {"x": zero, "n": zero, "y": zero, "w": zero, "U": U.mean(0)}
        self.leaf = {"sway": np.zeros((self.nl, n)), "tx": np.zeros((self.nl, n)), "ty": np.zeros((self.nl, n)), "wave": np.zeros((self.nl, n)), "ph": np.zeros(self.nl)}
        self.far = {"sway": np.zeros((self.nf, n))}
        return self

    def petal_args(self, i, k, s):
        """The arguments of Mesh.pose for petal i at sample k. The margins roll out a little, in one fixed shape that only grows."""
        p = self.pet
        e = sum(q[i, k] * (0.6 + 0.4 * np.sin((m + 1) * np.pi * s + i)) for m, q in enumerate(p["edges"]))
        return dict(flap=float(p["flap"][i, k]), bend=float(p["bend"][i, k]), tip=float(p["tip"][i, k]), twist=float(p["twist"][i, k]), cup=float(p["cup"][i, k]), el=e, er=e)

    def head_move(self, P, k, pivot=None):
        return P
