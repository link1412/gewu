"""Bias and noise of an estimator against a reference, from two seeds of each.

    python3 -I compare.py ref1.pfm ref2.pfm on1.pfm on2.pfm [block]
"""
import sys

import numpy as np


def read_pfm(path):
    with open(path, 'rb') as f:
        kind = f.readline().strip()
        w, h = map(int, f.readline().split())
        scale = float(f.readline())
        ch = 3 if kind == b'PF' else 1
        data = np.fromfile(f, '<f4' if scale < 0 else '>f4', w * h * ch)
    return data.reshape(h, w, ch)[::-1].astype(np.float64)


def lum(im):
    return im @ np.array([0.2126, 0.7152, 0.0722])


def blocks(a, b):
    h, w = a.shape[:2]
    a = a[:h - h % b, :w - w % b]
    return a.reshape(h // b, b, w // b, b, *a.shape[2:]).mean((1, 3))


def stats(name, x1, x2, b):
    """Per-block mean of the pair and its standard error from the pair's difference."""
    m = 0.5 * (x1 + x2)
    var_pix = 0.5 * (x1 - x2) ** 2 / 2          # variance of the pair mean, per pixel
    n = b * b
    return blocks(m, b), np.sqrt(blocks(var_pix, b) / n)


def main():
    r1, r2, e1, e2 = (lum(read_pfm(p)) for p in sys.argv[1:5])
    b = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    mr, sr = stats('ref', r1, r2, b)
    me, se = stats('est', e1, e2, b)
    z = (me - mr) / np.sqrt(sr ** 2 + se ** 2 + 1e-30)
    lit = mr > 0.02 * mr.max()
    print(f"image mean: est/ref = {e1.mean() / r1.mean() * 0.5 + e2.mean() / r2.mean() * 0.5:.4f}  "
          f"(ref seeds differ by {abs(r1.mean() / r2.mean() - 1):.4f}, est seeds by {abs(e1.mean() / e2.mean() - 1):.4f})")
    print(f"{b}x{b} blocks (lit {lit.sum()}): mean z {z[lit].mean():+.3f}, rms z {np.sqrt((z[lit] ** 2).mean()):.3f}, "
          f"|z|>3: {(np.abs(z[lit]) > 3).mean() * 100:.2f}% (pure noise: 0.27%)")
    rel = (me - mr) / np.maximum(mr, 1e-12)
    print(f"block rel. difference: median {np.median(rel[lit]) * 100:+.2f}%, 5-95% [{np.percentile(rel[lit], 5) * 100:+.2f}, "
          f"{np.percentile(rel[lit], 95) * 100:+.2f}]%")


    def noise(x1, x2):
        m = 0.5 * (x1 + x2)
        keep = m > 0.02 * m.max()
        return np.sqrt((0.5 * (x1 - x2) ** 2)[keep].mean()) / m[keep].mean()


    print(f"per-pixel relative noise: ref {noise(r1, r2) * 100:.1f}%  est {noise(e1, e2) * 100:.1f}%")
    # where the estimator disagrees most, by rows of blocks (cracks sit in the middle)
    worst = np.unravel_index(np.argmax(np.abs(z) * lit), z.shape)
    print(f"worst block {worst}: ref {mr[worst]:.4g} ± {sr[worst]:.2g}, est {me[worst]:.4g} ± {se[worst]:.2g}, z {z[worst]:+.2f}")


if __name__ == "__main__":
    main()
