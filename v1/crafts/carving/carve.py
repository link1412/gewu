"""Carving (雕) as a height field: vector motifs -> signed distance -> a knife's profile -> relief; incised lines,
pockets, geometric diaper grounds (锦地), knife facets, wear; the layer exposed at each height (剔红, 剔犀); and the
files a renderer reads (docs/crafts/carving.md).

Coordinates: mm, z up. The grid is x0 + i*step, y0 + j*step; arrays are indexed [j, i], row 0 at y0 (the bottom).
Heights are measured up from the substrate (the wood core's top): the lacquer stack runs from z = 0 to the uncut
surface, so the layer at a point is the one at its height (crafts never paint colour, they expose it).

A motif is a closed outline (polygon or circle) and a profile: from its outline inward the wall rises at `wall_deg`
from the horizontal (the knife's flank), meets a top that is flat ("flat"), a cushion ("pillow": a quarter circle in
the normalised inner distance d/D, D the inscribed radius) or a ridge ("ridge": linear in d/D, a crease on the medial
axis), the wall-top corner rounded over `shoulder_mm`. Motifs combine by max, back to front, so a front motif's wall
drops onto whatever lies behind it (overlapping leaves, 刀口一层压一层); the foot of the wall meets what is below with
a fillet of `fillet_mm` (0: a V knife's sharp foot; > 0: a round gouge).
"""
import math
import os
import subprocess

import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import LinearNDInterpolator


# --- signed distances ------------------------------------------------------------------------
def sdf_polygon(P, X, Y, chunk=200000):
    """Exact signed distance (mm) of points (X, Y) to the closed polygon P (n, 2): positive inside."""
    P = np.asarray(P, float)
    A, B = P, np.roll(P, -1, 0)
    x, y = X.ravel(), Y.ravel()
    out = np.empty(x.size)
    for s in range(0, x.size, chunk):
        px, py = x[s:s + chunk, None], y[s:s + chunk, None]
        ex, ey = (B - A)[:, 0], (B - A)[:, 1]
        wx, wy = px - A[:, 0], py - A[:, 1]
        t = np.clip((wx * ex + wy * ey) / np.maximum(ex * ex + ey * ey, 1e-18), 0, 1)
        d2 = (wx - t * ex) ** 2 + (wy - t * ey) ** 2
        # even-odd crossing count of a ray to +x
        c = ((A[:, 1] > py) != (B[:, 1] > py)) & (px < A[:, 0] + (py - A[:, 1]) * ex / np.where(ey == 0, 1e-18, ey))
        inside = (c.sum(1) % 2) == 1
        out[s:s + chunk] = np.sqrt(d2.min(1)) * np.where(inside, 1, -1)
    return out.reshape(X.shape)


def sdf_circle(c, r, X, Y):
    return r - np.hypot(X - c[0], Y - c[1])


def sdf_annulus(c, r0, r1, X, Y):
    rho = np.hypot(X - c[0], Y - c[1])
    return np.minimum(rho - r0, r1 - rho)


def dist_polyline(L, X, Y, chunk=200000):
    """Unsigned distance to an open polyline L (n, 2)."""
    L = np.asarray(L, float)
    A, B = L[:-1], L[1:]
    x, y = X.ravel(), Y.ravel()
    out = np.empty(x.size)
    for s in range(0, x.size, chunk):
        px, py = x[s:s + chunk, None], y[s:s + chunk, None]
        ex, ey = (B - A)[:, 0], (B - A)[:, 1]
        wx, wy = px - A[:, 0], py - A[:, 1]
        t = np.clip((wx * ex + wy * ey) / np.maximum(ex * ex + ey * ey, 1e-18), 0, 1)
        out[s:s + chunk] = np.sqrt(((wx - t * ex) ** 2 + (wy - t * ey) ** 2).min(1))
    return out.reshape(X.shape)


def smax(a, b, k):
    """Polynomial smooth maximum; k (mm) is the width of the blend (a fillet of about k/4 at a right angle)."""
    if k <= 0:
        return np.maximum(a, b)
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0, 1)
    return a * h + b * (1 - h) + k * h * (1 - h)


def smin(a, b, k):
    return -smax(-a, -b, k)


