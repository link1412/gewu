"""The lychee object: the fruit's shape, its tubercles, the pericarp's two layers, the aril and the seed, whole or cut
through by a plane (the knife: crafts/cutting/), written as a pbrt fragment for tools/build.py.

    python3 -I objects/lychee/lychee.py guiwei --section [--cut-z 0] [--out DIR]   # the half below a transverse cut,
                                                                                    # its cut face to the camera
    python3 -I objects/lychee/lychee.py CONFIG --parts whole|peeled|seed ...         # the material card's pieces

The fruit's own frame: the axis is z, the stem at +z, the apex at -z; theta from the stem, phi about the axis.
- Envelope (the groove level of the pericarp's outer face): x, y = a sin(theta) (1 + k cos(theta)) (cos, sin)(phi),
  z = c cos(theta); a = D/2, c = L/2, k the shoulder of a cordiform fruit.
- Tubercles (龟裂片): plates centred on a jittered Fibonacci lattice; for a point, e = (d2 - d1)/2 is its distance to
  its plate's border (d1, d2 the distances to the nearest two centres, along the surface); the plate stands
  h = H_i (e / e_max,i)^q out of the envelope, e_max,i half the plate's distance to its nearest neighbour; the plates'
  finer divisions (facets, optional) add a second lattice's H2_j (e2 / e2_max,j)^q2 sqrt(e / e_max,i). A suture
  (缝合线) runs down the meridian phi = 0 as a groove. True geometry: the tubercles make the arc's edge.
- Layers, as offsets along one direction field (the envelope's normal, turned into the cut plane in a band next to
  the cut so every layer's cut lies in the plane): the red layer from h down to t_red under the envelope (the
  tubercles red through);
  a gap; the white layer down to -t_pericarp; a gap; the aril from there to the seed (an ellipsoid on the axis) plus a
  gap; the seed coat t_testa thick; a gap; the cotyledon.
- Every part is a closed mesh with air outside it (materials/lychee/material.json "model"); a cut part is closed by
  its face in the plane. The aril's cut face carries the cut texture (crafts/cutting/cut.py) by planar UVs; its
  other faces map to the texture's zero border, so no bump there.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "optics"))
sys.path.insert(0, os.path.join(ROOT, "materials/lychee"))
sys.path.insert(0, os.path.join(ROOT, "crafts/cutting"))
from studio import write_ply  # noqa: E402
import optics as LO  # noqa: E402

GOLDEN = math.pi * (3 - math.sqrt(5))
ZERO_UV = (0.004, 0.004)          # in the cut texture's zero border (cut.py BORDER)


def v(d):
    return d["value"] if isinstance(d, dict) and "value" in d else d


def load(name):
    p = name if name.endswith(".json") else os.path.join(HERE, f"{name}.json")
    return json.load(open(p))


# --- shape --------------------------------------------------------------------------------------
class Fruit:
    def __init__(self, cfg, seed=0):
        f, t = cfg["fruit"], cfg["tubercles"]
        D = v(f["D_mm"])
        self.a, self.c, self.k = D / 2, D * v(f["L_over_D"]) / 2, v(f["shoulder"])
        self.Rm = (self.a * self.a * self.c) ** (1 / 3)
        rng = np.random.default_rng(seed)
        s = v(t["spacing_over_D"]) * D
        n = int(round(4 * math.pi * self.Rm ** 2 / (0.866 * s * s)))
        i = np.arange(n) + 0.5
        z = 1 - 2 * i / n
        r = np.sqrt(1 - z * z)
        d = np.c_[r * np.cos(GOLDEN * i), r * np.sin(GOLDEN * i), z]
        # jitter in the tangent plane
        tx = np.cross(d, np.where(np.abs(d[:, 2:3]) < 0.9, [[0, 0, 1.0]], [[1.0, 0, 0]]))
        tx /= np.linalg.norm(tx, axis=1, keepdims=True)
        ty = np.cross(d, tx)
        j = v(t["jitter"]) * s / self.Rm
        u = rng.uniform(-j, j, (n, 2))
        d = d + u[:, :1] * tx + u[:, 1:] * ty
        self.dirs = d / np.linalg.norm(d, axis=1, keepdims=True)
        self.tree = cKDTree(self.dirs)
        dd, _ = self.tree.query(self.dirs, k=2)
        self.emax = 0.5 * self._mm(dd[:, 1])
        H, cv = v(t["height_over_D"]) * D, v(t["height_cv"])
        sig = math.sqrt(math.log(1 + cv * cv))
        self.H = H * np.exp(rng.normal(-sig * sig / 2, sig, n))
        self.q = v(t["sharpness_q"])
        fc = t.get("facets")
        if fc:
            # the plates' finer divisions: a second lattice, its own jitter and heights, on top of the plates
            s2 = v(fc["spacing_over_plate"]) * s
            n2 = int(round(4 * math.pi * self.Rm ** 2 / (0.866 * s2 * s2)))
            i2 = np.arange(n2) + 0.5
            z2 = 1 - 2 * i2 / n2
            r2 = np.sqrt(1 - z2 * z2)
            d2 = np.c_[r2 * np.cos(GOLDEN * i2 + 1.0), r2 * np.sin(GOLDEN * i2 + 1.0), z2]
            t2 = np.cross(d2, np.where(np.abs(d2[:, 2:3]) < 0.9, [[0, 0, 1.0]], [[1.0, 0, 0]]))
            t2 /= np.linalg.norm(t2, axis=1, keepdims=True)
            u2 = rng.uniform(-1, 1, (n2, 2)) * v(t["jitter"]) * s2 / self.Rm
            d2 = d2 + u2[:, :1] * t2 + u2[:, 1:] * np.cross(d2, t2)
            d2 /= np.linalg.norm(d2, axis=1, keepdims=True)
            self.tree2 = cKDTree(d2)
            dd2, _ = self.tree2.query(d2, k=2)
            self.emax2 = 0.5 * self._mm(dd2[:, 1])
            self.H2 = v(fc["height_over_H"]) * H * np.exp(rng.normal(-sig * sig / 2, sig, n2))
            self.q2 = v(fc["sharpness_q"])
        else:
            self.tree2 = None
        su = cfg.get("suture")
        self.suture = (v(su["depth_mm"]), v(su["width_mm"])) if su else None
        self.n_plates, self.spacing = n, s

    def _mm(self, chord):
        return 2 * np.arcsin(np.clip(chord / 2, 0, 1)) * self.Rm

    def envelope(self, th, ph):
        """Points and outward unit normals of the envelope, arrays broadcast over (theta, phi)."""
        th, ph = np.broadcast_arrays(th, ph)
        s, co = np.sin(th), np.cos(th)
        rho = self.a * s * (1 + self.k * co)
        drho = self.a * (co * (1 + self.k * co) - self.k * s * s)
        cp, sp = np.cos(ph), np.sin(ph)
        P = np.stack([rho * cp, rho * sp, self.c * co], -1)
        dth = np.stack([drho * cp, drho * sp, -self.c * s], -1)
        dph = np.stack([-rho * sp, rho * cp, np.zeros_like(rho)], -1)
        N = np.cross(dth, dph)
        nn = np.linalg.norm(N, axis=-1, keepdims=True)
        pole = nn[..., 0] < 1e-12
        N = np.where(pole[..., None], np.stack([0 * co, 0 * co, np.sign(co)], -1), N / np.maximum(nn, 1e-30))
        return P, N

    def z_of(self, th):
        return self.c * np.cos(th)

    def theta_of_z(self, z):
        if abs(z) >= self.c:
            raise SystemExit(f"cut at z = {z} mm misses the fruit (|z| < {self.c:.2f})")
        return math.acos(z / self.c)

    def height(self, P):
        """The tubercles' height (mm, along the envelope's normal) at envelope points P."""
        d = P / np.linalg.norm(P, axis=-1, keepdims=True)
        dist, idx = self.tree.query(d.reshape(-1, 3), k=2)
        d1, d2 = self._mm(dist[:, 0]), self._mm(dist[:, 1])
        i = idx[:, 0]
        e = np.clip((d2 - d1) / 2 / self.emax[i], 0, 1)
        h = self.H[i] * e ** self.q
        if self.tree2 is not None:
            dist2, idx2 = self.tree2.query(d.reshape(-1, 3), k=2)
            j = idx2[:, 0]
            e2 = np.clip((self._mm(dist2[:, 1]) - self._mm(dist2[:, 0])) / 2 / self.emax2[j], 0, 1)
            h = h + self.H2[j] * e2 ** self.q2 * np.sqrt(e)       # the plates' grooves stay the deepest
        if self.suture:
            depth, w = self.suture
            x, y = P.reshape(-1, 3)[:, 0], P.reshape(-1, 3)[:, 1]
            h = h - np.where(x > 0, depth * np.exp(-(y / w) ** 2), 0.0)
        return h.reshape(P.shape[:-1])


# --- meshes -------------------------------------------------------------------------------------
class Mesh:
    def __init__(self):
        self.P, self.N, self.UV, self.T = [], [], [], []
        self.n = 0

    def add(self, P, N, UV, T):
        self.P.append(P.reshape(-1, 3))
        self.N.append(N.reshape(-1, 3))
        self.UV.append(UV.reshape(-1, 2))
        self.T.append(T + self.n)
        self.n += len(P.reshape(-1, 3))

    def arrays(self, outward_check=True):
        P, N, UV, T = (np.concatenate(x) for x in (self.P, self.N, self.UV, self.T))
        gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        flip = np.einsum("ij,ij->i", gn, N[T].mean(1)) < 0
        T[flip] = T[flip][:, [0, 2, 1]]
        return P, N, UV, T


def grid_tris(nr, nc, periodic=True):
    """Quads of an nr x nc grid (rows, columns; columns periodic) as triangles."""
    j, i = np.meshgrid(np.arange(nr - 1), np.arange(nc if periodic else nc - 1), indexing="ij")
    i1 = (i + 1) % nc
    a, b, c, d = j * nc + i, j * nc + i1, (j + 1) * nc + i, (j + 1) * nc + i1
    return np.concatenate([np.stack([a, c, d], -1).reshape(-1, 3), np.stack([a, d, b], -1).reshape(-1, 3)])


def grid_normals(P, outward):
    """Normals of a (rows, cols, 3) grid with periodic columns, flipped to agree with `outward` (rows, cols, 3)."""
    dr = np.gradient(P, axis=0)
    dc = (np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)) / 2
    N = np.cross(dr, dc)
    N /= np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-30)
    s = np.sign(np.einsum("...i,...i->...", N, outward))
    return N * np.where(s == 0, 1, s)[..., None]


def add_grid(mesh, P, outward, uv, pole_start=None, pole_end=None, sign=1.0):
    """A grid surface (rows along theta, periodic columns along phi) with optional pole vertices closing the first
    or last row. `sign` -1 for a surface facing into a cavity. If the UVs wrap in u (a texture round the axis), the
    first column is repeated at u + 1 so no triangle spans the texture backwards."""
    nr, nc = P.shape[:2]
    N = grid_normals(P, sign * outward)
    if np.ptp(uv[..., 0]) > 0.5:
        P, N = np.concatenate([P, P[:, :1]], 1), np.concatenate([N, N[:, :1]], 1)
        uv = np.concatenate([uv, uv[:, :1] + [1.0, 0.0]], 1)
        T = grid_tris(nr, nc + 1, periodic=False)
        nc += 1
        wrapped = True
    else:
        T = grid_tris(nr, nc)
        wrapped = False
    PP, NN, UU = [P.reshape(-1, 3)], [N.reshape(-1, 3)], [uv.reshape(-1, 2)]
    base = nr * nc
    for pole, row in ((pole_start, 0), (pole_end, nr - 1)):
        if pole is None:
            continue
        pp, pn = pole
        PP.append(np.asarray(pp, float)[None])
        NN.append(sign * np.asarray(pn, float)[None])
        UU.append(np.full((1, 2), uv.reshape(-1, 2)[0]))
        i = np.arange(nc - 1) if wrapped else np.arange(nc)
        T = np.concatenate([T, np.stack([np.full(len(i), base), row * nc + i, row * nc + (i + 1) % nc], -1)])
        base += 1
    mesh.add(np.concatenate(PP), np.concatenate(NN), np.concatenate(UU), T)


def zipper(A, B):
    """Triangles between two closed loops A, B (arrays of points in a plane z = const, star-shaped about the axis),
    by walking both in angle. Returns (points, triangles) with A's points first."""
    aa = np.unwrap(np.arctan2(A[:, 1], A[:, 0]))
    bb = np.unwrap(np.arctan2(B[:, 1], B[:, 0]))
    if aa[-1] < aa[0]:
        A, aa = A[::-1], aa[::-1]
    if bb[-1] < bb[0]:
        B, bb = B[::-1], bb[::-1]
    # start B at the point nearest in angle to A's first
    k = int(np.argmin(np.abs(((bb - aa[0] + np.pi) % (2 * np.pi)) - np.pi)))
    B = np.roll(B, -k, axis=0)
    bb = np.unwrap(np.arctan2(B[:, 1], B[:, 0]))
    bb += 2 * np.pi * np.round((aa[0] - bb[0]) / (2 * np.pi))
    na, nb = len(A), len(B)
    A2 = np.r_[aa, aa[0] + 2 * np.pi]
    B2 = np.r_[bb, bb[0] + 2 * np.pi]
    T, i, j = [], 0, 0
    while i < na or j < nb:
        if j >= nb or (i < na and A2[i + 1] <= B2[j + 1]):
            T.append((i % na, (i + 1) % na, na + j % nb))
            i += 1
        else:
            T.append((i % na, na + (j + 1) % nb, na + j % nb))
            j += 1
    return np.concatenate([A, B]), np.array(T)


