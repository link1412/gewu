"""The standard comparison of one shot against the original. Builders and checkers both use it.

    python3 -I tools/shotcheck.py 38                       # frames from spec/film.json
    python3 -I tools/shotcheck.py 38 --frames out/shots/01-38-ink/r2/dev1080 --at 420,470,485
    python3 -I tools/shotcheck.py 38 --film                # our decoded out/film/film.mp4 (camera chain + x264)
    options: --every N (default: about 6 frames, first and last included), --at F,F (add frames), --out DIR

Ours: 16-bit (or 8-bit) 1920x1080 PNGs fNNNN.png named by film frame, or --film. The original is decoded the
way compare.py decodes it (bt709, tv range -> full) and each frame is cached as uint8 .npy in out/cache/orig/.
The original's caption pixels are masked in both images. All numbers are 8-bit codes.
Out (default out/check/SHOT, with --film out/check/SHOT-film): shotcheck.json, side.png and lifted.png
(original above, ours below; lifted = gamma 1/1.6). PASS: each region's mean luma and R, G, B within +-3 codes;
arc: compare.py check's tolerance on the shot's middle frame; cuts: --film finds them where the original has them.
"""

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare  # noqa: E402
import spec_measure as sm  # noqa: E402

ROOT, FW, FH = compare.ROOT, compare.FW, compare.FH
ORIG = os.path.join(ROOT, "ref/opus55.mp4")
FILM = os.path.join(ROOT, "out/film/film.mp4")
CACHE = os.path.join(ROOT, "out/cache/orig")
TOL = 3.0
YW = np.array([0.2126, 0.7152, 0.0722])                     # BT.709 luma on codes, as shots/01-38-ink/measure.py
REGIONS = {"full": (0, FH), "top60": (0, 60), "middle": (360, 720), "bottom": (720, FH)}
BANDS = [(200, 360), (880, 1040), (1560, 1720)]             # the column bands of shots/01-38-ink/measure_sky.py
TEXT_ZONE = (int(0.04 * FH), int(0.62 * FH), int(0.22 * FW), int(0.78 * FW))   # where the original's captions sit
LIFT = 1 / 1.6


# --- reading ---------------------------------------------------------------------------------------
def decode(path, frames, w=FW, h=FH):
    """Yield (frame, uint8 HxWx3) for the given film frames of a video, one ffmpeg pass, streamed."""
    frames = sorted(frames)
    runs = []                                            # consecutive frames -> between(), short expressions
    for f in frames:
        if runs and runs[-1][1] == f - 1:
            runs[-1][1] = f
        else:
            runs.append([f, f])
    sel = "+".join(f"between(n\\,{x}\\,{y})" for x, y in runs)
    vf = f"select='{sel}',{compare.DECODE_VF}" + (f",scale={w}:{h}" if (w, h) != (FW, FH) else "")
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf", vf, "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = w * h * 3
    for f in frames:
        buf = p.stdout.read(n)
        if len(buf) != n:
            raise SystemExit(f"{path}: frame {f} missing in the decode")
        yield f, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    p.stdout.close()
    p.wait()


def orig_frames(frames):
    """Make sure the cache holds these original frames (decoding only the missing ones); return a loader."""
    os.makedirs(CACHE, exist_ok=True)
    st = os.stat(ORIG)
    sig = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "vf": compare.DECODE_VF}
    sigp = os.path.join(CACHE, "source.json")
    old = json.load(open(sigp)) if os.path.exists(sigp) else None
    if old != sig:
        for fn in os.listdir(CACHE):
            os.remove(os.path.join(CACHE, fn))
        json.dump(sig, open(sigp, "w"))
    path = lambda f: os.path.join(CACHE, f"f{f:04d}.npy")
    missing = [f for f in frames if not os.path.exists(path(f))]
    if missing:
        for f, im in decode(ORIG, missing):
            np.save(path(f) + ".tmp.npy", im)
            os.replace(path(f) + ".tmp.npy", path(f))
    return lambda f: np.load(path(f))


def read_png(path):
    """Float codes 0..255 from an 8- or 16-bit PNG (16-bit kept at full precision)."""
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-f", "rawvideo",
                          "-pix_fmt", "rgb48le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, "<u2")
    if a.size != FW * FH * 3:
        raise SystemExit(f"{path}: not {FW}x{FH}")
    return a.reshape(FH, FW, 3).astype(np.float32) * np.float32(255 / 65535)


