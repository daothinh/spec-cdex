---
title: "Claude-to-Codex Root Port Plan"
description: "Track the root-side port of 38 Claude-source plugins plus 7 original root plugins, with 45 Claude entries, 36 Codex entries, and 9 blocked high-risk plugins."
status: in-progress
priority: P1
effort: 12-16d
issue: null
branch: main
tags: [feature, docs, infra, experimental]
created: 2026-04-17
---

# Claude-to-Codex Root Port Plan

## Overview

Goal: keep every Claude-source plugin under `E:\MyProject\spec-codex\skills\plugins\` mirrored into repo-root `E:\MyProject\spec-codex\plugins\` so the root repo remains the installable Codex surface.

Hard constraints:
- Do not modify anything under `E:\MyProject\spec-codex\skills\`.
- Keep Claude and Codex manifests aligned in the root repo.
- Do not expose a plugin in the Codex marketplace until its workflow is actually Codex-compatible.

Non-goals:
- Rewriting the upstream skills repo.
- Forcing feature parity in one giant batch.
- Shipping hook-dependent Claude workflows into Codex without a root-side replacement.

## Current State

- Root repo now has 45 plugin directories under `plugins/`: the original 7 Codex-ready plugins plus all 38 source plugins copied from `skills/plugins/`.
- `plugins/catalog.json`, `scripts/sync-root-plugins.mjs`, and `scripts/validate-root-plugins.mjs` are implemented in the root repo.
- Marketplace counts are now:
  - Claude marketplace: 45 entries
  - Codex marketplace: 36 entries
- Validator status:
  - `scripts/validate-root-plugins.mjs` passes across all 45 root plugins
- Remaining gap:
  - dedicated smoke installs and representative invocation checks are still a residual release risk
- Current publish split from the root inventory:

| Tier | Count | Meaning |
|---|---:|---|
| T1 | 17 | Copied into root `plugins/` and published in both marketplaces. |
| T2 | 12 | Copied into root `plugins/` and published in both marketplaces. |
| T3 | 9 | Copied into root `plugins/`, kept staged in inventory, and blocked from the Codex marketplace pending Codex-compatible workflow work. |

### T1 Low-Risk Plugins

`agentic-actions-auditor`, `ask-questions-if-underspecified`, `claude-in-chrome-troubleshooting`, `culture-index`, `debug-buttercup`, `devcontainer-setup`, `dimensional-analysis`, `dwarf-expert`, `insecure-defaults`, `let-fate-decide`, `mutation-testing`, `property-based-testing`, `seatbelt-sandboxer`, `semgrep-rule-variant-creator`, `sharp-edges`, `supply-chain-risk-auditor`, `yara-authoring`

### T2 Medium-Risk Plugins

`audit-context-building`, `building-secure-contracts`, `burpsuite-project-parser`, `constant-time-analysis`, `differential-review`, `entry-point-analyzer`, `firebase-apk-scanner`, `semgrep-rule-creator`, `spec-to-code-compliance`, `testing-handbook-skills`, `trailmark`, `variant-analysis`

### T3 High-Risk Plugins

`fp-check`, `gh-cli`, `git-cleanup`, `modern-python`, `second-opinion`, `skill-improver`, `static-analysis`, `workflow-skill-design`, `zeroize-audit`

## Port Strategy

1. Root repo is the integration layer.
   - Copy or sync source plugin content from `skills/plugins/<name>/` into `plugins/<name>/`.
   - Keep all Codex-specific rewrites in the root copy only.

2. Every root plugin gets dual manifests.
   - Add `plugins/<name>/.claude-plugin/plugin.json`.
   - Add `plugins/<name>/.codex-plugin/plugin.json`.
   - Keep identity, version, repository, and license aligned between both.

3. Marketplace exposure is staged.
   - A root plugin may exist before it is listed in `E:\MyProject\spec-codex\.agents\plugins\marketplace.json`.
   - Only Codex-validated plugins go into the Codex marketplace.
   - Claude marketplace and Codex marketplace are updated from the same root inventory to avoid drift.

4. Prefer metadata-only ports first.
   - T1 and most T2 plugins should ship with copied content plus generated manifests.
   - T3 gets root-only workflow rewrites where required.

5. Introduce automation before batch porting.
   - Manual edits across 45 root plugins and 2 marketplace catalogs will drift.
   - Add a root-side inventory plus generator/validator before bulk porting.

## Architecture

### Root-Side Source of Truth

Create one inventory file in the root repo, for example:

- `E:\MyProject\spec-codex\plugins\catalog.json`

Each record should contain:
- `name`
- `sourcePluginPath`
- `displayName`
- `description`
- `category`
- `version`
- `license`
- `repository`
- `defaultPrompts`
- `codexStatus` (`staged`, `available`, `blocked`)
- `notes`

### Root-Side Automation

Create two root-only scripts:

- `E:\MyProject\spec-codex\scripts\sync-root-plugins.mjs`
  - Copies plugin content from `skills/plugins/<name>/` to `plugins/<name>/`
  - Preserves relative paths used by `SKILL.md`, references, agents, commands, hooks, templates, scripts
  - Refuses to write under `skills/`

- `E:\MyProject\spec-codex\scripts\validate-root-plugins.mjs`
  - Verifies dual manifest parity
  - Verifies `skills` path exists in each root plugin
  - Verifies every marketplace entry resolves to an existing root plugin
  - Verifies every relative file reference used by `SKILL.md` exists after port

### Codex Adaptation Rules

- Replace Claude `TaskCreate`/`TaskUpdate`/`TaskList` orchestration with Codex-friendly plan tracking or inline workflow steps in the root copy.
- Replace `AskUserQuestion` requirements with plain user questions and safe defaults when possible.
- Replace “spawn task agents” language with “use subagents when allowed; otherwise execute inline”, matching the existing root Codex-ready style.
- Treat Claude hooks and bundled MCP as blockers until confirmed workable in the root Codex flow.

## Phases

| # | Phase | Status | Effort | Link |
|---|---|---|---|---|
| 1 | Foundation and Inventory | Completed | 2d | [phase-01](./phase-01-foundation-and-inventory.md) |
| 2 | Port T1 Low-Risk Plugins | Completed | 3d | [phase-02](./phase-02-port-low-risk-plugins.md) |
| 3 | Port T2 Medium-Risk Plugins | Completed | 3d | [phase-03](./phase-03-port-medium-risk-plugins.md) |
| 4 | Adapt T3 High-Risk Plugins | In Progress | 3-5d | [phase-04](./phase-04-adapt-high-risk-plugins.md) |
| 5 | Validate and Release | In Progress | 1-3d | [phase-05-validate-and-release.md](./phase-05-validate-and-release.md) |

## Key Decisions

- Do not use the `skills/` tree as the shipped marketplace path. Root `plugins/` remains the installable surface.
- Do not rely on manual dual-manifest editing once the port starts. Generate or validate both from one inventory.
- Do not ship hook-dependent plugins into Codex just because the content copies cleanly.
- Keep T3 blockers visible in root status docs even if they are not yet market-listed.

## Open Risks

- Dedicated install/invocation smoke tests have not been completed yet, so the validator is the primary confidence signal rather than end-to-end install coverage.
- Codex runtime support for bundled MCP assets and Claude-style plugin hooks may not match the source plugins.
- Some T3 plugins use hard enforcement via stop hooks. Root-only prompt rewrites may reduce enforcement strength.
- Multi-skill plugins need consistent categorization and prompt design, or marketplace UX will be noisy.
- T3 plugins are intentionally staged in root `plugins/` but still blocked in the Codex marketplace until their runtime assumptions are ported or replaced.

## Success Criteria

- There is a root `plugins/<name>/` directory for all 45 current plugins, including all 38 Claude-source ports.
- Every root plugin has both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`.
- `E:\MyProject\spec-codex\.claude-plugin\marketplace.json` and `E:\MyProject\spec-codex\.agents\plugins\marketplace.json` are generated or validated from a shared root inventory.
- All 29 T1/T2 Claude-source ports plus the original 7 root plugins are installable from the Codex marketplace (36 total).
- The 9 T3 high-risk plugins are explicitly staged and withheld from the Codex marketplace until Codex-safe workflow ports exist.
- `README.md` documents the support matrix and staging status.
