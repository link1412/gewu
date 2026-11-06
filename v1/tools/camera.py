"""The camera: pbrt's raw sensor RGB in, the finished H.264 out, made the way a photograph is.

    python3 -I tools/camera.py matrix  --shot 6                        # white balance, colour matrix, its ColorChecker errors
    python3 -I tools/camera.py develop --shot 6 --first 100 RAW.exr…   # raw frames -> out/dev/fNNNN.png (16-bit R'G'B')
    python3 -I tools/camera.py develop --settings PATH/camera.json --first 0 RAW.exr…   # same, a camera.json anywhere
    python3 -I tools/camera.py encode  --frames 100-106                # out/dev -> out/film.mp4 -> out/film/fNNNN.png

The chain (DESIGN 5):
1. Raw. pbrt's patched film ("bool rawsensor" true) writes imagingRatio x the integral of the
   sensor's spectral response times radiance, per channel, with no matrix.
2. Diffraction. pbrt traces rays, so the scene builder writes optics.json (f-number,
   magnification) next to the scene and the chain convolves each channel with the polychromatic
   Airy pattern of that aperture, weighted by the channel's response to the key light.
3. Electrons. The photographer's exposure puts a highlight percentile at a chosen fraction of
   the sensor's saturation. Each 1080p pixel sums the photosites behind it, R and B a quarter
   of them and G half (Bayer); Poisson shot noise and Gaussian read noise on that sum. The
   mosaic and its demosaicing are finer than a 1080p pixel (3.5 photosites across) and are not
   simulated; nor are PRNU, quantisation and pattern noise (see the sensor file for why).
4. White balance on the scene's key light seen through the same sensor (a grey card), or on the
   blackbody camera.json's white_balance names (a photographer's Kelvin setting).
5. Colour matrix, sensor RGB to XYZ: least squares on the 24 ColorChecker patches lit by that
   light, against their colours under D65, constrained to keep white white (a custom profile,
   as art photographers make); then XYZ to linear BT.709.
6. Tone: exposure in stops; a contrast about a pivot (a straight line of slope `contrast` in log
   exposure, as a film's or a camera's tone curve has in its middle), fitted per shot to the original's
   large-scale levels (`grade`); then a shoulder that rolls the sensor's saturation into white.
7. sRGB encoding: a photograph dropped into a BT.709 timeline keeps its code values.
8. Unsharp mask on luma, if the shot asks for it.
9. Y'CbCr: BT.709 matrix, limited range, 4:2:0 with chroma sited left, as the original.
10. H.264: x264 with the options in the original's own SEI, cut into the original's 75-frame
   segments (it is a segmented transcode: I-frames at 0, 75, ... 450 under keyint=infinite).

Data, from one source, the renderer's: the sensor's curves, the CIE 1931 observer, D65 and the
24 ColorChecker reflectances (BabelColor) are read out of pbrt's sources. Sensor noise:
tools/sensors/*.json, with sources. Per-shot settings: shots/NN-*/camera.json.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from scipy import ndimage, special

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import DECODE_VF, arc_poly, load_spec  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PBRT_SRC = os.path.join(ROOT, "third_party/pbrt-v4/src/pbrt")
IMGTOOL = os.path.join(ROOT, "third_party/pbrt-build/imgtool")
FW, FH, FPS = 1920, 1080, 25
SEGMENT = 75                       # the original's I-frames: 0, 75, ..., 450
LAM = np.arange(360.0, 831.0)      # pbrt's Lambda_min..Lambda_max: its 1 nm sums (InnerProduct, ProjectReflectance)
KR, KB = 0.2126, 0.0722            # BT.709 luma
GRADE_SIGMA_PX, GRADE_MARGIN_PX = 40.0, 60.0    # cmd_grade: the light's scale, and clear of the limb

# The original's x264 options, from its SEI (core 164 r3095), in x264's parameter names.
X264 = ("cabac=1:ref=5:deblock=0,0:partitions=i4x4,i8x8,p8x8,b8x8:me=hex:subme=2:psy=0:mixed-refs=1:"
        "merange=16:chroma-me=1:trellis=1:8x8dct=1:cqm=flat:deadzone-inter=21:deadzone-intra=11:"
        "fast-pskip=1:chroma-qp-offset=0:threads=5:lookahead-threads=1:sliced-threads=0:nr=0:"
        "dct-decimate=1:interlaced=0:bluray-compat=0:stitchable=1:constrained-intra=0:bframes=3:"
        "b-pyramid=normal:b-adapt=1:b-bias=0:direct=spatial:weightb=1:open-gop=1:weightp=2:"
        "keyint=infinite:min-keyint=30:scenecut=0:intra-refresh=0:rc-lookahead=40:mbtree=0:crf=23:"
        "qcomp=0.6:qpmin=10:qpmax=69:qpstep=4:vbv-maxrate=10240:vbv-bufsize=10240:nal-hrd=none:"
        "filler=0:ipratio=1.4:pbratio=1.3:aq-mode=2:aq-strength=1.0")


# --- spectral data, read out of pbrt ---------------------------------------------------------
def _numbers(body):
    body = re.sub(r"//[^\n]*", "", body)
    return np.array([float(v) for v in re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", body)])


def pbrt_array(name, src="util/spectrum.cpp"):
    text = open(os.path.join(PBRT_SRC, src)).read()
    m = re.search(r"const Float " + re.escape(name) + r"\[[^\]]*\]\s*=\s*\{(.*?)\};", text, re.S)
    if not m:
        raise SystemExit(f"{name}: not in pbrt's {src}")
    return _numbers(m.group(1))


def piecewise(interleaved):
    """pbrt's PiecewiseLinearSpectrum on LAM: linear between samples, zero outside them."""
    return np.interp(LAM, interleaved[0::2], interleaved[1::2], left=0.0, right=0.0)


