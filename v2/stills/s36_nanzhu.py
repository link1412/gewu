"""Shot 36: a South Sea pearl from Hepu (合浦南珠): the sphere's edge is the arc. Grey-black room, a window, slow.

    python3 -I v2/stills/s36_nanzhu.py sketch      numpy only, seconds: out/v2/s36_nanzhu/sketch.jpg (composition, the window, the orient)
    python3 -I v2/stills/s36_nanzhu.py lut         the stack's reflectance table and a chart of it, out/v2/s36_nanzhu/stack_chart.jpg
    python3 -I v2/stills/s36_nanzhu.py [preview|mid|final]        The final's tag is cand; never writes final.*
    python3 -I v2/stills/s36_nanzhu.py motion      all frames, small: s36_nanzhu_cand_move_preview/
    GEWU_MOVE=final python3 -I v2/stills/s36_nanzhu.py final      all frames, 1080p: s36_nanzhu_cand_move_final/ (the shot's own s36_nanzhu_move_final is left alone)

What a pearl's lustre is, and how each part is made here:
- a sharp mirror from the outermost layer: Fresnel, n = 1.6. It carries the window's edges. Coat lobe in pearl_shader.py. n: aragonite is 1.53 and 1.68 along its axes, from memory of mineral tables, not looked up today. 1.6 is a compromise, an ESTIMATE.
- a soft glow round it from the stack below: many tablets each slightly tilted, so the window is seen spread out. The tilt spread is an ESTIMATE by eye, against ref/pearl (the GIA pearl and the nacre at 3.68 mm field).
- overtone colours: interference in the stack, computed: transfer matrix over a stack of aragonite tablets and organic films (stack_lut), reflectance by wavelength, angle and thickness, turned into linear RGB with an analytic fit to the CIE curves (Wyman, Sloan, Shirley 2013, formula from memory, not checked against the paper).
  Inputs, all from general knowledge, not measured: tablet n 1.68, film n 1.50, film 25 nm, 60 periods, thickness spread 7%; tablet thickness 300-420 nm (Akoya-like, I recall 0.3-0.5 um quoted; not looked up).
  What is computed and what is chosen: the table is computed. CHROMA, the gain that mixes the table with white, is chosen by eye: a real pearl shows far less colour than an ideal coherent stack because of tablet edges and disorder, and I did not model that.
- where the colour sits: the red lobe is widest and the blue narrowest. Stand-in for diffraction by the tablet edges, whose angle goes with wavelength (the idea that edges diffract is from memory of the pearl literature, not looked up today); the widths' ratio is that of wavelengths, 620:540:460, their size chosen by eye.
  So the tint gathers round the edge of a highlight and vanishes in the plain body, without any painted patch. It moves with the light: there is no colour in the albedo.
- the body: silvery white, a milky solid (Subsurface), no gloss of its own. Colour and radii are ESTIMATES by eye against pearl_gia_pearl_large_01.
- surface (second round, with growth lines): out-of-round 40 um; a slow unevenness that bends the window's edges; growth lines in patches, three directions, about 40 um apart (measured on ref/pearl/pearl_gia_pearl_necklace_02: peak period 19-25 um in four patches, 3.68 mm field across 636 px, near the JPEG's limit; ours is made coarser so that it survives 1080p at 6.4 um a pixel. It is the only thing here deliberately coarser than the reference); a faint ring of grooves; five small dimples and hairlines. All in the normal, none painted, so a window's edge is broken by them and the break travels with them. A very faint trace in the colour (LINE_C), so the lines can be seen where no window lies. Heights are ESTIMATES by eye for how far the reflection moves.
- the light: a window in the room (window_env), written here in numpy, reflections only plus the body's diffuse: no lamp in the scene. Its shape and brightness are ESTIMATES by eye. Its panes are not a photograph.
Not done: real layered transport (the lobes are added); a scattering volume inside the coat; polarisation.

The move: the camera and the room do not move, so the window stays where it is. The pearl turns on an axis leaning away from the camera, one direction, even: its surface passes under the window from left to right, about 2.8 pixels a frame at 1080p, less than half the period of the lines so that they do not alias. Two extra frames are rendered and dropped so that the first and last kept frames have whole motion blur.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

import kit
from kit import OUT, _cam_axes, blur, fbm, frame_camera, rank, shoot, sstep

NAME = "s36_nanzhu"
TAKE = "s36_nanzhu_cand"
R = 0.72
W = 0.93
DIST = 13.0
EL = 8.0
APEX_Y = 0.50
LU, V0, V1 = 1.95, -0.13, 1.06
VIEW = np.array([0.0, -np.cos(np.radians(EL)), np.sin(np.radians(EL))])
UP = np.array([0.0, np.sin(np.radians(EL)), np.cos(np.radians(EL))])
CENTRE = np.array([0.0, 0.0, -R])

# the orient
ROUGH = {"coat": 0.035, "r": 0.30, "g": 0.262, "b": 0.222, "milk": 0.60}  # Cycles squares roughness: alpha 0.09, 0.069, 0.049, milk 0.36
ORIENT = 0.18
MILK = 0.05
CHROMA = 0.7
BODY = np.array([0.76, 0.755, 0.74])
D0, D1 = 300.0, 420.0
BODY_W = 9000.0
OOR, WAVE = 0.0012, 0.00007
LINE, LINE_H, LINE_C, LINE_G, RING_H = 0.004, 0.0000078, 0.04, 0.16, 0.00004  # cm: period, height; trace in colour and in the stack's reflection (fractions; the reference's lines are 6-8% std in its lit parts, measured); groove depth
DMEAN, DSWING = 352.0, 26.0  # nm; the thickness field's centre and half range: picked from the chart, from rose through to green
FRAMES, TURN = 36, 0.11  # kept frames, degrees a frame



def D(u, v):
    a = u / R
    b = v / R - np.radians(EL)
    return np.stack([np.sin(a), -np.cos(a) * np.sin(b), np.cos(a) * np.cos(b)], -1)


def coarse(shape, cm_per, lo, hi, beta, seed):
    g = (int((V1 - V0) / cm_per), int(LU / cm_per))
    f = fbm(g, 1.0 / cm_per, lo, hi, beta, seed)
    f = cv2.resize(f, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return blur(f, max(shape[1] / g[1], 1.0))


# --- the stack: transfer matrix, by wavelength, angle and tablet thickness
def _cie(lam):
    def g(x, m, s1, s2):
        t = (x - m) * np.where(x < m, s1, s2)
        return np.exp(-0.5 * t * t)

    X = 1.056 * g(lam, 599.8, 0.0264, 0.0323) + 0.362 * g(lam, 442.0, 0.0624, 0.0374) - 0.065 * g(lam, 501.1, 0.049, 0.0382)
    Y = 0.821 * g(lam, 568.8, 0.0213, 0.0247) + 0.286 * g(lam, 530.9, 0.0613, 0.0322)
    Z = 1.217 * g(lam, 437.0, 0.0845, 0.0278) + 0.681 * g(lam, 459.0, 0.0385, 0.0725)
    return np.stack([X, Y, Z], -1)


XYZ2RGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.204, 1.057]])


def stack_reflect(lam, cos0, dm, n1=1.68, n2=1.50, d2=25.0, N=60, spread=0.07, reals=6, seed=361):
    """Mean reflectance (s and p) of a disordered stack, inside a tablet to start with: lam (L,), cos0 the cosine in that first medium. Layers differ from each other; an average over realisations stands in for an incoherent patch."""
    rng = np.random.default_rng(seed)
    sin1 = np.sqrt(np.maximum(1 - cos0**2, 0))
    cos2 = np.sqrt(np.maximum(1 - (n1 * sin1 / n2) ** 2, 1e-4))
    out = np.zeros(lam.shape)
    for _ in range(reals):
        d1s = dm * (1 + spread * rng.normal(size=N))
        d2s = d2 * (1 + 0.2 * rng.normal(size=N))
        for pol in ("s", "p"):
            e1, e2 = (n1 * cos0, n2 * cos2) if pol == "s" else (n1 / cos0, n2 / cos2)
            M = np.tile(np.eye(2, dtype=complex), (len(lam), 1, 1))
            for j in range(N):
                for n_, c_, d_, e_ in ((n1, cos0, d1s[j], e1), (n2, cos2, d2s[j], e2)):
                    ph = 2 * np.pi * n_ * d_ * c_ / lam
                    m = np.zeros((len(lam), 2, 2), complex)
                    m[:, 0, 0] = m[:, 1, 1] = np.cos(ph)
                    m[:, 0, 1] = 1j * np.sin(ph) / e_
                    m[:, 1, 0] = 1j * e_ * np.sin(ph)
                    M = M @ m
            B = M[:, 0, 0] + M[:, 0, 1] * e1
            C = M[:, 1, 0] + M[:, 1, 1] * e1
            r = (e1 * B - C) / (e1 * B + C)
            out += np.abs(r) ** 2
    return out / (2 * reals)


def stack_lut(path):
    """x: cos of the angle in air, 0..1 (32); y: tablet thickness D0..D1 (32). Value: linear RGB of the stack's reflection of white, normalised to luminance 1, then mixed towards white by CHROMA. Refracted into the tablet first."""
    raw = path.replace(".npy", ".raw.npy")
    if os.path.exists(raw):
        T = np.load(raw)
        np.save(path, 1.0 + CHROMA * (T - 1.0))
        return np.load(path)
    lam = np.arange(400.0, 701.0, 10.0)
    cmf = _cie(lam)
    ncos, nd = 24, 32
    T = np.zeros((nd, ncos, 3), np.float32)
    for j, dm in enumerate(np.linspace(D0, D1, nd)):
        for i, c in enumerate(np.linspace(0.0, 1.0, ncos)):
            s = np.sqrt(1 - c * c)
            c1 = np.sqrt(1 - (s / 1.68) ** 2)
            Rl = stack_reflect(lam, c1, dm)
            xyz = (Rl[:, None] * cmf).sum(0) / cmf[:, 1].sum()
            rgb = XYZ2RGB @ xyz
            T[j, i] = np.maximum(rgb, 0) / max(xyz[1], 1e-5)
    np.save(raw, T)
    T = 1.0 + CHROMA * (T - 1.0)
    np.save(path, T)
    return T