def add_cap(mesh, outer, inner, normal, uvf):
    """The cut face between two loops (annulus), or a disk if inner is None (rings shrinking to the loop's centre)."""
    if inner is None:
        c = outer.mean(0)
        rings = [c + (outer - c) * f for f in np.linspace(1, 0.06, 12)]
        P = np.stack(rings)
        T = grid_tris(len(rings), len(outer))
        P = np.concatenate([P.reshape(-1, 3), c[None]])
        nc, last = len(outer), (len(rings) - 1) * len(outer)
        i = np.arange(nc)
        T = np.concatenate([T, np.stack([np.full(nc, len(P) - 1), last + (i + 1) % nc, last + i], -1)])
    else:
        P, T = zipper(outer, inner)
    N = np.broadcast_to(np.asarray(normal, float), P.shape).copy()
    mesh.add(P, N, uvf(P), T)


def theta_rows(th0, th1, R, step, fine=None):
    """Rows from th0 to th1 (radians), `step` mm apart; with fine = (band_mm, fine_step) rows start fine next to th0
    and grow geometrically to `step`."""
    L = abs(th1 - th0) * R
    if fine is None:
        n = max(2, int(math.ceil(L / step)) + 1)
        return np.linspace(th0, th1, n)
    band, fs = fine
    x = [0.0]
    ds = fs
    while x[-1] < L:
        ds = fs if x[-1] < band else min(step, ds * 1.15)
        x.append(x[-1] + ds)
    x = np.array(x) * L / x[-1]
    return th0 + np.sign(th1 - th0) * x / R


