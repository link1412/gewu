"""Coat test, the check: pbrt and Cycles against the 1-D stack (materials/qinghua/optics.py) and each other.

For each region far from edges (white, three cobalt bands, the c = 3 step; tile B's red base under the absorbing
coat at three c), the ratio of its camera RGB to the reference plate's (diffuse 0.5, the same light, same pixels):
  analytic: 2 * sum_j w_j L(lambda; mu_j) / sum_j w_j, L = optics.stack(tau, rho, n, mu_in = mu_j) the 1-D stack's
            pi * radiance per unit irradiance from direction j, j over a 24 x 24 grid on the light, w_j its
            irradiance (cos at the tile x cos at the light / r^2); per wavelength, then weighted per channel by the
            sensor x 5500 K (the renders' raw sensor RGB);
  pbrt:     spectral, the reference for the true-geometry coat;
  cycles:   camera RGB (tools/rgbscene.py: the film's per-crossing transmittance by the p = 2 projection).
Across the painted lines (0.2-2 mm wide, c = 3) and the step: the profile along x, averaged over the painted rows;
the line's darkest value against the wide step's, and the step's 10-90% width (the coat's lateral walk).

    python3 -I tests/qinghua/check_coat.py [--dir out/qinghua/coat] [--variants coat thin] [--plot out.png]
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_coat as G  # noqa: E402
import qh  # noqa: E402
import optics  # noqa: E402  (gen_coat put materials/qinghua on the path)
from camera import LAM, Spectra, blackbody  # noqa: E402

S = Spectra("canon_eos_5d_mkiv")
W = S.sens * blackbody(5500.0)                     # (3, K): per channel weights of a spectrum's raw RGB


def world_xy():
    """(H, W, 2): where each pixel's centre ray meets z = 0 (the coat's surface)."""
    eye, d = qh.pixel_rays(G.EYE, G.TARGET, G.UP, G.FOV, G.RES)
    t = -eye[2] / d[..., 2]
    return eye[:2] + d[..., :2] * t[..., None]


def light_dirs(p, n=24):
    """Unit directions from tile point p (3,) to a grid on the light, and their irradiance weights."""
    c = np.asarray(G.LIGHT["center"], float)
    nl = -c / np.linalg.norm(c)
    ref = np.array([0.0, 0.0, 1.0])
    e1 = np.cross(ref, nl)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(nl, e1)
    s = (np.arange(n) + 0.5) / n - 0.5
    q = c + G.LIGHT["size"] * (s[:, None, None] * e1 + s[None, :, None] * e2)
    v = (q - p).reshape(-1, 3)
    r = np.linalg.norm(v, axis=1)
    w = v / r[:, None]
    wt = np.maximum(w[:, 2], 0) * np.maximum(-(w @ nl), 0) / r ** 2
    return w, wt


def analytic(tau, rho, at, n=G.ETA):
    """Ratio to the 0.5 plate, per channel: the stack under the area light, seen from straight above."""
    w, wt = light_dirs(np.array([at[0], at[1], 0.0]))
    L = np.zeros(LAM.shape)
    for mu, a in zip(w[:, 2], wt):
        L += a * optics.stack(tau, rho, n, mu_in=mu)[0]
    L /= wt.sum()
    return (W @ L) / (W @ np.full(LAM.shape, 0.5))


def family_interp(c_grid, R, c):
    """familymap's lookup: linear in c between the family's rows."""
    i = np.clip(np.searchsorted(c_grid, c) - 1, 0, len(c_grid) - 2)
    t = (c - c_grid[i]) / (c_grid[i + 1] - c_grid[i])
    return (1 - t) * R[i] + t * R[i + 1]


def regions(h):
    """name, (x0, x1), (y0, y1), tau(lambda), rho(lambda); h the coat's thickness (mm)."""
    k = optics.cobalt_kappa()
    white = np.full(LAM.shape, 0.8)
    out = [("A white", (-6, 6), (2.5, 5.5), 0 * k, white)]
    for x0, x1, c in G.BANDS:
        out.append((f"A band c={c}", (x0 + 2, x1 - 2), (10, 15), c * k, white))
    out.append((f"A step c={G.C_LINE}", (28, 31), (10, 15), G.C_LINE * k, white))
    sa = np.interp(LAM, G.LAM, G.lacquer_sigma_a())
    for cb in (0.2, 0.5, 0.8):
        xc = -40 + 80 * (0.1 + 0.8 * cb)
        rho = np.interp(LAM, G.LAM, family_interp(G.C_BASE, G.red_family(G.C_BASE), cb))
        out.append((f"B red c={cb}", (xc - 1, xc + 1), (-15, -5), sa * h, rho))
    return out


def mean_in(img, xy, xr, yr):
    m = (xy[..., 0] >= xr[0]) & (xy[..., 0] <= xr[1]) & (xy[..., 1] >= yr[0]) & (xy[..., 1] <= yr[1])
    v = img[m]
    return v.mean(0), v.std(0) / np.sqrt(len(v)), int(m.sum())


