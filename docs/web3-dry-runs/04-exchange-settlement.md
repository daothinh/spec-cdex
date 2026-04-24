# Dry Run 04 - Exchange-Like Settlement Target

Use [examples/exchange-settlement-target.json](examples/exchange-settlement-target.json).

## Expected Lane

- primary lane: `bounty-program-triage`
- likely follow-on lanes:
  - `bounty-program-web`
  - `bounty-program-smart-contracts`

## Bootstrap Checks

- `scope/dependency-boundaries.md` should mention signer, relayer, or settlement dependencies
- `prep/attack-surface-map.md` should show off-chain control-plane edges
- `prep/protocol-invariants.md` should align with `Perps / Orderbook / Exchange`

## Hunting Checks

- reverify must be able to downgrade claims that require unrealistic custody, signer, or liquidity assumptions

## Reporting Checks

- `web3-facts.json` should preserve market, chain, and settlement identifiers
- `asset-delta.md` should separate observed balance movement from inferred exchange-wide blast radius
