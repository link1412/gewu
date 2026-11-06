"""胭脂红 card, round 2: fit the softboxes to Met 1971.180.248 (docs/materials/yanzhi.md, "fitting the light").

Evidence, both read the same way off the photo and off every probe group's render (probe.py):
  1. the outer wall's luminance across the bowl, relative to the front: rows at 30 / 55 % of the red's height,
     columns at u = -0.8 .. 0.8 of the row's half width (the photo's sides are about 2.3 x the front);
  2. where the two softboxes reflect in the inside's far wall: the centroids of the bright blobs between the far
     rim and the near rim, in u (fraction of the bowl's half width from its axis) and v (fraction from the far rim's
     top to the near rim's red edge). The photo's blobs are clipped (JPEG 255), so only their place and size count.
A candidate light = one softbox pair (a probe group) + the top light at a weight + optionally a second pair at a
weight. Light adds, so each candidate is a weighted sum of the groups' raw images; it is developed and measured as
card.py develops a render. Score = rms of log(side / front) over the wall's columns + a weight x the blobs' miss.

    python3 -I materials/yanzhi/lightfit/fit.py features out/materials/yanzhi/lightfit/yz-probe-c050
    python3 -I materials/yanzhi/lightfit/fit.py fit out/materials/yanzhi/lightfit/yz-probe-c050 [--blob-weight 1]
"""
import argparse
import itertools
import json
import os
import sys

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import card  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "tools"))
from camera import read_raw  # noqa: E402

LUM = np.array([0.2126, 0.7152, 0.0722])
US = np.round(np.linspace(-0.8, 0.8, 9), 2)
FZ = (0.3, 0.55)


def geometry(lin, name):
    """card.regions' outline, plus the red mask's half width and centre per row."""
    box, info = card.regions(lin, name)
    return box, info


def wall(lin, box, info):
    """{(fz, u): linear rgb over the white} on the outer wall."""
    sm = ndi.gaussian_filter(lin, (2, 2, 0))
    R, G = sm[..., 0], sm[..., 1]
    red = ndi.binary_opening((R > 2 * G) & (R > 0.004 * np.percentile(R, 99.5)), iterations=2)
    w = card.median_box(lin, box["white"])
    s = max(2, int(round(0.012 * info["width"])))
    out = {}
    for fz in FZ:
        r = int(info["red_top"] + fz * (info["red_bot"] - info["red_top"]))
        c = np.nonzero(red[r])[0]
        hw, cc = 0.5 * (c.max() - c.min()), 0.5 * (c.max() + c.min())
        for u in US:
            out[(fz, float(u))] = card.median_box(lin, (r, int(round(cc + u * hw)), s)) / w
    return out


def blobs(lin, box, info, thresh):
    """The bright blobs on the inside: luminance over the white above thresh, between the far rim and the near
    rim's red edge; [(u, v, area_frac, w, h)] largest first."""
    w = card.median_box(lin, box["white"])
    Y = (lin / w) @ LUM
    m = Y > thresh
    m[:info["top"] - 3] = 0
    m[info["red_top"]:] = 0
    hw0 = info["width"] / 2
    xs_ = np.arange(m.shape[1])
    m[:, np.abs(xs_ - info["cx"]) > 0.95 * hw0] = 0      # inside the rim's ellipse, not the backdrop beside it
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(m)
    hw = info["width"] / 2
    H = info["red_top"] - info["top"]
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 0.00015 * hw * H * 4:
            continue
        out.append(((xs.mean() - info["cx"]) / hw, (ys.mean() - info["top"]) / H, len(ys) / (hw * H),
                    (xs.max() - xs.min()) / hw, (ys.max() - ys.min()) / H))
    return sorted(out, key=lambda b: -b[2])


def photo_features():
    from PIL import Image
    lin = card.photo_linear()
    box, info = geometry(lin, "photo")
    v = np.asarray(Image.open(card.PHOTO).convert("RGB")).astype(float)
    # clipped: sRGB >= 248 in all channels; over the white that is about lin 0.94 / 0.83
    w = card.median_box(lin, box["white"])
    clip = 0.94 / float(w @ LUM)
    return lin, box, info, wall(lin, box, info), blobs(lin, box, info, clip)


def backdrop(lin, box, info):
    """The backdrop over the white: the floor in front of the foot, and the wall beside the bowl (left, right)."""
    w = card.median_box(lin, box["white"])
    H, cx, W = info["red_bot"] - info["top"], int(info["cx"]), info["width"]
    s = max(3, int(0.02 * W))
    out = []
    r = min(int(info["top"] + 1.25 * H), lin.shape[0] - s - 1)
    out.append(card.median_box(lin, (r, cx, s)) / w)
    for fu in (-0.8, 0.8):
        out.append(card.median_box(lin, (max(int(info["top"] - 0.1 * H), s + 1), int(cx + fu * W / 2), s)) / w)
    return np.array(out)


