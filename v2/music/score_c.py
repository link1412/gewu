"""Version C of the film's music: the same voice and breath as B, written as a piece with a harmony and a form. Design and reasons in README.md.

    python3 -I v2/music/score_c.py       out/v2/music/mix_C.wav, stems_C/

Reads the cut, like score.py: change the cut and run again. The music never touches the picture; bake it on with v2/music/bake.sh.

Form, bar form on the text of the 盘铭 (short, short, long):
  一声     before the first caption    Eb, filter shut, one voice, then the canon
  苟日新   Eb                         third voice; the bell; the yangqin plays only 新
  日日新   C minor                    the bass falls a third; the yangqin plays the whole loop
  又日新   Bb sus, Eb/G, C minor      the yangqin runs in eighths
  留白     一滴, then 油纸伞·黑        ink: one voice over an open fifth. The still shot: nothing but a bell
  新音     the run to the sunrise     Ab, a note the film has not had until now: 清角, outside the pentatonic. 又日新 is heard, not only read
  日出     the cut shuts the filter; Ab falls to Eb; on the name everything returns and the lead lands on the tonic

Stand-ins: the same as score.py (a choir sample chopped; a reed organ for 笙; bell partials estimated). The yangqin is a SoundFont patch, Timbres of Heaven bank 3 program 46: its pitch was measured
(within 2 cents), its likeness to the instrument was not, and I cannot hear it. Its tremolo is repeated single strikes, not a recorded 轮音.
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import (BEAT0, CEILING_DB, FPS, LEAD_DB, OUT, ROOT, SEED, SR, TARGET_LUFS, Clock, Voice, add, bank, bell, curve, db, ensemble, gate_down, gate_up, highpass, limiter, lowpass, lufs, measured_cents,  # noqa: E402
                   room, shown, sstep, sweep_lowpass, wet)  # fmt: skip

CELL = (70, 77, 72)  # Bb4 F5 C5: low, high, middle
NEW_CELL = (68, 77, 72)  # the second voice in the last run: Ab4, the new note, sung
HOME = (70, 77, 75)  # on the name: comes home to Eb5

# (stem, midi, dB). A note that is in two neighbouring chords keeps sounding across the change: the voices move by common tones, nothing is struck again.
CHORDS = {
    "Eb": [("str", 39, -8), ("str", 46, -5), ("str", 51, -9), ("str", 53, -10), ("str", 55, -9), ("str", 58, -11), ("str", 60, -18), ("low", 39, -15), ("low", 46, -13), ("low", 51, -17), ("low", 55, -19), ("low", 58, -20), ("high", 58, -17), ("high", 63, -15), ("high", 65, -17), ("high", 67, -17)],
    "Cm": [("str", 36, -7), ("str", 48, -7), ("str", 51, -9), ("str", 55, -9), ("str", 58, -11), ("str", 60, -13), ("low", 36, -14), ("low", 48, -14), ("low", 55, -19), ("low", 58, -20), ("high", 58, -17), ("high", 63, -15), ("high", 65, -18), ("high", 67, -17)],
    "Bb": [("str", 34, -7), ("str", 46, -5), ("str", 51, -11), ("str", 53, -9), ("str", 58, -10), ("str", 60, -13), ("low", 34, -14), ("low", 46, -13), ("low", 53, -17), ("low", 58, -19), ("high", 58, -16), ("high", 60, -17), ("high", 63, -16), ("high", 65, -15)],
    "Eb/G": [("str", 43, -6), ("str", 51, -8), ("str", 55, -9), ("str", 58, -10), ("str", 60, -15), ("low", 43, -13), ("low", 51, -16), ("low", 58, -19), ("high", 58, -17), ("high", 63, -15), ("high", 65, -17), ("high", 67, -16)],
    "Ab": [("str", 32, -7), ("str", 44, -5), ("str", 51, -9), ("str", 56, -8), ("str", 58, -10), ("str", 60, -10), ("low", 44, -13), ("low", 51, -17), ("low", 56, -17), ("high", 60, -15), ("high", 63, -16), ("high", 65, -18), ("high", 70, -16)],
    "fifth": [("str", 39, -9), ("str", 46, -6), ("low", 39, -14), ("low", 46, -13)],
}
SUB = {"Eb": 38.89, "Cm": 32.70, "Bb": 58.27, "Eb/G": 38.89, "Ab": 51.91, "fifth": 38.89}  # Bb0 and Ab0 are below what most speakers play, so those two sit an octave up


class Form(Clock):
    """The points where the piece turns, each one a cut of the picture and a whole number of loops from the last. The tempo gives a little between them, as the original's beats do."""

    def __init__(self, shots=None):
        super().__init__(shots)
        shots = self.shots
        t = np.cumsum([0] + [shown(s) for s in shots]) / FPS
        where = lambda test: next(i for i, s in enumerate(shots) if test(s))
        name_beats = self.back - self.sun
        t_days = t[where(lambda s: s.get("caption") == "日日新")]
        t_again = t[where(lambda s: s.get("caption") == "又日新")]
        t_ink = t[where(lambda s: s["src"] == "s76_yidi")]
        i_still = where(lambda s: s["src"] == "s73_heisan")
        t_still, t_run = t[i_still], t[i_still + 1]

        def loops(a, b):
            return 3 * max(1, round((b - a) / BEAT0 / 3))

        self.days = self.cap + loops(self.t[3], t_days)
        self.again = self.days + loops(t_days, t_again)
        self.ink = self.again + loops(t_again, t_ink)
        self.still = self.ink + 3  # the ink is one loop
        self.run = self.still + 3  # nothing sounds here, so these three beats can be any length
        self.sun = self.run + loops(t_run, self.sunrise)
        self.back = self.sun + name_beats
        n = [*self.n[:4], self.days, self.again, self.ink, self.still, self.run, self.sun, self.back]
        s = [*self.t[:4], t_days, t_again, t_ink, t_still, t_run, self.sunrise, self.t[-1]]
        self.n, self.t = np.array(n), np.array(s, float)
        gaps = np.diff(self.t) / np.diff(self.n)
        sung = np.delete(gaps, list(self.n).index(self.still))  # not the silent stretch
        if sung.min() < 0.44 or sung.max() > 0.62:
            raise SystemExit(f"seconds per beat {np.round(gaps, 3).tolist()} between beats {self.n.tolist()}: too far from {BEAT0:.3f} s, the cut has moved, rewrite the form")
        self.still_t = float(t_still)
        loops_again = (self.ink - self.again) // 3
        self.eg = self.again + 3 * max(1, round(loops_again / 3))  # 又日新 has three chords, about equal, on whole loops
        self.cm2 = max(self.eg + 3, self.again + 3 * round(2 * loops_again / 3))
        if self.cm2 >= self.ink:
            raise SystemExit(f"又日新 is too short for three chords: {loops_again} loops")
        self.harmony =[(-99, "Eb"), (self.days, "Cm"), (self.again, "Bb"), (self.eg, "Eb/G"), (self.cm2, "Cm"), (self.ink, "fifth"), (self.run, "Ab"), (self.sun, "fifth"), (self.back, "Eb")]

    def chord_at(self, n):
        return next(c for b, c in reversed(self.harmony) if n >= b)

    def top(self, n):
        """新, the highest note of the loop: F5, G5 on 日日新, Bb5 on 又日新, back to F5 for the ink, then C6 and Eb6 in the run."""
        if n >= self.sun:
            return 77
        if n >= self.sun - 3:
            return 87
        if n >= self.run:
            return 84
        if n >= self.ink:
            return 77
        if n >= self.again:
            return 82
        return 79 if n >= self.days else 77


