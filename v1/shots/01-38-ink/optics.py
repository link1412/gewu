"""Optics for shots 1 and 38: a wet, inked sheet of xuan paper lit from behind, seen obliquely through a macro lens.

Renderer (preview, numpy; not path traced): for every pixel the ray from a pinhole camera meets the paper plane;
the sheet there is a Kubelka-Munk layer (scattering S, absorption K, per wavelength) built from the simulation's
maps; the light leaving the front is
    L = T_KM * E_back / pi + R_KM * E_front / pi
with E_back the irradiance of the lamps behind the paper (Lambertian discs, integrated numerically, plus since round 2 an
'ambient' back-light: a diffuse source larger than the field, uniform irradiance) and E_front a
dim uniform fill. Round 2b: lamps may be directional (radiance ~ cos^n), the lens veil has a halo and a
uniform part (veil), the paper texture is tiled outside the simulated patch and pre-filtered to the pixel footprint, and
the thick ink film mirrors the dim surroundings in front of the sheet (sheen, Fresnel at the view angle). The sheet is flat and the surroundings dark, so interreflection is left out; lateral light
diffusion inside a 0.1 mm sheet is far below a pixel here (0.02 mm). Thin-lens defocus is applied per pixel
(blur diameter from the depth), by interpolating between disc-blurred copies. Spectral (10 nm) -> CIE XYZ ->
linear BT.709 (D65 white) -> sRGB encoding, the way tools/compare.py decodes the original.
"""
import os
import sys

import numpy as np
from numpy.fft import irfft2, rfft2
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera as cam  # noqa: E402

LAM = np.arange(400.0, 701.0, 10.0)


def _cmf():
    lam = cam.pbrt_array("CIE_lambda")
    cmf = np.array([np.interp(LAM, lam, cam.pbrt_array(n)) for n in ("CIE_X", "CIE_Y", "CIE_Z")])
    d65 = np.interp(LAM, cam.pbrt_array("CIE_Illum_D6500")[0::2], cam.pbrt_array("CIE_Illum_D6500")[1::2])
    return cmf, d65


CMF, D65 = _cmf()
WHITE = CMF @ D65
WHITE = WHITE / WHITE[1]
M709 = cam.rgb709_from_xyz(WHITE)


def blackbody(T):
    l = LAM * 1e-9
    c, h, kb = 299792458.0, 6.62606957e-34, 1.3806488e-23
    b = 1 / (l ** 5 * (np.exp(h * c / (l * kb * T)) - 1))
    return b / np.interp(560.0, LAM, b)


def spectrum(spec):
    """A light's spectrum from params: blackbody T, or 'sky': D65 x (lambda/550)^-beta x exp(-gamma ((lambda-550)/100)^2)
    (a smooth two-parameter stand-in for a filtered daylight / twilight sky; gamma > 0 narrows it toward cyan-green)."""
    if spec["kind"] == "blackbody":
        return blackbody(spec["T"])
    if spec["kind"] == "sky":
        x = (LAM - 550.0) / 100.0
        s = D65 * (LAM / 550.0) ** (-spec["beta"]) * np.exp(-spec.get("gamma", 0.0) * x * x)
        return s / np.interp(560.0, LAM, s)
    raise SystemExit(f"unknown light spectrum {spec}")


def fresnel(mu, n):
    """Unpolarised Fresnel reflectance of a smooth dielectric (index n) for incidence cosine mu, from air."""
    mu = np.clip(mu, 1e-6, 1)
    st2 = (1 - mu * mu) / (n * n)
    mt = np.sqrt(np.maximum(1 - st2, 0))
    rs = (mu - n * mt) / (mu + n * mt)
    rp = (n * mu - mt) / (n * mu + mt)
    return 0.5 * (rs * rs + rp * rp)


def km(SX, KX):
    """Kubelka-Munk reflectance and transmittance of a layer (no substrate): SX = S d, KX = K d (arrays)."""
    SX = np.maximum(SX, 1e-6)
    a = 1 + KX / SX
    b = np.sqrt(np.maximum(a * a - 1, 1e-12))
    bs = np.minimum(b * SX, 50)
    sh, ch = np.sinh(bs), np.cosh(bs)
    den = a * sh + b * ch
    return sh / den, b / den


