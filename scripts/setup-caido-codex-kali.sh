#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
INSTALL_SCRIPT="${SCRIPT_DIR}/install-caido-kali-latest.sh"
IMPORT_CERT_SCRIPT="${SCRIPT_DIR}/import-caido-chrome-cert.sh"
EXPORT_MANUAL_SCRIPT="${SCRIPT_DIR}/export-caido-manual-setup.sh"
CHROME_LAUNCHER_SCRIPT="${SCRIPT_DIR}/launch-caido-chrome.sh"
LIST_CHROME_PROFILES_SCRIPT="${SCRIPT_DIR}/list-chrome-profiles.sh"
CAIDO_WRAPPER="${REPO_ROOT}/plugins/caido/skills/caido-mode/scripts/caido"

CAIDO_URL="${CAIDO_URL:-http://localhost:8080}"
PAT="${CAIDO_PAT:-}"
CA_CERT_PATH=""
CHROME_USER_DATA_DIR="${CAIDO_CHROME_USER_DATA_DIR:-}"
CHROME_PROFILE_DIRECTORY="${CAIDO_CHROME_PROFILE_DIRECTORY:-}"
SKIP_INSTALL=0
SKIP_CERT_IMPORT=1
SKIP_CHROME_TEST=0
LAUNCH_CAIDO=1
CHOOSE_CHROME_PROFILE=0
LIST_CHROME_PROFILES_ONLY=0

REAL_USER="${SUDO_USER:-${USER}}"
REAL_HOME="$(getent passwd "${REAL_USER}" | cut -d: -f6 || true)"
[[ -n "${REAL_HOME}" ]] || REAL_HOME="${HOME}"
CA_CERT_EXPORT_DIR="${CAIDO_CERT_EXPORT_DIR:-${REAL_HOME}/.codex/caido}"

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

die() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/setup-caido-codex-kali.sh [options]

Options:
  --pat TOKEN           Caido PAT. If omitted, the script prompts when interactive.
  --ca-cert PATH        Path to the downloaded Caido CA certificate.
  --caido-url URL       Caido local API URL. Defaults to http://localhost:8080.
  --choose-profile      List detected Chrome profiles and let you reuse one.
  --list-profiles       Print detected Chrome/Chromium profiles and exit.
  --chrome-user-data-dir PATH
                        Reuse an existing Chrome user-data-dir.
  --chrome-profile-directory NAME
                        Reuse a specific profile directory inside the user-data-dir.
  --skip-install        Skip the system installer step.
  --import-cert         Automatically import the CA certificate into Chrome's NSS DB.
  --skip-cert-import    Keep Chrome setup manual. This is the default.
  --skip-chrome-test    Do not print or offer the Chrome launcher step.
  --no-launch-caido     Do not try to launch Caido automatically.
  -h, --help            Show this help text.

Behavior:
  1. Runs the existing Kali installer unless --skip-install is set.
  2. Ensures libnss3-tools is installed for Chrome/Chromium certificate import.
  3. Launches Caido and waits for localhost to respond.
  4. Reuses a saved PAT when available, otherwise prompts for one.
  5. Reuses an existing CA certificate, otherwise downloads it from the local Caido instance.
  6. Optionally reuses one of your existing Chrome profiles.
  7. Runs the repo's caido wrapper setup and exports manual PAT/cert/proxy values.
  8. Imports the CA cert into Chrome only when --import-cert is supplied.
EOF
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --pat)
        [[ $# -ge 2 ]] || die "--pat requires a value"
        PAT="$2"
        shift 2
        ;;
      --ca-cert)
        [[ $# -ge 2 ]] || die "--ca-cert requires a value"
        CA_CERT_PATH="$2"
        shift 2
        ;;
      --caido-url)
        [[ $# -ge 2 ]] || die "--caido-url requires a value"
        CAIDO_URL="$2"
        shift 2
        ;;
      --choose-profile)
        CHOOSE_CHROME_PROFILE=1
        shift
        ;;
      --list-profiles)
        LIST_CHROME_PROFILES_ONLY=1
        shift
        ;;
      --chrome-user-data-dir)
        [[ $# -ge 2 ]] || die "--chrome-user-data-dir requires a value"
        CHROME_USER_DATA_DIR="$2"
        shift 2
        ;;
      --chrome-profile-directory)
        [[ $# -ge 2 ]] || die "--chrome-profile-directory requires a value"
        CHROME_PROFILE_DIRECTORY="$2"
        shift 2
        ;;
      --skip-install)
        SKIP_INSTALL=1
        shift
        ;;
      --import-cert)
        SKIP_CERT_IMPORT=0
        shift
        ;;
      --skip-cert-import)
        SKIP_CERT_IMPORT=1
        shift
        ;;
      --skip-chrome-test)
        SKIP_CHROME_TEST=1
        shift
        ;;
      --no-launch-caido)
        LAUNCH_CAIDO=0
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done
}

