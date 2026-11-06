"""Shot 19 round 1: the studio's levels, fitted to the original as a linear mix of the light groups' passes, and the
frames mixed from them (docs/shots/19-luodian.md, 布光).

    python3 -I shots/19-luodian/fit.py fit  --raw out/shots/19-luodian/r1/raw/f05 --out shots/19-luodian/lights.json
    python3 -I shots/19-luodian/fit.py key  --raw out/shots/19-luodian/r1/raw --lights shots/19-luodian/lights.json
    python3 -I shots/19-luodian/fit.py mix  --raw out/shots/19-luodian/r1/raw --lights shots/19-luodian/lights.json --out DIR

Light adds: every frame is sum_g w_g * pass_g, w_g a camera-RGB weight per group (cycles_scene.py writes each group's
pass from one render). All the studio's emitters are 5500 K; a per-channel weight makes a group a light of that camera
RGB (the usual three-channel approximation for what it lights; the nacre tables are exact for the 5500 K key).

fit: the weights of the panel bands (p..), the overhead (ov) and the key (at frame 5), per channel, non-negative, with a
  smoothness penalty between neighbouring bands, against the original's 12-frame mean, row by row (the original's band
  and body are row profiles, docs/shots/19-dianluo.md), in raw camera RGB: the original's decoded frames are taken back
  through the camera chain's linear part (tools/camera.py develop: exposure, white balance, matrix; the shoulder
  inverted). Columns: all of 100-860 (of 960) under the arc, the two sides only above it (the caption). [F] fitted.
key: the key's weight per frame, so the body's mean (rows under the band) follows the original's frame by frame
  (its last five frames are ~15 % darker) [F].
mix: the frames as PFM (raw camera RGB, for tools/cycles_denoise.py with each render's albedo and normal).
"""

import argparse
import glob
import json
import os
import subprocess
import sys

import numpy as np
from scipy.optimize import nnls

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import compare  # noqa: E402

SPEC = json.load(open(os.path.join(ROOT, "spec/shots.json")))
SHOT = next(s for s in SPEC["shots"] if s["shot"] == 19)
F0, N = SHOT["frame_in"], SHOT["frame_out"] - SHOT["frame_in"]
W, H = 960, 540
BODY_ROWS = (0.62, 1.0)
RAMP_WARM = (1.0, 0.32, 0.10)    # display-linear BT.709, the free bands' warm end [A]
RAMP_COOL = (0.32, 0.24, 1.0)    # and cool end [A]          # under the band
CAPTION_COLS = (0.25, 0.75)      # above the arc the caption sits here (spec_measure's caption zone)


def chain(cam_path=os.path.join(HERE, "camera.json")):
    """The camera chain's linear part: display-linear BT.709 = M @ raw, below the shoulder."""
    cam = json.load(open(cam_path))
    sensor = json.load(open(os.path.join(ROOT, "tools/sensors", cam["sensor"] + ".json")))
    S = camera.Spectra(sensor["pbrt_sensor"])
    cal = camera.calibrate(S, camera.balance_spectrum(cam))
    g = cal["gains"]
    e = cam["expose"]["of_saturation"] / cam["expose"]["raw_ref"]
    k = 2.0 ** cam["develop"]["ev"] / g.min()
    return k * e * cal["C"] @ np.diag(g), cam


def develop8(raw, cam_path=os.path.join(HERE, "camera.json")):
    """tools/camera.py develop without noise or blur: the sensor's clipping (per raw channel, then the balanced
    clip to white), the matrix, the tone curve, sRGB; 0-255 floats. The fit's M is only the linear part below the
    clip: a light the fit pushes past saturation comes out of the real chain in another hue (round 1's magenta)."""
    cam = json.load(open(cam_path))
    sensor = json.load(open(os.path.join(ROOT, "tools/sensors", cam["sensor"] + ".json")))
    S = camera.Spectra(sensor["pbrt_sensor"])
    cal = camera.calibrate(S, camera.balance_spectrum(cam))
    g = cal["gains"]
    v = np.minimum(np.maximum(raw, 0) * cam["expose"]["of_saturation"] / cam["expose"]["raw_ref"], 1.0)
    v = np.minimum(v * g, g.min())
    lin = np.maximum(v @ cal["C"].T, 0.0) * 2.0 ** cam["develop"]["ev"] / g.min()
    return 255 * camera.srgb_encode(np.clip(camera.tone(lin, cam["develop"]), 0, 1))


