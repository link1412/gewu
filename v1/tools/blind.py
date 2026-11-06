"""Blind A/B pair for a judge: a real photo and a render, at the same scale and size, renamed A and B.

    python3 -I tools/blind.py PHOTO.png RENDER.png OUTDIR --seed yanzhi-r1

Writes OUTDIR/blind/A.png and OUTDIR/blind/B.png (pixels only: re-saved, no metadata, no source names) and
OUTDIR/key/key.json (which one is the photo). The judge is given OUTDIR/blind/ only. The order comes from the
seed (sha256), so the same seed gives the same order and a rerun can be checked; different rounds take
different seeds. Both images must already be cropped to the same size and px/mm by whoever made them:
this tool does not resample, it refuses a size mismatch.
"""
import argparse
import hashlib
import json
import os

import numpy as np
from PIL import Image


def load(p):
    im = Image.open(p)
    im.load()
    return np.asarray(im.convert("RGB"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("render")
    ap.add_argument("outdir")
    ap.add_argument("--seed", required=True)
    a = ap.parse_args()
    ph, rd = load(a.photo), load(a.render)
    if ph.shape != rd.shape:
        raise SystemExit(f"size mismatch: photo {ph.shape[1]}x{ph.shape[0]}, render {rd.shape[1]}x{rd.shape[0]}")
    photo_is_a = hashlib.sha256(a.seed.encode()).digest()[0] % 2 == 0
    pair = {"A": ph, "B": rd} if photo_is_a else {"A": rd, "B": ph}
    bd, kd = os.path.join(a.outdir, "blind"), os.path.join(a.outdir, "key")
    os.makedirs(bd, exist_ok=True)
    os.makedirs(kd, exist_ok=True)
    for k, v in pair.items():
        Image.fromarray(v).save(os.path.join(bd, k + ".png"))
    with open(os.path.join(kd, "key.json"), "w") as f:
        json.dump({"photo": "A" if photo_is_a else "B", "seed": a.seed,
                   "photo_src": os.path.abspath(a.photo), "render_src": os.path.abspath(a.render)}, f, indent=1)
    print(bd)


if __name__ == "__main__":
    main()
