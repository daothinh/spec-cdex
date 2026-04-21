# bug-bounty-report-submitter

Inspect live bug bounty forms with Playwright MCP, then draft and submit program-specific reports that match the discovered fields, evidence requirements, and attachment flow.

## Included

| Path | Purpose |
|------|---------|
| `skills/bug-bounty-report-submitter/SKILL.md` | Core draft-and-submit workflow |
| `skills/bug-bounty-report-submitter/references/report-structure.md` | Report section and field mapping |
| `skills/bug-bounty-report-submitter/references/writing-style.md` | Natural writing and anti-template pass |
| `skills/bug-bounty-report-submitter/references/playwright-submit.md` | Playwright MCP submission sequence |

## Usage

1. Gather verified findings, evidence, PoC, and the submission URL.
2. Activate the skill and let Codex open the form with Playwright MCP, inventory the live fields, and build `bug-bounty-reports/<slug>/`.
3. Draft the report from the discovered schema, then let Codex fill the form, upload proof, and capture the confirmation page.
