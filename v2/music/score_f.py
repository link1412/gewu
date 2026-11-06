"""Version F: E's sound, the original's arc played twice.

    python3 -I v2/music/score_f.py       out/v2/music/mix_F.wav, stems_F/

Why: the original builds for about 7.6 s after its low voice enters, and shuts at 16.1 s. E stretched that build over 18.4 s, about 2.4 times, one long slope. Our first 又日新 is at 16.52 s, so the first wave
can run at nearly the original's own length and shut there, on the word "again". 南红's fall, 1.36 s, is the hush (the original's is about 1.25 s). The sweep lands on the next cut. A second, larger wave runs to the sunrise.

Same voice, swing, band-following and limits as score_e.py. The second wave's level is taken from the original's from its 7 s on. That two waves carry more feeling is my reasoning: I cannot hear it.
"""

import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as base  # noqa: E402
from score import BEAT0, CEILING_DB, FPS, OUT, SEED, SR, TARGET_LUFS, add, bank, curve, db, ensemble, gate_down, gate_up, highpass, limiter, lowpass, lufs, measured_cents, room, shown, sstep, sweep_lowpass, wet  # noqa: E402
from score_d import Steady  # noqa: E402
from score_e import BANDS, CELL, HALF, HOME, LEAD_DB, PAD, SWING, DOWN, Sung, band_levels  # noqa: E402

from scipy.ndimage import gaussian_filter1d  # noqa: E402
from scipy.signal import istft, stft  # noqa: E402

SWEEP = 0.35
FIRST = 10 ** (-3.0 / 10)  # the first wave stays 3 dB under the original's levels, so the second is the larger
SUB_HZ = 36.71


