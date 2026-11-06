"""A plane-parallel glaze on a body, by Monte Carlo: the independent reference for our renderers' media
(docs/slab.md), and later the fast model a glaze's parameters are fitted with.

    python3 -I tools/slab.py check                        # the closed-form checks (tests/slab/ runs them too)
    python3 -I tools/slab.py albedo --n 1.5 --layer 1.2,2.5,0.03,0.7 --body 0.12 --mu 1

The slab is laterally infinite: air above a dielectric surface (refractive index n; smooth, or rough with GGX
alpha as pbrt-v4's rough DielectricBxDF: microfacet normals sampled from the visible normals, Fresnel at the
microfacet, Smith height-correlated shadowing, single scattering on the microsurface), then one or more
homogeneous layers (thickness in mm, sigma_s and sigma_a in 1/mm, Henyey-Greenstein g, or a mixture of HG lobes
for a medium of several kinds of scatterer: ((share of sigma_s, g), ...)), all of index n, on an
opaque Lambertian body of albedo rho. Light comes from one direction (cosine mu0 to the normal, azimuth phi0 of
the direction it comes from). The method is
MCML's (Wang, Jacques & Zheng 1995): photon packets with implicit capture (the weight times the single-scattering
albedo at each interaction), a free path sampled afresh at every boundary (exact for piecewise-constant media),
partial reflection at the top (the escaping part w(1-F) tallied, the reflected part w F carried on, so no photon
is lost to a coin flip there), Russian roulette below a weight of 1e-4.

What comes out is the slab's reflectance for that incidence, split into the specular part (the surface's Fresnel
reflection, exact) and the part that went in and came out; with the directions the escaping light leaves in
(binned, and summed on any set of distant lights given as quads). By reciprocity, a camera looking along mu0
at the slab under a uniform sky of radiance L sees L times this reflectance, and under area lights it sees the sum,
over the lights, of each light's radiance times the escaping weight that leaves towards it. That is how a render
is checked against it (tests/slab/).

Units: millimetres. z is up; the surface is z = 0, the body z = -sum(thickness).
"""

import argparse
import json
import math
import sys

import numpy as np


# --- optics ---------------------------------------------------------------------------------------
def fresnel(cos_i, eta):
    """Unpolarised Fresnel reflectance for light hitting an interface from the side of index 1, the other side
    having relative index eta (n_other / n_this). cos_i > 0. Total internal reflection gives 1."""
    cos_i = np.clip(cos_i, 0.0, 1.0)
    sin_t2 = (1.0 - cos_i * cos_i) / (eta * eta)
    tir = sin_t2 >= 1.0
    cos_t = np.sqrt(np.maximum(0.0, 1.0 - sin_t2))
    rs = (cos_i - eta * cos_t) / (cos_i + eta * cos_t)
    rp = (eta * cos_i - cos_t) / (eta * cos_i + cos_t)
    return np.where(tir, 1.0, 0.5 * (rs * rs + rp * rp))


def hg_cos(g, xi):
    """cos(theta) between the old and the new direction, Henyey-Greenstein with asymmetry g (> 0 forward)."""
    if abs(g) < 1e-6:
        return 1.0 - 2.0 * xi
    s = (1.0 - g * g) / (1.0 - g + 2.0 * g * xi)
    return np.clip((1.0 + g * g - s * s) / (2.0 * g), -1.0, 1.0)


def turn(ux, uy, uz, cos_t, phi):
    """The direction at polar angle acos(cos_t), azimuth phi about (ux, uy, uz) (MCML's formulas)."""
    sin_t = np.sqrt(np.maximum(0.0, 1.0 - cos_t * cos_t))
    cp, sp = np.cos(phi), np.sin(phi)
    near = np.abs(uz) > 0.99999
    tmp = np.sqrt(np.maximum(1e-300, 1.0 - uz * uz))
    nx = np.where(near, sin_t * cp, sin_t * (ux * uz * cp - uy * sp) / tmp + ux * cos_t)
    ny = np.where(near, sin_t * sp, sin_t * (uy * uz * cp + ux * sp) / tmp + uy * cos_t)
    nz = np.where(near, np.sign(uz) * cos_t, -sin_t * cp * tmp + uz * cos_t)
    r = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx * r, ny * r, nz * r


def ggx_lambda(cz, alpha):
    """Smith's Lambda of the GGX (Trowbridge-Reitz) distribution, isotropic alpha, for a direction at cosine cz to
    the macro normal (either side)."""
    c2 = np.clip(cz * cz, 1e-12, 1.0)
    return 0.5 * (np.sqrt(1.0 + alpha * alpha * (1.0 - c2) / c2) - 1.0)


