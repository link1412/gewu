"""Shot 19 round 1: from the 12 renders to developed 1080p frames (docs/shots/19-luodian.md).

    python3 -I shots/19-luodian/shot.py [--r out/shots/19-luodian/r1] [--mini gewu-render/scenes/19lu/r1b] [--skip-fit]

The scenes are made by scene.py (--frame 0..11, the key moved, all else the same) and rendered on the GPU with
light groups (each light's pass from one render, tools/cycles_scene.py). Here:
1. fetch every frame's passes, albedo and normal (R/raw/fNN/);
2. fit.py fit (frame 5) and key (all frames) unless --skip-fit; fit.py mix -> R/mix/mNN.pfm (raw camera RGB);
3. denoise each mix (tools/cycles_denoise.py, OIDN with that render's albedo and normal; on the CPU);
4. Lanczos-upscale each denoised raw 960x540 -> 1920x1080 (PIL, float, unclamped; not ffmpeg, which clamps to 1), then tools/camera.py develop with this shot's
   camera.json (diffraction from optics.json, per-frame sensor noise at 1080, film frames 255-266) -> R/dev1080/fNNNN.png
   (16-bit). The upscale is before the noise, so the grain is at the film's pixel size.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import fit  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as camera_mod  # noqa: E402

PY = sys.executable


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit(f"{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r", default=os.path.join(ROOT, "out/shots/19-luodian/r1"))
    ap.add_argument("--mini", default="gewu-render/scenes/19lu/r1b")
    ap.add_argument("--skip-fit", action="store_true")
    a = ap.parse_args()
    R = os.path.abspath(a.r)
    raw = os.path.join(R, "raw")
    n = fit.N
    # 1. fetch
    for k in range(n):
        d = os.path.join(raw, f"f{k:02d}")
        os.makedirs(d, exist_ok=True)
        run(["scp", "-q", f"link:{a.mini}/f{k:02d}/x*.exr", d + "/"])
    lights = os.path.join(HERE, "lights.json")
    # 2. fit and mix
    if not a.skip_fit:
        print(run([PY, "-I", os.path.join(HERE, "fit.py"), "fit", "--raw", os.path.join(raw, "f05"), "--out", lights]))
        print(run([PY, "-I", os.path.join(HERE, "fit.py"), "key", "--raw", raw, "--lights", lights]))
    mixd = os.path.join(R, "mix")
    print(run([PY, "-I", os.path.join(HERE, "fit.py"), "mix", "--raw", raw, "--lights", lights, "--out", mixd]))
    # 3. denoise (one Blender per frame: each frame's own albedo and normal)
    md = f"{a.mini}/den"
    run(["ssh", "link", f"mkdir -p {md} && find {md} -name '*.exr' -delete && find {md} -name '*.pfm' -delete"])   # zsh: no bare globs
    run(["scp", "-q"] + [os.path.join(mixd, f"m{k:02d}.pfm") for k in range(n)] + [f"link:{md}/"])
    loop = (f"cd ~/{md} && for k in $(seq -f %02g 0 {n - 1}); do ~/gewu-render/bin/mini-cpu.sh /tmp/gewu-19lu-den.log "
            "blender -b --factory-startup --python-exit-code 1 -P ~/gewu-render/tools/cycles_denoise.py -- "
            f"--albedo ~/{a.mini}/f$k/x.albedo.exr --normal ~/{a.mini}/f$k/x.normal.exr m$k.pfm $PWD/d$k.exr "
            "> /dev/null 2>&1; tail -1 /tmp/gewu-19lu-den.log | grep -q '^done 0' || { echo failed $k; tail -20 /tmp/gewu-19lu-den.log; exit 1; }; done; echo ok")
    print(run(["ssh", "link", loop]))
    den = os.path.join(R, "den")
    os.makedirs(den, exist_ok=True)
    run(["scp", "-q", f"link:{md}/d*.exr", den + "/"])
    # 4. Lanczos to 1080, then the camera chain
    up = os.path.join(R, "up1080")
    os.makedirs(up, exist_ok=True)
    for k in range(n):
        pfm = os.path.join(up, f"d{k:02d}.540.pfm")
        run([os.path.join(ROOT, "third_party/pbrt-build/imgtool"), "convert", "--outfile", pfm, os.path.join(den, f"d{k:02d}.exr")])
        # Lanczos in float with PIL, per channel: ffmpeg's scale filter clamps float PFM to [0, 1], which cut the
        # raw highlights (the silver lip, key-lit shell at up to ~27x) to raw (1, 1, 1), and raw white is magenta once
        # white-balanced: round 1's neon rim and hot-pink pieces (docs/skill-notes.md)
        lo = camera_mod.read_raw(pfm)
        hi = np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(lo[..., c], np.float32), "F").resize((1920, 1080), Image.LANCZOS))
                       for c in range(3)], -1)
        if not np.isfinite(hi).all():
            raise SystemExit(f"{pfm}: NaN or inf after the upscale")
        fit.write_pfm(os.path.join(up, f"u{k:02d}.pfm"), np.maximum(hi, 0.0))     # Lanczos rings below 0 at edges
        os.remove(pfm)
    shutil.copy(os.path.join(R, "build/f05/optics.json"), up)
    dev = os.path.join(R, "dev1080")
    print(run([PY, "-I", os.path.join(ROOT, "tools/camera.py"), "develop", "--settings", os.path.join(HERE, "camera.json"),
               "--first", str(fit.F0), "--out", dev] + [os.path.join(up, f"u{k:02d}.pfm") for k in range(n)]))


if __name__ == "__main__":
    main()
