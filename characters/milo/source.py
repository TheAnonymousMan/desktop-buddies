"""Milo's sprites. Edit this, then run  python tools/bake_sprites.py
to rebuild sprites.json (the app only reads the json)."""
from buddyart import *

ART = 2       # sprites are drawn at double detail

N_LEGS_A = ["....klk..klk", "....klk..klk", "....kffk.kffk", "....kkkk.kkkk"]
N_LEGS_B = ["...klk....klk", "...klk....klk", "...kffk...kffk", "...kkkk...kkkk"]


MILO_COLORS = {
    "k": "#2a2230",  # outline
    "h": "#7a4a2a",  # messy brown hair
    "H": "#5a3520",  # hair shade
    "s": "#ffdcc4",  # skin
    "S": "#f4a8a0",  # blush
    "L": "#f5f7fa",  # lab coat
    "D": "#c9d1db",  # lab coat shade
    "e": "#7a5230",  # eyes (warm brown)
    "E": "#2a1a12",  # pupils
    "i": "#c08a52",  # eye light
    "m": "#e2707a",  # open mouth
    "v": "#7fc8a9",  # mint sweater vest
    "V": "#5aa588",  # vest pattern
    "w": "#ffffff",  # shirt / mug
    "b": "#e0566a",  # bow tie
    "l": "#4a5a8a",  # trousers
    "f": "#f0f0f0",  # sneakers
    "B": "#c0504d",  # book cover
    "P": "#fff4d6",  # book pages
    "C": "#6b3e26",  # coffee
    "T": "#f1c0a6",  # skin shadow
    "A": "#9a6640",  # hair shine
    "W": "#ffffff",  # eye shine
}
MILO_RAMP = {"h": ("H", "A"), "L": ("D", None), "v": ("V", None), "s": ("T", None)}
# Hand-drawn faces, 20 x 8 double-detail pixels ('.' = skin)
MILO_FACE = {           # 20 x 8 double-detail pixels ('.' = skin)
    "open":   ["....kkkk....kkkk....",
               "....WWEe....WWEe....",
               "....WEEe....WEEe....",
               "....eEEi....eEEi....",
               ".SS...ii......ii..SS",
               "....................",
               ".........kk.........",
               "...................."],
    "blink":  ["....................",
               "....................",
               "....kkkk....kkkk....",
               "....................",
               ".SS...............SS",
               "....................",
               ".........kk.........",
               "...................."],
    "happy":  ["....................",
               ".....kk......kk.....",
               "....k..k....k..k....",
               "....................",
               ".SS...............SS",
               "........kkkk........",
               "........kmmk........",
               ".........kk........."],
    "eureka": ["....kkkk....kkkk....",
               "....WWEe....WWEe....",
               "....WEEe....WEEe....",
               "....eEEi....eEEi....",
               ".SS...ii......ii..SS",
               ".........kk.........",
               "........kmmk........",
               ".........kk........."],
}
# (brow row, upper eye row, lower eye row, mouth row) - 10 px wide
_S10 = "s" * 10
MILO_FACES = {
    "open":   (_S10, "sss" + "we" + "ss" + "we" + "s", "sss" + "ee" + "ss" + "ee" + "s",
               "sSssssksSs"),
    "blink":  (_S10, _S10, "sss" + "kk" + "ss" + "kk" + "s", "sSssssksSs"),
    "happy":  (_S10, "sss" + "kk" + "ss" + "kk" + "s", _S10, "sSssskksSs"),
    "eureka": ("sss" + "kk" + "ss" + "kk" + "s",          # raised brows, wide eyes:
               "sss" + "we" + "ss" + "we" + "s",          # a fact is coming!
               "sss" + "ee" + "ss" + "ee" + "s", "sSssskksSs"),
}


def milo_top(face="open", book=False, mug=False):
    brow = eye1 = eye2 = mouth = _S10          # face is drawn in detail later
    rows = [
        ".....kk..kk",
        "....khhkkhhk",
        "...k" + "h" * 8 + "k",
        "..k" + "hhhhHhhhhh" + "k",
        ".k" + "hhHhhhhhhHhh" + "k",
        ".k" + "hhsshhsssshh" + "k",
        ".kh" + "s" * 10 + "hk",
        ".kh" + brow + "hk",
        ".kh" + eye1 + "hk",
        ".kh" + eye2 + "hk",
        ".kh" + mouth + "hk",
        "..kh" + "s" * 8 + "hk",
        "....kLwbbwLk",                  # lab coat collar + bow tie
        "...kLLwbbwLLk",
    ]
    if mug:                              # both hands round his coffee mug
        rows += ["..kLkvkCCCkvLk",       # coffee on top (his red mug)
                 "..kLksBBBBsLLk",       # hands either side
                 "..kLkvkBBBkvLk"]
    elif book == "turn":                 # turning a page
        rows += ["..kLBPPkPPPBLk", "..kLBPPkPPkBLk", "..ksBBBBBBBBsk"]
    elif book:                           # holding an open book
        rows += ["..kLBPPkkPPBLk", "..kLBPPkkPPBLk", "..ksBBBBBBBBsk"]
    else:                                # open lab coat over the mint vest
        rows += ["..kLkLvvvvbkLk",       # red pen in the coat pocket
                 "..kLkLvVVvLkLk",
                 "..kskLvvvvLksk"]
    return rows + ["...kLDllllDLk"]      # coat tails over the trousers


