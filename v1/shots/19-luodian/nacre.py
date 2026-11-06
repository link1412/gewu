"""Nacre (mother-of-pearl) for shot 19 (点螺): the reflectance of its disordered aragonite / organic
multilayer under the polished surface (docs/shots/19-dianluo.md, 物理).

    python3 -I shots/19-luodian/nacre.py lut --params shots/19-luodian/nacre.json --out out/shots/19-luodian/nacre_lut_wide.npz
    python3 -I shots/19-luodian/nacre.py swatch --lut out/shots/19-luodian/nacre_lut_wide.npz --out out/shots/19-luodian/nacre_swatch.png

The model:
- The stack: aragonite tablets (thickness d_a) and thin organic interlamellar layers (d_o), repeated.
  Every layer's thickness is drawn on its own (normal, mean and spread from the shell's measurements,
  kept above 5% of the mean): one draw is one column of tablets.
- Aragonite is biaxial, but in nacre its c axis is normal to the tablets: in the plane of the layers it
  has n_beta and n_gamma (0.005 apart), along the normal n_alpha. We take it as uniaxial: n_o = the mean
  of n_beta and n_gamma, n_e = n_alpha. With the optic axis normal to the interfaces, s and p do not mix
  and a 2 x 2 characteristic matrix is exact for each. With b the tangential index (the same in every
  layer; for layers parallel to the surface, the sine of the angle in air):
      s:  q = sqrt(n_o^2 - b^2),                admittance Y = q
      p:  q = (n_o / n_e) sqrt(n_e^2 - b^2),    admittance Y = n_o^2 / q
  (isotropic layers are the case n_o = n_e), and the layer's matrix is [[cos d, i sin d / Y], [i Y sin d, cos d]]
  with phase d = 2 pi q t / lambda.
- A pixel (tens of um) spans many tablet columns (5-10 um wide, wider than the wavelength) whose
  reflections have unrelated phases: it sees the mean of |r|^2 over the draws, not |mean r|^2.
- Below the shell is black lacquer: what gets through the stack is absorbed. The shell / lacquer
  interface is the stack's substrate, so its small reflection is included.
- The polished top surface is tilted against the layers, so the phase between its reflection and the
  stack's changes across a pixel: it is a separate reflection with its own normal (the renderer's
  surface normal; the stack's lobe uses the layers' normal). Light gets into the stack and out through
  it, and bounces between it and the stack:  R_lobe = T_top^2 R_stack / (1 - R_top R_stack),  per polarisation.
- Unpolarised light: the mean of s and p, for each lobe.

The tables, for the renderer (tools/cycles_scene.py composes them per shading point):
- R_stack[pol][d, b, lam]: the stack alone, lit from inside a tablet, as a function of the shell's mean
  tablet thickness d (the colour of a piece) and of b = n_o sin(angle to the layers' normal) inside the
  shell. b, not an angle in air: the layers are tilted against the polished surface, so the angle that
  matters to them is not the one outside.
- R_top[pol][mu, lam]: the polished surface, air to aragonite, mu = cos(angle in air to the surface normal);
  its transmission is 1 - R_top (no absorption).
- The renderer refracts the view ray in, reflects it off the layers, refracts it out (or loses it to total
  internal reflection), and weights the stack by T_top in and out, per polarisation:
      lobe = sum over s, p of T_in T_out R_stack / (1 - R_top,out R_stack),  then the mean of s and p.
  (The polarisation basis turns a little with the tilt, a few degrees; ignored.)
"""

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from camera import LAM, Spectra, rgb709_from_xyz  # noqa: E402


# --- optics ------------------------------------------------------------------------------------
def qy(n, b, pol):
    """z component of the wave vector (over k0) and tangential admittance (free space = 1) in a
    uniaxial medium n = (n_o, n_e) whose optic axis is normal to the layers."""
    no, ne = n
    if pol == "s":
        q = np.sqrt(no * no - b * b + 0j)
        return q, q
    q = (no / ne) * np.sqrt(ne * ne - b * b + 0j)
    return q, no * no / q


