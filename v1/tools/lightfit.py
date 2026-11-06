"""Fit a shot's light strengths in seconds from per-light basis renders, instead of re-rendering per trial.

    python3 -I tools/lightfit.py fit SPEC.json --out WEIGHTS.json      # nnls fit, variant table, residuals per frame
    python3 -I tools/lightfit.py mix SPEC.json WEIGHTS.json --out DIR  # DIR/<frame>.pfm: mixed raw frames, full res

Light adds in raw linear camera RGB: a frame is sum_k w_k * B_k, B_k the frame lit by light k alone at unit strength
(Cycles light-group passes, a pbrt run per light, a numpy model per light). The w_k (per channel, a scalar, or
non-negative mixes of named colours) are a non-negative least-squares problem against the original's frames, which are
taken back to raw camera RGB through the inverse of camera.json's linear chain (exposure, white balance, matrix; the
shoulder inverted), as shots/19-luodian/fit.py does. Everything is reduced to per-channel Gram sums over the target
entries (lights x lights x 3), so variants, ties and penalties cost nothing once the bases are read (cached in
out/lightfit-cache). Nonlinear parameters (beam width, lamp depth, ...) are not solved here: render a few variants of
that light ONCE, list them as "variants", and the outer loop picks the best (table in the output).
Spec (JSON; paths relative to the repo): camera (camera.json, or "display-linear"), raw_ref?, shot? (arc masks, "spec"
gain), res [480,270], basis "DIR/{frame}/x.{light}.exr", frames [{name, target "255-266" | [257] | target_raw, held_out?,
basis? {light: path}}], target {kind rows|image|regions, mask [ops, see mask()], bands?, regions?}, target_average
linear|codes, weights channel|scalar, lights {name: {weights?, colors? | colors_display?, tie?, fixed?, in_fit?, share?
{value, rows}, prior?, prior_weight?, basis?, variants? {vname: {overrides}}}}, smooth [{chain|pair, weight}],
variants [{name, lights {name: overrides}}] (joint), gain? {mean8 [r,g,b]|"spec", mask}. Weights out are [F].
Examples: tests/lightfit/shot19_spec.py (reproduces shots/19-luodian/fit.py `fit`), tests/lightfit/synth.py.

Per-light bases from the numpy KM ink model (shots/01-38-ink/optics.py render), read, not run (analysis only):
- L = (T * E_back + R * E_front) / pi + sheen. T and R (km() of S d, K d from sheet.optics) depend only on the paper
  and ink maps and O["paper"], O["carbon"], never on the light: the transmittance step is linear in irradiance.
- E_back = sum over lamps of scale * view factor * spectrum (the ambient lamp: pi * scale * spectrum): linear in each
  lamp's "scale"; so are the front fill's and the sheen's "scale".
- After it, XYZ -> BT.709 -> * exposure, defocus (disc blurs mixed by weights from depth only), veil / glare (Gaussian
  blur, the frame mean) are all linear in the image, so render() is exactly sum_k scale_k * render(lamp k at 1).
- Nonlinear: a lamp's x_mm, y_mm, depth_mm, radius_mm, cos_power and its spectrum's T / beta / gamma (variants, or
  separate bases per spectrum); to_display's clip and encoding (after the sum; lightfit inverts nothing there).
- A per-channel weight on a lamp is exact only as a scale; as a colour change it is the 3-channel approximation of a
  spectral one. optics.py's images are display-linear BT.709, already exposed: use "camera": "display-linear".
"""

import argparse
import hashlib
import itertools
import json
import os
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import nnls

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import compare  # noqa: E402

CACHE = os.path.join(ROOT, "out/lightfit-cache")
LUM709 = np.array([0.2126, 0.7152, 0.0722])
CAPTION = (0.25, 0.75, 0.28, 0.48)          # x0 x1 y0 y1: spec_measure.py's caption zone [D: tools/spec_measure.py]


