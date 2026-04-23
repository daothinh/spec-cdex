# Report Structure

Start from `form-schema.json`, then write only the content the live form actually asks for.

## Before Drafting

- Read the live labels, help text, validators, and limits from `form-schema.json`.
- Build `submission.json` from those fields first.
- Treat `artifacts.json`, `poc.md`, `impact.md`, and `severity.md` as required inputs, not optional extras.
- Treat attachments as optional by default, not part of the primary report payload.
- For Web3 or exchange targets, also treat chain or environment identifiers, contract or account IDs, tx hashes, order IDs, and role prerequisites as required facts.
- Draft the full local body with [immunefi-body-template.md](immunefi-body-template.md) before compressing or splitting it for platform-specific fields.

## Long-Form Detail Body

Use the shared order from [immunefi-body-template.md](immunefi-body-template.md):

1. `Brief/Intro`
2. `Vulnerability Details`
3. `The Vulnerable Function` or `Affected Endpoint` or `Affected Component`
4. `Why The Check Fails` or `Root Cause`
5. `Attack Vector Explained` or `Exploit Walkthrough`
6. `Impact Details`
7. `Output from POC`
8. `Proof of Concept`

This is the default skeleton even when the live form later forces the content into smaller buckets.

## Title

Default formula from `report-writing-rules.md`:

`[Target] - [Vulnerability Type] at [Location] leads to [Impact]`

Examples:
- `[api.target.com] IDOR at GET /api/v2/invoices/{id} leads to invoice data exposure`
- `[admin.target.com] Missing auth at POST /api/admin/users leads to admin account creation`
- `[target.com] SSRF at image import URL handler leads to AWS metadata access`

Build the title from four technical parts:
- `Target`: domain, app name, protocol, repository, or contract name
- `Vulnerability Type`: precise class such as `IDOR`, `RCE`, `Reentrancy`, `SSRF`
- `Location`: endpoint, function, route, file, component, panel, or config path
- `Impact`: highest observed consequence such as `Account Takeover`, `Data Leak`, `Fund Drain`, `System Compromise`

Title rules:
- Prefer observed impact over speculative worst case.
- Keep it professional and information-dense, not emotional.
- Avoid generic titles such as `Critical issue in your app` or `Serious bug found`.
- Keep it near 60-80 characters when the facts still fit cleanly, but keep the decisive technical detail if tradeoffs are required.
- If the form title field is very short, preserve target, vuln type, and impact first, then compress the location.
- If the platform has no dedicated title field, reuse this structure in the nearest summary or subject-like field.

## Summary Paragraph

Keep the first paragraph to 2-4 sentences:
1. Name the affected asset and entry point.
2. State the bug and exact impact in plain English.
3. Add the prerequisite only if it materially changes severity.
4. Point to the decisive proof when the field length allows it.

If the form has separate summary and impact fields, keep the summary factual and move consequence detail to impact.

## Vulnerability Details

For code-driven bugs, use this order:

1. One sentence naming the vulnerable file, function, or endpoint.
2. The smallest decisive code snippet.
3. A repo or GitHub line link when available. Never use a local absolute filesystem path in the report body.
4. One short paragraph explaining the exact broken assumption.
5. If needed, one extra snippet for the downstream effect or call chain.

This is strong enough for the triager to answer:
- where the bug lives
- why the code or path is wrong
- which exact lines or branch matter

Strong pattern from live Critical Immunefi reports:
- name the exact function or handler
- show the decisive snippet
- give the repo link
- explain the faulty loop, missing check, bad comparison, or accounting mistake in plain English

Do not wait until the PoC section to show the vulnerable code if the bug is primarily in code.

If the bug is not code-driven, replace the snippet with the smallest decisive request, state transition, or UI fragment that carries the same explanatory weight.

## Attack Vector Explained

After showing the vulnerable function or endpoint, walk the triager through the exploit path:

1. setup or attacker identity
2. trigger of the vulnerable path
3. critical incorrect state change or computation
4. observed result

