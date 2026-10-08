"""Pipeline: storyboard + voiceover -> frames (pycairo) -> ASS -> music (NumPy) -> MP4 via
ffmpeg-skill's scripts (sequence -> caption --ass -> audio --replace -> loudness -> check -> look)."""
import glob
import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import cairo
import numpy as np
from PIL import Image

from . import logo as logomod
from . import music as musicmod
from .draw import clamp, ease_in_out
from .layout import ASPECTS, SUBTITLE
from .scenes import render_scene, validate_scene
from .subs import FONT_DIR, SPEAKER_STYLE, build_ass, font_set, make_cues, resolve_overlay_xy
from .timing import plan_scenes, speech_curve, read_wav

XFADE_S = 0.30

# ---------------------------------------------------------------- ffmpeg-skill lookup


def find_ffmpeg_skill():
    cands = [os.environ.get("FFMPEG_SKILL_DIR", "")]
    cands += [str(Path.home() / ".claude/skills/ffmpeg-skill")]
    cands += glob.glob(str(Path.home() / ".claude/plugins/cache/*/ffmpeg-skill/*"))
    cands += glob.glob(str(Path.home() / ".claude/plugins/marketplaces/*/ffmpeg-skill"))
    for c in cands:
        if c and (Path(c) / "scripts" / "sequence.py").exists():
            return Path(c)
    raise SystemExit(
        "ไม่พบ ffmpeg-skill (ต้องมี scripts/sequence.py, caption.py, audio.py, loudness.py, check.py, look.py). "
        "ติดตั้ง skill นั้นหรือตั้งตัวแปร FFMPEG_SKILL_DIR ชี้ไปที่โฟลเดอร์ของมัน")