class Builder:
    """Every part's mesh for one lychee (whole, or the part below a cut at z = cut_z)."""

    def __init__(self, cfg, cut_z=None, seed=0):
        self.cfg = cfg
        self.F = Fruit(cfg, seed)
        self.cut_z = cut_z
        p, g = cfg["pericarp"], cfg["gaps"]
        self.t_peri, self.t_red = v(p["thickness_mm"]), v(p["outer_mm"])
        self.g_layer = v(p["layer_gap_mm"])
        self.g_pa, self.g_as, self.g_tc = v(g["pericarp_aril_mm"]), v(g["aril_seed_mm"]), v(g["testa_cotyledon_mm"])
        s = cfg["seed"]
        self.seed_axes = np.array([v(s["width_mm"]), v(s["thickness_mm"]), v(s["length_mm"])]) / 2
        self.seed_z = v(s["centre_z_mm"])
        m = cfg["mesh"]
        self.step, self.sstep = m["step_mm"], m["smooth_step_mm"]
        self.th0 = self.F.theta_of_z(cut_z) if cut_z is not None else 0.0
        self.extent = max(self.F.a * (1 + abs(self.F.k)), self.F.c) + 2.0      # half side of the cut texture's square, mm

    # the direction field the layers are offset along
    def directions(self, th, ph):
        P, N = self.F.envelope(th, ph)
        if self.cut_z is not None:
            w = np.exp(-(((th - self.th0) * self.F.Rm) / 0.8) ** 2)[..., None]
            N = N - w * N[..., 2:3] * np.array([0, 0, 1.0])
            N /= np.linalg.norm(N, axis=-1, keepdims=True)
        return P, N

    def rows(self, step):
        th1 = math.pi
        if self.cut_z is None:
            return theta_rows(0.0, th1, self.F.Rm, step)[1:-1]
        return theta_rows(self.th0, th1, self.F.Rm, max(step, 0.3), fine=(3.0, step))[:-1]

    def cols(self, step, R=None):
        n = int(math.ceil(2 * math.pi * (R or self.F.a) / step))
        return np.arange(n) * 2 * math.pi / n

    def poles(self, offset_fn):
        """Pole vertices (stem, apex) of an offset surface."""
        out = []
        for th in (0.0, math.pi):
            P, N = self.F.envelope(np.array(th), np.array(0.0))
            out.append((P + N * offset_fn(P[None], N[None])[0], N))
        return out

    def uv_zero(self, P):
        return np.broadcast_to(np.array(ZERO_UV), P.shape[:-1] + (2,)).copy()

    def uv_plane(self, P):
        return (P[..., :2] + self.extent) / (2 * self.extent)

    def uv_sphere(self, P):
        ph = np.arctan2(P[..., 1], P[..., 0]) % (2 * math.pi)
        th = np.arccos(np.clip(P[..., 2] / np.linalg.norm(P, axis=-1), -1, 1))
        return np.stack([ph / (2 * math.pi), th / math.pi], -1)

    def offset_surface(self, mesh, off, step, sign=1.0, uvf=None):
        """A surface offset from the envelope by off(P_env, N) along the direction field; returns its cut loop."""
        th, ph = self.rows(step), self.cols(step)
        TH, PH = np.meshgrid(th, ph, indexing="ij")
        P0, N = self.directions(TH, PH)
        P = P0 + N * off(P0, N)[..., None]
        uvf = uvf or self.uv_zero
        if self.cut_z is None:
            stem, apex = self.poles(lambda P_, N_: off(P_, N_)[..., None])
            add_grid(mesh, P, N, uvf(P), pole_start=stem, pole_end=apex, sign=sign)
            return None
        _, apex = self.poles(lambda P_, N_: off(P_, N_)[..., None])
        add_grid(mesh, P, N, uvf(P), pole_end=apex, sign=sign)
        loop = P[0].copy()
        loop[:, 2] = self.cut_z
        return loop

    # --- the parts -----------------------------------------------------------------------------
    def h_outer(self, P0, N):
        return self.F.height(P0)

    def h_red_inner(self, P0, N):
        """The red layer's inner face: t_red under the grooves' level, so the tubercles are red through (S4: following
        the tubercles smoothed left their cores white, and the cut showed a white band twice the red)."""
        h = self.F.height(P0)
        if np.any(h <= -self.t_red):
            raise SystemExit(f"the suture's groove ({h.min():.3f} mm) cuts through the red layer ({self.t_red} mm)")
        return np.full(np.shape(h), -self.t_red)

    def pericarp(self, outer_uv=None):
        """Two meshes: the red layer and the white layer."""
        red, white = Mesh(), Mesh()
        lo = self.offset_surface(red, self.h_outer, self.step, uvf=outer_uv)
        li = self.offset_surface(red, self.h_red_inner, self.step, sign=-1)
        wo = self.offset_surface(white, lambda P0, N: self.h_red_inner(P0, N) - self.g_layer, self.step)
        wi = self.offset_surface(white, lambda P0, N: np.full(P0.shape[:-1], -self.t_peri), self.sstep, sign=-1)
        if self.cut_z is not None:
            up = np.array([0, 0, 1.0])
            add_cap(red, lo, li, up, self.uv_zero)
            add_cap(white, wo, wi, up, self.uv_zero)
        return red, white

    def seed_surface(self, mesh, grow, step, sign=1.0, uvf=None):
        """The seed's ellipsoid grown by `grow` mm (negative: shrunk); returns its cut loop (or None)."""
        A = self.seed_axes + grow
        if np.any(A <= 0):
            raise SystemExit(f"seed surface grown by {grow}: axes {A}")
        zc = self.seed_z
        if self.cut_z is not None:
            if abs(self.cut_z - zc) >= A[2]:
                raise SystemExit(f"the cut at z = {self.cut_z} misses the seed (z {zc - A[2]:.2f}..{zc + A[2]:.2f}); "
                                 "a section without the seed is not built")
            t0 = math.acos((self.cut_z - zc) / A[2])
        else:
            t0 = 0.0
        R = A.max()
        th = theta_rows(t0, math.pi, R, step)
        th = th[:-1] if self.cut_z is not None else th[1:-1]
        ph = self.cols(step, R)
        TH, PH = np.meshgrid(th, ph, indexing="ij")
        P = np.stack([A[0] * np.sin(TH) * np.cos(PH), A[1] * np.sin(TH) * np.sin(PH), zc + A[2] * np.cos(TH)], -1)
        out = np.stack([np.sin(TH) * np.cos(PH) / A[0], np.sin(TH) * np.sin(PH) / A[1], np.cos(TH) / A[2]], -1)
        uvf = uvf or self.uv_zero
        apex = (np.array([0, 0, zc - A[2]]), np.array([0, 0, -1.0]))
        stem = (np.array([0, 0, zc + A[2]]), np.array([0, 0, 1.0]))
        if self.cut_z is None:
            add_grid(mesh, P, out, uvf(P), pole_start=stem, pole_end=apex, sign=sign)
            return None
        add_grid(mesh, P, out, uvf(P), pole_end=apex, sign=sign)
        loop = P[0].copy()
        loop[:, 2] = self.cut_z
        return loop

    def aril(self, outer_uv=None, cap_uv=None):
        m = Mesh()
        lo = self.offset_surface(m, lambda P0, N: np.full(P0.shape[:-1], -self.t_peri - self.g_pa), self.sstep,
                                 uvf=outer_uv)
        li = self.seed_surface(m, self.g_as, self.sstep, sign=-1, uvf=outer_uv)
        if self.cut_z is not None:
            add_cap(m, lo, li, [0, 0, 1.0], cap_uv or self.uv_plane)
        return m

    def seed(self):
        testa, cot = Mesh(), Mesh()
        t = v(load_material()["testa"]["thickness_mm"])
        lo = self.seed_surface(testa, 0.0, self.sstep)
        li = self.seed_surface(testa, -t, self.sstep, sign=-1)
        lc = self.seed_surface(cot, -t - self.g_tc, self.sstep)
        if self.cut_z is not None:
            up = [0, 0, 1.0]
            add_cap(testa, lo, li, up, self.uv_zero)
            add_cap(cot, lc, None, up, self.uv_zero)
        return testa, cot

    def envelope_profile(self, lift):
        """The outer surface's profile of revolution (r, z), the tubercles as a mean lift: (thetas, r, z)."""
        th = np.linspace(self.th0, math.pi, 400)
        P, N = self.F.envelope(th, np.zeros_like(th))
        P = P + N * lift
        return np.abs(P[:, 0]), P[:, 2]


