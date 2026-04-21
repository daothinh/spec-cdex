# Report Structure

Start from `form-schema.json`, then write only the content the live form actually asks for.

## Before Drafting

- Read the live labels, help text, validators, and limits from `form-schema.json`.
- Build `submission.json` from those fields first.
- Treat `artifacts.json` and `poc.md` as required inputs, not optional extras.

## Title

Use this shape:

`[bug class] in [asset] allows [actor] to [impact]`

Examples:
- `IDOR in invoice download endpoint allows tenant data disclosure`
- `Stored XSS in support ticket body allows session theft for agents`

## Summary Paragraph

Keep the first paragraph to 2-4 sentences:
1. Name the affected asset and entry point.
2. State the bug in one plain sentence.
3. State the practical impact.
4. Add the prerequisite only if it materially changes severity.

If the form has separate summary and impact fields, keep the summary factual and move consequence detail to impact.

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

Avoid:
- generic "could lead to complete compromise" claims
- remediation text inside the impact field

## Evidence And PoC

- Put every uploadable proof file in `evidence/`.
- Track each proof item in `artifacts.json`: ID, filename, description, and which claim it supports.
- Use `poc.md` for replay steps, requests, payloads, or code that would be noisy inside the form.
- Mention attachments naturally: `Attached HAR shows the cross-tenant response.` Avoid dumping raw filenames without context.

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
| Severity | program scale plus evidence-backed rationale |
| Severity rationale | brief justification tied to observed impact and proof |
| Prerequisites | auth state, role, race window, or special setup |
| Summary | first paragraph |
| Steps to reproduce | numbered list |
| Impact | dedicated impact section |
| PoC / evidence | attachment summary plus `poc.md` when needed |
| Remediation | short fix guidance |
| Attachments | screenshots, logs, HAR, video, PoC |

If the platform adds custom fields, source them from `form-schema.json` and store the final mapping in `submission.json`.
