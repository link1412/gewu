"""Develop a rendered still again without rendering. python3 -I v2/develop.py NAME TAG ['{"exposure": 0.3}']"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from darkroom import develop, save_png
from kit import OUT

name, tag = sys.argv[1], sys.argv[2]
kw = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
out = sys.argv[4] if len(sys.argv) > 4 else tag
d = os.path.join(OUT, name)
L = np.load(os.path.join(d, f"{tag}.linear.npy"))
img = develop(L, **kw)
save_png(os.path.join(d, f"{out}.png"), img)
cv2.imwrite(os.path.join(d, f"{out}.jpg"), (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 96])
print(os.path.join(d, f"{out}.jpg"), "linear p50", float(np.median(L)), "p99", float(np.percentile(L, 99)))
