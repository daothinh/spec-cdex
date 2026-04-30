# caido

Codex-native port of the upstream `caido-mode` skill. This plugin uses the official
`@caido/sdk-client` to search HTTP history, replay and edit authenticated requests,
manage scopes and findings, export curl PoCs, and materialize local evidence for
the bug bounty pipeline in this repo.

## Included

| Path | Purpose |
|------|---------|
| `skills/caido-mode/SKILL.md` | Agent instructions for using Caido during web/API hunting |
| `skills/caido-mode/README.md` | Operator-facing setup and usage guide |
| `skills/caido-mode/caido-client.ts` | CLI entry point |
| `skills/caido-mode/lib/commands/*.ts` | Request, replay, findings, management, intercept, and evidence commands |
| `skills/caido-mode/scripts/caido` | Unix wrapper |
| `skills/caido-mode/scripts/caido.ps1` | PowerShell wrapper |
| `skills/caido-mode/tests/*.test.ts` | Pure local tests for output, request editing, and bundle parsing |

## Why This Exists

`kage` is already strong for recon, scanners, and broad dynamic testing. What the
pipeline still lacked was a stateful traffic broker for authenticated flows:

- mutate one real request without rebuilding 2 KB of cookies
- replay workflow-heavy endpoints while keeping auth intact
- mine logged-in traffic history quickly with HTTPQL
- turn a captured request into local PoC artifacts and synced Caido findings

That is the job of this plugin.

## Usage

1. Install dependencies inside `skills/caido-mode/`:

```bash
npm install
```

2. Authenticate once:

```bash
npx tsx caido-client.ts setup <your-pat> http://localhost:8080
```

3. Use the wrapper:

```bash
plugins/caido/skills/caido-mode/scripts/caido health
plugins/caido/skills/caido-mode/scripts/caido search 'req.path.cont:"/api/"' --limit 10
plugins/caido/skills/caido-mode/scripts/caido edit 123 --path /api/users/999 --compact
```

On Windows PowerShell:

```powershell
& "$PWD/plugins/caido/skills/caido-mode/scripts/caido.ps1" health
```

## Codex-Specific Additions

The upstream skill was Claude-oriented. This port adds:

- secret caching under `~/.codex/caido/secrets.json` by default
- `CAIDO_SECRETS_PATH` override for testing or custom storage
- `export-evidence` for saving local bug-bounty artifacts
- `sync-finding` for pushing a local finding bundle into Caido
- PowerShell wrapper for Windows

## Pipeline Role

Use Caido alongside `kage`, not instead of it.

- `kage`: recon, breadth, unauthenticated probing, scanner output
- `caido`: authenticated request mutation, replay-heavy abuse, workflow interception, traffic-corpus mining

## License

MIT
