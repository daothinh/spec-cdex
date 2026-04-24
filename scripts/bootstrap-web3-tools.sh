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

if [[ "$mode" != "status" && "$mode" != "guide" ]]; then
  echo "usage: scripts/bootstrap-web3-tools.sh [status|guide]" >&2
  exit 1
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
