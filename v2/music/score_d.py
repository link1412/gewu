"""Version D: warm, and unbroken.

    python3 -I v2/music/score_d.py       out/v2/music/mix_D.wav, stems_D/

Measured on C against the original (README.md): the original holds its major third at .65-1.0 of its strongest pitch class and has almost no sixth; ours had the third at .08-.35 and the sixth at .42-.77.
Its deepest dip in the build is 11 dB; C's was 27. So against C:
  the lead has the third: Bb4 G5 F5 (5, 3, 2). Low, high, middle like the original; not its notes moved (its 3, 9, 5 would be G4 F5 Bb4)
  the pad has the third, no sixth, and one chord throughout. No minor, no silence
  one steady tempo between the first shot, the first caption and the sunrise; the cuts inside are not chased, as they are not in the original
  the yangqin plays only 新, quietly
  what is left of 清角: Ab in place of G, for the last loop before the sunrise only, resolving to G on the cut

Stand-ins as in score_c.py. The third being the reason is a hypothesis from the numbers: I cannot hear it.
"""

import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import CEILING_DB, FPS, LEAD_DB, OUT, SEED, SR, TARGET_LUFS, Clock, Voice, add, air, bank, bell, curve, db, ensemble, gate_down, gate_up, highpass, limiter, lufs, measured_cents, room, shown, sstep, sub, sweep_lowpass, wet  # noqa: E402
from score_c import yq_note  # noqa: E402

CELL = (70, 79, 77)  # Bb4 G5 F5
HOME = (70, 79, 75)  # the same two, then the tonic, only here
CELL_SUS = (70, 80, 77)  # the last loop: Ab5 for G5

PAD = [("str", 39, -8), ("str", 46, -5), ("str", 51, -9), ("str", 53, -11), ("str", 55, -5), ("str", 58, -11), ("low", 39, -15), ("low", 46, -13), ("low", 51, -17), ("low", 55, -14), ("low", 58, -20), ("high", 58, -17), ("high", 63, -15), ("high", 65, -18), ("high", 67, -12)]
THIRD = {("str", 55), ("low", 55), ("high", 67)}  # lie down for the suspension
SUS = [("str", 56, -5), ("low", 56, -14)]


