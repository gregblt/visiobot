"""Point d'entrée : python -m visiobot [--avatar] [--port 8765] [--config config.json]"""

import argparse
import webbrowser

from .config import load_config
from .server import ROOT, serve
from .state import Hub


def main():
    parser = argparse.ArgumentParser(prog="visiobot", description="Overlays OBS pour visio : compteur Gary/Krabs + avatar réactif.")
    parser.add_argument("--config", default=str(ROOT / "config.json"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--avatar", action="store_true", help="écoute la visio et fait réagir l'avatar (nécessite requirements.txt)")
    parser.add_argument("--no-stt", action="store_true", help="avec --avatar : seulement la bouche au micro, sans transcription")
    parser.add_argument("--list-devices", action="store_true", help="liste les entrées audio puis quitte")
    parser.add_argument("--open", action="store_true", help="ouvre le panneau de contrôle dans le navigateur")
    args = parser.parse_args()

    if args.list_devices:
        from .audio import list_devices
        print("Entrées audio disponibles :")
        list_devices()
        return

    config = load_config(args.config)
    m = config["meeting"]
    hub = Hub(m["participants"], m["rate"], m["currency"], m["duration_min"])

    if args.avatar:
        start_avatar(hub, config, with_stt=not args.no_stt)

    httpd = serve(hub, config, args.host, args.port)
    base = f"http://{args.host}:{args.port}"
    print(f"visiobot prêt sur {base}")
    print(f"  Panneau de contrôle : {base}/control.html   (à ajouter aussi en dock OBS)")
    print(f"  Source OBS réunion  : {base}/overlay.html   (1920×1080)")
    print(f"  Source OBS avatar   : {base}/avatar.html    (1080×1080)")
    if args.open:
        webbrowser.open(f"{base}/control.html")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nau revoir 👋")


def start_avatar(hub, config, with_stt):
    from .audio import MeetingListener, MicLevel
    from .reactions import Reactor

    audio_cfg = config["audio"]
    MicLevel(audio_cfg["mic_device"], lambda lvl: hub.publish("level", {"level": lvl})).start()

    reactor = Reactor(hub, config)
    reactor.start()

    if not with_stt:
        return
    if not audio_cfg["meeting_device"]:
        print("[avatar] audio.meeting_device n'est pas réglé dans config.json : pas de transcription.")
        return

    from .stt import Transcriber

    listener = MeetingListener(audio_cfg["meeting_device"], audio_cfg)

    def on_text(text):
        print(f"[visio] {text}")
        hub.add_transcript(text)
        reactor.on_text(text)

    Transcriber(config["stt"], listener.segments, on_text).start()
    listener.start()


if __name__ == "__main__":
    main()
