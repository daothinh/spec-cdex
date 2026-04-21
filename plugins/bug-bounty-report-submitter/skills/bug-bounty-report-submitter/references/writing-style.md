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

## Good Patterns

- `The billing export endpoint returns another tenant's PDF when the invoice_id is changed.`
- `A low-privilege project member can approve pending invites by replaying the admin workflow request.`
- `The stored payload executes in the agent dashboard when the ticket thread is reopened.`
- `Attached HAR and the included replay steps in poc.md reproduce the issue on a fresh account.`

## Remove These Patterns

- `I would like to report...`
- `A malicious actor could potentially...`
- `This may allow...`
- `This could be used to...`
- `Please find below...`
- `This critical vulnerability can completely compromise...`
- generic filler such as `due to improper validation` without naming the missed check

## Evidence Mentions

- Mention proof naturally: `The attached video shows...`, `The included HAR captures...`
- If a separate evidence field exists, keep the summary concise and move proof inventory there.
- If the PoC is decisive, say so plainly and point to `poc.md` or the uploaded file.
- Do not fake certainty by citing proof that does not exist in `artifacts.json`.

## Anti-Template Pass

Before finalizing `report.md`, check:
1. Does the first paragraph mention the exact asset and bug class?
2. Does sentence 1 state the actual observed impact in plain English?
3. Does every major claim map to an artifact or `poc.md`?
4. Are reproduction steps specific enough to replay without guessing?
5. Did generic or speculative phrases survive from a prior report or template?
6. Was the text rewritten for the actual field label and length?
7. Would the report still make sense if the program name were removed? If yes, add more target-specific detail.

## Tone

- Stay calm and factual.
- Do not pad severity with dramatic language.
- Do not hide constraints that reduce impact.
- Do not claim certainty where only partial proof exists.
- Do not use `could potentially`, `may allow`, or similar hedging for the main claim.
- If a platform field is short, compress the prose for that field instead of pasting a full template.
- Keep local drafts more explicit than the submitted field when the site is too small; store the full proof path in `artifacts.json` and `poc.md`.
