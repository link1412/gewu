"""One command per shot (plan A, S10): render, fit the lights, develop, check, put the shot in the film.

    python3 -I tools/shotkit.py look 34              # 480x270, 64 spp: does the composition read? -> out/check/34-look/side.png
    python3 -I tools/shotkit.py run 34 [--round r1]  # 960x540 render, fit, offsets loop, 1080 frames, shotcheck, spec/film.json
      options: --from render|fit|develop|check (skip the steps before), --offsets N (max loops, default 2),
               --res WxH --spp N (override shot.json), --no-film (do not register), --dir shots/34-luopan (else found by number)

A shot directory shots/NN-*/ holds scene.py (runs in Blender; tools/kit_bpy.py's contract: --out --res
--spp --seed --device --frame, writes OUT, OUT.<group>.exr, OUT.albedo.exr, OUT.normal.exr, OUT.json) and shot.json:

{"shot": 34, "subject": "风水罗盘", "note": "one line for spec/film.json",
 "prep": [["python3", "-I", "face.py", "{build}/tex"]],  # local commands run in the shot dir before a render ({build}: the dir copied to the render machine)
 "files": ["helper.py"],                                  # more files from the shot dir to copy beside scene.py
 "scene_args": ["--tex", "tex"],                          # passed to scene.py; relative paths resolve in its dir on the render machine
 "per_frame": false,                                      # true: one render per film frame (--frame k); else one still for all frames
 "optics": {"f_number": 8, "magnification": 0.198, "focal_mm": 100},   # camera.py's diffraction (sensor 36 mm)
 "res": [960, 540], "spp": 256, "bounces": null,
 "camera": {"seed": 3434},                                # overrides of the default camera.json (DEFAULT_CAMERA)
 "bases": {"veil": "uniform", "glare": {"blur": "lamp", "sigma": 0.03}},   # extra light bases made here (sigma: of the width)
 "fit": {"res": [480, 270], "blocks": [8, 6], "band_weight": 1000,
         "lights": {"key": {}, "sky": {"tie": "key"}, "lamp": {"scalar": true}, "glow": {"fixed": 0.005},
                    "glare": {"tie": ["lamp", 1.0]}},     # tie: one scalar on the other's colour ([other, ratio]: held)
         "lead": {"light": "key", "others_max": 0.6}}}    # the other lights together give <= 0.6 of the key's light

The fit (S9's lessons, skill-notes 150-166): every light group's basis is denoised first (a noisy basis
averages low in codes); stage 1 is tools/lightfit.py (NNLS in linear raw); stage 2 here: per-channel weights by
bounded least squares on 8-bit codes through the camera chain (smooth clip at 0), on block means (content that differs
from the original's does not pull the levels) plus shotcheck's own region means (full, top60, middle, bottom) as
heavily weighted residuals; ties, held lights and the lead constraint are design choices [A]. Then the mix of the
noisy groups is denoised as one image (a denoiser is not linear), Lanczos to 1080 in float (ffmpeg clamps float),
camera.py develop (per-frame sensor noise), shotcheck. If shotcheck fails, its region errors are added to offsets
that move the region targets, and fit-develop-check runs again (the integral loop, skill-notes 161).
Weights are [F]. Outputs: out/shots/<dir>/<round>/{raw,mix,den,up1080,dev1080,fit*.json,lightfit.json,offsets.json}.
"""

import argparse
import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import camera  # noqa: E402
import lightfit as lf  # noqa: E402
import shotcheck  # noqa: E402

PY = sys.executable
IMGTOOL = os.path.join(ROOT, "third_party/pbrt-build/imgtool")
MINI_BASE = "gewu-render/scenes/kit"
REGIONS_1080 = {"full": (0, 1080), "top60": (0, 60), "middle": (360, 720), "bottom": (720, 1080)}   # shotcheck's
DEFAULT_CAMERA = {
    "sensor": "canon_eos_5d_mkiv",
    "light": {"blackbody_K": 5500, "why": "[A] daylight white balance (a fixed setting); emitters are white and each "
              "light group's colour is fitted per channel in raw camera RGB, so the balance only sets where the weights land"},
    "iso": 100,
    "expose": {"raw_ref": 1.0, "of_saturation": 0.7, "why": "fixed manual exposure; the weights are fitted at it"},
    "develop": {"ev": 0.0, "shoulder_from": 0.5},
    "sharpen": {"amount": 0.0, "sigma_px": 0.7},
    "seed": 1,
}
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f} s] {msg}", flush=True)


