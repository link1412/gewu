"""Render SoundFont notes with fluidsynth, no effects, one file per note. The SoundFonts are real recordings of instruments.

    python3 -I v2/music/sf2.py FONT.sf2 [BANK:]PROGRAM STEM 39,46,51 [hold seconds] [velocity] [out dir]
"""
import os
import subprocess
import sys
import tempfile

import mido
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SR = 48000


def render(font, prog, notes, hold, vel, bank=0):
    gap = hold + 5.0
    mf = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))  # 960 ticks a second
    tr.append(mido.Message("control_change", control=0, value=bank, channel=0, time=0))
    tr.append(mido.Message("program_change", program=prog, channel=0, time=0))
    sec = 960
    tr.append(mido.Message("note_off", note=0, velocity=0, channel=0, time=sec))
    for m in notes:
        tr.append(mido.Message("note_on", note=m, velocity=vel, channel=0, time=0))
        tr.append(mido.Message("note_off", note=m, velocity=0, channel=0, time=int(hold * sec)))
        tr.append(mido.Message("note_off", note=0, velocity=0, channel=0, time=int((gap - hold) * sec)))
    with tempfile.TemporaryDirectory() as d:
        mid, wav = os.path.join(d, "a.mid"), os.path.join(d, "a.wav")
        mf.save(mid)
        r = subprocess.run(["fluidsynth", "-ni", "-g", "1.0", "-r", str(SR), "-R", "0", "-C", "0", "-O", "float", "-T", "wav", "-F", wav, font, mid], capture_output=True, text=True)
        if not os.path.exists(wav):
            raise SystemExit(r.stderr[-500:])
        y, sr = sf.read(wav, always_2d=True)
    assert sr == SR
    return [y[int((1 + i * gap) * SR) : int((1 + (i + 1) * gap) * SR)] for i in range(len(notes))]


if __name__ == "__main__":
    font, stem, notes = sys.argv[1], sys.argv[3], [int(x) for x in sys.argv[4].split(",")]
    bank, prog = [int(x) for x in sys.argv[2].split(":")] if ":" in sys.argv[2] else (0, int(sys.argv[2]))
    hold = float(sys.argv[5]) if len(sys.argv) > 5 else 28.0
    vel = int(sys.argv[6]) if len(sys.argv) > 6 else 90
    out = sys.argv[7] if len(sys.argv) > 7 else os.path.join(ROOT, "out", "v2", "music", "bank")
    os.makedirs(out, exist_ok=True)
    for m, x in zip(notes, render(font, prog, notes, hold, vel, bank)):
        p = os.path.join(out, f"{stem}_{m}.wav")
        sf.write(p, x, SR, subtype="FLOAT")
        print(p, f"peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dB")
