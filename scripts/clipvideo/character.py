"""'Nong Fah' - the clip's original host character (round head, teal scrubs, white coat,
stethoscope). Drawn in the unit box; mood/pose come from the storyboard layer. The mouth
opens with the real voiceover loudness (`speech`, 0..1), so lip-flap follows the audio."""
import math

from .draw import (INK, WHITE, SKIN, HAIR, TEAL, PINK, circle, ellipse, fill_stroke,
                   rounded_rect, set_color, mix, clamp)

MOODS = ("happy", "think", "worry", "wow")
POSES = ("idle", "wave", "point", "think", "cheer")


def _arm(ctx, sx, shoulder, hand, color):
    ctx.move_to(*shoulder)
    ctx.line_to(*hand)
    set_color(ctx, INK)
    ctx.set_line_width(0.115)
    ctx.set_line_cap(1)
    ctx.stroke()
    ctx.move_to(*shoulder)
    ctx.line_to(*hand)
    set_color(ctx, color)
    ctx.set_line_width(0.085)
    ctx.stroke()
    circle(ctx, hand[0], hand[1], 0.052)
    fill_stroke(ctx, SKIN, lw=0.02)


def draw_character(ctx, t, p, speech=0.0):
    mood = p.get("mood", "happy")
    pose = p.get("pose", "idle")
    coat = p.get("coat", WHITE)
    scrubs = p.get("scrubs", TEAL)
    bob = 0.012 * math.sin(t * 2.4)
    ctx.save()
    ctx.translate(0, bob)

    # legs + shoes
    for sx in (-1, 1):
        rounded_rect(ctx, sx * 0.1 - 0.05, 0.36, 0.1, 0.12, 0.03)
        fill_stroke(ctx, "#4b5a78", lw=0.02)
        ellipse(ctx, sx * 0.1 + sx * 0.015, 0.485, 0.075, 0.032)
        fill_stroke(ctx, INK, lw=0.015)

    # arms behind body for down poses
    sh_l, sh_r = (-0.2, 0.06), (0.2, 0.06)
    tt = t * 5.0
    hand_l, hand_r = (-0.27, 0.28), (0.27, 0.28)
    if pose == "wave":
        hand_r = (0.34 + 0.05 * math.sin(tt), -0.12 + 0.03 * math.cos(tt))
    elif pose == "point":
        hand_r = (0.42, 0.04 + 0.01 * math.sin(tt * 0.5))
    elif pose == "think":
        hand_r = (0.07, -0.02)
    elif pose == "cheer":
        hand_l = (-0.34 - 0.02 * math.sin(tt), -0.2)
        hand_r = (0.34 + 0.02 * math.sin(tt), -0.2)
    _arm(ctx, -1, sh_l, hand_l, coat)

    # torso: coat with scrubs V
    ctx.new_path()
    ctx.move_to(-0.22, 0.02)
    ctx.curve_to(-0.26, 0.2, -0.24, 0.34, -0.2, 0.42)
    ctx.line_to(0.2, 0.42)
    ctx.curve_to(0.24, 0.34, 0.26, 0.2, 0.22, 0.02)
    ctx.curve_to(0.12, -0.04, -0.12, -0.04, -0.22, 0.02)
    ctx.close_path()
    fill_stroke(ctx, coat)
    ctx.new_path()
    ctx.move_to(-0.1, -0.02)
    ctx.line_to(0, 0.2)
    ctx.line_to(0.1, -0.02)
    ctx.close_path()
    fill_stroke(ctx, scrubs, lw=0.02)
    ctx.move_to(0, 0.2)
    ctx.line_to(0, 0.42)
    set_color(ctx, mix(coat, INK, 0.25))
    ctx.set_line_width(0.015)
    ctx.stroke()
    # stethoscope
    ctx.new_path()
    ctx.arc(0, -0.02, 0.13, math.pi * 0.05, math.pi * 0.95)
    set_color(ctx, "#5b6b8a")
    ctx.set_line_width(0.028)
    ctx.stroke()
    circle(ctx, 0.11, 0.2, 0.032)
    fill_stroke(ctx, "#9fb0cc", lw=0.015)

    _arm(ctx, 1, sh_r, hand_r, coat)

    # head
    hy = -0.2
    ctx.save()
    if pose == "think" or mood == "think":
        ctx.translate(0.0, 0.0)
        ctx.rotate(0.05)
    for sx in (-1, 1):
        circle(ctx, sx * 0.205, hy + 0.02, 0.04)
        fill_stroke(ctx, SKIN, lw=0.018)
    circle(ctx, 0, hy, 0.215)
    fill_stroke(ctx, SKIN)
    # hair cap + fringe
    ctx.new_path()
    ctx.arc(0, hy, 0.225, math.pi * 1.0, math.pi * 2.0)
    ctx.curve_to(0.16, hy - 0.12, 0.02, hy - 0.04, -0.06, hy - 0.1)
    ctx.curve_to(-0.12, hy - 0.04, -0.2, hy - 0.04, -0.225, hy)
    ctx.close_path()
    fill_stroke(ctx, HAIR, lw=0.02)
    # eyes
    blink = 0.12 if (t % 3.4) < 0.12 else 1.0
    for sx in (-1, 1):
        ex = sx * 0.075
        ey = hy + 0.02
        if mood == "wow":
            circle(ctx, ex, ey, 0.04)
            fill_stroke(ctx, WHITE, lw=0.015)
            circle(ctx, ex, ey, 0.018)
            set_color(ctx, INK)
            ctx.fill()
        else:
            ellipse(ctx, ex, ey, 0.026, 0.036 * blink)
            set_color(ctx, INK)
            ctx.fill()
            if blink > 0.5:
                circle(ctx, ex + 0.008, ey - 0.012, 0.008)
                set_color(ctx, WHITE)
                ctx.fill()
        # brows
        by = hy - 0.05
        set_color(ctx, INK)
        ctx.set_line_width(0.017)
        ctx.set_line_cap(1)
        if mood == "worry":
            ctx.move_to(ex - sx * 0.035, by - 0.01 + 0.0)
            ctx.line_to(ex + sx * 0.03, by + 0.015)
            ctx.line_to(ex + sx * 0.03, by + 0.015)
        elif mood == "think":
            ctx.move_to(ex - 0.03, by + (0.01 if sx < 0 else -0.01))
            ctx.line_to(ex + 0.03, by + (0.0 if sx < 0 else -0.02))
        elif mood == "wow":
            ctx.move_to(ex - 0.03, by - 0.025)
            ctx.curve_to(ex - 0.01, by - 0.04, ex + 0.01, by - 0.04, ex + 0.03, by - 0.025)
        else:
            ctx.move_to(ex - 0.03, by)
            ctx.curve_to(ex - 0.01, by - 0.02, ex + 0.01, by - 0.02, ex + 0.03, by)
        ctx.stroke()
    # cheeks
    for sx in (-1, 1):
        ellipse(ctx, sx * 0.13, hy + 0.08, 0.034, 0.02)
        set_color(ctx, PINK, 0.55)
        ctx.fill()
    # mouth: audio-driven opening
    my = hy + 0.115
    open_ = clamp(speech * 1.6)
    if open_ > 0.08:
        ellipse(ctx, 0, my, 0.036 + 0.014 * open_, 0.012 + 0.04 * open_)
        set_color(ctx, "#7a2e3a")
        ctx.fill_preserve()
        set_color(ctx, INK)
        ctx.set_line_width(0.014)
        ctx.stroke()
    elif mood == "worry":
        ctx.arc(0, my + 0.03, 0.035, math.pi * 1.15, math.pi * 1.85)
        set_color(ctx, INK)
        ctx.set_line_width(0.016)
        ctx.set_line_cap(1)
        ctx.stroke()
    elif mood == "wow":
        ellipse(ctx, 0, my + 0.01, 0.022, 0.03)
        set_color(ctx, "#7a2e3a")
        ctx.fill()
    else:
        ctx.arc(0, my - 0.02, 0.05, math.pi * 0.15, math.pi * 0.85)
        set_color(ctx, INK)
        ctx.set_line_width(0.016)
        ctx.set_line_cap(1)
        ctx.stroke()
    ctx.restore()
    ctx.restore()