def ggx_visible_normal(wx, wy, wz, alpha, u1, u2):
    """A microfacet normal sampled from the GGX normals visible from w (unit, wz > 0, macro normal +z): Heitz 2018,
    line for line pbrt-v4's TrowbridgeReitzDistribution::Sample_wm."""
    hx, hy, hz = alpha * wx, alpha * wy, wz
    r = 1.0 / np.sqrt(hx * hx + hy * hy + hz * hz)
    hx, hy, hz = hx * r, hy * r, hz * r
    lt = np.maximum(np.sqrt(hx * hx + hy * hy), 1e-300)
    pole = hz >= 0.99999
    t1x = np.where(pole, 1.0, -hy / lt)
    t1y = np.where(pole, 0.0, hx / lt)
    t2x, t2y, t2z = -hz * t1y, hz * t1x, hx * t1y - hy * t1x
    rr, th = np.sqrt(u1), 2 * np.pi * u2
    px, py = rr * np.cos(th), rr * np.sin(th)
    h = np.sqrt(np.maximum(0.0, 1.0 - px * px))
    t = 0.5 * (1.0 + hz)
    py = (1.0 - t) * h + t * py
    pz = np.sqrt(np.maximum(0.0, 1.0 - px * px - py * py))
    nx = px * t1x + py * t2x + pz * hx
    ny = px * t1y + py * t2y + pz * hy
    nz = py * t2z + pz * hz
    mx, my, mz = alpha * nx, alpha * ny, np.maximum(1e-6, nz)
    r = 1.0 / np.sqrt(mx * mx + my * my + mz * mz)
    return mx * r, my * r, mz * r


def rough_surface(dx, dy, dz, eta, alpha, u1, u2):
    """A photon travelling along d meets the rough surface z = 0 from either side; eta is the other side's index
    over this side's. Photon (importance) transport through pbrt-v4's rough DielectricBxDF: m from the normals
    visible from the photon's side, Fresnel F at m, both branches kept, each with its weight factor G2/G1 (zero
    when the branch would leave on the wrong side of the macro surface: the microsurface's single-scattering loss).
    Returns ((rx, ry, rz), wr), ((tx, ty, tz), wt): the reflected and the transmitted direction, in the slab's
    frame, and the factor each weight takes."""
    sg = np.where(dz < 0, 1.0, -1.0)                    # the frame with the photon's side up is z -> sg z
    ox, oy, oz = -dx, -dy, np.abs(dz)                   # wo: back towards where the photon came from
    mx, my, mz = ggx_visible_normal(ox, oy, oz, alpha, u1, u2)
    c = np.clip(ox * mx + oy * my + oz * mz, 0.0, 1.0)
    F = fresnel(c, eta)
    lo = 1.0 + ggx_lambda(oz, alpha)                    # 1 / G1(wo)
    rx, ry, rz = 2 * c * mx - ox, 2 * c * my - oy, 2 * c * mz - oz
    wr = np.where(rz > 0, F * lo / (lo + ggx_lambda(rz, alpha)), 0.0)
    s2 = (1.0 - c * c) / (eta * eta)
    k = c / eta - np.sqrt(np.maximum(0.0, 1.0 - s2))
    tx, ty, tz = k * mx - ox / eta, k * my - oy / eta, k * mz - oz / eta
    wt = np.where((s2 < 1.0) & (tz < 0), (1.0 - F) * lo / (lo + ggx_lambda(tz, alpha)), 0.0)
    return ((rx, ry, sg * rz), wr), ((tx, ty, sg * tz), wt)


def film_reflects(cos_i, below, films, rng):
    """Photons at an internal boundary meet the film under layer `below`, if there is one: True for those it
    reflects, with pbrt's thin-slab reflectance at |cos_i| (a coin flip: no weight change)."""
    refl = np.zeros(len(below), bool)
    for k, v in films.items():
        j = np.nonzero(below == k)[0]
        if not len(j):
            continue
        if isinstance(v, tuple):                        # ("R", r): a constant reflectance (for the probes)
            R = np.full(len(j), float(v[1]))
        else:
            F = fresnel(np.abs(cos_i[j]), float(v))
            R = np.where(F < 1, F + (1 - F) ** 2 * F / np.maximum(1 - F * F, 1e-300), 1.0)
        refl[j] = rng.random(len(j)) < R
    return refl


