"""Shared pieces of the metal tests (docs/metals.md): the texture tests' image and scene helpers
(tests/textures/common.py), and the render queue with our own copy of the Cycles adapter.

Renders go to out/metals/<test>/. pbrt runs in a CPU slot
; Cycles on the GPU if it is free within 10 s, else a CPU slot, with
a test copy of cycles_scene.py.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "textures"))
from common import (ROOT, IMGTOOL, write_pfm, read_pfm, read_image, write_exr, header, light_quad, quad,  # noqa: E402,F401
                    pixel_rays, sh)

OUT = os.path.join(ROOT, "out/metals")
REMOTE = "~/gewu-render/scenes"
TOOLS_TEST = "~/gewu-render/tools-test-metal"


def deploy_adapter():
    sh(f"ssh link 'mkdir -p {TOOLS_TEST}'")
    sh(f"scp -q {ROOT}/tools/cycles_scene.py link:{TOOLS_TEST.replace('~/', '')}/cycles_scene.py")


def rgbscene(scene, out_json, key_K=5500):
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), scene, "-o", out_json,
                        "--key-K", str(key_K)], check=True, capture_output=True, text=True)
    return r.stdout


def push(name, files):
    d = f"{REMOTE}/metals-{name}"
    sh(f"ssh link 'mkdir -p {d}'")
    sh("scp -q " + " ".join(files) + f" link:{d.replace('~/', '')}/")
    return d


def cycles(name, scene_json, out, extra="--spp 64", script="mini-cycles.sh"):
    """Queue a Blender job; script mini-cycles.sh (GPU or a CPU slot) or mini-gpu.sh (the GPU only, for same-seed
    comparisons that must stay on one device)."""
    d = f"{REMOTE}/metals-{name}"
    log = f"/tmp/gewu-metal-{name}-{os.path.splitext(out)[0]}.log"
    sh(f"ssh link 'rm -f {log}; cd {d} && nohup ~/gewu-render/bin/{script} {log} -b --factory-startup "
       f"--python-exit-code 1 -P {TOOLS_TEST}/cycles_scene.py -- {scene_json} --out $PWD/{out} {extra} "
       f"> /dev/null 2>&1 & echo queued'", stdout=subprocess.DEVNULL)
    return log


def pbrt(name, scene, tag, extra=""):
    d = f"{REMOTE}/metals-{name}"
    log = f"/tmp/gewu-metal-{name}-{tag}.log"
    sh(f"ssh link 'rm -f {log}; cd ~ && nohup ~/gewu-render/bin/mini-pbrt.sh {d} {scene} {log} {extra} "
       f"> /dev/null 2>&1 & echo queued'", stdout=subprocess.DEVNULL)
    return log


def wait(logs):
    for log in logs:
        r = subprocess.run(f"ssh link 'while ! tail -1 {log} 2>/dev/null | grep -q \"^done\"; do sleep 5; done; "
                           f"head -1 {log}; tail -1 {log}'", shell=True, capture_output=True, text=True).stdout.strip().splitlines()
        print(log, "->", " | ".join(r))
        if not r or r[-1].split()[1] != "0":
            raise SystemExit(f"{log} failed: {r}")


def pull(name, files, local):
    os.makedirs(local, exist_ok=True)
    d = f"{REMOTE}/metals-{name}"
    sh("scp -q " + " ".join(f"link:{d.replace('~/', '')}/{f}" for f in files) + f" {local}/")
