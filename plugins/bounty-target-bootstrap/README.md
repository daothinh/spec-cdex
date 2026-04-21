# bounty-target-bootstrap

Bootstrap a whitebox or Android bug bounty target from a program URL. The skill uses Playwright MCP for rendered scope capture, writes normalized metadata under `audit-targets/`, preserves `in-scope`, `out-of-scope`, and `rules` as dedicated files, clones source repos, downloads in-scope APK or archive artifacts, and stages the next Bounty Hunting Program lane.

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

## Usage

1. Use Playwright MCP to inspect the scope page and write a JSON file matching `references/workspace-contract.md`.
2. Run:

```bash
python plugins/bounty-target-bootstrap/skills/bounty-target-bootstrap/scripts/bootstrap_target.py --input target.json --repo-root .
```

3. Continue from `audit-targets/<slug>/prep/ready-for-bounty.md`.