def load_material():
    return LO.load()


def write_skin_grain(path, B, grain, seed=0):
    """The epicarp's fine relief on the red layer's spherical UVs (u = phi / 2 pi, v = theta / pi): a network of
    fissures across the plates (the card's photo shows them [M, qualitative]; at the section's 2.55x a smooth skin
    reads as clay, S4). Band-limited noise of about `across_mm`, folded (-|n|) into sharp valleys, `rms_mm` [A];
    texels about `px_mm` at the equator."""
    import cut as CUT
    rng = np.random.default_rng([seed, 13])
    Lu, Lv = 2 * math.pi * B.F.a, math.pi * B.F.c
    nu = int(2 ** math.ceil(math.log2(Lu / grain["px_mm"])))
    nv = nu // 2
    ku = np.fft.fftfreq(nu, Lu / nu)[None, :].astype(np.float32)
    kv = np.fft.fftfreq(nv, Lv / nv)[:, None].astype(np.float32)
    env = np.exp(-0.5 * (ku ** 2 + kv ** 2) * (grain["across_mm"] * 2 * math.pi / 2) ** 2)
    n = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((nv, nu)).astype(np.float32)) * env))
    h = -np.abs(n / n.std())
    h = (h - h.mean()) / h.std() * grain["rms_mm"]
    CUT.write_pfm(path, h.astype(np.float32))
    return {"file": os.path.basename(path), "px": [nu, nv], "mm_per_px_equator": [Lu / nu, Lv / nv], **grain}