def swatches():
    """The 24 ColorChecker reflectances of PixelSensor::swatchReflectances (film.cpp), on LAM."""
    text = open(os.path.join(PBRT_SRC, "film.cpp")).read()
    block = text[text.index("PixelSensor::swatchReflectances"):]
    block = block[:block.index("};")]
    out = [piecewise(_numbers(b)) for b in re.findall(r"FromInterleaved\(\s*\{(.*?)\}", block, re.S)]
    if len(out) != 24:
        raise SystemExit(f"film.cpp: {len(out)} swatches, expected 24")
    return np.array(out)


def blackbody(T):
    """pbrt's Blackbody(lambda, T) on LAM, up to scale."""
    c, h, kb = 299792458.0, 6.62606957e-34, 1.3806488e-23
    l = LAM * 1e-9
    return 2 * h * c * c / (l ** 5 * (np.exp(h * c / (l * kb * T)) - 1))


class Spectra:
    def __init__(self, sensor_name):
        lam = pbrt_array("CIE_lambda")
        self.cmf = np.array([np.interp(LAM, lam, pbrt_array(n)) for n in ("CIE_X", "CIE_Y", "CIE_Z")])
        self.d65 = piecewise(pbrt_array("CIE_Illum_D6500"))
        self.sens = np.array([piecewise(pbrt_array(f"{sensor_name}_{c}")) for c in "rgb"])
        self.swatches = swatches()


# --- colour -------------------------------------------------------------------------------------
def rgb709_from_xyz(white):
    xy = np.array([[0.64, 0.33], [0.30, 0.60], [0.15, 0.06]])
    P = np.stack([xy[:, 0] / xy[:, 1], np.ones(3), (1 - xy.sum(1)) / xy[:, 1]])   # columns: the primaries, Y = 1
    return np.linalg.inv(P * np.linalg.solve(P, white))


