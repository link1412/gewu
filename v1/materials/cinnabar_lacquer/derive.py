"""Derive the body reflectances of the lacquers (materials/cinnabar_lacquer/material.json, "derived") from the measured
paint spectra of Reichert et al. 2025 (HSI mean spectra, VNIR, 400-1000 nm at 5 nm; doi 10.6084/m9.figshare.28639103).

    python3 -I materials/cinnabar_lacquer/derive.py ref/carved_lacquer/reichert2025/x [--write]

The CSVs are downloaded data: pass their directory; nothing is run from it.

What is derived, and how (docs/materials/cinnabar_lacquer.md):
- The HSI readings carry a flat part that is not the pigment's: a gum-arabic paint of grape-seed black on the same paper
  reads 0.158-0.166 from 400 to 780 nm (15A), where a black body is expected near 0.0x. We take that reading as the
  flat part common to all paints of that binder on that substrate (surface scatter of a matte paint plus the instrument's
  offset) [A], and remove it: R = (R_paint - R_black) / (1 - R_black).
- What is left is the paint's body reflectance without a smooth interface (a lean matte paint, pigment at the surface).
  In lacquer the same pigment sits under a smooth film of n 1.52; the renderer puts that interface on top (a dielectric
  over the body), which gives the lacquer's deeper, more saturated colour by itself (Saunderson). So R is used as the
  body reflectance as it is [I].
- Sampled 400-780 nm at 10 nm (the sensor x 5500 K weight outside 400-780 nm is under 0.03%, tools/camera.py).
"""
import argparse
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAM = np.arange(400, 781, 10)
FILES = {"cinnabar": "06A-HSI_VNIR-Cinnabar-GA-Paper.csv",
         "black_ref": "15A-HSI_VNIR-Grape Seed Black-GA-Paper.csv",
         "cinnabar_egg": "38A-HSI_VNIR-Cinnabar-EG-Paper.csv"}


def load(d, name):
    a = np.loadtxt(os.path.join(d, FILES[name]), delimiter=",")
    if a.ndim != 2 or a.shape[1] != 2 or a[0, 0] > 400 or a[-1, 0] < 780:
        raise SystemExit(f"{FILES[name]}: expected two columns covering 400-780 nm")
    return np.interp(LAM, a[:, 0], a[:, 1])


def derive(d):
    black = load(d, "black_ref")
    out = {}
    for name in ("cinnabar",):
        R = np.clip((load(d, name) - black) / (1 - black), 0.0, 1.0)
        out[name] = [v for pair in zip(LAM.tolist(), np.round(R, 4).tolist()) for v in pair]
    out["black_ref_mean"] = round(float(black.mean()), 4)
    out["black_ref_range"] = [round(float(black.min()), 4), round(float(black.max()), 4)]
    eg = load(d, "cinnabar_egg")
    out["cinnabar_egg_raw_550_650"] = [round(float(np.interp(550, LAM, eg)), 4), round(float(np.interp(650, LAM, eg)), 4)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_dir")
    ap.add_argument("--write", action="store_true", help="put the result into material.json's 'derived'")
    a = ap.parse_args()
    out = derive(a.csv_dir)
    print(json.dumps(out))
    if a.write:
        p = os.path.join(HERE, "material.json")
        m = json.load(open(p))
        m["derived"] = {"what": "made by derive.py from the Reichert 2025 CSVs (ref/, not in git); see 'body'", **out}
        json.dump(m, open(p, "w"), indent=1, ensure_ascii=False)
        print("written", p)


if __name__ == "__main__":
    main()
