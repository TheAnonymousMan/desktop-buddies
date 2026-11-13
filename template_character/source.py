"""Pip's sprites: a simple round blob, as a starting point for your own art.

Edit this, then rebuild sprites.json with:
    python tools/bake_sprites.py characters/<your folder>

How it works: the body is drawn as small "normal-size" pixel rows (easy to
edit), then detail() doubles the resolution, thins the outlines and adds
shading, and the face is painted on at double detail. If you'd rather draw
every pixel yourself, set ART = 1 and write the rows directly in SPRITES.
"""
from buddyart import *

ART = 2          # 2 = double detail (each art pixel is half size on screen)

# One character per colour. "." is always see-through.
PIP_COLORS = {
    "k": "#2a2140",  # outline
    "b": "#7fc8f0",  # body
    "B": "#58a3d6",  # body shadow   (added by shade() along the bottom)
    "L": "#bfe6ff",  # body light    (added by shade() along the top)
    "e": "#2a2140",  # eyes
    "w": "#ffffff",  # eye shine
    "p": "#ff9bb8",  # blush
    "c": "#d9a35b",  # cookie
    "C": "#8a5a2b",  # chocolate chips
}
# shade(): colour -> (shadow colour, light colour); None = leave as is
PIP_RAMP = {"b": ("B", "L")}

# Normal-size body, 14 wide. Sprites face RIGHT (they're mirrored to walk left).
BODY = [
    "....kkkkkk....",
    "..kkbbbbbbkk..",
    ".kbbbbbbbbbbk.",
    ".kbbbbbbbbbbk.",
    "kbbbbbbbbbbbbk",
    "kbbbbbbbbbbbbk",
    "kbbbbbbbbbbbbk",
    ".kbbbbbbbbbbk.",
    "..kkkkkkkkkk..",
]
LEGS_A = ["...kbk..kbk...", "...kkk..kkk..."]      # standing / walk frame 1
LEGS_B = ["..kbk....kbk..", "..kkk....kkk.."]      # walk frame 2
LEGS_DANGLE = ["...kbk..kbk...", "...kbk..kbk..."]  # held in the air
SIT_BOTTOM = ["..kkkkkkkkkk.."]                     # sitting: no legs

# Faces at double detail (28 wide over the body's rows 2-5).
# "." keeps the body colour underneath.
FACES = {
    "open":  ["............................",
              "........ww.......ww.........",
              "........ee.......ee.........",
              "........ee.......ee.........",
              ".....pp...............pp....",
              "............kkk.............",
              "............................",
              "............................"],
    "blink": ["............................",
              "............................",
              "............................",
              "........ee.......ee.........",
              ".....pp...............pp....",
              "............kkk.............",
              "............................",
              "............................"],
    "happy": ["............................",
              "............................",
              ".........e.........e........",
              "........e.e.......e.e.......",
              ".....pp...............pp....",
              "...........k...k............",
              "............kkk.............",
              "............................"],
}


def pip(face="open", legs=LEGS_A, sitting=False):
    """Build one sprite. sitting = the body sits 2 normal pixels lower."""
    lo = (["", ""] + BODY + SIT_BOTTOM) if sitting else BODY + legs
    dy = 2 if sitting else 0
    return detail(lo, PIP_RAMP, FACES[face], (0, 4 + 2 * dy))


PALETTE = PIP_COLORS


def item(level):
    """The food, at 6 levels: 0 = whole ... 5 = gone. Normal-size pixels."""
    cookie = [".kkkk.", "kcCcck", "kcccCk", "kCccck", ".kkkk."]
    bite = min(6, level + (1 if level else 0))       # bitten from the left
    return ["." * bite + r[bite:] for r in cookie] if bite < 6 else ["."]


# Every sprite the engine uses. Required: stand blink walk1 walk2 happy held
# loaf loaf_blink sleep sleep_b. Optional: stand_b happy_b loaf_b (extra
# animation frames), climb1 climb2 (for climb_style "claws"), glitch1 glitch2.
# Your own moves (behaviours.py) can use any other names.
SPRITES = {
    "stand": pip(),
    "stand_b": pip(),
    "blink": pip("blink"),
    "walk1": pip(legs=LEGS_A),
    "walk2": pip(legs=LEGS_B),
    "happy": pip("happy"),
    "held": pip("open", legs=LEGS_DANGLE),
    "loaf": pip(sitting=True),
    "loaf_blink": pip("blink", sitting=True),
    "sleep": pip("blink", sitting=True),
    "sleep_b": pip("blink", sitting=True),
    "climb1": rotate_ccw(pip(legs=LEGS_A)),     # rotated: clinging to a screen edge
    "climb2": rotate_ccw(pip(legs=LEGS_B)),
    "squish": pip("happy", sitting=True),       # used by the example "bounce" move
}


# Optional extras (see CHARACTERS.md): effects float up and vanish, marks stay
# put on the screen and fade, props are objects that sit on the floor.
EFFECTS = {
    "sparkle": up2(["..w..", ".wLw.", "wLLLw", ".wLw.", "..w.."]),
}
MARKS = {
    "drip": up2([".b.", "bbb", ".b."]),
}
PROPS = {
    "pebble": thin(up2([".kkk.", "kbLbk", "kbbBk", ".kkk."])),
}
