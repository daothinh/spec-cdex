# Asciinema Replay

Use this for the last clean reverify rerun and the final PoC validation. It is mandatory.

## Hard Stop

Check `asciinema` on the system first. Prefer native PATH. Use WSL only as fallback or for local testing in this environment:

```powershell
asciinema --version
wsl bash -lc 'command -v asciinema && asciinema --version'
```

If both checks fail, stop immediately. Do not draft or submit.

## Record The Final Replay

Run the replay from the real working directory, not from memory:

```powershell
python plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/scripts/record_asciinema_replay.py `
  --finding-dir audit-targets/<slug>/findings/<finding-id> `
  --workdir <repo-or-target-dir> `
  --run-command "<exact replay command>" `
  --success-signal "<short decisive output>"
```

This writes:
- `artifacts/asciinema/reverify-session.cast`
- `artifacts/asciinema/asciinema-session.json`

The script:
- checks native `asciinema` first, then WSL as fallback
- records the replay locally
- prints each replay command before executing it, so the cast starts at the first PoC command instead of only showing the final output
- uploads the cast to `asciinema`
- saves the returned `https://asciinema.org/a/...` URL

## Carry It Into The Report Bundle

After `prepare_report_artifacts.py`, the recording should exist under:
- `evidence/asciinema/reverify-session.cast`
- `evidence/asciinema/asciinema-session.json`

`prepare_external_proof_pack.py` now blocks if that metadata is missing.

## Link Block In The Report

Place the reference URLs in this order and format:

```md
PoC and logs: [https://gist.github.com/...](https://gist.github.com/...)
PoC runtime: [https://asciinema.org/a/...](https://asciinema.org/a/...)
```

Rules:
- use one line per reference
- keep the descriptive prefix before the URL
- use markdown link format for the URL
- visible text must equal the URL
- place the `asciinema` link on the next non-empty line under the gist link
- keep both links in the opening summary or intro paragraph
- keep both links in the main report body, not only in metadata or attachments
