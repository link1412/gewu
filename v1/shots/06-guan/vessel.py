"""The vase of shot 6 as a surface of revolution: the smoothed measured profile, and the
conformal map the crackle is simulated on.

World frame: Z is the vase's axis (the turntable's), the widest point at Z = 0, the neck up
(+Z). The profile in form.json has z positive towards the foot, in belly radii R_b.

Conformal map of the surface (phi, t), dt = ds / r(s): X = r0 phi, Y = r0 t with r0 = R_b, so
near the widest point a conformal mm is a physical mm; elsewhere lengths scale by r / r0.
Y grows towards the neck.

Profile, in three parts:
- In and around the frame (|z| <= CIRCLE_TO R_b) it is the circle fitted to the measured
  silhouette near the widest point (|z| <= 0.25: max deviation 0.28% R_b, 0.2 mm). The real
  silhouette falls away faster beyond that, by up to 1.2% R_b (0.87 mm) at the frame's edges:
  we regularise it to the circle there, a stylisation, because the original's arc is a clean
  circle (1.2 px at 1920) and the two are compared side by side. The silhouette's own 0.1-0.3%
  bumps (faint ribs or edge noise) would also make the curvature wander.
- Towards the neck: the measured silhouette, smoothed, blended in beyond the frame.
- The photo shows the mounts below z ~ 0.42 and the lip's shadow above the neck, so the lower
  belly and foot ring, and the top of the neck, are SKETCHES (out of the frame).
"""

import json
import math

import numpy as np
from scipy.interpolate import UnivariateSpline

EDGE_NOISE = 0.0015       # silhouette edge noise, in R_b (about 1.7 px at the photo's 1162 px R_b)
CIRCLE_FIT = 0.25         # fit the circle over |z| <= this (as form.py)
CIRCLE_TO = 0.33          # the circle is the profile over |z| <= this; the frame spans +-0.316
BLEND_TO = 0.45           # towards the neck, blended into the smoothed silhouette by here
# SKETCH, out of frame: lower belly to the foot ring, read off the photo by eye
FOOT = {"z_top": 0.69, "r": 0.65, "z_bottom": 0.95}
NECK_TOP = -2.30          # SKETCH: the neck carried straight up to here, then a flat lip


def fit_circle(z, r):
    A = np.c_[2 * z, 2 * r, np.ones_like(z)]
    (zc, rc, k), *_ = np.linalg.lstsq(A, z ** 2 + r ** 2, rcond=None)
    return float(zc), float(rc), float(np.sqrt(k + zc ** 2 + rc ** 2))


def hermite(u, p0, m0, p1, m1):
    return ((2 * u**3 - 3 * u**2 + 1) * p0 + (u**3 - 2 * u**2 + u) * m0
            + (-2 * u**3 + 3 * u**2) * p1 + (u**3 - u**2) * m1)


