"""The darkroom: scene-linear image -> a photograph. What a lens, a sensor and a raw developer do to light.

Order follows the light: lens (chromatic aberration, vignette, veiling glare and halation) -> sensor (exposure,
white balance) -> developer (tone curve, saturation, capture sharpening) -> grain. Grain goes last and is a
separate call for moving shots, so that it changes on every frame while the still stays put.
"""

import cv2
import numpy as np


def _radial(img, scale):
    h, w = img.shape[:2]
    X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    return cv2.remap(img, cx + (X - cx) / scale, cy + (Y - cy) / scale, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def srgb_encode(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def tone(x, contrast=1.25, mid=0.18):
    """Film-like S-curve per channel (Naka-Rushton): a soft toe, highlights that roll off and desaturate.
    Scene-linear `mid` lands on display-linear `mid`; white is approached, never hit."""
    xc = np.power(np.maximum(x, 0.0), contrast)
    m = mid**contrast * (1.0 / mid - 1.0)
    return xc / (xc + m)


def develop(
    L,
    exposure=0.0,
    wb=(1.0, 1.0, 1.0),
    contrast=1.25,
    mid=0.18,
    saturation=1.0,
    black=0.0,
    ca=0.0004,
    vignette=0.25,
    glare=0.004,
    halation=0.05,
    sharpen=0.45,
    grain=1.4,
    seed=1,
):
    h, w = L.shape[:2]
    scale = w / 1920.0
    x = L.astype(np.float32).copy()

    # lens: lateral chromatic aberration
    if ca:
        x[..., 0] = _radial(x[..., 0], 1.0 + ca)
        x[..., 2] = _radial(x[..., 2], 1.0 - ca)

    # sensor: exposure and white balance
    x = x * (2.0**exposure) * np.array(wb, np.float32)

    # lens: vignette
    if vignette:
        Y, X = np.ogrid[:h, :w]
        r2 = ((X - (w - 1) / 2.0) ** 2 + (Y - (h - 1) / 2.0) ** 2) / (((w - 1) / 2.0) ** 2 + ((h - 1) / 2.0) ** 2)
        x = x * (1.0 - vignette * r2[..., None] ** 1.3).astype(np.float32)

    # lens and sensor: halation (warm glow around highlights, in the sensor stack or the film base) and veiling glare
    if halation or glare:
        hi = np.maximum(x - 0.8, 0.0)
        hi = np.minimum(hi, 20.0)
        if halation:
            g = cv2.GaussianBlur(hi, (0, 0), 9.0 * scale) * 0.6 + cv2.GaussianBlur(hi, (0, 0), 32.0 * scale) * 0.4
            x = x + halation * g * np.array([1.0, 0.45, 0.2], np.float32)
        if glare:
            small = cv2.resize(x, (w // 8, h // 8), interpolation=cv2.INTER_AREA)
            v = cv2.GaussianBlur(small, (0, 0), 28.0)
            x = x + glare * cv2.resize(v, (w, h), interpolation=cv2.INTER_LINEAR)

    # developer: tone curve in linear, then display encode
    y = tone(x, contrast, mid)
    if saturation != 1.0:
        luma = (y * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
        y = np.maximum(luma + (y - luma) * saturation, 0.0)
    if black:
        y = np.maximum(y - black, 0.0) / (1.0 - black)
    d = srgb_encode(y).astype(np.float32)

    # capture sharpening on luma, as every raw developer does
    if sharpen:
        luma = (d * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1)
        lo = cv2.GaussianBlur(luma, (0, 0), 0.9 * scale)
        d = d + (sharpen * (luma - lo))[..., None]

    if grain:
        d = add_grain(d, grain, seed, scale)
    return np.clip(d, 0.0, 1.0)


def add_grain(d, amount=1.4, seed=1, scale=1.0):
    """Luminance-dependent grain in display space, amount in 8-bit codes at mid grey; slightly correlated."""
    rng = np.random.default_rng(seed)
    h, w = d.shape[:2]
    n = rng.standard_normal((h, w, 3), dtype=np.float32)
    n = cv2.GaussianBlur(n, (0, 0), 0.65 * scale)
    n /= n.std()
    c = 0.75 * n + 0.25 * n.mean(-1, keepdims=True)
    luma = d.mean(-1, keepdims=True)
    env = np.sqrt(np.clip(luma, 0.0, 1.0)) * (1.15 - np.clip(luma, 0.0, 1.0)) * 2.0
    return d + (amount / 255.0) * env * c * 1.15


def save_png(path, d):
    u = (np.clip(d, 0.0, 1.0) * 65535.0 + 0.5).astype(np.uint16)
    cv2.imwrite(path, u[..., ::-1])


# --- the print: what the lab does to the whole film, after each shot has its own development --------------------------
_LMS = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
_LAB = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)
_LMSi = np.linalg.inv(_LMS).astype(np.float32)
_LABi = np.linalg.inv(_LAB).astype(np.float32)


def srgb_decode(d):
    d = np.clip(d, 0.0, 1.0)
    return np.where(d <= 0.04045, d / 12.92, ((d + 0.055) / 1.055) ** 2.4).astype(np.float32)


def _oklab(lin):
    lms = np.maximum(lin @ _LMS.T, 0.0)
    return np.cbrt(lms) @ _LAB.T


def _oklab_inv(lab):
    return (((lab @ _LABi.T) ** 3) @ _LMSi.T).astype(np.float32)


def print_look(d, glare=0.010, halation=0.07, chroma_knee=0.15, chroma_max=0.285, hue=0.05, floor=(10.0, 11.5, 14.0), shoulder=0.5):
    """Display-referred picture (sRGB-encoded float) -> the print. In the order of the light:
    - veiling glare: a long-tailed lens PSF, so a dark sky near a bright thing is never empty and bright skies wrap around edges;
    - halation: the warm halo a bright edge gets from light scattered in the sensor stack or film base;
    - dye: chroma rolls off instead of clipping, film's small hue rotations (reds to orange, greens to olive, blues to cyan), highlights desaturate;
    - base: the blacks sit on a soft, slightly cool floor (the original film's blacks measure 10-20 of 255, never 0), with mid-tones untouched."""
    h, w = d.shape[:2]
    x = srgb_decode(d)
    if glare:
        small = cv2.resize(x, (w // 8, h // 8), interpolation=cv2.INTER_AREA)
        v = 0.45 * cv2.GaussianBlur(small, (0, 0), 3.0) + 0.33 * cv2.GaussianBlur(small, (0, 0), 12.0) + 0.22 * cv2.GaussianBlur(small, (0, 0), 44.0)
        x = x + glare * cv2.resize(v, (w, h), interpolation=cv2.INTER_LINEAR)
    if halation:
        hi = np.maximum(x - 0.45, 0.0)
        half = cv2.resize(hi, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        g = 0.65 * cv2.GaussianBlur(half, (0, 0), 3.0) + 0.35 * cv2.GaussianBlur(half, (0, 0), 11.0)
        x = x + halation * cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR) * np.array([1.0, 0.42, 0.14], np.float32)
    lab = _oklab(x)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    H = np.arctan2(b, a)
    if hue:
        # red (near 0.5 rad) to orange, green (near 2.5) to olive, blue (near -1.5) to cyan
        dH = hue * (0.8 * np.exp(-(((H - 0.45) / 0.6) ** 2)) - 0.9 * np.exp(-(((H - 2.5) / 0.7) ** 2)) - 1.0 * np.exp(-(((H + 1.55) / 0.7) ** 2)))
        H = H + dH
    # chroma: linear up to the knee, then an exponential roll-off to the maximum
    k, m = chroma_knee, chroma_max
    C2 = np.where(C < k, C, k + (m - k) * (1.0 - np.exp(-(C - k) / (m - k))))
    # bright colours bleach
    t = np.clip((L - 0.78) / 0.22, 0.0, 1.0)
    C2 = C2 * (1.0 - shoulder * t * t)
    lab = np.stack([L, C2 * np.cos(H), C2 * np.sin(H)], -1)
    y = srgb_encode(np.clip(_oklab_inv(lab), 0.0, 1.0)).astype(np.float32)
    # the film base: a soft floor per channel (a smooth maximum), which leaves mid-tones where they were
    f = np.array(floor, np.float32) / 255.0
    return np.power(np.power(y, 2.2) + np.power(f, 2.2), 1.0 / 2.2)


def film_grain(d, amount=1.0, seed=1):
    """Grain at 1080p, in 8-bit codes: not zero at black (about 1.3), about 2.3 at mid-grey, weaker in highlights; blue a little noisier; slightly correlated."""
    rng = np.random.default_rng(seed)
    h, w = d.shape[:2]
    n = rng.standard_normal((h, w, 3), dtype=np.float32)
    n = cv2.GaussianBlur(n, (0, 0), 0.62)
    n /= n.std()
    c = (0.62 * n + 0.38 * n.mean(-1, keepdims=True)) * np.array([1.0, 0.95, 1.25], np.float32)
    luma = np.clip(d.mean(-1, keepdims=True), 0.0, 1.0)
    env = 1.3 + 2.6 * np.sqrt(luma) * (1.0 - luma) * 1.35
    return d + (amount / 255.0) * env * c
