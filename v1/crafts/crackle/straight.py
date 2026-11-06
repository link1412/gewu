"""Straightness of crack lines at 0.25-5 mm, measured the same way on the photo (Met 48503), on a card render and on
the generator's network drawn as the photo shows lines (network.synth_image), all found by network.detect.

- chains: the found graph's edges joined through junctions where two branches are within 30 deg of straight on (the
  crack that runs through a T), so the long-wave shape is seen across junctions;
- turn(l): rms of the angle between consecutive chords of length l along the chains (sliding, 0.1 mm step).
  A smooth meander of curvature k gives turn ~ k l (slope 1 in log-log); straight runs with sharp kinks give a turn
  that grows slower than l (slope < 1) and a heavy-tailed fine-scale turn (kurtosis >> 3);
- tortuosity: path length / chord between two junctions (segments >= 1 mm), and for whole chains >= 5 mm;
- sagitta(l): rms of the largest distance of the path from the chord of a window of length l, over l.

    python3 -I crafts/crackle/straight.py OUT.json photo | render DIR... | sim CRACKLE.json [GEN] | exact CRACKLE.json [x0,y0,x1,y1]
(S3, the Guan glaze card, round 2: docs/materials/guan_glaze.md, "Network")."""
import sys, os, json, math
import numpy as np
from scipy import ndimage as ndi
ROOT = "."
for d in ("tools", "crafts/crackle", "materials/guan_glaze"):
    sys.path.insert(0, os.path.join(ROOT, d))
import network as nw

PX = 16.11
LS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0]


def chains(G, r_mm=0.5):
    px = G.px
    ends = {}
    for i, e in enumerate(G.edges):
        if e["a"] == e["b"]:
            continue
        for side, k in ((0, e["a"]), (1, e["b"])):
            if k >= 0 and G.nodes[k]["kind"] == "J":
                ends.setdefault(k, []).append((i, side))
    pair = {}
    for k, lst in ends.items():
        dirs = []
        for (i, side) in lst:
            d = nw._branch_dir(G, G.edges[i], k, r_mm * px)
            dirs.append(d)
        cand = []
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                if dirs[a] is None or dirs[b] is None or lst[a][0] == lst[b][0]:
                    continue
                c = float(np.dot(dirs[a], dirs[b]))
                if c < -math.cos(math.radians(30)):
                    cand.append((c, a, b))
        used = set()
        for c, a, b in sorted(cand):
            if a in used or b in used:
                continue
            used |= {a, b}
            pair[lst[a]] = lst[b]
            pair[lst[b]] = lst[a]
    seen = set()
    out = []
    for i0 in range(len(G.edges)):
        if i0 in seen or G.edges[i0]["a"] == G.edges[i0]["b"]:
            continue
        seen.add(i0)
        seq = [G.edges[i0]["path"]]
        # forward from side 1
        cur = (i0, 1)
        while cur in pair:
            j, sj = pair[cur]
            if j in seen:
                break
            seen.add(j)
            p = G.edges[j]["path"]
            seq.append(p if sj == 0 else p[::-1])
            cur = (j, 1 - sj)
        cur = (i0, 0)
        while cur in pair:
            j, sj = pair[cur]
            if j in seen:
                break
            seen.add(j)
            p = G.edges[j]["path"]
            seq.insert(0, p[::-1] if sj == 0 else p)
            cur = (j, 1 - sj)
        out.append(np.vstack(seq))
    return out


def resample(p, px, step_mm=0.05):
    p = np.c_[ndi.gaussian_filter1d(p[:, 0], 1.0, mode="nearest"), ndi.gaussian_filter1d(p[:, 1], 1.0, mode="nearest")] / px
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    keep = np.r_[True, np.diff(s) > 1e-9]
    p, s = p[keep], s[keep]
    if s[-1] < 0.3:
        return None, 0
    t = np.arange(0, s[-1], step_mm)
    return np.c_[np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], s[-1]


def measure(G):
    px = G.px
    ch = chains(G)
    turns = {l: [] for l in LS}
    sag = {l: [] for l in LS}
    tort_chain = []
    fine = []
    total = 0.0
    for c in ch:
        q, L = resample(c, px)
        if q is None:
            continue
        total += L
        n = len(q)
        if L >= 5:
            tort_chain.append(L / np.linalg.norm(q[-1] - q[0]))
        for l in LS:
            m = int(round(l / 0.05))
            if 2 * m >= n:
                continue
            idx = np.arange(0, n - 2 * m, 2)            # 0.1 mm sliding
            d1 = q[idx + m] - q[idx]
            d2 = q[idx + 2 * m] - q[idx + m]
            a = np.arctan2(d1[:, 0], d1[:, 1]) - np.arctan2(d2[:, 0], d2[:, 1])
            a = (a + np.pi) % (2 * np.pi) - np.pi
            turns[l].extend(np.degrees(a).tolist())
            if l == 0.25:
                fine.extend(np.degrees(a[::3]).tolist())  # non-overlapping
            # sagitta of windows of length l
            idx2 = np.arange(0, n - m, 2)
            for i in idx2[::3]:
                seg = q[i:i + m + 1]
                ab = seg[-1] - seg[0]
                nn = np.linalg.norm(ab)
                if nn < 1e-9:
                    continue
                dist = np.abs((seg[:, 0] - seg[0, 0]) * ab[1] - (seg[:, 1] - seg[0, 1]) * ab[0]) / nn
                sag[l].append(dist.max() / l)
    # junction-to-junction tortuosity
    tj = []
    for e in G.edges:
        a, b = e["a"], e["b"]
        if a < 0 or b < 0 or a == b or G.nodes[a]["kind"] != "J" or G.nodes[b]["kind"] != "J":
            continue
        L = G.edge_len(e) / px
        if L < 1.0:
            continue
        tj.append(L / (np.linalg.norm(e["path"][-1] - e["path"][0]) / px))
    rms = {l: (round(float(np.sqrt(np.mean(np.square(turns[l])))), 2) if len(turns[l]) > 20 else None) for l in LS}
    f = np.array(fine)
    kurt = float(np.mean(f ** 4) / np.mean(f ** 2) ** 2) if len(f) > 20 else None
    sl = None
    if rms[0.5] and rms[2.0]:
        sl = round(math.log(rms[2.0] / rms[0.5]) / math.log(4), 3)
    pc = lambda a: [round(float(np.percentile(a, x)), 3) for x in (50, 90)] if len(a) else None
    return {"chains": len(ch), "chain_length_mm": round(total, 1),
            "turn_rms_deg_by_chord_mm": {str(l): rms[l] for l in LS},
            "samples_by_chord_mm": {str(l): len(turns[l]) for l in LS},
            "turn_loglog_slope_0.5_2mm": sl,
            "turn_0.25mm_kurtosis": round(kurt, 2) if kurt else None,
            "sagitta_over_l_rms": {str(l): (round(float(np.sqrt(np.mean(np.square(sag[l])))), 4) if len(sag[l]) > 20 else None) for l in LS},
            "tortuosity_junction_to_junction_p50_p90": pc(np.array(tj)), "segments_ge_1mm": len(tj),
            "tortuosity_chains_ge_5mm_p50_p90": pc(np.array(tort_chain)), "chains_ge_5mm": len(tort_chain)}


