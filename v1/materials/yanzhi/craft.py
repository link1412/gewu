"""胭脂红 card, round 3 (S8 r2): the craft layer on the card's bowl (docs/materials/yanzhi.md, "craft").

The round-2 card was a perfect lathe surface with a uniform enamel; the judges named that first (a perfect ellipse of
a rim, mirror-symmetric window reflections, a flat even red, a generic foot). Here the bowl gets what making it
leaves, every number in craft.json with its tag:
  - the form: six lobes (V notches at the rim fading to faint ribs down the wall), kiln ovality and a tilted lip;
  - the glaze's surface: a gentle undulation (random waves 4-25 mm, rms slope as craft.json), as geometry, so the
    lamps' reflections break up and both renderers see the same surface;
  - the enamel's column density c(theta, s): vertical streaks, slow patches, a run downwards, a pool in the angle
    between wall and foot, a soft top edge; a familymap of the film's transmittance (docs/textures.md) over a map in
    (u = angle / 2 pi, v = arc length from the sole (0) to the film's top (1)); the film mesh carries those UVs (its
    seam column doubled so u runs 0..1 without wrapping a triangle backwards).
The mean of c over the wall (pool excluded) is --c, so c stays comparable with the uniform cards.

    python3 -I materials/yanzhi/craft.py --c 0.5 --name craft-c050 [--no-craft]
        -> out/materials/yanzhi/card/<name>/bowl.pbrt (+ ply, film.npz, c.pfm, craft_info.json)
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
sys.path.insert(0, os.path.join(ROOT, "tests/optics"))
import card  # noqa: E402
from camera import LAM  # noqa: E402
from studio import write_ply  # noqa: E402
import gen_object as G  # noqa: E402

CRAFT = os.path.join(HERE, "craft.json")
MAP_W, MAP_H = 2048, 512
C_GRID = np.linspace(0.0, 2.0, 401)      # the familymap's rows, even (exact in Cycles)


def craft():
    return json.load(open(CRAFT))


def V(d, k):
    return d[k]["value"]


# --- the form --------------------------------------------------------------------------------------
def deform(P, cf, on=True):
    """Lobes, ovality and tilt as a smooth map of space (the same for glaze, body and film, so the layers keep their
    spacing to well under a micrometre)."""
    if not on:
        return P.copy()
    lo, wp = cf["lobes"], cf["warp"]
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    n = V(lo, "count")
    ph = np.radians(V(lo, "phase_deg"))
    step = 2 * np.pi / n
    dphi = np.abs((th - ph + step / 2) % step - step / 2)               # angular distance to the nearest notch
    notch = np.exp(-np.degrees(dphi) / V(lo, "notch_width_deg"))
    top = card.H_MM
    fade = np.clip(1 - (top - z) / V(lo, "fade_mm"), 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    wall = np.clip((z - 15.0) / 15.0, 0, 1)                             # no ribs on the foot and the floor
    depth = (V(lo, "rib_depth_mm") * wall + (V(lo, "notch_depth_mm") - V(lo, "rib_depth_mm")) * fade) * notch
    rn = np.maximum(r - depth * (r > 30), 0)
    zn = z - V(lo, "notch_depth_mm") * notch * fade                     # the lip dips at a notch
    e = V(wp, "ovality") * np.cos(2 * (th - np.radians(V(wp, "ovality_phase_deg")))) * np.clip(z / top, 0, 1)
    rn = rn * (1 + e)
    zn = zn + V(wp, "tilt_mm") * np.cos(th - np.radians(V(wp, "ovality_phase_deg") + 70)) * np.clip(z / top, 0, 1) ** 2
    k = np.where(r > 1e-9, rn / np.maximum(r, 1e-9), 1.0)
    return np.c_[x * k, y * k, zn]


def undulation(P, cf):
    """The glaze's height along its normal (mm): random plane waves in space, amplitude ~ 1/k (equal slope per wave),
    scaled to craft.json's rms slope (the in-surface gradient taken as 2/3 of the 3-D one, isotropic waves)."""
    gs = cf["glaze_surface"]
    rng = np.random.default_rng(gs["seed"])
    lam0, lam1 = V(gs, "wavelength_mm")
    m = 96
    lam = np.exp(rng.uniform(np.log(lam0), np.log(lam1), m))
    kv = rng.normal(size=(m, 3))
    kv /= np.linalg.norm(kv, axis=1, keepdims=True)
    kv *= (2 * np.pi / lam)[:, None]
    a = 1 / np.linalg.norm(kv, axis=1)
    phase = rng.uniform(0, 2 * np.pi, m)
    slope = np.sqrt((2 / 3) * np.sum(a ** 2 * np.sum(kv ** 2, 1) / 2))
    a *= np.radians(V(gs, "slope_rms_deg")) / slope
    h = np.zeros(len(P))
    for i in range(m):
        h += a[i] * np.cos(P @ kv[i] + phase[i])
    return h


