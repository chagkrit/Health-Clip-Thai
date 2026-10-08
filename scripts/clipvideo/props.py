"""Flat 2D props drawn in a unit box (-0.5..0.5). Each prop: fn(ctx, t, p) where t is the
seconds since the layer appeared and p the layer dict (color, value...). Original art only."""
import math

from .draw import (INK, WHITE, CREAM, GREY, RED, PINK, YELLOW, ORANGE, GREEN, TEAL, BLUE, PURPLE,
                   circle, ellipse, fill_stroke, rounded_rect, set_color, star4, mix, clamp,
                   ease_out)


def heart(ctx, t, p):
    c = p.get("color", RED)
    ctx.new_path()
    ctx.move_to(0, 0.40)
    ctx.curve_to(-0.62, 0.02, -0.40, -0.50, 0, -0.18)
    ctx.curve_to(0.40, -0.50, 0.62, 0.02, 0, 0.40)
    ctx.close_path()
    fill_stroke(ctx, c)
    set_color(ctx, WHITE, 0.55)
    ctx.set_line_width(0.035)
    ctx.set_line_cap(1)
    ctx.arc(-0.2, -0.12, 0.13, math.pi * 1.05, math.pi * 1.6)
    ctx.stroke()


def brain(ctx, t, p):
    c = p.get("color", PINK)
    ctx.new_path()
    for (x, y, r) in [(-0.22, -0.08, 0.2), (0.0, -0.18, 0.22), (0.22, -0.08, 0.2),
                      (-0.16, 0.14, 0.2), (0.16, 0.14, 0.2), (0.0, 0.05, 0.2)]:
        circle(ctx, x, y, r)
    set_color(ctx, c)
    ctx.fill_preserve()
    set_color(ctx, INK)
    ctx.set_line_width(0.025)
    ctx.stroke()
    ctx.new_path()
    for (x, y, r) in [(-0.22, -0.08, 0.2), (0.0, -0.18, 0.22), (0.22, -0.08, 0.2),
                      (-0.16, 0.14, 0.2), (0.16, 0.14, 0.2), (0.0, 0.05, 0.2)]:
        circle(ctx, x, y, r)
    set_color(ctx, c)
    ctx.fill()
    set_color(ctx, mix(c, INK, 0.45))
    ctx.set_line_width(0.022)
    ctx.set_line_cap(1)
    ctx.move_to(0, -0.38)
    ctx.curve_to(0.06, -0.15, -0.06, 0.05, 0.0, 0.3)
    ctx.stroke()
    for (x, y, d) in [(-0.2, -0.12, 1), (0.2, -0.1, -1), (-0.15, 0.15, 1), (0.16, 0.16, -1)]:
        ctx.move_to(x, y)
        ctx.curve_to(x + 0.08 * d, y - 0.07, x + 0.1 * d, y + 0.06, x + 0.18 * d, y)
        ctx.stroke()


def moon(ctx, t, p):
    c = p.get("color", YELLOW)
    ctx.new_path()
    ctx.arc(0, 0, 0.38, 0, 2 * math.pi)
    ctx.new_sub_path()
    ctx.arc(0.18, -0.08, 0.32, 0, 2 * math.pi)
    ctx.set_fill_rule(1)  # EVEN_ODD
    set_color(ctx, c)
    ctx.fill_preserve()
    set_color(ctx, INK)
    ctx.set_line_width(0.025)
    ctx.stroke()
    ctx.set_fill_rule(0)
    for i, (x, y, r) in enumerate([(0.3, -0.3, 0.07), (0.38, 0.12, 0.05), (0.12, 0.34, 0.045)]):
        s = 0.75 + 0.25 * math.sin(t * 3 + i * 2)
        star4(ctx, x, y, r * s * 1.6)
        set_color(ctx, YELLOW)
        ctx.fill()


