"""Coherent thin films: the reflectance of a stack of thin layers between two half-spaces, by the transfer
matrix (characteristic matrix) method. The independent reference for the renderers' thin-film interference
(the iridescence of yohen tenmoku, docs/materials/yohen.md), as tools/slab.py is for their media.

    python3 -I tools/tmm.py check                                    # the closed-form checks (tests/yohen/ runs them)
    python3 -I tools/tmm.py strip --film 2.5 --sub 1.6 --dmax 800 --angles 0,30,60 --out out/yohen/strip.png

The stack: an incidence medium of real index n0 (air, 1), layers j = 1..m of complex index N_j = n_j + i k_j and
thickness d_j (nm), then a semi-infinite substrate N_s. All interfaces flat and parallel; light coherent inside
the layers (each layer much thinner than the light's coherence length, ~1 um for daylight), incoherent in the
substrate (it does not come back: a black glaze absorbs what enters it). Polarisation s and p; unpolarised is
their mean.

Sign convention: a wave exp(i (k z - w t)), so an absorbing medium has k > 0 and Im(N cos theta) >= 0 in every
layer (the forward wave decays). Two independent methods are coded: the 2x2 characteristic matrix (Abeles,
Born & Wolf 1.6) and Rouard's recursion of Fresnel coefficients; check() requires they agree.

Spectra: wavelengths in nm on camera.LAM (360..830, 1 nm), pbrt's grid; the colour of a reflectance is computed
under an illuminant with the CIE 1931 2-degree observer read out of pbrt (camera.Spectra).
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera  # noqa: E402


# --- optics ---------------------------------------------------------------------------------------
def _cos(N, n0, cos0):
    """cos of the refraction angle in a medium of complex index N, from Snell's law n0 sin0 = N sin; the branch
    with Im(N cos) >= 0 (forward wave decays), and Re(N cos) >= 0 when lossless."""
    N = np.asarray(N, complex)
    sin0 = np.sqrt(1.0 - cos0 * cos0 + 0j)
    c = np.sqrt(1.0 - (n0 * sin0 / N) ** 2)
    q = N * c
    flip = (q.imag < 0) | ((np.abs(q.imag) < 1e-12) & (q.real < 0))
    return np.where(flip, -c, c)


def _admittance(N, c, pol):
    """The tilted admittance of a medium: N cos for s, N / cos for p (in units of free space's)."""
    return N * c if pol == "s" else N / c


def stack_rt(lam, layers, n_sub, n0=1.0, cos0=1.0, pol="s"):
    """The amplitude reflection coefficient r and the power transmittance T into the substrate, by the
    characteristic-matrix method (r in the admittance convention: its sign for p is opposite to some texts').

    lam: wavelengths (nm), array. layers: [(N, d_nm), ...] top to bottom, N a complex scalar or an array over lam.
    n_sub: the substrate's complex index (scalar or array). Returns complex arrays over lam.
    """
    lam = np.asarray(lam, float)
    one = np.ones_like(lam, complex)
    y0 = _admittance(n0 * one, cos0 * one, pol)
    Ns = np.asarray(n_sub, complex) * one
    cs = _cos(Ns, n0, cos0)
    ys = _admittance(Ns, cs, pol)
    M11, M12, M21, M22 = one.copy(), 0 * one, 0 * one, one.copy()
    for N, d in layers:
        N = np.asarray(N, complex) * one
        c = _cos(N, n0, cos0)
        y = _admittance(N, c, pol)
        delta = 2 * np.pi * N * c * d / lam
        a, b = np.cos(delta), np.sin(delta)
        # -i: our N = n + ik convention (Macleod's matrix has +i for N = n - ik)
        L11, L12, L21, L22 = a, -1j * b / y, -1j * y * b, a
        M11, M12, M21, M22 = (M11 * L11 + M12 * L21, M11 * L12 + M12 * L22,
                              M21 * L11 + M22 * L21, M21 * L12 + M22 * L22)
    B = M11 + M12 * ys
    C = M21 + M22 * ys
    r = (y0 * B - C) / (y0 * B + C)
    # power transmitted into the substrate (Macleod, Thin-Film Optical Filters, eq. 2.57)
    T = 4 * y0.real * ys.real / np.abs(y0 * B + C) ** 2
    return r, T


def stack_r_rouard(lam, layers, n_sub, n0=1.0, cos0=1.0, pol="s"):
    """The same reflection coefficient by Rouard's recursion (from the substrate up); an independent check."""
    lam = np.asarray(lam, float)
    one = np.ones_like(lam, complex)
    media = [n0 * one] + [np.asarray(N, complex) * one for N, _ in layers] + [np.asarray(n_sub, complex) * one]
    cos = [_cos(N, n0, cos0) for N in media]
    y = [_admittance(N, c, pol) for N, c in zip(media, cos)]
    r = (y[-2] - y[-1]) / (y[-2] + y[-1])
    for j in range(len(layers), 0, -1):
        N, d = media[j], layers[j - 1][1]
        beta = 2 * np.pi * N * cos[j] * d / lam
        e = np.exp(2j * beta)
        rij = (y[j - 1] - y[j]) / (y[j - 1] + y[j])
        r = (rij + r * e) / (1 + rij * r * e)
    return r


def reflectance(lam, layers, n_sub, n0=1.0, cos0=1.0, pol="u"):
    """Power reflectance |r|^2; pol 's', 'p', or 'u' (unpolarised, the mean)."""
    if pol == "u":
        return 0.5 * (reflectance(lam, layers, n_sub, n0, cos0, "s") + reflectance(lam, layers, n_sub, n0, cos0, "p"))
    r, _ = stack_rt(lam, layers, n_sub, n0, cos0, pol)
    return np.abs(r) ** 2


def transmittance(lam, layers, n_sub, n0=1.0, cos0=1.0, pol="s"):
    """Power transmittance into the substrate (the energy check: R + T = 1 for lossless layers)."""
    return stack_rt(lam, layers, n_sub, n0, cos0, pol)[1]


def fresnel_bare(N, n0, cos0, pol):
    """Fresnel reflectance of a single interface, written out (not through the stack code)."""
    N = np.asarray(N, complex)
    c = _cos(N, n0, cos0)
    if pol == "s":
        r = (n0 * cos0 - N * c) / (n0 * cos0 + N * c)
    else:
        r = (N * cos0 - n0 * c) / (N * cos0 + n0 * c)
    return np.abs(r) ** 2


# --- colour -----------------------------------------------------------------------------------------
_S = None


def spectra():
    global _S
    if _S is None:
        _S = camera.Spectra("canon_eos_5d_mkiv")
    return _S


def xyz_of(R, illum=None):
    """XYZ of a reflectance spectrum R (on camera.LAM; last axis) under an illuminant, Y of the white = 1."""
    S = spectra()
    E = S.d65 if illum is None else illum
    w = S.cmf * E
    return np.tensordot(R, w, axes=([-1], [1])) / w[1].sum()


def rgb709_of(R, illum=None):
    """Linear Rec.709 RGB (white-balanced to the illuminant: a perfect reflector is 1, 1, 1)."""
    S = spectra()
    E = S.d65 if illum is None else illum
    white = (S.cmf * E).sum(1) / (S.cmf[1] * E).sum()
    return xyz_of(R, E) @ camera.rgb709_from_xyz(white).T


# --- checks -----------------------------------------------------------------------------------------
def check(verbose=True):
    lam = camera.LAM
    rng = np.random.default_rng(1)
    worst = {}

    def note(name, err):
        worst[name] = max(worst.get(name, 0.0), float(np.max(np.abs(err))))

    for cos0 in (1.0, 0.8, 0.5, 0.15):
        for pol in "sp":
            # 1. no layer, and a layer of zero thickness: the bare interface
            for Ns in (1.5 + 0j, 1.6 + 0.02j, 3.0 + 0.5j):
                Rb = fresnel_bare(Ns, 1.0, cos0, pol)
                note("bare", reflectance(lam, [], Ns, 1.0, cos0, pol) - Rb)
                note("zero-thickness", reflectance(lam, [(2.3 + 0.1j, 0.0)], Ns, 1.0, cos0, pol) - Rb)
            # 2. a layer of the substrate's own index changes nothing
            note("same-index", reflectance(lam, [(1.6 + 0.02j, 137.0)], 1.6 + 0.02j, 1.0, cos0, pol)
                 - fresnel_bare(1.6 + 0.02j, 1.0, cos0, pol))
            # 3. lossless stacks conserve energy, R + T = 1
            for _ in range(5):
                layers = [(rng.uniform(1.3, 3.0) + 0j, rng.uniform(10, 600)) for _ in range(rng.integers(1, 4))]
                Ns = rng.uniform(1.3, 2.0)
                note("R+T=1", reflectance(lam, layers, Ns, 1.0, cos0, pol)
                     + transmittance(lam, layers, Ns, 1.0, cos0, pol) - 1)
            # 4. the matrix method and Rouard's recursion agree, absorbing layers included
            for _ in range(5):
                layers = [(rng.uniform(1.3, 3.0) + 1j * rng.uniform(0, 1.0), rng.uniform(5, 400))
                          for _ in range(rng.integers(1, 4))]
                Ns = rng.uniform(1.4, 2.0) + 1j * rng.uniform(0, 0.3)
                r1, _ = stack_rt(lam, layers, Ns, 1.0, cos0, pol)
                note("matrix=Rouard", r1 - stack_r_rouard(lam, layers, Ns, 1.0, cos0, pol))
    # 5. normal incidence, one lossless layer: quarter-wave and half-wave (closed forms)
    n1, ns, l0 = 2.2, 1.6, 550.0
    i = int(np.argmin(np.abs(lam - l0)))
    Rq = reflectance(lam, [(n1, l0 / (4 * n1))], ns, 1.0, 1.0, "s")[i]
    note("quarter-wave", Rq - ((ns - n1 ** 2) / (ns + n1 ** 2)) ** 2)
    Rh = reflectance(lam, [(n1, l0 / (2 * n1))], ns, 1.0, 1.0, "s")[i]
    note("half-wave", Rh - ((1 - ns) / (1 + ns)) ** 2)
    # 6. the Airy formula for one absorbing layer, written out
    N1, Ns, d, cos0 = 2.8 + 0.4j, 1.6 + 0.01j, 120.0, 0.7
    for pol in "sp":
        c1, cs = _cos(N1, 1.0, cos0), _cos(Ns, 1.0, cos0)
        if pol == "s":
            r01 = (cos0 - N1 * c1) / (cos0 + N1 * c1)
            r12 = (N1 * c1 - Ns * cs) / (N1 * c1 + Ns * cs)
        else:
            r01 = (N1 * cos0 - c1) / (N1 * cos0 + c1)
            r12 = (Ns * c1 - N1 * cs) / (Ns * c1 + N1 * cs)
        e = np.exp(2j * 2 * np.pi * N1 * c1 * d / lam)
        R_airy = np.abs((r01 + r12 * e) / (1 + r01 * r12 * e)) ** 2
        note("Airy", reflectance(lam, [(N1, d)], Ns, 1.0, cos0, pol) - R_airy)
    # 7. colour: a perfect reflector is white (1, 1, 1); a flat 0.5 is grey 0.5
    note("white", rgb709_of(np.ones_like(lam)) - 1)
    note("grey", rgb709_of(0.5 * np.ones_like(lam)) - 0.5)

    ok = all(v < 1e-9 for v in worst.values())
    if verbose:
        for k, v in worst.items():
            print(f"  {k:16s} max |err| {v:.2e}")
        print("tmm check:", "OK" if ok else "FAILED")
    return ok


# --- the strip: colour against thickness, at several angles ---------------------------------------------
def strip(film, sub, dmax, angles, out, width=800, band=60, gain=None):
    """Rows: viewing angles; columns: film thickness 0..dmax nm. Each cell is the specular reflectance of
    air / film / substrate under D65, as sRGB. Exposure: the brightest cell to 1 unless gain is given."""
    from PIL import Image
    lam = camera.LAM
    d = np.linspace(0, dmax, width)
    rows = []
    for a in angles:
        cos0 = np.cos(np.radians(a))
        R = np.array([reflectance(lam, [(film, x)], sub, 1.0, cos0) for x in d])
        rows.append(rgb709_of(R))
    rgb = np.array(rows)
    g = gain if gain is not None else 1.0 / rgb.max()
    img = camera.srgb_encode(np.clip(rgb * g, 0, 1))
    img = np.repeat((img * 255 + 0.5).astype(np.uint8), band, axis=0)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    Image.fromarray(img).save(out)
    return rgb, g


def _cx(s):
    return complex(s.replace("i", "j")) if any(c in s for c in "ij") else complex(float(s), 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    s = sub.add_parser("strip")
    s.add_argument("--film", default="2.5", help="the film's complex index, e.g. 2.5 or 2.9+0.3j")
    s.add_argument("--sub", default="1.6", help="the substrate's complex index")
    s.add_argument("--dmax", type=float, default=800.0)
    s.add_argument("--angles", default="0,30,60")
    s.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "check":
        sys.exit(0 if check() else 1)
    angles = [float(x) for x in a.angles.split(",")]
    rgb, g = strip(_cx(a.film), _cx(a.sub), a.dmax, angles, a.out)
    print(f"wrote {a.out}: gain {g:.3f}, max linear {rgb.max():.4f}")


if __name__ == "__main__":
    main()
