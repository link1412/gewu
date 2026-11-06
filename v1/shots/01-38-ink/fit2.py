"""Round 2: the light against frame 0 AND the sky far above the bleed (frames 420, 470 of shot 38).

    python3 -I shots/01-38-ink/fit2.py MAPS.npz --floor   # what r2 uses (see below)
    python3 -I shots/01-38-ink/fit2.py MAPS.npz           # the joint fit (tries 1-5; none kept, see the notes at _FIXED)
    python3 -I shots/01-38-ink/fit2.py MAPS.npz --dry     # evaluate optics.json
    -> shots/01-38-ink/optics.json in place, out/shots/01-38-ink/r2/fit2.json

Targets (measure_sky.py, bt709 tv decode): the three column-band profiles (200-360, 880-1040, 1560-1720 at 1920) of
  - frame 0, rows from the top down to 0.3 H below the horizon (r1's rows),
  - frames 420 and 470, every row, title rows masked;
plus the top-60-row sky RGB of each. Each frame is rendered with its measured, smoothed pose (render.pose_camera; the
geometry is input, not tested). Held out, never in any residual: frames 456 and 485 (and every other frame).

What r2 keeps (--floor): r1's light unchanged, plus one new light, an 'ambient' back-light (uniform, larger than the
field) whose strength and spectral slope are fitted only to the top-60 sky RGB of 420 and 470. The joint refits (tries
1-5) all traded that sky against r1's wide lens veil, which the original's frame 420 does not show but which is what
lights the ink core in frame 0 (round 1 open item 4); they lowered the sky to 14-15.6 and still regressed frame 0.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy import optimize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fit as F  # noqa: E402
import measure as M  # noqa: E402
import optics as op  # noqa: E402
import render as RD  # noqa: E402

R2 = os.path.join(M.ROOT, "out/shots/01-38-ink/r2")
FIT = [0, 420, 470]
HELD = [456, 485]
BANDS = F.BANDS

AMBIENT = {"name": "ambient", "kind": "ambient", "scale": 0.007,
           "spectrum": {"kind": "sky", "beta": 3.0, "gamma": 0.0},
           "_": "[F] round 2: diffuse cool back-light larger than the field (the dark navy floor far above the bleed, "
                "shot 38 frames 399-490: (15,19,23) bt709 tv); transmitted by the same KM sheet as the lamps"}

# Light only. Try 1 (fit2_try1.*) also freed r1's fine-carbon AAE and the aperture: the aperture ran to 7.9 mm (from 1.86)
# to blur the far field, frame 0 regressed (14.2 codes) and the sky floor stopped at 14.3. Both are held at r1 now.
_ALL = F.PARAMS + [(("lamps", 2, "scale"), "log"), (("lamps", 2, "spectrum", "beta"), None), (("glare_sigma_frac",), "log")]
_LO = [-20, -70, np.log(0.5), np.log(1200), -20, -120, np.log(1), -2, -30, 0, 0.5, np.log(0.2), np.log(5), -2, -20, -4,
       np.log(0.01)]
_HI = [20, 0, np.log(200), np.log(6500), 20, 40, np.log(400), 8, 5, 0.3, 6.0, np.log(40), np.log(200), 4, 5, 12,
       np.log(0.3)]
# Try 2 (fit2_try2.*, light only) lowered the glare 0.149 -> 0.104 to darken frame 0's top: the glare is also what lights
# the ink core there, so the ground went dark and frame 0 regressed to 14.7 codes. The glare (an image-space veil) is
# held at r1 too: it is neither the fix nor free to trade against it.
# Try 3 (glare held at r1's 0.149 / sigma 0.2 W): sky 14.1, frame 0 13.9. Decomposing frame 420 showed why: r1's veil
# spreads the bright bottom of the frame up the whole sky (+3-11 codes at rows 60-150 of 180), the original rises only
# 18.4 -> 21.9 there, so the fit kept the ambient low. Try 4 frees the veil's fraction AND width, constrained by all
# three frames (a lens property: one veil for every frame). The sky floor itself comes only from the ambient lamp.
# Try 4 (fit2_try4.*): veil 0.126 / sigma 0.133 W, sky 15.6 (10.8,16.1,23.8), frame 0 14.1. A grid at r1's lamps + the
# ambient showed frame 0's rms is held up by the wide veil (it is what lifts the ink core to ~20: 13.8 at r1's veil,
# 16.9-18.3 at sigma 0.06 W), so the veil cannot be narrowed without regressing frame 0; the core's light is round 1's
# open item 4, out of scope. Try 5 (final): veil and the sun (hidden behind the core; it sets the band, out of scope)
# held at r1; free: the sky lamp, the ambient back-light, the front fill; the top-60 sky weighs one frame.
_FIXED = {("carbon", "aae", "fine"), ("camera", "aperture_mm"), ("glare",), ("glare_sigma_frac",),
          ("lamps", 0, "scale"), ("lamps", 0, "y_mm"), ("lamps", 0, "depth_mm"), ("lamps", 0, "spectrum", "T")}
W_SKY = 3.0   # x the 1/3-frame weight of try 1-4: the top-60 sky RGB of a fit frame now weighs one frame's profile
W0 = 2.0     # frame 0 weighs twice a shot-38 frame: it must not regress (acceptance), and it is two shots' worth of screen
PARAMS = [p for p in _ALL if p[0] not in _FIXED]
LO = [v for p, v in zip(_ALL, _LO) if p[0] not in _FIXED]
HI = [v for p, v in zip(_ALL, _HI) if p[0] not in _FIXED]


def targets(res):
    """Original band profiles at the fit resolution: {frame: (3 bands x H x 3 codes, 3 x H valid)}."""
    d = np.load(os.path.join(R2, "orig_profiles.npz"))
    frames = list(d["frames"])
    H = res * 9 // 16
    k = M.FH // H
    out = {}
    for f in frames:
        i = frames.index(f)
        p = d["prof"][i][:, :H * k].reshape(3, H, k, 3).mean(axis=2)
        v = d["valid"][i][:, :H * k].reshape(3, H, k).all(axis=2)
        out[int(f)] = (p.astype(float), v)
    return out


def frame0_rows(H):
    orig = json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/orig.json")))["0"]
    keep = []
    for a0, a1 in BANDS:
        xm = (a0 + a1) / 2
        r = orig["r_over_w"] * M.FW
        hrow = (orig["apex_y"] * M.FH + r - np.sqrt(r * r - (xm - orig["apex_x"] * M.FW) ** 2)) / M.FH * H
        keep.append(np.arange(H) < hrow + 0.3 * H)
    return np.stack(keep)


def band_codes(codes, W):
    return np.stack([codes[:, int(a0 / 1920 * W):int(a1 / 1920 * W)].mean(axis=1) for a0, a1 in BANDS])


def evaluate(sheet, O, res, tg, pose, frames):
    """Per frame: our band profiles (3 x H x 3 codes) and our top-60-row sky luma (r1's definition, at 1080 rows)."""
    W, H = res, res * 9 // 16
    out = {}
    for f in frames:
        C = RD.pose_camera(O["camera"], *pose[f])
        codes = F.to_codes(op.render(sheet, O, C, W, H))
        top = codes[:max(1, round(60 / M.FH * H))].reshape(-1, 3).mean(axis=0)
        out[f] = (band_codes(codes, W), float(M.luma(top[None])[0]), top)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("maps")
    ap.add_argument("--res", type=int, default=320)
    ap.add_argument("--dry", action="store_true", help="evaluate the current optics.json, do not fit")
    ap.add_argument("--floor", action="store_true",
                    help="final r2: start from r1's light, fit ONLY the ambient back-light (strength, slope) to the top-60 sky "
                         "RGB of frames 420 and 470; everything else stays at r1")
    a = ap.parse_args()
    P = json.load(open(os.path.join(HERE, "params.json")))
    O = json.load(open(F.OPT))
    sheet = op.Sheet(a.maps, P)
    W, H = a.res, a.res * 9 // 16
    tg = targets(a.res)
    track = {int(k): v for k, v in json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/track.json"))).items()}
    pose = RD.smooth_track(track, sorted(track))
    keep0 = frame0_rows(H)
    masks = {0: keep0 & tg[0][1]}
    for f in FIT[1:] + HELD:
        masks[f] = tg[f][1]

    def report(tag):
        ev = evaluate(sheet, O, a.res, tg, pose, FIT + HELD)
        rep = {}
        for f in FIT + HELD:
            ours, sky, top = ev[f]
            m = masks[f]
            e = (ours - tg[f][0])[m]
            rep[f] = dict(band_rms=round(float(np.sqrt(np.mean(e ** 2))), 2), sky_luma_fitres=round(sky, 2),
                          sky_rgb_fitres=[round(float(x), 1) for x in top], role="fit" if f in FIT else "held-out")
        print(tag, json.dumps(rep), flush=True)
        return rep

    if a.floor:
        O = json.load(open(os.path.join(R2, "optics_r1.json")))
    if not any(L.get("kind") == "ambient" for L in O["lamps"]):
        O["lamps"].append(json.loads(json.dumps(AMBIENT)))
        if a.dry:
            O["lamps"][2]["scale"] = 1e-12        # r1 as it was (no ambient)
    assert O["lamps"][2].get("kind") == "ambient"
    before = report("start")
    if a.dry:
        return

    O.setdefault("glare_sigma_frac", 0.2)
    if a.floor:
        sky_t = {f: np.array(json.load(open(os.path.join(R2, "targets.json")))["per_frame"][str(f)]["sky_rgb"]) for f in FIT[1:]}
        L2 = O["lamps"][2]

        def r_floor(x):
            L2["scale"], L2["spectrum"]["beta"] = float(np.exp(x[0])), float(x[1])
            ev = evaluate(sheet, O, a.res, tg, pose, FIT[1:])
            return np.concatenate([ev[f][2] - sky_t[f] for f in FIT[1:]])
        sol = optimize.least_squares(r_floor, [np.log(0.0075), 1.6], diff_step=1e-3, x_scale="jac")
        r_floor(sol.x)
        print("floor fit:", L2["scale"], L2["spectrum"]["beta"], "resid codes", np.round(sol.fun, 2), flush=True)
        after = report("end")
        with open(F.OPT, "w") as fh:
            json.dump(O, fh, indent=2, ensure_ascii=False)
        with open(os.path.join(R2, "fit2.json"), "w") as fh:
            json.dump(dict(res=a.res, mode="floor", fit_frames=FIT[1:], fit_quantity="top-60 sky RGB",
                           held_out=HELD, before=before, after=after,
                           params={"lamps.2.scale": L2["scale"], "lamps.2.spectrum.beta": L2["spectrum"]["beta"]}), fh, indent=1)
        return
    x0 = []
    for path, tr in PARAMS:
        v = F.getp(O, path)
        x0.append(np.log(v) if tr == "log" else v)
    lo, hi = np.array(LO), np.array(HI)
    x0 = np.clip(np.array(x0, float), lo + 1e-6, hi - 1e-6)

    def apply(x):
        for (path, tr), v in zip(PARAMS, x):
            F.setp(O, path, float(np.exp(v)) if tr == "log" else float(v))

    sky_t = {f: np.array(json.load(open(os.path.join(R2, "targets.json")))["per_frame"][str(f)]["sky_rgb"]) for f in FIT}

    def resid(x):
        """Each fit frame weighs the same (1/sqrt(n)); plus the top-60 sky RGB of each fit frame (the acceptance
        quantity, so it is a fit target: weight 1 per channel, as if 1/3 of a frame's profile)."""
        apply(x)
        ev = evaluate(sheet, O, a.res, tg, pose, FIT)
        r = []
        for f in FIT:
            e = ((ev[f][0] - tg[f][0])[masks[f]] / 255.0).ravel()
            w = np.sqrt(W0) if f == 0 else 1.0
            r.append(w * e / np.sqrt(e.size))
            r.append(w * (ev[f][2] - sky_t[f]) / 255.0 / np.sqrt(3) * np.sqrt(W_SKY / 3))
        return np.concatenate(r) * np.sqrt(4302)       # back to roughly per-sample scale for the printout

    r0 = resid(x0)
    print(f"joint: start rms {np.sqrt(np.mean(r0 ** 2)) * 255:.2f} codes ({r0.size} residuals)", flush=True)
    sol = optimize.least_squares(resid, x0, bounds=(lo, hi), x_scale="jac", diff_step=1e-3, max_nfev=60, verbose=1)
    apply(sol.x)
    print(f"joint: end rms {np.sqrt(np.mean(sol.fun ** 2)) * 255:.2f} codes ({sol.nfev} evaluations)", flush=True)
    after = report("end")
    with open(F.OPT, "w") as fh:
        json.dump(O, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(R2, "fit2.json"), "w") as fh:
        json.dump(dict(res=a.res, fit_frames=FIT, held_out=HELD, before=before, after=after,
                       params={".".join(map(str, p)): F.getp(O, p) for p, _ in PARAMS}), fh, indent=1)


if __name__ == "__main__":
    main()
