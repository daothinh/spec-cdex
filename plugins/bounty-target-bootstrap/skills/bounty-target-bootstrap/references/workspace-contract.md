# Workspace Contract

The bootstrap script expects one JSON object.

## Required Keys

- `program_name`
- `program_url`
- `target_type`

`target_type` must be `web`, `whitebox`, `android`, `smart-contract`, or `native`.

## Optional Keys

- `slug`
- `focus_areas`
- `scope_summary`
- `in_scope`
- `out_of_scope`
- `allowed_assets`
- `scope`
- `out_scope`
- `rules`
- `safe_harbor`
- `submission_guidelines`
- `program_notes`
- `auth_notes`
- `environment_notes`
- `repo_urls`
- `source_repos`
- `source_code_urls`
- `artifacts`
- `artifact_urls`
- `package_names`
- `app_urls`
- `store_urls`
- `web_urls`
- `api_urls`
- `rpc_urls`
- `ws_urls`
- `keeper_urls`
- `relayer_urls`
- `signer_urls`
- `oracle_urls`
- `docs_urls`
- `whitepaper_urls`
- `api_spec_urls`
- `audit_report_urls`
- `registry_urls`
- `explorer_urls`
- `smart_contracts`
- `contracts`
- `deployed_contracts`
- `protocol_archetype`
- `protocol_archetype_hint`
- `raw_scope_notes`
- `ignored_assets`

## Artifact Shape

Each artifact entry may be a string URL or an object:

```json
{
  "url": "https://target.local/builds/app.apk",
  "kind": "apk",
  "filename": "target-app.apk"
}
```

`kind` is optional. The script infers `apk` and `source-archive` from the URL when omitted.

Supported explicit `kind` values now include `apk`, `source-archive`, `abi`, `api-spec`, `audit-report`, and `other`.

## Smart Contract Shape

Each `smart_contracts` entry may include:

```json
{
  "name": "VaultProxy",
  "kind": "proxy",
  "chain": "Ethereum",
  "chain_id": "1",
  "network": "mainnet",
  "vm": "EVM",
  "address": "0x1234...",
  "proxy_address": "0x1234...",
  "implementation_address": "0xabcd...",
  "explorer_url": "https://etherscan.io/address/0x1234...",
  "abi_url": "https://target.local/contracts/vault-proxy-abi.json",
  "source_url": "https://github.com/acme/protocol/blob/main/src/VaultProxy.sol",
  "repo_url": "https://github.com/acme/protocol.git",
  "language": "Solidity",
  "notes": "Host marks this as the primary production proxy."
}
```

## Minimal Example

```json
{
  "program_name": "Acme Whitebox",
  "program_url": "https://program.local/acme",
  "target_type": "whitebox",
  "focus_areas": ["Exchange", "Blockchain"],
  "scope_summary": "GitHub repos are in scope for authenticated whitebox review.",
  "in_scope": [
    "https://git.local/acme/api.git"
  ],
  "out_of_scope": [
    "Production customer data"
  ],
  "repo_urls": [
    "https://git.local/acme/api.git"
  ],
  "web_urls": [
    "https://app.acme.local"
  ],
  "api_urls": [
    "https://api.acme.local"
  ],
  "rpc_urls": [
    "https://rpc.acme.local"
  ],
  "smart_contracts": [
    {
      "name": "SettlementProxy",
      "chain": "Ethereum",
      "network": "mainnet",
      "address": "0x1234...",
      "explorer_url": "https://etherscan.local/address/0x1234..."
    }
  ],
  "rules": [
    "Stay inside staging."
  ],
  "raw_scope_notes": "Copied from the rendered scope table."
}
```

## Generated Layout

`audit-targets/<slug>/`

- `README.md`
- `scope/input.json`
- `scope/target.json`
- `scope/raw-scope-notes.md`
- `scope/summary.md`
- `scope/in-scope.md`
- `scope/out-of-scope.md`
- `scope/rules.md`
- `scope/program-notes.md`
- `scope/target-surface.md`
- `scope/smart-contracts.md`
- `scope/chain-inventory.json`
- `scope/protocol-archetype.md`
- `scope/proxy-topology.md`
- `scope/dependency-boundaries.md`
- `findings/README.md`
- `source/repos/`
- `source/artifacts/`
- `prep/asset-inventory.md`
- `prep/tried-and-ruled-out.md`
- `prep/finding-pipeline.md`
- `prep/bootstrap-summary.md`
- `prep/environment-readiness.md`
- `prep/environment-readiness.json`
- `prep/severity-conditions.md`
- `prep/attack-surface-map.md`
- `prep/protocol-invariants.md`
- `prep/web3-readiness.md`
- `prep/context-pack/`
- `prep/ready-for-bounty.md`

## Lane Routing

- `web` -> `bounty-program-web`
- `android` -> `bounty-program-mobile-android`
- `smart-contract` -> `bounty-program-smart-contracts`
- `native` -> `bounty-program-native`
- `whitebox` -> script fingerprints cloned source and suggests:
  - `bounty-program-web`
  - `bounty-program-native`
  - `bounty-program-smart-contracts`
  - or fallback `bounty-program-triage`

The generated `scope/target.json` also records:

- `surface_signals` - observed mix such as `web`, `smart-contract`, `wallet`, or `exchange`
- `follow_on_lanes` - any executable lanes that should stay in scope after the first deep pass
- `chain_inventory` - normalized network, contract, and dependency inventory for web3-heavy targets
- `protocol_archetype` - current archetype guess plus the reason it was chosen
- `dependency_boundaries` - off-chain and cross-surface trust edges that still matter
- `protocol_invariants` - initial invariants to preserve before exploit work
- `attack_surface_map` - public, privileged, callback, and dependency-centric attack surfaces
- `web3_readiness` - toolchain and replay readiness for smart-contract and hybrid web3 work
- `environment_readiness` - cross-lane local toolchain state, auto-setup actions, and remaining blockers before hunting

The generated `findings/README.md` defines the closed-loop per-finding bundle contract used by the standard pipeline:

- `claim.md`
- `scope-check.md`
- `facts.md`
- `facts-chain.md` for chain, market, tx, block, and contract identifiers on web3-heavy findings
- `poc.md`
- `impact.md`
- `impact-financials.md` for asset delta, capital assumptions, and solvency or settlement reasoning on web3-heavy findings
- `environment.md` for fork, staging, testnet, or static-only replay assumptions
- `reverify.md`
- `severity.md` for `TRUE POSITIVE` findings after severity triage
- `artifacts/`

The generated `prep/bootstrap-summary.md` is the hunting handoff contract and should summarize:

- active constraints
- decisive in-scope assets and out-of-scope reminders
- trust-boundary summary
- chosen primary lane
- follow-on lanes
- protocol archetype
- first three prioritized bug classes
- severity conditions that clear medium, high, and critical
- environment readiness status, active tool profiles, and remaining blockers
- auth or test-account state
- top endpoints, repos, binaries, APKs, contracts, or other assets
- toolchain and replay readiness for web3-heavy targets

The generated `prep/finding-pipeline.md` also uses explicit lifecycle states:

- `untested`
- `confirmed`
- `reverify-pending`
- `true-positive`
- `false-positive`
- `needs-more-evidence`
- `preverify-pending`
- `preverify-passed`
- `preverify-blocked`
- `report-ready`
- `reported`
