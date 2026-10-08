"""Render README artwork that mirrors pet.py's actual motion model.

    python make_preview.py

Writes docs/preview.gif (breathing + one blink, seamless loop) and
docs/poses.png (front view plus the three turn angles).

The bob/sway frequencies here are integer cycles per loop length on purpose,
so the GIF closes on itself without a jump. pet.py uses slightly different
frequencies because it does not need to loop.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.join(HERE, "sprites")
DOCS = os.path.join(HERE, "docs")

LOOP_S = 2.8
FPS = 18
FRAMES = int(LOOP_S * FPS)
HEIGHT = 260

BOB_CYCLES = 3
SWAY_CYCLES = 1
BLINK_AT = 11
BLINK_LEN = 3


def sprite(name):
    return Image.open(os.path.join(SP, name)).convert("RGBA")


def compose(art, canvas, sx, sy, deg, dy):
    w, h = canvas
    dw, dh = art.width * sx, art.height * sy
    dw, dh = max(1, int(dw)), max(1, int(dh))
    scaled = art.resize((dw, dh), Image.LANCZOS)
    if deg:
        scaled = scaled.rotate(deg, resample=Image.BICUBIC, expand=True)
    layer = Image.new("RGBA", canvas, (0, 0, 0, 0))
    x = (w - scaled.width) // 2
    y = h - scaled.height - int(h * 0.04) + int(dy)
    layer.alpha_composite(scaled, (x, y))
    return layer


def preview():
    front, blink = sprite("idle.png"), sprite("blink.png")
    for art in (front, blink):
        art.thumbnail((999, HEIGHT), Image.LANCZOS)
    canvas = (int(front.width * 1.35), HEIGHT + 14)
    frames = []
    for i in range(FRAMES):
        t = i / FRAMES * LOOP_S
        phase = i / FRAMES
        sy = 1.0 + math.sin(2 * math.pi * BOB_CYCLES * phase) * 0.016
        sx = 1.0 - math.sin(2 * math.pi * BOB_CYCLES * phase) * 0.011
        deg = math.sin(2 * math.pi * SWAY_CYCLES * phase) * 2.0
        dy = -abs(math.sin(2 * math.pi * BOB_CYCLES * phase)) * 1.5
        art = blink if BLINK_AT <= i < BLINK_AT + BLINK_LEN else front
        frames.append(compose(art, canvas, sx, sy, deg, dy))

    out = os.path.join(DOCS, "preview.gif")
    _save_gif(frames, out)
    return out


def _save_gif(frames, path, bg=(245, 241, 232)):
    """GIF transparency is 1-bit, which would fray the soft fur edge. Flattening
    onto a solid panel instead, and sharing one palette across frames so the
    loop does not shimmer."""
    flat = []
    for f in frames:
        panel = Image.new("RGB", f.size, bg)
        panel.paste(f, (0, 0), f)
        flat.append(panel)
    pal = flat[0].quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)
    prepared = [im.quantize(palette=pal, dither=Image.NONE) for im in flat]
    prepared[0].save(path, save_all=True, append_images=prepared[1:],
                     duration=int(1000 / FPS), loop=0, optimize=False)


def poses():
    names = ["idle.png", "turn_a.png", "turn_b.png", "turn_c.png"]
    labels = ["正面仰天大笑", "侧身", "侧身（镜像）", "躺地狂笑"]
    h = 300
    arts = []
    for n in names:
        s = sprite(n)
        arts.append(s.resize((max(1, int(s.width * h / s.height)), h), Image.LANCZOS))
    pad, gap = 40, 26
    w = sum(a.width for a in arts) + gap * (len(arts) - 1) + pad * 2
    canvas = Image.new("RGBA", (w, h + pad * 2 + 34), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    x = pad
    for a, lab in zip(arts, labels):
        canvas.alpha_composite(a, (x, pad))
        tw = draw.textlength(lab, font=font)
        draw.text((x + (a.width - tw) / 2, h + pad + 8), lab, font=font, fill=(110, 101, 89, 255))
        x += a.width + gap
    out = os.path.join(DOCS, "poses.png")
    canvas.save(out)
    return out


def main():
    os.makedirs(DOCS, exist_ok=True)
    for p in (preview(), poses()):
        print("%s  %.0f KB" % (p, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
