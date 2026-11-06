"""The cinnabar lacquer material (material.json): body reflectances of the lacquers and the family the carving indexes.

    import lacquer
    m = lacquer.load()
    lam, R = lacquer.body(m, "red")                  # (K,), (K,) body reflectance, no interface
    lacquer.write_family("family.npz", m, ["black", "red"])   # c = 0, 1 in that order

The family is the familymap of docs/textures.md: c is the layer's index in the craft's stack order, so the rows the
renderer interpolates between (at a band's edge, one texel wide) are neighbours in the stack.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAM = np.arange(400, 781, 10, dtype=float)


def load(path=None):
    return json.load(open(path or os.path.join(HERE, "material.json")))


def _spectrum(m, ref):
    if not ref.startswith("derived."):
        raise SystemExit(f"spectrum reference {ref!r}: expected derived.<name>")
    key = ref.split(".", 1)[1]
    if key not in m.get("derived", {}):
        raise SystemExit(f"material.json has no derived.{key}: run derive.py --write")
    v = np.asarray(m["derived"][key], float)
    lam, R = v[0::2], v[1::2]
    if not np.array_equal(lam, LAM):
        raise SystemExit(f"derived.{key}: not on 400-780 nm at 10 nm")
    return R


def km_add_absorption(R, ks_add):
    """Kubelka-Munk: R_inf -> K/S, add, back to R_inf."""
    R = np.clip(R, 1e-4, 1 - 1e-6)
    ks = (1 - R) ** 2 / (2 * R) + ks_add
    return 1 + ks - np.sqrt(ks * ks + 2 * ks)


def binder_absorption(m):
    """The lacquer polymer's absorption coefficient (1/mm) on LAM, from the 30 um film's transmission (material.json
    'binder'): a = -ln(T / T0) / 0.030 with T0 the two faces' Fresnel transmission; held flat below its first sample."""
    b = m["binder"]
    v = np.asarray(b["transmission_30um_pct"]["lambda_nm_value"], float)
    lam, T = v[0::2], v[1::2] / 100.0
    n = m["interface"]["eta"]["value"]
    T0 = (1 - ((n - 1) / (n + 1)) ** 2) ** 2
    a = -np.log(np.clip(T / T0, 1e-6, 1.0)) / 0.030
    return np.interp(LAM, lam, a)


def body(m, name, S=None):
    """Body reflectance of one lacquer (no interface) on LAM. For the red: the paint's R_inf with the binder's
    Kubelka-Munk absorption K = 2a added over the pigment's scattering S (1/mm): K/S += 2a/S. S None: material.json's
    scattering_S_per_mm (null there = no binder absorption)."""
    b = m["body"][name]
    if b.get("spectrum") == "flat":
        return LAM, np.full(LAM.shape, float(b["value"]))
    R = _spectrum(m, b["spectrum"])
    if S is None:
        S = b.get("scattering_S_per_mm", {}).get("value")
    if S:
        R = km_add_absorption(R, m["binder"]["km_K_over_a"]["value"] * binder_absorption(m) / S)
    return LAM, R


def interface(m):
    """(eta, alpha, gap mm) of the new, polished surface (its satin when old is crafts/weathering and wear)."""
    i = m["interface"]
    return i["eta"]["value"], i["ggx_alpha"]["value"], i["coat_gap_mm"]["value"]


def write_family(path, m, names, S=None):
    """familymap npz: c = 0..N-1 for the lacquers in `names` (the stack's order); S: the red's scattering (1/mm)."""
    R = np.stack([body(m, n, S if n == "red" else None)[1] for n in names])
    np.savez(path, lambda_nm=LAM, c=np.arange(len(names), dtype=float), R=np.clip(R, 0, 1))
    return {n: i for i, n in enumerate(names)}
