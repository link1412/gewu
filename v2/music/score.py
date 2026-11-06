"""The film's music. Our own notes; the feel is taken from what was measured on ref/opus55.mp4 (the recording is not used and no note of it is copied).

    python3 -I v2/music/score.py A       out/v2/music/mix_A.wav, stems_A/       the loop rises in fourths
    python3 -I v2/music/score.py B       out/v2/music/mix_B.wav, stems_B/       the loop goes low, high, middle: the original's shape, other notes

Everything that lands on a picture is read from v2/cut.json: first caption, last shot, the name. Change the cut and run again. Banks: see README.md.

Measured on the original (see README.md), and kept here:
  lead      a chopped human voice (heard as one; the nearest of 18 real samples by numbers is Choir Aahs). About 200 ms, falling 30-70 cents, a long reverb behind it
  form      three-note loop at about 113 BPM; the same loop entering again one beat later, as a canon; a mono sub rising from nothing; air rising 25 dB;
            the sound opening from mono to wide
  pad       the loudest thing in the build: a thick chord under a low-pass filter that opens through the piece, shuts in 0.25 s on the cut to the title, and sweeps open
            in 0.35 s into the return. That shut and sweep is the original's breath.
  level     -16.4 LUFS integrated, -0.6 dBTP peak

Ours, not theirs:
  key and notes  Eb pentatonic, 宫调. Three words 苟日新, tones low / falling / high: 依字行腔. Its highest note, 新, climbs with each caption.
  ending         the last note is the tonic, the only time the lead lands on it.
  bronze         one bell, modal synthesis, on the cut to the sunrise and on the name. Not in the original.

Stand-ins: the lead is a choir sample chopped short, not a solo singer, with breath added because the sample lacks it. The bell's partials are estimates, not measured from a 编钟.
Keyscape Harmochord is a reed organ: recorded free reeds, standing in for 笙.
"""

import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d
from scipy.signal import butter, fftconvolve, istft, sosfilt, stft

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from film import FPS, SLOW, shown  # noqa: E402  the picture's own timing

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "v2", "music")
BANK = os.path.join(OUT, "bank")
BEAT0 = 60.0 / 113.0  # the original's tempo, seconds per beat
LEAD_DB = -2.0  # The whole lead, every voice and its reverb
TARGET_LUFS = -16.4
CEILING_DB = -1.0
SEED = 7
SUB_HZ = 38.89  # Eb1

# loop, position of its highest note, the three notes that come home on the name
CELLS = {"A": ([67, 72, 77], 2, [67, 72, 75]), "B": ([70, 77, 72], 1, [70, 77, 75])}

# Eb major with its ninth and sixth, spread as a low chord: the third (G) is what makes it warm. (bank, midi, dB)
PAD = [("str", 39, -8), ("str", 46, -5), ("str", 51, -9), ("str", 53, -10), ("str", 55, -9), ("str", 58, -11), ("str", 60, -18),
       ("low", 39, -15), ("low", 46, -13), ("low", 51, -17), ("low", 55, -19), ("low", 58, -20),
       ("high", 58, -17), ("high", 63, -15), ("high", 65, -17), ("high", 67, -17)]  # fmt: skip; strings 63, 65, 67 are out: their 1st and 2nd partials are 32 cents apart, no single ratio tunes them


def db(x):
    return 10.0 ** (np.asarray(x, float) / 20.0)


def sstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def bandpass(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x, axis=0)


def highpass(x, f, order=4):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x, axis=0)


def lowpass(x, f, order=4):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x, axis=0)


def bank(stem, m):
    p = os.path.join(BANK, f"{stem}_{m}.wav")
    if not os.path.exists(p):
        raise SystemExit(f"missing {p}: render the banks, see README.md")
    y, sr = sf.read(p, always_2d=True)
    if sr != SR:
        raise SystemExit(f"{p}: sample rate {sr}")
    return y


# ---- the cut gives the clock ----


