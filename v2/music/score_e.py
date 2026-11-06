"""Version E: as close to the original as we may go.

    python3 -I v2/music/score_e.py       out/v2/music/mix_E.wav, stems_E/

Not used: the recording itself, its sounds, and its melody note for note (its loop is F#4 E5 A4). Taken from it by measurement:
  key            D major, the same pedal; our loop has the same three pitch classes in another order and register: A4 F#5 E5
  timing         neighbouring notes are .39-.66 s apart, long and short in turn, not a metronome. Ours: each voice's loop swings, so voices interlock unevenly
  note           a broad bite at the start, then the fall. Ours sits 4-5 dB under its peaks at 500-2500 Hz with half its contrast, so the note is louder and its attack sharper
  arc            the level of each octave band follows the original's through the whole build, on a time map (film seconds to original seconds). Only smoothed band levels are read from the original, never its signal

Dropped, not in the original: the yangqin, the bell, the Ab. Chop is the same choir sample with the same stand-ins as score.py; samples are played a semitone down from the bank.
"""

import os
import sys

import numpy as np
import soundfile as sf
from scipy.ndimage import gaussian_filter1d
from scipy.signal import istft, stft

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as base  # noqa: E402
from score import CEILING_DB, OUT, SEED, SR, TARGET_LUFS, Voice, add, air, bandpass, bank, curve, db, ensemble, gate_down, gate_up, highpass, limiter, lufs, measured_cents, room, sstep, sub, sweep_lowpass, wet  # noqa: E402
from score_d import PAD as PAD_D, Steady  # noqa: E402

UP = {("str", 55): 3.0, ("low", 55): 3.0, ("high", 67): 3.0, ("str", 51): 4.0, ("high", 63): 4.0}  # the third, measured .44-.64 against the original's .65-1; the tonic, .28-.55 against .70-.93
PAD = [(st, m, g + UP.get((st, m), 0.0)) for st, m, g in PAD_D]

base.SUB_HZ = 36.71  # D1
DOWN = 2.0 ** (-1.0 / 12.0)  # the banks are in Eb. Everything below is written in Eb midi and sounds in D
CELL = (70, 79, 77)  # sounds A4 F#5 E5
HOME = (70, 79, 75)  # sounds A4 F#5 D5
HALF = 0.26
SWING = (0.0, 0.085, 0.0)  # of a second: long after the low note, short after the high one. Read from the original's gaps
LEAD_DB = 5.0  # against the 500-2500 Hz peaks of the original (measured); replaces score.LEAD_DB, -2, set on an older mix
BANDS = [30, 60, 120, 250, 500, 1000, 2000, 4000, 8000, 16000]


class Sung(Voice):
    def sample(self, m):
        x = super().sample(m)
        if not hasattr(self, "done"):
            self.done = set()
        if m not in self.done:
            self.trim[m] += 100.0  # read a semitone slow
            self.done.add(m)
        return x

    def note(self, m, gate=0.21, length=2.2, breath=1.0):
        r = self.rng
        x = self.sample(m)
        t = np.arange(int(length * SR)) / SR
        cents = r.uniform(35, 85) * np.exp(-t / 0.09) - 22.0 * (1 - np.exp(-t / 0.22)) - 8.0 - self.trim[m]
        start = (0.10 + r.uniform(0, 0.06)) * SR
        y = np.interp(start + np.cumsum(2.0 ** (cents / 1200.0)), np.arange(len(x)), x)
        att = sstep(t / 0.010)
        y *= att * db(-4.0 * t / 0.17) * (1 - sstep((t - gate) / 0.03)) + att * db(-60.0 * t / 1.6) * db(-20.0)
        n = int(0.06 * SR)
        i = r.integers(0, len(self.mid) - n)  # the bite: a breath of consonant, wide, gone in 30 ms
        y[:n] += 0.11 * breath * self.mid[i : i + n] * np.exp(-t[:n] / 0.012) * att[:n]
        nenv = sstep(t / 0.012) * (1 - sstep((t - gate - 0.015) / 0.04))
        k = np.count_nonzero(nenv > 0)
        j = r.integers(0, len(self.hi) - k)
        y[:k] += breath * 0.03 * self.hi[j : j + k] * nenv[:k]
        return y


def top(n, c):
    """Constant, as in the original, until the very end."""
    if n >= c.sun:
        return 79
    return 87 if n >= c.sun - 3 else 82 if n >= c.sun - 9 else 79


