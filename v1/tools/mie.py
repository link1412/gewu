"""Mie scattering by spheres in a glass, and what a population of them does to light passing through: the scattering
and absorption coefficients and the phase function a glaze's medium is built from (docs/mie.md; the medium then
goes to tools/slab.py and the renderers).

    python3 -I tools/mie.py check        # published reference values and limits (tests/mie/ runs them too)
    python3 -I tools/mie.py example      # the illustration in docs/mie.md
    python3 -I tools/mie.py medium --lam 450,550,650 --n-host 1.52 --n-particle 1.54 --d 81 --phi 0.2

One sphere: Bohren & Huffman's BHMIE (1983, Appendix A), vectorised over the size parameter, with two changes
(each found by a failing reference value, see _logderiv and _coefficients). The logarithmic derivative D_n(mx) by
downward recurrence from n = max(nstop, |mx|) + 16 as in BHMIE, but started from the exact value there (Lentz's
continued fraction) instead of 0; psi_n and chi_n by upward recurrence, except below x = 2, where psi_n comes from
the downward ratios and a_n, b_n from differences of logarithmic derivatives, which do not cancel. The number of
terms nstop is Wiscombe's (1980, Appl. Opt. 19, 1505, eq. 1) above x = 8 and BHMIE's x + 4 x^(1/3) + 2 below.
Conventions are Bohren & Huffman's: time dependence exp(-i omega t), so an absorbing
sphere has m = n + ik with k >= 0 (MIEV0 and miepython write n - ik: their amplitudes are our conjugates); the
size parameter is x = 2 pi a n_host / lambda; Q_back = 4 |S1(180 deg)|^2 / x^2 (BHMIE's QBACK, the radar
backscattering efficiency); g is the mean cosine of the scattering angle.

A population: number density from the volume fraction and the size distribution (number weights); the
differential cross-section (|S1|^2 + |S2|^2) / (2 k^2) times the hard-sphere Percus-Yevick structure factor S(q),
q = 2 k sin(theta / 2), integrated over the sphere (the interference approximation, as in Magkiriadou et al. 2014,
PRE 90, 062302, eq. 3, and the intensity-based mean free path of Vynck et al. 2023, RMP 95, 045003 [arXiv
2106.13892], eq. 111). The integral is Gauss-Legendre in mu = cos(theta): S1 and S2 are polynomials of degree
<= nstop in mu, and S(q) is an entire function of q^2 = 2 k^2 (1 - mu), so a modest node count makes it exact to
rounding. A polydisperse population takes one monodisperse S(q) at one diameter (the number-weighted mean unless
given) [A]. Absorption by the particles is the independent one (S(q) does not touch it) [A]; the host must not
absorb here (its absorption is the glaze's own and adds on outside).

Units: wavelengths and diameters in nm; coefficients in 1/mm (the unit tools/slab.py takes).
"""

import argparse
import json
import math
import sys
import time

import numpy as np

CHUNK = 4_000_000            # elements per work array (complex): about 64 MB


# --- one sphere -----------------------------------------------------------------------------------
def nstop(x):
    """The number of terms: Wiscombe (1980) eq. 1 above x = 8 (x + 4.05 x^(1/3) + 2 up to 4200, x + 4 x^(1/3) + 2
    beyond); below 8 BHMIE's x + 4 x^(1/3) + 2, one more than Wiscombe's, so that even x = 1e-4 gets two terms."""
    x = np.asarray(x, float)
    c = np.where((x > 8) & (x < 4200), 4.05, 4.0)
    return (x + c * np.cbrt(x) + 2.0).astype(np.int64)


def lentz_D(n, z, tol=1e-17, itmax=100_000):
    """The logarithmic derivative D_n(z) = psi_n'(z)/psi_n(z) at one order n, for an array z, by Lentz's (1976,
    Appl. Opt. 15, 668) continued fraction in the modified form (Thompson & Barnett 1986): with r_n =
    psi_{n-1}/psi_n, r_n = (2n+1)/z - 1/r_{n+1}, so r_n = b_0 - 1/(b_1 - 1/(b_2 - ...)), b_k = (2n+1+2k)/z, and
    D_n = r_n - n/z. Converges in a few tens of terms for n > |z|, where it is used."""
    z = np.asarray(z, complex)
    tiny = 1e-300
    f = (2 * n + 1) / z
    C = f.copy()
    Dl = np.zeros_like(z)
    done = np.zeros(z.shape, bool)
    for k in range(1, itmax):
        b = (2 * n + 1 + 2 * k) / z
        Dl = b - Dl
        Dl = np.where(Dl == 0, tiny, Dl)
        C = b - 1.0 / C
        C = np.where(C == 0, tiny, C)
        Dl = 1.0 / Dl
        delta = np.where(done, 1.0, C * Dl)
        f = f * delta
        done |= np.abs(delta - 1) < tol
        if done.all():
            return f - n / z
    raise RuntimeError("lentz_D: no convergence")


def _logderiv(z, N):
    """D_n(z), n = 0..N, shape (N + 1, len(z)), by downward recurrence D_{n-1} = n/z - 1/(D_n + n/z) (BHMIE) from
    n = max(N, |z|) + 16, started from the exact value there (lentz_D) rather than BHMIE's D = 0: with little
    absorption the zero start's error is only damped above n = |z|, and at m = 1.33 + 1e-5 i, x = 100 it left
    2e-5 in Q_sca (MIEV0 case 10)."""
    start = max(N, int(np.abs(z).max())) + 16
    D = np.zeros((N + 1, len(z)), complex)
    d = lentz_D(start, z)
    for n in range(start, 0, -1):
        d = n / z - 1.0 / (d + n / z)
        if n - 1 <= N:
            D[n - 1] = d
    return D


NQ = (2, 4, 64)              # Gauss-Legendre nodes for the S(q) integral: NQ[0] nstop + NQ[1] k d + NQ[2]
X_SMALL = 2.0                # below this, psi_n by the product form and a_n, b_n by differences of D (see below)


