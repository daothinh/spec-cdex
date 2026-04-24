# Web3 Pipeline Dry Runs

These dry runs are lightweight acceptance scenarios for the upgraded web3-first security pipeline.

Each scenario gives:

- a sample `target.json`
- expected primary and follow-on lanes
- the bootstrap artifacts that should appear
- the minimum finding-bundle and report-bundle checks to confirm migration health

## Scenarios

- [01-evm-vault.md](01-evm-vault.md)
- [02-hybrid-web-contract.md](02-hybrid-web-contract.md)
- [03-solana-program.md](03-solana-program.md)
- [04-exchange-settlement.md](04-exchange-settlement.md)

## Example Inputs

- [examples/evm-vault-target.json](examples/evm-vault-target.json)
- [examples/hybrid-web-contract-target.json](examples/hybrid-web-contract-target.json)
- [examples/solana-program-target.json](examples/solana-program-target.json)
- [examples/exchange-settlement-target.json](examples/exchange-settlement-target.json)

## Acceptance Goal

The upgrade is only healthy when these dry runs no longer collapse into generic routing and can carry web3-specific artifacts from bootstrap through submission packaging.