def lead_notes(c):
    """(beat, midi, dB, pan, voice, seconds late)."""
    rng = np.random.default_rng(SEED + 1)
    third = int(np.ceil(c.to_beat(7.0)))  # the original adds a voice about here
    ev = [(0, 79, 0.0, 0.0, "v1", 0.0)]

    def note(n, phase):
        k = (n - phase) % 3
        return (top(n + 1, c) if k == 1 else CELL[k]), SWING[k] + rng.normal(0, 0.014)

    for n in range(2, c.sun):
        lift = np.interp(n, [2, c.canon, c.canon + 1, c.cap, c.sun - 1], [3.0, 3.0, 6.0, 5.0, 7.0])
        m, dt = note(n, c.LOOP)
        ev.append((n, m, -3.0 + lift + rng.normal(0, 0.5), 0.0, "v1", dt))
        if n >= c.canon:
            m, dt = note(n, c.LOOP + 1)
            ev.append((n, m, -6.0 + lift + rng.normal(0, 0.7), -0.45, "v2", dt + HALF))  # the original's gaps around its 4.4 s are .27, .27: the second voice falls between the first's notes
        if n >= third:
            m, dt = note(n, c.LOOP + 2)
            ev.append((n, m - 12, -8.0 + lift + rng.normal(0, 0.7), 0.5, "v3", dt))
        if n >= c.cap:
            m, dt = note(n, c.LOOP + 1)
            ev.append((n, min(m, 77) - 24, -11.0 + lift + rng.normal(0, 0.7), -0.25, "v5", dt))
        if n >= c.mid:
            m, dt = note(n, c.LOOP)
            hi = m + 12
            ev.append((n, hi if hi <= 87 else hi - 12, -17.0 + lift + rng.normal(0, 0.7), 0.7, "v4", dt))
    for n in range(c.sun, c.back - 2):
        m, dt = note(n, c.LOOP)
        ev.append((n, m, -7.0 + (n - c.sun) * 0.7 + rng.normal(0, 0.5), 0.0, "v1", dt))
    ev += [(c.back - 2, HOME[0], -5.0, 0.0, "v1", 0.0), (c.back - 1, HOME[1], -5.0, 0.0, "v1", 0.0)]
    ev += [(c.back, HOME[2], -3.0, 0.0, "v1", 0.0), (c.back, 58, -9.0, 0.5, "v3", 0.0), (c.back, 67, -13.0, -0.45, "v2", 0.0), (c.back, 63, -12.0, 0.5, "v3", 0.0)]
    return ev


def pad(t, c):
    cap, end, back, stop = c.marks()
    dur = t[-1]
    swell = curve(t, [(0, -50), (cap * 0.5, -22), (cap, -9), (cap + 1, -6), (end - 3, -1), (end, 4)])
    a = swell * gate_down(t, end + 0.27, 30) + db(-4.0) * gate_up(t, back - 0.37, 20) * gate_down(t, stop + 0.27, 30)
    p = np.array([(0, 120), (cap * 0.5, 180), (cap - 0.05, 320), (cap + 0.1, 650), (end - 3, 1300), (end, 2800), (end + 0.25, 45), (back - 0.35, 45), (back, 1000), (stop, 800), (stop + 0.25, 45), (dur, 45)])
    fc = np.exp(np.interp(t, p[:, 0], np.log(p[:, 1])))
    res = np.interp(t, [0, end, end + 0.01, end + 0.25, end + 0.3, back - 0.36, back - 0.35, back, back + 0.15, dur], [1, 1, 5, 5, 1, 1, 6, 6, 1, 1])
    out = np.zeros((len(t), 2))
    for stem, m, g in PAD:
        y = bank(stem, m)
        ratio = 2.0 ** (-measured_cents(y, m) / 1200.0) * DOWN
        n = min(len(y), len(t))
        y = y[: n + SR]
        rms = np.sqrt((y[int(3 * SR) : int(20 * SR)] ** 2).mean())
        out[:n] += ensemble(y, SEED + m + len(stem) * 100, ratio)[:n] * db(g) * 0.1 / rms
    return sweep_lowpass(out * a[:, None], t, fc, res)


# ---- the arc: band levels follow the original's ----


