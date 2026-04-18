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
- Privileged roles, upgrade model, and token integrations
- Any protocol-specific assumptions about pricing, minting, or settlement

## Workflow

1. Identify the platform using `smart-contract-matrix.md`.
2. Map state-changing entry points and privileged operations first:
   - use `entry-point-analyzer` when installed
   - write down every role-protected, public, or callback-style function
3. Choose the platform lane:
   - Solana or Anchor: prefer `solana-audit`, then strengthen invariants with `kani-proof` where needed
   - Solidity or Vyper: prefer `building-secure-contracts` skills such as `secure-workflow-guide`, `guidelines-advisor`, and `token-integration-analyzer`
   - Cosmos, Cairo, Substrate, TON, or Algorand: use the corresponding `building-secure-contracts` scanner first
4. Prioritize bug classes in this order:
   - access control and signer or owner validation
   - replay, initialization, and upgrade mistakes
   - accounting, rounding, and precision loss
   - callback, CPI, or reentrancy-style trust breaks
   - token integration edge cases and weird-token assumptions
   - oracle, pricing, and slippage invariants
5. Strengthen high-value claims with:
   - `property-based-testing` for protocol invariants
   - `mutation-testing` to see whether tests would have caught the issue
   - `kani-proof` for Rust or Solana invariants that need machine-checked confidence
6. Use `variant-analysis` after the first confirmed root cause, not before.

## Rules

- Treat entry-point mapping as mandatory, not optional.
- Do not conflate read-only helper functions with exploit surface.
- Keep findings tied to a concrete state transition or privileged action.
