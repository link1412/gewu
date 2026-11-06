"""The lychee's substances as spectra and pbrt lines (material.json says what each number is and where it comes from).

    python3 -I materials/lychee/optics.py [SET]        # print the media's channel averages and diffuse reflectances

Every medium is written as pbrt's homogeneous medium on 360-830 nm, coefficients in 1/mm ("float scale" 1: the scene
unit is the millimetre), and its surface as a dielectric that carries it (MediumInterface "name" ""): tools/rgbscene.py
reads both, and tools/cycles_scene.py builds the Cycles volume. Nothing here knows the fruit's shape.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import LAM  # noqa: E402

PARTS = ("aril", "pericarp_outer", "pericarp_inner", "testa")


def load(path=os.path.join(HERE, "material.json")):
    return json.load(open(path))


def value(p, key, which):
    """A parameter's value; a dict of values is per set."""
    v = p[key]["value"]
    if isinstance(v, dict) and which in v:
        return v[which]
    if isinstance(v, dict) and set(v) & {"leidus", "guiwei"}:
        raise SystemExit(f"{key}: no value for the set {which!r}")
    if v is None:
        raise SystemExit(f"{key}: not fitted yet for the set {which!r} (materials/lychee/fit_card.py)")
    return v


def csv(name):
    rows = [ln.split(",") for ln in open(os.path.join(HERE, "data", name)) if ln[0].isdigit()]
    a = np.array(rows, float)
    return a[:, 0], a[:, 1]


def water_mua():
    """Pure water, 1/mm on LAM: Pope & Fry 1997 inside its 380-727.5 nm, Segelstein 1981 outside."""
    lp, ap = csv("water_pope97.csv")
    ls, as_ = csv("water_segelstein81.csv")
    if LAM.min() < ls.min() or LAM.max() > ls.max():
        raise SystemExit("water: Segelstein's rows do not cover 360-830 nm")
    a = np.interp(LAM, ls, as_)
    inside = (LAM >= lp.min()) & (LAM <= lp.max())
    a[inside] = np.interp(LAM[inside], lp, ap)
    return a / 10.0                                  # 1/cm -> 1/mm


def prospect(column):
    """A PROSPECT-D coefficient on LAM (data/prospect_d.csv, 400-900 nm), held at its 400 nm value below."""
    rows = [ln.split(",") for ln in open(os.path.join(HERE, "data", "prospect_d.csv")) if ln[0].isdigit()]
    a = np.array(rows, float)
    col = {"k_carotenoid_cm2_per_ug": 1, "k_anthocyanin_cm2_per_ug": 2, "k_brown_au": 3}[column]
    if LAM.max() > a[:, 0].max():
        raise SystemExit("prospect_d.csv does not reach 830 nm")
    return np.interp(LAM, a[:, 0], a[:, col])


def media(m, which):
    """{part: {"eta", "sigma_a", "sigma_s", "g"}} on LAM, 1/mm."""
    w = water_mua()
    out = {}
    p = m["aril"]
    g = value(p, "g", which)
    musp = value(p, "mus_prime_550_per_mm", which) * (LAM / 550.0) ** -value(p, "mus_prime_power", which)
    yellow = value(p, "yellow_mua_400_per_mm", which) * np.exp(-(LAM - 400.0) / value(p, "yellow_width_nm", which))
    out["aril"] = {"eta": value(p, "eta", which), "sigma_a": w + yellow, "sigma_s": musp / (1 - g), "g": g}
    p = m["pericarp_outer"]
    anth = value(p, "anthocyanin_ug_per_cm3", which) * prospect("k_anthocyanin_cm2_per_ug") / 10.0     # 1/cm -> 1/mm
    car = value(p, "carotenoid_ug_per_cm3", which) * prospect("k_carotenoid_cm2_per_ug") / 10.0
    kb = prospect("k_brown_au")
    brown = value(p, "browning_mua_500_per_mm", which) * kb / np.interp(500.0, LAM, kb)
    out["pericarp_outer"] = {"eta": value(p, "eta", which), "sigma_a": w + anth + car + brown,
                             "sigma_s": np.full(LAM.shape, value(p, "mus_prime_per_mm", which)), "g": 0.0}
    p = m["pericarp_inner"]
    out["pericarp_inner"] = {"eta": value(p, "eta", which), "sigma_a": w + value(p, "mua_per_mm", which),
                             "sigma_s": np.full(LAM.shape, value(p, "mus_prime_per_mm", which)), "g": 0.0}
    p = m["testa"]
    anc = value(p, "mua_anchors_per_mm", which)
    xs = np.array(sorted(float(k) for k in anc))
    out["testa"] = {"eta": value(p, "eta", which), "sigma_a": w + np.interp(LAM, xs, [anc[f"{x:g}"] for x in xs]),
                    "sigma_s": np.full(LAM.shape, value(p, "mus_per_mm", which)), "g": 0.0}
    return out


def spectrum(a, step=5):
    """pbrt's interleaved "spectrum" array, every `step` nm (piecewise linear between, as pbrt reads it)."""
    i = np.arange(0, len(LAM), step)
    if i[-1] != len(LAM) - 1:
        i = np.r_[i, len(LAM) - 1]
    return "[ " + " ".join(f"{LAM[k]:g} {a[k]:.6g}" for k in i) + " ]"


