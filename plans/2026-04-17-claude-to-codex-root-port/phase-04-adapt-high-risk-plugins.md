# Phase 04: Adapt T3 High-Risk Plugins

## Context Links

- [Overview plan](./plan.md)
- [Foundation phase](./phase-01-foundation-and-inventory.md)
- [Source plugin tree](../../skills/plugins/)
- [Root plugins directory](../../plugins/)

## Overview

Priority: P1

Status: In Progress

Purpose: port the 9 high-risk plugins that depend on Claude-specific workflow semantics or runtime features. This is the only phase where root-side skill behavior changes are expected.

Current state:

- All 9 T3 plugins now exist under root `plugins/`.
- All 9 T3 plugins have explicit `blocked` status in `plugins/catalog.json`.
- None of the 9 T3 plugins are listed in the Codex marketplace.
- Root staging is done; Codex-compatible rewrites and/or promotion decisions are still open.

## Key Insights

- T3 is where “copy + manifest” stops being enough.
- Some plugins are still publishable after prompt rewrites.
- Some plugins should exist in root `plugins/` but stay out of the Codex marketplace until a real replacement exists.

## Requirements

- Keep all behavior changes confined to the root copy.
- Preserve the source plugin as reference content.
- Add a per-plugin publish decision: `available` or `blocked`.

## Architecture

T3 plugins:

- `fp-check`
- `gh-cli`
- `git-cleanup`
- `modern-python`
- `second-opinion`
- `skill-improver`
- `static-analysis`
- `workflow-skill-design`
- `zeroize-audit`

### Publishable After Root-Only Rewrite

- `git-cleanup` — replace `AskUserQuestion` gate with plain user question and safe default handling
- `second-opinion` — make bundled MCP optional or verify Codex plugin loading first
- `static-analysis` — rewrite `Task*` orchestration into Codex-friendly phased execution
- `workflow-skill-design` — rewrite Claude-specific tool assumptions into Codex equivalents
- `zeroize-audit` — replace Claude tool mentions with Codex-compatible instructions and inline fallbacks

### Stage But Do Not Publish Until Runtime Parity Exists

- `gh-cli` — depends on Claude hook interception and session cleanup behavior
- `modern-python` — depends on SessionStart PATH-shim hook behavior
- `skill-improver` — depends on stop-hook loop continuation
- `fp-check` — uses stop hooks for completeness enforcement; can be ported only if enforcement becomes explicit, not implicit

## Related Code Files

- Modify: `E:\MyProject\spec-codex\plugins\catalog.json` — set T3 status and notes
- Create: `E:\MyProject\spec-codex\plugins\<name>\...` — copied content and root-only rewrites
- Modify: `E:\MyProject\spec-codex\.agents\plugins\marketplace.json` — add only the validated T3 plugins
- Modify: `E:\MyProject\spec-codex\README.md` — document blocked versus available T3 plugins

## Implementation Steps

1. Copy all T3 source trees into root `plugins/`.
2. For each plugin, classify the blocker: hooks, MCP, `Task*`, `AskUserQuestion`, or stop-loop behavior.
3. Rewrite root `SKILL.md` files only where Codex compatibility actually requires it.
4. Keep root README notes for any degraded or advisory behavior compared with Claude.
5. Publish only the T3 plugins that pass functional smoke tests in Codex.
6. Mark the remaining T3 plugins as blocked in the root inventory and keep them out of the Codex marketplace.

## Todo List

- [x] Copy all T3 source trees into root plugins
- [ ] Rewrite prompt flows for `git-cleanup`, `second-opinion`, `static-analysis`, `workflow-skill-design`, `zeroize-audit`
- [ ] Evaluate whether `fp-check` can be safely downgraded from enforced to advisory behavior
- [x] Keep `gh-cli`, `modern-python`, and `skill-improver` blocked until an equivalent Codex runtime path exists
- [x] Update README support matrix

## Success Criteria

- All 9 T3 plugins exist in root `plugins/`.
- Every T3 plugin has an explicit status in the inventory.
- Only validated T3 plugins are added to the Codex marketplace.
- Blocked T3 plugins remain installable for Claude metadata if needed, but are not falsely advertised as Codex-ready.

## Risk Assessment

- Risk: root rewrites drift too far from source behavior.
  - Mitigation: keep rewrites narrow and document every deliberate deviation.
- Risk: hook-dependent plugins get published prematurely.
  - Mitigation: publish gating lives in the root inventory, not in manual judgment.

## Security Considerations

- `gh-cli`, `static-analysis`, `zeroize-audit`, and `second-opinion` invoke security-sensitive flows. Do not weaken safety guidance while rewriting prompts.
- Keep audit and review plugins conservative when replacing explicit gates with plain conversation prompts.

## Next Steps

- Phase 05 is already handling validator/release gating, but this phase stays in progress until any T3 plugin is either ported for Codex or intentionally left blocked with final rationale.
