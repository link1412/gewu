"""青花's optics: the spectra of its parts and a 1-D model of the stack, glaze over a cobalt film over the body.

The stack (docs/materials/qinghua.md), from the top:
- glaze: a clear glass of index n, smooth here (the renderers add its roughness), weakly absorbing or not;
- the cobalt film at the glaze-body boundary: pure absorption, optical depth tau(lambda) = c kappa(lambda) at normal
  incidence, crossed at the angle inside the glaze; c is the cobalt's column density, g CoO per m^2;
- the body: a Lambertian reflector of albedo rho(lambda) (its translucency, the lateral spread inside it, is not
  modelled: docs/materials/qinghua.md "not done").
The 1-D model is exact for that planar stack (all orders of internal reflection, including total internal reflection
at the glaze surface, which sends ~60% of the body's light back to it); the renderers do the same in true geometry
(tools/coat.py), which adds what a 1-D model cannot: the glaze's thickness lets the recycled light walk sideways.

    python3 -I materials/qinghua/optics.py          # prints the stack's reflectance for a few c
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import LAM  # noqa: E402  pbrt's 1 nm grid, 360-830 nm

M_COO = 74.9326          # g/mol, NIST WebBook [I]
LN10 = np.log(10.0)


def material():
    return json.load(open(os.path.join(HERE, "material.json")))


def spectrum(v):
    """A material.json spectrum {"lambda_nm_value": [l0, v0, l1, v1, ...]} or a number, on LAM; held flat beyond its ends."""
    if isinstance(v, (int, float)):
        return np.full(LAM.shape, float(v))
    a = np.asarray(v["lambda_nm_value"], float).reshape(-1, 2)
    return np.interp(LAM, a[:, 0], a[:, 1])


# --- cobalt -------------------------------------------------------------------------------------
def thiemsorn_curve():
    d = np.loadtxt(os.path.join(HERE, "data/thiemsorn2007_fig7_co5.csv"), delimiter=",", skiprows=2)
    return d[:, 0], d[:, 1]


def cobalt_kappa(baseline=0.03, hold_below=400.0, conc_mol_l=0.016):
    """Optical depth at normal incidence per g CoO / m^2 (natural log), on LAM.
    From Thiemsorn 2007 Fig. 7 (glass Co5): A/d [M] minus the base glass's flat floor `baseline` (its value at
    750-900 nm, where Co2+ does not absorb [D]); below `hold_below` the rise is the glass's UV edge, so the cobalt's
    value at hold_below is held [A]. Per mol/L, then per column: tau = ln10 * eps * N, eps = (A/d)/C in L/(mol cm)
    = 0.1 (A/d)/C m^2/mol, N = m / M_CoO mol/m^2."""
    lam, A = thiemsorn_curve()
    a = np.maximum(np.interp(LAM, lam, A) - baseline, 0.0)
    a = np.where(LAM < hold_below, np.interp(hold_below, lam, A) - baseline, a)
    eps_m2 = 0.1 * a / conc_mol_l
    return LN10 * eps_m2 / M_COO


def companion_kappa(r, s):
    """What travels with the cobalt in an ore pigment and absorbs broadly (Mn, Fe: the Kangxi blue's MnO/CoO 5-7,
    Fe2O3/CoO 0.4-1 [M, Chen, Guo & Zhang 1978]), per g CoO / m^2 like cobalt_kappa: r (1 + s (lambda - 550)/100),
    clipped at 0. Its shape is not measured: a line in lambda, r and s fitted on the material card [F]."""
    return r * np.maximum(0.0, 1.0 + s * (LAM - 550.0) / 100.0)


FE2_PEAK_NM = 1100.0     # Fe2+ in soda-lime-silica glass: its band peaks at 1100 nm [M, Ceglia et al. 2015 JAAS 30:1552]
FE2_SIGMA_CM = 2100.0    # its width, a Gaussian in wavenumber (FWHM ~4900 /cm) [A]: no visible-range table found
FE3_EDGE_NM = 40.0       # Fe3+'s violet absorption (bands at 380, 420, 435 nm on a UV edge [M, Mehdikhani & Borhani
                         # 2013 PAC 7:117 Fig. 2]) as one exponential edge from 400 nm with this scale [A]


def fe2_shape():
    """Fe2+-like absorption, 1 at its peak (1100 nm): in the visible, only its short-wave tail (5% of the peak at 700 nm)."""
    nu = 1e7 / LAM
    return np.exp(-0.5 * ((nu - 1e7 / FE2_PEAK_NM) / FE2_SIGMA_CM) ** 2)


def fe3_shape():
    """Fe3+-like absorption, 1 at 400 nm, falling over FE3_EDGE_NM toward the red."""
    return np.exp(-(LAM - 400.0) / FE3_EDGE_NM)


def iron_like_kappa(fe3, fe2):
    """A companion of the cobalt shaped like iron's two absorptions (violet: Fe3+; red: Fe2+'s tail), per g CoO / m^2:
    fe3 at 400 nm, fe2 at 1100 nm. Shapes from the sources [M, A above]; amplitudes fitted on the card [F]. The fitted
    amplitudes are far above what the iron of a Kangxi pigment could give dissolved (docs/materials/qinghua.md):
    the companion stands for whatever makes the photo's blue less violet, not for a measured iron."""
    return fe3 * fe3_shape() + fe2 * fe2_shape()


