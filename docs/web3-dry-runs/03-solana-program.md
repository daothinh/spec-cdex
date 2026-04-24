# Dry Run 03 - Solana Program

Use [examples/solana-program-target.json](examples/solana-program-target.json).

## Expected Lane

- primary lane: `bounty-program-smart-contracts`
- first deep pass: `solana-audit`

## Bootstrap Checks

- `scope/chain-inventory.json`
- `scope/protocol-archetype.md`
- `prep/protocol-invariants.md`
- `prep/web3-readiness.md`

## Hunting Checks

- `security-hunting-pipeline` should still load the new web3 prep artifacts before using `solana-audit`
- finding bundles can use `facts-chain.md` and `environment.md` for tx and account evidence

## Reporting Checks

- web3 report bundle generation should work even when the deep lane is Solana rather than EVM
