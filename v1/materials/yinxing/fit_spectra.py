"""Fit PROSPECT-D to measured leaf spectra (Morimoto et al. 2022, Zenodo 5217752, CC BY 4.0; ref/yinxing/research2/data/morimoto/).

    python3 -I materials/yinxing/fit_spectra.py [--out JSON]

The data: a spectroradiometer (Topcon SR-2A, 1 degree field), 380-780 nm in 5 nm steps. Reflectance: an X-Rite
SpectraLight QC booth at D65, diffuse from above, the receiver at 45 degrees elevation, over a white standard's
reading (a directional reflectance factor, not PROSPECT's hemispherical R) [I, the paper sec. 2.1]. Transmittance:
the leaf flat on a FUJICOLOR LED Viewer ST-A4, a black mask round it, over the bare viewer's reading [I].
What the backing under the leaf was in the reflectance booth is not stated (black or white changes R by about R T)
[A: black, so R is the leaf's own].

Three samples (selected_spectra_derived.csv):
- ginkgo_yellow_20141210: a yellow ginkgo leaf (by its thumbnail), R only. The only calibrated measurement of a
  yellow ginkgo leaf we have; fitting R gives N, Cab, Car, Cbrown, and the model predicts T.
- ginkgo_green_20140821, dioscorea_yellow_20141105: R and T of the same leaf. Fitting R alone and predicting T tests
  that step (R -> T through PROSPECT) on a ginkgo leaf (green) and on a yellow leaf (another species).
Fit: least squares on 400-780 nm (PROSPECT starts at 400), R_meas = R_PROSPECT + s with a flat surface term s >= 0
(without it the green ginkgo's R fit runs N to its bound and predicts T five times low; with it T's green channel
comes within 5 %); Cw 0.012 cm, Cm 0.009 g/cm2 held (material.json,
little effect in the visible), Anth 0; several starts, the best kept. The predicted and measured T are compared as
spectra and as the colour of light through them: a 3000 K blackbody, the 5D Mk IV's channels (the card's camera),
relative to the light itself.
"""
import argparse
import csv
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import prospect as P  # noqa: E402

DATA = os.path.join(ROOT, "ref/yinxing/research2/data/morimoto/selected_spectra_derived.csv")
FREE = ("N", "Cab", "Car", "Cbrown", "s")
LO = [1.0, 0.0, 0.0, 0.0, 0.0]
HI = [3.5, 80.0, 30.0, 3.0, 0.2]


def load():
    rows = list(csv.DictReader(open(DATA)))
    out = {}
    for r in rows:
        s = out.setdefault(r["sample_id"], {"lam": [], "R": [], "T": [], "Tb": []})
        s["lam"].append(float(r["wavelength_nm"]))
        s["R"].append(float(r["R_directional"]))
        s["T"].append(float(r["T_FrontSideUp"]) if r["T_FrontSideUp"] else np.nan)
        s["Tb"].append(float(r["T_BackSideUp"]) if r["T_BackSideUp"] else np.nan)
    return {k: {q: np.array(v) for q, v in s.items()} for k, s in out.items()}


def model(x, lam, fixed):
    """R (with the flat surface term s added: the cuticle's specular share at the booth's 45 degrees, wavelength-
    independent [A]) and T (PROSPECT's, no s)."""
    p = dict(fixed)
    p.update(dict(zip(FREE, x)))
    sfc = p.pop("s")
    _, R, T = P.leaf(p, lam)
    return R + sfc, T


def fit_R(lam, R, fixed, fix=None):
    fix = fix or {}
    free = [k for k in FREE if k not in fix]
    best = None
    for s in ([1.5, 1, 5, 0, 0.01], [2.0, 5, 8, 0.1, 0.03], [1.2, 0.2, 3, 0.5, 0.0], [2.5, 40, 10, 0, 0.03],
              [1.5, 30, 8, 0.2, 0.02]):
        x0 = [v for k, v in zip(FREE, s) if k in free]
        lo = [v for k, v in zip(FREE, LO) if k in free]
        hi = [v for k, v in zip(FREE, HI) if k in free]

        def res(x):
            full = dict(fix)
            full.update(dict(zip(free, x)))
            return model([full[k] for k in FREE], lam, fixed)[0] - R
        r = least_squares(res, x0, bounds=(lo, hi))
        if best is None or r.cost < best.cost:
            best = r
    full = dict(fix)
    full.update(dict(zip(free, best.x)))
    return {k: float(full[k]) for k in FREE}, float(np.sqrt(np.mean(best.fun ** 2)))


def channels(spec_lam, x):
    from camera import LAM, Spectra, blackbody
    S = Spectra("canon_eos_5d_mkiv")
    w = S.sens * blackbody(3000.0)
    xi = np.interp(LAM, spec_lam, np.nan_to_num(x), left=np.nan, right=np.nan)
    ok = np.isfinite(xi)
    return (w[:, ok] @ xi[ok]) / w[:, ok].sum(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    D = load()
    fixed = {"Anth": 0.0, "Cw": 0.012, "Cm": 0.009}
    rep = {}
    for sid, s in D.items():
        k = (s["lam"] >= 400) & (s["lam"] <= 780)
        lam = s["lam"][k]
        p, rms = fit_R(lam, s["R"][k], fixed)
        Rm, Tm = model([p[q] for q in FREE], lam, fixed)
        e = {"fit": {q: round(v, 4) for q, v in p.items()}, "R_rms": round(rms, 4),
             "R_meas_ch_3000K": np.round(channels(lam, s["R"][k]), 4).tolist(),
             "R_model_ch_3000K": np.round(channels(lam, Rm), 4).tolist(),
             "T_pred_ch_3000K": np.round(channels(lam, Tm), 4).tolist()}
        if np.isfinite(s["T"][k]).all():
            for name, T in (("front", s["T"][k]), ("back", s["Tb"][k])):
                tm, tp = channels(lam, T), channels(lam, Tm)
                e[f"T_meas_{name}_ch_3000K"] = np.round(tm, 4).tolist()
                e[f"T_pred_over_meas_{name}"] = np.round(tp / tm, 3).tolist()
                e[f"T_spec_rms_{name}"] = round(float(np.sqrt(np.mean((Tm - T) ** 2))), 4)
        # Cab held at the literature's ends for yellow ginkgo (docs: 2.4-7.3)
        if sid == "ginkgo_yellow_20141210":
            for cab in (2.4, 7.3):
                pp, rr = fit_R(lam, s["R"][k], fixed, {"Cab": cab})
                e[f"fit_Cab_{cab}"] = {"fit": {q: round(v, 4) for q, v in pp.items()}, "R_rms": round(rr, 4)}
        rep[sid] = e
    s = json.dumps(rep, indent=1)
    print(s)
    if a.out:
        open(a.out, "w").write(s)


if __name__ == "__main__":
    main()
