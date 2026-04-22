---
name: bug-bounty-report-submitter
description: >
  Inspect live bug bounty forms with Playwright MCP, then draft and submit
  evidence-backed reports that match the platform fields, proof requirements,
  and attachment flow.
metadata:
  author: workers.io
  version: "0.2.1"
---

# Bug Bounty Report Submitter

Inspect the live submission form first, then turn independently re-verified findings into an evidence-backed report bundle and submit it through Playwright MCP.

Load these on demand:
- [references/report-writing-rules.md](references/report-writing-rules.md) for impact-first report rules, title formula, severity discipline, and final checklist
- [references/report-structure.md](references/report-structure.md) for field mapping and section order
- [references/immunefi-body-template.md](references/immunefi-body-template.md) for the default long-form body skeleton based on recurring accepted Immunefi report patterns
- [references/writing-style.md](references/writing-style.md) for natural prose rules and anti-template cleanup
- [references/playwright-submit.md](references/playwright-submit.md) for the browser automation sequence
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` if target scope or program constraints are still unclear

## Preconditions

- Reproduce the issue end to end.
- Have an independent re-verification verdict for the finding. The closed-loop standard expects `TRUE POSITIVE` from `security-finding-reverify` before any submission work begins.
- Know the affected asset, prerequisites, impact, and evidence set.
- Have the submission URL and any login requirements.
- Have a minimal PoC or replayable proof path for the bug.
- For Web3, blockchain, or exchange findings, know the chain, contract or account identifiers, and any tx hash, block number, order ID, or session identifier that makes the proof concrete.

If any precondition is missing, gather it before submission work starts.

## Local Bundle

Create `bug-bounty-reports/<slug>/` and keep:
- `facts.md` - raw, verified facts only
- `form-schema.json` - live form fields, options, limits, and notes
- `artifacts.json` - evidence inventory with stable IDs and file paths
- `poc.md` - replayable exploit or reproduction details
- `report-appendix.md` - optional markdown appendix used only when the platform requires an attachment or the field limits cannot honestly hold the full detail body
- `reverify.md` - independent re-verification verdict and blockers already checked
- `report.md` - final prose draft
- `submission.json` - field-to-value map for the form
- `evidence/` - screenshots, HAR, video, logs, payloads, PoC files
- `confirmation.md` - final URL, report ID, screenshots, follow-up notes

## Workflow

1. Open the submission URL with Playwright MCP before drafting anything long-form.
2. Snapshot the rendered form, complete login if needed, expand hidden sections, and record required fields, custom prompts, enums, validators, character limits, and attachment rules in `form-schema.json`.
3. Normalize the proof package. Separate observed behavior from theory in `facts.md`, inventory every artifact in `artifacts.json`, store the replayable exploit path in `poc.md`, and carry the independent verdict into `reverify.md`.
   - For Web3 or exchange bugs, record chain, network, contract address, tx hash, order ID, market pair, user role, or custody boundary as structured facts, not buried prose.
4. Build `submission.json` from `form-schema.json`, not from a fixed template. Include custom site fields exactly as discovered and precompute title, summary, severity, CVSS, and field-specific short variants from verified facts only.
5. Draft `report.md` from `facts.md`, `artifacts.json`, `poc.md`, and `reverify.md` using [references/immunefi-body-template.md](references/immunefi-body-template.md), [references/report-structure.md](references/report-structure.md), and [references/report-writing-rules.md](references/report-writing-rules.md). Draft the full detail body locally even if the live platform later splits it across several smaller fields.
6. Run the evidence, structure, and style pass from [references/writing-style.md](references/writing-style.md) plus the checklist in [references/report-writing-rules.md](references/report-writing-rules.md). If the local draft does not clearly show the vulnerable function, exact broken code or path, exploit walkthrough, and PoC output in the expected order, fix it before any submission work. If a claim is inferred rather than proved, move it out of the title, opening paragraph, and severity rationale. Do not proceed if the finding is still `reverify-pending`, `needs-more-evidence`, or `false-positive`.
7. Use the Playwright flow in [references/playwright-submit.md](references/playwright-submit.md) to fill the live form. Upload nothing by default. Only upload proof when the program explicitly requires an attachment or a supporting artifact cannot be represented inline without losing fidelity. When an attachment is mandatory, prefer `report-appendix.md` as the primary upload rather than raw source files. Submit only after the visible form matches `submission.json`.
8. Capture the confirmation page, report ID, and final URL in `confirmation.md`.

## Report Rules

- Lead with the bug and affected asset, not background.
- Discover the live form schema before drafting prose.
- Use the title formula from [references/report-writing-rules.md](references/report-writing-rules.md) when the form has a title-like field.
- Keep the title technical and professional. Use target, exact vuln names, concrete locations, and the highest observed impact.
- First sentence must state the practical impact in plain English, not background or jargon.
- The default body order is `Brief/Intro -> Vulnerability Details -> The Vulnerable Function or Affected Endpoint -> Why The Check Fails -> Attack Vector Explained -> Impact Details -> Output from POC -> Proof of Concept`.
- Prefer short paragraphs and numbered reproduction steps.
- For smart contract or code-heavy bugs, make `Vulnerability Details` code-first: show the vulnerable function or exact snippet immediately, then explain why that code path fails.
- When the bug is code-driven, include file path plus repo or GitHub line reference whenever it exists.
- The detail body must answer three questions without making the triager open a full attachment first: where the bug is, why the code or path is wrong, and how to replay the exploit.
- Show the exploit function, test case, or request sequence that triggers the bug. Do not paste the whole file unless the program explicitly requires it.
- The report body is the primary source of truth. Do not offload core bug details, exploit reasoning, or replay steps to attachments.
- Tie impact to the program context: auth bypass, account takeover, data exposure, privilege gain, funds risk, or availability.
- When the bug is on-chain or exchange-related, separate observed fund movement, permission gain, or market-state change from the larger blast radius you infer.
- State prerequisites honestly. If auth, timing, or rare roles are required, say so.
- Use two identities when claiming an authorization boundary failure unless the boundary is visible without that setup.
- Mention observed result before expected result.
- Keep observed impact separate from reasoned extension.
- Fill severity and CVSS only when the program asks or the field exists, and keep both evidence-backed.
- Reference evidence naturally in the text or attachment notes; do not leave important claims unsupported.
- Mention the PoC when it is needed to replay the issue or understand exploitability.
- `Output from POC` or its field-equivalent must appear before the full PoC whenever a PoC exists.
- Use the independent re-verification verdict to sharpen the report claim, not to pad it with generic certainty language.
- Prefer an `Output from POC` or equivalent evidence block before the full PoC when logs, balances, tx results, or assertions make the impact obvious faster than code alone.
- If a coded PoC is impossible, state exactly why and replace it with a replayable actor timeline, transaction sequence, or state-machine walkthrough.
- Do not attach raw source files, exploit scripts, full test suites, archives, or random code dumps by default.
- If the platform requires a file upload or the field limit makes a fully honest report impossible inline, attach `report-appendix.md` with the same self-contained detail structure instead of a raw `.sol`, `.py`, `.js`, `.t.sol`, or archive file whenever the platform accepts markdown or plain text.
- Supporting artifacts such as screenshots, HAR, video, or logs may be uploaded only as evidence supplements. They must never be the only place where the triager can learn the core bug mechanics.
- Never inflate severity with generic breach language.
- Never use `could potentially`, `may allow`, or similar hedging for the main claim.
- Never invent screenshots, logs, identifiers, or attachments.
- Rewrite for the actual field label and limit, not a mail-merge template.

## Form-Fill Rules

- Use `browser_snapshot` before any drafting, before the first fill, and after each major section.
- Fill metadata fields first because severity or asset choices may reveal extra required prompts. That includes the report title when the form has one.
- Prefer `browser_fill_form` for standard controls and `browser_type` for editors with live validation.
- Update `form-schema.json` if hidden or dynamic fields appear after a selection.
- Use `browser_file_upload` only after `submission.json`, `artifacts.json`, and local artifact paths are final.
- Before final submit, confirm the visible title still matches the target, vuln type, location, and impact formula and was not truncated into ambiguity.
- If a field strips markdown or truncates text, rewrite for that field instead of forcing the template.
- If the platform supports drafts, save one before final submit.
- If a captcha or MFA gate blocks submission, stop after the draft and report the blocker.
- If the platform has dedicated fields for chain, contract, transaction, asset, market, or environment, fill them from verified facts instead of repeating a generic summary.

## Output

Return:
- report title
- submission URL
- confirmation ID or blocker
- saved `form-schema.json` and `submission.json` paths
- saved local bundle path
- any manual follow-up the user still needs
