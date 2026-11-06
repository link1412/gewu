"""Plots of the acceptance numbers (measure.py + track.py) -> out/shots/01-38-ink/measure/targets.png"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure as M  # noqa: E402

D = os.path.join(M.ROOT, "out/shots/01-38-ink/measure")


def main():
    t = {int(k): v for k, v in json.load(open(os.path.join(D, "track.json"))).items()}
    m = {int(k): v for k, v in json.load(open(os.path.join(D, "orig.json"))).items()}
    ours = None
    if os.path.exists(os.path.join(D, "track_ours.json")):
        ours = {int(k): v for k, v in json.load(open(os.path.join(D, "track_ours.json"))).items()}
    kymo = np.load(os.path.join(D, "track_kymo.npy"))           # (frames, FH, 3) RGB codes, cols 1300-1460
    f38 = [f for f in sorted(t) if f >= 399]
    f1 = [f for f in sorted(t) if f < 399]
    fig, ax = plt.subplots(2, 3, figsize=(18, 9.5))
    a = ax[0, 0]
    a.plot(f38, [t[f]["horizon_y"] for f in f38], "k-", lw=2, label="original (frame-0 horizon mapped)")
    if ours:
        g = [f for f in f38 if f in ours]
        a.plot(g, [ours[f]["horizon_y"] for f in g], "o", color="tab:red", label="ours")
    a.axhline(1.0, color="0.6", lw=0.8)
    a.invert_yaxis()
    a.set_title("shot 38: horizon height at the centre (y / frame height; >1 = below the frame)")
    a.set_xlabel("frame")
    for f0, f1_, lab in [(399, 431, "Opus 5.5"), (432, 491, "Claude")]:
        a.axvspan(f0, f1_, color="tab:blue" if lab == "Opus 5.5" else "tab:orange", alpha=0.08)
        a.text((f0 + f1_) / 2, 0.45, lab, ha="center")
    a.legend(loc="lower left")
    a = ax[0, 1]
    hy = np.array([t[f]["horizon_y"] for f in f38])
    v = -np.gradient(hy) * M.FH
    a.plot(f38, v, "k-", lw=2, label="original")
    if ours:
        g = [f for f in f38 if f in ours]
        if len(g) > 2:
            a.plot(g, -np.gradient([ours[f]["horizon_y"] for f in g], g) * M.FH, "o", color="tab:red", label="ours")
    a.set_title("shot 38: rise speed (px/frame at 1080)")
    a.set_xlabel("frame")
    a.legend()
    a = ax[0, 2]
    a.plot(f38, [t[f]["mean_lin"] for f in f38], "k-", lw=2, label="38 mean linear luma")
    a.plot([f - 399 + 399 for f in f1], [t[f]["mean_lin"] for f in f1], "k--", lw=1, label="shot 1 (frames 0-30, x shifted +399)")
    if ours:
        g = sorted(ours)
        a.plot(g, [ours[f]["mean_lin"] for f in g], "o", color="tab:red", label="ours")
    a.set_title("frame brightness (mean of linear luma)")
    a.legend()
    a = ax[1, 0]
    prof = np.array(m[0]["profile_centre"])                    # every 4th row, cols 880-1040
    rows = np.arange(len(prof)) * 4
    h0 = m[0]["horizon_y_centre"] * M.FH
    rel = (h0 - rows) / M.FH
    for c, col in zip(range(3), ["r", "g", "b"]):
        a.plot(rel, prof[:, c], col + "-", lw=1.5)
    a.set_xlim(-0.3, 0.48)
    a.axvline(0, color="0.5", lw=0.8)
    a.set_title("frame 0, centre columns: R G B code values vs height above horizon (/H)")
    a.set_xlabel("height above the horizon / frame height")
    strip = np.repeat(prof[None, ::-1] / 255.0, 30, axis=0)
    a.imshow(strip, extent=(rel[-1], rel[0], 230, 250), aspect="auto")
    a.set_ylim(0, 255)
    a = ax[1, 1]
    a.imshow(kymo.transpose(1, 0, 2)[::2] / 255.0, aspect="auto",
             extent=(f1[0], f1[0] + len(kymo), M.FH, 0))
    a.set_title("kymograph, cols 1300-1460 (x: frames 0-30 then 399-499 concatenated)")
    a.axvline(f1[0] + len(f1), color="w", lw=0.8)
    a = ax[1, 2]
    a.plot(f1, [m[f]["apex_y"] for f in f1], "k-", label="shot 1 apex y")
    a.plot(f1, [m[f]["r_over_w"] / 10 for f in f1], "b-", label="shot 1 R/W / 10")
    a.plot(f1, [m[f]["edge_10_90_px"] / 100 for f in f1], "g-", label="shot 1 edge 10-90 % (px/100)")
    a.set_title("shot 1 (frames 0-30): arc and edge")
    a.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(D, "targets.png"), dpi=80)


if __name__ == "__main__":
    main()
