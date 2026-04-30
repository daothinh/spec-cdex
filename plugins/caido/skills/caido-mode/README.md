# Caido Mode

Full SDK CLI for [Caido](https://caido.io) adapted for Codex. Search HTTP history,
edit and replay authenticated requests, manage scopes and findings, export curl
commands, and save local evidence under your finding bundle.

## Why Use It

When you already have a real authenticated request in Caido, the fastest path is
usually:

1. find the request in HTTP history
2. use `edit` to change only method, path, headers, or body
3. replay it with all cookies and auth headers preserved

This is ideal for:

- IDOR and BOLA
- role and header bypasses
- webhook replay
- stateful admin/API abuse
- post-login workflow testing

## Requirements

- Node.js
- a running Caido instance
- a Caido PAT
- dependencies installed in this skill directory

## Setup

```bash
cd plugins/caido/skills/caido-mode
npm install
npx tsx caido-client.ts setup <your-pat> http://localhost:8080
```

Auth lookup order:

1. `CAIDO_PAT` / `CAIDO_URL`
2. cached values in `~/.codex/caido/secrets.json`

Optional override:

```bash
export CAIDO_SECRETS_PATH=/absolute/path/secrets.json
```

## Wrapper Usage

Unix:

```bash
plugins/caido/skills/caido-mode/scripts/caido health
plugins/caido/skills/caido-mode/scripts/caido recent --limit 5
```

PowerShell:

```powershell
& "$PWD/plugins/caido/skills/caido-mode/scripts/caido.ps1" health
& "$PWD/plugins/caido/skills/caido-mode/scripts/caido.ps1" recent --limit 5
```

## High-Value Commands

### Search history

```bash
npx tsx caido-client.ts search 'req.method.eq:"POST" AND resp.code.eq:200'
npx tsx caido-client.ts search 'req.path.cont:"/admin"' --ids-only
```

### Edit and replay

```bash
npx tsx caido-client.ts edit 123 --path /api/users/999
npx tsx caido-client.ts edit 123 --method POST --body '{"role":"admin"}'
npx tsx caido-client.ts edit 123 --set-header "X-Forwarded-For: 127.0.0.1"
```

### Evidence export

```bash
npx tsx caido-client.ts export-evidence 123 --out audit-targets/acme/findings/F001/artifacts/caido
```

### Sync a local finding bundle into Caido

```bash
npx tsx caido-client.ts sync-finding --bundle audit-targets/acme/findings/F001 --request-id 123
```

### Export PoC curl

```bash
npx tsx caido-client.ts export-curl 123
```

## HTTPQL Reminder

- strings must be quoted
- integers are not quoted
- do not use `NOT`
- use negated operators instead:
  - `ne`
  - `ncont`
  - `nlike`
  - `nregex`

Examples:

```text
req.method.eq:"POST" AND resp.code.eq:200
req.path.ncont:"/health"
resp.len.gt:100000
source:"replay" OR source:"automate"
```

## Local Testing

Pure helper tests:

```bash
npm test
```

These tests do not require a live Caido instance.
