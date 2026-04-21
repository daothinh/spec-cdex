# bounty-target-bootstrap

Bootstrap a bug bounty target from a program URL. The skill uses Playwright MCP for rendered host-provided scope capture, writes normalized metadata under `audit-targets/`, preserves `in-scope`, `out-of-scope`, and `rules` as dedicated files, clones source repos, downloads direct artifacts, inventories smart-contract metadata, and stages the next Bounty Hunting Program lane.

## Included

| Path | Purpose |
|------|---------|
| `skills/bounty-target-bootstrap/SKILL.md` | Intake workflow and handoff rules |
| `skills/bounty-target-bootstrap/references/playwright-intake.md` | Playwright MCP extraction checklist |
| `skills/bounty-target-bootstrap/references/workspace-contract.md` | JSON input contract and generated layout |
| `skills/bounty-target-bootstrap/scripts/bootstrap_target.py` | Creates the local workspace, clones repos, downloads artifacts |
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
- `prep/asset-inventory.md`
- `prep/tried-and-ruled-out.md`
- `prep/finding-pipeline.md`
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
python plugins/bounty-target-bootstrap/skills/bounty-target-bootstrap/scripts/bootstrap_target.py --input target.json --repo-root .
```

4. Continue from `audit-targets/<slug>/prep/ready-for-bounty.md`.

The generated `scope/target.json` also records:

- `surface_signals` for the mixed target surface
- `follow_on_lanes` for any executable lanes that should stay in scope after the first deep pass
