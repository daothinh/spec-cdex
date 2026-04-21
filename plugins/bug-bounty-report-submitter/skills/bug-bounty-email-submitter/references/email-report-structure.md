# Email Report Structure

Write to the actual disclosure channel: an email read by a triager, not a form field parser.

## Subject

Use one line with the same core formula as `report-writing-rules.md`:

`[Target] - [Vulnerability Type] at [Location] leads to [Impact]`

Examples:
- `[api.target.com] IDOR at GET /api/v2/invoices/{id} leads to invoice data exposure`
- `[admin.target.com] Missing auth at POST /api/admin/users leads to admin account creation`
- `[Support Dashboard] Stored XSS at ticket title field leads to account takeover`

Break the subject into four technical parts:
- `Target`: domain, app name, protocol, repository, or contract name
- `Vulnerability Type`: precise technical class such as `IDOR`, `RCE`, `Reentrancy`, `SSRF`
- `Location`: endpoint, function, file, route, component, panel, or config path
- `Impact`: highest observed consequence such as `Account Takeover`, `Data Leak`, `Fund Drain`, `System Compromise`

Subject rules:
- Prefer observed impact over speculative worst case.
- Keep it professional and information-dense, not emotional.
- Avoid generic or hostile subjects such as `Critical Bug Found!!!`, `I hacked your database`, or `Serious issue in your system`.
- Keep it near 60-80 characters when possible, but do not drop decisive technical detail just to hit the limit.
- Add a severity tag like `[CRITICAL]` or `[HIGH]` only when it is supported by the actual finding and helps triage.
- If the program requires a prefix such as `[Bug Bounty]`, prepend it without changing the core structure.

## Body Order

Use this order unless the program email template requires another:

1. Greeting
2. Summary paragraph
3. Affected asset
4. Prerequisites
5. Steps to reproduce
6. Observed impact
7. Evidence and attachments
8. Optional remediation
9. Availability for follow-up

## Greeting

Keep it neutral:
- `Hello security team,`
- `Hello [program name] team,`

Avoid:
- `I would like to report...`
- `Dear Sir/Madam`

## Summary Paragraph

Keep the opening to 2-4 sentences:
- name the affected asset and entry point
- state the bug and exact practical impact in one plain sentence
- add prerequisites only if they materially change severity
- mention the decisive proof when the body length allows it

## Vulnerability Details In Email

If the bug is primarily in code, do not make the triager jump to attachments first.

- Name the vulnerable file and function in the body.
- Include the shortest decisive snippet inline when the mail client allows readable formatting.
- Use repo-relative names or GitHub links, never local absolute paths from your machine.
- Explain the exact broken assumption right below the snippet.
- If the full exploit is long, keep the full code in `poc.md` or an attachment and keep only the decisive excerpt inline.

## Steps To Reproduce

Use numbered steps. Each step should contain:
- exact role or auth state
- target URL, endpoint, or UI path
- attacker action
- observed result
- proof anchor: artifact ID, attachment name, or `poc.md`

## Observed Impact

Tie impact to what was directly shown:
- what the attacker gains
- which boundary fails
- what data or action becomes exposed
- whether the issue repeats across tenants, projects, or accounts
- quantified records, funds, or role scope when known

Keep inferred extension separate with language such as `Based on the observed behavior...`

## Evidence And Attachments

Mention proof naturally in prose:
- `Attached HAR shows the cross-tenant response.`
- `The attached video demonstrates the full replay on a fresh account.`
- `The included poc.md contains the exact request sequence.`

Attach only files that support a claim in the body.

For code-heavy findings:
- summarize `Output from POC` in the body with the most convincing logs or deltas
- then attach the full PoC or point to `poc.md`

## Optional Remediation

Keep it short and implementation-agnostic unless the program asks for more:
- validate object ownership on the server
- encode stored HTML before render
- enforce state transitions server-side

## Follow-Up Closing

End with a short follow-up note:
- `I can provide additional traces or retest a fix if useful.`

Do not pad the ending with gratitude templates or severity sales language.
