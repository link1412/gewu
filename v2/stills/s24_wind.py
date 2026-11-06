"""Shot 24: a light wind skims the blue cloth and the paper-cut answers. Writes a displacement stack for kit/studio's `deform`; nothing here renders.

    python3 -I v2/stills/s24_wind.py [--h=0.02] [--out=PATH] [--seed=N] [--frames=24]

Needs out/v2/s24_jianzhi/paper.final.npz (python3 -I v2/stills/s24_jianzhi.py final): the plate's shape is the shot's real alpha, and missing data is an error.

The solve, on a coarse grid (cell h, default 0.2 mm, about 580 x 260), all of it numpy/scipy and no sine waves:
- a Kirchhoff plate: rho w_tt + c(gap) w_t + div div (D grad grad w) = p(x,y,t) - rho g, with a floor at w = 0, semi-implicit, one sparse factorisation reused every step.
  w is measured from the sheet's own rest shape (its creases and lifts are in the npz), so the floor is "it cannot go below where it lies". Paper never gets lower than its rest z, and that z is above the cloth (the script checks it).
- the cut shape sets the softness: each bending stencil takes D times the smallest paper coverage among its nodes, so a thin bridge is a soft hinge, a thick field is stiff. Mass and load also go with coverage.
- contact: a soft floor under the rest shape (kf, about 0.05 mm under its own weight; the frames written are measured from that resting level and never negative). Friction is only used below, for the in-plane part.
- wind: moving dynamic pressure q = 1/2 rho_air U^2. U has low-frequency gusts travelling across the sheet at the convection speed, and advected eddies. Air gets under the paper only from
  windward-facing edges, so the load is q times an upstream exposure of the holes, whose reach grows as the gap opens; a lifted part facing the wind gets more (angle of attack), one facing away is pushed down.
- air damping: a linear free-air term, set larger than the plain flow estimate so that the paper does not flicker (an artistic choice within a factor of a few), plus a squeeze film under small gaps ~ 1/(gap + g0)^3, clamped to what the factorisation holds; the part above the clamp is lost, the part below is lagged on the right hand side, which acts like a little extra mass.
- inextensibility, approximately: each output frame solves one least-squares membrane problem for the in-plane drift that cancels the small-slope stretch 1/2 w_x^2 etc; cells in contact are anchored (friction). So a flap that rises also pulls in.

ESTIMATED, not measured (all from general knowledge of thin paper; tuned until it moved like paper): D = 4 dyn cm (a thin 25 um sheet at about 0.3 GPa, softened by handling and folding; D is the softest-looking estimate here, chosen by how it moves); areal density 40 g/m2 (0.004 g/cm2), +50 % added air mass;
U0, gust times, exposure and attack coefficients, squeeze-film length, free-air damping. Not simulated: air flow itself, self contact, paper's creases as softer lines, any motion of the cloth.
Units: cm, g, s; pressure in dyn/cm2 (weight of this paper = 3.9).
"""

import os
import sys
import time

import cv2
import numpy as np
import scipy.ndimage as ndi
import scipy.sparse as sp
import scipy.sparse.linalg as spl

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2", "s24_jianzhi")
X0, X1, Y0, Y1 = -5.8, 5.8, -5.0, 5.4  # the npz's plane, from s24_jianzhi.py
YTOP = 0.3  # nothing above: the rim's apex is at 0.2 and the paper ends there
VIEW = (-4.1, 4.1, -3.5, 0.3)  # what the frame sees, roughly

ARG = {"h": 0.02, "D": 4.0, "U0": 220.0, "rho": 0.004, "added": 0.002, "Ce": 5.0, "Cb": 0.03, "Ca": 0.8, "cair": 0.6, "Cbar": 1.0, "Lsq": 0.35, "g0": 0.012, "dt": 0.004, "spin": 1.2, "frames": 24, "seed": 11, "wx": 0.82, "wy": -0.57, "conv": 0.4, "tb": 0.25, "wv": 0.15, "kf": 800.0, "sigH": 1.5, "ell0": 0.35, "ell1": 0.7}
out_path = os.path.join(OUT, "wind.npy")
for a in sys.argv[1:]:
    k, v = a.lstrip("-").split("=")
    if k == "out":
        out_path = v
    else:
        ARG[k] = type(ARG[k])(v)