def unshoulder(y, d):
    """Invert camera.tone (contrast 1) numerically, per value."""
    xs = np.linspace(0, 8, 20001)
    ys = camera.tone(xs, d)
    return np.interp(y, ys, xs)


def decode_frames(path, frames):
    """Frames (film numbers) of a video, decoded as tools/compare.py decodes (BT.709, limited range), 1920x1080."""
    frames = list(frames)
    vf = f"select='between(n\\,{frames[0]}\\,{frames[-1]})'," + compare.DECODE_VF
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf", vf, "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.uint8).reshape(-1, compare.FH, compare.FW, 3)
    if len(v) != frames[-1] - frames[0] + 1:
        raise SystemExit(f"decoded {len(v)} frames, wanted {frames[0]}-{frames[-1]}")
    return v[[f - frames[0] for f in frames]]


def original_raw(frames):
    """The original's frames (film numbers) as raw camera RGB at W x H."""
    M, cam = chain()
    orig = decode_frames(os.path.join(ROOT, "ref/opus55.mp4"), frames)
    out = []
    for a in orig:
        a = a.astype(np.float64).reshape(H, 2, W, 2, 3).mean((1, 3)) / 255.0
        lin = unshoulder(camera.srgb_decode(a), cam["develop"])
        out.append(lin @ np.linalg.inv(M).T)
    return np.array(out)


def passes(d):
    names = sorted(os.path.basename(p)[2:-4] for p in glob.glob(os.path.join(d, "x.*.exr")))
    names = [n for n in names if n not in ("albedo", "normal", "layers")]
    return {n: camera.read_raw(os.path.join(d, f"x.{n}.exr")) for n in names}


def arc_rows():
    a = SHOT["arc"]
    x = (np.arange(W) + 0.5) / W
    return (a["apex_y"] + a["sagitta_of_width"] * W / H * 4 * (x - a["apex_x"]) ** 2) * H     # parabola, rows at H


def row_profile(img):
    """Mean per row over the fit's columns: (H, 3); NaN where a row has no columns."""
    arc = arc_rows()
    cols = np.arange(W)
    side = (cols < 100) | (cols >= 860) | ((cols >= CAPTION_COLS[0] * W) & (cols < CAPTION_COLS[1] * W))
    prof = np.full((H, 3), np.nan)
    for r in range(int(0.05 * H), H):
        m = (cols >= 100) & (cols < 860)
        m = m & ~(side & (r < arc + 6))
        if m.any():
            prof[r] = img[r, m].mean(0)
    return prof


