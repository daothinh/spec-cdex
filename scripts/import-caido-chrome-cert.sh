#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
CERT_PATH=""
NICKNAME="${CAIDO_CERT_NICKNAME:-Caido Local CA}"
declare -a NSSDB_DIRS=()

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
  bash scripts/import-caido-chrome-cert.sh --cert /path/to/ca.crt [--nickname "Caido Local CA"] [--nssdb-dir /path]

Options:
  --cert PATH        Path to the Caido CA certificate file to import.
  --nickname NAME    NSS nickname to use for the imported certificate.
  --nssdb-dir PATH   Import into one specific NSS database directory. May be repeated.
  -h, --help         Show this help text.

Notes:
  - If no --nssdb-dir is provided, the script imports into the active Chromium/Chrome
    shared NSS DB path(s) for Linux.
  - Chromium documents the default NSS shared DB as $HOME/.local/share/pki/nssdb,
    while older setups may still use $HOME/.pki/nssdb.
EOF
}

resolve_default_nssdb_dirs() {
  local modern_dir="${HOME}/.local/share/pki/nssdb"
  local legacy_dir="${HOME}/.pki/nssdb"

  if [[ -d "${modern_dir}" ]]; then
    NSSDB_DIRS+=("${modern_dir}")
  fi

  if [[ -d "${legacy_dir}" ]]; then
    NSSDB_DIRS+=("${legacy_dir}")
  fi

  if ((${#NSSDB_DIRS[@]} == 0)); then
    NSSDB_DIRS+=("${modern_dir}")
  fi
}

ensure_unique_nssdb_dirs() {
  local dir
  local seen=""
  local -a unique=()

  for dir in "${NSSDB_DIRS[@]}"; do
    [[ -n "${dir}" ]] || continue
    case "|${seen}|" in
      *"|${dir}|"*) continue ;;
    esac
    unique+=("${dir}")
    seen="${seen}|${dir}"
  done

  NSSDB_DIRS=("${unique[@]}")
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --cert)
        [[ $# -ge 2 ]] || die "--cert requires a value"
        CERT_PATH="$2"
        shift 2
        ;;
      --nickname)
        [[ $# -ge 2 ]] || die "--nickname requires a value"
        NICKNAME="$2"
        shift 2
        ;;
      --nssdb-dir)
        [[ $# -ge 2 ]] || die "--nssdb-dir requires a value"
        NSSDB_DIRS+=("$2")
        shift 2
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

ensure_nssdb() {
  local dir="$1"
  mkdir -p "${dir}"

  if [[ ! -f "${dir}/cert9.db" ]]; then
    certutil -N -d "sql:${dir}" --empty-password >/dev/null
  fi
}

import_into_nssdb() {
  local dir="$1"
  ensure_nssdb "${dir}"

  certutil -D -d "sql:${dir}" -n "${NICKNAME}" >/dev/null 2>&1 || true
  certutil -A -d "sql:${dir}" -n "${NICKNAME}" -t "C,," -i "${CERT_PATH}"
  certutil -L -d "sql:${dir}" -n "${NICKNAME}" >/dev/null
  log "Imported certificate into ${dir}"
}

main() {
  parse_args "$@"
  need_cmd certutil

  [[ -n "${CERT_PATH}" ]] || die "--cert is required"
  [[ -f "${CERT_PATH}" ]] || die "Certificate file not found: ${CERT_PATH}"

  if ((${#NSSDB_DIRS[@]} == 0)); then
    resolve_default_nssdb_dirs
  fi
  ensure_unique_nssdb_dirs

  local dir
  for dir in "${NSSDB_DIRS[@]}"; do
    import_into_nssdb "${dir}"
  done

  log "Done. Restart Chrome/Chromium if it was already running."
}

main "$@"
