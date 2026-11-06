"""How a glaze moves when it melts: thin-film flow on the body of a vessel of revolution, during the firing.

The raw glaze goes on about evenly (dipping); in the kiln it melts into a viscous film that surface tension and
gravity move until it cools stiff. Surface tension pulls it off convex edges (the lip, the foot's edges) towards
concave ones (the crease over the foot ring, the inside corner of the floor); gravity draws it down the walls. On a
Ru washer that is the light band along the lip (the body shows through the thin glaze there) and the deeper green
of the glaze pooled in the creases.

Model: lubrication theory on a curved substrate (Schwartz & Weidner 1995, J. Eng. Math. 29:91): along the profile's
arc length s, with r(s) the radius, e(s) the film's thickness and the outward normal n = (n_r, n_z),
    de/dt + (1/r) d(r q)/ds = 0,      q = e^3 / (3 mu) (-dp/ds - rho g dz/ds),
    p = gamma (kappa - lap(e)) + rho g n_z e,
kappa the substrate's mean curvature (twice: kappa_1 + kappa_2, the profile's and n_r / r; positive where convex,
seen from the glaze), lap(e) = (1/r) d(r de/ds)/ds the surface Laplacian, the last term the film's weight. The
viscosity changes through the firing; only tau = integral dt / mu matters (time and viscosity enter no other way),
the flow's dose, in s/(Pa s). Valid for films thin against the radii they lie on and slopes of the film small;
where the lip's body is thinner than the glaze is thick this is stretched (said so where it is used).

Numerics: nodes uniform in s, fluxes on the faces; the fourth-order term implicit and the mobility e^3 explicit
(one banded solve per step), steps limited to a few per cent change of e. Checks (check): the levelling of a
sinusoid on a flat film against its closed form, a^2 decay rate gamma e0^3 k^4 / (3 mu); volume conservation.

    python3 -I crafts/glazeflow/flow.py check
"""
import argparse
import math
import sys

import numpy as np
from scipy.linalg import solve_banded