def lab(xyz, white):
    t = xyz / white
    f = np.where(t > (6 / 29) ** 3, np.cbrt(t), t / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def calibrate(S, light):
    """White-balance gains and the matrix from white-balanced sensor RGB to linear BT.709."""
    w = S.sens @ light                                   # the sensor's RGB of a white card
    cam = (S.swatches * light) @ S.sens.T / w            # white balanced: white -> (1, 1, 1)
    yn = S.cmf[1] @ S.d65
    xyz = (S.swatches * S.d65) @ S.cmf.T / yn            # the patches' colours under D65
    white = S.cmf @ S.d65 / yn
    # least squares, one XYZ row at a time, with the constraint M (1,1,1) = white (KKT system)
    K = np.block([[cam.T @ cam, np.ones((3, 1))], [np.ones((1, 3)), np.zeros((1, 1))]])
    M = np.array([np.linalg.solve(K, np.r_[cam.T @ xyz[:, j], white[j]])[:3] for j in range(3)])
    free = np.linalg.lstsq(cam, xyz, rcond=None)[0].T
    err = lambda m: np.linalg.norm(lab(cam @ m.T, white) - lab(xyz, white), axis=1)
    return {"gains": w[1] / w, "C": rgb709_from_xyz(white) @ M, "M": M,
            "dE": err(M), "dE_free": err(free)}


def light_spectrum(cam):
    L = cam["light"]
    if "blackbody_K" in L:
        return blackbody(L["blackbody_K"])
    raise SystemExit("camera.json: light must give blackbody_K")


def balance_spectrum(cam):
    """What the white balance is set for: the key light, unless camera.json sets white_balance.K
    (a photographer's choice, as a camera's Kelvin setting; the diffraction stays weighted by the light)."""
    wb = cam.get("white_balance", {})
    return blackbody(wb["K"]) if "K" in wb else light_spectrum(cam)


# --- images -------------------------------------------------------------------------------------
def read_raw(path):
    with tempfile.TemporaryDirectory() as d:
        pfm = os.path.join(d, "raw.pfm")
        subprocess.run([IMGTOOL, "convert", "--outfile", pfm, path], check=True, capture_output=True)
        with open(pfm, "rb") as f:
            if f.readline().strip() != b"PF":
                raise SystemExit(f"{path}: not an RGB image")
            w, h = map(int, f.readline().split())
            scale = float(f.readline())
            a = np.frombuffer(f.read(), "<f4" if scale < 0 else ">f4").reshape(h, w, 3)
    return np.flipud(a).astype(np.float64)


def to_film_size(raw):
    h, w, _ = raw.shape
    if (w, h) == (FW, FH):
        return raw, ""
    if w % FW == 0 and h % FH == 0 and w // FW == h // FH:
        k = w // FW
        return raw.reshape(FH, k, FW, k, 3).mean((1, 3)), f"binned {k}x{k}"
    if FW % w == 0 and FH % h == 0 and FW // w == FH // h:
        k = FW // w
        return ndimage.zoom(raw, (k, k, 1), order=1), f"PREVIEW: raw {w}x{h} upsampled {k}x before the noise"
    raise SystemExit(f"raw {w}x{h}: not a whole multiple or fraction of {FW}x{FH}")


def srgb_encode(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.maximum(x, 0.0031308) ** (1 / 2.4) - 0.055)


def shoulder(x, start, white):
    """Linear up to `start`, then an exponential roll-off that reaches 1 at `white` with matching
    slope at `start` (monotonic for any white). With white <= 1 the image is simply linear."""
    if white <= 1:
        return x
    m = (white - start) / (1 - start)                    # slope needed at start, in units of the roll-off
    a = 1.0
    for _ in range(60):                                  # solve a / (1 - exp(-a)) = m (Newton)
        e = np.exp(-a)
        f = a / (1 - e) - m
        df = (1 - e - a * e) / (1 - e) ** 2
        a -= f / df
    u = np.clip((x - start) / (white - start), 0, 1)
    return np.where(x <= start, x, start + (1 - start) * (1 - np.exp(-a * u)) / (1 - np.exp(-a)))


def tone(x, d):
    """Linear scene values (a grey at saturation = 2^ev) to linear display values in [0, 1]: the contrast
    about the pivot, then the shoulder from shoulder_from to where the saturation of a grey has gone."""
    c, p = d.get("contrast", 1.0), d.get("pivot", 0.18)
    sat = 2.0 ** d["ev"]
    if c != 1.0:
        x = p * (np.maximum(x, 0.0) / p) ** c
        sat = p * (sat / p) ** c
    return shoulder(x, d["shoulder_from"], sat)


def airy_kernels(S, light, optics, radius_px=8, sub=8):
    """Per-channel diffraction PSF on the 1080p pixel grid: the Airy pattern of an ideal lens at
    working f-number N (1 + m) (pupil magnification taken as 1), averaged over wavelength with the
    channel's response to the light as weights, integrated over each pixel's area. Cut at
    radius_px: at f/38 that keeps ~97% of the pattern (Rayleigh: 1 - 2/(pi x) far out); the rest,
    a faint wide skirt, is renormalised away."""
    N = optics["f_number"] * (1 + optics["magnification"])
    px_um = optics["sensor_width_mm"] / FW * 1000
    n = 2 * radius_px + 1
    g = (np.arange(n * sub) + 0.5) / sub - n / 2                     # sub-pixel centres, in px
    r_um = np.hypot(*np.meshgrid(g, g)) * px_um
    lam = LAM[(LAM >= 380) & (LAM <= 720)][::10]
    ks = []
    for c in range(3):
        w = np.interp(lam, LAM, S.sens[c] * light)
        k = np.zeros_like(r_um)
        for l, wl in zip(lam, w / w.sum()):
            x = np.pi * r_um / (l * 1e-3 * N)
            a = np.where(x > 1e-9, 2 * special.j1(x) / np.maximum(x, 1e-9), 1.0) ** 2
            k += wl * a / a.sum()
        ks.append(k.reshape(n, sub, n, sub).sum((1, 3)))
    return [k / k.sum() for k in ks], N


def exposure_ref(paths, ex):
    """The raw value the exposure puts at `of_saturation`: fixed for the whole shot, as a real
    camera's manual exposure (a per-frame meter would flicker)."""
    if "raw_ref" in ex:
        return ex["raw_ref"], "fixed in camera.json"
    ref = max(np.percentile(read_raw(p).max(2), ex["percentile"]) for p in paths)
    if not ref > 0:
        raise SystemExit("black frames")
    return ref, f"{ex['percentile']}th percentile, max over {len(paths)} frames; freeze it as expose.raw_ref"


def diffract(raw, psf):
    """Convolve each channel with its PSF; edges extended ("nearest"). FFT on the padded image: the same numbers as
    ndimage.convolve(mode="nearest") to float rounding (S10: 0.3 s instead of 7.6 s per 1080p frame). Clipped at 0: the
    FFT's rounding leaves ~-1e-17 in black areas, which the Poisson noise rejects (shot 27's black studio, S10)."""
    from scipy.signal import fftconvolve
    out = []
    for c in range(3):
        h = psf[c].shape[0] // 2
        pad = np.pad(raw[..., c], h, mode="edge")
        out.append(np.maximum(fftconvolve(pad, psf[c], mode="valid"), 0.0))
    return np.stack(out, -1)


def develop(raw, ref, cam, sensor, cal, rng, psf=None, diffracted=None):
    if diffracted is not None:
        raw, note = diffracted
    else:
        raw, note = to_film_size(raw)
        if psf is not None:
            raw = diffract(raw, psf)
    iso = cam["iso"]
    if iso < sensor["base_iso"]:
        raise SystemExit(f"ISO {iso}: below the base ISO, not modelled")
    rn = sensor["read_noise_e"].get(str(iso))
    if rn is None:
        raise SystemExit(f"ISO {iso}: no read noise measurement in the sensor file")
    sat = sensor["saturation_e_at_base_iso"] * sensor["base_iso"] / iso
    mean_e = np.minimum(raw * (cam["expose"]["of_saturation"] * sat / ref), sat)   # electrons per photosite
    n = np.array([0.25, 0.5, 0.25]) * (sensor["photosites"][0] / FW) ** 2   # R, G, B photosites per pixel
    total = rng.poisson(mean_e * n) + rng.normal(0.0, rn["e"] * np.sqrt(n), mean_e.shape)
    v = np.minimum(total / n / sat, 1.0)                                 # in units of saturation
    g = cal["gains"]
    v = np.minimum(v * g, g.min())                       # white balance; clipped highlights go white
    lin = np.maximum(v @ cal["C"].T, 0.0)
    k = 2.0 ** cam["develop"]["ev"] / g.min()            # saturation of a grey -> 2^ev
    rgb = srgb_encode(tone(lin * k, cam["develop"]))
    sh = cam.get("sharpen", {"amount": 0})
    if sh["amount"] > 0:
        Y = rgb @ np.array([KR, 1 - KR - KB, KB])
        rgb = rgb + sh["amount"] * (Y - ndimage.gaussian_filter(Y, sh["sigma_px"]))[..., None]
    return np.clip(rgb, 0, 1), note


def write_png16(path, rgb):
    a = np.round(np.clip(rgb, 0, 1) * 65535).astype("<u2")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le",
                    "-s", f"{a.shape[1]}x{a.shape[0]}", "-i", "-", "-frames:v", "1", path],
                   input=a.tobytes(), check=True)


