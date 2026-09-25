"""Transcription locale et gratuite avec faster-whisper."""

import threading


class Transcriber:
    def __init__(self, cfg, segments, on_text):
        from faster_whisper import WhisperModel  # import tardif : lourd à charger

        print(f"[stt] chargement du modèle Whisper « {cfg['model']} » (le 1er lancement le télécharge)…")
        self.model = WhisperModel(cfg["model"], device=cfg["device"], compute_type=cfg["compute_type"])
        self.language = cfg["language"]
        self.segments = segments
        self.on_text = on_text

    def _loop(self):
        while True:
            audio = self.segments.get()
            parts, _ = self.model.transcribe(
                audio, language=self.language, beam_size=1, vad_filter=True, condition_on_previous_text=False,
            )
            text = " ".join(p.text.strip() for p in parts).strip()
            if text:
                self.on_text(text)

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()