def pbrt_media(which, prefix="lychee_"):
    """MakeNamedMedium lines for every part; the medium of part X is named prefix + X."""
    md = media(load(), which)
    return [f'MakeNamedMedium "{prefix}{k}" "string type" "homogeneous" "spectrum sigma_a" {spectrum(v["sigma_a"])} '
            f'"spectrum sigma_s" {spectrum(v["sigma_s"])} "float g" [ {v["g"]:g} ] "float scale" [ 1 ]'
            for k, v in md.items()]


def pbrt_surface(part, which, displacement=None, roughness=0.0):
    """The dielectric that carries a part's medium (a smooth wet or waxed surface unless `roughness`)."""
    eta = media(load(), which)[part]["eta"]
    s = f'Material "dielectric" "float eta" [ {eta:g} ] "float roughness" [ {roughness:g} ] "bool remaproughness" false'
    if displacement:
        s += f' "texture displacement" "{displacement}"'
    return s


def cotyledon_reflectance(which):
    return value(load()["cotyledon"], "reflectance", which)


# --- a closed-form check, for starting values (the card's renders decide) -------------------------
def diffuse_reflectance(mua, musp, eta):
    """Total diffuse reflectance of a semi-infinite medium under diffuse-ish light, the dipole's closed form (Jensen,
    Marschner, Levoy & Hanrahan 2001, eq. for R_d; F_dr by Egan & Hilgeman's fit as they give it)."""
    a = musp / (mua + musp)
    Fdr = -1.440 / eta ** 2 + 0.710 / eta + 0.668 + 0.0636 * eta
    A = (1 + Fdr) / (1 - Fdr)
    s = np.sqrt(3 * (1 - a))
    return a / 2 * (1 + np.exp(-4 / 3 * A * s)) * np.exp(-s)


def fdr(eta):
    """Diffuse reflectance of the boundary seen from inside (Egan & Hilgeman's fit, as Jensen et al. 2001 give it)."""
    return -1.440 / eta ** 2 + 0.710 / eta + 0.668 + 0.0636 * eta


def km_layer(mua, musp, d, Rg):
    """Kubelka-Munk reflectance of a layer d thick over a background of reflectance Rg, inside the medium (no
    surface); K = 2 mu_a, S = 3/4 mu_s' - 1/4 mu_a (the diffusion-theory relation, Star, Marijnissen & van Gemert
    1988). A starting value only: the card's renders decide."""
    K = 2 * mua
    S = np.maximum(0.75 * musp - 0.25 * mua, 1e-9)
    a = 1 + K / S
    b = np.sqrt(a * a - 1)
    bc = b / np.tanh(np.maximum(b * S * d, 1e-12))
    return (1 - Rg * (a - bc)) / (a - Rg + bc)


def saunderson(R, eta):
    """Through the surface, the specular reflection left out (as the card's colour regions avoid highlights)."""
    ri = fdr(eta)
    re = 1 - (1 - ri) * eta ** 2
    return (1 - re) * (1 - ri) * R / (1 - ri * R)


def channel_media(which, sen, parts=("pericarp_outer", "testa")):
    """Per-channel coefficients for an RGB renderer, for the media whose absorption is steep inside a channel.
    rgbscene averages sigma_a over each channel (sensor x key light), which is exact for one short path only: the
    anthocyanin band puts 2.3 /mm into the camera's R channel, whose own wavelengths past 600 nm are hardly
    absorbed, and the red layer renders dull brown. Here sigma_a per channel is the value whose semi-infinite
    diffuse reflectance equals the channel average of the spectral one (diffuse_reflectance), sigma_s and g as
    rgbscene has them. Per metre, as scene.cycles.json writes media."""
    from scipy.optimize import brentq
    out = {}
    md = media(load(), which)
    for k in parts:
        v_ = md[k]
        musp = v_["sigma_s"] * (1 - v_["g"])
        Rc = sen.average(diffuse_reflectance(v_["sigma_a"], musp, v_["eta"]))
        mc = sen.average(musp)
        f = [lambda x, c=c: diffuse_reflectance(x, mc[c], v_["eta"]) - Rc[c] for c in range(3)]
        sa = [brentq(f[c], 0.0, 1e5) if f[c](0.0) > 0 else 0.0 for c in range(3)]
        out[k] = {"sigma_a_per_m": [x * 1000 for x in sa], "sigma_s_per_m": list(sen.average(v_["sigma_s"]) * 1000),
                  "g": v_["g"], "averaged_sigma_a_per_m": list(sen.average(v_["sigma_a"]) * 1000)}
    return out


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "leidus"
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import rgbscene
    sen = rgbscene.Sensor("canon_eos_5d_mkiv", 5500.0)
    for k, v in media(load(), which).items():
        sa, ss = sen.average(v["sigma_a"]), sen.average(v["sigma_s"])
        print(f"{k:15s} eta {v['eta']:.4f} g {v['g']:.2f}  sigma_a/mm {np.round(sa, 4)}  sigma_s/mm {np.round(ss, 3)}  "
              f"R_d(semi-inf) {np.round(diffuse_reflectance(sa, ss * (1 - v['g']), v['eta']), 3)}")


if __name__ == "__main__":
    main()
