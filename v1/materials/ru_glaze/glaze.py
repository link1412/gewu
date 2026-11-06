"""The Ru glaze's optics from its chemistry (material.json; docs/materials/ru_glaze.md): what can be computed
before anything is fitted.

    composition_mol(wt)           oxide mol% from wt%
    appen_nD(wt)                  Appen's n_D (EP3013762B1 factors), and the share of oxides it has no factor for
    n_cauchy(lam, nD, abbe)       n(lambda) through n_D with the given Abbe number (two-term Cauchy)
    eps_fe2(lam), eps_fe3(lam)    molar absorption coefficients, decadic, L/mol/cm (Volotinen 2008's peaks)
    iron_mol_per_l(sample)        Fe2+ and Fe3+ concentrations of a sample
    sigma_a(lam, sample)          the glass's absorption, 1/mm (natural log)
    lab(R)                        CIELAB of a reflectance spectrum on camera.LAM (D65, CIE 1931 2 deg)

    python3 -I materials/ru_glaze/glaze.py        # the derived numbers, for the material doc
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import LAM, pbrt_array, piecewise  # noqa: E402
from camera import lab as lab_from_xyz  # noqa: E402

MOLAR = {"SiO2": 60.084, "Al2O3": 101.961, "CaO": 56.077, "MgO": 40.304, "K2O": 94.196, "Na2O": 61.979,
         "TiO2": 79.866, "Fe2O3": 159.688, "P2O5": 141.943, "MnO": 70.937, "MnO2": 86.937}
LINES_NM = {"D": 589.294, "F": 486.133, "C": 656.273}


def load():
    return json.load(open(os.path.join(HERE, "material.json")))


def composition_mol(wt):
    q = {k: v / MOLAR[k] for k, v in wt.items()}
    tot = sum(q.values())
    return {k: 100 * v / tot for k, v in q.items()}


def appen_nD(wt):
    """n_D = sum p_i f_i / sum p_i over the oxides with a factor (mol%; EP3013762B1, P2O5 from Duminis 2018).
    Returns (n_D, wt% left out, mol% left out): Fe2O3, MnO and MnO2 have no factor in either table."""
    p = composition_mol(wt)
    ps = p["SiO2"]
    if not 50 <= ps <= 80:
        raise SystemExit(f"appen_nD: SiO2 {ps:.1f} mol% outside the TiO2 factor's range 50-80")
    f = {"SiO2": 1.475 if ps <= 67 else 1.5085 - 0.0005 * ps, "Al2O3": 1.520, "CaO": 1.730, "MgO": 1.610,
         "Na2O": 1.590, "K2O": 1.575 if p.get("Na2O", 0.0) >= 1 else 1.595, "TiO2": 2.480 - 0.005 * ps, "P2O5": 1.31}
    have = [k for k in p if k in f]
    out = [k for k in p if k not in f]
    n = sum(p[k] * f[k] for k in have) / sum(p[k] for k in have)
    return n, sum(wt[k] for k in out), sum(p[k] for k in out)


def n_cauchy(lam, nD, abbe):
    """n = A + B / lambda^2 with n(D) = nD and (nD - 1) / (nF - nC) = abbe; lambda in nm."""
    um = lambda k: (LINES_NM[k] * 1e-3) ** 2
    B = (nD - 1) / abbe / (1 / um("F") - 1 / um("C"))
    A = nD - B / um("D")
    return A + B / (np.asarray(lam, float) * 1e-3) ** 2


def _peaks(mat, ions):
    return [(nu0, sg, H) for ion, nu0, sg, H in mat["iron"]["volotinen2008_peaks"]["value"] if ion in ions]


def _sum(peaks, lam):
    nu = 1e7 / np.asarray(lam, float)
    return sum(H * np.exp(-0.5 * ((nu - nu0) / sg) ** 2) for nu0, sg, H in peaks)


def eps_fe2(lam, mat=None, glass=None):
    """Fe2+: Volotinen's p1-p5, scaled to epsilon(1000 nm) of the glass chosen in material.json (or `glass`)."""
    mat = mat or load()
    e = mat["iron"]["eps_fe2_1000nm"]
    k = e[glass or e["use"]] / float(_sum(_peaks(mat, ("Fe2+",)), 1000.0))
    return k * _sum(_peaks(mat, ("Fe2+",)), lam)


def eps_fe3(lam, mat=None, variant=None):
    """Fe3+: Volotinen's p6-p14 with Fe2+'s conversion 30 / 11.920; 'table_sum' adds the peaks as tabulated,
    'eq1_nt_half' weights the tetrahedral and octahedral ones by 0.5 (their Eq. 1)."""
    mat = mat or load()
    variant = variant or mat["iron"]["fe3_normalisation"]["value"]
    k = 30.0 / float(_sum(_peaks(mat, ("Fe2+",)), 1000.0))
    t, o, uv = (_sum(_peaks(mat, (ion,)), lam) for ion in ("Fe3+t", "Fe3+o", "Fe3+uv"))
    if variant == "table_sum":
        return k * (t + o + uv)
    if variant == "eq1_nt_half":
        return k * (0.5 * (t + o) + uv)
    raise SystemExit(f"eps_fe3: variant {variant}")


