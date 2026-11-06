"""The dark felt the washer stands on, as textures for scene.py --felt [A: all numbers; the CMA photo's cloth by eye:
a fine-grained dark grey felt, its mean reflectance as scene.py's ground (0.02, so the lit front reads about as the
photo's 0.023)]. Felt's fibres (20-30 um) are under a pixel; what shows is their clumps, 0.15-0.6 mm, and a slower
unevenness, 3-15 mm. Both are band-limited noise made periodic over the tile (FFT), so the tile repeats seamlessly:
- felt_c.pfm: the reflectance c (a grey family R(lambda; c) = c, felt.npz), mean RHO;
- felt_h.pfm: a bump height in mm (the nap), its own noise at the clumps' scale.

    python3 -I objects/ru_washer/felt.py --out out/ru/final/felt [--tile 25] [--n 2048] [--seed 1]
"""
import argparse
import json
import os

import numpy as np

RHO, GRAIN, MOTTLE, NAP_MM = 0.02, 0.35, 0.0, 0.03   # MOTTLE 0: within a tile it repeats, a pattern far off


def band(n, px_mm, lo_mm, hi_mm, rng):
    """Periodic noise with its power between wavelengths lo_mm and hi_mm, unit std."""
    f = np.fft.fftfreq(n, d=px_mm)
    k = np.hypot(*np.meshgrid(f, f))
    m = (k >= 1.0 / hi_mm) & (k <= 1.0 / lo_mm)
    x = np.real(np.fft.ifft2(np.fft.fft2(rng.normal(size=(n, n))) * m))
    return x / x.std()


def write_pfm(path, a):
    a = np.asarray(a, np.float32)
    with open(path, "wb") as f:
        f.write(f"PF\n{a.shape[1]} {a.shape[0]}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(np.flipud(np.repeat(a[..., None], 3, 2))).astype("<f4").tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tile", type=float, default=25.0)
    ap.add_argument("--n", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    px = a.tile / a.n
    grain = band(a.n, px, 0.15, 0.6, rng)
    mottle = band(a.n, px, 3.0, min(15.0, a.tile), rng)
    c = RHO * np.clip(1 + GRAIN * np.tanh(grain / 1.5) + MOTTLE * mottle, 0.2, 2.5)
    h = NAP_MM * np.tanh(band(a.n, px, 0.12, 0.5, rng) / 1.5)
    write_pfm(os.path.join(a.out, "felt_c.pfm"), c)
    write_pfm(os.path.join(a.out, "felt_h.pfm"), h)
    cs = np.linspace(0.0, 0.08, 81)
    np.savez(os.path.join(a.out, "felt.npz"), lambda_nm=np.array([360.0, 830.0]), c=cs, R=np.repeat(cs[:, None], 2, 1))
    json.dump({"tile_mm": a.tile, "n": a.n, "rho": RHO, "grain": GRAIN, "mottle": MOTTLE, "nap_mm": NAP_MM,
               "c_mean": float(c.mean()), "c_p5_p95": np.percentile(c, [5, 95]).round(4).tolist(), "tag": "A"},
              open(os.path.join(a.out, "felt.json"), "w"), indent=1)
    print(f"felt: c mean {c.mean():.4f}, p5-p95 {np.percentile(c, [5, 95]).round(4)}, nap rms {h.std():.4f} mm")


if __name__ == "__main__":
    main()