def fs_run(fs, script, *args, fatal=True):
    """Run one ffmpeg-skill script with --json-brief; return its parsed JSON. Fails loudly."""
    cmd = [sys.executable, str(fs / "scripts" / f"{script}.py"), *map(str, args), "--json-brief"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    try:
        js = json.loads(out[out.index("{"):]) if "{" in out else {}
    except json.JSONDecodeError:
        js = {"raw": out[-600:]}
    if (r.returncode != 0 or js.get("status") == "failed") and fatal:
        msg = (js.get("error") or {}).get("message") or r.stderr.strip()[-600:] or out[-600:]
        raise SystemExit(f"ffmpeg-skill {script}.py ล้มเหลว (exit {r.returncode}): {msg}")
    js["_returncode"] = r.returncode
    return js


# ---------------------------------------------------------------- rendering workers

_G = {}


def _init(aspect, fps, logo_path, logo_d, speech):
    W, H = ASPECTS[aspect]
    _G.update(W=W, H=H, aspect=aspect, fps=fps, speech=speech, logo_d=logo_d, cache={})
    if logo_path:
        _G["logo"] = logomod.to_cairo(logomod.circular_logo(logo_path, logo_d))


def _draw_seg(ctx, seg, t):
    W, H = _G["W"], _G["H"]
    if seg["kind"] == "bumper":
        logomod.draw_bumper(ctx, W, H, t, seg["dur"], _G["logo"], _G["logo_d"], outro=seg.get("outro", False))
    else:
        sp = 0.0
        fi = int(round((seg["f0"] + t * _G["fps"]) - seg["voice_f0"]))
        arr = _G["speech"]
        if 0 <= fi < len(arr):
            sp = float(arr[fi])
        render_scene(ctx, W, H, _G["aspect"], seg["scene"], t, sp, seg["seed"])


def _prev_last(prev):
    key = prev["f0"]
    if key not in _G["cache"]:
        s = cairo.ImageSurface(cairo.FORMAT_RGB24, _G["W"], _G["H"])
        c = cairo.Context(s)
        _draw_seg(c, prev, (prev["f1"] - prev["f0"] - 1) / _G["fps"])
        _G["cache"][key] = s
    return _G["cache"][key]


def _render_chunk(task):
    seg, prev, a, b, outdir = task
    W, H, fps = _G["W"], _G["H"], _G["fps"]
    for f in range(a, b):
        t = (f - seg["f0"]) / fps
        s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        ctx = cairo.Context(s)
        if prev is not None and t < XFADE_S:
            ctx.set_source_surface(_prev_last(prev), 0, 0)
            ctx.paint()
            ctx.push_group()
            _draw_seg(ctx, seg, t)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(ease_in_out(t / XFADE_S))
        else:
            _draw_seg(ctx, seg, t)
        s.flush()   # PIL + zlib level 1 is ~3x faster than cairo's PNG writer on 1080p frames
        Image.frombuffer("RGB", (W, H), s.get_data(), "raw", "BGRX", s.get_stride(), 1).save(
            str(Path(outdir) / f"frame_{f:06d}.png"), compress_level=1)
    return b - a


# ---------------------------------------------------------------- storyboard

def load_storyboard(path):
    sb = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes = sb.get("scenes")
    if not scenes:
        raise SystemExit("storyboard ไม่มี scenes")
    errs = []
    if sb.get("fonts") is not None:
        font_set(sb["fonts"])
    for i, sc in enumerate(scenes, 1):
        errs += validate_scene(sc, i)
        if sc.get("speaker") not in (None, *SPEAKER_STYLE):
            errs.append(f"scene {sc.get('id', i)}: speaker ต้องเป็น {', '.join(SPEAKER_STYLE)}")
    if errs:
        raise SystemExit("storyboard ไม่ผ่านการตรวจ:\n  " + "\n  ".join(errs))
    return sb


def narration_scenes(sb):
    return [{**sc, "narration": sc["narration"]} for sc in sb["scenes"]]


# ---------------------------------------------------------------- main build

def build(args):
    sb = load_storyboard(args.storyboard)
    scenes = sb["scenes"]
    voice = Path(args.voice)
    if not voice.exists():
        raise SystemExit(f"ไม่พบไฟล์เสียง {voice}")
    fps = args.fps
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = args.name or Path(args.storyboard).stem
    aspects = [a.strip() for a in args.aspect.split(",")]
    for a in aspects:
        if a not in ASPECTS:
            raise SystemExit(f"aspect '{a}' ไม่รู้จัก ({', '.join(ASPECTS)})")
    logo_path = args.logo
    if logo_path and not Path(logo_path).exists():
        raise SystemExit(f"ไม่พบไฟล์ logo {logo_path}")
    fs = find_ffmpeg_skill()
    plan, vtotal, notes, (vx, vsr, runs) = plan_scenes(
        scenes, voice, Path(args.parts_dir) if args.parts_dir else None, args.group)
    for n in notes:
        print("หมายเหตุ:", n, file=sys.stderr)

    at = "both" if args.outro else args.logo_at
    intro = args.logo_seconds if (logo_path and at in ("start", "both")) else 0.0
    outro = args.logo_seconds if (logo_path and at in ("end", "both")) else 0.0
    total = intro + vtotal + outro
    nframes = int(round(total * fps))
    results = []
    for aspect in aspects:
        results.append(_build_one(args, fs, sb, scenes, plan, vtotal, vx, vsr, runs, aspect, fps,
                                  out, name, logo_path, intro, outro, total, nframes, len(aspects) > 1))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return results


def _build_one(args, fs, sb, scenes, plan, vtotal, vx, vsr, runs, aspect, fps, out, name, logo_path,
               intro, outro, total, nframes, multi):
    W, H = ASPECTS[aspect]
    tag = aspect.replace(":", "x")
    work = Path(args.work or out / "_work") / tag
    frames = work / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir(parents=True, exist_ok=True)

    # segments with exact frame ranges (contiguous)
    segs = []
    if intro:
        segs.append({"kind": "bumper", "dur": intro, "f0": 0, "f1": int(round(intro * fps))})
    bounds = [int(round((intro + p["start"]) * fps)) for p in plan] + [int(round((intro + vtotal) * fps))]
    bounds[0] = segs[-1]["f1"] if segs else 0
    voice_f0 = int(round(intro * fps))
    for i, sc in enumerate(scenes):
        segs.append({"kind": "scene", "scene": sc, "seed": i + 1, "f0": bounds[i], "f1": bounds[i + 1],
                     "voice_f0": voice_f0})
    if outro:
        segs.append({"kind": "bumper", "dur": outro, "f0": bounds[-1], "f1": nframes, "outro": True})
    segs[-1]["f1"] = nframes

    # subtitle cues + overlays, in absolute seconds
    cues, overlays, warns = [], [], []
    for i, sc in enumerate(scenes):
        p = plan[i]
        text = sc.get("subtitle") or sc["narration"]
        cues += make_cues(text, p["start"], p["end"], runs, aspect, voice_offset=intro,
                          family=font_set(sb.get("fonts"))["sub"], speaker=sc.get("speaker"),
                          min_cue=2.5 if sb.get("format") else 0.5)
        for ov in sc.get("overlays", []):
            o = dict(ov)
            o["a"] = intro + p["start"] + ov.get("start", 0.3)
            o["b"] = intro + (p["start"] + ov["end"] if ov.get("end") else p["end"]) - 0.05
            if o["b"] - o["a"] < 0.4:
                o["a"] = max(intro + p["start"], o["b"] - 0.4)
            o["xy"] = resolve_overlay_xy(ov, sc, aspect)
            overlays.append(o)
    if sb.get("format"):   # formats carry subtitle timing rules (myth-busting: 2.5-7 s per cue)
        for c in cues:
            if not 2.5 <= c[2] - c[1] <= 7.0:
                warns.append(f"ซับ {_srt_t(c[1])} อยู่บนจอ {c[2] - c[1]:.1f} วินาที (กฎรูปแบบ: 2.5-7)")
    ass_text = build_ass(aspect, cues, overlays, None, title=sb.get("title", name),
                         fonts=sb.get("fonts"), box=bool(sb.get("subtitle_box")))
    for o in overlays:
        if o.get("_warn"):
            warns.append(o["_warn"])
    ass_path = work / "subs.ass"
    ass_path.write_text(ass_text, encoding="utf-8")
    srt = []
    for k, (t_, a, b, _st) in enumerate(sorted(cues, key=lambda c: c[1]), 1):
        srt.append(f"{k}\n{_srt_t(a)} --> {_srt_t(b)}\n{t_.replace(chr(92) + 'N', chr(10))}\n")
    srt_path = out / f"{name}_{tag}.srt" if multi else out / f"{name}.srt"
    srt_path.write_text("\n".join(srt), encoding="utf-8")

    # music + mix
    mood = args.music
    mus = musicmod.synth_music(total, mood=mood)
    bells = []
    if intro:
        bells.append(logomod.CHIME_AT)
    if outro:
        bells.append(intro + vtotal + logomod.CHIME_AT)
    t_stage = {"start": time.time()}
    stereo, gain = musicmod.mix_audio(vx, vsr, total, intro, mus, bells,
                                      music_level=args.music_level, depth_db=args.duck_db)
    duck = {"music_free_db": round(20 * float(np.log10(np.percentile(gain, 95) * args.music_level)), 1),
            "music_ducked_db": round(20 * float(np.log10(np.percentile(gain, 5) * args.music_level)), 1)}
    mix_wav = work / "mix.wav"
    musicmod.write_wav(mix_wav, stereo)

    # frames
    speech = speech_curve(vx, vsr, fps)
    logo_d = int(min(W, H) * 0.40)
    tasks = []
    for k, seg in enumerate(segs):
        prev = segs[k - 1] if k > 0 else None
        step = 45
        for a in range(seg["f0"], seg["f1"], step):
            tasks.append((seg, prev, a, min(a + step, seg["f1"]), str(frames)))
    jobs = args.jobs or max(1, (os.cpu_count() or 2) - 1)
    t0 = time.time()
    ctx = mp.get_context("spawn")
    with ctx.Pool(jobs, initializer=_init, initargs=(aspect, fps, logo_path, logo_d, speech)) as pool:
        done = 0
        for n in pool.imap_unordered(_render_chunk, tasks):
            done += n
            if done % (fps * 10) < n:
                print(f"[{tag}] frames {done}/{nframes}", file=sys.stderr, flush=True)
    render_s = time.time() - t0
    got = len(list(frames.glob("frame_*.png")))
    if got != nframes:
        raise SystemExit(f"เรนเดอร์เฟรมได้ {got} จาก {nframes}")

    # assemble through ffmpeg-skill
    silent = work / "01_silent.mp4"
    capt = work / "02_captioned.mp4"
    withau = work / "03_audio.mp4"
    final = out / (f"{name}_{tag}.mp4" if multi else f"{name}.mp4")
    for p in (silent, capt, withau, final):
        if p.exists():
            p.unlink()
    T = {"frames": round(render_s, 1)}
    t_seq = time.time()
    steps = []
    steps.append(("sequence", fs_run(fs, "sequence", "--dir", frames, "--pattern", "frame_%06d.png",
                                     "--fps", fps, "-o", silent, "--quality", 12, "--preset", "fast")))
    T["sequence"] = round(time.time() - t_seq, 1)
    t_cap = time.time()
    steps.append(("caption --ass", fs_run(fs, "caption", silent, "--ass", ass_path, "--fonts-dir", FONT_DIR,
                                          "-o", capt)))
    T["caption"] = round(time.time() - t_cap, 1)
    t_au = time.time()
    steps.append(("audio --replace", fs_run(fs, "audio", capt, "--replace", mix_wav, "-o", withau)))
    steps.append(("loudness", fs_run(fs, "loudness", withau, "-I", args.lufs, "--tp", -1.5, "-o", final)))
    T["audio+loudness"] = round(time.time() - t_au, 1)
    platform = {"9:16": "shorts", "4:5": "instagram"}.get(aspect, "youtube")
    chk = fs_run(fs, "check", final, "--platform", platform, fatal=False)
    sheet = out / f"{name}_{tag}_sheet.png"
    look = fs_run(fs, "look", final, "--tiles", "3x2", "-o", sheet)
    if not args.keep_frames:
        shutil.rmtree(frames, ignore_errors=True)
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,pix_fmt,channels,sample_rate:format=duration",
         "-of", "json", str(final)], capture_output=True, text=True).stdout)
    plan_out = {"aspect": aspect, "size": [W, H], "fps": fps, "intro_s": intro, "outro_s": outro,
                "voice_s": round(vtotal, 3),
                "scenes": [{"id": s.get("id", i + 1), "start": round(intro + p["start"], 3),
                            "end": round(intro + p["end"], 3)} for i, (s, p) in enumerate(zip(scenes, plan))]}
    (work / "plan.json").write_text(json.dumps(plan_out, ensure_ascii=False, indent=2))
    return {"final": str(final), "srt": str(srt_path), "sheet": str(sheet), "probe": probe,
            "frames": nframes, "stage_seconds": T, "jobs": jobs,
            "warnings": warns, "ducking": duck, "check": {"ok": chk.get("ok"), "failed": [f"{c['check']} {c['value']} (expected {c['expected']})" for c in (chk.get("checks") or []) if c.get("status") == "FAIL"],
                      "warnings": [f"{c['check']}: {c['value']}" for c in (chk.get("checks") or []) if c.get("status") == "WARN"]},
            "check_platform": platform, "steps": [s for s, _ in steps], "plan": plan_out}


def _srt_t(sec):
    ms = int(round(max(0, sec) * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