def vertex_normals(P, T, N_ref):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for j in range(3):
        np.add.at(N, T[:, j], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    N[np.einsum("ij,ij->i", N, N_ref) < 0] *= -1
    return N


def revolve_open(R, Z, n_around):
    """An open band (the film): rows along the profile, n_around + 1 columns (the seam doubled), so its UVs run
    u 0..1. Returns P, N, T, and per-vertex (column, row)."""
    n2 = G.normals2d(R, Z)
    ph = 2 * np.pi * np.arange(n_around + 1) / n_around
    c, s = np.cos(ph), np.sin(ph)
    nr, nc = len(R), n_around + 1
    P = np.stack([np.outer(R, c), np.outer(R, s), np.repeat(Z[:, None], nc, 1)], -1).reshape(-1, 3)
    N = np.stack([np.outer(n2[:, 0], c), np.outer(n2[:, 0], s), np.repeat(n2[:, 1:2], nc, 1)], -1).reshape(-1, 3)
    i, j = np.meshgrid(np.arange(nr - 1), np.arange(nc - 1), indexing="ij")
    a, b, cc, d = i * nc + j, (i + 1) * nc + j, (i + 1) * nc + j + 1, i * nc + j + 1
    T = np.concatenate([np.c_[a.ravel(), b.ravel(), cc.ravel()], np.c_[a.ravel(), cc.ravel(), d.ravel()]])
    gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    flip = np.einsum("ij,ij->i", gn, N[T].mean(1)) < 0
    T[flip] = T[flip][:, [0, 2, 1]]
    col, row = np.meshgrid(np.arange(nc), np.arange(nr))
    return P, N, T, col.ravel(), row.ravel()


def seam_normals(N, col, row, nc):
    """The doubled seam column: both copies get the mean of the two (a closed band's normal)."""
    a = np.nonzero(col == 0)[0]
    b = np.nonzero(col == nc - 1)[0]
    m = N[a] + N[b]
    m /= np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)
    N[a], N[b] = m, m
    return N


# --- the enamel's thickness -----------------------------------------------------------------------
def gauss_field(shape, sig_px, rng):
    """Unit-variance gaussian random field, periodic in both axes (wraps in u as the bowl does), gaussian
    correlation of sig_px = (rows, cols)."""
    f = np.fft.fft2(rng.normal(size=shape))
    ky = np.fft.fftfreq(shape[0])[:, None]
    kx = np.fft.fftfreq(shape[1])[None, :]
    g = np.exp(-2 * np.pi ** 2 * ((ky * sig_px[0]) ** 2 + (kx * sig_px[1]) ** 2))
    x = np.real(np.fft.ifft2(f * g))
    return (x - x.mean()) / x.std()


