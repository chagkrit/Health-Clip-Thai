---
name: health-clip-thai
description: Workflow for short Thai health and medical explainer clips (about 120 s, 2D cartoon, aspect 16:9 / 9:16 / 1:1 / 4:5) - choose a topic, find real PubMed evidence, write a cited spoken-Thai script, make video prompts and SRT subtitles, record the Thai voiceover as WAV with free Google Gemini TTS (female Leda or male Puck), then build a finished 1080p H.264/AAC MP4 with code-drawn animation (pycairo), ASS Thai subtitles, original NumPy-synthesised music, a circular logo ring bumper and ffmpeg-skill assembly, optionally run by a small subagent team, plus a 2-slide carousel (myth / medical fact PNGs) and a caption with PubMed references and hashtags for the post. Includes a ready-made "myth-busting" 120 s format (hook, patient-doctor Q&A, mechanism, three evidence cards, fact card, CTA, logo). Use whenever the user wants a health or medical video, clip, MP4, YouTube/TikTok/Reels/Shorts, คลิปสุขภาพ, สคริปต์ 120 วินาที, prompt วิดีโอการ์ตูน, ซับไตเติลไทย, Thai narration, พากย์เสียงไทย, voiceover, ทำวิดีโอสำเร็จรูป, ตัดต่อ, carousel, สไลด์โพสต์, แคปชัน, caption พร้อมอ้างอิง PubMed - including a single stage such as audio from an existing script, or an MP4 from an existing script and voice. Not for ElevenLabs pipelines (use hearyourvoice) or speech-to-text.
---

# Health Clip Thai — ทำคลิปสุขภาพพร้อมเสียงบรรยายไทย

ผู้ใช้เข้าได้ทุกขั้น (เช่น มีบทแล้วต้องการแค่เสียง) ให้ถามว่าอยู่ขั้นไหนเฉพาะเมื่อไม่ชัดจากคำขอ อย่าพาทำทุกขั้นถ้าไม่ได้ขอ

## เวิร์กโฟลว์ 8 ขั้น

ข้อความ prompt เต็มและกฎเข้มงวดของขั้น 1–5 อยู่ใน `references/workflow-prompts.md` **อ่านเฉพาะส่วนของขั้นที่กำลังทำ** (ไม่ต้องอ่านทั้งไฟล์ล่วงหน้า) แล้วทำตามนั้นในบทสนทนาเลย อย่าพิมพ์ prompt ย้อนให้ผู้ใช้ ขั้น 1 และ 2 ต้องหยุดรอคำตอบผู้ใช้ตามที่ prompt กำหนด

| ขั้น | ทำอะไร | ผลลัพธ์ | หยุดรอผู้ใช้ |
|---|---|---|---|
| 1 | เสนอ 10 ไอเดียสุขภาพ (ตำนาน vs หลักฐาน ฯลฯ) | รายการไอเดีย | ใช่: เลือกไอเดีย |
| 2 | ค้นหลักฐานจริง 3–5 งาน | ตารางหลักฐาน | ใช่: ยืนยันชุดหลักฐาน |
| 3 | เขียนสคริปต์ไทย 120 วินาที มีเลขอ้างอิง | TITLE, SCRIPT ตาม timecode, REFERENCE MAP, SOURCES, YOUTUBE DESCRIPTION | ไม่ |
| 4 | แปลงสคริปต์เป็น video prompt ฉากละ ~8 วินาที (การ์ตูน 2D, ไม่มีตัวอักษรในภาพ, ไม่ใช้ตัวละครลิขสิทธิ์) แล้วจัดรูปแบบ `Scene N` + batch prompt (ข้ามได้ถ้าจะทำ MP4 ด้วยขั้น 7 เพราะขั้น 7 วาดภาพให้เอง) | STYLE BIBLE + prompt ต่อฉาก | ไม่ (ทำเมื่อผู้ใช้ต้องการภาพ) |
| 5 | TTS-READY SCRIPT + ไฟล์ SRT | สคริปต์พร้อมอ่าน + `.srt` | ไม่ |
| 6 | บันทึกเสียงไทยเป็นไฟล์ WAV ด้วย Gemini TTS | `voice/part_XX.wav`, `voiceover.wav` | ไม่ |
| 7 | ประกอบ MP4 สำเร็จรูป: ภาพ+แอนิเมชัน (pycairo), ซับ ASS, เพลงสังเคราะห์ด้วย NumPy (เสียงเบาลงอัตโนมัติเมื่อมีเสียงพูด), logo ring เคลื่อนไหว + เสียงกระดิ่ง, ffmpeg | `NAME_16x9.mp4` (+ `.srt`, contact sheet) | ถาม: สัดส่วน, path โลโก้ |
| 8 | ชุดโพสต์: Carousel 2 สไลด์ (ความเชื่อผิด / ข้อเท็จจริงทางการแพทย์) เป็น PNG + แคปชันพร้อมอ้างอิง PMID + แฮชแท็ก + รายการคำที่ปรับเพื่อความถูกต้อง | `NAME_slide1/2_4x5.png` + ข้อความแคปชัน | ไม่ (ทำเมื่อผู้ใช้ต้องการโพสต์) |

