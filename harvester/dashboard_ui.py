# dashboard_ui.py
import tkinter as tk  # Interface graphique (GUI) de base avec Tkinter
from tkinter import messagebox  # Fenêtres contextuelles pour afficher des messages à l'utilisateur
from latency_check import average_ping  # Fonction pour mesurer la latence réseau
from data_manager import get_local_ip_hostname, load_scan_report  # Fonctions pour récupérer des infos locales
from network_scan import scan_network  # Fonction pour exécuter un scan réseau
from config import VERSION  # Version de l'application
import subprocess  # Pour exécuter des scripts Python externes
import json # Pour gerer ke Json

class HarvesterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Seahawks Harvester")

        # Initialisation de l'interface et affichage des informations dès le lancement
        self.build_ui()
        self.refresh_dashboard()

        # Création du bouton pour envoyer les données vers Nester
        self.send_button = tk.Button(self.root, text="Envoyer vers Nester", command=self.envoyer_vers_nester)
        self.send_button.pack(pady=5)

        # Label qui affiche les messages de statut dynamiques (en bas de la fenêtre)
        self.status_label = tk.Label(self.root, text="", fg="black")
        self.status_label.pack()

    def build_ui(self):
        # Création des widgets pour afficher les données système
        self.lbl_version = tk.Label(self.root, text=f"Version: {VERSION}")
        self.lbl_ip = tk.Label(self.root, text="")
        self.lbl_hostname = tk.Label(self.root, text="")
        self.lbl_machines = tk.Label(self.root, text="")
        self.lbl_latency = tk.Label(self.root, text="")
        self.txt_scan = tk.Text(self.root, height=15, width=80)

        # Placement de tous les labels principaux
        for widget in [self.lbl_version, self.lbl_ip, self.lbl_hostname, self.lbl_machines, self.lbl_latency]:
            widget.pack()

        # Zone de texte affichant le rapport de scan
        self.txt_scan.pack()

        # Création des boutons principaux de l'application
        tk.Button(self.root, text="Scan Réseau", command=self.run_scan).pack(pady=5)
        tk.Button(self.root, text="Vérifier MAJ", command=self.run_update).pack(pady=5)
        tk.Button(self.root, text="Actualiser", command=self.refresh_dashboard).pack(pady=5)

    def run_scan(self):
        # Lance un scan réseau local
        scan_network()

        # Met à jour les informations du tableau de bord
        self.refresh_dashboard()

        # Envoi automatique des données à Nester après le scan
        try:
            # Exécution du script d'envoi avec récupération de la sortie JSON
            result = subprocess.run(["python3", "send_to_nester.py"], capture_output=True, text=True)
            response_data = result.stdout.strip()

            # Tentative de parsing JSON du résultat
            try:
                parsed = json.loads(response_data)
                status_code = parsed.get("status_code", 0)
            except json.JSONDecodeError:
                status_code = 0  # Code nul en cas de réponse non interprétable

            # Affichage des messages selon le retour de l'API
            if status_code == 200:
                messagebox.showinfo("Scan", "Scan terminé et données envoyées vers le Nester")
                self.status_label.config(text="Scan et envoi réussis", fg="green")
            else:
                messagebox.showwarning("Envoi échoué", "Scan bien terminé mais impossible de les envoyer vers le Nester")
                self.status_label.config(text="Scan terminé, envoi vers Nester échoué", fg="orange")

        except Exception as e:
            # Erreur système lors du lancement du script
            messagebox.showerror("Erreur", f"Erreur système lors de l'envoi : {e}")
            self.status_label.config(text="Erreur lors de l'envoi vers le Nester", fg="red")

    def run_update(self):
        # Exécute le script de vérification de mise à jour
        result = subprocess.run(["python3", "/home/user/harvester/checkmaj.py"])

        # Retour 1 => Mise à jour disponible
        if result.returncode == 1:
            confirm = messagebox.askyesno("Mise à jour disponible", "Une mise à jour est disponible. Voulez-vous l’installer ?")
            if confirm:
                # Si l'utilisateur accepte, installation immédiate
                install = subprocess.run(["python3", "/home/user/harvester/installmaj.py"])
                if install.returncode == 0:
                    messagebox.showinfo("MAJ", "Mise à jour appliquée avec succès.")
                    self.refresh_dashboard()
                else:
                    messagebox.showerror("MAJ", "Échec de l'installation de la mise à jour.")
        elif result.returncode == 0:
            messagebox.showinfo("MAJ", "L'application est déjà à jour.")
        else:
            messagebox.showerror("MAJ", "Impossible de vérifier les mises à jour.")

    def refresh_dashboard(self):
        # Recharge les informations système à partir des modules internes
        ip, host = get_local_ip_hostname()
        latency = average_ping()
        scan_data = load_scan_report()

        # Mise à jour de l'affichage des labels
        self.lbl_ip.config(text=f"Adresse IP : {ip}")
        self.lbl_hostname.config(text=f"Nom de l'agent : {host}")
        self.lbl_machines.config(text=f"Machines détectées : {len(scan_data)}")
        self.lbl_latency.config(text=f"Latence WAN : {latency}")

        # Affichage détaillé des résultats du scan réseau dans la zone de texte
        self.txt_scan.delete("1.0", tk.END)
        for h, data in scan_data.items():
            ports = data['ports']
            port_text = ", ".join(map(str, ports)) if ports else "Aucun port ouvert"
            self.txt_scan.insert(tk.END, f"{h} ({data['hostname']}) -> Ports: {port_text}\n")

    def envoyer_vers_nester(self):
        # Fonction d'envoi manuel des données à l'API Nester
        try:
            result = subprocess.run(["python3", "send_to_nester.py"], capture_output=True, text=True)
            response_data = result.stdout.strip()

            # Parsing du JSON retourné
            try:
                parsed = json.loads(response_data)
                status_code = parsed.get("status_code", 0)
            except json.JSONDecodeError:
                status_code = 0

            # Gestion du retour
            if status_code == 200:
                messagebox.showinfo("Nester", "Données bien envoyées vers le Nester")
                self.status_label.config(text="Envoi vers Nester réussi", fg="green")
            else:
                messagebox.showerror("Échec", "Impossible d'envoyer les données vers le Nester")
                self.status_label.config(text="Échec d'envoi vers le Nester", fg="red")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exécution de l'envoi : {e}")
            self.status_label.config(text="Erreur critique lors de l'envoi", fg="red")

# Point d'entrée de l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = HarvesterApp(root)
    root.mainloop()