def _coefficients(m, x):
    """a_n, b_n for n = 1..N (N the largest nstop; zero beyond each row's own), for 1-D arrays m (complex) and x.
    Returns (a, b) of shape (K, N) and the row-wise nstop.

    x >= X_SMALL: BHMIE's a_n = ((D_n(mx)/m + n/x) psi_n - psi_{n-1}) / ((D_n(mx)/m + n/x) xi_n - xi_{n-1}),
    psi_n and chi_n by upward recurrence, xi_n = psi_n - i chi_n. Below, the numerator is a difference of nearly
    equal numbers (at x = 1e-4 it kept 8 digits, 6 at m = 1.02), so with psi_{n-1} = psi_n (D_n(x) + n/x) it is
    written psi_n (D_n(mx)/m - D_n(x)), whose two terms do not cancel; likewise the denominator xi_n (D_n(mx)/m -
    G_n), G_n = xi_{n-1}/xi_n - n/x; and psi_n = psi_{n-1} / (D_n(x) + n/x) (no zero of psi_n below x = pi), since
    the upward recurrence for psi cancels there too."""
    K = len(x)
    ns = nstop(x)
    N = int(ns.max())
    Dm = _logderiv(m * x, N)
    small = x < X_SMALL
    Dx = _logderiv(x.astype(complex), N).real if small.any() else None
    a = np.zeros((K, N), complex)
    b = np.zeros((K, N), complex)
    psi0, psi1 = np.cos(x), np.sin(x)                       # psi_{-1}, psi_0
    chi0, chi1 = -np.sin(x), np.cos(x)                      # chi_{-1}, chi_0
    xi1 = psi1 - 1j * chi1
    with np.errstate(all="ignore"):
        for n in range(1, N + 1):
            act = n <= ns
            psi = (2 * n - 1) * psi1 / x - psi0
            if Dx is not None:
                psi = np.where(small, psi1 / (Dx[n] + n / x), psi)
            chi = (2 * n - 1) * chi1 / x - chi0
            xi = psi - 1j * chi
            ta = Dm[n] / m + n / x
            tb = m * Dm[n] + n / x
            an = (ta * psi - psi1) / (ta * xi - xi1)
            bn = (tb * psi - psi1) / (tb * xi - xi1)
            if Dx is not None:
                G = xi1 / xi - n / x
                r = psi / xi
                an = np.where(small, r * (Dm[n] / m - Dx[n]) / (Dm[n] / m - G), an)
                bn = np.where(small, r * (m * Dm[n] - Dx[n]) / (m * Dm[n] - G), bn)
            a[:, n - 1] = np.where(act, an, 0.0)
            b[:, n - 1] = np.where(act, bn, 0.0)
            # rows past their nstop keep their last values (chi would overflow for small x)
            psi0, psi1 = np.where(act, psi1, psi0), np.where(act, psi, psi1)
            chi0, chi1 = np.where(act, chi1, chi0), np.where(act, chi, chi1)
            xi1 = psi1 - 1j * chi1
    return a, b, ns


def _efficiencies(a, b, x):
    """Q_ext, Q_sca, Q_back, g from the coefficients (BHMIE's sums; g as in Bohren & Huffman eq. 4.62)."""
    N = a.shape[1]
    n = np.arange(1, N + 1, dtype=float)
    f = 2 * n + 1
    x2 = x * x
    qext = 2.0 / x2 * (f * (a + b).real).sum(1)
    qsca = 2.0 / x2 * (f * (np.abs(a) ** 2 + np.abs(b) ** 2)).sum(1)
    sgn = np.where(np.arange(1, N + 1) % 2 == 1, -1.0, 1.0)
    qback = np.abs((f * sgn * (a - b)).sum(1)) ** 2 / x2
    t1 = (n[:-1] * (n[:-1] + 2) / (n[:-1] + 1) * (a[:, :-1] * a[:, 1:].conj() + b[:, :-1] * b[:, 1:].conj()).real).sum(1)
    t2 = (f / (n * (n + 1)) * (a * b.conj()).real).sum(1)
    with np.errstate(all="ignore"):
        g = np.where(qsca > 0, 4.0 / x2 * (t1 + t2) / qsca, 0.0)
    return qext, qsca, qback, g


def _chunks(x):
    """Index arrays into x (sorted by x, so that rows in a chunk need similar numbers of terms), each small enough
    that a (rows x terms) complex array stays under CHUNK elements."""
    order = np.argsort(x, kind="stable")
    ns = nstop(x[order])
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and (j + 1 - i) * (ns[j] + 1) <= CHUNK:
            j += 1
        yield order[i:j]
        i = j


def _prep(m, x):
    m = np.asarray(m, complex)
    x = np.asarray(x, float)
    shape = np.broadcast_shapes(m.shape, x.shape)
    m = np.broadcast_to(m, shape).ravel()
    x = np.broadcast_to(x, shape).ravel()
    if np.any(m.imag < 0):
        raise ValueError("mie: Im(m) < 0. The convention here is Bohren & Huffman's, n + ik with k >= 0 absorbing")
    if np.any(x <= 0) or not np.all(np.isfinite(x)):
        raise ValueError("mie: x must be positive and finite")
    return m, x, shape


def mie(m, x):
    """Q_ext, Q_sca, Q_back, g for homogeneous spheres of relative index m (real or complex, m < 1 allowed) and size
    parameter x = 2 pi a n_host / lambda. m and x broadcast; each result has their broadcast shape."""
    m, x, shape = _prep(m, x)
    out = np.zeros((4, len(x)))
    for i in _chunks(x):
        a, b, _ = _coefficients(m[i], x[i])
        out[:, i] = _efficiencies(a, b, x[i])
    return tuple(o.reshape(shape) for o in out)


def pitau(mu, N):
    """The angular functions pi_n(mu), tau_n(mu), n = 1..N, shape (N, len(mu)) (Bohren & Huffman eq. 4.47)."""
    mu = np.asarray(mu, float)
    pi = np.zeros((N, len(mu)))
    tau = np.zeros((N, len(mu)))
    p0, p1 = np.zeros_like(mu), np.ones_like(mu)            # pi_0, pi_1
    for n in range(1, N + 1):
        pi[n - 1] = p1
        tau[n - 1] = n * mu * p1 - (n + 1) * p0
        p0, p1 = p1, ((2 * n + 1) * mu * p1 - (n + 1) * p0) / n
    return pi, tau


