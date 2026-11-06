"""Shot 70, the flow: tea leaving lumps of pressed tea, just out of frame, in a bowl of hot water that is still turning slowly from the pour. The solver is s68_flow.Flow (3D Boussinesq, pseudo-spectral); what is new here is the bowl, the swirl, the source and the output.

    python3 -I v2/stills/s70_flow.py NAME k=v,k=v|@params.json     out/v2/s70_sim/NAME/

Output: previews p#####.jpg and sheet.jpg (flat view along the camera, on a warm card, for judging the flow; refraction only as an apparent depth) and, at the times in `save`, grids for the renderer: T.vdb (grids `fine` and `coarse`, by s70_vdb.py).

The bowl is a real boundary: Brinkman penalisation (Angot, Bruneau, Fabrie 1999; for spectral codes Kolomenskiy and Schneider 2009), here in its limit of infinite drag: after each step the velocity is multiplied by a smooth fluid mask and projected again. So the heavy tea runs down the glaze, and the swirl has its bottom boundary layer, whose inflow is what gathers tea leaves at the centre (Einstein 1926).

Particles have no numerical diffusion, so filaments stay as thin as the flow makes them; molecular diffusion comes back at output from each particle's age, sigma^2 = 2 D age.

Numbers: D defaults to 1e-5 cm2/s, catechin about 2.2e-6 at 25 C read off Srinivas et al. 2011 via ref/tea_plume/report.md, scaled up about 4x to 80 C (an estimate); the take uses 3e-6, an estimate for black tea's larger polyphenols, chosen because filaments stayed too soft at the higher value. g' of undiluted liquor g1: delta rho / rho about 0.5% gives 5 cm/s2, an estimate from that report's assumed solids; set lower by eye for a slower picture. nu = 0.0036 cm2/s, water at 80 C (general knowledge). The swirl and the stir are choices.
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import torch
import torch.nn.functional as TF

import s68_flow as SF

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2", "s70_sim")
DEV = SF.DEV

SIM = dict(
    dx=0.045, x0=-6.6, x1=6.6, y0=-6.6, y1=6.6, z0=-4.4, z1=0.0,
    nu=0.0036, D=1e-5, g1=3.0, dt=0.04, cfl=0.8, T=16.0, seed=70,
    n_dyn=3_000_000, n_pass=20_000_000, K=2, up=2,
    preview_every=1.0, preview_w=960,
    sigma=[1.0, 2.3, 8.0], K_abs=1.2,  # per cm of undiluted tea, and light crosses it twice
    W=8.2, E=18.0, apex_y=0.48, z_rim=0.45,  # the preview's frame, as in s70_chatang
    save=[], mem_frac=0.6,
    swirl=0.12,  # rad/s, counter-clockwise from above: the far wall moves right to left in the frame
    stir=dict(seed=6, lam=1.5, rms=0.08, width=0.6),
    lumps=[
        dict(x=3.9, y=3.05, z=-0.55, ax=0.5, ay=0.4, az=0.2, seeps=40, vol=2.0, t0=0.0, dur=20.0, r=0.05, spread=0.9, seed=1),
        dict(x=4.6, y=1.6, z=-1.0, ax=0.4, ay=0.3, az=0.2, seeps=25, vol=1.0, t0=0.0, dur=20.0, r=0.05, spread=0.8, seed=2),
    ],
    grid=dict(fine=0.0125, coarse=0.04, box=[-5.0, 5.0, -3.0, 5.95, -4.4, 0.0], thresh=3e-4),  # from low down the frame sees almost the whole bowl
)

R_RIM, BOWL_D, BOWL_P = 6.0, 4.47, 1.6  # as in s70_chatang


def z_wall(r, z_rim):
    """The glaze: torch or numpy. Past the rim, the wall goes on up, so all of that is solid."""
    q = (r / R_RIM).clamp(min=1e-4)
    return z_rim - BOWL_D * (1.0 - q**BOWL_P)


def bowl_mask(F, S):
    nz, ny, nx = F.n
    x = S["x0"] + (torch.arange(nx, device=DEV, dtype=torch.float32) + 0.5) * float(F.cell[0])
    y = S["y0"] + (torch.arange(ny, device=DEV, dtype=torch.float32) + 0.5) * float(F.cell[1])
    z = S["z0"] + (torch.arange(nz, device=DEV, dtype=torch.float32) + 0.5) * float(F.cell[2])
    Z, Y, X = torch.meshgrid(z, y, x, indexing="ij")
    r = torch.hypot(X, Y)
    sl = BOWL_D * BOWL_P / R_RIM * (r / R_RIM).clamp(min=1e-4) ** (BOWL_P - 1)
    sd = (Z - z_wall(r, S["z_rim"])) / torch.sqrt(1 + sl * sl)  # height above the glaze along its normal, near enough
    d = float(F.cell.min())
    t = ((sd + d) / (2 * d)).clamp(0, 1)
    return (t * t * (3 - 2 * t)).float(), X, Y


def penalise(F, M):
    for i, k in enumerate((SF.KU, SF.KV, SF.KW)):
        F.U[i] = F.tr.fwd(F.tr.inv(F.U[i], k) * M, k)
    F.U = F.project(F.U)


def out_of_glaze(P, S):
    r = torch.hypot(P[:, 0], P[:, 1])
    zw = z_wall(r, S["z_rim"]) + 0.002
    P[:, 2] = torch.maximum(P[:, 2], zw).clamp(max=-1e-3)


def seeps(lumps, z_rim=0.38):
    out = []
    for L in lumps:
        r = np.random.default_rng(L["seed"])
        n = L["seeps"]
        w = r.lognormal(0.0, L.get("spread", 0.8), n)
        w = L["vol"] * w / w.sum()
        # points on the lower half of a lumpy ellipsoid
        a = r.uniform(0, 2 * np.pi, n)
        c = r.uniform(0.05, 1.0, n)  # cos of the angle from straight down
        s = np.sqrt(1 - c * c)
        lump = 1.0 + 0.25 * r.normal(size=n)
        x = L["x"] + L["ax"] * s * np.cos(a) * lump
        y = L["y"] + L["ay"] * s * np.sin(a) * lump
        z = np.minimum(L["z"] - L["az"] * c * lump, -0.02)
        rr_ = np.hypot(x, y)
        z = np.maximum(z, z_rim - BOWL_D * (1 - np.clip(rr_ / R_RIM, 0, 1) ** BOWL_P) + 0.03)
        for i in range(n):
            out.append(dict(x=float(x[i]), y=float(y[i]), z=float(z[i]), vol=float(w[i]), r=float(L["r"] * r.uniform(0.6, 1.4)), t0=float(L["t0"] + r.uniform(0.0, 2.0)), dur=float(L["dur"]), age0=float(L.get("age0", 0.0)), tau=L.get("tau")))
    return out


def particles(ss, n_total, rng):
    vols = np.array([s["vol"] for s in ss])
    counts = (vols / vols.sum() * n_total).astype(np.int64)
    P, B, A = [], [], []
    for s, n in zip(ss, counts):
        th = rng.random(n, dtype=np.float32) * 2 * np.pi
        rr = s["r"] * np.sqrt(rng.random(n, dtype=np.float32))
        zz = s["z"] - s["r"] * rng.random(n, dtype=np.float32)
        P.append(np.stack([s["x"] + rr * np.cos(th), s["y"] + rr * np.sin(th), zz], -1))
        u = rng.random(n, dtype=np.float32)
        if s.get("tau"):  # extraction slows as the lump gives up what is near its surface: rate exp(-t / tau). tau is a choice
            B.append(s["t0"] - s["tau"] * np.log(1.0 - u * (1.0 - np.exp(-s["dur"] / s["tau"]))))
        else:
            B.append(s["t0"] + s["dur"] * u)
        A.append(np.full(n, s["age0"], np.float32))
    P, B, A = np.concatenate(P).astype(np.float32), np.concatenate(B).astype(np.float32), np.concatenate(A)
    o = np.argsort(B, kind="stable")
    return P[o], B[o], A[o]


def blur3(x, sig):
    """Separable Gaussian in place of a 3D FFT; x is (nz, ny, nx)."""
    r = int(3 * sig + 0.5)
    k = torch.exp(-0.5 * (torch.arange(-r, r + 1, device=x.device, dtype=x.dtype) / sig) ** 2)
    k = k / k.sum()
    x = x[None, None]
    x = TF.conv3d(x, k.view(1, 1, -1, 1, 1), padding=(r, 0, 0))
    x = TF.conv3d(x, k.view(1, 1, 1, -1, 1), padding=(0, r, 0))
    x = TF.conv3d(x, k.view(1, 1, 1, 1, -1), padding=(0, 0, r))
    return x[0, 0]


def cic(P, w, lo, vox, n):
    nz, ny, nx = n
    q = (P - lo) / vox - 0.5
    i = q.floor().long()
    f = q - i
    keep = (i[:, 0] >= 0) & (i[:, 0] < nx - 1) & (i[:, 1] >= 0) & (i[:, 1] < ny - 1) & (i[:, 2] >= 0) & (i[:, 2] < nz - 1)
    i, f, w = i[keep], f[keep], w[keep]
    out = torch.zeros(nz * ny * nx, device=P.device, dtype=torch.float32)
    for dz in (0, 1):
        wz = f[:, 2] if dz else 1 - f[:, 2]
        for dy in (0, 1):
            wy = f[:, 1] if dy else 1 - f[:, 1]
            for dx in (0, 1):
                wx = f[:, 0] if dx else 1 - f[:, 0]
                out.index_add_(0, ((i[:, 2] + dz) * ny + (i[:, 1] + dy)) * nx + (i[:, 0] + dx), w * wx * wy * wz)
    return out.view(nz, ny, nx)


LAYERS = [(0, 0.0075), (0, 0.015), (1, 0.03), (1, 0.06), (1, 0.12), (1, 0.24)]  # (grid, sigma in cm)


def grids(P, age, mass, S):
    """Concentration (fraction of undiluted tea) on a fine and a coarse grid. Each particle is shared between the two layers around its own diffusion width, so nothing pops as it ages."""
    gc = S["grid"]
    x0, x1, y0, y1, z0, z1 = gc["box"]
    lo = torch.tensor([x0, y0, z0], device=DEV, dtype=torch.float32)
    vox = (gc["fine"], gc["coarse"])
    n = [tuple(int(round(v)) for v in ((z1 - z0) / h, (y1 - y0) / h, (x1 - x0) / h)) for h in vox]
    sg = torch.sqrt(2.0 * S["D"] * age.clamp(min=0.0))
    sb = torch.tensor([s for _, s in LAYERS], device=DEV, dtype=torch.float32)
    sc = sg.clamp(min=float(sb[0]), max=float(sb[-1]) - 1e-5)
    b = torch.bucketize(sc, sb, right=True) - 1
    t = (sc - sb[b]) / (sb[b + 1] - sb[b])
    out = [torch.zeros(n[0], device=DEV, dtype=torch.float32), torch.zeros(n[1], device=DEV, dtype=torch.float32)]
    for j, (g, s) in enumerate(LAYERS):
        w = (1 - t) * (b == j).float() + t * (b == j - 1).float() if j else (1 - t) * (b == 0).float()
        m = w > 0
        if not m.any():
            continue
        c = cic(P[m], w[m] * (mass / vox[g] ** 3), lo, vox[g], n[g])
        out[g] += blur3(c, s / vox[g])
    return out


def preview(path, Ps, mass, S):
    """Column density seen along the camera on a warm card, doubled because the light crosses the tea twice. Each particle is carried up the refracted ray to where that ray meets the flat water, and is drawn at that point (rim and meniscus are ignored)."""
    w = S["preview_w"]
    h = w * 9 // 16
    e = np.radians(S["E"])
    Hc = S["W"] * 9 / 16
    px = w / S["W"]
    N = torch.zeros((h, w), device=DEV, dtype=torch.float32)
    y0 = (R_RIM + 0.05) * np.sin(e) + S["z_rim"] * np.cos(e)
    st = np.cos(e) / 1.33  # sine of the ray's angle from the vertical, in the water
    tan_t, cos_t = st / np.sqrt(1 - st * st), np.sqrt(1 - st * st)
    side = S.get("side")  # looking through the wall, level: straight along y, with no refraction
    for P in Ps:
        if len(P) == 0:
            continue
        u = P[:, 0] * px + w / 2 - 0.5
        v = (S["apex_y"] + (S["z_rim"] - P[:, 2]) / Hc) * h - 0.5 if side else (S["apex_y"] + (y0 - (P[:, 1] + P[:, 2] * tan_t) * np.sin(e)) / Hc) * h - 0.5
        keep = (u >= 0) & (u < w - 1) & (v >= 0) & (v < h - 1)
        u, v = u[keep], v[keep]
        iu, iv = u.long(), v.long()
        fu, fv = u - iu, v - iv
        wt = mass * px**2 * (1.0 if side else np.sin(e) / cos_t)  # per area across the ray, not across the screen
        for dy, wy in ((0, 1 - fv), (1, fv)):
            for dx, wx in ((0, 1 - fu), (1, fu)):
                N.view(-1).index_add_(0, (iv + dy) * w + (iu + dx), wx * wy * wt)
    N = cv2.GaussianBlur(N.cpu().numpy(), (0, 0), 0.8)
    sig = np.array(S["sigma"]) * S["K_abs"]
    x = np.array([0.86, 0.84, 0.76]) * np.exp(-(1 if side else 2) * N[..., None] * sig)
    X = (np.arange(w) + 0.5 - w / 2) / px
    rim = (S["apex_y"] + (R_RIM + 0.05 - np.sqrt(np.maximum(R_RIM**2 - X**2, 0))) * np.sin(e) / Hc) * h
    if not side:
        x[np.arange(h)[:, None] < rim] = 0.012
    x = (np.clip(x, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)[..., ::-1]
    cv2.imwrite(path, x, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return x


def run(name, over):
    global R_RIM, BOWL_D, BOWL_P
    S = {**SIM, **over}
    R_RIM, BOWL_D, BOWL_P = S.get("bowl", (R_RIM, BOWL_D, BOWL_P))  # another vessel, in the same form
    if DEV == "cuda":
        torch.cuda.set_per_process_memory_fraction(S["mem_frac"])
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    t0 = time.time()
    ss = seeps(S["lumps"], S["z_rim"])
    Pd, Bd, Ad = particles(ss, S["n_dyn"], np.random.default_rng(S["seed"]))
    Pp, Bp, Ap = particles(ss, S["n_pass"], np.random.default_rng(S["seed"] + 1))
    print(f"[init] {len(Pd)/1e6:.1f} + {len(Pp)/1e6:.1f} M particles, {len(ss)} seeps, {time.time()-t0:.0f} s", flush=True)
    F = SF.Flow(S)
    nz, ny, nx = F.n
    M, Xg, Yg = bowl_mask(F, S)
    st = S.get("stir")
    if st:
        g = torch.Generator(device=DEV).manual_seed(st["seed"])
        k = torch.sqrt(F.K2)
        band = torch.exp(-0.5 * (torch.log(k.clamp(min=1e-3) / (2 * np.pi / st["lam"])) / st.get("width", 0.5)) ** 2)
        F.U = F.project(torch.randn((3, nz, ny, nx), device=DEV, generator=g) * band)
        F.U *= st["rms"] / float(F.grid().std())
    if S.get("swirl"):
        F.U[0] += F.tr.fwd(-S["swirl"] * Yg, SF.KU)
        F.U[1] += F.tr.fwd(S["swirl"] * Xg, SF.KV)
    penalise(F, M)
    print(f"[grid] {nx}x{ny}x{nz} = {nx*ny*nz/1e6:.2f} M cells, cell {[round(float(c),4) for c in F.cell]} cm, {DEV}", flush=True)
    Pd_, Pp_ = torch.from_numpy(Pd).to(DEV), torch.from_numpy(Pp).to(DEV)
    Bd_, Bp_ = torch.from_numpy(Bd).to(DEV), torch.from_numpy(Bp).to(DEV)
    Ad_, Ap_ = torch.from_numpy(Ad).to(DEV), torch.from_numpy(Ap).to(DEV)
    tot = sum(s["vol"] for s in ss)
    # each particle carries the volume of undiluted tea its birth rate implies, over the whole release
    tot_all = tot
    mass_d = tot_all / len(Pd)
    mass_all = tot_all / (len(Pd) + len(Pp))
    cell_v = float(F.cell.prod())
    json.dump({**S, "mass_all": mass_all}, open(os.path.join(d, "params.json"), "w"), indent=1)
    saves = sorted(S["save"])
    t, it, alive_d, alive_p = 0.0, 0, 0, 0
    Gp_old, tp_old, refresh = None, 0.0, True
    next_prev = S["preview_every"]
    vid = []
    t0 = time.time()
    rw = float(np.sqrt(2 * S["D"]))
    while t < S["T"] - 1e-9:
        alive_d = int(np.searchsorted(Bd, t, side="right"))
        c = F.deposit(Pd_[:alive_d]) * (mass_d / cell_v) if alive_d else torch.zeros(F.n, device=DEV)
        Fz = F.tr.fwd(-S["g1"] * c, SF.KW) * F.lowF
        U_g = F.grid()
        umax = float(U_g.abs().max())
        dt = min(S["dt"], S["cfl"] * float(F.cell.min()) / max(umax, 1e-3))
        marks = [x for x in saves + [next_prev] if x > t + 1e-9]
        if marks and min(marks) - t < dt * 1.5:
            dt = min(marks) - t
        if refresh:
            Gp_old, tp_old = F.grid_fine(), t
            n_p = int(np.searchsorted(Bp, t, side="right"))
            if n_p > alive_p:
                q = Pp_[alive_p:n_p]
                q += (t - Bp_[alive_p:n_p])[:, None] * F.sample(Gp_old, q)
                F.keep_in(q)
            alive_p = n_p
            refresh = False
        F.step(Fz, dt)
        penalise(F, M)
        U_new = F.grid()
        if alive_d:
            p = Pd_[:alive_d]
            v0 = F.sample(U_g, p)
            v1 = F.sample(U_new, p + dt * v0)
            p += 0.5 * dt * (v0 + v1) + torch.randn_like(p) * float(rw * np.sqrt(dt))
            F.keep_in(p)
            out_of_glaze(p, S)
        t += dt
        it += 1
        due_save = any(abs(x - t) < 1e-6 for x in saves)
        due_prev = t >= next_prev - 1e-6
        if it % S["K"] == 0 or due_save or due_prev or t >= S["T"] - 1e-9:
            Gn = F.grid_fine()
            h = t - tp_old
            for a in range(0, alive_p, 8_000_000):
                q = Pp_[a : min(a + 8_000_000, alive_p)]
                v0 = F.sample(Gp_old, q)
                v1 = F.sample(Gn, q + h * v0)
                q += 0.5 * h * (v0 + v1)
                F.keep_in(q)
                out_of_glaze(q, S)
            refresh = True
            if due_prev:
                x = preview(os.path.join(d, f"p{int(round(t*100)):05d}.jpg"), [Pd_[:alive_d], Pp_[:alive_p]], mass_all, S)
                vid.append(x)
                next_prev += S["preview_every"]
            if due_save:
                t1 = time.time()
                P_all = torch.cat([Pd_[:alive_d], Pp_[:alive_p]])
                A_all = torch.cat([t - Bd_[:alive_d] + Ad_[:alive_d], t - Bp_[:alive_p] + Ap_[:alive_p]])
                fine, coarse = grids(P_all, A_all, mass_all, S)
                gc = S["grid"]
                fine, coarse = fine.cpu().numpy().astype(np.float16), coarse.cpu().numpy().astype(np.float16)
                np.save(os.path.join(d, f"fine_{t:07.3f}.npy"), fine)
                np.save(os.path.join(d, f"coarse_{t:07.3f}.npy"), coarse)
                print(f"[save] t={t:.3f} fine {fine.shape} max {float(fine.max()):.3f}, active {(fine>gc['thresh']).mean()*100:.1f}%, coarse max {float(coarse.max()):.3f}; {time.time()-t1:.1f} s", flush=True)
                # a frame is 400 MB as an array and mostly empty: keep only the sparse VDB, or a take fills the disk
                bl = os.environ.get("GEWU_BLENDER_ROOT", "blender-5.2.1-linux-x64")
                subprocess.run([os.path.join(bl, "5.2/python/bin/python3.13"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "s70_vdb.py"), d, f"{t:07.3f}"], env={**os.environ, "LD_LIBRARY_PATH": os.path.join(bl, "lib")}, check=True, stdout=subprocess.DEVNULL)
                os.remove(os.path.join(d, f"fine_{t:07.3f}.npy"))
                os.remove(os.path.join(d, f"coarse_{t:07.3f}.npy"))
        if it % 50 == 0:
            mem = torch.cuda.max_memory_reserved() / 2**30 if DEV == "cuda" else 0
            print(f"[{it}] t={t:.2f} dt={dt:.4f} umax {umax:.2f} cm/s, cmax {float(c.max()):.2f}, {(time.time()-t0)/it:.2f} s/step, alive {alive_d/1e6:.1f}+{alive_p/1e6:.1f} M, peak {mem:.1f} GB", flush=True)
    if vid:
        cols = 4
        rows = int(np.ceil(len(vid) / cols))
        hh, ww = vid[0].shape[:2]
        sheet = np.zeros((rows * hh // 2, cols * ww // 2, 3), np.uint8)
        for i, v in enumerate(vid):
            sheet[(i // cols) * hh // 2 : (i // cols + 1) * hh // 2, (i % cols) * ww // 2 : (i % cols + 1) * ww // 2] = cv2.resize(v, (ww // 2, hh // 2), interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(d, "sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"[done] {it} steps, {time.time()-t0:.0f} s", flush=True)


def args(s):
    if not s or s == "-":
        return {}
    if s.startswith("@"):
        return json.load(open(s[1:]))
    return {k: json.loads(v) for k, v in (kv.split("=", 1) for kv in s.split(","))}


if __name__ == "__main__":
    with torch.no_grad():
        run(sys.argv[1], args(sys.argv[2]) if len(sys.argv) > 2 else {})
