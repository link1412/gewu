"""胭脂红 card, round 2: why is the model more saturated than the photo (a* high by 8-11 on locus.py's light-free
test)? Three hypotheses, each a change to locus.py's model, scored the same way (per photo region, the best c and
light factor E, the CIEDE2000 left over; the photo regions from a card_measure.json):

  base      locus.py's model: the 1-D stack (stack.py) at normal view, uniform light, through the 5D Mark IV and
            its matrix (card.py's development)
  gloss     + a neutral term k x white (the glaze's surface reflecting a surround; k free, 0-0.08 of the white)
  cie       the same stack seen by the CIE 1931 observer instead of the simulated camera (von Kries in BT.709 on
            the 5500 K white, as card.py balances)
  sizes     gold particles 20-60 nm (uniform in number) instead of 20 nm; also lognormal around 30 nm (sigma 0.4)
  A0.5      Kreibig's A 0.5 (Takebe's panel c fitted 0.25-0.5)

    python3 -I materials/yanzhi/lightfit/diag.py out/materials/yanzhi/card/runs/c0.56/card_measure.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import card  # noqa: E402
import enamel  # noqa: E402
import stack  # noqa: E402
from camera import LAM, blackbody, lab, rgb709_from_xyz  # noqa: E402


def de2000(l1, l2):
    """CIEDE2000, vectorised over the leading axes (Sharma, Wu & Dalal 2005)."""
    L1, a1, b1 = np.moveaxis(l1, -1, 0)
    L2, a2, b2 = np.moveaxis(l2, -1, 0)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = 0.5 * (C1 + C2)
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lpm, Cpm = 0.5 * (L1 + L2), 0.5 * (C1p + C2p)
    hs = h1p + h2p
    hpm = np.where(np.abs(h1p - h2p) <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2))
    T = (1 - 0.17 * np.cos(np.radians(hpm - 30)) + 0.24 * np.cos(np.radians(2 * hpm))
         + 0.32 * np.cos(np.radians(3 * hpm + 6)) - 0.20 * np.cos(np.radians(4 * hpm - 63)))
    dth = 30 * np.exp(-(((hpm - 275) / 25) ** 2))
    RC = 2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25.0 ** 7))
    SL = 1 + 0.015 * (Lpm - 50) ** 2 / np.sqrt(20 + (Lpm - 50) ** 2)
    SC, SH = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    RT = -np.sin(np.radians(2 * dth)) * RC
    return np.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))


CS = np.linspace(0.02, 1.5, 149)
ES = np.exp(np.linspace(np.log(0.1), np.log(3.0), 86))
KS = np.r_[0.0, np.linspace(0.0025, 0.08, 32)]


def spectra(k, mat):
    rho = np.full(LAM.shape, mat["body"]["albedo"]["value"])
    ne, ng = float(enamel.n_host(589.3, mat)), mat["glaze"]["eta"]["value"]
    return np.array([stack.stack(c * k, rho, ne, ng)[0] for c in np.r_[0.0, CS]])


def rgb_camera(Rs):
    W = card._S.sens * blackbody(card.K_LIGHT)
    raw = Rs @ W.T
    return (raw[1:] / raw[0]) @ card._CAL["C"].T


def rgb_cie(Rs):
    xyz = Rs @ (card._S.cmf * blackbody(card.K_LIGHT)).T
    M = rgb709_from_xyz(card._WN)
    rgb = xyz @ M.T
    return rgb[1:] / rgb[0]


def best(target_lab, rgb, ks=(0.0,)):
    """min over c, E, k of dE00(target, E rgb(c) + k)."""
    ks = np.asarray(ks)
    v = ES[None, :, None, None] * rgb[:, None, None, :] + ks[None, None, :, None]       # c, E, k, 3
    L = card.lab(v @ card._XYZ.T, card._WN) if False else lab(v @ card._XYZ.T, card._WN)
    d = de2000(np.broadcast_to(target_lab, L.shape), L)
    i = np.unravel_index(np.argmin(d), d.shape)
    return float(d[i]), CS[i[0]], ES[i[1]], ks[i[2]], L[i]


def main():
    m = json.load(open(sys.argv[1]))
    mat = card.material()
    g = mat["enamel"]["gold"]
    nh = enamel.n_host(LAM, mat)
    k20, _ = enamel.kappa(LAM, nh, [20.0], A=0.25, source="mcpeak")
    d = np.arange(20, 61, 2.0)
    ku, _ = enamel.kappa(LAM, nh, d, A=0.25, source="mcpeak")
    dl = np.arange(8, 90, 2.0)
    wl = np.exp(-0.5 * (np.log(dl / 30) / 0.4) ** 2) / dl
    kl, _ = enamel.kappa(LAM, nh, dl, wl, A=0.25, source="mcpeak")
    kA, _ = enamel.kappa(LAM, nh, [20.0], A=0.5, source="mcpeak")
    S20 = spectra(k20, mat)
    cases = [("base", rgb_camera(S20), (0.0,)), ("gloss", rgb_camera(S20), KS), ("cie", rgb_cie(S20), (0.0,)),
             ("cie+gloss", rgb_cie(S20), KS),
             ("sizes 20-60", rgb_camera(spectra(ku, mat)), (0.0,)),
             ("lognormal 30/0.4", rgb_camera(spectra(kl, mat)), (0.0,)), ("A 0.5", rgb_camera(spectra(kA, mat)), (0.0,))]
    out = {}
    for name, rgb, ks in cases:
        rows = []
        for reg, v in m["photo"]["rgb"].items():
            t = card.lab_of(np.array(v))
            dE, c, E, kk, L = best(t, rgb, ks)
            rows.append((reg, dE, c, E, kk, t, L))
        dm = np.mean([r[1] for r in rows])
        print(f"{name:17s} mean dE00 {dm:.2f}  | " + "  ".join(
            f"{r[0][:1]}{r[0].split('_')[1][:1]} {r[1]:.1f} (c {r[2]:.2f} k {r[4]:.3f} da {r[6][1] - r[5][1]:+.1f})" for r in rows))
        out[name] = {"mean_dE00": dm, "regions": [{"region": r[0], "dE00": r[1], "c": r[2], "E": r[3], "k": r[4],
                                                   "photo_lab": r[5].tolist(), "model_lab": r[6].tolist()} for r in rows]}
    json.dump(out, open(os.path.join(os.path.dirname(sys.argv[1]), "diag.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
