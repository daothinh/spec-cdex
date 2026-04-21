---
name: bug-bounty-email-submitter
description: >
  Draft and send evidence-backed bug bounty report emails through a live webmail
  UI with Playwright MCP, using the user-specified recipient and verified proof.
metadata:
  author: workers.io
  version: "0.1.0"
---

# Bug Bounty Email Submitter

Draft the report bundle first, then open the sender mailbox in a browser and send from the live webmail UI with Playwright MCP.

Load these on demand:
- [references/email-report-structure.md](references/email-report-structure.md) for subject and body layout
- [references/playwright-email-submit.md](references/playwright-email-submit.md) for the inbox and compose flow
- [shared writing-style reference](../bug-bounty-report-submitter/references/writing-style.md) for the natural-prose cleanup pass
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` if target scope or disclosure constraints are still unclear

## Preconditions

- Reproduce the issue end to end.
- Know the affected asset, prerequisites, impact, and evidence set.
- Have the recipient email address supplied by the user.
- Have the sender mailbox URL and any login requirements.
- Have replayable proof in screenshots, HAR, video, requests, or a PoC file.

If any precondition is missing, gather it before email work starts.

## Local Bundle

Create `bug-bounty-reports/<slug>/email/` and keep:
- `facts.md` - raw verified facts only
- `artifacts.json` - evidence inventory with stable IDs and file paths
- `poc.md` - replayable exploit or reproduction details
- `mail-ui-schema.json` - live compose controls, attachment flow, and send confirmation signals
- `mail-envelope.json` - `to`, optional `cc` and `bcc`, subject, and attachment plan
- `email-draft.md` - final subject and body draft
- `confirmation.md` - sent time, recipient, provider confirmation, screenshot path, follow-up notes
- `evidence/` - screenshots, HAR, video, logs, payloads, PoC files

## Workflow

1. Confirm the recipient address, sender mailbox URL, and whether the program wants plain text, markdown-like formatting, or a strict disclosure template.
2. Open the mailbox with Playwright MCP before drafting anything long-form. Snapshot the inbox, login flow, compose button, editor type, attachment control, draft affordance, and success indicator. Store the observed UI contract in `mail-ui-schema.json`.
3. Normalize the proof package. Separate observed behavior from theory in `facts.md`, inventory every artifact in `artifacts.json`, and store the replayable exploit path in `poc.md`.
4. Build `mail-envelope.json` from the verified recipient and the discovered mailbox behavior. Do not invent `cc`, `bcc`, reply-to, or tracking settings.
5. Draft `email-draft.md` from `facts.md`, `artifacts.json`, and `poc.md` using [references/email-report-structure.md](references/email-report-structure.md). Keep the subject and opening sentence specific to the bug and asset.
6. Run the cleanup pass from the [shared writing-style reference](../bug-bounty-report-submitter/references/writing-style.md). Every major claim must map to an artifact or be marked as an explicit assumption.
7. Use the Playwright flow in [references/playwright-email-submit.md](references/playwright-email-submit.md) to open a fresh compose window, set the `To` field to the user-specified address, fill the subject and body from `mail-envelope.json` and `email-draft.md`, upload proof, and save a draft when the provider supports it.
8. Take a final snapshot, verify the visible recipient, subject, body, and attachments match the local bundle, then send. Capture the provider confirmation, sent-folder URL if available, and any message ID in `confirmation.md`.

## Email Rules

- Lead with the bug and affected asset, not generic disclosure filler.
- Use the user-specified recipient exactly. Do not rewrite or expand the address list unless the user asks.
- Keep the message readable in plain text even if the provider uses a rich-text editor.
- Prefer short paragraphs and numbered reproduction steps.
- Mention the decisive proof naturally: screenshots, HAR, video, replay script, or `poc.md`.
- Separate observed impact from reasoned extension.
- Mention prerequisites honestly. If auth, rare roles, or timing are required, say so.
- Keep remediation short and optional unless the program explicitly asks for it.
- Do not send from the browser until the compose view matches `mail-envelope.json` and `email-draft.md`.
- Do not claim the report was sent unless a visible provider confirmation was captured.

## Form-Fill Rules

- Use `browser_snapshot` before login, after login, after compose opens, and before sending.
- Prefer `browser_fill_form` for standard input fields and `browser_type` for rich-text editors or chip-based address boxes.
- If the mailbox uses chips or autocomplete for recipients, confirm the address was accepted before filling the body.
- If the editor strips formatting, rewrite the body for that editor instead of fighting it.
- Upload attachments only after `artifacts.json`, `mail-envelope.json`, and local evidence paths are final.
- If the provider supports drafts, save one before final send.
- If MFA, captcha, suspicious-login review, or anti-automation gates block sending, stop after the draft and report the blocker.

## Output

Return:
- email subject
- recipient address
- sender mailbox URL
- confirmation ID, sent-folder URL, or blocker
- saved `mail-ui-schema.json` and `mail-envelope.json` paths
- saved local bundle path
- any manual follow-up the user still needs
