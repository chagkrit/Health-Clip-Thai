"""Subtitles + all on-screen Thai text as ONE ASS file rendered by libass (via ffmpeg-skill's
caption.py --ass). Cue text is the narration as written: it is split on phrase breaks and
re-flowed to the frame width, never reworded."""
import re
import unicodedata
from pathlib import Path

from PIL import ImageFont

from .layout import ASPECTS, SUBTITLE, slots
from .timing import split_span, speakable_len

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
FONT_FAMILY = "Sarabun"
_font_cache = {}


def _font(px, bold=True):
    key = (round(px), bold)
    if key not in _font_cache:
        f = FONT_DIR / ("Sarabun-ExtraBold.ttf" if bold else "Sarabun-Regular.ttf")
        _font_cache[key] = ImageFont.truetype(str(f), max(8, round(px)))
    return _font_cache[key]


def text_width(text, px, bold=True):
    return _font(px, bold).getlength(text)


LEADING = "เแโใไ"


def _breakable(s, i):
    """True if a line may break between s[i-1] and s[i] without splitting a Thai cluster."""
    if i <= 0 or i >= len(s):
        return False
    if unicodedata.category(s[i]) == "Mn" or s[i] in "ะาำๆฯ":
        return False
    if s[i - 1] in LEADING:
        return False
    return True


