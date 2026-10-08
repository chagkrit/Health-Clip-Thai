---
name: health-clip-thai
description: Create Thai voiceover / narration audio (WAV) for health and medical explainer video clips with Google Gemini TTS through an AI Studio API key, using the free-tier model gemini-3.8-flash-tts, a female (Leda) or male (Puck) voice, and natural spoken-Thai delivery that does not sound like AI. Use this whenever the user wants Thai narration, พากย์เสียงไทย, เสียงบรรยาย, voiceover, "บันทึกเสียง", text-to-speech or TTS for a health/medical video, short clip, YouTube or TikTok script, wants to audition or compare Gemini voices, or wants a free non-ElevenLabs Thai voice — even if they never say "Gemini". Not for ElevenLabs pipelines (use hearyourvoice), not for speech-to-text, not for non-Thai languages unless asked.
---

# Health Clip Thai — เสียงพากย์ไทยสำหรับคลิปสุขภาพ

สร้างเสียงพากย์ไทยจากบท (script) ด้วย Gemini TTS ผ่าน Google AI Studio API ใช้ได้ทุกโปรเจกต์ เพราะสคริปต์และ key อยู่ระดับ user ไม่ผูกกับโฟลเดอร์ใดโฟลเดอร์หนึ่ง

## ข้อเท็จจริงที่ต้องรู้ (ตรวจกับ docs และการเรียกจริงเมื่อ 8 ต.ค. 2026)

- โมเดล `gemini-3.8-flash-tts`: รองรับไทย และ **ใช้ฟรีใน free tier ของ AI Studio** ส่วน `gemini-3.8-flash-lite-tts` **ไม่รองรับไทย** ห้ามใช้
- แพ็กเกจ Gemini Pro / Google AI Pro **ไม่ได้รวมโควตา API** ต้องใช้ API key จาก aistudio.google.com/apikey (free tier ไม่ต้องผูกบัตร) ถ้าโดน rate limit สคริปต์รอแล้วลองใหม่เอง
- ผลลัพธ์เป็น WAV 24 kHz mono 16-bit
- เสียงหลักที่ผู้ใช้เลือกแล้ว: **ผู้หญิง = Leda, ผู้ชาย = Puck**

## API key

สคริปต์หา key ตามลำดับ: ตัวแปรสภาพแวดล้อม `GEMINI_API_KEY` → `.env` ในโฟลเดอร์ปัจจุบัน → `~/.config/gemini-tts/.env` → `~/.env` (อ่านเฉพาะ `GEMINI_API_KEY`/`GOOGLE_API_KEY` ไม่แตะค่าอื่น)

ถ้าไม่พบ key ให้บอกผู้ใช้ให้สร้างที่ aistudio.google.com/apikey แล้วใส่เองในไฟล์ด้านบน (แนะนำ `! echo 'GEMINI_API_KEY=...' >> ~/.env`) **ห้ามขอให้วาง key ในแชต ห้ามเขียน key ลงไฟล์ในโปรเจกต์หรือแสดงค่า key ในผลลัพธ์** ถ้า key ปรากฏในแชตแล้ว ให้แนะนำให้สร้างใหม่

เช็กว่ามี key โดยไม่แสดงค่า: `printenv GEMINI_API_KEY >/dev/null || grep -q GEMINI_API_KEY ~/.env ~/.config/gemini-tts/.env 2>/dev/null && echo มี`

## ขั้นตอนใช้งาน

รันสคริปต์ด้วย uv (ไม่ต้องติดตั้ง package ถาวร) สคริปต์อยู่ที่ `scripts/gemini_tts.py` ใต้ base directory ของ skill นี้ (ระบบแจ้ง path ตอนโหลด skill) ถ้าติดตั้งแบบ skill ในเครื่องจะเป็น `~/.claude/skills/health-clip-thai` แต่ถ้าติดตั้งผ่าน marketplace จะอยู่ใต้ `~/.claude/plugins/cache/` จึงให้หา path ก่อนเสมอ:

