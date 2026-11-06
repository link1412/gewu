"""Shot 17 round 3 (孔雀羽毛的眼): stacked train feathers, a 100 mm macro at f/2.8 (docs/shots/17-peacock.md).
Round 1 (a 12 mm frame of single barbules) is in git, commit 072b8da; round 2 (this layout, region 2 and 3 as separate
meshes with a hard edge) in 736eb98. Round 3: one vane mesh grading from region 2's stack into region 3's (the
material's table2, a per-vertex mix), the two rows of a barb shaded alike (no striping), a broad sheen band from the
vane's large-scale curvature, the feather behind in soft colour fields.

    python3 -I shots/17-peacock/scene.py --out DIR [--res 1280x720] [--spp N] [--seed S]

Writes DIR/scene.pbrt, vane.ply, vane_L.ply, back_R2.ply, back_R3.ply, back_R4.ply, optics.json, framing.json; the barbule tables (barbule.py
lut) are read from out/shots/17-peacock/lut_R2.npz, lut_R3.npz, lut_R4.npz. Cycles only (material "barbule").

The picture: the lower half is the near feather's blue-green zone (Freyer's region 2), sharp; its edge with the
bronze ring (region 3) is the original's arc; above it the same vane rolls over away from the lens (out of focus
within a few mm), and past its edge, 12 mm deeper, another feather (bronze with green-gold patches), far out of focus.

At 64 mm across, one pixel of the 1920 frame is 33 um, a barbule (~35-50 um wide, ~1 mm long) is a pixel or less:
the barbules are not modelled one by one. Each barb is two strips (its two rows of barbules, one each side), and
the barbules are in the shading: the strip's normal leans across it (a row of barbules rising from the barb and
curving down: a crescent, Yoshioka & Kinoshita 2002 [查到 shape; angles A]), the anisotropic lobe's wide axis
across the barbules' axis (a field of parallel curved cylinders), the colour the stack's (TMM table, barbule.py)
at mu = cos(view, normal).

World: mm, the feather about z = 0, the lens on +Z looking down; image right = -X, image up = +Y. Laid out in
image-plane mm (x right, y up), written with X = -x. Everything in GEOM is [A] unless said.
"""

import argparse
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = json.load(open(os.path.join(ROOT, "spec", "shots.json")))
SHOT = next(s for s in SPEC["shots"] if s["shot"] == 17)
OUT = os.path.join(ROOT, "out/shots/17-peacock")

# --- frame and lens [A]: a 100 mm macro on the 5D Mark IV at f/2.8, 16:9 crop; the frame 64 mm (the brief's 8 cm -20%,
# so the blue-green zone can fill the lower half: its width is [A], see GEOM["zone_R_scale"])
FRAME_W = 64.0
SENSOR_W = 36.0
FOCAL = 100.0
FNUMBER = 2.8
MAG = SENSOR_W / FRAME_W
U = FOCAL * (1 + 1 / MAG)               # object distance
V = FOCAL * (1 + MAG)                   # image distance

