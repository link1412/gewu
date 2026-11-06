"""Translate one of our pbrt-v4 scenes into a camera-RGB scene for Blender Cycles (tools/cycles_scene.py).

    python3 -I tools/rgbscene.py DIR/scene.pbrt [--key-K 5500] [-o DIR/scene.cycles.json]

Cycles renders three channels. We make them the camera's own raw channels, so tools/camera.py develops
a Cycles render exactly as it develops pbrt's "rawsensor" film:
- an emission spectrum L is projected onto the sensor curves, E_c = sum s_c L (1 nm, as pbrt's
  rawsensor film sums them): exact for light seen directly;
- a reflectance or a medium coefficient is averaged over each channel, weighted by the sensor curve times
  the key light: exact for one bounce of the key light, the usual RGB-rendering error after that.
pbrt's semantics are kept: a PiecewiseLinear spectrum is zero outside its samples; an area light's
"scale" is divided by the luminance of its spectrum (lights.cpp, "radiance equivalent to 1 nit");
"rgb" values become spectra by pbrt's sigmoid model, solved here instead of read from its table.

Handles the subset our shot generators write and stops on anything else: LookAt, Camera "perspective",
Sampler, Integrator, Film "rgb", AttributeBegin/End, Translate, Rotate, Scale, ActiveTransform,
AreaLightSource "diffuse" (blackbody L, rgb L, or spectrum L: one of pbrt's named illuminants or sampled values;
scale), Material diffuse / diffusetransmission / dielectric / thindielectric / conductor (eta, k or reflectance spectra, projected to
per-channel eta, k whose Fresnel curves are the channel-averaged spectral ones: conductor_channels, docs/metals.md),
MakeNamedMedium homogeneous, MediumInterface (a medium inside a dielectric must be a watertight plymesh: Cycles
renders a medium only inside a closed mesh, docs/slab.md; tools/shell.py), Shape bilinearmesh / disk / plymesh
(a plymesh's "u","v" or "s","t" vertex properties are its UVs; a bilinearmesh's "point2 uv", else pbrt's corner
default);
Texture (docs/textures.md), all with pbrt-v4's syntax and semantics:
- Texture "n" "float" "imagemap" "string filename" f ["float scale"] ["bool invert"] ["string wrap" repeat|clamp]
  ["float uscale"|"vscale"|"udelta"|"vdelta"] ["string encoding"] (default UV mapping; EXR/PFM float, 16-bit PNG);
- "texture displacement" "n" (bump map, scene units) on diffuse / dielectric / thindielectric;
- "texture roughness" "n" on dielectric (with "bool remaproughness" false, as the uniform roughness);
and things of ours: the material "nacreinlay" (shot 19's mother-of-pearl in lacquer, nacre_inlay below; Cycles
only), the material "barbule" (shot 17's peacock barbules, barbule below; Cycles only), and two that the patched pbrt also reads (patches/pbrt-v4-gewu.patch, docs/coats.md): the spectrum texture
  Texture "n" "spectrum" "familymap" "string family" f.npz "string map" c.exr   (family_table below)
used as Material "diffuse" "texture reflectance" "n": a reflectance that runs through a one-parameter family
of spectra R(c), c read from a float map; and an absorbing film,
  Material "thindielectric" "float eta" 1 "spectrum transmittance" [...] | "texture transmittance" "n"
its internal transmittance T0 for one crossing at normal incidence, T0^(1/cos) at an angle (film_transmittance
below; a familymap texture there is a family of T0, as cobalt under a glaze).
Scenes are composed with pbrt's Include (relative names against the main file's directory, as pbrt), and an area
light is put in a light group by pbrt's own Attribute directive, which pbrt renders and ignores:
  Attribute "light" "string group" "key"      (before the AreaLightSource; scoped by AttributeBegin/End)
tools/cycles_scene.py then renders one pass per group (docs/optics.md); if any light has a group, all must.
Lengths are written in metres (Blender's unit); the scene's unit is the millimetre. Mesh files are named
relative to the scene file, so the JSON travels with its directory (to a render machine, say).
"""

import argparse
import json
import math
import os
import re
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from camera import LAM, Spectra, blackbody, pbrt_array, piecewise, rgb709_from_xyz  # noqa: E402
import shell  # noqa: E402

MM = 1e-3   # metres per scene unit


# --- parsing ---------------------------------------------------------------------------------
TOKEN = re.compile(r'"[^"]*"|\[|\]|[^\s\[\]"]+')


def tokens(text):
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        yield from TOKEN.findall(line)


def statements(text):
    """(directive, [args]) with args as numbers, strings (unquoted) or lists."""
    def value(u):
        if u.startswith('"'):
            return u[1:-1]
        if u in ("true", "false"):
            return u == "true"
        return float(u)

    out, cur = [], None
    it = iter(tokens(text))
    for t in it:
        if t == "[":
            lst = []
            for u in it:
                if u == "]":
                    break
                lst.append(value(u))
            cur[1].append(lst)
        elif t.startswith('"') or t in ("true", "false") or re.fullmatch(r"[-+0-9.eE]+", t):
            cur[1].append(value(t))
        elif cur and cur[0] == "ActiveTransform" and not cur[1]:
            cur[1].append(t)                       # its argument is a bare word: StartTime, EndTime, All
        else:
            cur = (t, [])
            out.append(cur)
    return out


