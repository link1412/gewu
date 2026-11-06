"""胭脂红 card, round 2: the light probe (docs/materials/yanzhi.md, "fitting the light").

One Cycles render carries many light groups; light adds, so any mix of the groups is the render those lamps at those
strengths would give (tools/build.py's mixing). The probe rig is a grid of left/right softbox pairs (one group per
pair: the museum's set-up is symmetric [A, Jin 2020]) over azimuth and elevation, plus the top light; the fit
(fit.py) then picks the pair's place and the strengths that make the render's wall look like the photo's.

    python3 -I materials/yanzhi/lightfit/probe.py rig  [--size 600] [--name probe] [--az ..] [--el ..] [--dist 1000]
    python3 -I materials/yanzhi/lightfit/probe.py run RECIPE.json [--spp 1024] [--res 960x540] [--lane gpu] [--no-wait]
    python3 -I materials/yanzhi/lightfit/probe.py pull RECIPE.json

`run` stages (tools/build.py's stage), pushes, queues one Cycles job and (unless --no-wait) waits and pulls
x.<group>.exr; no mixing, no denoising, no development (fit.py reads the raw groups).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

BASE = os.path.join(ROOT, "optics/rigs/museum_flat.json")


def make_rig(a):
    base = json.load(open(BASE))
    lamps = []
    for az, el, size in [(az, el, sz) for az in a.az for el in a.el for sz in a.size] + \
            [tuple(int(x) for x in e.split(",")) for e in a.extra]:
        if True:
            g = f"a{az:03d}e{el:02d}s{size:04d}"
            for side, s in (("L", -1), ("R", 1)):
                lamps.append({"name": f"{g}{side}", "group": g, "shape": "rect", "size": {"mm": [size, size]},
                              "at": {"anchor": "centre", "azimuth_deg": s * az, "elevation_deg": el,
                                     "distance": {"mm": a.dist}},
                              "aim": {"anchor": "centre"}, "lux": 1000,
                              "why": "probe: a softbox pair on the grid (fit.py picks one)"})
    if a.top:
        t = dict(next(l for l in base["lamps"] if l["name"] == "top"))
        lamps.append(t)
    rig = {"name": a.name, "title": "胭脂红卡：灯的探针", "what": "probe grid of softbox pairs (materials/yanzhi/lightfit)",
           "spectrum": base["spectrum"], "lamps": lamps,
           "backdrop": dict(base["backdrop"], distance={"R": a.back}, width={"R": 30},
                            **({"material": a.backdrop} if a.backdrop else {}),
                            why="museum_flat's grey sweep, moved back (10 R) so the rear probes fit in front of it [A]")}
    p = os.path.join(HERE, f"rig_{a.name}.json")
    json.dump(rig, open(p, "w"), indent=1, ensure_ascii=False)
    print("->", p, len(lamps), "lamps")


def run(a):
    recipe = json.load(open(a.recipe))
    name = os.path.splitext(os.path.basename(a.recipe))[0]
    out = os.path.join(ROOT, "out/materials/yanzhi/lightfit", name)
    res = tuple(int(x) for x in a.res.split("x"))
    groups = build.stage(recipe, out, res, a.spp)
    build.push(out, name)
    log = build.queue_cycles(name, a.lane, "~/gewu-render/tools", f"--spp {a.spp} --seed 0")
    json.dump({"log": log, "groups": groups}, open(os.path.join(out, "queued.json"), "w"))
    if not a.no_wait:
        pull(a)


def pull(a):
    name = os.path.splitext(os.path.basename(a.recipe))[0]
    out = os.path.join(ROOT, "out/materials/yanzhi/lightfit", name)
    q = json.load(open(os.path.join(out, "queued.json")))
    build.wait([q["log"]])
    build.pull(name, ["x.exr"] + [f"x.{g}.exr" for g in q["groups"]], out)
    print("pulled", out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rig")
    r.add_argument("--name", default="probe")
    r.add_argument("--size", type=int, nargs="+", default=[600])
    r.add_argument("--extra", nargs="*", default=[], help="more pairs as az,el,size")
    r.add_argument("--backdrop", default=None, help="backdrop material (optics/backdrops.json)")
    r.add_argument("--dist", type=float, default=1000)
    r.add_argument("--back", type=float, default=10)
    r.add_argument("--az", type=int, nargs="+", default=[30, 45, 60, 75, 90, 110, 135])
    r.add_argument("--el", type=int, nargs="+", default=[10, 25, 40, 55])
    r.add_argument("--top", action="store_true")
    q = sub.add_parser("run")
    q.add_argument("recipe")
    q.add_argument("--spp", type=int, default=1024)
    q.add_argument("--res", default="960x540")
    q.add_argument("--lane", default="gpu", choices=sorted(build.LANES))
    q.add_argument("--no-wait", action="store_true")
    p = sub.add_parser("pull")
    p.add_argument("recipe")
    a = ap.parse_args()
    {"rig": make_rig, "run": run, "pull": pull}[a.cmd](a)


if __name__ == "__main__":
    main()
