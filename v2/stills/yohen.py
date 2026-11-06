"""The yohen glaze, shared by s02 (close) and s47 (from above). Everything is painted in a Dish's flat coordinates, in cm.

The mechanism here, and what is measured and what is not (ref/yohen/report.md):
- The colour is true thin-film interference (Principled Thin Film): a thickness in nm per vertex, a film IOR of 2.5. Film n is an ESTIMATE between magnetite (2.4) and hematite (2.9) from the
  optical tables in ref/yohen/data; the real bowl's structure is argued over and never measured as a film thickness on the original. The thickness ramp is a LOOK chosen from an Airy chart so that the order runs
  cream > pale green > turquoise > blue > violet, as seen outward from the spots in the Inaba photographs.
- The film lies on a reflecting oxide layer: its lobe is Metallic with Base Color 0.6 (ESTIMATE, a stand-in for a stack that has never been measured), because a film on bare glass reflects too little against the glass skin's own 4%. The thickness ramp was read from a rendered chart of this lobe (second and third order, so the hue moves quickly with the angle).
- The film thins into islands of partial coverage away from the spots: `cov` is a mix between bare glaze and film. That is a stand-in for a film that breaks up.
- A dim diffuse tint under the film, from the same chart at normal incidence (STAND-IN: the real blue has a weakly angular, scattering part; Fukushima, Feng, ref/yohen/report.md). It keeps the blue alive where the surface mirrors nothing bright.
- Spot outlines, sizes and clusters: estimates compared by eye with ref/yohen/images/inaba_2025_internetmuseum_frame53.5.png.
- `vivid`: the same interference, far more of it. Against ref/yohen/images the spots and their ponds nearly fill the bowl, and the blue goes electric. Thickness now wanders across the bowl, so that ponds differ in hue, and every hue still moves with the angle. All of it is a LOOK read off the same chart, not a measurement. The diffuse body takes its hue from airy() of the local thickness, saturated by eye: STAND-IN.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

import kit
from kit import _cam_axes, blur, caps, color, fbm, mix, rank, sstep

FILM_N, GLASS_N = 2.5, 1.55


# --- fields fixed to the bowl, so that a preview and a final show the same picture -------------------------------------
def fixed(X, Y, lo, hi, beta, seed, extent=11.0, res=48.0):
    """Noise on a fixed grid over the bowl (res px/cm), sampled at X, Y. For anything that shapes the composition."""
    n = int(2 * extent * res)
    f = fbm((n, n), res, lo, hi, beta, seed)
    u = ((X + extent) * res).astype(np.float32)
    v = ((Y + extent) * res).astype(np.float32)
    return cv2.remap(f, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def hatch(X, Y, width, length, seed, rho_max=11.0, wander=0.0):
    """A streak field down the wall: a table far finer across the wall than along it. width, length in cm at rho = rho_max / 2. Fixed size, the same at every quality."""
    rho = np.hypot(X, Y)
    th = np.arctan2(Y, X) + wander
    ncol = min(int(2 * np.pi * rho_max / 2 / (width / 2.5)), 32000)
    nrow = max(int(rho_max / (length / 2.5)), 8)
    # the table is noise with one sample per quarter width; the remap limit of 32767 rows/cols is respected
    t = np.random.default_rng(seed).standard_normal((nrow, ncol), dtype=np.float32)
    # the table closes round the bowl: wrapped columns, or the seam at th = pi draws a notch through the lip
    t = np.concatenate([t[:, -8:], t, t[:, :8]], 1)
    t = cv2.GaussianBlur(t, (0, 0), sigmaX=1.2, sigmaY=1.2, borderType=cv2.BORDER_REFLECT)[:, 8:-8]
    t = (t - t.mean()) / t.std()
    u = (np.mod(th + np.pi, 2 * np.pi) / (2 * np.pi) * (ncol - 1)).astype(np.float32)
    v = (np.clip(rho / rho_max, 0, 1) * (nrow - 1)).astype(np.float32)
    return cv2.remap(t, u, v, cv2.INTER_LINEAR)


# --- the chart ---------------------------------------------------------------------------------------------------------
_WL = np.arange(380.0, 781.0, 5.0)


def _g(x, m, s1, s2):
    return np.exp(-0.5 * ((x - m) / np.where(x < m, s1, s2)) ** 2)


_XB = 1.056 * _g(_WL, 599.8, 37.9, 31) + 0.362 * _g(_WL, 442, 16, 26.7) - 0.065 * _g(_WL, 501.1, 20.4, 26.2)
_YB = 0.821 * _g(_WL, 568.8, 46.9, 40.5) + 0.286 * _g(_WL, 530.9, 16.3, 31.1)
_ZB = 1.217 * _g(_WL, 437, 11.8, 36) + 0.681 * _g(_WL, 459, 26, 13.8)
_M = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.204, 1.057]])


def airy_table(nf=FILM_N, ns=GLASS_N, dmax=320):
    """Linear RGB of the reflectance of a film of d nm on glass, at normal incidence. For the dim diffuse stand-in."""
    d = np.arange(0.0, dmax + 1.0)
    r1, r2 = (1 - nf) / (1 + nf), (nf - ns) / (nf + ns)
    ph = 4 * np.pi * nf * d[:, None] / _WL
    z = (r1 + r2 * np.exp(1j * ph)) / (1 + r1 * r2 * np.exp(1j * ph))
    R = np.abs(z) ** 2
    XYZ = np.stack([R @ _XB, R @ _YB, R @ _ZB], -1) / _YB.sum()
    return np.clip(XYZ @ _M.T, 0, None).astype(np.float32)


def airy(d, tab=airy_table()):
    i = np.clip(d, 0, len(tab) - 1.001)
    a = i.astype(np.int32)
    f = (i - a)[..., None]
    return tab[a] * (1 - f) + tab[a + 1] * f


# --- spots: outlines that are not circles, gathered in clusters, sizes running over a decade ---------------------------
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Spots:
    def __init__(self, X, Y, pxcm, dish, seed):
        self.X, self.Y, self.pxcm = X, Y, pxcm
        self.shape = X.shape
        self.F = np.full(X.shape, 9.0, np.float32)  # signed distance, cm, negative inside
        self.VAL = np.zeros(X.shape, np.float32)
        self.R = np.zeros(X.shape, np.float32)  # the spot's radius
        self.rng = np.random.default_rng(seed)
        self.x0, self.y0 = float(X[0, 0]), float(Y[0, 0])
        tab_r = np.linspace(0.0, dish.L, 1024)
        tab_k = np.maximum(tab_r / np.maximum(dish.prof.at(np.clip(dish.L - tab_r, 0.0, dish.L))[0], 0.2), 1.0)
        self.k = lambda rho: float(np.interp(rho, tab_r, tab_k))
        self.placed = []  # (cx, cy, r)

    def stamp(self, cx, cy, r, neck=0.012, value=None):
        """One spot: a polar outline with low harmonics, a little run-out down the wall. Neighbours flow together through a smooth minimum."""
        rng = self.rng
        rho = float(np.hypot(cx, cy))
        b = float(np.arctan2(cy, cx))
        k2 = self.k(rho)
        el = float(rng.choice([1.0, 1.08, 1.2, 1.38, 1.7], p=[0.3, 0.3, 0.22, 0.13, 0.05]))
        # the harmonics are drawn for this spot alone; large spots have more wander than small ones
        amp = 0.05 + 0.11 * min(r / 0.2, 1.0)
        hs = [(kk, rng.normal(0, amp / kk**0.9), rng.uniform(0, 2 * np.pi)) for kk in (2, 3, 4, 5, 7)]
        tear = rng.uniform(-0.03, 0.28) if rng.random() < 0.45 else 0.0  # fatter towards the well, as a drop that began to run
        m = r * 1.9 * el * k2 + 0.05
        pxcm = self.pxcm
        i0, i1 = max(int((cx - m - self.x0) * pxcm), 0), min(int((cx + m - self.x0) * pxcm) + 2, self.shape[1])
        j0, j1 = max(int((cy - m - self.y0) * pxcm), 0), min(int((cy + m - self.y0) * pxcm) + 2, self.shape[0])
        if i1 <= i0 or j1 <= j0:
            return
        dx, dy = self.X[j0:j1, i0:i1] - cx, self.Y[j0:j1, i0:i1] - cy
        er, et = (dx * np.cos(b) + dy * np.sin(b)) / el, (-dx * np.sin(b) + dy * np.cos(b)) / k2
        rr = np.hypot(er, et)
        ph = np.arctan2(et, er)
        out = 1.0 + tear * np.cos(ph - np.pi)  # ph = pi looks towards the well
        for kk, a, p in hs:
            out = out + a * np.cos(kk * ph + p)
        d = (rr - r * out) * np.minimum(el, 1.25) ** 0.3
        F = self.F[j0:j1, i0:i1]
        win = d < F
        self.VAL[j0:j1, i0:i1][win] = rng.uniform(0, 1) if value is None else value
        self.R[j0:j1, i0:i1][win] = r
        self.F[j0:j1, i0:i1] = smin(F, d, neck).astype(np.float32)
        self.placed.append((cx, cy, r))

    def free(self, cx, cy, r, gap):
        for a, b, q in self.placed:
            if (a - cx) ** 2 + (b - cy) ** 2 < (q + r + gap) ** 2:
                return False
        return True


def layout(S, rl, n_cl, rho0, rho1, r_big=(0.13, 0.3), seed_rim=0.0, pack=1.0, spacing=0.85):
    """A cluster process. A cluster is one or two large spots with satellites packed against them. A chain (some clusters run on as a chain, as on the bowl)."""
    rng = S.rng
    done = 0
    centres = []
    tries = 0
    while done < n_cl and tries < n_cl * 200:
        tries += 1
        rho = rng.uniform(rho0, rho1)
        th = rng.uniform(-np.pi, np.pi)
        cx, cy = rho * np.cos(th), rho * np.sin(th)
        if centres and min((cx - a) ** 2 + (cy - b) ** 2 for a, b in centres) < spacing**2:
            continue
        centres.append((cx, cy))
        done += 1
        near = sstep(rl - 0.6, rl - 2.2, rho)  # small and sparse towards the lip
        scale = 0.5 + 0.5 * float(near)
        big = np.clip(rng.lognormal(np.log(np.mean(r_big)), 0.42), r_big[0] * 0.5, r_big[1] * 1.15) * scale
        kind = rng.choice(["clump", "pair", "chain", "lone"], p=[0.5, 0.15, 0.25, 0.1])
        S.stamp(cx, cy, big)
        members = [(cx, cy, big)]
        if kind == "lone":
            if rng.random() < 0.6:
                t = rng.uniform(0, 2 * np.pi)
                r2 = big * rng.uniform(0.25, 0.45)
                S.stamp(cx + (big + r2 + 0.025) * np.cos(t), cy + (big + r2 + 0.025) * np.sin(t), r2)
            continue
        if kind == "pair":
            t = rng.uniform(0, 2 * np.pi)
            r2 = big * rng.uniform(0.55, 0.95)
            g = big + r2 + rng.uniform(-0.01, 0.05)
            S.stamp(cx + g * np.cos(t), cy + g * np.sin(t), r2)
            members.append((cx + g * np.cos(t), cy + g * np.sin(t), r2))
        if kind == "chain":
            t = rng.uniform(0, 2 * np.pi)
            px_, py_, pr = cx, cy, big
            for _ in range(int(rng.integers(3, 8))):
                t = t + rng.normal(0, 0.55)
                r2 = float(np.clip(pr * rng.lognormal(-0.1, 0.45), 0.03, big))
                g = pr + r2 + rng.uniform(0.0, 0.05)
                px_, py_, pr = px_ + g * np.cos(t), py_ + g * np.sin(t), r2
                if not (0.9 < np.hypot(px_, py_) < rl - 0.3):
                    break
                S.stamp(px_, py_, r2)
                members.append((px_, py_, r2))
        # satellites: packed round the members, with sizes far below them
        n_sat = int(rng.lognormal(np.log(6.0 * pack), 0.65))
        for _ in range(n_sat):
            for _try in range(14):
                mx_, my_, mr = members[rng.integers(0, len(members))]
                r3 = float(np.clip(rng.lognormal(np.log(0.05), 0.55), 0.016, 0.8 * big)) * (0.6 + 0.4 * float(near))
                t = rng.uniform(0, 2 * np.pi)
                g = mr + r3 + rng.uniform(0.012, 0.05)
                sx, sy = mx_ + g * np.cos(t), my_ + g * np.sin(t)
                if not (0.9 < np.hypot(sx, sy) < rl - 0.25):
                    continue
                if S.free(sx, sy, r3, 0.008):
                    S.stamp(sx, sy, r3)
                    members.append((sx, sy, r3))
                    break


def paint(dish, X, Y, pxcm, seed, n_cl, rho0, rho1, r_big=(0.13, 0.3), pack=1.0, blue=1.0, metal_frac=0.5, hatch_w=0.011, pools=None, vivid=None):
    """The fields of the fired surface. Returns dict with col, rough, film, cov, h and the masks the caller wants for the shell.
    vivid: {"spacing": cm between clusters, "pond": (lo, hi), "hue": nm of thickness wander across the bowl, "flash": nm at a finer scale, "satin": extra roughness of the film, "crust": brightness of the spots, "island": width of the gaps that close to cream, "fade": where the blue has broken up into black, in units of its reach, "halo": a narrower band of pale colour round each spot, for a close view, "floor": the thinnest film, nm, so that a wide reach stays blue and does not run into rose, "ramp": thickness against distance from the spot, flatter means less of a contour map, "hair": nm each hare's-fur hair adds or takes, so that threads of different hue lie side by side, "ring": where the solid band at the spot's edge ends, "spot_var": how much spots differ in brightness, "silver": spots with a dark heart in a silver rim, "soft": how much of the hatch reaches the edge of the colour, 1 is all of it, "tint": strength of the diffuse stand-in beside the real film}. None is the look before it."""
    shape = X.shape
    rho = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    rl = dish.rho_lip
    S = Spots(X, Y, pxcm, dish, seed)
    layout(S, rl, n_cl, rho0, rho1, r_big=r_big, pack=pack, spacing=vivid["spacing"] if vivid else 0.85)
    print("spots", len(S.placed), flush=True)
    # a tiny bite in every outline: it comes from fixed fine noise, on the distance field
    bite = 0.0005 * fbm(shape, pxcm, 0.012, 0.05, 1.8, seed + 3) + 0.0016 * fbm(shape, pxcm, 0.05, 0.22, 2.4, seed + 4)
    F = S.F + bite
    disc = sstep(0.0035, -0.0035, F)
    inside = np.maximum(-F, 0.0)

    # --- islands: close the gaps between spots with a width that belongs to each place, so the cream is an outline and not a coat of even thickness
    gw = 0.028 + 0.05 * rank(fixed(X, Y, 0.4, 2.0, 2.6, seed + 5)) + 0.01 * fbm(shape, pxcm, 0.04, 0.2, 2.2, seed + 6)
    if vivid:
        gw = gw * vivid["island"]  # packed spots close nearly every gap: most of them stay open, or the bowl goes cream
    grown = F < gw
    Din = cv2.distanceTransform(grown.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm
    island = Din > 0.5 * gw
    nl, labs = cv2.connectedComponents(island.astype(np.uint8), connectivity=8)
    hold = np.bincount(labs.ravel(), weights=(F < -0.012).ravel().astype(np.float64), minlength=nl)
    island = (hold >= max(6.0, (0.03 * pxcm) ** 2))[labs] & (labs > 0)
    # big-enough only: specks carry no island
    Eo, lab = cv2.distanceTransformWithLabels((~island).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    Eo = Eo.astype(np.float32) / pxcm
    Ei = cv2.distanceTransform(island.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32) / pxcm
    ys, xs = np.nonzero(island)
    L_ = lab[ys, xs]
    bx, by = np.zeros(L_.max() + 1, np.int32), np.zeros(L_.max() + 1, np.int32)
    bx[L_], by[L_] = xs, ys
    # the feather: short hairs at right angles to the island's edge
    fr = rank(fbm(shape, pxcm, max(0.008, 2.2 / pxcm), 0.03, 1.0, seed + 81))
    feather = blur(fr[by[lab], bx[lab]], max(0.0018 * pxcm, 0.5)) - 0.5
    feather = feather * sstep(0.25, 0.04, Eo)

    # --- where the blue lies: ponds, deep towards the well, with black reaches between them
    pond = rank(fixed(X, Y, 0.7, 4.5, 3.0, seed + 8))
    lower = sstep(rl - 0.2, rl - 1.4, rho)
    if pools is not None:
        pond = pools(X, Y, pond)
    # the film ran down the wall: long below an island, hardly any above it. Which side of its island a point lies on, blurred or the seams where the nearest edge jumps show
    ex = (np.arange(shape[1], dtype=np.float32)[None, :] - bx[lab].astype(np.float32)) / pxcm
    ey = (np.arange(shape[0], dtype=np.float32)[:, None] - by[lab].astype(np.float32)) / pxcm
    down = -(ex * X + ey * Y) / np.maximum(Eo * rho, 1e-4)
    down = blur(np.clip(down, -1, 1), max(0.05 * pxcm, 1.0))
    side = np.clip(0.5 + 0.5 * down, 0.0, 1.0)  # the blur can round just past the ends, and a negative base has no power
    reach = 0.012 + blue * (0.03 + 0.1 * side**1.5 + 1.05 * sstep(*(vivid["pond"] if vivid else (0.36, 0.86)), pond) ** 1.2 * (0.12 + 0.88 * side)) * (0.25 + 0.75 * lower)
    # the streaks run down the wall, each with its own wander. Two sizes, and a slow bend across the wall so that they are not ruled
    bend = 0.006 * fixed(X, Y, 0.6, 2.4, 2.8, seed + 40)
    s1 = hatch(X, Y, hatch_w, 0.16, seed + 41, wander=bend)
    s2 = hatch(X, Y, hatch_w * 3.5, 0.45, seed + 42, wander=bend)
    s3 = hatch(X, Y, hatch_w * 9.0, 1.6, seed + 43, wander=bend)
    streak = 0.75 * s1 + 0.3 * s2 + 0.12 * s3
    soft = vivid.get("soft", 1.0) if vivid else 1.0  # how much of the hatch reaches the edge of the colour: a close view at 1 shows felt, not a film thinning out
    x = Eo / reach * np.clip(1.0 + 0.08 * soft * streak, 0.75, 1.3) * (1.0 - 0.5 * soft * feather)
    # the film breaks up into hairs as it thins: coverage falls along x, sooner in the dark streaks
    cov_blue = sstep(vivid.get("fade", 1.05) if vivid else 1.05, 0.4, x + 0.18 * soft * np.minimum(streak, 0.5))
    # the hatch: short dark dashes across the blue. They are the texture of the real thing, crisp at 100 percent
    s0 = hatch(X, Y, hatch_w * 0.6, 0.07, seed + 46, wander=bend)
    dash = 0.7 * s0 + 0.5 * s1
    cov_blue = cov_blue * (1.0 - 0.5 * soft * sstep(0.1, -1.0, dash)) * (1.0 - 0.14 * soft * sstep(0.8, -1.0, s2))
    # the hatch is lost right at the cream
    ring_x = vivid["ring"] if vivid and "ring" in vivid else (0.16, 0.05)
    cov_blue = np.maximum(cov_blue, sstep(*ring_x, x) * sstep(1.22, 0.45, x))
    # thickness: an Airy chart read outward from the spot: cream > pale green > turquoise > blue > violet
    drift = fixed(X, Y, 0.5, 3.5, 2.6, seed + 44)
    d_x = np.interp(np.clip(x, 0, 3).ravel(), [0.0, 0.05, 0.14, 0.32, 0.65, 1.2, 3.0], [188.0, 176.0, 166.0, 161.0, 157.0, 154.0, 152.0]).reshape(shape).astype(np.float32)
    film = d_x + 2.0 * drift + 1.2 * streak
    if vivid:
        # past the violet the ramp runs on into rose; and each part of the bowl sits at its own place on the chart: turquoise and green here, ultramarine and violet there, a flash of gold by an island
        d_v = np.interp(np.clip(x * vivid.get("halo", 1.0), 0, 3).ravel(), [0.0, 0.03, 0.08, 0.2, 0.5, 1.0, 3.0], vivid.get("ramp", [198.0, 176.0, 163.0, 156.0, 154.0, 152.0, 140.0])).reshape(shape).astype(np.float32)
        d_v = np.maximum(d_v, vivid.get("floor", 0.0))
        film = d_v + vivid["hue"] * 2.0 * (rank(fixed(X, Y, 0.9, 5.0, 3.2, seed + 91)) - 0.5) + vivid["flash"] * fixed(X, Y, 0.2, 0.9, 2.4, seed + 92) + vivid.get("hair", 1.2) * streak
    # inside an island: cream to pale gold, thick against the spots
    t_i = sstep(0.0, 0.05, Ei)
    tone = rank(fixed(X, Y, 0.25, 1.6, 2.4, seed + 22))
    film_i = 88.0 + 8.0 * t_i + 8.0 * (tone - 0.5) + 2.5 * fbm(shape, pxcm, 0.02, 0.12, 2.0, seed + 23)
    isl = sstep(0.0, 0.007, Ei + 0.002 * fbm(shape, pxcm, 0.01, 0.05, 1.5, seed + 24)) * (Ei > 0)
    film = mix(film, film_i, isl)
    cov = np.maximum(cov_blue, isl)
    # the glow fades by the lip, where the fire was gentler
    fade = sstep(rl - 0.05, rl - 0.75, rho)
    cov = cov * fade * (0.8 + 0.2 * rank(fixed(X, Y, 0.4, 2.0, 2.6, seed + 45)))

    # --- the black: not one black. The glaze is dark brown where it is thin, and has a dusting of crystals
    m = rank(fixed(X, Y, 0.1, 1.8, 2.8, seed + 10))
    glaze = mix(color([0.0035, 0.003, 0.0034]), color([0.009, 0.0072, 0.0068]), m)
    # the dim body of the colour: a ramp, STAND-IN (the real blue's weakly angular scattering part); the film adds the part that moves
    RX = [0.0, 0.05, 0.13, 0.3, 0.6, 1.0, 1.5]
    RC = np.array([[0.46, 0.5, 0.36], [0.26, 0.46, 0.42], [0.05, 0.29, 0.42], [0.012, 0.115, 0.36], [0.007, 0.05, 0.24], [0.005, 0.016, 0.1], [0.004, 0.004, 0.006]], np.float32)
    xc = np.clip(x, 0, 2).ravel()
    tint = np.stack([np.interp(xc, RX, RC[:, i]).reshape(shape) for i in range(3)], -1).astype(np.float32)
    if vivid:
        hue = airy(np.clip(film, 0, 320))
        hue = (hue / (hue.max(-1, keepdims=True) + 1e-4)) ** 1.9
        tint = hue * tint.max(-1, keepdims=True)
    cream = mix(color([0.5, 0.48, 0.34]), color([0.62, 0.56, 0.42]), tone) * (0.86 + 0.14 * sstep(-1.0, 1.0, fbm(shape, pxcm, 0.015, 0.08, 1.6, seed + 25)))[..., None]
    tint = mix(tint, cream, isl)
    col = glaze + (vivid.get("tint", 0.72) if vivid else 0.72) * tint * cov[..., None]

    # --- the spot: crust. A hard dark outline, a grey-tan body broken into crystals, a lighter heart in some
    cell = fbm(shape, pxcm, 0.006, 0.028, 1.2, seed + 77)
    cell2 = fbm(shape, pxcm, 0.02, 0.11, 2.0, seed + 78)
    val = S.VAL
    heart = sstep(0.008, 0.11, inside)
    blotch = fbm(shape, pxcm, 0.03, 0.22, 2.6, seed + 79)
    web = sstep(0.28, 0.0, np.abs(fbm(shape, pxcm, 0.014, 0.06, 2.0, seed + 80)))  # a crystalline net, not grains
    # silver: as in inaba_mitsubishi2025_img-1-1.jpg, a spot is a dark heart inside a rim of silver crystals, not an even grey block. Colours and widths by eye
    silver = bool(vivid and vivid.get("silver"))
    body = mix(color([0.1, 0.105, 0.115] if silver else [0.07, 0.058, 0.04]), color([0.46, 0.47, 0.5] if silver else [0.36, 0.3, 0.2]), np.clip(0.2 + 0.6 * val**0.8 + 0.13 * blotch, 0, 1))
    body = body * (1.0 - 0.22 * web)[..., None] * (0.92 + 0.08 * sstep(-0.5, 1.0, cell))[..., None]
    rr = inside / np.maximum(S.R, 0.01)
    # the rim's width goes with the spot's size (a fixed width in cm filled the small spots with grey), and it is broken into crystals
    rim = sstep(*(vivid["rim"] if vivid and "rim" in vivid else (0.3, 0.1)), rr) * (0.45 + 0.55 * sstep(-0.6, 0.5, cell)) if silver else None
    body = body * (0.1 + 1.25 * rim if silver else 0.62 + 0.55 * sstep(0.0, 0.75, rr))[..., None]
    if vivid:
        body = body * vivid["crust"] * (0.55 + vivid.get("spot_var", 0.0) * val)[..., None] if vivid.get("spot_var") else body * vivid["crust"]
    pupil = (val < 0.2) * sstep(0.05, 0.15, inside)  # some have a sunken dark pupil
    body = mix(body, color([0.018, 0.016, 0.014]), 0.8 * pupil)
    ring = sstep(0.022, 0.006, inside) * sstep(0.0, 0.004, inside)
    ring_w = 0.5 + 0.5 * sstep(0.05, 0.14, S.R)  # small spots have no room for a heavy line
    body = body * (1.0 - (0.4 if silver else 0.9) * ring * ring_w)[..., None]
    col = mix(col, body, disc)
    # a faint silver sheen on the crust: thin film, little coverage
    film = mix(film, 58.0 + 18.0 * cell2, disc)
    cov = mix(cov, (0.18 + (0.55 if vivid else 0.3) * val * heart) * (0.6 + 0.4 * sstep(-0.8, 1.0, cell)), disc)
    # just outside a spot the film stands thick and bright: the outline's other side
    edge_out = sstep(0.0, 0.002, F) * sstep(0.012, 0.0, F)

    # --- crystals: a dust of tiny stars over the black
    dust_h = caps(shape, pxcm, 1.6 * pack, 0.0022, 0.009, seed + 6, slope=-2.6)
    dust = sstep(0.0, 0.0012, dust_h) * (1 - isl) * (1 - disc) * fade
    film = mix(film, 170.0 + 30.0 * (cell2 * 0.5), dust)
    cov = np.maximum(cov, 0.9 * dust)
    col = mix(col, color([0.22, 0.2, 0.17]), 0.7 * dust)

    # --- finish
    rough = 0.09 + 0.05 * m
    # the film is satin under the glass: a small bright lamp is a crisp glint in the glass and a wide glow of colour in the film. That is how black stays black
    rough = rough + (vivid["satin"] if vivid else 0.17) * sstep(0.0, 0.2, cov)
    rough = mix(rough, 0.34 + 0.12 * sstep(-1, 1, cell), disc)

    # --- the lip: stoneware under a thin glaze. A burnt silver grit in a brown, the black glaze pulling back from it in a broken line
    edge = 0.012 * fixed(X, Y, 0.15, 1.1, 2.8, seed + 11) + 0.004 * fbm(shape, pxcm, 0.02, 0.1, 1.8, seed + 12)
    lip = sstep(rl - 0.15, rl - 0.05, rho + edge)
    sp = rank(0.65 * fbm(shape, pxcm, 0.012, 0.05, 1.4, seed + 75) + 0.5 * fbm(shape, pxcm, 0.004, 0.012, 1.0, seed + 76))
    patch = rank(fixed(X, Y, 0.08, 0.5, 1.8, seed + 78))
    lip_col = mix(color([0.06, 0.042, 0.03]), color([0.3, 0.24, 0.17]), sp**3.0 * (0.7 + 0.5 * patch))
    lip_col = lip_col * (0.8 + 0.3 * patch)[..., None]
    col = mix(col, lip_col, lip)
    # rust where the glaze thins under the lip: brown hairs run down from it
    fur = sstep(0.5, 1.9, 0.9 * hatch(X, Y, 0.012, 0.16, seed + 71) + 0.5 * hatch(X, Y, 0.04, 0.35, seed + 72))
    thin = sstep(rl - 0.5, rl - 0.18, rho + 1.5 * edge) * (1 - lip)
    col = mix(col, color([0.05, 0.026, 0.012]), 0.38 * thin * fur)
    cov = cov * (1 - lip)
    rough = mix(rough, 0.5 + 0.2 * sp, lip)

    # --- height of the fired surface: the crust sits a hair proud, each streak leans a little. The tilt is what makes colour sparkle as it turns
    h = 0.0007 * blur(disc, max(0.01 * pxcm, 0.8)) + 0.00022 * s1 * (1 - disc) * cov + 0.00045 * fbm(shape, pxcm, 0.03, 0.12, 1.8, seed + 13) * disc
    h = h + 0.00025 * sstep(-0.5, 1.5, cell) * disc + 0.5 * dust_h * 0.25 + lip * 0.007 * (sp - 0.5)
    return dict(col=np.clip(col, 0, 1).astype(np.float32), rough=np.clip(rough, 0.03, 1).astype(np.float32), film=np.clip(film, 0, 400).astype(np.float32), cov=np.clip(cov * metal_frac, 0, 1).astype(np.float32), h=h.astype(np.float32), lip=lip, disc=disc, island=isl)


def shell_fields(dish, X, Y, pxcm, seed, gap=0.05, wave=0.003, rings=0.0008, scratches=1.0):
    """The glass over all of it: where the surface's slow waves live, the throwing rings, hair scratches, pinholes."""
    shape = X.shape
    rho = np.hypot(X, Y)
    rl = dish.rho_lip
    g = 0.002 + gap * sstep(rl - 0.1, rl - 1.3, rho)
    # slow waves, on the fixed grid. Rings: the potter's fingers, of irregular spacing, broken around the bowl
    w1 = fixed(X, Y, 1.0, 5.0, 3.6, seed + 14)
    w2 = fixed(X, Y, 0.3, 1.1, 3.0, seed + 15)
    rng = np.random.default_rng(seed + 16)
    phase = np.zeros(shape, np.float32)
    ph0 = rng.uniform(0, 2 * np.pi, 5)
    for i, lam in enumerate((0.42, 0.57, 0.83, 1.17, 1.9)):
        phase = phase + np.sin(2 * np.pi * rho / lam + ph0[i] + 1.3 * fixed(X, Y, 1.5, 6.0, 3.0, seed + 60 + i)) * rng.uniform(0.5, 1.0)
    orange = fbm(shape, pxcm, 0.05, 0.18, 2.2, seed + 17)
    h = g + wave * w1 + 0.12 * wave * w2 + rings * phase + 0.000012 * orange
    # hair scratches: mostly short, a few long, in no order, with a few deep ones
    scr = np.zeros(shape, np.uint8)
    n = int(shape[0] * shape[1] / pxcm**2 * 16 * scratches)
    for _ in range(n):
        a = rng.uniform(0, np.pi)
        L0 = rng.lognormal(np.log(0.16), 0.75) * pxcm
        p0 = np.array([rng.uniform(0, shape[1]), rng.uniform(0, shape[0])])
        p1 = p0 + L0 * np.array([np.cos(a), np.sin(a)])
        cv2.line(scr, tuple(np.int32(p0)), tuple(np.int32(p1)), int(rng.lognormal(np.log(60), 0.6)), 1, cv2.LINE_AA)
    sc = scr.astype(np.float32) / 255.0
    rough = 0.018 + 0.006 * rank(w2) + 0.13 * np.clip(sc, 0, 1)
    h = h - 0.00025 * sc
    # the glass ends in the thin glaze of the lip
    on = sstep(rl + 0.02, rl - 0.1, rho) * (0.3 + 0.7 * sstep(rl - 0.1, rl - 0.25, rho))
    rough = rough + 0.2 * sstep(rl - 0.25, rl - 0.08, rho)
    return h.astype(np.float32), np.clip(rough, 0.012, 1).astype(np.float32), on.astype(np.float32)


