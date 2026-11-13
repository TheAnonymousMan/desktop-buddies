"""Roxy's sprites: a hip, cool girl, all in pink. A high side ponytail, pink
shades, headphones round her neck, a crop hoodie and a skateboard.

Rebuild sprites.json after editing:
    python tools/bake_sprites.py roxy
"""
from buddyart import *

ART = 2

ROXY_COLORS = {
    "k": "#3a1530",  # outline (dark plum)
    "h": "#ff5fa8",  # hair, hot pink
    "H": "#d93d86",  # hair shadow
    "A": "#ffa8d2",  # hair shine
    "s": "#ffdbe3",  # skin (pink-tinted)
    "T": "#f6bccb",  # skin shadow
    "S": "#ff8fb1",  # blush
    "l": "#ff2e93",  # sunglasses lenses
    "w": "#ffffff",  # shine / teeth / sneakers
    "E": "#c2185b",  # eyes (when the shades come down)
    "j": "#ff9ccd",  # crop hoodie
    "J": "#e86aa8",  # hoodie shadow
    "U": "#ffc6e3",  # hoodie light
    "d": "#c2185b",  # shorts, deep pink
    "D": "#99124a",  # shorts shadow
    "m": "#ff3d8b",  # headphones / skateboard deck
    "p": "#ff5fa8",  # shoelaces
    "b": "#ff9fd0",  # bubblegum
    "t": "#f7b6d2",  # bubble tea
    "c": "#fff0f7",  # empty cup
    "r": "#e0457b",  # lips
}
ROXY_RAMP = {"h": ("H", "A"), "j": ("J", "U"), "s": ("T", None), "d": ("D", None)}


def roxy_top():
    """Normal-size head and body, 16 wide, with a plain face (drawn later)."""
    face = "kh" + "s" * 12 + "hk"
    return [
        "....kkkkkkkk....",
        "..kkhhhhhhhhkk..",
        ".khhhhhhhhhhhhk.",
        ".khhhhhhhhhhhhk.",
        "khhhhhhhhhhhhhhk",
        "khhhHhhhhhhHhhhk",
        "khhsshhsshhsshhk",        # bangs
        face, face, face, face,
        ".kh" + "s" * 10 + "hk.",
        "...kssssssssk...",
        "....kmmssmmk....",        # headphones round her neck
        "...kmmjjjjmmk...",
        "..kjjjjjjjjjjk..",        # crop hoodie
        ".kjjJjjjjjjJjjk.",
        "kssjjjjjjjjjjssk",
        "..kJJJJJJJJJJk..",
        "..kddddddddddk..",        # shorts
        "...kddkkkkddk...",
    ]


LEGS_A = ["....kssk.kssk...", "....kssk.kssk...", "....kwpk.kwpk...", "....kkkk.kkkk..."]
LEGS_B = ["...kssk...kssk..", "...kssk...kssk..", "...kwpk...kwpk..", "...kkkk...kkkk.."]
BOARD = ["....kwpk.kwpk...",               # on her skateboard
         "kmmmmmmmmmmmmmmk",
         ".kkkkkkkkkkkkkk.",
         "..kwk......kwk.."]

# Faces, 20 x 8 double-detail pixels painted over her face ('.' = skin)
FACES = {
    "cool":  ["....................",       # shades on, little smirk
              "..kkkkkkkkkkkkkkkk..",
              "..kwllllk..kwllllk..",
              "..klllllk..klllllk..",
              "...kkkkk....kkkkk...",
              ".SS.........r....SS.",
              "........rrrr........",
              "...................."],
    "grin":  ["....................",
              "..kkkkkkkkkkkkkkkk..",
              "..kwllllk..kwllllk..",
              "..klllllk..klllllk..",
              "...kkkkk....kkkkk...",
              ".SS..............SS.",
              ".......rwwwwr.......",
              "........rrrr........"],
    "peek":  ["....................",       # shades pulled down: a wink
              "...kkkk.......kkk...",
              "...wEEk......k...k..",
              "...EEEk.............",
              "..kkkkkkkkkkkkkkkk..",
              ".SklllllkkklllllkS..",
              "........rrrr........",
              "...................."],
    "chill": ["....................",       # eyes closed behind the shades, relaxed
              "..kkkkkkkkkkkkkkkk..",
              "..klllllk..klllllk..",
              "..klllllk..klllllk..",
              "...kkkkk....kkkkk...",
              ".SS..............SS.",
              ".........rrr........",
              "...................."],
}