GEOM = {
    "barb_spacing": 0.35,              # Freyer Fig. 1b's 5 mm bar [A, from a figure]
    "spacing_jitter": 0.04,            # combed: a few % [A]
    "barb_deg": 128.0,                 # barbs run up-left to their tips: the original's "\\" streaks [A]
    "bow_deg_per_mm": 0.35,            # the barbs bow, all alike [A]
    "warp_mm": 1.4, "warp_corr": 14.0,  # the large-scale flow (a smooth displacement of the whole vane) [A]
    "step": 0.2,                       # along the barb (4 px of the 1280 render)
    "overlap": 1.06, "overlap_R3": 0.95,   # each row of barbules reaches a little under the next barb's; in region 3 they leave gaps [A]
    "barbule_deg": 35.0,               # barbule axis to the barb (r1's) [A]
    "lean0_deg": 0.5, "crescent_deg": 1.5, "crescent_R3_deg": 6.0,   # a row's normal across it (lean at the barb .. at its edge); more in region 3, whose barbules stand out on both sides of the barb (Freyer p. 53) [查到 shape; angles A]
    "rise_deg": 6.0,                   # toward the barb's tip [A]
    "tilt_deg": 6.0, "tilt_corr": 8.0,  # the vane's slow waves [A]
    "sweep_az": -45.0, "sweep_deg_per_mm": 0.45, "sweep_at0_deg": 10.0,   # the vane's large-scale curvature (shading only): its normal tilts toward sweep_az by at0 + k q (q: mm along sweep_az from the centre), so one broad band where it meets the key's half-vector crosses the frame diagonally [A]
    "barb_jitter_deg": 0.7,            # a barb's own tilt: combed [A]
    "glint_deg": 1.8, "glint_corr": 0.2,   # barbule-scale waviness: glints [A]
    "band_mm": 6.5, "band_field": 1.2, "band_jitter": 0.15,   # the bronze band's width above the arc; beyond it the barbs are loose [A]
    "curl_from": 2.0, "curl_R": 12.0,  # beyond curl_from above the arc the vane curls away: z = -(d - from)^2 / (2 R) [A]
    "loose_w": 0.025, "taper_mm": 2.5,   # a loose barb's width (no barbules; its colour region 3's table, a_mean["L"]); the vane's rows narrow to it over taper_mm before the band's edge [A]
    "edge_jitter": 0.25, "edge_field": 0.2, "edge_corr": 3.0,   # the zone's edge staggered barb by barb (ref/peacock2 3-side/02, 07) [A]
    "edge_bias": -0.4,                 # r3: the grade centred this far inside the eye edge (mm), so the band's copper reaches the edge rows [A, fitted]
    "edge_w": 2.0,                     # along a barb region 2's stack grades into region 3's over this (mm): mix = smoothstep [A]
    "a_mean": {"R2": 170.0, "R3": 224.0, "L": 222.0}, "a_sigma": {"R2": 4.0, "R3": 8.0, "L": 6.0},   # lattice period: R3 within 198-223 (Durrer) [查到 range; values A]
    "a_corr": 2.5,                     # patches of like colour [A]
    "rim_nm": 0.0, "rim_mm": 2.0,     # inside the edge the period falls (bluer): a = a_mean - rim exp(-dist/rim_mm) [A, fitted to the original's region colours]
    "back_z": -16.0, "back_spacing": 0.5, "back_deg": 145.0,   # the feather behind [A]
    "back_clump_mm": 2.2, "back_clump_deg": 6.0, "back_gap": -0.85,             # its barbs gathered in locks: diagonal streaks [A]
    "back_R4_level": 0.6, "back_R4_corr": 7.0,                 # (unused since r3's rings)
    "back_rings": {"eyes": [((-25.0, 36.0), (28.0, 26.0)), ((32.0, 41.0), (30.0, 28.0))], "edges": (0.74, 0.86, 0.96), "wobble": 0.04},   # two eyes behind, above the frame: R2 inside edges[0], R3 to [1], green-gold R4 to [2], R3 beyond; blurred they cross the top as soft arcs (ref/peacock2 2-stack/01, 03) [A]
    "back_tilt_deg": 14.0, "back_tilt_corr": 5.0,              # its own waves: uneven bright patches [A]
    "back_R2_level": 1.4, "back_R2_a": 160.0,                  # patches of its blue-green zone, seen off-normal: violet-blue [A]
    "back_eye": (-14.0, 22.0, 0.0),                            # its eye (centre x, y, radius, mm; at the top edge): blue-green zone, blurred [A]
}
BODY_RGB = (0.02, 0.012, 0.013)   # the barbules' melanin body: near black, a faint violet (r3) [A]
BODY_NEAR_RGB = (0.02, 0.012, 0.024)   # r3: the near feather's, with a violet cast (the band's dark gaps read purple in the original) [A]
FLOOR_RGB = (0.012, 0.008, 0.010)   # far below everything [A]
ALPHA = 0.12                       # the stack's lobe (GGX alpha) [A]
TABLE = {"R2": "R2", "R3": "R3", "L": "R3"}   # region -> barbule table (the vane: R2 graded into R3)
ANISO = 0.25                      # wide across the barbules' axis [A]