# --- the run --------------------------------------------------------------------------------------
def run(n, layers, rho, mu0, phi0=0.0, nphot=1_000_000, seed=0, lights=(), bins=(45, 36), box=None,
        batch=250_000, max_events=100_000, max_vertices=None, light_scale=None, alpha=0.0, record=False, films=None):
    """layers: [(thickness_mm, sigma_s, sigma_a, g), ...] top to bottom. lights: [(name, P4x3 corners, in mm,
    as seen from the entry point at the origin), ...]. box: (half_x, half_y) in mm, lateral bounds beyond which a
    photon is dropped (a finite tile's leak, as an estimate), or None. max_vertices: a renderer's path-length limit
    (pbrt's maxdepth), counting the entry, every scattering, every body bounce and every hit on the surface from
    inside as one vertex each; the light is reached after the last one. light_scale: {name: radiance} to sum the
    lights into one pixel value ("pixel", with its standard error "pixel_se"; the specular reflection counts when
    it reaches a light, "lights_specular"). alpha: the surface's GGX alpha (0: smooth). record: also return every
    escape ("events": weight, path length in each layer, body bounces, the light it reaches or -1), so that other
    absorptions and body albedos can be applied afterwards: run with sigma_a = 0 and rho = 1, then a photon's
    weight is w exp(-sum_i sigma_a,i L_i) rho^k (events_apply). films: {i: eta} a thin film (pbrt's
    ThinDielectricBxDF: R = F + T^2 F / (1 - F^2) at the film's relative index eta, specular, no displacement) on
    the boundary below layer i, reflected or passed by a coin flip; each meeting is a vertex; ("R", r) instead of
    eta: a constant reflectance r. Returns a dict (see the module docstring)."""
    rng = np.random.default_rng(seed)
    mix = [tuple((float(a), float(b)) for a, b in g) if np.ndim(g) else ((1.0, float(g)),) for *_, g in layers]
    for k, m in enumerate(mix):
        if abs(sum(a for a, _ in m) - 1.0) > 1e-9:
            raise SystemExit(f"slab.run: layer {k}'s phase-function shares add up to {sum(a for a, _ in m)}, not 1")
    L = [(float(t), float(ss), float(sa), sum(a * b for a, b in m)) for (t, ss, sa, _), m in zip(layers, mix)]
    nl = len(L)
    tops = np.concatenate([[0.0], -np.cumsum([l[0] for l in L])])        # boundaries, z of layer i: tops[i] .. tops[i+1]
    st = np.array([l[1] + l[2] for l in L])
    alb = np.array([l[1] / (l[1] + l[2]) if l[1] + l[2] > 0 else 0.0 for l in L])
    rough = alpha > 0
    sin0 = math.sqrt(max(0.0, 1.0 - mu0 * mu0))
    din = np.array([-sin0 * math.cos(phi0), -sin0 * math.sin(phi0), -mu0])   # the incoming light's direction
    R0 = float(fresnel(np.array(mu0), n))
    sin_t = sin0 / n
    d0 = np.array([din[0] / n, din[1] / n, -math.sqrt(1.0 - sin_t * sin_t)])  # refracted (smooth)
    nb_t, nb_p = bins
    hist = np.zeros((nb_t, nb_p))                       # escaping weight by (cos theta, phi) in air, equal-mu bins
    quads = [(name, np.asarray(P, float)) for name, P in lights]
    light_w = {name: 0.0 for name, _ in quads}
    spec_w = {name: 0.0 for name, _ in quads}
    if not rough:                                       # the mirror direction, from the entry point
        for name, P in quads:
            if hits_quad(np.zeros((1, 3)), np.array([[din[0], din[1], mu0]]), P)[0]:
                spec_w[name] = R0 * nphot
    pix_w = pix_w2 = 0.0
    out_w = out_w2 = 0.0                                # per-photon sums and sums of squares, for the standard error
    sp_w = sp_w2 = 0.0
    lost_box = 0.0
    absorbed_body = 0.0
    events_max = 0
    rec = {"w": [], "L": [], "k": [], "light": []} if record else None
    done = 0
    while done < nphot:
        m = min(batch, nphot - done)
        x = np.zeros(m); y = np.zeros(m); z = np.zeros(m)
        per = np.zeros(m)                               # each photon's escaped weight (for the error estimate)
        perpix = np.zeros(m)                            # each photon's pixel value (light_scale)
        if rough:
            ((rx, ry, rz), wr), ((ux, uy, uz), w) = rough_surface(np.full(m, din[0]), np.full(m, din[1]),
                                                                  np.full(m, din[2]), n, alpha,
                                                                  rng.random(m), rng.random(m))
            sp_w += wr.sum(); sp_w2 += (wr * wr).sum()
            for name, P in quads:
                h = hits_quad(np.zeros((m, 3)), np.stack([rx, ry, rz], 1), P)
                spec_w[name] += wr[h].sum()
                if light_scale:
                    perpix[h] += wr[h] * light_scale[name]
        else:
            ux = np.full(m, d0[0]); uy = np.full(m, d0[1]); uz = np.full(m, d0[2])
            w = np.full(m, 1.0 - R0)
            if light_scale:
                perpix += sum(v / nphot * light_scale[k] for k, v in spec_w.items())
        lay = np.zeros(m, np.int64)
        nv = np.ones(m, np.int64)                       # vertices so far (the entry is the first)
        pid = np.arange(m)
        Lp = np.zeros((m, nl)) if record else None      # path length in each layer
        kb = np.zeros(m, np.int64) if record else None  # body bounces
        live = w > 0
        x, y, z, ux, uy, uz, w, lay, nv, pid = (a[live] for a in (x, y, z, ux, uy, uz, w, lay, nv, pid))
        if record:
            Lp, kb = Lp[live], kb[live]
        ev = 0
        while len(w) and ev < max_events:
            ev += 1
            s = -np.log(1.0 - rng.random(len(w))) / np.maximum(st[lay], 1e-300)
            s = np.where(st[lay] > 0, s, np.inf)
            zt, zb = tops[lay], tops[lay + 1]
            down = uz < 0
            dist = np.where(down, (z - zb) / np.maximum(-uz, 1e-300), (zt - z) / np.maximum(uz, 1e-300))
            dist = np.where(uz == 0, np.inf, dist)
            hit = s >= dist
            step = np.where(hit, dist, s)
            x = x + ux * step; y = y + uy * step; z = z + uz * step
            if record:
                Lp[np.arange(len(w)), lay] += step
            # interactions: implicit capture, then a new direction
            inter = ~hit
            if inter.any():
                i = np.nonzero(inter)[0]
                nv[i] += 1
                w[i] *= alb[lay[i]]
                ct = np.empty(len(i))
                for k in np.unique(lay[i]):
                    j = np.nonzero(lay[i] == k)[0]
                    if len(mix[k]) == 1:
                        ct[j] = hg_cos(mix[k][0][1], rng.random(len(j)))
                    else:                                       # pick the lobe by its share of sigma_s
                        c = np.searchsorted(np.cumsum([a for a, _ in mix[k]])[:-1], rng.random(len(j)), side="right")
                        for q, (_, gq) in enumerate(mix[k]):
                            jq = j[c == q]
                            ct[jq] = hg_cos(gq, rng.random(len(jq)))
                ux[i], uy[i], uz[i] = turn(ux[i], uy[i], uz[i], ct, 2 * np.pi * rng.random(len(i)))
            # boundaries
            if hit.any():
                i = np.nonzero(hit)[0]
                up = uz[i] > 0
                # top of the slab
                t = i[up & (lay[i] == 0)]
                if len(t):
                    z[t] = 0.0
                    nv[t] += 1
                    if rough:
                        ((rx, ry, rz), wr), ((ax, ay, az), wt) = rough_surface(ux[t], uy[t], uz[t], 1.0 / n, alpha,
                                                                              rng.random(len(t)), rng.random(len(t)))
                        esc = w[t] * wt
                    else:
                        F = fresnel(uz[t], 1.0 / n)
                        esc = w[t] * (1.0 - F)
                        ax, ay = n * ux[t], n * uy[t]
                        az = np.sqrt(np.maximum(0.0, 1.0 - ax * ax - ay * ay))
                    if max_vertices is not None:
                        esc = np.where(nv[t] <= max_vertices, esc, 0.0)
                    ok = esc > 0
                    if ok.any():
                        te, ee, ex, ey, ez = t[ok], esc[ok], ax[ok], ay[ok], az[ok]
                        out_w += ee.sum()
                        np.add.at(per, pid[te], ee)
                        it = np.minimum((ez * nb_t).astype(int), nb_t - 1)
                        ip = np.minimum(((np.arctan2(ey, ex) % (2 * np.pi)) / (2 * np.pi) * nb_p).astype(int), nb_p - 1)
                        np.add.at(hist, (it, ip), ee)
                        which = np.full(len(te), -1)
                        for li, (name, P) in enumerate(quads):
                            h = hits_quad(np.stack([x[te], y[te], np.zeros(len(te))], 1), np.stack([ex, ey, ez], 1), P)
                            light_w[name] += ee[h].sum()
                            which[h & (which < 0)] = li
                            if light_scale:
                                np.add.at(perpix, pid[te[h]], ee[h] * light_scale[name])
                        if record:
                            rec["w"].append(ee); rec["L"].append(Lp[te].copy()); rec["k"].append(kb[te].copy())
                            rec["light"].append(which)
                    if rough:
                        w[t] *= wr
                        ux[t], uy[t], uz[t] = rx, ry, rz
                    else:
                        w[t] *= F
                        uz[t] = -uz[t]
                # internal boundaries going up
                t = i[up & (lay[i] > 0)]
                if films:                                      # a film on that boundary: back down, or through
                    nv[t] += np.isin(lay[t] - 1, list(films))      # a vertex, as in pbrt
                    r = film_reflects(uz[t], lay[t] - 1, films, rng)
                    tr = t[r]
                    uz[tr] = -uz[tr]
                    z[tr] = tops[lay[tr]]
                    t = t[~r]
                lay[t] -= 1
                z[t] = tops[lay[t] + 1]
                # going down: to the next layer, or the body
                dn = i[~up]
                last = lay[dn] == nl - 1
                b = dn[last]
                if len(b):
                    z[b] = tops[-1]
                    nv[b] += 1
                    absorbed_body += (w[b] * (1.0 - rho)).sum()
                    w[b] *= rho
                    if record:
                        kb[b] += 1
                    c = np.sqrt(rng.random(len(b)))
                    ph = 2 * np.pi * rng.random(len(b))
                    sn = np.sqrt(np.maximum(0.0, 1.0 - c * c))
                    ux[b], uy[b], uz[b] = sn * np.cos(ph), sn * np.sin(ph), c
                o = dn[~last]
                if films:
                    nv[o] += np.isin(lay[o], list(films))
                    r = film_reflects(uz[o], lay[o], films, rng)
                    orf = o[r]
                    uz[orf] = -uz[orf]
                    z[orf] = tops[lay[orf] + 1]
                    o = o[~r]
                lay[o] += 1
                z[o] = tops[lay[o]]
            # a finite tile's lateral leak
            if box is not None:
                out = (np.abs(x) > box[0]) | (np.abs(y) > box[1])
                lost_box += w[out].sum()
                w[out] = 0.0
            if max_vertices is not None:
                w[nv >= max_vertices] = 0.0                     # no direction is sampled at the last vertex
            # roulette
            small = (w < 1e-4) & (w > 0)
            if small.any():
                i = np.nonzero(small)[0]
                lucky = rng.random(len(i)) < 0.1
                w[i[lucky]] *= 10.0
                w[i[~lucky]] = 0.0
            keep = w > 0
            if not keep.all():
                x, y, z, ux, uy, uz, w, lay, nv, pid = (a[keep] for a in (x, y, z, ux, uy, uz, w, lay, nv, pid))
                if record:
                    Lp, kb = Lp[keep], kb[keep]
        if len(w):
            raise SystemExit(f"slab.run: {len(w)} photons still alive after {max_events} events")
        events_max = max(events_max, ev)
        out_w2 += (per * per).sum()
        pix_w += perpix.sum()
        pix_w2 += (perpix * perpix).sum()
        done += m
    mean = out_w / nphot
    se = math.sqrt(max(0.0, out_w2 / nphot - mean * mean) / nphot)
    pm = pix_w / nphot
    pse = math.sqrt(max(0.0, pix_w2 / nphot - pm * pm) / nphot)
    if rough:
        Rs = sp_w / nphot
        Rs_se = math.sqrt(max(0.0, sp_w2 / nphot - Rs * Rs) / nphot)
    else:
        Rs, Rs_se = R0, 0.0
    res = {"R_specular": Rs, "R_specular_se": Rs_se, "R_diffuse": mean, "R_diffuse_se": se, "R_total": Rs + mean,
           "pixel": pm, "pixel_se": pse, "lights": {k: v / nphot for k, v in light_w.items()},
           "lights_specular": {k: v / nphot for k, v in spec_w.items()}, "hist": hist / nphot,
           "lost_box": lost_box / nphot, "absorbed_body": absorbed_body / nphot, "events_max": events_max,
           "nphot": nphot}
    if record:
        cat = lambda v, empty: np.concatenate(v) if v else empty
        res["events"] = {"w": cat(rec["w"], np.zeros(0)), "L": cat(rec["L"], np.zeros((0, nl))),
                         "k": cat(rec["k"], np.zeros(0, np.int64)), "light": cat(rec["light"], np.zeros(0, np.int64)),
                         "lights": [name for name, _ in quads]}
    return res


