# Evidence-First Detail Body Planning Template

The filename is kept for compatibility, but this document is a local planning aid, not a literal heading set to paste into every form.

Use it to preserve content order for `report.md`, `email-draft.md`, or any single rich-text detail field. The winning pattern is still: name the exact vulnerable location early, show the smallest decisive code or request fragment, explain the broken assumption, then prove the impact with PoC output before dumping the full exploit.

If the live platform splits the report into multiple fields, keep this logic order locally and then map each block into the closest field in `submission.json`.

If the live platform gives you one long free-text field, do not blindly paste all of these headings. Collapse or rename them into platform-native or target-specific prose.

The report body must remain self-contained. Attachments can support the report, but they must not carry the core explanation of where the bug is, why it works, or how to replay it.

## Required content order

1. `Brief/Intro`
2. `Vulnerability Details`
3. `The Vulnerable Function` or `Affected Endpoint` or `Affected Component`
4. `Why The Check Fails` or `Root Cause`
5. `Attack Vector Explained` or `Exploit Walkthrough`
6. `Impact Details`
7. `Output from POC`
8. `Proof of Concept`

Optional sections:
- `References`
- `Recommendation`
- `Environment / Setup`

The content order matters. The literal heading words do not.

## What each section must do

### Brief/Intro

- 1 to 3 sentences only.
- Name the affected asset and the practical bug immediately.
- State the highest observed impact in plain English.
- Mention any prerequisite only if it materially lowers or changes severity.

### Vulnerability Details

- Describe the vulnerable workflow before narrating the exploit.
- Explain the broken invariant, missing check, stale state, wrong assumption, or accounting error.
- Keep this section technical and causal, not dramatic.

### The Vulnerable Function / Affected Endpoint / Affected Component

This section is mandatory for code-driven findings.

- Name the exact file and function, route handler, method, component, or contract entry point.
- Include the smallest decisive snippet only. Elide unrelated lines with `...`.
- Add a repo-relative location or GitHub line link whenever available.
- Never paste a whole file.
- Never paste a raw local filesystem path from your workstation.

If the bug is not source-code driven, replace this section with the most concrete execution point you do have:
- exact endpoint and request parameters
- exact UI component and state transition
- exact message type, queue consumer, cron, or webhook handler

### Why The Check Fails / Root Cause

- Explain why the exact snippet or branch is wrong.
- Tie the bug to one broken assumption at a time.
- If multiple snippets are needed, show a short call chain instead of a giant dump.

### Attack Vector Explained / Exploit Walkthrough

- Use numbered steps or short labeled phases.
- Name the attacker identity, role, or setup.
- Show how the attacker reaches the vulnerable state and turns it into impact.
- Include the critical state transition, request, call, or transaction.
- For auth bugs, use two actors when the boundary is between users.

### Impact Details

- State what the attacker gains now.
- Separate observed impact from broader inferred blast radius.
- Quantify funds, records, roles, pools, tenants, or tokens when known.
- Do not mix remediation into this section.

### Output from POC

This section is mandatory whenever a PoC exists.

- Show the shortest decisive output first: balances, logs, assertions, changed role, returned secret, tx delta, or state diff.
- Make the impact obvious without forcing the triager to read the exploit code first.
- If the PoC is a test, include the exact run command when it materially helps replay.

### Proof of Concept

- Include only the exploit function, test case, request sequence, or script fragment needed to replay the bug.
- Do not paste the entire file unless the live platform explicitly requires it.
- If supporting helpers exist, name them briefly and keep the decisive logic inline.
- If the exploit spans multiple functions, show only the call chain that makes the bug reproducible.

## Attachment policy

- Do not rely on attachments as the primary carrier of bug details.
- Do not write `see attached file` instead of explaining the bug inline.
- Do not attach raw exploit source files, full test suites, zip archives, or unrelated helper code by default.
- If the platform forces an attachment or the field limit prevents an honest inline explanation, generate `report-appendix.md` and keep it self-contained with the same section order used in the main report.
- If the platform still cannot hold the full runnable PoC, keep the minimal replay command or sequence plus decisive output inline, and move the longer helper files or logs into `proof-pack/` or a markdown appendix.
- Supporting screenshots, HAR files, videos, and logs are allowed only as supplements to claims already explained in the body.

## Local drafting scaffold

Do not paste this verbatim into a live program. Rewrite the headings or collapse them before submission.

````md
## Brief/Intro
[Affected asset] contains [exact bug]. An attacker who controls [role or prerequisite] can [observed impact]. [Mention decisive artifact or PoC output if helpful.]

## Vulnerability Details
[Explain the vulnerable workflow and the invariant/check/accounting assumption that should hold.]

## The Vulnerable Function
File: `[path/to/file.ext]`
Function / handler: `[name]`
Reference: `[repo or GitHub link]`

```[language]
[Smallest decisive snippet with unrelated lines replaced by ...]
```

## Why The Check Fails
[Explain exactly why the snippet is wrong and how the wrong state or permission propagates.]

## Attack Vector Explained
1. [Attacker setup, identity, or prerequisite]
2. [Trigger the vulnerable path]
3. [State transition or incorrect computation]
4. [Observed result]

## Impact Details
[Observed impact.]
[Optional: broader inferred blast radius, clearly labeled as inferred.]

## Output from POC
Command:
```bash
[run command]
```

Observed output:
```text
[Shortest decisive logs / assertion / balances / tx result]
```

## Proof of Concept
```[language]
[Minimal exploit function / test / replay script fragment]
```
````

Good submitted heading examples for a single long field:
- `Broken fallback in SignatureValidator._validateSessionKeyApproval`
- `Replay on commit <hash>`
- `Observed revert after setAccountFactory(address(0))`
- `Minimal Forge test`

## Channel mapping

If the platform has separate fields:

- `Summary` or `Description` field: `Brief/Intro`
- `Vulnerability Details` field: `Vulnerability Details` + `The Vulnerable Function` + `Why The Check Fails`
- `Steps to Reproduce` field: `Attack Vector Explained`
- `Impact` field: `Impact Details`
- `PoC` or `Additional Details` field: `Output from POC` + `Proof of Concept`

If the platform has only one long field, keep the same content order but use fewer, sharper headings or none at all when the report reads better without them.

## Non-negotiables

- The triager must be able to answer `where is the bug?`, `why is this code/path wrong?`, and `how exactly do I replay it?` without opening a full attachment.
- If a coded PoC exists, the body must expose the exact run command or replay sequence and the success signal, even when a gist or appendix carries the full helper files.
- Show the exploit function or request sequence, not a whole helper library or test suite.
- If you cannot provide a coded PoC, say exactly why and replace it with a replayable actor timeline, transaction sequence, or state machine walkthrough.
- Keep the report focused on one confirmed exploit path. Do not pad it with alternative theories.
- If an attachment is unavoidable, prefer a markdown appendix over raw source files.
- The final submitted text must not read like a reusable 8-section form letter. If the same headings could be copied into a different target unchanged, rewrite them.
