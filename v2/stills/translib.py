"""What the light-through shots (s21, s16, s15, s40) share: smooth tubes and strips as triangle soups, bamboo and tree leaves for real blur, and dropping this shot's old painted sky from looks.json.

The looks.json entries for these shots still hold a painted `sky`/`env` from the old versions. kit gives looks.json the last word, and a sky wall at 2400 cm would stand in front of the real background, so `real_background()` keeps only `move`. A stand-in until the entries are cleaned.
"""

import os

import numpy as np

import kit

SOFT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "softsheet_shader.py")


def real_background():
    orig = kit.looks

    def only_move():
        return {k: ({"move": v["move"]} if isinstance(v, dict) and "move" in v else {}) for k, v in orig().items()}

    kit.looks = only_move


def _ring_faces(n, ns, nside, base=0):
    """Quads as triangles for n tubes, each ns rings of nside points."""
    i = np.arange(ns - 1)[None, :, None]
    t = np.arange(n)[:, None, None] * (ns * nside) + base
    j = np.arange(nside)[None, None, :]
    a = t + i * nside + j
    b = t + i * nside + (j + 1) % nside
    c = t + (i + 1) * nside + (j + 1) % nside
    d = t + (i + 1) * nside + j
    return np.concatenate([np.stack([a, b, c], -1).reshape(-1, 3), np.stack([a, c, d], -1).reshape(-1, 3)])


def frames(paths):
    """A rotation-free frame along many paths (n, ns, 3): an approximate parallel transport, good for gently curving paths."""
    t = np.gradient(paths, axis=1)
    t /= np.linalg.norm(t, axis=-1, keepdims=True) + 1e-9
    r = np.zeros_like(t)
    ref = np.array([0.31, 0.53, 0.79], np.float32)
    r0 = np.cross(t[:, 0], ref)
    r0 /= np.linalg.norm(r0, axis=-1, keepdims=True) + 1e-9
    r[:, 0] = r0
    for i in range(1, t.shape[1]):
        p = r[:, i - 1] - t[:, i] * np.sum(r[:, i - 1] * t[:, i], -1, keepdims=True)
        r[:, i] = p / (np.linalg.norm(p, axis=-1, keepdims=True) + 1e-9)
    return r, np.cross(t, r)


def tubes(paths, radius, attrs=None, nside=6, side=None, ht=None, power=2.0):
    """Tubes along (n, ns, 3). radius: half width, scalar, (n,) or (n, ns). `side` (n, ns, 3) fixes the section's width direction and `ht` its half thickness, so a flat strip can lie where it should; power>2 squares the section. Returns dict(V, F, **attrs). attrs per path or per point."""
    paths = np.asarray(paths, np.float32)
    n, ns = paths.shape[:2]
    rad = np.broadcast_to(np.asarray(radius, np.float32).reshape((n, -1) if np.ndim(radius) == 2 else (-1, 1)), (n, ns))
    if side is None:
        s, b = frames(paths)
    else:
        t = np.gradient(paths, axis=1)
        s = side - t * (np.sum(side * t, -1, keepdims=True) / (np.sum(t * t, -1, keepdims=True) + 1e-9))
        s = s / (np.linalg.norm(s, axis=-1, keepdims=True) + 1e-9)
        b = np.cross(t, s)
        b = b / (np.linalg.norm(b, axis=-1, keepdims=True) + 1e-9)
    hh = rad if ht is None else np.broadcast_to(np.asarray(ht, np.float32).reshape((n, -1) if np.ndim(ht) == 2 else (-1, 1)), (n, ns))
    a = np.arange(nside, dtype=np.float32) * 2 * np.pi / nside + np.pi / nside
    ca, sa = np.cos(a), np.sin(a)
    e = 2.0 / power
    cx, cy = np.sign(ca) * np.abs(ca) ** e, np.sign(sa) * np.abs(sa) ** e
    V = paths[:, :, None, :] + (rad[..., None] * cx)[..., None] * s[:, :, None, :] + (hh[..., None] * cy)[..., None] * b[:, :, None, :]
    out = {"V": V.reshape(-1, 3).astype(np.float32), "F": _ring_faces(n, ns, nside).astype(np.int32)}
    for k, v in (attrs or {}).items():
        v = np.asarray(v, np.float32)
        tail = v.shape[1:]
        if v.shape[:2] == (n, ns):  # per point
            pass
        elif len(tail) <= 1 and v.shape[0] == n:  # per path
            v = np.broadcast_to(v.reshape((n, 1) + tail), (n, ns) + tail)
        vv = np.repeat(v[:, :, None], nside, axis=2)
        out[k] = vv.reshape((-1,) + vv.shape[3:]).astype(np.float32)
    return out


def merge(*soups):
    """Several soups into one mesh. All must have the same attributes."""
    keys = [k for k in soups[0] if k not in ("V", "F")]
    base = 0
    Fs = []
    for s in soups:
        Fs.append(s["F"] + base)
        base += len(s["V"])
    out = {"V": np.concatenate([s["V"] for s in soups]), "F": np.concatenate(Fs).astype(np.int32)}
    for k in keys:
        out[k] = np.concatenate([s[k] for s in soups])
    return out


def leaves(rng, at, axis, normal, L, W, col, tr, ns=7, droop=0.25, curl=0.1):
    """Narrow pointed leaves as soups. at (n, 3): the base; axis (n, 3): the way it points; normal (n, 3): its face. L, W (n,). col, tr (n, 3). Width across has 3 points so the midrib folds."""
    n = len(at)
    s = np.linspace(0, 1, ns, dtype=np.float32)
    prof = np.maximum(np.sin(np.pi * s**0.62), 0.0) ** 0.9  # widest a third of the way, drawn out to a point
    A = axis / np.linalg.norm(axis, axis=-1, keepdims=True)
    Nn = normal - A * np.sum(normal * A, -1, keepdims=True)
    Nn /= np.linalg.norm(Nn, axis=-1, keepdims=True) + 1e-9
    Sd = np.cross(A, Nn)
    d = droop * rng.uniform(0.4, 1.6, n)[:, None]
    along = (L[:, None] * s)[..., None]
    drop = (L[:, None] * d * s**2)[..., None]
    mid = at[:, None] + along * A[:, None] - drop * Nn[:, None]
    hw = (0.5 * W[:, None] * prof)[..., None]
    fold = (0.25 * hw) * rng.uniform(0.5, 1.2, n)[:, None, None]
    tw = (curl * rng.normal(0, 1, n))[:, None, None] * s[None, :, None]
    lft = mid - hw * (Sd[:, None] + tw * Nn[:, None]) + fold * Nn[:, None]
    rgt = mid + hw * (Sd[:, None] + tw * Nn[:, None]) + fold * Nn[:, None]
    V = np.stack([lft, mid, rgt], 2)  # n, ns, 3, 3
    idx = np.arange(n * ns * 3).reshape(n, ns, 3)
    a, b, c, e = idx[:, :-1, :-1], idx[:, 1:, :-1], idx[:, 1:, 1:], idx[:, :-1, 1:]
    F = np.concatenate([np.stack([a, b, c], -1).reshape(-1, 3), np.stack([a, c, e], -1).reshape(-1, 3)])
    def per(x):
        return np.repeat(np.asarray(x, np.float32)[:, None], ns * 3, axis=1).reshape(-1, 3)
    return {"V": V.reshape(-1, 3).astype(np.float32), "F": F.astype(np.int32), "col": per(col), "tr": per(tr)}


def save(path, soup):
    np.savez(path, **soup)
    return path