กฎที่ห้ามพลาด (มาจากต้นฉบับ):
- **ขั้น 2 ต้องใช้หลักฐานที่เปิดอ่านได้จริงเท่านั้น** ใช้เครื่องมือ PubMed / Semantic Scholar หรือ WebFetch ไปที่ `pubmed.ncbi.nlm.nih.gov/[PMID]/` ห้ามสร้าง PMID/DOI/ลิงก์ขึ้นเอง ถ้าเข้าถึงเครื่องมือค้นหาไม่ได้ให้บอกผู้ใช้ตรง ๆ แล้วหยุด ตรวจว่าไม่ถูกถอนตีพิมพ์ และตัวเลขตรงกับ abstract
- สคริปต์ห้ามสรุปเกินหลักฐาน ห้ามใช้ "พิสูจน์แล้ว", "ชัวร์", "หายขาด", "ป้องกันได้ 100%" และต้องมีประโยคปฏิเสธความรับผิดชอบทางการแพทย์ตอนปิดท้าย
- ห้ามเสนอหัวข้อที่เป็นการวินิจฉัยหรือรักษาเฉพาะบุคคล ขนาดยา ผลิตภัณฑ์/แบรนด์ หรือเนื้อหาปลุกความกลัว
- ภาพการ์ตูนต้องเป็นตัวละครต้นฉบับ ห้ามเลียน Snoopy/Peanuts หรือตัวละครมีลิขสิทธิ์

**รูปแบบสำเร็จรูป "Myth-Busting" 120 วินาที** (ความเชื่อผิด → คนไข้ถามหมอตอบ → กลไก → การ์ดหลักฐาน 3 ใบ → Fact Card → CTA → โลโก้): อ่าน `references/format-myth-busting-120s.md` ก่อนเขียนบทขั้น 3 เมื่อผู้ใช้ขอรูปแบบนี้ หรือไม่ได้ระบุรูปแบบ (ให้ถามว่าจะใช้หรือไม่) ตัวอย่างและตัวเลขในไฟล์นั้นยังไม่ผ่านการตรวจ PubMed ห้ามนำไปใช้เป็นข้อเท็จจริง

ขั้น 8 อ่าน `references/post-package.md` ก่อนทำ (ใช้ได้โดยไม่ต้องมีเสียงหรือวิดีโอ ขอแค่มีตารางหลักฐานที่ยืนยันแล้ว)

ขั้น 7 อ่าน `references/video-pipeline.md` ก่อนรัน และเลือกสัดส่วนได้: `16:9` (1920×1080 ค่าเริ่มต้น), `9:16` (1080×1920), `1:1` (1080×1080), `4:5` (1080×1350) หลายสัดส่วนในคำสั่งเดียวได้

เมื่อจะเข้าขั้น 6 ให้ใช้บทจากขั้น 5 (หรือบทที่ผู้ใช้มี) แบ่งเป็น `narration.txt` ฉากละหนึ่งย่อหน้า ตัดหัวข้อ timecode และโน้ตกำกับออก เพราะโมเดลอ่านทุกตัวอักษร

