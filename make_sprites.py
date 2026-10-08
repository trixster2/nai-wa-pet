"""Cut 奶蛙 out of the renders and emit transparent sprites.

    python make_sprites.py
"""
from collections import deque
import os
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "sprites")

# The renders sit on a pure white plate while the belly is cream-tinted,
# so hue neutrality separates them better than brightness does.
def tight(p):
    return min(p) >= 249 and (max(p) - min(p)) <= 7

def loose(p):
    return min(p) >= 185 and (max(p) - min(p)) <= 18

def shadow(p):
    # The plate's contact shadow is a warm light grey; feet are far more
    # saturated, so a wider net here is safe as long as it stays edge-seeded.
    return min(p) >= 150 and (max(p) - min(p)) <= 30

def pale(p):
    # Slabs of plate left between the legs: the border flood cannot reach them
    # once edge anti-aliasing breaks the chain, but nothing on the body is
    # this neutral (the cream belly sits ~40 channels wide).
    return min(p) >= 235 and (max(p) - min(p)) <= 18

def _flood(px, seen, w, h, rule, seeds):
    dq = deque(seeds)
    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                i = ny * w + nx
                if not seen[i] and rule(px[nx, ny]):
                    seen[i] = 1
                    dq.append((nx, ny))


def _largest_component(seen, w, h):
    """Background specks cut off from the border by the card's rounded edge."""
    keep = bytearray(w * h)
    best = []
    for start in range(w * h):
        if seen[start] or keep[start]:
            continue
        keep[start] = 1
        comp = [start]
        head = 0
        while head < len(comp):
            i = comp[head]
            head += 1
            x, y = i % w, i // w
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    k = ny * w + nx
                    if not seen[k] and not keep[k]:
                        keep[k] = 1
                        comp.append(k)
        if len(comp) > len(best):
            best = comp
    keep = bytearray(w * h)
    for i in best:
        keep[i] = 1
    return keep


def _pale_slabs(px, w, h, seen, min_size=400):
    out = []
    done = bytearray(w * h)
    for start in range(w * h):
        if seen[start] or done[start]:
            continue
        x0, y0 = start % w, start // w
        if not pale(px[x0, y0]):
            continue
        done[start] = 1
        comp = [start]
        head = 0
        while head < len(comp):
            i = comp[head]
            head += 1
            x, y = i % w, i // w
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    k = ny * w + nx
                    if not seen[k] and not done[k] and pale(px[nx, ny]):
                        done[k] = 1
                        comp.append(k)
        if len(comp) >= min_size:
            out.extend((i % w, i // w) for i in comp)
    return out


def cutout(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    dq = deque()

    def seed(x, y, rule):
        i = y * w + x
        if not seen[i] and rule(px[x, y]):
            seen[i] = 1
            dq.append((x, y, rule))

    for x in range(w):
        seed(x, 0, tight)
        seed(x, h - 1, tight)
    for y in range(h):
        seed(0, y, tight)
        seed(w - 1, y, tight)
    while dq:
        x, y, rule = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                i = ny * w + nx
                if not seen[i] and rule(px[nx, ny]):
                    seen[i] = 1
                    dq.append((nx, ny, rule))

    # Second flood, seeded from the already-known backdrop, with a looser rule:
    # the plate and its contact shadow are both near-neutral, feet are not.
    seeds = [(i % w, i // w) for i in range(w * h) if seen[i]]
    _flood(px, seen, w, h, loose, seeds)

    # The plate and its shadow form one neutral slab under the feet; the legs
    # are saturated enough to stop the flood before it eats the body.
    def neutral(p):
        return (max(p) - min(p)) <= 40

    floor = int(h * 0.85)
    seeds = [(x, y) for y in range(floor, h) for x in range(w)
             if not seen[y * w + x] and neutral(px[x, y])]
    for x, y in seeds:
        seen[y * w + x] = 1
    _flood(px, seen, w, h, neutral, seeds)

    # The plate showing between the legs is cut off from every seed above by
    # edge anti-aliasing, so knock out pale slabs that are big enough to be
    # backdrop rather than teeth.
    for x, y in _pale_slabs(px, w, h, seen):
        seen[y * w + x] = 1

    keep = _largest_component(seen, w, h)
    alpha = Image.new("L", (w, h), 255)
    ad = alpha.load()
    for i in range(w * h):
        if seen[i] or not keep[i]:
            ad[i % w, i // w] = 0
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.9))

    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out.crop(alpha.getbbox())


def fit(sprite, key, value):
    if key == "height":
        ratio = value / sprite.height
    else:
        ratio = value / sprite.width
    return sprite.resize((max(1, round(sprite.width * ratio)),
                          max(1, round(sprite.height * ratio))), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [("hero_src.png", "idle", "height", 460),
            ("web_a1.png", "turn_a", "height", 460),
            ("web_a2.png", "turn_c", "width", 430)]
    made = {}
    for name, stem, key, value in jobs:
        src = os.path.join(SRC, name)
        if not os.path.exists(src):
            print("skip", name)
            continue
        sprite = fit(cutout(src), key, value)
        made[stem] = sprite

    if "turn_a" in made:
        made["turn_b"] = made["turn_a"].transpose(Image.FLIP_LEFT_RIGHT)

    for stem, sprite in made.items():
        sprite.save(os.path.join(OUT, stem + ".png"))
        probe = Image.new("RGBA", sprite.size, (210, 40, 150, 255))
        probe.alpha_composite(sprite)
        probe.convert("RGB").save(os.path.join(OUT, stem + "_probe.jpg"), quality=88)
        print(stem, sprite.size)


if __name__ == "__main__":
    main()