class Clock:
    """Beat number -> seconds, a piecewise line through the points where a beat must land on a picture.

    The form stays and the cut gives its numbers: how many beats fit each stretch at the original's tempo, with the loop beginning anew on the first caption and on the sunrise.
    Times are what the film shows, film.shown: a shot's frames with its slow-down, not its rendered `len`."""

    LOOP = 3  # the loop starts here. Beat 0 is a note alone; beat 2, on the second shot, is the loop's last note as a pick-up
    SWEEP = 0.35  # the filter opens over this long, starting as the name starts to fade in
    NAME_K = 84, 96  # film.py: the name fades in over these rendered frames of the last shot

    def __init__(self, shots=None):
        shots = shots or json.load(open(os.path.join(ROOT, "v2", "cut.json")))["shots"]
        self.shots = shots
        t = np.cumsum([0] + [shown(s) for s in shots]) / FPS
        where = lambda test: next(i for i, s in enumerate(shots) if test(s))
        cap = where(lambda s: s.get("caption"))
        end = where(lambda s: s.get("end"))
        self.total = float(t[-1])
        fit = lambda a, b: (t[b] - t[a]) / BEAT0  # beats between two cuts, at the original's tempo
        n3 = 2 + max(1, round(fit(1, 2)))
        n4 = n3 + max(1, round(fit(2, 3)))
        self.cap = self.LOOP + 3 * round((n4 + fit(3, cap) - self.LOOP) / 3)
        self.sun = self.cap + 3 * round(fit(cap, end) / 3)
        self.beat = float((t[end] - t[cap]) / (self.sun - self.cap))
        self.first_caption, self.sunrise = float(t[cap]), float(t[end])
        first, slow = shots[end].get("first", 0), shots[end].get("slow", SLOW)
        self.name_in = float(t[end] + (self.NAME_K[0] - first) * slow / FPS)
        self.name_full = float(t[end] + (self.NAME_K[1] - first) * slow / FPS)
        self.back = self.sun + round((self.name_in + self.SWEEP - t[end]) / self.beat)
        self.n = np.array([2, n3, n4, self.cap, self.sun, self.back])
        self.t = np.array([t[1], t[2], t[3], t[cap], t[end], self.name_in + self.SWEEP])
        gaps = np.diff(self.t) / np.diff(self.n)
        if gaps.min() < 0.44 or gaps.max() > 0.62:
            raise SystemExit(f"seconds per beat {np.round(gaps, 3).tolist()} between beats {self.n.tolist()}: too far from the original's {BEAT0:.3f} s, the cut has moved, rewrite the form")
        self.canon = int(np.ceil(self.to_beat(4.0) - 1e-6))  # the same loop again, one beat late, from about 4 s as measured on the original
        self.mid = self.cap + (self.sun - self.cap) // 2  # the climax's two voices enter
        # the top note climbs with the captions: 日日新, 又日新, then on the last two loops before the cut
        self.rise = [int(round(self.to_beat(t[where(lambda s: s.get("caption") == c)]))) for c in ("日日新", "又日新")] + [self.sun - 4, self.sun - 1]

    def to_beat(self, sec):
        return float(np.interp(sec, self.t, self.n))

    def at(self, n):
        n = np.asarray(n, float)
        out = np.interp(n, self.n, self.t)
        out = np.where(n < self.n[0], self.t[0] + (n - self.n[0]) * self.beat, out)
        return np.where(n > self.n[-1], self.t[-1] + (n - self.n[-1]) * self.beat, out)

    def marks(self):
        back = float(self.at(self.back))
        return float(self.at(self.cap)), float(self.at(self.sun)), back, min(back + 0.3, self.total - 0.05)


# ---- the lead: a voice, chopped ----


