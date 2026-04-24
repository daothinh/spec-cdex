# Web3 Pipeline Contracts

This document defines the repo-local artifact contract for the upgraded web3-first security pipeline.

## Scope Artifacts

For web3-heavy targets, bootstrap should emit:

- `scope/target.json`
- `scope/chain-inventory.json`
- `scope/target-surface.md`
- `scope/smart-contracts.md`
- `scope/protocol-archetype.md`
- `scope/proxy-topology.md`
- `scope/dependency-boundaries.md`

## Prep Artifacts

Bootstrap should also emit:

- `prep/asset-inventory.md`
- `prep/tried-and-ruled-out.md`
- `prep/finding-pipeline.md`
- `prep/bootstrap-summary.md`
- `prep/attack-surface-map.md`
- `prep/protocol-invariants.md`
- `prep/web3-readiness.md`
- `prep/context-pack/`

## Context Pack

`prep/context-pack/` should contain:

- `trust-boundaries.md`
- `lane-decision.md`
- `asset-pointers.md`
- `protocol-archetype.md`
- `dependency-boundaries.md`
- `attack-surface-map.md`
- `web3-readiness.md` for web3-heavy targets

## Finding Bundle

Every finding bundle still uses the generic core files:

- `claim.md`
- `facts.md`
- `poc.md`
- `impact.md`
- `reverify.md`
- `severity.md`
- `artifacts/`

For web3 or exchange-heavy findings, add:

- `facts-chain.md`
- `impact-financials.md`
- `environment.md`

## Report Bundle

For web3 or exchange-heavy disclosures under `bug-bounty-reports/<slug>/<finding-id>/`, also generate:

- `web3-facts.json`
- `asset-delta.md`
- `reproduction-matrix.md`

## Readiness Expectations

`prep/web3-readiness.md` should record:

- whether `slither` is installed
- whether `forge` is installed
- whether `echidna` is installed
- whether `medusa` is installed
- whether `trailmark` is installed
- whether replay is `fork-capable`, `local-test-capable`, or `static-only`
- which missing tools block which audit paths

## Design Rule

Do not treat a web3 target as “just contracts” when the real authority surface spans:

- contracts
- web or API backends
- wallets or extensions
- relayers
- keepers
- signer services
- exchanges
- oracles

The artifacts above exist so the split pipeline can keep those boundaries visible across bootstrap, hunting, reverify, and submission.