def events_apply(events, nphot, sigma_a, rho, light_scale=None):
    """A recorded run (record=True, sigma_a = 0, rho = 1) under other absorptions: sigma_a [n_layers] or
    [n_layers, n_lambda] in 1/mm, rho a number or [n_lambda]. Returns the diffuse reflectance (per wavelength) and,
    with light_scale {name: radiance}, the pixel's diffuse part."""
    sa = np.asarray(sigma_a, float)
    sa = sa[:, None] if sa.ndim == 1 else sa
    rho = np.atleast_1d(np.asarray(rho, float))
    att = np.exp(-events["L"] @ sa) * rho[None, :] ** events["k"][:, None] * events["w"][:, None]
    R = att.sum(0) / nphot
    if light_scale is None:
        return R
    sc = np.array([light_scale.get(name, 0.0) for name in events["lights"]] + [0.0])
    return R, (att * sc[events["light"]][:, None]).sum(0) / nphot


def hits_quad(o, d, P):
    """Rays o + t d (t > 0) against the quad P (4 corners p00 p10 p01 p11, a planar bilinear patch). Boolean."""
    p00, p10, p01, p11 = P
    nrm = np.cross(p10 - p00, p01 - p00)
    den = d @ nrm
    t = ((p00 - o) @ nrm) / np.where(np.abs(den) < 1e-300, 1e-300, den)
    q = o + t[:, None] * d
    # inside test: the quad's two triangles (p00 p10 p11) and (p00 p11 p01)
    def inside(a, b, c):
        n1 = np.cross(b - a, q - a) @ nrm
        n2 = np.cross(c - b, q - b) @ nrm
        n3 = np.cross(a - c, q - c) @ nrm
        return ((n1 >= 0) & (n2 >= 0) & (n3 >= 0)) | ((n1 <= 0) & (n2 <= 0) & (n3 <= 0))
    return (t > 0) & (inside(p00, p10, p11) | inside(p00, p11, p01))