def _amp(a, b, pi, tau):
    """S1, S2 of shape (K, len(mu)) from coefficients (K, N) and angular functions (N, len(mu)), by matrix products."""
    N = a.shape[1]
    n = np.arange(1, N + 1, dtype=float)
    c = ((2 * n + 1) / (n * (n + 1)))[:, None]
    P, T = c * pi[:N], c * tau[:N]
    return a @ P + b @ T, a @ T + b @ P


def amplitudes(m, x, mu):
    """The amplitude functions S1(mu), S2(mu) (Bohren & Huffman eq. 4.74), mu = cos(scattering angle). m and x
    broadcast to some shape; the result has that shape plus len(mu)."""
    m, x, shape = _prep(m, x)
    mu = np.atleast_1d(np.asarray(mu, float))
    S1 = np.zeros((len(x), len(mu)), complex)
    S2 = np.zeros_like(S1)
    for i in _chunks(x):
        a, b, _ = _coefficients(m[i], x[i])
        pi, tau = pitau(mu, a.shape[1])
        S1[i], S2[i] = _amp(a, b, pi, tau)
    return S1.reshape(shape + (len(mu),)), S2.reshape(shape + (len(mu),))


# --- hard-sphere structure ------------------------------------------------------------------------
def _py_abc(phi):
    """The Percus-Yevick direct correlation function of hard spheres, c(r) = -(alpha + beta s + gamma s^3) for
    s = r/d < 1 and 0 beyond (Wertheim 1963, PRL 10, 321; Thiele 1963, J. Chem. Phys. 39, 474)."""
    alpha = (1 + 2 * phi) ** 2 / (1 - phi) ** 4
    beta = -6 * phi * (1 + phi / 2) ** 2 / (1 - phi) ** 4
    gamma = phi * alpha / 2
    return alpha, beta, gamma


def py_structure(qd, phi):
    """The Percus-Yevick structure factor of hard spheres of diameter d at volume fraction phi, as a function of
    q d: S = 1 / (1 - rho c(q)), rho c(q) = 24 phi int_0^1 c(s) s^2 sin(Qs)/(Qs) ds, in closed form (Ashcroft &
    Lekner 1966, Phys. Rev. 145, 83; written out as in Kinning & Thomas 1984, Macromolecules 17, 1712, eqs. 7-8).
    Below Q = 1 the closed form loses digits to cancellation (it divides by Q^6), so there the integral's Taylor
    series is used: rho c = -24 phi sum_k (-Q^2)^k/(2k+1)! [alpha/(2k+3) + beta/(2k+4) + gamma/(2k+6)]."""
    Q = np.asarray(qd, float)
    if not 0 <= phi < 1:
        raise ValueError("py_structure: phi must be in [0, 1)")
    al, be, ga = _py_abc(phi)
    small = Q < 1.0
    Qs = np.where(small, Q, 0.0)
    ser = np.zeros_like(Q)
    term = np.ones_like(Q)
    for k in range(14):                                      # Q < 1: the k = 13 term is below 1e-30
        if k:
            term = term * (-Qs * Qs) / ((2 * k) * (2 * k + 1))
        ser += term * (al / (2 * k + 3) + be / (2 * k + 4) + ga / (2 * k + 6))
    Ql = np.where(small, 1.0, Q)
    s, c = np.sin(Ql), np.cos(Ql)
    G = (al * (s - Ql * c) / Ql ** 2
         + be * (2 * Ql * s + (2 - Ql ** 2) * c - 2) / Ql ** 3
         + ga * (-Ql ** 4 * c + 4 * ((3 * Ql ** 2 - 6) * c + (Ql ** 3 - 6 * Ql) * s + 6)) / Ql ** 5)
    rc = np.where(small, -24 * phi * ser, -24 * phi * G / Ql)
    return 1.0 / (1.0 - rc)


# --- a population in a glass ----------------------------------------------------------------------
def maxwell_garnett(n_host, n_particle, phi):
    """The Maxwell-Garnett effective index of spheres at volume fraction phi in a host (real part)."""
    eh, ep = np.asarray(n_host, complex) ** 2, np.asarray(n_particle, complex) ** 2
    beta = (ep - eh) / (ep + 2 * eh)
    return np.sqrt(eh * (1 + 2 * phi * beta) / (1 - phi * beta)).real


def lognormal(d_median, sigma_g, n=50, span=4.0):
    """A log-normal number distribution of diameters (median d_median, geometric standard deviation sigma_g > 1),
    sampled at n diameters evenly spaced in log over +-span sigma: (sizes, number weights summing to 1)."""
    s = math.log(sigma_g)
    t = np.linspace(-span, span, n)
    w = np.exp(-0.5 * t * t)
    return d_median * np.exp(s * t), w / w.sum()


