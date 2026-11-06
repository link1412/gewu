"""What is missing from the Ru glaze's hue (docs/materials/ru_glaze.md): with the scattering fitted to L* (fit.py),
the model is bluer and greener than the sherds. Two candidates, each one parameter, told apart by the two sherds:
    tail   the Fe3+ absorption has a tail into the blue that Volotinen's Gaussians lack (the charge-transfer edge of
           real glasses): eps_tail(lambda) = A exp(-(lambda - 400 nm) / w), per mol/L of Fe3+, w = 40 nm [A];
           A is fitted to R2's b*, and R1's b* (more Fe3+) is then a prediction
    body   the body is warm: rho(lambda) = rho0 (1 + t tanh((lambda - 560 nm) / 40 nm)) [A: the shape], t fitted
One white Monte Carlo per sherd and wavelength, at the fitted anorthite fraction; absorption and body are applied to
its recorded escapes, so the candidates cost no new runs.

    python3 -I materials/ru_glaze/hue.py --fit-r2 out/ru/fit/R2_SCI.json --fit-r1 out/ru/fit/R1_SCI.json
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
from camera import LAM  # noqa: E402

W_TAIL = 40.0


def white_runs(fitres, mat, nphot, seed=1):
    """The recorded white runs of a fit's medium, one per wavelength of the fit."""
    s = fitres["sample"]
    lam = np.array(fitres["lam"])
    smp = mat["samples"][s]
    nD = glaze.appen_nD(smp["composition_wt"]["value"])[0]
    n = glaze.n_cauchy(lam, nD, mat["glass"]["abbe_number"]["value"])
    d = smp["thickness_um"]["value"] * 1e-3
    out = []
    for i in range(len(lam)):
        r = slab.run(float(n[i]), [(d, float(fitres["sigma_s_star"][i]), 0.0, fitres["g_star"])], 1.0,
                     F.MU_INSTRUMENT, nphot=nphot, seed=seed + i, alpha=fitres["alpha"], record=True)
        out.append((r["events"], r["R_specular"]))
    return lam, out


def lab_with(lam, runs, nphot, sa, rho, mode):
    Rd = np.array([slab.events_apply(ev, nphot, [sa[i]], rho[i])[0] for i, (ev, _) in enumerate(runs)])
    Rs = np.array([rs for _, rs in runs])
    return F.lab_of(lam, Rd, Rs, mode)


def tail_sigma(lam, A, sample, mat):
    """The tail's absorption, 1/mm: ln 10 eps_tail c(Fe3+) / 10."""
    c3 = glaze.iron_mol_per_l(sample, mat)[1]
    return math.log(10) * A * np.exp(-(lam - 400.0) / W_TAIL) * c3 / 10.0


def solve(f, lo, hi, target, it=40):
    """Bisection for f(x) = target, f increasing."""
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < target else (lo, mid)
    return 0.5 * (lo + hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit-r2", required=True)
    ap.add_argument("--fit-r1", required=True)
    ap.add_argument("--nphot", type=int, default=60000)
    ap.add_argument("--out")
    a = ap.parse_args()
    mat = glaze.load()
    fits = {k: json.load(open(p)) for k, p in (("R2", a.fit_r2), ("R1", a.fit_r1))}
    mode = fits["R2"]["mode"]
    runs = {k: white_runs(f, mat, a.nphot) for k, f in fits.items()}
    res = {"mode": mode}
    base = {}
    for k, f in fits.items():
        lam, rr = runs[k]
        sa = glaze.sigma_a(lam, f["sample"], mat)
        base[k] = lab_with(lam, rr, a.nphot, sa, np.full(len(lam), f["rho_body"]), mode)
    res["base"] = {k: v.tolist() for k, v in base.items()}
    # tail: A from R2's b*, then R1 predicted
    lam2, rr2 = runs["R2"]
    s2 = fits["R2"]["sample"]
    sa2 = glaze.sigma_a(lam2, s2, mat)
    rho2 = np.full(len(lam2), fits["R2"]["rho_body"])
    tb = mat["samples"][s2]["lab"]["value"][2]
    A = solve(lambda A: lab_with(lam2, rr2, a.nphot, sa2 + tail_sigma(lam2, A, s2, mat), rho2, mode)[2], 0.0, 200.0, tb)
    tail = {}
    for k, f in fits.items():
        lam, rr = runs[k]
        sa = glaze.sigma_a(lam, f["sample"], mat) + tail_sigma(lam, A, f["sample"], mat)
        tail[k] = lab_with(lam, rr, a.nphot, sa, np.full(len(lam), f["rho_body"]), mode)
    res["tail"] = {"A_L_per_mol_cm_at_400nm": A, "w_nm": W_TAIL, **{k: v.tolist() for k, v in tail.items()}}
    # body: t from R2's b*, then the same body under R1
    def body_rho(lam, f, t):
        return f["rho_body"] * (1 + t * np.tanh((lam - 560.0) / 40.0))
    t = solve(lambda t: lab_with(lam2, rr2, a.nphot, sa2, body_rho(lam2, fits["R2"], t), mode)[2], 0.0, 0.95, tb)
    body = {}
    for k, f in fits.items():
        lam, rr = runs[k]
        body[k] = lab_with(lam, rr, a.nphot, glaze.sigma_a(lam, f["sample"], mat), body_rho(lam, f, t), mode)
    res["body"] = {"t": t, **{k: v.tolist() for k, v in body.items()}}
    for k in fits:
        m = mat["samples"][fits[k]["sample"]]["lab"]["value"]
        print(f"{k} {mode}: measured {m[0]:6.2f} {m[1]:6.2f} {m[2]:6.2f} | base " + " ".join(f"{v:6.2f}" for v in base[k])
              + " | tail " + " ".join(f"{v:6.2f}" for v in tail[k]) + " | body " + " ".join(f"{v:6.2f}" for v in body[k]))
    print(f"tail A = {A:.3f} L/mol/cm at 400 nm (w {W_TAIL} nm); body t = {t:.3f}")
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