def lead_notes(f):
    """(beat, midi, dB, pan, voice). Silent on the still shot."""
    rng = np.random.default_rng(SEED + 1)
    ev = [(0, 77, 0.0, 0.0, "v1")]

    def note(n, phase, cell=CELL):
        k = (n - phase) % 3
        return f.top(n + 2 - 1) if k == 1 else cell[k]

    for n in range(2, f.sun):
        if f.still <= n < f.run:  # 留白
            continue
        if f.ink <= n < f.still:  # the ink: one voice, quiet, its top note back where it began
            ev.append((n, note(n, f.LOOP), -5.5 + rng.normal(0, 0.4), 0.0, "v1"))
            continue
        lift = np.interp(n, [2, f.canon, f.canon + 1, f.cap, f.again, f.run, f.sun - 1], [3.0, 3.0, 6.0, 5.0, 4.5, 4.5, 6.5])
        ev.append((n, note(n, f.LOOP), -3.0 + lift + rng.normal(0, 0.5), 0.0, "v1"))
        if n >= f.canon:
            ev.append((n, note(n, f.LOOP + 1, NEW_CELL if n >= f.run else CELL), -6.0 + lift + rng.normal(0, 0.7), -0.45, "v2"))
        if n >= f.cap:
            ev.append((n, note(n, f.LOOP + 2) - 12, -8.0 + lift + rng.normal(0, 0.7), 0.5, "v3"))
        if n >= f.run:  # the two outer voices are kept for the run
            hi = note(n, f.LOOP) + 12
            ev.append((n, hi if hi <= 87 else hi - 12, -17.0 + lift + rng.normal(0, 0.7), 0.7, "v4"))
            ev.append((n, min(note(n, f.LOOP + 1, NEW_CELL), 77) - 24, -11.0 + lift + rng.normal(0, 0.7), -0.25, "v5"))
    for n in range(f.sun, f.back - 2):  # under the sun: far away
        ev.append((n, note(n, f.LOOP), -7.0 + (n - f.sun) * 0.7 + rng.normal(0, 0.5), 0.0, "v1"))
    ev += [(f.back - 2, HOME[0], -5.0, 0.0, "v1"), (f.back - 1, HOME[1], -5.0, 0.0, "v1")]
    ev += [(f.back, HOME[2], -3.0, 0.0, "v1"), (f.back, 58, -9.0, 0.5, "v3"), (f.back, 70, -13.0, -0.45, "v2"), (f.back, 63, -12.0, 0.5, "v3")]
    return ev