def write_aril_skin(path, B, skin, seed=0):
    """The peeled aril's surface: creases running along the meridians (the card's photo shows a crinkled membrane,
    ridges about `across_mm` apart and `along_mm` long [M, by eye]), as a height map on the aril's spherical UVs
    (u = phi / 2 pi, periodic; v = theta / pi). Anisotropic Gaussian-filtered noise, folded (-|n|) so the creases
    are sharp valleys [A], scaled to `rms_mm` [A]."""
    import cut as CUT
    rng = np.random.default_rng([seed, 11])
    nu, nv = 2048, 1024
    r = B.F.a - B.t_peri - B.g_pa
    Lu, Lv = 2 * math.pi * r, math.pi * B.F.c                      # mm across u and v (at the equator)
    ku = np.fft.fftfreq(nu, Lu / nu)[None, :]
    kv = np.fft.fftfreq(nv, Lv / nv)[:, None]
    env = np.exp(-0.5 * ((ku * skin["across_mm"]) ** 2 + (kv * skin["along_mm"]) ** 2) * (2 * math.pi) ** 2 / 4)
    n = np.real(np.fft.ifft2(np.fft.fft2(rng.normal(size=(nv, nu))) * env))
    n /= n.std()
    h = -np.abs(n)
    h = (h - h.mean()) / h.std() * skin["rms_mm"]
    CUT.write_pfm(path, h.astype(np.float32))
    return {"file": os.path.basename(path), "mm_per_px": [Lu / nu, Lv / nv], **skin}


