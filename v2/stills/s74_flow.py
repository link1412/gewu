"""Shot 74's flow: a viscous film running down the ball. Thin-film (lubrication) equation on the ball's surface, in a flat patch of azimuthal coordinates about the opening:

    h_t + div( h^3 / (3 mu) * (G - gn * grad h) ) = 0

G is gravity along the surface, varying over the ball. gn * grad h is the hydrostatic pressure in the film, the term that makes a viscous current's nose thick and round. A precursor film b stands in for the contact line, as is usual for this equation. The opening is a reservoir whose level breathes a little and unevenly, which sends waves down the run and makes it run ahead in places. Gravity's flux is upwinded; everything is explicit. Second order, so the step is bounded by ds^2 / (4 D), D = h^3 gn / (3 mu).

Surface tension (a fourth-order term) is left out. I tried it with a constant-coefficient implicit biharmonic through the FFT: it went unstable even with gravity off, since the mobility varies by a factor of about 1e5 across the front (measured in a small test, the cause of the instability is my reading). So there is no capillary ridge behind the front and no fingering of the contact line in the sense of Huppert 1982; gn is set by eye and stands in for surface tension's rounding too.

A map X carries each point back to where its material left the reservoir, by semi-Lagrangian steps with the surface speed h^2 / (2 mu) * (G - gn * grad h). Texture read through X is stretched by the flow: that is where the streaks come from.

Limits: small slopes, which a blob at the opening does not have; the patch is taken as flat, its metric ignored; no overhang and no drop leaving the surface; constant viscosity, no yield stress. Numbers: rho g 1079 dyn/cm3 for density 1.1 (estimate); mu is a choice that gives the speed wanted, see P0 in s74_tangyuan.py.
"""

import hashlib
import json
import os
import time

import cv2
import numpy as np

RHO_G = 1079.0


def solve(p, inflow, gravity_c, gravity_r, ds, cache_dir):
    """inflow: bool array, the reservoir. gravity_c, gravity_r: gravity along the columns and rows, dyn/cm3. Returns h and the map X (2 x ny x nx, in pixels of this grid). Cached by the inputs."""
    ny, nx = inflow.shape
    key = hashlib.md5(json.dumps({k: p[k] for k in ("mu", "gn", "b", "h0", "T")}, sort_keys=True).encode() + inflow.tobytes() + gravity_c.tobytes() + gravity_r.tobytes()).hexdigest()[:12]
    path = os.path.join(cache_dir, f"flow_{key}.npz")
    if os.path.exists(path):
        print(f"[flow] cached {path}", flush=True)
        return dict(np.load(path))
    t0 = time.time()
    mu, gn, b, h0 = p["mu"], p["gn"], p["b"], p["h0"]
    h_cap = 1.3 * h0
    D_max = h_cap**3 * gn / (3 * mu)
    u_max = 3.0 * h_cap**2 * max(np.abs(gravity_c).max(), np.abs(gravity_r).max()) / (3 * mu)  # the kinematic wave runs at 3 times the mean speed
    dt = 0.8 / (4.0 * D_max / (ds * ds) + 2.0 * u_max / ds)
    steps = int(p["T"] / dt)
    soft = cv2.GaussianBlur(inflow.astype(np.float32), (0, 0), 1.5)
    h = b + (h0 - b) * soft
    jj, ii = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
    X = np.stack([jj, ii])
    edge = np.minimum.reduce([jj, nx - 1 - jj, ii, ny - 1 - ii])
    sponge = np.clip(edge / 12.0, 0.0, 1.0)
    x_lat = (jj - jj[inflow].mean()) * ds
    y_lat = (ii - ii[inflow].mean()) * ds
    G_c_f = 0.5 * (gravity_c + np.roll(gravity_c, -1, 1))
    G_r_f = 0.5 * (gravity_r + np.roll(gravity_r, -1, 0))
    k_map = 4
    for n in range(steps):
        t = n * dt
        hr_c, hr_r = np.roll(h, -1, 1), np.roll(h, -1, 0)
        up_c = np.where(G_c_f > 0, h, hr_c)
        up_r = np.where(G_r_f > 0, h, hr_r)
        m_c, m_r = 0.5 * (h + hr_c), 0.5 * (h + hr_r)
        F_c = (up_c**3 * G_c_f - m_c**3 * gn * (hr_c - h) / ds) / (3 * mu)
        F_r = (up_r**3 * G_r_f - m_r**3 * gn * (hr_r - h) / ds) / (3 * mu)
        h = h - dt * (F_c - np.roll(F_c, 1, 1) + F_r - np.roll(F_r, 1, 0)) / ds
        h = np.clip(h, b, h_cap)
        # the reservoir breathes: long crests across the run, not ridges along it
        level = h0 * (1.0 + 0.14 * np.sin(2 * np.pi * (x_lat / 1.1 + 0.8 * t)) + 0.06 * np.sin(2 * np.pi * (-x_lat / 0.7 + 1.37 * t + 0.3)))
        h = h * (1.0 - soft) + level * soft
        h = b + (h - b) * sponge
        # the map: back along the surface speed, each point takes what was upstream of it
        if n % k_map == 0:
            hc = np.maximum(h - b, 0.0)
            speed = hc * hc / (2 * mu) * dt * k_map / ds
            u = speed * (gravity_c - gn * (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * ds))
            v = speed * (gravity_r - gn * (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * ds))
            mx, my = jj - np.clip(u, -3, 3), ii - np.clip(v, -3, 3)
            X = np.stack([cv2.remap(X[0], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), cv2.remap(X[1], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)])
            X[0][inflow] = jj[inflow]
            X[1][inflow] = ii[inflow]
    if not np.isfinite(h).all():
        raise SystemExit("flow: blew up")
    print(f"[flow] {steps} steps of {dt * 1e3:.3f} ms on {nx} x {ny} in {time.time() - t0:.0f} s; h max {h.max():.3f} cm; covers {(h > 2 * b).mean():.3f} of the patch", flush=True)
    np.savez(path, h=h, X=X)
    return {"h": h, "X": X}
