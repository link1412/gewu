"""Shot 5: cinnabar seal paste (朱砂印泥) heaped in a white porcelain box; the top of the heap is the arc.

    python3 -I v2/stills/s05_yinni.py [sketch|preview|mid|final]

Second version. The blind review of the first: "depth of field and the white porcelain rim look shot; the paste surface undulates at one frequency, like fractal noise, with no clumping of grains and no pressed marks".
So the surface is now the result of what happened to the paste, in order, on a height field in fixed cm (the same at every quality):
1. it is turned over with a bone spatula: a rounded blade sweeps a curved path, shaves what is above it, and pushes a raised burr to one side and a heap at its end. Later strokes cut earlier ones. The scraped ground is smooth, with drag lines along the stroke;
2. the crumbs: paste is tacky and clots. A few crumbs of a power-law size lie mostly in the burrs and the untouched ground, stuck on as lumps (each its own), hardly any in the scraped faces; a tack stipple on the ground, as a real surface shows;
3. a seal has been pressed into it: two square dents with a soft shoulder, slightly tilted; where the seal came away, the paste was pulled into small peaks (a tack stipple) which have fallen over in one direction;
4. moxa floss (艾绒), fibres 0.05-0.15 mm thick and several mm long, lies along the drag, shows in thin places and sticks out on the crumbs, a few bare strands stand off the crest;
5. oil: paste is wet (photos in refs_s12c/yinni, reference only, measure median sRGB about 173-187, 6-34, 9-40, speculars to 250): crimson, not orange, and glistening; the scraped faces are smoother and wetter than the ground. Roughness comes from the history, not a noise.
Colour: deeper in the pressed faces where the oil came up; no slow colour cloud.
All scales are estimates from general knowledge of seal paste, not measured.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, mix, rank, shoot, sstep
from vessel import Profile, fit_arc, patch, project, reflect_light_loc, turned, view_dir, window

NAME = "s05_yinni"
W = 7.4
RB = 4.45  # radius of the paste at the rim
H0 = 0.9  # height of the heap above the rim
AZ = -np.pi / 2
RIM = Profile([(5.05, -2.0), (5.05, -0.1), (5.0, 0.06), (4.82, 0.13), (4.6, 0.06), (4.52, -0.3), (4.45, -1.2)], sigma=0.035, ds=0.002)
# fixed grid for all large-scale form, so that every quality has the same composition
X0, X1, Y0, Y1 = -6.0, 6.0, -5.2, 5.2
NG = 1800


def dome(X, Y):
    r = np.sqrt(X**2 + Y**2)
    t = np.clip(r / RB, 0, 1.3)
    return H0 * (np.clip(1 - t**2, 0, 1) ** 0.72) - 3.0 * sstep(1.0, 1.04, t)


def history():
    """The surface's history, on the fixed grid. Returns height relative to the dome (cm), drag direction (radians), `face` (1 on scraped faces), `burr` (1 on burrs), `press` (1 in seal dents), pxcm."""
    rng = np.random.default_rng(511)
    pxcm = NG / (X1 - X0)
    ny, nx = int((Y1 - Y0) * pxcm), NG
    x = X0 + (np.arange(nx) + 0.5) / pxcm
    y = Y0 + (np.arange(ny) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)
    # the first form: slumped and lumpy, as it came out of the mixing: only a slow shape, with a heavier few lumps
    H = 0.05 * fbm((ny, nx), pxcm, 0.5, 3.5, 3.2, 512).astype(np.float32)
    phi = np.zeros((ny, nx), np.float32)
    face = np.zeros((ny, nx), np.float32)
    burr = np.zeros((ny, nx), np.float32)
    tear = fbm((ny, nx), pxcm, 0.02, 0.12, 1.5, 513)

    n_strokes = 24
    for i in range(n_strokes):
        # a stroke: curved path across the heap, blade width and depth its own; most go round the heap, as a hand does turning a box
        a0 = rng.uniform(0, 2 * np.pi)
        r0 = rng.uniform(0.5, 3.9)
        Lc = rng.lognormal(np.log(2.6), 0.4)
        curvature = rng.normal(0, 0.28)
        hd = a0 + np.pi / 2 * rng.choice([-1, 1]) + rng.normal(0, 0.5)
        n = 240
        t = np.linspace(0, 1, n)
        ang = hd + curvature * Lc * t
        px = r0 * np.cos(a0) + np.cumsum(np.cos(ang)) * Lc / n
        py = r0 * np.sin(a0) + np.cumsum(np.sin(ang)) * Lc / n
        bw = rng.uniform(0.32, 0.72)  # half width of the blade
        depth = rng.uniform(0.012, 0.042)
        # the region of this stroke
        mg = bw * 1.8
        ix0, ix1 = max(int((px.min() - mg - X0) * pxcm), 0), min(int((px.max() + mg - X0) * pxcm), nx)
        iy0, iy1 = max(int((py.min() - mg - Y0) * pxcm), 0), min(int((py.max() + mg - Y0) * pxcm), ny)
        if ix0 >= ix1 or iy0 >= iy1:
            continue
        Xs, Ys = X[iy0:iy1, ix0:ix1], Y[iy0:iy1, ix0:ix1]
        # nearest point on the path by brute force on a coarse stride, enough on this size
        dx = Xs[..., None] - px
        dy = Ys[..., None] - py
        d2 = dx * dx + dy * dy
        k = np.argmin(d2, axis=-1)
        d = np.sqrt(np.take_along_axis(d2, k[..., None], -1))[..., 0]
        s = k / (n - 1)
        side = np.sign(np.cos(ang[k]) * (Ys - py[k]) - np.sin(ang[k]) * (Xs - px[k]))
        # the blade: flat across with rounded corners, tilted in the hand so one side cuts deeper and the other leaves the burr
        along = sstep(0.0, 0.12, s) * sstep(1.0, 0.82, s)
        across = d / bw
        tilt = rng.uniform(0.2, 0.7) * rng.choice([-1, 1])
        lvl = H[iy0:iy1, ix0:ix1]
        # the blade surface sits at a level below the current local mean; it shaves what is above it
        ref = cv2.GaussianBlur(lvl, (0, 0), 0.25 * pxcm)
        blade = ref - depth * (1.0 + tilt * side * across)
        cover = sstep(1.0, 0.82, across + 0.03 * tear[iy0:iy1, ix0:ix1]) * along
        new = lvl + (np.minimum(lvl, blade) - lvl) * cover
        # what it removed goes to the burr on the proud side and to a heap at the end
        burr_prof = np.exp(-(((across - 1.04) / 0.17) ** 2)) * (side * np.sign(tilt) < 0) * sstep(0.04, 0.3, s) * sstep(1.0, 0.9, s)
        end_heap = np.exp(-(((s - 0.97) / 0.03) ** 2)) * sstep(1.25, 0.5, across)
        new = new + depth * (0.7 * burr_prof + 1.0 * end_heap) * (1.0 + 0.5 * tear[iy0:iy1, ix0:ix1])
        H[iy0:iy1, ix0:ix1] = new
        f = cover * (1.0 - 0.3 * end_heap)
        face[iy0:iy1, ix0:ix1] = np.maximum(face[iy0:iy1, ix0:ix1] * (1 - cover), f)
        burr[iy0:iy1, ix0:ix1] = np.maximum(burr[iy0:iy1, ix0:ix1] * (1 - cover), np.clip(burr_prof + end_heap, 0, 1))
        p_ = phi[iy0:iy1, ix0:ix1]
        phi[iy0:iy1, ix0:ix1] = p_ * (1 - cover) + ang[k].astype(np.float32) * cover
    # seals: a square face pressed in a few times. Locations chosen on the camera-side slope, not centred
    press = np.zeros((ny, nx), np.float32)
    for (cx, cy, sz, rot, dp) in ((-1.55, -1.75, 2.0, 0.22, 0.045), (1.8, -1.3, 1.45, -0.35, 0.032)):
        u = (X - cx) * np.cos(rot) + (Y - cy) * np.sin(rot)
        v = -(X - cx) * np.sin(rot) + (Y - cy) * np.cos(rot)
        q = np.maximum(np.abs(u), np.abs(v)) - sz / 2
        m = sstep(0.06, -0.03, q + 0.012 * tear)
        # a shoulder pushed up round the dent; a tilted press, one corner deeper
        H = H - dp * m * (1.0 + 0.35 * u / sz + 0.2 * v / sz) + 0.012 * np.exp(-((q / 0.05) ** 2)) * (q > -0.02)
        face = face * (1 - m)
        press = np.maximum(press, m)
    H = cv2.GaussianBlur(H, (0, 0), 2.2)
    face = cv2.GaussianBlur(face, (0, 0), 2.5)
    return H, phi, face, burr, press, pxcm


