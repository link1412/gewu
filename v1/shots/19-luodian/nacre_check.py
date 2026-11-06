"""Checks of the nacre tables for shot 19 round 1 (docs/shots/19-luodian.md, 物理), and a plot for the sheet.

    python3 -I shots/19-luodian/nacre_check.py --lut out/shots/19-luodian/nacre_lut.npz --out out/shots/19-luodian/r1/tmm.png

1. The transfer-matrix code (nacre.py stack_r, from S2) on ONE film against the Airy formula
   (s and p, several angles): max |difference| printed; it must be < 1e-9.
2. Our stack's R(lambda) at 0, 30, 60 deg in air, layers parallel to the surface, tablets 420 nm (the luodian.md
   section 5 starting values): the shell's lobe (stack through the polished surface, s/p averaged), from the LUT.
   The check against the literature is a TREND check (Finnemore et al. 2012 Fig. 4, measured H. tuberculata
   15-75 deg: the reflection bands move to shorter wavelengths as the angle grows), not a fit to a curve.
3. The piece colours: d over the pieces' range at 0..60 deg, under the key light (5500 K), as sRGB swatches.
"""

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)        # nacre.py moved here from shots/19-dianluo in S10
import nacre  # noqa: E402
from camera import LAM, Spectra, blackbody, rgb709_from_xyz  # noqa: E402

sys.path.insert(0, HERE)        # this shot's pattern.py, not shots/19-dianluo's (round 1 charted S2's 360-480 nm by mistake)
sys.modules.pop("pattern", None)
import pattern  # noqa: E402
assert os.path.dirname(os.path.abspath(pattern.__file__)) == HERE


def airy_r(lam, th, n0, n1, n2, t, pol):
    """Single film n1 (thickness t) between n0 and n2: the textbook Airy amplitude, exp(-2i delta) convention."""
    s0 = np.sin(th)
    c0 = np.cos(th)
    c1 = np.sqrt(1 - (n0 * s0 / n1) ** 2 + 0j)
    c2 = np.sqrt(1 - (n0 * s0 / n2) ** 2 + 0j)
    if pol == "s":
        r01 = (n0 * c0 - n1 * c1) / (n0 * c0 + n1 * c1)
        r12 = (n1 * c1 - n2 * c2) / (n1 * c1 + n2 * c2)
    else:
        r01 = (n1 * c0 - n0 * c1) / (n1 * c0 + n0 * c1)
        r12 = (n2 * c1 - n1 * c2) / (n2 * c1 + n1 * c2)
    d = 2 * np.pi * n1 * t * c1 / lam
    e = np.exp(-2j * d)
    return (r01 + r12 * e) / (1 + r01 * r12 * e)


