"""Compare a tools/lightfit.py result with shots/19-luodian/fit.py's lights.json-style output.

    python3 -I tests/lightfit/against_fitpy.py LIGHTFIT.json FITPY.json
"""
import json
import sys

import numpy as np

m, r = (json.load(open(p)) for p in sys.argv[1:3])
scale = max(np.abs(v).max() for v in r["groups"].values())
d = max(np.abs(np.array(m["weights"][g]) - np.array(v)).max() for g, v in r["groups"].items())
print(f"weights: max |diff| {d:.3g} (of max weight {scale:.4g}, rel {d / scale:.2g})")
print(f"gain: {m['gain']} vs {r['fit']['gain']}; tie chroma {m['tie_chroma']['panel']} vs {r['fit']['shared_chroma']}")
fr = next(k for k, v in m["residuals"].items() if not v["held_out"])
print(f"rms 8-bit ({fr}): {m['residuals'][fr]['rms_8bit']} vs {r['fit']['rms_8bit']} ({m['residuals'][fr]['entries']} vs {r['fit']['rows']} rows)")
print(f"variant: {m['variant']} vs {r['fit']['ramp']['order'][0]} below {r['fit']['ramp']['split']}")