# --- profiles (a knife's section) ----------------------------------------------------------
def profile(d, D, base, edge, top, kind, wall_deg, shoulder_mm, d_cap=None):
    """Height of a motif at inner distance d (mm, > 0 inside): wall from `base` at the outline, top from `edge` at the
    outline to `top` at the inscribed centre (distance D)."""
    wall = base + d * math.tan(math.radians(wall_deg))       # continues below base outside the outline
    if d_cap is None:
        d_cap = d
    t = np.clip(d_cap / max(D, 1e-9), 0, 1)
    if kind == "flat":
        cap = np.full(d.shape, float(top))
    elif kind == "pillow":
        cap = edge + (top - edge) * np.sqrt(1 - (1 - t) ** 2)
    elif kind == "ridge":
        cap = edge + (top - edge) * t
    elif kind == "dome":                         # a spherical cap over a circle of radius D (exact for circles)
        hc = max(top - edge, 1e-9)
        Rs = (D * D + hc * hc) / (2 * hc)
        cap = edge + np.sqrt(np.maximum(Rs * Rs - (D - np.minimum(d_cap, D)) ** 2, 0)) - (Rs - hc)
    else:
        raise ValueError(f"profile kind {kind}")
    return smin(wall, cap, shoulder_mm)


# --- the relief ------------------------------------------------------------------------------
class Relief:
    def __init__(self, x0, x1, y0, y1, step, ground):
        self.x0, self.y0, self.step = x0, y0, step
        nx, ny = int(round((x1 - x0) / step)) + 1, int(round((y1 - y0) / step)) + 1
        self.x = x0 + step * np.arange(nx)
        self.y = y0 + step * np.arange(ny)
        self.x1, self.y1 = self.x[-1], self.y[-1]
        self.h = np.full((ny, nx), float(ground))
        self.ground = float(ground)
        self.log = []

    def window(self, bbox, pad):
        """Index slices and coordinates of the part of the grid that bbox (x0, y0, x1, y1) + pad covers."""
        i0 = max(0, int(math.floor((bbox[0] - pad - self.x0) / self.step)))
        i1 = min(len(self.x), int(math.ceil((bbox[2] + pad - self.x0) / self.step)) + 1)
        j0 = max(0, int(math.floor((bbox[1] - pad - self.y0) / self.step)))
        j1 = min(len(self.y), int(math.ceil((bbox[3] + pad - self.y0) / self.step)) + 1)
        if i1 <= i0 or j1 <= j0:
            return None
        X, Y = np.meshgrid(self.x[i0:i1], self.y[j0:j1])
        return (slice(j0, j1), slice(i0, i1)), X, Y

    def add(self, sdf_fn, bbox, base, edge, top, kind="pillow", wall_deg=70.0, shoulder_mm=0.3, fillet_mm=0.0,
            smooth_mm=0.0, jitter=None, name=""):
        """A raised motif. sdf_fn(X, Y) -> signed distance (mm, + inside); bbox its extent. smooth_mm > 0: the top is
        shaped from the distance blurred by a Gaussian of that sigma, which takes out the crease the distance has on the
        medial axis (a cushion with no ridge); the wall keeps the exact outline."""
        w = self.window(bbox, 1.0 + fillet_mm)
        if w is None:
            return
        sl, X, Y = w
        d = sdf_fn(X, Y)
        if jitter is not None:
            d = d + jitter(X, Y)
        dc = ndi.gaussian_filter(d, smooth_mm / self.step, mode="nearest") if smooth_mm > 0 else d
        D = float(dc.max())
        z = profile(d, D, base, edge, top, kind, wall_deg, shoulder_mm, d_cap=dc)
        self.h[sl] = smax(self.h[sl], z, fillet_mm)
        self.log.append({"motif": name, "kind": kind, "base": base, "edge": edge, "top": top, "inscribed_mm": round(D, 3)})

    def pocket(self, sdf_fn, bbox, floor, wall_deg=70.0, fillet_mm=0.0, name=""):
        """A cut: inside the outline the surface is lowered to `floor`, the walls rise outward at wall_deg."""
        w = self.window(bbox, 1.0)
        if w is None:
            return
        sl, X, Y = w
        d = sdf_fn(X, Y)
        cut = floor + np.maximum(-d, 0) * math.tan(math.radians(wall_deg))
        self.h[sl] = smin(self.h[sl], cut, fillet_mm)
        self.log.append({"pocket": name, "floor": floor})

    def incise(self, polyline, depth, knife="v", angle_deg=60.0, radius_mm=None, name=""):
        """A cut line along a polyline. knife 'v': a V of included angle angle_deg, depth `depth`;
        'round': a gouge of radius radius_mm, depth `depth` (width 2 sqrt(2 r depth - depth^2))."""
        L = np.asarray(polyline, float)
        if knife == "v":
            half_w = depth * math.tan(math.radians(angle_deg / 2))
        else:
            if radius_mm is None or depth > radius_mm:
                raise ValueError("round gouge needs radius_mm >= depth")
            half_w = math.sqrt(2 * radius_mm * depth - depth * depth)
        bbox = (L[:, 0].min(), L[:, 1].min(), L[:, 0].max(), L[:, 1].max())
        w = self.window(bbox, half_w + 2 * self.step)
        if w is None:
            return
        sl, X, Y = w
        r = dist_polyline(L, X, Y)
        if knife == "v":
            g = np.maximum(0, depth - r / math.tan(math.radians(angle_deg / 2)))
        else:
            R = radius_mm
            g = np.maximum(0, np.sqrt(np.maximum(R * R - r * r, 0)) - (R - depth))
        # cut from the surface as it was before the cuts that cross here: the local maximum over the cut's width
        # stands in for it, so crossing cuts do not add their depths (exact on flat ground; on a slope s the cut
        # is up to s * half width shallower)
        n = 2 * int(math.ceil(half_w / self.step)) + 1
        ref = ndi.maximum_filter(self.h[sl], size=n, mode="nearest")
        self.h[sl] = np.minimum(self.h[sl], ref - g)
        self.log.append({"incise": name, "knife": knife, "depth": depth, "width_mm": round(2 * half_w, 4)})

    # --- finishing ----------------------------------------------------------------------------


