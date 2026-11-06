"""The crack faces of a crackle network as meshes, for a scene (crafts/crackle; used by the Guan glaze card and,
later, shot 6).

A crack is a plane through the glaze under its surface trace (a polyline, mm): from the glaze surface down to the
body, inclined by `tilt_deg` from the surface normal towards one side (`side` +1/-1). Yang et al. 2012 (InTech,
OCT of 10th-13th century Hangzhou celadon shards, figs. 1b-1d) show cracks "basically vertical with a slight
incline"; read off their scale bars: 10, 14, 16 and 19 deg (four cracks), and some at about 30 deg [D].

The plane is cut into cells (du along the trace, dz down); each cell is either open (an air film, the
thin dielectric of pbrt with eta 1/n_glaze) or filled with a deposit (a diffuse surface). The chance that a cell
is filled is cover(depth), which the deposition craft gives (crafts/deposition/deposit.py: None for a piece fresh
from the kiln). Cells are a few tens of um, under a pixel at the card's 31 um/px, so the filled fraction acts as an area
mixture. Runs of open cells in a column are merged into one quad.

    faces(paths, thickness, tilt_deg, sides, cover, rng) -> {"gap": (P, N, T), "deposit": (P, N, T)}

Chips at the mouth (chips(...)): Yang et al. 2012 find a chip at the opening of most cracks in the Hangzhou shards:
"a 'T' structure", the crack ('I') with a chip at its mouth ('-'), "an upside down cone hanging from the surface"
[M, Yang 2012]. Read off their scale bars: about 130 um wide and 150 um deep (fig. 1b), 50-70 um (fig. 1c),
about 30 um (fig. 1a) [D]. A chip is modelled as a lateral crack: an air film that leaves the crack plane at
depth d and curves up to the glaze surface at a distance w from the mouth, z(x) = -d (1 - x/w)^2 (a conchoidal
spall meets the surface at a low angle; the form is ours [A]); its cells take deposit like the crack face.
Where chips are along a crack, how wide, and on which side, vary along it (chip_params).
"""
import math

import numpy as np


def resample(p, step):
    """Polyline -> points every `step` mm along it (linear; the craft's paths are already fine)."""
    p = np.asarray(p, float)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    if s[-1] < 1e-9:
        return p[:1]
    t = np.linspace(0, s[-1], max(2, int(math.ceil(s[-1] / step)) + 1))
    return np.c_[np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])]


def faces(paths, thickness, tilt_deg, sides, cover, rng, du=0.02, dz=0.02, inset=0.001, clip=None):
    """paths: list of (n, 2) polylines (mm). thickness(x, y) -> glaze thickness (mm). tilt_deg, sides: per path.
    cover(depth_mm) -> chance of a deposit, or None (no deposit anywhere). clip: (x0, y0, x1, y1) keep cells whose
    trace point lies inside. Returns dict of (P (m,3), N (m,3), T (k,3)) for 'gap' and 'deposit'."""
    out = {"gap": ([], [], []), "deposit": ([], [], [])}
    base = {"gap": 0, "deposit": 0}

    def quad(kind, a, b, c, d, n):
        P, N, T = out[kind]
        i = base[kind]
        P.extend([a, b, c, d])
        N.extend([n, n, n, n])
        T.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        base[kind] += 4

    for path, tilt, side in zip(paths, tilt_deg, sides):
        q = resample(path, du)
        if len(q) < 2:
            continue
        tng = np.gradient(q, axis=0)
        tng /= np.linalg.norm(tng, axis=1, keepdims=True) + 1e-12
        nrm = np.c_[-tng[:, 1], tng[:, 0]] * side                  # the side the plane leans to
        k = math.tan(math.radians(tilt))
        e = np.asarray(thickness(q[:, 0], q[:, 1]), float)
        for i in range(len(q) - 1):
            if clip is not None:
                x0, y0, x1, y1 = clip
                if not (x0 <= q[i, 0] <= x1 and y0 <= q[i, 1] <= y1 and x0 <= q[i + 1, 0] <= x1 and y0 <= q[i + 1, 1] <= y1):
                    continue
            ee = 0.5 * (e[i] + e[i + 1])
            nz = max(1, int(round((ee - 2 * inset) / dz)))
            zs = -inset - np.linspace(0, ee - 2 * inset, nz + 1)          # z of the cell edges (negative)
            depth_mid = -0.5 * (zs[:-1] + zs[1:])
            filled = (rng.random(nz) < np.array([cover(d) for d in depth_mid])) if cover is not None else np.zeros(nz, bool)
            def pt(j, z):
                return [q[j, 0] + (-z) * k * nrm[j, 0], q[j, 1] + (-z) * k * nrm[j, 1], z]
            # plane normal: tangent x (down + lean)
            dn = np.array([k * nrm[i, 0], k * nrm[i, 1], -1.0])
            n = np.cross(np.r_[tng[i], 0.0], dn)
            n /= np.linalg.norm(n)
            j = 0
            while j < nz:
                kind = "deposit" if filled[j] else "gap"
                m = j
                while m + 1 < nz and filled[m + 1] == filled[j]:
                    m += 1
                za, zb = zs[j], zs[m + 1]
                quad(kind, pt(i, za), pt(i + 1, za), pt(i + 1, zb), pt(i, zb), n)
                j = m + 1
    res = {}
    for kind, (P, N, T) in out.items():
        res[kind] = (np.array(P, float).reshape(-1, 3), np.array(N, float).reshape(-1, 3), np.array(T, int).reshape(-1, 3))
    return res