MILO_HAIR_W, MILO_HAIR_H = 40, 30
# Each strand is a tapered spike: (root x, root y, tip x, tip y, root width),
# in double-detail pixels on a 40-wide canvas (his face is centred at x 19.5).
MILO_STRANDS = [
    # top: tousled spikes swept up and to the right
    (14, 6, 14, -2, 5), (18, 6, 25, -2, 6), (22, 6, 31, -1, 6), (25, 8, 35, 3, 7),
    (12, 7, 7, 1, 5),
    # sides: spikes, the right side sweeping out further
    (9, 11, 3, 14, 7), (9, 15, 4, 21, 6),
    (30, 10, 37, 10, 7), (31, 14, 37, 17, 7), (30, 17, 34, 22, 5),
    # bangs swept diagonally across his forehead towards the left
    (26, 10, 17, 18, 7), (22, 10, 12, 19, 7), (18, 10, 10, 20, 6),
    (29, 11, 27, 18, 6), (14, 11, 9, 21, 5),
]
MILO_HAIR_TOP = 0        # extra rows above the hair canvas for taller spikes
MILO_HAIR_SQUASH = 0.8   # hair above his brow is drawn this much shorter (same shape)
MILO_HAIR_PIVOT = 15


def _in_tri(px, py, a, b, c):
    def side(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = side((px, py), a, b), side((px, py), b, c), side((px, py), c, a)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def squash(y):
    """Pull points above the pivot down, keeping the hair's shape."""
    return y if y >= MILO_HAIR_PIVOT else MILO_HAIR_PIVOT - (MILO_HAIR_PIVOT - y) * MILO_HAIR_SQUASH


def unsquash(y):
    return y if y >= MILO_HAIR_PIVOT else MILO_HAIR_PIVOT - (MILO_HAIR_PIVOT - y) / MILO_HAIR_SQUASH


def milo_hair():
    """Rasterise the strands into a sprite patch: hair, darker strand edges,
    a shine on top and a dark outline wherever hair meets anything else."""
    w, h = MILO_HAIR_W, MILO_HAIR_H
    hair = [[False] * w for _ in range(h)]
    shadow = [[False] * w for _ in range(h)]
    T = MILO_HAIR_TOP
    for y in range(h):                       # the dome over his head
        for x in range(w):
            if ((x + 0.5 - 19.5) / 12) ** 2 + ((unsquash(y + 0.5) - T - 13.5) / 10) ** 2 <= 1                     and y - T <= 15:
                hair[y][x] = True
    for rx, ry, tx, ty, rw in MILO_STRANDS:
        ry, ty = squash(ry) + T, squash(ty) + T
        dx, dy = tx - rx, ty - ry
        n = (dx * dx + dy * dy) ** 0.5 or 1
        ox, oy = -dy / n * rw / 2, dx / n * rw / 2
        A, B, C = (rx + ox, ry + oy), (rx - ox, ry - oy), (tx + 0.5, ty + 0.5)
        for y in range(h):
            for x in range(w):
                if _in_tri(x + 0.5, y + 0.5, A, B, C):
                    hair[y][x] = True
                    # the side of each strand nearer its left edge is shaded
                    if _in_tri(x + 0.5, y + 0.5, A, ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2), C):
                        shadow[y][x] = True
    for _ in range(1):                       # drop stray single pixels at tips
        for y in range(h):
            for x in range(w):
                if hair[y][x] and sum(0 <= x + i < w and 0 <= y + j < h and hair[y + j][x + i]
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))) < 2:
                    hair[y][x] = False
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            if not hair[y][x]:
                row.append(".")
                continue
            edge = any(not (0 <= x + i < w and 0 <= y + j < h and hair[y + j][x + i])
                       for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                row.append("k")
            elif 8 <= y <= 10 and 12 <= x <= 18 and (x - y) in (4, 5):
                row.append("A")              # shine
            elif y >= 13 and y + 1 < h and not hair[y + 1][x]:
                row.append("H")              # shadow under each strand
            else:
                row.append("h")
        rows.append("".join(row))
    return rows


MILO_HAIR = milo_hair()


def milo_hd(lo, dy, face):
    """Double detail with anime hair (4 rows taller and 8 wider, so the
    spikes can flare out past his head)."""
    # his old side hair goes: the new strands replace it
    lo = [r.replace("kh", "ks", 1)[::-1].replace("kh", "ks", 1)[::-1]
          if r.lstrip(".").startswith("kh") and "s" in r else r for r in lo]
    rows = [("." * 4 + r).ljust(MILO_HAIR_W, ".")
            for r in ["." * 32] * 4 + detail(lo, MILO_RAMP)]
    rows = stamp(rows, 0, 2 * dy, MILO_HAIR)
    return stamp(rows, 10, 18 + 2 * dy, MILO_FACE[face])


def milo_stand(face="open", legs=N_LEGS_A):
    return milo_hd(milo_top() + legs, 0, face)


def milo_read(face="blink", turn=False):
    return milo_hd(milo_top(book="turn" if turn else True) + N_LEGS_A, 0, face)


def milo_sip(face="blink"):
    return milo_hd(milo_top(mug=True) + N_LEGS_A, 0, face)


def milo_sit(face="open"):
    return milo_hd(["", "", ""] + milo_top(book=True) + ["....kffk.kffk"], 3, face)


def coffee(level):
    top = "kCCCCkkk" if level < 3 else "kwwwwkkk"
    return ["kkkkkk..", top, "kwwwwk.k", "kwwwwkkk", ".kkkk..."]


MILO_FACTS = [
    "Octopuses have three hearts and blue blood.",
    "Honey never spoils. Edible honey has been found in ancient Egyptian tombs.",
    "A day on Venus is longer than its whole year.",
    "Bananas are berries, but strawberries aren't.",
    "Wombats poop cubes. Really!",
    "Sharks have been around longer than trees.",
    "Sea otters hold hands while they sleep so they don't drift apart.",
    "Cleopatra lived closer to the Moon landing than to the building of the Great Pyramid.",
    "There are more possible chess games than atoms in the observable universe.",
    "A group of flamingos is called a flamboyance.",
    "The Eiffel Tower grows about 15 cm taller in summer heat.",
    "Your stomach makes a new lining every few days.",
    "Butterflies taste with their feet.",
    "The first computer 'bug' was a real moth, found in a computer in 1947.",
    "Oxford University is older than the Aztec Empire.",
    "Sunlight takes about 8 minutes to reach Earth.",
    "Koala fingerprints are almost identical to human ones.",
    "A teaspoon of neutron star would weigh billions of tons.",
    "The dot over a lowercase i is called a tittle.",
    "Python, the language I'm written in, is named after Monty Python, not the snake.",
    "Lightning is about five times hotter than the surface of the Sun.",
    "Scotland's national animal is the unicorn.",
    "Some turtles can breathe through their butts.",
    "The shortest war in history lasted about 38 minutes.",
    "Cats can't taste sweet things.",
    "Venus spins backwards compared to most planets.",
    "Your brain uses about 20% of your body's energy.",
    "An ostrich's eye is bigger than its brain.",
]


PALETTE = MILO_COLORS
item = coffee          # what it eats, at 6 levels of eaten

SPRITES = {
    "stand": milo_stand(),
    "stand_b": milo_stand(),
    "blink": milo_stand("blink"),
    "walk1": milo_stand(legs=N_LEGS_A),
    "walk2": milo_stand(legs=N_LEGS_B),
    "happy": milo_stand("happy"),
    "held": milo_stand("blink", legs=N_LEGS_B),
    "fact": milo_stand("eureka"),
    "loaf": milo_sit(),                 # sits and reads
    "loaf_blink": milo_sit("blink"),
    "sleep": milo_sit("blink"),         # dozed off reading
    "sleep_b": milo_sit("blink"),
    # his own moves (behaviours.py)
    "read1": milo_read(),
    "read2": milo_read(turn=True),
    "read_look": milo_read("open"),
    "sip": milo_sip(),
    "sip_happy": milo_sip("happy"),
}

PROPS = {
    "mug": thin(up2(coffee(3))),        # his empty coffee mug
}
# Effects float up and vanish, like hearts (buddy.spawn("steam")).
EFFECTS = {
    "steam": up2([".D.", "D..", ".D.", "..D", ".D."]),     # from his coffee
}
