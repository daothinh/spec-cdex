---
name: bug-bounty-report-submitter
description: >
  Inspect live bug bounty forms with Playwright MCP, then draft and submit
  evidence-backed reports that match the platform fields, proof requirements,
  and attachment flow.
metadata:
  author: workers.io
  version: "0.1.0"
---

# Bug Bounty Report Submitter

Inspect the live submission form first, then turn validated findings into an evidence-backed report bundle and submit it through Playwright MCP.

Load these on demand:
- [references/report-structure.md](references/report-structure.md) for field mapping and section order
- [references/writing-style.md](references/writing-style.md) for natural prose rules and anti-template cleanup
- [references/playwright-submit.md](references/playwright-submit.md) for the browser automation sequence
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` if target scope or program constraints are still unclear

## Preconditions

- Reproduce the issue end to end.
- Know the affected asset, prerequisites, impact, and evidence set.
- Have the submission URL and any login requirements.
- Have a minimal PoC or replayable proof path for the bug.

If any precondition is missing, gather it before submission work starts.

## Local Bundle

Create `bug-bounty-reports/<slug>/` and keep:
- `facts.md` - raw, verified facts only
- `form-schema.json` - live form fields, options, limits, and notes
- `artifacts.json` - evidence inventory with stable IDs and file paths
- `poc.md` - replayable exploit or reproduction details
- `report.md` - final prose draft
- `submission.json` - field-to-value map for the form
- `evidence/` - screenshots, HAR, video, logs, payloads, PoC files
- `confirmation.md` - final URL, report ID, screenshots, follow-up notes

## Workflow

1. Open the submission URL with Playwright MCP before drafting anything long-form.
2. Snapshot the rendered form, complete login if needed, expand hidden sections, and record required fields, custom prompts, enums, validators, character limits, and attachment rules in `form-schema.json`.
3. Normalize the proof package. Separate observed behavior from theory in `facts.md`, inventory every artifact in `artifacts.json`, and store the replayable exploit path in `poc.md`.
4. Build `submission.json` from `form-schema.json`, not from a fixed template. Include custom site fields exactly as discovered.
5. Draft `report.md` from `facts.md`, `artifacts.json`, and `poc.md` using [references/report-structure.md](references/report-structure.md). Write to the actual field labels and limits from `form-schema.json`.
6. Run the evidence and style pass from [references/writing-style.md](references/writing-style.md). Every major claim must map to an artifact or be marked as an explicit assumption.
7. Use the Playwright flow in [references/playwright-submit.md](references/playwright-submit.md) to fill the live form, upload proof, preview or save draft, and submit only after the visible form matches `submission.json`.
8. Capture the confirmation page, report ID, and final URL in `confirmation.md`.

## Report Rules

- Lead with the bug and affected asset, not background.
- Discover the live form schema before drafting prose.
- Prefer short paragraphs and numbered reproduction steps.
- Tie impact to the program context: auth bypass, account takeover, data exposure, privilege gain, funds risk, or availability.
- State prerequisites honestly. If auth, timing, or rare roles are required, say so.
- Mention observed result before expected result.
- Keep observed impact separate from reasoned extension.
- Reference evidence naturally in the text or attachment notes; do not leave important claims unsupported.
- Mention the PoC when it is needed to replay the issue or understand exploitability.
- Never inflate severity with generic breach language.
- Never invent screenshots, logs, identifiers, or attachments.
- Rewrite for the actual field label and limit, not a mail-merge template.

## Form-Fill Rules

- Use `browser_snapshot` before any drafting, before the first fill, and after each major section.
- Fill metadata fields first because severity or asset choices may reveal extra required prompts.
- Prefer `browser_fill_form` for standard controls and `browser_type` for editors with live validation.
- Update `form-schema.json` if hidden or dynamic fields appear after a selection.
- Use `browser_file_upload` only after `submission.json`, `artifacts.json`, and local artifact paths are final.
- If a field strips markdown or truncates text, rewrite for that field instead of forcing the template.
- If the platform supports drafts, save one before final submit.
- If a captcha or MFA gate blocks submission, stop after the draft and report the blocker.

## Output

Return:
- report title
- submission URL
- confirmation ID or blocker
- saved `form-schema.json` and `submission.json` paths
- saved local bundle path
- any manual follow-up the user still needs
