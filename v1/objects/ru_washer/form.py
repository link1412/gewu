"""The Ru washer's form: a lathe profile and the camera of the museum photo, solved together from the photo's edges
(measure.py) with the museum's diameter as the scale.

HEIGHT: the museum's record (diameter 12.8 cm, overall 3.8 cm; checked against the CMA open-access record) does not
fit the photo: with D = 128 mm the fitted height is 32.96 +- 0.13 mm (H / D = 0.257 against the record's 0.297).
So the height is fitted by default and the conflict is reported; fit --museum-height holds it at 38 mm instead.

    python3 -I objects/ru_washer/form.py fit      [--edges out/ru/washer/edges.json]   -> form.json, photo_camera.json
    python3 -I objects/ru_washer/form.py show                                           (the profile's numbers)

Object frame: mm, z up along the axis, z = 0 on the ground (the foot ring's lowest point), the axis at x = y = 0;
right-handed. The profile (r, z) is the glaze's OUTER surface: that is what the photo shows and what the museum
measured (Cleveland Museum of Art 1957.40: diameter 12.8 cm, height 3.8 cm [M]). washer.py derives the body from it
(inwards by the glaze thickness) and the glaze shell.

FOOT_TOP: the photo shows a thin bright line on the front of the lower wall, ~45 px above the top of the foot
ring's lit face. It was first taken for the ring's top edge, which made the ring 5 mm tall at the front while the
outline at the ring's two ends looked only ~55 px (~2.7 mm) tall; so it is not fitted (the final fit, which does
not use it, puts the crease 7.9 px (median) from it, so it may be the crease after all). What it is is not known (a ridge left by trimming, or a highlight
band on the curved underside); measure.py still finds it and fit reports its distance to the crease's circle.
There is no ledge: the wall leaves the ring's top at a concave crease (a free ledge, tried, came out as an undercut
slot, not a form).

The profile is a polygon of sharp corners with each corner rounded by a fillet, and a Bezier for the outer wall:
  base underside (axis) -> foot inner face -> foot bottom -> foot outer face (bottom corner = the bead) -> foot top
  -> outer wall (quintic Bezier, vertical where it meets the lip) -> lip (a half round) -> inner wall (the
  outer wall moved inwards by the wall thickness) -> inner floor (to the axis).
What the photo shows fixes the outer side from the foot's bottom to the lip ([M], fitted): the foot ring's outer
face (radius at the bottom and the top, height), the outer wall and the height; the lip's thickness is measured
apart (LIP_MM). The photo is at
~9 deg elevation: the inside below the far wall's upper half, the floor and the base are not seen, so the inner
wall's thickness, the floor and the foot's inner side are [A] (ASSUMED below, with reasons).

Camera: a pinhole with its principal point at the photo's centre [A: the museum's photo may be cropped from a larger
frame; a shifted principal point is nearly the same as a small turn of the camera, which is fitted], square pixels,
no distortion [A]. Fitted: the focal length in pixels, the camera's distance and height relative to the washer, and
its yaw, pitch and roll. Its residuals are the distances, in photo pixels, from each edge point to the projected
edge of the fitted form (the outline of a surface of revolution: its contour generator, solved per profile point
in closed form, contour_points).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EDGES = os.path.join(ROOT, "out/ru/washer/edges.json")
FORM = os.path.join(HERE, "form.json")
CAMERA = os.path.join(HERE, "photo_camera.json")
FIT_LOG = os.path.join(ROOT, "out/ru/washer/fit.json")

DIAMETER_MM = 128.0       # [M] CMA 1957.40, the museum's record: the widest diameter (at the rim)
HEIGHT_MM = 38.0          # [M] CMA 1957.40: ground to the top of the lip ("Overall: 3.8 cm")
REF_Z = 19.0              # the camera is placed relative to the axis point this high (a parametrisation only)
LIP_MM = 1.4              # [M] the lip's thickness (a half round of radius LIP_MM / 2): the band of thin glaze over
                          # the lip, seen edge-on at the rim's two ends, is 25-28 px wide at 19.8 px/mm (rows 840-880;
                          # measure by G - R < 3 from the outline inwards); fitted, it ran to its bound (0.8 mm), the
                          # outline barely depends on it
FIT_SETS = ("outline_top", "outline_side", "outline_bottom", "lip_front")   # foot_top: reported, not fitted (FOOT_TOP)
PHOTO_SIZE = (3400, 1942)

# ASSUMED [A], not seen in the photo (it looks at the washer from ~9 deg above the ground: the floor, the lower inner
# wall, the base and the foot's inner side are hidden). Ru washers are thin-bodied and fully glazed, fired on spurs
# set under the base; these are plain choices of that kind, to be replaced by a section if one is found.
ASSUMED = {
    "wall_mm": {"value": 3.0, "why": "the body's wall thickness below the lip (with the glaze); the lip itself is "
                                    "measured (lip_mm); the wall thickens from the lip to this over the upper third"},
    "floor_z_mm": {"value": 7.0, "why": "the inner floor's height above the ground (the base ~5 mm thick over its "
                                       "recessed underside); where the inner wall ends higher, the floor is there"},
    "floor_fillet_mm": {"value": 6.0, "why": "the inner floor turns into the inner wall in a broad curve, as a thrown "
                                            "washer does"},
    "base_under_frac": {"value": 0.6, "why": "the base's underside inside the foot ring, recessed above the ground "
                                             "by this fraction of the ring's measured height"},
    "foot_width_mm": {"value": 4.5, "why": "the foot ring's thickness at its bottom (its inner face is hidden)"},
    "bead_mm": {"value": 1.2, "why": "the foot ring's rounded bottom edge: its bright band in the photo is ~1.5 mm "
                                    "tall (read off by eye, 30 px at 20 px/mm)"},
    "foot_top_fillet_mm": {"value": 0.8, "why": "the crease where the outer wall meets the foot ring's outer face "
                                               "(concave): rounded, as glaze pooled in it would round it"},
    "foot_inner_fillets_mm": {"value": 0.8, "why": "the foot ring's inner edges and the base underside's corner"},
}

# the fitted parameters
FIT_PARAMS = [
    # name, start (a solution found before; the fit is local), lower, upper, typical change (x_scale)
    # camera
    ("f_px", 11877.0, 3000.0, 80000.0, 100.0),
    ("dist_mm", 612.0, 150.0, 6000.0, 5.0),    # from the camera to the point on the axis REF_Z above the ground
    ("elev_deg", 10.09, 0.0, 40.0, 0.05),      # the camera's elevation seen from that point
    ("dyaw_deg", 0.054, -10.0, 10.0, 0.01),    # the view direction's turn away from that point (right +)
    ("dpitch_deg", -1.17, -10.0, 10.0, 0.01),  # ... and its tilt (down +)
    ("roll_deg", 0.165, -5.0, 5.0, 0.05),
    # profile
    ("r_foot_bottom", 43.6, 30.0, 60.0, 0.2),  # the foot ring's outer face, extended to the ground (sharp corner)
    ("r_foot_top", 43.4, 30.0, 60.0, 0.2),     # ... at the ring's top, where the wall leaves it (sharp corner)
    ("h_foot", 2.8, 1.0, 10.0, 0.2),            # the ring's height (ground to its top)
    ("wall_a", 6.0, 0.5, 30.0, 0.5),            # Bezier: the first control leg's length
    ("wall_alpha_deg", 12.0, 0.0, 60.0, 1.0),  # ... and its angle above the horizontal (the wall rises from the
                                                # crease: a negative angle, tried, made an undercut over the ring)
    ("wall_p2r", 50.0, 35.0, 66.0, 0.5), ("wall_p2z", 8.5, 2.0, 30.0, 0.5),
    ("wall_p3r", 58.0, 35.0, 66.0, 0.5), ("wall_p3z", 18.0, 5.0, 36.0, 0.5),
    ("wall_b", 12.0, 0.5, 30.0, 0.5),           # the last control leg's length (vertical, under the lip)
    ("height_mm", 33.1, 25.0, 50.0, 0.2),       # ground to the lip's top: fitted, see HEIGHT below
]
NAMES = [p[0] for p in FIT_PARAMS]
CAM_NAMES = NAMES[:6]


# --- the profile ----------------------------------------------------------------------------------------------
def bezier(P, n):
    P = np.asarray(P, float)
    k = len(P) - 1
    t = np.linspace(0, 1, n)[:, None]
    out = np.zeros((n, 2))
    for i in range(k + 1):
        out += math.comb(k, i) * t ** i * (1 - t) ** (k - i) * P[i]
    return out


def resample(C, step):
    """A polyline at even arc-length spacing no larger than step (its ends kept)."""
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
    n = max(2, int(math.ceil(s[-1] / step)) + 1)
    t = np.linspace(0, s[-1], n)
    return np.c_[np.interp(t, s, C[:, 0]), np.interp(t, s, C[:, 1])]


def at_length(C, s, q):
    return np.array([np.interp(q, s, C[:, 0]), np.interp(q, s, C[:, 1])])


def fillet(C, lab, i, rho, room, label):
    """Round the corner at index i of the dense polyline C (labels lab) with an arc of radius rho, tangent to the
    polyline's chords at the distance L = rho tan(turn / 2) along it on either side; L is held to `room` (and rho
    shrunk to match) so that the fillet stays clear of the next corner. Returns the new (C, lab, rho used)."""
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
    L = min(room, 0.5)
    for _ in range(3):
        pa, pb = at_length(C, s, s[i] - L), at_length(C, s, s[i] + L)
        d_in, d_out = C[i] - pa, pb - C[i]
        d_in /= np.linalg.norm(d_in)
        d_out /= np.linalg.norm(d_out)
        turn = math.atan2(d_in[0] * d_out[1] - d_in[1] * d_out[0], float(d_in @ d_out))
        if abs(turn) < 1e-4:
            return C, lab, 0.0
        L = rho * math.tan(abs(turn) / 2)
        if L > room:
            L, rho = room, room / math.tan(abs(turn) / 2)
    pa, pb = at_length(C, s, s[i] - L), at_length(C, s, s[i] + L)
    centre = pa + rho * np.sign(turn) * np.array([-d_in[1], d_in[0]])
    a0 = math.atan2(*(pa - centre)[::-1])
    a1 = math.atan2(*(pb - centre)[::-1])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    m = 161                                    # fixed, so that the profile's points move smoothly with the parameters
    w = np.linspace(0, 1, m)
    rad = (1 - w) * np.linalg.norm(pa - centre) + w * np.linalg.norm(pb - centre)
    arc = centre + rad[:, None] * np.c_[np.cos(a0 + da * w), np.sin(a0 + da * w)]
    ia = int(np.searchsorted(s, s[i] - L, side="right"))
    ib = int(np.searchsorted(s, s[i] + L, side="left"))
    C = np.vstack([C[:ia], arc, C[ib:]])
    lab = np.concatenate([lab[:ia], np.full(m, label, dtype=lab.dtype), lab[ib:]])
    return C, lab, rho


def params_dict(x, names=None):
    p = dict(zip(names or NAMES, map(float, x)))
    p.setdefault("lip_mm", LIP_MM)
    return p


def line(P, Q, n):
    """n points from P to Q (a fixed count: the fit needs points that move smoothly with the parameters)."""
    w = np.linspace(0, 1, n)[:, None]
    return (1 - w) * np.asarray(P, float) + w * np.asarray(Q, float)


def resample_n(C, n):
    """A polyline at n points evenly spaced in arc length."""
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
    t = np.linspace(0, s[-1], n)
    return np.c_[np.interp(t, s, C[:, 0]), np.interp(t, s, C[:, 1])]


def closed_profile(p, assumed=None, n_wall=1500, inner=True):
    """The whole cross-section of the glaze's outer surface, as one dense polyline (r, z) with a label per point,
    run from the axis under the base, out along the base's underside, down the foot ring's inner face, along its
    bottom, up its outer face, over its top and the ledge, up the outer wall, over the lip, down the inner wall and
    along the floor to the axis. Labels: base foot_inner foot_bottom face ledge wall lip inner floor, and the
    rounded corners c_base c_foot_inner bead foot_top junction c_floor. inner=False stops after the lip (the fit)."""
    A = {k: v["value"] for k, v in (assumed or ASSUMED).items()}
    H, R, t = p.get("height_mm", HEIGHT_MM), DIAMETER_MM / 2, p.get("lip_mm", LIP_MM)
    rb, rt, hf = p["r_foot_bottom"], p["r_foot_top"], p["h_foot"]
    rj = rt                       # the wall leaves the ring's top: a concave crease, no ledge (see FOOT_TOP)
    rfi, zbu = rb - A["foot_width_mm"], A["base_under_frac"] * hf
    if not (0 < zbu < hf and 0 < rfi < min(rb, rt, rj)):
        raise ValueError("the foot ring and the base do not fit together")
    corners = [(0.0, zbu), (rfi, zbu), (rfi, 0.0), (rb, 0.0), (rt, hf), (rj, hf)]
    names = ["base", "foot_inner", "foot_bottom", "face", "ledge"]
    pieces, labs = [], []
    for k in range(len(corners) - 1):
        if k == 4 and abs(rj - rt) < 1e-3:
            continue
        seg = line(corners[k], corners[k + 1], (2400, 300, 300, 400, 300)[k])[:-1]
        pieces.append(seg)
        labs.append(np.full(len(seg), names[k], dtype="<U12"))
    al = math.radians(p["wall_alpha_deg"])
    P0, P5 = np.array([rj, hf]), np.array([R, H - t / 2])
    Bz = np.array([P0, P0 + p["wall_a"] * np.array([math.cos(al), math.sin(al)]), [p["wall_p2r"], p["wall_p2z"]],
                   [p["wall_p3r"], p["wall_p3z"]], P5 - np.array([0, p["wall_b"]]), P5])
    wall = bezier(Bz, n_wall)
    pieces.append(wall[:-1])
    labs.append(np.full(len(wall) - 1, "wall", dtype="<U12"))
    ang = np.linspace(0, math.pi, 3000)
    lip = np.c_[R - t / 2 + t / 2 * np.cos(ang), H - t / 2 + t / 2 * np.sin(ang)]
    pieces.append(lip if not inner else lip[:-1])
    labs.append(np.full(len(pieces[-1]), "lip", dtype="<U12"))
    floor_z = None
    if inner:
        # the inner wall: the outer wall moved inwards along its normal by the wall's thickness, the lip's at the
        # top growing to wall_mm over the upper third of the wall (smoothstep) [A]
        nw = normals(wall)
        sw = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(wall, axis=0).T))])
        u = np.clip((sw[-1] - sw) / (sw[-1] / 3), 0, 1)
        thick = t + (A["wall_mm"] - t) * u * u * (3 - 2 * u)
        inn = (wall - thick[:, None] * nw)[::-1]                 # from the lip down
        zf = A["floor_z_mm"]
        below = np.nonzero(inn[:, 1] <= zf)[0]
        if len(below):
            j = below[0]
            w0 = (inn[j - 1, 1] - zf) / (inn[j - 1, 1] - inn[j, 1])
            end = inn[j - 1] + w0 * (inn[j] - inn[j - 1])
            inn = np.vstack([inn[:j], end])
            floor_z = zf
        else:
            floor_z = float(inn[-1, 1])                          # the inner wall ends above zf: the floor there
        inn = resample_n(inn, 1500)
        pieces.append(inn[:-1])
        labs.append(np.full(len(inn) - 1, "inner", dtype="<U12"))
        fl = line(inn[-1], (0.0, floor_z), 1200)
        pieces.append(fl)
        labs.append(np.full(len(fl), "floor", dtype="<U12"))
    C = np.vstack(pieces)
    lab = np.concatenate(labs)
    # the fillets, from the last corner back (so that earlier indices hold)
    fil = [("c_base", (rfi, zbu), A["foot_inner_fillets_mm"]), ("c_foot_inner", (rfi, 0.0), A["foot_inner_fillets_mm"]),
           ("bead", (rb, 0.0), A["bead_mm"]), ("foot_top", (rt, hf), A["foot_top_fillet_mm"])]
    if inner:
        fil.append(("c_floor", tuple(inn[-1]), A["floor_fillet_mm"]))
    idx = [int(np.argmin(np.hypot(*(C - np.array(c)).T))) for _, c, _ in fil]
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
    used = {}
    order = np.argsort(idx)[::-1]
    srt = sorted(idx)
    for o in order:
        i = idx[o]
        k = srt.index(i)
        gap_prev = s[i] - (s[srt[k - 1]] if k > 0 else 0.0)
        gap_next = (s[srt[k + 1]] if k + 1 < len(srt) else s[-1]) - s[i]
        room = 0.45 * min(gap_prev, gap_next)
        C, lab, used[fil[o][0]] = fillet(C, lab, i, fil[o][2], room, fil[o][0])
    # drop points closer than 10 nm to the one before (a fillet's ends against the polyline's own points): they
    # would make normals from differences noisy and weld into degenerate rings
    keep = np.concatenate([[True], np.hypot(*np.diff(C, axis=0).T) > 1e-5])
    keep[-1] = True
    if not keep[-2] and len(C) > 2:
        keep[-2] = False
    C, lab = C[keep], lab[keep]
    return {"C": C, "lab": lab, "bezier": Bz, "floor_z": floor_z, "fillets_used": used}


def outer_visible(p):
    """The seen parts of the profile, for the fit: foot (its outer side: bottom, bead, face), wall, lip, and the
    crease between the foot ring and the wall (the middle of its fillet, for FOOT_TOP's report)."""
    P = closed_profile(p, inner=False)
    C, lab = P["C"], P["lab"]
    N = normals(C)
    part = lambda names: np.isin(lab, names)
    foot = part(["foot_bottom", "bead", "face"])
    ft = np.nonzero(lab == "foot_top")[0]
    return {"foot": (C[foot], N[foot]), "wall": (C[lab == "wall"], N[lab == "wall"]),
            "lip": (C[lab == "lip"], N[lab == "lip"]), "foot_top_point": C[ft[len(ft) // 2]], "bezier": P["bezier"]}


def normals(C):
    """Outward normals of a profile run in our order (axis under the base -> ... -> axis on the floor): the tangent
    turned clockwise, (dz, -dr)."""
    d = np.gradient(C, axis=0)
    n = np.c_[d[:, 1], -d[:, 0]]
    return n / np.linalg.norm(n, axis=1, keepdims=True)


# --- the camera -----------------------------------------------------------------------------------------------
def camera(p):
    """Centre (object frame, mm) and rotation rows [right, down, forward] of the photo's pinhole (right-handed: image
    x = right, image y = down). The camera sits at dist_mm from the axis point at half the height, elev_deg above it,
    in the plane x = 0 (the washer is round: its turn about the axis is free); it looks at that point, turned by
    dyaw_deg and tilted by dpitch_deg, and rolled by roll_deg."""
    e = math.radians(p["elev_deg"])
    yaw, pitch, roll = math.radians(p["dyaw_deg"]), e + math.radians(p["dpitch_deg"]), math.radians(p["roll_deg"])
    C = np.array([0.0, -p["dist_mm"] * math.cos(e), REF_Z + p["dist_mm"] * math.sin(e)])
    fwd = np.array([math.cos(pitch) * math.sin(yaw), math.cos(pitch) * math.cos(yaw), -math.sin(pitch)])
    right0 = np.array([math.cos(yaw), -math.sin(yaw), 0.0])
    down0 = np.cross(fwd, right0)
    right = right0 * math.cos(roll) + down0 * math.sin(roll)
    down = -right0 * math.sin(roll) + down0 * math.cos(roll)
    return C, np.stack([right, down, fwd])


def project(P, p, size=PHOTO_SIZE):
    C, Rm = camera(p)
    q = (np.asarray(P, float) - C) @ Rm.T
    f = p["f_px"]
    return np.c_[size[0] / 2 + f * q[:, 0] / q[:, 2], size[1] / 2 + f * q[:, 1] / q[:, 2]]


def contour_points(C2, N2, p, front=None, vmax=1.0):
    """The contour generator of the surface of revolution of profile C2 (n, 2) with outward normals N2, seen from
    the camera, as 3D polylines: per profile point the (up to two) azimuths where the view ray grazes the surface,
    from (P - C) . n = 0, i.e. cos(phi - phi_c) = (r n_r + (z - z_c) n_z) / (n_r rho_c); one polyline per run of
    consecutive profile points and per branch (+-). front: True keeps the near half (cos > 0), False the far half,
    None both; vmax drops the part nearer the camera's plane in front than cos(phi - phi_c) = vmax."""
    Cc, _ = camera(p)
    rho_c = float(np.hypot(Cc[0], Cc[1]))
    phi_c = math.atan2(Cc[1], Cc[0])
    r, z = C2[:, 0], C2[:, 1]
    nr, nz = N2[:, 0], N2[:, 1]
    ok = np.abs(nr) > 1e-9
    v = np.full(len(r), 9.0)
    v[ok] = (r[ok] * nr[ok] + (z[ok] - Cc[2]) * nz[ok]) / (nr[ok] * rho_c)
    ok &= (np.abs(v) <= 1) & (v <= vmax)
    if front is True:
        ok &= v > 0
    elif front is False:
        ok &= v <= 0
    idx = np.nonzero(ok)[0]
    if len(idx) == 0:
        return []
    runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
    out = []
    for run in runs:
        if len(run) < 2:
            continue
        # the two branches meet where |v| -> 1 (phi = phi_c or phi_c + pi), and there phi ~ sqrt(1 - |v|) moves
        # fast along the profile: so the run is taken from the meeting point (v = +-1, interpolated on the segment
        # beyond the run's end) and resampled evenly in the angle a = acos|v| (1 mrad, ~1.3 px at the rim) as well
        # as at its own points, and the two branches are joined there into one polyline. All the points move
        # smoothly with the camera, and none jumps in when a profile point crosses |v| = 1.
        if abs(v[run[-1]]) > abs(v[run[0]]):
            run = run[::-1]
        rr, zz, vv = r[run], z[run], v[run]
        o = run[0] - 1 if run[1] > run[0] else run[0] + 1            # the profile point beyond the meeting end
        joined = 0 <= o < len(r) and abs(nr[o]) > 1e-9 and abs(v[o]) > 1
        ang = np.arccos(np.clip(vv, -1, 1))                              # phi - phi_c on the + branch
        if joined:
            vm = math.copysign(1.0, vv[0])
            w = (vm - vv[0]) / (v[o] - vv[0])                            # where v = +-1 on the segment
            r0, z0 = rr[0] + w * (r[o] - rr[0]), zz[0] + w * (z[o] - zz[0])
            rr, zz, ang = np.r_[r0, rr], np.r_[z0, zz], np.r_[0.0 if vm > 0 else math.pi, ang]
            t = np.abs(ang - ang[0])                                     # the angle from the meeting
            bad = np.nonzero(np.diff(t) < 0)[0]
            m = int(bad[0]) + 1 if len(bad) else len(t)                  # its monotone stretch from the meeting
            if m >= 2:
                g = np.arange(0.0, t[m - 1], 1e-3)
                rr = np.r_[rr[:m], np.interp(g, t[:m], rr[:m]), rr[m:]]
                zz = np.r_[zz[:m], np.interp(g, t[:m], zz[:m]), zz[m:]]
                tt = np.r_[t[:m], g]
                k = np.argsort(tt, kind="stable")
                rr[:len(tt)], zz[:len(tt)] = rr[:len(tt)][k], zz[:len(tt)][k]
                sg = np.sign(math.pi / 2 - ang[0])
                ang = np.r_[ang[0] + sg * tt[k], ang[m:]]
        phi_off = ang
        P = [np.c_[rr * np.cos(phi_c + sg * phi_off), rr * np.sin(phi_c + sg * phi_off), zz] for sg in (1, -1)]
        if joined:
            out.append(np.vstack([P[1][::-1], P[0][1:]]))
        else:
            out += P
    return out


def circle_points(r, z, p, n=3000, front=True):
    Cc, _ = camera(p)
    phi = np.linspace(-math.pi, math.pi, n + 1)
    P = np.c_[r * np.cos(phi), r * np.sin(phi), np.full(n + 1, z)]
    if front:
        k = np.nonzero((P[:, :2] @ Cc[:2]) > 0)[0]
        P = P[k.min():k.max() + 1] if np.all(np.diff(k) == 1) else P[k]
    return [P]


class Polylines:
    """Distances from image points to a set of 2D polylines: exact point-to-segment, over the segments whose
    midpoints are among the k nearest."""

    def __init__(self, lines):
        lines = [L for L in lines if len(L) >= 2]
        self.A = np.vstack([L[:-1] for L in lines])
        self.B = np.vstack([L[1:] for L in lines])
        self.tree = cKDTree(0.5 * (self.A + self.B))

    def distance(self, Q, k=6):
        _, ii = self.tree.query(Q, k=k)
        A, B = self.A[ii], self.B[ii]
        d = B - A
        t = np.clip(np.einsum("nkj,nkj->nk", Q[:, None] - A, d) / np.maximum(np.einsum("nkj,nkj->nk", d, d), 1e-12), 0, 1)
        P = A + t[..., None] * d
        return np.sqrt(np.min(np.sum((Q[:, None] - P) ** 2, axis=2), axis=1))

    def points(self):
        return np.vstack([self.A, self.B])


def model_curves(p):
    """Projected model edges (photo px, as polylines) for each edge set of measure.py. The polylines' vertices move
    smoothly with the parameters (none appear or vanish but at the branches' meeting points), so the distances are
    smooth too; their chords are chords of the contour, whose image is flat where they are long (the back and the
    front of the rim's ellipse, radius of curvature ~9000 px)."""
    V = outer_visible(p)
    pr = lambda Ls: [project(L, p) for L in Ls if len(L) > 1]
    lip_c = pr(contour_points(*V["lip"], p))
    # the lower wall's contour in front (cos(phi - phi_c) > 0.6) runs behind the foot ring: hidden, and left out
    wall_c = pr(contour_points(*V["wall"], p, vmax=0.6))
    foot_c = pr(contour_points(*V["foot"], p))
    ft = V["foot_top_point"]
    return {"outline_top": Polylines(lip_c),
            "outline_side": Polylines(lip_c + wall_c + foot_c),
            "outline_bottom": Polylines(wall_c + foot_c),
            "lip_front": Polylines(lip_c),
            "foot_top": Polylines(pr(circle_points(ft[0], ft[1], p)))}


def residuals(x, E, sets):
    p = params_dict(x)
    try:
        M = model_curves(p)
    except ValueError:
        return np.full(sum(len(E[k]) for k in sets), 1e3)
    return np.concatenate([M[k].distance(E[k]) for k in sets])


def point_residuals(p, E):
    """Per set: the distance (px) of each edge point to the model's edge."""
    M = model_curves(p)
    return {k: M[k].distance(pts) for k, pts in E.items()}


def fit(a):
    J = json.load(open(a.edges))
    E = {k: np.asarray(v, float) for k, v in J["sets"].items()}
    # thin the dense outline sets (every stride-th point): neighbouring points are not independent anyway
    Ef = {k: E[k][::a.stride] for k in FIT_SETS}
    sets = list(Ef)
    keep = [q[0] != "height_mm" or not a.museum_height for q in FIT_PARAMS]
    Q = [q for q, k in zip(FIT_PARAMS, keep) if k]
    names = [q[0] for q in Q]
    x0, lo, hi, xs = (np.array([q[i] for q in Q]) for i in (1, 2, 3, 4))
    if a.start:                            # start from an earlier fit (fit.json's x)
        prev = json.load(open(a.start))["x"]
        x0 = np.array([prev.get(n, v) for n, v in zip(names, x0)])
        x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)

    def fun(y):
        try:
            M = model_curves(params_dict(y, names))
        except ValueError:
            return np.full(sum(len(Ef[k]) for k in sets), 1e3)
        return np.concatenate([M[k].distance(Ef[k]) for k in sets])

    # the residuals are exact point-to-polyline distances (smooth); robust: soft L1 beyond 1.5 px, for the
    # edge-finding failures (the right lower wall's soft limb, the foot's left end in shadow). The trust region
    # sometimes stalls (xtol) far from a minimum; it is restarted from where it stopped while that still helps.
    x, cost = x0, np.inf
    for _ in range(a.rounds):
        r2 = least_squares(fun, x, bounds=(lo, hi), loss="soft_l1", f_scale=1.5, x_scale=xs, max_nfev=a.max_nfev,
                           diff_step=2e-4, xtol=1e-10, ftol=1e-10, gtol=1e-10, verbose=1)
        done = r2.cost > cost * 0.998
        x, cost = r2.x, r2.cost
        if done:
            break
    p = params_dict(x, names)
    NAMES_FIT = names
    # uncertainty: from the Jacobian at the solution, with the robust residuals' scale (a guide, not a guarantee:
    # the residuals are correlated along each edge)
    Jm = r2.jac
    dof = max(1, len(r2.fun) - len(r2.x))
    s2 = float(np.sum(r2.fun ** 2) / dof)
    try:
        cov = np.linalg.inv(Jm.T @ Jm) * s2 * a.stride      # stride: the thinned points are not independent anyway
        sd = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        sd = np.full(len(r2.x), np.nan)
    R = point_residuals(p, E)
    stats = {k: {"n": int(len(v)), "median_px": round(float(np.median(v)), 3), "p90_px": round(float(np.percentile(v, 90)), 3),
                 "rms_px": round(float(np.sqrt(np.mean(v ** 2))), 3), "max_px": round(float(v.max()), 2)}
             for k, v in R.items()}
    return p, dict(zip(NAMES_FIT, sd.tolist())), stats, r2


def write_outputs(p, sd, stats, r2, a):
    V = outer_visible(p)
    C, Rm = camera(p)
    f = p["f_px"]
    fov_y = math.degrees(2 * math.atan(PHOTO_SIZE[1] / 2 / f))
    target = C + Rm[2] * float(np.hypot(C[1], C[2] - REF_Z))
    elev = math.degrees(math.atan2(C[2] - p.get("height_mm", HEIGHT_MM), math.hypot(C[0], C[1])))
    tag = lambda k: {"value": round(p[k], 4), "sd": round(sd[k], 4), "tag": "M", "how": "fitted to the photo's edges (form.py fit)"}
    form = {
        "source": "Cleveland Museum of Art 1957.40, Ru ware washer; photo Gary Kirchenbauer, CC0 (reference only, "
                  "ref/ru/photos/cma_1957.40.jpg)",
        "frame": "mm; z up along the axis, z = 0 on the ground; profile r(z) of the glaze's outer surface",
        "scale": {"diameter_mm": {"value": DIAMETER_MM, "tag": "M", "how": "the museum's record; the rim's outer diameter"},
                  "height_mm_museum": {"value": HEIGHT_MM, "tag": "M", "how": "the museum's record; ground to the lip's "
                                       "top. NOT used unless fit --museum-height: with D = 128 mm the photo fits "
                                       "H = fitted.height_mm (see docs/objects/ru_washer.md)"}},
        "fitted": {k: tag(k) for k in p if k not in CAM_NAMES and k != "lip_mm"},
        "measured": {"lip_mm": {"value": LIP_MM, "tag": "M", "how": "the lip band's width at the rim's two ends (LIP_MM)"}},
        "assumed": ASSUMED,
        "wall_bezier": np.round(V["bezier"], 4).tolist(),
        "derived": derived_numbers(p),
    }
    json.dump(form, open(FORM, "w"), indent=1, ensure_ascii=False)
    cam = {
        "about": "the pinhole of the CMA 1957.40 photo, solved with the washer's form (objects/ru_washer/form.py); "
                 "object frame: mm, z up, the axis at the origin, z = 0 the ground; right-handed (scene.py turns it "
                 "into pbrt's left-handed LookAt)",
        "photo": "ref/ru/photos/cma_1957.40.jpg", "photo_size_px": list(PHOTO_SIZE),
        "model": "pinhole, principal point at the photo's centre [A], square pixels, no distortion [A]",
        "f_px": {"value": round(f, 2), "sd": round(sd["f_px"], 2)},
        "fov_y_deg": round(fov_y, 5),
        "focal_mm_if_36mm_wide": round(f * 36.0 / PHOTO_SIZE[0], 2),
        "eye_mm": np.round(C, 4).tolist(), "forward": np.round(Rm[2], 6).tolist(), "down": np.round(Rm[1], 6).tolist(),
        "target_mm": np.round(target, 4).tolist(),
        "params": {k: {"value": round(p[k], 5), "sd": round(sd[k], 5)} for k in
                   CAM_NAMES[1:]},
        "distance_to_rim_centre_mm": round(float(np.linalg.norm(C - [0, 0, p.get("height_mm", HEIGHT_MM)])), 2),
        "elevation_over_rim_deg": round(elev, 3),
        "residuals_px": stats,
        "residuals_about": "distance from each edge point (measure.py) to the projected edge of the fitted form, photo "
                           "px (20 px/mm at the rim); the fit is robust (soft L1, 1.5 px), so a few far points are "
                           "edge-finding failures (the right lower wall's soft limb, the foot's left end in shadow)",
    }
    json.dump(cam, open(CAMERA, "w"), indent=1)
    os.makedirs(os.path.dirname(FIT_LOG), exist_ok=True)
    json.dump({"cost": float(r2.cost), "nfev": int(r2.nfev), "status": int(r2.status), "message": r2.message,
               "x": {k: v for k, v in p.items()}, "sd": sd, "stride": a.stride,
               "museum_height": bool(a.museum_height)}, open(a.log or FIT_LOG, "w"), indent=1)


def derived_numbers(p):
    """Numbers to read off: diameters, heights, the lip (from the filleted profile)."""
    V = outer_visible(p)
    foot, wall = V["foot"][0], V["wall"][0]
    full = closed_profile(p)
    ground = foot[foot[:, 1] < 0.02]
    return {
        "foot_diameter_max_mm": round(2 * float(foot[:, 0].max()), 3),
        "foot_diameter_ground_contact_outer_mm": round(2 * float(ground[:, 0].max()), 3),
        "foot_diameter_top_mm": round(2 * p["r_foot_top"], 3),
        "foot_height_mm": round(p["h_foot"], 3),
        "foot_splay_deg": round(math.degrees(math.atan2(p["r_foot_bottom"] - p["r_foot_top"], p["h_foot"])), 3),
        "lip_thickness_mm": round(p.get("lip_mm", LIP_MM), 3),
        "rim_diameter_mm": DIAMETER_MM,
        "max_outer_radius_mm": round(float(wall[:, 0].max()), 3),
        "outer_wall_radius_at_z_mm": {f"{z:g}": round(float(np.interp(z, wall[:, 1], wall[:, 0])), 3)
                                      for z in (6, 8, 10, 15, 20, 25, 30, 35) if wall[:, 1].min() <= z <= wall[:, 1].max()},
        "floor_z_mm": round(full["floor_z"], 3),
        "depth_inside_mm": round(HEIGHT_MM - full["floor_z"], 3),
        "fillets_used_mm": {k: round(v, 3) for k, v in full["fillets_used"].items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fit", "show"])
    ap.add_argument("--edges", default=EDGES)
    ap.add_argument("--stride", type=int, default=6, help="use every n-th edge point in the fit")
    ap.add_argument("--max-nfev", type=int, default=300)
    ap.add_argument("--museum-height", action="store_true",
                    help="hold the height at the museum's 38 mm instead of fitting it (HEIGHT: it fits worse)")
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--log", help="where fit.json goes (default out/ru/washer/fit.json)")
    ap.add_argument("--start", help="fit.json of an earlier fit to start from")
    a = ap.parse_args()
    if a.cmd == "fit":
        p, sd, stats, r2 = fit(a)
        write_outputs(p, sd, stats, r2, a)
        for k in p:
            print(f"  {k:16s} {p[k]:10.4f}  +- {sd.get(k, 0.0):.4f}")
        for k, s in stats.items():
            print(f"  {k:15s} n {s['n']:5d}  median {s['median_px']:.2f}  p90 {s['p90_px']:.2f}  rms {s['rms_px']:.2f}  max {s['max_px']:.1f} px")
        print(json.dumps(derived_numbers(p)))
    else:
        F = json.load(open(FORM))
        print(json.dumps(F["fitted"], indent=1))
        print(json.dumps(F["derived"], indent=1))


if __name__ == "__main__":
    main()
