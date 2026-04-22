# Writing Style

Write after discovering the live form. Make the report read like a specific analyst note, not a bulk template.

## Core Rules

- Write to the actual field label and size limit from `form-schema.json`.
- Write from concrete evidence: exact asset names, roles, endpoints, and observed behavior.
- Anchor every major claim to an artifact in `artifacts.json` or mark it as an explicit assumption.
- Put the exact practical impact in the first sentence.
- Keep sentences direct. Prefer one claim per sentence.
- Use short paragraphs. Break long explanations into steps or evidence bullets.
- Vary the opening sentence so it reflects the actual bug, not a canned intro.
- Prefer plain verbs: `returns`, `accepts`, `renders`, `bypasses`, `exposes`.
- Keep observed impact separate from inferred extension.
- Default to the section names and order from `immunefi-body-template.md` unless the live form forces something smaller.
- Make the body feel like a triager-ready whitehat note: exact bug location first, exploit path second, proof third.
- Inline only the smallest decisive snippet or request. Put helpers and boilerplate elsewhere.
- If you mention a function, route, component, or handler, explain why that exact location is the bug carrier.
- Treat attachments as supplemental evidence, not as the main explanation.
- If the report still makes sense only because the attachment exists, the body is not finished yet.

## Good Patterns

- `The billing export endpoint returns another tenant's PDF when the invoice_id is changed.`
- `A low-privilege project member can approve pending invites by replaying the admin workflow request.`
- `The stored payload executes in the agent dashboard when the ticket thread is reopened.`
- `The attached HAR is supplemental, and the replay steps below reproduce the issue on a fresh account.`
- `The bug is in [function or handler]. The snippet below uses [wrong state/check/comparison], which lets the attacker [observed result].`
- `The PoC output below shows [balance delta / changed role / leaked record] before the full exploit code.`
- `The attached HAR is supplemental; the exact request and failing authorization check are reproduced below.`

## Remove These Patterns

- `I would like to report...`
- `A malicious actor could potentially...`
- `This may allow...`
- `This could be used to...`
- `Please find below...`
- `This critical vulnerability can completely compromise...`
- generic filler such as `due to improper validation` without naming the missed check
- `See attached code for details` without first naming the vulnerable function or endpoint
- full source-file dumps when a 10-30 line excerpt would prove the point
- generic exploit narration that never shows the exact request, function, or state transition
- body text that depends on an uploaded `.sol`, `.py`, `.js`, `.zip`, or test file to explain the actual bug

## Evidence Mentions

- Mention proof naturally: `The attached video shows...`, `The included HAR captures...`
- If a separate evidence field exists, keep the summary concise and move proof inventory there.
- If the PoC is decisive, say so plainly and summarize the decisive output inline before mentioning any supplemental artifact.
- Do not fake certainty by citing proof that does not exist in `artifacts.json`.

## Anti-Template Pass

Before finalizing `report.md`, check:
1. Does the first paragraph mention the exact asset and bug class?
2. Does sentence 1 state the actual observed impact in plain English?
3. Does every major claim map to an artifact or `poc.md`?
4. Does the body explicitly name the vulnerable function, endpoint, or component?
5. Is the broken assumption explained directly below the decisive snippet or request?
6. Is the exploit function or replay path shown without dumping the whole file?
7. Does `Output from POC` prove the impact before the full PoC body?
8. Would the report still be fully understandable if every attachment were removed? If no, move the missing explanation into the body.
9. Are reproduction steps specific enough to replay without guessing?
10. Did generic or speculative phrases survive from a prior report or template?
11. Was the text rewritten for the actual field label and length?
12. Would the report still make sense if the program name were removed? If yes, add more target-specific detail.

## Tone

- Stay calm and factual.
- Do not pad severity with dramatic language.
- Do not hide constraints that reduce impact.
- Do not claim certainty where only partial proof exists.
- Do not use `could potentially`, `may allow`, or similar hedging for the main claim.
- If a platform field is short, compress the prose for that field instead of pasting a full template.
- Keep local drafts more explicit than the submitted field when the site is too small; store the full proof path in `artifacts.json` and `poc.md`.
