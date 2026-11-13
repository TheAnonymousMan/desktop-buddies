"""
Desktop buddies engine - tiny pixel-art companions that live on your desktop.

Characters live in characters/<name>/ and are loaded at start-up:
  character.json  name, size, settings and everything they say
  sprites.json    their art (rebuilt from source.py by tools/bake_sprites.py)
  behaviours.py   optional: their own moves, scenes with friends and powers
See CHARACTERS.md for how to make or share one.

Run desktop_buddy.pyw to start (double-click it). Needs Python 3 with tkinter.

Controls
  Left-click ......... pet (hearts!) / wake up from a nap
  Drag ............... pick up; let go to drop or throw (shake for dizziness)
  Double-click ....... feed
  Right-click ........ menu (feed, come here, nap, add a buddy, send home, quit)

Buddies roam across all your monitors, climb up to stacked screens, chat and play
with each other, and move out of the way of fullscreen apps.
"""
import ctypes
import importlib.util
import sys
import types
from ctypes import wintypes
import json
import os
import math
import random
import threading
import time
import urllib.request
import tkinter as tk
from pathlib import Path

KEY = "#ff00fe"      # window color that Windows renders as fully transparent
TICK_MS = 50         # 20 updates per second
BREAK_EVERY = 45 * 60 * 1000 // TICK_MS   # break reminder every 45 minutes
HERE = Path(__file__).resolve().parent
SETTINGS = HERE / "buddy_settings.json"
OLD_SETTINGS = HERE / "pet_settings.json"      # name from before the rename
CHARACTERS_DIR = HERE / "characters"

FX_COLORS = {"k": "#2b1d14", "r": "#e2445c", "z": "#7fb3ff",
             "n": "#b56cff", "s": "#9a8f88", "y": "#ffd84a"}
HEART = [".kk.kk.", "krrkrrk", "krrrrrk", ".krrrk.", "..krk..", "...k..."]
ZED = ["zzzzz", "...z.", "..z..", ".z...", "zzzzz"]
NOTE = ["..nn.", "..n.n", "..n..", "nnn..", "nnn.."]
IDEA = [".kkk.", "kyyyk", "kyyyk", "kyyyk", ".kyk.", ".kkk.", ".kkk."]
STAR = ["..y..", ".yyy.", "yyyyy", ".yyy.", ".y.y."]
SCRATCH = ["s..s..s..", ".s..s..s.", ".s..s..s.", "..s..s..s", "..s..s..s"]


def pad(r, w):
    assert len(r) <= w, r
    return r.ljust(w, ".")


SMOOTH = False    # smooth diagonal edges on normal-detail art (buddies now use double detail)


def smooth_corners(grid, scale):
    """Find the corners to round off when a pixel grid is drawn `scale` times
    bigger. Each art pixel is split into scale x scale screen pixels, and a
    corner of it takes its neighbours' color when both of the neighbours
    touching that corner match (an EPX-style rule, which keeps one-pixel
    details like eyes intact). Stair-step outlines become smooth slopes."""
    h, w = len(grid), len(grid[0])
    cut = scale // 2
    if cut < 1:
        return []
    out = []
    at = lambda x, y: grid[y][x] if 0 <= x < w and 0 <= y < h else KEY
    for y in range(h):
        for x in range(w):
            c = grid[y][x]
            up, down, left, right = at(x, y - 1), at(x, y + 1), at(x - 1, y), at(x + 1, y)
            for vert, horiz, other_v, other_h, cx, cy in (
                    (up, left, down, right, 0, 0), (up, right, down, left, 1, 0),
                    (down, left, up, right, 0, 1), (down, right, up, left, 1, 1)):
                if vert == horiz != c and vert != other_v and horiz != other_h:
                    out.append((x, y, cx, cy, vert, c))
    return out


def blend(a, b):
    """Mix two #rrggbb colors half and half."""
    return "#" + "".join("%02x" % ((int(a[i:i + 2], 16) + int(b[i:i + 2], 16)) // 2)
                         for i in (1, 3, 5))


def make_image(rows, scale, palette, mirror=False, art=1):
    """Turn sprite rows into a PhotoImage `scale` screen pixels per art pixel.
    art=2 means the rows are drawn at double detail, so each of their pixels
    covers half as much screen and the sprite comes out the same size."""
    w = max(len(r) for r in rows)
    grid = []
    for r in rows:
        r = pad(r, w)
        if mirror:
            r = r[::-1]
        grid.append([palette.get(ch, KEY) for ch in r])
    img = tk.PhotoImage(width=w, height=len(rows))
    img.put(" ".join("{" + " ".join(r) + "}" for r in grid))
    if art == 2:                     # hand-detailed art: no corner smoothing
        if scale % 2 == 0:
            return img.zoom(scale // 2, scale // 2)
        return img.zoom(scale, scale).subsample(2, 2)
    img = img.zoom(scale, scale)
    if SMOOTH:
        cut = scale // 2
        for x, y, cx, cy, color, under in smooth_corners(grid, scale):
            # where two solid colors meet, the slope's edge pixels get a
            # half-and-half blend so it looks smooth instead of jagged
            soft = blend(color, under) if KEY not in (color, under) else None
            for j in range(cut):                 # a small triangle in that corner
                n = cut - j
                py = y * scale + (j if cy == 0 else scale - 1 - j)
                px = x * scale + (0 if cx == 0 else scale - n)
                img.put(color, to=(px, py, px + n, py + 1))
                if soft:
                    ex = px + n if cx == 0 else px - 1   # just past the triangle's slope
                    img.put(soft, to=(ex, py, ex + 1, py + 1))
    return img


SHAKE_MIN = 4             # direction flips (within a second) before it counts as shaking
GLOW = ["..vvvv..", ".vvvvvv."]

# How a buddy feels about another, from "relationships" in its character.json
# (one-way: A can love B while B just sees A as a friend). Anyone not listed
# is a friend.
RELATIONS = ("loves", "bestie", "friend", "dislikes")
SEEK = {"loves": 3.0, "bestie": 3.0, "friend": 1.0, "dislikes": 0.25}   # how much they seek each other out
COMES_OVER = ("loves", "bestie")      # will walk across the screen to start a scene

# When BOTH sides are known, the pair has a bond with its own behaviour:
#   couple      both love each other: dates, holding hands, strolls together
#   besties     both bestie: hang out and play the most
#   crush       one loves, the other doesn't: pining, maybe a confession
#   heartbreak  one loves, the other dislikes them: confession gets turned down
#   rivals      both dislike each other: staredowns and races
#   clingy      thinks they're besties, but the other dislikes them: tags along
#   eager       thinks they're besties, the other just sees a friend: "besties, right?"
# ...and the other side of each one-way feeling:
#   admired     someone you like as a friend / bestie has a crush on you
#   pestered    someone you dislike keeps coming round (clingy or in love with you)
#   casual      someone thinks you're besties; to you they're a friend
BOND_SEEK = {"couple": 5.0, "besties": 4.0, "crush": 3.0, "heartbreak": 2.0, "rivals": 1.0,
             "clingy": 3.0, "eager": 2.5, "admired": 1.2, "pestered": 0.15, "casual": 1.0}
BOND_COMES_OVER = ("couple", "besties", "crush", "heartbreak", "rivals", "clingy", "eager")

# Lines for the built-in bond scenes, used when a character has none of its own
# (a character can override any of them, or add "<key>_<bond>" versions).
DEFAULT_LINES = {
    "date": ["*takes {other}'s hand*", "Hi, {other}... *blushes*", "Walk with me, {other}?"],
    "date_back": ["*holds hands with {other}*", "Hi you \u2665", "Always, {other}."],
    "date_end": ["Best walk ever \u2665", "Same time tomorrow, {other}?", "*leans on {other}*"],
    "race": ["Race you to the edge, {other}!", "Loser's a rotten egg!", "First one there wins!"],
    "race_win": ["Ha! Too slow, {other}!", "Winner! Obviously.", "Eat my dust!"],
    "race_lose": ["Rematch. Now.", "You cheated, {other}!", "I let you win..."],
    "staredown": ["*glares at {other}*", "What are YOU looking at?", "Hmph."],
    "pine": ["*sighs dreamily at {other}*", "{other} is so... *sigh*", "*stares at {other}* ...huh? Nothing!"],
    "confess": ["{other}... I really like you. Like, LIKE like.", "*nervously* {other}, will you be mine?"],
    "friendzone": ["Aww, {other}! You're my favorite... friend!", "That's so sweet! Friends forever?"],
    "reject": ["Ew, no.", "Not happening, {other}.", "In your dreams."],
    "heartbroken": ["*heart cracks*", "...It's fine. I'm fine.", "*sniff*"],
    "tagalong": ["{other}! Bestie! Whatcha doing?", "Hey bestie! Let's hang out!", "{other}!! There you are!"],
    "brush_off": ["Ugh. Not you again.", "I'm busy, {other}.", "Oh no. Not now."],
    "tagalong_follow": ["Wait up, {other}!", "Hey, wait for me!", "Bestie, where are you going?"],
    "groan": ["*groans* Fine. Five minutes.", "Why are you like this, {other}?", "*sigh* ...Hi."],
    "tagalong_end": ["Best friends forever!", "This is the best day ever!", "I knew you'd say hi ♥"],
    "bestie_ask": ["We're besties, right {other}?", "Bestie! ...We ARE besties, right?",
                   "I told everyone we're best friends, {other}!"],
    "bestie_dodge": ["Haha... you're a great friend, {other}!", "Uh... sure, buddy!",
                     "Let's just say we're good friends!"],
    "bestie_hopeful": ["Close enough! Besties!", "I'll take it! *happy wiggle*", "Someday, {other}. Someday."],
}


# ============================================================== characters ==
def load_characters(folder=None):
    """Load every characters/<name>/ folder: character.json + sprites.json, and
    behaviours.py if there is one. A broken character is skipped, not fatal."""
    folder = Path(folder or CHARACTERS_DIR)
    found = {}
    for d in sorted(p for p in folder.iterdir() if p.is_dir()) if folder.exists() else []:
        try:
            ch = json.loads((d / "character.json").read_text(encoding="utf-8"))
            art = json.loads((d / "sprites.json").read_text(encoding="utf-8"))
            ch.update(palette=art["palette"], sprites=art["sprites"],
                      items=art["items"], art=art.get("art", 1),
                      effects=art.get("effects", {}),     # float up and vanish (like hearts)
                      marks=art.get("marks", {}),         # stay put on the screen, then fade
                      props=art.get("props", {}))         # objects that sit on the floor
            ch.setdefault("extra_states", [])
            ch["folder"] = d
            ch["behaviour"] = load_behaviour(d) if (d / "behaviours.py").exists() else None
            found[ch["name"]] = ch
        except Exception as e:             # keep going without it
            print(f"skipped character {d.name}: {e}", file=sys.stderr)
    return found


def load_behaviour(d):
    """Import characters/<name>/behaviours.py as part of a little package, so it
    can import its own helper files (from .fact_search import ...)."""
    pkg_name = "pet_character_" + d.name
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(d)]
    sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(pkg_name + ".behaviours", d / "behaviours.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CHARACTERS = load_characters()


class World:
    """What a behaviour's tick() gets: the floor height, the walkable range on
    this screen, and whether the buddy is busy with a scene or leaving."""
    def __init__(self, ground, lo, hi, busy, rect):
        self.ground, self.lo, self.hi, self.busy, self.rect = ground, lo, hi, busy, rect


MAX_BUDDIES = 8

def work_area(root):
    """Desktop area excluding the taskbar: (left, top, right, bottom)."""
    try:
        class RECT(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                        ("r", ctypes.c_long), ("b", ctypes.c_long)]
        rc = RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rc), 0):
            return rc.l, rc.t, rc.r, rc.b
    except Exception:
        pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - 48


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


