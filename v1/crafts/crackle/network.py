"""The shape of a crack network, measured the same way on a photo, on a render and on a simulated network.

    python3 -I crafts/crackle/network.py photo  --out out/crafts/crackle/net_met48503     # Met 48503, below the band
    python3 -I crafts/crackle/network.py sim    CRACKLE.json --out DIR [--px-mm 32.23] [--window X0 Y0 X1 Y1]
    python3 -I crafts/crackle/network.py image  PNG --px-mm 16.11 --out DIR [--mask MASK.png]

What is measured (our yardstick, S3; the definitions are in the code and in `stats`):
- junctions: degree-3 nodes split by their largest angle (T: >= 150 deg, Y: < 140 deg, between: 'T~Y'),
  degree-4 nodes (X when the branches form two straight pairs), free ends (degree 1, away from the border);
- segments (junction to junction): length, tortuosity (arc / chord), and the turning of the direction at 0.25 mm
  steps (RMS and the share of steps over 15 deg: 'kinks');
- cells: the complete faces (not touching the region's border), area and number of sides (junctions on their rim).

Lines in an image are found with an oriented ridge filter (bright or dark lines on the log of the luma: a Mexican
hat across, sigma 70 um, a Gaussian along, sigma 0.25 mm; the same filter as measure_ref.py), thresholded with
hysteresis, thinned, and turned into a graph: spurs shorter than 0.6 mm cut, junctions closer than 0.4 mm merged.
A simulated network is rasterised as a 1 px skeleton at the same px/mm and goes through the same graph code, so
both sides are counted alike; the image route also misses what is too faint to detect, as it does on the photo.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def srgb_to_lin(x):
    x = np.asarray(x, np.float64) / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def luma(lin):
    return lin @ np.array([0.2126, 0.7152, 0.0722])


# --- lines in an image ------------------------------------------------------------------------
def ridge_response(Y, px_mm, sw_um=70.0, sl_mm=0.25, n_orient=16, polarity=0):
    """Oriented Mexican-hat filter on log luma. polarity +1: bright lines only, -1: dark only, 0: both (|.|).
    Returns (strength, angle of the line's direction in radians, image axes x right, y down)."""
    from scipy.signal import fftconvolve
    sw = sw_um * 1e-3 * px_mm
    sl = sl_mm * px_mm
    n = int(2 * math.ceil(3.5 * max(sw, sl)) + 1)
    r = np.arange(n) - n // 2
    yk, xk = np.meshgrid(r, r, indexing="ij")
    logY = np.log(np.maximum(Y, 1e-6))
    ths = np.linspace(0, math.pi, n_orient, endpoint=False)
    out = []
    for th in ths:
        u = xk * math.cos(th) + yk * math.sin(th)
        v = -xk * math.sin(th) + yk * math.cos(th)
        k = -(1 - v ** 2 / sw ** 2) * np.exp(-v ** 2 / (2 * sw ** 2)) * np.exp(-u ** 2 / (2 * sl ** 2))
        k -= k.mean()
        k /= np.abs(k).sum()
        out.append(fftconvolve(logY, -k, mode="same"))     # > 0 on a bright line
    R = np.stack(out)
    if polarity > 0:
        R = np.maximum(R, 0)
    elif polarity < 0:
        R = np.maximum(-R, 0)
    else:
        R = np.abs(R)
    i = R.argmax(0)
    return R.max(0), ths[i]


def detect(Y, px_mm, region, lo=0.035, hi=0.07, min_len_mm=1.0, bridge_mm=0.6, sw_um=60.0, sl_mm=0.4):
    """Centre lines of the bright lines inside `region` (bool): the bright-ridge response, thinned across the line by
    non-maximum suppression, hysteresis thresholds (log-luma contrast units), pieces under min_len_mm dropped, and
    free ends bridged to a line or end within bridge_mm ahead (within 35 deg of the end's direction): a faint stretch
    breaks a line in two on the photo, and the network's topology needs it whole."""
    from skimage.filters import apply_hysteresis_threshold
    from skimage.morphology import skeletonize
    from skimage.draw import line as dline
    A, th = ridge_response(Y, px_mm, sw_um=sw_um, sl_mm=sl_mm, polarity=+1)
    A = np.where(region, A, 0.0)
    nx_, ny_ = -np.sin(th), np.cos(th)       # normal (x, y)
    H, W = A.shape
    yy, xx = np.mgrid[0:H, 0:W]
    a1 = ndi.map_coordinates(A, [yy + ny_, xx + nx_], order=1, mode="nearest")
    a2 = ndi.map_coordinates(A, [yy - ny_, xx - nx_], order=1, mode="nearest")
    ridge = (A >= a1) & (A >= a2)
    cand = apply_hysteresis_threshold(np.where(ridge, A, 0.0), lo, hi)
    cand = apply_hysteresis_threshold(np.where(ndi.binary_dilation(cand) , A, 0.0) * ndi.binary_dilation(cand), lo, hi)
    sk = skeletonize(ndi.binary_closing(cand, structure=np.ones((3, 3))))
    lab, n = ndi.label(sk, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    sk = sk & (sizes[lab] >= min_len_mm * px_mm) & (lab > 0)
    # bridge free ends
    nb = _neighbours(sk)
    ends = np.argwhere(sk & (nb == 1))
    lab, n = ndi.label(sk, structure=np.ones((3, 3)))
    reach = bridge_mm * px_mm
    pts = np.argwhere(sk)
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    for y, x in ends:
        # the end's direction: from the point 6 px back along its own component
        own = lab[y, x]
        near = tree.query_ball_point([y, x], 6)
        back = [pts[i] for i in near if lab[pts[i][0], pts[i][1]] == own]
        if len(back) < 3:
            continue
        b = np.mean(back, 0)
        d = np.array([y, x]) - b
        if np.linalg.norm(d) < 1e-6:
            continue
        d /= np.linalg.norm(d)
        best = None
        for i in tree.query_ball_point([y, x], reach):
            q = pts[i]
            v = q - np.array([y, x])
            L = np.linalg.norm(v)
            if L < 2 or (lab[q[0], q[1]] == own and L < 12):
                continue
            if lab[q[0], q[1]] == own:
                continue
            if np.dot(v / L, d) < math.cos(math.radians(35)):
                continue
            if best is None or L < best[0]:
                best = (L, q)
        if best is not None:
            rr, cc = dline(int(y), int(x), int(best[1][0]), int(best[1][1]))
            sk[rr, cc] = True
    return skeletonize(sk), A, th


# --- skeleton -> graph --------------------------------------------------------------------------
def _neighbours(sk):
    k = np.ones((3, 3), int)
    k[1, 1] = 0
    return ndi.convolve(sk.astype(int), k, mode="constant") * sk


def _trace(seg_mask, ends_hint):
    """Order the pixels of one 1-px-wide segment (a path) from one end to the other."""
    pts = set(map(tuple, np.argwhere(seg_mask)))
    if not pts:
        return []
    deg = {p: sum((p[0] + dy, p[1] + dx) in pts for dy, dx in NB) for p in pts}
    start = next((p for p in ends_hint if p in pts), None) or min(pts, key=lambda p: (deg[p], p))
    path = [start]
    seen = {start}
    cur = start
    while True:
        nxt = [(cur[0] + dy, cur[1] + dx) for dy, dx in NB if (cur[0] + dy, cur[1] + dx) in pts and (cur[0] + dy, cur[1] + dx) not in seen]
        if not nxt:
            break
        # prefer 4-neighbours (a staircase has both)
        nxt.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
        cur = nxt[0]
        path.append(cur)
        seen.add(cur)
    return path


class Graph:
    """nodes: list of dicts {yx (float), kind 'J'|'E'}; edges: list of dicts {a, b (node ids or -1), path (N,2) yx}."""

    def __init__(self, sk, px_mm, spur_mm=0.6, merge_mm=0.4, region=None):
        self.px = px_mm
        sk = sk.copy().astype(bool)
        for _ in range(3):            # cut spurs, repeat (cutting can expose new short ends)
            self._build(sk)
            cut = False
            for e in self.edges:
                L = self.edge_len(e)
                na, nb_ = (self.nodes[e["a"]] if e["a"] >= 0 else None), (self.nodes[e["b"]] if e["b"] >= 0 else None)
                free = (na is not None and na["kind"] == "E") or (nb_ is not None and nb_["kind"] == "E")
                atj = (na is not None and na["kind"] == "J") or (nb_ is not None and nb_["kind"] == "J")
                if free and atj and L < spur_mm * px_mm:
                    for y, x in np.round(e["path"]).astype(int):
                        sk[y, x] = False
                    cut = True
            if not cut:
                break
            from skimage.morphology import skeletonize
            sk = skeletonize(sk)
        self._build(sk)
        self._merge(merge_mm * px_mm)
        self.region = region

    def _build(self, sk):
        nb = _neighbours(sk)
        jmask = sk & (nb >= 3)
        emask = sk & (nb == 1)
        jlab, nj = ndi.label(ndi.binary_dilation(jmask, structure=np.ones((3, 3))) & sk, structure=np.ones((3, 3)))
        self.nodes = []
        for i, sl in enumerate(ndi.find_objects(jlab)):
            yy, xx = np.nonzero(jlab[sl] == i + 1)
            self.nodes.append({"yx": np.array([yy.mean() + sl[0].start, xx.mean() + sl[1].start]), "kind": "J", "pix": i + 1})
        ey, ex = np.nonzero(emask & (jlab == 0))
        e_ids = {}
        for y, x in zip(ey, ex):
            e_ids[(y, x)] = len(self.nodes)
            self.nodes.append({"yx": np.array([y, x], float), "kind": "E"})
        rest = sk & (jlab == 0)
        slab, ns = ndi.label(rest, structure=np.ones((3, 3)))
        self.edges = []
        jdil = ndi.binary_dilation(jlab > 0, structure=np.ones((3, 3)))
        for i, sl in enumerate(ndi.find_objects(slab)):
            m = slab[sl] == i + 1
            off = np.array([sl[0].start, sl[1].start])
            pts = np.argwhere(m) + off
            ends = []
            touch = []
            for p in pts:
                if tuple(p) in e_ids:
                    ends.append(tuple(p))
                elif jdil[p[0], p[1]]:
                    # which junction cluster(s) does it touch
                    y0, x0 = p
                    labs = set(jlab[max(0, y0 - 1):y0 + 2, max(0, x0 - 1):x0 + 2].ravel()) - {0}
                    for l in labs:
                        touch.append((tuple(p), l))
            path = _trace(m, [tuple(np.array(q) - off) for q in ends] + [tuple(np.array(t[0]) - off) for t in touch])
            path = np.array(path) + off if path else pts
            ids = []
            for q in (tuple(path[0]), tuple(path[-1])):
                if q in e_ids:
                    ids.append(e_ids[q])
                else:
                    labs = [l for (pp, l) in touch if pp == q]
                    ids.append(next((k for k, n_ in enumerate(self.nodes) if n_.get("pix") == labs[0]), -1) if labs else -1)
            if len(path) == 1 and ids[0] == ids[1] and len(set(l for _, l in touch)) == 2:
                ls = sorted(set(l for _, l in touch))
                ids = [next(k for k, n_ in enumerate(self.nodes) if n_.get("pix") == ls[0]),
                       next(k for k, n_ in enumerate(self.nodes) if n_.get("pix") == ls[1])]
            self.edges.append({"a": ids[0], "b": ids[1], "path": path.astype(float)})
        # junction clusters directly adjacent to each other with no pixels between: join them by a zero edge
        self._attach()

    def _attach(self):
        """Edge endpoints: put the node's position at the start/end of the path so directions are measured from it."""
        for e in self.edges:
            p = e["path"]
            if e["a"] >= 0 and self.nodes[e["a"]]["kind"] == "J":
                e["path"] = np.vstack([self.nodes[e["a"]]["yx"], p])
            if e["b"] >= 0 and self.nodes[e["b"]]["kind"] == "J":
                e["path"] = np.vstack([e["path"], self.nodes[e["b"]]["yx"]])

    def edge_len(self, e):
        p = e["path"]
        return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()) if len(p) > 1 else 0.0

    def _merge(self, dmin):
        """Contract edges shorter than dmin between two junctions (two nearby T's that a thick line made, a junction
        split by the thinning)."""
        changed = True
        while changed:
            changed = False
            for k, e in enumerate(self.edges):
                a, b = e["a"], e["b"]
                if a >= 0 and b >= 0 and a != b and self.nodes[a]["kind"] == "J" and self.nodes[b]["kind"] == "J" \
                        and self.edge_len(e) < dmin:
                    na, nb_ = self.nodes[a], self.nodes[b]
                    na["yx"] = 0.5 * (na["yx"] + nb_["yx"])
                    for f in self.edges:
                        if f["a"] == b:
                            f["a"] = a
                        if f["b"] == b:
                            f["b"] = a
                    nb_["kind"] = "dead"
                    del self.edges[k]
                    changed = True
                    break

    def degree(self):
        d = np.zeros(len(self.nodes), int)
        for e in self.edges:
            for v in (e["a"], e["b"]):
                if v >= 0:
                    d[v] += 1
            if e["a"] == e["b"] and e["a"] >= 0:
                pass
        return d


def _branch_dir(G, e, node, r_px):
    """Unit direction (yx) from `node` along edge e, to the point at arc distance r_px."""
    p = e["path"]
    if e["b"] == node and e["a"] != node:
        p = p[::-1]
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    if s[-1] < 1e-9:
        return None
    t = min(r_px, s[-1])
    q = np.array([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])])
    v = q - G.nodes[node]["yx"]
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else None