def medium(lam_nm, n_host, n_particle, d_nm, phi, structure=True, sizes=None, weights=None, phase_deg=None,
           effective=None):
    """The medium made by spheres at volume fraction phi in a non-absorbing host.

    lam_nm: vacuum wavelengths (nm). n_host (real) and n_particle (real or n + ik) scalars or arrays over lam_nm.
    d_nm: the diameter (nm); with sizes (nm) and weights (number fractions), the hard-sphere diameter for S(q)
    (None: the number-weighted mean of sizes) [A]. structure: multiply the differential cross-section by the
    Percus-Yevick S(q). phase_deg: scattering angles (degrees) at which to tabulate the phase function.
    effective: None, the wave number and the contrast both in the host (exact Mie for a lone sphere; in the Born
    limit the contrast against the host is the right one, as in small-angle scattering); "k", the wave number in
    the Maxwell-Garnett medium and the contrast against the host (Vynck et al. 2023 eq. 110-111) [A: the T-matrix
    at another wave number is approximated by Mie at x = k_eff a]; "km", both against the Maxwell-Garnett medium
    (Magkiriadou et al. 2014).

    Returns a dict over lam_nm: sigma_s, sigma_a (1/mm), g; sigma_s_indep, g_indep (without S(q)); albedo;
    number_density (1/um^3); S0 (= S(q -> 0)); d_structure_nm; n_k (the index the wave number is taken in); and
    with phase_deg, theta_deg and phase (1/sr, normalised to 1 over the sphere, one row per wavelength)."""
    lam = np.atleast_1d(np.asarray(lam_nm, float))
    L = len(lam)
    nh = np.asarray(n_host)
    if np.iscomplexobj(nh) and np.any(nh.imag != 0):
        raise ValueError("medium: the host must not absorb here (add its absorption to sigma_a outside)")
    nh = np.broadcast_to(nh.real.astype(float), lam.shape)
    npt = np.broadcast_to(np.asarray(n_particle, complex), lam.shape)
    if sizes is None:
        if d_nm is None:
            raise ValueError("medium: give d_nm, or sizes and weights")
        sizes, weights = np.array([float(d_nm)]), np.array([1.0])
    else:
        sizes = np.asarray(sizes, float)
        weights = np.ones_like(sizes) if weights is None else np.asarray(weights, float)
        if sizes.shape != weights.shape or np.any(weights < 0) or weights.sum() <= 0:
            raise ValueError("medium: sizes and weights must match, weights >= 0")
        weights = weights / weights.sum()
    d_s = float(np.sum(weights * sizes)) if d_nm is None else float(d_nm)
    if not 0 < phi <= 0.64:
        raise ValueError("medium: phi must be in (0, 0.64] (random close packing; PY is a fluid theory, see docs/mie.md)")
    vol = math.pi / 6 * float(np.sum(weights * sizes ** 3))  # mean volume, nm^3
    rho = phi / vol                                          # 1/nm^3
    if effective is None:
        nk, nc = nh, nh
    elif effective in ("k", "km"):
        nk = maxwell_garnett(nh, npt, phi)
        nc = nh if effective == "k" else nk
    else:
        raise ValueError("medium: effective is None, 'k' or 'km'")
    k = 2 * np.pi * nk / lam                                 # 1/nm
    m = npt / nc
    # rows: (wavelength, size)
    li, si = np.meshgrid(np.arange(L), np.arange(len(sizes)), indexing="ij")
    li, si = li.ravel(), si.ravel()
    a_r = sizes[si] / 2
    x = k[li] * a_r
    mr = m[li]
    wr = weights[si]
    area = np.pi * a_r ** 2
    Csca = np.zeros(len(x)); Cext = np.zeros(len(x)); gC = np.zeros(len(x))
    Cs_S = np.zeros(len(x)); gC_S = np.zeros(len(x))
    want_phase = phase_deg is not None
    if want_phase:
        th = np.atleast_1d(np.asarray(phase_deg, float))
        mu_p = np.cos(np.radians(th))
        dsig = np.zeros((len(x), len(th)))                   # w * dC/dOmega (times S(q)), nm^2/sr
    for i in _chunks(x):
        a, b, _ = _coefficients(mr[i], x[i])
        qe, qs, _, g = _efficiencies(a, b, x[i])
        Csca[i] = qs * area[i]; Cext[i] = qe * area[i]; gC[i] = g * qs * area[i]
        kk = k[li[i]][:, None]
        if structure:
            # Gauss-Legendre in mu: exact for the polynomial |S|^2 (degree 2N) times the smooth S(q(mu))
            N = a.shape[1]
            kd = float((k[li[i]] * d_s).max())
            nq = NQ[0] * N + int(NQ[1] * kd) + NQ[2]
            mu, wq = np.polynomial.legendre.leggauss(nq)
            pi, tau = pitau(mu, N)
            S1, S2 = _amp(a, b, pi, tau)
            dC = (np.abs(S1) ** 2 + np.abs(S2) ** 2) / (2 * kk * kk)     # nm^2/sr
            Sq = py_structure(kk * d_s * np.sqrt(2 * (1 - mu))[None, :], phi)
            Cs_S[i] = 2 * np.pi * (dC * Sq * wq).sum(1)
            gC_S[i] = 2 * np.pi * (dC * Sq * mu * wq).sum(1)
        if want_phase:
            pi, tau = pitau(mu_p, a.shape[1])
            S1, S2 = _amp(a, b, pi, tau)
            dC = (np.abs(S1) ** 2 + np.abs(S2) ** 2) / (2 * kk * kk)
            if structure:
                dC = dC * py_structure(kk * d_s * np.sqrt(2 * (1 - mu_p))[None, :], phi)
            dsig[i] = wr[i][:, None] * dC
    def per_lam(v):
        return np.bincount(li, weights=wr * v, minlength=L)
    cs, ce, gc = per_lam(Csca), per_lam(Cext), per_lam(gC)
    out = {"lam_nm": lam, "sigma_s_indep": rho * cs * 1e6, "g_indep": gc / cs,
           "sigma_a": rho * (ce - cs) * 1e6, "number_density": rho * 1e9, "S0": float(py_structure(0.0, phi)),
           "d_structure_nm": d_s, "n_k": np.asarray(nk, float)}
    if structure:
        css, gcs = per_lam(Cs_S), per_lam(gC_S)
        out["sigma_s"], out["g"] = rho * css * 1e6, gcs / css
    else:
        out["sigma_s"], out["g"] = out["sigma_s_indep"], out["g_indep"]
    out["albedo"] = out["sigma_s"] / (out["sigma_s"] + out["sigma_a"])
    if want_phase:
        P = np.zeros((L, len(th)))
        np.add.at(P, li, dsig)
        out["theta_deg"] = th
        out["phase"] = P / (out["sigma_s"] / (rho * 1e6))[:, None]
    return out


# --- closed forms and published values, for the checks --------------------------------------------
def rayleigh(m, x):
    """Q_sca = 8/3 x^4 |(m^2-1)/(m^2+2)|^2 and Q_abs = 4 x Im((m^2-1)/(m^2+2)) (Bohren & Huffman eqs. 5.8, 5.11)."""
    p = (m * m - 1) / (m * m + 2)
    return 8.0 / 3.0 * x ** 4 * abs(p) ** 2, 4 * x * p.imag