def load_groups(d):
    q = json.load(open(os.path.join(d, "queued.json")))
    return {g: read_raw(os.path.join(d, f"x.{g}.exr")) for g in q["groups"]}


def develop(raw):
    return (raw * card._CAL["gains"]) @ card._CAL["C"].T


def shape(wl):
    """log(luminance / the front's), per (fz, u); the front = u 0 of the same row."""
    return np.array([np.log(float(wl[(fz, u)] @ LUM) / float(wl[(fz, 0.0)] @ LUM)) for fz in FZ for u in US])


def features(a):
    lin, box, info, wl, bl = photo_features()
    print("photo: geometry", info)
    for fz in FZ:
        print(f"  fz {fz}: Y/front " + " ".join(f"{float(wl[(fz, u)] @ LUM) / float(wl[(fz, 0.0)] @ LUM):.2f}" for u in US))
    for b in bl[:4]:
        print("  blob u {:+.3f} v {:.3f} area {:.4f} w {:.3f} h {:.3f}".format(*b))
    if a.dir:
        G = load_groups(a.dir)
        for g, raw in G.items():
            lin = develop(raw)
            box, info = geometry(lin, g)
            wl = wall(lin, box, info)
            bl = blobs(lin, box, info, 1.10)
            print(f"{g}: side/front (fz .3, u +-.6) {np.exp(shape(wl)[[1, 7]]).round(2)}; blobs " +
                  "; ".join("u {:+.2f} v {:.2f} a {:.4f}".format(*b[:3]) for b in bl[:3]))


def probe_data(d, geo=None):
    """geo: (box, info, red reference image) from another probe of the same camera and bowl (a bright backdrop can
    defeat card.regions' "white above the red" rule; the outline does not depend on the light)."""
    G = load_groups(d)
    tot = develop(sum(G.values()))
    box, info = geometry(tot, "sum") if geo is None else geo[:2]
    if geo is not None:
        tot = geo[2]
    D = {"box": box, "info": info, "ref": tot, "groups": list(G), "wall": {}, "white": {}, "back": {}, "blobs": {}}
    for g, raw in G.items():
        lin = develop(raw)
        D["white"][g] = card.median_box(lin, box["white"])
        D["wall"][g] = wall_abs(lin, box, info, tot)
        D["back"][g] = backdrop(lin, box, info) * D["white"][g]       # absolute again
        D["blobs"][g] = sorted(blobs(lin, box, info, 1.10)[:2], key=lambda x: x[0])
    return D


def evaluate(D, parts):
    W = sum(w * D["white"][g] for g, w in parts)
    wl = {k: sum(w * D["wall"][g][k] for g, w in parts) / W for k in D["wall"][parts[0][0]]}
    bk = sum(w * D["back"][g] for g, w in parts) / W
    return wl, bk


