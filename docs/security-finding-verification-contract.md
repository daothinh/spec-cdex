# Security Finding Verification Contract

This document defines the minimum verification bar before a finding can move from hypothesis to report-ready in the split security pipeline.

## Why This Exists

The recurring failure mode is not "missing one extra screenshot." It is mistaking an internal side effect for a real exploit consequence.

These are not enough on their own:

- a dangerous function call
- a saved invoice or queued payment
- an initiated HTLC
- an emitted event
- an outbound request or bridge message
- a partial state transition

Those may be useful clues, but they are not reportable impact unless they lead to an attacker-observable boundary break.

## Claim Shape

Every `claim.md` should answer:

- which asset is at risk
- what attacker capability exists at the start
- which control is supposed to stop the attacker
- which exact trust boundary fails
- which observed consequence proves the failure
- for financial or payment findings, which step realizes value and who controls it
- for cryptographic findings, how the attacker satisfies the required signature, proof, witness, preimage, or approval gate

If a claim cannot be written that way, it is not ready for reverify.

## Domain Logic

For Web3, smart-contract, Lightning, payment, escrow, bridge, exchange, or other cryptography-heavy targets, the pipeline must record the domain logic explicitly instead of assuming it from surface code.

At minimum, `prep/domain-logic.md` should capture:

- custody and authority model
- which actor controls the decisive key, signature, proof, witness, preimage, or approval
- nonce, replay, domain-separation, chain-binding, funding-state, or finality assumptions
- off-chain signer, relayer, keeper, oracle, sequencer, or settlement dependencies
- the exact end-state that realizes attacker value

If the finding depends on a cryptographic or settlement gate, the reportable claim must explain how that gate is satisfied, not merely that a nearby function was reached.

## Evidence Ladder

The pipeline should distinguish these levels:

1. source pattern or suspicious code
2. reachability
3. attacker control over decisive input
4. boundary failure
5. attacker-observable consequence
6. value realization or settlement proof when the bug class needs it

`confirmed` requires level 5. Financial, wallet, bridge, Lightning, escrow, and exchange findings also require level 6.

## Hard Stops

Do not call a finding `confirmed`, `TRUE POSITIVE`, or `report-ready` when any of these remain unresolved:

- the proof ends at an internal side effect instead of an attacker-visible consequence
- the attacker does not control a required preimage, signature, relayer, keeper, settlement worker, or liquidity dependency
- the attacker does not control a required proof, witness, approval, or other domain-logic gate
- the PoC proves only initiation, while value realization or claimability is still hypothetical
- the claim inflates an operational robustness issue into a security boundary break

## Validation Node

The pipeline needs a separate validation node, not just a success narrative.

`security-finding-reverify` is that node. Its default job is devil's advocate:

- rebuild the path independently
- identify the strongest business-logic and cryptographic blockers
- try to falsify the claim with those blockers
- downgrade or kill the finding when the mechanism is impossible

## Negative Controls

Every verified finding should include at least one negative control that would have falsified the claim if the intended security control were actually working.

Examples:

- same request with a different actor or identifier
- same flow with the missing prerequisite removed
- same exploit path after restoring the supposed blocker
- same financial flow without the attacker-controlled settlement input

For cryptographic and settlement findings, negative controls should preferentially attack the decisive gate:

- missing or wrong signature
- missing proof or witness
- wrong preimage
- wrong nonce, replay domain, or chain binding
- missing funding or settlement precondition

## End-To-End PoC Standard

For business-logic, cryptographic, and financial findings, a PoC must prove end-to-end state impact.

Examples:

- attacker balance increases and victim balance decreases
- attacker can actually claim or settle the pending payment
- unauthorized ownership, role, or custody state is reached
- a previously blocked withdrawal, release, or settlement succeeds

Logs such as `pay_invoice_called`, `invoice_saved`, or `event_emitted` are useful diagnostics, but they are not sufficient proof on their own.

## Recorded Replay

Before a finding becomes `TRUE POSITIVE` or `report-ready`, the last clean rerun must be recorded with `asciinema`.

Minimum bar:

- check system `asciinema` first and stop if neither native PATH nor WSL fallback is available
- save the local `.cast` file under `artifacts/asciinema/`
- upload the recording to `asciinema` and save the returned `https://asciinema.org/a/...` URL
- carry both the local cast and uploaded URL into the report bundle
- place the `asciinema` URL directly under the gist URL in the report link block

## Manual 20-Minute Gate

Before any finding becomes `report-ready` or enters submission packaging, a human must complete `manual-review.md`.

That review should record:

- who reviewed the finding
- when the review happened
- that at least about 20 minutes were spent on the mechanism
- what business logic or cryptographic mechanism was read manually
- which blocker hypotheses were checked
- why the claim still holds, or why it was downgraded or stopped

## Submission Discipline

Titles, severity, and opening paragraphs must match the observed effect, not the most dramatic theoretical extension.

If the proof shows only:

- an attempted payment
- a queued transfer
- an event that might matter later
- a state machine entering an intermediate state

then the report should stop until the end-state is proved or the claim is downgraded to the actually observed effect.
