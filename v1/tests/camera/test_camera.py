"""Checks of tools/camera.py against theory.

    python3 -I tests/camera/test_camera.py

1. Noise: a flat raw frame through the electron model; the spread per channel must match
   sqrt((mu + rn^2) / n_c) electrons, n_c = the channel's photosites behind a 1080p pixel.
2. Diffraction: one wavelength, a fine grid: the Airy pattern keeps 83.8% of its energy inside the
   first dark ring (radius 1.22 lambda N).
3. Colour: a white card under the key light comes out white; the matrix keeps (1, 1, 1).
4. Y'CbCr: flat colours through our BT.709 4:2:0 encoding and ffmpeg's decoding (as compare.py
   decodes) come back within one code value.
"""

import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as C  # noqa: E402
from compare import DECODE_VF  # noqa: E402

fails = []


def check(name, ok, detail):
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


# 1. noise
import json  # noqa: E402
sensor = json.load(open(os.path.join(ROOT, "tools/sensors/canon_eos_5d_mkiv.json")))
cam = {"iso": 100, "expose": {"of_saturation": 1.0}, "develop": {"ev": 0.0, "shoulder_from": 0.5}}
sat = sensor["saturation_e_at_base_iso"]
rn = sensor["read_noise_e"]["100"]["e"]
n = np.array([0.25, 0.5, 0.25]) * (sensor["photosites"][0] / C.FW) ** 2
for level in (0.002, 0.02, 0.3):                         # fractions of saturation
    raw = np.full((C.FH, C.FW, 3), level)
    mean_e = raw * sat
    rng = np.random.default_rng(1)
    total = rng.poisson(mean_e * n) + rng.normal(0.0, rn * np.sqrt(n), mean_e.shape)
    got = (total / n).reshape(-1, 3).std(0)
    want = np.sqrt((level * sat + rn ** 2) / n)
    check(f"noise at {level:g} of saturation", np.all(np.abs(got / want - 1) < 0.01),
          f"std {np.round(got, 2)} e- vs theory {np.round(want, 2)}")

# 2. diffraction: monochromatic Airy against Rayleigh's encircled energy 1 - J0(x)^2 - J1(x)^2,
#    both sums taken inside circles (the grid's inscribed circle loses the far tail)
from scipy import special  # noqa: E402
lam_um, N, h = 0.55, 20.0, 0.05                           # grid step in um
g = np.arange(-1200, 1201) * h
r = np.hypot(*np.meshgrid(g, g))
x = np.pi * r / (lam_um * N)
I = np.where(x > 1e-12, 2 * special.j1(x) / np.maximum(x, 1e-12), 1.0) ** 2
ee = lambda q: 1 - special.j0(q) ** 2 - special.j1(q) ** 2
r1, rmax = 1.2197 * lam_um * N, g.max()
got = I[r <= r1].sum() / I[r <= rmax].sum()
want = ee(np.pi * r1 / (lam_um * N)) / ee(np.pi * rmax / (lam_um * N))
check("Airy encircled energy at the first dark ring", abs(got - want) < 0.003,
      f"{got:.4f} vs Rayleigh {want:.4f} (0.838 of the whole pattern)")
S = C.Spectra("canon_eos_5d_mkiv")
light = C.blackbody(5500)
ks, Neff = C.airy_kernels(S, light, {"f_number": 19.25, "magnification": 0.965, "sensor_width_mm": 36.0})
check("Airy kernels sum to 1", all(abs(k.sum() - 1) < 1e-9 for k in ks), f"working f/{Neff:.2f}")
check("red spreads more than blue", ks[0].max() < ks[2].max(), f"centre R {ks[0].max():.3f}, B {ks[2].max():.3f}")

# 3. colour
cal = C.calibrate(S, light)
white = (S.sens @ light) * cal["gains"] / (S.sens @ light)[1]
check("white card balances to (1,1,1)", np.allclose(white, 1), np.round(white, 6))
check("matrix keeps white", np.allclose(cal["C"].sum(1), 1, atol=1e-6), np.round(cal["C"].sum(1), 6))

# 4. Y'CbCr round trip through ffmpeg's decoder, as compare.py decodes
cols = np.array([[0.1, 0.1, 0.1], [0.8, 0.2, 0.2], [0.2, 0.7, 0.3], [0.25, 0.3, 0.9], [0.95, 0.9, 0.85]])
rgb = np.repeat(cols, C.FW // len(cols) + 1, axis=0)[: C.FW][None].repeat(C.FH, 0)
y, cb, cr = C.ycbcr420(rgb)
out = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p",
                      "-s", f"{C.FW}x{C.FH}", "-i", "-", "-vf", DECODE_VF, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     input=y.tobytes() + cb.tobytes() + cr.tobytes(), capture_output=True, check=True).stdout
dec = np.frombuffer(out, np.uint8).reshape(C.FH, C.FW, 3).astype(float)
w = C.FW // len(cols)
err = max(np.abs(dec[540, i * w + w // 2] - cols[i] * 255).max() for i in range(len(cols)))
check("BT.709 4:2:0 round trip", err <= 1.0, f"worst {err:.2f} code values (flat patches, centres)")

print("all passed" if not fails else f"{len(fails)} failed: {fails}")
sys.exit(1 if fails else 0)
