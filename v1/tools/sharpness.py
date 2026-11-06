"""How much detail each shot of the original really carries -> `sharpness` fields in spec/shots.json.

    python3 -I tools/sharpness.py ref/opus55.mp4 spec/shots.json          # add/refresh the fields
    python3 -I tools/sharpness.py ref/opus55.mp4 spec/shots.json --plot   # also out/spec/sharpness.png
    python3 -I tools/sharpness.py ref/opus55.mp4 spec/shots.json --validate   # blur test -> out/spec/

spec_measure.py calls add() at the end, so a full re-measure keeps these fields. Run on its own, this
script loads the json, replaces only each shot's "sharpness" entry and the notes line it owns, and
writes it back in the same format (json.dump, indent=1), so every other byte stays as it was.

What is measured (all on the decoded luma plane Y', 8-bit code values, full 1920x1080; chroma is
4:2:0 in the file, so it carries nothing above 0.25 cycles/px by construction and is not measured):

  spectrum   Welch: 128 px tiles, half overlap, Hann window, mean removed, |FFT|^2 / sum(window^2), so
             white noise of variance v reads v in every bin. Radially averaged in 1/128 cycles/px bins.
             Tiles are labelled sky / object / edge (straddling the arc, which is the silhouette) from
             the spec's arc fit; shots without an automatic arc have only "frame". The caption zone (the
             same box spec_measure.motion masks) is left out of every shot. Interior frames only (the
             frame after a cut and the one before the next cut are skipped).
  floor      what the camera chain can make on its own: a noise-like, featureless spectrum. Estimated
             per shot as the median spectrum of its flattest tenth of tiles (least power at 0.03-0.09
             cycles/px; tiles the codec flattened to a solid value left out), raised to the codec's own
             error spectrum E where that is higher (below). Not matched in brightness: matching made
             the floor out of texture in shots that are textured edge to edge (13, 24). The bias that
             remains: when the flattest tiles are dark and carry less grain than a brighter sky, the
             sky's grain counts as signal and the cutoff comes out high (shot 1's sky), i.e. on the
             expensive side. Static fine texture (paper, the grain the codec freezes between I-frames)
             reads as floor: it is noise-like, so a grain/texture pass at full width can stand in for it.
  cutoff     the first frequency >= 0.03 cycles/px where the region spectrum falls below 2x the floor
             (signal power = floor power) and stays below for 3 more bins (3-bin log-smoothed);
             0.5 = never falls below it before Nyquist. "effective width" = 3840 * cutoff px: the
             width whose Nyquist is that frequency. The shot's cutoff is the highest of its regions.
  grain      std of Y - Gaussian(Y, 1.5 px) in the floor tiles of the whole frame, code values; and the
             floor's power at 0.25 cycles/px.
  codec      the original is Twitter's x264 re-encode (CRF 23, psy off, AQ 2; the options string is in
             the file's SEI). We re-encode the decoded film with the same options, shifted by (6, 4) px
             so the 8x8/16x16 blocks do not line up with the first pass (an aligned re-encode is nearly
             idempotent), and measure per shot the transfer T(f) = P_out/P_in and the error spectrum
             E(f) = PSD(out - in). codec cutoff = first frequency where E >= P_in (the codec's error is
             as large as what it carries). This is a second-generation measurement: the first pass saw
             a sharper source, so its loss was at least this large [A].
             Codec loss vs optical softness: the cutoff is a signal-to-floor crossing, and a linear
             codec low-pass scales signal and floor alike, so it does not move the crossing; what the
             codec does move it with is its error (dead-zone quantisation), which is why the floor is
             raised to E. A shot whose cutoff is well below the codec cutoff is soft in the source
             (lens, grade, motion); one whose cutoff sits at the codec cutoff is codec-limited
             ("limited_by").
  render     two rules, the recommendation is the larger (on the safe side):
             by cutoff: the smallest of 960 / 1280 / 1920 whose Nyquist, times 0.8 for the upscaler's
             roll-off, is at or above the cutoff (<= 0.20 -> 960, <= 0.267 -> 1280, else 1920);
             by round trip: the mid frame downscaled to 960 / 1280 (Lanczos) and back up (Lanczos); the
             smallest width whose RMS error over the measured tiles is at most the codec's own re-encode
             error RMS (the delivery codec already scrambles that much) [A: that this is invisible].
             The round trip counts lost grain as error, so it too errs on the safe side.
  agree      the cutoff measured on two single frames (1/3 and 2/3 into the shot), to show the number
             is a property of the shot and not of one frame.
"""