# --- lights (image-plane coordinates): a key from the lower right, one from the left (slightly low), one from the top (it lights the vane
# where it rolls away), a dome fill in 4 azimuth quadrants; each its own light group [A]
KEYS = {"key": {"az": -45.0, "polar": 22.0, "dist": 150.0, "size": 60.0},
        "key2": {"az": -165.0, "polar": 35.0, "dist": 150.0, "size": 60.0},
        "top": {"az": 90.0, "polar": 62.0, "dist": 150.0, "size": 80.0}}
DOME = 250.0
BANDS = [(8, 75)]
QUADS = 4

ARC_CORR = {"dx": 0.0, "dy": 0.0, "R_scale": 1.0}   # the zone's edge is where it is put (z = 0 there) [checked by measure.py]


def arc_circle():
    """The zone's edge as a circle in image-plane mm: centre, radius."""
    H = FRAME_W * 9 / 16
    ax = (SHOT["arc"]["apex_x"] + ARC_CORR["dx"] - 0.5) * FRAME_W
    ay = (0.5 - SHOT["arc"]["apex_y"] - ARC_CORR["dy"]) * H
    R = SHOT["arc"]["radius_over_width"] * FRAME_W * ARC_CORR["R_scale"]
    return np.array([ax, ay - R]), R


def field(rng, corr, ext, n=256):
    """A smooth Gaussian random field (unit std) over ext=(x0,x1,y0,y1), correlation length corr; a sampler."""
    x0, x1, y0, y1 = ext
    k = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None] ** 2
    px = max(x1 - x0, y1 - y0) / n
    f = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((n, n))) * np.exp(-2 * (math.pi * corr / px) ** 2 * k)))
    f /= f.std()

    def at(x, y):
        i = np.clip((np.asarray(y) - y0) / px, 0, n - 1.001)
        j = np.clip((np.asarray(x) - x0) / px, 0, n - 1.001)
        i0, j0 = i.astype(int), j.astype(int)
        di, dj = i - i0, j - j0
        return (f[i0, j0] * (1 - di) * (1 - dj) + f[i0 + 1, j0] * di * (1 - dj) + f[i0, j0 + 1] * (1 - di) * dj
                + f[i0 + 1, j0 + 1] * di * dj)
    return at


def lean(N, d, ang):
    """Tilt unit normals N (...,3) toward the directions d (...,3) by ang (...) radians (about N x d)."""
    a = np.cross(N, d)
    a /= np.linalg.norm(a, axis=-1, keepdims=True) + 1e-12
    c, s = np.cos(ang)[..., None], np.sin(ang)[..., None]
    return N * c + np.cross(a, N) * s + a * (a * N).sum(-1, keepdims=True) * (1 - c)


