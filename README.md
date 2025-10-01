# Plot Armor — Game Jam 2025

Ce projet utilise Python + Pygame.

## Prérequis
- Python 3.10+ installé et disponible dans votre `PATH` (Windows).
- Terminal Bash (vous utilisez `bash.exe`).

## Installation (environnement isolé recommandé)
Depuis la racine du repo :

```bash
# 1) Créer un environnement virtuel
python -m venv .venv

# 2) Activer l'environnement (Bash sous Windows)
source .venv/Scripts/activate

# 3) Mettre à jour pip (optionnel mais recommandé)
pip install --upgrade pip

# 4) Installer les dépendances
pip install -r requirements.txt
```

## Lancer le jeu
Toujours depuis la racine du repo:
```bash
# (Assurez-vous que l'environnement est activé)
python main.py
```

## Commandes
- Global:
  - `ENTER`: passer les textes de l'histoire

- Niveau 1 — Mini-jeu 1 (Messager coureur):
  - `ZQSD` ou Flèches directionnelles: déplacer le messager
  - Objectif: éviter les flèches et atteindre le château.

- Niveau 1 — Mini-jeu 2 (Défense du prince):
  - `ESPACE`: faire apparaître des soldats pour protéger le prince
  - Objectif: empêcher les flèches d'atteindre le prince pendant qu'il se déplace.

- Niveau 2 — Mini-jeu 1 (QTE):
  - `Q/D` ou Flèches Gauche/Droite: réussir les QTE
  - Objectif: compléter les séquences pour progresser (ou non ><).

- Niveau 2 — Mini-jeu 2 (Libération du cheval):
  - `E`: spammer pour libérer le cheval

- Niveau 2 — Mini-jeu 3 (Cheval):
  - `ZQSD` ou Flèches directionnelles: déplacer le cheval
  - Objectif: guider le cheval jusqu'au château.

## Dépannage rapide
- Si `python` n'est pas reconnu, essayez `py -3` ou vérifiez l'installation de Python.
- Si l'activation échoue, vérifiez le chemin: `source .venv/Scripts/activate` (Bash Windows) ou `.venv\Scripts\activate` dans `cmd.exe`/PowerShell.
- Pygame nécessite parfois des composants système (DirectX/SDL). Mettez à jour vos pilotes graphiques si vous rencontrez des erreurs d'initialisation.