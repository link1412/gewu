"""Geometry helpers for glaze in a real medium (shots 29, 6, 11, 26, 28).

studio_bpy.grid_mesh only makes one (rows, cols) grid, so anything else is folded out of a grid:
- close_shell: a top sheet and a coarse bottom sheet joined into one closed surface;
- strips:      many disconnected sheets (crack ribbons) in one grid, joined by zero-area quads;
- balls:       many spheres in one grid, the same way.
"""

import numpy as np


def close_shell(top, bot, attrs_top, attrs_bot_value, outward=None):
    """top (ny, nx, 3) and bot (m, nx, 3), rows running the same way. Rows go out along the top and back along the bottom and
    meet the first row again; the first and last columns of the bottom are pulled up onto the top, so the sides are closed.
    Normals (dRow x dCol) are checked against `outward` at the middle of the top, the columns flipped if needed.
    Returns P and the attributes (dict name -> field on the whole grid); attrs_bot_value gives the bottom's constant values."""
    ny, nx = top.shape[:2]
    m = bot.shape[0]
    bot = bot.copy()
    idx = np.round(np.linspace(0, ny - 1, m)).astype(int)
    bot[:, 0] = top[idx, 0]
    bot[:, -1] = top[idx, -1]
    P = np.concatenate([top, bot[::-1], top[:1]], 0)
    out = {}
    for k, f in attrs_top.items():
        tail = np.full((m + 1,) + f.shape[1:], attrs_bot_value[k], f.dtype)
        out[k] = np.concatenate([f, tail], 0)
    if outward is not None:
        j, i = ny // 2, nx // 2
        n = np.cross(top[j + 1, i] - top[j, i], top[j, i + 1] - top[j, i])
        if np.dot(n, outward) < 0:
            P = P[:, ::-1]
            out = {k: v[:, ::-1] for k, v in out.items()}
    return P.astype(np.float32), out


def strips(polys, attrs):
    """polys: list of (n_i, K, 3) arrays, each a ribbon with n_i points along and K levels across. attrs: name -> list of
    (n_i, K) arrays. Two extra columns between ribbons collapse each end to a line, so the joining quads have no area."""
    K = polys[0].shape[1]
    Ps, As = [], {k: [] for k in attrs}
    for j, p in enumerate(polys):
        a0 = np.repeat(p[:1, :1], K, 1)
        a1 = np.repeat(p[-1:, :1], K, 1)
        Ps.extend([a0, p, a1])
        for k in attrs:
            f = attrs[k][j]
            zero = np.zeros((1, K), np.float32)
            As[k].extend([zero, f, zero])
    P = np.concatenate(Ps, 0).transpose(1, 0, 2)  # rows = levels, cols = along
    return P.astype(np.float32), {k: np.concatenate(v, 0).T.astype(np.float32) for k, v in As.items()}


def balls(centers, radii, nlon=14, nlat=9, seed=0):
    """Spheres in one grid. Slightly irregular radii around the sphere are not needed at these sizes. Outward normals."""
    lon = np.linspace(0, 2 * np.pi, nlon + 1)
    lat = np.linspace(-np.pi / 2, np.pi / 2, nlat)
    La, Lo = np.meshgrid(lat, lon, indexing="ij")
    # dRow x dCol must point outward: rows go down in latitude
    La = La[::-1]
    d = np.stack([np.cos(La) * np.cos(Lo), np.cos(La) * np.sin(Lo), np.sin(La)], -1)
    d = d[:, :, :] if np.dot(np.cross(d[nlat // 2 + 1, 3] - d[nlat // 2, 3], d[nlat // 2, 4] - d[nlat // 2, 3]), d[nlat // 2, 3]) > 0 else d[:, ::-1]
    cols = []
    for c, r in zip(centers, radii):
        q = c[None, None] + d * r
        cols.append(np.repeat(c[None, None] + 0 * d[:, :1], 1, 1))
        cols.append(q)
        cols.append(np.repeat(c[None, None] + 0 * d[:, :1], 1, 1))
    return np.concatenate(cols, 1).astype(np.float32)
