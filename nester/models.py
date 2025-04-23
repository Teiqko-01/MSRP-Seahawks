# models.py
import json     # Utilisé pour lire/écrire des données au format JSON
import os       # Utilisé ici pour vérifier l'existence d'un fichier

DB_FILE = "data/harvesters.json"  # Chemin du fichier JSON stockant les données des harvesters

# Fonction pour charger la liste des harvesters depuis le fichier JSON
def load_harvesters():
    if os.path.exists(DB_FILE):  # Vérifie que le fichier existe
        with open(DB_FILE, "r") as f:
            return json.load(f)  # Charge et retourne les données JSON
    return []  # Retourne une liste vide si le fichier n'existe pas

# Fonction pour récupérer un harvester par son identifiant
def get_harvester(harvester_id):
    harvesters = load_harvesters()  # Charge tous les harvesters
    for h in harvesters:
        if h["id"] == harvester_id:  # Si l'ID correspond, retourne le harvester
            return h
    return None  # Aucun harvester trouvé avec cet ID