"""Closed-form checks of crafts/carving/carve.py and the cinnabar lacquer family.

    python3 -I tests/carving/test_carve.py
"""
import math
import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "crafts/carving"))
sys.path.insert(0, os.path.join(ROOT, "materials/cinnabar_lacquer"))
import carve  # noqa: E402
import lacquer  # noqa: E402

FAIL = []


def check(name, got, want, tol):
    ok = abs(got - want) <= tol
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {got:.5g} (want {want:.5g} +- {tol:g})")
    if not ok:
        FAIL.append(name)


def at(rel, x, y):
    return rel.h[int(round((y - rel.y0) / rel.step)), int(round((x - rel.x0) / rel.step))]


def test_sdf():
    X, Y = np.meshgrid(np.linspace(-3, 3, 61), np.linspace(-3, 3, 61))
    sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float)
    d = carve.sdf_polygon(sq, X, Y)
    want = np.where((np.abs(X) <= 1) & (np.abs(Y) <= 1), np.minimum(1 - np.abs(X), 1 - np.abs(Y)),
                    -np.hypot(np.maximum(np.abs(X) - 1, 0), np.maximum(np.abs(Y) - 1, 0)))
    check("sdf of a square, max |error| mm", float(np.abs(d - want).max()), 0.0, 1e-9)


def test_v_and_round():
    rel = carve.Relief(-2, 2, -2, 2, 0.005, 1.0)
    rel.incise([(-2, 0), (2, 0)], depth=0.3, knife="v", angle_deg=60)
    check("V cut: depth at the line", 1.0 - at(rel, 0, 0), 0.3, 1e-9)
    half = 0.3 * math.tan(math.radians(30))
    check("V cut: half width (mm)", float(np.sum(rel.h[:, 200] < 1.0 - 1e-9) * rel.step / 2), half, rel.step)
    check("V cut: depth at a quarter width", 1.0 - at(rel, 0, half / 2), 0.15, 0.01)
    rel = carve.Relief(-2, 2, -2, 2, 0.005, 1.0)
    rel.incise([(-2, 0), (2, 0)], depth=0.2, knife="round", radius_mm=0.5)
    w = 2 * math.sqrt(2 * 0.5 * 0.2 - 0.04)
    check("round gouge: width (mm)", float(np.sum(rel.h[:, 200] < 1.0 - 1e-9) * rel.step), w, 2 * rel.step)


def test_dome_and_wall():
    rel = carve.Relief(-6, 6, -6, 6, 0.01, 0.0)
    rel.add(lambda X, Y: carve.sdf_circle((0, 0), 4.0, X, Y), (-4, -4, 4, 4), base=0.0, edge=1.0, top=3.0,
            kind="dome", wall_deg=89.0, shoulder_mm=0.0)
    hc = 2.0
    Rs = (16 + hc * hc) / (2 * hc)
    check("dome: top", float(at(rel, 0, 0)), 3.0, 1e-6)
    check("dome: on the sphere at r = 2", float(at(rel, 2.0, 0)), 1.0 + math.sqrt(Rs * Rs - 4) - (Rs - hc), 2e-3)
    rel = carve.Relief(-6, 6, -6, 6, 0.01, 0.0)
    rel.add(lambda X, Y: carve.sdf_circle((0, 0), 4.0, X, Y), (-4, -4, 4, 4), base=0.0, edge=2.0, top=2.0,
            kind="flat", wall_deg=60.0, shoulder_mm=0.0)
    check("wall at 60 deg: height 0.5 mm inside the outline", float(at(rel, 3.5, 0)), 0.5 * math.tan(math.radians(60)), 2e-2)


def test_wear():
    rel = carve.Relief(-2, 2, -1, 1, 0.01, 0.0)
    rel.h[:, rel.x <= 0] = 2.0                                  # a block with a vertical wall at x = 0
    r = 0.3
    sys.path.insert(0, os.path.join(ROOT, "crafts/wear"))
    import wear  # noqa: E402
    rel.h = wear.round_edges(rel.h, rel.step, {"edge_radius_mm": r})
    x = -r / 2                                                  # on the rounded arris, r/2 in from the wall
    check("wear: arris rounded to r", float(at(rel, x, 0)), 2.0 - r + math.sqrt(r * r - (r + x) ** 2), 0.01)
    check("wear: flat top untouched", float(at(rel, -1.0, 0)), 2.0, 1e-9)


def test_layers():
    stack = carve.tixi_stack(red_mm=0.4, black_mm=0.2, pairs=3)
    idx, names = carve.layer_index(np.array([0.1, 0.35, 0.5, 0.75, 0.95, 5.0]), stack)
    check("tixi: names in stack order", float(names == ["black", "red"]), 1.0, 0)
    check("tixi: the bands at 0.1 0.35 0.5 0.75 0.95 5", float(np.abs(idx - [0, 1, 1, 0, 1, 0]).sum()), 0.0, 0)
    m = lacquer.load()
    with tempfile.TemporaryDirectory() as d:
        order = lacquer.write_family(os.path.join(d, "f.npz"), m, ["black", "red"])
        F = np.load(os.path.join(d, "f.npz"))
        check("family: red row at c = 1 is the red body at 650 nm", float(np.interp(650, F["lambda_nm"], F["R"][1])),
              float(np.interp(650, *lacquer.body(m, "red"))), 1e-12)
        check("family: c ascending 0..1", float(np.abs(F["c"] - [0, 1]).sum()), 0.0, 0)


