"""The arc of a picture, with the same ruler used on the original film (the original is composed around one arc, several of ours are not).

    python3 -I tools/arc.py IMAGE...     apex x and y, sagitta and the share of columns on the arc, for each image (jpg, png; 16-bit is fine)
    python3 -I tools/arc.py --film       every shot of v2/cut.json, with what is out of range

Measured on the original (spec/shots.json, 30 shots with a clean arc): sagitta over the frame's width .036 to .201, median .079; apex x .43 to .55; apex y .46 to .58, median .49.
Sagitta = R - sqrt(R*R - .25), with R the arc's radius in frame widths: .20 means a subject at least 1.45 frame widths across, .10 means 2.6, .08 means 3.2.
The ruler finds the first row in each column that leaves the sky, so it reads badly when the sky is not plain or the edge is broken: a low `on arc` means look at the picture before believing the numbers.
"""

import glob
import json
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAG = (0.036, 0.20)
APEX_X = (0.43, 0.55)
APEX_Y = (0.44, 0.58)  # the caption is at .37 in film.py, so .42 is the hard floor

W, H = 960, 540

def edge(g):
    """g float 0..1 display, W x H. First row in each column that leaves the sky."""
    b = cv2.GaussianBlur(g, (0, 0), 2.0)
    sky = np.median(b[: int(H * 0.12)], axis=0)  # the sky of this column
    sky = cv2.GaussianBlur(sky[None], (0, 0), 25)[0]
    noise = np.std(b[: int(H * 0.12)]) 
    T = max(0.035, 3.0 * float(noise))
    d = np.abs(b - sky[None]) > T
    ys = np.full(W, np.nan)
    for x in range(W):
        idx = np.flatnonzero(d[:, x])
        # must stay away from the sky for a while: a speck or a caption is not the edge
        for i in idx:
            if d[i: i + 14, x].mean() > 0.85:
                ys[x] = i
                break
    return ys

def fit(ys, seed=1):
    """Circle through columns, RANSAC in pixels at 960 wide. Returns cx, cy, R, inlier share of all columns, resid."""
    x = np.flatnonzero(np.isfinite(ys)); y = ys[x]
    if len(x) < 60:
        return None
    rng = np.random.default_rng(seed); best = None; TOL = 6.0
    for _ in range(1500):
        i = rng.choice(len(x), 3, replace=False)
        A = np.c_[2 * x[i], 2 * y[i], np.ones(3)]; b = x[i] ** 2 + y[i] ** 2
        try:
            s = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            continue
        cx, cy = s[0], s[1]; R2 = s[2] + cx * cx + cy * cy
        if R2 <= 0 or cy < y[i].max():  # convex up only: centre below the edge
            continue
        R = np.sqrt(R2)
        r = np.abs(np.hypot(x - cx, y - cy) - R)
        n = (r < TOL).sum()
        if best is None or n > best[0]:
            best = (n, cx, cy, R)
    if best is None:
        return None
    n, cx, cy, R = best
    for _ in range(4):  # refine on the inliers
        r = np.abs(np.hypot(x - cx, y - cy) - R); m = r < TOL
        A = np.c_[2 * x[m], 2 * y[m], np.ones(m.sum())]; b = x[m] ** 2 + y[m] ** 2
        s = np.linalg.lstsq(A, b, rcond=None)[0]; cx, cy = s[0], s[1]; R = np.sqrt(s[2] + cx * cx + cy * cy)
    r = np.abs(np.hypot(x - cx, y - cy) - R); m = r < TOL
    return dict(cx=float(cx), cy=float(cy), R=float(R), inl=float(m.sum()) / W, resid=float(np.sqrt((r[m] ** 2).mean())), cov=len(x) / W)

def measure(img):
    """img: uint8 BGR any size."""
    g = cv2.cvtColor(cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    ys = edge(g); f = fit(ys)
    if f is None:
        return {"none": True, "cov": float(np.isfinite(ys).mean())}, ys
    f.update(apex_x=f["cx"] / W, apex_y=(f["cy"] - f["R"]) / H, sag=(f["R"] - np.sqrt(max(f["R"] ** 2 - (W / 2) ** 2, 0.0))) / W, R_W=f["R"] / W)
    return f, ys


def text(f):
    if f.get("none"):
        return f"no arc found, {f['cov']:.2f} of columns have an edge"
    return f"apex x {f['apex_x']:.3f} y {f['apex_y']:.3f}  sagitta {f['sag']:.3f}  on arc {f['inl']:.2f}"


def wrong(f):
    if f.get("none"):
        return ["no arc"]
    out = []
    if f["sag"] > SAG[1]:
        out.append(f"too curved: subject {f['R_W'] * 2:.2f} frame widths across, needs 1.45 or more")
    if f["apex_y"] < APEX_Y[0] or f["apex_y"] > APEX_Y[1]:
        out.append("apex y out of range")
    if f["apex_x"] < APEX_X[0] or f["apex_x"] > APEX_X[1]:
        out.append("apex x off centre")
    return out


def read(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit(f"cannot read {path}")
    if im.dtype == np.uint16:
        im = (im / 257).astype(np.uint8)
    return im[..., :3]


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    if args[0] != "--film":
        for p in args:
            f, _ = measure(read(p))
            print(f"{p}: {text(f)}" + "".join(f"  [{w}]" for w in wrong(f)))
        return
    c = json.load(open(os.path.join(ROOT, "v2/cut.json")))
    for ov in c["shots"]:
        o = os.path.join(ROOT, "out/v2", ov["src"])
        takes = sorted(glob.glob(o + "_take_final/f*.png"))
        if takes and not os.path.isdir(o + "_move_final") and not ov.get("still"):
            p = takes[min(ov.get("first", 0) + ov["len"] // 2, len(takes) - 1)]
        else:
            p = o + "/final.jpg"
        f, _ = measure(read(p))
        print(f"{ov['src']:18s} {ov['name']:6s} {text(f)}" + "".join(f"  [{w}]" for w in wrong(f)))


if __name__ == "__main__":
    main()