def facet_jitter(bbox, cell_mm, amp_mm, rng):
    """A continuous, piecewise-planar field (linear interpolation over a Delaunay triangulation of random points,
    one per cell_mm^2 on average) of amplitude amp_mm: added to a motif's distance, it moves its wall by facets, as
    separate knife strokes leave separate planes that meet at creases."""
    x0, y0, x1, y1 = bbox[0] - 2 * cell_mm, bbox[1] - 2 * cell_mm, bbox[2] + 2 * cell_mm, bbox[3] + 2 * cell_mm
    n = max(4, int((x1 - x0) * (y1 - y0) / cell_mm ** 2))
    pts = np.c_[rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)]
    corners = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]])
    pts = np.r_[pts, corners]
    f = LinearNDInterpolator(pts, rng.uniform(-amp_mm, amp_mm, len(pts)))
    return lambda X, Y: np.nan_to_num(f(X, Y))


def scratches(shape, step, density_per_cm2, len_mm, depth_um, width_mm, rng):
    """Fine wear scratches as a height field (mm, <= 0): random straight V-lines. density: lines per cm^2."""
    ny, nx = shape
    area_cm2 = nx * ny * step * step / 100.0
    n = int(rng.poisson(density_per_cm2 * area_cm2))
    h = np.zeros(shape)
    for _ in range(n):
        L = rng.lognormal(math.log(len_mm), 0.6)
        c = rng.uniform([0, 0], [nx * step, ny * step])
        a = rng.uniform(0, math.pi)
        A, B = c - 0.5 * L * np.array([math.cos(a), math.sin(a)]), c + 0.5 * L * np.array([math.cos(a), math.sin(a)])
        lo = np.floor((np.minimum(A, B) - width_mm) / step).astype(int)
        hi = np.ceil((np.maximum(A, B) + width_mm) / step).astype(int) + 1
        i0, j0 = max(lo[0], 0), max(lo[1], 0)
        i1, j1 = min(hi[0], nx), min(hi[1], ny)
        if i1 <= i0 or j1 <= j0:
            continue
        X, Y = np.meshgrid(np.arange(i0, i1) * step, np.arange(j0, j1) * step)
        r = dist_polyline(np.array([A, B]), X, Y)
        dep = depth_um * 1e-3 * rng.uniform(0.3, 1.0)
        h[j0:j1, i0:i1] = np.minimum(h[j0:j1, i0:i1], -np.maximum(0, dep * (1 - r / (width_mm / 2))))
    return h, n


