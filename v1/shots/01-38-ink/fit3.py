"""Round 2b (fix pass): the light refit jointly on frame 0 AND the sky of shot 38 (frames 420, 470).

    python3 shots/01-38-ink/fit3.py MAPS.npz [--res 320] [--nfev 80] [--start optics.json]
    -> out/shots/01-38-ink/r2/fit3TAG.json, fit3TAG_optics.json (and shots/01-38-ink/optics.json with --write)

What changed against fit2 (r2) [the model, optics.py]:
  - lamps may be directional: radiance ~ cos^n of the emission angle ('cos_power' n; n = 0 is r1/r2's Lambertian disc).
    A Lambertian disc's tail falls as a^-4: r2's warm sun lamp (1815 K, 1 mm deep) still lit the paper 50-70 mm
    away (frame 420 rows 90-140: R 20-38 against the original's 17-20), and the sky lamp's tail made the gradient in the
    upper sky. n is fitted per lamp.
  - the lens veil has two parts (optics.veil): a narrow halo and a uniform veil (a fraction of the frame mean), replacing
    r1's single 15 % / 0.2 W Gaussian that put the band's orange into the ink core and up shot 38's sky.
  - the thick ink film mirrors the dim surroundings (optics.render 'sheen', Fresnel at the view angle; glossy where
    carbon > film_gsm [A], first tried on the sim's pool mask, which drew a second arc in the core): a neutral light
    on the opaque ink core that is not a lens veil. Fit A (without it) made the veil carry the core again (halo 9 %,
    uniform 4.7 %), which put 8 codes of warm grey on held-out frame 485's sky (original: no veil there at all).
Free [F]: sun (scale, y, depth, T, n), sky lamp (scale, y, depth, radius, beta, gamma, n), ambient back-light (scale,
beta), veil (halo, halo sigma, uniform), sheen (scale). Held at r1: camera, aperture, carbon AAE, paper, the front fill (fitted to ~0 in r1).
Residuals: frame 0's three column-band profiles (rows down to 0.3 H below the horizon, r1's rows; weight 2), the three
band profiles of 420 and 470 (all rows, title rows masked) and the top-60-row sky RGB of 420 and 470.
Held out, never in a residual: 456, 485 and every other frame.
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
import fit2 as F2  # noqa: E402
import measure as M  # noqa: E402
import optics as op  # noqa: E402
import render as RD  # noqa: E402

R2 = F2.R2
FIT, HELD = [0, 420, 470], [456, 485]
W0, W_SKY = 2.0, 3.0

# (path, transform, lo, hi) in the transformed space
PARAMS = [
    (("lamps", 0, "scale"), "log", -20, 30), (("lamps", 0, "y_mm"), None, -70, 0), (("lamps", 0, "depth_mm"), "log", np.log(0.3), np.log(200)),
    (("lamps", 0, "spectrum", "T"), "log", np.log(1200), np.log(6500)), (("lamps", 0, "cos_power"), None, 0.0, 60.0),
    (("lamps", 1, "scale"), "log", -20, 30), (("lamps", 1, "y_mm"), None, -120, 60), (("lamps", 1, "depth_mm"), "log", np.log(0.5), np.log(400)),
    (("lamps", 1, "radius_mm"), "log", np.log(2), np.log(300)), (("lamps", 1, "spectrum", "beta"), None, -2, 14),
    (("lamps", 1, "spectrum", "gamma"), None, -4, 12), (("lamps", 1, "cos_power"), None, 0.0, 60.0),
    (("lamps", 2, "scale"), "log", np.log(1e-5), np.log(1.0)), (("lamps", 2, "spectrum", "beta"), None, -4, 12),
    (("veil", "halo"), None, 0.0, 0.4), (("veil", "halo_sigma_frac"), "log", np.log(0.003), np.log(0.3)),
    (("veil", "uniform"), None, 0.0, 0.4),
    (("sheen", "scale"), "log", np.log(1e-5), np.log(10.0)),
]
SHEEN = {"scale": 0.04, "n": 1.333, "spectrum": {"kind": "blackbody", "T": 6500.0},
         "_": "[F] scale: radiance of the dim surroundings in front of the sheet, seen mirrored in the pool's surface "
              "(optics.render). n 1.333 [A]: the pool stopped feeding 400 tau before the shot; its surface taken as "
              "still wet. Neutral (6500 K) [A]. Only the pool (sim mask) is glossy [A]; the paper is matte."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("maps")
    ap.add_argument("--res", type=int, default=320)
    ap.add_argument("--nfev", type=int, default=80)
    ap.add_argument("--start", default=F.OPT)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--tag", default="", help="suffix for the outputs (parallel starts)")
    ap.add_argument("--write", action="store_true", help="also write shots/01-38-ink/optics.json")
    a = ap.parse_args()
    P = json.load(open(os.path.join(HERE, "params.json")))
    O = json.load(open(a.start))
    O.setdefault("veil", {"halo": O.get("glare", 0.149), "halo_sigma_frac": O.get("glare_sigma_frac", 0.2), "uniform": 0.0,
                          "_": "[F] round 2b: two-part lens veil (optics.veil); replaces r1's single wide Gaussian"})
    for k in ("glare", "glare_sigma_frac", "_glare_sigma"):
        O.pop(k, None)
    O.setdefault("sheen", json.loads(json.dumps(SHEEN)))
    for i in (0, 1):
        O["lamps"][i].setdefault("cos_power", 0.0)   # start = r2 exactly (Lambertian, r1 veil)
    sheet = op.Sheet(a.maps, P)
    W, H = a.res, a.res * 9 // 16
    tg = F2.targets(a.res)
    track = {int(k): v for k, v in json.load(open(os.path.join(M.ROOT, "out/shots/01-38-ink/measure/track.json"))).items()}
    pose = RD.smooth_track(track, sorted(track))
    masks = {0: F2.frame0_rows(H) & tg[0][1]}
    for f in FIT[1:] + HELD:
        masks[f] = tg[f][1]
    sky_t = {f: np.array(json.load(open(os.path.join(R2, "targets.json")))["per_frame"][str(f)]["sky_rgb"]) for f in FIT + HELD}

    def report(tag):
        ev = F2.evaluate(sheet, O, a.res, tg, pose, FIT + HELD)
        rep = {}
        for f in FIT + HELD:
            ours, sky, top = ev[f]
            e = (ours - tg[f][0])[masks[f]]
            rep[f] = dict(role="fit" if f in FIT else "held-out", band_rms=round(float(np.sqrt(np.mean(e ** 2))), 2),
                          sky_luma_fitres=round(sky, 2), sky_rgb_fitres=[round(float(x), 1) for x in top],
                          sky_rgb_orig=[round(float(x), 1) for x in sky_t[f]])
        print(tag, json.dumps(rep), flush=True)
        return rep

    before = report("start")
    if a.dry:
        return
    lo = np.array([p[2] for p in PARAMS], float)
    hi = np.array([p[3] for p in PARAMS], float)
    x0 = np.array([np.log(F.getp(O, p)) if t == "log" else F.getp(O, p) for p, t, _, _ in PARAMS], float)
    x0 = np.clip(x0, lo + 1e-6, hi - 1e-6)

    def apply(x):
        for (p, t, _, _), v in zip(PARAMS, x):
            F.setp(O, p, float(np.exp(v)) if t == "log" else float(v))

    def resid(x):
        apply(x)
        ev = F2.evaluate(sheet, O, a.res, tg, pose, FIT)
        r = []
        for f in FIT:
            e = ((ev[f][0] - tg[f][0])[masks[f]] / 255.0).ravel()
            w = np.sqrt(W0) if f == 0 else 1.0
            r.append(w * e / np.sqrt(e.size))
            if f != 0:
                r.append(w * (ev[f][2] - sky_t[f]) / 255.0 / np.sqrt(3) * np.sqrt(W_SKY / 3))
        return np.concatenate(r) * 255

    r0 = resid(x0)
    print(f"start cost {np.sum(r0 ** 2):.3f}", flush=True)
    sol = optimize.least_squares(resid, x0, bounds=(lo, hi), x_scale="jac", diff_step=1e-3, max_nfev=a.nfev, verbose=2)
    apply(sol.x)
    print(f"end cost {np.sum(sol.fun ** 2):.3f} nfev {sol.nfev}", flush=True)
    after = report("end")
    if a.write:
        with open(F.OPT, "w") as fh:
            json.dump(O, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(R2, f"fit3{a.tag}_optics.json"), "w") as fh:
        json.dump(O, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(R2, f"fit3{a.tag}.json"), "w") as fh:
        json.dump(dict(res=a.res, fit_frames=FIT, held_out=HELD, before=before, after=after,
                       params={".".join(map(str, p)): F.getp(O, p) for p, _, _, _ in PARAMS}), fh, indent=1)


if __name__ == "__main__":
    main()