def pigment_kappa(pigment):
    """kappa of a material.json set's pigment: the cobalt, plus the companion if the set has one."""
    k = cobalt_kappa()
    comp = pigment.get("companion")
    if comp and comp.get("model") == "iron_like":
        k = k + iron_like_kappa(comp["fe3"]["value"], comp["fe2"]["value"])
    elif comp:
        k = k + companion_kappa(comp["r"]["value"], comp["s"]["value"])
    return k


def body_albedo(body):
    """The body's albedo spectrum on LAM: its value, times its tint (1 + t x + q x^2, x = (lambda - 550)/100) if the
    set has one [F]."""
    rho = np.full(LAM.shape, float(body["albedo"]["value"]))
    tint = body.get("tint")
    if tint:
        x = (LAM - 550.0) / 100.0
        rho = rho * (1 + tint["t"]["value"] * x + tint["q"]["value"] * x * x)
    return np.clip(rho, 0.0, 0.999)


def thiemsorn_mn3_kappa():
    """Mn3+ in the same glass series (Thiemsorn 2007, Fig. 4), if digitized; else None."""
    p = os.path.join(HERE, "data/thiemsorn2007_fig4_mn5.csv")
    if not os.path.exists(p):
        return None
    d = np.loadtxt(p, delimiter=",", skiprows=2)
    return d


# --- Fresnel ------------------------------------------------------------------------------------
def fresnel_inside(mu, n):
    """Reflectance at the glaze-air boundary for light inside the glaze at cos mu (unpolarised); 1 beyond the
    critical angle."""
    mu = np.asarray(mu, float)
    s2 = n * n * (1 - mu * mu)
    ct = np.sqrt(np.maximum(0.0, 1 - s2))
    rs = (n * mu - ct) / (n * mu + ct + 1e-30)
    rp = (mu - n * ct) / (mu + n * ct + 1e-30)
    return np.where(s2 >= 1, 1.0, 0.5 * (rs ** 2 + rp ** 2))


def refracted_mu(mu_out, n):
    """cos of the angle inside the glaze for light at cos mu_out outside."""
    return np.sqrt(1 - (1 - np.asarray(mu_out, float) ** 2) / n ** 2)


# --- the stack ------------------------------------------------------------------------------------
_MU = np.linspace(1e-5, 1.0, 4001)


def stack(tau, rho, n, mu_in=None, mu_view=1.0):
    """The diffuse part of the stack's reflection, per wavelength.
    tau: (K,) optical depth at normal incidence of everything between body and air (film + glaze absorption);
    rho: (K,) body albedo; n: glaze index;
    mu_in: cos of the incident direction OUTSIDE (collimated), or None for uniform diffuse light from the hemisphere;
    mu_view: cos of the viewing direction outside.
    Returns (radiance factor pi*L/E: the reflectance a white Lambertian standard would read 1 for, excluding the
    specular reflection off the glaze surface; hemispherical albedo of the diffuse part)."""
    tau = np.asarray(tau, float)[:, None]
    mu = _MU[None, :]
    Ri = fresnel_inside(_MU, n)[None, :]
    a = np.exp(-tau / mu)
    K = 2 * np.trapezoid(a * a * Ri * mu, _MU, axis=1)          # body exitance that comes back to the body
    E = 2 * np.trapezoid(a * (1 - Ri) * mu, _MU, axis=1)        # body exitance that leaves the glaze
    if mu_in is None:
        Tin = n * n * E                                          # diffuse in: reciprocity (1 - r_ext = n^2 E at tau 0)
    else:
        mt = refracted_mu(mu_in, n)
        Tin = (1 - fresnel_inside(mt, n)) * np.exp(-tau[:, 0] / mt)
    J = rho * Tin / (1 - rho * K)                                # body radiosity per unit incident irradiance
    mv = refracted_mu(mu_view, n)
    L = J * np.exp(-tau[:, 0] / mv) * (1 - fresnel_inside(mv, n)) / n ** 2      # pi * radiance outside
    return L, J * E


def film_family(kappa, c_grid):
    """The film's transmittance at normal incidence, T0(lambda; c) = exp(-c kappa), as a familymap family."""
    return np.exp(-np.outer(c_grid, kappa))


if __name__ == "__main__":
    from camera import Spectra, blackbody
    m = material()
    S = Spectra("canon_eos_5d_mkiv")
    w = S.sens * blackbody(5500.0)
    proj = lambda x: (w @ x) / w.sum(1)
    k = cobalt_kappa()
    print(f"kappa(595 nm) = {k[LAM == 595][0]:.3f} per g CoO/m^2")
    for name in ("modern", "kangxi"):
        g = m["sets"][name]
        n, rho, kp = g["glaze"]["eta"]["value"], body_albedo(g["body"]), pigment_kappa(g["pigment"])
        for c in (0, 0.5, 1, 2, 4):
            L, alb = stack(c * kp, rho, n)
            print(f"{name} c {c:4}: camera RGB under 5500 K, diffuse light, normal view: {np.round(proj(L), 4)}")
