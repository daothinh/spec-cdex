---
name: bug-bounty-email-submitter
description: >
  Draft and send evidence-backed bug bounty report emails through a live webmail
  UI with Playwright MCP, using the user-specified recipient and verified proof.
metadata:
  author: workers.io
  version: "0.1.1"
---

# Bug Bounty Email Submitter

Draft the report bundle first, then open the sender mailbox in a browser and send from the live webmail UI with Playwright MCP.

Load these on demand:
- [shared report-writing rules](../bug-bounty-report-submitter/references/report-writing-rules.md) for impact-first claims, title discipline, severity guidance, and final checklist
- [references/email-report-structure.md](references/email-report-structure.md) for subject and body layout
- [references/playwright-email-submit.md](references/playwright-email-submit.md) for the inbox and compose flow
- [shared writing-style reference](../bug-bounty-report-submitter/references/writing-style.md) for the natural-prose cleanup pass
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` if target scope or disclosure constraints are still unclear

## Preconditions

- Reproduce the issue end to end.
- Have an independent re-verification verdict for the finding. The closed-loop standard expects `TRUE POSITIVE` from `security-finding-reverify` before any email disclosure work begins.
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
- `reverify.md` - independent re-verification verdict and blockers already checked
- `mail-ui-schema.json` - live compose controls, attachment flow, and send confirmation signals
- `mail-envelope.json` - `to`, optional `cc` and `bcc`, subject, and attachment plan
- `email-draft.md` - final subject and body draft
- `confirmation.md` - sent time, recipient, provider confirmation, screenshot path, follow-up notes
- `evidence/` - screenshots, HAR, video, logs, payloads, PoC files

## Workflow

1. Confirm the recipient address, sender mailbox URL, and whether the program wants plain text, markdown-like formatting, or a strict disclosure template.
2. Open the mailbox with Playwright MCP before drafting anything long-form. Snapshot the inbox, login flow, compose button, editor type, attachment control, draft affordance, and success indicator. Store the observed UI contract in `mail-ui-schema.json`.
3. Normalize the proof package. Separate observed behavior from theory in `facts.md`, inventory every artifact in `artifacts.json`, store the replayable exploit path in `poc.md`, and carry the independent verdict into `reverify.md`.
4. Build `mail-envelope.json` from the verified recipient and the discovered mailbox behavior. Do not invent `cc`, `bcc`, reply-to, or tracking settings.
5. Draft `email-draft.md` from `facts.md`, `artifacts.json`, `poc.md`, and `reverify.md` using [references/email-report-structure.md](references/email-report-structure.md) and the [shared report-writing rules](../bug-bounty-report-submitter/references/report-writing-rules.md). Build the subject from target, exact vuln type, location, and max observed impact.
6. Run the cleanup pass from the [shared writing-style reference](../bug-bounty-report-submitter/references/writing-style.md) plus the checklist in the [shared report-writing rules](../bug-bounty-report-submitter/references/report-writing-rules.md). Every major claim must map to an artifact or be marked as an explicit assumption. Do not proceed if the finding is still `reverify-pending`, `needs-more-evidence`, or `false-positive`.
7. Use the Playwright flow in [references/playwright-email-submit.md](references/playwright-email-submit.md) to open a fresh compose window, set the `To` field to the user-specified address, fill the subject and body from `mail-envelope.json` and `email-draft.md`, upload proof, and save a draft when the provider supports it.
8. Take a final snapshot, verify the visible recipient, subject, body, and attachments match the local bundle, then send. Capture the provider confirmation, sent-folder URL if available, and any message ID in `confirmation.md`.

## Email Rules

- Lead with the bug and affected asset, not generic disclosure filler.
- Prefer the shared formula from `report-writing-rules.md`: `[Target] - [Vulnerability Type] at [Location] leads to [Impact]`.
- Use precise technical names in the subject: `IDOR`, `RCE`, `Reentrancy`, `SSRF`, not vague wording.
- Name the concrete location in the subject when known: endpoint, function, route, file, panel, or component.
- Put the highest observed consequence in the subject, not a speculative worst case.
- Keep the subject professional, information-dense, and ideally within about 60-80 characters when the facts still fit cleanly.
- Add a severity tag such as `[CRITICAL]` or `[HIGH]` only when it is evidence-backed and useful to the program.
- Use the user-specified recipient exactly. Do not rewrite or expand the address list unless the user asks.
- Keep the message readable in plain text even if the provider uses a rich-text editor.
- Prefer short paragraphs and numbered reproduction steps.
- First sentence must state the exact observed impact in plain English.
- For code-driven findings, include the vulnerable function or a short decisive snippet in the body, then explain the failing check or accounting mistake in plain English.
- Mention the decisive proof naturally: screenshots, HAR, video, replay script, or `poc.md`.
- Let `reverify.md` constrain the claim. Report what survived independent review, not the hunter's most aggressive wording.
- When the exploit is code-heavy, summarize `Output from POC` in the body before attaching or pasting the full PoC.
- Separate observed impact from reasoned extension.
- Mention prerequisites honestly. If auth, rare roles, or timing are required, say so.
- Keep remediation short and optional unless the program explicitly asks for it.
- Never use `could potentially`, `may allow`, or similar hedging for the main claim.
- Do not use emotional or adversarial subjects such as `Critical Bug Found!!!` or `I hacked your database`.
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
