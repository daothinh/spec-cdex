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
- Any Caido project context, request IDs, HTTPQL filters, or authenticated replay notes
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
   - `caido` when authenticated request replay or traffic-corpus mining will be faster than rebuilding requests manually
   - `agentic-actions-auditor` when CI, GitHub Actions, or agent-driven release flows touch the target
4. When Caido context exists, run the Caido-backed branch before hand-rebuilding requests:
   - load `prep/caido-plan.md` if the target came from `bounty-target-bootstrap`
   - run `health`, `auth-status`, `projects`, and `recent` to verify corpus readiness
   - create or verify target-specific scopes, filters, and environments for roles, tenants, object IDs, and workflow variables
   - use `search` to find authenticated seed requests, then `edit` and `replay` for boundary hypotheses
   - organize promising seeds with replay sessions or collections when multiple variants are needed
   - save decisive requests with `export-evidence --out <finding>/artifacts/caido`
   - record request IDs, session IDs, filter names, exported curl paths, and evidence paths in `prep/asset-inventory.md`
5. Prioritize bug classes in this order:
   - broken object-level authorization and tenant isolation
   - internal-only route exposure and admin flag bypasses
   - webhook trust, replay, and background job abuse
   - SSRF, file upload, archive extraction, and path traversal
   - deserialization, template injection, and dangerous helper execution
   - dangerous defaults in auth, storage, and debug configuration
6. After the first confirmed issue, use `variant-analysis` to search for siblings.
7. If the root cause can be codified, write a reusable rule with `semgrep-rule-creator` and generalize it with `semgrep-rule-variant-creator`.

## Lane-Specific Notes

- If you already have a logged-in request in Caido, prefer `edit` over hand-rebuilding cookies, CSRF tokens, and auth headers.
- Use `kage` for recon and breadth. Use `caido` for authenticated mutation, replay-heavy flows, and quick curl PoCs.
- Save decisive Caido request IDs, replay session IDs, filter presets, `export-curl` output paths, and `export-evidence` directories in the local finding bundle.
- Use `sync-finding` only for operator visibility. Local finding bundles remain authoritative for reverify and report submission.
- For Next.js or other hybrid stacks, treat server actions, middleware, and internal fetch helpers as first-class attack surface.
- For Python and Ruby stacks, scrutinize background jobs and serializer/model trust, not just controllers.
- For Go and .NET, pay attention to middleware order and path normalization before assuming auth is correct.
- For Java or Spring, verify method-level security and actuator-style operational endpoints early.

## Exit Criteria

- You can name the exact handler, middleware gap, or state transition that fails.
- Reproduction shows attacker-controlled reachability.
- Impact is framed in terms of account, tenant, or admin boundary breakage.