def chart():
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    T = stack_lut(os.path.join(d, "stack_lut.npy"))
    im = cv2.resize(T[::-1], (640, 640), interpolation=cv2.INTER_NEAREST)
    im = np.clip(im * 0.7, 0, 1) ** (1 / 2.2)
    p = os.path.join(d, "stack_chart.jpg")
    cv2.imwrite(p, (im[..., ::-1] * 255).astype(np.uint8))
    print(p, "x cos 0..1, y thickness", D1, "(top) to", D0, flush=True)


# --- the room, in the camera's frame. A function of direction, so that the sketch and the render read the same thing
WIN_AT = (0.36, 0.71)  # where in the frame the window's reflection is centred
WIN = {"w": 0.29, "h": 0.215, "L": 6.5, "tilt": -8.0}  # half-sizes as tangents
STRIP = {"at": (0.86, 0.76), "w": 0.05, "h": 0.5, "L": 0.45}
for _k in ("ORIENT", "MILK", "CHROMA", "BODY_W", "LINE_H", "LINE_C", "LINE_G", "RING_H", "WAVE"):  # batches of trials: S36_ORIENT=.. on the command line
    if os.environ.get("S36_" + _k):
        globals()[_k] = float(os.environ["S36_" + _k])
for _k in ("w", "h", "L"):
    if os.environ.get("S36_WIN_" + _k):
        WIN[_k] = float(os.environ["S36_WIN_" + _k])


