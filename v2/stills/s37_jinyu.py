"""Shot 37: the tail of a red goldfish, lit from behind in black water. Its rays fan out towards the sunrise of shot 38.

    python3 -I v2/stills/s37_jinyu.py [preview|mid|final]            the still (t = 0)
    python3 -I v2/stills/s37_jinyu.py [preview|mid|final] --take=50  a moving take, 25 fps, in out/v2/s37_jinyu_take_<q>/

Built like the real thing (scale from general fish anatomy, not measured from a specimen):
- bony rays that fork two or three times on the way out, each a chain of short segments;
- a thin membrane between them, carrying star-shaped pigment cells that thin out towards a colourless margin;
- rays that run on a little past the membrane, and a few tears, so that the edge is not clean;
- a sheet that keeps its length along each arc: the excess at the margin has to fold, as it does in a real fin.

Reworked after blind review ("ray lines evenly spaced, red-orange gradient too clean, the white bar on the edge is hard"):
- rays at uneven spacing and of uneven weight, forks at scattered radii;
- two pigments in cells, red and yellow, each in its own patches; pigment goes by membrane sector, so a patch edge jumps at a ray, as in a sarasa fish; stipple at the patch edges; a few melanophores;
- each membrane sector sags by its own amount, so the sheet is pleated;
- folds stop short of edge-on, and the path length through the sheet is capped lower: the white bar was a fold seen edge-on.
All of these sizes and densities are estimates from general knowledge of fish fins and from looking at photographs, not measurements of a specimen. Background: the grey-black of the tank room.
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from kit import OUT, ROOT, blur, color, fbm, frame_camera, shoot, sstep

W = 7.5  # frame width at the subject (cm)
R = 7.0  # radius of the fan at the crown of the arc (cm)
R0 = 3.3  # where the mesh starts, below the frame
TH = 1.5  # half angle of the mesh (rad)


def smooth1d(n, sigma, rng):
    """Unit-variance smooth noise along one axis; sigma in samples."""
    x = rng.standard_normal(n + 8 * int(sigma + 1)).astype(np.float32)
    x = cv2.GaussianBlur(x[None, :], (0, 0), float(sigma), borderType=cv2.BORDER_REFLECT)[0][4 * int(sigma + 1) :][:n]
    return (x - x.mean()) / (x.std() + 1e-9)


NY0, NX0 = 440, 1760  # the fixed grid of everything large-scale, so that a seed gives one composition at every quality


def coarse0(lo, hi, beta, seed, k=1):
    """Low-frequency noise on the fixed grid; k elongates it along the rays. Periodic, so that it can slide."""
    return fbm((NY0 // k, NX0), NX0 / (2 * TH * R), lo, hi, beta, seed)


def opened(f, ny, nx):
    return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)


def coarse(ny, nx, lo, hi, beta, seed, k=1):
    return opened(coarse0(lo, hi, beta, seed, k), ny, nx)


# --- the motion: slow motion of a tail in still water; at t = 0 the fin is the still ------------------------------
LAM, PERIOD = 5.0, 1.6  # the bending wave that runs out along the rays: wavelength (cm), period (s)
FOLD_SWAY, FAN_SWAY, RIPPLE = 0.55, 0.035, 0.28  # sideways sway of the folds (cm), of the fan (rad), out of plane (cm)


def wave(r, t, phase=0.0):
    return np.sin(2 * np.pi * (r / LAM - t / PERIOD) + phase)


def slid(f, t, drift):
    """A fold field at time t: it drifts sideways (cm/s), and its folds sway with the wave running out along the rays."""
    rows, cols = f.shape
    rr = np.linspace(R0, R + 0.42, rows, dtype=np.float32)
    u = (rr - R0) / (R - R0)
    shift = (drift * t + FOLD_SWAY * u**2 * (wave(rr, t) - wave(rr, 0.0))) * NX0 / (2 * TH * R)
    X = (np.arange(cols, dtype=np.float32)[None, :] - shift[:, None]).astype(np.float32)
    Y = np.repeat(np.arange(rows, dtype=np.float32)[:, None], cols, 1)
    return cv2.remap(f, X, Y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)


def stretched(ny, nx, pxcm, lo, hi, beta, seed, k):
    """Noise elongated along the rays by a factor k: generated on a squeezed grid, then opened up along r."""
    f = fbm((max(ny // k, 4), nx), pxcm, lo, hi, beta, seed)
    return cv2.resize(f, (nx, ny), interpolation=cv2.INTER_CUBIC)


# --- the rays ---------------------------------------------------------------------------------------------------
def segments(r, rng, start=None):
    """Joints along a ray as a 1-D field on r (1 at a joint); segments get shorter towards the margin."""
    dr = float(r[1] - r[0])
    width = max(0.0035, 0.8 * dr)
    j = np.zeros(r.size, np.float32)
    x = float(r[0] if start is None else start) + rng.uniform(0, 0.05)
    while x < r[-1]:
        i = int((x - r[0]) / dr)
        n = int(3 * width / dr) + 1
        a, b = max(i - n, 0), min(i + n + 1, r.size)
        j[a:b] = np.maximum(j[a:b], np.exp(-(((r[a:b] - x) / width) ** 2)))
        x += (0.105 - 0.062 * x / R) * rng.uniform(0.82, 1.18)
    return j


def grow_rays(r, seed):
    """All rays as paths from base to margin; rays that fork share their path up to the fork."""
    rng = np.random.default_rng(seed)
    rng_j = np.random.default_rng(seed + 1000)
    rf = np.linspace(r[0], r[-1], 700, dtype=np.float32)  # paths live on a fixed grid
    wob_sigma = 0.8 / float(rf[1] - rf[0])
    leaves = []

    def grow(path, lo, hi, gen, rlast, j, forks):
        rb = np.array([0.46, 0.69, 0.85, 0.95])[min(gen, 3)] * R + rng.normal(0, 0.085 * R)
        rb = max(rb, rlast + 0.35)
        if gen >= 3 or rb > 0.975 * R:
            leaves.append((path, j, forks))
            return
        length = rng.uniform(1.3, 2.4)
        mid = lo + (hi - lo) * rng.uniform(0.3, 0.7)
        ramp = sstep(rb, rb + length, rf).astype(np.float32)
        for a, b in ((lo, mid), (mid, hi)):
            c = 0.5 * (a + b)
            child = path + ramp * c + 0.0022 * smooth1d(rf.size, wob_sigma, rng) * ramp
            jc = j.copy()
            after = r >= rb
            jc[after] = segments(r, rng_j, start=rb)[after]
            grow(child, a - c, b - c, gen + 1, rb, jc, forks + sstep(rb, rb + 0.4, rf).astype(np.float32))

    dth = 0.092
    th = -TH - 0.1
    while th < TH + 0.1:
        c = th + rng.normal(0, 0.1 * dth)
        path = c + 0.0035 * smooth1d(rf.size, 1.5 * wob_sigma, rng)
        step = dth * float(np.clip(rng.lognormal(0.0, 0.34), 0.5, 1.9))
        grow(path, -step / 2, step / 2, 0, r[0], segments(r, rng_j), np.zeros(rf.size, np.float32))
        th += step

    paths = np.stack([np.interp(r, rf, p) for p, _, _ in leaves]).astype(np.float32)
    joints = np.stack([j for _, j, _ in leaves])
    forks = np.stack([np.interp(r, rf, f) for _, _, f in leaves]).astype(np.float32)
    order = np.argsort(paths[:, -1])
    return paths[order], joints[order], forks[order]


# --- pigment cells ----------------------------------------------------------------------------------------------
def star_kernels(px, n, rng):
    """Stellate cells: a small body and a few fine dendrites; px = the cell's overall radius in pixels."""
    m = int(np.ceil(px * 1.25))
    size = 2 * m + 1
    out = []
    for _ in range(n):
        img = np.zeros((size, size), np.float32)
        for _ in range(rng.integers(4, 8)):
            a = rng.uniform(0, 2 * np.pi)
            L = px * rng.uniform(0.55, 1.15)
            p1 = (int(m * 8), int(m * 8))
            mid = (int((m + 0.5 * L * np.cos(a + rng.normal(0, 0.3))) * 8), int((m + 0.5 * L * np.sin(a + rng.normal(0, 0.3))) * 8))
            p2 = (int((m + L * np.cos(a)) * 8), int((m + L * np.sin(a)) * 8))
            cv2.polylines(img, [np.array([p1, mid, p2], np.int32)], False, 0.55, 1, cv2.LINE_AA, shift=3)
        Y, X = np.ogrid[-m : m + 1, -m : m + 1]
        img = np.maximum(img, np.exp(-(X**2 + Y**2) / (2 * (0.22 * px + 0.3) ** 2)))
        out.append(cv2.GaussianBlur(img, (0, 0), 0.45))
    return out


