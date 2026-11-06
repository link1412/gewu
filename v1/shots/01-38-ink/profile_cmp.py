"""Plot our centre-column profile against the original's frame 0 (diagnostic for fit.py).
    python3 -I shots/01-38-ink/profile_cmp.py MAPS OUT.png [--res 320]"""
import json, os, sys
import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M, optics as op, fit as F
maps, out = sys.argv[1], sys.argv[2]
res = int(sys.argv[3]) if len(sys.argv) > 3 else 320
P = json.load(open(os.path.join(HERE, "params.json"))); O = json.load(open(F.OPT))
sheet = op.Sheet(maps, P)
W, H = res, res * 9 // 16
codes = F.to_codes(F.full_render(sheet, O, O["camera"], W, H))
ref = M.decode_original([0])[0].astype(float)
ref_s = ndimage.zoom(ref, (H / M.FH, W / M.FW, 1), order=1)
c0, c1 = int(880 / 1920 * W), int(1040 / 1920 * W)
a, b = codes[:, c0:c1].mean(1), ref_s[:, c0:c1].mean(1)
y = np.arange(H) / H
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for c, col in enumerate("rgb"):
    ax[0].plot(y, b[:, c], col + "-", lw=2); ax[0].plot(y, a[:, c], col + "--", lw=1.5)
ax[0].set_xlabel("row / H (solid original, dashed ours)")
ax[1].imshow(np.concatenate([ref_s / 255, codes / 255], 1))
fig.tight_layout(); fig.savefig(out, dpi=80)
