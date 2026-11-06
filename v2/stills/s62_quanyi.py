"""Shot 62: the round back of a Ming armchair in huanghuali (黄花梨圈椅), three-quarters and a little above: the whole horseshoe of the yoke is the arc, from the top of the back down to the out-turned hand grip.

    python3 -I v2/stills/s62_quanyi.py sketch                 where everything falls in the frame, no render: out/v2/s62_quanyi/sketch.jpg
    python3 -I v2/stills/s62_quanyi.py [preview|mid|cand|final]    cand is final size, written beside the final

The versions before: first a wooden pipe, then a chair in matte plastic. The wood went flat because the mesh normals pointed inwards (the coat did not work) and because the colour was noise, not a history. Now (s62_wood.py, s62_shader.py):
- the wood is a solid, a 1-D growth history by radius (bands of gold and red-brown of very unequal width, rings, mineral lines) read through wandering shells; pores are dashes that follow the fibre and part round the buds (鬼脸);
- the depth is chatoyance: the fibres lean differently from one group of years to the next, and an anisotropic lobe tinted by the wood sits under the wax, so bands swap brightness as the camera moves;
- a yoke is scarfed from five pieces, each sawn from straight stock on a slant, so the figure runs in long diagonal strokes and does not match across a joint;
- wear by cause: wax broad and even where hands rub (top of the rail, the grip), dull and darker under the rail, grime in clouds under the rail at the top of the splat.
- under it the plain S-curved back splat, the two back posts, the goose-neck front posts (鹅脖) and the slim side spindles (联帮棍). The seat is below the frame and not modelled.

Measured at 100%, lit part of the splat of the final, sRGB: rgb 103,51,27, sat .73, detail hf 6.6 mf 8.6. Reference chair brought to this scale (26 px/cm): rgb 121,71,40, sat .67, hf 9.4, mf 15.1. So this is darker, a little more saturated, and has less detail than the photograph; the long diagonal strokes on the rail are weaker than on a real one. The reference is Christie's, kept out of the picture and out of git: only a comparison.

Stand-ins and estimates:
- sizes are estimates from general knowledge and from reference photographs, no particular chair is copied;
- the wood's colours, ring and band widths, lean of the fibres, pore size and the strength of the lobe (`sheen`) are chosen by eye against ref/huali_*; the lobe is added on top of the Principled, so energy is not strictly conserved;
- the corner brackets where the splat meets the yoke are one piece with the splat, with a hairline, where a real chair has separate 牙子;
- the scarf joint is a hairline without the wooden key of a real 楔钉榫.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

from kit import OUT, frame_camera, shoot, sstep
from s62_wood import n3, wood
from vessel import project, view_dir

NAME = "s62_quanyi"
SEED = 62
YAW = -32.0  # three-quarters, as a chair is always photographed: the near arm sweeps down across the frame and the far one goes behind the splat. Seen from the front it is a diagram
W, EL, DIST = 98.0, 17.0, 270.0
APEX = 0.16  # where the top of the back falls in the frame
PXCM = 50.0
FOOT = 42.0  # how far down the posts and the splat are built. The seat is under the frame and not modelled

# the yoke's right half, from the middle of the back to the grip: x across, y towards the back (the sitter's front is -y), z up, cm
YOKE = [(0.0, 0.0, 96.0), (10.0, -1.8, 95.2), (20.0, -7.5, 92.8), (26.8, -16.0, 88.8), (29.6, -26.0, 83.5), (30.0, -36.0, 77.6), (29.4, -44.0, 73.2), (29.9, -49.3, 71.2), (31.9, -53.2, 70.2), (34.5, -55.3, 69.6), (36.7, -55.5, 69.2), (37.9, -54.2, 68.8), (37.3, -52.8, 68.5), (36.0, -53.0, 68.3)]
JOINTS = (-46.0, -18.0, 18.0, 46.0)  # where the scarfs cross, arc length from the middle of the back
SCARF = 4.0  # how far a joint runs along the rail


def catmull(p, n=40):
    p = np.array(p, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    out = []
    for i in range(len(p) - 3):
        a, b, c, d = p[i], p[i + 1], p[i + 2], p[i + 3]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t**2 + (3 * b - a - 3 * c + d) * t**3))
    return np.vstack(out + [p[-2][None]])


def resample(c, ns):
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    t = np.linspace(0, s[-1], ns)
    return np.stack([np.interp(t, s, c[:, i]) for i in range(3)], 1), t


def tube(C, a, b, nv, up=(0.0, 0.0, 1.0)):
    """A swept section along centre line C: half-widths a (across) and b (along `up`) per row. Rows along C; columns round the section."""
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    up = np.array(up, float)
    N = up[None] - (T @ up)[:, None] * T
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    B = np.cross(T, N)
    th = np.linspace(2 * np.pi, 0, nv)  # this way round the mesh's normal (row x column) points outwards: dielectric and coat need it
    P = C[:, None] + (b[:, None] * np.cos(th))[..., None] * N[:, None] + (a[:, None] * np.sin(th))[..., None] * B[:, None]
    return P.astype(np.float32), th


# --- the chair ------------------------------------------------------------------------------------------------------
def grid_normal(P):
    """The mesh's own normal: row direction x column direction (studio_bpy.grid_mesh)."""
    n = np.cross(np.gradient(P, axis=0), np.gradient(P, axis=1))
    return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)


