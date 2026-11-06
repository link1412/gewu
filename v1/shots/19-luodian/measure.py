"""Shot 19 round 1, measured from the decoded film the way spec/shots.json measured the original (docs/shots/19-luodian.md).

    python3 -I shots/19-luodian/measure.py [--film out/film/film.mp4] [--json out/shots/19-luodian/r1/measure.json]

- arc: tools/spec_measure.py fit_arc on the middle frame (261) at 480x270, as tools/compare.py check does;
- sky luma and object mean RGB: spec_measure's definitions on the middle frame (sky: rows above the fitted arc - 8 and
  below 5 % of the height, BT.709 luma mean; object: every pixel below the arc + 8, mean RGB), and on every frame;
- motion: the mean |difference| of luma between neighbouring frames, sky and body (as docs/shots/19-dianluo.md);
- the shell pieces' colour change: each pixel of the floor is traced to the dish's floor (scene.Camera, frame 5's
  framing) and to its piece (pattern.py ids), eroded by 2 px; per piece with >= 8 such pixels at 960x540, its mean
  colour in each frame (CIELAB, D65, from the decoded film). Lightness and colour apart: the L* range, the largest
  a*b* distance between any two frames, the hue-angle range; a hue histogram at frame 261; the lacquer's L*.
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
import fit  # noqa: E402
import spec_measure as sm  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722])
LUT = os.path.join(ROOT, "out/shots/19-luodian/nacre_lut_wide.npz")


def stats(im8):
    """spec_measure on one 1920x1080 RGB frame (uint8): arc, sky luma, object mean."""
    im = im8.astype(np.float32).reshape(270, 4, 480, 4, 3).mean((1, 3))
    p, ax, ay, sag, inl, res = sm.fit_arc(im)
    yy, xx = np.mgrid[0:270, 0:480]
    arc = np.polyval(p, xx)
    lum = im @ LUMA
    sky = lum[(yy < arc - 8) & (yy > 0.05 * 270)]
    obj = im[yy > arc + 8]
    return {"apex_x": float(ax), "apex_y": float(ay), "sagitta": float(sag), "inliers": float(inl),
            "sky_luma": float(sky.mean()), "object_rgb": obj.mean(0).tolist()}


def lab(rgb8):
    c = rgb8 / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def piece_map(res=(960, 540)):
    """Piece id per pixel at res (0: lacquer or not the floor), from frame 5's framing and the pattern."""
    import scene
    import pattern
    fr = json.load(open(os.path.join(ROOT, "out/shots/19-luodian/r1/build/f05/framing.json")))
    cam = scene.Camera(fr["C"], math.radians(fr["beta_deg"]), fr["u"], res)
    W, H = res
    ext = (-50.0, 50.0, 14.0, 58.0)
    L = np.load(LUT)
    _, _, _, _, ids, _ = pattern.maps(ext, (float(L["d_nm"][0]), float(L["d_nm"][-1])), 19)        # ids in design space, image rows y down
    fx, fy = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
    d = (cam.fwd + (fx[..., None] - 0.5) * scene.SENSOR_W_MM / cam.v * cam.right
         + (0.5 - fy[..., None]) * cam.sensor_h / cam.v * cam.up)
    t = (scene.FLOOR_Z - cam.C[2]) / d[..., 2]
    P = cam.C + t[..., None] * d
    x, y = -P[..., 0], P[..., 1]                  # object -> design x
    i = ((x - ext[0]) / pattern.TEXEL_MM).astype(int)
    j = ((ext[3] - y) / pattern.TEXEL_MM).astype(int)
    ok = (t > 0) & (np.hypot(x, y) < pattern.FLOOR_R - 0.5) & (j >= 0) & (j < ids.shape[0]) & (i >= 0) & (i < ids.shape[1])
    out = np.zeros((H, W), np.int32)
    out[ok] = ids[j[ok], i[ok]]
    return out


