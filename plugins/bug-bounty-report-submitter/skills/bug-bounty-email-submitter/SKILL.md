---
name: bug-bounty-email-submitter
description: >
  Draft and send evidence-backed bug bounty report emails through a live webmail
  UI with Playwright MCP, using the user-specified recipient and verified proof.
metadata:
  author: workers.io
  version: "0.5.0"
---

# Bug Bounty Email Submitter

Draft the report bundle first, then open the sender mailbox in a browser and send from the live webmail UI with Playwright MCP.

Load these on demand:
- [shared report-writing rules](../bug-bounty-report-submitter/references/report-writing-rules.md) for impact-first claims, title discipline, severity guidance, and final checklist
- [shared Immunefi-style body template](../bug-bounty-report-submitter/references/immunefi-body-template.md) for the default long-form detail skeleton
- [shared external proof pack reference](../bug-bounty-report-submitter/references/external-proof-pack.md) for secret-gist and field-limit handling
- [shared asciinema replay reference](../bug-bounty-report-submitter/references/asciinema-proof.md) for the mandatory final replay recording and link placement
- [references/email-report-structure.md](references/email-report-structure.md) for subject and body layout
- [references/playwright-email-submit.md](references/playwright-email-submit.md) for the inbox and compose flow
- [shared writing-style reference](../bug-bounty-report-submitter/references/writing-style.md) for the natural-prose cleanup pass
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` if target scope or disclosure constraints are still unclear

Optional helper:

- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_web3_report_bundle.py --finding-dir <finding-dir> --bundle-dir <bundle-dir>`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_report_artifacts.py --finding-dir <finding-dir> --bundle-dir <bundle-dir>`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/record_asciinema_replay.py --finding-dir <finding-dir> --workdir <target-dir> --run-command "<cmd>" --success-signal "<signal>"`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py --bundle-dir <bundle-dir> --run-command "<cmd>" --success-signal "<signal>" --publish-gist`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/validate_submission_bundle.py --bundle-dir <bundle-dir> --channel email`

## Preconditions

- Reproduce the issue end to end.
- Have an independent re-verification verdict for the finding. The closed-loop standard expects `TRUE POSITIVE` from `security-finding-reverify` before any email disclosure work begins.
- Have `severity.md` in the finding bundle. Use it as the source of truth for severity labels, CWE, CVSS when applicable, affected asset, preconditions, impact reasoning, and downgrade notes.
- Know the affected asset, prerequisites, impact, and evidence set.
- Have the recipient email address supplied by the user.
- Have the sender mailbox URL and any login requirements.
- Have `manual-review.md` in the finding bundle.
- Have a runnable PoC or deterministic replay sequence plus decisive output in screenshots, HAR, logs, requests, or a PoC file.
- Have a final clean replay recorded with `asciinema`. Native PATH is preferred. WSL is only fallback. If both checks fail, stop immediately.

If any precondition is missing, gather it before email work starts.

## Local Bundle