# --- writing ------------------------------------------------------------------------------------
def rot_matrix(axis_to):
    """The rotation taking the fruit's +z to `axis_to` (a unit vector), about the axis perpendicular to both."""
    z = np.array([0, 0, 1.0])
    b = np.asarray(axis_to, float) / np.linalg.norm(axis_to)
    c = float(z @ b)
    if c > 1 - 1e-12:
        return np.eye(3)
    if c < -1 + 1e-12:
        return np.diag([1.0, -1.0, -1.0])
    ax = np.cross(z, b)
    s = np.linalg.norm(ax)
    ax /= s
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def place(P, N, R, t):
    return P @ R.T + t, N @ R.T


MATERIALS = {   # part -> (medium, roughness, extra)
    "pericarp_outer": ("pericarp_outer", 0.45),        # [A] matte epicarp; S4: 0.3 looked like plastic at 2.55x
    "pericarp_inner": ("pericarp_inner", 0.3),
    "aril": ("aril", 0.0),
    "testa": ("testa", 0.05),
}


def write_part(out, name, mesh, R, t, lines, which, part, prefix, texture=None):
    P, N, UV, T = mesh.arrays()
    P, N = place(P, N, R, t)
    fn = f"{prefix}{name}.ply"
    write_ply(os.path.join(out, fn), P.astype(np.float32), N.astype(np.float32), T.astype(np.int32),
              UV.astype(np.float32))
    lines.append("AttributeBegin")
    if part == "cotyledon":
        r = LO.cotyledon_reflectance(which)
        lines.append(f'  Material "diffuse" "spectrum reflectance" [ 360 {r:g} 830 {r:g} ]')
    else:
        med, rough = MATERIALS[part]
        lines.append(f'  MediumInterface "lychee_{med}" ""')
        lines.append("  " + LO.pbrt_surface(med, which, displacement=texture, roughness=rough))
    lines.append(f'  Shape "plymesh" "string filename" [ "{fn}" ]')
    lines.append("AttributeEnd")
    return len(P), len(T)