def iron_mol_per_l(sample, mat=None):
    """c(Fe2+), c(Fe3+) in mol/L: all iron, reported as Fe2O3 wt%, at the glass density, split by the measured
    Fe2+ fraction: c = 20 rho p / M(Fe2O3)."""
    mat = mat or load()
    s = mat["samples"][sample]
    rho = mat["glass"]["density_g_cm3"]["value"]
    c = 20 * rho * s["composition_wt"]["value"]["Fe2O3"] / MOLAR["Fe2O3"]
    f2 = s["fe2_fraction"]["value"]
    return f2 * c, (1 - f2) * c


def sigma_a(lam, sample, mat=None, glass=None, variant=None):
    """The glass's absorption from its iron, 1/mm (natural log): ln 10 (eps2 c2 + eps3 c3) / 10."""
    mat = mat or load()
    c2, c3 = iron_mol_per_l(sample, mat)
    return math.log(10) * (eps_fe2(lam, mat, glass) * c2 + eps_fe3(lam, mat, variant) * c3) / 10.0


_CMF = None


def lab(R):
    """CIELAB (D65, CIE 1931 2 deg) of reflectance spectra R[..., LAM] on camera.LAM (360-830 nm, 1 nm)."""
    global _CMF
    if _CMF is None:
        lam = pbrt_array("CIE_lambda")
        cmf = np.array([np.interp(LAM, lam, pbrt_array(n)) for n in ("CIE_X", "CIE_Y", "CIE_Z")])
        d65 = piecewise(pbrt_array("CIE_Illum_D6500"))
        _CMF = (cmf * d65) / (cmf[1] @ d65)
    xyz = np.asarray(R, float) @ _CMF.T
    return lab_from_xyz(xyz, _CMF.sum(1))


def main():
    mat = load()
    print("Appen n_D (glass only; iron and manganese have no factor):")
    for name, wt in [(k, v["composition_wt"]["value"]) for k, v in mat["samples"].items()] + \
                    [(k, mat["phases"][k]["value"]) for k in ("si_rich_wt", "ca_rich_wt", "ca_rich_droplet_row_wt")]:
        n, w_out, m_out = appen_nD(wt)
        print(f"  {name:24s} n_D {n:.4f}   left out {w_out:.2f} wt% ({m_out:.2f} mol%)")
    ns = appen_nD(mat["phases"]["si_rich_wt"]["value"])[0]
    print(f"  Ca-rich minus Si-rich: {appen_nD(mat['phases']['ca_rich_wt']['value'])[0] - ns:+.4f} (EDS3), "
          f"{appen_nD(mat['phases']['ca_rich_droplet_row_wt']['value'])[0] - ns:+.4f} (droplet row)")
    an = mat["anorthite"]["n_principal"]
    lam_an = np.array(an["lambda_nm"])
    i = np.argmin(abs(lam_an - 589.3))
    print(f"  anorthite, mean of the three axes at {lam_an[i]} nm: "
          f"{(an['n_alpha'][i] + an['n_beta'][i] + an['n_gamma'][i]) / 3:.4f}")
    lam = np.array([400, 450, 500, 550, 600, 650, 700, 750])
    print("\nmolar absorption, L/mol/cm:", " ".join(f"{l:5d}" for l in lam))
    print("  Fe2+ (E-glass scale)   ", " ".join(f"{v:5.2f}" for v in eps_fe2(lam, mat)))
    print("  Fe2+ (soda-lime scale) ", " ".join(f"{v:5.2f}" for v in eps_fe2(lam, mat, "soda_lime")))
    print("  Fe3+ (table sum)       ", " ".join(f"{v:5.2f}" for v in eps_fe3(lam, mat)))
    print("  Fe3+ (Eq. 1, n_t 0.5)  ", " ".join(f"{v:5.2f}" for v in eps_fe3(lam, mat, "eq1_nt_half")))
    for s in mat["samples"]:
        c2, c3 = iron_mol_per_l(s, mat)
        print(f"\n{s}: c(Fe2+) {c2:.3f}, c(Fe3+) {c3:.3f} mol/L")
        print("  sigma_a, 1/mm          ", " ".join(f"{v:5.3f}" for v in sigma_a(lam, s, mat)))
        # a clear glaze of the sample's thickness on a white body, seen straight on: the round trip's colour
        d = mat["samples"][s]["thickness_um"]["value"] * 1e-3
        T2 = np.exp(-2 * d * sigma_a(LAM, s, mat))
        print(f"  clear {d:.3f} mm on white, one straight round trip: L*a*b* "
              + " ".join(f"{v:6.2f}" for v in lab(T2)))


if __name__ == "__main__":
    main()
