# Game Jam 2025 — Mini guide

Ce projet utilise Python et Pygame.

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
python src/main.py
```

## Dépannage rapide
- Si `python` n'est pas reconnu, essayez `py -3` ou vérifiez l'installation de Python.
- Si l'activation échoue, vérifiez le chemin: `source .venv/Scripts/activate` (Bash Windows) ou `.venv\Scripts\activate` dans `cmd.exe`/PowerShell.
- Pygame nécessite parfois des composants système (DirectX/SDL). Mettez à jour vos pilotes graphiques si vous rencontrez des erreurs d'initialisation.

## Arborescence
```
assets/
  fonts/ images/ sounds/
src/
  main.py
requirements.txt
```