Use actor names when a boundary matters:
- `Account A` and `Account B`
- `Attacker` and `Victim`
- named smart-contract actors when a scenario is easier to read that way

## Reproduction Steps

Use numbered steps. Each step should contain:
- exact role or auth state
- target URL, endpoint, or UI path
- attacker action
- observed result
- proof anchor: artifact ID, attachment name, or `poc.md` reference

Put payloads, IDs, headers, and toggles inline when short. Use attachments for long traces.

## Impact

Tie impact to the program, not to abstract worst-case language.

Prefer:
- what the attacker gains
- which boundary fails
- what data or action becomes exposed
- whether the issue is repeatable across tenants, projects, or accounts
- what was directly observed versus what is inferred from the observed behavior
- quantified funds, records, or role scope when known

Avoid:
- generic "could lead to complete compromise" claims
- remediation text inside the impact field

## Evidence And PoC

- Keep every local proof file in `evidence/`, but upload only the smallest necessary subset.
- Track each proof item in `artifacts.json`: ID, filename, description, and which claim it supports.
- Use `poc.md` for replay steps, requests, payloads, or code that would be noisy inside the form.
- Mention attachments naturally only when they are truly needed: `Attached HAR shows the cross-tenant response.` Avoid dumping raw filenames without context.
- When the exploit is code-heavy, add an `Output from POC` block before the full PoC if the platform supports headings or separate fields.
- `Output from POC` should show the shortest decisive evidence: balances, logs, tx deltas, claim amounts, changed state, or assertion results.
- After the output block, include the minimal runnable PoC excerpt inline. Keep `poc.md` as a local drafting artifact, not as something the submitted report depends on.
- Show the exploit function, test case, or request sequence, not the whole helper file.
- If a full helper file is needed for local replay, keep it in `poc.md` or `evidence/` and keep only the decisive excerpt in the body.
- If a coded PoC is impossible, say why and replace it with a replayable actor timeline or transaction sequence.
- Do not upload raw source files or archives by default.
- If the platform requires a file upload or the field length makes the report incomplete, create `report-appendix.md` and upload that markdown appendix before considering any raw code file.
- Even when `report-appendix.md` is uploaded, the main report fields must still contain the full bug narrative, root cause, exploit path, and decisive PoC output.

## Web3 / Exchange Proof Details

When applicable, surface the identifiers that make the issue replayable:

- chain and network
- contract or wallet address
- transaction hash and block number
- market, pool, vault, or order identifiers
- user role or auth prerequisite
- observed token or balance delta

Keep observed state change separate from inferred total blast radius. Example: "Observed unauthorized withdrawal of 0.5 ETH from vault X in tx Y" is stronger than "all TVL is at risk" unless the broader claim is also proved.

## Remediation

Keep remediation short and implementation-agnostic unless the program asks for detail:
- validate object ownership on the server
- encode stored HTML before render
- enforce state transitions server-side

## Common Field Map

| Form field | Source |
| --- | --- |
| Title | final title line |
| Scope / asset | hostname, app, endpoint, package, or contract |
| Severity | `severity.md` mapped to the program scale |
| Severity rationale | brief justification from `severity.md`, adjusted only when the form forces a different format |
| CVSS | vector and score from `severity.md` when the form asks for it |
| Prerequisites | auth state, role, race window, or special setup |
| Summary | first paragraph |
| Steps to reproduce | numbered list |
| Impact | dedicated impact section |
| PoC / evidence | inline `Output from POC` plus inline exploit excerpt, with supplemental attachment notes only when needed |
| Remediation | short fix guidance |
| Attachments | optional supporting screenshots, logs, HAR, video, or `report-appendix.md` when the platform requires a file |
| Chain / contract / tx / market | verified Web3 or exchange identifiers when the form provides dedicated fields |

If the platform adds custom fields, source them from `form-schema.json` and store the final mapping in `submission.json`.
