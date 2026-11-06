"""The washer's glaze file (scene.py --glaze) from the Ru glaze material: the R2 fit (materials/ru_glaze/fit.py,
out/ru/fit/R2_SCI_mix.json) gives the scatterers' sigma_s at the render's g* and the body's warmth; the iron's
sigma_a and Appen's n come from material.json's sample. The ground cloth is not part of the material: [A].

    python3 -I objects/ru_washer/glaze_ru.py [--fit out/ru/fit/R2_SCI_mix.json] [--out objects/ru_washer/glaze_ru.json]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "materials/ru_glaze"))
import fit as F  # noqa: E402
import glaze  # noqa: E402


def table(lam, v):
    return [float(x) for pair in zip(lam, v) for x in pair]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", default=os.path.join(ROOT, "out/ru/fit/R2_SCI_mix.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "glaze_ru.json"))
    ap.add_argument("--ground", type=float, default=0.06)
    ap.add_argument("--blue-tail", type=float, default=0.0,
                    help="this piece's extra blue absorption A exp(-(lam - 400) / 50), 1/mm at 400 nm [F]")
    ap.add_argument("--fe2", type=float, help="this piece's Fe2+ fraction in place of the sample's [F]")
    a = ap.parse_args()
    fit = json.load(open(a.fit))
    mat = glaze.load()
    lam = np.array(fit["lam"], float)
    if a.fe2 is not None:
        mat["samples"][fit["sample"]]["fe2_fraction"] = {"value": a.fe2, "tag": "F", "why": "fitted to the photo's glaze"}
    if abs(fit["g_star"] - mat["render"]["g_star"]["value"]) > 1e-9:
        raise SystemExit("glaze_ru: the fit's g* is not the material's render g*")
    nD = glaze.appen_nD(mat["samples"][fit["sample"]]["composition_wt"]["value"])[0]
    out = {
        "about": f"Ru glaze for the washer, from {os.path.relpath(a.fit, ROOT)} (objects/ru_washer/glaze_ru.py)",
        "eta": {"value": round(float(nD), 5), "tag": "I", "why": "Appen's n_D of the sample's composition"},
        "roughness": {"value": fit["alpha"], "tag": "A", "why": "the fit's surface alpha"},
        "sigma_a_per_mm": {"lambda_nm_value": table(lam, glaze.sigma_a(lam, fit["sample"], mat)
                                                    + a.blue_tail * np.exp(-(lam - 400.0) / 50.0)), "tag": "I",
                           "why": "the sample's Fe2+ and Fe3+ (material.json iron)",
                           "fe2_fraction": mat["samples"][fit["sample"]]["fe2_fraction"],
                           "blue_tail_per_mm_at_400nm": {"value": a.blue_tail, "tag": "F", "why":
                               "this washer's glaze is yellower than Shi's R2 (the photo's glaze median b* +7, R2's 0): "
                               "an extra blue absorber, its cause not modelled (Fe3+ or Fe-Ti charge transfer [I]), "
                               "its strength fitted to the photo"}},
        "sigma_s_per_mm": {"lambda_nm_value": table(lam, fit["sigma_s_star"]), "tag": "F",
                           "why": f"anorthite phi {fit['phi_an']:.4f} fitted to R2's L*, one lobe at g* (similarity)"},
        "g": {"value": fit["g_star"], "tag": "D", "why": "material.json render.g_star"},
        "max_depth": mat["render"]["max_depth"]["value"],
        "body_reflectance": {"lambda_nm_value": table(lam, F.body_rho(lam, fit["rho_body"], fit["body_t"])),
                             "tag": "F", "why": f"rho0 {fit['rho_body']} [A], warmth t {fit['body_t']:.4f} fitted to R2's b*"},
        "ground_reflectance": {"lambda_nm_value": [360, a.ground, 830, a.ground], "tag": "A",
                               "why": "the photo's dark felt, grey; set so its ratio to the glaze is about the photo's"},
    }
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}: n {nD:.4f}, sigma_s* {np.mean(fit['sigma_s_star']):.2f}/mm, g* {fit['g_star']}")


if __name__ == "__main__":
    main()
