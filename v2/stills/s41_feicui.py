"""Shot 41 (spare): an imperial-green jadeite cabochon (翡翠蛋面, 玻璃种帝王绿): the dome's crest is the arc.

    python3 -I v2/stills/s41_feicui.py [preview|mid|final]

First version followed s03 (chord along the line of sight in Emission Color): it read as neon CG, and its streaks as drawn hair. So this is a
real medium, changed from the brief: a closed dome (top + flat base) of a green, weakly scattering medium, light from under and behind. All
sigma are estimates. Structure, from general knowledge of jadeite (scales are estimates):
- 4.4 x 3.0 cm, 1.0 cm high;
- the structure is in real sheets at several depths inside the medium, so it has parallax and goes soft with depth:
  green gathers in soft clouds and in a fine felted mottle of interlocking crystals (0.3-1 mm, 翠性), roots of colour (色根) a little deeper in
  places; cotton (棉) sparse pale wisps;
- a hard glassy polish: one long highlight; a few hair scratches.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from glazekit import balls, close_shell
from kit import OUT, ROOT, blur, fbm, frame_camera, rank, shoot, sstep
from vessel import window

A_, C_, B_ = 2.2, 1.5, 1.0  # half length (x), half width (y), height (z), cm
ABC = np.array([A_, C_, B_])
W = 3.95
EL = np.radians(14.0)
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)])
UP = np.array([0.0, np.sin(EL), np.cos(EL)])
SHADER = os.path.join(ROOT, "v2", "stills", "glaze_shader.py")
STONE = {"kind": "glaze", "ior": 1.66, "g": 0.6, "sigma_s": [0.6, 0.6, 0.6], "sigma_a": [5.0, 0.42, 3.6]}


def warped_axis(n, center, a, span):
    w = np.linspace(-1, 1, n, dtype=np.float64)
    return center + a * w + (span - a) * w**7


def dome_dirs(nc, nr):
    lam = warped_axis(nc, 0.0, 1.0, np.pi / 2)
    psi = warped_axis(nr, np.radians(32.0), 0.95, np.pi / 2 + np.radians(32.0))  # polar angle from +z towards the viewer
    psi = np.clip(psi, -np.pi / 2, np.pi / 2)
    L, S = np.meshgrid(lam, psi)
    return np.stack([np.sin(L), -np.cos(L) * np.sin(S), np.cos(L) * np.cos(S)], -1).astype(np.float32)


def noise_on(shape, pxcm, lo, hi, beta, seed):
    return fbm(shape, pxcm, lo, hi, beta, seed)


def build(dens):
    nc, nr = int(3000 * dens), int(1900 * dens)
    d = dome_dirs(nc, nr)
    shape = d.shape[:2]
    pxcm = nc / (2 * A_)
    n = d / ABC
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    # the surface: a polished dome with a very slow undulation, hairlines
    h = 0.0015 * blur(cv2.resize(fbm((340, 520), 52.0, 2.0, 8.0, 3.4, 1), (nc, nr), interpolation=cv2.INTER_CUBIC), nr / 340 * 2.0)
    P = d * ABC + n * h[..., None]
    P[..., 2] = np.maximum(P[..., 2], 0.0)
    rough = 0.06 + 0.012 * rank(fbm(shape, pxcm, 0.02, 0.3, 2.2, 30))
    # the flat base
    m = 48
    idx = np.round(np.linspace(0, nr - 1, m)).astype(int)
    bot = P[idx].copy()
    bot[..., 2] = -0.004
    Pg, at = close_shell(P.astype(np.float32), bot, {"rough": rough.astype(np.float32)}, {"rough": 0.3}, outward=VIEW)

    # --- sheets inside: a smaller dome each, coarser (the medium softens them)
    ns, nl = nc // 2, nr // 2
    ds = dome_dirs(ns, nl)
    px2 = pxcm / 2
    sheets = {}
    cloud = cv2.resize(fbm((340, 520), 52.0, 0.25, 2.2, 2.8, 23), (ns, nl), interpolation=cv2.INTER_CUBIC)
    cloud = blur((cloud - cloud.mean()) / cloud.std(), nl / 340 * 1.5)
    # Felt came from milk in the sheets: they read as a diffuse skin. So the sheets only filter (soft clouds of colour at depth), and what comes back to
    # the eye comes from the medium and a pale reflecting base: thick at the centre (deep), thin at the edge (pale), which is what a cabochon does.
    for k, (frac, sd) in enumerate([(0.75, 201), (0.45, 203)]):
        Ps = ds * ABC * np.array([0.97, 0.97, frac])
        mott = fbm((nl, ns), px2, 0.05, 0.3, 2.4, sd)
        a = np.clip(0.5 + 0.75 * cloud + 0.3 * mott, 0, 1)
        T = np.stack([1.0 - 0.7 * a, 1.0 - 0.28 * a, 1.0 - 0.62 * a], -1).astype(np.float32)
        wisp = sstep(0.8, 0.98, rank(fbm((nl, ns), px2, 0.03, 0.2, 2.1, sd + 30)))
        milk = 0.05 * wisp
        mcol = np.broadcast_to(np.array([0.72, 0.92, 0.78], np.float32), (nl, ns, 3))
        sheets[f"s{k}"] = dict(P=Ps.astype(np.float32), tint=T, milk=milk.astype(np.float32), mcol=np.asarray(mcol))
    Pb = ds * ABC * np.array([0.985, 0.985, 0.03])
    sheets["base"] = dict(P=Pb.astype(np.float32), tint=np.ones((nl, ns, 3), np.float32), milk=np.full((nl, ns), 0.92, np.float32), mcol=np.broadcast_to(np.array([0.92, 0.98, 0.92], np.float32), (nl, ns, 3)).copy())
    return Pg, at["rough"], sheets


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    DRAFT = q == "draft"  # full size at few samples: to judge at 100% before spending a final
    q = "final" if DRAFT else q
    dens = {"preview": 0.4, "mid": 0.6, "final": 1.0}[q]
    Pg, Rg, sheets = build(dens)
    d = os.path.join(OUT, "s41_feicui")
    os.makedirs(d, exist_ok=True)
    fs = {}

    def save(name, **kw):
        fs[name] = os.path.join(d, f"mesh.{name}.{q}.npz")
        np.savez(fs[name], **kw)

    save("stone", P=Pg, rough=Rg)
    meshes = [{"name": "stone", "npz": fs["stone"], "shader_py": SHADER, "params": STONE}]
    for k, kw in sheets.items():
        save(k, **kw)
        meshes.append({"name": k, "npz": fs[k], "shader_py": SHADER, "params": {"kind": "layer"}})

    H_frame = W * 9.0 / 16.0
    # the silhouette at x = 0: the point of the ellipse furthest along the frame's up
    k_ = np.array([0.0, C_ * C_ * UP[1], B_ * B_ * UP[2]])
    k_ = k_ / np.sqrt(np.sum(k_**2 / ABC**2))
    target = k_ + UP * (0.46 - 0.5) * H_frame
    focus = np.array([0.0, k_[1] - 0.45, k_[2] - 0.03])
    cam = frame_camera(target, VIEW, W, 26.0, aperture_mm=1.2, focus_point=focus)

    pt = np.array([-0.25, -0.35, 0.0])
    pt[2] = B_ * np.sqrt(max(1 - (pt[0] / A_) ** 2 - (pt[1] / C_) ** 2, 0.01))
    nn = pt / ABC**2
    nn = nn / np.linalg.norm(nn)
    r = 2 * nn.dot(VIEW) * nn - VIEW
    scene = {
        "camera": cam,
        "meshes": meshes,
        "lights": window("win", pt + r * 46, pt, 13, 13, 2, 2, 0.4, 2200, rgb=[1.0, 0.98, 0.95]) + [
            {"name": "under", "loc": [1.0, 3.0, -7.0], "target": [0, 0, 0.2], "size": [9, 9], "watts": 16000, "rgb": [1.0, 0.98, 0.9], "hide_in_gloss": True},
            {"name": "back", "loc": [-4, 16, 9], "target": [0, 0.3, 0.4], "size": [10, 6], "watts": 9000, "rgb": [1.0, 0.98, 0.92], "hide_in_gloss": True},
        ],
        "bounces": 64,
        "volume_bounces": 64,
        "transmission_bounces": 64,
        "glossy_bounces": 4,
        "diffuse_bounces": 6,
        "spp": {"preview": 64, "mid": 128, "final": 384},
    }
    scene["spp"] = {"final": 40} if DRAFT else scene.get("spp", {})
    shoot("s41_feicui", scene, q, tag="draft" if DRAFT else None, develop={"exposure": 0.14, "contrast": 1.45, "saturation": 0.92, "black": 0.002, "grain": 1.2, "sharpen": 0.28, "halation": 0.05, "vignette": 0.22})


main()
