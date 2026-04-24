# Oracle Consumer

## Priority Invariants

- prices must be fresh, bounded, and correctly normalized
- fallback paths must fail closed
- updater or keeper trust must stay narrower than protocol-wide authority

## First Checks

- stale price use
- decimal mismatch
- manipulation window
- unsafe fallback assumptions