def finish(P, col, rough, fib, dent, patina=None):
    """The last of the surface: the dents and pores go into the geometry, and the wax is what it is. patina: 1 where hands and cloths have rubbed for centuries, 0 in the corners and under the rails."""
    n = grid_normal(P)
    Q = P + n * dent[..., None]
    if patina is None:
        patina = np.full(P.shape[:2], 0.5, np.float32)
    # polish: a rubbed place is a little paler and much more even; an unrubbed one is darker and duller. The wax's roughness is the broad soft highlight
    col = col * (0.5 + 0.62 * patina)[..., None]
    coatr = np.clip(0.34 - 0.13 * patina + 0.05 * n3(P[..., 0] / 3.1, P[..., 1] / 3.1, P[..., 2] / 3.1), 0.12, 0.6)
    return Q.astype(np.float32), {"col": np.clip(col, 0, 1).astype(np.float32), "rough": rough, "coatr": coatr.astype(np.float32), "fib": fib}


def yoke_line():
    right = np.array(YOKE, float)
    left = right[1:][::-1] * np.array([-1.0, 1.0, 1.0])
    c = catmull(np.vstack([left, right]), 60)
    for i in range(3):
        c[:, i] = gaussian_filter1d(c[:, i], 18, mode="nearest")  # a bent rail has no kinks in it
    return c


def yoke_at(c, y, side):
    """The yoke's centre line where it passes y on this side."""
    m = (c[:, 0] * side > 0)
    q = c[m]
    return q[np.argmin(np.abs(q[:, 1] - y))]


