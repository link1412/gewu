"""Write a tools/lightfit.py spec equivalent to `shots/19-luodian/fit.py fit` (its defaults, --key-share 0.5).

    python3 -I tests/lightfit/shot19_spec.py --raw DIR --out spec.json [--ref fit.json]

DIR/fNN/x.<group>.exr are r1's light-group passes (a copy, so a re-render does not change them under the test).
Fit: render f05 against the mean of original frames 255-266, row profiles under the arc, cols 100-860 of 960, at
960x540 with the 8-bit codes averaged before linearising (as fit.py). Held out: f02 vs 257, f09 vs 264.
The free bands' warm/neutral/cool split is searched as 2 x (n+1) joint variants. fit.py's dark bands (set by an L*
bisection, shot-specific) are taken from --ref (its weights / its gain) as fixed lights outside the fit; without
--ref they are off (= fit.py --lacquer-L 0).
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "shots/19-luodian"))
import scene  # noqa: E402  (read-only: BANDS)

WARM, COOL, NEUTRAL = (1.0, 0.32, 0.10), (0.32, 0.24, 1.0), (1.0, 1.0, 1.0)     # fit.py's ramp [A there]

ap = argparse.ArgumentParser()
ap.add_argument("--raw", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--ref")
a = ap.parse_args()
groups = sorted(n[2:-4] for n in os.listdir(os.path.join(a.raw, "f05")) if n.startswith("x.p") and n.endswith(".exr"))
B = scene.BANDS
free = [g for g in groups if B[int(g[1:])] >= 64.0]
dark = [g for g in groups if B[int(g[1:])] >= 20.0 and B[int(g[1:]) + 1] <= 36.0]
shared = [g for g in groups if g not in free and g not in dark]
ref = json.load(open(a.ref)) if a.ref else None
lights = {g: {"tie": "panel"} for g in shared}
for g in dark:
    lights[g] = {"fixed": [v / ref["fit"]["gain"] for v in ref["groups"][g]] if ref else 0, "in_fit": False}
lights.update({g: {} for g in free})
lights["key"] = {"share": {"value": 0.5, "rows": [0.62, 1.0]}}
variants = []
for o in (("warm", "cool"), ("cool", "warm")):
    for split in range(len(free) + 1):
        col = {"warm": WARM, "cool": COOL, "neutral": NEUTRAL}
        variants.append({"name": f"{o[0]} below {split}", "lights": {
            g: {"colors_display": {k: col[k] for k in ((o[0], "neutral") if i < split else ("neutral", o[1]))}}
            for i, g in enumerate(free)}})
spec = {"camera": "shots/19-luodian/camera.json", "shot": 19, "res": [960, 540], "target_average": "codes",
        "basis": os.path.join(os.path.abspath(a.raw), "{frame}", "x.{light}.exr"),
        "frames": [{"name": "f05", "target": "255-266"},
                   {"name": "f02", "target": [257], "held_out": True},
                   {"name": "f09", "target": [264], "held_out": True}],
        "target": {"kind": "rows", "mask": [{"rows": [0.05, 1.0]}, {"cols": [100 / 960, 860 / 960]}, {"below_arc_max": 6}]},
        "lights": {g: lights[g] for g in groups + ["key"]},
        "smooth": [{"chain": shared, "weight": 0.3}, {"chain": free, "weight": 0.3 * 5.0}],
        "variants": variants,
        "gain": {"mean8": "spec", "mask": [{"below_arc": 16}]}}
json.dump(spec, open(a.out, "w"), indent=1)
print(f"{len(groups)} bands: shared {len(shared)}, dark {len(dark)}, free {len(free)}; {len(variants)} variants -> {a.out}")
