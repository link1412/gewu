"""Shot 6 scene for pbrt-v4: the Guan vase on a turntable, macro, the camera rolled 90 degrees so
the curve of the belly is the arc of the original shot (docs/shots/06-guan.md). The vase's motion is fitted
to the original's flow: the turntable plus a slow arc of the camera (motion_fit.py, motion.json).

    python3 -I shots/06-guan/scene.py --crackle out/06/vase_crackle.json --out out/06/scene \
        [--frame k] [--spp N] [--res 1920x1080] [--glaze-mm 1.2]

Writes scene.pbrt plus meshes (.ply) into --out. World: mm, Z up = the vase's axis; the limb of
the belly (the widest point) on +X; the camera on -Y looking +Y.

Materials: the glaze is fitted to the measured colour of Guan fenqing (GLAZE, glaze_fit.py); the stains
are measured spectra of stand-ins for their minerals (STAIN_REFLECTANCE); the glaze surface's roughness is
the measured gloss of Southern Song Guan fenqing. Still PLACEHOLDER: the lights.
"""

import argparse
import json
import math
import os
import struct
import sys

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vessel import Vessel  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "..", "..", "spec", "shots.json")))
SHOT = next(s for s in SPEC["shots"] if s["shot"] == 6)

# camera: a 100 mm macro on a full-frame sensor cropped to 16:9 (thin lens)
FOCAL_MM = 100.0
SENSOR_W_MM = 36.0
GLAZE_MM = 1.2           # uniform for now (--glaze-mm); the glaze-flow model will give e(s)
CRACK_INSET_MM = 0.001   # crack faces stop 1 um short of the two glaze surfaces
PATCH_STEP_MM = 0.5      # mesh spacing where the camera looks (facet sagitta < 1 um)
# focus and aperture, measured on the original's frame 103 (docs/shots/06-guan.md, 场景)
FOCUS_ROW = 0.84         # its sharpest band: mean |Laplacian| of luma peaks at rows 880-940 of 1080
LIMB_BLUR_PX = 36        # its limb rises 10-90% over ~25 px (1920 wide); a disc blur does that over 0.69 d
WIDEST_FNUMBER = 2.8     # a 100 mm macro lens

# the motion: fitted to the original's flow by motion_fit.py (velocity w x P + t, world mm per frame)
MOTION = os.path.join(HERE, "motion.json")
SHUTTER = 0.5            # 180 degrees

# the glaze, fitted so that the glaze over the body has the measured reflectance of Guan fenqing sherd J2
# (glaze_fit.py --invert --photons 40000 --glaze-mm e; docs/shots/06-guan.md, 釉). The fit depends on the
# glaze thickness, an assumption (0.5-2 mm on Guan [M]), so it is kept per thickness.
GLAZE = {
    "eta": 1.50,                       # [A] a soda-lime-silica glass, n ~ 1.5
    "g": 0.7,                          # [A] Henyey-Greenstein, bubbles larger than the wavelength
    "fits": {
        1.2: {"sigma_s": 2.5, "body_reflectance": 0.12,       # 1/mm; body "dark grey to black" [M]
              "sigma_a": [400, 0.1717, 450, 0.07757, 500, 0.02558, 550, 0.01028,
                          600, 0.01403, 650, 0.06212, 700, 0.1447, 750, 0.2371]},
    },
}

# the glaze surface: the 60-degree gloss of Southern Song Guan fenqing, 46.7 GU (2 sherds; the Guan-Ge paper of
# glaze_fit.py, Table 1; Longquan Ge 60.6), as a GGX alpha: tools/gloss.py 46.7 (meter angle 60 assumed [A])
GLAZE_ROUGHNESS = 0.0307

# what stains the crackle (Wu et al. 2025, Laohudong sherds): the iron wire is carbon with a little pyrite in
# an iron-rich deposit, the golden thread lepidocrocite and hematite in a clay-like deposit (Fe2O3 ~6 wt%).
# Reflectances measured on stand-ins, USGS Spectral Library v7 (splib07a, public domain; fetched from
# a GitHub mirror of the USGS files, checksums in its manifest, not checked against the USGS host):
# carbon black GDS68 (0.17 um) for the iron wire; raw sienna GDS805 (goethite in clays) for the golden thread,
# the nearest in kind (an iron oxyhydroxide in clay; lepidocrocite GDS80 alone is more orange).
STAIN_REFLECTANCE = {
    1: [400, 0.0198, 420, 0.0199, 440, 0.0195, 460, 0.0194, 480, 0.0193, 500, 0.0191, 520, 0.0191, 540, 0.0192,
        560, 0.0191, 580, 0.0191, 600, 0.0190, 620, 0.0190, 640, 0.0190, 660, 0.0190, 680, 0.0190, 700, 0.0190,
        720, 0.0189, 740, 0.0189, 750, 0.0189],
    2: [400, 0.0269, 420, 0.0322, 440, 0.0415, 460, 0.0494, 480, 0.0526, 500, 0.0614, 520, 0.0784, 540, 0.1049,
        560, 0.1397, 580, 0.1748, 600, 0.1993, 620, 0.2125, 640, 0.2209, 660, 0.2300, 680, 0.2425, 700, 0.2590,
        720, 0.2778, 740, 0.2933, 750, 0.2979],
}

