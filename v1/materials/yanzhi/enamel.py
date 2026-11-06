"""胭脂红 (gold-ruby enamel): the optics of gold nanoparticles in a lead-glass enamel, from first principles
(docs/materials/yanzhi.md). Nothing here is fitted to a photograph; the card (card.py) does that.

    au_nk(lam, source)              gold's bulk n + ik on lam (nm): "jc" Johnson & Christy 1972, "mcpeak" McPeak 2015
    drude_fit(source)               the free-electron part of the bulk data (eps_b, hbar omega_p, hbar gamma_0), fitted
                                    to the table's infrared rows [F], to subtract it again in the size correction
    eps_size(lam, d_nm, A, source)  bulk epsilon with the electrons' extra damping at the particle's surface,
                                    gamma(R) = gamma_0 + A v_F / R (Kreibig's correction)
    particles(lam, n_host, sizes, weights, A, source)
                                    per unit gold volume fraction: sigma_a, sigma_s (1/mm), g, from Mie (tools/mie.py)
    kappa(lam, ...)                 the enamel's absorption per gram of gold per square metre: tau(lam) = c kappa(lam),
                                    c the gold's column density (g Au / m^2) through the layer at normal incidence
    n_host(lam, mat)                the enamel glass's index (material.json)
    appen_nD(wt)                    Appen's additive n_D and Abbe number from a composition (wt%)

    python3 -I materials/yanzhi/enamel.py          # the numbers for the doc: Drude fit, peaks, albedo, checks

Conventions: Bohren & Huffman's (n + ik, k >= 0), as tools/mie.py. Wavelengths in vacuum, nm.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mie  # noqa: E402

HC_EV_NM = 1239.841984          # h c in eV nm [I, CODATA]
HBAR_EV_S = 6.582119569e-16     # hbar in eV s [I, CODATA]
RHO_AU = 19.32                  # g/cm^3, gold at room temperature [I, CRC Handbook]
DATA = {"jc": "au_johnson_christy_1972.txt", "mcpeak": "au_mcpeak_2015.txt"}


def load():
    return json.load(open(os.path.join(HERE, "material.json")))


def _table(source):
    t = np.loadtxt(os.path.join(HERE, "data", DATA[source]), comments="#")
    return t[:, 0] * 1000.0, t[:, 1], t[:, 2]


def au_nk(lam, source="jc"):
    """Gold's bulk n + ik at lam (nm), interpolated linearly in photon energy in epsilon = (n + ik)^2 (the table
    rows of Johnson & Christy are evenly spaced in energy; epsilon is the smooth quantity) [A: linear]."""
    L, n, k = _table(source)
    lam = np.asarray(lam, float)
    if lam.min() < L.min() or lam.max() > L.max():
        raise ValueError(f"au_nk: {source} covers {L.min():.0f}-{L.max():.0f} nm, asked {lam.min():.0f}-{lam.max():.0f}")
    e = (n + 1j * k) ** 2
    E, Et = HC_EV_NM / lam, HC_EV_NM / L
    o = np.argsort(Et)
    eps = np.interp(E, Et[o], e.real[o]) + 1j * np.interp(E, Et[o], e.imag[o])
    return np.sqrt(eps)        # principal root: Im >= 0 since Im(eps) > 0


def drude_fit(source="jc", lam_min=950.0):
    """eps = eps_b - wp^2 / (w (w + i g0)) fitted to the table's rows at lam >= lam_min (the infrared, where the
    interband transitions are far): returns (eps_b, hbar wp in eV, hbar g0 in eV) [F]. Least squares on eps1 and
    eps2 together, each relative to its own size."""
    from scipy.optimize import least_squares
    L, n, k = _table(source)
    m = L >= lam_min
    w = HC_EV_NM / L[m]
    e = (n[m] + 1j * k[m]) ** 2

    def model(p):
        eb, wp, g = p
        return eb - wp * wp / (w * (w + 1j * g))

    def res(p):
        d = model(p) - e
        return np.concatenate([d.real / np.abs(e.real), d.imag / np.abs(e.imag)])
    r = least_squares(res, [5.0, 9.0, 0.07], bounds=([0.0, 5.0, 0.005], [20.0, 12.0, 0.5]))
    return tuple(float(v) for v in r.x), float(np.sqrt(np.mean(r.fun ** 2)))


def eps_size(lam, d_nm, A, source="jc", drude=None, v_f=1.40e6):
    """Bulk epsilon with the free electrons' damping raised by scattering at the surface of a sphere of diameter
    d_nm: eps(R) = eps_bulk + wp^2 / (w (w + i g0)) - wp^2 / (w (w + i g(R))), g(R) = g0 + A hbar v_F / R
    (Kreibig & von Fragstein 1969; Kreibig & Vollmer 1995). v_F in m/s. A = 0: the bulk."""
    lam = np.asarray(lam, float)
    eps = au_nk(lam, source) ** 2
    if A == 0:
        return eps
    if drude is None:
        drude = drude_fit(source)[0]
    _, wp, g0 = drude
    w = HC_EV_NM / lam
    gR = g0 + A * HBAR_EV_S * v_f / (0.5 * d_nm * 1e-9)
    return eps + wp * wp / (w * (w + 1j * g0)) - wp * wp / (w * (w + 1j * gR))


def particles(lam, n_host, sizes, weights=None, A=0.0, source="jc", drude=None):
    """Spheres of gold in a clear glass of index n_host (scalar or over lam), number fractions `weights` over the
    diameters `sizes` (nm), each with its own size-corrected epsilon. Per unit volume fraction of gold:
    sigma_a, sigma_s in 1/mm (independent scattering: at the enamel's ppm-level volume fractions S(q) = 1), g.
    Returns a dict over lam."""
    lam = np.atleast_1d(np.asarray(lam, float))
    sizes = np.atleast_1d(np.asarray(sizes, float))
    w = np.ones_like(sizes) if weights is None else np.asarray(weights, float)
    w = w / w.sum()
    nh = np.broadcast_to(np.asarray(n_host, float), lam.shape)
    if drude is None and A != 0:
        drude = drude_fit(source)[0]
    Cabs = np.zeros(len(lam)); Csca = np.zeros(len(lam)); gC = np.zeros(len(lam))
    for d, wi in zip(sizes, w):
        npart = np.sqrt(eps_size(lam, d, A, source, drude))
        x = 2 * np.pi * nh * (d / 2) / lam
        qe, qs, _, g = mie.mie(npart / nh, x)
        area = np.pi * (d / 2) ** 2                       # nm^2
        Cabs += wi * (qe - qs) * area
        Csca += wi * qs * area
        gC += wi * g * qs * area
    vol = math.pi / 6 * float(np.sum(w * sizes ** 3))     # mean volume, nm^3
    # per unit volume fraction: number density 1/vol (1/nm^3) times cross-section (nm^2) = 1/nm -> 1/mm
    return {"lam_nm": lam, "sigma_a": Cabs / vol * 1e6, "sigma_s": Csca / vol * 1e6,
            "g": np.where(Csca > 0, gC / np.maximum(Csca, 1e-300), 0.0)}


def kappa(lam, n_host, sizes, weights=None, A=0.0, source="jc"):
    """The absorption per unit column density of gold: tau(lam) = c kappa(lam) at normal incidence, c in g Au/m^2.
    sigma_a = kappa_phi phi; tau = sigma_a d = kappa_phi (phi d); phi d = c / rho_Au (a volume of gold per area)."""
    p = particles(lam, n_host, sizes, weights, A, source)
    um_per_gm2 = 1.0 / RHO_AU                              # 1 g/m^2 of gold is a 1/19.32 um thick layer
    return p["sigma_a"] * um_per_gm2 * 1e-3, p           # (1/mm) * mm


MOLAR = {"Na2O": 61.979, "MgO": 40.304, "Al2O3": 101.961, "SiO2": 60.084, "PbO": 223.199, "K2O": 94.196,
         "CaO": 56.077, "TiO2": 79.866, "MnO": 70.937, "Fe2O3": 159.688, "CuO": 79.545, "Au2O3": 441.93}   # g/mol [I]


def appen_nD(wt):
    """Appen's additive n_D and mean dispersion n_F - n_C over the oxides with a factor (mol% basis):
    SiO2, PbO (2.350 - 0.0067 (S - 50), S = SiO2 + Al2O3 mol%; dispersion 1e-5 (7440 - 72 (S - 50))), K2O, Na2O from
    the 1963 handbook's Table 72 (Appen et al., Spravochnik po proizvodstvu stekla, vol. 1, pp.206-207; transcribed by
    research S7, ref/yanzhi/research2/sources/index) [I]; Al2O3, CaO, MgO, TiO2 from EP3013762B1 as materials/ru_glaze uses
    them [I]. The dispersion only from the four main oxides (the others' factors not in hand). Fe2O3, MnO, CuO, Au2O3
    and the "trace" As2O3 have no factor and are left out (1.4 wt% here). Returns (n_D, Abbe number, wt% left out)."""
    w = {k: v for k, v in wt.items() if isinstance(v, (int, float))}
    q = {k: v / MOLAR[k] for k, v in w.items()}
    t = sum(q.values())
    p = {k: 100 * v / t for k, v in q.items()}
    ps = p["SiO2"]
    S = ps + p.get("Al2O3", 0.0)
    f = {"SiO2": 1.475 if ps <= 67 else 1.475 - 0.0005 * (ps - 67), "PbO": 2.350 - 0.0067 * (S - 50),
         "K2O": 1.575, "Na2O": 1.590, "Al2O3": 1.520, "CaO": 1.730, "MgO": 1.610, "TiO2": 2.480 - 0.005 * ps}
    D = {"SiO2": 0.00675, "PbO": (7440 - 72 * (S - 50)) * 1e-5, "K2O": 0.01300, "Na2O": 0.01420}
    have = [k for k in p if k in f]
    n = sum(p[k] * f[k] for k in have) / sum(p[k] for k in have)
    hd = [k for k in p if k in D]
    d = sum(p[k] * D[k] for k in hd) / sum(p[k] for k in hd)
    return n, (n - 1) / d, sum(w[k] for k in w if k not in f)


def n_host(lam, mat=None):
    """The enamel glass's index over lam: two-term Cauchy through n_D with the Abbe number (material.json)."""
    mat = mat or load()
    g = mat["enamel"]["glass"]
    nD, V = g["n_D"]["value"], g["abbe_number"]["value"]
    lines = {"D": 589.294, "F": 486.133, "C": 656.273}
    um = lambda k: (lines[k] * 1e-3) ** 2
    B = (nD - 1) / V / (1 / um("F") - 1 / um("C"))
    return nD - B / um("D") + B / (np.asarray(lam, float) * 1e-3) ** 2


def peak(lam, y):
    i = int(np.argmax(y))
    if 0 < i < len(y) - 1:                               # parabola through the three points about the maximum
        a, b, c = y[i - 1], y[i], y[i + 1]
        return float(lam[i] + 0.5 * (a - c) / (a - 2 * b + c) * (lam[1] - lam[0]))
    return float(lam[i])


def main():
    lam = np.arange(380.0, 781.0, 1.0)
    for src in ("jc", "mcpeak"):
        (eb, wp, g0), rms = drude_fit(src)
        print(f"{src}: Drude fit to the rows >= 950 nm: eps_b {eb:.2f}, hbar wp {wp:.3f} eV, hbar g0 {g0:.4f} eV "
              f"(rms relative residual {rms:.3f})")
    print("\ncheck: in water (n 1.333, no dispersion), the peak of a 20 nm sphere's absorption, bulk and A = 1:")
    for src in ("jc", "mcpeak"):
        for A in (0.0, 1.0):
            p = particles(lam, 1.333, [20.0], A=A, source=src)
            print(f"  {src} A {A}: peak {peak(lam, p['sigma_a'] + p['sigma_s']):.1f} nm (extinction)")
    mat = load()
    n, V, out = appen_nD(mat["enamel"]["glass"]["composition_wt_pct"]["value"])
    print(f"\nAppen on the enamel's composition (H18 Yongzheng): n_D {n:.4f}, Abbe {V:.1f} ({out:.2f} wt% without a "
          f"factor); material.json uses n_D {mat['enamel']['glass']['n_D']['value']}, "
          f"Abbe {mat['enamel']['glass']['abbe_number']['value']}")
    nh = n_host(lam, mat)
    print(f"\nenamel glass: n {nh[lam == 450][0]:.4f} / {nh[lam == 550][0]:.4f} / {nh[lam == 650][0]:.4f} at 450/550/650 nm")
    print("gold spheres in it, per gram of gold per m^2 (tau = c kappa), and the single-scattering albedo:")
    print("   d nm   A   source   peak nm   kappa(peak)  FWHM nm   albedo(peak)  albedo(650)")
    for src in ("jc", "mcpeak"):
        for A in (0.0, 0.5, 1.0):
            for d in (5.0, 10.0, 20.0, 40.0, 60.0):
                k, p = kappa(lam, nh, [d], A=A, source=src)
                pk = peak(lam, k)
                half = lam[k >= k.max() / 2]
                alb = p["sigma_s"] / (p["sigma_s"] + p["sigma_a"])
                print(f"  {d:5.0f}  {A:3.1f}  {src:7s}  {pk:7.1f}   {k.max():9.3f}   {half[-1] - half[0]:6.0f}   "
                      f"{alb[np.argmax(k)]:10.4f}   {alb[lam == 650][0]:9.4f}")


if __name__ == "__main__":
    main()