def params(args):
    """pbrt's '"type name" [values]' pairs after the leading positional string(s)."""
    p = {}
    for i in range(0, len(args) - 1, 2):
        typ, name = args[i].split()
        v = args[i + 1]
        p[name] = (typ, v if isinstance(v, list) else [v])
    return p


def one(p, name, default=None):
    return p[name][1][0] if name in p else default


# --- transforms (pbrt's, row-major 4x4 acting on column vectors) -----------------------------
def translate(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def rotate(deg, x, y, z):
    a = np.array([x, y, z], float)
    a /= np.linalg.norm(a)
    s, c = math.sin(math.radians(deg)), math.cos(math.radians(deg))
    m = np.eye(4)
    for i in range(3):
        for j in range(3):
            m[i, j] = a[i] * a[j] * (1 - c) + (c if i == j else 0)
    m[0, 1] -= a[2] * s
    m[0, 2] += a[1] * s
    m[1, 0] += a[2] * s
    m[1, 2] -= a[0] * s
    m[2, 0] -= a[1] * s
    m[2, 1] += a[0] * s
    return m


def scale(x, y, z):
    return np.diag([x, y, z, 1.0])


# --- spectra -> camera RGB -------------------------------------------------------------------
class Sensor:
    def __init__(self, name, key_K):
        self.S = Spectra(name)
        self.w = self.S.sens * blackbody(key_K)          # weights for reflectances and coefficients
        self.yint = self.S.cmf[1].sum()                  # pbrt's CIE_Y_integral, on the 1 nm grid
        d65 = self.S.d65
        self.d65n = d65 * self.yint / (self.S.cmf[1] @ d65)   # "stdillum-D65": normalised, Y = CIE_Y_integral
        self.white = self.S.cmf @ self.d65n / (self.S.cmf[1] @ self.d65n)
        self.rgb_from_xyz = rgb709_from_xyz(self.white)

    def emission(self, L):
        return self.S.sens @ L

    def average(self, x):
        return (self.w @ x) / self.w.sum(1)

    def sigmoid_spectrum(self, rgb):
        """pbrt's RGBSigmoidPolynomial for an sRGB albedo, solved by least squares on its rgb."""
        rgb = np.asarray(rgb, float)
        if np.any(rgb < 0) or np.any(rgb > 1):
            raise SystemExit(f"rgb {rgb}: outside [0, 1]; only albedos are handled")
        x = (LAM - 360.0) / (830.0 - 360.0)

        def spec(c):
            v = c[0] * x * x + c[1] * x + c[2]
            return 0.5 + v / (2 * np.sqrt(1 + v * v))

        def rgb_of(s):
            xyz = self.S.cmf @ (s * self.d65n) / (self.S.cmf[1] @ self.d65n)
            return self.rgb_from_xyz @ xyz

        r = least_squares(lambda c: rgb_of(spec(c)) - rgb, np.zeros(3), xtol=1e-12, ftol=1e-12)
        if np.abs(r.fun).max() > 2e-3:
            raise SystemExit(f"rgb {rgb}: the sigmoid spectrum misses it by {np.abs(r.fun).max():.4f}")
        return spec(r.x)

    def illuminant(self, typ, v):
        """An area light's L as pbrt builds it, before the photometric normalisation."""
        if typ == "blackbody":
            T = v[0]
            b = blackbody(T)
            return b / blackbody_peak(T), b / blackbody_peak(T)     # (spectrum, spectrum for the photometric scale)
        if typ == "rgb":
            m = max(v)
            s = 2 * m * self.sigmoid_spectrum(np.asarray(v) / (2 * m)) * self.d65n
            return s, self.d65n                                    # SpectrumToPhotometric uses the illuminant only
        if typ == "spectrum":
            s = named_spectrum(v[0]) if len(v) == 1 and isinstance(v[0], str) else piecewise(np.asarray(v, float))
            if not s.max() > 0:
                raise SystemExit("light spectrum: zero over 360-830 nm")
            return s, s                                            # pbrt: scale /= SpectrumToPhotometric(L), any L
        raise SystemExit(f"light spectrum type {typ} not handled")

    def reflectance(self, typ, v):
        if typ == "rgb":
            return self.sigmoid_spectrum(v)
        if typ == "spectrum":
            return piecewise(np.asarray(v, float))
        if typ == "float":
            return np.full(LAM.shape, v[0])
        raise SystemExit(f"reflectance type {typ} not handled")


def nacre_inlay(p, base, sen):
    """Our material for shot 19, not pbrt's (S2 shots/19-dianluo, removed in S10; now shots/19-luodian): black lacquer with shell pieces
    inlaid, after the maps file. The shell's tables (shots/19-luodian/nacre.py) are spectra, averaged
    over the channels like reflectances (exact for one bounce of the key light); the polished surface's
    are flat in wavelength (no dispersion), the stack's are not."""
    need = ("tables", "maps", "lacquereta", "lacquerdiffuse", "lacquerroughness", "shellroughness", "layersroughness")
    missing = [k for k in need if k not in p]
    if missing:
        raise SystemExit(f"nacreinlay: no {missing}")
    T = np.load(os.path.join(base, one(p, "tables")))
    if not np.array_equal(T["lam"], LAM):
        raise SystemExit("nacreinlay: the tables are not on pbrt's 1 nm grid")

    def avg(R):
        return (np.einsum("...l,cl->...c", R.astype(float), sen.w) / sen.w.sum(1)).round(6).tolist()

    return {"type": "nacreinlay", "maps": one(p, "maps"), "n_o": float(T["n_o"]),
            "d_nm": [float(T["d_nm"][0]), float(T["d_nm"][-1])], "b_max": float(T["b"][-1]),
            "stack_s": avg(T["R_stack_s"]), "stack_p": avg(T["R_stack_p"]),
            "top_s": avg(T["R_top_s"]), "top_p": avg(T["R_top_p"]),
            "lacquer_eta": one(p, "lacquereta"), "lacquer_diffuse": one(p, "lacquerdiffuse"),
            "lacquer_alpha": one(p, "lacquerroughness"), "shell_alpha": one(p, "shellroughness"),
            "layers_alpha": one(p, "layersroughness")}


def barbule(p, base, sen):
    """Our material for shot 17 (shots/17-peacock/barbule.py), not pbrt's: a peacock barbule's melanin-rod photonic
    crystal as a 1-D stack, a glossy lobe about the shading normal coloured by the table R(s, mu, lam) (unpolarised)
    at the barbule's structure coordinate s (the UV map's u) and mu = cos(view, normal), over a dark diffuse body (the
    melanin-filled barbule; sRGB albedo). The table is averaged over the channels like a reflectance (exact for one
    bounce of the key light). Cycles only."""
    need = ("table", "roughness", "body")
    missing = [k for k in need if k not in p]
    if missing:
        raise SystemExit(f"barbule: no {missing}")
    def table(name):
        T = np.load(os.path.join(base, name))
        if not np.array_equal(T["lam"], LAM):
            raise SystemExit("barbule: the table is not on pbrt's 1 nm grid")
        mu = np.asarray(T["mu"], float)
        if not np.allclose(mu, np.linspace(0, 1, len(mu))):
            raise SystemExit("barbule: the table's mu must run uniformly over [0, 1]")
        return (np.einsum("...l,cl->...c", np.asarray(T["R"], float), sen.w) / sen.w.sum(1)).round(6)
    R = table(one(p, "table"))
    typ, v = p["body"]
    out = {"type": "barbule", "table": R.tolist(), "alpha": one(p, "roughness"),
           "body": list(sen.average(sen.reflectance(typ.split()[0], v)))}
    # optional (shot 17 r2): an anisotropic lobe, its tangent the UV map's u direction (the slope spread is wider
    # along it: across the barbule's axis); the structure coordinate from a float vertex property of the plymesh
    # (`sattr`) instead of the UV map's u: the tangent comes from both UV gradients, so the UVs must be a proper frame
    if "anisotropy" in p:
        out["anisotropy"] = one(p, "anisotropy")
    if "sattr" in p:
        out["s_attribute"] = one(p, "sattr")
    # optional (shot 17 r3): a second table blended in by a float vertex property (`mixattr`, 0 = table, 1 = table2),
    # its structure coordinate from `sattr2`: one surface grading from one region's stack into the next
    if "table2" in p:
        miss = [k for k in ("mixattr", "sattr2") if k not in p]
        if miss:
            raise SystemExit(f"barbule: table2 needs {miss}")
        out["table2"] = table(one(p, "table2")).tolist()
        out["mix_attribute"] = one(p, "mixattr")
        out["s2_attribute"] = one(p, "sattr2")
    return out


def image_texture(p, base, where):
    """A float imagemap's parameters as the JSON the Cycles side reads (pbrt's FloatImageTexture, UV mapping)."""
    fn = one(p, "filename")
    if not fn:
        raise SystemExit(f"{where}: no filename")
    full = os.path.join(base, fn)
    if not os.path.isfile(full):
        raise SystemExit(f"{where}: {full} does not exist")
    ext = os.path.splitext(fn)[1].lower()
    if ext not in (".exr", ".pfm", ".png"):
        raise SystemExit(f"{where}: {ext} images not handled (EXR, PFM, 16-bit PNG)")
    wrap = one(p, "wrap", "repeat")
    if wrap not in ("repeat", "clamp"):
        raise SystemExit(f"{where}: wrap {wrap!r} not handled (repeat, clamp)")
    enc = one(p, "encoding", "sRGB" if ext == ".png" else "linear")     # pbrt's defaults
    if enc not in ("linear", "sRGB"):
        raise SystemExit(f"{where}: encoding {enc!r} not handled")
    if one(p, "filter", "bilinear") != "bilinear" or one(p, "mapping", "uv") != "uv":
        raise SystemExit(f"{where}: only the bilinear filter and the uv mapping are handled")
    return {"file": fn, "scale": float(one(p, "scale", 1.0)), "invert": bool(one(p, "invert", False)),
            "wrap": wrap, "encoding": enc, "su": float(one(p, "uscale", 1.0)), "sv": float(one(p, "vscale", 1.0)),
            "du": float(one(p, "udelta", 0.0)), "dv": float(one(p, "vdelta", 0.0))}


def family_table(p, base, sen, where):
    """Our "familymap" spectrum texture: f.npz holds lambda_nm (K,), c (N,) ascending, R (N, K). Each member is
    projected as a reflectance is (channel average, sensor x key light) into an (N, 3) table."""
    for k in ("family", "map"):
        if k not in p:
            raise SystemExit(f"{where}: familymap needs \"string {k}\"")
    for k in ("scale", "invert"):
        if k in p:
            raise SystemExit(f"{where}: familymap reads c as the map's value; \"{k}\" not handled")
    F = np.load(os.path.join(base, one(p, "family")))
    lam, c, R = (np.asarray(F[k], float) for k in ("lambda_nm", "c", "R"))
    if R.shape != (len(c), len(lam)) or len(c) < 2 or np.any(np.diff(c) <= 0):
        raise SystemExit(f"{where}: need c ascending (N>=2) and R of shape (N, K), got c {c.shape}, R {R.shape}")
    if np.diff(lam).min() <= 0 or R.min() < 0 or R.max() > 1:
        raise SystemExit(f"{where}: lambda_nm must ascend and R lie in [0, 1]")
    outside = sen.w[:, (LAM < lam[0]) | (LAM > lam[-1])].sum(1) / sen.w.sum(1)
    if outside.max() > 5e-3:
        raise SystemExit(f"{where}: the spectra span {lam[0]:.0f}-{lam[-1]:.0f} nm; the sensor x key weight "
                         f"outside is {outside.max():.1%} (pbrt would read zero there)")
    table = np.array([sen.average(piecewise(np.stack([lam, r], 1).ravel())) for r in R])
    cm = image_texture({"filename": ("string", [one(p, "map")]),
                        **{k: p[k] for k in ("wrap", "encoding", "uscale", "vscale", "udelta", "vdelta") if k in p}},
                       base, where)                      # c is the map's value as it is: no scale, no invert
    return {"c": c.tolist(), "table": table.round(7).tolist(), "map": cm, "family": one(p, "family")}


FILM_MU = np.linspace(0.0, 1.0, 33)       # the cosines a film's transmittance table is tabulated at (docs/coats.md)


def film_table(T0, sen):
    """A film's transmittance for one crossing at cos mu (the slab's own angle; eta 1: the ray's), T0^(1/mu), per
    channel, from its spectrum T0 at normal incidence: each entry is the square root of the channel average of two
    crossings, sqrt(avg(T0^(2/mu))). A film under a coat is mostly crossed twice (down to what is under it and back);
    averaging one crossing and squaring it would err by Jensen's inequality, badly for a banded absorber (cobalt:
    10-35% in the 1-D study of docs/coats.md). Exact for two crossings at the same angle under the key light.
    Returns (len(FILM_MU), 3)."""
    T0 = np.clip(T0, 0.0, 1.0)
    rows = []
    for mu in FILM_MU:
        two = np.zeros_like(T0) if mu <= 0 else np.where(T0 > 0, T0, 0.0) ** (2.0 / mu)
        rows.append(np.sqrt(sen.average(two)))
    return np.array(rows)


def film_transmittance(p, base, sen, named, where):
    """Ours: "transmittance" on a thindielectric, the slab's internal transmittance for one crossing at normal
    incidence (pbrt, as patched: ThinDielectricBxDF). Uniform (spectrum, float) or a familymap of spectra."""
    typ = p["transmittance"][0].split()[0]
    if typ == "texture":
        f = named(p, "transmittance", "family", where)
        F = np.load(os.path.join(base, f["family"]))
        lam, R = np.asarray(F["lambda_nm"], float), np.asarray(F["R"], float)
        T = np.array([film_table(piecewise(np.stack([lam, r], 1).ravel()), sen) for r in R])     # (N, M, 3)
        return {"transmittance_family": {"c": f["c"], "mu": FILM_MU.tolist(), "table": T.round(7).tolist(),
                                         "map": f["map"]}}
    if typ in ("spectrum", "float"):
        return {"transmittance": {"mu": FILM_MU.tolist(),
                                  "table": film_table(sen.reflectance(typ, p["transmittance"][1]), sen).round(7).tolist()}}
    raise SystemExit(f"{where}: transmittance {typ} not handled (texture familymap, spectrum, float)")


# pbrt's named illuminants (util/spectrum.cpp, namedSpectra) and the arrays they are made from; the photometric
# normalisation of an area light makes their own scale irrelevant
NAMED_ILLUMINANTS = {"stdillum-A": "CIE_Illum_A", "stdillum-D50": "CIE_Illum_D5000", "stdillum-D65": "CIE_Illum_D6500",
                     "illum-acesD60": "ACES_Illum_D60", **{f"stdillum-F{i}": f"CIE_Illum_F{i}" for i in range(1, 13)}}


def named_spectrum(name):
    if name not in NAMED_ILLUMINANTS:
        raise SystemExit(f"light spectrum {name!r}: not one of pbrt's named illuminants handled here "
                         f"({', '.join(NAMED_ILLUMINANTS)}); spectrum files are not handled")
    return piecewise(pbrt_array(NAMED_ILLUMINANTS[name]))


def read_statements(path, base, depth=0):
    """A scene file's statements with pbrt-v4's Include expanded in place. pbrt resolves every relative file name
    (Include, meshes, textures) against one search directory, the main scene file's (util/file.cpp), so `base` is
    that directory for nested includes too."""
    out = []
    for d, args in statements(open(path).read()):
        if d == "Include":
            if len(args) != 1 or not isinstance(args[0], str):
                raise SystemExit(f"{path}: Include takes one file name")
            full = args[0] if os.path.isabs(args[0]) else os.path.join(base, args[0])
            if not os.path.isfile(full):
                raise SystemExit(f"{path}: Include {args[0]!r}: {full} does not exist")
            if depth >= 16:
                raise SystemExit(f"{path}: Include nested more than 16 deep")
            out += read_statements(full, base, depth + 1)
        elif d == "Import":
            raise SystemExit(f"{path}: Import not handled (Include is)")
        else:
            out.append((d, args))
    return out


# --- conductors (docs/metals.md) ---------------------------------------------------------------
FRESNEL_FIT_DEG = np.arange(0.0, 89.75, 0.5)          # the angles the per-channel fit is made over (uniform in angle)
FRESNEL_REPORT_DEG = (0, 30, 45, 60, 70, 80, 85, 89)


def fresnel_conductor(cos_i, n, k):
    """pbrt's FrComplex (util/scattering.h): unpolarised Fresnel reflectance of a conductor eta = n + ik from air.
    Broadcasts over cos_i, n, k. Cycles' fresnel_conductor (closure/bsdf_util.h, physical conductor) is the same
    function written in real arithmetic."""
    eta = np.asarray(n, float) + 1j * np.asarray(k, float)
    c = np.clip(np.asarray(cos_i, float), 0.0, 1.0)
    ct = np.sqrt(1 - (1 - c * c) / eta ** 2)
    r_parl = (eta * c - ct) / (eta * c + ct)
    r_perp = (c - eta * ct) / (c + eta * ct)
    return (np.abs(r_parl) ** 2 + np.abs(r_perp) ** 2) / 2


def conductor_spectrum(p, key, base, where):
    """A conductor's "spectrum eta" / "spectrum k" on LAM, as pbrt reads it: a named spectrum (metal-X-eta/k, built by
    FromInterleaved, which holds the end values beyond its samples), a spectrum file (pairs, relative to the scene's
    directory) or sampled values (both PiecewiseLinear, zero outside the samples)."""
    typ, v = p[key]
    if typ.split()[0] != "spectrum":
        raise SystemExit(f"{where}: \"{typ}\" not handled for {key} (\"spectrum\": named, a file or sampled values)")
    if len(v) == 1 and isinstance(v[0], str):
        m = re.fullmatch(r"metal-(\w+)-(eta|k)", v[0])
        if m:
            a = pbrt_array(f"{m.group(1)}_{m.group(2)}")
            return np.interp(LAM, a[0::2], a[1::2]), v[0]                # held at the ends (FromInterleaved)
        fn = v[0] if os.path.isabs(v[0]) else os.path.join(base, v[0])
        if not os.path.isfile(fn):
            raise SystemExit(f"{where}: {key} {v[0]!r} is neither one of pbrt's metal-*-eta/k spectra nor a file")
        vals = np.array([float(x) for x in re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?",
                                                     re.sub(r"#[^\n]*", "", open(fn).read()))])
        if len(vals) < 4 or len(vals) % 2:
            raise SystemExit(f"{where}: {fn}: need (lambda, value) pairs")
        lam, src = vals[0::2], v[0]
    else:
        vals = np.asarray(v, float)
        lam, src = vals[0::2], "sampled"
    if np.any(np.diff(lam) <= 0):
        raise SystemExit(f"{where}: {key}: wavelengths must increase")
    return piecewise(vals), src


