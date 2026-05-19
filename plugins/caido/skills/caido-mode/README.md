# Caido Mode

Full SDK CLI for Caido adapted for Codex. Search HTTP history, edit and replay
authenticated requests, manage scopes, filters, environments, findings,
projects, intercept, automate/fuzz sessions, export curl commands, and save
local evidence under finding bundles.

## Why Use It

When you already have a real authenticated request in Caido, the fastest path is
usually:

1. find the request in HTTP history
2. use `edit` to change only method, path, headers, or body
3. replay it with all cookies and auth headers preserved
4. export curl and local artifacts only when the behavior matters

This is ideal for IDOR/BOLA, role bypasses, header trust issues, webhook replay,
post-login workflow testing, and admin/API state-machine abuse.

## Command Coverage

| Category | Commands |
| --- | --- |
| HTTP history | `search`, `recent`, `get`, `get-response`, `export-curl` |
| Edit and replay | `edit`, `replay`, `send-raw` |
| Sessions | `create-session`, `rename-session`, `replay-sessions`, `delete-sessions` |
| Collections | `replay-collections`, `create-collection`, `rename-collection`, `delete-collection` |
| Automate and fuzzing | `create-automate-session`, `fuzz` |
| Scopes | `scopes`, `create-scope`, `update-scope`, `delete-scope` |
| Filter presets | `filters`, `create-filter`, `update-filter`, `delete-filter` |
| Environments | `envs`, `create-env`, `select-env`, `env-set`, `delete-env` |
| Findings | `findings`, `get-finding`, `create-finding`, `update-finding`, `sync-finding` |
| Local evidence | `export-evidence` |
| Tasks | `tasks`, `cancel-task` |
| Projects | `projects`, `select-project` |
| Hosted files | `hosted-files`, `delete-hosted-file` |
| Intercept | `intercept-status`, `intercept-enable`, `intercept-disable` |
| Info and auth | `viewer`, `plugins`, `health`, `setup`, `auth-status` |

## Requirements

- Node.js and npm
- running Caido instance
- Caido PAT
- dependencies installed in this skill directory

## Setup

```bash
cd plugins/caido/skills/caido-mode
npm install
npx tsx caido-client.ts setup <your-pat> http://localhost:8080
```

Auth lookup order:

1. `CAIDO_PAT` and `CAIDO_URL`
2. cached values in `~/.codex/caido/secrets.json`
3. optional override path in `CAIDO_SECRETS_PATH`

Optional override:

```bash
export CAIDO_SECRETS_PATH=/absolute/path/secrets.json
```

## Wrapper Usage

Unix:

```bash
plugins/caido/skills/caido-mode/scripts/caido health
plugins/caido/skills/caido-mode/scripts/caido recent --limit 5
plugins/caido/skills/caido-mode/scripts/caido search 'req.path.cont:"/api/"' --limit 10
```

PowerShell:

```powershell
& "$PWD/plugins/caido/skills/caido-mode/scripts/caido.ps1" health
& "$PWD/plugins/caido/skills/caido-mode/scripts/caido.ps1" recent --limit 5
```

## Usage

All commands output JSON unless a command is explicitly a raw export such as
`export-curl`.

### Search and Browse

```bash
npx tsx caido-client.ts search 'req.method.eq:"POST" AND resp.code.eq:200'
npx tsx caido-client.ts search 'req.host.cont:"api"' --limit 50
npx tsx caido-client.ts search 'req.path.cont:"/admin"' --ids-only
npx tsx caido-client.ts recent --limit 10
npx tsx caido-client.ts get <request-id>
npx tsx caido-client.ts get-response <request-id>
```

### Edit and Replay

```bash
npx tsx caido-client.ts edit <id> --path /api/user/999
npx tsx caido-client.ts edit <id> --method POST --body '{"role":"admin"}'
npx tsx caido-client.ts edit <id> --set-header "X-Forwarded-For: 127.0.0.1"
npx tsx caido-client.ts edit <id> --remove-header "X-CSRF-Token"
npx tsx caido-client.ts edit <id> --replace "user123:::user456"
npx tsx caido-client.ts replay <id> --compact
```