class Vessel:
    def __init__(self, form_path, n=4000):
        F = json.load(open(form_path))
        self.F = F
        self.Rb = F["scale"]["belly_diameter_mm"] / 2.0
        z, r = np.array(F["profile"], float).T
        order = np.argsort(z)
        z, r = z[order], r[order]
        # the circle near the widest point
        m = np.abs(z) <= CIRCLE_FIT
        zc, rc, Rc = fit_circle(z[m], r[m])
        self.circle = (zc, rc, Rc)
        circ = lambda q: rc + np.sqrt(np.maximum(Rc ** 2 - (q - zc) ** 2, 0))
        dcirc = lambda q: -(q - zc) / np.sqrt(np.maximum(Rc ** 2 - (q - zc) ** 2, 1e-12))
        # the measured silhouette towards the neck, smoothed to the edge noise
        up = z <= -0.2
        spl = UnivariateSpline(z[up], r[up], k=3, s=up.sum() * EDGE_NOISE ** 2)
        za = np.linspace(z[0], CIRCLE_TO, n)
        ra = circ(za)
        b = za < -CIRCLE_TO
        w = np.clip((-CIRCLE_TO - za[b]) / (BLEND_TO - CIRCLE_TO), 0, 1)
        w = w * w * (3 - 2 * w)                                    # smoothstep
        ra[b] = (1 - w) * circ(za[b]) + w * spl(za[b])
        # SKETCH: neck straight up to the lip
        zn = np.linspace(NECK_TOP, za[0], 40, endpoint=False)
        rn = np.full_like(zn, ra[0])
        # SKETCH: from the circle's end to the foot ring (cubic Hermite in r(z): the circle's value
        # and slope, then upright at the ring), then the ring itself
        z0 = CIRCLE_TO
        z1, r1 = FOOT["z_top"], FOOT["r"]
        L = z1 - z0
        u = np.linspace(0, 1, 200)[1:]
        zb = z0 + u * L
        rb = hermite(u, circ(z0), L * dcirc(z0), r1, 0.0)
        zf = np.linspace(z1, FOOT["z_bottom"], 30)[1:]
        rf = np.full_like(zf, r1)
        zz = np.concatenate([zn, za, zb, zf])
        rr = np.concatenate([rn, ra, rb, rf])
        if np.any(rr <= 0):
            raise ValueError("profile reaches the axis")
        # world units (mm): Z up
        self.Z = -zz * self.Rb
        self.R = rr * self.Rb
        # order from the lip down to the foot; arc length s from the widest point, + towards the neck
        ds = np.hypot(np.diff(self.Z), np.diff(self.R))
        s = np.concatenate([[0], np.cumsum(ds)])
        i_eq = int(np.argmax(np.where(np.abs(zz) < 0.3, rr, -1)))
        self.s = s[i_eq] - s          # + towards the neck (the lip end has the largest s)
        self.i_eq = i_eq
        self.r0 = self.Rb
        # conformal t(s) = integral ds / r, zero at the widest point, + towards the neck
        inv = 1.0 / self.R
        t = np.concatenate([[0], np.cumsum(0.5 * (inv[1:] + inv[:-1]) * ds)])
        self.t = t[i_eq] - t
        # increasing-t order for interpolation
        o = np.argsort(self.t)
        self._t, self._R, self._Z, self._s = self.t[o], self.R[o], self.Z[o], self.s[o]
        # tangent along the profile (towards +t, i.e. towards the neck): (dR, dZ) / ds
        dR = np.gradient(self._R, self._s)
        dZ = np.gradient(self._Z, self._s)
        nrm = np.hypot(dR, dZ)
        self._tR, self._tZ = dR / nrm, dZ / nrm

    # --- the map ----------------------------------------------------------------------
    def profile_at(self, Y):
        """(r, Z, tangent_R, tangent_Z) at conformal Y (mm), interpolated along the profile."""
        t = np.asarray(Y, float) / self.r0
        if np.any(t < self._t[0]) or np.any(t > self._t[-1]):
            raise ValueError("conformal Y outside the vessel")
        f = lambda a: np.interp(t, self._t, a)
        tR, tZ = f(self._tR), f(self._tZ)
        n = np.hypot(tR, tZ)
        return f(self._R), f(self._Z), tR / n, tZ / n

    def scale(self, Y):
        """Physical mm per conformal mm at conformal Y: r / r0."""
        return self.profile_at(Y)[0] / self.r0

    def point(self, X, Y, depth=0.0):
        """World point (mm) at conformal (X, Y), `depth` mm inside the outer surface, and the
        outward normal there."""
        r, Z, tR, tZ = self.profile_at(Y)
        phi = np.asarray(X, float) / self.r0
        c, s_ = np.cos(phi), np.sin(phi)
        # outward normal in the meridian plane: tangent (tR, tZ) turned by -90 deg -> (tZ, -tR)
        nR, nZ = tZ, -tR
        nR, nZ = np.where(nR < 0, -nR, nR), np.where(nR < 0, -nZ, nZ)  # point away from the axis
        P = np.stack([(r - depth * nR) * c, (r - depth * nR) * s_, Z - depth * nZ], -1)
        N = np.stack([nR * c, nR * s_, nZ], -1)
        return P, N

    def Y_of_Z(self, Zw):
        """Conformal Y at world height Z on the belly (near the widest point, where Z is monotonic)."""
        sel = np.abs(self._Z) < 0.8 * self.Rb
        Zs, ts = self._Z[sel], self._t[sel]
        o = np.argsort(Zs)
        return np.interp(Zw, Zs[o], ts[o]) * self.r0

    def meridian_curvature_radius(self, Y=0.0, h=1.0):
        """Radius of curvature of the profile at conformal Y (finite differences, mm)."""
        rs, Zs = [], []
        for y in (Y - h, Y, Y + h):
            r, Z, _, _ = self.profile_at(y)
            rs.append(float(r)); Zs.append(float(Z))
        (x1, y1), (x2, y2), (x3, y3) = zip(rs, Zs)
        a = math.dist((x1, y1), (x2, y2)); b = math.dist((x2, y2), (x3, y3)); c = math.dist((x1, y1), (x3, y3))
        area2 = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))   # twice the triangle's area
        return a * b * c / max(2 * area2, 1e-12)


if __name__ == "__main__":
    import sys
    v = Vessel(sys.argv[1] if len(sys.argv) > 1 else "shots/06-guan/form.json")
    print(f"R_b = {v.Rb} mm; profile {len(v.R)} points; t from {v._t[0]:.3f} to {v._t[-1]:.3f}")
    for Y in (-40, -20, 0, 20, 40):
        r, Z, _, _ = v.profile_at(Y)
        print(f"  Y {Y:+4d} mm: r {float(r):6.2f} mm, Z {float(Z):+7.2f} mm, scale {float(r) / v.r0:.4f}, "
              f"R_meridian {v.meridian_curvature_radius(Y):6.1f} mm")
