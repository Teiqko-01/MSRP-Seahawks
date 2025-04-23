#!/bin/bash
# scan-auto.sh – lance un scan réseau puis envoie le résultat à Nester

# Variables globales
SCRIPT_DIR="/home/user/harvester"              # Dossier base du projet
VENV_PATH="${SCRIPT_DIR}/harvester/bin/activate" # Fichier d’activation du venv
SCAN_SCRIPT="${SCRIPT_DIR}/network_scan.py"    # Script Python de scan réseau
SEND_SCRIPT="${SCRIPT_DIR}/send_to_nester.py"  # Script Python d’envoi
PYTHON_CMD="python3"                           # Interpréteur Python (dans le venv)
LOG_FILE="${SCRIPT_DIR}/cron_scan.log"         # Fichier log

# Locale UTF‑8 forcée pour éviter les problèmes d’encodage
export LANG="fr_FR.UTF-8"
export LC_ALL="fr_FR.UTF-8"

# Gestion des signaux et des erreurs
trap 'on_exit'              SIGINT SIGTERM   # Interruption ou terminaison
trap 'on_error ${LINENO}'   ERR              # Toute commande en erreur

on_exit() {                                 # Appelé lors d’un SIGINT/SIGTERM
  printf "[EXIT] Script interrupted or terminated.\n" >&2
  return 1
}

on_error() {                                # Appelé sur la première erreur
  local lineno="$1"                         # Numéro de ligne fautive
  printf "[ERROR] An error occurred at line %s.\n" "$lineno" >&2
  return 1
}

sanitize_environment() {                    # Vérifie la présence des éléments clés
  [[ -f "$VENV_PATH"   ]] || { printf "[ERROR] Virtualenv introuvable : %s\n" "$VENV_PATH" >&2;   return 1; }
  [[ -f "$SCAN_SCRIPT" ]] || { printf "[ERROR] Script de scan manquant : %s\n"   "$SCAN_SCRIPT" >&2; return 1; }
  [[ -f "$SEND_SCRIPT" ]] || { printf "[ERROR] Script d'envoi manquant : %s\n"  "$SEND_SCRIPT" >&2; return 1; }
}

activate_venv() {                           # Active l’environnement virtuel Python
  # shellcheck disable=SC1090
  source "$VENV_PATH" || { printf "[ERROR] Impossible d'activer le virtualenv.\n" >&2; return 1; }
}

run_scan() {                                # Lance le scan réseau
  printf "[INFO] Lancement du scan reseau...\n"
  local output
  if ! output=$($PYTHON_CMD "$SCAN_SCRIPT" 2>&1); then
    printf "[SCAN ERROR] Le scan a echoue :\n%s\n" "$output" >&2
    return 1
  fi
  printf "[INFO] Scan termine avec succes.\n"
}

send_to_nester() {                          # Envoie les données générées
  printf "[INFO] Envoi des donnees a Nester...\n"
  local response
  if ! response=$($PYTHON_CMD "$SEND_SCRIPT" 2>&1); then
    printf "[SEND ERROR] Echec de l'envoi :\n%s\n" "$response" >&2
    return 1
  fi

  local status_code
  status_code=$(printf "%s" "$response" | grep -oE '"status_code"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+')

  [[ "$status_code" == "200" ]] && { printf "[INFO] Donnees envoyees avec succes.\n"; return 0; }

  printf "[WARNING] Reponse invalide ou echec d'envoi :\n%s\n" "$response" >&2
  return 1
}

main() {
  sanitize_environment   || return 1        # Vérifications préalables
  activate_venv          || return 1        # Activation du venv

  printf "Lancement automatique (%s)\n" "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

  if run_scan >> "$LOG_FILE" 2>&1; then
    if ! send_to_nester >> "$LOG_FILE" 2>&1; then
      printf "[INFO] Scan termine mais l'envoi a echoue.\n"
    fi
    printf "[SUCCESS] Operation terminee.\n"
  else
    printf "[ERROR] Le scan a echoue.\n" >&2
  fi

  printf "Fin du processus\n\n" >> "$LOG_FILE"
}

main                                          # Point d’entrée du script
