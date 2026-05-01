#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
CONFIG_ENV_PATH="${CAIDO_CONFIG_ENV:-${HOME}/.codex/caido/manual-setup.env}"
if [[ -f "${CONFIG_ENV_PATH}" ]]; then
  # shellcheck disable=SC1090
  source "${CONFIG_ENV_PATH}"
fi

PROFILE_DIR="${CAIDO_CHROME_PROFILE_DIR:-${HOME}/.config/caido-codex-chrome}"
CHROME_USER_DATA_DIR="${CAIDO_CHROME_USER_DATA_DIR:-}"
CHROME_PROFILE_DIRECTORY="${CAIDO_CHROME_PROFILE_DIRECTORY:-}"
PROXY_SERVER="${CAIDO_PROXY_SERVER:-127.0.0.1:8080}"
PROXY_BYPASS_LIST="${CAIDO_PROXY_BYPASS_LIST:-<-loopback>}"
CHROME_COMMAND="${CAIDO_CHROME_COMMAND:-}"
QUIET_MODE="${CAIDO_CHROME_QUIET_MODE:-1}"
GPU_MODE="${CAIDO_CHROME_GPU_MODE:-swiftshader}"
CHROME_EXTRA_ARGS="${CAIDO_CHROME_EXTRA_ARGS:-}"

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

die() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

detect_chrome_command() {
  local candidate
  for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/launch-caido-chrome.sh [chrome-args...]

Environment overrides:
  CAIDO_CONFIG_ENV          Optional env file to source before launching.
  CAIDO_CHROME_COMMAND      Browser binary to launch.
  CAIDO_CHROME_PROFILE_DIR  Separate user-data-dir for the Caido session.
  CAIDO_CHROME_USER_DATA_DIR
                            Existing Chrome user-data-dir to reuse.
  CAIDO_CHROME_PROFILE_DIRECTORY
                            Existing profile directory inside the user-data-dir.
  CAIDO_PROXY_SERVER        Proxy host:port, defaults to 127.0.0.1:8080.
  CAIDO_PROXY_BYPASS_LIST   Proxy bypass list, defaults to <-loopback>.
  CAIDO_CHROME_QUIET_MODE   1 to reduce Chrome background-service noise
                            (default), 0 to keep Chrome's normal behavior.
  CAIDO_CHROME_GPU_MODE     swiftshader (default), system, or disabled.
  CAIDO_CHROME_EXTRA_ARGS   Extra Chrome args appended before CLI args.
EOF
}

is_enabled() {
  case "$1" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    0|false|FALSE|no|NO|off|OFF|"") return 1 ;;
    *) die "Unsupported boolean value: $1" ;;
  esac
}

append_default_runtime_args() {
  local -n args_ref="$1"

  if is_enabled "${QUIET_MODE}"; then
    args_ref+=(
      --no-first-run
      --no-default-browser-check
      --disable-background-networking
      --disable-component-update
      --disable-domain-reliability
      --disable-sync
      --metrics-recording-only
    )
  fi

  case "${GPU_MODE}" in
    ""|swiftshader)
      args_ref+=(
        --ignore-gpu-blocklist
        --use-gl=swiftshader
        --enable-unsafe-swiftshader
        --disable-features=VaapiVideoDecoder
      )
      ;;
    system)
      ;;
    disabled)
      args_ref+=(
        --disable-gpu
        --disable-features=VaapiVideoDecoder
      )
      ;;
    *)
      die "Unsupported CAIDO_CHROME_GPU_MODE value: ${GPU_MODE} (expected swiftshader, system, or disabled)"
      ;;
  esac
}

append_extra_args() {
  local -n args_ref="$1"
  local -a extra_args=()

  [[ -n "${CHROME_EXTRA_ARGS}" ]] || return 0
  # Intentionally split on shell-style whitespace for simple flag injection.
  # shellcheck disable=SC2206
  extra_args=(${CHROME_EXTRA_ARGS})
  args_ref+=("${extra_args[@]}")
}

main() {
  local -a chrome_args=()

  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  if [[ -z "${CHROME_COMMAND}" ]]; then
    CHROME_COMMAND="$(detect_chrome_command)" || die "Could not detect a Chrome/Chromium binary"
  fi

  if [[ -n "${CHROME_PROFILE_DIRECTORY}" && -z "${CHROME_USER_DATA_DIR}" ]]; then
    die "CAIDO_CHROME_PROFILE_DIRECTORY requires CAIDO_CHROME_USER_DATA_DIR"
  fi

  if [[ -n "${CHROME_USER_DATA_DIR}" ]]; then
    [[ -d "${CHROME_USER_DATA_DIR}" ]] || die "Configured Chrome user-data-dir not found: ${CHROME_USER_DATA_DIR}"
    chrome_args+=(--user-data-dir="${CHROME_USER_DATA_DIR}")
    if [[ -n "${CHROME_PROFILE_DIRECTORY}" ]]; then
      chrome_args+=(--profile-directory="${CHROME_PROFILE_DIRECTORY}")
    fi
    log "Launching ${CHROME_COMMAND} with proxy ${PROXY_SERVER} using existing Chrome user-data-dir ${CHROME_USER_DATA_DIR}${CHROME_PROFILE_DIRECTORY:+ (profile ${CHROME_PROFILE_DIRECTORY})}"
    log "Close other Chrome windows using this profile first to avoid profile lock conflicts."
  else
    mkdir -p "${PROFILE_DIR}"
    chrome_args+=(--user-data-dir="${PROFILE_DIR}")
    log "Launching ${CHROME_COMMAND} with proxy ${PROXY_SERVER} and profile ${PROFILE_DIR}"
  fi

  append_default_runtime_args chrome_args
  append_extra_args chrome_args
  log "Chrome runtime mode: quiet=${QUIET_MODE} gpu=${GPU_MODE}${CHROME_EXTRA_ARGS:+ extra-args=${CHROME_EXTRA_ARGS}}"

  exec "${CHROME_COMMAND}" \
    "${chrome_args[@]}" \
    --proxy-server="${PROXY_SERVER}" \
    --proxy-bypass-list="${PROXY_BYPASS_LIST}" \
    "$@"
}

main "$@"
