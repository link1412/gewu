"""Test d, the check: new against old cycles_scene.py, same seed, against the seed-to-seed noise.

    python3 -I tests/textures/check_regress.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def main():
    ok = True
    for name in ("s19", "s06"):
        d = os.path.join(C.OUT, "regress", name)
        o1, o2, n1, n2 = (C.read_image(os.path.join(d, f"{k}.exr")) for k in ("old1", "old2", "new1", "new2"))
        sig = np.abs(o1).mean()
        print(f"{name}: {o1.shape[1]}x{o1.shape[0]}, mean {o1.mean():.4g}")
        for label, a, b in (("new1 - old1 (same seed)", n1, o1), ("new2 - old2 (same seed)", n2, o2),
                            ("old2 - old1 (noise floor, other seed)", o2, o1), ("new2 - new1 (other seed)", n2, n1)):
            df = a - b
            print(f"  {label}: max |diff| {np.abs(df).max():.3g}, mean |diff| {np.abs(df).mean():.3g}, "
                  f"rms {np.sqrt((df ** 2).mean()):.3g} ({np.sqrt((df ** 2).mean()) / sig:.2%} of the mean); "
                  f"mean signed {df.mean():.3g}; pixels differing {(df != 0).any(2).mean():.1%}")
        same = (np.abs(n1 - o1).max() == 0) and (np.abs(n2 - o2).max() == 0)
        ok &= same or np.sqrt(((n1 - o1) ** 2).mean()) < 0.1 * np.sqrt(((o2 - o1) ** 2).mean())
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
