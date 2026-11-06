"""Dishes and bowls seen from above: paint in flat coordinates, then lay the paint on a turned surface.

Flat coordinates (X, Y): rho = hypot(X, Y) is the arc length along the profile from the centre of the well, theta = atan2(Y, X). So a pattern drawn on the flat keeps its
radial proportions on the wall, and gravity runs along -rho. The camera stands on the -y side, so +y is the far side and the far lip is the arc.

    d = Dish(PROFILE)                               profile from the outer foot, up over the lip, down to the centre (r = 0), so that the inner surface's normal points up
    cam, sag = d.camera(W, EL, DIST, apex=(.5, .36), aperture_mm=.., focus_rho=..)
    X, Y = d.grid(cam, pxcm)                        only the part in the frame
    P = d.surface(X, Y, h)                          h along the normal, cm
    n = d.normal(X, Y)

Composition: the dish rises from the bottom of the frame and shows more than its upper half, its far lip the arc. Tilt 15-25 degrees off square with some depth of field.

A foliate rim (葵口, 荷叶边): Dish(PROFILE, lobes=dict(n=12, a=0.05, b=0.3, p=0.8, rho0=9.4)). From rho0 out to the lip the wall is drawn in between n lobes, by the fraction a of its radius at the
notch, and dips there by b cm. A lobe's crown is on the far side, so the arc's crown is one. Paint in flat coordinates as usual: what follows rho follows the lobes.
"""

import numpy as np

from vessel import Profile, fit_arc, project, view_dir


class Dish:
    def __init__(self, pts, sigma=0.12, ds=0.002, lobes=None):
        self.lobes = lobes
        self.prof = Profile(pts, sigma=sigma, ds=ds)
        self.L = self.prof.L
        i = int(np.argmax(self.prof.z))
        self.s_lip = float(self.prof.s[i])
        self.rho_lip = self.L - self.s_lip  # rho of the highest point of the lip
        self.R = float(self.prof.r[i])

    def at(self, X, Y):
        rho = np.hypot(X, Y)
        th = np.arctan2(Y, X)
        r, z, nr, nz = self.prof.at(np.clip(self.L - rho, 0.0, self.L))
        return rho, th, r, z, nr, nz

    def _lobe(self, rho, th):
        """How far a point is drawn in between the lobes, 0 at a lobe's crown or inside rho0, -1 at a notch on the lip; and the ramp from rho0 to the lip."""
        lb = self.lobes
        t = np.clip((rho - lb["rho0"]) / (self.rho_lip - lb["rho0"]), 0.0, 1.0)
        ramp = t * t * (3.0 - 2.0 * t)
        # the notch is a sharp crease only at the lip; further in it is rounded off, or a crease that has hardly any depth still catches the light
        e2 = (0.05 + 0.6 * (1.0 - ramp)) ** 2
        c2 = np.cos(lb["n"] * (th - np.pi / 2) / 2.0) ** 2
        return (((c2 + e2) / (1.0 + e2)) ** (lb["p"] / 2.0) - 1.0) * ramp, ramp

    def surface(self, X, Y, h=0.0):
        rho, th, r, z, nr, nz = self.at(X, Y)
        rr = r + h * nr
        zz = z + h * nz
        if self.lobes:
            q, ramp = self._lobe(rho, th)
            rr = rr * (1.0 + self.lobes["a"] * q)
            zz = zz + self.lobes["b"] * q * ramp
        return np.stack([rr * np.cos(th), rr * np.sin(th), zz], -1).astype(np.float32)

    def normal(self, X, Y):
        _, th, _, _, nr, nz = self.at(X, Y)
        return np.stack([nr * np.cos(th), nr * np.sin(th), nz], -1).astype(np.float32)

    def polar(self, rho, th):
        """A point on the surface from rho and theta."""
        return self.surface(np.asarray(rho) * np.cos(th), np.asarray(rho) * np.sin(th))

    def _outline(self):
        """Everything that can be the silhouette: the lip and what lies just outside it."""
        rho = np.linspace(self.rho_lip - 0.2, min(self.rho_lip + 1.2, self.L), 12)
        th = np.linspace(0.0, 2 * np.pi, 1440)
        R_, T_ = np.meshgrid(rho, th)
        return self.polar(R_, T_).reshape(-1, 3)

    def camera(self, W, el, dist, apex=(0.5, 0.36), roll=0.0, aperture_mm=None, focus_rho=None, focus_th=np.pi / 2):
        """A camera at elevation el on the -y side, with the far lip's crown on `apex`. Focus on the surface at focus_rho, on the far side by default."""
        fp = None if focus_rho is None else self.polar(np.array(focus_rho, float), focus_th)
        return fit_arc(self._outline(), view_dir(-90.0, el), W, dist, apex=apex, target0=(0.0, self.R * 0.3, 0.0), roll=roll, aperture_mm=aperture_mm, focus_point=fp)

    def grid(self, cam, pxcm, margin=0.05, n=700):
        """Flat coordinates of the part of the dish in the frame: X, Y as float32 grids with +y increasing with the row."""
        rho = np.linspace(0.0, self.L, n)
        th = np.linspace(-np.pi, np.pi, 2 * n)
        R_, T_ = np.meshgrid(rho, th)
        x, y, _ = project(cam, self.polar(R_, T_).reshape(-1, 3))
        x, y = x.reshape(R_.shape), y.reshape(R_.shape)
        ok = (x > -margin) & (x < 1 + margin) & (y > -margin) & (y < 1 + margin)
        fx, fy = R_ * np.cos(T_), R_ * np.sin(T_)
        x0, x1, y0, y1 = fx[ok].min(), fx[ok].max(), fy[ok].min(), fy[ok].max()
        nx, ny = int((x1 - x0) * pxcm), int((y1 - y0) * pxcm)
        print(f"dish grid {nx} x {ny} = {nx * ny / 1e6:.1f} M, rho_lip {self.rho_lip:.2f}, R {self.R:.2f}, L {self.L:.2f}", flush=True)
        return np.meshgrid(x0 + (np.arange(nx, dtype=np.float32) + 0.5) / pxcm, y0 + (np.arange(ny, dtype=np.float32) + 0.5) / pxcm)