def build_yoke(c, dens):
    ns0 = 6000
    C, s = resample(c, ns0)
    L = s[-1]
    ns = int(L * PXCM * dens)
    C, s = resample(C, ns)
    s0 = s - 0.5 * L  # arc length from the middle of the back
    e = np.abs(s0) / (0.5 * L)
    # the section: thickest where it leaves the back, thinning along the arm, then spreading into the grip
    grip = sstep(0.8, 0.96, e)
    a = 1.32 - 0.24 * sstep(0.1, 0.65, e) - 0.22 * grip
    b = 1.32 - 0.24 * sstep(0.1, 0.65, e) - 0.22 * grip
    tip = np.clip((0.5 * L - np.abs(s0)) / 0.85, 0, 1)
    round_ = np.sqrt(np.maximum(1.0 - (1.0 - tip) ** 2, 0.0))
    # shaved by hand: never quite true
    hand = 1.0 + 0.012 * gaussian_filter1d(np.random.default_rng(SEED + 3).normal(size=ns), 2.0 * PXCM * dens, mode="nearest") * np.sqrt(2.0 * PXCM * dens) * 2
    a, b = a * round_ * hand, b * round_ * hand
    nv = int(11.0 * PXCM * dens)
    P, th = tube(C, a, b, nv)
    S0, TH = np.meshgrid(s0, th, indexing="ij")
    # which piece of wood: the scarf is a long slant across the rail
    ss = S0 + SCARF * np.sin(TH + 0.6)
    piece = np.zeros_like(ss, np.int32)
    for j in JOINTS:
        piece = piece + (ss > j)
    col, rough = np.zeros(P.shape, np.float32), np.zeros(P.shape[:2], np.float32)
    fib, dent = np.zeros(P.shape, np.float32), np.zeros(P.shape[:2], np.float32)
    edges = [-L, *JOINTS, L]
    pith = ((3.0, 5.0), (-2.0, 5.5), (2.0, 4.2), (-3.0, 4.5), (2.5, 6.0))
    tones = (1.0, 0.92, 1.04, 0.95, 1.0)
    # the stock is never sawn true to the rail, and the grain runs across it on a slant: this is what makes the long diagonal strokes on a real yoke
    skew = ((0.34, 0.1), (-0.42, 0.12), (0.38, -0.14), (-0.36, 0.16), (0.28, -0.1))
    for k in range(5):
        m = np.flatnonzero(np.any(piece == k, axis=1))
        i0, i1 = m[0], m[-1] + 1
        a0 = C[np.clip(np.searchsorted(s0, max(edges[k], s0[0])), 0, ns - 1)]
        a1 = C[np.clip(np.searchsorted(s0, min(edges[k + 1], s0[-1])), 0, ns - 1)]
        ax = (a1 - a0) / np.linalg.norm(a1 - a0)
        e1 = np.array([0.0, 0.0, 1.0]) - ax[2] * ax
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(ax, e1)
        ax = ax + skew[k][0] * e1 + skew[k][1] * e2
        cl, ro, fi, de = wood(P[i0:i1], 0.5 * (a0 + a1), ax, e1, pith[k], slope=0.06, tone=tones[k], seed=SEED + 10 * k, spread=(0.04, 1.02), line=1.6)
        mm = piece[i0:i1] == k
        col[i0:i1][mm] = cl[mm]
        rough[i0:i1][mm] = ro[mm]
        fib[i0:i1][mm] = fi[mm]
        dent[i0:i1][mm] = de[mm]
    # the hairline of each joint. The two pieces' dents must meet: a step there would catch the light all along the joint
    line = np.zeros_like(ss)
    near = np.zeros_like(ss)
    for j in JOINTS:
        line = np.maximum(line, sstep(0.05, 0.015, np.abs(ss - j)))
        near = np.maximum(near, sstep(0.5, 0.1, np.abs(ss - j)))
    dent = dent * (1.0 - near)
    col = col * (1.0 - 0.72 * line)[..., None]
    rough = rough + 0.2 * line
    # where it has been rubbed: the top of the rail, all of the grip; under the rail nobody's hand goes
    up = np.cos(TH)  # the section's column 0 is up
    patina = np.clip(0.45 + 0.45 * sstep(-0.6, 0.5, up) + 0.5 * grip[:, None] - 0.3 * sstep(-0.3, -0.9, up), 0, 1).astype(np.float32)
    return finish(P, col, rough, fib, dent, patina)


