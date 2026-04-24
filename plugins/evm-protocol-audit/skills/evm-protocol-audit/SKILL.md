---
name: evm-protocol-audit
description: >-
  Structured EVM protocol and DeFi security audits. Use when reviewing Solidity
  or Vyper systems with privileged entry points, accounting invariants,
  token integrations, oracle dependencies, callbacks, or upgrade logic.
---

# EVM Protocol Audit

Activate this skill when the target is primarily EVM-based:

- Solidity or Vyper source
- Foundry, Hardhat, or Truffle projects
- proxy or upgradeable contracts
- DeFi protocols with pools, vaults, lending, staking, bridges, governance, or market logic

Load these references on demand:

- [references/CHEATSHEET.md](references/CHEATSHEET.md)
- [references/scoring.md](references/scoring.md)
- [references/vulnerability-taxonomy.md](references/vulnerability-taxonomy.md)
- [references/protocol-archetypes.md](references/protocol-archetypes.md)
- [references/report-template.md](references/report-template.md)
- [references/agents/explorer.md](references/agents/explorer.md)
- [references/agents/auth-upgrade-scanner.md](references/agents/auth-upgrade-scanner.md)
- [references/agents/accounting-invariant-scanner.md](references/agents/accounting-invariant-scanner.md)
- [references/agents/integration-callback-scanner.md](references/agents/integration-callback-scanner.md)
- [references/agents/oracle-market-scanner.md](references/agents/oracle-market-scanner.md)
- [references/agents/adversarial-scanner.md](references/agents/adversarial-scanner.md)

## Workflow

### Phase 0 - Scope And Baseline

1. If `audit-targets/<slug>/` exists, load:
   - `scope/chain-inventory.json`
   - `scope/protocol-archetype.md`
   - `scope/proxy-topology.md`
   - `scope/dependency-boundaries.md`
   - `prep/attack-surface-map.md`
   - `prep/protocol-invariants.md`
   - `prep/web3-readiness.md`
2. If the target is not bootstrapped, still continue, but explicitly note missing chain inventory, proxy topology, and replay readiness.
3. Read `references/CHEATSHEET.md` and `references/scoring.md` before scanning.
4. Load the matching protocol pack from `references/protocols/` once the archetype is clear.

### Phase 1 - Explore

Use [references/agents/explorer.md](references/agents/explorer.md) as the exploration contract.

The exploration phase must output:

- framework and build system
- proxy and upgrade topology
- protocol archetype
- key value-bearing entry points
- callback and integration surfaces
- oracle and external dependency surfaces
- highest-value trust boundaries

### Phase 2 - Adaptive Scan Strategy

Choose the scan shape by target size:

- Small: one combined pass using the full cheatsheet
- Medium: four scanner passes
- Large: four scanner passes plus an adversarial pass

Scanner families:

1. auth and upgrade
2. accounting and invariants
3. integrations and callbacks
4. oracle and market logic
5. adversarial cross-check for deep mode

Protocol packs available under `references/protocols/`:

- `token-vesting-escrow.md`
- `amm-dex-pool.md`
- `vault-yield-strategy.md`
- `lending-borrowing.md`
- `staking-rewards.md`
- `bridge-messaging.md`
- `governance-timelock.md`
- `perps-orderbook-exchange.md`
- `nft-marketplace.md`
- `oracle-consumer.md`

### Phase 3 - Validation And Falsification

For each candidate:

1. identify the decisive state transition
2. show who controls each decisive variable
3. separate observed impact from inferred blast radius
4. test the strongest blockers from `references/scoring.md`
5. downgrade or drop anything that depends on unrealistic capital, oracle, role, or governance assumptions

### Phase 4 - Report

Use [references/report-template.md](references/report-template.md).

Every confirmed finding should name:

- taxonomy ID
- file and line
- vulnerable boundary
- attacker preconditions
- asset or market at risk
- observed impact
- confidence

## Rules

- Prefer `entry-point-analyzer` before scanner fan-out when the entry surface is still unclear.
- Prefer `secure-workflow-guide`, `token-integration-analyzer`, and `spec-to-code-compliance` as specialist support, not as a replacement for this orchestrated audit.
- If `prep/web3-readiness.md` says replay is `static-only`, say so explicitly and avoid pretending a fork test happened.
- Do not report hypothetical accounting exploits without showing the broken invariant and the attacker-controlled variables that break it.
- Taxonomy-backed output is mandatory. Every finding should map to `U-*`, `A-*`, `I-*`, or `O-*` from `references/vulnerability-taxonomy.md`.