def sun(ctx, t, p):
    c = p.get("color", YELLOW)
    ctx.save()
    ctx.rotate(t * 0.5)
    for i in range(10):
        a = i * 2 * math.pi / 10
        ctx.new_path()
        ctx.move_to(0.34 * math.cos(a), 0.34 * math.sin(a))
        ctx.line_to(0.47 * math.cos(a), 0.47 * math.sin(a))
        set_color(ctx, ORANGE)
        ctx.set_line_width(0.05)
        ctx.set_line_cap(1)
        ctx.stroke()
    ctx.restore()
    circle(ctx, 0, 0, 0.27)
    fill_stroke(ctx, c)


def clock(ctx, t, p):
    h = p.get("hours", 7.0)
    m = h * 60 * (0.6 + 0.4 * ease_out(t / 1.4))  # hands sweep to the target time
    circle(ctx, 0, 0, 0.42)
    fill_stroke(ctx, WHITE, lw=0.035)
    for i in range(12):
        a = i * math.pi / 6
        ctx.move_to(0.34 * math.sin(a), -0.34 * math.cos(a))
        ctx.line_to(0.38 * math.sin(a), -0.38 * math.cos(a))
        set_color(ctx, INK)
        ctx.set_line_width(0.02)
        ctx.stroke()
    ang_h = (m / 720.0) * 2 * math.pi
    ang_m = (m / 60.0) * 2 * math.pi
    for ang, ln, w in ((ang_h, 0.2, 0.04), (ang_m, 0.3, 0.028)):
        ctx.move_to(0, 0)
        ctx.line_to(ln * math.sin(ang), -ln * math.cos(ang))
        set_color(ctx, INK)
        ctx.set_line_width(w)
        ctx.set_line_cap(1)
        ctx.stroke()
    circle(ctx, 0, 0, 0.03)
    set_color(ctx, RED)
    ctx.fill()


def bed(ctx, t, p):
    c = p.get("color", BLUE)
    rounded_rect(ctx, -0.46, 0.02, 0.92, 0.2, 0.04)   # mattress base
    fill_stroke(ctx, "#b98b5e")
    rounded_rect(ctx, -0.46, -0.30, 0.07, 0.52, 0.03)   # headboard
    fill_stroke(ctx, "#8a6540")
    rounded_rect(ctx, -0.38, -0.12, 0.28, 0.13, 0.06)   # pillow
    fill_stroke(ctx, WHITE)
    rounded_rect(ctx, -0.14, -0.1, 0.58, 0.24, 0.06)    # blanket
    fill_stroke(ctx, c)
    set_color(ctx, WHITE, 0.35)
    ctx.set_line_width(0.02)
    ctx.move_to(0.0, -0.06)
    ctx.line_to(0.0, 0.1)
    ctx.stroke()
    rounded_rect(ctx, -0.44, 0.2, 0.06, 0.16, 0.02)
    fill_stroke(ctx, "#8a6540")
    rounded_rect(ctx, 0.38, 0.2, 0.06, 0.16, 0.02)
    fill_stroke(ctx, "#8a6540")


def zzz(ctx, t, p):
    c = p.get("color", PURPLE)
    for i, (x, y, s) in enumerate([(-0.18, 0.2, 0.18), (0.0, 0.0, 0.25), (0.22, -0.26, 0.33)]):
        k = clamp((t * 1.2 - i * 0.35) % 2.2 / 1.0)
        a = 1.0 if k < 0.8 else max(0.0, 1 - (k - 0.8) * 2.5)
        ctx.save()
        ctx.translate(x, y - 0.04 * math.sin(t * 2 + i))
        ctx.new_path()
        ctx.move_to(-s / 2, -s / 2)
        ctx.line_to(s / 2, -s / 2)
        ctx.line_to(-s / 2, s / 2)
        ctx.line_to(s / 2, s / 2)
        set_color(ctx, c, a)
        ctx.set_line_width(0.07)
        ctx.set_line_cap(1)
        ctx.set_line_join(1)
        ctx.stroke()
        ctx.restore()


