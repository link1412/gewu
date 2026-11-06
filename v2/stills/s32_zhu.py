"""Shot 32: a transverse section of bamboo culm under a bright-field microscope, safranin and fast green. The field stop is the arc.

    python3 -I v2/stills/s32_zhu.py [preview|mid|final]

No Blender: a transmission micrograph is an absorption image, so it is computed directly (Beer-Lambert through the stained
walls), then blurred by the focal plane, and the darkroom takes it from there. Structure (from general plant anatomy of
Bambusoideae; sizes are estimates, drawn in pixels of the final image, roughly 0.35 um/px):
- ground parenchyma: thin-walled cells of very unequal size, walls in fast green, cells really separate (Voronoi on a
  dart-thrown point set, not a grid), rounded corners; some hold starch grains;
- vascular bundles, the "skull": two big metaxylem vessels (eyes), a torn protoxylem lacuna below them (mouth),
  phloem of small thin-walled cells above (brow), all in a sheath of fibres: thick walls in safranin, pin-point lumina, lamellae;
- what a real slide has: uneven staining, a shallow knife-chatter, section thickness (out-of-focus walls beneath), a focal plane
  tilted across the field, longitudinal colour, a field stop with a coloured edge.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from scipy.spatial import cKDTree

from darkroom import develop, save_png
from kit import OUT, blur, color, fbm, sstep

FW, FH = 2560, 1440
RF = 2060.0  # radius of the field stop (final px)
CX, CY = 1270.0, 0.475 * FH + RF

# (x, y, scale, rotation in degrees): the "up" of the skull faces the outside of the culm, up in the picture
BUNDLES = [
    (1250, 1210, 1.5, -3),
    (190, 1450, 1.15, -16),
    (2360, 1430, 1.2, 13),
    (640, 890, 0.5, -9),
    (1885, 900, 0.52, 10),
]


def local(x, y, b):
    a = np.radians(b[3])
    dx, dy = (x - b[0]) / b[2], (y - b[1]) / b[2]
    return dx * np.cos(a) + dy * np.sin(a), -dx * np.sin(a) + dy * np.cos(a)


def ell(u, v, cx, cy, rx, ry):
    return ((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2


def warp_noise(rng):
    return rng.normal(0, 1)


def tissue_at(x, y, nx, ny):
    """Class of the point: 0 parenchyma, 1 fibre, 2 phloem, 3 sheath (small cells round the vessels). x, y scalars or arrays."""
    cls = np.zeros(np.shape(x), np.int32)
    for b in BUNDLES:
        u, v = local(x + nx, y + ny, b)
        fib = (ell(u, v, 0, -205, 215, 150) < 1) | (ell(u, v, 0, 205, 165, 120) < 1) | (ell(u, v, -205, 10, 92, 150) < 1) | (ell(u, v, 205, 10, 92, 150) < 1)
        sh = ell(u, v, 0, 20, 215, 190) < 1
        ph = ell(u, v, 0, -95, 100, 62) < 1
        cls = np.where(fib, 1, cls)
        cls = np.where(sh & ~fib, 3, cls)
        cls = np.where(ph, 2, cls)
    return cls


RADIUS = np.array([47.0, 13.0, 16.0, 17.0])


def holes(x, y):
    """Signed distance outside the hollow things: vessels and lacunae; (d, kind): kind 1 vessel, 2 lacuna."""
    d = np.full(np.shape(x), 1e6, np.float32)
    kind = np.zeros(np.shape(x), np.int32)
    for b in BUNDLES:
        u, v = local(x, y, b)
        for cx, cy, r, ky, kk in ((-118, 18, 76, 1.04, 1), (118, 12, 82, 0.97, 1), (2, 100, 50, 0.72, 2)):
            a_ = np.arctan2((v - cy) * ky, u - cx)
            lobe = 1 + 0.035 * np.sin(3 * a_ + cx) + 0.022 * np.sin(5 * a_ + 2.2 * cy) + 0.012 * np.sin(11 * a_ + r)
            di = (np.hypot(u - cx, (v - cy) * ky) - r * lobe) * b[2]
            kind = np.where(di < d, kk, kind)
            d = np.minimum(d, di)
    return d, kind


def seeds(seed=32):
    """Dart throwing with a radius that depends on the tissue: cells of unequal size, no lattice."""
    rng = np.random.default_rng(seed)
    pts, rad, cl = [], [], []
    bins = {}
    B = 60.0
    n = 0
    xs = rng.uniform(-120, FW + 120, 640000)
    ys = rng.uniform(380, FH + 120, 640000)
    nx, ny = rng.normal(0, 7, 640000), rng.normal(0, 7, 640000)
    c_all = tissue_at(xs, ys, nx, ny)
    k_rand = rng.uniform(0.7, 1.35, 640000) ** 1.4
    h, _ = holes(xs, ys)
    # bundles are drawn at their scale: smaller bundles have somewhat smaller cells
    for i in range(xs.size):
        c = int(c_all[i])
        if h[i] < 1.2:
            continue
        r = RADIUS[c] * (k_rand[i] if c == 0 else 0.86 + 0.28 * k_rand[i] / 1.35)
        if c == 0:
            # parenchyma gets smaller near a bundle
            pass
        ix, iy = int(xs[i] // B), int(ys[i] // B)
        ok = True
        for a in range(ix - 2, ix + 3):
            for b in range(iy - 2, iy + 3):
                for j in bins.get((a, b), ()):
                    if (xs[i] - pts[j][0]) ** 2 + (ys[i] - pts[j][1]) ** 2 < (0.82 * (r + rad[j])) ** 2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            bins.setdefault((ix, iy), []).append(len(pts))
            pts.append((xs[i], ys[i]))
            rad.append(r)
            cl.append(c)
    return np.array(pts, np.float32), np.array(rad, np.float32), np.array(cl, np.int32)


def image(s):
    w, h = int(FW * s), int(FH * s)
    X, Y = np.meshgrid((np.arange(w, dtype=np.float32) + 0.5) / s, (np.arange(h, dtype=np.float32) + 0.5) / s)
    # a hand-cut section is not straight: bend the whole thing
    nw = fbm((180, 320), 320, 60, 500 / FW, 2.4, 3200)
    ne = fbm((180, 320), 320, 60, 500 / FW, 2.4, 3201)
    dx = cv2.resize(nw, (w, h), interpolation=cv2.INTER_CUBIC) * 9.0
    dy = cv2.resize(ne, (w, h), interpolation=cv2.INTER_CUBIC) * 9.0
    # and the cells are not polygons: walls bend at the scale of a cell, each in its own way
    fx = cv2.resize(fbm((h // 2 + 1, w // 2 + 1), 0.5 * s, 22, 110, 2.0, 3210), (w, h), interpolation=cv2.INTER_CUBIC)
    fy = cv2.resize(fbm((h // 2 + 1, w // 2 + 1), 0.5 * s, 22, 110, 2.0, 3211), (w, h), interpolation=cv2.INTER_CUBIC)
    Xw, Yw = X + dx + 4.5 * fx, Y + dy + 4.5 * fy
    field = np.hypot(X - CX, Y - CY)
    in_field = field < RF + 30

    P, Rd, Cl = seeds()
    print("cells", P.shape[0], "fibre", (Cl == 1).sum())
    rng = np.random.default_rng(321)
    tree = cKDTree(P)
    q = np.stack([Xw[in_field], Yw[in_field]], -1)
    d, idx = tree.query(q, k=3, workers=-1)
    c1, c2, c3 = P[idx[:, 0]], P[idx[:, 1]], P[idx[:, 2]]
    d12 = np.linalg.norm(c1 - c2, axis=1) + 1e-3
    d13 = np.linalg.norm(c1 - c3, axis=1) + 1e-3
    w12 = (d[:, 1] ** 2 - d[:, 0] ** 2) / (2 * d12)
    w13 = (d[:, 2] ** 2 - d[:, 0] ** 2) / (2 * d13)
    # thickness of the wall for each cell
    n = P.shape[0]
    T = np.select([Cl == 1, Cl == 2, Cl == 3], [Rd * rng.uniform(0.62, 0.86, n), np.full(n, 2.2, np.float32), np.full(n, 4.0, np.float32)], rng.uniform(3.0, 5.6, n)).astype(np.float32)
    th = 0.5 * (T[idx[:, 0]] + T[idx[:, 1]])
    # rounded lumen corners: a soft minimum of the distances to the two nearest walls
    p = 3.0
    de = (np.maximum(w12, 1e-3) ** -p + np.maximum(w13, 1e-3) ** -p) ** (-1.0 / p) * 1.1
    aa = 0.7 / s
    W_ = sstep(th + aa, th - aa, de)
    lam = np.exp(-((w12 / (0.75 + 0.2 * th.clip(0, 2))) ** 2))  # the middle lamella

    # per-cell stain: fibres red, parenchyma green with some pink, phloem green-blue
    M = np.select([Cl == 1, Cl == 2, Cl == 3], [rng.uniform(1.25, 1.75, n), rng.uniform(0.02, 0.1, n), rng.uniform(0.7, 1.3, n)], rng.uniform(0.03, 0.34, n)).astype(np.float32)
    G = np.select([Cl == 1, Cl == 2, Cl == 3], [rng.uniform(0.0, 0.05, n), rng.uniform(1.0, 1.7, n), rng.uniform(0.05, 0.3, n)], rng.uniform(1.0, 1.9, n)).astype(np.float32)

    frac = np.clip(w12 / (th + 1e-3), 0, 1)
    bands = 1 + 0.045 * np.sin(frac * 17.0)  # lamellae of the thick walls
    is_f = (Cl[idx[:, 0]] == 1).astype(np.float32)
    bands = 1 + (bands - 1) * is_f
    m0 = W_ * M[idx[:, 0]] * bands * (0.55 + 0.75 * lam)
    g0 = W_ * G[idx[:, 0]] * (0.5 + 0.8 * lam)

    # --- starch grains and shrunken contents in some parenchyma cells
    has = rng.random(n) < 0.36
    lum_tint = rng.uniform(0.0, 1.0, n) ** 2
    lum = (1 - W_) * ((Cl[idx[:, 0]] == 0) | (Cl[idx[:, 0]] == 2))

    M_all, G_all, Dn = [np.zeros((h, w), np.float32) for _ in range(3)]
    M_all[in_field], G_all[in_field] = m0, g0
    # lumen wash: a faint tint inside cells
    Dn[in_field] = lum * lum_tint[idx[:, 0]]
    cid = np.full((h, w), -1, np.int32)
    cid[in_field] = idx[:, 0]

    # the hollow ones: vessels and lacunae have a wall ring and are empty
    hd, kind = holes(Xw, Yw)
    vessel_wall = sstep(-16.0, -12.0, hd) * sstep(1.4, -0.2, hd) * (kind == 1)
    empty = sstep(1.4, 0.0, hd)
    M_all = M_all * (1 - empty) + vessel_wall * (1.6 + 0.2 * np.sin(hd * 1.3))
    G_all = G_all * (1 - empty)
    Dn = Dn * (1 - empty)
    # the lacuna: torn wall remnants of protoxylem, a few rings inside it
    r2 = np.random.default_rng(322)
    rem = np.zeros((h, w), np.float32)
    for b in BUNDLES:
        for _ in range(5):
            cx, cy = r2.uniform(-28, 28), 100 + r2.uniform(-24, 24)
            a = np.radians(b[3])
            xc = b[0] + (cx * np.cos(a) - cy * np.sin(a)) * b[2]
            yc = b[1] + (cx * np.sin(a) + cy * np.cos(a)) * b[2]
            rr = r2.uniform(5, 15)
            pts = []
            ph0 = r2.uniform(0, 6.28)
            arc = r2.uniform(2.0, 5.5)
            for t in np.linspace(0, arc, 14):
                pts.append([(xc + (rr + r2.normal(0, 0.8)) * np.cos(ph0 + t)) * s, (yc + (rr + r2.normal(0, 0.8)) * np.sin(ph0 + t)) * s])
            cv2.polylines(rem, [(np.array(pts) * 8).astype(np.int32)], False, 1.0, max(int(2.6 * b[2] * s), 1), cv2.LINE_AA, shift=3)
    M_all = M_all + rem * (kind == 2) * empty * 1.3
    # starch: refractile little ovals, dark rim and light centre
    st = np.zeros((h, w), np.float32)
    sel = np.nonzero(has & (Cl == 0))[0]
    for i in sel:
        c = P[i]
        for _ in range(int(r2.integers(2, 9))):
            ang = r2.uniform(0, 6.28)
            rr = Rd[i] * r2.uniform(0.0, 0.5)
            cx, cy = (c[0] + rr * np.cos(ang) - dx[min(int(c[1] * s), h - 1) if 0 <= c[1] * s < h else 0, 0]), c[1] + rr * np.sin(ang)
            a, b = r2.uniform(2.4, 6.5) * s, r2.uniform(1.6, 4.4) * s
            cv2.ellipse(st, (int(cx * s * 8), int(cy * s * 8)), (int(a * 8), int(b * 8)), r2.uniform(0, 180), 0, 360, 1.0, -1, cv2.LINE_AA, shift=3)
    st = st * (1 - W_big(M_all, G_all))
    # --- uneven staining and a knife chatter that runs across the section
    wash = cv2.resize(fbm((180, 320), 320, 200, 1400 / FW, 2.2, 3202), (w, h), interpolation=cv2.INTER_CUBIC)
    wash2 = cv2.resize(fbm((180, 320), 320, 80, 500 / FW, 2.0, 3203), (w, h), interpolation=cv2.INTER_CUBIC)
    v = 0.87 * X + 0.5 * Y
    chatter = 1 + 0.05 * np.sin(v / 48.0 + 1.4 * np.sin(v / 170.0)) + 0.03 * wash2
    M_all = M_all * (1.05 + 0.2 * wash) * chatter
    G_all = G_all * (1.0 - 0.22 * wash) * chatter

    # debris and the fine tooth of the section: specks of stain, a scratch or two
    r5 = np.random.default_rng(323)
    deb = np.zeros((h, w), np.float32)
    for _ in range(900):
        a = r5.uniform(0.6, 2.6) * s
        cv2.ellipse(deb, (int(r5.uniform(0, w) * 8), int(r5.uniform(0, h) * 8)), (int(a * 8), int(a * r5.uniform(0.5, 1.0) * 8)), r5.uniform(0, 180), 0, 360, float(r5.uniform(0.3, 1.0)), -1, cv2.LINE_AA, shift=3)
    tooth = cv2.resize(fbm((h // 2 + 1, w // 2 + 1), 0.5 * s, 2.5, 14, 1.3, 3212), (w, h), interpolation=cv2.INTER_LINEAR)
    M_all = M_all * (1 + 0.12 * tooth) + 0.35 * deb
    G_all = G_all * (1 + 0.12 * tooth) + 0.3 * deb
    # --- the wall profile under the microscope: thickness behind them (out-of-focus walls beneath)
    def sh(f, dx0, dy0, sig):
        return cv2.GaussianBlur(cv2.warpAffine(f, np.float32([[1, 0, dx0 * s], [0, 1, dy0 * s]]), (w, h)), (0, 0), max(sig * s, 0.5))

    ghost_m, ghost_g = sh(M_all, 3.0, -2.0, 3.6), sh(G_all, 3.0, -2.0, 3.6)

    # absorption (per unit of stain, in linear light): safranin takes green and some blue; fast green takes red and some blue
    sig_m = color([0.1, 1.85, 0.72])
    sig_g = color([1.0, 0.1, 0.36])
    A = M_all[..., None] * sig_m + G_all[..., None] * sig_g
    A = A + 0.28 * (ghost_m[..., None] * sig_m + ghost_g[..., None] * sig_g)
    A = A + (0.7 * Dn)[..., None] * color([0.3, 0.06, 0.16]) + (1.1 * st)[..., None] * color([0.5, 0.42, 0.34])
    # a faint overall tint of the mountant and uneven background
    A = A + color([0.07, 0.05, 0.14]) * (1 + 0.2 * wash2[..., None])
    # bright diffraction line beside each wall
    T_ = np.exp(-A)
    gray = T_.mean(-1)
    halo = np.clip(gray - cv2.GaussianBlur(gray, (0, 0), 2.6 * s), -0.3, 0.3)
    T_ = T_ * (1 + 0.5 * halo[..., None])

    # --- focus: the plane tilts across the field; sharp along the upper arc, soft towards the lower corners
    rel = np.hypot((X - 1250) / 1700, (Y - 700) / 900)
    foc = np.clip(rel - 0.2, 0, 1) ** 1.35 * 5.0 + 0.3 * cv2.resize(fbm((90, 160), 160, 200, 900 / FW, 2.0, 3204), (w, h), interpolation=cv2.INTER_CUBIC).clip(-1, 1)
    foc = np.maximum(foc, 0.25)
    levels = [0.3, 1.2, 2.5, 5.0]
    stack = []
    for sig in levels:
        ch = [cv2.GaussianBlur(T_[..., c], (0, 0), max(sig * s * f, 0.3)) for c, f in ((0, 1.0), (1, 1.0), (2, 1.0 + 0.4 / max(sig, 0.3)))]
        stack.append(np.stack(ch, -1))
    out = np.zeros_like(T_)
    for a in range(3):
        lo, hi = levels[a], levels[a + 1]
        t = np.clip((foc - lo) / (hi - lo), 0, 1)
        sel_ = ((foc >= lo) & (foc < hi)) | ((a == 0) & (foc < lo)) | ((a == 2) & (foc >= hi))
        out = np.where(sel_[..., None], stack[a] * (1 - t[..., None]) + stack[a + 1] * t[..., None], out)

    # --- the lamp and the field stop; the stop is imaged with some lateral colour
    falloff = 1.0 - 0.44 * np.clip(np.hypot(X - 1200, Y - 1150) / 2100, 0, 1) ** 2.2
    lamp = color([1.0, 0.95, 0.83]) * 1.0
    edge = 5.0
    stop = np.stack([sstep(RF + edge + 1.6, RF - edge + 1.6, field), sstep(RF + edge, RF - edge, field), sstep(RF + edge - 1.6, RF - edge - 1.6, field)], -1)
    # a scrap of lens flare: the field just inside the stop is a little lighter on one side
    L = out * lamp * falloff[..., None] * stop
    L = L + stop * 0.012 * color([0.8, 0.9, 1.0])
    return L.astype(np.float32)


def W_big(M, G):
    return np.clip(4 * (M + G), 0, 1)


def main():
    q = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview")
    s = {"preview": 0.375, "mid": 0.5, "final": 1.0}[q]
    d = os.path.join(OUT, "s32_zhu")
    os.makedirs(d, exist_ok=True)
    L = image(s)
    look = {"exposure": 0.0, "contrast": 1.38, "saturation": 1.04, "black": 0.0, "ca": 0.0005, "grain": 1.1, "sharpen": 0.32, "halation": 0.012, "glare": 0.004, "vignette": 0.1}
    np.save(os.path.join(d, f"{q}.linear.npy"), L)
    json.dump(look, open(os.path.join(d, f"{q}.develop.json"), "w"))
    img = develop(L, **look)
    p = os.path.join(d, f"{q}.png")
    save_png(p, img)
    cv2.imwrite(p[:-4] + ".jpg", (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(p[:-4] + ".jpg")


main()
