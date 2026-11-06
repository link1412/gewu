"""Shot 17: our arc from the colour boundary (the blue-green zone against the brown ring), as the spec fits arcs.

    python3 -I shots/17-peacock/measure.py out/shots/17-peacock/r1/dev1080/f0240.png [--orig 240]

tools/shotcheck.py's arc fitter takes the strongest step per column (spec_measure.fit_arc), and on our frame the
darkest gaps between the brown barbs win over the zone's edge. Here a pixel is 'zone' where G - R > 40 codes
(blue-green: R ~ 54 G ~ 197 in the original; the brown ring: R > G), smoothed over 15 px; the top of the zone column by
column is fitted with optics/framing.py measure. --orig F runs the same on the original's frame F, as a control.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "optics"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import framing  # noqa: E402


def arc(im):
    im = np.asarray(im, np.float32)
    z = ndimage.uniform_filter((im[..., 1] - im[..., 0]), 15) > 40
    z = ndimage.binary_opening(z, iterations=3)
    H, W = z.shape
    x, y = [], []
    for c in range(0, W, framing.BIN_PX):
        col = z[:, c:c + framing.BIN_PX].mean(1) > 0.5
        run = np.convolve(col, np.ones(60), "valid") >= 57          # 60 rows mostly zone below the edge
        r = np.nonzero(run)[0]
        if len(r):
            x.append(c + framing.BIN_PX / 2)
            y.append(r[0])
    return framing.measure(np.array(x, float), np.array(y, float))


ap = argparse.ArgumentParser()
ap.add_argument("png")
ap.add_argument("--orig", type=int)
a = ap.parse_args()
r = arc(Image.open(a.png).convert("RGB"))
print("ours ", {k: round(v, 4) for k, v in r.items()})
if a.orig is not None:
    import shotcheck
    o = arc(shotcheck.orig_frames([a.orig])(a.orig))
    print("orig ", {k: round(v, 4) for k, v in o.items()})
    print(f"apex dy {abs(r['apex_y'] - o['apex_y']):.3f} of the height (tol 0.03), sagitta ratio {r['sagitta_of_width'] / o['sagitta_of_width']:.3f} (tol 0.7-1.3)")
