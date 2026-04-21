# Bounty Hunting Programs

Standardized bug bounty workflows for Codex across four target classes:

- Web and API applications
- Android applications
- Smart contracts
- Native code and parser-heavy systems

This plugin is designed for the root-ported marketplace in this repository. It does not depend on blocked Codex plugins. When companion plugins are installed, the workflows explicitly reuse them; otherwise the playbooks still remain usable as manual checklists.

## Included Skills

- `/bounty-program-triage` — normalize program rules, fingerprint the target, and route to the correct lane or mixed-surface sequence
- `/bounty-program-web` — web/API workflow across common server frameworks
- `/bounty-program-mobile-android` — Android pentest workflow for APKs and rooted-device testing
- `/bounty-program-smart-contracts` — chain-specific workflow for EVM, Solana, Cosmos, Cairo, Substrate, TON, and Algorand
- `/bounty-program-native` — workflow for C/C++, Rust, Go, crypto, parsers, and binaries

## Reused Building Blocks

The playbooks are intentionally composed from Codex-ready plugins already present in this repo:

- `audit-context-building`
- `agentic-actions-auditor`
- `building-secure-contracts`
- `burpsuite-project-parser`
- `constant-time-analysis`
- `dimensional-analysis`
- `dwarf-expert`
- `entry-point-analyzer`
- `firebase-apk-scanner`
- `fuzzer`
- `insecure-defaults`
- `kani-proof`
- `mutation-testing`
- `property-based-testing`
- `semgrep-rule-creator`
- `semgrep-rule-variant-creator`
- `sharp-edges`
- `solana-audit`
- `supply-chain-risk-auditor`
- `variant-analysis`
- `workers-app-tester`

## Standard Workflow Model

Every playbook follows the same reportable sequence:

1. Read program rules, scope, and safe-harbor constraints.
2. Fingerprint the target stack and trust boundaries.
3. Map attack surface before testing or exploit reasoning.
4. Use the most specific Codex-ready building blocks available for that target.
5. Reproduce the issue with the least-destructive evidence that still proves impact.
6. Expand to variants only after the first issue is understood.
7. Package evidence using the shared reporting checklist.

The routing layer now keeps hybrid Web3 targets honest:

- wallet, blockchain, and exchange context stay visible during triage
- smart-contract review now classifies protocol archetypes before deep review
- hybrid targets can keep follow-on lanes in scope instead of forcing a fake single-lane answer

## Recommended Install Set

For the best experience, install this plugin alongside the security plugins already exposed in the `workersio` marketplace. The playbooks stay useful without them, but companion plugins let Codex jump directly into specialized workflows instead of treating the playbook as a pure checklist.