def build(cfg, out, name, parts, cut_z=None, axis_to=(0, 0, 1), at=(0, 0, 0), seed=0, cut_texture=None, prefix="",
          lines=None, aril_uv=None, skin_grain=None):
    """Write the parts' PLYs into `out`, append their pbrt lines; returns (lines, Builder)."""
    which = cfg["material_set"]
    B = Builder(cfg, cut_z, seed)
    R, t = rot_matrix(axis_to), np.asarray(at, float)
    lines = [] if lines is None else lines
    stats = {}
    if "pericarp" in parts:
        gtex = None
        if skin_grain is not None:
            gtex = f"{name}_grain"
            lines.insert(0, f'Texture "{gtex}" "float" "imagemap" "string filename" [ "{skin_grain}" ] '
                            f'"string wrap" "repeat"')
        red, white = B.pericarp(outer_uv=B.uv_sphere if skin_grain is not None else None)
        stats["pericarp_outer"] = write_part(out, f"{name}_peri_red", red, R, t, lines, which, "pericarp_outer", prefix,
                                             texture=gtex)
        stats["pericarp_inner"] = write_part(out, f"{name}_peri_white", white, R, t, lines, which, "pericarp_inner",
                                             prefix)
    if "aril" in parts:
        tex = None
        if cut_texture is not None and cut_z is not None:
            tex = f"{name}_cut"
            lines.insert(0, f'Texture "{tex}" "float" "imagemap" "string filename" [ "{cut_texture}" ] '
                            f'"string wrap" "clamp"')
        elif aril_uv is not None:
            tex = f"{name}_skin"
            lines.insert(0, f'Texture "{tex}" "float" "imagemap" "string filename" [ "{aril_uv}" ] '
                            f'"string wrap" "repeat"')
        m = B.aril(outer_uv=B.uv_sphere if aril_uv is not None else None)
        stats["aril"] = write_part(out, f"{name}_aril", m, R, t, lines, which, "aril", prefix, texture=tex)
    if "seed" in parts:
        testa, cot = B.seed()
        stats["testa"] = write_part(out, f"{name}_testa", testa, R, t, lines, which, "testa", prefix)
        stats["cotyledon"] = write_part(out, f"{name}_cotyledon", cot, R, t, lines, which, "cotyledon", prefix)
    return lines, B, stats


