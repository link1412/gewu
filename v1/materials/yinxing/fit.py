"""Fit the lamina's PROSPECT parameters to a scanned yellow leaf's colour (a starting value; the card's renders check it).

    python3 -I materials/yinxing/fit.py [--photo ref/yinxing/commons/Ginkgo_biloba_top_01.jpg] [--free N,Cab,Car]
    python3 -I materials/yinxing/fit.py --lamp          # the lamp set's Cbrown (lamp_fit below)

The target: the median colour of the leaves' blades in NobbiP's scan of three yellow leaves, upper side (Commons,
'Ginkgo biloba top 01', CanoScan LiDE 220, 400 dpi, CC BY-SA 3.0; ref/yinxing/commons/), decoded as sRGB to linear
[A: the scanner's output is sRGB with its white reference at 1; the background was blacked in GIMP, the leaves look
untouched]. The model: PROSPECT-D's R(lambda) seen as the scanner sees it, i.e. linear sRGB under D65 with a white
of reflectance 1 at (1, 1, 1) [A: a scanner calibrated to its white strip; its LEDs' spectra unknown]. A scanner
lights at about 45 degrees and looks along the normal: for a Lambertian leaf that is R [A].
Free parameters by default N, Cab, Car; Anth and Cbrown 0 (a clean yellow leaf), Cw and Cm from material.json.
Several starting points, the best kept (skill-notes 59). --fix holds a parameter (e.g. Cab at the ends of its range).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import optics as O  # noqa: E402
import prospect as P  # noqa: E402
from camera import LAM, Spectra, rgb709_from_xyz  # noqa: E402


def srgb_decode(v):
    v = np.asarray(v, float) / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def blade_colour(path):
    """Median linear colour of the leaf blades: leaf pixels (not the black ground), the petioles left out by a
    morphological opening wider than a petiole."""
    from scipy.ndimage import binary_opening
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    leaf = im.max(2) > 90
    blade = binary_opening(leaf, iterations=12)
    from scipy.ndimage import binary_erosion
    blade = binary_erosion(blade, iterations=6)          # off the margins
    lin = srgb_decode(im[blade])
    return np.median(lin, 0), int(blade.sum()), np.percentile(lin, [10, 90], 0)


class Scanner:
    def __init__(self):
        S = Spectra("canon_eos_5d_mkiv")
        self.cmf, d65 = S.cmf, S.d65
        self.d65 = d65 / (S.cmf[1] @ d65)
        white = S.cmf @ self.d65
        self.M = rgb709_from_xyz(white)

    def rgb(self, R):
        return self.M @ (self.cmf @ (R * self.d65))


def lamp_fit(m, rho=0.8, K=3000.0):
    """The lamp set's Cbrown: the backlit photo's blade colour relative to its lamp, green over red (its blue is
    clipped to 0), matched by the nobbip set's leaf with Cbrown added. The leaf over the shade: T / (1 - rho R) relative
    to the bare shade (the shade's reflectance rho returns what the leaf reflects; materials/yinxing/card.py), seen by
    the card's camera (white balanced on the lamp, camera.calibrate's matrix to linear BT.709). The phone's tone
    curve and colour processing are in the target, so the fitted Cbrown carries them too [F, not a material truth]."""
    from scipy.optimize import brentq
    import importlib.util
    import camera as C
    spec = importlib.util.spec_from_file_location("yinxing_compare", os.path.join(HERE, "compare.py"))
    compare = importlib.util.module_from_spec(spec)              # not tools/compare.py
    spec.loader.exec_module(compare)
    lin, _, info = compare.photo_linear("lamp")
    msk = compare.leaf_mask(lin, "lamp", 16.0)
    target = np.median(lin[msk], 0)
    S = C.Spectra("canon_eos_5d_mkiv")
    L = C.blackbody(K)
    cal = C.calibrate(S, L)
    w = S.sens @ L

    def seen(cb):
        p = O.lamina_params(m, "nobbip")
        p["Cbrown"] = cb
        R, T = O.spectra(p)
        return cal["C"] @ ((S.sens @ (L * T / (1 - rho * R))) / w)

    f = lambda cb: seen(cb)[1] / seen(cb)[0] - target[1] / target[0]
    print(f"lamp photo blade, linear BT.709 over its lamp: {np.round(target, 4)}  (lamp {info['photo_white_srgb8']} in sRGB 8 bit)")
    print(f"nobbip leaf (Cbrown 0) seen so: {np.round(seen(0.0), 4)}")
    if f(0.0) < 0:
        print("the nobbip leaf is already redder than the photo: no Cbrown")
        return
    cb = brentq(f, 0.0, 5.0)
    print(f"Cbrown {cb:.4f}: {np.round(seen(cb), 4)}  g/r {seen(cb)[1] / seen(cb)[0]:.4f} target {target[1] / target[0]:.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default=os.path.join(ROOT, "ref/yinxing/commons/Ginkgo_biloba_top_01.jpg"))
    ap.add_argument("--free", default="N,Cab,Car")
    ap.add_argument("--set", default="nobbip")
    ap.add_argument("--fix", default="", help="e.g. Cab=2.4 (held, not fitted)")
    ap.add_argument("--lamp", action="store_true", help="fit the lamp set's Cbrown to the backlit photo instead")
    a = ap.parse_args()
    if a.lamp:
        return lamp_fit(O.load())
    target, npx, spread = blade_colour(a.photo)
    print(f"target (linear sRGB, median of {npx} px): {np.round(target, 4)}  p10 {np.round(spread[0], 4)} p90 {np.round(spread[1], 4)}")
    sc = Scanner()
    m = O.load()
    base = O.lamina_params(m, a.set) if all(m["lamina"][k]["value"].get(a.set) is not None for k in P.PARAMS) else None
    if base is None:
        base = {"N": 1.8, "Cab": 4.0, "Car": 7.0, "Anth": 0.0, "Cbrown": 0.0,
                "Cw": float(O.value(m["lamina"]["Cw"], a.set)), "Cm": float(O.value(m["lamina"]["Cm"], a.set))}
    for kv in filter(None, a.fix.split(",")):
        k, v = kv.split("=")
        base[k] = float(v)
    free = a.free.split(",")
    lo = {"N": 1.0, "Cab": 0.0, "Car": 0.0, "Cbrown": 0.0, "Anth": 0.0}
    hi = {"N": 4.0, "Cab": 60.0, "Car": 40.0, "Cbrown": 3.0, "Anth": 10.0}

    def model(x):
        p = dict(base)
        p.update(dict(zip(free, x)))
        R, T = O.spectra(p)
        return sc.rgb(R), sc.rgb(T), p

    def resid(x):
        return np.log(np.maximum(model(x)[0], 1e-6)) - np.log(target)

    best = None
    rng = np.random.default_rng(0)
    for k in range(8):
        x0 = [rng.uniform(lo[f] + 0.1 * (hi[f] - lo[f]), lo[f] + 0.5 * (hi[f] - lo[f])) for f in free]
        r = least_squares(resid, x0, bounds=([lo[f] for f in free], [hi[f] for f in free]), xtol=1e-12, ftol=1e-12)
        if best is None or r.cost < best.cost:
            best = r
        print(f"start {k}: {dict(zip(free, np.round(r.x, 3)))} rms log {np.sqrt(np.mean(r.fun ** 2)):.4f}")
    Rr, Tr, p = model(best.x)
    print("best:", json.dumps({k: round(v, 4) for k, v in p.items()}))
    print(f"R (linear sRGB) {np.round(Rr, 4)} vs target {np.round(target, 4)}; T {np.round(Tr, 4)}")
    print(f"R chroma {np.round(Rr / Rr.sum(), 3)} target {np.round(target / target.sum(), 3)}; T chroma {np.round(Tr / Tr.sum(), 3)}")
    from camera import lab
    xyz = lambda rgb: np.linalg.solve(sc.M, rgb)
    white = sc.cmf @ sc.d65
    dE = np.linalg.norm(lab(xyz(Rr), white) - lab(xyz(target), white))
    print(f"dE76 (CIELAB, D65, the scanner's white) model vs target: {dE:.2f}")
    print("at bounds:", [f for f, v in zip(free, best.x) if abs(v - lo[f]) < 1e-6 or abs(v - hi[f]) < 1e-6])


if __name__ == "__main__":
    main()