def roll(P2, c0, R):
    """The near vane from its flat layout (image-plane points P2 (...,2)) to 3-D: flat inside, curling away from the
    lens beyond curl_from above the arc. Returns P (...,3) and the surface normal (...,3)."""
    G = GEOM
    r = P2 - c0
    rr = np.linalg.norm(r, axis=-1, keepdims=True)
    rh = r / rr
    dd = np.clip(rr - R - G["curl_from"], 0, None)
    z = -0.5 * dd ** 2 / G["curl_R"]
    P = np.concatenate([P2, z], -1)
    N = np.concatenate([rh * dd / G["curl_R"], np.ones_like(dd)], -1)
    return P, N / np.linalg.norm(N, axis=-1, keepdims=True)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def strips(seed, ext, c0, R, rng):
    """The near feather: per barb two rows. Returns {"V": runs, "L": runs}: the vane (region 2 graded into region 3;
    columns u, v, s of region 2's table, s of region 3's, mix) and the loose barbs beyond the bronze band (u, v, s)."""
    G = GEOM
    th = math.radians(G["barb_deg"])
    u0 = np.array([math.cos(th), math.sin(th)])
    n0 = np.array([u0[1], -u0[0]])                        # across the barbs (to the lower right)
    if n0 @ np.array([math.cos(math.radians(38)), math.sin(math.radians(38))]) < 0:
        n0 = -n0
    wx, wy = field(rng, G["warp_corr"], ext), field(rng, G["warp_corr"], ext)
    tx, ty = field(rng, G["tilt_corr"], ext), field(rng, G["tilt_corr"], ext)
    fa = {r: field(rng, G["a_corr"], ext) for r in ("R2", "R3", "L")}
    fe = field(rng, G["edge_corr"], ext)
    gx, gy = field(rng, G["glint_corr"], ext, n=1024), field(rng, G["glint_corr"], ext, n=1024)
    fw = field(rng, 8.0, ext)
    sa = math.radians(G["sweep_az"])
    dsw = np.array([math.cos(sa), math.sin(sa)])
    half = math.hypot(ext[1] - ext[0], ext[3] - ext[2]) / 2 + 3
    sp = G["barb_spacing"]
    offs = np.arange(-half, half, sp) + rng.uniform(0, sp)
    offs = offs + rng.normal(0, sp * G["spacing_jitter"], len(offs))
    kap = math.radians(G["bow_deg_per_mm"])
    ts = np.arange(-half, half, G["step"])
    lo_hi = {r: np.load(os.path.join(OUT, f"lut_{TABLE[r]}.npz"))["s"][[0, -1]] for r in ("R2", "R3", "L")}
    lo_hi = {r: (float(v[0]), float(v[1])) for r, v in lo_hi.items()}
    out = {"V": [], "L": []}
    ws = np.array([0.0, 0.5, 1.0])
    for o in offs:
        c = o * n0 + np.multiply.outer(ts, u0) + np.multiply.outer(0.5 * kap * ts ** 2, n0)
        c = c + G["warp_mm"] * np.stack([wx(c[:, 0], c[:, 1]), wy(c[:, 0], c[:, 1])], -1)
        m = (c[:, 0] > ext[0]) & (c[:, 0] < ext[1]) & (c[:, 1] > ext[2]) & (c[:, 1] < ext[3])
        if m.sum() < 3:
            continue
        i0, i1 = np.flatnonzero(m)[[0, -1]]
        c = c[max(i0 - 1, 0):i1 + 2]
        tan = np.gradient(c, axis=0)
        tan /= np.linalg.norm(tan, axis=1, keepdims=True)
        nn = np.stack([tan[:, 1], -tan[:, 0]], -1)
        nn *= np.sign((nn @ n0))[:, None]
        # region 2 -> 3 along the barb: a smoothstep over edge_w about the (staggered) edge; beyond the band: loose
        e = G["edge_bias"] + rng.normal(0, G["edge_jitter"]) + G["edge_field"] * fe(c[:, 0], c[:, 1])
        dc = np.linalg.norm(c - c0, axis=1) - R
        mix = smooth((dc - e) / G["edge_w"] + 0.5)
        wb = G["band_mm"] + G["band_field"] * fw(c[:, 0], c[:, 1]) + G["band_jitter"] * rng.standard_normal()
        reg = np.where(dc < wb, "V", "L")
        jit = math.radians(G["barb_jitter_deg"]) * rng.standard_normal(2)
        zb = 0.003 * rng.random()
        T = nn                                                            # the lobe's wide axis: across the barb, both rows alike
        rnd = {r: 0.3 * rng.standard_normal() for r in ("R2", "R3", "L")}
        for side in (+1, -1):
            ovl = G["overlap"] + (G["overlap_R3"] - G["overlap"]) * mix
            tp = smooth((wb - dc) / G["taper_mm"])
            hw = np.where(reg == "L", G["loose_w"] / 2, G["loose_w"] / 2 + (sp / 2 * ovl - G["loose_w"] / 2) * tp)
            P2 = c[:, None, :] + side * nn[:, None, :] * (ws[None, :, None] * hw[:, None, None])
            P, N = roll(P2, c0, R)
            P = P + N * (zb + 0.004 * (1 - ws))[..., None]
            # the large-scale curvature (the sweep), the vane's slow waves, the barb's own (combed) tilt, fine glints
            q = (P2 * dsw).sum(-1)
            N = lean(N, np.broadcast_to(np.r_[dsw, 0.0], N.shape), np.radians(G["sweep_at0_deg"] + G["sweep_deg_per_mm"] * q))
            N = lean(N, np.broadcast_to(np.array([1.0, 0, 0]), N.shape), math.radians(G["tilt_deg"]) * tx(P2[..., 0], P2[..., 1]) + jit[0])
            N = lean(N, np.broadcast_to(np.array([0, 1.0, 0]), N.shape), math.radians(G["tilt_deg"]) * ty(P2[..., 0], P2[..., 1]) + jit[1])
            N = lean(N, np.broadcast_to(np.array([1.0, 0, 0]), N.shape), math.radians(G["glint_deg"]) * gx(P2[..., 0], P2[..., 1]))
            N = lean(N, np.broadcast_to(np.array([0, 1.0, 0]), N.shape), math.radians(G["glint_deg"]) * gy(P2[..., 0], P2[..., 1]))
            t3 = np.concatenate([tan, np.zeros((len(tan), 1))], -1)[:, None, :].repeat(3, 1)
            n3 = np.concatenate([side * nn, np.zeros((len(nn), 1))], -1)[:, None, :].repeat(3, 1)
            N = lean(N, t3, np.full(N.shape[:2], math.radians(G["rise_deg"])))
            cres = (G["crescent_deg"] + (G["crescent_R3_deg"] - G["crescent_deg"]) * mix)[:, None]
            N = lean(N, n3, np.radians(G["lean0_deg"] + cres * ws[None, :]))
            uu = (P2 * T[:, None, :]).sum(-1)
            vv = (P2 * tan[:, None, :]).sum(-1)
            sv = {}
            for r in ("R2", "R3", "L"):
                a = G["a_mean"][r] + G["a_sigma"][r] * (0.8 * fa[r](P2[..., 0], P2[..., 1]) + rnd[r])
                if r == "R2":
                    a = a - G["rim_nm"] * np.exp(-np.clip(R - np.linalg.norm(P2 - c0, axis=-1), 0, None) / G["rim_mm"])
                lo, hi = lo_hi[r]
                sv[r] = np.clip((a - lo) / (hi - lo), 0, 1)
            mx = np.broadcast_to(mix[:, None], uu.shape)
            for r, cols in (("V", [uu, vv, sv["R2"], sv["R3"], mx]), ("L", [uu, vv, sv["L"]])):
                # runs of this part; a run takes one more sample so the join has no gap
                sel = (reg == r).astype(int)
                b = np.flatnonzero(np.diff(np.r_[0, sel, 0]))
                for k0, k1 in zip(b[::2], b[1::2]):
                    sl = slice(k0, min(k1 + 1, len(c)))
                    if sl.stop - sl.start >= 2:
                        out[r].append((P[sl], N[sl], np.stack([x[sl] for x in cols], -1)))
    return out


