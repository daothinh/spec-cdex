---
name: caido-mode
description: Use the official Caido SDK from Codex to search HTTP history, replay and edit authenticated requests, manage scopes, filters, environments, projects, findings, intercept, automate/fuzz sessions, export curl commands, and save local bug-bounty evidence. Prefer when a live request corpus already exists or auth-preserving replay is more valuable than broad scanner coverage.
metadata:
  author: workers.io
  version: "0.2.0"
---

# Caido Mode

Use this skill when the target is web or API and the highest-value next step is
to work from real captured traffic instead of rebuilding requests by hand.

This is the right tool when:

- authenticated traffic already exists in Caido
- cookies, CSRF tokens, or JWTs are large and easy to break when copied manually
- one real request needs repeated path, method, header, or body mutation
- a quick curl PoC is needed from request history
- local finding-bundle artifacts must preserve request metadata and replay output

## Core Model

Treat Caido as a stateful traffic broker.

- `kage` is better for recon, scanners, breadth, and unauthenticated discovery.
- `caido` is better for authenticated replay, request-corpus mining, intercept-driven workflows, and workflow-heavy API abuse.

Preferred loop:

1. Find an organic request in Caido history.
2. Verify the request has current auth.
3. Use `edit` to change only what matters.
4. Replay and compare the response.
5. Export curl and local evidence when behavior matters.
6. Sync a Caido finding only as operator convenience.

## Setup

Requires:

- running Caido instance
- Caido PAT
- Node.js and dependencies installed in `plugins/caido/skills/caido-mode/`

Authenticate once:

```bash
cd plugins/caido/skills/caido-mode
npm install
npx tsx caido-client.ts setup <your-pat> http://localhost:8080
```

Auth lookup order:

1. `CAIDO_PAT` and `CAIDO_URL`
2. cached values in `~/.codex/caido/secrets.json`
3. optional override path in `CAIDO_SECRETS_PATH`

Do not store PATs in the repo tree.

## Shell Entry Points

From repo-local development:

```bash
plugins/caido/skills/caido-mode/scripts/caido health
plugins/caido/skills/caido-mode/scripts/caido recent --limit 5
plugins/caido/skills/caido-mode/scripts/caido search 'req.path.cont:"/api/"' --limit 10
```

PowerShell:

```powershell
& "$PWD/plugins/caido/skills/caido-mode/scripts/caido.ps1" health
```

## Command Surface

| Category | Commands |
| --- | --- |
| HTTP history | `search`, `recent`, `get`, `get-response`, `export-curl` |
| Edit and replay | `edit`, `replay`, `send-raw` |
| Sessions | `create-session`, `rename-session`, `replay-sessions`, `delete-sessions` |
| Collections | `replay-collections`, `create-collection`, `rename-collection`, `delete-collection` |
| Automate and fuzzing | `create-automate-session`, `fuzz` |
| Scope | `scopes`, `create-scope`, `update-scope`, `delete-scope` |
| Filter presets | `filters`, `create-filter`, `update-filter`, `delete-filter` |
| Environments | `envs`, `create-env`, `select-env`, `env-set`, `delete-env` |
| Findings | `findings`, `get-finding`, `create-finding`, `update-finding`, `sync-finding` |
| Local evidence | `export-evidence` |
| Tasks | `tasks`, `cancel-task` |
| Projects | `projects`, `select-project` |
| Hosted files | `hosted-files`, `delete-hosted-file` |
| Intercept | `intercept-status`, `intercept-enable`, `intercept-disable` |
| Info and auth | `viewer`, `plugins`, `health`, `setup`, `auth-status` |

## High-Value Workflows

### 1. Search history

```bash
npx tsx caido-client.ts search 'req.method.eq:"POST" AND resp.code.eq:200'
npx tsx caido-client.ts search 'req.path.cont:"/admin"' --ids-only
npx tsx caido-client.ts recent --limit 20
```

