"""The ginkgo leaf's tissue as spectra and pbrt lines (material.json says what each number is and where it comes from).

    python3 -I materials/yinxing/optics.py [SET]          # print the lamina's and the vein's R, T per sensor channel
    python3 -I materials/yinxing/optics.py SET --family DIR   # write DIR/leaf_R.npz, DIR/leaf_T.npz (familymaps)

The leaf is a thin two-sided surface with Lambertian reflection R(lambda) and Lambertian transmission T(lambda)
(pbrt-v4's "diffusetransmission"), both from PROSPECT-D (prospect.py), a hemispherical-integral model: the angular
shape of the leaf's scattering (the cuticle's specular sheen, the forward peak of transmission) is not in it, and the
two faces are the same [A, round 1; docs/materials/yinxing.md]. The spatial variation is one parameter c in [0, 1],
the vascular bundle's share of the leaf's thickness (objects/yinxing/leaf.py writes c(u, v)): the leaf's PROSPECT
parameters run linearly from the lamina's (c = 0) to the vein column's (c = 1), and the family holds R and T at
FAMILY_C. PROSPECT starts at 400 nm; below it R and T are held at their 400 nm values [A] (pbrt's 360 nm start).
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import prospect as P  # noqa: E402
from camera import LAM  # noqa: E402

FAMILY_C = np.linspace(0.0, 1.0, 11)


def load(path=os.path.join(HERE, "material.json")):
    return json.load(open(path))


def value(entry, which):
    v = entry["value"]
    if isinstance(v, dict):
        if which not in v:
            raise SystemExit(f"no value for the set {which!r} ({sorted(v)})")
        v = v[which]
    if v is None:
        raise SystemExit(f"not fitted yet for the set {which!r}")
    return v


def lamina_params(m, which):
    L = m["lamina"]
    return {k: float(value(L[k], which)) for k in P.PARAMS}


def vein_params(m, which):
    """The vein column's PROSPECT parameters: N its own, the pigments the lamina's times the vein's pigment factor,
    water and dry matter the lamina's times the thickness ratio."""
    lam = lamina_params(m, which)
    V = m["vein"]
    f_pig = float(value(V["pigment_factor"], which))
    t = float(value(V["thickness_ratio"], which))
    return {"N": float(value(V["N"], which)), "Cab": lam["Cab"] * f_pig, "Car": lam["Car"] * f_pig,
            "Anth": lam["Anth"] * f_pig, "Cbrown": lam["Cbrown"] * f_pig, "Cw": lam["Cw"] * t, "Cm": lam["Cm"] * t}


def spectra(p):
    """R, T on LAM (360-830 nm): PROSPECT on 400-830, held at 400 nm below [A]."""
    lam, R, T = P.leaf(p, np.clip(LAM, 400.0, 830.0))
    return R, T


def mix(a, b, c):
    return {k: a[k] + c * (b[k] - a[k]) for k in a}


def family(m, which):
    a, b = lamina_params(m, which), vein_params(m, which)
    Rs, Ts = [], []
    for c in FAMILY_C:
        R, T = spectra(mix(a, b, c))
        Rs.append(R)
        Ts.append(T)
    return np.array(Rs), np.array(Ts)


def write_family(out, which, prefix="leaf"):
    """np.savez (stored, as pbrt's reader needs): lambda_nm, c, R; one file for R, one for T."""
    os.makedirs(out, exist_ok=True)
    Rs, Ts = family(load(), which)
    paths = {}
    for name, A in (("R", Rs), ("T", Ts)):
        p = os.path.join(out, f"{prefix}_{name}.npz")
        np.savez(p, lambda_nm=LAM.astype(np.float64), c=FAMILY_C.astype(np.float64), R=np.clip(A, 0, 1).astype(np.float64))
        paths[name] = p
    return paths


BROWN_C = np.array([0, 0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0, 3.7, 4.5, 5.5, 7.0])


def brown_families(m, which):
    """Round 2's families: indexed by Cbrown (senescence.py's brown.exr), one for the lamina and one for the vein
    column (its Cbrown the lamina's times the vein's pigment factor, as its other pigments)."""
    a, b = lamina_params(m, which), vein_params(m, which)
    f_pig = float(value(m["vein"]["pigment_factor"], which))
    out = {}
    for name, base, k in (("lam", a, 1.0), ("vein", b, f_pig)):
        Rs, Ts = [], []
        for cb in BROWN_C:
            q = dict(base)
            q["Cbrown"] = base["Cbrown"] + k * float(cb)
            R, T = spectra(q)
            Rs.append(R)
            Ts.append(T)
        out[name] = (np.array(Rs), np.array(Ts))
    return out