def conductor_channels(eta, k, sen, where):
    """Per-channel (n_c, k_c) for an RGB conductor (Cycles' Metallic BSDF, physical conductor) whose Fresnel curve is
    the channel average of the spectral one: F_c(theta) = sum_l w_c(l) F(theta; n(l), k(l)) / sum_l w_c(l), with w the
    sensor x key-light weights that average a reflectance (so one bounce of the key light is right at every angle,
    to the fit's error). Least squares over FRESNEL_FIT_DEG; the error at FRESNEL_REPORT_DEG goes into the JSON."""
    outside = sen.w[:, ~((eta > 0) | (k > 0))].sum(1) / sen.w.sum(1)
    if outside.max() > 5e-3:
        raise SystemExit(f"{where}: eta and k are zero over {outside.max():.1%} of the sensor x key weight "
                         "(pbrt reads a sampled spectrum as zero outside its samples)")
    c = np.cos(np.radians(FRESNEL_FIT_DEG))
    target = fresnel_conductor(c[:, None], eta[None], k[None]) @ sen.w.T / sen.w.sum(1)       # (angles, 3)
    nk, err = [], []
    for ch in range(3):
        x0 = [max(sen.average(eta)[ch], 0.05), max(sen.average(k)[ch], 0.05)]
        r = least_squares(lambda q: fresnel_conductor(c, q[0], q[1]) - target[:, ch], x0,
                          bounds=([1e-4, 0.0], [50.0, 50.0]), xtol=1e-12, ftol=1e-12)
        nk.append(r.x)
        err.append(r.fun)
    nk, err = np.array(nk), np.array(err).T
    at = [int(np.argmin(np.abs(FRESNEL_FIT_DEG - d))) for d in FRESNEL_REPORT_DEG]
    return {"eta": nk[:, 0].round(6).tolist(), "k": nk[:, 1].round(6).tolist(),
            "fresnel_fit": {"deg": list(FRESNEL_REPORT_DEG), "spectral": target[at].round(5).tolist(),
                            "error": err[at].round(5).tolist(), "max_abs_error": np.abs(err).max(0).round(5).tolist()}}


