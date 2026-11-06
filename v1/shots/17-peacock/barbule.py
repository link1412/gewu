"""Shot 17: the reflectance of a peacock barbule's melanosome / air-channel stack (barbule.json; Freyer & Stavenga
2020's effective-medium multilayer), as tables for the renderer's "barbule" material (tools/rgbscene.py,
tools/cycles_scene.py).

    python3 -I shots/17-peacock/barbule.py lut --region R2_blue_green --out out/shots/17-peacock/lut_R2.npz
    python3 -I shots/17-peacock/barbule.py check --out out/shots/17-peacock/r1/tmm.png

The table R[s, mu, lam]: s runs over the lattice period a (the region's a_table), mu = cos(angle of incidence in air
to the barbule's surface) uniformly 0..1, lam on pbrt's 1 nm grid; unpolarised (mean of TE = s with w 2.5 and
TM = p with w -1.5). The 1-D stack is the model, not the 2-D crystal [A, as Freyer's]. The stack is lit from air
through the keratin cortex; under it keratin, and what enters it is lost.
"""

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import camera  # noqa: E402
import tmm  # noqa: E402

P = json.load(open(os.path.join(HERE, "barbule.json")))
LAM = camera.LAM


def n_keratin(lam):
    return 1.532 + 5890.0 / lam ** 2


def n_melanin(lam):
    return (1.648 + 23700.0 / lam ** 2) + 1j * 0.56 * np.exp(-lam / 270.0)     # ours: N = n + ik, k > 0 absorbs


def profile(g, a, step):
    """Volume fractions (fk, fm, fa) per slice and the slice thickness, top (under the cortex) to bottom."""
    r_m, r_a = g["Dm"] / 2, g["Da"] / 2
    depth = g["Nm"] * a
    z = np.arange(0.0, depth, step) + step / 2
    fm = np.zeros_like(z)
    fa = np.zeros_like(z)
    for k in range(g["Nm"]):
        zc = r_m + k * a
        fm += 2 * np.sqrt(np.maximum(r_m ** 2 - (z - zc) ** 2, 0)) / g["b"]
        if k < g["Nm"] - 1 and not (k == 0 and g["first_air_omitted"]):
            za = zc + a / 2
            fa += 2 * np.sqrt(np.maximum(r_a ** 2 - (z - za) ** 2, 0)) / g["b"]
    if (fm + fa).max() > 1:
        raise SystemExit("profile: rods and channels overlap")
    return 1 - fm - fa, fm, fa


def stack(g, a, step, pol, lam):
    fk, fm, fa = profile(g, a, step)
    w = 2.5 if pol == "s" else -1.5
    nk, nm = n_keratin(lam), n_melanin(lam)
    layers = [(nk, g["c"])]
    for k_, m_, a_ in zip(fk, fm, fa):
        layers.append(((k_ * nk ** w + m_ * nm ** w + a_ * 1.0) ** (1 / w), step))
    return layers, nk


def R_of(g, a, mu, lam=LAM, step=2.0):
    out = 0
    for pol in ("s", "p"):
        layers, nk = stack(g, a, step, pol, lam)
        r, _ = tmm.stack_rt(lam, layers, nk, 1.0, max(mu, 1e-4), pol)
        out = out + 0.5 * np.abs(r) ** 2
    return out


def lut(region, out):
    g = P["regions"][region]
    t = P["table"]
    a_s = np.linspace(*g["a_table"], t["n_s"])
    mus = np.linspace(0, 1, t["n_mu"])
    R = np.zeros((len(a_s), len(mus), len(LAM)), np.float32)
    for i, a in enumerate(a_s):
        for j, mu in enumerate(mus):
            R[i, j] = R_of(g, a, mu, step=t["slice_nm"]) * g.get("amplitude_scale", 1.0)
        print(f"a {a:.1f} nm: peak at normal {LAM[R[i, -1].argmax()]:.0f} nm, R {R[i, -1].max():.3f}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    np.savez_compressed(out, R=R, lam=LAM, mu=mus, s=a_s, region=region, params=json.dumps(g))
    print(f"-> {out}")


def peaks(R, lo=400, hi=760):
    """Local maxima of R over lo..hi nm (5 nm smoothing), largest first."""
    m = (LAM >= lo) & (LAM <= hi)
    x, y = LAM[m], np.convolve(R[m], np.ones(5) / 5, "same")
    i = np.nonzero((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:]))[0] + 1
    i = i[np.argsort(-y[i])]
    return [(float(x[k]), float(y[k])) for k in i[:3]]


def check(out):
    """Normal incidence of each region's model against the measured peaks; the peak's shift with angle."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    lines = []
    for i, (name, g) in enumerate(P["regions"].items()):
        R0 = R_of(g, g["a_model"], 1.0)
        pk = peaks(R0)
        lines.append(f"{name}: model a {g['a_model']}: peaks {[(round(p), round(v, 3)) for p, v in pk]} "
                     f"(measured {g['measured_peak_nm']})")
        ax[0].plot(LAM, R0, label=name)
        for th in (0, 15, 30, 45, 60):
            R = R_of(g, g["a_model"], np.cos(np.radians(th)))
            if i < 2:
                ax[1 + i].plot(LAM, R, label=f"{th} deg")
            lines.append(f"  {name} incidence {th:2d} deg: main peak {peaks(R)[0][0]:.0f} nm")
    ax[0].set_title("normal incidence, Freyer models")
    for k, nm in ((1, "R2"), (2, "R3")):
        ax[k].set_title(f"{nm}, angle of incidence (specular)")
        ax[k].legend()
    ax[0].legend()
    for a_ in ax:
        a_.set_xlabel("nm")
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, dpi=80)
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["lut", "check"])
    ap.add_argument("--region")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "lut":
        lut(a.region, a.out)
    else:
        check(a.out)


if __name__ == "__main__":
    main()