def P(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


# --- images -------------------------------------------------------------------------------------
def read_image(path):
    """Raw camera RGB, float64 (H, W, 3): EXR (via imgtool), PFM, npy, 16-bit PNG."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".exr":
        return camera.read_raw(path)
    if ext == ".npy":
        return np.load(path).astype(np.float64)[..., :3]
    if ext == ".pfm":
        with open(path, "rb") as f:
            if f.readline().strip() != b"PF":
                raise SystemExit(f"{path}: not an RGB PFM")
            w, h = map(int, f.readline().split())
            s = float(f.readline())
            a = np.frombuffer(f.read(), "<f4" if s < 0 else ">f4").reshape(h, w, 3)
        return np.flipud(a).astype(np.float64)
    if ext == ".png":
        wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                             "stream=width,height,pix_fmt", "-of", "csv=p=0", path], capture_output=True, check=True,
                            text=True).stdout.strip().split(",")
        if "48" not in wh[2] and "64" not in wh[2]:
            raise SystemExit(f"{path}: {wh[2]} PNG; a basis PNG must be 16-bit raw camera RGB")
        raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-f", "rawvideo",
                              "-pix_fmt", "rgb48le", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, "<u2").reshape(int(wh[1]), int(wh[0]), 3) / 65535.0
    raise SystemExit(f"{path}: unknown image type")


def write_pfm(path, img):
    a = np.ascontiguousarray(np.flipud(img).astype("<f4"))
    with open(path, "wb") as f:
        f.write(f"PF\n{img.shape[1]} {img.shape[0]}\n-1.0\n".encode())
        f.write(a.tobytes())


def box(img, W, H):
    h, w = img.shape[:2]
    if (w, h) == (W, H):
        return img
    if w % W or h % H or w // W != h // H:
        raise SystemExit(f"image {w}x{h} is not a whole multiple of the fit's {W}x{H}")
    k = w // W
    return img.reshape(H, k, W, k, -1).mean((1, 3))


def cache_key(*parts):
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:20]


def basis_at(path, W, H):
    """A basis image box-averaged to W x H, cached (float32) by path, mtime and size."""
    st = os.stat(path)
    f = os.path.join(CACHE, "b" + cache_key(os.path.abspath(path), st.st_mtime_ns, st.st_size, W, H) + ".npy")
    if os.path.exists(f):
        return np.load(f).astype(np.float64)
    a = box(read_image(path), W, H)
    os.makedirs(CACHE, exist_ok=True)
    np.save(f, a.astype(np.float32))
    return a


# --- the original, back to raw camera RGB -------------------------------------------------------
def chain(cam_path, raw_ref=None):
    """The camera chain's linear part: display-linear BT.709 = M @ raw, below the shoulder (as shots/19 fit.py).
    Needs a fixed exposure: a percentile exposure moves with the lights, so it has no fixed inverse."""
    if cam_path.endswith("display-linear"):             # images already display-linear BT.709, no tone (ink model)
        return np.eye(3), {"develop": {"ev": 0.0, "shoulder_from": 1.0}}
    cam = json.load(open(cam_path))
    if raw_ref is not None:
        cam["expose"]["raw_ref"] = raw_ref
    if "raw_ref" not in cam["expose"]:
        raise SystemExit(f"{cam_path}: expose has no raw_ref; freeze the exposure (camera.py develop prints the raw "
                         "value it used) in camera.json, or give \"raw_ref\" in the spec")
    sensor = json.load(open(os.path.join(ROOT, "tools/sensors", cam["sensor"] + ".json")))
    S = camera.Spectra(sensor["pbrt_sensor"])
    cal = camera.calibrate(S, camera.balance_spectrum(cam))
    g = cal["gains"]
    e = cam["expose"]["of_saturation"] / cam["expose"]["raw_ref"]
    k = 2.0 ** cam["develop"]["ev"] / g.min()
    return k * e * cal["C"] @ np.diag(g), cam


def unshoulder(y, d):
    xs = np.linspace(0, 8, 20001)
    return np.interp(y, camera.tone(xs, d), xs)


def to8(raw, M, d):
    """Raw camera RGB -> full-range 8-bit codes (float), the chain without noise."""
    return 255 * camera.srgb_encode(np.clip(camera.tone(np.maximum(raw @ M.T, 0), d), 0, 1))


def original_raw(video, frames, W, H, M, cam, average):
    """Mean over `frames` (film numbers) of the original as raw camera RGB at W x H. average 'linear': linearise each
    1080p pixel, then box-average (right for light); 'codes': box-average the 8-bit codes first (shots/19 fit.py)."""
    key = lambda f: os.path.join(CACHE, "t" + cache_key(os.path.abspath(video), os.path.getmtime(video), f, W, H,
                                                        average, cam["develop"], M.tolist()) + ".npy")
    out = {f: np.load(key(f)).astype(np.float64) for f in frames if os.path.exists(key(f))}
    need = sorted(set(frames) - set(out))
    if need:
        vf = f"select='between(n\\,{need[0]}\\,{need[-1]})'," + compare.DECODE_VF
        p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", video, "-vf", vf, "-fps_mode",
                              "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        n = compare.FW * compare.FH * 3
        Minv = np.linalg.inv(M)
        for f in range(need[0], need[-1] + 1):
            buf = p.stdout.read(n)
            if len(buf) != n:
                raise SystemExit(f"{video}: decoding stopped before frame {f}")
            if f not in need:
                continue
            a = np.frombuffer(buf, np.uint8).reshape(compare.FH, compare.FW, 3).astype(np.float64) / 255.0
            if average == "codes":
                lin = unshoulder(camera.srgb_decode(box(a, W, H)), cam["develop"])
            else:
                lin = box(unshoulder(camera.srgb_decode(a), cam["develop"]), W, H)
            out[f] = lin @ Minv.T
            os.makedirs(CACHE, exist_ok=True)
            np.save(key(f), out[f].astype(np.float32))
        p.stdout.close()
        p.wait()
    return np.mean([out[f] for f in frames], 0)


def frame_list(t):
    if isinstance(t, str):
        a, b = map(int, t.split("-"))
        return list(range(a, b + 1))
    return [int(t)] if isinstance(t, int) else [int(f) for f in t]


# --- masks and targets ---------------------------------------------------------------------------
def arc_rows(arc, W, H):
    x = (np.arange(W) + 0.5) / W
    return (arc["apex_y"] + arc["sagitta_of_width"] * W / H * 4 * (x - arc["apex_x"]) ** 2) * H


def mask(ops, W, H, arc):
    """AND of ops: {"cols":[a,b]}, {"rows":[a,b]} (fractions, [a,b)), {"exclude":[x0,x1,y0,y1]}, {"caption":true},
    {"below_arc":px} / {"above_arc":px} (strictly beyond arc+px, px at the fit's res), {"below_arc_max":px}."""
    yy, xx = np.mgrid[0:H, 0:W]
    m = np.ones((H, W), bool)
    eps = 1e-6
    for op in ops:
        (k, v), = op.items()
        if k == "cols":
            m &= (xx >= v[0] * W - eps) & (xx < v[1] * W - eps)
        elif k == "rows":
            m &= (yy >= v[0] * H - eps) & (yy < v[1] * H - eps)
        elif k == "caption":                  # spec_measure.py's own pixels: [int(y0 h), int(y1 h)) x [int(x0 w), int(x1 w))
            x0, x1, y0, y1 = CAPTION
            m[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = False
        elif k == "exclude":
            x0, x1, y0, y1 = v
            m &= ~((xx >= x0 * W - eps) & (xx < x1 * W - eps) & (yy >= y0 * H - eps) & (yy < y1 * H - eps))
        elif k in ("below_arc", "above_arc", "below_arc_max"):
            if arc is None:
                raise SystemExit(f"mask {k}: the spec names no shot with an arc")
            a = arc_rows(arc, W, H)
            m &= (yy > a[None] + v) if k == "below_arc" else (yy < a[None] + v) if k == "above_arc" else (yy > a.max() + v)
        else:
            raise SystemExit(f"unknown mask op {k}")
    return m


def extractor(tk, W, H, arc):
    """The target kind as a function image -> (E, 3) entries, plus each entry's row (for 'share'; -1 for regions)."""
    m = mask(tk.get("mask", []), W, H, arc)
    kind = tk["kind"]
    if kind == "image":
        rows = np.nonzero(m)[0]
        return (lambda img: img[m]), rows
    if kind == "rows":
        bands = [mask([{"cols": b}], W, H, arc) & m for b in tk.get("bands", [[0, 1]])]
        sel = [(r, b) for b in bands for r in range(H) if b[r].any()]
        rows = np.array([r for r, _ in sel])
        return (lambda img: np.array([img[r, b[r]].mean(0) for r, b in sel])), rows
    if kind == "regions":
        regs = [mask(ops, W, H, arc) & m for ops in tk["regions"].values()]
        if any(not r.any() for r in regs):
            raise SystemExit("a region is empty")
        return (lambda img: np.array([img[r].mean(0) for r in regs])), np.full(len(regs), -1)
    raise SystemExit(f"unknown target kind {kind}")


# --- the problem ---------------------------------------------------------------------------------
class Problem:
    def __init__(self, spec_path):
        self.spec = s = json.load(open(spec_path))
        self.W, self.H = s.get("res", [480, 270])
        self.M, self.cam = chain(P(s["camera"]), s.get("raw_ref"))
        shot = s.get("shot")
        self.shot = None if shot is None else next(x for x in json.load(open(P("spec/shots.json")))["shots"] if x["shot"] == shot)
        self.arc = self.shot["arc"] if self.shot else None
        self.lights = list(s["lights"])
        self.configs = self.expand()
        self.ext, self.rows = extractor(s["target"], self.W, self.H, self.arc)

    def light_opts(self, name, over):
        o = dict(self.spec["lights"][name] or {})
        o.pop("variants", None)
        o.update(over.get(name, {}))
        return o

    def expand(self):
        """Every combination: per-light variants (cartesian) x joint variants (spec "variants": [{name, lights}])."""
        per = []
        for l in self.lights:
            v = (self.spec["lights"][l] or {}).get("variants")
            per.append([(f"{l}={k}", {l: o}) for k, o in v.items()] if v else [("", {})])
        joint = [(j["name"], j["lights"]) for j in self.spec.get("variants", [])] or [("", {})]
        out = []
        for combo in itertools.product(*per, joint):
            over = {}
            for _, o in combo:
                for l, d in o.items():
                    over.setdefault(l, {}).update(d)
            name = " ".join(n for n, _ in combo if n) or "base"
            out.append((name, {l: self.light_opts(l, over) for l in self.lights}))
        return out

    def basis_path(self, fr, light, opts):
        if light in fr.get("basis", {}):
            return P(fr["basis"][light])
        t = opts.get("basis", self.spec.get("basis"))
        if t is None:
            raise SystemExit(f"no basis for light {light}")
        return P(t.format(frame=fr["name"], light=light))

    def load(self):
        """Per frame: target entries t (E,3), basis entries per virtual light {(light, path-template)} (E,3)."""
        self.vl = {}                       # (light, template-or-path per frame) -> index; built per frame below
        self.frames = []
        video = P(self.spec.get("original", "ref/opus55.mp4"))
        avg = self.spec.get("target_average", "linear")
        for fr in self.spec["frames"]:
            if "target_raw" in fr:
                T = box(read_image(P(fr["target_raw"])), self.W, self.H)
            else:
                T = original_raw(video, frame_list(fr["target"]), self.W, self.H, self.M, self.cam, avg)
            B = {}
            for _, opts in self.configs:
                for l in self.lights:
                    if opts[l].get("fixed") == 0 and opts[l].get("in_fit") is False:
                        continue
                    p = self.basis_path(fr, l, opts[l])
                    key = (l, opts[l].get("basis", self.spec.get("basis")))
                    if key not in B:
                        B[key] = basis_at(p, self.W, self.H)
            vkeys = sorted(B, key=str)
            for k in vkeys:
                self.vl.setdefault(k, len(self.vl))
            held = bool(fr.get("held_out"))
            img = {k: b.astype(np.float32) for k, b in B.items()} if self.spec.get("gain") and not held else None
            self.frames.append({"name": fr["name"], "held_out": held, "t": self.ext(T),
                                "A": {k: self.ext(B[k]).astype(np.float32) for k in vkeys}, "img": img})
            del B
        V = len(self.vl)
        fit = [f for f in self.frames if not f["held_out"]]
        if not fit:
            raise SystemExit("no frame to fit (all held out)")
        self.K = np.zeros((V, V, 3))
        self.Kb = np.zeros((V, 3))
        self.tt = np.zeros(3)
        for f in fit:
            for c in range(3):
                A = np.zeros((len(f["t"]), V))
                for k, a in f["A"].items():
                    A[:, self.vl[k]] = a[:, c]
                self.K[:, :, c] += A.T @ A
                self.Kb[:, c] += A.T @ f["t"][:, c]
            self.tt += (f["t"] ** 2).sum(0)
        self.mabs = np.mean(np.concatenate([np.abs(f["t"]).ravel() for f in fit]))

    def vidx(self, l, o):
        return self.vl.get((l, o.get("basis", self.spec.get("basis"))))

    def colours(self, o):
        Minv = np.linalg.inv(self.M)
        if "colors" in o:
            return {k: np.array(v, float) for k, v in o["colors"].items()}
        if "colors_display" in o:           # a 'white' raw emitter turned into display colour v, unit luminance
            white = Minv @ np.ones(3)
            out = {}
            for k, v in o["colors_display"].items():
                w = (Minv @ np.array(v, float)) / white
                out[k] = w / (LUM709 @ (self.M @ (w * white)))
            return out
        if o.get("weights", self.spec.get("weights", "channel")) == "scalar":
            return {"s": np.ones(3)}
        return {"r": np.eye(3)[0], "g": np.eye(3)[1], "b": np.eye(3)[2]}

    def share_weight(self, l, o):
        """A fixed weight so this light gives `share` of the target's luma-ish mean over rows [a,b) (fit.py's key)."""
        sh = o["share"]
        a, b = sh.get("rows", [0, 1])
        lw = np.array(sh.get("lum", [0.25, 0.5, 0.25]))
        num = den = 0.0
        n = 0
        for f in self.frames:
            if f["held_out"]:
                continue
            m = (self.rows >= int(a * self.H)) & (self.rows < (self.H if b >= 1 else int(b * self.H)))
            num += (f["t"][m] @ lw).sum()
            den += (f["A"][(l, o.get("basis", self.spec.get("basis")))][m] @ lw).sum()
            n += m.sum()
        if n == 0:
            raise SystemExit(f"share of {l}: no target entries in rows {a}-{b}")
        return sh["value"] * num / max(den, 1e-30) * np.ones(3)

    def solve_config(self, opts):
        """NNLS on the Gram-reduced system; ties (shared colour per group, G = 1) by alternation as shots/19 fit.py."""
        fixed, cols, ties = {}, [], {}
        for l in self.lights:
            o = opts[l]
            if "share" in o:
                fixed[l] = (self.share_weight(l, o), True)
            elif "fixed" in o:
                fixed[l] = (np.broadcast_to(np.array(o["fixed"], float), (3,)).copy(), o.get("in_fit", True))
            elif "tie" in o:
                ties.setdefault(o["tie"], []).append(l)
                cols.append((l, "tie:" + o["tie"], None))
            else:
                cols += [(l, k, c) for k, c in self.colours(o).items()]
        chroma = {g: np.ones(3) for g in ties}
        names = [(l, k) for l, k, _ in cols]
        vi = np.array([self.vidx(l, opts[l]) for l, _, _ in cols])
        pens = []
        for sm in self.spec.get("smooth", []):
            ch = sm.get("chain") or sm["pair"]
            for l1, l2 in zip(ch[:-1], ch[1:]):
                for k in dict.fromkeys([k for l, k in names if l in (l1, l2)]):
                    r = np.zeros(len(cols))
                    for sign, l in ((-1, l1), (1, l2)):
                        if (l, k) in names:
                            r[names.index((l, k))] = sign
                    pens.append((r * sm["weight"] * self.mabs, 0.0))
        for l in self.lights:
            o = opts[l]
            if "prior" in o:
                for j, (l2, k) in enumerate(names):
                    if l2 == l:
                        pv = o["prior"][k] if isinstance(o["prior"], dict) else o["prior"]
                        r = np.zeros(len(cols))
                        r[j] = o.get("prior_weight", 1.0) * self.mabs
                        pens.append((r, r[j] * pv))
        fx = [(self.vidx(l, opts[l]), w) for l, (w, inf) in fixed.items() if inf and np.any(w)]
        Kb = self.Kb.copy()
        tt = self.tt.copy()
        for v, w in fx:                      # the target minus the fixed lights
            Kb -= self.K[:, v] * w
            tt -= 2 * w * self.Kb[v]
            for u, w2 in fx:
                tt += w * w2 * self.K[v, u]
        for it in range(30):
            D = np.array([c if c is not None else chroma[k[4:]] for _, k, c in cols])      # (J, 3)
            G = np.einsum("jc,kc,jkc->jk", D, D, self.K[np.ix_(vi, vi)])
            b = np.einsum("jc,jc->j", D, Kb[vi])
            d = np.sqrt(np.maximum(np.diag(G), 1e-300))
            Gs = G / np.outer(d, d)
            s, U = np.linalg.eigh(Gs)
            keep = s > 1e-13 * s.max()
            R = np.sqrt(s[keep])[:, None] * U[:, keep].T
            y = (U[:, keep].T @ (b / d)) / np.sqrt(s[keep])
            if pens:
                R = np.concatenate([R, np.array([r / d for r, _ in pens])])
                y = np.concatenate([y, [v for _, v in pens]])
            z, _ = nnls(R, y, maxiter=20000)
            x = z / d
            obj = x @ G @ x - 2 * b @ x + tt.sum() + sum((r @ x - v) ** 2 for r, v in pens)
            if not ties:
                break
            wl = self.weights(cols, x, chroma, fixed, all_fixed=False)
            new, done = {}, True
            for g, members in ties.items():
                mi = [self.vidx(l, opts[l]) for l in members]
                v = np.array([wl[l][1] for l in members])
                others = [(self.vidx(l, opts[l]), wl[l][0]) for l in wl if l not in members]
                others += fx
                num = np.array([sum(v[a] * (self.Kb[mi[a], c] - sum(w[c] * self.K[u, mi[a], c] for u, w in others))
                                    for a in range(len(mi))) for c in range(3)])
                den = np.array([v @ self.K[np.ix_(mi, mi, [c])][..., 0] @ v for c in range(3)])
                nc = np.maximum(0.0, num / np.maximum(den, 1e-30))
                nc = nc / max(nc[1], 1e-12)
                done &= np.abs(nc - chroma[g]).max() < 1e-5
                new[g] = nc
            if done:
                break
            chroma = new
        wl = self.weights(cols, x, chroma, fixed, all_fixed=True)
        return {l: w for l, (w, _) in wl.items()}, chroma, float(np.sqrt(max(obj, 0.0))), it + 1

    def weights(self, cols, x, chroma, fixed, all_fixed):
        out = {}
        for (l, k, c), v in zip(cols, x):
            vec = c if c is not None else chroma[k[4:]]
            w, s = out.get(l, (np.zeros(3), 0.0))
            out[l] = (w + v * vec, s + v)
        if all_fixed:
            for l, (w, _) in fixed.items():
                out[l] = (w, 0.0)
        return out

    def mixed(self, f, opts, W):
        return sum(f["img"][(l, opts[l].get("basis", self.spec.get("basis")))] * W[l].astype(np.float32) for l in self.lights
                   if np.any(W[l]))

    def gain(self, opts, W):
        """One gain on every light so the 8-bit mean over the gain mask (all channels) is the target (fit.py's)."""
        g = self.spec.get("gain")
        if not g:
            return 1.0
        m = mask(g.get("mask", []), self.W, self.H, self.arc)
        tgt = g["mean8"]
        tgt = np.mean(self.shot["object_rgb"] if tgt == "spec" else tgt)
        px = np.concatenate([self.mixed(f, opts, W)[m] for f in self.frames if not f["held_out"]]).astype(np.float64)
        lo, hi = 0.05, 20.0
        for _ in range(30):
            k = np.sqrt(lo * hi)
            lo, hi = (k, hi) if to8(px * k, self.M, self.cam["develop"]).mean() < tgt else (lo, k)
        return k

    def residuals(self, opts, W):
        out = {}
        d = self.cam["develop"]
        for f in self.frames:
            fit = sum(f["A"][(l, opts[l].get("basis", self.spec.get("basis")))] * W[l] for l in self.lights if np.any(W[l]))
            e = to8(fit, self.M, d) - to8(f["t"], self.M, d)
            ey = e @ LUM709
            out[f["name"]] = {"held_out": f["held_out"], "entries": len(e),
                              "rms_8bit": [round(float(v), 3) for v in np.sqrt((e ** 2).mean(0))],
                              "bias_8bit": [round(float(v), 3) for v in e.mean(0)],
                              "luma_rms": round(float(np.sqrt((ey ** 2).mean())), 3),
                              "luma_bias": round(float(ey.mean()), 3),
                              "luma_p95_abs": round(float(np.percentile(np.abs(ey), 95)), 3),
                              "within_3_codes": bool(abs(ey.mean()) <= 3 and np.all(np.abs(e.mean(0)) <= 3))}
        return out


def cmd_fit(a):
    t0 = time.time()
    pb = Problem(a.spec)
    pb.load()
    t1 = time.time()
    table, best = [], None
    for name, opts in pb.configs:
        W, chroma, obj, its = pb.solve_config(opts)
        table.append({"variant": name, "objective": obj})
        if best is None or obj < best[2]:
            best = (name, opts, obj, W, chroma, its)
    name, opts, obj, W, chroma, its = best
    k = pb.gain(opts, W)
    W = {l: w * k for l, w in W.items()}
    res = pb.residuals(opts, W)
    t2 = time.time()
    out = {"about": f"tools/lightfit.py fit {os.path.relpath(a.spec, ROOT) if a.spec.startswith(ROOT) else a.spec}: "
                    "camera-RGB weight per light (multiplies its unit basis), non-negative least squares against the "
                    "original in raw camera RGB [F]",
           "weights": {l: [round(float(v), 6) for v in W[l]] for l in pb.lights},
           "basis": {l: opts[l].get("basis", pb.spec.get("basis")) for l in pb.lights},
           "variant": name, "gain": round(float(k), 6),
           "tie_chroma": {g: [round(float(v), 6) for v in c] for g, c in chroma.items()}, "tie_rounds": its,
           "residuals": res,
           "variants": sorted(table, key=lambda r: r["objective"]),
           "seconds": {"load": round(t1 - t0, 2), "solve": round(t2 - t1, 3)}}
    json.dump(out, open(a.out, "w"), indent=1)
    for r in sorted(table, key=lambda r: r["objective"])[:a.show]:
        print(f"  {r['objective']:.6g}  {r['variant']}")
    if len(table) > a.show:
        print(f"  ... {len(table)} variants")
    print(f"best: {name}  gain {k:.5g}  tie chroma {out['tie_chroma']}")
    for l in pb.lights:
        print(f"{l:>8} {np.round(W[l], 4)}")
    for fn, r in res.items():
        print(f"{fn:>8}{' (held out)' if r['held_out'] else '':11} rms RGB {r['rms_8bit']} bias RGB {r['bias_8bit']} "
              f"luma rms {r['luma_rms']} bias {r['luma_bias']} p95 {r['luma_p95_abs']} "
              f"{'within 3' if r['within_3_codes'] else 'NOT within 3'}")
    print(f"load {t1 - t0:.2f} s, solve {len(table)} variants {t2 - t1:.3f} s -> {a.out}")


def cmd_mix(a):
    spec = json.load(open(a.spec))
    L = json.load(open(a.weights))
    os.makedirs(a.out, exist_ok=True)
    want = a.frames.split(",") if a.frames else None
    pb = Problem.__new__(Problem)
    pb.spec = spec
    per = L.get("per_frame", {})          # optional {light: {frame: factor}}, e.g. a key that follows the original
    for fr in spec["frames"]:
        if want and fr["name"] not in want:
            continue
        img = 0
        for l, w in L["weights"].items():
            if not np.any(w):
                continue
            p = pb.basis_path(fr, l, {"basis": L["basis"][l]} if L.get("basis", {}).get(l) else {})
            img = img + read_image(p) * np.array(w) * per.get(l, {}).get(fr["name"], 1.0)
        write_pfm(os.path.join(a.out, fr["name"] + ".pfm"), img)
        print(os.path.join(a.out, fr["name"] + ".pfm"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("fit")
    s.add_argument("spec")
    s.add_argument("--out", required=True)
    s.add_argument("--show", type=int, default=8, help="variants to print")
    s = sub.add_parser("mix")
    s.add_argument("spec")
    s.add_argument("weights")
    s.add_argument("--out", required=True)
    s.add_argument("--frames", help="comma-separated frame names (default all)")
    a = ap.parse_args()
    {"fit": cmd_fit, "mix": cmd_mix}[a.cmd](a)


if __name__ == "__main__":
    main()
