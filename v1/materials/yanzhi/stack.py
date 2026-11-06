"""A 1-D model of the 胭脂红 stack, exact for parallel layers (docs/materials/yanzhi.md), from the top:

- the enamel: a lead glass of index n_e, its gold absorbing with optical depth tau(lambda) = c kappa(lambda) at
  normal incidence (c, g Au/m^2; enamel.kappa), crossed at the angle inside the enamel; no scattering (the gold's
  single-scattering albedo is below 2% for spheres up to 20 nm: enamel.py);
- the clear glaze, index n_g, not absorbing;
- the body: a Lambertian reflector of albedo rho(lambda), radiating into the glaze.

All orders of reflection between the body, the glaze-enamel boundary (Fresnel at n_e/n_g) and the enamel-air
boundary (Fresnel at n_e, total internal reflection beyond the critical angle) are summed incoherently (the layers
are tens of um thick, far beyond the light's coherence for a broadband source), Fresnel unpolarised per boundary [A:
the two polarisations are averaged at each boundary instead of carried through]. With n_e = n_g it is the qinghua
stack (materials/qinghua/optics.py), which check() compares against.

    stack(tau, rho, n_e, n_g, mu_in=None, mu_view=1.0)   pi L / E of the diffuse part, its albedo, the specular R
    python3 -I materials/yanzhi/stack.py check
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

_MU = np.linspace(1e-5, 1.0, 4001)       # cosines in the glaze


def fresnel(mu1, n1, n2):
    """Unpolarised reflectance going from index n1 to n2 at cos mu1 (in n1); 1 beyond the critical angle."""
    mu1 = np.asarray(mu1, float)
    s2 = (n1 / n2) ** 2 * (1 - mu1 * mu1)
    ct = np.sqrt(np.maximum(0.0, 1 - s2))
    rs = (n1 * mu1 - n2 * ct) / (n1 * mu1 + n2 * ct + 1e-30)
    rp = (n2 * mu1 - n1 * ct) / (n2 * mu1 + n1 * ct + 1e-30)
    return np.where(s2 >= 1, 1.0, 0.5 * (rs ** 2 + rp ** 2))


def _up(mu_g, tau, n_e, n_g):
    """For light in the glaze going up at cos mu_g: (T to the air, R back into the glaze), per wavelength (rows) and
    angle (columns)."""
    mu_g = np.asarray(mu_g, float)
    s2g = 1 - mu_g * mu_g
    s2e = (n_g / n_e) ** 2 * s2g
    mu_e = np.sqrt(np.maximum(1e-12, 1 - s2e))
    RA = fresnel(mu_g, n_g, n_e)                          # glaze -> enamel (same from the other side, reciprocity)
    RB = fresnel(mu_e, n_e, 1.0)                          # enamel -> air, 1 under total internal reflection
    a = np.exp(-np.asarray(tau, float)[:, None] / mu_e[None, :])
    den = 1 - RA * RB * a * a
    T = (1 - RA) * a * (1 - RB) / den
    R = RA + (1 - RA) ** 2 * a * a * RB / den
    return T, R


def stack(tau, rho, n_e, n_g, mu_in=None, mu_view=1.0):
    """tau: (K,) the enamel's optical depth at normal incidence; rho: (K,) the body's albedo; n_e, n_g: the enamel's
    and the glaze's index (scalars); mu_in: cos of a collimated light outside, or None for uniform diffuse light;
    mu_view: cos of the view outside. Returns (pi L / E of the diffuse part, its hemispherical albedo, the specular
    reflectance at mu_in or at mu_view for diffuse light) per wavelength."""
    tau = np.atleast_1d(np.asarray(tau, float))
    rho = np.broadcast_to(np.asarray(rho, float), tau.shape)
    T, R = _up(_MU, tau, n_e, n_g)
    K = 2 * np.trapezoid(R * _MU, _MU, axis=1)
    E = 2 * np.trapezoid(T * _MU, _MU, axis=1)

    def glaze_mu(mu_out):                                 # cos in the glaze of a direction at cos mu_out in air
        return np.sqrt(1 - (1 - mu_out * mu_out) / n_g ** 2)
    if mu_in is None:
        Tin = n_g * n_g * E
        mu_s = mu_view
    else:
        Tin = _up(np.array([glaze_mu(mu_in)]), tau, n_e, n_g)[0][:, 0]
        mu_s = mu_in
    J = rho * Tin / (1 - rho * K)
    Tv = _up(np.array([glaze_mu(mu_view)]), tau, n_e, n_g)[0][:, 0]
    L = J * Tv / n_g ** 2
    # specular: the enamel's surface, plus the glaze-enamel boundary seen through the enamel
    mu_se = np.sqrt(1 - (1 - mu_s * mu_s) / n_e ** 2)
    RB = float(fresnel(mu_s, 1.0, n_e))
    RA = float(fresnel(np.sqrt(1 - (n_e / n_g) ** 2 * (1 - mu_se ** 2)), n_g, n_e))
    a = np.exp(-tau / mu_se)
    spec = RB + (1 - RB) ** 2 * a * a * RA / (1 - RB * RA * a * a)
    return L, J * E, spec


def check():
    sys.path.insert(0, os.path.join(ROOT, "materials", "qinghua"))
    import importlib
    qo = importlib.import_module("optics")
    lam = np.linspace(400, 700, 7)
    tau = np.linspace(0.0, 2.0, 7)
    rho = np.full(7, 0.85)
    for mu_in in (None, 0.8, 0.5):
        a = stack(tau, rho, 1.52, 1.52, mu_in=mu_in)[0]
        b = qo.stack(tau, rho, 1.52, mu_in=mu_in)[0]
        print(f"n_e = n_g = 1.52, mu_in {mu_in}: max |this/qinghua - 1| = {np.max(np.abs(a / b - 1)):.2e}")
    # energy: with tau = 0 and rho = 1 nothing is lost: diffuse albedo + specular = 1 under diffuse light
    for ne, ng in ((1.52, 1.52), (1.62, 1.52), (1.70, 1.50)):
        L, alb, sp = stack(np.zeros(1), np.ones(1), ne, ng)
        # the specular albedo under diffuse light, 2 int R_spec(mu) mu dmu (the surface and the inner boundary)
        mu = np.linspace(1e-4, 1, 801)
        Rs = np.array([stack(np.zeros(1), np.ones(1), ne, ng, mu_in=m)[2][0] for m in mu])
        sa = 2 * np.trapezoid(Rs * mu, mu)
        print(f"n_e {ne}, n_g {ng}, rho 1, tau 0: diffuse albedo {alb[0]:.5f} + specular albedo {sa:.5f} = {alb[0] + sa:.5f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check()