def fit(a):
    lin, pbox, pinfo, pwl, pbl = photo_features()
    target = shape(pwl)
    pback = backdrop(lin, pbox, pinfo) @ LUM
    pblobs = sorted(pbl[:2], key=lambda b: b[0])                   # left, right
    print(f"photo: side/front at u +-0.6 {np.exp(np.mean(target[[1, 7, 10, 16]])):.2f}; backdrop/white "
          f"{pback.round(2)}; blobs " + "; ".join("u {:+.2f} v {:.2f}".format(*b[:2]) for b in pblobs))
    rows = []
    geo = None
    for d in a.dirs:
        D = probe_data(d, geo)
        geo = geo or (D["box"], D["info"], D["ref"])
        pairs = [g for g in D["groups"] if g != "top"]
        for g1 in pairs:
            b = D["blobs"][g1]
            miss = (float(np.sqrt(np.mean([(p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for p, q in zip(pblobs, b)])))
                    if len(b) == 2 and b[0][0] < 0 < b[1][0] else 1.0)
            for g2 in [None] + pairs:
                if g2 == g1:
                    continue
                for w2 in ([0] if g2 is None else [0.25, 0.5, 1.0]):
                    for wt in (0, 0.25, 0.5, 1.0):
                        parts = [(g1, 1.0)] + ([(g2, w2)] if g2 else []) + ([("top", wt)] if wt else [])
                        wl, bk = evaluate(D, parts)
                        sh = shape(wl)
                        rms = float(np.sqrt(np.mean((sh - target) ** 2)))
                        brms = float(np.sqrt(np.mean(np.log((bk @ LUM) / pback) ** 2)))
                        rows.append((rms + a.back_weight * brms + a.blob_weight * miss, rms, brms, miss,
                                     os.path.basename(d), g1, g2, w2, wt, float(np.exp(np.mean(sh[[1, 7, 10, 16]]))),
                                     (bk @ LUM).round(2).tolist()))
    rows.sort(key=lambda r: r[0])
    for r in rows[:a.top]:
        print("score {:.3f} = wall {:.3f} + back {:.3f} + blob {:.3f} | {} | {} + {} x {} + top x {} | side/front {:.2f}"
              " back {}".format(*r))
    print("best per main pair:")
    seen = set()
    for r in rows:
        if (r[4], r[5]) not in seen and len(seen) < a.top:
            seen.add((r[4], r[5]))
            print("  {4} {5}: score {0:.3f} wall {1:.3f} back {2:.3f} blob {3:.3f}, + {6} x {7}, top x {8}, "
                  "side/front {9:.2f}".format(*r))
    json.dump([list(r) for r in rows[:200]], open(os.path.join(a.dirs[0], "fit.json"), "w"), indent=1, default=str)


def weights(a):
    """Strengths of a few groups (the first fixed at 1), by grid: wall shape + backdrop, as fit(); then, for the best,
    the inside's reflections at the photo's clip level (their place, and the peak over the white)."""
    lin, pbox, pinfo, pwl, pbl = photo_features()
    target = shape(pwl)
    pback = backdrop(lin, pbox, pinfo) @ LUM
    pw = card.median_box(lin, pbox["white"])
    clip = 0.94 / float(pw @ LUM)
    G0 = probe_data(a.geo) if a.geo else None
    D = probe_data(a.dir, None if G0 is None else (G0["box"], G0["info"], G0["ref"]))
    gs = D["groups"]
    grid = [0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    rows = []
    for ws in itertools.product(grid, repeat=len(gs) - 1):
        parts = [(gs[0], 1.0)] + [(g, w) for g, w in zip(gs[1:], ws) if w]
        wl, bk = evaluate(D, parts)
        sh = shape(wl)
        rms = float(np.sqrt(np.mean((sh - target) ** 2)))
        brms = float(np.sqrt(np.mean(np.log((bk @ LUM) / pback) ** 2)))
        rows.append((rms + a.back_weight * brms, rms, brms, dict(zip(gs, (1.0,) + ws)),
                     float(np.exp(np.mean(sh[[1, 7, 10, 16]]))), (bk @ LUM).round(2).tolist()))
    rows.sort(key=lambda r: r[0])
    print(f"photo: side/front {np.exp(np.mean(target[[1, 7, 10, 16]])):.2f}, backdrop {pback.round(2)}, clip {clip:.3f}")
    for r in rows[:a.top]:
        print("score {:.3f} wall {:.3f} back {:.3f} | {} | side/front {:.2f} back {}".format(*r))
    G = load_groups(a.dir)
    best = rows[0][3]
    raw = sum(w * G[g] for g, w in best.items())
    l = develop(raw)
    b = sorted(blobs(l, D["box"], D["info"], clip)[:2], key=lambda x: x[0])
    wv = card.median_box(l, D["box"]["white"])
    Y = (l / wv) @ LUM
    Y[:D["info"]["top"]] = 0
    Y[D["info"]["red_top"]:] = 0
    print("best: inside reflections at the photo's clip:", [tuple(np.round(x, 3)) for x in b],
          f"; peak / white {np.percentile(Y[Y > 0], 99.9):.2f}")
    print("photo:", [tuple(np.round(x, 3)) for x in sorted(pbl[:2], key=lambda x: x[0])])
    json.dump({"best": best, "rows": [[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rows[:30]]},
              open(os.path.join(a.dir, "weights.json"), "w"), indent=1)
    # the mixed raw, for card.py measure (--raw mix.pfm)
    from build import write_pfm
    write_pfm(os.path.join(a.dir, "mix.pfm"), raw)


def wall_abs(lin, box, info, ref):
    """wall() but with the red mask and per-row extent taken from `ref` (the sum of all groups), not lin."""
    sm = ndi.gaussian_filter(ref, (2, 2, 0))
    R, G = sm[..., 0], sm[..., 1]
    red = ndi.binary_opening((R > 2 * G) & (R > 0.004 * np.percentile(R, 99.5)), iterations=2)
    s = max(2, int(round(0.012 * info["width"])))
    out = {}
    for fz in FZ:
        r = int(info["red_top"] + fz * (info["red_bot"] - info["red_top"]))
        c = np.nonzero(red[r])[0]
        hw, cc = 0.5 * (c.max() - c.min()), 0.5 * (c.max() + c.min())
        for u in US:
            out[(fz, float(u))] = card.median_box(lin, (r, int(round(cc + u * hw)), s))
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("features")
    f.add_argument("dir", nargs="?")
    g = sub.add_parser("fit")
    g.add_argument("dirs", nargs="+")
    g.add_argument("--blob-weight", type=float, default=1.0)
    g.add_argument("--back-weight", type=float, default=0.5)
    g.add_argument("--top", type=int, default=15)
    w = sub.add_parser("weights")
    w.add_argument("dir")
    w.add_argument("--geo", default=None, help="a probe dir whose outline to use")
    w.add_argument("--back-weight", type=float, default=0.5)
    w.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    {"features": features, "fit": fit, "weights": weights}[a.cmd](a)


if __name__ == "__main__":
    main()