def apple(ctx, t, p):
    c = p.get("color", RED)
    ctx.new_path()
    ctx.move_to(0, -0.2)
    ctx.curve_to(-0.2, -0.36, -0.46, -0.2, -0.4, 0.08)
    ctx.curve_to(-0.34, 0.36, -0.12, 0.46, 0, 0.38)
    ctx.curve_to(0.12, 0.46, 0.34, 0.36, 0.4, 0.08)
    ctx.curve_to(0.46, -0.2, 0.2, -0.36, 0, -0.2)
    ctx.close_path()
    fill_stroke(ctx, c)
    ctx.move_to(0, -0.2)
    ctx.curve_to(0.02, -0.3, 0.04, -0.36, 0.08, -0.42)
    set_color(ctx, "#6b4a2b")
    ctx.set_line_width(0.04)
    ctx.set_line_cap(1)
    ctx.stroke()
    ctx.new_path()
    ctx.move_to(0.06, -0.34)
    ctx.curve_to(0.16, -0.5, 0.34, -0.46, 0.34, -0.4)
    ctx.curve_to(0.3, -0.3, 0.16, -0.28, 0.06, -0.34)
    fill_stroke(ctx, GREEN, lw=0.02)
    set_color(ctx, WHITE, 0.5)
    ctx.set_line_width(0.03)
    ctx.arc(-0.2, 0.0, 0.14, math.pi * 1.1, math.pi * 1.45)
    ctx.stroke()


def drop(ctx, t, p):
    c = p.get("color", BLUE)
    ctx.new_path()
    ctx.move_to(0, -0.42)
    ctx.curve_to(0.1, -0.2, 0.34, 0.0, 0.34, 0.17)
    ctx.curve_to(0.34, 0.36, 0.18, 0.46, 0, 0.46)
    ctx.curve_to(-0.18, 0.46, -0.34, 0.36, -0.34, 0.17)
    ctx.curve_to(-0.34, 0.0, -0.1, -0.2, 0, -0.42)
    ctx.close_path()
    fill_stroke(ctx, c)
    set_color(ctx, WHITE, 0.6)
    ctx.set_line_width(0.04)
    ctx.set_line_cap(1)
    ctx.arc(0, 0.18, 0.2, math.pi * 0.62, math.pi * 0.9)
    ctx.stroke()


def magnifier(ctx, t, p):
    ctx.save()
    ctx.translate(0.03 * math.sin(t * 1.6), 0.03 * math.cos(t * 1.3))
    ctx.move_to(0.17, 0.17)
    ctx.line_to(0.42, 0.42)
    set_color(ctx, INK)
    ctx.set_line_width(0.1)
    ctx.set_line_cap(1)
    ctx.stroke()
    circle(ctx, -0.08, -0.08, 0.3)
    set_color(ctx, "#d8f1ff", 0.85)
    ctx.fill_preserve()
    set_color(ctx, INK)
    ctx.set_line_width(0.06)
    ctx.stroke()
    set_color(ctx, WHITE, 0.7)
    ctx.set_line_width(0.035)
    ctx.set_line_cap(1)
    ctx.arc(-0.08, -0.08, 0.19, math.pi * 1.1, math.pi * 1.45)
    ctx.stroke()
    ctx.restore()


def doc(ctx, t, p):
    c = p.get("color", WHITE)
    ctx.new_path()
    ctx.move_to(-0.3, -0.42)
    ctx.line_to(0.14, -0.42)
    ctx.line_to(0.3, -0.26)
    ctx.line_to(0.3, 0.42)
    ctx.line_to(-0.3, 0.42)
    ctx.close_path()
    fill_stroke(ctx, c)
    ctx.new_path()
    ctx.move_to(0.14, -0.42)
    ctx.line_to(0.14, -0.26)
    ctx.line_to(0.3, -0.26)
    fill_stroke(ctx, GREY, lw=0.02)
    n = int(p.get("lines", 5))
    for i in range(n):
        w = 0.44 if i % 3 != 2 else 0.3
        rounded_rect(ctx, -0.2, -0.16 + i * 0.1, w, 0.04, 0.02)
        set_color(ctx, p.get("line_color", BLUE) if i == 0 else GREY)
        ctx.fill()


