"""État partagé (réunion + avatar) et diffusion aux pages web via Server-Sent Events."""

import json
import queue
import threading
import time


class Hub:
    """Garde l'état courant et le pousse à tous les clients SSE connectés."""

    def __init__(self, participants=6, rate=50.0, currency="EUR"):
        self._lock = threading.Lock()
        self._clients = set()
        self.meeting = {
            "participants": participants,
            "rate": rate,  # coût horaire moyen par personne
            "currency": currency,
            "running": False,
            "elapsed": 0.0,  # secondes de réunion
            "cost": 0.0,  # coût cumulé
            "started_at": None,  # dernier instant où elapsed/cost ont été calculés
        }
        self.avatar = {"expression": "neutre", "since": time.time()}
        self.transcript = []  # [(timestamp, texte)], seulement la dernière minute

    # --- clients SSE -------------------------------------------------------

    def subscribe(self):
        q = queue.Queue(maxsize=200)
        with self._lock:
            self._clients.add(q)
        # Premier envoi : l'état complet
        q.put(("meeting", self.meeting_snapshot()))
        q.put(("avatar", dict(self.avatar)))
        return q

    def unsubscribe(self, q):
        with self._lock:
            self._clients.discard(q)

    def publish(self, event, data):
        with self._lock:
            clients = list(self._clients)
        for q in clients:
            try:
                q.put_nowait((event, data))
            except queue.Full:
                pass  # client trop lent : on saute ce message

    # --- réunion -----------------------------------------------------------

    def _fold(self):
        """Intègre le temps écoulé depuis le dernier calcul (le coût suit les changements de participants)."""
        m = self.meeting
        now = time.time()
        if m["running"] and m["started_at"]:
            dt = now - m["started_at"]
            m["elapsed"] += dt
            m["cost"] += dt * m["participants"] * m["rate"] / 3600
        m["started_at"] = now if m["running"] else None

    def meeting_snapshot(self):
        with self._lock:
            self._fold()
            m = dict(self.meeting)
            m.pop("started_at", None)
            return m

    def update_meeting(self, data):
        with self._lock:
            self._fold()
            m = self.meeting
            if "participants" in data:
                m["participants"] = max(0, int(data["participants"]))
            if "rate" in data:
                m["rate"] = max(0.0, float(data["rate"]))
            if "currency" in data:
                m["currency"] = str(data["currency"])[:3].upper() or "EUR"
            action = data.get("action")
            if action == "toggle":
                action = "pause" if m["running"] else "start"
            if action == "start":
                m["running"] = True
            elif action == "pause":
                m["running"] = False
            elif action == "reset":
                m["elapsed"], m["cost"] = 0.0, 0.0
            self._fold()
        self.publish("meeting", self.meeting_snapshot())

    # --- avatar ------------------------------------------------------------

    def set_expression(self, expression, duration=None, source="auto"):
        self.avatar = {
            "expression": expression,
            "since": time.time(),
            "duration": duration,
            "source": source,
        }
        self.publish("avatar", dict(self.avatar))

    def add_transcript(self, text):
        now = time.time()
        with self._lock:
            self.transcript.append((now, text))
            self.transcript = [(t, s) for t, s in self.transcript if now - t < 60]
        self.publish("transcript", {"text": text})

    def recent_transcript(self, seconds=30):
        now = time.time()
        with self._lock:
            return " ".join(s for t, s in self.transcript if now - t < seconds)


def sse_format(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
