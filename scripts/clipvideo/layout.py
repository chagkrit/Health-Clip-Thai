"""Aspect presets, the art 'stage' and named slots. Everything is a fraction of W/H,
so a storyboard written once renders at any aspect. Subtitles sit in the band below the
stage; for 9:16 the bottom fifth stays free for TikTok/Reels/Shorts UI."""

ASPECTS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

# stage rectangle (x0, y0, x1, y1) as fractions of the frame; art lives inside it
STAGE = {
    "16:9": (0.03, 0.04, 0.97, 0.78),
    "9:16": (0.04, 0.07, 0.96, 0.62),
    "1:1": (0.04, 0.04, 0.96, 0.74),
    "4:5": (0.04, 0.05, 0.96, 0.72),
}
# subtitle: bottom edge of the text block (fraction of H), font size (fraction of H),
# max line width (fraction of W), max lines
SUBTITLE = {
    "16:9": dict(bottom=0.945, size=0.060, width=0.86, lines=2),
    "9:16": dict(bottom=0.775, size=0.036, width=0.86, lines=3),
    "1:1": dict(bottom=0.955, size=0.050, width=0.88, lines=2),
    "4:5": dict(bottom=0.955, size=0.047, width=0.88, lines=2),
}


def aspect_key(aspect):
    if aspect not in ASPECTS:
        raise SystemExit(f"aspect ต้องเป็นหนึ่งใน {', '.join(ASPECTS)} (ได้ '{aspect}')")
    return aspect


def stage_rect(aspect):
    W, H = ASPECTS[aspect]
    x0, y0, x1, y1 = STAGE[aspect]
    return W * x0, H * y0, W * (x1 - x0), H * (y1 - y0)


def _orient(aspect):
    W, H = ASPECTS[aspect]
    r = W / H
    return "landscape" if r > 1.2 else "portrait" if r < 0.85 else "square"


def slots(layout, aspect):
    """-> {slot_name: (cx, cy, u)} in pixels. u = side of the unit box the item is drawn in."""
    ox, oy, sw, sh = stage_rect(aspect)
    o = _orient(aspect)

    def at(fx, fy, u):
        return (ox + fx * sw, oy + fy * sh, u)

    m = min(sw, sh)
    if layout == "solo":
        return {"a": at(0.5, 0.5, m * 0.92)}
    if layout in ("duo", "split"):
        if o == "portrait":
            u = min(sw * 0.9, sh * 0.40)   # room for a label under the top item
            return {"a": at(0.5, 0.24, u), "b": at(0.5, 0.76, u)}
        u = min(sw * 0.46, sh * 0.95)
        if layout == "duo":
            return {"a": at(0.27, 0.52, u * 1.05), "b": at(0.72, 0.5, u * 0.92)}
        return {"a": at(0.25, 0.5, u), "b": at(0.75, 0.5, u)}
    if layout == "trio":
        if o == "portrait":
            u = min(sw * 0.62, sh * 0.27)
            return {"a": at(0.5, 0.17, u), "b": at(0.5, 0.5, u), "c": at(0.5, 0.83, u)}
        u = min(sw / 3 * 0.92, sh * 0.8)
        return {"a": at(1 / 6, 0.5, u), "b": at(0.5, 0.5, u), "c": at(5 / 6, 0.5, u)}
    if layout == "quad":
        u = min(sw / 2, sh / 2) * 0.86
        return {"a": at(0.25, 0.25, u), "b": at(0.75, 0.25, u),
                "c": at(0.25, 0.75, u), "d": at(0.75, 0.75, u)}
    raise SystemExit(f"layout '{layout}' ไม่รู้จัก (solo, duo, split, trio, quad)")


LAYOUTS = ("solo", "duo", "split", "trio", "quad")
