# data_manager.py
import json  # Pour écrire des données structurées vers un fichier
import socket  # Pour obtenir l'IP locale et le nom de la machine
import os  # Pour vérifier l'existence du fichier de rapport de scan

def get_local_ip_hostname():
    hostname = socket.gethostname()  # Nom d'hôte de la machine
    try:
        # Création d’un socket UDP pour déterminer l’adresse IP locale réelle
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connexion fictive à un serveur Google (pas de données échangées)
        ip = s.getsockname()[0]  # Récupère l’IP assignée par la route par défaut
        s.close()
    except Exception:
        ip = "127.0.0.1"  # Si échec, retourne l’IP loopback (fallback)

    # Nettoie le nom d’hôte pour enlever les éventuels suffixes DNS (ex: .home)
    hostname = hostname.split('.')[0]
    return ip, hostname

def load_scan_report():
    """Charge le rapport de scan depuis le fichier JSON local."""
    path = "assets/scan_report.json"
    try:
        if not os.path.exists(path):
            return {}  # Si le fichier n’existe pas, retourne un dictionnaire vide

        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}  # Si le fichier est vide, retourne aussi un dict vide
            return json.loads(content)  # Parse le JSON en dictionnaire Python
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Gère les erreurs classiques de lecture JSON