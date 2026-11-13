"""Milo's power-up: fact searching. While Milo is out, a background thread
picks up a few new fun facts every 10 minutes from a free random-fact site,
filters them, and saves them in learned_facts.json next to this file.
Only downloads; nothing about you is sent."""
import json
import re
import threading
import time
import urllib.request
from pathlib import Path

FACTS_FILE = Path(__file__).with_name("learned_facts.json")
FACT_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
FACT_AGENT = "DesktopBuddy/1.0 (personal desktop toy; python-urllib)"
FACT_EVERY_S = 600            # look for new facts every 10 minutes
FACT_MAX_LEN = 110            # longest fact that still fits in Milo's bubble
FACT_GRIM = re.compile(
    r"\b(kill\w*|die[sd]?|dying|dead|deaths?|suicide|rape\w*|nazis?|drugs?|murder\w*|"
    r"blood\w*|guns?|naked|porn\w*|sex\w*|wars?|bomb\w*|massacre\w*|terror\w*|"
    r"execut\w*|assassinat\w*|shot|shoot\w*|genocide|victims?|weapons?|"
    r"prison\w*|hang(ed|ing)|breasts?|penis\w*|vagina\w*|orgasm\w*|nude|toilet paper)\b", re.I)
# The site has a few well-known myths in it; Milo won't repeat these.
FACT_MYTHS = re.compile(
    r"da vinci.*scissors|great wall.*(space|moon)|goldfish.*memory|10 ?% of .*brain|"
    r"bulls?.*(red|colou?r)|lightning never|bats are blind|swallow.*spiders|"
    r"camels?.*(store|water in).*hump|hair.*(grow|growing) after death|"
    r"tongue.*(map|zones)|ostrich.*(head|sand)|einstein.*fail\w* math", re.I)


def clean_fact(text):
    """Keep only short, plain, family-friendly facts that fit in a bubble."""
    text = " ".join(str(text).split()).replace("`", "'")
    for fancy, plain in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"),
                         ("–", "-"), ("—", " - "), ("…", "...")):
        text = text.replace(fancy, plain)
    if not (20 <= len(text) <= FACT_MAX_LEN) or not text.isascii():
        return None
    if FACT_GRIM.search(text) or FACT_MYTHS.search(text):
        return None
    return text if text[-1] in ".!?" else text + "."


def load_learned():
    try:
        return [f for f in json.loads(FACTS_FILE.read_text())["learned"] if isinstance(f, str)]
    except Exception:
        return []


class FactSearch:
    def __init__(self, facts, kind):
        self.facts = facts            # the character's roster; new facts are added to it
        self.kind = kind
        self.learned = load_learned()
        known = {f.lower() for f in facts}
        facts.extend(f for f in self.learned if f.lower() not in known)
        self.inbox, self.fresh = [], []

    def start(self, app):
        threading.Thread(target=self.worker, args=(app,), daemon=True).start()

    def worker(self, app):
        """Background thread: up to 3 new facts every 10 minutes while he's out."""
        time.sleep(30)
        while True:
            if any(q.kind == self.kind for q in list(app.buddies)):
                known = {f.lower() for f in self.facts}
                got = 0
                for _ in range(12):
                    try:
                        req = urllib.request.Request(FACT_URL, headers={
                            "User-Agent": FACT_AGENT, "Accept": "application/json"})
                        with urllib.request.urlopen(req, timeout=8) as r:
                            text = json.loads(r.read().decode("utf-8")).get("text", "")
                    except Exception:
                        break                       # offline: try again next round
                    fact = clean_fact(text)
                    if fact and fact.lower() not in known:
                        known.add(fact.lower())
                        self.inbox.append(fact)
                        got += 1
                        if got >= 3:
                            break
            time.sleep(FACT_EVERY_S)

    def absorb(self):
        """Main thread: add downloaded facts to the roster and save them.
        Returns the new facts."""
        new = []
        known = {f.lower() for f in self.facts}
        while self.inbox:
            fact = clean_fact(self.inbox.pop(0))
            if fact and fact.lower() not in known:
                known.add(fact.lower())
                self.facts.append(fact)
                self.learned.append(fact)
                self.fresh.append(fact)
                new.append(fact)
        if new:
            self.learned = self.learned[-500:]
            try:
                FACTS_FILE.write_text(json.dumps({"learned": self.learned}, indent=1))
            except Exception:
                pass
        return new
