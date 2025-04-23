# main.py
import tkinter as tk  # Importe Tkinter pour la gestion de l’interface graphique
from dashboard_ui import HarvesterApp  # Importe l'application GUI principale depuis le module dédié

if __name__ == "__main__":
    # Point d'entrée du programme : crée la fenêtre principale Tkinter
    root = tk.Tk()
    app = HarvesterApp(root)  # Initialise l'interface graphique via la classe définie dans dashboard_ui.py
    root.mainloop()  # Lance la boucle principale de l’interface 