def stack_r(lam, b, n_inc, layers, n_sub, pol):
    """Amplitude reflection of a stack lit from the medium n_inc: layers = [(n, thickness_nm), ...]
    from the top down, n = (n_o, n_e); the substrate n_sub. All arrays broadcast together."""
    _, Y0 = qy(n_inc, b, pol)
    _, Ys = qy(n_sub, b, pol)
    shape = np.broadcast_shapes(np.shape(lam), np.shape(b), np.shape(Ys))
    B = np.ones(shape, complex)
    C = Ys * B
    k0 = 2 * np.pi / lam
    cache = {}
    for n, t in reversed(layers):                       # [B, C] = M_1 ... M_N [1, Y_sub]
        if id(n) not in cache:                          # the layers share a few n tuples
            cache[id(n)] = qy(n, b, pol)
        q, Y = cache[id(n)]
        ph = k0 * q * t
        c, s = np.cos(ph), np.sin(ph)
        B, C = c * B + 1j * s / Y * C, 1j * Y * s * B + c * C
    return (Y0 * B - C) / (Y0 * B + C)


def fresnel_R(lam, b, n_inc, n_sub, pol):
    return np.abs(stack_r(lam, b, n_inc, [], n_sub, pol)) ** 2


def stack_T(lam, b, n_inc, layers, n_sub, pol):
    """Power transmitted into a non-absorbing substrate (for the energy check)."""
    _, Y0 = qy(n_inc, b, pol)
    _, Ys = qy(n_sub, b, pol)
    shape = np.broadcast_shapes(np.shape(lam), np.shape(b), np.shape(Ys))
    B = np.ones(shape, complex)
    C = Ys * B
    k0 = 2 * np.pi / lam
    for n, t in reversed(layers):
        q, Y = qy(n, b, pol)
        ph = k0 * q * t
        c, s = np.cos(ph), np.sin(ph)
        B, C = c * B + 1j * s / Y * C, 1j * Y * s * B + c * C
    return 4 * Y0.real * Ys.real / np.abs(Y0 * B + C) ** 2


# --- the shell's stack -------------------------------------------------------------------------
REQUIRED = ["aragonite_n_alpha", "aragonite_n_beta", "aragonite_n_gamma", "organic_n",
            "tablet_spread_nm", "organic_nm", "organic_spread_nm", "sheet_um", "lacquer_n"]


def load_params(path):
    """Every number must be in the file with its source; nothing has a default (缺数据就报错)."""
    P = json.load(open(path))
    missing = [k for k in REQUIRED if k not in P or P[k].get("value") is None]
    if missing:
        raise SystemExit(f"{path}: no value for {missing}")
    for k in REQUIRED:
        if not P[k].get("source"):
            raise SystemExit(f"{path}: {k} has no source")
    return {k: P[k]["value"] for k in REQUIRED} | {"grid": P.get("grid", {})}


def draw_layers(p, d_a, rng, K):
    """K columns: the layers from the top of the stack down, thicknesses (K, 1, 1) arrays in nm."""
    period = d_a + p["organic_nm"]
    n_org = int(round(p["sheet_um"] * 1000 / period))
    nA = (0.5 * (p["aragonite_n_beta"] + p["aragonite_n_gamma"]), p["aragonite_n_alpha"])
    nO = (p["organic_n"], p["organic_n"])

    def t(mean, spread):
        return np.maximum(rng.normal(mean, spread, (K, 1, 1)), 0.05 * mean)

    layers = []
    for i in range(n_org):                  # the light starts in a tablet: organic, tablet, ..., organic
        layers.append((nO, t(p["organic_nm"], p["organic_spread_nm"])))
        if i < n_org - 1:
            layers.append((nA, t(d_a, p["tablet_spread_nm"])))
    return nA, layers


def stack_table(p, d_a, b, K, seed):
    """R_stack per polarisation, (b, lam), mean over K columns, for tablets of mean thickness d_a."""
    rng = np.random.default_rng(seed)
    nA, layers = draw_layers(p, d_a, rng, K)
    nL = (p["lacquer_n"], p["lacquer_n"])
    lam = LAM[None, None, :]
    bb = np.asarray(b, float)[None, :, None]
    return {pol: (np.abs(stack_r(lam, bb, nA, layers, nL, pol)) ** 2).mean(0) for pol in ("s", "p")}


def top_table(p, mu):
    """R_top per polarisation, (mu, lam): the polished surface, air to aragonite."""
    nA = (0.5 * (p["aragonite_n_beta"] + p["aragonite_n_gamma"]), p["aragonite_n_alpha"])
    mu = np.maximum(np.asarray(mu, float), 1e-4)       # exactly grazing, air's p admittance is infinite
    b = np.sqrt(1 - mu * mu)[:, None]
    return {pol: fresnel_R(LAM[None, :], b, (1.0, 1.0), nA, pol) for pol in ("s", "p")}


