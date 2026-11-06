"""The light of the CMA 1957.40 photo, read off the photo: the floor's shadow (the key's direction, size and
distance), the floor's tone, and the comparison of a render with the photo (docs/optics/cma_1957_40.md).

    python3 -I objects/ru_washer/light.py shadow [--out out/ru/light]          # fit the key to the floor's shadow
    python3 -I objects/ru_washer/light.py compare RAW.exr [--out out/ru/light/cmp] [--res WxH]
                                                                               # a render against the photo

Frames: the object frame of form.py (right-handed, mm, z up, z = 0 the ground, the camera on -y). The photo's
right is the object frame's +x (form.camera: right = (1, 0, 0) for no yaw).

The shadow model. The washer as an occluder is the solid of revolution under its outer profile (a ray that enters
the bowl's mouth ends on its inside, so for the floor the bowl is solid). A floor point's visibility of a lamp is the
fraction of the lamp's area it sees past that solid (rays sampled over the lamp). The photo's floor luminance is
Y = Y0(X) (V_key (1 - f) + f): Y0 the unshadowed floor (a smooth field fitted outside the shadow), f the share of
the floor's light that comes from everything else (fill, the room, the washer's own glow) taken as unshadowed [A].
So V = Y / Y0 is the photo's visibility map, independent of the cloth's BRDF; the lamp is fitted to it.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import form as fm  # noqa: E402

PHOTO = os.path.join(ROOT, "ref/ru/photos/cma_1957.40.jpg")
Y709 = np.array([0.2126, 0.7152, 0.0722])


# --- the photo ------------------------------------------------------------------------------------------------
def photo_linear(scale=4):
    """The photo (sRGB, its ICC profile is sRGB IEC61966-2.1) decoded to linear, block-averaged by `scale`."""
    from PIL import Image
    im = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float64) / 255.0
    lin = np.where(im <= 0.04045, im / 12.92, ((im + 0.055) / 1.055) ** 2.4)
    H, W = lin.shape[0] // scale * scale, lin.shape[1] // scale * scale
    return lin[:H, :W].reshape(H // scale, scale, W // scale, scale, 3).mean((1, 3))


def cam_params():
    C = json.load(open(fm.CAMERA))
    p = {k: v["value"] for k, v in C["params"].items()}
    p["f_px"] = C["f_px"]["value"]
    return p


def form_params():
    F = json.load(open(fm.FORM))
    return {k: v["value"] for k, v in F["fitted"].items()}


def envelope(step=0.25):
    """(z, R(z)): the outer profile's largest radius at each height, foot to lip, on a `step` mm grid."""
    prof = fm.closed_profile(form_params(), inner=False)
    C = prof["C"]
    H = float(C[:, 1].max())
    z = np.linspace(0.0, H, int(H / step) + 1)
    R = np.zeros_like(z)
    # the profile's outer side: for each z the largest r of the polyline's crossings
    for i in range(len(C) - 1):
        (r0, z0), (r1, z1) = C[i], C[i + 1]
        lo, hi = min(z0, z1), max(z0, z1)
        m = (z >= lo) & (z <= hi)
        if not m.any():
            continue
        w = (z[m] - z0) / (z1 - z0) if z1 != z0 else 0.5
        R[m] = np.maximum(R[m], r0 + w * (r1 - r0))
    return z, R


def pixel_rays(shape, scale):
    """Camera centre and unit ray directions (object frame) for the centres of the blocks of photo_linear(scale)."""
    p = cam_params()
    C, Rm = fm.camera(p)
    h, w = shape
    W, H = fm.PHOTO_SIZE
    xs = (np.arange(w) + 0.5) * scale
    ys = (np.arange(h) + 0.5) * scale
    X, Y = np.meshgrid(xs, ys)
    q = np.stack([(X - W / 2) / p["f_px"], (Y - H / 2) / p["f_px"], np.ones_like(X)], -1)
    d = q @ Rm                                  # rows of Rm are right, down, forward
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    return C, d


