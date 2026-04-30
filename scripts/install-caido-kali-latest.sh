#!/usr/bin/env bash
set -Eeuo pipefail

CAIDO_RELEASE_API="${CAIDO_RELEASE_API:-https://caido.download/releases/latest}"
CAIDO_CLI_ROOT="${CAIDO_CLI_ROOT:-/opt/caido-cli}"
NODE_CHANNEL="${NODE_CHANNEL:-lts}"
INSTALL_DESKTOP="${INSTALL_DESKTOP:-1}"
INSTALL_NODE_TOOLCHAIN="${INSTALL_NODE_TOOLCHAIN:-1}"
BOOTSTRAP_REPO_CAIDO="${BOOTSTRAP_REPO_CAIDO:-1}"
RUN_FULL_SETUP="${RUN_FULL_SETUP:-1}"
IMPORT_CERT_ON_SETUP="${IMPORT_CERT_ON_SETUP:-1}"
CAIDO_SKIP_POST_SETUP="${CAIDO_SKIP_POST_SETUP:-0}"
CAIDO_URL="${CAIDO_URL:-http://localhost:8080}"
CAIDO_PAT="${CAIDO_PAT:-}"
CHOOSE_CHROME_PROFILE="${CHOOSE_CHROME_PROFILE:-0}"
CHROME_USER_DATA_DIR="${CAIDO_CHROME_USER_DATA_DIR:-}"
CHROME_PROFILE_DIRECTORY="${CAIDO_CHROME_PROFILE_DIRECTORY:-}"
CAIDO_DESKTOP_PACKAGE=""

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SETUP_SCRIPT="${SCRIPT_DIR}/setup-caido-codex-kali.sh"
WORK_DIR="$(mktemp -d)"

REAL_USER="${SUDO_USER:-${USER}}"
REAL_HOME="$(getent passwd "${REAL_USER}" | cut -d: -f6 || true)"
[[ -n "${REAL_HOME}" ]] || REAL_HOME="${HOME}"

cleanup() {
  rm -rf -- "${WORK_DIR}"
}

trap cleanup EXIT

log() {
  printf '[caido-kali] %s\n' "$*"
}

die() {
  printf '[caido-kali] ERROR: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install-caido-kali-latest.sh [options]

Options:
  --pat TOKEN         Pass the Caido PAT through to the post-install setup step.
  --caido-url URL     Caido local API URL. Defaults to http://localhost:8080.
  --choose-profile    During setup, list detected Chrome profiles and reuse one.
  --chrome-user-data-dir PATH
                      Reuse an existing Chrome user-data-dir.
  --chrome-profile-directory NAME
                      Reuse a specific profile directory inside the user-data-dir.
  --skip-full-setup   Only install packages; do not launch the all-in-one setup flow.
  --no-import-cert    Do not import the Caido CA certificate into Chrome automatically.
  -h, --help          Show this help text.

Environment:
  NODE_CHANNEL=lts|current
  INSTALL_DESKTOP=0|1
  INSTALL_NODE_TOOLCHAIN=0|1
  BOOTSTRAP_REPO_CAIDO=0|1
  RUN_FULL_SETUP=0|1
  IMPORT_CERT_ON_SETUP=0|1

Notes:
  - If node/npm already exist for the real user (including via nvm), the installer
    will reuse them and skip system Node.js installation.
  - When run directly, this script can continue into the full Caido/Codex/Chrome setup.
EOF
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --pat)
        [[ $# -ge 2 ]] || die "--pat requires a value"
        CAIDO_PAT="$2"
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
      --skip-full-setup)
        RUN_FULL_SETUP=0
        shift
        ;;
      --no-import-cert)
        IMPORT_CERT_ON_SETUP=0
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

ensure_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    need_cmd sudo
    log "Re-running with sudo"
    exec sudo -E bash "$0" "$@"
  fi
}

validate_host() {
  [[ -r /etc/os-release ]] || die "Cannot read /etc/os-release"
  # shellcheck disable=SC1091
  source /etc/os-release

  [[ "${ID:-}" == "kali" ]] || die "This script only supports Kali Linux. Detected ID='${ID:-unknown}'"

  case "$(dpkg --print-architecture)" in
    amd64|arm64) ;;
    *) die "Unsupported architecture: $(dpkg --print-architecture). Supported: amd64, arm64" ;;
  esac

  case "${NODE_CHANNEL}" in
    lts|current) ;;
    *) die "NODE_CHANNEL must be 'lts' or 'current'. Current value: ${NODE_CHANNEL}" ;;
  esac
}

