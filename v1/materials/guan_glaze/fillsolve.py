"""From two line-test renders that differ only in the fill's reflectance, solve per channel the line ratio's
dependence on the fill (rho = 1 + cov (K F - 1)), then the fill colour that gives the photo's ratio, then a smooth
reflectance spectrum (anchors at 450/550/650 nm, linear between, held at the ends) with that camera colour."""
import sys, json
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, 'tools'); sys.path.insert(0, 'crafts/deposition')
import camera, deposit as dp
S = camera.Spectra("canon_eos_5d_mkiv"); light = camera.blackbody(5500); cal = camera.calibrate(S, light); LAM = camera.LAM
W = (S.sens @ light) * cal['gains'] @ cal['C'].T
rgb = lambda r: (S.sens @ (r * light)) * cal['gains'] @ cal['C'].T / W
def cam_of(interleaved):
    v = np.asarray(interleaved, float); return rgb(np.interp(LAM, v[0::2], v[1::2]))
d1, d2 = sys.argv[1], sys.argv[2]
target = np.array([float(x) for x in sys.argv[3].split(',')])
R = []
for d in (d1, d2):
    b = json.load(open(d + '/build.json')); k = json.load(open(d + '/lines.json'))['known_place']
    F = cam_of(dp.fill_spectrum(b['params']['dep']))
    rho = np.array(k['colour_over_glaze_median_bright'])
    R.append((F, rho)); print(d, 'fill cam rgb', F.round(3), 'line ratio', rho, 'contrast p50', k['contrast_p10_p50_p90'][1])
(F1, r1), (F2, r2) = R
covK = (r1 - r2) / (F1 - F2)
cov = covK * F1 - (r1 - 1)
Fs = (target - 1 + cov) / covK
print('cov', cov.round(3), 'cov*K', covK.round(3), '-> fill camera rgb for the target', Fs.round(3))
anch = np.array([450, 550, 650.0])
def spec(a):
    return np.interp(LAM, np.r_[400, anch, 700], np.r_[a[0], a, a[2]])
sol = least_squares(lambda a: rgb(spec(a)) - Fs, x0=Fs, bounds=(0.01, 0.95))
a = sol.x
print('anchors 450/550/650 nm', a.round(4), '-> camera rgb', rgb(spec(a)).round(3))
lam = np.arange(360, 831, 10.0)
print(json.dumps([float(x) for pair in zip(lam, np.round(np.interp(lam, np.r_[400, anch, 700], np.r_[a[0], a, a[2]]), 4)) for x in pair]))
