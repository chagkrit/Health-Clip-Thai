# ขั้นที่ 7 — ประกอบเป็น MP4 สำเร็จรูป

ภาพการ์ตูน แอนิเมชัน ซับไตเติล เพลง และโลโก้ ถูกสร้างและประกอบด้วยโค้ดทั้งหมด ไม่ต้องใช้ AI สร้างวิดีโอและไม่มีเพลงสำเร็จรูป

| ส่วน | เครื่องมือ |
|---|---|
| วาดภาพและแอนิเมชัน | Python + **pycairo** (ตัวละครต้นฉบับ "น้องฟ้า" + ไอคอนแบน 22 แบบ) |
| ข้อความไทยและซับไตเติล | ไฟล์ **ASS** แล้วเผาด้วย **libass** (cairo ไม่จัดสระ/วรรณยุกต์ไทย จึงไม่วาดตัวอักษรในภาพเลย) |
| ฟอนต์ | **Sarabun** จาก Google Fonts (SIL OFL ใช้เชิงพาณิชย์ได้) อยู่ใน `assets/fonts/` พร้อม `OFL.txt` |
| เพลงประกอบ | Python + **NumPy** สังเคราะห์ใหม่ทั้งหมด: ทำนอง เบส เสียงเขย่า คอร์ดพื้น และเสียงกระดิ่งตอนขึ้นโลโก้ |
| โลโก้ | **Pillow** ครอปรูปเป็นวงกลม แล้ววาดซ้อนกับวงแหวนเคลื่อนไหว (รูปอ่านจาก `--logo` ไม่ถูกคัดลอกเข้า skill) |
| รวมไฟล์ | **ffmpeg** ผ่านสคริปต์ของ `ffmpeg-skill`: `sequence` → `caption --ass` → `audio --replace` → `loudness` → `check` → `look` ได้ H.264 + AAC |

## ต้องมีอะไรบ้าง

- `uv` (รันด้วย `uv run --with pycairo --with numpy --with pillow --with pythainlp python ...`)
- **pycairo** ต้อง build จากซอร์ส: macOS ต้องมี cairo และ pkg-config (`brew install cairo pkgconf`)
- skill **`ffmpeg-skill`** (หาที่ `$FFMPEG_SKILL_DIR`, `~/.claude/skills/ffmpeg-skill` หรือ cache ของ plugin) และ `ffmpeg` ที่มี libass + libx264
- **pythainlp** (ติดมากับ `uv --with` อยู่แล้ว) ตัดคำไทยเพื่อให้ซับขึ้นบรรทัดใหม่ระหว่างคำ ไม่ตัดกลางคำ ถ้าไม่มีจะตัดได้เฉพาะที่ช่องว่างในบท และอาจตัดกลางคำในสัดส่วนแคบ
- ไฟล์เสียง `voice/voiceover.wav` จากขั้น 6 (หรือ WAV 16-bit อื่น)

## คำสั่ง

```bash
S=~/.claude/skills/health-clip-thai/scripts   # หรือ path ใต้ ~/.claude/plugins/cache/
R="uv run --with pycairo --with numpy --with pillow --with pythainlp python"

# ทดสอบทั้งระบบโดยไม่เสียโควตา TTS (เสียงสังเคราะห์ + บทตัวอย่างที่ไม่มีข้อมูลสุขภาพ)
$R $S/make_video.py demo --out /tmp/demo
$R $S/make_video.py build --storyboard /tmp/demo/demo_storyboard.json \
    --voice /tmp/demo/demo_voice.wav --aspect 16:9 --out /tmp/demo_out

# งานจริง: หลายสัดส่วนในคำสั่งเดียว
$R $S/make_video.py build --storyboard storyboard.json --voice voice/voiceover.wav \
    --parts-dir voice --group 4 --aspect 16:9,9:16,1:1,4:5 --fps 30 \
    --logo ~/path/logo.png --outro --music calm --out out/ --name clip
```