def mesh(runs):
    Ps, Ns, UVs, Ts = [], [], [], []
    nv = 0
    for P, N, UV in runs:
        n = len(P)
        Ps.append(P.reshape(-1, 3))
        Ns.append(N.reshape(-1, 3))
        UVs.append(UV.reshape(-1, UV.shape[-1]))
        i = np.arange(n - 1)[:, None]
        q = []
        for j in range(2):
            a, b, cc, d = i * 3 + j, i * 3 + j + 1, (i + 1) * 3 + j + 1, (i + 1) * 3 + j
            q.append(np.concatenate([np.stack([a, b, cc], -1), np.stack([a, cc, d], -1)], 0).reshape(-1, 3))
        Ts.append(np.concatenate(q) + nv)
        nv += n * 3
    return np.concatenate(Ps), np.concatenate(Ns), np.concatenate(UVs), np.concatenate(Ts)


def back_mesh(ext, rng):
    """The feather behind: a flat vane at back_z, barbs as plain strips gathered in locks (its fine detail is lost in
    the blur), bronze (region 3) with patches of green-gold (region 4). Returns {region: mesh}."""
    G = GEOM
    th = math.radians(G["back_deg"])
    u0 = np.array([math.cos(th), math.sin(th)])
    n0 = np.array([u0[1], -u0[0]])
    k = 1 - G["back_z"] / U                           # it is farther: a wider field
    e = [v * k * 1.15 for v in ext]
    half = math.hypot(e[1] - e[0], e[3] - e[2]) / 2
    fa, fb, fc = field(rng, 4.0, e), field(rng, G["back_R4_corr"], e), field(rng, 5.0, e)
    btx, bty = field(rng, G["back_tilt_corr"], e), field(rng, G["back_tilt_corr"], e)
    lohi = {r: tuple(float(v) for v in np.load(os.path.join(OUT, f"lut_{r}.npz"))["s"][[0, -1]]) for r in ("R2", "R3", "R4")}
    amean = {"R2": (G["back_R2_a"], 3.0), "R3": (224.0, 3.0), "R4": (192.0, 3.0)}
    bwx, bwy = field(rng, 10.0, e), field(rng, 10.0, e)
    kap = math.radians(0.5)
    ox = np.arange(-half, half, 0.1)
    o1 = np.cumsum(rng.standard_normal(len(ox)))
    o1 = np.convolve(o1 - np.linspace(o1[0], o1[-1], len(o1)), np.ones(30) / 30, "same")
    o1 = 2.2 * o1 / (np.abs(o1).max() + 1e-9)                # a smooth random phase across the barbs: locks of uneven width
    ph2 = rng.uniform(0, 2 * math.pi)
    runs = {"R2": [], "R3": [], "R4": []}
    ts = np.arange(-half, half, 1.0)
    ph = rng.uniform(0, 2 * math.pi)
    for o in np.arange(-half, half, G["back_spacing"]):
        c = o * n0 + np.multiply.outer(ts, u0) + np.multiply.outer(0.5 * kap * ts ** 2, n0)
        c = c + 1.5 * np.stack([bwx(c[:, 0], c[:, 1]), bwy(c[:, 0], c[:, 1])], -1)
        m = (c[:, 0] > e[0]) & (c[:, 0] < e[1]) & (c[:, 1] > e[2]) & (c[:, 1] < e[3])
        if m.sum() < 2:
            continue
        c = c[m]
        jit = rng.normal(0, 0.06, 2)
        phs = 2 * math.pi * o / G["back_clump_mm"] + ph + float(np.interp(o, ox, o1)) * 2 * math.pi / 2.2
        sn = math.sin(phs)
        if sn < G["back_gap"]:                        # between locks: a gap (the dark below shows)
            continue
        lock = math.radians(G["back_clump_deg"]) * math.sin(phs + 0.8 * rng.standard_normal())
        bR = G["back_rings"]
        rho = np.min([np.hypot((c[:, 0] - ce[0]) / ra[0], (c[:, 1] - ce[1]) / ra[1]) for ce, ra in bR["eyes"]], 0)
        rho = rho + bR["wobble"] * fb(c[:, 0], c[:, 1])
        e0, e1, e2 = bR["edges"]
        reg = np.where(rho < e0, "R2", np.where(rho < e1, "R3", np.where(rho < e2, "R4", "R3")))
        ex, ey, er = G["back_eye"]
        ineye = np.hypot((c[:, 0] - ex) / 1.3, c[:, 1] - ey) < er * (1 + 0.15 * fc(c[:, 0], c[:, 1]))
        reg = np.where(ineye, "R2", reg)
        for side in (+1, -1):
            ws = np.array([0.0, 0.5, 1.0])
            P2 = c[:, None, :] + side * n0[None, None, :] * (ws[None, :, None] * G["back_spacing"] / 2 * 1.05)
            P = np.concatenate([P2, np.full(P2.shape[:2] + (1,), G["back_z"])], -1)
            N = np.zeros(P.shape)
            N[..., 2] = 1
            N = lean(N, np.broadcast_to(np.r_[n0, 0], N.shape), np.full(N.shape[:2], lock))
            N = lean(N, np.broadcast_to(np.r_[side * n0, 0], N.shape), np.broadcast_to(0.05 + 0.2 * ws, N.shape[:2]))
            N = lean(N, np.broadcast_to(np.array([1.0, 0, 0]), N.shape), jit[0] + math.radians(G["back_tilt_deg"]) * btx(P2[..., 0], P2[..., 1]))
            N = lean(N, np.broadcast_to(np.array([0, 1.0, 0]), N.shape), math.radians(G["back_tilt_deg"]) * bty(P2[..., 0], P2[..., 1]))
            T = np.array([-n0[1], n0[0]])
            for r in ("R2", "R3", "R4"):
                a = amean[r][0] + amean[r][1] * (fa(P2[..., 0], P2[..., 1]) + 0.5 * rng.standard_normal())
                lo, hi = lohi[r]
                s = np.clip((a - lo) / (hi - lo), 0, 1)
                sel = (reg == r).astype(int)
                b = np.flatnonzero(np.diff(np.r_[0, sel, 0]))
                for k0, k1 in zip(b[::2], b[1::2]):
                    sl = slice(k0, min(k1 + 1, len(c)))
                    if sl.stop - sl.start >= 2:
                        runs[r].append((P[sl], N[sl], np.stack([(P2[sl] * T).sum(-1), (P2[sl] * n0).sum(-1), s[sl]], -1)))
    return {r: mesh(v) for r, v in runs.items() if v}


