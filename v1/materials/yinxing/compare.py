"""The ginkgo cards' renders against their photographs: side-by-side images and numbers.

    python3 -I materials/yinxing/compare.py lamp|scan RENDER.exr [RENDER2.exr ...] [--out DIR]   # card.json beside each render

Both sides are brought to linear BT.709 relative to their white:
- the photo: sRGB decoded, divided by its white (lamp: the median of the lamp around the leaf; scan: 1, the
  scanner's calibration [A]);
- a render (raw sensor RGB, materials/yinxing/card.py): divided by its white (lamp: the median of the shade around
  the leaf; scan: the median of the white patch), then camera.calibrate's matrix for the card's light (white
  balanced sensor RGB to linear BT.709).
Numbers, on the blade (the leaf mask, 0.5 mm in from the margin):
- the median colour relative to white, its chromaticity r, g, b = RGB / sum, and dE76 (CIELAB, D65 white) between
  photo and render;
- the vein texture: the band of the veins' spacing isolated by a difference of Gaussians (sigma 0.06 and 0.25 mm),
  its standard deviation over the blade divided by the blade's median (green channel; red for the lamp, whose green
  is the cleaner channel there? no: green for both, stated);
- the vein lines' contrast: along curves 2 and 4 mm inside the distal margin, the green channel's peaks over the
  local mean (high-passed over 0.4 mm), the median relative peak height and whether the veins are lighter (+) or
  darker (-) than the lamina.
The lamp card's render and photo share their pixels (the leaf's outline was traced from the photo and the render is
framed on it); the scan card compares a crop of the photo with the render's frame, a different leaf.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import (binary_erosion, binary_fill_holes, binary_opening, gaussian_filter, gaussian_filter1d,
                           label, map_coordinates)
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as C  # noqa: E402

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2  # noqa: E402

PHOTO = {"lamp": "ref/yinxing/commons/Ginkgo_biloba_yellow_leaf_on_a_lamp.jpg",
         "scan": "ref/yinxing/commons/Ginkgo_biloba_top_01.jpg"}
SCAN_CROP = (160, 1280, 1120, 1820)        # x0, y0, x1, y1 px of NobbiP's scan: the big left leaf's lower lobe [A, a choice]


def srgb_decode(v):
    v = np.asarray(v, float) / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def biggest(m):
    lab, n = label(m)
    if n == 0:
        return m
    s = np.bincount(lab.ravel())
    s[0] = 0
    return lab == np.argmax(s)


def lab_of(rgb):
    xyz_from_rgb = np.linalg.inv(C.rgb709_from_xyz(np.array([0.95047, 1.0, 1.08883])))
    white = np.array([0.95047, 1.0, 1.08883])
    return C.lab(np.asarray(rgb) @ xyz_from_rgb.T, white)


def develop(path, card, rig):
    raw = C.read_raw(path)
    S = C.Spectra(card["sensor"])
    light = C.blackbody(card["key_K"]) if rig == "lamp" else S.d65
    cal = C.calibrate(S, light)
    if rig == "lamp":
        g = raw[..., 1]
        bright = g > 0.7 * np.percentile(g, 95)
        white = np.median(raw[bright], 0)
    else:
        x0, y0, x1, y1 = card["white_patch_px"]
        white = np.median(raw[y0:y1, x0:x1].reshape(-1, 3), 0)
    wb = raw / white
    # einsum, not 'wb @ C.T': numpy's matmul on the (H, W, 3) array segfaults on this machine now and then (S8 r2/r3;
    # the local numpy's BLAS path) [M: three crashes in a row at this line, S8 r3]
    return np.einsum("...j,ij->...i", wb, np.asarray(cal["C"], float)), {"white_raw": white.tolist(), "calibration_dE_mean": float(np.mean(cal["dE"]))}


def photo_linear(rig):
    im = np.asarray(Image.open(os.path.join(ROOT, PHOTO[rig])).convert("RGB")).astype(float)
    if rig == "scan":
        x0, y0, x1, y1 = SCAN_CROP
        im = im[y0:y1, x0:x1]
    lin = srgb_decode(im)
    info = {}
    if rig == "lamp":
        bg = im[..., 2] > 200
        white = np.median(lin[bg], 0)
        info["photo_white_srgb8"] = np.median(im[bg], 0).tolist()
        lin = lin / white
        if lin.shape[0] == 959:
            lin = np.r_[lin, lin[-1:]]
    return lin, im, info


def leaf_mask(lin, rig, pxmm):
    if rig == "lamp":
        m = lin[..., 2] < 0.5
    else:
        m = lin.max(2) > 0.1
    m = biggest(binary_fill_holes(binary_opening(m, iterations=2)))
    return binary_erosion(m, iterations=max(1, int(0.5 * pxmm)))


def vein_texture(lin, m, pxmm):
    g = lin[..., 1]
    band = gaussian_filter(g, 0.06 * pxmm) - gaussian_filter(g, 0.25 * pxmm)
    return float(np.std(band[m]) / np.median(g[m]))


def vein_lines(lin, m_full, pxmm, depths=(2.0, 4.0)):
    from scipy.ndimage import distance_transform_edt
    D = distance_transform_edt(m_full) / pxmm
    g = lin[..., 1]
    out = []
    for d in depths:
        cs, _ = cv2.findContours((D > d).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cs:
            continue
        c = max(cs, key=len)[:, 0, :].astype(float)
        ys = np.nonzero(m_full.any(1))[0]
        top = c[:, 1] < ys.min() + 0.55 * (ys.max() - ys.min())        # the distal part (upper half of the leaf)
        idx = np.nonzero(top)[0]
        if len(idx) < 10:
            continue
        runs = np.split(idx, np.nonzero(np.diff(idx) != 1)[0] + 1)
        P = c[max(runs, key=len)]
        s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        t = np.arange(0, s[-1], 0.5)
        x, y = np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])
        v = map_coordinates(g, [y, x], order=1)
        mean = gaussian_filter1d(v, 0.4 * pxmm * 2)
        hp = (v - mean) / mean
        res = {}
        for sign, name in ((1, "lighter"), (-1, "darker")):
            pk, pr = find_peaks(sign * hp, prominence=0.01, distance=max(2, int(0.45 * pxmm * 2)))
            res[name] = {"count": int(len(pk)), "median_prominence": round(float(np.median(pr["prominences"])), 4) if len(pk) else 0.0}
        out.append({"depth_mm": d, "length_mm": round(s[-1] / pxmm, 1), **res,
                    "hp_std": round(float(np.std(hp)), 4)})
    return out


def stats(lin, rig, pxmm):
    m = leaf_mask(lin, rig, pxmm)
    med = np.median(lin[m], 0)
    full = biggest(binary_fill_holes(binary_opening(lin[..., 2] < 0.5 if rig == "lamp" else lin.max(2) > 0.1, iterations=2)))
    return m, {"blade_median_rel_white": np.round(med, 4).tolist(),
               "chroma": np.round(med / med.sum(), 4).tolist(),
               "p10": np.round(np.percentile(lin[m], 10, 0), 4).tolist(),
               "p90": np.round(np.percentile(lin[m], 90, 0), 4).tolist(),
               "vein_texture": round(vein_texture(lin, m, pxmm), 4),
               "vein_lines": vein_lines(lin, full, pxmm) if rig == "lamp" else None}


def display(lin):
    return (np.clip(C.srgb_encode(np.clip(lin, 0, None)), 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rig", choices=("lamp", "scan"))
    ap.add_argument("renders", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    card = json.load(open(os.path.join(os.path.dirname(os.path.abspath(a.renders[0])), "card.json")))
    card.setdefault("sensor", "canon_eos_5d_mkiv")
    pxmm = card["px_per_mm"]
    if a.rig == "scan":
        cx, cy = card["frame_centre_mm"]
        W, H = 960, 540
        x0, y0, x1, y1 = card["white_patch_mm"]
        px = lambda x: int(round(W / 2 + (x - cx) * pxmm))
        py = lambda y: int(round(H / 2 - (y - cy) * pxmm))
        card["white_patch_px"] = [px(x0) + 3, py(y1) + 3, px(x1) - 3, py(y0) - 3]
    plin, pim, pinfo = photo_linear(a.rig)
    _, ps = stats(plin, a.rig, pxmm)
    report = {"rig": a.rig, "photo": PHOTO[a.rig], "photo_crop": SCAN_CROP if a.rig == "scan" else None,
              "photo_stats": ps, **pinfo, "renders": {}}
    panels = [pim.astype(np.uint8) if a.rig == "scan" else display(plin)]
    labels = ["photo"]
    for r in a.renders:
        card_r = json.load(open(os.path.join(os.path.dirname(os.path.abspath(r)), "card.json")))
        card_r.setdefault("sensor", "canon_eos_5d_mkiv")
        card_r["white_patch_px"] = card.get("white_patch_px")
        if card_r["rig"] != a.rig:
            raise SystemExit(f"{r}: a {card_r['rig']} card")
        lin, info = develop(r, card_r, a.rig)
        info["set"] = card_r["set"]
        if a.rig == "scan":
            x0, y0, x1, y1 = card["white_patch_px"]
            lin_m = lin.copy()
            lin_m[y0 - 6:y1 + 6, x0 - 6:x1 + 6] = 0                  # the white patch is not leaf
        else:
            lin_m = lin
        _, rs = stats(lin_m, a.rig, pxmm)
        dE = float(np.linalg.norm(lab_of(rs["blade_median_rel_white"]) - lab_of(ps["blade_median_rel_white"])))
        rs["dE76_vs_photo"] = round(dE, 2)
        name = os.path.relpath(os.path.abspath(r), os.path.join(ROOT, "out/yinxing/card"))
        report["renders"][name] = {**rs, **info}
        panels.append(display(lin))
        labels.append(name.replace(".exr", ""))
    h = min(p.shape[0] for p in panels)
    row = np.concatenate([p[:h] for p in panels], 1)
    for i, t in enumerate(labels):
        x = sum(p.shape[1] for p in panels[:i]) + 12
        cv2.putText(row, t, (x, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(row, t, (x, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
    out = a.out or os.path.join(ROOT, "out/yinxing/card", f"compare_{a.rig}")
    os.makedirs(out, exist_ok=True)
    Image.fromarray(row).save(os.path.join(out, "side_by_side.png"))
    # a 1:1 crop of the middle of the distal half, all panels
    if a.rig == "lamp":
        crop = [p[150:450, 440:840] for p in panels]
        Image.fromarray(np.concatenate(crop, 1)).save(os.path.join(out, "side_by_side_crop.png"))
    json.dump(report, open(os.path.join(out, "compare.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))
    print("->", os.path.join(out, "side_by_side.png"))


if __name__ == "__main__":
    main()
