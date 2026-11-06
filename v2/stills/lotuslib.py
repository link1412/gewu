"""What the lotus shots share: the sheet shader, the sky over the pond, the far leaves and the water. All far out of focus, so all coarse."""

import os

import numpy as np

from kit import color, fbm, mix, sstep

SHEET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thinsheet_shader.py")
FAR_MAT = {"k": 0.32, "rough": 0.5, "spec": 0.35, "sheen": 0.15}


def pond_env(path, sun, top=(0.55, 0.68, 0.86), low=(0.86, 0.9, 0.92), tree=(0.03, 0.07, 0.035), tree_el=11.0, pond=(0.012, 0.03, 0.03), cloud=0.5, disc=(2.0, 160.0), aureole=(14.0, 2.4), gain=1.0, seed=0, soft=0.5, gaps=0.0):
    """A bright hazy day in world directions: what the water and the drops mirror and what lights everything softly. Painted, not measured.

    A line of trees stands round the pond, because that dark band is what gives a drop its dark rim and the water its depth; a plain sky gives neither.
    The sun is here for the glossy rays only (a hard small highlight with a bloom round it); the area light in the scene does the lighting of the diffuse surfaces.
    """
    h, w = 768, 1536
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    d = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    el = np.degrees(lat)
    rgb = mix(color(low), color(top), sstep(0.0, 0.55, np.sin(lat))[..., None])
    cl = sstep(-0.4, 1.3, fbm((h, w), w / 360.0, 12.0, 140.0, 2.8, seed + 20))[..., None]
    rgb = mix(rgb, color([1.05, 1.05, 1.04]), cloud * cl * sstep(0.02, 0.25, np.sin(lat))[..., None])
    # the tree line: an uneven top, and clumps of light and dark
    top_edge = tree_el * (0.75 + 0.3 * fbm((1, w), w / 360.0, 6.0, 60.0, 2.4, seed + 21)[0])
    leaf = 0.75 + 0.5 * fbm((h, w), w / 360.0, 1.0, 14.0, 2.0, seed + 22)
    edge = sstep(top_edge[None, :] + soft, top_edge[None, :] - soft, el)[..., None]
    rgb = mix(rgb, color(tree) * np.clip(leaf, 0.2, 2.2)[..., None], edge)
    if gaps:  # sky through the trees: what puts soft light and dark into the water
        hole = sstep(0.35, 1.2, fbm((h, w), w / 360.0, 3.0, 26.0, 2.4, seed + 23))[..., None]
        rgb = mix(rgb, color(low), gaps * hole * edge)
    rgb = mix(rgb, color(pond), sstep(0.5, -0.5, el)[..., None])
    s = np.clip(d @ np.asarray(sun, np.float32), -1, 1)
    ang = np.degrees(np.arccos(s))
    rgb = rgb + (aureole[1] * np.exp(-((ang / aureole[0]) ** 2)))[..., None] * color([1.0, 0.96, 0.88])
    rgb = rgb + (sstep(disc[0] + 0.25, disc[0] - 0.25, ang) * disc[1])[..., None] * color([1.0, 0.97, 0.92])
    np.save(path, (rgb * gain).astype(np.float32))
    return path


def far_leaf(path, at, R, tilt, azim, seed, n=48):
    """A leaf of the field behind: a dish with a wavy rim and a pale navel, tipped to one side. It only has to carry the right colours into the blur."""
    rng = np.random.default_rng(seed)
    rho = np.linspace(0, 1, n, dtype=np.float32)
    th = np.linspace(0, 2 * np.pi, n * 2, dtype=np.float32)
    Th, Rho = np.meshgrid(th, rho)
    rim = 1 + 0.06 * np.sin(2 * Th + rng.uniform(0, 6)) + 0.03 * np.sin(5 * Th + rng.uniform(0, 6))
    x, y = R * Rho * rim * np.cos(Th), R * Rho * rim * np.sin(Th)
    z = 0.16 * R * Rho**1.6 + 0.05 * R * Rho**3 * np.sin(5 * Th + rng.uniform(0, 6)) + 0.025 * R * Rho**2 * np.sin(13 * Th + rng.uniform(0, 6))
    t, a = np.radians(tilt), np.radians(azim)
    # tip about a horizontal axis
    ca, sa = np.cos(a), np.sin(a)
    u = ca * x + sa * y
    v = -sa * x + ca * y
    u, z = u * np.cos(t) - z * np.sin(t), u * np.sin(t) + z * np.cos(t)
    x, y = ca * u - sa * v, sa * u + ca * v
    tone = rng.uniform(0.75, 1.25)
    ribs = 0.5 + 0.5 * np.cos(23 * Th)
    col = mix(color([0.075, 0.2, 0.075]), color([0.11, 0.25, 0.1]), (0.5 + 0.5 * np.sin(4 * Th + rng.uniform(0, 6)))[..., None]) * tone
    col = mix(col, color([0.3, 0.38, 0.12]), np.exp(-((Rho / 0.09) ** 2))[..., None])
    tr = mix(color([0.1, 0.25, 0.03]), color([0.15, 0.3, 0.04]), (ribs * Rho)[..., None]) * tone  # dark enough that the flower is the brightest thing
    np.savez(path, P=np.stack([x + at[0], y + at[1], z + at[2]], -1).astype(np.float32), col=np.clip(col, 0, 1).astype(np.float32), tr=np.clip(tr, 0, 1).astype(np.float32))
    return path


def stalk(path, at, z0, r=0.45, lean=(0.0, 0.0), n=24):
    """A leaf stalk going down to the water."""
    th = np.linspace(0, 2 * np.pi, 12, dtype=np.float32)
    t = np.linspace(0, 1, n, dtype=np.float32)
    Th, T = np.meshgrid(th, t)
    x = at[0] + lean[0] * T**1.5 + r * np.cos(Th)
    y = at[1] + lean[1] * T**1.5 + r * np.sin(Th)
    z = z0 + (at[2] - z0) * T
    col = np.broadcast_to(color([0.1, 0.17, 0.05]), Th.shape + (3,)).astype(np.float32)
    tr = np.broadcast_to(color([0.16, 0.3, 0.04]), Th.shape + (3,)).astype(np.float32)
    np.savez(path, P=np.stack([x, y, z], -1).astype(np.float32), col=col, tr=tr)
    return path


def water(path, z, x=(-2500.0, 2500.0), y=(-400.0, 6000.0), n=320, seed=7, amp=0.25):
    """The pond as a plane, with slow swells only: it is seen out of focus, as what it mirrors."""
    X, Y = np.meshgrid(np.linspace(x[0], x[1], n, dtype=np.float32), np.linspace(y[0], y[1], n, dtype=np.float32))
    h = fbm((n, n), n / (x[1] - x[0]), 40.0, 600.0, 2.6, seed)
    np.savez(path, P=np.stack([X, Y, z + amp * h], -1).astype(np.float32))
    return path