def resample(rz, ds):
    """The polyline rz (N x 2: r, z in m) at uniform arc-length spacing ds: (s, rz, tangent, normal) with the
    outward normal the tangent turned clockwise (the profile runs with the body on its left)."""
    rz = np.asarray(rz, float)
    seg = np.hypot(*np.diff(rz, axis=0).T)
    s0 = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(round(s0[-1] / ds)), 8)
    s = np.linspace(0.0, s0[-1], n + 1)
    P = np.stack([np.interp(s, s0, rz[:, 0]), np.interp(s, s0, rz[:, 1])], 1)
    T = np.gradient(P, s, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = np.stack([T[:, 1], -T[:, 0]], 1)
    return s, P, T, N


def curvature(s, P, T, N, r_axis):
    """Twice the mean curvature, positive where convex seen along N: kappa_1 = -(dT/ds).N, kappa_2 = n_r / r (on the
    axis, where r < r_axis, kappa_2 = kappa_1, the surface being smooth there)."""
    dT = np.gradient(T, s, axis=0)
    k1 = -np.einsum("ij,ij->i", dT, N)
    r = P[:, 0]
    k2 = np.where(r > r_axis, N[:, 0] / np.maximum(r, r_axis), k1)
    return k1 + k2, k1, k2


def simulate(rz, e0, tau, gamma=0.3, rho=2450.0, g=9.81, ds=2e-5, max_rel=0.03, tau_steps=None, normal_sign=1.0):
    """Flow the film e0 (a number, or a function of s in m) on the profile rz (m) for the dose tau (s/(Pa s)).
    normal_sign: +1 if the glaze lies on the side of the clockwise-turned tangent (the profile run with the body on
    its left), -1 otherwise. Returns dict(s, rz, e, e0, kappa, volume_error, steps)."""
    s, P, T, N = resample(rz, ds)
    N = N * normal_sign
    n = len(s)
    r = P[:, 0]
    r_axis = 2 * ds
    kap, k1, k2 = curvature(s, P, T, N, r_axis)
    e = np.asarray(e0(s) if callable(e0) else np.full(n, float(e0)), float).copy()
    e_start = e.copy()
    h = s[1] - s[0]
    rf = 0.5 * (r[1:] + r[:-1])                         # radius on the faces
    rn = np.maximum(r, r_axis)                          # on the nodes, kept off zero (the flux there is zero anyway)
    dzds_f = np.diff(P[:, 1]) / h                       # dz/ds on the faces
    nz = N[:, 1]
    vol = lambda x: np.sum(x * rn) * h                  # the film's volume over 2 pi (end nodes count half: close)
    v0 = vol(e)
    tau_done, steps = 0.0, 0
    dtau = 1e-6 * h ** 4 / (gamma * max(e.max(), 1e-6) ** 3) * 1e6
    while tau_done < tau:
        dtau = min(dtau, tau - tau_done)
        mf = (0.5 * (e[1:] + e[:-1])) ** 3 / 3.0        # mobility on the faces, explicit
        a = rf * mf                                     # r M on the faces
        # implicit: p_impl = C e, C tridiagonal (lo, di, up): -gamma lap(e) + rho g n_z e, lap(e)_i =
        # (rf_i (e_i+1 - e_i) - rf_i-1 (e_i - e_i-1)) / (r_i h^2), no flux through the ends.
        # Face f (between nodes f, f+1) carries F_f = a_f (-(p_f+1 - p_f) / h - rho g dz/ds), a_f = r_f e_f^3 / 3;
        # node i changes by -(F_i - F_i-1) / (r_i h). So de/dtau = M e + b, M pentadiagonal; backward Euler in e.
        wl = np.concatenate([[0.0], rf]) / (rn * h * h)
        wu = np.concatenate([rf, [0.0]]) / (rn * h * h)
        lo, up = -gamma * wl, -gamma * wu
        di = gamma * (wl + wu) + rho * g * nz
        cr = 1.0 / (rn * h * h)
        z1 = np.zeros(1)
        ai, aim1 = np.concatenate([a, z1]), np.concatenate([z1, a])
        nxt = lambda x: np.concatenate([x[1:], z1])
        prv = lambda x: np.concatenate([z1, x[:-1]])
        M = {-2: cr * aim1 * prv(lo),
             -1: cr * (ai * -lo - aim1 * (lo - prv(di))),
             0: cr * (ai * (nxt(lo) - di) - aim1 * (di - prv(up))),
             1: cr * (ai * (nxt(di) - up) - aim1 * up),
             2: cr * ai * nxt(up)}
        ab = np.zeros((5, n))                           # solve_banded's storage: ab[2 + i - j, j] = A[i, j]
        ab[4, :-2] = M[-2][2:]
        ab[3, :-1] = M[-1][1:]
        ab[2, :] = M[0]
        ab[1, 1:] = M[1][:-1]
        ab[0, 2:] = M[2][:-2]
        ab *= -dtau
        ab[2] += 1.0
        # explicit part: from gamma kappa and gravity
        pe = gamma * kap
        Fe = a * (-(pe[1:] - pe[:-1]) / h - rho * g * dzds_f)
        rhs = e.copy()
        rhs[:-1] -= dtau * cr[:-1] * h * Fe
        rhs[1:] += dtau * cr[1:] * h * Fe
        e_new = solve_banded((2, 2), ab, rhs)
        if np.any(e_new <= 0) or np.max(np.abs(e_new - e) / np.maximum(e, 1e-9)) > max_rel:
            dtau *= 0.5
            if dtau < 1e-30:
                raise SystemExit("glazeflow: the step shrank to nothing (the film is draining to zero somewhere)")
            continue
        e = e_new
        tau_done += dtau
        steps += 1
        dtau *= 1.3
        if tau_steps is not None and steps > tau_steps:
            raise SystemExit(f"glazeflow: more than {tau_steps} steps")
    return {"s": s, "rz": P, "e": e, "e0": e_start, "kappa": kap, "kappa1": k1, "kappa2": k2,
            "volume_error": vol(e) / v0 - 1.0, "steps": steps}


def check():
    ok = True
    # 1. levelling of a sinusoid on a flat film (a cylinder of a large radius: kappa_2 tiny, no gravity)
    R, L, e0, a0, gamma = 10.0, 2e-3, 2e-4, 1e-6, 0.3
    k = 2 * math.pi / (L / 4)
    rz = np.stack([np.full(400, R), np.linspace(L, 0.0, 400)], 1)    # z downwards along s; g = 0 below
    tau = 3.0 / (gamma * e0 ** 3 * k ** 4)                          # one e-folding of the amplitude
    res = simulate(rz, lambda s: e0 + a0 * np.cos(k * s), tau, gamma=gamma, g=0.0, ds=L / 800)
    s, e = res["s"], res["e"]
    amp = 2 * np.mean((e - e.mean()) * np.cos(k * s))
    want = a0 * math.exp(-1.0)
    print(f"levelling: amplitude {amp:.4e} after one e-folding, closed form {want:.4e} ({amp / want:.4f}); "
          f"volume error {res['volume_error']:.2e}, {res['steps']} steps")
    ok &= abs(amp / want - 1) < 0.01 and abs(res["volume_error"]) < 1e-6
    # 2. a film on a sphere drains from nowhere (uniform curvature): stays uniform
    th = np.linspace(0.0, math.pi, 600)
    Rs = 5e-3
    rz = np.stack([Rs * np.sin(th), -Rs * np.cos(th)], 1)           # from the south pole up: the body on the left
    res = simulate(rz, 3e-4, 1e-3, gamma=0.3, g=0.0, ds=Rs * math.pi / 600)
    spread = (res["e"].max() - res["e"].min()) / res["e"].mean()
    print(f"sphere, no gravity: relative spread {spread:.2e}, volume error {res['volume_error']:.2e}")
    ok &= spread < 1e-3 and abs(res["volume_error"]) < 1e-6
    print("all checks pass" if ok else "CHECK FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    a = ap.parse_args()
    if a.cmd == "check":
        sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
