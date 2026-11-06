"""Shot 6's motion: the rigid motion of our vase whose flow best matches the original's, with the
silhouette held still (docs/shots/06-guan.md, 运动).

    python3 -I tools/flow.py measure 6
    python3 -I shots/06-guan/motion_fit.py [--flow out/flow/06_original.npz] [--out shots/06-guan/motion.json]

The original's texture does not just run down the frame, as a turntable seen side on makes it: near the limb
it slides along the limb, and lower down it runs faster on the right (1-2 px/frame on the left, 7 on the
right; tools/flow.py, S2). A turntable alone fits that at 2.1 px/frame rms. So the motion is fitted in full:
the velocity of a point P of the vase is w x P + t (world, mm per frame), and its image flow is the projection's
Jacobian times that. Where the original's moving blocks fall on our vase, the flows are matched (least squares);
along the silhouette inside the frame, the velocity across the silhouette is held at zero (weighted rows), as the
original's limb stays put (within a few px over the shot). Linear in (w, t).

The fit is a turntable plus a slow arc of the camera about the vase, as a motion-control rig makes. It is
then checked exactly, not to first order: the silhouette of the moved vase, two and a half frames either side.
"""

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import scene as S  # noqa: E402
from flow import STILL_PX  # noqa: E402

SILHOUETTE_WEIGHT = 30.0     # rows of px/frame across the silhouette, against rows of flow
T_MID = 2.5                  # the rest pose at mid-shot: the second-order drift of the silhouette splits both ways


def jacobian(cam, P, h=1e-3):
    """d(pixel)/d(world), (n, 2, 3)."""
    J = np.zeros((len(P), 2, 3))
    for i in range(3):
        e = np.zeros(3)
        e[i] = h
        J[:, :, i] = (cam.project(P + e) - cam.project(P - e)) / (2 * h)
    return J


def velocity_matrix(P):
    """(n, 3, 6): [w x P | I] so that the velocity is this times (w, t)."""
    x, y, z = P.T
    O, I = np.zeros_like(x), np.ones_like(x)
    W = np.stack([np.stack([O, z, -y], -1), np.stack([-z, O, x], -1), np.stack([y, -x, O], -1)], -2)
    T = np.broadcast_to(np.eye(3), (len(P), 3, 3))
    return np.concatenate([W, T], axis=2)


