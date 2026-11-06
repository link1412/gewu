"""The recipe tool, v0 (docs/optics.md): an object, a rig, a camera and a development, built into a picture.

    python3 -I tools/build.py RECIPE.json --preview          # 480x270: write, render, mix, develop, sheet
    python3 -I tools/build.py RECIPE.json --check            # the same at 960x540
    python3 -I tools/build.py RECIPE.json --remix            # mix and develop again from the renders already pulled
    python3 -I tools/build.py RECIPE.json --stage-only       # write the scenes, no render
    options: --spp N, --seed S, --lane cycles|gpu|cpu (cycles: the default for previews; gpu;
             cpu), --remote-tools DIR (where cycles_scene.py is on the render machine), --pbrt (also render each group
             with pbrt on the CPU slots, as a reference), --out DIR (default out/recipes/<recipe name>)

The flow:
1. Stage, in OUT: the object's files (copied flat: pbrt resolves every name against the main scene's directory),
   backdrop.ply, rig.pbrt (every lamp tagged with its group, Attribute "light" "string group"), scene.pbrt =
   camera + Include "rig.pbrt" + Include the object (moved to stand on the floor, centred on Z); pbrt renders it as
   it is. Also rig.<group>.pbrt and scene.<group>.pbrt, the same with only that group lit (pbrt's references),
   optics.json (diffraction), camera.json (development), build.json (where everything went). Then rgbscene.
2. Render: push OUT to the render machine, one Cycles job; it writes x.exr and x.<group>.exr per group (one render, same
   samples), x.albedo.exr and x.normal.exr. Pull them.
3. Mix: raw = sum 2^stops[g] raw_g. Light adds, so this is the render those lamps at those strengths would give.
   The variants for the sheet are made the same way: each group at -1 and +1 stop, and each alone.
4. Denoise (if the recipe asks): after mixing, never before (a denoiser is not linear): every mix through OIDN with the
   render's albedo and normal, in Blender's compositor (tools/cycles_denoise.py, on this machine's Blender).
5. Develop: tools/camera.py's chain; one exposure for all variants (from the base mix, or camera.json's raw_ref),
   so a stop up looks a stop brighter.
6. Out: OUT/dev/<variant>.png (16-bit, 1080p), OUT/sheet.png (rows: groups; columns: -1, base, +1, alone) and
   OUT/mix.json (the stops, each group's share of the light).

A recipe (JSON; paths relative to the repository):
  {"object": {"file": "out/optics/objects/dome_glaze/dome_glaze.pbrt"},
   "rig": "optics/rigs/product_three.json", "rig_overrides": {"lamps.key.lux": 3000, "backdrop.material": "rose"},
   "camera": {"focal_mm": 100, "f_number": 11, "azimuth_deg": 0, "elevation_deg": 20, "frame": {"arc_of_shot": 20}},
             (or "fill": 0.8, "aim": "centre" for the whole object; "frame" needs the object's <name>.silhouette.json)
   "render": {"spp": 128, "maxdepth": 32, "refractivenee": true, "denoise": true, "seed": 0},
   "mix": {"key": 0, "rim": -0.5},
   "develop": {...camera.json without "light" (the rig's spectrum gives it)...},
   "sheet": {"stops": 1}}
"""

import argparse
import glob
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
import camera as C  # noqa: E402
import framing  # noqa: E402
import rgbscene  # noqa: E402
import studio  # noqa: E402

REMOTE = "~/gewu-render/scenes"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
SENSOR = "canon_eos_5d_mkiv"
RESERVED = ("scene", "rig", "backdrop", "optics", "camera", "build", "mix", "x", "pbrt", "sheet")


def rel(p):
    return os.path.join(ROOT, p) if not os.path.isabs(p) else p


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, check=True, **kw)


# --- 1. stage --------------------------------------------------------------------------------
def header(cam, res, spp, render, film):
    lines = [f"# written by tools/build.py"] + cam.lines()
    lines.append(f'Sampler "zsobol" "integer pixelsamples" [ {spp} ]')
    integ = f'Integrator "volpath" "integer maxdepth" [ {render.get("maxdepth", 32)} ]'
    if render.get("refractivenee"):
        integ += ' "bool refractivenee" true'
    lines.append(integ)
    lines.append(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
                 f'"string filename" [ "{film}" ] "string sensor" [ "{SENSOR}" ] "float iso" [ 100 ] "bool rawsensor" true')
    lines.append("WorldBegin")
    return lines


