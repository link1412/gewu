"""Faults that numbers can find. Clicks, DC, phase, whether the notes are the ones written and land where they should, and how far the tune is from the original's.

    python3 -I v2/music/verify.py A
"""
import os
import sys

import librosa
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import CELLS, OUT, SR, Clock, score  # noqa: E402

cell = sys.argv[1] if len(sys.argv) > 1 else "A"
if cell == "C":  # same voice, its own form
    from score_c import CELL, Form, lead_notes

    Clock, CELLS = Form, {"C": (list(CELL),)}
    score = lambda clk, _: lead_notes(clk)
elif cell == "E":
    from score_e import CELL, lead_notes
    from score_d import Steady

    Clock, CELLS = Steady, {"E": (list(CELL),)}
    score = lambda clk, _: lead_notes(clk)
elif cell == "F":
    from score_f import Twice, lead_notes
    from score_e import CELL

    Clock, CELLS = Twice, {"F": (list(CELL),)}
    score = lambda clk, _: lead_notes(clk)
elif cell == "G":
    from score_f import Twice
    from score_g import notes as lead_notes
    from score_e import CELL

    Clock, CELLS = Twice, {"G": (list(CELL),)}
    score = lambda clk, _: lead_notes(clk)
elif cell == "D":
    from score_d import CELL, Steady, lead_notes

    Clock, CELLS = Steady, {"D": (list(CELL),)}
    score = lambda clk, _: lead_notes(clk)
y = sf.read(os.path.join(OUT, "mix_G_mit3.wav" if cell == "G" else f"mix_{cell}.wav"), always_2d=True)[0]
clk = Clock()
m = y.mean(1)
print(f"length {len(y) / SR:.3f} s, film {clk.total:.3f} s; DC {m.mean():+.5f}; start {20 * np.log10(np.abs(y[:480]).max() + 1e-9):.0f} dB, last 10 ms {20 * np.log10(np.abs(y[-480:]).max() + 1e-9):.0f} dB")
print(f"mono against stereo RMS {10 * np.log10((m**2).mean() / ((y**2).mean() + 1e-12)):+.1f} dB (0 is fully mono-safe, -3 is uncorrelated)")
# clicks: a one-sample jump far above its neighbourhood, above 1.5 kHz so the sub does not count
d = np.abs(np.diff(y, axis=0)).max(1)
loc = np.convolve(d, np.ones(480) / 480, "same") + 1e-6
sus = np.where((d > 8 * loc) & (d > 0.03))[0]
print("click candidates:", len(sus), np.round(sus[:12] / SR, 3).tolist())
# the notes of voice 1 before the canon enters
print("voice 1, written against measured, first beats:")
for n, mid, *_ in [e for e in score(clk, cell) if e[4] == "v1" and e[0] < clk.canon]:
    t0 = float(clk.at(n))
    seg = m[int((t0 + 0.04) * SR) : int((t0 + 0.2) * SR)]
    f, *_ = librosa.pyin(seg, fmin=librosa.midi_to_hz(mid - 3), fmax=librosa.midi_to_hz(mid + 3), sr=SR, frame_length=2048, hop_length=240)
    med = np.nanmedian(f)
    print(f"  beat {n:2d} at {t0:5.2f} s: {librosa.midi_to_note(mid, unicode=False):4s} measured {librosa.hz_to_note(med, cents=True, unicode=False)}")
# onsets against the beats that must land on a picture
ons = librosa.onset.onset_detect(y=m, sr=SR, hop_length=256, units="time", backtrack=False)
labels = ("shot 2", "shot 3", "shot 4", "first caption", "日日新", "又日新", "一滴", "still", "new note", "sunrise", "name, loud again") if cell == "C" else ("shot 2", "first caption", "sunrise", "name, loud again") if cell in "DE" else ("shot 2", "first caption", "shut, 又日新", "back", "sunrise", "name, loud again") if cell in "FG" else ("shot 2", "shot 3", "shot 4", "first caption", "sunrise", "name, loud again")
for name, n in zip(labels, clk.n.tolist()):
    t = float(clk.at(n))
    print(f"  {name:18s} beat {n:2d} at {t:6.2f} s, nearest onset {ons[np.abs(ons - t).argmin()] - t:+.3f} s")
print(f"  name fades in {clk.name_in:.2f}-{clk.name_full:.2f} s; everything comes back at {float(clk.at(clk.back)):.2f} s; film ends {clk.total:.2f} s")
# against the original: interval patterns and their positions
ours = CELLS[cell][0]
theirs = [66, 76, 69]
iv = lambda c: [c[(i + 1) % 3] - c[i] for i in range(3)]
pc = lambda c: sorted(x % 12 for x in c)
print(f"loop intervals: ours {iv(ours)}, original {iv(theirs)}; relative to tonic ours {[(x - 63) % 12 for x in ours]}, original {[(x - 62) % 12 for x in theirs]}")
