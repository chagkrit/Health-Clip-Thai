"""Scene engine: background + animated layers -> one cairo frame at scene time t."""
import math
import random

import cairo

from .character import MOODS, POSES, draw_character
from .draw import (clamp, ease_back, ease_out, ease_in_out, set_color, circle, INK, WHITE, mix,
                   star4)
from .layout import ASPECTS, LAYOUTS, slots, stage_rect
from .props import PROPS

BACKGROUNDS = {
    "sky": ("#dff3ff", "#f6fbff", ("#bfe5ff", "#fff0b8")),
    "warm": ("#fff1de", "#ffe0bd", ("#ffd1a1", "#ffe9a8")),
    "mint": ("#e2f8ee", "#f4fffa", ("#bdeed7", "#d9f0ff")),
    "lavender": ("#ece8ff", "#f9f7ff", ("#d6cdff", "#ffd9ec")),
    "clinic": ("#eef6f8", "#ffffff", ("#d3ebf1", "#e5f6e9")),
    "night": ("#1b2550", "#35427f", ("#2c3a74", "#4b5aa0")),
}
ANIMS = ("pop", "fade", "slide_left", "slide_right", "slide_up", "none")
IDLES = ("float", "pulse", "wobble", "none")


def validate_scene(scene, idx):
    errs = []
    sid = scene.get("id", idx)
    where = f"scene {sid}"
    if not str(scene.get("narration", "")).strip():
        errs.append(f"{where}: ไม่มี narration")
    if scene.get("bg", "sky") not in BACKGROUNDS:
        errs.append(f"{where}: bg '{scene.get('bg')}' ไม่รู้จัก ({', '.join(BACKGROUNDS)})")
    layout = scene.get("layout", "solo")
    if layout not in LAYOUTS:
        errs.append(f"{where}: layout '{layout}' ไม่รู้จัก ({', '.join(LAYOUTS)})")
        return errs
    slot_names = set(slots(layout, "16:9"))
    for j, ly in enumerate(scene.get("layers", [])):
        lw = f"{where} layer {j}"
        typ = ly.get("type", "prop")
        if typ == "character":
            if ly.get("mood", "happy") not in MOODS:
                errs.append(f"{lw}: mood ต้องเป็น {', '.join(MOODS)}")
            if ly.get("pose", "idle") not in POSES:
                errs.append(f"{lw}: pose ต้องเป็น {', '.join(POSES)}")
        elif typ == "prop":
            if ly.get("kind") not in PROPS:
                errs.append(f"{lw}: kind '{ly.get('kind')}' ไม่รู้จัก ({', '.join(sorted(PROPS))})")
        else:
            errs.append(f"{lw}: type ต้องเป็น character หรือ prop")
        if ly.get("slot", "a") not in slot_names:
            errs.append(f"{lw}: slot '{ly.get('slot')}' ไม่มีใน layout {layout} ({', '.join(sorted(slot_names))})")
        if ly.get("anim", "pop") not in ANIMS:
            errs.append(f"{lw}: anim ต้องเป็น {', '.join(ANIMS)}")
        if ly.get("idle", "float") not in IDLES:
            errs.append(f"{lw}: idle ต้องเป็น {', '.join(IDLES)}")
    for j, ov in enumerate(scene.get("overlays", [])):
        ow = f"{where} overlay {j}"
        if not str(ov.get("text", "")).strip():
            errs.append(f"{ow}: ไม่มี text")
        if "slot" in ov and ov["slot"] not in slot_names:
            errs.append(f"{ow}: slot '{ov['slot']}' ไม่มีใน layout {layout}")
        if "slot" not in ov and "at" not in ov:
            errs.append(f"{ow}: ต้องมี slot หรือ at [fx, fy]")
    return errs


