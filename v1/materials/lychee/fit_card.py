"""Starting values for the card's fitted parameters ([F] in material.json), from a Kubelka-Munk layer model of the
three pieces and the colour ratios measured on the photograph (measure_ref.py). The card's render then decides.

    python3 -I materials/lychee/fit_card.py [--write] [--correct OUT/card_measure.json]

--factors FILE: the factors a --correct saved, applied after a change the layer model can follow.
--correct: one step of using the render as the forward model: the skin's and the aril's targets are multiplied, per
channel, by what the layer model predicts for the current material.json over what the render measured
(measure_card.py), so the next fit lands where the render would meet the photo. The seed is left out: on the card its
lower body mirrors the white floor and sweep (a smooth dielectric), which no absorption in the testa can take away.

- skin: the red layer over the white layer over the aril (thicknesses from objects/lychee/leidus.json);
- aril: its flesh over the seed, as thick as at the fruit's side (half the diameter less the pericarp and half the
  seed's width);
- seed: the testa over the cotyledon.
Each through its surface (optics.saunderson), as the camera chain sees it: sensor RGB under the card's 5500 K,
white balanced, to linear BT.709 (tools/camera.py calibrate).
Fitted: the aril's yellow (its B/G), the anthocyanins and carotenoids (the skin's chromaticity), the testa's three
anchors (the seed against the aril, all three channels). Not fitted: the skin's brightness against the aril (printed:
the light falls on the two pieces at different angles, on the photo in a way not known), and the browning, held at
material.json's value (a first fit with it free and the skin's level as a target drove it to 0, S4).
"""
import argparse
import copy
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import camera as C  # noqa: E402
import rgbscene  # noqa: E402
import optics as LO  # noqa: E402

SET = "leidus"
SENSOR, K = "canon_eos_5d_mkiv", 5500.0


