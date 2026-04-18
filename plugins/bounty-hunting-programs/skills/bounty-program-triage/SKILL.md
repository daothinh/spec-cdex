---
name: bounty-program-triage
description: >
  Standard intake and routing workflow for bug bounty targets. Use when you need
  to read program rules, fingerprint a target, map trust boundaries, and choose
  the correct bounty lane for web/API, Android, smart contract, native, or
  agentic workflow review.
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

## Routing Workflow

1. Read the rules first. Write down anything explicitly out of scope.
2. Fingerprint the target from files, manifests, build configs, package names, or protocol artifacts.
3. Choose the primary lane:
   - Web or API source, routes, controllers, templates, job workers: use `bounty-program-web`
   - APK, `AndroidManifest.xml`, dex files, mobile traffic, rooted-device testing: use `bounty-program-mobile-android`
   - Contracts, chain configs, on-chain entry points, token logic: use `bounty-program-smart-contracts`
   - Parsers, binaries, crypto libraries, protocol handlers, CLI tools: use `bounty-program-native`
4. Always map trust boundaries before exploit reasoning:
   - external input
   - privileged roles
   - background execution
   - storage and secret boundaries
5. Run baseline building blocks when relevant:
   - `audit-context-building` for unfamiliar architectures
   - `supply-chain-risk-auditor` for risky dependency surface
   - `sharp-edges` and `insecure-defaults` for language/framework anti-patterns
   - `agentic-actions-auditor` if CI, GitHub Actions, or AI-agent workflows are in scope
6. If the first confirmed issue exposes a repeatable pattern, expand with `variant-analysis`.

## Output

Before switching to a deeper lane, produce:

- the chosen lane
- the primary technology signals that justified the choice
- the top trust boundaries to test first
- the first three bug classes to prioritize

## Rules

- Do not start with a generic code review when the target class can be identified quickly.
- Do not use blocked Codex plugins as the mandatory path.
- Keep the first pass focused on scoping and routing, not writing exploit fan fiction.
