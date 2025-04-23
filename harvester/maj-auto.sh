#!/bin/bash
# maj-auto.sh - Verification et installation des mises a jours

# Variables globales 
SCRIPT_DIR="/home/user/harvester"          # Dossier où se trouvent les scripts Python
CHECK_SCRIPT="${SCRIPT_DIR}/checkmaj.py"   # Script de détection de mise à jour
INSTALL_SCRIPT="${SCRIPT_DIR}/installmaj.py" # Script d’installation de la mise à jour
PYTHON_CMD="/usr/bin/python3"              # Interpréteur Python à utiliser
LOG_FILE="${SCRIPT_DIR}/maj_auto.log"      # Fichier de journal

# Gestion des signaux / erreurs 
trap 'on_exit'  SIGINT SIGTERM             
trap 'on_error ${LINENO}' ERR              

on_exit() {                                # Exécuté quand le script est interrompu
  printf "[EXIT] Script interrompu ou terminé.\n" >&2
  return 1
}

on_error() {                               # Exécuté sur la première erreur non gérée
  local lineno="$1"                        
  printf "[ERROR] Erreur détectée à la ligne %s.\n" "$lineno" >&2
  return 1
}

# Vérifications préalables
sanitize_environment() {
  # Vérifie que l’interpréteur Python existe et est exécutable
  if [[ ! -x "$PYTHON_CMD" ]]; then
    printf "[ERROR] Interpréteur Python introuvable : %s\n" "$PYTHON_CMD" >&2
    return 1
  fi
  # Vérifie la présence des scripts Python
  if [[ ! -f "$CHECK_SCRIPT" ]]; then
    printf "[ERROR] Script de vérification manquant : %s\n" "$CHECK_SCRIPT" >&2
    return 1
  fi
  if [[ ! -f "$INSTALL_SCRIPT" ]]; then
    printf "[ERROR] Script d’installation manquant : %s\n" "$INSTALL_SCRIPT" >&2
    return 1
  fi
}

# Détection de mise à jour
run_update_check() {
  local output
  output=$("$PYTHON_CMD" "$CHECK_SCRIPT" 2>/dev/null)   # Lance checkmaj.py en silence
  printf "[DEBUG] Sortie checkmaj : %s\n" "$output"      # Log de débogage

  # Recherche la chaîne “Update available” (insensible à la casse)
  if printf "%s" "$output" | grep -iq "Update available"; then
    printf "[INFO] Mise à jour disponible détectée.\n"
    return 0   # 0 = succès → mise à jour requise
  fi

  printf "[INFO] Aucune mise à jour trouvée.\n"
  return 1     # 1 = rien à faire
}

# Installation de la mise à jour 
run_install_update() {
  local result
  result=$("$PYTHON_CMD" "$INSTALL_SCRIPT" 2>/dev/null) # Exécute installmaj.py
  printf "[INFO] Mise à jour appliquée :\n%s\n" "$result"
}

# Fonction principale 
main() {
  sanitize_environment || return 1                      # Stop si pré‑requis manquants

  printf "\n===== Vérification MAJ - %s =====\n" \
         "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE" # Timestamp dans le log

  # Si une MAJ est détectée → on l’installe (tee écrit aussi dans le log)
  if run_update_check | tee -a "$LOG_FILE"; then
    run_install_update | tee -a "$LOG_FILE"
  fi

  printf "===== Fin de vérification =====\n" >> "$LOG_FILE"
}

main   # Point d’entrée du script