H = ARG["h"]
DT = ARG["dt"]
RHO = ARG["rho"] + ARG["added"]
GRAV = ARG["rho"] * 980.0  # weight only sees the paper's own mass
AIR = 1.2e-3
MU = 1.8e-4
WIND = np.array([ARG["wx"], ARG["wy"]]) / np.hypot(ARG["wx"], ARG["wy"])


def load_sheet():
    p = os.path.join(OUT, "paper.final.npz")
    if not os.path.exists(p):
        raise SystemExit(f"missing {p}: run s24_jianzhi.py final first")
    d = np.load(p)
    alpha, P = d["alpha"], d["P"]
    ny, nx = alpha.shape
    pxcm = nx / (X1 - X0)
    nodes_x = X0 + H * np.arange(int(round((X1 - X0) / H)) + 1)
    nodes_y = Y0 + H * np.arange(int(round((YTOP - Y0) / H)) + 1)
    size = max(int(round(H * pxcm)) | 1, 1)
    cover = cv2.blur(alpha, (size, size))
    # rows of the npz run down in y
    jj = np.clip(((Y1 - nodes_y) * pxcm - 0.5).round().astype(int), 0, ny - 1)
    ii = np.clip(((nodes_x - X0) * pxcm - 0.5).round().astype(int), 0, nx - 1)
    return cover[np.ix_(jj, ii)].astype(np.float64), nodes_x, nodes_y, P, d["alpha"]


def check_cloth(P, alpha):
    """Paper at rest must be above the cloth, or w >= 0 does not mean what it says."""
    p = os.path.join(OUT, "cloth.final.npz")
    if not os.path.exists(p):
        raise SystemExit(f"missing {p}")
    Pc = np.load(p)["P"]
    zc = cv2.resize(Pc[..., 2], (P.shape[1], P.shape[0]), interpolation=cv2.INTER_LINEAR)
    gap = P[..., 2] - zc
    m = alpha > 0.5
    print(f"rest gap paper-cloth: min {gap[m].min():.4f} cm, p1 {np.percentile(gap[m], 1):.4f}, median {np.median(gap[m]):.4f}", flush=True)
    if gap[m].min() < 0:
        print(f"WARNING: {float((gap[m] < 0).mean()) * 100:.3f} % of the paper already below the cloth at rest", flush=True)


def active_mask(c):
    a = c > 0.04
    a[:, 0] = a[:, -1] = True  # not free ends: the sheet goes on outside the plane, see pin below
    while True:
        # a node takes part only if some stencil holds it: three in a row or a full quad
        xx = a[:, :-2] & a[:, 1:-1] & a[:, 2:]
        yy = a[:-2] & a[1:-1] & a[2:]
        q = a[:-1, :-1] & a[1:, :-1] & a[:-1, 1:] & a[1:, 1:]
        held = np.zeros_like(a)
        for k in range(3):
            held[:, k : k + xx.shape[1]] |= xx
            held[k : k + yy.shape[0]] |= yy
        for dj in (0, 1):
            for di in (0, 1):
                held[dj : dj + q.shape[0], di : di + q.shape[1]] |= q
        b = a & held
        if (b == a).all():
            break
        a = b
    lab, n = ndi.label(a, structure=np.ones((3, 3)))
    if n == 0:
        raise SystemExit("no paper")
    sizes = ndi.sum(a, lab, range(1, n + 1))
    keep = lab == (1 + int(np.argmax(sizes)))
    print(f"active: {int(keep.sum())} of {a.size} nodes; {n - 1} small islands left to follow their neighbours ({int(a.sum() - keep.sum())} nodes)", flush=True)
    return keep