def at_frame(fx, fy):
    """The room's direction, in (right, up, back), that the ball mirrors at this place in the frame."""
    cam = camera()
    rt, ut, bk = _cam_axes(cam)
    loc, tgt = np.array(cam["loc"]), np.array(cam["target"])
    ray = tgt + (fx - 0.5) * W * rt + (0.5 - fy) * W * 9.0 / 16.0 * ut - loc
    ray /= np.linalg.norm(ray)
    oc = loc - CENTRE
    b_ = ray @ oc
    n = (loc + ray * (-b_ - np.sqrt(b_**2 - (oc @ oc - R * R))) - CENTRE) / R
    r = ray - 2 * (ray @ n) * n
    return np.array([r @ rt, r @ ut, r @ bk])


def _panel(d, cen, w, h, tilt, soft):
    """Gnomonic coordinates on a panel at direction cen, with edges softened by `soft` of the half-size. Returns x, y, mask."""
    c = cen / np.linalg.norm(cen)
    up0 = np.array([0.0, 1.0, 0.0]) if abs(c[1]) < 0.95 else np.array([0.0, 0.0, 1.0])
    e1 = np.cross(up0, c)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(c, e1)
    t = np.radians(tilt)
    e1, e2 = e1 * np.cos(t) + e2 * np.sin(t), -e1 * np.sin(t) + e2 * np.cos(t)
    dc = d @ c
    fw = dc > 0.05
    x = np.where(fw, (d @ e1) / np.maximum(dc, 0.05), 99.0) / w
    y = np.where(fw, (d @ e2) / np.maximum(dc, 0.05), 99.0) / h
    return x, y, sstep(1.0, 1.0 - soft, np.abs(x)) * sstep(1.0, 1.0 - soft, np.abs(y))


