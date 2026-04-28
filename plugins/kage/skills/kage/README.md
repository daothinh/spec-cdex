# Kage — pentest sandbox skill

A Codex- and Agent-Skills-compatible skill that drives a full black-box,
greybox, or white-box pentest engagement from inside your coding agent.
Type `kage example.com` and Kage runs recon, deep testing, exploit
verification, chain-building, judging, and writes a consolidated audit
report to `./results/<target>/audit-report.md`.

Every tool runs inside a per-engagement Kali Docker container, so each
host working directory gets its own isolated sandbox — no shared state
between engagements, no host pollution.

## Install

Kage ships as a plugin in the workers.io spec marketplace. The easiest
path is to install the whole marketplace:

```bash
npx skills add workersio/spec
```

Pick `kage` during the interactive selection, or install everything.
In Codex, the plugin normally lands under `~/.codex/plugins/kage/`. In
repo-local development, the skill also works directly from
`plugins/kage/skills/kage/`.

Warm the sandbox:

```bash
~/.codex/plugins/kage/skills/kage/scripts/k whoami
```

On Windows PowerShell, use the wrapper:

```powershell
& "$HOME/.codex/plugins/kage/skills/kage/scripts/k.ps1" whoami
```

Optional — put `k` on `$PATH`:

```bash
sudo ln -sf ~/.codex/plugins/kage/skills/kage/scripts/k /usr/local/bin/k
```

### Requirements

- **Docker** (Desktop on macOS/Windows, Engine on Linux), running
- Codex or another Agent Skills-compatible client
- ~3 GB disk for the image, ~200 MB idle RAM per container

## Usage

```text
/kage acme.com
/kage recon-only acme.com
/kage greybox acme.com ./src
/kage audit ./src
```

Output lands at `./results/<target>/audit-report.md`. Raw artifacts
(nmap, nuclei, PoCs, verified exploits) live under `./results/<target>/`.

Optional: drop a `./creds.md` in your engagement dir before running.
Kage reads it in Turn 0 for target credentials, multi-account IDOR
testing, and rules of engagement. Template at
[`assets/creds.sample.md`](assets/creds.sample.md).

### Managing sandboxes

```bash
k ls       # list all kage containers
k reset    # remove this folder's container
k prune    # remove containers whose workspace dir no longer exists
k nuke     # remove every kage container
```

## Pipeline

| Turn | Phase                             | Output                                               |
| ---- | --------------------------------- | ---------------------------------------------------- |
| 0    | Engagement setup                  | `engagement.json`, results tree                      |
| 1    | Reconnaissance                    | subdomains, live hosts, ports, URLs, tech            |
| 2    | Deep testing (parallel)           | per-class candidate findings                         |
| 3    | Exploit · Verify · Chain · Judge  | reproducible PoCs → `judging/approved_findings.json` |
| 4    | Audit report                      | consolidated `audit-report.md`                       |

Full methodology in [`references/methodology.md`](references/methodology.md);
judging rules in [`references/judging.md`](references/judging.md);
escalation patterns in [`references/chains.md`](references/chains.md).

## Layout

```
kage/
├── SKILL.md       # agent instructions (loaded by /kage)
├── scripts/       # k shim, probe scripts, shared tls/browser client
├── agents/        # sub-agents — testers, verifier, chain-builder, judge, report-writer
├── references/    # methodology, judging, chains, report formatting, tools
│   ├── audit-context-building/   # bundled greybox methodology
│   └── agentmail/                # disposable-inbox provisioning
└── assets/        # Dockerfile, compose.yml, creds template, dorks, wordlists
```

The Codex port uses the same sidecar and scripts, but runs locally as a
single-agent workflow by default. The `agents/` directory remains useful
as prompt/checklist material rather than a hard runtime dependency.


## Scope and safety

Only test systems you own or have explicit permission to test. All
output stays on your local filesystem; `creds.md` is bind-mounted into
the container but never transmitted.

## License

MIT. See the repository [LICENSE](../../../../LICENSE).