class Voice:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.hi = bandpass(self.rng.normal(size=8 * SR), 6500, 9200, 8)  # the gap at 5.2-6.5 kHz is measured
        self.mid = bandpass(self.rng.normal(size=8 * SR), 2000, 5000)
        self.hi /= self.hi.std()
        self.mid /= self.mid.std()
        self.notes = {}
        self.trim = {}

    def sample(self, m):
        if m not in self.notes:
            x = bank("voice", m).mean(1)
            self.trim[m] = measured_cents(bank("voice", m), m, 0.10, 0.40)  # the read part runs up to 13 cents off the note, unlike the sustain
            a = x[int(0.3 * SR) : int(1.8 * SR)]
            x = x + 1.6 * bandpass(x, 2400, 4600, 2)  # the sample is darker up here than the original's voice (+8 dB, measured against it)
            self.notes[m] = x * 0.7 / np.sqrt((a**2).mean())  # a sine of amplitude 1, so that gains mean the same on every note
        return self.notes[m]

    def note(self, m, gate=0.205, length=1.6, breath=1.0):
        r = self.rng
        x = self.sample(m)
        t = np.arange(int(length * SR)) / SR
        cents = r.uniform(25, 65) * np.exp(-t / 0.11) - 22.0 * (1 - np.exp(-t / 0.22)) - 8.0 - self.trim[m]  # measured: +10..+90 falling to about -20 by 300 ms; centred on the note over the 200 ms
        start = (0.10 + r.uniform(0, 0.06)) * SR  # past the sample's slow swell: this is the chop
        y = np.interp(start + np.cumsum(2.0 ** (cents / 1200.0)), np.arange(len(x)), x)
        att = sstep(t / 0.028)
        env = att * db(-4.0 * t / 0.17) * (1 - sstep((t - gate) / 0.03)) + att * db(-60.0 * t / 1.3) * db(-20.0)
        y *= env
        nenv = sstep(t / 0.015) * (1 - sstep((t - gate - 0.015) / 0.04))
        n = np.count_nonzero(nenv > 0)
        i = r.integers(0, len(self.hi) - n)
        y[:n] += breath * (0.03 * self.hi[i : i + n] + 0.008 * self.mid[i : i + n]) * nenv[:n]
        return y


