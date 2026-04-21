---
name: bounty-target-bootstrap
description: >
  Bootstrap a whitebox or Android bounty target from a program URL. Use
  Playwright MCP to capture scope, save target metadata in-repo, pull source or
  APK artifacts, and prep the next bounty playbook.
metadata:
  author: workers.io
  version: "0.1.0"
---

# Bounty Target Bootstrap

Bootstrap a target from a program page when intake must finish before deeper auditing.

Load these on demand:
- [references/playwright-intake.md](references/playwright-intake.md) for the Playwright MCP flow
- [references/workspace-contract.md](references/workspace-contract.md) for the input JSON and generated layout
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` after whitebox source lands locally
- `plugins/bounty-hunting-programs/skills/bounty-program-mobile-android/SKILL.md` for Android follow-on work

## Inputs To Capture

- program name and program URL
- target type: `whitebox` or `android`
- scope summary, full in-scope list, full out-of-scope list, and rules
- safe-harbor notes, submission notes, auth notes, and environment limits
- source repo URLs, APK or archive URLs, package names, app or store URLs
- raw scope notes copied from the rendered page

## Workflow

1. Use Playwright MCP, not plain HTTP, so rendered scope tables and collapsed sections are visible.
2. Navigate to the URL, expand scope and rule accordions, and capture only assets explicitly marked `whitebox` or `android`.
3. Ignore unsupported assets. If no whitebox or Android target exists, write the unsupported note and stop.
4. Normalize findings into a JSON file matching `references/workspace-contract.md`.
5. Run:
   `python plugins/bounty-target-bootstrap/skills/bounty-target-bootstrap/scripts/bootstrap_target.py --input <json> --repo-root .`
6. Review `audit-targets/<slug>/scope/target.json` and `audit-targets/<slug>/prep/ready-for-bounty.md`.
7. Continue with the next lane:
   - `android` -> `bounty-program-mobile-android`
   - `whitebox` -> start with `bounty-program-triage` on the cloned source tree

## Playwright Extraction Rules

- Prefer `browser_snapshot` after each expand or click cycle.
- Save decisive scope text into `raw_scope_notes`; do not rely on memory.
- Persist `in_scope`, `out_of_scope`, and `rules` as separate lists, not one merged blob.
- Capture absolute URLs for repos, APKs, archives, docs, and login portals.
- Record qualifiers exactly: production or staging, test accounts, rate limits, and forbidden actions.
- Keep every repo URL. Let the bootstrap script fingerprint them before choosing the lane.

## Output Rules

- Keep generated artifacts inside `audit-targets/<slug>/`.
- Preserve both raw notes and normalized JSON.
- Write dedicated files for `in-scope`, `out-of-scope`, `rules`, and program notes.
- Clone source repos when a git URL exists.
- Download APK or source archives when direct URLs exist and are explicitly in scope.
- Surface the suggested bounty lane from `ready-for-bounty.md` before starting deeper review.

## Rules

- Do not bootstrap web-only, smart-contract-only, or native-only targets through this skill.
- Do not invent scope. If a field is absent, leave it empty and note the gap in `raw_scope_notes`.
- Do not start exploit attempts from the scope page. Finish intake first.