def conductor(p, base, sen, named):
    """pbrt's "conductor": eta and k spectra (default metal-Cu), or a "reflectance" spectrum, which pbrt turns into
    eta = 1, k = 2 sqrt(r) / sqrt(1 - r) per wavelength (r clamped to [0, 0.9999]; materials.h). Roughness as the
    dielectric's: "bool remaproughness" false, alpha = the value or a float texture."""
    where = "Material conductor"
    if one(p, "remaproughness", True) is not False:
        raise SystemExit(f"{where}: remapped roughness not handled (\"bool remaproughness\" false)")
    for key in ("eta", "k", "reflectance"):
        if key in p and p[key][0].split()[0] == "texture":
            raise SystemExit(f"{where}: a textured {key} not handled")
    if "reflectance" in p:
        if "eta" in p or "k" in p:
            raise SystemExit(f"{where}: both reflectance and eta/k (pbrt refuses it too)")
        typ, v = p["reflectance"]
        r = np.clip(sen.reflectance(typ.split()[0], v), 0.0, 0.9999)
        eta, k, src = np.ones(LAM.shape), 2 * np.sqrt(r) / np.sqrt(1 - r), {"reflectance": typ.split()[0]}
    else:
        dflt = {"eta": ("spectrum", ["metal-Cu-eta"]), "k": ("spectrum", ["metal-Cu-k"])}     # pbrt's default
        eta, se = conductor_spectrum({**dflt, **p}, "eta", base, where)
        k, sk = conductor_spectrum({**dflt, **p}, "k", base, where)
        src = {"eta": se, "k": sk}
    m = {"type": "conductor", "source": src, **conductor_channels(eta, k, sen, where)}
    if "roughness" in p and p["roughness"][0].split()[0] == "texture":
        m["alpha_texture"] = named(p, "roughness", "float", where)
    else:
        m["alpha"] = one(p, "roughness", 0.0)
    f = m["fresnel_fit"]
    print(f"conductor {src}: per channel eta {m['eta']} k {m['k']}; Fresnel fit max |error| {f['max_abs_error']}")
    return m


