"""Line colour on the Palace Museum vase photo (arg 1) along three hand-picked windows, each holding one near-vertical
line: the line's column per row is the minimum of the smoothed blue channel, a quadratic fitted (robust), then
cross profiles as lines.block_profiles does. px/mm arg 2 (R_b = 70.5 mm chosen [A]); out JSON arg 3."""
import sys, os, json
import numpy as np
from scipy import ndimage as ndi
ROOT = "."
sys.path.insert(0, os.path.join(ROOT, "crafts/crackle")); sys.path.insert(0, os.path.join(ROOT, "materials/guan_glaze"))
import network as nw, lines as ln
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
px = float(sys.argv[2])
W0 = [(4140, 4480, 2470, 2560), (4160, 4380, 2030, 2130), (4200, 4440, 1820, 1900)]
y0, y1 = 4100, 4520; x0, x1 = 1780, 2600
lin = nw.srgb_to_lin(im[y0:y1, x0:x1]).astype(float)
B = ndi.gaussian_filter(lin[..., 2], 1.5)
paths, fits = [], []
for (r0, r1, c0, c1) in W0:
    rows = np.arange(r0, r1) - y0
    cols = np.array([c0 - x0 + np.argmin(B[r, c0 - x0:c1 - x0]) for r in rows], float)
    ok = np.ones(len(rows), bool)
    for _ in range(4):
        p = np.polyfit(rows[ok], cols[ok], 2)
        res = cols - np.polyval(p, rows)
        ok = np.abs(res) < max(2.5, 2.5 * np.std(res[ok]))
    paths.append(np.c_[rows, np.polyval(p, rows)])
    fits.append({"window": [r0, r1, c0, c1], "inliers": round(float(ok.mean()), 2), "rms_px": round(float(np.std(res[ok])), 2)})
r, prof, ori = ln.block_profiles(lin, None, px, paths=paths)
Yp = prof @ ln.LUMA
bgm = np.abs(r) >= 0.3
bg = np.median(prof[:, bgm], 1)
cen = np.abs(r) <= 0.15
ic = np.nonzero(cen)[0][np.argmin(Yp[:, cen], 1)]
k = np.arange(len(prof))
ratio = prof[k, ic] / bg
cY = Yp[k, ic] / np.median(Yp[:, bgm], 1) - 1
fw = []
for i in k:
    a = 1 - Yp[i] / np.median(Yp[i, bgm]); j = ic[i]; hm = a[j] / 2
    l = j
    while l > 0 and a[l] > hm: l -= 1
    q = j
    while q < len(a) - 1 and a[q] > hm: q += 1
    fw.append(r[q] - r[l])
pc = lambda a, q=(10, 50, 90): [round(float(np.percentile(a, x)), 3) for x in q]
mp = np.mean(prof / bg[:, None, :], 0)                 # mean profile per channel, over the shoulders
res = {"blocks": int(len(prof)), "windows": fits, "contrast_p10_p50_p90": pc(cY),
       "colour_over_glaze_p50": [round(float(np.median(ratio[:, c])), 3) for c in range(3)],
       "mean_profile_min_rgb": [round(float(mp[:, c].min()), 3) for c in range(3)],
       "fwhm_um_p10_p50_p90": [round(1000 * v) for v in pc(np.array(fw))],
       "glaze_median_lin": [round(float(x), 4) for x in np.median(bg, 0)], "px_per_mm": px,
       "source": sys.argv[1] + " rows 4100-4520, cols 1780-2600 (the belly below the ridges)"}
print(json.dumps(res))
json.dump(res, open(sys.argv[3], "w"), indent=1)
ov = im[y0:y1, x0:x1].copy()
for p in paths:
    for rr, cc in p[::3].astype(int):
        ov[rr, min(cc + 6, ov.shape[1] - 1)] = [255, 0, 0]
Image.fromarray(ov).save(sys.argv[3].replace(".json", ".png"))