```bash
TTS=$(ls ~/.claude/skills/health-clip-thai/scripts/gemini_tts.py ~/.claude/plugins/cache/*/health-clip-thai/*/scripts/gemini_tts.py 2>/dev/null | head -1)
# 1) ประโยคเดียว
uv run --with "google-genai>=2.25" python "$TTS" \
  --text "สวัสดีครับ วันนี้เรามาคุยเรื่องการนอนหลับกัน" --voice female --out voice/

# 2) ทั้งบท: narration.txt, 1 ฉาก = 1 ย่อหน้า (คั่นบรรทัดว่าง) -> scene_01.wav ... + voiceover.wav
uv run --with "google-genai>=2.25" python "$TTS" \
  narration.txt --voice female --out voice/      # ผู้หญิง (Leda); --voice male = ผู้ชาย (Puck)

# 3) เทียบเสียง: เจนประโยคเดียวหลายเสียง (ค่าเริ่มต้น 6 เสียง หรือกำหนดเองด้วย --voices)
uv run --with "google-genai>=2.25" python "$TTS" \
  --audition "ประโยคทดสอบ" --voices Zephyr,Leda,Callirrhoe --out voice/
```

ลำดับที่ควรทำ:
1. **ถามเฉพาะสิ่งที่ยังไม่รู้**: ผู้หญิงหรือผู้ชาย (ถ้าผู้ใช้ไม่บอก ใช้ผู้หญิง) และบทอยู่ที่ไหน
2. **เตรียมบทก่อนเจน**: ถ้าบทยังเป็นภาษาเขียน ตัวเลข ศัพท์อังกฤษ หรือมีเลขอ้างอิง ให้ปรับตาม `references/thai-narration-style.md` (อ่านเมื่อต้องเขียนหรือแก้บท) สคริปต์ตัดเลขอ้างอิง `[1]` และแปลง `[หยุดสั้น]`/`[หยุดยาว]` ให้อัตโนมัติ และเตือนเมื่อพบตัวเลข อักษรอังกฤษ หรือสำนวนแข็ง ๆ ให้แก้บทตามคำเตือนก่อนเจนต่อ เพราะเจนซ้ำเสียโควตา
3. **เจน** แล้วตรวจด้วยเครื่องมือ: `ffprobe -v error -show_entries format=duration -of csv=p=0 voice/voiceover.wav`
4. **ส่งมอบ**: บอก path ไฟล์ เสียงที่ใช้ และความยาว แล้วให้ผู้ใช้ฟังเอง ผมฟังเสียงไม่ได้ จึงห้ามอ้างว่า "เสียงเป็นธรรมชาติ" ให้บอกว่าตรวจแค่รูปแบบไฟล์และความยาว
5. ฉากไหนไม่ดี: ลบ `scene_XX.wav` ของฉากนั้นแล้วรันซ้ำ (สคริปต์ข้ามฉากที่มีแล้ว) หรือใช้ `--force` เพื่อเจนทับทั้งหมด

## ข้อควรระวัง

- โมเดลอ่านทุกตัวอักษรของบท อย่าใส่คำกำกับท่าทางหรือหัวข้อลงไปในไฟล์บท
- style ในสคริปต์สั้นโดยตั้งใจ (style ยาวทำให้เสียงเพี้ยน) อย่าเพิ่ม director's notes ยาว ๆ
- tag หยุด `<short pause>`/`<long pause>` ยังไม่ได้ยืนยันด้วยการฟังว่าทำงานกับเสียงไทย ถ้าผู้ใช้บอกว่าไม่หยุด ให้ลดการพึ่ง tag และใช้ประโยคสั้นแทน
- ถ้าบัญชีผู้ใช้ผูก billing แบบจ่ายเงินไว้ การเจนอาจมีค่าใช้จ่าย (ราคา paid ณ ต.ค. 2026: ประมาณ 0.50 ดอลลาร์ต่อล้าน token ข้อความ และ 9 ดอลลาร์ต่อล้าน token เสียง จนถึงสิ้นปี 2026 แล้วเพิ่มเป็นสองเท่า) ให้บอกผู้ใช้ก่อนถ้ารู้ว่าใช้แบบจ่ายเงิน
- งานวิดีโอที่ใช้ ElevenLabs ใน pipeline `hearyourvoice` ให้ใช้ skill นั้น skill นี้เป็นทางเลือกฟรีสำหรับเสียงไทย ถ้าจะป้อนบทจาก `voiceover-v1.md` ให้แยกเฉพาะข้อความหลัง `VO:` ลง narration.txt ก่อน
- ถ้า API ตอบ error ที่ไม่ใช่ rate limit ให้อ่านข้อความ error แล้วรายงานตรง ๆ ห้ามเดา และถ้าเรียก `interactions.create` ไม่ได้เพราะ SDK เก่า ให้เช็กว่า `google-genai>=2.25`