# --- measures --------------------------------------------------------------------------------------
def caption_mask(o):
    """The original's caption pixels: unsaturated type well off its local background inside the text zone (white
    on dark: luma > 90; dark on light), glyph-sized solid components on the one text line that holds the
    most of them (wider than 3x tall is a rim, not a glyph: shot 19), dilated 12 px. Misses dark letters that touch an object below (shot 31)."""
    y0, y1, x0, x1 = TEXT_ZONE
    z = o[y0:y1, x0:x1].astype(np.float32)
    L = z @ YW.astype(np.float32)
    bg = ndimage.gaussian_filter(L, 25)
    flat = (z.max(2) - z.min(2)) < 40
    m = flat & (((L > 90) & (L > bg + 25)) | ((L < 70) & (L < bg - 60)))
    lab, n = ndimage.label(m)
    area = np.bincount(lab.ravel(), minlength=n + 1)
    glyph = []
    for i, (ys, xs) in enumerate(ndimage.find_objects(lab), 1):
        h, w = ys.stop - ys.start, xs.stop - xs.start
        if area[i] >= 40 and h <= 170 and w <= 3 * h and area[i] >= 0.12 * h * w:   # not long thin rims
            glyph.append((i, (ys.start + ys.stop) / 2, area[i]))
    out = np.zeros((FH, FW), bool)
    if not glyph:
        return out
    c = np.array([g[1] for g in glyph])
    wts = np.array([g[2] for g in glyph])
    line = max(c, key=lambda y: wts[np.abs(c - y) < 60].sum())       # the densest 120-row text line
    ids = [g[0] for g in glyph if abs(g[1] - line) < 60]
    if area[ids].sum() < 300:
        return out
    out[y0:y1, x0:x1] = ndimage.binary_dilation(np.isin(lab, ids), iterations=12)
    return out


def regions(im, keep):
    res = {}
    for k, (a, b) in REGIONS.items():
        px = im[a:b][keep[a:b]]
        if not len(px):
            res[k] = None
            continue
        rgb = px.mean(0, dtype=np.float64)
        res[k] = [round(float(v), 2) for v in rgb] + [round(float(rgb @ YW), 2)]     # R, G, B, luma
    return res


def band_rms(o, u, mask):
    """Per column band, then all three: rms over rows (masked rows out) and channels of (ours - original) row means
    (the "three-column profile rms" of docs/shots/01-38-ink.md)."""
    out, sq = [], []
    for a, b in BANDS:
        ok = ~mask[:, a:b].any(1)
        d = u[:, a:b].mean(1) - o[:, a:b].mean(1, dtype=np.float32)
        out.append(round(float(np.sqrt(np.mean(d[ok] ** 2))), 2))
        sq.append(d[ok] ** 2)
    return out + [round(float(np.sqrt(np.mean(np.concatenate(sq)))), 2)]


def grain(o, u, mask):
    """Grain and blotch in the original's flattest 360x640 tile (unmasked): std of L - G3(L) (1:1 grain) and of
    G8(L) - G60(L) (the soft blotches the eye sees in a dark sky), for both."""
    q = (o[::4, ::4].astype(np.float32) @ YW.astype(np.float32))
    best = None
    for ty in range(3):
        for tx in range(3):
            if mask[ty * 360:(ty + 1) * 360, tx * 640:(tx + 1) * 640].any():
                continue
            s = float(q[ty * 90:(ty + 1) * 90, tx * 160:(tx + 1) * 160].std())
            if best is None or s < best[0]:
                best = (s, ty, tx)
    if best is None:
        return None
    _, ty, tx = best
    sl = (slice(ty * 360, (ty + 1) * 360), slice(tx * 640, (tx + 1) * 640))
    res = {"tile_rows_cols": [ty * 360, tx * 640]}
    for name, im in (("orig", o), ("ours", u)):
        L = im[sl].astype(np.float32) @ YW.astype(np.float32)
        g8 = ndimage.gaussian_filter(L, 8)
        res[name] = {"luma": round(float(L.mean()), 2), "grain": round(float((L - ndimage.gaussian_filter(L, 3)).std()), 3),
                     "blotch": round(float((g8 - ndimage.gaussian_filter(L, 60)).std()), 3)}
    return res


def arc_fit(im):
    _, ax, ay, sag, inl, res = sm.fit_arc(np.asarray(im, np.float32)[::4, ::4])
    return {"apex": [round(float(ax), 3), round(float(ay), 3)], "sagitta": round(float(sag), 4), "inliers": round(float(inl), 2)}


def cuts_in_film(sh, spec):
    """--film: hard cuts found (spec_measure.find_cuts) in a window around the shot; strict: exactly the spec's cuts
    in that window (a short shot's window also holds its neighbours' cuts; find_cuts can't see window frames 1-2)."""
    nframes = spec["frames"]
    lo, hi = max(0, sh["frame_in"] - 6), min(nframes, sh["frame_out"] + 6)
    v = np.stack([im for _, im in decode(FILM, range(lo, hi), sm.W, sm.H)]).astype(np.float32)
    found = [c + lo for c in sm.find_cuts(v)[0] if c > 0]
    want = sorted(s["frame_in"] for s in spec["shots"] if s["frame_in"] > 0 and lo + 2 < s["frame_in"] < hi)
    return {"window": [lo, hi], "found": found, "want": want, "ok": sorted(found) == want}


