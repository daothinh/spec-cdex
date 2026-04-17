# Phase 01: Foundation and Inventory

## Context Links

- [Root README](../../README.md)
- [Claude marketplace](../../.claude-plugin/marketplace.json)
- [Codex marketplace](../../.agents/plugins/marketplace.json)
- [Source plugin tree](../../skills/plugins/)
- [Overview plan](./plan.md)

## Overview

Priority: P1

Status: Completed

Purpose: record the implemented root-only porting foundation: shared inventory, sync script, and validator.

Current state:

- `plugins/catalog.json` exists and covers all 45 root plugins: 7 root-native plugins and 38 copied source plugins.
- `scripts/sync-root-plugins.mjs` and `scripts/validate-root-plugins.mjs` exist in the root repo.
- Validator currently passes for all 45 root plugins, with 45 Claude marketplace entries and 36 Codex marketplace entries.

## Key Insights

- Root repo is already the shipped marketplace surface. The missing piece is scale, not pattern discovery.
- A 45-plugin root surface will drift if manifests are hand-maintained.
- The root port must be idempotent and must never write back into `skills/`.

## Requirements

- Functional:
  - Create a root inventory for every source plugin.
  - Create a sync workflow that copies source plugin content into root `plugins/`.
  - Create a validator for manifest parity and path integrity.
- Non-functional:
  - No write operations under `E:\MyProject\spec-codex\skills\`.
  - Re-running the sync must be safe.
  - Validation output must clearly identify missing references and marketplace drift.

## Architecture

- Inventory:
  - `E:\MyProject\spec-codex\plugins\catalog.json`
- Sync:
  - `E:\MyProject\spec-codex\scripts\sync-root-plugins.mjs`
- Validation:
  - `E:\MyProject\spec-codex\scripts\validate-root-plugins.mjs`
- Marketplace outputs:
  - `E:\MyProject\spec-codex\.claude-plugin\marketplace.json`
  - `E:\MyProject\spec-codex\.agents\plugins\marketplace.json`

## Related Code Files

- Create: `E:\MyProject\spec-codex\plugins\catalog.json` — root plugin metadata inventory
- Create: `E:\MyProject\spec-codex\scripts\sync-root-plugins.mjs` — copies source plugin trees into root `plugins/`
- Create: `E:\MyProject\spec-codex\scripts\validate-root-plugins.mjs` — parity and reference validator
- Modify: `E:\MyProject\spec-codex\.claude-plugin\marketplace.json` — generated or validated from catalog
- Modify: `E:\MyProject\spec-codex\.agents\plugins\marketplace.json` — generated or validated from catalog

## Implementation Steps

1. Inventory the 38 source plugins and write one record per plugin into `plugins/catalog.json`.
2. Define per-plugin metadata fields required by both marketplaces and both manifest types.
3. Implement `sync-root-plugins.mjs` to copy source plugin trees into root `plugins/<name>/` without touching `skills/`.
4. Add manifest rendering to the sync step or a dedicated generator step.
5. Implement `validate-root-plugins.mjs` to catch missing files, missing manifests, and marketplace drift.
6. Test the pipeline on one existing Codex-ready root plugin and one new low-risk plugin before batch work starts.

## Todo List

- [x] Create root inventory schema
- [x] Add inventory entries for all 38 source plugins
- [x] Build sync script
- [x] Build validator
- [x] Dry-run the workflow on a single new plugin
- [x] Document the workflow in the root README or contributor docs

## Success Criteria

- `plugins/catalog.json` exists and covers all source plugins.
- Sync copies one plugin end-to-end into root `plugins/<name>/`.
- Validator catches broken relative references and missing manifest fields.
- No generated step modifies files inside `skills/`.

## Risk Assessment

- Risk: inventory fields become too sparse and force later manual edits.
  - Mitigation: include category, prompts, status, and metadata from day 1.
- Risk: copy logic breaks hidden files like `.mcp.json`.
  - Mitigation: explicitly support dotfiles and deep trees.

## Security Considerations

- Do not auto-execute copied scripts during sync.
- Treat source plugin content as data until the validator passes.
- Preserve licenses and repository metadata verbatim across root manifests.

## Next Steps

- Phase 01 is complete. Remaining work is release validation depth, not missing foundation tooling.