def room(d):
    """d: (..., 3) unit directions in (right, up, back). Returns radiance (..., 3)."""
    el = np.arcsin(np.clip(d[..., 1], -1, 1))
    wall = 0.022 + 0.05 * sstep(-0.1, 1.2, el)  # a dim room, a little lighter above
    # a floor that catches light near the window's side
    E = wall[..., None] * np.array([1.0, 0.99, 0.97])
    # the window, overcast sky behind panes: brighter at the top of the sky, a mullion cross and glazing bars. Slightly soft.
    x, y, m = _panel(d, at_frame(*WIN_AT), WIN["w"], WIN["h"], WIN["tilt"], 0.012)
    bars = sstep(0.035, 0.05, np.abs(x + 0.04)) * sstep(0.05, 0.07, np.abs(y - 0.2))
    grad = 0.72 + 0.42 * (y * 0.5 + 0.5) - 0.1 * x
    E = E + (WIN["L"] * m * bars * grad)[..., None] * np.array([0.97, 0.985, 1.03])
    # the wall round the window takes light from it: a gentle halo in the room itself
    halo = np.exp(-(np.maximum(np.abs(x) - 1, 0) ** 2 + np.maximum(np.abs(y) - 1, 0) ** 2) / 0.8)
    E = E + (0.13 * halo)[..., None] * np.array([1.0, 0.98, 0.95])
    # a long dim warm strip on the other side, its reflection a thin line along the shoulder: it draws the shape in the dark half
    x2, y2, m2 = _panel(d, at_frame(*STRIP["at"]), STRIP["w"], STRIP["h"], 14.0, 0.25)
    E = E + (STRIP["L"] * m2)[..., None] * np.array([1.04, 0.98, 0.9])
    return E.astype(np.float32)


def window_env(path, cam):
    h, w = 1024, 2048
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    dw = np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)  # as kit.room_env: Blender's equirect, row 0 up
    r, u, b = [np.array(v, np.float32) for v in _cam_axes(cam)]
    E = room(np.stack([dw @ r, dw @ u, dw @ b], -1))
    np.save(path, E)
    return path


# --- the skin
def _dir_field(d, pole, warp, period):
    """Fine lines round a pole: phase is the distance along the surface from the pole, so the spacing holds wherever the lines are in the frame; a slow warp makes them wander and meet."""
    g = np.arccos(np.clip(d @ (pole / np.linalg.norm(pole)).astype(np.float32), -1, 1)) * R
    ph = (g + warp) / period
    # steps are not evenly spaced: a second, longer period beats against the first, so some lines crowd and some stand apart
    return np.sin(2 * np.pi * ph) * (0.72 + 0.28 * np.sin(2 * np.pi * ph / 3.7 + 0.6)) + 0.3 * np.sin(4 * np.pi * ph + 1.0)


