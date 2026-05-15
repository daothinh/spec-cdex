---
name: bug-bounty-report-submitter
description: >
  Inspect live bug bounty forms with Playwright MCP, then draft and submit
  evidence-backed reports that match the platform fields, proof requirements,
  and attachment flow.
metadata:
  author: workers.io
  version: "0.5.0"
---

# Bug Bounty Report Submitter

Inspect the live submission form first, then turn independently re-verified findings into an evidence-backed report bundle and submit it through Playwright MCP.

Load these on demand:
- [references/report-writing-rules.md](references/report-writing-rules.md) for impact-first report rules, title guidance, severity discipline, and the final checklist
- [references/report-structure.md](references/report-structure.md) for field mapping and section order
- [references/immunefi-body-template.md](references/immunefi-body-template.md) for the evidence-first local drafting scaffold and content order
- [references/writing-style.md](references/writing-style.md) for natural prose rules and anti-template cleanup
- [references/external-proof-pack.md](references/external-proof-pack.md) for secret-gist and field-limit handling without offloading the core claim
- [references/asciinema-proof.md](references/asciinema-proof.md) for the mandatory final replay recording flow and link placement
- [references/playwright-submit.md](references/playwright-submit.md) for the browser automation sequence
- `plugins/bounty-hunting-programs/skills/bounty-program-triage/SKILL.md` if target scope or program constraints are still unclear

Optional helper:

- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_web3_report_bundle.py --finding-dir <finding-dir> --bundle-dir <bundle-dir>`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_report_artifacts.py --finding-dir <finding-dir> --bundle-dir <bundle-dir>`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/record_asciinema_replay.py --finding-dir <finding-dir> --workdir <target-dir> --run-command "<cmd>" --success-signal "<signal>"`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py --bundle-dir <bundle-dir> --run-command "<cmd>" --success-signal "<signal>" --publish-gist`
- `python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/validate_submission_bundle.py --bundle-dir <bundle-dir> --channel form`

## Preconditions

- Reproduce the issue end to end.
- Have an independent re-verification verdict for the finding. The closed-loop standard expects `TRUE POSITIVE` from `security-finding-reverify` before any submission work begins.
- Have `severity.md` in the finding bundle. Use it as the source of truth for Severity, CWE, CVSS, affected asset, exploit preconditions, impact reasoning, and downgrade notes.
- Know the affected asset, prerequisites, impact, and evidence set.
- Have the submission URL and any login requirements.
- Have a runnable PoC or an exact replayable actor timeline, request sequence, or transaction path for the bug.
- Have decisive PoC output, logs, assertions, tx results, or balance deltas proving the replay worked from a clean state.
- Have a final clean replay recorded with `asciinema`. Native PATH is preferred. WSL is only fallback. If both checks fail, stop immediately.
- For Web3, blockchain, or exchange findings, know the chain, contract or account identifiers, and any tx hash, block number, order ID, or session identifier that makes the proof concrete.
- Have `manual-review.md` in the finding bundle. This is the mandatory 20-minute checkpoint before submission. It should record who reviewed the claim, what mechanism or business logic was read manually, which cryptographic or domain-logic blockers were checked, and why the finding still survives.
- Do not begin submission work when the proof stops at an internal side effect such as a dangerous function call, queued payment, initiated HTLC, emitted event, or partial state transition. For financial or payment findings, the bundle must prove value realization, recipient-controlled settlement, claimed funds, balance delta, or a clearly equivalent end-state.

If any precondition is missing, gather it before submission work starts.

## Local Bundle

