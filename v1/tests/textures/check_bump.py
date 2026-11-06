"""Test a, the check: the highlight's stripes of the bump map, pbrt against Cycles against the geometry.

    python3 -I tests/textures/check_bump.py

Reads out/textures/bump/{pbrt,cyc}_{bump,zero,plain}.exr. The oracle is geometric optics on the slab: per pixel
ray, the normal (-h', 0, 1) of h = A sin(kx), the mirror direction, and whether it meets the light (4x4
sub-pixels, so a coverage). Stripes are the profile along x, averaged over the rows (they depend on x only).
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gen_bump as G  # noqa: E402

D = os.path.join(C.OUT, "bump")
ROWS = slice(120, 420)


def oracle(amp=G.AMP):
    k = 2 * math.pi / G.PERIOD
    ss = 4
    res = (G.RES[0] * ss, G.RES[1] * ss)
    eye, d = C.pixel_rays(G.EYE, G.TARGET, G.UP, G.FOV, res, rows=slice(ROWS.start * ss, ROWS.stop * ss))
    t = -eye[2] / d[..., 2]
    x = eye[0] + t * d[..., 0]
    s = amp * k * np.cos(k * x)
    n = np.stack([-s, 0 * s, 1 + 0 * s], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    r = d - 2 * (d * n).sum(-1, keepdims=True) * n
    p = np.stack([x, eye[1] + t * d[..., 1], 0 * x], -1)
    ln = np.array(G.LIGHT_N, float)
    ln /= np.linalg.norm(ln)
    ref = np.array([0.0, 0.0, 1.0])
    e1 = np.cross(ref, ln)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ln, e1)
    tl = ((np.array(G.LIGHT_C) - p) @ ln) / (r @ ln)
    q = p + tl[..., None] * r - np.array(G.LIGHT_C)
    hit = (tl > 0) & (np.abs(q @ e1) < G.LIGHT_SIZE[0] / 2) & (np.abs(q @ e2) < G.LIGHT_SIZE[1] / 2) & (x > -G.HALF) & (x < G.HALF)
    cov = hit.reshape(hit.shape[0] // ss, ss, G.RES[0], ss).mean((1, 3))
    return cov.mean(0), x.reshape(-1, G.RES[0], ss)[0].mean(1)


def profile(path):
    a = C.read_image(path)[ROWS].mean(2)
    return a.mean(0)


def edges(p, level):
    """Sub-pixel crossings of `level` (rising +1, falling -1)."""
    q = np.convolve(p, np.ones(3) / 3, "same")
    out = []
    for i in range(2, len(q) - 2):
        if (q[i] - level) * (q[i + 1] - level) < 0:
            out.append((i + (level - q[i]) / (q[i + 1] - q[i]) + 0.5, 1 if q[i + 1] > q[i] else -1))
    return out


def stripes(p, hi):
    """(start, end) of each lit stripe, in px: a rising edge followed by the next falling one."""
    e = edges(p, 0.5 * hi)
    return [(a, b) for (a, sa), (b, sb) in zip(e, e[1:]) if sa == 1 and sb == -1]


def compare(name, A, B, tol_px=1.0):
    n = min(len(A), len(B))
    if len(A) != len(B):
        print(f"  {name}: {len(A)} vs {len(B)} stripes")
    pos = [abs((a0 + a1) / 2 - (b0 + b1) / 2) for (a0, a1), (b0, b1) in zip(A, B)]
    wid = [((a1 - a0) / (b1 - b0)) for (a0, a1), (b0, b1) in zip(A, B)]
    print(f"  {name}: {n} stripes; centre offset mean {np.mean(pos):.2f} px, max {np.max(pos):.2f} px; "
          f"width ratio mean {np.mean(wid):.3f} (min {np.min(wid):.3f}, max {np.max(wid):.3f})")
    return np.max(pos) < tol_px


def main():
    cov, xs = oracle()
    pitch = G.PERIOD * G.RES[0] / 36.0
    print(f"slab period {G.PERIOD} mm = {pitch:.0f} px (36 mm across); slope amplitude {G.SLOPE}")
    prof = {}
    for r in ("pbrt", "cyc"):
        for v in ("bump", "zero", "plain", "ply", "png"):
            f = os.path.join(D, f"{r}_{v}.exr")
            if os.path.exists(f):
                prof[(r, v)] = profile(f)
    # the plateau (full-coverage level) of each renderer: the plain render's lit-region mean
    ok = True
    st = {"oracle": stripes(cov, 1.0)}
    levels = {}
    for r in ("pbrt", "cyc"):
        if (r, "bump") in prof:
            levels[r] = np.percentile(prof[(r, "bump")][cov > 0.99], 50) if (cov > 0.99).any() else prof[(r, "bump")].max()
            st[r] = stripes(prof[(r, "bump")], levels[r])
    print("stripes found:", {k: len(v) for k, v in st.items()})
    for r in ("pbrt", "cyc"):
        if r in st:
            ok &= compare(f"{r} vs oracle", st[r], st["oracle"])
    if "pbrt" in st and "cyc" in st:
        ok &= compare("pbrt vs Cycles", st["pbrt"], st["cyc"])
    for r in ("pbrt", "cyc"):          # the plymesh slab (UVs from "u","v" properties); the map as a 16-bit PNG
        for v, what in (("ply", "plymesh slab"), ("png", "16-bit PNG map")):
            if (r, v) in prof:
                lv = np.percentile(prof[(r, v)][cov > 0.99], 50)
                ok &= compare(f"{r} {what} vs oracle", stripes(prof[(r, v)], lv), st["oracle"])
    if "pbrt" in levels and "cyc" in levels:
        a, b = prof[("pbrt", "bump")], prof[("cyc", "bump")]
        print(f"  profile mean pbrt/Cycles (bump) {a.mean() / b.mean():.3f}; correlation {np.corrcoef(a, b)[0, 1]:.4f}")
        for r in ("pbrt", "cyc"):
            c = np.corrcoef(prof[(r, 'bump')], cov)[0, 1]
            print(f"  {r}: correlation with the oracle coverage {c:.4f}; mean {prof[(r, 'bump')].mean():.4f}, "
                  f"oracle coverage x plateau {cov.mean() * levels[r]:.4f}")
    # zero map = no texture
    for r in ("pbrt", "cyc"):
        if (r, "zero") in prof and (r, "plain") in prof:
            A = C.read_image(os.path.join(D, f"{r}_zero.exr"))
            B = C.read_image(os.path.join(D, f"{r}_plain.exr"))
            print(f"  {r}: zero map vs no texture: max |diff| {np.abs(A - B).max():.3g}, "
                  f"mean |diff| {np.abs(A - B).mean():.3g} (image mean {B.mean():.4g})")
    if "pbrt" in levels and "cyc" in levels:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
        ax[0].plot(cov * levels["pbrt"], "k", lw=1, label="oracle (geometry)")
        ax[0].plot(prof[("pbrt", "bump")], "r", lw=0.8, label="pbrt")
        ax[0].plot(prof[("cyc", "bump")], "b", lw=0.8, label="Cycles")
        ax[0].legend()
        ax[0].set_title("bump-map highlight stripes along x (mean of rows 120-420)")
        ax[1].plot(prof[("pbrt", "bump")] - prof[("cyc", "bump")], "g", lw=0.8)
        ax[1].set_ylabel("pbrt - Cycles")
        ax[1].set_xlabel("column")
        fig.savefig(os.path.join(D, "stripes.png"), dpi=80)
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
