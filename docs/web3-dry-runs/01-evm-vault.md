# Dry Run 01 - EVM Vault Or Yield Strategy

Use [examples/evm-vault-target.json](examples/evm-vault-target.json).

## Expected Lane

- primary lane: `bounty-program-smart-contracts`
- first deep pass: `evm-protocol-audit`

## Bootstrap Checks

- `scope/chain-inventory.json`
- `scope/protocol-archetype.md` should classify `Vault / Yield Strategy`
- `scope/proxy-topology.md`
- `prep/protocol-invariants.md`
- `prep/web3-readiness.md`

## Hunting Checks

- finding bundle can contain `facts-chain.md`, `impact-financials.md`, `environment.md`
- EVM findings should name broken accounting or share invariants

## Reporting Checks

- `prepare_web3_report_bundle.py` should emit:
  - `web3-facts.json`
  - `asset-delta.md`
  - `reproduction-matrix.md`