Create `bug-bounty-reports/<slug>/<finding-id>/` and keep:
- `facts.md` - raw verified facts only
- `facts-chain.md` - optional chain, market, tx, block, and contract identifiers for web3 or exchange findings
- `impact.md` - observed impact and reasoned extension kept separate
- `impact-financials.md` - optional asset delta, attack capital, and solvency or settlement impact for web3 or exchange findings
- `severity.md` - severity level, CWE, CVSS when applicable, affected asset, preconditions, impact reasoning, and downgrade notes
- `manual-review.md` - human checkpoint recording the manual domain review and blockers checked before disclosure
- `environment.md` - optional fork, staging, testnet, or static-only replay assumptions
- `artifacts.json` - evidence inventory with stable IDs and file paths
- `poc.md` - replayable exploit or reproduction details
- `report-appendix.md` - optional markdown appendix used only when the email program explicitly requires an attachment or the provider makes the full detail body impossible inline
- `reverify.md` - independent re-verification verdict and blockers already checked
- `external-evidence.json` - required secret-gist pointer for the detailed PoC, helper files, and raw logs
- `evidence/asciinema/asciinema-session.json` - mandatory replay-recording metadata with the uploaded `asciinema` URL
- `evidence/asciinema/reverify-session.cast` - mandatory local terminal replay recording
- `mail-ui-schema.json` - live compose controls, attachment flow, and send confirmation signals
- `mail-envelope.json` - `to`, optional `cc` and `bcc`, subject, and attachment plan
- `mail-envelope.json.external_proof` - required proof-reference contract when `external-evidence.json` exists
- `email-draft.md` - final subject and body draft
- `web3-facts.json` - optional normalized chain-aware facts for web3-heavy findings
- `asset-delta.md` - optional observed fund movement or market-state change summary
- `reproduction-matrix.md` - optional prerequisite and replay matrix for web3-heavy findings
- `proof-pack/` - optional gist-ready runnable PoC pack with appendix, logs, helper files, and manifest
- `confirmation.md` - sent time, recipient, provider confirmation, screenshot path, follow-up notes
- `evidence/` - screenshots, HAR, video, logs, payloads, PoC files

## Workflow

1. Confirm the recipient address, sender mailbox URL, and whether the program wants plain text, markdown-like formatting, or a strict disclosure template.
2. Open the mailbox with Playwright MCP before drafting anything long-form. Snapshot the inbox, login flow, compose button, editor type, attachment control, draft affordance, and success indicator. Store the observed UI contract in `mail-ui-schema.json`.
3. Normalize the proof package. Separate observed behavior from theory in `facts.md`, copy impact reasoning into `impact.md`, carry severity/CWE/CVSS from `severity.md`, inventory every artifact in `artifacts.json`, store the replayable exploit path in `poc.md`, and carry the independent verdict into `reverify.md`. Run `record_asciinema_replay.py` during the last clean reverify rerun, then run `prepare_report_artifacts.py` so the email proof does not depend on source tool state.
4. When web3-heavy finding files exist, preserve them as `facts-chain.md`, `impact-financials.md`, `environment.md`, `web3-facts.json`, `asset-delta.md`, and `reproduction-matrix.md` instead of flattening everything into one prose blob.
   - When the web3-heavy bundle is still raw, use `prepare_web3_report_bundle.py` to materialize `web3-facts.json`, `asset-delta.md`, and `reproduction-matrix.md` before drafting the email body.
5. Stop unless `manual-review.md` survives a sanity read. If it records unresolved blockers, impossible assumptions, or missing end-state proof, do not send.
6. Build `mail-envelope.json` from the verified recipient, `severity.md`, and the discovered mailbox behavior. Do not invent `cc`, `bcc`, reply-to, or tracking settings.
   - When `external-evidence.json` exists, add `mail-envelope.json.external_proof` with:
     - `required`
     - `type`
     - `url`
     - `source: "external-evidence.json"`
     - `target_field`
     - `inline_note_required`