def read_png16(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-f", "rawvideo",
                          "-pix_fmt", "rgb48le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<u2").reshape(FH, FW, 3) / 65535.0


def ycbcr420(rgb):
    """R'G'B' in [0, 1] -> 8-bit Y', Cb, Cr planes: BT.709, limited range, 4:2:0 sited left."""
    Y = rgb @ np.array([KR, 1 - KR - KB, KB])
    Cb = (rgb[..., 2] - Y) / (2 * (1 - KB))
    Cr = (rgb[..., 0] - Y) / (2 * (1 - KR))

    def sub(c):                     # rows averaged in pairs; columns [1 2 1]/4 about the even ones
        c = 0.5 * (c[0::2] + c[1::2])
        p = np.pad(c, ((0, 0), (1, 1)), mode="edge")
        return 0.25 * p[:, 0:-2:2] + 0.5 * p[:, 1:-1:2] + 0.25 * p[:, 2::2]

    q = lambda v: np.clip(np.round(v), 0, 255).astype(np.uint8)
    return q(16 + 219 * Y), q(128 + 224 * sub(Cb)), q(128 + 224 * sub(Cr))


def x264_options(path):
    with open(path, "rb") as f:
        m = re.search(rb"x264 - core (\d+ r\d+)[^\x00]*? - options: ([^\x00\x80]*)", f.read(1 << 20))
    if not m:
        raise SystemExit(f"{path}: no x264 SEI")
    return m.group(1).decode(), dict(t.split("=", 1) for t in m.group(2).decode().split())


