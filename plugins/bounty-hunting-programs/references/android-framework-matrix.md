# Android Framework Matrix

This plugin is intentionally Android-specific because the current Codex-ready tooling in this repo targets APKs and rooted-device testing.

| Stack | Signals | Priority Surfaces | Preferred Building Blocks |
| --- | --- | --- | --- |
| Native Android (Java/Kotlin) | `AndroidManifest.xml`, `classes*.dex`, AndroidX packages | exported components, intent filters, local storage, WebViews, auth flows | `workers-app-tester`, `firebase-apk-scanner`, `burpsuite-project-parser` |
| Flutter | `libapp.so`, `flutter_assets`, Dart symbols | API endpoints in assets, deeplinks, WebViews, Firebase config, insecure storage | `workers-app-tester`, `firebase-apk-scanner` |
| React Native | JS bundles, Hermes bytecode, RN package names | JS bridge exposure, auth state sync, deep links, local storage, embedded keys | `workers-app-tester`, `firebase-apk-scanner` |
| Cordova / Capacitor / Hybrid | `www/`, web assets, bridge plugins | WebView origin trust, JS bridges, deep links, file exposure, token storage | `workers-app-tester`, `burpsuite-project-parser` |

## Common Bug Classes

- IDOR and broken object-level authorization
- Exported activity/service/broadcast abuse
- SSL pinning or root checks that are bypassable
- Firebase exposure and debug config leakage
- WebView bridge abuse
- Deep-link hijacking or open redirect style handoff bugs
- Insecure local storage, logging, and clipboard leakage
