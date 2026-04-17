# Phase 05: Validate and Release

## Context Links

- [Overview plan](./plan.md)
- [Codex marketplace](../../.agents/plugins/marketplace.json)
- [Claude marketplace](../../.claude-plugin/marketplace.json)
- [Root README](../../README.md)

## Overview

Priority: P1

Status: In Progress

Purpose: verify the full root port, publish only the plugins that are truly ready, and document what is still blocked.

Current state:

- Full validator passes: 45 root plugins, 45 Claude marketplace entries, 36 Codex marketplace entries.
- Marketplace gating is in place: all 29 T1/T2 ports are published to Codex, and all 9 T3 plugins remain blocked.
- README now documents the staged Codex policy and the blocked T3 list.
- Dedicated install smoke tests and representative invocation checks remain open.

## Key Insights

- The port is only complete when the marketplaces, manifests, copied assets, and docs all agree.
- A staged support matrix is better than pretending every plugin is equally ready.
- Validation needs to happen at three levels: file integrity, metadata integrity, and install/use smoke tests.

## Requirements

- Both marketplaces must match the root inventory.
- Every published plugin must install from the root marketplace path.
- README must list newly available plugins and clearly call out blocked T3 plugins.

## Architecture

Validation layers:

1. File validation
   - root plugin exists
   - dual manifests exist
   - skill paths exist
   - relative references resolve

2. Metadata validation
   - Claude and Codex manifests are aligned
   - marketplace entries resolve to the correct root plugin
   - blocked plugins are absent from the Codex marketplace

3. Smoke testing
   - install representative T1 plugin
   - install representative T2 multi-skill plugin
   - run one publishable T3 plugin
   - confirm blocked T3 plugins are documented, not listed

## Related Code Files

- Modify: `E:\MyProject\spec-codex\.claude-plugin\marketplace.json`
- Modify: `E:\MyProject\spec-codex\.agents\plugins\marketplace.json`
- Modify: `E:\MyProject\spec-codex\README.md`
- Use: `E:\MyProject\spec-codex\scripts\validate-root-plugins.mjs`

## Implementation Steps

1. Run the validator across the full root plugin set.
2. Fix any missing files, unresolved references, or manifest drift.
3. Perform smoke installs and one representative invocation per risk tier.
4. Update the root README with the final support matrix.
5. Freeze the publish set and keep blocked plugins out of the Codex marketplace.

## Todo List

- [x] Run full validator
- [x] Resolve all validation failures
- [ ] Smoke-test T1, T2, and publishable T3 plugins
- [x] Update README support matrix
- [x] Finalize marketplace catalogs

## Success Criteria

- Validator passes for every root plugin.
- README matches the real publish status.
- Codex marketplace contains every validated plugin and no blocked plugin.
- Claude and Codex marketplace metadata stay aligned.

## Risk Assessment

- Risk: README and marketplace status diverge after late fixes.
  - Mitigation: treat README update as part of the release gate, not optional cleanup.
- Risk: representative smoke tests miss a broken plugin in a large batch.
  - Mitigation: use validator for breadth and smoke tests for depth.

## Security Considerations

- Do not mark review or audit plugins as ready unless their gating behavior is still trustworthy after root-side rewrites.
- Keep installation policies conservative for plugins that execute external CLIs or security tooling.

## Next Steps

- After dedicated smoke coverage is finished, future source plugin changes can be re-imported through the same root sync and validation workflow.