# --- commands -----------------------------------------------------------------------------------
def rel(p):
    r = os.path.relpath(p, ROOT)
    return p if r.startswith("..") else r


def settings_camera(path):
    """A camera.json anywhere (material cards are not shots)."""
    if not os.path.exists(path):
        raise SystemExit(f"{path}: no such camera settings file")
    cam = json.load(open(path))
    sensor = json.load(open(os.path.join(ROOT, "tools/sensors", cam["sensor"] + ".json")))
    return cam, sensor


def shot_camera(n):
    hits = glob.glob(os.path.join(ROOT, f"shots/{n:02d}-*/camera.json"))
    if len(hits) != 1:
        raise SystemExit(f"shot {n}: expected one shots/{n:02d}-*/camera.json, found {len(hits)}")
    cam = json.load(open(hits[0]))
    sensor = json.load(open(os.path.join(ROOT, "tools/sensors", cam["sensor"] + ".json")))
    return cam, sensor


def cmd_matrix(a):
    cam, sensor = shot_camera(a.shot)
    cal = calibrate(Spectra(sensor["pbrt_sensor"]), balance_spectrum(cam))
    np.set_printoptions(precision=4, suppress=True)
    print(f"{sensor['name']} under {cam['light']}, white balance {cam.get('white_balance', 'on the light')}")
    print("white balance gains (G = 1):", cal["gains"])
    print("white-balanced sensor RGB -> linear BT.709:\n", cal["C"])
    print(f"ColorChecker dE*ab: mean {cal['dE'].mean():.2f}, max {cal['dE'].max():.2f} (patch {cal['dE'].argmax() + 1}); "
          f"without the white constraint: mean {cal['dE_free'].mean():.2f}, max {cal['dE_free'].max():.2f}")