linux_arch_for_caido() {
  case "$(dpkg --print-architecture)" in
    amd64) printf 'x86_64\n' ;;
    arm64) printf 'aarch64\n' ;;
    *) die "Unsupported architecture: $(dpkg --print-architecture)" ;;
  esac
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

run_as_real_user_shell() {
  local shell_cmd="$1"
  local shell_init='export NVM_DIR="$HOME/.nvm"; if [ -s "$NVM_DIR/nvm.sh" ]; then . "$NVM_DIR/nvm.sh" >/dev/null 2>&1; fi'

  if [[ "${EUID}" -eq 0 && -n "${SUDO_USER:-}" ]]; then
    sudo -u "${REAL_USER}" -H \
      env \
        DISPLAY="${DISPLAY:-}" \
        XAUTHORITY="${XAUTHORITY:-}" \
        DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
        WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
        XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" \
        CAIDO_RUN_SHELL_CMD="${shell_cmd}" \
      bash -lc "${shell_init}; eval \"\$CAIDO_RUN_SHELL_CMD\""
  else
    env CAIDO_RUN_SHELL_CMD="${shell_cmd}" \
      bash -lc "${shell_init}; eval \"\$CAIDO_RUN_SHELL_CMD\""
  fi
}

user_has_node_toolchain() {
  run_as_real_user_shell 'command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1'
}

user_node_version() {
  run_as_real_user_shell 'node --version'
}

user_npm_version() {
  run_as_real_user_shell 'npm --version'
}

install_base_packages() {
  log "Installing base packages"
  apt-get update
  apt-get install -y ca-certificates curl git gnupg libnss3-tools python3 tar unzip xz-utils
}

fetch_caido_release() {
  local metadata_path="${WORK_DIR}/caido-release.json"
  local env_path="${WORK_DIR}/caido-release.env"
  local target_arch

  target_arch="$(linux_arch_for_caido)"

  log "Fetching latest Caido release metadata from ${CAIDO_RELEASE_API}"
  curl -fsSL --retry 5 --retry-all-errors "${CAIDO_RELEASE_API}" -o "${metadata_path}"

  python3 - "${metadata_path}" "${target_arch}" <<'PY' > "${env_path}"
import json
import shlex
import sys
from pathlib import Path

metadata_path = Path(sys.argv[1])
target_arch = sys.argv[2]
data = json.loads(metadata_path.read_text(encoding="utf-8"))

def pick(kind: str, fmt: str):
    for item in data.get("links", []):
        if (
            item.get("kind") == kind
            and item.get("os") == "linux"
            and item.get("arch") == target_arch
            and str(item.get("format", "")).lower() == fmt.lower()
        ):
            return item
    return None

cli = pick("cli", "tar.gz")
desktop = pick("desktop", "deb")
if cli is None:
    raise SystemExit(f"Could not find a Linux CLI release for arch={target_arch}")
if desktop is None:
    raise SystemExit(f"Could not find a Linux desktop .deb release for arch={target_arch}")

values = {
    "CAIDO_VERSION": data["version"],
    "CAIDO_CLI_URL": cli["link"],
    "CAIDO_CLI_HASH": cli["hash"],
    "CAIDO_DESKTOP_URL": desktop["link"],
    "CAIDO_DESKTOP_HASH": desktop["hash"],
}

for key, value in values.items():
    print(f"{key}={shlex.quote(str(value))}")
PY

  # shellcheck disable=SC1090
  source "${env_path}"
  log "Latest Caido release: v${CAIDO_VERSION}"
}

verify_sha512_b64() {
  local file_path="$1"
  local expected_b64="$2"
  local actual_b64

  actual_b64="$(
    python3 - "${file_path}" <<'PY'
import base64
import hashlib
import sys
from pathlib import Path

payload = Path(sys.argv[1]).read_bytes()
digest = hashlib.sha512(payload).digest()
print(base64.b64encode(digest).decode("ascii"))
PY
  )"

  [[ "${actual_b64}" == "${expected_b64}" ]] || die "Checksum mismatch for ${file_path}"
}

download_release_file() {
  local url="$1"
  local destination="$2"
  local expected_hash="$3"

  log "Downloading $(basename "${destination}")"
  curl -fsSL --retry 5 --retry-all-errors "${url}" -o "${destination}"
  verify_sha512_b64 "${destination}" "${expected_hash}"
}

