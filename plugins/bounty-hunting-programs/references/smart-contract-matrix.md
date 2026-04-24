# Smart Contract Matrix

Choose the platform lane before starting detailed review.

| Platform | Signals | Priority Surfaces | Preferred Building Blocks |
| --- | --- | --- | --- |
| Solidity / EVM | `.sol`, Foundry/Hardhat configs, proxy patterns | privileged entry points, upgrade/auth flows, token integrations, callbacks, price/oracle logic | `evm-protocol-audit`, `entry-point-analyzer`, `building-secure-contracts`, `property-based-testing`, `mutation-testing` |
| Vyper | `.vy`, Vyper configs | access control, pricing math, initialization, callbacks | `evm-protocol-audit`, `entry-point-analyzer`, `building-secure-contracts` |
| Solana / Anchor | `.rs`, `Anchor.toml`, `#[program]`, account structs | signer checks, PDA validation, CPI, account ownership, reinitialization, arithmetic | `solana-audit`, `entry-point-analyzer`, `kani-proof`, `property-based-testing` |
| Cosmos / CosmWasm | `cosmwasm-std`, `execute`, `reply`, `sudo` | privileged executes, IBC hooks, reply handling, state invariants | `entry-point-analyzer`, `building-secure-contracts` |
| Cairo / Starknet | `.cairo`, Starknet deps | access control, storage initialization, arithmetic, reentrancy-like patterns | `building-secure-contracts` |
| Substrate | pallets, `decl_module!`, FRAME traits | origin checks, weight/accounting, unsigned tx paths, arithmetic | `building-secure-contracts`, `property-based-testing` |
| TON | `.fc`, `.func`, `.tact` | replay protection, sender validation, receiver exposure | `entry-point-analyzer`, `building-secure-contracts` |
| Algorand / TEAL | TEAL or PyTEAL projects | rekeying, fee validation, group constraints, time-based replay | `building-secure-contracts` |

## Common Bug Classes

- Access control failures
- Replay and nonce handling flaws
- Rounding, precision, and accounting errors
- Initialization and upgrade mistakes
- Unsafe token integration assumptions
- Cross-program or cross-contract callback abuse

## Protocol Archetype Triage

After choosing the platform, classify the protocol shape so the first audit pass hits the real invariants instead of a generic checklist.

| Archetype | Assets At Risk | Priority Surfaces | First Bug Classes To Test |
| --- | --- | --- | --- |
| Token / Vesting / Escrow | balances, mint caps, vesting state | mint, burn, transfer hooks, permit, vesting release, admin rescue | mint or burn auth, cap bypass, vesting schedule corruption, permit or signature replay |
| AMM / DEX Pool | pool reserves, LP shares, fee buckets | swap math, fee accounting, callback hooks, oracle accumulation, admin fee controls | invariant breaks, fee rounding, callback abuse, TWAP or oracle manipulation |
| Vault / Yield Strategy | deposited assets, shares, strategy debt | deposit or withdraw accounting, share price, harvest, strategy callbacks, keeper flows | share inflation, stale debt accounting, unsafe harvest hooks, privileged withdrawal paths |
| Lending / Borrowing | collateral, debt, reserves, liquidation bonus | borrow, repay, collateral factor math, liquidation, interest accrual, oracle feeds | bad collateral checks, debt-share math, liquidation edge cases, oracle decimal or staleness bugs |
| Staking / Rewards | staked balances, reward buckets, delegation state | checkpointing, reward accrual, delegation, slashing, pause or rescue controls | checkpoint desync, reward inflation, delegation auth bugs, slashing or unstake bypass |
| Bridge / Messaging | escrowed assets, minted wrappers, message queue | deposit, mint or unlock, message verification, replay protection, domain separation, relayer trust | replay, proof verification gaps, nonce reuse, double mint or double release |
| Governance / Timelock | admin power, treasury, config state | proposal lifecycle, voting power snapshots, executor auth, timelock queue or cancel | voting power manipulation, snapshot bugs, timelock bypass, privileged execution |
| Perps / Orderbook / Exchange | margin, insurance fund, open interest, settlement state | order placement, matching, funding, liquidation, settlement, fee routing | margin accounting bugs, liquidation flaws, funding drift, sequencer or backend trust breaks |
| NFT / Marketplace | custody, listings, royalties, bids | order auth, signature validation, callbacks, settlement, royalty or fee logic | signature replay, unauthorized fills, royalty mis-accounting, callback abuse |
| Oracle Consumer | protocol solvency, rate or price state | feed freshness, decimals, bounds checks, fallback paths, circuit breakers | stale price use, decimal mismatch, manipulation windows, unsafe fallback assumptions |

## Hybrid Surface Reminder

Smart-contract review is often only one lane of a Web3 target.

If the protocol depends on:
- keepers
- relayers
- sequencers
- signer services
- exchange settlement backends
- browser wallet or extension trust

then keep those dependencies in the threat model and route back through `bounty-program-triage` when needed.