def draw_background(ctx, W, H, name, t, seed):
    top, bot, blobs = BACKGROUNDS[name]
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *_rgb(top))
    g.add_color_stop_rgb(1, *_rgb(bot))
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(seed * 7919 + 13)
    m = min(W, H)
    for i in range(6):
        bx, by = rnd.random(), rnd.random()
        r = (0.16 + 0.18 * rnd.random()) * m
        ph = rnd.random() * 6.28
        x = (bx + 0.02 * math.sin(t * 0.35 + ph)) * W
        y = (by + 0.02 * math.cos(t * 0.3 + ph)) * H
        set_color(ctx, blobs[i % 2], 0.45)
        circle(ctx, x, y, r)
        ctx.fill()
    if name == "night":
        for i in range(34):
            sx, sy = rnd.random() * W, rnd.random() * H * 0.8
            s = 0.6 + 0.4 * math.sin(t * 2.2 + i)
            star4(ctx, sx, sy, m * 0.008 * s + 1.5)
            set_color(ctx, WHITE, 0.7)
            ctx.fill()
    if name == "clinic":
        for i in range(18):
            px, py = rnd.random() * W, rnd.random() * H
            d = m * 0.014
            ctx.rectangle(px - d, py - d * 0.35, 2 * d, d * 0.7)
            ctx.rectangle(px - d * 0.35, py - d, d * 0.7, 2 * d)
            set_color(ctx, "#c9e6ee", 0.7)
            ctx.fill()


def _rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _anim(layer, t):
    """-> (alpha, scale, dx, dy, rot, visible) from the entrance + idle animation."""
    k = t - layer.get("delay", 0.0)
    if k < 0:
        return 0.0, 1.0, 0.0, 0.0, 0.0, False
    dur = layer.get("anim_dur", 0.55)
    x = clamp(k / dur)
    a, s, dx, dy = 1.0, 1.0, 0.0, 0.0
    anim = layer.get("anim", "pop")
    if anim == "pop":
        a, s = clamp(x * 2.5), max(0.01, ease_back(x))
    elif anim == "fade":
        a = ease_out(x)
    elif anim == "slide_left":
        a, dx = clamp(x * 2), -(1 - ease_out(x)) * 0.9
    elif anim == "slide_right":
        a, dx = clamp(x * 2), (1 - ease_out(x)) * 0.9
    elif anim == "slide_up":
        a, dy = clamp(x * 2), (1 - ease_out(x)) * 0.7
    rot = 0.0
    idle = layer.get("idle", "float")
    if x >= 1.0 or anim == "none":
        ph = layer.get("delay", 0) * 3.1
        if idle == "float":
            dy += 0.018 * math.sin(k * 2.0 + ph)
        elif idle == "pulse":
            s *= 1 + 0.075 * max(0.0, math.sin(k * 7.5)) ** 6
        elif idle == "wobble":
            rot = 0.05 * math.sin(k * 2.2 + ph)
    if layer.get("state") == "dim":
        a *= 0.4
    return a, s, dx, dy, rot, True


def render_scene(ctx, W, H, aspect, scene, t, speech=0.0, seed=0):
    draw_background(ctx, W, H, scene.get("bg", "sky"), t, seed)
    sl = slots(scene.get("layout", "solo"), aspect)
    if scene.get("divider"):
        ox, oy, sw, sh = stage_rect(aspect)
        set_color(ctx, INK, 0.18)
        ctx.set_line_width(max(3, min(W, H) * 0.004))
        ctx.set_dash([min(W, H) * 0.014, min(W, H) * 0.016])
        if W / H >= 0.85:
            ctx.move_to(ox + sw / 2, oy + sh * 0.08)
            ctx.line_to(ox + sw / 2, oy + sh * 0.92)
        else:
            ctx.move_to(ox + sw * 0.08, oy + sh / 2)
            ctx.line_to(ox + sw * 0.92, oy + sh / 2)
        ctx.stroke()
        ctx.set_dash([])
    for ly in scene.get("layers", []):
        a, s, dx, dy, rot, vis = _anim(ly, t)
        if not vis or a <= 0.002:
            continue
        cx, cy, u = sl[ly.get("slot", "a")]
        sc = ly.get("scale", 1.0)
        k = t - ly.get("delay", 0.0)
        ctx.save()
        ctx.translate(cx + (ly.get("dx", 0) + dx) * u, cy + (ly.get("dy", 0) + dy) * u)
        ctx.rotate(rot + ly.get("rot", 0.0))
        ctx.scale(u * sc * s, u * sc * s)
        if ly.get("flip"):
            ctx.scale(-1, 1)
        ctx.push_group()
        if ly.get("type", "prop") == "character":
            draw_character(ctx, k, ly, speech)
        else:
            PROPS[ly["kind"]](ctx, k, ly)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        ctx.restore()