def cmd_fit(a):
    P = passes(a.raw)
    groups = [g for g in P if g.startswith("p")] + ["key"]
    T = row_profile(original_raw(range(F0, F0 + N)).mean(0))
    A = np.stack([row_profile(P[g]) for g in groups], 1)          # (H, G, 3)
    ok = np.isfinite(T).all(1) & np.isfinite(A).all((1, 2))
    ok &= np.arange(H) > arc_rows().max() + 6          # the band and the body; the table is set by `fit.py table`
    nb = sum(g.startswith("p") for g in groups)
    sys.path.insert(0, HERE)
    import scene
    free = [g for g in groups if g.startswith("p") and scene.BANDS[int(g[1:])] >= a.free_from]   # their own colour
    dark = [g for g in groups if g.startswith("p") and scene.BANDS[int(g[1:])] >= a.dark[0]
            and scene.BANDS[int(g[1:]) + 1] <= a.dark[1]]                                # kept off: the lacquer's mirror
    shared = [g for g in groups if g not in free and g not in dark and g != "key"]       # one chroma for all
    lam = a.smooth
    Ao, t = A[ok], T[ok]                                   # (R, G, 3), (R, 3)
    gi = {g: i for i, g in enumerate(groups)}
    M, cam = chain()
    Minv = np.linalg.inv(M)
    # the free (high) bands may only take colours on a ramp warm - neutral - cool (round 1 let them take any camera
    # RGB and they came out as magenta: warm + cool in one band). Each band mixes two neighbours of the ramp,
    # {warm, neutral} below a split and {neutral, cool} above it (or the other way round); the split and the order are
    # searched. The ramp's ends are display-linear BT.709 colours of bounded chroma [A, our choice, from the
    # original's orange and violet: decoded ~(230,110,50) and ~(120,100,230), desaturated]
    # a weight w per raw channel turns a 5500 K emitter (raw white Minv @ 1, balanced to neutral) into a light whose
    # display colour is v when w = (Minv @ v) / (Minv @ 1); scaled to unit luminance
    basis = {}
    white_raw = Minv @ np.ones(3)
    for k, v in (("warm", RAMP_WARM), ("neutral", (1.0, 1.0, 1.0)), ("cool", RAMP_COOL)):
        w = (Minv @ np.array(v)) / white_raw
        basis[k] = w / (np.array([0.2126, 0.7152, 0.0722]) @ (M @ (w * white_raw)))
    # the key's share of the body (rows under the band): fixed, so the moving light, not the static panel, lights the
    # shell pieces enough that their colours visibly change [A, a lighting choice]; the rest is fitted to what is left
    r0 = int(BODY_ROWS[0] * H)
    body = np.arange(H)[ok] >= r0
    lumw = np.array([0.25, 0.5, 0.25])
    key_w = 0.0
    if a.key_share > 0:
        key_w = a.key_share * (t[body] @ lumw).mean() / max((Ao[body, gi["key"], :] @ lumw).mean(), 1e-30)
    t_rest = t - key_w * Ao[:, gi["key"], :]

    def solve(chroma, assign):
        cols, names = [], []
        for g in free:
            for k in assign[g]:
                cols.append((Ao[:, gi[g], :] * basis[k]).T.ravel())
                names.append((g, k))
        for g in shared:
            cols.append((Ao[:, gi[g], :] * chroma).T.ravel())
            names.append((g, None))
        if a.key_share <= 0:
            cols.append(Ao[:, gi["key"], :].T.ravel())
            names.append(("key", None))
        X = np.stack(cols, 1)
        sc = np.abs(X).max(0) + 1e-12
        pen, wp = [], []
        sh = [g for g in shared if g.startswith("p")]
        for g1, g2 in zip(sh[:-1], sh[1:]):
            r = np.zeros(X.shape[1])
            i1, i2 = names.index((g1, None)), names.index((g2, None))
            r[i1], r[i2] = -1 / sc[i1], 1 / sc[i2]
            pen.append(r)
            wp.append(lam)
        for g1, g2 in zip(free[:-1], free[1:]):
            for k in ("warm", "neutral", "cool"):
                r = np.zeros(X.shape[1])
                if (g1, k) in names:
                    r[names.index((g1, k))] = -1 / sc[names.index((g1, k))]
                if (g2, k) in names:
                    r[names.index((g2, k))] = 1 / sc[names.index((g2, k))]
                if np.any(r):
                    pen.append(r)
                    wp.append(lam * a.free_smooth)
        Xs = np.concatenate([X / sc, (np.array(wp) * np.abs(t).mean())[:, None] * np.array(pen)])
        y = np.concatenate([t_rest.T.ravel(), np.zeros(len(pen))])
        x, res = nnls(Xs, y, maxiter=10000)
        return x / sc, names, res

    def fit_chroma(assign):
        chroma = np.ones(3)
        for it in range(30):
            x, names, res = solve(chroma, assign)
            rest = key_w * Ao[:, gi["key"], :]
            shared_sum = np.zeros_like(t)
            for (g, k), v in zip(names, x):
                if g in free:
                    rest = rest + v * Ao[:, gi[g], :] * basis[k]
                elif g == "key":
                    rest = rest + v * Ao[:, gi[g], :]
                else:
                    shared_sum += v * Ao[:, gi[g], :]
            new = np.array([max(0.0, ((t[:, c] - rest[:, c]) @ shared_sum[:, c]) / max(shared_sum[:, c] @ shared_sum[:, c], 1e-30))
                            for c in range(3)])
            new = new / max(new[1], 1e-12)
            if np.abs(new - chroma).max() < 1e-5:
                break
            chroma = new
        return x, names, res, chroma, it

    best = None
    for order in (("warm", "cool"), ("cool", "warm")):
        for split in range(len(free) + 1):
            assign = {g: ((order[0], "neutral") if i < split else ("neutral", order[1])) for i, g in enumerate(free)}
            x, names, res, chroma, it = fit_chroma(assign)
            if best is None or res < best[2]:
                best = (x, names, res, chroma, it, order, split)
    x, names, res, chroma, it, order, split = best
    print(f"free bands: {order[0]} side below band {split} of {len(free)}, {order[1]} side above (residual {res:.4g})")
    wts = np.zeros((len(groups), 3))
    for (g, k), v in zip(names, x):
        if g in free:
            wts[gi[g]] += v * basis[k]
        elif g == "key":
            wts[gi[g]] = v
        else:
            wts[gi[g]] = v * chroma
    if a.key_share > 0:
        wts[gi["key"]] = key_w
    print(f"shared chroma (camera RGB, G = 1): {np.round(chroma, 4)} after {it + 1} rounds")
    # one gain on every light so the object's mean 8-bit RGB (spec_measure's region: under the arc + 8 px at 480x270)
    # is the spec's: the row fit matches linear means, but a black lacquer with bright pieces averages lower once
    # encoded (the encoding is concave), so the 8-bit mean needs more light [F]
    to8 = lambda raw: 255 * camera.srgb_encode(np.clip(camera.tone(np.maximum(raw @ M.T, 0), cam["develop"]), 0, 1))
    img = sum(P[g] * wts[i] for i, g in enumerate(groups))
    arc = arc_rows()
    obj = np.arange(H)[:, None] > arc[None] + 16
    tgt = np.mean(SHOT["object_rgb"])

    def gain_for(im):
        lo, hi = 0.05, 20.0
        for _ in range(30):
            gain = np.sqrt(lo * hi)
            if to8(im[obj] * gain).mean() < tgt:
                lo = gain
            else:
                hi = gain
        return gain
    # the dark bands (the floor's mirror) as one dim, even panel of the shared chroma, its level s set with the gain so
    # the black lacquer between the pieces has L* = lacquer_L at the middle of the floor (a black lacquer seen at ~66
    # deg mirrors ~9 % of what is over it: a smooth sheen, not black, not the round-1 grey haze of the key) [A, a
    # lighting choice] while the object's 8-bit mean is the spec's [F]
    sdark = 0.0
    if a.lacquer_L > 0 and dark:
        sys.path.insert(0, HERE)
        import measure
        pm = measure.piece_map()
        from scipy import ndimage
        lac = measure.piece_map_floor() & ~ndimage.binary_dilation(pm > 0, iterations=3)
        Dk = sum(P[g] for g in dark) * chroma
        def lacL(sd):
            im = img + sd * Dk
            g_ = gain_for(im)
            v = to8(im[lac] * g_)
            Lv = measure.lab(v)[..., 0]
            return float(np.mean(Lv)), g_
        lo, hi = 0.0, 1.0
        while lacL(hi)[0] < a.lacquer_L and hi < 1e6:
            hi *= 4
        for _ in range(25):
            mid = 0.5 * (lo + hi)
            if lacL(mid)[0] < a.lacquer_L:
                lo = mid
            else:
                hi = mid
        sdark = 0.5 * (lo + hi)
        print(f"dark bands at {sdark:.4g} x chroma: lacquer L* {lacL(sdark)[0]:.1f} (target {a.lacquer_L}; "
              f"{lacL(0.0)[0]:.1f} with them off)")
        for g in dark:
            wts[gi[g]] = sdark * chroma
        img = img + sdark * Dk
    gain = gain_for(img)
    wts = wts * gain
    print(f"gain {gain:.4f}: object mean 8-bit {np.round(to8(img[obj] * gain).mean(0), 1)} (spec {SHOT['object_rgb']})")
    fit = np.einsum("hgc,gc->hc", A, wts)
    to8 = lambda raw: 255 * camera.srgb_encode(np.clip(camera.tone(np.maximum(raw @ M.T, 0), cam["develop"]), 0, 1))
    err = to8(fit[ok]) - to8(T[ok])
    out = {"about": "shots/19-luodian/fit.py: camera-RGB weights of each light group (all emitters 5500 K, scale 1 in scene.py) "
                    "fitted to the original's 12-frame mean row profile under the arc [F]: the bands from free_from_deg up a colour on the ramp warm-neutral-cool (only the cavetto and the lip see them), the bands in dark_deg one dim even level dark_level (the floor's mirror: the lacquer's sheen at L* lacquer_L), the key's share of the body fixed (key_share), the rest of the panel one shared chroma, the key "
                    "neutral (the 5500 K the camera is balanced on); key_per_frame from `fit.py key`",
           "groups": {g: [round(float(v), 6) for v in wts[i]] for i, g in enumerate(groups)},
           "fit": {"gain": round(float(gain), 5), "key_share": a.key_share, "lacquer_L": a.lacquer_L, "dark_level": round(float(sdark), 6), "ramp": {"warm": RAMP_WARM, "cool": RAMP_COOL, "order": list(order), "split": int(split)}, "smooth": lam, "free_smooth": a.free_smooth, "dark_deg": a.dark, "free_from_deg": a.free_from, "shared_chroma": [round(float(v), 5) for v in chroma], "rows": int(ok.sum()), "rms_8bit": [round(float(v), 2) for v in np.sqrt((err ** 2).mean(0))],
                   "against": "original frames 255-266 (mean), raw camera RGB via camera.json's linear chain; render frame 5"}}
    if os.path.exists(a.out):
        old = json.load(open(a.out))
        if "key_per_frame" in old:
            out["key_per_frame"] = old["key_per_frame"]
    json.dump(out, open(a.out, "w"), indent=1)
    for i, g in enumerate(groups):
        print(f"{g:>4} {np.round(wts[i], 4)}")
    print(f"row-profile rms (8-bit, R G B): {out['fit']['rms_8bit']} over {ok.sum()} rows -> {a.out}")