def stats(G, region, border_mm=0.6, branch_mm=0.5, step_mm=0.25):
    """Junction types, free ends, segment shape, cells (see the module's doc)."""
    px = G.px
    deg = G.degree()
    inner = ndi.binary_erosion(region, iterations=max(1, int(border_mm * px)))
    def inside(yx):
        y, x = int(round(yx[0])), int(round(yx[1]))
        return 0 <= y < inner.shape[0] and 0 <= x < inner.shape[1] and inner[y, x]
    J = {"T": 0, "Y": 0, "T~Y": 0, "X": 0, "4-other": 0, "5+": 0}
    largest = []
    for k, n in enumerate(G.nodes):
        if n["kind"] != "J" or not inside(n["yx"]):
            continue
        es = [e for e in G.edges if e["a"] == k or e["b"] == k]
        dirs = []
        for e in es:
            for _ in range(2 if e["a"] == e["b"] == k else 1):
                d = _branch_dir(G, e, k, branch_mm * px)
                if d is not None:
                    dirs.append(d)
        if len(dirs) == 3:
            ang = sorted(math.atan2(d[0], d[1]) for d in dirs)
            gaps = np.diff(ang + [ang[0] + 2 * math.pi])
            mx = math.degrees(gaps.max())
            largest.append(mx)
            J["T" if mx >= 150 else ("Y" if mx < 140 else "T~Y")] += 1
        elif len(dirs) == 4:
            ang = np.array(sorted(math.atan2(d[0], d[1]) for d in dirs))
            opp = [abs(((ang[i + 2] - ang[i]) % (2 * math.pi)) - math.pi) for i in range(2)]
            J["X" if max(opp) < math.radians(30) else "4-other"] += 1
        elif len(dirs) >= 5:
            J["5+"] += 1
    ends = sum(1 for k, n in enumerate(G.nodes) if n["kind"] == "E" and inside(n["yx"]))
    # segments between two junctions inside the region
    segs = []
    for e in G.edges:
        a, b = e["a"], e["b"]
        if a < 0 or b < 0 or a == b:
            continue
        if G.nodes[a]["kind"] != "J" or G.nodes[b]["kind"] != "J" or not (inside(G.nodes[a]["yx"]) and inside(G.nodes[b]["yx"])):
            continue
        p = e["path"]
        L = G.edge_len(e) / px
        chord = float(np.linalg.norm(p[-1] - p[0])) / px
        if L < 0.3:
            continue
        # direction at step_mm spacing along the (lightly smoothed) path
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))] / px
        if s[-1] < 3 * step_mm:
            turns = []
        else:
            t = np.arange(0, s[-1] + 1e-9, step_mm)
            q = np.c_[np.interp(t, s, ndi.gaussian_filter1d(p[:, 0], 1.0, mode="nearest")),
                      np.interp(t, s, ndi.gaussian_filter1d(p[:, 1], 1.0, mode="nearest"))]
            d = np.diff(q, axis=0)
            a_ = np.unwrap(np.arctan2(d[:, 0], d[:, 1]))
            turns = list(np.degrees(np.diff(a_)))
        segs.append({"len_mm": L, "tort": L / max(chord, 1e-9), "turns": turns})
    turns = np.array([t for s_ in segs for t in s_["turns"]]) if segs else np.zeros(0)
    # cells
    walls = np.zeros(region.shape, bool)
    for e in G.edges:
        p = np.round(e["path"]).astype(int)
        ok = (p[:, 0] >= 0) & (p[:, 0] < walls.shape[0]) & (p[:, 1] >= 0) & (p[:, 1] < walls.shape[1])
        walls[p[ok, 0], p[ok, 1]] = True
    walls = ndi.binary_dilation(walls, iterations=2)
    lab, n = ndi.label(region & ~walls)
    touch = set(np.unique(lab[ndi.binary_dilation(~region, iterations=3) & (lab > 0)]))
    areas, sides = [], []
    jn = [(k, n_["yx"]) for k, n_ in enumerate(G.nodes) if n_["kind"] == "J"]
    for i, sl in enumerate(ndi.find_objects(lab)):
        if sl is None or (i + 1) in touch:
            continue
        a_ = float((lab[sl] == i + 1).sum()) / px ** 2
        if a_ < 0.05:
            continue
        rim = ndi.binary_dilation(lab == i + 1, iterations=4)
        sides.append(sum(1 for k, yx in jn if rim[min(int(round(yx[0])), rim.shape[0] - 1), min(int(round(yx[1])), rim.shape[1] - 1)]))
        areas.append(a_)
    nJ3 = J["T"] + J["Y"] + J["T~Y"]
    nodes_all = nJ3 + J["X"] + J["4-other"] + J["5+"]
    lens = np.array([s_["len_mm"] for s_ in segs]) if segs else np.zeros(0)
    tort = np.array([s_["tort"] for s_ in segs]) if segs else np.zeros(0)
    area_mm2 = float(region.sum()) / px ** 2
    total_len = sum(G.edge_len(e) for e in G.edges) / px
    pct = lambda a, q: [round(float(np.percentile(a, x)), 3) for x in q] if len(a) else None
    return {
        "region_mm2": round(area_mm2, 1),
        "line_length_mm_per_mm2": round(total_len / area_mm2, 4),
        "junctions": J,
        "junction_fractions": {k: round(v / max(nodes_all, 1), 3) for k, v in J.items()},
        "deg3_largest_angle_deg_p10_p50_p90": pct(np.array(largest), (10, 50, 90)),
        "free_ends": ends,
        "free_ends_per_junction": round(ends / max(nodes_all, 1), 3),
        "segments": len(segs),
        "segment_len_mm_p10_p50_p90": pct(lens, (10, 50, 90)),
        "tortuosity_p50_p90": pct(tort, (50, 90)),
        "turn_per_0.25mm_rms_deg": round(float(np.sqrt(np.mean(turns ** 2))), 2) if len(turns) else None,
        "kinks_over_15deg_per_mm": round(float((np.abs(turns) > 15).sum() / max(lens.sum(), 1e-9)), 3) if len(turns) else None,
        "cells_complete": len(areas),
        "cell_area_mm2_p10_p50_p90": pct(np.array(areas), (10, 50, 90)),
        "cell_sqrt_mean_area_mm": round(math.sqrt(float(np.mean(areas))), 2) if areas else None,
        "cell_sides_mean": round(float(np.mean(sides)), 2) if sides else None,
        "cell_sides_hist": {str(k): int(v) for k, v in zip(*np.unique(sides, return_counts=True))} if sides else {},
    }


