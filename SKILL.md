---
name: health-clip-thai
description: Workflow for short Thai health and medical explainer clips (120 s, 16:9, 2D cartoon) - choose a topic, find real PubMed evidence, write a cited spoken-Thai script, make video prompts and SRT subtitles, then record the Thai voiceover as WAV with free Google Gemini TTS (gemini-3.8-flash-tts, female Leda or male Puck, natural delivery that does not sound like AI). Use whenever the user wants a health or medical video, clip, YouTube/TikTok/Reels script, คลิปสุขภาพ, สคริปต์ 120 วินาที, prompt วิดีโอการ์ตูน, ซับไตเติลไทย, or Thai narration, พากย์เสียงไทย, voiceover, text-to-speech - including a single stage such as audio from an existing script or auditioning voices. Not for ElevenLabs pipelines (use hearyourvoice) or speech-to-text.
---

# Health Clip Thai — ทำคลิปสุขภาพพร้อมเสียงบรรยายไทย

ผู้ใช้เข้าได้ทุกขั้น (เช่น มีบทแล้วต้องการแค่เสียง) ให้ถามว่าอยู่ขั้นไหนเฉพาะเมื่อไม่ชัดจากคำขอ อย่าพาทำทุกขั้นถ้าไม่ได้ขอ

## เวิร์กโฟลว์ 6 ขั้น

ข้อความ prompt เต็มและกฎเข้มงวดของขั้น 1–5 อยู่ใน `references/workflow-prompts.md` **อ่านเฉพาะส่วนของขั้นที่กำลังทำ** (ไม่ต้องอ่านทั้งไฟล์ล่วงหน้า) แล้วทำตามนั้นในบทสนทนาเลย อย่าพิมพ์ prompt ย้อนให้ผู้ใช้ ขั้น 1 และ 2 ต้องหยุดรอคำตอบผู้ใช้ตามที่ prompt กำหนด

| ขั้น | ทำอะไร | ผลลัพธ์ | หยุดรอผู้ใช้ |
|---|---|---|---|
| 1 | เสนอ 10 ไอเดียสุขภาพ (ตำนาน vs หลักฐาน ฯลฯ) | รายการไอเดีย | ใช่: เลือกไอเดีย |
| 2 | ค้นหลักฐานจริง 3–5 งาน | ตารางหลักฐาน | ใช่: ยืนยันชุดหลักฐาน |
| 3 | เขียนสคริปต์ไทย 120 วินาที มีเลขอ้างอิง | TITLE, SCRIPT ตาม timecode, REFERENCE MAP, SOURCES, YOUTUBE DESCRIPTION | ไม่ |
| 4 | แปลงสคริปต์เป็น video prompt ฉากละ ~8 วินาที (การ์ตูน 2D, ไม่มีตัวอักษรในภาพ, ไม่ใช้ตัวละครลิขสิทธิ์) แล้วจัดรูปแบบ `Scene N` + batch prompt | STYLE BIBLE + prompt ต่อฉาก | ไม่ (ทำเมื่อผู้ใช้ต้องการภาพ) |
| 5 | TTS-READY SCRIPT + ไฟล์ SRT | สคริปต์พร้อมอ่าน + `.srt` | ไม่ |
| 6 | บันทึกเสียงไทยเป็นไฟล์ WAV ด้วย Gemini TTS | `voice/scene_XX.wav`, `voiceover.wav` | ไม่ |

กฎที่ห้ามพลาด (มาจากต้นฉบับ):
- **ขั้น 2 ต้องใช้หลักฐานที่เปิดอ่านได้จริงเท่านั้น** ใช้เครื่องมือ PubMed / Semantic Scholar หรือ WebFetch ไปที่ `pubmed.ncbi.nlm.nih.gov/[PMID]/` ห้ามสร้าง PMID/DOI/ลิงก์ขึ้นเอง ถ้าเข้าถึงเครื่องมือค้นหาไม่ได้ให้บอกผู้ใช้ตรง ๆ แล้วหยุด ตรวจว่าไม่ถูกถอนตีพิมพ์ และตัวเลขตรงกับ abstract
- สคริปต์ห้ามสรุปเกินหลักฐาน ห้ามใช้ "พิสูจน์แล้ว", "ชัวร์", "หายขาด", "ป้องกันได้ 100%" และต้องมีประโยคปฏิเสธความรับผิดชอบทางการแพทย์ตอนปิดท้าย
- ห้ามเสนอหัวข้อที่เป็นการวินิจฉัยหรือรักษาเฉพาะบุคคล ขนาดยา ผลิตภัณฑ์/แบรนด์ หรือเนื้อหาปลุกความกลัว
- ภาพการ์ตูนต้องเป็นตัวละครต้นฉบับ ห้ามเลียน Snoopy/Peanuts หรือตัวละครมีลิขสิทธิ์

