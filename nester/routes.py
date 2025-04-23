# routes.py
from flask import Blueprint, render_template, abort, jsonify, request, send_file
# Importation des fonctions liées aux harvesters
from models import load_harvesters, get_harvester
# Importation des fonctions pour consulter l'historique des scans
from scan_history import (
    get_scan_history_by_harvester,
    get_scan_by_id,
    get_scans_by_date,
    get_unique_scan_moments_by_date
)
# Importation de modules standards pour la manipulation de fichiers, données et système
import json
import os
import csv
import sqlite3
from datetime import datetime
from io import BytesIO
import socket
import platform
import subprocess

# Création du Blueprint qui regroupe toutes les routes de l'application Flask
routes = Blueprint('routes', __name__)

# Page d'accueil : liste tous les harvesters avec leur statut (connecté/déconnecté)
@routes.route("/")
def index():
    harvesters = load_harvesters()  # Chargement des harvesters depuis le fichier JSON
    for h in harvesters:
        # Ping l'adresse IP pour savoir si l'harvester est joignable
        h["status"] = "connecte" if is_host_reachable(h["ip"]) else "deconnecte"
    return render_template("index.html", harvesters=harvesters)

# Fonction utilitaire pour récupérer la dernière date de scan pour un hostname donné
def get_last_scan_date(harvester_hostname):
    harvester_hostname = harvester_hostname.lower().replace(" ", "_")
    try:
        conn = sqlite3.connect("data/scan_logs.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT scanned_at FROM scans
            WHERE hostname_sonde = ?
            ORDER BY scanned_at DESC LIMIT 1
        """, (harvester_hostname,))
        row = cursor.fetchone()
        return row[0] if row else None
    except:
        return None

# Route affichant le dashboard d’un harvester donné
@routes.route("/harvester/<harvester_id>")
def dashboard(harvester_id):
    harvester = get_harvester(harvester_id)
    if not harvester:
        abort(404)  # Si l'ID est inconnu → 404

    report_path = f"data/reports/{harvester_id}.json"
    report = {}
    # Si un rapport JSON existe pour ce harvester, on le charge
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8", errors="replace") as f:
            report = json.load(f)

    # Récupère la date du dernier scan effectué sur cet harvester
    last_scan = get_last_scan_date(harvester["hostname"])

    return render_template("dashboard.html", harvester=harvester, report=report, last_scan=last_scan)

# Affichage du rapport brut pour un harvester donné
@routes.route("/report/<harvester_id>")
def report(harvester_id):
    report_path = f"data/reports/{harvester_id}.json"
    if not os.path.exists(report_path):
        abort(404)
    with open(report_path, "r", encoding="utf-8", errors="replace") as f:
        report = json.load(f)
    return render_template("report.html", report=report, id=harvester_id)

# Interface de sélection de l'historique des scans par date pour un harvester
@routes.route("/history/<harvester_id>", methods=["GET", "POST"])
def history(harvester_id):
    selected_date = request.form.get("date") if request.method == "POST" else None
    history = []

    # Si une date est sélectionnée, on récupère les moments de scan uniques à cette date
    if selected_date:
        history = get_unique_scan_moments_by_date(harvester_id, selected_date)

    return render_template("history.html", harvester_id=harvester_id, history=history, selected_date=selected_date)

# Affiche les scans d’un moment précis pour un harvester donné
@routes.route("/history/scans/<harvester_id>/<scanned_at>")
def scan_group_view(harvester_id, scanned_at):
    conn = sqlite3.connect("data/scan_logs.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ip, hostname, ports FROM scans
        WHERE hostname_sonde = ? AND scanned_at = ?
    """, (harvester_id.lower().replace(" ", "_"), scanned_at))
    results = cursor.fetchall()
    return render_template("scan_group.html", scans=results, scanned_at=scanned_at, harvester_id=harvester_id)

# Permet de télécharger les résultats du scan précédent au format CSV
@routes.route("/history/scans/<harvester_id>/<scanned_at>/csv")
def scan_group_csv(harvester_id, scanned_at):
    conn = sqlite3.connect("data/scan_logs.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ip, hostname, ports FROM scans
        WHERE hostname_sonde = ? AND scanned_at = ?
    """, (harvester_id.lower().replace(" ", "_"), scanned_at))
    results = cursor.fetchall()

    # Construction du CSV en mémoire
    output = BytesIO()
    content = "IP,Hostname,Ports\n"
    for row in results:
        content += f"{row[0]},{row[1]},{row[2]}\n"

    output.write(content.encode("utf-8"))
    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        download_name=f"scan_{harvester_id}_{scanned_at}.csv",
        as_attachment=True
    )

# API pour recevoir et stocker un rapport de scan envoyé par un client
@routes.route("/api/upload", methods=["POST"])
def api_upload():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Donnees manquantes"}), 400

    # Normalisation du hostname
    data["hostname"] = data["hostname"].split('.')[0].lower().replace(" ", "_")
    scanned_at = data.get("scanned_at") or datetime.now().isoformat(timespec='seconds')

    # Mise à jour ou ajout du harvester dans le fichier JSON
    harvesters = load_harvesters()
    harvesters = [h for h in harvesters if h["id"] != data["id"]]
    harvesters.append({k: data[k] for k in data if k != "scan_report"})

    with open("data/harvesters.json", "w") as f:
        json.dump(harvesters, f, indent=2)

    # Sauvegarde du rapport de scan dans le dossier reports/
    os.makedirs("data/reports", exist_ok=True)
    with open(f"data/reports/{data['id']}.json", "w") as f:
        json.dump(data["scan_report"], f, indent=2)

    # Enregistrement des données de scan dans la base de données
    try:
        conn = sqlite3.connect("data/scan_logs.db")
        cursor = conn.cursor()
        for ip, hostdata in data["scan_report"].items():
            host_name = hostdata.get("hostname", "inconnu")
            ports = hostdata["ports"]
            ports_str = ", ".join(map(str, ports)) if ports else "Aucun"
            cursor.execute("""
                INSERT INTO scans (ip, hostname, ports, scanned_at, hostname_sonde)
                VALUES (?, ?, ?, ?, ?)
            """, (ip, host_name, ports_str, scanned_at, data["hostname"]))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Erreur BDD:", e)

    return jsonify({"message": "OK"}), 200

# Fonction utilitaire : vérifie si une adresse IP répond à un ping
def is_host_reachable(ip):
    # Utilisation du paramètre adapté selon le système (Windows ou Unix)
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        output = subprocess.check_output(["ping", param, "1", ip], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False