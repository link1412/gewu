"""Test c: the test objects under every rig, side by side with each rig's look targets from the reference film.

    python3 -I tests/optics/sheet_rigs.py [--recipes dome_glaze-museum_flat,...] [--out out/optics/rigs_sheet.png]

Needs the recipes built first (python3 -I tools/build.py tests/optics/recipes/<recipe>.json --preview). Each row:
our base mix (out/recipes/<recipe>/dev/base.png, the recipe's stops, denoised after mixing, developed) and the
frames the rig's JSON names as its look target in ref/reference-film.mp4 (a target for the light
only; decoded as BT.709, as viewers see it). Each recipe is framed to the arc of the original's shot of its rig's
first look target. The objects (tests/optics/gen_object.py) are test objects, not material cards: shot 6's glaze on a
dome (not validated), a diffuse dome with a bump-mapped test relief, a thin marble disc (Jensen 2001's marble).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build as B  # noqa: E402
import camera as C  # noqa: E402
from compare import DECODE_VF  # noqa: E402

RECIPES = ["dome_glaze-museum_flat", "dome_glaze-product_three", "dome_relief-raking_hard", "plate_marble-backlit",
           "dome_glaze-dark_field"]
OBJECTS = {"dome_glaze": "釉面穹顶\n(06 的釉,未验)", "dome_relief": "浮雕穹顶\n(凹凸贴图试片,\n颜色是占位)",
           "plate_marble": "4 mm 大理石薄板\n(Jensen 2001 实测,\n代替玉)", "vase": "06 的瓶"}


def video_frame(path, n, w=480, h=270):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf",
                          f"select=eq(n\\,{n}),{DECODE_VF},scale={w}:{h}:flags=area", "-fps_mode", "passthrough",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipes", default=",".join(RECIPES))
    ap.add_argument("--out", default=os.path.join(ROOT, "out/optics/rigs_sheet.png"))
    a = ap.parse_args()
    rows = []
    for name in a.recipes.split(","):
        recipe = json.load(open(os.path.join(HERE, f"recipes/{name}.json")))
        rig = json.load(open(os.path.join(ROOT, recipe["rig"])))
        d = os.path.join(ROOT, f"out/recipes/{name}")
        ours = C.read_png16(os.path.join(d, "dev/base.png"))
        mix = json.load(open(os.path.join(d, "mix.json")))
        info = json.load(open(os.path.join(d, "build.json")))
        groups = ", ".join(f"{g} {s:+g}" for g, s in mix["base_stops"].items() if s) or "各组 0 档"
        ground = info["backdrop"]["material"] if info.get("backdrop") else "无"
        shot = recipe["camera"].get("frame", {}).get("arc_of_shot")
        cells = [(f"我们:{groups};底 {ground}" + (f";弧:原片 {shot}" if shot else ""), ours)]
        vm = rig["look_target"]
        for s in vm["shots"]:
            f = video_frame(os.path.join(ROOT, vm["film"]), s["frame"]).astype(float) / 255
            cells.append((f"参照片 第 {s['shot']} 镜 帧 {s['frame']}", np.kron(f, np.ones((4, 4, 1)))))
        rows.append((rig["title"] + "\n" + OBJECTS.get(name.split("-")[0], ""), cells))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    B.sheet(a.out, rows, lab=200, title="五套灯,各配一件能显出这套灯的试物,按原片的弧取景;右边三张是外观目标(参照片,只看光)")
    print("->", a.out)


if __name__ == "__main__":
    main()
