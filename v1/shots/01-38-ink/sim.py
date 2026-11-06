"""Ink spreading in xuan paper: water wicks out of a pool, carbon rides along and is filtered out by the fibres.

    python3 -I shots/01-38-ink/sim.py [--params shots/01-38-ink/params.json] [--out DIR] [--dx 0.2]
    -> DIR/maps.npz: x0, y0, dx, grammage (optical, fine grid), sat (water), coarse, fine (deposited carbon g/m^2),
       mobile carbon too; plus DIR/sim_log.json (front radius vs time: the Lucas-Washburn check).

Model (2D, per unit area of paper; lengths mm, time in units tau = 1 / D0):
  water   ds/dt = div( k(x) D(s) grad s ),  D(s) = D0 (s^m + eps)       Richards equation, unsaturated wicking
                                                                         (sharp front for large m); k from the
                                                                         local grammage (fibre flocs wick faster).
  carbon  d(s C_j)/dt = -div(q C_j) - lam_j k_f |q| C_j                  advection with the water flux q, and
          d sigma_j/dt = lam_j k_f |q| C_j                               deep-bed filtration (Iwasaki 1937):
                                                                         particles caught per length travelled.
  Two size classes j (coarse aggregates, fine particles): the chromatography (dark core, lighter fringe).
  The pool (r < a, centred at (0, -a)) holds s = 1, C = C0 until t_pool; then it is gone (its own carbon is
  deposited in place: the opaque core). Backward Euler with lagged coefficients; upwind carbon, also implicit.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paper  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))


def dirichlet(A, act):
    """Rows in act become identity rows."""
    keep = sp.diags((~act).astype(float))
    return (keep @ A + sp.diags(act.astype(float))).tocsr()


def harm(a, b):
    return 0.5 * (a + b)          # arithmetic: a harmonic mean stalls a degenerate (D(0) ~ 0) front


def run(P, dx, out):
    S = P["sim"]
    a = P["ink"]["pool_radius_mm"]
    x0, x1, y0, y1 = S["extent_mm"]
    # paper: optical grammage on a fine grid; the sim's permeability on the coarse grid from the same sheet
    dxo = P["paper"]["optical_dx_mm"]
    g = paper.grammage((x0, x1, y0, y1), dxo, P["paper"], P["paper"]["seed"])
    f = int(round(dx / dxo))
    nyc, nxc = g.shape[0] // f, g.shape[1] // f
    gc = g[:nyc * f, :nxc * f].reshape(nyc, f, nxc, f).mean(axis=(1, 3))
    k = gc ** S["perm_grammage_exponent"]
    k /= k.mean()
    ny, nx = nyc, nxc
    xc = x0 + (np.arange(nx) + 0.5) * dx
    yc = y0 + (np.arange(ny) + 0.5) * dx
    X, Y = np.meshgrid(xc, yc)
    R = np.hypot(X, Y + a)
    pool = R < a
    N = nx * ny
    idx = np.arange(N).reshape(ny, nx)

    s = np.where(pool, 1.0, 0.0)
    m_, eps, D0 = S["m"], S["eps"], 1.0
    classes = P["ink"]["classes"]
    C = [np.where(pool, c["C0_gsm_per_sat"], 0.0) for c in classes]       # carbon per unit water (g/m^2 at s=1)
    sig = [np.zeros((ny, nx)) for _ in classes]
    lamk = [c["lambda_per_mm"] * k ** S["filter_grammage_exponent"] for c in classes]

    t, dt = 0.0, S["dt0"]
    dt_front, front_prev = np.inf, None
    log = []
    t_pool, t_end = S["t_pool"], S["t_shot"]
    snaps = {}
    wall = time.time()
    step = 0
    while t < t_end - 1e-9:
        dt = min(dt * 1.15, dt_front, S["dt_max"], t_end - t)
        if t < t_pool < t + dt:
            dt = t_pool - t
        active = pool & (t < t_pool)
        # ---- water: face transmissibilities (lagged)
        Dc = k * D0 * (np.maximum(s, 0) ** m_ + eps)
        Tx = harm(Dc[:, :-1], Dc[:, 1:])            # faces between (i, j) and (i, j+1); per unit width / dx^2
        Ty = harm(Dc[:-1, :], Dc[1:, :])
        rows, cols, vals = [], [], []
        diag = np.full((ny, nx), 1.0 / dt)
        for T, a_, b_ in ((Tx, idx[:, :-1], idx[:, 1:]), (Ty, idx[:-1, :], idx[1:, :])):
            w = T / dx ** 2
            rows += [a_.ravel(), b_.ravel()]
            cols += [b_.ravel(), a_.ravel()]
            vals += [-w.ravel(), -w.ravel()]
        diag[:, :-1] += Tx / dx ** 2
        diag[:, 1:] += Tx / dx ** 2
        diag[:-1, :] += Ty / dx ** 2
        diag[1:, :] += Ty / dx ** 2
        rhs = s / dt
        # Dirichlet in the active pool
        A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))
        A = A + sp.diags(diag.ravel())
        if active.any():
            A = dirichlet(A, active.ravel())
            rhs = np.where(active, 1.0, rhs)
        s_new = spla.spsolve(A.tocsc(), rhs.ravel()).reshape(ny, nx)
        s_new = np.clip(s_new, 0, 1)
        # face fluxes (per unit width): positive in +x / +y
        qx = -Tx * (s_new[:, 1:] - s_new[:, :-1]) / dx
        qy = -Ty * (s_new[1:, :] - s_new[:-1, :]) / dx
        qcx = np.zeros((ny, nx))
        qcy = np.zeros((ny, nx))
        qcx[:, :-1] += qx / 2
        qcx[:, 1:] += qx / 2
        qcy[:-1, :] += qy / 2
        qcy[1:, :] += qy / 2
        qmag = np.hypot(qcx, qcy)
        # ---- carbon (each class): unknown C^{n+1}; mass s C
        for j in range(len(classes)):
            rows, cols, vals = [], [], []
            dg = s_new / dt + lamk[j] * qmag
            # x faces: flux qx from (.,i) to (.,i+1) if positive
            pos = np.maximum(qx, 0) / dx
            neg = np.maximum(-qx, 0) / dx
            dg[:, :-1] += pos          # outflow from left cell
            dg[:, 1:] += neg           # outflow from right cell
            rows += [idx[:, 1:].ravel(), idx[:, :-1].ravel()]
            cols += [idx[:, :-1].ravel(), idx[:, 1:].ravel()]
            vals += [-pos.ravel(), -neg.ravel()]
            pos = np.maximum(qy, 0) / dx
            neg = np.maximum(-qy, 0) / dx
            dg[:-1, :] += pos
            dg[1:, :] += neg
            rows += [idx[1:, :].ravel(), idx[:-1, :].ravel()]
            cols += [idx[:-1, :].ravel(), idx[1:, :].ravel()]
            vals += [-pos.ravel(), -neg.ravel()]
            dg = np.maximum(dg, 1e-12)
            rhs = s * C[j] / dt
            A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))
            A = A + sp.diags(dg.ravel())
            if active.any():
                A = dirichlet(A, active.ravel())
                rhs = np.where(active, classes[j]["C0_gsm_per_sat"], rhs)
            Cn = np.maximum(spla.spsolve(A.tocsc(), rhs.ravel()).reshape(ny, nx), 0)
            sig[j] += np.where(pool, 0.0, dt * lamk[j] * qmag * Cn)
            C[j] = Cn
        # front speed along the centre column -> next dt moves the front <= cfl cells
        colc = s_new[:, nx // 2] > 0.5
        fr = yc[np.nonzero(colc)[0].max()] if colc.any() else 0.0
        if front_prev is not None and fr > front_prev:
            dt_front = S["cfl"] * dx / ((fr - front_prev) / dt)
        else:
            dt_front = dt * 1.5
        front_prev = fr
        s = s_new
        t += dt
        step += 1
        if step % 10 == 0 or t >= t_end - 1e-9:
            wet = (s > 0.5) & ~pool
            col = s[:, nx // 2]
            front = yc[np.nonzero(col > 0.5)[0].max()] if (col > 0.5).any() else 0.0
            log.append(dict(t=t, front_mm=float(front), wet_area_mm2=float(wet.sum() * dx * dx),
                            water=float(s[~pool].sum() * dx * dx), wall=time.time() - wall))
            print(f"step {step} t {t:.3f} dt {dt:.4f} front {front:.2f} mm  wall {time.time() - wall:.0f} s", flush=True)
            for ts in S.get("snap_times", []):
                if ts not in snaps and t >= ts:
                    snaps[ts] = (s.copy(), [x.copy() for x in sig])
    # the pool's own carbon (dried puddle) -> the core
    core = P["ink"]["core_gsm"]
    for j, c in enumerate(classes):
        sig[j] = np.where(pool, core * c["share"], sig[j] + s * C[j] * 0)   # mobile carbon left in water: not deposited yet
    os.makedirs(out, exist_ok=True)
    np.savez_compressed(os.path.join(out, "maps.npz"), x0=x0, y0=y0, dx=dx, dxo=dxo, grammage=g.astype(np.float32),
                        sat=s.astype(np.float32), pool=pool, perm=k.astype(np.float32),
                        **{f"sigma_{c['name']}": sig[j].astype(np.float32) for j, c in enumerate(classes)},
                        **{f"mobile_{c['name']}": (s * C[j]).astype(np.float32) for j, c in enumerate(classes)})
    with open(os.path.join(out, "sim_log.json"), "w") as fh:
        json.dump(log, fh)
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default=os.path.join(HERE, "params.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "out/shots/01-38-ink/sim"))
    ap.add_argument("--dx", type=float, default=None)
    a = ap.parse_args()
    P = json.load(open(a.params))
    run(P, a.dx or P["sim"]["dx_mm"], a.out)


if __name__ == "__main__":
    main()