def write_fragment(out, name, which, body, note):
    media = LO.pbrt_media(which)
    with open(os.path.join(out, f"{name}.pbrt"), "w") as f:
        f.write(f"# {note}\n# written by objects/lychee/lychee.py; materials: materials/lychee/material.json, set "
                f"{which!r}\n")
        f.write("\n".join(media + body) + "\n")


def section(cfg, out, name, cut_z, seed, cut_params=None):
    """The half below a transverse cut, lying with its cut face to the camera (-Y), the fruit's axis along Y."""
    import cut as CUT
    os.makedirs(out, exist_ok=True)
    B0 = Builder(cfg, cut_z, seed)
    tex = f"{name}_cut.pfm"
    info = CUT.write_cut_texture(os.path.join(out, tex), B0, cut_params or CUT.load(), seed)
    axis_to = (0, -1, 0)
    grain = cfg["tubercles"].get("grain")
    ginfo = None
    if grain:
        ginfo = write_skin_grain(os.path.join(out, f"{name}_grain.pfm"), B0, {k: v(x) for k, x in grain.items()}, seed)
    body, B, stats = build(cfg, out, name, ("pericarp", "aril", "seed"), cut_z=cut_z, axis_to=axis_to, seed=seed,
                           cut_texture=tex, skin_grain=ginfo["file"] if ginfo else None)
    # the silhouette for framing: the dome's profile (tubercles as their mean height) and the flat cut face
    lift = float(np.mean(B.F.H)) * 0.5
    r, z = B.envelope_profile(lift)
    pieces = [[[float(r[0]), 0.0], [float(z[0]), float(z[0])]], [r.tolist(), z.tolist()]]
    pieces[0] = [np.linspace(0, r[0], 50).tolist(), np.full(50, z[0]).tolist()]
    R = rot_matrix(axis_to)
    json.dump({"kind": "revolved", "origin": [0.0, 0.0, 0.0], "axis": (R @ [0, 0, 1.0]).tolist(),
               "pieces": [[np.round(p[0], 5).tolist(), np.round(p[1], 5).tolist()] for p in pieces],
               "about": "the lychee half's outer profile (r, z along the fruit's axis, z = 0 at the fruit's centre), the "
                        "tubercles as half their mean height; first piece the cut face, second the dome "
                        "(objects/lychee/lychee.py)"}, open(os.path.join(out, f"{name}.silhouette.json"), "w"))
    write_fragment(out, name, cfg["material_set"], body,
                   f"a lychee ({cfg['name']}) cut across at z = {cut_z} mm: the half towards the apex, its cut face to "
                   f"-Y; {B.F.n_plates} tubercles {B.F.spacing:.2f} mm apart")
    meta = {"config": cfg["name"], "cut_z_mm": cut_z, "seed": seed, "plates": B.F.n_plates,
            "spacing_mm": B.F.spacing, "parts": stats, "cut_texture": info, "skin_grain": ginfo}
    json.dump(meta, open(os.path.join(out, f"{name}.json"), "w"), indent=1)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--section", action="store_true")
    ap.add_argument("--cut-z", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out")
    a = ap.parse_args()
    cfg = load(a.config)
    if a.section:
        out = a.out or os.path.join(ROOT, "out/lychee/objects", f"{cfg['name']}_section")
        meta = section(cfg, out, f"{cfg['name']}_section", a.cut_z, a.seed)
        print(json.dumps(meta, indent=1))
    else:
        raise SystemExit("--section, or use materials/lychee/card.py for the card's pieces")


if __name__ == "__main__":
    main()
