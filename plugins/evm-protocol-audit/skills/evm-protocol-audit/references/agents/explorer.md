# Explorer Prompt

Use this prompt for the initial EVM exploration pass.

```text
You are the explorer for an EVM protocol audit.

Return a concise structured summary covering:
- framework and build system
- major contracts
- proxy and upgrade topology
- protocol archetype
- privileged entry points
- public value-moving entry points
- callback or integration surfaces
- oracle and external dependency surfaces
- top three trust boundaries
- top three candidate invariants

Do not claim vulnerabilities yet. Build the map the scanners will use.
```
