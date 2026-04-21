# Playwright Email Submit Flow

Use Playwright MCP to discover the live webmail UI and send without assuming provider-specific selectors.

## Sequence

1. `browser_navigate` to the sender mailbox URL.
2. `browser_snapshot` to map login prompts, inbox state, compose trigger, and any suspicious-login gate.
3. Complete login if needed, then snapshot again.
4. Open a fresh compose window or draft, expand `Cc` and `Bcc` only when needed, and record the live UI contract in `mail-ui-schema.json`.
5. Capture the recipient field behavior: plain input, chips, autocomplete, or validation toast.
6. Capture the body editor behavior: textarea, contenteditable, markdown-like, or rich text with formatting toolbar.
7. Build `mail-envelope.json` and `email-draft.md` before filling. Do not improvise directly in the mailbox.
8. Fill the `To` field with the user-specified address and confirm the provider accepted it.
9. Fill the subject, then the body. Use `browser_type` for editors that need real keystrokes or preserve line breaks.
10. Upload attachments with `browser_file_upload` only after the evidence list is final.
11. Save a draft if the provider supports it, then snapshot the draft for verification.
12. Verify the visible recipient, subject, body, and attachments match the local bundle.
13. Send with `browser_click`, then capture the success toast, sent-folder item, message ID, or resulting URL.

## Practical Rules

- Do not assume Gmail, Outlook, or Proton selectors. Discover the rendered UI each time.
- Fill recipient and subject before the long body because some providers auto-save or warn on missing recipients.
- If the recipient field uses chips, ensure the chip is committed before moving on.
- If the body editor collapses blank lines or strips markdown, rewrite the body for that editor instead of forcing formatting.
- If attachments need time to upload, wait for the upload-complete indicator before sending.
- After each major step, snapshot again so validation or anti-abuse errors are visible.

## Stop Conditions

Stop and report the blocker instead of brute forcing when:
- the mailbox requires captcha, MFA, or suspicious-login approval that cannot be completed in-session
- the provider rejects the recipient and the correct address is unknown
- attachments needed for proof cannot be uploaded
- the provider shows a send failure and the cause is not recoverable from the live UI
- the compose view cannot be verified against `mail-envelope.json` and `email-draft.md`
