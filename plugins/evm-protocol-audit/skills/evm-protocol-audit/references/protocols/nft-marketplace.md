# NFT / Marketplace

## Priority Invariants

- listings, signatures, bids, and fills must bind to the intended asset and seller
- callbacks must not redirect or re-enter payout state
- royalties and fee routes must not be attacker-controlled

## First Checks

- signature replay
- unauthorized fills
- royalty mis-accounting
- callback abuse