# --- layers ----------------------------------------------------------------------------------
def layer_index(h, stack):
    """stack: [(name, thickness_mm), ...] from the substrate up. Returns (index into the distinct names in stack
    order, float array; names). The top layer extends upward without end."""
    names = []
    for n, _ in stack:
        if n not in names:
            names.append(n)
    tops = np.cumsum([t for _, t in stack])
    k = np.searchsorted(tops, h, side="right")
    k = np.minimum(k, len(stack) - 1)
    idx = np.array([names.index(n) for n, _ in stack], float)[k]
    return idx, names


def tixi_stack(red_mm, black_mm, pairs, base=("black", 0.3)):
    """剔犀: alternating red and black bands, `pairs` times, on a base coat."""
    return [base] + [s for _ in range(pairs) for s in (("red", red_mm), ("black", black_mm))]


# --- output ----------------------------------------------------------------------------------
def downsample(a, k):
    if k == 1:
        return a
    ny, nx = (a.shape[0] - 1) // k * k + 1, (a.shape[1] - 1) // k * k + 1
    return a[:ny:k, :nx:k]


def write_ply_grid(path, x, y, h, z_shift=0.0, uv_extent=None):
    """A height field as a triangle mesh with per-vertex normals and u, v (pbrt plymesh, binary).
    uv_extent (x0, x1, y0, y1): u = (x - x0)/(x1 - x0), v likewise (pbrt reads the image's first row at v = 1)."""
    ny, nx = h.shape
    X, Y = np.meshgrid(x, y)
    Z = h + z_shift
    gy, gx = np.gradient(h, y, x)
    N = np.stack([-gx, -gy, np.ones_like(h)], -1)
    N /= np.linalg.norm(N, axis=-1, keepdims=True)
    ux0, ux1, vy0, vy1 = uv_extent or (x[0], x[-1], y[0], y[-1])
    U, V = (X - ux0) / (ux1 - ux0), (Y - vy0) / (vy1 - vy0)
    vert = np.stack([X, Y, Z, N[..., 0], N[..., 1], N[..., 2], U, V], -1).reshape(-1, 8).astype("<f4")
    j, i = np.mgrid[0:ny - 1, 0:nx - 1]
    a = (j * nx + i).ravel()
    b, c, d = a + 1, a + nx, a + nx + 1
    tris = np.concatenate([np.c_[a, b, d], np.c_[a, d, c]]).astype("<i4")      # counter-clockwise seen from +z
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(vert)}"]
    head += [f"property float {p}" for p in ("x", "y", "z", "nx", "ny", "nz", "u", "v")]
    head += [f"element face {len(tris)}", "property list uchar int vertex_indices", "end_header"]
    face = np.zeros(len(tris), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = tris
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(vert.tobytes())
        f.write(face.tobytes())
    return len(vert), len(tris)


def write_pfm(path, a):
    """A float map, rows bottom (y0) first: PFM stores rows bottom to top, so it is written as it is."""
    a = np.ascontiguousarray(np.asarray(a, "<f4"))
    with open(path, "wb") as f:
        f.write(b"Pf\n%d %d\n-1\n" % (a.shape[1], a.shape[0]))
        f.write(a.tobytes())


def read_pfm(path):
    with open(path, "rb") as f:
        kind = f.readline().strip()
        w, h = map(int, f.readline().split())
        sc = float(f.readline())
        a = np.frombuffer(f.read(), "<f4" if sc < 0 else ">f4").reshape(h, w, 3 if kind == b"PF" else 1)
    return a[..., 0] if kind == b"Pf" else a


def bilinear_up(coarse, k, shape):
    """The mesh's own surface between its vertices (bilinear on the coarse grid), on the fine grid."""
    ny, nx = shape
    jj, ii = np.mgrid[0:ny, 0:nx] / k
    return ndi.map_coordinates(coarse, [jj, ii], order=1, mode="nearest")
