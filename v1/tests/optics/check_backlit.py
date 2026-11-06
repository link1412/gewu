"""Test e: does light go through the backlit plate, and how much? (plate_marble-backlit, after its --preview)

    python3 -I tests/optics/check_backlit.py [--photons 40000]

In the rigs sheet the backlit plate does not read as translucent. Three numbers:
1. Calibration, from the render itself: the sky-blue wall in the ground group alone, at the top rows where the camera
   sees the flat wall above the cove; its irradiance from the ground lamp integrated over the lamp (48 x 48 points);
   its camera-G albedo from scene.cycles.json. Gives k: the raw G of a white Lambertian reflector under 1 lux of the
   rig's light, times pi.
2. The plate's transmittance as rendered: in the through group alone, each plate pixel's raw G over what a perfect
   Lambertian transmitter would give there, k E_back / pi, with E_back the through lamp's irradiance on the back face
   behind that pixel (the plate taken as thin: light spreads sideways in it by a few mm, so pixels near the lamp's
   axis, where E_back changes slowly, are the fair ones).
3. The same slab by Monte Carlo (numpy): collimated light at normal incidence, smooth faces (Fresnel, n 1.5, total
   internal reflection), isotropic scattering, marble's G-channel coefficients as pbrt's preset has them (sigma_s
   2.62, sigma_a 0.0041 per mm; Jensen 2001 [M]); transmittance and the number of scatterings a transmitted path
   takes (the render stops at the recipe's maxdepth bounces), for several thicknesses.
And the brightness of the plate against the background and against the brightest pixels in the recipe's mix.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "optics"))
import camera as C  # noqa: E402
from studio import Studio  # noqa: E402

D = os.path.join(ROOT, "out/recipes/plate_marble-backlit")
ETA = 1.5
SIG_S, SIG_A = 2.62, 0.0041          # marble, G, per mm (pbrt-v4 media.cpp "Marble"; Jensen et al. 2001)


def rays(cam, W, H):
    """World ray directions through every pixel centre (pbrt's perspective camera; image right = up x dir)."""
    d = np.array(cam["aim"]) - np.array(cam["eye"])
    d /= np.linalg.norm(d)
    up = np.array([0, 0, 1.0])
    r = np.cross(up, d)
    r /= np.linalg.norm(r)
    u = np.cross(d, r)
    th = math.tan(math.radians(cam["fov_deg"]) / 2)               # across the shorter side (the height)
    tw = th * W / H
    x = ((np.arange(W) + 0.5) / W - 0.5) * 2 * tw
    y = (0.5 - (np.arange(H) + 0.5) / H) * 2 * th
    X, Y = np.meshgrid(x, y)
    return d + X[..., None] * r + Y[..., None] * u


def irradiance(L, P, n):
    """Irradiance (lux) at points P (..., 3) with normal n from lamp L (build.json's), by 48 x 48 points."""
    if L["shape"] == "disk":
        S = Studio._disk_samples(np.array(L["centre"]), np.array(L["normal"]), L["radius"])
        area = math.pi * L["radius"] ** 2
    else:
        S = Studio._rect_samples(np.array(L["corners"]))
        area = L["area_mm2"]
    Pf = P.reshape(-1, 3)
    E = np.zeros(len(Pf))
    for i in range(0, len(Pf), 2048):
        q = S[None, :, :] - Pf[i:i + 2048, None, :]
        r2 = (q * q).sum(-1)
        qn = q / np.sqrt(r2)[..., None]
        E[i:i + 2048] = (L["luminance"] * np.maximum(qn @ n, 0) * np.maximum(-(qn @ np.array(L["normal"])), 0) / r2).sum(1) * area / len(S)
    return E.reshape(P.shape[:-1])


def fresnel(cos_i, eta):
    """Unpolarised Fresnel reflectance from a medium into one eta_t / eta_i = eta."""
    sin_t2 = (1 - cos_i ** 2) / eta ** 2
    tir = sin_t2 >= 1
    cos_t = np.sqrt(np.clip(1 - sin_t2, 0, 1))
    rs = (cos_i - eta * cos_t) / (cos_i + eta * cos_t)
    rp = (eta * cos_i - cos_t) / (eta * cos_i + cos_t)
    return np.where(tir, 1.0, 0.5 * (rs * rs + rp * rp))


def slab(d, n, rng, sig_s=SIG_S, sig_a=SIG_A, eta=ETA):
    """Monte Carlo through a slab 0 < z < d: collimated, normal incidence. (T, R, scatterings of transmitted paths)"""
    st = sig_s + sig_a
    w = np.full(n, 1 - fresnel(np.ones(1), eta)[0])                 # weight after entering
    z = np.zeros(n)
    mu = np.ones(n)                                                  # direction cosine along +z
    k = np.zeros(n, int)
    alive = np.ones(n, bool)
    T = R = 0.0
    Tk = []
    while alive.any():
        i = np.nonzero(alive)[0]
        s = -np.log(rng.random(len(i))) / st
        zn = z[i] + mu[i] * s
        out = (zn <= 0) | (zn >= d)
        # inside: scatter (absorption as weight), isotropic
        j = i[~out]
        z[j] = zn[~out]
        w[j] *= sig_s / st
        mu[j] = 2 * rng.random(len(j)) - 1
        k[j] += 1
        # at a face: Fresnel from inside (eta inside = ETA, outside 1), reflect with probability F
        j = i[out]
        top = zn[out] >= d
        z[j] = np.where(top, d, 0.0)
        F = fresnel(np.abs(mu[j]), 1 / eta)
        refl = rng.random(len(j)) < F
        mu[j[refl]] *= -1
        esc = j[~refl]
        et = top[~refl]
        T += w[esc[et]].sum()
        R += w[esc[~et]].sum()
        Tk.append(k[esc[et]])
        alive[esc] = False
        alive &= w > 1e-4                                             # absorbed: negligible weight
    return T / n, R / n, np.concatenate(Tk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photons", type=int, default=40000)
    a = ap.parse_args()
    b = json.load(open(os.path.join(D, "build.json")))
    recipe = b["recipe"]
    lamps = {L["name"]: L for L in b["lamps"]}
    W, H = b["res"]
    cam = b["camera"]
    eye = np.array(cam["eye"])
    dirs = rays(cam, W, H)
    raw = {g: C.read_raw(os.path.join(D, f"x.{g}.exr")) for g in b["groups"]}

    # 1. calibration on the wall above the cove
    back = np.array([0, 1.0, 0])                                     # azimuth 0: the backdrop is towards +Y
    t = (b["backdrop"]["depth"] - eye @ back) / (dirs @ back)        # the object is centred at x = y = 0
    P = eye + t[..., None] * dirs
    wall = P[..., 2] > b["backdrop"]["cove"] + 5
    rows = np.nonzero(wall.all(1))[0]
    cols = slice(W // 4, 3 * W // 4)
    if len(rows) < 3:
        raise SystemExit("too few rows see the flat wall")
    Pw = P[rows][:, cols]
    Ew = irradiance(lamps["ground"], Pw, -back)
    sc = json.load(open(os.path.join(D, "scene.cycles.json")))
    rho = next(o["material"]["reflectance"] for o in sc["objects"] if o.get("file") == "backdrop.ply")[1]
    k = float(np.median(raw["ground"][rows][:, cols, 1] * math.pi / (rho * Ew)))
    print(f"1. calibration: {len(rows)} rows of wall, irradiance {Ew.min():.0f}-{Ew.max():.0f} lux from the ground lamp, "
          f"camera-G albedo {rho:.4f}: a white Lambertian surface under 1 lux reads {k / math.pi:.4g} raw G")

    # 2. the plate as rendered (front face at y = -thickness/2; the generator's plate is 4 mm, centred on y = 0)
    th = float(recipe.get("plate_thickness_mm", 4.0))
    tf = (-th / 2 - eye[1]) / dirs[..., 1]
    Pf = eye + tf[..., None] * dirs
    alb = C.read_raw(os.path.join(D, "x.albedo.exr"))
    sky = np.abs(alb - np.array(next(o["material"]["reflectance"] for o in sc["objects"]
                                     if o.get("file") == "backdrop.ply"))).max(2) < 0.02
    plate = ~sky & (alb.max(2) <= 1.01) & (np.hypot(Pf[..., 0], Pf[..., 2] - (b["box_mm"][0][2] + b["box_mm"][1][2]) / 2)
                                         < 120 - 3)                   # off the rounded edge
    Pb = Pf.copy()
    Pb[..., 1] = th / 2                                              # the back face behind each pixel
    Eb = irradiance(lamps["through"], Pb, back)                      # the back face looks back, at the lamp
    T = raw["through"][..., 1] * math.pi / (k * Eb)
    near = plate & (Eb > 0.8 * Eb[plate].max())
    print(f"2. the plate as rendered (through group alone): back-face irradiance up to {Eb[plate].max():.0f} lux in the "
          f"frame; effective diffuse transmittance (G) where it is within 80% of that: median {np.median(T[near]):.3f} "
          f"({near.sum()} px), over the whole plate in the frame {np.median(T[plate]):.3f}")

    # 3. Monte Carlo
    rng = np.random.default_rng(1)
    depth = int(recipe["render"]["maxdepth"])
    print(f"3. Monte Carlo slab, marble G (sigma_s {SIG_S}, sigma_a {SIG_A} /mm), n {ETA}, {a.photons} photons:")
    for d in (1.0, 2.0, 4.0, 8.0):
        Tm, Rm, ks = slab(d, a.photons, rng)
        over = float((ks > depth - 2).mean()) if len(ks) else 0.0
        print(f"   {d:g} mm: T {Tm:.3f}, R {Rm:.3f}; transmitted paths scatter {np.median(ks):.0f} times (median), "
              f"{np.percentile(ks, 90):.0f} (90%); beyond the render's {depth} bounces: {over:.1%}")

    # 4. how bright, in the recipe's mix
    mix = recipe.get("mix", {})
    base = sum(2 ** mix.get(g, 0.0) * raw[g] for g in b["groups"])
    G = base[..., 1]
    p999 = np.percentile(G, 99.9)
    hi = G >= p999
    who = {g: float((2 ** mix.get(g, 0.0) * raw[g][..., 1])[hi].sum() / G[hi].sum()) for g in b["groups"]}
    print(f"4. in the mix {mix}: the plate's brightest 10% (G) {np.percentile(G[plate], 90):.4g}, its median "
          f"{np.median(G[plate]):.4g}; the sky's median {np.median(G[sky]):.4g} "
          f"({math.log2(np.median(G[plate]) / np.median(G[sky])):+.2f} stops plate over sky); the 99.9th percentile "
          f"{p999:.4g} ({math.log2(p999 / np.median(G[plate])):+.2f} stops over the plate's median), made by "
          + ", ".join(f"{g} {v:.0%}" for g, v in who.items()))


if __name__ == "__main__":
    main()