def stage(recipe, out, res, spp):
    os.makedirs(out, exist_ok=True)
    obj = rel(recipe["object"]["file"])
    if not os.path.isfile(obj):
        raise SystemExit(f"object {obj}: no such file")
    obj_files = []
    for f in sorted(os.listdir(os.path.dirname(obj))):
        src = os.path.join(os.path.dirname(obj), f)
        if os.path.isfile(src):
            if os.path.splitext(f)[0].split(".")[0] in RESERVED:
                raise SystemExit(f"object file {f}: its name is one of the recipe's own ({RESERVED})")
            shutil.copy2(src, os.path.join(out, f))
            obj_files.append(f)
    obj_name = os.path.basename(obj)
    rig = studio.load(rel(recipe["rig"]))
    K = rig["spectrum"].get("blackbody_K")
    if K is None:
        raise SystemExit("v0: the rig's spectrum must be a blackbody (camera.json's light and rgbscene's key are)")
    lo, hi = studio.bounds(os.path.join(out, obj_name), K)
    shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])     # on the floor, centred on Z
    lo, hi = lo + shift, hi + shift
    sil = os.path.splitext(obj)[0] + ".silhouette.json"         # written by the object's generator, if it can be
    sil = framing.Revolved(sil, shift) if os.path.isfile(sil) else None
    cam = studio.Camera(recipe["camera"], lo, hi, res, sil)
    st = studio.Studio(rig, lo, hi, cam, recipe.get("rig_overrides"))
    if st.back:
        studio.write_ply(os.path.join(out, "backdrop.ply"), *st.sweep_mesh())
    groups = st.groups()
    render = recipe.get("render", {})
    obj_lines = ["AttributeBegin", f"  Translate {shift[0]:.4f} {shift[1]:.4f} {shift[2]:.4f}",
                 f'  Include "{obj_name}"', "AttributeEnd"]
    st.write(os.path.join(out, "rig.pbrt"))
    with open(os.path.join(out, "scene.pbrt"), "w") as f:
        f.write("\n".join(header(cam, res, spp, render, "pbrt.exr") + ['Include "rig.pbrt"'] + obj_lines) + "\n")
    for g in groups:
        st.write(os.path.join(out, f"rig.{g}.pbrt"), only=g)
        with open(os.path.join(out, f"scene.{g}.pbrt"), "w") as f:
            f.write("\n".join(header(cam, res, spp, render, f"pbrt.{g}.exr") + [f'Include "rig.{g}.pbrt"'] + obj_lines) + "\n")
    json.dump(cam.optics_json(), open(os.path.join(out, "optics.json"), "w"), indent=1)
    dev = dict(recipe["develop"])
    dev["light"] = {"blackbody_K": K, "why": "the rig's spectrum (all its lamps, v0)"}
    dev.setdefault("sensor", SENSOR)
    json.dump(dev, open(os.path.join(out, "camera.json"), "w"), indent=1)
    info = {"recipe": recipe, "res": list(res), "spp": spp, "groups": groups, "object_shift_mm": shift.tolist(),
            "object_files": obj_files,
            "camera": cam.summary(), **st.summary()}
    json.dump(info, open(os.path.join(out, "build.json"), "w"), indent=1, default=float)
    sc = rgbscene.convert(os.path.join(out, "scene.pbrt"), SENSOR, K)
    json.dump(sc, open(os.path.join(out, "scene.cycles.json"), "w"), indent=1)
    print(f"staged {out}: groups {groups}, R {st.R:.1f} mm, camera {cam.u:.0f} mm away, fov {cam.fov:.2f} deg, "
          f"frame {cam.sensor_w / cam.magnification:.1f} mm wide")
    if cam.arc is not None:
        print(f"  arc: {cam.arc} (target {cam.arc_target})")
    for L in st.lamps:
        print(f"  {L['name']:>8s} [{L['group']}] {L['shape']:5s} {L['lux']:7.0f} lux at target, luminance "
              f"{L['luminance']:9.4g}, {L['clear_px']:7.1f} px outside the frame" + (" (in frame)" if L["in_frame"] else "")
              + (f", {L['hidden_px']:.0f} px under the silhouette" if L.get("behind_object") else ""))
    return groups


