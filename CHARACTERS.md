# Characters

Every buddy lives in its own folder in `characters/`. The app loads every folder
it finds when it starts, so **sharing a buddy = sharing its folder**.

```
characters/
  mochi/
    character.json   name, size, settings, and everything she says
    sprites.json     her art (what the app draws)
    behaviours.py    her own moves and reactions (optional)
    source.py        the code that draws her art (optional, for editing)
```

## Making your own

Start from `template_character/`: a working little blob called Pip, with every
setting, line and hook filled in. Copy it into `characters/`, rename the
folder and the `"name"`, and change it bit by bit (its `README.md` has the
steps). Because it lives outside `characters/`, the template itself never
shows up as a buddy.

## Sharing

- **Give someone a buddy:** zip its folder (e.g. `characters/mochi`) and send it.
- **Add a buddy you were given:** unzip it into `characters/`, so you get
  `characters/<name>/character.json`, and restart the buddies. It shows up under
  right-click → *Add a buddy*.
- **Remove one:** delete its folder.

> **Only add characters from people you trust.** `behaviours.py` (and any other
> `.py` file in the folder) is Python code, and it runs when the buddies start, with
> the same access to your computer as the buddies app itself. Open it and have a
> look first if you're unsure. A folder with just the two `.json` files can't run
> any code.

If a character folder is broken, the app skips it and starts anyway.

## character.json

Plain text you can edit. The main keys:

| key | what it does |
|---|---|
| `name` | shown in menus; must be unique |
| `scale` | how many screen pixels per art pixel at 100% display scaling (usually 4) |
| `head` | `[x, y standing, y sitting]` in normal-size art pixels: where speech bubbles and hearts start |
| `item_x`, `item_y` | where the food is drawn while eating |
| `feed_label` | the menu text for feeding, e.g. `"Feed Mochi"` |
| `extra_states` | extra weight for built-in moves, e.g. `[["chase", 8]]` |
| `climb_style` | `"claws"` (clings to the edge) or `"hover"` (floats up on a glow) |
| `climb_speed` | pixels per tick while climbing |
| `can_climb` | `false` to stay on the floor |
| `needs_food` | `false` if it never gets hungry |
| `watch_pose` | how it watches while you're fullscreen: `"loaf"` (the default), `"stand"`, or any sprite of its own like `"sit"` (it also uses `sit_blink` and `sit_b` if they exist) |
| `bubble_room` | extra space above the head for long speech bubbles |
| `relationships` | how it feels about other buddies, by name, e.g. `{"Milo": "bestie"}` (see below) |
| `lines` | everything it says (see below) |
| `facts` | (Milo) the starting list of fun facts |

**Lines:** each key is a moment, and the value is a list of things to say (one
is picked at random). `{other}` becomes the other buddy's name, `{time}` the
clock, `{mins}` how long the buddies have been running. Moments the engine uses
include `greet pet wake eat full yum hungry chatter sleepy wake_up lands held
come arrive bye break climb made_it drop moods hello hello_back play flee tag
cuddle pet_other petted scanned bump oof hey scared fact_reply fs_flee watch_fs
fs_back shaking dizzy after_shake dizzy_other`. A character's behaviours can
use any other keys they like.

**Fullscreen moments** also come in flavours for what you're doing:
`fs_flee_video`, `watch_fs_video`, `fs_back_video` (a show or video: they sit
with popcorn and whisper) and `fs_flee_game`, `watch_fs_game`, `fs_back_game`
(a game: they jump up and cheer). Without them the plain `fs_flee` /
`watch_fs` / `fs_back` lines are used. During a presentation or while you're
sharing your screen, buddies hide and say nothing. How a fullscreen app is
recognised lives in `fullscreen_context.txt` - add your own programs there.

## Relationships

```json
"relationships": {"Milo": "bestie", "Nova": "loves", "Echo": "dislikes"}
```

Every other buddy is a **friend** (the default). Use `"*"` for "everyone not
listed by name", e.g. Biscuit's `{"*": "bestie"}` (besties with everyone,
including buddies added later). The four kinds:

| kind | what happens |
|---|---|
| `friend` | normal: chats, tag, petting, cuddles |
| `bestie` | seeks them out about 3x as often, plays more, and will walk across the screen to start a scene |
| `loves` | a crush: seeks them out, more petting and cuddles, little hearts while talking to them, walks over to them |
| `dislikes` | avoids them, only chats (snippily) or plays tag, and never pets or cuddles them |

Relationships are one-way: if Mochi `loves` Nova but Nova doesn't list Mochi,
Nova just sees Mochi as a friend. Unrequited love, built in.

### Bonds: when both sides count

