"""Original background music, synthesised from scratch with NumPy (no samples, no
third-party melodies, so nothing to license): chord pad, plucked melody, bass, shaker and a
bell for the logo reveal. Deterministic for a given seed/mood. Also the final mix:
voice + music with sidechain-style ducking computed from the voice itself."""
import wave

import numpy as np

SR = 48000

# mood -> (bpm, root MIDI of the key, progression as semitone offsets of chord roots)
MOODS = {
    "calm": (84, 60, [0, 9, 5, 7]),      # C Am F G
    "bright": (100, 67, [0, 9, 5, 7]),   # G Em C D feel
    "gentle": (76, 65, [0, 2, 7, 5]),    # F Gm C Bb feel
}
MAJOR = [0, 4, 7]
MINOR = [0, 3, 7]
PENTA = [0, 2, 4, 7, 9]


def _hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def _add(buf, start, sig, gain=1.0):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[:e - s] * gain


def _pluck(freq, dur, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 5.5) * np.minimum(1.0, t * 400)
    y = (np.sin(2 * np.pi * freq * t) + 0.35 * bright * np.sin(4 * np.pi * freq * t) * np.exp(-t * 9)
         + 0.12 * np.sin(6 * np.pi * freq * t) * np.exp(-t * 14))
    return y * env


def _pad(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    att, rel = min(0.5, dur * 0.4), min(0.7, dur * 0.4)
    env = np.minimum(1.0, t / att) * np.minimum(1.0, (dur - t) / rel).clip(0, 1)
    y = sum(np.sin(2 * np.pi * freq * d * t + k) for k, d in enumerate((0.997, 1.0, 1.004)))
    return y / 3 * env


def _bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 3.2) * np.minimum(1.0, t * 300)
    return (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)) * env


def _shaker(dur=0.07, rng=None):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    hp = np.diff(noise, prepend=0.0)          # crude high-pass
    env = np.exp(-np.arange(n) / SR * 55)
    return hp * env * 0.25


def bell(freq=1318.5, dur=2.6):
    """Bright struck-bell: inharmonic partials with different decays."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for ratio, amp, dec in ((1.0, 1.0, 1.6), (2.76, 0.55, 2.4), (5.4, 0.3, 3.6), (8.93, 0.16, 5.5)):
        y += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t * dec)
    y *= np.minimum(1.0, t * 2000)
    return y / 1.8


def synth_music(duration, mood="calm", seed=7):
    """-> float32 mono array of `duration` seconds (SR=48000), peak ~0.8."""
    bpm, root, prog = MOODS[mood]
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = 4 * beat
    buf = np.zeros(int((duration + 3.0) * SR))
    nbars = int(duration / bar) + 2
    pitch = 2
    for b in range(nbars):
        r = root + prog[b % 4]
        minor = (prog[b % 4] in (9, 2))
        triad = [r + x for x in (MINOR if minor else MAJOR)]
        t0 = b * bar
        for k, n in enumerate(triad):
            _add(buf, t0, _pad(_hz(n), bar + 0.4), 0.10)
        _add(buf, t0, _bass(_hz(r - 24), beat * 1.9), 0.55)
        _add(buf, t0 + 2 * beat, _bass(_hz(r - 24 + (7 if b % 2 else 0)), beat * 1.9), 0.42)
        scale = [r + x for x in PENTA] + [r + 12 + x for x in PENTA]
        for e in range(8):   # eighth-note melody grid
            if rng.random() < 0.38 and e not in (0, 4):
                continue
            pitch = int(np.clip(pitch + rng.integers(-2, 3), 0, len(scale) - 1))
            _add(buf, t0 + e * beat / 2, _pluck(_hz(scale[pitch] + 12), beat * 1.1), 0.20)
        for e in range(8):
            if e % 2 == 1:
                _add(buf, t0 + e * beat / 2, _shaker(rng=rng), 0.5)
    buf = buf[: int(duration * SR)]
    fade = int(min(2.0, duration / 4) * SR)
    if fade > 0 and len(buf) > fade:
        buf[-fade:] *= np.linspace(1, 0, fade)
    buf /= max(1e-6, np.abs(buf).max())
    return (buf * 0.8).astype(np.float32)


def resample(x, sr_in, sr_out):
    """Band-limited resample via FFT (exact enough for speech; no scipy needed)."""
    if sr_in == sr_out:
        return x.astype(np.float32)
    n_out = int(round(len(x) * sr_out / sr_in))
    X = np.fft.rfft(x.astype(np.float64))
    m = n_out // 2 + 1
    Y = np.zeros(m, dtype=X.dtype)
    k = min(len(X), m)
    Y[:k] = X[:k]
    return (np.fft.irfft(Y, n_out) * (n_out / len(x))).astype(np.float32)


def duck_gain(voice, sr, depth_db=-12.0, attack=0.08, release=0.45):
    """Smoothed 0..1 'voice is speaking' follower -> per-sample music gain."""
    win = int(0.03 * sr)
    if win < 1:
        return np.ones(len(voice))
    env = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, mode="same"))
    ref = np.percentile(env, 95) or 1.0
    active = np.clip(env / (ref * 0.12), 0.0, 1.0)
    out = np.empty_like(active)
    a_a, a_r = np.exp(-1 / (attack * sr)), np.exp(-1 / (release * sr))
    # run the follower on a decimated grid for speed, then interpolate
    step = max(1, sr // 400)
    ds = active[::step]
    o = np.empty_like(ds)
    cur = 0.0
    sa, sr_ = a_a ** step, a_r ** step
    for i, v in enumerate(ds):
        coef = sa if v > cur else sr_
        cur = coef * cur + (1 - coef) * v
        o[i] = cur
    out = np.interp(np.arange(len(active)), np.arange(len(ds)) * step, o)
    return 1.0 - out * (1.0 - 10 ** (depth_db / 20.0))


def mix_audio(voice, voice_sr, total, voice_offset, music, bell_times,
              music_level=0.55, depth_db=-12.0, bell_gain=0.55, voice_gain=1.0):
    """-> float32 stereo (n,2) at SR. Voice sits at `voice_offset`; music is ducked under it."""
    n = int(total * SR)
    v = resample(voice, voice_sr, SR)
    vfull = np.zeros(n, dtype=np.float32)
    s = int(voice_offset * SR)
    e = min(n, s + len(v))
    vfull[s:e] = v[: e - s]
    peak = np.abs(vfull).max() or 1.0
    vfull *= voice_gain * (0.89 / peak)          # voice peak about -1 dBFS before the limiter
    m = np.zeros(n, dtype=np.float32)
    m[: min(n, len(music))] = music[:n]
    fade_in = int(0.4 * SR)
    m[:fade_in] *= np.linspace(0, 1, fade_in)
    out_fade = int(1.5 * SR)
    m[-out_fade:] *= np.linspace(1, 0, out_fade)
    g = duck_gain(vfull, SR, depth_db)
    mix = vfull + m * g * music_level
    for bt in bell_times:
        _add(mix, bt, bell().astype(np.float32), bell_gain)
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)      # soft limiter, no hard clipping
    st = np.stack([mix, mix], axis=1).astype(np.float32)
    return st, g


def write_wav(path, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