import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from scipy.ndimage import gaussian_filter

W, H = 1920, 1080
T = 128                       # tile; frequency bins are 1/T cycles/px
NB = T // 2 + 1
F = np.arange(NB) / T
SHIFT = (6, 4)                # luma shift for the codec re-encode (chroma gets half)
REGIONS = ("sky", "object", "edge", "frame")
WIDTHS = (960, 1280, 1920)
UPSCALE_MARGIN = 0.8
X264 = ("ref=5:deblock=0,0:partitions=p8x8,b8x8,i4x4,i8x8:me=hex:subme=2:psy=0:mixed-refs=1:merange=16:"
        "chroma-me=1:trellis=1:8x8dct=1:deadzone-inter=21:deadzone-intra=11:fast-pskip=1:chroma-qp-offset=0:"
        "nr=0:bframes=3:b-pyramid=normal:b-adapt=1:b-bias=0:direct=spatial:weightb=1:open-gop=1:weightp=2:"
        "keyint=75:min-keyint=75:scenecut=0:rc-lookahead=40:mbtree=0:qcomp=0.6:qpmin=10:qpmax=69:qpstep=4:"
        "vbv-maxrate=10240:vbv-bufsize=10240:ipratio=1.4:pbratio=1.3:aq-mode=2:aq-strength=1.0:crf=23")
NOTE = ("sharpness: luma (Y') power spectra, 128 px Welch tiles; cutoff in cycles/px at 1920 wide where the "
        "spectrum meets 2x the noise-like floor; effective_width_px = 3840*cutoff; render_width = smallest "
        "of 960/1280/1920 with 0.8*Nyquist >= cutoff; codec = same-options x264 re-encode; see tools/sharpness.py")

_win = np.outer(np.hanning(T), np.hanning(T)).astype(np.float32)
_wp = float((_win ** 2).sum())
_fy = np.fft.fftfreq(T)
_rb = np.round(np.sqrt(_fy[:, None] ** 2 + _fy[None, :] ** 2) * T).astype(int).ravel()
_rc = np.bincount(_rb)[:NB]


# ---------------------------------------------------------------- decoding and tiles

def frames_yuv(path):
    """Decoded frames as raw yuv420p planes (no colour conversion: Y is the coded luma)."""
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-f", "rawvideo",
                          "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)
    n = W * H * 3 // 2
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8)
    if p.wait():
        sys.exit(f"ffmpeg failed decoding {path}")


def luma(buf):
    return buf[:W * H].reshape(H, W)


