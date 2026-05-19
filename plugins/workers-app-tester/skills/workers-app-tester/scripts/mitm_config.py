from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


HOST_RE = re.compile(rb"(?:(?:https?://)?)([a-zA-Z0-9][a-zA-Z0-9.-]{2,}\.[a-zA-Z]{2,})(?::\d+)?")
NOISE_HOSTS = [
    "clients[0-9]*\\.google\\.com",
    "connectivitycheck\\.gstatic\\.com",
    "android\\.clients\\.google\\.com",
]


def run(command: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def config_path(raw: str | None = None) -> Path:
    if raw:
        return Path(raw).expanduser()
    env_path = os.environ.get("MITMPROXY_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".mitmproxy" / "config.yaml"


def read_config(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def has_blanket_bypass(config_text: str) -> bool:
    pattern = r"ignore_hosts:\s*\n(?:\s*-\s*[\"']?\^?\.\*\$?[\"']?\s*\n?)+"
    return bool(re.search(pattern, config_text))


def normalize_host(host: str) -> str:
    parsed = urlparse(host if "://" in host else f"https://{host}")
    value = (parsed.hostname or host).strip().lower().lstrip(".")
    return value[2:] if value.startswith("*.") else value


def host_regex(host: str) -> str:
    return rf"(^|\.){re.escape(host)}$"


def strip_yaml_block(lines: list[str], key: str) -> list[str]:
    result: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith(f"{key}:"):
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                i += 1
            continue
        result.append(lines[i])
        i += 1
    return result


def write_config(path: Path, hosts: list[str], capture_all: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = read_config(path).splitlines()
    for key in ("allow_hosts", "ignore_hosts", "listen_port"):
        lines = strip_yaml_block(lines, key)
    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("listen_port: 18088")
    if hosts and not capture_all:
        lines.append("allow_hosts:")
        lines.extend(f"  - {host_regex(host)}" for host in hosts)
    lines.append("ignore_hosts:")
    lines.extend(f"  - {pattern}" for pattern in NOISE_HOSTS)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def hosts_from_traffic(path: Path) -> set[str]:
    hosts: set[str] = set()
    if not path.exists():
        return hosts
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        for key in ("host", "pretty_url"):
            value = str(record.get(key, ""))
            if value:
                hosts.add(normalize_host(value))
    return {host for host in hosts if "." in host}


def hosts_from_package(package: str) -> set[str]:
    path_result = run(["adb", "shell", "pm", "path", package])
    apk_paths = [line.split(":", 1)[1].strip() for line in path_result.stdout.splitlines() if ":" in line]
    if not apk_paths:
        return set()
    with tempfile.TemporaryDirectory() as temp_dir:
        local_apk = Path(temp_dir) / "base.apk"
        pull_result = run(["adb", "pull", apk_paths[0], str(local_apk)], timeout=120)
        if pull_result.returncode != 0 or not local_apk.exists():
            return set()
        data = local_apk.read_bytes()
    return {match.group(1).decode("ascii", "ignore").lower() for match in HOST_RE.finditer(data)}


def collect_hosts(hosts: list[str], package: str | None, traffic: str | None) -> list[str]:
    collected = {normalize_host(host) for host in hosts}
    if package:
        collected.update(hosts_from_package(package))
    if traffic:
        collected.update(hosts_from_traffic(Path(traffic).expanduser()))
    return sorted(host for host in collected if "." in host and not host.startswith("-"))