install_caido_cli() {
  local cli_archive="${WORK_DIR}/$(basename "${CAIDO_CLI_URL}")"
  local version_dir="${CAIDO_CLI_ROOT}/v${CAIDO_VERSION}"
  local cli_bin

  download_release_file "${CAIDO_CLI_URL}" "${cli_archive}" "${CAIDO_CLI_HASH}"

  log "Installing caido-cli into ${version_dir}"
  rm -rf -- "${version_dir}"
  install -d -m 0755 "${version_dir}"
  tar -xzf "${cli_archive}" -C "${version_dir}"

  cli_bin="$(
    find "${version_dir}" -maxdepth 4 -type f -name 'caido-cli' -perm -u+x | head -n 1
  )"
  [[ -n "${cli_bin}" ]] || die "Could not locate caido-cli after extracting ${cli_archive}"

  install -d -m 0755 "${CAIDO_CLI_ROOT}"
  ln -sfn "${version_dir}" "${CAIDO_CLI_ROOT}/current"
  ln -sfn "${cli_bin}" /usr/local/bin/caido-cli
}

install_caido_desktop() {
  local desktop_deb="${WORK_DIR}/$(basename "${CAIDO_DESKTOP_URL}")"

  if [[ "${INSTALL_DESKTOP}" != "1" ]]; then
    log "Skipping Caido desktop install because INSTALL_DESKTOP=${INSTALL_DESKTOP}"
    return
  fi

  download_release_file "${CAIDO_DESKTOP_URL}" "${desktop_deb}" "${CAIDO_DESKTOP_HASH}"

  CAIDO_DESKTOP_PACKAGE="$(dpkg-deb -f "${desktop_deb}" Package)"
  log "Installing Caido desktop package"
  apt-get install -y "${desktop_deb}"
}

resolve_node_major() {
  python3 - "${NODE_CHANNEL}" <<'PY'
import json
import sys
import urllib.request

channel = sys.argv[1]
with urllib.request.urlopen("https://nodejs.org/dist/index.json") as response:
    versions = json.load(response)

def major(version: str) -> str:
    return version.lstrip("v").split(".", 1)[0]

if channel == "current":
    print(major(versions[0]["version"]))
    raise SystemExit

for entry in versions:
    if entry.get("lts"):
        print(major(entry["version"]))
        raise SystemExit

raise SystemExit("Could not resolve a Node.js version")
PY
}

install_node_toolchain() {
  local node_major

  if user_has_node_toolchain; then
    log "Using existing Node.js for ${REAL_USER}: $(user_node_version) / npm $(user_npm_version)"
    return
  fi

  if [[ "${INSTALL_NODE_TOOLCHAIN}" != "1" ]]; then
    die "Node.js/npm not found for ${REAL_USER} and INSTALL_NODE_TOOLCHAIN=${INSTALL_NODE_TOOLCHAIN}"
  fi

  node_major="$(resolve_node_major)"
  log "Installing system Node.js ${NODE_CHANNEL} channel (major ${node_major})"
  curl -fsSL --retry 5 --retry-all-errors "https://deb.nodesource.com/setup_${node_major}.x" | bash -
  apt-get install -y nodejs

  user_has_node_toolchain || die "Node.js/npm are still unavailable for ${REAL_USER} after installation"
  log "Installed Node.js for ${REAL_USER}: $(user_node_version) / npm $(user_npm_version)"
}

collect_caido_package_dirs() {
  local dirs=()
  local candidate

  for candidate in "${REPO_ROOT}/plugins/caido/skills/caido-mode"; do
    if [[ -f "${candidate}/package.json" ]]; then
      dirs+=("${candidate}")
    fi
  done

  printf '%s\n' "${dirs[@]}"
}

bootstrap_caido_workspace() {
  local dir="$1"
  local escaped_dir

  printf -v escaped_dir '%q' "${dir}"

  if [[ -f "${dir}/package-lock.json" ]]; then
    log "Bootstrapping ${dir} with npm ci"
    run_as_real_user_shell "cd ${escaped_dir} && npm ci --no-fund --no-audit"
  else
    log "Bootstrapping ${dir} with npm install"
    run_as_real_user_shell "cd ${escaped_dir} && npm install --no-fund --no-audit"
  fi
}

