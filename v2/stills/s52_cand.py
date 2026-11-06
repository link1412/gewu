"""Ru ware (汝窑), a shallow six-lobed washer from above, second version: a real medium with the crackle as sheets inside it. The old version is s52_ruyao.py; this one writes only cand.* and s52_ruyao_cand_move_final/, nothing in the film changes until it has been seen.

    python3 -I v2/stills/s52_cand.py flat                  the crackle on the flat: out/v2/s52_ruyao/cand_flat.png
    python3 -I v2/stills/s52_cand.py [preview|mid|final]   a still; final writes cand.*
    GEWU_MOVE=check|final python3 -I v2/stills/s52_cand.py final     the move, in s52_ruyao_cand_move_*/

What it is:
- Glaze: a closed shell over the body, with real scattering and absorption in it (s52_shader, a repair of glaze_shader: see there). Colour comes from thickness, as in the real thing: thin on the lip and the ribs the body shows through warm, pooled in the corner of the well it goes deep. sigma_s and g are from s29 (Shi 2020 fit, v1-archive docs/materials/ru_glaze.md); sigma_a has been moved by eye from iron's values towards blue. Thickness up to 1.5 mm is an ESTIMATE, more than the 0.5-1 mm of the literature, chosen for depth.
- Crackle: sequential fracture as in s29, later cracks stopping at older ones. Four generations, each crack a ribbon going down into the glaze, an air gap with a tan deposit (ref/ru/lotus/17009895.jpg shows tan lines, ref/ru/photos/cma_1957.40.jpg both tan and pale ones). Sizes of the plates are by eye from those two. The fine crab's claws only live in some regions, so large calm plates remain.
- Light: what shows in the polish is one long soft strip in the room, laid so that the far wall mirrors it (r = 2(n.v)n - v) as a highlight that runs along the wall and bends at the lobes. The body is lit by a large soft overhead lamp hidden from reflections, so that no dark band lies across the dish.
- Table: a dark matte top, the film's grey-black. Six lobes at depth 5% of the radius are ours, not checked against a photograph (ref/ru has no such washer).
STAND-INS: the glaze has no refraction at its surface (depths read 1.5x deeper, so the ribbons are scaled); the deposit in a crack is an opaque diffuse fraction; bubbles few, real spheres.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from dishkit import Dish
from glazekit import balls, close_shell, strips
import kit
import yohen
from kit import OUT, blur, fbm, rank, shoot, sstep

NAME = "s52_ruyao"
SEED = 52
HERE = os.path.dirname(os.path.abspath(__file__))
W, EL, DIST = 20.4, 70.0, 88.0
PROFILE = [(4.0, 0.0), (4.35, 0.2), (5.6, 0.9), (6.6, 1.9), (7.02, 2.62), (7.05, 2.86), (6.88, 2.9), (6.5, 2.35), (5.6, 1.4), (4.5, 0.82), (2.5, 0.6), (0.0, 0.55)]
RHO0 = 4.7  # just outside the well
GLAZE = {"kind": "glaze", "ior": 1.5, "g": 0.6, "sigma_s": [55.0, 62.5, 70.0], "sigma_a": [2.6, 0.36, 0.38]}
TABLE = np.array([0.011, 0.011, 0.0115], np.float32)
# the extent of the flat where anything is needed, cm
BOX = (-10.5, 10.5, -7.0, 10.5)
CACHE = os.path.join(OUT, NAME, "cand_cracks.npz")


def fixed_field(lo, hi, beta, seed):
    """A noise field on a fixed grid over the dish; returned as a function of X, Y arrays of any shape."""
    res, ext = 48.0, 11.0
    n = int(2 * ext * res)
    f = fbm((n, n), res, lo, hi, beta, seed)

    def at(X, Y):
        X, Y = np.asarray(X, np.float32), np.asarray(Y, np.float32)
        sh = X.shape
        # cv2.remap has a limit of 32767 rows: go through it in a square
        n_ = X.size
        side = int(np.ceil(np.sqrt(n_))) or 1
        u, v = np.zeros(side * side, np.float32), np.zeros(side * side, np.float32)
        u[:n_], v[:n_] = ((X + ext) * res).ravel(), ((Y + ext) * res).ravel()
        o = cv2.remap(f, u.reshape(side, side), v.reshape(side, side), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        return o.ravel()[:n_].reshape(sh)

    return at


class Body:
    """The fields shared by the surface, the cracks, the bubbles: everything is a function of the flat (X, Y)."""

    def __init__(self):
        self.dish = Dish(PROFILE, lobes=dict(n=6, a=0.05, b=0.2, p=0.8, rho0=RHO0))
        self.rl = self.dish.rho_lip
        self.wave_f = fixed_field(1.2, 6.0, 3.4, SEED + 14)
        self.thick_f = fixed_field(1.0, 5.0, 3.0, SEED + 3)

    def wave(self, X, Y):
        return 0.006 * self.wave_f(X, Y)

    def thickness(self, X, Y):
        rho = np.hypot(X, Y)
        th = np.arctan2(Y, X)
        t = 0.095 + 0.045 * np.exp(-(((rho - RHO0) / 0.9) ** 2))  # it pools where the wall meets the well
        t = t * (1.0 + 0.16 * self.thick_f(X, Y))
        c2 = np.cos(self.dish.lobes["n"] * (th - np.pi / 2) / 2.0) ** 2
        ramp = sstep(RHO0 - 0.6, self.rl, rho)
        t = t * (1.0 - 0.6 * np.exp(-c2 / (0.012 + 0.09 * (1 - ramp))) * ramp)  # thin over the ribs that run down from the notches
        lip = sstep(self.rl - 0.75, self.rl - 0.08, rho) * sstep(self.rl + 0.5, self.rl + 0.15, rho)
        return np.maximum(t * (1 - 0.8 * lip), 0.012)


def grow_cracks(b):
    """Sequential fracture on the flat. Each crack is a polyline with a generation, a depth, a tilt."""
    if os.path.exists(CACHE):
        d = np.load(CACHE, allow_pickle=True)
        return list(d["cracks"])
    rng = np.random.default_rng(SEED)
    cell = 0.016
    x0, x1, y0, y1 = BOX
    gx, gy = int((x1 - x0) / cell), int((y1 - y0) / cell)
    occ = np.zeros((gy, gx), np.uint8)
    # the lip stops all of them: thin glaze hardly crazes
    Xc, Yc = np.meshgrid(x0 + (np.arange(gx) + 0.5) * cell, y0 + (np.arange(gy) + 0.5) * cell)
    Rc = np.hypot(Xc, Yc)
    no = Rc > b.rl - 0.18
    sf = fbm((96, 96), 96 / (x1 - x0), 1.5, 8.0, 3.5, SEED + 1).astype(np.float32)
    zone = rank(fbm((gy // 8, gx // 8), 1.0 / (8 * cell), 1.0, 5.0, 3.2, SEED + 2)).astype(np.float32)
    zone = cv2.resize(zone, (gx, gy), interpolation=cv2.INTER_CUBIC)
    densf = np.exp(0.5 * (zone - 0.5) * 2)

    def to_cell(p):
        return int((p[0] - x0) / cell), int((p[1] - y0) / cell)

    def stress(p):
        """A direction of the local stress: radial, the wall pulls in hoops and meridians (ref/ru/lotus/17009895.jpg is nearly a grid), wandering slowly."""
        return (np.arctan2(p[1], p[0]) if np.hypot(p[0], p[1]) > 3.0 else 0.6) + 0.3 * float(sf[int(np.clip((p[1] - y0) / (y1 - y0) * 95, 0, 95)), int(np.clip((p[0] - x0) / (x1 - x0) * 95, 0, 95))])

    def run(p0, a0, dist, maxlen, curl, stop_rate):
        pts = [np.array(p0, float)]
        a = a0
        ds = 0.02
        length, turn, step = 0.0, 0.0, 0
        hit = False
        own = {}
        while length < maxlen:
            p = pts[-1]
            x, y = to_cell(p)
            if 2 < x < gx - 3 and 2 < y < gy - 3 and length > 0.06:
                dd = dist[y, x] * cell
                if dd < 0.14:  # steer to meet an older crack square on
                    gxd, gyd = dist[y, x + 2] - dist[y, x - 2], dist[y + 2, x] - dist[y - 2, x]
                    if abs(gxd) + abs(gyd) > 1e-3:
                        da = (np.arctan2(-gyd, -gxd) - a + np.pi) % (2 * np.pi) - np.pi
                        if abs(da) < 1.7:
                            a += da * (0.10 * (1 - dd / 0.14) + 0.015)
            turn = 0.6 * turn + rng.normal(0, curl)
            a += turn
            if rng.random() < 1.3 * ds:  # fracture changes its mind abruptly
                a += rng.normal(0, 0.3)
            a += 0.03 * (((stress(p) - a + np.pi / 4) % (np.pi / 2)) - np.pi / 4)  # towards the nearest of four directions: along and across the local stress
            q = p + ds * rng.uniform(0.7, 1.3) * np.array([np.cos(a), np.sin(a)])
            cx, cy = to_cell(q)
            if not (0 <= cx < gx and 0 <= cy < gy):
                break
            if no[cy, cx]:
                pts.append(q)
                hit = True
                break
            if (occ[cy, cx] and length > 0.03) or own.get((cx, cy), step) < step - 5:
                pts.append(q)
                hit = True
                break
            own.setdefault((cx, cy), step)
            step += 1
            pts.append(q)
            length += ds
            if rng.random() < stop_rate * ds:
                break
        return np.array(pts), hit

    # (generation, open distance that a new crack needs, how many at most, longest, curl, chance to stop per cm, recompute the distance every n, how much of it obeys the zones)
    stages = [(0, 0.7, 180, 2.6, 0.0025, 0.2, 1, 0.0), (1, 0.3, 1000, 1.8, 0.004, 0.2, 2, 0.0), (2, 0.14, 6000, 0.9, 0.006, 0.3, 8, 0.0), (3, 0.07, 9000, 0.4, 0.012, 1.4, 16, 1.0)]
    cracks = []
    for gen, thresh, n, maxlen, curl, stop, rec, zk in stages:
        print("gen", gen, flush=True)
        dist = None
        for i in range(n):
            if dist is None or i % rec == 0:
                dist = cv2.distanceTransform(1 - occ, cv2.DIST_L2, 3)
                ok_all = (dist * cell > thresh * densf) & ~no
                if zk:
                    ok_all &= zone > 0.75 * zk * (0.55 if gen == 2 else 0.8)
                ok = np.argwhere(ok_all)
            if len(ok) == 0:
                break
            y, x = ok[rng.integers(len(ok))]
            p0 = np.array([x0 + (x + rng.random()) * cell, y0 + (y + rng.random()) * cell])
            a = stress(p0) + rng.normal(0, 0.2) + (np.pi / 2 if rng.random() < 0.5 else 0.0)
            pa, ha = run(p0, a, dist, maxlen * rng.uniform(0.7, 1.2), curl, stop)
            pb, hb = run(p0, a + np.pi + rng.normal(0, 0.1), dist, maxlen * rng.uniform(0.7, 1.2), curl, stop)
            pts = np.concatenate([pa[::-1], pb[1:]])
            if len(pts) < 3:
                continue
            ip = ((pts - [x0, y0]) / cell).astype(np.int32)
            cv2.polylines(occ, [ip.reshape(-1, 1, 2)], False, 1, 1)
            depth = {0: rng.uniform(0.75, 1.0), 1: rng.uniform(0.55, 0.85), 2: rng.uniform(0.3, 0.6), 3: rng.uniform(0.12, 0.3)}[gen]
            cracks.append({"p": pts.astype(np.float32), "gen": gen, "depth": depth, "tilt": float(np.clip(rng.normal(0, 0.16), -0.3, 0.3)), "val": float(rng.random()), "hit": (ha, hb)})
    print("cracks", len(cracks), "total length cm", round(sum(np.hypot(*np.diff(c["p"], axis=0).T).sum() for c in cracks), 1), flush=True)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.savez(CACHE, cracks=np.array(cracks, dtype=object), allow_pickle=True)
    return cracks


def crack_meshes(b, cracks):
    """Each crack: a ribbon with 4 levels from the mouth down into the glaze."""
    rng = np.random.default_rng(SEED + 91)
    polys, op, pale = [], [], []
    K = 4
    for c in cracks:
        p = np.asarray(c["p"], float)
        pj = (p + rng.normal(0, 0.0008, p.shape)).astype(np.float32)
        s = np.cumsum(np.r_[0, np.hypot(*np.diff(pj, axis=0).T)])
        n = len(p)
        grid = np.arange(0, s[-1] + 0.5, 0.16)
        along = np.interp(s, grid, rng.random(len(grid)))  # a crack gapes in stretches
        endf = np.ones(n)
        if not c["hit"][0]:
            endf = np.minimum(endf, s / 0.12 + 0.04)
        if not c["hit"][1]:
            endf = np.minimum(endf, (s[-1] - s) / 0.12 + 0.04)
        t = b.thickness(pj[:, 0], pj[:, 1])
        D = c["depth"] * t * 0.85 * 0.5 * (0.7 + 0.3 * along) * endf  # 0.5: no refraction at the surface, a sheet would read 1.5x deeper and more
        a = np.diff(pj, axis=0, append=pj[-1:] + (pj[-1:] - pj[-2:-1]))
        nrm = np.stack([-a[:, 1], a[:, 0]], -1) / (np.hypot(a[:, 0], a[:, 1])[:, None] + 1e-6)
        rib = np.zeros((n, K, 3), np.float32)
        o = np.zeros((n, K), np.float32)
        w = np.zeros((n, K), np.float32)
        g = {0: 0.55, 1: 0.55, 2: 0.5, 3: 0.3}[c["gen"]]
        dep = 0.35 + 0.65 * c["val"]  # how much the tan has gone down this one
        for j in range(K):
            f = j / (K - 1.0)
            q = pj + nrm * (np.tan(c["tilt"]) * D * f)[:, None]
            qu, qv = q[:, 0].astype(np.float32), q[:, 1].astype(np.float32)
            rib[:, j] = b.dish.surface(qu, qv, b.wave(qu, qv) - 0.0012 - D * f)
            o[:, j] = (0.25 + 0.5 * along) * g * endf * (1 - f) ** 0.7
            w[:, j] = (0.6 + 0.4 * along) * dep * endf * (1 - f) ** 0.9  # most of what shows in a crack is the tan deposit (ref/ru/lotus/17009895.jpg), hardly any dark
        polys.append(rib)
        op.append(o)
        pale.append(w)
    print("crack verts", sum(x.shape[0] * x.shape[1] for x in polys), flush=True)
    return strips(polys, {"op": op, "pale": pale})


def bubbles(b):
    rng = np.random.default_rng(SEED + 92)
    n = 420
    rho = b.rl * np.sqrt(rng.random(n)) * 0.97
    th = rng.uniform(-np.pi, np.pi, n)
    x, y = (rho * np.cos(th)).astype(np.float32), (rho * np.sin(th)).astype(np.float32)
    r = np.clip(rng.lognormal(np.log(0.008), 0.6, n), 0.003, 0.028).astype(np.float32)
    t = b.thickness(x, y)
    d = (r + 0.004 + rng.random(n) * np.maximum(t * 0.55 - r, 0.002)).astype(np.float32)
    return balls(b.dish.surface(x, y, b.wave(x, y) - d), r)


def flat(b, cracks):
    pxcm = 125.0
    x0, x1, y0, y1 = BOX
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    im = np.zeros((ny, nx), np.float32)
    for gen, val, wd in ((3, 0.25, 1), (2, 0.45, 1), (1, 0.75, 1), (0, 1.0, 2)):
        lay = np.zeros((ny, nx), np.uint8)
        for c in cracks:
            if c["gen"] == gen:
                ip = np.round((np.asarray(c["p"]) - [x0, y0]) * pxcm * 16).astype(np.int32)
                cv2.polylines(lay, [ip.reshape(-1, 1, 2)], False, 255, wd, cv2.LINE_AA, 4)
        im = np.maximum(im, lay.astype(np.float32) / 255.0 * val)
    out = (150 - 120 * im).astype(np.uint8)
    cv2.imwrite(os.path.join(OUT, NAME, "cand_flat.png"), out[::-1])


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    b = Body()
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cracks = grow_cracks(b)
    if q == "flat":
        flat(b, cracks)
        return
    dish, rl = b.dish, b.rl
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.42), aperture_mm=20.0, focus_rho=rl - 1.6)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 170.0 * dens
    X, Y = dish.grid(cam, pxcm, margin=0.14)
    rho = np.hypot(X, Y)
    # beyond the lip the sheet folds together in a ring just past the lip: a grid has corners, a dish has not
    k = np.minimum(1.0, (rl + 0.6) / np.maximum(rho, 1e-6))
    X, Y = X * k, Y * k
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    wave = b.wave(X, Y)

    # mouths of the cracks: a hair groove in the skin, so that the highlight breaks at them
    x0, y0 = X[0, 0], Y[0, 0]
    ny, nx = X.shape
    mouth = np.zeros((ny, nx), np.uint8)
    for c in cracks:
        if c["gen"] <= 2:
            ip = np.round((np.asarray(c["p"]) - [x0, y0]) * pxcm * 16 - 8).astype(np.int32)
            cv2.polylines(mouth, [ip.reshape(-1, 1, 2)], False, {0: 255, 1: 200, 2: 110}[c["gen"]], 1, cv2.LINE_AA, 4)
    mo = blur(mouth.astype(np.float32) / 255.0, max(0.002 * pxcm, 0.5))
    fine = fbm((ny, nx), pxcm, 0.03, 0.3, 2.4, SEED + 9)  # a hair of orange peel
    top = dish.surface(X, Y, wave - 0.0005 * mo + 0.00006 * fine)
    rg = rank(fbm((ny // 4, nx // 4), pxcm / 4, 0.4, 3.0, 2.8, SEED + 10))
    rg = cv2.resize(rg, (nx, ny), interpolation=cv2.INTER_CUBIC)
    rough = np.clip(0.095 + 0.03 * rg + 0.06 * mo + 0.04 * sstep(rl - 0.3, rl - 0.05, rho), 0.05, 1.0).astype(np.float32)  # satin; a little rougher on the worn lip

    m = max(ny // 16, 16)
    idx = np.linspace(0, ny - 1, m).astype(int)
    Xb, Yb = X[idx], Y[idx]
    bot = dish.surface(Xb, Yb, b.wave(Xb, Yb) - b.thickness(Xb, Yb) - 0.03)
    Pg, at = close_shell(top, bot, {"rough": rough}, {"rough": 0.3}, outward=np.array([0.0, -0.35, 0.9]))
    fs = {k_: os.path.join(d, f"cand_{k_}.{q}.npz") for k_ in ("glaze", "bodym", "crack", "bubble", "rest")}
    np.savez(fs["glaze"], P=Pg, **at)

    # the body: stoneware, 香灰胎: warm grey-buff, faint mottling [estimate], under the glaze
    step = 3
    Xc, Yc = X[::step, ::step], Y[::step, ::step]
    Pb = dish.surface(Xc, Yc, b.wave(Xc, Yc) - b.thickness(Xc, Yc))
    var = 1.0 + 0.1 * fbm(Xc.shape, pxcm / step, 0.1, 1.2, 2.6, SEED + 21)
    burn = 1.0 - sstep(rl - 0.55, rl - 0.1, np.hypot(Xc, Yc))[..., None] * np.array([0.45, 0.55, 0.62])  # where the glaze runs thin at the lip the body shows, a darker warm rim [estimate]
    colb = (np.stack([0.44 * var, 0.385 * var, 0.32 * var], -1) * burn).astype(np.float32)
    np.savez(fs["bodym"], **yohen.front(P=Pb, col=colb))

    Pc, atc = crack_meshes(b, cracks)
    np.savez(fs["crack"], P=Pc, **atc)
    np.savez(fs["bubble"], P=bubbles(b))
    Pr, Cr = yohen.rest_of_bowl(dish, col=(0.3, 0.37, 0.36), under=0.2)
    np.savez(fs["rest"], **yohen.front(P=Pr, col=Cr))

    # the table: a dark matte top with hardly any variation: the film's grey-black, a surface for the shadow to fall on, nothing to look at
    tn = 700
    tx, ty = np.meshgrid(np.linspace(-140, 140, tn, dtype=np.float32), np.linspace(-140, 140, tn, dtype=np.float32))
    tcol = TABLE * (1.0 + 0.05 * fbm((tn, tn), tn / 280.0, 8.0, 80.0, 3.0, SEED + 30) + 0.02 * fbm((tn, tn), tn / 280.0, 1.0, 6.0, 2.2, SEED + 31))[..., None]
    table_npz = os.path.join(d, f"cand_table.{q}.npz")
    np.savez(table_npz, P=np.stack([tx, ty, np.zeros_like(tx)], -1), col=tcol.astype(np.float32))

    # the room. A long soft strip above and behind the camera, which the far wall mirrors; it runs along the wall and bends at the lobes
    yohen.use_room()
    r0, _, _ = yohen.reflection_at(dish, cam, 0.5, 0.56)
    print("wall mirrors", np.round(r0, 3), flush=True)
    env = {"diffuse": False, "base": [0.05, 0.053, 0.06], "panels": [
        {"dir": r0.tolist(), "w": 62, "h": 4, "L": 11.0, "rgb": [1.0, 0.99, 0.97], "soft": 3.5, "soft_w": 14, "grad": 0.25},
        {"dir": [0.0, 0.34, 0.94], "w": 42, "h": 26, "L": 0.3, "rgb": [0.97, 0.99, 1.0], "soft": 20},  # a dim ceiling for the well to mirror: the fat sheen of the glaze
    ]}
    tgt = dish.polar(np.array(rl * 0.45), np.pi / 2).tolist()
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "glaze", "npz": fs["glaze"], "shader_py": os.path.join(HERE, "s52_shader.py"), "params": GLAZE},
            {"name": "bodym", "npz": fs["bodym"], "material": {"Base Color": "col", "Roughness": 0.7, "Specular IOR Level": 0.2}},
            {"name": "crack", "npz": fs["crack"], "shader_py": os.path.join(HERE, "glaze_shader.py"), "params": {"kind": "crack", "rough": 0.15, "pale_rgb": [0.72, 0.6, 0.4]}},
            {"name": "bubble", "npz": fs["bubble"], "shader_py": os.path.join(HERE, "glaze_shader.py"), "params": {"kind": "bubble"}},
            {"name": "rest", "npz": fs["rest"], "material": {"Base Color": "col", "Roughness": 0.3}},
            {"name": "table", "npz": table_npz, "material": {"Base Color": "col", "Roughness": 0.6, "Specular IOR Level": 0.25}},
        ],
        "env": env,
        "lights": [
            {"name": "key", "loc": [-34.0, 22.0, 90.0], "target": tgt, "size": [90, 90], "watts": 85000, "rgb": [1.0, 0.985, 0.96], "hide_in_gloss": True},
        ],
        "bounces": 64,
        "volume_bounces": 48,
        "transmission_bounces": 48,
        "diffuse_bounces": 4,
        "glossy_bounces": 4,
        "spp": {"preview": 96, "mid": 160, "final": 320},
    }
    develop = {"exposure": 0.0, "contrast": 1.2, "saturation": 1.05, "black": 0.001, "grain": 1.0, "sharpen": 0.2, "halation": 0.03, "glare": 0.003, "vignette": 0.2}
    if os.environ.get("GEWU_MOVE"):
        # under its own name: _take clears {name}_move_*. Two more frames than wanted, the first and last have only half a blur: drop them afterwards
        deg = -3.0 * 16.0 / 14.0  # 3 degrees over the 15 frames kept: slow, one way, even
        spin = {"pt": [0, 0, 0], "axis": [0, 0, 1], "deg": deg, "meshes": {"except": ["table"]}}
        kit.looks = lambda: {NAME + "_cand": {"move": {"frames": 17, "spin": spin, "spp": int(os.environ.get("S52_SPP", 192))}}}
        shoot(NAME + "_cand", scene, q, develop=develop)
        return
    shoot(NAME, scene, q, develop=develop, tag="cand" if q == "final" else f"cand_{q}{os.environ.get('S52_TAG', '')}")


main()
