---
name: kage
description: >
  Run a local pentest sandbox in Docker for black-box, greybox, or
  white-box security audits. Triggers on "kage", "pentest",
  "security audit on", and "audit the security of". Uses the bundled
  Kali sidecar and writes artifacts under `./results/<target>/`.
metadata:
  author: workers.io
  version: "0.1.0"
---

# Kage — Codex port

Use Kage when active testing should happen inside the bundled Kali
sidecar, not on the host. The Codex port keeps the same container and
probe scripts, but runs as a **single-agent workflow by default**. The
`agents/` docs remain useful as checklists and prompt contracts, but
they are optional references rather than a hard dependency.

## Modes

- `kage <target>` — black-box engagement against a domain, URL, or wildcard
- `kage recon-only <target>` — recon and vuln scan only
- `kage greybox <target> <source-path>` — black-box plus local source context
- `kage audit <local path>` — source-driven review with containerized helpers when useful

## Essential rules

- Run active scanners and PoCs through the Kage sidecar. Do not spray
  host-installed pentest tools directly unless the sidecar is clearly unavailable.
- Prefer direct script and tool execution over subagent orchestration.
- Keep every artifact under `results/<target>/` so the engagement is reproducible.
- Apply [`references/judging.md`](references/judging.md) before writing or keeping a PoC.
- Change one variable at a time. If a path stalls after 2–3 real attempts, pivot and record the ruled-out path.

## Shell setup

Treat `$K` below as the shell-appropriate shim command:

- Bash / zsh: `"{baseDir}/scripts/k"`
- PowerShell on Windows: `& (Join-Path "{baseDir}" "scripts/k.ps1")`

Warm the sandbox first. If Docker is missing or the daemon is down, stop
and surface the exact error.

## Phase 1 — Bootstrap

Entry:
- user supplied a target or local source path
- Docker should be available

Actions:
1. Resolve the mode: `blackbox`, `recon-only`, `greybox`, or `audit`.
2. Normalize the target slug for `results/<target>/`.
3. Run the Kage shim with `whoami` to bootstrap the container.
4. Create:
   - `results/<target>/recon`
   - `results/<target>/vulns`
   - `results/<target>/testing`
   - `results/<target>/exploits`
   - `results/<target>/chains`
   - `results/<target>/verification`
   - `results/<target>/judging`
   - `results/<target>/reports`
5. Read `./creds.md` if present. If authenticated testing is required and
   the file is missing, surface the gap and continue only with unauthenticated work.
6. Write `results/<target>/engagement.json` with:
   - `target`
   - `scope_type`
   - `started_at`
   - `rules_of_engagement`

Greybox add-on:
- Load [`references/audit-context-building/SKILL.md`](references/audit-context-building/SKILL.md).
- Build `results/<target>/context.md` with trust boundaries, auth flow,
  high-value entry points, sensitive parameters, and any data that the client
  should never legitimately receive.
- The bundled reference still mentions Claude in a few places; read that as
  "the current coding agent".

Exit:
- container is healthy
- engagement tree exists
- `engagement.json` exists

## Phase 2 — Recon

Entry:
- Phase 1 completed

Actions:
1. Run the discovery pipeline in the sidecar and save:
   - `recon/subs.txt`
   - `recon/live.txt`
   - `recon/wayback.txt`
   - `recon/crawl.txt`
   - `recon/dorks.json`
2. Run port scanning from the sidecar against live hosts and save under
   `recon/ports/` or `recon/ports.txt`.
3. Run nuclei and save `vulns/nuclei.txt`.
4. If `GITHUB_TOKEN` is available and the target looks organization-backed,
   run `scripts/gitmail.py` and save `recon/github.json`.
5. Write `recon/summary.md` covering:
   - subdomain count
   - live host count
   - high-value ports
   - nuclei severity counts and top hits
   - auth endpoints
   - object-ID-bearing endpoints
   - URL-accepting parameters
   - obvious JS bundle or secret surfaces

Helpful commands:

```bash
"$K" bash -lc 'cd /workspace && R="results/<target>" && \
  (subfinder -d "<target>" -silent | tee "$R/recon/subs.txt" | \
    httpx -silent -title -tech-detect -status-code | tee "$R/recon/live.txt") & \
  (gau --subs "<target>" > "$R/recon/wayback.txt") & \
  (until [ -s "$R/recon/live.txt" ]; do sleep 1; done; \
    katana -u "$R/recon/live.txt" -d 3 -jc -silent -o "$R/recon/crawl.txt") & \
  (python3 /skill/scripts/dorks.py -d "<target>" --output "$R/recon/dorks.json") & \
  wait'
```

