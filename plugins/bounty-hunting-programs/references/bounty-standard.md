# Standard Bounty Flow

Use this flow across every target class in this plugin.

## 1. Intake

- Capture the program rules, explicit out-of-scope assets, rate-limit guidance, and whether test accounts are permitted.
- Identify what evidence is acceptable: screenshots, request/response pairs, transaction traces, crash logs, or invariant violations.
- Record anything that constrains testing: production-only assets, no-destructive-testing language, prohibited spam, or financial-loss limits.

## 2. Fingerprint

- Detect the primary language and framework before hunting.
- Mark where trust enters the system: routes, RPC handlers, job workers, webhook consumers, deeplinks, on-chain entry points, file parsers.
- Identify privileged actors and secrets boundaries.

## 3. Attack Surface Map

- Enumerate reachable entry points.
- Note state-changing paths, admin-only flows, and background execution paths.
- Find code that bridges trusted and untrusted data.

## 4. Focused Review

- Start with the most target-specific skill or companion plugin available.
- Prefer deep context before exploit reasoning when the architecture is unfamiliar.
- Keep a running list of assumptions that still need proof.

## 5. Exploitability Check

- Prove the bug with the smallest safe reproduction.
- Show why a normal user or attacker can reach the vulnerable state.
- Keep evidence concise: requests, parameters, traces, or minimal PoC steps.

## 6. Variant Expansion

- Only expand after understanding the first confirmed pattern.
- Reuse `variant-analysis` or a targeted grep/rule search to find siblings.
- Group variants by root cause, not by superficial syntax.

## 7. Reporting

- Write reproducible steps.
- State prerequisites clearly.
- Separate assumptions from confirmed facts.
- Include impact in terms the program owner will accept.