def overlay(rgb8, G, path, scale=1.0):
    """The graph drawn over the image: edges green, T red, Y blue, T~Y yellow, X magenta, free ends cyan."""
    from PIL import ImageDraw
    im = Image.fromarray(rgb8).convert("RGB")
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    dr = ImageDraw.Draw(im)
    for e in G.edges:
        p = e["path"] * scale
        dr.line([(x, y) for y, x in p], fill=(40, 220, 40), width=1)
    deg = G.degree()
    for k, n in enumerate(G.nodes):
        y, x = n["yx"] * scale
        if n["kind"] == "E":
            c = (0, 230, 230)
        elif n["kind"] == "J":
            es = [e for e in G.edges if e["a"] == k or e["b"] == k]
            dirs = [d for e in es if (d := _branch_dir(G, e, k, 0.5 * G.px)) is not None]
            if len(dirs) == 3:
                ang = sorted(math.atan2(d[0], d[1]) for d in dirs)
                mx = math.degrees(np.diff(ang + [ang[0] + 2 * math.pi]).max())
                c = (255, 40, 40) if mx >= 150 else ((60, 90, 255) if mx < 140 else (255, 230, 0))
            else:
                c = (255, 0, 255)
        else:
            continue
        r = 4
        dr.ellipse([x - r, y - r, x + r, y + r], outline=c, width=2)
    im.save(path)


