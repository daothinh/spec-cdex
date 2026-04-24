# EVM Audit Cheatsheet

Use this as the first-pass taxonomy and grepable reminder set.

## U - Auth And Upgrade

- `U-1` Missing or broken privileged access control
- `U-2` Unsafe upgrade path or proxy admin assumptions
- `U-3` Reinitialization or initializer ordering mistakes
- `U-4` Timelock or governance bypass

## A - Accounting And Invariants

- `A-1` Share inflation or price-per-share manipulation
- `A-2` Debt, collateral, or reserve accounting drift
- `A-3` Rounding or decimal mismatch with solvency impact
- `A-4` Fee bucket or reward accrual corruption

## I - Integrations And Callbacks

- `I-1` Reentrancy or callback ordering failure
- `I-2` Unsafe token integration assumptions
- `I-3` External call, delegatecall, or adapter trust break
- `I-4` Bridge or messaging replay and verification failure

## O - Oracle And Market Logic

- `O-1` Stale or unchecked oracle data
- `O-2` Decimal, unit, or bounds mismatch in price handling
- `O-3` Manipulation window or missing slippage guard
- `O-4` Settlement or funding logic using attacker-influenced state

## Fast Questions

1. Which entry point moves value or authority?
2. Which variable makes that state transition safe?
3. Can the attacker influence that variable?
4. Is the safety assumption on-chain, off-chain, or both?
5. What invariant breaks when the transition succeeds?
