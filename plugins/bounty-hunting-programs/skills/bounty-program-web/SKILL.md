---
name: bounty-program-web
description: >
  Standard bug bounty workflow for web and API targets across JavaScript and
  TypeScript, Python, Ruby, PHP, Java, Go, and .NET frameworks. Use when
  reviewing routes, controllers, auth layers, admin panels, background jobs,
  webhooks, or multi-tenant application logic.
---

# Bounty Program Web

Use this workflow for monoliths, APIs, admin portals, and service backends.

Load these references on demand:
- `../../references/bounty-standard.md`
- `../../references/codex-ready-building-blocks.md`
- `../../references/web-framework-matrix.md`
- `../../references/report-checklist.md`

## Inputs

- Test accounts or seed data if available
- Any `.burp` project, API collection, or captured request corpus
- Scope restrictions for rate limits, data mutation, or production assets

## Workflow

1. Detect the server stack and read the matching row in `web-framework-matrix.md`.
2. Map the attack surface:
   - routes and handlers
   - auth and session middleware
   - admin or internal-only flows
   - file upload and storage paths
   - webhook consumers
   - background jobs and replayable tasks
3. Reuse Codex-ready building blocks when installed:
   - `audit-context-building` for deep route and trust-boundary comprehension
   - `sharp-edges` for language and framework risk patterns
   - `insecure-defaults` for debug, auth, CORS, storage, or deployment defaults
   - `supply-chain-risk-auditor` for dependency exposure
   - `burpsuite-project-parser` if a Burp project is already available
   - `agentic-actions-auditor` when CI, GitHub Actions, or agent-driven release flows touch the target
4. Prioritize bug classes in this order:
   - broken object-level authorization and tenant isolation
   - internal-only route exposure and admin flag bypasses
   - webhook trust, replay, and background job abuse
   - SSRF, file upload, archive extraction, and path traversal
   - deserialization, template injection, and dangerous helper execution
   - dangerous defaults in auth, storage, and debug configuration
5. After the first confirmed issue, use `variant-analysis` to search for siblings.
6. If the root cause can be codified, write a reusable rule with `semgrep-rule-creator` and generalize it with `semgrep-rule-variant-creator`.

## Lane-Specific Notes

- For Next.js or other hybrid stacks, treat server actions, middleware, and internal fetch helpers as first-class attack surface.
- For Python and Ruby stacks, scrutinize background jobs and serializer/model trust, not just controllers.
- For Go and .NET, pay attention to middleware order and path normalization before assuming auth is correct.
- For Java or Spring, verify method-level security and actuator-style operational endpoints early.

## Exit Criteria

- You can name the exact handler, middleware gap, or state transition that fails.
- Reproduction shows attacker-controlled reachability.
- Impact is framed in terms of account, tenant, or admin boundary breakage.
