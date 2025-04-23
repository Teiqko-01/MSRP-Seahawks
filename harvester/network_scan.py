# network_scan.py
import nmap  # Utilise python-nmap pour scanner le réseau via Nmap
import socket  # Utilisé ici pour vérifier manuellement l'ouverture de port
import json  # Pour enregistrer les résultats de scan au format JSON
from scan_logger import init_db, log_scan  # Initialisation et journalisation des résultats de scan

def is_port_open(ip, port, timeout=1):
    try:
        # Tente une connexion TCP directe au port (permet de vérifier l'ouverture réelle)
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except:
        return False  # Si la connexion échoue, le port est considéré comme fermé ou filtré

def scan_network():
    init_db()  # Initialise la base de données ou le système de log des scans
    scanner = nmap.PortScanner()  # Initialise un scanner Nmap
    scan_range = "192.168.1.1-100"  # Plage IP à scanner

    print(f"[SCAN] Scanning {scan_range} ...")
    # Lance le scan Nmap sur les ports spécifiés (les plus classiques : FTP, SSH, HTTP, HTTPS, RDP)
    scanner.scan(hosts=scan_range, arguments='-p 21,22,80,443,3389')

    result = {}  # Stockera les résultats structurés du scan

    for host in scanner.all_hosts():
        # Récupère le nom d’hôte détecté, nettoyé pour retirer les éventuels suffixes
        raw_hostname = scanner[host].hostname()
        hostname = raw_hostname.split('.')[0] if raw_hostname else "inconnu"
        verified_ports = []

        if 'tcp' in scanner[host]:
            for port, pdata in scanner[host]['tcp'].items():
                # Vérifie que le port est ouvert selon Nmap et via une connexion directe
                if pdata['state'] == 'open' and is_port_open(host, port):
                    verified_ports.append(port)

        result[host] = {
            "hostname": hostname,
            "ports": verified_ports if verified_ports else ["Aucun port ouvert"]
        }

        # Enregistre les résultats du scan dans la base/log
        log_scan(host, hostname, verified_ports)

    # Sauvegarde les résultats dans un fichier JSON
    with open("assets/scan_report.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"[SCAN] {len(result)} machine(s) detectees.")
    return result  # Retourne les résultats du scan pour affichage ou traitement