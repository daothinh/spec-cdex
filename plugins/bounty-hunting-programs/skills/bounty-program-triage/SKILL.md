---
name: bounty-program-triage
description: >
  Standard intake and routing workflow for bug bounty targets. Use when you need
  to read program rules, fingerprint a target, map trust boundaries, and choose
  the correct bounty lane or mixed-surface sequence for web/API, Android, smart
  contract, native, or agentic workflow review.
---

# Bounty Program Triage

Use this skill before starting a new bug bounty engagement when the target type is not yet normalized.

Load these references on demand:
- `../../references/bounty-standard.md` for the shared lifecycle
- `../../references/codex-ready-building-blocks.md` for reusable Codex-ready plugins
- `../../references/report-checklist.md` before closing a finding
- `../../references/web-framework-matrix.md`, `../../references/android-framework-matrix.md`, `../../references/smart-contract-matrix.md`, or `../../references/native-language-matrix.md` after the stack is clear

## Inputs To Collect

- Program rules or safe-harbor language
- Known target assets and auth model
- Whether source code, APKs, deployed addresses, or binaries are available
- Whether testing must stay non-destructive or on test environments only
- Whether the target is hybrid: web/API plus contracts, wallet plus backend, or exchange plus blockchain
- Whether `audit-targets/<slug>/scope/target.json` already exists from `bounty-target-bootstrap`

## Routing Workflow

1. Read the rules first. Write down anything explicitly out of scope.
2. If the user gives only a program URL or scope page, run `bounty-target-bootstrap` first so the target surface is persisted before deeper review.
3. Fingerprint the target from files, manifests, build configs, package names, protocol artifacts, and any existing `scope/target.json`.
4. Build a surface inventory before choosing a lane:
   - executable lanes: web/API, Android, smart contract, native
   - context surfaces that still matter even without a dedicated lane: wallet, blockchain, exchange, admin panels, browser extensions
5. Choose the primary lane and note any follow-on lanes:
   - Web or API source, routes, controllers, templates, job workers: use `bounty-program-web`
   - APK, `AndroidManifest.xml`, dex files, mobile traffic, rooted-device testing: use `bounty-program-mobile-android`
   - Contracts, chain configs, on-chain entry points, token logic: use `bounty-program-smart-contracts`
   - Parsers, binaries, crypto libraries, protocol handlers, CLI tools: use `bounty-program-native`
   - If multiple executable lanes are genuinely in play, keep `bounty-program-triage` active and route the first deep pass to the highest-value lane instead of pretending the target is single-surface
6. Always map trust boundaries before exploit reasoning:
   - external input
   - privileged roles
   - background execution
   - storage and secret boundaries
   - off-chain vs on-chain control plane
   - wallet or browser-extension origin trust
   - exchange custody, settlement, and signer boundaries
7. Run baseline building blocks when relevant:
   - `audit-context-building` for unfamiliar architectures
   - `supply-chain-risk-auditor` for risky dependency surface
   - `sharp-edges` and `insecure-defaults` for language/framework anti-patterns
   - `agentic-actions-auditor` if CI, GitHub Actions, or AI-agent workflows are in scope
8. If the first confirmed issue exposes a repeatable pattern, expand with `variant-analysis`.

## Output

Before switching to a deeper lane, produce:

- the primary lane
- any follow-on lanes that should stay in scope after the first deep pass
- the primary technology signals that justified the choice
- the surface inventory, including wallet, blockchain, and exchange context when present
- the top trust boundaries to test first
- the first three bug classes to prioritize

## Rules

- Do not start with a generic code review when the target class can be identified quickly.
- Do not use blocked Codex plugins as the mandatory path.
- Keep the first pass focused on scoping and routing, not writing exploit fan fiction.
- Do not collapse wallet, blockchain, and exchange context into a generic "web target" note.
- Do not force a hybrid Web3 target into one lane when the architecture clearly spans multiple trust boundaries.