How *both* buddies feel makes a bond with its own behaviour. Every pair of
feelings has one (rows: how A feels about B; columns: how B feels about A;
the cell is A's side of the bond):

| A \ B | loves | bestie | friend | dislikes |
|---|---|---|---|---|
| **loves** | couple | crush | crush | heartbreak |
| **bestie** | admired | besties | eager | clingy |
| **friend** | admired | casual | *(just friends)* | *(dislikes, one way)* |
| **dislikes** | pestered | pestered | *(dislikes)* | rivals |

| bond | what happens |
|---|---|
| `couple` | they seek each other out the most and go on **dates**: hold hands, stroll side by side with hearts, sit together |
| `besties` | they hang out and play tag the most |
| `crush` | gazes and sighs at them, and once in a while **confesses**. The answer: "...as a friend!" |
| `heartbreak` | confesses anyway, and gets turned down flat |
| `admired` | the other side of a crush: friendly, a little flattered |
| `eager` | thinks they're besties; seeks them out and asks **"We're besties, right?"** The other dodges: "You're a great... friend!" |
| `casual` | the other side of eager: friendly, just not *that* close |
| `clingy` | thinks they're besties, but is disliked: **tags along**, gets brushed off, chases after them anyway |
| `pestered` | the other side of clingy (or of an unwanted crush): mostly avoids them |
| `rivals` | staredowns, and **races** to the edge of the screen: a gloating winner and a sore loser |

Couples, besties, crushes, eager and clingy buddies, and rivals walk across the screen to find each other.
The built-in scenes have default lines, so any two buddies can be a couple or
rivals without writing anything. To give a character its own, use these line
keys: `date date_back date_end race race_win race_lose staredown pine confess
friendzone reject heartbroken tagalong brush_off tagalong_follow groan
tagalong_end bestie_ask bestie_dodge bestie_hopeful`.

**Keep it kind unless they dislike each other.** Buddies can tease (Mochi's a
tsundere, Roxy's cool), but anything actually mean - hissing, insults,
"serves you right", scaring someone off - belongs only in `_dislikes` lines
and in scenes with buddies they dislike. Echo, for example, sulks at *you* when
you pet a friend, and only storms over to scare off buddies she dislikes.

**Lines per relationship:** add `_bestie`, `_loves` or `_dislikes` to any line
key (e.g. `hello_loves`, `fact_reply_bestie`, `pet_other_dislikes`), or a bond
(`hello_couple`, `tag_rivals`, `hello_besties`...), and those lines are used
when talking to that buddy. A bond version wins over a relationship version,
and anything without its own version falls back to the normal line. See Roxy
and Milo.

In `behaviours.py`, `buddy.relation(other)` tells you how `buddy` feels about
`other`, and `buddy.bond(other)` gives the two-way bond (or `None`), so your own
scenes can react to them. A scene's `"weight"` can be a
function, e.g. `lambda a, b: 40 if a.relation(b) == "bestie" else 0`, and
`"walks_over": True` lets it start from across the screen.

## sprites.json

```json
{
 "art": 2,
 "palette": {"k": "#2b1d14", "o": "#f2a65a"},
 "items": [["kk", "kk"], "... 6 frames: the food, from whole to eaten"],
 "sprites": {
  "stand": ["....kk....", "...kook...", "..."]
 }
}
```

- Each sprite is a list of text rows. Each character is one pixel, coloured by
  `palette`, and `.` is see-through.
- `art: 2` means the sprites are drawn at double detail (each art pixel is half
  size on screen). Use `1` for chunkier art.
- Sprites face **right**. They're mirrored automatically for walking left.
- Sprites the engine uses: `stand stand_b blink walk1 walk2 happy held loaf
  loaf_blink sleep sleep_b` (required), plus `happy_b loaf_b` (optional
  animation frames), `climb1 climb2` (for `climb_style: "claws"`), and
  `glitch1 glitch2` (screen glitches, if the buddy sets `glitch_t`). A
  character's own states can use any sprite names.

You can write `sprites.json` by hand, or generate it:

### Effects, marks and props

`sprites.json` can also have three optional sections, drawn with the same
palette and `art` setting as the sprites:

```json
"effects": {"gum_pop": ["..."]},
"marks":   {"paw": ["..."]},
"props":   {"ball": ["..."]}
```

| kind | what it is | from behaviours.py |
|---|---|---|
| **effects** | float up from the head and vanish, like hearts | `buddy.spawn("gum_pop", n)` |
| **marks** | stay put on the screen (they don't follow the buddy) and fade | `buddy.leave_mark("paw", x, y, life)` |
| **props** | real objects: they fall, bounce and roll, you can drag and throw them, and buddies can carry or kick them | `buddy.drop_prop("ball", x, y, vx, vy, life)` |

Built-in effects anyone can use: `heart zed note idea star`. (`life` is in
frames: 20 = one second. Props last 3 minutes by default, and fade out.)

**Props in behaviours.py** - `drop_prop` returns the prop:
`prop.kind`, `prop.owner` (the buddy that dropped it), `prop.cx()`,
`prop.floor()`, `prop.on_floor()`, `prop.kick(vx, vy, off_edge=False)`,
`prop.carry(buddy)` / `prop.drop()`, `prop.remove()`, `prop.age`, and
`prop.data` for your own notes. `app.props` lists them all.

A buddy can react to props near it with an `on_prop(buddy, prop)` hook (called
now and then while it's idle, walking or loafing; return True if it does
something). Biscuit fetches balls, Mochi bats things around and knocks them
off the edge of the screen, Roxy goes back for her parked skateboard.

At most 12 props exist at once (the oldest goes), they get out of the way of
fullscreen apps, and right-click → **Tidy up toys** clears them.

## source.py (optional)

Python that builds the art, using helpers in `buddyart.py` (doubling the
resolution, thin outlines, shading, painting faces on). It must define
`ART`, `PALETTE`, `SPRITES` and `item(level)`, and can define `EFFECTS`, `MARKS`
and `PROPS`. After editing, rebuild:

```
python tools/bake_sprites.py mochi
```

The app never runs `source.py`; it only reads `sprites.json`.

## behaviours.py (optional): unique moves and powers

Everything here is optional. Define only what your character needs.

```python
import random

# Its own moves. The engine picks them at random alongside walking, napping, etc.
STATES = {
    "dance": {
        "weight": 12,                 # how often it's picked (walk is 40); 0 = never at random
        "start": start_dance,         # start(buddy): set_state(), say a line...
        "tick": tick_dance,           # tick(buddy, world): runs every frame while in this state
        "sprite": sprite_dance,       # sprite(buddy) -> sprite name to draw
        "floats": True,               # don't snap to the floor (hops, hovering)
        "glow": False,                # draw a glow underneath
        "climb_pose": False,          # draw it clinging to the screen edge
        "bob": 2,                     # bounce while doing it: a height in art pixels, or
                                      # a function(buddy) -> screen pixels (see buddy.hop)
    },
}

# Scenes with another buddy: `scene.a` (this buddy) and `scene.b` (the friend).
INTERACTIONS = {
    "scan": {"weight": 18, "start": start_scan, "step": step_scan},
}

MENU = [("Tell me a fact", tell_fact)]     # extra right-click items: fn(buddy)

def setup(buddy): ...                         # once per buddy; keep notes in buddy.mem
def on_tick(buddy, world): ...                # every frame on the ground; return True to take over
def on_pet(buddy): ...                        # return {"line", "hearts", "happy", "ticks"} to change petting
def on_prop(buddy, prop): ...                 # a prop is nearby; return True if you act on it
def on_event(buddy, event, other=None): ...   # "chatter", "dizzy", "dizzy_end", "fs_flee", "fs_cheer", "ate",
                                            # "attention_elsewhere" (you petted `other`);
                                            # return True if you handled it
def on_app_start(app, ch): ...              # once when the app starts (e.g. background downloads)
def on_app_tick(app, ch): ...               # every 2 seconds
```

`buddy.app.fs_kind` says what's fullscreen right now: `"video"`, `"game"`,
`"present"`, `"other"`, or `None`.

**Useful things on `buddy`:** `say(key, ticks)`, `set_state(name, ticks)`,
`spawn("heart"|"zed"|"note"|"idea"|"star"|"scratch", n)`, `face(other)`,
`walk_to(x, then=fn, speed=2.4)`, `start_scene(kind, other)`, `pointer()`, `cx()`,
`floor()`, `limits(rect)`, `on_ground()`, `drop_social()`, `blinking()`,
`walk_frame(fast)`, `hop(height, period)` (a bounce, for `"bob"`), and the fields `x y facing state timer state_len tick
scale sw sh energy hunger glitch_t social mem lines ch app`.

**`world`** (passed to `tick` and `on_tick`): `ground` (y of the floor), `lo`
and `hi` (how far it can walk), `busy` (in a scene or leaving) and `rect` (the
screen).

**On a `scene`:** `t` (ticks so far), `phase` and `mark` (for your own
script), `speak(buddy, key, ticks)`, `approach()` (a walks up to b), and `end()`.

A behaviours file can import its own helper files from the same folder, e.g.
Milo's `from .fact_search import FactSearch`.

### Examples in this folder

- `mochi`: tsundere petting (`on_pet`), scratching the screen, sneaking up to sit by your cursor (`walk_to`), sulking after being shaken.
- `nova`: hovering, scanning (also her friends, via `INTERACTIONS`), dancing.
- `echo`: screen glitches (`on_tick`), getting jealous when you pet someone else (`on_event`).
- `milo`: telling facts, plus **fact searching** in `fact_search.py`, a background download started from `on_app_start`.
- `biscuit`: zoomies, going round every buddy for pets when you ignore him, loving being shaken.