# --- the room: a real environment image, painted panel by panel, seen only in reflections ----------------------------------
def direction_grid(w=4096, h=2048):
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi - np.pi / 2
    lon, lat = np.meshgrid(lon, lat[::-1])
    return np.stack([np.cos(lat) * np.cos(lon), -np.cos(lat) * np.sin(lon), np.sin(lat)], -1)


def paint_room(path, cam, spec):
    """spec: base [r,g,b] (the dark room), panels: [{dir, up?, w, h (half size, degrees), L, rgb, soft (degrees), bars (n verticals), hbars, grad, roll}]. Registered into kit in place of kit.room_env."""
    d = direction_grid()
    E = np.ones(d.shape, np.float32) * np.array(spec.get("base", [0.01, 0.01, 0.01]), np.float32)
    n = fbm((512, 1024), 1.0, 5.0, 200.0, 2.6, spec.get("seed", 3))
    E = E * np.exp(0.6 * cv2.resize(n, (d.shape[1], d.shape[0]), interpolation=cv2.INTER_CUBIC))[..., None]
    for p in spec.get("panels", []):
        c = np.array(p["dir"], np.float32)
        c /= np.linalg.norm(c)
        up = np.array(p.get("up", [0, 0, 1]), np.float32)
        r = np.cross(up, c)
        r /= np.linalg.norm(r)
        u = np.cross(c, r)
        roll = np.radians(p.get("roll", 0.0))
        r, u = r * np.cos(roll) + u * np.sin(roll), -r * np.sin(roll) + u * np.cos(roll)
        fw = np.maximum(d @ c, 1e-3)
        a = np.degrees(np.arctan((d @ r) / fw))
        b = np.degrees(np.arctan((d @ u) / fw))
        s = p.get("soft", 4.0)
        sw = p.get("soft_w", s)
        if p.get("round"):
            q_ = np.hypot(a / p["w"], b / p["h"])
            m = sstep(1.0 + p["round"], 1.0 - p["round"], q_) * (d @ c > 0)
        else:
            m = sstep(p["w"] + sw, p["w"] - sw, np.abs(a)) * sstep(p["h"] + s, p["h"] - s, np.abs(b)) * (d @ c > 0)
        if p.get("bars"):
            for f in (np.arange(p["bars"]) + 1) / (p["bars"] + 1):
                m = m * (1 - p.get("bar_dark", 0.9) * sstep(p.get("bar_w", 0.9), 0.3 * p.get("bar_w", 0.9), np.abs(a - (2 * f - 1) * p["w"])))
        if p.get("hbars"):
            for f in (np.arange(p["hbars"]) + 1) / (p["hbars"] + 1):
                m = m * (1 - p.get("bar_dark", 0.9) * sstep(p.get("bar_w", 0.9), 0.3 * p.get("bar_w", 0.9), np.abs(b - (2 * f - 1) * p["h"])))
        if p.get("grad"):
            m = m * np.clip(1.0 + p["grad"] * b / p["h"], 0.05, 3)
        E = E + (m * p["L"])[..., None] * np.array(p.get("rgb", [1, 1, 1]), np.float32)
    np.save(path, E.astype(np.float32))
    return path