def cmd_develop(a):
    cam, sensor = settings_camera(a.settings) if a.settings else shot_camera(a.shot)
    S, light = Spectra(sensor["pbrt_sensor"]), light_spectrum(cam)
    cal = calibrate(S, balance_spectrum(cam))
    psf = None
    if not a.no_diffraction:
        optics = [os.path.join(os.path.dirname(os.path.abspath(p)), "optics.json") for p in a.raw]
        if any(not os.path.exists(o) for o in optics) or len({open(o).read() for o in optics}) != 1:
            raise SystemExit("every raw needs the same optics.json beside it (written by the scene builder); "
                             "--no-diffraction to go without")
        psf, N = airy_kernels(S, light, json.load(open(optics[0])))
        print(f"diffraction: working f/{N:.1f}, centre pixel keeps {psf[1][len(psf[1]) // 2].max():.0%} (G)")
    os.makedirs(a.out, exist_ok=True)
    ref, how = exposure_ref(a.raw, cam["expose"])
    print(f"exposure: raw {ref:.6g} -> {cam['expose']['of_saturation']} of saturation ({how})")
    # a still (the same raw for several frames) is read and diffracted once; PNG writes overlap the next frame (S10)
    from concurrent.futures import ThreadPoolExecutor
    cache = {}
    with ThreadPoolExecutor(4) as pool:
        jobs = []
        for i, path in enumerate(a.raw):
            f = a.first + i
            key = os.path.abspath(path)
            if key not in cache:
                cache.clear()
                r, note0 = to_film_size(read_raw(path))
                cache[key] = (diffract(r, psf) if psf is not None else r, note0)
            rng = np.random.default_rng([cam["seed"], f])
            rgb, note = develop(None, ref, cam, sensor, cal, rng, psf, diffracted=cache[key])
            jobs.append(pool.submit(write_png16, os.path.join(a.out, f"f{f:04d}.png"), rgb))
            print(f"f{f:04d} <- {rel(path)} {note}")
        for j in jobs:
            j.result()


