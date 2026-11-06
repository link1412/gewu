"""The Guan heirloom card's crack lines in Cycles against pbrt (docs/slab.md, "裂缝"): the card's scene
(out/ru/guan_check/heirloom, materials/guan_glaze/card.py) with one change at a time, rendered by both, and the
line / off-line / frame means compared as tests/slab/guan_card.py does (its mask: pixels 3% darker than their 9-pixel
neighbourhood in the independent Cycles image cyc-heirloom-s7.exr).

    python3 -I tests/slab/crack_probes.py write                 # out/ru/guan_check/probes/<probe>/ (+ scene.cycles.json)
    python3 -I tests/slab/crack_probes.py queue > q.sh          # the queue: pbrt on CPU slots, Cycles on the GPU
    python3 -I tests/slab/crack_probes.py table                 # after fetching <probe>/{pbrt,cyc}-s<seed>.exr

A probe's directory holds its scene files; the meshes are links to the card's.

"""
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import read_raw  # noqa: E402

CARD = os.path.join(ROOT, "out/ru/guan_check/heirloom")
OUT = os.path.join(ROOT, "out/ru/guan_check/probes")
MASK = os.path.join(ROOT, "out/ru/guan_check/r/cyc-heirloom-s7.exr")
REMOTE_CARD = "ru2-guan-heirloom"
MESHES = ["body.ply", "deposit.ply", "gap.ply", "outer.ply", "h.exr"]

# name -> (what changes, {"drop": [ply files whose shape block goes], "flat": [ply files written without normals],
#          "eta1": the gap a thindielectric of eta 1, "nobump": the glaze surface without its "displacement"})
PROBES = {
    "base": ("the card as it is", {}),
    "nodep": ("no deposit (the gap alone)", {"drop": ["deposit.ply"]}),
    "nogap": ("no gap (the deposit alone)", {"drop": ["gap.ply"]}),
    "flatgap": ("the gap without vertex normals (geometric normals in both)", {"flat": ["gap.ply"]}),
    "nocrack": ("no gap, no deposit (the glaze's relief and the body only)", {"drop": ["gap.ply", "deposit.ply"]}),
    "nobump": ("the glaze surface without its bump map (the cracks kept)", {"nobump": True}),
    "nobump_nocrack": ("no bump, no cracks", {"nobump": True, "drop": ["gap.ply", "deposit.ply"]}),
}
SPP = {"pbrt": 64, "cycles": 256}
SEEDS = {"base": (1, 2)}


def read_ply(path):
    raw = open(path, "rb").read()
    h = raw.index(b"end_header\n") + len(b"end_header\n")
    head = raw[:h].decode()
    nv = int(head.split("element vertex ")[1].split()[0])
    nf = int(head.split("element face ")[1].split()[0])
    props = [l.split()[-1] for l in head.splitlines() if l.startswith("property float")]
    V = np.frombuffer(raw, "<f4", nv * len(props), h).reshape(nv, len(props))
    F = np.frombuffer(raw, dtype=[("n", "u1"), ("i", "<i4", (3,))], count=nf, offset=h + nv * 4 * len(props))
    if not (F["n"] == 3).all():
        raise SystemExit(f"{path}: only triangles")
    return V[:, :3].copy(), F["i"].copy()


def write_ply(path, P, T):
    P, T = np.asarray(P, "<f4"), np.asarray(T, "<i4")
    head = (f"ply\nformat binary_little_endian 1.0\nelement vertex {len(P)}\nproperty float x\nproperty float y\n"
            f"property float z\nelement face {len(T)}\nproperty list uchar int vertex_indices\nend_header\n")
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"], face["i"] = 3, T
    with open(path, "wb") as f:
        f.write(head.encode())
        f.write(np.ascontiguousarray(P).tobytes())
        f.write(face.tobytes())


def write():
    src = open(os.path.join(CARD, "scene.pbrt")).read()
    for name, (_, ch) in PROBES.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        text = src
        for m in MESHES:
            p = os.path.join(d, m)
            if os.path.lexists(p):
                os.remove(p)
            os.symlink(os.path.join("..", "..", "heirloom", m), p)
        blocks = text.split("AttributeBegin")
        keep = [blocks[0]]
        for b in blocks[1:]:
            if any(f'"{f}"' in b for f in ch.get("drop", [])):
                continue
            if ch.get("eta1") and '"gap.ply"' in b:
                b = b.replace('Material "thindielectric" "float eta" [ 0.66667 ]', 'Material "thindielectric" "float eta" [ 1 ]')
            keep.append(b)
        text = "AttributeBegin".join(keep)
        if ch.get("nobump"):
            assert ' "texture displacement" "h"' in text
            text = text.replace(' "texture displacement" "h"', "")
        for f in ch.get("flat", []):
            P, T = read_ply(os.path.join(CARD, f))
            flat = f.replace(".ply", "_flat.ply")
            write_ply(os.path.join(d, flat), P, T)
            text = text.replace(f'"{f}"', f'"{flat}"')
        text = text.replace("# material card", f"# crack probe {name}: {PROBES[name][0]} (tests/slab/crack_probes.py)\n# material card", 1)
        open(os.path.join(d, "scene.pbrt"), "w").write(text)
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools/rgbscene.py"), os.path.join(d, "scene.pbrt")],
                       check=True)
    print(f"{len(PROBES)} probes in {OUT}")


