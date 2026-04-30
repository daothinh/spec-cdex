---
name: bounty-target-bootstrap
description: >
  Bootstrap a bounty target from a program URL. Use Playwright MCP to capture
  host-provided scope, save target metadata in-repo, pull source or binary
  artifacts, preserve smart-contract references, and prep the next bounty
  playbook.
metadata:
  author: workers.io
  version: "0.2.0"
---

# Bounty Target Bootstrap

Bootstrap a target from a program page when intake must finish before deeper auditing.

This is an intake-only phase. The job is to collect and normalize everything the host explicitly exposes for later whitebox or audit work. Do not invent new assets, and do not start exploit work from this skill.

Load these on demand:
- [references/playwright-intake.md](references/playwright-intake.md) for the Playwright MCP flow
- [references/workspace-contract.md](references/workspace-contract.md) for the input JSON and generated layout
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` after whitebox source lands locally
- `plugins/bounty-hunting-programs/skills/bounty-program-mobile-android/SKILL.md` for Android follow-on work
- `plugins/bounty-hunting-programs/skills/bounty-program-smart-contracts/SKILL.md` when the host provides deployed contracts or on-chain source references

## Inputs To Capture

- program name and program URL
- target type: `whitebox`, `android`, or `smart-contract`
- focus areas such as `Wallet`, `Smart Contract`, `Blockchain`, and `Exchange`
- scope summary, full in-scope list, full out-of-scope list, and rules
- safe-harbor notes, submission notes, auth notes, and environment limits
- source repo URLs, source-code URLs, APK or archive URLs, package names, app or store URLs
- web URLs, API URLs, RPC URLs, WebSocket URLs, docs URLs, explorer URLs, API spec URLs, audit report URLs, registry URLs
- keeper URLs, relayer URLs, signer service URLs, oracle URLs, and whitepaper or spec URLs when the target is web3-heavy
- smart-contract metadata: chain, chain ID, network, VM, address, proxy, implementation, explorer, ABI URL, source URL, repo URL, notes
- raw scope notes copied from the rendered page

## Workflow

1. Use Playwright MCP, not plain HTTP, so rendered scope tables and collapsed sections are visible.
2. Navigate to the URL, expand scope and rule accordions, and capture only assets explicitly marked in scope for `whitebox`, `android`, or `smart-contract`.
3. Ignore unsupported assets. If the page exposes no in-scope target for those lanes, write the unsupported note and stop.
4. Normalize findings into a JSON file matching `references/workspace-contract.md`.
5. Run:
   `python plugins/bounty-target-bootstrap/skills/bounty-target-bootstrap/scripts/bootstrap_target.py --input <json> --repo-root .`
6. Review `audit-targets/<slug>/scope/target.json`, `scope/target-surface.md`, `scope/smart-contracts.md`, `prep/bootstrap-summary.md`, `prep/context-pack/`, and `prep/ready-for-bounty.md`.
7. For web3-heavy targets, ensure the generated handoff also includes `scope/chain-inventory.json`, `scope/protocol-archetype.md`, `scope/proxy-topology.md`, `scope/dependency-boundaries.md`, `prep/attack-surface-map.md`, `prep/protocol-invariants.md`, and `prep/web3-readiness.md`.
8. When the target keeps a web/API lane alive, ensure bootstrap also emits `prep/kage-plan.md`, `prep/caido-plan.md`, and `prep/context-pack/web-handoff.md`.
9. Stop after intake and handoff. Do not continue into the next lane from this skill; the hunting pipeline owns that step.
10. Preserve the generated handoff files even when no finding exists yet:
   - `prep/asset-inventory.md`
   - `prep/tried-and-ruled-out.md`
   - `prep/finding-pipeline.md`
   - `prep/bootstrap-summary.md`
   - `prep/kage-plan.md` when web/API breadth testing stays in scope
   - `prep/caido-plan.md` when authenticated replay is likely useful
   - `prep/attack-surface-map.md`
   - `prep/protocol-invariants.md`
   - `prep/web3-readiness.md`
   - `prep/context-pack/`
   - `findings/README.md`

## Playwright Extraction Rules

- Prefer `browser_snapshot` after each expand or click cycle.
- Save decisive scope text into `raw_scope_notes`; do not rely on memory.
- Persist `in_scope`, `out_of_scope`, and `rules` as separate lists, not one merged blob.
- Capture absolute URLs for repos, source mirrors, APKs, archives, docs, explorers, ABI files, and login portals.
- Capture absolute URLs for keepers, relayers, signer services, oracle endpoints, and whitepapers when the host exposes them.
- Record qualifiers exactly: production or staging, test accounts, rate limits, and forbidden actions.
- Keep every repo URL. Let the bootstrap script fingerprint them before choosing the lane.
- Preserve every host-provided pointer even when it is not directly downloadable: explorers, docs, audit PDFs, RPC endpoints, WebSocket endpoints, app stores, package registries.
- Treat wallet, blockchain, and exchange context as focus metadata. Persist it even when the executable lane is still `whitebox` or `android`.
- When the target is hybrid, capture enough evidence to keep multiple lanes alive later instead of flattening the scope into one guessed path.

## Output Rules

- Keep generated artifacts inside `audit-targets/<slug>/`.
- Preserve both raw notes and normalized JSON.
- Write dedicated files for `in-scope`, `out-of-scope`, `rules`, and program notes.
- Write dedicated files for the host-provided target surface and smart-contract inventory.
- Write `prep/kage-plan.md` for breadth-first web/API follow-up when a web lane exists.
- Write `prep/caido-plan.md` for authenticated replay-heavy web/API follow-up when a web lane exists.
- For web3-heavy targets, write dedicated files for chain inventory, proxy topology, dependency boundaries, attack-surface mapping, protocol invariants, and readiness.
- Write a reusable handoff state bundle for asset inventory, tried paths, finding lifecycle state, and the per-finding evidence contract.
- Write `prep/bootstrap-summary.md` so the hunting pipeline can resume without reconstructing trust boundaries, lane choice, or next best attack path.
- Write `prep/context-pack/` with bootstrap-friendly summaries or pointers for the baseline context.
- Clone source repos when a git URL exists.
- Download APK or source archives when direct URLs exist and are explicitly in scope.
- Download ABI, API spec, or audit-report artifacts when the host exposes direct file URLs.
- Surface the suggested bounty lane from `ready-for-bounty.md` before starting deeper review.

## Rules

- Do not invent or enrich target data beyond what the host exposes on the program page.
- Do not collapse wallet, blockchain, exchange, and smart-contract context into one generic note. Persist them in structured fields when available.
- Do not flatten hybrid web3 targets into one lane if the scope clearly spans contracts, web, wallets, exchanges, or off-chain operators.
- Do not invent scope. If a field is absent, leave it empty and note the gap in `raw_scope_notes`.
- Do not start exploit attempts from the scope page. Finish intake first.
