"""Shot 68, tea into water: the numbers shared by the cup, the flow and the compositor. Numpy only; 1 unit = 1 cm; z = 0 is the still water, z up; the cup's axis is the z axis; the camera looks towards +y.

Values, all estimates from general knowledge, none measured unless a comment says so:
hot water n = 1.33, nu = 0.004 cm2/s, surface tension 0.0626 N/m and density 972 kg/m3 at about 80 C give a capillary length of 0.257 cm; a glazed wall's contact angle of 30 degrees.
"""

import numpy as np

N_WATER = 1.33
R0 = 4.2  # inner radius at the rim
DEPTH = 5.2  # rim to the inside of the bottom
SHAPE_P = 2.6
LC = 0.257  # capillary length
CONTACT_DEG = 30.0
H_CONTACT = LC * np.sqrt(2.0 * (1.0 - np.sin(np.radians(CONTACT_DEG))))  # how far the water climbs the wall (1-D Young-Laplace)
STRIP = 0.07  # dry wall between the contact line and the top of the rim
Z_RIM = H_CONTACT + STRIP

W_FRAME = 5.0  # frame width at the rim, cm: sagitta about .08, the original film's median
ELEV = 30.0  # camera above the horizontal, degrees
DIST = 22.0
APERTURE_MM = 5.5
APEX_Y = 0.485  # where the rim's top should land, frame heights from the top


def inner_radius(z):
    """The bowl's inner profile without the wobble: nearly straight just under the rim, closing to the bottom."""
    q = np.clip(Z_RIM - z, 0.0, DEPTH)
    return R0 * (1.0 - (q / DEPTH) ** SHAPE_P) ** (1.0 / SHAPE_P)


def camera():
    """Dict in the form kit.frame_camera makes, target on the axis of view, so that the rim's top lands at APEX_Y."""
    e = np.radians(ELEV)
    view = np.array([0.0, -np.cos(e), np.sin(e)])  # from target to camera
    up = np.array([0.0, np.sin(e), np.cos(e)])
    H = W_FRAME * 9.0 / 16.0
    top = np.array([0.0, R0 + 0.03, Z_RIM])
    target = top - up * (0.5 - APEX_Y) * H
    loc = target + view * DIST
    fp = focus_point()
    return {
        "loc": loc.tolist(),
        "target": target.tolist(),
        "lens_mm": 36.0 * DIST / W_FRAME,
        "roll": 0.0,
        "aperture_mm": APERTURE_MM,
        "focus_distance": float(np.dot(loc - fp, view)),
    }


def focus_point():
    """The focal plane passes through this point, seen directly (in air). Just in front of the rim, so the rim is crisp and the nearer tea softens: chosen by eye."""
    return np.array([0.0, R0 - 0.45, Z_RIM])


def axes(cam):
    loc, tgt = np.array(cam["loc"], float), np.array(cam["target"], float)
    back = loc - tgt
    back /= np.linalg.norm(back)
    up0 = np.array([0.0, 0.0, 1.0])
    right = np.cross(up0, back)
    right /= np.linalg.norm(right)
    up = np.cross(back, right)
    return right, up, back


def meniscus_table():
    """Height of the water above still level against distance from the contact line: the 1-D solution of Young-Laplace, exact for a straight wall. Returns d (cm, rising), h (cm)."""
    h = np.geomspace(H_CONTACT, 0.0015, 800)
    # x(h) = lc * (acosh(2 lc / h) - sqrt(4 - h^2 / lc^2)) up to a constant
    x = LC * (np.arccosh(2.0 * LC / h) - np.sqrt(np.maximum(4.0 - (h / LC) ** 2, 0.0)))
    x = x - x[0]
    return x, h


def meniscus(d):
    x, h = meniscus_table()
    d_ = np.maximum(d, 0.0)
    out = np.exp(np.interp(d_, x, np.log(h)))
    far = d_ > x[-1]
    out = np.where(far, h[-1] * np.exp(-(d_ - x[-1]) / LC), out)
    return out


def cie_xyz(l):
    """Wyman, Sloan, Shirley 2013: multi-lobe fit of the CIE 1931 2-degree observer. l in nm."""
    def g(x, m, s1, s2):
        s = np.where(x < m, s1, s2)
        return np.exp(-0.5 * ((x - m) * s) ** 2)

    X = 1.056 * g(l, 599.8, 0.0264, 0.0323) + 0.362 * g(l, 442.0, 0.0624, 0.0374) - 0.065 * g(l, 501.1, 0.0490, 0.0382)
    Y = 0.821 * g(l, 568.8, 0.0213, 0.0247) + 0.286 * g(l, 530.9, 0.0613, 0.0322)
    Z = 1.217 * g(l, 437.0, 0.0845, 0.0278) + 0.681 * g(l, 459.0, 0.0385, 0.0725)
    return np.stack([X, Y, Z], -1)


XYZ_TO_709 = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])


def band_weights(lams):
    """Weights (bands, 3) so that a spectrally flat filter of 1 gives (1, 1, 1) in linear Rec.709: how a filter's transmission per band turns into a colour multiplier on a white light."""
    x = cie_xyz(np.asarray(lams, float))
    rgb = x @ XYZ_TO_709.T
    return rgb / rgb.sum(0, keepdims=True)
