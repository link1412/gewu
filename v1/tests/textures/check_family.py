"""Test c, the check: along each tile's ramp the family render divided by the uniform-0.5 render (the same
illumination, per pixel) must equal the table interpolated at c(u), over 0.5.

    python3 -I tests/textures/check_family.py

Two expected tables: (1) the one rgbscene wrote into the JSON (tests the Cycles side: map, lookup, clamp),
(2) one recomputed here from the spectra (channel average weighted by sensor x 5500 K blackbody; tests the
projection). The family and the reference render share a seed, so the illumination's noise cancels in the ratio (the
agreement is then the lookup's, not the noise's); the second seed shows what the noise would be. c(u) is read back from the stored ramp file (EXR half floats round it), bilinear, clamped.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import gen_family as G  # noqa: E402
from camera import LAM, Spectra, blackbody  # noqa: E402

D = os.path.join(C.OUT, "family")
ROWS = slice(200, 340)                 # tile rows well inside (y within about +-4 mm)


def pixel_u(t):
    eye, d = C.pixel_rays(G.EYE, G.TARGET, G.UP, G.FOV, G.RES, rows=ROWS)
    x = eye[0] + (-eye[2] / d[..., 2]) * d[..., 0]
    return x[0], (x[0] - t["x0"]) / (t["x1"] - t["x0"])


def ramp_c(t, u):
    p = os.path.join(D, t["file"])
    c = (C.read_image(p) if p.endswith(".exr") else C.read_pfm(p))[0, :, 0]
    return np.interp(u * len(c) - 0.5, np.arange(len(c)), c)          # bilinear at texel centres, clamped


def table_from_spectra(name):
    F = np.load(os.path.join(D, f"family_{name.lower()}.npz"))
    S = Spectra("canon_eos_5d_mkiv")
    w = S.sens * blackbody(5500.0)
    R = np.array([np.interp(LAM, F["lambda_nm"], r, left=0, right=0) for r in F["R"]])
    return F["c"], (R @ w.T) / w.sum(1)


def main():
    sc = json.load(open(os.path.join(D, "scene_fam.cycles.json")))
    mats = [o["material"] for o in sc["objects"] if "reflectance_family" in o["material"]]
    fam1, fam2, ref = (C.read_image(os.path.join(D, f"{n}.exr"))[ROWS].mean(0) for n in ("fam1", "fam2", "ref1"))
    ok = True
    for (k, t), m in zip(G.TILES.items(), mats):
        x, u = pixel_u(t)
        inside = (u > 0.02) & (u < 0.98)
        c = ramp_c(t, u)
        tab = np.array(m["reflectance_family"]["table"])
        cj = np.array(m["reflectance_family"]["c"])
        exp_json = np.stack([np.interp(np.clip(c, cj[0], cj[-1]), cj, tab[:, ch]) for ch in range(3)], 1)
        cs, tabs = table_from_spectra(k)
        exp_own = np.stack([np.interp(np.clip(c, cs[0], cs[-1]), cs, tabs[:, ch]) for ch in range(3)], 1)
        got, got2 = 0.5 * fam1 / ref, 0.5 * fam2 / ref       # same seed as the reference: its noise cancels; seed 2: it does not
        cols = np.where(inside)[0]
        cols = cols[(x[cols] > t["x0"]) & (x[cols] < t["x1"])]
        under, over = (c[cols] < cj[0]).sum(), (c[cols] > cj[-1]).sum()
        print(f"tile {k}: {len(cols)} columns, c from {c[cols].min():.2f} to {c[cols].max():.2f} "
              f"({under} below and {over} above the family's ends: clamped)")
        for name, exp in (("JSON table", exp_json), ("spectra recomputed", exp_own)):
            err = got[cols] - exp[cols]
            rel = err / exp[cols]
            print(f"  vs {name}: abs err rms {np.sqrt((err ** 2).mean(axis=0)).round(5)} (R,G,B), max {np.abs(err).max():.5f}; "
                  f"relative rms {np.sqrt((rel ** 2).mean()):.4f}, max {np.abs(rel).max():.4f}")
            ok &= np.abs(rel).max() < 0.002
        e2 = got2[cols] - exp_json[cols]
        print(f"  seed 2 (noise not cancelled): rms {np.sqrt((e2 ** 2).mean(axis=0)).round(5)}, bias {e2.mean(axis=0).round(5)} (R,G,B)")
        spread = exp_json[cols].max(0) - exp_json[cols].min(0)
        print(f"  signal range along the ramp (R,G,B): {spread.round(3)}")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(14, 4))
    for a_, (k, t) in zip(ax, G.TILES.items()):
        x, u = pixel_u(t)
        c = ramp_c(t, u)
        m = mats[list(G.TILES).index(k)]
        cj, tab = np.array(m["reflectance_family"]["c"]), np.array(m["reflectance_family"]["table"])
        sel = (u > 0.02) & (u < 0.98)
        for ch, col in enumerate("rgb"):
            a_.plot(c[sel], 0.5 * fam1[sel, ch] / ref[sel, ch], col, lw=0.8)
            a_.plot(cj, tab[:, ch], col + "o", ms=3)
        a_.set_title(f"tile {k}: render / reference (lines), table rows (dots)")
        a_.set_xlabel("c")
    fig.savefig(os.path.join(D, "ramps.png"), dpi=80)
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
