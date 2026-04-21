# Email Report Structure

Write to the actual disclosure channel: an email read by a triager, not a form field parser.

## Subject

Use one line:

`[bug class] in [asset] allows [impact]`

Examples:
- `IDOR in invoice export API allows cross-tenant PDF access`
- `Stored XSS in support portal allows agent-session theft`

If the program requires a prefix such as `[Bug Bounty]` or a program name, prepend it without changing the core structure.

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
- state the bug in one plain sentence
- state the practical impact
- add prerequisites only if they materially change severity

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

Keep inferred extension separate with language such as `Based on the observed behavior...`

## Evidence And Attachments

Mention proof naturally in prose:
- `Attached HAR shows the cross-tenant response.`
- `The attached video demonstrates the full replay on a fresh account.`
- `The included poc.md contains the exact request sequence.`

Attach only files that support a claim in the body.

## Optional Remediation

Keep it short and implementation-agnostic unless the program asks for more:
- validate object ownership on the server
- encode stored HTML before render
- enforce state transitions server-side

## Follow-Up Closing

End with a short follow-up note:
- `I can provide additional traces or retest a fix if useful.`

Do not pad the ending with gratitude templates or severity sales language.
