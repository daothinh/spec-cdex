# External Proof Pack

Use this when the live form, mail client, or bug bounty portal cannot honestly hold the full runnable PoC, helper files, or captured logs.

This is the pattern visible in strong Cantina-style submissions:
- keep the main body self-contained
- show the exact bug location, exploit path, run command or replay sequence, and decisive output inline
- store the longer helper files, raw logs, or multi-file PoC in a stable secret link or markdown appendix

## When To Create It

- the form has tight character limits
- the platform strips formatting and makes the PoC unreadable
- the PoC needs multiple files or long logs
- you need a stable replay pack for reviewer follow-up

Do not create it just because you can.

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

4. This creates:
- `proof-pack/`
- `external-evidence.json`
- a markdown index and manifest for the proof pack

## Secret Gist Publishing

If the platform allows a reference URL and a secret link helps review, publish the pack:

```bash
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/prepare_external_proof_pack.py \
  --bundle-dir bug-bounty-reports/<slug>/<finding-id> \
  --run-command "<exact replay command>" \
  --success-signal "<short decisive output>" \
  --publish-gist
```

The script uses `gh gist create`. GitHub secret gists are the default; do not add `--public`.

## How To Reference It

Good:
- `Full runnable PoC, raw test output, and helper files are preserved in the linked secret gist. The inline report below includes the vulnerable function, replay command, and decisive output.`

Bad:
- `See gist for the PoC.`
- `PoC is too long, attached elsewhere.`

## Non-Negotiables

- The body must still explain where the bug is, why it works, and how to replay it.
- The body must still contain the minimal run command or deterministic replay sequence.
- The body must still contain the decisive PoC output.
- The proof pack is for long helper files, raw logs, and multi-file replay support, not for hiding the main claim.