class Steady(Clock):
    """Few fixed points, so one tempo: the first cut, the first caption, the sunrise, the name."""

    def __init__(self, shots=None):
        super().__init__(shots)
        t = self.t
        self.n, self.t = np.array([self.n[0], self.cap, self.sun, self.back]), np.array([t[0], t[3], t[4], t[5]])
        self.canon = int(np.ceil(self.to_beat(4.0) - 1e-6))
        self.mid = self.cap + 3 * ((self.sun - self.cap) // 6)
        self.top_at = [self.sun - 3 * ((self.sun - self.cap) // 9), self.sun - 3]  # 新 rises only twice, late: for the last third, then for the last loop


def top(n, c):
    """新: G5, then Bb5 in the last third, then Eb6 for the last loop."""
    if n >= c.sun:
        return 79
    return 87 if n >= c.top_at[1] else 82 if n >= c.top_at[0] else 79


def lead_notes(c):
    rng = np.random.default_rng(SEED + 1)
    ev = [(0, 79, 0.0, 0.0, "v1")]

    def note(n, phase, cell=CELL):
        k = (n - phase) % 3
        return top(n + 1, c) if k == 1 else cell[k]

    for n in range(2, c.sun):
        lift = np.interp(n, [2, c.canon, c.canon + 1, c.cap, c.mid, c.sun - 1], [3.0, 3.0, 6.0, 5.0, 4.5, 5.5])
        ev.append((n, note(n, c.LOOP), -3.0 + lift + rng.normal(0, 0.5), 0.0, "v1"))
        if n >= c.canon:
            # the suspension is sung here, by the second voice, over the last loop
            m = 80 if n >= c.sun - 3 and (n - c.LOOP - 1) % 3 == 1 else note(n, c.LOOP + 1)
            ev.append((n, m, -6.0 + lift + rng.normal(0, 0.7), -0.45, "v2"))
        if n >= c.cap:
            ev.append((n, note(n, c.LOOP + 2) - 12, -8.0 + lift + rng.normal(0, 0.7), 0.5, "v3"))
        if n >= c.mid:
            hi = note(n, c.LOOP) + 12
            ev.append((n, hi if hi <= 87 else hi - 12, -17.0 + lift + rng.normal(0, 0.7), 0.7, "v4"))
            ev.append((n, min(note(n, c.LOOP + 1), 77) - 24, -11.0 + lift + rng.normal(0, 0.7), -0.25, "v5"))
    for n in range(c.sun, c.back - 2):
        ev.append((n, note(n, c.LOOP), -7.0 + (n - c.sun) * 0.7 + rng.normal(0, 0.5), 0.0, "v1"))
    ev += [(c.back - 2, HOME[0], -5.0, 0.0, "v1"), (c.back - 1, HOME[1], -5.0, 0.0, "v1")]
    ev += [(c.back, HOME[2], -3.0, 0.0, "v1"), (c.back, 58, -9.0, 0.5, "v3"), (c.back, 67, -13.0, -0.45, "v2"), (c.back, 63, -12.0, 0.5, "v3")]
    return ev


def pad(t, c):
    cap, end, back, stop = c.marks()
    dur = t[-1]
    swell = curve(t, [(0, -50), (cap * 0.5, -22), (cap, -9), (cap + 1, -6), (end - 3, -1), (end, 4)])
    a = swell * gate_down(t, end + 0.27, 30) + db(-4.0) * gate_up(t, back - 0.37, 20) * gate_down(t, stop + 0.27, 30)
    p = np.array([(0, 120), (cap * 0.5, 180), (cap - 0.05, 300), (cap + 0.1, 620), (end - 3, 800), (end, 1500), (end + 0.25, 45), (back - 0.35, 45), (back, 1000), (stop, 800), (stop + 0.25, 45), (dur, 45)])
    fc = np.exp(np.interp(t, p[:, 0], np.log(p[:, 1])))
    res = np.interp(t, [0, end, end + 0.01, end + 0.25, end + 0.3, back - 0.36, back - 0.35, back, back + 0.15, dur], [1, 1, 5, 5, 1, 1, 6, 6, 1, 1])
    s0 = float(c.at(c.sun - 3))
    sus = sstep((t - s0) / 0.4) * (1 - sstep((t - end + 0.15) / 0.15))  # in over the last loop, out just as the cut lands
    out = np.zeros((len(t), 2))
    for stem, m, g in PAD + SUS:
        y = bank(stem, m)
        ratio = 2.0 ** (-measured_cents(y, m) / 1200.0)
        n = min(len(y), len(t))
        y = y[: n + SR]
        rms = np.sqrt((y[int(3 * SR) : int(20 * SR)] ** 2).mean())
        x = ensemble(y, SEED + m + len(stem) * 100, ratio)[:n] * db(g) * 0.1 / rms
        e = sus if (stem, m, g) in SUS else (1 - sus) if (stem, m) in THIRD else 1.0
        out[:n] += x * (e[:n, None] if np.ndim(e) else e)
    return sweep_lowpass(out * a[:, None], t, fc, res)


def render(shots=None, name="D"):
    os.makedirs(OUT, exist_ok=True)
    c = Steady(shots)
    dur = c.total + 2.0
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(SEED)
    cap, end, back, stop = c.marks()
    print(f"film {c.total:.2f} s; seconds per beat {np.round(np.diff(c.t) / np.diff(c.n), 3).tolist()} = {np.round(60 * np.diff(c.n) / np.diff(c.t), 1).tolist()} BPM; beats {c.n.tolist()} canon {c.canon} mid {c.mid} top {c.top_at}", flush=True)

    voices = np.zeros((len(t), 2))
    voice = Voice(SEED + 2)
    for n, m, g, p, _ in lead_notes(c):
        hum = 0.0 if n in c.n else rng.normal(0, 0.012)
        add(voices, voice.note(m, breath=0.45 if c.sun <= n < c.back else 1.0), float(c.at(n)) + hum, db(g) * 0.16, p)
    lead_bus = voices * db(LEAD_DB)

    yq_bus = np.zeros((len(t), 2))
    r = np.random.default_rng(SEED + 12)
    for n in range(c.cap, c.sun):
        if (n - c.LOOP) % 3 == 1:
            add(yq_bus, yq_note(top(n + 1, c), -3.0 + 2.5 * (n - c.cap) / (c.sun - c.cap), r), float(c.at(n)) + r.normal(0, 0.004), db(-17.0), 0.2)

    bell_bus = np.zeros((len(t), 2))
    add(bell_bus, bell(155.56, SEED + 3), end, db(-29.0), 0.0)
    add(bell_bus, bell(311.13, SEED + 4), back, db(-30.0), 0.0)

    ir = room(SEED + 5)
    send = np.interp(t, [0, cap, end, end + 0.2, back - 0.3, back], [-17, -9, -5, -9, -9, -6])
    stems = {
        "lead": lead_bus + wet(lead_bus, ir) * db(send)[:, None],
        "yangqin": yq_bus + wet(yq_bus, ir) * db(-9.0),
        "sub": sub(t, c)[:, None] * [1, 1],
        "pad": (p := pad(t, c)) + wet(p, ir) * db(-14.0),
        "air": air(t, c, rng),
        "bell": bell_bus + wet(bell_bus, ir) * db(-5.0),
    }
    mix = sum(stems.values())
    width = np.interp(t, [0, cap, end - 0.01, end, back, dur], [0.25, 0.75, 0.95, 0.85, 1.0, 1.0])
    mid_ch, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = highpass(side, 90, 2) * width
    mix = highpass(np.stack([mid_ch + side, mid_ch - side], 1), 18, 2)
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
    d = os.path.join(OUT, f"stems_{name}")
    os.makedirs(d, exist_ok=True)
    for k, v in stems.items():
        sf.write(os.path.join(d, f"{k}.wav"), v[: int(c.total * SR)] * gain, SR, subtype="FLOAT")


if __name__ == "__main__":
    render()
