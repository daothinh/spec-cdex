# Codex-Ready Building Blocks

These playbooks are composed from plugins that are already exposed in the Codex marketplace from this repo.

| Plugin | Use For |
| --- | --- |
| `audit-context-building` | Deep architecture and trust-boundary comprehension before bug hunting |
| `agentic-actions-auditor` | GitHub Actions, CI, and AI-agent workflow abuse paths |
| `building-secure-contracts` | Platform-specific smart contract scanners and secure workflow guides |
| `burpsuite-project-parser` | Reusing `.burp` project evidence instead of re-collecting traffic |
| `constant-time-analysis` | Timing side-channel analysis in crypto-heavy code |
| `dimensional-analysis` | Arithmetic, unit, and state-transition consistency issues |
| `dwarf-expert` | Binary and DWARF-assisted native analysis |
| `entry-point-analyzer` | State-changing smart contract entry points and privileged flows |
| `evm-protocol-audit` | Structured EVM, Solidity, and Vyper protocol audits |
| `firebase-apk-scanner` | Firebase exposure and APK secret/config discovery |
| `fuzzer` | Coverage-guided fuzzing for C/C++, Rust, and Go |
| `insecure-defaults` | Risky framework and deployment defaults |
| `kani-proof` | Rust and Solana proof harnesses for critical invariants |
| `mutation-testing` | Sanity-check whether tests actually detect security regressions |
| `property-based-testing` | Express invariants on stateful or parser-heavy targets |
| `semgrep-rule-creator` | Turn a confirmed issue into a reusable rule |
| `semgrep-rule-variant-creator` | Generate variants of an existing Semgrep rule |
| `sharp-edges` | High-risk language/framework patterns and dangerous APIs |
| `solana-audit` | Structured Solana/Anchor audit workflow |
| `supply-chain-risk-auditor` | Dependency-maintainer and ecosystem risk scoping |
| `variant-analysis` | Find siblings of a confirmed vulnerability pattern |
| `workers-app-tester` | Rooted-device Android dynamic analysis |

## Non-Goals

- Do not require blocked plugins as the main path.
- If a blocked plugin becomes Codex-ready later, treat it as an optional extension until its workflow is fully portable.
