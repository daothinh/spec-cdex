from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


WEB3_TOOL_GUIDANCE = {
    "slither": {
        "label": "Slither",
        "install": "pipx install slither-analyzer",
    },
    "forge": {
        "label": "Foundry",
        "install": "curl -L https://foundry.paradigm.xyz | bash && foundryup",
    },
    "echidna": {
        "label": "Echidna",
        "install": "Download a release from https://github.com/crytic/echidna/releases",
    },
    "medusa": {
        "label": "Medusa",
        "install": "go install github.com/crytic/medusa@latest",
    },
    "trailmark": {
        "label": "Trailmark",
        "install": "uv pip install trailmark",
    },
}


def build_environment_readiness(
    *,
    target: dict[str, Any],
    repo_root: Path,
    target_root: Path,
    mode: str,
) -> dict[str, Any]:
    platform_info = detect_platform()
    profiles = determine_profiles(target)
    tool_results: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    if "web" in profiles:
        web_tools, web_actions = assess_web_profile(
            target=target,
            repo_root=repo_root,
            platform_info=platform_info,
            mode=mode,
        )
        tool_results.extend(web_tools)
        actions.extend(web_actions)

    if "android" in profiles:
        android_tools, android_actions = assess_android_profile(
            target=target,
            platform_info=platform_info,
            mode=mode,
        )
        tool_results.extend(android_tools)
        actions.extend(android_actions)

    if "native" in profiles:
        native_tools, native_actions = assess_native_profile(
            platform_info=platform_info,
            mode=mode,
        )
        tool_results.extend(native_tools)
        actions.extend(native_actions)

    if "smart-contract" in profiles:
        contract_tools, contract_actions = assess_smart_contract_profile(
            target=target,
            repo_root=repo_root,
            platform_info=platform_info,
            mode=mode,
        )
        tool_results.extend(contract_tools)
        actions.extend(contract_actions)

    profile_summaries = summarize_profiles(profiles, tool_results)
    overall_status = summarize_overall_status(profile_summaries)
    blockers = collect_unique_lines(
        line
        for tool in tool_results
        for line in tool.get("manual_follow_up", [])
    )
    ready_profiles = [item["profile"] for item in profile_summaries if item["status"] == "ready"]
    degraded_profiles = [item["profile"] for item in profile_summaries if item["status"] != "ready"]
    next_steps = build_next_steps(profile_summaries, tool_results, actions)

    report = {
        "mode": mode,
        "target_root": target_root.as_posix(),
        "primary_lane": target.get("suggested_lane", ""),
        "follow_on_lanes": list(target.get("follow_on_lanes", [])),
        "surface_signals": list(target.get("surface_signals", [])),
        "profiles": profiles,
        "platform": platform_info,
        "tool_results": tool_results,
        "profile_summaries": profile_summaries,
        "overall_status": overall_status,
        "ready_profiles": ready_profiles,
        "degraded_profiles": degraded_profiles,
        "actions_attempted": actions,
        "blockers": blockers,
        "next_steps": next_steps,
    }
    return report


