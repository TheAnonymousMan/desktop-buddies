"""Echo's sprites. Edit this, then run  python tools/bake_sprites.py
to rebuild sprites.json (the app only reads the json)."""
from buddyart import *

ART = 2       # sprites are drawn at double detail

def battery(level):
    cells = "v" * level + "l" * (5 - level)
    return ["kkkkkkk.", "k" + cells + "kk", "k" + cells + "kk", "kkkkkkk."]


ECHO_COLORS = {
    "k": "#241a2e",  # outline
    "m": "#d4d0e3",  # metal
    "M": "#9e99b5",  # metal shade
    "s": "#1d1633",  # screen
    "S": "#3d0c1f",  # screen, jealous red
    "p": "#ff4fa3",  # pink pixels
    "P": "#ffa3d1",  # light pink
    "r": "#e0245e",  # heart antenna / chest light / jealous eyes
    "j": "#b8336a",  # scarf
    "w": "#ffffff",
    "v": "#ff4fa3",  # glow / charge
    "l": "#2b2140",  # empty battery cell
    "n": "#efedf7",  # metal shine
    "J": "#8a2450",  # scarf shadow
}
ECHO_RAMP = {"m": ("M", "n"), "j": ("J", None)}
# Hand-drawn screen faces, 16 x 8 double-detail pixels ('.' = screen)
ECHO_FACE = {
    "open":    ["................",
                "...pp......pp...",
                "..pPpp....pPpp..",
                "..pppp....pppp..",
                "...pp......pp...",
                "................",
                ".......pp.......",
                "................"],
    "blink":   ["................",
                "................",
                "................",
                "..pppp....pppp..",
                "................",
                "................",
                ".......pp.......",
                "................"],
    "love":    ["................",
                ".pp.pp....pp.pp.",
                ".Ppppp....Ppppp.",
                ".ppppp....ppppp.",
                "..ppp......ppp..",
                "...p........p...",
                "......pppp......",
                "................"],
    "jealous": ["................",
                "..r..........r..",
                "...rr......rr...",
                "..rrrr....rrrr..",
                "..rrrr....rrrr..",
                "................",
                "......rrrr......",
                "................"],
    "heart":   ["....pp....pp....",       # one big heart filling the screen
                "...pPPp..pppp...",
                "...pPpppppppp...",
                "...pppppppppp...",
                "....pppppppp....",
                ".....pppppp.....",
                "......pppp......",
                ".......pp......."],
    "heart_s": ["................",       # ...beating
                ".....pp..pp.....",
                "....pPpppppp....",
                "....pppppppp....",
                ".....pppppp.....",
                "......pppp......",
                ".......pp.......",
                "................"],
    "load1":   ["................",
                "................",
                "................",
                "...PP..pp..pp...",
                "...PP..pp..pp...",
                "................",
                "................",
                "................"],
    "load2":   ["................",
                "................",
                "................",
                "...pp..PP..pp...",
                "...pp..PP..pp...",
                "................",
                "................",
                "................"],
    "load3":   ["................",
                "................",
                "................",
                "...pp..pp..PP...",
                "...pp..pp..PP...",
                "................",
                "................",
                "................"],
    "sleep":   ["................",
                "................",
                "................",
                "................",
                "..PPPP....PPPP..",
                "................",
                ".......PP.......",
                "................"],
}
# Screen-face rows (8 px wide) for each expression
ECHO_SCREENS = {
    "open":    ("ssssssss", "sppsspps", "sppsspps", "ssssssss"),
    "blink":   ("ssssssss", "ssssssss", "sppsspps", "ssssssss"),
    "love":    ("ssssssss", "pspsspsp", "pppssppp", "spssssps"),
    "jealous": ("SSSSSSSS", "SSSSSSSS", "SrrSSrrS", "SSSSSSSS"),
    "sleep":   ("ssssssss", "ssssssss", "sPPssPPs", "ssssssss"),
}


def echo_top(face="open"):
    """Normal-size body with a blank screen (the face is drawn in detail)."""
    a = b = c = d = ("S" if face == "jealous" else "s") * 8
    return [
        "......rr.rr",            # heart antenna
        "......rrrrr",
        ".......rrr",
        "........k",
        "..kkkkkkkkkkkk",         # monitor head
        ".kmmmmmmmmmmmmk",
        ".kmkkkkkkkkkkmk",
        ".kmk" + a + "kmk",
        ".kmk" + b + "kmk",
        ".kmk" + c + "kmk",
        ".kmk" + d + "kmk",
        ".kmkkkkkkkkkkmk",
        ".kMmmmmmmmmmmMk",
        "..kkkkkkkkkkkk",
        "......kmmk",             # neck
        "....kjjjjjjk",           # scarf
        "...kmmjjjjmmk",
        "..kmmmmjjmmmmk",
        ".kmkmmmrrmmmkmk",        # arms + chest light
        ".kkkMMMMMMMMkkk",
    ]


E_LEGS_A = ["....kmk..kmk", "...kkkk..kkkk"]
E_LEGS_B = ["...kmk....kmk", "..kkkk....kkkk"]


def echo_hd(lo, dy, face):
    return detail(lo, ECHO_RAMP, ECHO_FACE[face], (8, 14 + 2 * dy))


def echo_stand(face="open", legs=E_LEGS_A):
    return echo_hd(echo_top(face) + legs, 0, face)


def echo_sit(face="open"):
    return echo_hd(["", ""] + echo_top(face)[:19] + ["..kkkkkkkkkkkk"], 2, face)


PALETTE = ECHO_COLORS
item = battery          # what it eats, at 6 levels of eaten

SPRITES = {
    "stand": echo_stand(),
    "stand_b": echo_stand(),
    "blink": echo_stand("blink"),
    "walk1": echo_stand(legs=E_LEGS_A),
    "walk2": echo_stand(legs=E_LEGS_B),
    "happy": echo_stand("love"),
    "held": echo_stand("love", legs=E_LEGS_B),
    "jealous": echo_stand("jealous"),
    "loaf": echo_sit(),
    "loaf_blink": echo_sit("blink"),
    "sleep": echo_sit("sleep"),
    "sleep_b": echo_sit("sleep"),
    "heart": echo_stand("heart"),
    "heart_s": echo_stand("heart_s"),
    "load1": echo_stand("load1"),
    "load2": echo_stand("load2"),
    "load3": echo_stand("load3"),
    "glitch1": glitchify(echo_stand(), [(14, 4), (15, 4), (16, 4), (17, 4), (18, 2),
                                        (19, 2), (32, -2), (33, -2)],
                         [(24, "n", "P"), (25, "m", "P"), (16, "p", "w"), (17, "p", "w")]),
    "glitch2": glitchify(echo_stand("jealous"), [(10, -2), (11, -2), (18, -4), (19, -4),
                                                 (20, -4), (21, -4), (36, 2), (37, 2)],
                         [(12, "k", "p"), (13, "k", "p"), (34, "m", "M"), (35, "m", "M")]),
}

MARKS = {
    "smear": up2(["pppp..PPP", "..PPPPpp.", "ppp..pppp"]),     # a glitch left on the screen
}
