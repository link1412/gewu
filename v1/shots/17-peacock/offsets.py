"""Shot 17 r2: the offsets codefit.py's targets move by (an integral loop on shotcheck's own numbers): per shotcheck
region (top60, middle, bottom), offset += shotcheck's ours - orig (python3 -I shots/17-peacock/offsets.py, after
shotcheck; then codefit again). The bottom's offset also moves its halves. [F]"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sc = json.load(open(os.path.join(ROOT, "out/check/17/shotcheck.json")))
pf = sc["per_frame"]
frames = list(pf.values()) if isinstance(pf, dict) else pf
offp = os.path.join(ROOT, "out/shots/17-peacock/codefit_offsets.json")
off = json.load(open(offp)) if os.path.exists(offp) else {}
for k in ("top60", "middle", "bottom"):
    e = [sum(f["ours"][k][c] - f["orig"][k][c] for f in frames) / len(frames) for c in range(3)]
    off[k] = [round(off.get(k, [0, 0, 0])[c] + e[c], 2) for c in range(3)]
json.dump(off, open(offp, "w"))
print(off)
