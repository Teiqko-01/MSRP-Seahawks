# add-db.py
import sqlite3  # Module standard pour interagir avec une base SQLite
import os       # Utilisé ici pour créer le dossier de destination si besoin

DB_PATH = "data/scan_logs.db"  # Chemin relatif vers la base de données

# Création du dossier "data" s'il n'existe pas déjà
os.makedirs("data", exist_ok=True)

# Connexion à la base de données SQLite (créée si elle n'existe pas encore)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()  # Création d'un curseur pour exécuter des requêtes SQL

# Création de la table "scans" si elle n'existe pas déjà
cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  # Identifiant unique auto-incrémenté
        ip TEXT,                                # Adresse IP scannée
        hostname TEXT,                          # Nom d’hôte correspondant (si résolu)
        ports TEXT,                             # Ports détectés ouverts (stockés en texte)
        scanned_at TEXT                         # Date et heure du scan (format texte)
    )
""")

conn.commit()  # Enregistrement des modifications
conn.close()   # Fermeture de la connexion à la base

print("Base de donnes initialise sur le Nester.")  # Message de confirmation