# ---------------------------------------------------------------- the sheet
def _edge_corrected(g, band=40):
    """paper.py drops the parts of fibres that cross the patch edge, so the outer ~1.25 mm (half a fibre) of the
    grammage map is thin: row/column means fall from 1.0 to 0.55 at the edge [M]. Seen through a backlight that is a
    bright line wherever the patch ends; once the texture is tiled (round 2b) the seams show as lines converging
    to the vanishing point. Divide out the deficit (smoothed row and column means, outer 'band' cells only)."""
    g = np.asarray(g, float)
    out = g
    for ax in (0, 1):
        m = ndimage.gaussian_filter1d(g.mean(axis=1 - ax), 3.0, mode="nearest")
        ref = m[band:-band].mean()
        corr = np.ones_like(m)
        corr[:band] = m[:band] / ref
        corr[-band:] = m[-band:] / ref
        corr = np.minimum(corr, 1.0)
        out = out / (corr[:, None] if ax == 0 else corr[None, :])
    return out.astype(np.float32)


class Sheet:
    """Maps from sim.py, sampled at paper points (x, y) in mm."""

    def __init__(self, maps_path, P):
        d = np.load(maps_path)
        self.P = P
        self.x0, self.y0, self.dx, self.dxo = (float(d[k]) for k in ("x0", "y0", "dx", "dxo"))
        self.g = _edge_corrected(d["grammage"])
        self.sat = d["sat"]
        names = [c["name"] for c in P["ink"]["classes"]]
        self.carbon = {n: d[f"sigma_{n}"] + d[f"mobile_{n}"] for n in names}      # g/m^2 (suspended counts too)
        self.a = P["ink"]["pool_radius_mm"]
        self.pool = d["pool"].astype(np.float32)                                # 1 where the ink pool stood

    def sample(self, arr, x, y, fine=False, mode="nearest"):
        dx = self.dxo if fine else self.dx
        fx = (x - self.x0) / dx - 0.5
        fy = (y - self.y0) / dx - 0.5
        return ndimage.map_coordinates(arr, [fy, fx], order=1, mode=mode)

    def grammage(self, x, y, foot=None):
        """Local grammage at paper points. Round 2b: the formation is a stationary texture, so outside the simulated
        patch (52 x 54 mm) it is tiled (mode 'wrap'; paper.py's floc field is periodic and the seam differs from
        neighbouring rows by the same 0.20 as any two rows [M]). r1/r2 clamped it ('nearest'): far above the bleed (shot
        38 sees paper up to y = 280 mm) every column then repeated the patch's last row, a fan of streaks along the
        lines x = const [M, r2 checker]. Also pre-filtered to the pixel's footprint on the paper (foot, mm), so a pixel
        that covers 20 fibre cells averages them instead of point-sampling one (no aliasing)."""
        if foot is None:
            return self.sample(self.g, x, y, fine=True, mode="wrap")
        if not hasattr(self, "_gmip"):
            self._gsig = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]          # Gaussian sigma in 0.05 mm cells
            self._gmip = [self.g] + [ndimage.gaussian_filter(self.g, s, mode="wrap") for s in self._gsig[1:]]
        sig = 0.5 * np.asarray(foot) / self.dxo                          # footprint (mm) -> sigma in cells
        lv = np.interp(sig, self._gsig, np.arange(len(self._gsig)))
        i0 = np.minimum(np.floor(lv).astype(int), len(self._gsig) - 2)
        w = lv - i0
        out = np.zeros_like(x, dtype=float)
        for i in range(len(self._gsig) - 1):
            m = i0 == i
            if m.any():
                a = self.sample(self._gmip[i], x[m], y[m], fine=True, mode="wrap")
                b = self.sample(self._gmip[i + 1], x[m], y[m], fine=True, mode="wrap")
                out[m] = (1 - w[m]) * a + w[m] * b
        return out

    def optics(self, x, y, O, foot=None):
        """Spectral R, T (n, nlam) at paper points (foot: pixel footprint on the paper, mm, for the texture filter)."""
        g = self.grammage(x, y, foot)
        w = np.clip(self.sample(self.sat, x, y), 0, 1)
        p = O["paper"]
        bw = self.P["paper"]["basis_weight_gsm"] * 1e-3                 # kg/m^2
        SX = p["s_m2_per_kg"] * bw * g * (1 - w * (1 - p["wet_scatter_factor"]))
        lam = LAM[None, :] / 550.0
        KX = p["k550_m2_per_kg"] * bw * g[:, None] * lam ** (-p["k_slope"])
        for c in self.P["ink"]["classes"]:
            n = c["name"]
            sig = self.sample(self.carbon[n], x, y)
            KX = KX + 2 * O["carbon"]["mac550_m2_per_g"] * sig[:, None] * lam ** (-O["carbon"]["aae"][n])
        R, T = km(SX[:, None] * np.ones_like(lam), KX)
        return R, T, w


