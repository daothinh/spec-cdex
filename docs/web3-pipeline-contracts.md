# Web3 Pipeline Contracts

This document defines the repo-local artifact contract for the upgraded web3-first security pipeline.

All web3-heavy findings also follow [security-finding-verification-contract.md](security-finding-verification-contract.md). In particular, a transaction, event, queued settlement, or initiated payout is not enough on its own. The finding must prove the attacker-visible consequence and, when relevant, the value-realization or settlement step.

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
- `prep/environment-readiness.md`
- `prep/environment-readiness.json`
- `prep/attack-surface-map.md`
- `prep/protocol-invariants.md`
- `prep/domain-logic.md`
- `prep/manual-review-checkpoint.md`
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
- `domain-logic.md`
- `environment-readiness.md` when bootstrap assessed or repaired the local toolchain
- `web3-readiness.md` for web3-heavy targets

## Finding Bundle

Every finding bundle still uses the generic core files:

- `claim.md`
- `facts.md`
- `poc.md`
- `impact.md`
- `reverify.md` with gate review and verdict
- `severity.md`
- `manual-review.md`
- `artifacts/`

For web3 or exchange-heavy findings, add:

- `facts-chain.md`
- `impact-financials.md` with observed settlement or asset delta kept separate from inferred blast radius
- `environment.md`

## Report Bundle

For web3 or exchange-heavy disclosures under `bug-bounty-reports/<slug>/<finding-id>/`, also generate:

- `web3-facts.json`
- `asset-delta.md`
- `reproduction-matrix.md`
- `manual-review.md` copied from the verified finding bundle

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

## Verification Rule

For web3-heavy and exchange-heavy findings, do not stop at code reachability or an intermediate event. The finding must prove:

- how the attacker satisfies the decisive signature, proof, witness, preimage, or approval gate
- how settlement or value realization actually occurs
- why any relayer, keeper, signer, or off-chain engine dependency does not kill exploitability