# ---- 扬琴 ----

YQ_PITCHES = [51, 53, 55, 58, 60, 63, 65, 67, 68, 70, 72, 75, 77, 79, 80, 82, 84, 87]
# the run of eighths over one loop, in the notes each chord holds, the top is 新
RIPPLE = {"Bb": (70, 75, "top", 79, 72, 77), "Eb/G": (70, 75, "top", 79, 72, 77), "Cm": (70, 75, "top", 79, 72, 77), "Ab": (68, 75, "top", 80, 72, 77)}


def yq_note(m, vel_db, r):
    y = bank("yq", m)
    n = int(np.argmax(np.abs(y).max(1) > 0.02 * np.abs(y).max()))
    x = y[n : n + int(3.0 * SR)].mean(1)
    k = np.arange(len(x)) / SR
    return x * (1 - sstep((k - 2.6) / 0.4)) * db(vel_db + r.normal(0, 0.8))


def yangqin(f, total):
    """(seconds, midi, dB, pan). Enters by degrees: 新 alone, then the loop, then eighths, then the tremolo of the run; one rolled chord into the name."""
    ev = []
    r = np.random.default_rng(SEED + 11)
    for n in range(f.cap, f.ink):
        k = (n - f.LOOP) % 3
        loud = 1.5 if k == 1 else 0.0
        if n < f.days:  # 苟日新: only 新
            if k == 1:
                ev.append((float(f.at(n)), f.top(n + 1), -3.0, 0.25))
        elif n < f.again:  # 日日新: the loop
            ev.append((float(f.at(n)), f.top(n + 1) if k == 1 else CELL[k], -5.0 + loud, 0.25))
        else:  # 又日新: eighths
            six = RIPPLE[f.chord_at(n)]
            for j in range(2):
                m = six[k * 2 + j]
                m = f.top(n + 1) if m == "top" else m
                ev.append((float(f.at(n + j / 2)), m, (-5.0 if j == 0 else -9.0) + loud + (n - f.again) * 0.08, 0.25 - 0.5 * j))
    # the run: 轮音, a tremolo on the note that is new, closing up from eighths to fast, opening to a chord on the last beat
    a, b = float(f.at(f.run)), float(f.at(f.sun))
    t = a
    while t < b - 0.02:
        x = (t - a) / (b - a)
        ev.append((t, 68 if x < 0.5 else 80, -13.0 + 11.0 * x, 0.25 if len(ev) % 2 else -0.25))
        ev.append((t + 0.004, 75, -19.0 + 11.0 * x, 0.0))
        t += float(np.interp(x, [0, 0.45, 1], [0.21, 0.11, 0.058]))
    # the sweep into the name: four notes up, the last on the name itself
    back = float(f.at(f.back))
    for i, m in enumerate((63, 70, 75, 79, 87)):
        ev.append((back - (4 - i) * 0.07, m, -8.0 - (4 - i) * 0.6, -0.3 + 0.15 * i))
    return [e for e in ev if e[0] < total]


# ---- pad and sub ----


def chord_env(t, f, name):
    """One note of a chord: 0 or 1 through the piece, moving over about a beat as the chords change."""
    g = np.zeros_like(t)
    for (b0, c0), (b1, _) in zip(f.harmony, f.harmony[1:] + [(1e9, None)]):
        if c0 != name:
            continue
        a = -1.0 if b0 < 0 else float(f.at(b0))
        e = t[-1] + 2.0 if b1 > 1e8 else float(f.at(b1))
        g = np.maximum(g, sstep((t - a) / 0.42 + 1) * (1 - sstep((t - e) / 0.42 + 1)))
    return g


