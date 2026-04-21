# Playwright Submit Flow

Use Playwright MCP to inspect the rendered form and submit without guessing field names.

## Sequence

1. `browser_navigate` to the submission URL.
2. `browser_snapshot` to map headings, labels, editors, attachments, help text, and buttons.
3. Complete login if needed, then snapshot again.
4. Expand tabs, accordions, and conditional sections before drafting.
5. Record the live schema in `form-schema.json`: label, field type, required flag, options, character limit, validation note, and attachment policy.
6. Build `submission.json` from `form-schema.json`. Draft the report only after the schema is known. If the form has a title or subject-like field, set it with the shared title formula from `report-writing-rules.md`.
7. Fill metadata fields first with `browser_fill_form` or `browser_select_option`.
8. Snapshot again if asset, severity, or classification choices reveal new prompts. Update `form-schema.json` and `submission.json` when they do.
9. Fill long-form fields with `browser_type` when editors have live validation or markdown quirks.
10. Use `browser_file_upload` only after `artifacts.json`, `poc.md`, and local evidence paths are final.
11. Save draft or preview if the platform supports it.
12. Take a final `browser_snapshot` and verify the visible content matches `submission.json`. Confirm the title or subject-like field still carries target, vuln type, location, and impact without ambiguous truncation.
13. Submit with `browser_click`, then capture the confirmation screen and report ID.

## Practical Rules

- Do not draft long-form prose before discovering required fields, custom prompts, and limits.
- Fill one logical section at a time: metadata, summary, steps, impact, evidence, attachments.
- After each major section, snapshot again so validation errors are visible.
- Watch for dynamic fields that appear after severity, category, or asset selection.
- If the platform has a short title field, compress the location before dropping the impact or vuln type.
- If the form rewrites markdown, inspect the preview and edit the field-specific text.
- If a control is hidden behind tabs or accordions, expand it first and resnapshot.
- If submission triggers a modal, capture that modal text before confirming.

## Stop Conditions

Stop and report the blocker instead of brute forcing when:
- the form requires captcha or MFA that cannot be completed in-session
- the program blocks uploads needed for proof
- the field limit forces loss of decisive evidence and no attachment path exists
- the form rejects a required value and the correct platform-specific format is unknown
- the live form requires fields that cannot be filled honestly from the verified finding
