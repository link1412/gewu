"""Compare a mix with the original by numbers and a picture: I cannot hear, so this is what I can check. It says nothing about whether the music is good.

    python3 -I v2/music/check.py [out/v2/music/mix_A.wav]

Reports the lead's isolated notes against the original's, and draws band levels, L/R correlation and spectrograms side by side, both over their own form:
0 = start, first landmark = the swell (original 8.5 s, ours the first caption), second = the cut (16.1 s, ours the sunrise).
"""

import os
import subprocess
import sys

import matplotlib
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import OUT, ROOT, SR, Clock  # noqa: E402

BANDS = [(25, 90), (90, 300), (300, 1500), (1500, 6000), (6000, 16000)]


def load_ref():
    p = os.path.join(OUT, "ref.wav")  # stays in out/, which is not in git; the recording is only measured
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(ROOT, "ref", "opus55.mp4"), "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s24le", p], check=True)
    return sf.read(p, always_2d=True)[0]


def band(x, lo, hi):
    return sosfiltfilt(butter(4, [lo, hi], "band", fs=SR, output="sos"), x, axis=0)


def levels(y, step=0.25):
    out = {}
    for lo, hi in BANDS:
        s = band(y.mean(1), lo, hi)
        w = int(step * SR)
        out[(lo, hi)] = np.array([10 * np.log10((s[i : i + w] ** 2).mean() + 1e-12) for i in range(0, len(s) - w, w)])
    return out


def corr(y, step=0.5):
    w = int(step * SR)
    out = {}
    for lo, hi in BANDS:
        l, r = band(y[:, 0], lo, hi), band(y[:, 1], lo, hi)
        out[(lo, hi)] = np.array([np.corrcoef(l[i : i + w], r[i : i + w])[0, 1] for i in range(0, len(l) - w, w)])
    return out


def puff_report(y, t0, f0, name):
    m = y.mean(1)
    a, b = int((t0 + 0.03) * SR), int((t0 + 0.19) * SR)
    c, d = int((t0 + 0.30) * SR), int((t0 + 0.46) * SR)
    row = []
    for lo, hi in [(200, 1000), (1000, 2000), (2000, 5200), (5200, 6500), (6500, 9200)]:
        s = band(m, lo, hi)
        row.append(f"{lo}-{hi}: {10 * np.log10((s[a:b] ** 2).mean() + 1e-14) - 10 * np.log10((band(m, 200, 1000)[a:b] ** 2).mean() + 1e-14):+.0f} tail {10 * np.log10((s[c:d] ** 2).mean() + 1e-14) - 10 * np.log10((band(m, 200, 1000)[a:b] ** 2).mean() + 1e-14):+.0f}")
    print(f"{name:10s} {f0:5.0f} Hz  " + " | ".join(row))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "mix_A.wav")
    y = sf.read(path, always_2d=True)[0]
    ref = load_ref()
    clk = Clock()
    cap, end, back = clk.marks()[:3]

    print("lead notes, levels in dB against the 200-1000 Hz band in the puff (original then ours):")
    for t0, f0, name in [(1.30, 658, "orig E5"), (1.83, 442, "orig A4"), (2.36, 369, "orig F#4")]:
        puff_report(ref, t0, f0, name)
    for n, f0, name in [(clk.LOOP, 392, "ours G4"), (clk.LOOP + 1, 523, "ours C5"), (clk.LOOP + 2, 698, "ours F5")]:
        puff_report(y, float(clk.at(n)), f0, name)

    def warp(t, a, b, e):  # to form time: 0-1 before the swell, 1-2 to the cut, 2+ after
        return np.where(t < a, t / a, np.where(t < b, 1 + (t - a) / (b - a), 2 + (t - b) / (e - b)))

    lr, ly = levels(ref), levels(y)
    cr, cy = corr(ref), corr(y)
    tr = np.arange(len(next(iter(lr.values())))) * 0.25 + 0.125
    ty = np.arange(len(next(iter(ly.values())))) * 0.25 + 0.125
    fig, ax = plt.subplots(len(BANDS) + 1, 2, figsize=(17, 13))
    for i, b in enumerate(BANDS):
        ax[i, 0].plot(warp(tr, 8.5, 16.1, 20.05), lr[b], label="original")
        ax[i, 0].plot(warp(ty, cap, end, clk.total), ly[b], label="ours")
        ax[i, 0].set_ylabel(f"{b[0]}-{b[1]} Hz dB")
        ax[i, 0].set_ylim(-95, -5)
        ax[i, 0].grid(alpha=0.3)
        tc = np.arange(len(cr[b])) * 0.5 + 0.25
        tc2 = np.arange(len(cy[b])) * 0.5 + 0.25
        ax[i, 1].plot(warp(tc, 8.5, 16.1, 20.05), cr[b])
        ax[i, 1].plot(warp(tc2, cap, end, clk.total), cy[b])
        ax[i, 1].set_ylabel("L/R corr")
        ax[i, 1].set_ylim(-1, 1.05)
        ax[i, 1].grid(alpha=0.3)
    ax[0, 0].legend()
    for a, x, title in [(ax[-1, 0], ref, "original"), (ax[-1, 1], y, "ours")]:
        a.specgram(x.mean(1) + 1e-9, NFFT=4096, Fs=SR, noverlap=3072, cmap="magma", vmin=-140, vmax=-40)
        a.set_ylim(0, 3000)
        a.set_title(title)
    plt.tight_layout()
    p = os.path.join(OUT, "check_" + os.path.basename(path)[:-4] + ".png")
    plt.savefig(p, dpi=80)
    print(p)
    print("level by band, ours minus original, in form time (dB):")
    for b in BANDS:
        a, c = warp(tr, 8.5, 16.1, 20.05), warp(ty, cap, end, clk.total)
        grid = np.arange(0.1, 3.0, 0.3)
        print(f"  {b[0]:5d}-{b[1]:<5d} " + " ".join(f"{np.interp(g, c, ly[b]) - np.interp(g, a, lr[b]):+4.0f}" for g in grid))


main()