def fibres(shape, pxcm, x0, y0, phi, gpx, seed, per_cm2, count_layers=6):
    """Fibre height buffers: curved short polylines following the drag direction `phi` (on the fixed grid)."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    out = np.zeros(shape, np.float32)
    tops = np.zeros(shape, np.float32)
    gh, gw = phi.shape
    for lay in range(count_layers):
        n = int(area * per_cm2 / count_layers)
        px = rng.uniform(0, nx, n)
        py = rng.uniform(0, ny, n)
        lens = rng.lognormal(np.log(0.45), 0.6, n) * pxcm
        steps = 9
        pts = np.zeros((n, steps, 2), np.float32)
        pts[:, 0, 0], pts[:, 0, 1] = px, py
        curl = rng.normal(0, 0.5, n)
        jitter = rng.normal(0, 0.6, n)
        for s in range(1, steps):
            gx = np.clip(((pts[:, s - 1, 0] / pxcm + x0 - X0) * gpx).astype(int), 0, gw - 1)
            gy = np.clip(((pts[:, s - 1, 1] / pxcm + y0 - Y0) * gpx).astype(int), 0, gh - 1)
            ang = phi[gy, gx] + jitter + curl * s / steps + rng.normal(0, 0.1, n)
            pts[:, s, 0] = pts[:, s - 1, 0] + np.cos(ang) * lens / steps
            pts[:, s, 1] = pts[:, s - 1, 1] + np.sin(ang) * lens / steps
        layer = np.zeros(shape, np.float32)
        ipts = np.round(pts * 16).astype(np.int32)
        thick = rng.choice([1, 2, 3], n, p=[0.55, 0.3, 0.15])
        for t in (1, 2, 3):
            sel = np.nonzero(thick == t)[0]
            if sel.size:
                w = max(1, int(round(t * pxcm / 450.0 * 2.3)))
                cv2.polylines(layer, list(ipts[sel]), False, 1.0, w, cv2.LINE_AA, shift=4)
        layer = blur(layer, max(0.6, 0.0014 * pxcm))
        hl = layer * (0.6 + 0.4 * lay / count_layers)
        tops = np.where(hl > out, lay / count_layers, tops)
        out = np.maximum(out, hl)
    return out, tops


def crumbs(shape, pxcm, density, seed):
    """Discrete clots of paste, power-law sizes: each a lump (a flattened bump with a torn outline). density: a map of where they stick (0..1)."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    area = nx * ny / pxcm**2
    out = np.zeros(shape, np.float32)
    idm = np.zeros(shape, np.float32)
    # sizes in cm: radius; number per cm2 of each class
    for r0, r1, per_cm2 in ((0.05, 0.1, 0.9), (0.022, 0.05, 9.0), (0.009, 0.022, 70.0), (0.0035, 0.009, 450.0)):
        n = int(area * per_cm2)
        xs, ys = rng.integers(0, nx, n), rng.integers(0, ny, n)
        keep = rng.random(n) < density[ys, xs]
        xs, ys = xs[keep], ys[keep]
        rr = np.exp(rng.uniform(np.log(r0), np.log(r1), len(xs))) * pxcm
        if len(xs) == 0 or rr.mean() < 0.7:
            continue
        if rr.mean() > 3.0:  # large: drawn one by one, not round
            for x_, y_, r_ in zip(xs, ys, rr):
                R_ = int(r_ * 1.6) + 2
                y0_, y1_, x0_, x1_ = max(y_ - R_, 0), min(y_ + R_ + 1, ny), max(x_ - R_, 0), min(x_ + R_ + 1, nx)
                yy, xx = np.mgrid[y0_:y1_, x0_:x1_]
                a_ = np.arctan2(yy - y_, xx - x_)
                k = 1 + 0.35 * np.sin(2 * a_ + rng.uniform(0, 6)) + 0.2 * np.sin(3 * a_ + rng.uniform(0, 6)) + 0.1 * np.sin(5 * a_ + rng.uniform(0, 6))
                d_ = np.hypot(yy - y_, xx - x_) / (r_ * k)
                dome_ = np.sqrt(np.clip(1 - d_ * d_, 0, 1)) * r_ / pxcm * rng.uniform(0.35, 0.7)
                sub = out[y0_:y1_, x0_:x1_]
                on = dome_ > sub
                sub[on] = dome_[on]
                idm[y0_:y1_, x0_:x1_][on] = rng.random()
        else:  # small: stamped through a distance transform
            seeds = np.ones(shape, np.uint8)
            seeds[ys, xs] = 0
            d_ = cv2.distanceTransform(seeds, cv2.DIST_L2, 3)
            rm = float(rr.mean())
            dome_ = np.sqrt(np.clip(1 - (d_ / rm) ** 2, 0, 1)) * rm / pxcm * 0.55
            out = np.maximum(out, dome_.astype(np.float32))
    return out, idm


