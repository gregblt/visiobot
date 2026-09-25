"""Chargement de la configuration (config.json fusionné avec les valeurs par défaut)."""

import copy
import json
from pathlib import Path

DEFAULTS = {
    "meeting": {
        "participants": 6,
        "rate": 50,
        "currency": "EUR",
        # Paliers de coût (dans la devise) où M. Krabs monte d'un cran de colère
        "krabs_thresholds": [50, 200, 500, 1000],
    },
    "audio": {
        # Nom (ou morceau de nom) du périphérique qui reçoit le son de la visio
        # (VB-Cable, BlackHole, moniteur PipeWire...). null = pas d'écoute.
        "meeting_device": None,
        # Ton micro, pour faire bouger la bouche de l'avatar quand tu parles. null = micro par défaut.
        "mic_device": None,
        "speech_threshold": 0.01,  # RMS au-dessus duquel on considère qu'on parle
        "silence_seconds": 0.7,  # silence qui termine une phrase
        "max_segment_seconds": 10,
    },
    "stt": {
        "model": "small",  # tiny, base, small, medium... (plus gros = plus lent mais meilleur)
        "language": "fr",
        "device": "cpu",
        "compute_type": "int8",
    },
    "avatar": {
        "my_name": [],  # ex. ["Grégory", "Greg"] : l'avatar sursaute quand on t'appelle
        "expressions": [
            "neutre", "sourit", "rit", "acquiesce", "surpris", "choque",
            "sceptique", "inquiet", "reflechit", "ennuye", "endormi",
        ],
        "reaction_seconds": 4,
        "bored_after_seconds": 240,  # sans réaction -> "ennuye"
        "asleep_after_seconds": 480,  # sans réaction -> "endormi"
        "talk_threshold": 0.02,
        "rules": [
            {"expression": "rit", "keywords": ["haha", "hahaha", "mdr", "ptdr", "lol", "trop drole", "c'est drole", "blague", "rigole"]},
            {"expression": "sourit", "keywords": ["merci", "bravo", "super", "genial", "top", "parfait", "excellent", "felicitations", "bonne nouvelle"]},
            {"expression": "acquiesce", "keywords": ["d'accord", "ok", "exactement", "tout a fait", "effectivement", "ca marche", "valide", "on est d'accord"]},
            {"expression": "inquiet", "keywords": ["budget", "retard", "deadline", "urgent", "risque", "probleme", "bug", "incident", "en production", "licenciement"]},
            {"expression": "choque", "keywords": ["catastrophe", "c'est la cata", "tout est casse", "on a perdu", "annule", "virer", "surcout"]},
            {"expression": "sceptique", "keywords": ["synergie", "disruptif", "paradigme", "on verra", "quick win", "low hanging fruit", "a l'echelle", "blockchain"]},
            {"expression": "surpris", "keywords": ["vraiment", "incroyable", "serieusement", "sans blague", "ah bon", "nouveau"]},
            {"expression": "reflechit", "keywords": ["question", "qu'en pensez-vous", "vous en pensez quoi", "des idees", "une idee", "comment on fait"]},
            {"expression": "ennuye", "keywords": ["point suivant", "ordre du jour", "on va faire un tour de table", "prochaine slide", "on reprend", "je partage mon ecran"]},
        ],
    },
    # Réactions « intelligentes » via un LLM local gratuit (Ollama). Désactivé par défaut.
    "llm": {
        "enabled": False,
        "url": "http://localhost:11434/api/generate",
        "model": "llama3.2:3b",
        "every_seconds": 12,
    },
}


def _merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path):
    config = copy.deepcopy(DEFAULTS)
    p = Path(path)
    if p.is_file():
        with p.open(encoding="utf-8") as f:
            _merge(config, json.load(f))
    return config