def band_levels(x):
    """Octave-band power against time, smoothed. Returns frame times and (bands, frames)."""
    f, tt, Z = stft(x.mean(1), SR, nperseg=2048, noverlap=2048 - 256)
    P = np.abs(Z) ** 2
    L = np.stack([P[(f >= a) & (f < b)].sum(0) for a, b in zip(BANDS, BANDS[1:])])
    return tt, gaussian_filter1d(L, 0.3 * SR / 256, axis=1, mode="nearest")


def follow(mix, t, c, ref_levels, max_db=12.0):
    """A slow gain per octave band so that the mix's levels follow the original's, up to the sunrise; nothing after it."""
    rt, rL = ref_levels
    film = np.array([0.0, float(c.at(2)), c.first_caption, c.sunrise - 0.05])
    orig = np.array([0.0, 1.3, 8.5, 16.05])  # the first note after the opening one, the low voice's entry, the shut
    ft, fL = band_levels(mix)
    want = np.stack([np.interp(np.interp(ft, film, orig), rt, rL[i]) for i in range(len(BANDS) - 1)])
    g = np.clip(10 * np.log10((want + 1e-14) / (fL + 1e-14)), -max_db, max_db)
    g = gaussian_filter1d(g, 0.25 * SR / 256, axis=1, mode="nearest")
    g *= (1 - sstep((ft - (c.sunrise - 0.4)) / 0.35))[None, :]  # out before the cut, so the shut stays ours
    centres = np.sqrt(np.array(BANDS[:-1]) * np.array(BANDS[1:]))
    out = []
    for ch in range(2):
        f, tt, Z = stft(mix[:, ch], SR, nperseg=2048, noverlap=2048 - 256)
        lf = np.log2(np.maximum(f, 1.0))
        H = np.stack([np.interp(lf, np.log2(centres), g[:, k]) for k in range(g.shape[1])], 1)
        _, y = istft(Z * db(H), SR, nperseg=2048, noverlap=2048 - 256)
        out.append(y[: len(mix)])
    print("band gains applied, dB, median over the build:", np.round(np.median(g[:, ft < c.sunrise - 0.5], axis=1), 1).tolist(), flush=True)
    return np.stack(out, 1)


def render(shots=None, name="E"):
    os.makedirs(OUT, exist_ok=True)
    c = Steady(shots)
    dur = c.total + 2.0
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(SEED)
    cap, end, back, stop = c.marks()
    print(f"film {c.total:.2f} s; BPM {np.round(60 * np.diff(c.n) / np.diff(c.t), 1).tolist()}; beats {c.n.tolist()}", flush=True)

    voices = np.zeros((len(t), 2))
    voice = Sung(SEED + 2)
    for n, m, g, p, _, dt in lead_notes(c):
        add(voices, voice.note(m, breath=0.45 if c.sun <= n < c.back else 1.0), float(c.at(n)) + dt, db(g) * 0.16, p)
    lead_bus = voices * db(LEAD_DB)

    ir = room(SEED + 5, rt=3.2)  # longer than score.py's 2.4: the original's gaps fill as it builds
    send = np.interp(t, [0, cap, end, end + 0.2, back - 0.3, back], [-19, -13, -7, -11, -11, -8])
    p = pad(t, c)
    stems = {"lead": lead_bus + wet(lead_bus, ir) * db(send)[:, None], "sub": sub(t, c)[:, None] * [1, 1], "pad": p + wet(p, ir) * db(-12.0), "air": air(t, c, rng)}
    mix = sum(stems.values())
    width = np.interp(t, [0, cap, end - 0.01, end, back, dur], [0.25, 0.75, 0.95, 0.85, 1.0, 1.0])
    mid_ch, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = highpass(side, 90, 2) * width
    mix = highpass(np.stack([mid_ch + side, mid_ch - side], 1), 18, 2)

    ref, sr = sf.read(os.path.join(OUT, "ref.wav"), always_2d=True)
    if sr != SR:
        raise SystemExit(f"ref.wav sample rate {sr}")
    ref_levels = band_levels(ref)
    # the levels only mean something at the master's level: first bring ours near
    mix *= db(-3.0)
    for _ in range(2):
        mix = follow(mix, t, c, ref_levels)

    k = np.clip((t - (c.total - 0.28)) / 0.28, 0, 1)
    mix *= (1 - sstep(k))[:, None]
    mix = mix[: int(c.total * SR)]

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


if __name__ == "__main__":
    render()