Create `bug-bounty-reports/<slug>/<finding-id>/` and keep:
- `facts.md` - raw, verified facts only
- `facts-chain.md` - optional chain, market, tx, block, and contract identifiers for web3 or exchange findings
- `impact.md` - observed impact and reasoned extension kept separate
- `impact-financials.md` - optional asset delta, attack capital, and solvency or settlement impact for web3 or exchange findings
- `severity.md` - severity level, CWE, CVSS when applicable, affected asset, preconditions, impact reasoning, and downgrade notes
- `manual-review.md` - human checkpoint recording the 20-minute domain-logic review and blockers checked before disclosure
- `environment.md` - optional fork, staging, testnet, or static-only replay assumptions
- `form-schema.json` - live form fields, options, limits, and notes
- `artifacts.json` - evidence inventory with stable IDs and file paths
- `poc.md` - replayable exploit or reproduction details
- `report-appendix.md` - optional markdown appendix used only when the platform requires an attachment or the field limits cannot honestly hold the full detail body
- `reverify.md` - independent re-verification verdict and blockers already checked
- `report.md` - final prose draft
- `submission.json` - field-to-value map for the form
- `submission.json.external_proof` - required proof-reference contract when `external-evidence.json` exists
- `external-evidence.json` - required secret-gist pointer for the detailed PoC, helper files, and raw logs
- `evidence/asciinema/asciinema-session.json` - mandatory replay-recording metadata with the uploaded `asciinema` URL
- `evidence/asciinema/reverify-session.cast` - mandatory local terminal replay recording
- `web3-facts.json` - optional normalized chain-aware facts for web3-heavy findings
- `asset-delta.md` - optional observed fund movement or market-state change summary
- `reproduction-matrix.md` - optional prerequisite and replay matrix for web3-heavy findings
- `proof-pack/` - optional gist-ready runnable PoC pack with appendix, logs, helper files, and manifest
- `evidence/` - screenshots, HAR, video, logs, payloads, PoC files
- `confirmation.md` - final URL, report ID, screenshots, follow-up notes

## Workflow

1. Open the submission URL with Playwright MCP before drafting anything long-form.
2. Snapshot the rendered form, complete login if needed, expand hidden sections, and record required fields, custom prompts, enums, validators, character limits, and attachment rules in `form-schema.json`.
3. Normalize the proof package. Separate observed behavior from theory in `facts.md`, copy impact reasoning into `impact.md`, carry severity/CWE/CVSS from `severity.md`, inventory every artifact in `artifacts.json`, store the replayable exploit path in `poc.md`, and carry the independent verdict into `reverify.md`.
   - For Web3 or exchange bugs, record chain, network, contract address, tx hash, order ID, market pair, user role, or custody boundary as structured facts, not buried prose.
   - When web3-heavy finding files exist, preserve them as `facts-chain.md`, `impact-financials.md`, `environment.md`, `web3-facts.json`, `asset-delta.md`, and `reproduction-matrix.md` instead of flattening everything into one prose blob.
   - When the web3-heavy bundle is still raw, use `prepare_web3_report_bundle.py` to materialize `web3-facts.json`, `asset-delta.md`, and `reproduction-matrix.md` before long-form drafting.
   - Always run `prepare_report_artifacts.py` before drafting so `artifacts.json` and `evidence/` exist and local proof does not depend on source tool state. If `artifacts/caido/` exists in the finding bundle, preserve those request metadata files, curl PoCs, and response snapshots as first-class evidence entries.
   - Run `record_asciinema_replay.py` during the last clean reverify rerun so `artifacts/asciinema/` is present before `prepare_report_artifacts.py` copies the recording into `evidence/asciinema/`.
   - Treat `poc.md` as incomplete until it includes an exact run command or deterministic replay sequence plus a success signal that can be observed again.
4. Stop unless `manual-review.md` survives a sanity read. If it documents unresolved blockers, impossible cryptographic assumptions, or a failure to prove end-state impact, do not draft.
5. Build `submission.json` from `form-schema.json`, not from a fixed template. Include custom site fields exactly as discovered and precompute title, summary, severity, CVSS, and field-specific short variants from verified facts and `severity.md` only.
   - When `external-evidence.json` exists, add `submission.json.external_proof` with:
     - `required`
     - `type`
     - `url`
     - `source: "external-evidence.json"`
     - `target_field`
     - `inline_note_required`