def post(d, name, pts, r, seed_tone, dens, grain=(0.0, 3.0)):
    C = catmull(pts, 30)
    L = np.linalg.norm(np.diff(C, axis=0), axis=1).sum()
    ns = int(L * 28.0 * dens)
    C, s = resample(C, ns)
    rr = np.interp(s / L, np.linspace(0, 1, len(r)), r)
    P, _ = tube(C, rr, rr, int(2 * np.pi * max(r) * 40.0 * dens), up=(1.0, 0.0, 0.0))
    ax = C[-1] - C[0]
    ax = ax / np.linalg.norm(ax) + np.array([0.09, 0.06, 0.0])
    cl, ro, fi, de = wood(P, C[ns // 2], ax, (1.0, 0.0, 0.0), grain, slope=0.05, tone=seed_tone, seed=sum(map(ord, name)))
    # darker towards the joint under the rail, where the cloth does not reach
    near = np.clip(np.linspace(1.0, 0.0, ns)[:, None] * 6.0 - 5.0, 0, 1)
    Q, at = finish(P, cl, ro, fi, de, np.broadcast_to(0.55 - 0.45 * near, P.shape[:2]).astype(np.float32))
    p = os.path.join(d, f"{name}.npz")
    np.savez(p, P=Q, **at)
    return p, P


SPLAT_KNOTS = ((2.3, 11.0, 2.5, 2.0), (0.4, 12.2, 1.4, 1.2), (-3.0, -3.5, 1.9, 1.6))  # x1, al, swell, r: the ghost faces, cm from (0, -6, 70)


def build_splat(c, d, dens):
    zt = float(c[len(c) // 2, 2]) - 0.5
    pxcm = PXCM * dens
    nv, nu = int((zt - FOOT) * pxcm), int(18.0 * pxcm)
    v = np.linspace(zt, FOOT, nv, dtype=np.float32)  # top row first: the mesh's normal (row x column) then faces the sitter, and the camera
    uu = np.linspace(-1.0, 1.0, nu, dtype=np.float32)
    t = (zt - v) / (zt - FOOT)
    flare = np.clip((v - (zt - 6.5)) / 6.5, 0, 1)
    hw = 4.9 + 2.1 * t + 1.1 * (1.0 - np.sqrt(np.maximum(1.0 - flare**2, 0.0)))  # narrow and straight-sided, wider at the foot. A wide board with a flared head was the most wrong thing in the first version
    y = -1.9 - 9.2 * t**1.4 + 2.6 * np.sin(np.pi * t)  # the S of a back that was shaped to a spine: this is what shows from three-quarters
    H = np.outer(hw, uu)
    Vv = np.outer(v, np.ones(nu, np.float32))
    # the board bows a very little across
    Yy = y[:, None] + 0.012 * (H**2)
    P = np.stack([H, Yy, Vv], -1).astype(np.float32)
    grain = dict(o=(0.0, -6.0, 70.0), a=(0.0, 0.17, 1.0), e1=(1.0, 0.0, 0.0), pith=(0.4, 3.2), slope=0.15, seed=SEED + 77, knots=SPLAT_KNOTS)
    cl, ro, fi, de = wood(P, **grain)
    # the hairline where the bracket joins the board
    br = sstep(0.05, 0.02, np.abs(np.abs(H) - (4.8 + 2.1 * t[:, None] + 0.12 * np.sin(Vv * 1.5)))) * sstep(zt - 7.0, zt - 6.2, Vv)
    cl = cl * (1.0 - 0.55 * br)[..., None]
    # grime gathers under the rail and in along the edges, in clouds, not in a line. On the reference it is near black
    top = sstep(zt - 7.5, zt - 0.2, Vv + 2.2 * n3(H / 3.0, Vv / 3.0, H * 0 + 2.0))
    edge = sstep(0.8, 1.0, np.abs(uu))[None] * np.ones_like(H)
    patina = np.clip(0.62 - 0.55 * top - 0.25 * edge + 0.1 * n3(H / 5.0, Vv / 7.0, H * 0 + 5.0), 0, 1).astype(np.float32)
    Q, at = finish(P, cl, ro, fi, de, patina)
    p = os.path.join(d, "splat.npz")
    np.savez(p, P=Q, **at)
    # its two edges, so that it has thickness, rounded
    edges = []
    for k, sgn in enumerate((-1.0, 1.0)):
        a = np.linspace(0, np.pi, 24, dtype=np.float32)
        if sgn < 0:
            a = a[::-1]  # the normal points outwards on both
        ex = sgn * (hw[:, None] + 0.25 * np.sin(a))
        ey = y[:, None] + 0.012 * (hw[:, None] ** 2) + 0.7 * (1 - np.cos(a))
        ez = np.outer(v, np.ones(24, np.float32))
        Pe = np.stack([ex, ey, ez], -1).astype(np.float32)
        ce, re, fe, de = wood(Pe, **grain)
        Qe, at = finish(Pe, ce, re, fe, de, np.full(Pe.shape[:2], 0.35, np.float32))
        pe = os.path.join(d, f"splat_edge{k}.npz")
        np.savez(pe, P=Qe, **at)
        edges.append(pe)
    return p, edges, P


def turn(P):
    """The chair stands turned by YAW about the back's vertical."""
    a = np.radians(YAW)
    c_, s_ = np.cos(a), np.sin(a)
    Q = P.copy()
    Q[..., 0] = c_ * P[..., 0] - s_ * P[..., 1]
    Q[..., 1] = s_ * P[..., 0] + c_ * P[..., 1]
    return Q


def turn_file(p):
    with np.load(p) as z:
        arrs = dict(z)
    arrs["P"] = turn(arrs["P"]).astype(np.float32)
    arrs["fib"] = turn(arrs["fib"]).astype(np.float32)  # world directions turn with it
    np.savez(p, **arrs)


def parts(c, d, dens):
    out = []
    for name, side, sign in (("rear", 1.0, "r"), ("rear", -1.0, "l")):
        top = yoke_at(c, -9.5, side)
        out.append(post(d, f"rear_{sign}", [top + (0, 0, 0.3), top + (0.18 * side, -1.1, -14.0), top + (0.42 * side, -2.3, -30.0), (top[0] + 0.62 * side, top[1] - 3.5, FOOT)], (1.26, 1.29, 1.33, 1.37), 0.97 if side > 0 else 1.02, dens, (2.0 * side, 3.5)))
    for side, sign in ((1.0, "r"), (-1.0, "l")):
        top = yoke_at(c, -41.0, side)
        out.append(post(d, f"goose_{sign}", [top + (0, 0, 0.3), top + (-0.3 * side, 1.3, -6.5), top + (-0.8 * side, -0.2, -13.0), top + (-1.0 * side, -3.4, -19.0), (top[0] - 1.2 * side, top[1] - 5.2, FOOT)], (1.1, 1.25, 1.38, 1.32, 1.3), 1.0, dens, (1.0 * side, 3.0)))
        top = yoke_at(c, -27.5, side)
        out.append(post(d, f"spindle_{sign}", [top + (0, 0, 0.3), top + (0.28 * side, -0.1, -9.0), top + (0.3 * side, -0.7, -19.0), (top[0] - 0.1 * side, top[1] - 1.5, FOOT)], (0.66, 0.74, 0.88, 1.02), 0.96, dens, (0.5 * side, 2.0)))
    return out


def camera_for():
    c = yoke_line()
    top = turn(c[len(c) // 2][None])[0]
    v = view_dir(-90.0, EL)
    tgt = np.array([top[0] + 1.0, top[1], top[2] - 12.0])
    focus = np.array([top[0], top[1] - 5.0, top[2] - 3.0])
    line = turn(c)
    for _ in range(8):
        cam = frame_camera(tgt, v, W, DIST, aperture_mm=24.0, focus_point=focus)
        x, y, _z = project(cam, line)
        tgt = tgt + np.array([(0.5 * (float(x.min()) + float(x.max())) - 0.5) * W, 0.0, (APEX - float(y.min())) * W * 9.0 / 16.0])
    return cam, c


def sketch():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cam, c = camera_for()
    im = np.full((720, 1280, 3), 24, np.uint8)
    seq = [turn(np.array(c))]
    tmp = os.path.join(d, "_sk")
    os.makedirs(tmp, exist_ok=True)
    for p, P in parts(c, tmp, 0.12):
        seq.append(turn(P[:, 0]))
    _, _, Ps = build_splat(c, tmp, 0.12)
    seq += [turn(Ps[:, 0]), turn(Ps[:, -1])]
    for q in seq:
        x, y, _ = project(cam, q)
        pts = np.round(np.stack([x * 1280, y * 720], 1)).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(im, [pts], False, (140, 190, 235), 2, cv2.LINE_AA)
    p = os.path.join(d, "sketch.jpg")
    cv2.imwrite(p, im)
    x, y, _ = project(cam, turn(c))
    print(p, "x", round(float(x.min()), 3), round(float(x.max()), 3), "y", round(float(y.min()), 3), round(float(y.max()), 3), flush=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "sketch":
        sketch()
        return
    tag = q
    if q == "cand":  # final size, written beside the final: the film reads final.*, and this has to pass a side-by-side first
        q = "final"
    dens = {"preview": 0.5, "mid": 0.75, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    cam, c = camera_for()
    P, at = build_yoke(c, dens)
    print("yoke", P.shape, flush=True)
    ypath = os.path.join(d, f"yoke.{q}.npz")
    at["fib"] = turn(at["fib"]).astype(np.float32)
    np.savez(ypath, P=turn(P), **at)
    files = [ypath]
    sp, edges, _ = build_splat(c, d, dens)
    files += [sp, *edges]
    for p, _P in parts(c, d, dens):
        files.append(p)
    for p in files[1:]:
        turn_file(p)
    shader = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s62_shader.py")
    meshes = [{"name": os.path.basename(p).split(".")[0], "npz": p, "shader_py": shader, "params": {"sheen": 0.3}} for p in files]
    tgt = np.array(cam["target"], float)
    lights = [
        # the long soft window over the chair, for its reflection only: the line of light that rides along the wood. The wood's body is lit by the key
        {"type": "gradient", "name": "strip", "loc": (tgt + np.array([-20.0, -30.0, 190.0])).tolist(), "target": tgt.tolist(), "size": [460, 170], "sigma": [130, 36], "L": 7.5, "rgb": [1.0, 0.94, 0.86], "hide_in_diffuse": True},
        # a pool of light from high on the left: it falls away down the splat and leaves the undersides dark
        {"name": "key", "loc": (tgt + np.array([-90.0, -120.0, 210.0])).tolist(), "target": (tgt + np.array([6.0, 0.0, 12.0])).tolist(), "size": [130, 130], "watts": 150000.0, "rgb": [1.0, 0.95, 0.88], "spread": 70.0},
        {"name": "fill", "loc": (tgt + np.array([170.0, -180.0, 90.0])).tolist(), "target": tgt.tolist(), "size": [190, 190], "watts": 8000.0, "rgb": [0.98, 0.97, 1.0], "hide_in_gloss": True},
        {"type": "gradient", "name": "edge", "loc": (tgt + np.array([120.0, 170.0, 60.0])).tolist(), "target": tgt.tolist(), "size": [80, 220], "sigma": [24, 70], "L": 6.0, "rgb": [1.0, 0.93, 0.84]},
    ]
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "diffuse_bounces": 4,
        "glossy_bounces": 4,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot(NAME, scene, q, tag=tag, develop={"exposure": 0.78, "contrast": 1.32, "saturation": 1.03, "black": 0.002, "grain": 1.15, "sharpen": 0.22, "halation": 0.04, "glare": 0.004, "vignette": 0.2})
    for p in files:
        os.remove(p)


main()
