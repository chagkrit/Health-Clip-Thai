# Health Clip Thai

Claude Code skill for making **short Thai health and medical explainer clips** (about 120 s, 2D cartoon) from topic to a **finished MP4**. The voice step uses free-tier Google Gemini TTS (`gemini-3.8-flash-tts`) through an AI Studio API key, so a Gemini subscription is not required. Step 7 draws the animation, subtitles, music and logo ring with code and assembles a 1080p H.264/AAC MP4 in 16:9, 9:16, 1:1 or 4:5.

ชุดทำคลิปสุขภาพภาษาไทยตั้งแต่เลือกหัวข้อ หาหลักฐาน เขียนบท ซับไตเติล เสียงพากย์ไทย จนถึงไฟล์ MP4 สำเร็จรูป (ภาพการ์ตูน แอนิเมชัน เพลง และโลโก้สร้างด้วยโค้ดทั้งหมด)

## Workflow

| Step | What it does | Pauses for you |
|---|---|---|
| 1 | Propose 10 health topics that suit 2D cartoon storytelling | pick one |
| 2 | Find 3–5 real studies (PubMed / Semantic Scholar), table with PMID, DOI, limits | confirm evidence |
| 3 | Write the 120 s spoken-Thai script with citations and a medical disclaimer | |
| 4 | Convert to ~8 s scene prompts for AI video generators (original characters, no text in frame) | |
| 5 | TTS-ready script and `.srt` subtitles | |
| 6 | Record Thai voiceover WAV with Gemini TTS | |
| 7 | Build the finished MP4: code-drawn cartoon animation, ASS Thai subtitles, synthesized music, logo ring, ffmpeg-skill assembly | aspect ratio, logo path |

You can enter at any step, for example paste a finished script and ask only for the audio. The full prompts and strict evidence rules are in `references/workflow-prompts.md`.

## Step 7: finished MP4 (new)

| Part | Tool |
|---|---|
| Drawing and animation | Python + **pycairo**: original host character "Nong Fah" + 22 flat props (heart, brain, clock, bars, ring, ...) on animated backgrounds; the mouth follows the real voiceover loudness |
| Thai text and subtitles | **ASS + libass** (cairo cannot shape Thai, so no text is ever drawn in the picture) |
| Fonts | **Sarabun** from Google Fonts (SIL OFL, commercial use allowed), bundled in `assets/fonts/` with `OFL.txt` |
| Music | **NumPy** synthesis from scratch: melody, bass, shaker, chord pad and a bell chime on the logo reveal. No samples, so no music licensing. Ducked under the voice automatically |
| Logo | **Pillow** crops your picture to a circle, drawn over an animated ring (`--logo PATH`; your image is never copied into the repo) |
| Assembly | **ffmpeg** through the separate `ffmpeg-skill` skill's scripts: `sequence` -> `caption --ass` -> `audio --replace` -> `loudness` -> `check` -> `look`; H.264 video + AAC audio |
| Aspects | `16:9` 1920x1080 (default), `9:16` 1080x1920, `1:1` 1080x1080, `4:5` 1080x1350. Layout and subtitles scale per aspect; 9:16 keeps the bottom fifth free of text |

Timing comes from the measured voiceover (part lengths + the 0.35 s join gap, scene cuts snapped to real pauses), never from the planned script.

```bash
S=~/.claude/skills/health-clip-thai/scripts
R="uv run --with pycairo --with numpy --with pillow --with pythainlp python"
$R $S/make_video.py demo --out /tmp/demo       # no-TTS-quota smoke test (synthetic voice)
$R $S/make_video.py build --storyboard storyboard.json --voice voice/voiceover.wav \
    --parts-dir voice --group 4 --aspect 16:9,9:16 --logo ~/logo.png --outro --out out/ --name clip
```

Needs: `uv`, a cairo toolchain for pycairo (`brew install cairo pkgconf` on macOS), `pythainlp` (pulled in by `uv --with`; word-safe Thai line breaks), `ffmpeg` with libass + libx264, and the **ffmpeg-skill** skill (found automatically in `~/.claude/skills/ffmpeg-skill` or via `FFMPEG_SKILL_DIR`). Full spec (storyboard JSON, timing rules, audio chain, checks): `references/video-pipeline.md`.