# --- closed forms, for the checks -----------------------------------------------------------------
def no_scatter(n, d, sigma_a, rho, mu0, nq=20000):
    """Reflectance with no scattering: the Fresnel reflection, plus the body seen through an absorbing layer with
    all the round trips between the body and the surface (one-dimensional integrals over the body's cosine lobe)."""
    R0 = float(fresnel(np.array(mu0), n))
    mu1 = math.sqrt(1.0 - (1.0 - mu0 * mu0) / (n * n))
    t1 = math.exp(-sigma_a * d / mu1)
    mu = (np.arange(nq) + 0.5) / nq                                  # midpoint rule in mu (upward, inside)
    Fi = fresnel(mu, 1.0 / n)
    E = np.sum(2 * mu * np.exp(-sigma_a * d / mu) * (1 - Fi)) / nq   # escapes after leaving the body once
    B = np.sum(2 * mu * np.exp(-2 * sigma_a * d / mu) * Fi) / nq     # comes back to the body
    return R0 + (1 - R0) * t1 * rho * E / (1 - rho * B)


def chandrasekhar_H(omega, nq=400, iters=2000):
    """H(mu) for isotropic scattering with single-scattering albedo omega, by iterating
    1/H(mu) = sqrt(1 - omega) + (omega/2) int_0^1 mu' H(mu') / (mu + mu') dmu' (the form that converges fast)."""
    x, wq = np.polynomial.legendre.leggauss(nq)
    mu = 0.5 * (x + 1); wq = 0.5 * wq
    H = np.ones(nq)
    for _ in range(iters):
        Hn = 1.0 / (math.sqrt(1 - omega) + 0.5 * omega * ((mu[None, :] * H[None, :] * wq[None, :]) /
                                                         (mu[:, None] + mu[None, :])).sum(1))
        if np.max(np.abs(Hn - H)) < 1e-13:
            H = Hn
            break
        H = Hn
    def at(m):
        return 1.0 / (math.sqrt(1 - omega) + 0.5 * omega * np.sum(mu * H * wq / (m + mu)))
    return at


