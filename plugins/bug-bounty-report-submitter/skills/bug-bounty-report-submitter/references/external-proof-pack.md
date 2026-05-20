# External Proof Pack

Use this for every report bundle. The gist-backed proof pack is mandatory because live form and email fields should not be the only place that carries the detailed runnable PoC, helper files, or captured logs.
The last clean replay must also be recorded with `asciinema`, saved locally, and uploaded before the report is considered ready.

This is the pattern visible in strong Cantina-style submissions:
- keep the main body self-contained
- show the exact bug location, exploit path, run command or replay sequence, and decisive output inline
- store the longer helper files, raw logs, or multi-file PoC in a stable secret link or markdown appendix

The secret gist itself should stay tight. Publish only:
1. the standalone PoC code files needed for re-check
2. the full report body
3. decisive output logs

## When To Create It

- every report needs a durable place for the full PoC, raw logs, and helper files
- the form has tight character limits
- the platform strips formatting and makes the PoC unreadable
- the PoC needs multiple files or long logs
- you need a stable replay pack for reviewer follow-up

## Local Proof-Pack Contents

The local `proof-pack/` should preserve:
- `poc.md`
- `report-appendix.md` when present
- decisive logs or output files
- helper PoC files already copied under `evidence/`
- `artifacts.json`
- replay metadata: run command, success signal, and file manifest

## Secret Gist Contents

Publish only the reviewer-critical subset, in this order:
1. standalone PoC replay files from `evidence/poc/` or equivalent evidence paths that the rerun actually needs
2. `report.md` as the full report body. If it is missing, fall back to `report-appendix.md`
3. output logs from `evidence/logs/` or equivalent evidence paths

Do not push manifests, index files, environment notes, severity notes, or generic evidence inventory into the gist unless the workflow is changed explicitly.
If the rerun needs helper configs, fixtures, ABI files, or support scripts, `poc.md` must name those files explicitly so the gist builder can include them in the first group.
If the replay still depends on source-tree `/test` or a borrowed repo harness, stop and fix the finding before building the proof pack.

## Build It

1. Finish `artifacts.json` and `evidence/` first.
2. Record the final clean replay first:

```powershell
asciinema --version
wsl bash -lc 'command -v asciinema && asciinema --version'
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/record_asciinema_replay.py `
  --finding-dir audit-targets/<slug>/findings/<finding-id> `
  --workdir <repo-or-target-dir> `
  --run-command "<exact replay command>" `
  --success-signal "<short decisive output>"
```

If both checks fail, stop.

3. Write the inline report body first.
4. If the channel is still too small, run:

```bash
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py \
  --bundle-dir bug-bounty-reports/<slug>/<finding-id> \
  --run-command "<exact replay command>" \
  --success-signal "<short decisive output>"
```

5. Publish a secret gist or provide an existing gist URL:

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

6. This creates:
- `proof-pack/`
- `external-evidence.json`
- a markdown index and manifest for the proof pack
7. Add the gist URL and the `asciinema` URL to the primary report body, then add an `external_proof` object to `submission.json` or `mail-envelope.json`, then run:

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
- `[https://gist.github.com/...](https://gist.github.com/...)`
- `[https://asciinema.org/a/...](https://asciinema.org/a/...)`

Bad:
- `See gist for the PoC.`
- `PoC is too long, attached elsewhere.`

## Non-Negotiables

- The body must still explain where the bug is, why it works, and how to replay it.
- The body must still contain the minimal run command or deterministic replay sequence.
- The body must still contain the decisive PoC output.
- The body must include the gist URL inline.
- The body must include the `asciinema` URL inline on the next non-empty line below the gist URL.
- Both URLs must use markdown link format with visible text equal to the URL.
- The gist must include the standalone PoC code file.
- The gist must include the decisive output-log file.
- The proof pack is for long helper files, raw logs, and multi-file replay support, not for hiding the main claim.
- Missing the gist reference in either the payload or the report body is a blocker and the report must not be submitted.