def cmd_table(a):
    """The table's reflectance so the sky over the rim (side columns, caption excluded) is the original's, per channel:
    the table is lit once by the studio, so its pixels scale with it [F]."""
    sys.path.insert(0, HERE)
    import scene
    L = json.load(open(a.lights))
    ours = mix(passes(a.raw), L)
    orig = original_raw(range(F0, F0 + N)).mean(0)
    arc = arc_rows()
    yy, xx = np.mgrid[0:H, 0:W]
    m = (yy < arc[None] - 8) & (yy > 0.05 * H) & ((xx < CAPTION_COLS[0] * W) | (xx >= CAPTION_COLS[1] * W))
    k = orig[m].mean(0) / ours[m].mean(0)
    new = np.clip(np.array(scene.TABLE_RGB) * k, 0, 0.9)
    print(f"sky ratio original / ours (raw, R G B): {np.round(k, 4)}; TABLE_RGB {scene.TABLE_RGB} -> {np.round(new, 5).tolist()}")


def mix(P, L, k=1.0):
    img = 0
    for g, w in L["groups"].items():
        img = img + P[g] * np.array(w) * (k if g == "key" else 1.0)
    return img


def frame_dirs(raw):
    ds = [os.path.join(raw, f"f{i:02d}") for i in range(N)]
    missing = [d for d in ds if not os.path.isdir(d)]
    if missing:
        raise SystemExit(f"missing renders: {missing}")
    return ds


