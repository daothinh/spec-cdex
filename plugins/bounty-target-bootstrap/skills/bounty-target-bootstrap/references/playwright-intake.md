# Playwright Intake

Use Playwright MCP to collect rendered scope, not just raw HTML.

## Sequence

1. `browser_navigate` to the program URL.
2. `browser_snapshot` to map headings, links, accordions, tabs, and tables.
3. Expand hidden sections with `browser_click`.
4. After each change, run `browser_snapshot` again and copy decisive scope text into notes.
5. Stop when the page has enough data to fill the JSON contract in `workspace-contract.md`.

## Fields To Extract

- `program_name`
- `program_url`
- `target_type`
- `scope_summary`
- `in_scope`
- `out_of_scope`
- `rules`
- `safe_harbor`
- `submission_guidelines`
- `auth_notes`
- `environment_notes`
- `program_notes`
- `repo_urls`
- `artifacts`
- `package_names`
- `app_urls`
- `raw_scope_notes`

## Target-Type Rules

- Keep only entries clearly marked `whitebox` or `android`.
- If the page mixes target classes, store unsupported ones in notes and skip them.
- If `whitebox` scope includes multiple repos, keep them all.
- If `android` scope exposes only APK or store links, keep those links even when source is absent.

## Good Capture Pattern

- Expand every rules or scope accordion before copying text.
- Preserve each scope bucket separately: in scope, out of scope, rules, safe harbor.
- Prefer full absolute URLs.
- Preserve exact package names and build identifiers.
- Preserve exact testing restrictions and environment boundaries.

## Bad Capture Pattern

- Guessing the target type from branding alone
- Dropping secondary source repos because they look less important
- Rewriting or summarizing strict rules too loosely
- Treating unsupported assets as in scope
