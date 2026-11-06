"""Synthetic check of tools/lightfit.py: bases with known weights + noise, one light with 3 beam-width variants.

    python3 -I tests/lightfit/synth.py DIR      # writes bases, targets, spec into DIR, fits, checks recovery
"""
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.abspath(sys.argv[1])
os.makedirs(D, exist_ok=True)
rng = np.random.default_rng(7)
W, H, NF = 960, 540, 6
yy, xx = np.mgrid[0:H, 0:W] / H
true = {"a": [0.8, 0.6, 0.4], "b": [0.2, 0.3, 0.5], "c": [1.5, 1.5, 1.5], "beam": [0.7, 0.5, 0.3]}
widths = {"n10": 0.10, "n20": 0.20, "n40": 0.40}
TRUE_BEAM = "n20"


def blob(cx, cy, s, col):
    return np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * s * s))[..., None] * np.array(col) * 0.1


frames = []
for f in range(NF):
    t = f / NF
    B = {"a": blob(0.3 + 0.1 * t, 0.5, 0.25, [1, 0.9, 0.7]), "b": blob(1.4, 0.3, 0.35, [0.6, 0.8, 1.0]),
         "c": blob(0.9, 0.9 - 0.2 * t, 0.15, [1, 1, 1]) + 0.002}
    for k, s in widths.items():
        B[f"beam.{k}"] = blob(1.2 - 0.3 * t, 0.6, s, [1, 0.95, 0.9])
    for k, b in B.items():
        np.save(os.path.join(D, f"f{f}.{k}.npy"), b)
    img = sum(B[k] * np.array(w) for k, w in true.items() if k != "beam") + B[f"beam.{TRUE_BEAM}"] * np.array(true["beam"])
    img = img * (1 + 0.01 * rng.standard_normal(img.shape))                 # 1 % noise
    np.save(os.path.join(D, f"f{f}.target.npy"), img)
    frames.append({"name": f"f{f}", "target_raw": os.path.join(D, f"f{f}.target.npy"), "held_out": f == NF - 1})
spec = {"camera": "shots/06-guan/camera.json", "raw_ref": 0.1, "res": [480, 270], "basis": os.path.join(D, "{frame}.{light}.npy"),
        "frames": frames, "target": {"kind": "image", "mask": [{"caption": True}]},
        "lights": {"a": {}, "b": {}, "c": {"weights": "scalar"},
                   "beam": {"variants": {k: {"basis": os.path.join(D, "{frame}.beam." + k + ".npy")} for k in widths}}}}
json.dump(spec, open(os.path.join(D, "spec.json"), "w"), indent=1)
subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/lightfit.py"), "fit", os.path.join(D, "spec.json"),
                "--out", os.path.join(D, "fit.json")], check=True)
r = json.load(open(os.path.join(D, "fit.json")))
err = max(np.abs(np.array(r["weights"][k]) / np.array(w) - 1).max() for k, w in true.items())
print(f"picked {r['variant']} (true beam={TRUE_BEAM}); max relative weight error {err:.2e}")
ok = r["variant"] == f"beam={TRUE_BEAM}" and err < 0.01
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
