# bounty-target-bootstrap

Bootstrap a bug bounty target from a program URL. The skill uses Playwright MCP for rendered host-provided scope capture, writes normalized metadata under `audit-targets/`, preserves `in-scope`, `out-of-scope`, and `rules` as dedicated files, clones source repos, downloads direct artifacts, inventories smart-contract metadata, stages the next Bounty Hunting Program lane, and records local environment readiness for the follow-on phase.

## Included

| Path | Purpose |
|------|---------|
| `skills/bounty-target-bootstrap/SKILL.md` | Intake workflow and handoff rules |
| `skills/bounty-target-bootstrap/references/playwright-intake.md` | Playwright MCP extraction checklist |
| `skills/bounty-target-bootstrap/references/workspace-contract.md` | JSON input contract and generated layout |
| `skills/bounty-target-bootstrap/scripts/bootstrap_target.py` | Creates the local workspace, clones repos, downloads artifacts |
| `skills/bounty-target-bootstrap/scripts/readiness.py` | Assesses and optionally auto-sets up the local toolchain for the chosen lane |
| `tests/test_bootstrap_target.py` | CLI regression tests |

Generated target folders include:

- `scope/target.json`
- `scope/summary.md`
- `scope/in-scope.md`
- `scope/out-of-scope.md`
- `scope/rules.md`
- `scope/program-notes.md`
- `scope/target-surface.md`
- `scope/smart-contracts.md`
- `scope/chain-inventory.json`
- `scope/protocol-archetype.md`
- `scope/proxy-topology.md`
- `scope/dependency-boundaries.md`
- `findings/README.md`
- `prep/asset-inventory.md`
- `prep/tried-and-ruled-out.md`
- `prep/finding-pipeline.md`
- `prep/bootstrap-summary.md`
- `prep/environment-readiness.md`
- `prep/environment-readiness.json`
- `prep/kage-plan.md` when web/API breadth testing is in scope
- `prep/caido-plan.md` when authenticated replay or request-corpus testing is in scope
- `prep/attack-surface-map.md`
- `prep/protocol-invariants.md`
- `prep/domain-logic.md`
- `prep/manual-review-checkpoint.md`
- `prep/web3-readiness.md`
- `prep/context-pack/`
- `prep/ready-for-bounty.md`

## Usage

1. Use Playwright MCP to inspect the scope page and write a JSON file matching `references/workspace-contract.md`.
2. Capture all host-provided references relevant to later audit or whitebox work:
   - repos and source mirrors
   - APKs or source archives
   - wallet / blockchain / exchange focus metadata
   - deployed contract addresses, explorers, ABI URLs, and source links
   - docs, API specs, audit reports, RPC endpoints, and WebSocket endpoints
3. Run:

```bash
python plugins/bounty-target-bootstrap/skills/bounty-target-bootstrap/scripts/bootstrap_target.py --input target.json --repo-root . --readiness-mode ensure
```

4. Stop after bootstrap handoff. Continue hunting from `audit-targets/<slug>/prep/bootstrap-summary.md`, `audit-targets/<slug>/prep/context-pack/`, and `audit-targets/<slug>/prep/ready-for-bounty.md`.

The generated `scope/target.json` also records:

- `surface_signals` for the mixed target surface
- `follow_on_lanes` for any executable lanes that should stay in scope after the first deep pass
- `chain_inventory`, `protocol_archetype`, `dependency_boundaries`, `protocol_invariants`, `domain_logic_checks`, `attack_surface_map`, and `web3_readiness` for web3-heavy targets

The generated finding state also supports the closed-loop pipeline:

- `prep/finding-pipeline.md` tracks `untested -> confirmed -> reverify-pending -> true-positive|false-positive|needs-more-evidence -> report-ready -> reported`
- `prep/bootstrap-summary.md` and `prep/context-pack/` let the hunting pipeline resume without rebuilding trust boundaries or lane choice
- `prep/environment-readiness.md` and `prep/environment-readiness.json` keep Docker, Kage, Caido, mobile, native, and web3 prerequisites explicit before hunting starts
- `prep/domain-logic.md` captures custody, settlement, signature, proof, preimage, and replay assumptions before the hunter calls a finding real
- `prep/manual-review-checkpoint.md` defines the mandatory 20-minute human gate before a finding becomes report-ready
- `prep/kage-plan.md` and `prep/caido-plan.md` split the web/API handoff between breadth-first dynamic testing and authenticated replay-heavy testing
- `findings/README.md` defines the per-finding bundle contract used by independent re-verification and downstream severity triage, including `facts-chain.md`, `impact-financials.md`, `environment.md`, and `manual-review.md` for domain-logic-heavy disclosures
