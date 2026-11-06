"""Shared pieces of the qinghua tests: tests/textures/common.py's images and scene text, and the render queues with
test copies (the patched pbrt, cycles_scene.py).
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests/textures"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from common import (header, light_quad, pixel_rays, quad, read_image, read_pfm, sh, write_exr,  # noqa: E402,F401
                    write_pfm)

OUT = os.path.join(ROOT, "out/qinghua")
REMOTE = "~/gewu-render/scenes"
PBRT = "~/gewu-render/bin-qinghua/pbrt"
TOOLS = "~/gewu-render/tools-test-qinghua"


def rgbscene(scene, out, key_K=5500.0):
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), scene, "-o", out,
                    "--key-K", str(key_K)], check=True, stdout=subprocess.DEVNULL)


def push(name, files):
    d = f"{REMOTE}/qinghua-{name}"
    sh(f"ssh link 'mkdir -p {d}'")
    sh("scp -q " + " ".join(files) + f" link:{d}/")
    return d


def cycles(name, scene_json, out, extra="--spp 256", lane="mini-gpu.sh"):
    d = f"{REMOTE}/qinghua-{name}"
    log = f"/tmp/gewu-qh-{name}-{os.path.splitext(out)[0]}.log"
    sh(f"ssh link 'rm -f {log}; cd {d} && nohup ~/gewu-render/bin/{lane} {log} -b --factory-startup "
       f"--python-exit-code 1 -P {TOOLS}/cycles_scene.py -- {scene_json} --out $PWD/{out} {extra} > /dev/null 2>&1 & echo queued'")
    return log


def pbrt(name, scene, tag, extra=""):
    """The patched pbrt on a CPU slot, 4 threads."""
    d = f"{REMOTE}/qinghua-{name}"
    log = f"/tmp/gewu-qh-{name}-{tag}.log"
    sh(f"ssh link 'rm -f {log}; cd ~ && nohup ~/gewu-render/bin/mini-cpu.sh {log} run {d} {PBRT} --quiet --nthreads 4 "
       f"{extra} {scene} > /dev/null 2>&1 & echo queued'")
    return log


def wait(logs):
    for log in logs:
        r = subprocess.run(f"ssh link 'while ! tail -1 {log} 2>/dev/null | grep -q \"^done\"; do sleep 5; done; tail -3 {log}'",
                           shell=True, capture_output=True, text=True).stdout.strip().splitlines()
        print(log, "->", r[-1] if r else "?")
        if not r or r[-1].split()[1] != "0":
            raise SystemExit(f"{log} failed:\n" + "\n".join(r))


def pull(name, files, local):
    os.makedirs(local, exist_ok=True)
    d = f"{REMOTE}/qinghua-{name}"
    sh("scp -q " + " ".join(f"link:{d}/{f}" for f in files) + f" {local}/")