def add(bus, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(bus):
        return
    n = min(len(x), len(bus) - i)
    bus[i : i + n, 0] += x[:n] * gain * np.cos((pan + 1) * np.pi / 4)
    bus[i : i + n, 1] += x[:n] * gain * np.sin((pan + 1) * np.pi / 4)


# ---- the score ----


def top_note(n, clk):
    """The highest note of the loop, 新. It rises with each caption and is highest on the last beat before the cut."""
    for limit, m in zip(clk.rise, (77, 79, 82, 84)):  # F5, G5, Bb5, C6
        if n < limit:
            return m
    return 87 if n < clk.sun else 77  # Eb6


def score(clk, cell="A"):
    """(beat, midi, gain dB, pan, voice). A new loop falls on the first caption and on the sunrise."""
    loop, top, home = CELLS[cell]
    start, cap, sun, back = clk.LOOP, clk.cap, clk.sun, clk.back

    def note(n, phase):
        k = (n - phase) % 3
        return top_note(n + 2 - top, clk) if k == top else loop[k]

    ev = [(0, 77, 0.0, 0.0, "v1")]  # one note alone, 新, then the loop
    rng = np.random.default_rng(SEED + 1)
    for n in range(2, sun):
        lift = np.interp(n, [2, clk.canon, clk.canon + 1, cap, clk.mid, sun - 1], [3.0, 3.0, 6.0, 5.0, 4.5, 5.5])
        ev.append((n, note(n, start), -3.0 + lift + rng.normal(0, 0.5), 0.0, "v1"))
        if n >= clk.canon:  # the loop again, one beat late
            ev.append((n, note(n, start + 1), -6.0 + lift + rng.normal(0, 0.7), -0.45, "v2"))
        if n >= cap:  # an octave down, two beats late
            ev.append((n, note(n, start + 2) - 12, -8.0 + lift + rng.normal(0, 0.7), 0.5, "v3"))
        if n >= clk.mid:
            hi = note(n, start) + 12
            ev.append((n, hi if hi <= 87 else hi - 12, -17.0 + lift + rng.normal(0, 0.7), 0.7, "v4"))  # an octave up, where a voice can still reach
            ev.append((n, min(note(n, start + 1), 77) - 24, -11.0 + lift + rng.normal(0, 0.7), -0.25, "v5"))  # the body of the climax, two octaves down
    # under the rising sun: the loop from the start, alone, far away. The last shot runs fast now, so the lead turns for home here, not after the name
    for n in range(sun, back - 2):
        ev.append((n, note(n, start), -7.0 + (n - sun) * 0.7 + rng.normal(0, 0.5), 0.0, "v1"))
    ev += [(back - 2, home[0], -5.0, 0.0, "v1"), (back - 1, home[1], -5.0, 0.0, "v1")]
    # on the name: everything back, and the lead lands on the tonic, the only time
    ev += [(back, home[2], -3.0, 0.0, "v1"), (back, 58, -9.0, 0.5, "v3"), (back, 70, -13.0, -0.45, "v2"), (back, 63, -12.0, 0.5, "v3")]
    return ev


# ---- sub, pad, air, bell ----


def curve(t, pts):
    """dB against time, a line through pts."""
    p = np.array(pts, float)
    return db(np.interp(t, p[:, 0], p[:, 1]))


def gate_down(t, at, ms=25.0):
    return 1 - sstep((t - at) / (ms / 1000.0))


def gate_up(t, at, ms=25.0):
    return sstep((t - at) / (ms / 1000.0))


def sub(t, clk):
    cap, end, back, stop = clk.marks()
    # the rise, shaped as measured on the original's band under 60 Hz (its 0..8.5 s stretched to our first caption)
    s = cap / 8.5
    rise = curve(t, [(0, -75), (1 * s, -59), (2 * s, -48), (4 * s, -34), (6 * s, -24), (8 * s, -18), (cap - 0.02, -17), (cap + 0.12, -12), (end, -10.5)])
    a = rise * gate_down(t, end, 150) + db(-18.0) * gate_up(t, back - 0.28, 230) * gate_down(t, stop, 220)  # it comes back with the sweep
    f = np.full_like(t, SUB_HZ) * (1 + 0.42 * np.exp(-(((t - cap - 0.05) / 0.04) ** 2)))  # the small upward kick the original has at its 8.5 s
    ph = 2 * np.pi * np.cumsum(f) / SR
    # the roll: the original's band under 60 Hz swings 9.4 dB at about 3.3 Hz, 32 %, not locked to the beat. Two close low tones beating give that.
    x = np.sin(ph) + 0.42 * np.sin(2 * np.pi * np.cumsum(f + 3.3) / SR + 1.1) + 0.03 * np.sin(3 * ph + 0.9)
    return a * x


def sweep_lowpass(x, t, fc, res_db):
    """A low-pass that moves, 24 dB per octave with a resonant bump at the cutoff. On the STFT, so it cannot click or blow up."""
    Y = []
    for c in range(2):
        f, tt, Z = stft(x[:, c], SR, nperseg=2048, noverlap=2048 - 256)
        fcs = np.interp(tt, t, fc)[None, :]
        rs = np.interp(tt, t, res_db)[None, :]
        f = np.maximum(f, 1.0)[:, None]
        H = (1 + (f / fcs) ** 8) ** -0.5 * db(rs * np.exp(-((np.log2(f / fcs) / 0.35) ** 2)))
        _, y = istft(Z * H, SR, nperseg=2048, noverlap=2048 - 256)
        Y.append(y[: len(x)])
    return np.stack(Y, 1)


def measured_cents(y, m, a=5.0, b=20.0):
    """How far a sample is from its note between a and b seconds, weighted over its first partials. Some string samples are 14 cents off, which turns sour against the reeds."""
    seg = y[int(a * SR) : int(b * SR)].mean(1)
    n = 2**20
    S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n=n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f0 = 440.0 * 2.0 ** ((m - 69) / 12.0)
    total, weight = 0.0, 0.0
    for h in (1, 2, 3):
        i = np.where((f > f0 * h * 2 ** (-0.07)) & (f < f0 * h * 2**0.07))[0]
        k = i[S[i].argmax()]
        total += 1200 * np.log2(f[k] / (f0 * h)) * S[k]
        weight += S[k]
    return total / weight


def ensemble(y, seed, ratio=1.0, copies=3):
    """Looped samples are perfectly periodic, which draws a thin straight line. Several players drift against each other by a few cents: a fat line that moves, as in the original."""
    r = np.random.default_rng(seed)
    base = np.arange(len(y), dtype=float)
    out = np.zeros_like(y)
    for i in range(copies):
        spread = 2.0 ** ((i - (copies - 1) / 2) * 6.0 / 1200.0)  # players a few cents apart: the original's low lines are thick, ours were thin even with moving delays
        for c in range(2):
            lfo = sum(a * np.sin(2 * np.pi * r.uniform(*rate) * base / SR + r.uniform(0, 6.28)) for a, rate in [(1.0, (0.12, 0.3)), (0.5, (0.35, 0.7))])
            out[:, c] += np.interp(base * ratio * spread - (r.uniform(4, 22) + 2.4 * lfo) * SR / 1000, base, y[:, c])
    wave = 1 + 0.5 * np.sin(2 * np.pi * r.uniform(0.6, 1.3) * base / SR + r.uniform(0, 6.28))  # the original's low bands swing about 5 dB more than a steady chord does
    return out * wave[:, None] / np.sqrt(copies)


def pad(t, clk):
    cap, end, back, stop = clk.marks()
    dur = t[-1]
    swell = curve(t, [(0, -50), (cap * 0.5, -22), (cap, -9), (cap + 1, -6), (end - 3, -1), (end, 4)])
    a = swell * gate_down(t, end + 0.27, 30) + db(-4.0) * gate_up(t, back - 0.37, 20) * gate_down(t, stop + 0.27, 30)
    # opening through the piece; shut in 0.25 s on the cut; open in 0.35 s into the return; shut again at the end
    pts = [(0, 120), (cap * 0.5, 180), (cap - 0.05, 300), (cap + 0.1, 620), (end - 3, 800), (end, 1500), (end + 0.25, 45), (back - 0.35, 45), (back, 1000), (stop, 800), (stop + 0.25, 45), (dur, 45)]
    p = np.array(pts)
    fc = np.exp(np.interp(t, p[:, 0], np.log(p[:, 1])))
    res = np.interp(t, [0, end, end + 0.01, end + 0.25, end + 0.3, back - 0.36, back - 0.35, back, back + 0.15, dur], [1, 1, 5, 5, 1, 1, 6, 6, 1, 1])
    out = np.zeros((len(t), 2))
    for stem, m, g in PAD:
        y = bank(stem, m)
        ratio = 2.0 ** (-measured_cents(y, m) / 1200.0)
        n = min(len(y), len(t))
        y = y[: n + SR]  # a second more than needed: copies reading faster than real time must not run off the end
        rms = np.sqrt((y[int(3 * SR) : int(20 * SR)] ** 2).mean())  # gains mean the same on every patch
        out[:n] += ensemble(y, SEED + m + len(stem) * 100, ratio)[:n] * db(g) * 0.1 / rms
    return sweep_lowpass(out * a[:, None], t, fc, res)


def air(t, clk, rng):
    cap, end, back, stop = clk.marks()
    g = curve(t, [(0, -90), (cap * 0.3, -60), (cap, -47), (end - 3, -42), (end - 0.2, -34), (end, -32)])
    g = g * gate_down(t, end, 30) + db(-55.0) * gate_up(t, back - 0.2, 200) * gate_down(t, stop, 60)
    n = rng.normal(size=(len(t), 2))
    n = lowpass(highpass(n, 6000, 4), 15000, 4)
    n /= n.std()
    return n * g[:, None]


def bell(f0, seed, length=9.0):
    """One bronze strike with a wooden mallet. Ratios and decays are estimates; each mode is a close pair, which is what makes a bell beat."""
    r = np.random.default_rng(seed)
    t = np.arange(int(length * SR)) / SR
    ratio = [1.0, 1.19, 2.02, 2.41, 2.98, 3.56, 4.22, 5.06, 6.02, 7.1]
    amp = [0.24, 0.22, 0.6, 0.2, 0.5, 0.16, 0.3, 0.14, 0.1, 0.06]  # a quiet, short fundamental: it was the loudest line in the hush, 13 dB over the original at 120-300 Hz, and read as a hum
    tau = [0.7, 0.9, 0.95, 0.8, 0.7, 0.55, 0.42, 0.3, 0.24, 0.18]
    x = np.zeros_like(t)
    for q, a, d in zip(ratio, amp, tau):
        f = f0 * q
        split = r.uniform(0.0006, 0.002)
        x += a * np.exp(-t / d) * (np.sin(2 * np.pi * f * (1 + split) * t + r.uniform(0, 6.28)) + 0.7 * np.sin(2 * np.pi * f * (1 - split) * t + r.uniform(0, 6.28)))
    n = int(0.004 * SR)  # the mallet is 4 ms of contact, which takes the top off
    x = fftconvolve(x, np.hanning(n) / np.hanning(n).sum())[: len(t)]
    knock = bandpass(r.normal(size=int(0.05 * SR)), 300, 2200) * np.exp(-np.arange(int(0.05 * SR)) / (0.008 * SR))
    x[: len(knock)] += 0.6 * knock
    return x * sstep(t / 0.002)


# ---- the room ----


def room(seed, rt=2.4):
    """A hall that takes a moment to bloom, the shape of the original's tails (a plateau about 13 dB down for 250 ms, then falling)."""
    r = np.random.default_rng(seed)
    n = int(rt * 1.6 * SR)
    t = np.arange(n) / SR
    bloom = 1 - np.exp(-t / 0.05)
    ir = np.zeros((n, 2))
    for lo, hi, k, g in [(60, 300, 1.05, 0.9), (300, 1200, 1.0, 1.0), (1200, 4000, 0.72, 0.65), (4000, 14000, 0.42, 0.3)]:
        ns = bandpass(r.normal(size=(n, 2)), lo, hi, 3)
        ir += ns * (g * bloom * db(-60.0 * t / (rt * k)))[:, None]
    pre = int(0.018 * SR)
    ir = np.vstack([np.zeros((pre, 2)), ir])
    return ir / np.sqrt((ir**2).sum(0)).max()


def wet(x, ir):
    out = np.zeros((len(x), 2))
    mono = x.mean(1)
    for c in range(2):
        out[:, c] = fftconvolve(mono, ir[:, c])[: len(x)]
    return out


# ---- the master ----


def limiter(x, ceil_db, look_ms=4.0, rel_ms=90.0):
    ceil = db(ceil_db)
    n = int(look_ms / 1000 * SR)
    peak = np.abs(x).max(1)
    need = np.minimum(1.0, ceil / np.maximum(peak, 1e-9))
    held = minimum_filter1d(need, size=2 * n + 1)
    a = np.exp(-1.0 / (rel_ms / 1000 * SR))
    g = held.copy()
    for i in range(1, len(g)):
        g[i] = min(held[i], a * g[i - 1] + (1 - a) * 1.0)
    w = np.hanning(2 * n + 1)
    g = np.convolve(np.pad(g, n, mode="edge"), w / w.sum(), mode="valid")
    return x * g[:, None], float(g.min())


def lufs(path):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    lines = p[p.rindex("Summary:") :].splitlines()
    i = next(float(s.split()[1]) for s in lines if s.strip().startswith("I:"))
    pk = next(float(s.split()[1]) for s in lines if s.strip().startswith("Peak:"))
    return i, pk


def main():
    cell = sys.argv[1] if len(sys.argv) > 1 else "A"
    if cell not in CELLS:
        raise SystemExit(f"cell must be one of {list(CELLS)}")
    os.makedirs(OUT, exist_ok=True)
    clk = Clock()
    dur = float(clk.total + 2.0)
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(SEED)
    cap, end, back, stop = clk.marks()
    print(f"film {clk.total:.2f} s, beat {clk.beat:.3f} s = {60 / clk.beat:.1f} BPM; beats {clk.n.tolist()} at {np.round(clk.t, 2).tolist()}, seconds per beat {np.round(np.diff(clk.t) / np.diff(clk.n), 3).tolist()}; canon from beat {clk.canon}, top note rises {clk.rise}; first caption {cap:.2f}, sunrise {end:.2f}, sweep from {back - clk.SWEEP:.2f}, back {back:.2f}, name fades in {clk.name_in:.2f}-{clk.name_full:.2f}", flush=True)

    voices = {k: np.zeros((len(t), 2)) for k in ("v1", "v2", "v3", "v4", "v5")}
    voice = Voice(SEED + 2)
    for n, m, g, p, v in score(clk, cell):
        hum = 0.0 if n in clk.n else rng.normal(0, 0.012)  # the original's beats wander by about 40 ms
        add(voices[v], voice.note(m, breath=0.45 if clk.sun <= n < clk.back else 1.0), float(clk.at(n)) + hum, db(g) * 0.16, p)
    lead_bus = sum(voices.values()) * db(LEAD_DB)

    sub_bus = sub(t, clk)[:, None] * [1, 1]
    pad_bus = pad(t, clk)
    air_bus = air(t, clk, rng)
    bell_bus = np.zeros((len(t), 2))
    add(bell_bus, bell(155.56, SEED + 3), end, db(-29.0), 0.0)  # Eb3, under the cut to the sunrise
    add(bell_bus, bell(311.13, SEED + 4), back, db(-30.0), 0.0)  # an octave up, on the name

    ir = room(SEED + 5)
    # the hall grows with the build, which fills the gaps between the notes as in the original; it falls back at the cut and returns with the sweep
    send = np.interp(t, [0, cap, end, end + 0.2, back - 0.3, back], [-17, -9, -5, -9, -9, -6])
    lead_wet = wet(lead_bus, ir) * db(send)[:, None]
    pad_wet = wet(pad_bus, ir) * db(-14.0)
    bell_wet = wet(bell_bus, ir) * db(-5.0)

    stems = {"lead": lead_bus + lead_wet, "sub": sub_bus, "pad": pad_bus + pad_wet, "air": air_bus, "bell": bell_bus + bell_wet}
    mix = sum(stems.values())

    # below 90 Hz is mono; above, the width opens with the build, as measured (L/R correlation 0.97 falling to 0.37)
    width = np.interp(t, [0, cap, end - 0.01, end, back, dur], [0.25, 0.75, 0.95, 0.85, 1.0, 1.0])
    mid_ch, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = highpass(side, 90, 2) * width
    mix = highpass(np.stack([mid_ch + side, mid_ch - side], 1), 18, 2)

    # the film ends on the picture: fade the tail into the last frame
    k = np.clip((t - (clk.total - 0.28)) / 0.28, 0, 1)
    mix *= (1 - sstep(k))[:, None]
    mix = mix[: int(clk.total * SR)]

    tmp = os.path.join(OUT, f"_tmp_{cell}.wav")
    gain = 1.0
    for _ in range(3):
        out, gmin = limiter(mix * gain, CEILING_DB - 0.4)
        sf.write(tmp, out, SR, subtype="PCM_24")
        i, pk = lufs(tmp)
        gain *= db(TARGET_LUFS - i)
    out, gmin = limiter(mix * gain, CEILING_DB - 0.4)
    path = os.path.join(OUT, f"mix_{cell}.wav")
    sf.write(path, out, SR, subtype="PCM_24")
    os.remove(tmp)
    i, pk = lufs(path)
    print(f"{path}: {i:.1f} LUFS, peak {pk:.1f} dBTP, deepest limiting {20 * np.log10(gmin):.1f} dB", flush=True)
    d = os.path.join(OUT, f"stems_{cell}")
    os.makedirs(d, exist_ok=True)
    for k, v in stems.items():
        sf.write(os.path.join(d, f"{k}.wav"), v[: int(clk.total * SR)] * gain, SR, subtype="FLOAT")


if __name__ == "__main__":
    main()
