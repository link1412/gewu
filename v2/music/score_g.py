"""Version G: F with real counterpoint. Until now every voice sang the same three notes at another time or octave: a canon that reads as one figure and its echo.

    python3 -I v2/music/voice_mit.py MuseScore_General.sf2    # once: out/v2/music/bank_mit/
    python3 -I v2/music/score_g.py                            # out/v2/music/mix_G_mit3.wav, the film's music

Keeps: the ostinato and its canon a half beat late, the high voice in the second wave, everything else of F.
New, from the first caption, in place of the two voices that doubled the figure below it:
  counter line   long sung notes, one to a loop, by step and rising: first wave D5 E5 F#5 E5, second F#5 A5 B5 A5 F#5 A5 D6
  bass line      long sung notes, against it: first wave D3 B2 A2 B2, second D3 B2 A2 F#2 A2 B2 A2. It stops on the fifth, so the cut to the sunrise resolves it to D
Silent in the hush. Notes are written in Eb midi and sound a semitone down, as in score_e.py. The long notes are the same choir sample as the chops, held, with a slow vibrato that is added. Written, not heard.
"""
import json
import os
import sys
from functools import lru_cache

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score  # noqa: E402
from score import SR, add, bank, db, measured_cents, sstep  # noqa: E402
from score_e import Sung  # noqa: E402
from score_f import lead_notes, render  # noqa: E402

COUNTER = ([75, 77, 79, 77, 79, 77], [79, 82, 84, 82, 79, 82, 87])
BASS = ([51, 48, 46, 48, 46, 48], [51, 48, 46, 43, 46, 48, 46])
COUNTER_DB, BASS_DB = -9.0, -8.0  # against a voice of the ostinato, about -4 here. 0.16 is the same scale as the chops


def notes(c):
    """The chops, without the voices the lines replace."""
    return [e for e in lead_notes(c) if not (e[0] < c.sun and ((e[4] == "v3" and e[0] >= c.cap) or e[4] == "v5"))]


class MitSung(Sung):
    """The chops at the table's gain, each note as loud as it was before the change of sounds (voice_mit.py)."""

    GAIN = {int(k): v["chop_gain"] for k, v in json.load(open(os.path.join(HERE, "voice_mit.json"))).items()}

    def note(self, m, **kw):
        return super().note(m, **kw) * self.GAIN[m]


@lru_cache(maxsize=None)
def held_trim(m):
    """A long note reads later in the sample than a chop, where this choir sits at another pitch: up to 26 cents off with the chops' trim. Sung reads a semitone slow, hence the 100."""
    return measured_cents(bank("voice", m), m, 0.25, 2.0) + 100.0


def held(voice, m, dur, r):
    x = voice.sample(m)
    t = np.arange(int(min(dur, 1.75) * SR)) / SR
    rate = r.uniform(4.6, 5.4)
    depth = 14.0 * sstep((t - 0.25) / 0.4)  # a slow vibrato that comes in late, as a singer's does
    cents = 18.0 * np.exp(-t / 0.08) + depth * np.sin(2 * np.pi * rate * t + r.uniform(0, 6.28)) - held_trim(m)
    y = np.interp((0.25 + r.uniform(0, 0.05)) * SR + np.cumsum(2.0 ** (cents / 1200.0)), np.arange(len(x)), x)
    return y * sstep(t / 0.09) * (1 - sstep((t - (t[-1] - 0.22)) / 0.22)) * (0.82 + 0.18 * sstep(t / 0.7))


def lines(voice, c, t):
    r = np.random.default_rng(31)
    out = np.zeros((len(t), 2))
    rms = {}
    for label, (w1, w2), level, pan in (("counter", COUNTER, COUNTER_DB, 0.3), ("bass", BASS, BASS_DB, -0.2)):
        bus = np.zeros((len(t), 2))
        for a, b, pattern in ((c.cap, c.again, w1), (c.re, c.sun, w2)):
            k = (b - a) // 3
            if k > len(pattern):
                raise SystemExit(f"{label}: {k} loops, the pattern has {len(pattern)}; write more notes")
            for i, m in enumerate(pattern[:k] if a == c.cap else pattern[-k:]):
                n = a + 3 * i
                dur = float(c.at(n + 3) - c.at(n)) + 0.06
                # the first wave rises in level, the second more
                g = level + (i / max(1, k - 1)) * (2.0 if a == c.cap else 3.5)
                add(bus, held(voice, m, dur, r), float(c.at(n)), db(g) * 0.16, pan)
        rms[label] = 20 * np.log10(np.sqrt((bus[int(c.first_caption * SR) : int(c.sunrise * SR)] ** 2).mean()) + 1e-9)
        out += bus
    print("lines, RMS from first caption to sunrise, dB:", {k: round(float(v), 1) for k, v in rms.items()}, flush=True)
    return out


if __name__ == "__main__":
    score.BANK = os.path.join(score.OUT, "bank_mit")
    render(name="G_mit3", notes=notes, lines=lines, sung=MitSung)
