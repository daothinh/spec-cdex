# Vault / Yield Strategy

## Priority Invariants

- shares must track asset value conservatively
- strategy debt must not drift from real asset state
- keeper and harvest flows must not bypass accounting or withdrawal safety

## First Checks

- share inflation
- stale debt accounting
- harvest hook abuse
- privileged withdrawal path