def lobe_at(L, d, theta_deg):
    """The untilted lobe spectrum (polished surface + stack, s/p mean) for tablets d at angle theta in air."""
    mu = np.cos(np.radians(theta_deg))
    b = np.sin(np.radians(theta_deg))           # untilted, isotropic: the tangential index is the sine in air
    i = np.interp(d, L["d_nm"], np.arange(len(L["d_nm"])))
    i0 = int(np.floor(i))
    f = i - i0
    out = 0
    for pol in ("s", "p"):
        Rd = (1 - f) * L[f"R_stack_{pol}"][i0] + f * L[f"R_stack_{pol}"][min(i0 + 1, len(L["d_nm"]) - 1)]
        R = np.array([np.interp(b, L["b"], Rd[:, k]) for k in range(len(L["lam"]))])
        Rt = np.array([np.interp(mu, L["mu"], L[f"R_top_{pol}"][:, k]) for k in range(len(L["lam"]))])
        T = 1 - Rt
        out = out + 0.5 * T * T * R / (1 - Rt * R)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lut", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 1. one film against Airy
    lam = LAM.astype(float)
    worst = 0.0
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for th in (0, 30, 60):
        for pol in ("s", "p"):
            r_tmm = nacre.stack_r(lam, np.sin(np.radians(th)), (1.0, 1.0), [((1.63, 1.63), 420.0)], (1.55, 1.55), pol)
            r_air = airy_r(lam, np.radians(th), 1.0, 1.63, 1.55, 420.0, pol)
            worst = max(worst, float(np.abs(np.abs(r_tmm) ** 2 - np.abs(r_air) ** 2).max()))
            if pol == "s":
                ax[0].plot(lam, np.abs(r_air) ** 2, lw=3, alpha=0.35, label=f"Airy {th} deg s")
                ax[0].plot(lam, np.abs(r_tmm) ** 2, "k--", lw=0.8)
    if worst > 1e-9:
        raise SystemExit(f"TMM vs Airy: max |dR| {worst:.2e}")
    ax[0].set_title(f"single film n 1.63, 420 nm on 1.55\nTMM (dashed) vs Airy: max |dR| = {worst:.1e}")
    ax[0].set_xlabel("wavelength nm")
    ax[0].set_xlim(380, 780)
    ax[0].legend(fontsize=7)

    # 2. our stack at 0/30/60 deg, d = 420
    L = np.load(a.lut)
    peaks = {}
    for th, c in ((0, "C3"), (30, "C2"), (60, "C0")):
        R = lobe_at(L, 420.0, th)
        ax[1].plot(L["lam"], R, c, label=f"{th} deg")
        # the long-wave band's peak, on the spectrum smoothed over 21 nm (the 32 draws leave a ripple)
        Rs = np.convolve(R, np.ones(21) / 21, mode="same")
        band = (L["lam"] >= 520) & (L["lam"] <= 760)
        mx = int(L["lam"][band][np.argmax(Rs[band])])
        peaks[th] = mx
    ax[1].set_title("our stack, tablets 420 +- 50 nm, organic 25 nm, ~100 pairs\n(lobe through the polished surface, s/p mean, 32 draws)")
    ax[1].set_xlabel("wavelength nm")
    ax[1].set_xlim(380, 780)
    ax[1].set_ylabel("reflectance")
    ax[1].legend()

    # 3. piece colours under 5500 K
    S = Spectra("canon_eos_5d_mkiv")
    key = blackbody(5500.0)
    white = S.cmf @ key / (S.cmf[1] @ key)
    M = rgb709_from_xyz(white)
    ds = np.linspace(pattern.D_RANGE_NM[0], pattern.D_RANGE_NM[1], 31)
    ths = np.arange(0, 61, 5)
    sw = np.zeros((len(ds), len(ths), 3))
    lum = np.zeros((len(ds), len(ths)))
    for i, d in enumerate(ds):
        for j, th in enumerate(ths):
            R = lobe_at(L, d, th)
            xyz = S.cmf @ (R * key) / (S.cmf[1] @ key)
            sw[i, j] = M @ xyz
            lum[i, j] = xyz[1]
    k = 1.0 / np.percentile(sw.max(2), 95)
    img = np.clip(sw * k, 0, 1)
    img = np.where(img <= 0.0031308, 12.92 * img, 1.055 * img ** (1 / 2.4) - 0.055)
    ax[2].imshow(img, aspect="auto", extent=(-2.5, 62.5, ds[-1] + 5, ds[0] - 5))
    ax[2].set_title("piece colour under 5500 K (sRGB, one exposure)\nrows: mean tablet d; columns: angle in air")
    ax[2].set_xlabel("angle deg")
    ax[2].set_ylabel("d nm")
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fig.savefig(a.out, dpi=110)
    print(f"TMM vs Airy (single film, s/p, 0/30/60 deg): max |dR| {worst:.2e}")
    print(f"420 nm stack, long-wave band peak (nm, 21 nm smoothing) at 0/30/60 deg: {peaks}")
    print(f"luminance reflectance of the lobe at 0 deg: {lum[:, 0].min():.3f}..{lum[:, 0].max():.3f}; at 30 deg "
          f"{lum[:, 6].min():.3f}..{lum[:, 6].max():.3f}")
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
