# Dry Run 02 - Hybrid Web Plus Contract Target

Use [examples/hybrid-web-contract-target.json](examples/hybrid-web-contract-target.json).

## Expected Lane

- primary lane: `bounty-program-triage`
- follow-on lanes should include both `bounty-program-web` and `bounty-program-smart-contracts`

## Bootstrap Checks

- `scope/dependency-boundaries.md` should mention hybrid off-chain plus on-chain trust
- `prep/attack-surface-map.md` should include dependency edges
- `prep/bootstrap-summary.md` should keep wallet, blockchain, and exchange context visible

## Hunting Checks

- first deep pass should be chosen from trust boundary and value concentration, not platform alone
- finding bundles should keep off-chain role assumptions explicit in `environment.md`

## Reporting Checks

- final report bundle should still preserve chain identifiers and web boundary facts without flattening the issue into “just web” or “just contract”
