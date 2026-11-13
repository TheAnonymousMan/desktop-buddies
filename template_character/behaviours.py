"""Pip's behaviours: an example of every hook, ready to change or delete.

Everything in this file is optional - a character works with no
behaviours.py at all (it just does the built-in things: walking, napping,
climbing, chatting, playing tag, eating...). See CHARACTERS.md for details.
"""
import random


# ======================================================== your own moves ==
# Each move: start(buddy) when it's picked, tick(buddy, world) every frame while
# it lasts, sprite(buddy) for what to draw. When buddy.timer runs out the engine
# picks the next move by itself.

def start_bounce(buddy):
    buddy.set_state("bounce", random.randint(60, 100))   # name, how many frames (20 = 1 second)
    buddy.say("bounce", 40)
    buddy.spawn("sparkle", 2)                            # its own effect (source.py EFFECTS)


def tick_bounce(buddy, world):
    hop = abs((buddy.tick % 16) - 8)                     # 8, 7 ... 0 ... 7, 8
    if hop == 8:                                       # each landing leaves a little drip
        buddy.leave_mark("drip", x=buddy.cx(), y=world.ground + buddy.sh - 4, life=60)
    buddy.y = world.ground - (8 - hop) * 3               # up and down
    buddy.x += 1.5 * buddy.facing
    if buddy.x <= world.lo or buddy.x >= world.hi:         # turn around at the screen edge
        buddy.facing = -buddy.facing


def sprite_bounce(buddy):
    on_floor = buddy.y >= buddy.floor()[3] - buddy.sh - 1
    return "squish" if on_floor else "happy"


STATES = {
    "bounce": {
        "weight": 10,          # how often it's picked (walk is 40); 0 = only when you start it
        "start": start_bounce,
        "tick": tick_bounce,
        "sprite": sprite_bounce,
        "floats": True,        # don't snap to the floor (needed for hopping)
        # "glow": True,        # draw a glow underneath
        # "climb_pose": True,  # draw it clinging to the screen edge
    },
}


# ================================================ scenes with other buddies ==
# scene.a is this buddy, scene.b the friend. scene.t counts frames; phase and
# mark are yours to use. speak(buddy, line_key), approach() (a walks up to b),
# end() when done.

def start_high_five(scene):
    scene.b.set_state("idle", 9999)
    scene.approach()


def step_high_five(scene):
    a, b = scene.a, scene.b
    if scene.phase == 0:
        if a.state != "goto":                  # arrived
            a.face(b)
            b.face(a)
            a.set_state("happy", 9999)
            b.set_state("happy", 9999)
            a.say("High five!", 40)            # a key from lines, or plain text
            a.spawn("star")
            scene.phase, scene.mark = 1, scene.t
        elif scene.t > 300:
            scene.end()
    elif scene.t == scene.mark + 30:
        scene.speak(b, "petted")
    elif scene.t >= scene.mark + 70:
        scene.end()


INTERACTIONS = {
    "high_five": {"weight": 15, "start": start_high_five, "step": step_high_five},
}


# ============================================================ menu items ==
def do_a_bounce(buddy):
    if buddy.on_ground():
        buddy.drop_social()
        start_bounce(buddy)


def drop_pebble(buddy):
    """Props are real objects: they fall, roll, and you can throw them."""
    buddy.drop_prop("pebble", vx=buddy.facing * 6, vy=-6)


MENU = [("Bounce!", do_a_bounce), ("Drop a pebble", drop_pebble)]   # extra right-click items


# ================================================================= hooks ==
def setup(buddy):
    """Once per buddy. Keep your own notes in buddy.mem."""
    buddy.mem["pets_today"] = 0


def on_pet(buddy):
    """You clicked to pet it. Return None for the normal reaction, or a dict:
    line (lines key or text), hearts, happy (frames), ticks (bubble time)."""
    buddy.mem["pets_today"] += 1
    if buddy.mem["pets_today"] % 10 == 0:
        return {"line": f"That's {buddy.mem['pets_today']} pets today!", "hearts": 5}
    return None


def on_prop(buddy, prop):
    """A prop lying near it (now and then). Return True if it does something.
    Here: it nudges pebbles along."""
    if prop.kind == "pebble" and prop.on_floor() and random.random() < 0.1:
        buddy.walk_to(prop.cx() - buddy.sw / 2, then=lambda p: prop.kick(p.facing * 6, -3))
        return True
    return False


def on_tick(buddy, world):
    """Every frame while on the ground. Return True to skip the normal
    behaviour this frame (you're handling it)."""
    return False


def on_event(buddy, event, other=None):
    """Things that happen. Return True if you handled it (where it matters):
      "chatter"              it just said something idly
      "dizzy"                it was shaken and is now dizzy
      "dizzy_end"            dizziness wore off (True = you chose what's next)
      "fs_flee"              it's running away from a fullscreen app
      "attention_elsewhere"  you petted or fed `other` (True = stop telling the rest)
    """
    if event == "dizzy_end":
        buddy.spawn("heart", 2)
        start_bounce(buddy)                     # shakes it off with a bounce
        return True
    return False


# Called once when the app starts / every 2 seconds, with the character's
# settings (ch). Good for background work - see milo/fact_search.py.
# def on_app_start(app, ch): ...
# def on_app_tick(app, ch): ...
