"""Shot 23: cloisonné (景泰蓝) as a macro: nothing but a few gilt wires and the worn enamel between them, on the dome of a small round box. Low raking light. No flower and no dish: s49_falang is the whole piece, this is the craft.

    python3 -I v2/stills/s23_jingtailan.py flat            the fields: out/v2/s23_jingtailan/cand_flat.jpg
    python3 -I v2/stills/s23_jingtailan.py [preview|mid]
    python3 -I v2/stills/s23_jingtailan.py cand            final size, tag cand; never writes final.*

The surface follows the Ming enamels in ref/cloisonne (Cleveland 1987.58, 100% crops: a sandy, opaque turquoise, full of pits with black dirt in them, flat wire tops that are thin and break here and there) and not the clean later shop work.
Scales are estimates from those photographs and general knowledge, not measured: wire about 0.3-0.4 mm across on top, standing a hair above the enamel after polishing; the wire is laid in lengths, so there are butt joints, not all of them true; a hand's wobble in every bend;
each cell fired on its own, so its level and its sheen differ a little; the enamel sinks beside the wire (a meniscus, which is what catches the raking light); polish scratches run one way across both enamel and gilt, and the gilt is rubbed through to copper on the high spots.
Height field on a sphere, Principled surfaces. A box of 2.2 cm radius is our choice, not a measured object.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
import yohen
from kit import OUT, blur, caps, fbm, frame_camera, rank, shoot, sstep
from vessel import fit_arc, reflect_light_loc, view_dir

R = 2.2
W = 1.6
DIST = 13.0
EL = 21.0
APEX = (0.5, 0.46)
APERTURE = 4.2  # mm
BOX = (-1.6, 1.6, -1.8, 1.05)  # x0, x1, y0, y1 in the plane above the dome, cm; the camera looks along +y
MOVE = {"truck": [0.022, 0.0], "frames": 13, "shutter": 0.5}  # a slow slide along the arc, one way, 2.2% of the frame width in all
ARC_C = np.array([0.18, -3.05])  # the wires' common centre, far below the frame, so they sweep across it as arcs that echo the horizon


def srgb(r, g, b):
    c = np.array([r, g, b], np.float32) / 255.0
    return np.where(c < 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def wobble(t, rng, amp, lam):
    """Hand: slow wander, a few short corrections."""
    n = len(t)
    f = np.zeros(n)
    for k in range(3):
        L = lam / 2**k
        ph = rng.uniform(0, 6.28)
        f += amp / 3.0**k * np.sin(t / L * 6.28 + ph + 0.8 * np.sin(t / (L * 2.3) + ph))
    return f


def wires(rng):
    """Lengths of wire as (xy, half width). The band of two parallel wires, a third apart, tendrils that leave an arc and curl: drawn after the Ming scrolls, none copied."""
    out = []
    radii = [2.34, 2.46, 2.86, 3.24, 3.72]  # at x = ARC_C, down to up in the frame
    for ri, r0 in enumerate(radii):
        a = np.pi / 2 - 1.1 + rng.uniform(-0.04, 0.04)
        end = np.pi / 2 + 1.1
        shift = 0.0
        while a < end:
            L = rng.uniform(0.9, 1.9)  # one length of wire, cm
            da = L / r0
            t = np.arange(0, L, 0.008)
            aa = a + t / r0
            rr = r0 + wobble(t + 11 * ri + a, rng, 0.010, 1.1) + shift
            xy = np.stack([ARC_C[0] + rr * np.cos(aa), ARC_C[1] + rr * np.sin(aa)], 1)
            out.append((xy, rng.uniform(0.0105, 0.0155)))
            a += da + rng.uniform(0.0, 0.006)  # a butt joint, seldom closed
            shift += rng.normal(0, 0.0045)  # and not quite in line
    # tendrils: leave the inner arc tangentially, tighten into a curl
    for (a0, sign, size, ri) in ((1.80, 1, 1.25, 3), (1.42, -1, 1.1, 2), (1.25, -1, 1.0, 3), (1.86, 1, 0.8, 2)):
        r0 = radii[ri]
        p = ARC_C + r0 * np.array([np.cos(a0), np.sin(a0)])
        d = np.array([-np.sin(a0), np.cos(a0)]) * -sign
        ang = np.arctan2(d[1], d[0])
        s = np.arange(0, size, 0.005)
        # the bend tightens along the length, about one and a half turns in all, so a scroll never crosses itself: a clothoid-like curl, as a hand bends it
        th = ang + sign * 2 * np.pi * rng.uniform(1.25, 1.6) * (s / size) ** 2.6
        P = p + np.cumsum(np.stack([np.cos(th), np.sin(th)], 1) * 0.005, 0)
        P = P + np.stack([wobble(s, rng, 0.002, 0.5), wobble(s + 5, rng, 0.002, 0.5)], 1)
        out.append((P, rng.uniform(0.0095, 0.0125)))
    return out


def fields(dens):
    x0, x1, y0, y1 = BOX
    pxcm = 1500.0 * dens
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, round(nx * ny / 1e6, 1), "M")
    x = x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    y = y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)

    rng = np.random.default_rng(31)
    WS = wires(rng)
    SH = 4
    k = pxcm * (1 << SH)
    center = np.zeros(shape, np.uint8)
    hw_img = np.zeros(shape, np.float32)
    wid = np.zeros(shape, np.float32)
    for xy, hw in WS:
        P = np.round((xy - [x0, y0]) * k).astype(np.int32)
        cv2.polylines(center, [P.reshape(-1, 1, 2)], False, 255, 1, cv2.LINE_8, SH)
        cv2.polylines(wid, [P.reshape(-1, 1, 2)], False, float(hw), max(int(0.08 * pxcm), 3), cv2.LINE_8, SH)
    wid = np.where(wid > 0, wid, 0.016)
    dist = cv2.distanceTransform(255 - center, cv2.DIST_L2, 5) / pxcm
    # a thick and thin of hand-drawn wire; the wire narrows where it was polished down
    hw = wid * (1 + 0.05 * fbm(shape, pxcm, 0.12, 0.6, 2.6, 42)) * (0.88 + 0.24 * rank(fbm(shape, pxcm, 0.3, 1.4, 2.6, 142)))
    e_ = dist / hw
    # a slightly torn outline: enamel creeps a little over the edge
    e_ = e_ * (1 + 0.02 * fbm(shape, pxcm, 0.012, 0.05, 2.2, 143))
    wire = sstep(1.04, 0.92, e_)

    # --- cells
    n_cells, lab = cv2.connectedComponents((wire < 0.5).astype(np.uint8), connectivity=4)
    print("cells", n_cells)
    r_rng = np.random.default_rng(43)
    lv = r_rng.normal(0, 1, n_cells).astype(np.float32)
    sheen = r_rng.uniform(-1, 1, n_cells).astype(np.float32)
    # the narrow band between the two inner arcs is cobalt; all else the ground
    rad = np.hypot(X - ARC_C[0], Y - ARC_C[1])
    cnt = np.bincount(lab.ravel(), minlength=n_cells).astype(np.float64)
    mid_cob = (rad > 2.37) & (rad < 2.43)
    fc = np.bincount(lab[mid_cob].ravel(), minlength=n_cells) / np.maximum(cnt, 1)
    cobalt = fc > 0.25
    level = lv[lab]
    d_in = cv2.distanceTransform((wire < 0.5).astype(np.uint8), cv2.DIST_L2, 5) / pxcm

    # --- pits: a steep size law, in drifts. Wide ones are open craters with dirt
    drift = rank(fbm(shape, pxcm, 0.12, 0.9, 2.6, 44))
    # most are specks, a few are bigger and never round: a pit is where bubbles met and the polish opened them. Thresholded noise for the irregular ones, a steep law of small caps for the specks
    blob = rank(fbm(shape, pxcm, 0.014, 0.05, 2.6, 45)) + 0.1 * (drift - 0.5)
    open_ = cv2.GaussianBlur((blob > 0.982).astype(np.float32), (0, 0), 0.0025 * pxcm)
    dt_ = cv2.distanceTransform((open_ > 0.5).astype(np.uint8), cv2.DIST_L2, 3) / pxcm
    specks = caps(shape, pxcm, 150, 0.0012, 0.011, 145, slope=-3.0, mask=(drift > 0.3).astype(np.float32))
    pits = np.maximum(np.minimum(dt_ * 1.1, 0.02), specks)
    pit_m = sstep(0.0, 0.0012, pits)
    # sugary chips: the polish tore a grain out here and there. Slight: they only lift the sheen
    chips = sstep(0.93, 0.99, rank(fbm(shape, pxcm, 0.01, 0.04, 1.8, 46))) * sstep(0.6, 0.9, drift) * sstep(0.01, 0.03, d_in)

    # --- polish scratches, one way (diagonal), very long against their width: noise on rotated axes, stretched
    ang = np.radians(17.0)
    sU = np.cos(ang) * X + np.sin(ang) * Y
    sV = -np.sin(ang) * X + np.cos(ang) * Y
    sg = fbm((384, 3072), 300.0, 0.003, 0.05, 1.3, 47)
    mapu = ((sU * 30.0) % 384).astype(np.float32)  # along: stretched 10:1
    mapv = ((sV * 300.0) % 3072).astype(np.float32)
    scr = cv2.remap(sg, mapv, mapu, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    scr_r = rank(scr)

    # --- height
    wave = fbm(shape, pxcm, 0.1, 0.7, 2.8, 48)
    enamel_top = -0.0018 - 0.0011 * level - 0.0042 * np.exp(-d_in / 0.016) + 0.00028 * wave + 0.00006 * scr + 0.0001 * fbm(shape, pxcm, 0.006, 0.03, 1.6, 49)
    enamel = enamel_top - 1.2 * np.minimum(pits, 0.02) - 0.0016 * chips
    wire_top = 0.0007 + 0.0009 * np.sqrt(np.maximum(1 - np.minimum(e_, 1) ** 2, 0)) + 0.00004 * scr + 0.00018 * fbm(shape, pxcm, 0.02, 0.2, 2.0, 50)
    h = enamel * (1 - wire) + wire_top * wire
    h = h + 0.0012 * fbm(shape, pxcm, 0.6, 3.0, 3.2, 51)

    # --- colour, opaque: read off the Cleveland crops by eye. A sugary turquoise, pale where the powder lay thick, greener in the deep
    powder = rank(fbm(shape, pxcm, 0.008, 0.035, 1.4, 52))
    cloud = rank(fbm(shape, pxcm, 0.1, 0.9, 2.5, 53))
    lo, hi = srgb(16, 122, 158), srgb(62, 186, 208)
    t = np.clip(0.55 * cloud + 0.45 * powder, 0, 1)[..., None]
    pal = lo + (hi - lo) * t
    pal = pal + (srgb(150, 222, 226) - pal) * (sstep(0.72, 0.96, 0.5 * powder + 0.5 * cloud) * 0.6)[..., None]
    for mask, a, b in ((cobalt[lab], srgb(12, 22, 96), srgb(36, 52, 164)),):
        pal[mask] = (a + (b - a) * t[mask])
    pal = pal * (0.96 + 0.04 * level[..., None])
    pal = pal * (1 - 0.32 * np.exp(-d_in / 0.012))[..., None]  # dark gathers against the wire: old grime and the thin edge of the fill
    pal = pal + (srgb(190, 225, 225) - pal) * (0.28 * chips)[..., None]
    dirt = srgb(30, 24, 20)
    pal = pal + (dirt - pal) * (pit_m * (0.55 + 0.45 * rank(fbm(shape, pxcm, 0.003, 0.016, 1.5, 54))))[..., None]

    # the gilt, rubbed to copper where it stood highest
    wear = sstep(0.62, 0.9, 0.7 * rank(fbm(shape, pxcm, 0.03, 0.28, 2.2, 55)) + 0.3 * scr_r)
    gold, copper = srgb(247, 197, 100), srgb(214, 128, 86)
    gilt = gold + (copper - gold) * wear[..., None]
    # grime on the wire's shoulders: gold is dark at its edge, where the polish did not go
    gilt = gilt * (0.52 + 0.48 * sstep(1.0, 0.72, e_))[..., None]
    col = pal * (1 - wire[..., None]) + gilt * wire[..., None]

    rough_e = 0.15 + 0.035 * sheen[lab] + 0.03 * scr_r + 0.2 * pit_m + 0.14 * chips + 0.05 * (1 - np.exp(-(powder - 0.5) ** 2 * 8))
    rough_w = 0.2 + 0.09 * scr_r + 0.05 * wear
    rough = rough_e * (1 - wire) + rough_w * wire
    return dict(shape=shape, pxcm=pxcm, X=X, Y=Y, h=h.astype(np.float32), col=np.clip(col, 0, 1).astype(np.float32), rough=np.clip(rough, 0.05, 1).astype(np.float32), metal=wire.astype(np.float32))


def sphere(X, Y, h=0.0):
    r2 = X * X + Y * Y
    z = np.sqrt(np.maximum(R * R - r2, 0.01))
    n = np.stack([X, Y, z], -1) / np.sqrt(r2 + z * z)[..., None]
    return np.stack([X, Y, z], -1) + n * np.asarray(h)[..., None] if np.ndim(h) else np.stack([X, Y, z], -1)


def flat(F, d):
    g = np.gradient(F["h"], 1.0 / F["pxcm"])
    shade = np.clip(1.0 + 7.0 * g[1] + 3.0 * g[0], 0.3, 2.0)
    img = np.clip(F["col"] * shade[..., None], 0, 1) ** (1 / 2.2)
    img = img[::-1]  # y up
    H = img.shape[0]
    x0 = int(0.25 * img.shape[1])
    crop = img[int(0.05 * H) : int(0.75 * H), x0 : x0 + int(0.5 * img.shape[1])]
    s = 1800.0 / crop.shape[1]
    out = cv2.resize(crop, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(d, "cand_flat.jpg"), (out[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])


def main():
    # looks.json still holds the old shot's sky, env and move, and it has the last word in kit._dress: for this new shot its entry should go. Until the main line does that, say so here
    kit.looks = lambda: {"s23_jingtailan": {"move": MOVE}}
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    d = os.path.join(OUT, "s23_jingtailan")
    os.makedirs(d, exist_ok=True)
    if q == "flat":
        return flat(fields(0.5), d)
    tag = q
    if q == "cand":
        q = "final"
    dens = {"preview": 0.45, "mid": 0.7, "final": 1.0}[q]
    # the arc: the dome's silhouette, seen low
    view = view_dir(-90.0, EL)
    xx, yy = np.meshgrid(np.linspace(-2.0, 2.0, 300), np.linspace(-2.0, 1.25, 300))
    Pc = sphere(xx.astype(np.float32), yy.astype(np.float32)).reshape(-1, 3)
    v_ = np.array(view, float)
    n = Pc / R
    Pc = Pc[(n @ v_) > -0.02]
    focus = sphere(np.array([0.0], np.float32), np.array([-0.15], np.float32))[0]
    cam, sag = fit_arc(Pc, view, W, DIST, apex=APEX, target0=(0, 0, R), aperture_mm=APERTURE, focus_point=focus)

    F = fields(dens)
    P = sphere(F["X"], F["Y"], F["h"]).astype(np.float32)
    # the grid runs +x, +y seen from above; check the normal comes out upwards
    a, b = P[1, 1] - P[0, 1], P[1, 1] - P[1, 0]
    if np.cross(a, b)[2] < 0:
        P = P[::-1].copy()
        for k_ in ("col", "rough", "metal"):
            F[k_] = F[k_][::-1].copy()
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=F["col"], rough=F["rough"], metal=F["metal"])

    # raking key low from the left, hard enough to throw the meniscus into relief; a long window along the arc, mirrored in the wire tops and the far enamel
    nrm = focus / R
    pw = sphere(np.array([0.0], np.float32), np.array([-0.32], np.float32))[0]
    _, rdir = reflect_light_loc(pw, pw / R, cam, 60.0)
    print("window dir", rdir)
    yohen.use_room()
    env = {
        "base": [0.022, 0.022, 0.024],
        "panels": [
            {"dir": rdir.tolist(), "w": 46, "h": 4.5, "L": 3.2, "rgb": [1.0, 0.975, 0.93], "soft": 1.0, "soft_w": 10.0, "bars": 5, "bar_w": 0.7, "grad": 0.2},
            # the lit back wall and ceiling of the room: this is all the gilt has to mirror, from about 20 to 80 degrees up on the far side
            {"dir": [0.0, 0.64, 0.77], "w": 70, "h": 34, "L": 0.36, "rgb": [1.0, 0.97, 0.92], "soft": 14.0, "soft_w": 24.0, "grad": -0.35},
        ],
    }
    lights = [
        {"name": "rake", "loc": (focus + np.array([-24.0, 4.0, 5.5])).tolist(), "target": focus.tolist(), "size": [5.0, 3.0], "watts": 2600, "rgb": [1.0, 0.95, 0.87]},
        {"name": "fill", "loc": (focus + np.array([18.0, -26.0, 26.0])).tolist(), "target": focus.tolist(), "size": [34, 34], "watts": 15000, "rgb": [0.96, 0.98, 1.0], "hide_in_gloss": True},
    ]
    scene = {
        "camera": cam,
        "meshes": [{"name": "dome", "npz": npz, "material": {"Base Color": "col", "Roughness": "rough", "Metallic": "metal", "Specular IOR Level": 0.55}}],
        "lights": lights,
        "env": env,
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    shoot("s23_jingtailan", scene, q, tag=tag, develop={"exposure": 0.25, "contrast": 1.3, "saturation": 1.0, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "vignette": 0.2})


main()
