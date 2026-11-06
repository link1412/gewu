"""Heirloom fill colour from two card renders that differ only in the fill's spectrum (args: render dir A, its
known_rgb JSON, dir B, its JSON, target line colour R,G,B (mean cross profile minimum over the glaze)).
Per channel the line follows the fill's camera colour F linearly, rho = a + b F (the fill is a diffuse surface
seen through the glaze); solve a, b from the two renders, then F for the target, then a smooth spectrum
through anchors at 450/550/650 nm with that camera colour."""
import sys, os, json, re
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, "./tools")
import camera
S = camera.Spectra("canon_eos_5d_mkiv"); light = camera.blackbody(5500); cal = camera.calibrate(S, light); LAM = camera.LAM
W = (S.sens @ light) * cal['gains'] @ cal['C'].T
rgb = lambda r: (S.sens @ (r * light)) * cal['gains'] @ cal['C'].T / W

def fill_spec(d):
    t = open(os.path.join(d, "scene.pbrt")).read()
    i = t.index('"deposit.ply"')
    m = re.findall(r'Material "diffuse" "spectrum reflectance" \[([^\]]*)\]', t[:i])[-1]
    v = np.array([float(x) for x in m.split()])
    return np.interp(LAM, v[0::2], v[1::2])

dA, jA, dB, jB = sys.argv[1:5]
tgt = np.array([float(x) for x in sys.argv[5].split(",")])
FA, FB = rgb(fill_spec(dA)), rgb(fill_spec(dB))
rA = np.array(json.load(open(jA))["mean_profile_min_rgb"]); rB = np.array(json.load(open(jB))["mean_profile_min_rgb"])
b = (rA - rB) / (FA - FB); a = rA - b * FA
F = (tgt - a) / b
anch = np.array([450, 550, 650.0])
spec = lambda x: np.interp(LAM, np.r_[400, anch, 700], np.r_[x[0], x, x[2]])
x = least_squares(lambda x: rgb(spec(x)) - F, x0=np.clip(F, 0.02, 0.9), bounds=(0.005, 0.95)).x
print(json.dumps({"F_A": FA.round(4).tolist(), "F_B": FB.round(4).tolist(), "line_A": rA.tolist(), "line_B": rB.tolist(),
                  "a": a.round(4).tolist(), "b": b.round(4).tolist(), "target": tgt.tolist(), "F_needed": F.round(4).tolist(),
                  "anchors_450_550_650": x.round(4).tolist(), "anchor_rgb": rgb(spec(x)).round(4).tolist()}))
