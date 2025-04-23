# send_to_nester.py
import json
import requests
from data_manager import get_local_ip_hostname, load_scan_report
from latency_check import average_ping
from config import VERSION
from datetime import datetime

# URL de l'API de réception Nester
NESTER_API_URL = "http://192.168.1.50:5000/api/upload"

def send_data():
    # Préparation des informations à transmettre
    ip, hostname = get_local_ip_hostname()
    latency = average_ping()
    scan = load_scan_report()

    payload = {
        "id": hostname.lower().replace(" ", "_"),
        "name": hostname,
        "ip": ip,
        "hostname": hostname,
        "latency": latency,
        "version": VERSION,
        "status": "connecte",
        "scanned_at": datetime.now().isoformat(timespec='seconds'),
        "scan_report": scan
    }

    try:
        # Envoi HTTP POST vers le Nester
        response = requests.post(NESTER_API_URL, json=payload)

        # Sortie JSON utilisée par l'interface UI
        print(json.dumps({"status_code": response.status_code}))
    except requests.exceptions.RequestException as e:
        # En cas de problème réseau ou serveur
        print(json.dumps({"status_code": 0, "error": str(e)}))

if __name__ == "__main__":
    send_data()