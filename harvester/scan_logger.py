# scan_logger.py
import sqlite3  # Module standard pour interagir avec une base SQLite
from datetime import datetime  # Pour horodater les enregistrements
import os  # Pour gérer les chemins et créer le dossier si nécessaire

DB_PATH = "assets/scan_logs.db"  # Chemin vers la base de données locale contenant les logs de scan

def init_db():
    """Crée la base de données et la table 'scans' si elle n'existe pas."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Crée le dossier 'assets/' si besoin
    conn = sqlite3.connect(DB_PATH)  # Connexion à la base de données SQLite
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Clé primaire auto-incrémentée
            ip TEXT,                                -- Adresse IP scannée
            hostname TEXT,                          -- Nom d’hôte détecté
            ports TEXT,                             -- Ports ouverts
            scanned_at TEXT                         -- Date et heure du scan (format ISO)
        )
    """)
    conn.commit()  # Applique les changements
    conn.close()  # Ferme la connexion proprement

def log_scan(ip, hostname, ports):
    """Ajoute une ligne de log dans la table 'scans'."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat(timespec='seconds')  # Timestamp ISO, sans millisecondes
    ports_str = ",".join(map(str, ports)) if ports else "Aucun"  # Convertit les ports en chaîne
    cursor.execute("""
        INSERT INTO scans (ip, hostname, ports, scanned_at)
        VALUES (?, ?, ?, ?)
    """, (ip, hostname, ports_str, now))  # Injection sécurisée des valeurs
    conn.commit()
    conn.close()