# ---------------------------------------------------------------- lamps behind the paper
def disc_view_factor(a, h, r):
    """View factor from a small patch to a coaxial-parallel Lambertian disc (radius r, at distance h, patch offset a from
    the disc axis): F = (1 - (a^2 + h^2 - r^2) / sqrt((a^2 + h^2 + r^2)^2 - 4 a^2 r^2)) / 2  [the standard configuration
    factor "differential planar element to a parallel disc", as in Howell's catalogue (catalogue number not checked);
    checked here against a 400 x 1600 polar sum: equal to 5 digits at 3 mm off axis, 20-60 mm from the centre [M]]. At a = 0 it is r^2 / (r^2 + h^2)."""
    a2, h2, r2 = a * a, h * h, r * r
    return 0.5 * (1 - (a2 + h2 - r2) / np.sqrt((a2 + h2 + r2) ** 2 - 4 * a2 * r2))


def irradiance(x, y, lamps):
    """Spectral irradiance (n, nlam) on the back of the paper from Lambertian discs parallel to it, below it:
    E = pi * radiance * F (closed-form view factor). Round 1 integrated the disc numerically on 6 rings x 16 angles;
    with a lamp 4-5 mm deep and 28 mm wide that undersampled it (samples 10 mm apart round the rim): +-10-20 % ripple
    along the rim and up to -30 % at the edge [M, against a 40 x 160 sum]. Round 2 uses the exact formula.
    Each lamp: centre (x, y) mm, depth mm below the paper, radius mm, radiance scale, spectrum; or kind 'ambient'."""
    E = np.zeros((x.size, LAM.size))
    for L in lamps:
        if L.get("kind") == "ambient":
            # A diffuse back-light much larger than the field (it fills the hemisphere behind the sheet for every point
            # we see): uniform irradiance E = pi * radiance. Round 2: the original's dark navy floor far above the bleed.
            E += np.pi * L["scale"] * spectrum(L["spectrum"])[None, :]
            continue
        a = np.hypot(x - L["x_mm"], y - L["y_mm"])
        n = float(L.get("cos_power", 0.0))
        if n == 0.0:
            acc = np.pi * disc_view_factor(a, L["depth_mm"], L["radius_mm"])
        else:
            acc = disc_irradiance_cosn(a, L["depth_mm"], L["radius_mm"], n)
        E += L["scale"] * acc[:, None] * spectrum(L["spectrum"])[None, :]
    return E


def disc_irradiance_cosn(a, h, r, n, nr=96, nphi=96):
    """Irradiance per unit on-axis radiance from a disc (radius r, depth h, parallel to the paper) whose radiance falls
    off as cos^n of the emission angle (n = 0: Lambertian; n > 0: a directional back-light, e.g. a lamp behind a lens,
    a grid or a louvred diffuser): E(a) = integral over the disc of (h/d)^(n+2) / d^2 dA, d the distance from the paper
    point (offset a from the axis) to the disc element. A Lambertian disc's tail falls as a^-4; the cos^n one as
    a^-(n+4). Gauss-Legendre in (rho, phi) on a table of a (0 .. 2000 mm), interpolated in log E. Checked against the
    closed form at n = 0 (see tests in the round-2b notes)."""
    key = (round(h, 9), round(r, 9), round(n, 9))
    tab = _COSN.get(key)
    if tab is None:
        aa = np.concatenate([np.linspace(0, 3 * r + 3 * h, 300)[:-1], np.geomspace(3 * r + 3 * h, 2000.0, 200)])
        xr, wr = np.polynomial.legendre.leggauss(nr)
        xp, wp = np.polynomial.legendre.leggauss(nphi)
        rho = 0.5 * r * (xr + 1)
        phi = 0.5 * np.pi * (xp + 1)
        w = (0.5 * r * wr)[:, None] * (0.5 * np.pi * wp)[None, :] * rho[:, None] * 2   # x2: phi in 0..pi, symmetric
        Ev = np.empty(aa.size)
        for k, av in enumerate(aa):
            # finer rho near the receiver when it sits over the disc and the lamp is shallow: split the radial range
            d2 = h * h + av * av + rho[:, None] ** 2 - 2 * av * rho[:, None] * np.cos(phi)[None, :]
            Ev[k] = np.sum(w * h ** (n + 2) / d2 ** ((n + 4) / 2))
        tab = (aa, np.log(np.maximum(Ev, 1e-300)))
        _COSN[key] = tab
    return np.exp(np.interp(a, tab[0], tab[1]))


_COSN = {}


