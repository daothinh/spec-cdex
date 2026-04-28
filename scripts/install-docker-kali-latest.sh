#!/usr/bin/env bash
set -Eeuo pipefail

DOCKER_DEBIAN_CODENAME="${DOCKER_DEBIAN_CODENAME:-trixie}"
DOCKER_CHANNEL="${DOCKER_CHANNEL:-stable}"
DOCKER_PACKAGES=(
  docker-ce
  docker-ce-cli
  containerd.io
  docker-buildx-plugin
  docker-compose-plugin
)
CONFLICTING_PACKAGES=(
  docker.io
  docker-compose
  docker-compose-v2
  docker-doc
  podman-docker
  containerd
  runc
)

log() {
  printf '[docker-kali] %s\n' "$*"
}

die() {
  printf '[docker-kali] ERROR: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
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
    amd64|arm64|armhf|ppc64el) ;;
    *) die "Unsupported architecture: $(dpkg --print-architecture)" ;;
  esac

  case "${DOCKER_CHANNEL}" in
    stable|test) ;;
    *) die "DOCKER_CHANNEL must be 'stable' or 'test'. Current value: ${DOCKER_CHANNEL}" ;;
  esac
}

remove_conflicts() {
  local installed=()
  local pkg

  for pkg in "${CONFLICTING_PACKAGES[@]}"; do
    if dpkg-query -W -f='${db:Status-Abbrev}' "${pkg}" 2>/dev/null | grep -q '^ii'; then
      installed+=("${pkg}")
    fi
  done

  if ((${#installed[@]} == 0)); then
    log "No conflicting packages found"
    return
  fi

  log "Removing conflicting packages: ${installed[*]}"
  apt-get remove -y "${installed[@]}"
}

setup_repo() {
  local arch
  arch="$(dpkg --print-architecture)"

  log "Installing base dependencies"
  apt-get update
  apt-get install -y ca-certificates curl

  log "Setting up Docker apt repository for Debian '${DOCKER_DEBIAN_CODENAME}' (${DOCKER_CHANNEL})"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: ${DOCKER_DEBIAN_CODENAME}
Components: ${DOCKER_CHANNEL}
Architectures: ${arch}
Signed-By: /etc/apt/keyrings/docker.asc
EOF
}

install_docker() {
  log "Installing latest Docker packages"
  apt-get update
  apt-get install -y "${DOCKER_PACKAGES[@]}"
}

enable_service() {
  log "Enabling and starting Docker"
  systemctl enable --now docker
  systemctl is-active --quiet docker || die "Docker service failed to start"
}

post_install() {
  local target_user="${SUDO_USER:-}"

  if [[ -n "${target_user}" && "${target_user}" != "root" ]]; then
    if id -nG "${target_user}" | tr ' ' '\n' | grep -qx docker; then
      log "User '${target_user}' is already in the docker group"
    else
      log "Adding '${target_user}' to the docker group"
      usermod -aG docker "${target_user}"
      log "User '${target_user}' must log out and back in for group changes to apply"
    fi
  fi
}

verify_install() {
  log "Docker version: $(docker --version)"
  log "Compose version: $(docker compose version)"

  log "Running hello-world verification"
  docker run --rm hello-world >/dev/null
}

main() {
  ensure_root "$@"
  need_cmd apt-get
  need_cmd curl
  need_cmd dpkg-query
  need_cmd systemctl

  validate_host
  remove_conflicts
  setup_repo
  install_docker
  enable_service
  post_install
  verify_install

  log "Done"
  log "Installed channel: ${DOCKER_CHANNEL}"
  log "Debian codename used for Docker repo: ${DOCKER_DEBIAN_CODENAME}"
}

main "$@"