### 2. Edit while preserving auth

Prefer `edit` before rebuilding a request from scratch.

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

### 4. Save local evidence

When a request matters for a finding bundle:

```bash
npx tsx caido-client.ts export-evidence 123 --out audit-targets/acme/findings/F001/artifacts/caido
```

This writes request metadata JSON, curl command, response raw when available,
and optional request raw when `--include-request-raw` is used.

### 5. Sync a local bundle into Caido Findings

```bash
npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --request-id 123
npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --finding-id 77
```

Use this for operator convenience only. Local finding bundles stay the reporting
source of truth.

### 6. Prepare project, scope, filters, and variables

```bash
npx tsx caido-client.ts projects
npx tsx caido-client.ts select-project <project-id>
npx tsx caido-client.ts create-scope "Target" --allow "*.target.com,api.target.com"
npx tsx caido-client.ts create-filter "Target API 2xx" --query 'req.host.cont:"api.target.com" AND resp.code.lt:300'
npx tsx caido-client.ts create-env "IDOR-Test"
npx tsx caido-client.ts env-set <env-id> victim_id user_456
```

### 7. Organize replay and fuzzing

```bash
npx tsx caido-client.ts create-session 123
npx tsx caido-client.ts rename-session <session-id> "idor-user-profile"
npx tsx caido-client.ts create-collection "Auth Boundary Tests"
npx tsx caido-client.ts create-automate-session 123
npx tsx caido-client.ts fuzz <session-id>
```

Configure automate markers and payloads in the Caido UI before `fuzz`.

### 8. Control intercept

```bash
npx tsx caido-client.ts intercept-status
npx tsx caido-client.ts intercept-enable
npx tsx caido-client.ts intercept-disable
```

Use intercept only when the next browser action needs capture or manual
workflow shaping. Disable it before broad automation to avoid blocking traffic.

## Request-History Workflow

Recommended flow for auth-heavy web/API hunting:

1. `health`
2. `auth-status`
3. `projects` and `select-project` when multiple projects exist
4. `scopes` or `create-scope` to keep the corpus target-bound
5. `recent --limit 5`
6. `search <httpql>` to locate a seed request
7. `edit <id> ...` for each hypothesis
8. `export-curl <id>` or `export-evidence <id> --out <dir>` when a result becomes relevant
9. `create-finding` or `sync-finding` only after the behavior is concrete enough to keep

## HTTPQL Rules

Critical reminders:

- string values must be quoted
- integer values are not quoted
- `NOT` does not exist
- use negated operators instead: `ne`, `ncont`, `nlike`, `nregex`

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
- prefer `caido` for authenticated mutation, replay, and request-corpus mining
- load `prep/caido-plan.md` before live replay
- keep Caido project IDs, request IDs, replay session IDs, filter presets, exported curl paths, and evidence directories in `prep/asset-inventory.md`
- save decisive artifacts under the local finding bundle, especially `artifacts/caido/`
- use `sync-finding` only as convenience; do not let the Caido UI become the only evidence store
- if Caido, PAT, or the request corpus is unavailable, record the blocker in `prep/tried-and-ruled-out.md` before falling back to `kage` or direct tooling

## Output Control

Works with `get`, `get-response`, `replay`, `edit`, and `send-raw`.

| Flag | Default | Purpose |
| --- | --- | --- |
| `--max-body <n>` | `200` | Max response body lines; `0` means unlimited |
| `--max-body-chars <n>` | `5000` | Max response body characters; `0` means unlimited |
| `--no-request` | off | Skip request raw in output |
| `--headers-only` | off | Show only HTTP headers and no body |
| `--compact` | off | Shorthand for small, token-friendly output |

## Testing

Local helper tests:

```bash
npm test
```

Live E2E checks, when Caido is available:

```bash
npx tsx caido-client.ts health
npx tsx caido-client.ts recent --limit 1
```