def rgd(m, x, nq=4000):
    """Rayleigh-Gans-Debye for m -> 1 (van de Hulst 1957, sec. 7.2; Bohren & Huffman sec. 6.1):
    S1 = -i (2/3)(m-1) x^3 G(u), S2 = S1 cos(theta), G(u) = 3 (sin u - u cos u)/u^3, u = 2 x sin(theta/2).
    Q_sca and g by Gauss-Legendre in mu."""
    mu, w = np.polynomial.legendre.leggauss(nq)
    u = 2 * x * np.sqrt((1 - mu) / 2)
    u = np.maximum(u, 1e-8)
    G = np.where(u < 1e-3, 1 - u * u / 10, 3 * (np.sin(u) - u * np.cos(u)) / u ** 3)
    s2 = (2.0 / 3.0 * abs(m - 1) * x ** 3 * G) ** 2 * (1 + mu * mu) / 2
    q = 2 * np.pi * np.sum(s2 * w) / (np.pi * x * x)
    return q, 2 * np.pi * np.sum(s2 * mu * w) / (np.pi * x * x) / q


def adt(m, x):
    """Anomalous diffraction, m real -> 1, x large: Q_ext = 2 - (4/r) sin r + (4/r^2)(1 - cos r), r = 2x(m-1)
    (van de Hulst 1957, sec. 11.22)."""
    r = 2 * x * (m - 1)
    return 2 - 4 / r * math.sin(r) + 4 / r ** 2 * (1 - math.cos(r))


# Bohren & Huffman (1983) Appendix A, the sample run of BHMIE: refmed 1.0, refre 1.55, refim 0, rad 0.525 um,
# wavel 0.6328 um (x = 5.213). Q_sca = Q_ext = 3.10543, Q_back = 2.92534; and per angle, S11 / S11(0),
# POL = -S12/S11, S33/S11, S34/S11 (transcribed from the listing in miepython's tests/test_mie.py,
# test_phase_matrix_bohren; g = 0.63314 from its test_03, which is Draine's BHMIE value, not in the book's listing).
BH_ANGLES = np.array([
    [0, 1.00000e00, 0.00000e00, 1.00000e00, 0.00000e00],
    [9, 7.85390e-01, -4.59811e-03, 9.99400e-01, 3.43261e-02],
    [18, 3.56897e-01, -4.58541e-02, 9.86022e-01, 1.60184e-01],
    [27, 7.66119e-02, -3.64744e-01, 8.43603e-01, 3.94076e-01],
    [36, 3.55355e-02, -5.34997e-01, 6.86967e-01, -4.91787e-01],
    [45, 7.01845e-02, 9.59953e-03, 9.59825e-01, -2.80434e-01],
    [54, 5.74313e-02, 4.77927e-02, 9.85371e-01, 1.63584e-01],
    [63, 2.19660e-02, -4.40604e-01, 6.48043e-01, 6.21216e-01],
    [72, 1.25959e-02, -8.31996e-01, 2.03255e-01, -5.16208e-01],
    [81, 1.73750e-02, 3.41670e-02, 7.95354e-01, -6.05182e-01],
    [90, 1.24601e-02, 2.30462e-01, 9.37497e-01, 2.60742e-01],
    [99, 6.79093e-03, -7.13472e-01, -7.17397e-03, 7.00647e-01],
    [108, 9.54239e-03, -7.56255e-01, -3.94748e-02, -6.53085e-01],
    [117, 8.63419e-03, -2.81215e-01, 5.36251e-01, -7.95835e-01],
    [126, 2.27421e-03, -2.39612e-01, 9.67602e-01, 7.95798e-02],
    [135, 5.43998e-03, -8.50804e-01, 1.87531e-01, -4.90882e-01],
    [144, 1.60243e-02, -7.06334e-01, 4.95254e-01, -5.05781e-01],
    [153, 1.88852e-02, -8.91081e-01, 4.53277e-01, -2.26817e-02],
    [162, 1.95254e-02, -7.83319e-01, -3.91613e-01, 4.82752e-01],
    [171, 3.01676e-02, -1.96194e-01, -9.62069e-01, 1.89556e-01],
    [180, 3.83189e-02, 0.00000e00, -1.00000e00, 0.00000e00]])