def semi_infinite_isotropic(omega, mu0):
    """Plane albedo of a semi-infinite, index-matched, isotropically scattering medium: 1 - H(mu0) sqrt(1 - omega)
    (Chandrasekhar 1960, Radiative Transfer, ch. IV)."""
    return 1.0 - chandrasekhar_H(omega)(mu0) * math.sqrt(1.0 - omega)


def check(nphot=400_000):
    """The closed-form checks. Returns a list of (name, mc, se, exact)."""
    res = []
    for (n, d, sa, rho, mu0) in [(1.5, 1.2, 0.3, 0.6, 1.0), (1.5, 0.5, 0.0, 0.8, 0.5), (1.0, 1.0, 0.5, 0.5, 0.7),
                                 (1.5, 1.2, 0.03, 0.12, 1.0)]:
        r = run(n, [(d, 0.0, sa, 0.0)], rho, mu0, nphot=nphot, seed=1)
        res.append((f"no scattering n={n} d={d} sa={sa} rho={rho} mu0={mu0}", r["R_total"], r["R_diffuse_se"],
                    no_scatter(n, d, sa, rho, mu0)))
    for omega, mu0 in [(0.9, 1.0), (0.99, 0.5), (0.5, 0.8)]:
        r = run(1.0, [(1e6, omega, 1 - omega, 0.0)], 0.0, mu0, nphot=nphot, seed=2)
        res.append((f"semi-infinite isotropic omega={omega} mu0={mu0}", r["R_total"], r["R_diffuse_se"],
                    semi_infinite_isotropic(omega, mu0)))
    # the HG sampler's mean cosine is g
    rng = np.random.default_rng(3)
    for g in (0.7, -0.3):
        c = hg_cos(g, rng.random(2_000_000))
        res.append((f"HG mean cosine g={g}", float(c.mean()), float(c.std() / math.sqrt(len(c))), g))
    # GGX by quadrature over the projected-area measure D cos(theta_m) dw = du dphi / 2 pi, u = t / (alpha^2 + t),
    # t = tan^2(theta_m), with u = 1 - v^2 (du = 2 v dv) to take out the 1/cos(theta_m) singularity at u -> 1:
    # Smith's 1 + Lambda(wo) = int (wo.m)+ D dw / cos(theta_o), and the visible-normal pdf
    # G1(wo) (wo.m)+ D / cos(theta_o) gives the mean of cos(theta_m) and the share with t < alpha^2
    for alpha, mu in ((0.0307, 1.0), (0.3, 0.6), (0.6, 0.2)):
        so = math.sqrt(1 - mu * mu)
        nq = 4000
        v = (np.arange(nq) + 0.5) / nq
        u, du = 1 - v * v, 2 * v
        ph = 2 * np.pi * (np.arange(nq) + 0.5) / nq
        t = alpha * alpha * u / (1 - u)
        cm = 1 / np.sqrt(1 + t)
        sm = np.sqrt(t) * cm
        dot = np.maximum(0.0, so * sm[:, None] * np.cos(ph)[None, :] + mu * cm[:, None]) * du[:, None]
        q = (dot / cm[:, None]).mean()                         # int (wo.m)+ D dw
        lam = float(ggx_lambda(np.array(mu), alpha))
        res.append((f"GGX Lambda alpha={alpha} mu={mu} (quadrature)", 1 + lam, 1e-5, q / mu))
        G1 = 1 / (1 + lam)
        k = 1_000_000
        mx, my, mz = ggx_visible_normal(np.full(k, so), np.zeros(k), np.full(k, mu), alpha, rng.random(k),
                                        rng.random(k))
        res.append((f"GGX visible normals alpha={alpha} mu={mu}: mean cos", float(mz.mean()),
                    float(mz.std() / math.sqrt(k)), float(G1 / mu * dot.mean())))
        h = (1 - mz * mz) < alpha * alpha * mz * mz
        res.append((f"GGX visible normals alpha={alpha} mu={mu}: tan^2 < alpha^2", float(h.mean()),
                    float(h.std() / math.sqrt(k)), float(G1 / mu * (dot / cm[:, None])[u < 0.5].sum() / dot.size)))
    # a thin air film in a clear glass: normal incidence, black body; the light bounces between the film and the
    # surface along the normal: R_d = (1 - F0) (1 - Fi) R_f e / (1 - Fi R_f e), e = exp(-2 sigma_a d1)
    n_, d1, sa1 = 1.5, 0.3, 0.4
    F0 = float(fresnel(np.array(1.0), n_))
    Fi = float(fresnel(np.array(1.0), 1 / n_))
    Ff = float(fresnel(np.array(1.0), 1 / n_))
    Rf = Ff + (1 - Ff) ** 2 * Ff / (1 - Ff * Ff)
    e = math.exp(-2 * sa1 * d1)
    rf = run(n_, [(d1, 0.0, sa1, 0.0), (0.3, 0.0, sa1, 0.0)], 0.0, 1.0, nphot=nphot, seed=10, films={0: 1 / n_})
    res.append(("thin air film in clear glass, normal incidence", rf["R_diffuse"], rf["R_diffuse_se"],
                (1 - F0) * (1 - Fi) * Rf * e / (1 - Fi * Rf * e)))
    # a mixture of HG lobes, through run(): single scattering only (max_vertices 3: entry, one scattering, the
    # surface), index-matched, black body, normal incidence, against R1 = int_0^1 p(mu) omega
    # (1 - exp(-tau (1 + 1/mu))) / (1 + 1/mu) dmu with p the mixture's density of mu = -cos(theta)
    lobes = ((0.3, 0.0), (0.7, 0.85))
    ss_, sa_, d_ = 0.5, 0.1, 1.0
    m2 = run(1.0, [(d_, ss_, sa_, lobes)], 0.0, 1.0, nphot=nphot, seed=8, max_vertices=3)
    mu = (np.arange(200000) + 0.5) / 200000
    pm = sum(a * (1 - g * g) / (2 * (1 + g * g + 2 * g * mu) ** 1.5) for a, g in lobes)
    tau, om = (ss_ + sa_) * d_, ss_ / (ss_ + sa_)
    r1 = float(np.mean(pm * om * (1 - np.exp(-tau * (1 + 1 / mu))) / (1 + 1 / mu)))
    res.append(("HG mixture (0.3 x g 0, 0.7 x g 0.85), single scattering", m2["R_diffuse"], m2["R_diffuse_se"], r1))
    # a recorded white run, with absorption and body applied afterwards, against a direct run (two seeds)
    wh = run(1.5, [(0.5, 3.0, 0.0, 0.6)], 1.0, 1.0, nphot=nphot, seed=6, alpha=0.1, record=True)
    di = run(1.5, [(0.5, 3.0, 0.4, 0.6)], 0.5, 1.0, nphot=nphot, seed=7, alpha=0.1)
    ap = float(events_apply(wh["events"], nphot, [0.4], 0.5)[0])
    res.append(("recorded run, sigma_a 0.4 and rho 0.5 applied (R_diffuse)", ap, math.hypot(di["R_diffuse_se"],
                wh["R_diffuse_se"] * ap / max(wh["R_diffuse"], 1e-12)), di["R_diffuse"]))
    # a nearly smooth rough surface gives the smooth answer (two seeds, the same slab)
    sm = run(1.5, [(1.2, 2.5, 0.03, 0.7)], 0.12, 1.0, nphot=nphot, seed=4)
    ro = run(1.5, [(1.2, 2.5, 0.03, 0.7)], 0.12, 1.0, nphot=nphot, seed=5, alpha=1e-3)
    res.append(("rough alpha=1e-3 against smooth (R_total)", ro["R_total"],
                math.hypot(ro["R_diffuse_se"], sm["R_diffuse_se"], ro["R_specular_se"]), sm["R_total"]))
    return res


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--nphot", type=int, default=400_000)
    a = sub.add_parser("albedo")
    a.add_argument("--n", type=float, default=1.5)
    a.add_argument("--layer", action="append", required=True, help="thickness_mm,sigma_s,sigma_a,g (top first)")
    a.add_argument("--body", type=float, required=True)
    a.add_argument("--mu", type=float, default=1.0)
    a.add_argument("--nphot", type=int, default=1_000_000)
    a.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if args.cmd == "check":
        bad = 0
        for name, mc, se, ex in check(args.nphot):
            z = (mc - ex) / se if se > 0 else float("inf") * (mc != ex)
            flag = "" if abs(z) < 4 else "  <-- FAIL"
            bad += bool(flag)
            print(f"{name:58s} mc {mc:.6f} +- {se:.6f}  exact {ex:.6f}  z {z:+.2f}{flag}")
        sys.exit(1 if bad else 0)
    layers = [tuple(float(v) for v in s.split(",")) for s in args.layer]
    r = run(args.n, layers, args.body, args.mu, nphot=args.nphot, seed=args.seed)
    r.pop("hist")
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
