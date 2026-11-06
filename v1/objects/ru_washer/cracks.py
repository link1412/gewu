"""The washer's crackle: grown crack by crack on the glaze's conformal map (crafts/crackle/crackle.py, the physics of
the cooling and later loads) and built as air films inside the glaze, for scene.py --cracks.

A piece of the same batch, not a copy (DESIGN 0): the network is this washer's own (its seed); what is the batch's is
the density, which the third load sets so the cells are as in the CMA photo (2-4 mm across, by eye on its
full-resolution crops [F]).

Two charts of the glaze's outer surface, each conformal (X = r0 (phi - phi0), Y = r0 integral ds / r; crackle.py
takes the scale r / r0 and keeps the physics in mm):
- out: the foot ring's face, the wall and the lip's outer half, over the front 216 deg (the back is not seen);
- in: the lip's inner half, the inner wall and the floor down to R_MIN, all the way round, the seam at the front
  (there the near rim hides it).

Two kinds of crack [D: Yang et al. 2012, OCT of celadon shards, as crafts/crackle/faces.py reads them]:
- generations 1 and 2, the network's big cells: deep, down to the body, leaning TILT_DEEP from the normal;
- the fine cracks, a second network in a near-surface layer (LAYER_MM thick: a shallow crack relaxes the stress
  over a length set by its own depth, so its spacing follows the layer, not the whole glaze [A]), over the first
  one (Jia Cui 2016's 「层叠」): shallow (DEPTH_FINE) and leaning far over (TILT_FINE): Yang find such
  shallow, strongly inclined cracks give a cloudy band over their reach; the air film under the thin wedge of glaze
  reflects (total internal reflection) what reaches it from above, on one side of the trace: the light edges.
Open everywhere (an air film: thindielectric, eta 1 / n_glaze); stains (传世) are not modelled.

    python3 -I objects/ru_washer/cracks.py --out out/ru/final/cracks --eta 1.5017 [--e0 0.6] [--seed 6] [--deform-seed N]
    python3 -I objects/ru_washer/cracks.py deform IN_DIR OUT_DIR SEED     # move an existing set with the form
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "crafts/crackle"))
import form as fm  # noqa: E402
import washer as wa  # noqa: E402
from crackle import DEFAULTS, Crackle  # noqa: E402

LOADS_DEEP = [[1.15, 1], [6.0, 2]]          # crackle.py's two loads (calibrated on Guan): the big cells, 4.3 mm
LOADS_FINE = [[1.15, 1], [6.0, 2], [60.0, 3]]
LAYER_MM = 0.3      # the shallow cracks' layer: its thickness sets their spacing (shear lag), 1.7 mm cells [F: the photo's]
TILT_DEEP = (10.0, 20.0)                     # deg [D]
TILT_FINE = (50.0, 65.0)                     # deg [D]
DEPTH_FINE = (0.08, 0.20)                    # mm [A]
R_MIN = 6.0                                  # mm: the floor's middle left out of the inner chart [A]
DU = 0.08                                    # mm along a trace
INSET = 0.015                                # mm kept from the glaze's surfaces (the meshes' chords cut in by < 0.01)


class Chart:
    """A conformal chart of a piece of the glaze's outer surface (object frame, mm, z up)."""

    def __init__(self, rz, nrm, e, r0, phi0):
        ds = np.hypot(*np.diff(rz, axis=0).T)
        keep = np.concatenate([[True], ds > 1e-9])
        rz, nrm, e = rz[keep], nrm[keep], e[keep]
        ds = np.hypot(*np.diff(rz, axis=0).T)
        r = rz[:, 0]
        t = np.concatenate([[0.0], np.cumsum(ds / (0.5 * (r[1:] + r[:-1])))])
        if t[-1] < 0:
            raise ValueError("chart: the profile must run with t increasing")
        self.t, self.r, self.z, self.n, self.e = t, r, rz[:, 1], nrm, e
        self.r0, self.phi0 = r0, phi0

    def y_range(self):
        return 0.0, float(self.t[-1] * self.r0)

    def at(self, Y):
        t = np.asarray(Y, float) / self.r0
        f = lambda a: np.interp(t, self.t, a)
        nr, nz = f(self.n[:, 0]), f(self.n[:, 1])
        k = np.hypot(nr, nz)
        return f(self.r), f(self.z), nr / k, nz / k, f(self.e)

    def scale(self, Y):
        return self.at(Y)[0] / self.r0

    def thickness(self, X, Y):
        return self.at(Y)[4] + 0.0 * np.asarray(X, float)

    def point(self, X, Y):
        r, z, nr, nz, e = self.at(Y)
        phi = self.phi0 + np.asarray(X, float) / self.r0
        c, s = np.cos(phi), np.sin(phi)
        return np.stack([r * c, r * s, z], -1), np.stack([nr * c, nr * s, nz], -1), e


