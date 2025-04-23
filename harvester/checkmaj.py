# checkmaj.py
# -*- coding: utf-8 -*-
import requests  # Utilisé pour effectuer des requêtes HTTP vers l'API GitLab
import re        # Utilisé pour extraire la version à l'aide d'expressions régulières
import os        # Permet d'accéder aux variables d'environnement et au système de fichiers
import sys       # Utilisé pour afficher les erreurs et quitter le script avec un code de retour

# URL de base de l'instance GitLab privée
GITLAB_URL = "http://192.168.1.100"

# Token d'authentification GitLab (chargé depuis les variables d'environnement ou valeur par défaut)
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "glpat-3dVXiUT_JHxSnjzyN9iW")

# Identifiant du dépôt GitLab (URL-encodé)
REPO_ID = "root%2Fharvester"

# Branche à vérifier pour la version distante
BRANCH = "main"

# Chemin local du fichier contenant la version
LOCAL_CONFIG_PATH = "/home/user/harvester/config.py"

def get_local_version():
    try:
        # Ouvre le fichier de config local et lit son contenu
        with open(LOCAL_CONFIG_PATH, "r") as f:
            content = f.read()
        # Cherche une ligne contenant la version locale sous la forme __version__ = "x.y.z"
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None
    except Exception as e:
        # En cas d’erreur (fichier introuvable, etc.), affiche une erreur sur stderr
        print(f"Error reading local version: {e}", file=sys.stderr)
        return None

def get_remote_version():
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    # URL de l’API GitLab pour récupérer le fichier config.py brut depuis la branche spécifiée
    api_url = f"{GITLAB_URL}/api/v4/projects/{REPO_ID}/repository/files/config.py/raw?ref={BRANCH}"
    try:
        # Requête GET vers l’API GitLab
        resp = requests.get(api_url, headers=headers)
        resp.raise_for_status()  # Déclenche une exception en cas de code HTTP d'erreur
        content = resp.text
        # Extrait la version distante comme dans la fonction précédente
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None
    except Exception as e:
        print(f"Error fetching remote version: {e}", file=sys.stderr)
        return None

def main():
    # Récupère les versions locale et distante
    local_version = get_local_version()
    remote_version = get_remote_version()

    # Si l'une des versions est indisponible, signale un échec
    if not local_version or not remote_version:
        print("Unable to determine version.")
        sys.exit(2)

    # Compare les deux versions
    if local_version != remote_version:
        print("Update available")  # Mise à jour disponible
        sys.exit(1)
    else:
        print("Already up to date")  # Aucune mise à jour nécessaire
        sys.exit(0)

if __name__ == "__main__":
    # Point d'entrée du script
    main()