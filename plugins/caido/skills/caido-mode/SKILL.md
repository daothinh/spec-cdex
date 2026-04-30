---
name: caido-mode
description: Use the official Caido SDK from Codex to search HTTP history, replay and edit authenticated requests, manage scopes and findings, export curl commands, and save local bug-bounty evidence. Prefer when a live request corpus already exists or auth-preserving replay is more valuable than broad scanner coverage.
metadata:
  author: workers.io
  version: "0.1.0"
---

# Caido Mode

Use this skill when the target is web or API and the highest-value next step is
to work from real captured traffic rather than rebuild requests manually.

This is the right tool when:

- you already have authenticated traffic in Caido
- cookies, CSRF tokens, or JWTs are large and annoying to reconstruct
- you want to mutate one real request repeatedly
- you need a quick curl PoC from a captured request
- you want local finding-bundle artifacts derived from Caido history

## Core Model

Treat Caido as a stateful traffic broker.

- `kage` is still better for recon, scanners, and unauthenticated surface expansion.
- `caido` is better for authenticated replay, request-corpus mining, and intercept-driven workflows.

Preferred sequence:

1. find an organic request in Caido history
2. verify it has valid auth
3. use `edit` to change only what matters
4. replay
5. export curl and local evidence when the behavior matters

## Setup

Requires:

- a running Caido instance
- a PAT
- dependencies installed in `plugins/caido/skills/caido-mode/`

Authenticate once:

```bash
npx tsx caido-client.ts setup <your-pat> http://localhost:8080
```

Auth lookup order:

1. `CAIDO_PAT` and `CAIDO_URL`
2. cached values in `~/.codex/caido/secrets.json`
3. optional override path in `CAIDO_SECRETS_PATH`

Do not store PATs in the repo tree.

## Shell Entry Points

From repo-local development:

- Unix: `plugins/caido/skills/caido-mode/scripts/caido`
- PowerShell: `plugins/caido/skills/caido-mode/scripts/caido.ps1`

Examples:

```bash
plugins/caido/skills/caido-mode/scripts/caido health
plugins/caido/skills/caido-mode/scripts/caido recent --limit 5
plugins/caido/skills/caido-mode/scripts/caido search 'req.path.cont:"/api/"' --limit 10
```

## High-Value Commands

### 1. Search history

```bash
npx tsx caido-client.ts search 'req.method.eq:"POST" AND resp.code.eq:200'
npx tsx caido-client.ts search 'req.path.cont:"/admin"' --ids-only
```

### 2. Edit while preserving auth

Use `edit` before rebuilding a request from scratch.

```bash
npx tsx caido-client.ts edit 123 --path /api/users/999
npx tsx caido-client.ts edit 123 --method POST --body '{"role":"admin"}'
npx tsx caido-client.ts edit 123 --set-header "X-Forwarded-For: 127.0.0.1"
npx tsx caido-client.ts edit 123 --remove-header "X-CSRF-Token"
npx tsx caido-client.ts edit 123 --replace 'user123:::user999'
```

### 3. Replay and export PoC

```bash
npx tsx caido-client.ts replay 123 --compact
npx tsx caido-client.ts export-curl 123
```

### 4. Local evidence export

When a request matters for a finding bundle, save local artifacts:

```bash
npx tsx caido-client.ts export-evidence 123 --out audit-targets/acme/findings/F001/artifacts/caido
```

This writes:

- request metadata JSON
- curl command
- formatted response raw when available
- optional raw request when `--include-request-raw` is used

### 5. Sync a local bundle into Caido Findings

```bash
npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --request-id 123
npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --finding-id 77
```

Use this for operator convenience only. Local finding bundles stay the reporting source of truth.

## Request-History Workflow

Recommended workflow for auth-heavy web/API hunting:

1. `health`
2. `recent --limit 5`
3. `search <httpql>` to locate a seed request
4. `edit <id> ...` for each hypothesis
5. `export-curl <id>` or `export-evidence <id> --out <dir>` when a result becomes relevant
6. `create-finding` or `sync-finding` only after the behavior is concrete enough to keep

## HTTPQL Rules

Critical reminders:

- string values must be quoted
- integer values are not quoted
- `NOT` does not exist
- use negated operators instead:
  - `ne`
  - `ncont`
  - `nlike`
  - `nregex`

Examples:

```text
req.method.eq:"POST" AND resp.code.eq:200
req.path.regex:"/(login|auth|oauth)/"
resp.len.gt:100000
req.path.ncont:"/static"
source:"replay" OR source:"automate"
```

## Bug Bounty Pipeline Rules

When this skill is used inside the repo's web/API bounty pipeline:

- prefer `kage` for recon and broad surface discovery
- prefer `caido` for authenticated mutation and replay
- keep request IDs, session IDs, and exported curl paths in `prep/asset-inventory.md`
- save decisive artifacts under the local finding bundle
- do not let the Caido UI become the only place where evidence exists

## Testing

Local helper tests:

```bash
npm test
```

Live E2E checks, when a Caido instance is available:

```bash
npx tsx caido-client.ts health
npx tsx caido-client.ts recent --limit 1
```