ตัวเลือกสำคัญ: `--aspect` (`16:9` 1920×1080 ค่าเริ่มต้น, `9:16` 1080×1920, `1:1` 1080×1080, `4:5` 1080×1350), `--fps` (30), `--logo`, `--outro`, `--music calm|bright|gentle`, `--duck-db` (-12), `--lufs` (-14), `--work` (โฟลเดอร์เฟรมชั่วคราว ต้องอยู่นอก skill), `--jobs`, `--keep-frames`, `make_video.py validate FILE` ตรวจ storyboard โดยไม่เรนเดอร์

ผลลัพธ์ต่อสัดส่วน: `NAME_16x9.mp4`, `NAME_16x9.srt`, `NAME_16x9_sheet.png` (contact sheet), `_work/16x9/plan.json` (เวลาแต่ละฉากที่วัดจากเสียงจริง) และสรุป JSON (ffprobe, ducking, ผล check, เวลาแต่ละขั้น)

## เวลามาจากเสียงพากย์ที่วัดจริง

- ความยาวคลิป = บัมเปอร์โลโก้ (3 วินาที ถ้ามี `--logo`) + ความยาวเสียงจริง + บัมเปอร์ท้าย (ถ้า `--outro`)
- **ถ้ามี `--parts-dir` + `--group`** ขอบเขตของแต่ละ part คือความยาวไฟล์ `part_XX.wav` จริง + ช่องว่างต่อไฟล์ 0.35 วินาที (เท่ากับที่ `gemini_tts.py` ใช้) ถ้าจำนวน part หรือความยาวรวมไม่ตรงกับ `voiceover.wav` ระบบจะเตือนและถอยไปใช้วิธีด้านล่าง
- **ขอบเขตฉากภายใน part (หรือทั้งไฟล์ถ้าไม่มี parts)**: ประมาณตามจำนวนตัวอักษรที่พูดจริงของแต่ละฉาก แล้วขยับไปจุดหยุดเงียบ (≥ 0.12 วินาที) ที่ใกล้ที่สุด
- ซับไตเติลแบ่งตามวลี (ช่องว่างในบทพูด) จัดบรรทัดตามความกว้างเฟรมที่วัดด้วยฟอนต์จริง แล้วแบ่งเวลาด้วยวิธีเดียวกัน **ไม่เปลี่ยนคำในบท**
- ปากตัวละครขยับตามความดังของเสียงพากย์จริง

ข้อจำกัด: การแบ่งเวลาภายใน part เป็นการประมาณ ไม่ใช่ forced alignment ถ้าเสียงหยุดไม่ตรงกับย่อหน้า ซับอาจเลื่อนได้ราว 0.5 วินาที ลดความเสี่ยงด้วยการใช้ `--group` น้อยลง (แต่เสียโควตา TTS มากขึ้น) และให้ `hcth-qa` เทียบ `plan.json` กับไฟล์ซับ

## Storyboard JSON

```json
{
  "title": "ชื่อคลิป",
  "scenes": [
    {
      "id": 1,
      "narration": "ย่อหน้าเดียวกับที่ส่งเข้า TTS (ตรงตัวอักษร ใช้คำนวณเวลา)",
      "subtitle": "ข้อความที่แสดงถ้าต่างจากเสียง เช่น 7 ชั่วโมง (ไม่บังคับ)",
      "bg": "sky",
      "layout": "duo",
      "divider": false,
      "layers": [
        {"type": "character", "slot": "a", "mood": "happy", "pose": "wave", "anim": "slide_left"},
        {"type": "prop", "kind": "clock", "slot": "b", "hours": 7, "anim": "pop", "delay": 0.6, "idle": "float"}
      ],
      "overlays": [
        {"text": "7 ชั่วโมง", "slot": "b", "dy": 0.6, "start": 1.0, "style": "number"}
      ]
    }
  ]
}
```

