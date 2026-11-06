"""Shot 17: refine tools/lightfit.py's weights on the numbers shotcheck judges (python3 -I shots/17-peacock/codefit.py).

Why (as shot 21's codefit, docs/skill-notes.md 151): lightfit matches linear region means; shotcheck compares mean
8-bit codes, and this frame is mottled (fine structure, dark gaps) so the two differ by up to ~13 codes in the middle
band. Here: the bases at the render's 1280x720, each pixel taken through camera.json's chain (lightfit.chain's
matrix, camera.tone, sRGB) to codes; per shotcheck region (rows top60, 60-360, middle, bottom, the bottom's halves)
the mean code per channel against the original's (mean of frames 236-243, decoded as shotcheck decodes it).
Unknowns: one intensity per light group (>= 0) and the one shared gel (R, B; G = 1), as lightfit's tie; the fill's
quadrants kept alike, and the other lamps held to at most FILL_MAX of the key's light (r3). Writes lights.json in lightfit's format. Weights are [F].
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import lightfit as lf  # noqa: E402
import shotcheck  # noqa: E402

spec = json.load(open(os.path.join(HERE, "lightfit.json")))
LJ = os.path.join(HERE, "lights.json")
start = json.load(open(LJ))
M, cam = lf.chain(lf.P(spec["camera"]), spec.get("raw_ref"))
lights = list(spec["lights"])
fr = spec["frames"][0]
B0 = [lf.read_image(lf.P(spec["basis"].format(frame=fr["name"], light=l))).astype(np.float32) for l in lights]
H, W = B0[0].shape[:2]
ROWS = {"top60": (0, 60), "upper": (60, 360), "middle": (360, 720), "bottom": (720, 1080)}
regs = []
# r2: shotcheck's region means (after denoise, upscale, the camera's noise, its glyph mask) differ from this fit's
# prediction by a few codes; offsets.py accumulates shotcheck's error per region and the targets move by it [F]
OFFP = os.path.join(ROOT, "out/shots/17-peacock/codefit_offsets.json")
OFFS = json.load(open(OFFP)) if os.path.exists(OFFP) else {}
o = np.mean([shotcheck.orig_frames([f])(f).astype(np.float64) for f in range(236, 244)], 0)
for k, (a, b) in ROWS.items():
    for cols in ([(0, 1)] + ([(0, 0.5), (0.5, 1)] if k == "bottom" else [])):
        ys, ye = int(a / 1080 * H), int(b / 1080 * H)
        xs, xe = int(cols[0] * W), int(cols[1] * W)
        tgt = o[a:b, int(cols[0] * 1920):int(cols[1] * 1920)].reshape(-1, 3).mean(0)
        regs.append((k + str(cols), (slice(ys, ye), slice(xs, xe)), tgt - np.asarray(OFFS.get(k, [0, 0, 0]))))
# per region, the bases' pixels (subsampled 2x2 for speed: the codes are per pixel, the mean is over many)
Bs = [np.stack([b[sl][::2, ::2].reshape(-1, 3) for b in B0]) for _, sl, _ in regs]      # L, P, 3
w0 = np.array([np.mean(start["weights"][l]) for l in lights]) + 1e-4
w0 = np.maximum(w0, 0.2 * w0.max())          # no lamp starts off (lightfit may zero the key)
g0 = np.array(start["weights"][lights[int(np.argmax(w0))]], float)
g0 = g0 / g0[1]


def codes(raw):
    return 255 * camera.srgb_encode(np.clip(camera.tone(np.maximum(raw @ M.T, 0), cam["develop"]), 0, 1))


def unpack(z):
    return np.exp(z[:len(lights)]), np.array([np.exp(z[-2]), 1.0, np.exp(z[-1])])


FILL = [l for l in lights if l.startswith("b")]
mean_l = np.array([b.mean() for b in B0])                              # each lamp's mean raw signal over the frame
FILL_MAX = 0.6         # r3: all the other lamps together give at most this fraction of the key's light (so its sheen band shows; a lighting choice) [A]


def resid(z):
    w, g = unpack(z)
    r = []
    for (_, _, t), Bk in zip(regs, Bs):
        raw = np.einsum("l,lpc->pc", w, Bk) * g
        r.extend(codes(raw).mean(0) - t)
    lw = np.log(w)
    q = [lights.index(l) for l in FILL]
    r.extend(0.3 * (lw[q] - lw[q].mean()))                              # the fill's quadrants alike
    if "key" in lights:                                                 # the key leads: the others <= FILL_MAX of it
        k = lights.index("key")
        o = [i for i in range(len(lights)) if i != k]
        ratio = (w[o] * mean_l[o]).sum() / (w[k] * mean_l[k])
        r.append(20.0 * max(0.0, math.log(ratio / FILL_MAX)))
    return np.array(r)


z0 = np.r_[np.log(w0), np.log(g0[0]), np.log(g0[2])]
sol = least_squares(resid, z0, method="trf")
w, g = unpack(sol.x)
for (name, _, t), Bk in zip(regs, Bs):
    print(f"{name:22s} orig {np.round(t, 1)} ours {np.round(codes(np.einsum('l,lpc->pc', w, Bk) * g).mean(0), 1)}")
print("gel", g.round(4))
out = dict(start)
out["weights"] = {l: (wi * g).round(6).tolist() for l, wi in zip(lights, w)}
out["about"] = "shots/17-peacock/codefit.py: lightfit's weights refined on shotcheck's region mean codes [F]"
json.dump(out, open(LJ, "w"), indent=1)
print("->", LJ)