```bash
"$K" bash -lc 'cd /workspace && LIVE="results/<target>/recon/live.txt" && \
  [ -s "$LIVE" ] && cut -d" " -f1 "$LIVE" | sort -u | \
  xargs -r -n1 -P4 -I{} nmap -Pn -T4 -p- --min-rate 1000 "{}" -oN "results/<target>/recon/ports-{}.txt"'
```

```bash
"$K" bash -lc 'cd /workspace && nuclei -l results/<target>/recon/live.txt -o results/<target>/vulns/nuclei.txt'
```

Exit:
- recon artifacts exist
- `recon/summary.md` exists
- if mode is `recon-only`, stop here

## Phase 3 — Focused testing

Entry:
- Phase 2 completed

Actions:
1. Read [`references/methodology.md`](references/methodology.md).
2. Decide which attack classes are actually triggered by recon.
3. Run direct probes into `testing/<class>/` instead of delegating by default:
   - auth / header bypass → `scripts/authbypass.py`
   - IDOR / BOLA → `scripts/idor.py`
   - access-control diffing → `scripts/diff.py`
   - SSRF → `scripts/ssrf.py`
   - CORS / header issues → `scripts/cors.py`, `scripts/headers.py`
   - race conditions → `scripts/race.py`
   - WAF-sensitive HTTP checks → `scripts/tls.py`
   - Cloudflare / JS gate paths → `scripts/browser.py`
   - directory / parameter fuzzing → sidecar tools such as `ffuf`, `dirsearch`, `sqlmap`, `dalfox`, `nuclei`
4. For JS bundles, scan crawled assets and downloaded source with `rg` for keys,
   secrets, internal URLs, GraphQL operations, and auth hints.
5. Keep a live inventory of candidate findings and a `tried-and-ruled-out` list.
6. In greybox mode, bias testing toward weaknesses implied by `context.md`.

Rules:
- The 5-minute rule applies: if a lead does not sharpen quickly, move on.
- Use the bundled `agents/*.md` files only as checklists or prompt contracts if you
  explicitly choose to delegate in a different environment.
- Do not keep generic scanner noise as findings.

Exit:
- each triggered class has either a result artifact or a ruled-out note
- candidate findings are reduced to concrete, reproducible leads

## Phase 4 — Exploit, verify, and judge

Entry:
- Phase 3 produced concrete leads

Actions:
1. Apply the 4-check gate in [`references/judging.md`](references/judging.md).
2. Drop low-signal items before building any PoC.
3. For each surviving lead, write a runnable PoC under `exploits/`.
4. Re-run each PoC from a clean session at least 3 times and save outputs under
   `verification/F<NNN>/`.
5. Build `verification/verified_findings.json`.
6. Read [`references/chains.md`](references/chains.md) and look for meaningful finding chains.
7. Write:
   - `judging/approved_findings.json`
   - `judging/judgment.md`
   - `judging/dropped_findings.md`

Requirements:
- A finding is not real until it reproduces cleanly.
- A PoC must include target, payload construction, request flow, and output.
- If `tls.py` gets blocked, retry with a rotated impersonation or switch to `browser.py`.

Exit:
- only verified findings survive
- rejected findings are documented with reasons

## Phase 5 — Report

Entry:
- approved findings exist, or the engagement is conclusively clean

Actions:
1. Use [`references/audit-report-template.md`](references/audit-report-template.md)
   as the structure for `results/<target>/audit-report.md`.
2. Fill the template directly; do not leave placeholders in the final file.
3. Order findings by severity, then by exploit reliability.
4. Include concise reproduction steps, decisive evidence, and concrete remediation.
5. Print a short summary table for the user after the report is written.

Exit:
- `results/<target>/audit-report.md` exists
- supporting artifacts stay in `results/<target>/`

## Failure modes to surface

- Docker not installed or not running
- target unreachable or DNS dead
- rate-limited or WAF-blocked path that needs slower pacing or browser fallback
- missing `creds.md` when authenticated testing is required
- missing external dependency inside the sidecar that blocks a named probe

## Load on demand

- [`references/methodology.md`](references/methodology.md) — trigger matrix and concrete probe commands
- [`references/judging.md`](references/judging.md) — filter, severity, and exclusion rules
- [`references/chains.md`](references/chains.md) — escalation-chain patterns
- [`references/report-formatting.md`](references/report-formatting.md) — platform conventions
- [`references/audit-report-template.md`](references/audit-report-template.md) — final report skeleton
- [`references/tools.md`](references/tools.md) — sidecar tool inventory
- [`references/audit-context-building/SKILL.md`](references/audit-context-building/SKILL.md) — greybox methodology
- [`references/agentmail/SKILL.md`](references/agentmail/SKILL.md) — disposable inboxes when multi-account signup matters
- [`assets/creds.sample.md`](assets/creds.sample.md) — credentials and scope template
- [`assets/wordlist-strategy.md`](assets/wordlist-strategy.md) — target-specific wordlist guidance
