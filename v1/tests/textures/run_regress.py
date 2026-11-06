"""Test d, the runs: the old tools/cycles_scene.py (git HEAD) and the new
one on two existing scenes, same seed and spp, plus a second seed of the old one for the noise floor.
  shot 19: out/19/shot2/f05.cycles.json (lobe.ply, inlay.npz);  shot 6: out/06/shot3/common/scene_f3.cycles.json (its .ply files).

    python3 -I tests/textures/run_regress.py [--spp 32] [--res 480x270]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--spp", type=int, default=32)
ap.add_argument("--res", default="480x270")
a = ap.parse_args()
d = os.path.join(C.OUT, "regress")
os.makedirs(d, exist_ok=True)
src = {"s19": (os.path.join(C.ROOT, "out/19/shot2"), ["f05.cycles.json", "lobe.ply", "inlay.npz"], "f05.cycles.json"),
       "s06": (os.path.join(C.ROOT, "out/06/shot3/common"), ["scene_f3.cycles.json"] + [os.path.basename(p) for p in glob.glob(os.path.join(C.ROOT, "out/06/shot3/common/*.ply"))], "scene_f3.cycles.json")}
logs = []
for name, (dirn, files, scene) in src.items():
    C.push(f"reg-{name}", [os.path.join(dirn, f) for f in files])
    extra = f"--spp {a.spp} --res {a.res}"
    logs += [C.cycles(f"reg-{name}", scene, "old1.exr", extra + " --seed 1", py="cycles_scene_old.py"),
             C.cycles(f"reg-{name}", scene, "old2.exr", extra + " --seed 2", py="cycles_scene_old.py"),
             C.cycles(f"reg-{name}", scene, "new1.exr", extra + " --seed 1"),
             C.cycles(f"reg-{name}", scene, "new2.exr", extra + " --seed 2")]
C.wait(logs)
for name in src:
    C.pull(f"reg-{name}", [f"{n}.exr" for n in ("old1", "old2", "new1", "new2")], os.path.join(d, name))
