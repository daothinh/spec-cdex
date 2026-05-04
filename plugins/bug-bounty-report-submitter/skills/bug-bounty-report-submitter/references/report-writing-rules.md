# Report Writing Rules

Use after validation and before any submit action. Write for a tired triager: impact first, evidence only, no theory in the main claim.

## Non-Negotiables

- Never use `could potentially`, `may allow`, `could be used to`, or `appears to` for the primary claim.
- If the effect is proved, state it directly: `can read`, `can drain`, `returns`, `creates`, `executes`.
- If the broader consequence is only inferred, label it as inferred and keep it out of the main title and severity claim.
- Separate observed impact from broader blast radius.
- Do not report until the issue reproduces from a fresh state with the saved proof path.
- The report body must stand on its own. The triager should not need an attachment to understand the core bug.
- Do not confuse an internal side effect with impact. A dangerous function call, queued payment, initiated HTLC, emitted event, outbound request, or partial state transition is not enough unless it produces an attacker-observable consequence.
- For wallet, payment, Lightning, bridge, escrow, and exchange findings, prove settlement, claimability, cash-out, balance delta, or a clearly equivalent end-state. If the attacker does not control the preimage, signature, relayer, keeper, or liquidity dependency required to realize value, downgrade or block the report.
- For signature-, proof-, or preimage-based findings, name the exact signature, proof, or preimage gate the attacker satisfies. If you cannot show how the attacker obtains the required signature, witness, preimage, or approval, keep that claim out of the title, opening paragraph, and severity rationale.
- A completed `manual-review.md` is mandatory before submission. If the 20-minute manual review did not happen, the report is not ready.

## Evidence Order Is The Default

Unless the live program forces a different field layout, keep the long-form body in this logic order:

1. Summary of the exact bug and observed effect
2. Exact vulnerable location
3. Root cause
4. Exploit or replay path
5. Impact details
6. Decisive PoC output
7. Minimal PoC or replay instructions

Do not skip the vulnerable-location section for code-driven bugs. The triager should not have to hunt through the PoC to discover where the bug actually lives.
Do not force those phrases as literal headings in the submitted text when the platform does not ask for them.

## Title And Subject Formula

Preferred formulas:

- `[Target] [bug class] in [location] exposes / breaks / bypasses [observed effect]`
- `[Target] [root cause] in [location] causes [observed result]`
- `[Target] - [Vulnerability Type] at [Location] leads to [Impact]`

Good:
- `[api.target.com] IDOR at GET /api/v2/invoices/{id} leads to invoice data exposure`
- `[admin.target.com] Missing auth at POST /api/admin/users leads to admin account creation`
- `[Support Dashboard] Stored XSS at ticket title field leads to account takeover`

Channel adaptation:
- Keep the target prefix. It is part of the formula, not an optional addon.
- If the field is short, preserve target, vulnerability type, and impact before trimming the location.
- For availability-only or behavior-mismatch bugs, prefer the broken action or observed failure over inflated exploit language.

## Opening Paragraph

- Sentence 1: asset, exact bug, exact impact in plain English.
- Sentence 2: prerequisites only if they change severity.
- Sentence 3: point to decisive proof: screenshot, HAR, response body, PoC, tx, or video.

Good pattern:
- `The GET /api/users/{id}/orders endpoint does not verify resource ownership. An authenticated user can read any other user's order history and shipping details by replacing the path ID. Attached HAR and response body reproduce this with two normal accounts.`

## Code-First Body Detail

For smart contract, parser, auth logic, and other code-centric findings, do not keep `Vulnerability Details` abstract.

- Show the vulnerable function or the minimum decisive snippet immediately.
- Name the file and function before or above the snippet.
- Add a repo or GitHub line link when available.
- Never expose local absolute paths such as `C:\\...`, `/home/...`, or temp directories in the submitted report.
- After the snippet, explain exactly what the bad branch, missing check, stale variable, or accounting mistake does.
- If one snippet is not enough, show the call chain in 2-3 short snippets instead of a giant paste.
- Redact unrelated lines with `...` rather than pasting the whole file.
- Do not write `see attached PoC for details` before naming the exact function, endpoint, or component where the bug is.
- If the bug is endpoint-driven rather than source-driven, show the shortest decisive request and response pair with the same level of precision.

Good pattern:
- vulnerable snippet
- one short explanation paragraph
- `Output from POC` with balances, logs, tx result, or assertion delta
- full PoC after the impact is already obvious

## Exploit Walkthrough Rules

- Show how the exploit is performed, not just why the bug exists.
- Use numbered steps or short actor-driven phases after the vulnerable function section.
- Include the attacker setup, the trigger, the critical state change, and the observed result.
- For multi-actor bugs, use distinct identities such as `Account A` and `Account B`.
- For smart contract bugs, include the relevant actor roles, timestamps, pools, token IDs, markets, or epochs when they make the replay path unambiguous.

## Exploit Function Rules

- Include the exploit function, test case, or request sequence that actually triggers the bug.
- Do not paste the entire PoC file into the main body unless the platform explicitly requires it.
- Keep helpers and boilerplate out of the body. Put them in `poc.md` locally, not in the submitted report unless unavoidable.
- If the exploit spans multiple functions, show only the decisive chain.
- If a run command is needed to replay the test, include it near `Output from POC`.