def test_km():
    R = np.array([0.05, 0.3, 0.8])
    check("KM: adding nothing returns R", float(np.abs(lacquer.km_add_absorption(R, 0.0) - R).max()), 0.0, 1e-9)
    check("KM: more absorption is darker", float(np.all(lacquer.km_add_absorption(R, 0.5) < R)), 1.0, 0)


def test_ply():
    with tempfile.TemporaryDirectory() as d:
        x, y = np.linspace(0, 2, 5), np.linspace(0, 1, 3)
        h = np.zeros((3, 5))
        nv, nt = carve.write_ply_grid(os.path.join(d, "g.ply"), x, y, h, 0.0, (0, 2, 0, 1))
        check("ply: vertices", nv, 15, 0)
        check("ply: triangles", nt, 16, 0)
        raw = open(os.path.join(d, "g.ply"), "rb").read()
        body = raw[raw.index(b"end_header\n") + 11:]
        V = np.frombuffer(body[:15 * 32], "<f4").reshape(15, 8)
        check("ply: u of the last vertex", float(V[-1, 6]), 1.0, 1e-7)
        check("ply: normal z of a flat grid", float(V[:, 5].min()), 1.0, 1e-7)
        F = np.frombuffer(body[15 * 32:], dtype=[("n", "u1"), ("i", "<i4", (3,))])
        P = V[:, :3]
        t = F["i"][0]
        n = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
        check("ply: winding faces +z", float(np.sign(n[2])), 1.0, 0)


def test_facets():
    rng = np.random.default_rng(3)
    f = carve.facet_jitter((0, 0, 10, 10), 1.5, 0.02, rng)
    X, Y = np.meshgrid(np.linspace(0, 10, 501), np.linspace(0, 10, 501))
    v = f(X, Y)
    check("facets: amplitude bound", float(np.abs(v).max() <= 0.02 + 1e-12), 1.0, 0)
    check("facets: continuous (max step between 0.02 mm samples, mm)", float(np.abs(np.diff(v, axis=1)).max()) < 0.02, 1.0, 0)


def test_processes():
    """The surface processes (crafts/wear, dust, duanwen): their 'new' values change nothing; a ball's touch."""
    for c in ("wear", "dust", "duanwen"):
        sys.path.insert(0, os.path.join(ROOT, "crafts", c))
    import wear, dust, duanwen  # noqa: E401,E402
    new = lambda mod: {k: v.get("new") for k, v in mod.load()["parameters"].items()}
    rel = carve.Relief(-10, 10, -10, 10, 0.05, 0.0)
    rel.add(lambda X, Y: carve.sdf_circle((0, 0), 5.0, X, Y), (-5, -5, 5, 5), base=0.0, edge=2.0, top=2.0, kind="flat", wall_deg=60)
    rng = np.random.default_rng(1)
    W = new(wear)
    check("new: edges not rounded", float(np.abs(wear.round_edges(rel.h, rel.step, W) - rel.h).max()), 0, 0)
    check("new: nothing touched", float(wear.touch(rel.h, rel.step, W).max()), 0, 0)
    check("new: no scratches", float(np.abs(wear.scratches(rel.h.shape, rel.step, W, rng)[0]).max()), 0, 0)
    check("new: no cracks", float(np.abs(duanwen.cracks(rel.h.shape, rel.step, rel.x, rel.y, new(duanwen), rng)[0]).max()), 0, 0)
    g = wear.gap(rel.h, rel.step, 3.0)
    check("new: no dust", float(dust.mask(rel.h, rel.step, None, new(dust)).sum()), 0, 0)
    dm = dust.mask(rel.h, rel.step, None, {"on": 1, "corner_radius_mm": 0.5, "min_depth_mm": 0.05, "in_cracks": 0})
    foot = int(round((10 + 5) / 0.05))                          # the wall's foot at x = 5 (row 200 is y = 0)
    check("dust: at the wall's foot", float(dm[200, foot - 1:foot + 2].any()), 1, 0)
    check("dust: not on the open ground or the top", float(dm[200, 395] or dm[200, 200]), 0, 0)
    # a 3 mm ball pressed on a 2 mm high disc (wall 60 degrees inward from r 5, top edge at r0 = 5 - 2/tan 60) rests
    # on the top edge and the ground with its centre at x = r0 + sqrt(9 - 1), z 3: below it the envelope is
    # 3 - sqrt(9 - (xc - x)^2) (the closing is on a 4x coarser grid: 0.08 mm)
    r0 = 5 - 2 / math.tan(math.radians(60)); xc = r0 + math.sqrt(8)
    for x in (5.0, 5.5, 6.0):
        check(f"touch: gap under the resting ball at x {x}", float(g[200, int(round((x + 10) / 0.05))]),
              3 - math.sqrt(9 - (xc - x) ** 2), 0.08)
    check("touch: far out on the ground (gap mm)", float(g[200, 395]), 0, 0.02)
    E = wear.touch(rel.h, rel.step, {**W, "touch_radius_mm": 3.0, "touch_reach_mm": 0.1}, g)
    check("touch: E on the top", float(E[200, 200]), 1, 0.2)


if __name__ == "__main__":
    for t in (test_sdf, test_v_and_round, test_dome_and_wall, test_wear, test_layers, test_km, test_ply, test_facets,
              test_processes):
        t()
    print("FAILED: " + ", ".join(FAIL) if FAIL else "all passed")
    sys.exit(1 if FAIL else 0)