def profile(img, xy, yr=(9.0, 16.0), dx=0.02):
    """The image along x (world mm), averaged over the painted rows; bins of dx."""
    m = (xy[..., 1] >= yr[0]) & (xy[..., 1] <= yr[1])
    x = xy[..., 0][m]
    v = img[m]
    edges = np.arange(x.min(), x.max() + dx, dx)
    b = np.digitize(x, edges) - 1
    cnt = np.bincount(b, minlength=len(edges))
    prof = np.stack([np.bincount(b, v[:, i], minlength=len(edges)) for i in range(3)], 1)
    ok = cnt > 0
    return edges[ok] + dx / 2, prof[ok] / cnt[ok, None]


def lines_and_step(x, p, white):
    """Each line's darkest (5-bin median-smoothed) value over white, the step's plateau over white, and the step's
    10-90% width in mm, per channel."""
    rows = []
    sm = np.stack([np.convolve(p[:, i], np.ones(5) / 5, mode="same") for i in range(3)], 1)
    for xc, w in G.LINES:
        m = np.abs(x - xc) < max(w, 0.3)
        rows.append((f"line {w} mm", sm[m].min(0) / white))
    on = (x > G.STEP_X + 2) & (x < G.STEP_X + 5)
    plateau = p[on].mean(0)
    rows.append(("step plateau", plateau / white))
    side = (x > 21.5) & (x < G.STEP_X + 2.5)
    widths = []
    for i in range(3):
        lo, hi = plateau[i], white[i]
        f = (p[side, i] - lo) / (hi - lo)               # 1 white, 0 blue
        xs = x[side]
        x90 = xs[np.argmax(f < 0.9)]
        x10 = xs[np.argmax(f < 0.1)]
        widths.append(x10 - x90)
    return rows, np.array(widths)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(qh.OUT, "coat"))
    ap.add_argument("--variants", nargs="+", default=["coat"])
    ap.add_argument("--plot")
    a = ap.parse_args()
    xy = world_xy()
    imgs = {}                                       # (variant, renderer) -> (image, its reference plate)
    for r in ("pbrt", "cycles"):
        ref_path = f"{a.dir}/ref_{r}.exr"
        if not os.path.exists(ref_path):
            print(f"no {ref_path}")
            continue
        ref = qh.read_image(ref_path)[..., :3]
        for v in a.variants:
            p = f"{a.dir}/{v}_{r}.exr"
            if os.path.exists(p):
                imgs[(v, r)] = (qh.read_image(p)[..., :3], ref)
    print("ratio to the 0.5 plate (camera raw RGB), per region: analytic | pbrt (+- s.e.) | cycles; and the renders' "
          "ratios to analytic")
    for v in a.variants:
        h = G.VARIANTS[v]
        print(f"--- {v} (coat {h} mm)")
        for name, xr, yr, tau, rho in regions(h):
            ana = analytic(tau, rho, ((xr[0] + xr[1]) / 2, (yr[0] + yr[1]) / 2))
            line = f"{name:14s} ana {np.round(ana, 4)}"
            for r in ("pbrt", "cycles"):
                if (v, r) not in imgs:
                    continue
                img, ref = imgs[(v, r)]
                num, se, npx = mean_in(img, xy, xr, yr)
                den, _, _ = mean_in(ref, xy, xr, yr)
                val = num / den
                line += f" | {r} {np.round(val, 4)} (+-{np.round(se / den, 4).max():.4f}) x{np.round(val / ana, 3)}"
            print(line)
    print("\nlines and step (painted rows y 9-16): darkest / white, per channel; step 10-90% width (mm)")
    plots = []
    for v in a.variants:
        for r in ("pbrt", "cycles"):
            if (v, r) not in imgs:
                continue
            img, ref = imgs[(v, r)]
            x, pr = profile(img, xy)
            white, _, _ = mean_in(img, xy, (-6, 6), (2.5, 5.5))
            rows, widths = lines_and_step(x, pr, white)
            print(f"--- {v} {r}: step width {np.round(widths, 3)} mm")
            for name, val in rows:
                print(f"   {name:14s} {np.round(val, 3)}")
            plots.append((f"{v} {r}", x, pr / white))
    if a.plot and plots:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        for lab, x, pr in plots:
            m = (x > 1) & (x < 31)
            axs[0].plot(x[m], pr[m, 2], label=lab, lw=0.8)
            axs[1].plot(x[m], pr[m, 0], label=lab, lw=0.8)
        axs[0].set_ylabel("blue channel / white")
        axs[1].set_ylabel("red channel / white")
        axs[1].set_xlabel("x (mm): lines 0.2, 0.5, 1, 2 mm wide at 4, 9, 14, 20; step at 26")
        axs[0].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(a.plot, dpi=120)
        print("plot ->", a.plot)


if __name__ == "__main__":
    main()