def srgb_decode(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def cmd_grade(a):
    """Fit the shot's contrast and pivot so that its large-scale levels match the original's: the 10th, 50th
    and 90th percentiles of luma blurred at GRADE_SIGMA_PX (the light, not the texture, which differs by subject)
    over the object (below the spec's arc, GRADE_MARGIN_PX clear of it), one frame of each. Our frame is
    developed with the shot's camera.json, then the tone is redone from its linear values (tone is per pixel)."""
    from scipy.optimize import least_squares
    cam, sensor = shot_camera(a.shot)
    sh = next(s for s in load_spec()["shots"] if s["shot"] == a.shot)
    if not sh["arc"]:
        raise SystemExit(f"shot {a.shot}: no arc in the spec to separate the object from the sky")
    S = Spectra(sensor["pbrt_sensor"])
    cal = calibrate(S, balance_spectrum(cam))
    psf = airy_kernels(S, light_spectrum(cam), json.load(open(os.path.join(os.path.dirname(os.path.abspath(a.raw)), "optics.json"))))[0]
    ref, _ = exposure_ref([a.raw], cam["expose"])
    flat = dict(cam, develop=dict(cam["develop"], contrast=1.0))
    flat["develop"]["shoulder_from"] = 1.0                # linear and unclipped below saturation
    rgb, _ = develop(read_raw(a.raw), ref, flat, sensor, cal, np.random.default_rng([cam["seed"], a.frame]), psf)
    lin = srgb_decode(rgb)
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", a.orig, "-vf",
                          f"select=eq(n\\,{a.frame}),{DECODE_VF}", "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    orig = np.frombuffer(raw, np.uint8).reshape(FH, FW, 3) / 255.0
    yy, xx = np.mgrid[0:FH, 0:FW]
    mask = yy > arc_poly(sh["arc"])(xx) + GRADE_MARGIN_PX
    Yw = np.array([KR, 1 - KR - KB, KB])
    q = [10, 50, 90]
    levels = lambda img: np.percentile(ndimage.gaussian_filter(img @ Yw, GRADE_SIGMA_PX)[mask], q) * 255
    target = levels(orig)
    d0 = cam["develop"]
    ours = lambda c, p: levels(srgb_encode(tone(lin, dict(d0, contrast=c, pivot=p))))
    fit = least_squares(lambda u: ours(*u) - target, [1.2, 0.18], bounds=([0.5, 0.01], [3.0, 1.0]))
    c, p = fit.x
    print(f"shot {a.shot} frame {a.frame}: luma blurred {GRADE_SIGMA_PX} px, p{q} over the object")
    print(f"  original {np.round(target, 1)}")
    print(f"  ours now (contrast {d0.get('contrast', 1.0)}, pivot {d0.get('pivot', 0.18)}) {np.round(ours(d0.get('contrast', 1.0), d0.get('pivot', 0.18)), 1)}")
    print(f"  ours fitted {np.round(ours(c, p), 1)}")
    print(f'  -> camera.json develop: "contrast": {c:.3f}, "pivot": {p:.4f}')


def cmd_encode(a):
    lo, _, hi = a.frames.partition("-")
    frames = list(range(int(lo), int(hi or lo) + 1))
    paths = [os.path.join(a.dev, f"f{f:04d}.png") for f in frames]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise SystemExit(f"missing {len(missing)} developed frames, first {missing[0]}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        segs = []
        for s in sorted({f // SEGMENT for f in frames}):
            seg = os.path.join(d, f"seg{s}.mp4")
            enc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                                    "-pix_fmt", "yuv420p", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
                                    "-c:v", "libx264", "-profile:v", "high", "-x264-params", X264, seg],
                                   stdin=subprocess.PIPE)
            for f, p in zip(frames, paths):
                if f // SEGMENT == s:
                    for plane in ycbcr420(read_png16(p)):
                        enc.stdin.write(plane.tobytes())
            enc.stdin.close()
            if enc.wait():
                raise SystemExit("x264 failed")
            segs.append(seg)
        lst = os.path.join(d, "segments.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{s}'\n" for s in segs)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", "-movflags", "+faststart", a.out], check=True)
    core, ours = x264_options(a.out)
    core0, orig = x264_options(os.path.join(ROOT, "ref/opus55.mp4"))
    diff = {k: (orig.get(k), ours.get(k)) for k in sorted(set(orig) | set(ours)) if orig.get(k) != ours.get(k)}
    print(f"x264 core {core} (original {core0}); options that differ: {diff or 'none'}")
    print(f"{len(frames)} frames, {os.path.getsize(a.out) * 8 / (len(frames) / FPS) / 1e6:.2f} Mb/s "
          f"(the original: 5.12 Mb/s over the whole film)")
    if a.decode:
        os.makedirs(a.decode, exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.out, "-vf", DECODE_VF,
                        "-start_number", str(frames[0]), os.path.join(a.decode, "f%04d.png")], check=True)
        print(f"decoded to {rel(a.decode)}/f{frames[0]:04d}.png ...")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("matrix")
    p.add_argument("--shot", type=int, required=True)
    p = sub.add_parser("develop")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--shot", type=int)
    g.add_argument("--settings", help="a camera.json anywhere, instead of a shot's")
    p.add_argument("--first", type=int, required=True, help="film frame of the first raw file")
    p.add_argument("--out", default=os.path.join(ROOT, "out/dev"))
    p.add_argument("--no-diffraction", action="store_true", help="skip the Airy PSF (say so wherever it is used)")
    p.add_argument("raw", nargs="+")
    p = sub.add_parser("encode")
    p.add_argument("--frames", required=True, help="film frames, e.g. 100-106")
    p.add_argument("--dev", default=os.path.join(ROOT, "out/dev"))
    p.add_argument("--out", default=os.path.join(ROOT, "out/film.mp4"))
    p.add_argument("--decode", default=os.path.join(ROOT, "out/film"), help="decoded PNGs for compare.py ('' to skip)")
    p = sub.add_parser("grade", help="fit the shot's contrast to the original's large-scale levels")
    p.add_argument("--shot", type=int, required=True)
    p.add_argument("--frame", type=int, required=True, help="film frame, the original's and the raw's")
    p.add_argument("--raw", required=True, help="our raw render of that frame (optics.json beside it)")
    p.add_argument("--orig", default=os.path.join(ROOT, "ref/opus55.mp4"))
    a = ap.parse_args()
    {"matrix": cmd_matrix, "develop": cmd_develop, "encode": cmd_encode, "grade": cmd_grade}[a.cmd](a)


if __name__ == "__main__":
    main()