def _field1d(n, corr_samples, rng):
    from scipy import ndimage as ndi
    k = max(1.0, corr_samples)
    f = ndi.gaussian_filter1d(rng.standard_normal(n + int(8 * k)), k)[int(4 * k):int(4 * k) + n]
    return (f - f.mean()) / (f.std() + 1e-12) if n > 4 else rng.standard_normal(n)


def chips(paths, thickness, tilt_deg, sides, cover, rng, share=0.7, w50_mm=0.06, w_sigma=0.5, depth_per_width=1.0,
          corr_mm=0.5, both_share=0.3, du=0.02, nx=6, inset=0.001, clip=None):
    """Lateral chips along the mouths of the cracks. share: the fraction of the length that has a chip; width
    lognormal (median w50_mm, sigma w_sigma) varying along the crack over corr_mm; the chip leaves the crack plane at
    depth depth_per_width x width; on one side (the side the plane leans away from, or the other) or both
    (both_share). Returns the same dict as faces()."""
    from scipy.special import ndtri
    out = {"gap": ([], [], []), "deposit": ([], [], [])}
    base = {"gap": 0, "deposit": 0}

    def quad(kind, a, b, c, d):
        P, N, T = out[kind]
        n = np.cross(np.subtract(b, a), np.subtract(d, a))
        n = n / (np.linalg.norm(n) + 1e-15)
        i = base[kind]
        P.extend([a, b, c, d])
        N.extend([n, n, n, n])
        T.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        base[kind] += 4

    for path, tilt, side in zip(paths, tilt_deg, sides):
        q = resample(path, du)
        n = len(q)
        if n < 3:
            continue
        tng = np.gradient(q, axis=0)
        tng /= np.linalg.norm(tng, axis=1, keepdims=True) + 1e-12
        nrm = np.c_[-tng[:, 1], tng[:, 0]]
        k = math.tan(math.radians(tilt))
        cs = corr_mm / du
        present = _field1d(n, cs, rng) < ndtri(share) if share < 1 else np.ones(n, bool)
        width = w50_mm * np.exp(w_sigma * _field1d(n, cs, rng))
        which = _field1d(n, 3 * cs, rng)                 # < low: this side; > high: other; between: both
        lo_, hi_ = ndtri((1 - both_share) / 2), ndtri(1 - (1 - both_share) / 2)
        for i in range(n - 1):
            if not (present[i] and present[i + 1]):
                continue
            if clip is not None:
                x0, y0, x1, y1 = clip
                if not (x0 <= q[i, 0] <= x1 and y0 <= q[i, 1] <= y1):
                    continue
            sds = [-side] if which[i] < lo_ else ([side] if which[i] > hi_ else [side, -side])
            for sd in sds:
                xs = np.linspace(0, 1, nx + 1)
                prof = []
                for j in (i, i + 1):
                    w = width[j]
                    d = depth_per_width * w
                    # start on the crack plane at depth d (it leans by k towards `side`)
                    start = q[j] + (d * k * side) * nrm[j]
                    end = q[j] + sd * w * nrm[j]
                    pts = [np.r_[start + (end - start) * x, -inset - (d - inset) * (1 - x) ** 2] for x in xs]
                    prof.append(pts)
                for m in range(nx):
                    za = -0.5 * (prof[0][m][2] + prof[0][m + 1][2])
                    filled = cover is not None and rng.random() < cover(za)
                    quad("deposit" if filled else "gap", prof[0][m], prof[1][m], prof[1][m + 1], prof[0][m + 1])
    res = {}
    for kind, (P, N, T) in out.items():
        res[kind] = (np.array(P, float).reshape(-1, 3), np.array(N, float).reshape(-1, 3), np.array(T, int).reshape(-1, 3))
    return res


