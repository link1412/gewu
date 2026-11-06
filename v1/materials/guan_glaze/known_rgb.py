"""Per-channel line colour of a card render at the cracks' known places (as lines_cmd reads the render): the mean
cross profile over the shoulders (|r| >= 0.3 mm), its minimum (dark lines) and maximum (bright) per channel, and the
luma contrast p10/p50/p90 per block. Args: out JSON, render dirs (seeds)."""
import sys, os, json
import numpy as np
from scipy import ndimage as ndi
ROOT = "."
for d in ("tools", "crafts/crackle", "materials/guan_glaze"):
    sys.path.insert(0, os.path.join(ROOT, d))
import camera, lines as ln
import card
outp, dirs = sys.argv[1], sys.argv[2:]
cam = json.load(open(os.path.join(dirs[0], "camera.json")))
cal = camera.calibrate(camera.Spectra(cam["sensor"]), camera.balance_spectrum(cam))
lin = np.mean([np.maximum((camera.read_raw(os.path.join(d, "raw.exr")) * cal["gains"]) @ cal["C"].T, 0) for d in dirs], 0)
H, W = lin.shape[:2]
M = json.load(open(card.MEASURED))
px = M["scale"]["px_per_mm"] * W / 1920
lin = np.stack([ndi.gaussian_filter(lin[..., c], 0.75 * px / M["scale"]["px_per_mm"]) for c in range(3)], -1)
B = json.load(open(os.path.join(dirs[0], "build.json")))
region = np.zeros((H, W), bool)
cw, chh = int(round(card.CROP_MM[0] * px)), int(round(card.CROP_MM[1] * px))
region[H // 2 - chh // 2:H // 2 - chh // 2 + chh, W // 2 - cw // 2:W // 2 - cw // 2 + cw] = True
paths = [np.c_[H / 2 - np.asarray(c["pts"])[:, 1] * px - 0.5, W / 2 - np.asarray(c["pts"])[:, 0] * px - 0.5] for c in B["cracks"]]
paths = [q for q in paths if region[np.clip(q[:, 0].astype(int), 0, H - 1), np.clip(q[:, 1].astype(int), 0, W - 1)].mean() > 0.5]
r, prof, ori = ln.block_profiles(lin, None, px, paths=paths)
Yp = prof @ ln.LUMA
bgm = np.abs(r) >= 0.3
bg = np.median(prof[:, bgm], 1)
mp = np.mean(prof / bg[:, None, :], 0)
cen = np.abs(r) <= 0.15
c = Yp / np.median(Yp[:, bgm], 1)[:, None] - 1
pk = np.array([ck[np.nonzero(cen)[0][np.argmax(np.abs(ck[cen]))]] for ck in c])
pc = lambda a, q=(10, 50, 90): [round(float(np.percentile(a, x)), 3) for x in q]
res = {"blocks": int(len(prof)), "mean_profile_min_rgb": [round(float(mp[cen, k].min()), 3) for k in range(3)],
       "mean_profile_max_rgb": [round(float(mp[cen, k].max()), 3) for k in range(3)], "contrast_p10_p50_p90": pc(pk),
       "glaze_median_lin": [round(float(x), 4) for x in np.median(bg, 0)], "px_per_mm": round(px, 2), "dirs": dirs}
print(json.dumps(res))
json.dump(res, open(outp, "w"), indent=1)
