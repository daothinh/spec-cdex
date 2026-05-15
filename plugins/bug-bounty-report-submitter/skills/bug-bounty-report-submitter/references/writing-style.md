# Writing Style

Write after discovering the live form. Make the report read like a specific analyst note, not a bulk template.

## Core Rules

- Write to the actual field label and size limit from `form-schema.json`.
- Write from concrete evidence: exact asset names, roles, endpoints, and observed behavior.
- Anchor every major claim to an artifact in `artifacts.json` or mark it as an explicit assumption.
- Put the exact practical impact in the first sentence.
- Put the secret gist URL in the opening summary or intro when a gist-backed proof pack exists.
- Put the `asciinema` URL on the next non-empty line below the gist URL.
- Format both URLs as markdown links whose visible text matches the URL.
- Keep sentences direct. Prefer one claim per sentence.
- Use short paragraphs. Break long explanations into steps or evidence bullets.
- Vary the opening sentence so it reflects the actual bug, not a canned intro.
- Use platform labels or target-specific headings. Remove generic scaffolding headings when they do not help the reviewer.
- Prefer plain verbs: `returns`, `accepts`, `renders`, `bypasses`, `exposes`.
- Keep observed impact separate from inferred extension.
- Keep the content order from `immunefi-body-template.md`, but rewrite or collapse the section names before the final submission.
- Make the body feel like a triager-ready whitehat note: exact bug location first, exploit path second, proof third.
- Inline only the smallest decisive snippet or request. Put helpers and boilerplate elsewhere.
- If you mention a function, route, component, or handler, explain why that exact location is the bug carrier.
- Treat attachments as supplemental evidence, not as the main explanation.
- If the report still makes sense only because the attachment exists, the body is not finished yet.
- If a proof pack or secret gist exists, describe it as supplemental storage for the long PoC, logs, or helper files, not as the place where the triager first learns the exploit.
- Mention the gist early enough that a triager can open it immediately, but never make the gist carry the first explanation of the bug.
- Do not add unsolicited post-submit comments that restate the report with more code unless the reviewer asked for that delta.

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
- Mention replay links naturally: `[https://gist.github.com/...](https://gist.github.com/...)` then `[https://asciinema.org/a/...](https://asciinema.org/a/...)`
- If a separate evidence field exists, keep the summary concise and move proof inventory there.
- If the PoC is decisive, say so plainly and summarize the decisive output inline before mentioning any supplemental artifact.
- Do not fake certainty by citing proof that does not exist in `artifacts.json`.

## Anti-Template Pass

Before finalizing `report.md`, check:
1. Does the first paragraph mention the exact asset and bug class?
2. Does sentence 1 state the actual observed impact in plain English?
3. Does the opening summary or intro include the secret gist URL when a proof pack exists?
4. Is the `asciinema` URL on the next non-empty line below the gist URL?
5. Does every major claim map to an artifact or `poc.md`?
6. Does the body explicitly name the vulnerable function, endpoint, or component?
7. Is the broken assumption explained directly below the decisive snippet or request?
8. Is the exploit function or replay path shown without dumping the whole file?
9. Does the body include the exact run command or deterministic replay sequence plus the success signal?
10. Does `Output from POC` prove the impact before the full PoC body?
11. Would the report still be fully understandable if every attachment or gist link were removed? If no, move the missing explanation into the body.
12. Are reproduction steps specific enough to replay without guessing?
13. Did generic or speculative phrases survive from a prior report or template?
14. Was the text rewritten for the actual field label and length?
15. Would the report still make sense if the program name were removed? If yes, add more target-specific detail.
16. Could the headings be copied into a different report unchanged? If yes, rename or remove them.
17. Is any planned follow-up comment adding new reviewer-needed evidence, or only reformatting the same proof? If it is only reformatting, delete it.

## Tone

- Stay calm and factual.
- Sound deliberate and respectful so the report creates immediate reviewer confidence.
- Do not pad severity with dramatic language.
- Do not hide constraints that reduce impact.
- Do not claim certainty where only partial proof exists.
- Do not use `could potentially`, `may allow`, or similar hedging for the main claim.
- If a platform field is short, compress the prose for that field instead of pasting a full template.
- Keep local drafts more explicit than the submitted field when the site is too small; store the full proof path in `artifacts.json` and `poc.md`.
