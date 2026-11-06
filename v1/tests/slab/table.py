"""The variants' table: each renderer's frame mean over the light's sensor RGB (pixel / E1), against the Monte
Carlo (tests/slab/variants.py mc). Run after the renders are fetched into out/ru/lt/<variant>/{raw,cyc}.exr.

    python3 -I tests/slab/table.py           # the variants
    python3 -I tests/slab/table.py probes    # the Cycles probes (variants.PROBES), out/ru/lt/<variant>/probe-*.exr
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import read_raw  # noqa: E402

OUT = os.path.join(ROOT, "out/ru/lt")
E1 = np.array([0.45682123816966275, 0.9611177928535815, 0.6856201783145797])   # light 1, sensor RGB (rgbscene)


def stat(path, middle=True):
    """The frame's mean over the key light's sensor RGB, and its standard error from 6 x 6 blocks. middle: only the
    middle third in each direction, where the distant lights subtend what they do from the frame's centre (the
    Monte Carlo's entry point) to well under 0.1%."""
    if not os.path.exists(path):
        return None, None
    a = read_raw(path) / E1                      # per channel, over the light's own sensor RGB
    if middle:
        h, w, _ = a.shape
        a = a[h // 3: h - h // 3, w // 3: w - w // 3]
    v = a.mean(2)                                # the medium is grey: the three channels agree
    # the standard error from 6 x 6 blocks of the frame (pixels are independent samples of one number)
    h, w = v.shape
    b = v[: h - h % 6, : w - w % 6].reshape(6, (h - h % 6) // 6, 6, (w - w % 6) // 6).mean((1, 3)).ravel()
    return float(v.mean()), float(b.std(ddof=1) / np.sqrt(len(b)))


def probes():
    """The Cycles probes against their references: unlimited, and at Cycles' 64 bounces where it differs."""
    import variants
    mc = json.load(open(os.path.join(OUT, "mc.json")))
    refs = json.load(open(os.path.join(OUT, "mc_probes.json")))
    look = lambda k: None if k is None else (mc[k[3:]] if k.startswith("mc:") else refs.get(k))
    rows = []
    print(f"{'probe':48s} {'Cycles':>16s} {'reference':>16s} ratio  (z)   {'64 vertices':>16s} ratio  (z)")
    for label, var, probe, ref, ref64 in variants.PROBES:
        c, cs = stat(os.path.join(OUT, var, variants.probe_slug(probe) + ".exr"))
        row = {"probe": label, "variant": var, "GEWU_PROBE": probe, "cycles": c, "cycles_se": cs}
        line = f"{label:48s} " + (f"{c:.5f}+-{cs:.5f}" if c is not None else f"{'-':>16s}")
        for key, r in (("ref", look(ref)), ("ref64", look(ref64))):
            if r is None or c is None:
                line += f" {'-':>16s}" + " " * 14
                continue
            v, s = r["pixel_over_E1"], r["pixel_se"]
            line += f" {v:.5f}+-{s:.5f} {c / v:.3f} ({(c - v) / np.hypot(cs, s):+5.1f})"
            row[key], row[key + "_value"], row[key + "_se"] = (ref if key == "ref" else ref64), v, s
        print(line)
        rows.append(row)
    with open(os.path.join(OUT, "probes.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


def main():
    if sys.argv[1:] == ["probes"]:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        return probes()
    mc = json.load(open(os.path.join(OUT, "mc.json")))
    rows = []
    print(f"{'variant':18s} {'MC':>8s} {'pbrt':>16s} {'Cycles':>16s}   pbrt/MC  Cycles/MC")
    for name, m in mc.items():
        ref = m["pixel_over_E1"]
        p, ps = stat(os.path.join(OUT, name, "raw.exr"))
        c, cs = stat(os.path.join(OUT, name, "cyc.exr"))
        f = lambda v, s: f"{v:.5f}+-{s:.5f}" if v is not None else "-"
        r = lambda v: f"{v / ref:8.4f}" if v is not None else "       -"
        print(f"{name:18s} {ref:8.5f} {f(p, ps):>16s} {f(c, cs):>16s}  {r(p)}  {r(c)}")
        rows.append({"variant": name, "mc": ref, "pbrt": p, "pbrt_se": ps, "cycles": c, "cycles_se": cs})
    with open(os.path.join(OUT, "table.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