เมื่อจะเข้าขั้น 6 ให้ใช้บทจากขั้น 5 (หรือบทที่ผู้ใช้มี) แบ่งเป็น `narration.txt` ฉากละหนึ่งย่อหน้า ตัดหัวข้อ timecode และโน้ตกำกับออก เพราะโมเดลอ่านทุกตัวอักษร

---

## ขั้นที่ 6 — บันทึกเสียงพากย์ไทย (รายละเอียด)

### ข้อเท็จจริงที่ต้องรู้ (ตรวจกับ docs และการเรียกจริงเมื่อ 8 ต.ค. 2026)

- โมเดล `gemini-3.8-flash-tts`: รองรับไทย และ **ใช้ฟรีใน free tier ของ AI Studio** ส่วน `gemini-3.8-flash-lite-tts` **ไม่รองรับไทย** ห้ามใช้
- แพ็กเกจ Gemini Pro / Google AI Pro **ไม่ได้รวมโควตา API** ต้องใช้ API key จาก aistudio.google.com/apikey (free tier ไม่ต้องผูกบัตร) ถ้าโดน rate limit สคริปต์รอแล้วลองใหม่เอง
- ผลลัพธ์เป็น WAV 24 kHz mono 16-bit
- เสียงหลักที่ผู้ใช้เลือกแล้ว: **ผู้หญิง = Leda, ผู้ชาย = Puck**

### API key

สคริปต์หา key ตามลำดับ: ตัวแปรสภาพแวดล้อม `GEMINI_API_KEY` → `.env` ในโฟลเดอร์ปัจจุบัน → `~/.config/gemini-tts/.env` → `~/.env` (อ่านเฉพาะ `GEMINI_API_KEY`/`GOOGLE_API_KEY` ไม่แตะค่าอื่น)

ถ้าไม่พบ key ให้บอกผู้ใช้ให้สร้างที่ aistudio.google.com/apikey แล้วใส่เองในไฟล์ด้านบน (แนะนำ `! echo 'GEMINI_API_KEY=...' >> ~/.env`) **ห้ามขอให้วาง key ในแชต ห้ามเขียน key ลงไฟล์ในโปรเจกต์หรือแสดงค่า key ในผลลัพธ์** ถ้า key ปรากฏในแชตแล้ว ให้แนะนำให้สร้างใหม่

เช็กว่ามี key โดยไม่แสดงค่า: `printenv GEMINI_API_KEY >/dev/null || grep -q GEMINI_API_KEY ~/.env ~/.config/gemini-tts/.env 2>/dev/null && echo มี`

### ขั้นตอนใช้งาน

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

### ข้อควรระวัง

- โมเดลอ่านทุกตัวอักษรของบท อย่าใส่คำกำกับท่าทางหรือหัวข้อลงไปในไฟล์บท
- style ในสคริปต์สั้นโดยตั้งใจ (style ยาวทำให้เสียงเพี้ยน) อย่าเพิ่ม director's notes ยาว ๆ
- tag หยุด `<short pause>`/`<long pause>` ยังไม่ได้ยืนยันด้วยการฟังว่าทำงานกับเสียงไทย ถ้าผู้ใช้บอกว่าไม่หยุด ให้ลดการพึ่ง tag และใช้ประโยคสั้นแทน
- ถ้าบัญชีผู้ใช้ผูก billing แบบจ่ายเงินไว้ การเจนอาจมีค่าใช้จ่าย (ราคา paid ณ ต.ค. 2026: ประมาณ 0.50 ดอลลาร์ต่อล้าน token ข้อความ และ 9 ดอลลาร์ต่อล้าน token เสียง จนถึงสิ้นปี 2026 แล้วเพิ่มเป็นสองเท่า) ให้บอกผู้ใช้ก่อนถ้ารู้ว่าใช้แบบจ่ายเงิน
- งานวิดีโอที่ใช้ ElevenLabs ใน pipeline `hearyourvoice` ให้ใช้ skill นั้น skill นี้เป็นทางเลือกฟรีสำหรับเสียงไทย ถ้าจะป้อนบทจาก `voiceover-v1.md` ให้แยกเฉพาะข้อความหลัง `VO:` ลง narration.txt ก่อน
- ถ้า API ตอบ error ที่ไม่ใช่ rate limit ให้อ่านข้อความ error แล้วรายงานตรง ๆ ห้ามเดา และถ้าเรียก `interactions.create` ไม่ได้เพราะ SDK เก่า ให้เช็กว่า `google-genai>=2.25`