def queue(only=None):
    print("#!/bin/bash\n# crack probes (tests/slab/crack_probes.py queue): pbrt in the CPU slots (in the background), "
          "Cycles on the GPU one after another\nS=$HOME/gewu-render/scenes")
    for name, (what, ch) in PROBES.items():
        if only and name not in only:
            continue
        extra = [os.path.basename(f).replace(".ply", "_flat.ply") for f in ch.get("flat", [])]
        print(f"# {name}: {what}\nD=$S/ru3-{name}; mkdir -p $D; cd $D")
        for m in MESHES:
            print(f"ln -sf ../{REMOTE_CARD}/{m} {m}")
        for seed in SEEDS.get(name, (1,)):
            print(f"rm -f /tmp/gewu-ru3-{name}-pbrt-s{seed}.log; nohup ~/gewu-render/bin/mini-pbrt.sh $D scene.pbrt "
                  f"/tmp/gewu-ru3-{name}-pbrt-s{seed}.log --seed {seed} --spp {SPP['pbrt']} --outfile $D/pbrt-s{seed}.exr "
                  f"< /dev/null > /dev/null 2>&1 &")
        _ = extra
    for name in PROBES:
        if only and name not in only:
            continue
        for seed in SEEDS.get(name, (1,)):
            print(f"cd $S/ru3-{name}; rm -f /tmp/gewu-ru3-{name}-cyc-s{seed}.log; ~/gewu-render/bin/mini-gpu.sh "
                  f"/tmp/gewu-ru3-{name}-cyc-s{seed}.log -b --factory-startup --python-exit-code 1 -P "
                  f"$HOME/gewu-render/tools/cycles_scene.py -- scene.cycles.json --spp {SPP['cycles']} --seed {seed} "
                  f"--out $S/ru3-{name}/cyc-s{seed}.exr < /dev/null > /dev/null 2>&1")
    print("echo done > /tmp/gewu-ru3.done")


def metrics(img, line, rest):
    """Per channel: frame mean, line mean, off-line mean; and G's line contrast (line pixel over its 9-pixel mean)."""
    from scipy.ndimage import uniform_filter
    G = img[..., 1]
    return {"frame": img.mean((0, 1)), "line": img[line].mean(0), "off": img[rest].mean(0),
            "contrast": float((G[line] / uniform_filter(G, 9)[line]).mean())}


def table():
    from scipy.ndimage import uniform_filter
    g = read_raw(MASK)[..., 1]
    loc = uniform_filter(g, 9)
    line, rest = g < 0.97 * loc, g > loc
    rows = {}
    print(f"{'probe':9s} {'':6s} {'frame G':>8s} {'line G':>8s} {'off G':>8s} {'contrast':>8s}   Cycles/pbrt: frame  line   off  (R G B on the line)")
    for name, (what, _) in PROBES.items():
        res = {}
        for r in ("pbrt", "cyc"):
            for seed in SEEDS.get(name, (1,)):
                p = os.path.join(OUT, name, f"{r}-s{seed}.exr")
                if os.path.exists(p):
                    res[(r, seed)] = metrics(read_raw(p), line, rest)
        for (r, seed), m in sorted(res.items()):
            print(f"{name:9s} {r + '-s' + str(seed):6s} {m['frame'][1]:8.5f} {m['line'][1]:8.5f} {m['off'][1]:8.5f} {m['contrast']:8.4f}")
        s = SEEDS.get(name, (1,))[0]
        if ("pbrt", s) in res and ("cyc", s) in res:
            p, c = res[("pbrt", s)], res[("cyc", s)]
            q = {k: (c[k] / p[k]).tolist() for k in ("frame", "line", "off")}
            print(f"{'':16s} {'':35s}   {q['frame'][1]:.4f} {q['line'][1]:.4f} {q['off'][1]:.4f}  ("
                  + " ".join(f"{v:.4f}" for v in q["line"]) + f")  contrast {c['contrast']:.4f} / {p['contrast']:.4f}")
            rows[name] = {"what": what, "cyc_over_pbrt": q, "contrast_cyc": c["contrast"], "contrast_pbrt": p["contrast"]}
        # two seeds: the noise of each number, from the difference
        for r in ("pbrt", "cyc"):
            if (r, 1) in res and (r, 2) in res:
                a, b = res[(r, 1)], res[(r, 2)]
                print(f"{'':9s} {r:6s} noise (|s1 - s2| / sqrt 2, relative): frame {abs(a['frame'][1] / b['frame'][1] - 1) / 2 ** 0.5:.4f}"
                      f"  line {abs(a['line'][1] / b['line'][1] - 1) / 2 ** 0.5:.4f}  off {abs(a['off'][1] / b['off'][1] - 1) / 2 ** 0.5:.4f}"
                      f"  contrast {abs(a['contrast'] - b['contrast']) / 2 ** 0.5:.4f}")
    with open(os.path.join(OUT, "table.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "write":
        write()
    elif cmd == "queue":
        queue(sys.argv[2].split(",") if len(sys.argv) > 2 else None)
    elif cmd == "table":
        table()
