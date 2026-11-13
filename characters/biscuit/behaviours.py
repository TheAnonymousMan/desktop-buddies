"""Biscuit: an overeager golden retriever who loves everyone. If you ignore
him for a while he goes round every buddy asking for pets, then comes to you.
He gets the zoomies (leaving muddy paw prints), plays fetch with his ball,
and he LOVES being shaken."""
import random


# ------------------------------------------------------------------ states --
def start_zoomies(buddy):
    buddy.set_state("zoomies", random.randint(60, 100))
    buddy.say("zoomies", 40)


def tick_zoomies(buddy, world):
    buddy.x += 6 * buddy.facing
    if buddy.x <= world.lo or buddy.x >= world.hi or random.random() < 0.02:
        buddy.facing = -buddy.facing
    if buddy.tick % 7 == 0:                            # muddy paw prints behind him
        buddy.leave_mark("paw", x=buddy.cx() - buddy.facing * buddy.sw * 0.3,
                       y=buddy.y + buddy.sh - buddy.scale * 2, life=160)


def sprite_zoomies(buddy):
    return buddy.walk_frame(fast=True)


def start_play_ball(buddy):
    """Gets his ball out and gives it a kick (then fetches it)."""
    if my_ball(buddy):
        buddy.set_state("idle", 20)
        return
    buddy.drop_prop("ball", vx=buddy.facing * random.uniform(7, 11), vy=-7, life=2400)
    buddy.say("ball", 40)
    buddy.set_state("happy", 20)


# ----------------------------------------------------- sit nicely, beg --
def start_sit(buddy):
    """Sits nicely, like a good boy. Tail going."""
    buddy.set_state("sit", random.randint(80, 160))
    if random.random() < 0.3:
        buddy.say("sit", 45)