- **`bg`**: `sky` `warm` `mint` `lavender` `clinic` `night`
- **`layout` / slot** (ตำแหน่งปรับตามสัดส่วนเอง ไม่ต้องใส่พิกเซล): `solo` (a) · `duo` (a ตัวละคร/หลัก, b รอง) · `split` (a|b เท่ากัน, แนวตั้งเป็นบน/ล่าง) · `trio` (a b c) · `quad` (a b c d)
- **layer**: `type` = `character` หรือ `prop`; ร่วมกัน: `slot`, `scale`, `dx`/`dy` (หน่วยเป็นสัดส่วนของช่อง), `rot`, `flip`, `delay` (วินาทีนับจากต้นฉาก), `anim` = `pop` `fade` `slide_left` `slide_right` `slide_up` `none`, `idle` = `float` `pulse` `wobble` `none`, `state`: `dim`
- **character**: `mood` = `happy` `think` `worry` `wow`; `pose` = `idle` `wave` `point` `think` `cheer`; `coat`/`scrubs` เปลี่ยนสีได้
- **prop `kind`**: `heart brain moon sun clock bed zzz apple drop magnifier doc check cross mug phone dumbbell plate shield bars ring timeline sparkle`; พารามิเตอร์ที่ใช้ได้: `color`, `hours` (clock), `values`/`colors` (bars, ค่า 0–1), `progress` (ring, 0–1), `points` (timeline), `lines` (doc)
- **overlay** (ข้อความไทยในฉาก ผ่าน ASS): `text` (ขึ้นบรรทัดใหม่ด้วย `\n`), ตำแหน่งแบบ `slot` + `dx`/`dy` หรือ `at: [fx, fy]` (สัดส่วนของเฟรม), `start`/`end` (วินาทีในฉาก; `end` ว่าง = จนจบฉาก), `style` = `title` `label` `number` `note`, `size` = `s` `m` `l` ข้อความกว้างเกินเฟรมจะถูกย่อให้พอดีและรายงานใน `warnings`

ใช้ไอคอน/ตัวละครที่มีให้เท่านั้น ถ้าต้องการภาพใหม่ ให้เพิ่มฟังก์ชันใน `scripts/clipvideo/props.py` (ลงทะเบียนใน `PROPS`) แล้วรัน `validate`

## เสียง

ลำดับสัญญาณ: เสียงพากย์ (ปรับ peak ประมาณ -1 dBFS) + เพลงที่ลดระดับอัตโนมัติเมื่อมีเสียงพูด (ตัวตามซองเสียงจากเสียงพากย์เอง, `--duck-db` -12 dB, attack 80 ms, release 450 ms) + เสียงกระดิ่งตอนโลโก้ขึ้น → soft limiter → `loudness.py` ที่ -14 LUFS (ค่าเริ่มต้น เหมาะกับ YouTube; ปรับด้วย `--lufs`) สรุปตัวเลข `ducking.music_free_db` กับ `music_ducked_db` ออกมาในผลลัพธ์ทุกครั้ง

## ตรวจก่อนส่งมอบ

1. ตัวเลขจาก ffprobe: ความยาว ความละเอียด fps codec ตรงตามที่ขอ
2. `check.py` (YouTube สำหรับ 16:9/1:1, Instagram สำหรับ 4:5, Shorts สำหรับ 9:16) รายงานทุก FAIL/WARN ตรง ๆ
3. เปิดรูป contact sheet **ทุกสัดส่วน** เช็กว่าไทยไม่เป็นสี่เหลี่ยม ซับไม่ทับตัวละคร และใน 9:16 ซับอยู่เหนือโซน UI ด้านล่าง
4. ผมฟังเสียงไม่ได้ จึงตรวจเพลงและเสียงเป็นตัวเลข (ระดับเสียง ducking) ไม่ใช่ความไพเราะ ให้ผู้ใช้ฟังเอง

## แก้ปัญหา

- `ไม่พบ ffmpeg-skill`: ติดตั้ง skill นั้น หรือ `export FFMPEG_SKILL_DIR=...`
- pycairo build ไม่ผ่าน (`Did not find pkg-config`): `brew install pkgconf`
- ซับขึ้นแต่ฟอนต์ผิด: ต้องมี `assets/fonts/Sarabun-*.ttf` (สคริปต์ส่ง `--fonts-dir` ให้ libass เสมอ)
- เรนเดอร์ช้า: ใช้ `--jobs N` เพิ่ม worker เฟรมเป็น PNG ชั่วคราวใน `--work` (ราว 100–150 KB ต่อเฟรม) ลบอัตโนมัติเมื่อจบ ยกเว้น `--keep-frames`