## Attachment Discipline

- Do not default to attachments.
- Do not attach raw source files, exploit scripts, or full test suites when the same information can be expressed inline.
- Do not write `see attachment for the PoC` as a substitute for the inline exploit walkthrough.
- If the platform requires an attachment or field limits make inline detail impossible, attach a markdown appendix such as `report-appendix.md` that mirrors the same self-contained structure.
- Upload screenshots, HAR files, videos, and logs only as supporting evidence for claims already made inline.
- If an attachment is optional and adds no decisive evidence, do not upload it.

## Steps To Reproduce

- For auth bugs, use Account A and Account B, not one account testing itself.
- Include exact auth state, request or UI path, attacker action, and observed result in each step.
- Prefer copy-paste-ready requests when the channel supports them.
- Include `Expected` versus `Actual` when the field structure allows it.
- Every decisive step should map to an artifact ID, attachment, or `poc.md`.

## Impact

- State what the attacker gains now, not a worst-case story.
- Quantify records, roles, funds, or tenant scope when known.
- Say when only a free account is required.
- For Web3 and exchange bugs, include chain, contract or wallet, tx hash, block, market or pool, asset delta, and attack cost when known.
- For payment-style bugs, show the point where the attacker actually receives or can claim value, not only the function call that initiates the flow.
- For cryptographic workflows, state exactly when the proof, signature, nonce, or preimage is checked and how the attacker satisfies that gate.
- Keep total blast radius separate unless it is also proved.

## POC Evidence Order

- Put the shortest decisive proof before the full exploit code.
- If the report channel supports it, add `Output from POC` before `Proof of Concept`.
- Use logs that show impact numerically: balance before and after, claim amount, stolen funds, changed role, wrong return value, or failing assertion.
- Then include the runnable PoC, test, or replay script.
- For Forge or Foundry-style reports, include the exact run command when it matters.
- If a coded PoC is impossible, say exactly why and replace it with a replayable sequence of actors, calls, or transactions.
- The full exploit should still be a minimal excerpt in the report body, not a hand-off to an uploaded source file.

## Severity And CVSS

- Claim only the highest severity that the observed proof supports.
- If the program asks for CVSS 3.1, include the vector and one-line rationale.
- Read-only IDOR with PII is usually Medium.
- Write, delete, or reusable financial abuse is usually High.
- Admin auth bypass, full account takeover, cloud metadata SSRF, or RCE is usually Critical.
- Lower the claim when auth, rare roles, timing, or special environment are required.
- For Web3 or exchange programs, use the platform rubric first and CVSS second. Quantify funds at risk whenever possible.

## Tone

- Human tone, technical content.
- Short paragraphs and numbered steps.
- No generic filler such as `I would like to report` or `Please find below`.
- No lectures about what IDOR, XSS, or SSRF means.
- No invented screenshots, logs, identifiers, or attachments.
- No local workstation paths in prose, snippets, commands, screenshots, or attachment notes.

## Anti-Template Hygiene

- Do not ship literal headings such as `Brief/Intro`, `Vulnerability Details`, or `Impact Details` unless the platform uses those labels.
- If the report still reads well after replacing the target name, function, and identifiers with placeholders, it is too generic. Rewrite it.
- The first paragraph should carry at least two target-specific anchors: exact asset, exact function or endpoint, actor role, contract name, tx hash, market, or other concrete identifier.
- Prefer one decisive snippet and one decisive output block over multiple near-duplicate snippets or repeated narrative restatements.
- Do not post a follow-up comment that merely restates the same proof with a larger code dump. Follow-up comments should only add reviewer-requested delta.
- If the issue is a documented-behavior mismatch or scoped availability break, say that plainly instead of forcing a more dramatic vulnerability label.

## Pre-Submit Checklist

- Title follows the formula and names exact impact.
- First sentence states the bug and practical consequence.
- The detail body follows the Immunefi-style order or a platform-constrained equivalent.
- The submitted text uses platform labels or target-specific headings, not reusable scaffold headings.
- The report names the exact vulnerable function, endpoint, or component.
- Steps contain exact requests, IDs, or UI actions.
- Core proof and exploit logic are present inline, even if supporting evidence is also attached.
- Response or proof showing the bug is quoted inline or supported by a supplemental artifact.
- Vulnerable code snippet appears in `Vulnerability Details` for code-driven findings.
- The broken assumption or root cause is explained right below the decisive snippet or request.
- The exploit function or replay sequence is shown without dumping a full unrelated file.
- POC output shows the impact before the full PoC body.
- The proof does not stop at an internal side effect when the title or severity claims real exploit impact.
- Financial-impact claims prove claimability, settlement, or asset movement rather than only initiation.
- Domain-logic or cryptographic assumptions are explained explicitly instead of being hand-waved inside prose like `the attacker can then claim the funds`.
- No raw source file or archive is uploaded unless there is a documented reason it was unavoidable.
- No unsolicited follow-up comment is queued that only reformats the same proof.
- Two identities are used where an authorization boundary is claimed.
- Severity or CVSS matches the observed impact and prerequisites.
- `manual-review.md` exists and confirms the 20-minute domain-logic review happened before submission.
- Remediation is short and optional unless the program asks for it.
- No speculative verbs survived the final pass.
- The report is reproducible from the saved local bundle.
- Submitted field values match the live schema and field limits.
