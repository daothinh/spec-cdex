---
name: bounty-program-smart-contracts
description: >
  Standard bug bounty workflow for smart contracts across EVM, Vyper, Solana,
  CosmWasm, Cairo, Substrate, TON, and Algorand targets. Use when auditing
  privileged entry points, token logic, upgrade paths, or protocol invariants.
---

# Bounty Program Smart Contracts

Use this workflow when the target is primarily on-chain and the main risks are state transitions, privileged entry points, callbacks, accounting, or upgrade logic.

Load these references on demand:
- `../../references/bounty-standard.md`
- `../../references/codex-ready-building-blocks.md`
- `../../references/smart-contract-matrix.md`
- `../../references/report-checklist.md`

## Inputs

- Chain or VM family
- Deployed addresses or testnet references if available
- Protocol archetype if already known: token, AMM, vault, lending, staking, bridge, governance, orderbook, perps, marketplace, oracle consumer
- Privileged roles, upgrade model, and token integrations
- Off-chain dependencies such as keepers, relayers, signers, oracles, sequencers, or settlement backends
- Any protocol-specific assumptions about pricing, minting, or settlement
- Whitepaper, docs, audits, or design notes when available

## Workflow

1. Identify the platform using `smart-contract-matrix.md`.
2. Classify the protocol archetype before deep review. Use the protocol-archetype table in `smart-contract-matrix.md` and write down:
   - assets at risk
   - critical state transitions
   - protocol-specific invariants
   - protocol-specific external dependencies
3. Map state-changing entry points and privileged operations first:
   - use `entry-point-analyzer` when installed
   - write down every role-protected, public, or callback-style function
4. Map fund and control flow, not just functions:
   - who can change balances, debt, shares, collateral, voting power, or settlement state
   - which contracts or accounts custody value
   - which callbacks, hooks, CPI paths, or delegate patterns can break trust
5. Record non-contract trust edges that materially affect exploitability:
   - price feeds and oracle update paths
   - relayers, signers, keepers, harvesters, sequencers, settlement workers
   - frontend or backend gates that may hide but not remove a vulnerable state transition
   - If those dependencies are critical, keep `bounty-program-triage` active in parallel instead of pretending the issue is purely on-chain
6. Choose the platform lane:
   - Solana or Anchor: prefer `solana-audit`, then strengthen invariants with `kani-proof` where needed
   - Solidity or Vyper: prefer `evm-protocol-audit` for the first deep pass, then use `building-secure-contracts` skills such as `secure-workflow-guide`, `guidelines-advisor`, and `token-integration-analyzer` as specialist follow-ons
   - Cosmos, Cairo, Substrate, TON, or Algorand: use the corresponding `building-secure-contracts` scanner first
7. Prioritize universal bug classes in this order:
   - access control and signer or owner validation
   - replay, initialization, and upgrade mistakes
   - accounting, rounding, and precision loss
   - callback, CPI, or reentrancy-style trust breaks
   - token integration edge cases and weird-token assumptions
   - oracle, pricing, and slippage invariants
8. Overlay protocol-archetype priorities from `smart-contract-matrix.md` so the first deep pass matches the system you actually have.
9. Strengthen high-value claims with:
   - `property-based-testing` for protocol invariants
   - `dimensional-analysis` for share, price, debt, collateral, and settlement arithmetic
   - `mutation-testing` to see whether tests would have caught the issue
   - `kani-proof` for Rust or Solana invariants that need machine-checked confidence
   - `spec-to-code-compliance` when docs, whitepapers, or audits define intended behavior
   - `trailmark` when you need static call paths, blast radius, or taint-guided audit prioritization
10. Use `variant-analysis` after the first confirmed `medium+` root cause, not before.

## Web3 Bootstrap Expectations

When `audit-targets/<slug>/` came from the upgraded bootstrap flow, consume these before the first deep pass:

- `scope/chain-inventory.json`
- `scope/protocol-archetype.md`
- `scope/proxy-topology.md`
- `scope/dependency-boundaries.md`
- `prep/attack-surface-map.md`
- `prep/protocol-invariants.md`
- `prep/web3-readiness.md`
- `prep/severity-conditions.md`

For EVM targets, do not skip the tool-readiness check. If replay is only `static-only`, say so and adjust claim confidence instead of pretending fork validation happened.

## Output

Before going deep, produce:

- platform lane
- protocol archetype
- assets at risk
- top invariants to preserve
- privileged and callback-style entry points
- non-contract trust dependencies that still matter to exploitability
- first three high-value attack paths

## Rules

- Treat entry-point mapping as mandatory, not optional.
- Treat protocol classification as mandatory, not optional.
- Do not conflate read-only helper functions with exploit surface.
- Keep findings tied to a concrete state transition or privileged action.
- Do not treat off-chain oracle, relayer, keeper, or settlement assumptions as "out of band" if exploitability depends on them.
- Compare every candidate against scope and `prep/severity-conditions.md` before assigning severity.
- Low-only findings do not end the hunt. Keep going until a `medium+` finding exists or an exact blocker is recorded.