### Send Raw and Export Curl

```bash
npx tsx caido-client.ts send-raw --host example.com --port 443 --raw $'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n'
npx tsx caido-client.ts export-curl <request-id>
```

### Evidence Export

```bash
npx tsx caido-client.ts export-evidence 123 --out audit-targets/acme/findings/F001/artifacts/caido
npx tsx caido-client.ts export-evidence 123 --out audit-targets/acme/findings/F001/artifacts/caido --include-request-raw
```

`export-evidence` writes request metadata JSON, a curl PoC, response raw when
available, and optional request raw.

### Findings

```bash
npx tsx caido-client.ts findings
npx tsx caido-client.ts get-finding <finding-id>
npx tsx caido-client.ts create-finding <request-id> --title "IDOR in user profile" --description "Can access other users' data"
npx tsx caido-client.ts update-finding <finding-id> --title "Updated title"
npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --request-id 123
```

`sync-finding` is convenience only. Local finding bundles remain the source of
truth for the reporting pipeline.

### Scopes, Filters, and Environments

```bash
npx tsx caido-client.ts scopes
npx tsx caido-client.ts create-scope "Target" --allow "*.target.com,api.target.com" --deny "*.cdn.target.com"
npx tsx caido-client.ts filters
npx tsx caido-client.ts create-filter "API Errors" --query 'req.path.cont:"/api/" AND resp.code.gte:400'
npx tsx caido-client.ts create-env "IDOR-Test"
npx tsx caido-client.ts env-set <env-id> victim_id "user_456"
npx tsx caido-client.ts select-env <env-id>
```

### Sessions, Collections, and Fuzzing

```bash
npx tsx caido-client.ts create-session <request-id>
npx tsx caido-client.ts rename-session <session-id> "idor-user-profile"
npx tsx caido-client.ts replay-sessions
npx tsx caido-client.ts create-collection "Auth Boundary Tests"
npx tsx caido-client.ts create-automate-session <request-id>
npx tsx caido-client.ts fuzz <session-id>
```

Configure automate markers and payloads in the Caido UI before starting `fuzz`.

### Tasks, Projects, Info, and Intercept

```bash
npx tsx caido-client.ts tasks
npx tsx caido-client.ts cancel-task <task-id>
npx tsx caido-client.ts projects
npx tsx caido-client.ts select-project <id>
npx tsx caido-client.ts viewer
npx tsx caido-client.ts plugins
npx tsx caido-client.ts health
npx tsx caido-client.ts auth-status
npx tsx caido-client.ts intercept-status
npx tsx caido-client.ts intercept-enable
npx tsx caido-client.ts intercept-disable
```

## HTTPQL Reminder

- strings must be quoted
- integers are not quoted
- do not use `NOT`
- use negated operators instead: `ne`, `ncont`, `nlike`, `nregex`

Examples:

```text
req.method.eq:"POST" AND resp.code.eq:200
req.path.regex:"/(login|auth|oauth)/"
req.path.ncont:"/health"
resp.len.gt:100000
source:"replay" OR source:"automate"
```

## Output Control

| Flag | Default | Description |
| --- | --- | --- |
| `--max-body <n>` | `200` | Max response body lines; `0` means unlimited |
| `--max-body-chars <n>` | `5000` | Max response body chars; `0` means unlimited |
| `--no-request` | off | Skip request raw in output |
| `--headers-only` | off | Show only HTTP headers and no body |
| `--compact` | off | Shorthand for small output |

## Pipeline Notes

Use this skill alongside the web target pipeline:

- bootstrap emits `prep/caido-plan.md` when web/API replay is likely useful
- hunting should record request IDs, session IDs, filter names, curl exports, and evidence directories in `prep/asset-inventory.md`
- findings should preserve exported Caido artifacts under `findings/<id>/artifacts/caido/`
- report submission consumes those artifacts from the local bundle, not from the Caido UI

## Local Testing

Pure helper tests:

```bash
npm test
```

These tests do not require a live Caido instance.
