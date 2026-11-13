"""Nova's sprites. Edit this, then run  python tools/bake_sprites.py
to rebuild sprites.json (the app only reads the json)."""
from buddyart import *

ART = 2       # sprites are drawn at double detail

NOVA_COLORS = {
    "k": "#1f2233",  # outline
    "h": "#a8e0dc",  # silver-teal hair
    "H": "#6fb3b0",  # hair shade
    "s": "#ffe3d1",  # skin
    "S": "#f6b3a3",  # blush
    "c": "#3be3ff",  # cheek circuit lines
    "v": "#3be3ff",  # visor / glow
    "e": "#2f6fa6",  # eyes
    "w": "#ffffff",  # eye shine
    "j": "#5a5fc8",  # hoodie
    "J": "#3f43a0",  # hoodie shade
    "t": "#f2f2f7",  # drawstrings
    "l": "#2b2d42",  # leggings
    "f": "#e8e8f2",  # shoes
    "G": "#2e8b57",  # RAM circuit board
    "C": "#1f2233",  # RAM chips
    "Y": "#e8c24a",  # gold pins
    "A": "#d8f6f3",  # hair shine
    "U": "#7d82e6",  # hoodie light
    "T": "#f5c9b4",  # skin shadow
    "E": "#1d4a7a",  # pupil
    "i": "#7cc0ee",  # iris light
}
NOVA_RAMP = {"h": ("H", "A"), "j": ("J", "U"), "s": ("T", None)}
# Hand-drawn faces, 20 x 8 double-detail pixels over her face ('.' = skin)
NOVA_FACE = {
    "open":  ["......kkkk....kkkk..",
              "......wEEe....wEEe..",
              "......EEEe....EEEe..",
              "......eiie....eiie..",
              "..SS..............SS",
              "..SS..............SS",
              "...........kk.......",
              "...................."],
    "blink": ["....................",
              "....................",
              "......kkkk....kkkk..",
              "....................",
              "..SS..............SS",
              "..SS..............SS",
              "...........kk.......",
              "...................."],
    "happy": ["....................",
              ".......kk......kk...",
              "......k..k....k..k..",
              "....................",
              "..SS..............SS",
              "..SS.....k...k....SS",
              "..........kkk.......",
              "...................."],
    "visor": ["....................",
              ".vvvvvvvvvvvvvvvvvv.",
              ".vwwvvvvvvvvvvvvvvv.",
              ".vvvvvvvvvvvvvvvvvv.",
              "..SS..............SS",
              "..SS..............SS",
              "...........kk.......",
              "...................."],
    "sleep": ["....................",
              "....................",
              "....................",
              "......kkkk....kkkk..",
              "..SS..............SS",
              "..SS..............SS",
              "...........kk.......",
              "...................."],
}
# Inner face rows (x3..x12) for each expression: (row7, row8, row9, row10)
NOVA_FACES = {
    "open":  ("ssskksskks", "ssswesswes", "ssseesseeS", "sSSsssksSs"),
    "blink": ("ssssssssss", "ssskksskks", "sssssssssS", "sSSsssksSs"),
    "happy": ("ssssssssss", "ssskksskks", "sssssssssS", "sSSsskksSs"),
    "visor": ("ssssssssss", "svvvvvvvvs", "sssssssssS", "sSSsssksSs"),
    "sleep": ("ssssssssss", "ssssssssss", "ssskksskkS", "sSSsssksSs"),
}


def nova_top(face="open"):
    """Normal-size head and hoodie with a plain face (drawn later in detail)."""
    r7 = r8 = r9 = r10 = "s" * 10
    return [
        "...." + "k" * 8,
        "...k" + "h" * 8 + "k",
        "..k" + "h" * 10 + "k",
        ".k" + "h" * 12 + "k",
        ".k" + "hH" + "h" * 6 + "vv" + "Hh" + "k",       # glowing hair clip
        ".k" + "hh" + "ss" + "h" + "sss" + "h" + "ss" + "h" + "k",
        ".kh" + "s" * 10 + "hk",
        ".kh" + r7 + "hk",
        ".kh" + r8 + "hk",
        ".kh" + r9 + "hk",
        ".kh" + r10 + "hk",
        "..kh" + "s" * 8 + "hk",
        # oversized hoodie
        "..kjjkssssk" + "jjk",
        ".kjjjjtjjtjjjjk",
        "kjJjjjtjjtjjjJjk",
        "kjJjjjjjvjjjjJjk",
        "kssk" + "jjJJJJjj" + "kssk",
        ".kkkJJJJJJJJkkk",
    ]


