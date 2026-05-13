---
name: workers-app-tester
description: >-
  Test Android apps on a rooted device. Decompile APKs, intercept traffic,
  parse UI, test for IDORs, bypass SSL pinning, hook methods with Frida,
  inspect exported components, read local storage, and find sensitive data.
  Use when asked to "test this app", "find bugs", "pentest", "reverse
  engineer", "decompile", "intercept requests", "check for IDORs", "bypass
  cert pinning", "hook this method", or "check deeplinks".
metadata:
  author: workers.io
  version: "3.0.0"
---

# Workers App Tester

Pentest Android apps through a rooted device. Drives the device UI, intercepts network traffic, and uses Frida for runtime analysis.

For detailed guides, load these on demand:
- [references/testing-methodology.md](references/testing-methodology.md) — IDOR, auth, exposure, local storage, deeplinks, exported components, logging
- [references/android-vuln-chain-pipeline.md](references/android-vuln-chain-pipeline.md) — end-to-end Android recon mindset, runtime instrumentation, attack-surface ranking, and vuln-chain assembly
- [references/frida.md](references/frida.md) — SSL bypass, root bypass, codeshare scripts, hooking patterns, custom certs
- [agents/reverse-agent.md](references/agents/reverse-agent.md) — APK decompilation sub-agent, reads codebase for endpoints, secrets, components

## Session Setup

This workflow assumes the Android lab is already prepared:
- rooted device or emulator is stable
- `adb shell settings get global http_proxy` already points at port `18088`
- the MITM CA certificate is already installed on the device
- the host uses the default mitmproxy config at `C:\Users\emet\.mitmproxy\config.yaml`

### 1. Pick the target

```bash
adb shell pm list packages -3
adb shell dumpsys activity activities | grep -m 1 -E 'topResumedActivity=|ResumedActivity:|mFocusedApp='
```

### 2. Create session directory

```bash
SESSION_DIR=/tmp/workers-app-tester-$(date +%Y%m%d-%H%M%S)
mkdir -p "$SESSION_DIR"
```

### 3. Verify the preconfigured transport path

```bash
python3 scripts/mitm_watch.py verify
```

Expected:
- the proxy value still points at port `18088`
- `su -c id` returns `uid=0`
- the mitmproxy CA hash is present in the Android cert store
- the host config does not contain a blanket catch-all bypass with no monitored hosts

If verification says the config is still bypassing everything, patch it before launching the app.

### 4. Start traffic interception

The capture helper now seeds hosts automatically from the installed package APK on the device. Start there before doing any manual host curation.

```bash
python3 scripts/mitm_watch.py start \
  --session-dir "$SESSION_DIR" \
  --package "<package>" \
  --preserve-auth
```

What this does:
- pulls the base APK for `<package>` from the device
- extracts host candidates from APK strings, manifest, assets, raw resources, and printable binary strings
- updates `C:\Users\emet\.mitmproxy\config.yaml`
- removes the blanket `ignore_hosts` rule that bypasses everything
- adds the discovered hosts to `allow_hosts`
- keeps only narrow system-noise bypasses in `ignore_hosts`
- starts `mitmdump` in the background with `capture.py`

If you already have extra hosts from reverse work, append them explicitly:

```bash
python3 scripts/mitm_watch.py start \
  --session-dir "$SESSION_DIR" \
  --package "<package>" \
  --host "api.example.com" \
  --host "auth.example.com" \
  --preserve-auth
```

If APK seeding still looks incomplete, do a short census pass:

```bash
python3 scripts/mitm_watch.py start \
  --session-dir "$SESSION_DIR" \
  --package "<package>" \
  --capture-all \
  --preserve-auth
```

Exercise login/home/API-heavy paths for 1-2 minutes, then merge newly seen hosts from traffic:

```bash
python3 scripts/mitm_watch.py configure \
  --traffic "$SESSION_DIR/traffic.jsonl"
```

### 5. Launch the app

```bash
adb shell am force-stop <package> || true
adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1
```

### 6. If no HTTPS traffic appears

Assume the proxy and certificate path are already correct. Missing HTTPS traffic now usually means SSL pinning. See [references/frida.md](references/frida.md) — start frida-server, then spawn the app with `bypass.js`.

### Recovery only if the proxy drifted

Emulator:

```bash
adb shell settings put global http_proxy 10.0.2.2:18088
```

Physical device:

```bash
adb shell settings put global http_proxy <host-ip>:18088
```

If the proxy is fine but config scope is wrong, patch only the monitored hosts:

```bash
python3 scripts/mitm_watch.py configure --host "api.example.com" --host "auth.example.com"
```