---

## ขั้นที่ 6 — บันทึกเสียงพากย์ไทย (รายละเอียด)

### ข้อเท็จจริงที่ต้องรู้ (ตรวจกับ docs และการเรียกจริงเมื่อ 8 ต.ค. 2026)

- โมเดล `gemini-3.8-flash-tts`: รองรับไทย และ **ใช้ฟรีใน free tier ของ AI Studio** ส่วน `gemini-3.8-flash-lite-tts` **ไม่รองรับไทย** ห้ามใช้
- **free tier จำกัดวันละ 10 คำขอต่อโมเดล** (API ตอบ `limit: 10` เมื่อ 8 ต.ค. 2026 และต้องรอราว 17 ชั่วโมงให้รีเซ็ต) 1 คำขอ = 1 ครั้งที่สคริปต์เรียกโมเดล ดังนั้นห้ามเปลืองคำขอกับการลองเสียงหรือเจนซ้ำโดยไม่จำเป็น และคลิป 15 ฉากต้องรวมหลายย่อหน้าต่อคำขอด้วย `--group 3` หรือ `--group 4` (ประมาณ 4–5 คำขอต่อคลิป) สคริปต์พิมพ์จำนวนคำขอก่อนเจนทุกครั้ง ถ้าโควตาหมดมันจะหยุดพร้อมบอกว่ารอนานเท่าไร ไฟล์ที่เจนแล้วยังอยู่ รันซ้ำวันถัดไปทำต่อได้ ทางเลือกอื่นคือเปิด billing ที่ AI Studio (คิดตามจริง ราคา ณ ต.ค. 2026 เสียงออกประมาณ 9 ดอลลาร์ต่อล้าน token ซึ่งคลิป 120 วินาทีน่าจะอยู่ในหลักไม่กี่เซนต์ถึงสิบกว่าเซนต์ ตัวเลขนี้ผมประมาณเอง ยังไม่ได้วัดจากการใช้จริง)
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

# 2) ทั้งบท: narration.txt, 1 ฉาก = 1 ย่อหน้า (คั่นบรรทัดว่าง) -> part_01.wav ... + voiceover.wav
#    --group N = รวม N ย่อหน้าต่อ 1 คำขอ (free tier วันละ 10 คำขอ ใช้ 3–4 สำหรับ 15 ฉาก)
uv run --with "google-genai>=2.25" python "$TTS" \
  narration.txt --voice female --group 4 --out voice/      # ผู้หญิง (Leda); --voice male = ผู้ชาย (Puck)

# 3) เทียบเสียง: 1 เสียง = 1 คำขอ (ค่าเริ่มต้น Leda, Puck, Kore หรือกำหนดเองด้วย --voices) เสียงหลักเลือกไว้แล้ว ไม่ต้องรันถ้าไม่จำเป็น
uv run --with "google-genai>=2.25" python "$TTS" \
  --audition "ประโยคทดสอบ" --voices Zephyr,Leda,Callirrhoe --out voice/
