"""Pixel-art helpers for building character sprites (used by each
character's source.py and by tools/bake_sprites.py - the buddies app itself only
reads the baked sprites.json files)."""


def pad(r, w):
    assert len(r) <= w, r
    return r.ljust(w, ".")


def up2(rows):
    """Double a sprite's resolution (EPX): every pixel becomes 2x2, and
    corners follow diagonal edges so outlines come out smooth, not blocky."""
    w = max((len(r) for r in rows), default=0)
    g = [pad(r, w) for r in rows]
    h = len(g)
    at = lambda x, y: g[y][x] if 0 <= x < w and 0 <= y < h else "."
    out = []
    for y in range(h):
        top, bot = [], []
        for x in range(w):
            p, a, b, c, d = g[y][x], at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            p1 = a if c == a and c != d and a != b else p
            p2 = b if a == b and a != c and b != d else p
            p3 = c if d == c and d != b and c != a else p
            p4 = d if b == d and b != a and d != c else p
            top += [p1, p2]
            bot += [p3, p4]
        out += ["".join(top), "".join(bot)]
    return out


def thin(rows):
    """After up2 every outline is 2 pixels thick; keep only the outer pixel
    so lines are as fine as the new detail (inner lines keep one pixel)."""
    w = max((len(r) for r in rows), default=0)
    g = [list(pad(r, w)) for r in rows]
    src = [r[:] for r in g]
    h = len(g)
    at = lambda x, y: src[y][x] if 0 <= x < w and 0 <= y < h else "."
    for y in range(h):
        for x in range(w):
            if src[y][x] != "k":
                continue
            for dx, dy in ((0, 1), (1, 0)):
                before, after = at(x - dx, y - dy), at(x + dx, y + dy)
                if before not in "k." and after == "k":            # fill / k / k
                    g[y][x] = before
                    break
                if after not in "k." and before == "k" and at(x - 2 * dx, y - 2 * dy) == ".":
                    g[y][x] = after                                  # . / k / k / fill
                    break
    return ["".join(r) for r in g]


def shade(rows, ramp):
    """Add soft volume: colors in `ramp` ({base: (shadow, light)}) get their
    shadow tone along bottom outlines and their light tone under top ones."""
    w = max((len(r) for r in rows), default=0)
    g = [list(pad(r, w)) for r in rows]
    src = [r[:] for r in g]
    h = len(g)
    for y in range(h):
        for x in range(w):
            c = src[y][x]
            if c not in ramp:
                continue
            dark, light = ramp[c]
            below = [src[y + i][x] if y + i < h else "." for i in (1, 2)]
            above = src[y - 1][x] if y > 0 else "."
            if dark and ("k" in below or "." in below[:1]):
                g[y][x] = dark
            elif light and above in "k.":
                g[y][x] = light
    return ["".join(r) for r in g]


def detail(lo, ramp, face=None, at=(0, 0)):
    """Normal-size rows -> double-detail rows with fine outlines and shading,
    with an optional hand-drawn face patch painted at `at`."""
    rows = shade(thin(up2(lo)), ramp)
    return stamp(rows, at[0], at[1], face) if face else rows


def stamp(rows, x, y, patch):
    """Paint a hand-drawn patch onto rows at (x, y); '.' in the patch keeps
    what was there and ' ' makes it transparent."""
    out = list(rows)
    while len(out) < y + len(patch):
        out.append("")
    for j, prow in enumerate(patch):
        r = list(out[y + j].ljust(x + len(prow), "."))
        for i, ch in enumerate(prow):
            if ch != ".":
                r[x + i] = "." if ch == " " else ch
        out[y + j] = "".join(r)
    return out


def rotate_ccw(rows):
    """Rotate a sprite 90 degrees counter-clockwise (a right-facing buddy now
    faces up, with its feet against a wall on the right)."""
    w = max(len(r) for r in rows)
    rows = [pad(r, w) for r in rows]
    return ["".join(row[w - 1 - i] for row in rows) for i in range(w)]


def glitchify(rows, shifts, recolor):
    """Fake a display glitch: slide some rows sideways and recolor others."""
    w = max(len(r) for r in rows)
    out = [pad(r, w) for r in rows]
    for i, d in shifts:
        out[i] = ("." * d + out[i])[:w] if d > 0 else out[i][-d:] + "." * -d
    for i, a, b in recolor:
        out[i] = out[i].replace(a, b)
    return out


def strands(w, h, spikes, fill="h", shade="H"):
    """Draw tapered hair strands (or tails, spikes...) on a w x h canvas.
    spikes: [(root x, root y, tip x, tip y, root width), ...] in pixels.
    Returns rows with a dark outline and a shaded underside; '.' elsewhere."""
    def inside(px, py, a, b, c):
        def side(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        d = (side((px, py), a, b), side((px, py), b, c), side((px, py), c, a))
        return not (min(d) < 0 < max(d))
    mask = [[False] * w for _ in range(h)]
    for rx, ry, tx, ty, rw in spikes:
        dx, dy = tx - rx, ty - ry
        n = (dx * dx + dy * dy) ** 0.5 or 1
        ox, oy = -dy / n * rw / 2, dx / n * rw / 2
        a, b, c = (rx + ox, ry + oy), (rx - ox, ry - oy), (tx + 0.5, ty + 0.5)
        for y in range(h):
            for x in range(w):
                if inside(x + 0.5, y + 0.5, a, b, c):
                    mask[y][x] = True
    on = lambda x, y: 0 <= x < w and 0 <= y < h and mask[y][x]
    rows = []
    for y in range(h):
        row = ""
        for x in range(w):
            if not mask[y][x]:
                row += "."
            elif not all(on(x + i, y + j) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                row += "k"
            elif not on(x, y + 2) or not on(x - 2, y):
                row += shade
            else:
                row += fill
        rows.append(row)
    return rows


def behind(front, back):
    """Layer two sprites: `front` wherever it isn't see-through, else `back`."""
    h = max(len(front), len(back))
    w = max(max((len(r) for r in front), default=0), max((len(r) for r in back), default=0))
    f = [pad(r, w) for r in front] + ["." * w] * (h - len(front))
    b = [pad(r, w) for r in back] + ["." * w] * (h - len(back))
    return ["".join(fc if fc != "." else bc for fc, bc in zip(fr, br)) for fr, br in zip(f, b)]