def silhouette_rows(cam, v, M, cols):
    """The top edge of the moved vase in the frame: per pixel column, the least y over the surface near the
    rest silhouette (dense parallels; the edge is the envelope of the parallels' tops)."""
    W, H = cam.res
    Ys = np.linspace(-0.6 * v.Rb, 0.6 * v.Rb, 6001)
    Pc, phi_c = S.contour(v, cam, Ys)
    xy = cam.project(Pc)
    keep = (xy[:, 0] > -0.05 * W) & (xy[:, 0] < 1.05 * W)
    Ys, phi_c = Ys[keep], phi_c[keep]
    dphi = np.linspace(-0.04, 0.04, 401)
    top = np.full(len(cols), np.inf)
    for i in range(0, len(Ys), 500):
        yy = np.repeat(Ys[i:i + 500], len(dphi))
        pp = (phi_c[i:i + 500, None] + dphi[None, :]).ravel()
        P, _ = v.point(pp * v.r0, yy)
        P = P @ M[:3, :3].T + M[:3, 3]
        q = cam.project(P)
        c = np.round(q[:, 0]).astype(int)
        ok = (c >= cols[0]) & (c <= cols[-1])
        np.minimum.at(top, c[ok] - cols[0], q[ok, 1])
    return top


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow", default=os.path.join(ROOT, "out", "flow", "06_original.npz"))
    ap.add_argument("--form", default=os.path.join(HERE, "form.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "motion.json"))
    a = ap.parse_args()
    v = S.Vessel(a.form)
    cam, _ = S.frame_and_focus(v, (1920, 1080))
    F = np.load(a.flow)
    m = np.hypot(F["dx"], F["dy"]) > STILL_PX
    x, y, b = F["x"][m], F["y"][m], np.c_[F["dx"][m], F["dy"][m]]
    P, on = S.surface_hit(v, cam, x, y)
    x, y, b, P = x[on], y[on], b[on], P[on]
    A_flow = np.einsum("nij,njk->nik", jacobian(cam, P), velocity_matrix(P))           # (n, 2, 6)

    Ys = np.linspace(-0.6 * v.Rb, 0.6 * v.Rb, 801)
    Pc, _ = S.contour(v, cam, Ys)
    xy = cam.project(Pc)
    inf = (xy[:, 0] > 0) & (xy[:, 0] < cam.res[0]) & (xy[:, 1] > 0) & (xy[:, 1] < cam.res[1])
    Pc, xy = Pc[inf][::10], xy[inf][::10]
    tan = np.gradient(xy, axis=0)
    nrm = np.c_[-tan[:, 1], tan[:, 0]] / np.linalg.norm(tan, axis=1)[:, None]
    A_sil = np.einsum("ni,nij->nj", nrm, np.einsum("nij,njk->nik", jacobian(cam, Pc), velocity_matrix(Pc)))

    def fit(cols):
        A = np.r_[A_flow.reshape(-1, 6)[:, cols], SILHOUETTE_WEIGHT * A_sil[:, cols]]
        rhs = np.r_[b.ravel(), np.zeros(len(A_sil))]
        u = np.zeros(6)
        u[cols] = np.linalg.lstsq(A, rhs, rcond=None)[0]
        pred = (A_flow.reshape(-1, 6) @ u).reshape(-1, 2)
        return u, float(np.sqrt(np.mean((pred - b) ** 2))), float(np.abs(A_sil @ u).max()), pred

    u_tt, rms_tt, _, _ = fit([2])
    u, rms, sil, pred = fit([0, 1, 2, 3, 4, 5])
    w, t = u[:3], u[3:]
    m6 = S.screw(w, t)
    print(f"{len(x)} moving blocks on our vase ({(~on).sum()} fall above our limb)")
    print(f"turntable alone: {math.degrees(-u_tt[2]):.4f} deg/frame, rms {rms_tt:.2f} px/frame")
    print(f"rigid motion: w {np.round(w, 6)} rad/frame ({math.degrees(m6[2]):.4f} deg/frame), t {np.round(t, 4)} mm/frame; "
          f"rms {rms:.2f} px/frame; across the silhouette at most {sil:.2f} px/frame (first order)")
    print(f"  as a screw: axis through {np.round(m6[0], 2)} mm along {np.round(m6[1], 4)}, "
          f"{m6[3] * 1000:.1f} um/frame along it")
    for lo, hi in ((480, 700), (700, 850), (850, 1080)):
        for xl, xh in ((0, 640), (640, 1280), (1280, 1920)):
            k = (y >= lo) & (y < hi) & (x >= xl) & (x < xh)
            if k.any():
                print(f"  rows {lo}-{hi} cols {xl}-{xh}: original ({b[k, 0].mean():+.1f},{b[k, 1].mean():+.1f}) "
                      f"fit ({pred[k, 0].mean():+.1f},{pred[k, 1].mean():+.1f})  n {k.sum()}")

    cols = np.arange(0, cam.res[0])
    rest = silhouette_rows(cam, v, np.eye(4), cols)
    drift = {}
    for s in (-T_MID, T_MID):
        d = silhouette_rows(cam, v, S.pose(m6, s), cols) - rest
        ok = np.isfinite(d) & (rest > 0) & (rest < cam.res[1])
        drift[s] = float(np.abs(d[ok]).max())
        print(f"silhouette {s:+.1f} frames from the rest pose: moves at most {drift[s]:.2f} px (exact)")

    out = {"about": "shot 6's motion, fitted by shots/06-guan/motion_fit.py to the original's flow (tools/flow.py); "
                    "velocity of a world point P (mm) is w x P + t per frame; the rest pose is at frame T_MID of the shot",
           "w_rad_per_frame": [round(float(c), 8) for c in w], "t_mm_per_frame": [round(float(c), 6) for c in t],
           "t_mid_frame": T_MID,
           "fit": {"blocks": int(len(x)), "rms_px_per_frame": round(rms, 3),
                   "turntable_alone_rms_px_per_frame": round(rms_tt, 3),
                   "silhouette_drift_px_at_ends": round(max(drift.values()), 3)}}
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