def plate_matrix(c, a, idx):
    """K: stiffness from the bending stencils, weights D * min coverage."""
    D0 = ARG["D"]
    rows, cols, vals = [], [], []

    def stencil(nodes, weights, coefs):
        # energy 1/2 w (sum coef_i w_i)^2; assemble coef_i coef_j w
        n = len(coefs)
        for p in range(n):
            for q in range(n):
                rows.append(nodes[p])
                cols.append(nodes[q])
                vals.append(weights * coefs[p] * coefs[q])

    ny, nx = c.shape
    jj, ii = np.mgrid[0:ny, 0:nx]
    # xx
    m = a[:, :-2] & a[:, 1:-1] & a[:, 2:]
    w = D0 * np.minimum(np.minimum(c[:, :-2], c[:, 1:-1]), c[:, 2:])[m] / H**2
    stencil([idx[:, :-2][m], idx[:, 1:-1][m], idx[:, 2:][m]], w, (1.0, -2.0, 1.0))
    # yy
    m = a[:-2] & a[1:-1] & a[2:]
    w = D0 * np.minimum(np.minimum(c[:-2], c[1:-1]), c[2:])[m] / H**2
    stencil([idx[:-2][m], idx[1:-1][m], idx[2:][m]], w, (1.0, -2.0, 1.0))
    # xy (twist), 2(1-nu) with nu = 0.2
    m = a[:-1, :-1] & a[1:, :-1] & a[:-1, 1:] & a[1:, 1:]
    mc = np.minimum(np.minimum(c[:-1, :-1], c[1:, :-1]), np.minimum(c[:-1, 1:], c[1:, 1:]))[m]
    w = D0 * 1.6 * mc / H**2
    stencil([idx[:-1, :-1][m], idx[1:, :-1][m], idx[:-1, 1:][m], idx[1:, 1:][m]], w, (1.0, -1.0, -1.0, 1.0))
    N = int(a.sum())
    return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))


def upstream(hole, ell):
    """How much hole lies just upwind: a one-sided exponential along the wind. The sheet going on beyond the plane counts as paper."""
    r = int(4 * ell / H) + 1
    y, x = np.mgrid[-r : r + 1, -r : r + 1].astype(np.float64) * H
    s = -(x * WIND[0] + y * WIND[1])  # distance upwind
    perp = np.abs(x * -WIND[1] + y * WIND[0])
    k = np.where((s >= 0) & (perp <= 0.75 * H), np.exp(-s / ell), 0.0)
    k /= k.sum()
    # rows run +y here, as the nodes do
    return cv2.filter2D(hole.astype(np.float32), -1, k.astype(np.float32), borderType=cv2.BORDER_CONSTANT)