def bubble(r):
    """A bubblegum bubble of radius r (double-detail pixels), centred on her mouth."""
    size = 2 * r + 1
    rows = []
    for y in range(size):
        row = ""
        for x in range(size):
            d = ((x - r) ** 2 + (y - r) ** 2) ** 0.5
            if d <= r - 0.6:
                row += "w" if (x - r + r * 0.45) ** 2 + (y - r + r * 0.45) ** 2 < (r * 0.25) ** 2 + 0.5 else "b"
            elif d <= r + 0.4:
                row += "k"
            else:
                row += "."
        rows.append(row)
    return rows


# High side ponytail, drawn behind her head: tied at the top right and swept
# out and down. (root x, root y, tip x, tip y, width) in double-detail pixels.
PONYTAIL = strands(40, 40, [(29, 3, 38, 24, 13), (30, 6, 35, 33, 10), (28, 2, 39, 12, 9)])
TIE = ["mm", "mm", "mm"]            # hair tie


def with_hair(rows, dy=0):
    """Put the ponytail behind a double-detail sprite (dy: rows lower)."""
    tail = ["." * 40] * dy + PONYTAIL
    return stamp(behind(rows, tail), 27, 1 + dy, TIE)


def roxy(face="cool", legs=LEGS_A, gum=0):
    rows = with_hair(detail(roxy_top() + legs, ROXY_RAMP, FACES[face], (6, 14)))
    if gum:                                   # mouth is around x 16, y 20
        b = bubble(gum)
        rows = stamp(rows, 16 - gum, 20 - gum, b)
    return rows


def roxy_sit(face="cool"):
    feet = "....kwpk.kwpk..."
    return with_hair(detail(["", "", ""] + roxy_top() + [feet], ROXY_RAMP, FACES[face], (6, 20)), 6)


def roxy_skate(face="cool", lean=False):
    return with_hair(detail(roxy_top() + BOARD, ROXY_RAMP, FACES[face], (6, 14)))


def boba(level):
    """Bubble tea, 6 levels: the tea goes down, then it's gone."""
    cup = ["...kk.", "...k..", "kkkkkk", "kttttk", "kttttk", "kttttk", "ktktkk", ".kkkk."]
    if level >= 5:
        return ["."]
    for i in range(3, 3 + min(3, level)):        # drink from the top
        cup[i] = cup[i].replace("t", "c")
    return cup


PALETTE = ROXY_COLORS
item = boba

SPRITES = {
    "stand": roxy(),
    "stand_b": roxy("chill"),
    "blink": roxy("chill"),
    "walk1": roxy(legs=LEGS_A),
    "walk2": roxy(legs=LEGS_B),
    "happy": roxy("grin"),
    "happy_b": roxy("grin", legs=LEGS_B),
    "held": roxy("grin", legs=LEGS_B),
    "loaf": roxy_sit(),
    "loaf_blink": roxy_sit("chill"),
    "sleep": roxy_sit("chill"),
    "sleep_b": roxy_sit("chill"),
    "climb1": rotate_ccw(roxy(legs=LEGS_A)),
    "climb2": rotate_ccw(roxy(legs=LEGS_B)),
    # her own moves (behaviours.py)
    "peek": roxy("peek"),
    "skate": roxy_skate(),
    "skate_b": roxy_skate("grin"),
    "gum1": roxy("cool", gum=2),
    "gum2": roxy("cool", gum=4),
    "gum3": roxy("cool", gum=6),
    "vibe1": roxy("chill"),
    "vibe2": roxy("grin", legs=LEGS_B),
}

PROPS = {
    "board": thin(up2(["kmmmmmmmmmmmmmmk", ".kkkkkkkkkkkkkk.", "..kwk......kwk.."])),
}
# Effects float up and vanish, like hearts (buddy.spawn("gum_pop")).
EFFECTS = {
    "gum_pop": up2(["b..b..b", ".b.b.b.", "..bbb..", "bbbwbbb", "..bbb..", ".b.b.b.", "b..b..b"]),
}