def fields(dens):
    """Coarse shape goes in the mesh (h); everything finer than about half a mm goes in the normal (hf), since float32 positions cannot hold ten nanometres."""
    pxcm = 2100.0 * dens
    nx, ny = int(LU * pxcm), int((V1 - V0) * pxcm)
    shape = (ny, nx)
    u = (np.arange(nx, dtype=np.float32) + 0.5) / pxcm - LU / 2
    v = (np.arange(ny, dtype=np.float32) + 0.5) / pxcm + V0
    U, V = np.meshgrid(u, v)
    d = D(U, V).astype(np.float32)
    # out of round, slowly: never a CAD sphere, a good pearl all the same
    h = OOR * coarse(shape, 0.004, 0.6, 1.6, 3.4, 361)
    # a slow unevenness of the nacre: invisible as relief, but it bends a window's edges
    h = h + WAVE * coarse(shape, 0.002, 0.05, 0.28, 2.8, 374)
    # growth lines, in three fields round three poles, each in its own patches: nothing is level sets of noise, which reads as a contour map. Period from ref/pearl's nacre photograph, measured
    w1 = 0.1 * coarse(shape, 0.002, 0.4, 1.3, 2.8, 362) + 0.002 * coarse(shape, 0.001, 0.04, 0.16, 2.2, 363)
    w2 = 0.1 * coarse(shape, 0.002, 0.4, 1.3, 2.8, 377) + 0.002 * coarse(shape, 0.001, 0.04, 0.16, 2.2, 378)
    w3 = 0.1 * coarse(shape, 0.002, 0.4, 1.3, 2.8, 379) + 0.002 * coarse(shape, 0.001, 0.04, 0.16, 2.2, 380)
    l1 = _dir_field(d, np.array([0.5, -0.5, 0.3]), w1, LINE)
    l2 = _dir_field(d, np.array([-0.8, -0.2, -0.3]), w2, LINE * 1.25)
    l3 = _dir_field(d, np.array([0.1, 0.9, -0.5]), w3, LINE * 0.85)
    m = coarse(shape, 0.003, 0.08, 0.5, 2.8, 364)
    n_ = coarse(shape, 0.003, 0.08, 0.5, 2.8, 381)
    m1, m2 = sstep(0.05, 0.25, m), sstep(0.05, 0.25, n_)
    lines = l1 * m1 * (1 - m2) + l2 * (1 - m1) * (1 - m2) + l3 * m2
    # strength: strong in patches, gone in others, broken up along the way
    amp = sstep(0.3, 0.8, rank(coarse(shape, 0.003, 0.06, 0.4, 2.6, 382))) * (0.55 + 0.45 * sstep(0.3, 0.7, rank(coarse(shape, 0.001, 0.01, 0.06, 2.2, 383))))
    amp = 0.2 + 0.8 * amp
    hf = LINE_H * lines * amp
    # a little waviness at the scale of half a mm, on all the surface
    hf = hf + 0.000006 * coarse(shape, 0.001, 0.012, 0.06, 2.4, 376)
    # a satin grain, finest
    hf = hf + 0.0000012 * fbm(shape, pxcm, 0.0012, 0.008, 1.6, 365)
    # a ring: a few grooves round an axis that is not the turning axis, wandering, deeper here and shallower there. Circled pearls have them; this is a faint one, a good pearl
    ax = np.array([-0.46, -0.55, 0.70], np.float32)
    ax = ax / np.linalg.norm(ax)
    ring_g = (np.arccos(np.clip(d @ ax, -1, 1)) - np.radians(54.0)) * R + 0.012 * coarse(shape, 0.002, 0.1, 0.5, 2.8, 368)
    gate = sstep(0.2, 0.65, rank(coarse(shape, 0.003, 0.1, 0.5, 2.8, 369)))
    groove = np.zeros(shape, np.float32)
    for off, dp, wd in ((0.0, 1.0, 0.0028), (0.009, 0.45, 0.002), (-0.012, 0.3, 0.0022), (0.024, 0.2, 0.002)):
        groove += dp * np.exp(-(((ring_g - off) / wd) ** 2))
    hf = hf - RING_H * groove * gate
    # small flaws: dimples and one blister, in the ways a good pearl has them, a few and shallow
    for cu, cv_, rr, depth in [(-0.28, 0.40, 0.0035, 0.00016), (0.18, 0.21, 0.0025, 0.00012), (0.33, 0.48, 0.0030, -0.00010), (-0.1, 0.27, 0.002, 0.00010), (-0.46, 0.55, 0.0028, 0.00012)]:
        hf = hf - depth * np.exp(-((np.hypot(U - cu, V - cv_) / rr) ** 2))
    # hairlines from a lifetime in a pouch: straight, faint, in a few directions, few
    sr = np.random.default_rng(375)
    hair = np.zeros(shape, np.uint8)
    for _ in range(26):
        x0, y0 = sr.uniform(0, nx), sr.uniform(0, ny)
        a_ = sr.choice([0.5, 2.1, 2.9]) + sr.normal(0, 0.2)
        L_ = sr.lognormal(np.log(0.03), 0.7) * pxcm
        cv2.line(hair, (int(x0 * 8), int(y0 * 8)), (int((x0 + np.cos(a_) * L_) * 8), int((y0 + np.sin(a_) * L_) * 8)), int(sr.uniform(60, 200)), 1, cv2.LINE_AA, 3)
    hair_f = blur(hair.astype(np.float32) / 255.0, max(0.6, 0.9 * dens))
    hf = hf - 0.000006 * hair_f
    # tablet thickness: slow, with one larger drift, so the tint is rose in one region and green in another; the lines leave a trace in it too
    film = DMEAN + DSWING * np.clip(0.9 * coarse(shape, 0.004, 0.25, 1.2, 2.6, 370), -1.4, 1.4) + 2.5 * lines * amp
    # how well the tablets line up: the glow is tighter here, wider there; so a highlight's glow is uneven, and the lines show in it
    tight = coarse(shape, 0.003, 0.05, 0.35, 2.6, 373)
    return U, V, h, hf, film, tight, hair_f, lines * amp, groove * gate