def channels(paths, thickness, tilt_deg, sides, cover, rng, w0_mm=0.063, w_deep_mm=None, ramp_mm=0.3, w_sigma=0.3,
             corr_mm=0.3, fill_corr_mm=0.1, top_mm=0.0, du=0.04, inset=0.001, proud=0.001, clip=None):
    """A crack whose walls the burial has corroded, filled with deposit from the mouth down.

    Li et al. 2022 (Microsc. Microanal. 28:1878, SEM sections, Figs. 4-6) [M]: the brown crack channels of an
    excavated Jiaotanxia Guan sherd (GW-1) are about 63 um wide at the surface and widen inside, locally from <70 to
    >400 um, filled with a silicate-rich residue (burial soil, their reading). The channel here: width w0 at the
    mouth (lognormal along the crack, sigma w_sigma, correlation corr_mm), growing linearly to w_deep at ramp_mm
    below the mouth (w_deep None: no widening) [A: the form]. Filled from the mouth down to a depth d drawn per
    column so that the chance of being filled at depth z is cover(z) (a uniform field along the crack, correlated
    over fill_corr_mm, through cover's inverse: deeper where it is high) [A]. The fill is opaque and diffuse (soil:
    clay and silt grains, free paths of microns) as a closed prism per column, its top `proud` above the glaze
    surface so that the mouth is seen in air, not through the glaze; or, with top_mm > 0, from top_mm down only (the
    mouth emptied, e.g. washed: the fill is then seen through the glaze). Above and under the fill the crack stays an
    open air film
    (faces' 'gap'), also where the channel is wide [A: a wide open channel is not modelled].
    Returns {'gap': ..., 'deposit': ...} as faces()."""
    from scipy.special import ndtr
    out = {"gap": ([], [], []), "deposit": ([], [], [])}
    base = {"gap": 0, "deposit": 0}

    def tri_add(kind, pts, tris):
        P, N, T = out[kind]
        pts = np.asarray(pts, float)
        for t in tris:                     # flat faces: each triangle its own vertices and its plane's normal
            a_, b_, c_ = pts[t[0]], pts[t[1]], pts[t[2]]
            n = np.cross(b_ - a_, c_ - a_)
            ln = np.linalg.norm(n)
            if ln < 1e-15:
                continue
            i = base[kind]
            P.extend([a_, b_, c_])
            N.extend([n / ln] * 3)
            T.append((i, i + 1, i + 2))
            base[kind] += 3

    zgrid = np.linspace(0, 3.0, 3001)
    for path, tilt, side in zip(paths, tilt_deg, sides):
        q = resample(path, du)
        n = len(q)
        if n < 2:
            continue
        tng = np.gradient(q, axis=0)
        tng /= np.linalg.norm(tng, axis=1, keepdims=True) + 1e-12
        nrm = np.c_[-tng[:, 1], tng[:, 0]] * side
        k = math.tan(math.radians(tilt))
        e = np.asarray(thickness(q[:, 0], q[:, 1]), float)
        w0 = w0_mm * np.exp(w_sigma * _field1d(n, corr_mm / du, rng))       # w0_mm: the median
        wd = None if w_deep_mm is None else w_deep_mm * np.exp(w_sigma * _field1d(n, corr_mm / du, rng))
        U = ndtr(_field1d(n, fill_corr_mm / du, rng))
        for i in range(n - 1):
            if clip is not None:
                x0, y0, x1, y1 = clip
                if not (x0 <= q[i, 0] <= x1 and y0 <= q[i, 1] <= y1 and x0 <= q[i + 1, 0] <= x1 and y0 <= q[i + 1, 1] <= y1):
                    continue
            ee = 0.5 * (e[i] + e[i + 1])
            # fill depth: the deepest z with cover(z) > U (cover falls with depth)
            if cover is None:
                d = 0.0
            else:
                cz = np.array([cover(z) for z in zgrid[zgrid < ee - 2 * inset]])
                ok = np.nonzero(cz > U[i])[0]
                d = float(zgrid[ok[-1]]) if len(ok) else 0.0
            dn = np.array([k * nrm[i, 0], k * nrm[i, 1], -1.0])
            nf = np.cross(np.r_[tng[i], 0.0], dn)
            nf /= np.linalg.norm(nf)

            def at(j, x, z):                      # x across (mm, along nrm), z <= 0 below the surface
                return [q[j, 0] + ((-min(z, 0)) * k + x) * nrm[j, 0], q[j, 1] + ((-min(z, 0)) * k + x) * nrm[j, 1], z]
            def half(z):                          # half width at depth z >= 0
                if wd is None:
                    return 0.5 * w0[i]
                return 0.5 * (w0[i] + (wd[i] - w0[i]) * min(z, ramp_mm) / ramp_mm)
            if d > top_mm:
                if top_mm <= 0:
                    lv = [(proud, half(0)), (0.0, half(0))]
                else:
                    lv = [(-top_mm, half(top_mm))]
                if wd is not None and top_mm < ramp_mm < d:
                    lv.append((-ramp_mm, half(ramp_mm)))
                lv.append((-d, half(d)))
                m = len(lv)
                # section polygon: left side down, right side up; at both ends of the column
                sec = [(-h, z) for z, h in lv] + [(h, z) for z, h in lv[::-1]]
                K = len(sec)
                pts = [at(i, x, z) for x, z in sec] + [at(i + 1, x, z) for x, z in sec]
                tris = []
                for s in range(K):
                    a_, b_ = s, (s + 1) % K
                    tris += [(a_, b_, K + b_), (a_, K + b_, K + a_)]
                for s in range(1, K - 1):                  # end caps (fans)
                    tris += [(0, s + 1, s), (K, K + s, K + s + 1)]
                tri_add("deposit", pts, tris)
            # the open film above (an emptied mouth) and below the fill
            if d > top_mm:
                spans = [(-inset, -top_mm), (-d, -(ee - inset))] if top_mm > 0 else [(-max(d, inset), -(ee - inset))]
            else:
                spans = [(-inset, -(ee - inset))]
            for zt, zb in spans:
                if zb < zt - 1e-6:
                    pts = [at(i, 0, zt), at(i + 1, 0, zt), at(i + 1, 0, zb), at(i, 0, zb)]
                    P, N, T = out["gap"]
                    j0 = base["gap"]
                    P.extend(pts)
                    N.extend([nf.tolist()] * 4)
                    T.extend([(j0, j0 + 1, j0 + 2), (j0, j0 + 2, j0 + 3)])
                    base["gap"] += 4
    res = {}
    for kind, (P, N, T) in out.items():
        res[kind] = (np.array(P, float).reshape(-1, 3), np.array(N, float).reshape(-1, 3), np.array(T, int).reshape(-1, 3))
    return res


def merge(*dicts):
    """Concatenate several faces()/chips() results kind by kind."""
    res = {}
    for kind in ("gap", "deposit"):
        Ps, Ns, Ts, off = [], [], [], 0
        for d in dicts:
            P, N, T = d[kind]
            if len(T):
                Ps.append(P)
                Ns.append(N)
                Ts.append(T + off)
                off += len(P)
        res[kind] = (np.concatenate(Ps) if Ps else np.zeros((0, 3)), np.concatenate(Ns) if Ns else np.zeros((0, 3)),
                     np.concatenate(Ts) if Ts else np.zeros((0, 3), int))
    return res