def check(ctx, t, p):
    c = p.get("color", GREEN)
    circle(ctx, 0, 0, 0.4)
    fill_stroke(ctx, c)
    ctx.move_to(-0.19, 0.0)
    ctx.line_to(-0.05, 0.14)
    ctx.line_to(0.21, -0.14)
    set_color(ctx, WHITE)
    ctx.set_line_width(0.1)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.stroke()


def cross(ctx, t, p):
    c = p.get("color", RED)
    circle(ctx, 0, 0, 0.4)
    fill_stroke(ctx, c)
    set_color(ctx, WHITE)
    ctx.set_line_width(0.1)
    ctx.set_line_cap(1)
    ctx.move_to(-0.15, -0.15)
    ctx.line_to(0.15, 0.15)
    ctx.move_to(0.15, -0.15)
    ctx.line_to(-0.15, 0.15)
    ctx.stroke()


def mug(ctx, t, p):
    c = p.get("color", ORANGE)
    rounded_rect(ctx, -0.28, -0.12, 0.46, 0.5, 0.07)
    fill_stroke(ctx, c)
    ctx.new_path()
    ctx.arc(0.2, 0.1, 0.16, -math.pi / 2, math.pi / 2)
    set_color(ctx, INK)
    ctx.set_line_width(0.06)
    ctx.stroke()
    for i in range(3):
        x = -0.15 + i * 0.13
        k = (t * 0.8 + i * 0.33) % 1.0
        ctx.move_to(x, -0.16)
        ctx.curve_to(x - 0.06, -0.26, x + 0.06, -0.3, x, -0.42 - 0.04 * k)
        set_color(ctx, GREY, 1 - k * 0.8)
        ctx.set_line_width(0.035)
        ctx.set_line_cap(1)
        ctx.stroke()


def phone(ctx, t, p):
    c = p.get("color", TEAL)
    rounded_rect(ctx, -0.2, -0.42, 0.4, 0.84, 0.07)
    fill_stroke(ctx, INK)
    rounded_rect(ctx, -0.165, -0.35, 0.33, 0.66, 0.03)
    set_color(ctx, mix(c, WHITE, 0.2 + 0.1 * math.sin(t * 3)))
    ctx.fill()
    circle(ctx, 0, 0.365, 0.02)
    set_color(ctx, GREY)
    ctx.fill()
    for i in range(3):
        rounded_rect(ctx, -0.12, -0.28 + i * 0.12, 0.24 if i != 1 else 0.16, 0.05, 0.02)
        set_color(ctx, WHITE, 0.75)
        ctx.fill()


def dumbbell(ctx, t, p):
    c = p.get("color", PURPLE)
    ctx.save()
    ctx.rotate(-0.25 + 0.06 * math.sin(t * 2))
    rounded_rect(ctx, -0.34, -0.03, 0.68, 0.06, 0.03)
    fill_stroke(ctx, GREY, lw=0.02)
    for sx in (-1, 1):
        rounded_rect(ctx, sx * 0.3 - 0.07, -0.2, 0.14, 0.4, 0.04)
        fill_stroke(ctx, c)
        rounded_rect(ctx, sx * 0.42 - 0.05, -0.13, 0.1, 0.26, 0.03)
        fill_stroke(ctx, mix(c, INK, 0.25))
    ctx.restore()


def plate(ctx, t, p):
    circle(ctx, 0, 0.02, 0.34)
    fill_stroke(ctx, WHITE)
    circle(ctx, 0, 0.02, 0.22)
    set_color(ctx, GREY)
    ctx.set_line_width(0.02)
    ctx.stroke()
    for i, c in enumerate((GREEN, ORANGE, RED)):
        a = i * 2.1 + 0.4
        circle(ctx, 0.09 * math.cos(a), 0.02 + 0.09 * math.sin(a), 0.09)
        fill_stroke(ctx, c, lw=0.015)
    for sx in (-1, 1):  # fork / knife
        x = sx * 0.46
        rounded_rect(ctx, x - 0.02, -0.28, 0.04, 0.68, 0.02)
        fill_stroke(ctx, GREY, lw=0.015)