# --- 2. render --------------------------------------------------------------------
def remote_dir(name):
    return f"{REMOTE}/recipe-{name}"


def push(out, name):
    """The staged scene: every file but images (renders, the sheet), plus the object's own files, images or not
    (its textures)."""
    d = remote_dir(name)
    sh(f"ssh link 'mkdir -p {d}'")
    files = [f for f in glob.glob(os.path.join(out, "*")) if os.path.isfile(f) and not f.endswith((".exr", ".png", ".pfm"))]
    bj = os.path.join(out, "build.json")
    if os.path.isfile(bj):
        files += [os.path.join(out, f) for f in json.load(open(bj)).get("object_files", [])
                  if f.endswith((".exr", ".png", ".pfm"))]
    sh("scp -q " + " ".join(files) + f" link:{d}/")
    return d


LANES = {"cycles": "mini-cycles.sh", "gpu": "mini-gpu.sh", "cpu": "mini-cpu.sh"}


def queue_cycles(name, lane, tools, extra, out_exr="x.exr", tag="", scene_json="scene.cycles.json"):
    d = remote_dir(name)
    log = f"/tmp/gewu-recipe-{name}{tag}.log"
    run = f"~/gewu-render/bin/{LANES[lane]} {log}" + (" blender" if lane == "cpu" else "")
    sh(f"ssh link 'rm -f {log}; cd {d} && nohup {run} -b --factory-startup --python-exit-code 1 "
       f"-P {tools}/cycles_scene.py -- {scene_json} --out $PWD/{out_exr} {extra} > /dev/null 2>&1 & echo queued'")
    return log


def queue_pbrt(name, scene, tag, extra=""):
    d = remote_dir(name)
    log = f"/tmp/gewu-recipe-{name}-{tag}.log"
    sh(f"ssh link 'rm -f {log}; cd ~ && nohup ~/gewu-render/bin/mini-pbrt.sh {d} {scene} {log} {extra} "
       f"> /dev/null 2>&1 & echo queued'")
    return log


def wait(logs):
    """Block until each log's last line is `done <code> ...` (the queue scripts write it); fail on a code not 0."""
    for log in logs:
        r = subprocess.run(f"ssh link 'while ! tail -1 {log} 2>/dev/null | grep -q \"^done\"; do sleep 3; done; "
                           f"head -1 {log}; tail -1 {log}'", shell=True, capture_output=True, text=True).stdout.split("\n")
        r = [x for x in r if x]
        print(log, "->", " | ".join(r))
        if not r or r[-1].split()[1] != "0":
            tail = subprocess.run(f"ssh link 'grep -v ^Fra: {log} | tail -25'", shell=True, capture_output=True, text=True).stdout
            raise SystemExit(f"{log} failed:\n{tail}")


def pull(name, files, out):
    d = remote_dir(name)
    sh("scp -q " + " ".join(f"link:{d}/{f}" for f in files) + f" {out}/")


# --- 3-5. mix, denoise, develop ---------------------------------------------------------------
def write_pfm(path, a):
    """(H, W, 3) float, row 0 the top; PFM stores the bottom row first."""
    a = np.asarray(a, "<f4")
    with open(path, "wb") as f:
        f.write(b"PF\n" + f"{a.shape[1]} {a.shape[0]}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(a[::-1]).tobytes())


def mix(raws, stops):
    out = 0.0
    for g, r in raws.items():
        s = stops.get(g, 0.0)
        if s is None:                         # off
            continue
        out = out + 2.0 ** s * r
    return np.asarray(out, float)


def variants(groups, base, step):
    """name -> stops: the base, each group -step and +step (the rest at base), each group alone (at its base)."""
    v = {"base": dict(base)}
    for g in groups:
        for s in (-step, step):
            v[f"{g}{s:+g}"] = {**base, g: base.get(g, 0.0) + s}
        v[f"{g}-alone"] = {h: (base.get(h, 0.0) if h == g else None) for h in groups}
    return v


def denoise(pairs, albedo, normal):
    """OIDN on each (in, out) with the render's albedo and normal, in this machine's Blender (tools/cycles_denoise.py)."""
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "-P", os.path.join(ROOT, "tools/cycles_denoise.py"),
           "--", "--albedo", albedo, "--normal", normal] + [p for pr in pairs for p in pr]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.count("DENOISED") != len(pairs):
        raise SystemExit("denoise failed:\n" + r.stdout[-3000:] + r.stderr[-2000:])