class Eddies:
    """Advected noise: two tiles moving with the wind at different speeds, so the pattern changes as it passes."""

    def __init__(self, shape, seed):
        r = np.random.default_rng(seed)
        self.n = 1024
        self.t = []
        for sig in (5.0, 2.0):
            a = ndi.gaussian_filter(r.normal(0, 1, (self.n, self.n)).astype(np.float32), sig / H, mode="wrap")
            b = ndi.gaussian_filter(r.normal(0, 1, (self.n, self.n)).astype(np.float32), sig / H, mode="wrap")
            self.t += [a / a.std(), b / b.std()]
        self.shape = shape

    def at(self, t, speed):
        ny, nx = self.shape
        out = np.zeros(self.shape, np.float32)
        for tile, v, wt in zip(self.t, (1.0, 0.72, 0.9, 1.15), (0.6, 0.6, 0.2, 0.2)):
            d = v * speed * t / H
            M = np.array([[1, 0, -d * WIND[0]], [0, 1, -d * WIND[1]]], np.float32)
            out += wt * cv2.warpAffine(tile, M, (nx, ny), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        return out / 1.0


def gusts(seed, t_end):
    """Gusts at irregular times, irregular strengths: never a period."""
    r = np.random.default_rng(seed)
    out, t = [], 0.1
    while t < t_end + 1.0:
        out.append((t, r.uniform(0.16, 0.34), r.uniform(0.4, 1.0)))
        t += r.lognormal(np.log(0.55), 0.4)
    return out


def membrane(w, c, a, idx):
    """In-plane drift that cancels the stretch of the lifted sheet, least squares, contact anchored. Second order in the slope, so small."""
    N = int(a.sum())
    W = np.zeros(a.shape)
    W[a] = w
    rows, cols, vals, rhs = [], [], [], np.zeros(2 * N)

    def edge(i0, i1, off0, off1, target, wt):
        # wt (u1 - u0 - target)^2
        rows.extend([i0 + off0, i0 + off0, i1 + off1, i1 + off1])
        cols.extend([i0 + off0, i1 + off1, i0 + off0, i1 + off1])
        vals.extend([wt, -wt, -wt, wt])
        np.add.at(rhs, i0 + off0, -wt * target)
        np.add.at(rhs, i1 + off1, wt * target)

    m = a[:, :-1] & a[:, 1:]
    dw = (W[:, 1:] - W[:, :-1])[m]
    edge(idx[:, :-1][m], idx[:, 1:][m], 0, 0, -0.5 * dw * dw / H, np.minimum(c[:, :-1], c[:, 1:])[m])
    m = a[:-1] & a[1:]
    dw = (W[1:] - W[:-1])[m]
    edge(idx[:-1][m], idx[1:][m], N, N, -0.5 * dw * dw / H, np.minimum(c[:-1], c[1:])[m])
    # shear, softer: du/dy + dv/dx = -w_x w_y
    m = a[:-1, :-1] & a[1:, :-1] & a[:-1, 1:] & a[1:, 1:]
    wx = 0.5 * (W[:-1, 1:] - W[:-1, :-1] + W[1:, 1:] - W[1:, :-1])[m] / H
    wy = 0.5 * (W[1:, :-1] - W[:-1, :-1] + W[1:, 1:] - W[:-1, 1:])[m] / H
    cq = np.minimum(np.minimum(c[:-1, :-1], c[1:, :-1]), np.minimum(c[:-1, 1:], c[1:, 1:]))[m] * 0.35
    edge(idx[:-1, :-1][m], idx[1:, :-1][m], 0, 0, -0.5 * wx * wy * H, cq)
    edge(idx[:-1, 1:][m], idx[1:, 1:][m], 0, 0, -0.5 * wx * wy * H, cq)
    edge(idx[:-1, :-1][m], idx[:-1, 1:][m], N, N, -0.5 * wx * wy * H, cq)
    edge(idx[1:, :-1][m], idx[1:, 1:][m], N, N, -0.5 * wx * wy * H, cq)
    anchor = np.where(w < 0.003, 2.0, 1e-3)
    A = sp.csc_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(2 * N, 2 * N)) + sp.diags(np.r_[anchor, anchor])
    u = spl.splu(A.tocsc(), permc_spec="MMD_AT_PLUS_A", options={"SymmetricMode": True}).solve(rhs)
    return u[:N], u[N:]


def spread(field, a, nearest):
    """Fill the cells without paper from the nearest paper, so bilinear sampling near an edge follows the edge."""
    out = np.zeros(a.shape, field.dtype)
    out[a] = field
    return out[nearest[0], nearest[1]]