def monitors(root):
    """Work area (l, t, r, b) of every monitor, taskbars excluded."""
    found = []
    try:
        user32 = ctypes.WinDLL("user32")
        user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
        proc_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                    ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
        user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p,
                                               proc_t, wintypes.LPARAM]

        def callback(hmon, hdc, rect, data):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
                w = info.rcWork
                dpi_x, dpi_y = wintypes.UINT(96), wintypes.UINT(96)
                try:
                    ctypes.windll.shcore.GetDpiForMonitor(
                        wintypes.HMONITOR(hmon), 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
                except Exception:
                    pass
                found.append(((w.left, w.top, w.right, w.bottom), dpi_x.value or 96))
            return True

        user32.EnumDisplayMonitors(None, None, proc_t(callback), 0)
    except Exception:
        pass
    return sorted(set(found)) or [(work_area(root), 96)]


OURS = object()   # "the foreground window is one of ours": keep the previous answer


def fullscreen_monitor():
    """Work area of the monitor covered by a fullscreen foreground window (a game,
    a video, an F11 browser), None if there is none, or OURS if the foreground
    window belongs to this app (e.g. our right-click menu)."""
    try:
        user32 = ctypes.WinDLL("user32")
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.MonitorFromWindow.restype = wintypes.HMONITOR
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
        user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.IsZoomed.argtypes = [wintypes.HWND]
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid():
            return OURS
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        if cls.value in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
            return None                       # the desktop / taskbar
        if user32.IsZoomed(hwnd):
            return None                       # maximized isn't fullscreen
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, 2), ctypes.byref(info)):
            return None
        m = info.rcMonitor
        if r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom:
            w = info.rcWork
            return (w.left, w.top, w.right, w.bottom)
    except Exception:
        pass
    return None