# --- simulated network -> skeleton ----------------------------------------------------------------
def rasterise(cracks, px_mm, window):
    """1 px skeleton of the polylines (mm, y up) inside window (x0, y0, x1, y1) mm; rows from y1 down."""
    from skimage.draw import line as dline
    from skimage.morphology import skeletonize
    x0, y0, x1, y1 = window
    W, H = int(round((x1 - x0) * px_mm)), int(round((y1 - y0) * px_mm))
    sk = np.zeros((H, W), bool)
    for c in cracks:
        p = np.asarray(c["pts"], float)
        X = (p[:, 0] - x0) * px_mm
        Y = (y1 - p[:, 1]) * px_mm
        for i in range(len(p) - 1):
            rr, cc = dline(int(round(Y[i])), int(round(X[i])), int(round(Y[i + 1])), int(round(X[i + 1])))
            ok = (rr >= 0) & (rr < H) & (cc >= 0) & (cc < W)
            sk[rr[ok], cc[ok]] = True
    return skeletonize(ndi.binary_dilation(sk, structure=np.ones((3, 3)))), (H, W)


def synth_image(cracks, px_mm, window, rng, fwhm_um=110.0, contrast=0.30, sigma_ln=0.8, corr_mm=2.0, speckle_rms=0.065,
                psf_px=0.75):
    """A luma image of a simulated network as the photo would show it, for measuring it the photo's way: lines of
    the photo's measured cross profile (Gaussian, FWHM 110 um: lines_met48503.json, blocks' median) and median
    contrast 0.30, varying along each line as a lognormal (sigma 0.8, correlated over 2 mm: the first round's
    reading of the photo's 1 mm blocks), on a speckle of the photo's measured rms (DoG 0.7-3 px: 6.5%), blurred
    by the photo's PSF (sigma 0.75 px, from its smallest specks). Returns luma (H, W)."""
    x0, y0, x1, y1 = window
    W, H = int(round((x1 - x0) * px_mm)), int(round((y1 - y0) * px_mm))
    acc = np.zeros((H, W))
    sig = fwhm_um * 1e-3 / 2.3548 * px_mm
    for c in cracks:
        p = np.asarray(c["pts"], float)
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        if s[-1] < 1e-6:
            continue
        t = np.arange(0, s[-1], 0.5 / px_mm)
        q = np.c_[np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])]
        k = max(1.0, corr_mm * px_mm * 2)
        f = ndi.gaussian_filter1d(rng.standard_normal(len(t) + int(8 * k)), k)[int(4 * k):int(4 * k) + len(t)]
        f = f / (f.std() + 1e-9) if len(t) > 8 else rng.standard_normal(len(t))
        amp = contrast * np.exp(sigma_ln * f - 0.5 * sigma_ln ** 2)
        X = (q[:, 0] - x0) * px_mm
        Y = (y1 - q[:, 1]) * px_mm
        ok = (X >= 0) & (X < W - 1) & (Y >= 0) & (Y < H - 1)
        np.add.at(acc, (Y[ok].astype(int), X[ok].astype(int)), amp[ok] * 0.5)
    lines = ndi.gaussian_filter(acc, sig) * (2 * math.pi * sig ** 2) / (sig * math.sqrt(2 * math.pi))
    noise = ndi.gaussian_filter(rng.standard_normal((H, W)), 0.8)
    dog = ndi.gaussian_filter(noise, 0.7) - ndi.gaussian_filter(noise, 3.0)
    noise *= speckle_rms / dog.std()
    Y = 0.03 * (1 + np.minimum(lines, 1.5) + noise)
    return ndi.gaussian_filter(np.maximum(Y, 1e-4), psf_px)