run_as_real_user() {
  if [[ "${EUID}" -eq 0 && -n "${SUDO_USER:-}" ]]; then
    sudo -u "${REAL_USER}" -H \
      env \
        DISPLAY="${DISPLAY:-}" \
        XAUTHORITY="${XAUTHORITY:-}" \
        DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
        WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
        XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" \
      "$@"
  else
    "$@"
  fi
}

run_system_step() {
  if [[ "${EUID}" -ne 0 ]]; then
    sudo "$@"
  else
    "$@"
  fi
}

list_chrome_profiles() {
  [[ -f "${LIST_CHROME_PROFILES_SCRIPT}" ]] || die "Chrome profile listing script not found: ${LIST_CHROME_PROFILES_SCRIPT}"
  run_as_real_user bash "${LIST_CHROME_PROFILES_SCRIPT}" "$@"
}

validate_chrome_profile_inputs() {
  if [[ -n "${CHROME_PROFILE_DIRECTORY}" && -z "${CHROME_USER_DATA_DIR}" ]]; then
    die "--chrome-profile-directory requires --chrome-user-data-dir"
  fi
}

install_system_dependencies() {
  if [[ "${SKIP_INSTALL}" == "0" ]]; then
    [[ -f "${INSTALL_SCRIPT}" ]] || die "Install script not found: ${INSTALL_SCRIPT}"
    log "Running ${INSTALL_SCRIPT}"
    if [[ "${EUID}" -ne 0 ]]; then
      sudo -E CAIDO_SKIP_POST_SETUP=1 bash "${INSTALL_SCRIPT}"
    else
      CAIDO_SKIP_POST_SETUP=1 bash "${INSTALL_SCRIPT}"
    fi
  fi

  if ! command -v certutil >/dev/null 2>&1; then
    log "Installing libnss3-tools for Chrome/Chromium certificate management"
    run_system_step apt-get update
    run_system_step apt-get install -y libnss3-tools
  fi
}

caido_http_ready() {
  local status
  status="$(curl -ksS -o /dev/null -w '%{http_code}' "${CAIDO_URL}" || true)"
  [[ "${status}" =~ ^(200|204|301|302|303|307|308|401|403)$ ]]
}

launch_caido_if_needed() {
  [[ "${LAUNCH_CAIDO}" == "1" ]] || return 0

  if caido_http_ready; then
    return 0
  fi

  if ! command -v caido >/dev/null 2>&1; then
    die "Caido desktop command not found on PATH"
  fi

  log "Launching Caido desktop for ${REAL_USER}"
  run_as_real_user bash -lc "nohup caido >/tmp/caido-codex-bootstrap.log 2>&1 &"
}

wait_for_caido() {
  local attempts=60
  local i
  for ((i = 1; i <= attempts; i++)); do
    if caido_http_ready; then
      log "Caido is reachable at ${CAIDO_URL}"
      return 0
    fi
    sleep 2
  done

  die "Caido did not become reachable at ${CAIDO_URL}"
}

prompt_if_interactive() {
  [[ -t 0 ]]
}

read_saved_value() {
  local field="$1"
  local secrets_path="${REAL_HOME}/.codex/caido/secrets.json"

  [[ -f "${secrets_path}" ]] || return 0

  python3 - "${secrets_path}" "${field}" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
field = sys.argv[2]
value = ((data.get("caido") or {}).get(field))
if value:
    print(value)
PY
}

