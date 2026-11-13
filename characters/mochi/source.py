"""Mochi's sprites. Edit this, then run  python tools/bake_sprites.py
to rebuild sprites.json (the app only reads the json)."""
from buddyart import *

ART = 2       # sprites are drawn at double detail

MOCHI_COLORS = {
    "k": "#2b1d14", "o": "#f2a65a", "d": "#d9843a", "w": "#fff4e6",
    "p": "#f7a1b5", "g": "#3f9b4f", "b": "#5b8bd9",
    "r": "#ff6f91",  # blush
    "O": "#f9c487",  # fur highlight
    "q": "#c06a2c",  # fur shadow
    "W": "#e9d3bc",  # cream shadow
    "n": "#e8708c",  # nose
    "G": "#8fe08a",  # eye shine
    "K": "#5a4434",  # whiskers
    "x": "#b9aea6",  # claw marks
}
MOCHI_RAMP = {"o": ("q", "O"), "w": ("W", None), "d": ("q", None)}
# Hand-drawn face, painted over the head (16 x 8 double-detail pixels).
# '.' keeps the fur underneath.
# Mochi's head is hand-drawn at double detail: 20 wide, 16 tall. Rows are
# written as the left half and mirrored, so the face stays symmetric.
_MOCHI_HEAD_LEFT = [
    "...k......",
    "..kOk.....",
    "..kpOk....",
    ".kOppOk...",
    ".kOpppkkkk",
    "kOooooOOOd",
    "kooooooOod",
    "kOoooooooo",
    "kooooooooo",
    "kooooooooo",
    "kooooooooo",
    "kqoooowwnn",               # nose
    "kqqoowwwkn",
    ".kqqowwwwk",
]
MOCHI_HEAD = [r + r[::-1] for r in _MOCHI_HEAD_LEFT] + [
    "..kqowwwwwwwwwwk....",           # chin flows into the white chest
    "...qowwwwwwwwwwk....",
]
# Whiskers poke out past both cheeks (32 wide, painted from 6 px left of the head).
MOCHI_WHISKERS = [
    ".KKKKK.KK." + "." * 12 + ".KK.KKKKK.",
    "." * 32,
    "..KKKK.KK." + "." * 12 + ".KK.KKKK..",
]
# Eyes (and blush) painted onto the head, starting at its 9th row.
MOCHI_FACE = {
    "open":   ["....kkk......kkk...",
               "....Gkg......gkG...",
               "....gkg......gkg..."],
    "closed": ["....................",
               "....kkk......kkk...",
               "...................."],
    "happy":  ["....................",
               ".....k........k....",
               "....k.k......k.k...",
               "....................",
               ".rr..............rr."],
}
MOCHI_BODY = [
    "",
    "..............k....k",
    ".............kpk..kpk",
    ".k" + "." * 10 + "kooodooook",
    "kok" + "." * 9 + "kooogoogok",
    "kok" + "." * 9 + "kooooopook",
    "kok" + "." * 10 + "kwwwwwwk",
    ".kok" + "k" * 10 + "owwwwk",
    "..k" + "ooodooodoooo" + "wwww" + "k",
    "..k" + "oooodooodoooo" + "www" + "k",
    "..k" + "o" * 14 + "ww" + "k",
    "...k" + "o" * 15 + "k",
]
M_LEGS_A = ["....kok.kok.kok.kok", "....kkk.kkk.kkk.kkk"]
M_LEGS_B = ["....kokkok....kokkok", "....kkkkkk....kkkkkk"]
M_LEGS_DANGLE = ["....kok.kok.kok.kok", "....kok.kok.kok.kok"]


def mochi_lo(tail="a"):
    """The normal-size body, without a face (the face is drawn in detail)."""
    rows = [pad(r, 22).replace("g", "o").replace("p", "o") for r in MOCHI_BODY]
    rows[2] = pad(MOCHI_BODY[2], 22)               # keep the pink inside the ears
    if tail == "b":
        for i, pre in ((3, "..k."), (4, ".kok"), (5, ".kok")):
            rows[i] = pre + rows[i][4:]
    return rows


def mochi_hd(lo, dy, eyes=True, blush=False):
    """Double the detail and shade the body, then paint the hand-drawn head
    and face (dy = rows the body sits lower in this pose, normal-size)."""
    lo = [pad(r, 22) for r in lo]
    for i in range(1 + dy, 7 + dy):                 # clear the old blocky head
        lo[i] = lo[i][:12] + "." * 10
    face = "happy" if blush else "open" if eyes else "closed"
    rows = shade(thin(up2(lo)), MOCHI_RAMP)
    rows = stamp(rows, 24, 2 * dy, MOCHI_HEAD)
    rows = stamp(rows, 24, 2 * dy + 8, MOCHI_FACE[face])
    return stamp(rows, 18, 2 * dy + 11, MOCHI_WHISKERS)


def mochi_body(tail="a", eyes=True, blush=False):
    return mochi_hd(mochi_lo(tail), 0, eyes, blush)


def mochi_stand(tail="a", eyes=True, legs=M_LEGS_A, blush=False):
    feet = thin(up2(legs))
    return mochi_body(tail, eyes, blush) + feet


def mochi_loaf(tail="a", eyes=True):
    lo = ["", ""] + mochi_lo(tail)[1:] + ["...k" + "k" * 15 + "k"]
    return mochi_hd(lo, 1, eyes)


PALETTE = MOCHI_COLORS
item = lambda level: [".dddddddd.", "kbbbbbbbbk", ".kbbbbbbk.", "..kkkkkk.."]          # what it eats, at 6 levels of eaten

SPRITES = {
    "stand": mochi_stand(),
    "stand_b": mochi_stand(tail="b"),
    "blink": mochi_stand(eyes=False),
    "walk1": mochi_stand(legs=M_LEGS_A),
    "walk2": mochi_stand(tail="b", legs=M_LEGS_B),
    "happy": mochi_stand(tail="b", eyes=False, blush=True),
    "happy_b": mochi_stand(tail="a", eyes=False, blush=True),
    "held": mochi_stand(legs=M_LEGS_DANGLE, blush=True),
    "loaf": mochi_loaf(),
    "loaf_blink": mochi_loaf(eyes=False),
    "sleep": mochi_loaf(eyes=False),
    "sleep_b": mochi_loaf(tail="b", eyes=False),
    "climb1": rotate_ccw(mochi_stand(legs=M_LEGS_A)),
    "climb2": rotate_ccw(mochi_stand(tail="b", legs=M_LEGS_B)),
}

# Marks stay put on the screen and fade (buddy.leave_mark("scratch")).
MARKS = {
    "scratch": up2(["x..x..x..", ".x..x..x.", ".x..x..x.", "..x..x..x", "..x..x..x"]),
}
