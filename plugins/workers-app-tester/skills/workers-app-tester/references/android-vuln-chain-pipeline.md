# Android Vulnerability Chain Pipeline

Use this reference when a single Android signal is not enough and the work needs
to become a replayable vulnerability chain.

## Pipeline

1. Establish the lab state.
2. Identify the package, launch activity, user role, and current auth state.
3. Start capture with `scripts/mitm_watch.py start --package <package> --session-dir <dir> --preserve-auth`.
4. Run the UI loop: observe with `scripts/ui.py`, act with ADB, inspect with `scripts/traffic.py`.
5. Run static reverse review for endpoints, exported components, deeplinks, storage, and hardcoded secrets.
6. Use Frida only when runtime behavior blocks observation or proof.
7. Convert every candidate into a chain: attacker capability -> controlled input -> broken boundary -> observed consequence.
8. Keep only chains with evidence that survives a negative control.

## Attack Surface Ranking

Prioritize in this order:

- Backend API authorization reached from the app.
- Session, tenant, account, or role confusion across captured requests.
- Deeplinks and exported components that route into authenticated screens or privileged actions.
- WebView bridge, custom scheme, file access, or JavaScript interface exposure.
- Local token, key, database, log, or clipboard exposure.
- SSL pinning or root-detection bypass only when it unlocks higher-value evidence.

## Recon Checklist

- Package name, version, installer source, and signing certificate.
- Launch activity and exported activities, services, receivers, and providers.
- Auth state and available test roles.
- Hosts discovered from APK strings, manifest, assets, resources, and live traffic.
- Deeplink schemes and path patterns.
- Local storage paths that contain tokens, PII, or feature flags.
- Runtime protections: SSL pinning, root detection, anti-debug, emulator checks.

## Runtime Instrumentation

Use Frida to answer a narrow question:

- Which method builds or signs the request?
- Which pinning or trust manager blocks capture?
- Which root/emulator check changes control flow?
- Which local secret, token, or feature flag is read before the sensitive request?

Do not keep broad hooks running after the question is answered. Record hook
script path, target method, input, and observed return value.

## Chain Assembly

Each chain should include:

- Initial attacker position: logged-out, normal user, second account, rooted device, or malicious app.
- Decisive input: request field, ID, intent extra, deeplink, file, local setting, or runtime return value.
- Intended security control: ownership check, role check, signature, token binding, app-link verification, or storage isolation.
- Failure: exact place the control is missing, bypassed, or applied too late.
- Observed consequence: unauthorized read/write, token disclosure, privilege transition, or backend state change.
- Negative control: same path with blocker restored, wrong role, different ID, or missing prerequisite.

## Evidence Layout

Save evidence under the target finding bundle:

- `artifacts/android/traffic.jsonl` for relevant capture slices.
- `artifacts/android/requests.md` for decisive request/response summaries.
- `artifacts/android/frida/` for hook scripts and output.
- `artifacts/android/static/` for manifest, deeplink, exported component, or storage findings.
- `poc.md` with exact package, session setup, ADB steps, payload, and success signal.

## Stop Conditions

Stop or downgrade when:

- The proof only shows client-side tampering with no server-side consequence.
- The sensitive data is already public or belongs to the same authenticated user.
- A non-attacker-controlled signature, preimage, admin action, or backend worker is still required.
- The path needs destructive actions outside scope.
