# Smart Contract Matrix

Choose the platform lane before starting detailed review.

| Platform | Signals | Priority Surfaces | Preferred Building Blocks |
| --- | --- | --- | --- |
| Solidity / EVM | `.sol`, Foundry/Hardhat configs, proxy patterns | privileged entry points, upgrade/auth flows, token integrations, callbacks, price/oracle logic | `entry-point-analyzer`, `building-secure-contracts`, `property-based-testing`, `mutation-testing` |
| Vyper | `.vy`, Vyper configs | access control, pricing math, initialization, callbacks | `entry-point-analyzer`, `building-secure-contracts` |
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
