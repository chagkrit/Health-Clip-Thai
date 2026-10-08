"""Logo bumper: Pillow crops the supplied picture to a circle, pycairo draws an animated
ring around it, the bell chime (music.bell) lands on the reveal. The user's image is read
from --logo and never copied into the skill."""
import math

import cairo
import numpy as np
from PIL import Image, ImageChops, ImageDraw

from .draw import ease_back, ease_out, clamp, set_color, star4, TEAL, BLUE, YELLOW, WHITE, mix
from .scenes import draw_background

CHIME_AT = 0.55  # seconds into the bumper


def circular_logo(path, diameter):
    """Centre-crop to a square, resize, cut to an anti-aliased circle -> PIL RGBA."""
    im = Image.open(path).convert("RGBA")
    side = min(im.size)
    l, t = (im.width - side) // 2, (im.height - side) // 2
    im = im.crop((l, t, l + side, t + side))
    ss = 4  # supersample the mask for a smooth edge
    mask = Image.new("L", (diameter * ss, diameter * ss), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter * ss - 1, diameter * ss - 1), fill=255)
    mask = mask.resize((diameter, diameter), Image.LANCZOS)
    im = im.resize((diameter, diameter), Image.LANCZOS)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), mask))
    return im


def to_cairo(im):
    """PIL RGBA -> cairo ImageSurface (premultiplied BGRA)."""
    a = np.asarray(im, dtype=np.float32)
    rgb, al = a[..., :3], a[..., 3:4] / 255.0
    pm = np.concatenate([rgb[..., 2::-1] * al, a[..., 3:4]], axis=2).astype(np.uint8)
    pm = np.ascontiguousarray(pm)
    h, w = pm.shape[:2]
    surf = cairo.ImageSurface.create_for_data(bytearray(pm.tobytes()), cairo.FORMAT_ARGB32, w, h, w * 4)
    return surf


def draw_bumper(ctx, W, H, t, dur, logo_surf, logo_d, outro=False):
    m = min(W, H)
    draw_background(ctx, W, H, "sky", t, 99)
    cx, cy = W / 2, H / 2
    R = logo_d / 2 * 1.22   # ring radius
    pop = clamp((t - 0.35) / 0.7)
    s = ease_back(pop) if pop > 0 else 0
    # expanding pulses at the chime
    for i in range(3):
        k = (t - CHIME_AT - i * 0.22) / 1.3
        if 0 < k < 1:
            set_color(ctx, TEAL, 0.5 * (1 - k))
            ctx.set_line_width(m * 0.006)
            ctx.arc(cx, cy, R * (1.02 + 0.7 * ease_out(k)), 0, 2 * math.pi)
            ctx.stroke()
    # main ring draws itself on, in segments that fade from teal to blue
    sweep = ease_out(clamp(t / 1.15)) * 2 * math.pi
    rot = -math.pi / 2 + t * 0.7
    seg = 48
    lw = m * 0.016
    ctx.set_line_cap(1)
    for i in range(seg):
        a0 = i * 2 * math.pi / seg
        if a0 > sweep:
            break
        a1 = min(sweep, a0 + 2 * math.pi / seg + 0.02)
        set_color(ctx, mix(TEAL, BLUE, i / seg))
        ctx.set_line_width(lw)
        ctx.arc(cx, cy, R, rot + a0, rot + a1)
        ctx.stroke()
    # counter-rotating dashed ring
    if t > 0.5:
        ctx.set_dash([m * 0.012, m * 0.02])
        set_color(ctx, BLUE, 0.55 * ease_out(clamp((t - 0.5) / 0.5)))
        ctx.set_line_width(m * 0.005)
        ctx.arc(cx, cy, R * 1.14, -t * 0.5, -t * 0.5 + 2 * math.pi)
        ctx.stroke()
        ctx.set_dash([])
    # logo with a white halo
    if s > 0.01:
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(s, s)
        set_color(ctx, WHITE)
        ctx.arc(0, 0, logo_d / 2 * 1.06, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_surface(logo_surf, -logo_d / 2, -logo_d / 2)
        ctx.paint()
        ctx.restore()
    # sparkles around the ring right after the chime
    k = (t - CHIME_AT) / 1.0
    if 0 < k < 1:
        for i in range(8):
            a = i * math.pi / 4 + 0.3
            r = R * (1.15 + 0.5 * ease_out(k))
            star4(ctx, cx + r * math.cos(a), cy + r * math.sin(a), m * 0.016 * (1 - k) + 1)
            set_color(ctx, YELLOW, 1 - k)
            ctx.fill()
    # closing bumper fades to white over its last second
    if outro and dur > 1.5 and t > dur - 1.0:
        set_color(ctx, WHITE, clamp((t - (dur - 1.0)) / 1.0))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()
