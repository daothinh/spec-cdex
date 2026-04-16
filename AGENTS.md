## Repository Scope

This repository ships plugin metadata for both Claude Code and Codex.

## Layout

- Claude marketplace catalog lives at `.claude-plugin/marketplace.json`.
- Codex marketplace catalog lives at `.agents/plugins/marketplace.json`.
- Each plugin lives under `plugins/<plugin-name>/`.
- Claude metadata for a plugin lives at `plugins/<plugin-name>/.claude-plugin/plugin.json`.
- Codex metadata for a plugin lives at `plugins/<plugin-name>/.codex-plugin/plugin.json`.
- Skills remain under `plugins/<plugin-name>/skills/`.

## Editing Rules

- Keep Claude and Codex manifests aligned when plugin identity, version, repository, or license changes.
- Do not remove Claude-specific metadata while adding Codex support.
- If a plugin depends on non-Codex workflow-specific behavior, do not expose it as installable in the Codex marketplace until the workflow is ported.
- Prefer minimal metadata-only changes unless the task explicitly requires changing skill behavior.