def build(dens):
    U, V, h, hf, film, tight, hair_f, lines, groove = fields(dens)
    print("grid", U.shape[1], U.shape[0], round(U.size / 1e6, 1), "M", flush=True)
    pxcm = 2100.0 * dens
    a = U / R
    b = V / R - np.radians(EL)
    d = D(U, V)
    P = CENTRE.astype(np.float32) + d * (R + h)[..., None]
    # the normal from hf: slopes along the surface. Tangents are at the rest pose; the shader takes them from object to world, so they turn with the pearl
    gy, gx = np.gradient(hf, 1.0 / pxcm)
    tu = np.stack([np.cos(a), np.sin(a) * np.sin(b), -np.sin(a) * np.cos(b)], -1)
    tv = np.stack([np.zeros_like(a), -np.cos(b), -np.sin(b)], -1)
    gy = gy / np.maximum(np.cos(a), 0.15)
    T = -(gx[..., None] * tu + gy[..., None] * tv)
    print("slope rms", round(float(np.sqrt((gx**2 + gy**2).mean())), 5), "p99.9", round(float(np.percentile(np.hypot(gx, gy), 99.9)), 4), flush=True)
    t1 = coarse(U.shape, 0.005, 0.2, 1.2, 3.0, 371)
    col = np.ones(U.shape + (3,), np.float32) * BODY.astype(np.float32) * (1 + 0.012 * t1 + LINE_C * lines - 0.03 * groove)[..., None]
    w = np.clip(1.0 + 0.16 * tight + 0.07 * lines, 0.7, 1.35)
    A = dict(col=np.clip(col, 0, 1).astype(np.float32), film=film.astype(np.float32), crough=np.clip(ROUGH["coat"] + 0.05 * hair_f + 0.02 * groove, 0, 1).astype(np.float32), tx=T[..., 0].astype(np.float32), ty=T[..., 1].astype(np.float32), tz=T[..., 2].astype(np.float32))
    for k, n in (("r", "rr"), ("g", "rg"), ("b", "rb")):
        A[n] = (ROUGH[k] * w).astype(np.float32)
    A["rmilk"] = np.full(U.shape, ROUGH["milk"], np.float32)
    A["og"] = np.clip(1.0 + LINE_G * lines - 0.25 * groove, 0.4, 1.5).astype(np.float32)
    return P.astype(np.float32), A


def camera():
    H_frame = W * 9.0 / 16.0
    apex = np.array([0.0, R * np.sin(np.radians(EL)), R * np.cos(np.radians(EL)) - R])
    target = apex + UP * (APEX_Y - 0.5) * H_frame
    # the reflection's image lies behind the surface by R/2 at most; the focus goes a little behind the surface in the window's reflection
    focus = CENTRE + D(np.array([-0.2]), np.array([0.34]))[0] * (R - 0.13)
    return frame_camera(target, VIEW, W, DIST, aperture_mm=0.55, focus_point=focus)


