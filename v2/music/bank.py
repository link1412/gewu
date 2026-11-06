"""Render held Keyscape notes, once per patch. The score then uses them without rendering again.

    python3 -I v2/music/bank.py "Harmochord - Dry Slow" reed 39,46,53,60,67 [hold seconds, default 28]

Writes out/v2/music/bank/<stem>_<midi>.wav. Runs khost and keyscape.py, not in this repository, on the Mac named by GEWU_KEYSCAPE_HOST, in ~/keyscape.
khostw ends khost once the file is written, because Keyscape hangs in its teardown.
"""

import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANK = os.path.join(ROOT, "out", "v2", "music", "bank")
SR = 48000
HOST = os.environ.get("GEWU_KEYSCAPE_HOST")


def main():
    if not HOST:
        raise SystemExit("set GEWU_KEYSCAPE_HOST to a Mac with Keyscape; see v2/music/README.md")
    patch, stem, notes = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")]
    hold = float(sys.argv[4]) if len(sys.argv) > 4 else 28.0
    vel = int(sys.argv[5]) if len(sys.argv) > 5 else 80
    os.makedirs(BANK, exist_ok=True)
    gap = hold + 12.0  # some patches ring for seconds after release
    ev = []
    for i, m in enumerate(notes):
        t = 1.0 + i * gap
        ev += [[t, 144, m, vel], [t + hold, 128, m, 0]]
    with tempfile.TemporaryDirectory() as d:
        j = os.path.join(d, "ev.json")
        json.dump({"events": ev}, open(j, "w"))
        subprocess.run(["scp", "-q", j, f"{HOST}:keyscape/work/{stem}.json"], check=True)
        cmd = f'cd ~/keyscape && /usr/bin/python3 keyscape.py state "{patch}" work/{stem}.plist && ./khostw --state work/{stem}.plist --events work/{stem}.json --out work/{stem}.wav --warm 10 --tail 6'
        subprocess.run(["ssh", HOST, cmd], check=True)
        w = os.path.join(d, "x.wav")
        subprocess.run(["scp", "-q", f"{HOST}:keyscape/work/{stem}.wav", w], check=True)
        y, sr = sf.read(w, always_2d=True)
    if sr != SR:
        raise SystemExit(f"sample rate {sr}")
    for i, m in enumerate(notes):
        a = int((1.0 + i * gap) * SR)
        x = y[a : a + int(gap * SR)]
        p = os.path.join(BANK, f"{stem}_{m}.wav")
        sf.write(p, x, SR, subtype="FLOAT")
        print(p, f"peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dB")


main()
