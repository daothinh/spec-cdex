#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ASCIINEMA_URL_PATTERN = re.compile(r"https?://asciinema\.org/a/\S+", re.IGNORECASE)
INTRO_BLOCK = "\n".join(
    [
        "clear",
        'echo " > Proof of Concept"',
        'echo " > crafted by dxoth1nh"',
        'echo ""',
        "sleep 2",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record the final clean PoC replay with system-installed asciinema, save the local .cast file, "
            "upload it to asciinema.org, and write portable metadata into artifacts/asciinema/."
        )
    )
    parser.add_argument("--finding-dir", required=True, help="Path to audit-targets/<slug>/findings/<finding-id>")
    parser.add_argument("--run-command", required=True, help="Exact replay command to record with asciinema")
    parser.add_argument(
        "--workdir",
        default=".",
        help="Directory where the replay command should run. Defaults to the current directory.",
    )
    parser.add_argument("--title", help="Optional asciinema recording title")
    parser.add_argument(
        "--success-signal",
        action="append",
        default=[],
        help="Decisive output expected from the recorded replay. Repeatable.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional artifacts/asciinema output path. Defaults to <finding-dir>/artifacts/asciinema",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing cast and metadata file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = record_asciinema_replay(
        finding_dir=Path(args.finding_dir),
        run_command=args.run_command,
        workdir=Path(args.workdir),
        title=args.title,
        success_signals=args.success_signal,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        force=args.force,
    )
    print(json.dumps(payload, indent=2))
    return 0


def record_asciinema_replay(
    *,
    finding_dir: Path,
    run_command: str,
    workdir: Path,
    title: str | None,
    success_signals: list[str],
    output_dir: Path | None,
    force: bool,
) -> dict[str, Any]:
    finding_dir = finding_dir.resolve()
    if not finding_dir.is_dir():
        raise SystemExit(f"error: finding directory does not exist: {finding_dir}")

    workdir = workdir.resolve()
    if not workdir.is_dir():
        raise SystemExit(f"error: workdir does not exist: {workdir}")

    output_dir = output_dir.resolve() if output_dir else finding_dir / "artifacts" / "asciinema"
    output_dir.mkdir(parents=True, exist_ok=True)
    cast_path = output_dir / "reverify-session.cast"
    metadata_path = output_dir / "asciinema-session.json"
    if not force and (cast_path.exists() or metadata_path.exists()):
        raise SystemExit(f"error: asciinema artifacts already exist in {output_dir}. Re-run with --force to overwrite.")

    title = (title or f"{finding_dir.parent.name}/{finding_dir.name} final reverify replay").strip()
    backend = resolve_asciinema_backend()
    recorded_command = build_recorded_command(run_command)

    record_result = record_cast(
        backend=backend,
        workdir=workdir,
        cast_path=cast_path,
        title=title,
        run_command=recorded_command,
    )
    if record_result.returncode != 0:
        stderr = record_result.stderr.strip() or record_result.stdout.strip() or "unknown asciinema record failure"
        raise SystemExit(f"error: failed to record asciinema replay: {stderr}")
    if not cast_path.is_file():
        raise SystemExit(f"error: asciinema did not create the local cast file: {cast_path}")

    upload_result = upload_cast(backend=backend, cast_path=cast_path, output_dir=output_dir)
    if upload_result.returncode != 0:
        stderr = upload_result.stderr.strip() or upload_result.stdout.strip() or "unknown asciinema upload failure"
        raise SystemExit(f"error: failed to upload asciinema replay: {stderr}")
    server_url = parse_asciinema_url(upload_result.stdout, upload_result.stderr)
    if not server_url:
        raise SystemExit("error: asciinema upload succeeded without returning an asciinema.org URL")

    metadata = {
        "tool": "asciinema",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "run_command": run_command,
        "recorded_command": recorded_command,
        "success_signals": unique(success_signals),
        "workdir": workdir.as_posix(),
        "cast_filename": cast_path.name,
        "local_cast_path": cast_path.name,
        "server_url": server_url,
        "link_markdown": markdown_link(server_url),
        "environment_check": {
            "binary": backend["binary"],
            "version": backend["version"],
            "mode": backend["mode"],
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "finding_dir": finding_dir.as_posix(),
        "output_dir": output_dir.as_posix(),
        "cast_path": cast_path.as_posix(),
        "metadata_path": metadata_path.as_posix(),
        "server_url": server_url,
    }


def resolve_asciinema_backend() -> dict[str, str]:
    native = run_native(["asciinema", "--version"])
    native_version = (native.stdout or native.stderr).strip()
    if native.returncode == 0 and native_version:
        return {"mode": "native", "binary": "asciinema", "version": native_version}

    wsl = run_wsl("command -v asciinema >/dev/null && asciinema --version")
    wsl_version = (wsl.stdout or wsl.stderr).strip()
    if wsl.returncode == 0 and wsl_version:
        return {"mode": "wsl", "binary": "asciinema", "version": wsl_version}

    native_error = native.stderr.strip() or native.stdout.strip() or "not found on native PATH"
    wsl_error = wsl.stderr.strip() or wsl.stdout.strip() or "not found in WSL"
    raise SystemExit(
        "error: asciinema is required before replay recording can continue. "
        f"Checked native PATH ({native_error}) and WSL ({wsl_error})."
    )


def record_cast(
    *,
    backend: dict[str, str],
    workdir: Path,
    cast_path: Path,
    title: str,
    run_command: str,
) -> subprocess.CompletedProcess[str]:
    if backend["mode"] == "native":
        return run_native(
            ["asciinema", "rec", "--overwrite", "--quiet", "--title", title, "-c", run_command, str(cast_path)],
            cwd=workdir,
        )

    record_command = (
        f"cd {shlex.quote(to_wsl_path(workdir))} && "
        f"asciinema rec --overwrite --quiet --title {shlex.quote(title)} "
        f"-c {shlex.quote(run_command)} {shlex.quote(to_wsl_path(cast_path))}"
    )
    return run_wsl(record_command)


def build_recorded_command(run_command: str) -> str:
    replay_command = run_command.strip()
    if not replay_command:
        raise SystemExit("error: run_command must not be empty")
    return f"{INTRO_BLOCK}\n{replay_command}"


def upload_cast(*, backend: dict[str, str], cast_path: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    if backend["mode"] == "native":
        return run_native(["asciinema", "upload", str(cast_path)], cwd=output_dir)
    return run_wsl(f"asciinema upload {shlex.quote(to_wsl_path(cast_path))}")


def run_native(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))


def run_wsl(command: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["wsl", "bash", "-lc", command],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(["wsl", "bash", "-lc", command], 127, "", str(exc))


def parse_asciinema_url(*chunks: str) -> str:
    for chunk in chunks:
        if not chunk:
            continue
        match = ASCIINEMA_URL_PATTERN.search(chunk)
        if match:
            return match.group(0)
    return ""


def to_wsl_path(path: Path) -> str:
    resolved = path.resolve()
    raw = str(resolved)
    if raw.startswith("/"):
        return resolved.as_posix()
    match = re.match(r"^([A-Za-z]):[\\/](.*)$", raw)
    if not match:
        raise SystemExit(f"error: unable to convert path to WSL format: {resolved}")
    drive = match.group(1).lower()
    tail = match.group(2).replace("\\", "/")
    return f"/mnt/{drive}/{tail}"


def markdown_link(url: str) -> str:
    return f"[{url}]({url})"


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


if __name__ == "__main__":
    raise SystemExit(main())
