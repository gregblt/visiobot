"""Choix de la réaction de l'avatar à partir de ce qui se dit dans la visio."""

import json
import re
import threading
import time
import unicodedata
import urllib.request


def normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")  # retire les accents
    return text.replace("’", "'")


class Reactor:
    def __init__(self, hub, config):
        self.hub = hub
        av = config["avatar"]
        self.expressions = av["expressions"]
        self.reaction_seconds = av["reaction_seconds"]
        self.bored_after = av["bored_after_seconds"]
        self.asleep_after = av["asleep_after_seconds"]
        self.llm = config["llm"]
        self.rules = []
        for rule in av["rules"]:
            words = [re.escape(normalize(k)) for k in rule["keywords"]]
            self.rules.append((rule["expression"], re.compile(r"\b(" + "|".join(words) + r")\b")))
        names = [re.escape(normalize(n)) for n in av.get("my_name", []) if n]
        if names:
            self.rules.insert(0, ("surpris", re.compile(r"\b(" + "|".join(names) + r")\b")))
        self.last_reaction = time.time()

    def react(self, expression, source="auto"):
        if expression not in self.expressions:
            return
        self.last_reaction = time.time()
        self.hub.set_expression(expression, self.reaction_seconds, source)

    def on_text(self, text):
        """Appelé pour chaque phrase transcrite : réaction immédiate par mots-clés."""
        norm = normalize(text)
        for expression, pattern in self.rules:
            if pattern.search(norm):
                self.react(expression, "mot-cle")
                return True
        return False

    # --- boucle de fond : ennui, sommeil et LLM --------------------------------

    def _ask_llm(self, transcript):
        prompt = (
            "Tu pilotes l'avatar d'un participant à une visio de travail. Voici ce qui vient d'être dit :\n"
            f"\"\"\"{transcript}\"\"\"\n"
            f"Choisis la réaction la plus drôle mais crédible parmi : {', '.join(self.expressions)}.\n"
            'Réponds uniquement en JSON : {"expression": "..."}'
        )
        body = json.dumps({"model": self.llm["model"], "prompt": prompt, "format": "json", "stream": False}).encode()
        req = urllib.request.Request(self.llm["url"], body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            answer = json.loads(json.loads(resp.read())["response"])
        return str(answer.get("expression", "")).strip().lower()

    def _loop(self):
        last_llm = 0.0
        while True:
            time.sleep(1)
            now = time.time()
            idle = now - self.last_reaction
            current = self.hub.avatar["expression"]
            if idle > self.asleep_after and current != "endormi":
                self.hub.set_expression("endormi", None, "ennui")
            elif self.bored_after < idle <= self.asleep_after and current not in ("ennuye", "endormi"):
                self.hub.set_expression("ennuye", None, "ennui")

            if self.llm["enabled"] and now - last_llm > self.llm["every_seconds"] and idle > self.reaction_seconds:
                last_llm = now
                transcript = self.hub.recent_transcript(30)
                if transcript:
                    try:
                        self.react(self._ask_llm(transcript), "llm")
                    except Exception as exc:  # Ollama absent, JSON invalide...
                        print(f"[llm] {exc}")

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()
