"""Nova: a cheerful android. She hovers on her glow, scans things with her
visor (including her friends), and breaks into little dances."""
import math
import random


# ------------------------------------------------------------------ states --
def start_hover(buddy):
    buddy.set_state("hover", random.randint(70, 120))
    buddy.say("hover", 40)


def tick_hover(buddy, world):
    progress = 1 - buddy.timer / buddy.state_len
    buddy.y = world.ground - math.sin(math.pi * progress) * 26
    buddy.x += 0.8 * buddy.facing
    if buddy.x <= world.lo or buddy.x >= world.hi:
        buddy.facing = -buddy.facing


def sprite_hover(buddy):
    return "blink" if buddy.blinking() else "stand"


def start_scan(buddy):
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
    buddy.set_state("scan", 60)
    buddy.say("scan", 55)


def tick_scan(buddy, world):
    if buddy.tick % 12 == 0:
        buddy.spawn("spark")                 # little sparks from her visor


def sprite_scan(buddy):
    return "scan" if (buddy.tick // 6) % 4 else "stand"


def start_dance(buddy):
    buddy.set_state("dance", random.randint(100, 160))
    buddy.say("dance", 50)


def tick_dance(buddy, world):
    beat = (buddy.tick // 6) % 2
    buddy.y = world.ground - (buddy.scale + 1 if beat else 0)    # little hops
    if buddy.tick % 12 == 0:
        buddy.facing = -buddy.facing                               # spin
    if buddy.tick % 15 == 0:
        buddy.spawn("note")


def sprite_dance(buddy):
    return "dance1" if (buddy.tick // 6) % 2 else "dance2"


STATES = {
    # floats: not snapped to the floor; glow: her hover glow is drawn under her
    "hover": {"weight": 12, "start": start_hover, "tick": tick_hover, "sprite": sprite_hover,
              "floats": True, "glow": True},
    "scan": {"weight": 12, "start": start_scan, "tick": tick_scan, "sprite": sprite_scan},
    "dance": {"weight": 12, "start": start_dance, "tick": tick_dance, "sprite": sprite_dance,
              "floats": True},
}


# ------------------------------------------------------------ with friends --
def start_scan_friend(scene):
    a, b = scene.a, scene.b
    a.face(b)
    b.face(a)
    a.set_state("scan", 9999)
    b.set_state("idle", 9999)
    key = "scan_" + b.kind
    scene.speak(a, key if key in a.lines else "scan_other", 55)


def step_scan_friend(scene):
    if scene.t == 60:
        scene.speak(scene.b, "scanned")
    elif scene.t >= 115:
        scene.end()


INTERACTIONS = {"scan": {"weight": 18, "start": start_scan_friend, "step": step_scan_friend}}
