---
name: bounty-program-native
description: >
  Standard bug bounty workflow for native code, parsers, binaries, Rust crates,
  crypto-heavy components, and protocol handlers. Use when the target's primary
  risk comes from memory safety, parser confusion, FFI boundaries, or timing
  side channels.
---

# Bounty Program Native

Use this workflow for C, C++, Rust, Go, parser-heavy code, helper binaries, and crypto-sensitive implementations.

Load these references on demand:
- `../../references/bounty-standard.md`
- `../../references/codex-ready-building-blocks.md`
- `../../references/native-language-matrix.md`
- `../../references/report-checklist.md`

## Inputs

- Build instructions or reproducible test command
- Parser or protocol inputs
- Crash artifacts, corpora, or sample files if they exist
- Any known security boundaries such as privilege level, secret handling, or trusted helpers

## Workflow

1. Decide whether the target is truly native-first. If the main attack surface is HTTP, switch to `bounty-program-web`.
2. Read the matching lane in `native-language-matrix.md`.
3. Map the main surfaces:
   - parsers and decoders
   - file, archive, or network protocol boundaries
   - privilege transitions
   - unsafe blocks or FFI crossings
   - crypto or secret-dependent logic
4. Reuse Codex-ready building blocks when installed:
   - `fuzzer` for parser and coverage-guided exploration
   - `constant-time-analysis` for crypto and secret-dependent control flow
   - `dwarf-expert` for binary-only or DWARF-assisted inspection
   - `dimensional-analysis` for arithmetic and unit consistency
   - `kani-proof` for Rust invariants and panic freedom
   - `supply-chain-risk-auditor` for risky third-party code
5. Prioritize bug classes in this order:
   - memory corruption and unsafe parsing
   - integer, length, and unit mismatches
   - unsafe FFI and ABI assumptions
   - temporary file, path, or environment trust failures
   - timing side channels in crypto or auth code
   - privilege-boundary failures in helper binaries or CLIs
6. After a crash or invariant break, minimize the reproducer and expand with `variant-analysis`.

## Rules

- Prefer one minimized reproducer over a long story.
- Distinguish code-execution risk from mere crashability.
- When the issue depends on secret-dependent timing, say exactly what branch or instruction pattern leaks.
- Compare every candidate against `scope/target.json`, `scope/in-scope.md`, `scope/rules.md`, and `prep/severity-conditions.md` before assigning severity.
- Low-only findings do not end the hunt. Keep going until a `medium+` finding exists or an exact blocker is recorded.