def piece_map_floor(res=(960, 540)):
    """Pixels that see the dish's floor (inside the pattern's field radius)."""
    import scene
    import pattern
    fr = json.load(open(os.path.join(ROOT, "out/shots/19-luodian/r1/build/f05/framing.json")))
    cam = scene.Camera(fr["C"], math.radians(fr["beta_deg"]), fr["u"], res)
    W, H = res
    fx, fy = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
    d = (cam.fwd + (fx[..., None] - 0.5) * scene.SENSOR_W_MM / cam.v * cam.right
         + (0.5 - fy[..., None]) * cam.sensor_h / cam.v * cam.up)
    t = (scene.FLOOR_Z - cam.C[2]) / d[..., 2]
    P = cam.C + t[..., None] * d
    return (t > 0) & (np.hypot(P[..., 0], P[..., 1]) < pattern.FLOOR_R - 0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", default=os.path.join(ROOT, "out/film/film.mp4"))
    ap.add_argument("--json", default=os.path.join(ROOT, "out/shots/19-luodian/r1/measure.json"))
    a = ap.parse_args()
    frames = list(range(fit.F0, fit.F0 + fit.N))
    ours = fit.decode_frames(a.film, frames)
    orig = fit.decode_frames(os.path.join(ROOT, "ref/opus55.mp4"), frames)
    mid = frames.index(261)
    out = {"ours_mid": stats(ours[mid]), "orig_mid": stats(orig[mid]),
           "ours_frames": [stats(f) for f in ours], "orig_frames": [stats(f) for f in orig]}
    # motion: neighbouring-frame luma difference, sky rows and body rows (at 1080, columns 200-1720)
    def diffs(v, r0, r1):
        g = v[:, r0:r1, 200:1720].astype(np.float32) @ LUMA
        return [float(np.abs(g[k] - g[k - 1]).mean()) for k in range(1, len(g))]
    for name, v in (("ours", ours), ("orig", orig)):
        out[f"{name}_change_sky"] = diffs(v, 60, 440)
        out[f"{name}_change_body"] = diffs(v, 760, 1080)
    # pieces: each piece's pixels at 960x540, eroded by 2 px so the lacquer at its edges is left out (the checker's
    # way); per frame its mean CIELAB. Lightness and colour are reported apart (round 1's single dE76 counted
    # brightness flicker as colour change): the L* range over the 12 frames, the largest distance in the a*b* plane
    # between any two frames, and the hue-angle range (pieces with chroma >= 5 in every frame)
    from scipy import ndimage
    pm = piece_map()
    ids_all = np.unique(pm[pm > 0])
    pe = np.zeros_like(pm)
    for i in ids_all:
        m = ndimage.binary_erosion(pm == i, iterations=2)
        pe[m] = i
    small = ours.astype(np.float32).reshape(len(ours), 540, 2, 960, 2, 3).mean((2, 4))
    labs = lab(small)
    ids, counts = np.unique(pe[pe > 0], return_counts=True)
    ids = ids[counts >= 8]
    per = np.stack([np.stack([ndimage.mean(labs[k][..., c], pe, ids) for c in range(3)], -1) for k in range(len(ours))])
    Lr = per[..., 0].max(0) - per[..., 0].min(0)
    ab = per[..., 1:]
    dab = np.linalg.norm(ab[:, None] - ab[None], axis=-1).max((0, 1))
    C = np.hypot(ab[..., 0], ab[..., 1])
    h = np.degrees(np.arctan2(ab[..., 1], ab[..., 0]))
    hu = np.unwrap(np.radians(h), axis=0)
    hr = np.degrees(hu.max(0) - hu.min(0))
    chromatic = (C >= 5).all(0)
    hm = h[mid][C[mid] >= 10]
    hist, edges = np.histogram(hm, bins=12, range=(-180, 180))
    # the lacquer between the pieces (floor pixels at least 3 px from any piece), L* at the middle frame
    fl = piece_map_floor()
    lac = fl & ~ndimage.binary_dilation(pm > 0, iterations=3)
    out["lacquer_Lstar_mid"] = {"median": float(np.median(labs[mid][..., 0][lac])), "p90": float(np.percentile(labs[mid][..., 0][lac], 90))}
    q = lambda v: {"median": float(np.median(v)), "p90": float(np.percentile(v, 90))}
    out["pieces"] = {"seen_eroded_ge8px": int(len(ids)),
                     "L_range": q(Lr), "ab_change": q(dab) | {"share_gt5": float((dab > 5).mean()), "share_gt8": float((dab > 8).mean()),
                                                               "share_gt10": float((dab > 10).mean())},
                     "hue_range_deg_chromatic": q(hr[chromatic]) | {"pieces": int(chromatic.sum())},
                     "chroma_mid": q(C[mid]),
                     "hue_hist_mid_C_ge10": {"edges_deg": edges.tolist(), "counts": hist.tolist(), "pieces": int(len(hm))}}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    json.dump(out, open(a.json, "w"), indent=1)
    o, t = out["ours_mid"], out["orig_mid"]
    print(f"frame 261: apex ({o['apex_x']:.3f}, {o['apex_y']:.3f}) vs ({t['apex_x']:.3f}, {t['apex_y']:.3f}); sagitta "
          f"{100 * o['sagitta']:.2f}% vs {100 * t['sagitta']:.2f}%")
    print(f"sky luma {o['sky_luma']:.1f} vs {t['sky_luma']:.1f} (spec 19.7); object {np.round(o['object_rgb'], 1)} vs "
          f"{np.round(t['object_rgb'], 1)} (spec 72 76 95)")
    print("object per frame ours:", [np.round(f["object_rgb"], 0).astype(int).tolist() for f in out["ours_frames"]])
    print("sky per frame ours:", [round(f["sky_luma"], 1) for f in out["ours_frames"]])
    for name in ("ours", "orig"):
        print(f"{name} luma change per frame, sky {np.round(out[name + '_change_sky'], 2)}, body {np.round(out[name + '_change_body'], 2)}")
    print("pieces:", json.dumps(out["pieces"]))
    print("lacquer L*:", out["lacquer_Lstar_mid"])
    print(f"-> {a.json}")


if __name__ == "__main__":
    main()
