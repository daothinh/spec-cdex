# Token / Vesting / Escrow

## Priority Invariants

- mint, burn, permit, vesting, and rescue functions must remain role-gated
- release schedules must be monotonic and non-bypassable
- approvals and signatures must remain non-replayable

## First Checks

- cap bypass
- vesting bypass
- rescue abuse
- permit and nonce replay