def pad(t, f):
    cap, end, back, stop = f.marks()
    ink, still, run = float(f.at(f.ink)), f.still_t, float(f.at(f.run))
    dur = t[-1]
    swell = curve(t, [(0, -50), (cap * 0.5, -22), (cap, -9), (cap + 1, -6), (ink - 0.5, -2), (ink + 0.5, -13), (still, -17), (run - 0.1, -17), (run + 0.2, -7), (end - 0.5, 4), (end, 4.5)])
    a = swell * gate_down(t, end + 0.27, 30) + db(-4.0) * gate_up(t, back - 0.37, 20) * gate_down(t, stop + 0.27, 30)
    # opens through 又日新, falls with the ink over a beat, opens again wider in the run; shuts in 0.25 s on the sunrise, 0.35 s open on the name
    pts = [(0, 120), (cap * 0.5, 180), (cap - 0.05, 300), (cap + 0.1, 620), (float(f.at(f.again)), 750), (ink - 0.3, 1300), (ink + 0.6, 240), (run - 0.1, 200), (end - 0.6, 2600), (end, 3200), (end + 0.25, 45), (back - 0.35, 45), (back, 1000), (stop, 800), (stop + 0.25, 45), (dur, 45)]
    p = np.array(pts)
    fc = np.exp(np.interp(t, p[:, 0], np.log(p[:, 1])))
    res = np.interp(t, [0, end, end + 0.01, end + 0.25, end + 0.3, back - 0.36, back - 0.35, back, back + 0.15, dur], [1, 1, 5, 5, 1, 1, 6, 6, 1, 1])
    want = {}
    for c, notes in CHORDS.items():
        for stem, m, g in notes:
            want.setdefault((stem, m), {})[c] = g
    out = np.zeros((len(t), 2))
    for (stem, m), gains in want.items():
        y = bank(stem, m)
        ratio = 2.0 ** (-measured_cents(y, m) / 1200.0)
        n = min(len(y), len(t))
        y = y[: n + SR]
        rms = np.sqrt((y[int(3 * SR) : int(20 * SR)] ** 2).mean())
        x = ensemble(y, SEED + m + len(stem) * 100, ratio)[:n] * 0.1 / rms
        e = sum(chord_env(t[:n], f, c) * db(g) for c, g in gains.items())
        out[:n] += x * e[:, None]
    return sweep_lowpass(out * a[:, None], t, fc, res)


def sub(t, f):
    cap, end, back, stop = f.marks()
    ink, run = float(f.at(f.ink)), float(f.at(f.run))
    s = cap / 8.5
    rise = curve(t, [(0, -75), (1 * s, -59), (2 * s, -48), (4 * s, -34), (6 * s, -24), (8 * s, -18), (cap - 0.02, -17), (cap + 0.12, -12), (ink - 0.2, -10.5), (ink + 0.4, -24), (run - 0.05, -26), (run + 0.3, -13), (end, -9.5)])
    a = rise * gate_down(t, end, 150) + db(-18.0) * gate_up(t, back - 0.28, 230) * gate_down(t, stop, 220)
    points = [(max(0.0, float(f.at(b))), SUB[c]) for b, c in f.harmony if b >= 0]
    hz = np.full_like(t, 38.89)
    for at, v in points:  # a quick slide, as a bass player would
        hz = hz + (v - hz) * sstep((t - at) / 0.09)
    hz = hz * (1 + 0.42 * np.exp(-(((t - cap - 0.05) / 0.04) ** 2)))
    ph = 2 * np.pi * np.cumsum(hz) / SR
    x = np.sin(ph) + 0.42 * np.sin(2 * np.pi * np.cumsum(hz + 3.3) / SR + 1.1) + 0.03 * np.sin(3 * ph + 0.9)
    return a * x


def air(t, f, rng):
    cap, end, back, stop = f.marks()
    ink, run = float(f.at(f.ink)), float(f.at(f.run))
    g = curve(t, [(0, -90), (cap * 0.3, -60), (cap, -47), (ink - 0.3, -42), (ink + 0.4, -60), (run, -62), (end - 0.2, -34), (end, -32)])
    g = g * gate_down(t, end, 30) + db(-55.0) * gate_up(t, back - 0.2, 200) * gate_down(t, stop, 60)
    n = lowpass(highpass(rng.normal(size=(len(t), 2)), 6000, 4), 15000, 4)
    return n / n.std() * g[:, None]


# ---- the mix ----


