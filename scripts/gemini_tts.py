#!/usr/bin/env python3
"""gemini_tts.py - narration.txt -> เสียงพากย์ไทยด้วย Gemini TTS (โมเดลที่ใช้ฟรีได้ใน AI Studio)

รัน:  uv run --with "google-genai>=2.25" python gemini_tts.py narration.txt --voice female --out voice/
ประโยคเดียว:  ... gemini_tts.py --text "สวัสดีครับ" --out voice/
ฟังเทียบเสียง:  ... gemini_tts.py --audition "ประโยคทดสอบ" [--voices Zephyr,Leda] --out voice/
"""
import argparse, base64, os, re, sys, time, wave
from pathlib import Path

MODEL = "gemini-3.8-flash-tts"  # รองรับไทย / flash-lite ไม่รองรับไทย ห้ามใช้
STYLE = "warm, friendly, natural conversational Thai, slow and clear"  # ให้สั้น style ยาวทำเสียงเพี้ยน
VOICES = {"female": "Leda", "male": "Puck"}  # เสียงหลักที่เลือกแล้ว: --voice female | male (หรือใส่ชื่อเสียงอื่นตรง ๆ)
AUDITION_VOICES = ["Kore", "Puck", "Charon", "Aoede", "Sulafat", "Achird"]
RETRY_HINTS = ("429", "RESOURCE_EXHAUSTED", "500", "503", "UNAVAILABLE", "INTERNAL")
KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
KEY_FILES = (Path(".env"), Path.home() / ".config/gemini-tts/.env", Path.home() / ".env")
STIFF = ["ในยุคปัจจุบัน", "ในปัจจุบัน", "นอกจากนี้", "อย่างไรก็ตาม", "ทั้งนี้", "เป็นที่ทราบกันดีว่า", "สิ่งสำคัญคือ"]


def load_env():
    """หา key จาก env แล้วไล่ .env ในโฟลเดอร์ปัจจุบัน, ~/.config/gemini-tts/.env, ~/.env (อ่านเฉพาะ key ของ Gemini)"""
    if not any(os.environ.get(k) for k in KEY_NAMES):
        for p in KEY_FILES:
            if not p.is_file():
                continue
            for line in p.read_text().splitlines():
                k, _, v = line.strip().partition("=")
                if k in KEY_NAMES and v.strip():
                    os.environ.setdefault(k, v.strip().strip("'\""))
            if any(os.environ.get(k) for k in KEY_NAMES):
                break
    if not any(os.environ.get(k) for k in KEY_NAMES):
        sys.exit("ไม่พบ GEMINI_API_KEY: สร้าง key ที่ aistudio.google.com/apikey แล้วใส่ใน ~/.config/gemini-tts/.env (หรือ ~/.env)")


def clean(text):
    """แปลง marker จาก Prompt 5 เป็น tag ของ Gemini และตัดสิ่งที่ไม่ควรถูกอ่านออกเสียง"""
    t = text.replace("[หยุดสั้น]", " <short pause> ").replace("[หยุดยาว]", " <long pause> ")
    t = re.sub(r"\[\d+(?:[,–-]\s*\d+)*\]", "", t)          # เลขอ้างอิง [1] [2] ห้ามอ่านออกเสียง
    left = re.findall(r"\[[^\]]*\]", t)
    if left:
        print(f"  ! ตัด marker ที่เหลือ: {left}")
        t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"[ \t]+", " ", t.replace("\n", " ")).strip()
    if re.search(r"\d", t):
        print("  ! ยังมีตัวเลข: ควรเขียนเป็นคำอ่านไทยก่อน ไม่งั้นอาจอ่านเพี้ยน")
    if re.search(r"[A-Za-z]{2,}", re.sub(r"</?[a-z ]+>", "", t)):
        print("  ! ยังมีอักษรอังกฤษ: ควรทับศัพท์เป็นไทย")
    stiff = [w for w in STIFF if w in t]
    if stiff:
        print(f"  ! สำนวนภาษาเขียน (ฟังเป็น AI): {stiff} ลองเปลี่ยนเป็นภาษาพูด")
    return t