def hits_solid(O, D, zR, tmax=None):
    """For rays O + t D (O (n,3) or (3,), D (n,3)): does the ray (or the segment up to t = tmax, default to where
    it leaves 0 <= z <= H) pass inside the solid r < R(z)? Marched over z (no ray here is horizontal)."""
    z, R = zR
    O = np.broadcast_to(O, D.shape)
    out = np.zeros(len(D), bool)
    dz = D[:, 2]
    ok = np.abs(dz) > 1e-9
    for zi, Ri in zip(z, R):
        t = (zi - O[:, 2]) / np.where(ok, dz, 1.0)
        good = ok & (t > 1e-6) if tmax is None else ok & (t > 1e-6) & (t < tmax)
        P = O + t[:, None] * D
        out |= good & (P[:, 0] ** 2 + P[:, 1] ** 2 < Ri * Ri)
    return out


def floor_points(C, d):
    """Where the rays meet the floor z = 0 (nan if they go up)."""
    t = -C[2] / d[..., 2]
    P = C + t[..., None] * d
    P[t <= 0] = np.nan
    return P


# --- lamps ----------------------------------------------------------------------------------------------------
def rect_lamp(az_deg, el_deg, dist, w, h, aim=(0.0, 0.0, 15.0)):
    """A rectangle facing `aim` from (azimuth, elevation, distance) about `aim` in the photographer's terms of
    optics/studio.py: azimuth 0 the camera's side (-y), +90 the photo's right (+x). Returns centre, normal, the
    two half-edge vectors (width horizontal)."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    aim = np.asarray(aim, float)
    u = np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)])
    c = aim + dist * u
    n = -u
    hor = np.cross([0, 0, 1.0], n)
    hor /= np.linalg.norm(hor)
    ver = np.cross(n, hor)
    return c, n, hor * w / 2, ver * h / 2


def lamp_samples(lamp, k=8):
    c, n, a, b = lamp
    u = (np.arange(k) + 0.5) / k * 2 - 1
    U, V = np.meshgrid(u, u)
    return c + U.ravel()[:, None] * a + V.ravel()[:, None] * b


def floor_irradiance(X, lamp, zR, k=8, occlude=True):
    """Irradiance (relative: a lamp of unit radiance) at floor points X (n,3), and the visible fraction."""
    S = lamp_samples(lamp, k)
    c, n, a, b = lamp
    area = 4 * np.linalg.norm(a) * np.linalg.norm(b)
    E = np.zeros(len(X))
    Ev = np.zeros(len(X))
    for s in S:
        D = s - X
        r2 = (D * D).sum(1)
        r = np.sqrt(r2)
        Dn = D / r[:, None]
        g = np.maximum(Dn[:, 2], 0) * np.maximum(-(Dn @ n), 0) / r2 * area / len(S)
        E += g
        if occlude:
            blocked = hits_solid(X, Dn, zR, tmax=r)
            Ev += g * ~blocked
    return E, (Ev if occlude else E)


# --- the shadow fit -------------------------------------------------------------------------------------------
def poly_terms(X, Y, deg=3):
    return np.stack([X ** i * Y ** j for i in range(deg + 1) for j in range(deg + 1 - i)], -1)


def shadow_data(scale=8):
    """The photo's floor at 1/scale: luminance, floor points, the washer's mask, the unshadowed field Y0 (a cubic
    in floor (x, y) fitted, robustly, to the floor outside the shadow: pixels within 10% of the fit, iterated) and
    the visibility map V = Y / Y0."""
    lin = photo_linear(scale)
    Y = lin @ Y709
    C, d = pixel_rays(Y.shape, scale)
    zR = envelope()
    washer = hits_solid(C, d.reshape(-1, 3), zR).reshape(Y.shape)
    P = floor_points(C, d)
    from scipy import ndimage as nd
    near = nd.binary_dilation(washer, iterations=max(1, 16 // scale))
    floor = ~near & np.isfinite(P[..., 0])
    Xs, Ys = P[..., 0] / 100.0, P[..., 1] / 100.0
    # Y0 is fitted in log (the field spans a factor of 20 from front to back); the region used is the floor up
    # to 300 mm behind the axis (beyond, the photo's black backdrop and JPEG floor)
    use = floor & (P[..., 1] < 300.0)
    w = use.copy()
    A = poly_terms(Xs, Ys)
    for _ in range(12):
        coef, *_ = np.linalg.lstsq(A[w], np.log(np.maximum(Y[w], 1e-5)), rcond=None)
        Y0 = np.exp(A @ coef)
        w = use & (Y > 0.9 * Y0)
    V = Y / Y0
    return {"Y": Y, "P": P, "washer": washer, "floor": floor, "use": use, "Y0": Y0, "V": V, "fit_mask": w,
            "scale": scale, "zR": zR}


def model_V(D, lamp, f, k=8):
    """The model's visibility map on the photo's floor pixels (D: shadow_data) for a lamp and a fill share f."""
    m = D["use"]
    X = D["P"][m]
    E, Ev = floor_irradiance(X, lamp, D["zR"], k)
    V = np.full(D["Y"].shape, np.nan)
    V[m] = (1 - f) * Ev / E + f
    return V


def fit_shadow(D, out):
    """Fit (azimuth, elevation, size, fill) of a square lamp at a fixed distance to the photo's V map near the
    shadow, for several distances (the distance and the size trade against each other: the penumbra's width goes
    with the lamp's angular size; the distance shows only in the falloff, fitted apart)."""
    from scipy.optimize import least_squares
    m = D["use"] & (D["P"][..., 0] < 60.0) & (D["P"][..., 1] > -80.0)       # the left and back of the washer
    m[:, 1::2] = False                                                       # every other pixel (speed)
    Vp = D["V"][m]
    X = D["P"][m]
    zR = envelope(0.5)
    res = []
    for dist in (500.0, 800.0, 1200.0):
        def F(x):
            az, el, size, f = x
            lamp = rect_lamp(az, el, dist, size, size)
            E, Ev = floor_irradiance(X, lamp, zR, 6)
            return (1 - f) * Ev / E + f - np.clip(Vp, 0, 1.2)
        best = None
        for az0 in (40.0, 70.0, 100.0):
            for el0 in (25.0, 45.0):
                r = least_squares(F, [az0, el0, 0.4 * dist, 0.05], bounds=([-10, 3, 20, 0], [170, 85, 2.5 * dist, 0.5]),
                                  x_scale=[5, 5, 50, 0.02], diff_step=[1e-3, 1e-3, 1e-2, 1e-2], max_nfev=60)
                if best is None or r.cost < best.cost:
                    best = r
        az, el, size, f = best.x
        rms = float(np.sqrt(np.mean(best.fun ** 2)))
        res.append({"dist_mm": dist, "azimuth_deg": float(az), "elevation_deg": float(el), "size_mm": float(size),
                    "angular_size_deg": float(math.degrees(2 * math.atan(size / 2 / dist))), "fill_share": float(f),
                    "rms_V": rms, "n_px": int(m.sum())})
        print(json.dumps(res[-1]), flush=True)
    json.dump(res, open(os.path.join(out, "shadow_fit.json"), "w"), indent=1)
    return res


def show_V(D, Vm, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2 if Vm is not None else 1, figsize=(16, 5))
    ax = np.atleast_1d(ax)
    V = np.where(D["use"], D["V"], np.nan)
    ax[0].imshow(V, vmin=0, vmax=1.2, cmap="gray")
    ax[0].contour(np.nan_to_num(V, nan=1), levels=[0.25, 0.5, 0.75], colors=["r", "y", "g"], linewidths=0.6)
    ax[0].set_title("photo: V = Y / Y0 (floor)")
    if Vm is not None:
        ax[1].imshow(Vm, vmin=0, vmax=1.2, cmap="gray")
        ax[1].contour(np.nan_to_num(V, nan=1), levels=[0.25, 0.5, 0.75], colors=["r", "y", "g"], linewidths=0.6)
        ax[1].contour(np.nan_to_num(Vm, nan=1), levels=[0.25, 0.5, 0.75], colors=["r", "y", "g"], linewidths=0.6,
                      linestyles="dashed")
        ax[1].set_title("model V (dashed) and photo (solid): 0.25 red, 0.5 yellow, 0.75 green")
    plt.savefig(path, dpi=80, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["shadow"])
    ap.add_argument("--out", default=os.path.join(ROOT, "out/ru/light"))
    ap.add_argument("--scale", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.cmd == "shadow":
        D = shadow_data(a.scale)
        show_V(D, None, os.path.join(a.out, "shadow_V_photo.png"))
        res = fit_shadow(D, a.out)
        best = min(res, key=lambda r: r["rms_V"])
        lamp = rect_lamp(best["azimuth_deg"], best["elevation_deg"], best["dist_mm"], best["size_mm"], best["size_mm"])
        show_V(D, model_V(D, lamp, best["fill_share"]), os.path.join(a.out, "shadow_V.png"))


if __name__ == "__main__":
    main()
