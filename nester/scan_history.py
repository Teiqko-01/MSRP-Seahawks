# scan_history.py
import sqlite3  # Permet de se connecter et interagir avec une base SQLite

DB_PATH = "data/scan_logs.db"  # Chemin vers la base de données locale

# Récupère l'historique des scans d'un harvester (trié du plus récent au plus ancien)
def get_scan_history_by_harvester(harvester_id):
    # Normalisation de l'ID (important pour assurer la cohérence avec les noms enregistrés)
    harvester_id = harvester_id.lower().replace(" ", "_")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, scanned_at FROM scans
        WHERE hostname_sonde = ?
        ORDER BY scanned_at DESC
    """, (harvester_id,))
    return cursor.fetchall()  # Retourne une liste de tuples (id, date du scan)

# Récupère le détail d’un scan à partir de son identifiant unique
def get_scan_by_id(scan_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ip, hostname, ports, scanned_at
        FROM scans
        WHERE id = ?
    """, (scan_id,))
    return cursor.fetchone()  # Retourne un tuple ou None si non trouvé

# Récupère les scans effectués à une date précise pour un harvester donné
def get_scans_by_date(harvester_id, date_str):
    harvester_id = harvester_id.lower().replace(" ", "_")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, scanned_at FROM scans
        WHERE hostname_sonde = ? AND DATE(scanned_at) = DATE(?)
        ORDER BY scanned_at ASC
    """, (harvester_id, date_str))
    return cursor.fetchall()  # Liste des scans pour cette date (id et timestamp)

# Retourne les timestamps uniques des moments de scan sur une date donnée
def get_unique_scan_moments_by_date(harvester_id, date_str):
    harvester_id = harvester_id.lower().replace(" ", "_")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT scanned_at FROM scans
        WHERE hostname_sonde = ? AND DATE(scanned_at) = DATE(?)
        ORDER BY scanned_at ASC
    """, (harvester_id, date_str))
    return cursor.fetchall()  # Liste des horaires uniques où des scans ont eu lieu
