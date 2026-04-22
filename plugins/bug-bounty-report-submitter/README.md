# bug-bounty-report-submitter

Inspect live bug bounty forms or webmail with Playwright MCP, then draft and deliver program-specific reports that match the discovered fields, evidence requirements, and attachment flow.

## Included

| Path | Purpose |
|------|---------|
| `skills/bug-bounty-report-submitter/SKILL.md` | Core live-form draft-and-submit workflow |
| `skills/bug-bounty-report-submitter/references/report-writing-rules.md` | Shared impact-first bug bounty report rules, severity discipline, and checklist |
| `skills/bug-bounty-report-submitter/references/report-structure.md` | Report section and field mapping for form workflows |
| `skills/bug-bounty-report-submitter/references/writing-style.md` | Shared natural writing and anti-template pass |
| `skills/bug-bounty-report-submitter/references/playwright-submit.md` | Playwright MCP submission sequence for forms |
| `skills/bug-bounty-email-submitter/SKILL.md` | Email-based disclosure workflow |
| `skills/bug-bounty-email-submitter/references/email-report-structure.md` | Subject and body structure for bug report emails |
| `skills/bug-bounty-email-submitter/references/playwright-email-submit.md` | Playwright MCP compose-and-send sequence for webmail |

## Usage

1. Gather independently re-verified findings, evidence, PoC, and either the program submission URL or the recipient email plus sender mailbox URL.
2. Choose the matching skill:
   - `bug-bounty-report-submitter` for live submission forms
   - `bug-bounty-email-submitter` for disclosure by email through webmail
3. Let Codex inspect the live surface with Playwright MCP, build `bug-bounty-reports/<slug>/`, carry the `reverify.md` verdict into the bundle, then draft, submit, or send and capture the confirmation state.