bootstrap_caido_workspaces() {
  local dir
  local found=0

  if [[ "${BOOTSTRAP_REPO_CAIDO}" != "1" ]]; then
    log "Skipping repo bootstrap because BOOTSTRAP_REPO_CAIDO=${BOOTSTRAP_REPO_CAIDO}"
    return
  fi

  user_has_node_toolchain || die "Cannot bootstrap repo packages because Node.js/npm are unavailable for ${REAL_USER}"

  while IFS= read -r dir; do
    [[ -n "${dir}" ]] || continue
    found=1
    bootstrap_caido_workspace "${dir}"
  done < <(collect_caido_package_dirs)

  if [[ "${found}" == "0" ]]; then
    log "No local caido-mode package directories found under ${REPO_ROOT}"
  fi
}

show_versions() {
  local desktop_version=""
  local desktop_package="${CAIDO_DESKTOP_PACKAGE:-caido}"

  log "Verification"
  log "Caido release API version: v${CAIDO_VERSION}"

  if command -v caido-cli >/dev/null 2>&1; then
    log "caido-cli path: $(command -v caido-cli)"
    if caido-cli --version >/dev/null 2>&1; then
      log "caido-cli version: $(caido-cli --version)"
    else
      log "caido-cli is installed but does not support '--version'; run 'caido-cli --help'"
    fi
  else
    die "caido-cli is not on PATH after installation"
  fi

  if [[ "${INSTALL_DESKTOP}" == "1" ]]; then
    if dpkg-query -W -f='${Version}' "${desktop_package}" >/dev/null 2>&1; then
      desktop_version="$(dpkg-query -W -f='${Version}' "${desktop_package}")"
      log "caido desktop package version (${desktop_package}): ${desktop_version}"
    elif command -v caido >/dev/null 2>&1; then
      log "caido desktop command: $(command -v caido)"
    else
      die "Caido desktop does not appear to be installed correctly"
    fi
  fi

  if user_has_node_toolchain; then
    log "Node.js for ${REAL_USER}: $(user_node_version)"
    log "npm for ${REAL_USER}: $(user_npm_version)"
  fi
}

run_full_setup() {
  local -a setup_args=(--skip-install)

  if [[ "${RUN_FULL_SETUP}" != "1" || "${CAIDO_SKIP_POST_SETUP}" == "1" ]]; then
    log "Skipping post-install setup"
    return
  fi

  [[ -f "${SETUP_SCRIPT}" ]] || die "Setup script not found: ${SETUP_SCRIPT}"

  if [[ "${IMPORT_CERT_ON_SETUP}" == "1" ]]; then
    setup_args+=(--import-cert)
  else
    setup_args+=(--skip-cert-import)
  fi

  if [[ -n "${CAIDO_PAT}" ]]; then
    setup_args+=(--pat "${CAIDO_PAT}")
  fi

  if [[ -n "${CAIDO_URL}" ]]; then
    setup_args+=(--caido-url "${CAIDO_URL}")
  fi
  if [[ "${CHOOSE_CHROME_PROFILE}" == "1" ]]; then
    setup_args+=(--choose-profile)
  fi
  if [[ -n "${CHROME_USER_DATA_DIR}" ]]; then
    setup_args+=(--chrome-user-data-dir "${CHROME_USER_DATA_DIR}")
  fi
  if [[ -n "${CHROME_PROFILE_DIRECTORY}" ]]; then
    setup_args+=(--chrome-profile-directory "${CHROME_PROFILE_DIRECTORY}")
  fi

  log "Running full Caido/Codex/Chrome bootstrap"
  bash "${SETUP_SCRIPT}" "${setup_args[@]}"
}

next_steps() {
  cat <<'EOF'
[caido-kali] Next steps
[caido-kali] 1. Run the all-in-one bootstrap:
[caido-kali]    bash scripts/setup-caido-codex-kali.sh --skip-install --import-cert
[caido-kali] 2. Launch the separate proxied Chrome profile:
[caido-kali]    bash scripts/launch-caido-chrome.sh
EOF
}

main() {
  parse_args "$@"
  ensure_root "$@"

  need_cmd apt-get
  need_cmd curl
  need_cmd dpkg
  need_cmd dpkg-deb
  need_cmd dpkg-query
  need_cmd find
  need_cmd getent
  need_cmd python3
  need_cmd tar

  validate_host
  install_base_packages
  fetch_caido_release
  install_caido_cli
  install_caido_desktop
  install_node_toolchain
  bootstrap_caido_workspaces
  show_versions
  run_full_setup

  if [[ "${RUN_FULL_SETUP}" != "1" || "${CAIDO_SKIP_POST_SETUP}" == "1" ]]; then
    next_steps
  fi
}

main "$@"
