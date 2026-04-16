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
- [Plugins](#plugins)
  - [fuzzer](#fuzzer) — Coverage-guided fuzzing for C/C++, Rust, and Go
  - [kani-proof](#kani-proof) — Model checking for Rust and Solana
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
/kani-proof        Write bounded model checker proofs for Rust and Solana
/solana-audit      Run a structured smart contract security audit
/axiom             Verify and repair Lean 4 proofs
/skill-benchmark   Benchmark a skill with controlled eval sessions
/workers-app-tester   Pentest an Android app on a rooted device
/save              Save the current session as a reusable agent
```

Codex support is included through repo-local metadata:

- Codex marketplace catalog: `.agents/plugins/marketplace.json`
- Per-plugin Codex manifests: `plugins/<name>/.codex-plugin/plugin.json`
- All repo plugins are marked `AVAILABLE` for Codex: `axiom`, `fuzzer`, `kani-proof`, `save`, `skill-benchmark`, `solana-audit`, `workers-app-tester`

To use this repo as a repo-scoped Codex marketplace:

1. Keep the repository layout intact so `.agents/plugins/marketplace.json` can resolve `./plugins/<name>` relative to the repo root.
2. Restart Codex after cloning the repo or after changing marketplace metadata.
3. In Codex CLI, run `codex`, then `/plugins`, open the `workersio` marketplace, and install the plugins you want.

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

What it creates:

- `%USERPROFILE%\.codex\.agents\plugins` -> junction to this repo's `.agents\plugins`
- `%USERPROFILE%\.codex\plugins\<plugin-name>` -> junctions to this repo's `plugins\<plugin-name>`

Why this layout:

- Codex keeps reading the marketplace from the user-level `.codex` home
- The plugin content stays in this repo as the single source of truth
- Future updates are simple: pull the repo, then restart Codex
- If new plugins are added later, re-run `-Mode install`

For dry runs or custom targets, override the Codex home:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\install-user-level.ps1 -Mode status -CodexHome D:\temp\codex-home
```

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