# what the stains fill (Wu et al. 2025, Laohudong sherds): the iron wire (generation 1) runs to the bottom
# of the crack and does not fade; the golden thread (generation 2) fades with depth. The stained part of a
# crack wall is a diffuse surface; below it the wall is the bare air film.
STAIN_DEPTH = {1: 1.0, 2: 0.5}     # fraction of the glaze thickness from the surface; 0.5 is [A]
# the stain in the crack's mouth: real lines stay thin and crisp even where the pot is seen obliquely
# (the Palace Museum vase near its limb; Met 52611's base: 2-3 px at ~16 px/mm, so about 0.06-0.15 mm
# once the photographs' own blur is taken off [D, rough]); a wall seen through the milky glaze alone
# gives a soft band instead (first render with the fitted glaze, S2)
MOUTH_MM = {1: 0.10, 2: 0.06}      # strip width
MOUTH_DEPTH_MM = 0.003             # under the outer surface [A]


# --- motion ----------------------------------------------------------------------------
def screw(w, t):
    """The rigid motion whose velocity is w x P + t, as a screw: (a point on its axis, the unit axis,
    rad per frame about it, mm per frame along it)."""
    n = np.linalg.norm(w)
    return np.cross(w, t) / n ** 2, w / n, n, float(w @ t) / n


def pose(m, s):
    """4x4 pose of the vase s frames from the rest pose, for the screw m."""
    O, u, rate, along = m
    a = rate * s
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    R = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = O - R @ O + along * s * u
    return M


# --- framing ---------------------------------------------------------------------------
class Camera:
    """Pinhole at the lens centre C looking +Y, rolled so image-up is +X (away from the axis).
    pbrt's LookAt: right = up x dir = +Z (the neck is on the image's right)."""

    def __init__(self, C, u, res):
        self.C = np.asarray(C, float)
        self.u = u                                   # lens to the focus plane
        self.v = 1.0 / (1.0 / FOCAL_MM - 1.0 / u)    # lens to the sensor
        self.res = res
        self.sensor_h = SENSOR_W_MM * res[1] / res[0]
        self.fwd = np.array([0.0, 1.0, 0.0])
        self.up = np.array([1.0, 0.0, 0.0])
        self.right = np.cross(self.up, self.fwd)

    def project(self, P):
        """World points -> (x, y) in pixels, y down."""
        d = np.asarray(P, float) - self.C
        zf = d @ self.fwd
        x = (d @ self.right) / zf * self.v
        y = (d @ self.up) / zf * self.v
        W, H = self.res
        return np.c_[W / 2 + x / SENSOR_W_MM * W, H / 2 - y / self.sensor_h * H]

    @property
    def fov_deg(self):
        """pbrt's fov: the full angle across the shorter image side."""
        return math.degrees(2 * math.atan(0.5 * self.sensor_h / self.v))

    @property
    def frame_width_mm(self):
        return SENSOR_W_MM * self.u / self.v

    def ray(self, x, y):
        """Direction through pixel (x, y), scaled so its component along fwd is 1 (t = depth)."""
        W, H = self.res
        return (self.fwd + (x - W / 2) / W * SENSOR_W_MM / self.v * self.right
                + (H / 2 - y) / H * self.sensor_h / self.v * self.up)


def contour(v, cam, Ys):
    """The silhouette on the +X side seen from the lens: on each parallel (conformal Y) the point
    where the line of sight grazes the surface, (P - C) . N = 0."""
    r, Z, tR, tZ = v.profile_at(Ys)
    nR, nZ = tZ, -tR
    flip = nR < 0
    nR, nZ = np.where(flip, -nR, nR), np.where(flip, -nZ, nZ)
    xc, D, zc = cam.C[0], -cam.C[1], cam.C[2]
    # nR (r - xc cos phi + D sin phi) + (Z - zc) nZ = 0  ->  xc cos phi - D sin phi = q
    q = r + (Z - zc) * nZ / nR
    A = math.hypot(xc, D)
    delta = math.atan2(D, xc)
    phi = -delta + np.arccos(np.clip(q / A, -1, 1))
    P = np.stack([r * np.cos(phi), r * np.sin(phi), Z], -1)
    return P, phi


def fit_circle(x, y):
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]
    (a, b, k), *_ = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)
    R = math.sqrt(k + a * a + b * b)
    return a, b, R, float(np.abs(np.hypot(x - a, y - b) - R).max())


def arc_in_frame(v, cam):
    """Measure the silhouette inside the frame the way the spec measured the original
    (tools/spec_measure.py fit_arc): a quadratic y(x); apex = its vertex (fractions of width and
    height); sagitta = mean of y at the two frame edges minus the vertex, over the width. Also the
    radius and worst residual of the best circle, for information."""
    W, H = cam.res
    Ys = np.linspace(-0.6 * v.Rb, 0.6 * v.Rb, 2001)
    P, _ = contour(v, cam, Ys)
    xy = cam.project(P)
    m = (xy[:, 0] >= 0) & (xy[:, 0] <= W) & (xy[:, 1] >= 0) & (xy[:, 1] <= H)
    x, y = xy[m, 0], xy[m, 1]
    p = np.polyfit(x, y, 2)
    xv = -p[1] / (2 * p[0])
    yv = np.polyval(p, xv)
    sag = (0.5 * (np.polyval(p, 0) + np.polyval(p, W)) - yv) / W
    _, _, R, resid = fit_circle(x, y)
    return {"apex_x": xv / W, "apex_y": yv / H, "sagitta_of_width": sag,
            "circle_R_over_width": R / W, "circle_resid_px": resid}


def visible_patch(v, cam, margin):
    """(phi range, conformal Y range) of the surface that faces the lens and lands in the frame
    enlarged by `margin` of its size on every side."""
    W, H = cam.res
    phis = np.radians(np.linspace(-90, 90, 721))
    Ys = np.linspace(-1.2 * v.Rb, 1.2 * v.Rb, 481)
    pg, yg = np.meshgrid(phis, Ys)
    P, N = v.point(pg.ravel() * v.r0, yg.ravel())
    facing = np.einsum("ij,ij->i", P - cam.C, N) < 0
    xy = cam.project(P)
    inside = ((xy[:, 0] > -margin * W) & (xy[:, 0] < (1 + margin) * W)
              & (xy[:, 1] > -margin * H) & (xy[:, 1] < (1 + margin) * H))
    m = facing & inside
    if not m.any():
        raise SystemExit("no surface in the frame")
    p, y = pg.ravel()[m], yg.ravel()[m]
    return np.array([p.min(), p.max()]), np.array([y.min(), y.max()])


