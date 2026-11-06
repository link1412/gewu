"""Shot 17 round 1: from the one render to 8 developed 1080p frames (docs/shots/17-peacock.md).

    python3 -I shots/17-peacock/shot.py [--r out/shots/17-peacock/r1] [--mini gewu-render/scenes/17pk/r1] [--skip-fit]

The original holds still for its 8 frames (spec motion.moves false, frame-to-frame mean |diff| 0.14), so there is one
render (scene.py, Cycles GPU, a pass per light group) and the 8 frames differ only by the camera's per-frame noise.
1. fetch the passes, albedo, normal (R/raw/f00/);
2. tools/lightfit.py fit (spec lightfit.json: the original's mean of frames 236-243, regions above and below the
   arc) unless --skip-fit, then mix -> R/mix/f00.pfm (raw camera RGB);
3. denoise the mix (tools/cycles_denoise.py, OIDN with the render's albedo and normal; on the CPU);
4. float Lanczos (PIL, per channel, not ffmpeg: it clamps float to 1) 1280x720 -> 1920x1080, then tools/camera.py
   develop with camera.json (diffraction from optics.json, per-frame noise), film frames 236-243 -> R/dev1080/.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as camera_mod  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

PY = sys.executable
F0, NF = 236, 8


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit(f"{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def write_pfm(path, img):
    img = np.asarray(img, np.float32)
    with open(path, "wb") as f:
        f.write(f"PF\n{img.shape[1]} {img.shape[0]}\n-1.0\n".encode())
        f.write(np.ascontiguousarray(img[::-1]).astype("<f4").tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r", default=os.path.join(ROOT, "out/shots/17-peacock/r1"))
    ap.add_argument("--mini", default="gewu-render/scenes/17pk/r1")
    ap.add_argument("--skip-fit", action="store_true")
    ap.add_argument("--skip-fetch", action="store_true")
    a = ap.parse_args()
    R = os.path.abspath(a.r)
    raw = os.path.join(R, "raw", "f00")
    os.makedirs(raw, exist_ok=True)
    if not a.skip_fetch:
        run(["scp", "-q", f"link:{a.mini}/f00/x*.exr", raw + "/"])
    spec = os.path.join(HERE, "lightfit.json")
    weights = os.path.join(HERE, "lights.json")
    if not a.skip_fit:
        print(run([PY, "-I", os.path.join(ROOT, "tools/lightfit.py"), "fit", spec, "--out", weights]))
    mixd = os.path.join(R, "mix")
    print(run([PY, "-I", os.path.join(ROOT, "tools/lightfit.py"), "mix", spec, weights, "--out", mixd]))
    mix = os.path.join(mixd, "f00.pfm")
    md = f"{a.mini}/den"
    run(["ssh", "link", f"mkdir -p {md} && find {md} -name '*.exr' -delete && find {md} -name '*.pfm' -delete"])
    run(["scp", "-q", mix, f"link:{md}/m00.pfm"])
    print(run(["ssh", "link", f"cd ~/{md} && ~/gewu-render/bin/mini-cpu.sh /tmp/gewu-17pk-den.log blender -b --factory-startup "
               f"--python-exit-code 1 -P ~/gewu-render/tools/cycles_denoise.py -- --albedo ~/{a.mini}/f00/x.albedo.exr "
               f"--normal ~/{a.mini}/f00/x.normal.exr m00.pfm $PWD/d00.exr > /dev/null 2>&1; tail -1 /tmp/gewu-17pk-den.log"]))
    den = os.path.join(R, "den")
    os.makedirs(den, exist_ok=True)
    run(["scp", "-q", f"link:{md}/d00.exr", den + "/"])
    up = os.path.join(R, "up1080")
    os.makedirs(up, exist_ok=True)
    pfm = os.path.join(up, "d00.lo.pfm")
    run([os.path.join(ROOT, "third_party/pbrt-build/imgtool"), "convert", "--outfile", pfm, os.path.join(den, "d00.exr")])
    lo = camera_mod.read_raw(pfm)
    hi = np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(lo[..., c], np.float32), "F").resize((1920, 1080), Image.LANCZOS))
                   for c in range(3)], -1)
    if not np.isfinite(hi).all():
        raise SystemExit("NaN or inf after the upscale")
    os.remove(pfm)
    names = []
    for k in range(NF):              # the same still for every frame; the camera adds each frame's own noise
        p = os.path.join(up, f"u{k:02d}.pfm")
        write_pfm(p, np.maximum(hi, 0.0))
        names.append(p)
    shutil.copy(os.path.join(R, "build/optics.json"), up)
    dev = os.path.join(R, "dev1080")
    print(run([PY, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings", os.path.join(HERE, "camera.json"),
               "--first", str(F0), "--out", dev] + names))


if __name__ == "__main__":
    main()
