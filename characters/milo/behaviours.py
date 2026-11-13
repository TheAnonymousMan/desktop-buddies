"""Milo: a nerd in a lab coat who blurts out fun facts every minute or two,
shares them with friends, and keeps learning new ones (see fact_search.py)."""
import random

from .fact_search import FactSearch

search = None          # started once when the app starts (see on_app_start)


# ---------------------------------------------------------- the app itself --
def on_app_start(app, ch):
    """Called once when the buddies app starts, for each character type."""
    global search
    search = FactSearch(ch["facts"], ch["name"])
    search.start(app)


def on_app_tick(app, ch):
    """Called every 2 seconds: pick up anything the search found."""
    new = search.absorb() if search else []
    if new:
        nerds = [q for q in app.buddies if q.kind == ch["name"] and q.on_ground() and not q.social]
        if nerds:
            nerds[0].say(f"Ooh! I just learned {len(new)} new fact{'s' if len(new) > 1 else ''}!", 70)


def next_fact(buddy):
    fresh = search.fresh if search else []
    if fresh and random.random() < 0.7:            # brand-new ones first
        fact = fresh.pop(0)
        return ("I just learned this! " + fact) if len(fact) <= 85 else fact
    m = buddy.mem
    if not m["deck"]:                              # shuffle, so facts don't repeat soon
        m["deck"] = random.sample(buddy.ch["facts"], len(buddy.ch["facts"]))
    return random.choice(["Fun fact! ", "Did you know? ", ""]) + m["deck"].pop()


def tell_fact(buddy):
    if not buddy.on_ground() or buddy.state == "climb":
        return
    buddy.drop_social()
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
    buddy.set_state("fact", 120)
    buddy.say(next_fact(buddy), 120)
    buddy.spawn("idea")
    buddy.mem["timer"] = random.randint(1200, 2400)   # next one in 1-2 minutes


# ------------------------------------------------------------------ hooks --
def setup(buddy):
    buddy.mem["timer"] = random.randint(300, 900)     # first fact within ~15-45 s
    buddy.mem["deck"] = []


def on_tick(buddy, world):
    if world.busy:
        return False
    buddy.mem["timer"] -= 1
    if buddy.mem["timer"] <= 0 and buddy.state in ("idle", "walk", "loaf"):
        tell_fact(buddy)
        return True
    return False


def sprite_fact(buddy):
    return "fact" if (buddy.tick // 10) % 3 else "stand"


STATES = {"fact": {"weight": 0, "sprite": sprite_fact}}


def on_event(buddy, event, other=None):
    if event == "ate":                     # finished his coffee: leaves the mug about
        buddy.drop_prop("mug", life=2400)
        buddy.say("mug_down", 50)
    return False
MENU = [("Tell me a fact", tell_fact)]


# ------------------------------------------------------------ with friends --
def start_fact(scene):
    a, b = scene.a, scene.b
    a.face(b)
    b.face(a)
    a.set_state("fact", 9999)
    b.set_state("idle", 9999)
    b.bubble = None
    a.say(next_fact(a), 110)
    a.spawn("idea")
    a.mem["timer"] = random.randint(1200, 2400)


def step_fact(scene):
    if scene.t == 100:
        scene.speak(scene.b, "fact_reply", 50)
        scene.a.set_state("happy", 9999)
    elif scene.t >= 150:
        scene.end()


INTERACTIONS = {"fact": {"weight": 30, "start": start_fact, "step": step_fact}}