maybe_prompt_for_pat() {
  [[ -n "${PAT}" ]] && return 0

  PAT="$(read_saved_value pat)"
  if [[ -n "${PAT}" ]]; then
    log "Using saved Caido PAT from ${REAL_HOME}/.codex/caido/secrets.json"
    return 0
  fi

  if ! prompt_if_interactive; then
    return 0
  fi

  printf '\n'
  log "Finish these steps in Caido before continuing:"
  log "  1. Log in and create/open a project"
  log "  2. Create a PAT in https://dashboard.caido.io/developer"
  printf '\n'
  read -r -p "Press Enter once Caido is ready and you have the PAT..." _
  read -r -s -p "Enter your Caido PAT (leave blank to skip Codex auth bootstrap): " PAT
  printf '\n'
}

detect_default_ca_cert() {
  local candidate
  for candidate in \
    "${REAL_HOME}/Downloads/ca.crt" \
    "${REAL_HOME}/Downloads/caido.crt" \
    "${REAL_HOME}/Downloads/caido-ca.crt" \
    "${CA_CERT_EXPORT_DIR}/caido-ca.crt"
  do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

download_ca_cert_from_instance() {
  local cert_url="${CAIDO_URL%/}/ca.crt"
  local destination="${CA_CERT_EXPORT_DIR}/caido-ca.crt"

  if run_as_real_user env CERT_URL="${cert_url}" CERT_DEST="${destination}" bash -lc '
    mkdir -p "$(dirname "${CERT_DEST}")"
    curl -fsSL --retry 5 --retry-all-errors "${CERT_URL}" -o "${CERT_DEST}"
  '; then
    CA_CERT_PATH="${destination}"
    log "Downloaded Caido CA certificate from ${cert_url} to ${CA_CERT_PATH}"
    return 0
  fi

  rm -f "${destination}"
  return 1
}

maybe_prompt_for_ca_cert() {
  [[ -n "${CA_CERT_PATH}" ]] && return 0

  if CA_CERT_PATH="$(detect_default_ca_cert)"; then
    log "Detected downloaded CA certificate at ${CA_CERT_PATH}"
    return 0
  fi

  if download_ca_cert_from_instance; then
    return 0
  fi

  if ! prompt_if_interactive; then
    return 0
  fi

  read -r -p "Path to downloaded ca.crt (leave blank to leave Chrome cert path unset): " CA_CERT_PATH
}

maybe_choose_chrome_profile() {
  local selection
  local profile_index
  local selected
  local browser_name=""
  local profile_name=""
  local -a profiles=()

  if [[ -n "${CHROME_USER_DATA_DIR}" ]]; then
    return 0
  fi

  [[ "${CHOOSE_CHROME_PROFILE}" == "1" ]] || return 0

  mapfile -t profiles < <(list_chrome_profiles --tsv)
  if ((${#profiles[@]} == 0)); then
    log "No Chrome/Chromium profiles detected. Falling back to the separate Caido profile."
    return 0
  fi

  if ! prompt_if_interactive; then
    log "Profiles were detected, but profile selection requires an interactive shell."
    log "Pass --chrome-user-data-dir and optionally --chrome-profile-directory explicitly."
    return 0
  fi

  printf '\n'
  log "Detected Chrome/Chromium profiles:"
  list_chrome_profiles
  printf '\n'
  read -r -p "Select profile number to reuse through Caido (leave blank to keep the separate Caido profile): " selection
  [[ -n "${selection}" ]] || return 0
  [[ "${selection}" =~ ^[0-9]+$ ]] || die "Profile selection must be a number"

  profile_index=$((selection - 1))
  ((profile_index >= 0 && profile_index < ${#profiles[@]})) || die "Profile selection out of range"

  selected="${profiles[${profile_index}]}"
  IFS=$'\t' read -r browser_name CHROME_USER_DATA_DIR CHROME_PROFILE_DIRECTORY profile_name <<< "${selected}"
  log "Selected ${browser_name} profile '${profile_name}' (${CHROME_PROFILE_DIRECTORY})"
}

setup_codex_wrapper() {
  [[ -n "${PAT}" ]] || {
    log "Skipping Codex wrapper auth bootstrap because no PAT was provided"
    return 0
  }

  [[ -f "${CAIDO_WRAPPER}" ]] || die "Caido wrapper not found: ${CAIDO_WRAPPER}"

  log "Configuring the repo's Caido wrapper"
  run_as_real_user env CAIDO_PAT= CAIDO_URL= bash "${CAIDO_WRAPPER}" setup "${PAT}" "${CAIDO_URL}"
}

export_manual_setup() {
  local -a export_args=(
    --pat "${PAT}"
    --caido-url "${CAIDO_URL}"
  )

  [[ -f "${EXPORT_MANUAL_SCRIPT}" ]] || die "Export script not found: ${EXPORT_MANUAL_SCRIPT}"
  if [[ -n "${CA_CERT_PATH}" ]]; then
    export_args+=(--ca-cert "${CA_CERT_PATH}")
  fi
  if [[ -n "${CHROME_USER_DATA_DIR}" ]]; then
    export_args+=(--chrome-user-data-dir "${CHROME_USER_DATA_DIR}")
  fi
  if [[ -n "${CHROME_PROFILE_DIRECTORY}" ]]; then
    export_args+=(--chrome-profile-directory "${CHROME_PROFILE_DIRECTORY}")
  fi

  log "Exporting manual Chrome/Codex setup values"
  run_as_real_user env CAIDO_PAT= CAIDO_URL= bash "${EXPORT_MANUAL_SCRIPT}" "${export_args[@]}"
}

import_chrome_cert() {
  [[ "${SKIP_CERT_IMPORT}" == "0" ]] || return 0

  if [[ -z "${CA_CERT_PATH}" ]]; then
    log "Skipping Chrome certificate import because no ca.crt path was provided"
    return 0
  fi

  [[ -f "${CA_CERT_PATH}" ]] || die "Certificate file not found: ${CA_CERT_PATH}"
  [[ -f "${IMPORT_CERT_SCRIPT}" ]] || die "Import script not found: ${IMPORT_CERT_SCRIPT}"

  log "Importing Caido CA certificate into Chrome/Chromium NSS DB"
  run_as_real_user bash "${IMPORT_CERT_SCRIPT}" --cert "${CA_CERT_PATH}"
}

print_next_steps() {
  printf '\n'
  log "Bootstrap complete"
  log "Caido API URL: ${CAIDO_URL}"
  log "Codex secrets path: ${REAL_HOME}/.codex/caido/secrets.json"
  log "Manual export env: ${REAL_HOME}/.codex/caido/manual-setup.env"
  log "Manual export guide: ${REAL_HOME}/.codex/caido/manual-setup.txt"
  log "Chrome launcher: bash ${CHROME_LAUNCHER_SCRIPT}"
  if [[ -n "${CA_CERT_PATH}" ]]; then
    log "Caido CA certificate: ${CA_CERT_PATH}"
  fi
  if [[ -n "${CHROME_USER_DATA_DIR}" ]]; then
    log "Selected Chrome user-data-dir: ${CHROME_USER_DATA_DIR}"
  fi
  if [[ -n "${CHROME_PROFILE_DIRECTORY}" ]]; then
    log "Selected Chrome profile directory: ${CHROME_PROFILE_DIRECTORY}"
  fi

  if [[ "${SKIP_CHROME_TEST}" == "0" ]]; then
    log "To open the configured Chrome profile proxied through Caido:"
    log "  bash ${CHROME_LAUNCHER_SCRIPT}"
    log "  No proxy extension is required for that launcher flow."
  fi

  if [[ "${SKIP_CERT_IMPORT}" == "0" && -z "${CA_CERT_PATH}" ]]; then
    log "If you skipped certificate import, use Caido's preconfigured browser or rerun with --ca-cert /path/to/ca.crt"
  fi

  log "To verify Codex -> Caido auth:"
  log "  bash ${CAIDO_WRAPPER} health"
  log "  bash ${CAIDO_WRAPPER} recent --limit 5"
}

main() {
  parse_args "$@"
  need_cmd bash
  need_cmd curl
  need_cmd getent
  validate_chrome_profile_inputs

  if [[ "${LIST_CHROME_PROFILES_ONLY}" == "1" ]]; then
    list_chrome_profiles
    exit 0
  fi

  install_system_dependencies
  launch_caido_if_needed
  wait_for_caido
  maybe_prompt_for_pat
  maybe_prompt_for_ca_cert
  maybe_choose_chrome_profile
  setup_codex_wrapper
  export_manual_setup
  import_chrome_cert
  print_next_steps
}

main "$@"