def untilted_lobe(Rst, Rtop):
    """The stack's lobe seen from air when the layers lie parallel to the surface, for looking at the
    tables: Rst per polarisation at b = the sine in air, Rtop at the same angles."""
    out = 0.0
    for pol in ("s", "p"):
        R = Rst[pol]
        T = 1 - Rtop[pol]
        out = out + 0.5 * T * T * R / (1 - Rtop[pol] * R)
    return out


def _one(args):
    p, d_a, b, K, seed = args
    return stack_table(p, d_a, b, K, seed)


def cmd_lut(a):
    p = load_params(a.params)
    g = p["grid"]
    d_grid = np.arange(g["d_min_nm"], g["d_max_nm"] + 1e-9, g["d_step_nm"])
    b_grid = np.linspace(0.0, g["b_max"], g["n_b"])
    mu = np.linspace(0.0, 1.0, g["n_mu"])
    K = g["draws"]
    jobs = [(p, float(d), b_grid, K, 1000 + i) for i, d in enumerate(d_grid)]
    with ProcessPoolExecutor(a.jobs) as ex:
        res = list(ex.map(_one, jobs))
    top = top_table(p, mu)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    np.savez_compressed(a.out, lam=LAM, d_nm=d_grid, b=b_grid, mu=mu,
                        R_stack_s=np.array([r["s"] for r in res], np.float32),
                        R_stack_p=np.array([r["p"] for r in res], np.float32),
                        R_top_s=top["s"].astype(np.float32), R_top_p=top["p"].astype(np.float32),
                        n_o=0.5 * (p["aragonite_n_beta"] + p["aragonite_n_gamma"]),
                        params=json.dumps(json.load(open(a.params))))
    print(f"{len(d_grid)} tablet thicknesses x {len(b_grid)} b (0..{g['b_max']}) x {len(LAM)} wavelengths, "
          f"{K} draws; polished surface at {len(mu)} angles -> {a.out}")


# --- looking at it -----------------------------------------------------------------------------
def srgb(xyz, white):
    rgb = rgb709_from_xyz(white) @ xyz
    rgb = np.clip(rgb, 0, None)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)


def cmd_swatch(a):
    """Rows: tablet thickness; columns: angle (mu from 1 at the left to 0.1). The lobe's colour under
    D65, exposed so its brightest cell is white: hue and saturation, not level."""
    from PIL import Image
    L = np.load(a.lut)
    S = Spectra("canon_eos_5d_mkiv")
    d65 = S.d65
    white = S.cmf @ d65 / (S.cmf[1] @ d65)
    mus = np.linspace(1.0, 0.1, 28)
    b = np.sqrt(1 - mus * mus)                           # untilted: b inside = sin in air
    Rst = {pol: np.array([[np.interp(b, L["b"], L[f"R_stack_{pol}"][i, :, k]) for k in range(len(L["lam"]))]
                          for i in range(len(L["d_nm"]))]).transpose(0, 2, 1) for pol in ("s", "p")}
    Rtop = {pol: np.array([np.interp(mus, L["mu"], L[f"R_top_{pol}"][:, k]) for k in range(len(L["lam"]))]).T
            for pol in ("s", "p")}
    R = untilted_lobe(Rst, Rtop)                         # (d, mu, lam)
    xyz = np.einsum("cl,dml->dmc", S.cmf, R * d65) / (S.cmf[1] @ d65)
    xyz /= xyz[..., 1].max()
    img = srgb(xyz.reshape(-1, 3).T, white).T.reshape(R.shape[0], len(mus), 3)
    cell = 12
    big = np.kron(np.clip(img, 0, 1), np.ones((cell, cell, 1)))
    Image.fromarray((big * 255 + 0.5).astype(np.uint8)).save(a.out)
    y = S.cmf[1] * d65 / (S.cmf[1] @ d65)
    print(f"{a.out}: rows d = {L['d_nm'][0]:.0f}..{L['d_nm'][-1]:.0f} nm, columns mu = 1..0.1 (layers parallel "
          f"to the surface); luminance reflectance at normal incidence {(R[:, 0] @ y).min():.3f}..{(R[:, 0] @ y).max():.3f}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lut")
    s.add_argument("--params", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--jobs", type=int, default=6)
    s = sub.add_parser("swatch")
    s.add_argument("--lut", required=True)
    s.add_argument("--out", required=True)
    a = ap.parse_args()
    {"lut": cmd_lut, "swatch": cmd_swatch}[a.cmd](a)


if __name__ == "__main__":
    main()