def use_room():
    kit.room_env = paint_room


def lamp_field(dish, cam, seed, sep=14.0, L=(650.0, 1250.0), size=(0.55, 0.32), n=2500):
    """A museum case's many small lamps, one for each patch of the room the visible glaze can mirror, no two nearer than sep degrees.
    Only glaze whose mirror direction leaves the bowl is served: the rest mirrors the bowl's own far wall, and no lamp can reach it (measured with this profile: 8% of what shows leaves the bowl at elevation 66, 49% at 46).
    The film's satin lobe is about as wide as sep, so together they light its colour widely, while the glass shows each lamp only as one crisp point. Number and strength are estimates, by eye against ref/yohen/images/inaba_showcase_lighting_kokuyo.jpg."""
    from vessel import project

    rng = np.random.default_rng(seed)
    rl = dish.rho_lip
    R_, T_ = rng.uniform(0.3, rl - 0.2, n), rng.uniform(-np.pi, np.pi, n)
    P = dish.polar(R_, T_).reshape(-1, 3)
    N = np.asarray(dish.normal(R_ * np.cos(T_), R_ * np.sin(T_)), float).reshape(-1, 3)
    x, y, w = project(cam, P)
    v = np.array(cam["loc"], float) - P
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    cos = (N * v).sum(1)
    ok = (x > 0) & (x < 1) & (y > 0) & (y < 1) & (w > 0) & (cos > 0.05)
    r = 2 * cos[:, None] * N - v
    prof = dish.polar(np.linspace(0.0, rl, 800), np.zeros(800)).reshape(-1, 3)
    z_top, r_top = prof[:, 2].max(), prof[:, 0].max()
    keep = []
    for k in np.nonzero(ok)[0]:
        if r[k, 2] < 0.08:
            continue
        s = np.arange(0.15, 40.0, 0.15)[:, None]
        q = P[k] + s * r[k]
        rad = np.hypot(q[:, 0], q[:, 1])
        inside = (q[:, 2] < z_top + 0.1) & (rad < r_top + 0.1)
        last = int(np.argmin(inside)) if not inside.all() else len(s)
        if (q[:last, 2] < np.interp(rad[:last], prof[:, 0], prof[:, 2]) - 0.02).any():
            continue
        if all(np.degrees(np.arccos(np.clip(r[k].dot(j), -1, 1))) > sep for j in keep):
            keep.append(r[k])
    print("lamps", len(keep), "of", int(ok.sum()), "points", flush=True)
    return [{"dir": d.tolist(), "w": size[0] * rng.uniform(0.8, 1.3), "h": size[1] * rng.uniform(0.8, 1.3), "L": rng.uniform(*L), "rgb": [1.0, 0.97, 0.93], "round": 0.25} for d in keep]