def surface_hit(v, cam, x, y):
    """First crossing of each pixel's ray into the vase at rest (marching 0.05 mm, then bisection): world
    points, and which rays hit."""
    d = np.stack([cam.ray(a, b) for a, b in zip(x, y)])
    Zs, Rs = v.Z[::-1], v.R[::-1]
    inside = lambda t: np.hypot(*(cam.C[:2, None] + t * d[:, :2].T)) < np.interp(cam.C[2] + t * d[:, 2], Zs, Rs)
    t = np.full(len(d), 100.0)
    lo, done = t.copy(), np.zeros(len(d), bool)
    for _ in range(8000):
        nxt = t + 0.05
        h = inside(nxt) & ~done
        lo[h], done[h] = t[h], True
        t = np.where(done, t, nxt)
        if done.all():
            break
    lo = np.where(done, lo, 100.0)
    hi = lo + 0.05
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        ins = inside(mid)
        lo, hi = np.where(ins, lo, mid), np.where(ins, mid, hi)
    return cam.C + lo[:, None] * d, done


def surface_normal(v, P, h=0.01):
    """Outward normal of the vase at rest at the world point P: radial, tilted by the profile's slope."""
    Zs, Rs = v.Z[::-1], v.R[::-1]
    slope = (np.interp(P[2] + h, Zs, Rs) - np.interp(P[2] - h, Zs, Rs)) / (2 * h)
    r = math.hypot(P[0], P[1])
    n = np.array([P[0] / r, P[1] / r, -slope])
    return n / np.linalg.norm(n)


def depth_of_row(v, cam, row):
    """Depth (along the lens axis) of the surface seen at the frame's centre column and `row`
    (fraction of the height): the first crossing of the ray into the vase, by marching then
    bisection. The vase is a surface of revolution, so the turntable does not change it; the rest pose
    of the camera's arc (motion.json) is the one framed and focused."""
    d = cam.ray(cam.res[0] / 2, row * cam.res[1])
    Zs, Rs = v.Z[::-1], v.R[::-1]                    # increasing Z
    inside = lambda t: math.hypot(*(cam.C[:2] + t * d[:2])) < np.interp(cam.C[2] + t * d[2], Zs, Rs)
    step, t = 0.05, 1.0
    while not inside(t + step):
        t += step
        if t > 2000:
            raise SystemExit(f"row {row}: the ray misses the vase")
    lo, hi = t, t + step
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if inside(mid) else (mid, hi)
    return lo


def solve_framing(v, res, u_focus):
    """Lens position (X, -D, Z) so the silhouette's arc has the original's sagitta and apex, as
    the spec measures them, with the lens focused at u_focus (which sets its extension, so the
    field of view). Newton on three unknowns, numerical Jacobian."""
    tgt = np.array([SHOT["arc"]["sagitta_of_width"], SHOT["arc"]["apex_x"], SHOT["arc"]["apex_y"]])
    x = np.array([223.0, v.Rb, 0.0])        # D, lens X, lens Z

    def cam_of(x):
        D, X, Z = x
        return Camera([X, -D, Z], u_focus, res)

    def F(x):
        a = arc_in_frame(v, cam_of(x))
        return np.array([a["sagitta_of_width"], a["apex_x"], a["apex_y"]]) - tgt

    for _ in range(30):
        f = F(x)
        if np.abs(f).max() < 1e-6:
            break
        J = np.zeros((3, 3))
        for j, h in enumerate((0.05, 0.01, 0.01)):
            dx = np.zeros(3)
            dx[j] = h
            J[:, j] = (F(x + dx) - f) / h
        x = x - np.linalg.solve(J, f)
    cam = cam_of(x)
    return cam, arc_in_frame(v, cam)


def frame_and_focus(v, res):
    """Framing and focus together. Focusing on the original's sharpest row sets the lens's
    extension, so the field of view, so where the lens must stand for the arc, so the depth of
    that row: solve depth(u) = u. (Iterating u <- depth(u) diverges: the slope is above 1.)"""
    g = lambda u: depth_of_row(v, solve_framing(v, res, u)[0], FOCUS_ROW) - u
    lo, hi = 150.0, 300.0
    if g(lo) * g(hi) > 0:
        raise SystemExit("framing and focus: no solution between 150 and 300 mm")
    u = brentq(g, lo, hi, xtol=1e-5)
    return solve_framing(v, res, u)


def aperture_for_limb_blur(v, cam):
    """Lens radius (mm) that blurs the limb at the apex by LIMB_BLUR_PX: a point at depth s,
    focused at u, blurs to 2a |v_s - v_u| / v_s on the sensor (thin lens; pbrt's thin lens agrees)."""
    P, _ = contour(v, cam, np.linspace(-0.6 * v.Rb, 0.6 * v.Rb, 4001))
    xy = cam.project(P)
    s = float((P[np.argmin(np.abs(xy[:, 0] - cam.res[0] / 2))] - cam.C) @ cam.fwd)
    img = lambda d: 1.0 / (1.0 / FOCAL_MM - 1.0 / d)
    b = LIMB_BLUR_PX / 1920 * SENSOR_W_MM
    a = b * img(s) / (2 * abs(img(s) - img(cam.u)))
    if FOCAL_MM / (2 * a) < WIDEST_FNUMBER:
        raise SystemExit(f"the limb blur needs f/{FOCAL_MM / (2 * a):.2f}, wider than the lens")
    return a, s


