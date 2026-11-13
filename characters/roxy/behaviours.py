"""Roxy: hip, cool and always in pink. She skates across your screen, blows
bubblegum bubbles, vibes to music, lowers her shades to wink at you, and
fist-bumps her friends. She acts unbothered, but if you keep petting her
she admits you're her favorite."""
import math
import random


# ------------------------------------------------------------------ skate --
def my_board(buddy):
    return next((pr for pr in buddy.app.props if pr.kind == "board" and pr.owner is buddy), None)


def start_skate(buddy):
    board = my_board(buddy)
    if board is not None and board.floor() == buddy.floor():   # go and grab her board first
        lo, hi = buddy.limits(buddy.floor())
        buddy.walk_to(max(lo, min(hi, board.cx() - buddy.sw / 2)), then=pick_up_board)
        return
    if board is not None:
        board.remove()                                  # (it's on another screen)
    really_skate(buddy)


def pick_up_board(buddy):
    board = my_board(buddy)
    if board is not None:
        board.remove()
    really_skate(buddy)


def really_skate(buddy):
    buddy.mem["ollie"] = 0                              # start on the ground
    buddy.set_state("skate", random.randint(60, 110))
    buddy.say("skate", 40)
    if random.random() < 0.5:
        buddy.facing = -buddy.facing


OLLIE = 16                                              # frames in the air


def tick_skate(buddy, world):
    buddy.x += 5 * buddy.facing
    if buddy.x <= world.lo or buddy.x >= world.hi:          # turn around at the edge
        buddy.facing = -buddy.facing
    o = buddy.mem.get("ollie", 0)
    if o > 0:                                           # in the air
        buddy.mem["ollie"] = o - 1
        if o == 1 and random.random() < 0.5:            # landed a trick
            buddy.spawn("star", 2)
            buddy.say("trick", 35)
    elif random.random() < 0.02:                        # pop an ollie now and then
        buddy.mem["ollie"] = OLLIE
    if buddy.timer == 1 and random.random() < 0.4:       # parks her board for later
        buddy.drop_prop("board", x=buddy.cx() - buddy.facing * buddy.sw * 0.6, life=3000)
        buddy.say("park", 45)


def bob_skate(buddy):
    """Smooth rolling, plus a little arc in the air for each ollie."""
    o = buddy.mem.get("ollie", 0)
    return math.sin(math.pi * (OLLIE - o) / OLLIE) * 6 * buddy.scale if o > 0 else 0


