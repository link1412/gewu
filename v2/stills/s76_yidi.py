"""Shot 76, 一滴: one drop of ink opening in clear water, as when a brush is rinsed in a brush washer, seen from the side against a lit ground, with no vessel and no surface in the frame. The picture is turned upside down, as photographers do with ink: the falling cap becomes a dome rising, and the dome is the arc. The camera does not move.

    python3 -I v2/stills/s76_yidi.py NAME [k=v,k=v]     out/v2/s76_yidi/NAME*.jpg

The solve is real: s68_flow.Flow, 3D Boussinesq, pseudo-spectral, free-slip box, carried by particles, so there is no numerical diffusion of the pigment.

Stand-ins and choices:
- Size, g1 and viscosity are chosen for the picture, not measured from a pigment. The drop is far bigger than a real one, and the ink in a brush would leave as a thread, not a ball.
- The ink only absorbs, grey in every channel, with no scattering; its strength and the warm ground are chosen by eye. The absorption is summed from particles in depth bins, each with its own defocus. Not a path-traced volume.
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import torch

import darkroom
import s68_flow as SF

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2", "s76_yidi")
DEV = SF.DEV
DEVELOP = {"exposure": 0.0, "contrast": 1.25, "saturation": 1.0, "black": 0.0, "grain": 1.0, "sharpen": 0.22, "halation": 0.05, "glare": 0.006, "vignette": 0.2}

S0 = dict(
    dx=0.03, x0=-3.0, x1=3.0, y0=-3.0, y1=3.0, z0=-8.0, z1=0.0,
    nu=0.003, g1=4.0, dt=0.03, cfl=0.8, K=2, up=2, T=6.0, seed=76,
    n_dyn=3_000_000, n_pass=40_000_000, stir=0.05,
    drops=[
        dict(x=0.0, y=0.0, d=0.8, t0=0.0, r=0.6, kick=0.0, tail=0.15, tail_T=2.5, tail_r=0.09),
        dict(x=0.12, y=0.1, d=0.4, t0=0.7, r=0.3, kick=0.0, tail=0.2, tail_T=2.0, tail_r=0.05),
    ],
    # picture. slow: film seconds per solve second. z_cam: the height of the frame's apex line; None follows the top, for looking only
    W=3.6, cx=0.45, apex_y=0.48, H=1080, tau=0.5, thin=0.02, dist=30.0, focus=0.0, coc=7.0, z_cam=None, soft=0.65,
    ground=1.2, falloff=0.2, glow_y=0.3, paper=[1.0, 0.975, 0.925], ink=[1.0, 1.0, 1.0], floor=0.004,
    looks=[3.5, 5.0, 6.0], snap=False, frames=0, slow=4.0, fps=24.0, shutter=0.5,
)


def gblur(t, s):
    if s < 0.25:
        return t
    return torch.from_numpy(cv2.GaussianBlur(t.cpu().numpy(), (0, 0), float(s))).to(DEV)


def render(chunks, mass, S, z_top):
    """Linear RGB (H, W, 3), numpy, from the particles in chunks, so memory does not grow with their number. Ink on a lit ground: only absorption along the line of sight (Beer-Lambert). Depth from the camera is y (the camera is at -dist). Falling (-z) is drawn upward."""
    H = S["H"]
    Wp = int(round(H * 16 / 9))
    px0 = Wp / S["W"]
    op = mass * px0 * px0 * S["tau"] / S["thin"]
    edges = np.linspace(-3.0, 3.0, 49)  # thin: a bin's centre sets its defocus, so with thick bins even the plane of focus goes soft
    nb = len(edges) - 1
    bins = torch.zeros(nb * H * Wp, device=DEV)
    for P in chunks:
        mag = S["dist"] / (S["dist"] + P[:, 1] - S["focus"])
        x = (P[:, 0] - S["cx"]) * mag * px0 + Wp / 2
        y = (S["apex_y"] * H / px0 + (P[:, 2] - z_top) * mag) * px0
        n = ((P[:, 1] - edges[0]) / (edges[1] - edges[0])).floor().long()
        i, j = x.floor().long(), y.floor().long()
        fx, fy = x - i, y - j
        for dj, di in ((0, 0), (0, 1), (1, 0), (1, 1)):
            a = (fx if di else 1 - fx) * (fy if dj else 1 - fy) * op
            ii, jj = i + di, j + dj
            ok = (ii >= 0) & (ii < Wp) & (jj >= 0) & (jj < H) & (n >= 0) & (n < nb)
            bins.index_add_(0, (n[ok] * H + jj[ok]) * Wp + ii[ok], a[ok])
    bins = bins.view(nb, H, Wp)
    k = H / 1080
    tau = torch.zeros((H, Wp), device=DEV)
    for b_, a, b in zip(bins, edges[:-1], edges[1:]):
        if bool(b_.any()):
            tau += gblur(b_, abs(0.5 * (a + b) - S["focus"]) * S["coc"] * k + S["soft"] * k)
    tau = tau.cpu().numpy()
    # the ground: a light behind the water, falling off from a little above the middle
    yy, xx = np.mgrid[0:H, 0:Wp].astype(np.float32)
    r2 = ((xx - 0.5 * Wp) / (0.75 * Wp)) ** 2 + ((yy - S["glow_y"] * H) / (0.8 * H)) ** 2
    ground = S["ground"] * (1 - S["falloff"] * np.clip(r2, 0, 1.5))
    return np.stack([ground * S["paper"][i] * np.exp(-tau * S["ink"][i]) for i in range(3)], -1) + S["floor"]


def printed(rgb):
    """What the film's pipeline will do to this frame, for looking."""
    d = darkroom.develop(rgb.astype(np.float32), **DEVELOP)
    return darkroom.print_look(d)


