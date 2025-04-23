# app.py
from routes import routes  # Importation des routes définies dans un module séparé
from flask import Flask    # Importation de Flask, framework léger pour créer des applications web

app = Flask(__name__)  # Création de l'application Flask

# Enregistrement du blueprint contenant les routes, permet de modulariser l'app
app.register_blueprint(routes)

# Point d'entrée de l'application
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)  # Lancement du serveur Flask en mode debug