def shield(ctx, t, p):
    c = p.get("color", TEAL)
    ctx.new_path()
    ctx.move_to(0, -0.44)
    ctx.curve_to(0.18, -0.34, 0.3, -0.34, 0.38, -0.32)
    ctx.curve_to(0.4, 0.1, 0.26, 0.32, 0, 0.46)
    ctx.curve_to(-0.26, 0.32, -0.4, 0.1, -0.38, -0.32)
    ctx.curve_to(-0.3, -0.34, -0.18, -0.34, 0, -0.44)
    ctx.close_path()
    fill_stroke(ctx, c)
    ctx.move_to(-0.16, 0.0)
    ctx.line_to(-0.04, 0.12)
    ctx.line_to(0.17, -0.12)
    set_color(ctx, WHITE)
    ctx.set_line_width(0.08)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.stroke()


def bars(ctx, t, p):
    vals = p.get("values", [0.8, 0.5, 0.3])
    cols = p.get("colors", [TEAL, ORANGE, PURPLE, GREEN, RED])
    n = len(vals)
    gap = 0.07
    w = (0.9 - gap * (n - 1)) / n
    d = p.get("delay_each", 0.18)
    ctx.move_to(-0.46, 0.42)
    ctx.line_to(0.46, 0.42)
    set_color(ctx, INK)
    ctx.set_line_width(0.03)
    ctx.set_line_cap(1)
    ctx.stroke()
    for i, v in enumerate(vals):
        h = 0.8 * clamp(v) * ease_out((t - i * d) / 0.8)
        x = -0.45 + i * (w + gap)
        if h > 0.003:
            rounded_rect(ctx, x, 0.4 - h, w, h, 0.03)
            fill_stroke(ctx, cols[i % len(cols)], lw=0.02)


def ring(ctx, t, p):
    prog = clamp(p.get("progress", 0.7)) * ease_out(t / 1.3)
    c = p.get("color", TEAL)
    circle(ctx, 0, 0, 0.36)
    set_color(ctx, GREY)
    ctx.set_line_width(0.1)
    ctx.stroke()
    if prog > 0.003:
        ctx.arc(0, 0, 0.36, -math.pi / 2, -math.pi / 2 + prog * 2 * math.pi)
        set_color(ctx, c)
        ctx.set_line_width(0.1)
        ctx.set_line_cap(1)
        ctx.stroke()


def timeline(ctx, t, p):
    n = int(p.get("points", 4))
    ctx.move_to(-0.45, 0)
    ctx.line_to(0.45, 0)
    set_color(ctx, INK)
    ctx.set_line_width(0.04)
    ctx.set_line_cap(1)
    ctx.stroke()
    cols = [TEAL, ORANGE, PURPLE, GREEN, RED, BLUE]
    for i in range(n):
        x = -0.4 + i * 0.8 / max(1, n - 1)
        k = ease_out((t - i * 0.35) / 0.5)
        if k <= 0:
            continue
        circle(ctx, x, 0, 0.075 * k + 0.02)
        fill_stroke(ctx, cols[i % len(cols)], lw=0.025)


def sparkle(ctx, t, p):
    for i, (x, y, r) in enumerate([(0, 0, 0.3), (0.28, -0.26, 0.14), (-0.28, 0.26, 0.11)]):
        s = 0.8 + 0.2 * math.sin(t * 4 + i * 2)
        star4(ctx, x, y, r * s * 1.4, 0.3)
        fill_stroke(ctx, YELLOW, lw=0.02)


PROPS = {f.__name__: f for f in (
    heart, brain, moon, sun, clock, bed, zzz, apple, drop, magnifier, doc, check, cross, mug,
    phone, dumbbell, plate, shield, bars, ring, timeline, sparkle)}
