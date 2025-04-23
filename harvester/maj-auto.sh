#!/bin/bash

# maj-auto.sh - Verification et installation automatique des mises a jour

# Globals
SCRIPT_DIR="/home/user/harvester"
CHECK_SCRIPT="${SCRIPT_DIR}/checkmaj.py"
INSTALL_SCRIPT="${SCRIPT_DIR}/installmaj.py"
PYTHON_CMD="/usr/bin/python3"
LOG_FILE="${SCRIPT_DIR}/maj_auto.log"

trap 'on_exit' SIGINT SIGTERM
trap 'on_error ${LINENO}' ERR

on_exit() {
  printf "[EXIT] Script interrompu ou termine.\n" >&2
  return 1
}

on_error() {
  local lineno="$1"
  printf "[ERROR] Erreur detectee a la ligne %s.\n" "$lineno" >&2
  return 1
}

sanitize_environment() {
  if [[ ! -x "$PYTHON_CMD" ]]; then
    printf "[ERROR] Interpreteur Python introuvable a %s\n" "$PYTHON_CMD" >&2
    return 1
  fi

  if [[ ! -f "$CHECK_SCRIPT" ]]; then
    printf "[ERROR] Script de verification manquant : %s\n" "$CHECK_SCRIPT" >&2
    return 1
  fi

  if [[ ! -f "$INSTALL_SCRIPT" ]]; then
    printf "[ERROR] Script d'installation manquant : %s\n" "$INSTALL_SCRIPT" >&2
    return 1
  fi
}

run_update_check() {
  local output;
  output=$("$PYTHON_CMD" "$CHECK_SCRIPT" 2>/dev/null)

  printf "[DEBUG] Sortie checkmaj : %s\n" "$output"

  if printf "%s" "$output" | grep -iq "Update available"; then
    printf "[INFO] Mise a jour disponible detectee.\n"
    return 0
  fi

  printf "[INFO] Aucune mise a jour trouvee.\n"
  return 1
}

run_install_update() {
  local result;
  result=$("$PYTHON_CMD" "$INSTALL_SCRIPT" 2>/dev/null)

  printf "[INFO] Mise a jour appliquee :\n%s\n" "$result"
}

main() {
  sanitize_environment || return 1

  printf "\n===== Verification MAJ - %s =====\n" "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

  if run_update_check | tee -a "$LOG_FILE"; then
    run_install_update | tee -a "$LOG_FILE"
  fi

  printf "===== Fin de verification =====\n" >> "$LOG_FILE"
}

main