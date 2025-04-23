#!/bin/bash

# Globals
SCRIPT_DIR="/home/user/harvester"
VENV_PATH="${SCRIPT_DIR}/harvester/bin/activate"
SCAN_SCRIPT="${SCRIPT_DIR}/network_scan.py"
SEND_SCRIPT="${SCRIPT_DIR}/send_to_nester.py"
PYTHON_CMD="python3"
LOG_FILE="${SCRIPT_DIR}/cron_scan.log"

# Force UTF-8 locale for consistent encoding
export LANG="fr_FR.UTF-8"
export LC_ALL="fr_FR.UTF-8"

trap 'on_exit' SIGINT SIGTERM
trap 'on_error ${LINENO}' ERR

on_exit() {
  printf "[EXIT] Script interrupted or terminated.\n" >&2
  return 1
}

on_error() {
  local lineno="$1"
  printf "[ERROR] An error occurred at line %s.\n" "$lineno" >&2
  return 1
}

sanitize_environment() {
  if [[ ! -f "$VENV_PATH" ]]; then
    printf "[ERROR] Virtualenv introuvable : %s\n" "$VENV_PATH" >&2
    return 1
  fi

  if [[ ! -f "$SCAN_SCRIPT" ]]; then
    printf "[ERROR] Script de scan manquant : %s\n" "$SCAN_SCRIPT" >&2
    return 1
  fi

  if [[ ! -f "$SEND_SCRIPT" ]]; then
    printf "[ERROR] Script d'envoi manquant : %s\n" "$SEND_SCRIPT" >&2
    return 1
  fi
}

activate_venv() {
  # shellcheck disable=SC1090
  source "$VENV_PATH" || {
    printf "[ERROR] Impossible d'activer le virtualenv.\n" >&2
    return 1
  }
}

run_scan() {
  printf "[INFO] Lancement du scan reseau...\n"
  local output;
  if ! output=$($PYTHON_CMD "$SCAN_SCRIPT" 2>&1); then
    printf "[SCAN ERROR] Le scan a echoue :\n%s\n" "$output" >&2
    return 1
  fi
  printf "[INFO] Scan termine avec succes.\n"
  return 0
}

send_to_nester() {
  printf "[INFO] Envoi des donnees a Nester...\n"
  local response;
  if ! response=$($PYTHON_CMD "$SEND_SCRIPT" 2>&1); then
    printf "[SEND ERROR] Echec de l'envoi :\n%s\n" "$response" >&2
    return 1
  fi

  local status_code;
  status_code=$(printf "%s" "$response" | grep -oE '"status_code"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+')

  if [[ "$status_code" == "200" ]]; then
    printf "[INFO] Donnees envoyees avec succes.\n"
    return 0
  fi

  printf "[WARNING] Reponse invalide ou echec d'envoi :\n%s\n" "$response" >&2
  return 1
}

main() {
  sanitize_environment || return 1
  activate_venv || return 1

  printf "===== Lancement automatique (%s) =====\n" "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

  if run_scan >> "$LOG_FILE" 2>&1; then
    if ! send_to_nester >> "$LOG_FILE" 2>&1; then
      printf "[INFO] Scan termine mais l'envoi a echoue.\n"
    fi
    printf "[SUCCESS] Operation terminee.\n"
  else
    printf "[ERROR] Le scan a echoue.\n" >&2
  fi

  printf "===== Fin du processus =====\n\n" >> "$LOG_FILE"
}

main