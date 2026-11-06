"""Fit the Ru glaze's unknown volume fractions to a sherd's measured CIELAB with the slab Monte Carlo
(tools/slab.py), everything else from material.json (docs/materials/ru_glaze.md).

The glaze is one layer of the sample's thickness over a Lambertian body, under the instrument's geometry (d/8:
by reciprocity, light from 8 deg and all of the reflection collected; SCI keeps the surface reflection, SCE drops
it). Its absorption is the iron's (glaze.sigma_a); its scattering is the sum of the kinds of scatterer, each from
Mie theory (tools/mie.py) at its measured size and index contrast and an unknown volume fraction:
    anorthite crystals    the "white" scattering: needles, as spheres of their width (material.json)
    Ca-rich droplets      the nanometre phase separation, with the Percus-Yevick structure factor
    bubbles               an assumed volume fraction (none measured)
For a renderer the layer has one Henyey-Greenstein g* (pbrt's media take one, not per wavelength, and the
anorthite's g of about 0.95 needs more scatterings than renderers follow): each kind's sigma_s (1 - g) is kept
(similarity, material.json render.g_star); the Monte Carlo can also run the exact mixture of the kinds' lobes.

The body is grey, or warm: rho(lambda) = rho0 (1 + t tanh((lambda - 560 nm) / 40 nm)) [A: the shape], t fitted
to the sherd's b* or given (hue.py: of the two one-parameter fixes for the model's too-blue hue, only the warm body
also gets R2's a*, and it is what the Palace Museum's "thin glaze shows the body pink" asks for).

    python3 -I materials/ru_glaze/fit.py lab --sample shi2020_R2 --phi-an 0.02 --phi-d 0.1
    python3 -I materials/ru_glaze/fit.py fit --sample shi2020_R2 --mode SCI [--mixture] [--fit-t | --t 0.2]
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
import glaze  # noqa: E402
import slab  # noqa: E402
from camera import LAM  # noqa: E402

LAM_FIT = np.arange(380.0, 781.0, 40.0)      # the Monte Carlo's wavelengths; the spectrum is interpolated between
MU_INSTRUMENT = math.cos(math.radians(8.0))


def scatterers(lam, sample, phi_an, phi_d, phi_b, mat=None, dn_d=None):
    """[(name, sigma_s[lam] 1/mm, g[lam])] for the three kinds of scatterer, in the glass of the sample."""
    import mie
    mat = mat or glaze.load()
    s = mat["samples"][sample]
    nD = glaze.appen_nD(s["composition_wt"]["value"])[0]
    abbe = mat["glass"]["abbe_number"]["value"]
    n_host = glaze.n_cauchy(lam, nD, abbe)
    out = []
    if phi_an > 0:
        an = mat["anorthite"]["n_principal"]
        n_an = (np.array(an["n_alpha"]) + np.array(an["n_beta"]) + np.array(an["n_gamma"])) / 3
        # outside the measured 435.8-643.8 nm: the nearest measured value (no extrapolation of the fit)
        order = np.argsort(an["lambda_nm"])
        n_p = np.interp(lam, np.array(an["lambda_nm"])[order], n_an[order])
        w = mat["anorthite"]["scattering_width_nm"]
        t = np.linspace(-4.0, 4.0, 40)                  # a log-normal by volume, as number weights (volume / d^3)
        sizes = w["volume_median"] * np.exp(math.log(w["sigma_g"]) * t)
        weights = np.exp(-0.5 * t * t) / sizes ** 3
        r = mie.medium(lam, n_host, n_p, None, phi_an, structure=False, sizes=sizes, weights=weights / weights.sum())
        out.append(("anorthite", np.asarray(r["sigma_s"]), np.asarray(r["g"])))
    if phi_d > 0:
        ph = mat["phases"]
        n_si = glaze.appen_nD(ph["si_rich_wt"]["value"])[0]
        n_ca = glaze.appen_nD(ph["ca_rich_wt"]["value"])[0]
        dn = (n_ca - n_si) if dn_d is None else dn_d
        r = mie.medium(lam, n_host, n_host + dn, s["droplet_d_nm"]["value"], phi_d, structure=True)
        out.append(("droplets", np.asarray(r["sigma_s"]), np.asarray(r["g"])))
    if phi_b > 0:
        r = mie.medium(lam, n_host, np.ones_like(n_host), mat["bubbles"]["d_um"]["value"] * 1e3, phi_b,
                       structure=False)
        out.append(("bubbles", np.asarray(r["sigma_s"]), np.asarray(r["g"])))
    return out


def similar(comps, g_star):
    """One medium for the renderers: each kind's sigma_s (1 - g) kept, all with g* (material.json render.g_star:
    the error is under 1%, measured); returns sigma_s*[lam]."""
    return sum(c[1] * (1 - c[2]) for c in comps) / (1 - g_star)


def body_rho(lam, rho0, t):
    """The body's albedo: grey rho0 for t = 0, warm (redder) for t > 0."""
    return rho0 * (1 + t * np.tanh((np.asarray(lam, float) - 560.0) / 40.0))


