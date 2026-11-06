"""A fast stand-in for the lamp card's pbrt render, to tune senescence.py's parameters in seconds (S8 round 2).

    python3 -I materials/yinxing/proxy.py fit  REF_CARD_DIR            # -> REF_CARD_DIR/proxy_cal.json
    python3 -I materials/yinxing/proxy.py make CARD_DIR CAL.json [--gain LAMPFIELD.json] [--bg REF_CARD_DIR]
                                                                       # -> CARD_DIR/proxy.npy (linear BT.709 over white)

The blade's light on the lamp, texel by texel: the families' (optics.write_brown_families) R and T on the brown map,
in the camera's channels under the lamp's 3000 K, mixed by veinamt as pbrt's mix material does (area-weighted),
blurred and sampled onto the card's 16 px/mm frame. The camera's linear BT.709 over the shade's white is then a
fitted 3 x 6 map of (T, T*R) per channel: T the direct light, T*R the light bounced between leaf and shade
(shade reflectance 0.8). The map is fitted [F] on a real pbrt render of the card (REF_CARD_DIR: its brown.exr,
veinamt.exr, families and pbrt.exr) over the blade's pixels; 'fit' reports its error. Outside the blade (the shade
and the petiole) the proxy copies the reference render's pixels. It is only for tuning: every reported number of the
round is measured on pbrt renders.
With --gain the lamp's measured brightness field (lampfield.py) multiplies everything (the leaf is 0.8 mm above the
shade, so it sees the shade's local brightness) [A].
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import camera  # noqa: E402,F401
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("yinxing_compare", os.path.join(HERE, "compare.py"))
CMP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CMP)
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2  # noqa: E402

KEY_K = 3000.0
BLUR_TEXEL = 1.0           # the pixel's footprint and pbrt's filter, as a Gaussian in texels [F, see 'fit']


def read1(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    return (a[..., 0] if a.ndim == 3 else a).astype(np.float32)


def fam_cam(card_dir):
    import rgbscene
    sen = rgbscene.Sensor("canon_eos_5d_mkiv", KEY_K)
    out = {}
    for name in ("lam", "vein"):
        for q in ("R", "T"):
            z = np.load(os.path.join(card_dir, f"{name}_{q}.npz"))
            lam = z["lambda_nm"]
            if len(lam) != sen.w.shape[1]:
                raise SystemExit("family wavelength grid differs from the sensor's")
            out[f"{name}_{q}"] = (z["c"], np.stack([sen.average(z["R"][k]) for k in range(len(z["c"]))], 1))
    return out


def texel_RT(card_dir):
    F = fam_cam(card_dir)
    b = read1(os.path.join(card_dir, "brown.exr"))
    bv_p = os.path.join(card_dir, "brown_vein.exr")
    bv = read1(bv_p) if os.path.exists(bv_p) else b
    a = read1(os.path.join(card_dir, "veinamt.exr"))
    res = {}
    for q in ("R", "T"):
        ch = []
        for c in range(3):
            cl, vl = F[f"lam_{q}"][0], F[f"lam_{q}"][1][c]
            cv_, vv = F[f"vein_{q}"][0], F[f"vein_{q}"][1][c]
            ch.append((1 - a) * np.interp(b, cl, vl) + a * np.interp(bv, cv_, vv))
        res[q] = np.stack(ch, -1)
    return res


def to_frame(card_dir, X):
    card = json.load(open(os.path.join(card_dir, "card.json")))
    vj = json.load(open(os.path.join(ROOT, "out/yinxing/objects", card["leaf"], "veins.json")))
    x0, y0, x1, y1 = vj["uv_box_mm"]
    t = (x1 - x0) / X.shape[1]
    o = json.load(open(os.path.join(ROOT, "objects/yinxing/lamp_outline.json")))["outline"]
    S = o["px_per_mm"]
    ox, oy = o["photo_frame"]["O_px"]
    W, H = 1280, 960
    py, px = np.mgrid[0:H, 0:W].astype(np.float64)
    xm, ym = (px + 0.5 - ox) / S, (oy - (py + 0.5)) / S
    j, i = (xm - x0) / t - 0.5, (y1 - ym) / t - 0.5
    inside = (i >= 0) & (i <= X.shape[0] - 1) & (j >= 0) & (j <= X.shape[1] - 1)
    out = []
    for c in range(X.shape[2]):
        f = gaussian_filter(X[..., c], BLUR_TEXEL)
        out.append(map_coordinates(f, [i, j], order=1, mode="constant", cval=0.0))
    return np.stack(out, -1), inside


def features(card_dir):
    RT = texel_RT(card_dir)
    a = read1(os.path.join(card_dir, "veinamt.exr"))
    T, R = RT["T"], RT["R"]
    Xt, inside = to_frame(card_dir, np.concatenate([T, T * R], -1))
    return Xt, inside


def blade_mask(card_dir):
    """The blade on the frame: veins.exr's texels inside the outline (c is set to 0 outside it, so use the brown
    map's support or the vein map's: the outline polygon instead)."""
    card = json.load(open(os.path.join(card_dir, "card.json")))
    vj = json.load(open(os.path.join(ROOT, "out/yinxing/objects", card["leaf"], "veins.json")))
    o = json.load(open(os.path.join(ROOT, "objects/yinxing/lamp_outline.json")))["outline"]
    S = o["px_per_mm"]
    ox, oy = o["photo_frame"]["O_px"]
    poly = np.asarray(o["polygon_mm"], float)
    pts = np.stack([ox + poly[:, 0] * S, oy - poly[:, 1] * S], 1)
    m = np.zeros((960, 1280), np.uint8)
    cv2.fillPoly(m, [np.round(pts * 8).astype(np.int32)], 1, shift=3)
    return m.astype(bool)


def cmd_fit(a):
    card = json.load(open(os.path.join(a.ref, "card.json")))
    card.setdefault("sensor", "canon_eos_5d_mkiv")
    lin, _ = CMP.develop(os.path.join(a.ref, "pbrt.exr"), card, "lamp")
    X, inside = features(a.ref)
    from scipy.ndimage import binary_erosion
    m = binary_erosion(blade_mask(a.ref), iterations=8) & inside
    A = X[m]
    M = []
    rep = {}
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A, lin[..., c][m], rcond=None)
        M.append(coef.tolist())
        pred = A @ coef
        y = lin[..., c][m]
        rep[f"ch{c}"] = {"rel_rms": round(float(np.sqrt(np.mean((pred - y) ** 2)) / np.mean(np.abs(y))), 4),
                         "median_pred_over_meas": round(float(np.median(pred) / np.median(y)), 4)}
    # the residual's smooth part (noise is pbrt's 256 spp; the smoothed residual is the proxy's own error)
    pred_g = np.zeros(lin.shape[:2]); pred_g[m] = A @ np.array(M[1])
    res = np.where(m, np.log(np.clip(pred_g, 1e-4, None)) - np.log(np.clip(lin[..., 1], 1e-4, None)), 0)
    rep["green_log_resid_std_smoothed_0.25mm"] = round(float(np.std(gaussian_filter(res, 4)[m])), 4)
    rep["green_log_resid_std"] = round(float(np.std(res[m])), 4)
    out = {"M": M, "ref": os.path.relpath(a.ref, ROOT), "blur_texel": BLUR_TEXEL, "report": rep}
    json.dump(out, open(os.path.join(a.ref, "proxy_cal.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


def make(card_dir, cal, gain_json=None, bg_dir=None):
    X, inside = features(card_dir)
    M = np.asarray(json.load(open(cal))["M"])
    lin = np.einsum("...j,ij->...i", X, M)          # not X @ M.T: matmul on big arrays segfaults here (S8 r3)
    bm = blade_mask(card_dir) & inside
    if bg_dir:
        cache = os.path.join(bg_dir, "pbrt_lin.npy")       # developed once (numpy's matmul on the big array crashed
        if os.path.exists(cache):                          # now and then on this machine)
            ref = np.load(cache)
        else:
            card = json.load(open(os.path.join(bg_dir, "card.json")))
            card.setdefault("sensor", "canon_eos_5d_mkiv")
            ref, _ = CMP.develop(os.path.join(bg_dir, "pbrt.exr"), card, "lamp")
            np.save(cache, ref.astype(np.float32))
    else:
        ref = np.ones_like(lin)
    lin = np.where(bm[..., None], lin, ref)
    if gain_json:
        import lampfield
        lj = json.load(open(gain_json))
        Y, Xp = np.mgrid[0:960, 0:1280]
        ox, oy = lj["O_px"]
        g = lampfield.gain_at_mm(lj, (Xp - ox) / lj["px_per_mm"], (oy - Y) / lj["px_per_mm"])
        lin = lin * g[..., None]
    return lin


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("fit"); f.add_argument("ref")
    mk = sp.add_parser("make"); mk.add_argument("card"); mk.add_argument("cal"); mk.add_argument("--gain"); mk.add_argument("--bg")
    a = ap.parse_args()
    if a.cmd == "fit":
        cmd_fit(a)
    else:
        lin = make(a.card, a.cal, a.gain, a.bg)
        np.save(os.path.join(a.card, "proxy.npy"), lin.astype(np.float32))
        print("->", os.path.join(a.card, "proxy.npy"))


if __name__ == "__main__":
    main()