def blackbody_peak(T):
    lam = 2.8977721e-3 / T * 1e9
    c, h, kb = 299792458.0, 6.62606957e-34, 1.3806488e-23
    l = lam * 1e-9
    return 2 * h * c * c / (l ** 5 * (math.exp(h * c / (l * kb * T)) - 1))


def material(kind, p, base, sen, named):
    """One Material directive as the JSON material. The dispatch: add a material (a pbrt one or ours) as one more
    branch here, its Cycles side in tools/cycles_scene.py's material()."""
    m = None
    for k in ("uroughness", "vroughness", "normalmap"):
        if k in p:
            raise SystemExit(f"Material {kind}: {k} not handled")
    if kind == "diffuse":
        if "reflectance" in p and p["reflectance"][0].split()[0] == "texture":
            m = {"type": "diffuse", "reflectance_family": named(p, "reflectance", "family", "Material diffuse")}
        else:
            typ, v = p.get("reflectance", ("float", [0.5]))
            m = {"type": "diffuse", "reflectance": list(sen.average(sen.reflectance(typ.split()[0], v)))}
    elif kind == "dielectric":
        if one(p, "remaproughness", True) is not False:
            raise SystemExit("dielectric with remapped roughness not handled")
        m = {"type": "dielectric", "eta": one(p, "eta", 1.5)}
        if "roughness" in p and p["roughness"][0].split()[0] == "texture":
            m["alpha_texture"] = named(p, "roughness", "float", "Material dielectric")
        else:
            m["alpha"] = one(p, "roughness", 0.0)
    elif kind == "thindielectric":
        m = {"type": "thindielectric", "eta": one(p, "eta", 1.5)}
        if "transmittance" in p:          # ours: an absorbing film (docs/coats.md); Cycles handles it with eta 1
            if m["eta"] != 1:
                raise SystemExit("thindielectric with transmittance: only eta 1 (a film) is handled")
            m.update(film_transmittance(p, base, sen, named, "Material thindielectric"))
    elif kind == "diffusetransmission":
        # pbrt's DiffuseTransmissionMaterial: Lambertian reflection R and transmission T (a leaf, paper), both
        # spectrum textures (pbrt's default 0.25 when absent); a familymap on either (materials/yinxing/)
        if one(p, "scale", 1.0) != 1.0:
            raise SystemExit("Material diffusetransmission: \"scale\" not handled")
        m = {"type": "diffusetransmission"}
        for key in ("reflectance", "transmittance"):
            if key in p and p[key][0].split()[0] == "texture":
                m[key + "_family"] = named(p, key, "family", "Material diffusetransmission")
            else:
                typ, v = p.get(key, ("float", [0.25]))
                m[key] = list(sen.average(sen.reflectance(typ.split()[0], v)))
    elif kind == "conductor":
        m = conductor(p, base, sen, named)
    elif kind == "nacreinlay":
        return nacre_inlay(p, base, sen)
    elif kind == "barbule":
        return barbule(p, base, sen)
    else:
        raise SystemExit(f"material {kind} not handled")
    if "displacement" in p:
        if p["displacement"][0].split()[0] != "texture":
            raise SystemExit(f"Material {kind}: displacement must be a named float texture")
        if kind not in ("diffuse", "dielectric", "thindielectric", "conductor", "diffusetransmission"):
            raise SystemExit(f"Material {kind}: displacement not handled")
        m["displacement"] = named(p, "displacement", "float", f"Material {kind}")
        m["displacement_m_per_unit"] = MM            # pbrt: the height is in scene units
    return m