def main():
    t0 = time.time()
    c, xs, ys, P, alpha = load_sheet()
    check_cloth(P, alpha)
    del P, alpha
    ny, nx = c.shape
    a = active_mask(c)
    nearest = ndi.distance_transform_edt(~a, return_distances=False, return_indices=True)
    idx = -np.ones(a.shape, np.int64)
    idx[a] = np.arange(a.sum())
    N = int(a.sum())
    cA = np.where(a, np.maximum(c, 0.04), 0.0)
    area = cA[a] * H * H
    M = RHO * area
    K = plate_matrix(cA, a, idx)
    # pins: the plane's left, right and lower ends are not the paper's: the sheet continues, flat, under its own weight
    pin = np.zeros(a.shape, bool)
    pin[:, :4] = pin[:, -4:] = True
    pin[:4] = True
    pin = pin[a]
    pinv = np.where(pin, 1e12, 0.0)
    A = (K + sp.diags(M / DT**2 + ARG["Cbar"] * area / DT + ARG["kf"] * area + pinv)).tocsc()
    print(f"N {N}, factorising, {time.time() - t0:.0f} s", flush=True)
    t1 = time.time()
    lu = spl.splu(A, permc_spec="MMD_AT_PLUS_A", options={"SymmetricMode": True})
    print(f"factor {time.time() - t1:.1f} s, nnz {lu.L.nnz / 1e6:.1f} M", flush=True)

    hole = 1.0 - c
    # the sheet is a quarter holes, so its mean under-pressure leaks away through them: only the excess over the surroundings (about a cm) pushes.
    # That keeps the rim and the big windows' windward edges loaded and the middle of the field not.
    Ebar = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), ARG["sigH"] / H).astype(np.float64)
    E0 = np.maximum(upstream(hole, ARG["ell0"]).astype(np.float64) - Ebar, 0.0)
    E1 = np.maximum(upstream(hole, ARG["ell1"]).astype(np.float64) - Ebar, 0.0)
    speed = ARG["conv"] * ARG["U0"]
    edd = Eddies((ny, nx), ARG["seed"] + 1)
    t_all = ARG["spin"] + ARG["frames"] / 25.0
    gs = gusts(ARG["seed"], t_all)
    print("gusts at", [f"{g[0]:.2f}" for g in gs], flush=True)
    Xn, Yn = np.meshgrid(xs, ys)
    S = Xn * WIND[0] + Yn * WIND[1]
    amask = a.astype(np.float32)
    ablur = cv2.GaussianBlur(amask, (0, 0), 0.05 / H) + 1e-3

    w = np.zeros(N)
    v = np.zeros(N)
    d0 = GRAV / ARG["kf"]  # sits this far into its floor under its own weight; the floor is its rest shape, and this is well below the rest gap to the cloth
    weight = GRAV * area
    W = np.zeros(a.shape, np.float32)
    vis = (Xn > VIEW[0]) & (Xn < VIEW[1]) & (Yn > VIEW[2]) & (Yn < VIEW[3])
    vis_a = vis[a]
    steps_per = int(round(1 / 25.0 / DT))
    n_spin = int(round(ARG["spin"] * 25))
    out = []
    t = 0.0
    log = []
    for fr in range(n_spin + ARG["frames"]):
        for _ in range(steps_per):
            t += DT
            tau = t - S / speed
            G = 0.28 + sum(amp * np.exp(-0.5 * ((tau - tc) / sg) ** 2) for tc, sg, amp in gs)
            U = ARG["U0"] * G * (1.0 + ARG["tb"] * edd.at(t, speed))
            q = 0.5 * AIR * U * U
            W[:] = 0
            W[a] = w
            Ws = cv2.GaussianBlur(W * amask, (0, 0), 0.05 / H) / ablur
            gx = cv2.Sobel(Ws, cv2.CV_32F, 1, 0, ksize=3) / (8 * H)
            gy = cv2.Sobel(Ws, cv2.CV_32F, 0, 1, ksize=3) / (8 * H)
            dwds = np.clip(gx * WIND[0] + gy * WIND[1], -0.6, 0.6)
            ga = np.clip(w / 0.08, 0.0, 1.0)
            ga = ga * ga * (3 - 2 * ga)
            expo = E0[a] + (E1[a] - E0[a]) * ga
            # the higher it lifts, the more of the air goes through under it and out: the load falls off with the gap (venting). This is what keeps a breeze from flipping it
            vent = 1.0 / (1.0 + (w / ARG["wv"]) ** 2)
            p = q[a] * (ARG["Cb"] + (ARG["Ce"] * expo - ARG["Ca"] * dwds[a]) * vent)
            gap = w + ARG["g0"]
            cd = np.minimum(ARG["cair"] + MU * ARG["Lsq"] ** 2 / gap**3, ARG["Cbar"])
            b = M / DT**2 * (w + DT * v) + ARG["Cbar"] * area / DT * w + (ARG["Cbar"] - cd) * area * v + p * area - weight
            # contact as a stiff soft floor, implicit while in contact and lagged once free, so the factorisation stays the same: F = kf max(d0 - w, 0), which at w = 0 holds the weight
            wn = lu.solve(b + ARG["kf"] * area * np.maximum(w, d0))
            v = (wn - w) / DT
            w = wn
        wv = w[vis_a]
        log.append((fr, float(w.max()), float(np.percentile(wv, 99)), float((wv > 0.01).mean()), float((wv > 0.1).mean())))
        if fr % 5 == 0 or fr >= n_spin:
            print(f"frame {fr - n_spin:+d}: max {w.max() * 10:.2f} mm (in view {wv.max() * 10:.2f}), p99 {np.percentile(wv, 99) * 10:.2f}, lifted>0.1mm {(wv > 0.01).mean() * 100:.1f} %, >1mm {(wv > 0.1).mean() * 100:.1f} %, q max {q.max():.1f}, p p99 {np.percentile(p, 99):.1f} max {p.max():.1f},  t {time.time() - t0:.0f} s", flush=True)
        if fr >= n_spin:
            out.append(np.maximum(w - d0, 0.0))

    print(f"solved, {time.time() - t0:.0f} s. Membrane per frame.", flush=True)
    d = np.zeros((len(out), ny, nx, 3), np.float16)
    for i, wf in enumerate(out):
        ux, uy = membrane(wf, cA, a, idx)
        d[i, ..., 0] = spread(ux, a, nearest).astype(np.float16)
        d[i, ..., 1] = spread(uy, a, nearest).astype(np.float16)
        d[i, ..., 2] = spread(wf, a, nearest).astype(np.float16)
        print(f"membrane {i}: in-plane max {max(np.abs(ux).max(), np.abs(uy).max()) * 10:.3f} mm", flush=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    np.save(out_path, d)
    import json

    json.dump({"extent": [float(xs[0]), float(xs[-1]), float(ys[0]), float(ys[-1])], "args": ARG, "gusts": gs}, open(out_path + ".json", "w"), indent=1)
    print(f"{out_path}: {d.shape}, {os.path.getsize(out_path) / 1e6:.1f} MB, total {time.time() - t0:.0f} s", flush=True)

    # a look: w per frame, y up, in view
    x0, x1 = np.searchsorted(xs, VIEW[0]), np.searchsorted(xs, VIEW[1])
    tiles = []
    for i in range(0, len(out), max(len(out) // 8, 1)):
        im = np.sqrt(np.clip(d[i, ::-1, x0:x1, 2].astype(np.float32) / 0.4, 0, 1))
        im = (im * 255).astype(np.uint8)
        im[a[::-1, x0:x1] == 0] = (im[a[::-1, x0:x1] == 0] * 0.5).astype(np.uint8)
        tiles.append(cv2.resize(cv2.applyColorMap(im, cv2.COLORMAP_INFERNO), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    rows = [np.hstack(tiles[k : k + 2]) for k in range(0, len(tiles) - 1, 2)]
    cv2.imwrite(out_path + ".jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])


if __name__ == "__main__":
    main()
