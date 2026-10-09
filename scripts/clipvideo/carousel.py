"""2-slide carousel (slide 1 = the myth in big type, slide 2 = the medical fact in 3-4 lines)
exported as clean PNGs. Same rules as the video: pycairo draws backgrounds and icons only, every
Thai string goes through ASS + libass (burned by ffmpeg-skill `caption --ass`), then ffmpeg-skill
`look --at` pulls the two stills out. Nothing here touches the network or the user's logo."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import cairo
from PIL import Image

from .build import find_ffmpeg_skill, fs_run
from .draw import INK, WHITE, RED, GREEN, TEAL, rounded_rect, set_color
from .layout import ASPECTS
from .props import PROPS
from .scenes import draw_background
from .subs import FONT_DIR, _c, _t, flow_lines, font_set, text_width

DEFAULT_ASPECT = "4:5"
FPS = 10   # frames per second of the throwaway 2-second stills video
BAD_GLYPHS = "✓✗•"
DISCLAIMER = "ข้อมูลทั่วไป ไม่ใช่การวินิจฉัยหรือรักษา ปรึกษาแพทย์ผู้ดูแลก่อนเปลี่ยนแปลงการรักษา"
SWIPE = "ปัดดูข้อเท็จจริงทางการแพทย์"
FACT_TITLE = "ข้อเท็จจริงทางการแพทย์"
MYTH_BADGE = "ความเชื่อผิด?"
OBS_NOTE = "งานวิจัยเชิงสังเกตบอกความสัมพันธ์ ไม่ได้พิสูจน์สาเหตุ"


def load_spec(path):
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    errs = []
    s1, s2 = spec.get("slide1"), spec.get("slide2")
    if not isinstance(s1, dict) or not str(s1.get("headline", "")).strip():
        errs.append("slide1.headline (ความเชื่อผิดตัวใหญ่) ว่าง")
    if not isinstance(s2, dict):
        errs.append("ไม่มี slide2")
    else:
        pts = s2.get("points")
        if not isinstance(pts, list) or not 2 <= len(pts) <= 5 or not all(str(p).strip() for p in pts):
            errs.append("slide2.points ต้องมี 2-5 ข้อ (แนะนำ 3-4) และไม่ว่าง")
    for k in ("slide1", "slide2"):
        ic = (spec.get(k) or {}).get("icon")
        if ic and ic not in PROPS:
            errs.append(f"{k}.icon '{ic}' ไม่มีใน props ({', '.join(sorted(PROPS))})")
        for v in json.dumps(spec.get(k, {}), ensure_ascii=False):
            if v in BAD_GLYPHS:
                errs.append(f"{k}: อักขระ '{v}' ฟอนต์แสดงผลเพี้ยน ให้ใช้ไอคอนแทน")
                break
    if errs:
        raise SystemExit("carousel spec ไม่ผ่าน:\n  - " + "\n  - ".join(errs))
    return spec


def _fit(text, px0, max_w, max_lines, family, floor=0.55):
    """Largest size <= px0 whose Thai-safe flow fits max_lines; -> (px, lines)."""
    px = px0
    while True:
        lines = flow_lines(text, px, max_w, family)
        if len(lines) <= max_lines or px <= px0 * floor:
            return px, lines
        px *= 0.94


def _ev(style, x, y, an, lines, px=None):
    """One text event (times are filled in per slide by _dialogue)."""
    return (style, x, y, an, lines, px)


def _dialogue(ev, a, b):
    style, x, y, an, lines, px = ev
    tag = "{\\an%d\\pos(%d,%d)%s}" % (an, x, y, f"\\fs{px:.0f}" if px else "")
    return f"Dialogue: 2,{_t(a)},{_t(b)},{style},,0,0,0,,{tag}" + "\\N".join(lines)


def _pill(ctx, cx, cy, w, h, color):
    set_color(ctx, color)
    rounded_rect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
    ctx.fill()


def _icon(ctx, kind, cx, cy, size):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(size, size)
    PROPS[kind](ctx, 0.0, {})
    ctx.restore()


def _slide1(ctx, W, H, spec, fam):
    s = spec["slide1"]
    draw_background(ctx, W, H, "warm", 0.0, 3)
    m = min(W, H)
    badge = s.get("badge", MYTH_BADGE)
    bpx = W * 0.058
    bw = text_width(badge, bpx, True, fam["label"]) + W * 0.10
    _pill(ctx, W / 2, H * 0.115, bw, bpx * 1.9, RED)
    _icon(ctx, s.get("icon", "cross"), W / 2, H * 0.355, m * 0.30)
    px, lines = _fit(s["headline"].replace("\n", " "), W * 0.105, W * 0.88, 4, fam["sub"])
    ev = [_ev("Badge", W / 2, H * 0.115, 5, [badge]),
          _ev("Head", W / 2, H * 0.70, 5, lines, px)]
    foot = s.get("footer", SWIPE)
    ev.append(_ev("Foot", W / 2, H * 0.945, 5, [foot]))
    return ev


def _slide2(ctx, W, H, spec, fam):
    s = spec["slide2"]
    draw_background(ctx, W, H, "mint", 0.0, 5)
    m = min(W, H)
    title = s.get("title", FACT_TITLE)
    tpx = W * 0.056
    tw = text_width(title, tpx, True, fam["label"]) + W * 0.10
    _pill(ctx, W / 2, H * 0.085, tw, tpx * 1.9, GREEN)
    pts = [str(p).replace("\n", " ") for p in s["points"]]
    note = s.get("note", OBS_NOTE) if s.get("note", True) else ""
    top, bottom = H * 0.155, H * (0.835 if note else 0.88)
    gap = H * 0.018
    ch = (bottom - top - gap * (len(pts) - 1)) / len(pts)
    left, cw = W * 0.06, W * 0.88
    icon_d = min(ch * 0.62, W * 0.12)
    tx = left + icon_d + W * 0.055
    tmax = left + cw - W * 0.03 - tx
    px0 = min(W * 0.058, ch * 0.32)
    # one shared size so every card matches: shrink until the longest point fits the card
    px = px0
    while True:
        fits = [len(flow_lines(p, px, tmax, fam["sub"])) * px * 1.28 <= ch * 0.86 for p in pts]
        if all(fits) or px <= px0 * 0.5:
            break
        px *= 0.94
    ev = [_ev("Badge", W / 2, H * 0.085, 5, [title])]
    for i, p in enumerate(pts):
        y0 = top + i * (ch + gap)
        set_color(ctx, WHITE, 0.94)
        rounded_rect(ctx, left, y0, cw, ch, min(ch * 0.22, W * 0.04))
        ctx.fill()
        set_color(ctx, TEAL, 0.35)
        ctx.set_line_width(max(2, m * 0.003))
        rounded_rect(ctx, left, y0, cw, ch, min(ch * 0.22, W * 0.04))
        ctx.stroke()
        _icon(ctx, s.get("icon", "check"), left + W * 0.03 + icon_d / 2, y0 + ch / 2, icon_d)
        ev.append(_ev("Point", tx, y0 + ch / 2, 4, flow_lines(p, px, tmax, fam["sub"]), px))
    if note:
        npx, nl = _fit(note, W * 0.034, W * 0.93, 2, fam["label"])
        ev.append(_ev("Note", W / 2, H * 0.885, 5, nl, npx))
    ev.append(_ev("Foot", W / 2, H * 0.955, 5, [s.get("footer", DISCLAIMER)]))
    return ev


def _ass(W, H, fam, events):
    def st(name, family, size, prim, bold, outline="#ffffff", ow=0):
        return (f"Style: {name},{family},{size:.0f},{_c(prim)},{_c(prim)},{_c(outline)},{_c('#000000', 255)},"
                f"{-1 if bold else 0},0,0,0,100,100,0,0,1,{ow:.0f},0,5,0,0,0,1")
    out = ["[Script Info]", "Title: carousel", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
           "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
           "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
           "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st("Badge", fam["label"], W * 0.056, WHITE, True),
           st("Head", fam["sub"], W * 0.105, INK, True, "#ffffff", max(2, W * 0.006)),
           st("Point", fam["sub"], W * 0.05, INK, True),
           st("Note", fam["label"], W * 0.034, INK, False),
           st("Foot", fam["label"], W * 0.03, "#5b6b8c", False),
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    return "\n".join(out + events) + "\n"


def make_carousel(spec_path, out_dir, name="carousel", aspect=DEFAULT_ASPECT, work=None):
    if aspect not in ASPECTS:
        raise SystemExit(f"aspect '{aspect}' ไม่รู้จัก ({', '.join(ASPECTS)})")
    spec = load_spec(spec_path)
    W, H = ASPECTS[aspect]
    fam = font_set(spec.get("fonts"))
    fs = find_ffmpeg_skill()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(work) if work else Path(tempfile.mkdtemp(prefix="hcth_carousel_"))
    frames = tmp / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    events = []
    for idx, fn in enumerate((_slide1, _slide2), start=1):
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        ev = fn(cairo.Context(surf), W, H, spec, fam)
        surf.flush()
        first = frames / f"frame_{(idx - 1) * FPS + 1:06d}.png"
        Image.frombuffer("RGB", (W, H), surf.get_data(), "raw", "BGRX", surf.get_stride(), 1).save(str(first))
        for k in range(1, FPS):   # hold each slide 1 s so look.py can seek into the middle of it
            shutil.copyfile(first, frames / f"frame_{(idx - 1) * FPS + 1 + k:06d}.png")
        events += [_dialogue(e, idx - 1, idx) for e in ev]   # slide 1 = 0-1 s, slide 2 = 1-2 s
    ass = _ass(W, H, fam, events)
    ass_path = tmp / "carousel.ass"
    ass_path.write_text(ass, encoding="utf-8")
    silent, capt = tmp / "01.mp4", tmp / "02.mp4"
    fs_run(fs, "sequence", "--dir", frames, "--pattern", "frame_%06d.png", "--start-number", 1, "--fps", FPS, "-o", silent,
           "--quality", 1, "--preset", "slow", "--overwrite")
    fs_run(fs, "caption", silent, "--ass", ass_path, "--fonts-dir", FONT_DIR, "-o", capt, "--overwrite")
    paths = []
    for idx, at in ((1, 0.5), (2, 1.5)):
        base = tmp / f"slide{idx}"
        fs_run(fs, "look", capt, "--at", at, "-o", base, "--no-timecode", "--overwrite")
        got = sorted(tmp.glob(f"slide{idx}*.png"))
        if not got:
            raise SystemExit(f"look.py ไม่สร้างภาพสไลด์ {idx}")
        dest = out / f"{name}_slide{idx}_{aspect.replace(':', 'x')}.png"
        shutil.copyfile(got[0], dest)
        paths.append(str(dest))
    if not work:
        shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"slides": paths, "aspect": aspect, "size": [W, H]}, ensure_ascii=False, indent=2),
          file=sys.stdout)
    return paths
