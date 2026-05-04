# Tetris (Pygame)

Jeu Tetris conforme aux exigences type **cahier des charges Python / Pygame** : fenêtre fixe **800×600**, boucle **FPS**, **POO** (`Board`, `Tetromino`, `Bag`, `Game`), **écrans** (accueil, jeu, game over / victoire marathon), **score / niveau / vies** (affichage + progression), **collisions**, **souris** (boutons menu / pause / fin), **sons** procéduraux, **animations** lors de la disparition des lignes, **high score** (`assets/highscore.txt`), **pause** (**P** / **Échap**), difficultés (**Normal**, **Hard**, **Expert**).

Le **niveau** augmente avec le **score** (seuil par difficulté) et accélère la gravité ; le HUD indique le **palier** de points avant le prochain niveau.

## Installation

```bash
pip install -r requirements.txt
```

Python **3.10+** recommandé.

## Lancement

```bash
python main.py
```

Sous **Windows**, si votre extension (ex. *Code Runner*) exécutait `#!/usr/bin/env python3` : cette ligne Unix n’existe pas dans PowerShell. Utilisez plutôt `py -3.11 main.py` (avec pygame installé sur ce Python) ou choisissez l’interpréteur **3.11+** dans Cursor / VS Code (**Python: Select Interpreter**). Le dépôt contient `.vscode/settings.json` pour *Code Runner* avec `py -3.11`.

## Contrôles (en partie)

| Touche       | Action            |
|-------------|-------------------|
| ← / →       | Déplacer          |
| Z / Haut / X | Rotation        |
| Bas         | Chute rapide      |
| Espace      | Chute instantanée |
| P / Échap   | Pause / reprendre |
| M           | Pause → menu (clavier) |

Sur l’accueil : **boutons** Jouer / Quitter et **< >** pour la difficulté ; **souris** ou **← / →** et **SPACE** / **ENTER** pour démarrer. En pause ou fin de partie : boutons **Reprendre**, **Menu principal**, **Quitter**.

## Victoire et défaite

- **Défaite** : plus d’emplacement pour une nouvelle pièce.
- **Victoire** (**marathon**) : effacer au moins **150 lignes** au total pendant la partie (objectif explicite côté barème).

## Structure

```
main.py           # entrée obligatoire
config.py         # constantes fenêtre et difficultés
game.py           # classe Game, menus, HUD, scoring
board.py          # grille et collisions
tetromino.py      # formes et génération
audio.py          # bips WAV générés (sans fichier .wav externe)
assets/           # highscore (+ possibilité d’ajouter des assets)
requirements.txt
```