def pigment_cells(shape, pxcm, per_cm2, density, seed):
    rng = np.random.default_rng(seed)
    ny, nx = shape
    field = np.zeros(shape, np.float32)
    kernels = star_kernels(max(0.0085 * pxcm, 1.6), 6, rng)
    total = int(nx * ny / pxcm**2 * per_cm2)
    for k in kernels:
        n = total // len(kernels)
        x, y = rng.integers(0, nx, n), rng.integers(0, ny, n)
        keep = rng.random(n) < density[y, x]
        seeds = np.zeros(shape, np.float32)
        seeds[y[keep], x[keep]] = rng.uniform(0.5, 1.0, int(keep.sum()))
        field = np.maximum(field, cv2.filter2D(seeds, -1, k, borderType=cv2.BORDER_REFLECT))
    return field


# --- the fin ----------------------------------------------------------------------------------------------------
def material(dens, seed=7, fold=1.0):
    """Everything that belongs to the tissue and moves with it: made once. pose() makes the shape of each frame."""
    nx, ny = int(7000 * dens), int(1750 * dens)
    r = np.linspace(R0, R + 0.42, ny, dtype=np.float32)
    th = np.linspace(-TH, TH, nx, dtype=np.float32)
    pxcm = nx / (2 * TH * R)
    shape = (ny, nx)
    Rr = r[:, None]
    rng = np.random.default_rng(seed + 100)

    # --- nearest ray for every vertex, one row at a time (rays never cross, so the row is sorted)
    paths, joints, forks = grow_rays(r, seed)
    nk = paths.shape[0]
    w_ray = 0.0205 * (1.0 - 0.42 * (r - R0) / (R - R0))[None, :] * 0.73 ** forks[:, :]  # half-width (cm)
    rr_w = np.random.default_rng(seed + 103)
    w_ray = w_ray * np.clip(rr_w.lognormal(-0.08, 0.42, (nk, 1)), 0.42, 1.95).astype(np.float32)
    ray_weight = np.clip(rr_w.lognormal(-0.1, 0.5, nk), 0.3, 1.6).astype(np.float32)  # how dense a ray's bone and pigment are

    top = np.maximum.accumulate(paths[:, -1])
    k = np.clip(np.searchsorted(top, th), 1, nk - 1)
    dl, dr = th - top[k - 1], top[k] - th
    gap_top = (dl + dr) * R
    t_top = np.clip(np.minimum(np.abs(dl), np.abs(dr)) / (0.5 * (dl + dr) + 1e-6), 0, 1)
    th_f = np.linspace(-TH, TH, 4000)
    R_low = R * (1.0 + 0.016 * smooth1d(4000, 0.35 / (2 * TH / 4000), rng) + 0.006 * smooth1d(4000, 0.08 / (2 * TH / 4000), rng))
    R_low = np.interp(th, th_f, R_low).astype(np.float32)
    fine = smooth1d(nx, 0.0035 / (2 * TH / nx) + 0.8, np.random.default_rng(seed + 101))
    R_mem = R_low - 0.16 * np.minimum(gap_top, 0.4) * t_top**2 + 0.006 * fine
    i_top = np.clip(np.searchsorted(th, top), 0, nx - 1)
    tips = R_low[i_top] + rng.uniform(0.0, 0.1, nk) ** 1.5 * 0.9

    dist, signed, gap, width, joint, tipfade = [np.zeros(shape, np.float32) for _ in range(6)]
    sector = np.zeros(shape, np.int32)
    ray_id = np.zeros(shape, np.int32)
    for i in range(ny):
        c = np.maximum.accumulate(paths[:, i])
        k = np.clip(np.searchsorted(c, th), 1, nk - 1)
        dl, dr = th - c[k - 1], c[k] - th
        near = np.where(np.abs(dl) < np.abs(dr), k - 1, k)
        s = np.where(np.abs(dl) < np.abs(dr), dl, -dr) * r[i]
        dist[i], signed[i], gap[i] = np.abs(s), s, (dl + dr) * r[i]
        sector[i], ray_id[i] = k, near
        taper = 0.3 + 0.7 * sstep(tips[near], tips[near] - 0.3, r[i])
        width[i] = w_ray[near, i] * taper
        joint[i] = joints[near, i]
        tipfade[i] = sstep(tips[near], tips[near] - 0.05, r[i])

    t_mid = np.clip(dist / (0.5 * gap + 1e-5), 0, 1)
    x_ray = dist / (width + 1e-5)
    ray = sstep(1.0, 0.72, x_ray) * tipfade
    groove = np.exp(-((x_ray / 0.2) ** 2))  # a ray is two half-rays side by side

    # --- the membrane: where it ends, and a few tears that run in along the rays
    mem = sstep(R_mem[None, :] + 0.005, R_mem[None, :] - 0.005, Rr)
    rng_t = np.random.default_rng(seed + 102)
    for _ in range(10):
        a = int(rng.integers(0, nk - 1))
        depth, w0 = 0.12 + 0.9 * rng.uniform(0, 1) ** 2.2, rng.uniform(0.012, 0.045)
        ia = int(np.clip(np.searchsorted(th, 0.5 * (paths[a, -1] + paths[a + 1, -1])), 0, nx - 1))
        r_in = R_mem[ia] - depth
        jag = 1.0 + 0.32 * smooth1d(ny, 0.018 / float(r[1] - r[0]) + 0.8, rng_t)
        for i in np.nonzero(r > r_in)[0]:
            hw = max((w0 * ((r[i] - r_in) / depth) ** 1.25 + 0.002) * jag[i], 0.0008)  # jag can go negative: that once cut a whole row of the sheet
            d = np.abs(th - 0.5 * (paths[a, i] + paths[a + 1, i])) * r[i]
            mem[i] *= sstep(hw * 0.6, hw, d)

    # --- pigment: two kinds, in cells, in patches. A patch goes by membrane sector, so that its edge jumps at a ray (a sarasa fish is like this)
    n_soft = coarse(ny, nx, 0.4, 3.0, 2.6, seed + 1)
    patch_a = coarse(ny, nx, 0.5, 4.5, 2.7, seed + 41, 4)  # stretched along the rays
    patch_b = coarse(ny, nx, 0.25, 2.2, 2.4, seed + 42, 3)
    rs = np.random.default_rng(seed + 43)
    jump = np.cumsum(rs.normal(0, 0.16, nk + 1) + (rs.random(nk + 1) < 0.08) * rs.normal(0, 1.1, nk + 1))
    jump = jump - cv2.GaussianBlur(jump[None, :].astype(np.float32), (0, 0), 7.0, borderType=cv2.BORDER_REFLECT)[0]
    sec_r = np.exp(0.36 * jump).astype(np.float32)[sector]
    sec_y = np.exp(0.3 * rs.normal(0, 1, nk + 1)).astype(np.float32)[sector]
    red = sstep(1.03 * R, 0.66 * R, Rr + 0.62 * patch_a + 0.18 * patch_b) * (0.5 + 0.5 * sstep(-1.1, 0.2, patch_b + 0.5 * patch_a))
    red = np.clip(red * sec_r, 0.0, 1.5)
    yel = sstep(1.1 * R, 0.68 * R, Rr + 0.42 * coarse(ny, nx, 0.4, 3.2, 2.6, seed + 44, 3)) * sec_y
    n_blot = fbm(shape, pxcm, 0.03, 0.5, 2.0, seed + 2)
    # cells gather: a parent process in small clusters, so that the stipple is not an even dust
    clump = sstep(-0.8, 1.2, fbm(shape, pxcm, 0.04, 0.3, 1.6, seed + 45))
    red_cells = pigment_cells(shape, pxcm, 16000, np.clip((0.2 + 0.8 * red) * clump + 0.02, 0, 1), seed + 3)
    yel_cells = pigment_cells(shape, pxcm, 11000, np.clip((0.25 + 0.75 * yel) * (1.2 - clump) * 0.8, 0, 1), seed + 46)
    mel_place = sstep(1.5, 2.3, coarse(ny, nx, 0.25, 1.4, 2.2, seed + 47))  # melanophores: rare, in a few small groups
    mel = pigment_cells(shape, pxcm, 240, np.clip(mel_place + 0.004, 0, 1), seed + 48)
    # blood runs beside each ray in the inner part of the fin
    v_w = max(0.0032, 0.75 / pxcm)
    vessel = np.exp(-(((np.abs(signed) - width * 1.25) / v_w) ** 2)) * sstep(0.86 * R, 0.62 * R, Rr) * (0.6 + 0.4 * sstep(-1, 1, n_blot))
    rw = ray_weight[ray_id]
    pig_r = 2.3 * red**1.3 + 0.6 * red_cells * (0.25 + 0.75 * np.minimum(red, 1.0)) + ray * rw * (0.18 + 0.5 * np.minimum(red, 1.0))
    pig_y = 1.0 * yel**1.2 + 0.5 * yel_cells * np.minimum(yel, 1.0) + ray * rw * 0.2
    sig_r, sig_y = color([0.16, 1.45, 3.1]), color([0.02, 0.26, 2.0])
    trans = np.exp(-pig_r[..., None] * sig_r - pig_y[..., None] * sig_y - (mel * 1.1)[..., None]) * color([1.0, 0.985, 0.95])
    trans = trans * (1.0 - vessel[..., None] * color([0.05, 0.55, 0.7]) * 0.3)
    scat = np.power(trans, 0.8) * color([1.0, 0.76, 0.48])

    # --- how much it scatters: the rays much more than the membrane; fine fibres near the margin
    fib = stretched(ny, nx, pxcm, 0.012, 0.07, 1.4, seed + 4, 14)
    glass = 0.3 + 0.7 * sstep(R_mem[None, :], R_mem[None, :] - 1.1, Rr)  # the margin is nearly clear
    t_mem = (0.27 - 0.08 * sstep(0.6 * R, 1.0 * R, Rr)) * glass * (1.0 + 0.05 * n_blot + 0.1 * fib * sstep(0.7 * R, R, Rr)) * (1.0 + 0.35 * (1.0 - t_mid) ** 2)
    t_ray = (0.5 - 0.3 * sstep(0.6 * R, R, Rr) + 0.05 * fib) * (0.55 + 0.45 * rw) * (1.0 - 0.3 * groove) * (1.0 - 0.3 * joint) * (0.7 + 0.3 * (width / 0.014).clip(0, 1))
    tau = mem * t_mem
    tau = tau * (1.0 - ray) + ray * t_ray
    tau = np.maximum(tau, 0.0)
    mask = np.maximum(mem, ray)

    # --- the sheet: every arc keeps its length, so that the excess at the margin folds
    u = (Rr - R0) / (R - R0)
    calm = 0.62 + 0.38 * sstep(-0.5, 0.8, coarse(ny, nx, 3.5, 9.0, 2.0, seed + 8, 3))
    # relief, along the local normal: rays stand proud, the membrane sags between them
    sag = np.exp(0.5 * rs.normal(0, 1, nk + 1)).astype(np.float32)[sector]
    h = blur(0.006 * ray * (1.0 - 0.3 * groove) * (1.0 - 0.45 * joint) - (0.004 + 0.012 * sstep(0.2, 1.0, u)) * sag * t_mid**2 * mem, 0.6)
    return {
        "nx": nx, "ny": ny, "pxcm": pxcm, "th": th, "Rr": Rr, "u": u, "h": h,
        "amp": (0.2 + 1.2 * sstep(0.1, 1.0, u)) * calm * fold,
        "g1": (coarse0(1.5, 4.5, 2.4, seed + 5, 8), coarse0(1.5, 4.5, 2.4, seed + 205, 8)),
        "g2": (coarse0(0.42, 1.1, 2.0, seed + 6, 5), coarse0(0.42, 1.1, 2.0, seed + 206, 5)),
        "attrs": {"tau": tau.astype(np.float32), "scat": scat.astype(np.float32), "trans": (trans * mask[..., None] + (1.0 - mask[..., None])).astype(np.float32), "mask": mask.astype(np.float32)},
    }  # fmt: skip