```

ลำดับที่ควรทำ:
1. **ถามเฉพาะสิ่งที่ยังไม่รู้**: ผู้หญิงหรือผู้ชาย (ถ้าผู้ใช้ไม่บอก ใช้ผู้หญิง) และบทอยู่ที่ไหน
2. **เตรียมบทก่อนเจน**: ถ้าบทยังเป็นภาษาเขียน ตัวเลข ศัพท์อังกฤษ หรือมีเลขอ้างอิง ให้ปรับตาม `references/thai-narration-style.md` (อ่านเมื่อต้องเขียนหรือแก้บท) สคริปต์ตัดเลขอ้างอิง `[1]` และแปลง `[หยุดสั้น]`/`[หยุดยาว]` ให้อัตโนมัติ และเตือนเมื่อพบตัวเลข อักษรอังกฤษ หรือสำนวนแข็ง ๆ ให้แก้บทตามคำเตือนก่อนเจนต่อ เพราะเจนซ้ำเสียโควตา
3. **เจน** แล้วตรวจด้วยเครื่องมือ: `ffprobe -v error -show_entries format=duration -of csv=p=0 voice/voiceover.wav`
4. **ส่งมอบ**: บอก path ไฟล์ เสียงที่ใช้ และความยาว แล้วให้ผู้ใช้ฟังเอง ผมฟังเสียงไม่ได้ จึงห้ามอ้างว่า "เสียงเป็นธรรมชาติ" ให้บอกว่าตรวจแค่รูปแบบไฟล์และความยาว
5. ท่อนไหนไม่ดี: ลบ `part_XX.wav` ของท่อนนั้นแล้วรันซ้ำ (สคริปต์ข้ามท่อนที่มีแล้ว และกินโควตาแค่ท่อนที่ขาด) ใช้ `--group` เท่าเดิมเสมอ ไม่งั้นการแบ่งท่อนจะเปลี่ยน หรือใช้ `--force` เพื่อเจนทับทั้งหมด

### ข้อควรระวัง

- โมเดลอ่านทุกตัวอักษรของบท อย่าใส่คำกำกับท่าทางหรือหัวข้อลงไปในไฟล์บท
- style ในสคริปต์สั้นโดยตั้งใจ (style ยาวทำให้เสียงเพี้ยน) อย่าเพิ่ม director's notes ยาว ๆ
- **ยังไม่ได้ทดสอบกับ API จริง**: การรวมหลายย่อหน้าต่อคำขอ (`--group`) ว่าโมเดลรับความยาวประมาณ 30 วินาทีต่อคำขอได้ดีและเสียงไม่เพี้ยนกลางท่อน (ทดสอบได้แค่ด้วย client จำลองเพราะโควตาวันที่ 8 ต.ค. หมด) ถ้าท่อนยาวแล้วเสียงเพี้ยนให้ลด `--group` และบอกผู้ใช้ตรง ๆ ว่าต้องใช้โควตามากขึ้นหรือเปิด billing
- tag หยุด `<short pause>`/`<long pause>` ยังไม่ได้ยืนยันด้วยการฟังว่าทำงานกับเสียงไทย ถ้าผู้ใช้บอกว่าไม่หยุด ให้ลดการพึ่ง tag และใช้ประโยคสั้นแทน
- ถ้าบัญชีผู้ใช้ผูก billing แบบจ่ายเงินไว้ การเจนอาจมีค่าใช้จ่าย (ราคา paid ณ ต.ค. 2026: ประมาณ 0.50 ดอลลาร์ต่อล้าน token ข้อความ และ 9 ดอลลาร์ต่อล้าน token เสียง จนถึงสิ้นปี 2026 แล้วเพิ่มเป็นสองเท่า) ให้บอกผู้ใช้ก่อนถ้ารู้ว่าใช้แบบจ่ายเงิน
- งานวิดีโอที่ใช้ ElevenLabs ใน pipeline `hearyourvoice` ให้ใช้ skill นั้น skill นี้เป็นทางเลือกฟรีสำหรับเสียงไทย ถ้าจะป้อนบทจาก `voiceover-v1.md` ให้แยกเฉพาะข้อความหลัง `VO:` ลง narration.txt ก่อน
- ถ้า API ตอบ error ที่ไม่ใช่ rate limit ให้อ่านข้อความ error แล้วรายงานตรง ๆ ห้ามเดา และถ้าเรียก `interactions.create` ไม่ได้เพราะ SDK เก่า ให้เช็กว่า `google-genai>=2.25`

---

## ขั้นที่ 7 — ประกอบ MP4 (สรุป)

รายละเอียดเต็ม (เครื่องมือ, storyboard JSON, การคิดเวลา, เสียง, การตรวจ) อยู่ใน `references/video-pipeline.md` ย่อ ๆ:

1. ทำ **storyboard JSON** จากบท (รูปแบบ myth-busting: เริ่มจาก `assets/templates/myth-busting-120s.storyboard.json`, ใส่ `fonts`, `subtitle_box`, `speaker`, และรันด้วย `--logo-at end --logo-seconds 6`) (หนึ่งฉากต่อหนึ่งย่อหน้า `narration` ที่ส่งเข้า TTS) เลือก `bg`, `layout`, `layers` (ตัวละคร "น้องฟ้า" + ไอคอนแบน) และ `overlays` (ข้อความไทยทั้งหมดต้องมาทาง overlay/ซับ ห้ามวาดตัวอักษรไทยด้วย cairo) แล้วรัน `make_video.py validate`
2. **ถามผู้ใช้**: สัดส่วนที่ต้องการ, path ไฟล์โลโก้ (ไม่มีโลโก้ = ไม่มีบัมเปอร์/เสียงกระดิ่ง, ห้าม commit รูปของผู้ใช้เข้า repo), fps (30), ต้องการบัมเปอร์ท้ายหรือไม่
3. รัน `make_video.py build ...` (ใช้ `uv run --with pycairo --with numpy --with pillow --with pythainlp`) ทดสอบระบบด้วย `make_video.py demo` ก่อน ไม่เสียโควตา TTS
4. ตรวจตามหัวข้อ "ตรวจก่อนส่งมอบ": ตัวเลข ffprobe, `check.py`, เปิด contact sheet ทุกสัดส่วน และบอกผู้ใช้ตรง ๆ ว่าผมฟังเสียง/เพลงไม่ได้

ต้องมี `ffmpeg-skill` ติดตั้งอยู่ (สคริปต์หาให้เอง หรือ `FFMPEG_SKILL_DIR`) ถ้าไม่มีให้บอกผู้ใช้แล้วหยุด ห้ามเรียก ffmpeg ดิบแทน

## ขั้นที่ 8 — Carousel + แคปชัน (สรุป)

รายละเอียด แม่แบบแคปชัน และกฎอยู่ใน `references/post-package.md` ย่อ ๆ: เขียน `carousel.json` จาก Fact Card/REFERENCE MAP ของขั้น 3 แล้วรัน `make_video.py carousel carousel.json --out out/ --name clip --aspect 4:5` ได้ PNG 2 ไฟล์ (ข้อความไทยผ่าน ASS เหมือนวิดีโอ) เปิดดูภาพก่อนส่งมอบเสมอ จากนั้นเขียนแคปชันตามแม่แบบ: อ้างเฉพาะงานที่เปิดอ่านได้จริงในขั้น 2 (ผู้แต่ง วารสาร ปี PMID), งานเชิงสังเกตใช้คำว่า "สัมพันธ์กับ" และมีหมายเหตุ, จบด้วยประโยคปฏิเสธความรับผิดชอบ และบอกผู้ใช้ว่าปรับคำอะไรเพื่อความถูกต้อง

## โหมดทีม subagent (แบบ hearyourvoice)

ใช้เมื่อผู้ใช้อยากให้ทำทั้งคลิปแบบขนาน subagent อยู่ในโฟลเดอร์ `agents/` ของ repo (ถ้าติดตั้งเป็น skill ในโฟลเดอร์ ให้คัดลอก `agents/*.md` ไป `~/.claude/agents/`):

- `hcth-producer` ทำทั้งคลิปเอง หยุดทุก gate (หัวข้อ, หลักฐาน, ก่อนใช้โควตา TTS, สัดส่วน+โลโก้) และ **แตกงานแนวขวางเท่านั้น**
- `hcth-storyboarder` ×2–3 ขนานกันคนละชุดฉาก
- `hcth-assembler` รันบิลด์และตรวจ ffprobe/check/look
- `hcth-qa` ขนานกันคนละสัดส่วน อ่านอย่างเดียว ตรวจซับตรงกับบท ตัวเลขตรงหลักฐาน ภาษาไทยไม่เป็นสี่เหลี่ยม ซับอยู่ในโซนปลอดภัย

อย่าให้ subagent เรียก Gemini TTS ซ้ำ (โควตาวันละ 10 คำขอ) และห้าม commit/push ถ้าผู้ใช้ไม่สั่ง
