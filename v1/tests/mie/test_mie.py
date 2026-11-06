"""Checks of tools/mie.py (docs/mie.md).

    python3 -I tests/mie/test_mie.py

1. Everything in tools/mie.py's check(): Bohren & Huffman's sample run, Wiscombe's MIEV0 cases, the Rayleigh,
   Rayleigh-Gans-Debye and anomalous-diffraction limits, Q_ext -> 2, energy, the amplitudes against the series, the
   Percus-Yevick limits and closed form, the population's own consistency.
2. Speed: a 471-wavelength x 50-size table (360..830 nm, log-normal sizes) for the droplets and the anorthite
   crystals, both with S(q), must take seconds, not minutes (here: under 60 s on an Apple laptop CPU).
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mie  # noqa: E402

fails = 0
for name, v, ref, tol, kind in mie.check():
    ok = mie.passed(v, ref, tol, kind)
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {v:.7g} (ref {ref:.7g}, tol {tol:.1e} {kind})")

lam = np.arange(360.0, 831.0, 1.0)
for name, nh, npart, d, sg, phi in [("droplets", 1.52, 1.54, 60.0, 1.4, 0.2), ("anorthite", 1.52, 1.58, 4400.0, 1.3, 0.1)]:
    sizes, w = mie.lognormal(d, sg, 50)
    t = time.time()
    r = mie.medium(lam, nh, npart, None, phi, sizes=sizes, weights=w)
    dt = time.time() - t
    ok = dt < 60 and np.all(np.isfinite(r["sigma_s"])) and np.all(np.isfinite(r["g"]))
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} speed: {name}, {len(lam)} x {len(sizes)} with S(q): {dt:.1f} s")

print("all passed" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
