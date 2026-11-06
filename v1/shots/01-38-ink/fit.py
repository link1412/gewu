"""Fit the camera (to the arc) and the lamps (to the colour profile) against the original's frame 0.

    python3 -I shots/01-38-ink/fit.py MAPS.npz [--stage geo|light|both] [--res 320]
    -> updates shots/01-38-ink/optics.json in place (fitted values only; labels stay), prints the residuals.

Geometry: pitch puts the apex of the horizon on row 0.4728 H; f_px gives R/W = 3.29 (measure.py on frame 0).
Light: least squares on three column profiles (cols 200-360, 880-1040, 1560-1720; every row) in display code values, rows from the
top of the frame down to 0.3 H below the horizon. Free: the two lamps (position, depth, colour, strength), the
front fill, lens veiling glare, the fine carbon's AAE, the aperture.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy import ndimage, optimize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402
import optics as op  # noqa: E402

OPT = os.path.join(HERE, "optics.json")


def full_render(sheet, O, C, W, H, ss=1):
    return op.render(sheet, O, C, W, H, ss=ss)


def to_codes(img):
    return op.to_display(img) * 255


def upscale(codes):
    H, W = codes.shape[:2]
    z = (M.FH / H, M.FW / W, 1)
    return np.clip(ndimage.zoom(codes, z, order=1), 0, 255).astype(np.uint8)


def aim_y(sheet, thresh_gsm=0.3):
    names = list(sheet.carbon)
    tot = sum(sheet.carbon[n] for n in names)
    col = tot[:, tot.shape[1] // 2]
    y = sheet.y0 + (np.arange(len(col)) + 0.5) * sheet.dx
    out = y[(col > thresh_gsm)]
    return float(out.max())


def fit_geometry(sheet, O, res, target):
    W, H = res, res * 9 // 16
    C = O["camera"]
    C["aim"] = [0.0, aim_y(sheet)]
    for it in range(8):
        codes = to_codes(full_render(sheet, O, C, W, H))
        m = M.measure(upscale(codes))
        if "apex_y" not in m:
            print("geo: no arc found", m.get("peak_luma"))
            C["pitch_deg"] = C.get("pitch_deg", 0) - 1.0
            continue
        dy = m["apex_y"] - target["apex_y"]
        dr = m["r_over_w"] / target["r_over_w"]
        print(f"geo it {it}: apex_y {m['apex_y']:.4f} (target {target['apex_y']:.4f}), R/W {m['r_over_w']:.3f} "
              f"(target {target['r_over_w']:.3f}), pitch {C.get('pitch_deg', 0):.3f}, f_px {C['f_px']:.0f}")
        if abs(dy) < 0.002 and abs(dr - 1) < 0.02:
            break
        # image row moves down when the camera pitches up: d(row)/d(pitch) ~ f_px (rad)
        C["pitch_deg"] = C.get("pitch_deg", 0) - np.degrees(dy * M.FH / C["f_px"])
        C["f_px"] = C["f_px"] / dr ** 0.8
    return m


BANDS = [(200, 360), (880, 1040), (1560, 1720)]   # column bands (1920 px) the light is fitted on: left, centre, right
PARAMS = [  # (path, transform) transform: 'log' for positive scales
    (("lamps", 0, "scale"), "log"), (("lamps", 0, "y_mm"), None), (("lamps", 0, "depth_mm"), "log"),
    (("lamps", 0, "spectrum", "T"), "log"),
    (("lamps", 1, "scale"), "log"), (("lamps", 1, "y_mm"), None), (("lamps", 1, "depth_mm"), "log"),
    (("lamps", 1, "spectrum", "beta"), None),
    (("front", "scale"), "log"), (("glare",), None), (("carbon", "aae", "fine"), None),
    (("camera", "aperture_mm"), "log"), (("lamps", 1, "radius_mm"), "log"),
    (("lamps", 1, "spectrum", "gamma"), None),
]


def getp(O, path):
    v = O
    for k in path:
        v = v[k]
    return v


def setp(O, path, val):
    v = O
    for k in path[:-1]:
        v = v[k]
    v[path[-1]] = val


def fit_light(sheet, O, res, ref_codes, rows_keep):
    W, H = res, res * 9 // 16
    x0 = []
    for path, tr in PARAMS:
        v = getp(O, path) if path != ("glare",) else O.get("glare", 0.01)
        x0.append(np.log(v) if tr == "log" else v)
    x0 = np.array(x0, float)
    bands = [(int(a0 / 1920 * W), int(a1 / 1920 * W)) for a0, a1 in BANDS]

    def apply(x):
        for (path, tr), v in zip(PARAMS, x):
            setp(O, path, float(np.exp(v)) if tr == "log" else float(v))

    def resid(x):
        apply(x)
        O["glare"] = float(np.clip(O["glare"], 0, 0.5))
        codes = to_codes(full_render(sheet, O, O["camera"], W, H))
        r = [(codes[:, c0:c1].mean(axis=1) - rc)[rk] / 255.0 for (c0, c1), rc, rk in zip(bands, ref_codes, rows_keep)]
        return np.concatenate([x.ravel() for x in r])

    lo = np.array([-20, -70, np.log(0.5), np.log(1200), -20, -120, np.log(1), -2, -30, 0, 0.5, np.log(0.2), np.log(5), -2])
    hi = np.array([20, 0, np.log(200), np.log(6500), 20, 40, np.log(400), 8, 5, 0.3, 6.0, np.log(40), np.log(200), 4])
    x0 = np.clip(x0, lo + 1e-6, hi - 1e-6)
    r0 = resid(x0)
    print(f"light: start rms {np.sqrt(np.mean(r0 ** 2)) * 255:.2f} codes")
    sol = optimize.least_squares(resid, x0, bounds=(lo, hi), x_scale="jac", diff_step=1e-3, max_nfev=400, verbose=1)
    apply(sol.x)
    print(f"light: end rms {np.sqrt(np.mean(sol.fun ** 2)) * 255:.2f} codes ({sol.nfev} renders)")
    return sol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("maps")
    ap.add_argument("--stage", default="both")
    ap.add_argument("--res", type=int, default=320)
    a = ap.parse_args()
    P = json.load(open(os.path.join(HERE, "params.json")))
    O = json.load(open(OPT))
    sheet = op.Sheet(a.maps, P)
    orig = json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/orig.json")))["0"]
    target = dict(apex_y=orig["apex_y"], r_over_w=orig["r_over_w"])
    ref = M.decode_original([0])[0].astype(float)
    W, H = a.res, a.res * 9 // 16
    ref_s = ndimage.zoom(ref, (H / M.FH, W / M.FW, 1), order=1)
    ref_codes, rows_keep = [], []
    for a0, a1 in BANDS:
        c0, c1 = int(a0 / 1920 * W), int(a1 / 1920 * W)
        ref_codes.append(ref_s[:, c0:c1].mean(axis=1))
        xm = (a0 + a1) / 2
        r = orig["r_over_w"] * M.FW
        hrow = (orig["apex_y"] * M.FH + r - np.sqrt(r * r - (xm - orig["apex_x"] * M.FW) ** 2)) / M.FH * H
        rows_keep.append(np.arange(H) < hrow + 0.3 * H)
    for k in range(2):
        if a.stage in ("geo", "both"):
            fit_geometry(sheet, O, a.res, target)
        if a.stage in ("light", "both"):
            fit_light(sheet, O, a.res, ref_codes, rows_keep)
        if a.stage != "both":
            break
    m = fit_geometry(sheet, O, a.res, target) if a.stage in ("geo", "both") else None
    with open(OPT, "w") as fh:
        json.dump(O, fh, indent=2, ensure_ascii=False)
    print(json.dumps({k: O[k] for k in ("lamps", "front", "glare", "camera", "carbon") if k in O}, indent=1))


if __name__ == "__main__":
    main()
