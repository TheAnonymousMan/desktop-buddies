"""Mochi: a tsundere cat. She scratches your screen, sneaks up to sit near
your cursor (with her back to you), and only admits she likes pets after
you've kept going for a while."""
import random


# ------------------------------------------------------------------ states --
def start_scratch(buddy):
    buddy.set_state("scratch", 70)
    buddy.say("scratch", 50)


def tick_scratch(buddy, world):
    if buddy.tick % 12 == 0:
        buddy.spawn("scratch")              # claw marks that fade


def start_sneak(buddy):
    """Walk over to your cursor, then sit next to it facing away."""
    px, py = buddy.pointer()
    if buddy.app.floor_at(px, py) != buddy.floor():
        buddy.set_state("idle", 40)
        return
    lo, hi = buddy.limits(buddy.floor())
    side = -1 if px - buddy.sw / 2 > buddy.x else 1        # stop on our side of the cursor
    buddy.walk_to(max(lo, min(hi, px - buddy.sw / 2 + side * 120)), then=sit_facing_away)


def sit_facing_away(buddy):
    buddy.facing = -1 if buddy.pointer()[0] > buddy.cx() else 1
    buddy.set_state("loaf", random.randint(140, 220))
    buddy.say("sneak", 60)


# ------------------------------------------------------------- sit, groom --
def start_sit(buddy):
    """Sits up neatly, tail curled, and flicks it now and then."""
    buddy.set_state("sit", random.randint(90, 180))
    if random.random() < 0.3:
        buddy.say("sit", 45)


def sprite_sit(buddy):
    if buddy.blinking():
        return "sit_blink"
    return "sit_b" if (buddy.tick // 7) % 6 == 0 else "sit"     # tail flick


def start_groom(buddy):
    buddy.set_state("groom", random.randint(60, 100))
    if random.random() < 0.5:
        buddy.say("groom", 45)


def sprite_groom(buddy):
    return "groom1" if (buddy.tick // 6) % 2 == 0 else "groom2"    # lick, lick


STATES = {
    "sit": {"weight": 6, "start": start_sit, "sprite": sprite_sit},
    "groom": {"weight": 5, "start": start_groom, "sprite": sprite_groom,
              "bob": lambda buddy: buddy.hop(0.3, 6)},
    # climb_pose: drawn clinging to the screen edge, like when she climbs
    "scratch": {"weight": 7, "start": start_scratch, "tick": tick_scratch, "climb_pose": True},
    "sneak": {"weight": 7, "start": start_sneak},
}


# ----------------------------------------------------------------- reactions --
def setup(buddy):
    buddy.mem["pet_streak"], buddy.mem["last_pet"] = 0, -9999


def on_pet(buddy):
    """Grumpy at first; pets close together add up until she melts."""
    m = buddy.mem
    m["pet_streak"] = m["pet_streak"] + 1 if buddy.app.tick - m["last_pet"] < 120 else 1
    m["last_pet"] = buddy.app.tick
    if m["pet_streak"] >= 3:
        return {"line": "pet_melt", "hearts": 3, "happy": 60, "ticks": 70}
    return {"line": "pet", "hearts": 1}


def on_event(buddy, event, other=None):
    if event == "dizzy_end":              # sulks with her back to you
        buddy.facing = -1 if buddy.pointer()[0] > buddy.cx() else 1
        buddy.set_state("loaf", 160)
        return True
    return False


# ------------------------------------------------------------------ props --
def on_prop(buddy, prop):
    """She bats at things lying around. Near the edge of the screens, she
    knocks them right off. (Every cat's favourite game.)"""
    if not prop.on_floor() or random.random() > 0.25:
        return False
    if prop.data.get("batted", -9999) > buddy.app.tick - 300:
        return False
    side = 1 if prop.cx() > buddy.cx() else -1
    lo, hi = buddy.limits(buddy.floor())
    x = prop.cx() - side * (buddy.sw * 0.45 + prop.w * 0.5) - buddy.sw / 2
    buddy.mem["prop"] = prop
    buddy.walk_to(max(lo, min(hi, x)), then=bat)
    return True


def bat(buddy):
    prop = buddy.mem.pop("prop", None)
    if prop is None or prop.gone or abs(prop.cx() - buddy.cx()) > buddy.sw * 1.2:
        return
    buddy.facing = 1 if prop.cx() > buddy.cx() else -1
    prop.data["batted"] = buddy.app.tick
    vl, vt, vr, vb = buddy.app.virtual
    edge = vr - prop.cx() if buddy.facing > 0 else prop.cx() - vl
    if edge < 400:                                  # close to the edge: off it goes
        prop.kick(buddy.facing * 16, -7, off_edge=True)
        buddy.say("knock_off", 60)
    else:
        prop.kick(buddy.facing * random.uniform(9, 14), -6)
        buddy.say("bat", 45)
    buddy.set_state("happy", 25)
