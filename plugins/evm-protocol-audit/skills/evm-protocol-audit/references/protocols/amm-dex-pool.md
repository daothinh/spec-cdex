# AMM / DEX Pool

## Priority Invariants

- reserve and LP accounting must reconcile after swaps and liquidity events
- callbacks must not observe or exploit half-updated state
- oracle accumulation and fee routing must remain internally consistent

## First Checks

- reserve invariant drift
- fee rounding
- callback abuse
- slippage and oracle manipulation
