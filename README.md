# Tetris (Pygame)

Jeu Tetris conforme aux exigences type **cahier des charges Python / Pygame** : fenêtre fixe **800×600**, boucle **FPS**, **POO** (`Board`, `Tetromino`, `Bag`, `Game`), **écrans** (accueil, jeu, game over / victoire marathon), **score / niveau / lignes**, **collisions**, **sons** procéduraux, **animations** lors de la disparition des lignes, **high score** (`assets/highscore.txt`), **pause** (**P** / **Échap**), difficultés (**Normal**, **Hard**, **Expert**).

## Installation

```bash
pip install -r requirements.txt
```

Python **3.10+** recommandé.

## Lancement

```bash
python main.py
```

## Contrôles (en partie)

| Touche       | Action            |
|-------------|-------------------|
| ← / →       | Déplacer          |
| Z / Haut / X | Rotation        |
| Bas         | Chute rapide      |
| Espace      | Chute instantanée |
| P / Échap   | Pause             |

Sur l’accueil : ← / → choisissent la difficulté ; **SPACE** ou **ENTER** démarrent.

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
