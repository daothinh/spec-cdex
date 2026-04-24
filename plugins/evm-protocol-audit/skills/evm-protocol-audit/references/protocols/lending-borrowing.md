# Lending / Borrowing

## Priority Invariants

- collateral, debt, and liquidation math must remain conservative
- stale, bounded, or malformed prices must not create bad debt
- liquidations must not bypass role or state constraints

## First Checks

- collateral factor mistakes
- debt-share math bugs
- liquidation edge cases
- oracle decimal and freshness failures
