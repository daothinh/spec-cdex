# workers-app-tester

Test Android apps on a rooted device. Give a coding agent access to a phone — it observes the screen, taps buttons, intercepts traffic, and finds vulnerabilities autonomously.

## Requirements

- Rooted Android device or emulator (Magisk via [rootAVD](https://gitlab.com/newbit/rootAVD))
- ADB connected
- [mitmproxy](https://mitmproxy.org/) installed
- [Frida](https://frida.re/) installed (for SSL pinning bypass)
- Python 3.10+
- Stable lab defaults are supported: Android global proxy already on port `18088`, CA certificate already installed, mitmproxy config at `C:\Users\emet\.mitmproxy\config.yaml`

## What's included

| File | Purpose |
|------|---------|
| `scripts/ui.py` | Parse UI hierarchy into numbered interactive elements |
| `scripts/mitm_watch.py` | Verify proxy/root/cert trust, patch `config.yaml`, and manage `mitmdump` |
| `scripts/mitm_config.py` | Shared host discovery and mitmproxy config helpers used by `mitm_watch.py` |
| `scripts/capture.py` | mitmproxy addon — logs HTTP flows to JSONL |
| `scripts/traffic.py` | Summarize recent traffic by time window |
| `scripts/analyze.py` | Security analyzer — IDORs, auth, exposure, headers |
| `scripts/bypass.js` | Frida SSL pinning bypass (8 hook targets) |
| `references/frida.md` | Frida setup, codeshare scripts, hooking patterns |
| `references/testing-methodology.md` | What to do with each finding type |
| `references/android-vuln-chain-pipeline.md` | Android recon-to-vulnerability-chain mindset and operator checklist |
| `references/agents/reverse-agent.md` | APK decompilation sub-agent |

## Install

```bash
npx skills add workersio/spec
```

## Usage

Tell the agent to test an app:

```
Test com.example.app. creds: user@example.com / password123
```

The agent will verify the existing proxy/cert path, pull the APK from the connected device to seed host discovery, patch `C:\Users\emet\.mitmproxy\config.yaml`, start `mitmdump`, launch the app, login, intercept traffic, and find vulnerabilities.

## The loop

1. **Observe** — dump the screen with `ui.py`, get a numbered list of interactive elements
2. **Act** — tap, type, or scroll via ADB
3. **Intercept** — read the traffic that action produced with `traffic.py`
4. **Decide** — pick the next action based on what it sees

Repeat until done.