def render_environment_readiness(report: dict[str, Any]) -> str:
    lines = [
        "# Environment Readiness",
        "",
        f"- Mode: {report['mode']}",
        f"- Overall Status: {report['overall_status']}",
        f"- Primary Lane: {report['primary_lane'] or 'Not captured'}",
        f"- Follow-On Lanes: {', '.join(report['follow_on_lanes']) if report['follow_on_lanes'] else 'None recorded'}",
        f"- Active Profiles: {', '.join(report['profiles']) if report['profiles'] else 'None recorded'}",
        f"- Platform: {render_platform_label(report['platform'])}",
        "",
        "## Profile Summary",
        "",
        "| Profile | Status | Critical Missing | Non-Critical Gaps |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["profile_summaries"]:
        lines.append(
            "| {profile} | {status} | {critical} | {non_critical} |".format(
                profile=item["profile"],
                status=item["status"],
                critical=item["critical_missing_count"],
                non_critical=item["non_critical_gap_count"],
            )
        )

    lines.extend(["", "## Tool Matrix", ""])
    lines.extend(render_tool_matrix(report["tool_results"]))
    lines.extend(["", "## Actions Attempted"])
    lines.extend(render_action_list(report["actions_attempted"]))
    lines.extend(["", "## Blockers And Manual Follow-Up"])
    lines.extend(render_list(report["blockers"]))
    lines.extend(["", "## Next Steps"])
    lines.extend(render_list(report["next_steps"]))
    return "\n".join(lines).rstrip() + "\n"


def render_environment_readiness_context(report: dict[str, Any]) -> str:
    lines = [
        "# Environment Readiness",
        "",
        f"- Overall Status: {report['overall_status']}",
        f"- Active Profiles: {', '.join(report['profiles']) if report['profiles'] else 'None recorded'}",
        f"- Ready Profiles: {', '.join(report['ready_profiles']) if report['ready_profiles'] else 'None recorded'}",
        f"- Degraded Profiles: {', '.join(report['degraded_profiles']) if report['degraded_profiles'] else 'None recorded'}",
        "",
        "## Critical Follow-Up",
    ]
    lines.extend(render_list(report["blockers"]))
    lines.extend(["", "## Next Steps"])
    lines.extend(render_list(report["next_steps"]))
    return "\n".join(lines).rstrip() + "\n"


def render_environment_summary_list(report: dict[str, Any]) -> list[str]:
    lines = [
        f"- Overall Status: {report['overall_status']}",
        f"- Active Profiles: {', '.join(report['profiles']) if report['profiles'] else 'None recorded'}",
    ]
    for item in report["profile_summaries"]:
        lines.append(f"- {item['profile']}: {item['status']}")
    lines.extend(render_list(report["blockers"])[:5])
    return lines


def determine_profiles(target: dict[str, Any]) -> list[str]:
    profiles: list[str] = []
    lanes = [target.get("suggested_lane", ""), *target.get("follow_on_lanes", [])]
    signals = set(target.get("surface_signals", []))
    target_type = target.get("target_type", "")

    if target_type == "web" or "bounty-program-web" in lanes or "web" in signals:
        profiles.append("web")
    if target_type == "android" or "bounty-program-mobile-android" in lanes or "android" in signals:
        profiles.append("android")
    if target_type == "native" or "bounty-program-native" in lanes or "native" in signals:
        profiles.append("native")
    if (
        target_type == "smart-contract"
        or "bounty-program-smart-contracts" in lanes
        or "smart-contract" in signals
        or bool(target.get("web3_readiness", {}).get("is_web3_target"))
    ):
        profiles.append("smart-contract")
    return collect_unique_lines(profiles)


def detect_platform() -> dict[str, str]:
    system = platform.system().lower()
    release = platform.release()
    machine = platform.machine()
    distro = ""
    if system == "linux":
        os_release = Path("/etc/os-release")
        if os_release.exists():
            try:
                lines = os_release.read_text(encoding="utf-8").splitlines()
                data = {}
                for line in lines:
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    data[key] = value.strip().strip('"')
                distro = data.get("ID", "")
            except OSError:
                distro = ""
    return {
        "system": system,
        "release": release,
        "machine": machine,
        "distro": distro,
    }


def render_platform_label(platform_info: dict[str, str]) -> str:
    system = platform_info.get("system", "unknown")
    distro = platform_info.get("distro", "")
    release = platform_info.get("release", "")
    if distro:
        return f"{system}/{distro} {release}".strip()
    return f"{system} {release}".strip()


def assess_web_profile(
    *,
    target: dict[str, Any],
    repo_root: Path,
    platform_info: dict[str, str],
    mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    tools: list[dict[str, Any]] = []

    docker_tool = check_docker(platform_info)
    if mode == "ensure" and docker_tool["status"] != "ready":
        action = ensure_docker(repo_root, platform_info)
        if action:
            actions.append(action)
            docker_tool = check_docker(platform_info)
            if docker_tool["status"] != "ready" and action["status"] != "skipped":
                docker_tool["manual_follow_up"].append("Docker still is not healthy after auto-setup attempt.")
    tools.append(docker_tool)

    kage_tool = check_kage(repo_root, docker_ready=docker_tool["status"] == "ready")
    if mode == "ensure" and docker_tool["status"] == "ready" and kage_tool["status"] != "ready":
        action = ensure_kage(repo_root, platform_info)
        if action:
            actions.append(action)
            kage_tool = check_kage(repo_root, docker_ready=docker_tool["status"] == "ready")
    tools.append(kage_tool)

    caido_runtime_tool = check_caido_runtime(platform_info)
    if mode == "ensure" and caido_runtime_tool["status"] != "ready":
        action = ensure_caido_runtime(repo_root, platform_info)
        if action:
            actions.append(action)
            caido_runtime_tool = check_caido_runtime(platform_info)
    tools.append(caido_runtime_tool)

    node_tool = check_node_runtime()
    if mode == "ensure" and node_tool["status"] != "ready" and caido_runtime_tool["status"] == "ready":
        node_tool = check_node_runtime()
    tools.append(node_tool)

    caido_repo_tool = check_caido_repo_cli(repo_root, node_ready=node_tool["status"] == "ready")
    if mode == "ensure" and caido_repo_tool["status"] != "ready" and node_tool["status"] == "ready":
        action = ensure_caido_repo_cli(repo_root)
        if action:
            actions.append(action)
            caido_repo_tool = check_caido_repo_cli(repo_root, node_ready=node_tool["status"] == "ready")
    tools.append(caido_repo_tool)

    caido_auth_tool = check_caido_auth()
    tools.append(caido_auth_tool)

    caido_capture_tool = check_caido_capture()
    if mode == "ensure" and caido_capture_tool["status"] != "ready":
        action = ensure_caido_capture(repo_root, platform_info, caido_auth_tool)
        if action:
            actions.append(action)
            caido_capture_tool = check_caido_capture()
    if target.get("auth_notes"):
        caido_capture_tool["manual_follow_up"].append(
            "Authenticated web flows are in scope. Keep Caido project, proxy profile, and request corpus ready before hunting."
        )
    tools.append(caido_capture_tool)
    return tools, actions


def assess_android_profile(
    *,
    target: dict[str, Any],
    platform_info: dict[str, str],
    mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    tools = [
        command_tool(
            profile="android",
            tool_id="adb",
            label="ADB",
            command="adb",
            critical=False,
            auto_setup_supported=is_linux_like(platform_info),
            install="Install Android platform-tools (Kali/Debian: apt-get install adb).",
            ready_hint="ADB is available for device or emulator control.",
            missing_hint="ADB is missing; rooted-device or emulator automation is blocked.",
        ),
        command_tool(
            profile="android",
            tool_id="apktool",
            label="apktool",
            command="apktool",
            critical=True,
            auto_setup_supported=is_linux_like(platform_info),
            install="Install apktool (Kali/Debian: apt-get install apktool).",
            ready_hint="Static APK decompilation is available.",
            missing_hint="apktool is missing; APK decompilation is blocked.",
        ),
        command_tool(
            profile="android",
            tool_id="jadx",
            label="jadx",
            command="jadx",
            critical=True,
            auto_setup_supported=False,
            install="Install JADX from the upstream release or package manager.",
            ready_hint="Java and Smali navigation is available.",
            missing_hint="jadx is missing; Java-source recovery is degraded.",
        ),
        command_tool(
            profile="android",
            tool_id="mitmproxy",
            label="mitmproxy",
            command="mitmproxy",
            critical=False,
            auto_setup_supported=True,
            install=f"{sys.executable} -m pip install --user mitmproxy",
            ready_hint="Traffic interception tooling is available.",
            missing_hint="mitmproxy is missing; live traffic capture is blocked.",
        ),
        command_tool(
            profile="android",
            tool_id="frida",
            label="Frida CLI",
            command="frida",
            critical=False,
            auto_setup_supported=True,
            install=f"{sys.executable} -m pip install --user frida-tools",
            ready_hint="Runtime hooking tooling is available.",
            missing_hint="Frida is missing; SSL-pinning and runtime-hook flows are degraded.",
        ),
    ]

    if mode == "ensure":
        actions.extend(ensure_android_packages(tools, platform_info))
        tools = reassess_command_tools(tools)

    rooted_device_tool = check_rooted_device()
    proxy_tool = check_android_global_proxy()
    mitm_config_tool = check_mitmproxy_default_config()
    cert_trust_tool = check_mitmproxy_ca_trust()
    if target.get("package_names"):
        rooted_device_tool["manual_follow_up"].append(
            "Connect a rooted device or emulator before running workers-app-tester dynamic flows."
        )
    tools.extend([rooted_device_tool, proxy_tool, mitm_config_tool, cert_trust_tool])
    return tools, actions


def assess_native_profile(
    *,
    platform_info: dict[str, str],
    mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    tools = [
        command_tool(
            profile="native",
            tool_id="file",
            label="file",
            command="file",
            critical=True,
            auto_setup_supported=is_linux_like(platform_info),
            install="Install the file utility (Kali/Debian: apt-get install file).",
            ready_hint="Binary fingerprinting is available.",
            missing_hint="file is missing; fast binary fingerprinting is blocked.",
        ),
        command_tool(
            profile="native",
            tool_id="strings",
            label="strings",
            command="strings",
            critical=True,
            auto_setup_supported=is_linux_like(platform_info),
            install="Install binutils (Kali/Debian: apt-get install binutils).",
            ready_hint="Strings extraction is available.",
            missing_hint="strings is missing; static binary triage is degraded.",
        ),
        command_tool(
            profile="native",
            tool_id="gdb",
            label="GDB",
            command="gdb",
            critical=True,
            auto_setup_supported=is_linux_like(platform_info),
            install="Install GDB (Kali/Debian: apt-get install gdb).",
            ready_hint="Native debugging is available.",
            missing_hint="GDB is missing; exploit debugging is blocked.",
        ),
        command_tool(
            profile="native",
            tool_id="checksec",
            label="checksec",
            command="checksec",
            critical=True,
            auto_setup_supported=is_linux_like(platform_info),
            install="Install checksec (Kali/Debian: apt-get install checksec).",
            ready_hint="Mitigation inspection is available.",
            missing_hint="checksec is missing; binary mitigation triage is degraded.",
        ),
        python_module_tool(
            profile="native",
            tool_id="pwntools",
            label="Pwntools",
            import_name="pwn",
            critical=False,
            install=f"{sys.executable} -m pip install --user pwntools",
            missing_hint="Pwntools is missing; exploit harness authoring is slower.",
        ),
    ]

    if mode == "ensure":
        actions.extend(ensure_native_packages(tools, platform_info))
        tools = reassess_command_tools(tools)
        tools = reassess_python_tools(tools)
    return tools, actions


def assess_smart_contract_profile(
    *,
    target: dict[str, Any],
    repo_root: Path,
    platform_info: dict[str, str],
    mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    tools: list[dict[str, Any]] = []
    has_rpc = bool(target.get("rpc_urls"))

    for tool_id, spec in WEB3_TOOL_GUIDANCE.items():
        critical = tool_id in {"slither", "trailmark"} or (tool_id == "forge" and has_rpc)
        result = command_tool(
            profile="smart-contract",
            tool_id=tool_id,
            label=spec["label"],
            command=tool_id,
            critical=critical,
            auto_setup_supported=True,
            install=spec["install"],
            ready_hint=f"{spec['label']} is available.",
            missing_hint=f"{spec['label']} is missing.",
        )
        if tool_id == "forge" and has_rpc and result["status"] != "ready":
            result["manual_follow_up"].append("Fork-capable replay needs Foundry because RPC endpoints are already in scope.")
        tools.append(result)

    if mode == "ensure":
        action = ensure_web3_toolchain(repo_root, platform_info)
        if action:
            actions.append(action)
            tools = reassess_command_tools(tools)
    return tools, actions


def check_docker(platform_info: dict[str, str]) -> dict[str, Any]:
    result = command_tool(
        profile="web",
        tool_id="docker",
        label="Docker Engine",
        command="docker",
        critical=True,
        auto_setup_supported=is_kali(platform_info),
        install="Use scripts/install-docker-kali-latest.sh on Kali/Linux or start Docker Desktop on macOS/Windows.",
        ready_hint="Docker CLI is available.",
        missing_hint="Docker CLI is missing; Kage sidecar cannot run.",
    )
    if result["status"] != "ready":
        return result

    command = ["docker", "info"]
    completed = run_command(command, timeout=30)
    if completed["returncode"] == 0:
        result["evidence"] = "docker info succeeded; daemon is healthy."
        return result

    result["status"] = "missing"
    result["evidence"] = "docker info failed."
    result["manual_follow_up"].append("Docker CLI exists but the daemon is not healthy. Start or repair the daemon before Kage runs.")
    return result


def check_kage(repo_root: Path, *, docker_ready: bool) -> dict[str, Any]:
    unix_shim = repo_root / "plugins" / "kage" / "skills" / "kage" / "scripts" / "k"
    pwsh_shim = repo_root / "plugins" / "kage" / "skills" / "kage" / "scripts" / "k.ps1"
    result = {
        "profile": "web",
        "tool_id": "kage",
        "label": "Kage sidecar",
        "status": "ready" if unix_shim.exists() and pwsh_shim.exists() and docker_ready else "missing",
        "critical": True,
        "auto_setup_supported": docker_ready,
        "install": "Kage ships in-repo. Keep Docker healthy and warm the sidecar with the repo-local shim.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if not unix_shim.exists() or not pwsh_shim.exists():
        result["manual_follow_up"].append("The repo-local Kage wrapper is missing.")
    elif not docker_ready:
        result["manual_follow_up"].append("Docker is not healthy, so the Kage sidecar cannot be warmed yet.")
    else:
        result["evidence"] = "Repo-local Kage wrapper exists and Docker is healthy."
    return result


def check_node_runtime() -> dict[str, Any]:
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    ready = bool(node_path and npm_path)
    result = {
        "profile": "web",
        "tool_id": "node-npm",
        "label": "Node.js + npm",
        "status": "ready" if ready else "missing",
        "critical": True,
        "auto_setup_supported": False,
        "install": "Install Node.js and npm before using the repo-local Caido CLI wrapper.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if ready:
        result["evidence"] = f"node={node_path}; npm={npm_path}"
    else:
        result["manual_follow_up"].append("Node.js and npm are required for the repo-local Caido wrapper.")
    return result


def check_caido_repo_cli(repo_root: Path, *, node_ready: bool) -> dict[str, Any]:
    package_dir = repo_root / "plugins" / "caido" / "skills" / "caido-mode"
    wrapper = package_dir / "scripts" / "caido"
    wrapper_ps1 = package_dir / "scripts" / "caido.ps1"
    node_modules = package_dir / "node_modules"
    ready = wrapper.exists() and wrapper_ps1.exists() and node_modules.exists() and node_ready
    result = {
        "profile": "web",
        "tool_id": "caido-repo-cli",
        "label": "Repo-local Caido CLI wrapper",
        "status": "ready" if ready else "missing",
        "critical": True,
        "auto_setup_supported": node_ready,
        "install": "Run npm install in plugins/caido/skills/caido-mode.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if ready:
        result["evidence"] = "Caido wrapper scripts and node_modules are present."
    else:
        if not node_ready:
            result["manual_follow_up"].append("Node.js/npm are missing, so the repo-local Caido wrapper cannot be bootstrapped.")
        if not node_modules.exists():
            result["manual_follow_up"].append("Run npm install in plugins/caido/skills/caido-mode.")
    return result


def check_caido_runtime(platform_info: dict[str, str]) -> dict[str, Any]:
    caido_path = shutil.which("caido")
    caido_cli_path = shutil.which("caido-cli")
    ready = bool(caido_path or caido_cli_path)
    result = {
        "profile": "web",
        "tool_id": "caido-runtime",
        "label": "Caido desktop or CLI",
        "status": "ready" if ready else "missing",
        "critical": True,
        "auto_setup_supported": is_kali(platform_info),
        "install": "Use scripts/install-caido-kali-latest.sh on Kali/Linux.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if ready:
        result["evidence"] = f"caido={caido_path or '-'}; caido-cli={caido_cli_path or '-'}"
    else:
        result["manual_follow_up"].append("Caido runtime is missing, so authenticated traffic capture and replay are not ready.")
    return result


def check_caido_auth() -> dict[str, Any]:
    has_pat = bool(os.environ.get("CAIDO_PAT")) or bool(read_saved_caido_secret("pat"))
    result = {
        "profile": "web",
        "tool_id": "caido-auth",
        "label": "Caido PAT",
        "status": "ready" if has_pat else "partial",
        "critical": False,
        "auto_setup_supported": False,
        "install": "Provide CAIDO_PAT or save the PAT through the repo-local setup flow.",
        "evidence": "PAT detected in environment or cached secret store." if has_pat else "",
        "manual_follow_up": [],
    }
    if not has_pat:
        result["manual_follow_up"].append("Provide a Caido PAT if hunting needs the SDK wrapper for search, replay, or evidence export.")
    return result


def check_caido_capture() -> dict[str, Any]:
    codex_dir = Path.home() / ".codex" / "caido"
    manual_env = codex_dir / "manual-setup.env"
    manual_txt = codex_dir / "manual-setup.txt"
    cert_file = codex_dir / "caido-ca.crt"
    ready = manual_env.exists() or (manual_txt.exists() and cert_file.exists())
    result = {
        "profile": "web",
        "tool_id": "caido-capture",
        "label": "Caido proxy and browser bootstrap",
        "status": "ready" if ready else "partial",
        "critical": False,
        "auto_setup_supported": False,
        "install": "Run scripts/setup-caido-codex-kali.sh and scripts/launch-caido-chrome.sh to prepare browser capture.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if ready:
        result["evidence"] = f"Found {manual_env if manual_env.exists() else manual_txt}"
    else:
        result["manual_follow_up"].append("Prepare the Caido browser bootstrap so traffic capture can start immediately during web hunting.")
    return result


def check_rooted_device() -> dict[str, Any]:
    adb_path = shutil.which("adb")
    result = {
        "profile": "android",
        "tool_id": "rooted-device",
        "label": "Rooted device or emulator",
        "status": "partial",
        "critical": False,
        "auto_setup_supported": False,
        "install": "Connect a rooted device or emulator before running workers-app-tester dynamic flows.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if not adb_path:
        result["manual_follow_up"].append("ADB is missing, so device readiness cannot be verified.")
        return result

    completed = run_command(["adb", "devices"], timeout=20)
    if completed["returncode"] != 0:
        result["manual_follow_up"].append("ADB exists but no device inventory was returned.")
        return result

    if any("\tdevice" in line for line in completed["stdout"].splitlines()):
        root_check = run_command(["adb", "shell", "su", "-c", "id"], timeout=20)
        if root_check["returncode"] == 0 and "uid=0" in root_check["stdout"]:
            result["status"] = "ready"
            result["evidence"] = "At least one ADB device is connected and su returned uid=0."
        else:
            result["manual_follow_up"].append("ADB device is connected, but `adb shell su -c id` did not confirm root access.")
    else:
        result["manual_follow_up"].append("ADB is installed but no connected device or emulator is ready.")
    return result


def check_android_global_proxy() -> dict[str, Any]:
    adb_path = shutil.which("adb")
    result = {
        "profile": "android",
        "tool_id": "android-global-proxy",
        "label": "Android global proxy on port 18088",
        "status": "partial",
        "critical": False,
        "auto_setup_supported": False,
        "install": "Keep the Android global proxy pointed at the existing MITM listener on port 18088.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if not adb_path:
        result["manual_follow_up"].append("ADB is missing, so the Android proxy setting could not be verified.")
        return result

    completed = run_command(["adb", "shell", "settings", "get", "global", "http_proxy"], timeout=20)
    if completed["returncode"] != 0:
        result["manual_follow_up"].append("Could not read `settings get global http_proxy` from the connected device.")
        return result

    proxy_value = completed["stdout"].strip()
    if proxy_value and proxy_value.lower() != "null" and proxy_value.endswith(":18088"):
        result["status"] = "ready"
        result["evidence"] = f"http_proxy={proxy_value}"
    else:
        display = proxy_value or "<empty>"
        result["manual_follow_up"].append(
            f"Android global proxy is {display}; expected an existing listener on port 18088 before dynamic capture."
        )
    return result


def check_mitmproxy_default_config() -> dict[str, Any]:
    config_path = Path.home() / ".mitmproxy" / "config.yaml"
    result = {
        "profile": "android",
        "tool_id": "mitmproxy-default-config",
        "label": "mitmproxy default config",
        "status": "ready" if config_path.exists() else "partial",
        "critical": False,
        "auto_setup_supported": False,
        "install": f"Keep the stable mitmproxy defaults at {config_path}.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if config_path.exists():
        result["evidence"] = str(config_path)
        try:
            config_text = config_path.read_text(encoding="utf-8")
        except OSError as exc:
            result["status"] = "partial"
            result["manual_follow_up"].append(f"Could not read {config_path}: {exc}")
            return result
        if "ignore_hosts:" in config_text and "'.*\\.*'" in config_text and "allow_hosts:" not in config_text:
            result["status"] = "partial"
            result["manual_follow_up"].append(
                "The mitmproxy config still bypasses every host. Run `python3 scripts/mitm_watch.py start --session-dir <dir> --package <pkg> --host <host>` before dynamic capture."
            )
    else:
        result["manual_follow_up"].append(
            f"The expected mitmproxy default config was not found at {config_path}."
        )
    return result


def check_mitmproxy_ca_trust() -> dict[str, Any]:
    cert_pem = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    cert_cer = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
    cert_path = cert_pem if cert_pem.exists() else cert_cer
    result = {
        "profile": "android",
        "tool_id": "mitmproxy-ca-trust",
        "label": "mitmproxy CA trust on device",
        "status": "partial",
        "critical": False,
        "auto_setup_supported": False,
        "install": "Keep the mitmproxy CA installed in the Android trust store before traffic capture.",
        "evidence": "",
        "manual_follow_up": [],
    }
    if not cert_path.exists():
        result["manual_follow_up"].append(
            f"Local mitmproxy CA cert was not found at {cert_pem} or {cert_cer}."
        )
        return result
    if not shutil.which("adb"):
        result["manual_follow_up"].append("ADB is missing, so Android certificate trust could not be verified.")
        return result
    openssl_path = shutil.which("openssl")
    if not openssl_path:
        result["manual_follow_up"].append("openssl is missing, so the mitmproxy CA hash could not be verified.")
        return result

    hash_result = run_command([openssl_path, "x509", "-in", str(cert_path), "-subject_hash_old", "-noout"], timeout=20)
    if hash_result["returncode"] != 0:
        result["manual_follow_up"].append(
            hash_result["stderr"].strip() or "Failed to compute the mitmproxy CA subject hash."
        )
        return result

    expected_hash = next((line.strip() for line in hash_result["stdout"].splitlines() if line.strip()), "")
    if not expected_hash:
        result["manual_follow_up"].append("openssl did not return a subject hash for the mitmproxy CA.")
        return result

    device_path = ""
    for candidate in (
        f"/data/misc/user/0/cacerts-added/{expected_hash}.0",
        f"/system/etc/security/cacerts/{expected_hash}.0",
    ):
        device_result = run_command(["adb", "shell", f"su -c 'ls {candidate}'"], timeout=20)
        if device_result["returncode"] == 0 and candidate in device_result["stdout"]:
            device_path = candidate
            break
    if device_path:
        result["status"] = "ready"
        result["evidence"] = f"{cert_path.name} -> {device_path}"
    else:
        result["manual_follow_up"].append(
            f"mitmproxy CA hash {expected_hash} was not found in the Android certificate stores."
        )
    return result


def command_tool(
    *,
    profile: str,
    tool_id: str,
    label: str,
    command: str,
    critical: bool,
    auto_setup_supported: bool,
    install: str,
    ready_hint: str,
    missing_hint: str,
) -> dict[str, Any]:
    command_path = shutil.which(command)
    status = "ready" if command_path else "missing"
    result = {
        "profile": profile,
        "tool_id": tool_id,
        "label": label,
        "status": status,
        "critical": critical,
        "auto_setup_supported": auto_setup_supported,
        "install": install,
        "evidence": ready_hint if command_path else "",
        "command": command,
        "manual_follow_up": [],
    }
    if command_path:
        result["evidence"] = f"{command}={command_path}"
    else:
        result["manual_follow_up"].append(missing_hint)
    return result


def python_module_tool(
    *,
    profile: str,
    tool_id: str,
    label: str,
    import_name: str,
    critical: bool,
    install: str,
    missing_hint: str,
) -> dict[str, Any]:
    completed = run_command([sys.executable, "-c", f"import {import_name}"], timeout=20)
    ready = completed["returncode"] == 0
    result = {
        "profile": profile,
        "tool_id": tool_id,
        "label": label,
        "status": "ready" if ready else "missing",
        "critical": critical,
        "auto_setup_supported": True,
        "install": install,
        "evidence": "Python module import succeeded." if ready else "",
        "import_name": import_name,
        "manual_follow_up": [],
    }
    if not ready:
        result["manual_follow_up"].append(missing_hint)
    return result


def reassess_command_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for tool in tools:
        command = tool.get("command")
        if not command:
            updated.append(tool)
            continue
        refreshed = dict(tool)
        if shutil.which(command):
            refreshed["status"] = "ready"
            refreshed["evidence"] = f"{command}={shutil.which(command)}"
            refreshed["manual_follow_up"] = [
                line for line in refreshed.get("manual_follow_up", []) if "missing" not in line.lower()
            ]
        updated.append(refreshed)
    return updated


def reassess_python_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for tool in tools:
        import_name = tool.get("import_name")
        if not import_name:
            updated.append(tool)
            continue
        refreshed = dict(tool)
        completed = run_command([sys.executable, "-c", f"import {import_name}"], timeout=20)
        if completed["returncode"] == 0:
            refreshed["status"] = "ready"
            refreshed["evidence"] = "Python module import succeeded."
            refreshed["manual_follow_up"] = []
        updated.append(refreshed)
    return updated


def ensure_docker(repo_root: Path, platform_info: dict[str, str]) -> dict[str, Any] | None:
    script_path = repo_root / "scripts" / "install-docker-kali-latest.sh"
    if not script_path.exists():
        return None
    if not is_kali(platform_info):
        return skipped_action(
            "docker-install",
            "Docker auto-install skipped because the repo only ships a Kali/Linux installer.",
        )
    return run_action("docker-install", ["bash", str(script_path)])


def ensure_kage(repo_root: Path, platform_info: dict[str, str]) -> dict[str, Any] | None:
    unix_shim = repo_root / "plugins" / "kage" / "skills" / "kage" / "scripts" / "k"
    pwsh_shim = repo_root / "plugins" / "kage" / "skills" / "kage" / "scripts" / "k.ps1"
    if platform_info["system"] == "windows":
        if not pwsh_shim.exists():
            return None
        return run_action(
            "kage-warm",
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(pwsh_shim),
                "whoami",
            ],
            timeout=180,
        )
    if not unix_shim.exists():
        return None
    return run_action("kage-warm", ["bash", str(unix_shim), "whoami"], timeout=180)


def ensure_caido_repo_cli(repo_root: Path) -> dict[str, Any] | None:
    package_dir = repo_root / "plugins" / "caido" / "skills" / "caido-mode"
    package_json = package_dir / "package.json"
    if not package_json.exists():
        return None
    return run_action("caido-npm-install", ["npm", "install"], cwd=package_dir, timeout=900)


def ensure_caido_runtime(repo_root: Path, platform_info: dict[str, str]) -> dict[str, Any] | None:
    script_path = repo_root / "scripts" / "install-caido-kali-latest.sh"
    if not script_path.exists():
        return None
    if not is_kali(platform_info):
        return skipped_action(
            "caido-install",
            "Caido auto-install skipped because the repo only ships a Kali/Linux installer.",
        )
    return run_action("caido-install", ["bash", str(script_path), "--skip-full-setup"], timeout=1800)


def ensure_caido_capture(
    repo_root: Path,
    platform_info: dict[str, str],
    caido_auth_tool: dict[str, Any],
) -> dict[str, Any] | None:
    script_path = repo_root / "scripts" / "setup-caido-codex-kali.sh"
    if not script_path.exists():
        return None
    if not is_kali(platform_info):
        return skipped_action(
            "caido-capture-bootstrap",
            "Caido capture bootstrap skipped because the repo setup flow targets Kali/Linux.",
        )
    pat = os.environ.get("CAIDO_PAT") or read_saved_caido_secret("pat")
    if not pat:
        return skipped_action(
            "caido-capture-bootstrap",
            "Caido PAT is still missing, so proxy bootstrap cannot complete non-interactively.",
        )
    display_ready = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if not display_ready:
        return skipped_action(
            "caido-capture-bootstrap",
            "No graphical display is available, so the Chrome + certificate setup flow was skipped.",
        )
    return run_action(
        "caido-capture-bootstrap",
        [
            "bash",
            str(script_path),
            "--skip-install",
            "--skip-chrome-test",
            "--import-cert",
            "--pat",
            pat,
        ],
        timeout=1800,
    )


def ensure_android_packages(tools: list[dict[str, Any]], platform_info: dict[str, str]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not is_linux_like(platform_info):
        missing = [tool["label"] for tool in tools if tool["status"] != "ready" and tool["auto_setup_supported"]]
        if missing:
            actions.append(
                skipped_action(
                    "android-package-bootstrap",
                    f"Auto-install for Android tooling is only scripted for Linux/Kali. Missing: {', '.join(missing)}",
                )
            )
        return actions

    packages: list[str] = []
    for tool in tools:
        if tool["status"] == "ready":
            continue
        if tool["tool_id"] == "adb":
            packages.append("adb")
        elif tool["tool_id"] == "apktool":
            packages.append("apktool")

    if packages:
        actions.append(run_linux_package_install("android-core-packages", packages))

    if any(tool["tool_id"] == "mitmproxy" and tool["status"] != "ready" for tool in tools):
        actions.append(run_action("android-mitmproxy-pip", [sys.executable, "-m", "pip", "install", "--user", "mitmproxy"], timeout=1200))
    if any(tool["tool_id"] == "frida" and tool["status"] != "ready" for tool in tools):
        actions.append(run_action("android-frida-pip", [sys.executable, "-m", "pip", "install", "--user", "frida-tools"], timeout=1200))
    return actions


def ensure_native_packages(tools: list[dict[str, Any]], platform_info: dict[str, str]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not is_linux_like(platform_info):
        missing = [tool["label"] for tool in tools if tool["status"] != "ready" and tool["auto_setup_supported"]]
        if missing:
            actions.append(
                skipped_action(
                    "native-package-bootstrap",
                    f"Auto-install for native tooling is only scripted for Linux/Kali. Missing: {', '.join(missing)}",
                )
            )
        return actions

    packages: list[str] = []
    for tool in tools:
        if tool["status"] == "ready":
            continue
        if tool["tool_id"] == "file":
            packages.append("file")
        elif tool["tool_id"] == "strings":
            packages.append("binutils")
        elif tool["tool_id"] == "gdb":
            packages.append("gdb")
        elif tool["tool_id"] == "checksec":
            packages.append("checksec")

    if packages:
        actions.append(run_linux_package_install("native-core-packages", packages))

    if any(tool.get("import_name") == "pwn" and tool["status"] != "ready" for tool in tools):
        actions.append(run_action("native-pwntools-pip", [sys.executable, "-m", "pip", "install", "--user", "pwntools"], timeout=1200))
    return actions


def ensure_web3_toolchain(repo_root: Path, platform_info: dict[str, str]) -> dict[str, Any] | None:
    if platform_info["system"] == "windows":
        script_path = repo_root / "scripts" / "bootstrap-web3-tools.ps1"
        if not script_path.exists():
            return None
        return run_action(
            "web3-toolchain-bootstrap",
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-Mode",
                "ensure",
            ],
            timeout=1800,
        )

    script_path = repo_root / "scripts" / "bootstrap-web3-tools.sh"
    if not script_path.exists():
        return None
    return run_action("web3-toolchain-bootstrap", ["bash", str(script_path), "ensure"], timeout=1800)


def summarize_profiles(profiles: list[str], tool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for profile in profiles:
        scoped = [tool for tool in tool_results if tool["profile"] == profile]
        critical_missing = [tool for tool in scoped if tool["critical"] and tool["status"] != "ready"]
        non_critical_gaps = [tool for tool in scoped if not tool["critical"] and tool["status"] != "ready"]

        status = "ready"
        if any(tool["status"] == "missing" for tool in critical_missing):
            status = "needs-setup"
        if any(tool.get("manual_follow_up") for tool in critical_missing) and critical_missing:
            status = "blocked" if all(not tool["auto_setup_supported"] for tool in critical_missing) else status
        if status == "ready" and non_critical_gaps:
            status = "partial"

        summaries.append(
            {
                "profile": profile,
                "status": status,
                "critical_missing_count": len(critical_missing),
                "non_critical_gap_count": len(non_critical_gaps),
            }
        )
    return summaries


def summarize_overall_status(profile_summaries: list[dict[str, Any]]) -> str:
    statuses = [item["status"] for item in profile_summaries]
    if not statuses:
        return "ready"
    if "blocked" in statuses:
        return "blocked"
    if "needs-setup" in statuses:
        return "needs-setup"
    if "partial" in statuses:
        return "partial"
    return "ready"


def build_next_steps(
    profile_summaries: list[dict[str, Any]],
    tool_results: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> list[str]:
    lines: list[str] = []
    degraded = [item["profile"] for item in profile_summaries if item["status"] != "ready"]
    if degraded:
        lines.append(f"Finish readiness repair for: {', '.join(degraded)}.")
    for tool in tool_results:
        if tool["status"] == "ready":
            continue
        for follow_up in tool.get("manual_follow_up", [])[:2]:
            lines.append(follow_up)
    if actions:
        lines.append("Re-read prep/environment-readiness.md before hunting if any auto-setup action was attempted during bootstrap.")
    return collect_unique_lines(lines)


def render_tool_matrix(tool_results: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Profile | Tool | Status | Critical | Auto-Setup | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for tool in tool_results:
        evidence = tool.get("evidence", "") or "; ".join(tool.get("manual_follow_up", [])[:1]) or "-"
        lines.append(
            "| {profile} | {label} | {status} | {critical} | {auto} | {evidence} |".format(
                profile=tool["profile"],
                label=tool["label"],
                status=tool["status"],
                critical="yes" if tool["critical"] else "no",
                auto="yes" if tool["auto_setup_supported"] else "no",
                evidence=evidence.replace("|", "/"),
            )
        )
    return lines


def render_action_list(actions: list[dict[str, Any]]) -> list[str]:
    if not actions:
        return ["- No auto-setup action was attempted."]
    rendered = []
    for action in actions:
        note = action.get("note", "")
        rendered.append(
            f"- {action['name']}: {action['status']}" + (f" ({note})" if note else "")
        )
    return rendered


def render_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None recorded"]
    return [f"- {item}" for item in items]


def collect_unique_lines(items: Any) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def read_saved_caido_secret(field: str) -> str:
    secrets_path = Path.home() / ".codex" / "caido" / "secrets.json"
    if not secrets_path.exists():
        return ""
    try:
        payload = json.loads(secrets_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(((payload.get("caido") or {}).get(field)) or "").strip()


def is_kali(platform_info: dict[str, str]) -> bool:
    return platform_info.get("system") == "linux" and platform_info.get("distro") == "kali"


def is_linux_like(platform_info: dict[str, str]) -> bool:
    return platform_info.get("system") == "linux"


def run_linux_package_install(name: str, packages: list[str]) -> dict[str, Any]:
    unique_packages = collect_unique_lines(packages)
    if not unique_packages:
        return skipped_action(name, "No Linux packages needed.")
    if os.geteuid() == 0 if hasattr(os, "geteuid") else False:
        update_prefix: list[str] = []
        install_prefix: list[str] = []
    elif shutil.which("sudo"):
        update_prefix = ["sudo"]
        install_prefix = ["sudo"]
    else:
        return skipped_action(name, "sudo is unavailable, so apt-get installation was skipped.")

    update = run_action(f"{name}-apt-update", [*update_prefix, "apt-get", "update"], timeout=1200)
    install = run_action(
        name,
        [*install_prefix, "apt-get", "install", "-y", *unique_packages],
        timeout=1800,
    )
    if update["status"] != "ok":
        install["note"] = f"{install.get('note', '')} apt-get update status={update['status']}".strip()
    return install


def run_action(
    name: str,
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    completed = run_command(command, cwd=cwd, timeout=timeout)
    status = "ok" if completed["returncode"] == 0 else "error"
    note_parts = []
    if completed["stdout"]:
        note_parts.append(squash_output(completed["stdout"]))
    if completed["stderr"]:
        note_parts.append(squash_output(completed["stderr"]))
    return {
        "name": name,
        "status": status,
        "command": " ".join(command),
        "note": " | ".join(part for part in note_parts if part)[:500],
    }


def skipped_action(name: str, note: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "skipped",
        "command": "",
        "note": note,
    }


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def squash_output(value: str) -> str:
    return " ".join(value.split())