def white(sample, comps, alpha, nphot=60000, seed=1, mixture=False, mat=None, lam=LAM_FIT, thickness_mm=None):
    """Per wavelength one white Monte Carlo (sigma_a 0, body 1, recorded) for light from the instrument's 8 deg:
    [(events, R_specular)]; apply() puts in the iron's absorption and the body afterwards."""
    mat = mat or glaze.load()
    s = mat["samples"][sample]
    d = thickness_mm or s["thickness_um"]["value"] * 1e-3
    nD = glaze.appen_nD(s["composition_wt"]["value"])[0]
    n = glaze.n_cauchy(lam, nD, mat["glass"]["abbe_number"]["value"])
    g_star = mat["render"]["g_star"]["value"]
    ss_star = similar(comps, g_star)
    out = []
    for i in range(len(lam)):
        if mixture:                                     # the exact mixture of the kinds' lobes
            ss = float(sum(c[1][i] for c in comps))
            g = tuple((float(c[1][i]) / ss, float(c[2][i])) for c in comps)
        else:
            ss, g = float(ss_star[i]), g_star
        r = slab.run(float(n[i]), [(d, ss, 0.0, g)], 1.0, MU_INSTRUMENT, nphot=nphot, seed=seed + i, alpha=alpha,
                     record=True)
        out.append((r["events"], r["R_specular"]))
    return out


def apply(runs, nphot, sigma_a, rho):
    """(diffuse, specular) reflectance from white runs, the iron's sigma_a[lam] and the body's rho[lam]."""
    Rd = np.array([slab.events_apply(ev, nphot, [sigma_a[i]], rho[i])[0] for i, (ev, _) in enumerate(runs)])
    return Rd, np.array([rs for _, rs in runs])


def spectrum(sample, comps, rho_body, alpha, nphot=60000, seed=1, mixture=False, mat=None, lam=LAM_FIT,
             thickness_mm=None):
    """The reflectance on LAM_FIT: (diffuse, specular) for light from the instrument's 8 deg."""
    mat = mat or glaze.load()
    runs = white(sample, comps, alpha, nphot, seed, mixture, mat, lam, thickness_mm)
    rho = np.broadcast_to(np.asarray(rho_body, float), lam.shape)
    return apply(runs, nphot, glaze.sigma_a(lam, sample, mat), rho)