# --- pictures --------------------------------------------------------------------------------------
def thumb(im):
    return np.asarray(im, np.float32).reshape(FH // 4, 4, FW // 4, 4, 3).mean((1, 3))


def sheet(rows, labels, dst, lift):
    tw, th, pad = FW // 4, FH // 4, 22
    canvas = Image.new("RGB", (len(labels) * tw, 2 * (th + pad)), (24, 24, 24))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=15)
    for r, (name, ims) in enumerate(rows):
        for i, im in enumerate(ims):
            x = 255 * (np.clip(im, 0, 255) / 255) ** lift if lift else im
            canvas.paste(Image.fromarray(np.round(np.clip(x, 0, 255)).astype(np.uint8)), (i * tw, r * (th + pad) + pad))
            d.text((i * tw + 4, r * (th + pad) + 3), f"{name} f{labels[i][0]:04d}  {labels[i][1 + r]}", fill=(230, 230, 230), font=font)
    canvas.save(dst)


# --- main ------------------------------------------------------------------------------------------
def pick_frames(sh, every, at):
    fi, fo = sh["frame_in"], sh["frame_out"]
    every = every or max(1, -(-(fo - 1 - fi) // 5))
    fr = set(range(fi, fo, every)) | {fo - 1} | {f for f in at if fi <= f < fo}
    if sh["arc"]:
        fr.add((fi + fo) // 2)
    return sorted(fr)


def main():
    t0 = time.time()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("shot", type=int)
    ap.add_argument("--frames")
    ap.add_argument("--film", action="store_true")
    ap.add_argument("--every", type=int)
    ap.add_argument("--at", default="")
    ap.add_argument("--out")
    a = ap.parse_args()
    spec = compare.load_spec()
    sh = next((s for s in spec["shots"] if s["shot"] == a.shot), None) or sys.exit(f"no shot {a.shot} in spec/shots.json")
    at = [int(x) for x in a.at.split(",") if x]
    bad_at = [f for f in at if not sh["frame_in"] <= f < sh["frame_out"]]
    if bad_at:
        sys.exit(f"--at {bad_at}: outside shot {a.shot} (frames {sh['frame_in']}-{sh['frame_out'] - 1})")
    frames = pick_frames(sh, a.every, at)
    out = os.path.join(ROOT, a.out) if a.out else os.path.join(ROOT, "out/check", f"{a.shot}-film" if a.film else str(a.shot))
    os.makedirs(out, exist_ok=True)

    if a.film:
        src = os.path.relpath(FILM, ROOT)
        ours = decode(FILM, frames)
        complete = None
    else:
        d = a.frames or json.load(open(os.path.join(ROOT, "spec/film.json")))["shots"].get(str(a.shot), {}).get("frames")
        if not d:
            sys.exit(f"shot {a.shot}: no frames in spec/film.json; pass --frames DIR")
        d = os.path.join(ROOT, d)
        src = os.path.relpath(d, ROOT)
        missing = [f for f in range(sh["frame_in"], sh["frame_out"]) if not os.path.exists(os.path.join(d, f"f{f:04d}.png"))]
        complete = {"missing": missing[:10], "n_missing": len(missing), "ok": not missing}
        if any(not os.path.exists(os.path.join(d, f"f{f:04d}.png")) for f in frames):
            sys.exit(f"{src}: sampled frames missing (first missing {missing[0]})")
        ours = ((f, read_png(os.path.join(d, f"f{f:04d}.png"))) for f in frames)
    load = orig_frames(frames)
    t_orig = time.time() - t0

    res = {"shot": a.shot, "frames": [sh["frame_in"], sh["frame_out"]], "ours": src, "tolerance_codes": TOL,
           "per_frame": {}}
    thumbs_o, thumbs_u, labels = [], [], []
    mid = (sh["frame_in"] + sh["frame_out"]) // 2
    for f, u in ours:
        u = np.asarray(u, np.float32)
        o = load(f)
        mask = caption_mask(o) if sh["caption"] else np.zeros((FH, FW), bool)
        keep = ~mask
        ro, ru = regions(o, keep), regions(u, keep)
        fails = []
        for k in REGIONS:
            if ro[k] and max(abs(x - y) for x, y in zip(ru[k], ro[k])) > TOL:
                fails.append(k)
        n = {"orig": ro, "ours": ru, "diff": {k: ro[k] and [round(x - y, 2) for x, y in zip(ru[k], ro[k])] for k in REGIONS},
             "band_rms": band_rms(o, u, mask), "grain": grain(o, u, mask), "masked_px": int(mask.sum()),
             "pass": not fails, "fail_regions": fails}
        if sh["arc"]:
            n["arc_orig"], n["arc_ours"] = arc_fit(o), arc_fit(u)
            n["arc_ours"]["sag_ratio_vs_orig"] = round(n["arc_ours"]["sagitta"] / n["arc_orig"]["sagitta"], 3) if n["arc_orig"]["sagitta"] else None
            if f == mid:
                t, g = sh["arc"], n["arc_ours"]
                ax, ay = g["apex"]
                res["arc"] = {"frame": f, "ours": g, "spec": t, "sag_ratio": round(g["sagitta"] / t["sagitta_of_width"], 3),
                              "ok": abs(ay - t["apex_y"]) < 0.03 and abs(ax - t["apex_x"]) < 0.03
                              and abs(g["sagitta"] / t["sagitta_of_width"] - 1) < 0.3}
        res["per_frame"][f] = n
        t = thumb(o)
        t[thumb(mask[..., None].repeat(3, 2))[..., 0] > 0.5] *= np.array([1.0, 0.55, 0.55], np.float32)   # mask shown red
        thumbs_o.append(t)
        thumbs_u.append(thumb(u))
        labels.append((f, f"Y {ro['full'][3]:.1f}" if ro["full"] else "", f"Y {ru['full'][3]:.1f}  {'PASS' if not fails else 'FAIL ' + ','.join(fails)}"))
    if not sh["arc"]:
        res["arc"] = {"manual": sh["arc_manual_reason"], "ok": None}
    res["cuts"] = cuts_in_film(sh, spec) if a.film else {"frames_complete": complete, "ok": complete["ok"]}
    res["pass"] = all(n["pass"] for n in res["per_frame"].values()) and res["arc"]["ok"] is not False and res["cuts"]["ok"]
    sheet([("orig", thumbs_o), ("ours", thumbs_u)], labels, os.path.join(out, "side.png"), None)
    sheet([("orig", thumbs_o), ("ours", thumbs_u)], labels, os.path.join(out, "lifted.png"), LIFT)
    res["seconds"] = {"orig_cache": round(t_orig, 1), "total": round(time.time() - t0, 1)}
    with open(os.path.join(out, "shotcheck.json"), "w") as fh:
        json.dump(res, fh, indent=1)

    # the printed table: luma ours/orig (diff) per region, worst channel diff, band rms, grain/blotch ours/orig
    print(f"shot {a.shot} frames {sh['frame_in']}-{sh['frame_out'] - 1}  ours {src}  (codes; ours/orig; tol +-{TOL:g})")
    print(f"{'frame':>5} " + " ".join(f"{k:>17}" for k in REGIONS) + "  maxdRGB  band rms L/C/R/all       grain o/u   blotch o/u  ")
    for f, n in res["per_frame"].items():
        cells = []
        for k in REGIONS:
            o, u = n["orig"][k], n["ours"][k]
            cells.append(f"{u[3]:5.1f}/{o[3]:5.1f} ({u[3] - o[3]:+5.1f})" if o else f"{'-':>17}")
        dmax = max(abs(x) for k in REGIONS if n["diff"][k] for x in n["diff"][k][:3])
        g = n["grain"]
        gs = f"{g['orig']['grain']:.2f}/{g['ours']['grain']:.2f}  {g['orig']['blotch']:.2f}/{g['ours']['blotch']:.2f}" if g else "-"
        print(f"{f:>5} " + " ".join(cells) + f"  {dmax:6.1f}  {'/'.join(f'{x:.1f}' for x in n['band_rms']):>21}  {gs:>23}  "
              + ("PASS" if n["pass"] else "FAIL " + ",".join(n["fail_regions"])))
    ar = res["arc"]
    if ar["ok"] is None:
        print(f"arc: manual ({ar['manual']}), check by eye")
    else:
        print(f"arc f{ar['frame']}: apex {ar['ours']['apex']} vs ({ar['spec']['apex_x']}, {ar['spec']['apex_y']}), "
              f"sag ratio {ar['sag_ratio']}  {'PASS' if ar['ok'] else 'FAIL'}")
    c = res["cuts"]
    print(f"cuts: found {c['found']} want {c['want']}" if a.film else f"frames: {c['frames_complete']['n_missing']} missing",
          "PASS" if c["ok"] else "FAIL")
    print(f"{'PASS' if res['pass'] else 'FAIL'}  -> {os.path.relpath(out, ROOT)}/{{shotcheck.json,side.png,lifted.png}}  "
          f"{res['seconds']['total']} s (original decode/cache {res['seconds']['orig_cache']} s)")


if __name__ == "__main__":
    main()
