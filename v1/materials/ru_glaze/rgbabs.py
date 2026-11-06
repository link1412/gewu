"""What Cycles' RGB medium does to the Ru strip's colour (card.py), in the slab Monte Carlo: spectral transport (the
fit's 11 wavelengths, one n, as pbrt is given) against RGB transport (three channels with rgbscene.py's channel
averages of sigma_a, sigma_s and rho, as Cycles is given), and RGB with sigma_a taken at a reference path length L:
sigma_a,c = -ln <exp(-sigma_a L)>_c / L, L the mean path in the glaze of the light that leaves towards the box.
Camera looking down, the card's soft box, through the camera chain; prints L*a*b* and the raw channels over the
bare body's (TODO.md, the RGB absorption item).

    python3 -I materials/ru_glaze/rgbabs.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
os.chdir(ROOT)
import numpy as np  # noqa: E402
import slab, glaze, card, rgbscene  # noqa: E402
import fit as F  # noqa: E402
from camera import LAM, lab, rgb709_from_xyz, calibrate, blackbody  # noqa: E402
c = json.load(open("out/ru/strip/R2_SCI_g06/card.json")); f = json.load(open("out/ru/fit/R2_SCI.json"))
mat = glaze.load(); lam = np.array(f["lam"])
ss = sum(np.array(f["sigma_s"][k]) * (1 - np.array(f["g"][k])) for k in f["sigma_s"]) / (1 - c["g_star"])
sa = glaze.sigma_a(lam, f["sample"], mat)
rho = F.body_rho(lam, c["body_rho0"], c["body_t"])
nD = glaze.appen_nD(mat["samples"][f["sample"]]["composition_wt"]["value"])[0]
sen = rgbscene.Sensor("canon_eos_5d_mkiv", 5500)
cal = calibrate(sen.S, blackbody(5500))
white = sen.S.cmf @ sen.S.d65 / (sen.S.cmf[1] @ sen.S.d65)
on = lambda v: np.interp(LAM, lam, v)
saL, ssL, rhoL = on(sa), on(ss), on(rho)
sa_lin, ss_c, rho_c = sen.average(saL), sen.average(ssL), sen.average(rhoL)
omega = card.projected_solid_angle(card.BOX) / math.pi
NP = 200000
def lab_raw(raw, raw_body):
    lin = (raw * cal["gains"]) @ cal["C"].T
    lb = (raw_body * cal["gains"]) @ cal["C"].T
    Y = np.array([0.2126, 0.7152, 0.0722])
    yb = (sen.S.cmf[1] * sen.S.d65) @ rhoL / (sen.S.cmf[1] @ sen.S.d65)
    return lab(lin * yb / (lb @ Y) @ np.linalg.inv(rgb709_from_xyz(white)).T, white)
light = blackbody(5500)
raw_body = sen.S.sens @ (light * rhoL)
for d in (0.3, 1.0):
    # spectral: one white run per wavelength of the fit, the soft box's tally
    R = np.zeros(len(lam))
    for i in range(len(lam)):
        r = slab.run(nD, [(d, float(ss[i]), 0.0, c["g_star"])], 1.0, 1.0,          # one n, as both renderers
                     nphot=NP, seed=31, lights=[("box", card.BOX)], alpha=f["alpha"], record=True, max_vertices=c["max_depth"])
        R[i] = (slab.events_apply(r["events"], NP, [sa[i]], rho[i], light_scale={"box": 1.0})[1][0] + r["lights_specular"]["box"]) / omega
    spec = lab_raw(sen.S.sens @ (light * on(R)), raw_body)
    # RGB: one white run per channel (its sigma_s), then the channel's sigma_a and rho; and the mean path
    out = {}
    runs = []
    for ch in range(3):
        r = slab.run(nD, [(d, float(ss_c[ch]), 0.0, c["g_star"])], 1.0, 1.0, nphot=NP, seed=31, lights=[("box", card.BOX)],
                     alpha=f["alpha"], record=True, max_vertices=c["max_depth"])
        runs.append(r)
    ev = runs[1]["events"]
    tow = ev["light"] == 0
    Lmean = float((ev["w"][tow] * ev["L"][tow, 0]).sum() / ev["w"][tow].sum())
    for name, Lref in (("linear", None), (f"L {Lmean:.2f} mm", Lmean)):
        if Lref is None:
            sac = sa_lin
        else:
            sac = -np.log((sen.w @ np.exp(-saL * Lref)) / sen.w.sum(1)) / Lref
        Rc = np.array([(slab.events_apply(runs[ch]["events"], NP, [sac[ch]], rho_c[ch], light_scale={"box": 1.0})[1][0]
                        + runs[ch]["lights_specular"]["box"]) / omega for ch in range(3)])
        # the RGB render's raw is the channel value times the white's raw (Cycles' RGB is relative to the key light)
        if Lref is None:
            Rc_lin = Rc
        out[name] = lab_raw(Rc * (sen.S.sens @ light), raw_body * 0 + rho_c * (sen.S.sens @ light))
    print(f"d {d}: spectral {spec.round(2)} | " + " | ".join(f"RGB {k} {v.round(2)}" for k, v in out.items()), flush=True)
    rs = sen.S.sens @ (light * on(R)) / raw_body * 0.3
    rr = Rc_lin * (sen.S.sens @ light) / (rho_c * (sen.S.sens @ light)) * 0.3
    print(f"   raw over body x 0.3: spectral {rs.round(4)}  RGB linear {rr.round(4)}", flush=True)
