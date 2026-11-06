"""Test b (numbers only, no render): how well per-channel eta, k (tools/rgbscene.py conductor_channels) carry a
conductor's spectral Fresnel, at one bounce (the fit's error, by angle) and at several bounces between two
surfaces of the metal (F^n averaged over the channel against the fit's F^n), against the naive mapping (eta and k
each averaged over the channel like a reflectance).

    python3 -I tests/metals/check_fit.py [--extra NAME=eta.spd,k.spd ...]
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import rgbscene as R  # noqa: E402
from camera import LAM, pbrt_array  # noqa: E402

DEG = (0, 30, 45, 60, 70, 80, 85, 89)


def named(m):
    e, k = pbrt_array(f"{m}_eta"), pbrt_array(f"{m}_k")
    return np.interp(LAM, e[0::2], e[1::2]), np.interp(LAM, k[0::2], k[1::2])


def report(name, eta, k, sen):
    fit = R.conductor_channels(eta, k, sen, name)
    c = np.cos(np.radians(DEG))
    spec = R.fresnel_conductor(c[:, None, None], eta[None, None], k[None, None])[:, 0]       # (deg, lam)
    W = sen.w / sen.w.sum(1, keepdims=True)
    tgt = spec @ W.T
    Ff = np.stack([R.fresnel_conductor(c, fit["eta"][i], fit["k"][i]) for i in range(3)], 1)
    nv = sen.average(eta), sen.average(k)
    Fn = np.stack([R.fresnel_conductor(c, nv[0][i], nv[1][i]) for i in range(3)], 1)
    print(f"\n{name}: eta {np.round(fit['eta'], 3)} k {np.round(fit['k'], 3)}  (naive eta {nv[0].round(3)} k {nv[1].round(3)})")
    print("  deg  spectral F (RGB)        fit - spectral             naive - spectral")
    for i, d in enumerate(DEG):
        print(f"  {d:3d}  {tgt[i].round(4)}  {(Ff[i] - tgt[i]).round(4)}  {(Fn[i] - tgt[i]).round(4)}")
    print(f"  max |fit - spectral| over 0-89.5 deg: {fit['fresnel_fit']['max_abs_error']}")
    for nb in (2, 3, 5):
        t = (spec[0] ** nb) @ W.T
        print(f"  {nb} bounces at normal incidence: spectral {t.round(4)}, fit {(Ff[0] ** nb).round(4)}, "
              f"relative error {((Ff[0] ** nb) / t - 1).round(4)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", nargs="*", default=[], help="NAME=eta.spd,k.spd (pbrt spectrum files)")
    a = ap.parse_args()
    sen = R.Sensor("canon_eos_5d_mkiv", 5500.0)
    for m in ("Au", "Ag", "Cu", "CuZn", "Al"):
        report(m, *named(m), sen)
    for e in a.extra:
        name, files = e.split("=")
        fe, fk = files.split(",")
        eta, _ = R.conductor_spectrum({"eta": ("spectrum", [os.path.abspath(fe)])}, "eta", "", name)
        k, _ = R.conductor_spectrum({"k": ("spectrum", [os.path.abspath(fk)])}, "k", "", name)
        report(name, eta, k, sen)


if __name__ == "__main__":
    main()