# ---------------------------------------------------------------- camera
class Camera:
    """Pinhole + thin lens. Paper plane z = 0; the camera above it, looking along +y and down.
    pose: el (deg, elevation of the line to the aim point), dist (mm), aim (x, y) on paper, pitch/yaw offsets (deg),
    f_px (focal length in pixels at the given width), aperture_mm (entrance pupil diameter), focus_mm."""

    def __init__(self, C, W, H):
        self.W, self.H = W, H
        el = np.radians(C["el_deg"])
        ax, ay = C["aim"]
        self.pos = np.array([ax, ay - C["dist_mm"] * np.cos(el), C["dist_mm"] * np.sin(el)])
        fwd = np.array([ax, ay, 0.0]) - self.pos
        fwd /= np.linalg.norm(fwd)
        p = np.radians(C.get("pitch_deg", 0.0))
        right = np.array([1.0, 0, 0])
        up = np.cross(right, fwd)
        fwd2 = np.cos(p) * fwd + np.sin(p) * up                       # positive pitch looks up
        up2 = np.cross(right, fwd2)
        self.R = np.stack([right, -up2, fwd2])                        # rows: image x, image y (down), forward
        self.f = C["f_px"] * W / 1920.0
        self.cx, self.cy = W / 2 + C.get("shift_px", [0, 0])[0] * W / 1920, H / 2 + C.get("shift_px", [0, 0])[1] * W / 1920
        self.A = C["aperture_mm"]
        self.focus = C["focus_mm"]

    def rays(self, ss=1):
        u = (np.arange(self.W * ss) + 0.5) / ss
        v = (np.arange(self.H * ss) + 0.5) / ss
        U, V = np.meshgrid(u, v)
        d = np.stack([(U - self.cx) / self.f, (V - self.cy) / self.f, np.ones_like(U)], -1)
        dw = d @ self.R                                               # camera -> world
        t = -self.pos[2] / np.minimum(dw[..., 2], -1e-9)
        hit = dw[..., 2] < -1e-9
        P = self.pos[None, None, :] + t[..., None] * dw
        depth = t                                                     # along the ray with d_z(cam) = 1 -> axial depth
        return P[..., 0], P[..., 1], depth, hit

    def project(self, X, Y):
        Pc = (np.stack([X, Y, np.zeros_like(X)], -1) - self.pos) @ self.R.T
        return self.cx + self.f * Pc[..., 0] / Pc[..., 2], self.cy + self.f * Pc[..., 1] / Pc[..., 2], Pc[..., 2]

    def coc_px(self, depth):
        """Blur diameter in pixels: A f |z - s| / (z s)."""
        return self.A * self.f * np.abs(depth - self.focus) / (depth * self.focus)


def disc_blur(img, diam):
    if diam < 0.75:
        return img
    r = diam / 2
    n = int(np.ceil(r)) + 1
    yy, xx = np.mgrid[-n:n + 1, -n:n + 1]
    # anti-aliased disc
    k = np.clip(r + 0.5 - np.hypot(xx, yy), 0, 1)
    k /= k.sum()
    H, W = img.shape[:2]
    pad = n + 2
    out = np.empty_like(img)
    for c in range(img.shape[2]):
        a = np.pad(img[..., c], pad, mode="edge")
        K = np.zeros_like(a)
        K[:2 * n + 1, :2 * n + 1] = k
        K = np.roll(K, (-n, -n), axis=(0, 1))
        out[..., c] = irfft2(rfft2(a) * rfft2(K), s=a.shape)[pad:pad + H, pad:pad + W]
    return out


def defocus(img, coc, levels=12):
    cmax = max(float(coc.max()), 1e-3)
    lv = np.linspace(0, cmax, levels)
    stack = [disc_blur(img, d) for d in lv]
    f = np.clip(coc / cmax * (levels - 1), 0, levels - 1 - 1e-6)
    i0 = np.floor(f).astype(int)
    w = (f - i0)[..., None]
    out = np.zeros_like(img)
    for i in range(levels - 1):
        m = (i0 == i)[..., None]
        out += m * ((1 - w) * stack[i] + w * stack[i + 1])
    return out


