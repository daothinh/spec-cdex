# Perps / Orderbook / Exchange

## Priority Invariants

- margin, settlement, funding, and fee routing must reconcile
- sequencer, signer, or backend trust must not replace hard boundaries
- liquidation decisions must not depend on attacker-shaped market inputs

## First Checks

- margin accounting bugs
- liquidation flaws
- funding drift
- sequencer or settlement trust breaks
