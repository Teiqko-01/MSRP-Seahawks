# Harvester-monitoring.py

# Ping les harvesters et, après 2 scans KO consécutifs, ouvre ou met à jour un ticket GLPI

# Importation des bibliothèques nécessaires
import json
import os
import subprocess
import pathlib
import datetime
import sys
import requests

# Définition des chemins de répertoires et fichiers
BASE_DIR = pathlib.Path(__file__).resolve().parent  
DATA_DIR = BASE_DIR / "data"  
HARVESTERS_FILE = DATA_DIR / "harvesters.json"  
STATE_FILE = DATA_DIR / "harvester_status.json"  

# Variables d'environnement pour accéder à l'API GLPI
GLPI_URL = os.getenv("http://172.16.60.6/apirest.php")  
GLPI_APP_TOKEN = os.getenv("qv2d0k5b7Ydseo5jMsMylGTvt9XdMOuHGtzGsld0")  
GLPI_USER_TOKEN = os.getenv("dF4Os2UHavSdfTms6bgt6VDQCtTiRZrCm6S18xGa")  
GLPI_ENTITY_ID = os.getenv("0")  

# Paramètres pour le scan des harvesters
PING_COUNT = 10  
FAIL_SCANS_THRESHOLD = 2  

# Utilitaires pour gérer les ping et l'état des harvesters

def load_harvesters():
    # Charge la liste des harvesters depuis le fichier JSON et retourne la liste d'hôtes
    with open(HARVESTERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def ping(host: str) -> bool:
    # Effectue un ping sur un hôte donné et retourne True si au moins un ping réussit
    result = subprocess.run(
        ["ping", "-c", str(PING_COUNT), "-W", "1", host],  
        stdout=subprocess.DEVNULL,  
        stderr=subprocess.DEVNULL,  
    )
    return result.returncode == 0  # Si le retour est 0, le ping a réussi

def load_state():
    # Charge l'état actuel du script (scans précédents) depuis un fichier JSON
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}  

def save_state(state):
    # Sauvegarde l'état actuel du script dans un fichier JSON
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# GLPI API helpers

def glpi_request(method, endpoint, session_token=None, **kwargs):
    # Fonction générique pour envoyer une requête à l'API GLPI
    headers = {
        "App-Token": GLPI_APP_TOKEN,  
        "Authorization": f"user_token {GLPI_USER_TOKEN}",  
        "Content-Type": "application/json",  
    }
    if session_token:
        headers["Session-Token"] = session_token  
    url = f"{GLPI_URL.rstrip('/')}/{endpoint.lstrip('/')}"  
    return requests.request(method, url, headers=headers, timeout=30, **kwargs)  

def glpi_open_session():
    # Ouvre une session avec GLPI et retourne le jeton de session
    r = glpi_request("GET", "initSession")
    r.raise_for_status()  
    return r.json()["session_token"]  

def glpi_kill_session(token):
    # Ferme la session GLPI avec le jeton de session donné
    glpi_request("GET", "killSession", session_token=token)

def search_open_ticket(token, host):
    # Recherche un ticket ouvert avec un titre contenant <host>, retourne son ID ou None
    criteria = {
        "criteria[0][field]": "1",            # 1 = name (titre)
        "criteria[0][searchtype]": "contains", # Recherche par correspondance partielle
        "criteria[0][value]": host,           # Valeur à chercher dans le titre
        "criteria[1][link]": "AND",           # Condition supplémentaire
        "criteria[1][field]": "12",           # 12 = status
        "criteria[1][searchtype]": "not",     # Recherche de tickets non résolus
        "criteria[1][value]": "6"             # 6 = solved/closed
    }
    r = glpi_request("GET", "search/Ticket", session_token=token, params=criteria)
    r.raise_for_status()  # Lève une exception si la requête échoue
    data = r.json()
    if data["totalcount"] > 0:  # Si des tickets ont été trouvés
        return int(data["data"][0]["id"])  
    return None  # Retourne None si aucun ticket n'a été trouvé

def add_followup(token, ticket_id, content):
    # Ajoute un suivi à un ticket GLPI existant avec le contenu spécifié
    payload = {"input": {"content": content}}  # Contenu du suivi
    r = glpi_request("POST", f"Ticket/{ticket_id}/TicketFollowup", session_token=token, json=payload)
    r.raise_for_status()  # Lève une exception si la requête échoue

def create_ticket(token, title, content):
    # Crée un nouveau ticket GLPI avec le titre et le contenu spécifiés
    payload = {"input": {"name": title, "content": content, "status": 1}}  # Statut 1 = nouveau
    if GLPI_ENTITY_ID:  # Si un ID d'entité est fourni, l'ajouter au ticket
        payload["input"]["entities_id"] = int(GLPI_ENTITY_ID)
    r = glpi_request("POST", "Ticket", session_token=token, json=payload)
    r.raise_for_status()  # Lève une exception si la requête échoue
    return int(r.json()["id"])  # Retourne l'ID du ticket créé


# logique principale

def main():
    # Vérifie que toutes les variables d'environnement nécessaires sont définies
    if not all([GLPI_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN]):
        print("GLPI_* variables are missing", file=sys.stderr); return

    harvesters = load_harvesters()  # Charge la liste des harvesters
    state = load_state()  # Charge l'état des scans précédents
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Heure actuelle formatée

    session_token = glpi_open_session()  # Ouvre une session avec GLPI

    try:
        for hv in harvesters:
            host = hv.get("host") or hv.get("ip");  # Récupère l'hôte (par nom ou IP)
            if not host: continue  # Si aucune adresse n'est fournie, passe à l'hôte suivant

            ok = ping(host)  # Effectue un ping sur l'hôte
            entry = state.get(host, {"fails": 0})  # Récupère l'état du harvester (nombre de pannes)
            entry["fails"] = 0 if ok else entry["fails"] + 1  # Si le ping a échoué, incrémente le compteur de pannes
            state[host] = entry  # Met à jour l'état du harvester

            if entry["fails"] >= FAIL_SCANS_THRESHOLD:  # Si le nombre d'échecs atteint le seuil
                title = f"Harvester indisponible : {host}"  # Titre du ticket
                msg = (f"Le harvester {host} n'a pas répondu aux pings "
                       f"({PING_COUNT} tentatives) pendant {entry['fails']} scans consécutifs "
                       f"— {now_str}")  # Message à inclure dans le ticket

                try:
                    existing = search_open_ticket(session_token, host)  # Recherche un ticket existant
                    if existing:  # Si un ticket existe déjà, ajoute un suivi
                        add_followup(session_token, existing, msg +
                                     "\nProblème toujours présent (scan automatique).")
                        print(f"Ajout d'un suivi au ticket {existing} (host {host})")
                    else:  # Si aucun ticket n'existe, crée un nouveau ticket
                        tid = create_ticket(session_token, title, msg)
                        print(f"Nouveau ticket {tid} créé pour {host}")
                except Exception as e:
                    print(f"Erreur GLPI pour {host}: {e}", file=sys.stderr)  # Gestion des erreurs GLPI

                entry["fails"] = 0  # Réinitialise le compteur de pannes après notification

    finally:
        glpi_kill_session(session_token)  # Ferme la session GLPI
        save_state(state)  # Sauvegarde l'état des scans

# Exécution du script si ce fichier est exécuté directement
if __name__ == "__main__":
    main()