def sprite_sit(buddy):
    if buddy.blinking():
        return "sit_blink"
    return "sit_b" if (buddy.tick // 4) % 2 else "sit"          # wag wag


def beg_pose(buddy, ticks=120):
    """Up on his haunches, paws going, puppy eyes."""
    buddy.set_state("beg", ticks)


def sprite_beg(buddy):
    if buddy.blinking():
        return "beg_blink"
    return "beg1" if (buddy.tick // 6) % 2 == 0 else "beg2"


def walk_to_you(buddy, then):
    px, py = buddy.pointer()
    if buddy.app.floor_at(px, py) != buddy.floor():
        then(buddy)
        return
    lo, hi = buddy.limits(buddy.floor())
    buddy.walk_to(max(lo, min(hi, px - buddy.sw / 2)), then=then, speed=4)


def beg_you(buddy):
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
    beg_pose(buddy, 160)
    buddy.say("beg_you", 60)


def beg_treat(buddy):
    buddy.facing = 1 if buddy.pointer()[0] > buddy.cx() else -1
    beg_pose(buddy, 160)
    buddy.say("beg_treat", 60)


STATES = {"sit": {"weight": 6, "start": start_sit, "sprite": sprite_sit},
          "beg": {"weight": 0, "sprite": sprite_beg,
                  "bob": lambda buddy: buddy.hop(0.8, 6)},          # paws going
          "zoomies": {"weight": 8, "start": start_zoomies, "tick": tick_zoomies,
                      "sprite": sprite_zoomies,
                      "bob": lambda buddy: buddy.hop(2.5, 5)},     # big springy bounds
          "play_ball": {"weight": 4, "start": start_play_ball}}


# ------------------------------------------------------------------- fetch --
def my_ball(buddy):
    return next((pr for pr in buddy.app.props if pr.kind == "ball" and pr.owner is buddy), None)


def on_prop(buddy, prop):
    """A ball! Go get it, and bring it to you."""
    if prop.kind != "ball" or prop.carried_by or not prop.on_floor():
        return False
    if buddy.mem.get("ball") or random.random() > 0.6:
        return False
    buddy.mem["ball"], buddy.mem["tries"] = prop, 0
    buddy.say("ball", 40)
    go_get(buddy)
    return True


def go_get(buddy):
    ball = buddy.mem.get("ball")
    if ball is None or ball.gone:
        buddy.mem["ball"] = None
        return
    lo, hi = buddy.limits(buddy.floor())
    buddy.walk_to(max(lo, min(hi, ball.cx() - buddy.sw / 2)), then=grab, speed=5.5)   # runs for it


def grab(buddy):
    ball = buddy.mem.get("ball")
    if ball is None or ball.gone or ball.carried_by:
        buddy.mem["ball"] = None
        return
    if abs(ball.cx() - buddy.cx()) > buddy.sw * 0.6:     # it rolled: chase it again
        buddy.mem["tries"] += 1
        if buddy.mem["tries"] < 4:
            go_get(buddy)
        else:
            buddy.mem["ball"] = None
        return
    ball.carry(buddy)
    px, py = buddy.pointer()
    if buddy.app.floor_at(px, py) == buddy.floor():     # bring it to you
        lo, hi = buddy.limits(buddy.floor())
        buddy.walk_to(max(lo, min(hi, px - buddy.sw / 2)), then=give, speed=4)       # trots back
    else:
        give(buddy)


def give(buddy):
    ball = buddy.mem.get("ball")
    buddy.mem["ball"] = None
    if ball is not None and not ball.gone:
        ball.drop()
        ball.data["batted"] = buddy.app.tick          # (Mochi: leave it a moment)
    buddy.set_state("happy", 40)
    buddy.say("fetch_done", 60)
    buddy.spawn("heart", 2)
    buddy.last_attention = buddy.app.tick


def throw_ball(buddy):
    """Menu: throw his ball from where your mouse is."""
    px, py = buddy.pointer()
    ball = my_ball(buddy)
    if ball is None:
        ball = buddy.drop_prop("ball", x=px, y=py, life=2400)
    else:
        ball.drop()
        ball.x, ball.y = px - ball.w / 2, py - ball.h / 2
    if ball:
        ball.age = 0
        ball.kick(random.choice((-1, 1)) * random.uniform(6, 12), -9)


MENU = [("Throw a ball", throw_ball)]


# ----------------------------------------------------------------- begging --
def setup(buddy):
    buddy.mem["queue"] = []          # friends (and finally you) to ask for pets
    buddy.mem["ball"] = None         # the ball he's fetching


def on_tick(buddy, world):
    ball = buddy.mem.get("ball")
    if ball is not None and buddy.state != "goto":      # fetch got interrupted
        if ball.carried_by is buddy:
            give(buddy)                                 # just drop it here
        buddy.mem["ball"] = None
    if world.busy or buddy.state not in ("idle", "walk", "loaf"):
        return False
    queue = buddy.mem["queue"]
    if queue:
        friend = queue.pop(0)
        if friend == "you":                         # finally, beg the human
            buddy.say("come", 40)
            walk_to_you(buddy, beg_you)
            buddy.last_attention = buddy.app.tick - 600  # asks again in ~1 min
            return True
        if friend in buddy.app.buddies and friend.on_ground() and not friend.social \
                and not friend.leaving and friend.state != "climb" \
                and friend.floor() == buddy.floor():
            buddy.start_scene("beg", friend)
            return True
    elif buddy.hunger > 55 and random.random() < 0.002:  # treat? treat??
        walk_to_you(buddy, beg_treat)
        return True
    elif buddy.app.tick - buddy.last_attention > 1800:   # ignored for ~90 s
        friends = [q for q in buddy.app.buddies if q is not buddy and not q.leaving
                   and q.floor() == buddy.floor()]
        random.shuffle(friends)
        buddy.mem["queue"] = friends + ["you"]
        buddy.say("lonely", 50)
        return True
    return False


def on_event(buddy, event, other=None):
    if event == "fs_flee":                          # a fullscreen app: plans are off
        buddy.mem["queue"] = []
        buddy.mem["ball"] = None
    elif event == "dizzy_end":                      # he loved it
        buddy.spawn("heart", 3)
        buddy.set_state("zoomies", 80)
        return True
    return False


# ------------------------------------------------------------ with friends --
def start_beg(scene):
    scene.b.set_state("idle", 9999)
    scene.approach()


def step_beg(scene):
    a, b = scene.a, scene.b
    if scene.phase == 0:
        if a.state != "goto":
            a.face(b)
            b.face(a)
            beg_pose(a, 9999)                        # sits up and begs
            scene.speak(a, "beg", 45)
            scene.phase, scene.mark = 1, scene.t
        elif scene.t > 400:
            scene.end()
    elif scene.t == scene.mark + 45:
        b.set_state("happy", 9999)
        scene.speak(b, "pet_other", 45)
        a.spawn("heart", 3)
    elif scene.t == scene.mark + 85:
        a.set_state("happy", 9999)                   # wag wag wag
        scene.speak(a, "petted", 45)
        a.spawn("heart", 2)
    elif scene.t >= scene.mark + 120:
        scene.end()
        a.social_cd = 0                              # straight on to the next friend


INTERACTIONS = {"beg": {"weight": 0, "start": start_beg, "step": step_beg}}
