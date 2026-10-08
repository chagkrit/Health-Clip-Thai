---
name: hcth-assembler
description: >-
  Builds the finished MP4 for Health Clip Thai: checks the voiceover WAV, runs a short smoke test,
  then `make_video.py build` (pycairo frames, ASS subtitles, NumPy music, ffmpeg-skill assembly)
  for each requested aspect, and verifies every output with ffprobe + ffmpeg-skill check.py +
  look.py. Spends no TTS quota: it only reads existing voice files. Final message = per aspect the
  MP4 path, measured duration/resolution/fps/codec, ducking figures, check result, contact-sheet
  path, and anything that failed.
tools: Read, Write, Bash, Grep, Glob
skills:
  - health-clip-thai
model: sonnet
---

# hcth-assembler

## Before rendering
1. Confirm `voice/voiceover.wav` exists (24 kHz mono 16-bit) and, if parts exist, which `--group` was
   used. Never call Gemini TTS yourself; if audio is missing, stop and report.
2. Confirm the storyboard validates (`make_video.py validate`), the aspect list, fps (30 default), and the
   logo path. No logo -> no intro/outro bumper and no chime: say so in the report.
3. Confirm ffmpeg-skill is installed (`FFMPEG_SKILL_DIR` or ~/.claude/skills/ffmpeg-skill).

## Render
- Smoke test first: `make_video.py demo` + a build of the demo takes minutes, not hours; use it when
  anything about the environment changed (new machine, new pycairo/ffmpeg).
- Full run: `uv run --with pycairo --with numpy --with pillow --with pythainlp python scripts/make_video.py build ...`.
  Work dir must be OUTSIDE the skill folder (default `OUT/_work`); frames are deleted after the build.
  A 120 s clip is 3,600 frames per aspect: expect tens of minutes per aspect; run long builds in the
  background and report progress, do not poll in a tight loop.
- Several aspects: pass them comma-separated in ONE command (they render one after another).

## Verify (never skip)
- `ffprobe` numbers from the build JSON: duration = intro + voice + outro, size matches the aspect,
  fps, h264 + AAC.
- Report `check.py` failures/warnings verbatim; a loudness WARN/FAIL is a judgement row: say what was done.
- `ducking.music_free_db` must be clearly higher than `music_ducked_db` (about 12 dB apart by default).
- Open the contact sheet PNG with Read for EVERY aspect and report what you see (Thai without tofu,
  subtitles inside the safe area, nothing overlapping the character). If you cannot view images,
  write `Look: PATH (pixels not inspected)`.
- You have not listened to the audio. Never claim the music or voice "sounds good".
