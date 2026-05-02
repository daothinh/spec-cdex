#!/usr/bin/env bash
set -euo pipefail

mode="${1:-status}"

tools=(
  "slither|Slither|pipx install slither-analyzer|Solidity static extraction; ERC conformance checks; upgradeability review automation"
  "forge|Foundry|Use https://book.getfoundry.sh/getting-started/installation|mainnet fork replay; Foundry PoC validation; state-diff simulation"
  "echidna|Echidna|Download a release from https://github.com/crytic/echidna/releases|EVM invariant fuzzing"
  "medusa|Medusa|go install github.com/crytic/medusa@latest|parallel smart-contract fuzzing"
  "trailmark|Trailmark|uv pip install trailmark|graph-based attack-surface and blast-radius analysis"
)

log() {
  printf '[web3-bootstrap] %s\n' "$*"
}

ensure_tool() {
  local command="$1"
  case "$command" in
    slither)
      if command -v pipx >/dev/null 2>&1; then
        pipx install slither-analyzer
      elif command -v python3 >/dev/null 2>&1; then
        python3 -m pip install --user slither-analyzer
      else
        return 1
      fi
      ;;
    forge)
      if command -v curl >/dev/null 2>&1; then
        bash -lc 'curl -L https://foundry.paradigm.xyz | bash'
        if command -v foundryup >/dev/null 2>&1; then
          foundryup
        elif [[ -x "${HOME}/.foundry/bin/foundryup" ]]; then
          "${HOME}/.foundry/bin/foundryup"
        else
          return 1
        fi
      else
        return 1
      fi
      ;;
    medusa)
      if command -v go >/dev/null 2>&1; then
        go install github.com/crytic/medusa@latest
      else
        return 1
      fi
      ;;
    trailmark)
      if command -v python3 >/dev/null 2>&1; then
        python3 -m pip install --user trailmark
      else
        return 1
      fi
      ;;
    *)
      return 1
      ;;
  esac
}

if [[ "$mode" != "status" && "$mode" != "guide" && "$mode" != "ensure" ]]; then
  echo "usage: scripts/bootstrap-web3-tools.sh [status|guide|ensure]" >&2
  exit 1
fi

if [[ "$mode" == "ensure" ]]; then
  for spec in "${tools[@]}"; do
    IFS="|" read -r command label install blocks <<<"$spec"
    if command -v "$command" >/dev/null 2>&1; then
      log "$label already installed"
      continue
    fi
    if ensure_tool "$command"; then
      log "Installed $label"
    else
      log "Skipped auto-install for $label"
    fi
  done
fi

printf "%-12s %-12s %-10s %s\n" "TOOL" "COMMAND" "STATUS" "SOURCE"
for spec in "${tools[@]}"; do
  IFS="|" read -r command label install blocks <<<"$spec"
  if source_path="$(command -v "$command" 2>/dev/null)"; then
    printf "%-12s %-12s %-10s %s\n" "$label" "$command" "installed" "$source_path"
  else
    printf "%-12s %-12s %-10s %s\n" "$label" "$command" "missing" "-"
  fi
done

if [[ "$mode" == "guide" ]]; then
  echo
  echo "Install guidance:"
fi

if [[ "$mode" == "guide" || "$mode" == "status" ]]; then
  for spec in "${tools[@]}"; do
    IFS="|" read -r command label install blocks <<<"$spec"
    if ! command -v "$command" >/dev/null 2>&1; then
      echo
      echo "$label ($command)"
      echo "  install: $install"
      echo "  blocks:  $blocks"
    fi
  done
fi