def veil(img, halo, halo_sigma_frac, uniform):
    """Round 2b lens veiling glare, two parts [A: the form; F: the numbers]: a halo (fraction 'halo' of the light
    spread by a Gaussian of sigma halo_sigma_frac frame widths: scatter near the bright band) and a uniform veil
    (fraction 'uniform' of the frame's mean, spread evenly: the lens's veiling glare index; neutral when the frame's mean
    is). It replaces r1's single wide Gaussian (0.149 at 0.2 W), which carried the band's orange into the ink core
    (r1 item 4: warm-brown ground) and up the dark sky of shot 38 (+3-11 codes, r2). Light from outside the field is
    not modelled."""
    W = img.shape[1]
    out = (1 - halo - uniform) * img
    if halo > 0:
        out = out + halo * np.stack([ndimage.gaussian_filter(img[..., c], halo_sigma_frac * W, mode="nearest")
                                     for c in range(3)], -1)
    if uniform > 0:
        out = out + uniform * img.mean(axis=(0, 1))[None, None, :]
    return out


def glare(img, frac, sigma_frac=0.2):
    """Lens veiling glare: a fraction of the light spread by a wide Gaussian [F]. r1: sigma 0.2 frame widths [A], fraction
    fitted on frame 0 alone. Round 2 fits both on frames 0, 420, 470: frame 420 shows the original has almost no wide veil
    (its floor rises 18.4 -> 21.9 codes at 0.3 frame heights above the bright bottom; r1's veil alone added 3-11)."""
    if frac <= 0:
        return img
    W = img.shape[1]
    b = np.stack([ndimage.gaussian_filter(img[..., c], sigma_frac * W, mode="nearest") for c in range(3)], -1)
    return (1 - frac) * img + frac * b


def to_display(lin_rgb):
    return np.clip(cam.srgb_encode(np.clip(lin_rgb, 0, 1)), 0, 1)


def render(sheet, O, C, W, H, ss=1, return_parts=False):
    """Linear BT.709 image (H, W, 3), already exposed (O['exposure'])."""
    camr = Camera(C, W, H)
    X, Y, depth, hit = camr.rays(ss)
    x, y = X.ravel(), Y.ravel()
    # pixel footprint on the paper (mm): the longer side of the projected pixel (for the texture pre-filter)
    dYv, dXv = np.gradient(Y, axis=0), np.gradient(X, axis=0)
    dYu, dXu = np.gradient(Y, axis=1), np.gradient(X, axis=1)
    foot = np.maximum(np.hypot(dXv, dYv), np.hypot(dXu, dYu)).ravel()
    R, T, w = sheet.optics(x, y, O, foot=foot)
    Eb = irradiance(x, y, O["lamps"])
    Ef = O["front"]["scale"] * spectrum(O["front"]["spectrum"])[None, :]
    L = (T * Eb + R * Ef) / np.pi
    if O.get("sheen"):
        # Round 2b: the pool's surface is a smooth liquid / binder film, so it mirrors the dim surroundings in front of
        # the sheet (Fresnel at the camera's grazing angle, ~72 deg incidence at frame 0's centre); the matte paper
        # does not. Neutral. This is what lights the opaque ink core (the original: (22,22,22), falling to 18-20 toward
        # the bottom of frame 0, i.e. toward less grazing angles), which r1/r2 got from a wide lens veil.
        Sh = O["sheen"]
        dist = np.sqrt((x - camr.pos[0]) ** 2 + (y - camr.pos[1]) ** 2 + camr.pos[2] ** 2)
        mu = camr.pos[2] / dist                                                  # cos of the incidence angle
        # glossy where the ink film is continuous: carbon (both classes) / film_gsm, clipped [A]. The sim's pool mask
        # (a circle) ends 2-4 mm inside the carbon edge and drew a visible second arc in the core (first try of 2b).
        tot = sum(sheet.sample(c, x, y) for c in sheet.carbon.values())
        pool = np.clip(tot / Sh["film_gsm"], 0, 1)
        L = L + (fresnel(mu, Sh["n"]) * pool)[:, None] * Sh["scale"] * spectrum(Sh["spectrum"])[None, :]
    xyz = L @ CMF.T / (CMF[1] @ np.ones_like(LAM))
    rgb = np.einsum("...j,ij->...i", xyz, M709) * O["exposure"]
    rgb = rgb.reshape(H * ss, W * ss, 3)
    rgb[~hit] = 0
    dep = depth.reshape(H * ss, W * ss)
    if ss > 1:
        rgb = rgb.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
        dep = dep.reshape(H, ss, W, ss).mean(axis=(1, 3))
    coc = camr.coc_px(dep)
    if "veil" in O:
        V = O["veil"]
        img = veil(defocus(rgb, coc), V["halo"], V["halo_sigma_frac"], V["uniform"])
    else:   # r1 / r2
        img = glare(defocus(rgb, coc), O.get("glare", 0.0), O.get("glare_sigma_frac", 0.2))
    if return_parts:
        return img, dict(coc=coc, depth=dep, cam=camr)
    return img
