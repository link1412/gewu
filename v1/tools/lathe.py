"""Lathe forms seen by a pinhole camera: the geometry shared by the objects' form fits (a surface of revolution's
projected contour, distances from photo edge points to it).

Taken from objects/ru_washer/form.py (S4), where it was written and checked; there it is still inlined (with the
camera's reference height a module constant, here p["ref_z"], and the principal point at the photo's centre, here
p["cx"], p["cy"]). Object frame: mm, z up along the axis, right-handed; a profile is a polyline (r, z).
"""
import math

import numpy as np
from scipy.spatial import cKDTree


def bezier(P, n):
    P = np.asarray(P, float)
    k = len(P) - 1
    t = np.linspace(0, 1, n)[:, None]
    out = np.zeros((n, 2))
    for i in range(k + 1):
        out += math.comb(k, i) * t ** i * (1 - t) ** (k - i) * P[i]
    return out



def normals(C):
    """Outward normals of a profile run in our order (axis under the base -> ... -> axis on the floor): the tangent
    turned clockwise, (dz, -dr)."""
    d = np.gradient(C, axis=0)
    n = np.c_[d[:, 1], -d[:, 0]]
    return n / np.linalg.norm(n, axis=1, keepdims=True)



def camera(p):
    """Centre (object frame, mm) and rotation rows [right, down, forward] of the photo's pinhole (right-handed: image
    x = right, image y = down). The camera sits at dist_mm from the axis point p["ref_z"] high, elev_deg above it,
    in the plane x = 0 (the washer is round: its turn about the axis is free); it looks at that point, turned by
    dyaw_deg and tilted by dpitch_deg, and rolled by roll_deg."""
    e = math.radians(p["elev_deg"])
    yaw, pitch, roll = math.radians(p["dyaw_deg"]), e + math.radians(p["dpitch_deg"]), math.radians(p["roll_deg"])
    C = np.array([0.0, -p["dist_mm"] * math.cos(e), p["ref_z"] + p["dist_mm"] * math.sin(e)])
    fwd = np.array([math.cos(pitch) * math.sin(yaw), math.cos(pitch) * math.cos(yaw), -math.sin(pitch)])
    right0 = np.array([math.cos(yaw), -math.sin(yaw), 0.0])
    down0 = np.cross(fwd, right0)
    right = right0 * math.cos(roll) + down0 * math.sin(roll)
    down = -right0 * math.sin(roll) + down0 * math.cos(roll)
    return C, np.stack([right, down, fwd])


def project(P, p):
    """Photo pixels of object points; the principal point is p["cx"], p["cy"]."""
    C, Rm = camera(p)
    q = (np.asarray(P, float) - C) @ Rm.T
    f = p["f_px"]
    return np.c_[p["cx"] + f * q[:, 0] / q[:, 2], p["cy"] + f * q[:, 1] / q[:, 2]]


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

    def beyond(o):
        return 0 <= o < len(r) and (abs(nr[o]) <= 1e-9 or abs(v[o]) > 1)

    # a run whose branches meet at both ends (a closed loop of contour, e.g. round a foot ring) is split where |v| is
    # least, so that each half has one meeting end; else the end joined below flips with the parameters and the
    # other end's gap jumps (S6: the tenmoku's foot; not in ru_washer's inlined copy)
    split = []
    for run in runs:
        if len(run) >= 4 and beyond(run[0] - 1) and beyond(run[-1] + 1):
            m = int(np.argmin(np.abs(v[run])))
            m = min(max(m, 1), len(run) - 2)
            split += [run[:m + 1], run[m:]]
        else:
            split.append(run)
    runs = split
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
        # beyond the end: past |v| = 1, or a flat ring (n_r = 0, e.g. a foot ring's bottom), which is never on the
        # contour and stands for |v| = infinity (the meeting is then at the run's end). Inlined in ru_washer, a flat
        # ring there split the branches, leaving a gap in the contour (S6: the tenmoku's foot)
        flat = 0 <= o < len(r) and abs(nr[o]) <= 1e-9
        joined = 0 <= o < len(r) and (flat or abs(v[o]) > 1)
        ang = np.arccos(np.clip(vv, -1, 1))                              # phi - phi_c on the + branch
        if joined:
            vm = math.copysign(1.0, vv[0])
            w = 0.0 if flat else (vm - vv[0]) / (v[o] - vv[0])          # where v = +-1 on the segment
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


