"""Yohen tenmoku (曜变天目), the second time in the film: close on the far wall like s02, from higher and further into the bowl, the arc crossing the frame. A different bowl's worth of spots (its own seed) and a different character: mostly deep black, the colour only in places, where s02 is full of it.

Rebuilt on the glaze of yohen.py, the same as s02 (real thin-film interference on a satin oxide lobe, a glass skin above with a real gap, bubbles in it), see there for what is measured and what is estimated.
Bowl about 12.2 cm across (museum record); section estimated. Above the arc the photographer's grey-black, as in s02: the linen table it stood on showed only as a weave behind the arc.
The room replaces kit.room_env.

    python3 -I v2/stills/s47_yaobian.py [preview|mid|final]     final goes to cand.*, never final.*; the move's frames to s47_yaobian_take_c_move_final
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import kit
import yohen
from dishkit import Dish
from kit import OUT, shoot

NAME = "s47_yaobian"
SEED = 47
DEV = {"exposure": 0.45, "contrast": 1.3, "saturation": 1.0, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "vignette": 0.22}
HERE = os.path.dirname(os.path.abspath(__file__))
W, EL, DIST = 9.0, 48.0, 38.0
APEX_Y = 0.48
RUN = "s47_yaobian_take_c"  # the candidate's own folder: nothing here touches final.* or *_move_final, and "_take_" makes kit read this shot's move from looks.json
TURN = 4.0  # degrees in the shot: the 10 it had at 15 cm of frame would run 20 px a frame at the lip here
PROFILE = [(2.2, 0.0), (2.4, 0.5), (3.6, 1.7), (5.0, 3.6), (5.85, 5.2), (6.12, 6.05), (6.1, 6.22), (5.92, 6.2), (5.7, 5.85), (5.56, 5.45), (5.25, 4.75), (4.3, 3.35), (3.1, 2.05), (2.0, 1.2), (1.1, 0.8), (0.0, 0.7)]



def crop(dish, X, Y, extra=0.5):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, RUN)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, ds=0.0005)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, APEX_Y), aperture_mm=5.5, focus_rho=dish.rho_lip - 0.7)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 370.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.07))
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    rl = dish.rho_lip
    # s02's close-up look (narrow pale ring, soft hatch), s47's sparse ponds: the black stays
    vivid = {"spacing": 0.62, "pond": (0.5, 0.94), "soft": 0.4, "hue": 8.0, "flash": 2.5, "satin": 0.26, "crust": 0.22, "silver": True, "tint": 0.3, "island": 0.2, "fade": 1.75, "ramp": [172, 161, 156, 153.6, 152.8, 152.3, 151.8], "hair": 2.0, "ring": (0.05, 0.015), "spot_var": 1.1, "rim": (0.2, 0.07)}
    f = yohen.paint(dish, X, Y, pxcm, SEED, n_cl=520, rho0=1.0, rho1=rl - 0.3, r_big=(0.06, 0.15), pack=0.85, blue=1.2, hatch_w=0.0078, metal_frac=0.8, vivid=vivid)
    npz_u = os.path.join(d, f"under.{q}.npz")
    np.savez(npz_u, **yohen.front(P=dish.surface(X, Y, f["h"]), col=f["col"], rough=f["rough"], film=f["film"], cov=f["cov"]))
    Xs, Ys = X[::2, ::2], Y[::2, ::2]
    hs, rs, on = yohen.shell_fields(dish, Xs, Ys, pxcm / 2, SEED, wave=0.0018, rings=0.0009, scratches=0.8)
    npz_s = os.path.join(d, f"shell.{q}.npz")
    np.savez(npz_s, **yohen.front(P=dish.surface(Xs, Ys, hs), rough=rs, on=on))
    npz_b = os.path.join(d, f"bubbles.{q}.npz")
    np.savez(npz_b, **yohen.front(P=yohen.bubbles(dish, X, Y, SEED, per_cm2=18.0)))

    # the room: as in s02, a museum case's small lamps, one key behind the camera. A dim overcast in the glass so that the far wall reads as a surface: its reflection is a slow fall of grey across the black
    yohen.use_room()
    panels = yohen.lamp_field(dish, cam, SEED, sep=11.0, L=(900.0, 1800.0), size=(0.4, 0.23))
    rg, _, _ = yohen.reflection_at(dish, cam, 0.34, 0.72)
    panels.append({"dir": rg.tolist(), "w": 34, "h": 12, "L": 0.14, "rgb": [0.95, 0.97, 1.0], "soft": 9, "grad": 0.4})
    env = {"diffuse": True, "base": [0.012, 0.012, 0.014], "panels": panels}
    tgt = dish.polar(np.array(rl - 1.0), np.pi / 2).tolist()
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "under", "npz": npz_u, "shader_py": os.path.join(HERE, "yohen_shader.py"), "params": {"kind": "under", "film_ior": yohen.FILM_N, "ior": yohen.GLASS_N, "bare_spec": 0.08, "metal": 1.0}},
            {"name": "shell", "npz": npz_s, "shader_py": os.path.join(HERE, "yohen_shader.py"), "params": {"kind": "shell", "ior": yohen.GLASS_N}},
            {"name": "bubbles", "npz": npz_b, "shader_py": os.path.join(HERE, "glaze_shader.py"), "params": {"kind": "bubble", "ior": yohen.GLASS_N}},
        ],
        "env": env,
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": APEX_Y, "seed": 47},
        "lights": [
            {"name": "key", "loc": [-12.0, -30.0, 52.0], "target": tgt, "size": [30, 30], "watts": 13000, "rgb": [1.0, 0.97, 0.93], "hide_in_gloss": True},
        ],
        "bounces": 12,
        "glossy_bounces": 6,
        "diffuse_bounces": 2,
        "transmission_bounces": 8,
        "spp": {"preview": 96, "mid": 192, "final": 384},
    }
    if os.environ.get("GEWU_MOVE"):  # the turn this close, with nothing but the sky left out of it: move it into looks.json when this take goes into the film. Full size for final, and only this run sees that
        lk = kit.looks()
        mv = {**lk[NAME]["move"], "spin": {**lk[NAME]["move"]["spin"], "deg": TURN, "meshes": {"except": ["sky"]}}}
        if os.environ["GEWU_MOVE"] == "final":
            mv.update(res=[2560, 1440], spp=192)
        lk[NAME]["move"] = mv
        kit.looks = lambda: lk
    shoot(RUN, scene, q, develop=DEV, tag={"final": "cand"}.get(q, q))


def deliver():
    """The take's linear frames, developed into out/v2/s47_yaobian_take_cand: f###.png, f###.jpg, take.mp4, the form the dev page reads."""
    import json
    import subprocess

    import cv2

    from darkroom import develop as dev, save_png

    src = os.path.join(OUT, RUN + "_move_final")
    dst = os.path.join(OUT, NAME + "_take_cand")
    os.makedirs(dst, exist_ok=True)
    fs = sorted(f for f in os.listdir(src) if f.startswith("take.linear_") and f.endswith(".npy"))
    for i, f in enumerate(fs):
        img = dev(np.load(os.path.join(src, f)).astype(np.float32), **{**DEV, "seed": i + 1})
        save_png(os.path.join(dst, f"f{i:03d}.png"), img)
        cv2.imwrite(os.path.join(dst, f"f{i:03d}.jpg"), (img * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
    json.dump(DEV, open(os.path.join(dst, "develop.json"), "w"))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-r", "25", "-i", os.path.join(dst, "f%03d.jpg"), "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-movflags", "+faststart", os.path.join(dst, "take.mp4")])
    print(dst, len(fs))


if sys.argv[1:] == ["deliver"]:
    deliver()
else:
    main()
