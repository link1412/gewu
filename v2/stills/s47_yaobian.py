"""Yohen tenmoku (曜变天目), a whole tea bowl from above, standing on linen: its far lip the arc, most of the inside deep black, the spots and their colour only in places.

Rebuilt on the glaze of yohen.py, the same as s02 (real thin-film interference on a satin oxide lobe, a glass skin above with a real gap, bubbles in it), see there for what is measured and what is estimated.
Bowl about 12.2 cm across (museum record); section estimated. Table: linen with a painted contact shadow (kit.table_mesh, a stand-in) plus the real shadow of the bowl's inside mesh.
The room replaces kit.room_env.

    python3 -I v2/stills/s47_yaobian.py [preview|mid|final]
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
HERE = os.path.dirname(os.path.abspath(__file__))
W, EL, DIST = 15.0, 46.0, 72.0
PROFILE = [(2.2, 0.0), (2.4, 0.5), (3.6, 1.7), (5.0, 3.6), (5.85, 5.2), (6.12, 6.05), (6.1, 6.22), (5.92, 6.2), (5.7, 5.85), (5.56, 5.45), (5.25, 4.75), (4.3, 3.35), (3.1, 2.05), (2.0, 1.2), (1.1, 0.8), (0.0, 0.7)]



def crop(dish, X, Y, extra=0.5):
    ok = np.hypot(X, Y) < dish.rho_lip + extra
    r, c = np.nonzero(ok.any(1))[0], np.nonzero(ok.any(0))[0]
    return X[r[0] : r[-1] + 1, c[0] : c[-1] + 1], Y[r[0] : r[-1] + 1, c[0] : c[-1] + 1]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    dish = Dish(PROFILE, ds=0.0005)
    cam, sag = dish.camera(W, EL, DIST, apex=(0.5, 0.44), aperture_mm=14.0, focus_rho=dish.rho_lip - 1.2)
    print("sag", round(float(sag), 3), flush=True)
    pxcm = 240.0 * dens
    X, Y = crop(dish, *dish.grid(cam, pxcm, margin=0.07))
    print("grid", X.shape, round(X.size / 1e6, 1), "M", flush=True)
    rl = dish.rho_lip
    vivid = {"spacing": 0.62, "pond": (0.48, 0.94), "hue": 8.0, "flash": 2.5, "satin": 0.26, "crust": 0.5, "silver": True, "tint": 0.35, "island": 0.28, "fade": 1.75, "ramp": [174, 163, 158, 155.5, 154.5, 154, 153.5], "hair": 3.0, "ring": (0.07, 0.02), "spot_var": 1.1, "rim": (0.3, 0.1)}
    f = yohen.paint(dish, X, Y, pxcm, SEED, n_cl=520, rho0=1.0, rho1=rl - 0.3, r_big=(0.06, 0.15), pack=0.85, blue=1.0, hatch_w=0.011, metal_frac=0.8, vivid=vivid)
    npz_u = os.path.join(d, f"under.{q}.npz")
    np.savez(npz_u, **yohen.front(P=dish.surface(X, Y, f["h"]), col=f["col"], rough=f["rough"], film=f["film"], cov=f["cov"]))
    Xs, Ys = X[::2, ::2], Y[::2, ::2]
    hs, rs, on = yohen.shell_fields(dish, Xs, Ys, pxcm / 2, SEED, wave=0.0016, rings=0.0009, scratches=0.5)
    npz_s = os.path.join(d, f"shell.{q}.npz")
    np.savez(npz_s, **yohen.front(P=dish.surface(Xs, Ys, hs), rough=rs, on=on))
    npz_b = os.path.join(d, f"bubbles.{q}.npz")
    np.savez(npz_b, **yohen.front(P=yohen.bubbles(dish, X, Y, SEED, per_cm2=10.0)))

    npz_r = os.path.join(d, f"rest.{q}.npz")
    Pr, Cr = yohen.rest_of_bowl(dish)
    np.savez(npz_r, **yohen.front(P=Pr, col=Cr))

    # the room: a low north window on the left for the table and a skylight's single lamp: the shot's character is quiet. Lamps: fx, fy of the frame point that mirrors them
    yohen.use_room()
    panels = yohen.lamp_field(dish, cam, SEED, sep=16.0, L=(1400.0, 2800.0), size=(0.3, 0.17))
    # the glass itself: a dim overcast sky, so the far wall reads as a surface and not a hole. Its reflection is a slow fall of grey across the black
    rg, _, _ = yohen.reflection_at(dish, cam, 0.34, 0.5)
    panels.append({"dir": rg.tolist(), "w": 34, "h": 12, "L": 0.55, "rgb": [0.95, 0.97, 1.0], "soft": 9, "grad": 0.4})
    env = {"diffuse": True, "base": [0.02, 0.02, 0.022], "panels": panels}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "under", "npz": npz_u, "shader_py": os.path.join(HERE, "yohen_shader.py"), "params": {"kind": "under", "film_ior": yohen.FILM_N, "ior": yohen.GLASS_N, "bare_spec": 0.08, "metal": 1.0}},
            {"name": "shell", "npz": npz_s, "shader_py": os.path.join(HERE, "yohen_shader.py"), "params": {"kind": "shell", "ior": yohen.GLASS_N}},
            {"name": "bubbles", "npz": npz_b, "shader_py": os.path.join(HERE, "glaze_shader.py"), "params": {"kind": "bubble", "ior": yohen.GLASS_N}},
            {"name": "rest", "npz": npz_r, "material": {"Base Color": "col", "Roughness": 0.16, "IOR": yohen.GLASS_N}},
        ],
        "env": env,
        "table": {"z": 0.0, "kind": "linen", "rgb": [0.02, 0.019, 0.017], "thread": 0.05, "angle": 7, "seed": 47},
        "lights": [
            {"name": "north", "loc": [-70.0, -10.0, 60.0], "target": [0, 4, 3], "size": [50, 70], "watts": 30000, "rgb": [0.97, 0.98, 1.0], "hide_in_gloss": True},
            {"name": "lip", "loc": [10.0, 40.0, 30.0], "target": [0, 6, 6], "size": [60, 6], "watts": 4000, "rgb": [1.0, 0.95, 0.88], "hide_in_gloss": True},
        ],
        "bounces": 12,
        "glossy_bounces": 6,
        "diffuse_bounces": 2,
        "spp": {"preview": 96, "mid": 192, "final": 320},
    }
    shoot(NAME, scene, q, develop={"exposure": 0.45, "contrast": 1.25, "saturation": 1.0, "black": 0.001, "grain": 1.2, "sharpen": 0.25, "halation": 0.05, "vignette": 0.22})


main()
