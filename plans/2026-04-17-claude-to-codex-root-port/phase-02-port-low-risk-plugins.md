# Phase 02: Port T1 Low-Risk Plugins

## Context Links

- [Overview plan](./plan.md)
- [Foundation phase](./phase-01-foundation-and-inventory.md)
- [Source plugin tree](../../skills/plugins/)
- [Root plugins directory](../../plugins/)

## Overview

Priority: P1

Status: Completed

Purpose: batch-port the 17 low-risk plugins that mainly need copied content plus root manifests.

Current state:

- All 17 T1 plugins now exist under root `plugins/`.
- All 17 T1 plugins are marked `available` in `plugins/catalog.json`.
- All 17 T1 plugins are published in both marketplaces.
- Dedicated install smoke tests remain tracked as residual release validation in Phase 05.

## Key Insights

- T1 plugins have no hooks, no bundled MCP, and no Claude `Task*` workflow.
- This is the fastest path to expanding Codex coverage.
- The batch will prove the inventory and generator are correct before moving to more complex plugins.

## Requirements

- Each T1 plugin must exist under `E:\MyProject\spec-codex\plugins\<name>\`.
- Each T1 plugin must have both root manifests.
- Each T1 plugin must be listed in both root marketplaces once validation passes.

## Architecture

T1 plugins:

- `agentic-actions-auditor`
- `ask-questions-if-underspecified`
- `claude-in-chrome-troubleshooting`
- `culture-index`
- `debug-buttercup`
- `devcontainer-setup`
- `dimensional-analysis`
- `dwarf-expert`
- `insecure-defaults`
- `let-fate-decide`
- `mutation-testing`
- `property-based-testing`
- `seatbelt-sandboxer`
- `semgrep-rule-variant-creator`
- `sharp-edges`
- `supply-chain-risk-auditor`
- `yara-authoring`

## Related Code Files

- Modify: `E:\MyProject\spec-codex\plugins\catalog.json` — add T1 metadata rows
- Create: `E:\MyProject\spec-codex\plugins\<name>\...` — copied plugin content for each T1 plugin
- Modify: `E:\MyProject\spec-codex\.claude-plugin\marketplace.json` — add validated T1 entries
- Modify: `E:\MyProject\spec-codex\.agents\plugins\marketplace.json` — add validated T1 entries
- Modify: `E:\MyProject\spec-codex\README.md` — expand supported plugin list after the batch is stable

## Implementation Steps

1. Add T1 plugin metadata to the root inventory.
2. Run the sync workflow to copy each T1 source plugin into root `plugins/`.
3. Generate `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` for each copied plugin.
4. Validate that every `SKILL.md` relative reference resolves inside the root copy.
5. Add the validated T1 plugins to both marketplaces.
6. Smoke-test install and skill discovery for at least 3 representative T1 plugins before marking the batch complete.

## Todo List

- [x] Catalog all T1 plugins
- [x] Copy all T1 source trees into root plugins
- [x] Generate root manifests for all T1 plugins
- [x] Validate links and manifest parity
- [x] Add T1 plugins to both marketplaces
- [ ] Smoke-test representative installs

## Success Criteria

- All 17 T1 plugins are present in root `plugins/`.
- All 17 T1 plugins validate cleanly.
- All 17 T1 plugins are listed in the Codex marketplace.
- No T1 plugin needs manual workflow rewrites to function in Codex.

## Risk Assessment

- Risk: README/install text still points at Claude-first usage.
  - Mitigation: keep README normalization minimal in this phase and document Codex usage at the root level first.
- Risk: category/default-prompt quality is inconsistent across the batch.
  - Mitigation: define category and prompt conventions in the inventory before generation.

## Security Considerations

- Keep source licenses and authorship metadata intact in the root manifests.
- Do not widen capabilities beyond what the skill actually needs.

## Next Steps

- Phase 02 porting is complete. Remaining install smoke coverage is tracked in Phase 05.
