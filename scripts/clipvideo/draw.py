"""Small pycairo helpers shared by props, character and scenes.

All shapes are drawn in a unit box (about -0.5..0.5) that the scene engine scales to
pixels, so no coordinate in this package depends on the output size.
NO TEXT is ever drawn with cairo: Thai needs shaping that cairo's toy text API lacks,
so every string goes through ASS + libass (see subs.py).
"""
import math

INK = "#23304a"
WHITE = "#ffffff"
CREAM = "#fff6e5"
GREY = "#cfd6e4"
RED = "#ef5b5b"
PINK = "#ff8fa3"
YELLOW = "#ffc83d"
ORANGE = "#ff9f43"
GREEN = "#3fbf7f"
TEAL = "#2ab7ca"
BLUE = "#4a90e2"
PURPLE = "#8e7cf0"
SKIN = "#f6c9a0"
HAIR = "#3b2a20"

NAMED = {"ink": INK, "white": WHITE, "cream": CREAM, "grey": GREY, "red": RED, "pink": PINK,
         "yellow": YELLOW, "orange": ORANGE, "green": GREEN, "teal": TEAL, "blue": BLUE,
         "purple": PURPLE}


def rgb(c):
    """'#rrggbb' or a palette name -> (r, g, b) floats."""
    c = NAMED.get(c, c)
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def set_color(ctx, c, alpha=1.0):
    r, g, b = rgb(c)
    ctx.set_source_rgba(r, g, b, alpha)


def mix(c1, c2, t):
    a, b = rgb(c1), rgb(c2)
    return "#%02x%02x%02x" % tuple(int(round((a[i] + (b[i] - a[i]) * t) * 255)) for i in range(3))


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x ** 3


def ease_back(x):
    """Overshoot 'pop' easing, 0 -> 1 with a small bounce past 1."""
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def fill_stroke(ctx, fill=None, stroke=INK, lw=0.025, alpha=1.0):
    if fill is not None:
        set_color(ctx, fill, alpha)
        ctx.fill_preserve() if stroke else ctx.fill()
    if stroke:
        set_color(ctx, stroke, alpha)
        ctx.set_line_width(lw)
        ctx.set_line_cap(1)   # ROUND
        ctx.set_line_join(1)  # ROUND
        ctx.stroke()


def rounded_rect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def circle(ctx, x, y, r):
    ctx.new_sub_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)


def ellipse(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def star4(ctx, x, y, r, inner=0.35):
    ctx.new_sub_path()
    for i in range(8):
        a = i * math.pi / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * inner
        px, py = x + rr * math.cos(a), y + rr * math.sin(a)
        ctx.move_to(px, py) if i == 0 else ctx.line_to(px, py)
    ctx.close_path()


def soft_shadow(ctx, cx, cy, rx, ry, alpha=0.16):
    """Flat ground shadow under an object."""
    set_color(ctx, INK, alpha)
    ellipse(ctx, cx, cy, rx, ry)
    ctx.fill()
