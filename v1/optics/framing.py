"""Framing to the film's arc (docs/optics.md "构图"): where the lens stands so the object's upper silhouette makes the
arc of an original shot, apex and sagitta as spec/shots.json measured them (tools/spec_measure.py fit_arc: a quadratic
y(x) through the edge; apex = its vertex, in fractions of the width and height; sagitta = the mean of y at the two
frame edges minus the vertex, over the width). Shot 6 does this for its vase (shots/06-guan/scene.py solve_framing);
this is the same for any object of revolution, about any axis, seen from any direction.

The silhouette of a surface of revolution (profile r(s), z(s) about an axis) seen from a point C: on each parallel,
the points where the line of sight grazes the surface, (P - C) . N = 0, which with C in the axis's frame
(Cx, Cy, Cz) reads Cx cos phi + Cy sin phi = r + nZ (z - Cz) / nR. Solved two ways and pooled, as each is sparse
where the other is dense: per parallel for phi (closed form), and per meridian for s (a sign change of the residual
along the profile, interpolated). Sharp edges between profile pieces (a lid's rim, a dome's base) are whole circles.
The top of the projected points, column by column, is the upper silhouette.
"""

import json
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = (1920, 1080)          # the arc is measured at the spec's resolution, whatever the render's
N_PHI = 8192                 # meridians for the per-meridian roots and the edge circles
BIN_PX = 4                   # columns of the upper silhouette, px at GRID: wider than the gaps between the points
PROFILE_STEP_MM = 0.25


def shot_arc(n):
    """The arc an original shot was measured to have (spec/shots.json)."""
    shots = json.load(open(os.path.join(ROOT, "spec/shots.json")))["shots"]
    s = next((x for x in shots if x["shot"] == n), None)
    if s is None or not s.get("arc"):
        raise SystemExit(f"spec/shots.json: shot {n} has no arc")
    return {k: s["arc"][k] for k in ("apex_x", "apex_y", "sagitta_of_width")}


def _resample(r, z, step):
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(r), np.diff(z)))])
    n = max(2, int(math.ceil(s[-1] / step)) + 1)
    t = np.linspace(0, s[-1], n)
    return np.interp(t, s, r), np.interp(t, s, z)


class Revolved:
    """An object of revolution: `pieces` of profile [(r...), (z...)] (mm, each piece smooth; the joins between pieces
    are sharp), about the axis through `origin` along `axis`. From the object's sidecar <name>.silhouette.json
    (written by its generator), moved by `shift` (build.py stands the object on the floor)."""

    def __init__(self, sidecar, shift=(0, 0, 0)):
        d = json.load(open(sidecar))
        if d.get("kind") != "revolved":
            raise SystemExit(f"{sidecar}: only objects of revolution can be framed to an arc (kind 'revolved')")
        self.O = np.asarray(d["origin"], float) + np.asarray(shift, float)
        self.a = np.asarray(d["axis"], float) / np.linalg.norm(d["axis"])
        h = np.array([1.0, 0, 0]) if abs(self.a[0]) < 0.9 else np.array([0, 1.0, 0])
        self.e1 = np.cross(self.a, h)
        self.e1 /= np.linalg.norm(self.e1)
        self.e2 = np.cross(self.a, self.e1)
        self.pieces, self.edges = [], []
        for r, z in d["pieces"]:
            r, z = _resample(np.asarray(r, float), np.asarray(z, float), PROFILE_STEP_MM)
            dr, dz = np.gradient(r), np.gradient(z)
            n = np.hypot(dr, dz)
            self.pieces.append((r, z, -dz / n, dr / n))       # (r, z, nR, nZ); the sign does not matter here
            for i in (0, -1):
                if r[i] > 1e-6:
                    self.edges.append((r[i], z[i]))

    def _world(self, r, phi, z):
        c, s = np.cos(phi), np.sin(phi)
        return self.O + (r * c)[:, None] * self.e1 + (r * s)[:, None] * self.e2 + z[:, None] * self.a

    def points(self, C):
        """Points on the silhouette (limbs and edges) seen from C (world, mm)."""
        d = np.asarray(C, float) - self.O
        Cx, Cy, Cz = d @ self.e1, d @ self.e2, d @ self.a
        A, delta = math.hypot(Cx, Cy), math.atan2(Cy, Cx)
        phis = 2 * np.pi * np.arange(N_PHI) / N_PHI
        out = []
        for r, z, nR, nZ in self.pieces:
            ok = np.abs(nR) > 1e-6
            q = np.full_like(r, np.inf)
            q[ok] = r[ok] + nZ[ok] * (z[ok] - Cz) / nR[ok]
            m = ok & (np.abs(q) <= A)
            ac = np.arccos(q[m] / A)
            for sg in (1, -1):                                   # per parallel
                out.append(self._world(r[m], delta + sg * ac, z[m]))
            # per meridian: f(s) = nR (r - (Cx cos phi + Cy sin phi)) + nZ (z - Cz) changes sign
            w = Cx * np.cos(phis) + Cy * np.sin(phis)
            f = nR[:, None] * (r[:, None] - w[None, :]) + (nZ * (z - Cz))[:, None]
            i, j = np.nonzero(f[:-1] * f[1:] < 0)
            t = f[i, j] / (f[i, j] - f[i + 1, j])
            out.append(self._world(r[i] + t * (r[i + 1] - r[i]), phis[j], z[i] + t * (z[i + 1] - z[i])))
        for r, z in self.edges:
            out.append(self._world(np.full(N_PHI, r), phis, np.full(N_PHI, z)))
        return np.concatenate(out)


def upper_silhouette(xy, P, res=GRID):
    """Column by column (BIN_PX wide at res), the highest projected point inside the frame: (x, y, P)."""
    W, H = res
    ok = np.isfinite(xy[:, 0]) & (xy[:, 0] >= 0) & (xy[:, 0] < W)
    x, y, P = xy[ok, 0], xy[ok, 1], P[ok]
    col = (x // BIN_PX).astype(int)
    order = np.lexsort((y, col))                                 # by column, then y up
    col, x, y, P = col[order], x[order], y[order], P[order]
    first = np.r_[True, col[1:] != col[:-1]]
    x, y, P = x[first], y[first], P[first]
    keep = (y >= 0) & (y <= H)
    return x[keep], y[keep], P[keep]


def measure(x, y, res=GRID):
    """The spec's arc numbers from upper-silhouette points (pixels at res), fitted as the spec fitted the film
    (tools/spec_measure.py fit_arc: a quadratic, four rounds of dropping points over 3 (median residual + 0.5 px))."""
    W, H = res
    n = W // BIN_PX
    if len(x) < 0.2 * n:
        raise SystemExit(f"the upper silhouette is in only {len(x)} of {n} columns: the object does not cross the frame")
    cols = len(x) / n
    for _ in range(4):
        p = np.polyfit(x, y, 2)
        r = np.abs(np.polyval(p, x) - y)
        m = r < 3 * (np.median(r) + 0.5)
        x, y = x[m], y[m]
    xv = -p[1] / (2 * p[0])
    yv = np.polyval(p, xv)
    sag = (0.5 * (np.polyval(p, 0) + np.polyval(p, W)) - yv) / W
    return {"apex_x": float(xv / W), "apex_y": float(yv / H), "sagitta_of_width": float(sag),
            "columns": cols, "inliers": len(x) / n, "resid_px": float(np.median(np.abs(np.polyval(p, x) - y)))}