def pose(m, t):
    """The shape of the sheet at time t. Every arc keeps its length, so that the excess at the margin folds."""
    nx, ny, th, Rr, u, h = m["nx"], m["ny"], m["th"], m["Rr"], m["u"], m["h"]

    def folds(pair, period, drift):
        a = 2 * np.pi * t / period
        return opened(np.cos(a) * slid(pair[0], t, drift) + np.sin(a) * slid(pair[1], t, drift), ny, nx)

    phi = m["amp"] * (folds(m["g1"], 7.0, 0.45) + 0.3 * sstep(0.55, 1.0, u) * folds(m["g2"], 2.6, 0.7))
    phi = 0.98 * np.tanh(phi / 0.98)
    ds = (2 * TH / (nx - 1)) * Rr
    T = np.cumsum((np.cos(phi) - 1.0) * ds, axis=1)
    D = np.cumsum(np.sin(phi) * ds, axis=1)
    T -= T[:, nx // 2 : nx // 2 + 1]
    # the drift of the integral across the fan is not a fold
    small = cv2.resize(D, (nx // 8, ny // 8), interpolation=cv2.INTER_AREA)
    wide = cv2.GaussianBlur(small, (int(18 * m["pxcm"] / 8) | 1, 1), 3.0 * m["pxcm"] / 8, borderType=cv2.BORDER_REPLICATE)
    D -= cv2.resize(wide, (nx, ny), interpolation=cv2.INTER_LINEAR)
    T = T - h * np.sin(phi)
    D = D + h * np.cos(phi)

    # the rays bend: the tips of the fan lag behind its base
    a = th[None, :] + T / Rr + FAN_SWAY * u**1.5 * (wave(Rr, t) - wave(Rr, 0.0))
    x = Rr * np.sin(a)
    z = Rr * np.cos(a)
    # the whole fin leans away from the camera towards its margin and curves gently across; the wave crosses it at a slant
    slant = 0.35 * Rr * np.sin(th[None, :])
    y = D + 0.16 * (Rr - R) + 0.035 * x**2 + RIPPLE * u**2 * (wave(Rr, t, slant) - wave(Rr, 0.0, slant))
    return np.stack([x, y, z], -1).astype(np.float32)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seed = next((int(a[7:]) for a in sys.argv if a.startswith("--seed=")), 64)
    take = next((int(a[7:]) for a in sys.argv if a.startswith("--take=")), 0)
    q = args[0] if args else "preview"
    dens = {"preview": 0.4, "mid": 0.6, "final": 1.0}[q]
    d = os.path.join(OUT, "s37_jinyu")
    os.makedirs(d, exist_ok=True)
    fin = material(dens, seed=seed)
    npz, npz2 = os.path.join(d, f"mesh.{q}.npz"), os.path.join(d, f"mesh2.{q}.npz")

    def write_meshes(t):
        P = pose(fin, t)
        np.savez(npz, P=P, **fin["attrs"])
        return P

    P = write_meshes(0.0)

    apex_y = 0.36
    H_frame = W * 9.0 / 16.0
    az, el = np.radians(5.0), np.radians(-13.0)
    view = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])
    target = np.array([0.0, 0.0, R - (0.5 - apex_y) * H_frame])
    i, j = int(P.shape[0] * (R - 0.25 - R0) / (R + 0.42 - R0)), P.shape[1] // 2
    fin_params = {"k_tau": 1.0, "front": 0.12, "k_gloss": 0.05, "rough": 0.34, "cos_min": 0.42}
    cam = frame_camera(target, view, W, 34.0, aperture_mm=8.0, focus_point=P[i, j])
    scene = {
        "camera": cam,
        "meshes": [{"name": "fin", "npz": npz, "shader_py": os.path.join(ROOT, "v2", "stills", "s37_shader.py"), "params": fin_params}],  # the second lobe was never lit: against the grey it only cast a dark shape
        "lights": [
            {"name": "rake", "loc": [-26, 9, 11], "target": [0, 0, 6], "size": [10, 14], "watts": 10000, "rgb": [1.0, 0.92, 0.8]},
            {"name": "sun", "loc": [2, 18, 16], "target": [0, 0, 6], "size": [14, 14], "watts": 9000, "rgb": [1.0, 0.9, 0.76], "hide_in_gloss": True},
            {"name": "low", "loc": [12, 12, 0], "target": [0, 0, 5], "size": [14, 8], "watts": 1800, "rgb": [1.0, 0.72, 0.5]},
            {"name": "sheen", "loc": [-14, -20, 22], "target": [0, 0, 6], "size": [18, 18], "watts": 350, "rgb": [0.92, 0.95, 1.0]},
        ],
        "world": [0.0007, 0.0009, 0.0016],
        "sky": {"top": [0.0065, 0.0065, 0.0068], "glow": [0.017, 0.017, 0.0175], "h": 0.62, "mottle": 0.12, "x0": 0.5, "y0": 0.42, "seed": 37},
        "bounces": 10,
        "diffuse_bounces": 3,
        "glossy_bounces": 2,
        "spp": {"preview": 96, "mid": 160, "final": 384},
    }
    look = {"exposure": 1.05, "contrast": 1.3, "saturation": 1.08, "black": 0.002, "grain": 1.2, "sharpen": 0.25, "halation": 0.03, "glare": 0.002}
    if not take:
        shoot("s37_jinyu", scene, q, tag=f"{q}.s{seed}" if seed != 64 else q, develop=look)
        return

    # a take: the camera, the lights and the render seed stay put, the fin moves, the grain changes on every frame
    name = f"s37_jinyu_take_{q}" + os.environ.get("S37_SUFFIX", "")  # a suffix keeps a new take out of the folder the film reads, until it has been checked
    if os.environ.get("S37_SPP"):
        scene["spp"] = {q: int(os.environ["S37_SPP"])}
    for i in range(take):
        if os.path.exists(os.path.join(OUT, name, f"f{i:03d}.png")):  # resume: the fin's motion and the seed are fixed, so a frame already made is the same frame
            continue
        write_meshes(i / 25.0)
        shoot(name, json.loads(json.dumps(scene)), q, tag=f"f{i:03d}", develop={**look, "seed": i + 1})
    clip = os.path.join(OUT, name, "take.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25", "-i", os.path.join(OUT, name, "f%03d.png"), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", clip], check=True)
    print(clip)


main()
