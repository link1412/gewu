"""Test a, the check: each plate's reflectance (plate / white reference, per channel) in pbrt and Cycles, against
an analytic prediction per pixel, and pbrt against Cycles.

    python3 -I tests/metals/check_fresnel.py [--variants Au_a0,...]

The prediction is computed here, independently of tools/rgbscene.py's functions: pbrt's camera rays through pixel
centres, each ray's hit on its plate, and
- smooth: F(theta) L, theta the ray's angle of incidence, if the mirror ray reaches a light;
- rough: the sum over every light of the integral of the GGX BRDF (pbrt's TrowbridgeReitz: D, height-correlated
  Smith G) times L cos over the light (a 32 x 32 midpoint rule);
with F the spectral Fresnel averaged over each channel (sensor x 5500 K weights: what pbrt computes, up to its
wavelength sampling) for pbrt, and the per-channel eta, k from the JSON for Cycles. Only the pixels at least 2 mm
(projected) inside a plate's edges count. Colours as dE*ab (the camera chain's colour-checker matrix, white = the
reference light).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcommon as C  # noqa: E402
import gen_fresnel as G  # noqa: E402

sys.path.insert(0, os.path.join(C.ROOT, "tools"))
import camera  # noqa: E402

D = os.path.join(C.OUT, "fresnel")
MARGIN = 2.0


def fresnel(c, n, k):
    eta = np.asarray(n) + 1j * np.asarray(k)
    c = np.clip(c, 0, 1)
    ct = np.sqrt(1 - (1 - c * c) / eta ** 2)
    a, b = (eta * c - ct) / (eta * c + ct), (c - eta * ct) / (c + eta * ct)
    return (abs(a) ** 2 + abs(b) ** 2) / 2


S = camera.Spectra("canon_eos_5d_mkiv")
W = S.sens * camera.blackbody(5500.0)


def spectral_F(metal):
    """F_c(cos) for pbrt: a function on a fine cos grid, interpolated."""
    if metal == "refl":
        v = np.array([float(x) for x in G.REFL.strip("[] ").split()])
        r = np.clip(camera.piecewise(v), 0, 0.9999)
        n, k = np.ones_like(r), 2 * np.sqrt(r) / np.sqrt(1 - r)
    else:
        e, kk = camera.pbrt_array(f"{metal}_eta"), camera.pbrt_array(f"{metal}_k")
        n, k = np.interp(camera.LAM, e[0::2], e[1::2]), np.interp(camera.LAM, kk[0::2], kk[1::2])
    cg = np.linspace(0, 1, 4001)
    tab = fresnel(cg[:, None], n[None], k[None]) @ W.T / W.sum(1)
    return lambda c: np.stack([np.interp(c, cg, tab[:, i]) for i in range(3)], -1), (n, k)


def fit_F(mat):
    return lambda c: np.stack([fresnel(c, mat["eta"][i], mat["k"][i]) for i in range(3)], -1)


def ggx_d(cos_h, a):
    c2 = cos_h ** 2
    t2 = np.maximum(1 - c2, 0) / np.maximum(c2, 1e-12)
    return 1 / (math.pi * a * a * c2 * c2 * (1 + t2 / (a * a)) ** 2)


def lam(cos, a):
    t2 = np.maximum(1 - cos * cos, 0) / np.maximum(cos * cos, 1e-12)
    return (np.sqrt(1 + a * a * t2) - 1) / 2


def all_lights():
    L = G.lights()
    L.append((G.REF_C, np.array([0.0, 1.0, 0.0]), np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), G.REF_S / 2))
    return L


def hits_light(P, R, L):
    """does the ray P + t R (t > 0) hit the front of any light quad?"""
    hit = np.zeros(P.shape[0], bool)
    for c, n, e1, e2, h in L:
        dn = R @ n
        t = ((c - P) @ n) / np.where(abs(dn) > 1e-12, dn, 1e-12)
        X = P + t[:, None] * R - c
        hit |= (t > 0) & (dn < 0) & (abs(X @ e1) < h) & (abs(X @ e2) < h)
    return hit


def predict(P, wo, nrm, F, alpha, L, grid=32):
    """(N, 3) radiance over L for points P (N, 3) seen along wo (towards the eye)."""
    cos_o = wo @ nrm
    if alpha == 0:
        R = 2 * cos_o[:, None] * nrm - wo
        return F(cos_o) * hits_light(P, R, L)[:, None]
    out = np.zeros((P.shape[0], 3))
    g = (np.arange(grid) + 0.5) / grid * 2 - 1
    for c, ln, e1, e2, h in L:
        Q = (c + h * (g[:, None, None] * e1 + g[None, :, None] * e2)).reshape(-1, 3)    # (M, 3)
        dA = (2 * h / grid) ** 2
        V = Q[None] - P[:, None]                                                      # (N, M, 3)
        r2 = (V ** 2).sum(-1)
        wi = V / np.sqrt(r2)[..., None]
        cos_i = wi @ nrm
        cos_l = -(wi @ ln)
        ok = (cos_i > 0) & (cos_l > 0)
        H = wi + wo[:, None]
        H /= np.linalg.norm(H, axis=-1, keepdims=True)
        cos_h = H @ nrm
        Gs = 1 / (1 + lam(cos_o[:, None], alpha) + lam(np.maximum(cos_i, 1e-9), alpha))
        f = ggx_d(cos_h, alpha) * Gs / (4 * cos_o[:, None] * np.maximum(cos_i, 1e-9))
        Fh = F(np.clip((wo[:, None] * H).sum(-1), 0, 1))                                # (N, M, 3)
        w = np.where(ok, f * cos_i * cos_l / r2 * dA, 0.0)
        out += (Fh * w[..., None]).sum(1)
    return out


def plate_pixels(i, eye, Dir):
    c, n, ex, t, hx, ht = G.plate(i)
    dn = Dir @ n
    tt = ((c - eye) @ n) / dn
    P = eye + tt[..., None] * Dir
    u, v = (P - c) @ ex, (P - c) @ t
    th = math.radians(G.TH[i])
    m = (abs(u) < hx - MARGIN) & (abs(v) < ht - MARGIN / math.cos(th))
    return m, P[m], -Dir[m], n


def ref_pixels(eye, Dir):
    n = np.array([0.0, 1.0, 0.0])
    tt = ((G.REF_C - eye) @ n) / (Dir @ n)
    P = eye + tt[..., None] * Dir - G.REF_C
    h = G.REF_S / 2 - MARGIN
    return (abs(P[..., 0]) < h) & (abs(P[..., 2]) < h)


def lab_of(rgb, cal, white):
    return camera.lab(np.atleast_2d(rgb) @ cal["M"].T, white)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants")
    a = ap.parse_args()
    V = a.variants.split(",") if a.variants else list(G.VARIANTS)
    eye, Dir = C.pixel_rays(G.EYE, G.TARGET, G.UP, G.FOV, G.RES)
    L = all_lights()
    cal = camera.calibrate(S, camera.blackbody(5500.0))
    white = S.cmf @ S.d65 / (S.cmf[1] @ S.d65)
    rm = ref_pixels(eye, Dir)
    res, ok = {}, True
    for v in V:
        metal, alpha = G.VARIANTS[v]
        mat = [o for o in json.load(open(f"{D}/scene_{v}.cycles.json"))["objects"] if o["material"]["type"] == "conductor"][0]["material"]
        E = np.array(json.load(open(f"{D}/scene_{v}.cycles.json"))["objects"][0]["emission"])
        Fs, (n_l, k_l) = spectral_F(metal)
        Ff = fit_F(mat)
        nv = (W @ n_l) / W.sum(1), (W @ k_l) / W.sum(1)                   # naive: eta, k averaged like a reflectance
        Fn = lambda c: np.stack([fresnel(c, nv[0][i], nv[1][i]) for i in range(3)], -1)
        img = {r: C.read_image(f"{D}/{r}_{v}.exr") for r in ("pbrt", "cyc")}
        ref = {r: img[r][rm].mean(0) for r in img}
        rows = []
        print(f"\n{v}: white reference pbrt {ref['pbrt'].round(4)}, Cycles {ref['cyc'].round(4)}, JSON emission {E.round(4)}")
        print("  deg | pbrt/pred(spectral) RGB | Cycles/pred(fit) RGB | Cycles/pbrt RGB | F pbrt (RGB) | dE pbrt-Cycles | dE pbrt-pred | dE naive-spectral")
        for i in range(len(G.TH)):
            m, P, wo, n = plate_pixels(i, eye, Dir)
            ps, pf, pn = (predict(P, wo, n, F, alpha, L) for F in (Fs, Ff, Fn))
            meas = {r: img[r][m] / ref[r] for r in img}
            sp, sc = meas["pbrt"].sum(0), meas["cyc"].sum(0)
            r_p, r_c, r_pc = sp / ps.sum(0), sc / pf.sum(0), sc / sp
            Fp, Fc = sp / len(P), sc / len(P)                          # mean ratio (for a smooth plate: F)
            norm = ps.sum(0) / len(P)                                  # prediction's mean, the colour's scale
            k = 1 / norm.max()                                         # dE on colours scaled alike (a brightness-independent hue check)
            dE_pc = float(np.linalg.norm(lab_of(Fp * k, cal, white) - lab_of(Fc * k, cal, white)))
            dE_pp = float(np.linalg.norm(lab_of(Fp * k, cal, white) - lab_of(norm * k, cal, white)))
            dE_nv = float(np.linalg.norm(lab_of(pn.sum(0) / len(P) * k, cal, white) - lab_of(norm * k, cal, white)))
            rows.append({"deg": G.TH[i], "pixels": int(len(P)), "pbrt_over_pred": r_p.round(4).tolist(),
                         "cycles_over_pred": r_c.round(4).tolist(), "cycles_over_pbrt": r_pc.round(4).tolist(),
                         "F_pbrt": Fp.round(4).tolist(), "F_cycles": Fc.round(4).tolist(), "pred_spectral": norm.round(4).tolist(),
                         "pred_fit": (pf.sum(0) / len(P)).round(4).tolist(), "pred_naive": (pn.sum(0) / len(P)).round(4).tolist(),
                         "dE_pbrt_cycles": round(dE_pc, 2), "dE_pbrt_pred": round(dE_pp, 2), "dE_naive": round(dE_nv, 2)})
            print(f"  {G.TH[i]:3d} | {r_p.round(4)} | {r_c.round(4)} | {r_pc.round(4)} | {Fp.round(3)} | {dE_pc:.2f} | {dE_pp:.2f} | {dE_nv:.2f}")
            tol = 0.01 if alpha == 0 else 0.03
            ok &= bool(np.all(abs(r_p - 1) < tol) and np.all(abs(r_c - 1) < tol))
        res[v] = rows
    json.dump(res, open(f"{D}/numbers.json", "w"), indent=1)
    print("\nPASS" if ok else "\nFAIL")


if __name__ == "__main__":
    main()
