"""Offline demo: a neutral 4-scene storyboard + a synthetic 'speech-like' voice track, so the
whole MP4 path can be tested without spending Gemini TTS quota. The demo text makes no health claims."""
import json
import wave
from pathlib import Path

import numpy as np

from .timing import speakable_len

DEMO = {
    "title": "ตัวอย่างทดสอบระบบ",
    "scenes": [
        {"id": 1, "narration": "สวัสดีครับ [หยุดสั้น] นี่คือคลิปตัวอย่าง สำหรับทดสอบระบบทำวิดีโอ",
         "bg": "sky", "layout": "duo",
         "layers": [{"type": "character", "slot": "a", "mood": "happy", "pose": "wave", "anim": "slide_left"},
                    {"type": "prop", "kind": "sparkle", "slot": "b", "delay": 0.5, "idle": "float"}],
         "overlays": [{"text": "คลิปตัวอย่าง", "slot": "b", "dy": 0.55, "start": 0.6, "style": "title"}]},
        {"id": 2, "narration": "ภาพทั้งหมดวาดด้วยโค้ด ส่วนข้อความไทยแสดงด้วยไฟล์ซับแยกต่างหาก",
         "bg": "mint", "layout": "split", "divider": True,
         "layers": [{"type": "prop", "kind": "cross", "slot": "a", "delay": 0.2},
                    {"type": "prop", "kind": "check", "slot": "b", "delay": 0.9, "idle": "pulse"}],
         "overlays": [{"text": "ตำนาน", "slot": "a", "dy": 0.55, "start": 0.3, "style": "label"},
                      {"text": "หลักฐาน", "slot": "b", "dy": 0.55, "start": 1.0, "style": "label"}]},
        {"id": 3, "narration": "ตรงนี้ลองแสดงแท่งเปรียบเทียบสามค่า พร้อมวงแหวนความคืบหน้า",
         "bg": "lavender", "layout": "duo",
         "layers": [{"type": "prop", "kind": "bars", "slot": "a", "values": [0.9, 0.55, 0.3]},
                    {"type": "prop", "kind": "ring", "slot": "b", "progress": 0.75, "delay": 0.4},
                    {"type": "prop", "kind": "clock", "slot": "b", "delay": 0.4, "scale": 0.4, "hours": 7}],
         "overlays": [{"text": "75%", "slot": "b", "dy": 0.0, "start": 1.2, "style": "number"}]},
        {"id": 4, "narration": "ข้อมูลในคลิปนี้ใช้ทดสอบระบบเท่านั้น ไม่ใช่คำแนะนำทางการแพทย์",
         "bg": "warm", "layout": "solo",
         "layers": [{"type": "character", "slot": "a", "mood": "happy", "pose": "cheer", "scale": 0.9},
                    {"type": "prop", "kind": "shield", "slot": "a", "dx": 0.38, "dy": -0.3, "scale": 0.35, "delay": 0.5}],
         "overlays": [{"text": "ใช้ทดสอบระบบเท่านั้น", "at": [0.5, 0.045], "start": 0.4, "style": "note"}]},
    ],
}


def synth_voice(scenes, path, sr=24000, seed=3):
    """Syllable-rate voiced bursts with pauses at spaces and scene ends (not real speech)."""
    rng = np.random.default_rng(seed)
    out = []
    for si, sc in enumerate(scenes):
        text = sc["narration"].replace("[หยุดสั้น]", " , ")
        for phrase in text.split():
            if phrase == ",":
                out.append(np.zeros(int(0.35 * sr)))
                continue
            n_syl = max(1, int(speakable_len(phrase) / 2.3))
            for _ in range(n_syl):
                d = rng.uniform(0.12, 0.2)
                t = np.arange(int(d * sr)) / sr
                f0 = rng.uniform(150, 230)
                y = sum(np.sin(2 * np.pi * f0 * k * t) / k ** 1.2 for k in range(1, 12))
                env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
                out.append(y * env * 0.12)
                out.append(np.zeros(int(0.03 * sr)))
            out.append(np.zeros(int(rng.uniform(0.2, 0.3) * sr)))
        if si < len(scenes) - 1:
            out.append(np.zeros(int(0.35 * sr)))
    x = np.concatenate(out)
    pcm = (np.clip(x / np.abs(x).max() * 0.7, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return len(x) / sr


def write_demo(outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sb = outdir / "demo_storyboard.json"
    sb.write_text(json.dumps(DEMO, ensure_ascii=False, indent=2), encoding="utf-8")
    dur = synth_voice(DEMO["scenes"], outdir / "demo_voice.wav")
    return sb, outdir / "demo_voice.wav", dur