def c_map(cf, s_mm, s_foot, s_top, r_mm, c0, on=True):
    """c(v, u) on MAP_H x MAP_W, row 0 the film's top (pbrt's t = 1). s_mm: arc length from the film's top down to
    the sole; s_foot: where the wall meets the foot; r_mm: the radius at each row (for mm per pixel round)."""
    et = cf["enamel_thickness"]
    rows = np.linspace(0, s_top, MAP_H)                  # arc length from the top, per map row
    if not on:
        return np.full((MAP_H, MAP_W), c0), {}
    rng = np.random.default_rng(et["seed"])
    r_row = np.interp(rows, s_mm, r_mm)
    mm_u = 2 * np.pi * np.median(r_row[rows < s_foot]) / MAP_W          # mm per column (at the wall's median radius)
    mm_v = s_top / (MAP_H - 1)
    w0, w1 = V(et, "streak_width_mm")
    st = sum(gauss_field((MAP_H, MAP_W), (40.0 / mm_v, w / mm_u), rng) for w in np.geomspace(w0, w1, 3))
    st = (st - st.mean()) / st.std()
    pa = gauss_field((MAP_H, MAP_W), (20.0 / mm_v, 20.0 / mm_u), rng)
    t = np.clip(rows / s_foot, 0, 1)
    down = 1 + V(et, "down_gradient") * (t - 0.5)
    pool = 1 + V(et, "pool_at_foot") * np.exp(-0.5 * ((rows - s_foot) / 2.5) ** 2)
    f = (1 + V(et, "streak_rms") * st) * (1 + V(et, "patch_rms") * pa) * down[:, None]
    wall = (rows > 2 * V(et, "lip_taper_mm")) & (rows < s_foot - 6)
    f /= f[wall].mean()                                  # mean c over the wall = c0
    # S8 r3: the top edge wanders round the bowl (lip_wander_mm), the ring is thinner (foot_wear) and its standing
    # edge more so, raggedly (foot_edge_wear); the rest as round 2 (the same random fields, drawn first)
    rng3 = np.random.default_rng(et["seed"] + 1000)
    if "lip_wander_mm" in et:
        lo, hi = V(et, "lip_wander_mm")
        g = gauss_field((8, MAP_W), (2.0, 8.0 / mm_u), rng3)[0]
        g = (g - g.min()) / (g.max() - g.min())
        off = lo + (hi - lo) * g ** 1.5
    else:
        off = np.zeros(MAP_W)
    taper = np.clip((rows[:, None] - off[None, :]) / V(et, "lip_taper_mm"), 0, 1)
    taper = taper * taper * (3 - 2 * taper)
    foot = np.ones((MAP_H, MAP_W))
    if "foot_wear" in et:
        t1 = np.clip((rows - (s_foot + 3.0)) / 1.5, 0, 1)
        foot *= (1 + (V(et, "foot_wear") - 1) * t1)[:, None]
        e = np.clip((rows - (s_top - 1.2)) / 0.6, 0, 1)
        rag = np.clip(1 + 0.4 * gauss_field((MAP_H, MAP_W), (1.0 / mm_v, 6.0 / mm_u), rng3), 0, 2)
        foot *= 1 + (V(et, "foot_edge_wear") - 1) * e[:, None] * rag
        foot = np.maximum(foot, 0.02)
    c = c0 * f * pool[:, None] * taper * foot
    info = {"mm_per_px_u_at_wall": mm_u, "mm_per_px_v": mm_v, "s_foot_mm": float(s_foot), "s_top_mm": float(s_top),
            "wall_mean": float(c[wall].mean()), "wall_rms_rel": float(c[wall].std() / c[wall].mean()),
            "max": float(c.max())}
    return c, info