def grow(chart, x_half, seed, raster, loads, layer=None):
    P = dict(DEFAULTS)
    y0, y1 = chart.y_range()
    e = layer or float(np.median(chart.e))
    P.update({"x_range": [-x_half, x_half], "y_range": [y0, y1], "raster_mm": raster, "glaze_mm": e, "e_ref_mm": e,
              "loads": loads, "seed": seed})
    thick = (lambda X, Y: np.full(np.shape(X), layer, float)) if layer else chart.thickness
    cr = Crackle(P, thick, chart.scale, np.random.default_rng(seed))
    cr.run([(float(l), int(g)) for l, g in P["loads"]])
    return [(c["gen"], np.asarray(c["pts"], float)) for c in cr.cracks if len(c["pts"]) >= 2]


def films(chart, cracks, rng):
    """The air films under the traces: quads (4 vertices each, normals from the winding)."""
    V, F = [], []
    for deep, pts in cracks:
        # resample at about DU of the surface's own length
        S, N, E = chart.point(pts[:, 0], pts[:, 1])
        seg = np.linalg.norm(np.diff(S, axis=0), axis=1)
        sl = np.concatenate([[0.0], np.cumsum(seg)])
        if sl[-1] < 2 * DU:
            continue
        u = np.linspace(0.0, sl[-1], max(int(sl[-1] / DU), 1) + 1)
        X, Y = np.interp(u, sl, pts[:, 0]), np.interp(u, sl, pts[:, 1])
        S, N, E = chart.point(X, Y)
        T = np.gradient(S, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        side = rng.choice([-1.0, 1.0])
        B = np.cross(N, T) * side                       # in the surface, across the trace: the side it leans to
        if deep:
            tilt = math.radians(rng.uniform(*TILT_DEEP))
            depth = E - 2 * INSET
        else:
            tilt = math.radians(rng.uniform(*TILT_FINE))
            depth = np.minimum(rng.uniform(*DEPTH_FINE), E - 2 * INSET)
        down = -N * math.cos(tilt) + B * math.sin(tilt)
        top = S - N * INSET
        bot = top + down * (np.broadcast_to(depth, len(S)) / math.cos(tilt))[:, None]
        for i in range(len(S) - 1):
            a, b, c, d = top[i], top[i + 1], bot[i + 1], bot[i]
            k = len(V)
            V.extend([a, b, c, d])
            F.extend([(k, k + 1, k + 2), (k, k + 2, k + 3)])
    V = np.asarray(V, float).reshape(-1, 3)
    F = np.asarray(F, np.int64).reshape(-1, 3)
    Q = V.reshape(-1, 4, 3)
    n = np.cross(Q[:, 1] - Q[:, 0], Q[:, 3] - Q[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-30
    Nv = np.repeat(n, 4, axis=0)
    return V, Nv, F


def read_ply(path):
    """washer.write_ply's binary PLY (no uv) -> (P, N, T)."""
    with open(path, "rb") as f:
        head = []
        while True:
            line = f.readline().decode().strip()
            head.append(line)
            if line == "end_header":
                break
        nv = int(next(h for h in head if h.startswith("element vertex")).split()[-1])
        nf = int(next(h for h in head if h.startswith("element face")).split()[-1])
        nprop = sum(1 for h in head if h.startswith("property float"))
        V = np.frombuffer(f.read(nv * nprop * 4), "<f4").reshape(nv, nprop).astype(float)
        face = np.frombuffer(f.read(nf * 13), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    return V[:, :3], V[:, 3:6], face["i"].astype(np.int64)


def deform_existing(d_in, d_out, seed):
    """A cracks.py output moved by washer.deviation(seed) (the films' normals from their winding)."""
    os.makedirs(d_out, exist_ok=True)
    P, N, T = read_ply(os.path.join(d_in, "gap.ply"))
    V, _ = wa.deform(P, N, wa.deviation(seed))
    Q = V.reshape(-1, 4, 3)
    n = np.cross(Q[:, 1] - Q[:, 0], Q[:, 3] - Q[:, 0])
    N = np.repeat(n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-30), 4, axis=0)
    wa.write_ply(os.path.join(d_out, "gap.ply"), V, N, T)
    for fn in ("cracks.pbrt", "cracks.json"):
        with open(os.path.join(d_in, fn)) as f, open(os.path.join(d_out, fn), "w") as g:
            g.write(f.read())
    info = json.load(open(os.path.join(d_out, "cracks.json")))
    info["deform_seed"] = seed
    json.dump(info, open(os.path.join(d_out, "cracks.json"), "w"), indent=1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "deform":       # cracks.py deform IN OUT SEED
        deform_existing(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--e0", type=float, default=0.6)
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--raster", type=float, default=0.1)
    ap.add_argument("--deform-seed", type=int, help="as scene.py's")
    ap.add_argument("--eta", type=float, required=True, help="the glaze's n (the glaze JSON's eta)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    _, _, rec, curves = wa.build(wa.thin_edges(a.e0), 0.0, 36)
    outer, lab = np.asarray(curves["outer"], float), np.asarray(curves["lab"])
    body = np.asarray(curves["body"], float)
    nrm = fm.normals(outer)
    e = np.linalg.norm(outer - body, axis=1)
    rng = np.random.default_rng(a.seed)
    # the lip's top: the highest point of the outer curve
    i_top = int(np.argmax(outer[:, 1]))
    i_face = int(np.nonzero(lab == "face")[0][0])
    i_floor = int(np.nonzero(lab == "floor")[0][-1])
    out_idx = np.arange(i_face, i_top + 1)                        # up the outside: t increasing
    in_idx = np.arange(i_floor, i_top - 1, -1)                     # from the floor's middle out and up the inside
    in_idx = in_idx[outer[in_idx, 0] >= R_MIN]
    charts = {"out": (Chart(outer[out_idx], nrm[out_idx], e[out_idx], 55.0, -math.pi / 2), 0.6 * math.pi * 55.0),
              "in": (Chart(outer[in_idx], nrm[in_idx], e[in_idx], 30.0, math.pi / 2), math.pi * 30.0)}
    allV, allN, allF, info = [], [], [], {}
    for k, (ch, xh) in charts.items():
        deep = grow(ch, xh, a.seed + 10 * (k == "in"), a.raster, LOADS_DEEP)
        fine = grow(ch, xh, a.seed + 10 * (k == "in") + 1, a.raster, LOADS_FINE, LAYER_MM)
        cr = [(True, p) for _, p in deep] + [(False, p) for _, p in fine]
        V, N, F = films(ch, cr, rng)
        allF.append(F + sum(len(v) for v in allV))
        allV.append(V)
        allN.append(N)
        info[k] = {"deep": len(deep), "fine": len(fine),
                   "quads": len(V) // 4, "y_range": ch.y_range(), "x_half": xh}
        print(k, info[k])
    V, N, F = np.vstack(allV), np.vstack(allN), np.vstack(allF)
    if a.deform_seed is not None:                    # the washer's own departure from the turned form (scene.py)
        V, _ = wa.deform(V, N, wa.deviation(a.deform_seed))
        Q = V.reshape(-1, 4, 3)
        n = np.cross(Q[:, 1] - Q[:, 0], Q[:, 3] - Q[:, 0])
        N = np.repeat(n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-30), 4, axis=0)
    wa.write_ply(os.path.join(a.out, "gap.ply"), V, N, F)
    frag = ["# the crackle's air films (objects/ru_washer/cracks.py), inside the glaze",
            "AttributeBegin", '  MediumInterface "glaze" "glaze"',
            f'  Material "thindielectric" "float eta" [ {1 / a.eta:.5f} ]',
            '  Shape "plymesh" "string filename" [ "gap.ply" ]', "AttributeEnd"]
    open(os.path.join(a.out, "cracks.pbrt"), "w").write("\n".join(frag) + "\n")
    json.dump({"seed": a.seed, "e0": a.e0, "deform_seed": a.deform_seed, "loads_deep": LOADS_DEEP, "loads_fine": LOADS_FINE, "layer_mm": LAYER_MM, "tilt_deep": TILT_DEEP, "tilt_fine": TILT_FINE,
               "depth_fine": DEPTH_FINE, "charts": info}, open(os.path.join(a.out, "cracks.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
