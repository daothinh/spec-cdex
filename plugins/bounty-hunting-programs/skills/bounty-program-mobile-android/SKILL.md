---
name: bounty-program-mobile-android
description: >
  Standard bug bounty workflow for Android applications. Use when the target is
  an APK, rooted-device session, Android backend client, hybrid mobile app, or
  Firebase-backed mobile target that needs static and dynamic testing.
---

# Bounty Program Mobile Android

This workflow is intentionally Android-specific because the Codex-ready mobile tooling in this repo centers on APKs and rooted-device testing.

Load these references on demand:
- `../../references/bounty-standard.md`
- `../../references/codex-ready-building-blocks.md`
- `../../references/android-framework-matrix.md`
- `../../references/report-checklist.md`

## Inputs

- APK or installed package name
- Rooted device or emulator access if dynamic testing is expected
- Proxy allowance and any testing account guidance
- Prior traffic captures or Burp project if one exists

## Workflow

1. Fingerprint the app stack using `android-framework-matrix.md`.
2. Start with static surface mapping:
   - manifest, exported components, deeplinks, webviews
   - embedded endpoints, keys, and Firebase configuration
   - storage locations and debug toggles
3. Reuse Codex-ready building blocks when installed:
   - `firebase-apk-scanner` for Firebase keys, project IDs, storage, and leaked mobile config
   - `workers-app-tester` for rooted-device traffic interception, UI driving, and Frida-based checks
   - `burpsuite-project-parser` when prior traffic evidence exists
   - `supply-chain-risk-auditor` for mobile dependency risk if source code is also in scope
4. Prioritize bug classes in this order:
   - IDOR and account-boundary failures in mobile flows
   - exported activity, service, or broadcast abuse
   - deep-link takeover, open redirects, or auth handoff bugs
   - WebView and JavaScript bridge trust
   - insecure local storage, logging, and clipboard exposure
   - Firebase misconfiguration and exposed backend resources
   - SSL pinning or root checks that collapse under runtime hooking
5. If the app mainly fronts a server-side repo that is also in scope, hand the backend portion to `bounty-program-web`.
6. Group findings by boundary failure instead of filing one report per screen.

## Rules

- Do not claim a mobile-only bug if the real issue is backend authorization.
- Use dynamic testing to confirm reachability whenever static analysis finds an interesting path.
- Keep the proof safe: avoid mass requests, destructive writes, or broad data extraction.
