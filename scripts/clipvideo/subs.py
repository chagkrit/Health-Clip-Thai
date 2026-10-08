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
# family -> (bold file, regular file); all Google Fonts, SIL OFL, shipped in assets/fonts
FONT_FILES = {
    "Sarabun": ("Sarabun-ExtraBold.ttf", "Sarabun-Regular.ttf"),
    "Kanit": ("Kanit-Bold.ttf", "Kanit-Regular.ttf"),
    "Mali": ("Mali-Bold.ttf", "Mali-Regular.ttf"),
}
# storyboard "fonts": preset -> family for subtitles / on-screen labels
FONT_SETS = {
    "sarabun": {"sub": "Sarabun", "label": "Sarabun"},
    "kanit-mali": {"sub": "Kanit", "label": "Mali"},
}
SPEAKER_STYLE = {"patient": "SubPatient", "doctor": "Sub"}
SPEAKER_COLOR = {"Sub": "#ffffff", "SubPatient": "#cdb8ff"}
_font_cache = {}


def font_set(name):
    if name is None:
        return FONT_SETS["sarabun"]
    if name not in FONT_SETS:
        raise SystemExit(f"fonts '{name}' ไม่รู้จัก ({', '.join(FONT_SETS)})")
    return FONT_SETS[name]


def _font(px, bold=True, family=FONT_FAMILY):
    key = (round(px), bold, family)
    if key not in _font_cache:
        f = FONT_DIR / FONT_FILES[family][0 if bold else 1]
        _font_cache[key] = ImageFont.truetype(str(f), max(8, round(px)))
    return _font_cache[key]


def text_width(text, px, bold=True, family=FONT_FAMILY):
    return _font(px, bold, family).getlength(text)


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


def flow_lines(text, px, max_w, family=FONT_FAMILY):
    """Greedy-pack words into lines <= max_w (phrase gaps keep their space); hard-break a
    single over-long token only at a safe Thai cluster boundary."""
    items = []   # (token, leading_space)
    for pi, ph in enumerate(phrases(text)):
        for ti, tok in enumerate(_tokens(ph)):
            items.append((tok, pi > 0 and ti == 0))
    lines, cur = [], ""
    for tok, sp in items:
        cand = cur + (" " if sp and cur else "") + tok
        if text_width(cand, px, True, family) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append(cur)
            cur = ""
        while text_width(tok, px, True, family) > max_w:
            cut = len(tok) - 1
            while cut > 1 and (text_width(tok[:cut], px, True, family) > max_w or not _breakable(tok, cut)):
                cut -= 1
            lines.append(tok[:cut])
            tok = tok[cut:]
        cur = tok
    if cur:
        lines.append(cur)
    return lines


def make_cues(text, start, end, runs, aspect, voice_offset=0.0, family=FONT_FAMILY, speaker=None,
              min_cue=0.5):
    """-> [(text_with_\\N, abs_start, abs_end, style)] for one scene. speaker 'patient'/'doctor'
    picks the cue colour (patient lavender, doctor white)."""
    W, H = ASPECTS[aspect]
    cfg = SUBTITLE[aspect]
    px = H * cfg["size"]
    lines = flow_lines(text, px, W * cfg["width"], family)
    if not lines:
        return []
    n = cfg["lines"]
    groups = [lines[i:i + n] for i in range(0, len(lines), n)]
    # avoid a lonely last line when it would make a 1-line cue after a full one
    weights = [sum(speakable_len(l) for l in g) for g in groups]
    if (end - start) < min_cue * len(groups):
        min_cue = 0.5   # scene too short to give every cue the longer minimum
    spans = split_span(start, end, weights, runs, min_len=min_cue)
    style = SPEAKER_STYLE.get(speaker, "Sub")
    return [("\\N".join(g), a + voice_offset, b + voice_offset, style) for g, (a, b) in zip(groups, spans)]


def _t(sec):
    sec = max(0.0, sec)
    cs = int(round(sec * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def _c(hexrgb, alpha=0):
    """'#rrggbb' -> ASS &HAABBGGRR."""
    h = hexrgb.lstrip("#")
    return "&H%02X%s%s%s" % (alpha, h[4:6], h[2:4], h[0:2])


def build_ass(aspect, cues, overlays, scene_times, title="clip", fonts=None, box=False):
    """cues: [(text,a,b)]; overlays: list of dict(text, slot/at, dy, start, end, style, size)
    already resolved to absolute seconds; scene_times unused (kept for future).
    fonts: preset from FONT_SETS; box: subtitles on a translucent dark box (BorderStyle 3)."""
    fam = font_set(fonts)
    W, H = ASPECTS[aspect]
    cfg = SUBTITLE[aspect]
    m = min(W, H)
    sub_px = round(H * cfg["size"])
    mv = round(H * (1 - cfg["bottom"]))
    ml = round(W * (1 - cfg["width"]) / 2)
    ow = max(3, round(sub_px * 0.09))
    styles = [
        # name, size, primary, outline, bold, outlinepx, shadow, alignment, marginV
        ("Sub", sub_px, SPEAKER_COLOR["Sub"], "#23304a", 1, ow, 2, 2, mv),
        ("SubPatient", sub_px, SPEAKER_COLOR["SubPatient"], "#23304a", 1, ow, 2, 2, mv),
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
        family = fam["sub"] if name.startswith("Sub") else fam["label"]
        border = 1
        outl_c, back_c = _c(outl), _c("#000000", 140)
        if box and name.startswith("Sub"):
            border, o, sh = 3, round(size * 0.22), 0   # opaque box = OutlineColour, o = padding
            outl_c = _c("#101828", 0x5A)
        out.append(f"Style: {name},{family},{size},{_c(prim)},{_c(prim)},{outl_c},{back_c},"
                   f"{-1 if bold else 0},0,0,0,100,100,0,0,{border},{o},{sh},{al},{ml},{ml},{mvv},1")
    out += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for cue in cues:
        text, a, b = cue[:3]
        style = cue[3] if len(cue) > 3 else "Sub"
        out.append(f"Dialogue: 1,{_t(a)},{_t(b)},{style},,0,0,0,,{{\\fad(120,100)}}{text}")
    for ov in overlays:
        style = ov.get("style", "label")
        size_scale = {"s": 0.8, "m": 1.0, "l": 1.25}.get(ov.get("size", "m"), 1.0)
        base = next(s[1] for s in styles if s[0].lower() == style.lower())
        px = base * size_scale
        text = ov["text"].replace("\n", "\\N")
        widest = max(text_width(line, px, style.lower() != "note", fam["label"]) for line in ov["text"].split("\n"))
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
