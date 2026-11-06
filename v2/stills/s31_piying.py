"""Shot 31: a piece of a shadow puppet's robe, pressed against the lit white screen. Its curved hem is the arc.

    python3 -I v2/stills/s31_piying.py [preview|mid|final]

Built by the rules of the craft (from what is generally known of Shaanxi / Luanzhou pi ying; the layout itself is our own design, sizes are estimates):
- thin scraped hide, translucent, dyed with transparent red, green and black; undyed parts stay amber;
- everything is one connected piece: the pattern is what is left between knife cuts. Holes are willow-leaf slits and round punches, laid out along
  the lines of the drawing so that thin bridges of hide hold it together; density changes from band to band;
- bands parallel to the hem: an inked edge, a row of beads, a zig-zag; as main motif a band of ruyi clouds whose volutes are chains of slits; below, overlapping fish scales;
- bilaterally symmetric in design, cut by hand: both halves are cut separately, so no two slits are the same.
The sky of this shot is the screen itself, cream-white, as the table allows; it is the only way a shadow puppet reads.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

from kit import OUT, blur, color, fbm, frame_camera, shoot, sstep
from s21_lib import SHEETS, smooth1d, up

W = 11.0
RC = 27.0  # radius of the hem (cm)
LX, Z1, Z0 = 6.6, 0.2, -5.0  # the mesh, apex of the hem at z = 0


class Cut:
    """A sheet of hide and a knife. Motifs are given in (s, t): s along the hem from the axis (cm), t in from the hem (cm)."""

    def __init__(self, nx, ny, seed, side):
        self.nx, self.ny = nx, ny
        self.px = nx / (2 * LX)
        self.rng = np.random.default_rng(seed)
        self.side = side
        self.img = np.zeros((ny, nx), np.uint8)

    def xy(self, s, t):
        """(s, t) to raster pixels. The arc-length coordinate is mirrored for the left half."""
        s = np.asarray(s) * self.side
        t = np.asarray(t)
        th = s / RC
        r = RC - t
        x, z = r * np.sin(th), r * np.cos(th) - RC
        return np.stack([(x + LX) * self.px, (Z1 - z) * self.px], -1)

    def poly(self, s, t):
        p = self.xy(s, t)
        if p[..., 0].max() < -10 or p[..., 0].min() > self.nx + 10 or p[..., 1].max() < -10 or p[..., 1].min() > self.ny + 10:
            return
        cv2.fillPoly(self.img, [(p * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)

    def leaf(self, s0, t0, s1, t1, w=0.042, bend=0.0, k=1.0):
        """A willow-leaf slit from p0 to p1: pointed at both ends, each one its own. Over-cut tips run a little past the end."""
        r = self.rng
        s0, t0 = s0 + r.normal(0, 0.006), t0 + r.normal(0, 0.006)
        s1, t1 = s1 + r.normal(0, 0.006), t1 + r.normal(0, 0.006)
        w = w * k * r.uniform(0.82, 1.2)
        n = 12
        u = np.linspace(0, 1, n)
        ds, dt = s1 - s0, t1 - t0
        L = np.hypot(ds, dt) + 1e-6
        ns, nt = -dt / L, ds / L
        b = (bend + r.normal(0, 0.008)) * np.sin(np.pi * u)
        cs, ct = s0 + ds * u + ns * b, t0 + dt * u + nt * b
        prof = w * np.sin(np.pi * u) ** 0.75 * (1 + 0.1 * r.normal(0, 1, n))
        # one side of a cut is straighter than the other
        a = r.uniform(0.75, 1.0)
        S = np.concatenate([cs + ns * prof * a, (cs - ns * prof)[::-1]])
        T = np.concatenate([ct + nt * prof * a, (ct - nt * prof)[::-1]])
        self.poly(S, T)

    def punch(self, s, t, rad):
        r = self.rng
        a = np.linspace(0, 2 * np.pi, 14, endpoint=False)
        rr = rad * r.uniform(0.9, 1.1)
        self.poly(s + r.normal(0, 0.006) + rr * np.cos(a), t + r.normal(0, 0.006) + rr * np.sin(a))

    def chain(self, cs, ct, seg=0.2, gap=0.035, w=0.036, bendk=0.0):
        """Slits along a curve, with bridges: the curve is a polyline in (s, t), cut into leaves of unequal length."""
        r = self.rng
        d = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(cs), np.diff(ct)))])
        x = r.uniform(0, 0.03)
        while x < d[-1] - 0.03:
            L = seg * r.uniform(0.75, 1.25)
            e = min(x + L, d[-1])
            self.leaf(np.interp(x, d, cs), np.interp(x, d, ct), np.interp(e, d, cs), np.interp(e, d, ct), w=w, bend=bendk * (e - x))
            x = e + gap * r.uniform(0.8, 1.3)


def cut_half(nx, ny, seed, side):
    c = Cut(nx, ny, seed, side)
    S = np.linspace(0.0, 7.2, 400)
    r = c.rng

    # --- a line of slits parallel to the hem at t
    def line(t, seg, gap, w):
        c.chain(S, np.full_like(S, t), seg=seg, gap=gap, w=w)

    # the row of beads under the inked hem: alternating drop and punch, spacing with hand drift
    s = r.uniform(0, 0.05)
    while s < 7.2:
        c.punch(s, 0.215, 0.027)
        st = 0.13 * r.uniform(0.92, 1.08)
        c.leaf(s + 0.032, 0.215, s + st - 0.032, 0.215, w=0.02)
        s += st
    line(0.345, 0.2, 0.024, 0.01)

    # zig-zag band: triangles, cut alternately point in and point out
    s = r.uniform(-0.02, 0.02)
    # (a dark band with a row of small diamonds, a punch between each pair)
    while s < 7.3:
        q_ = 0.19 * r.uniform(0.95, 1.05)
        hw, hh = r.uniform(0.042, 0.052), r.uniform(0.075, 0.09)
        c.poly(np.array([s - hw, s, s + hw, s]) + r.normal(0, 0.004, 4), np.array([0.53, 0.53 - hh, 0.53, 0.53 + hh]) + r.normal(0, 0.004, 4))
        c.punch(s + q_ * 0.5, 0.45, 0.014)
        c.punch(s + q_ * 0.5, 0.61, 0.014)
        s += q_
    line(0.73, 0.22, 0.024, 0.011)

    # --- the band of ruyi clouds
    P = 2.46
    T0 = 1.32  # the height of the volutes
    for i in range(0, 4):
        s0 = i * P  # the axis of each cloud: the first on the centre line
        for sg in (1, -1):
            if i == 0 and sg == -1:
                continue
            cx, cy = s0 + sg * 0.53, T0
            # a volute: leather spiral whose gap is cut as a chain of slits
            ph = np.linspace(0.0, 2 * np.pi * 2.7, 360)
            rho = 0.47 * np.exp(-ph * 0.105)
            sign = -sg
            start = np.pi if sg > 0 else 0.0
            sp = cx + rho * np.cos(start + sign * ph)
            tp = cy + rho * np.sin(start + sign * ph)
            # chords of a tight spiral read as a polygon: slits get shorter as the curl tightens, and a knife follows the curve
            for lo, hi, sg_len in ((0.0, 0.42, 0.13), (0.42, 0.72, 0.075), (0.72, 1.0, 0.05)):
                a0, a1 = int(lo * 359), int(hi * 359) + 1
                c.chain(sp[a0:a1], tp[a0:a1], seg=sg_len, gap=0.018, w=0.0115, bendk=0.09 * sign)
            # the eye
            c.punch(cx + 0.012 * sg, cy, 0.016)
            # feathering outside the volute: short leaves along the normal of the spiral, getting longer on the outer turn
            pa = np.linspace(0.2, np.pi * 1.8, 70)
            for a in pa:
                a2 = start + sign * a
                rr = 0.47 * np.exp(-a * 0.105)
                if r.random() < 0.08:
                    continue
                L = r.uniform(0.09, 0.15)
                rs = rr + 0.04
                c.leaf(cx + rs * np.cos(a2), cy + rs * np.sin(a2), cx + (rs + L) * np.cos(a2 + 0.08 * sign), cy + (rs + L) * np.sin(a2 + 0.08 * sign), w=0.0085)
        # the lobe in the middle of the cloud head: a heart outlined by a chain, with a column of leaves
        if True:
            ts = np.linspace(0, 1, 60)
            for sg in (1, -1):
                if i == 0 and sg == -1 and side < 0:
                    continue
                c.chain(s0 + sg * 0.26 * np.sin(np.pi * ts) ** 0.8 + sg * 0.018, 0.86 + 0.35 * ts, seg=0.15, gap=0.02, w=0.0105)
            for t_ in np.arange(0.93, 1.16, 0.075):
                c.leaf(s0 + (0.02 if i else 0.012) + r.normal(0, 0.006), t_, s0 + 0.12 * (1 - (t_ - 0.93) / 0.25) + 0.03, t_ - 0.022, w=0.016)
            # the stem that joins cloud heads: a double chain sweeping down and out to the next cloud
            sw = np.linspace(0, 1, 120)
            sC = s0 + 0.08 + 2.28 * sw
            tC = 1.84 + 0.1 * np.sin(sw * np.pi * 2 + 1.1)
            c.chain(sC, tC, seg=0.22, gap=0.02, w=0.011)
            # triple drops in the gap between one cloud and the next
            gx = s0 + P * 0.5
            # a small fan of grass in the gap between one cloud and the next, its blades of unequal length
            # (lattice of small diamonds: the ground of the band between the cloud heads, tightly and evenly cut)
            for a_ in range(-7, 8):
                for b_ in range(-7, 8):
                    ds_, dt_ = (a_ + b_) * 0.073, 1.32 + (a_ - b_) * 0.073
                    if abs(ds_) + 0.42 * abs(dt_ - 1.32) > 0.3 or dt_ < 0.82 or dt_ > 1.8:
                        continue
                    hw, hh = r.uniform(0.024, 0.031), r.uniform(0.024, 0.031)
                    xx = gx + ds_ + r.normal(0, 0.004)
                    tt = dt_ + r.normal(0, 0.004)
                    c.poly(np.array([xx - hw, xx, xx + hw, xx]), np.array([tt, tt - hh, tt, tt + hh]))
    line(1.97, 0.2, 0.024, 0.011)

    # --- fish scales: rows offset by half; each scale outlined by a crescent, with a small seed inside
    t = 2.26
    row = 0
    while t < 5.6:
        w_ = 0.36 + 0.022 * row
        off = 0.0 if row % 2 == 0 else w_ * 0.5
        s = off + r.uniform(-0.015, 0.015)
        while s < 7.4:
            aa = np.linspace(np.pi * 1.1, np.pi * 1.9, 24)
            rr = w_ * 0.5
            cs, ct = s + rr * np.cos(aa), t - 0.26 * np.sin(aa) * 1.0 - 0.05
            # crescent with one bridge
            m = int(r.integers(9, 15))
            c.leaf(cs[0], ct[0], cs[m], ct[m], w=0.0145, bend=0.03 * np.sign(cs[m] - cs[0]))
            c.leaf(cs[m + 1], ct[m + 1], cs[-1], ct[-1], w=0.0145, bend=0.03 * np.sign(cs[-1] - cs[m + 1]))
            # the rib and a seed
            c.leaf(s, t + 0.02, s + r.normal(0, 0.01), t + 0.13, w=0.008)
            if r.random() < 0.75:
                c.punch(s - 0.11, t + 0.08, 0.013)
                c.punch(s + 0.11, t + 0.08, 0.013)
            s += w_ * r.uniform(0.97, 1.03)
        t += 0.26 + 0.012 * row
        row += 1
    return c.img


def main():
    q = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview")
    dens = {"preview": 0.5, "mid": 0.7, "final": 1.0}[q]
    d = os.path.join(OUT, "s31_piying")
    os.makedirs(d, exist_ok=True)
    seed = 31
    # the knife is drawn at 1.5x for clean edges at every quality
    pxcm = 2560 * dens / W * 1.25
    nx, ny = int(2 * LX * pxcm), int((Z1 - Z0) * pxcm)
    x = np.linspace(-LX, LX, nx, dtype=np.float32)
    z = np.linspace(Z1, Z0, ny, dtype=np.float32)
    X, Z = np.meshgrid(x, z)

    # both halves are cut separately (seeds differ): the same design, not the same cuts
    h1 = cut_half(nx, ny, seed + 1, 1)
    h2 = cut_half(nx, ny, seed + 2, -1)
    holes = np.maximum(h1 * (X >= 0), h2 * (X < 0)).astype(np.float32) / 255.0
    r = np.hypot(X, Z + RC)
    T = RC - r  # how far in from the hem
    S = RC * np.arctan2(X, Z + RC)

    # --- the hem: hand-cut, slightly wavy, and a couple of nicks; the dye runs a bit past its bands
    rng = np.random.default_rng(seed + 3)
    hem = 0.004 * up(fbm((4, 800), 800 / (2 * LX), 0.3, 1.8, 2.0, seed + 4), 1, nx, 1.0)[0] + 0.0025 * smooth1d(nx, 0.03 * pxcm + 0.8, rng)
    T = T + hem[None, :]
    body = sstep(-0.006, 0.006, T)
    hide = body * (1 - holes)

    # --- dyes, as optical densities. Bands soften into each other with a wash; the dye gathers at the edges of the bands
    wash = up(fbm((220, 500), 500 / (2 * LX), 0.25, 1.5, 1.9, seed + 5), ny, nx)
    wet = up(fbm((220, 500), 500 / (2 * LX), 0.06, 0.4, 1.6, seed + 6), ny, nx)
    fib = cv2.resize(fbm((ny // 2, nx // 2), pxcm / 2, 0.006, 0.05, 1.3, seed + 7), (nx, ny), interpolation=cv2.INTER_LINEAR)
    long_fib = cv2.resize(fbm((ny // 6, nx // 2), pxcm / 2, 0.03, 0.3, 1.5, seed + 8), (nx, ny), interpolation=cv2.INTER_LINEAR)
    tj = T + 0.0025 * wet
    black = np.maximum(sstep(0.13, 0.1, tj), sstep(0.38, 0.4, tj) * sstep(0.71, 0.69, tj))
    red = sstep(0.73, 0.76, tj) * sstep(1.97, 1.94, tj)
    # alternate: heads red, the stem at the bottom of the band green, and a yellow between
    green = sstep(1.97, 2.0, tj)
    # dark seams beside the bands
    seam = np.exp(-(((T - 1.97) / 0.022) ** 2)) + np.exp(-(((T - 0.73) / 0.018) ** 2))
    # the gaps between clouds carry green
    per = 2.46
    gapd = np.abs(((S + per / 2) % per) - per / 2)  # distance from the centre of a cloud
    # dye follows the drawing: a brush goes round each cloud head; what is left of the band is green
    dv = np.hypot(gapd - 0.53, T - 1.32)
    head = np.maximum(sstep(0.645, 0.625, dv + 0.003 * wet), sstep(0.56, 0.54, gapd + 0.003 * wet) * sstep(0.8, 0.86, T) * sstep(1.84, 1.78, T))
    band = red
    # (the whole band red: dyeing round each cloud head made badges)
    red = band
    # the eye of each volute rubbed to bare yellow hide, and red washed thin towards it
    eye = sstep(0.07, 0.05, dv) * band
    red = red * (1 - 0.92 * eye)
    amb = (0.42 + 0.12 * wash + 0.07 * long_fib)[..., None] * color([0.3, 0.85, 2.3])  # raw hide
    dye_k = 1 + 0.13 * wash + 0.1 * wet + 0.08 * fib
    density = amb + (red * dye_k)[..., None] * color([0.2, 2.6, 2.4]) + (green * dye_k)[..., None] * color([2.3, 0.95, 1.9]) + (black * (1 + 0.05 * fib))[..., None] * color([2.9, 3.0, 3.1])
    density = density + seam[..., None] * 0.55 * color([1.2, 1.3, 1.3])
    # the edge of every cut: the hide is thick there seen at an angle, and dye gathers. Darker in a thin line beside each hole
    # (a hard thin line, as the craftsman inks along each cut; not a glow)
    near = np.clip((blur(holes, 0.008 * pxcm) - 0.04) * 8.0, 0, 1)
    density = density * 1.55 + near[..., None] * 1.5 * color([1.0, 1.05, 1.1])
    # scratches and rubbed thin places
    trans = np.exp(-density)
    trans = np.where(hide[..., None] > 0.02, trans * hide[..., None] + (1 - hide[..., None]), 1.0)
    scat = np.power(np.exp(-density), 0.7) * 0.8
    tau = hide * (0.16 + 0.03 * long_fib)
    P = np.stack([X, 0.11 * up(fbm((220, 500), 500 / (2 * LX), 1.6, 8.0, 2.2, seed + 9), ny, nx) + 0.012 * wash, Z], -1).astype(np.float32)
    keep = (T > -0.02).astype(np.float32)
    np1 = os.path.join(d, f"mesh.{q}.npz")
    np.savez(np1, P=P, tau=np.clip(tau, 0, 2).astype(np.float32), scat=np.clip(scat, 0, 1).astype(np.float32), trans=np.clip(trans, 0, 1).astype(np.float32), mask=hide.astype(np.float32), keep=keep)

    # --- the screen: cotton cloth lit from behind by an oil lamp; a warm gradient, a little weave far out of focus
    ng = 1400
    xg = np.linspace(-24, 24, ng, dtype=np.float32)
    Xg, Zg = np.meshgrid(xg, xg + 2.0)
    glow = (np.exp(-(((Xg + 1.6) / 7.0) ** 2) - ((Zg + 1.5) / 5.0) ** 2) * 0.82 + 0.18) * 1.9
    un = up(fbm((512, 512), 512 / 48.0, 0.6, 5.0, 1.9, seed + 10), ng, ng)
    em = glow[..., None] * color([1.0, 0.62, 0.26]) * (1 + 0.04 * un)[..., None]
    np2 = os.path.join(d, f"screen.{q}.npz")
    np.savez(np2, P=np.stack([Xg, np.full_like(Xg, 1.3), Zg], -1).astype(np.float32), em=em.astype(np.float32))

    H = W * 9 / 16
    az, el = np.radians(9.0), np.radians(-20.0)
    view = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])
    target = np.array([0.0, 0.0, -(0.5 - 0.46) * H])
    cam = frame_camera(target, view, W, 42.0, aperture_mm=16.0, focus_point=[0.0, 0.0, -0.3])
    scene = {
        "camera": cam,
        "meshes": [
            {"name": "hide", "npz": np1, "shader_py": SHEETS, "params": {"kind": "sheet", "cut": True, "k_tau": 1.0, "front": 0.5, "k_gloss": 0.05, "rough": 0.42, "cos_min": 0.5}},
            {"name": "screen", "npz": np2, "material": {"Base Color": [0.0, 0.0, 0.0], "Roughness": 1.0, "Specular IOR Level": 0.0, "Emission Color": "em", "Emission Strength": 1.0}},
        ],
        "lights": [
            {"name": "rake", "loc": [-20, -6, 8], "target": [0, 0, -1], "size": [5, 5], "watts": 260, "rgb": [1.0, 0.9, 0.75]},
        ],
        "world": [0.001, 0.001, 0.0012],
        "bounces": 8,
        "diffuse_bounces": 2,
        "glossy_bounces": 2,
        "spp": {"preview": 96, "mid": 160, "final": 384},
    }
    look = {"exposure": -0.55, "contrast": 1.45, "saturation": 0.96, "black": 0.0, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "glare": 0.006, "vignette": 0.62}
    shoot("s31_piying", scene, q, develop=look)


main()
