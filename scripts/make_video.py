#!/usr/bin/env python3
"""health-clip-thai: build a finished MP4 from a storyboard JSON + Thai voiceover WAV.

Run with uv so nothing is installed globally:
  uv run --with pycairo --with numpy --with pillow --with pythainlp python make_video.py build \
      --storyboard storyboard.json --voice voice/voiceover.wav --aspect 16:9 --logo logo.png --out out/
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from clipvideo.layout import ASPECTS  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="storyboard + voice -> MP4 (H.264/AAC)")
    b.add_argument("--storyboard", required=True)
    b.add_argument("--voice", required=True, help="voiceover.wav (24 kHz mono 16-bit from gemini_tts.py)")
    b.add_argument("--parts-dir", help="voice/ with part_XX.wav: makes scene boundaries exact (needs --group)")
    b.add_argument("--group", type=int, help="the --group N used when the voice was generated")
    b.add_argument("--aspect", default="16:9", help=f"one or more of {', '.join(ASPECTS)} (comma-separated)")
    b.add_argument("--fps", type=int, default=30)
    b.add_argument("--logo", help="logo image: cropped to a circle inside an animated ring (intro bumper + chime)")
    b.add_argument("--outro", action="store_true", help="repeat the logo bumper at the end")
    b.add_argument("--music", default="calm", choices=["calm", "bright", "gentle"])
    b.add_argument("--music-level", type=float, default=0.55)
    b.add_argument("--duck-db", type=float, default=-12.0, help="music reduction while the voice speaks")
    b.add_argument("--lufs", type=float, default=-14.0)
    b.add_argument("--out", required=True)
    b.add_argument("--name")
    b.add_argument("--work", help="scratch dir for frames (default OUT/_work)")
    b.add_argument("--jobs", type=int)
    b.add_argument("--keep-frames", action="store_true")

    v = sub.add_parser("validate", help="check a storyboard JSON without rendering")
    v.add_argument("storyboard")

    d = sub.add_parser("demo", help="write a neutral demo storyboard + synthetic voice (no TTS quota)")
    d.add_argument("--out", required=True)

    m = sub.add_parser("music", help="render only the background music WAV")
    m.add_argument("--seconds", type=float, default=30)
    m.add_argument("--mood", default="calm", choices=["calm", "bright", "gentle"])
    m.add_argument("-o", "--output", required=True)

    a = ap.parse_args(argv)
    if a.cmd == "validate":
        from clipvideo.build import load_storyboard
        sb = load_storyboard(a.storyboard)
        print(f"OK: {len(sb['scenes'])} scenes")
    elif a.cmd == "demo":
        from clipvideo.selftest import write_demo
        sb, wav, dur = write_demo(a.out)
        print(json.dumps({"storyboard": str(sb), "voice": str(wav), "voice_seconds": round(dur, 2)}, ensure_ascii=False))
    elif a.cmd == "music":
        from clipvideo import music
        x = music.synth_music(a.seconds, a.mood)
        import numpy as np
        music.write_wav(a.output, np.stack([x, x], 1))
        print(a.output)
    else:
        from clipvideo.build import build
        build(a)


if __name__ == "__main__":
    main()
