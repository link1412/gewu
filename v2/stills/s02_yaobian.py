"""Shot 2: yohen tenmoku, 曜变天目, close on the far wall: the rim is the arc, the wall a night sky under black glass.

Rebuilt after the blind review (four in a hundred: circles, blue glow, a patch of a highlight). See yohen.py for what is measured and what is estimated. In short:
- two layers with a real gap: the fired surface carrying a real interference film (Thin Film Thickness in nm per vertex), and a glass skin above it with slow waves, the potter's rings and hair scratches;
- the reflections come from a painted room (yohen.paint_room, in place of kit.room_env): the colour moves through the islands as the bowl turns;
- bowl about 12.2 cm across (museum record); section estimated.

    python3 -I v2/stills/s02_yaobian.py [preview|mid|final]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import kit
from dishkit import Dish
from kit import OUT, shoot
import yohen

NAME = "s02_yaobian"
SEED = 2
HERE = os.path.dirname(os.path.abspath(__file__))
W, EL, DIST = 8.0, 38.0, 34.0
PROFILE = [(2.2, 0.0), (2.4, 0.5), (3.6, 1.7), (5.0, 3.6), (5.85, 5.2), (6.12, 6.05), (6.1, 6.22), (5.92, 6.2), (5.7, 5.85), (5.56, 5.45), (5.25, 4.75), (4.3, 3.35), (3.1, 2.05), (2.0, 1.2), (1.1, 0.8), (0.0, 0.7)]




def crop(dish, X, Y, extra=0.45):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.4, "mid": 0.6, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, ds=0.0005)
    print("rho_lip", dish.rho_lip, "R", dish.R, "L", dish.L, flush=True)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.478), aperture_mm=5.0, focus_rho=dish.rho_lip - 0.5)
    print("sag", round(float(sag), 3), flush=True)

    pxcm = 400.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.07))
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    rl = dish.rho_lip
    vivid = {"spacing": 0.62, "pond": (0.42, 1.0), "soft": 0.4, "hue": 6.0, "flash": 2.5, "satin": 0.26, "crust": 0.2, "silver": True, "tint": 0.3, "island": 0.2, "fade": 1.75, "ramp": [171, 160, 155, 152.8, 152, 151.6, 151.2], "hair": 2.0, "ring": (0.05, 0.015), "spot_var": 1.1, "rim": (0.2, 0.07)}  # see yohen.py and s47; closer than s47, so the pale ring is narrower and the blue dies away more slowly
    f = yohen.paint(dish, X, Y, pxcm, SEED, n_cl=520, rho0=1.0, rho1=rl - 0.3, r_big=(0.06, 0.15), pack=0.85, blue=1.3, metal_frac=0.8, hatch_w=0.0075, vivid=vivid)
    npz_u = os.path.join(d, f"under.{q}.npz")
    np.savez(npz_u, **yohen.front(P=dish.surface(X, Y, f["h"]), col=f["col"], rough=f["rough"], film=f["film"], cov=f["cov"]))
    # the glass is thicker well above its own detail: half the density is enough
    Xs, Ys = X[::2, ::2], Y[::2, ::2]
    hs, rs, on = yohen.shell_fields(dish, Xs, Ys, pxcm / 2, SEED, wave=0.0018)
    npz_s = os.path.join(d, f"shell.{q}.npz")
    np.savez(npz_s, **yohen.front(P=dish.surface(Xs, Ys, hs), rough=rs, on=on))

    npz_b = os.path.join(d, f"bubbles.{q}.npz")
    np.savez(npz_b, **yohen.front(P=yohen.bubbles(dish, X, Y, SEED)))

    # --- the room. The shot's character: a northern window at dusk, low behind the camera to the left; one tall slit of lamp far right
    yohen.use_room()
    panels = yohen.lamp_field(dish, cam, SEED, L=(700.0, 1400.0), size=(0.33, 0.19))
    env = {"diffuse": True, "base": [0.012, 0.012, 0.014], "panels": panels}
    tgt = dish.polar(np.array(rl - 1.0), np.pi / 2).tolist()
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "under", "npz": npz_u, "shader_py": os.path.join(HERE, "yohen_shader_v1.py"), "params": {"kind": "under", "film_ior": yohen.FILM_N, "ior": yohen.GLASS_N, "bare_spec": 0.08, "metal": 1.0}},
            {"name": "shell", "npz": npz_s, "shader_py": os.path.join(HERE, "yohen_shader_v1.py"), "params": {"kind": "shell", "ior": yohen.GLASS_N}},
            {"name": "bubbles", "npz": npz_b, "shader_py": os.path.join(HERE, "glaze_shader_v1.py"), "params": {"kind": "bubble", "ior": yohen.GLASS_N}},
        ],
        "env": env,
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "lights": [
            {"name": "key", "loc": [-16.0, -36.0, 50.0], "target": tgt, "size": [30, 30], "watts": 13000, "rgb": [1.0, 0.97, 0.93], "hide_in_gloss": True},
        ],
        "bounces": 12,
        "glossy_bounces": 6,
        "diffuse_bounces": 2,
        "transmission_bounces": 8,
        "spp": {"preview": 96, "mid": 192, "final": 384},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.45, "contrast": 1.3, "saturation": 1.0, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "vignette": 0.22, "halation": 0.05})


main()
