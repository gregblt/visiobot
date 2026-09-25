"""Capture audio : son de la visio (découpé en phrases) et niveau du micro."""

import queue
import threading
import time

import numpy as np
import sounddevice as sd

TARGET_RATE = 16000  # ce qu'attend Whisper


def list_devices():
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            api = sd.query_hostapis(dev["hostapi"])["name"]
            print(f"  [{i:2}] {dev['name']}  ({api}, {int(dev['default_samplerate'])} Hz)")


def find_device(name):
    """Retourne l'index du premier périphérique d'entrée dont le nom contient `name`."""
    if name is None:
        return None
    if isinstance(name, int) or str(name).isdigit():
        return int(name)
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0 and str(name).lower() in dev["name"].lower():
            return i
    raise SystemExit(f"Périphérique audio introuvable : {name!r}. Lance avec --list-devices.")


def _resample(x, src_rate):
    if src_rate == TARGET_RATE:
        return x
    n = int(len(x) * TARGET_RATE / src_rate)
    return np.interp(np.linspace(0, len(x), n, endpoint=False), np.arange(len(x)), x).astype(np.float32)


class MeetingListener:
    """Écoute le son de la visio et produit des segments de parole (numpy float32, 16 kHz)."""

    def __init__(self, device, cfg):
        self.device = find_device(device)
        self.threshold = cfg["speech_threshold"]
        self.silence = cfg["silence_seconds"]
        self.max_len = cfg["max_segment_seconds"]
        self.segments = queue.Queue(maxsize=5)
        self._chunks = []
        self._last_voice = 0.0
        self._rate = int(sd.query_devices(self.device, "input")["default_samplerate"])

    def _callback(self, indata, frames, time_info, status):
        mono = indata.mean(axis=1).astype(np.float32)
        now = time.monotonic()
        loud = float(np.sqrt(np.mean(mono ** 2))) > self.threshold
        if loud:
            self._last_voice = now
        if loud or self._chunks:
            self._chunks.append(mono.copy())
        if not self._chunks:
            return
        duration = sum(len(c) for c in self._chunks) / self._rate
        if now - self._last_voice > self.silence or duration > self.max_len:
            audio = np.concatenate(self._chunks)
            self._chunks = []
            if duration > 0.6:
                try:
                    self.segments.put_nowait(_resample(audio, self._rate))
                except queue.Full:
                    pass  # la transcription est à la traîne : on laisse tomber

    def start(self):
        self._stream = sd.InputStream(
            device=self.device, channels=1, samplerate=self._rate,
            blocksize=int(self._rate * 0.05), callback=self._callback,
        )
        self._stream.start()


class MicLevel:
    """Mesure le volume de ton micro et appelle on_level(niveau) ~15 fois par seconde."""

    def __init__(self, device, on_level):
        self.device = find_device(device)
        self.on_level = on_level
        self._level = 0.0

    def _callback(self, indata, frames, time_info, status):
        rms = float(np.sqrt(np.mean(indata ** 2)))
        self._level = max(rms, self._level * 0.6)  # lissage (retombée douce)

    def _loop(self):
        last = -1.0
        while True:
            time.sleep(1 / 15)
            level = round(self._level, 3)
            self._level *= 0.8
            if abs(level - last) > 0.002:
                self.on_level(level)
                last = level

    def start(self):
        self._stream = sd.InputStream(device=self.device, channels=1, blocksize=800, callback=self._callback)
        self._stream.start()
        threading.Thread(target=self._loop, daemon=True).start()
