# Workspace Contract

The bootstrap script expects one JSON object.

## Required Keys

- `program_name`
- `program_url`
- `target_type`

`target_type` must be `whitebox` or `android`.

## Optional Keys

- `slug`
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
- `artifacts`
- `artifact_urls`
- `package_names`
- `app_urls`
- `store_urls`
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

## Minimal Example

```json
{
  "program_name": "Acme Whitebox",
  "program_url": "https://program.local/acme",
  "target_type": "whitebox",
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
- `source/repos/`
- `source/artifacts/`
- `prep/asset-inventory.md`
- `prep/ready-for-bounty.md`

## Lane Routing

- `android` -> `bounty-program-mobile-android`
- `whitebox` -> script fingerprints cloned source and suggests:
  - `bounty-program-web`
  - `bounty-program-native`
  - `bounty-program-smart-contracts`
  - or fallback `bounty-program-triage`
