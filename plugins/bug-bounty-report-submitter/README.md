# bug-bounty-report-submitter

Inspect live bug bounty forms or webmail with Playwright MCP, then draft and deliver program-specific reports that match the discovered fields, evidence requirements, and attachment flow. The shared writing flow is now schema-first and target-specific: exact vulnerable function or endpoint, decisive snippet, exploit walkthrough, PoC output, and only then the minimal exploit excerpt. Attachments are supplemental by default and must not be the primary place where bug details live.

## Included

| Path | Purpose |
|------|---------|
| `skills/bug-bounty-report-submitter/SKILL.md` | Core live-form draft-and-submit workflow |
| `skills/bug-bounty-report-submitter/references/immunefi-body-template.md` | Evidence-first local drafting scaffold for long-form detail bodies |
| `skills/bug-bounty-report-submitter/references/report-writing-rules.md` | Shared impact-first bug bounty report rules, severity discipline, and checklist |
| `skills/bug-bounty-report-submitter/references/report-structure.md` | Report section and field mapping for form workflows |
| `skills/bug-bounty-report-submitter/references/writing-style.md` | Shared natural writing and anti-template pass |
| `skills/bug-bounty-report-submitter/references/playwright-submit.md` | Playwright MCP submission sequence for forms |
| `skills/bug-bounty-report-submitter/scripts/prepare_report_artifacts.py` | Copy `artifacts/` into `evidence/` and build `artifacts.json`, including Caido evidence metadata |
| `skills/bug-bounty-report-submitter/scripts/prepare_web3_report_bundle.py` | Materialize `web3-facts.json`, `asset-delta.md`, and `reproduction-matrix.md` from a verified finding bundle |
| `skills/bug-bounty-email-submitter/SKILL.md` | Email-based disclosure workflow |
| `skills/bug-bounty-email-submitter/references/email-report-structure.md` | Subject and body structure for bug report emails |
| `skills/bug-bounty-email-submitter/references/playwright-email-submit.md` | Playwright MCP compose-and-send sequence for webmail |

## Usage

1. Gather independently re-verified findings, evidence, PoC, and either the program submission URL or the recipient email plus sender mailbox URL.
2. Choose the matching skill:
   - `bug-bounty-report-submitter` for live submission forms
   - `bug-bounty-email-submitter` for disclosure by email through webmail
3. Let Codex inspect the live surface with Playwright MCP, build `bug-bounty-reports/<slug>/<finding-id>/`, carry the `reverify.md` verdict, `severity.md` triage, and `manual-review.md` checkpoint into the bundle, then draft, submit, or send and capture the confirmation state.
4. Normalize local evidence before drafting. Run `prepare_report_artifacts.py` so `artifacts.json` and `evidence/` exist, and run `prepare_web3_report_bundle.py` when web3-specific report files still need to be materialized.
5. Stop if the proof still depends on unresolved domain-logic or cryptographic assumptions. The manual 20-minute review is a hard gate, not a nicety.
6. Draft the detail body from the shared evidence-first scaffold before adapting it to the live form or mailbox, then rewrite it into platform-native prose so the final report always shows the exact bug location, root cause, exploit path, PoC output, and minimal exploit excerpt without reading like a reusable template.
7. Keep the final report self-contained. Only upload attachments when the platform genuinely requires them or when a supplemental artifact adds decisive evidence. If a file is mandatory, prefer a markdown appendix such as `report-appendix.md` over raw code files.
