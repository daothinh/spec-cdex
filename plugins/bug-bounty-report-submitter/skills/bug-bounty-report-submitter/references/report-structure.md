# Report Structure

Start from `form-schema.json`, then write only the content the live form actually asks for.

## Before Drafting

- Read the live labels, help text, validators, and limits from `form-schema.json`.
- Build `submission.json` from those fields first.
- Treat `artifacts.json` and `poc.md` as required inputs, not optional extras.
- For Web3 or exchange targets, also treat chain or environment identifiers, contract or account IDs, tx hashes, order IDs, and role prerequisites as required facts.

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

Strong pattern from live Critical Immunefi reports:
- `The bug is in the internal function _claimable(..) of RevenueHandler. Here's the relevant part:`
- code snippet
- GitHub line link
- plain-English explanation of the faulty loop, missing check, or accounting error

Do not wait until the PoC section to show the vulnerable code if the bug is primarily in code.

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

- Put every uploadable proof file in `evidence/`.
- Track each proof item in `artifacts.json`: ID, filename, description, and which claim it supports.
- Use `poc.md` for replay steps, requests, payloads, or code that would be noisy inside the form.
- Mention attachments naturally: `Attached HAR shows the cross-tenant response.` Avoid dumping raw filenames without context.
- When the exploit is code-heavy, add an `Output from POC` block before the full PoC if the platform supports headings or separate fields.
- `Output from POC` should show the shortest decisive evidence: balances, logs, tx deltas, claim amounts, changed state, or assertion results.
- After the output block, include the runnable PoC or point to `poc.md`.

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
| Severity | program scale plus evidence-backed rationale only |
| Severity rationale | brief justification tied to observed impact, prerequisites, and proof |
| CVSS | vector and score when the form asks for it |
| Prerequisites | auth state, role, race window, or special setup |
| Summary | first paragraph |
| Steps to reproduce | numbered list |
| Impact | dedicated impact section |
| PoC / evidence | attachment summary plus `poc.md` when needed |
| Remediation | short fix guidance |
| Attachments | screenshots, logs, HAR, video, PoC |
| Chain / contract / tx / market | verified Web3 or exchange identifiers when the form provides dedicated fields |

If the platform adds custom fields, source them from `form-schema.json` and store the final mapping in `submission.json`.