def pieces(m, cfg):
    md = LO.media(m, SET)
    a, ro, ri_, t = md["aril"], md["pericarp_outer"], md["pericarp_inner"], md["testa"]
    sp = lambda v: v["sigma_s"] * (1 - v["g"])
    tp = cfg["pericarp"]["thickness_mm"]["value"]
    to = cfg["pericarp"]["outer_mm"]["value"]
    d_aril = cfg["fruit"]["D_mm"]["value"] / 2 - tp - cfg["seed"]["width_mm"]["value"] / 2
    seed_in = LO.km_layer(t["sigma_a"], sp(t), LO.value(m["testa"], "thickness_mm", SET),
                          LO.value(m["cotyledon"], "reflectance", SET))
    aril_in = LO.km_layer(a["sigma_a"], sp(a), d_aril, seed_in)
    white = LO.km_layer(ri_["sigma_a"], sp(ri_), tp - to, aril_in)
    skin_in = LO.km_layer(ro["sigma_a"], sp(ro), to, white)
    return {"skin": LO.saunderson(skin_in, ro["eta"]), "aril": LO.saunderson(aril_in, a["eta"]),
            "seed": LO.saunderson(seed_in, t["eta"])}, d_aril


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--correct")
    ap.add_argument("--factors", help="apply the factors a previous --correct saved (out/lychee/card_correction.json), "
                                      "after a change the layer model can follow (a thickness, a mu_s')")
    args = ap.parse_args()
    m0 = LO.load()
    cfg = json.load(open(os.path.join(ROOT, "objects/lychee/leidus.json")))
    ref = json.load(open(os.path.join(ROOT, "out/lychee/ref_measure.json")))["colours"]
    sen = rgbscene.Sensor(SENSOR, K)
    cal = C.calibrate(sen.S, C.blackbody(K))
    lin = lambda R: cal["C"] @ sen.average(R)
    photo = {k: np.array(ref[k]["linear_srgb"]) for k in ("skin", "aril", "seed")}
    if args.correct:
        meas = json.load(open(args.correct))["colours"]
        now = {k: lin(v) for k, v in pieces(m0, cfg)[0].items()}
        s = now["aril"][1] / meas["aril"]["render"][1]            # render units -> the model's, by the aril's G
        cors = {}
        for k in ("skin", "aril"):
            cor = now[k] / (np.array(meas[k]["render"]) * s)
            print(f"  correction {k}: {np.round(cor, 3)}")
            photo[k] = photo[k] * cor
            cors[k] = cor.round(4).tolist()
        json.dump({"from": args.correct, "factors": cors}, open(os.path.join(ROOT, "out/lychee/card_correction.json"), "w"),
                  indent=1)
    elif args.factors:
        cors = json.load(open(args.factors))["factors"]
        for k, cor in cors.items():
            print(f"  correction {k} (saved): {cor}")
            photo[k] = photo[k] * np.array(cor)

    def setp(x):
        m = copy.deepcopy(m0)
        a400, cant, ccar, t450, t540, t610 = np.exp(x)
        m["aril"]["yellow_mua_400_per_mm"]["value"] = a400
        m["pericarp_outer"]["anthocyanin_ug_per_cm3"]["value"][SET] = cant
        m["pericarp_outer"]["carotenoid_ug_per_cm3"]["value"][SET] = ccar
        m["testa"]["mua_anchors_per_mm"]["value"] = {"450": t450, "540": t540, "610": t610}
        return m

    def res(x):
        P, _ = pieces(setp(x), cfg)
        c = {k: lin(v) for k, v in P.items()}
        r = [np.log((c["aril"][2] / c["aril"][1]) / (photo["aril"][2] / photo["aril"][1]))]
        r += list(np.log((c["skin"][1:] / c["skin"][0]) / (photo["skin"][1:] / photo["skin"][0])))
        r += list(np.log((c["seed"] / c["aril"]) / (photo["seed"] / photo["aril"])))
        return np.array(r)

    x0 = np.log([0.05, 300.0, 30.0, 9.0, 8.0, 4.0])
    f = least_squares(res, x0, bounds=(np.log([1e-4, 10, 0.1, 0.1, 0.1, 0.01]), np.log([20, 3000, 3000, 200, 200, 200])))
    m = setp(f.x)
    P, d_aril = pieces(m, cfg)
    c = {k: lin(v) for k, v in P.items()}
    names = ["aril yellow_mua_400 /mm", "anthocyanin ug/cm3", "carotenoid ug/cm3", "testa 450", "testa 540", "testa 610"]
    print(f"aril depth {d_aril:.2f} mm; residuals (log) {np.round(f.fun, 4)}")
    for n, v in zip(names, np.exp(f.x)):
        print(f"  {n:26s} {v:.4g}")
    for k in ("skin", "aril", "seed"):
        print(f"  {k}: model {np.round(c[k], 4)}  /aril {np.round(c[k] / c['aril'], 3)}   photo /aril "
              f"{np.round(photo[k] / photo['aril'], 3)}")
    print(f"  aril R/G model {c['aril'][0] / c['aril'][1]:.3f}, photo {photo['aril'][0] / photo['aril'][1]:.3f}")
    if args.write:
        p = os.path.join(HERE, "material.json")
        m1 = LO.load()
        v = np.exp(f.x)
        m1["aril"]["yellow_mua_400_per_mm"]["value"] = round(float(v[0]), 4)
        m1["pericarp_outer"]["anthocyanin_ug_per_cm3"]["value"][SET] = round(float(v[1]), 1)
        m1["pericarp_outer"]["carotenoid_ug_per_cm3"]["value"][SET] = round(float(v[2]), 1)
        m1["testa"]["mua_anchors_per_mm"]["value"] = {k: round(float(x), 3) for k, x in zip(("450", "540", "610"), v[3:])}
        json.dump(m1, open(p, "w"), indent=1, ensure_ascii=False)
        print(f"-> {p}")


if __name__ == "__main__":
    main()
