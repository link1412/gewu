"""The Ru washer's meshes: the body as a closed opaque solid, and the glaze as a closed shell for its medium
(docs/slab.md: Cycles fills a medium only inside a watertight mesh), from the profile in form.json (form.py).

    python3 -I objects/ru_washer/washer.py --out out/ru/washer/mesh [--thickness uniform|thin] [--e0 0.5]
                                           [--bare-foot-mm 0] [--n-around 360]

Frame: mm, z up along the axis, z = 0 on the ground; right-handed (scene.py writes pbrt's camera for it).

- The measured profile (form.json) is the glaze's outer surface as photographed. The body is that surface moved
  inwards by E_REF = 0.5 mm [A: the glaze thickness assumed when the body is derived from the photo]; the body is then
  the fixed thing, and the glaze's outer surface is the body moved outwards by the thickness field e(s) (s the arc
  length along the profile, mm from the axis under the base). With e = E_REF everywhere it is the measured surface
  again. A thinner glaze somewhere (thin_edges) or none (bare_foot) puts the surface inside the photo's outline
  there, as it would be on the real piece.
- The glaze shell is closed: its outer surface (normals out), and an inner surface DELTA = 0.02 mm inside the body
  (normals into the body), so the opaque body lies inside the shell and no ray reaches the inner face; where the
  glaze stops (bare_foot) the two are joined by a ring (a cap). The shell and the body each pass
  tools/shell.py's watertight() (0 bad edges).
- Ru ware is glazed all over and fired on spurs under the base (满釉支烧 [I], the usual account of Ru ware; not
  checked against a single source here). The photo shows the foot ring's outer face and its bottom edge glazed,
  with brown patches on the edge where the glaze is thin or worn through: so the default glazes everything; the
  spur marks under the base (not seen) are left out; --bare-foot-mm leaves the ring's lowest band bare instead.
- The thickness field's shapes are [A] placeholders until the craft layer (glaze flow) gives e(s):
  uniform(e0); thin_edges(e0, f_edge, length): e0 (1 - (1 - f_edge) exp(-(d / length)^2)), d the distance along
  the profile to the nearest convex edge (the lip's top, the foot ring's bead, its inner bottom edge, its top edge).
- Mesh: each piece of the profile is resampled for a sagitta under SAG_MM (0.004 mm: 0.06 px at 1920 px across the
  washer), and revolved in n_around steps (360: the chord's sagitta at the rim is 0.04 px at that size); a vertex
  on the axis is a pole. Smooth normals (the profile's corners are filleted), split only at the caps. UV: u = phi / 2 pi,
  v = s / L along the measured profile (L in mesh.json).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import form as fm  # noqa: E402
import shell  # noqa: E402

E_REF = 0.5          # mm [A]: the glaze's thickness taken when the body is derived from the photographed surface
DELTA = 0.02         # mm: the shell's inner surface lies this far inside the body
SAG_MM = 0.004       # mm: the profile's chord sagitta
CONVEX_EDGES = ("lip", "bead", "c_foot_inner", "foot_top")


# --- the thickness field e(s) ----------------------------------------------------------------------------------
def uniform(e0=E_REF):
    def e(s, prof):
        return np.full(len(s), float(e0))
    e.about = {"kind": "uniform", "e0_mm": e0, "tag": "A"}
    return e


def thin_edges(e0=E_REF, f_edge=0.4, length=1.5):
    """Thinner on convex edges, where surface tension draws a glaze away when it melts [A: the shape and both numbers
    are placeholders, until a glaze-flow model gives e(s)]."""
    def e(s, prof):
        d = np.full(len(s), np.inf)
        for name in CONVEX_EDGES:
            k = np.nonzero(prof["lab"] == name)[0]
            if len(k) == 0:
                continue
            if name == "lip":                       # its apex: the top of the half round
                apex = s[k[np.argmax(prof["C"][k, 1])]]
            else:                                   # the middle of the fillet's arc
                apex = s[k[len(k) // 2]]
            d = np.minimum(d, np.abs(s - apex))
        return e0 * (1 - (1 - f_edge) * np.exp(-(d / length) ** 2))
    e.about = {"kind": "thin_edges", "e0_mm": e0, "f_edge": f_edge, "length_mm": length, "tag": "A"}
    return e


# --- profile helpers -----------------------------------------------------------------------------------------------
def arclength(C):
    return np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])


def offset(C, d):
    """The profile moved along its outward normals by d (mm, per point; negative = inwards). Points on the axis stay
    on it."""
    N = fm.normals(C)
    O = C + np.asarray(d, float)[:, None] * N
    O[C[:, 0] < 1e-9, 0] = 0.0
    return O


def adaptive(C, sag=SAG_MM, hmax=0.5, hmin=0.01):
    """Indices into the dense polyline C for a resampling whose chords keep a sagitta under `sag` (h = sqrt(8 rho sag))."""
    s = arclength(C)
    t = np.gradient(C, axis=0)
    ang = np.unwrap(np.arctan2(t[:, 1], t[:, 0]))
    kappa = np.abs(np.gradient(ang, s, edge_order=1))
    h = np.clip(np.sqrt(8 * sag / np.maximum(kappa, 1e-9)), hmin, hmax)
    n = np.concatenate([[0], np.cumsum(np.diff(s) / (0.5 * (h[1:] + h[:-1])))])
    want = np.arange(0, math.floor(n[-1]) + 1)
    idx = np.unique(np.concatenate([np.searchsorted(n, want), [len(C) - 1]]))
    return idx[idx < len(C)]


# --- revolving -----------------------------------------------------------------------------------------------------
class Builder:
    """Accumulates revolved curves: each curve (n, 2) with its own smooth normals; rings of n_around + 1 vertices
    (the seam duplicated for the UVs, at the same position bit for bit) or one pole vertex on the axis."""

    def __init__(self, n_around):
        self.n = n_around
        ph = 2 * np.pi * np.arange(n_around + 1) / n_around
        self.c, self.s = np.cos(ph), np.sin(ph)
        self.c[-1], self.s[-1] = self.c[0], self.s[0]
        self.u = np.arange(n_around + 1) / n_around
        self.P, self.N, self.UV, self.T = [], [], [], []
        self.nv = 0

    def curve(self, C, N2, v):
        """C (m, 2) points, N2 (m, 2) outward normals (the 3D surface's side), v (m,) texture coordinate."""
        rows = []
        for (r, z), (nr, nz), vv in zip(C, N2, v):
            if r < 1e-9:
                rows.append(np.array([self.nv]))
                self.P.append(np.array([[0.0, 0.0, z]]))
                self.N.append(np.array([[0.0, 0.0, 1.0 if nz > 0 else -1.0]]))
                self.UV.append(np.array([[0.5, vv]]))
                self.nv += 1
            else:
                k = self.n + 1
                rows.append(np.arange(self.nv, self.nv + k))
                self.P.append(np.c_[r * self.c, r * self.s, np.full(k, z)])
                self.N.append(np.c_[nr * self.c, nr * self.s, np.full(k, nz)])
                self.UV.append(np.c_[self.u, np.full(k, vv)])
                self.nv += k
        n = self.n
        for a, b in zip(rows[:-1], rows[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            j = np.arange(n)
            if len(a) == 1:
                self.T.append(np.c_[np.full(n, a[0]), b[j], b[j + 1]])
            elif len(b) == 1:
                self.T.append(np.c_[a[j], np.full(n, b[0]), a[j + 1]])
            else:
                self.T.append(np.c_[a[j], b[j], b[j + 1]])
                self.T.append(np.c_[a[j], b[j + 1], a[j + 1]])

    def mesh(self):
        P, N, UV = np.vstack(self.P), np.vstack(self.N), np.vstack(self.UV)
        T = np.vstack(self.T).astype(np.int64)
        gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        flip = np.einsum("ij,ij->i", gn, N[T].mean(1)) < 0       # wind each face with its outward normal
        T[flip] = T[flip][:, [0, 2, 1]]
        return P, N, T, UV


def deviation(seed, ovality=0.012, rim_mm=0.5, wave=0.002, kmax=6, height=32.3, rim_r=64.0):
    """This piece's departure from the turned form, a smooth displacement d(P) of the object frame (mm) [A: every
    amplitude; a piece of the batch, DESIGN 0]: the firing's slump leaves it a little oval (ovality, of the radius,
    at the rim) and its rim not level (rim_mm, harmonics 2..kmax falling as 1/k) with a slight waviness of the walls
    (wave); all grow towards the rim, the foot being held on the kiln furniture. Apply it to the body, the glaze and
    the cracks alike (deform)."""
    rng = np.random.default_rng(seed)
    phi2, eps2 = rng.uniform(0, 2 * np.pi), ovality * rng.uniform(0.6, 1.0)
    ks = np.arange(2, kmax + 1)
    a, psi = rng.normal(size=len(ks)) * rim_mm / ks, rng.uniform(0, 2 * np.pi, len(ks))
    b, chi = rng.normal(size=len(ks)) * wave / ks, rng.uniform(0, 2 * np.pi, len(ks))

    def d(P):
        x, y, z = np.asarray(P, float).T
        r, phi = np.hypot(x, y), np.arctan2(y, x)
        w = np.clip(z / height, 0.0, 1.0)
        harm = lambda amp, ph: sum(amp[i] * np.cos(k * phi + ph[i]) for i, k in enumerate(ks))
        dr = r * (eps2 * w * np.cos(2 * (phi - phi2)) + w ** 2 * harm(b, chi))
        dz = w * (r / rim_r) ** 2 * harm(a, psi)
        return np.stack([dr * np.cos(phi), dr * np.sin(phi), dz], 1)

    d.about = {"seed": seed, "ovality": round(float(eps2), 5), "ovality_axis_deg": round(float(np.degrees(phi2)), 2),
               "rim_harmonics_mm": dict(zip(ks.tolist(), np.round(a, 4).tolist())), "tag": "A"}
    return d


def deform(P, N, d, h=0.01):
    """Positions moved by d, normals by the inverse transpose of the map's Jacobian (central differences)."""
    P = np.asarray(P, float)
    J = np.repeat(np.eye(3)[None], len(P), 0)
    for j in range(3):
        e = np.zeros(3)
        e[j] = h
        J[:, :, j] += (d(P + e) - d(P - e)) / (2 * h)
    N2 = np.linalg.solve(np.transpose(J, (0, 2, 1)), np.asarray(N, float)[..., None])[..., 0]
    N2 /= np.linalg.norm(N2, axis=1, keepdims=True)
    return P + d(P), N2


def write_ply(path, P, N, tris, uv=None):
    """Binary little-endian PLY, float xyz, normals, u v; int vertex_indices (as materials/guan_glaze/card.py)."""
    cols = [np.asarray(P, np.float32), np.asarray(N, np.float32)] + ([np.asarray(uv, np.float32)] if uv is not None else [])
    V = np.ascontiguousarray(np.concatenate(cols, 1))
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(P)}",
            "property float x", "property float y", "property float z",
            "property float nx", "property float ny", "property float nz"]
    if uv is not None:
        head += ["property float u", "property float v"]
    head += [f"element face {len(tris)}", "property list uchar int vertex_indices", "end_header"]
    face = np.zeros(len(tris), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = np.asarray(tris, np.int32)
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.astype("<f4").tobytes())
        f.write(face.tobytes())


# --- the washer ----------------------------------------------------------------------------------------------------
def load_form(path=fm.FORM):
    F = json.load(open(path))
    p = {k: v["value"] for k, v in F["fitted"].items()}
    return p, F["assumed"]


def build(e=None, bare_foot_mm=0.0, n_around=360, form_path=fm.FORM):
    """Body and glaze-shell meshes and their record. e: a thickness field (uniform() by default)."""
    e = e or uniform()
    p, assumed = load_form(form_path)
    prof = fm.closed_profile(p, assumed)
    C, lab = prof["C"], prof["lab"]
    s = arclength(C)
    L = float(s[-1])
    body = offset(C, np.full(len(C), -E_REF))
    eg = np.asarray(e(s, prof), float)
    foot = np.isin(lab, ["foot_bottom", "bead", "c_foot_inner"])
    bare = foot & (body[:, 1] - body[:, 1].min() < bare_foot_mm) if bare_foot_mm > 0 else np.zeros(len(C), bool)
    eg[bare] = 0.0
    if np.any(eg[~bare] <= 0):
        raise ValueError("the glaze thickness must be positive where there is glaze")
    outer = offset(body, eg)
    outer[bare] = body[bare]
    inner = offset(body, np.full(len(C), -DELTA))
    # where the profile's tangent turns sharply between two of its pieces (a fillet's end against the wall's
    # Bezier), normals from differences can swing so far that an offset point steps backwards: drop such points
    # from all the curves alike (measured: 2 points at the crease over the foot ring)
    for _ in range(3):
        d0 = np.diff(C, axis=0)
        rev = np.zeros(len(C), bool)
        for A in (body, outer, inner):
            rev[1:] |= np.einsum("ij,ij->i", np.diff(A, axis=0), d0) <= 0
        rev[[0, -1]] = False
        if not rev.any():
            break
        k = ~rev
        C, lab, s, eg, bare, body, outer, inner = (q[k] for q in (C, lab, s, eg, bare, body, outer, inner))
    # stand it on the ground: the lowest point of what touches it at z = 0
    z0 = float(min(outer[:, 1].min(), body[:, 1].min()))
    for A in (C, body, outer, inner):
        A[:, 1] -= z0
    v = s / L

    # the body: one closed surface (the profile is smooth: its corners are filleted, so one set of normals)
    keep = adaptive(body)
    B = Builder(n_around)
    B.curve(body[keep], fm.normals(body)[keep], v[keep])
    body_mesh = B.mesh()

    # the glaze shell: per glazed run, outer (forward) + cap + inner (backward) + cap, a closed loop
    G = Builder(n_around)
    runs = []
    gl = ~bare
    st = np.nonzero(gl & ~np.concatenate([[False], gl[:-1]]))[0]
    en = np.nonzero(gl & ~np.concatenate([gl[1:], [False]]))[0]
    No, Ni = fm.normals(outer), -fm.normals(inner)     # the inner face looks into the body, away from the glaze
    tang = np.gradient(C, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    for i0, i1 in zip(st, en):
        idx = np.arange(i0, i1 + 1)
        k = np.unique(np.concatenate([idx[adaptive(outer[idx])], [i0, i1]]))
        G.curve(outer[k], No[k], v[k])
        G.curve(inner[k[::-1]], Ni[k[::-1]], v[k[::-1]])
        for i, sgn in ((i1, 1.0), (i0, -1.0)):         # a ring where the glaze stops off the axis
            if C[i, 0] > 1e-9:
                seg = np.array([outer[i], inner[i]]) if sgn > 0 else np.array([inner[i], outer[i]])
                n2 = sgn * tang[i]                       # facing along the profile, out of the glazed run
                G.curve(seg, np.vstack([n2, n2]), np.array([v[i], v[i]]))
        runs.append([round(float(s[i0]), 4), round(float(s[i1]), 4)])
    glaze_mesh = G.mesh()
    rec = {
        "form": os.path.relpath(form_path, ROOT),
        "frame": "mm; z up along the axis; z = 0 the ground (the lowest point of the washer); right-handed",
        "E_REF_mm": E_REF, "DELTA_mm": DELTA, "n_around": n_around, "sag_mm": SAG_MM,
        "profile_length_mm": round(L, 4), "uv": "u = phi / 2 pi, v = s / profile_length (s along the measured profile)",
        "thickness": getattr(e, "about", {"kind": "custom"}),
        "thickness_range_mm": [round(float(eg[~bare].min()), 4), round(float(eg[~bare].max()), 4)],
        "bare_foot_mm": bare_foot_mm, "glazed_runs_s_mm": runs,
        "lifted_mm": round(-z0, 4),
        "floor_z_mm": prof["floor_z"], "fillets_used_mm": prof["fillets_used"],
        "profiles": {"measured": np.round(C, 5).tolist()},
    }
    return body_mesh, glaze_mesh, rec, {"body": body, "outer": outer, "inner": inner, "measured": C, "lab": lab}


def check(body_mesh, glaze_mesh, curves):
    """Watertightness and the clearances between the surfaces."""
    from scipy.spatial import cKDTree
    out = {"body_bad_edges": shell.watertight(body_mesh[0], body_mesh[2]),
           "glaze_bad_edges": shell.watertight(glaze_mesh[0], glaze_mesh[2])}
    tb = cKDTree(curves["body"])
    di, _ = tb.query(curves["inner"])
    do, _ = tb.query(curves["outer"])
    out["inner_to_body_mm"] = [round(float(di.min()), 5), round(float(di.max()), 5)]
    out["outer_to_body_mm"] = [round(float(do.min()), 5), round(float(do.max()), 5)]
    for k in ("body", "glaze"):
        P, N, T, _ = body_mesh if k == "body" else glaze_mesh
        out[f"{k}_vertices"], out[f"{k}_triangles"] = int(len(P)), int(len(T))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out/ru/washer/mesh"))
    ap.add_argument("--thickness", choices=["uniform", "thin"], default="uniform")
    ap.add_argument("--e0", type=float, default=E_REF)
    ap.add_argument("--bare-foot-mm", type=float, default=0.0)
    ap.add_argument("--n-around", type=int, default=360)
    a = ap.parse_args()
    e = uniform(a.e0) if a.thickness == "uniform" else thin_edges(a.e0)
    bm, gm, rec, curves = build(e, a.bare_foot_mm, a.n_around)
    rec["check"] = check(bm, gm, curves)
    os.makedirs(a.out, exist_ok=True)
    write_ply(os.path.join(a.out, "body.ply"), bm[0], bm[1], bm[2], bm[3])
    write_ply(os.path.join(a.out, "glaze.ply"), gm[0], gm[1], gm[2], gm[3])
    json.dump(rec, open(os.path.join(a.out, "mesh.json"), "w"), indent=1)
    print(json.dumps(rec["check"]))


if __name__ == "__main__":
    main()