You can also rebuild the allowlist from APK or traffic evidence instead of typing hosts by hand:

```bash
python3 scripts/mitm_watch.py configure --package "<package>"
python3 scripts/mitm_watch.py configure --traffic "$SESSION_DIR/traffic.jsonl"
```

## Static Analysis

Dispatch to the **reverse-agent** with the package name and session directory. It will:
1. Pull the APK from the device
2. Decompile with apktool (manifest, smali, resources)
3. Grep for hardcoded secrets, API endpoints, security anti-patterns
4. Read through interesting files for deeper context

Returns: exported components, deeplink schemes, API endpoints, hardcoded secrets, security issues.

Use these findings to drive targeted testing in The Loop.

## The Loop

### 1. Observe

```bash
python3 scripts/ui.py
```

Returns a compact numbered list of interactive elements:

```
[1] "Sign In" btn @ (540,1200) bounds=[380,1150][700,1250] clickable
[2] "Email" input @ (540,400) bounds=[100,350][980,450] focusable
```

### 2. Act

One action per cycle. Tap element [1]:

```bash
adb shell input tap 540 1200
```

For text fields, tap then type:

```bash
adb shell input tap 540 400
adb shell input text "test@example.com"
```

### 3. Intercept

```bash
python3 scripts/traffic.py --input "$SESSION_DIR/traffic.jsonl" --since-seconds 15 --limit 10
```

With headers and bodies:

```bash
python3 scripts/traffic.py --input "$SESSION_DIR/traffic.jsonl" --since-seconds 15 --show-headers --show-body
```

### 4. Decide next step and repeat

## Security Analysis

After exercising the app's main flows, run the analyzer:

```bash
python3 scripts/analyze.py --input "$SESSION_DIR/traffic.jsonl" --mode full
```

Individual modes: `endpoints`, `idor`, `auth`, `exposure`, `headers`.

See [references/testing-methodology.md](references/testing-methodology.md) for what to do with each finding.

## ADB Reference

| Action      | Command                                              |
|-------------|------------------------------------------------------|
| Tap         | `adb shell input tap <x> <y>`                        |
| Type        | `adb shell input text "hello%sworld"` (%s = space)   |
| Scroll down | `adb shell input swipe 540 1500 540 500 300`         |
| Scroll up   | `adb shell input swipe 540 500 540 1500 300`         |
| Back        | `adb shell input keyevent KEYCODE_BACK`              |
| Home        | `adb shell input keyevent KEYCODE_HOME`              |
| Enter       | `adb shell input keyevent KEYCODE_ENTER`             |
| Long press  | `adb shell input swipe <x> <y> <x> <y> 1000`        |
| Launch app  | `adb shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1` |
| Force stop  | `adb shell am force-stop <pkg>`                      |

## Session Teardown

```bash
python3 scripts/mitm_watch.py stop --session-dir "$SESSION_DIR"
adb shell "su -c 'pkill frida-server'" 2>/dev/null || true
```

Do not clear the global proxy in a preconfigured lab unless you intentionally want to reset the device network path.

## Rules

- One UI action per cycle. Observe, act, intercept, then decide.
- Always run `ui.py` before acting so coordinates match the current screen.
- Always tear down the session when done, but leave the preconfigured proxy state alone unless you are intentionally resetting the device.
- Prefer the package-seeded host list first, then widen only when evidence says you need more coverage.
- If reverse-derived hosts look incomplete, do a brief `--capture-all` census and immediately convert the observed hosts back into a narrower allowlist.
- Document findings: endpoint, vulnerability type, reproduction steps, evidence.
- NEVER use `sleep` in any command. No `sleep 1`, no `sleep 2`, no `sleep && command`. Run commands directly. `ui.py` handles its own timing. Chain with `&&` if needed.
- Be fast. No unnecessary delays between actions.

## Bundled Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ui.py` | Smart UI parser. Filters to interactive elements with spatial dedup. |
| `scripts/mitm_watch.py` | Verify proxy/root/cert trust, patch `config.yaml`, and start/stop `mitmdump`. |
| `scripts/capture.py` | mitmproxy addon. Logs to JSONL. Set `PRESERVE_AUTH=1` to keep auth headers. |
| `scripts/traffic.py` | Traffic viewer. `--since-seconds`, `--show-headers`, `--show-body`. |
| `scripts/analyze.py` | Security analyzer. Modes: `endpoints`, `idor`, `auth`, `exposure`, `headers`, `full`. |
| `scripts/bypass.js` | SSL pinning bypass. TrustManagerImpl, OkHttp3, SSLContext, Conscrypt. |
