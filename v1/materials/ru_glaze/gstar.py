"""Which one-lobe medium the renderers get for the Ru glaze (material.json render), measured with the slab Monte
Carlo (tools/slab.py): the glaze's scatterers have g of about 0.95 (anorthite) and 0.9 (bubbles); a renderer's
medium takes one Henyey-Greenstein g, and its paths stop after a fixed number of vertices (pbrt's maxdepth, Cycles'
bounces: 64 in our scenes). Similarity (sigma_s (1 - g) kept, g*) trades the two: a lower g* means fewer
scatterings per path, so less is cut by the limit, but it is further from the real lobes.

For each g*, thickness and geometry, against the exact mixture of the kinds' lobes with no limit:
    sim     similarity alone, no limit
    cut     similarity with the path limit
at one wavelength, the fitted volume fractions, the sherd's body and surface.

    python3 -I materials/ru_glaze/gstar.py --fit out/ru/fit/R2_SCI.json --out out/ru/fit/gstar.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import fit as F  # noqa: E402
import glaze  # noqa: E402
import slab  # noqa: E402

GEOMETRIES = {"instrument_8deg": math.cos(math.radians(8.0)), "strip_45deg": math.cos(math.radians(45.0))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", required=True)
    ap.add_argument("--lam", type=float, default=540.0)
    ap.add_argument("--g", default="0.8,0.6,0.4,0.2,0.0")
    ap.add_argument("--d", default="0.1,0.3,0.5,1.0")
    ap.add_argument("--limit", type=int, default=64)
    ap.add_argument("--nphot", type=int, default=60000)
    ap.add_argument("--out")
    a = ap.parse_args()
    f = json.load(open(a.fit))
    mat = glaze.load()
    s = f["sample"]
    lam = np.array([a.lam])
    comps = F.scatterers(lam, s, f["phi_an"], f["phi_d"], f["phi_b"], mat)
    sa = float(glaze.sigma_a(lam, s, mat)[0])
    nD = glaze.appen_nD(mat["samples"][s]["composition_wt"]["value"])[0]
    n = float(glaze.n_cauchy(lam, nD, mat["glass"]["abbe_number"]["value"])[0])
    ss = float(sum(c[1][0] for c in comps))
    lobes = tuple((float(c[1][0]) / ss, float(c[2][0])) for c in comps)
    reduced = float(sum(c[1][0] * (1 - c[2][0]) for c in comps))
    print(f"{s} at {a.lam:g} nm: sigma_s {ss:.2f}/mm, lobes {lobes}, sigma_s' {reduced:.3f}/mm, sigma_a {sa:.4f}/mm")
    rows = []
    for geo, mu in GEOMETRIES.items():
        for d in (float(v) for v in a.d.split(",")):
            ref = slab.run(n, [(d, ss, sa, lobes)], f["rho_body"], mu, nphot=a.nphot, seed=11, alpha=f["alpha"])
            line = f"{geo:16s} d {d:.1f} mm: exact {ref['R_diffuse']:.4f} +- {ref['R_diffuse_se']:.4f} |"
            for g in (float(v) for v in a.g.split(",")):
                sim = slab.run(n, [(d, reduced / (1 - g), sa, g)], f["rho_body"], mu, nphot=a.nphot, seed=12,
                               alpha=f["alpha"])
                cut = slab.run(n, [(d, reduced / (1 - g), sa, g)], f["rho_body"], mu, nphot=a.nphot, seed=12,
                               alpha=f["alpha"], max_vertices=a.limit)
                rows.append({"geometry": geo, "d_mm": d, "g_star": g, "exact": ref["R_diffuse"],
                             "exact_se": ref["R_diffuse_se"], "sim": sim["R_diffuse"], "sim_se": sim["R_diffuse_se"],
                             "cut": cut["R_diffuse"], "cut_se": cut["R_diffuse_se"], "limit": a.limit})
                line += f" g* {g:.1f}: {sim['R_diffuse'] / ref['R_diffuse']:.3f} {cut['R_diffuse'] / ref['R_diffuse']:.3f} |"
            print(line, flush=True)
    if a.out:
        with open(a.out, "w") as fh:
            json.dump({"fit": os.path.relpath(a.fit, ROOT), "lam_nm": a.lam, "sigma_s": ss, "lobes": lobes,
                       "sigma_s_reduced": reduced, "sigma_a": sa, "n": n, "rows": rows}, fh, indent=1)


if __name__ == "__main__":
    main()