def cmd_key(a):
    L = json.load(open(a.lights))
    orig = original_raw(range(F0, F0 + N))
    r0, r1 = int(BODY_ROWS[0] * H), int(BODY_ROWS[1] * H)
    lum = lambda im: (im[r0:r1, 100:860] @ np.array([0.25, 0.5, 0.25])).mean()
    target = np.array([lum(o) for o in orig])
    rests, keys = [], []
    for i, d in enumerate(frame_dirs(a.raw)):
        P = passes(d)
        rest = lum(mix(P, L, 0.0))
        rests.append(rest)
        keys.append(lum(mix(P, L, 1.0)) - rest)
    rests, keys = np.array(rests), np.array(keys)
    # the original's frame-to-frame change, about our own level with the key as fitted (the fit's gain sets the level)
    level = (rests + keys).mean()
    ks = np.maximum(0.0, (level * target / target.mean() - rests) / keys)
    L["key_per_frame"] = [round(float(k), 4) for k in ks]
    L["key_fit"] = {"against": "the original body mean's change frame by frame (rows 0.62-1.0, columns 100-860 of 960, raw G-weighted), about our level with the key as fitted [F]",
                    "original_body_rel": [round(float(t / target.mean()), 4) for t in target]}
    json.dump(L, open(a.lights, "w"), indent=1)
    print("key weight per frame:", L["key_per_frame"])
    print("original body, relative:", L["key_fit"]["original_body_rel"])


