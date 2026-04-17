# Phase 03: Port T2 Medium-Risk Plugins

## Context Links

- [Overview plan](./plan.md)
- [Foundation phase](./phase-01-foundation-and-inventory.md)
- [Source plugin tree](../../skills/plugins/)
- [Root plugins directory](../../plugins/)

## Overview

Priority: P1

Status: Completed

Purpose: port the 12 medium-risk plugins that are structurally clean for Codex but have more skills, more assets, or command-oriented documentation that needs careful packaging.

Current state:

- All 12 T2 plugins now exist under root `plugins/`.
- All 12 T2 plugins are marked `available` in `plugins/catalog.json`.
- All 12 T2 plugins are published in both marketplaces.
- Dedicated install smoke tests remain tracked as residual release validation in Phase 05.

## Key Insights

- T2 plugins are mostly packaging work, not behavioral rewrites.
- Multi-skill plugins need good manifest descriptions and prompts or they will be hard to discover from the marketplace.
- Command folders can remain in the root copy as docs or auxiliary assets even if Codex does not consume them directly.

## Requirements

- Preserve all skill-relative references in the root copy.
- Preserve auxiliary assets needed by skills: agents, resources, scripts, references, templates, command docs.
- Only publish a T2 plugin after its multi-skill layout works in the root copy.

## Architecture

T2 plugins:

- `audit-context-building`
- `building-secure-contracts`
- `burpsuite-project-parser`
- `constant-time-analysis`
- `differential-review`
- `entry-point-analyzer`
- `firebase-apk-scanner`
- `semgrep-rule-creator`
- `spec-to-code-compliance`
- `testing-handbook-skills`
- `trailmark`
- `variant-analysis`

## Related Code Files

- Modify: `E:\MyProject\spec-codex\plugins\catalog.json` — add T2 metadata rows
- Create: `E:\MyProject\spec-codex\plugins\<name>\...` — copied plugin content for each T2 plugin
- Modify: `E:\MyProject\spec-codex\.claude-plugin\marketplace.json` — add validated T2 entries
- Modify: `E:\MyProject\spec-codex\.agents\plugins\marketplace.json` — add validated T2 entries
- Modify: `E:\MyProject\spec-codex\README.md` — document multi-skill plugin availability

## Implementation Steps

1. Add all T2 plugin metadata to the root inventory.
2. Copy full source trees for each T2 plugin into root `plugins/`.
3. Generate dual manifests with clear `displayName`, category, and Codex `defaultPrompt` values.
4. Validate all nested skill references, agent prompts, scripts, and resource files.
5. Run smoke tests on one single-skill plugin with command docs and one large multi-skill plugin.
6. Publish the validated T2 plugins into both marketplaces.

## Todo List

- [x] Catalog all T2 plugins
- [x] Copy all T2 source trees into root plugins
- [x] Generate manifests for each T2 plugin
- [x] Validate nested asset references
- [ ] Smoke-test representative T2 plugins
- [x] Publish validated T2 plugins

## Success Criteria

- All 12 T2 plugins are present in root `plugins/`.
- Multi-skill plugins preserve all internal references after copy.
- Codex marketplace discovery is sane for large plugins such as `trailmark`, `testing-handbook-skills`, and `building-secure-contracts`.

## Risk Assessment

- Risk: very large plugins become noisy in the marketplace.
  - Mitigation: use better short descriptions and prompts in the root manifest.
- Risk: command-oriented docs confuse Codex users.
  - Mitigation: root README should explain that Codex consumes skills, while commands stay as reference content.

## Security Considerations

- Avoid exposing scripts as executable entrypoints unless the skill already invokes them intentionally.
- Preserve any warning text present in source READMEs for security-sensitive tools.

## Next Steps

- Phase 03 porting is complete. Remaining install smoke coverage is tracked in Phase 05.
