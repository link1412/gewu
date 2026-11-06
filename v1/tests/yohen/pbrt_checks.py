"""Checks of pbrt's thinfilm material beyond the smooth strip (tests/yohen/pbrt_strip.py):

1. rough: film of zero thickness with GGX roughness against pbrt's own conductor with k = 0 (the same microfacet
   model with the dielectric Fresnel); a uniform white sky, so each image's mean is the directional albedo.
2. rough film: a 150 nm film, roughness 0.2, against tools/tmm.py's R integrated over the GGX lobe here
   (Monte Carlo over visible normals, as pbrt samples; the reference is computed in this script).
3. diffuse base: smooth, no film, rho = 0.5: R(t) + rho (1 - R(t)) (1 - 2 int_0^1 R(mu) mu dmu).

    python3 -I tests/yohen/pbrt_checks.py out/yohen/pbrt_checks
"""
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import tmm  # noqa: E402

PBRT = os.path.join(ROOT, "third_party/pbrt-build/pbrt")
D = sys.argv[1]
os.makedirs(D, exist_ok=True)
ANG = 30.0
SPP = 1024


def const(v):
    return f"[ 360 {v:.6f} 830 {v:.6f} ]"


def render(name, material):
    th = np.radians(ANG)
    scene = f"""LookAt 0 {-10 * np.sin(th)} {10 * np.cos(th)}  0 0 0  0 1 0
Camera "orthographic" "float screenwindow" [ -0.5 0.5 -0.5 0.5 ]
Sampler "independent" "integer pixelsamples" {SPP}
Integrator "volpath" "integer maxdepth" 4
Film "rgb" "integer xresolution" 32 "integer yresolution" 32 "string filename" "{name}.exr"
WorldBegin
LightSource "infinite" "rgb L" [ 1 1 1 ]
{material}
Shape "bilinearmesh" "point3 P" [ -4 -4 0  4 -4 0  -4 4 0  4 4 0 ]
"""
    with open(os.path.join(D, name + ".pbrt"), "w") as f:
        f.write(scene)
    subprocess.run([PBRT, "--quiet", name + ".pbrt"], cwd=D, check=True)
    img = camera.read_raw(os.path.join(D, name + ".exr")).reshape(-1, 3)
    return img.mean(0), img.std(0) / np.sqrt(len(img))


def film_mat(d, rough, rho=0.0, n1=2.5, n2=1.6):
    m = (f'Material "thinfilm" "spectrum filmeta" {const(n1)} "spectrum eta" {const(n2)} '
         f'"float thickness" {d} "float roughness" {rough} "bool remaproughness" false')
    if rho:
        m += f' "spectrum reflectance" {const(rho)}'
    return m


def report(name, got, err, ref):
    z = (got - ref) / np.maximum(err, 1e-12)
    rel = got / ref - 1
    print(f"{name:34s} pbrt {np.round(got, 5)}  ref {np.round(ref, 5)}  rel {np.round(rel * 100, 2)} %  "
          f"z {np.round(z, 1)}")
    return np.all(np.abs(rel) < 0.01)


ok = True
lam = camera.LAM
cos0 = np.cos(np.radians(ANG))

# 1. zero thickness, rough: thinfilm against conductor (k = 0)
for alpha in (0.1, 0.3):
    a, ea = render(f"tf0_a{alpha}", film_mat(0, alpha))
    b, eb = render(f"cond_a{alpha}", f'Material "conductor" "spectrum eta" {const(1.6)} "spectrum k" '
                                       f'{const(0)} "float roughness" {alpha} "bool remaproughness" false')
    ok &= report(f"d=0 alpha {alpha} vs conductor", a, np.hypot(ea, eb), b)


# 2. a 150 nm film, rough: the GGX lobe's albedo with the film's R at the microfacet, by Monte Carlo here
def ggx_film_albedo(alpha, d, n=200000, seed=3):
    rng = np.random.default_rng(seed)
    wo = np.array([np.sqrt(1 - cos0 ** 2), 0.0, cos0])
    # Heitz 2018 visible-normal sampling (as pbrt's Sample_wm), isotropic alpha
    wh = np.array([alpha * wo[0], alpha * wo[1], wo[2]])
    wh /= np.linalg.norm(wh)
    T1 = np.cross([0, 0, 1], wh)
    T1 /= np.linalg.norm(T1)
    T2 = np.cross(wh, T1)
    u1, u2 = rng.random(n), rng.random(n)
    r = np.sqrt(u1)
    phi = 2 * np.pi * u2
    t1, t2 = r * np.cos(phi), r * np.sin(phi)
    s = 0.5 * (1 + wh[2])
    t2 = (1 - s) * np.sqrt(1 - t1 ** 2) + s * t2
    nh = t1[:, None] * T1 + t2[:, None] * T2 + np.sqrt(np.maximum(0, 1 - t1 ** 2 - t2 ** 2))[:, None] * wh
    wm = np.stack([alpha * nh[:, 0], alpha * nh[:, 1], np.maximum(1e-6, nh[:, 2])], 1)
    wm /= np.linalg.norm(wm, axis=1)[:, None]
    cosm = wm @ wo
    wi = 2 * cosm[:, None] * wm - wo
    up = wi[:, 2] > 0

    def lam_(w):
        t2_ = (w[:, 0] ** 2 + w[:, 1] ** 2) / np.maximum(w[:, 2] ** 2, 1e-12)
        return (np.sqrt(1 + alpha ** 2 * t2_) - 1) / 2

    lo = lam_(wo[None])[0]
    li = lam_(wi)
    # estimator: F * G2 / G1(wo) (Smith height-correlated, as pbrt's G)
    w = np.where(up, (1 + lo) / (1 + lo + li), 0.0)
    # R at each microfacet cosine: tabulate over cos
    cg = np.linspace(1e-4, 1.0, 401)
    tab = np.array([tmm.rgb709_of(tmm.reflectance(lam, [(2.5, d)], 1.6, 1.0, c)) for c in cg])
    Rm = np.stack([np.interp(np.clip(cosm, 0, 1), cg, tab[:, k]) for k in range(3)], 1)
    est = Rm * w[:, None]
    return est.mean(0), est.std(0) / np.sqrt(n)


for alpha in (0.05, 0.2):
    got, e1 = render(f"tf150_a{alpha}", film_mat(150, alpha))
    ref, e2 = ggx_film_albedo(alpha, 150)
    ok &= report(f"d=150 alpha {alpha} vs GGX(tmm)", got, np.hypot(e1, e2), ref)

# 3. diffuse base, smooth, no film
rho = 0.5
got, e = render("rho", film_mat(0, 0, rho))
mu = np.linspace(0, 1, 2001)
Rmu = np.array([tmm.reflectance(lam, [], 1.6, 1.0, max(m, 1e-6)).mean() for m in mu])
hem = 2 * np.trapezoid(Rmu * mu, mu)
R0 = tmm.reflectance(lam, [], 1.6, 1.0, cos0).mean()
ref = np.full(3, R0 + rho * (1 - R0) * (1 - hem))
ok &= report("diffuse base rho 0.5", got, e, ref)
print("pbrt thinfilm checks:", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
