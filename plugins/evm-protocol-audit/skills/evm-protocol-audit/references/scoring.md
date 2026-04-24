# EVM Audit Scoring

Use this to keep findings honest.

## Confidence

- `90-100`: replayable exploit path, attacker control proved, blocker disproved
- `75-89`: strong path with concrete evidence, but one non-decisive gap remains
- `50-74`: plausible but still missing decisive replay or blocker analysis
- `<50`: hypothesis only

## False-Positive Gates

Drop or downgrade the claim when any of these fail:

1. **Reachability**: the attacker cannot reach the path in the required role
2. **Control**: the attacker does not control the decisive variable
3. **State realism**: the market, oracle, or liquidity assumptions are unrealistic
4. **Boundary failure**: no actual security boundary breaks, only robustness degrades
5. **Impact realism**: the claimed blast radius depends on conditions not shown by evidence

## Web3-Specific Falsification

Always ask:

- does the attacker need privileged governance or a compromised keeper?
- does the exploit need impossible capital or liquidity?
- does it depend on stale prices that the protocol already rejects?
- does the proxy, adapter, or settlement layer actually expose the claimed boundary?