def grid(off=0):
    """Tile corners, caption zone left out (spec_measure.motion's box)."""
    out = []
    for ty in range(off, H - T + 1 - off, T // 2):
        for tx in range(off, W - T + 1 - off, T // 2):
            if ty < 0.48 * H and ty + T > 0.28 * H and tx < 0.75 * W and tx + T > 0.25 * W:
                continue
            out.append((ty, tx))
    return np.array(out)


def arc_y(arc, x):
    """The spec's arc (apex + sagitta of a parabola) at pixel column x, pixel rows at 1920x1080."""
    xv, yv, s = arc["apex_x"] * W, arc["apex_y"] * H, arc["sagitta_of_width"]
    return yv + 2 * s * W / (xv ** 2 + (W - xv) ** 2) * (x - xv) ** 2


def labels(shot, g):
    a = shot["arc"]
    if not a:
        return np.full(len(g), 3)
    lab = []
    for ty, tx in g:
        ya = arc_y(a, np.array([tx, tx + T / 2, tx + T]))
        lab.append(0 if ty + T < ya.min() - 0.03 * H else 1 if ty > ya.max() + 0.03 * H else 2)
    return np.array(lab)


def tiles(y, g):
    return np.stack([y[a:a + T, b:b + T] for a, b in g]).astype(np.float32)


def radial(P):
    """(n, T, T) power -> (n, NB) radial means."""
    P = P.reshape(len(P), -1)
    return np.stack([np.bincount(_rb, p)[:NB] / _rc for p in P])


def psd(t):
    t = t - t.mean((1, 2), keepdims=True)
    return radial(np.abs(np.fft.fft2(t * _win)) ** 2 / _wp)


# ---------------------------------------------------------------- the estimator

def smooth_log(x):
    lx = np.log(np.maximum(x, 1e-12))
    return np.exp(np.convolve(np.pad(lx, 1, mode="edge"), np.ones(3) / 3, "valid"))


def cutoff(P, N):
    """First frequency >= 0.03 where P < 2N and stays so for 3 more bins; 0.5 if never."""
    r = smooth_log(P) / smooth_log(N)
    lo = int(np.ceil(0.03 * T))
    for i in range(lo, NB):
        if np.all(r[i:i + 4] < 2):
            return float(F[i])
    return 0.5


def floor_of(rec, codec_err=None):
    """Noise-like floor of a shot: median spectrum of its flattest tenth of tiles (least power at
    0.03-0.09 cycles/px), codec-flattened tiles (solid black/colour, no power at all) left out;
    raised to the codec's own error spectrum where that is higher."""
    cand = np.flatnonzero(rec["psd"][:, 2:].max(1) >= 1e-3)
    if len(cand) < 8:
        cand = np.arange(len(rec["psd"]))
    k = max(8, len(cand) // 10)
    pick = cand[np.argsort(rec["struct"][cand])[:k]]
    N = np.median(rec["psd"][pick], 0)
    if codec_err is not None:
        N = np.maximum(N, codec_err)
    return N, pick


def measure_set(rec, codec_err=None):
    """Region spectra, floors and cutoffs for one set of tiles (one shot, or one frame of it)."""
    out = {}
    for ri, name in enumerate(REGIONS):
        mask = (rec["lab"] == ri) if ri < 3 else np.ones(len(rec["lab"]), bool)
        if ri == 3 and (rec["lab"] < 3).any():
            continue                      # arc shots: report sky / object / edge, not the mix
        if mask.sum() < 4:
            continue
        P = rec["psd"][mask].mean(0)
        N, pick = floor_of(rec, codec_err)
        flat = P[2:].max() < 1e-3            # codec-flattened (solid black / solid colour)
        out[name] = {"P": P, "N": N, "pick": pick, "mask": mask,
                     "cutoff": None if flat else cutoff(P, N), "luma": float(np.median(rec["mean"][mask]))}
    return out


# ---------------------------------------------------------------- passes over the film

def collect(src, shots, off=0, frames=None):
    """Per-tile spectra of the film (interior frames of every shot)."""
    g = grid(off)
    shot_of = np.zeros(10 ** 5, int) - 1
    for s in shots:
        a, b = s["frame_in"] + 1, s["frame_out"] - 1
        if b <= a:
            a, b = s["frame_in"], s["frame_out"]
        shot_of[a:b] = s["shot"]
    labs = {s["shot"]: labels(s, g) for s in shots}
    rec = {s["shot"]: {k: [] for k in ("psd", "mean", "struct", "hp", "lab", "frame")} for s in shots}
    for k, buf in enumerate(frames if frames is not None else frames_yuv(src)):
        s = shot_of[k]
        if s < 0:
            continue
        y = luma(buf).astype(np.float32)
        t = tiles(y, g)
        hp = tiles(y - gaussian_filter(y, 1.5), g)
        P = psd(t)
        r = rec[s]
        r["psd"].append(P)
        r["mean"].append(t.mean((1, 2)))
        r["struct"].append(P[:, 4:13].mean(1))
        r["hp"].append(hp.std((1, 2)))
        r["lab"].append(labs[s])
        r["frame"].append(np.full(len(g), k))
    return {s: {k: np.concatenate(v) for k, v in r.items()} for s, r in rec.items() if r["psd"]}


def shifted(src):
    dy, dx = SHIFT
    for buf in frames_yuv(src):
        y = luma(buf)
        u = buf[W * H:W * H * 5 // 4].reshape(H // 2, W // 2)
        v = buf[W * H * 5 // 4:].reshape(H // 2, W // 2)
        yield np.concatenate([np.roll(y, (dy, dx), (0, 1)).ravel(),
                              np.roll(u, (dy // 2, dx // 2), (0, 1)).ravel(),
                              np.roll(v, (dy // 2, dx // 2), (0, 1)).ravel()])


def x264(frames, dst):
    """Encode raw yuv420p frames with the original's x264 options."""
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                          "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", "25", "-i", "-", "-c:v", "libx264",
                          "-profile:v", "high", "-pix_fmt", "yuv420p", "-x264-params", X264, dst],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f, np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        sys.exit("x264 re-encode failed")


def codec_pass(src, shots, tmpdir):
    """Per shot: input spectrum, output spectrum, error spectrum of a same-options re-encode."""
    enc = os.path.join(tmpdir, "reencode.mp4")
    x264(shifted(src), enc)
    g = grid(16)                              # stay clear of the roll seam
    shot_of = np.zeros(10 ** 5, int) - 1
    for s in shots:
        shot_of[s["frame_in"] + 1:max(s["frame_out"] - 1, s["frame_in"] + 2)] = s["shot"]
    acc = {s["shot"]: np.zeros((3, NB)) for s in shots}
    mse = {s["shot"]: 0.0 for s in shots}
    cnt = {s["shot"]: 0 for s in shots}
    for k, (a, b) in enumerate(zip(shifted(src), frames_yuv(enc))):
        s = shot_of[k]
        if s < 0:
            continue
        ya = tiles(luma(a).astype(np.float32), g)
        yb = tiles(luma(b).astype(np.float32), g)
        acc[s] += np.stack([psd(ya).mean(0), psd(yb).mean(0), psd(yb - ya).mean(0)])
        mse[s] += float(((yb - ya) ** 2).mean())
        cnt[s] += 1
    out = {}
    for s in acc:
        Pin, Pout, E = acc[s] / max(cnt[s], 1)
        hit = np.flatnonzero((E >= Pin) & (F >= 0.03))
        out[s] = {"Pin": Pin, "Pout": Pout, "E": E, "cutoff": float(F[hit[0]]) if len(hit) else 0.5,
                  "err_rms": float(np.sqrt(mse[s] / max(cnt[s], 1)))}
    return out


def codec_cached(src, shots, cache="out/spec/codec_cache.npz"):
    """codec_pass is the slow part (a full re-encode); keep it keyed on the source's size and mtime."""
    st = os.stat(src)
    key = f"{os.path.abspath(src)}|{st.st_size}|{int(st.st_mtime)}|{X264}|{SHIFT}"
    try:
        z = np.load(cache, allow_pickle=False)
        if str(z["key"]) == key:
            return {int(s): {"Pin": z[f"Pin{s}"], "Pout": z[f"Pout{s}"], "E": z[f"E{s}"],
                             "cutoff": float(z[f"cut{s}"]), "err_rms": float(z[f"rms{s}"])} for s in z["shots"]}
    except (OSError, KeyError):
        pass
    with tempfile.TemporaryDirectory() as td:
        codec = codec_pass(src, shots, td)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    arr = {"key": np.array(key), "shots": np.array(sorted(codec))}
    for s, c in codec.items():
        arr.update({f"Pin{s}": c["Pin"], f"Pout{s}": c["Pout"], f"E{s}": c["E"],
                    f"cut{s}": np.array(c["cutoff"]), f"rms{s}": np.array(c["err_rms"])})
    np.savez(cache, **arr)
    return codec


def roundtrip(y, width):
    from PIL import Image
    im = Image.fromarray(y.astype(np.float32), mode="F")
    h = round(H * width / W)
    return np.asarray(im.resize((width, h), Image.LANCZOS).resize((W, H), Image.LANCZOS), np.float32)


def render_width(fc):
    for w in WIDTHS:
        if fc <= UPSCALE_MARGIN * 0.5 * w / W + 1e-9:
            return w
    return W


# ---------------------------------------------------------------- main

def analyse(src, shots, keep=False):
    codec = codec_cached(src, shots)
    rec = collect(src, shots)
    mids = {}
    want = {}
    for s in shots:
        r = rec[s["shot"]]
        fr = np.unique(r["frame"])
        want[fr[len(fr) // 2]] = s["shot"]
    for k, buf in enumerate(frames_yuv(src)):
        if k in want:
            mids[want[k]] = luma(buf).astype(np.float32)
    res = {}
    for s in shots:
        n = s["shot"]
        r, c = rec[n], codec[n]
        regs = measure_set(r, c["E"])
        fcs = {k: v["cutoff"] for k, v in regs.items() if v["cutoff"] is not None}
        best = max(fcs, key=fcs.get) if fcs else None
        fc = fcs[best] if best else None
        # grain: floor tiles at the whole frame's brightness
        _, pick = floor_of(r)
        Nall = np.median(r["psd"][pick], 0)
        # two single frames
        fr = np.unique(r["frame"])
        agree = []
        for q in (fr[len(fr) // 3], fr[(2 * len(fr)) // 3]):
            sub = {k: v[r["frame"] == q] for k, v in r.items()}
            m = measure_set(sub, c["E"])
            agree.append(max([v["cutoff"] for v in m.values() if v["cutoff"] is not None], default=None))
        # round trip on the mid frame: what rendering at a lower width and upscaling would lose,
        # as an RMS over the measured tiles, next to what the delivery codec itself scrambles
        g = grid()
        y = mids[n]
        rt = {str(w): round(float(np.sqrt(np.mean((tiles(roundtrip(y, w), g) - tiles(y, g)) ** 2))), 2)
              for w in (960, 1280)}
        rw_spec = render_width(fc) if fc is not None else 960
        rw_rt = next((w for w in (960, 1280) if rt[str(w)] <= c["err_rms"]), W)
        rw = max(rw_spec, rw_rt)
        res[n] = {
            "entry": {
                "cutoff_cpp": round(fc, 4) if fc is not None else None,
                "effective_width_px": int(round(3840 * fc)) if fc is not None else None,
                "set_by": best,
                "regions": {k: {"cutoff_cpp": None if v["cutoff"] is None else round(v["cutoff"], 4),
                                "luma": round(v["luma"], 1), "tiles": int(v["mask"].sum())}
                            for k, v in regs.items()},
                "codec_cutoff_cpp": round(c["cutoff"], 4),
                "codec_err_rms": round(c["err_rms"], 2),
                "limited_by": None if fc is None else ("codec" if fc >= 0.85 * c["cutoff"] else "source"),
                "grain_std": round(float(np.median(r["hp"][pick])), 2),
                "grain_luma": round(float(np.median(r["mean"][pick])), 1),
                "floor_psd_at_0.25": round(float(Nall[T // 4]), 3),
                "two_frames_cutoff_cpp": [None if a is None else round(a, 4) for a in agree],
                "render_width": rw,
                "render_width_by_cutoff": rw_spec,
                "render_width_by_roundtrip": rw_rt,
                "roundtrip_err_rms": rt,
            },
            "spectra": regs, "codec": c,
        }
    return res


def add(out, src, plot=False):
    """Put the sharpness fields into a spec dict (as built by spec_measure, or loaded from json)."""
    res = analyse(src, out["shots"])
    for s in out["shots"]:
        s["sharpness"] = res[s["shot"]]["entry"]
    out["notes"] = [n for n in out["notes"] if not n.startswith("sharpness:")] + [NOTE]
    if plot:
        figure(out, res, "out/spec/sharpness.png")
    return res


def figure(out, res, dst):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shots = out["shots"]
    n = [s["shot"] for s in shots]
    fc = [s["sharpness"]["cutoff_cpp"] or 0 for s in shots]
    cc = [s["sharpness"]["codec_cutoff_cpp"] for s in shots]
    rw = [s["sharpness"]["render_width"] for s in shots]
    col = {960: "#2a9d8f", 1280: "#e9c46a", 1920: "#e76f51"}
    fig = plt.figure(figsize=(16, 10), dpi=110)
    ax = fig.add_axes([0.05, 0.56, 0.92, 0.38])
    ax.bar(n, fc, color=[col[w] for w in rw], width=0.75)
    ax.scatter(n, cc, marker="_", s=160, color="#222", zorder=3, label="codec cutoff (same-options x264 re-encode)")
    for w in (960, 1280):
        ax.axhline(UPSCALE_MARGIN * 0.5 * w / W, color=col[w], ls="--", lw=1)
        ax.text(0.5, UPSCALE_MARGIN * 0.5 * w / W + 0.004, f"0.8 x Nyquist of {w} px", va="bottom", fontsize=8, color=col[w])
    ax.set_xlim(0.3, 39.6)
    ax.set_ylim(0, 0.52)
    ax.set_xticks(n)
    ax.set_xlabel("shot")
    ax.set_ylabel("cutoff, cycles/px at 1920 wide")
    ax.set_title("Original film: frequency where each shot's luma spectrum meets its noise-like floor "
                 "(bar colour = recommended render width: teal 960, yellow 1280, red 1920)")
    sec = ax.secondary_yaxis("right", functions=(lambda f: 3840 * f, lambda w: w / 3840))
    sec.set_ylabel("effective width, px")
    ax.legend(loc="upper left", fontsize=8)
    ex = sorted(n, key=lambda k: fc[k - 1])
    pick = [ex[0], ex[len(ex) // 3], ex[2 * len(ex) // 3], ex[-1]]
    for i, k in enumerate(pick):
        a = fig.add_axes([0.05 + i * 0.235, 0.07, 0.2, 0.38])
        r = res[k]
        reg = r["entry"]["set_by"]
        sp = r["spectra"][reg]
        a.semilogy(F[1:], sp["P"][1:], color="#264653", lw=1.6, label=f"{reg} spectrum")
        a.semilogy(F[1:], sp["N"][1:], color="#999", lw=1.2, ls="--", label="floor")
        a.semilogy(F[1:], r["codec"]["E"][1:], color="#e76f51", lw=1, ls=":", label="codec error E")
        f = r["entry"]["cutoff_cpp"]
        if f:
            a.axvline(f, color="#264653", lw=0.8)
        a.set_title(f"shot {k}: cutoff {f} c/px, render {r['entry']['render_width']}", fontsize=9)
        a.set_xlabel("cycles/px")
        if i == 0:
            a.set_ylabel("power (code values^2 per bin)")
            a.legend(fontsize=7)
    fig.savefig(dst)
    plt.close(fig)


# ---------------------------------------------------------------- validation: known blur

def validate(src, shots, shot_no, dst_dir, sigma_n=2.0):
    """Blur one frame by known Gaussians, add white noise of known level, measure the cutoff.

    Predicted cutoff: where the unblurred frame's spectrum times the Gaussian's |MTF|^2 meets the added
    noise's level (sigma_n^2 per bin). Done twice: as is, and through the same-options x264 (there the
    floor is raised to that encode's own error spectrum, as in the film measurement)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    shot = next(s for s in shots if s["shot"] == shot_no)
    k0 = (shot["frame_in"] + shot["frame_out"]) // 2
    base = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", src, "-vf",
                           f"select=eq(n\\,{k0})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                          capture_output=True, check=True).stdout
    base = np.frombuffer(base, np.uint8)
    y0 = luma(base).astype(np.float32)
    g = grid()
    lab = labels(shot, g)
    P0 = psd(tiles(y0, g)).mean(0)
    rng = np.random.default_rng(1)
    sigmas = [0, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for sg in sigmas:
            yb = gaussian_filter(y0, sg) if sg else y0
            pred = cutoff(P0 * np.exp(-4 * np.pi ** 2 * sg ** 2 * F ** 2) + sigma_n ** 2, np.full(NB, sigma_n ** 2))
            frames, recs = [], []
            for j in range(6):
                yn = np.clip(np.round(yb + rng.normal(0, sigma_n, yb.shape)), 0, 255).astype(np.uint8)
                frames.append(np.concatenate([yn.ravel(), base[W * H:]]))
            r = _rec_from(frames[:1], g, lab)
            meas = max(v["cutoff"] for v in measure_set(r).values() if v["cutoff"] is not None)
            enc = os.path.join(td, f"v{sg}.mp4")
            x264(frames, enc)
            dec = list(frames_yuv(enc))[1:]
            r2 = _rec_from(dec, g, lab)
            E = np.mean([psd(tiles(luma(d).astype(np.float32), g) - tiles(luma(i).astype(np.float32), g)).mean(0)
                         for d, i in zip(dec, frames[1:])], 0)
            meas_c = max(v["cutoff"] for v in measure_set(r2, E).values() if v["cutoff"] is not None)
            rows.append((sg, pred, meas, meas_c))
            print(f"sigma {sg:4.2f}  predicted {pred:.4f}  measured {meas:.4f}  through x264 {meas_c:.4f}")
    os.makedirs(dst_dir, exist_ok=True)
    with open(os.path.join(dst_dir, f"validate_blur_{shot_no}.json"), "w") as f:
        json.dump({"shot": shot_no, "frame": k0, "sigma_noise": sigma_n,
                   "rows": [{"sigma_px": a, "predicted": b, "measured": c, "measured_x264": d} for a, b, c, d in rows]},
                  f, indent=1)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)
    s = [r[0] for r in rows]
    ax.plot(s, [r[1] for r in rows], "k-", label="predicted (known blur, known noise)")
    ax.plot(s, [r[2] for r in rows], "o", color="#2a9d8f", label="measured")
    ax.plot(s, [r[3] for r in rows], "s", mfc="none", color="#e76f51", label="measured after x264")
    ax.set_xlabel("Gaussian blur sigma, px")
    ax.set_ylabel("cutoff, cycles/px")
    ax.set_title(f"Blur test on shot {shot_no}, frame {k0}, noise sigma {sigma_n}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(dst_dir, f"validate_blur_{shot_no}.png"))
    return rows


def _rec_from(frames, g, lab):
    r = {k: [] for k in ("psd", "mean", "struct", "hp", "lab", "frame")}
    for k, buf in enumerate(frames):
        y = luma(buf).astype(np.float32)
        t = tiles(y, g)
        P = psd(t)
        r["psd"].append(P)
        r["mean"].append(t.mean((1, 2)))
        r["struct"].append(P[:, 4:13].mean(1))
        r["hp"].append(np.zeros(len(g)))
        r["lab"].append(lab)
        r["frame"].append(np.full(len(g), k))
    return {k: np.concatenate(v) for k, v in r.items()}


def main(argv):
    src, dst = argv[0], argv[1]
    with open(dst) as f:
        text = f.read()
    out = json.loads(text)
    if "--validate" in argv:
        validate(src, out["shots"], int(os.environ.get("GEWU_VALIDATE_SHOT", "24")), "out/spec")
        return
    add(out, src, plot="--plot" in argv)
    with open(dst, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for s in out["shots"]:
        e = s["sharpness"]
        print(f"{s['shot']:>2} cutoff {e['cutoff_cpp']!s:>6} ({e['set_by']!s:>6})  eff {e['effective_width_px']!s:>5}px  "
              f"codec {e['codec_cutoff_cpp']:.3f} {e['limited_by']!s:>6}  grain {e['grain_std']:.2f}@{e['grain_luma']:.0f}  "
              f"two {e['two_frames_cutoff_cpp']}  render {e['render_width']} ({e['render_width_by_cutoff']}/{e['render_width_by_roundtrip']})  "
              f"rt {e['roundtrip_err_rms']} vs codec {e['codec_err_rms']}")


if __name__ == "__main__":
    main(sys.argv[1:])
