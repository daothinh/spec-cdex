# Playwright Submit Flow

Use Playwright MCP to inspect the rendered form and submit without guessing field names.

## Sequence

1. `browser_navigate` to the submission URL.
2. `browser_snapshot` to map headings, labels, editors, attachments, help text, and buttons.
3. Complete login if needed, then snapshot again.
4. Expand tabs, accordions, and conditional sections before drafting.
5. Record the live schema in `form-schema.json`: label, field type, required flag, options, character limit, validation note, and attachment policy.
6. Build `submission.json` from `form-schema.json`. Draft the report only after the schema is known. Draft the long-form body with `immunefi-body-template.md` first, then split or compress it for the discovered fields. If the form has a title or subject-like field, set it with the shared title formula from `report-writing-rules.md`.
7. Fill metadata fields first with `browser_fill_form` or `browser_select_option`.
8. Snapshot again if asset, severity, or classification choices reveal new prompts. Update `form-schema.json` and `submission.json` when they do.
9. Fill long-form fields with `browser_type` when editors have live validation or markdown quirks.
10. Ensure `report-appendix.md`, `proof-pack/`, and the secret gist already exist before the final fill pass. The gist URL is mandatory and must appear in the report body, starting in the summary or intro, plus the intended reference field or inline note.
11. Run `validate_submission_bundle.py --bundle-dir <bundle-dir> --channel form` before any final submit attempt. Treat a failing validator as a hard blocker, not a warning.
12. Use `browser_file_upload` only after confirming the platform actually needs an attachment. If a file is required, prefer `report-appendix.md` first and upload raw source files only as a last resort.
13. Save draft or preview if the platform supports it.
14. Take a final `browser_snapshot` and verify the visible content matches `submission.json`. Confirm the title or subject-like field still carries target, vuln type, location, and impact without ambiguous truncation.
15. Verify the intended URL field or inline note is visibly populated with the expected gist URL before submit, and confirm the visible summary or intro also carries that gist link.
16. Submit with `browser_click`, then capture the confirmation screen and report ID.

## Practical Rules

- Do not draft long-form prose before discovering required fields, custom prompts, and limits.
- Fill one logical section at a time: metadata, summary, vulnerability details, exploit path, impact, evidence, attachments.
- After each major section, snapshot again so validation errors are visible.
- Watch for dynamic fields that appear after severity, category, or asset selection.
- If the platform has a short title field, compress the location before dropping the impact or vuln type.
- If the platform has one long rich-text field, preserve the shared heading order from `immunefi-body-template.md`.
- If the platform splits fields, keep the vulnerable function or endpoint details and exploit walkthrough together in the most relevant detail field instead of scattering them randomly.
- Never let field compression delete the run command, deterministic replay sequence, or decisive PoC output block.
- Never let the last-mile UI state omit the required gist reference.
- Do not upload files just because an upload control exists.
- If the platform requires an attachment, upload a markdown appendix that repeats the essential bug details instead of outsourcing them to a raw code file.
- If the form rewrites markdown, inspect the preview and edit the field-specific text.
- If a control is hidden behind tabs or accordions, expand it first and resnapshot.
- If submission triggers a modal, capture that modal text before confirming.

## Stop Conditions

Stop and report the blocker instead of brute forcing when:
- the form requires captcha or MFA that cannot be completed in-session
- the program blocks uploads needed for proof
- the field limit forces loss of the runnable replay or decisive evidence and no attachment path or honest external-reference path exists
- the form rejects a required value and the correct platform-specific format is unknown
- the live form requires fields that cannot be filled honestly from the verified finding