# --- the scene -------------------------------------------------------------------------------
def convert(path, sensor_name, key_K):
    base = os.path.dirname(os.path.abspath(path))
    sen = Sensor(sensor_name, key_K)
    out = {"source": os.path.abspath(path), "sensor": sensor_name, "key_light": {"blackbody_K": key_K},
           "units": "metre", "media": {}, "objects": []}
    ctm = [np.eye(4), np.eye(4)]          # start, end
    active = [True, True]
    stack = []
    state = {"material": {"type": "diffuse", "reflectance": list(sen.average(np.full(LAM.shape, 0.5)))},
             "light": None, "inside": None, "outside": None,
             "light_attrs": {}, "light_group": None}        # Attribute "light" "string group" (docs/optics.md)
    lights = []                           # the emitters' groups and spectra, written when any light has a group
    n = 0
    textures = {}                         # name -> ("float", image json) | ("family", family json); global, as pbrt's

    def named(p, key, kind, where):
        """The texture a "texture KEY" parameter names, which must be of the kind (float, family)."""
        name = one(p, key)
        if name not in textures or textures[name][0] != kind:
            raise SystemExit(f"{where}: \"texture {key}\" {name!r} is not a {kind} texture defined before it")
        return textures[name][1]

    def apply(m):
        for i in (0, 1):
            if active[i]:
                ctm[i] = ctm[i] @ m

    def metres(m):
        return (scale(MM, MM, MM) @ m).tolist()

    for d, args in read_statements(path, base):
        if d == "LookAt":
            e, t, u = np.array(args[0:3]), np.array(args[3:6]), np.array(args[6:9])
            out["camera"] = {"eye": list(e * MM), "target": list(t * MM), "up": list(u)}
        elif d == "Camera":
            if args[0] != "perspective":
                raise SystemExit(f"camera {args[0]} not handled")
            p = params(args[1:])
            out["camera"].update({"fov_short_deg": one(p, "fov"), "lens_radius_m": one(p, "lensradius", 0) * MM,
                                  "focus_m": one(p, "focaldistance", 1e6) * MM,
                                  "shutter": [one(p, "shutteropen", 0), one(p, "shutterclose", 1)]})
        elif d == "Sampler":
            out["spp"] = int(one(params(args[1:]), "pixelsamples", 16))
        elif d == "Integrator":
            out["maxdepth"] = int(one(params(args[1:]), "maxdepth", 5))
        elif d == "Film":
            p = params(args[1:])
            if one(p, "rawsensor") is not True:
                raise SystemExit("the film must write raw sensor RGB (\"bool rawsensor\" true)")
            if one(p, "sensor") not in (None, sensor_name):
                raise SystemExit(f"film sensor {one(p, 'sensor')} differs from {sensor_name}")
            out["film"] = {"res": [int(one(p, "xresolution")), int(one(p, "yresolution"))],
                           "filename": one(p, "filename"), "iso": one(p, "iso", 100)}
        elif d == "WorldBegin":
            ctm = [np.eye(4), np.eye(4)]
        elif d == "AttributeBegin":
            stack.append(([c.copy() for c in ctm], dict(state)))
        elif d == "AttributeEnd":
            ctm, state = stack.pop()
        elif d == "ActiveTransform":
            active = {"StartTime": [True, False], "EndTime": [False, True], "All": [True, True]}[args[0]]
        elif d == "Translate":
            apply(translate(*args[:3]))
        elif d == "Rotate":
            apply(rotate(*args[:4]))
        elif d == "Scale":
            apply(scale(*args[:3]))
        elif d == "AreaLightSource":
            if args[0] != "diffuse":
                raise SystemExit(f"area light {args[0]} not handled")
            p = params(args[1:])
            if "L" not in p:
                raise SystemExit("area light without L")
            typ, v = p["L"]
            L, photo = sen.illuminant(typ.split()[0], v)
            sc = one(p, "scale", 1.0) / (sen.S.cmf[1] @ photo)
            if one(p, "twosided", False) is not False:
                raise SystemExit("two-sided area lights not handled")
            state["light"] = list(sen.emission(L * sc))
            state["light_group"] = state["light_attrs"].get("group")       # pbrt takes the attributes in force now
            state["light_spectrum"] = (f"{typ.split()[0]} {v[0]:g}" if len(v) == 1 and not isinstance(v[0], str)
                                       else f"{typ.split()[0]} {v[0]}" if len(v) == 1 else f"{typ.split()[0]} [sampled]")
        elif d == "Attribute":
            # pbrt-v4 marks attribute parameters "may be unused", so it renders a scene that tags its lights this way;
            # we read one: the light group an area light belongs to (one Cycles pass per group)
            p = params(args[1:])
            if args[0] != "light" or set(p) != {"group"} or p["group"][0] != "string":
                raise SystemExit(f'Attribute {args[0]!r} {sorted(p)}: only Attribute "light" "string group" is handled')
            state["light_attrs"] = {**state["light_attrs"], "group": p["group"][1][0]}
        elif d == "Texture":
            p = params(args[3:])
            where = f"Texture {args[0]!r}"
            if args[1] == "float" and args[2] == "imagemap":
                textures[args[0]] = ("float", image_texture(p, base, where))
            elif args[1] == "spectrum" and args[2] == "familymap":
                textures[args[0]] = ("family", family_table(p, base, sen, where))
            else:
                raise SystemExit(f"{where}: texture {args[1]} {args[2]} not handled")
        elif d == "Material":
            p = params(args[1:])
            state["material"] = material(args[0], p, base, sen, named)
        elif d == "MakeNamedMedium":
            p = params(args[1:])
            if one(p, "type") != "homogeneous":
                raise SystemExit("only homogeneous media are handled")
            k = one(p, "scale", 1.0) / MM          # 1/mm -> 1/m
            sa = sen.average(sen.reflectance(*[p["sigma_a"][0].split()[0], p["sigma_a"][1]])) * k
            ss = sen.average(sen.reflectance(*[p["sigma_s"][0].split()[0], p["sigma_s"][1]])) * k
            out["media"][args[0]] = {"sigma_a_per_m": list(sa), "sigma_s_per_m": list(ss), "g": one(p, "g", 0.0)}
        elif d == "MediumInterface":
            state["inside"], state["outside"] = (args[0] or None), (args[1] or None) if len(args) > 1 else (args[0] or None)
        elif d == "Shape":
            p = params(args[1:])
            obj = {"name": f"{args[0]}{n}", "material": state["material"], "emission": state["light"],
                   "inside": state["inside"], "outside": state["outside"]}
            if state["light"]:
                lights.append({"object": obj["name"], "group": state["light_group"], "spectrum": state["light_spectrum"]})
                if state["light_group"] is not None:
                    obj["light_group"] = state["light_group"]
            n += 1
            if args[0] == "bilinearmesh":
                P = np.array(p["P"][1]).reshape(-1, 3)
                if len(P) != 4 or p.get("indices", (None, [0, 1, 2, 3]))[1] != [0, 1, 2, 3]:
                    raise SystemExit("only single-patch bilinear meshes are handled")
                obj.update(kind="quad", P=P.tolist())
                if "uv" in p:                      # per corner, in the order of P (p00 p10 p01 p11); else (0,0) (1,0) (0,1) (1,1)
                    obj["uv"] = np.array(p["uv"][1], float).reshape(4, 2).tolist()
            elif args[0] == "disk":
                obj.update(kind="disk", radius=one(p, "radius", 1.0))
            elif args[0] == "plymesh":
                obj.update(kind="ply", file=os.path.relpath(os.path.join(base, one(p, "filename")), base))
            else:
                raise SystemExit(f"shape {args[0]} not handled")
            if obj["inside"] and obj["inside"] != obj["outside"] and state["material"]["type"] == "dielectric":
                # Cycles fills a medium only inside a watertight mesh (an open glaze sheet renders 12-24% dark,
                # docs/slab.md): refuse rather than render wrong
                if obj["kind"] != "ply":
                    raise SystemExit(f"{obj['name']}: medium {obj['inside']!r} inside a {obj['kind']}: Cycles needs a "
                                     f"closed mesh around a medium (docs/slab.md); write it as a closed plymesh "
                                     f"(tools/shell.py)")
                P, T = shell.read_ply(os.path.join(base, obj["file"]))
                bad = shell.watertight(P, T)
                if bad:
                    raise SystemExit(f"{obj['name']} ({obj['file']}): medium {obj['inside']!r} inside a mesh with {bad} "
                                     f"open or inconsistent edges: Cycles needs a closed mesh around a medium, or it "
                                     f"renders the medium dark (docs/slab.md); close it (tools/shell.py) or render "
                                     f"this scene in pbrt")
            obj["matrix"] = metres(ctm[0])
            if not np.allclose(ctm[0], ctm[1]):
                obj["matrix_end"] = metres(ctm[1])
            out["objects"].append(obj)
        else:
            raise SystemExit(f"directive {d} not handled")
    if any(l["group"] is not None for l in lights):
        missing = [l["object"] for l in lights if l["group"] is None]
        if missing:
            raise SystemExit(f"emitters {missing} have no light group while others have one: the groups would not add "
                             f"up to the whole render")
        out["lights"] = lights
        key = f"blackbody {key_K:g}"
        other = sorted({l["spectrum"] for l in lights if l["spectrum"] != key})
        if other:
            print(f"note: lights with spectra {other} differ from the key ({key}) that weights reflectances and media: "
                  f"their colour after a bounce is approximate (docs/optics.md)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--sensor", default="canon_eos_5d_mkiv")
    ap.add_argument("--key-K", type=float, default=5500.0,
                    help="the key light that weights reflectances and coefficients (camera.json's light)")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    out = convert(a.scene, a.sensor, a.key_K)
    path = a.out or os.path.join(os.path.dirname(os.path.abspath(a.scene)), "scene.cycles.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"{len(out['objects'])} objects, media {list(out['media'])} -> {path}")


if __name__ == "__main__":
    main()