def lab_of(lam, Rd, Rs, mode):
    R = np.interp(LAM, lam, Rd + (Rs if mode == "SCI" else 0.0))
    return glaze.lab(R)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["lab", "fit"])
    ap.add_argument("--sample", default="shi2020_R2")
    ap.add_argument("--phi-an", type=float, default=0.02)
    ap.add_argument("--phi-d", type=float, default=0.0)
    ap.add_argument("--phi-b", type=float, help="bubbles' volume fraction (default: material.json's)")
    ap.add_argument("--rho", type=float, default=0.3, help="body albedo, rho0 [A]")
    ap.add_argument("--t", type=float, default=0.0, help="the body's warmth t (body_rho)")
    ap.add_argument("--fit-t", action="store_true", help="fit t to the sherd's b* (at every step of phi_an)")
    ap.add_argument("--alpha", type=float, default=0.05, help="surface GGX alpha [A]")
    ap.add_argument("--mode", choices=["SCI", "SCE"], default="SCI")
    ap.add_argument("--mixture", action="store_true")
    ap.add_argument("--nphot", type=int, default=60000)
    ap.add_argument("--bracket", default="1e-4,0.2", help="phi_an's bracket for the bisection (geometric)")
    ap.add_argument("--iters", type=int, default=14)
    ap.add_argument("--out")
    a = ap.parse_args()
    mat = glaze.load()
    if a.phi_b is None:
        a.phi_b = mat["bubbles"]["volume_fraction"]["value"]
    target = mat["samples"][a.sample]["lab"]["value"]
    if a.cmd == "lab":
        comps = scatterers(LAM_FIT, a.sample, a.phi_an, a.phi_d, a.phi_b, mat)
        for name, ss, g in comps:
            print(f"{name:10s} sigma_s", " ".join(f"{v:.3f}" for v in ss), " g", " ".join(f"{v:.3f}" for v in g))
        Rd, Rs = spectrum(a.sample, comps, body_rho(LAM_FIT, a.rho, a.t), a.alpha, a.nphot, mixture=a.mixture,
                          mat=mat)
        L = lab_of(LAM_FIT, Rd, Rs, a.mode)
        print(f"{a.mode} L*a*b* {L[0]:.2f} {L[1]:.2f} {L[2]:.2f}; measured {target}")
        return
    # fit: phi_an to L* (bisection, common seeds); with --fit-t, at every step the body's t to b* (on the same runs)
    sa = glaze.sigma_a(LAM_FIT, a.sample, mat)

    def lab_at(phi_an, phi_d):
        comps = scatterers(LAM_FIT, a.sample, phi_an, phi_d, a.phi_b, mat)
        runs = white(a.sample, comps, a.alpha, a.nphot, mixture=a.mixture, mat=mat)
        t = a.t
        if a.fit_t:
            lo_t, hi_t = -0.5, 0.95
            for _ in range(30):
                mid = 0.5 * (lo_t + hi_t)
                b = lab_of(LAM_FIT, *apply(runs, a.nphot, sa, body_rho(LAM_FIT, a.rho, mid)), a.mode)[2]
                lo_t, hi_t = (mid, hi_t) if b < target[2] else (lo_t, mid)
            t = 0.5 * (lo_t + hi_t)
        Rd, Rs = apply(runs, a.nphot, sa, body_rho(LAM_FIT, a.rho, t))
        return lab_of(LAM_FIT, Rd, Rs, a.mode), comps, Rd, Rs, t
    lo, hi = (float(v) for v in a.bracket.split(","))
    for _ in range(a.iters):
        mid = math.sqrt(lo * hi)
        L = lab_at(mid, a.phi_d)[0]
        lo, hi = (mid, hi) if L[0] < target[0] else (lo, mid)
    phi_an = math.sqrt(lo * hi)
    L, comps, Rd, Rs, t = lab_at(phi_an, a.phi_d)
    res = {"sample": a.sample, "mode": a.mode, "rho_body": a.rho, "body_t": t, "alpha": a.alpha, "phi_b": a.phi_b,
           "phi_d": a.phi_d, "phi_an": phi_an, "mixture": a.mixture, "g_star": mat["render"]["g_star"]["value"],
           "sigma_s_star": similar(comps, mat["render"]["g_star"]["value"]).tolist(), "lab": L.tolist(), "measured": target,
           "lam": LAM_FIT.tolist(), "R_diffuse": Rd.tolist(), "R_specular": Rs.tolist(),
           "sigma_s": {c[0]: c[1].tolist() for c in comps}, "g": {c[0]: c[2].tolist() for c in comps}}
    print(json.dumps({k: v for k, v in res.items() if k not in ("R_diffuse", "R_specular", "sigma_s", "g", "lam")}))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