def write_brown_families(out, which):
    os.makedirs(out, exist_ok=True)
    paths = {}
    for name, (Rs, Ts) in brown_families(load(), which).items():
        for q, A in (("R", Rs), ("T", Ts)):
            p = os.path.join(out, f"{name}_{q}.npz")
            np.savez(p, lambda_nm=LAM.astype(np.float64), c=BROWN_C.astype(np.float64), R=np.clip(A, 0, 1).astype(np.float64))
            paths[f"{name}_{q}"] = p
    return paths


def pbrt_blade_mix(brown="brown.exr", amount="veinamt.exr", brown_vein=None):
    """The blade as pbrt's mix of two named materials, the lamina and the vein column, each a familymap on the
    brown map; the mix amount is the vein map with its strength (senescence.py). pbrt picks one of the two per
    shading point with probability 'amount', which averages to the area-weighted mix of the two over a pixel
    (right for veins narrower than a pixel; for a resolved vein it is a mix of R and T rather than of PROSPECT's
    parameters, as round 1 did) [A]."""
    L = []
    for name in ("lam", "vein"):
        bmap = brown_vein if (name == "vein" and brown_vein) else brown
        for q in ("R", "T"):
            L.append(f'Texture "{name}_{q}" "spectrum" "familymap" "string family" "{name}_{q}.npz" '
                     f'"string map" "{bmap}" "string wrap" "clamp"')
        L.append(f'MakeNamedMaterial "{name}" "string type" "diffusetransmission" '
                 f'"texture reflectance" "{name}_R" "texture transmittance" "{name}_T"')
    L.append(f'Texture "veinamt" "float" "imagemap" "string filename" "{amount}" "string wrap" "clamp" '
             f'"string encoding" "linear"')
    L.append('Material "mix" "string materials" [ "lam" "vein" ] "texture amount" "veinamt"')
    return L


def spectrum_array(a, step=5):
    i = np.arange(0, len(LAM), step)
    if i[-1] != len(LAM) - 1:
        i = np.r_[i, len(LAM) - 1]
    return "[ " + " ".join(f"{LAM[k]:g} {a[k]:.6g}" for k in i) + " ]"


def pbrt_blade(R_family, T_family, cmap, relief=None, prefix="leaf"):
    """The blade's textures and material: familymaps of R and T on the vein map c(u, v)."""
    lines = [f'Texture "{prefix}_R" "spectrum" "familymap" "string family" "{os.path.basename(R_family)}" '
             f'"string map" "{cmap}" "string wrap" "clamp"',
             f'Texture "{prefix}_T" "spectrum" "familymap" "string family" "{os.path.basename(T_family)}" '
             f'"string map" "{cmap}" "string wrap" "clamp"']
    mat = f'Material "diffusetransmission" "texture reflectance" "{prefix}_R" "texture transmittance" "{prefix}_T"'
    if relief:
        lines.append(f'Texture "{prefix}_relief" "float" "imagemap" "string filename" "{relief}" "string wrap" "clamp"')
        mat += f' "texture displacement" "{prefix}_relief"'
    return lines + [mat]


def petiole_params(m, which):
    """The petiole wall seen as a leaf of its own: the lamina's pigments per volume over the wall's thickness, N in
    proportion [A, round 1: the petiole is a tube of the same tissue, its wall thickness the config's]."""
    lam = lamina_params(m, which)
    k = float(value(m["petiole"]["thickness_over_lamina"], which))
    return {key: (lam[key] * k) for key in P.PARAMS}


def pbrt_petiole(m, which):
    R, T = spectra(petiole_params(m, which))
    return (f'Material "diffusetransmission" "spectrum reflectance" {spectrum_array(R)} '
            f'"spectrum transmittance" {spectrum_array(T)}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set", nargs="?", default="nobbip")
    ap.add_argument("--family")
    a = ap.parse_args()
    m = load()
    if a.family:
        print(write_family(a.family, a.set))
        return
    import rgbscene
    sen = rgbscene.Sensor("canon_eos_5d_mkiv", 5500.0)
    for name, p in (("lamina", lamina_params(m, a.set)), ("vein", vein_params(m, a.set)),
                    ("petiole", petiole_params(m, a.set))):
        R, T = spectra(p)
        print(f"{name:8s} {json.dumps({k: round(v, 4) for k, v in p.items()})}")
        print(f"         R/ch {np.round(sen.average(R), 4)}  T/ch {np.round(sen.average(T), 4)}")


if __name__ == "__main__":
    main()