# --- the photo ------------------------------------------------------------------------------------
def photo_region(which="lower"):
    """Met 48503: the glaze below the dark band (the region measure_ref.py measures; which='lower'), or all the glaze
    but the band (which='all': the dome above it is curved and foreshortened, so its lengths and areas are not used,
    only its junctions), as a bool mask at full size, recomputed with measure_ref's own steps."""
    sys.path.insert(0, os.path.join(ROOT, "materials", "guan_glaze"))
    import measure_ref as mr
    M = json.load(open(os.path.join(ROOT, "out/materials/guan_glaze/measured_met48503.json")))
    im = np.asarray(Image.open(os.path.join(ROOT, M["photo"])).convert("RGB"))
    H, W = im.shape[:2]
    lin = srgb_to_lin(im)
    bd = mr.fit_backdrop(lin)
    chroma = ndi.gaussian_filter(lin[..., 1] / np.maximum(lin[..., 0], 1e-6), 3)
    rel = ndi.gaussian_filter(luma(lin), 3) / luma(bd)
    m = ndi.binary_opening((rel < 0.70) | (chroma > 1.12), iterations=3)
    lab, n = ndi.label(m)
    best = ndi.binary_fill_holes(lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1))
    pxmm = M["scale"]["px_per_mm"]
    inner = ndi.binary_erosion(best, iterations=int(0.8 * pxmm))
    Y = luma(lin)
    ys8 = ndi.gaussian_filter(Y, 6 * pxmm / 33)
    band = inner & (ys8 < 0.55 * np.median(Y[inner]))
    lb, nb = ndi.label(band)
    band = lb == (np.argmax(np.bincount(lb.ravel())[1:]) + 1)
    band = ndi.binary_dilation(band, iterations=int(0.8 * pxmm))
    g = inner & ~band
    ys, xs = np.nonzero(band)
    colmax = np.full(W, -1)
    np.maximum.at(colmax, xs, ys)
    xc = np.nonzero(colmax >= 0)[0]
    pb = np.polyfit(xc, colmax[xc], 2)
    yy, xx = np.mgrid[0:H, 0:W]
    below = yy > np.polyval(pb, xx) + 1.5 * pxmm
    lower = g & below & (xx > xc.min()) & (xx < xc.max())
    return im, lin, (lower if which == "lower" else g), pxmm


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("photo")
    p.add_argument("--out", required=True)
    p.add_argument("--px-mm", type=float, help="resample the photo to this scale first (e.g. 16.11, the preview's)")
    p.add_argument("--region", default="lower", choices=["lower", "all"])
    p.add_argument("--lo", type=float, default=0.035)
    p.add_argument("--hi", type=float, default=0.07)
    s = sub.add_parser("sim")
    s.add_argument("crackle")
    s.add_argument("--out", required=True)
    s.add_argument("--px-mm", type=float, default=32.23)
    s.add_argument("--window", type=float, nargs=4, help="x0 y0 x1 y1 mm (default: the simulated patch minus 3 mm)")
    s.add_argument("--gen", type=int, default=9, help="only cracks of generation <= this")
    s.add_argument("--as-photo", action="store_true", help="draw it as the photo would show it (synth_image) and "
                                                          "find the lines in that image, as on the photo")
    s.add_argument("--seed", type=int, default=1)
    i = sub.add_parser("image")
    i.add_argument("png")
    i.add_argument("--px-mm", type=float, required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--mask", help="PNG, white = region (default: all but a 3% border)")
    i.add_argument("--crop", type=int, nargs=4, help="x0 y0 x1 y1 px: measure only this box")
    i.add_argument("--lo", type=float, default=0.035)
    i.add_argument("--hi", type=float, default=0.07)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.cmd == "photo":
        im, lin, region, px = photo_region(a.region)
        if a.px_mm:
            f = a.px_mm / px
            im = np.asarray(Image.fromarray(im).resize((int(im.shape[1] * f), int(im.shape[0] * f)), Image.LANCZOS))
            lin = srgb_to_lin(im)
            region = np.asarray(Image.fromarray(region.astype(np.uint8) * 255).resize((im.shape[1], im.shape[0]), Image.NEAREST)) > 127
            px = a.px_mm
        ys, xs = np.nonzero(region)
        sl = (slice(ys.min() - 10, ys.max() + 10), slice(xs.min() - 10, xs.max() + 10))
        im, lin, region = im[sl], lin[sl], region[sl]
        sk, A, th = detect(luma(lin), px, region, a.lo, a.hi)
        G = Graph(sk, px, region=region)
        st = stats(G, region)
        st["source"] = f"Met 48503 (ref/guan/met48503_0.jpg), region {a.region}" + (f", resampled to {a.px_mm} px/mm" if a.px_mm else "")
        st["px_per_mm"] = px
        overlay(im, G, os.path.join(a.out, "overlay.png"))
    elif a.cmd == "sim":
        C = json.load(open(a.crackle))
        P = C["params"]
        win = a.window or (P["x_range"][0] + 3, P["y_range"][0] + 3, P["x_range"][1] - 3, P["y_range"][1] - 3)
        cr = [c for c in C["cracks"] if c["gen"] <= a.gen]
        if a.as_photo:
            Y = synth_image(cr, a.px_mm, win, np.random.default_rng(a.seed))
            region = np.zeros(Y.shape, bool)
            region[8:-8, 8:-8] = True
            sk, _, _ = detect(Y, a.px_mm, region)
            H, W = Y.shape
        else:
            sk, (H, W) = rasterise(cr, a.px_mm, win)
            region = np.ones((H, W), bool)
        G = Graph(sk, a.px_mm, region=region)
        st = stats(G, region)
        st["source"] = (f"simulated network {a.crackle}, generations <= {a.gen}, window {win} mm, "
                        + ("drawn as the photo shows lines and found again (synth_image)" if a.as_photo else "all cracks (none missed)"))
        st["px_per_mm"] = a.px_mm
        overlay((np.full((H, W, 3), 90) + 120 * sk[..., None]).astype(np.uint8), G, os.path.join(a.out, "overlay.png"))
    else:
        im = np.asarray(Image.open(a.png).convert("RGB"))
        if a.crop:
            x0, y0, x1, y1 = a.crop
            im = im[y0:y1, x0:x1]
        lin = srgb_to_lin(im)
        if a.mask:
            region = np.asarray(Image.open(a.mask).convert("L")) > 127
            if a.crop:
                region = region[y0:y1, x0:x1]
        else:
            region = np.zeros(im.shape[:2], bool)
            b = int(0.03 * im.shape[1])
            region[b:-b, b:-b] = True
        sk, A, th = detect(luma(lin), a.px_mm, region, a.lo, a.hi)
        G = Graph(sk, a.px_mm, region=region)
        st = stats(G, region)
        st["source"] = a.png
        st["px_per_mm"] = a.px_mm
        overlay(im, G, os.path.join(a.out, "overlay.png"))
    json.dump(st, open(os.path.join(a.out, "network.json"), "w"), indent=1)
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