def build(dens, hist):
    pxcm = 520.0 * dens
    x0, x1, y0, y1 = -4.2, 4.2, -5.0, 1.1
    nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
    shape = (ny, nx)
    print("grid", nx, ny, nx * ny / 1e6, "M", flush=True)
    x = x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    # rows run -y (as they must, for the normals to be up on this heap)
    y = y1 - (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    X, Y = np.meshgrid(x, y)

    Hg, phi, faceg, burrg, pressg, gpx = hist
    mx = ((X - X0) * gpx).astype(np.float32)
    my = ((Y - Y0) * gpx).astype(np.float32)
    H = cv2.remap(Hg, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    face = cv2.remap(faceg, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    burr = cv2.remap(burrg, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    press = cv2.remap(pressg, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # phi on the fine grid, to run drag lines
    ph = cv2.remap(phi, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE)

    ground = np.clip(1.0 - face - press, 0, 1)  # the torn, untouched paste
    # drag lines on the faces: stretched noise along the stroke (coordinates by the stroke's own angle)
    drag = fbm((1024, 1024), 1.0, 1.5, 18.0, 1.5, 521)
    su = X * np.cos(ph) + Y * np.sin(ph)
    sv = -X * np.sin(ph) + Y * np.cos(ph)
    dl = cv2.remap(drag, np.mod(su * 40.0, 1023).astype(np.float32), np.mod(sv * 360.0, 1023).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

    fib, tops = fibres(shape, pxcm, x0, y0, phi, gpx, 21, 900)
    fib_show = 0.42 * face + 0.5 * press + 0.8 * ground
    # the crumbs live on ground and burrs
    density = 0.22 * np.clip(0.8 * ground + 0.8 * burr + 0.1 * face + 0.14 * press, 0, 1) * (0.5 + 0.5 * rank(fbm(shape, pxcm, 0.35, 2.0, 2.6, 522)))
    cr, cid = crumbs(shape, pxcm, density, 523)
    # a tack stipple in the seal dents: peaks pulled up and fallen to one side (positive height, skewed)
    stip_seed = fbm(shape, pxcm, 0.012, 0.05, 1.3, 524)
    st = np.clip(stip_seed - 0.4, 0, 2.5) * (press + 0.5 * ground)
    st = 0.65 * st + 0.35 * np.roll(st, int(0.014 * pxcm), axis=1)
    # torn ground: rough at the scale of paste threads, gone on faces
    torn = fbm(shape, pxcm, 0.006, 0.035, 1.4, 525)
    micro = fbm(shape, pxcm, 0.002, 0.008, 1.1, 526)
    h_detail = 0.021 * fib * fib_show + cr * 0.82 + 0.0052 * st + (0.0012 * ground + 0.0005 * press) * torn + 0.0022 * face * np.abs(dl) + 0.0005 * face * torn + 0.00018 * micro

    z = dome(X, Y) + H * sstep(RB + 0.1, RB - 0.6, np.hypot(X, Y)) + h_detail

    # --- colour: linear; from history
    cavity = blur(h_detail, 0.012 * pxcm) - h_detail
    cav = np.clip(cavity / 0.008, -1, 1)
    deep = color([0.2, 0.004, 0.006])
    red = color([0.56, 0.011, 0.014])
    bright = color([0.72, 0.028, 0.026])
    col = mix(red, deep, sstep(0.0, 0.9, cav))
    col = mix(col, bright, sstep(0.0, 0.8, -cav) * 0.7)
    # broken crumbs are dry and more orange; scraped and pressed faces have oil on them, deeper
    oil = np.clip(face * 0.75 + press * 0.8, 0, 1)
    col = mix(col, col * color([0.88, 0.8, 0.8]), oil)
    dry = sstep(0.003, 0.03, cr)
    col = mix(col, color([0.68, 0.034, 0.03]), dry * 0.4)
    # a few strands of floss hardly coated
    bare = (fib > 0.6) * (tops > 0.82) * sstep(0.6, 0.97, rank(fbm(shape, pxcm, 0.05, 0.3, 1.5, 27))) * sstep(0.2, 1.0, ground)
    col = mix(col, color([0.8, 0.08, 0.06]), blur(bare.astype(np.float32), 0.7) * 0.7)
    rough = 0.32 * ground + 0.22 * face + 0.27 * press + 0.1 * dry - 0.04 * sstep(0.2, 1.0, fib) * ground + 0.03 * dl * face
    P = np.stack([X, Y, z], -1).astype(np.float32)
    return P, np.clip(col, 0, 1).astype(np.float32), np.clip(rough, 0.08, 1).astype(np.float32)


def build_rim(box, dens):
    u0, u1, v0, v1 = box
    pxcm = 300.0 * dens
    nx, ny = int((u1 - u0) * pxcm), int((v1 - v0) * pxcm)
    print("rim", nx, ny)
    u = u0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm
    v = v0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm
    U, V = np.meshgrid(u, v)
    shape = U.shape
    h = 0.0012 * fbm(shape, pxcm, 0.3, 2.0, 3.4, 31) + 0.0003 * fbm(shape, pxcm, 0.05, 0.2, 2.4, 32)
    # a stain of paste on the lip, and a tiny chip
    st = rank(fbm(shape, pxcm, 0.05, 0.8, 2.8, 33))
    r_, z_, _, _ = RIM.at(V)
    stain = sstep(0.55, 0.8, st) * sstep(4.6, 4.53, r_)
    P = turned(RIM, U, V, h, az=AZ)
    wob = 0.012 * fbm(shape, pxcm, 0.8, 5.0, 3.0, 34)
    def line(z0, w):
        return sstep(w, w * 0.6, np.abs(z_ + wob - z0))
    bleed = 0.75 + 0.25 * rank(fbm(shape, pxcm, 0.02, 0.2, 2.0, 35))
    blue = np.maximum(line(-0.13, 0.04), line(-0.27, 0.016)) * bleed * sstep(4.95, 5.03, r_)
    white = mix(color([0.86, 0.90, 0.88]), color([0.92, 0.94, 0.91]), rank(fbm(shape, pxcm, 0.2, 2.0, 2.4, 36)))
    col = mix(white, color([0.02, 0.05, 0.27]), blue)
    col = mix(col, color([0.62, 0.05, 0.03]), stain * 0.8)
    rough = 0.09 + 0.2 * stain
    return P, np.clip(col, 0, 1).astype(np.float32), np.full(shape, 0, np.float32) + rough.astype(np.float32)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "preview"
    dens = {"sketch": 0.32, "preview": 0.42, "mid": 0.65, "final": 1.0}[q]
    d = os.path.join(OUT, NAME)
    os.makedirs(d, exist_ok=True)

    # framing on the coarse form, with the strokes
    hist = history()
    Hg, _, _, _, _, gpx = hist
    Yg, Xg = np.mgrid[0 : Hg.shape[0], 0 : Hg.shape[1]].astype(np.float32)
    Xc, Yc = X0 + Xg / gpx, Y0 + Yg / gpx
    Zc = dome(Xc, Yc) + Hg * sstep(RB + 0.1, RB - 0.6, np.hypot(Xc, Yc))
    Pc = np.stack([Xc, Yc, Zc], -1)[::4, ::4]
    view = view_dir(-90.0, 7.0)
    # focus on the crest of the heap, near the camera side of the silhouette
    focus = np.array([0.2, -1.9, float(H0) - 0.2])  # mid-paste: sharp from the crest to the middle, only the porcelain lip goes a little soft
    cam, sag = fit_arc(Pc, view, W, 40.0, aperture_mm=2.9, focus_point=focus)

    P, C, Ro = build(dens, hist)
    npz = os.path.join(d, f"mesh.{q}.npz")
    np.savez(npz, P=P, col=C, rough=Ro)
    box = patch(RIM, cam, (-9, 9), (0.0, RIM.L), az=AZ)
    print("rim box", box)
    Pr, Cr, Rr = build_rim(box, dens)
    npz2 = os.path.join(d, f"rim.{q}.npz")
    np.savez(npz2, P=Pr, col=Cr, rough=Rr)

    # the lights: a window mirrored off the crest (from behind the heap), a low hard side light that rakes the relief
    pt = np.array([0.0, -1.6, 0.85])
    nrm = np.array([0.0, -0.32, 0.95])
    lw, r = reflect_light_loc(pt, nrm, cam, 42.0)
    lw = lw + np.array([-8.0, 0.0, 0.0])
    print("window", lw)
    lights = window("win", lw, pt, 22, 26, 2, 2, 1.0, 170, rgb=[1.0, 0.97, 0.92])
    lights += [
        # low behind the heap, seen only as a reflection: the mirror direction from a camera at 7 degrees over a nearly flat wet surface
        {"type": "gradient", "name": "sheen", "loc": [-6, 62, 15], "target": [0, -1, 0.8], "size": [130, 44], "sigma": [36, 7], "L": 2.3, "rgb": [1.0, 0.97, 0.93], "hide_in_diffuse": True},
        {"name": "rake", "loc": [-34, 6, 9], "target": [0, -1, 0.7], "size": [9, 5], "watts": 15000, "rgb": [1.0, 0.92, 0.82]},
        {"name": "fill", "loc": [20, -30, 12], "target": [0, -1, 0.7], "size": [30, 30], "watts": 2000, "rgb": [1.0, 0.86, 0.82], "hide_in_gloss": True},
        {"name": "low", "loc": [-6, -40, -5], "target": [0, -4.9, -0.8], "size": [24, 6], "watts": 7000, "rgb": [1.0, 0.98, 0.95], "hide_in_gloss": True},
        {"name": "strip", "loc": [0, -44, 2], "target": [0, -4.9, -0.2], "size": [160, 3], "watts": 7000, "rgb": [1.0, 0.98, 0.95]},
    ]
    material = {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.5, "Subsurface Weight": 0.25, "Subsurface Radius": [1.0, 0.12, 0.08], "Subsurface Scale": 0.04, "Sheen Weight": 0.03, "Sheen Roughness": 0.3}
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "paste", "npz": npz, "material": material},
            {"name": "rim", "npz": npz2, "material": {"Base Color": "col", "Roughness": "rough", "Specular IOR Level": 0.55}},
        ],
        "lights": lights,
        "world": [0.0008, 0.0006, 0.0006],
        "diffuse_bounces": 3,
        "glossy_bounces": 3,
        "spp": {"preview": 64, "mid": 128, "final": 320},
    }
    # the film reads final.*: a candidate goes to cand.* and is renamed only after it has passed a look at 100%
    shoot(NAME, scene, "preview" if q == "sketch" else q, develop={"exposure": 0.0, "contrast": 1.35, "saturation": 1.04, "black": 0.002, "grain": 1.2, "sharpen": 0.28, "halation": 0.03, "glare": 0.002}, tag="cand" if q == "final" else q)


main()
