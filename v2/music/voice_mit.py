"""The film's choir and strings, from MuseScore General 0.2 (MIT, after Fluid R3; notice in NOTICE-MuseScore-General.md). Sounds with clear terms; this is the third try.

    python3 -I v2/music/voice_mit.py MuseScore_General.sf2

Writes out/v2/music/bank_mit/: voice_* and str_*, with links to the Keyscape low_* and high_* in out/v2/music/bank/. score_g.py reads this directory.

Strings (program 49): rendered as they are.
Choir (program 52), per note, from voice_mit.json:
- root: which recording. Taken from any key and shifted, because the font's own key map gives the motif's three notes three recordings whose 1.2-1.8 kHz runs -26.6, -8.9 and -15.1 dB; heard as a man and a woman.
- cut: the seconds dropped from the start, so that what the chops read is the steadiest stretch. The choir scoops and swells for about 0.4 s.
- filter_db: one static filter, the gain at each harmonic of the note up to 14 kHz. Without it the note reads harsh (the second try).
- chop_gain is used by score_g.py: a chop as loud as the same note's chop before the change.
The table's numbers were measured against the earlier voice from TimbresOfHeaven V3.4, which is not in the film. Only numbers came across.
"""

import json
import os
import sys
from fractions import Fraction

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sf2 import ROOT, SR, render  # noqa: E402

OUT = os.path.join(ROOT, "out", "v2", "music")
HOLD = 7.0
TOP_HZ = 14000.0
SECONDS = 5  # kept after the cut
STRINGS = [39, 46, 51, 53, 55, 58]
KEYSCAPE = ["low_39", "low_46", "low_51", "low_55", "low_58", "high_58", "high_63", "high_65", "high_67"]


def shifted(y, semitones):
    if semitones == 0:
        return y
    r = Fraction(float(2.0 ** (-semitones / 12.0))).limit_denominator(4000)  # a higher pitch reads faster: fewer samples for the same audio
    return resample_poly(y, r.numerator, r.denominator, axis=0)


def filtered(y, m, gains):
    f0 = 440.0 * 2.0 ** ((m - 69) / 12.0)
    hz = np.array([k * f0 for k in range(1, len(gains) + 1)])
    f = np.fft.rfftfreq(len(y), 1 / SR)
    curve = np.interp(np.log2(np.maximum(f, 1.0)), np.log2(hz), gains)
    return np.fft.irfft(np.fft.rfft(y, axis=0) * (10 ** (curve / 20))[:, None], n=len(y), axis=0)


def main(font):
    table = {int(k): v for k, v in json.load(open(os.path.join(HERE, "voice_mit.json"))).items()}
    out = os.path.join(OUT, "bank_mit")
    os.makedirs(out, exist_ok=True)
    roots = sorted({v["root"] for v in table.values()})
    takes = dict(zip(roots, render(font, 52, roots, HOLD, 100)))
    for m, v in sorted(table.items()):
        y = shifted(takes[v["root"]], m - v["root"])
        i = int(v["cut"] * SR)
        y = y[i : i + SECONDS * SR].astype(np.float32).astype(np.float64)  # the chosen take passed through a 32-bit file here; with this the mix matches it bit for bit
        y = filtered(y, m, np.array(v["filter_db"]))
        sf.write(os.path.join(out, f"voice_{m}.wav"), y, SR, subtype="FLOAT")
    for m, y in zip(STRINGS, render(font, 49, STRINGS, 38.0, 90)):
        sf.write(os.path.join(out, f"str_{m}.wav"), y, SR, subtype="FLOAT")
    for stem in KEYSCAPE:
        link = os.path.join(out, stem + ".wav")
        if not os.path.lexists(link):
            os.symlink(os.path.join("..", "bank", stem + ".wav"), link)
    print(out, len(table), "voice notes,", len(STRINGS), "string notes")


if __name__ == "__main__":
    main(sys.argv[1])
