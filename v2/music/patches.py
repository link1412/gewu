"""What each Keyscape audition patch does, by numbers: A4 short (0.5 s), A4 held (2.5 s), low chord D2 A2 D3 (6.5 s). I cannot hear them; these are facts for choosing, not a verdict.

    python3 -I v2/music/patches.py DIR
"""
import glob
import os
import sys

import numpy as np
import soundfile as sf


def band(S, f, lo, hi):
    return 10 * np.log10((S[(f >= lo) & (f < hi)] ** 2).sum() + 1e-12)


for p in sorted(glob.glob(os.path.join(sys.argv[1], "*.wav"))):
    y, sr = sf.read(p, always_2d=True)
    m = y.mean(1)
    a = m[int(2.5 * sr) : int(4.5 * sr)]
    if np.abs(a).max() < 1e-5:
        print(os.path.basename(p), "silent")
        continue
    env = np.abs(a)
    w = int(0.005 * sr)
    e = np.convolve(env, np.ones(w) / w, "same")
    pk = e.max()
    t10, t90 = np.argmax(e > 0.1 * pk) / sr, np.argmax(e > 0.9 * pk) / sr
    hold = 20 * np.log10(np.sqrt((a[int(1.5 * sr) : int(1.9 * sr)] ** 2).mean()) / np.sqrt((a[int(0.2 * sr) : int(0.6 * sr)] ** 2).mean() + 1e-12) + 1e-9)
    rel = m[int(4.5 * sr) : int(6.4 * sr)]
    r_db = 20 * np.log10(np.sqrt((rel[int(0.8 * sr) : int(1.2 * sr)] ** 2).mean()) / np.sqrt((a[int(1.5 * sr) : int(1.9 * sr)] ** 2).mean() + 1e-12) + 1e-9)
    lf = np.abs(np.fft.rfft(a[int(0.2 * sr) : int(1.9 * sr)] * np.hanning(int(1.9 * sr) - int(0.2 * sr))))
    f = np.fft.rfftfreq(int(1.9 * sr) - int(0.2 * sr), 1 / sr)
    cent = (lf * f).sum() / lf.sum()
    ch = y[int(6.8 * sr) : int(10.2 * sr)]
    corr = np.corrcoef(ch[:, 0], ch[:, 1])[0, 1]
    S = np.abs(np.fft.rfft(ch.mean(1) * np.hanning(len(ch))))
    g = np.fft.rfftfreq(len(ch), 1 / sr)
    h = [band(S, g, lo, hi) for lo, hi in [(50, 200), (200, 800), (800, 3000), (3000, 12000)]]
    print(f"{os.path.basename(p)[:-4]:34s} attack {1000 * (t90 - t10):5.0f} ms  hold change {hold:+5.1f} dB  1 s after release {r_db:+5.1f} dB  centroid {cent:5.0f} Hz  chord L/R {corr:+.2f}  chord bands {h[0] - h[1]:+.0f} / 0 / {h[2] - h[1]:+.0f} / {h[3] - h[1]:+.0f}  peak {20 * np.log10(np.abs(y).max()):.0f}")