# --- the sketch: numpy, per pixel, Monte Carlo over tilted tablets. Same room, same lobes, same fields. The body is only a stand-in for the Subsurface
def sketch():
    t = __import__("time").time()
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)
    T = stack_lut(os.path.join(d, "stack_lut.npy"))
    w, h = 800, 450
    cam = camera()
    rt, ut, bk = _cam_axes(cam)
    loc = np.array(cam["loc"])
    tgt = np.array(cam["target"])
    dist = np.linalg.norm(loc - tgt)
    px = (np.arange(w) + 0.5) / w - 0.5
    py = 0.5 - (np.arange(h) + 0.5) / h
    X, Y = np.meshgrid(px * W, py * W * 9.0 / 16.0)
    ray = (tgt + X[..., None] * rt + Y[..., None] * ut) - loc
    ray /= np.linalg.norm(ray, axis=-1, keepdims=True)
    oc = loc - CENTRE
    b_ = ray @ oc
    disc = b_**2 - (oc @ oc - R * R)
    hit = disc > 0
    tt = -b_ - np.sqrt(np.maximum(disc, 0))
    P = loc + ray * tt[..., None]
    n0 = (P - CENTRE) / R
    # the surface's fields, sampled at the pixel
    U, V, hh, _, film, tight, *_ = fields(0.3)
    pxcm = 2100.0 * 0.3
    a = np.arcsin(np.clip(n0[..., 0], -1, 1))
    bb = np.arctan2(-n0[..., 1], n0[..., 2])
    mu = ((a * R + LU / 2) * pxcm - 0.5).astype(np.float32)
    mv = (((bb + np.radians(EL)) * R - V0) * pxcm - 0.5).astype(np.float32)
    gy, gx = np.gradient(hh * pxcm)
    sx = cv2.remap(gx, mu, mv, cv2.INTER_LINEAR)
    sy = cv2.remap(gy, mu, mv, cv2.INTER_LINEAR)
    fm = cv2.remap(film, mu, mv, cv2.INTER_LINEAR)
    # normals in world: tangent along u and v
    eps = 1e-3
    du = (D(np.array([eps]), np.array([0.3]))[0] - D(np.array([-eps]), np.array([0.3]))[0])
    tu = np.stack([np.cos(a), np.sin(a) * np.sin(bb), -np.sin(a) * np.cos(bb)], -1)
    tv = np.stack([np.zeros_like(a), -np.cos(a) * 0 - np.cos(bb), -np.sin(bb)], -1)
    n = n0 - sx[..., None] * tu - sy[..., None] * tv
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    cosv = np.clip(-(ray * n).sum(-1), 0, 1)
    # to the camera's frame
    B = np.stack([rt, ut, bk])
    rng = np.random.default_rng(5)
    S = 48

    def lobe(alpha):
        """Mean of the room over tilted normals (a gaussian of width alpha stands in for GGX; a GGX has longer tails, so the render's glow reaches further)."""
        acc = np.zeros((h, w, 3), np.float32)
        for _ in range(S):
            j = rng.normal(0, alpha, (h, w, 3))
            m = n + j
            m /= np.linalg.norm(m, axis=-1, keepdims=True)
            r_ = ray - 2 * (ray * m).sum(-1, keepdims=True) * m
            acc += room(r_ @ B.T)
        return acc / S

    r_sharp = ray - 2 * (ray * n).sum(-1, keepdims=True) * n
    F0 = ((1.6 - 1) / (1.6 + 1)) ** 2
    F = F0 + (1 - F0) * (1 - cosv) ** 5
    L = F[..., None] * room(r_sharp @ B.T)
    # the table
    iy = np.clip((fm - D0) / (D1 - D0) * (T.shape[0] - 1), 0, T.shape[0] - 1).astype(np.float32)
    ix = (cosv * (T.shape[1] - 1)).astype(np.float32)
    tint = cv2.remap(T, ix, iy, cv2.INTER_LINEAR)
    for c, k in enumerate("rgb"):
        L[..., c] += ORIENT * tint[..., c] * lobe(ROUGH[k] ** 2)[..., c]
    L += MILK * lobe(ROUGH["milk"] ** 2)
    # the body: a wrapped key from the window, stand-in
    lw = at_frame(*WIN_AT) @ B
    wrap = np.clip((n @ lw + 0.35) / 1.35, 0, 1) ** 1.3
    L += (0.30 * wrap + 0.02)[..., None] * BODY.astype(np.float32)
    bg = np.full((h, w, 3), 0.012, np.float32)
    L = np.where(hit[..., None], L, bg)
    from darkroom import develop as dev

    im = dev(L, **{**DEV, "grain": 0.0})
    p = os.path.join(d, "sketch.jpg")
    cv2.imwrite(p, (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 94])
    print(p, round(__import__("time").time() - t, 1), "s; apex y", round(np.nonzero(hit.any(1))[0][0] / h, 3), flush=True)


