# External Proof Pack

Use this for every report bundle. The gist-backed proof pack is mandatory because live form and email fields should not be the only place that carries the detailed runnable PoC, helper files, or captured logs.

This is the pattern visible in strong Cantina-style submissions:
- keep the main body self-contained
- show the exact bug location, exploit path, run command or replay sequence, and decisive output inline
- store the longer helper files, raw logs, or multi-file PoC in a stable secret link or markdown appendix

## When To Create It

- every report needs a durable place for the full PoC, raw logs, and helper files
- the form has tight character limits
- the platform strips formatting and makes the PoC unreadable
- the PoC needs multiple files or long logs
- you need a stable replay pack for reviewer follow-up

## Minimum Contents

The proof pack should preserve:
- `poc.md`
- `report-appendix.md` when present
- decisive logs or output files
- helper PoC files already copied under `evidence/`
- `artifacts.json`
- replay metadata: run command, success signal, and file manifest

## Build It

1. Finish `artifacts.json` and `evidence/` first.
2. Write the inline report body first.
3. If the channel is still too small, run:

```bash
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py \
  --bundle-dir bug-bounty-reports/<slug>/<finding-id> \
  --run-command "<exact replay command>" \
  --success-signal "<short decisive output>"
```

4. Publish a secret gist or provide an existing gist URL:

```bash
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py \
  --bundle-dir bug-bounty-reports/<slug>/<finding-id> \
  --run-command "<exact replay command>" \
  --success-signal "<short decisive output>" \
  --publish-gist
```

Or:

```bash
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py \
  --bundle-dir bug-bounty-reports/<slug>/<finding-id> \
  --run-command "<exact replay command>" \
  --success-signal "<short decisive output>" \
  --gist-url "https://gist.github.com/..."
```

5. This creates:
- `proof-pack/`
- `external-evidence.json`
- a markdown index and manifest for the proof pack
6. Add the gist URL to the primary report body, then add an `external_proof` object to `submission.json` or `mail-envelope.json`, then run:

```bash
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/validate_submission_bundle.py \
  --bundle-dir bug-bounty-reports/<slug>/<finding-id> \
  --channel form
```

Use `--channel email` for disclosure mail.

The script uses `gh gist create`. GitHub secret gists are the default; do not add `--public`.

## How To Reference It

Good:
- `Full runnable PoC, raw test output, and helper files are preserved in the linked secret gist. The inline report below includes the vulnerable function, replay command, and decisive output.`
- `Detailed PoC, replay logs, and helper files are in the secret gist: https://gist.github.com/...`

Bad:
- `See gist for the PoC.`
- `PoC is too long, attached elsewhere.`

## Non-Negotiables

- The body must still explain where the bug is, why it works, and how to replay it.
- The body must still contain the minimal run command or deterministic replay sequence.
- The body must still contain the decisive PoC output.
- The body must include the gist URL inline.
- The proof pack is for long helper files, raw logs, and multi-file replay support, not for hiding the main claim.
- Missing the gist reference in either the payload or the report body is a blocker and the report must not be submitted.
