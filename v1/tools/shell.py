"""Closed meshes for media (docs/slab.md).

Cycles renders a medium only inside a watertight mesh: a glaze written as an open sheet over its body (pbrt's
MediumInterface semantics, which need no closed mesh) comes out 12-24% dark there, measured against an independent
Monte Carlo (tools/slab.py), while pbrt is right; closing the same sheet into a box fixes it, two sheets with open
sides do not. So a glaze, or any medium, is written as a closed shell, and tools/rgbscene.py refuses a medium on a
mesh that is not watertight.

    box(hx, hy, z_top, z_bottom)       a closed box (outward normals, per-face vertices); the top carries UV 0..1
    watertight(P, tris)                the edges that are not shared by exactly two faces of opposite orientation,
                                       after welding the vertices by position (0 for a closed, consistent mesh)
    read_ply(path)                     positions and triangles of one of our binary PLY files
"""

import numpy as np


def box(hx, hy, z_top, z_bottom):
    """Six faces, each its own four vertices (flat normals), two triangles each, wound with the outward normal.
    Returns P (24, 3), N (24, 3), tris (12, 3), uv (24, 2): the top's uv spans 0..1 over the tile (for a height map
    in the material), the other faces' uv is 0 (a constant: no bump there)."""
    if not z_bottom < z_top:
        raise ValueError("box: z_bottom must be below z_top")
    X, Y, t, b = hx, hy, z_top, z_bottom
    faces = [
        ([(-X, -Y, t), (X, -Y, t), (X, Y, t), (-X, Y, t)], (0, 0, 1)),
        ([(-X, -Y, b), (-X, Y, b), (X, Y, b), (X, -Y, b)], (0, 0, -1)),
        ([(-X, -Y, b), (X, -Y, b), (X, -Y, t), (-X, -Y, t)], (0, -1, 0)),
        ([(X, Y, b), (-X, Y, b), (-X, Y, t), (X, Y, t)], (0, 1, 0)),
        ([(X, -Y, b), (X, Y, b), (X, Y, t), (X, -Y, t)], (1, 0, 0)),
        ([(-X, Y, b), (-X, -Y, b), (-X, -Y, t), (-X, Y, t)], (-1, 0, 0)),
    ]
    P, N, T, UV = [], [], [], []
    for k, (vs, n) in enumerate(faces):
        i = len(P)
        P += vs
        N += [n] * 4
        T += [(i, i + 1, i + 2), (i, i + 2, i + 3)]
        UV += [((x + X) / (2 * X), (y + Y) / (2 * Y)) for x, y, _ in vs] if k == 0 else [(0.0, 0.0)] * 4
    P, N, T, UV = (np.asarray(a, float) for a in (P, N, T, UV))
    T = T.astype(np.int64)
    for a, bb, c in T:                       # the winding agrees with the normal
        if np.dot(np.cross(P[bb] - P[a], P[c] - P[a]), N[a]) <= 0:
            raise AssertionError("box: winding")
    return P, N, T, UV


def watertight(P, tris, rel_tol=1e-6):
    """The number of bad edges: after welding vertices closer than rel_tol times the mesh's size, every edge
    (a, b) must occur once as a -> b and once as b -> a. Open boundaries, non-manifold edges and flipped faces count."""
    P = np.asarray(P, float)
    T = np.asarray(tris, np.int64)
    if len(T) == 0:
        return 0
    size = float(np.max(np.ptp(P, axis=0))) or 1.0
    q = np.round(P / (rel_tol * size)).astype(np.int64)
    _, weld = np.unique(q, axis=0, return_inverse=True)
    weld = weld.ravel()
    W = weld[T]
    e = np.concatenate([W[:, [0, 1]], W[:, [1, 2]], W[:, [2, 0]]])
    e = e[e[:, 0] != e[:, 1]]                # degenerate slivers after welding
    fwd = e[:, 0] < e[:, 1]
    key = np.where(fwd[:, None], e, e[:, ::-1])
    sign = np.where(fwd, 1, -1)
    uk, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    net = np.zeros(len(uk), np.int64)
    np.add.at(net, inv.ravel(), sign)
    return int(np.sum((cnt != 2) | (net != 0)))


def read_ply(path):
    """Positions and triangles from a binary little-endian PLY with float x, y, z (other float vertex properties
    allowed) and a face list "uchar int vertex_indices" of triangles, as our writers produce."""
    with open(path, "rb") as f:
        head = []
        while True:
            line = f.readline()
            if not line:
                raise SystemExit(f"{path}: no end_header")
            line = line.decode("ascii", "replace").strip()
            head.append(line)
            if line == "end_header":
                break
        if "format binary_little_endian 1.0" not in head:
            raise SystemExit(f"{path}: only binary little-endian PLY is read here")
        nv = nf = None
        props, cur = [], None
        sizes = {"float": 4, "float32": 4, "double": 8, "float64": 8, "uchar": 1, "uint8": 1, "int": 4, "int32": 4,
                 "uint": 4, "uint32": 4, "short": 2, "ushort": 2}
        types = {"float": "<f4", "float32": "<f4", "double": "<f8", "float64": "<f8", "uchar": "u1", "uint8": "u1",
                 "int": "<i4", "int32": "<i4", "uint": "<u4", "uint32": "<u4", "short": "<i2", "ushort": "<u2"}
        face_list = None
        for line in head:
            w = line.split()
            if w[:2] == ["element", "vertex"]:
                nv, cur = int(w[2]), "v"
            elif w[:2] == ["element", "face"]:
                nf, cur = int(w[2]), "f"
            elif w[:1] == ["element"]:
                cur = "other"
            elif w[:1] == ["property"] and cur == "v":
                props.append((w[2], types[w[1]]))
            elif w[:2] == ["property", "list"] and cur == "f":
                face_list = (types[w[2]], types[w[3]])
        if nv is None or nf is None or face_list is None:
            raise SystemExit(f"{path}: needs vertex and face elements")
        V = np.frombuffer(f.read(nv * sum(np.dtype(t).itemsize for _, t in props)), dtype=props, count=nv)
        rest = f.read()
    P = np.stack([V["x"], V["y"], V["z"]], 1).astype(float)
    ct, it = face_list
    rec = np.dtype([("n", ct), ("i", it, (3,))])
    if len(rest) >= nf * rec.itemsize:
        F = np.frombuffer(rest, dtype=rec, count=nf)
        if np.all(F["n"] == 3):
            return P, F["i"].astype(np.int64)
    raise SystemExit(f"{path}: only triangle faces are read here")
