<div align="center">
  <img src="header.jpg" alt="Agent Skills for Software Reliability and Correctness — Claude Code plugins by workers.io" width="100%">

  <br>
  <br>

  <p>
    <strong>Claude Code and Codex Skills for Software Correctness</strong>
    <br>
    Formal verification, model checking, security auditing, proof repair, and benchmarking — as slash commands.
  </p>

</div>

<br>

## Contents

- [Quick Start](#quick-start)
- [Codex User-Level Install](#codex-user-level-install)
- [Codex Workspace Install](#codex-workspace-install)
- [Plugins](#plugins)
  - [fuzzer](#fuzzer) — Coverage-guided fuzzing for C/C++, Rust, and Go
  - [kage](#kage) — Local pentest sandbox in a per-engagement Kali container
  - [kani-proof](#kani-proof) — Model checking for Rust and Solana
  - [evm-protocol-audit](#evm-protocol-audit) — Protocol-aware EVM and DeFi audits
  - [solana-audit](#solana-audit) — Smart contract security audits
  - [axiom](#axiom) — Lean 4 proof verification and repair
  - [skill-benchmark](#skill-benchmark) — Measure whether a skill actually helps
  - [workers-app-tester](#workers-app-tester) — Mobile application security testing
  - [save](#save) — Convert sessions into reusable agents
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)
- [License](#license)

<br>

## Quick Start

Install every plugin for Claude Code in one command:

```bash
npx skills add workersio/spec
```

Individual plugins can be selected during installation. Once installed, invoke any skill by name inside Claude Code:

```
/fuzzer            Coverage-guided fuzzing with audit-driven harness design
/kage              Local pentest sandbox — recon, exploit, verify, judge, report
/kani-proof        Write bounded model checker proofs for Rust and Solana
/evm-protocol-audit  Run a structured EVM and DeFi protocol audit
/solana-audit      Run a structured smart contract security audit
/axiom             Verify and repair Lean 4 proofs
/skill-benchmark   Benchmark a skill with controlled eval sessions
/workers-app-tester   Pentest an Android app on a rooted device
/save              Save the current session as a reusable agent
```

Claude and Codex support are included through repo-local metadata:

- Claude marketplace catalog: `.claude-plugin/marketplace.json`
- Codex marketplace catalog: `.agents/plugins/marketplace.json`
- Per-plugin Codex manifests: `plugins/<name>/.codex-plugin/plugin.json`
- The Claude marketplace currently exposes 49 plugins from the repo root
- The Codex marketplace currently exposes 40 installable plugins from the repo root

To use this repo as a repo-scoped Codex marketplace:

1. Keep the repository layout intact so `.agents/plugins/marketplace.json` can resolve `./plugins/<name>` relative to the repo root.
2. Restart Codex after cloning the repo or after changing marketplace metadata.
3. In Codex CLI, run `codex`, then `/plugins`, open the `workersio` marketplace, and install the plugins you want.

Claude-source plugin ports are now managed from the root repo through:

- `plugins/catalog.json` — root inventory for existing plugins and vendored Claude-source ports
- `scripts/sync-root-plugins.mjs` — copies `skills/plugins/<name>` into root `plugins/<name>` and generates manifests
- `scripts/validate-root-plugins.mjs` — validates manifest parity, marketplace drift, and `SKILL.md` relative links
- `.codex-port/preserve-paths.json` inside any copied plugin — opt-in list of root-only files to restore after re-sync when a plugin gets Codex-specific adaptations

Current port policy:

- Codex marketplace publishes all low/medium-risk ports plus the repo's Codex-ready root plugins
- 9 high-risk Claude workflows remain staged in root `plugins/` but blocked from the Codex marketplace until their hook/MCP/task-specific behavior is ported
- Currently blocked from Codex marketplace: `fp-check`, `gh-cli`, `git-cleanup`, `modern-python`, `second-opinion`, `skill-improver`, `static-analysis`, `workflow-skill-design`, `zeroize-audit`

## Codex User-Level Install

If you want the plugins available user-wide and automatically synced to this repo, use the PowerShell installer:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\install-user-level.ps1 -Mode install
```

Useful commands:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\install-user-level.ps1 -Mode status
pwsh -ExecutionPolicy Bypass -File .\scripts\install-user-level.ps1 -Mode uninstall
pwsh -ExecutionPolicy Bypass -File .\scripts\install-user-level.ps1 -Mode install -Force
```

`-Force` backs up conflicting user-level paths to `*.backup-YYYYMMDD-HHMMSS` before replacing them with junctions.

To sync the repo's reusable security agents under `.codex/agents` together with the plugin links after future updates, run:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\sync-codex-security.ps1 -Mode install
```

What it creates:

- `%USERPROFILE%\.codex\.agents\plugins` -> junction to this repo's `.agents\plugins`
- `%USERPROFILE%\.codex\plugins\<plugin-name>` -> junctions to this repo's `plugins\<plugin-name>`
- `%USERPROFILE%\.codex\agents\<agent>.toml` -> synced copies of this repo's `.codex\agents\*.toml` when `sync-codex-security.ps1` is used

Why this layout:

- Codex keeps reading the marketplace from the user-level `.codex` home
- The plugin content stays in this repo as the single source of truth
- Future updates are simple: pull the repo, then restart Codex
- If new plugins are added later, re-run `-Mode install`

For dry runs or custom targets, override the Codex home:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\install-user-level.ps1 -Mode status -CodexHome D:\temp\codex-home
```

## Codex Workspace Install

If you want another workspace to reuse this repo's root-ported plugins, skills, agents, and `AGENTS.md`, run the workspace installer from this repo:

```bat
scripts\install-workspace.bat "D:\path\to\target-repo"
```

What it does:

- Creates repo-root links in the target workspace for `plugins\`, `skills\`, `.agents\plugins`, and `.codex\agents`
- Generates a workspace-safe `AGENTS.md` from this repo's rule prelude and preserves any target-local `AGENTS.md` content inside a managed block
- Makes repo-local reusable Codex agents available inside the target workspace through `.codex\agents`
- Pre-enables every `AVAILABLE` `workersio` Codex plugin by linking `%USERPROFILE%\.codex\plugins\<name>` or `$HOME/.codex/plugins/<name>` to the target workspace and writing `[plugins."<name>@workersio"] enabled = true` into the matching Codex `config.toml`

Useful flags:

```bat
scripts\install-workspace.bat "D:\path\to\target-repo" -Force
scripts\install-workspace.bat "D:\path\to\target-repo" -NoEnablePlugins
scripts\install-workspace.bat "D:\path\to\target-repo" -CodexHome "D:\temp\codex-home"
```

`-Force` backs up conflicting target paths or existing Codex plugin links before replacing them. Restart Codex after running the installer.

<br>

## Plugins

### fuzzer

Coverage-guided fuzzing workflow for C/C++, Rust, and Go targets. Runs a deep audit-context-building pass first to locate suspicious code, then writes a targeted harness, builds with sanitizers, runs the fuzzer, and reports crashes with reproducers.

**Use case** — Find memory safety bugs, integer overflows, and logic faults in native code through coverage-guided fuzzing driven by prior code understanding.

```
/fuzzer
```

<details>
<summary>What's included</summary>
<br>

- `fuzzer` skill — end-to-end harness authoring, build, run, and triage workflow
- `audit-context-building` skill — line-by-line analysis using First Principles, 5 Whys, and 5 Hows to locate fuzz targets
- Function-analyzer agent and reference docs for completeness, output requirements, and worked micro-analysis examples

</details>

---

### kage

Local pentest sandbox that runs a full black-box engagement end-to-end. Every tool runs inside a per-engagement Kali Docker container, so each working directory gets its own isolated sandbox with no cross-contamination. Recon, deep testing, exploit verification, chain-building, judging, and report writing all happen through one Codex-friendly workflow backed by the same upstream probe set.

**Use case** — Run a complete black-box, greybox, or white-box security audit on a target domain or source path and get a deduplicated, verified findings report at `./results/<target>/audit-report.md`.

Status: Codex-ready. The port keeps the upstream Kali sidecar and probe scripts, adds a PowerShell shim for Windows, and defaults to a single-agent workflow instead of Claude-only subagent dispatch.

```
/kage
```

<details>
<summary>What's included</summary>
<br>

- Per-engagement Kali container with a `k` shim for concurrent, isolated runs
- Parallel tester sub-agents (auth, IDOR, access control, SSRF, injection, client-side, API, logic, content discovery, headers, JS secrets, port scanner, vuln scanner)
- Verifier, chain-builder, judge, and report-writer agents for reproducible PoCs and a filtered, scored final report
- Reference docs for methodology, 4-gate judging, 7 escalation-chain patterns, platform report formatting, and the bundled audit-context-building greybox workflow
- Dockerfile, compose file, dork list, credentials template, and wordlist strategy

</details>

---

### kani-proof

Writes [Kani](https://github.com/model-checking/kani) bounded model checker proofs for Rust and Solana programs. Generates proof harnesses, loop invariants, and property checks. Includes reference docs for proof patterns, invariant design, coverage workflows, Kani features, and Anchor program verification.

**Use case** — Prove absence of panics, arithmetic overflows, and unsafe memory access in Rust code. Verify Solana program logic with bounded inputs.

Status: Codex-ready. The standard workflow now uses Codex-friendly subagent prompts with inline fallback when subagents are unavailable.

```
/kani-proof
```

<details>
<summary>What's included</summary>
<br>

- Proof pattern references for common Rust constructs
- Invariant design guides for loops and recursion
- Coverage workflow for measuring proof completeness
- Anchor-specific verification patterns for Solana programs
- Kani feature reference (stubs, contracts, harness configuration)

</details>

---

### evm-protocol-audit

Structured EVM and DeFi security audits for Solidity and Vyper protocols. The workflow is protocol-aware instead of checklist-only: it starts with exploration and archetype classification, then scans auth and upgrade paths, accounting invariants, integrations and callbacks, and oracle or market logic.

**Use case** — Audit EVM protocols with vaults, AMMs, lending markets, staking, bridges, governance, exchanges, or oracle-heavy logic.

Status: Codex-ready. Designed to plug directly into the split security pipeline as the preferred deep lane for EVM smart-contract targets.

```
/evm-protocol-audit
```

<details>
<summary>What's included</summary>
<br>

- Protocol archetype guide for EVM targets
- Cheatsheet and scoring references for auth, accounting, integration, and oracle bug families
- Explorer and scanner prompt contracts for structured audit passes
- Local report template for confidence-scored EVM findings

</details>

---

### solana-audit

Structured security audits for Solana smart contracts covering 25 vulnerability types. Walks through each attack vector systematically — from missing signer checks and PDA validation to re-initialization attacks and arithmetic overflows.

**Use case** — Audit Solana programs before deployment. Identify vulnerabilities across the full attack surface for on-chain programs.

Status: Codex-ready. Audit state now persists under `./.codex/solana-audit/`, and scanner orchestration uses Codex-friendly subagent prompts with inline fallback.

```
/solana-audit
```

<details>
<summary>What's included</summary>
<br>

- Per-vulnerability reference docs for all 25 audit categories
- Audit checklist for systematic coverage
- Cheatsheet for quick reference during review
- Exploit case studies from real-world incidents

</details>

---

### axiom

Verify, check, transform, and repair [Lean 4](https://lean-lang.org/) proofs using the Axiom (Axle) API and CLI. Submits proof terms to the Axiom kernel for type-checking and returns structured verification results.

**Use case** — Machine-check mathematical proofs and formal specifications. Validate and repair proof steps during interactive theorem proving.

Status: Codex-ready. The direct CLI/API workflow and both helper sub-workflows are written for Codex-compatible subagent orchestration.

Primary skill path: `plugins/axiom/skills/axiom-verify/SKILL.md`

```
/axiom
```

---

### skill-benchmark

Benchmark any agent skill to measure whether it actually improves performance. Runs isolated eval sessions with and without the target skill, grades outputs via layered grading (deterministic checks + LLM-as-judge), analyzes behavioral signals, and generates a comparison report with a USE / DON'T USE verdict.

**Use case** — Objectively measure whether a skill helps or hurts on a specific class of tasks before committing to it.

Status: Codex-ready. Headless benchmark runs now use `codex exec --json`.

```
/skill-benchmark
```

<details>
<summary>What's included</summary>
<br>

- Runner agent for executing controlled eval sessions
- Grader agent with layered grading (deterministic + LLM-as-judge)
- Reporter agent for generating comparison reports
- Scripts for stream parsing, transcript analysis, and check execution
- Configuration reference and directory structure docs

</details>

---

### workers-app-tester

Penetration test Android applications on a rooted device. Drives the UI over ADB, intercepts HTTPS traffic through mitmproxy, bypasses SSL pinning with Frida, decompiles APKs for static analysis, and runs security checks for IDORs, auth issues, data exposure, and hardcoded secrets.

**Use case** — Security test mobile applications for common vulnerabilities before release.

```
/workers-app-tester
```

<details>
<summary>What's included</summary>
<br>

- UI parsing and automation scripts for ADB
- Traffic capture and analysis tooling via mitmproxy
- Universal SSL pinning bypass with Frida
- Static analysis through APK decompilation

</details>

---

### save

Converts sessions into reusable Codex agents. Analyzes the current session — the original task, every correction, tool calls, and final output — and distills it into a `.toml` agent file, typically under `~/.codex/agents/` or a repo-local `./.codex/agents/` directory. No server, no API, no accounts.

**Use case** — Capture a working workflow once, replay it forever.

Status: Codex-ready. The workflow now emits Codex agent TOML files.

```
/save
```

<br>

## Repository Structure

```
.claude-plugin/marketplace.json       Claude Code marketplace catalog
.agents/plugins/marketplace.json      Codex marketplace catalog
plugins/
  fuzzer/                              Coverage-guided fuzzing workflow
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/fuzzer/SKILL.md
    skills/audit-context-building/SKILL.md
    skills/audit-context-building/agents/
    skills/audit-context-building/resources/
  kage/                                Local pentest sandbox in a Kali container
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/kage/SKILL.md
    skills/kage/agents/
    skills/kage/references/
    skills/kage/scripts/
    skills/kage/assets/
  kani-proof/                          Bounded model checking for Rust
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/kani-proof/SKILL.md
    skills/kani-proof/references/
  solana-audit/                        Solana smart contract audits
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/solana-audit/SKILL.md
    skills/solana-audit/references/
  axiom/                               Lean 4 proof verification
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/axiom-verify/SKILL.md
  skill-benchmark/                     Benchmark agent skills
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/skill-benchmark/SKILL.md
    skills/skill-benchmark/scripts/
    skills/skill-benchmark/agents/
    skills/skill-benchmark/references/
  workers-app-tester/                  Mobile app security testing
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/workers-app-tester/SKILL.md
    skills/workers-app-tester/scripts/
    skills/workers-app-tester/references/
  save/                                Session-to-agent converter
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/save/SKILL.md
```

Each plugin is self-contained under `plugins/` with its own manifest and skill definitions. Claude discovery continues to use `.claude-plugin/marketplace.json`, while Codex now uses `.agents/plugins/marketplace.json`.

<br>

## Contributing

Contributions welcome. To add a new plugin:

1. Create a directory under `plugins/`
2. Add a `.claude-plugin/plugin.json` manifest for Claude Code
3. Add a `.codex-plugin/plugin.json` manifest for Codex
4. Define skills under `skills/<skill-name>/SKILL.md`
5. Register the plugin in `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`

See any existing plugin for the expected structure.

<br>

## License

[MIT](LICENSE)