def to_world(P):
    P = np.asarray(P, float).copy()
    P[..., 0] *= -1
    return P


def fix_winding(P, N, T):
    """Faces wound so their geometric normal is on the side of the vertex normals (skill-notes 80)."""
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    flip = (fn * N[T].sum(1)).sum(1) < 0
    T = T.copy()
    T[flip] = T[flip][:, [0, 2, 1]]
    return T


def write_ply(path, P, N, T, UV=None):
    P = np.asarray(P, np.float32)
    N = np.asarray(N, np.float32)
    N = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)
    cols = [P, N] + ([np.asarray(UV, np.float32)] if UV is not None else [])     # UV: u, v[, lut_s]
    V = np.ascontiguousarray(np.concatenate(cols, 1).astype("<f4"))
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(P)}",
            "property float x", "property float y", "property float z",
            "property float nx", "property float ny", "property float nz"]
    if UV is not None:
        names = {2: [], 3: ["lut_s"], 5: ["lut_s", "lut_s2", "mix"]}[np.shape(UV)[1]]
        head += ["property float u", "property float v"] + [f"property float {n}" for n in names]
    head += [f"element face {len(T)}", "property list uchar int vertex_indices", "end_header"]
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = T
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.tobytes())
        f.write(face.tobytes())


def quad_light(w, group, c, n, size):
    """A square emitter of side `size` centred at c (image-plane coords), facing -n... facing the origin."""
    d = -c / np.linalg.norm(c)
    a = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < 0.99 else np.array([1.0, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(d, a)
    pts = np.array([c + size / 2 * (sa * a + sb * b) for sa in (-1, 1) for sb in (-1, 1)])
    pts = to_world(pts)
    nn = np.cross(pts[1] - pts[0], pts[2] - pts[0])
    if nn @ (-pts.mean(0)) <= 0:
        pts = pts[[1, 0, 3, 2]]
    w("AttributeBegin")
    w('  Material "diffuse" "rgb reflectance" [ 0.02 0.02 0.02 ]')
    w(f'  Attribute "light" "string group" [ "{group}" ]')
    w('  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 1 ]')
    w(f'  Shape "bilinearmesh" "point3 P" [ {" ".join(f"{v:.4f}" for v in pts.ravel())} ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")


def lights(w):
    for name, k in KEYS.items():
        t, f = math.radians(k["polar"]), math.radians(k["az"])
        c = k["dist"] * np.array([math.sin(t) * math.cos(f), math.sin(t) * math.sin(f), math.cos(t)])
        quad_light(w, name, c, None, k["size"])
    for bi, (p0, p1) in enumerate(BANDS):
        for qi in range(QUADS):
            for sub in range(6):
                a0 = 2 * math.pi * (qi + sub / 6) / QUADS
                a1 = 2 * math.pi * (qi + (sub + 1) / 6) / QUADS
                pts = []
                for pol in (p0, p1):
                    for az in (a0, a1):
                        t, f = math.radians(pol), az
                        pts.append([DOME * math.sin(t) * math.cos(f), DOME * math.sin(t) * math.sin(f), DOME * math.cos(t)])
                c = to_world(np.array(pts))
                n = np.cross(c[1] - c[0], c[2] - c[0])
                if n @ (-c.mean(0)) <= 0:
                    c = c[[1, 0, 3, 2]]
                w("AttributeBegin")
                w('  Material "diffuse" "rgb reflectance" [ 0.02 0.02 0.02 ]')
                w(f'  Attribute "light" "string group" [ "b{bi}q{qi}" ]')
                w('  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ 1 ]')
                w(f'  Shape "bilinearmesh" "point3 P" [ {" ".join(f"{v:.4f}" for v in c.ravel())} ] "integer indices" [ 0 1 2 3 ]')
                w("AttributeEnd")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--spp", type=int, default=256)
    ap.add_argument("--seed", type=int, default=17)
    a = ap.parse_args()
    res = tuple(int(v) for v in a.res.split("x"))
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    H = FRAME_W * 9 / 16
    mg = 3.0
    ext = (-FRAME_W / 2 - mg, FRAME_W / 2 + mg, -H / 2 - mg, H / 2 + mg)
    c0, R = arc_circle()
    runs = strips(a.seed, ext, c0, R, rng)
    stats = {}
    for part, name in (("V", "vane.ply"), ("L", "vane_L.ply")):
        P, N, UV, T = mesh(runs[part])
        P, N = to_world(P), to_world(N)
        T = fix_winding(P, N, T)
        write_ply(os.path.join(a.out, name), P, N, T, UV)
        stats[part] = {"runs": len(runs[part]), "triangles": len(T), "s_mean": float(UV[:, 2].mean())}
    for reg, (P, N, UV, T) in back_mesh(ext, rng).items():
        P, N = to_world(P), to_world(N)
        write_ply(os.path.join(a.out, f"back_{reg}.ply"), P, N, fix_winding(P, N, T), UV)
        stats[f"back_{reg}"] = {"triangles": len(T)}
    sh = SENSOR_W * res[1] / res[0]
    fov = math.degrees(2 * math.atan(0.5 * sh / V))
    Lw = []
    w = Lw.append
    w(f"# shot 17 round 2 (stacked peacock feathers), shots/17-peacock/scene.py seed {a.seed}; light groups key, top, bBqQ")
    w(f"LookAt 0 0 {U:.5f}  0 0 0  0 1 0")
    w(f'Camera "perspective" "float fov" [ {fov:.6f} ] "float lensradius" [ {FOCAL / (2 * FNUMBER):.5f} ] '
      f'"float focaldistance" [ {U:.5f} ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 8 ]')
    w(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] "string filename" [ "x.exr" ] '
      f'"string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] "bool rawsensor" true')
    w("WorldBegin")
    lights(w)
    w("AttributeBegin")
    w(f'  Material "diffuse" "rgb reflectance" [ {FLOOR_RGB[0]} {FLOOR_RGB[1]} {FLOOR_RGB[2]} ]')
    w('  Shape "bilinearmesh" "point3 P" [ -150 -150 -40  150 -150 -40  -150 150 -40  150 150 -40 ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    lutp = lambda reg: os.path.relpath(os.path.join(OUT, f"lut_{reg}.npz"), os.path.abspath(a.out))
    for reg, ply in (("V", "vane.ply"), ("R3", "vane_L.ply"), ("R2", "back_R2.ply"), ("R3", "back_R3.ply"), ("R4", "back_R4.ply")):
        two = (f'"string table2" [ "{lutp("R3")}" ] "string sattr2" [ "lut_s2" ] "string mixattr" [ "mix" ] ' if reg == "V" else "")
        w("AttributeBegin")
        w(f'  Material "barbule" "string table" [ "{lutp("R2" if reg == "V" else reg)}" ] {two}"float roughness" [ {ALPHA} ] "float anisotropy" [ {ANISO} ] '
          f'"string sattr" [ "lut_s" ] "rgb body" [ {" ".join(str(v) for v in (BODY_NEAR_RGB if ply.startswith("vane") else BODY_RGB))} ]')
        w(f'  Shape "plymesh" "string filename" [ "{ply}" ]')
        w("AttributeEnd")
    open(os.path.join(a.out, "scene.pbrt"), "w").write("\n".join(Lw) + "\n")
    json.dump({"f_number": FNUMBER, "magnification": round(MAG, 5), "sensor_width_mm": SENSOR_W, "focal_mm": FOCAL},
              open(os.path.join(a.out, "optics.json"), "w"))
    json.dump({"frame_w_mm": FRAME_W, "U": U, "V": V, "arc_centre_mm": c0.tolist(), "arc_R_mm": R, "geom": GEOM,
               "keys": KEYS, "stats": stats, "res": list(res)}, open(os.path.join(a.out, "framing.json"), "w"), indent=1)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
