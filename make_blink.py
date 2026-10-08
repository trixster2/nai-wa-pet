"""Derive a closed-eye frame from sprites/idle.png.

    python make_blink.py

The lids are painted by lifting a strip of fur from just above each eye and
drawing a smile-shaped lash line, so the blink stays in the plush's own
texture instead of looking like a flat patch.
"""
import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.join(HERE, "sprites")
SRC = os.path.join(SP, "idle.png")
DST = os.path.join(SP, "blink.png")

LID = (107, 74, 42, 255)


def greenish(p):
    r, g, b = p[:3]
    return g > r + 6 and g > b + 20 and g > 90


def find_eyes(im):
    px = im.load()
    w, h = im.size
    pts = [(x, y) for y in range(h) for x in range(w) if greenish(px[x, y])]
    if len(pts) < 40:
        return []
    # A few stray greenish pixels sit in the hat crease and between the toes;
    # the iris rings are by far the densest rows, so keep only those.
    rows = Counter(y // 10 for _, y in pts)
    dense = {r for r, n in rows.items() if n > 20}
    pts = [p for p in pts if p[1] // 10 in dense]
    mid = sum(x for x, _ in pts) / len(pts)
    left = [p for p in pts if p[0] < mid]
    right = [p for p in pts if p[0] >= mid]
    boxes = []
    for group in (left, right):
        if len(group) < 15:
            continue
        xs = [p[0] for p in group]
        ys = [p[1] for p in group]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    return boxes


def ring_color(im, box, grow=11):
    """Median fur colour from the annulus hugging an eye — locally lit, so it
    matches far better than lifting a patch from the forehead."""
    px = im.load()
    w, h = im.size
    x0, y0, x1, y1 = box
    xs0, ys0 = max(0, x0 - grow), max(0, y0 - grow)
    xs1, ys1 = min(w, x1 + grow), min(h, y1 + grow)
    inner0, inner1 = (x0 - 2, y0 - 2), (x1 + 2, y1 + 2)
    rs, gs, bs = [], [], []
    for y in range(ys0, ys1):
        for x in range(xs0, xs1):
            if inner0[0] <= x <= inner1[0] and inner0[1] <= y <= inner1[1]:
                continue
            r, g, b, a = px[x, y]
            if a < 200 or greenish((r, g, b)) or min((r, g, b)) < 150:
                continue
            rs.append(r); gs.append(g); bs.append(b)
    if len(rs) < 50:
        return (250, 226, 150, 255)
    rs.sort(); gs.sort(); bs.sort()
    m = len(rs) // 2
    return (rs[m], gs[m], bs[m], 255)


def main():
    base = Image.open(SRC).convert("RGBA")
    out = base.copy()
    boxes = find_eyes(base)
    if not boxes:
        raise SystemExit("no eyes found — check sprites/idle.png")

    for (x0, y0, x1, y1) in boxes:
        ew, eh = x1 - x0, y1 - y0
        fill = ring_color(base, (x0, y0, x1, y1))
        mask = Image.new("L", out.size, 0)
        pad = 2
        ImageDraw.Draw(mask).ellipse((x0 - pad, y0 - pad, x1 + pad, y1 + pad), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(4.5))
        lid = Image.new("RGBA", out.size, fill)
        out = Image.composite(lid, out, mask)

    draw = ImageDraw.Draw(out)
    for (x0, y0, x1, y1) in boxes:
        ew, eh = x1 - x0, y1 - y0
        inset = max(2, ew // 8)
        draw.arc((x0 + inset, y0 - eh * 0.18, x1 - inset, y1 - eh * 0.08),
                 start=20, end=160, fill=LID, width=max(3, ew // 7))

    out.save(DST)
    probe = Image.new("RGBA", (out.width * 2 + 16, out.height), (210, 40, 150, 255))
    probe.alpha_composite(base, (0, 0))
    probe.alpha_composite(out, (out.width + 16, 0))
    probe.convert("RGB").save(os.path.join(SP, "blink_probe.jpg"), quality=90)
    print("eyes:", boxes)


if __name__ == "__main__":
    main()