def write_pfm(path, img):
    a = np.ascontiguousarray(np.flipud(img).astype("<f4"))
    with open(path, "wb") as f:
        f.write(f"PF\n{img.shape[1]} {img.shape[0]}\n-1.0\n".encode())
        f.write(a.tobytes())


def cmd_mix(a):
    L = json.load(open(a.lights))
    if "key_per_frame" not in L:
        raise SystemExit("run `fit.py key` first")
    os.makedirs(a.out, exist_ok=True)
    for i, d in enumerate(frame_dirs(a.raw)):
        img = mix(passes(d), L, L["key_per_frame"][i])
        write_pfm(os.path.join(a.out, f"m{i:02d}.pfm"), img)
    print(f"{N} mixes -> {a.out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("fit")
    s.add_argument("--raw", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--smooth", type=float, default=0.3)
    s.add_argument("--free-from", type=float, default=64.0, help="panel bands from this elevation (deg) up take their own colour")
    s.add_argument("--lacquer-L", type=float, default=13.0, help="L* of the floor's lacquer between the pieces (0: dark bands off)")
    s.add_argument("--key-share", type=float, default=0.35, help="the key's share of the body's mean (0: fitted freely)")
    s.add_argument("--free-smooth", type=float, default=5.0, help="extra smoothness factor between the free bands")
    s.add_argument("--dark", type=float, nargs=2, default=[20.0, 36.0],
                   help="panel bands inside these elevations (deg) stay off: the floor's lacquer mirrors ~25-28 deg, so the "
                        "lacquer stays black and the body's light comes from the shell pieces (whose tilted layers see the rest)")
    s = sub.add_parser("key")
    s.add_argument("--raw", required=True)
    s.add_argument("--lights", required=True)
    s = sub.add_parser("mix")
    s.add_argument("--raw", required=True)
    s.add_argument("--lights", required=True)
    s.add_argument("--out", required=True)
    s = sub.add_parser("table")
    s.add_argument("--raw", required=True)
    s.add_argument("--lights", required=True)
    a = ap.parse_args()
    {"fit": cmd_fit, "key": cmd_key, "mix": cmd_mix, "table": cmd_table}[a.cmd](a)


if __name__ == "__main__":
    main()
