"""Petit serveur HTTP local : sert les pages web et diffuse l'état en SSE."""

import json
import mimetypes
import queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .state import sse_format

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
AVATAR_DIR = ROOT / "avatar"
EXPRESSION_EXTS = (".png", ".webp", ".gif", ".jpg", ".jpeg")


def make_handler(hub, config):
    class Handler(BaseHTTPRequestHandler):
        server_version = "visiobot"

        def log_message(self, *args):
            pass  # silencieux

        # --- utilitaires ---------------------------------------------------

        def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data, code=200):
            self._send(code, json.dumps(data, ensure_ascii=False).encode(), "application/json")

        def _file(self, base, rel):
            path = (base / rel).resolve()
            if base.resolve() not in path.parents or not path.is_file():
                return self._send(404, b"introuvable")
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self._send(200, path.read_bytes(), ctype)

        def _body(self):
            length = int(self.headers.get("Content-Length") or 0)
            if not length:
                return {}
            try:
                return json.loads(self.rfile.read(length))
            except ValueError:
                return {}

        # --- routes --------------------------------------------------------

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self.send_response(302)
                self.send_header("Location", "/control.html")
                self.end_headers()
            elif path == "/events":
                self._events()
            elif path == "/api/state":
                self._json({"meeting": hub.meeting_snapshot(), "avatar": hub.avatar})
            elif path == "/api/config":
                self._json(self._public_config())
            elif path.startswith("/expressions/"):
                self._file(AVATAR_DIR / "expressions", path[len("/expressions/"):])
            else:
                self._file(WEB_DIR, path.lstrip("/"))

        def do_POST(self):
            path = urlparse(self.path).path
            data = self._body()
            if path == "/api/meeting":
                hub.update_meeting(data)
                self._json(hub.meeting_snapshot())
            elif path == "/api/react":
                expr = data.get("expression", "neutre")
                hub.set_expression(expr, data.get("duration"), source="manuel")
                self._json({"ok": True})
            else:
                self._send(404, b"introuvable")

        def _public_config(self):
            av = config["avatar"]
            files = {}
            exp_dir = AVATAR_DIR / "expressions"
            if exp_dir.is_dir():
                for f in sorted(exp_dir.iterdir()):
                    if f.suffix.lower() in EXPRESSION_EXTS:
                        files.setdefault(f.stem, f.name)
            assets_dir = WEB_DIR / "assets"
            assets = sorted(f.name for f in assets_dir.iterdir() if f.is_file()) if assets_dir.is_dir() else []
            return {
                "assets": assets,
                "expressions": av["expressions"],
                "files": files,
                "reaction_seconds": av["reaction_seconds"],
                "talk_threshold": av["talk_threshold"],
                "krabs_thresholds": config["meeting"]["krabs_thresholds"],
            }

        def _events(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q = hub.subscribe()
            try:
                self.wfile.write(b"retry: 2000\n\n")
                while True:
                    try:
                        event, data = q.get(timeout=15)
                        self.wfile.write(sse_format(event, data))
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                hub.unsubscribe(q)

    return Handler


def serve(hub, config, host, port):
    httpd = ThreadingHTTPServer((host, port), make_handler(hub, config))
    httpd.daemon_threads = True
    return httpd