class Twice(Steady):
    def __init__(self, shots=None):
        super().__init__(shots)
        shots = self.shots
        t = np.cumsum([0] + [shown(s) for s in shots]) / FPS
        i = next(k for k, s in enumerate(shots) if s.get("caption") == "又日新")
        delta = self.back - self.sun
        self.t_again, self.t_re = float(t[i]), float(t[i + 1])
        loops = lambda a, b: 3 * max(1, round((b - a) / BEAT0 / 3))
        self.again = self.cap + loops(self.first_caption, self.t_again)
        self.re = self.again + 3  # the hush is one loop
        self.sun = self.re + loops(self.t_re, self.sunrise)
        self.back = self.sun + delta
        last = self.t[-1]
        self.n = np.array([self.n[0], self.cap, self.again, self.re, self.sun, self.back])
        self.t = np.array([self.t[0], self.first_caption, self.t_again, self.t_re, self.sunrise, last])
        gaps = np.diff(self.t) / np.diff(self.n)
        if gaps.min() < 0.44 or gaps.max() > 0.62:
            raise SystemExit(f"seconds per beat {np.round(gaps, 3).tolist()} between beats {self.n.tolist()}: the cut has moved, rewrite the form")
        self.canon = int(np.ceil(self.to_beat(4.0) - 1e-6))
        self.third = int(np.ceil(self.to_beat(7.0)))
        self.high = self.re + 3 * ((self.sun - self.re) // 6)  # the top voice waits for the middle of the second wave


def top(n, c):
    """新: F#5 through the first wave, A5 through the second, D6 on its last loop. (Written in Eb midi.)"""
    if n >= c.sun or n < c.re:
        return 79
    return 87 if n >= c.sun - 3 else 82


def lead_notes(c):
    rng = np.random.default_rng(SEED + 1)
    ev = [(0, 79, 0.0, 0.0, "v1", 0.0)]

    def note(n, phase):
        k = (n - phase) % 3
        return (top(n + 1, c) if k == 1 else CELL[k]), SWING[k] + rng.normal(0, 0.014)

    for n in range(2, c.sun):
        hushed = c.again <= n < c.re
        if hushed:  # one voice, far off
            m, dt = note(n, c.LOOP)
            ev.append((n, m, -15.0 + rng.normal(0, 0.4), 0.0, "v1", dt))
            continue
        second = n >= c.re
        lift = np.interp(n, [2, c.canon, c.canon + 1, c.cap, c.again - 1, c.re, c.sun - 1], [3.0, 3.0, 6.0, 5.0, 6.5, 5.5, 7.5])
        m, dt = note(n, c.LOOP)
        ev.append((n, m, -3.0 + lift + rng.normal(0, 0.5), 0.0, "v1", dt))
        if n >= c.canon:
            m, dt = note(n, c.LOOP + 1)
            ev.append((n, m, -6.0 + lift + rng.normal(0, 0.7), -0.45, "v2", dt + HALF))
        if n >= c.third:
            m, dt = note(n, c.LOOP + 2)
            ev.append((n, m - 12, -8.0 + lift + rng.normal(0, 0.7), 0.5, "v3", dt))
        if n >= c.cap:
            m, dt = note(n, c.LOOP + 1)
            ev.append((n, min(m, 77) - 24, -11.0 + lift + rng.normal(0, 0.7), -0.25, "v5", dt))
        if n >= c.high:
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
    cap, a1, re, end = c.first_caption, c.t_again, c.t_re, c.sunrise
    back = float(c.at(c.back))
    stop = min(back + 0.3, c.total - 0.05)
    dur = t[-1]
    swell = curve(t, [(0, -50), (cap * 0.5, -22), (cap, -9), (cap + 1, -6), (a1 - 3, -2), (a1, 2), (a1 + 0.01, 2), (re, -2), (re + 0.5, -4), (end - 3, 0), (end, 5)])
    open_gate = gate_down(t, a1 + 0.27, 30) + gate_up(t, re - SWEEP - 0.02, 20)
    a = swell * np.minimum(open_gate, 1.0) * gate_down(t, end + 0.27, 30) + db(-4.0) * gate_up(t, back - 0.37, 20) * gate_down(t, stop + 0.27, 30)
    p = np.array([(0, 120), (cap * 0.5, 180), (cap - 0.05, 320), (cap + 0.1, 650), (a1 - 2, 1300), (a1, 2600), (a1 + 0.25, 45), (re - SWEEP, 45), (re, 1100), (end - 3, 1700), (end, 3200), (end + 0.25, 45), (back - SWEEP, 45), (back, 1000), (stop, 800), (stop + 0.25, 45), (dur, 45)])
    fc = np.exp(np.interp(t, p[:, 0], np.log(p[:, 1])))
    res = np.interp(t, [0, a1, a1 + 0.01, a1 + 0.25, a1 + 0.3, re - SWEEP - 0.01, re - SWEEP, re, re + 0.15, end, end + 0.01, end + 0.25, end + 0.3, back - 0.36, back - 0.35, back, back + 0.15, dur], [1, 1, 5, 5, 1, 1, 6, 6, 1, 1, 5, 5, 1, 1, 6, 6, 1, 1])
    out = np.zeros((len(t), 2))
    for stem, m, g in PAD:
        y = bank(stem, m)
        ratio = 2.0 ** (-measured_cents(y, m) / 1200.0) * DOWN
        n = min(len(y), len(t))
        y = y[: n + SR]
        rms = np.sqrt((y[int(3 * SR) : int(20 * SR)] ** 2).mean())
        out[:n] += ensemble(y, SEED + m + len(stem) * 100, ratio)[:n] * db(g) * 0.1 / rms
    return sweep_lowpass(out * a[:, None], t, fc, res)


def sub(t, c):
    cap, a1, re, end = c.first_caption, c.t_again, c.t_re, c.sunrise
    back = float(c.at(c.back))
    stop = min(back + 0.3, c.total - 0.05)
    s = cap / 8.5
    rise = curve(t, [(0, -75), (1 * s, -59), (2 * s, -48), (4 * s, -34), (6 * s, -24), (8 * s, -18), (cap - 0.02, -17), (cap + 0.12, -12), (a1, -10.5), (a1 + 0.01, -14), (re - 0.3, -14), (re, -13), (end, -9.5)])
    a = rise * (gate_down(t, a1, 150) + db(-16.0) * gate_up(t, a1 + 0.1, 150) * gate_down(t, re - 0.25, 50) + gate_up(t, re - 0.25, 230)).clip(0, 1) * gate_down(t, end, 150)
    a = a + db(-18.0) * gate_up(t, back - 0.28, 230) * gate_down(t, stop, 220)
    f = np.full_like(t, SUB_HZ) * (1 + 0.42 * np.exp(-(((t - cap - 0.05) / 0.04) ** 2)) + 0.42 * np.exp(-(((t - re - 0.05) / 0.04) ** 2)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return a * (np.sin(ph) + 0.42 * np.sin(2 * np.pi * np.cumsum(f + 3.3) / SR + 1.1) + 0.03 * np.sin(3 * ph + 0.9))


def air(t, c, rng):
    cap, a1, re, end = c.first_caption, c.t_again, c.t_re, c.sunrise
    back = float(c.at(c.back))
    stop = min(back + 0.3, c.total - 0.05)
    g = curve(t, [(0, -90), (cap * 0.3, -60), (cap, -47), (a1 - 0.2, -36), (a1, -34), (a1 + 0.05, -80), (re - 0.3, -80), (re, -46), (end - 0.2, -32), (end, -30)])
    g = g * gate_down(t, end, 30) + db(-55.0) * gate_up(t, back - 0.2, 200) * gate_down(t, stop, 60)
    n = lowpass(highpass(rng.normal(size=(len(t), 2)), 6000, 4), 15000, 4)
    return n / n.std() * g[:, None]


def follow(mix, c, ref_levels, max_db=12.0):
    """Band levels follow the original's in each wave: the first from its start to its shut, the second from its 7 s to its shut. Nothing in the hushes, so those stay ours."""
    rt, rL = ref_levels
    ft, fL = band_levels(mix)
    film = np.array([0.0, float(c.at(2)), c.first_caption, c.t_again - 0.05, c.t_re + 0.15, c.sunrise - 0.05])
    orig = np.array([0.0, 1.3, 8.5, 16.05, 7.0, 16.05])
    mapped = np.where(ft < film[3] + 0.5, np.interp(ft, film[:4], orig[:4]), np.interp(ft, film[4:], orig[4:]))
    want = np.stack([np.interp(mapped, rt, rL[i]) for i in range(len(BANDS) - 1)])
    want = want * np.where(ft < film[3] + 0.5, FIRST, 1.0)
    g = np.clip(10 * np.log10((want + 1e-14) / (fL + 1e-14)), -max_db, max_db)
    g = gaussian_filter1d(g, 0.25 * SR / 256, axis=1, mode="nearest")
    on = (1 - sstep((ft - (c.t_again - 0.4)) / 0.35)) + sstep((ft - (c.t_re + 0.05)) / 0.3) * (1 - sstep((ft - (c.sunrise - 0.4)) / 0.35))
    g *= on[None, :]
    centres = np.sqrt(np.array(BANDS[:-1]) * np.array(BANDS[1:]))
    out = []
    for ch in range(2):
        f, tt, Z = stft(mix[:, ch], SR, nperseg=2048, noverlap=2048 - 256)
        lf = np.log2(np.maximum(f, 1.0))
        H = np.stack([np.interp(lf, np.log2(centres), g[:, k]) for k in range(g.shape[1])], 1)
        _, y = istft(Z * db(H), SR, nperseg=2048, noverlap=2048 - 256)
        out.append(y[: len(mix)])
    return np.stack(out, 1)


def render(shots=None, name="F", notes=None, lines=None, sung=None):
    """notes: the chopped voices, default lead_notes. lines: an optional function (voice, c, seconds) giving a bus of long sung lines (score_g.py). sung: the voice class, default Sung."""
    notes = notes or lead_notes
    os.makedirs(OUT, exist_ok=True)
    c = Twice(shots)
    dur = c.total + 2.0
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(SEED)
    cap, a1, re, end = c.first_caption, c.t_again, c.t_re, c.sunrise
    back = float(c.at(c.back))
    print(f"film {c.total:.2f} s; BPM {np.round(60 * np.diff(c.n) / np.diff(c.t), 1).tolist()}; beats {c.n.tolist()}; shut {a1:.2f}, back {re:.2f}, sunrise {end:.2f}, name {back:.2f}", flush=True)
    voices = np.zeros((len(t), 2))
    voice = (sung or Sung)(SEED + 2)
    for n, m, g, p, _, dt in notes(c):
        far = (c.sun <= n < c.back) or (c.again <= n < c.re)
        add(voices, voice.note(m, breath=0.45 if far else 1.0), float(c.at(n)) + dt, db(g) * 0.16, p)
    lead_bus = voices * db(LEAD_DB)
    if lines:
        lead_bus = lead_bus + lines(voice, c, t)

    ir = room(SEED + 5, rt=3.2)
    send = np.interp(t, [0, cap, a1, a1 + 0.2, re - 0.3, re, end, end + 0.2, back - 0.3, back], [-19, -13, -9, -20, -20, -11, -6, -11, -11, -8])
    p = pad(t, c)
    stems = {"lead": lead_bus + wet(lead_bus, ir) * db(send)[:, None], "sub": sub(t, c)[:, None] * [1, 1], "pad": p + wet(p, ir) * db(-12.0), "air": air(t, c, rng)}
    mix = sum(stems.values())
    width = np.interp(t, [0, cap, a1 - 0.01, a1, re, end - 0.01, end, back, dur], [0.25, 0.75, 0.9, 0.7, 0.8, 1.0, 0.85, 1.0, 1.0])
    mid_ch, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = highpass(side, 90, 2) * width
    mix = highpass(np.stack([mid_ch + side, mid_ch - side], 1), 18, 2)

    ref, sr = sf.read(os.path.join(OUT, "ref.wav"), always_2d=True)
    if sr != SR:
        raise SystemExit(f"ref.wav sample rate {sr}")
    ref_levels = band_levels(ref)
    mix *= db(-3.0)
    for _ in range(2):
        mix = follow(mix, c, ref_levels)

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
