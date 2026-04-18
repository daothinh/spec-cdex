# Reporting Checklist

Use this checklist before concluding a finding.

## Required Fields

- Target and exact affected component
- Bug class
- Preconditions and attacker model
- Step-by-step reproduction
- Minimal evidence
- Impact statement
- Why existing controls fail

## Evidence Examples

- Request/response pair with identifiers redacted only when safe
- Transaction trace or state diff
- Decompiled APK path plus runtime confirmation
- Crash log plus minimized input
- Code reference that shows the trust-boundary break

## Quality Bar

- Reproduction is deterministic or the source of nondeterminism is called out.
- Every assumption is labeled as an assumption.
- Impact avoids hype and matches the actual control failure.
- Variants are grouped under one root cause when appropriate.