# Wiscombe's MIEV0 test cases (NCAR TN-140+STR, 1979, rev. 1996), as transcribed in miepython's tests/test_mie.py
# (written there as n - ik; here n + ik). (case, m, x, {quantity: value}); "back" is S1(180 deg), giving Q_back.
MIEV0 = [
    (5, 0.75, 0.099, {"qsca": 0.000007, "g": 0.001448, "back": 1.81756e-8 - 1.64810e-4j}),
    (6, 0.75, 0.101, {"qsca": 0.000008, "g": 0.001507, "back": 2.04875e-08 - 1.74965e-04j}),
    (7, 0.75, 10.0, {"qsca": 2.232265, "g": 0.896473, "back": -1.07857e00 - 3.60881e-02j}),
    (8, 0.75, 1000.0, {"qsca": 1.997908, "g": 0.844944, "back": 1.70578e01 + 4.84251e02j}),
    (9, 1.33 + 1e-5j, 1.0, {"qsca": 0.093923, "g": 0.184517}),
    (10, 1.33 + 1e-5j, 100.0, {"qsca": 2.096594, "g": 0.868959}),
    (11, 1.33 + 1e-5j, 10000.0, {"qsca": 1.723857, "g": 0.907840}),
    (12, 1.5 + 1j, 0.055, {"qext": 0.101491, "qsca": 0.000011, "g": 0.000491}),
    (13, 1.5 + 1j, 0.056, {"qext": 0.1033467, "qsca": 0.000012, "g": 0.000509}),
    (14, 1.5 + 1j, 1.0, {"qext": 2.336321, "qsca": 0.6634538, "g": 0.192136}),
    (15, 1.5 + 1j, 100.0, {"qext": 2.097502, "qsca": 1.283697, "g": 0.850252}),
    (16, 1.5 + 1j, 10000.0, {"qext": 2.004368, "qsca": 1.236575, "g": 0.846309}),
    (17, 10 + 10j, 1.0, {"qsca": 2.049405, "g": -0.110664}),
    (18, 10 + 10j, 100.0, {"qsca": 1.836785, "g": 0.556215}),
    (19, 10 + 10j, 10000.0, {"qsca": 1.795393, "g": 0.548194}),
    # the older MIEV0 table (miepython test_05_old_...): m = 1.5, 4 to 5 digits
    ("old", 1.5, 10.0, {"qsca": 2.8820, "back": 4.322e00 + 4.868e00j}),
    ("old", 1.5, 100.0, {"qsca": 2.0944, "back": 4.077e01 + 5.175e01j}),
    ("old", 1.5, 1000.0, {"qsca": 2.0139, "qback": 4 * 2.576e06 / 1000.0 ** 2}),
    ("old", 1.5, 5000.0, {"qsca": 2.0086, "qback": 4 * 2.378e08 / 5000.0 ** 2}),
]
# MIEV0 case 14's amplitudes at 0, 30, ..., 180 deg (miepython test_12, MIEV0's normalisation; here conjugated)
MIEV0_S = np.array([
    [0.584080 + 0.190515j, 0.584080 + 0.190515j], [0.565702 + 0.187200j, 0.500161 + 0.145611j],
    [0.517525 + 0.178443j, 0.287964 + 0.041054j], [0.456340 + 0.167167j, 0.0362285 - 0.0618265j],
    [0.400212 + 0.156643j, -0.174875 - 0.122959j], [0.362157 + 0.149391j, -0.305682 - 0.143846j],
    [0.348844 + 0.146829j, -0.348844 - 0.146829j]])