N_LEGS_A = ["....klk..klk", "....klk..klk", "....kffk.kffk", "....kkkk.kkkk"]
N_LEGS_B = ["...klk....klk", "...klk....klk", "...kffk...kffk", "...kkkk...kkkk"]


NOVA_HAIR = [
    '...........kkkkkkkkkk...........',
    '.........kkhhhhhhhhhhkk.........',
    '.......khhhAAAhhhhhhhhhhk.......',
    '......khhAAAhhhhhhhhhhhhhk......',
    '.....khhAAhhhhhhhhhhhhhhhhk.....',
    '....khhhhhhhhhhhhhhhhhhhhhhk....',
    '...khhhhhhhhhhhhhhhhhhhhhhhhk...',
    '..khhhhhhhhhhhhhhhhhhhhhhhhhhk..',
    '.khhhhhhhhhhhhhhhhhhhhhvvhhhhhk.',
    'khhhhhhhhhhhhhhhhhhhhhvwvhhhhhhk',
    'khhhhhhHhhhHhhhhhhhhhhhvvhhhhhhk',
    'khhhhhHshhhhhHHhhhhhhhhhhhhhhhhk',
    'khhhhHssHHhhHssHHhhhhHHhhhhhhhhk',
    'khhhhsssssHHsssssHHhHssHHHHHhhhk',
    'khhhHssssssssssssssHsssssssHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHh....................hHhhhk',
    'khhhHk....................kHhhhk',
    'khhhHk....................kHhhhk',
    'khhhHk....................kHhhhk',
    'khhHhk....................khHhhk',
    'khhHk......................kHhhk',
    '.khHk......................kHhk.',
    '.khhk......................khhk.',
    '..kk........................kk..',
]


def nova_hd(lo, dy, face):
    """Double detail with her hand-drawn long hair and face."""
    rows = stamp(detail(lo, NOVA_RAMP), 0, 2 * dy, NOVA_HAIR)
    return stamp(rows, 4, 14 + 2 * dy, NOVA_FACE[face])


def nova_stand(face="open", legs=N_LEGS_A):
    return nova_hd(nova_top() + legs, 0, face)


def nova_sit(face="open", swing=False):
    feet = "...kffk...kffk" if swing else "....kffk.kffk"
    return nova_hd(["", "", ""] + nova_top() + [feet], 3, face)


def ram_stick(level):
    rows = ["kkkkkkkkkk", "kGCGCGCGCk", "kGGGGGGGGk", "kYYYYYYYYk"]
    bite = min(10, level * 2)          # eaten from the end nearest her mouth
    return ["." * bite + r[bite:] for r in rows] if bite < 10 else ["."]


def battery(level):
    cells = "v" * level + "l" * (5 - level)
    return ["kkkkkkk.", "k" + cells + "kk", "k" + cells + "kk", "kkkkkkk."]


PALETTE = NOVA_COLORS
item = ram_stick          # what it eats, at 6 levels of eaten

SPRITES = {
    "stand": nova_stand(),
    "stand_b": nova_stand(),
    "blink": nova_stand("blink"),
    "walk1": nova_stand(legs=N_LEGS_A),
    "walk2": nova_stand(legs=N_LEGS_B),
    "happy": nova_stand("happy"),
    "held": nova_stand(legs=N_LEGS_B),
    "scan": nova_stand("visor"),
    "loaf": nova_sit(),
    "loaf_b": nova_sit(swing=True),
    "loaf_blink": nova_sit("blink"),
    "sleep": nova_sit("sleep"),
    "sleep_b": nova_sit("sleep"),
}
SPRITES["stand_b"] = SPRITES["stand"]
SPRITES["dance1"] = nova_stand("happy", legs=N_LEGS_B)
SPRITES["dance2"] = nova_stand("open", legs=N_LEGS_A)

EFFECTS = {
    "spark": up2(["..v..", ".vwv.", "vwwwv", ".vwv.", "..v.."]),
}