def run(cmd, cwd=None, quiet=False):
    if not quiet:
        log("+ " + " ".join(shlex.quote(str(c)) for c in cmd)[:400])
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        raise SystemExit(f"command failed ({r.returncode}): {' '.join(map(str, cmd))[:300]}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def write_pfm(path, a):
    h, w, _ = a.shape
    with open(path, "wb") as f:
        f.write(b"PF\n%d %d\n-1.0\n" % (w, h))
        f.write(np.ascontiguousarray(np.flipud(a), "<f4").tobytes())


def to_exr(path, a):
    tmp = path + ".tmp.pfm"
    write_pfm(tmp, a.astype(np.float32))
    run([IMGTOOL, "convert", "--outfile", path, tmp], quiet=True)
    os.remove(tmp)


def merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


# --- the shot -----------------------------------------------------------------------------------------------
class Shot:
    def __init__(self, n, d, rnd, res, spp):
        self.n = n
        if d:
            self.dir = os.path.abspath(d)
        else:
            c = sorted(glob.glob(os.path.join(ROOT, f"shots/{n:02d}-*/shot.json")))
            if len(c) != 1:
                raise SystemExit(f"shot {n}: {len(c)} shots/{n:02d}-*/shot.json (pass --dir)")
            self.dir = os.path.dirname(c[0])
        self.cfg = json.load(open(os.path.join(self.dir, "shot.json")))
        if self.cfg.get("shot") != n:
            raise SystemExit(f"{self.dir}/shot.json: shot {self.cfg.get('shot')} != {n}")
        self.name = os.path.basename(self.dir)
        self.spec = next(s for s in json.load(open(os.path.join(ROOT, "spec/shots.json")))["shots"] if s["shot"] == n)
        self.f0, self.f1 = self.spec["frame_in"], self.spec["frame_out"]
        self.N = self.f1 - self.f0
        self.per_frame = bool(self.cfg.get("per_frame"))
        self.frames = [f"f{k:02d}" for k in range(self.N if self.per_frame else 1)]
        self.round = rnd
        self.R = os.path.join(ROOT, "out/shots", self.name, rnd)
        self.mini = f"{MINI_BASE}/{self.name}/{rnd}"
        self.res = res or self.cfg.get("res", [960, 540])
        self.spp = spp or self.cfg.get("spp", 256)
        fit = self.cfg.get("fit", {})
        self.fit = fit
        self.fres = fit.get("res", [480, 270])
        self.lights_cfg = fit.get("lights") or {}
        os.makedirs(self.R, exist_ok=True)
        self.cam_path = os.path.join(self.R, "camera.json")
        json.dump(merge(DEFAULT_CAMERA, merge({"seed": 1000 + n}, self.cfg.get("camera"))), open(self.cam_path, "w"), indent=1)
        self.optics = {"sensor_width_mm": 36.0, **self.cfg["optics"]}

    def raw(self, fr):
        return os.path.join(self.R, "raw", fr)


# --- render -------------------------------------------------------------------------------------------------
def render(S):
    b = os.path.join(S.R, "build")
    shutil.rmtree(b, ignore_errors=True)
    os.makedirs(b)
    for cmd in S.cfg.get("prep", []):
        run([c.replace("{build}", b) for c in cmd], cwd=S.dir)
    for f in ["scene.py"] + S.cfg.get("files", []):
        src = os.path.join(S.dir, f)
        (shutil.copytree(src, os.path.join(b, os.path.basename(f))) if os.path.isdir(src) else shutil.copy(src, b))
    shutil.copy(os.path.join(TOOLS, "kit_bpy.py"), b)
    json.dump(S.spec, open(os.path.join(b, "shot.spec.json"), "w"), indent=1)
    W, H = S.res
    seed = S.cfg.get("render_seed", 0)
    args = " ".join(shlex.quote(x) for x in S.cfg.get("scene_args", []))
    lg = f"/tmp/gewu-kit-{S.n:02d}"
    ks = " ".join(f"{k:02d}" for k in range(len(S.frames)))
    script = f"""set -e
cd ~/{S.mini}
for k in {ks}; do
  mkdir -p f$k
  : > {lg}-r.log
  ~/gewu-render/bin/mini-gpu.sh {lg}-r.log -b --factory-startup --python-exit-code 1 -P scene.py -- --out $PWD/f$k/x.exr \\
    --res {W}x{H} --spp {S.spp} --seed {seed} --device GPU {"--frame $((10#$k))" if S.per_frame else ""} {args}
  tail -1 {lg}-r.log | grep -q '^done 0' || {{ tail -40 {lg}-r.log; echo RENDER-FAILED $k; exit 1; }}
  grep -h CYCLES_DONE {lg}-r.log | tail -1
done
"""
    open(os.path.join(b, "render.sh"), "w").write(script)
    run(["ssh", "link", f"rm -rf ~/{S.mini} && mkdir -p ~/{S.mini}"], quiet=True)
    run(["scp", "-q", "-r"] + glob.glob(os.path.join(b, "*")) + [f"link:{S.mini}/"])
    log(f"render {len(S.frames)} frame(s) {W}x{H} {S.spp} spp on the mini's GPU")
    print(run(["ssh", "link", f"bash ~/{S.mini}/render.sh"], quiet=True).strip())
    # each group's basis denoised (CPU slot): fitted on these, the mix of the noisy groups is denoised later
    groups = group_names(run(["ssh", "link", f"cd ~/{S.mini}/f00 && ls x.*.exr"], quiet=True).split())
    pairs = lambda k: " ".join(f"$PWD/f{k}/x.{g}.exr $PWD/f{k}/xd.{g}.exr" for g in groups)
    loop = "; ".join(
        f"~/gewu-render/bin/mini-cpu.sh {lg}-dg.log blender -b --factory-startup --python-exit-code 1 -P "
        f"~/gewu-render/tools/cycles_denoise.py -- --albedo $PWD/f{fr[1:]}/x.albedo.exr --normal $PWD/f{fr[1:]}/x.normal.exr "
        f"{pairs(fr[1:])} > /dev/null 2>&1; tail -1 {lg}-dg.log | grep -q '^done 0' || {{ tail -20 {lg}-dg.log; echo DENOISE-FAILED {fr}; exit 1; }}"
        for fr in S.frames)
    log(f"denoise {len(groups)} group bases x {len(S.frames)} frame(s): {', '.join(groups)}")
    run(["ssh", "link", f"cd ~/{S.mini} && {loop}"], quiet=True)
    for fr in S.frames:
        d = S.raw(fr)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    run(["scp", "-q", "-r"] + [f"link:{S.mini}/{fr}" for fr in S.frames] + [os.path.join(S.R, "raw") + "/"])
    for fr in S.frames:
        json.dump(S.optics, open(os.path.join(S.raw(fr), "optics.json"), "w"))
    extra_bases(S)


def extra_bases(S):
    """Bases made from the render: "uniform" (a lens veil: a flat add) or {"blur": group, "sigma": fraction of the
    width} (glare/bloom: a group's light spread by the lens's wide PSF tail) [A]."""
    for name, how in (S.cfg.get("bases") or {}).items():
        for fr in S.frames:
            d = S.raw(fr)
            ref = camera.read_raw(os.path.join(d, "x.albedo.exr"))
            h, w = ref.shape[:2]
            if how == "uniform":
                img = {"x": np.ones((h, w, 3)), "xd": np.ones((h, w, 3))}
            elif isinstance(how, dict) and "blur" in how:
                img = {}
                for p in ("x", "xd"):
                    src = camera.read_raw(os.path.join(d, f"{p}.{how['blur']}.exr"))
                    img[p] = np.stack([gaussian_filter(src[..., c], how["sigma"] * w, mode="nearest") for c in range(3)], -1)
            else:
                raise SystemExit(f"bases.{name}: unknown {how!r}")
            for p, a in img.items():
                to_exr(os.path.join(d, f"{p}.{name}.exr"), a)


def group_names(files):
    """Light groups from a render's files x.<group>.exr (not the albedo or normal)."""
    return sorted(f[2:-4] for f in files if f.startswith("x.") and f.endswith(".exr") and f.count(".") == 2
                  and f[2:-4] not in ("albedo", "normal", "layers"))


def groups_of(S):
    made = set(S.cfg.get("bases") or {})
    g = [x for x in group_names(os.listdir(S.raw("f00"))) if x not in made]
    return g + [k for k in (S.cfg.get("bases") or {}) if k not in g]


# --- fit ----------------------------------------------------------------------------------------------------
def lf_spec(S, prefix):
    lights = {}
    for l in groups_of(S):
        c = S.lights_cfg.get(l, {})
        o = {}
        if "fixed" in c:
            v = c["fixed"]
            o["fixed"] = v if isinstance(v, list) else [v] * 3
        lights[l] = o
    unknown = set(S.lights_cfg) - set(lights)
    if unknown:
        raise SystemExit(f"fit.lights {sorted(unknown)}: not groups of the render ({sorted(lights)})")
    fr = [{"name": f, "target": [S.f0 + k] if S.per_frame else f"{S.f0}-{S.f1 - 1}"} for k, f in enumerate(S.frames)]
    return {"camera": os.path.relpath(S.cam_path, ROOT), "shot": S.n, "res": S.fres, "target_average": "codes",
            "basis": os.path.relpath(os.path.join(S.R, "raw/{frame}/" + prefix + ".{light}.exr"), ROOT),
            "frames": fr, "target": {"kind": "image", "mask": [{"caption": True}]}, "weights": "channel", "lights": lights}


def fit(S, stage1=True):
    fs = os.path.join(S.R, "fitspec.json")
    json.dump(lf_spec(S, "xd"), open(fs, "w"), indent=1)
    json.dump(lf_spec(S, "x"), open(os.path.join(S.R, "mixspec.json"), "w"), indent=1)
    start_p = os.path.join(S.R, "lightfit.stage1.json")
    if stage1 or not os.path.exists(start_p):
        out = run([PY, "-I", os.path.join(TOOLS, "lightfit.py"), "fit", fs, "--out", start_p, "--show", "1"], quiet=True)
        log("lightfit stage 1: " + " | ".join(l.strip() for l in out.strip().splitlines()[-2:])[:300])
    codefit(S, json.load(open(fs)), json.load(open(start_p))["weights"])


def codefit(S, spec, start):
    W, H = S.fres
    M, cam = lf.chain(S.cam_path, None)
    m = lf.mask(spec["target"]["mask"], W, H, S.spec["arc"])
    lights = list(spec["lights"])
    cfg = S.lights_cfg
    yy, xx = np.nonzero(m)
    nx, ny = S.fit.get("blocks", [8, 6])
    blk = (yy * ny // H) * nx + xx * nx // W
    nb = nx * ny
    cnt = np.bincount(blk, minlength=nb)
    use = cnt > 0
    wb = np.sqrt(cnt[use] / cnt[use].mean())
    regs = {k: (yy >= a * H // 1080) & (yy < b * H // 1080) for k, (a, b) in REGIONS_1080.items()}
    regs = {k: v for k, v in regs.items() if v.any()}
    bw = np.sqrt(S.fit.get("band_weight", 1000))
    offp = os.path.join(S.R, "offsets.json")
    offs = json.load(open(offp)) if os.path.exists(offp) else {}

    def codes(raw):
        x = raw @ M.T
        x = 0.5 * (x + np.sqrt(x * x + 1e-6))                 # smooth clip at 0 (skill-notes 157)
        return 255 * camera.srgb_encode(camera.tone(x, cam["develop"]))

    def bmean(c):
        return np.stack([np.bincount(blk, c[:, k], minlength=nb)[use] / cnt[use] for k in range(3)], -1)

    def rmeans(c):
        return {k: c[s].mean(0) for k, s in regs.items()}

    # targets: the original's 1080 codes (cached decode), area-averaged to the fit grid: what shotcheck measures
    load = shotcheck.orig_frames(list(range(S.f0, S.f1)))
    Bs, TB, TR = [], [], []
    for k, fr in enumerate(S.frames):
        fl = [S.f0 + k] if S.per_frame else list(range(S.f0, S.f1))
        o = np.mean([load(f).astype(np.float64) for f in fl], 0)
        o = o.reshape(H, 1080 // H, W, 1920 // W, 3).mean((1, 3))[m]
        Bs.append(np.stack([lf.basis_at(lf.P(spec["basis"].format(frame=fr, light=l)), W, H)[m] for l in lights]))
        TB.append(bmean(o))
        TR.append({r: v - np.asarray(offs.get(r, [0, 0, 0])) for r, v in rmeans(o).items()})
    meanB = np.mean([B.mean(1) for B in Bs], 0)          # L,3: each light's mean raw signal at unit weight

    ties = {l: c["tie"] for l, c in cfg.items() if "tie" in c}
    fixed = {l: np.asarray(c["fixed"] if isinstance(c["fixed"], list) else [c["fixed"]] * 3, float)
             for l, c in cfg.items() if "fixed" in c}
    scalar = [l for l in lights if cfg.get(l, {}).get("scalar") and l not in fixed and l not in ties]
    free = [l for l in lights if l not in ties and l not in fixed and l not in scalar]
    tie_free = [l for l, t in ties.items() if not isinstance(t, list)]

    def weights(z):
        w, i = dict(fixed), 0
        for l in free:
            w[l] = z[i:i + 3]
            i += 3
        for l in scalar:
            w[l] = z[i] * np.ones(3)
            i += 1
        for l in tie_free:
            w[l] = z[i] * w[ties[l]]
            i += 1
        for l, t in ties.items():
            if isinstance(t, list):
                w[l] = t[1] * w[t[0]]
        return w

    lead = S.fit.get("lead")

    def resid(z):
        w = weights(z)
        out = []
        for B, tb, tr in zip(Bs, TB, TR):
            c = codes(np.einsum("lpc,lc->pc", B, np.array([w[l] for l in lights])))
            out.append(((bmean(c) - tb) * wb[:, None]).ravel())
            rm = rmeans(c)
            out.append(np.concatenate([bw * (rm[r] - tr[r]) for r in regs]))
        if lead:
            li = lights.index(lead["light"])
            amt = np.array([(w[l] * meanB[i]).sum() for i, l in enumerate(lights)])
            ratio = (amt.sum() - amt[li] + 1e-12) / (amt[li] + 1e-12)
            out.append([50.0 * max(0.0, np.log(ratio / lead["others_max"]))])
        return np.concatenate([np.ravel(x) for x in out])

    # start: lightfit's weights, each light floored at 5% of the brightest light's contribution (a 0 start sticks)
    st = {l: np.maximum(np.asarray(start.get(l, [0, 0, 0]), float), 0) for l in lights}
    contrib = {l: (st[l] * meanB[i]).sum() for i, l in enumerate(lights)}
    top = max(contrib.values()) or 1.0
    for i, l in enumerate(lights):
        floor = 0.05 * top / max(meanB[i].sum(), 1e-12)
        if contrib[l] < 0.05 * top:
            st[l] = np.maximum(st[l], floor / 3)
    z0 = np.concatenate([st[l] for l in free] + [[st[l].mean()] for l in scalar] +
                        [[max(st[l].mean() / max(st[ties[l]].mean(), 1e-9), 0.05)] for l in tie_free]) if (free or scalar or tie_free) else np.zeros(0)
    if z0.size:
        r = least_squares(resid, z0, bounds=(0, np.inf), x_scale=np.maximum(z0, 1e-4), diff_step=1e-3, max_nfev=3000)
        z = r.x
    else:
        z = z0
    w = weights(z)
    e0, e = resid(z0), resid(z)
    log(f"codefit: residual rms start {np.sqrt((e0 ** 2).mean()):.2f} -> {np.sqrt((e ** 2).mean()):.2f} (weighted codes)")
    pred = {}
    for fr, B, tr in zip(S.frames, Bs, TR):
        c = codes(np.einsum("lpc,lc->pc", B, np.array([w[l] for l in lights])))
        pred[fr] = {r: (np.round(v, 1).tolist(), np.round(v - tr[r], 1).tolist()) for r, v in rmeans(c).items()}
    amt = np.array([(w[l] * meanB[i]).sum() for i, l in enumerate(lights)])
    share = amt / max(amt.sum(), 1e-12)
    for i, l in enumerate(lights):
        log(f"   {l:>10} w {np.round(w[l], 5).tolist()}  light share {share[i]:.2f}")
    log(f"   predicted region codes - target (f00): " + ", ".join(f"{r} {d}" for r, (_, d) in pred[S.frames[0]].items()))
    json.dump({"about": "tools/shotkit.py codefit: per-channel weights on 8-bit block + region means through the "
                        "camera chain, started from lightfit stage 1 [F]",
               "weights": {l: [round(float(v), 8) for v in w[l]] for l in lights},
               "light_share": {l: round(float(s), 4) for l, s in zip(lights, share)},
               "offsets": offs, "predicted": pred},
              open(os.path.join(S.R, "lightfit.json"), "w"), indent=1)


# --- develop ------------------------------------------------------------------------------------------------
def develop(S, out_name="dev1080"):
    mixd = os.path.join(S.R, "mix")
    shutil.rmtree(mixd, ignore_errors=True)
    run([PY, "-I", os.path.join(TOOLS, "lightfit.py"), "mix", os.path.join(S.R, "mixspec.json"),
         os.path.join(S.R, "lightfit.json"), "--out", mixd], quiet=True)
    md = f"{S.mini}/den"
    run(["ssh", "link", f"rm -rf ~/{md} && mkdir -p ~/{md}"], quiet=True)
    run(["scp", "-q"] + [os.path.join(mixd, f"{fr}.pfm") for fr in S.frames] + [f"link:{md}/"], quiet=True)
    lg = f"/tmp/gewu-kit-{S.n:02d}-den.log"
    loop = "; ".join(
        f"~/gewu-render/bin/mini-cpu.sh {lg} blender -b --factory-startup --python-exit-code 1 -P "
        f"~/gewu-render/tools/cycles_denoise.py -- --albedo ~/{S.mini}/{fr}/x.albedo.exr --normal ~/{S.mini}/{fr}/x.normal.exr "
        f"$PWD/{fr}.pfm $PWD/{fr}.exr > /dev/null 2>&1; tail -1 {lg} | grep -q '^done 0' || {{ tail -20 {lg}; echo DENOISE-FAILED {fr}; exit 1; }}"
        for fr in S.frames)
    log(f"denoise the mix ({len(S.frames)} frame(s)) on the mini")
    run(["ssh", "link", f"cd ~/{md} && {loop}"], quiet=True)
    den = os.path.join(S.R, "den")
    shutil.rmtree(den, ignore_errors=True)
    os.makedirs(den)
    run(["scp", "-q"] + [f"link:{md}/{fr}.exr" for fr in S.frames] + [den + "/"], quiet=True)
    up = os.path.join(S.R, "up1080")
    shutil.rmtree(up, ignore_errors=True)
    os.makedirs(up)
    ups = []
    for fr in S.frames:
        lo = camera.read_raw(os.path.join(den, f"{fr}.exr"))
        hi = np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(lo[..., c], np.float32), "F").resize((1920, 1080), Image.LANCZOS))
                       for c in range(3)], -1)
        if not np.isfinite(hi).all():
            raise SystemExit(f"{fr}: NaN or inf after the upscale")
        u = os.path.join(up, f"{fr}.pfm")
        write_pfm(u, np.maximum(hi, 0.0))                  # Lanczos rings below 0 at edges
        ups.append(u)
    json.dump(S.optics, open(os.path.join(up, "optics.json"), "w"))
    dev = os.path.join(S.R, out_name)
    shutil.rmtree(dev, ignore_errors=True)
    raws = ups if S.per_frame else ups * S.N
    run([PY, "-I", os.path.join(TOOLS, "camera.py"), "develop", "--settings", S.cam_path, "--first", str(S.f0),
         "--out", dev] + raws, quiet=True)
    log(f"developed {S.N} frames -> {os.path.relpath(dev, ROOT)}")
    return dev


# --- check, offsets, film -----------------------------------------------------------------------------------
def check(S, dev, out):
    o = run([PY, "-I", os.path.join(TOOLS, "shotcheck.py"), str(S.n), "--frames", dev, "--out", out], quiet=True)
    r = json.load(open(os.path.join(ROOT, out, "shotcheck.json")))
    worst = {}
    for f, n in r["per_frame"].items():
        for k, d in n["diff"].items():
            if d:
                worst[k] = max(worst.get(k, 0), max(abs(x) for x in d))
    arc = r.get("arc", {})
    log(f"shotcheck {'PASS' if r['pass'] else 'FAIL'}: worst |diff| per region " +
        ", ".join(f"{k} {v:.1f}" for k, v in worst.items()) +
        (f"; arc apex {arc['ours']['apex']} sag ratio {arc['sag_ratio']} {'ok' if arc['ok'] else 'OFF'}" if arc.get("ours") else "; arc manual")
        + f" -> {out}/side.png")
    return r, o


def update_offsets(S, r):
    offp = os.path.join(S.R, "offsets.json")
    off = json.load(open(offp)) if os.path.exists(offp) else {}
    pf = list(r["per_frame"].values())
    for k in REGIONS_1080:
        ds = [n["diff"][k][:3] for n in pf if n["diff"].get(k)]
        if ds:
            e = np.mean(ds, 0)
            off[k] = [round(off.get(k, [0, 0, 0])[c] + float(e[c]), 2) for c in range(3)]
    json.dump(off, open(offp, "w"))
    log(f"offsets -> {off}")


def register(S, dev):
    import fcntl
    p = os.path.join(ROOT, "spec/film.json")
    lockf = open(p + ".lock", "w")
    fcntl.flock(lockf, fcntl.LOCK_EX)          # several shots register at once (parallel runs)
    d = json.load(open(p))
    e = d["shots"].get(str(S.n), {})
    e.update({"frames": os.path.relpath(dev, ROOT), "status": "preview",
              "note": f"shotkit {S.round}: " + S.cfg.get("note", "")})
    if S.cfg.get("subject"):
        e["subject"] = S.cfg["subject"]
    d["shots"][str(S.n)] = e
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    fcntl.flock(lockf, fcntl.LOCK_UN)
    log(f"spec/film.json: shot {S.n} -> {e['frames']}")


# --- commands -----------------------------------------------------------------------------------------------
STEPS = ["render", "fit", "develop", "check"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["look", "run"])
    ap.add_argument("shot", type=int)
    ap.add_argument("--round", default=None)
    ap.add_argument("--from", dest="start", choices=STEPS, default="render")
    ap.add_argument("--offsets", type=int, default=2)
    ap.add_argument("--res")
    ap.add_argument("--spp", type=int)
    ap.add_argument("--no-film", action="store_true")
    ap.add_argument("--dir")
    a = ap.parse_args()
    look = a.cmd == "look"
    res = [int(x) for x in a.res.split("x")] if a.res else ([480, 270] if look else None)
    spp = a.spp or (64 if look else None)
    S = Shot(a.shot, a.dir, a.round or ("look" if look else "r1"), res, spp)
    log(f"shot {S.n} ({S.name}) {a.cmd} round {S.round}: frames {S.f0}-{S.f1 - 1}, "
        f"{'one render per frame' if S.per_frame else 'one still'}, {S.res[0]}x{S.res[1]} {S.spp} spp")
    i = STEPS.index(a.start)
    if i <= 0:
        render(S)
    if i <= 1:
        offp = os.path.join(S.R, "offsets.json")
        if os.path.exists(offp) and a.start in ("render", "fit"):
            os.remove(offp)
        fit(S)
    dev = os.path.join(S.R, "dev1080")
    if i <= 2:
        dev = develop(S)
    out = os.path.relpath(os.path.join(ROOT, "out/check", f"{S.n}-look" if look else str(S.n)), ROOT)
    r, _ = check(S, dev, out)
    loops = 0 if look else a.offsets
    while not r["pass"] and loops > 0:
        loops -= 1
        update_offsets(S, r)
        fit(S, stage1=False)
        dev = develop(S)
        r, _ = check(S, dev, out)
    if not look and not a.no_film:
        register(S, dev)
    log(f"done: shot {S.n} {'PASS' if r['pass'] else 'FAIL'}; look at {out}/side.png and lifted.png")


if __name__ == "__main__":
    main()