def check():
    """Returns [(name, value, reference, tolerance, kind)]; kind 'abs' or 'rel'. Pass if |value - ref| <= tol (abs)
    or <= tol |ref| (rel)."""
    res = []
    def add(name, v, ref, tol, kind="rel"):
        res.append((name, float(v), float(ref), tol, kind))

    # Bohren & Huffman's sample run
    x = 2 * np.pi * 0.525 / 0.6328
    qe, qs, qb, g = mie(1.55, x)
    add("BH App. A m=1.55 x=5.213 Qext", qe, 3.10543, 6e-6, "abs")
    add("BH App. A m=1.55 x=5.213 Qsca", qs, 3.10543, 6e-6, "abs")
    add("BH App. A m=1.55 x=5.213 Qback", qb, 2.92534, 6e-6, "abs")
    add("BH (Draine) m=1.55 x=5.213 g", g, 0.63314, 6e-6, "abs")
    S1, S2 = amplitudes(1.55, x, np.cos(np.radians(BH_ANGLES[:, 0])))
    s11 = 0.5 * (abs(S2) ** 2 + abs(S1) ** 2)
    s12 = 0.5 * (abs(S2) ** 2 - abs(S1) ** 2)
    s33 = (S1 * S2.conj()).real
    s34 = (S2 * S1.conj()).imag
    cols = [s11 / s11[0], -s12 / s11, s33 / s11, s34 / s11]
    for j, nm in enumerate(["S11/S11(0)", "POL", "S33/S11", "S34/S11"]):
        err = np.abs(cols[j] - BH_ANGLES[:, j + 1])
        k = int(err.argmax())
        # the listing has 6 significant digits: half a unit in the 6th digit of each entry
        tol = 0.5e-5 * np.maximum(np.abs(BH_ANGLES[:, j + 1]), 1e-1)
        add(f"BH App. A {nm}, worst of 21 angles (theta {BH_ANGLES[k, 0]:.0f})", cols[j][k], BH_ANGLES[k, j + 1],
            float(tol[k]) + 1e-7, "abs")

    # Wiscombe's MIEV0 cases
    for case, m, x, ref in MIEV0:
        qe, qs, qb, g = mie(m, x)
        S1b = amplitudes(m, x, [-1.0])[0][0]
        for q, v in ref.items():
            if q == "back":
                val, rv, nm = S1b, v.conjugate(), "S1(180)"
                # printed to 6 significant digits (4 in the old table): 0.6 units in the last digit of |S1|
                tol = 0.6 * 10.0 ** -(5 if case != "old" else 3) * abs(rv)
                add(f"MIEV0 {case} m={m} x={x:g} Re {nm}", val.real, rv.real, tol, "abs")
                add(f"MIEV0 {case} m={m} x={x:g} Im {nm}", val.imag, rv.imag, tol, "abs")
                continue
            val = {"qext": qe, "qsca": qs, "g": g, "qback": qb}[q]
            # the tables print 6 decimals (4 in the old one, 4 significant digits for Q_back there)
            tol = 0.6e-6 if case != "old" else 0.6e-4
            if case == 16 and q in ("qsca", "g"):
                # 0.7e-6 and 1.0e-6 off; the same series in 30-digit arithmetic (mpmath, once, docs/mie.md) gives
                # ours, 1.23657431 and 0.84630996, to 1e-9: taken as MIEV0's rounding
                tol = 1.5e-6
            if q == "qback":
                add(f"MIEV0 {case} m={m} x={x:g} {q}", val, v, 0.6e-3, "rel")
            else:
                add(f"MIEV0 {case} m={m} x={x:g} {q}", val, v, tol, "abs")
    mus = np.cos(np.radians(np.arange(0, 181, 30)))
    S1, S2 = amplitudes(1.5 + 1j, 1.0, mus)
    err = max(np.abs(S1 - MIEV0_S[:, 0].conj()).max(), np.abs(S2 - MIEV0_S[:, 1].conj()).max())
    add("MIEV0 14 m=1.5+1i x=1 S1,S2 at 0..180/30, max |diff|", err, 0.0, 1e-6, "abs")

    # Rayleigh
    for m, x in [(1.5, 1e-3), (1.5, 1e-4), (1.02, 1e-4), (1.0135, 1e-2), (1.5 + 0.1j, 1e-3)]:
        qe, qs, _, _ = mie(m, x)
        rs, ra = rayleigh(complex(m), x)
        add(f"Rayleigh m={m} x={x:g} Qsca", qs, rs, 3 * x * x + 1e-9)
        if complex(m).imag:
            add(f"Rayleigh m={m} x={x:g} Qabs", qe - qs, ra, 3 * x * x + 1e-9)
    # Rayleigh-Gans-Debye, m -> 1 (error of order 2x|m-1|)
    for m, x in [(1.0001, 1.0), (1.0001, 5.0), (1.0001, 20.0), (1.013, 1.5)]:
        _, qs, _, g = mie(m, x)
        rq, rg = rgd(m, x)
        tol = 2 * x * abs(m - 1)
        add(f"RGD m={m} x={x:g} Qsca", qs, rq, tol)
        add(f"RGD m={m} x={x:g} g", g, rg, tol, "abs")
    # anomalous diffraction, m -> 1, x large
    for m, x in [(1.01, 100.0), (1.01, 300.0), (1.01, 1000.0), (1.005, 3000.0)]:
        qe, _, _, _ = mie(m, x)
        add(f"ADT m={m} x={x:g} (rho={2 * x * (m - 1):g}) Qext", qe, adt(m, x), 0.02)
    # extinction paradox, Q_ext -> 2
    for m, x in [(1.5, 3000.0), (1 / 1.52, 3000.0), (1.58 / 1.52, 20000.0)]:
        qe, _, _, _ = mie(m, x)
        add(f"large x m={m:.4f} x={x:g} Qext -> 2", qe, 2.0, 0.02, "abs")
    # energy: Q_ext = Q_sca for real m (m < 1 included), over a log grid of x
    xs = np.logspace(-4, np.log10(3000), 400)
    for m in (1.5, 1 / 1.52, 1.013, 1.58 / 1.52):
        qe, qs, _, _ = mie(m, xs)
        add(f"energy m={m:.4f} max |Qext-Qsca|/Qsca over x 1e-4..3000", np.max(np.abs(qe - qs) / qs), 0.0, 1e-9, "abs")
    # rows of very different x and m in one chunk (frozen recurrences, the small-x branch) = one at a time
    rng = np.random.default_rng(1)
    xs = np.logspace(-4, 3.5, 40)
    ms = rng.choice(np.array([1.013, 1 / 1.52, 1.5 + 0.01j, 1.58 / 1.52, 1.33 + 1e-5j]), len(xs))
    vec = np.array(mie(ms, xs))
    one = np.array([mie(m, x) for m, x in zip(ms, xs)]).T
    add("vectorised over mixed (m, x) = one at a time, max rel diff", np.max(np.abs(vec - one) / np.abs(one)), 0.0,
        1e-12, "abs")
    # the amplitudes against the series: optical theorem, Q_back, and the integrated phase function
    for m, x in [(1.55, 5.213), (1.5 + 1j, 100.0), (1 / 1.52, 300.0)]:
        qe, qs, qb, g = mie(m, x)
        N = int(nstop(x))
        mu, w = np.polynomial.legendre.leggauss(N + 8)
        S1, S2 = amplitudes(m, x, np.concatenate([[1.0, -1.0], mu]))
        add(f"optical theorem m={m:.4g} x={x:g} 4 Re S(0)/x^2 vs Qext", 4 * S1[0].real / x ** 2, qe, 1e-10)
        add(f"m={m:.4g} x={x:g} 4|S1(180)|^2/x^2 vs Qback", 4 * abs(S1[1]) ** 2 / x ** 2, qb, 1e-9)
        p = (abs(S1[2:]) ** 2 + abs(S2[2:]) ** 2) / 2
        add(f"m={m:.4g} x={x:g} GL int of |S|^2 vs Qsca", 2 * np.pi * np.sum(p * w) / (np.pi * x * x), qs, 1e-10)
        add(f"m={m:.4g} x={x:g} GL int of cos |S|^2 vs g", 2 * np.pi * np.sum(p * mu * w) / (np.pi * x * x) / qs, g,
            1e-10, "abs")

    # Percus-Yevick
    for phi in (0.01, 0.1, 0.3, 0.5):
        add(f"PY phi={phi} S(q->0) vs (1-phi)^4/(1+2phi)^2", py_structure(1e-6, phi),
            (1 - phi) ** 4 / (1 + 2 * phi) ** 2, 1e-12)
        add(f"PY phi={phi} S(qd=1e4) -> 1", py_structure(1e4, phi), 1.0, 1e-4, "abs")
        lo, hi = py_structure(1 - 1e-12, phi), py_structure(1 + 1e-12, phi)
        add(f"PY phi={phi} series vs closed form at qd=1", lo, hi, 1e-10)
        # closed form against the direct quadrature of the defining integral
        al, be, ga = _py_abc(phi)
        s, ws = np.polynomial.legendre.leggauss(200)
        s, ws = (s + 1) / 2, ws / 2
        worst = 0.0
        for Q in (2.0, 4.5, 7.0, 13.0, 40.0):
            rc = 24 * phi * np.sum(-(al + be * s + ga * s ** 3) * s * s * np.sin(Q * s) / (Q * s) * ws)
            worst = max(worst, abs(py_structure(Q, phi) - 1 / (1 - rc)))
        add(f"PY phi={phi} closed form vs quadrature of c(r), qd 2..40", worst, 0.0, 1e-11, "abs")
    add("PY phi=1e-6 max |S-1| over qd 0..100", np.abs(py_structure(np.linspace(0, 100, 2001), 1e-6) - 1).max(),
        0.0, 1e-5, "abs")
    # the core condition: the pair correlation h(r) = -1 inside the core (r = d/2), by inverse transform
    # h(r) = 1/(2 pi^2 rho r) int (S - 1) q sin(qr) dq, here with Q = qd, r in units of d, rho d^3 = 6 phi / pi
    for phi in (0.1, 0.3):
        Q = np.linspace(1e-6, 4000, 4_000_001)
        dq = Q[1] - Q[0]
        r = 0.5
        taper = np.exp(-(Q / 1500) ** 2)
        h = np.sum((py_structure(Q, phi) - 1) * Q * np.sin(Q * r) * taper) * dq / (2 * np.pi ** 2 * (6 * phi / np.pi) * r)
        add(f"PY phi={phi} h(r=d/2) = -1 (inverse transform)", h, -1.0, 2e-3, "abs")

    # the population: dilute and tiny particles; the S(q) integral reaches S(0); node count converged
    r = medium([500.0], 1.52, 1.54, 10.0, 1e-4, structure=False)
    qs = mie(1.54 / 1.52, np.pi * 10 * 1.52 / 500)[1]
    add("medium sigma_s = rho C_sca (d=10 nm, phi=1e-4)", r["sigma_s"][0],
        1e-4 / (np.pi / 6 * 1000.0) * qs * np.pi * 25 * 1e6, 1e-12)
    for phi in (0.1, 0.4):
        r = medium([550.0], 1.52, 1.54, 2.0, phi)
        add(f"medium d=2 nm phi={phi}: sigma_s/sigma_s_indep vs S(0)", r["sigma_s"][0] / r["sigma_s_indep"][0],
            r["S0"], 2e-4)
    r = medium([450.0], 1.52, 1.54, 81.0, 0.3)
    r2 = medium([450.0], 1.52, 1.54, 81.0, 0.3, phase_deg=np.linspace(0, 180, 2001))
    th = np.radians(r2["theta_deg"])
    norm = np.trapezoid(r2["phase"][0] * 2 * np.pi * np.sin(th), th)
    add("medium d=81 nm phi=0.3: phase function normalised", norm, 1.0, 1e-5)
    gp = np.trapezoid(r2["phase"][0] * np.cos(th) * 2 * np.pi * np.sin(th), th)
    add("medium d=81 nm phi=0.3: phase function's mean cosine vs g", gp, r["g"][0], 1e-5, "abs")
    global CHUNK, NQ
    for args in [(450.0, 1.52, 1.54, 81.0, 0.4), (450.0, 1.52, 1.58, 4400.0, 0.2), (650.0, 1.52, 1.0, 80000.0, 0.01)]:
        r1 = medium([args[0]], *args[1:])
        save = NQ
        try:
            NQ = (4, 8, 128)
            r2 = medium([args[0]], *args[1:])
        finally:
            NQ = save
        # rounding in S1, S2 at large x (forward |S|^2 ~ x^4 against the side lobes) leaves ~1e-7 at x ~ 1000
        add(f"medium d={args[3]:g} nm phi={args[4]}: S(q) integral, nodes doubled, sigma_s", r1["sigma_s"][0],
            r2["sigma_s"][0], 1e-6)
        add(f"medium d={args[3]:g} nm phi={args[4]}: S(q) integral, nodes doubled, g", r1["g"][0], r2["g"][0], 1e-6,
            "abs")
    save = CHUNK
    try:
        # the same population in tiny chunks, and the angle grid's node count doubled through a larger N
        CHUNK = 50
        r3 = medium([450.0], 1.52, 1.58, 4400.0, 0.2)
    finally:
        CHUNK = save
    r4 = medium([450.0], 1.52, 1.58, 4400.0, 0.2)
    add("medium anorthite phi=0.2: chunking does not change sigma_s", r3["sigma_s"][0], r4["sigma_s"][0], 1e-12)
    return res