def synth(client, text, voice):
    body = [{"type": "user_input", "content": [{
        "type": "text", "text": text,
        "annotations": [{"type": "speech_metadata", "style": STYLE}],
    }]}]
    for attempt in range(6):
        try:
            it = client.interactions.create(
                model=MODEL, input=body, response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": voice}]},
            )
            if not it.output_audio:
                raise RuntimeError(f"ไม่ได้เสียงกลับมา (status={it.status})")
            return base64.b64decode(it.output_audio.data)
        except Exception as e:  # noqa: BLE001
            if not any(h in str(e) for h in RETRY_HINTS) or attempt == 5:
                raise
            wait = 20 * 2 ** attempt if attempt < 3 else 120
            print(f"  ... {str(e)[:70]} รอ {wait}s แล้วลองใหม่ ({attempt + 1}/5)")
            time.sleep(wait)


def wav_info(path):
    with wave.open(str(path), "rb") as w:
        return w.getparams(), w.getnframes() / w.getframerate()


def concat(files, out, gap=0.35):
    params, _ = wav_info(files[0])
    silence = b"\x00" * (int(params.framerate * gap) * params.sampwidth * params.nchannels)
    with wave.open(str(out), "wb") as o:
        o.setparams(params)
        for i, f in enumerate(files):
            with wave.open(str(f), "rb") as w:
                if w.getparams()[:3] != params[:3]:
                    sys.exit(f"รูปแบบเสียงไม่ตรงกัน: {f}")
                o.writeframes(w.readframes(w.getnframes()))
            if i < len(files) - 1:
                o.writeframes(silence)


def main(argv=None, client=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?", help="narration.txt: 1 ฉาก = 1 ย่อหน้า (คั่นด้วยบรรทัดว่าง)")
    ap.add_argument("--text", help="ข้อความตรง ๆ แทนไฟล์ (ย่อหน้าคั่นด้วยบรรทัดว่างได้เหมือนกัน)")
    ap.add_argument("--out", default="voice")
    ap.add_argument("--voice", default="female", help="female (Leda) | male (Puck) | ชื่อเสียงอื่นของ Gemini")
    ap.add_argument("--audition", metavar="TEXT", help="เจนประโยคเดียวด้วยหลายเสียงเพื่อเลือกฟัง")
    ap.add_argument("--voices", help="รายชื่อเสียงสำหรับ --audition คั่นด้วยจุลภาค เช่น Zephyr,Leda (ค่าเริ่มต้น 6 เสียงในสคริปต์)")
    ap.add_argument("--pause", type=float, default=3, help="วินาทีพักระหว่างคำขอ (กัน rate limit)")
    ap.add_argument("--force", action="store_true", help="เจนทับไฟล์เดิม (ปกติข้ามไฟล์ที่มีแล้วเพื่อประหยัดโควตา)")
    a = ap.parse_args(argv)
    if not (a.script or a.text or a.audition):
        ap.error("ต้องมี narration.txt, --text หรือ --audition")
    if client is None:
        load_env()
        from google import genai
        client = genai.Client()
    voice = VOICES.get(a.voice, a.voice)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.audition:
        t = clean(a.audition)
        for v in (a.voices.split(",") if a.voices else AUDITION_VOICES):
            (out / f"audition_{v}.wav").write_bytes(synth(client, t, v))
            print(f"audition_{v}.wav")
            time.sleep(a.pause)
        return

    src = a.text if a.text else Path(a.script).read_text(encoding="utf-8")
    scenes = [s for s in re.split(r"\n\s*\n", src) if s.strip()]
    files = []
    for n, s in enumerate(scenes, 1):
        f = out / f"scene_{n:02d}.wav"
        files.append(f)
        if f.exists() and not a.force:
            print(f"scene {n}/{len(scenes)} มีแล้ว ข้าม")
            continue
        print(f"scene {n}/{len(scenes)}")
        f.write_bytes(synth(client, clean(s), voice))
        time.sleep(a.pause)
    full = out / "voiceover.wav"
    concat(files, full)
    print(f"เสร็จ: {full}  ความยาว {wav_info(full)[1]:.1f} วินาที")


if __name__ == "__main__":
    main()
