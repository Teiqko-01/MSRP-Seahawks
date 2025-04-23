# lantency_check.py
import subprocess  # Permet d'exécuter la commande système "ping"

def average_ping(target="8.8.8.8", count=4):
    try:
        # Exécute la commande ping avec 4 paquets vers l'IP cible (par défaut : Google DNS)
        output = subprocess.check_output(["ping", "-c", str(count), target], text=True)

        # Parcours les lignes du résultat à la recherche des statistiques de latence
        for line in output.splitlines():
            if "avg" in line:
                # Extrait la valeur moyenne à partir de la ligne du type : rtt min/avg/max/mdev = ...
                avg = line.split("/")[4]  # La moyenne est à l'index 4 (position standard du "avg")
                return f"{avg} ms"
        return "N/A"  # Si aucune ligne avec "avg" n'est trouvée
    except Exception:
        return "Ping error"  # En cas d'échec de la commande (réseau)