# --- meshes ----------------------------------------------------------------------------
def write_ply(path, P, N, tris, uv=None):
    """Binary little-endian PLY: float xyz, normals, optional uv; int vertex_indices."""
    P = np.asarray(P, np.float32)
    N = np.asarray(N, np.float32)
    cols = [P, N] + ([np.asarray(uv, np.float32)] if uv is not None else [])
    V = np.ascontiguousarray(np.concatenate(cols, 1))
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(P)}",
            "property float x", "property float y", "property float z",
            "property float nx", "property float ny", "property float nz"]
    if uv is not None:
        head += ["property float u", "property float v"]
    head += [f"element face {len(tris)}", "property list uchar int vertex_indices", "end_header"]
    T = np.asarray(tris, np.int32)
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = T
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.astype("<f4").tobytes())
        f.write(face.tobytes())


def grid_lines(lo, hi, fine_lo, fine_hi, coarse, fine):
    """Coordinates from lo to hi: `coarse` steps outside [fine_lo, fine_hi], `fine` inside."""
    a = np.arange(lo, fine_lo, coarse)
    b = np.arange(fine_lo, fine_hi, fine)
    c = np.arange(fine_hi, hi, coarse)
    return np.unique(np.concatenate([a, b, c, [hi]]))


def surface_grid(v, phis, Ys, depth):
    """Vertices, normals and triangles of the surface `depth` mm inside the outer glaze surface,
    on a phi x Y grid; phi wraps around."""
    PP, NN = [], []
    for Y in Ys:
        P, N = v.point(phis * v.r0, np.full_like(phis, Y), depth)
        PP.append(P)
        NN.append(N)
    P = np.concatenate(PP)
    N = np.concatenate(NN)
    n_phi, n_y = len(phis), len(Ys)
    tris = []
    for j in range(n_y - 1):
        for i in range(n_phi):
            i2 = (i + 1) % n_phi
            a, b = j * n_phi + i, j * n_phi + i2
            c, d = (j + 1) * n_phi + i, (j + 1) * n_phi + i2
            # winding so the geometric normal agrees with N (outward): Y grows to the neck (+Z)
            tris.append((a, b, d))
            tris.append((a, d, c))
    return P, N, np.array(tris)


def glaze_shell(v, phis, Ys, depth_in):
    """The glaze as one closed shell (Cycles fills a medium only inside a watertight mesh, and rgbscene.py rejects
    an open one; docs/slab.md): the outer surface (outward normals), the same grid `depth_in` mm inside it, turned
    to face inwards, and the two annuli joining them at the foot's and the mouth's rings. depth_in is past the
    body (GLAZE_MM), so the inner wall lies inside the opaque body and is never seen."""
    if phis[0] + 2 * math.pi - phis[-1] < 1e-6:   # grid_lines ends at pi - 1e-9: the seam's column again
        phis = phis[:-1]
    Po, No, To = surface_grid(v, phis, Ys, 0.0)
    Pi, Ni, Ti = surface_grid(v, phis, Ys, depth_in)
    n_phi, n = len(phis), len(Po)
    P = np.concatenate([Po, Pi])
    N = np.concatenate([No, -Ni])
    tris = [To, Ti[:, ::-1] + n]
    for j, sgn in ((0, -1), (len(Ys) - 1, 1)):   # the band's normal: down at the foot, up at the mouth
        k0 = len(P)
        ring = np.arange(n_phi) + j * n_phi
        P = np.concatenate([P, Po[ring], Pi[ring]])
        N = np.concatenate([N, np.tile([0.0, 0.0, float(sgn)], (2 * n_phi, 1))])
        band = []
        for i in range(n_phi):
            i2 = (i + 1) % n_phi
            a, b, c, d = k0 + i, k0 + i2, k0 + n_phi + i, k0 + n_phi + i2
            band += [(a, c, d), (a, d, b)]
        band = np.array(band)
        # wind each band so its geometric normal agrees with sgn (z)
        e = np.cross(P[band[:, 1]] - P[band[:, 0]], P[band[:, 2]] - P[band[:, 0]])[:, 2] * sgn
        band[e < 0] = band[e < 0][:, ::-1]
        tris.append(band)
    T = np.concatenate(tris)
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
    import shell
    bad = shell.watertight(P, T)
    if bad:
        raise SystemExit(f"glaze shell: {bad} bad edges")
    return P, N, T