def tone_u8(x):
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1]


def look(name, snap, over):
    """Only the picture, from a saved solve."""
    S = {**S0, **over}
    d = json.load(open(os.path.join(OUT, snap + "_snap.json")))
    P = torch.from_numpy(np.load(os.path.join(OUT, snap + "_snap.npy"))).to(DEV)
    z_top = S["z_cam"] if S["z_cam"] is not None else float(torch.quantile(P[:, 2][::40], 0.002))
    t0 = time.time()
    rgb = render([P], d["mass"], S, z_top)
    im = tone_u8(printed(rgb))
    cv2.imwrite(os.path.join(OUT, name + ".jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(f"[{name}] z_top {z_top:.3f}, {time.time()-t0:.1f} s, mean {im.mean():.1f}", flush=True)


def run(name, over):
    S = {**S0, **over}
    os.makedirs(OUT, exist_ok=True)
    if DEV == "cuda":
        torch.cuda.set_per_process_memory_fraction(float(os.environ.get("S76_MEM", "0.6")))
    t0 = time.time()
    Pd, Bd, _, _ = SF.source_particles(S["drops"], S["n_dyn"], np.random.default_rng(S["seed"]), S["seed"] + 3)
    Pp, Bp, _, _ = SF.source_particles(S["drops"], S["n_pass"], np.random.default_rng(S["seed"] + 1), S["seed"] + 3)
    F = SF.Flow(S)
    nz, ny, nx = F.n
    print(f"[init] {time.time()-t0:.0f} s, {nx}x{ny}x{nz} = {nx*ny*nz/1e6:.1f} M cells", flush=True)
    g = torch.Generator(device=DEV).manual_seed(S["seed"])
    k = torch.sqrt(F.K2)
    band = torch.exp(-0.5 * (torch.log(k.clamp(min=1e-3) / (2 * np.pi / 0.8)) / 0.6) ** 2)
    F.U = F.project(torch.randn((3, nz, ny, nx), device=DEV, generator=g) * band)
    F.U *= S["stir"] / float(F.grid().std())
    vol = sum(SF.source_volume(d) for d in S["drops"])
    mass_d, mass_all = vol / len(Pd), vol / (len(Pd) + len(Pp))
    cell_v = float(F.cell.prod())
    Pd_, Pp_ = torch.from_numpy(Pd).to(DEV), torch.from_numpy(Pp).to(DEV)
    t, it, alive_d, alive_p = 0.0, 0, 0, 0
    tk = [S["T"] - (S["frames"] - 1 - i) / (S["fps"] * S["slow"]) for i in range(S["frames"])]
    marks = sorted(set(S["looks"]) | set(tk))
    take_dir = os.path.join(ROOT, "out", "v2", f"s76_yidi_move_{name}")
    if tk:
        os.makedirs(take_dir, exist_ok=True)
        json.dump(DEVELOP, open(os.path.join(take_dir, "develop.json"), "w"))
    Gp_old, tp_old, refresh = None, 0.0, True
    panels = []
    t0 = time.time()
    while t < S["T"] - 1e-9:
        alive_d = int(np.searchsorted(Bd, t, side="right"))
        c = F.deposit(Pd_[:alive_d]) * (mass_d / cell_v) if alive_d else torch.zeros(F.n, device=DEV)
        Fz = F.tr.fwd(-S["g1"] * c, SF.KW) * F.lowF
        U_g = F.grid()
        umax = float(U_g.abs().max())
        dt = min(S["dt"], S["cfl"] * float(F.cell.min()) / max(umax, 1e-3))
        nxt = [m for m in marks if m > t + 1e-9]
        if nxt and nxt[0] - t < dt * 1.5:
            dt = nxt[0] - t
        if refresh:
            Gp_old, tp_old = F.grid_fine(), t
            alive_p = int(np.searchsorted(Bp, t, side="right"))
            refresh = False
        F.step(Fz, dt)
        U_new = F.grid()
        if alive_d:
            p = Pd_[:alive_d]
            v0 = F.sample(U_g, p)
            v1 = F.sample(U_new, p + dt * v0)
            p += 0.5 * dt * (v0 + v1)
            F.keep_in(p)
        t += dt
        it += 1
        due = any(abs(m - t) < 1e-6 for m in marks)
        if it % S["K"] == 0 or due:
            Gn = F.grid_fine()
            h = t - tp_old
            for a in range(0, alive_p, 8_000_000):
                q = Pp_[a : min(a + 8_000_000, alive_p)]
                v0 = F.sample(Gp_old, q)
                v1 = F.sample(Gn, q + h * v0)
                q += 0.5 * h * (v0 + v1)
                F.keep_in(q)
            refresh = True
        if due:
            step = max(40, alive_p // 10_000_000 + 1)  # torch.quantile takes at most 16 M values
            zq = float(torch.quantile(Pp_[:alive_p, 2][::step], 0.002))
            z_top = S["z_cam"] if S["z_cam"] is not None else zq
            chunks = lambda: [Pd_[:alive_d]] + [Pp_[a_ : min(a_ + 16_000_000, alive_p)] for a_ in range(0, alive_p, 16_000_000)]
            if any(abs(m - t) < 1e-6 for m in S["looks"]):
                rgb = render(chunks(), mass_all, S, z_top)
                im = tone_u8(printed(rgb))
                cv2.imwrite(os.path.join(OUT, f"{name}_t{t:05.2f}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 93])
                panels.append(cv2.resize(im, (960, 540), interpolation=cv2.INTER_AREA))
                print(f"[look] t={t:.2f} top z {zq:.3f}, mean {im.mean():.1f}, umax {umax:.2f}, {time.time()-t0:.0f} s", flush=True)
                if S["snap"] and t >= S["T"] - 1e-6:
                    np.save(os.path.join(OUT, f"{name}_snap.npy"), torch.cat(chunks()).cpu().numpy())
                    json.dump({"mass": mass_all, "t": t}, open(os.path.join(OUT, f"{name}_snap.json"), "w"))
            for i, m in enumerate(tk):
                if abs(m - t) < 1e-6:
                    # a half-open shutter: the particles at either end of it, along the velocity now
                    span = S["shutter"] / (S["fps"] * S["slow"])
                    moved = lambda s_: (q + s_ * span * F.sample(Gn, q) for q in chunks())
                    rgb = 0.5 * (render(moved(-0.25), mass_all, S, z_top) + render(moved(0.25), mass_all, S, z_top))
                    np.save(os.path.join(take_dir, f"take.linear_{i:03d}.npy"), rgb.astype(np.float16))
                    if i % 12 == 0:
                        print(f"[take] {i}/{len(tk)} t={t:.3f}, {time.time()-t0:.0f} s", flush=True)
    if panels:
        cv2.imwrite(os.path.join(OUT, f"{name}_sheet.jpg"), np.vstack(panels), [cv2.IMWRITE_JPEG_QUALITY, 90])


if __name__ == "__main__":
    args = sys.argv[1:]
    mode_look = args[0] == "look"
    if mode_look:
        args = args[1:]
    head = args[:2] if mode_look else args[:1]
    over = {}
    tail = args[len(head):]
    if tail:
        for kv in re.split(r",(?![^\[]*\])", tail[0]):  # not the commas inside a list
            k, v = kv.split("=")
            over[k] = json.loads(v)
    with torch.no_grad():
        if mode_look:
            look(head[0], head[1], over)
        else:
            run(head[0], over)
