# Créer tes expressions

L'avatar est un « PNGtuber » : une image par expression, qu'on anime ensuite (respiration, hochement de tête,
tremblements, bouche qui bouge…). Il te faut une dizaine d'images de toi **avec exactement le même cadrage**.

## Les fichiers

À déposer dans `avatar/expressions/`, au format PNG (ou WebP), idéalement **1080 × 1080 à fond transparent** :

| Fichier | Obligatoire | Description |
|---|---|---|
| `neutre.png` | ✅ | visage détendu, bouche fermée |
| `neutre-parle.png` | conseillé | la même, bouche ouverte (sert quand tu parles) |
| `cligne.png` | facultatif | la même, yeux fermés (clignement) |
| `sourit.png` | | petit sourire |
| `rit.png` | | éclat de rire, yeux plissés |
| `acquiesce.png` | | sourire poli, yeux mi-clos (il hoche la tête) |
| `surpris.png` | | sourcils levés, bouche en « o » |
| `choque.png` | | yeux écarquillés, mains sur les joues |
| `sceptique.png` | | un sourcil levé, moue |
| `inquiet.png` | | sourcils froncés vers le haut, grimace |
| `reflechit.png` | | main au menton, regard en l'air |
| `ennuye.png` | | paupières lourdes, joue sur la main |
| `endormi.png` | | yeux fermés, tête penchée, bulle de salive |

Une expression sans image utilise `neutre.png`, avec le mouvement de l'expression.
Tu peux aussi ajouter `<expression>-parle.png` (par exemple `rit-parle.png`) et `<expression>-cligne.png`.

## Les générer gratuitement

### Méthode simple : un générateur d'images en ligne gratuit

Par exemple Google Gemini, Microsoft Designer / Bing Image Creator, ou tout outil qui accepte une photo de référence.

1. Donne une photo de toi, bien éclairée, de face, et demande le **portrait de base** :

   > Transforme cette photo en personnage de dessin animé 2D style cartoon, contours épais, couleurs vives,
   > cadré en buste, face caméra, centré, sur un fond uni vert (#00FF00), format carré.
   > Expression neutre, bouche fermée.

2. Quand le résultat te plaît, **garde cette image comme référence** et demande chaque expression
   **dans la même conversation**, en joignant à nouveau le portrait de base :

   > Exactement le même personnage, même cadrage, même pose, même fond vert.
   > Change UNIQUEMENT l'expression du visage : il éclate de rire, yeux plissés.

   Recommence pour chaque ligne du tableau ci-dessus. Pour `neutre-parle` : « même image, bouche ouverte
   comme s'il parlait ». Pour `cligne` : « même image, yeux fermés ».

3. **Retire le fond** : avec [rembg](https://github.com/danielgatis/rembg) (gratuit, en local) :

   ```bash
   pip install "rembg[cli]"
   rembg p dossier_des_images/ avatar/expressions/
   ```

   Autre option : dans OBS, ajoute un filtre **Clé de chrominance** (vert) sur la source avatar,
   et garde les images telles quelles.

4. Renomme les fichiers comme dans le tableau et relance `python -m visiobot --avatar`.

### Méthode 100 % locale : Stable Diffusion

Si tu as une carte graphique : [ComfyUI](https://github.com/comfyanonymous/ComfyUI) ou
[Fooocus](https://github.com/lllyasviel/Fooocus) avec **InstantID** ou **IP-Adapter FaceID** pour garder
ta ressemblance. Même principe : un portrait de base, puis une variante par expression,
avec la même graine (seed) et la même composition.

## Conseils

- Garde le **même cadrage** partout : sinon la tête « saute » d'une image à l'autre. Au besoin,
  recadre toutes les images d'un coup avec le même gabarit.
- Pose le bas du buste sur le bord inférieur de l'image : l'avatar est aligné en bas.
- Exagère les expressions, ça se lit mieux en petit dans une mosaïque de visio.
- Vérifie le rendu avec `http://127.0.0.1:8765/avatar.html?demo=1`.
