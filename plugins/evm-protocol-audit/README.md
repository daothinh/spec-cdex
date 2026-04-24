# evm-protocol-audit

Structured EVM and DeFi security audits for Solidity and Vyper targets.

## Included

| Path | Purpose |
|------|---------|
| `skills/evm-protocol-audit/SKILL.md` | Main orchestrated EVM audit workflow |
| `skills/evm-protocol-audit/references/CHEATSHEET.md` | Fast taxonomy and first-pass prompts |
| `skills/evm-protocol-audit/references/scoring.md` | Confidence and false-positive rules |
| `skills/evm-protocol-audit/references/vulnerability-taxonomy.md` | Structured finding IDs for auth, accounting, integration, and oracle bug families |
| `skills/evm-protocol-audit/references/protocol-archetypes.md` | Archetype selection guide |
| `skills/evm-protocol-audit/references/protocols/*.md` | Protocol-specific invariant and attack-surface packs |
| `skills/evm-protocol-audit/references/agents/*.md` | Explorer and scanner prompt contracts |

## Purpose

This plugin exists so EVM targets stop falling back to generic checklists.

Use it when the target is:

- Solidity or Vyper
- Foundry, Hardhat, or Truffle based
- proxy-heavy or upgradeable
- a DeFi or exchange-like protocol with real accounting, oracle, integration, or governance risk