def clean(text):
    text = re.sub(r"\[[^\]]*\]|<[^>]*>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def phrases(text):
    """Split display text into phrases at spaces and sentence punctuation."""
    parts = re.split(r"(?<=[.!?…])\s+|\s+", clean(text))
    return [p for p in parts if p]


def _tokens(phrase):
    """Thai word tokens (PyThaiNLP newmm) so lines break between words, not inside them.
    Without pythainlp the whole phrase is one token and only spaces are break points."""
    try:
        from pythainlp.tokenize import word_tokenize
        toks = [t for t in word_tokenize(phrase, engine="newmm", keep_whitespace=False) if t]
        if "".join(toks) == phrase.replace(" ", ""):
            return toks
    except Exception:
        pass
    return [phrase]


def flow_lines(text, px, max_w):
    """Greedy-pack words into lines <= max_w (phrase gaps keep their space); hard-break a
    single over-long token only at a safe Thai cluster boundary."""
    items = []   # (token, leading_space)
    for pi, ph in enumerate(phrases(text)):
        for ti, tok in enumerate(_tokens(ph)):
            items.append((tok, pi > 0 and ti == 0))
    lines, cur = [], ""
    for tok, sp in items:
        cand = cur + (" " if sp and cur else "") + tok
        if text_width(cand, px) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append(cur)
            cur = ""
        while text_width(tok, px) > max_w:
            cut = len(tok) - 1
            while cut > 1 and (text_width(tok[:cut], px) > max_w or not _breakable(tok, cut)):
                cut -= 1
            lines.append(tok[:cut])
            tok = tok[cut:]
        cur = tok
    if cur:
        lines.append(cur)
    return lines


def make_cues(text, start, end, runs, aspect, voice_offset=0.0):
    """-> [(text_with_\\N, abs_start, abs_end)] for one scene."""
    W, H = ASPECTS[aspect]
    cfg = SUBTITLE[aspect]
    px = H * cfg["size"]
    lines = flow_lines(text, px, W * cfg["width"])
    if not lines:
        return []
    n = cfg["lines"]
    groups = [lines[i:i + n] for i in range(0, len(lines), n)]
    # avoid a lonely last line when it would make a 1-line cue after a full one
    weights = [sum(speakable_len(l) for l in g) for g in groups]
    spans = split_span(start, end, weights, runs, min_len=0.5)
    return [("\\N".join(g), a + voice_offset, b + voice_offset) for g, (a, b) in zip(groups, spans)]


def _t(sec):
    sec = max(0.0, sec)
    cs = int(round(sec * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def _c(hexrgb, alpha=0):
    """'#rrggbb' -> ASS &HAABBGGRR."""
    h = hexrgb.lstrip("#")
    return "&H%02X%s%s%s" % (alpha, h[4:6], h[2:4], h[0:2])


def build_ass(aspect, cues, overlays, scene_times, title="clip"):
    """cues: [(text,a,b)]; overlays: list of dict(text, slot/at, dy, start, end, style, size)
    already resolved to absolute seconds; scene_times unused (kept for future)."""
    W, H = ASPECTS[aspect]
    cfg = SUBTITLE[aspect]
    m = min(W, H)
    sub_px = round(H * cfg["size"])
    mv = round(H * (1 - cfg["bottom"]))
    ml = round(W * (1 - cfg["width"]) / 2)
    ow = max(3, round(sub_px * 0.09))
    styles = [
        # name, size, primary, outline, bold, outlinepx, shadow, alignment, marginV
        ("Sub", sub_px, "#ffffff", "#23304a", 1, ow, 2, 2, mv),
        ("Title", round(m * 0.115), "#23304a", "#ffffff", 1, round(m * 0.014), 0, 5, 0),
        ("Label", round(m * 0.078), "#23304a", "#ffffff", 1, round(m * 0.010), 0, 5, 0),
        ("Number", round(m * 0.17), "#ef5b5b", "#ffffff", 1, round(m * 0.016), 0, 5, 0),
        ("Note", round(m * 0.052), "#23304a", "#ffffff", 0, round(m * 0.007), 0, 5, 0),
    ]
    out = [
        "[Script Info]", f"Title: {title}", "ScriptType: v4.00+",
        f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    ]
    for name, size, prim, outl, bold, o, sh, al, mvv in styles:
        out.append(f"Style: {name},{FONT_FAMILY},{size},{_c(prim)},{_c(prim)},{_c(outl)},{_c('#000000', 140)},"
                   f"{-1 if bold else 0},0,0,0,100,100,0,0,1,{o},{sh},{al},{ml},{ml},{mvv},1")
    out += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for text, a, b in cues:
        out.append(f"Dialogue: 1,{_t(a)},{_t(b)},Sub,,0,0,0,,{{\\fad(120,100)}}{text}")
    for ov in overlays:
        style = ov.get("style", "label")
        size_scale = {"s": 0.8, "m": 1.0, "l": 1.25}.get(ov.get("size", "m"), 1.0)
        base = next(s[1] for s in styles if s[0].lower() == style.lower())
        px = base * size_scale
        text = ov["text"].replace("\n", "\\N")
        widest = max(text_width(line, px) for line in ov["text"].split("\n"))
        warn = None
        limit = W * 0.92
        if widest > limit:
            px *= limit / widest
            warn = f"overlay '{ov['text'][:20]}' กว้างเกินเฟรม: ย่อฟอนต์ลงเหลือ {px:.0f}px"
        ov["_warn"] = warn
        x, y = ov["xy"]
        pos = f"\\pos({x:.0f},{y:.0f})"
        size_tag = f"\\fs{px:.0f}" if abs(px - base) > 0.5 else ""
        pop = "\\fscx70\\fscy70\\t(0,260,\\fscx100\\fscy100)"
        out.append(f"Dialogue: 2,{_t(ov['a'])},{_t(ov['b'])},{style.capitalize()},,0,0,0,,"
                   f"{{\\an5{pos}{size_tag}\\fad(180,150){pop}}}{text}")
    return "\n".join(out) + "\n"


def resolve_overlay_xy(ov, scene, aspect):
    W, H = ASPECTS[aspect]
    if "at" in ov:
        return ov["at"][0] * W, ov["at"][1] * H
    cx, cy, u = slots(scene.get("layout", "solo"), aspect)[ov["slot"]]
    return cx + ov.get("dx", 0.0) * u, cy + ov.get("dy", 0.55) * u
