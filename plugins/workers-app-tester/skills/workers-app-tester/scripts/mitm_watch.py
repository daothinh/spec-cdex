#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from mitm_config import collect_hosts, config_path, has_blanket_bypass, read_config, run, write_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage Android app mitmproxy capture sessions.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify", help="Check ADB, root, proxy, certificate, and mitmproxy config readiness.")

    configure = sub.add_parser("configure", help="Patch mitmproxy config from hosts, APK, or traffic.")
    add_config_args(configure)

    start = sub.add_parser("start", help="Configure and start mitmdump capture.")
    add_config_args(start)
    start.add_argument("--session-dir", required=True, help="Directory for traffic.jsonl and pid files.")
    start.add_argument("--preserve-auth", action="store_true", help="Do not redact auth headers in capture.py.")

    stop = sub.add_parser("stop", help="Stop a capture started by this helper.")
    stop.add_argument("--session-dir", required=True, help="Directory containing mitmdump.pid.")
    return parser.parse_args()


def add_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", action="append", default=[], help="Host to add to allow_hosts.")
    parser.add_argument("--package", help="Installed Android package to pull and scan for hosts.")
    parser.add_argument("--traffic", help="Existing traffic.jsonl to mine for hosts.")
    parser.add_argument("--capture-all", action="store_true", help="Do not write allow_hosts.")
    parser.add_argument("--config", help="mitmproxy config.yaml path.")


def adb_shell(command: str) -> str:
    result = run(["adb", "shell", command])
    return result.stdout.strip() if result.returncode == 0 else ""


def proxy_status() -> str:
    return adb_shell("settings get global http_proxy")


def root_status() -> str:
    return adb_shell("su -c id")


def cert_status() -> str:
    command = (
        "su -c 'ls /system/etc/security/cacerts /data/misc/user/0/cacerts-added "
        "2>/dev/null | head -20'"
    )
    return adb_shell(command)


def verify(args: argparse.Namespace) -> int:
    cfg = config_path(getattr(args, "config", None))
    report = {
        "adb": bool(shutil.which("adb")),
        "mitmdump": bool(shutil.which("mitmdump")),
        "proxy": proxy_status(),
        "root": root_status(),
        "cert_store_sample": cert_status(),
        "config_path": str(cfg),
        "config_exists": cfg.exists(),
        "blanket_ignore_hosts": has_blanket_bypass(read_config(cfg)),
    }
    print(json.dumps(report, indent=2))
    ready = report["adb"] and report["mitmdump"] and str(report["proxy"]).endswith(":18088")
    return 0 if ready else 1


def configure(args: argparse.Namespace) -> int:
    hosts = collect_hosts(args.host, args.package, args.traffic)
    write_config(config_path(args.config), hosts, args.capture_all)
    print(json.dumps({"hosts": hosts, "capture_all": args.capture_all, "count": len(hosts)}, indent=2))
    return 0


def start(args: argparse.Namespace) -> int:
    configure(args)
    session_dir = Path(args.session_dir).expanduser()
    session_dir.mkdir(parents=True, exist_ok=True)
    script_path = Path(__file__).with_name("capture.py")
    env = os.environ.copy()
    env["ANDROID_APP_TESTER_OUT_DIR"] = str(session_dir)
    env["ANDROID_APP_TESTER_PACKAGE"] = args.package or ""
    env["ANDROID_APP_TESTER_PRESERVE_AUTH"] = "1" if args.preserve_auth else "0"
    command = ["mitmdump", "--listen-port", "18088", "-s", str(script_path)]
    log_path = session_dir / "mitmdump.log"
    log = log_path.open("ab")
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
    (session_dir / "mitmdump.pid").write_text(str(process.pid), encoding="utf-8")
    print(json.dumps({"pid": process.pid, "traffic": str(session_dir / "traffic.jsonl"), "log": str(log_path)}, indent=2))
    return 0


def stop(args: argparse.Namespace) -> int:
    pid_path = Path(args.session_dir).expanduser() / "mitmdump.pid"
    if not pid_path.exists():
        print(json.dumps({"stopped": False, "reason": "pid file missing"}))
        return 0
    pid = int(pid_path.read_text(encoding="utf-8").strip())
    try:
        os.kill(pid, signal.SIGTERM)
        pid_path.unlink()
        print(json.dumps({"stopped": True, "pid": pid}))
    except ProcessLookupError:
        pid_path.unlink(missing_ok=True)
        print(json.dumps({"stopped": False, "pid": pid, "reason": "process not found"}))
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "verify":
        return verify(args)
    if args.command == "configure":
        return configure(args)
    if args.command == "start":
        return start(args)
    if args.command == "stop":
        return stop(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