def render(shots=None, name="C"):
    os.makedirs(OUT, exist_ok=True)
    f = Form(shots)
    dur = f.total + 2.0
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(SEED)
    cap, end, back, stop = f.marks()
    print(f"film {f.total:.2f} s, seconds per beat {np.round(np.diff(f.t) / np.diff(f.n), 3).tolist()} = {np.round(60 * np.diff(f.n) / np.diff(f.t), 1).tolist()} BPM", flush=True)
    for label, b in [("苟日新", f.cap), ("日日新", f.days), ("又日新", f.again), ("Eb/G", f.eg), ("Cm", f.cm2), ("一滴", f.ink), ("静", f.still), ("新音 Ab", f.run), ("日出", f.sun), ("名字", f.back)]:
        print(f"  {label:<6} beat {b:3d} at {float(f.at(b)):6.2f} s")

    voices = np.zeros((len(t), 2))
    voice = Voice(SEED + 2)
    for n, m, g, p, _ in lead_notes(f):
        hum = 0.0 if n in f.n else rng.normal(0, 0.012)
        add(voices, voice.note(m, breath=0.45 if (f.sun <= n < f.back or f.ink <= n < f.still) else 1.0), float(f.at(n)) + hum, db(g) * 0.16, p)
    lead_bus = voices * db(LEAD_DB)

    yq_bus = np.zeros((len(t), 2))
    r = np.random.default_rng(SEED + 12)
    for at, m, g, p in yangqin(f, dur):
        add(yq_bus, yq_note(m, g, r), at + r.normal(0, 0.004), db(-11.0), p)

    bell_bus = np.zeros((len(t), 2))
    for at, hz, g, s in [(cap, 155.56, -27.0, 21), (float(f.at(f.days)), 130.81, -27.0, 22), (float(f.at(f.again)), 233.08, -27.0, 23), (f.still_t, 311.13, -19.0, 24), (end, 155.56, -29.0, 3), (back, 311.13, -30.0, 4)]:
        add(bell_bus, bell(hz, SEED + s), at, db(g), 0.0)

    sub_bus = sub(t, f)[:, None] * [1, 1]
    pad_bus = pad(t, f)
    air_bus = air(t, f, rng)

    ir = room(SEED + 5)
    still, run = f.still_t, float(f.at(f.run))
    send = np.interp(t, [0, cap, still, still + 0.1, run, end, end + 0.2, back - 0.3, back], [-17, -9, -6, -6, -8, -5, -9, -9, -6])
    stems = {
        "lead": lead_bus + wet(lead_bus, ir) * db(send)[:, None],
        "yangqin": yq_bus + wet(yq_bus, ir) * db(-11.0),
        "sub": sub_bus,
        "pad": pad_bus + wet(pad_bus, ir) * db(-14.0),
        "air": air_bus,
        "bell": bell_bus + wet(bell_bus, ir) * db(-5.0),
    }
    mix = sum(stems.values())

    ink = float(f.at(f.ink))
    width = np.interp(t, [0, cap, ink - 0.1, ink + 0.5, run, end - 0.01, end, back, dur], [0.25, 0.75, 0.9, 0.5, 0.5, 1.0, 0.85, 1.0, 1.0])
    mid_ch, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = highpass(side, 90, 2) * width
    mix = highpass(np.stack([mid_ch + side, mid_ch - side], 1), 18, 2)

    k = np.clip((t - (f.total - 0.28)) / 0.28, 0, 1)
    mix *= (1 - sstep(k))[:, None]
    mix = mix[: int(f.total * SR)]

    tmp = os.path.join(OUT, f"_tmp_{name}.wav")
    gain = 1.0
    for _ in range(3):
        out, gmin = limiter(mix * gain, CEILING_DB - 0.4)
        sf.write(tmp, out, SR, subtype="PCM_24")
        i, pk = lufs(tmp)
        gain *= db(TARGET_LUFS - i)
    out, gmin = limiter(mix * gain, CEILING_DB - 0.4)
    path = os.path.join(OUT, f"mix_{name}.wav")
    sf.write(path, out, SR, subtype="PCM_24")
    os.remove(tmp)
    i, pk = lufs(path)
    print(f"{path}: {i:.1f} LUFS, peak {pk:.1f} dBTP, deepest limiting {20 * np.log10(gmin):.1f} dB", flush=True)
    d = os.path.join(OUT, f"stems_{name}")
    os.makedirs(d, exist_ok=True)
    for k, v in stems.items():
        sf.write(os.path.join(d, f"{k}.wav"), v[: int(f.total * SR)] * gain, SR, subtype="FLOAT")
    return f


if __name__ == "__main__":
    render()