7. Draft `email-draft.md` from `facts.md`, `artifacts.json`, `poc.md`, `impact.md`, `reverify.md`, `severity.md`, and `manual-review.md` using [references/email-report-structure.md](references/email-report-structure.md), the [shared Immunefi-style body template](../bug-bounty-report-submitter/references/immunefi-body-template.md), and the [shared report-writing rules](../bug-bounty-report-submitter/references/report-writing-rules.md). Build the subject from target, exact vuln type, location, and max observed impact.
8. Run the cleanup pass from the [shared writing-style reference](../bug-bounty-report-submitter/references/writing-style.md) plus the checklist in the [shared report-writing rules](../bug-bounty-report-submitter/references/report-writing-rules.md). Every major claim must map to an artifact or be marked as an explicit assumption. The body must still show the vulnerable function or endpoint, exploit path, exact run command or replay sequence, `Output from POC`, and exploit excerpt even in plain text. The final tone should feel careful, serious, and reviewer-friendly rather than automated or promotional. Do not proceed if the finding is still `reverify-pending`, `needs-more-evidence`, or `false-positive`.
9. Create `report-appendix.md` and build `proof-pack/` with the shared external-proof-pack workflow for every disclosure bundle. A secret gist link is mandatory because it carries the detailed PoC, helper files, the full report, and raw logs. The final clean replay must also have an uploaded `asciinema` URL. The email body must place `[gist-url](gist-url)` and `[asciinema-url](asciinema-url)` in that order, with the `asciinema` link on the next non-empty line starting in the opening summary or intro paragraph.
10. Run `validate_submission_bundle.py --bundle-dir <bundle-dir> --channel email` after bundle prep and again immediately before send. Treat any failure as a hard blocker.
11. Use the Playwright flow in [references/playwright-email-submit.md](references/playwright-email-submit.md) to open a fresh compose window, set the `To` field to the user-specified address, fill the subject and body from `mail-envelope.json` and `email-draft.md`, and save a draft when the provider supports it. Do not attach files by default. If an attachment is genuinely required, prefer `report-appendix.md` instead of raw source files.
12. Take a final snapshot, verify the visible recipient, subject, body, and attachments match the local bundle, including the required gist reference, then send. Capture the provider confirmation, sent-folder URL if available, and any message ID in `confirmation.md`.

## Email Rules

- Lead with the bug and affected asset, not generic disclosure filler.
- Prefer the shared formula from `report-writing-rules.md`: `[Target] - [Vulnerability Type] at [Location] leads to [Impact]`.
- Use `severity.md` for any severity tag, CWE, or CVSS value. Recalculate only when the recipient explicitly requires a different format.
- Use precise technical names in the subject: `IDOR`, `RCE`, `Reentrancy`, `SSRF`, not vague wording.
- Name the concrete location in the subject when known: endpoint, function, route, file, panel, or component.
- Put the highest observed consequence in the subject, not a speculative worst case.
- Keep the subject professional, information-dense, and ideally within about 60-80 characters when the facts still fit cleanly.
- Add a severity tag such as `[CRITICAL]` or `[HIGH]` only when it is evidence-backed and useful to the program.
- Use the user-specified recipient exactly. Do not rewrite or expand the address list unless the user asks.
- Keep the message readable in plain text even if the provider uses a rich-text editor.
- Prefer short paragraphs and numbered reproduction steps.
- First sentence must state the exact observed impact in plain English.
- The opening summary or intro must include the secret gist URL so the triager can immediately review the full PoC pack, logs, and report.
- The body should mirror the shared Immunefi-style order as closely as the email format allows: `Brief/Intro -> Vulnerability Details -> The Vulnerable Function or Affected Endpoint -> Why The Check Fails -> Attack Vector Explained -> Impact Details -> Output from POC -> Proof of Concept`.
- For code-driven findings, include the vulnerable function or a short decisive snippet in the body, then explain the failing check or accounting mistake in plain English.
- Show the exploit function, test case, or request sequence that triggers the issue. Do not paste the whole file unless the program explicitly asks for it.
- The email body is the primary disclosure artifact. Do not push the main explanation into an attached file.
- Mention the decisive proof naturally: screenshots, HAR, video, replay script, or `poc.md`.
- Let `reverify.md` constrain the claim. Report what survived independent review, not the hunter's most aggressive wording.
- When the exploit is code-heavy, summarize `Output from POC` in the body before attaching or pasting the full PoC.
- If a coded PoC is impossible, say exactly why and replace it with a replayable actor timeline, transaction sequence, or state walkthrough.
- Do not attach raw source files, exploit scripts, or archives by default.
- If an attachment is mandatory, attach `report-appendix.md` or another markdown/plain-text appendix that restates the full detail body instead of relying on a raw code file.
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