def enable_dpi_awareness():
    """Use real pixel coordinates on every monitor. Without this, Windows fakes
    coordinates on scaled displays and side-by-side screens don't line up."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # per-monitor v2
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def load_settings():
    try:
        if not SETTINGS.exists() and OLD_SETTINGS.exists():
            return json.loads(OLD_SETTINGS.read_text())
        return json.loads(SETTINGS.read_text())
    except Exception:
        return {}


def save_settings(data):
    try:
        SETTINGS.write_text(json.dumps(data))
    except Exception:
        pass


# ================================================================== buddy ==
class Buddy:
    def __init__(self, app, kind, name):
        self.app, self.kind, self.name = app, kind, name
        self.ch = ch = CHARACTERS[kind]
        self.lines = ch["lines"]

        self.win = win = tk.Toplevel(app.root)
        win.title(name)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", KEY)
        win.config(bg=KEY)

        first = next(iter(ch["sprites"].values()))
        art = ch.get("art", 1)
        self.spr_w = -(-max(len(r) for r in first) // art)
        self.spr_h = -(-len(first) // art)
        self.canvas = c = tk.Canvas(win, bg=KEY, highlightthickness=0, bd=0)
        self.scale = 0
        self.apply_scale(app.scale_for(kind, app.pointer_monitor()))
        c.pack()
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Double-Button-1>", lambda e: self.feed())
        c.bind("<Button-3>", self.on_menu)

        l, t, r, b = app.pointer_monitor()
        self.x = random.randint(l + 20, max(l + 21, r - self.sw - 20))
        self.y = t - self.sh
        self.vx = self.vy = 0.0
        self.facing = random.choice((1, -1))
        self.state, self.timer, self.state_len = "fall", 0, 1
        self.tick = random.randint(0, 1000)      # so buddies don't blink in sync
        self.energy = random.uniform(70, 95)
        self.hunger = random.uniform(10, 35)
        self.effects, self.bubble, self.drag = [], None, None
        self.greeted = False
        self.dropped = True       # True when dropped/thrown (not a small step down)
        self.social = None        # current Interaction, if any
        self.target = None        # Buddy being chased / fled from
        self.goto_x = 0.0
        self.climb = None         # active climb: wall x, side, destination, top
        self.pending_climb = None # climb to start once we've walked to the wall
        self.social_cd = 120      # ticks before this buddy can start a new interaction
        self.bump_cd = 0
        self.glitch_t = 0         # >0: screen glitch (buddies with glitch1/glitch2 sprites)
        self.last_attention = 0   # app tick when you last petted/fed/held this buddy
        self.watch_x = None       # where to stand and watch while you're fullscreen
        self.watch_face = 1
        self.pending_watch = False
        self.on_arrive = None     # what to do after a walk_to() (set by behaviours)
        self.shake = 0            # how hard you've been shaking this buddy
        self.pending_dizzy = 0    # dizzy ticks to start when it lands
        self.flee_to = None       # monitor to run to when fullscreen covers ours
        self.leaving = False
        self._geo = None
        self.bhv = ch.get("behaviour")       # this character's behaviours.py, if any
        self.mem = {}                        # behaviours keep their own notes here
        self.hook("setup")

    # -------------------------------------------------------- behaviours --
    def hook(self, name, *args, **kw):
        """Call behaviours.<name>(self, ...) if this character has it."""
        fn = getattr(self.bhv, name, None)
        return fn(self, *args, **kw) if fn else None

    def custom_state(self, st=None):
        """The behaviours.STATES entry for a state, if this character has one."""
        return (getattr(self.bhv, "STATES", None) or {}).get(st or self.state)

    def start_scene(self, kind, other):
        """Start an Interaction (one of ours from behaviours.INTERACTIONS, or a
        built-in one) with another buddy."""
        self.app.interactions.append(Interaction(self.app, kind, self, other))

    def walk_to(self, x, then=None, speed=None):
        """Walk to x on this screen; then call then(buddy) on arrival.
        speed: pixels per frame (a normal walk is 2.4; 4-6 is a run)."""
        self.goto_x = x
        self.set_state("goto", 300)
        self.on_arrive = then
        self.goto_speed = speed or 2.4

    def pointer(self):
        return self.app.root.winfo_pointerxy()

    def blinking(self):
        return (self.tick % 73) < 3

    def walk_frame(self, fast=False):
        return "walk1" if (self.tick // (3 if fast else 5)) % 2 == 0 else "walk2"

    def hop(self, height, period):
        """A bounce for drawing: up to `height` art pixels, one bounce every
        `period` frames, in screen pixels."""
        return abs(math.sin(self.tick * math.pi / period)) * height * self.scale

    def lift(self):
        """How far above its real position the buddy is drawn right now, so it
        bounces along without changing where it actually is. A move in
        behaviours.STATES sets it with "bob": a height, or a function(buddy)."""
        spec = self.custom_state()
        if spec and "bob" in spec:
            b = spec["bob"]
            return b(self) if callable(b) else self.hop(b, 6)
        st = self.state
        if st in ("chase", "flee", "race") or (st == "goto" and getattr(self, "goto_speed", 2.4) > 3):
            return self.hop(1.5, 6)                 # a bouncy trot when running
        if st in ("walk", "goto"):
            return self.hop(0.5, 10)                # a gentle bob when walking
        return 0

    # ----------------------------------------------------------- helpers --
    def cx(self):
        return self.x + self.sw / 2

    def apply_scale(self, s):
        """Resize the buddy (e.g. when it moves to a screen with different scaling),
        keeping its feet in the same place."""
        if s == self.scale:
            return
        feet = (self.cx(), self.y + self.sh) if self.scale else None
        self.scale = s
        f = s / self.ch["scale"]
        self.gfx = self.app.graphics(self.kind, s)
        self.sw, self.sh = self.spr_w * s, self.spr_h * s
        self.padx = max(12 * s, (int(260 * f) - self.sw) // 2)   # room for long bubbles
        self.padtop = int(self.ch.get("bubble_room", 64) * f)
        self.padbot = int(10 * f)
        self.W = self.sw + 2 * self.padx
        self.H = self.padtop + self.sh + self.padbot
        self.canvas.config(width=self.W, height=self.H)
        self._geo = None
        if feet:
            self.x, self.y = feet[0] - self.sw / 2, feet[1] - self.sh
            if self.drag:
                self.drag["ox"], self.drag["oy"] = self.sw / 2, self.sh / 2

    def floor(self):
        """Work area of the monitor this buddy is standing on (or falling into)."""
        return self.app.floor_at(self.cx(), self.y + self.sh)

    def limits(self, rect):
        """Left/right limits for x. A side that touches another monitor is open."""
        l, t, r, b = rect
        lo = -1e9 if self.app.neighbour(rect, -1) else l
        hi = 1e9 if self.app.neighbour(rect, 1) else r - self.sw
        return lo, hi

    def start_climb(self, route):
        """route = (wall_x, side, dest_rect, top_y, step_over)."""
        wall, side, dest, top, step = route
        self.drop_social()
        self.pending_climb = None
        self.climb = {"wall": wall, "side": side, "dest": dest, "top": top, "step": step}
        self.facing = side
        self.set_state("climb", 99999)
        self.say("climb", 50)

    def walk_to_climb(self, route):
        wall, side = route[0], route[1]
        self.pending_climb = route
        self.goto_x = wall - self.sw if side > 0 else wall
        self.set_state("goto", 600)

    def flee_fullscreen(self, dest):
        """Dash toward the screen edge, then pop over to `dest`."""
        self.drop_social()
        self.climb = self.pending_climb = None
        self.hook("on_event", "fs_flee")
        self.flee_to = dest
        self.facing = 1 if (dest[0] + dest[2]) / 2 > self.cx() else -1
        self.set_state("fs_flee", 14)
        self.say("fs_flee", 60)

    def face(self, other):
        self.facing = 1 if other.cx() > self.cx() else -1

    def set_state(self, state, ticks):
        self.state, self.timer, self.state_len = state, ticks, max(1, ticks)
        if state != "goto":
            self.on_arrive = None        # an interrupted walk_to() doesn't resume later
            self.goto_speed = 2.4

    def relation(self, other):
        """How this buddy feels about another: "loves", "bestie", "friend"
        (the default) or "dislikes"."""
        kind = getattr(other, "kind", None)
        if kind is None:
            return None
        rels = self.ch.get("relationships") or {}
        rel = rels.get(kind, rels.get("*"))      # "*" = everyone not listed by name
        if rel is None and kind in self.ch.get("besties", []):      # older shorthand
            rel = "bestie"
        return rel if rel in RELATIONS else "friend"

    def is_bestie(self, other):
        return self.relation(other) == "bestie"

    def bond(self, other):
        """The two-way bond with another buddy, or None for anything ordinary:
        couple, besties, crush, heartbreak or rivals."""
        if not hasattr(other, "relation"):
            return None
        mine, theirs = self.relation(other), other.relation(self)
        if mine == "loves":
            return "couple" if theirs == "loves" else "heartbreak" if theirs == "dislikes" else "crush"
        if mine == "bestie" and theirs == "bestie":
            return "besties"
        if theirs == "loves":                    # they love me; I don't love them back
            return "pestered" if mine == "dislikes" else "admired"
        if mine == "dislikes" and theirs == "dislikes":
            return "rivals"
        if mine == "bestie":
            return {"bestie": "besties", "dislikes": "clingy", "friend": "eager"}[theirs]
        if theirs == "bestie":
            return "pestered" if mine == "dislikes" else "casual"
        return None                              # friends, or a one-way dislike

    def affinity(self, other):
        """How much this buddy seeks the other out."""
        return BOND_SEEK.get(self.bond(other)) or SEEK[self.relation(other)]

    def say(self, key, ticks=60, other=None):
        # talking to someone it loves / its bestie / someone it dislikes:
        # use the "<key>_<relationship>" lines if there are any
        # "<key>_<bond>" first (e.g. hello_couple), then "<key>_<relationship>"
        bond, rel = self.bond(other), self.relation(other)
        for k in ([f"{key}_{bond}"] if bond else []) + ([f"{key}_{rel}"] if rel and rel != "friend" else []):
            if k in self.lines:
                key = k
                break
        options = self.lines.get(key) or DEFAULT_LINES.get(key)
        text = random.choice(options) if options else key
        if other is not None:
            text = text.replace("{other}", other.name)
        text = (text.replace("{time}", time.strftime("%H:%M"))
                    .replace("{mins}", str(max(1, self.app.tick * TICK_MS // 60000))))
        self.bubble = [text, ticks]

    def head_pos(self):
        hx, hy, hy_sit = self.ch["head"]
        s = self.scale
        x = hx if self.facing > 0 else self.spr_w - hx
        y = hy_sit if self.state in ("loaf", "sleep", "eat") else hy
        return self.padx + x * s, self.padtop + y * s

    def spawn(self, kind, n=1):
        """Float an effect up from the buddy's head: one of its own (sprites.json
        "effects"), or a built-in one: heart, zed, note, idea, star."""
        hx, hy = self.head_pos()
        if kind in self.gfx["marks"] or kind == "scratch":      # (older behaviours)
            self.leave_mark(kind)
            return
        img = self.gfx["effects"].get(kind) or getattr(self.app, kind, None)
        if img is None:
            return
        for _ in range(n):
            self.effects.append({
                "img": img,
                "x": hx + random.uniform(-12, 12), "y": hy - 6,
                "vy": random.uniform(-1.6, -1.0),
                "vx": (0.6 * self.facing) if kind == "zed" else 0.0,
                "phase": random.uniform(0, 6.28), "life": 34,
            })

    def leave_mark(self, kind, x=None, y=None, life=90):
        """Leave a mark that stays put on the screen and fades (sprites.json
        "marks"). Default spot: just in front of the buddy, at body height."""
        img = self.gfx["marks"].get(kind) or (self.app.scratch if kind == "scratch" else None)
        if img is None:
            return
        s = self.scale
        if x is None:
            x = self.x + (self.sw + 3 * s if self.facing > 0 else -3 * s) + random.uniform(-6, 6)
        if y is None:
            y = self.y + random.uniform(-4, 4 * s)
        self.app.leave_mark(img, x, y, life)

    def drop_prop(self, kind, x=None, y=None, vx=0.0, vy=0.0, life=3600):
        """Put one of this character's props (sprites.json "props") into the
        world, centred on x / bottom at y (default: at its feet). Returns it."""
        img = self.gfx["props"].get(kind)
        if img is None:
            return None
        if x is None:
            x = self.cx() + self.facing * self.sw * 0.4
        if y is None:
            y = self.y + self.sh
        return self.app.add_prop(Prop(self.app, kind, img, self, x, y, vx, vy, life))

    def mouth(self):
        """Screen position just in front of the head (where things are carried)."""
        hx, hy = self.head_pos()
        return (self.x - self.padx + hx + self.facing * self.scale * 3,
                self.y - self.padtop + hy + self.scale * 5)

    def on_ground(self):
        return self.state not in ("fall", "held") and not self.leaving

    def is_free(self):
        return (self.on_ground() and self.social is None and self.social_cd <= 0
                and self.state in ("idle", "walk", "loaf", "goto"))

    def drop_social(self):
        if self.social:
            self.social.end()

    # ----------------------------------------------------------- actions --
    def pet(self):
        if not self.on_ground():
            return
        if self.state == "climb":
            self.spawn("heart", 2)
            self.say("pet")
            return
        was_sleeping = self.state == "sleep"
        self.drop_social()
        if was_sleeping:
            self.set_state("idle", 40)
            self.say("wake")
            return
        # behaviours.on_pet can change the reaction: {"line", "hearts", "happy", "ticks"}
        r = self.hook("on_pet") or {}
        self.set_state("happy", r.get("happy", 36))
        self.spawn("heart", r.get("hearts", 3))
        self.say(r.get("line", "pet"), r.get("ticks", 60))
        self.app.notice_attention(self)

    def feed(self):
        if not self.on_ground() or not self.ch.get("needs_food", True):
            return
        if self.hunger < 15:
            self.say("full")
            return
        self.drop_social()
        self.set_state("eat", 90)
        self.say("eat", 80)
        self.app.notice_attention(self)

    def come_here(self):
        if not self.on_ground():
            return
        self.drop_social()
        self.target = None
        self.last_attention = self.app.tick
        px, py = self.app.root.winfo_pointerxy()
        dest = self.app.floor_at(px, py)
        if dest == self.app.fullscreen:     # you're fullscreen there: stay out of the way
            self.say("I'll watch from here!", 50)
            return
        if dest != self.floor():            # different screen: drop in from its top
            self.x, self.y = px - self.sw / 2, dest[1] - self.sh
            self.vx = self.vy = 0
            self.dropped = True
            self.set_state("fall", 0)
        else:
            self.set_state("chase", 240)
        self.say("come")

    def nap(self):
        if self.on_ground():
            self.drop_social()
            self.set_state("sleep", 160)
            self.say("sleepy")

    def stats(self):
        low_e, hungry, happy = self.lines["moods"]
        mood = low_e if self.energy < 30 else hungry if self.hunger > 70 else happy
        if self.ch.get("needs_food", True):
            self.say(f"{mood}  ·  energy {int(self.energy)}%  ·  hunger {int(self.hunger)}%", 90)
        else:
            self.say(f"{mood}  ·  energy {int(self.energy)}%", 90)

    def leave(self, then=None):
        """Say bye, then close this buddy's window."""
        self.drop_social()
        self.say("bye", 30)
        self.set_state("happy", 999)
        self.spawn("heart", 4)
        self.leaving = True
        self.win.after(1100, then or (lambda: self.app.remove_buddy(self)))

    # ------------------------------------------------------------- mouse --
    def on_press(self, e):
        self.drag = {"ox": e.x_root - self.x, "oy": e.y_root - self.y,
                     "sx": e.x_root, "sy": e.y_root,
                     "lx": e.x_root, "ly": e.y_root,
                     "vx": 0.0, "vy": 0.0, "moved": False,
                     "dirx": 0, "diry": 0, "flips": []}
        self.shake = 0

    def on_drag(self, e):
        d = self.drag
        if not d or self.leaving:
            return
        if not d["moved"] and abs(e.x_root - d["sx"]) + abs(e.y_root - d["sy"]) > 4:
            d["moved"] = True
            self.drop_social()
            self.climb = self.pending_climb = None
            self.last_attention = self.app.tick
            self.set_state("held", 0)
            self.say("held", 40)
        if d["moved"]:
            self.check_shake(d, e.x_root - d["lx"], e.y_root - d["ly"])
            self.x, self.y = e.x_root - d["ox"], e.y_root - d["oy"]
            d["vx"] = 0.5 * d["vx"] + 0.5 * (e.x_root - d["lx"])
            d["vy"] = 0.5 * d["vy"] + 0.5 * (e.y_root - d["ly"])
            d["lx"], d["ly"] = e.x_root, e.y_root
            if abs(d["vx"]) > 1:
                self.facing = 1 if d["vx"] > 0 else -1

    def check_shake(self, d, dx, dy):
        """Count quick back-and-forth moves (side to side or up and down)."""
        now = time.monotonic()
        for axis, delta in (("dirx", dx), ("diry", dy)):
            if abs(delta) < 6:
                continue
            way = 1 if delta > 0 else -1
            if d[axis] and way != d[axis]:
                d["flips"].append(now)
            d[axis] = way
        d["flips"] = [t for t in d["flips"] if now - t < 1.0]
        if len(d["flips"]) >= SHAKE_MIN and d["flips"][-1] == now:
            self.shake += 1
            if self.shake == 1 or self.shake % 10 == 0:
                self.say("shaking", 45)
            if self.shake % 3 == 0:
                self.spawn("star")

    def on_release(self, e):
        d, self.drag = self.drag, None
        if d and d["moved"]:
            if self.shake >= 1:
                self.pending_dizzy = min(260, 70 + self.shake * 10)
            self.shake = 0
            self.dropped = True
            self.vx = max(-30, min(30, d["vx"] * 1.5))
            self.vy = max(-30, min(30, d["vy"] * 1.5))
            self.set_state("fall", 0)
        else:
            self.pet()

    def on_menu(self, e):
        m = self.app.build_menu(self)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    # ------------------------------------------------------------- brain --
    def choose_next(self):
        if self.energy < 20:
            self.say("sleepy")
            self.set_state("sleep", 200)
            return
        if self.hunger > 75 and random.random() < 0.5:
            self.say("hungry")
            self.set_state("idle", 60)
            return
        px = self.app.root.winfo_pointerx()
        others = [p for p in self.app.buddies if p is not self and not p.leaving
                  and p.floor() == self.floor()]
        rect = self.floor()
        climbs = self.app.climb_routes(rect, self)
        below = self.app.screen_below(rect, self.cx())
        options = [("walk", 40), ("idle", 20), ("loaf", 20),
                   ("chase", 6 if abs(px - self.x) < 900 else 0),
                   ("visit", 18 if others else 0),
                   ("climb", 7 if climbs else 0),
                   ("drop", 5 if below else 0),
                   ("sleep", 10 if self.energy < 60 else 0)] + [tuple(o) for o in self.ch["extra_states"]]
        custom = getattr(self.bhv, "STATES", None) or {}
        options += [(name, st.get("weight", 0)) for name, st in custom.items() if st.get("start")]
        pick = random.choices([o for o, _ in options], [w for _, w in options])[0]
        if pick in custom:
            custom[pick]["start"](self)
            return
        if pick == "walk":
            if random.random() < 0.6:
                self.facing = -self.facing
            self.set_state("walk", random.randint(40, 150))
        elif pick == "idle":
            self.set_state("idle", random.randint(40, 100))
        elif pick == "loaf":
            self.set_state("loaf", random.randint(80, 180))
        elif pick == "chase":
            self.target = None
            self.set_state("chase", 160)
        elif pick == "visit":
            friend = random.choices(others, [self.affinity(p) for p in others])[0]
            self.goto_x = friend.cx() + random.choice((-1, 1)) * 90 - self.sw / 2
            self.set_state("goto", 250)
        elif pick == "climb":
            self.walk_to_climb(random.choice(climbs))
        elif pick == "drop":
            self.say("drop", 40)
            self.y = rect[3] - self.sh + 4          # step through the floor
            self.vx, self.vy = 0, 2
            self.dropped = False
            self.set_state("fall", 0)
        else:
            self.say("sleepy")
            self.set_state("sleep", 200)

    def update(self):
        self.tick += 1
        self.social_cd -= 1
        self.bump_cd -= 1
        self.glitch_t -= 1
        self.apply_scale(self.app.scale_for(self.kind, self.floor()))
        rect = self.floor()
        l, t, r, b = rect
        ground = b - self.sh
        st = self.state
        self.timer -= 1
        if st != "sleep":
            self.energy = max(0.0, self.energy - 0.012)
        if self.ch.get("needs_food", True):
            self.hunger = min(100.0, self.hunger + 0.007)
        else:
            self.hunger = 0.0

        if st == "held":
            return

        if st == "climb" and self.climb:
            c = self.climb
            self.facing = c["side"]
            self.x = c["wall"] - self.sw if c["side"] > 0 else c["wall"]
            self.y -= self.ch.get("climb_speed", 2)
            if self.y + self.sh <= c["top"]:
                self.y = c["top"] - self.sh
                if c["step"]:                      # step over onto the next screen
                    self.x += c["side"] * (self.sw * 0.6 + 4)
                self.climb = None
                self.set_state("idle", 50)
                self.say("made_it", 50)
            return

        if st == "fall":
            self.vy += 1.1
            self.x += self.vx
            self.y += self.vy
            vl, vt, vr, vb = self.app.virtual     # bounce off the outer edges
            if self.x < vl:
                self.x, self.vx = vl, -self.vx * 0.5
            elif self.x > vr - self.sw:
                self.x, self.vx = vr - self.sw, -self.vx * 0.5
            if self.y < vt - self.sh:
                self.y, self.vy = vt - self.sh, 0
            if self.y >= ground:
                self.y = ground
                if self.vy > 9:
                    self.vy, self.vx = -self.vy * 0.35, self.vx * 0.6
                else:
                    self.land()
            return

        # --- grounded states ---
        spec = self.custom_state(st) or {}
        floats = spec.get("floats")
        if not floats and self.y < ground - 2:     # walked onto a lower screen
            self.drop_social()
            self.vx, self.vy = 2 * self.facing, 0
            self.set_state("fall", 0)
            return
        if not floats and self.y > ground + 2:     # stepped onto a higher one
            self.drop_social()
            self.y = ground
            self.vx, self.vy = 2 * self.facing, -6
            self.set_state("fall", 0)
            return
        if not floats:
            self.y = ground
        lo, hi = self.limits(rect)
        self.x = max(lo, min(hi, self.x))
        busy = self.social is not None or self.leaving
        if self.watch_x is not None and not busy and st in ("idle", "walk", "loaf", "happy") \
                and self.floor() != self.app.fullscreen:
            self.goto_x = self.watch_x
            self.pending_watch = True
            self.pending_climb = None
            self.set_state("goto", 600)
            return
        # behaviours.on_tick may take over this tick (return True)
        if self.hook("on_tick", World(ground, lo, hi, busy, rect)):
            return
        if spec.get("tick"):
            spec["tick"](self, World(ground, lo, hi, busy, rect))

        if st == "walk":
            self.x += 2 * self.facing
            if self.x <= lo or self.x >= hi:
                # a screen edge with a tall step beside it: maybe climb it
                route = self.app.step_route(rect, self.facing, self)
                if route and not busy and random.random() < 0.5:
                    self.start_climb(route)
                    return
                self.facing = -self.facing
        elif st == "goto":
            dx = self.goto_x - self.x
            if abs(dx) <= 3:
                if self.pending_watch and not busy:
                    self.pending_watch = False
                    self.facing = self.watch_face
                    self.set_state("watch", 99999)
                    return
                if self.pending_climb and not busy:
                    self.start_climb(self.pending_climb)
                    return
                if self.on_arrive and not busy:
                    then, self.on_arrive = self.on_arrive, None
                    then(self)
                    return
                self.set_state("idle", 9999 if busy else 40)
                return
            self.facing = 1 if dx > 0 else -1
            self.x += self.facing * min(getattr(self, "goto_speed", 2.4), abs(dx))
        elif st == "chase":
            if isinstance(self.target, Buddy):
                dx = self.target.cx() - self.cx()
                self.facing = 1 if dx > 0 else -1
                self.x += self.facing * min(4.8, abs(dx))
            else:
                target = self.app.root.winfo_pointerx() - self.sw / 2
                dx = target - self.x
                if abs(dx) < 8:
                    self.set_state("happy", 30)
                    self.spawn("heart", 2)
                    self.say("arrive", 40)
                    return
                self.facing = 1 if dx > 0 else -1
                self.x += self.facing * min(5, abs(dx))
        elif st == "flee":
            if isinstance(self.target, Buddy):
                away = 1 if self.cx() >= self.target.cx() else -1
                if self.x <= lo + 2:
                    away = 1
                elif self.x >= hi - 2:
                    away = -1
                dist = abs(self.cx() - self.target.cx())
                if dist < 220:              # run away, but stay close and teasing
                    self.facing = away
                    self.x += away * 3.2
                else:
                    self.face(self.target)
        elif st == "fs_flee":
            self.x += 7 * self.facing
            if self.timer <= 0 and self.flee_to:
                dest, self.flee_to = self.flee_to, None
                self.x = self.watch_x if self.watch_x is not None else (dest[0] + dest[2]) / 2
                self.y = dest[1] - self.sh           # drop in from the top of that screen
                self.vx = self.vy = 0
                self.dropped = False
                self.set_state("fall", 0)
            return
        elif st == "dizzy":
            self.x += math.sin(self.tick / 5) * 1.4          # staggering about
            if self.tick % 20 == 0:
                self.facing = -self.facing
            if self.timer <= 0:
                self.say("after_shake", 70)
                if not self.hook("on_event", "dizzy_end"):
                    self.set_state("idle", 60)
            return
        elif st == "race":                           # during a race with a rival
            self.x += self.mem.get("race_speed", 5) * self.facing
            if self.x <= lo or self.x >= hi:
                self.x = max(lo, min(hi, self.x))
                self.set_state("idle", 9999)             # reached the edge
            return
        elif st == "watch":
            self.facing = self.watch_face
            if random.random() < 0.0015:             # comment now and then (~every 30 s)
                self.say("watch_fs", 60)
            return
        elif st == "sleep":
            self.energy = min(100.0, self.energy + 0.3)
            if self.tick % 28 == 0:
                self.spawn("zed")
            if not busy and self.timer <= 0 and self.energy >= 99:
                self.say("wake_up")
                self.set_state("idle", 40)
            return
        elif st == "eat":
            if self.timer <= 0:
                self.hunger = 0.0
                self.say("yum")
                self.spawn("heart", 2)
                self.set_state("happy", 30)
                self.hook("on_event", "ate")
            return
        elif st == "idle" and not busy and random.random() < 0.003:
            crushes = [q for q in self.app.buddies if q is not self and not q.leaving
                       and self.bond(q) in ("crush", "heartbreak") and q.floor() == rect]
            if crushes and random.random() < 0.4:      # gazing at someone they love
                q = random.choice(crushes)
                self.face(q)
                self.say("pine", 80, other=q)
                self.spawn("heart", 1)
            else:
                late = "late" in self.lines and time.localtime().tm_hour < 5
                self.say("late" if late and random.random() < 0.5 else "chatter", 80)
                self.hook("on_event", "chatter")

        if self.timer <= 0 and not busy:
            self.pending_climb = None
            self.choose_next()

    def land(self):
        self.vx = self.vy = 0
        self.set_state("idle", 40)
        under = [p for p in self.app.buddies if p is not self and p.on_ground()
                 and p.floor() == self.floor()
                 and abs(p.cx() - self.cx()) < (p.sw + self.sw) / 4]
        if under and self.dropped:
            other = under[0]
            other.drop_social()
            self.say("oof", 50)
            other.face(self)
            if other.state != "dizzy":           # still too dizzy to do anything about it
                other.set_state("idle", 50)
            other.say("hey", 50)
            self.x += (24 if self.cx() >= other.cx() else -24)   # hop off
        elif not self.greeted:
            self.say("greet", 80)
        elif self.dropped and random.random() < 0.5:
            self.say("lands")
        self.greeted = True
        self.dropped = False
        if self.pending_dizzy:
            self.start_dizzy(self.pending_dizzy)
            self.pending_dizzy = 0

    def start_dizzy(self, ticks):
        self.drop_social()
        self.set_state("dizzy", ticks)
        self.say("dizzy", 70)
        self.hook("on_event", "dizzy")
        # a friend nearby notices
        friends = [q for q in self.app.buddies if q is not self and q.on_ground()
                   and q.social is None and q.state in ("idle", "walk", "loaf", "goto")
                   and q.floor() == self.floor() and abs(q.cx() - self.cx()) < 700]
        if friends:
            friend = random.choice(friends)
            friend.face(self)
            friend.set_state("idle", 80)
            friend.say("dizzy_other", 70, other=self)

    # ------------------------------------------------------------ render --
    def sprite_key(self):
        st, t = self.state, self.tick
        spr = self.ch["sprites"]
        blink = (t % 73) < 3
        if st == "goto" and getattr(self, "goto_speed", 2.4) > 3:     # running
            return "walk1" if (t // 3) % 2 == 0 else "walk2"
        if st in ("walk", "goto"):
            return "walk1" if (t // 5) % 2 == 0 else "walk2"
        if st in ("chase", "flee", "fs_flee", "race"):
            return "walk1" if (t // 3) % 2 == 0 else "walk2"
        if st in ("held", "fall"):
            return "held"
        if self.glitch_t > 0 and "glitch1" in spr and st in ("idle", "walk", "goto", "loaf"):
            return "glitch1" if t % 2 else "glitch2"
        spec = self.custom_state(st)
        if spec and spec.get("sprite"):
            return spec["sprite"](self)
        if st == "happy":
            return "happy_b" if "happy_b" in spr and (t // 3) % 2 else "happy"
        if st == "dizzy":
            return "blink" if (t // 7) % 2 else "stand"
        if st == "watch":
            if self.ch.get("watch_pose") == "loaf":
                return "loaf_blink" if blink else "loaf"
            return "blink" if blink else "stand"
        if st == "loaf":
            if blink:
                return "loaf_blink"
            return "loaf_b" if "loaf_b" in spr and (t // 8) % 2 else "loaf"
        if st == "sleep":
            return "sleep_b" if (t // 30) % 2 else "sleep"
        if st == "eat":
            return "loaf_blink" if (t // 4) % 2 else "loaf"
        if blink:
            return "blink"
        return "stand_b" if (t // 6) % 6 == 1 else "stand"

    def render(self):
        c = self.canvas
        c.delete("all")
        s = self.scale
        side = 0 if self.facing > 0 else 1

        spec = self.custom_state() or {}
        climbing = self.state == "climb" or spec.get("climb_pose")
        style = self.ch.get("climb_style")
        if spec.get("glow") or (climbing and style == "hover"):
            c.create_image(self.padx + self.sw // 2, self.padtop + self.sh + 4,
                           image=self.gfx["glow"])

        sprites = self.gfx["sprites"]
        if climbing and style == "claws":
            speed = 2 if spec.get("climb_pose") else 4
            key = "climb1" if (self.tick // speed) % 2 == 0 else "climb2"
            img = sprites[key][side]
            ix = self.padx + self.sw - img.width() if self.facing > 0 else self.padx
            c.create_image(ix, self.padtop + self.sh - img.height(), image=img, anchor="nw")
        else:
            img = sprites.get(self.sprite_key(), sprites["stand"])[side]
            rock = int(math.sin(self.tick / 3) * s) if self.state == "dizzy" else 0
            lift = int(self.lift())                 # bouncing along (drawing only)
            c.create_image(self.padx + rock, self.padtop - lift, image=img, anchor="nw")

        if self.state == "eat":
            level = min(5, int((1 - self.timer / self.state_len) * 6))
            item = self.gfx["items"][level][side]
            ix = self.ch["item_x"] if self.facing > 0 else \
                self.spr_w - self.ch["item_x"] - item.width() // s
            c.create_image(self.padx + ix * s, self.padtop + self.ch["item_y"] * s,
                           image=item, anchor="nw")

        if self.state == "dizzy":                 # stars circling the head
            hx, hy = self.head_pos()
            for i in range(3):
                a = self.tick * 0.22 + i * 2.094
                c.create_image(hx + math.cos(a) * 7 * s, hy - 2 + math.sin(a) * 2 * s,
                               image=self.app.star)

        alive = []
        for fx in self.effects:
            fx["life"] -= 1
            fx["y"] += fx["vy"]
            fx["x"] += fx["vx"] + math.sin(fx["phase"] + fx["life"] / 4) * 0.6 * fx.get("wobble", 1)
            if fx["life"] > 0:
                c.create_image(fx["x"], fx["y"], image=fx["img"])
                alive.append(fx)
        self.effects = alive

        if self.bubble:
            text, left = self.bubble
            if self.glitch_t > 0:
                text = "".join(random.choice("#%&@*") if ch != " " and random.random() < 0.2
                               else ch for ch in text)
            hx, hy = self.head_pos()
            tid = c.create_text(hx, hy - 10, text=text, fill="#2b1d14", anchor="s",
                                width=self.W - 24, justify="center",
                                font=("Segoe UI", 9, "bold"))
            x0, y0, x1, y1 = c.bbox(tid)
            shift = max(12 - x0, 0) + min(self.W - 12 - x1, 0)
            c.move(tid, shift, 0)
            x0, x1 = x0 + shift, x1 + shift
            rid = c.create_rectangle(x0 - 6, y0 - 2, x1 + 6, y1 + 2,
                                     fill="white", outline="#2b1d14", width=2)
            c.tag_raise(tid, rid)
            self.bubble[1] -= 1
            if self.bubble[1] <= 0:
                self.bubble = None

        wx = int(round(self.x)) - self.padx
        wy = int(round(self.y)) - self.padtop
        geo = f"{self.W}x{self.H}+{wx}+{wy}"   # "+-5" = 5px left of screen edge
        if geo != self._geo:
            self.win.geometry(geo)
            self._geo = geo


# =================================================================== props ==
class Prop:
    """An object in the world: it falls onto the floor, bounces and rolls, you
    can drag and throw it, and buddies can carry it or kick it around."""

    def __init__(self, app, kind, img, owner, x, y, vx, vy, life):
        self.app, self.kind, self.img, self.owner = app, kind, img, owner
        self.w, self.h = img.width(), img.height()
        self.x, self.y = x - self.w / 2, y - self.h
        self.vx, self.vy = vx, vy
        self.life, self.age = life, 0
        self.carried_by = None        # a Buddy holding it in its mouth / hands
        self.off_edge = False         # kicked hard enough to leave the screens
        self.data = {}                # behaviours can keep notes on a prop
        self.drag, self.gone, self._geo = None, False, None
        self.win = win = tk.Toplevel(app.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", KEY)
        win.config(bg=KEY)
        c = tk.Canvas(win, width=self.w, height=self.h, bg=KEY, highlightthickness=0, bd=0)
        c.pack()
        c.create_image(0, 0, image=img, anchor="nw")
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        self.place()

    # ------------------------------------------------------------ for behaviours --
    @property
    def name(self):
        return self.kind

    def cx(self):
        return self.x + self.w / 2

    def floor(self):
        return self.app.floor_at(self.cx(), self.y + self.h)

    def on_floor(self):
        return self.carried_by is None and self.drag is None and \
            abs(self.y + self.h - self.floor()[3]) < 2 and abs(self.vx) < 0.5

    def kick(self, vx, vy=-6.0, off_edge=False):
        """Send it flying. off_edge=True lets it leave the screens for good."""
        self.carried_by = None
        self.vx, self.vy = vx, vy
        self.off_edge = off_edge or self.off_edge

    def carry(self, buddy):
        self.carried_by = buddy

    def drop(self):
        self.carried_by = None
        self.vx = self.vy = 0.0

    def remove(self):
        if not self.gone:
            self.gone = True
            if self in self.app.props:
                self.app.props.remove(self)
            try:
                self.win.destroy()
            except tk.TclError:
                pass

    # ------------------------------------------------------------------- mouse --
    def on_press(self, e):
        self.carried_by = None
        self.drag = {"ox": e.x_root - self.x, "oy": e.y_root - self.y,
                     "lx": e.x_root, "ly": e.y_root, "vx": 0.0, "vy": 0.0}

    def on_drag(self, e):
        d = self.drag
        if d:
            self.x, self.y = e.x_root - d["ox"], e.y_root - d["oy"]
            d["vx"] = 0.5 * d["vx"] + 0.5 * (e.x_root - d["lx"])
            d["vy"] = 0.5 * d["vy"] + 0.5 * (e.y_root - d["ly"])
            d["lx"], d["ly"] = e.x_root, e.y_root
            self.place()

    def on_release(self, e):
        d, self.drag = self.drag, None
        if d:
            self.vx = max(-30, min(30, d["vx"] * 1.5))
            self.vy = max(-30, min(30, d["vy"] * 1.5))
            self.age = 0                      # you played with it: it stays longer

    # ------------------------------------------------------------------ update --
    def update(self):
        self.age += 1
        if self.age > self.life:
            if self.age > self.life + 30:
                self.remove()
                return
            self.win.attributes("-alpha", max(0.0, 1 - (self.age - self.life) / 30))
        if self.drag:
            return
        if self.carried_by is not None:
            buddy = self.carried_by
            if buddy not in self.app.buddies or buddy.leaving:
                self.drop()
            else:
                mx, my = buddy.mouth()
                self.x, self.y = mx - self.w / 2, my - self.h / 2
                self.place()
                return
        vl, vt, vr, vb = self.app.virtual
        ground = self.floor()[3] - self.h
        self.vy += 1.1
        self.x += self.vx
        self.y += self.vy
        if self.off_edge:
            if self.x > vr or self.x + self.w < vl:
                self.remove()                 # gone off the edge of the world
                return
        elif self.x < vl or self.x > vr - self.w:
            self.x = max(vl, min(vr - self.w, self.x))
            self.vx = -self.vx * 0.6          # bounce off the outer edges
        if self.y >= ground:
            self.y = ground
            if self.vy > 6:
                self.vy = -self.vy * 0.45     # bounce
                self.vx *= 0.8
            else:
                self.vy = 0.0
                self.vx *= 0.85               # roll to a stop
                if abs(self.vx) < 0.3:
                    self.vx = 0.0
        self.place()

    def place(self):
        geo = f"{self.w}x{self.h}+{int(round(self.x))}+{int(round(self.y))}"
        if geo != self._geo:
            self.win.geometry(geo)
            self._geo = geo


# ============================================================ interaction ==
class Interaction:
    """A short scripted scene between two buddies (a starts it, b responds)."""

    def __init__(self, app, kind, a, b):
        self.app, self.kind, self.a, self.b = app, kind, a, b
        self.t, self.phase, self.mark, self.done = 0, 0, 0, False
        a.social = b.social = self
        a.target, b.target = b, a
        # a scene from the starter's behaviours.INTERACTIONS, or a built-in one
        self.spec = (getattr(a.bhv, "INTERACTIONS", None) or {}).get(kind)
        if self.spec:
            self.spec["start"](self)
        else:
            getattr(self, "start_" + kind)()

    def partner(self, p):
        return self.b if p is self.a else self.a

    def speak(self, p, key, ticks=55):
        self.partner(p).bubble = None   # take turns talking
        p.say(key, ticks, other=self.partner(p))
        if p.relation(self.partner(p)) == "loves" and random.random() < 0.5:
            p.spawn("heart", 1)         # a little heart when talking to its crush

    def approach(self):
        """Send a to stand right next to b, facing it."""
        a, b = self.a, self.b
        side = 1 if a.cx() < b.cx() else -1
        gap = (a.sw + b.sw) / 2 * 0.6
        lo, hi = a.limits(a.floor())
        a.goto_x = max(lo, min(hi, b.cx() - side * gap - a.sw / 2))
        a.set_state("goto", 9999)
        b.face(a)

    def end(self):
        if self.done:
            return
        self.done = True
        for p in (self.a, self.b):
            if p.social is self:
                p.social, p.target = None, None
                p.social_cd = random.randint(300, 700)
                if p.on_ground():
                    p.set_state("idle", random.randint(30, 60))

    def step(self):
        a, b = self.a, self.b
        if self.done:
            return False
        if a not in self.app.buddies or b not in self.app.buddies \
                or not a.on_ground() or not b.on_ground():
            self.end()
            return False
        self.t += 1
        if self.spec:
            self.spec["step"](self)
        else:
            getattr(self, "step_" + self.kind)()
        if self.t > 900:              # safety net
            self.end()
        return not self.done

    # --- date (couple): hold hands, stroll together, sit side by side
    def start_date(self):
        self.b.set_state("idle", 9999)
        self.approach()

    def step_date(self):
        a, b = self.a, self.b
        t = self.t - self.mark
        if self.phase == 0:
            if a.state != "goto":
                a.face(b)
                b.face(a)
                a.set_state("happy", 9999)
                b.set_state("happy", 9999)
                self.speak(a, "date", 60)
                a.spawn("heart", 3)
                b.spawn("heart", 3)
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif self.phase == 1:
            if t == 45:
                self.speak(b, "date_back", 55)
                b.spawn("heart", 2)
            elif t == 90:                         # stroll off together, hand in hand
                lo, hi = a.limits(a.floor())
                self.dir = 1 if (hi - a.x) > (a.x - lo) else -1
                self.gap = (a.sw + b.sw) / 2 * 0.55
                for p in (a, b):
                    p.facing = self.dir
                    p.set_state("walk", 9999)
                self.phase, self.mark = 2, self.t
        elif self.phase == 2:
            b.x = a.x - self.dir * self.gap + (a.sw - b.sw) / 2     # stays right beside a
            b.facing = a.facing = self.dir
            if t % 18 == 0:
                random.choice((a, b)).spawn("heart", 1)
            lo, hi = a.limits(a.floor())
            if t >= 130 or not (lo + 4 < a.x < hi - 4):
                a.face(b)
                b.face(a)
                a.set_state("loaf", 9999)
                b.set_state("loaf", 9999)
                self.speak(a, "date_end", 70)
                a.spawn("heart", 3)
                self.phase, self.mark = 3, self.t
        elif t >= 90:
            self.end()

    # --- race (rivals): line up, race to the edge, gloat or sulk
    def start_race(self):
        self.b.set_state("idle", 9999)
        self.speak(self.a, "staredown", 45)
        self.approach()

    def step_race(self):
        a, b = self.a, self.b
        t = self.t - self.mark
        if self.phase == 0:
            if a.state != "goto":
                lo, hi = a.limits(a.floor())
                self.dir = 1 if (hi - a.x) > (a.x - lo) else -1
                a.facing = b.facing = self.dir
                a.set_state("idle", 9999)
                b.set_state("idle", 9999)
                self.speak(a, "race", 50)
                self.start_x = {a: a.cx(), b: b.cx()}
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif self.phase == 1 and t == 40:         # go!
            for p in (a, b):
                p.mem["race_speed"] = random.uniform(4.0, 6.5)
                p.set_state("race", 9999)
            self.phase, self.mark = 2, self.t
        elif self.phase == 2:
            if t >= 60 or (a.state != "race" and b.state != "race"):
                win, lose = (a, b) if (a.cx() - self.start_x[a]) * self.dir >= \
                    (b.cx() - self.start_x[b]) * self.dir else (b, a)
                win.set_state("happy", 9999)
                lose.set_state("loaf", 9999)
                win.face(lose)
                lose.face(win)
                self.speak(win, "race_win", 55)
                win.spawn("star", 3)
                self.phase, self.mark = 3, self.t
                self.loser = lose
        elif self.phase == 3 and t == 55:
            self.speak(self.loser, "race_lose", 55)
        elif self.phase == 3 and t >= 110:
            self.end()

    # --- tag-along (clingy): bounds over, gets brushed off, follows anyway
    def start_tagalong(self):
        self.b.set_state("idle", 9999)
        self.approach()

    def step_tagalong(self):
        a, b = self.a, self.b
        t = self.t - self.mark
        if self.phase == 0:
            if a.state != "goto":
                a.face(b)
                b.face(a)
                a.set_state("happy", 9999)
                self.speak(a, "tagalong", 55)
                a.spawn("heart", 2)
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif self.phase == 1 and t == 55:
            self.speak(b, "brush_off", 50)
        elif self.phase == 1 and t == 95:      # walks off; a follows
            lo, hi = b.limits(b.floor())
            b.facing = 1 if b.cx() >= a.cx() else -1
            if (b.facing > 0 and b.x > hi - 120) or (b.facing < 0 and b.x < lo + 120):
                b.facing = -b.facing            # cornered: go the other way
            b.set_state("walk", 9999)
            a.set_state("idle", 9999)
            self.phase, self.mark = 2, self.t
        elif self.phase == 2:
            if t == 25:
                self.speak(a, "tagalong_follow", 45)
                a.target = b
                a.set_state("chase", 9999)
            caught = t > 25 and abs(a.cx() - b.cx()) < (a.sw + b.sw) / 2 * 0.7
            if caught or t > 200:
                a.set_state("happy", 9999)
                b.set_state("idle", 9999)
                a.face(b)
                b.face(a)
                self.speak(b, "groan", 55)
                self.phase, self.mark = 3, self.t
        elif self.phase == 3 and t == 55:
            self.speak(a, "tagalong_end", 55)
            a.spawn("heart", 2)
        elif self.phase == 3 and t >= 110:
            self.end()

    # --- besties? (eager): asks if they're besties, gets a friendly dodge
    def start_bestie_ask(self):
        self.b.set_state("idle", 9999)
        self.approach()

    def step_bestie_ask(self):
        a, b = self.a, self.b
        t = self.t - self.mark
        if self.phase == 0:
            if a.state != "goto":
                a.face(b)
                b.face(a)
                a.set_state("happy", 9999)
                self.speak(a, "bestie_ask", 60)
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif t == 60:
            b.set_state("happy", 9999)
            self.speak(b, "bestie_dodge", 55)
        elif t == 120:
            self.speak(a, "bestie_hopeful", 55)
            a.spawn("heart", 1)
        elif t >= 175:
            self.end()

    # --- confess (crush / heartbreak): a nervous confession, and the answer
    def start_confess(self):
        self.b.set_state("idle", 9999)
        self.approach()

    def step_confess(self):
        a, b = self.a, self.b
        t = self.t - self.mark
        if self.phase == 0:
            if a.state != "goto":
                a.face(b)
                b.face(a)
                a.set_state("happy", 9999)
                self.speak(a, "confess", 70)
                a.spawn("heart", 3)
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif self.phase == 1 and t == 70:
            if b.relation(a) == "dislikes":
                self.speak(b, "reject", 55)
                b.facing = -b.facing              # turns away
            else:
                b.set_state("happy", 9999)
                self.speak(b, "friendzone", 60)
        elif self.phase == 1 and t == 135:
            a.set_state("loaf", 9999)
            self.speak(a, "heartbroken", 60)
        elif self.phase == 1 and t >= 200:
            self.end()

    # --- chat: say hi to each other
    def start_chat(self):
        for p in (self.a, self.b):
            p.set_state("idle", 9999)
            p.face(self.partner(p))
        a = self.a
        rivals = a.bond(self.b) == "rivals" and "hello_rivals" not in a.lines
        self.speak(a, "staredown" if rivals else "hello")

    def step_chat(self):
        if self.t == 45:
            self.speak(self.b, "hello_back")
        elif self.t == 95 and random.random() < 0.6:
            for p in (self.a, self.b):
                p.set_state("happy", 9999)
                p.spawn("heart", 1)
        elif self.t >= 125:
            self.end()

    # --- play tag: chaser runs after runner, roles swap when tagged
    def start_play(self):
        self.chaser, self.runner, self.swaps, self.wait = self.a, self.b, 0, 15
        self.chaser.face(self.runner)
        self.chaser.set_state("idle", 9999)
        self.runner.set_state("flee", 9999)
        self.speak(self.chaser, "play")

    def step_play(self):
        ch, rn = self.chaser, self.runner
        if self.phase == 1:                       # celebrating
            if self.t >= self.mark:
                self.end()
            return
        if self.wait > 0:
            self.wait -= 1
            if self.wait == 0:
                ch.set_state("chase", 9999)
            return
        if self.t == 25 and self.swaps == 0:
            self.speak(rn, "flee", 40)
        if abs(ch.cx() - rn.cx()) < 20:
            self.speak(ch, "tag", 40)
            ch.spawn("heart", 1)
            if self.swaps < 2:
                self.swaps += 1
                self.chaser, self.runner = rn, ch
                ch.set_state("flee", 9999)
                rn.set_state("idle", 9999)
                rn.face(ch)
                self.wait = 25
            else:
                for p in (ch, rn):
                    p.set_state("happy", 9999)
                    p.spawn("heart", 2)
                self.phase, self.mark = 1, self.t + 40
        elif self.t > 600:                    # nobody won; everyone is tired
            for p in (ch, rn):
                p.set_state("loaf", 9999)
            self.phase, self.mark = 1, self.t + 40

    # --- pet: a walks over and pets / headbutts b
    def start_pet(self):
        self.b.set_state("idle", 9999)
        self.approach()

    def step_pet(self):
        a, b = self.a, self.b
        if self.phase == 0:
            if a.state != "goto":
                a.face(b)
                b.face(a)
                a.set_state("happy", 9999)
                self.speak(a, "pet_other")
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif self.t == self.mark + 35:
            b.set_state("happy", 9999)
            b.spawn("heart", 3)
            self.speak(b, "petted")
        elif self.t >= self.mark + 90:
            self.end()

    # --- cuddle: nap side by side
    def start_cuddle(self):
        self.b.set_state("loaf", 9999)
        self.approach()

    def step_cuddle(self):
        a, b = self.a, self.b
        if self.phase == 0:
            if a.state != "goto":
                a.face(b)
                b.face(a)
                a.set_state("sleep", 9999)
                b.set_state("sleep", 9999)
                self.speak(a, "cuddle")
                a.spawn("heart", 1)
                b.spawn("heart", 1)
                self.phase, self.mark = 1, self.t
            elif self.t > 300:
                self.end()
        elif self.t >= self.mark + 320:
            self.speak(b, "wake_up")
            self.end()


# ==================================================================== app ==
class App:
    def __init__(self):
        enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.withdraw()                 # each buddy has its own window
        self.heart = make_image(HEART, 3, FX_COLORS)
        self.zed = make_image(ZED, 3, FX_COLORS)
        self.note = make_image(NOTE, 3, FX_COLORS)
        self.idea = make_image(IDEA, 3, FX_COLORS)
        self.scratch = make_image(SCRATCH, 3, FX_COLORS)
        self.star = make_image(STAR, 3, FX_COLORS)
        for ch in CHARACTERS.values():       # characters' own powers (e.g. Milo's facts)
            fn = getattr(ch["behaviour"], "on_app_start", None)
            if fn:
                fn(self, ch)
        self._gfx = {}
        self.refresh_monitors()
        self.buddies, self.interactions = [], []
        self.marks = []           # things left on the screen (claw marks), see leave_mark
        self.props = []           # objects in the world (balls, mugs...), see Prop
        self.fullscreen = None    # work area of the screen a fullscreen app is on
        self._fs_seen = None
        self.hidden = False       # buddies hidden: fullscreen and no other screen
        self.tick = 0

        cfg = load_settings()
        kinds = cfg.get("buddies") or cfg.get("pets") or [cfg.get("character", "Mochi")]
        kinds = [k for k in kinds if k in CHARACTERS][:MAX_BUDDIES] or list(CHARACTERS)[:1]
        for k in kinds:
            self.add_buddy(k, save=False)
        self.root.after(TICK_MS, self.loop)

    # ---------------------------------------------------------- monitors --
    def refresh_monitors(self):
        found = monitors(self.root)
        self.monitors = [rect for rect, dpi in found]
        self.dpi = dict(found)
        self.virtual = (min(m[0] for m in self.monitors), min(m[1] for m in self.monitors),
                        max(m[2] for m in self.monitors), max(m[3] for m in self.monitors))

    def floor_at(self, x, y):
        """The monitor whose floor something at (x, y) stands on or falls onto."""
        under = [m for m in self.monitors if m[0] <= x < m[2]]
        if not under:   # in a gap between screens: use the nearest one
            return min(self.monitors, key=lambda m: min(abs(x - m[0]), abs(x - m[2])))
        for m in sorted(under, key=lambda m: m[1]):
            if y <= m[3] + 2:
                return m
        return max(under, key=lambda m: m[3])

    def neighbour(self, rect, side):
        """A monitor touching rect's left (side=-1) or right (side=1) edge that a
        buddy can walk onto: any drop down, or a step up of at most 200px."""
        l, t, r, b = rect
        edge = l if side < 0 else r
        for m in self.monitors:
            other_edge = m[2] if side < 0 else m[0]
            if m != rect and m != self.fullscreen and abs(other_edge - edge) <= 2 \
                    and m[1] < b and m[3] > b - 200:
                return m
        return None

    def notice_attention(self, buddy):
        """You petted or fed `buddy`: tell the others (a jealous one may react)."""
        buddy.last_attention = self.tick
        for e in self.buddies:
            if e is not buddy and e.hook("on_event", "attention_elsewhere", other=buddy):
                return

    def step_route(self, rect, side, buddy):
        if not buddy.ch.get("can_climb", True):
            return None
        """Climb route up a tall step to a side-by-side screen whose floor is
        more than 200px higher (too tall to walk)."""
        l, t, r, b = rect
        edge = l if side < 0 else r
        for m in self.monitors:
            other_edge = m[2] if side < 0 else m[0]
            if m != rect and m != self.fullscreen and abs(other_edge - edge) <= 2 \
                    and t - 10 < m[3] <= b - 200:
                return (edge, side, m, m[3], True)
        return None

    def climb_routes(self, rect, buddy):
        """All ways up from this screen: tall steps beside it, and screens
        stacked above it (climbed up the edge of the overlap)."""
        if not buddy.ch.get("can_climb", True):
            return []
        routes = [r for r in (self.step_route(rect, -1, buddy), self.step_route(rect, 1, buddy)) if r]
        l, t, r, b = rect
        for m in self.monitors:
            if m == rect or m == self.fullscreen or not (t - 150 <= m[3] <= t + 2):
                continue
            lo, hi = max(l, m[0]), min(r, m[2])      # where the two screens overlap
            if hi - lo >= buddy.sw * 2:
                routes.append((lo, -1, m, m[3], False))
                routes.append((hi, 1, m, m[3], False))
        return routes

    def screen_below(self, rect, x):
        """A screen right under this one that a buddy at x could jump down to."""
        for m in self.monitors:
            if m != rect and m != self.fullscreen and m[0] <= x < m[2] \
                    and rect[3] - 2 <= m[1] <= rect[3] + 150:
                return m
        return None

    def pointer_monitor(self):
        px, py = self.root.winfo_pointerxy()
        found = self.monitors[0]
        for m in self.monitors:
            if m[0] <= px < m[2] and m[1] <= py < m[3]:
                found = m
        if found == self.fullscreen:          # new buddies don't land on your game
            free = [m for m in self.monitors if m != self.fullscreen]
            found = free[0] if free else found
        return found

    # -------------------------------------------------------- fullscreen --
    def check_fullscreen(self):
        """Called twice a second. Acts once the same answer is seen twice in a
        row, so alt-tabbing past a fullscreen window doesn't scatter the buddies."""
        fs = fullscreen_monitor()
        if fs is OURS:
            return
        if fs is not None and fs not in self.monitors:
            fs = None
        if fs != self._fs_seen:
            self._fs_seen = fs
            return
        if fs != self.fullscreen:
            if self.fullscreen is not None:
                self.leave_fullscreen()
            if fs is not None:
                self.enter_fullscreen(fs)
        elif fs is not None and not self.hidden:
            for p in self.buddies:                  # someone got dropped onto the game
                if p.on_ground() and p.state != "fs_flee" and p.floor() == fs:
                    p.flee_fullscreen(self.watch_home(fs, p))

    def watch_home(self, fs, buddy):
        """The free screen a buddy should watch from: its own, or the nearest one."""
        free = [m for m in self.monitors if m != fs]
        if buddy.floor() in free:
            return buddy.floor()
        fx, fy = (fs[0] + fs[2]) / 2, (fs[1] + fs[3]) / 2
        return min(free, key=lambda m: abs((m[0] + m[2]) / 2 - fx) + abs((m[1] + m[3]) / 2 - fy))

    def enter_fullscreen(self, fs):
        self.fullscreen = fs
        free = [m for m in self.monitors if m != fs]
        if not free:                              # nowhere to go: hide until it's over
            self.hidden = True
            for p in self.buddies:
                p.drop_social()
                p.win.withdraw()
            for pr in self.props:
                pr.win.withdraw()
            return
        fx = (fs[0] + fs[2]) / 2
        groups = {}
        for p in self.buddies:
            if not p.leaving:
                groups.setdefault(self.watch_home(fs, p), []).append(p)
        for home, buddies in groups.items():
            side = 1 if fx >= (home[0] + home[2]) / 2 else -1   # face the fullscreen screen
            x = home[2] - 30 if side > 0 else home[0] + 30      # line up along that edge
            for p in buddies:
                p.watch_face = side
                p.watch_x = max(home[0], min(home[2] - p.sw, x - p.sw if side > 0 else x))
                x += -side * (p.sw + 16)
                if p.state == "held":
                    continue
                if p.floor() == fs:
                    p.flee_fullscreen(home)
                else:
                    p.drop_social()
                    p.set_state("idle", 1)          # walks over to its watch spot

    def leave_fullscreen(self):
        self.fullscreen = None
        if self.hidden:
            self.hidden = False
            for p in self.buddies:
                p.win.deiconify()
                p.win.attributes("-topmost", True)
                p._geo = None
            for pr in self.props:
                pr.win.deiconify()
        watchers = []
        for p in self.buddies:
            if p.watch_x is not None:
                watchers.append(p)
            p.watch_x, p.pending_watch, p.flee_to = None, False, None
            if p.state in ("watch", "goto", "fs_flee"):
                p.set_state("idle", random.randint(20, 60))
        if watchers:
            random.choice(watchers).say("fs_back", 60)

    # ------------------------------------------------------------- marks --
    def leave_mark(self, img, x, y, life):
        """Leave an image at a fixed spot on the screen (centred on x, y) that
        fades out over `life` ticks - it doesn't follow the buddy around."""
        w, h = img.width(), img.height()
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", KEY)
        win.config(bg=KEY)
        c = tk.Canvas(win, width=w, height=h, bg=KEY, highlightthickness=0, bd=0)
        c.pack()
        c.create_image(0, 0, image=img, anchor="nw")
        win.geometry(f"{w}x{h}+{int(x - w / 2)}+{int(y - h / 2)}")
        self.marks.append({"win": win, "life": life, "full": life})

    MAX_PROPS = 12

    def add_prop(self, prop):
        self.props.append(prop)
        while len(self.props) > self.MAX_PROPS:      # no clutter: the oldest goes
            self.props[0].remove()
        return prop

    def clear_props(self):
        for pr in list(self.props):
            pr.remove()

    def update_props(self):
        for pr in list(self.props):
            if self.fullscreen is not None and pr.floor() == self.fullscreen:
                pr.remove()                        # out of the way of your game
            if not pr.gone:
                pr.update()
        self.props = [pr for pr in self.props if not pr.gone]
        # now and then, let buddies notice props near them (behaviours.on_prop)
        if self.tick % 15 == 0 and self.props:
            for buddy in self.buddies:
                if not getattr(buddy.bhv, "on_prop", None) or buddy.social or buddy.leaving \
                        or buddy.state not in ("idle", "walk", "loaf"):
                    continue
                here = [pr for pr in self.props if pr.floor() == buddy.floor() and not pr.gone]
                random.shuffle(here)
                for pr in here:
                    if buddy.hook("on_prop", pr):
                        break

    def update_marks(self):
        alive = []
        for m in self.marks:
            m["life"] -= 1
            if m["life"] <= 0 or self.hidden:
                m["win"].destroy()
                continue
            if m["life"] < 30:                     # fade out at the end
                m["win"].attributes("-alpha", m["life"] / 30)
            alive.append(m)
        self.marks = alive

    def scale_for(self, kind, rect):
        """Pixel scale for a buddy on this monitor, matched to its display scaling."""
        return max(2, round(CHARACTERS[kind]["scale"] * self.dpi.get(rect, 96) / 96))

    def graphics(self, kind, s):
        key = (kind, s)
        if key not in self._gfx:
            ch = CHARACTERS[kind]
            pal = ch["palette"]
            self._gfx[key] = {
                "sprites": {k: (make_image(v, s, pal, False, ch.get("art", 1)),
                                make_image(v, s, pal, True, ch.get("art", 1)))
                            for k, v in ch["sprites"].items()},
                "items": [(make_image(it, s, pal), make_image(it, s, pal, True))
                          for it in ch["items"]],
                "glow": make_image(GLOW, 3, pal),
                "effects": {k: make_image(v, s, pal, False, ch.get("art", 1))
                            for k, v in ch.get("effects", {}).items()},
                "marks": {k: make_image(v, s, pal, False, ch.get("art", 1))
                          for k, v in ch.get("marks", {}).items()},
                "props": {k: make_image(v, s, pal, False, ch.get("art", 1))
                          for k, v in ch.get("props", {}).items()},
            }
        return self._gfx[key]

    # -------------------------------------------------------- buddy list --
    def unique_name(self, kind):
        names = {p.name for p in self.buddies}
        if kind not in names:
            return kind
        n = 2
        while f"{kind} {n}" in names:
            n += 1
        return f"{kind} {n}"

    def add_buddy(self, kind, save=True):
        if len(self.buddies) >= MAX_BUDDIES:
            if self.buddies:
                self.buddies[0].say("That's a lot of friends already!")
            return
        buddy = Buddy(self, kind, self.unique_name(kind))
        self.buddies.append(buddy)
        buddy.render()
        if save:
            self.save()

    def remove_buddy(self, buddy):
        if buddy not in self.buddies:
            return
        if len(self.buddies) == 1:            # last one: quit, but remember it
            self.root.destroy()
            return
        self.buddies.remove(buddy)
        buddy.win.destroy()
        self.save()

    def save(self):
        save_settings({"buddies": [p.kind for p in self.buddies]})

    def goodbye_all(self):
        for p in self.buddies:
            p.leave(then=lambda: None)
        self.root.after(1200, self.root.destroy)

    def call_all(self):
        for p in self.buddies:
            p.come_here()

    def build_menu(self, buddy):
        m = tk.Menu(self.root, tearoff=0)
        name = buddy.name
        m.add_command(label=f"Pet {name}", command=buddy.pet)
        if buddy.ch.get("needs_food", True):
            m.add_command(label=buddy.ch["feed_label"].replace(buddy.kind, name), command=buddy.feed)
        m.add_command(label="Come here", command=buddy.come_here)
        m.add_command(label="Nap time", command=buddy.nap)
        m.add_command(label="How are you?", command=buddy.stats)
        for label, fn in getattr(buddy.bhv, "MENU", None) or []:     # character's own items
            m.add_command(label=label, command=lambda f=fn: f(buddy))
        m.add_separator()
        add = tk.Menu(m, tearoff=0)
        for kind in CHARACTERS:
            add.add_command(label=kind, command=lambda k=kind: self.add_buddy(k))
        m.add_cascade(label="Add a buddy", menu=add,
                      state="normal" if len(self.buddies) < MAX_BUDDIES else "disabled")
        if self.props:
            m.add_command(label="Tidy up toys", command=self.clear_props)
        if len(self.buddies) > 1:
            m.add_command(label="Everyone, come here!", command=self.call_all)
            m.add_command(label=f"Send {name} home", command=buddy.leave)
            m.add_separator()
            m.add_command(label="Goodbye, everyone", command=self.goodbye_all)
        else:
            m.add_separator()
            m.add_command(label="Say goodbye", command=buddy.leave)
        return m

    # ------------------------------------------------------------ social --
    def social(self):
        self.interactions = [it for it in self.interactions if it.step()]
        buddies = [p for p in self.buddies if not p.leaving]

        # bumping into each other while walking
        for i, p in enumerate(buddies):
            for q in buddies[i + 1:]:
                if p.social or q.social or p.bump_cd > 0 or q.bump_cd > 0                         or p.pending_climb or q.pending_climb                         or p.pending_watch or q.pending_watch or p.on_arrive or q.on_arrive:
                    continue
                if p.state not in ("walk", "goto") or q.state not in ("walk", "goto"):
                    continue
                dx = q.cx() - p.cx()
                if p.floor() == q.floor() and abs(dx) < min(p.sw, q.sw) * 0.5 and p.facing * dx > 0 and q.facing * dx < 0:
                    p.facing, q.facing = -p.facing, -q.facing
                    if p.state == "goto":
                        p.set_state("walk", 40)
                    if q.state == "goto":
                        q.set_state("walk", 40)
                    random.choice((p, q)).say("bump", 40)
                    p.bump_cd = q.bump_cd = 80

        # start a new interaction between two nearby free buddies
        free = [p for p in buddies if p.is_free()]
        if len(free) >= 2 and random.random() < 0.05:
            a = random.choice(free)
            others = [q for q in free if q is not a]
            b = random.choices(others, [a.affinity(q) for q in others])[0]
            rel, bond = a.relation(b), a.bond(b)
            near = abs(a.cx() - b.cx()) < 220
            comes_over = rel in COMES_OVER or bond in BOND_COMES_OVER
            if a.floor() == b.floor() and (near or comes_over):
                tired = min(a.energy, b.energy) < 60
                # scenes that walk over by themselves can start from far away
                walking = {"couple": [("date", 45)], "rivals": [("race", 40)],
                           "crush": [("confess", 2)], "heartbreak": [("confess", 3)],
                           "clingy": [("tagalong", 35)], "eager": [("bestie_ask", 8)]}.get(bond, [])
                # far apart: often they just don't bother ("none")
                kinds = (walking + [("none", 30)]) if not near else walking + ({
                    "couple":     [("chat", 20), ("pet", 30), ("cuddle", 35 if tired else 20)],
                    "besties":    [("chat", 35), ("play", 45), ("pet", 20), ("cuddle", 18 if tired else 8)],
                    "crush":      [("chat", 35), ("play", 12), ("pet", 25), ("cuddle", 18 if tired else 6)],
                    "heartbreak": [("chat", 30), ("pet", 10)],
                    "rivals":     [("chat", 25), ("play", 15)],
                    "clingy":     [("chat", 25), ("play", 15), ("pet", 10)],
                    "eager":      [("chat", 35), ("play", 30), ("pet", 20), ("cuddle", 12 if tired else 4)],
                    "admired":    [("chat", 35), ("play", 25), ("pet", 15), ("cuddle", 10 if tired else 2)],
                    "casual":     [("chat", 35), ("play", 25), ("pet", 20), ("cuddle", 12 if tired else 4)],
                    "pestered":   [("chat", 30)],                 # just wants to be left alone
                }.get(bond) or {
                    "loves":    [("chat", 30), ("play", 15), ("pet", 35), ("cuddle", 30 if tired else 12)],
                    "bestie":   [("chat", 35), ("play", 35), ("pet", 20), ("cuddle", 18 if tired else 6)],
                    "friend":   [("chat", 35), ("play", 25), ("pet", 20), ("cuddle", 18 if tired else 4)],
                    "dislikes": [("chat", 35), ("play", 6)],     # no petting, no cuddles
                }[rel])
                # scenes this character brings (behaviours.INTERACTIONS)
                for name, spec in (getattr(a.bhv, "INTERACTIONS", None) or {}).items():
                    if near or spec.get("walks_over"):
                        w = spec.get("weight", 0)
                        kinds.append((name, w(a, b) if callable(w) else w))
                if sum(w for _, w in kinds) > 0:
                    kind = random.choices([k for k, _ in kinds], [w for _, w in kinds])[0]
                    if kind != "none":
                        self.interactions.append(Interaction(self, kind, a, b))

    # -------------------------------------------------------------- loop --
    def loop(self):
        self.tick += 1
        try:
            if self.tick % 40 == 0:
                self.refresh_monitors()
                for ch in CHARACTERS.values():
                    fn = getattr(ch["behaviour"], "on_app_tick", None)
                    if fn:
                        fn(self, ch)
            if self.tick % 100 == 0:
                for p in self.buddies:
                    p.win.attributes("-topmost", True)
                for pr in self.props:
                    pr.win.attributes("-topmost", True)
            if self.tick % BREAK_EVERY == 0:
                awake = [p for p in self.buddies if p.on_ground() and p.state != "sleep"]
                if awake:
                    random.choice(awake).say("break", 120)
            if self.tick % 10 == 0:
                self.check_fullscreen()
            self.update_marks()
            if not self.hidden:
                self.update_props()
                for p in list(self.buddies):
                    p.update()
                self.social()
                for p in list(self.buddies):
                    p.render()
        except tk.TclError:
            return  # app was closed
        self.root.after(TICK_MS, self.loop)


def main():
    if not CHARACTERS:
        print(f"No characters found in {CHARACTERS_DIR}", file=sys.stderr)
        return
    App().root.mainloop()


if __name__ == "__main__":
    main()
