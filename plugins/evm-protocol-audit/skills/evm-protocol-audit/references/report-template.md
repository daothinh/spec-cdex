# EVM Audit Report Template

Use this structure for local reporting.

```markdown
# EVM Security Audit Report: [Target]

## Executive Summary
- Scope
- Framework and build system
- Protocol archetype
- Replay mode: fork-capable | local-test-capable | static-only
- Findings by severity

## Method
- exploration
- scanner passes used
- falsification approach

## Findings

### [HIGH] EVM-001: [Title] (Confidence: 88/100)
**Taxonomy:** A-1
**Location:** contracts/Vault.sol:123
**Boundary:** share accounting
**Observed Impact:** ...
**Attacker Preconditions:** ...
**Why It Fails:** ...
**Recommendation:** ...

## Below Threshold

Track plausible but unconfirmed paths here.
```