def main():
    out, mode = sys.argv[1], sys.argv[2]
    if mode == "photo":
        from PIL import Image
        im, lin, region, px = nw.photo_region("lower")
        f = PX / px
        im = np.asarray(Image.fromarray(im).resize((int(im.shape[1] * f), int(im.shape[0] * f)), Image.LANCZOS))
        lin = nw.srgb_to_lin(im)
        region = np.asarray(Image.fromarray(region.astype(np.uint8) * 255).resize((im.shape[1], im.shape[0]), Image.NEAREST)) > 127
        sk, _, _ = nw.detect(nw.luma(lin), PX, region)
        G = nw.Graph(sk, PX, region=region)
        src = "Met 48503 photo, region lower, at 16.11 px/mm"
    elif mode == "render":
        import camera, card
        dirs = sys.argv[3:]
        cam = json.load(open(os.path.join(dirs[0], "camera.json")))
        cal = camera.calibrate(camera.Spectra(cam["sensor"]), camera.balance_spectrum(cam))
        lin = np.mean([np.maximum((camera.read_raw(os.path.join(d, "raw.exr")) * cal["gains"]) @ cal["C"].T, 0) for d in dirs], 0)
        H, W = lin.shape[:2]
        M = json.load(open(card.MEASURED))
        px = M["scale"]["px_per_mm"] * W / 1920
        lin = np.stack([ndi.gaussian_filter(lin[..., c], 0.75 * px / M["scale"]["px_per_mm"]) for c in range(3)], -1)
        region = np.zeros((H, W), bool)
        cw, chh = int(round(card.CROP_MM[0] * px)), int(round(card.CROP_MM[1] * px))
        region[H // 2 - chh // 2:H // 2 - chh // 2 + chh, W // 2 - cw // 2:W // 2 - cw // 2 + cw] = True
        sk, _, _ = nw.detect(nw.luma(lin), px, region)
        G = nw.Graph(sk, px, region=region)
        src = f"card render {dirs}, the compare crop, found as on the photo"
    elif mode == "exact":
        C = json.load(open(sys.argv[3]))
        P = C["params"]
        win = (P["x_range"][0] + 3, P["y_range"][0] + 3, P["x_range"][1] - 3, P["y_range"][1] - 3)
        if len(sys.argv) > 4:
            win = tuple(float(v) for v in sys.argv[4].split(","))
        sk, (H, W) = nw.rasterise(C["cracks"], PX, win)
        region = np.ones((H, W), bool)
        G = nw.Graph(sk, PX, region=region)
        src = f"generator network {sys.argv[3]}, all cracks drawn exactly (no detection), window {win} mm"
        st = nw.stats(G, region)
    else:
        C = json.load(open(sys.argv[3]))
        gen = int(sys.argv[4]) if len(sys.argv) > 4 else 9
        P = C["params"]
        win = (P["x_range"][0] + 3, P["y_range"][0] + 3, P["x_range"][1] - 3, P["y_range"][1] - 3)
        cr = [c for c in C["cracks"] if c["gen"] <= gen]
        Y = nw.synth_image(cr, PX, win, np.random.default_rng(1))
        region = np.zeros(Y.shape, bool)
        region[8:-8, 8:-8] = True
        sk, _, _ = nw.detect(Y, PX, region)
        G = nw.Graph(sk, PX, region=region)
        src = f"generator network {sys.argv[3]} (gen <= {gen}), window {win} mm, drawn as the photo shows lines (synth_image) and found again"
    res = measure(G)
    res["source"] = src
    if mode == "exact":
        res["junction_fractions"] = st["junction_fractions"]; res["cell_sqrt_mean_area_mm"] = st["cell_sqrt_mean_area_mm"]
        res["turn_per_0.25mm_rms_deg"] = st["turn_per_0.25mm_rms_deg"]; res["kinks_over_15deg_per_mm"] = st["kinks_over_15deg_per_mm"]
    print(json.dumps(res))
    json.dump(res, open(out, "w"), indent=1)


main()
