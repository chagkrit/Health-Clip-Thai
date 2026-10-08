"""Timing comes from the MEASURED voiceover, never from the planned script.

* Scene boundaries: if the Gemini TTS parts are given (part_XX.wav + --group), every part
  boundary is exact (cumulative measured length + the 0.35 s join gap). Inside a part, and
  for a single voiceover.wav, a boundary is the character-count estimate snapped to the
  nearest real pause (silent run) in the audio.
* Subtitle cues are cut the same way, inside each scene.
"""
import re
import unicodedata
import wave

import numpy as np

JOIN_GAP = 0.35  # seconds of silence gemini_tts.py puts between parts


def read_wav(path):
    """-> (mono float32 array in -1..1, sample_rate)."""
    with wave.open(str(path), "rb") as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        raise SystemExit(f"{path}: รองรับเฉพาะ WAV 16-bit (ได้ {sw * 8}-bit)")
    x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def wav_duration(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def rms_envelope(x, sr, hop=0.01, win=0.025):
    """RMS per `hop` seconds -> (env, hop)."""
    h, wn = int(sr * hop), int(sr * win)
    n = max(1, (len(x) - wn) // h + 1)
    idx = np.arange(n)[:, None] * h + np.arange(wn)[None, :]
    seg = x[np.minimum(idx, len(x) - 1)]
    return np.sqrt((seg ** 2).mean(axis=1) + 1e-12), hop


def silent_runs(x, sr, min_len=0.12):
    """-> list of (start_s, end_s) pauses: RMS under ~3 % of the loud level."""
    env, hop = rms_envelope(x, sr)
    ref = np.percentile(env, 95)
    quiet = env < max(ref * 0.03, 1e-4)
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) * hop >= min_len:
                runs.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return runs


def speech_curve(x, sr, fps):
    """Loudness 0..1 per VIDEO frame, for lip movement."""
    env, hop = rms_envelope(x, sr, hop=1.0 / fps, win=min(0.05, 2.0 / fps))
    ref = np.percentile(env, 95) or 1.0
    return np.clip(env / ref, 0.0, 1.0)


def speakable_len(text):
    """Weight of a text: spoken letters, ignoring tags, punctuation and Thai marks."""
    text = re.sub(r"\[[^\]]*\]|<[^>]*>", "", text)
    n = 0
    for ch in text:
        if unicodedata.category(ch).startswith(("L", "N")) and unicodedata.category(ch) != "Mn":
            n += 1
    return max(n, 1)


def snap(b, runs, tol):
    """Move boundary b to the centre of the nearest pause within +-tol seconds."""
    best, bd = b, tol + 1e-9
    for s, e in runs:
        c = (s + e) / 2
        d = abs(c - b)
        if d <= bd:
            best, bd = c, d
    return best


def split_span(start, end, weights, runs, tol_frac=0.3, tol_max=1.6, min_len=0.6):
    """Cut [start,end] into len(weights) pieces: proportional, snapped to pauses.
    -> list of (a, b)."""
    total = float(sum(weights))
    cuts, acc = [start], 0.0
    for w in weights[:-1]:
        acc += w
        est = start + (end - start) * acc / total
        tol = min(tol_max, tol_frac * (end - start) * w / total + 0.2)
        inner = [r for r in runs if start < (r[0] + r[1]) / 2 < end]
        b = snap(est, inner, tol)
        lo = cuts[-1] + min_len
        cuts.append(min(max(b, lo), end - min_len * (len(weights) - len(cuts))))
    cuts.append(end)
    return [(cuts[i], max(cuts[i + 1], cuts[i] + 0.2)) for i in range(len(weights))]


def plan_scenes(scenes, voice_wav, parts_dir=None, group=None):
    """-> (plan list of {start,end} in voice time, voice duration, notes list)."""
    x, sr = read_wav(voice_wav)
    total = len(x) / sr
    runs = silent_runs(x, sr)
    notes = []
    w = [speakable_len(s["narration"]) for s in scenes]
    spans = None
    if parts_dir and group:
        import glob
        files = sorted(glob.glob(str(parts_dir) + "/part_*.wav"))
        need = -(-len(scenes) // group)
        if len(files) != need:
            notes.append(f"พบ {len(files)} part แต่ {len(scenes)} ฉาก / group {group} ต้องการ {need}: ใช้การประมาณทั้งไฟล์แทน")
        else:
            durs = [wav_duration(f) for f in files]
            expect = sum(durs) + JOIN_GAP * (len(durs) - 1)
            if abs(expect - total) > 0.15:
                notes.append(f"ความยาว part รวม {expect:.2f}s ไม่ตรง voiceover.wav {total:.2f}s: ใช้การประมาณทั้งไฟล์แทน")
            else:
                spans, pos = [], 0.0
                for k, d in enumerate(durs):
                    a = 0.0 if k == 0 else pos - JOIN_GAP / 2
                    b = total if k == len(durs) - 1 else pos + d + JOIN_GAP / 2
                    idx = list(range(k * group, min(len(scenes), (k + 1) * group)))
                    spans.extend(split_span(a, b, [w[i] for i in idx], runs))
                    pos += d + JOIN_GAP
    if spans is None:
        spans = split_span(0.0, total, w, runs)
    # make the chain gap-free: each scene starts where the previous ends
    out = []
    for i, (a, b) in enumerate(spans):
        s = 0.0 if i == 0 else out[-1]["end"]
        e = total if i == len(spans) - 1 else b
        out.append({"start": s, "end": max(e, s + 0.5)})
    return out, total, notes, (x, sr, runs)