DEV = {"exposure": 0.0, "contrast": 1.2, "saturation": 1.08, "black": 0.002, "grain": 1.0, "sharpen": 0.2, "halation": 0.05, "vignette": 0.22}
# the axis: in the plane of the view and up, perpendicular to the middle of what is seen (a normal about 55 degrees above the view), so what is seen slides sideways instead of swirling
AXIS = np.cos(np.radians(55.0)) * UP - np.sin(np.radians(55.0)) * VIEW
MOVE = {"spin": {"pt": CENTRE.tolist(), "axis": AXIS.tolist(), "deg": TURN * (FRAMES + 1), "meshes": ["pearl"]}, "frames": FRAMES + 2, "shutter": 0.5, "spp": 256}


def _small_take(name, cfg, lk, move, develop, q):
    """All frames, small, so that the motion can be judged. As s66's."""
    mv = lk["move"]
    path = kit.camera_path(cfg["camera"], cfg.get("lights", []), mv, mv["frames"])
    d = os.path.join(OUT, f"{name}_move_preview")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    cfg.update(res=[640, 360], frames=path, fetch_to=d, shutter=mv.get("shutter", 0.5), spin=mv["spin"], spp=48)
    kit._render_local(cfg, os.path.join(OUT, name), "take")  # small frames
    from darkroom import develop as dev

    for i, f in enumerate(sorted(x for x in os.listdir(d) if x.endswith(".npy"))):
        im = dev(np.load(os.path.join(d, f)).astype(np.float32), **{**develop, "seed": 700 + i})
        cv2.imwrite(os.path.join(d, f"f{i:03d}.png"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(d, "f%03d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(d, "take.mp4")], check=True)
    print(os.path.join(d, "take.mp4"), flush=True)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if q == "sketch":
        return sketch()
    if q == "lut":
        return chart()
    orig = kit.looks
    kit.looks = lambda: {**orig(), TAKE: {"move": MOVE}}
    name = NAME
    if q == "motion":
        kit._take = _small_take
        os.environ["GEWU_MOVE"] = "preview"
        q = "preview"
    if os.environ.get("GEWU_MOVE"):
        name = TAKE  # never the shot's own s36_nanzhu_move_final, which the film reads
    dens = {"preview": 0.45, "mid": 0.6, "final": 1.0}[q]
    P, A = build(dens)
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"mesh.{q}{os.environ.get('S36_TAG', '')}.npz")
    np.savez(npz, P=P, **A)
    lut = os.path.join(d, f"stack_lut{os.environ.get('S36_TAG', '')}.npy")
    stack_lut(lut)
    here = os.path.dirname(os.path.abspath(__file__))
    cam = camera()
    env = window_env(os.path.join(d, f"env{os.environ.get('S36_TAG', '')}.npy"), cam)
    scene = {
        "camera": cam,
        "meshes": [
            {
                "name": "pearl",
                "npz": npz,
                "shader_py": os.path.join(here, "pearl_shader.py"),
                "params": {"lut": lut, "fine_normal": True, "d0": D0, "d1": D1, "ior": 1.6, "orient": ORIENT, "milk": MILK, "radius": [0.09, 0.075, 0.06]},
                "send_params": ["lut"],
            }
        ],
        "lights": [{"name": "body", "loc": [-26.0, 6.0, 24.0], "target": CENTRE.tolist(), "size": [26, 26], "watts": BODY_W, "rgb": [1.0, 0.97, 0.93], "hide_in_gloss": True}],  # the room's light on the milky body, from up and behind on the left: the side towards the camera falls off, so the ball has a dark side
        "env": {"npy": env, "diffuse": True},
        "sky": {"top": [0.0065, 0.0065, 0.0065], "glow": [0.017, 0.017, 0.017], "h": 0.62, "mottle": 0.12},
        "diffuse_bounces": 4,
        "glossy_bounces": 3,
        "denoise": os.environ.get("S36_DENOISE", "1") == "1",
        "spp": {"preview": 96, "mid": 192, "final": 384},
    }
    shoot(name, scene, q, tag=os.environ.get("S36_TAG") or ("cand" if q == "final" else None), develop=DEV)


main()