6. Draft `report.md` from `facts.md`, `artifacts.json`, `poc.md`, `impact.md`, `reverify.md`, `severity.md`, and `manual-review.md` using [references/immunefi-body-template.md](references/immunefi-body-template.md), [references/report-structure.md](references/report-structure.md), and [references/report-writing-rules.md](references/report-writing-rules.md). Use the local scaffold only to preserve content order. Rewrite or collapse generic headings before anything reaches the live form so the submitted text reads like a target-specific analyst note, not a reusable skeleton.
7. Run the evidence, structure, style, and anti-template pass from [references/writing-style.md](references/writing-style.md) plus the checklist in [references/report-writing-rules.md](references/report-writing-rules.md). If the draft still reads like it could be pasted into a different program by changing a few nouns, rewrite it. If a claim is inferred rather than proved, move it out of the title, opening paragraph, and severity rationale. The final tone should feel careful, serious, and reviewer-friendly rather than automated or promotional. Do not proceed if the finding is still `reverify-pending`, `needs-more-evidence`, or `false-positive`.
8. Build `report-appendix.md` and `proof-pack/` with [references/external-proof-pack.md](references/external-proof-pack.md) for every report bundle. A secret gist link is mandatory because it carries the detailed PoC, helper files, the full report, and raw logs that the main form cannot hold comfortably. The final clean replay must also have an uploaded `asciinema` URL from [references/asciinema-proof.md](references/asciinema-proof.md). The inline body must still name the exact bug, exploit path, run command, decisive output, then place `[gist-url](gist-url)` and `[asciinema-url](asciinema-url)` in that order with the `asciinema` link on the next non-empty line.
9. Run `validate_submission_bundle.py --bundle-dir <bundle-dir> --channel form` after bundle prep and again immediately before submit. Treat any failure as a hard blocker.
10. Use the Playwright flow in [references/playwright-submit.md](references/playwright-submit.md) to fill the live form. Upload nothing by default. Only upload proof when the program explicitly requires an attachment or a supporting artifact cannot be represented inline without losing fidelity. When an attachment is mandatory, prefer `report-appendix.md` as the primary upload rather than raw source files. Do not add unsolicited follow-up comments, moderator notes, or large code dumps after submission unless the reviewer asks for a missing detail or the original form could not carry a decisive replay step. Submit only after the validator passes and the visible form matches `submission.json`, including the required gist reference.
11. Capture the confirmation page, report ID, and final URL in `confirmation.md`.

## Report Rules

