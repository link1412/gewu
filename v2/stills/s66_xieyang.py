"""Shot 66: the oil-paper umbrella from below and to one side, turning, the sun coming through its paper. Its far rim is the arc.

    python3 -I v2/stills/s66_xieyang.py [sketch|preview|mid|final]
    python3 -I v2/stills/s66_xieyang.py motion            all frames small: out/v2/s66_xieyang_move_preview/ with take.mp4 (kit's own preview takes only every 6th frame, which shows no motion)
    GEWU_MOVE=check|final python3 -I v2/stills/s66_xieyang.py final

The view from above (s65) did not work; so from below, at a slant. What is beautiful in this object is on its underside: the lit paper, the ribs, the lacing.
Every part, the grove and the sun are s21_youzhisan.py's, run with other numbers (its source with the last line cut off, so s21 stays as it is). What differs:
- the angle: about 55 degrees off the umbrella's axis, against s21's 42, and the camera looks up, so the far rim is against the grove's sky;
- the red: s65's absorption, set for the photographed umbrellas' (217,42,34) under flat light, against s21's brownish vermilion;
- it turns. The shadows of the sprays stay still while the paper goes round under them.
ESTIMATES, none measured: the angle, the framing, the turn; all of s21's sizes.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
from kit import OUT, color, shoot

NAME = "s66_xieyang"
FRAMES = 24
TURN = -1.4  # degrees per frame; 7.5 degrees between ribs. About 15% slower than s65: the film a little slower, rendered that way

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s21_youzhisan.py")
_src = open(_p).read()
U = {"__file__": _p, "__name__": "s21_parts"}
exec(compile(_src[: _src.rindex("\nmain()")], _p, "exec"), U)
U.update(NAME=NAME, AXIS_EL=72.0, AXIS_AZ=-20.0, W=84.0, EL=-24.0, DIST=125.0, APEX=0.42, APERTURE=24.0, SIGMA=color([0.12, 2.85, 3.2]))
LOOK = {"exposure": -0.3, "saturation": 1.04}


def _shoot(name, scene, q, tag=None, develop=None):
    shoot(name, scene, q, tag=tag, develop={**develop, **LOOK})


def _small_take(name, cfg, lk, move, develop, q):
    """All frames, small, so that the motion can be judged. As s65's."""
    mv = lk["move"]
    path = kit.camera_path(cfg["camera"], cfg.get("lights", []), mv, mv["frames"])
    d = os.path.join(OUT, f"{name}_move_preview")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    cfg.update(res=[640, 360], frames=path, fetch_to=d, shutter=mv.get("shutter", 0.5), spin=mv["spin"], spp=40)
    kit._render_local(cfg, os.path.join(OUT, name), "take")
    from darkroom import develop as dev

    for i, f in enumerate(sorted(x for x in os.listdir(d) if x.endswith(".npy"))):
        im = dev(np.load(os.path.join(d, f)).astype(np.float32), **{**develop, "seed": 700 + i})
        cv2.imwrite(os.path.join(d, f"f{i:03d}.png"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(d, "f%03d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(d, "take.mp4")], check=True)
    print(os.path.join(d, "take.mp4"), flush=True)


def main():
    orig = kit.looks
    axis = U["basis"]()[2].tolist()
    move = {"spin": {"pt": [0.0, 0.0, 0.0], "axis": axis, "deg": TURN * (FRAMES - 1), "meshes": ["paper", "ribs", "stretch", "lace", "wraps", "runner", "crown", "shaft"]}, "frames": FRAMES, "shutter": 0.5}
    kit.looks = lambda: {**orig(), NAME: {"move": move}}
    U["shoot"] = _shoot
    if sys.argv[1:] == ["motion"]:
        kit._take = _small_take
        os.environ["GEWU_MOVE"] = "preview"
        sys.argv[1:] = ["preview"]
    U["main"]()


main()
