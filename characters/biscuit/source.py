"""Biscuit's sprites. Edit this, then run  python tools/bake_sprites.py
to rebuild sprites.json (the app only reads the json)."""
from buddyart import *

ART = 2       # sprites are drawn at double detail

BISCUIT_COLORS = {
    "k": "#3a2414",  # outline
    "o": "#e8a948",  # golden fur
    "d": "#c98a2e",  # darker gold (ears, fluff)
    "w": "#fbe3b0",  # cream chest / muzzle
    "n": "#2a1a10",  # nose
    "e": "#2a1a10",  # eye
    "t": "#f27a8a",  # tongue
    "O": "#f6c873",  # fur shine
    "W": "#e8c98f",  # cream shadow
    "x": "#ffffff",  # eye shine
    "r": "#e5484d",  # ball
    "R": "#b32d32",  # ball shadow
    "m": "#8a6845",  # muddy paws
}
BISCUIT_RAMP = {"o": ("d", "O"), "w": ("W", None)}
BISCUIT_EYES = {          # 4 x 4 double-detail pixels over his eye
    True:  [".kk.", "kxkk", "kkkk", ".kk."],
    False: ["....", "....", "kkkk", "...."],
}
BISCUIT_BODY = [
    "." * 14 + "kkkk",
    "." * 13 + "k" + "oooo" + "k",
    "." * 12 + "kd" + "ooooo" + "k",
    "." * 12 + "kdd" + "oo" + "e" + "oo" + "kk",
    "." * 12 + "kdd" + "ooooo" + "wn",       # nose
    "." * 12 + "kdd" + "ooow" + "wwk",
    "." * 12 + "kdk" + "ooo" + "wtk",        # tongue out
    "..kkkkkkkkkkk" + "oooooo" + "tk",
    "..k" + "o" * 14 + "ww" + "k",
    "..k" + "ooo" + "d" + "oooooo" + "d" + "ooo" + "ww" + "k",
    "..k" + "o" * 15 + "w" + "k",
    "...k" + "o" * 13 + "k",
]
B_TAILS = {   # feathery tail, overlaid on the start of rows 3-7
    "a": {3: ".kk", 4: "kodk", 5: ".kook", 6: "..kook"},
    "b": {5: "kkk", 6: "koook"},
}
B_LEGS_A = ["...kok.kok...kok.kok", "...kkk.kkk...kkk.kkk"]
B_LEGS_B = ["....kokkok....kokkok", "....kkkkkk....kkkkkk"]
B_LEGS_DANGLE = ["...kok.kok...kok.kok", "...kok.kok...kok.kok"]


def biscuit_lo(tail="a"):
    rows = [pad(r, 22).replace("e", "o") for r in BISCUIT_BODY]
    for i, piece in B_TAILS[tail].items():
        rows[i] = piece + rows[i][len(piece):]
    return rows


def biscuit_body(tail="a", eyes=True, dy=0, lo=None):
    lo = lo or biscuit_lo(tail)
    return detail(lo, BISCUIT_RAMP, BISCUIT_EYES[eyes], (33, 5 + 2 * dy))


def biscuit_stand(tail="a", eyes=True, legs=B_LEGS_A):
    return biscuit_body(tail, eyes) + thin(up2(legs))


def biscuit_lie(tail="a", eyes=True):
    lo = ["", ""] + biscuit_lo(tail)[1:] + ["...k" + "k" * 13 + "k"]
    return biscuit_body(tail, eyes, 1, lo)


def bone(level):
    rows = ["kk....kk", "kwwwwwwk", "kk....kk"]
    bite = min(8, level * 2)
    return ["." * bite + r[bite:] for r in rows] if bite < 8 else ["."]


PALETTE = BISCUIT_COLORS
item = bone          # what it eats, at 6 levels of eaten

SPRITES = {
    "stand": biscuit_stand(),
    "stand_b": biscuit_stand(tail="b"),
    "blink": biscuit_stand(eyes=False),
    "walk1": biscuit_stand(legs=B_LEGS_A),
    "walk2": biscuit_stand(tail="b", legs=B_LEGS_B),
    "happy": biscuit_stand(eyes=False),
    "happy_b": biscuit_stand(tail="b", eyes=False),   # wag wag wag
    "held": biscuit_stand(tail="b", legs=B_LEGS_DANGLE),
    "loaf": biscuit_lie(),
    "loaf_blink": biscuit_lie(eyes=False),
    "sleep": biscuit_lie(eyes=False),
    "sleep_b": biscuit_lie(tail="b", eyes=False),
}

# Props are real objects in the world (buddy.drop_prop("ball")).
PROPS = {
    "ball": thin(up2([".kkkk.", "krrwrk", "krwrrk", "kwrrRk", "krrRRk", ".kkkk."])),
}
# Marks stay put on the screen and fade (buddy.leave_mark("paw")).
MARKS = {
    "paw": up2([".m.m.", "m.m.m", ".mmm.", ".mmm."]),
}