def passed(v, ref, tol, kind):
    return abs(v - ref) <= (tol if kind == "abs" else tol * abs(ref))


def example():
    """The illustration in docs/mie.md (all values [A])."""
    lam = [450.0, 550.0, 650.0]
    rows = []
    for d in (35.0, 81.0):
        for st in (False, True):
            r = medium(lam, 1.52, 1.54, d, 0.2, structure=st)
            rows.append((f"droplets d={d:g} nm, dn=0.02, phi=0.2, {'S(q)' if st else 'independent'}", r))
    for st in (False, True):
        r = medium(lam, 1.52, 1.58, 4400.0, 0.01, structure=st)
        rows.append((f"anorthite d=4.4 um, 1.58 in 1.52, phi=0.01, {'S(q)' if st else 'independent'}", r))
    for st in (False, True):
        r = medium(lam, 1.52, 1.0, 80000.0, 0.01, structure=st)
        rows.append((f"bubbles d=80 um, phi=0.01, {'S(q)' if st else 'independent'}", r))
    return rows


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("example")
    c = sub.add_parser("medium")
    c.add_argument("--lam", default="450,550,650", help="nm, comma separated")
    c.add_argument("--n-host", type=float, required=True)
    c.add_argument("--n-particle", type=complex, required=True)
    c.add_argument("--d", type=float, required=True, help="diameter, nm")
    c.add_argument("--phi", type=float, required=True)
    c.add_argument("--independent", action="store_true", help="no structure factor")
    c.add_argument("--effective", choices=["k", "km"], default=None)
    args = ap.parse_args()
    if args.cmd == "check":
        t0 = time.time()
        bad = 0
        for name, v, ref, tol, kind in check():
            ok = passed(v, ref, tol, kind)
            bad += not ok
            print(f"{name:72s} {v: .7g}  ref {ref: .7g}  tol {tol:.1e} {kind}{'' if ok else '  <-- FAIL'}")
        print(f"{'all passed' if not bad else f'{bad} FAILED'} ({time.time() - t0:.1f} s)")
        sys.exit(1 if bad else 0)
    if args.cmd == "example":
        for name, r in example():
            print(name)
            for i, l in enumerate(r["lam_nm"]):
                print(f"   {l:4.0f} nm  sigma_s {r['sigma_s'][i]:.5g} /mm  g {r['g'][i]:.4f}")
        return
    lam = [float(v) for v in args.lam.split(",")]
    r = medium(lam, args.n_host, args.n_particle, args.d, args.phi, structure=not args.independent,
               effective=args.effective)
    print(json.dumps({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in r.items()}, indent=1))


if __name__ == "__main__":
    main()