- Lead with the bug and affected asset, not background.
- Discover the live form schema before drafting prose.
- Use the title guidance from [references/report-writing-rules.md](references/report-writing-rules.md) when the form has a title-like field.
- Keep the title technical and professional. Use target, exact vuln names, concrete locations, and the highest observed impact.
- First sentence must state the practical impact in plain English, not background or jargon.
- The opening summary or intro must include the secret gist URL and the `asciinema` URL so the triager can immediately open the full PoC pack and recorded replay if needed.
- Keep the logic order `summary -> exact bug location -> root cause -> exploit path -> observed impact -> decisive PoC output -> minimal replay`, but do not force those exact phrases as literal headings in the submitted text.
- Prefer short paragraphs and numbered reproduction steps.
- For smart contract or code-heavy bugs, make `Vulnerability Details` code-first: show the vulnerable function or exact snippet immediately, then explain why that code path fails.
- When the bug is code-driven, include file path plus repo or GitHub line reference whenever it exists.
- The detail body must answer three questions without making the triager open a full attachment first: where the bug is, why the code or path is wrong, and how to replay the exploit.
- If a coded PoC exists, the body must show an exact run command or deterministic replay sequence plus the shortest decisive success signal before it points to any appendix, attachment, or gist.
- Format both external URLs as markdown links whose visible text exactly matches the URL.
- Treat headings such as `Brief/Intro`, `Vulnerability Details`, `Impact Details`, `Output from POC`, and `Proof of Concept` as local drafting aids only. In the final submission, prefer the platform's labels or tighter target-specific headings such as the exact function, endpoint, or failure mode.
- Show the exploit function, test case, or request sequence that triggers the bug. Do not paste the whole file unless the program explicitly requires it.
- The report body is the primary source of truth. Do not offload core bug details, exploit reasoning, or replay steps to attachments.
- Tie impact to the program context: auth bypass, account takeover, data exposure, privilege gain, funds risk, or availability.
- When the bug is on-chain or exchange-related, separate observed fund movement, permission gain, or market-state change from the larger blast radius you infer.
- Never equate a dangerous function call, queued invoice, initiated payment attempt, emitted event, or other internal side effect with user-visible impact.
- For wallet, payment, Lightning, bridge, escrow, and exchange findings, prove the attacker can reach the cash-out or settlement step. If a preimage, signature, keeper, relayer, or liquidity dependency is not attacker-controlled, state that and do not overclaim.
- State prerequisites honestly. If auth, timing, or rare roles are required, say so.
- Use two identities when claiming an authorization boundary failure unless the boundary is visible without that setup.
- Mention observed result before expected result.
- Keep observed impact separate from reasoned extension.
- Fill severity and CVSS only when the program asks or the field exists. Source them from `severity.md`; recalculate only when the platform requires a different format or verified evidence changed.
- Reference evidence naturally in the text or attachment notes; do not leave important claims unsupported.
- Mention the PoC when it is needed to replay the issue or understand exploitability.
- `Output from POC` or its field-equivalent must appear before the full PoC whenever a PoC exists.
- Use the independent re-verification verdict to sharpen the report claim, not to pad it with generic certainty language.
- Prefer an `Output from POC` or equivalent evidence block before the full PoC when logs, balances, tx results, or assertions make the impact obvious faster than code alone.
- If the issue is primarily a documented-behavior mismatch, fallback break, or availability-only failure, name the exact broken action in the title and opening paragraph instead of forcing stronger exploit labels than the reproduced effect supports.
- If a coded PoC is impossible, state exactly why and replace it with a replayable actor timeline, transaction sequence, or state-machine walkthrough.
- Do not attach raw source files, exploit scripts, full test suites, archives, or random code dumps by default.
- If the platform requires a file upload or the field limit makes a fully honest report impossible inline, attach `report-appendix.md` with the same self-contained detail structure instead of a raw `.sol`, `.py`, `.js`, `.t.sol`, or archive file whenever the platform accepts markdown or plain text.
- If the channel supports external reference URLs and the full runnable PoC needs multiple files or long logs, create `proof-pack/` and reference the resulting secret gist naturally in the summary/intro plus the evidence field or inline note. The body must still stand alone without that link.
- Supporting artifacts such as screenshots, HAR, video, or logs may be uploaded only as evidence supplements. They must never be the only place where the triager can learn the core bug mechanics.
- Caido exports such as request metadata JSON, curl PoCs, or formatted responses count as supporting artifacts, not replacements for a self-contained body. Use them to anchor `artifacts.json`, not to offload the core claim.
- Follow-up comments are off by default. Post one only when it adds missing, reviewer-relevant delta. Never paste a large code block into comments just to restate the body in a different format.
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
- If the form has a dedicated evidence URL, reference URL, or supplemental notes field, use it for a secret-gist proof pack only after the inline body already contains the minimal runnable replay.
- Before final submit, confirm the visible title still matches the target, vuln type, location, and impact formula and was not truncated into ambiguity.
- If a field strips markdown or truncates text, rewrite for that field instead of forcing the template.
- If the platform supports drafts, save one before final submit.
- If a captcha or MFA gate blocks submission, stop after the draft and report the blocker.
- If the platform has dedicated fields for chain, contract, transaction, asset, market, or environment, fill them from verified facts instead of repeating a generic summary.
- If the platform has dedicated CWE, CVSS, or severity fields, fill them from `severity.md` and document any required format conversion in `submission.json`.

## Output

Return:
- report title
- submission URL
- confirmation ID or blocker
- saved `artifacts.json` and `evidence/` paths
- saved `form-schema.json` and `submission.json` paths
- saved local bundle path
- any manual follow-up the user still needs
