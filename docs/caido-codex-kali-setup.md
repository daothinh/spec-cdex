# Caido + Codex + Chrome on Kali

This repo now includes a bootstrap flow for Kali that covers the missing runtime
pieces around the existing `caido-mode` skill:

- system install of Caido desktop/CLI and repo dependencies
- reuse of an existing user-level Node.js/npm toolchain when installed via `nvm`
- Codex PAT bootstrap for `plugins/caido/skills/caido-mode`
- manual export of PAT, proxy, and certificate values for Chrome setup
- optional Chrome/Chromium CA certificate import into the Linux NSS shared DB
- a Chrome launcher that can either use a dedicated profile or reuse one of your
  existing Chrome profiles through Caido

## Recommended Flow

### 1. Run the bootstrap script

```bash
bash scripts/install-caido-kali-latest.sh --choose-profile
```

This all-in-one path:

- installs Caido desktop + CLI
- reuses `node`/`npm` from your existing `nvm` setup when available
- bootstraps `plugins/caido/skills/caido-mode`
- launches Caido locally
- downloads the local `ca.crt` automatically when possible
- optionally lets you reuse an existing Chrome profile

Interactive mode will pause once Caido launches so you can:

1. log in and create/open a project
2. create a PAT at `https://dashboard.caido.io/developer`

The script then:

- saves the PAT through the repo wrapper setup
- exports manual setup artifacts under `~/.codex/caido/`

By default, `install-caido-kali-latest.sh` continues into the setup flow and
imports the certificate into Chrome automatically. If you only want the setup
portion later, run:

```bash
bash scripts/setup-caido-codex-kali.sh --skip-install --import-cert --choose-profile
```

The bootstrap writes:

- `~/.codex/caido/manual-setup.env`
- `~/.codex/caido/manual-setup.txt`

If you ran `install-caido-kali-latest.sh` without `--choose-profile`, the setup
does not bind to any existing Chrome profile. `launch-caido-chrome.sh` will use
the dedicated profile directory `~/.config/caido-codex-chrome` until you rerun
setup with `--choose-profile` or pass `--chrome-user-data-dir`.

### Manual Chrome step

Chrome does not need a special Caido extension for HTTPS interception.

What you actually need is:

1. trust the Caido root certificate in Chrome
2. run Chrome through the Caido proxy

For trust, open `chrome://certificate-manager/`, go to `Installed by you`, and
import the downloaded `ca.crt` into `Trusted Certificates`.

For proxying, either use the repo launcher:

```bash
bash scripts/launch-caido-chrome.sh
```

or launch Chrome manually:

```bash
google-chrome-stable --proxy-server=127.0.0.1:8080 --proxy-bypass-list="<-loopback>"
```

If you selected an existing Chrome profile during setup, the launcher will reuse
that profile automatically. If not, it falls back to a dedicated Caido-only
Chrome profile under `~/.config/caido-codex-chrome`.

### 2. List or choose Chrome profiles

```bash
bash scripts/setup-caido-codex-kali.sh --list-profiles
bash scripts/setup-caido-codex-kali.sh --skip-install --import-cert --choose-profile
```

Detected profiles are resolved from Chrome/Chromium's `Local State` and can be
reused by saving:

- `CAIDO_CHROME_USER_DATA_DIR`
- `CAIDO_CHROME_PROFILE_DIRECTORY`

into `~/.codex/caido/manual-setup.env`.

### 3. Launch Chrome through Caido

```bash
bash scripts/launch-caido-chrome.sh
```

The launcher always applies:

- `--proxy-server=127.0.0.1:8080`
- `--proxy-bypass-list="<-loopback>"`

If a profile was selected, it also applies that profile's `--user-data-dir` and
`--profile-directory`. Close other Chrome windows using the same profile first
to avoid profile lock conflicts.

### 4. Verify the Codex wrapper

```bash
bash plugins/caido/skills/caido-mode/scripts/caido health
bash plugins/caido/skills/caido-mode/scripts/caido recent --limit 5
```

## Non-Interactive / Codex-Friendly Mode

If you already have a PAT, Codex can finish the setup without stopping:

```bash
bash scripts/setup-caido-codex-kali.sh \
  --pat caido_xxxxx \
  --import-cert \
  --chrome-user-data-dir "$HOME/.config/google-chrome" \
  --chrome-profile-directory Default
```

## Export Values Again Later

If you want to regenerate the manual setup files without rerunning the installer:

```bash
bash scripts/export-caido-manual-setup.sh \
  --pat caido_xxxxx \
  --ca-cert "$HOME/.codex/caido/caido-ca.crt" \
  --chrome-user-data-dir "$HOME/.config/google-chrome" \
  --chrome-profile-directory Default
```

## Standalone Certificate Import

If Caido is already installed and you only need Chrome trust:

```bash
bash scripts/import-caido-chrome-cert.sh --cert "$HOME/Downloads/ca.crt"
```

The script imports into Chromium's Linux NSS shared DB path. Chromium currently
documents `$HOME/.local/share/pki/nssdb` as the default NSS DB, while older
setups may still use `$HOME/.pki/nssdb`.

## Playwright MCP Integration

If your active Chrome profile already has Playwright MCP-related state or
extensions, reusing that profile is the simplest route:

1. run `setup-caido-codex-kali.sh --skip-install --import-cert --choose-profile`
2. choose the Chrome profile you already use
3. close other Chrome windows for that profile
4. launch it again through `bash scripts/launch-caido-chrome.sh`
5. let Playwright MCP attach to or automate that proxied browser session

This keeps the browser automation layer in Playwright while Caido handles
traffic capture, search, replay, and evidence export.

## Practical Recommendation

For the first run:

1. use `install-caido-kali-latest.sh --choose-profile`
2. read `~/.codex/caido/manual-setup.txt`
3. if you want the least friction, let the scripts import the cert for you
4. if you want your own Chrome profile, select it during setup and relaunch it through `launch-caido-chrome.sh`

That keeps Caido for interception and request history, while the Codex wrapper
handles replay/search/findings from the terminal.