def reflection_at(dish, cam, fx, fy, grid=500):
    """The direction in which the glaze at frame point (fx, fy) mirrors. Found by projecting the inside of the bowl."""
    from vessel import project

    rho = np.linspace(0.3, dish.rho_lip, grid)
    th = np.linspace(-np.pi, np.pi, 2 * grid)
    R_, T_ = np.meshgrid(rho, th)
    P = dish.polar(R_, T_).reshape(-1, 3)
    x, y, w = project(cam, P)
    i = int(np.argmin((x - fx) ** 2 + (y - fy) ** 2 + (w < 0) * 9.0))
    fX, fY = R_.ravel()[i] * np.cos(T_.ravel()[i]), R_.ravel()[i] * np.sin(T_.ravel()[i])
    n = dish.normal(np.array(fX), np.array(fY)).astype(float)
    v = np.array(cam["loc"], float) - P[i]
    v /= np.linalg.norm(v)
    return (2 * n.dot(v) * n - v), P[i], float(R_.ravel()[i])


def bubbles(dish, X, Y, seed, per_cm2=26.0, gap=0.05):
    """Air in the glass: a real sphere mesh, at random depth under the skin, sizes on a steep law. Numbers are ESTIMATES. Returns P for glaze_shader's `bubble` kind."""
    from glazekit import balls

    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = float(X.min()), float(X.max()), float(Y.min()), float(Y.max())
    n = int((x1 - x0) * (y1 - y0) * per_cm2)
    xs, ys = rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)
    keep = np.hypot(xs, ys) < dish.rho_lip - 0.9
    xs, ys = xs[keep], ys[keep]
    rad = np.clip(rng.pareto(2.2, len(xs)) * 0.0035 + 0.0022, 0.002, 0.016)
    depth = gap * rng.uniform(0.25, 0.75, len(xs))
    c = dish.surface(xs[None], ys[None], depth[None])[0]
    print("bubbles", len(c), flush=True)
    return balls(c, rad, nlon=10, nlat=7)


def front(**a):
    """studio_bpy.grid_mesh winds a face row-first, so a Dish grid (+y with the row, seen from above) shows the camera its back, and a backfacing dielectric uses 1/ior: past 42 degrees it turns into a total-reflection mirror with a sharp edge. Rows reversed, the faces look at the camera."""
    return {k: v[::-1] for k, v in a.items()}


def rest_of_bowl(dish, n_rho=400, n_th=1200, col=(0.006, 0.0052, 0.0048), under=0.03):
    """The whole bowl, coarse, just under the painted skin: it blocks what the far wall would mirror through the missing near wall, gives the outer wall at the sides, and casts the true shadow on the table."""
    rho = np.linspace(0.0, dish.L - 1e-3, n_rho, dtype=np.float32)
    th = np.linspace(-np.pi, np.pi, n_th, dtype=np.float32)
    R_, T_ = np.meshgrid(rho, th)
    X_, Y_ = R_ * np.cos(T_), R_ * np.sin(T_)
    P = dish.surface(X_, Y_, -under)
    return P, np.ones(P.shape, np.float32) * np.array(col, np.float32)
