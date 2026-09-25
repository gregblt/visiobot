# 🐌 Visiobot

Des overlays OBS pour mettre un peu d'ambiance dans tes visios (Zoom, Teams, Visio de l'État…),
envoyés à la visio via la **Caméra virtuelle OBS**.

1. **Le compteur de réunion** : Gary traverse l'écran avec le prix de la réunion qui grimpe au-dessus
   de lui, des pièces s'envolent, et M. Krabs s'énerve palier après palier.
2. **Ton avatar réactif** : une version dessinée de toi qui réagit à ce qui se dit (rire, hochement de tête,
   air sceptique quand quelqu'un dit « synergie », endormi au bout de 8 minutes sans rien d'intéressant…)
   et qui bouge la bouche quand tu parles.

Tout est **gratuit** et tourne **en local** : pas de compte, pas de cloud. La transcription se fait
sur ta machine avec Whisper, et rien n'est enregistré.

---

## Installation

Il faut [Python 3.10+](https://www.python.org/downloads/) et [OBS Studio](https://obsproject.com/) 28+.

```bash
git clone https://github.com/gregblt/visiobot.git
cd visiobot
cp config.example.json config.json      # sous Windows : copy config.example.json config.json
```

- **Compteur seulement** : rien d'autre à installer, le serveur n'utilise que la bibliothèque standard.
- **Avatar** : `pip install -r requirements.txt` (faster-whisper, sounddevice, numpy).

## Lancer

```bash
python -m visiobot            # compteur Gary / Krabs + panneau de contrôle
python -m visiobot --avatar   # + avatar réactif (écoute la visio)
python -m visiobot --list-devices   # pour trouver le nom de tes périphériques audio
```

Le panneau de contrôle est sur <http://127.0.0.1:8765/control.html>.

---

## Réglages OBS

### 1. Les sources

Dans ta scène, ajoute des **Sources navigateur** (➕ > Navigateur) :

| Source | URL | Largeur × hauteur |
|---|---|---|
| Compteur de réunion | `http://127.0.0.1:8765/overlay.html` | 1920 × 1080 |
| Avatar | `http://127.0.0.1:8765/avatar.html` | 1080 × 1080 |

Pour les deux sources, **décoche** « Arrêter la source quand elle n'est pas visible » et
« Actualiser le navigateur quand la scène devient active ».

Place le compteur **au-dessus** de ta webcam (ou de l'avatar) dans la liste des sources.

### 2. Le panneau de contrôle dans OBS

Menu **Docks > Docks de navigateur personnalisés…** :
nom `Visiobot`, URL `http://127.0.0.1:8765/control.html`.
Tu as alors le compteur, les boutons Démarrer / Pause / Remise à zéro, le nombre de participants,
le coût horaire et des boutons pour déclencher une expression de l'avatar à la main, directement dans OBS.

### 3. Envoyer à la visio

Dans OBS, clique sur **Démarrer la caméra virtuelle**, puis choisis la caméra **OBS Virtual Camera** :

- **Zoom** : Paramètres > Vidéo > Caméra. Zoom affiche ton image en miroir chez toi seulement :
  décoche « Refléter ma vidéo » pour lire le compteur à l'endroit.
- **Teams** : Paramètres > Appareils > Caméra.
- **Visio (État) / toute visio dans le navigateur** : à l'arrivée dans la salle, choisis
  « OBS Virtual Camera » dans la liste des caméras (autorise la caméra dans le navigateur si besoin).

---

## Le compteur de réunion

Dans le panneau de contrôle, règle **le nombre de participants** et **le coût horaire moyen par personne**,
puis clique sur **▶ Démarrer**. Quand quelqu'un arrive en cours de route, fais « + » : le coût déjà écoulé
n'est pas recalculé, seul le rythme change.

`coût = Σ (participants × coût horaire / 3600) par seconde écoulée`

Valeurs par défaut et paliers de colère de Krabs : section `meeting` de `config.json`.

### Paramètres d'URL de `overlay.html`

| Paramètre | Défaut | Effet |
|---|---|---|
| `seuils` | `50,200,500,1000` | paliers où Krabs monte d'un cran (5 états) |
| `vitesse` | `110` | vitesse de Gary (pixels / seconde) |
| `piece` | `1` | une pièce s'envole tous les X € (`0` = aucune) |
| `krabs` | `haut-droite` | `haut-gauche`, `bas-droite`, `bas-gauche` ou `cache` |
| `echelle` | `1` | agrandit ou réduit tout |
| `gary_regarde` | `droite` | sens de ton image perso de Gary |

Exemple : `http://127.0.0.1:8765/overlay.html?krabs=haut-gauche&echelle=0.8&seuils=20,100,300,600`

### Sans serveur

`overlay.html` marche aussi en l'ouvrant directement comme **fichier local** dans la source navigateur,
avec les paramètres `n=` (participants), `taux=` (coût horaire) et `devise=`.
Le chrono démarre tout seul. Pour le piloter, fais un clic droit sur la source > **Interagir**, puis :
`Espace` = pause, `+` / `-` = participants, `R` = remise à zéro.

### Mettre les vrais Gary et Krabs

Les personnages fournis sont des dessins « inspirés de ». Pour utiliser tes propres images
(GIF, PNG ou WebP à fond transparent), dépose-les dans `web/assets/` :

- `gary.gif` (ou `.png` / `.webp`), tourné vers la droite (sinon ajoute `gary_regarde=gauche`) ;
- `krabs-0.png` (calme) → `krabs-4.png` (rage). S'il en manque, le palier précédent est réutilisé.

Ces personnages appartiennent à Nickelodeon : pour un usage perso en réunion, pas de souci,
mais ne les publie pas dans le dépôt s'il devient public (`web/assets/` est ignoré par git).

---

## L'avatar réactif

### 1. Créer tes expressions (une fois)

Voir [`avatar/README.md`](avatar/README.md) : comment générer gratuitement une dizaine d'images de toi
(neutre, rit, sceptique, endormi…) à partir d'une photo, et où les déposer.
Tant que tu n'as pas d'images, l'avatar s'affiche sous forme d'emojis.

### 2. Faire entendre la visio à visiobot

visiobot doit « entendre » le son de la visio. On passe par une entrée audio virtuelle gratuite :

**Windows** : [VB-Cable](https://vb-audio.com/Cable/)
1. Installe VB-Cable, puis redémarre.
2. Paramètres Windows > Système > Son > **Mélangeur de volume** : mets la sortie de Zoom, de Teams
   ou de ton navigateur (pour Visio) sur **CABLE Input**.
3. Pour continuer à entendre : Panneau de configuration Son > onglet Enregistrement > **CABLE Output** >
   Propriétés > Écouter > coche « Écouter ce périphérique » et choisis ton casque.
4. Dans `config.json` : `"meeting_device": "CABLE Output"`.

**macOS** : [BlackHole 2ch](https://existential.audio/blackhole/)
1. Installe BlackHole 2ch.
2. Dans Configuration audio et MIDI, crée un **périphérique à sorties multiples** (ton casque + BlackHole 2ch)
   et choisis-le comme sortie dans Zoom, Teams ou le système.
3. Dans `config.json` : `"meeting_device": "BlackHole"`.

**Linux (PipeWire / PulseAudio)**
1. `"meeting_device": "pulse"` dans `config.json`.
2. Lance `python -m visiobot --avatar`, ouvre `pavucontrol` > onglet Enregistrement et règle
   l'entrée de python sur « Monitor of <ton casque> ».

`mic_device` sert à la bouche de l'avatar. Laisse `null` pour utiliser le micro par défaut.

### 3. Régler les réactions

Dans `config.json`, section `avatar` :

- `my_name` : ton prénom ou tes surnoms. L'avatar sursaute quand on t'appelle.
- `rules` : les mots-clés qui déclenchent chaque expression. Les accents et majuscules sont ignorés.
- `bored_after_seconds` / `asleep_after_seconds` : délai sans réaction avant l'ennui, puis le sommeil.

Au premier lancement, Whisper télécharge le modèle `small` (environ 500 Mo). Si ton PC est lent,
mets `"model": "base"` dans la section `stt` ; s'il est costaud, mets `"medium"` pour une meilleure transcription.

**Option LLM local (gratuit)** : avec [Ollama](https://ollama.com/) installé (`ollama pull llama3.2:3b`),
passe `llm.enabled` à `true`. Toutes les 12 s, un petit modèle lit les 30 dernières secondes et choisit
une réaction « au feeling », en plus des mots-clés.

Pour tester sans visio : `http://127.0.0.1:8765/avatar.html?demo=1` fait défiler les expressions,
et `?debug=1` affiche ce que visiobot a entendu.

### Vie privée

La transcription reste sur ta machine et n'est gardée qu'une minute en mémoire, sans jamais être
écrite sur le disque. Ce sont quand même les paroles de tes collègues : préviens-les,
et évite l'avatar dans les réunions sensibles (RH, confidentiel…).

---

## Structure

```
visiobot/            serveur Python (HTTP + SSE), audio, transcription, réactions
web/overlay.html     Gary + prix + Krabs          (source OBS)
web/avatar.html      avatar réactif               (source OBS)
web/control.html     panneau de contrôle          (navigateur ou dock OBS)
web/assets/          tes images Gary / Krabs (facultatif, ignoré par git)
avatar/expressions/  tes images d'expressions
config.example.json  configuration à copier en config.json
```
