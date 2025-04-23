# installmaj.py
# -*- coding: utf-8 -*-
import subprocess  # Permet d'exécuter des commandes système (Python ou Git)
import sys  

# Chemin local vers le dossier Git du projet
REPO_PATH = "/home/user/harvester"

# Script utilisé pour vérifier si une mise à jour est nécessaire
CHECK_SCRIPT = "/home/user/harvester/checkmaj.py"

def main():
    # Lance le script de vérification de mise à jour
    check = subprocess.run(["python3", CHECK_SCRIPT])

    if check.returncode == 1:
        # Si une mise à jour est détectée (code retour 1), exécute les commandes Git
        print("==> Update detected. Pulling latest changes...")
        subprocess.run(["git", "fetch"], cwd=REPO_PATH)  # Récupère les dernières infos depuis le remote
        pull = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=REPO_PATH)  # Force la mise à jour des fichiers locaux
        if pull.returncode == 0:
            print("==> Update applied successfully.")  # Mise à jour réussie
        else:
            print("!! Failed to apply update.")  # Problème durant le reset Git
    elif check.returncode == 0:
        # Aucun changement à appliquer
        print("==> Already up to date.")
    else:
        # Erreur lors de la vérification
        print("!! Error while checking for update.")

if __name__ == "__main__":
    main()  # Point d'entrée du script