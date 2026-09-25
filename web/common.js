// Code partagé entre les pages : paramètres d'URL, connexion au serveur, calcul du coût.

const params = new URLSearchParams(location.search);

function param(name, fallback) {
  const v = params.get(name);
  return v === null || v === "" ? fallback : v;
}

// Mode serveur : la page est servie par `python -m visiobot`. Sinon (fichier ouvert directement
// dans OBS), tout tourne en local avec les paramètres d'URL.
const SERVER = location.protocol.startsWith("http") && param("local", "0") !== "1";

function connect(handlers) {
  if (!SERVER) return;
  const es = new EventSource("/events");
  for (const [event, fn] of Object.entries(handlers)) {
    es.addEventListener(event, (e) => fn(JSON.parse(e.data)));
  }
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

// Réunion : on garde un instantané + l'heure locale de réception, et on extrapole.
class Meeting {
  constructor() {
    this.set({
      participants: +param("n", 6),
      rate: +param("taux", 50),
      currency: param("devise", "EUR"),
      running: param("auto", "1") === "1",
      elapsed: 0,
      cost: 0,
    });
  }
  set(snapshot) {
    this.s = { ...snapshot };
    this.at = performance.now();
  }
  _fold() {
    const now = performance.now();
    if (this.s.running) {
      const dt = (now - this.at) / 1000;
      this.s.elapsed += dt;
      this.s.cost += (dt * this.s.participants * this.s.rate) / 3600;
    }
    this.at = now;
  }
  get elapsed() { this._fold(); return this.s.elapsed; }
  get cost() { this._fold(); return this.s.cost; }
  get perMinute() { return (this.s.participants * this.s.rate) / 60; }
  // Changement local (mode sans serveur) ou envoyé au serveur.
  update(change) {
    if (SERVER) return api("/api/meeting", change);
    this._fold();
    if ("participants" in change) this.s.participants = Math.max(0, change.participants);
    if ("rate" in change) this.s.rate = Math.max(0, change.rate);
    let action = change.action;
    if (action === "toggle") action = this.s.running ? "pause" : "start";
    if (action === "start") this.s.running = true;
    if (action === "pause") this.s.running = false;
    if (action === "reset") { this.s.elapsed = 0; this.s.cost = 0; }
  }
}

function money(value, currency) {
  try {
    return new Intl.NumberFormat("fr-FR", { style: "currency", currency }).format(value);
  } catch {
    return value.toFixed(2) + " " + currency;
  }
}

function duration(seconds) {
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const sec = String(s % 60).padStart(2, "0");
  return h ? `${h}:${m}:${sec}` : `${m}:${sec}`;
}

// Charge une image si elle existe, sinon garde le dessin SVG de secours.
function tryImage(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

// Raccourcis clavier (dans OBS : clic droit sur la source > Interagir).
function meetingKeys(meeting) {
  window.addEventListener("keydown", (e) => {
    const p = meeting.s.participants;
    if (e.key === " ") meeting.update({ action: "toggle" });
    else if (e.key === "+" || e.key === "ArrowUp") meeting.update({ participants: p + 1 });
    else if (e.key === "-" || e.key === "ArrowDown") meeting.update({ participants: p - 1 });
    else if (e.key.toLowerCase() === "r") meeting.update({ action: "reset" });
    else return;
    e.preventDefault();
  });
}
