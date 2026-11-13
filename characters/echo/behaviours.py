"""Echo: a self-aware little robot who is very attached to you. Her screen
glitches now and then, she stares at you, and she gets jealous when you pay
attention to another buddy: she sulks at you, and only storms over to scare
them off if it's someone she dislikes."""
import random


# ------------------------------------------------------------------ states --
def start_stare(buddy):
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
    buddy.set_state("idle", 90)
    buddy.say("watch", 60)


def sprite_jealous(buddy):
    return "jealous"


def start_heartbeat(buddy):
    """Her whole screen becomes a beating heart. For you."""
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
    buddy.set_state("heartbeat", random.randint(70, 110))
    buddy.say("heartbeat", 50)


def tick_heartbeat(buddy, world):
    if buddy.tick % 24 == 0:
        buddy.spawn("heart")


def sprite_heartbeat(buddy):
    return "heart" if buddy.tick % 24 in (0, 1, 2, 3, 7, 8, 9) else "heart_s"   # ba-dum


def start_buffer(buddy):
    """Loading... loading... (thinking about you)."""
    buddy.set_state("buffer", 80)
    buddy.say("buffer", 40)


def tick_buffer(buddy, world):
    if buddy.timer == 20:
        buddy.say("buffer_done", 50)
        buddy.spawn("heart", 2)


def sprite_buffer(buddy):
    if buddy.timer <= 20:
        return "happy"
    return ("load1", "load2", "load3")[(buddy.tick // 6) % 3]


STATES = {
    "stare": {"weight": 10, "start": start_stare},
    "heartbeat": {"weight": 5, "start": start_heartbeat, "tick": tick_heartbeat,
                  "sprite": sprite_heartbeat},
    "buffer": {"weight": 4, "start": start_buffer, "tick": tick_buffer, "sprite": sprite_buffer},
    "jealous": {"weight": 0, "sprite": sprite_jealous},     # only during a jealous scene
}


# ----------------------------------------------------------------- glitches --
def on_tick(buddy, world):
    if random.random() < 0.0008:                   # about once a minute
        buddy.glitch_t = 6
        smear(buddy)
    if buddy.state == "dizzy" and random.random() < 0.03:
        buddy.glitch_t = 4
    return False                                   # carry on as normal


def smear(buddy):
    """A glitch leaves a smear on your screen for a moment."""
    buddy.leave_mark("smear", x=buddy.cx() + random.uniform(-buddy.sw / 2, buddy.sw / 2),
                   y=buddy.y + random.uniform(0, buddy.sh * 0.6), life=70)


def on_event(buddy, event, other=None):
    if event == "chatter":
        buddy.glitch_t = 8
        smear(buddy)
    elif event == "dizzy":
        buddy.glitch_t = 12
    elif event == "attention_elsewhere":           # you petted / fed someone else
        if buddy.leaving or buddy.social or not buddy.on_ground():
            return False
        if buddy.state in ("sleep", "climb", "eat", "hover", "jealous"):
            return False
        if buddy.floor() != other.floor() or random.random() > 0.7:
            return False
        if buddy.relation(other) == "dislikes":
            buddy.start_scene("jealous", other)       # storms over and scares them off
        else:
            # a friend: no taking it out on them - she sulks at YOU instead
            buddy.drop_social()
            buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
            buddy.set_state("jealous", 70)
            buddy.say("jealous_you", 70, other=other)
            buddy.glitch_t = 6
        return True                                 # one jealous buddy is enough
    return False


# ------------------------------------------------------------ with friends --
def start_jealous(scene):
    scene.a.set_state("idle", 9999)
    scene.a.face(scene.b)
    scene.wait = 20                                 # let the hearts show first


def step_jealous(scene):
    a, b = scene.a, scene.b
    if scene.phase == 0:
        scene.wait -= 1
        if scene.wait <= 0:
            scene.speak(a, "jealous", 70)
            a.glitch_t = 6
            scene.approach()
            scene.phase = 1
    elif scene.phase == 1:
        if a.state != "goto":
            a.face(b)
            b.face(a)
            a.set_state("jealous", 9999)
            scene.speak(b, "scared", 45)
            b.set_state("flee", 9999)
            scene.phase, scene.mark = 2, scene.t
        elif scene.t > 400:
            scene.end()
    elif scene.t == scene.mark + 45:
        b.set_state("idle", 9999)
        b.face(a)
        a.set_state("happy", 9999)
        a.facing = 1 if a.pointer()[0] > a.cx() else -1
        a.spawn("heart", 2)
        scene.speak(a, "after_jealous", 60)
    elif scene.t >= scene.mark + 100:
        scene.end()


# weight 0: never picked at random, only started by on_event above
INTERACTIONS = {"jealous": {"weight": 0, "start": start_jealous, "step": step_jealous}}
