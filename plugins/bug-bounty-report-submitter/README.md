# bug-bounty-report-submitter

Inspect live bug bounty forms or webmail with Playwright MCP, then draft and deliver program-specific reports that match the discovered fields, evidence requirements, and attachment flow. The shared writing flow is now schema-first and target-specific: exact vulnerable function or endpoint, decisive snippet, exploit walkthrough, runnable PoC with command or replay sequence, PoC output, and only then the minimal exploit excerpt. Attachments are supplemental by default and must not be the primary place where bug details live. When forms are too small, the plugin now supports a gist-ready external proof pack that preserves full PoC files and logs without making the main body dependent on them.

## Included

| Path | Purpose |
|------|---------|
| `skills/bug-bounty-report-submitter/SKILL.md` | Core live-form draft-and-submit workflow |
| `skills/bug-bounty-report-submitter/references/immunefi-body-template.md` | Evidence-first local drafting scaffold for long-form detail bodies |
| `skills/bug-bounty-report-submitter/references/report-writing-rules.md` | Shared impact-first bug bounty report rules, severity discipline, and checklist |
| `skills/bug-bounty-report-submitter/references/report-structure.md` | Report section and field mapping for form workflows |
| `skills/bug-bounty-report-submitter/references/writing-style.md` | Shared natural writing and anti-template pass |
| `skills/bug-bounty-report-submitter/references/external-proof-pack.md` | Workflow for mandatory secret-gist proof handling |
| `skills/bug-bounty-report-submitter/references/playwright-submit.md` | Playwright MCP submission sequence for forms |
| `skills/bug-bounty-report-submitter/scripts/prepare_report_artifacts.py` | Copy `artifacts/` into `evidence/` and build `artifacts.json`, including Caido evidence metadata |
| `skills/bug-bounty-report-submitter/scripts/prepare_web3_report_bundle.py` | Materialize `web3-facts.json`, `asset-delta.md`, and `reproduction-matrix.md` from a verified finding bundle |
| `skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py` | Build a gist-backed runnable PoC proof pack and publish or register the required secret gist link |
| `skills/bug-bounty-report-submitter/scripts/validate_submission_bundle.py` | Hard-stop validator for `submission.json` / `mail-envelope.json` proof-reference completeness |
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
5. Treat `poc.md` as incomplete until it contains an exact run command or deterministic replay sequence plus a decisive success signal. Every report bundle must also carry a secret gist link containing the detailed PoC, helper files, the full report, and raw logs. Build `proof-pack/` with `prepare_external_proof_pack.py`, add an `external_proof` block to `submission.json` or `mail-envelope.json`, and include the gist URL in the report body itself, starting in the opening summary or intro paragraph.
6. Run `validate_submission_bundle.py --bundle-dir <bundle-dir> --channel form|email` before final submit or send. If the payload or report body omits the required gist link, stop instead of sending an incomplete report.
7. Stop if the proof still depends on unresolved domain-logic or cryptographic assumptions. The manual 20-minute review is a hard gate, not a nicety.
8. Draft the detail body from the shared evidence-first scaffold before adapting it to the live form or mailbox, then rewrite it into platform-native prose so the final report always shows the exact bug location, root cause, exploit path, runnable replay, PoC output, and minimal exploit excerpt without reading like a reusable template. The finished report should read like a careful whitehat note written for one program, not an AI-generated bulk submission.
9. Keep the final report self-contained. Only upload attachments when the platform genuinely requires them or when a supplemental artifact adds decisive evidence. If a file is mandatory, prefer a markdown appendix such as `report-appendix.md` over raw code files.