def resample(p, step):
    """A crack polyline (conformal mm) through Catmull-Rom at about `step` mm: the simulation's
    0.8 mm polyline would show its kinks in macro. (Centripetal would be safer at kinks; the steps
    are even.)"""
    q = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    out = []
    for i in range(len(p) - 1):
        n = max(1, int(math.ceil(seg[i] / step)))
        s = np.linspace(0, 1, n, endpoint=False)[:, None]
        p0, p1, p2, p3 = q[i], q[i + 1], q[i + 2], q[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(p[-1:])
    return np.vstack(out)


def crack_ribbons(v, cracks, e, v0=0.0, v1=1.0, step=0.1):
    """Each crack polyline as a vertical ribbon through the glaze (resampled). The whole wall runs
    from CRACK_INSET below the outer surface down to CRACK_INSET above the body; v0..v1 picks a band
    of it (0 = top, 1 = bottom), the uv's v likewise."""
    PP, NN, UV, TT = [], [], [], []
    base = 0
    for c in cracks:
        p = np.asarray(c["pts"], float)
        if len(p) < 2:
            continue
        path = resample(p, step)
        depth = lambda f: CRACK_INSET_MM + f * (e - 2 * CRACK_INSET_MM)
        top, Ntop = v.point(path[:, 0], path[:, 1], depth(v0))
        bot, _ = v.point(path[:, 0], path[:, 1], depth(v1))
        # the ribbon's normal: along-crack tangent x surface normal
        tan = np.gradient(top, axis=0)
        nrm = np.cross(tan, Ntop)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        n = len(path)
        PP += [top, bot]
        NN += [nrm, nrm]
        UV += [np.c_[np.arange(n) / max(n - 1, 1), np.full(n, v0)], np.c_[np.arange(n) / max(n - 1, 1), np.full(n, v1)]]
        i = np.arange(n - 1)
        TT.append(np.c_[base + i, base + i + 1, base + n + i + 1])
        TT.append(np.c_[base + i, base + n + i + 1, base + n + i])
        base += 2 * n
    return np.concatenate(PP), np.concatenate(NN), np.concatenate(UV), np.concatenate(TT)


def mouth_strips(v, cracks, width, depth, step=0.1):
    """Each crack's stained mouth: a flat strip `width` mm wide along the crack, lying `depth` mm
    under the outer surface. Offsets are made in the conformal map, divided by its scale so that
    the width is in mm on the pot."""
    PP, NN, TT = [], [], []
    base = 0
    for c in cracks:
        p = np.asarray(c["pts"], float)
        if len(p) < 2:
            continue
        path = resample(p, step)
        t = np.gradient(path, axis=0)
        t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
        side = np.c_[-t[:, 1], t[:, 0]] * (0.5 * width / v.scale(path[:, 1]))[:, None]
        a, N = v.point(*(path - side).T, depth)
        b, _ = v.point(*(path + side).T, depth)
        n = len(path)
        PP += [a, b]
        NN += [N, N]
        i = np.arange(n - 1)
        TT.append(np.c_[base + i, base + i + 1, base + n + i + 1])
        TT.append(np.c_[base + i, base + n + i + 1, base + n + i])
        base += 2 * n
    return np.concatenate(PP), np.concatenate(NN), np.concatenate(TT)


# --- the scene file --------------------------------------------------------------------
def spectrum(vals):
    return "[ " + " ".join(f"{x:g}" for x in vals) + " ]"


def held(vals):
    """A sampled spectrum held flat out to pbrt's 360-830 nm: a PiecewiseLinear spectrum is zero
    outside its samples, which would make the glaze clear and the stains black at the ends."""
    vals = list(vals)
    if vals[0] > 360:
        vals = [360, vals[1]] + vals
    if vals[-2] < 830:
        vals = vals + [830, vals[-1]]
    return vals


# --- lights (PLACEHOLDER studio, tuned against the original's frame 103) ---------------------
# Read off the original (docs/shots/06-guan.md, 场景): a bright, neutral band under the limb
# fading over ~130 px; above the limb a mauve halo ~50 px tall (rows 460-515, up to (97,83,85));
# a dark mauve sky (26,20,24); the limb itself out of focus.
# The strengths (scale) are fitted together with camera.json's contrast (S2): each light rendered alone once,
# their sum fitted to frame 103's luma blurred 40 px over the object (median, 90th percentile), the hotspot's
# peak and the band around it, and the sky (light adds, so no render per trial).
RIM = {"K": 5500, "scale": 26.6, "dist": 300.0, "elev_deg": (8.0, 35.0), "width": 700.0}   # 8: clear of the frame; 35: the band's ~130 px
HALO = {"rgb": (1.0, 0.62, 0.78), "scale": 6.7, "depth": 360.0, "inside_px": 6.0}
# the backdrop's reflectance: a dark mauve cloth; warmed in S2 by the sky's colour against the original's
# (22,19,30) -> (26,20,24) in linear light, once the white balance went to 4200 K
SKY = {"rgb": (0.072, 0.039, 0.0275)}
BACK = {"K": 5500, "scale": 3350.0, "y": 320.0}  # a small softbox behind the halo disk, aimed at the backdrop
# key: a softbox on the lens side, high, that lights the glaze from where the glaze does not mirror it
# into the frame. The frame sees the surface at 58-90 deg incidence, so it mirrors only directions more
# than ~116 deg from the lens, behind the vase; a light on the lens side lights the glaze body without
# a reflection in shot. (The first renders were lit almost only by reflections of the rim softbox,
# 93-96 % of the light on the vase, S2, so the crackle inside the glaze could not show; the fill
# that stood here added nothing measurable and is gone.)
KEY = {"K": 5500, "scale": 148.5, "dist": 400.0, "elev_deg": 50.0, "size": (400.0, 400.0), "row": 0.75}
# hotspot: the original's bright pool at the bottom of the frame (frame 103: centred near (935, 1060), about
# 240 x 200 px at half height over the band's median, still while the texture moves: a light's reflection,
# S2). A small softbox where the glaze at that pixel mirrors; the glaze's roughness spreads it.
HOT = {"K": 5500, "scale": 203.0, "dist": 300.0, "size": 40.0, "px": (935, 1060)}
FRAME_CLEAR_PX = 100                           # lights stay this far outside the frame (their blur)


def emitter(w, spec, scale, corners=None, disk=None):
    w("AttributeBegin")
    L = f'"blackbody L" [ {spec} ]' if np.isscalar(spec) else f'"rgb L" [ {spec[0]} {spec[1]} {spec[2]} ]'
    w(f'  AreaLightSource "diffuse" {L} "float scale" [ {scale} ]')
    if corners is not None:
        P = " ".join(f"{x:.4f}" for c in corners for x in c)
        w(f'  Shape "bilinearmesh" "point3 P" [ {P} ] "integer indices" [ 0 1 2 3 ]')
    else:
        centre, radius = disk                      # a disk facing -Y (the lens): +Z turned to -Y
        w(f"  Translate {centre[0]:.4f} {centre[1]:.4f} {centre[2]:.4f}")
        w("  Rotate 90 1 0 0")
        w(f'  Shape "disk" "float radius" [ {radius:.4f} ]')
    w("AttributeEnd")


def panel(centre, normal, up, size):
    """Corners of a rectangle emitting along `normal` (pbrt: cross(p10 - p00, p01 - p00))."""
    n = normal / np.linalg.norm(normal)
    vh = up - (up @ n) * n
    vh /= np.linalg.norm(vh)
    uw = np.cross(vh, n)
    hw, hh = size[0] / 2, size[1] / 2
    return [centre - hw * uw - hh * vh, centre + hw * uw - hh * vh,
            centre - hw * uw + hh * vh, centre + hw * uw + hh * vh]


def outside_frame_px(cam, corners):
    """How far (px) a panel's edges stay outside the frame (negative = inside), seen from the lens
    centre: every edge sampled, not just the corners (an edge can cross the frame)."""
    c = np.asarray(corners)
    u = np.linspace(0, 1, 200)[:, None]
    P = np.concatenate([c[i] + u * (c[j] - c[i]) for i, j in ((0, 1), (1, 3), (3, 2), (2, 0))])
    xy = cam.project(P)
    W, H = cam.res
    out = np.max(np.c_[-xy[:, 0], xy[:, 0] - W, -xy[:, 1], xy[:, 1] - H], axis=1)
    return np.where((P - cam.C) @ cam.fwd > 0, out, np.inf)      # behind the lens: never in frame


def studio(w, v, cam, apex):
    """apex: the silhouette's point at the apex of the arc (world, mm)."""
    # rim: a wide softbox behind the vase, above the frame; the limb reflects it at grazing
    # incidence (normals tilted e/2 off the limb reflect elevation e), a band fading downwards
    e0, e1 = np.radians(RIM["elev_deg"])
    ends = [apex + RIM["dist"] * np.array([math.sin(e), math.cos(e), 0.0]) for e in (e0, e1)]
    centre = 0.5 * (ends[0] + ends[1])
    corners = panel(centre, apex - centre, np.array([1.0, 0, 0]),
                    (RIM["width"], float(np.linalg.norm(ends[1] - ends[0]))))
    clear = outside_frame_px(cam, np.array(corners)).min()
    if clear < FRAME_CLEAR_PX:
        raise SystemExit(f"the rim softbox is {clear:.0f} px from the frame, less than {FRAME_CLEAR_PX}")
    emitter(w, RIM["K"], RIM["scale"], corners=corners)
    # halo: a disk behind the vase, hidden by it from the lens centre (its edge HALO inside_px
    # inside the silhouette's circle), out of focus: from the rest of the aperture its edge shows
    # over the limb, a glow that follows the arc
    Ys = np.linspace(-0.6 * v.Rb, 0.6 * v.Rb, 2001)
    xy = cam.project(contour(v, cam, Ys)[0])
    m = (xy[:, 0] >= 0) & (xy[:, 0] <= cam.res[0])
    xc, yc, R_px, _ = fit_circle(xy[m, 0], xy[m, 1])
    s = HALO["depth"]
    mm_per_px = SENSOR_W_MM / cam.res[0] * s / cam.v
    emitter(w, HALO["rgb"], HALO["scale"],
            disk=(cam.C + s * cam.ray(xc, yc), (R_px - HALO["inside_px"] * cam.res[0] / 1920) * mm_per_px))
    # the backdrop, and a small softbox behind the halo disk (hidden by it and by the vase) that lights it
    w("AttributeBegin")
    w(f'  Material "diffuse" "rgb reflectance" [ {SKY["rgb"][0]} {SKY["rgb"][1]} {SKY["rgb"][2]} ]')
    w('  Shape "bilinearmesh" "point3 P" [ -3000 1500 -3000  3000 1500 -3000  -3000 1500 3000  3000 1500 3000 ] '
      '"integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    if BACK["y"] <= cam.C[1] + s:
        raise SystemExit("the backdrop light must sit behind the halo disk")
    emitter(w, BACK["K"], BACK["scale"],
            corners=panel(np.array([0.0, BACK["y"], 0]), np.array([0, 1.0, 0]), np.array([1.0, 0, 0]), (100, 100)))
    # key: aimed at the surface seen at the frame's centre column, KEY row, from elev_deg above the lens axis
    W, H = cam.res
    P0 = cam.C + depth_of_row(v, cam, KEY["row"]) * cam.ray(W / 2, KEY["row"] * H)
    a = math.radians(KEY["elev_deg"])
    centre = P0 + KEY["dist"] * np.array([math.sin(a), -math.cos(a), 0.0])
    corners = panel(centre, P0 - centre, np.array([0, 0, 1.0]), KEY["size"])
    clear = outside_frame_px(cam, np.array(corners)).min()
    if clear < FRAME_CLEAR_PX:
        raise SystemExit(f"the key softbox is {clear:.0f} px from the frame, less than {FRAME_CLEAR_PX}")
    emitter(w, KEY["K"], KEY["scale"], corners=corners)
    # hotspot: a softbox along the mirror direction of the glaze seen at HOT["px"]
    P, on = surface_hit(v, cam, *([c * cam.res[0] / 1920] for c in HOT["px"]))
    if not on[0]:
        raise SystemExit(f"hotspot pixel {HOT['px']} does not see the vase")
    P = P[0]
    d = (P - cam.C) / np.linalg.norm(P - cam.C)
    N = surface_normal(v, P)
    centre = P + HOT["dist"] * (d - 2 * (d @ N) * N)
    corners = panel(centre, P - centre, np.array([0, 0, 1.0]), (HOT["size"], HOT["size"]))
    clear = outside_frame_px(cam, np.array(corners)).min()
    if clear < FRAME_CLEAR_PX:
        raise SystemExit(f"the hotspot softbox is {clear:.0f} px from the frame, less than {FRAME_CLEAR_PX}")
    emitter(w, HOT["K"], HOT["scale"], corners=corners)


def main():
    global GLAZE_MM
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", default=os.path.join(HERE, "form.json"))
    ap.add_argument("--crackle", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frame", type=int, default=0, help="0..5 within the shot")
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--fnumber", type=float, help="override the aperture matched to the original's limb blur")
    ap.add_argument("--glaze-mm", type=float, default=GLAZE_MM, help="glaze thickness; needs a fit in GLAZE")
    ap.add_argument("--no-mouth", action="store_true", help="leave out the stained crack mouths (to compare)")
    ap.add_argument("--motion", default=MOTION, help="the fitted motion (motion_fit.py)")
    a = ap.parse_args()
    GLAZE_MM = a.glaze_mm
    if GLAZE_MM not in GLAZE["fits"]:
        raise SystemExit(f"no glaze fit for {GLAZE_MM} mm (GLAZE['fits'] has {sorted(GLAZE['fits'])}): "
                         f"run glaze_fit.py --invert --glaze-mm {GLAZE_MM}")
    fit = GLAZE["fits"][GLAZE_MM]
    res = tuple(int(x) for x in a.res.split("x"))
    os.makedirs(a.out, exist_ok=True)
    v = Vessel(a.form)

    cam, arc = frame_and_focus(v, (1920, 1080))
    lens_r, s_limb = aperture_for_limb_blur(v, cam)
    if a.fnumber:
        lens_r = FOCAL_MM / (2 * a.fnumber)
    cam = Camera(cam.C, cam.u, res)
    print(f"focus {cam.u:.2f} mm (row {FOCUS_ROW}), limb at {s_limb:.2f} mm: f/{FOCAL_MM / (2 * lens_r):.2f} "
          f"(lens radius {lens_r:.3f} mm) for a {LIMB_BLUR_PX} px limb blur")
    print(f"lens at {np.round(cam.C, 2)} mm, frame {cam.frame_width_mm:.2f} mm wide at the focus, "
          f"fov {cam.fov_deg:.3f} deg; apex ({arc['apex_x']:.4f}, {arc['apex_y']:.4f}), sagitta "
          f"{arc['sagitta_of_width']:.4f} (spec: {SHOT['arc']}); as a circle R/W "
          f"{arc['circle_R_over_width']:.3f}, worst residual {arc['circle_resid_px']:.2f} px")

    # the visible patch: the part of the surface that faces the lens and projects into the frame
    # (with a 15% margin for the motion, the lens blur and the crack faces seen at grazing)
    phi_lim, Ys_lim = visible_patch(v, cam, margin=0.15)
    print(f"visible patch: phi {math.degrees(phi_lim[0]):.1f} to {math.degrees(phi_lim[1]):.1f} deg "
          f"(conformal X {phi_lim[0] * v.r0:.1f} to {phi_lim[1] * v.r0:.1f} mm), Y {Ys_lim[0]:.1f} to {Ys_lim[1]:.1f} mm")
    pc = json.load(open(a.crackle))["params"]
    need = 15.0   # mm of crackle beyond the patch, so the simulation's border stays out of view
    if (pc["x_range"][0] > phi_lim[0] * v.r0 - need or pc["x_range"][1] < phi_lim[1] * v.r0 + need
            or pc["y_range"][0] > Ys_lim[0] - need or pc["y_range"][1] < Ys_lim[1] + need):
        raise SystemExit(f"crackle domain {pc['x_range']} x {pc['y_range']} does not cover the patch with "
                         f"{need} mm to spare")
    dphi = PATCH_STEP_MM / v.r0
    phis = grid_lines(-math.pi, math.pi - 1e-9, phi_lim[0], phi_lim[1], math.radians(2), dphi)
    t_lo, t_hi = v._t[0] * v.r0, v._t[-1] * v.r0
    Ys = grid_lines(t_lo + 1e-6, t_hi - 1e-6, Ys_lim[0], Ys_lim[1], 2.0, PATCH_STEP_MM)
    P, N, T = glaze_shell(v, phis, Ys, GLAZE_MM + 0.05)
    write_ply(os.path.join(a.out, "glaze_outer.ply"), P, N, T)
    P, N, T = surface_grid(v, phis, Ys, GLAZE_MM)
    write_ply(os.path.join(a.out, "glaze_body.ply"), P, N, T)
    print(f"surfaces: {len(phis)} x {len(Ys)} vertices each")

    C = json.load(open(a.crackle))
    if abs(C["params"]["glaze_mm"] - GLAZE_MM) > 1e-9:
        raise SystemExit("crackle was simulated for a different glaze thickness")
    # per generation, the stained top of the wall and the bare air film below it
    gens = sorted({c["gen"] for c in C["cracks"]})
    if set(gens) - set(STAIN_DEPTH):
        raise SystemExit(f"generations {gens}: STAIN_DEPTH has {sorted(STAIN_DEPTH)}")
    parts = []                                   # (file, generation, stained)
    for g in gens:
        cg = [c for c in C["cracks"] if c["gen"] == g]
        d = STAIN_DEPTH[g]
        for name, v0, v1, stained in ((f"cracks_g{g}_stain.ply", 0.0, d, True), (f"cracks_g{g}_bare.ply", d, 1.0, False)):
            if v1 - v0 < 1e-9:
                continue
            P, N, UV, T = crack_ribbons(v, cg, GLAZE_MM, v0, v1)
            write_ply(os.path.join(a.out, name), P, N, T, UV)
            parts.append((name, g, stained))
        if not a.no_mouth:
            P, N, T = mouth_strips(v, cg, MOUTH_MM[g], MOUTH_DEPTH_MM)
            write_ply(os.path.join(a.out, f"cracks_g{g}_mouth.ply"), P, N, T)
            parts.append((f"cracks_g{g}_mouth.ply", g, True))
        print(f"cracks, generation {g}: {len(cg)} polylines, stained to {d:.0%} of the glaze"
              + ("" if a.no_mouth else f", mouth {MOUTH_MM[g] * 1000:.0f} um"))

    # the motion during this frame's shutter, frames from the rest pose
    if not os.path.exists(a.motion):
        raise SystemExit(f"no {a.motion}: run tools/flow.py measure 6, then motion_fit.py")
    mo = json.load(open(a.motion))
    m6 = screw(np.array(mo["w_rad_per_frame"]), np.array(mo["t_mm_per_frame"]))
    s_open = a.frame - mo["t_mid_frame"] - 0.5 * SHUTTER
    s_close = s_open + SHUTTER
    print(f"motion {math.degrees(m6[2]):.4f} deg/frame about {np.round(m6[1], 4)} through {np.round(m6[0], 2)} mm "
          f"(fit rms {mo['fit']['rms_px_per_frame']} px/frame); shutter {s_open:+.2f} to {s_close:+.2f} frames")

    L = []
    w = L.append
    w(f"# shot 6, generated by shots/06-guan/scene.py; glaze {GLAZE_MM} mm fitted to Guan fenqing; "
      f"PLACEHOLDER: lights")
    tgt = cam.C + cam.fwd * cam.u
    w(f"LookAt {cam.C[0]:.5f} {cam.C[1]:.5f} {cam.C[2]:.5f}  {tgt[0]:.5f} {tgt[1]:.5f} {tgt[2]:.5f}  1 0 0")
    w(f'Camera "perspective" "float fov" [ {cam.fov_deg:.6f} ] "float lensradius" [ {lens_r:.4f} ] '
      f'"float focaldistance" [ {cam.u:.4f} ] "float shutteropen" [ 0 ] "float shutterclose" [ 1 ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 64 ] "bool refractivenee" true')
    w(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
      f'"string filename" [ "frame{a.frame:02d}.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] '
      f'"bool rawsensor" true')
    w("WorldBegin")
    P_c, _ = contour(v, cam, np.linspace(-0.6 * v.Rb, 0.6 * v.Rb, 4001))
    apex = P_c[np.argmin(np.abs(cam.project(P_c)[:, 0] - SHOT["arc"]["apex_x"] * res[0]))]
    studio(w, v, cam, apex)
    ss = fit["sigma_s"]
    w(f'MakeNamedMedium "glaze" "string type" "homogeneous" "spectrum sigma_a" {spectrum(held(fit["sigma_a"]))} '
      f'"spectrum sigma_s" [ 360 {ss} 830 {ss} ] "float g" [ {GLAZE["g"]} ] "float scale" [ 1 ]')
    # the vase moves during the shutter (the camera and the lights stay)
    O, u, rate, along = m6
    for when, s in (("StartTime", s_open), ("EndTime", s_close)):
        w(f"ActiveTransform {when}")
        w("Translate {:.6f} {:.6f} {:.6f}".format(*(O + along * s * u)))
        w("Rotate {:.6f} {:.8f} {:.8f} {:.8f}".format(math.degrees(rate * s), *u))
        w("Translate {:.6f} {:.6f} {:.6f}".format(*(-O)))
    w("ActiveTransform All")
    w("AttributeBegin")
    w('  MediumInterface "glaze" ""')
    w(f'  Material "dielectric" "float eta" [ {GLAZE["eta"]} ] "float roughness" [ {GLAZE_ROUGHNESS} ] '
      f'"bool remaproughness" false "bool refractivenee" true')
    w('  Shape "plymesh" "string filename" [ "glaze_outer.ply" ]')
    w("AttributeEnd")
    w("AttributeBegin")
    w('  MediumInterface "" "glaze"')
    b = fit["body_reflectance"]
    w(f'  Material "diffuse" "spectrum reflectance" [ 360 {b} 830 {b} ]')
    w('  Shape "plymesh" "string filename" [ "glaze_body.ply" ]')
    w("AttributeEnd")
    for name, g, stained in parts:
        w("AttributeBegin")
        w('  MediumInterface "glaze" "glaze"')
        if stained:
            w(f'  Material "diffuse" "spectrum reflectance" {spectrum(held(STAIN_REFLECTANCE[g]))}')
        else:
            w(f'  Material "thindielectric" "float eta" [ {1 / GLAZE["eta"]:.5f} ]')
        w(f'  Shape "plymesh" "string filename" [ "{name}" ]')
        w("AttributeEnd")
    with open(os.path.join(a.out, "scene.pbrt"), "w") as f:
        f.write("\n".join(L) + "\n")
    # for the camera chain's diffraction (tools/camera.py): pbrt traces rays only
    with open(os.path.join(a.out, "optics.json"), "w") as f:
        json.dump({"f_number": round(FOCAL_MM / (2 * lens_r), 4), "magnification": round(cam.v / cam.u, 5),
                   "sensor_width_mm": SENSOR_W_MM, "focal_mm": FOCAL_MM}, f)
    print(f"-> {a.out}/scene.pbrt")


if __name__ == "__main__":
    main()