def specks(cf, R, Z, i_out, h):
    """S8 r3: dark specks (iron, kiln grit) under the inside's glaze: small discs (8-gons) on the body, GAP above it
    (between body and glaze, as the film), placed uniformly by area over the inside below the lip (craft.json)."""
    sp = cf["specks"]
    rng = np.random.default_rng(sp["seed"])
    n = int(V(sp, "count_inside"))
    d0, d1 = V(sp, "diameter_mm")
    j1 = int(np.argmax(Z[:i_out] > card.H_MM - 3.0)) or i_out      # the inside, up to 3 mm under the lip's top
    r, z = R[:j1], Z[:j1]
    t = np.gradient(np.c_[r, z], axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    nin = np.c_[-t[:, 1], t[:, 0]]                       # normal of the run (axis outwards, up the inside)
    nin[nin[:, 1] < 0] *= -1                             # into the bowl's cavity: up on the floor, axis-wards on the wall
    ds = np.r_[np.hypot(np.diff(r), np.diff(z)), 0]
    w = 2 * np.pi * np.maximum(r, 1e-3) * ds
    k = rng.choice(len(r), n, p=w / w.sum())
    th = rng.uniform(0, 2 * np.pi, n)
    dia = np.exp(rng.uniform(np.log(d0), np.log(d1), n))
    P, T, N = [], [], []
    for i in range(n):
        ct, st_ = np.cos(th[i]), np.sin(th[i])
        nn = np.array([nin[k[i], 0] * ct, nin[k[i], 0] * st_, nin[k[i], 1]])
        nn /= np.linalg.norm(nn)
        c = np.array([r[k[i]] * ct, r[k[i]] * st_, z[k[i]]]) - (h - card.GAP) * nn   # on the body, GAP above it
        a = np.cross(nn, [0, 0, 1.0]) if abs(nn[2]) < 0.9 else np.cross(nn, [1.0, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(nn, a)
        base = len(P)
        P.append(c)
        for m in range(8):
            ang = 2 * np.pi * m / 8
            P.append(c + 0.5 * dia[i] * (np.cos(ang) * a + np.sin(ang) * b))
        N += [nn] * 9
        for m in range(8):
            T.append([base, base + 1 + m, base + 1 + (m + 1) % 8])
    return np.array(P), np.array(N), np.array(T), {"count": n, "diameter_mm": [float(dia.min()), float(dia.max())]}


def write_pfm1(path, img):
    img = np.ascontiguousarray(img, dtype="<f4")
    with open(path, "wb") as f:
        f.write(f"Pf\n{img.shape[1]} {img.shape[0]}\n-1.0\n".encode())
        f.write(img[::-1].tobytes())


def make(a):
    cf = craft()
    mat = card.material()
    gl, en = mat["glaze"], mat["enamel"]
    h, eta, alpha = gl["thickness_mm"]["value"], gl["eta"]["value"], gl["ggx_alpha"]["value"]
    rho = mat["body"]["albedo"]["value"]
    on = not a.no_craft
    R, Z, i_out, i_sole = card.profile()
    glaze = [(R, Z)]
    body = G.offset(glaze, h)
    Rb, Zb = body[0]
    top = card.H_MM - en["white_lip_mm"]["value"]
    j0 = i_out + int(np.argmax(Z[i_out:i_sole] <= top))
    fr, fz = Rb[j0:i_sole + 1], Zb[j0:i_sole + 1]
    nf = G.normals2d(fr, fz)
    fr, fz = fr + card.GAP * nf[:, 0], fz + card.GAP * nf[:, 1]
    d = os.path.join(card.OUT, a.name)
    os.makedirs(d, exist_ok=True)
    stats = {}
    for name, pieces in (("glaze", glaze), ("body", body)):
        P, N, T = G.revolve(pieces, card.N_AROUND)
        P2 = deform(P, cf, on)
        N2 = vertex_normals(P2, T, N)
        if name == "glaze" and on:
            hgt = undulation(P2, cf)
            P2 = P2 + hgt[:, None] * N2
            N2 = vertex_normals(P2, T, N2)
            stats["undulation_rms_um"] = float(hgt.std() * 1e3)
            stats["undulation_max_um"] = float(np.abs(hgt).max() * 1e3)
            # the realised slope: angle between the undulated and the plain normals
            Nn = vertex_normals(deform(P, cf, on), T, N)
            stats["slope_rms_deg_realised"] = float(np.degrees(np.sqrt(np.mean(np.arccos(np.clip(
                np.einsum("ij,ij->i", N2, Nn), -1, 1)) ** 2))))
        write_ply(os.path.join(d, f"bowl_{name}.ply"), P2, N2, T)
    # the film, with UVs
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(fr), np.diff(fz)))])
    jf = int(np.argmin(np.hypot(fr - 43.0, fz - 14.1)))             # the wall meets the foot ring (card.FOOT)
    P, N, T, col, row = revolve_open(fr, fz, card.N_AROUND)
    P2 = deform(P, cf, on)
    N2 = seam_normals(vertex_normals(P2, T, N), col, row, card.N_AROUND + 1)
    uv = np.c_[col / card.N_AROUND, 1 - s[row] / s[-1]]
    write_ply(os.path.join(d, "bowl_film.ply"), P2, N2, T, uv)
    cm, info = c_map(cf, s, s[jf], s[-1], fr, a.c, on)
    write_pfm1(os.path.join(d, "c.pfm"), cm)
    k = card.kappa(mat)
    np.savez(os.path.join(d, "film.npz"), lambda_nm=LAM, c=C_GRID, R=np.exp(-np.outer(C_GRID, k)))
    body_line = f'Material "diffuse" "spectrum reflectance" [ 360 {rho} 830 {rho} ]'
    if a.body_rt:
        # a test (S8 r2): a translucent body, pbrt's diffusetransmission on both faces of the body's shell (light
        # crosses the wall in two diffuse transmissions: t^2 / (1 - r^2) through it) [A, not a porcelain model]
        br, bt = (float(x) for x in a.body_rt.split(","))
        body_line = (f'Material "diffusetransmission" "spectrum reflectance" [ 360 {br:g} 830 {br:g} ] '
                     f'"spectrum transmittance" [ 360 {bt:g} 830 {bt:g} ]')
    speck_block = ""
    if on and "specks" in cf:
        Ps, Ns, Ts, ns = specks(cf, R, Z, i_out, h)
        Ps = deform(Ps, cf, on)
        write_ply(os.path.join(d, "bowl_specks.ply"), Ps, Ns, Ts)
        sa = V(cf["specks"], "albedo")
        speck_block = (f'AttributeBegin\n  Material "diffuse" "spectrum reflectance" [ 360 {sa:g} 830 {sa:g} ]\n'
                       f'  Shape "plymesh" "string filename" [ "bowl_specks.ply" ]\nAttributeEnd\n')
        stats["specks"] = ns
    with open(os.path.join(d, "bowl.pbrt"), "w") as f:
        f.write(f"""# 胭脂红 card with its craft layer (materials/yanzhi/craft.py, craft.json): Met 1971.180.248's form,
# lobed, warped, its glaze undulating; the enamel's column density a map, mean over the wall {a.c:g} g/m^2
Texture "yz_c" "spectrum" "familymap" "string family" "film.npz" "string map" "c.pfm" "string wrap" "clamp"
AttributeBegin
  Material "dielectric" "float eta" [ {eta} ] "float roughness" [ {alpha} ] "bool remaproughness" false "bool refractivenee" true
  Shape "plymesh" "string filename" [ "bowl_glaze.ply" ]
AttributeEnd
AttributeBegin
  {body_line}
  Shape "plymesh" "string filename" [ "bowl_body.ply" ]
AttributeEnd
AttributeBegin
  Material "thindielectric" "float eta" [ 1 ] "texture transmittance" "yz_c"
  Shape "plymesh" "string filename" [ "bowl_film.ply" ]
AttributeEnd
""" + speck_block)
    out = {"c_mean_wall": a.c, "craft": on, "map": info, **stats}
    json.dump(out, open(os.path.join(d, "craft_info.json"), "w"), indent=1)
    print("->", d, json.dumps(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", type=float, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--no-craft", action="store_true", help="the plain lathe bowl and a uniform c (a control)")
    ap.add_argument("--body-rt", help="R,T: a translucent body (diffusetransmission), a test")
    make(ap.parse_args())


if __name__ == "__main__":
    main()