### Subagent team (hearyourvoice style)

`agents/` ships `hcth-producer` (runs one clip, stops at human gates, spawns across only), `hcth-storyboarder` (parallel, one per batch of scenes), `hcth-assembler` (build + verify) and `hcth-qa` (read-only, one per aspect). As a plugin they load automatically; for a skill installed in `~/.claude/skills/` copy `agents/*.md` to `~/.claude/agents/`.

## Voice features

- Female (`Leda`) and male (`Puck`) presets: `--voice female` / `--voice male`, or any other Gemini voice by name
- `--audition` renders one sentence in several voices so you can choose by ear
- Splits a script into parts (`--group N` paragraphs per request), waits out short rate limits, stops with a clear message when the daily quota is gone, skips parts already rendered (re-run to resume), and joins them into `voiceover.wav`
- Prepares the script for speech: removes citation numbers like `[1]`, converts `[หยุดสั้น]` / `[หยุดยาว]` to pause tags, and warns about digits, Latin letters and stiff written-Thai phrases that make narration sound like AI
- `references/thai-narration-style.md`: how to write spoken Thai, read numbers and terms, and health-specific wording

## Install

```
/plugin marketplace add chagkrit/Health-Clip-Thai
/plugin install health-clip-thai@health-clip-thai
```

Requires [`uv`](https://docs.astral.sh/uv/) (the scripts run with `uv run --with ...`, nothing is installed globally). `ffprobe` is optional for checking audio duration; step 7 needs the extra tools listed above.

## API key

1. Create a key at <https://aistudio.google.com/apikey>. A Google AI Pro / Gemini app subscription does **not** include API quota, but the AI Studio free tier covers `gemini-3.8-flash-tts` at the time of writing (Oct 2026; check the [pricing page](https://ai.google.dev/gemini-api/docs/pricing)).
2. Save it yourself, never paste it into a chat: `GEMINI_API_KEY=...` in `~/.config/gemini-tts/.env` or `~/.env` (or the `GEMINI_API_KEY` environment variable, or a `.env` in the working directory). Only the Gemini key variables are read from these files.

## Usage

Ask Claude, e.g. "พากย์เสียงผู้หญิงจากบทนี้", or run directly:

```bash
uv run --with "google-genai>=2.25" python scripts/gemini_tts.py narration.txt --voice female --out voice/
uv run --with "google-genai>=2.25" python scripts/gemini_tts.py --text "สวัสดีครับ" --voice male --out voice/
uv run --with "google-genai>=2.25" python scripts/gemini_tts.py --audition "ประโยคทดสอบ" --voices Zephyr,Leda --out voice/
```

If a part sounds wrong, delete its `part_XX.wav` and run the same command (same `--group`) again; only the missing part is regenerated.

**Free-tier quota:** on 8 Oct 2026 the API reported a limit of **10 requests per day** for `gemini-3.8-flash-tts` (`generate_content_free_tier_requests`). One request = one call to the model, so use `--group 3` or `--group 4` for a 15-scene clip and avoid needless voice auditions. If the quota runs out the script stops and tells you; completed parts are kept. Enabling billing in AI Studio removes the cap (pay per use).

## Notes and limits

- Step 7 was verified with a synthetic voice (no TTS quota used); no real Gemini TTS audio has been through it yet. I cannot listen: voice naturalness and music pleasantness are unverified, check by ear.
- Subtitle/scene timing inside a TTS part is an estimate snapped to pauses, not forced alignment (about 0.5 s drift possible).

- `gemini-3.8-flash-lite-tts` does not support Thai; do not use it.
- Verified: a live call to the API returns a 24 kHz mono 16-bit WAV for all voices tried. Not verified by listening: how natural the Thai sounds, and whether `<short pause>` / `<long pause>` tags take effect. Always listen to the result.
- The Google docs pages do not list per-model free-tier limits; the 10/day figure above comes from the API's own error message, so check <https://aistudio.google.com/rate-limit> for your project.
- Audio is generated by AI. Disclose synthetic narration where a platform or context requires it.

## License

MIT
