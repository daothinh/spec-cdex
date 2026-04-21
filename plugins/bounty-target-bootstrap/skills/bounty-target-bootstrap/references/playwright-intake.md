# Playwright Intake

Use Playwright MCP to collect rendered scope, not just raw HTML.

This step is strictly host-provided intake. Capture what the program page exposes for later audit or whitebox work; do not enrich it with guessed assets or outside intelligence here.

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
- `focus_areas`
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
- `source_code_urls`
- `artifacts`
- `package_names`
- `app_urls`
- `web_urls`
- `api_urls`
- `rpc_urls`
- `ws_urls`
- `docs_urls`
- `api_spec_urls`
- `audit_report_urls`
- `registry_urls`
- `explorer_urls`
- `smart_contracts`
- `raw_scope_notes`

## Target-Type Rules

- Keep only entries clearly marked `whitebox`, `android`, or `smart-contract`.
- If the page mixes target classes, store unsupported ones in notes and skip them.
- If `whitebox` scope includes multiple repos, keep them all.
- If `android` scope exposes only APK or store links, keep those links even when source is absent.
- If the host provides contract addresses, explorer links, ABI files, audit PDFs, or API specs, persist them even when they are not the primary execution lane.
- If the target belongs to a domain like wallet, blockchain, or exchange, store that under `focus_areas` even when `target_type` stays `whitebox` or `android`.

## Good Capture Pattern

- Expand every rules or scope accordion before copying text.
- Preserve each scope bucket separately: in scope, out of scope, rules, safe harbor.
- Prefer full absolute URLs.
- Preserve exact package names and build identifiers.
- Preserve exact chain names, chain IDs, network labels, proxy or implementation addresses, explorer URLs, ABI URLs, and source URLs for contracts.
- Preserve every host-provided surface pointer: docs, RPC endpoints, WebSocket endpoints, audit reports, API schemas, package registries.
- Preserve exact testing restrictions and environment boundaries.

## Bad Capture Pattern

- Guessing the target type from branding alone
- Dropping secondary source repos because they look less important
- Dropping contract metadata because it is "just documentation"
- Treating an explorer URL or audit PDF as optional noise instead of a first-class intake artifact
- Rewriting or summarizing strict rules too loosely
- Treating unsupported assets as in scope