def develop_set(out, mixes, settings, use_psf=True):
    """Develop every mix with one exposure (the base mix's, unless camera.json fixes raw_ref). -> {name: rgb 1080p}"""
    cam, sensor = C.settings_camera(settings)
    S, light = C.Spectra(sensor["pbrt_sensor"]), C.light_spectrum(cam)
    cal = C.calibrate(S, C.balance_spectrum(cam))
    psf = C.airy_kernels(S, light, json.load(open(os.path.join(out, "optics.json"))))[0] if use_psf else None
    ex = cam["expose"]
    ref = ex["raw_ref"] if "raw_ref" in ex else float(np.percentile(mixes["base"].max(2), ex["percentile"]))
    os.makedirs(os.path.join(out, "dev"), exist_ok=True)
    rgbs = {}
    for name, raw in mixes.items():
        rgb, note = C.develop(raw, ref, cam, sensor, cal, np.random.default_rng([cam["seed"], 0]), psf)
        C.write_png16(os.path.join(out, "dev", f"{name}.png"), rgb)
        rgbs[name] = rgb
    return rgbs, ref


def tile(rgb, w):
    """A developed 1080p image, area-averaged down to width w, as 8-bit."""
    H, W, _ = rgb.shape
    k = W // w
    small = rgb[:H // k * k, :W // k * k].reshape(H // k, k, W // k, k, 3).mean((1, 3))
    return (np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)


def font(size):
    from PIL import ImageFont
    for f in ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/PingFang.ttc",
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def sheet(path, rows, title, w=480, lab=150):
    """rows: [(row label, [(caption, rgb), ...]), ...] -> one PNG with captions (a label may have several lines)."""
    from PIL import Image, ImageDraw
    ncol = max(len(r[1]) for r in rows)
    th = w * 9 // 16
    cap, top = 26, 44
    img = Image.new("RGB", (lab + ncol * (w + 6), top + len(rows) * (th + cap + 6)), (24, 24, 24))
    d = ImageDraw.Draw(img)
    d.text((10, 10), title, fill=(235, 235, 235), font=font(22))
    for i, (rl, cells) in enumerate(rows):
        y = top + i * (th + cap + 6)
        d.multiline_text((10, y + th // 2 - 12 * (rl.count("\n") + 1)), rl, fill=(235, 235, 235), font=font(20),
                         spacing=6)
        for j, (c, rgb) in enumerate(cells):
            x = lab + j * (w + 6)
            if rgb is not None:
                img.paste(Image.fromarray(tile(rgb, w)), (x, y))
            d.text((x + 4, y + th + 3), c, fill=(200, 200, 200), font=font(17))
    img.save(path)
    return path


def remix(out, recipe, use_psf=True):
    b = json.load(open(os.path.join(out, "build.json")))
    groups = b["groups"]
    raws = {g: C.read_raw(os.path.join(out, f"x.{g}.exr")) for g in groups}
    base = {g: float(recipe.get("mix", {}).get(g, 0.0)) for g in groups}
    step = float(recipe.get("sheet", {}).get("stops", 1.0))
    V = variants(groups, base, step)
    mixes = {n: mix(raws, s) for n, s in V.items()}
    noisy = mixes
    if recipe.get("render", {}).get("denoise", False):
        tmp = os.path.join(out, "mixes")
        os.makedirs(tmp, exist_ok=True)
        pairs = []
        for n, m in mixes.items():
            write_pfm(os.path.join(tmp, f"{n}.pfm"), m)
            pairs.append((os.path.join(tmp, f"{n}.pfm"), os.path.join(tmp, f"{n}.dn.exr")))
        denoise(pairs, os.path.join(out, "x.albedo.exr"), os.path.join(out, "x.normal.exr"))
        mixes = {n: C.read_raw(os.path.join(tmp, f"{n}.dn.exr")) for n in mixes}
    rgbs, ref = develop_set(out, mixes, os.path.join(out, "camera.json"), use_psf)
    # each group's share of the base mix's light: the camera's G channel summed over the pixels that do not see a lamp
    # (Cycles' denoising albedo of an emitter carries its emission, far above 1; a reflectance's albedo is at most 1)
    seen = C.read_raw(os.path.join(out, "x.albedo.exr")).max(2) <= 1.01
    tot = sum(2.0 ** base[g] * raws[g][..., 1][seen].sum() for g in groups)
    share = {g: float(2.0 ** base[g] * raws[g][..., 1][seen].sum() / tot) for g in groups}
    rig = json.load(open(rel(recipe["rig"])))
    rows = [(g, [(f"{g} -{step:g} 档", rgbs[f"{g}{-step:+g}"]),
                 (f"配方({'先混合再降噪' if noisy is not mixes else '未降噪'})", rgbs["base"]),
                 (f"{g} +{step:g} 档", rgbs[f"{g}{step:+g}"]), (f"只开 {g}(占 {share[g]:.0%},灯本身不算)", rgbs[f"{g}-alone"])])
            for g in groups]
    title = (f"{os.path.basename(out)}:{rig.get('title', rig['name'])};配方的档 " +
             ", ".join(f"{g} {base[g]:+g}" for g in groups) + f";曝光固定在配方这一张(raw {ref:.4g})")
    p = sheet(os.path.join(out, "sheet.png"), rows, title)
    json.dump({"base_stops": base, "variants": V, "share_of_light_G": share,
               "share_how": "G channel summed over pixels whose denoising albedo <= 1.01 (lamps seen directly, whose albedo carries their emission, excluded)", "raw_ref": ref,
               "denoised": noisy is not mixes}, open(os.path.join(out, "mix.json"), "w"), indent=1)
    print(f"sheet -> {p}; shares {', '.join(f'{g} {s:.1%}' for g, s in share.items())}")
    return rgbs


# --- main ------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("recipe")
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--preview", action="store_true", help="480x270")
    m.add_argument("--check", action="store_true", help="960x540")
    m.add_argument("--remix", action="store_true", help="mix and develop the renders already pulled")
    m.add_argument("--stage-only", action="store_true")
    ap.add_argument("--spp", type=int)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--lane", default="cycles", choices=sorted(LANES))
    ap.add_argument("--remote-tools", default="~/gewu-render/tools")
    ap.add_argument("--pbrt", action="store_true", help="also render each group with pbrt (CPU slots)")
    ap.add_argument("--pbrt-spp", type=int)
    ap.add_argument("--no-diffraction", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    recipe = json.load(open(a.recipe))
    name = os.path.splitext(os.path.basename(a.recipe))[0]
    out = a.out or os.path.join(ROOT, "out/recipes", name)
    if a.remix:
        remix(out, recipe, not a.no_diffraction)
        return
    res = (960, 540) if a.check else (480, 270)
    render = recipe.get("render", {})
    spp = a.spp or render.get("spp", 128)
    groups = stage(recipe, out, res, spp)
    if a.stage_only:
        return
    push(out, name)
    seed = a.seed if a.seed is not None else render.get("seed", 0)
    logs = [queue_cycles(name, a.lane, a.remote_tools, f"--spp {spp} --seed {seed}")]
    if a.pbrt:
        ps = a.pbrt_spp or spp
        logs += [queue_pbrt(name, f"scene.{g}.pbrt", f"pbrt-{g}", f"--spp {ps} --seed {seed}") for g in groups]
    wait(logs)
    files = ["x.exr", "x.json", "x.albedo.exr", "x.normal.exr"] + [f"x.{g}.exr" for g in groups]
    if a.pbrt:
        files += [f"pbrt.{g}.exr" for g in groups]
    pull(name, files, out)
    remix(out, recipe, not a.no_diffraction)


if __name__ == "__main__":
    main()
