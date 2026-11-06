"""Shot 29: Ru ware (汝窑), a shallow dish seen over its near side: the far rim is the arc, the wall below it the sky-blue glaze.

    python3 -I v2/stills/s29_ruyao.py [preview|mid|final]

A real medium in a closed glaze shell, with the opaque body as another mesh inside it. Parameters:
- scattering: sigma_s' 2.5/mm (fit to Shi 2020 R2 L*, v1-archive docs/materials/ru_glaze.md), g* 0.6 and path limit 128 (ibid.,
  gstar.py), so sigma_s = 62.5/cm at 540 nm; blue +12%, red -9% following the anorthite Mie table there;
- absorption: iron, from the table there at R2's concentrations: 2.45, 0.33, 0.55 /cm at 650, 540, 450 nm; red a little less and blue
  more [estimate, to match the yellower green of the Cleveland photo];
- body: 0.3 with the warm tilt fitted there (0.36, 0.30, 0.24);
- glaze thickness 0.5-1 mm (Shi 2020 about 0.5; thicker in pools [estimate]), about 0.15 mm on the lip [estimate].

Crackle: the glaze breaks in sequence, long cracks first, each later crack stopping at an older one, nearly square. So the cracks are
polylines grown in continuous coordinates, never tied to the mesh. Each is a real sheet of geometry going down into the glaze, an air gap
that totally reflects at grazing angles, some of it whitish, its reflections and shadow made by the render. Two scales, about 1 cm and
2-4 mm, as on Cleveland 1957.40. Bubbles are few (寥若晨星), real spheres at random depths. Reference only, not in the film:
ref/ru/photos/cma_1957.40.jpg.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import yohen
from glazekit import balls, close_shell, strips
from kit import OUT, ROOT, blur, fbm, rank, shoot, sstep
from vessel import Profile, fit_arc, reflect_light_loc, turned, view_dir, window

W = 5.4
DIST = 30.0
EL = 40.0  # camera elevation above the dish's plane


def _wall(r0=7.40, z0=0.0, R=6.2, a0=np.radians(48.0), a1=np.radians(4.0), n=400):
    """The inner wall: a circular arc in section, starting a little inside the lip and flattening towards the well."""
    a = np.linspace(a0, a1, n)
    cx, cz = r0 - R * np.sin(a0), z0 + R * np.cos(a0)  # the centre of curvature, inside the dish above it
    return list(zip(cx + R * np.sin(a), cz - R * np.cos(a)))


PROF = Profile([(6.7, -2.6), (7.42, -0.45), (7.565, -0.05), (7.59, 0.03), (7.53, 0.075), (7.45, 0.03)] + _wall(), sigma=0.028)
S_LIP = float(PROF.s[np.argmax(PROF.z)])
AZ = np.pi / 2
LU, V0, V1 = 7.6, -0.34, 3.6  # flat patch of the glaze (cm); V is arc length from the crest of the lip, positive into the dish
SHADER = os.path.join(ROOT, "v2", "stills", "glaze_shader.py")
GLAZE = {"kind": "glaze", "ior": 1.5, "g": 0.6, "sigma_s": [57.0, 62.5, 70.0], "sigma_a": [1.7, 0.33, 1.0]}


def S(u, v, h=0.0):
    return turned(PROF, u, v + S_LIP, h, az=AZ)


_WOB = None


def wob_at(u, v):
    """The hand-thrown wobble (cm): one fixed coarse field, sampled wherever it is needed, so that the surface, the cracks, the bubbles and
    the body move together."""
    global _WOB
    if _WOB is None:
        g = (int((V1 - V0) / 0.02), int(LU / 0.02))
        _WOB = blur(0.004 * fbm(g, 50.0, 2.0, 8.0, 3.0, 11), 2.0).astype(np.float32)
    x = ((u + LU / 2) / 0.02).astype(np.float32)
    y = ((v - V0) / 0.02).astype(np.float32)
    return cv2.remap(_WOB, x.reshape(-1, 1) if x.ndim == 1 else x, y.reshape(-1, 1) if y.ndim == 1 else y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).reshape(x.shape)


def thickness(v):
    """Glaze thickness (cm): thin over the lip, full by half a centimetre in."""
    return 0.022 + 0.043 * sstep(0.02, 0.3, np.abs(v)) + 0.018 * sstep(0.6, 2.6, v)


def coarse(shape, cm_per, lo, hi, beta, seed):
    g = (int((V1 - V0) / cm_per), int(LU / cm_per))
    f = fbm(g, 1.0 / cm_per, lo, hi, beta, seed)
    f = cv2.resize(f, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return blur(f, max(shape[1] / g[1], 1.0))


# --- the crackle --------------------------------------------------------------------------------------------------
def grow_cracks(seed=29, cell=0.012):
    """Sequential fracture in the flat (u, v) patch. Returns a list of dicts with a polyline (cm), generation, depth, tilt."""
    rng = np.random.default_rng(seed)
    gx, gy = int(LU / cell), int((V1 - V0) / cell)
    occ = np.zeros((gy, gx), np.uint8)
    u0, v0 = -LU / 2, V0

    def to_cell(p):
        return int((p[0] - u0) / cell), int((p[1] - v0) / cell)

    def inside(p):
        return -LU / 2 < p[0] < LU / 2 and V0 < p[1] < V1

    # slow stress field: cracks prefer to run across it, so that neighbouring cracks share a mood
    sf = fbm((64, 128), 128 / LU, 0.8, 4.0, 3.5, seed + 1)
    sf = (sf / 3.0 * np.pi).astype(np.float32)

    def stress(p):
        x = int(np.clip((p[0] - u0) / LU * 127, 0, 127))
        y = int(np.clip((p[1] - v0) / (V1 - V0) * 63, 0, 63))
        return float(sf[y, x])

    def run(p0, a0, dist, maxlen, curl, stop_rate):
        pts = [np.array(p0, float)]
        a = a0
        ds = 0.018
        length = 0.0
        hit = False
        turn = 0.0
        own = {}
        step = 0
        while length < maxlen:
            p = pts[-1]
            # steer to meet an older crack square on: walk down the distance field when close
            x, y = to_cell(p)
            if 2 < x < gx - 3 and 2 < y < gy - 3 and length > 0.06:
                dd = dist[y, x] * cell
                if dd < 0.14:
                    gxd = dist[y, x + 2] - dist[y, x - 2]
                    gyd = dist[y + 2, x] - dist[y - 2, x]
                    if abs(gxd) + abs(gyd) > 1e-3:
                        want = np.arctan2(-gyd, -gxd)
                        da = (want - a + np.pi) % (2 * np.pi) - np.pi
                        if abs(da) < 1.7:  # never hook back
                            a += da * (0.10 * (1 - dd / 0.14) + 0.015)
            turn = 0.6 * turn + rng.normal(0, curl)
            a += turn
            if rng.random() < 3.0 * ds:  # fracture changes its mind abruptly, not smoothly
                a += rng.normal(0, 0.45)
            # wander back towards the local preferred direction, weakly
            pref = stress(p)
            da = ((pref - a + np.pi / 2) % np.pi) - np.pi / 2
            a += 0.012 * da
            q = p + ds * rng.uniform(0.7, 1.3) * np.array([np.cos(a), np.sin(a)])
            if not inside(q):
                pts.append(q)
                break
            cx, cy = min(to_cell(q)[0], gx - 1), min(to_cell(q)[1], gy - 1)
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

    # some regions craze finely, others stay in big plates
    densf = cv2.resize(np.exp(0.55 * fbm((64, 128), 128 / LU, 0.5, 2.5, 3.2, seed + 2)), (gx, gy), interpolation=cv2.INTER_CUBIC).astype(np.float32)

    cracks = []

    def commit(pts, gen, hit_a, hit_b):
        # mark the cells
        ip = ((pts - [u0, v0]) / cell).astype(np.int32)
        cv2.polylines(occ, [ip.reshape(-1, 1, 2)], False, 1, 1)
        depth = {0: rng.uniform(0.07, 0.1), 1: rng.uniform(0.05, 0.085), 2: rng.uniform(0.03, 0.06), 3: rng.uniform(0.012, 0.03)}[gen]
        cracks.append({"p": pts, "gen": gen, "depth": depth, "tilt": np.clip(rng.normal(0, 0.14), -0.25, 0.25), "val": rng.random(), "hit": (hit_a, hit_b)})

    # thresholds on open distance (cm), from wide to narrow: gen 0 long cracks, gen 3 the crab's claws
    stages = [(0, 0.42, 50, 6.0, 0.005, 0.0), (1, 0.18, 220, 3.0, 0.007, 0.05), (2, 0.085, 1100, 1.2, 0.009, 0.25), (3, 0.045, 2400, 0.4, 0.013, 1.6)]
    for gen, thresh, n, maxlen, curl, stop in stages:
        for _ in range(n):
            dist = cv2.distanceTransform(1 - occ, cv2.DIST_L2, 3) if occ.any() else np.full(occ.shape, 1e3, np.float32)
            ok = np.argwhere(dist * cell > thresh * rng.uniform(0.75, 1.25) * densf)
            ok = ok[(ok[:, 0] > 2) & (ok[:, 1] > 2) & (ok[:, 0] < gy - 3) & (ok[:, 1] < gx - 3)]
            if len(ok) == 0:
                break
            y, x = ok[rng.integers(len(ok))]
            p0 = np.array([u0 + (x + rng.random()) * cell, v0 + (y + rng.random()) * cell])
            a = stress(p0) + rng.normal(0, 0.55) + (np.pi / 2 if rng.random() < 0.3 else 0.0)
            pa, ha = run(p0, a, dist, maxlen * rng.uniform(0.7, 1.2), curl, stop)
            pb, hb = run(p0, a + np.pi + rng.normal(0, 0.1), dist, maxlen * rng.uniform(0.7, 1.2), curl, stop)
            commit(np.concatenate([pa[::-1], pb[1:]]), gen, ha, hb)
    print("cracks", len(cracks), "total length cm", round(sum(np.hypot(*np.diff(c["p"], axis=0).T).sum() for c in cracks), 1))
    return cracks, occ


def crack_meshes(cracks):
    """Each crack: a ribbon with 4 levels from the mouth down into the glaze."""
    rng = np.random.default_rng(291)
    polys, op, pale = [], [], []
    K = 4
    for c in cracks:
        p = c["p"]
        if len(p) < 3:
            continue
        pj = (p + rng.normal(0, 0.0007, p.shape)).astype(np.float32)
        s = np.cumsum(np.r_[0, np.hypot(*np.diff(pj, axis=0).T)])
        n = len(p)
        # a crack gapes in stretches
        grid = np.arange(0, s[-1] + 0.5, 0.16)
        along = np.interp(s, grid, rng.random(len(grid)))
        endf = np.ones(n) * sstep(0.03, 0.14, pj[:, 1])  # the thin glaze on the lip barely cracks
        if not c["hit"][0]:
            endf = np.minimum(endf, s / 0.12 + 0.04)
        if not c["hit"][1]:
            endf = np.minimum(endf, (s[-1] - s) / 0.12 + 0.04)
        t = thickness(pj[:, 1])
        # the render has no refraction at the surface, so a sheet would read 1.5x deeper: take that off
        D = np.minimum(c["depth"], t * 0.85) * (0.7 + 0.3 * along) * endf * 0.5
        tilt = np.tan(c["tilt"])
        a = np.diff(pj, axis=0, append=pj[-1:] + (pj[-1:] - pj[-2:-1]))
        nrm = np.stack([-a[:, 1], a[:, 0]], -1) / (np.hypot(a[:, 0], a[:, 1])[:, None] + 1e-6)
        rib = np.zeros((n, K, 3), np.float32)
        o = np.zeros((n, K), np.float32)
        w = np.zeros((n, K), np.float32)
        str_g = {0: 1.0, 1: 1.0, 2: 0.95, 3: 0.8}[c["gen"]]
        for j in range(K):
            f = j / (K - 1.0)
            q = pj + nrm * (tilt * D * f)[:, None]
            qu, qv = q[:, 0].astype(np.float32), q[:, 1].astype(np.float32)
            rib[:, j] = S(qu, qv, (wob_at(qu, qv) - 0.0012 - D * f).astype(np.float32))
            o[:, j] = (0.2 + 0.4 * along) * str_g * endf * (1 - f) ** 0.7
            w[:, j] = (0.55 + 0.45 * along) * str_g * endf * (1 - f) ** 1.2
        polys.append(rib)
        op.append(o)
        pale.append(w)
    print("crack verts", sum(p.shape[0] * p.shape[1] for p in polys))
    return strips(polys, {"op": op, "pale": pale})


def build(dens, cracks, occ):
    pxcm = 540.0 * dens
    nx, ny = int(LU * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M")
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - LU / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + V0
    U, V = np.meshgrid(u, v)

    # mouths of the cracks: a hair groove in the surface, drawn in continuous coordinates
    mouth = np.zeros(shape, np.uint8)
    SH = 4
    k = pxcm * (1 << SH)
    wid = max(1, int(round(0.0024 * pxcm)))
    for c in cracks:
        pts = np.round((c["p"] - [-LU / 2, V0]) * k - (0.5 * (1 << SH))).astype(np.int32)
        cv2.polylines(mouth, [pts.reshape(-1, 1, 2)], False, {0: 255, 1: 240, 2: 210, 3: 170}[c["gen"]], wid, cv2.LINE_AA, SH)
    mo = blur(mouth.astype(np.float32) / 255.0, max(0.001 * pxcm, 0.4))

    h = 0.0006 * coarse(shape, 0.01, 0.5, 2.2, 3.0, 8) + 0.00004 * fbm(shape, pxcm, 0.03, 0.2, 2.6, 9) - 0.00016 * blur(mo, max(0.0008 * pxcm, 0.4))
    # a small flake off the lip where the body shows
    fl = sstep(0.994, 0.998, rank(fbm(shape, pxcm, 0.012, 0.1, 2.2, 7))) * sstep(0.1, 0.02, np.abs(V - 0.03))
    t = thickness(V) * (1 + 0.14 * coarse(shape, 0.02, 0.5, 2.5, 3.0, 3))
    h = h - 0.012 * blur(fl, max(0.002 * pxcm, 0.5))
    rough = 0.10 + 0.015 * rank(fbm(shape, pxcm, 0.12, 1.2, 2.6, 10)) + 0.04 * mo

    # outer surface, with a body mesh inside it and the bottom of the shell a little inside the body
    wob = wob_at(U, V)
    top = S(U, V, h + wob)
    m = max(ny // 24, 8)
    vb = np.linspace(V0, V1, m, dtype=np.float32)
    Ub, Vb = np.meshgrid(u, vb)
    bot = S(Ub, Vb, wob_at(Ub, Vb) - thickness(Vb) * 1.3 - 0.008)
    Pg, at = close_shell(top, bot, {"rough": rough.astype(np.float32)}, {"rough": 0.3}, outward=np.array([0.0, -0.75, 0.65]))

    # the body: stoneware, warm grey-buff, with a faint mottling; slight tool marks under the glaze
    bm = max(ny // 3, 32)
    nb = max(nx // 3, 32)
    ub = np.linspace(-LU / 2, LU / 2, nb, dtype=np.float32)
    vbb = np.linspace(V0, V1, bm, dtype=np.float32)
    Ubb, Vbb = np.meshgrid(ub, vbb)
    tb = cv2.resize(t, (nb, bm), interpolation=cv2.INTER_AREA)
    Pb = S(Ubb, Vbb, wob_at(Ubb, Vbb) - tb)
    var = 1.0 + 0.1 * fbm((bm, nb), nb / LU, 0.1, 0.8, 2.6, 21)
    colb = np.stack([0.36 * var, 0.30 * var, 0.24 * var], -1).astype(np.float32)
    return Pg, at["rough"], Pb, colb


def bubbles(cracks_seed=292):
    rng = np.random.default_rng(cracks_seed)
    n = int(LU * (V1 - V0) * 11)
    u = rng.uniform(-LU / 2, LU / 2, n).astype(np.float32)
    v = rng.uniform(V0 + 0.15, V1, n).astype(np.float32)
    r = np.clip(rng.lognormal(np.log(0.0065), 0.55, n), 0.002, 0.03).astype(np.float32)
    t = thickness(v)
    d = (r + 0.002 + rng.random(n) * np.maximum(t * 0.8 - r, 0.002)).astype(np.float32)
    return balls(S(u, v, wob_at(u, v) - d), r)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    DRAFT = q == "draft"  # full size at few samples: to judge at 100% before spending a final
    q = "final" if DRAFT else q
    dens = {"preview": 0.4, "mid": 0.6, "final": 1.0}[q]

    uu, vv = np.linspace(-6, 6, 300, dtype=np.float32), np.linspace(V0, 3, 200, dtype=np.float32)
    Pc = S(*np.meshgrid(uu, vv))
    view = view_dir(-90.0, EL)
    focus = S(np.array([0.0], np.float32), np.array([0.45], np.float32))[0]
    cam, sag = fit_arc(Pc, view, W, DIST, apex=(0.5, 0.46), target0=(0, 7.5, 0), aperture_mm=8.5, focus_point=focus)

    cracks, occ = grow_cracks()
    Pg, Rg, Pb, Cb = build(dens, cracks, occ)
    Pc2, at = crack_meshes(cracks)
    Pbub = bubbles()
    d = os.path.join(OUT, "s29_ruyao")
    os.makedirs(d, exist_ok=True)
    fs = {k: os.path.join(d, f"mesh.{k}.{q}.npz") for k in ("glaze", "body", "crack", "bubble")}
    np.savez(fs["glaze"], P=Pg, rough=Rg)
    np.savez(fs["body"], P=Pb, col=Cb)
    np.savez(fs["crack"], P=Pc2, **at)
    np.savez(fs["bubble"], P=Pbub)

    pt = S(np.array([-0.5], np.float32), np.array([0.55], np.float32))[0]
    r_, z_, nr, nz = PROF.at(np.array([0.55 + S_LIP]))
    th = AZ - 0.5 / r_[0]
    nrm = np.array([nr[0] * np.cos(th), nr[0] * np.sin(th), nz[0]])
    lw, rdir = reflect_light_loc(pt, nrm, cam, 60.0)
    print("window at", lw, "dir", rdir)
    # no hard-edged window. A soft panel in the painted room: its edges fall off and it brightens towards one side
    lights = []
    yohen.use_room()
    env = {"base": [0.02, 0.02, 0.022], "panels": [{"dir": rdir.tolist(), "w": 12, "h": 3.6, "L": 1.5, "rgb": [1.0, 0.985, 0.96], "soft": 1.8, "soft_w": 5, "grad": 0.45}]}
    A = S(np.array([0.0], np.float32), np.array([0.0], np.float32))[0]
    lights += [
        {"name": "fill", "loc": (A + np.array([-22, -30, 60])).tolist(), "target": (A + np.array([0, -1.5, -0.8])).tolist(), "size": [60, 60], "watts": 15000, "rgb": [1.0, 0.98, 0.96], "hide_in_gloss": True},
        {"name": "lip", "loc": (A + np.array([-6, 22, 16])).tolist(), "target": A.tolist(), "size": [30, 1.5], "watts": 500, "rgb": [1.0, 0.93, 0.86]},
    ]
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "glaze", "npz": fs["glaze"], "shader_py": SHADER, "params": GLAZE},
            {"name": "body", "npz": fs["body"], "material": {"Base Color": "col", "Roughness": 0.7, "Specular IOR Level": 0.2}},
            {"name": "crack", "npz": fs["crack"], "shader_py": SHADER, "params": {"kind": "crack", "rough": 0.1, "pale_rgb": [0.97, 0.93, 0.80]}},
            {"name": "bubble", "npz": fs["bubble"], "shader_py": SHADER, "params": {"kind": "bubble"}},
        ],
        "lights": lights,
        "env": env,
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "bounces": 128,
        "volume_bounces": 128,
        "transmission_bounces": 128,
        "diffuse_bounces": 8,
        "glossy_bounces": 8,
        "spp": {"preview": 96, "mid": 192, "final": 512},
    }
    scene["spp"] = {"final": 40} if DRAFT else scene.get("spp", {})
    shoot("s29_ruyao", scene, q, tag="draft" if DRAFT else None, develop={"exposure": 0.5, "contrast": 1.55, "saturation": 1.2, "wb": [1.0, 1.0, 1.0], "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "vignette": 0.3})


main()