def sprite_skate(buddy):
    return "skate_b" if (buddy.tick // 8) % 3 == 0 else "skate"


# -------------------------------------------------------------- bubblegum --
def start_gum(buddy):
    buddy.set_state("gum", 70)
    buddy.say("gum", 30)


def tick_gum(buddy, world):
    if buddy.timer == 1:                                  # it pops!
        buddy.spawn("gum_pop", 2)
        buddy.say("pop", 50)


def sprite_gum(buddy):
    grown = 1 - buddy.timer / buddy.state_len               # 0 -> 1 as the bubble grows
    return "gum1" if grown < 0.35 else "gum2" if grown < 0.7 else "gum3"


# ------------------------------------------------------------------- vibe --
def start_vibe(buddy):
    buddy.set_state("vibe", random.randint(90, 140))
    buddy.say("vibe", 50)


def tick_vibe(buddy, world):
    if buddy.tick % 18 == 0:
        buddy.spawn("note")


def sprite_vibe(buddy):
    return "vibe2" if (buddy.tick // 8) % 2 else "vibe1"   # nodding to the beat


# ------------------------------------------------------------------- peek --
def start_peek(buddy):
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1   # looks at you
    buddy.set_state("peek", 50)
    buddy.say("peek", 45)


def sprite_peek(buddy):
    return "peek"


STATES = {
    "skate": {"weight": 10, "start": start_skate, "tick": tick_skate, "sprite": sprite_skate,
              "bob": bob_skate},                         # ollies
    "gum": {"weight": 8, "start": start_gum, "tick": tick_gum, "sprite": sprite_gum},
    "vibe": {"weight": 8, "start": start_vibe, "tick": tick_vibe, "sprite": sprite_vibe,
             "bob": lambda buddy: buddy.hop(0.6, 8)},       # nodding to the beat
    "peek": {"weight": 5, "start": start_peek, "sprite": sprite_peek},
}


# --------------------------------------------------------- with friends --
def start_fist_bump(scene):
    scene.b.set_state("idle", 9999)
    scene.approach()


def step_fist_bump(scene):
    a, b = scene.a, scene.b
    if scene.phase == 0:
        if a.state != "goto":
            a.face(b)
            b.face(a)
            a.set_state("happy", 9999)
            scene.speak(a, "fist_bump", 40)
            scene.phase, scene.mark = 1, scene.t
        elif scene.t > 300:
            scene.end()
    elif scene.t == scene.mark + 25:
        b.set_state("happy", 9999)
        if "fist_bump_back" in b.lines:
            scene.speak(b, "fist_bump_back", 40)
        else:
            scene.speak(b, "petted", 40)
        a.spawn("star", 2)
    elif scene.t >= scene.mark + 70:
        scene.end()


# --- hanging out with her bestie (when they're besties both ways: Milo)
def start_bestie(scene):
    a, b = scene.a, scene.b
    b.set_state("idle", 9999)
    scene.approach()
    scene.speak(a, "hello", 50)          # -> her hello_bestie lines


def step_bestie(scene):
    a, b = scene.a, scene.b
    t = scene.t - scene.mark
    if scene.phase == 0:                 # walking over
        if a.state != "goto":
            a.face(b)
            b.face(a)
            a.set_state("happy", 9999)
            b.set_state("happy", 9999)
            scene.speak(b, "hello_back", 50)
            a.spawn("heart", 2)
            b.spawn("heart", 2)
            scene.phase, scene.mark = 1, scene.t
        elif scene.t > 300:
            scene.end()
    elif scene.phase == 1:
        if t == 50:                      # he shares a fact, if he knows any
            tell = getattr(b.bhv, "next_fact", None)
            if tell:
                if "fact" in b.ch["sprites"]:
                    b.set_state("fact", 9999)
                b.say(tell(b), 110)
                b.spawn("idea")
            else:
                scene.speak(b, "chatter", 60)
        elif t == 150:
            b.set_state("happy", 9999)
            scene.speak(a, "bestie_hype", 70)
        elif t == 220:
            scene.speak(b, "bestie_shy" if "bestie_shy" in b.lines else "petted", 55)
        elif t == 280:                   # secret handshake
            scene.speak(a, "bestie_handshake", 45)
            a.spawn("star", 3)
        elif t == 320:
            scene.speak(b, "bestie_handshake" if "bestie_handshake" in b.lines else "petted", 45)
            b.spawn("star", 3)
        elif t == 370:
            scene.speak(a, "bestie_after", 60)
            a.spawn("heart", 3)
            b.spawn("heart", 3)
        elif t >= 430:
            scene.end()


INTERACTIONS = {
    "fist_bump": {"weight": 20, "start": start_fist_bump, "step": step_fist_bump},
    # weight can be a function of the two buddies: only with a bestie
    # walks_over: it can start from across the screen (she walks over to him)
    "bestie": {"weight": lambda a, b: 40 if a.bond(b) == "besties" else 0,
               "start": start_bestie, "step": step_bestie, "walks_over": True},
}


# ----------------------------------------------------------- menu & hooks --
def blow_bubble(buddy):
    if buddy.on_ground():
        buddy.drop_social()
        start_gum(buddy)


def go_skate(buddy):
    if buddy.on_ground():
        buddy.drop_social()
        start_skate(buddy)


MENU = [("Blow a bubble", blow_bubble), ("Go skate!", go_skate)]


def setup(buddy):
    buddy.mem["streak"], buddy.mem["last_pet"] = 0, -9999


def on_pet(buddy):
    """Cool about it... until you keep going."""
    m = buddy.mem
    m["streak"] = m["streak"] + 1 if buddy.app.tick - m["last_pet"] < 140 else 1
    m["last_pet"] = buddy.app.tick
    if m["streak"] >= 4:
        return {"line": "melt", "hearts": 4, "happy": 60, "ticks": 80}
    return {"line": "pet", "hearts": 2}


def on_event(buddy, event, other=None):
    if event == "dizzy_end":                   # shakes it off on her board
        start_skate(buddy)
        return True
    return False


def on_prop(buddy, prop):
    """Her parked board: after a while she goes back for it."""
    if prop.kind == "board" and prop.owner is buddy and prop.on_floor()             and prop.age > 600 and random.random() < 0.15:
        start_skate(buddy)
        return True
    return False
